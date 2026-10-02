// Generated only after independent JSON Schema and TypeSpec agreement. DO NOT EDIT.

package interfaces_server

const ContractVersion="ores.validation.v2"

type InternalCommand struct {
	Context ServerRequestContext `json:"context"`
	IdempotencyKey *string `json:"idempotencyKey,omitempty"`
	OperationId string `json:"operationId"`
}

type ServerRequestContext struct {
	Locale *string `json:"locale,omitempty"`
	RequestId string `json:"requestId"`
	Roles []string `json:"roles"`
	SourceIp *string `json:"sourceIp,omitempty"`
	TenantId *string `json:"tenantId,omitempty"`
	TraceId string `json:"traceId"`
	UserId string `json:"userId"`
}

type TrustedActor struct {
	Roles []string `json:"roles"`
	TenantId *string `json:"tenantId,omitempty"`
	UserId string `json:"userId"`
}
