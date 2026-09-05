/** Canonical authoring types. Runtime structural AND semantic validation is mandatory. */
export interface FieldBase {
  readonly name: string;
  readonly column: string;
  /** Wire presence, not SQL INSERT defaulting. */
  readonly required: boolean;
  readonly nullable: boolean;
}
export type SchemaField = FieldBase & (
  | { readonly type: "string"; readonly minLength?: number; readonly maxLength?: number }
  | { readonly type: "int32"; readonly minimum?: number; readonly maximum?: number }
  | { readonly type: "uuid" | "boolean" }
);
export interface ForeignKey {
  readonly fields: readonly string[];
  readonly references: { readonly entity: string; readonly fields: readonly string[] };
}
export interface SchemaEntity {
  readonly name: string;
  readonly table: string;
  readonly fields: readonly SchemaField[];
  readonly primaryKey: readonly string[];
  readonly uniqueKeys?: readonly (readonly string[])[];
  readonly indexes?: readonly (readonly string[])[];
  readonly foreignKeys?: readonly ForeignKey[];
}
export interface SchemaIrV1 {
  readonly schemaVersion: "ores.schema-ir.v1";
  readonly databaseSchema: string;
  readonly entities: readonly SchemaEntity[];
}
