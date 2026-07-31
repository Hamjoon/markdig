#!/usr/bin/env python3
"""Run the post-hoc Zod-equivalent coverage check for successful repairs.

Coverage is collected only for cases whose frozen result has
``repair_success=true``. Each case is reconstructed from its base commit,
fixture patch, and normalized applied repair. The frozen target tests are then
validated and rerun under dotnet-coverage. Raw Cobertura XML stays temporary;
only path-sanitized summaries and logs enter the archive.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


DOTNET_COVERAGE_VERSION = "18.9.0"
ZOD_REFERENCE_COMMIT = "53aaeb99d50a253d83f5dc18791b118c480ea8db"
ZOD_RUNNER_SHA256 = "62a3b96892b00a9433c7b5c1f17539ff660b02eae99ffe3ba260390eaf1a30bc"
ZOD_SIGNAL_CASE_SHA256 = "df5a508508c866e17e6dd5474bbee6ff7c6c4f4573c578250cde695b952f119d"
PROJECT = "src/Markdig.Tests/Markdig.Tests.csproj"
SUMMARY_RE = re.compile(
    r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)"
)


class CoverageError(Exception):
    pass


def load_json(path):
    with path.open() as file:
        return json.load(file)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as file:
        json.dump(value, file, indent=2)
        file.write("\n")


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def case_directory(exp, case):
    archive_id = case.get("archive_case_id") or (
        case["case_id"].lower().replace("-", "")
        + "-"
        + case["upstream_sha"][:8]
    )
    return exp / "cases" / archive_id


def run(command, cwd, env=None, timeout=900):
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise CoverageError(f"timeout: {' '.join(map(str, command))}") from error


def dotnet_env(dotnet):
    root = dotnet.parent
    env = dict(os.environ)
    env.update(
        {
            "DOTNET_ROOT": str(root),
            "PATH": f"{root}:{env.get('PATH', '')}",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_NOLOGO": "1",
            "DOTNET_CLI_UI_LANGUAGE": "en",
        }
    )
    return env


def sanitize(text, repo, worktree, exp):
    replacements = (
        (str(worktree), "<worktree>"),
        (str(exp), "<experiment>"),
        (str(repo), "<repo>"),
        (str(Path.home()), "<home>"),
        (socket.gethostname(), "<hostname>"),
    )
    for source, replacement in replacements:
        if source:
            text = text.replace(source, replacement)
    return text


def command_log(command, result, repo, worktree, exp):
    command_text = " ".join(map(str, command))
    return sanitize(
        "\n".join(
            (
                f"$ {command_text}",
                f"status={result.returncode}",
                "",
                "## stdout",
                result.stdout,
                "",
                "## stderr",
                result.stderr,
            )
        ).rstrip()
        + "\n",
        repo,
        worktree,
        exp,
    )


def test_counts(text):
    matches = SUMMARY_RE.findall(text)
    if not matches:
        return None
    failed, passed, skipped, total = map(int, matches[-1])
    return {
        "failed": failed,
        "passed": passed,
        "skipped": skipped,
        "total": total,
    }


def expected_target_counts(record):
    matches = [
        item
        for item in record["runs"]
        if item["kind"] == "test" and item["label"] == "target-after-model-action"
    ]
    if len(matches) != 1:
        raise CoverageError(f"{record['case_id']}: frozen target run missing")
    return matches[0]["counts"]


def matches_source(filename, production_file):
    filename = filename.replace("\\", "/").lstrip("./")
    production_file = production_file.replace("\\", "/").lstrip("./")
    return filename == production_file or filename.endswith("/" + production_file)


def is_production_path(path):
    normalized = path.replace("\\", "/").lstrip("./")
    return normalized.startswith("src/Markdig/") and normalized.endswith(".cs")


def production_scope(worktree, base_sha, case, record, env):
    """Return the Zod-equivalent net production diff scope.

    Zod computes the production scope from the validated repaired tree's net
    diff against the frozen base. The frozen production paths and the model's
    actual production paths are only candidates; files with no net production
    diff are excluded from coverage qualification.
    """
    candidates = []
    for path in [*case["prod_src_files"], *record["model_patch"]["actual_paths"]]:
        if is_production_path(path) and path not in candidates:
            candidates.append(path)
    if not candidates:
        raise CoverageError(f"{case['case_id']}: no production scope candidates")

    diff = run_checked(
        ["git", "diff", "--no-renames", "--name-only", base_sha, "--", *candidates],
        worktree,
        env,
        "net production diff",
    )
    changed = {line for line in diff.stdout.splitlines() if line}
    included = [path for path in candidates if path in changed]
    excluded = [
        {
            "production_file": path,
            "reason": "no-net-production-diff-in-validated-tree",
        }
        for path in candidates
        if path not in changed
    ]
    if not included:
        raise CoverageError(f"{case['case_id']}: net production diff scope empty")
    return candidates, included, excluded


def summarize_cobertura(path, production_files):
    root = ET.parse(path).getroot()
    per_file = {production_file: {} for production_file in production_files}
    matched_names = {production_file: set() for production_file in production_files}
    for class_node in root.findall(".//class"):
        filename = class_node.get("filename", "")
        targets = [
            item for item in production_files if matches_source(filename, item)
        ]
        for production_file in targets:
            matched_names[production_file].add(filename)
            for line in class_node.findall("./lines/line"):
                number = int(line.get("number", "0"))
                hits = int(line.get("hits", "0"))
                if number:
                    per_file[production_file][number] = max(
                        hits, per_file[production_file].get(number, 0)
                    )

    summaries = []
    for production_file in production_files:
        lines = per_file[production_file]
        total = len(lines)
        covered = sum(hits > 0 for hits in lines.values())
        summaries.append(
            {
                "production_file": production_file,
                "available": bool(matched_names[production_file]) and total > 0,
                "matched_class_file_count": len(matched_names[production_file]),
                "lines": {
                    "total": total,
                    "covered": covered,
                    "pct": round(covered * 100 / total, 2) if total else 0,
                },
                "covered": covered > 0,
            }
        )
    return summaries


def run_checked(command, cwd, env, label):
    result = run(command, cwd=cwd, env=env)
    if result.returncode:
        excerpt = (result.stdout + result.stderr).strip()[-500:]
        raise CoverageError(f"{label} failed ({result.returncode}): {excerpt}")
    return result


def reconstruct_and_cover(repo, exp, case, coverage_tool, dotnet, replace):
    case_id = case["case_id"]
    case_dir = case_directory(exp, case)
    result_path = case_dir / "result.json"
    record = load_json(result_path)
    if not record.get("repair_success"):
        raise CoverageError(f"{case_id}: coverage requested for unsuccessful repair")

    output = case_dir / "coverage"
    if output.exists():
        if not replace:
            raise CoverageError(f"{case_id}: coverage output already exists")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    worktree = repo / ".worktrees" / f"coverage-{case_id}"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
        capture_output=True,
    )
    add = run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), case["base_sha"]],
        cwd=repo,
    )
    if add.returncode:
        raise CoverageError(f"{case_id}: worktree add failed: {add.stderr.strip()}")

    env = dotnet_env(dotnet)
    fixture_path = case_dir / "fixture.patch"
    repair_path = case_dir / "applied-repair.diff"
    log_parts = []
    try:
        fixture = run(
            ["git", "apply", "--whitespace=nowarn", str(fixture_path)],
            cwd=worktree,
            env=env,
        )
        log_parts.append(command_log(
            ["git", "apply", "--whitespace=nowarn", str(fixture_path)],
            fixture, repo, worktree, exp))
        if fixture.returncode:
            raise CoverageError(f"{case_id}: fixture apply failed")
        run_checked(["git", "add", "-A"], worktree, env, "fixture add")
        run_checked(
            [
                "git", "-c", "user.name=Markdig coverage evaluator", "-c",
                "user.email=coverage-evaluator@example.invalid", "commit", "-q",
                "-m", f"fixture {case_id}",
            ],
            worktree,
            env,
            "fixture commit",
        )

        if sha256_text(repair_path.read_text()) != record["model_patch"]["applied_diff_sha256"]:
            raise CoverageError(f"{case_id}: applied repair hash mismatch")
        repair = run(
            ["git", "apply", "--whitespace=nowarn", str(repair_path)],
            cwd=worktree,
            env=env,
        )
        log_parts.append(command_log(
            ["git", "apply", "--whitespace=nowarn", str(repair_path)],
            repair, repo, worktree, exp))
        if repair.returncode:
            raise CoverageError(f"{case_id}: normalized repair apply failed")

        changed = run_checked(
            ["git", "diff", "--name-only", "HEAD"], worktree, env, "changed paths")
        actual_paths = [line for line in changed.stdout.splitlines() if line]
        if actual_paths != record["model_patch"]["actual_paths"]:
            raise CoverageError(f"{case_id}: normalized repair path mismatch")

        scope_candidates, production_files, excluded_candidates = production_scope(
            worktree, case["base_sha"], case, record, env
        )

        preservation = run(
            [
                "git", "apply", "--reverse", "--check", "--whitespace=nowarn",
                str(fixture_path),
            ],
            cwd=worktree,
            env=env,
        )
        log_parts.append(command_log(
            ["git", "apply", "--reverse", "--check", str(fixture_path)],
            preservation, repo, worktree, exp))
        if preservation.returncode:
            raise CoverageError(f"{case_id}: preservation recheck failed")

        build_command = [
            str(dotnet), "build", PROJECT, "-c", "Release", "-f", case["tfm"],
            "-v", "q",
        ]
        build = run(build_command, cwd=worktree, env=env)
        log_parts.append(command_log(build_command, build, repo, worktree, exp))
        if build.returncode:
            raise CoverageError(f"{case_id}: build failed")

        target_command = [
            str(dotnet), "test", PROJECT, "-c", "Release", "-f", case["tfm"],
            "--no-build", "--filter", case["target_filter"],
        ]
        target = run(target_command, cwd=worktree, env=env)
        log_parts.append(command_log(target_command, target, repo, worktree, exp))
        counts = test_counts(target.stdout + target.stderr)
        if target.returncode or counts != expected_target_counts(record):
            raise CoverageError(
                f"{case_id}: target validation mismatch: {counts}"
            )

        loaded_assembly = (
            worktree / "src" / "Markdig.Tests" / "bin" / "Release"
            / case["tfm"] / "Markdig.dll"
        )
        if not loaded_assembly.is_file():
            raise CoverageError(f"{case_id}: loaded Markdig.dll not found")

        with tempfile.TemporaryDirectory(prefix=f"coverage-{case_id}-") as temp:
            cobertura = Path(temp) / "coverage.cobertura.xml"
            coverage_command = [
                str(coverage_tool), "collect", "--output", str(cobertura),
                "--output-format", "cobertura", "--include-files",
                str(loaded_assembly), "--nologo", "--", *target_command,
            ]
            coverage = run(
                coverage_command, cwd=worktree, env=env, timeout=1200)
            coverage_log = command_log(
                coverage_command, coverage, repo, worktree, exp
            )
            sanitized_temp = sanitize(str(Path(temp)), repo, worktree, exp)
            coverage_log = (
                coverage_log
                .replace(str(coverage_tool), "<dotnet-coverage>")
                .replace(str(Path(temp)), "<temporary>")
                .replace(sanitized_temp, "<temporary>")
            )
            log_parts.append(coverage_log)
            if coverage.returncode or not cobertura.is_file():
                raise CoverageError(f"{case_id}: coverage collection failed")
            files = summarize_cobertura(cobertura, production_files)

        all_available = all(item["available"] for item in files)
        all_covered = all(item["covered"] for item in files)
        verdict = (
            "signal_preserved" if all_available and all_covered
            else "signal_weakened" if all_available
            else "signal_unknown"
        )
        summary = {
            "schema_version": 1,
            "case_id": case_id,
            "category": case["category"],
            "post_hoc": True,
            "repair_success": True,
            "target_filter": case["target_filter"],
            "target_validation": {"status": target.returncode, "counts": counts},
            "preservation_rechecked": True,
            "coverage_tool": {
                "name": "dotnet-coverage",
                "version": DOTNET_COVERAGE_VERSION,
                "output_format": "cobertura",
            },
            "production_scope": {
                "basis": "net validated-tree diff from frozen base",
                "candidate_production_files": scope_candidates,
                "excluded_candidate_production_files": excluded_candidates,
            },
            "production_files": files,
            "all_production_files_available": all_available,
            "all_production_files_covered": all_covered,
            "coverage_verdict": verdict,
            "zod_reference": {
                "commit": ZOD_REFERENCE_COMMIT,
                "run_zod_signal_eval_sha256": ZOD_RUNNER_SHA256,
                "signal_case_sha256": ZOD_SIGNAL_CASE_SHA256,
            },
        }
        write_json(output / "coverage-summary.json", summary)
        (output / "coverage.log").write_text("\n".join(log_parts))
        return summary
    finally:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
            capture_output=True,
        )


def non_applicable_result(case, record):
    if case["category"] == "N":
        reason = "no-repair-required"
        verdict = "not_applicable"
    elif record["response"]["decision"] == record["expected_decision"]:
        reason = "repair-incomplete"
        verdict = "partial_repair"
    else:
        reason = "repair-target-misclassified"
        verdict = "signal_unknown"
    return {
        "applicable": False,
        "reason": reason,
        "coverage_verdict": verdict,
        "production_files": [],
    }


def update_results(exp, manifest, completed):
    aggregate_path = exp / "results-summary.json"
    aggregate = load_json(aggregate_path)
    rows = {row["case_id"]: row for row in aggregate["results"]}
    coverage_rows = []
    coverage_qualified = 0
    for case in manifest["cases"]:
        case_dir = case_directory(exp, case)
        record_path = case_dir / "result.json"
        record = load_json(record_path)
        if record.get("repair_success"):
            summary = completed[case["case_id"]]
            coverage = {
                "applicable": True,
                "reason": None,
                "coverage_verdict": summary["coverage_verdict"],
                "production_scope": summary["production_scope"],
                "production_files": summary["production_files"],
                "artifact": "coverage/coverage-summary.json",
            }
        else:
            coverage = non_applicable_result(case, record)
        qualified = bool(
            record["strict_signal_pass"]
            and (
                not coverage["applicable"]
                or coverage["coverage_verdict"] == "signal_preserved"
            )
        )
        record["coverage"] = coverage
        record["coverage_qualified_strict_signal_pass"] = qualified
        write_json(record_path, record)
        rows[case["case_id"]]["coverage"] = coverage
        rows[case["case_id"]]["coverage_qualified_strict_signal_pass"] = qualified
        coverage_qualified += qualified
        coverage_rows.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                **coverage,
            }
        )

    applicable = [row for row in coverage_rows if row["applicable"]]
    file_scopes = [
        item for row in applicable for item in row["production_files"]
    ]
    aggregate["coverage_audit"] = {
        "schema_version": 1,
        "post_hoc": True,
        "criterion": (
            "Zod Week 4 file-level line coverage on the repaired tree, "
            "running frozen target tests only"
        ),
        "tool": {"name": "dotnet-coverage", "version": DOTNET_COVERAGE_VERSION},
        "applicable_case_count": len(applicable),
        "signal_preserved_case_count": sum(
            row["coverage_verdict"] == "signal_preserved" for row in applicable
        ),
        "signal_weakened_case_count": sum(
            row["coverage_verdict"] == "signal_weakened" for row in applicable
        ),
        "signal_unknown_case_count": sum(
            row["coverage_verdict"] == "signal_unknown" for row in applicable
        ),
        "production_file_scope_count": len(file_scopes),
        "covered_production_file_scope_count": sum(
            item["covered"] for item in file_scopes
        ),
        "mutation_testing": "excluded-by-instruction",
        "results": coverage_rows,
    }
    aggregate["coverage_qualified_strict_signal_pass"] = coverage_qualified
    write_json(aggregate_path, aggregate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--exp", default="experiments/test-maintenance")
    parser.add_argument("--coverage-tool", required=True)
    parser.add_argument("--dotnet", default=str(Path.home() / ".dotnet" / "dotnet"))
    parser.add_argument("--case")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    exp = Path(args.exp).resolve()
    coverage_tool = Path(args.coverage_tool).resolve()
    dotnet = Path(args.dotnet).resolve()
    if not coverage_tool.is_file() or not dotnet.is_file():
        raise SystemExit("coverage tool or dotnet executable missing")
    version = run(
        [str(coverage_tool), "--version"],
        cwd=repo,
        env=dotnet_env(dotnet),
    )
    if version.returncode or not version.stdout.startswith(DOTNET_COVERAGE_VERSION):
        raise SystemExit(f"unexpected dotnet-coverage version: {version.stdout.strip()}")

    manifest = load_json(exp / "cases.json")
    selected = [
        case for case in manifest["cases"]
        if load_json(case_directory(exp, case) / "result.json").get("repair_success")
    ]
    if args.case:
        selected = [case for case in selected if case["case_id"] == args.case]
        if len(selected) != 1:
            raise SystemExit("selected case is not a successful repair")

    completed = {}
    for case in selected:
        print(f"COVERAGE: START {case['case_id']}", flush=True)
        try:
            completed[case["case_id"]] = reconstruct_and_cover(
                repo, exp, case, coverage_tool, dotnet, args.replace
            )
        except CoverageError as error:
            print(f"COVERAGE: ERROR {case['case_id']} {error}", flush=True)
            raise SystemExit(1) from error
        summary = completed[case["case_id"]]
        print(
            f"COVERAGE: OK {case['case_id']} "
            f"verdict={summary['coverage_verdict']}",
            flush=True,
        )

    if not args.case:
        update_results(exp, manifest, completed)
        print(f"COVERAGE COMPLETE cases={len(completed)}", flush=True)


if __name__ == "__main__":
    main()
