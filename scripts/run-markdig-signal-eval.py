#!/usr/bin/env python3
"""Evaluate frozen GPT-OSS responses against frozen Markdig fixtures."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

BUILD_TIMEOUT = 900
TEST_TIMEOUT = 900
SUMMARY_RE = re.compile(
    r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)")
FAILED_NAME_RE = re.compile(r"^\s*Failed\s+(\S+)", re.MULTILINE)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
OLD_HEADER_RE = re.compile(r"^---\s+([^\t\n]+)", re.MULTILINE)
NEW_HEADER_RE = re.compile(r"^\+\+\+\s+([^\t\n]+)", re.MULTILINE)
HUNK_HEADER_RE = re.compile(
    r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@(?: .*)?$")

DECISIONS = {
    "DECISION: no_change": "no_change",
    "DECISION: fix_tests": "fix_tests",
    "DECISION: fix_production": "fix_production",
}
EXPECTED = {"S": "fix_tests", "P": "fix_production", "N": "no_change"}
APPLY_METHODS = ("git-apply", "git-apply-recount", "patch-fuzz", "context-match")


class PipelineError(Exception):
    pass


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_json(path):
    with path.open() as file:
        return json.load(file)


def case_directory(exp, case):
    archive_id = case.get("archive_case_id")
    if not archive_id:
        archive_id = (
            case["case_id"].lower().replace("-", "")
            + "-"
            + case["upstream_sha"][:8]
        )
    return exp / "cases" / archive_id


def run(cmd, cwd, env=None, timeout=None, stdin_text=None):
    try:
        return subprocess.run(
            cmd, cwd=cwd, env=env, input=stdin_text, capture_output=True,
            text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise PipelineError(f"timeout: {' '.join(map(str, cmd))}") from error


def dotnet_env():
    task_home = os.path.expanduser("~")
    env = dict(os.environ)
    env.update({
        "DOTNET_ROOT": f"{task_home}/.dotnet",
        "PATH": f"{task_home}/.dotnet:{env.get('PATH', '')}",
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_NOLOGO": "1",
        "DOTNET_CLI_UI_LANGUAGE": "en",
    })
    return env


def normalize_header_path(value):
    value = value.strip()
    if value == "/dev/null":
        return None
    if value.startswith(("a/", "b/")):
        value = value[2:]
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe diff path: {value}")
    return value


def extract_response(text, allowed_paths):
    lines = text.splitlines()
    first_line = lines[0].strip() if lines else ""
    decision = DECISIONS.get(first_line)
    body = "\n".join(lines[1:]).strip()
    result = {
        "first_line": first_line,
        "decision": decision,
        "decision_line_valid": decision is not None,
        "body_empty": not body,
        "patch_present": False,
        "raw_unified_diff_conformant": False,
        "header_paths_safe": True,
        "header_scope_valid": True,
        "header_paths": [],
        "parse_reason": None,
        "extracted_patch": None,
    }
    if decision is None:
        result["parse_reason"] = "invalid-decision-line"
        return result
    if decision == "no_change":
        if body:
            result["parse_reason"] = "no-change-with-body"
        return result
    if not body:
        result["parse_reason"] = "fix-without-patch"
        return result

    blocks = FENCE_RE.findall(body)
    if len(blocks) > 1:
        result["parse_reason"] = "multiple-fenced-blocks"
        return result
    patch = (blocks[0] if blocks else body).strip() + "\n"
    result["patch_present"] = True
    result["extracted_patch"] = patch

    old_headers = OLD_HEADER_RE.findall(patch)
    new_headers = NEW_HEADER_RE.findall(patch)
    hunk_headers = [line for line in patch.splitlines()
                    if line.startswith("@@")]
    try:
        paths = sorted(set(
            path for path in
            [normalize_header_path(item) for item in old_headers + new_headers]
            if path))
    except ValueError:
        result["header_paths_safe"] = False
        result["header_scope_valid"] = False
        result["parse_reason"] = "unsafe-diff-path"
        return result
    result["header_paths"] = paths
    result["header_scope_valid"] = set(paths).issubset(set(allowed_paths))
    if not result["header_scope_valid"]:
        result["parse_reason"] = "model-patch-header-out-of-scope"
        return result
    result["raw_unified_diff_conformant"] = bool(
        old_headers and len(old_headers) == len(new_headers)
        and hunk_headers
        and all(HUNK_HEADER_RE.fullmatch(line) for line in hunk_headers))
    return result


class Attempt:
    def __init__(self, repo, exp, case, attempt, output_dir):
        self.repo = repo
        self.exp = exp
        self.case = case
        self.case_id = case["case_id"]
        self.attempt = attempt
        self.output_dir = output_dir
        self.log_dir = output_dir / "logs"
        self.worktree = repo / ".worktrees" / f"evaluate-{self.case_id}"
        self.log_seq = 0
        self.all_allowed = list(dict.fromkeys(
            case["prod_src_files"] + case["test_src_files"] + case["spec_md_files"]))
        self.side_allowed = {
            "fix_tests": set(case["test_src_files"] + case["spec_md_files"]),
            "fix_production": set(case["prod_src_files"]),
        }
        self.record = {
            "case_id": self.case_id,
            "category": case["category"],
            "expected_decision": EXPECTED[case["category"]],
            "attempt": attempt,
            "status": None,
            "reason": None,
            "response": {},
            "fixture": {
                "base_sha": case["base_sha"],
                "upstream_sha": case["upstream_sha"],
                "tfm": case["tfm"],
                "target_filter": case["target_filter"],
                "constructed": False,
                "committed": False,
            },
            "model_patch": {
                "apply_attempted": False,
                "apply_attempts": [],
                "apply_method": None,
                "apply_succeeded": False,
                "effective_change": False,
                "actual_paths": [],
                "scope_valid": None,
                "decision_side_valid": None,
                "applied_diff": None,
                "applied_diff_sha256": None,
            },
            "preservation": {"checked": False, "passed": False, "rc": None},
            "runs": [],
            "decision_correct": False,
            "response_contract_valid": False,
            "behavior_validation_pass": False,
            "repair_success": False,
            "strict_signal_pass": False,
        }

    def sanitize(self, text):
        task_home = os.path.expanduser("~")
        return (text.replace(str(self.worktree), "<worktree>")
                    .replace(str(self.repo), "<repo>")
                    .replace(task_home, "<home>"))

    def save_log(self, label, text, tail=None):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        lines = [line.rstrip() for line in self.sanitize(text).splitlines()]
        if tail and len(lines) > tail:
            lines = [f"[... truncated, last {tail} lines ...]"] + lines[-tail:]
        self.log_seq += 1
        path = self.log_dir / f"{self.log_seq:02d}-{label}.txt"
        path.write_text("\n".join(lines) + "\n")
        return str(path.relative_to(self.exp))

    def create_worktree(self):
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "remove", "--force",
             str(self.worktree)], capture_output=True)
        result = run(
            ["git", "-C", str(self.repo), "worktree", "add", "--detach",
             str(self.worktree), self.case["base_sha"]], cwd=self.repo)
        if result.returncode:
            raise PipelineError(
                f"worktree-add-failed: {result.stderr.strip()[:200]}")

    def remove_worktree(self):
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "remove", "--force",
             str(self.worktree)], capture_output=True)

    def apply_fixture(self):
        patch_path = case_directory(self.exp, self.case) / "fixture.patch"
        result = run(
            ["git", "apply", "--whitespace=nowarn", str(patch_path)],
            cwd=self.worktree)
        self.record["fixture"]["apply_log"] = self.save_log(
            "apply-fixture", result.stdout + result.stderr)
        if result.returncode:
            raise PipelineError(
                f"frozen-fixture-apply-failed: {result.stderr.strip()[:200]}")
        self.record["fixture"]["constructed"] = True
        add = run(["git", "add", "-A"], cwd=self.worktree)
        commit = run([
            "git", "-c", "user.name=Markdig fixture evaluator", "-c",
            "user.email=fixture-evaluator@example.invalid", "commit", "-q",
            "-m", f"fixture {self.case_id}"], cwd=self.worktree)
        if add.returncode or commit.returncode:
            raise PipelineError(
                f"fixture-commit-failed: {(add.stderr + commit.stderr).strip()[:200]}")
        self.record["fixture"]["committed"] = True

    def reset_fixture(self):
        reset = run(["git", "reset", "--hard", "-q", "HEAD"], cwd=self.worktree)
        clean = run(["git", "clean", "-qfd"], cwd=self.worktree)
        if reset.returncode or clean.returncode:
            raise PipelineError("fixture-reset-failed")

    def apply_model_patch(self, patch_path):
        self.record["model_patch"]["apply_attempted"] = True
        context_script = self.exp / "apply-patch.py"
        patch_text = patch_path.read_text()
        commands = (
            ("git-apply", ["git", "apply", "--whitespace=nowarn", str(patch_path)], None),
            ("git-apply-recount", ["git", "apply", "--whitespace=nowarn",
                                   "--recount", str(patch_path)], None),
            ("patch-fuzz", ["patch", "-p1", "--forward", "--fuzz=3",
                            "--no-backup-if-mismatch"], patch_text),
            ("context-match", [sys.executable, str(context_script), str(patch_path),
                               str(self.worktree)] + self.all_allowed, None),
        )
        for method, cmd, stdin_text in commands:
            self.reset_fixture()
            result = run(cmd, cwd=self.worktree, stdin_text=stdin_text)
            log = self.save_log(
                f"apply-model-{method}", result.stdout + result.stderr)
            self.record["model_patch"]["apply_attempts"].append({
                "method": method, "rc": result.returncode, "log": log})
            if result.returncode == 0:
                self.record["model_patch"]["apply_method"] = method
                break
        else:
            self.reset_fixture()
            return False

        changed = run(["git", "diff", "--name-only", "HEAD"], cwd=self.worktree)
        if changed.returncode:
            raise PipelineError("changed-path-enumeration-failed")
        actual_paths = [line for line in changed.stdout.splitlines() if line]
        patch_record = self.record["model_patch"]
        patch_record["actual_paths"] = actual_paths
        patch_record["effective_change"] = bool(actual_paths)
        patch_record["scope_valid"] = bool(actual_paths) and (
            set(actual_paths).issubset(set(self.all_allowed))
            and not any(path.endswith(".generated.cs") for path in actual_paths))
        decision = self.record["response"]["decision"]
        patch_record["decision_side_valid"] = (
            patch_record["scope_valid"]
            and set(actual_paths).issubset(self.side_allowed[decision]))
        if not patch_record["scope_valid"]:
            self.reset_fixture()
            return False

        applied = run(["git", "diff", "--no-color", "HEAD"], cwd=self.worktree)
        if applied.returncode:
            raise PipelineError("applied-diff-capture-failed")
        applied_path = self.output_dir / "applied-repair.diff"
        applied_path.write_text(applied.stdout)
        patch_record.update({
            "apply_succeeded": True,
            "applied_diff": str(applied_path.relative_to(self.exp)),
            "applied_diff_sha256": sha256_text(applied.stdout),
        })
        return True

    def check_preservation(self):
        fixture_patch = case_directory(self.exp, self.case) / "fixture.patch"
        result = run([
            "git", "apply", "--reverse", "--check", "--whitespace=nowarn",
            str(fixture_patch)], cwd=self.worktree)
        log = self.save_log(
            "check-recent-change-preserved", result.stdout + result.stderr)
        self.record["preservation"].update({
            "checked": True,
            "passed": result.returncode == 0,
            "rc": result.returncode,
            "log": log,
            "method": "git apply --reverse --check fixture.patch",
        })

    def build(self):
        cmd = [
            "dotnet", "build", "src/Markdig.Tests/Markdig.Tests.csproj",
            "-c", "Release", "-f", self.case["tfm"], "-v", "q"]
        result = run(
            cmd, cwd=self.worktree, env=dotnet_env(), timeout=BUILD_TIMEOUT)
        log = self.save_log(
            "build-after-model-action", result.stdout + result.stderr,
            tail=None if result.returncode == 0 else 120)
        self.record["runs"].append({
            "kind": "build", "label": "after-model-action",
            "command": " ".join(cmd), "rc": result.returncode, "log": log})
        return result.returncode == 0

    def test(self, label, test_filter=None):
        cmd = [
            "dotnet", "test", "src/Markdig.Tests/Markdig.Tests.csproj",
            "-c", "Release", "-f", self.case["tfm"], "--no-build"]
        if test_filter:
            cmd += ["--filter", test_filter]
        result = run(
            cmd, cwd=self.worktree, env=dotnet_env(), timeout=TEST_TIMEOUT)
        output = result.stdout + result.stderr
        match = SUMMARY_RE.search(output)
        if not match:
            if "No test matches" in output or "No test is available" in output:
                counts = {"failed": 0, "passed": 0, "skipped": 0, "total": 0}
            else:
                self.save_log(f"test-{label}", output, tail=160)
                raise PipelineError(f"unparseable-test-output:{label}")
        else:
            counts = dict(zip(
                ("failed", "passed", "skipped", "total"),
                map(int, match.groups())))
        failed_names = sorted(set(FAILED_NAME_RE.findall(output)))[:50]
        log = self.save_log(
            f"test-{label}", output, tail=160 if counts["failed"] else 30)
        self.record["runs"].append({
            "kind": "test", "label": label, "command": " ".join(cmd),
            "filter": test_filter, "rc": result.returncode,
            "counts": counts, "failed_tests": failed_names, "log": log})
        return counts

    def execute(self):
        response_path = case_directory(
            self.exp, self.case) / "gptoss-response.md"
        response_text = response_path.read_text()
        parsed = extract_response(response_text, self.all_allowed)
        extracted = parsed.pop("extracted_patch")
        self.record["response"] = parsed
        self.record["response"].update({
            "response_sha256": sha256_text(response_text),
            "extracted_patch_sha256": sha256_text(extracted) if extracted else None,
        })
        decision = parsed["decision"]
        self.record["decision_correct"] = (
            decision == self.record["expected_decision"])
        self.record["response_contract_valid"] = bool(
            parsed["decision_line_valid"]
            and ((decision == "no_change" and parsed["body_empty"])
                 or (decision in {"fix_tests", "fix_production"}
                     and parsed["patch_present"]
                     and parsed["header_paths_safe"]
                     and parsed["header_scope_valid"])))

        if extracted is not None:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "extracted.patch").write_text(extracted)
        if not self.record["response_contract_valid"]:
            self.record["reason"] = parsed["parse_reason"] or "response-contract-invalid"
            self.record["status"] = "evaluated"
            return

        self.create_worktree()
        try:
            self.apply_fixture()
            if extracted is not None:
                patch_path = self.output_dir / "extracted.patch"
                if not self.apply_model_patch(patch_path):
                    reason = ("model-patch-out-of-scope"
                              if self.record["model_patch"]["scope_valid"] is False
                              else "model-patch-does-not-apply")
                    self.record["reason"] = reason
                    self.record["status"] = "evaluated"
                    return

            self.check_preservation()
            if not self.build():
                self.record["reason"] = "build-failed-after-model-action"
                self.record["status"] = "evaluated"
                return

            target = None
            if self.case["category"] in {"S", "P"}:
                target = self.test(
                    "target-after-model-action", self.case["target_filter"])
            full = self.test("full-suite-after-model-action")
            target_green = (
                target is None or target["failed"] == 0 and target["total"] > 0)
            full_green = full["failed"] == 0 and full["total"] > 0
            self.record["behavior_validation_pass"] = target_green and full_green
            if decision in {"fix_tests", "fix_production"}:
                self.record["repair_success"] = bool(
                    self.record["model_patch"]["apply_succeeded"]
                    and self.record["model_patch"]["scope_valid"]
                    and self.record["behavior_validation_pass"]
                    and self.record["preservation"]["passed"])
                action_success = self.record["repair_success"]
            else:
                action_success = bool(
                    self.record["behavior_validation_pass"]
                    and self.record["preservation"]["passed"])
            self.record["strict_signal_pass"] = bool(
                self.record["decision_correct"] and action_success)

            if not self.record["behavior_validation_pass"]:
                reason = "executable-validation-failed"
            elif not self.record["preservation"]["passed"]:
                reason = "recent-change-not-preserved"
            elif not self.record["decision_correct"]:
                reason = "decision-mismatch"
            else:
                reason = "signal-pass"
            self.record["reason"] = reason
            self.record["status"] = "evaluated"
        finally:
            self.remove_worktree()


def summarize(records, manifest, protocol_commit):
    decision_matrix = defaultdict(Counter)
    category = {}
    for cat in "SPN":
        rows = [record for record in records if record["category"] == cat]
        category[cat] = {
            "cases": len(rows),
            "decision_correct": sum(row["decision_correct"] for row in rows),
            "response_contract_valid": sum(
                row["response_contract_valid"] for row in rows),
            "raw_unified_diff_conformant": sum(
                row["response"]["raw_unified_diff_conformant"] for row in rows),
            "patch_apply_succeeded": sum(
                row["model_patch"]["apply_succeeded"] for row in rows),
            "behavior_validation_pass": sum(
                row["behavior_validation_pass"] for row in rows),
            "repair_success": sum(row["repair_success"] for row in rows),
            "strict_signal_pass": sum(row["strict_signal_pass"] for row in rows),
            "pipeline_errors": sum(row["status"] == "pipeline_error" for row in rows),
        }
    for record in records:
        decision_matrix[record["expected_decision"]][
            record["response"].get("decision") or "invalid"] += 1
    fix_rows = [record for record in records
                if record["response"].get("decision") in {"fix_tests", "fix_production"}]
    apply_methods = Counter(
        row["model_patch"]["apply_method"] or "none" for row in fix_rows)
    return {
        "schema_version": 2,
        "gate": "zod-equivalent-repair-and-signal-evaluation",
        "supersedes_evaluation_commit": "14899af0e446cbd592a55d821650ebb2ad275c74",
        "fixture_freeze_commit": "887caeb67bfe637030d625dc455aaaca9584bb5a",
        "model_run_artifact_commit": "f9e96fd7d78c49433f303bdc46cea517c1c61b45",
        "evaluation_protocol_commit": protocol_commit,
        "zod_reference": {
            "commit": "53aaeb99d50a253d83f5dc18791b118c480ea8db",
            "apply_patch_sha256": "4579a1eaa70bcf5ea31cf1b1fa3c2c39ac237a1d9fbb2438394b817c395ac7ef",
            "validate_sha256": "f4190de97b2894465825acad70ed85c3446732894690c0630fc6bec4f7bc5d1b",
        },
        "model": "openai/gpt-oss-120b",
        "case_count": len(records),
        "category_counts": manifest["counts"],
        "decision_correct": sum(row["decision_correct"] for row in records),
        "response_contract_valid": sum(
            row["response_contract_valid"] for row in records),
        "raw_unified_diff_conformant": sum(
            row["response"]["raw_unified_diff_conformant"] for row in fix_rows),
        "behavior_validation_pass": sum(
            row["behavior_validation_pass"] for row in records),
        "repair_success": sum(row["repair_success"] for row in records),
        "strict_signal_pass": sum(row["strict_signal_pass"] for row in records),
        "preservation_checked": sum(
            row["preservation"]["checked"] for row in records),
        "preservation_passed": sum(
            row["preservation"]["passed"] for row in records),
        "pipeline_errors": sum(row["status"] == "pipeline_error" for row in records),
        "fix_decision_count": len(fix_rows),
        "fix_patch_apply_attempted": sum(
            row["model_patch"]["apply_attempted"] for row in fix_rows),
        "fix_patch_apply_succeeded": sum(
            row["model_patch"]["apply_succeeded"] for row in fix_rows),
        "fix_patch_scope_valid": sum(
            row["model_patch"]["scope_valid"] is True for row in fix_rows),
        "fix_patch_decision_side_valid": sum(
            row["model_patch"]["decision_side_valid"] is True for row in fix_rows),
        "apply_method_counts": dict(apply_methods),
        "decision_matrix": {
            expected: dict(predicted) for expected, predicted in decision_matrix.items()
        },
        "by_category": category,
        "mutation_testing": "excluded_by_instruction",
        "results": [{
            "case_id": row["case_id"],
            "category": row["category"],
            "expected_decision": row["expected_decision"],
            "decision": row["response"].get("decision"),
            "decision_correct": row["decision_correct"],
            "response_contract_valid": row["response_contract_valid"],
            "raw_unified_diff_conformant": row["response"]["raw_unified_diff_conformant"],
            "patch_apply_method": row["model_patch"]["apply_method"],
            "patch_apply_succeeded": row["model_patch"]["apply_succeeded"],
            "patch_scope_valid": row["model_patch"]["scope_valid"],
            "patch_decision_side_valid": row["model_patch"]["decision_side_valid"],
            "actual_paths": row["model_patch"]["actual_paths"],
            "behavior_validation_pass": row["behavior_validation_pass"],
            "preservation_passed": row["preservation"]["passed"],
            "repair_success": row["repair_success"],
            "strict_signal_pass": row["strict_signal_pass"],
            "status": row["status"],
            "reason": row["reason"],
        } for row in records],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--exp", default="experiments/test-maintenance")
    parser.add_argument("--protocol-commit", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    exp = Path(args.exp).resolve()
    output = exp / "evaluation-rerun"
    result_path = exp / "evaluation-rerun-results.json"
    if output.exists() or result_path.exists():
        raise SystemExit("refusing to overwrite existing rerun artifacts")

    manifest = load_json(exp / "cases.json")
    if manifest.get("case_count") != 23 or manifest.get("counts") != {
            "S": 3, "P": 10, "N": 10}:
        raise SystemExit("unexpected frozen fixture manifest")
    output.mkdir()
    records = []
    for case in manifest["cases"]:
        case_root = output / case["case_id"]
        final_record = None
        attempt_summaries = []
        for attempt_number in (1, 2):
            attempt_dir = case_root / f"attempt-{attempt_number}"
            evaluator = Attempt(repo, exp, case, attempt_number, attempt_dir)
            try:
                evaluator.execute()
            except PipelineError as error:
                evaluator.remove_worktree()
                evaluator.record["status"] = "pipeline_error"
                evaluator.record["reason"] = str(error)
            attempt_dir.mkdir(parents=True, exist_ok=True)
            with (attempt_dir / "record.json").open("w") as file:
                json.dump(evaluator.record, file, indent=2)
                file.write("\n")
            attempt_summaries.append({
                "attempt": attempt_number,
                "status": evaluator.record["status"],
                "reason": evaluator.record["reason"],
                "record": str((attempt_dir / "record.json").relative_to(exp)),
            })
            final_record = evaluator.record
            if evaluator.record["status"] != "pipeline_error":
                break
            print(f"{case['case_id']}: pipeline error on attempt "
                  f"{attempt_number}: {evaluator.record['reason']}", flush=True)
        final_record["attempts"] = attempt_summaries
        with (case_root / "record.json").open("w") as file:
            json.dump(final_record, file, indent=2)
            file.write("\n")
        records.append(final_record)
        print(
            f"{case['case_id']}: expected={final_record['expected_decision']} "
            f"actual={final_record['response'].get('decision')} "
            f"apply={final_record['model_patch']['apply_method']} "
            f"preserved={final_record['preservation']['passed']} "
            f"reason={final_record['reason']} "
            f"strict={final_record['strict_signal_pass']}", flush=True)

    result = summarize(records, manifest, args.protocol_commit)
    with result_path.open("w") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(
        f"EVALUATION COMPLETE decision={result['decision_correct']}/23 "
        f"applied={result['fix_patch_apply_succeeded']}/16 "
        f"strict={result['strict_signal_pass']}/23 "
        f"pipeline_errors={result['pipeline_errors']}")
    raise SystemExit(1 if result["pipeline_errors"] else 0)


if __name__ == "__main__":
    main()
