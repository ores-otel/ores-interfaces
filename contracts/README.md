# Contract authority

`ores-platform/v1/schema.json` is the canonical portfolio wire contract.
`shared-auth-admin/v1/schema.json` is the canonical Shared Auth administration contract.
Bindings must preserve:

1. tenant and audience boundaries;
2. fail-closed assurance and authentication-method values;
3. bounded delegation depth;
4. no raw biometric material;
5. no token or secret values in errors, logs, or security events;
6. inactive introspection responses by default when state is unknown.

Shared Auth directory grants additionally require:

1. the wrapped `DirectoryAdminGrantSet` discriminator and payload, never a loose object;
2. exact audience introspection at AAL2 or AAL3 and a required token/session `expiresAt`;
3. canonical UUIDs for grant, organization, and optional project identifiers;
4. exact non-wildcard directory scopes and an explicit `directory_admin` role;
5. no flat organization/project/scope claims outside `directoryGrants`;
6. no raw email field or cross-organization fallback.

Shared Auth global revocation additionally requires:

1. immutable principal IDs; email is a transient operator search input and becomes a keyed
   digest before it enters the canonical contract;
2. explicit ambiguity handling and principal confirmation;
3. provider tenant plus internal opaque identity handles, never raw provider credentials;
4. preview-before-execute blast-radius reporting and explicit revocation scopes;
5. fresh phishing-resistant AAL2-or-higher WebAuthn step-up;
6. an auth-epoch/not-before fence committed before provider fan-out;
7. idempotent durable jobs with honest partial state and per-target bounded retry metadata,
   present only for scheduled retries and absent from terminal target results;
8. redacted audit correlation with no raw tokens, email addresses, session IDs, provider
   response bodies, or biometric material.

Changes require a versioned schema path and compatibility notes. Do not mutate v1 semantics
in place after a stable release. The Shared Auth revocation additions preserve all existing v1
read-projection definitions and add new contract discriminators and definitions only.
