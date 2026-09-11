#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
import pathlib
import re
from typing import Any, Callable

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/schema-ir/v1"
SCHEMA_PATH = CONTRACT / "schema.json"
EXAMPLE_PATH = CONTRACT / "example.json"
TYPES_PATH = CONTRACT / "types.d.ts"
DELETE_ACTIONS = {"noAction", "restrict", "cascade", "setNull"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_authoring_surface(schema: dict[str, Any], types_source: str) -> None:
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema must declare Draft 2020-12")
    require(schema.get("properties", {}).get("schemaVersion", {}).get("const") == "ores.schema-ir.v1", "schemaVersion discriminator drifted")
    schema_actions = set(schema["$defs"]["foreignKey"]["properties"]["onDelete"]["enum"])
    require(schema_actions == DELETE_ACTIONS, f"JSON Schema onDelete actions drifted: {sorted(schema_actions)!r}")
    match = re.search(r'export type ForeignKeyDeleteAction\s*=\s*([^;]+);', types_source)
    require(match is not None, "TypeScript ForeignKeyDeleteAction declaration is missing")
    type_actions = set(re.findall(r'"([A-Za-z]+)"', match.group(1)))
    require(type_actions == DELETE_ACTIONS, f"TypeScript onDelete actions drifted: {sorted(type_actions)!r}")
    require('readonly schemaVersion: "ores.schema-ir.v1"' in types_source, "TypeScript schemaVersion discriminator drifted")


def field_map(entity: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields = entity["fields"]
    names = [field["name"] for field in fields]
    columns = [field["column"] for field in fields]
    require(len(names) == len(set(names)), f"entity {entity['name']} has duplicate field names")
    require(len(columns) == len(set(columns)), f"entity {entity['name']} has duplicate SQL column names")
    return {field["name"]: field for field in fields}


def validate_key(entity: dict[str, Any], fields: dict[str, dict[str, Any]], key: list[str], label: str) -> None:
    require(len(key) == len(set(key)), f"entity {entity['name']} {label} repeats fields")
    for name in key:
        require(name in fields, f"entity {entity['name']} {label} references unknown field {name}")


def validate_semantics(document: dict[str, Any]) -> None:
    entities = document["entities"]
    entity_names = [entity["name"] for entity in entities]
    table_names = [entity["table"] for entity in entities]
    require(len(entity_names) == len(set(entity_names)), "duplicate entity names")
    require(len(table_names) == len(set(table_names)), "duplicate SQL table names")

    by_name = {entity["name"]: entity for entity in entities}
    fields_by_entity: dict[str, dict[str, dict[str, Any]]] = {}
    candidate_keys: dict[str, set[tuple[str, ...]]] = {}

    for entity in entities:
        fields = field_map(entity)
        fields_by_entity[entity["name"]] = fields
        primary = entity["primaryKey"]
        validate_key(entity, fields, primary, "primaryKey")
        for name in primary:
            field = fields[name]
            require(field["required"] is True, f"entity {entity['name']} primary key field {name} must be required")
            require(field["nullable"] is False, f"entity {entity['name']} primary key field {name} must be non-nullable")

        declared_keys = {tuple(primary)}
        for index, key in enumerate(entity.get("uniqueKeys", [])):
            validate_key(entity, fields, key, f"uniqueKeys[{index}]")
            declared_keys.add(tuple(key))
        for index, key in enumerate(entity.get("indexes", [])):
            validate_key(entity, fields, key, f"indexes[{index}]")
        candidate_keys[entity["name"]] = declared_keys

    for entity in entities:
        fields = fields_by_entity[entity["name"]]
        for index, foreign_key in enumerate(entity.get("foreignKeys", [])):
            local_names = foreign_key["fields"]
            reference = foreign_key["references"]
            target_name = reference["entity"]
            target_names = reference["fields"]
            label = f"foreignKeys[{index}]"
            validate_key(entity, fields, local_names, label)
            require(target_name in by_name, f"entity {entity['name']} {label} references unknown entity {target_name}")
            target_fields = fields_by_entity[target_name]
            require(len(local_names) == len(target_names), f"entity {entity['name']} {label} arity does not match target")
            require(tuple(target_names) in candidate_keys[target_name], f"entity {entity['name']} {label} target is not an exact primary/unique key")
            for local_name, target_field_name in zip(local_names, target_names, strict=True):
                require(target_field_name in target_fields, f"entity {entity['name']} {label} target field {target_field_name} is unknown")
                local_type = fields[local_name]["type"]
                target_type = target_fields[target_field_name]["type"]
                require(local_type == target_type, f"entity {entity['name']} {label} type mismatch: {local_name}={local_type}, {target_name}.{target_field_name}={target_type}")
            action = foreign_key.get("onDelete", "noAction")
            require(action in DELETE_ACTIONS, f"entity {entity['name']} {label} has unsupported onDelete={action}")
            if action == "setNull":
                for local_name in local_names:
                    require(fields[local_name]["nullable"] is True, f"entity {entity['name']} {label} setNull requires nullable field {local_name}")


def expect_semantic_failure(example: dict[str, Any], mutate: Callable[[dict[str, Any]], None], expected: str) -> None:
    candidate = deepcopy(example)
    mutate(candidate)
    try:
        validate_semantics(candidate)
    except AssertionError as error:
        require(expected in str(error), f"negative control failed for the wrong reason: {error}")
        return
    raise AssertionError(f"negative control unexpectedly passed; expected {expected!r}")


def validate_negative_controls(example: dict[str, Any]) -> None:
    def nullable_primary_key(candidate: dict[str, Any]) -> None:
        candidate["entities"][0]["fields"][0]["nullable"] = True

    def duplicate_column(candidate: dict[str, Any]) -> None:
        candidate["entities"][1]["fields"][1]["column"] = "id"

    def non_candidate_fk_target(candidate: dict[str, Any]) -> None:
        candidate["entities"][1]["foreignKeys"][0]["references"]["fields"] = ["slug", "id"]

    def mismatched_fk_type(candidate: dict[str, Any]) -> None:
        candidate["entities"][1]["fields"][1]["type"] = "string"

    def invalid_set_null(candidate: dict[str, Any]) -> None:
        candidate["entities"][1]["foreignKeys"][0]["onDelete"] = "setNull"

    expect_semantic_failure(example, nullable_primary_key, "must be non-nullable")
    expect_semantic_failure(example, duplicate_column, "duplicate SQL column names")
    expect_semantic_failure(example, non_candidate_fk_target, "arity does not match target")
    expect_semantic_failure(example, mismatched_fk_type, "type mismatch")
    expect_semantic_failure(example, invalid_set_null, "setNull requires nullable field")


def main() -> None:
    schema = load_json(SCHEMA_PATH)
    example = load_json(EXAMPLE_PATH)
    types_source = TYPES_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.absolute_path))
    require(not errors, "example.json failed structural validation: " + "; ".join(error.message for error in errors[:5]))
    validate_authoring_surface(schema, types_source)
    validate_semantics(example)
    validate_negative_controls(example)
    print("schema-ir-v1 admission passed: Draft 2020-12, authoring parity, relational semantics, and negative controls")


if __name__ == "__main__":
    main()
