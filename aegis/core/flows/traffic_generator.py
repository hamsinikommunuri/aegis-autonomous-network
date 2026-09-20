"""
AEGIS Traffic Generator
Generates reproducible packet streams for configured traffic flows using deterministic PRNG.
"""
import random
import uuid
from typing import List, Dict
from .flow import TrafficFlow
from ..packets.packet import Packet


class TrafficGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.packet_counter = 0

    def reset(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.packet_counter = 0

    def generate_packets_for_step(self, flows: Dict[str, TrafficFlow], step_duration_ms: float, current_time_ms: float) -> List[Packet]:
        """
        Generates simulated packets for each active flow over the interval [current_time_ms, current_time_ms + step_duration_ms].
        """
        generated: List[Packet] = []
        step_duration_sec = step_duration_ms / 1000.0

        for flow in flows.values():
            if not flow.active:
                continue

            # Expected packets in this interval
            expected_packets = flow.packets_per_second * step_duration_sec
            count = int(expected_packets)
            # Fractional packet handling via PRNG
            if self.rng.random() < (expected_packets - count):
                count += 1

            # Handle retransmissions if any in queue
            retrans_budget = min(len(flow.retransmission_queue), max(1, count // 4))
            for _ in range(retrans_budget):
                dropped_pkt = flow.retransmission_queue.pop(0)
                self.packet_counter += 1
                offset = self.rng.uniform(0.0, step_duration_ms * 0.5)
                retrans_pkt = Packet(
                    id=f"retrans-{flow.id}-{self.packet_counter}",
                    flow_id=flow.id,
                    source_id=flow.source_id,
                    dest_id=flow.dest_id,
                    protocol=flow.protocol,
                    traffic_class=flow.traffic_class,
                    priority=flow.priority,
                    size_bytes=flow.packet_size_bytes,
                    creation_time_ms=current_time_ms + offset,
                    sequence_number=dropped_pkt.sequence_number,
                    retransmission=True,
                    hop_path=[flow.source_id],
                    current_node=flow.source_id,
                )
                generated.append(retrans_pkt)
                flow.retransmissions += 1
                flow.packets_sent += 1
                flow.bytes_sent += flow.packet_size_bytes

            for _ in range(count):
                self.packet_counter += 1
                pkt_id = f"pkt-{flow.id}-{self.packet_counter}"
                
                # Small temporal spread within interval
                offset = self.rng.uniform(0.0, step_duration_ms)
                
                pkt = Packet(
                    id=pkt_id,
                    flow_id=flow.id,
                    source_id=flow.source_id,
                    dest_id=flow.dest_id,
                    protocol=flow.protocol,
                    traffic_class=flow.traffic_class,
                    priority=flow.priority,
                    size_bytes=flow.packet_size_bytes,
                    creation_time_ms=current_time_ms + offset,
                    sequence_number=flow.get_next_sequence_number(),
                    retransmission=False,
                    hop_path=[flow.source_id],
                    current_node=flow.source_id,
                )
                generated.append(pkt)
                flow.packets_sent += 1
                flow.bytes_sent += flow.packet_size_bytes

        # Sort chronologically
        generated.sort(key=lambda p: p.creation_time_ms)
        return generated
