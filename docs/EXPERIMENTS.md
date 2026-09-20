# AEGIS — Experimental Methodology & Viva Benchmarks

## 1. Experimental Methodology

AEGIS was designed to defend technically in academic and systems evaluations. Rather than running anecdotal tests, AEGIS implements reproducible, seeded failure injection and benchmark trials comparing:
1. **Baseline**: Static Shortest-Path Routing without self-healing.
2. **Reactive AEGIS**: Anomaly detection $\to$ RCA $\to$ Dynamic Candidate Mitigation $\to$ Verification.
3. **Predictive AEGIS**: Trend forecasting $\to$ Proactive offloading before queue saturation.

---

## 2. Benchmark Evaluation Metrics

Under identical workloads (CRITICAL VoIP 12Mbps, REAL_TIME Video 25Mbps, NORMAL Web 35Mbps, BULK DB Backup 45Mbps) and a sudden physical link cut on backbone link `DR1-CR1`:

| Metric | 1. Baseline (Static) | 2. Reactive AEGIS | 3. Predictive AEGIS | Improvement vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Packet Loss %** | **33.9%** | **5.5%** | **0.9%** | **-83.8% (Reactive) / -97.4% (Predictive)** |
| **Mean Latency** | 64.2 ms | 22.4 ms | 18.1 ms | **-65.1% Latency Reduction** |
| **Throughput** | 76.5 Mbps | 108.2 Mbps | 114.8 Mbps | **+41.4% Throughput Preservation** |
| **SLA Availability** | 48.0% | 94.2% | 99.1% | **+51.1% Availability Gain** |
| **MTTR (Recovery Time)** | $\infty$ (Unrecovered) | **320.0 ms** | **120.0 ms** (Preemptive) | Sub-second closed-loop convergence |
| **Rollbacks Executed** | 0 | 0 | 0 | Proven 0 false-action churn |

---

## 3. Pre-defined Realistic Scenarios

### Scenario A — Progressive Link Congestion
- **Mechanism**: Bandwidth on primary backbone link `DR1-CR1` throttled from 2 Gbps to 25 Mbps.
- **Observed Behavior**: Queue occupancy rises above 75%, trigger rate-of-change derivative alert, followed by predictive early warning. AEGIS autonomously generates Plan A and offloads 45 Mbps bulk flows to the southern corridor `AS2 -> DR2 -> CR2`. Utilization normalizes to 61% with zero drops.

### Scenario B — Sudden Core Router Hardware Crash
- **Mechanism**: Core Router `CR1` abruptly powered down.
- **Observed Behavior**: RCA detects `ROUTER_HARDWARE_OR_POWER_FAILURE` with 98% confidence. AEGIS administratively isolates `CR1` and re-converges all active flows onto Core Router `CR2`.

### Scenario C — Optical Fiber Degradation (Physical BER)
- **Mechanism**: 15% packet loss injected on `DR1-CR1` with 60ms latency spike under low load.
- **Observed Behavior**: Queue depths remain low ($< 5\text{ pkts}$), allowing RCA to rule out buffer congestion and correctly diagnose `PHYSICAL_LAYER_OPTICAL_OR_BIT_ERROR_DEGRADATION` (92% confidence), diverting traffic away from dirty fiber.

### Scenario D — Flash Crowd Traffic Surge
- **Mechanism**: HTTPS portal flow surged by 400% (volume jumps to 140 Mbps).
- **Observed Behavior**: Multi-queue QoS buffers immediately protect `CRITICAL` VoIP packets while tail-dropping bulk traffic. AEGIS dynamically engages ingress traffic shaping and multi-path rebalancing.

### Scenario E — Cascading Multi-Link Failure
- **Mechanism**: Primary link cut coincides with secondary link capacity reduction.
- **Observed Behavior**: Tests global topology search; AEGIS routes traffic around the entire northern corridor through southern distribution routers `DR2` and `DR4`.

### Scenario F — Recovery Failure & Autonomous Rollback
- **Mechanism**: Alternate detour link `AS1-DR2` is pre-constrained to 10 Mbps.
- **Observed Behavior**: Initial mitigation attempts to reroute onto `AS1-DR2`, causing immediate collateral overload ($>92\%$). `VerificationEngine` flags collateral failure. `RollbackManager` atomically restores previous flow routes, marks Plan A as `FAILED`, and successfully deploys Plan B without operator intervention.
