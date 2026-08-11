#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
from copy import deepcopy
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLATFORM_SCHEMA = ROOT / "contracts/ores-platform/v1/schema.json"
ADMIN_SCHEMA = ROOT / "contracts/shared-auth-admin/v1/schema.json"
ADMIN_EXAMPLE = ROOT / "contracts/shared-auth-admin/v1/examples/dashboard-response.json"
ADMIN_EXAMPLES = ROOT / "contracts/shared-auth-admin/v1/examples"
LANGUAGES = {"rust", "typescript", "go", "python", "dart", "java", "swift"}
AUTH_METHODS = {
    "jwt",
    "oidc",
    "webauthn",
    "totp",
    "kerberos",
    "ssh",
    "openpgp",
    "platform_biometric",
    "recovery",
}
REVOCATION_CONTRACTS = {
    "PrincipalSearchRequest",
    "PrincipalSearchResult",
    "GlobalRevocationPreview",
    "GlobalRevocationRequest",
    "GlobalRevocationOperation",
}
REVOCATION_SCOPES = {
    "interactive_sessions",
    "refresh_token_families",
    "offline_grants",
    "downstream_sessions",
    "impersonation_sessions",
    "user_api_credentials",
    "registered_device_sessions",
}
REVOCATION_JOB_STATES = {"queued", "running", "partial", "succeeded", "failed", "cancelled"}
REVOCATION_TARGET_STATES = {
    "pending",
    "running",
    "retry_scheduled",
    "succeeded",
    "failed",
    "skipped",
    "unsupported",
}
REVOCATION_TYPES = {
    "PrincipalSearchState",
    "RevocationScope",
    "RevocationJobState",
    "RevocationTargetState",
    "RevocationRedaction",
    "ProviderIdentityRef",
    "PrincipalSearchRequest",
    "PrincipalSearchCandidate",
    "PrincipalSearchResult",
    "RevocationBlastRadius",
    "RevocationPreviewTarget",
    "GlobalRevocationPreview",
    "RevocationStepUp",
    "RevocationRequestCorrelation",
    "GlobalRevocationRequest",
    "RevocationTargetResult",
    "RevocationFence",
    "RevocationAuditCorrelation",
    "GlobalRevocationOperation",
}
REVOCATION_FIELDS = {
    "providerTenantId",
    "opaqueIdentityHandle",
    "principalId",
    "emailSearchKeyHash",
    "requiresExplicitPrincipalSelection",
    "selectedScopes",
    "blastRadius",
    "idempotencyKey",
    "phishingResistant",
    "freshUntil",
    "attemptCount",
    "retryable",
    "nextAttemptAt",
    "resultCode",
    "residualAccessTokenMaxSeconds",
    "appliedAt",
    "notBefore",
    "previousAuthEpoch",
    "authEpoch",
    "idempotencyKeyHash",
    "actorSessionIdHash",
    "rawEmailsPresent",
    "rawTokensPresent",
    "rawBiometricMaterialPresent",
}
LANGUAGE_BINDINGS = {
    "rust": ROOT / "languages/rust/src/lib.rs",
    "typescript": ROOT / "languages/typescript/src/index.d.ts",
    "go": ROOT / "languages/go/interfaces.go",
    "python": ROOT / "languages/python/src/ores_interfaces/__init__.py",
    "dart": ROOT / "languages/dart/lib/ores_interfaces.dart",
    "java": ROOT / "languages/java/src/main/java/com/oresoftware/interfaces/AuthContracts.java",
    "swift": ROOT / "languages/swift/Sources/OresInterfaces/OresInterfaces.swift",
}
REVOCATION_EXAMPLE_NAMES = {
    "principal-search-request.json",
    "principal-search-result.json",
    "global-revocation-preview.json",
    "global-revocation-request.json",
    "global-revocation-operation.json",
    "global-revocation-operation-running.json",
}
EXAMPLE_DEFINITIONS = {
    "dashboard-response.json": "DashboardResponse",
    "principal-search-request.json": "PrincipalSearchRequest",
    "principal-search-result.json": "PrincipalSearchResult",
    "global-revocation-preview.json": "GlobalRevocationPreview",
    "global-revocation-request.json": "GlobalRevocationRequest",
    "global-revocation-operation.json": "GlobalRevocationOperation",
    "global-revocation-operation-running.json": "GlobalRevocationOperation",
}
EMAIL_VALUE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SKIP_PARTS = {".git", "target", "node_modules", "__pycache__", ".dart_tool", "build", ".vendor", "zed_modules"}
SKIP_SUFFIXES = {".pyc", ".class", ".o", ".a", ".so", ".dylib", ".dll", ".exe", ".jar"}
FORBIDDEN = re.compile(
    r"(?i)(BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|rawBiometric(?:Template|Image)|faceTemplate|fingerprintTemplate)"
)


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_revocation_redaction(value: dict[str, object]) -> None:
    assert value == {
        "rawEmailsPresent": False,
        "rawTokensPresent": False,
        "rawSessionIdentifiersPresent": False,
        "rawBiometricMaterialPresent": False,
    }


def validate_schema_value(
    value: object,
    schema: dict[str, object] | bool,
    root: dict[str, object],
    path: str = "$",
) -> None:
    if schema is False:
        raise AssertionError(f"prohibited value at {path}")
    if schema is True:
        return

    reference = schema.get("$ref")
    if reference is not None:
        assert isinstance(reference, str) and reference.startswith("#/$defs/"), f"unsupported ref at {path}: {reference}"
        definition = reference.removeprefix("#/$defs/")
        validate_schema_value(value, root["$defs"][definition], root, path)

    if "const" in schema:
        assert value == schema["const"], f"const mismatch at {path}: {value!r}"
    if "enum" in schema:
        assert value in schema["enum"], f"enum mismatch at {path}: {value!r}"

    expected_types = schema.get("type")
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    if expected_types is not None:
        type_matches = {
            "object": lambda candidate: isinstance(candidate, dict),
            "array": lambda candidate: isinstance(candidate, list),
            "string": lambda candidate: isinstance(candidate, str),
            "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
            "boolean": lambda candidate: isinstance(candidate, bool),
            "null": lambda candidate: candidate is None,
        }
        assert any(type_matches[item](value) for item in expected_types), f"type mismatch at {path}: {value!r}"

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        assert required <= set(value), f"missing fields at {path}: {sorted(required - set(value))}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(properties), f"additional fields at {path}: {sorted(set(value) - set(properties))}"
        for key, child in value.items():
            if key in properties:
                validate_schema_value(child, properties[key], root, f"{path}.{key}")

    if isinstance(value, list):
        if "minItems" in schema:
            assert len(value) >= schema["minItems"], f"too few items at {path}"
        if "maxItems" in schema:
            assert len(value) <= schema["maxItems"], f"too many items at {path}"
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            assert len(canonical) == len(set(canonical)), f"duplicate items at {path}"
        if "items" in schema:
            for index, child in enumerate(value):
                validate_schema_value(child, schema["items"], root, f"{path}[{index}]")
        if "contains" in schema:
            assert any(schema_matches(item, schema["contains"], root) for item in value), f"contains failed at {path}"

    if isinstance(value, str):
        if "minLength" in schema:
            assert len(value) >= schema["minLength"], f"string too short at {path}"
        if "maxLength" in schema:
            assert len(value) <= schema["maxLength"], f"string too long at {path}"
        if "pattern" in schema:
            assert re.search(schema["pattern"], value), f"pattern mismatch at {path}: {value!r}"
        if schema.get("format") == "date-time":
            timestamp(value)

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema:
            assert value >= schema["minimum"], f"minimum failed at {path}"
        if "maximum" in schema:
            assert value <= schema["maximum"], f"maximum failed at {path}"

    for constraint in schema.get("allOf", []):
        validate_schema_value(value, constraint, root, path)
    if "if" in schema and schema_matches(value, schema["if"], root):
        validate_schema_value(value, schema.get("then", {}), root, path)


def schema_matches(value: object, schema: dict[str, object] | bool, root: dict[str, object]) -> bool:
    try:
        validate_schema_value(value, schema, root)
    except AssertionError:
        return False
    return True


def validate_admin_contract() -> None:
    schema = json.loads(ADMIN_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    definitions = schema["$defs"]
    capabilities = definitions["CredentialCapabilityProjection"]
    dashboard = definitions["DashboardResponse"]

    assert REVOCATION_CONTRACTS <= set(schema["properties"]["contract"]["enum"])
    revocation_dispatch = {
        item["if"]["properties"]["contract"]["const"]: item["then"]["properties"]["payload"]["$ref"]
        for item in schema["allOf"]
    }
    assert revocation_dispatch == {
        name: f"#/$defs/{name}" for name in REVOCATION_CONTRACTS
    }
    assert set(definitions["RevocationScope"]["enum"]) == REVOCATION_SCOPES
    assert set(definitions["RevocationJobState"]["enum"]) == REVOCATION_JOB_STATES
    assert set(definitions["RevocationTargetState"]["enum"]) == REVOCATION_TARGET_STATES

    provider_identity = definitions["ProviderIdentityRef"]
    assert set(provider_identity["required"]) == {
        "providerId",
        "providerTenantId",
        "opaqueIdentityHandle",
    }
    assert "email" not in provider_identity["properties"]
    assert "token" not in provider_identity["properties"]

    search_request = definitions["PrincipalSearchRequest"]
    assert "emailSearchKeyHash" in search_request["properties"]
    assert "email" not in search_request["properties"]
    assert search_request["properties"]["purpose"]["const"] == "operator_email_search"
    assert definitions["IdempotencyKey"]["writeOnly"] is True

    search_candidate = definitions["PrincipalSearchCandidate"]
    assert "principalId" in search_candidate["required"]
    assert "principalId" in search_candidate["properties"]

    scopes = definitions["RevocationScopeSet"]
    mandatory_scopes = {item["contains"]["const"] for item in scopes["allOf"]}
    assert mandatory_scopes == {"interactive_sessions", "refresh_token_families"}

    preview = definitions["GlobalRevocationPreview"]
    assert preview["properties"]["ambiguityResolved"]["const"] is True
    assert preview["properties"]["requiresStepUp"]["const"] is True
    assert preview["properties"]["minimumAssurance"]["const"] == "aal2"
    assert preview["properties"]["phishingResistantStepUpRequired"]["const"] is True

    step_up = definitions["RevocationStepUp"]
    assert set(step_up["properties"]["assurance"]["enum"]) == {"aal2", "aal3"}
    assert step_up["properties"]["authMethods"]["contains"]["const"] == "webauthn"
    assert step_up["properties"]["phishingResistant"]["const"] is True
    assert {"verifiedAt", "freshUntil"} <= set(step_up["required"])

    request = definitions["GlobalRevocationRequest"]
    assert {
        "principalId",
        "previewId",
        "idempotencyKey",
        "selectedScopes",
        "principalSelectionConfirmed",
        "stepUp",
    } <= set(request["required"])
    assert request["properties"]["principalSelectionConfirmed"]["const"] is True

    operation = definitions["GlobalRevocationOperation"]
    assert {"principalId", "state", "fence", "targets", "audit"} <= set(operation["required"])
    fence = definitions["RevocationFence"]
    assert {"appliedAt", "notBefore", "previousAuthEpoch", "authEpoch", "effective"} == set(fence["required"])
    assert fence["properties"]["effective"]["const"] is True

    audit = definitions["RevocationAuditCorrelation"]
    for field in ("rawEmailsPresent", "rawTokensPresent", "rawBiometricMaterialPresent"):
        assert audit["properties"][field]["const"] is False

    capability_required = set(capabilities["required"])
    assert {
        "productionEnabled",
        "requiresOnlineIntrospection",
        "roleClaimsAuthoritative",
        "rawBiometricMaterialPresent",
    } <= capability_required

    scope = dashboard["properties"]["scope"]["properties"]
    assert scope["exactMembershipRequired"]["const"] is True
    assert scope["crossOrganizationFallbackAllowed"]["const"] is False

    redaction = dashboard["properties"]["redaction"]["properties"]
    for field in (
        "rawSessionIdentifiersPresent",
        "bearerTokensPresent",
        "rawIpAddressesPresent",
        "rawBiometricMaterialPresent",
    ):
        assert redaction[field]["const"] is False

    example = json.loads(ADMIN_EXAMPLE.read_text(encoding="utf-8"))
    assert example["schema"] == "ores.shared-auth-admin-dashboard/v1"
    assert example["scope"]["exactMembershipRequired"] is True
    assert example["scope"]["crossOrganizationFallbackAllowed"] is False
    assert all(value is False for value in example["redaction"].values())

    capabilities_by_method = {item["method"]: item for item in example["capabilities"]}
    ssh = capabilities_by_method["ssh"]
    assert ssh["productionEnabled"] is False
    assert ssh["requiresOnlineIntrospection"] is True
    assert ssh["maximumAssurance"] in {"aal0", "aal1"}
    assert ssh["roleClaimsAuthoritative"] is False

    openpgp = capabilities_by_method["openpgp"]
    assert openpgp["authority"] == "provenance_only"
    assert openpgp["tokenMintingAllowed"] is False
    assert openpgp["maximumAssurance"] == "aal0"

    biometric = capabilities_by_method["platform_biometric"]
    assert biometric["rawBiometricMaterialPresent"] is False
    assert biometric["retention"] == "none"

    example_names = {path.name for path in ADMIN_EXAMPLES.glob("*.json")}
    assert REVOCATION_EXAMPLE_NAMES <= example_names
    examples = {name: json.loads((ADMIN_EXAMPLES / name).read_text(encoding="utf-8")) for name in EXAMPLE_DEFINITIONS}
    for name, definition in EXAMPLE_DEFINITIONS.items():
        validate_schema_value(examples[name], definitions[definition], schema)
        if definition in REVOCATION_CONTRACTS:
            validate_schema_value({"contract": definition, "payload": examples[name]}, schema, schema)
    for name in REVOCATION_EXAMPLE_NAMES:
        source = (ADMIN_EXAMPLES / name).read_text(encoding="utf-8")
        assert EMAIL_VALUE.search(source) is None, f"raw email-like value in {name}"
        assert_revocation_redaction(examples[name]["redaction"])

    search_result = examples["principal-search-result.json"]
    assert search_result["state"] == "ambiguous"
    assert len(search_result["candidates"]) >= 2
    assert search_result["requiresExplicitPrincipalSelection"] is True
    assert len({candidate["principalId"] for candidate in search_result["candidates"]}) == len(search_result["candidates"])
    assert all(candidate["principalId"] for candidate in search_result["candidates"])
    assert all(
        {"providerTenantId", "opaqueIdentityHandle"} <= set(identity)
        for candidate in search_result["candidates"]
        for identity in candidate["identities"]
    )
    unsafe_search_request = deepcopy(examples["principal-search-request.json"])
    unsafe_search_request["email"] = "forbidden"
    assert not schema_matches(unsafe_search_request, definitions["PrincipalSearchRequest"], schema)
    unresolved_ambiguity = deepcopy(search_result)
    unresolved_ambiguity["candidates"] = unresolved_ambiguity["candidates"][:1]
    assert not schema_matches(unresolved_ambiguity, definitions["PrincipalSearchResult"], schema)

    preview_example = examples["global-revocation-preview.json"]
    request_example = examples["global-revocation-request.json"]
    operation_example = examples["global-revocation-operation.json"]
    running_operation_example = examples["global-revocation-operation-running.json"]
    assert preview_example["principalId"] == request_example["principalId"] == operation_example["principalId"]
    assert preview_example["previewId"] == request_example["previewId"] == operation_example["previewId"]
    assert preview_example["selectedScopes"] == request_example["selectedScopes"] == operation_example["selectedScopes"]
    assert {"interactive_sessions", "refresh_token_families"} <= set(request_example["selectedScopes"])
    assert timestamp(preview_example["generatedAt"]) < timestamp(preview_example["expiresAt"])
    assert timestamp(request_example["stepUp"]["verifiedAt"]) <= timestamp(request_example["requestedAt"])
    assert timestamp(request_example["requestedAt"]) <= timestamp(request_example["stepUp"]["freshUntil"])
    assert request_example["stepUp"]["assurance"] in {"aal2", "aal3"}
    assert request_example["stepUp"]["phishingResistant"] is True
    assert "webauthn" in request_example["stepUp"]["authMethods"]
    assert request_example["principalSelectionConfirmed"] is True
    weak_step_up = deepcopy(request_example)
    weak_step_up["stepUp"]["assurance"] = "aal1"
    assert not schema_matches(weak_step_up, definitions["GlobalRevocationRequest"], schema)

    assert operation_example["state"] == "partial"
    assert operation_example["fence"]["effective"] is True
    assert operation_example["fence"]["authEpoch"] > operation_example["fence"]["previousAuthEpoch"]
    assert timestamp(operation_example["fence"]["appliedAt"]) <= timestamp(operation_example["createdAt"])
    target_states = {target["state"] for target in operation_example["targets"]}
    assert "succeeded" in target_states
    assert target_states & {"failed", "unsupported"}
    assert all(target["attemptCount"] >= 0 for target in operation_example["targets"])
    assert all(not target["retryable"] for target in operation_example["targets"] if target["state"] in {"succeeded", "failed", "skipped", "unsupported"})
    assert all(
        "nextAttemptAt" not in target and "retryAfterSeconds" not in target
        for target in operation_example["targets"]
        if target["state"] in {"succeeded", "failed", "skipped", "unsupported"}
    )
    assert operation_example["audit"]["rawEmailsPresent"] is False
    assert operation_example["audit"]["rawTokensPresent"] is False
    assert operation_example["audit"]["rawBiometricMaterialPresent"] is False
    assert "idempotencyKey" not in operation_example
    retrying_targets = [
        target for target in running_operation_example["targets"]
        if target["state"] == "retry_scheduled"
    ]
    assert len(retrying_targets) == 1
    assert retrying_targets[0]["retryable"] is True
    assert retrying_targets[0]["attemptCount"] > 0
    assert timestamp(retrying_targets[0]["lastAttemptAt"]) < timestamp(retrying_targets[0]["nextAttemptAt"])
    assert retrying_targets[0]["retryAfterSeconds"] > 0
    retry_without_next_attempt = deepcopy(running_operation_example)
    next(
        target for target in retry_without_next_attempt["targets"]
        if target["state"] == "retry_scheduled"
    ).pop("nextAttemptAt")
    assert not schema_matches(retry_without_next_attempt, definitions["GlobalRevocationOperation"], schema)
    retry_without_delay = deepcopy(running_operation_example)
    next(
        target for target in retry_without_delay["targets"]
        if target["state"] == "retry_scheduled"
    ).pop("retryAfterSeconds")
    assert not schema_matches(retry_without_delay, definitions["GlobalRevocationOperation"], schema)
    retry_with_zero_delay = deepcopy(running_operation_example)
    next(
        target for target in retry_with_zero_delay["targets"]
        if target["state"] == "retry_scheduled"
    )["retryAfterSeconds"] = 0
    assert not schema_matches(retry_with_zero_delay, definitions["GlobalRevocationOperation"], schema)
    terminal_with_next_attempt = deepcopy(operation_example)
    next(
        target for target in terminal_with_next_attempt["targets"]
        if target["state"] == "failed"
    )["nextAttemptAt"] = "2026-08-11T15:04:00Z"
    assert not schema_matches(terminal_with_next_attempt, definitions["GlobalRevocationOperation"], schema)
    terminal_with_retry_delay = deepcopy(operation_example)
    next(
        target for target in terminal_with_retry_delay["targets"]
        if target["state"] == "failed"
    )["retryAfterSeconds"] = 30
    assert not schema_matches(terminal_with_retry_delay, definitions["GlobalRevocationOperation"], schema)
    falsely_complete = deepcopy(operation_example)
    for target in falsely_complete["targets"]:
        target["state"] = "succeeded"
        target["retryable"] = False
    assert not schema_matches(falsely_complete, definitions["GlobalRevocationOperation"], schema)
    false_success = deepcopy(operation_example)
    false_success["state"] = "succeeded"
    assert not schema_matches(false_success, definitions["GlobalRevocationOperation"], schema)
    leaked_idempotency_key = deepcopy(operation_example)
    leaked_idempotency_key["idempotencyKey"] = "forbidden_response_value"
    assert not schema_matches(leaked_idempotency_key, definitions["GlobalRevocationOperation"], schema)

    for language, path in LANGUAGE_BINDINGS.items():
        source = path.read_text(encoding="utf-8")
        missing_types = REVOCATION_TYPES - {name for name in REVOCATION_TYPES if name in source}
        assert not missing_types, f"{language} revocation type drift: {sorted(missing_types)}"
        missing_scopes = REVOCATION_SCOPES - {value for value in REVOCATION_SCOPES if value in source}
        assert not missing_scopes, f"{language} revocation scope drift: {sorted(missing_scopes)}"
        missing_states = (REVOCATION_JOB_STATES | REVOCATION_TARGET_STATES) - {
            value for value in REVOCATION_JOB_STATES | REVOCATION_TARGET_STATES if value in source
        }
        assert not missing_states, f"{language} revocation state drift: {sorted(missing_states)}"
        normalized_source = re.sub(r"[^a-z0-9]", "", source.lower())
        missing_fields = {
            field for field in REVOCATION_FIELDS
            if re.sub(r"[^a-z0-9]", "", field.lower()) not in normalized_source
        }
        assert not missing_fields, f"{language} revocation field drift: {sorted(missing_fields)}"


def main() -> int:
    document = json.loads(PLATFORM_SCHEMA.read_text(encoding="utf-8"))
    assert document["$schema"].endswith("2020-12/schema")
    methods = set(document["$defs"]["AuthMethod"]["enum"])
    assert methods == AUTH_METHODS, (methods, AUTH_METHODS)
    proof = document["$defs"]["PlatformBiometricProof"]["properties"]
    assert proof["rawBiometricMaterialPresent"]["const"] is False

    validate_admin_contract()

    present = {path.name for path in (ROOT / "languages").iterdir() if path.is_dir()}
    assert LANGUAGES <= present, LANGUAGES - present
    for path in ROOT.rglob("*"):
        if path.resolve() == pathlib.Path(__file__).resolve():
            continue
        if any(part in SKIP_PARTS for part in path.parts) or path.suffix in SKIP_SUFFIXES:
            continue
        if path.is_file() and path.stat().st_size < 2_000_000:
            text = path.read_text(encoding="utf-8", errors="ignore")
            match = FORBIDDEN.search(text)
            if match:
                raise AssertionError(
                    f"forbidden secret/biometric material marker in {path}: {match.group(0)}"
                )
    print(
        "contracts valid: "
        f"methods={len(methods)} languages={len(present)} revocation_scopes={len(REVOCATION_SCOPES)} "
        "admin_contract=shared-auth-admin/v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
