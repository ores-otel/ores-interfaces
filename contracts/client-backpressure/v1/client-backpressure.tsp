import "@typespec/json-schema";
using TypeSpec.JsonSchema;

namespace OresOtel.ClientBackpressure.V1;

@minLength(1)
@maxLength(128)
@pattern("^[A-Za-z0-9_.:/-]+$")
scalar SafeIdentifier extends string;

@id("BackpressurePhase")
enum BackpressurePhase {
  queued: "queued",
  delayed: "delayed",
  resumed: "resumed",
  dropped: "dropped",
  rejected: "rejected"
}

@id("BackpressureTransport")
enum BackpressureTransport {
  fetch: "fetch",
  rpc: "rpc",
  websocket: "websocket",
  sse: "sse",
  other: "other"
}

@id("BackpressureReason")
enum BackpressureReason {
  local_pacing: "local_pacing",
  server_retry_after: "server_retry_after",
  rate_limit: "rate_limit",
  concurrency: "concurrency",
  queue_full: "queue_full",
  queue_timeout: "queue_timeout",
  transport_backpressure: "transport_backpressure",
  service_overload: "service_overload",
  cancelled: "cancelled"
}

@id("BrowserBackpressureEvent")
model BrowserBackpressureEvent {
  schema_version: 1;
  event_name: "ores.client.backpressure";

  phase: BackpressurePhase;
  transport: BackpressureTransport;
  reason: BackpressureReason;

  @minValue(0) @maxValue(9007199254740991)
  observed_at_unix_ms: uint64;

  @minValue(0) @maxValue(9007199254740991)
  queued_at_unix_ms?: uint64;

  @minValue(0) @maxValue(9007199254740991)
  queue_age_ms: uint64;

  @minValue(0) @maxValue(9007199254740991)
  scheduled_delay_ms: uint64;

  @minValue(0) @maxValue(9007199254740991)
  queue_depth?: uint64;

  @minValue(0) @maxValue(9007199254740991)
  queue_bytes?: uint64;

  @minValue(0) @maxValue(9007199254740991)
  retry_after_ms?: uint64;

  @minValue(0) @maxValue(9007199254740991)
  recommended_next_request_after_ms?: uint64;

  policy_version?: SafeIdentifier;

  @minLength(1) @maxLength(20) @pattern("^(0|[1-9][0-9]{0,19})$")
  quota_fence?: string;

  @maxItems(8)
  limiting_policy_ids?: SafeIdentifier[];

  @minValue(0) @maxValue(9007199254740991)
  attempt?: uint64;

  operation?: SafeIdentifier;
  idempotent?: boolean;
}
