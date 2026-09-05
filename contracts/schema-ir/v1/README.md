# Portable relational schema IR v1

Status: **additive pilot, not a replacement for existing contracts**. The compiler
lives in `ores-otel/ores-lib-core`; independent checks live in `ores-otel-e2e`.
This directory owns types and declarations only. It does not own product database
schemas, migration execution, runtime authorization, or a new dependency registry.
Product `*-lib-core` repositories retain persistence authority.

`schema.json` is the structural Draft 2020-12 contract, `types.d.ts` is its immutable
TypeScript authoring interface, and `example.json` is synthetic conformance input.
The exact discriminator is `ores.schema-ir.v1`. Unknown versions and metadata fail
closed instead of silently producing weaker SQL or code. No external references
are required to validate this schema.

## Explicit semantics

- Supported scalars: PostgreSQL-compatible `string`, canonical hyphenated `uuid`,
  signed `int32`, and `boolean`. Int64/decimal/date-time/JSON/arrays/unions are not
  approximated. They require a later version or an explicit supported extension.
- `required` describes **wire presence**. `nullable` independently describes
  whether a present value can be null and whether its SQL column permits NULL.
  Optional non-nullable fields are NOT automatically legal to omit from INSERTs;
  no database defaults are inferred. Create/patch/read projections remain distinct
  future work, not a claim that every domain object is a safe write DTO.
- Tables and columns are explicitly named. Identifiers are ASCII, at most 63
  characters, and quoted by the compiler. Generated model names and field names
  must also pass the compiler's conservative cross-language reserved-name checks.
- Every entity declares a primary key whose fields are required and non-nullable.
  Unique keys, indexes, and foreign keys use **field names**, not SQL column names.
  Composite-key column order is preserved. A foreign-key target must exactly match
  an ordered declared primary/unique key and have matching scalar types/arity.
- Foreign keys use `MATCH SIMPLE` and `ON UPDATE NO ACTION`. `onDelete` accepts
  `noAction`, `restrict`, `cascade`, or `setNull`; omission retains the v1
  `noAction` compatibility default, while new declarations should be explicit.
  `setNull` is valid only when every local foreign-key field is nullable. A second
  declaration cannot assign a different delete policy to the same relationship.
- String length means Unicode code points, not bytes or grapheme clusters. NUL is
  not PostgreSQL TEXT-compatible. Full encoding/serialization interoperability
  still requires a PostgreSQL acceptance run and real language serializers.

The JSON Schema intentionally validates structure, not every relationship between
values. The semantic compiler additionally checks duplicate names, bounds,
reserved/system names, primary-key rules, reference integrity, scalar compatibility,
delete-policy compatibility, and generated SQL relation-name collisions. Structural
validation alone is not permission to generate, migrate, deploy, or authorize
anything.

## Architecture and adoption

TypeSpec/CUE can be future authoring frontends into this IR; existing JSON Schema
stays usable as a generated interchange artifact. **No TypeSpec frontend or
arbitrary JSON-Schema-to-SQL translator is shipped by this pilot.** The compiler
currently emits CUE constraints as an additional validation artifact.

The SQL output is *desired state*, not a migration diff. Feed reviewed desired SQL
into the existing declarative-migrations/Atlas process only after testing schema
changes, existing data, locks, rollback/backfill strategy, and deployment gates.
RLS, grants, extensions, triggers, defaults, encryption and tenant policy are not
invented by this compiler and remain explicit in their existing authorities.

Compiler output is normalized and hashed deterministically. Its manifest names the
actual canonicalization algorithm; it does **not** falsely claim RFC 8785/JCS or
cross-compiler equivalence. Native generated types do not enforce runtime bounds,
UUID validity, authorization, or foreign-key existence.

## Review gates

1. Validate structural fixtures and semantic rejection cases.
2. Compare artifact bytes and SHA-256 digests across declaration permutations.
3. Compile generated TypeScript with strict null and exact-optional checking.
4. Run CUE validation, Rust compilation, Dart analysis, and disposable-PostgreSQL
   constraint tests before promoting this pilot beyond draft status.
5. Verify exact-version/exact-digest installation through Zed after real releases
   exist. A source fixture lock is not a fabricated `.zpkg.lock` or release proof.

References:
- https://json-schema.org/understanding-json-schema/reference/object
- https://www.postgresql.org/docs/current/ddl-constraints.html
- https://cuelang.org/docs/concept/how-cue-works-with-json-schema/
- https://typespec.io/docs/extending-typespec/emitters-basics/
