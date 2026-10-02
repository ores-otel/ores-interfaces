# Candidate portable RPC retry contract

Status: **draft contract, not a published/generated SDK or network service**.

This additive profile describes normalized inputs and decisions for the pure retry
planner in `ores-otel/ores-lib-core`. It does not replace any existing Shared Auth
contract, define a database schema, or expose a remotely callable retry endpoint.

## Sources and projections

`main.tsp` is the candidate wire-authoring source. Explicit Protobuf field numbers
are compatibility identities: never renumber/reuse them; reserve removed numbers
and names before release. The exact lockfile pins TypeSpec 1.15.0, its JSON Schema
1.15.0 and Protobuf 0.85.0 emitters, Buf 1.72.0, and Ajv 8.20.0.

`generated/` contains deterministic compiler output. CI compiles twice into
separate temporary roots, byte-compares both runs with the committed artifacts,
and compiles identical Protobuf descriptor sets. `expected/retry.proto` and
`expected/schema.json` remain independently reviewed compatibility projections:
they are semantic vetoes, not compiler output. Emitters never write over
`expected/` or authored persistence JSON Schema.

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

Run from the repository root:

```bash
npm ci --ignore-scripts --prefix contracts/rpc-retry/v1
npm run compile --prefix contracts/rpc-retry/v1
node --test scripts/rpc-contract.test.mjs scripts/rpc-compiler-contract.test.mjs
```

The checks compile TypeSpec twice, compare generated Protobuf and JSON Schema with
both the second run and committed artifacts, compare their semantic projections
with the reviewed fixtures, compile deterministic descriptor sets, run Buf
STANDARD lint, and validate reviewed positive/negative instances with Ajv 2020.
They are still not a generated SDK or cross-language network interoperability test.

OpenAPI is intentionally not emitted by this slice: these are DTOs for a local
retry planner, not an HTTP service. An OpenAPI document belongs with a real HTTP
operation rather than an empty or invented endpoint surface.

Before promoting this profile:

1. Promote the reviewed npm lock into the Zed package/toolchain path and prove an
   install from that package source without changing any resolved bytes.
2. Record an explicit initial Buf baseline; subsequent releases must run breaking
   checks against it. Generate Rust, Dart and TS
   clients; run boundary, malformed-input and codec round-trip tests.
3. Run the same retry fixture corpus and host-adapter tests in native Rust,
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
