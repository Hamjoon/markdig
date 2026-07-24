#!/bin/bash
# make-fixture.sh <case-id> — build the Markdig fixture worktree for one case and capture failing output.
# Port of zod-week3-july fixture.sh (source commit 745ec751) adapted per markdig-smoke spec section 4:
# the fixture tree sits at upstream sha C with the category-appropriate side reverted.
#   S: apply stale-test.patch (reverse of C's test-side) -> new production + stale tests
#   P: apply reverse of C's production-side              -> old production + new tests
# With target_filter == "TBD" the script stops after a discovery run and prints failing test
# names so the exact NUnit FQN can be copied into cases.json (spec section 5 stage 3).
# Prints "FIXTURE: <OK|FAIL|DISCOVER> <id> <detail>" as the last line.
set -u
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)
EXP=$ROOT/experiments/markdig-smoke
ID=$1
CASEDIR=$EXP/$ID
WT=$ROOT/.worktrees/$ID
LOG=$CASEDIR/logs
TFM=net10.0
mkdir -p "$CASEDIR" "$LOG"

CASE=$(jq -c ".[] | select(.id == \"$ID\")" "$EXP/cases.json")
[ -z "$CASE" ] && { echo "FIXTURE: FAIL $ID unknown-case"; exit 1; }
CAT=$(jq -r .category <<<"$CASE")
SHA=$(jq -r .upstream_sha <<<"$CASE")
SUBJECT=$(jq -r .upstream_subject <<<"$CASE")
FILTER=$(jq -r .target_filter <<<"$CASE")
DISCOVER=$(jq -r .discover_filter <<<"$CASE")
TESTS=(); while IFS= read -r f; do [ -n "$f" ] && TESTS[${#TESTS[@]}]=$f; done < <(jq -r '.test_paths[]' <<<"$CASE")
PRODS=(); while IFS= read -r f; do [ -n "$f" ] && PRODS[${#PRODS[@]}]=$f; done < <(jq -r '.prod_paths[]' <<<"$CASE")
REVERTS=(); while IFS= read -r f; do [ -n "$f" ] && REVERTS[${#REVERTS[@]}]=$f; done < <(jq -r '.test_revert_paths[]' <<<"$CASE")

fail() { echo "FIXTURE: FAIL $ID $1"; exit 1; }

# 1. worktree at C, category-appropriate reversal, local fixture commit
if [ ! -d "$WT" ]; then
  ( cd "$ROOT" && git worktree add --detach "$WT" "$SHA" > "$LOG/worktree.log" 2>&1 ) || fail worktree-add
  cd "$WT" || fail cd-worktree
  if [ "$CAT" = "S" ]; then
    git diff --no-renames --binary "$SHA" "${SHA}^" -- "${REVERTS[@]}" > "$CASEDIR/stale-test.patch" || fail stale-diff
    [ -s "$CASEDIR/stale-test.patch" ] || fail stale-diff-empty
    git apply --whitespace=nowarn "$CASEDIR/stale-test.patch" 2> "$LOG/stale-apply.err" || fail stale-apply
    git diff --no-renames --binary "${SHA}^" "$SHA" -- "${PRODS[@]}" > "$CASEDIR/fixture.patch" || fail fixture-diff
  else
    git diff --no-renames --binary "$SHA" "${SHA}^" -- "${PRODS[@]}" > "$CASEDIR/prod-revert.patch" || fail prod-revert-diff
    [ -s "$CASEDIR/prod-revert.patch" ] || fail prod-revert-empty
    git apply --whitespace=nowarn "$CASEDIR/prod-revert.patch" 2> "$LOG/prod-revert-apply.err" || fail prod-revert-apply
    git diff --no-renames --binary "${SHA}^" "$SHA" -- "${TESTS[@]}" > "$CASEDIR/fixture.patch" || fail fixture-diff
  fi
  [ -s "$CASEDIR/fixture.patch" ] || fail fixture-patch-empty
  # sanity: the intentional change to preserve is fully present in the fixture tree
  git apply --reverse --check "$CASEDIR/fixture.patch" 2> "$LOG/fixture-check.err" || fail fixture-not-present
  git add -A > /dev/null 2>&1 && git commit -qm "fixture: $ID (upstream $SHA, category $CAT)" || fail fixture-commit
fi
cd "$WT" || fail cd-worktree

strip_ansi() { sed 's/\x1b\[[0-9;]*m//g' "$1"; }
summary_line() { strip_ansi "$1" | grep -E 'Failed:[[:space:]]*[0-9]+.*Passed:[[:space:]]*[0-9]+' | tail -1; }
count_of() { sed -n "s/.*$2:[[:space:]]*\([0-9][0-9]*\).*/\1/p" <<<"$1" | head -1; }

run_target() { # $1=logname $2=filter
  ( cd "$WT" && dotnet test src/Markdig.Tests -f $TFM --filter "FullyQualifiedName~$2" --nologo \
      > "$LOG/$1.raw.log" 2>&1 ); echo $? > "$LOG/$1.rc"
}

# 2. discovery mode: broad filter, list failing tests, stop
if [ "$FILTER" = "TBD" ]; then
  run_target discover "$DISCOVER"
  RC=$(cat "$LOG/discover.rc")
  SUM=$(summary_line "$LOG/discover.raw.log")
  echo "--- discovery run (filter ~$DISCOVER) rc=$RC summary: $SUM"
  strip_ansi "$LOG/discover.raw.log" | grep -E '^[[:space:]]+Failed [A-Za-z]' | sed 's/^[[:space:]]*//' | sort -u
  echo "FIXTURE: DISCOVER $ID copy the FQN into cases.json target_filter and re-run"
  exit 2
fi

# 3. red-state verification with the final target filter
run_target red "$FILTER"
RC=$(cat "$LOG/red.rc")
SUM=$(summary_line "$LOG/red.raw.log")
FAILED=$(count_of "$SUM" Failed)
PASSED=$(count_of "$SUM" Passed)
TOTAL=$(count_of "$SUM" Total)
[ "$RC" = "0" ] && fail "expected-red-got-green (summary: $SUM)"
[ -n "$SUM" ] || fail "no-test-summary-build-or-runner-error (rc=$RC, see logs/red.raw.log)"
[ -n "$FAILED" ] && [ "$FAILED" -gt 0 ] || fail "nonzero-exit-but-no-failed-tests (summary: $SUM)"
[ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ] || fail "filter-matched-no-tests"

strip_ansi "$LOG/red.raw.log" | tail -400 > "$CASEDIR/test-output.txt"
FIXCOMMIT=$(git rev-parse HEAD)

# 4. case.json (spec section 4: metadata + exact failing command + truncated output + file lists)
CMD="dotnet test src/Markdig.Tests -f $TFM --filter \"FullyQualifiedName~$FILTER\" --nologo"
CASE_JSON="$CASE" CMD="$CMD" FIXCOMMIT="$FIXCOMMIT" \
  python3 - "$CASEDIR" "$ID" "$FAILED" "${PASSED:-0}" "$TOTAL" <<'PYEOF'
import json, os, sys
from pathlib import Path
casedir = Path(sys.argv[1])
case = json.loads(os.environ["CASE_JSON"])
case.pop("discover_filter", None)
case.update({
    "worktree": ".worktrees/" + sys.argv[2],
    "fixture_commit": os.environ["FIXCOMMIT"],
    "failing_test_command": os.environ["CMD"],
    "failing_summary": {"failed": int(sys.argv[3]), "passed": int(sys.argv[4]), "total": int(sys.argv[5])},
    "failing_output_truncated": (casedir / "test-output.txt").read_text(),
})
(casedir / "case.json").write_text(json.dumps(case, indent=2) + "\n")
PYEOF
[ -s "$CASEDIR/case.json" ] || fail case-json-write
echo "FIXTURE: OK $ID red-confirmed failed=$FAILED passed=${PASSED:-0} total=$TOTAL commit=${FIXCOMMIT:0:8}"
