# ORES APM telemetry contract v1

This contract defines a portable, vendor-neutral telemetry envelope for application performance monitoring. It complements OpenTelemetry rather than replacing it.

## Portable process and filesystem telemetry

Common OS/process measurements use OpenTelemetry-compatible meanings where possible: process CPU time/utilization, resident and virtual memory, process disk I/O and operation counts, network I/O, threads, file descriptors/handles, context switches, paging faults and uptime.

Filesystem capacity is intentionally modeled separately from the process. A process does not own host disk capacity. `FilesystemSnapshot.target` is a bounded logical label such as `root`, `data` or `cache`; it is not a raw filesystem path and must not be populated with credentials, usernames or tenant data.

## Runtime telemetry

Heap, GC, event-loop/scheduler and runtime-pool semantics differ across JVM, Go, Node.js, .NET, BEAM, Dart, Python, Ruby and other runtimes. They therefore use `RuntimeMetric.runtime_namespace` plus a namespaced metric name instead of pretending one cross-runtime heap field has identical semantics.

Examples include `jvm.memory.used`, `go.memory.used`, `nodejs.event_loop.utilization`, `dotnet.gc.collections`, `beam.process.count`, `dart.heap.used` and `python.gc.collections` when a runtime adapter can provide them accurately.

## Latency and correlation

`ServicePerformanceSnapshot.latency_seconds` is a histogram. Implementations should use OpenTelemetry HTTP duration conventions when measuring HTTP requests and retain exemplars when trace context is available. Percentiles are derived by backends; they are not emitted as authoritative raw observations.

Trace IDs are 16-byte lowercase hex and span IDs are 8-byte lowercase hex. Attribute cardinality must remain bounded. Do not attach raw URLs with unbounded query strings, raw SQL, raw command lines, environment values, credentials or customer payloads.

## Profiling

Profiling support is capability-declared. `native` means the language/runtime implementation can produce the profile kind directly; `external-adapter` means it is delegated to a profiler/sidecar; `model-only` means the client can transport profile metadata but does not collect it; `unsupported` is explicit. A client must never claim native profiling merely because its platform has an unrelated profiler.

## APM parity target

The v1 contract covers the portable primitives required to integrate with common APM backends and observability stacks:

- metrics, logs, traces, profiles and error/event correlation;
- RED/golden-signal service data;
- process CPU/memory/disk/network telemetry;
- filesystem capacity/utilization;
- runtime-specific heap/GC/scheduler metrics;
- latency histograms and exemplars;
- W3C trace correlation;
- service-topology and SLO input capability declarations;
- profiling capability declarations.

Alert evaluation, anomaly detection, long-term storage, dashboards, topology inference and tail-sampling policy are backend/control-plane responsibilities and are not fabricated inside language SDKs.

## Safety

This contract never carries raw environment variables, raw command-line arguments, credentials, database URLs, customer payloads, heap-dump bytes or filesystem paths. Profile payloads are transported by the profiling/export plane; `ProfileSummary` contains bounded metadata only.
