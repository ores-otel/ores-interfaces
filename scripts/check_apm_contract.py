#!/usr/bin/env python3
"""Semantic checks for contracts/ores-apm/v1.

Structural parity belongs to TJSV. This script checks relationships that are
awkward or misleading to express as independent peer-schema structure.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "contracts" / "ores-apm" / "v1" / "example.snapshot.json"
OTEL_HTTP_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
PROFILE_KINDS = {"cpu", "wall", "allocation", "heap", "lock", "blocking"}
CAPABILITY_STATES = {"unsupported", "model-only", "external-adapter", "native"}


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def u64(value: object, label: str) -> int:
    require(isinstance(value, str), f"{label} must be a decimal string")
    require(value == "0" or (value and value[0] != "0" and value.isdigit()), f"{label} must be canonical non-negative decimal")
    return int(value)


def check_histogram(histogram: dict, *, latency: bool = False) -> None:
    count = u64(histogram["count"], "histogram.count")
    buckets = histogram["buckets"]
    bounds = [bucket["upper_bound"] for bucket in buckets]
    require(bounds == sorted(bounds) and len(bounds) == len(set(bounds)), "histogram bounds must be strictly increasing")
    require(sum(u64(bucket["count"], "histogram.bucket.count") for bucket in buckets) <= count, "finite histogram bucket counts cannot exceed total count")
    if "min" in histogram and "max" in histogram:
        require(histogram["min"] <= histogram["max"], "histogram min must not exceed max")
    for exemplar in histogram.get("exemplars", []):
        require(len(exemplar["trace_id"]) == 32, "exemplar trace id must be 16 bytes")
        require(len(exemplar["span_id"]) == 16, "exemplar span id must be 8 bytes")
        u64(exemplar["timestamp_unix_nano"], "exemplar.timestamp_unix_nano")
    if latency:
        require(bounds == OTEL_HTTP_BUCKETS, "service latency histogram must use the OTel HTTP advisory boundaries in v1")
        require(histogram["sum"] >= 0, "latency sum must be non-negative")
        if "min" in histogram:
            require(histogram["min"] >= 0, "latency min must be non-negative")


def check_snapshot(doc: dict) -> None:
    require(doc.get("schema_version") == 1, "schema_version must be 1")
    u64(doc["observed_at_unix_nano"], "observed_at_unix_nano")

    process = doc["process"]
    require(0 <= process["cpu_utilization"] <= 1, "process CPU utilization must be in [0,1]")
    if "memory_utilization" in process:
        require(0 <= process["memory_utilization"] <= 1, "process memory utilization must be in [0,1]")
    for key, value in process.items():
        if key.endswith("_bytes") or key.endswith("_count") or key.endswith("_operations"):
            u64(value, f"process.{key}")

    targets: set[str] = set()
    for filesystem in doc["filesystems"]:
        target = filesystem["target"]
        require("/" not in target and "\\" not in target, "filesystem target must be a logical label, not a path")
        require(target not in targets, "filesystem target labels must be unique")
        targets.add(target)
        total = u64(filesystem["total_bytes"], "filesystem.total_bytes")
        used = u64(filesystem["used_bytes"], "filesystem.used_bytes")
        free = u64(filesystem["free_bytes"], "filesystem.free_bytes")
        available = u64(filesystem["available_bytes"], "filesystem.available_bytes")
        if "files_total" in filesystem:
            u64(filesystem["files_total"], "filesystem.files_total")
        if "files_free" in filesystem:
            u64(filesystem["files_free"], "filesystem.files_free")
        require(used <= total, "filesystem used bytes cannot exceed total")
        require(free <= total, "filesystem free bytes cannot exceed total")
        require(available <= free, "filesystem available bytes cannot exceed free bytes")
        require(0 <= filesystem["utilization"] <= 1, "filesystem utilization must be in [0,1]")

    runtime = doc.get("runtime")
    if runtime:
        for metric in runtime["metrics"]:
            prefix = f"{metric['runtime_namespace']}."
            require(metric["name"].startswith(prefix), "runtime metric names must be namespaced by runtime_namespace")

    service = doc["service"]
    request_count = u64(service["request_count"], "service.request_count")
    error_count = u64(service["error_count"], "service.error_count")
    u64(service["active_requests"], "service.active_requests")
    require(error_count <= request_count, "service errors cannot exceed requests")
    if "saturation_ratio" in service:
        require(0 <= service["saturation_ratio"] <= 1, "service saturation must be in [0,1]")
    check_histogram(service["latency_seconds"], latency=True)

    capabilities = doc["capabilities"]
    for name, status in capabilities.items():
        if name == "profiling":
            continue
        require(status in CAPABILITY_STATES, f"invalid capability state for {name}")
    profile_kinds: set[str] = set()
    for capability in capabilities["profiling"]:
        kind = capability["kind"]
        require(kind in PROFILE_KINDS, f"invalid profile kind {kind}")
        require(kind not in profile_kinds, f"duplicate profile capability {kind}")
        profile_kinds.add(kind)
        require(capability["status"] in CAPABILITY_STATES, f"invalid profile capability state {kind}")

    for profile in doc.get("profiles", []):
        start = u64(profile["start_unix_nano"], "profile.start_unix_nano")
        end = u64(profile["end_unix_nano"], "profile.end_unix_nano")
        u64(profile["sample_count"], "profile.sample_count")
        u64(profile["dropped_sample_count"], "profile.dropped_sample_count")
        require(end >= start, "profile end must not precede start")

    for metric in doc.get("metrics", []):
        u64(metric["timestamp_unix_nano"], f"metric {metric['name']} timestamp")
        has_value = "value" in metric
        has_histogram = "histogram" in metric
        if metric["kind"] == "histogram":
            require(has_histogram and not has_value, f"histogram metric {metric['name']} must carry only histogram")
            check_histogram(metric["histogram"], latency=metric["name"] in {"http.server.request.duration", "http.client.request.duration"})
        else:
            require(has_value and not has_histogram, f"scalar metric {metric['name']} must carry only value")
        keys = [attribute["key"] for attribute in metric.get("attributes", [])]
        require(len(keys) == len(set(keys)), f"metric {metric['name']} has duplicate attributes")

    serialized = json.dumps(doc, sort_keys=True).lower()
    private_key_marker = "-----" + "begin " + "private key" + "-----"
    forbidden = ["authorization: bearer", "service_role", "database_url", "postgres://", "postgresql://", "env/dec/", private_key_marker]
    for token in forbidden:
        require(token not in serialized, f"fixture contains forbidden secret-bearing token {token!r}")


def expect_rejected(name: str, mutator) -> None:
    doc = json.loads(FIXTURE.read_text())
    mutator(doc)
    try:
        check_snapshot(doc)
    except ContractError:
        return
    raise AssertionError(f"negative control unexpectedly admitted: {name}")


def main() -> None:
    doc = json.loads(FIXTURE.read_text())
    check_snapshot(doc)
    expect_rejected("raw filesystem path", lambda d: d["filesystems"][0].__setitem__("target", "/var/lib/app"))
    expect_rejected("errors exceed requests", lambda d: d["service"].__setitem__("error_count", str(int(d["service"]["request_count"]) + 1)))
    expect_rejected("bad latency buckets", lambda d: d["service"]["latency_seconds"]["buckets"].reverse())
    expect_rejected("runtime namespace drift", lambda d: d["runtime"]["metrics"][0].__setitem__("name", "jvm.memory.used"))
    expect_rejected("scalar metric carries histogram", lambda d: d["metrics"][0].__setitem__("histogram", copy.deepcopy(d["service"]["latency_seconds"])))
    expect_rejected("duplicate profiling capability", lambda d: d["capabilities"]["profiling"].append(copy.deepcopy(d["capabilities"]["profiling"][0])))
    expect_rejected("profile time inversion", lambda d: d["profiles"][0].__setitem__("end_unix_nano", "1"))
    print("APM v1 semantic checks passed (1 positive fixture, 7 negative controls)")


if __name__ == "__main__":
    main()
