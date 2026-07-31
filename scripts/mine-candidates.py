#!/usr/bin/env python3
"""Deterministic candidate mining for the Markdig 30-case experiment.

Enumerates the frozen commit window, classifies every commit, applies the
frozen exclusion rules, assigns surviving commits to S/P/N pools, and emits
seeded, shuffled queues plus complete mining statistics.

Determinism: output depends only on the git object database at the frozen
window endpoints and the frozen seed. No timestamps, no environment data in
outputs. Run twice and diff to verify.

Usage: python3 scripts/mine-candidates.py <repo-root> <out-dir>
"""

import hashlib
import json
import os
import random
import re
import subprocess
import sys
from collections import OrderedDict

WINDOW_START = "2025-01-01"
WINDOW_END_SHA = "fc705234fa211d179ee1d5e7656b51ab99f70ca9"
SEED = "20260731"

SMOKE_SHAS = {
    "9dffce52b61068c4451399068f72cdad34f79bdb",
    "50061841a45e142192362131c9ed2ea6043f302e",
    "25506f20d96f214f951ac2d881550d8b883bf9f0",
}

MAX_PROD_FILES = 12
MAX_PROD_LINES = 600      # additions + deletions, production source
MAX_TEST_LINES = 600      # additions + deletions, test .cs source + spec .md

CATEGORIES = ("S", "P", "N")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def classify_path(path):
    """Frozen path classification."""
    if path.startswith("src/Markdig/"):
        return "prod_src" if path.endswith(".cs") else "prod_infra"
    if path.startswith("src/Markdig.Tests/"):
        if path.endswith(".generated.cs"):
            return "generated"
        if path.endswith(".md"):
            return "spec_md"
        if path.endswith(".cs"):
            return "test_src"
        return "test_infra"
    return "other"


COMMENT_RE = re.compile(r"^\s*(//|/\*|\*/|\*($|\s))")


def substantive_prod_lines(repo, parent, sha, prod_files):
    """Count added/removed prod-source lines that are not blank/comment-only."""
    if not prod_files:
        return 0
    diff = git(repo, "diff", "--no-renames", "--unified=0", parent, sha, "--", *prod_files)
    n = 0
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            body = line[1:].strip()
            if body and not COMMENT_RE.match(body):
                n += 1
    return n


def main():
    repo, out_dir = sys.argv[1], sys.argv[2]

    merges = git(repo, "rev-list", "--merges", f"--since={WINDOW_START}", WINDOW_END_SHA).split()
    shas = git(repo, "rev-list", "--no-merges", f"--since={WINDOW_START}", WINDOW_END_SHA).split()

    commits = []
    for sha in shas:  # rev-list order: newest -> oldest
        meta = git(repo, "show", "-s", "--format=%H%x00%P%x00%as%x00%s", sha).strip()
        full, parents, date, subject = meta.split("\x00")
        numstat = git(repo, "diff-tree", "-r", "--no-renames", "--numstat", "--root", sha)
        files = OrderedDict()
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) != 3 or parts[0] == full:
                continue
            a, d, path = parts
            a = 0 if a == "-" else int(a)
            d = 0 if d == "-" else int(d)
            files[path] = (a, d, classify_path(path))
        patch_id_out = subprocess.run(
            ["git", "-C", repo, "diff-tree", "-p", "--no-renames", sha],
            capture_output=True, text=True).stdout
        pid = subprocess.run(["git", "-C", repo, "patch-id", "--stable"],
                             input=patch_id_out, capture_output=True, text=True).stdout.split()
        patch_id = pid[0] if pid else ""
        prs = sorted(set(re.findall(r"#(\d+)", subject)))
        commits.append({
            "sha": full,
            "parent": parents.split()[0] if parents else "",
            "date": date,
            "subject": subject,
            "files": files,
            "patch_id": patch_id,
            "prs": prs,
        })

    def sum_class(c, cls):
        a = sum(v[0] for v in c["files"].values() if v[2] == cls)
        d = sum(v[1] for v in c["files"].values() if v[2] == cls)
        n = sum(1 for v in c["files"].values() if v[2] == cls)
        return n, a, d

    # Exclusion pass (first matching reason wins). Iterate oldest -> newest so
    # patch-id / PR-repeat rules keep the FIRST landing.
    seen_patch_ids = {}
    claimed_prs = {}
    excluded = []
    survivors = []
    for c in reversed(commits):
        pn, pa, pd = sum_class(c, "prod_src")
        tn, ta, td = sum_class(c, "test_src")
        mn, ma, md = sum_class(c, "spec_md")
        gn, _, _ = sum_class(c, "generated")
        reason = None
        if c["sha"] in SMOKE_SHAS:
            reason = "smoke-commit"
        elif pn == 0:
            reason = "no-production-source-change"
        elif gn > 0 and mn == 0:
            reason = "generated-without-spec-md"
        elif pn > MAX_PROD_FILES or (pa + pd) > MAX_PROD_LINES:
            reason = "prod-diff-too-large"
        elif (ta + td + ma + md) > MAX_TEST_LINES:
            reason = "test-diff-too-large"
        elif substantive_prod_lines(repo, c["parent"], c["sha"],
                                    [p for p, v in c["files"].items() if v[2] == "prod_src"]) == 0:
            reason = "comment-only-prod-diff"
        elif c["patch_id"] and c["patch_id"] in seen_patch_ids:
            reason = f"patch-id-duplicate-of-{seen_patch_ids[c['patch_id']][:8]}"
        else:
            hit = [p for p in c["prs"] if p in claimed_prs]
            if hit:
                reason = f"pr-repeat-{','.join('#' + p for p in hit)}-first-{claimed_prs[hit[0]][:8]}"
        if reason:
            excluded.append({"sha": c["sha"], "date": c["date"], "subject": c["subject"],
                             "reason": reason})
            continue
        if c["patch_id"]:
            seen_patch_ids.setdefault(c["patch_id"], c["sha"])
        for p in c["prs"]:
            claimed_prs.setdefault(p, c["sha"])
        test_side_add, test_side_del = ta + ma, td + md
        if test_side_add == 0 and test_side_del == 0:
            cat = "N"
        elif test_side_del > 0:
            cat = "S"
        else:
            cat = "P"
        survivors.append({
            "sha": c["sha"],
            "parent": c["parent"],
            "date": c["date"],
            "subject": c["subject"],
            "category": cat,
            "prod_src_files": [p for p, v in c["files"].items() if v[2] == "prod_src"],
            "test_src_files": [p for p, v in c["files"].items() if v[2] == "test_src"],
            "spec_md_files": [p for p, v in c["files"].items() if v[2] == "spec_md"],
            "generated_files": [p for p, v in c["files"].items() if v[2] == "generated"],
            "counts": {
                "prod": {"files": pn, "add": pa, "del": pd},
                "test_src": {"files": tn, "add": ta, "del": td},
                "spec_md": {"files": mn, "add": ma, "del": md},
                "generated_files": gn,
            },
            "prs": c["prs"],
            "patch_id": c["patch_id"],
        })

    # Restore rev-list (newest->oldest) order as the frozen pre-shuffle order.
    survivors.reverse()
    excluded.reverse()

    queues = {}
    for cat in CATEGORIES:
        pool = [s for s in survivors if s["category"] == cat]
        rng = random.Random(f"{SEED}:{cat}")
        rng.shuffle(pool)
        for i, entry in enumerate(pool, 1):
            entry["queue_id"] = f"{cat}-{i:02d}"
        queues[cat] = pool

    out = {
        "window": {"start_date": WINDOW_START, "end_sha": WINDOW_END_SHA},
        "seed": SEED,
        "thresholds": {
            "max_prod_files": MAX_PROD_FILES,
            "max_prod_lines": MAX_PROD_LINES,
            "max_test_lines": MAX_TEST_LINES,
        },
        "queues": queues,
    }
    stats = {
        "window": {"start_date": WINDOW_START, "end_sha": WINDOW_END_SHA},
        "total_commits_incl_merges": len(shas) + len(merges),
        "merge_commits_excluded": len(merges),
        "non_merge_commits": len(shas),
        "excluded": excluded,
        "excluded_count": len(excluded),
        "pool_sizes": {cat: len(queues[cat]) for cat in CATEGORIES},
    }
    with open(f"{out_dir}/screening_queues.json", "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    metadata_path = os.path.join(out_dir, "metadata", "experiment.json")
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
    else:
        metadata = {
            "schema_version": 1,
            "description": "Selection and fixture-verification provenance.",
            "selection": {"screening": {}},
        }
    metadata["selection"]["mining"] = stats
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")
    digest = hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()
    print(f"non-merge commits: {len(shas)}; merges: {len(merges)}; excluded: {len(excluded)}")
    print("pools:", {cat: len(queues[cat]) for cat in CATEGORIES})
    print(f"screening_queues.json sha256(canonical): {digest}")


if __name__ == "__main__":
    main()
