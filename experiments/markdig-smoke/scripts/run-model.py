#!/usr/bin/env python3
"""Single-shot gpt-oss-120b call for one Markdig smoke case (stage 1).

Port of zod-week3-july scripts/run-gptoss-test-maintenance.py (source commit
745ec751), v2-unified mode only, adapted to the Markdig substrate:
- snippet extraction targets src/**/*.cs and src/**/*.md (never *.generated.cs)
  instead of packages/zod/**/*.ts; pad/cap constants unchanged
- generated-spec cases (generated_guard) add one constraint line marking
  *.generated.cs off-limits
- intro says "C# library" instead of "TypeScript library" (logged deviation)

Artifacts written to --artifact-dir: prompt.txt, response.json (raw API body),
response-content.md (choices[0].message.content).
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

SNIPPET_PAD_LINES = 25
SNIPPET_MAX_LINES_PER_FILE = 220
DEFAULT_MODEL = "openai/gpt-oss-120b"

V2_INTRO = """You are maintaining a C# library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all."""

GENERATED_CONSTRAINT = (
    "Never modify `*.generated.cs` files: they are generated automatically from the spec "
    "`.md` files during the build and are off-limits. To change a spec test, edit the `.md` file."
)


def read_cmd(args: list[str]) -> str:
    return subprocess.check_output(args, text=True)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"missing required env var: {name}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one Markdig smoke case through OpenRouter.")
    parser.add_argument("--case", required=True)
    parser.add_argument("--cases-file", required=True)
    parser.add_argument("--repo", required=True, help="fixture worktree for snippets/hunk ranges")
    parser.add_argument("--recent-change-diff", required=True)
    parser.add_argument("--test-output", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--model", default=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL))
    return parser.parse_args()


def load_case(cases_file: str, case_id: str) -> dict:
    cases = json.loads(Path(cases_file).read_text())
    for case in cases:
        if case["id"] == case_id:
            return case
    raise SystemExit(f"case not found in {cases_file}: {case_id}")


def git_diff_hunk_ranges(repo: str, sha: str, paths: list[str], side: str) -> dict[str, list[tuple[int, int]]]:
    """Ranges touched by <sha> per file: side='old' uses pre-image lines, 'new' post-image."""
    if not paths:
        return {}
    out = read_cmd(
        ["git", "-C", repo, "diff", "--no-renames", "--unified=0", f"{sha}^", sha, "--", *paths]
    )
    ranges: dict[str, list[tuple[int, int]]] = {}
    current = None
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("@@ ") and current:
            old_part, new_part = line.split(" ")[1:3]
            spec = old_part[1:] if side == "old" else new_part[1:]
            start, _, count = spec.partition(",")
            start = int(start)
            count = int(count) if count else 1
            if count == 0:
                count = 1
            ranges.setdefault(current, []).append((start, start + count - 1))
    return ranges


def merge_padded_ranges(ranges: list[tuple[int, int]], pad: int = SNIPPET_PAD_LINES) -> list[tuple[int, int]]:
    padded = sorted((max(1, start - pad), end + pad) for start, end in ranges)
    merged: list[tuple[int, int]] = []
    for start, end in padded:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def extract_snippets(repo: str, sha: str, paths: list[str], side: str) -> list[tuple[str, str, str]]:
    """Returns (path, range_label, text) per snippet; Markdig sources and spec .md only."""
    snippet_paths = [
        p for p in paths
        if p.startswith("src/") and (p.endswith(".cs") or p.endswith(".md"))
        and not p.endswith(".generated.cs")
    ]
    per_file = git_diff_hunk_ranges(repo, sha, snippet_paths, side)
    snippets = []
    for path in snippet_paths:
        if path not in per_file or not Path(repo, path).exists():
            continue
        budget = SNIPPET_MAX_LINES_PER_FILE
        for start, end in merge_padded_ranges(per_file[path]):
            if budget <= 0:
                break
            end = min(end, start + budget - 1)
            budget -= end - start + 1
            text = read_cmd(["sed", "-n", f"{start},{end}p", str(Path(repo, path))])
            snippets.append((path, f"{start}-{end}", text))
    return snippets


def build_prompt_v2(case: dict, recent_change: str, test_output: str, repo: str) -> str:
    category = case["category"]
    test_paths = case.get("test_paths", [])
    prod_paths = case.get("prod_paths", [])
    sha = case["upstream_sha"]
    # Snippets reflect the fixture state: applied sides use post-image line numbers,
    # untouched (base) sides use pre-image line numbers.
    test_side = {"S": "old", "P": "new", "N": None}[category]
    prod_side = {"S": "new", "P": "old", "N": "new"}[category]
    test_snippets = extract_snippets(repo, sha, test_paths, test_side) if test_side else []
    prod_snippets = extract_snippets(repo, sha, prod_paths, prod_side)

    constraints = [
        "The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.",
        "If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.",
        f"Allowed files: {', '.join(test_paths + prod_paths)}.",
        "Do not weaken, delete, or skip assertions.",
        "Preserve nearby behavior that is still expected to pass.",
    ]
    if case.get("generated_guard"):
        constraints.insert(3, GENERATED_CONSTRAINT)
    constraint_text = "\n".join(f"- {constraint}" for constraint in constraints)

    sections = [
        V2_INTRO,
        f"Constraints:\n{constraint_text}",
        f"Recent change applied to the repository:\n<recent_change_diff>\n{recent_change}\n</recent_change_diff>",
        f"Current test results:\n<test_output>\n{test_output}\n</test_output>",
    ]
    for path, lines, text in test_snippets:
        sections.append(f'Relevant test snippet:\n<test_snippet path="{path}" lines="{lines}">\n{text}</test_snippet>')
    for path, lines, text in prod_snippets:
        sections.append(
            f'Relevant production snippet:\n<production_snippet path="{path}" lines="{lines}">\n{text}</production_snippet>'
        )
    return "\n\n".join(sections) + "\n"


def main() -> int:
    args = parse_args()
    api_key = require_env("OPENROUTER_API_KEY")

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    case = load_case(args.cases_file, args.case)
    recent_change_path = Path(args.recent_change_diff)
    test_output_path = Path(args.test_output)
    for path in (recent_change_path, test_output_path):
        if not path.exists():
            raise SystemExit(f"input not found: {path}")
    prompt = build_prompt_v2(
        case,
        recent_change_path.read_text(),
        test_output_path.read_text(),
        args.repo,
    )
    (artifact_dir / "prompt.txt").write_text(prompt)

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local-thesis-experiment",
            "X-Title": "markdig-maintenance-smoke",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=600) as response:
        raw = response.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # long-poll responses may carry keep-alive comment lines around the JSON body
        text = raw.decode("utf-8", errors="replace")
        stripped = "\n".join(line for line in text.splitlines() if not line.startswith(":")).strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            (artifact_dir / "raw-response.txt").write_text(text)
            raise SystemExit(f"unparseable API response; raw body saved to {artifact_dir / 'raw-response.txt'}")

    (artifact_dir / "response.json").write_text(json.dumps(data, indent=2) + "\n")
    if "choices" not in data or not data["choices"]:
        raise SystemExit(f"API response has no choices (see response.json): {str(data)[:200]}")
    content = data["choices"][0]["message"]["content"]
    (artifact_dir / "response-content.md").write_text(content)

    print(json.dumps({"model": data.get("model"), "usage": data.get("usage", {})}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
