# Client backpressure telemetry v1

`client-backpressure.tsp` and `client-backpressure.schema.json` are independently authored peer authorities for the same `ores.client.backpressure` event. Neither file is generated from the other. TJSV parity/convergence must pass before a consumer claims cross-language conformance.

The event describes a request that is intentionally held, resumed, dropped, or terminally rejected by a client-side backpressure layer. It is transport-neutral and supports browser `fetch`, generated RPC clients, WebSockets, SSE, and other SDK transports.

## Phases

- `queued`: work remains local rather than being sent;
- `delayed`: a pacing/retry delay is scheduled or extended;
- `resumed`: emitted immediately before the transport sends the request;
- `dropped`: pending work is removed without sending because of cancellation, bounds, timeout/deadline, or shedding;
- `rejected`: a terminal server throttle/overload response will not be retried.

Multiple `delayed` events may occur for one logical request. Event counts are telemetry, not authoritative queue state; a future UI should consume the queue/state model and may use these events for timeline/detail views.

## Safety boundary

The contract intentionally has no field for payloads, request/response bodies, headers, cookies, JWTs, API keys, user email/identity, arbitrary URLs, or raw Redis/lease keys. `operation` and policy identifiers are bounded safe identifiers. Full URLs (especially query strings) must never be stuffed into `operation`.

`quota_fence` remains the wire-compatible name but is serialized as a decimal string so JavaScript does not lose unsigned 64-bit precision. For quota/backpressure it represents the server's monotonic admission sequence used for stale-metadata ordering; it is not a generic resource-ownership fence.

All numeric fields are capped at JavaScript's exact integer range so browser logs/exporters cannot silently round queue sizes, timestamps, or delays.

## Runtime requirements outside the event schema

A conforming queue implementation must also enforce bounded pending item count, serialized bytes, and age/deadline; cancellation before send; idempotency-aware retries; bounded jitter; and monotonic handling of policy/admission metadata. The event schema reports those behaviors but does not itself implement a queue.

Telemetry export is best-effort and recursion-safe. A failing or backpressured telemetry exporter must never block, unblock, reorder, or grow the application request queue.
