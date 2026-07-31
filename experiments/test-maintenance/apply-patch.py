#!/usr/bin/env python3
"""Apply model-generated diff hunks by matching their pre-images.

This is a safety-hardened Markdig adaptation of zod Week 4's
``experiments/test-maintenance/apply-patch.py``. It deliberately tolerates
bare or inaccurate hunk coordinates and headerless sections, while restricting
every resolved target to the frozen per-case candidate list.
"""

import re
import sys
from pathlib import Path


def fail(message):
    raise SystemExit(message)


def safe_relative(value):
    value = re.sub(r"^[ab]/", "", value.strip())
    path = Path(value)
    if (not value or value == "/dev/null" or path.is_absolute()
            or ".." in path.parts):
        fail(f"unsafe target path: {value}")
    return value


def parse_sections(lines):
    files = []
    current_path = None
    current_hunks = []
    hunk = None

    def flush_file():
        nonlocal current_path, current_hunks, hunk
        if hunk:
            current_hunks.append(hunk)
            hunk = None
        if current_path and current_hunks:
            files.append((current_path, current_hunks))
        current_path, current_hunks = None, []

    for line in lines:
        if line.startswith("+++ "):
            flush_file()
            current_path = safe_relative(line[4:])
        elif line.startswith("@@"):
            if hunk:
                current_hunks.append(hunk)
            hunk = []
            if current_path is None:
                current_path = "__HEADERLESS__"
        elif hunk is not None and (line[:1] in {" ", "+", "-"} or line == ""):
            if not line.startswith(("--- ", "diff --git", "index ")):
                hunk.append(line if line else " ")
    flush_file()
    if not files:
        fail("no file sections found in patch")
    return files


def resolve_headerless(files, repo, candidates):
    resolved = []
    for path, hunks in files:
        if path != "__HEADERLESS__":
            if path not in candidates:
                fail(f"explicit target is outside candidate list: {path}")
            resolved.append((path, hunks))
            continue

        match_path = None
        for candidate in candidates:
            target = repo / candidate
            if not target.is_file():
                continue
            stripped = [line.strip() for line in target.read_text().splitlines()]

            def hunk_found(hunk):
                old = [line[1:].strip() for line in hunk
                       if line and line[0] in " -"]
                return bool(old) and any(
                    stripped[index:index + len(old)] == old
                    for index in range(len(stripped) - len(old) + 1))

            if all(hunk_found(hunk) for hunk in hunks):
                match_path = candidate
                break
        if match_path is None:
            fail("headerless hunks match no candidate file")
        resolved.append((match_path, hunks))
    return resolved


def apply_files(files, repo):
    for path, hunks in files:
        target = repo / path
        if not target.exists():
            if all(all(line.startswith("+") for line in hunk if line.strip())
                   for hunk in hunks):
                content = "\n".join(
                    line[1:] for hunk in hunks for line in hunk
                    if line.startswith("+")) + "\n"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
                continue
            fail(f"target file missing: {path}")

        file_lines = target.read_text().splitlines()
        cursor = 0
        for hunk_lines in hunks:
            old_block = [line[1:] for line in hunk_lines
                         if line and line[0] in " -"]
            if not old_block:
                fail(f"unanchored insertion hunk in {path}")

            def find(block, compare, start_at):
                return [
                    index for index in range(
                        start_at, len(file_lines) - len(block) + 1)
                    if all(compare(file_lines[index + offset], block[offset])
                           for offset in range(len(block)))
                ]

            comparators = (
                lambda left, right: left == right,
                lambda left, right: left.rstrip() == right.rstrip(),
                lambda left, right: left.strip() == right.strip(),
            )
            start = None
            for compare in comparators:
                matches = (find(old_block, compare, cursor)
                           or find(old_block, compare, 0))
                if matches:
                    start = matches[0]
                    break
            if start is None:
                fail(f"hunk pre-image not found in {path} "
                     f"(from line {cursor + 1})")

            replacement = []
            offset = 0
            for line in hunk_lines:
                if line[0] == " ":
                    replacement.append(file_lines[start + offset])
                    offset += 1
                elif line[0] == "-":
                    offset += 1
                else:
                    replacement.append(line[1:])
            file_lines[start:start + len(old_block)] = replacement
            cursor = start + len(replacement)
        target.write_text("\n".join(file_lines) + "\n")


def main():
    if len(sys.argv) < 4:
        fail("usage: context_apply.py <patch> <repo-root> <candidate-file ...>")
    patch_path = Path(sys.argv[1])
    repo = Path(sys.argv[2]).resolve()
    candidates = list(dict.fromkeys(safe_relative(item) for item in sys.argv[3:]))
    files = parse_sections(patch_path.read_text().splitlines())
    files = resolve_headerless(files, repo, candidates)
    apply_files(files, repo)
    print(f"applied {sum(len(hunks) for _, hunks in files)} hunk(s) "
          f"across {len(files)} file(s)")


if __name__ == "__main__":
    main()
