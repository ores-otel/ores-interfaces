# Candidate portable RPC retry contract

Status: **draft contract, not a published/generated SDK or network service**.

This additive profile describes normalized inputs and decisions for the pure retry
planner in `ores-otel/ores-lib-core`. It does not replace any existing Shared Auth
contract, define a database schema, or expose a remotely callable retry endpoint.

## Sources and projections

`main.tsp` is the candidate wire-authoring input. Explicit Protobuf field numbers
are compatibility identities: never renumber/reuse them; reserve removed numbers
and names before release. `expected/retry.proto` and `expected/schema.json` are
reviewed compatibility fixtures, **not claimed TypeSpec output**. Real emitters
write only under `generated/`, never over `expected/` or authored persistence JSON
Schema. This directory has no fabricated generator/package lock.

The JSON fixture describes **normalized SDK objects**, not raw ProtoJSON. A codec
adapter must materialize implicit Proto3 scalar defaults before validation and
preserve presence for `optional retry_after_ms`. Absence differs from explicit
zero; JSON null is invalid. Message presence must be checked for `policy` and
`attempt`. Missing nonzero-required values such as `max_attempts` fail validation.
All integers and intermediate arithmetic fit exactly in JavaScript and Dart web.

The bounded runtime adds invariants not expressed by these flat wire models:
`max_backoff_ms >= initial_backoff_ms`; retries require `replay_safe`; stop decisions
have zero delay; only reason 1 means retry; and a delay cannot consume the whole
remaining deadline. Never equate structural validation with behavioral parity.

## Retry semantics

`max_attempts` includes the initial request. The planner runs after a completed
failure. Codes 8 (resource exhausted) and 14 (unavailable) are the only retry
candidates. All other codes, including deadline exceeded and transaction abort,
stop. `replay_safe` comes from reviewed method metadata and replayable request
state, not untrusted request fields. An idempotency key alone does not justify
retrying a mutation: server-side atomic deduplication is required.

The host supplies monotonic elapsed milliseconds and a sampled integer jitter in
0..1000. Backoff is capped exponential full jitter. `retry_after_ms` is an optional
server minimum and is never shortened to the local cap or remaining deadline.
The host still owns initial-send checks, cancellation while sleeping/in flight,
per-attempt authentication, transport timeouts, and aggregate retry budgets.

Decision reason numbers: 1 retry; 2 invalid input; 3 cancelled; 4 unsafe replay;
5 attempts exhausted; 6 deadline exhausted; 7 non-retryable status.

## Verification and release gates

Run `node --test scripts/rpc-contract.test.mjs` from the repository root. These are
finite fixture/drift smoke tests, **not a substitute for either compiler**, full
JSON Schema validation, or cross-language network interoperability.

Before promoting this profile:

1. Resolve TypeSpec compiler, Protobuf/JSON Schema emitters, Buf and language
   generators through reviewed Zed package/toolchain pins and real lock digests.
2. Compile twice into separate disposable directories; compare deterministic
   output and normalized semantics against these fixtures. Fail on any warning,
   lossy mapping, missing presence, or unexpected output. The optional-scalar
   emitter must support Proto3 optional fields.
3. Compile a descriptor set; run Buf lint and breaking checks against the prior
   release (or record an explicit initial baseline). Generate Rust, Dart and TS
   clients; run boundary, malformed-input and codec round-trip tests.
4. Run the same retry fixture corpus and host-adapter tests in native Rust,
   Dart VM, Dart web and browser JS before releasing a coordinated SDK package.

## Persistence stays separate

API/wire TypeSpec lives in `*-interfaces`. Persistence TypeSpec P0 and independently
reviewed persistence JSON Schema P1 remain in `*-lib-core`; P1 retains veto power.
Neither this JSON projection nor Protobuf may overwrite P1. Diesel/diesel-async is
the primary runtime ORM; SeaORM is secondary and derived. Both use parity-certified
persistence artifacts plus identical PostgreSQL extensions. ORM models, driver
errors, credentials, and SQL do not become browser/Flutter DTOs. No DDL, provider
configuration, ORM switch, package publication, or production route is enabled here.

References: [TypeSpec Protobuf guide](https://typespec.io/docs/emitters/protobuf/guide/),
[JSON Schema emitter](https://typespec.io/docs/emitters/json-schema/reference/emitter/),
and [canonical migration plan](https://linear.app/denman/document/general-migration-plan-f76fadd4cbb2).
