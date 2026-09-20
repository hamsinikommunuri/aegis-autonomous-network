"""
AEGIS Packet / Flow Simulation Engine
Discrete-time network simulation engine modeling packet generation, hop-by-hop forwarding,
transmission & propagation delays, QoS queuing, packet loss, and link utilization.
"""
from typing import Dict, List, Optional, Tuple, Any, Callable
import copy
from ..network.topology import Topology
from ..network.link import Link, LinkStatus
from ..network.node import Node, NodeStatus
from ..packets.packet import Packet, TrafficClass
from ..packets.buffer import QoSBuffer
from ..flows.flow import TrafficFlow
from ..flows.traffic_generator import TrafficGenerator
from ..routing.base import RoutingAlgorithm
from ..routing.dijkstra import DijkstraRouter
from ..routing.congestion_aware import CongestionAwareRouter


class SimulationEngine:
    def __init__(
        self,
        topology: Optional[Topology] = None,
        routing_algo: Optional[RoutingAlgorithm] = None,
        step_duration_ms: float = 100.0,
        seed: int = 42,
    ):
        self.topology = topology or Topology.create_enterprise_isp_topology()
        self.routing_algo = routing_algo or DijkstraRouter()
        self.step_duration_ms = step_duration_ms
        self.current_time_ms: float = 0.0
        self.tick_count: int = 0
        self.is_running: bool = False

        # Link output queues: link_id -> QoSBuffer
        self.link_buffers: Dict[str, QoSBuffer] = {}
        for lid in self.topology.links:
            self.link_buffers[lid] = QoSBuffer(capacity_packets=250, capacity_bytes=375_000)

        # Flows: flow_id -> TrafficFlow
        self.flows: Dict[str, TrafficFlow] = {}
        self.traffic_generator = TrafficGenerator(seed=seed)

        # In-flight packets currently transmitting/propagating: (delivery_time_ms, packet, next_node_index)
        self.in_flight_packets: List[Tuple[float, Packet, int]] = []

        # Step metrics accumulator
        self.step_bytes_per_link: Dict[str, int] = {lid: 0 for lid in self.topology.links}
        self.step_drops_per_link: Dict[str, int] = {lid: 0 for lid in self.topology.links}

        # Event hooks for telemetry & intelligence
        self.on_step_complete: Optional[Callable[[Dict[str, Any]], None]] = None

    def add_flow(self, flow: TrafficFlow) -> None:
        # Compute initial path if not set
        if not flow.current_path:
            path = self.routing_algo.compute_path(self.topology, flow.source_id, flow.dest_id)
            flow.current_path = path or []
        self.flows[flow.id] = flow

    def recompute_all_routes(self) -> None:
        """Recomputes forwarding paths for all active flows based on current routing algorithm."""
        for flow in self.flows.values():
            new_path = self.routing_algo.compute_path(self.topology, flow.source_id, flow.dest_id)
            if new_path:
                flow.current_path = new_path

    def step(self) -> Dict[str, Any]:
        """
        Advances the simulation by step_duration_ms:
        1. In-flight packet deliveries from previous intervals.
        2. Generate new packets for all active flows.
        3. Enqueue packets at source interfaces.
        4. Service link buffers according to available link bandwidth and QoS.
        5. Compute link utilization and latency telemetry.
        6. Advance simulation clock.
        """
        step_start_time = self.current_time_ms
        step_end_time = self.current_time_ms + self.step_duration_ms

        # Reset interval counters
        for lid in self.topology.links:
            self.step_bytes_per_link[lid] = 0
            self.step_drops_per_link[lid] = 0

        # 1. Process in-flight packets arriving before or during this step
        arrived_in_flight: List[Tuple[float, Packet, int]] = []
        remaining_in_flight: List[Tuple[float, Packet, int]] = []

        for arrival_time, pkt, hop_idx in self.in_flight_packets:
            if arrival_time <= step_end_time:
                arrived_in_flight.append((arrival_time, pkt, hop_idx))
            else:
                remaining_in_flight.append((arrival_time, pkt, hop_idx))
        self.in_flight_packets = remaining_in_flight

        # Handle arrivals
        for arrival_time, pkt, hop_idx in arrived_in_flight:
            self._handle_hop_arrival(pkt, hop_idx, arrival_time)

        # 2. Generate new packets from active flows
        new_packets = self.traffic_generator.generate_packets_for_step(
            self.flows, self.step_duration_ms, step_start_time
        )

        # 3. Enqueue new packets into first hop link buffer
        for pkt in new_packets:
            flow = self.flows.get(pkt.flow_id)
            path = flow.current_path if flow else None
            if not path or len(path) < 2:
                # No valid path, drop packet
                pkt.dropped = True
                pkt.drop_reason = "NO_ROUTE_TO_HOST"
                if flow:
                    flow.record_packet_drop()
                continue

            first_link = self.topology.get_link_between(path[0], path[1])
            if not first_link or not first_link.is_operational():
                pkt.dropped = True
                pkt.drop_reason = "EGRESS_LINK_DOWN"
                if flow:
                    flow.record_packet_drop()
                continue

            # Enqueue into link buffer
            buf = self.link_buffers.get(first_link.id)
            if buf:
                enqueued = buf.enqueue(pkt)
                if not enqueued:
                    self.step_drops_per_link[first_link.id] += 1
                    first_link.packets_dropped += 1
                    if flow:
                        flow.record_packet_drop()

        # 4. Service link buffers: transmit packets across links up to capacity
        for link_id, link in self.topology.links.items():
            if not link.is_operational():
                # Drain or drop packets in down link buffer
                buf = self.link_buffers[link_id]
                while buf.total_packets > 0:
                    pkt = buf.dequeue()
                    if pkt:
                        pkt.dropped = True
                        pkt.drop_reason = "LINK_FAILURE_IN_TRANSIT"
                        self.step_drops_per_link[link_id] += 1
                        link.packets_dropped += 1
                        flow = self.flows.get(pkt.flow_id)
                        if flow:
                            flow.record_packet_drop()
                link.current_utilization = 0.0
                link.current_queue_depth = 0
                continue

            buf = self.link_buffers[link_id]
            # Max bits link can transmit in step_duration_ms
            link_capacity_bytes = int((link.bandwidth_bps / 8.0) * (self.step_duration_ms / 1000.0))
            bytes_sent_this_step = 0

            while buf.total_packets > 0:
                peeked = buf.peek()
                if not peeked:
                    break

                if bytes_sent_this_step + peeked.size_bytes > link_capacity_bytes:
                    # Link saturated for this time step; remaining packets stay in queue
                    break

                pkt = buf.dequeue()
                if not pkt:
                    break

                # Physical loss check
                effective_loss = link.get_effective_loss_rate()
                if effective_loss > 0.0 and self.traffic_generator.rng.random() < effective_loss:
                    pkt.dropped = True
                    pkt.drop_reason = "PHYSICAL_LINK_ERROR_OR_DEGRADATION"
                    self.step_drops_per_link[link_id] += 1
                    link.packets_dropped += 1
                    flow = self.flows.get(pkt.flow_id)
                    if flow:
                        flow.record_packet_drop()
                    continue

                bytes_sent_this_step += pkt.size_bytes
                self.step_bytes_per_link[link_id] += pkt.size_bytes
                link.bytes_transmitted += pkt.size_bytes
                link.packets_transmitted += 1

                # Calculate transmission & propagation delay
                tx_delay_ms = (pkt.size_bytes * 8.0 / link.bandwidth_bps) * 1000.0
                total_link_delay_ms = tx_delay_ms + link.propagation_delay_ms

                # Find next hop index along packet's flow path
                flow = self.flows.get(pkt.flow_id)
                path = flow.current_path if flow else [link.source, link.destination]
                
                try:
                    src_idx = path.index(link.source)
                    next_idx = src_idx + 1
                except ValueError:
                    next_idx = 1

                arrival_time = self.current_time_ms + total_link_delay_ms
                if arrival_time <= step_end_time:
                    self._handle_hop_arrival(pkt, next_idx, arrival_time)
                else:
                    self.in_flight_packets.append((arrival_time, pkt, next_idx))

            # 5. Compute Link Runtime Telemetry
            utilization = bytes_sent_this_step / max(1.0, float(link_capacity_bytes))
            link.current_utilization = min(1.0, max(0.0, utilization))
            link.current_queue_depth = buf.total_packets
            link.current_queue_bytes = buf.total_bytes
            
            # Dynamic link latency (propagation + queueing delay)
            queue_delay_ms = (buf.total_bytes * 8.0 / link.bandwidth_bps) * 1000.0
            link.current_latency_ms = link.propagation_delay_ms + queue_delay_ms

            # Recent loss rate
            total_pkts_interval = link.packets_transmitted + self.step_drops_per_link[link_id]
            if total_pkts_interval > 0:
                link.recent_loss_rate = self.step_drops_per_link[link_id] / max(1, total_pkts_interval)

        # Advance clock
        self.current_time_ms = step_end_time
        self.tick_count += 1

        # Summary for step
        summary = {
            "time_ms": self.current_time_ms,
            "tick": self.tick_count,
            "links": {lid: l.to_dict() for lid, l in self.topology.links.items()},
            "nodes": {nid: n.to_dict() for nid, n in self.topology.nodes.items()},
            "flows": {fid: f.to_dict() for fid, f in self.flows.items()},
        }

        if self.on_step_complete:
            self.on_step_complete(summary)

        return summary

    def _handle_hop_arrival(self, pkt: Packet, hop_idx: int, arrival_time_ms: float) -> None:
        """Processes packet reaching an intermediate or destination node."""
        flow = self.flows.get(pkt.flow_id)
        path = flow.current_path if flow else []

        if hop_idx >= len(path):
            hop_idx = len(path) - 1

        current_node_id = path[hop_idx] if path else pkt.dest_id
        pkt.hop_path.append(current_node_id)
        pkt.current_node = current_node_id

        # Destination reached?
        if current_node_id == pkt.dest_id:
            pkt.arrival_time_ms = arrival_time_ms
            if flow:
                latency = max(0.1, arrival_time_ms - pkt.creation_time_ms)
                flow.record_packet_arrival(latency)
            return

        # Intermediate node forwarding
        node = self.topology.get_node(current_node_id)
        if not node or not node.is_operational():
            pkt.dropped = True
            pkt.drop_reason = f"NODE_{current_node_id}_UNAVAILABLE"
            if flow:
                flow.record_packet_drop()
            return

        node.forwarded_packets += 1

        # TTL check
        pkt.ttl -= 1
        if pkt.ttl <= 0:
            pkt.dropped = True
            pkt.drop_reason = "TTL_EXPIRED"
            if flow:
                flow.record_packet_drop()
            return

        # Next hop link
        if hop_idx + 1 < len(path):
            next_node_id = path[hop_idx + 1]
            out_link = self.topology.get_link_between(current_node_id, next_node_id)
            if not out_link or not out_link.is_operational():
                pkt.dropped = True
                pkt.drop_reason = f"NEXT_HOP_LINK_DOWN_{current_node_id}_{next_node_id}"
                if flow:
                    flow.record_packet_drop()
                return

            buf = self.link_buffers.get(out_link.id)
            if buf:
                enqueued = buf.enqueue(pkt)
                if not enqueued:
                    self.step_drops_per_link[out_link.id] += 1
                    out_link.packets_dropped += 1
                    if flow:
                        flow.record_packet_drop()
        else:
            # End of path without reaching destination
            pkt.dropped = True
            pkt.drop_reason = "ROUTING_BLACK_HOLE"
            if flow:
                flow.record_packet_drop()
