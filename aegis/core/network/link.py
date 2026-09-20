"""
AEGIS Network Interfaces and Links
Defines interfaces, operational links, link state, and queue abstractions.
"""
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class LinkStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"


@dataclass
class NetworkInterface:
    name: str
    ip_address: str
    mac_address: str
    speed_bps: float = 1_000_000_000.0  # 1 Gbps default
    mtu: int = 1500
    is_up: bool = True
    tx_bytes: int = 0
    rx_bytes: int = 0
    tx_packets: int = 0
    rx_packets: int = 0
    tx_drops: int = 0
    rx_drops: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "speed_bps": self.speed_bps,
            "mtu": self.mtu,
            "is_up": self.is_up,
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
            "tx_packets": self.tx_packets,
            "rx_packets": self.rx_packets,
            "tx_drops": self.tx_drops,
            "rx_drops": self.rx_drops,
        }


@dataclass
class Link:
    id: str
    source: str
    destination: str
    bandwidth_bps: float = 100_000_000.0  # 100 Mbps default
    propagation_delay_ms: float = 5.0      # 5ms default
    loss_rate: float = 0.0                # Physical loss probability [0.0, 1.0]
    error_rate: float = 0.0               # BER [0.0, 1.0]
    base_cost: float = 1.0                # Base routing metric / hop cost
    operational_cost: float = 1.0         # Dynamic cost used by routing engine
    status: LinkStatus = LinkStatus.UP
    queue_capacity_packets: int = 200

    # Runtime operational state
    current_utilization: float = 0.0      # [0.0, 1.0]
    current_queue_depth: int = 0
    current_queue_bytes: int = 0
    current_latency_ms: float = 5.0
    bytes_transmitted: int = 0
    packets_transmitted: int = 0
    packets_dropped: int = 0
    recent_loss_rate: float = 0.0

    def is_operational(self) -> bool:
        return self.status != LinkStatus.DOWN

    def get_effective_loss_rate(self) -> float:
        if self.status == LinkStatus.DOWN:
            return 1.0
        if self.status == LinkStatus.DEGRADED:
            return max(self.loss_rate, 0.05)
        return self.loss_rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "destination": self.destination,
            "bandwidth_bps": self.bandwidth_bps,
            "propagation_delay_ms": self.propagation_delay_ms,
            "loss_rate": self.loss_rate,
            "error_rate": self.error_rate,
            "base_cost": self.base_cost,
            "operational_cost": self.operational_cost,
            "status": self.status.value,
            "queue_capacity_packets": self.queue_capacity_packets,
            "current_utilization": round(self.current_utilization, 4),
            "current_queue_depth": self.current_queue_depth,
            "current_latency_ms": round(self.current_latency_ms, 2),
            "bytes_transmitted": self.bytes_transmitted,
            "packets_transmitted": self.packets_transmitted,
            "packets_dropped": self.packets_dropped,
            "recent_loss_rate": round(self.recent_loss_rate, 4),
        }
