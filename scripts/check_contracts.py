#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from importlib.metadata import PackageNotFoundError, version
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_LOCK = ROOT / "scripts/requirements-contracts.lock"

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import best_match
except ModuleNotFoundError as error:
    raise SystemExit(
        "missing pinned contract validator dependency; install it with "
        "`python3 -m pip install --require-hashes "
        "--requirement scripts/requirements-contracts.lock`"
    ) from error

PLATFORM_SCHEMA = ROOT / "contracts/ores-platform/v1/schema.json"
ADMIN_ROOT = ROOT / "contracts/shared-auth-admin/v1"
ADMIN_SCHEMA = ADMIN_ROOT / "schema.json"
ADMIN_EXAMPLE = ADMIN_ROOT / "examples/dashboard-response.json"
ADMIN_VALID_FIXTURES = ADMIN_ROOT / "fixtures/valid"
ADMIN_INVALID_FIXTURES = ADMIN_ROOT / "fixtures/invalid"
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
ADMIN_CONTRACTS = (
    "DashboardQuery",
    "DashboardResponse",
    "OrganizationOption",
    "ProjectOption",
    "UserProjection",
    "SessionProjection",
    "RoleBindingProjection",
    "CredentialCapabilityProjection",
)
PINNED_VALIDATOR_PACKAGES = {
    "jsonschema": "4.25.1",
    "rfc3339-validator": "0.1.4",
}
SKIP_PARTS = {
    ".git",
    "target",
    "node_modules",
    "__pycache__",
    ".dart_tool",
    "build",
    ".vendor",
    "zed_modules",
}
SKIP_SUFFIXES = {".pyc", ".class", ".o", ".a", ".so", ".dylib", ".dll", ".exe", ".jar"}
FORBIDDEN = re.compile(
    r"(?i)(BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|rawBiometric(?:Template|Image)|faceTemplate|fingerprintTemplate)"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"cannot load JSON fixture {path.relative_to(ROOT)}: {error}") from error


def format_validation_error(error: Any) -> str:
    path = "$"
    for component in error.absolute_path:
        if isinstance(component, int):
            path += f"[{component}]"
        else:
            path += f".{component}"
    return f"{path}: {error.message}"


def require_valid(validator: Draft202012Validator, document: Any, path: pathlib.Path) -> None:
    errors = list(validator.iter_errors(document))
    if errors:
        error = best_match(errors)
        raise AssertionError(
            f"expected valid admin fixture {path.relative_to(ROOT)}; "
            f"{format_validation_error(error)}"
        )


def require_invalid(validator: Draft202012Validator, document: Any, path: pathlib.Path) -> None:
    if validator.is_valid(document):
        raise AssertionError(
            f"expected invalid admin fixture {path.relative_to(ROOT)}, but it validated"
        )


def require_restrictive_objects(node: Any, path: str = "$") -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            require(
                node.get("additionalProperties") is False,
                f"object schema at {path} must set additionalProperties to false",
            )
        for key, value in node.items():
            require_restrictive_objects(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            require_restrictive_objects(value, f"{path}[{index}]")


def validate_discriminator(schema: dict[str, Any]) -> None:
    expected = {contract: f"#/$defs/{contract}" for contract in ADMIN_CONTRACTS}
    actual: dict[str, str] = {}

    for index, branch in enumerate(schema.get("oneOf", [])):
        properties = branch.get("properties", {})
        contract = properties.get("contract", {}).get("const")
        payload_ref = properties.get("payload", {}).get("$ref")
        require(
            isinstance(contract, str) and isinstance(payload_ref, str),
            f"admin oneOf branch {index} must bind a contract const to a payload $ref",
        )
        require(contract not in actual, f"duplicate admin discriminator branch: {contract}")
        actual[contract] = payload_ref

    require(
        actual == expected,
        f"admin discriminator mapping drifted: actual={actual!r} expected={expected!r}",
    )


def validate_validator_dependencies() -> None:
    require(VALIDATOR_LOCK.is_file(), "pinned contract validator lock is missing")
    for package, expected in PINNED_VALIDATOR_PACKAGES.items():
        try:
            installed = version(package)
        except PackageNotFoundError as error:
            raise AssertionError(f"required validator package is missing: {package}") from error
        require(
            installed == expected,
            f"validator dependency drift: {package}={installed}, expected {expected}",
        )


def validate_admin_contract() -> tuple[int, int, int]:
    validate_validator_dependencies()
    schema = load_json(ADMIN_SCHEMA)
    require(
        schema["$schema"] == "https://json-schema.org/draft/2020-12/schema",
        "admin contract must declare JSON Schema Draft 2020-12",
    )
    Draft202012Validator.check_schema(schema)
    require_restrictive_objects(schema)
    validate_discriminator(schema)

    format_checker = FormatChecker()
    require(
        format_checker.conforms("2026-08-10T21:30:00Z", "date-time"),
        "date-time format checker rejected a valid RFC 3339 timestamp",
    )
    require(
        not format_checker.conforms("not-a-date-time", "date-time"),
        "date-time format validation is unavailable; install the pinned lock",
    )
    validator = Draft202012Validator(schema, format_checker=format_checker)

    example = load_json(ADMIN_EXAMPLE)
    require_valid(validator, example, ADMIN_EXAMPLE)

    valid_paths = sorted(ADMIN_VALID_FIXTURES.glob("*.json"))
    require(valid_paths, "admin positive fixture set is empty")
    valid_documents = [(ADMIN_EXAMPLE, example)]
    for path in valid_paths:
        document = load_json(path)
        require_valid(validator, document, path)
        valid_documents.append((path, document))

    coverage = Counter(document.get("contract") for _, document in valid_documents)
    require(
        coverage == Counter(ADMIN_CONTRACTS),
        f"positive fixtures must cover every admin discriminator exactly once: {coverage!r}",
    )

    legacy_validator = Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "contract": {"enum": list(ADMIN_CONTRACTS)},
                "payload": {"type": "object"},
            },
            "required": ["contract", "payload"],
        }
    )

    cross_shape_count = 0
    for source_path, source in valid_documents:
        for target_contract in ADMIN_CONTRACTS:
            if target_contract == source["contract"]:
                continue
            candidate = {
                "contract": target_contract,
                "payload": source["payload"],
            }
            require(
                legacy_validator.is_valid(candidate),
                "generated cross-shape case must exercise the former loose-payload gap",
            )
            require(
                not validator.is_valid(candidate),
                f"{source_path.relative_to(ROOT)} payload unexpectedly validates as "
                f"{target_contract}",
            )
            cross_shape_count += 1

    invalid_paths = sorted(ADMIN_INVALID_FIXTURES.glob("*.json"))
    require(invalid_paths, "admin negative fixture set is empty")
    for path in invalid_paths:
        document = load_json(path)
        require(
            legacy_validator.is_valid(document),
            f"negative fixture does not exercise the former loose-payload gap: {path.relative_to(ROOT)}",
        )
        require_invalid(validator, document, path)

    definitions = schema["$defs"]
    capabilities = definitions["CredentialCapabilityProjection"]
    dashboard = definitions["DashboardResponse"]

    capability_required = set(capabilities["required"])
    require(
        {
            "productionEnabled",
            "requiresOnlineIntrospection",
            "roleClaimsAuthoritative",
            "rawBiometricMaterialPresent",
        }
        <= capability_required,
        "capability truth fields are not all required",
    )

    scope = dashboard["properties"]["scope"]["properties"]
    require(scope["exactMembershipRequired"]["const"] is True, "exact membership must be required")
    require(
        scope["crossOrganizationFallbackAllowed"]["const"] is False,
        "cross-organization fallback must be prohibited",
    )

    redaction = dashboard["properties"]["redaction"]["properties"]
    for field in (
        "rawSessionIdentifiersPresent",
        "bearerTokensPresent",
        "rawIpAddressesPresent",
        "rawBiometricMaterialPresent",
    ):
        require(redaction[field]["const"] is False, f"redaction invariant drifted: {field}")

    payload = example["payload"]
    require(payload["schema"] == "ores.shared-auth-admin-dashboard/v1", "example schema drifted")
    require(payload["scope"]["exactMembershipRequired"] is True, "example weakens membership")
    require(
        payload["scope"]["crossOrganizationFallbackAllowed"] is False,
        "example enables cross-organization fallback",
    )
    require(all(value is False for value in payload["redaction"].values()), "example weakens redaction")

    capabilities_by_method = {item["method"]: item for item in payload["capabilities"]}
    ssh = capabilities_by_method["ssh"]
    require(ssh["productionEnabled"] is False, "SSH preview must not be production-enabled")
    require(ssh["requiresOnlineIntrospection"] is True, "SSH requires online introspection")
    require(ssh["maximumAssurance"] in {"aal0", "aal1"}, "SSH assurance exceeds AAL1")
    require(ssh["roleClaimsAuthoritative"] is False, "SSH role claims must not be authoritative")

    openpgp = capabilities_by_method["openpgp"]
    require(openpgp["authority"] == "provenance_only", "OpenPGP authority drifted")
    require(openpgp["tokenMintingAllowed"] is False, "OpenPGP must not mint tokens")
    require(openpgp["maximumAssurance"] == "aal0", "OpenPGP assurance must be AAL0")

    biometric = capabilities_by_method["platform_biometric"]
    require(biometric["rawBiometricMaterialPresent"] is False, "raw biometric material is prohibited")
    require(biometric["retention"] == "none", "platform biometric material must not be retained")

    return len(valid_documents), len(invalid_paths), cross_shape_count


def main() -> int:
    document = load_json(PLATFORM_SCHEMA)
    require(document["$schema"].endswith("2020-12/schema"), "platform schema draft drifted")
    methods = set(document["$defs"]["AuthMethod"]["enum"])
    require(methods == AUTH_METHODS, f"authentication method drift: {methods!r} != {AUTH_METHODS!r}")
    proof = document["$defs"]["PlatformBiometricProof"]["properties"]
    require(proof["rawBiometricMaterialPresent"]["const"] is False, "platform biometric proof weakened")

    valid_count, invalid_count, cross_shape_count = validate_admin_contract()

    present = {path.name for path in (ROOT / "languages").iterdir() if path.is_dir()}
    require(LANGUAGES <= present, f"missing language directories: {LANGUAGES - present!r}")
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
        f"methods={len(methods)} languages={len(present)} "
        f"admin_contract=shared-auth-admin/v1 valid_fixtures={valid_count} "
        f"legacy_loose_payloads_rejected={invalid_count} "
        f"cross_shapes_rejected={cross_shape_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
