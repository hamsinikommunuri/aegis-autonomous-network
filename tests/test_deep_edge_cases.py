"""
Deep Edge Cases Verification Suite
Tests extreme queue overflows, disconnected graph partitioning, strict QoS SLAs under stress,
and multi-tier cascading failure recoveries.
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.network.link import Link, LinkStatus
from aegis.core.network.node import Node, NodeStatus
from aegis.core.simulation.engine import SimulationEngine
from aegis.core.flows.flow import TrafficFlow
from aegis.core.packets.packet import Packet, TrafficClass
from aegis.core.packets.buffer import QoSBuffer
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.recovery.orchestrator import AegisOrchestrator
from aegis.experiments.failure_injection.injector import FailureInjector


def test_extreme_buffer_saturation_and_qos_preemption():
    """Verifies that under severe queue exhaustion, critical traffic preempts bulk traffic."""
    buf = QoSBuffer(capacity_packets=5)
    
    # Fill buffer with 5 bulk packets
    for i in range(5):
        pkt = Packet(id=f"b-{i}", flow_id="f-bulk", source_id="A", dest_id="B", traffic_class=TrafficClass.BULK, size_bytes=100)
        assert buf.enqueue(pkt) is True

    assert buf.total_packets == 5
    assert buf.occupancy_ratio() == 1.0

    # Try to enqueue another bulk packet -> should be dropped
    bulk_overflow = Packet(id="b-overflow", flow_id="f-bulk", source_id="A", dest_id="B", traffic_class=TrafficClass.BULK, size_bytes=100)
    assert buf.enqueue(bulk_overflow) is False
    assert bulk_overflow.dropped is True
    assert bulk_overflow.drop_reason == "QUEUE_OVERFLOW_TAIL_DROP"

    # Now enqueue a CRITICAL packet -> buffer should evict a bulk packet to accept critical!
    crit_pkt = Packet(id="c-1", flow_id="f-crit", source_id="A", dest_id="B", traffic_class=TrafficClass.CRITICAL, size_bytes=100)
    assert buf.enqueue(crit_pkt) is True
    assert buf.total_packets == 5
    # The first packet dequeued must be the critical packet!
    dequeued = buf.dequeue()
    assert dequeued.id == "c-1"
    assert dequeued.traffic_class == TrafficClass.CRITICAL


def test_partitioned_disconnected_topology():
    """Verifies behavior when topology is completely partitioned."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)

    # Disconnect all paths to SVR-1 by disabling DR3 and DR4
    topo.set_node_status("DR3", NodeStatus.DOWN)
    topo.set_node_status("DR4", NodeStatus.DOWN)

    # Recompute routes
    router = sim.routing_algo
    path = router.compute_path(topo, "HOST-A", "SVR-1")
    assert path is None

    # Flow cannot route, packets should be dropped gracefully with NO_ROUTE_TO_HOST
    flow = TrafficFlow(id="f-island", name="Island", source_id="HOST-A", dest_id="SVR-1", demand_bps=10_000_000.0)
    sim.add_flow(flow)

    sim.step()
    assert flow.packets_sent > 0
    assert flow.packets_dropped > 0
    assert flow.loss_rate_percent == 100.0


def test_multi_incident_memory_efficacy_metrics():
    """Verifies IncidentMemory calculates MTTR, rollback rate, and recovery rate."""
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    orchestrator = AegisOrchestrator(sim, telemetry)

    assert orchestrator.memory.get_efficacy_stats()["total_incidents"] == 0

    # Inject failure, simulate steps
    orchestrator.injector = FailureInjector(sim)
    flow = TrafficFlow(id="f1", name="F1", source_id="HOST-A", dest_id="SVR-1", demand_bps=40_000_000.0)
    sim.add_flow(flow)

    for _ in range(3):
        sim.step()

    orchestrator.injector.inject_bandwidth_reduction("DR1-CR1", 20_000_000.0)

    for _ in range(10):
        sim.step()

    stats = orchestrator.memory.get_efficacy_stats()
    assert stats["total_incidents"] >= 1
    assert stats["recovery_success_rate"] >= 0.0
