export type AuthMethod = "jwt" | "oidc" | "webauthn" | "totp" | "kerberos" | "ssh" | "openpgp" | "platform_biometric" | "recovery";
export type AssuranceLevel = "aal0" | "aal1" | "aal2" | "aal3";
export type DirectoryAdminScope = "directory.dashboard.read" | "directory.users.read" | "directory.sessions.read" | "directory.roles.read" | "directory.revocations.read" | "directory.revocations.execute";
export type DirectoryAdminRole = "directory_admin" | "directory_security_operator" | "directory_auditor";
export type PrincipalSearchState = "no_match" | "unique" | "ambiguous";
export type RevocationScope = "interactive_sessions" | "refresh_token_families" | "offline_grants" | "downstream_sessions" | "impersonation_sessions" | "user_api_credentials" | "registered_device_sessions";
export type RevocationJobState = "queued" | "running" | "partial" | "succeeded" | "failed" | "cancelled";
export type RevocationTargetState = "pending" | "running" | "retry_scheduled" | "succeeded" | "failed" | "skipped" | "unsupported";
export type PrincipalKind = "human" | "service" | "workload" | "device" | "automation";
export interface PrincipalRef { tenantId: string; subject: string; kind: PrincipalKind; organization?: string; displayName?: string; }
export interface RequestContext { requestId: string; traceId: string; spanId?: string; tenantId?: string; clientId?: string; source?: string; }
export interface ErrorEnvelope { code: string; message: string; retryable: boolean; requestId: string; details?: Record<string, unknown>; }
export interface TokenClaims { iss: string; sub: string; aud: string[]; exp: number; iat: number; authTime?: number; jti: string; tenantId: string; sessionId: string; aal: AssuranceLevel; amr: AuthMethod[]; scopes: string[]; }
export interface PlatformBiometricProof { verifiedByPlatformAuthenticator: true; userVerification: "required"; modalityHint?: "face" | "fingerprint" | "unknown"; rawBiometricMaterialPresent: false; }
export interface RevocationRedaction { rawEmailsPresent: false; rawTokensPresent: false; rawSessionIdentifiersPresent: false; rawBiometricMaterialPresent: false; }
export interface ProviderIdentityRef { providerId: string; providerTenantId: string; opaqueIdentityHandle: string; }
export interface PrincipalSearchRequest { schema: "ores.shared-auth-admin-principal-search-request/v1"; requestId: string; requestedByPrincipalId: string; emailSearchKeyHash: string; purpose: "operator_email_search"; requestedAt: string; redaction: RevocationRedaction; }
export interface PrincipalSearchCandidate { principalId: string; identities: ProviderIdentityRef[]; organizationCount: number; activeSessionCount: number; }
export interface PrincipalSearchResult { schema: "ores.shared-auth-admin-principal-search-result/v1"; lookupId: string; emailSearchKeyHash: string; state: PrincipalSearchState; candidates: PrincipalSearchCandidate[]; requiresExplicitPrincipalSelection: boolean; generatedAt: string; redaction: RevocationRedaction; }
export interface RevocationBlastRadius { providerTenantCount: number; identityCount: number; organizationCount: number; projectCount: number; interactiveSessionCount: number; refreshTokenFamilyCount: number; offlineGrantCount: number; downstreamSessionCount: number; impersonationSessionCount: number; userApiCredentialCount: number; registeredDeviceSessionCount: number; }
export interface RevocationPreviewTarget { targetIdHash: string; identity: ProviderIdentityRef; scope: RevocationScope; estimatedResourceCount: number; supported: boolean; requiresProviderFanout: boolean; residualAccessTokenMaxSeconds: number | null; warningCodes: string[]; }
export interface GlobalRevocationPreview { schema: "ores.shared-auth-admin-global-revocation-preview/v1"; previewId: string; principalId: string; generatedAt: string; expiresAt: string; selectedScopes: RevocationScope[]; blastRadius: RevocationBlastRadius; targets: RevocationPreviewTarget[]; ambiguityResolved: true; requiresStepUp: true; minimumAssurance: "aal2"; phishingResistantStepUpRequired: true; redaction: RevocationRedaction; }
export interface RevocationStepUp { actorPrincipalId: string; actorSessionIdHash: string; evidenceIdHash: string; assurance: "aal2" | "aal3"; authMethods: AuthMethod[]; phishingResistant: true; verifiedAt: string; freshUntil: string; }
export interface RevocationRequestCorrelation { requestId: string; traceId: string; reasonCode: string; ticketReferenceHash?: string; }
export interface GlobalRevocationRequest { schema: "ores.shared-auth-admin-global-revocation-request/v1"; principalId: string; previewId: string; idempotencyKey: string; selectedScopes: RevocationScope[]; principalSelectionConfirmed: true; requestedAt: string; stepUp: RevocationStepUp; correlation: RevocationRequestCorrelation; redaction: RevocationRedaction; }
export interface RevocationTargetResult { targetIdHash: string; identity: ProviderIdentityRef; scope: RevocationScope; state: RevocationTargetState; attemptCount: number; retryable: boolean; lastAttemptAt?: string; nextAttemptAt?: string; retryAfterSeconds?: number; completedAt?: string; resultCode?: string; providerRequestIdHash?: string; residualAccessTokenMaxSeconds: number | null; }
export interface RevocationFence { appliedAt: string; notBefore: string; previousAuthEpoch: number; authEpoch: number; effective: true; }
export interface RevocationAuditCorrelation { auditEventId: string; correlationId: string; requestId: string; traceId: string; actorPrincipalId: string; actorSessionIdHash: string; idempotencyKeyHash: string; reasonCode: string; rawEmailsPresent: false; rawTokensPresent: false; rawBiometricMaterialPresent: false; }
export interface GlobalRevocationOperation { schema: "ores.shared-auth-admin-global-revocation-operation/v1"; operationId: string; principalId: string; previewId: string; state: RevocationJobState; selectedScopes: RevocationScope[]; createdAt: string; updatedAt: string; completedAt?: string; fence: RevocationFence; targets: RevocationTargetResult[]; audit: RevocationAuditCorrelation; redaction: RevocationRedaction; }
export interface DirectoryAdminGrant { grantId: string; organizationId: string; projectIds?: string[]; scopes: DirectoryAdminScope[]; roles: DirectoryAdminRole[]; grantedAt: string; expiresAt?: string; }
export interface DirectoryAdminGrantSet { schema: "ores.shared-auth-admin-directory-grant-set/v1"; principalId: string; audience: string; assurance: "aal2" | "aal3"; directoryGrants: DirectoryAdminGrant[]; evaluatedAt: string; expiresAt: string; exactOrganizationMatchRequired: true; crossOrganizationFallbackAllowed: false; rawEmailsPresent: false; }
export declare const AuthMethod: Readonly<Record<string, AuthMethod>>;
export declare const AssuranceLevel: Readonly<Record<string, AssuranceLevel>>;
export declare const DirectoryAdminScope: Readonly<Record<string, DirectoryAdminScope>>;
export declare const DirectoryAdminRole: Readonly<Record<string, DirectoryAdminRole>>;
export declare const PrincipalSearchState: Readonly<Record<string, PrincipalSearchState>>;
export declare const RevocationScope: Readonly<Record<string, RevocationScope>>;
export declare const RevocationJobState: Readonly<Record<string, RevocationJobState>>;
export declare const RevocationTargetState: Readonly<Record<string, RevocationTargetState>>;
export declare function isSafePlatformBiometricProof(value: unknown): value is PlatformBiometricProof;
export declare function isSufficientRevocationStepUp(value: unknown): value is RevocationStepUp;
export declare function isTerminalRevocationJobState(value: RevocationJobState): boolean;
