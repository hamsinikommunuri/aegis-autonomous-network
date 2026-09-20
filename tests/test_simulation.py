"""
Tests for Core Network, Packets, Queues, Routing, and Simulation Engine
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.network.link import Link, LinkStatus
from aegis.core.network.node import Node, NodeType, NodeStatus
from aegis.core.packets.packet import Packet, TrafficClass
from aegis.core.packets.buffer import QoSBuffer
from aegis.core.flows.flow import TrafficFlow
from aegis.core.routing.dijkstra import DijkstraRouter
from aegis.core.routing.congestion_aware import CongestionAwareRouter
from aegis.core.simulation.engine import SimulationEngine


def test_topology_creation_and_k_paths():
    topo = Topology.create_enterprise_isp_topology()
    assert "CR1" in topo.nodes
    assert "HOST-A" in topo.nodes
    assert "SVR-1" in topo.nodes
    
    router = DijkstraRouter()
    path = router.compute_path(topo, "HOST-A", "SVR-1")
    assert path is not None
    assert path[0] == "HOST-A"
    assert path[-1] == "SVR-1"
    
    # Test K shortest paths
    k_paths = topo.find_k_shortest_paths("HOST-A", "SVR-1", k=3)
    assert len(k_paths) >= 2
    for p in k_paths:
        assert p[0] == "HOST-A"
        assert p[-1] == "SVR-1"


def test_qos_buffer_priority():
    buf = QoSBuffer(capacity_packets=3)
    p_bulk = Packet(id="p1", flow_id="f1", source_id="A", dest_id="B", traffic_class=TrafficClass.BULK, size_bytes=100)
    p_norm = Packet(id="p2", flow_id="f1", source_id="A", dest_id="B", traffic_class=TrafficClass.NORMAL, size_bytes=100)
    p_crit = Packet(id="p3", flow_id="f1", source_id="A", dest_id="B", traffic_class=TrafficClass.CRITICAL, size_bytes=100)

    # Enqueue bulk first, normal second, critical third
    assert buf.enqueue(p_bulk) is True
    assert buf.enqueue(p_norm) is True
    assert buf.enqueue(p_crit) is True

    # Critical must be dequeued first, then normal, then bulk
    d1 = buf.dequeue()
    assert d1.traffic_class == TrafficClass.CRITICAL
    d2 = buf.dequeue()
    assert d2.traffic_class == TrafficClass.NORMAL
    d3 = buf.dequeue()
    assert d3.traffic_class == TrafficClass.BULK


def test_simulation_engine_traffic_delivery():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo, step_duration_ms=100.0, seed=42)

    # Add a normal flow from HOST-A to SVR-1
    flow1 = TrafficFlow(
        id="flow-web",
        name="Web Traffic",
        source_id="HOST-A",
        dest_id="SVR-1",
        traffic_class=TrafficClass.NORMAL,
        demand_bps=20_000_000.0,  # 20 Mbps
        packet_size_bytes=1000,
    )
    sim.add_flow(flow1)

    # Step simulation 15 times (1.5 seconds)
    for _ in range(15):
        sim.step()

    assert flow1.packets_sent > 0
    assert flow1.packets_received > 0
    assert flow1.average_latency_ms > 0.0
    assert flow1.packets_dropped == 0


def test_congestion_aware_routing():
    topo = Topology.create_enterprise_isp_topology()
    router = CongestionAwareRouter()
    
    # Path under zero load
    path1 = router.compute_path(topo, "HOST-A", "SVR-1")
    assert path1 is not None

    # Artificially congest link DR1-CR1 to 95%
    link = topo.get_link_between("DR1", "CR1")
    assert link is not None
    link.current_utilization = 0.95
    link.current_latency_ms = 85.0

    # Congestion-aware router should divert through alternate path (e.g. via DR2 or CR2)
    path2 = router.compute_path(topo, "HOST-A", "SVR-1")
    assert path2 is not None
    # Check that either DR1-CR1 was avoided or cost reflected the load
    edge_cost = router.calculate_link_cost(link)
    assert edge_cost > 10.0
