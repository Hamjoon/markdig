#!/bin/bash
# run-case.sh <case-id> — stages 1–2 for one Markdig smoke case.
# Stage 1: render prompt (run-model.py), single gpt-oss-120b call via OpenRouter (temp 0, no
#          retries), parse DECISION + diff (parse-response.py), write decision.json.
# Stage 2: generated-file guard, then apply model-patch.diff in the fixture worktree using the
#          Zod v2 escalation chain (git apply -> --recount -> patch --fuzz=3 -> apply-patch.py).
# API key is injected from the keychain at call time only; never written anywhere.
# Prints "MODEL: ..." and "APPLY: ..." lines; apply.log records stage 2.
set -u
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)
EXP=$ROOT/experiments/markdig-smoke
ID=$1
CASEDIR=$EXP/$ID
WT=$ROOT/.worktrees/$ID
LOG=$CASEDIR/logs
mkdir -p "$LOG"

CASE=$(jq -c ".[] | select(.id == \"$ID\")" "$EXP/cases.json")
[ -z "$CASE" ] && { echo "RUN: FAIL $ID unknown-case"; exit 1; }
CAT=$(jq -r .category <<<"$CASE")
case "$CAT" in S) EXPECTED=fix_tests ;; P) EXPECTED=fix_production ;; *) EXPECTED=no_change ;; esac

[ -s "$CASEDIR/fixture.patch" ] && [ -s "$CASEDIR/test-output.txt" ] && [ -d "$WT" ] \
  || { echo "MODEL: FAIL $ID missing-fixture-inputs"; exit 1; }

# stage 1 — single model request (no retries; validation output is never fed back)
if [ ! -s "$CASEDIR/response.json" ]; then
  if OPENROUTER_API_KEY=$(security find-generic-password -s openrouter-api-key -w) \
    python3 "$SCRIPT_DIR/run-model.py" \
      --case "$ID" \
      --cases-file "$EXP/cases.json" \
      --repo "$WT" \
      --recent-change-diff "$CASEDIR/fixture.patch" \
      --test-output "$CASEDIR/test-output.txt" \
      --artifact-dir "$CASEDIR" > "$LOG/model-call.out" 2> "$CASEDIR/run.err"; then
    rm -f "$CASEDIR/run.err"
  else
    echo "MODEL: FAIL $ID api-error $(tail -1 "$CASEDIR/run.err" | head -c 120)"
    exit 1
  fi
else
  echo "MODEL: SKIP $ID response.json already exists (one request per case)"
fi

PARSED=$(python3 "$SCRIPT_DIR/parse-response.py" "$CASEDIR/response-content.md" "$CASEDIR/model-patch.diff")
DECISION=$(jq -r .decision <<<"$PARSED")
FIRSTOK=$(jq -r .first_line_ok <<<"$PARSED")
HASDIFF=$(jq -r .has_diff <<<"$PARSED")
MATCH=$([ "$DECISION" = "$EXPECTED" ] && echo true || echo false)
jq -n --arg id "$ID" --arg cat "$CAT" --arg expected "$EXPECTED" --arg decision "$DECISION" \
  --argjson first_line_ok "$FIRSTOK" --argjson has_diff "$HASDIFF" --argjson decision_match "$MATCH" \
  --argjson model_info "$(jq -c '{model, usage}' "$CASEDIR/response.json")" \
  '{id: $id, category: $cat, expected: $expected, decision: $decision, decision_match: $decision_match,
    first_line_ok: $first_line_ok, has_diff: $has_diff} + $model_info' > "$CASEDIR/decision.json"
echo "MODEL: OK $ID decision=$DECISION expected=$EXPECTED match=$MATCH has_diff=$HASDIFF"

# stage 2 — patch application
: > "$CASEDIR/apply.log"
alog() { echo "$1" | tee -a "$CASEDIR/apply.log"; }

if [ "$HASDIFF" = "false" ]; then
  rm -f "$CASEDIR/model-patch.diff"
  alog "APPLY: NONE $ID no-diff-in-response (decision=$DECISION)"
  exit 0
fi

# driver pre-check (spec section 5 stage 2): any *.generated.cs path in the model patch fails the stage
if grep -E '^(\+\+\+ |--- |diff --git )' "$CASEDIR/model-patch.diff" | grep -q '\.generated\.cs'; then
  alog "APPLY: FAILED $ID reason=generated-file-edit"
  exit 0
fi

cd "$WT" || { alog "APPLY: FAILED $ID missing-worktree"; exit 1; }
reset_fixture() { git reset --hard -q HEAD; git clean -qfd; }
reset_fixture   # start from the committed fixture state
METHOD=none
if git apply --whitespace=nowarn "$CASEDIR/model-patch.diff" 2> "$LOG/repair-apply.err"; then
  METHOD=git-apply
else
  reset_fixture
  if git apply --whitespace=nowarn --recount "$CASEDIR/model-patch.diff" 2>> "$LOG/repair-apply.err"; then
    METHOD=git-apply-recount
  else
    reset_fixture
    if patch -p1 --forward --fuzz=3 --no-backup-if-mismatch < "$CASEDIR/model-patch.diff" > "$LOG/repair-apply.out" 2>> "$LOG/repair-apply.err"; then
      METHOD=patch-fuzz
    else
      reset_fixture
      CANDIDATES=()
      while IFS= read -r f; do [ -n "$f" ] && CANDIDATES[${#CANDIDATES[@]}]=$f; done \
        < <(jq -r '.test_paths[], .prod_paths[]' <<<"$CASE")
      if python3 "$SCRIPT_DIR/apply-patch.py" "$CASEDIR/model-patch.diff" "$WT" ${CANDIDATES[@]+"${CANDIDATES[@]}"} >> "$LOG/repair-apply.out" 2>> "$LOG/repair-apply.err"; then
        METHOD=context-match
      else
        reset_fixture
        alog "APPLY: FAILED $ID reason=patch-does-not-apply (see logs/repair-apply.err)"
        exit 0
      fi
    fi
  fi
fi
# record what was actually applied, normalized as a git diff against the fixture commit
git add -A > /dev/null 2>&1 && git diff --cached --no-color > "$CASEDIR/applied-repair.diff"; git reset -q > /dev/null 2>&1
alog "APPLY: OK $ID method=$METHOD files=$(grep -cE '^\+\+\+ ' "$CASEDIR/applied-repair.diff")"
