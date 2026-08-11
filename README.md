# ores-interfaces

Canonical, language-neutral interfaces shared across OreSoftware organizations.

The repository is deliberately **contract-first**. `contracts/ores-platform/v1/schema.json`
is the authority for portfolio-wide identity, request, error, capability, and security-event
shapes. `contracts/shared-auth-admin/v1/schema.json` adds the read-only organization dashboard
projection used by Shared Auth and the additive global session-revocation workflow described
below. Product repositories may extend these types in their own namespaces, but must not
weaken tenant, audience, assurance, retention, pagination, or redaction semantics.

## Layout

- `contracts/ores-platform/v1` — portfolio-wide JSON Schema 2020-12 contracts.
- `contracts/shared-auth-admin/v1` — organization dropdown, project scope, users, sessions,
  role bindings, capability truth, and dashboard redaction contracts.
- `languages/rust` — zero-dependency Rust data types.
- `languages/typescript` — runtime constants plus TypeScript declarations.
- `languages/go` — Go structs and enums.
- `languages/python` — Python enums and dataclasses.
- `languages/dart` — Dart enums and immutable value types.
- `languages/java` — Java 17 records and enums.
- `languages/swift` — Swift `Codable` value types.
- `scripts/check_contracts.py` — offline drift, capability-truth, redaction, and secret-safety
  checks.

## Shared Auth administration boundary

The dashboard contract is intentionally read-only and organization-scoped:

- every request selects an exact organization; there is no cross-organization fallback;
- role bindings always carry an explicit organization/project/repository scope;
- session IDs, bearer tokens, raw IP addresses, and biometric material never enter the view;
- SSH and Kerberos capability records require online introspection and cannot exceed AAL1;
- OpenPGP is provenance-only and cannot mint a Shared Auth token;
- face/fingerprint/thumbprint language means local platform-authenticator user verification
  behind WebAuthn, not collection or retention of images or templates;
- non-implemented capabilities must advertise `productionEnabled: false`.

## Safe global session revocation

The revocation workflow is deliberately separate from the existing read projections:

1. A trusted edge accepts an operator-entered email only long enough to normalize it and
   compute a domain-separated keyed digest. Canonical contracts, examples, jobs, and audit
   events never contain the raw address.
2. `PrincipalSearchResult` can return no match, one match, or multiple candidates. A candidate
   carries an immutable `principalId` plus provider tenant and internal opaque identity handles;
   an ambiguous result requires explicit principal selection.
3. `GlobalRevocationPreview` freezes the selected scopes and displays the complete provider,
   organization, project, session, grant, credential, and device-session blast radius before
   execution.
4. `GlobalRevocationRequest` requires the unexpired preview, a caller idempotency key, explicit
   principal confirmation, and a fresh phishing-resistant WebAuthn step-up at AAL2 or AAL3.
   The server clock must fall between `verifiedAt` and `freshUntil`; caller timestamps are not
   themselves evidence of freshness. Reusing an idempotency key with different principal,
   preview, or scope values is a conflict, not a second operation.
5. Creating `GlobalRevocationOperation` atomically increments the principal auth epoch and
   records a `notBefore` fence before provider fan-out starts. Shared Auth authorizers reject
   older tokens even when a provider is unavailable or a provider JWT remains valid until its
   expiry.
6. Each provider target reports a redacted machine result, retryability, attempts, and bounded
   retry timing. `retry_scheduled` requires both `nextAttemptAt` and a positive
   `retryAfterSeconds`; terminal targets (`succeeded`, `failed`, `skipped`, or `unsupported`)
   carry neither field. A job can truthfully finish `partial`; it must never report success
   while a mandatory target failed or is unsupported.

The operation never carries raw provider tokens, raw session identifiers, raw email addresses,
provider response bodies, free-form provider errors, face data, or fingerprint data. Provider
identity handles and audit identifiers are internal opaque values or keyed digests. Idempotency
keys are write-only and only their keyed digests appear in responses and audit records.

### Compatibility

The dashboard query, response, user, session, role, organization, project, and capability
definitions retain their v1 fields and semantics. Revocation adds new discriminator values and
new `$defs` only. Consumers that do not implement mutation contracts can continue using the
read projections; exhaustive discriminator consumers should negotiate or reject unknown
contract names rather than silently interpreting them.

## Authentication boundaries

`platform_biometric` means a platform authenticator performed local user verification
(WebAuthn/passkey). Raw face images, face templates, fingerprint images, fingerprint
templates, or modality-specific secrets are never part of these contracts. OpenPGP is a
provenance mechanism. Kerberos and SSH integrations use bounded, audience-specific,
revocation-aware credential exchanges; PAC groups, Unix principals, and key comments never
grant application roles directly.

## Zed package

```sh
zed add ores-otel/ores-interfaces@^0.1
zed install
```

After the first registry-backed resolution creates and commits `.zpkg.lock`, CI and
repeatable deployments should use:

```sh
zed install --frozen
```

The root `.zpkg.toml` publishes one coordinated package with per-language targets. A
placeholder lock is intentionally not committed because it would not prove artifact
provenance or direct dependency coverage.
