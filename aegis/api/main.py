"""
AEGIS REST API and WebSocket Server
Provides high-speed control, telemetry streaming, fault injection, scenario execution,
and benchmark analytics for the AEGIS Network Operations Center (NOC).
"""
import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.network.topology import Topology
from ..core.simulation.engine import SimulationEngine
from ..core.flows.flow import TrafficFlow
from ..core.packets.packet import TrafficClass
from ..telemetry.collectors.collector import TelemetryCollector
from ..recovery.orchestrator import AegisOrchestrator
from ..experiments.failure_injection.injector import FailureInjector
from ..experiments.scenarios.scenarios import ScenarioRunner
from ..experiments.benchmarks.benchmark_runner import BenchmarkRunner

app = FastAPI(
    title="AEGIS Autonomous Network Intelligence & Self-Healing API",
    description="REST & WebSocket API for autonomous network management, real-time telemetry, and closed-loop recovery.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Engine Instance
class AegisRuntime:
    def __init__(self):
        self.reset()

    def reset(self):
        self.topology = Topology.create_enterprise_isp_topology()
        self.sim = SimulationEngine(topology=self.topology, step_duration_ms=100.0, seed=42)

        # Standard traffic profile: CRITICAL, REAL_TIME, NORMAL, BULK
        self.sim.add_flow(TrafficFlow(
            id="f-voip-1", name="VoIP SIP Trunk", source_id="HOST-A", dest_id="SVR-1",
            traffic_class=TrafficClass.CRITICAL, demand_bps=12_000_000.0, latency_sla_ms=30.0, loss_sla_percent=0.5
        ))
        self.sim.add_flow(TrafficFlow(
            id="f-video-1", name="HD Video Stream", source_id="HOST-A", dest_id="SVR-1",
            traffic_class=TrafficClass.REAL_TIME, demand_bps=25_000_000.0, latency_sla_ms=45.0, loss_sla_percent=1.0
        ))
        self.sim.add_flow(TrafficFlow(
            id="f-web-1", name="HTTPS App Portal", source_id="HOST-B", dest_id="SVR-1",
            traffic_class=TrafficClass.NORMAL, demand_bps=35_000_000.0, latency_sla_ms=65.0, loss_sla_percent=2.0
        ))
        self.sim.add_flow(TrafficFlow(
            id="f-db-sync", name="Datacenter DB Backup", source_id="HOST-B", dest_id="SVR-2",
            traffic_class=TrafficClass.BULK, demand_bps=45_000_000.0, latency_sla_ms=120.0, loss_sla_percent=5.0
        ))

        self.telemetry = TelemetryCollector(self.sim)
        self.orchestrator = AegisOrchestrator(self.sim, self.telemetry, autonomous_mode=True)
        self.injector = FailureInjector(self.sim)
        self.scenario_runner = ScenarioRunner(self.orchestrator)
        self.benchmark_runner = BenchmarkRunner(step_duration_ms=100.0, seed=42)
        self.is_paused = False


runtime = AegisRuntime()


class FailureInjectionRequest(BaseModel):
    action: str  # link_failure, node_failure, packet_loss, latency_spike, bandwidth_reduction, traffic_surge
    target: str  # e.g. "DR1-CR1", "CR1", "f-web-1"
    value: Optional[float] = None


class ScenarioRequest(BaseModel):
    scenario_id: str  # SCENARIO_A .. SCENARIO_F


class BenchmarkRequest(BaseModel):
    scenario_type: str = "LINK_FAILURE"  # LINK_FAILURE, CONGESTION, ROUTER_FAILURE
    simulation_steps: int = 35


@app.get("/api/status")
def get_status():
    return {
        "status": "RUNNING" if not runtime.is_paused else "PAUSED",
        "simulation_time_ms": round(runtime.sim.current_time_ms, 2),
        "tick_count": runtime.sim.tick_count,
        "autonomous_mode": runtime.orchestrator.autonomous_mode,
        "active_incidents": len(runtime.orchestrator.active_incidents),
        "resolved_incidents": len(runtime.orchestrator.memory.history),
    }


@app.get("/api/topology")
def get_topology():
    return runtime.topology.to_dict()


@app.get("/api/telemetry/snapshot")
def get_telemetry_snapshot():
    snapshot = runtime.telemetry.get_latest_snapshot()
    if not snapshot:
        snapshot = runtime.telemetry.collect()
    return snapshot.to_dict()


@app.get("/api/telemetry/history")
def get_telemetry_history(history_points: int = 60):
    return runtime.telemetry.buffer.to_dict(max_history=history_points)


@app.get("/api/incidents")
def get_incidents():
    return {
        "active": {k: v.to_dict() for k, v in runtime.orchestrator.active_incidents.items()},
        "history": runtime.orchestrator.memory.get_all_incidents(),
        "stats": runtime.orchestrator.memory.get_efficacy_stats(),
    }


@app.post("/api/simulation/step")
def step_simulation(count: int = 1):
    results = []
    for _ in range(max(1, min(count, 50))):
        res = runtime.sim.step()
        results.append(res)
    return {"stepped": count, "current_time_ms": runtime.sim.current_time_ms}


@app.post("/api/simulation/reset")
def reset_simulation():
    runtime.reset()
    return {"message": "Simulation reset to nominal baseline state."}


@app.post("/api/simulation/toggle-autonomous")
def toggle_autonomous():
    runtime.orchestrator.autonomous_mode = not runtime.orchestrator.autonomous_mode
    return {"autonomous_mode": runtime.orchestrator.autonomous_mode}


@app.post("/api/inject/failure")
def inject_failure(req: FailureInjectionRequest):
    action = req.action.lower()
    target = req.target
    val = req.value

    if action == "link_failure":
        ok = runtime.injector.inject_link_failure(target)
    elif action == "node_failure":
        ok = runtime.injector.inject_node_failure(target)
    elif action == "packet_loss":
        ok = runtime.injector.inject_packet_loss(target, loss_rate=val or 0.15)
    elif action == "latency_spike":
        ok = runtime.injector.inject_latency_spike(target, extra_delay_ms=val or 75.0)
    elif action == "bandwidth_reduction":
        ok = runtime.injector.inject_bandwidth_reduction(target, new_bandwidth_bps=val or 20_000_000.0)
    elif action == "traffic_surge":
        ok = runtime.injector.inject_traffic_surge(target, multiplier=val or 4.0)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown injection action: {action}")

    if not ok:
        raise HTTPException(status_code=404, detail=f"Target resource {target} not found or invalid.")

    return {"message": f"Injected {action} on {target}", "success": True}


@app.post("/api/inject/reset")
def reset_injections():
    runtime.injector.reset_all_failures()
    return {"message": "All injected failures cleared and restored to nominal."}


@app.post("/api/scenarios/run")
def run_scenario(req: ScenarioRequest):
    info = runtime.scenario_runner.load_scenario(req.scenario_id)
    return info


@app.post("/api/benchmarks/run")
def run_benchmark(req: BenchmarkRequest):
    results = runtime.benchmark_runner.run_comparison(
        scenario_type=req.scenario_type,
        simulation_steps=req.simulation_steps
    )
    return results


@app.websocket("/ws/stream")
async def websocket_telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Advance simulation step if not paused
            if not runtime.is_paused:
                runtime.sim.step()

            snapshot = runtime.telemetry.get_latest_snapshot()
            data = {
                "snapshot": snapshot.to_dict() if snapshot else {},
                "active_incidents": {k: v.to_dict() for k, v in runtime.orchestrator.active_incidents.items()},
                "resolved_count": len(runtime.orchestrator.memory.history),
                "stats": runtime.orchestrator.memory.get_efficacy_stats(),
                "time_ms": runtime.sim.current_time_ms,
                "autonomous": runtime.orchestrator.autonomous_mode,
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.12)  # ~8 updates per second
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
