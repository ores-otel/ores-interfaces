import "@typespec/json-schema";
using TypeSpec.JsonSchema;

namespace OresOtel.Apm.V1;

@id("ApmCapabilityStatus")
enum ApmCapabilityStatus { unsupported: "unsupported", model_only: "model-only", external_adapter: "external-adapter", native: "native" }
@id("MetricKind") enum MetricKind { gauge: "gauge", counter: "counter", up_down_counter: "up-down-counter", histogram: "histogram" }
@id("ProfileKind") enum ProfileKind { cpu: "cpu", wall: "wall", allocation: "allocation", heap: "heap", lock: "lock", blocking: "blocking" }

@id("Attribute") model Attribute { @minLength(1) @maxLength(128) @pattern("^[a-zA-Z][a-zA-Z0-9_.-]*$") key: string; @maxLength(512) value: string; }
@id("Exemplar") model Exemplar { @pattern("^[0-9a-f]{32}$") trace_id: string; @pattern("^[0-9a-f]{16}$") span_id: string; value: float64; @pattern("^(0|[1-9][0-9]*)$") timestamp_unix_nano: string; }
@id("HistogramBucket") model HistogramBucket { upper_bound: float64; @pattern("^(0|[1-9][0-9]*)$") count: string; }
@id("HistogramPoint") model HistogramPoint { @pattern("^(0|[1-9][0-9]*)$") count: string; sum: float64; min?: float64; max?: float64; buckets: HistogramBucket[]; exemplars?: Exemplar[]; }
@id("MetricPoint") model MetricPoint { @minLength(1) @maxLength(192) @pattern("^[a-z][a-z0-9_.-]*$") name: string; @minLength(1) @maxLength(32) unit: string; kind: MetricKind; @pattern("^(0|[1-9][0-9]*)$") timestamp_unix_nano: string; value?: float64; histogram?: HistogramPoint; attributes?: Attribute[]; }

@id("ProcessSnapshot")
model ProcessSnapshot {
  @minValue(0) cpu_time_seconds: float64;
  @minValue(0) @maxValue(1) cpu_utilization: float64;
  @pattern("^(0|[1-9][0-9]*)$") memory_usage_bytes: string;
  @pattern("^(0|[1-9][0-9]*)$") memory_virtual_bytes: string;
  @minValue(0) @maxValue(1) memory_utilization?: float64;
  @pattern("^(0|[1-9][0-9]*)$") disk_read_bytes: string;
  @pattern("^(0|[1-9][0-9]*)$") disk_write_bytes: string;
  @pattern("^(0|[1-9][0-9]*)$") disk_read_operations?: string;
  @pattern("^(0|[1-9][0-9]*)$") disk_write_operations?: string;
  @pattern("^(0|[1-9][0-9]*)$") network_receive_bytes?: string;
  @pattern("^(0|[1-9][0-9]*)$") network_transmit_bytes?: string;
  @pattern("^(0|[1-9][0-9]*)$") thread_count?: string;
  @pattern("^(0|[1-9][0-9]*)$") file_descriptor_count?: string;
  @pattern("^(0|[1-9][0-9]*)$") handle_count?: string;
  @pattern("^(0|[1-9][0-9]*)$") context_switches?: string;
  @pattern("^(0|[1-9][0-9]*)$") paging_faults?: string;
  @minValue(0) uptime_seconds: float64;
}

@id("FilesystemSnapshot") model FilesystemSnapshot { @minLength(1) @maxLength(64) @pattern("^[a-z][a-z0-9_-]*$") target: string; @pattern("^(0|[1-9][0-9]*)$") total_bytes: string; @pattern("^(0|[1-9][0-9]*)$") used_bytes: string; @pattern("^(0|[1-9][0-9]*)$") free_bytes: string; @pattern("^(0|[1-9][0-9]*)$") available_bytes: string; @minValue(0) @maxValue(1) utilization: float64; @pattern("^(0|[1-9][0-9]*)$") files_total?: string; @pattern("^(0|[1-9][0-9]*)$") files_free?: string; read_only?: boolean; }
@id("RuntimeMetric") model RuntimeMetric { @minLength(1) @maxLength(64) @pattern("^[a-z][a-z0-9_]*$") runtime_namespace: string; @minLength(1) @maxLength(192) @pattern("^[a-z][a-z0-9_.-]*$") name: string; @minLength(1) @maxLength(32) unit: string; value: float64; attributes?: Attribute[]; }
@id("RuntimeSnapshot") model RuntimeSnapshot { @minLength(1) @maxLength(64) runtime_name: string; @maxLength(128) runtime_version?: string; metrics: RuntimeMetric[]; }
@id("ServicePerformanceSnapshot") model ServicePerformanceSnapshot { @pattern("^(0|[1-9][0-9]*)$") request_count: string; @pattern("^(0|[1-9][0-9]*)$") error_count: string; @pattern("^(0|[1-9][0-9]*)$") active_requests: string; latency_seconds: HistogramPoint; @minValue(0) @maxValue(1) saturation_ratio?: float64; }
@id("ProfileCapability") model ProfileCapability { kind: ProfileKind; status: ApmCapabilityStatus; }
@id("ProfileSummary") model ProfileSummary { @minLength(1) @maxLength(128) @pattern("^[A-Za-z0-9._:-]+$") profile_id: string; kind: ProfileKind; @pattern("^(0|[1-9][0-9]*)$") start_unix_nano: string; @pattern("^(0|[1-9][0-9]*)$") end_unix_nano: string; @pattern("^(0|[1-9][0-9]*)$") sample_count: string; @pattern("^(0|[1-9][0-9]*)$") dropped_sample_count: string; @minLength(1) @maxLength(64) format: string; }
@id("CorrelationContext") model CorrelationContext { @pattern("^[0-9a-f]{32}$") trace_id?: string; @pattern("^[0-9a-f]{16}$") span_id?: string; @minValue(0) @maxValue(255) trace_flags?: int32; }
@id("ApmCapabilitySet") model ApmCapabilitySet { process_metrics: ApmCapabilityStatus; filesystem_metrics: ApmCapabilityStatus; runtime_metrics: ApmCapabilityStatus; latency_histograms: ApmCapabilityStatus; exemplars: ApmCapabilityStatus; trace_correlation: ApmCapabilityStatus; log_correlation: ApmCapabilityStatus; metrics_export: ApmCapabilityStatus; traces_export: ApmCapabilityStatus; logs_export: ApmCapabilityStatus; profiles_export: ApmCapabilityStatus; error_tracking: ApmCapabilityStatus; service_topology: ApmCapabilityStatus; slo_inputs: ApmCapabilityStatus; profiling: ProfileCapability[]; }
@id("ApmSnapshot") model ApmSnapshot { @minValue(1) @maxValue(1) schema_version: int32; @pattern("^(0|[1-9][0-9]*)$") observed_at_unix_nano: string; @minLength(1) @maxLength(128) service_name: string; @minLength(1) @maxLength(128) service_instance_id: string; process: ProcessSnapshot; filesystems: FilesystemSnapshot[]; runtime?: RuntimeSnapshot; service: ServicePerformanceSnapshot; correlation?: CorrelationContext; profiles?: ProfileSummary[]; capabilities: ApmCapabilitySet; metrics?: MetricPoint[]; }
