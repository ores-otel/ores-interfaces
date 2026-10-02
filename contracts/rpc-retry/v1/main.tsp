import "@typespec/protobuf";
import "@typespec/json-schema";
using TypeSpec.Protobuf;
using TypeSpec.JsonSchema;

// Candidate wire contracts only. Not a persistence schema or a remotely callable retry service.
@package({ name: "ores.rpc.v1" })
namespace Ores.Rpc.V1;

@message
@jsonSchema
model RetryPolicy {
  @field(1) @minValue(1) @maxValue(8)
  max_attempts: uint32;
  @field(2) @minValue(1) @maxValue(3600000)
  timeout_ms: uint32;
  @field(3) @minValue(1) @maxValue(60000)
  initial_backoff_ms: uint32;
  @field(4) @minValue(1) @maxValue(60000)
  max_backoff_ms: uint32;
}

@message
@jsonSchema
model RetryAttempt {
  @field(1) @minValue(1) @maxValue(8)
  attempts_completed: uint32;
  @field(2) @minValue(0) @maxValue(3600000)
  elapsed_ms: uint32;
  @field(3) @minValue(0) @maxValue(16)
  code: uint32;
  @field(4)
  cancelled: boolean;
  // Trusted method metadata, NOT a client authorization or a promise implied by having a key.
  @field(5)
  replay_safe: boolean;
  @field(6) @minValue(0) @maxValue(1000)
  jitter_permille: uint32;
  // Optional scalar presence must survive Protobuf emission; null is not a valid JSON value.
  @field(7) @minValue(0) @maxValue(3600000)
  retry_after_ms?: uint32;
}

@message
@jsonSchema
model RetryInput {
  @field(1)
  policy: RetryPolicy;
  @field(2)
  attempt: RetryAttempt;
}

@message
@jsonSchema
model RetryDecision {
  @field(1)
  retry: boolean;
  @field(2) @minValue(0) @maxValue(3600000)
  delay_ms: uint32;
  // 1 retry; 2 invalid; 3 cancelled; 4 unsafe; 5 attempts; 6 deadline; 7 non-retryable.
  @field(3) @minValue(1) @maxValue(7)
  reason: uint32;
}
