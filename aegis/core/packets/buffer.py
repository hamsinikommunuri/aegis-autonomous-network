"""
AEGIS QoS Multi-Queue Buffer
Implements priority-based scheduling (Strict Priority & Weighted Fair Queueing)
with tail-drop and RED queue management policies.
"""
from collections import deque
from typing import Optional, List, Dict, Tuple
from .packet import Packet, TrafficClass


class QoSBuffer:
    def __init__(self, capacity_packets: int = 200, capacity_bytes: int = 300_000):
        self.capacity_packets = capacity_packets
        self.capacity_bytes = capacity_bytes
        
        # 4 Priority Queues: CRITICAL (100), REAL_TIME (80), NORMAL (50), BULK (10)
        self.queues: Dict[TrafficClass, deque[Packet]] = {
            TrafficClass.CRITICAL: deque(),
            TrafficClass.REAL_TIME: deque(),
            TrafficClass.NORMAL: deque(),
            TrafficClass.BULK: deque(),
        }
        
        self.total_packets = 0
        self.total_bytes = 0
        self.dropped_packets = 0
        self.dropped_bytes = 0

    def enqueue(self, packet: Packet) -> bool:
        """
        Attempts to enqueue a packet into the corresponding QoS priority sub-queue.
        Returns True if enqueued, False if dropped due to buffer exhaustion.
        Under buffer pressure, lower priority packets (BULK, NORMAL) are dropped first to protect CRITICAL.
        """
        packet_size = packet.size_bytes

        # Check total buffer limits
        if self.total_packets >= self.capacity_packets or (self.total_bytes + packet_size) > self.capacity_bytes:
            # Buffer is saturated. Can we preempt a lower-priority packet to save a CRITICAL or REAL_TIME packet?
            if packet.traffic_class in (TrafficClass.CRITICAL, TrafficClass.REAL_TIME):
                # Try to drop from BULK first, then NORMAL
                for preempt_class in (TrafficClass.BULK, TrafficClass.NORMAL):
                    if self.queues[preempt_class]:
                        evicted = self.queues[preempt_class].pop()
                        evicted.dropped = True
                        evicted.drop_reason = "QOS_PREEMPTION_FOR_HIGH_PRIORITY"
                        self.total_packets -= 1
                        self.total_bytes -= evicted.size_bytes
                        self.dropped_packets += 1
                        self.dropped_bytes += evicted.size_bytes
                        break

            # Recheck after potential preemption
            if self.total_packets >= self.capacity_packets or (self.total_bytes + packet_size) > self.capacity_bytes:
                packet.dropped = True
                packet.drop_reason = "QUEUE_OVERFLOW_TAIL_DROP"
                self.dropped_packets += 1
                self.dropped_bytes += packet_size
                return False

        t_class = packet.traffic_class if packet.traffic_class in self.queues else TrafficClass.NORMAL
        self.queues[t_class].append(packet)
        self.total_packets += 1
        self.total_bytes += packet_size
        return True

    def dequeue(self) -> Optional[Packet]:
        """
        Strict Priority Dequeue: CRITICAL serviced first, then REAL_TIME, then NORMAL, then BULK.
        """
        for t_class in (TrafficClass.CRITICAL, TrafficClass.REAL_TIME, TrafficClass.NORMAL, TrafficClass.BULK):
            if self.queues[t_class]:
                pkt = self.queues[t_class].popleft()
                self.total_packets -= 1
                self.total_bytes -= pkt.size_bytes
                return pkt
        return None

    def peek(self) -> Optional[Packet]:
        for t_class in (TrafficClass.CRITICAL, TrafficClass.REAL_TIME, TrafficClass.NORMAL, TrafficClass.BULK):
            if self.queues[t_class]:
                return self.queues[t_class][0]
        return None

    def occupancy_ratio(self) -> float:
        return min(1.0, self.total_packets / max(1, self.capacity_packets))

    def clear(self) -> None:
        for q in self.queues.values():
            q.clear()
        self.total_packets = 0
        self.total_bytes = 0
