#!/usr/bin/env python3
"""Revalidate every accepted fixture from a fresh worktree.

Usage: python3 verify.py <repo-root> <exp-dir>

The verifier reconstructs each accepted case through the frozen screener,
requires the same accepted verdict and test counts, and records fresh logs.
It refuses to mix a new run with an existing verification directory.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "screen", os.path.join(os.path.dirname(__file__), "screen.py"))
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def load_json(path):
    with path.open() as f:
        return json.load(f)


def update_metadata(exp, key, value):
    path = exp / "metadata" / "experiment.json"
    metadata = load_json(path)
    metadata[key] = value
    with path.open("w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")


def counts_of(record):
    return {run["label"]: run["counts"] for run in record["runs"]
            if run["kind"] == "test"}


def identity_of(record):
    return {
        key: record.get(key) for key in (
            "queue_id", "category", "upstream_sha", "base_sha", "tfm",
            "dotnet_sdk", "target_filter", "prod_src_files",
            "test_src_files", "spec_md_files")
    }


def normalize_logs(case_dir):
    """Remove runner-only trailing padding while preserving log evidence."""
    for path in (case_dir / "logs").glob("*.txt"):
        lines = path.read_text().splitlines()
        path.write_text("\n".join(line.rstrip() for line in lines) + "\n")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify.py <repo-root> <exp-dir>")

    repo = Path(sys.argv[1]).resolve()
    exp = Path(sys.argv[2]).resolve()
    verification_dir = exp / "verification"
    if verification_dir.exists():
        raise SystemExit(
            f"refusing to reuse existing verification directory: {verification_dir}")

    manifest = load_json(exp / "cases.json")
    queues = load_json(exp / "screening_queues.json")
    by_qid = {
        entry["queue_id"]: entry
        for category in "SPN" for entry in queues["queues"][category]
    }
    results = []
    ok_all = True

    for case in manifest["cases"]:
        qid = case["case_id"]
        entry = by_qid[qid]
        original = load_json(exp / "screening" / qid / "record.json")
        verifier = screen.Screener(str(repo), str(exp), entry, case["category"])
        verifier.case_dir = str(verification_dir / qid)
        verifier.log_dir = str(verification_dir / qid / "logs")
        verifier.wt = str(repo / ".worktrees" / f"verify-{qid}")
        verifier.record["attempt"] = "fixture-freeze"
        try:
            verifier.screen()
        except screen.Reject as error:
            verifier.record["status"] = "rejected"
            verifier.record["reason"] = str(error)
        except screen.Pipeline as error:
            verifier.record["status"] = "pipeline_error"
            verifier.record["reason"] = str(error)

        case_dir = verification_dir / qid
        normalize_logs(case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        with (case_dir / "record.json").open("w") as f:
            json.dump(verifier.record, f, indent=2)
            f.write("\n")

        counts_match = counts_of(verifier.record) == counts_of(original)
        identity_matches = identity_of(verifier.record) == identity_of(original)
        ok = (verifier.record["status"] == "accepted"
              and counts_match and identity_matches)
        ok_all = ok_all and ok
        results.append({
            "case_id": qid,
            "category": case["category"],
            "upstream_sha": case["upstream_sha"],
            "reverified_status": verifier.record["status"],
            "counts_match_screening": counts_match,
            "identity_matches_screening": identity_matches,
            "ok": ok,
        })
        print(f"{qid}: {'OK' if ok else 'MISMATCH'} "
              f"({verifier.record['status']}, counts_match={counts_match}, "
              f"identity_match={identity_matches})", flush=True)

    result_doc = {
        "all_ok": ok_all,
        "verified_case_count": len(results),
        "counts": {
            category: sum(row["category"] == category for row in results)
            for category in "SPN"
        },
        "results": results,
    }
    update_metadata(exp, "fixture_verification", result_doc)
    print("ALL OK" if ok_all else "MISMATCHES PRESENT")
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
