"""
Tests for Recovery Planning, Network Actuation, Verification, and Rollback
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.network.link import LinkStatus
from aegis.core.simulation.engine import SimulationEngine
from aegis.core.flows.flow import TrafficFlow
from aegis.core.packets.packet import TrafficClass
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.recovery.incident import Incident, IncidentStatus, IncidentSeverity
from aegis.recovery.planner.planner import RecoveryPlanner
from aegis.recovery.actuator.network_actuator import NetworkActuator
from aegis.recovery.verification.verifier import VerificationEngine
from aegis.recovery.rollback.rollback_manager import RollbackManager
from aegis.recovery.orchestrator import AegisOrchestrator


def test_recovery_planner_candidate_generation():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    
    # Add critical and bulk flows
    f1 = TrafficFlow(id="crit-1", name="Crit", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.CRITICAL)
    f2 = TrafficFlow(id="bulk-1", name="Bulk", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.BULK)
    sim.add_flow(f1)
    sim.add_flow(f2)

    planner = RecoveryPlanner(sim)
    incident = Incident(
        id="INC-001",
        incident_type="LINK_CONGESTION",
        affected_resource="DR1-CR1",
        severity=IncidentSeverity.HIGH,
        detected_time_ms=100.0,
    )

    candidates = planner.generate_and_rank_plans(incident)
    assert len(candidates) >= 2
    # Ensure plans are scored and ranked
    assert candidates[0]["score"] >= candidates[-1]["score"]
    # Check that candidate A exists and preserves QoS
    assert any(c["id"] == "PLAN-A" for c in candidates)


def test_autonomous_recovery_and_verification_cycle():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo, step_duration_ms=100.0)
    
    # Add flow traversing DR1-CR1
    flow = TrafficFlow(id="f1", name="TestFlow", source_id="HOST-A", dest_id="SVR-1", demand_bps=40_000_000.0)
    sim.add_flow(flow)

    telemetry = TelemetryCollector(sim)
    orchestrator = AegisOrchestrator(sim, telemetry, autonomous_mode=True)

    # Prime baseline
    for _ in range(3):
        sim.step()

    # Degrade link to trigger genuine congestion (40 Mbps demand on 20 Mbps bandwidth)
    link = topo.get_link_between("DR1", "CR1")
    assert link is not None
    link.bandwidth_bps = 20_000_000.0

    # Step simulation through detection, diagnosis, planning, and execution
    for _ in range(8):
        sim.step()

    # Check that orchestrator intervened
    assert len(orchestrator.memory.history) > 0 or len(orchestrator.active_incidents) > 0


def test_rollback_on_failed_verification():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    flow = TrafficFlow(id="f1", name="TestFlow", source_id="HOST-A", dest_id="SVR-1")
    sim.add_flow(flow)
    original_path = list(flow.current_path)

    actuator = NetworkActuator(sim)
    rollback_mgr = RollbackManager(actuator)

    incident = Incident(
        id="INC-ROLLBACK-TEST",
        incident_type="LINK_CONGESTION",
        affected_resource="DR1-CR1",
        severity=IncidentSeverity.HIGH,
        detected_time_ms=100.0,
    )

    plan = {
        "id": "PLAN-BAD",
        "action_type": "REROUTE_FLOWS",
        "action_params": {
            "reroutes": [{
                "flow_id": "f1",
                "old_path": original_path,
                "new_path": ["HOST-A", "AS1", "DR2", "CR2", "DR4", "SVR-2"],
            }]
        }
    }

    # Execute bad plan
    record = actuator.execute_plan(plan)
    assert flow.current_path != original_path

    # Verification fails -> trigger rollback
    success = rollback_mgr.perform_rollback(incident, record, "Failed collateral test")
    assert success is True
    # Flow path must be restored to original!
    assert flow.current_path == original_path
    assert incident.rollback_performed is True
    assert incident.status == IncidentStatus.ROLLBACK
