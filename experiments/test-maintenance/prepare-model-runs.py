#!/usr/bin/env python3
"""Prepare immutable GPT-OSS inputs for all frozen Markdig fixtures."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0
SNIPPET_PAD_LINES = 25
SNIPPET_MAX_LINES_PER_FILE = 220

INTRO = """You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all."""


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def load_json(path):
    with path.open() as f:
        return json.load(f)


def hunk_ranges(repo, base, upstream, paths, side):
    if not paths:
        return {}
    diff = git(repo, "diff", "--no-renames", "--unified=0", base, upstream,
               "--", *paths)
    ranges = {}
    old_path = None
    new_path = None
    for line in diff.splitlines():
        if line.startswith("--- a/"):
            old_path = line[6:]
        elif line.startswith("--- /dev/null"):
            old_path = None
        elif line.startswith("+++ b/"):
            new_path = line[6:]
        elif line.startswith("+++ /dev/null"):
            new_path = None
        elif line.startswith("@@ "):
            old_spec, new_spec = line.split(" ")[1:3]
            spec = old_spec[1:] if side == "old" else new_spec[1:]
            path = old_path if side == "old" else new_path
            if not path:
                continue
            start_text, separator, count_text = spec.partition(",")
            start = int(start_text)
            count = int(count_text) if separator else 1
            if count == 0:
                count = 1
            ranges.setdefault(path, []).append((start, start + count - 1))
    return ranges


def merge_padded(ranges):
    padded = sorted(
        (max(1, start - SNIPPET_PAD_LINES), end + SNIPPET_PAD_LINES)
        for start, end in ranges)
    merged = []
    for start, end in padded:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def revision_lines(repo, revision, path):
    content = git(repo, "show", f"{revision}:{path}")
    return content.splitlines()


def extract_snippets(repo, base, upstream, paths, side, revision):
    per_file = hunk_ranges(repo, base, upstream, paths, side)
    snippets = []
    for path in paths:
        if path not in per_file:
            continue
        try:
            lines = revision_lines(repo, revision, path)
        except RuntimeError:
            continue
        remaining = SNIPPET_MAX_LINES_PER_FILE
        for start, end in merge_padded(per_file[path]):
            if remaining <= 0:
                break
            end = min(end, len(lines), start + remaining - 1)
            if end < start:
                continue
            remaining -= end - start + 1
            text = "\n".join(lines[start - 1:end]) + "\n"
            snippets.append((path, f"{start}-{end}", text))
    return snippets


def build_prompt(case, fixture_diff, test_output, test_snippets, prod_snippets):
    allowed = case["test_src_files"] + case["spec_md_files"] + case["prod_src_files"]
    constraints = [
        "The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.",
        "If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.",
        f"Allowed files: {', '.join(allowed)}.",
        "Do not weaken, delete, or skip assertions.",
        "Preserve nearby behavior that is still expected to pass.",
    ]
    sections = [
        INTRO,
        "Constraints:\n" + "\n".join(f"- {item}" for item in constraints),
        "Recent change applied to the repository:\n"
        f"<recent_change_diff>\n{fixture_diff}</recent_change_diff>",
        "Current test results:\n"
        f"<test_output>\n{test_output}</test_output>",
    ]
    for path, line_range, text in test_snippets:
        sections.append(
            f'<test_snippet path="{path}" lines="{line_range}">\n'
            f"{text}</test_snippet>")
    for path, line_range, text in prod_snippets:
        sections.append(
            f'<production_snippet path="{path}" lines="{line_range}">\n'
            f"{text}</production_snippet>")
    return "\n\n".join(sections) + "\n"


def test_log_path(exp, case_id, category):
    label = {
        "S": "05-test-stale-target.txt",
        "P": "04-test-oracle-target.txt",
        "N": "04-test-changed-full-suite.txt",
    }[category]
    return exp / "verification" / case_id / "logs" / label


def prepare_case(repo, exp, output_root, case):
    case_id = case["case_id"]
    category = case["category"]
    archive_case_id = case.get("archive_case_id") or (
        case_id.lower().replace("-", "") + "-" + case["upstream_sha"][:8])
    case_dir = output_root / archive_case_id
    case_dir.mkdir(parents=True)

    test_paths = case["test_src_files"] + case["spec_md_files"]
    prod_paths = case["prod_src_files"]
    fixture_paths = prod_paths if category in {"S", "N"} else test_paths
    fixture_diff = git(
        repo, "diff", "--no-renames", "--binary", case["base_sha"],
        case["upstream_sha"], "--", *fixture_paths)
    if not fixture_diff.strip():
        raise RuntimeError(f"{case_id}: empty fixture diff")

    frozen_test_log = test_log_path(exp, case_id, category)
    if not frozen_test_log.is_file():
        raise RuntimeError(f"{case_id}: missing frozen test output {frozen_test_log}")
    test_output = frozen_test_log.read_text()

    test_snippets = []
    if category == "S":
        test_snippets = extract_snippets(
            repo, case["base_sha"], case["upstream_sha"], test_paths,
            "old", case["base_sha"])
    elif category == "P":
        test_snippets = extract_snippets(
            repo, case["base_sha"], case["upstream_sha"], test_paths,
            "new", case["upstream_sha"])

    prod_side = "new" if category in {"S", "N"} else "old"
    prod_revision = case["upstream_sha"] if category in {"S", "N"} else case["base_sha"]
    prod_snippets = extract_snippets(
        repo, case["base_sha"], case["upstream_sha"], prod_paths,
        prod_side, prod_revision)
    if not prod_snippets:
        raise RuntimeError(f"{case_id}: no production snippet extracted")

    prompt = build_prompt(
        case, fixture_diff, test_output, test_snippets, prod_snippets)
    (case_dir / "fixture.patch").write_text(fixture_diff)
    (case_dir / "test-output.txt").write_text(test_output)
    (case_dir / "gptoss-prompt.md").write_text(prompt)

    metadata = {
        "case_id": case_id,
        "category": category,
        "base_sha": case["base_sha"],
        "upstream_sha": case["upstream_sha"],
        "model": MODEL,
        "temperature": TEMPERATURE,
        "allowed_files": test_paths + prod_paths,
        "fixture_paths": fixture_paths,
        "test_revision": (
            case["base_sha"] if category == "S"
            else case["upstream_sha"] if category == "P" else None),
        "production_revision": prod_revision,
        "prompt_sha256": sha256_text(prompt),
        "fixture_patch_sha256": sha256_text(fixture_diff),
        "test_output_sha256": sha256_text(test_output),
        "prompt_characters": len(prompt),
    }
    with (case_dir / "input.json").open("w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--exp", default="experiments/test-maintenance")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    exp = Path(args.exp).resolve()
    output_root = exp / "cases"
    if output_root.exists():
        raise SystemExit(f"refusing to overwrite existing model-run inputs: {output_root}")

    manifest = load_json(exp / "cases.json")
    if manifest.get("case_count") != 23 or manifest.get("counts") != {
            "S": 3, "P": 10, "N": 10}:
        raise SystemExit("unexpected frozen fixture manifest")

    output_root.mkdir()
    prepared = [prepare_case(repo, exp, output_root, case)
                for case in manifest["cases"]]
    print(f"prepared {len(prepared)} frozen GPT-OSS inputs")


if __name__ == "__main__":
    main()
