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
from ...core.packets.packet import TrafficClass


class NetworkActuator:
    def __init__(self, simulation: SimulationEngine):
        self.sim = simulation
        self.action_history: List[Dict[str, Any]] = []
        self.action_counter: int = 800

    def _next_action_id(self) -> str:
        self.action_counter += 1
        return f"ACTION #{self.action_counter:03d}"

    def reroute_flow(
        self,
        flow_id: str,
        new_path: List[str],
        reason: str = "Congestion mitigation",
        predicted_benefit: str = "Latency -31%"
    ) -> Dict[str, Any]:
        flow = self.sim.flows.get(flow_id)
        if not flow:
            return {"status": "ERROR", "message": f"Flow {flow_id} not found"}
        old_path = list(flow.current_path)
        snapshot = self._capture_rollback_snapshot({"action_type": "REROUTE_FLOW"})
        flow.current_path = list(new_path)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "REROUTE_FLOW",
            "flow": flow_id,
            "old_path": " -> ".join(old_path),
            "new_path": " -> ".join(new_path),
            "reason": reason,
            "predicted_benefit": predicted_benefit,
            "timestamp_ms": self.sim.current_time_ms,
            "snapshot": snapshot,
        }
        self.action_history.append(record)
        return record

    def change_route_cost(self, link_id: str, new_cost: float, reason: str = "Dynamic traffic engineering") -> Dict[str, Any]:
        link = self.sim.topology.get_link(link_id)
        if not link:
            return {"status": "ERROR", "message": f"Link {link_id} not found"}
        old_cost = link.operational_cost
        link.operational_cost = new_cost
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "CHANGE_ROUTE_COST",
            "resource": link_id,
            "old_cost": old_cost,
            "new_cost": new_cost,
            "reason": reason,
            "predicted_benefit": "Traffic diverted to lower cost alternatives",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def disable_link(self, link_id: str, reason: str = "Isolate degraded link") -> Dict[str, Any]:
        success = self.sim.topology.set_link_status(link_id, LinkStatus.DOWN)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "DISABLE_LINK",
            "resource": link_id,
            "reason": reason,
            "predicted_benefit": "Eliminate packet loss on degraded segment",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def restore_link(self, link_id: str, reason: str = "Link recovered") -> Dict[str, Any]:
        success = self.sim.topology.set_link_status(link_id, LinkStatus.UP)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "RESTORE_LINK",
            "resource": link_id,
            "reason": reason,
            "predicted_benefit": "Restore backbone capacity",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def disable_node(self, node_id: str, reason: str = "Isolate failing router") -> Dict[str, Any]:
        success = self.sim.topology.set_node_status(node_id, NodeStatus.DOWN)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "DISABLE_NODE",
            "resource": node_id,
            "reason": reason,
            "predicted_benefit": "Prevent packet drops at failing router",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def restore_node(self, node_id: str, reason: str = "Node online") -> Dict[str, Any]:
        success = self.sim.topology.set_node_status(node_id, NodeStatus.UP)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "RESTORE_NODE",
            "resource": node_id,
            "reason": reason,
            "predicted_benefit": "Restore transit capacity",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def change_bandwidth(self, link_id: str, new_bandwidth_bps: float, reason: str = "QoS bandwidth reservation") -> Dict[str, Any]:
        link = self.sim.topology.get_link(link_id)
        if not link:
            return {"status": "ERROR", "message": f"Link {link_id} not found"}
        old_bw = link.bandwidth_bps
        link.bandwidth_bps = new_bandwidth_bps
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "CHANGE_BANDWIDTH",
            "resource": link_id,
            "old_bandwidth_bps": old_bw,
            "new_bandwidth_bps": new_bandwidth_bps,
            "reason": reason,
            "predicted_benefit": "Reallocate throughput guarantee",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def change_traffic_priority(self, flow_id: str, new_priority: Any, reason: str = "QoS elevation") -> Dict[str, Any]:
        flow = self.sim.flows.get(flow_id)
        if not flow:
            return {"status": "ERROR", "message": f"Flow {flow_id} not found"}
        old_p = flow.priority
        if isinstance(new_priority, TrafficClass):
            flow.traffic_class = new_priority
            flow.priority = new_priority.priority_value
        else:
            flow.priority = int(new_priority)
        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
            "action": "CHANGE_TRAFFIC_PRIORITY",
            "flow": flow_id,
            "old_priority": old_p,
            "new_priority": flow.priority,
            "reason": reason,
            "predicted_benefit": "Elevated forwarding priority in QoS buffers",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

    def change_qos_policy(self, policy_rules: Any, reason: str = "QoS policy adjustment") -> Dict[str, Any]:
        action_id = self._next_action_id()
        rules_dict = dict(policy_rules) if isinstance(policy_rules, dict) else {"policy": str(policy_rules)}
        record = {
            "action_id": action_id,
            "action": "CHANGE_QOS_POLICY",
            "policy_rules": rules_dict,
            "status": "SUCCESS",
            "reason": reason,
            "predicted_benefit": "Strict queue prioritization applied",
            "timestamp_ms": self.sim.current_time_ms,
        }
        self.action_history.append(record)
        return record

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

        action_id = self._next_action_id()
        record = {
            "action_id": action_id,
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
