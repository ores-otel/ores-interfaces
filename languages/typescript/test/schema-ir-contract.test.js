import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../../contracts/schema-ir/v1/", import.meta.url);
const schema = JSON.parse(readFileSync(new URL("schema.json", root), "utf8"));
const fixture = JSON.parse(readFileSync(new URL("examples/team-directory.json", root), "utf8"));

test("IR v1 is a closed, versioned Draft 2020-12 contract", () => {
  assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema");
  assert.equal(schema.properties.version.const, fixture.version);
  assert.equal(schema.additionalProperties, false);
  for (const definition of Object.values(schema.$defs)) {
    if (definition.type === "object") {
      assert.equal(definition.additionalProperties, false);
    }
  }
});

test("all schema references are local and resolve", () => {
  function walk(value) {
    if (value === null || typeof value !== "object") {
      return;
    }
    if (value.$ref) {
      assert.match(value.$ref, /^#\/\$defs\//);
      assert.ok(schema.$defs[value.$ref.slice("#/$defs/".length)]);
    }
    Object.values(value).forEach(walk);
  }
  walk(schema);
});

test("portable identifier patterns reject SQL punctuation and trailing newlines", () => {
  for (const name of ["modelName", "fieldName", "sqlName"]) {
    const pattern = new RegExp(schema.$defs[name].pattern);
    const valid = name === "modelName" ? "Member" : "member";
    assert.ok(pattern.test(valid));
    for (const invalid of [`${valid}\n`, `${valid}\r`, `${valid};`, "a".repeat(64), "é"]) {
      assert.equal(pattern.test(invalid), false);
    }
  }
});

test("fixture distinguishes nullable row values from optional patch properties", () => {
  const row = fixture.models.find((model) => model.name === "Member");
  const patch = fixture.models.find((model) => model.name === "MemberPatch");
  assert.ok(row.fields.every((field) => field.required));
  assert.equal(row.fields.find((field) => field.name === "displayName").nullable, true);
  assert.ok(patch.fields.every((field) => !field.required));
  assert.equal(patch.storage, undefined);
  for (const model of fixture.models) {
    for (const field of model.fields) {
      assert.ok(schema.$defs.field.properties.type.enum.includes(field.type));
      assert.equal(typeof field.required, "boolean");
      assert.equal(typeof field.nullable, "boolean");
    }
  }
});
