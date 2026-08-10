#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLATFORM_SCHEMA = ROOT / "contracts/ores-platform/v1/schema.json"
ADMIN_SCHEMA = ROOT / "contracts/shared-auth-admin/v1/schema.json"
ADMIN_EXAMPLE = ROOT / "contracts/shared-auth-admin/v1/examples/dashboard-response.json"
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
SKIP_PARTS = {".git", "target", "node_modules", "__pycache__", ".dart_tool", "build", ".vendor", "zed_modules"}
SKIP_SUFFIXES = {".pyc", ".class", ".o", ".a", ".so", ".dylib", ".dll", ".exe", ".jar"}
FORBIDDEN = re.compile(
    r"(?i)(BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|rawBiometric(?:Template|Image)|faceTemplate|fingerprintTemplate)"
)


def validate_admin_contract() -> None:
    schema = json.loads(ADMIN_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    definitions = schema["$defs"]
    capabilities = definitions["CredentialCapabilityProjection"]
    dashboard = definitions["DashboardResponse"]

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
        f"methods={len(methods)} languages={len(present)} admin_contract=shared-auth-admin/v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
