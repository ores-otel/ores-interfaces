# Legacy `.ores-otel.toml` contract snapshot

This directory is retained as a historical compatibility snapshot only.

The canonical `.ores-otel.toml` v1 authority moved to the dedicated repository:

- repository: `ores-otel/ores-otel-interfaces`
- canonical promotion commit: `b544872d13323de7be19a9d5879c419149679f7a`
- TypeSpec: `contracts/ores-otel-config.v1/main.tsp`
- independently authored Draft 2020-12 JSON Schema: `contracts/ores-otel-config.v1/authored.schema.json`
- fixture corpus: `contracts/ores-otel-config.v1/instances/`

That DEN-4253 contract was created after this snapshot and explicitly owns the parsed
`.ores-otel.toml` v1 data model. New runtimes, linters, generators and consumers must pin
that dedicated authority rather than treating the files in this directory as a second live
schema pair.

## Historical bytes

The retired sources are kept immutable for auditability and migrations from repositories that
were briefly authored against the earlier DEN-390 envelope:

- `ores-otel-config.tsp` Git blob: `d523b16440654f8e7c0c01c16d028f433a24ebe8`
- `ores-otel-config.schema.json` Git blob: `a4119fa13c5692a36ebfe2e92fb3972c94c94b07`
- `examples/.ores-otel.toml` Git blob: `1493432fa4b911f8e1d8193bad0497ae9fdb7310`

Do not evolve v1 semantics here. If compatibility tooling needs to interpret this snapshot,
keep that translation explicit and one-way toward the dedicated authority. Do not merge the
old `version/mode/flags2env/env/client/server` model with the newer
`common/client/server` policy model and call the result canonical.

TypeSpec and JSON Schema in the dedicated repository remain independent peer authorities;
TJSV remains the fail-closed parity/admission gate. Generated schemas or migration projections
are evidence only.
