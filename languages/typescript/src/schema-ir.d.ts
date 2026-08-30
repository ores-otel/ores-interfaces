/** Canonical declarations for contracts/schema-ir/v1/schema.json. */
export type SchemaScalar = "string" | "boolean" | "int32" | "uuid";
export type SchemaField = Readonly<{
  name: string;
  required: boolean;
  nullable: boolean;
}> & (
  | Readonly<{ type: "string"; minLength?: number; maxLength?: number }>
  | Readonly<{ type: Exclude<SchemaScalar, "string">; minLength?: never; maxLength?: never }>
);
export interface SchemaColumn {
  readonly field: string;
  readonly name: string;
}
export interface SchemaForeignKey {
  readonly fields: readonly string[];
  readonly references: Readonly<{ model: string; fields: readonly string[] }>;
  readonly onDelete: "restrict" | "cascade" | "setNull";
}
export interface SchemaStorage {
  readonly schema: string;
  readonly table: string;
  readonly columns: readonly SchemaColumn[];
  readonly primaryKey: readonly string[];
  readonly uniqueKeys: readonly (readonly string[])[];
  readonly foreignKeys: readonly SchemaForeignKey[];
}
export interface SchemaModel {
  readonly name: string;
  readonly fields: readonly SchemaField[];
  readonly storage?: SchemaStorage;
}
export interface SchemaIR {
  readonly version: "ores.schema-ir.v1";
  readonly models: readonly SchemaModel[];
}
