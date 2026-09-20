# AEGIS — Algorithmic Models & Mathematical Formulations

## 1. Routing Algorithms

### 1.1 Dijkstra Shortest Path
Computes shortest path over graph $G=(V, E)$ respecting node and link availability:
$$\min_P \sum_{e \in P} c(e)$$
where $c(e) = \text{base\_cost}(e)$.

### 1.2 Congestion-Aware Dynamic Routing
Computes optimal forwarding paths using a multi-metric cost function penalizing queueing expansion as link utilization approaches capacity ($M/M/1$ delay asymptote):

$$C(e) = w_{\text{lat}} \cdot \left(\frac{D(e)}{D_0}\right) + w_{\text{cong}} \cdot \left(\frac{U(e)}{1.0 - \min(U(e), 0.98)}\right) + w_{\text{loss}} \cdot (100 \cdot L(e)) + w_{\text{hop}} \cdot h(e)$$

Default weights:
- $w_{\text{lat}} = 1.0$ (Latency factor)
- $w_{\text{cong}} = 2.5$ (Congestion / M/M/1 expansion factor)
- $w_{\text{loss}} = 10.0$ (Packet loss penalty)
- $w_{\text{hop}} = 0.5$ (Hop count cost)

### 1.3 Yen's K-Shortest Paths
Generates alternative loopless candidate detour paths $A = \{P_1, P_2, \dots, P_k\}$ by branching along spur nodes and root paths, enabling offloading without saturating parallel links.

---

## 2. Anomaly Detection & Telemetry Scoring

AEGIS employs deterministic thresholding coupled with moving baselines and rate-of-change derivatives:

### 2.1 Multi-Metric Anomaly Score
For link $e$, given utilization $U(e)$, loss rate $L(e)$, queue depth $Q(e)$, and derivative $\frac{dU}{dt}$:
- Utilization excess: $S_U = 0.35 + 0.65 \times \frac{U - U_{\text{thresh}}}{1 - U_{\text{thresh}}}$ if $U \ge 0.85$
- Loss severity: $S_L = 0.50 + 0.50 \times \min(1.0, \frac{L}{0.10})$ if $L \ge 0.02$
- Queue occupancy: $S_Q = 0.40 + 0.60 \times \frac{Q}{Q_{\text{capacity}}}$ if $\frac{Q}{Q_{\text{capacity}}} \ge 0.70$
- Rate-of-change derivative: $S_{\text{roc}} = 0.60$ if $\frac{dU}{dt} \ge 0.20$

Composite Anomaly Score:
$$S_{\text{composite}} = \min\left(1.0, \frac{\sum S_i}{k} + 0.15 (k - 1)\right)$$

---

## 3. Ordinary Least Squares (OLS) Degradation Forecasting

Given a sliding window of recent utilization measurements $\{u_0, u_1, \dots, u_{n-1}\}$:
$$m = \frac{\sum_{i=0}^{n-1} (i - \bar{x})(u_i - \bar{u})}{\sum_{i=0}^{n-1} (i - \bar{x})^2}$$
Estimated steps until threshold crossing ($U_{\text{sat}} = 0.88$):
$$\Delta k = \frac{U_{\text{sat}} - u_{n-1}}{m}$$
If $\Delta k \le 5\text{ intervals}$ and $m \ge 0.03/\text{interval}$, AEGIS generates a `PREDICTED_DEGRADATION` incident to prompt proactive offloading before packet loss occurs.

---

## 4. Recovery Plan Evaluation & Multi-Objective Ranking

Every candidate plan $P_j$ is evaluated across five predicted dimensions:
- Predicted packet loss reduction: $\Delta L_j \in [0, 100]\%$
- Predicted latency impact: $\Delta D_j \in [-100, +100]\%$
- Risk score: $R_j \in [0, 100]$ (operational blast radius)
- QoS preservation bonus: $Q_j = 10.0$ if critical flows are protected

Transparent Plan Score:
$$\text{Score}(P_j) = (0.40 \cdot \Delta L_j) + (0.30 \cdot (-\Delta D_j)) + (0.20 \cdot (100 - R_j)) + Q_j$$
The plan with the highest score is automatically selected for execution.
