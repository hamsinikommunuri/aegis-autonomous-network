"""
AEGIS Telemetry Metrics Definitions
Structured snapshot representations for links, nodes, flows, and global network state.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class LinkMetricSnapshot:
    link_id: str
    source: str
    destination: str
    status: str
    bandwidth_bps: float
    utilization: float          # [0.0, 1.0]
    latency_ms: float
    loss_rate: float            # [0.0, 1.0]
    queue_depth: int
    queue_bytes: int
    bytes_transmitted: int
    packets_transmitted: int
    packets_dropped: int


@dataclass
class NodeMetricSnapshot:
    node_id: str
    status: str
    cpu_utilization: float
    memory_utilization: float
    queue_depth: int
    health_score: float
    forwarded_packets: int
    dropped_packets: int


@dataclass
class FlowMetricSnapshot:
    flow_id: str
    traffic_class: str
    demand_bps: float
    packets_sent: int
    packets_received: int
    packets_dropped: int
    loss_percent: float
    avg_latency_ms: float
    jitter_ms: float
    sla_violated: bool
    current_path: List[str]


@dataclass
class NetworkGlobalSnapshot:
    timestamp_ms: float
    tick: int
    total_throughput_bps: float
    total_packets_sent: int
    total_packets_received: int
    total_packets_dropped: int
    global_packet_loss_rate: float
    average_latency_ms: float
    average_jitter_ms: float
    sla_compliance_rate: float
    active_incidents_count: int = 0
    links: Dict[str, LinkMetricSnapshot] = field(default_factory=dict)
    nodes: Dict[str, NodeMetricSnapshot] = field(default_factory=dict)
    flows: Dict[str, FlowMetricSnapshot] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_ms": round(self.timestamp_ms, 2),
            "tick": self.tick,
            "total_throughput_bps": round(self.total_throughput_bps, 2),
            "total_throughput_mbps": round(self.total_throughput_bps / 1_000_000.0, 3),
            "total_packets_sent": self.total_packets_sent,
            "total_packets_received": self.total_packets_received,
            "total_packets_dropped": self.total_packets_dropped,
            "global_packet_loss_rate": round(self.global_packet_loss_rate, 4),
            "average_latency_ms": round(self.average_latency_ms, 2),
            "average_jitter_ms": round(self.average_jitter_ms, 2),
            "sla_compliance_rate": round(self.sla_compliance_rate, 4),
            "active_incidents_count": self.active_incidents_count,
            "links": {k: vars(v) for k, v in self.links.items()},
            "nodes": {k: vars(v) for k, v in self.nodes.items()},
            "flows": {k: vars(v) for k, v in self.flows.items()},
        }
