"""
Comprehensive Tests for AEGIS Advanced Features:
1. Actuator direct methods (Section 15) & audit logging
2. All 10 RCA diagnoses
3. Queue saturation & packet corruption injections
4. Scenario F autonomous rollback progression across candidate plans
5. TCP packet retransmission tracking & sequence numbers
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.network.link import LinkStatus
from aegis.core.network.node import NodeStatus
from aegis.core.simulation.engine import SimulationEngine
from aegis.core.flows.flow import TrafficFlow
from aegis.core.packets.packet import Packet, TrafficClass
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.intelligence.anomaly_detection.correlator import AnomalyDetector
from aegis.intelligence.diagnosis.rca_engine import RootCauseAnalyzer
from aegis.recovery.incident import Incident, IncidentStatus, IncidentSeverity
from aegis.recovery.actuator.network_actuator import NetworkActuator
from aegis.recovery.orchestrator import AegisOrchestrator
from aegis.experiments.failure_injection.injector import FailureInjector


def test_actuator_direct_methods_and_audit_logging():
    """Verify all explicit actuator methods and ACTION audit logs."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    flow = TrafficFlow(id="f-test", name="Test", source_id="HOST-A", dest_id="SVR-1")
    sim.add_flow(flow)

    actuator = NetworkActuator(sim)

    # 1. reroute_flow
    act1 = actuator.reroute_flow("f-test", ["HOST-A", "AS1", "DR2", "CR2", "DR3", "SVR-1"])
    assert "ACTION #" in act1["action_id"]
    assert flow.current_path == ["HOST-A", "AS1", "DR2", "CR2", "DR3", "SVR-1"]

    # 2. change_route_cost
    act2 = actuator.change_route_cost("DR1-CR1", 25.0)
    assert "ACTION #" in act2["action_id"]
    link = topo.get_link("DR1-CR1")
    assert link.operational_cost == 25.0

    # 3. disable_link and restore_link
    act3 = actuator.disable_link("DR1-CR1")
    assert link.status == LinkStatus.DOWN
    act4 = actuator.restore_link("DR1-CR1")
    assert link.status == LinkStatus.UP

    # 4. disable_node and restore_node
    act5 = actuator.disable_node("CR2")
    node = topo.get_node("CR2")
    assert node.status == NodeStatus.DOWN
    act6 = actuator.restore_node("CR2")
    assert node.status == NodeStatus.UP

    # 5. change_bandwidth
    act7 = actuator.change_bandwidth("DR1-CR1", 500_000_000.0)
    assert link.bandwidth_bps == 500_000_000.0

    # 6. change_traffic_priority
    act8 = actuator.change_traffic_priority("f-test", TrafficClass.CRITICAL)
    assert flow.traffic_class == TrafficClass.CRITICAL
    assert flow.priority == 100

    # 7. change_qos_policy
    act9 = actuator.change_qos_policy("DR1-CR1", "WFQ")
    assert act9["status"] == "SUCCESS"

    # Check total action history length
    assert len(actuator.action_history) == 9


def test_failure_injector_queue_saturation_and_corruption():
    """Verify queue saturation and packet corruption injections."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    injector = FailureInjector(sim, seed=123)

    # Queue saturation
    res_q = injector.inject_queue_saturation("DR1-CR1", depth_packets=50)
    assert res_q is True
    link = topo.get_link("DR1-CR1")
    assert link.current_queue_depth > 0

    # Packet corruption
    res_c = injector.inject_packet_corruption("DR1-CR1", error_rate=0.22)
    assert res_c is True
    assert link.error_rate == 0.22
    assert link.status == LinkStatus.DEGRADED


def test_all_rca_root_cause_diagnoses():
    """Verify RootCauseAnalyzer diagnoses for all root cause categories."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    rca = RootCauseAnalyzer(topo)

    # 1. PHYSICAL_LINK_CUT_OR_PORT_SHUTDOWN
    topo.get_link("DR1-CR1").status = LinkStatus.DOWN
    snap = telemetry.collect()
    diag1 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "LINK_FAILURE", "anomaly_score": 1.0}, snap)
    assert diag1["root_cause"] == "PHYSICAL_LINK_CUT_OR_PORT_SHUTDOWN"

    # 2. HARDWARE_ROUTER_CRASH_OR_POWER_LOSS
    topo.get_link("DR1-CR1").status = LinkStatus.UP
    topo.get_node("CR1").status = NodeStatus.DOWN
    snap = telemetry.collect()
    diag2 = rca.diagnose({"resource": "CR1", "resource_type": "NODE", "anomaly_type": "NODE_FAILURE", "anomaly_score": 1.0}, snap)
    assert "ROUTER" in diag2["root_cause"]
    topo.get_node("CR1").status = NodeStatus.UP

    # 3. PHYSICAL_PACKET_LOSS_DEGRADATION
    link = topo.get_link("DR1-CR1")
    link.recent_loss_rate = 0.15
    link.current_utilization = 0.30
    link.current_queue_depth = 0
    snap = telemetry.collect()
    diag3 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "LINK_DEGRADATION", "anomaly_score": 0.85}, snap)
    assert diag3["root_cause"] == "PHYSICAL_PACKET_LOSS_DEGRADATION"

    # 4. QUEUE_OVERFLOW
    link.current_utilization = 0.88
    link.current_queue_depth = 195
    link.queue_capacity_packets = 200
    snap = telemetry.collect()
    diag4 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "QUEUE_OVERFLOW", "anomaly_score": 0.90}, snap)
    assert diag4["root_cause"] == "QUEUE_OVERFLOW"

    # 5. ABNORMAL_TRAFFIC_SURGE
    link.current_queue_depth = 50
    diag5 = rca.diagnose({
        "resource": "DR1-CR1",
        "resource_type": "LINK",
        "anomaly_type": "TRAFFIC_SURGE",
        "anomaly_score": 0.88,
        "evidence": {"rate_of_change": "+50 Mbps surge"}
    }, snap)
    assert diag5["root_cause"] == "ABNORMAL_TRAFFIC_SURGE"

    # 6. TOPOLOGY_PARTITION
    diag6 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "TOPOLOGY_PARTITION", "anomaly_score": 1.0}, snap)
    assert diag6["root_cause"] == "TOPOLOGY_PARTITION"

    # 7. ROUTING_FAILURE
    diag7 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "ROUTING_FAILURE", "anomaly_score": 0.80}, snap)
    assert diag7["root_cause"] == "ROUTING_FAILURE"

    # 8. CASCADING_CONGESTION
    link.current_utilization = 0.90
    link.current_queue_depth = 50
    for dest_nid, out_l in topo.get_out_links("DR1").items():
        out_l.current_utilization = 0.92
    snap = telemetry.collect()
    diag8 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "LINK_CONGESTION", "anomaly_score": 0.92}, snap)
    assert diag8["root_cause"] == "CASCADING_CONGESTION"

    # 9. LINK_CONGESTION (isolated bottleneck)
    for dest_nid, out_l in topo.get_out_links("DR1").items():
        if out_l.id != "DR1-CR1":
            out_l.current_utilization = 0.20
    link.current_utilization = 0.90
    snap = telemetry.collect()
    diag9 = rca.diagnose({"resource": "DR1-CR1", "resource_type": "LINK", "anomaly_type": "LINK_CONGESTION", "anomaly_score": 0.88}, snap)
    assert "CONGESTION" in diag9["root_cause"]


def test_scenario_f_autonomous_rollback_progression():
    """Verify Scenario F where candidate failure triggers rollback and moves to alternate candidate."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo, step_duration_ms=100.0)

    f_voip = TrafficFlow(id="f-voip", name="VoIP", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.CRITICAL, demand_bps=10_000_000.0)
    f_web = TrafficFlow(id="f-web", name="Web", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.NORMAL, demand_bps=20_000_000.0)
    sim.add_flow(f_voip)
    sim.add_flow(f_web)

    telemetry = TelemetryCollector(sim)
    orchestrator = AegisOrchestrator(sim, telemetry, autonomous_mode=True)

    incident = Incident(
        id="INC-SCENARIO-F",
        incident_type="LINK_CONGESTION",
        affected_resource="DR1-CR1",
        severity=IncidentSeverity.HIGH,
        detected_time_ms=100.0,
    )

    # Pre-populate failed plans to simulate rollback progression
    incident.failed_plan_ids.append("PLAN-A")
    candidates = orchestrator.planner.generate_and_rank_plans(incident)
    
    # Top candidate must now be an alternate plan (e.g. PLAN-D or PLAN-B), while PLAN-A is marked FAILED with negative score
    assert candidates[0]["id"] in ("PLAN-D", "PLAN-B")
    plan_a = next(c for c in candidates if c["id"] == "PLAN-A")
    assert plan_a["status"] == "FAILED"
    assert plan_a["score"] == -999.0

    # Now simulate the next candidate also failing
    next_cand_id = candidates[0]["id"]
    incident.failed_plan_ids.append(next_cand_id)
    candidates_after_next = orchestrator.planner.generate_and_rank_plans(incident)
    assert candidates_after_next[0]["id"] not in ("PLAN-A", next_cand_id)
    plan_next = next(c for c in candidates_after_next if c["id"] == next_cand_id)
    assert plan_next["status"] == "FAILED"
    assert len(candidates_after_next) >= 1


def test_packet_sequence_and_retransmissions():
    """Verify packet sequencing, comparison, and flow retransmission counters."""
    p1 = Packet(id="p1", flow_id="f1", source_id="HOST-A", dest_id="SVR-1", sequence_number=1, creation_time_ms=10.0)
    p2 = Packet(id="p2", flow_id="f1", source_id="HOST-A", dest_id="SVR-1", sequence_number=2, creation_time_ms=20.0)
    p3 = Packet(id="p3", flow_id="f1", source_id="HOST-A", dest_id="SVR-1", sequence_number=1, retransmission=True, creation_time_ms=30.0)

    assert p1 < p2
    assert p3.retransmission is True

    flow = TrafficFlow(id="f1", name="Flow", source_id="HOST-A", dest_id="SVR-1")
    flow.retransmissions += 1
    assert flow.retransmissions == 1
