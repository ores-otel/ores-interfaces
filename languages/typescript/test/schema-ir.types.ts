import type { SchemaField, SchemaIR } from "../src/schema-ir.js";

const input = {
  version: "ores.schema-ir.v1",
  models: [{ name: "Example", fields: [{ name: "value", type: "string", required: false, nullable: true, maxLength: 20 }] }],
} as const satisfies SchemaIR;
const field: SchemaField = input.models[0].fields[0];
void field;
// @ts-expect-error Unknown versions cannot be assigned to the canonical contract.
const version: SchemaIR["version"] = "ores.schema-ir.v2";
// @ts-expect-error Length constraints apply only to string fields.
const invalid: SchemaField = { name: "flag", type: "boolean", required: true, nullable: false, maxLength: 1 };
// @ts-expect-error The input graph is immutable.
input.models.push({ name: "Other", fields: [] });
void version;
void invalid;
