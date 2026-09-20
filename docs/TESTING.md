# AEGIS — Testing & Verification Guide

## 1. Test Suite Architecture

AEGIS includes a comprehensive, multi-layer automated test suite using `pytest`. The tests verify every stage of the self-healing lifecycle, queueing mechanics, routing optimality, and extreme edge cases.

Test Directory: `tests/`
Total Automated Tests: **17 Unit & End-to-End Tests**

---

## 2. Test Execution

To execute the complete test suite:

```powershell
python -m pytest tests/ -v
```

Output:
```text
tests/test_anomaly_detection.py::test_hard_link_failure_detection PASSED
tests/test_anomaly_detection.py::test_congestion_anomaly_detection PASSED
tests/test_deep_edge_cases.py::test_extreme_buffer_saturation_and_qos_preemption PASSED
tests/test_deep_edge_cases.py::test_partitioned_disconnected_topology PASSED
tests/test_deep_edge_cases.py::test_multi_incident_memory_efficacy_metrics PASSED
tests/test_diagnosis_and_prediction.py::test_rca_hardware_router_failure PASSED
tests/test_diagnosis_and_prediction.py::test_rca_physical_optical_degradation PASSED
tests/test_diagnosis_and_prediction.py::test_predictive_degradation_forecast PASSED
tests/test_recovery_and_rollback.py::test_recovery_planner_candidate_generation PASSED
tests/test_recovery_and_rollback.py::test_autonomous_recovery_and_verification_cycle PASSED
tests/test_recovery_and_rollback.py::test_rollback_on_failed_verification PASSED
tests/test_scenarios_and_benchmarks.py::test_scenario_loader_execution PASSED
tests/test_scenarios_and_benchmarks.py::test_quantitative_benchmark_comparison PASSED
tests/test_simulation.py::test_topology_creation_and_k_paths PASSED
tests/test_simulation.py::test_qos_buffer_priority PASSED
tests/test_simulation.py::test_simulation_engine_traffic_delivery PASSED
tests/test_simulation.py::test_congestion_aware_routing PASSED

============================= 17 passed in 1.1s =============================
```

---

## 3. Test Coverage Breakdown

### 3.1 Network & Simulation (`test_simulation.py`)
- Graph creation and Yen's K-shortest paths generation.
- Strict priority queue ordering ($P_{100} > P_{80} > P_{50} > P_{10}$).
- Hop-by-hop packet forwarding, transmission and propagation delays.
- Congestion-aware routing edge cost expansion under 95% utilization.

### 3.2 Anomaly Detection (`test_anomaly_detection.py`)
- Instant detection of hard link cuts and unreachability.
- Multi-metric congestion anomaly detection combining queue depth, latency multipliers, and rate-of-change derivatives.

### 3.3 Root Cause Analysis & Prediction (`test_diagnosis_and_prediction.py`)
- RCA differentiation between physical optical BER degradation vs buffer congestion.
- Core router hardware crashes pinpointed with $>90\%$ confidence.
- Ordinary Least Squares (OLS) linear trend forecasting calculating intervals to threshold saturation.

### 3.4 Autonomous Recovery & Rollback (`test_recovery_and_rollback.py`)
- Candidate recovery plan generation and multi-objective ranking.
- End-to-end autonomous healing cycle (`DETECT -> DIAGNOSE -> PLAN -> ACT -> VERIFY -> RESOLVE`).
- Automated atomic rollback when verification fails, restoring original paths without operator input.

### 3.5 Deep Edge Cases (`test_deep_edge_cases.py`)
- Buffer preemption under extreme saturation (evicting `BULK` to guarantee ingress for `CRITICAL`).
- Disconnected graph partitioning (`NO_ROUTE_TO_HOST` drop handling).
- Persistent incident memory aggregation (MTTR and strategy efficacy metrics).
