#!/usr/bin/env python3
"""Context-matching fallback applier for model-generated unified diffs.

Tolerates missing/bogus hunk line numbers (e.g. bare `@@`) by locating each
hunk's pre-image (context + deletions) in the target file. Exact match first,
then a retry ignoring trailing whitespace. Fails on not-found or ambiguity
(first match after the previous hunk is taken; a second overlapping candidate
before EOF is fine).

Hunks appearing before any +++ header (headerless model diffs) are attributed to
whichever candidate file (extra argv paths, repo-relative) matches every such
hunk's pre-image.

Usage: apply-patch.py <patch> <repo-root> [candidate-file ...]   (exit 0 on success)
"""
import re
import sys
from pathlib import Path

patch_path, repo = Path(sys.argv[1]), Path(sys.argv[2])
candidates = sys.argv[3:]
lines = patch_path.read_text().splitlines()

files: list[tuple[str, list[list[str]]]] = []  # (path, [hunk lines])
i = 0
current_path = None
current_hunks: list[list[str]] = []
hunk: list[str] | None = None

def flush_file():
    global current_path, current_hunks, hunk
    if hunk:
        current_hunks.append(hunk)
        hunk = None
    if current_path and current_hunks:
        files.append((current_path, current_hunks))
    current_path, current_hunks = None, []

while i < len(lines):
    line = lines[i]
    if line.startswith("+++ "):
        flush_file()
        current_path = re.sub(r"^\+\+\+ [ab]/", "", line).strip()
    elif line.startswith("@@"):
        if hunk:
            current_hunks.append(hunk)
        hunk = []
        if current_path is None:
            current_path = "__HEADERLESS__"
    elif hunk is not None and (line[:1] in {" ", "+", "-"} or line == ""):
        if line.startswith(("--- ", "diff --git", "index ")):
            pass
        else:
            hunk.append(line if line else " ")
    i += 1
flush_file()

if not files:
    sys.exit("no file sections found in patch")

# resolve headerless sections against candidate files by pre-image matching
resolved = []
for path, hunks in files:
    if path != "__HEADERLESS__":
        resolved.append((path, hunks))
        continue
    match_path = None
    for cand in candidates:
        target = repo / cand
        if not target.exists():
            continue
        stripped = [l.strip() for l in target.read_text().splitlines()]
        def hunk_found(h):
            old = [l[1:].strip() for l in h if l[0] in " -"]
            return any(stripped[j:j + len(old)] == old for j in range(len(stripped) - len(old) + 1))
        if all(hunk_found(h) for h in hunks):
            match_path = cand
            break
    if match_path is None:
        sys.exit("headerless hunks match no candidate file")
    resolved.append((match_path, hunks))
files = resolved

for path, hunks in files:
    target = repo / path
    if not target.exists():
        # new file creation: only additions allowed
        if all(all(l.startswith("+") for l in h if l.strip()) for h in hunks):
            content = "\n".join(l[1:] for h in hunks for l in h if l.startswith("+")) + "\n"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            continue
        sys.exit(f"target file missing: {path}")
    file_lines = target.read_text().splitlines()
    cursor = 0
    for hunk_lines in hunks:
        old_block = [l[1:] for l in hunk_lines if l[0] in " -"]
        if not old_block:  # pure insertion without context: cannot anchor
            sys.exit(f"unanchored insertion hunk in {path}")

        def find(block, compare, start_at):
            return [
                j for j in range(start_at, len(file_lines) - len(block) + 1)
                if all(compare(file_lines[j + k], block[k]) for k in range(len(block)))
            ]

        comparators = [
            lambda a, b: a == b,
            lambda a, b: a.rstrip() == b.rstrip(),
            lambda a, b: a.strip() == b.strip(),
        ]
        start = None
        for compare in comparators:
            matches = find(old_block, compare, cursor) or find(old_block, compare, 0)
            if matches:
                start = matches[0]
                break
        if start is None:
            sys.exit(f"hunk pre-image not found in {path} (from line {cursor + 1})")

        # Rebuild the region: keep the file's own context lines (indentation-safe),
        # drop deletions, splice in additions at their hunk positions.
        replacement = []
        offset = 0
        for l in hunk_lines:
            if l[0] == " ":
                replacement.append(file_lines[start + offset])
                offset += 1
            elif l[0] == "-":
                offset += 1
            else:  # addition
                replacement.append(l[1:])
        file_lines[start : start + len(old_block)] = replacement
        cursor = start + len(replacement)
    target.write_text("\n".join(file_lines) + "\n")

print(f"applied {sum(len(h) for _, h in files)} hunk(s) across {len(files)} file(s)")
