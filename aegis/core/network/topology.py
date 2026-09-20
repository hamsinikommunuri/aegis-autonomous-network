"""
AEGIS Topology Manager
Maintains graph structure of nodes and links, graph queries, state modifications,
and factory methods for realistic network topologies.
"""
from typing import Dict, List, Optional, Tuple, Set, Any
import copy
from .node import Node, NodeType, NodeStatus
from .link import Link, LinkStatus, NetworkInterface
from ..routing.dijkstra import DijkstraRouter


class Topology:
    def __init__(self, name: str = "AEGIS-Virtual-Network"):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[str, Link] = {}  # link_id -> Link
        # Adjacency structures: node_id -> {neighbor_id: link}
        self.adj_out: Dict[str, Dict[str, Link]] = {}
        self.adj_in: Dict[str, Dict[str, Link]] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adj_out:
            self.adj_out[node.id] = {}
        if node.id not in self.adj_in:
            self.adj_in[node.id] = {}

    def add_link(self, link: Link, bidirectional: bool = True) -> None:
        self.links[link.id] = link
        
        # Ensure endpoints exist in adjacency tables
        if link.source not in self.adj_out:
            self.adj_out[link.source] = {}
        if link.destination not in self.adj_in:
            self.adj_in[link.destination] = {}
            
        self.adj_out[link.source][link.destination] = link
        self.adj_in[link.destination][link.source] = link

        if bidirectional:
            rev_id = f"{link.destination}-{link.source}"
            if rev_id not in self.links:
                rev_link = Link(
                    id=rev_id,
                    source=link.destination,
                    destination=link.source,
                    bandwidth_bps=link.bandwidth_bps,
                    propagation_delay_ms=link.propagation_delay_ms,
                    loss_rate=link.loss_rate,
                    error_rate=link.error_rate,
                    base_cost=link.base_cost,
                    operational_cost=link.operational_cost,
                    status=link.status,
                    queue_capacity_packets=link.queue_capacity_packets,
                )
                self.links[rev_id] = rev_link
                if link.destination not in self.adj_out:
                    self.adj_out[link.destination] = {}
                if link.source not in self.adj_in:
                    self.adj_in[link.source] = {}
                self.adj_out[link.destination][link.source] = rev_link
                self.adj_in[link.source][link.destination] = rev_link

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_link(self, link_id: str) -> Optional[Link]:
        return self.links.get(link_id)

    def get_link_between(self, src: str, dst: str) -> Optional[Link]:
        return self.adj_out.get(src, {}).get(dst)

    def get_out_links(self, node_id: str) -> Dict[str, Link]:
        return self.adj_out.get(node_id, {})

    def get_in_links(self, node_id: str) -> Dict[str, Link]:
        return self.adj_in.get(node_id, {})

    def set_link_status(self, link_id: str, status: LinkStatus) -> bool:
        link = self.get_link(link_id)
        if link:
            link.status = status
            # Also update reverse link if exists
            rev_link = self.get_link_between(link.destination, link.source)
            if rev_link:
                rev_link.status = status
            return True
        return False

    def set_node_status(self, node_id: str, status: NodeStatus) -> bool:
        node = self.get_node(node_id)
        if node:
            node.status = status
            node.update_health()
            return True
        return False

    def find_k_shortest_paths(self, source: str, destination: str, k: int = 3) -> List[List[str]]:
        """Yen's K-Shortest Paths algorithm using DijkstraRouter."""
        router = DijkstraRouter()
        first_path = router.compute_path(self, source, destination)
        if not first_path:
            return []

        A = [first_path]
        B: List[Tuple[float, List[str]]] = []

        for i in range(1, k):
            prev_path = A[-1]
            for j in range(len(prev_path) - 1):
                spur_node = prev_path[j]
                root_path = prev_path[:j + 1]

                # Temporarily disable edges in previous paths sharing same root
                disabled_links: List[Link] = []
                for p in A:
                    if len(p) > j and p[:j + 1] == root_path:
                        edge = self.get_link_between(p[j], p[j + 1])
                        if edge and edge.is_operational():
                            edge.status = LinkStatus.DOWN
                            disabled_links.append(edge)

                spur_path = router.compute_path(self, spur_node, destination)
                if spur_path:
                    total_path = root_path[:-1] + spur_path
                    if total_path not in [p for _, p in B] and total_path not in A:
                        # Path cost calculation
                        cost = float(len(total_path))
                        B.append((cost, total_path))

                # Restore disabled links
                for edge in disabled_links:
                    edge.status = LinkStatus.UP

            if not B:
                break
            B.sort(key=lambda x: x[0])
            best_cand = B.pop(0)[1]
            A.append(best_cand)

        return A

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "links": {k: v.to_dict() for k, v in self.links.items()},
        }

    @classmethod
    def create_enterprise_isp_topology(cls) -> "Topology":
        """
        Creates a rich, multi-tiered Enterprise Core/Distribution ISP topology:
        - 2 Core Routers (CR1, CR2) with 10Gbps backbone
        - 4 Distribution Routers (DR1 North, DR2 East, DR3 South, DR4 West) with 1Gbps links
        - 2 Access Switches / Edge (AS1, AS2)
        - 2 Servers (SVR-DC1 Primary, SVR-DC2 Backup)
        - 2 Host Clients (HOST-A, HOST-B)
        """
        topo = cls(name="Enterprise-ISP-MultiTier")

        # 1. Add Nodes with layout coordinates (0..800 scale for UI)
        nodes_data = [
            ("HOST-A", "Client Host Alpha", NodeType.HOST, 100, 180),
            ("HOST-B", "Client Host Beta", NodeType.HOST, 100, 420),
            ("AS1", "Access Switch 1", NodeType.SWITCH, 220, 180),
            ("AS2", "Access Switch 2", NodeType.SWITCH, 220, 420),
            ("DR1", "Distribution North", NodeType.ROUTER, 380, 120),
            ("DR2", "Distribution South", NodeType.ROUTER, 380, 480),
            ("CR1", "Core Backbone Primary", NodeType.ROUTER, 520, 200),
            ("CR2", "Core Backbone Secondary", NodeType.ROUTER, 520, 400),
            ("DR3", "Distribution East", NodeType.ROUTER, 660, 200),
            ("DR4", "Distribution West", NodeType.ROUTER, 660, 400),
            ("SVR-1", "App Cluster Primary", NodeType.SERVER, 800, 200),
            ("SVR-2", "Storage Backup Vault", NodeType.SERVER, 800, 400),
        ]

        for nid, name, ntype, x, y in nodes_data:
            node = Node(id=nid, name=name, node_type=ntype, x=x, y=y)
            topo.add_node(node)

        # 2. Add Links with realistic bandwidths and propagation delays
        # Access links: 100 Mbps, 1ms
        topo.add_link(Link(id="HOST-A-AS1", source="HOST-A", destination="AS1", bandwidth_bps=100_000_000, propagation_delay_ms=1.0))
        topo.add_link(Link(id="HOST-B-AS2", source="HOST-B", destination="AS2", bandwidth_bps=100_000_000, propagation_delay_ms=1.0))
        
        # Access to Distribution: 1 Gbps, 2ms
        topo.add_link(Link(id="AS1-DR1", source="AS1", destination="DR1", bandwidth_bps=1_000_000_000, propagation_delay_ms=2.0))
        topo.add_link(Link(id="AS1-DR2", source="AS1", destination="DR2", bandwidth_bps=1_000_000_000, propagation_delay_ms=2.5))
        topo.add_link(Link(id="AS2-DR1", source="AS2", destination="DR1", bandwidth_bps=1_000_000_000, propagation_delay_ms=2.5))
        topo.add_link(Link(id="AS2-DR2", source="AS2", destination="DR2", bandwidth_bps=1_000_000_000, propagation_delay_ms=2.0))

        # Distribution to Core: 2 Gbps, 4ms
        topo.add_link(Link(id="DR1-CR1", source="DR1", destination="CR1", bandwidth_bps=2_000_000_000, propagation_delay_ms=4.0))
        topo.add_link(Link(id="DR1-CR2", source="DR1", destination="CR2", bandwidth_bps=2_000_000_000, propagation_delay_ms=5.0))
        topo.add_link(Link(id="DR2-CR1", source="DR2", destination="CR1", bandwidth_bps=2_000_000_000, propagation_delay_ms=5.0))
        topo.add_link(Link(id="DR2-CR2", source="DR2", destination="CR2", bandwidth_bps=2_000_000_000, propagation_delay_ms=4.0))

        # Core Backbone Cross-Link: 10 Gbps, 1ms
        topo.add_link(Link(id="CR1-CR2", source="CR1", destination="CR2", bandwidth_bps=10_000_000_000, propagation_delay_ms=1.0))

        # Core to Datacenter Distribution: 2 Gbps, 4ms
        topo.add_link(Link(id="CR1-DR3", source="CR1", destination="DR3", bandwidth_bps=2_000_000_000, propagation_delay_ms=4.0))
        topo.add_link(Link(id="CR2-DR4", source="CR2", destination="DR4", bandwidth_bps=2_000_000_000, propagation_delay_ms=4.0))
        # Cross links between core and distribution
        topo.add_link(Link(id="CR1-DR4", source="CR1", destination="DR4", bandwidth_bps=1_000_000_000, propagation_delay_ms=6.0))
        topo.add_link(Link(id="CR2-DR3", source="CR2", destination="DR3", bandwidth_bps=1_000_000_000, propagation_delay_ms=6.0))

        # Datacenter Distribution to Servers: 1 Gbps, 1ms
        topo.add_link(Link(id="DR3-SVR-1", source="DR3", destination="SVR-1", bandwidth_bps=1_000_000_000, propagation_delay_ms=1.0))
        topo.add_link(Link(id="DR4-SVR-2", source="DR4", destination="SVR-2", bandwidth_bps=1_000_000_000, propagation_delay_ms=1.0))
        # Inter-DC Sync Link
        topo.add_link(Link(id="DR3-DR4", source="DR3", destination="DR4", bandwidth_bps=1_000_000_000, propagation_delay_ms=2.0))

        return topo
