# AEGIS — System Architecture & Design Specification

## 1. Abstract & Architectural Objectives

**AEGIS** (*Autonomous Network Intelligence & Self-Healing System*) is an enterprise-grade autonomous network operations platform and experimentation environment designed to close the loop between network telemetry observation and real-time physical/logical remediation. 

Rather than relying on human operator triage or disjointed rule scripts, AEGIS enforces a continuous nine-stage control cycle:

```
OBSERVE ──> DETECT ──> DIAGNOSE ──> PREDICT ──> PLAN ──> ACT ──> VERIFY ──> ROLLBACK / ADAPT ──> LEARN
```

Every displayed metric, anomaly event, candidate plan, and verification diff originates directly from a deterministic discrete simulation engine with multi-queue QoS buffers, M/M/1 queuing models, Yen's K-shortest paths, and dynamic multi-metric routing.

---

## 2. Structural Decomposition

The system is decomposed into five primary decoupled subsystems:

```
aegis/
├── core/                   # Virtual Network & Discrete Simulation Engine
│   ├── network/            # Nodes (Host/Switch/Router/Server), Links, Interfaces, Topology
│   ├── packets/            # Simulated discrete packets, QoS Multi-Queue Buffers
│   ├── flows/              # Traffic flows, bandwidth demand, SLAs, PRNG traffic generator
│   ├── routing/            # Dijkstra Shortest Path, Congestion-Aware Multi-Metric Router
│   └── simulation/         # Discrete-time simulation clock, hop-by-hop forwarding, delays
│
├── telemetry/              # High-Speed Telemetry Aggregation
│   ├── collectors/         # Link, node, and flow state extraction
│   ├── metrics/            # Point-in-time snapshots
│   └── time_series/        # Ring buffer time series, rolling mean, variance, derivatives
│
├── intelligence/           # Anomaly Detection, RCA & Predictive Forecaster
│   ├── anomaly_detection/  # Multi-metric thresholding, EWMA, rate-of-change correlation
│   ├── diagnosis/          # Bayesian/Rule-based Root Cause Analysis (RCA) engine
│   └── prediction/         # Ordinary Least Squares (OLS) trend forecasting & time-to-breach
│
├── recovery/               # Closed-Loop Autonomous Healing Subsystem
│   ├── incident.py         # Incident lifecycle state machine
│   ├── planner/            # Multi-objective candidate plan generation & scoring
│   ├── policies/           # QoS priority preservation rules (CRITICAL > REAL_TIME > NORMAL > BULK)
│   ├── actuator/           # Physical/logical mutation execution & rollback snapshotting
│   ├── verification/       # Post-mitigation settle window verification & collateral check
│   ├── rollback/           # Automated atomic rollback manager
│   └── memory/             # Persistent incident memory and historical efficacy metrics
│
├── experiments/            # Experimentation & Empirical Benchmarks
│   ├── failure_injection/  # Link cut, node crash, BER loss, latency spike, surge
│   ├── scenarios/          # Scenarios A through F (congestion, cascading, rollback)
│   └── benchmarks/         # Head-to-head evaluation (Baseline vs Reactive vs Predictive)
│
├── api/                    # REST API & Real-time WebSockets (FastAPI + Uvicorn)
└── frontend/               # Network Operations Center (NOC) UI (React + TypeScript + Vite)
```

---

## 3. The Closed-Loop Lifecycle Subsystems

### Stage 1: OBSERVE
On each discrete simulation interval (default 100ms), `TelemetryCollector` extracts link utilization, queue depth, latency (propagation + queue delay), packet loss rate, node CPU/health, and end-to-end flow SLAs. All values are appended to a ring buffer `TimeSeriesBuffer`.

### Stage 2: DETECT
`AnomalyDetector` scans current state and time-series buffers using deterministic threshold bounds, moving baselines ($Z$-scores), and numerical derivatives ($\frac{d\text{utilization}}{dt}$). Multi-metric evidence is correlated to generate a composite `AnomalyScore` $[0.0 \dots 1.0]$.

### Stage 3: DIAGNOSE
`RootCauseAnalyzer` inspects topological context, load distributions across parallel trunks, and error signatures to distinguish between:
- `PHYSICAL_LINK_CUT_OR_PORT_SHUTDOWN`
- `ROUTER_HARDWARE_OR_POWER_FAILURE`
- `PHYSICAL_LAYER_OPTICAL_OR_BIT_ERROR_DEGRADATION`
- `LINK_BOTTLENECK_CONGESTION_AND_SUBOPTIMAL_FLOW_DISTRIBUTION`
- `CASCADING_SYSTEMIC_NETWORK_CONGESTION`

### Stage 4: PREDICT
`DegradationPredictor` applies Ordinary Least Squares (OLS) linear regression over sliding windows to forecast the exact intervals remaining before link saturation:
$$\Delta t_{\text{breach}} = \frac{U_{\text{threshold}} - U_{\text{current}}}{m}$$
If $\Delta t_{\text{breach}} \le \text{Horizon}$, AEGIS issues a proactive degradation alert before packet loss or queue drops occur.

### Stage 5: PLAN
`RecoveryPlanner` generates multiple candidate remediation plans (Plan A: Selective QoS Offload, Plan B: Dynamic Congestion Rebalancing, Plan C: Resource Isolation, Plan D: Ingress Traffic Shaping). Each plan evaluates predicted loss reduction, predicted latency change, affected flows, risk score, and QoS preservation.

### Stage 6: ACT
`NetworkActuator` captures an atomic network snapshot (flow paths, link statuses, node states) and applies the selected plan mutations to the virtual network.

### Stage 7: VERIFY
`VerificationEngine` observes network metrics across a stabilization settle window (3 intervals). It verifies that:
1. Target bottleneck utilization dropped below threshold ($\le 82\%$).
2. Packet loss is cleared.
3. No collateral degradation occurred on secondary detour paths ($\le 92\%$).

### Stage 8: ROLLBACK / ADAPT
If verification fails (or collateral congestion is triggered), `RollbackManager` immediately reverts the network configuration to the captured snapshot, logs a `VERIFICATION_FAILED` event, marks the candidate plan as `FAILED`, and automatically deploys the next best candidate plan.

### Stage 9: LEARN
Upon verified resolution, `IncidentMemory` stores the complete incident record: detected anomalies, RCA diagnosis, candidate evaluations, executed mutations, verification deltas, and recovery duration to compute system MTTR and strategy efficacy.
