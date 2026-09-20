"""
AEGIS Failure Injection Engine
Controlled, reproducible injection of faults: link cuts, router crashes, optical degradation,
latency spikes, bandwidth chokes, and traffic surges.
"""
from typing import Dict, List, Optional, Any
from ...core.simulation.engine import SimulationEngine
from ...core.network.link import LinkStatus
from ...core.network.node import NodeStatus


class FailureInjector:
    def __init__(self, simulation: SimulationEngine):
        self.sim = simulation
        self.original_link_configs: Dict[str, Dict[str, Any]] = {}
        self.original_node_configs: Dict[str, Dict[str, Any]] = {}
        self.original_flow_demands: Dict[str, float] = {}

        # Save baseline configuration for clean resets
        for lid, link in simulation.topology.links.items():
            self.original_link_configs[lid] = {
                "status": link.status,
                "bandwidth_bps": link.bandwidth_bps,
                "propagation_delay_ms": link.propagation_delay_ms,
                "loss_rate": link.loss_rate,
            }

        for nid, node in simulation.topology.nodes.items():
            self.original_node_configs[nid] = {
                "status": node.status,
                "processing_capacity_pps": node.processing_capacity_pps,
            }

        for fid, flow in simulation.flows.items():
            self.original_flow_demands[fid] = flow.demand_bps

    def inject_link_failure(self, link_id: str) -> bool:
        """Instantly cuts physical link."""
        return self.sim.topology.set_link_status(link_id, LinkStatus.DOWN)

    def inject_node_failure(self, node_id: str) -> bool:
        """Immediately powers off router or switch node."""
        return self.sim.topology.set_node_status(node_id, NodeStatus.DOWN)

    def inject_packet_loss(self, link_id: str, loss_rate: float = 0.12) -> bool:
        """Simulates physical layer BER degradation / dirty fiber."""
        link = self.sim.topology.get_link(link_id)
        if link:
            link.loss_rate = loss_rate
            link.status = LinkStatus.DEGRADED
            rev = self.sim.topology.get_link_between(link.destination, link.source)
            if rev:
                rev.loss_rate = loss_rate
                rev.status = LinkStatus.DEGRADED
            return True
        return False

    def inject_latency_spike(self, link_id: str, extra_delay_ms: float = 80.0) -> bool:
        """Simulates path stretching or queue delay."""
        link = self.sim.topology.get_link(link_id)
        if link:
            link.propagation_delay_ms += extra_delay_ms
            rev = self.sim.topology.get_link_between(link.destination, link.source)
            if rev:
                rev.propagation_delay_ms += extra_delay_ms
            return True
        return False

    def inject_bandwidth_reduction(self, link_id: str, new_bandwidth_bps: float = 20_000_000.0) -> bool:
        """Chokes link bandwidth (e.g. negotiation down to 10/100Mbps)."""
        link = self.sim.topology.get_link(link_id)
        if link:
            link.bandwidth_bps = new_bandwidth_bps
            rev = self.sim.topology.get_link_between(link.destination, link.source)
            if rev:
                rev.bandwidth_bps = new_bandwidth_bps
            return True
        return False

    def inject_traffic_surge(self, flow_id: str, multiplier: float = 4.0) -> bool:
        """Simulates sudden application traffic burst / flash crowd."""
        flow = self.sim.flows.get(flow_id)
        if flow:
            flow.demand_bps *= multiplier
            return True
        return False

    def reset_all_failures(self) -> None:
        """Restores network to clean nominal baseline."""
        for lid, cfg in self.original_link_configs.items():
            link = self.sim.topology.get_link(lid)
            if link:
                link.status = cfg["status"]
                link.bandwidth_bps = cfg["bandwidth_bps"]
                link.propagation_delay_ms = cfg["propagation_delay_ms"]
                link.loss_rate = cfg["loss_rate"]

        for nid, cfg in self.original_node_configs.items():
            node = self.sim.topology.get_node(nid)
            if node:
                node.status = cfg["status"]
                node.processing_capacity_pps = cfg["processing_capacity_pps"]
                node.update_health()

        for fid, demand in self.original_flow_demands.items():
            flow = self.sim.flows.get(fid)
            if flow:
                flow.demand_bps = demand

        # Drain and reset buffers
        for buf in self.sim.link_buffers.values():
            buf.clear()
        self.sim.recompute_all_routes()
