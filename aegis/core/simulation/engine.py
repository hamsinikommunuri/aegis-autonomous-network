"""
AEGIS Packet / Flow Simulation Engine
Discrete-time network simulation engine modeling packet generation, hop-by-hop forwarding,
transmission & propagation delays, QoS queuing, packet loss, and link utilization.
"""
from typing import Dict, List, Optional, Tuple, Any, Callable
import copy
import heapq
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

        # Link continuous bandwidth credits and last service times
        self.link_byte_credits: Dict[str, float] = {lid: 0.0 for lid in self.topology.links}
        self.link_last_service_time: Dict[str, float] = {lid: 0.0 for lid in self.topology.links}

        # Flows: flow_id -> TrafficFlow
        self.flows: Dict[str, TrafficFlow] = {}
        self.traffic_generator = TrafficGenerator(seed=seed)

        # In-flight packets currently transmitting/propagating: (delivery_time_ms, packet, next_node_index)
        self.in_flight_packets: List[Tuple[float, Packet, int]] = []

        # Step metrics accumulator
        self.step_bytes_per_link: Dict[str, int] = {lid: 0 for lid in self.topology.links}
        self.step_drops_per_link: Dict[str, int] = {lid: 0 for lid in self.topology.links}
        self.event_counter: int = 0

        # Event hooks for telemetry & intelligence
        self.on_step_complete: Optional[Callable[[Dict[str, Any]], None]] = None

    def _next_event_id(self) -> int:
        self.event_counter += 1
        return self.event_counter

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

    def _service_link_up_to(self, link_id: str, until_time_ms: float, event_queue: List[Any]) -> None:
        link = self.topology.get_link(link_id)
        if not link:
            return
        buf = self.link_buffers.get(link_id)
        if not buf:
            return

        last_time = self.link_last_service_time.get(link_id, self.current_time_ms)
        elapsed_sec = max(0.0, (until_time_ms - last_time) / 1000.0)
        self.link_last_service_time[link_id] = until_time_ms

        if not link.is_operational():
            while buf.total_packets > 0:
                pkt = buf.dequeue()
                if pkt:
                    pkt.dropped = True
                    pkt.drop_reason = f"LINK_{link_id}_DOWN_IN_TRANSIT"
                    self.step_drops_per_link[link_id] += 1
                    link.packets_dropped += 1
                    flow = self.flows.get(pkt.flow_id)
                    if flow:
                        flow.record_packet_drop(pkt)
            self.link_byte_credits[link_id] = 0.0
            return

        # Add transmission credit up to buffer capacity limit
        credit_addition = (link.bandwidth_bps / 8.0) * elapsed_sec
        self.link_byte_credits[link_id] = min(
            float(buf.capacity_bytes),
            self.link_byte_credits.get(link_id, 0.0) + credit_addition
        )

        step_end_time = self.current_time_ms + self.step_duration_ms

        while buf.total_packets > 0:
            peeked = buf.peek()
            if not peeked or self.link_byte_credits[link_id] < peeked.size_bytes:
                break

            pkt = buf.dequeue()
            if not pkt:
                break

            self.link_byte_credits[link_id] -= pkt.size_bytes
            self.step_bytes_per_link[link_id] += pkt.size_bytes
            link.bytes_transmitted += pkt.size_bytes
            link.packets_transmitted += 1

            # Physical loss check
            effective_loss = link.get_effective_loss_rate()
            if effective_loss > 0.0 and self.traffic_generator.rng.random() < effective_loss:
                pkt.dropped = True
                pkt.drop_reason = "PHYSICAL_LINK_ERROR_OR_DEGRADATION"
                self.step_drops_per_link[link_id] += 1
                link.packets_dropped += 1
                flow = self.flows.get(pkt.flow_id)
                if flow:
                    flow.record_packet_drop(pkt)
                continue

            # Transmission & propagation delay
            tx_delay_ms = (pkt.size_bytes * 8.0 / max(1.0, link.bandwidth_bps)) * 1000.0
            total_link_delay_ms = tx_delay_ms + link.propagation_delay_ms

            flow = self.flows.get(pkt.flow_id)
            path = flow.current_path if flow else [link.source, link.destination]

            try:
                src_idx = path.index(link.source)
                next_idx = src_idx + 1
            except ValueError:
                next_idx = 1

            arrival_time = until_time_ms + total_link_delay_ms
            if arrival_time <= step_end_time:
                heapq.heappush(event_queue, (arrival_time, self._next_event_id(), "HOP_ARRIVAL", pkt, next_idx))
            else:
                self.in_flight_packets.append((arrival_time, pkt, next_idx))

    def step(self) -> Dict[str, Any]:
        """
        Advances the simulation by step_duration_ms:
        1. In-flight packet deliveries from previous intervals.
        2. Generate new packets for all active flows with exact sequence numbers.
        3. Service link buffers continuously using token-bucket rate credits.
        4. Dynamically compute link utilization, queue depth, and latency telemetry.
        5. Advance simulation clock.
        """
        step_start_time = self.current_time_ms
        step_end_time = self.current_time_ms + self.step_duration_ms

        # Reset interval counters
        for lid in self.topology.links:
            self.step_bytes_per_link[lid] = 0
            self.step_drops_per_link[lid] = 0
            if lid not in self.link_last_service_time:
                self.link_last_service_time[lid] = step_start_time
            if lid not in self.link_buffers:
                self.link_buffers[lid] = QoSBuffer(capacity_packets=250, capacity_bytes=375_000)

        # Min-heap event queue: (timestamp_ms, event_seq, event_type, packet, param)
        event_queue: List[Tuple[float, int, str, Packet, int]] = []

        # 1. Gather in-flight packets arriving before or during this step
        remaining_in_flight = []
        for arrival_time, pkt, hop_idx in self.in_flight_packets:
            if arrival_time <= step_end_time:
                heapq.heappush(event_queue, (arrival_time, self._next_event_id(), "HOP_ARRIVAL", pkt, hop_idx))
            else:
                remaining_in_flight.append((arrival_time, pkt, hop_idx))
        self.in_flight_packets = remaining_in_flight

        # 2. Generate new packets from active flows
        new_packets = self.traffic_generator.generate_packets_for_step(
            self.flows, self.step_duration_ms, step_start_time
        )
        for pkt in new_packets:
            heapq.heappush(event_queue, (pkt.creation_time_ms, self._next_event_id(), "NEW_PACKET", pkt, 0))

        # 3. Process events chronologically
        while event_queue:
            t, _, ev_type, pkt, hop_idx = heapq.heappop(event_queue)

            if ev_type == "NEW_PACKET":
                flow = self.flows.get(pkt.flow_id)
                path = flow.current_path if flow else None
                if not path or len(path) < 2:
                    pkt.dropped = True
                    pkt.drop_reason = "NO_ROUTE_TO_HOST"
                    if flow:
                        flow.record_packet_drop(pkt)
                    continue

                first_link = self.topology.get_link_between(path[0], path[1])
                if not first_link or not first_link.is_operational():
                    pkt.dropped = True
                    pkt.drop_reason = "EGRESS_LINK_DOWN"
                    if flow:
                        flow.record_packet_drop(pkt)
                    continue

                # Service first link up to packet injection time
                self._service_link_up_to(first_link.id, t, event_queue)
                buf = self.link_buffers[first_link.id]
                enqueued = buf.enqueue(pkt)
                if not enqueued:
                    self.step_drops_per_link[first_link.id] += 1
                    first_link.packets_dropped += 1
                    if flow:
                        flow.record_packet_drop(pkt)

            elif ev_type == "HOP_ARRIVAL":
                self._handle_hop_arrival(pkt, hop_idx, t, event_queue)

        # 4. Service all links up to step_end_time to flush queues
        for lid in self.topology.links:
            self._service_link_up_to(lid, step_end_time, event_queue)

        # Process any hop arrivals scheduled during the final flush
        while event_queue:
            t, _, ev_type, pkt, hop_idx = heapq.heappop(event_queue)
            if ev_type == "HOP_ARRIVAL":
                self._handle_hop_arrival(pkt, hop_idx, t, event_queue)

        # 5. Compute Link Runtime Telemetry
        for lid, link in self.topology.links.items():
            buf = self.link_buffers[lid]
            link_capacity_bytes = int((link.bandwidth_bps / 8.0) * (self.step_duration_ms / 1000.0))
            utilization = self.step_bytes_per_link[lid] / max(1.0, float(link_capacity_bytes))
            link.current_utilization = min(1.0, max(0.0, utilization))
            link.current_queue_depth = buf.total_packets
            link.current_queue_bytes = buf.total_bytes

            queue_delay_ms = (buf.total_bytes * 8.0 / max(1.0, link.bandwidth_bps)) * 1000.0
            link.current_latency_ms = link.propagation_delay_ms + queue_delay_ms

            total_pkts_interval = link.packets_transmitted + self.step_drops_per_link[lid]
            if total_pkts_interval > 0:
                link.recent_loss_rate = self.step_drops_per_link[lid] / max(1, total_pkts_interval)
            else:
                link.recent_loss_rate = 0.0

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

    def _handle_hop_arrival(self, pkt: Packet, hop_idx: int, arrival_time_ms: float, event_queue: List[Any]) -> None:
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
                flow.record_packet_drop(pkt)
            return

        node.forwarded_packets += 1

        # TTL check
        pkt.ttl -= 1
        if pkt.ttl <= 0:
            pkt.dropped = True
            pkt.drop_reason = "TTL_EXPIRED"
            if flow:
                flow.record_packet_drop(pkt)
            return

        # Next hop link
        if hop_idx + 1 < len(path):
            next_node_id = path[hop_idx + 1]
            out_link = self.topology.get_link_between(current_node_id, next_node_id)
            if not out_link or not out_link.is_operational():
                pkt.dropped = True
                pkt.drop_reason = f"NEXT_HOP_LINK_DOWN_{current_node_id}_{next_node_id}"
                if flow:
                    flow.record_packet_drop(pkt)
                return

            self._service_link_up_to(out_link.id, arrival_time_ms, event_queue)
            buf = self.link_buffers.get(out_link.id)
            if buf:
                enqueued = buf.enqueue(pkt)
                if not enqueued:
                    self.step_drops_per_link[out_link.id] += 1
                    out_link.packets_dropped += 1
                    if flow:
                        flow.record_packet_drop(pkt)
        else:
            # End of path without reaching destination
            pkt.dropped = True
            pkt.drop_reason = "ROUTING_BLACK_HOLE"
            if flow:
                flow.record_packet_drop(pkt)
