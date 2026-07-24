#!/usr/bin/env python3
"""Locate per-file line coverage in a cobertura XML (stage 5 signal).

Usage: parse-cobertura.py <cobertura.xml> <repo-relative-file> [...]
For each target file, aggregates <line> entries across all matching <class>
elements (filename matched by path suffix, separators normalized) and prints a
JSON list of {file, lines_covered, lines_valid, covered} to stdout.
A target with no entry in the report gets lines 0/0 and covered=false.
"""
import json
import sys
import xml.etree.ElementTree as ET

xml_path, targets = sys.argv[1], sys.argv[2:]
if not targets:
    sys.exit("usage: parse-cobertura.py <cobertura.xml> <file> [...]")

root = ET.parse(xml_path).getroot()

def norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("/")

# file -> {line_number: max_hits}
per_file: dict[str, dict[int, int]] = {}
for cls in root.iter("class"):
    fname = norm(cls.get("filename", ""))
    for line in cls.iter("line"):
        num = int(line.get("number", 0))
        hits = int(float(line.get("hits", 0)))
        bucket = per_file.setdefault(fname, {})
        bucket[num] = max(bucket.get(num, 0), hits)

results = []
for target in targets:
    t = norm(target)
    matched = {}
    for fname, lines in per_file.items():
        if fname == t or fname.endswith("/" + t) or t.endswith("/" + fname):
            for num, hits in lines.items():
                matched[num] = max(matched.get(num, 0), hits)
    covered_lines = sum(1 for h in matched.values() if h > 0)
    results.append({
        "file": target,
        "lines_covered": covered_lines,
        "lines_valid": len(matched),
        "covered": covered_lines > 0,
    })

print(json.dumps(results, indent=2))
