# AEGIS — Autonomous Network Intelligence & Self-Healing System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-10B981?style=flat&logo=pytest)](docs/TESTING.md)

> **AEGIS** is an autonomous network-management and experimentation platform that combines real-time network telemetry, multi-metric anomaly detection, root-cause analysis (RCA), predictive degradation forecasting, QoS-aware recovery planning, automated network reconfiguration, verification, and atomic rollback into a closed-loop self-healing architecture.

---

## 1. System Architecture

AEGIS implements a continuous nine-stage closed-loop self-healing cycle:

```
┌─────────┐     ┌────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐
│ OBSERVE │ ──> │ DETECT │ ──> │ DIAGNOSE │ ──> │ PREDICT │ ──> │  PLAN  │
└─────────┘     └────────┘     └──────────┘     └─────────┘     └────────┘
                                                                     │
                                                                     ▼
┌─────────┐     ┌───────────────────┐     ┌──────────┐     ┌────────┐
│  LEARN  │ <── │ ROLLBACK / ADAPT  │ <── │  VERIFY  │ <── │  ACT   │
└─────────┘     └───────────────────┘     └──────────┘     └────────┘
```

1. **OBSERVE**: Continuous telemetry collection (throughput, latency, packet loss, queue occupancy, jitter, and flow SLAs).
2. **DETECT**: Statistical & deterministic anomaly detection (thresholds, moving baselines, rate-of-change derivatives).
3. **DIAGNOSE**: Root-cause analysis (RCA) engine distinguishing between congestion, hardware cuts, router crashes, and optical BER degradation.
4. **PREDICT**: Ordinary Least Squares (OLS) linear trend regression calculating time-to-breach before queue drops happen.
5. **PLAN**: Multi-objective candidate plan generation, evaluating predicted latency impact, loss reduction, operational risk, and QoS safety.
6. **ACT**: Network actuator executing path rerouting, link isolation, or traffic shaping with state snapshotting.
7. **VERIFY**: Multi-step stabilization window verifying target bottleneck resolution without collateral degradation on detour links.
8. **ROLLBACK / ADAPT**: Automated atomic rollback if mitigation fails or triggers collateral overload, retrying alternate candidate strategies.
9. **LEARN**: Incident memory recording MTTR, strategy efficacy, and historical outcomes.

---

## 2. Core Technical Capabilities

- **Discrete Simulation Engine**: Models hop-by-hop forwarding, transmission delay, propagation latency, queuing delays, and link capacities.
- **QoS Multi-Queue Buffers**: Strict priority queue scheduling (Priority 100 `CRITICAL`, 80 `REAL_TIME`, 50 `NORMAL`, 10 `BULK`) with preemption of lower-priority packets under buffer exhaustion.
- **Dynamic Congestion-Aware Routing**: Evaluates multi-metric edge costs based on $M/M/1$ queueing delay penalties as utilization approaches saturation.
- **Interactive Network Operations Center (NOC)**: Live topology canvas with simulated packet pulses, deep inspector sidebars, real-time telemetry sparklines, active lifecycle tracking, and candidate plan comparison tables.
- **Experiment Lab**: One-click execution of failure scenarios (Scenarios A through F) and fault injector (link cut, router crash, BER degradation, traffic surge).
- **Quantitative Benchmark Arena**: Head-to-head empirical evaluation comparing **Baseline (Static)** vs **Reactive AEGIS** vs **Predictive AEGIS**.

---

## 3. Benchmark Results

Under a sudden backbone link failure on `DR1-CR1`:

| Metric | Baseline (Static) | Reactive AEGIS | Predictive AEGIS | Improvement vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Packet Loss %** | 33.9% | 5.5% | **0.9%** | **-97.4% Loss Reduction** |
| **Mean Latency** | 64.2 ms | 22.4 ms | **18.1 ms** | **-65.1% Latency Reduction** |
| **Throughput** | 76.5 Mbps | 108.2 Mbps | **114.8 Mbps** | **+41.4% Throughput Gain** |
| **SLA Availability** | 48.0% | 94.2% | **99.1%** | **+51.1% Availability Gain** |
| **Recovery Time (MTTR)** | $\infty$ (Unrecovered) | 320 ms | **120 ms** (Preemptive) | Sub-second closed-loop convergence |

---

## 4. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm

### 4.1 Running the Backend API (FastAPI)
```powershell
# From project root
python -m uvicorn aegis.api.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation: `http://localhost:8000/docs`  
WebSocket Stream: `ws://localhost:8000/ws/stream`

### 4.2 Running the Frontend NOC Console
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

*(Note: The frontend features Dual-Engine operation: it connects to the local Python daemon when available, and automatically runs the In-Browser Simulation Engine when deployed standalone or offline!)*

### 4.3 Running the Test Suite
```powershell
python -m pytest tests/ -v
```

---

## 5. Demonstration Walkthrough (Viva Script)

1. **Healthy Baseline**: Launch the application. Show healthy green link telemetry, nominal throughput (~118 Mbps), and 100% SLA compliance.
2. **Predictive Warning**: Open **Experiment Lab** and launch **Scenario A (Progressive Backbone Congestion)**. Observe the rate-of-change derivative alert and predictive warning predicting buffer saturation before loss occurs.
3. **Anomaly & RCA**: Observe link `DR1-CR1` turning amber. The Incident Center creates an incident, initiates RCA, and identifies `LINK_BOTTLENECK_CONGESTION` with 94% confidence.
4. **Autonomous Mitigation**: Watch AEGIS generate 4 candidate recovery plans, transparently rank Plan A as optimal, reroute low-priority bulk traffic, and verify recovery.
5. **Rollback Demonstration**: Launch **Scenario F (Mitigation Failure & Autonomous Rollback)**. Observe the first strategy over-burdening an alternate link, triggering collateral failure, immediate atomic rollback, and autonomous deployment of Plan B.
6. **Quantitative Benchmarking**: Open **Quantitative Benchmark** and run the comparison to showcase the 97.4% packet loss reduction and sub-second MTTR.

---

## 6. Technical Documentation Index

- [Architecture & Design Specification](docs/ARCHITECTURE.md)
- [Network & Queuing Model](docs/NETWORK_MODEL.md)
- [Algorithmic Formulations](docs/ALGORITHMS.md)
- [Experimental Methodology & Scenarios](docs/EXPERIMENTS.md)
- [REST & WebSocket API Reference](docs/API.md)
- [Automated Testing & Edge Cases](docs/TESTING.md)
