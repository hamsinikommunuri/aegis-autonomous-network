# AEGIS — Network Digital Environment & Simulation Model

## 1. Network Topology Graph Model

The virtual network is modeled as a directed multi-graph $G = (V, E)$ where:
- $V = \{v_1, v_2, \dots, v_n\}$ represents network elements (Hosts, Access Switches, Distribution Routers, Core Backbone Routers, and Data Center Servers).
- $E = \{e_1, e_2, \dots, e_m\}$ represents operational physical/logical links.

### Node State Specification
Each node $v \in V$ contains:
- `id`: Unique alphanumeric identifier (e.g. `CR1`, `DR1`, `SVR-1`).
- `node_type`: `HOST`, `SWITCH`, `ROUTER`, or `SERVER`.
- `status`: `UP`, `DOWN`, or `DEGRADED`.
- `processing_capacity_pps`: Packet forwarding capacity in packets/sec (e.g., 250,000 pps on Core Routers).
- `queue_capacity_packets`: Maximum total ingress queue buffer capacity.
- `cpu_utilization`: Dynamic CPU load reflecting forwarding pressure.
- `health_score`: Composite health index computed as:
  $$H(v) = (1 - (0.35 U_{\text{cpu}} + 0.25 U_{\text{mem}} + 0.40 Q_{\text{ratio}})) \cdot D_v$$
  where $D_v = 0.5$ if degraded, $0.0$ if down, $1.0$ if nominal.

### Link State Specification
Each link $e = (u, v) \in E$ contains:
- `bandwidth_bps`: Channel capacity in bits/sec (10 Gbps core backbone, 2 Gbps distribution, 1 Gbps access).
- `propagation_delay_ms`: Physical medium propagation latency ($1.0 \dots 5.0\text{ ms}$).
- `loss_rate`: Physical bit-error-rate / optical degradation probability ($0.0 \dots 1.0$).
- `queue_capacity_packets`: Output interface buffer limit (200 packets).
- `current_utilization`: $\frac{\text{Bits transmitted in step}}{\text{Capacity bits in step}}$.
- `current_latency_ms`: Dynamic latency:
  $$D_{\text{link}} = D_{\text{prop}} + D_{\text{trans}} + D_{\text{queue}}$$

---

## 2. QoS Multi-Queue Buffer Model

Each output link interface is backed by a QoS-aware `QoSBuffer` supporting 4 priority queues:
1. `CRITICAL` (Priority 100): Control plane, network telemetry, emergency signals.
2. `REAL_TIME` (Priority 80): Voice SIP trunks, real-time video conferencing.
3. `NORMAL` (Priority 50): Web application portals, transactional HTTP/HTTPS.
4. `BULK` (Priority 10): Database synchronization, asynchronous backup vaults.

### Queuing & Preemption Policy:
- **Strict Priority Scheduling**: Packets are dequeued in strict priority order ($P_{100} \to P_{80} \to P_{50} \to P_{10}$).
- **Buffer Exhaustion Preemption**: When buffer reaches total capacity ($200$ packets), lower-priority packets (`BULK`, followed by `NORMAL`) are preemptively evicted and marked as dropped (`QOS_PREEMPTION_FOR_HIGH_PRIORITY`) to guarantee ingress headroom for `CRITICAL` and `REAL_TIME` packets.

---

## 3. Discrete Simulation Clock & Packet Forwarding

The simulation clock advances in deterministic discrete ticks of $\Delta t = 100\text{ ms}$:
1. **In-Flight Deliveries**: In-flight packets reaching their next hop or destination within $[t, t + \Delta t]$ are processed.
2. **Workload Generation**: `TrafficGenerator` samples each flow's packet generation rate using a seeded pseudo-random number generator (PRNG):
   $$N_{\text{pkts}} = \text{Flow}_{\text{pps}} \times \frac{\Delta t}{1000}$$
3. **Queue Ingress**: Packets enter the link buffer of the first hop link along the flow's current forwarding path.
4. **Link Transmission**: Links service their queues up to:
   $$\text{MaxBytes} = \frac{\text{Bandwidth}_{\text{bps}}}{8} \times \frac{\Delta t}{1000}$$
5. **Physical Impairments**: Packets are checked against link physical loss rates (`PHYSICAL_LINK_ERROR_OR_DEGRADATION`).
6. **Hop Traversal**: Packet TTL is decremented, hop path is recorded, and in-flight arrival timestamps are scheduled.
