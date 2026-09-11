import "@typespec/json-schema";
using TypeSpec.JsonSchema;

namespace OresOtel.Apm.V1;

@id("ApmCapabilityStatus")
enum ApmCapabilityStatus { unsupported: "unsupported", model_only: "model-only", external_adapter: "external-adapter", native: "native" }
@id("MetricKind") enum MetricKind { gauge: "gauge", counter: "counter", up_down_counter: "up-down-counter", histogram: "histogram" }
@id("ProfileKind") enum ProfileKind { cpu: "cpu", wall: "wall", allocation: "allocation", heap: "heap", lock: "lock", blocking: "blocking" }

@id("Attribute") model Attribute { @minLength(1) @maxLength(128) @pattern("^[a-zA-Z][a-zA-Z0-9_.-]*$") key: string; @maxLength(512) value: string; }
@id("Exemplar") model Exemplar { @pattern("^[0-9a-f]{32}$") trace_id: string; @pattern("^[0-9a-f]{16}$") span_id: string; value: float64; @minValue(0) timestamp_unix_nano: int64; }
@id("HistogramBucket") model HistogramBucket { upper_bound: float64; @minValue(0) count: int64; }
@id("HistogramPoint") model HistogramPoint { @minValue(0) count: int64; sum: float64; min?: float64; max?: float64; buckets: HistogramBucket[]; exemplars?: Exemplar[]; }
@id("MetricPoint") model MetricPoint { @minLength(1) @maxLength(192) @pattern("^[a-z][a-z0-9_.-]*$") name: string; @minLength(1) @maxLength(32) unit: string; kind: MetricKind; @minValue(0) timestamp_unix_nano: int64; value?: float64; histogram?: HistogramPoint; attributes?: Attribute[]; }

@id("ProcessSnapshot")
model ProcessSnapshot {
  @minValue(0) cpu_time_seconds: float64;
  @minValue(0) @maxValue(1) cpu_utilization: float64;
  @minValue(0) memory_usage_bytes: int64;
  @minValue(0) memory_virtual_bytes: int64;
  @minValue(0) @maxValue(1) memory_utilization?: float64;
  @minValue(0) disk_read_bytes: int64;
  @minValue(0) disk_write_bytes: int64;
  @minValue(0) disk_read_operations?: int64;
  @minValue(0) disk_write_operations?: int64;
  @minValue(0) network_receive_bytes?: int64;
  @minValue(0) network_transmit_bytes?: int64;
  @minValue(0) thread_count?: int64;
  @minValue(0) file_descriptor_count?: int64;
  @minValue(0) handle_count?: int64;
  @minValue(0) context_switches?: int64;
  @minValue(0) paging_faults?: int64;
  @minValue(0) uptime_seconds: float64;
}

@id("FilesystemSnapshot") model FilesystemSnapshot { @minLength(1) @maxLength(64) @pattern("^[a-z][a-z0-9_-]*$") target: string; @minValue(0) total_bytes: int64; @minValue(0) used_bytes: int64; @minValue(0) free_bytes: int64; @minValue(0) available_bytes: int64; @minValue(0) @maxValue(1) utilization: float64; @minValue(0) files_total?: int64; @minValue(0) files_free?: int64; read_only?: boolean; }
@id("RuntimeMetric") model RuntimeMetric { @minLength(1) @maxLength(64) @pattern("^[a-z][a-z0-9_]*$") runtime_namespace: string; @minLength(1) @maxLength(192) @pattern("^[a-z][a-z0-9_.-]*$") name: string; @minLength(1) @maxLength(32) unit: string; value: float64; attributes?: Attribute[]; }
@id("RuntimeSnapshot") model RuntimeSnapshot { @minLength(1) @maxLength(64) runtime_name: string; @maxLength(128) runtime_version?: string; metrics: RuntimeMetric[]; }
@id("ServicePerformanceSnapshot") model ServicePerformanceSnapshot { @minValue(0) request_count: int64; @minValue(0) error_count: int64; @minValue(0) active_requests: int64; latency_seconds: HistogramPoint; @minValue(0) @maxValue(1) saturation_ratio?: float64; }
@id("ProfileCapability") model ProfileCapability { kind: ProfileKind; status: ApmCapabilityStatus; }
@id("ProfileSummary") model ProfileSummary { @minLength(1) @maxLength(128) @pattern("^[A-Za-z0-9._:-]+$") profile_id: string; kind: ProfileKind; @minValue(0) start_unix_nano: int64; @minValue(0) end_unix_nano: int64; @minValue(0) sample_count: int64; @minValue(0) dropped_sample_count: int64; @minLength(1) @maxLength(64) format: string; }
@id("CorrelationContext") model CorrelationContext { @pattern("^[0-9a-f]{32}$") trace_id?: string; @pattern("^[0-9a-f]{16}$") span_id?: string; @minValue(0) @maxValue(255) trace_flags?: int32; }
@id("ApmCapabilitySet") model ApmCapabilitySet { process_metrics: ApmCapabilityStatus; filesystem_metrics: ApmCapabilityStatus; runtime_metrics: ApmCapabilityStatus; latency_histograms: ApmCapabilityStatus; exemplars: ApmCapabilityStatus; trace_correlation: ApmCapabilityStatus; log_correlation: ApmCapabilityStatus; metrics_export: ApmCapabilityStatus; traces_export: ApmCapabilityStatus; logs_export: ApmCapabilityStatus; profiles_export: ApmCapabilityStatus; error_tracking: ApmCapabilityStatus; service_topology: ApmCapabilityStatus; slo_inputs: ApmCapabilityStatus; profiling: ProfileCapability[]; }
@id("ApmSnapshot") model ApmSnapshot { @minValue(1) @maxValue(1) schema_version: int32; @minValue(0) observed_at_unix_nano: int64; @minLength(1) @maxLength(128) service_name: string; @minLength(1) @maxLength(128) service_instance_id: string; process: ProcessSnapshot; filesystems: FilesystemSnapshot[]; runtime?: RuntimeSnapshot; service: ServicePerformanceSnapshot; correlation?: CorrelationContext; profiles?: ProfileSummary[]; capabilities: ApmCapabilitySet; metrics?: MetricPoint[]; }
