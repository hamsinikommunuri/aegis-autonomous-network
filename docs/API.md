# AEGIS — REST & WebSocket API Reference

The AEGIS backend exposes a RESTful control plane and real-time WebSocket telemetry stream via FastAPI.

Default Server Port: `8000`  
Base URL: `http://localhost:8000`

---

## 1. Status & Control Endpoints

### `GET /api/status`
Returns high-level runtime status, simulation clock, autonomous state, and incident counts.
```json
{
  "status": "RUNNING",
  "simulation_time_ms": 3400.0,
  "tick_count": 34,
  "autonomous_mode": true,
  "active_incidents": 1,
  "resolved_incidents": 3
}
```

### `POST /api/simulation/step?count={n}`
Advances the discrete simulation by `n` intervals (each 100ms).

### `POST /api/simulation/reset`
Resets topology, flows, link buffers, and incident states to nominal baseline.

### `POST /api/simulation/toggle-autonomous`
Toggles closed-loop self-healing on or off.

---

## 2. Telemetry & Topology Endpoints

### `GET /api/topology`
Returns all nodes with coordinates and operational statuses, plus all physical/logical links.

### `GET /api/telemetry/snapshot`
Retrieves latest point-in-time snapshot of the entire virtual network.

### `GET /api/telemetry/history?history_points=60`
Retrieves rolling time-series arrays for global throughput, latency, loss, and SLA rates.

---

## 3. Incident & Recovery Endpoints

### `GET /api/incidents`
Returns active incidents with their closed-loop lifecycle stages, evidence, and historical memory.

### `POST /api/inject/failure`
Injects controlled physical/logical faults.
```json
{
  "action": "bandwidth_reduction",
  "target": "DR1-CR1",
  "value": 25000000.0
}
```
Supported actions: `link_failure`, `node_failure`, `packet_loss`, `latency_spike`, `bandwidth_reduction`, `traffic_surge`.

### `POST /api/inject/reset`
Clears all injected faults and restores nominal baseline state.

### `POST /api/scenarios/run`
Loads pre-defined scenarios (`SCENARIO_A` through `SCENARIO_F`).

### `POST /api/benchmarks/run`
Executes head-to-head empirical benchmark trial.
```json
{
  "scenario_type": "LINK_FAILURE",
  "simulation_steps": 35
}
```

---

## 4. Real-time Telemetry WebSocket

### `WebSocket /ws/stream`
Streams serialized `NetworkGlobalSnapshot` and active incidents at ~8 Hz for low-latency Network Operations Center (NOC) dashboards.
