#!/usr/bin/env python3
"""Parse a v2-unified model response: extract DECISION and unified diff.

Usage: parse-response.py <response.md> <out-patch-path>
Prints one JSON line: {decision, first_line_ok, has_diff}.
"""
import json
import re
import sys
from pathlib import Path

DECISION_RE = re.compile(r"DECISION:\s*(no_change|fix_tests|fix_production)")

response = Path(sys.argv[1]).read_text()
out_patch = Path(sys.argv[2])

lines = response.splitlines()
first_nonempty = next((line.strip() for line in lines if line.strip()), "")
first_match = DECISION_RE.search(first_nonempty)
anywhere = DECISION_RE.search(response)
decision = (first_match or anywhere).group(1) if (first_match or anywhere) else "missing"

# Diff extraction: prefer fenced code blocks that look like diffs; otherwise fall
# back to everything from the first diff marker line onward.
diff_text = ""
fences = re.findall(r"```[a-zA-Z]*\n(.*?)```", response, flags=re.DOTALL)
diff_fences = [f for f in fences if re.search(r"^(diff --git|--- |\+\+\+ |@@)", f, flags=re.MULTILINE)]
if diff_fences:
    diff_text = "\n".join(f.rstrip("\n") for f in diff_fences) + "\n"
else:
    for i, line in enumerate(lines):
        if line.startswith("diff --git") or (line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ ")):
            diff_text = "\n".join(lines[i:]) + "\n"
            break

if diff_text:
    out_patch.write_text(diff_text)

print(json.dumps({
    "decision": decision,
    "first_line_ok": bool(first_match),
    "has_diff": bool(diff_text),
}))
