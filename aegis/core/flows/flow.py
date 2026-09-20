"""
AEGIS Traffic Flow Model
Represents continuous network flows between endpoints, their QoS requirements,
SLA constraints, and runtime telemetry.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..packets.packet import TrafficClass, TRAFFIC_CLASS_PRIORITIES, Protocol


@dataclass
class TrafficFlow:
    id: str
    name: str
    source_id: str
    dest_id: str
    traffic_class: TrafficClass = TrafficClass.NORMAL
    demand_bps: float = 10_000_000.0       # 10 Mbps default
    packet_size_bytes: int = 1400          # bytes
    latency_sla_ms: float = 50.0           # Max allowed latency under SLA
    loss_sla_percent: float = 1.0          # Max allowed loss percentage under SLA
    protocol: Protocol = Protocol.TCP
    priority: int = 50
    active: bool = True
    current_path: List[str] = field(default_factory=list)

    # Runtime metrics
    packets_sent: int = 0
    packets_received: int = 0
    packets_dropped: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    recent_latencies_ms: List[float] = field(default_factory=list)
    average_latency_ms: float = 0.0
    jitter_ms: float = 0.0
    sla_violated: bool = False

    def __post_init__(self):
        if self.priority == 50 and self.traffic_class in TRAFFIC_CLASS_PRIORITIES:
            self.priority = TRAFFIC_CLASS_PRIORITIES[self.traffic_class]

    @property
    def packets_per_second(self) -> float:
        if self.packet_size_bytes <= 0:
            return 0.0
        return (self.demand_bps / 8.0) / self.packet_size_bytes

    @property
    def loss_rate_percent(self) -> float:
        total = self.packets_received + self.packets_dropped
        if total == 0:
            return 0.0
        return (self.packets_dropped / total) * 100.0

    def record_packet_arrival(self, latency_ms: float) -> None:
        self.packets_received += 1
        self.bytes_received += self.packet_size_bytes
        self.recent_latencies_ms.append(latency_ms)
        if len(self.recent_latencies_ms) > 50:
            self.recent_latencies_ms.pop(0)

        # Update average latency
        self.average_latency_ms = sum(self.recent_latencies_ms) / len(self.recent_latencies_ms)

        # RFC 3393 Jitter calculation
        if len(self.recent_latencies_ms) >= 2:
            diffs = [abs(self.recent_latencies_ms[i] - self.recent_latencies_ms[i-1]) for i in range(1, len(self.recent_latencies_ms))]
            self.jitter_ms = sum(diffs) / len(diffs)

        # Check SLA compliance
        self.sla_violated = (self.average_latency_ms > self.latency_sla_ms) or (self.loss_rate_percent > self.loss_sla_percent)

    def record_packet_drop(self) -> None:
        self.packets_dropped += 1
        self.sla_violated = (self.loss_rate_percent > self.loss_sla_percent) or (self.average_latency_ms > self.latency_sla_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_id": self.source_id,
            "dest_id": self.dest_id,
            "traffic_class": self.traffic_class.value,
            "demand_bps": self.demand_bps,
            "packet_size_bytes": self.packet_size_bytes,
            "packets_per_second": round(self.packets_per_second, 1),
            "latency_sla_ms": self.latency_sla_ms,
            "loss_sla_percent": self.loss_sla_percent,
            "protocol": self.protocol.value,
            "priority": self.priority,
            "active": self.active,
            "current_path": list(self.current_path),
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_dropped": self.packets_dropped,
            "loss_rate_percent": round(self.loss_rate_percent, 2),
            "average_latency_ms": round(self.average_latency_ms, 2),
            "jitter_ms": round(self.jitter_ms, 2),
            "sla_violated": self.sla_violated,
        }
