#!/usr/bin/env bash
set -euo pipefail

FILE="${1:-.agents/skills/review/anti-pattern-suppressions.tsv}"

if [ ! -f "$FILE" ]; then
  echo "[error] suppressions file not found: $FILE" >&2
  exit 1
fi

today="$(date -u +%Y-%m-%d)"
errors=0
line_no=0

while IFS=$'\t' read -r code path_regex owner expiry note || [ -n "${code:-}" ]; do
  line_no=$((line_no + 1))
  [ -z "${code:-}" ] && continue
  [[ "$code" =~ ^# ]] && continue

  if [ -z "${path_regex:-}" ] || [ -z "${owner:-}" ] || [ -z "${expiry:-}" ] || [ -z "${note:-}" ]; then
    echo "[error] $FILE:$line_no missing required columns (code, path_regex, owner, expiry, note)"
    errors=$((errors + 1))
    continue
  fi

  if ! [[ "$expiry" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "[error] $FILE:$line_no expiry must be YYYY-MM-DD, got: $expiry"
    errors=$((errors + 1))
    continue
  fi

  if [ "$expiry" \< "$today" ]; then
    echo "[error] $FILE:$line_no suppression expired on $expiry (today: $today)"
    errors=$((errors + 1))
  fi
done < "$FILE"

if [ "$errors" -gt 0 ]; then
  echo "[fail] suppression lint failed with $errors error(s)"
  exit 1
fi

echo "[ok] suppression lint passed: $FILE"
