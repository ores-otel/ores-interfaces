enum AuthMethod { jwt, oidc, webauthn, totp, kerberos, ssh, openpgp, platformBiometric, recovery }
enum AssuranceLevel { aal0, aal1, aal2, aal3 }
enum PrincipalSearchState {
  noMatch('no_match'), unique('unique'), ambiguous('ambiguous');
  const PrincipalSearchState(this.wireValue);
  final String wireValue;
}
enum RevocationScope {
  interactiveSessions('interactive_sessions'),
  refreshTokenFamilies('refresh_token_families'),
  offlineGrants('offline_grants'),
  downstreamSessions('downstream_sessions'),
  impersonationSessions('impersonation_sessions'),
  userApiCredentials('user_api_credentials'),
  registeredDeviceSessions('registered_device_sessions');
  const RevocationScope(this.wireValue);
  final String wireValue;
}
enum RevocationJobState {
  queued('queued', false), running('running', false), partial('partial', true),
  succeeded('succeeded', true), failed('failed', true), cancelled('cancelled', true);
  const RevocationJobState(this.wireValue, this.terminal);
  final String wireValue;
  final bool terminal;
}
enum RevocationTargetState {
  pending('pending'), running('running'), retryScheduled('retry_scheduled'),
  succeeded('succeeded'), failed('failed'), skipped('skipped'), unsupported('unsupported');
  const RevocationTargetState(this.wireValue);
  final String wireValue;
}
final class PrincipalRef {
  const PrincipalRef({required this.tenantId, required this.subject, required this.kind, this.organization, this.displayName});
  final String tenantId; final String subject; final String kind; final String? organization; final String? displayName;
}
final class PlatformBiometricProof {
  const PlatformBiometricProof({required this.verifiedByPlatformAuthenticator, required this.userVerification, this.rawBiometricMaterialPresent = false});
  final bool verifiedByPlatformAuthenticator; final String userVerification; final bool rawBiometricMaterialPresent;
  bool get safe => verifiedByPlatformAuthenticator && userVerification == 'required' && !rawBiometricMaterialPresent;
}
final class RevocationRedaction {
  const RevocationRedaction({required this.rawEmailsPresent, required this.rawTokensPresent, required this.rawSessionIdentifiersPresent, required this.rawBiometricMaterialPresent});
  final bool rawEmailsPresent; final bool rawTokensPresent; final bool rawSessionIdentifiersPresent; final bool rawBiometricMaterialPresent;
}
final class ProviderIdentityRef {
  const ProviderIdentityRef({required this.providerId, required this.providerTenantId, required this.opaqueIdentityHandle});
  final String providerId; final String providerTenantId; final String opaqueIdentityHandle;
}
final class PrincipalSearchRequest {
  const PrincipalSearchRequest({required this.schema, required this.requestId, required this.requestedByPrincipalId, required this.emailSearchKeyHash, required this.purpose, required this.requestedAt, required this.redaction});
  final String schema; final String requestId; final String requestedByPrincipalId; final String emailSearchKeyHash; final String purpose; final String requestedAt; final RevocationRedaction redaction;
}
final class PrincipalSearchCandidate {
  const PrincipalSearchCandidate({required this.principalId, required this.identities, required this.organizationCount, required this.activeSessionCount});
  final String principalId; final List<ProviderIdentityRef> identities; final int organizationCount; final int activeSessionCount;
}
final class PrincipalSearchResult {
  const PrincipalSearchResult({required this.schema, required this.lookupId, required this.emailSearchKeyHash, required this.state, required this.candidates, required this.requiresExplicitPrincipalSelection, required this.generatedAt, required this.redaction});
  final String schema; final String lookupId; final String emailSearchKeyHash; final PrincipalSearchState state; final List<PrincipalSearchCandidate> candidates; final bool requiresExplicitPrincipalSelection; final String generatedAt; final RevocationRedaction redaction;
}
final class RevocationBlastRadius {
  const RevocationBlastRadius({required this.providerTenantCount, required this.identityCount, required this.organizationCount, required this.projectCount, required this.interactiveSessionCount, required this.refreshTokenFamilyCount, required this.offlineGrantCount, required this.downstreamSessionCount, required this.impersonationSessionCount, required this.userApiCredentialCount, required this.registeredDeviceSessionCount});
  final int providerTenantCount; final int identityCount; final int organizationCount; final int projectCount; final int interactiveSessionCount; final int refreshTokenFamilyCount; final int offlineGrantCount; final int downstreamSessionCount; final int impersonationSessionCount; final int userApiCredentialCount; final int registeredDeviceSessionCount;
}
final class RevocationPreviewTarget {
  const RevocationPreviewTarget({required this.targetIdHash, required this.identity, required this.scope, required this.estimatedResourceCount, required this.supported, required this.requiresProviderFanout, required this.residualAccessTokenMaxSeconds, required this.warningCodes});
  final String targetIdHash; final ProviderIdentityRef identity; final RevocationScope scope; final int estimatedResourceCount; final bool supported; final bool requiresProviderFanout; final int? residualAccessTokenMaxSeconds; final List<String> warningCodes;
}
final class GlobalRevocationPreview {
  const GlobalRevocationPreview({required this.schema, required this.previewId, required this.principalId, required this.generatedAt, required this.expiresAt, required this.selectedScopes, required this.blastRadius, required this.targets, required this.ambiguityResolved, required this.requiresStepUp, required this.minimumAssurance, required this.phishingResistantStepUpRequired, required this.redaction});
  final String schema; final String previewId; final String principalId; final String generatedAt; final String expiresAt; final List<RevocationScope> selectedScopes; final RevocationBlastRadius blastRadius; final List<RevocationPreviewTarget> targets; final bool ambiguityResolved; final bool requiresStepUp; final AssuranceLevel minimumAssurance; final bool phishingResistantStepUpRequired; final RevocationRedaction redaction;
}
final class RevocationStepUp {
  const RevocationStepUp({required this.actorPrincipalId, required this.actorSessionIdHash, required this.evidenceIdHash, required this.assurance, required this.authMethods, required this.phishingResistant, required this.verifiedAt, required this.freshUntil});
  final String actorPrincipalId; final String actorSessionIdHash; final String evidenceIdHash; final AssuranceLevel assurance; final List<AuthMethod> authMethods; final bool phishingResistant; final String verifiedAt; final String freshUntil;
  bool get sufficient => (assurance == AssuranceLevel.aal2 || assurance == AssuranceLevel.aal3) && phishingResistant && authMethods.contains(AuthMethod.webauthn);
}
final class RevocationRequestCorrelation {
  const RevocationRequestCorrelation({required this.requestId, required this.traceId, required this.reasonCode, this.ticketReferenceHash});
  final String requestId; final String traceId; final String reasonCode; final String? ticketReferenceHash;
}
final class GlobalRevocationRequest {
  const GlobalRevocationRequest({required this.schema, required this.principalId, required this.previewId, required this.idempotencyKey, required this.selectedScopes, required this.principalSelectionConfirmed, required this.requestedAt, required this.stepUp, required this.correlation, required this.redaction});
  final String schema; final String principalId; final String previewId; final String idempotencyKey; final List<RevocationScope> selectedScopes; final bool principalSelectionConfirmed; final String requestedAt; final RevocationStepUp stepUp; final RevocationRequestCorrelation correlation; final RevocationRedaction redaction;
}
final class RevocationTargetResult {
  const RevocationTargetResult({required this.targetIdHash, required this.identity, required this.scope, required this.state, required this.attemptCount, required this.retryable, this.lastAttemptAt, this.nextAttemptAt, this.retryAfterSeconds, this.completedAt, this.resultCode, this.providerRequestIdHash, required this.residualAccessTokenMaxSeconds});
  final String targetIdHash; final ProviderIdentityRef identity; final RevocationScope scope; final RevocationTargetState state; final int attemptCount; final bool retryable; final String? lastAttemptAt; final String? nextAttemptAt; final int? retryAfterSeconds; final String? completedAt; final String? resultCode; final String? providerRequestIdHash; final int? residualAccessTokenMaxSeconds;
}
final class RevocationFence {
  const RevocationFence({required this.appliedAt, required this.notBefore, required this.previousAuthEpoch, required this.authEpoch, required this.effective});
  final String appliedAt; final String notBefore; final int previousAuthEpoch; final int authEpoch; final bool effective;
}
final class RevocationAuditCorrelation {
  const RevocationAuditCorrelation({required this.auditEventId, required this.correlationId, required this.requestId, required this.traceId, required this.actorPrincipalId, required this.actorSessionIdHash, required this.idempotencyKeyHash, required this.reasonCode, required this.rawEmailsPresent, required this.rawTokensPresent, required this.rawBiometricMaterialPresent});
  final String auditEventId; final String correlationId; final String requestId; final String traceId; final String actorPrincipalId; final String actorSessionIdHash; final String idempotencyKeyHash; final String reasonCode; final bool rawEmailsPresent; final bool rawTokensPresent; final bool rawBiometricMaterialPresent;
}
final class GlobalRevocationOperation {
  const GlobalRevocationOperation({required this.schema, required this.operationId, required this.principalId, required this.previewId, required this.state, required this.selectedScopes, required this.createdAt, required this.updatedAt, this.completedAt, required this.fence, required this.targets, required this.audit, required this.redaction});
  final String schema; final String operationId; final String principalId; final String previewId; final RevocationJobState state; final List<RevocationScope> selectedScopes; final String createdAt; final String updatedAt; final String? completedAt; final RevocationFence fence; final List<RevocationTargetResult> targets; final RevocationAuditCorrelation audit; final RevocationRedaction redaction;
}
