import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

// Fixture-level checks for these four flat models, NOT a TypeSpec/Protobuf compiler.
const root = new URL('../contracts/rpc-retry/v1/', import.meta.url);
const read = (path) => readFileSync(new URL(path, root), 'utf8');
const source = read('main.tsp');
const proto = read('expected/retry.proto');
const generatedProto = read('generated/protobuf/ores/rpc/v1.proto');
const schema = JSON.parse(read('expected/schema.json'));
const names = ['RetryPolicy', 'RetryAttempt', 'RetryInput', 'RetryDecision'];
const clean = (text) => text.replace(/\/\/[^\n]*/g, '');

function fields(text, kind, name) {
  const body = clean(text).match(new RegExp(`\\b${kind} ${name} \\{([^}]+)\\}`))?.[1];
  assert.ok(body, `${kind} ${name} exists`);
  const pattern = kind === 'model'
    ? /@field\((\d+)\)((?:\s+@(?:minValue|maxValue)\(\d+\))*)\s+(\w+)(\?)?:\s*(\w+);/g
    : /\b(optional\s+)?(\w+)\s+(\w+)\s*=\s*(\d+);/g;
  const matches = [...body.matchAll(pattern)];
  assert.equal(body.replace(pattern, '').trim(), '', `unsupported fixture syntax in ${name}`);
  return matches.map((match) => kind === 'model' ? {
    tag: Number(match[1]), name: match[3], optional: Boolean(match[4]),
    type: match[5] === 'boolean' ? 'bool' : match[5],
    minimum: Number(match[2].match(/@minValue\((\d+)\)/)?.[1]),
    maximum: Number(match[2].match(/@maxValue\((\d+)\)/)?.[1]),
  } : { tag: Number(match[4]), name: match[3], optional: Boolean(match[1]), type: match[2] });
}

function verify(name, tsp = source, pb = proto, json = schema) {
  const a = fields(tsp, 'model', name);
  const b = fields(pb, 'message', name);
  assert.deepEqual(a.map(({ tag, name, optional, type }) => ({ tag, name, optional, type })), b);
  assert.equal(new Set(a.map((field) => field.tag)).size, a.length, 'unique stable tags');
  assert.equal(new Set(a.map((field) => field.name)).size, a.length, 'unique field names');
  for (const field of a) {
    assert.ok(field.tag > 0 && field.tag < 536870912 && (field.tag < 19000 || field.tag > 19999));
  }
  const definition = json.$defs[name];
  assert.equal(definition.type, 'object');
  assert.equal(definition.additionalProperties, false);
  assert.deepEqual(Object.keys(definition.properties), a.map((field) => field.name));
  assert.deepEqual(definition.required, a.filter((field) => !field.optional).map((field) => field.name));
  for (const field of a) {
    const property = definition.properties[field.name];
    if (field.type === 'uint32') {
      assert.deepEqual(property, { type: 'integer', minimum: field.minimum, maximum: field.maximum });
    } else if (field.type === 'bool') {
      assert.deepEqual(property, { type: 'boolean' });
    } else {
      assert.deepEqual(property, { $ref: `#/$defs/${field.type}` });
    }
  }
}

for (const name of names) test(`${name}: explicit tags, presence, types and bounds agree`, () => verify(name));
for (const name of names) test(`${name}: emitted Protobuf agrees with reviewed projection`, () => {
  verify(name, source, generatedProto, schema);
});
for (const name of names) test(`${name}: emitted JSON Schema agrees with reviewed projection`, () => {
  const fieldsFromSource = fields(source, 'model', name);
  const generated = JSON.parse(read(`generated/json-schema/${name}.json`));
  const reviewed = schema.$defs[name];
  assert.equal(generated.type, 'object');
  assert.deepEqual(generated.unevaluatedProperties, { not: {} });
  assert.deepEqual(Object.keys(generated.properties), Object.keys(reviewed.properties));
  assert.deepEqual(generated.required, reviewed.required);
  for (const field of fieldsFromSource) {
    const emitted = generated.properties[field.name];
    const expected = reviewed.properties[field.name];
    if (field.type === 'uint32' || field.type === 'bool') {
      assert.deepEqual(emitted, expected);
    } else {
      assert.deepEqual(emitted, { $ref: `${field.type}.json` });
      assert.deepEqual(expected, { $ref: `#/$defs/${field.type}` });
    }
  }
});
test('fixture model inventory is closed and the input root is explicit', () => {
  assert.deepEqual(Object.keys(schema.$defs), names);
  assert.equal(schema.$ref, '#/$defs/RetryInput');
  assert.deepEqual([...clean(source).matchAll(/\bmodel (\w+)\s*\{/g)].map((m) => m[1]), names);
  assert.deepEqual([...clean(proto).matchAll(/\bmessage (\w+)\s*\{/g)].map((m) => m[1]), names);
  assert.deepEqual([...clean(generatedProto).matchAll(/\bmessage (\w+)\s*\{/g)].map((m) => m[1]), names);
  assert.match(proto, /package ores\.rpc\.v1;/);
});
test('presence loss is detected', () => {
  assert.throws(() => verify('RetryAttempt', source, proto.replace('optional uint32 retry_after_ms', 'uint32 retry_after_ms')));
});
test('field renumbering is detected', () => {
  assert.throws(() => verify('RetryPolicy', source, proto.replace('uint32 max_attempts = 1;', 'uint32 max_attempts = 9;')));
});
test('bounds drift is detected', () => {
  const changed = structuredClone(schema);
  changed.$defs.RetryPolicy.properties.max_attempts.maximum = 99;
  assert.throws(() => verify('RetryPolicy', source, proto, changed));
});
test('emitter destinations cannot overwrite reviewed expected fixtures', () => {
  const config = read('tspconfig.yaml');
  assert.match(config, /\{output-dir\}\/protobuf/);
  assert.match(config, /\{output-dir\}\/json-schema/);
  assert.doesNotMatch(config, /emitter-output-dir:.*expected/);
  assert.match(schema.$comment, /not compiler output/);
});
