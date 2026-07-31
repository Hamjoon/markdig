#!/usr/bin/env python3
"""Build cases.json and validate every frozen screening invariant.

Usage: python3 manifest.py <exp-dir>

The manifest is written only after all queue, result, record, path, build,
test, uniqueness, and smoke-case checks pass.
"""

import json
import sys
from pathlib import Path

PROTOCOL_COMMIT = "4c2a0fdab1d8ec95d6f7270b4bf49c8002aac92f"
SCREENING_ARTIFACT_COMMIT = "771692a0b53d411661a3a8729ce630c9635214a8"
CATEGORIES = ("S", "P", "N")
SMOKE_SHAS = {
    "9dffce52b61068c4451399068f72cdad34f79bdb",
    "50061841a45e142192362131c9ed2ea6043f302e",
    "25506f20d96f214f951ac2d881550d8b883bf9f0",
}


def load_json(path):
    with path.open() as f:
        return json.load(f)


def find_run(record, kind, label, problems):
    matches = [run for run in record["runs"]
               if run["kind"] == kind and run["label"] == label]
    if len(matches) != 1:
        problems.append(
            f"{record['queue_id']}: expected one {kind} run named {label}")
        return None
    return matches[0]


def green_test(record, label, problems, require_nonempty=True):
    run = find_run(record, "test", label, problems)
    if run is None:
        return False
    counts = run.get("counts", {})
    ok = counts.get("failed") == 0
    if require_nonempty:
        ok = ok and counts.get("total", 0) > 0
    return ok


def red_test(record, label, problems):
    run = find_run(record, "test", label, problems)
    if run is None:
        return False
    counts = run.get("counts", {})
    return counts.get("failed", 0) > 0 and counts.get("total", 0) > 0


def build_ok(record, label, problems):
    run = find_run(record, "build", label, problems)
    return run is not None and run.get("rc") == 0


def validate_accepted_record(record, entry, category, problems):
    qid = entry["queue_id"]
    exact_fields = {
        "queue_id": qid,
        "category": category,
        "upstream_sha": entry["sha"],
        "base_sha": entry["parent"],
        "prod_src_files": entry["prod_src_files"],
        "test_src_files": entry["test_src_files"],
        "spec_md_files": entry["spec_md_files"],
        "generated_files_in_commit": entry["generated_files"],
        "status": "accepted",
        "reason": None,
    }
    for field, expected in exact_fields.items():
        if record.get(field) != expected:
            problems.append(f"{qid}: record field {field} does not match queue")

    if record.get("upstream_sha") in SMOKE_SHAS:
        problems.append(f"{qid}: smoke SHA accepted")
    if record.get("tfm") not in {"net9.0", "net10.0"}:
        problems.append(f"{qid}: unexpected TFM {record.get('tfm')}")
    if not record.get("dotnet_sdk"):
        problems.append(f"{qid}: missing resolved .NET SDK")

    for step in record.get("construction", []):
        if any(path.endswith(".generated.cs") for path in step.get("paths", [])):
            problems.append(f"{qid}: generated file entered an apply set")
        if step.get("rc") != 0:
            problems.append(f"{qid}: construction step {step.get('step')} failed")

    if not build_ok(record, "base", problems):
        problems.append(f"{qid}: base build is not green")
    if not green_test(record, "base-full-suite", problems):
        problems.append(f"{qid}: base full suite is not green and non-empty")

    if category == "S":
        ok = (green_test(record, "base-target", problems)
              and build_ok(record, "stale", problems)
              and red_test(record, "stale-target", problems))
    elif category == "P":
        ok = (build_ok(record, "oracle", problems)
              and red_test(record, "oracle-target", problems)
              and build_ok(record, "full", problems)
              and green_test(record, "full-target", problems)
              and green_test(record, "full-suite", problems))
    else:
        ok = (record.get("target_filter") is None
              and build_ok(record, "changed", problems)
              and green_test(record, "changed-full-suite", problems))
    if not ok:
        problems.append(f"{qid}: executable acceptance condition is not satisfied")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: manifest.py <exp-dir>")

    exp = Path(sys.argv[1])
    queue_doc = load_json(exp / "screening_queues.json")
    metadata = load_json(exp / "metadata" / "experiment.json")
    screening = metadata["selection"]["screening"]
    manifest = {
        "schema_version": 1,
        "experiment": "markdig-week5-historical-test-maintenance",
        "protocol_commit": PROTOCOL_COMMIT,
        "screening_artifact_commit": SCREENING_ARTIFACT_COMMIT,
        "cases": [],
    }
    problems = []

    for category in CATEGORIES:
        queue = queue_doc["queues"][category]
        result_doc = screening[category]
        rows = result_doc["results"]
        if result_doc.get("category") != category:
            problems.append(f"{category}: result document category mismatch")
        if len(rows) != len(queue):
            problems.append(f"{category}: queue/result length mismatch")
            continue

        accepted_count = 0
        for entry, row in zip(queue, rows):
            qid = entry["queue_id"]
            if row.get("queue_id") != qid or row.get("sha") != entry["sha"]:
                problems.append(f"{qid}: result row does not match queue position")
            if accepted_count >= 10:
                if (row.get("status"), row.get("reason")) != (
                        "not-screened", "quota-reached-before-position"):
                    problems.append(f"{qid}: expected not-screened after quota")
                if (exp / "screening" / qid).exists():
                    problems.append(f"{qid}: not-screened case has an artifact directory")
                continue

            if row.get("status") == "not-screened":
                problems.append(f"{qid}: not-screened before quota")
                continue
            record_path = exp / "screening" / qid / "record.json"
            if not record_path.exists():
                problems.append(f"{qid}: missing screening record")
                continue
            record = load_json(record_path)
            if (row.get("status"), row.get("reason")) != (
                    record.get("status"), record.get("reason")):
                problems.append(f"{qid}: result status/reason differs from record")
            if row.get("status") != "accepted":
                continue

            accepted_count += 1
            validate_accepted_record(record, entry, category, problems)
            archive_case_id = (
                qid.lower().replace("-", "")
                + "-"
                + record["upstream_sha"][:8]
            )
            manifest["cases"].append({
                "case_id": qid,
                "archive_case_id": archive_case_id,
                "category": category,
                "upstream_sha": record["upstream_sha"],
                "base_sha": record["base_sha"],
                "subject": record["subject"],
                "date": record["date"],
                "tfm": record["tfm"],
                "dotnet_sdk": record["dotnet_sdk"],
                "target_filter": record["target_filter"],
                "prod_src_files": record["prod_src_files"],
                "test_src_files": record["test_src_files"],
                "spec_md_files": record["spec_md_files"],
            })

        if accepted_count != result_doc.get("accepted"):
            problems.append(f"{category}: accepted count mismatch")

    case_ids = [case["case_id"] for case in manifest["cases"]]
    shas = [case["upstream_sha"] for case in manifest["cases"]]
    if len(case_ids) != len(set(case_ids)):
        problems.append("accepted case IDs are not unique")
    if len(shas) != len(set(shas)):
        problems.append("accepted SHAs are not unique across categories")

    manifest["counts"] = {
        category: sum(case["category"] == category for case in manifest["cases"])
        for category in CATEGORIES
    }
    manifest["case_count"] = len(manifest["cases"])

    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print(" -", problem)
        raise SystemExit(1)

    with (exp / "cases.json").open("w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print("counts:", manifest["counts"])
    print("case_count:", manifest["case_count"])
    print("manifest OK")


if __name__ == "__main__":
    main()
