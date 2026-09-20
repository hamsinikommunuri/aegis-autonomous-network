"""
AEGIS Network Actuator
Executes planned reconfigurations on the virtual network simulation and tracks mutation state
for atomic rollback.
"""
from typing import Dict, List, Any, Optional
import copy
from ...core.simulation.engine import SimulationEngine
from ...core.network.link import LinkStatus
from ...core.network.node import NodeStatus
from ...core.routing.dijkstra import DijkstraRouter


class NetworkActuator:
    def __init__(self, simulation: SimulationEngine):
        self.sim = simulation
        self.action_history: List[Dict[str, Any]] = []

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a recovery plan on the network simulation.
        Captures pre-execution snapshot for rollback and returns execution result record.
        """
        action_type = plan.get("action_type")
        params = plan.get("action_params", {})

        # Snapshot state before applying changes
        snapshot = self._capture_rollback_snapshot(plan)

        executed_actions: List[str] = []

        if action_type == "REROUTE_FLOWS":
            reroutes = params.get("reroutes", [])
            for r in reroutes:
                fid = r["flow_id"]
                new_path = r["new_path"]
                flow = self.sim.flows.get(fid)
                if flow:
                    old_path = list(flow.current_path)
                    flow.current_path = list(new_path)
                    executed_actions.append(f"Rerouted flow {fid}: {' -> '.join(old_path)} ==> {' -> '.join(new_path)}")

        elif action_type == "ISOLATE_RESOURCE":
            res = params.get("resource", "")
            if "-" in res:
                self.sim.topology.set_link_status(res, LinkStatus.DOWN)
                executed_actions.append(f"Administratively isolated degraded link {res}")
            else:
                self.sim.topology.set_node_status(res, NodeStatus.DOWN)
                executed_actions.append(f"Administratively isolated failing node {res}")
            # Recompute routes bypassing the isolated element
            router = DijkstraRouter()
            for flow in self.sim.flows.values():
                alt_p = router.compute_path(self.sim.topology, flow.source_id, flow.dest_id)
                if alt_p:
                    flow.current_path = alt_p
                    executed_actions.append(f"Flow {flow.id} converged to {' -> '.join(alt_p)}")

        elif action_type == "SHAPE_TRAFFIC":
            fids = params.get("flow_ids", [])
            ratio = params.get("throttle_ratio", 0.50)
            for fid in fids:
                flow = self.sim.flows.get(fid)
                if flow:
                    old_demand = flow.demand_bps
                    flow.demand_bps = flow.demand_bps * ratio
                    executed_actions.append(f"Throttled flow {fid} from {round(old_demand / 1e6, 1)}Mbps to {round(flow.demand_bps / 1e6, 1)}Mbps")

        elif action_type == "RECOMPUTE_ROUTES":
            self.sim.recompute_all_routes()
            executed_actions.append("Recomputed all routes globally")

        record = {
            "plan_id": plan.get("id"),
            "action_type": action_type,
            "actions_applied": executed_actions,
            "timestamp_ms": self.sim.current_time_ms,
            "snapshot": snapshot,
        }
        self.action_history.append(record)
        return record

    def rollback_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restores network topology and flow state to the captured snapshot."""
        # 1. Restore flow paths and demands
        for fid, f_data in snapshot.get("flows", {}).items():
            flow = self.sim.flows.get(fid)
            if flow:
                flow.current_path = list(f_data["path"])
                flow.demand_bps = f_data["demand_bps"]

        # 2. Restore link statuses
        for lid, status_str in snapshot.get("links", {}).items():
            link = self.sim.topology.get_link(lid)
            if link:
                link.status = LinkStatus(status_str)

        # 3. Restore node statuses
        for nid, status_str in snapshot.get("nodes", {}).items():
            node = self.sim.topology.get_node(nid)
            if node:
                node.status = NodeStatus(status_str)

    def _capture_rollback_snapshot(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "flows": {
                fid: {"path": list(f.current_path), "demand_bps": f.demand_bps}
                for fid, f in self.sim.flows.items()
            },
            "links": {
                lid: l.status.value for lid, l in self.sim.topology.links.items()
            },
            "nodes": {
                nid: n.status.value for nid, n in self.sim.topology.nodes.items()
            },
        }
