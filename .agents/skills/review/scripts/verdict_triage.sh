#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'USAGE'
Usage:
  verdict_triage.sh <report_file> [min_severity]

Args:
  report_file   Path to a findings/final report markdown file
  min_severity  suggestion|important|blocker (default: suggestion)

Output (key=value lines):
  FILE
  MIN_SEVERITY
  HAS_PASS_MARKER
  BLOCKER
  IMPORTANT
  SUGGESTION
  TOTAL_ALL
  TOTAL_INCLUDED
  FILTERED_OUT
  VERDICT
  REASON
USAGE
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "[error] expected 1-2 args; run with --help" >&2
  exit 2
fi

FILE_PATH="$1"
MIN_SEVERITY="${2:-suggestion}"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "[error] report file not found: $FILE_PATH" >&2
  exit 2
fi

case "$MIN_SEVERITY" in
  suggestion|important|blocker) ;;
  *)
    echo "[error] invalid min_severity: $MIN_SEVERITY (expected suggestion|important|blocker)" >&2
    exit 2
    ;;
esac

count_matches() {
  local pattern="$1"
  local file_path="$2"
  grep -oE "$pattern" "$file_path" 2>/dev/null | wc -l | tr -d ' ' || true
}

# Primary parser: bracket-style findings used by review skill artifacts.
BLOCKER_COUNT=$(count_matches '\[BLOCKER\]' "$FILE_PATH")
IMPORTANT_COUNT=$(count_matches '\[IMPORTANT\]' "$FILE_PATH")
SUGGESTION_COUNT=$(count_matches '\[SUGGESTION\]' "$FILE_PATH")

# Fallback parser: severity-label style (High/Medium/Low) for mixed artifacts.
# Only used if no bracket-style markers are found.
if [[ "$BLOCKER_COUNT" -eq 0 && "$IMPORTANT_COUNT" -eq 0 && "$SUGGESTION_COUNT" -eq 0 ]]; then
  CRITICAL_LINES=$(count_matches 'Severity[^\n]*Critical' "$FILE_PATH")
  HIGH_LINES=$(count_matches 'Severity[^\n]*High' "$FILE_PATH")
  MEDIUM_LINES=$(count_matches 'Severity[^\n]*Medium' "$FILE_PATH")
  LOW_LINES=$(count_matches 'Severity[^\n]*Low' "$FILE_PATH")

  BLOCKER_COUNT=$((BLOCKER_COUNT + CRITICAL_LINES))
  IMPORTANT_COUNT=$((IMPORTANT_COUNT + HIGH_LINES + MEDIUM_LINES))
  SUGGESTION_COUNT=$((SUGGESTION_COUNT + LOW_LINES))
fi

TOTAL_ALL=$((BLOCKER_COUNT + IMPORTANT_COUNT + SUGGESTION_COUNT))

case "$MIN_SEVERITY" in
  suggestion)
    TOTAL_INCLUDED=$TOTAL_ALL
    ;;
  important)
    TOTAL_INCLUDED=$((BLOCKER_COUNT + IMPORTANT_COUNT))
    ;;
  blocker)
    TOTAL_INCLUDED=$BLOCKER_COUNT
    ;;
esac

FILTERED_OUT=$((TOTAL_ALL - TOTAL_INCLUDED))
HAS_PASS_MARKER=0

if grep -qiE '(No issues found\.|No findings\.|All previous findings have been addressed\.)' "$FILE_PATH"; then
  HAS_PASS_MARKER=1
fi

if [[ "$TOTAL_INCLUDED" -gt 0 ]]; then
  VERDICT="FAIL"
  REASON="included findings present at threshold"
else
  if [[ "$TOTAL_ALL" -gt 0 ]]; then
    VERDICT="PASS"
    REASON="findings exist but all are below threshold"
  elif [[ "$HAS_PASS_MARKER" -eq 1 ]]; then
    VERDICT="PASS"
    REASON="explicit pass marker with zero included findings"
  else
    VERDICT="UNKNOWN"
    REASON="zero included findings but no explicit pass marker"
  fi
fi

printf 'FILE=%s\n' "$FILE_PATH"
printf 'MIN_SEVERITY=%s\n' "$MIN_SEVERITY"
printf 'HAS_PASS_MARKER=%s\n' "$HAS_PASS_MARKER"
printf 'BLOCKER=%s\n' "$BLOCKER_COUNT"
printf 'IMPORTANT=%s\n' "$IMPORTANT_COUNT"
printf 'SUGGESTION=%s\n' "$SUGGESTION_COUNT"
printf 'TOTAL_ALL=%s\n' "$TOTAL_ALL"
printf 'TOTAL_INCLUDED=%s\n' "$TOTAL_INCLUDED"
printf 'FILTERED_OUT=%s\n' "$FILTERED_OUT"
printf 'VERDICT=%s\n' "$VERDICT"
printf 'REASON=%s\n' "$REASON"
