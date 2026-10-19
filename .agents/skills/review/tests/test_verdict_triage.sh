#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIAGE_SCRIPT="$SCRIPT_DIR/../scripts/verdict_triage.sh"
FIXTURE_DIR="$SCRIPT_DIR/fixtures/verdict_triage/data"

if [[ ! -f "$TRIAGE_SCRIPT" ]]; then
  echo "[error] missing triage script: $TRIAGE_SCRIPT" >&2
  exit 1
fi

assert_eq() {
  local label="$1"
  local expected="$2"
  local actual="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "[fail] $label: expected '$expected' got '$actual'" >&2
    exit 1
  fi
}

field() {
  local key="$1"
  local text="$2"
  awk -F= -v k="$key" '$1==k {print substr($0, index($0,$2))}' <<<"$text"
}

run_case() {
  local fixture="$1"
  local severity="$2"
  bash "$TRIAGE_SCRIPT" "$fixture" "$severity"
}

echo "[info] running verdict triage script tests"

# Case 1: explicit pass marker with no findings -> PASS
OUT="$(run_case "$FIXTURE_DIR/sample_no_findings_pass.md" suggestion)"
assert_eq "case1 VERDICT" "PASS" "$(field VERDICT "$OUT")"
assert_eq "case1 HAS_PASS_MARKER" "1" "$(field HAS_PASS_MARKER "$OUT")"
assert_eq "case1 TOTAL_ALL" "0" "$(field TOTAL_ALL "$OUT")"

# Case 2: no findings and no explicit marker -> UNKNOWN
OUT="$(run_case "$FIXTURE_DIR/sample_no_marker_unknown.md" suggestion)"
assert_eq "case2 VERDICT" "UNKNOWN" "$(field VERDICT "$OUT")"
assert_eq "case2 HAS_PASS_MARKER" "0" "$(field HAS_PASS_MARKER "$OUT")"
assert_eq "case2 TOTAL_ALL" "0" "$(field TOTAL_ALL "$OUT")"

# Case 3: bracket findings + suggestion threshold -> FAIL
OUT="$(run_case "$FIXTURE_DIR/sample_findings_bracket.md" suggestion)"
assert_eq "case3 VERDICT" "FAIL" "$(field VERDICT "$OUT")"
assert_eq "case3 BLOCKER" "1" "$(field BLOCKER "$OUT")"
assert_eq "case3 IMPORTANT" "1" "$(field IMPORTANT "$OUT")"
assert_eq "case3 SUGGESTION" "1" "$(field SUGGESTION "$OUT")"
assert_eq "case3 TOTAL_INCLUDED" "3" "$(field TOTAL_INCLUDED "$OUT")"

# Case 4: findings below active threshold -> PASS (below threshold)
OUT="$(run_case "$FIXTURE_DIR/sample_findings_important_only.md" blocker)"
assert_eq "case4 VERDICT" "PASS" "$(field VERDICT "$OUT")"
assert_eq "case4 TOTAL_ALL" "1" "$(field TOTAL_ALL "$OUT")"
assert_eq "case4 TOTAL_INCLUDED" "0" "$(field TOTAL_INCLUDED "$OUT")"

# Case 5: fallback severity label parsing -> FAIL
OUT="$(run_case "$FIXTURE_DIR/sample_findings_severity_label.md" important)"
assert_eq "case5 VERDICT" "FAIL" "$(field VERDICT "$OUT")"
assert_eq "case5 IMPORTANT" "1" "$(field IMPORTANT "$OUT")"

# Case 6: invalid min severity -> non-zero exit
set +e
bash "$TRIAGE_SCRIPT" "$FIXTURE_DIR/sample_no_findings_pass.md" nonsense >/tmp/verdict_triage_invalid.out 2>&1
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  echo "[fail] case6 expected non-zero exit for invalid severity" >&2
  exit 1
fi

echo "[ok] verdict triage tests passed"
