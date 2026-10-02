# Compiler-backed shared public contracts

Tracks DEN-3828 and ORESoftware/typespec-json-schema-validator#20. This is the
public compatibility source consumed by ORESoftware/ores-interfaces, not a new
copy of the portfolio's auth or platform contracts.

TypeSpec and hand-authored JSON Schema remain independent peers. Three existing
models retain their assertions; their existing aggregate has an emitted named
union and explicit resource IDs so all four declarations are checked. The root
JSON Schema pointers remain compatible. Object closure stays additionalProperties,
not a silent replacement with unevaluatedProperties. Runtime implementations and
other contract families are not certified by this gate.

Provision `.deps/tjsv` at `d60d0d79d83e075077382623ec9e23a401ab601f` and run
`npm ci --prefix .deps/tjsv` (the canonical flags2env addon needs its install hook).
Then run `node validation/tjsv/admission.mjs` and
`node --test validation/tjsv/admission.test.mjs`.

The reusable `withPublicAdmission` function runs the canonical TJSV CLI twice:
real compilation/comparison with both synthesized probes and the 31 recorded
cases, then exact-current-input `verify-ir` with the complete declaration list.
Consumers receive evidence and the unchanged source bytes only after both pass.
Each invocation owns fresh temporary files and removes only those files. No old
passing receipt is reused, and no generated witness becomes an editable source.
A callback may assemble a derived package; it must not claim that hashing bytes
alone proves admission, publisher authenticity, or all-language equivalence.
