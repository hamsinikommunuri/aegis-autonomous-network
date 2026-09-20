"""
AEGIS Congestion-Aware Dynamic Routing Algorithm
Computes optimal forwarding paths using a multi-metric cost function:
Cost = w_latency * latency + w_congestion * M/M/1(utilization) + w_loss * loss + w_hop * hops
"""
import heapq
from typing import List, Optional, Dict, Any, Set
from .base import RoutingAlgorithm


class CongestionAwareRouter(RoutingAlgorithm):
    def __init__(
        self,
        latency_weight: float = 1.0,
        congestion_weight: float = 2.5,
        loss_weight: float = 10.0,
        hop_weight: float = 0.5,
    ):
        self.latency_weight = latency_weight
        self.congestion_weight = congestion_weight
        self.loss_weight = loss_weight
        self.hop_weight = hop_weight

    def calculate_link_cost(self, link: Any) -> float:
        """
        Calculates dynamic edge cost based on link state:
        Uses M/M/1 queueing delay multiplier as utilization approaches 100%.
        """
        if not link.is_operational():
            return float("inf")

        u = min(0.99, max(0.0, link.current_utilization))
        # Queueing expansion factor (approaches high value as u -> 1.0)
        congestion_factor = u / max(0.01, (1.0 - u))

        effective_loss = link.get_effective_loss_rate()

        cost = (
            (self.latency_weight * (link.current_latency_ms / 5.0))
            + (self.congestion_weight * congestion_factor)
            + (self.loss_weight * (effective_loss * 100.0))
            + (self.hop_weight * link.base_cost)
        )
        return max(0.1, cost)

    def compute_path(self, topology: Any, source: str, destination: str) -> Optional[List[str]]:
        if source == destination:
            return [source]

        src_node = topology.get_node(source)
        dst_node = topology.get_node(destination)
        if not src_node or not dst_node or not src_node.is_operational() or not dst_node.is_operational():
            return None

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

            for neighbor_id, link in topology.get_out_links(u).items():
                if not link.is_operational():
                    continue

                v_node = topology.get_node(neighbor_id)
                if not v_node or not v_node.is_operational():
                    continue

                edge_cost = self.calculate_link_cost(link)
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
