package oresinterfaces

type AuthMethod string
const (
    AuthMethodJWT AuthMethod = "jwt"
    AuthMethodOIDC AuthMethod = "oidc"
    AuthMethodWebAuthn AuthMethod = "webauthn"
    AuthMethodTOTP AuthMethod = "totp"
    AuthMethodKerberos AuthMethod = "kerberos"
    AuthMethodSSH AuthMethod = "ssh"
    AuthMethodOpenPGP AuthMethod = "openpgp"
    AuthMethodPlatformBiometric AuthMethod = "platform_biometric"
    AuthMethodRecovery AuthMethod = "recovery"
)

type AssuranceLevel string
const ( Aal0 AssuranceLevel = "aal0"; Aal1 AssuranceLevel = "aal1"; Aal2 AssuranceLevel = "aal2"; Aal3 AssuranceLevel = "aal3" )

type PrincipalSearchState string
const ( PrincipalSearchNoMatch PrincipalSearchState = "no_match"; PrincipalSearchUnique PrincipalSearchState = "unique"; PrincipalSearchAmbiguous PrincipalSearchState = "ambiguous" )

type RevocationScope string
const (
    RevocationInteractiveSessions RevocationScope = "interactive_sessions"
    RevocationRefreshTokenFamilies RevocationScope = "refresh_token_families"
    RevocationOfflineGrants RevocationScope = "offline_grants"
    RevocationDownstreamSessions RevocationScope = "downstream_sessions"
    RevocationImpersonationSessions RevocationScope = "impersonation_sessions"
    RevocationUserAPICredentials RevocationScope = "user_api_credentials"
    RevocationRegisteredDeviceSessions RevocationScope = "registered_device_sessions"
)

type RevocationJobState string
const (
    RevocationQueued RevocationJobState = "queued"
    RevocationRunning RevocationJobState = "running"
    RevocationPartial RevocationJobState = "partial"
    RevocationSucceeded RevocationJobState = "succeeded"
    RevocationFailed RevocationJobState = "failed"
    RevocationCancelled RevocationJobState = "cancelled"
)
func (s RevocationJobState) Terminal() bool { return s == RevocationPartial || s == RevocationSucceeded || s == RevocationFailed || s == RevocationCancelled }

type RevocationTargetState string
const (
    RevocationTargetPending RevocationTargetState = "pending"
    RevocationTargetRunning RevocationTargetState = "running"
    RevocationTargetRetryScheduled RevocationTargetState = "retry_scheduled"
    RevocationTargetSucceeded RevocationTargetState = "succeeded"
    RevocationTargetFailed RevocationTargetState = "failed"
    RevocationTargetSkipped RevocationTargetState = "skipped"
    RevocationTargetUnsupported RevocationTargetState = "unsupported"
)

type PrincipalRef struct { TenantID string `json:"tenantId"`; Subject string `json:"subject"`; Kind string `json:"kind"`; Organization string `json:"organization,omitempty"`; DisplayName string `json:"displayName,omitempty"` }
type RequestContext struct { RequestID string `json:"requestId"`; TraceID string `json:"traceId"`; SpanID string `json:"spanId,omitempty"`; TenantID string `json:"tenantId,omitempty"`; ClientID string `json:"clientId,omitempty"`; Source string `json:"source,omitempty"` }
type ErrorEnvelope struct { Code string `json:"code"`; Message string `json:"message"`; Retryable bool `json:"retryable"`; RequestID string `json:"requestId"`; Details map[string]any `json:"details,omitempty"` }
type PlatformBiometricProof struct { VerifiedByPlatformAuthenticator bool `json:"verifiedByPlatformAuthenticator"`; UserVerification string `json:"userVerification"`; ModalityHint string `json:"modalityHint,omitempty"`; RawBiometricMaterialPresent bool `json:"rawBiometricMaterialPresent"` }
func (p PlatformBiometricProof) Safe() bool { return p.VerifiedByPlatformAuthenticator && p.UserVerification == "required" && !p.RawBiometricMaterialPresent }

type RevocationRedaction struct {
    RawEmailsPresent bool `json:"rawEmailsPresent"`
    RawTokensPresent bool `json:"rawTokensPresent"`
    RawSessionIdentifiersPresent bool `json:"rawSessionIdentifiersPresent"`
    RawBiometricMaterialPresent bool `json:"rawBiometricMaterialPresent"`
}

type ProviderIdentityRef struct {
    ProviderID string `json:"providerId"`
    ProviderTenantID string `json:"providerTenantId"`
    OpaqueIdentityHandle string `json:"opaqueIdentityHandle"`
}

type PrincipalSearchRequest struct {
    Schema string `json:"schema"`
    RequestID string `json:"requestId"`
    RequestedByPrincipalID string `json:"requestedByPrincipalId"`
    EmailSearchKeyHash string `json:"emailSearchKeyHash"`
    Purpose string `json:"purpose"`
    RequestedAt string `json:"requestedAt"`
    Redaction RevocationRedaction `json:"redaction"`
}

type PrincipalSearchCandidate struct {
    PrincipalID string `json:"principalId"`
    Identities []ProviderIdentityRef `json:"identities"`
    OrganizationCount uint64 `json:"organizationCount"`
    ActiveSessionCount uint64 `json:"activeSessionCount"`
}

type PrincipalSearchResult struct {
    Schema string `json:"schema"`
    LookupID string `json:"lookupId"`
    EmailSearchKeyHash string `json:"emailSearchKeyHash"`
    State PrincipalSearchState `json:"state"`
    Candidates []PrincipalSearchCandidate `json:"candidates"`
    RequiresExplicitPrincipalSelection bool `json:"requiresExplicitPrincipalSelection"`
    GeneratedAt string `json:"generatedAt"`
    Redaction RevocationRedaction `json:"redaction"`
}

type RevocationBlastRadius struct {
    ProviderTenantCount uint64 `json:"providerTenantCount"`
    IdentityCount uint64 `json:"identityCount"`
    OrganizationCount uint64 `json:"organizationCount"`
    ProjectCount uint64 `json:"projectCount"`
    InteractiveSessionCount uint64 `json:"interactiveSessionCount"`
    RefreshTokenFamilyCount uint64 `json:"refreshTokenFamilyCount"`
    OfflineGrantCount uint64 `json:"offlineGrantCount"`
    DownstreamSessionCount uint64 `json:"downstreamSessionCount"`
    ImpersonationSessionCount uint64 `json:"impersonationSessionCount"`
    UserAPICredentialCount uint64 `json:"userApiCredentialCount"`
    RegisteredDeviceSessionCount uint64 `json:"registeredDeviceSessionCount"`
}

type RevocationPreviewTarget struct {
    TargetIDHash string `json:"targetIdHash"`
    Identity ProviderIdentityRef `json:"identity"`
    Scope RevocationScope `json:"scope"`
    EstimatedResourceCount uint64 `json:"estimatedResourceCount"`
    Supported bool `json:"supported"`
    RequiresProviderFanout bool `json:"requiresProviderFanout"`
    ResidualAccessTokenMaxSeconds *uint64 `json:"residualAccessTokenMaxSeconds"`
    WarningCodes []string `json:"warningCodes"`
}

type GlobalRevocationPreview struct {
    Schema string `json:"schema"`
    PreviewID string `json:"previewId"`
    PrincipalID string `json:"principalId"`
    GeneratedAt string `json:"generatedAt"`
    ExpiresAt string `json:"expiresAt"`
    SelectedScopes []RevocationScope `json:"selectedScopes"`
    BlastRadius RevocationBlastRadius `json:"blastRadius"`
    Targets []RevocationPreviewTarget `json:"targets"`
    AmbiguityResolved bool `json:"ambiguityResolved"`
    RequiresStepUp bool `json:"requiresStepUp"`
    MinimumAssurance AssuranceLevel `json:"minimumAssurance"`
    PhishingResistantStepUpRequired bool `json:"phishingResistantStepUpRequired"`
    Redaction RevocationRedaction `json:"redaction"`
}

type RevocationStepUp struct {
    ActorPrincipalID string `json:"actorPrincipalId"`
    ActorSessionIDHash string `json:"actorSessionIdHash"`
    EvidenceIDHash string `json:"evidenceIdHash"`
    Assurance AssuranceLevel `json:"assurance"`
    AuthMethods []AuthMethod `json:"authMethods"`
    PhishingResistant bool `json:"phishingResistant"`
    VerifiedAt string `json:"verifiedAt"`
    FreshUntil string `json:"freshUntil"`
}
func (s RevocationStepUp) Sufficient() bool {
    if (s.Assurance != Aal2 && s.Assurance != Aal3) || !s.PhishingResistant { return false }
    for _, method := range s.AuthMethods { if method == AuthMethodWebAuthn { return true } }
    return false
}

type RevocationRequestCorrelation struct { RequestID string `json:"requestId"`; TraceID string `json:"traceId"`; ReasonCode string `json:"reasonCode"`; TicketReferenceHash string `json:"ticketReferenceHash,omitempty"` }

type GlobalRevocationRequest struct {
    Schema string `json:"schema"`
    PrincipalID string `json:"principalId"`
    PreviewID string `json:"previewId"`
    IdempotencyKey string `json:"idempotencyKey"`
    SelectedScopes []RevocationScope `json:"selectedScopes"`
    PrincipalSelectionConfirmed bool `json:"principalSelectionConfirmed"`
    RequestedAt string `json:"requestedAt"`
    StepUp RevocationStepUp `json:"stepUp"`
    Correlation RevocationRequestCorrelation `json:"correlation"`
    Redaction RevocationRedaction `json:"redaction"`
}

type RevocationTargetResult struct {
    TargetIDHash string `json:"targetIdHash"`
    Identity ProviderIdentityRef `json:"identity"`
    Scope RevocationScope `json:"scope"`
    State RevocationTargetState `json:"state"`
    AttemptCount uint32 `json:"attemptCount"`
    Retryable bool `json:"retryable"`
    LastAttemptAt string `json:"lastAttemptAt,omitempty"`
    NextAttemptAt string `json:"nextAttemptAt,omitempty"`
    RetryAfterSeconds *uint64 `json:"retryAfterSeconds,omitempty"`
    CompletedAt string `json:"completedAt,omitempty"`
    ResultCode string `json:"resultCode,omitempty"`
    ProviderRequestIDHash string `json:"providerRequestIdHash,omitempty"`
    ResidualAccessTokenMaxSeconds *uint64 `json:"residualAccessTokenMaxSeconds"`
}

type RevocationFence struct { AppliedAt string `json:"appliedAt"`; NotBefore string `json:"notBefore"`; PreviousAuthEpoch uint64 `json:"previousAuthEpoch"`; AuthEpoch uint64 `json:"authEpoch"`; Effective bool `json:"effective"` }

type RevocationAuditCorrelation struct {
    AuditEventID string `json:"auditEventId"`
    CorrelationID string `json:"correlationId"`
    RequestID string `json:"requestId"`
    TraceID string `json:"traceId"`
    ActorPrincipalID string `json:"actorPrincipalId"`
    ActorSessionIDHash string `json:"actorSessionIdHash"`
    IdempotencyKeyHash string `json:"idempotencyKeyHash"`
    ReasonCode string `json:"reasonCode"`
    RawEmailsPresent bool `json:"rawEmailsPresent"`
    RawTokensPresent bool `json:"rawTokensPresent"`
    RawBiometricMaterialPresent bool `json:"rawBiometricMaterialPresent"`
}

type GlobalRevocationOperation struct {
    Schema string `json:"schema"`
    OperationID string `json:"operationId"`
    PrincipalID string `json:"principalId"`
    PreviewID string `json:"previewId"`
    State RevocationJobState `json:"state"`
    SelectedScopes []RevocationScope `json:"selectedScopes"`
    CreatedAt string `json:"createdAt"`
    UpdatedAt string `json:"updatedAt"`
    CompletedAt string `json:"completedAt,omitempty"`
    Fence RevocationFence `json:"fence"`
    Targets []RevocationTargetResult `json:"targets"`
    Audit RevocationAuditCorrelation `json:"audit"`
    Redaction RevocationRedaction `json:"redaction"`
}
