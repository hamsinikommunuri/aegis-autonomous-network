"""
AEGIS Dijkstra Routing Algorithm
Standard shortest-path routing algorithm with link availability checks and priority queue.
"""
import heapq
from typing import List, Optional, Dict, Any, Set
from .base import RoutingAlgorithm


class DijkstraRouter(RoutingAlgorithm):
    def __init__(self, metric: str = "base_cost"):
        """
        metric: 'base_cost', 'hop', or 'propagation_delay_ms'
        """
        self.metric = metric

    def compute_path(self, topology: Any, source: str, destination: str) -> Optional[List[str]]:
        if source == destination:
            return [source]
        
        # Check source and destination operational status
        src_node = topology.get_node(source)
        dst_node = topology.get_node(destination)
        if not src_node or not dst_node or not src_node.is_operational() or not dst_node.is_operational():
            return None

        # Priority queue stores tuples: (cumulative_cost, current_node_id, path_so_far)
        pq = [(0.0, source, [source])]
        visited: Set[str] = set()
        min_costs: Dict[str, float] = {source: 0.0}

        while pq:
            cost, u, path = heapq.heappop(pq)

            if u in visited:
                continue
            visited.add(u)

            if u == destination:
                return path

            # Explore neighbors via operational links
            for neighbor_id, link in topology.get_out_links(u).items():
                if not link.is_operational():
                    continue

                v_node = topology.get_node(neighbor_id)
                if not v_node or not v_node.is_operational():
                    continue

                if self.metric == "hop":
                    edge_cost = 1.0
                elif self.metric == "propagation_delay_ms":
                    edge_cost = link.propagation_delay_ms
                else:
                    edge_cost = link.base_cost

                new_cost = cost + edge_cost
                if neighbor_id not in min_costs or new_cost < min_costs[neighbor_id]:
                    min_costs[neighbor_id] = new_cost
                    heapq.heappush(pq, (new_cost, neighbor_id, path + [neighbor_id]))

        return None

    def compute_all_paths(self, topology: Any) -> Dict[str, Dict[str, List[str]]]:
        all_paths: Dict[str, Dict[str, List[str]]] = {}
        for src in topology.nodes:
            all_paths[src] = {}
            for dst in topology.nodes:
                if src != dst:
                    path = self.compute_path(topology, src, dst)
                    if path:
                        all_paths[src][dst] = path
        return all_paths
