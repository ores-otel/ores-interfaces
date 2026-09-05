// Generated only after independent JSON Schema and TypeSpec agreement. DO NOT EDIT.
import gleam/option.{type Option}

pub const contract_version="ores.validation.v2"

pub type InternalCommand {
  InternalCommand(
    context: ServerRequestContext,
    idempotency_key: Option(String),
    operation_id: String,
  )
}

pub type ServerRequestContext {
  ServerRequestContext(
    locale: Option(String),
    request_id: String,
    roles: List(String),
    source_ip: Option(String),
    tenant_id: Option(String),
    trace_id: String,
    user_id: String,
  )
}

pub type TrustedActor {
  TrustedActor(
    roles: List(String),
    tenant_id: Option(String),
    user_id: String,
  )
}
