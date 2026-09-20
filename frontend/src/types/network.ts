export type TrafficClass = 'CRITICAL' | 'REAL_TIME' | 'NORMAL' | 'BULK';
export type LinkStatus = 'UP' | 'DOWN' | 'DEGRADED';
export type NodeStatus = 'UP' | 'DOWN' | 'DEGRADED';
export type NodeType = 'HOST' | 'ROUTER' | 'SWITCH' | 'SERVER';
export type IncidentSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 
  | 'DETECTED' 
  | 'INVESTIGATING' 
  | 'DIAGNOSED' 
  | 'PLANNING' 
  | 'MITIGATING' 
  | 'VERIFYING' 
  | 'RESOLVED' 
  | 'ROLLBACK';

export interface NetworkInterface {
  name: string;
  ip_address: string;
  mac_address: string;
  speed_bps: number;
  mtu: number;
  is_up: boolean;
}

export interface Node {
  id: string;
  name: string;
  node_type: NodeType;
  status: NodeStatus;
  processing_capacity_pps: number;
  queue_capacity_packets: number;
  interfaces?: Record<string, NetworkInterface>;
  routing_table?: Record<string, string>;
  x: number;
  y: number;
  cpu_utilization: number;
  memory_utilization: number;
  current_queue_depth: number;
  forwarded_packets: number;
  dropped_packets: number;
  health_score: number;
}

export interface Link {
  id: string;
  source: string;
  destination: string;
  bandwidth_bps: number;
  propagation_delay_ms: number;
  loss_rate: number;
  error_rate: number;
  base_cost: number;
  operational_cost: number;
  status: LinkStatus;
  queue_capacity_packets: number;
  current_utilization: number;
  current_queue_depth: number;
  current_latency_ms: number;
  bytes_transmitted: number;
  packets_transmitted: number;
  packets_dropped: number;
  recent_loss_rate: number;
}

export interface TrafficFlow {
  id: string;
  name: string;
  source_id: string;
  dest_id: string;
  traffic_class: TrafficClass;
  demand_bps: number;
  packet_size_bytes: number;
  packets_per_second: number;
  latency_sla_ms: number;
  loss_sla_percent: number;
  priority: number;
  active: boolean;
  current_path: string[];
  packets_sent: number;
  packets_received: number;
  packets_dropped: number;
  loss_rate_percent: number;
  average_latency_ms: number;
  jitter_ms: number;
  sla_violated: boolean;
}

export interface CandidatePlan {
  id: string;
  title: string;
  description: string;
  action_type: string;
  action_params: Record<string, any>;
  affected_flows: string[];
  predicted_latency_impact_pct: number;
  predicted_loss_reduction_pct: number;
  risk_score: number;
  reversibility: boolean;
  qos_priority_preserved: boolean;
  explanation: string;
  score: number;
  status?: string;
  failure_reason?: string;
}

export interface TimelineEvent {
  time_ms: number;
  event: string;
  details: string;
}

export interface Incident {
  id: string;
  incident_type: string;
  affected_resource: string;
  severity: IncidentSeverity;
  detected_time_ms: number;
  status: IncidentStatus;
  evidence: Record<string, any>;
  anomaly_score: number;
  diagnosis?: string;
  diagnosis_confidence: number;
  diagnosis_explanation?: string;
  is_predictive?: boolean;
  predicted_time_to_breach_ms?: number;
  predicted_consequence?: string;
  candidate_plans?: CandidatePlan[];
  selected_plan_id?: string;
  applied_action?: Record<string, any>;
  action_applied_time_ms?: number;
  pre_recovery_metrics?: Record<string, number>;
  post_recovery_metrics?: Record<string, number>;
  verification_success?: boolean;
  verification_reason?: string;
  rollback_performed?: boolean;
  rollback_reason?: string;
  resolved_time_ms?: number;
  timeline: TimelineEvent[];
}

export interface NetworkGlobalSnapshot {
  timestamp_ms: number;
  tick: number;
  total_throughput_bps: number;
  total_throughput_mbps: number;
  total_packets_sent: number;
  total_packets_received: number;
  total_packets_dropped: number;
  global_packet_loss_rate: number;
  average_latency_ms: number;
  average_jitter_ms: number;
  sla_compliance_rate: number;
  active_incidents_count: number;
  links: Record<string, Link>;
  nodes: Record<string, Node>;
  flows: Record<string, TrafficFlow>;
}

export interface BenchmarkResultItem {
  mode: string;
  packets_sent: number;
  packets_received: number;
  packets_dropped: number;
  packet_loss_rate: number;
  packet_loss_percent: number;
  average_latency_ms: number;
  total_throughput_mbps: number;
  sla_availability_percent: number;
  recovery_time_ms: number;
  incidents_handled: number;
  rollbacks_count: number;
}

export interface BenchmarkReport {
  scenario: string;
  total_steps: number;
  simulation_duration_sec: number;
  results: {
    baseline: BenchmarkResultItem;
    reactive: BenchmarkResultItem;
    predictive: BenchmarkResultItem;
  };
  summary: {
    loss_reduction_pct: number;
    latency_improvement_pct: number;
    predictive_loss_reduction_pct: number;
  };
}
