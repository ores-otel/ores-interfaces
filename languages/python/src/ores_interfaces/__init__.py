from dataclasses import dataclass
from enum import StrEnum

class AuthMethod(StrEnum):
    JWT="jwt"; OIDC="oidc"; WEBAUTHN="webauthn"; TOTP="totp"; KERBEROS="kerberos"; SSH="ssh"; OPENPGP="openpgp"; PLATFORM_BIOMETRIC="platform_biometric"; RECOVERY="recovery"
class AssuranceLevel(StrEnum):
    AAL0="aal0"; AAL1="aal1"; AAL2="aal2"; AAL3="aal3"
class PrincipalSearchState(StrEnum):
    NO_MATCH="no_match"; UNIQUE="unique"; AMBIGUOUS="ambiguous"
class RevocationScope(StrEnum):
    INTERACTIVE_SESSIONS="interactive_sessions"
    REFRESH_TOKEN_FAMILIES="refresh_token_families"
    OFFLINE_GRANTS="offline_grants"
    DOWNSTREAM_SESSIONS="downstream_sessions"
    IMPERSONATION_SESSIONS="impersonation_sessions"
    USER_API_CREDENTIALS="user_api_credentials"
    REGISTERED_DEVICE_SESSIONS="registered_device_sessions"
class RevocationJobState(StrEnum):
    QUEUED="queued"; RUNNING="running"; PARTIAL="partial"; SUCCEEDED="succeeded"; FAILED="failed"; CANCELLED="cancelled"
    def terminal(self) -> bool:
        return self in {self.PARTIAL, self.SUCCEEDED, self.FAILED, self.CANCELLED}
class RevocationTargetState(StrEnum):
    PENDING="pending"; RUNNING="running"; RETRY_SCHEDULED="retry_scheduled"; SUCCEEDED="succeeded"; FAILED="failed"; SKIPPED="skipped"; UNSUPPORTED="unsupported"
class PrincipalKind(StrEnum):
    HUMAN="human"; SERVICE="service"; WORKLOAD="workload"; DEVICE="device"; AUTOMATION="automation"
@dataclass(frozen=True, slots=True)
class PrincipalRef:
    tenant_id: str; subject: str; kind: PrincipalKind; organization: str | None = None; display_name: str | None = None
@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str; trace_id: str; span_id: str | None = None; tenant_id: str | None = None; client_id: str | None = None; source: str | None = None
@dataclass(frozen=True, slots=True)
class ErrorEnvelope:
    code: str; message: str; retryable: bool; request_id: str
@dataclass(frozen=True, slots=True)
class PlatformBiometricProof:
    verified_by_platform_authenticator: bool; user_verification: str; raw_biometric_material_present: bool = False
    def safe(self) -> bool:
        return self.verified_by_platform_authenticator and self.user_verification == "required" and not self.raw_biometric_material_present

@dataclass(frozen=True, slots=True)
class RevocationRedaction:
    raw_emails_present: bool
    raw_tokens_present: bool
    raw_session_identifiers_present: bool
    raw_biometric_material_present: bool

@dataclass(frozen=True, slots=True)
class ProviderIdentityRef:
    provider_id: str
    provider_tenant_id: str
    opaque_identity_handle: str

@dataclass(frozen=True, slots=True)
class PrincipalSearchRequest:
    schema: str
    request_id: str
    requested_by_principal_id: str
    email_search_key_hash: str
    purpose: str
    requested_at: str
    redaction: RevocationRedaction

@dataclass(frozen=True, slots=True)
class PrincipalSearchCandidate:
    principal_id: str
    identities: tuple[ProviderIdentityRef, ...]
    organization_count: int
    active_session_count: int

@dataclass(frozen=True, slots=True)
class PrincipalSearchResult:
    schema: str
    lookup_id: str
    email_search_key_hash: str
    state: PrincipalSearchState
    candidates: tuple[PrincipalSearchCandidate, ...]
    requires_explicit_principal_selection: bool
    generated_at: str
    redaction: RevocationRedaction

@dataclass(frozen=True, slots=True)
class RevocationBlastRadius:
    provider_tenant_count: int
    identity_count: int
    organization_count: int
    project_count: int
    interactive_session_count: int
    refresh_token_family_count: int
    offline_grant_count: int
    downstream_session_count: int
    impersonation_session_count: int
    user_api_credential_count: int
    registered_device_session_count: int

@dataclass(frozen=True, slots=True)
class RevocationPreviewTarget:
    target_id_hash: str
    identity: ProviderIdentityRef
    scope: RevocationScope
    estimated_resource_count: int
    supported: bool
    requires_provider_fanout: bool
    residual_access_token_max_seconds: int | None
    warning_codes: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class GlobalRevocationPreview:
    schema: str
    preview_id: str
    principal_id: str
    generated_at: str
    expires_at: str
    selected_scopes: tuple[RevocationScope, ...]
    blast_radius: RevocationBlastRadius
    targets: tuple[RevocationPreviewTarget, ...]
    ambiguity_resolved: bool
    requires_step_up: bool
    minimum_assurance: AssuranceLevel
    phishing_resistant_step_up_required: bool
    redaction: RevocationRedaction

@dataclass(frozen=True, slots=True)
class RevocationStepUp:
    actor_principal_id: str
    actor_session_id_hash: str
    evidence_id_hash: str
    assurance: AssuranceLevel
    auth_methods: tuple[AuthMethod, ...]
    phishing_resistant: bool
    verified_at: str
    fresh_until: str
    def sufficient(self) -> bool:
        return self.assurance in {AssuranceLevel.AAL2, AssuranceLevel.AAL3} and self.phishing_resistant and AuthMethod.WEBAUTHN in self.auth_methods

@dataclass(frozen=True, slots=True)
class RevocationRequestCorrelation:
    request_id: str
    trace_id: str
    reason_code: str
    ticket_reference_hash: str | None

@dataclass(frozen=True, slots=True)
class GlobalRevocationRequest:
    schema: str
    principal_id: str
    preview_id: str
    idempotency_key: str
    selected_scopes: tuple[RevocationScope, ...]
    principal_selection_confirmed: bool
    requested_at: str
    step_up: RevocationStepUp
    correlation: RevocationRequestCorrelation
    redaction: RevocationRedaction

@dataclass(frozen=True, slots=True)
class RevocationTargetResult:
    target_id_hash: str
    identity: ProviderIdentityRef
    scope: RevocationScope
    state: RevocationTargetState
    attempt_count: int
    retryable: bool
    last_attempt_at: str | None
    next_attempt_at: str | None
    retry_after_seconds: int | None
    completed_at: str | None
    result_code: str | None
    provider_request_id_hash: str | None
    residual_access_token_max_seconds: int | None

@dataclass(frozen=True, slots=True)
class RevocationFence:
    applied_at: str
    not_before: str
    previous_auth_epoch: int
    auth_epoch: int
    effective: bool

@dataclass(frozen=True, slots=True)
class RevocationAuditCorrelation:
    audit_event_id: str
    correlation_id: str
    request_id: str
    trace_id: str
    actor_principal_id: str
    actor_session_id_hash: str
    idempotency_key_hash: str
    reason_code: str
    raw_emails_present: bool
    raw_tokens_present: bool
    raw_biometric_material_present: bool

@dataclass(frozen=True, slots=True)
class GlobalRevocationOperation:
    schema: str
    operation_id: str
    principal_id: str
    preview_id: str
    state: RevocationJobState
    selected_scopes: tuple[RevocationScope, ...]
    created_at: str
    updated_at: str
    completed_at: str | None
    fence: RevocationFence
    targets: tuple[RevocationTargetResult, ...]
    audit: RevocationAuditCorrelation
    redaction: RevocationRedaction
