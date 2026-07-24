#!/bin/bash
# signal.sh <case-id> — stage 5 (signal: coverage only; mutation testing is explicitly deferred).
# Only runs for cases with repair_success == "yes" in verdicts.json.
# Collects cobertura via the Microsoft.NET.Test.Sdk built-in collector (no csproj changes),
# parses it with parse-cobertura.py, and merges signal_covered into verdicts.json.
# Prints "SIGNAL: ..." as the last line.
set -u
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)
EXP=$ROOT/experiments/markdig-smoke
ID=$1
CASEDIR=$EXP/$ID
WT=$ROOT/.worktrees/$ID
LOG=$CASEDIR/logs
TFM=net10.0
mkdir -p "$LOG" "$CASEDIR/coverage"

CASE=$(jq -c ".[] | select(.id == \"$ID\")" "$EXP/cases.json")
[ -z "$CASE" ] && { echo "SIGNAL: FAIL $ID unknown-case"; exit 1; }
FILTER=$(jq -r .target_filter <<<"$CASE")
PRODS=(); while IFS= read -r f; do [ -n "$f" ] && PRODS[${#PRODS[@]}]=$f; done < <(jq -r '.prod_paths[]' <<<"$CASE")

REPAIR=$(jq -r '.repair_success // "missing"' "$CASEDIR/verdicts.json" 2>/dev/null || echo missing)
if [ "$REPAIR" != "yes" ]; then
  jq '. + {signal_covered: null, signal_note: "skipped: repair_success != yes"}' \
    "$CASEDIR/verdicts.json" > "$CASEDIR/verdicts.json.tmp" && mv "$CASEDIR/verdicts.json.tmp" "$CASEDIR/verdicts.json"
  echo "SIGNAL: SKIP $ID repair_success=$REPAIR"
  exit 0
fi

cd "$WT" || { echo "SIGNAL: FAIL $ID missing-worktree"; exit 1; }
( dotnet test src/Markdig.Tests -f $TFM --filter "FullyQualifiedName~$FILTER" \
    --collect:"Code Coverage;Format=cobertura" --results-directory "$CASEDIR/coverage" --nologo \
    > "$LOG/signal.raw.log" 2>&1 ); RC=$?
sed 's/\x1b\[[0-9;]*m//g' "$LOG/signal.raw.log" | tail -100 > "$CASEDIR/coverage/run.log"
if [ "$RC" != "0" ]; then
  echo "SIGNAL: FAIL $ID coverage-run-rc=$RC (see coverage/run.log)"
  exit 1
fi
XML=$(find "$CASEDIR/coverage" -name '*.cobertura.xml' -print0 | xargs -0 ls -t 2>/dev/null | head -1)
[ -n "$XML" ] || { echo "SIGNAL: FAIL $ID no-cobertura-xml-found"; exit 1; }

python3 "$SCRIPT_DIR/parse-cobertura.py" "$XML" "${PRODS[@]}" > "$CASEDIR/coverage/summary.json" \
  || { echo "SIGNAL: FAIL $ID parse-cobertura"; exit 1; }

COVERED=$(jq 'all(.[]; .covered)' "$CASEDIR/coverage/summary.json")
jq --argjson covered "$COVERED" --arg xml "$(basename "$XML")" \
  '. + {signal_covered: $covered, signal_note: ("cobertura: " + $xml)}' \
  "$CASEDIR/verdicts.json" > "$CASEDIR/verdicts.json.tmp" && mv "$CASEDIR/verdicts.json.tmp" "$CASEDIR/verdicts.json"
echo "SIGNAL: OK $ID signal_covered=$COVERED $(jq -c 'map({file: (.file | split("/") | last), covered, lines_covered})' "$CASEDIR/coverage/summary.json")"
