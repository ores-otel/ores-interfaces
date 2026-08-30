# Schema IR v1 — bounded compiler foundation

This is the **intermediate contract**, not a new product database authority and
not a replacement for JSON Schema, TypeSpec, CUE, or DPM. A frontend can lower
its checked model into this representation. The initial reference compiler is
in `ores-otel/ores-lib-core`, under
`languages/typescript/src/schema-compiler/`.

The meta-schema and immutable declarations belong in `ores-interfaces`.
Human-authored product persistence inputs, interface-to-storage mappings,
desired SQL, generator pins, and migration history continue to belong in that
product's `*-lib-core`. The example is synthetic; it is not Shared Auth's schema.

## V1 profile

- A document explicitly selects `ores.schema-ir.v1` and declares 1–64 models.
  Each model has 1–128 fields. Names are bounded portable ASCII identifiers.
- Scalars are `string`, `boolean`, signed `int32`, and canonical lowercase
  hyphenated `uuid`. String length constraints count Unicode code points.
- Every field explicitly declares **required** (property presence) and
  **nullable** (whether its value may be null). These are independent.
- Storage is optional. When present, it declares a schema/table, a complete
  one-to-one field/column mapping, a primary key, unique keys, and foreign keys.
  All persisted row fields must be required. Represent PATCH/input DTOs as
  separate non-persisted models; SQL NULL must not silently erase absence.
- Foreign keys resolve within the same document, match declared candidate keys
  in their declared order, and use matching scalar types. `setNull` requires
  nullable referencing fields. Composite keys and reference cycles are allowed.
- Unknown versions, keys, and types are errors. Defaults, expressions, unions,
  inheritance, arbitrary indexes, decimals/int64, generated columns, arbitrary
  checks, partial indexes, RLS, and raw SQL are deliberately unsupported.

## Structural and semantic validation

`schema.json` validates structure. **Passing the meta-schema alone is not
permission to emit or deploy SQL.** The compiler additionally checks name
uniqueness, length consistency, complete mappings, key/reference integrity,
non-null primary keys, PostgreSQL system names, and generated SQL-name collisions.
The JavaScript entrypoint accepts JSON data, not executable JavaScript objects;
it rejects accessors, cycles, sparse arrays, non-JSON values, excessive nesting,
and excessively large graphs. It returns diagnostics without echoing input values.

The generated JSON Schema bundle validates any declared model at its root.
A consumer requiring a specific model must select its `$defs` entry. Database
uniqueness and foreign keys are cross-row constraints, not JSON instance rules.
TypeScript declarations express shapes, not runtime UUID/length/integer checks.
Consumers should enable `strictNullChecks` and `exactOptionalPropertyTypes`.

## Checks

From `languages/typescript`:

```sh
node --test test/schema-ir-contract.test.js
tsc --noEmit --strict --exactOptionalPropertyTypes --target es2022 \
  --module nodenext --moduleResolution nodenext test/schema-ir.types.ts
```

The Node checks are structural contract smoke tests, not a general JSON Schema
validator. Independently validate `schema.json` with Draft 2020-12 and validate
`examples/team-directory.json` before publishing a new contract version. The
repository already pins its independent validator in
`scripts/requirements-contracts.lock`; no additional dependency is introduced.

## Next slices and proof boundary

1. Add a pinned TypeSpec emitter (compiler API, not source-text parsing) and a CUE
   lowering path. Both must reject constraints they cannot preserve.
2. Add Rust/Dart/Go emitters and real compiler/runtime conformance tests. Do not
   claim that generating declarations also generates validation or serialization.
3. Expand the IR with explicit semantic constraints and persistence capabilities,
   preserving version negotiation and conformance fixtures.
4. Feed desired SQL to the existing
   `declarative-migrations/declarative-postgres-migrate.rs` shadow-database
   `diff`/`verify` flow, then generate ORM adapters and publish pinned Zed artifacts.

No frontend lowerer, ORM adapter, database convergence proof, runtime deployment,
or cross-language parity is claimed by this foundation.

## Design references

- https://typespec.io/docs/extending-typespec/emitters-basics/
- https://json-schema.org/understanding-json-schema/reference/object
- https://json-schema.org/understanding-json-schema/reference/null
- https://www.postgresql.org/docs/current/ddl-constraints.html
