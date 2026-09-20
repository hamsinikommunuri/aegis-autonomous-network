"""
AEGIS Node Models
Defines Host, Router, Switch, and Server nodes, their queuing and processing capacities,
interfaces, and health metrics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from .link import NetworkInterface


class NodeType(str, Enum):
    HOST = "HOST"
    ROUTER = "ROUTER"
    SWITCH = "SWITCH"
    SERVER = "SERVER"


class NodeStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"


@dataclass
class Node:
    id: str
    name: str
    node_type: NodeType
    status: NodeStatus = NodeStatus.UP
    processing_capacity_pps: float = 100_000.0  # Max packets processed per sec
    queue_capacity_packets: int = 500
    interfaces: Dict[str, NetworkInterface] = field(default_factory=dict)
    routing_table: Dict[str, str] = field(default_factory=dict)  # dest_node_id -> next_hop_node_id
    
    # Coordinates for visualization
    x: float = 0.0
    y: float = 0.0

    # Operational metrics
    cpu_utilization: float = 0.05       # [0.0, 1.0]
    memory_utilization: float = 0.10    # [0.0, 1.0]
    current_queue_depth: int = 0
    forwarded_packets: int = 0
    dropped_packets: int = 0
    health_score: float = 1.0           # [0.0, 1.0]

    def is_operational(self) -> bool:
        return self.status != NodeStatus.DOWN

    def add_interface(self, interface: NetworkInterface) -> None:
        self.interfaces[interface.name] = interface

    def update_health(self) -> None:
        """Calculates node health score based on operational status, CPU, memory, and queue pressure."""
        if self.status == NodeStatus.DOWN:
            self.health_score = 0.0
            return
        
        degradation_factor = 0.5 if self.status == NodeStatus.DEGRADED else 1.0
        queue_ratio = min(1.0, self.current_queue_depth / max(1, self.queue_capacity_packets))
        penalty = (0.35 * self.cpu_utilization) + (0.25 * self.memory_utilization) + (0.40 * queue_ratio)
        self.health_score = max(0.0, min(1.0, (1.0 - penalty) * degradation_factor))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "status": self.status.value,
            "processing_capacity_pps": self.processing_capacity_pps,
            "queue_capacity_packets": self.queue_capacity_packets,
            "interfaces": {k: v.to_dict() for k, v in self.interfaces.items()},
            "routing_table": dict(self.routing_table),
            "x": self.x,
            "y": self.y,
            "cpu_utilization": round(self.cpu_utilization, 4),
            "memory_utilization": round(self.memory_utilization, 4),
            "current_queue_depth": self.current_queue_depth,
            "forwarded_packets": self.forwarded_packets,
            "dropped_packets": self.dropped_packets,
            "health_score": round(self.health_score, 4),
        }
