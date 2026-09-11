//! Generated only after independent JSON Schema and TypeSpec agreement. DO NOT EDIT.

#[derive(Clone, Debug, PartialEq)]
pub struct InternalCommand {
    pub context: ServerRequestContext,
    pub idempotency_key: Option<String>,
    pub operation_id: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ServerRequestContext {
    pub locale: Option<String>,
    pub request_id: String,
    pub roles: Vec<String>,
    pub source_ip: Option<String>,
    pub tenant_id: Option<String>,
    pub trace_id: String,
    pub user_id: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct TrustedActor {
    pub roles: Vec<String>,
    pub tenant_id: Option<String>,
    pub user_id: String,
}
