"""
AEGIS Packet Model
Defines discrete simulated packets, traffic priorities, protocol headers, and lifecycle state.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TrafficClass(str, Enum):
    CRITICAL = "CRITICAL"    # Priority 100 - Telemetry, Control, Emergency
    REAL_TIME = "REAL_TIME"  # Priority 80  - Voice, Real-time video
    NORMAL = "NORMAL"        # Priority 50  - HTTP/HTTPS, Web Apps
    BULK = "BULK"            # Priority 10  - Backups, Large File Transfers

    @property
    def priority_value(self) -> int:
        return TRAFFIC_CLASS_PRIORITIES.get(self, 50)


TRAFFIC_CLASS_PRIORITIES = {
    TrafficClass.CRITICAL: 100,
    TrafficClass.REAL_TIME: 80,
    TrafficClass.NORMAL: 50,
    TrafficClass.BULK: 10,
}


class Protocol(str, Enum):
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"


@dataclass
class Packet:
    id: str
    flow_id: str
    source_id: str
    dest_id: str
    protocol: Protocol = Protocol.TCP
    traffic_class: TrafficClass = TrafficClass.NORMAL
    priority: int = 50
    size_bytes: int = 1500
    creation_time_ms: float = 0.0
    departure_time_ms: Optional[float] = None
    arrival_time_ms: Optional[float] = None
    sequence_number: int = 0
    retransmission: bool = False
    ttl: int = 64
    hop_path: List[str] = field(default_factory=list)
    current_node: Optional[str] = None
    dropped: bool = False
    drop_reason: Optional[str] = None

    def __post_init__(self):
        if self.priority == 50 and self.traffic_class in TRAFFIC_CLASS_PRIORITIES:
            self.priority = TRAFFIC_CLASS_PRIORITIES[self.traffic_class]

    @property
    def latency_ms(self) -> Optional[float]:
        if self.arrival_time_ms is not None:
            return max(0.0, self.arrival_time_ms - self.creation_time_ms)
        return None

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Packet):
            if self.creation_time_ms != other.creation_time_ms:
                return self.creation_time_ms < other.creation_time_ms
            return self.sequence_number < other.sequence_number
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "source_id": self.source_id,
            "dest_id": self.dest_id,
            "sequence_number": self.sequence_number,
            "retransmission": self.retransmission,
            "protocol": self.protocol.value,
            "traffic_class": self.traffic_class.value,
            "priority": self.priority,
            "size_bytes": self.size_bytes,
            "creation_time_ms": round(self.creation_time_ms, 2),
            "arrival_time_ms": round(self.arrival_time_ms, 2) if self.arrival_time_ms is not None else None,
            "latency_ms": round(self.latency_ms, 2) if self.latency_ms is not None else None,
            "ttl": self.ttl,
            "hop_path": list(self.hop_path),
            "dropped": self.dropped,
            "drop_reason": self.drop_reason,
        }
