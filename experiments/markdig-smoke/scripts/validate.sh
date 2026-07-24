#!/bin/bash
# validate.sh <case-id> — stage 3 (failing -> passing) + stage 4 (preservation), combined verdict.
# Stage 3: focused dotnet test run (-f net10.0). target_pass requires exit 0, a parsed test
#          summary with Failed=0 and Total>0 (guards against filter-matched-nothing greens).
# Stage 3 smoke-3 extra: generated-file invariant — the model's diff must go through the spec
#          .md; the .generated.cs change must be explainable by regeneration alone
#          (checkout the .generated.cs, touch the .md, rebuild, compare content hashes).
# Stage 4: git apply --reverse --check fixture.patch — runs on EVERY case (spec section 7.3).
# Writes validate.log and verdicts.json. Prints "VALIDATE: ..." as the last line.
set -u
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)
EXP=$ROOT/experiments/markdig-smoke
ID=$1
CASEDIR=$EXP/$ID
WT=$ROOT/.worktrees/$ID
LOG=$CASEDIR/logs
TFM=net10.0
mkdir -p "$LOG"

CASE=$(jq -c ".[] | select(.id == \"$ID\")" "$EXP/cases.json")
[ -z "$CASE" ] && { echo "VALIDATE: FAIL $ID unknown-case"; exit 1; }
CAT=$(jq -r .category <<<"$CASE")
FILTER=$(jq -r .target_filter <<<"$CASE")
GENGUARD=$(jq -r .generated_guard <<<"$CASE")
GENFILES=(); while IFS= read -r f; do [ -n "$f" ] && GENFILES[${#GENFILES[@]}]=$f; done < <(jq -r '.generated_files[]' <<<"$CASE")
MDFILES=(); while IFS= read -r f; do [ -n "$f" ] && MDFILES[${#MDFILES[@]}]=$f; done < <(jq -r '.test_paths[]' <<<"$CASE")
DECISION=$(jq -r '.decision // "missing"' "$CASEDIR/decision.json" 2>/dev/null || echo missing)
DMATCH=$(jq -r '.decision_match // false' "$CASEDIR/decision.json" 2>/dev/null || echo false)
APPLIED=$(grep -q '^APPLY: OK' "$CASEDIR/apply.log" 2>/dev/null && echo true || echo false)
APPLY_STATUS=$(head -1 "$CASEDIR/apply.log" 2>/dev/null || echo "APPLY: MISSING")

cd "$WT" || { echo "VALIDATE: FAIL $ID missing-worktree"; exit 1; }
: > "$CASEDIR/validate.log"
vlog() { echo "$1" >> "$CASEDIR/validate.log"; }
strip_ansi() { sed 's/\x1b\[[0-9;]*m//g' "$1"; }
summary_line() { strip_ansi "$1" | grep -E 'Failed:[[:space:]]*[0-9]+.*Passed:[[:space:]]*[0-9]+' | tail -1; }
count_of() { sed -n "s/.*$2:[[:space:]]*\([0-9][0-9]*\).*/\1/p" <<<"$1" | head -1; }

vlog "=== stage 3: validation run $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
vlog "case=$ID category=$CAT decision=$DECISION applied=$APPLIED ($APPLY_STATUS)"
CMD="dotnet test src/Markdig.Tests -f $TFM --filter \"FullyQualifiedName~$FILTER\" --nologo"
vlog "command: $CMD"
( dotnet test src/Markdig.Tests -f $TFM --filter "FullyQualifiedName~$FILTER" --nologo \
    > "$LOG/validate.raw.log" 2>&1 ); RC=$?
SUM=$(summary_line "$LOG/validate.raw.log")
FAILED=$(count_of "$SUM" Failed); PASSED=$(count_of "$SUM" Passed); TOTAL=$(count_of "$SUM" Total)
strip_ansi "$LOG/validate.raw.log" | tail -400 >> "$CASEDIR/validate.log"
vlog "rc=$RC summary: ${SUM:-none}"

BUILD_OK=true
if [ -z "$SUM" ]; then
  BUILD_OK=false
  TARGET_PASS=false
elif [ "$RC" = "0" ] && [ "${FAILED:-1}" = "0" ] && [ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
  TARGET_PASS=true
else
  TARGET_PASS=false
fi
vlog "target_pass=$TARGET_PASS build_ok=$BUILD_OK failed=${FAILED:-?} passed=${PASSED:-?} total=${TOTAL:-?}"

# stage 3 extra (generated-spec cases): verify the model did not bypass the spec layer
GENINV=null
if [ "$GENGUARD" = "true" ] && [ "$APPLIED" = "true" ]; then
  vlog "=== stage 3 extra: generated-file invariant ==="
  CHANGED=$(git diff --name-only)
  vlog "changed files vs fixture commit:"; git diff --name-only >> "$CASEDIR/validate.log"
  MD_CHANGED=false
  for f in "${MDFILES[@]}"; do grep -qx "$f" <<<"$CHANGED" && MD_CHANGED=true; done
  GENINV=true
  [ "$MD_CHANGED" = "true" ] || { GENINV=false; vlog "invariant FAIL: no spec .md changed"; }
  for g in "${GENFILES[@]}"; do
    H1=$(shasum -a 256 "$g" | cut -d' ' -f1)
    git checkout -- "$g"
    for f in "${MDFILES[@]}"; do touch "$f"; done
    ( dotnet build src/Markdig.Tests -f $TFM --nologo > "$LOG/geninv-rebuild.raw.log" 2>&1 ) || \
      vlog "invariant rebuild rc=$? (see logs/geninv-rebuild.raw.log)"
    H2=$(shasum -a 256 "$g" | cut -d' ' -f1)
    if [ "$H1" = "$H2" ]; then
      vlog "invariant OK: $g regenerated identically from the .md (sha256 $H1)"
    else
      GENINV=false
      vlog "invariant FAIL: $g content not explainable by regeneration ($H1 != $H2)"
    fi
  done
elif [ "$GENGUARD" = "true" ]; then
  vlog "=== stage 3 extra: generated-file invariant: not-applicable (no patch applied) ==="
fi

# stage 4 — preservation check (every case, unconditionally)
vlog "=== stage 4: preservation check ==="
vlog "command: git apply --reverse --check $CASEDIR/fixture.patch"
if git apply --reverse --check "$CASEDIR/fixture.patch" 2> "$LOG/preserve.err"; then
  PRESERVE=true
  vlog "preservation_pass=true (intentional change fully present)"
else
  PRESERVE=false
  vlog "preservation_pass=false: $(head -3 "$LOG/preserve.err" | tr '\n' ' ')"
fi

REPAIR=false
if [ "$TARGET_PASS" = "true" ] && [ "$PRESERVE" = "true" ]; then
  REPAIR=true
  [ "$GENINV" = "false" ] && REPAIR=false   # spec 5.3: green must come through the .md layer
fi
vlog "repair_success=$REPAIR"

jq -n --arg id "$ID" --arg cat "$CAT" --arg decision "$DECISION" \
  --argjson decision_match "$DMATCH" --argjson applied "$APPLIED" \
  --argjson target_pass "$TARGET_PASS" --argjson build_ok "$BUILD_OK" \
  --argjson preservation_pass "$PRESERVE" --argjson generated_invariant "$GENINV" \
  --argjson repair_success "$REPAIR" \
  --arg summary "${SUM:-none}" --arg apply_status "$APPLY_STATUS" \
  '{id: $id, category: $cat, decision: $decision, decision_match: $decision_match,
    stage2_applied: $applied, apply_status: $apply_status,
    target_pass: $target_pass, build_ok: $build_ok,
    preservation_pass: $preservation_pass, generated_invariant: $generated_invariant,
    repair_success: (if $repair_success then "yes" else "no" end),
    pipeline_error: false, test_summary: $summary}' > "$CASEDIR/verdicts.json"

echo "VALIDATE: $ID target_pass=$TARGET_PASS preservation_pass=$PRESERVE generated_invariant=$GENINV repair_success=$REPAIR"
