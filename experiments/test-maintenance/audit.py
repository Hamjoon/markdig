#!/usr/bin/env python3
"""Audit the public, case-centered Markdig Week 5 archive."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SUMMARY_RE = re.compile(
    r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)"
)
ROOT_ENTRIES = {".gitignore", "README.md", "docs", "experiments", "scripts"}
ROOT_SCRIPTS = {
    "mine-candidates.py",
    "run-gptoss-test-maintenance.py",
    "run-markdig-signal-eval.py",
}
REQUIRED_DOCS = {
    "markdig-23case-evaluation-protocol.md",
    "markdig-23case-model-run-protocol.md",
    "markdig-23case-protocol.md",
    "markdig-23case-screening.md",
    "markdig-23case-stage-log.md",
    "markdig-23case-verification-results.md",
    "markdig-v2-23case-report-full.md",
    "markdig-v2-23case-report.md",
}
REQUIRED_CASE_FILES = {
    "fixture.patch",
    "gptoss-prompt.md",
    "gptoss-response.md",
    "gptoss-run.json",
    "gptoss-usage.json",
    "input.json",
    "result.json",
    "test-output.txt",
}
CORE_JSON_FILES = {
    "cases.json",
    "results-summary.json",
    "screening_queues.json",
}
COVERAGE_EXPECTED = {
    "P-02": {
        "target": {"failed": 0, "passed": 4, "skipped": 0, "total": 4},
        "file": "src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs",
        "lines_valid": 115,
        "lines_covered": 108,
        "excluded": [],
    },
    "P-05": {
        "target": {"failed": 0, "passed": 46, "skipped": 0, "total": 46},
        "file": "src/Markdig/Parsers/Inlines/CodeInlineParser.cs",
        "lines_valid": 66,
        "lines_covered": 63,
        "excluded": [
            {
                "production_file": "src/Markdig/Polyfills/SpanExtensions.cs",
                "reason": "no-net-production-diff-in-validated-tree",
            }
        ],
    },
}


def load_json(path):
    with path.open() as file:
        return json.load(file)


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def test_counts(text):
    matches = SUMMARY_RE.findall(text)
    if not matches:
        return None
    return dict(zip(
        ("failed", "passed", "skipped", "total"), map(int, matches[-1])
    ))


def expected_archive_id(case):
    return (
        case["case_id"].lower().replace("-", "")
        + "-"
        + case["upstream_sha"][:8]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    exp = root / "experiments" / "test-maintenance"
    docs = root / "docs"
    scripts = root / "scripts"
    output = root / args.output if args.output else None
    failures = []
    checks = {}

    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            failures.append(name)

    top_entries = {path.name for path in root.iterdir() if path.name != ".git"}
    check("root-layout", top_entries == ROOT_ENTRIES)
    check(
        "root-scripts",
        scripts.is_dir()
        and {path.name for path in scripts.iterdir() if path.is_file()}
        == ROOT_SCRIPTS,
    )
    check(
        "docs-layout",
        docs.is_dir()
        and {path.name for path in docs.iterdir() if path.is_file()}
        == REQUIRED_DOCS,
    )
    check(
        "experiment-root-json-layout",
        {path.name for path in exp.glob("*.json")} == CORE_JSON_FILES,
    )
    check(
        "metadata-layout",
        (exp / "metadata").is_dir()
        and {
            path.name for path in (exp / "metadata").iterdir()
            if path.is_file()
        } == {"experiment.json"},
    )
    coverage_parser = exp / "scripts" / "parse-cobertura.py"
    check(
        "coverage-parser",
        coverage_parser.is_file()
        and sha256_text(coverage_parser.read_text())
        == "622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18",
    )

    manifest = load_json(exp / "cases.json")
    results = load_json(exp / "results-summary.json")
    queues = load_json(exp / "screening_queues.json")
    metadata = load_json(exp / "metadata" / "experiment.json")
    cases = manifest["cases"]
    result_rows = {row["case_id"]: row for row in results["results"]}

    check(
        "manifest-counts",
        manifest["case_count"] == 23
        and manifest["counts"] == {"S": 3, "P": 10, "N": 10}
        and len(cases) == 23,
    )
    check(
        "aggregate-results",
        results["case_count"] == 23
        and results["decision_correct"] == 17
        and results["fix_patch_apply_succeeded"] == 13
        and results["repair_success"] == 2
        and results["strict_signal_pass"] == 9
        and results["pipeline_errors"] == 0,
    )
    screening = metadata["selection"]["screening"]
    screening_matches = True
    for category in "SPN":
        queue = queues["queues"][category]
        screened = screening[category]
        screening_matches = screening_matches and (
            screened["category"] == category
            and len(screened["results"]) == len(queue)
            and screened["accepted"] == manifest["counts"][category]
            and all(
                row["queue_id"] == entry["queue_id"]
                and row["sha"] == entry["sha"]
                for row, entry in zip(screened["results"], queue)
            )
        )
    check(
        "selection-metadata",
        metadata["selection"]["mining"]["pool_sizes"]
        == {"S": 12, "P": 23, "N": 32}
        and screening_matches,
    )
    verification = metadata["fixture_verification"]
    check(
        "fixture-verification-metadata",
        verification["all_ok"]
        and verification["verified_case_count"] == 23
        and verification["counts"] == {"S": 3, "P": 10, "N": 10}
        and len(verification["results"]) == 23
        and all(row["ok"] for row in verification["results"]),
    )

    expected_dirs = {expected_archive_id(case) for case in cases}
    actual_dirs = {
        path.name for path in (exp / "cases").iterdir() if path.is_dir()
    }
    check("case-directory-set", actual_dirs == expected_dirs)

    artifact_counts = Counter()
    case_failures = []
    coverage_failures = []
    usage_totals = Counter()
    run_statuses = Counter()
    requested_models = Counter()
    returned_models = Counter()
    finish_reasons = Counter()
    transport_retries = 0
    for case in cases:
        case_id = case["case_id"]
        archive_id = expected_archive_id(case)
        case_dir = exp / "cases" / archive_id
        row = result_rows.get(case_id)
        try:
            record = load_json(case_dir / "result.json")
            run = load_json(case_dir / "gptoss-run.json")
            usage = load_json(case_dir / "gptoss-usage.json")
            local_input = load_json(case_dir / "input.json")
        except (FileNotFoundError, json.JSONDecodeError) as error:
            case_failures.append(f"{case_id}: {error}")
            continue

        names = {path.name for path in case_dir.iterdir() if path.is_file()}
        if not REQUIRED_CASE_FILES.issubset(names):
            case_failures.append(f"{case_id}: required file missing")
            continue
        if case.get("archive_case_id") != archive_id:
            case_failures.append(f"{case_id}: archive id mismatch")

        prompt = (case_dir / "gptoss-prompt.md").read_text()
        response = (case_dir / "gptoss-response.md").read_text()
        fixture = (case_dir / "fixture.patch").read_text()
        input_test = (case_dir / "test-output.txt").read_text()
        if not (
            local_input["case_id"] == case_id
            and local_input["category"] == case["category"]
            and local_input["base_sha"] == case["base_sha"]
            and local_input["upstream_sha"] == case["upstream_sha"]
            and local_input["prompt_sha256"] == sha256_text(prompt)
            and local_input["fixture_patch_sha256"] == sha256_text(fixture)
            and local_input["test_output_sha256"] == sha256_text(input_test)
            and run["response_sha256"] == sha256_text(response)
            and record["response"]["response_sha256"] == sha256_text(response)
        ):
            case_failures.append(f"{case_id}: immutable input/response hash mismatch")

        record_row = {
            "decision": record["response"]["decision"],
            "decision_correct": record["decision_correct"],
            "response_contract_valid": record["response_contract_valid"],
            "patch_apply_method": record["model_patch"]["apply_method"],
            "patch_apply_succeeded": record["model_patch"]["apply_succeeded"],
            "behavior_validation_pass": record["behavior_validation_pass"],
            "preservation_passed": record["preservation"]["passed"],
            "repair_success": record["repair_success"],
            "strict_signal_pass": record["strict_signal_pass"],
            "coverage": record.get("coverage"),
            "status": record["status"],
            "reason": record["reason"],
        }
        if row is None or any(row.get(key) != value for key, value in record_row.items()):
            case_failures.append(f"{case_id}: per-case result differs from aggregate")

        repair_path = case_dir / "gptoss-repair.patch"
        if repair_path.is_file() != record["response"]["patch_present"]:
            case_failures.append(f"{case_id}: extracted patch presence mismatch")
        elif repair_path.is_file() and sha256_text(repair_path.read_text()) != record[
            "response"
        ]["extracted_patch_sha256"]:
            case_failures.append(f"{case_id}: extracted patch hash mismatch")

        applied_path = case_dir / "applied-repair.diff"
        if applied_path.is_file() != record["model_patch"]["apply_succeeded"]:
            case_failures.append(f"{case_id}: applied diff presence mismatch")
        elif applied_path.is_file() and sha256_text(applied_path.read_text()) != record[
            "model_patch"
        ]["applied_diff_sha256"]:
            case_failures.append(f"{case_id}: applied diff hash mismatch")

        test_runs = [run_row for run_row in record["runs"] if run_row["kind"] == "test"]
        validation_path = case_dir / "validation.log"
        if bool(test_runs) != validation_path.is_file():
            case_failures.append(f"{case_id}: validation log presence mismatch")
        elif test_runs and test_counts(validation_path.read_text()) != test_runs[-1]["counts"]:
            case_failures.append(f"{case_id}: validation counts mismatch")

        coverage_dir = case_dir / "coverage"
        if case_id in COVERAGE_EXPECTED:
            expected = COVERAGE_EXPECTED[case_id]
            summary_path = coverage_dir / "coverage-summary.json"
            log_path = coverage_dir / "coverage.log"
            if not summary_path.is_file() or not log_path.is_file():
                coverage_failures.append(f"{case_id}: coverage artifact missing")
            else:
                summary = load_json(summary_path)
                files = summary.get("production_files", [])
                excluded = summary.get("production_scope", {}).get(
                    "excluded_candidate_production_files"
                )
                valid_file = len(files) == 1 and (
                    files[0].get("file") == expected["file"]
                    and files[0].get("lines_valid") == expected["lines_valid"]
                    and files[0].get("lines_covered") == expected["lines_covered"]
                    and files[0].get("covered") is True
                )
                coverage_log = log_path.read_text()
                if not (
                    summary.get("case_id") == case_id
                    and "post_hoc" not in summary
                    and summary.get("repair_success") is True
                    and summary.get("target_validation", {}).get("counts")
                    == expected["target"]
                    and summary.get("preservation_rechecked") is True
                    and summary.get("coverage_collector") == {
                        "name": "Microsoft.NET.Test.Sdk built-in Code Coverage collector",
                        "command": "dotnet test --collect:Code Coverage;Format=cobertura",
                        "output_format": "cobertura",
                    }
                    and summary.get("coverage_parser") == {
                        "path": "scripts/parse-cobertura.py",
                        "sha256": "622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18",
                    }
                    and summary.get("markdig_week4_reference") == {
                        "commit": "caf6195e3c3a25b3b153329cb29ae7270bce5b57",
                        "signal_sha256": "acdf6b3ca65f8cf3d9ad45e4ddedfea7c7f0d504c07e3da857e99db0a75273cf",
                        "parse_cobertura_sha256": "622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18",
                    }
                    and summary.get("production_scope", {}).get("basis")
                    == "net validated-tree diff from frozen base"
                    and excluded == expected["excluded"]
                    and valid_file
                    and summary.get("coverage_verdict") == "signal_preserved"
                    and record.get("coverage", {}).get("coverage_verdict")
                    == "signal_preserved"
                    and record.get("coverage", {}).get("production_files") == files
                    and record.get("strict_signal_pass") is True
                    and "--collect:Code Coverage;Format=cobertura" in coverage_log
                    and "<experiment>/scripts/parse-cobertura.py" in coverage_log
                    and "<temporary>/coverage.cobertura.xml" in coverage_log
                ):
                    coverage_failures.append(f"{case_id}: coverage evidence mismatch")
        elif coverage_dir.exists():
            coverage_failures.append(f"{case_id}: unexpected coverage directory")

        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            usage_totals[key] += usage.get(key, 0)
        usage_totals["cost_usd"] += usage.get("cost", 0)
        run_statuses[run.get("status")] += 1
        requested_models[run.get("model_requested")] += 1
        returned_models[run.get("model_returned")] += 1
        finish_reasons[run.get("finish_reason")] += 1
        transport_retries += max(run.get("attempt_count", 0) - 1, 0)
        for name in names:
            artifact_counts[name] += 1

    check("case-packet-integrity", not case_failures)
    check("coverage-case-integrity", not coverage_failures)
    check(
        "case-artifact-counts",
        artifact_counts["fixture.patch"] == 23
        and artifact_counts["gptoss-response.md"] == 23
        and artifact_counts["gptoss-repair.patch"] == 16
        and artifact_counts["applied-repair.diff"] == 13
        and artifact_counts["validation.log"] == 17,
    )
    check(
        "usage-totals",
        usage_totals["prompt_tokens"] == 75626
        and usage_totals["completion_tokens"] == 34534
        and usage_totals["total_tokens"] == 110160
        and abs(usage_totals["cost_usd"] - 0.011487683) < 1e-12,
    )
    check(
        "model-run-gate",
        run_statuses == {"response_received": 23}
        and requested_models == {"openai/gpt-oss-120b": 23}
        and returned_models == {"openai/gpt-oss-120b": 23}
        and finish_reasons == {"stop": 23}
        and transport_retries == 0,
    )
    coverage_audit = results.get("coverage_audit", {})
    check(
        "coverage-aggregate",
        results.get("strict_signal_pass") == 9
        and "coverage_qualified_strict_signal_pass" not in results
        and coverage_audit.get("schema_version") == 1
        and "post_hoc" not in coverage_audit
        and coverage_audit.get("collector") == {
            "name": "Microsoft.NET.Test.Sdk built-in Code Coverage collector",
            "command": "dotnet test --collect:Code Coverage;Format=cobertura",
            "output_format": "cobertura",
        }
        and coverage_audit.get("parser") == {
            "path": "scripts/parse-cobertura.py",
            "sha256": "622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18",
        }
        and coverage_audit.get("markdig_week4_reference") == {
            "commit": "caf6195e3c3a25b3b153329cb29ae7270bce5b57",
            "signal_sha256": "acdf6b3ca65f8cf3d9ad45e4ddedfea7c7f0d504c07e3da857e99db0a75273cf",
            "parse_cobertura_sha256": "622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18",
        }
        and coverage_audit.get("applicable_case_count") == 2
        and coverage_audit.get("signal_preserved_case_count") == 2
        and coverage_audit.get("signal_weakened_case_count") == 0
        and coverage_audit.get("signal_unknown_case_count") == 0
        and coverage_audit.get("production_file_scope_count") == 2
        and coverage_audit.get("covered_production_file_scope_count") == 2
        and coverage_audit.get("mutation_testing") == "excluded-by-instruction",
    )

    json_failures = []
    for path in root.rglob("*.json"):
        try:
            load_json(path)
        except json.JSONDecodeError:
            json_failures.append(str(path.relative_to(root)))
    check("json-parse", not json_failures)

    raw_coverage_artifacts = [
        str(path.relative_to(root))
        for suffix in ("*.xml", "*.coverage", "*.cobertura")
        for path in root.rglob(suffix)
    ]
    check("no-raw-coverage-artifacts", not raw_coverage_artifacts)

    empty_files = [
        str(path.relative_to(root))
        for base in (docs, exp / "cases", exp / "metadata")
        for path in base.rglob("*")
        if path.is_file() and path.stat().st_size == 0
    ]
    check("no-empty-public-artifacts", not empty_files)

    leak_patterns = (
        re.compile(r"/Users/[A-Za-z0-9._-]+/"),
        re.compile(r"/home/[A-Za-z0-9._-]+/"),
        re.compile(r"/\.openclaw/"),
        re.compile(r"Authorization:\s*Bearer\s+\S+"),
        re.compile(r"sk-or-[A-Za-z0-9_-]+"),
    )
    leak_matches = []
    for base in (docs, exp / "cases", exp / "metadata"):
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(errors="replace")
            for pattern in leak_patterns:
                if pattern.search(text):
                    leak_matches.append(
                        {
                            "file": str(path.relative_to(root)),
                            "pattern": pattern.pattern,
                        }
                    )
    check("sensitive-value-scan", not leak_matches)

    report = (docs / "markdig-v2-23case-report.md").read_text()
    full_report = (docs / "markdig-v2-23case-report-full.md").read_text()
    required_claims = (
        "17/23 cases (73.9%)",
        "13/16",
        "2/13 required repairs (15.4%)",
        "9/23 (39.1%)",
        "2/2",
        "108/115 (93.91%)",
        "63/66 (95.45%)",
        "Coverage Signal",
        'dotnet test --collect:"Code Coverage;Format=cobertura"',
        "parse-cobertura.py",
    )
    normalized_reports = " ".join((report + full_report).split())
    check("report-claims", all(claim in normalized_reports for claim in required_claims))
    matrix_rows = {}
    for line in report.splitlines():
        match = re.match(r"\| \[([SPN]-\d{2})\]", line)
        if match:
            matrix_rows[match.group(1)] = line
    matrix_ok = len(matrix_rows) == 23
    for case in cases:
        case_id = case["case_id"]
        row = result_rows[case_id]
        line = matrix_rows.get(case_id, "")
        decision_marker = "✅" if row["decision_correct"] else "❌"
        final_cell = (
            "none"
            if case["category"] == "N" and row["decision"] == "no_change"
            else "**yes**"
            if case["category"] == "N" or row["repair_success"]
            else "no"
        )
        matrix_ok = matrix_ok and all(
            token in line
            for token in (
                f"[{case_id}](../experiments/test-maintenance/cases/"
                f"{case['archive_case_id']}/)",
                f"[{case['base_sha'][:8]}](https://github.com/xoofx/markdig/"
                f"commit/{case['base_sha'][:8]})",
                f"[{case['upstream_sha'][:8]}](https://github.com/xoofx/"
                f"markdig/commit/{case['upstream_sha'][:8]})",
                f"| {row['decision']} {decision_marker} | {final_cell} |",
            )
        )
    check(
        "summary-case-matrix",
        matrix_ok
        and report.count("### Case Matrix —") == 3
        and "### Headline numbers" in report
        and "Unnecessary edits on normal cases: **3 / 10**" in report,
    )
    public_prose = (root / "README.md").read_text() + "\n" + "\n".join(
        path.read_text() for path in docs.glob("*.md")
    )
    check(
        "coverage-wording",
        not re.search(
            r"post-hoc|supplemental|coverage-qualified|accident",
            public_prose,
            re.IGNORECASE,
        ),
    )
    check(
        "canonical-evaluation-wording",
        not re.search(
            r"correction notice|corrected evaluation|supersed|"
            r"earlier evaluation|initial evaluation|preceding 0/16|"
            r"original 0/16|reevaluat|format-only (?:gate|stop)",
            public_prose,
            re.IGNORECASE,
        )
        and "supersedes_evaluation_commit" not in results,
    )

    audit = {
        "schema_version": 1,
        "all_ok": not failures,
        "checks": checks,
        "failures": failures,
        "case_count": len(cases),
        "case_failures": case_failures,
        "coverage_failures": coverage_failures,
        "artifact_counts": dict(sorted(artifact_counts.items())),
        "json_failures": json_failures,
        "raw_coverage_artifacts": raw_coverage_artifacts,
        "empty_files": empty_files,
        "leak_matches": leak_matches,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w") as file:
            json.dump(audit, file, indent=2)
            file.write("\n")
    print(json.dumps(audit, indent=2))
    raise SystemExit(0 if audit["all_ok"] else 1)


if __name__ == "__main__":
    main()
