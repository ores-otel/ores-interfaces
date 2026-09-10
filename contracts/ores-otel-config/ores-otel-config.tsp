import "@typespec/json-schema";
using TypeSpec.JsonSchema;

namespace OresOtel.Config;

@id("OresOtelMode")
enum OresOtelMode {
  client: "client",
  server: "server",
  hybrid: "hybrid",
}

@id("EnvKind")
enum EnvKind {
  string: "string",
  bool: "bool",
  integer: "integer",
  double: "double",
  json: "json",
  url: "url",
}

@id("Flags2EnvPrecedence")
enum Flags2EnvPrecedence {
  argv_over_env: "argv-over-env",
}

@id("Flags2EnvConfig")
model Flags2EnvConfig {
  @minLength(1)
  @maxLength(256)
  contract: string;

  require_audit: boolean;
  precedence: Flags2EnvPrecedence;
}

@id("EnvBinding")
model EnvBinding {
  @minLength(1)
  @maxLength(64)
  @pattern("^[a-z][a-z0-9_]*$")
  name: string;

  @minLength(1)
  @maxLength(128)
  @pattern("^[A-Z_][A-Z0-9_]*$")
  key: string;

  kind: EnvKind;
  required: boolean;
  secret: boolean;

  @maxLength(8192)
  default?: string;

  @maxLength(512)
  description?: string;
}

@id("OresOtelClientConfig")
model OresOtelClientConfig {
  enabled: boolean;

  @minLength(1)
  @maxLength(64)
  service_name_binding?: string;

  @minLength(1)
  @maxLength(64)
  log_filter_binding?: string;

  @minLength(1)
  @maxLength(64)
  sample_ratio_binding?: string;

  @minLength(1)
  @maxLength(64)
  include_trace_context_binding?: string;
}

@id("OresOtelServerConfig")
model OresOtelServerConfig {
  enabled: boolean;

  @minLength(1)
  @maxLength(64)
  service_name_binding?: string;

  @minLength(1)
  @maxLength(64)
  log_filter_binding?: string;

  @minLength(1)
  @maxLength(64)
  sample_ratio_binding?: string;

  @minLength(1)
  @maxLength(64)
  otlp_endpoint_binding?: string;

  @minLength(1)
  @maxLength(64)
  otlp_headers_binding?: string;

  @minLength(1)
  @maxLength(64)
  batch_max_queue_binding?: string;

  @minLength(1)
  @maxLength(64)
  redact_fields_binding?: string;
}

@id("OresOtelConfig")
model OresOtelConfig {
  @minValue(1)
  @maxValue(1)
  version: int32;

  mode: OresOtelMode;
  strict: boolean;
  flags2env: Flags2EnvConfig;
  env: EnvBinding[];
  client?: OresOtelClientConfig;
  server?: OresOtelServerConfig;
}
