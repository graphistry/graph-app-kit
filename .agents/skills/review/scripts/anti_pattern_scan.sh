#!/usr/bin/env bash
set -euo pipefail

# Signal catalog (source of truth):
# AP003 pytest.raises(Exception) broad exception capture
# AP009 back-compat shim comments requiring caller evidence
# AP010 bare `except:` / `except Exception` widens caught type
# AP011 module-level operational tunable (TTL/timeout/retry/...) not env-overridable
# AP016 credential-looking value committed in env/toml config (src/envs defaults stay commented)
# AP020 GitHub Action pinned by mutable tag/branch instead of full commit SHA
# AP021 workflow without a top-level `permissions:` block
# AP022 untrusted github.event / head_ref / inputs expression interpolated into `run:`
# AP023 long-lived AWS access keys in a workflow (prefer OIDC role-to-assume)
# AP024 pull_request_target / labeled trigger in a workflow that reaches secrets or OIDC
# AP025 secrets/OIDC reachable from dispatch/PR triggers with no `environment:` gate
# AP026 secrets/vars expression interpolated into `run:` (prefer env: + "$VAR")
# AP030 wide-open CIDR or wildcard IAM in a CloudFormation template (src/bootstraps)
#
# Usage:
#   anti_pattern_scan.sh [RANGE] [SUPPRESSIONS_FILE]
#   anti_pattern_scan.sh --help
#
# Suppressions TSV format:
#   CODE<TAB>path_regex<TAB>owner<TAB>expiry_yyyy-mm-dd<TAB>note

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  anti_pattern_scan.sh [RANGE] [SUPPRESSIONS_FILE]
  anti_pattern_scan.sh --help

Signal catalog (source of truth):
  AP003 pytest.raises(Exception) broad exception capture
  AP009 back-compat shim comments requiring caller evidence
  AP010 bare `except:` / `except Exception` widens caught type
  AP011 module-level operational tunable (TTL/timeout/retry/...) not env-overridable
  AP016 credential-looking value committed in env/toml config (src/envs defaults stay commented)
  AP020 GitHub Action pinned by mutable tag/branch instead of full commit SHA
  AP021 workflow without a top-level `permissions:` block
  AP022 untrusted github.event / head_ref / inputs expression interpolated into `run:`
  AP023 long-lived AWS access keys in a workflow (prefer OIDC role-to-assume)
  AP024 pull_request_target / labeled trigger in a workflow that reaches secrets or OIDC
  AP025 secrets/OIDC reachable from dispatch/PR triggers with no `environment:` gate
  AP026 secrets/vars expression interpolated into `run:` (prefer env: + "$VAR")
  AP030 wide-open CIDR or wildcard IAM in a CloudFormation template (src/bootstraps)

Suppressions TSV format:
  CODE<TAB>path_regex<TAB>owner<TAB>expiry_yyyy-mm-dd<TAB>note
EOF
  exit 0
fi

RANGE="${1:-origin/master...HEAD}"
SUPPRESSIONS_FILE="${2:-.agents/skills/review/anti-pattern-suppressions.tsv}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[error] must run inside a git repo" >&2
  exit 1
fi

# Portable `mapfile -t` — stock macOS bash is 3.2, which lacks the mapfile builtin,
# so this script (and its AP0xx signals) would otherwise die with "mapfile: command
# not found" before emitting anything.
read_lines() {  # usage: read_lines VARNAME < input
  local __arr="$1" __line
  eval "$__arr=()"
  while IFS= read -r __line; do eval "$__arr+=(\"\$__line\")"; done
}

read_lines CHANGED < <(git diff --name-only "$RANGE")
if [ "${#CHANGED[@]}" -eq 0 ]; then
  echo "[clean] no changed files for range: $RANGE"
  exit 0
fi

# The line-specific AP0xx signals grep whole working-tree files, so they also match lines a
# changed file already had before this range — noise when reading the scanner as PR findings.
# Build the set of lines this range ADDED ("path<TAB>newlineno") from the unified diff so each
# line-specific signal can be tagged `[added]` vs `[pre-existing]`. Bash 3.2-safe: a
# newline-delimited string (macOS bash lacks associative arrays). --unified=0 → only `@@`
# hunk headers (new-file start line) and `+` lines to walk.
ADDED_KEYS=$(git diff --unified=0 "$RANGE" | awk '
  /^\+\+\+ /  { f=$2; sub(/^b\//, "", f); next }
  /^@@ /      { split($3, a, ","); ln=a[1]; sub(/^\+/, "", ln); next }
  /^\+/       { if (f != "" && f != "/dev/null") print f "\t" ln; ln++; next }
')

# 0 (default) = annotate only, emit everything; 1 = strict, drop pre-existing (CI-gate mode).
ADDED_ONLY="${ADDED_ONLY:-0}"

is_added_line() {  # file line -> 0 if this exact (file,line) was added in range
  # Here-string, not `printf | grep -q`: under pipefail, grep -q exiting early SIGPIPEs the
  # producer on large diffs and would misreport every line as pre-existing.
  [ -n "$ADDED_KEYS" ] && grep -qxF "$1	$2" <<<"$ADDED_KEYS"
}

declare -a SUP_CODES=()
declare -a SUP_PATH_REGEX=()
declare -a SUP_NOTES=()

if [ -f "$SUPPRESSIONS_FILE" ]; then
  while IFS=$'\t' read -r code path_regex owner expiry note; do
    [ -z "${code:-}" ] && continue
    [[ "$code" =~ ^# ]] && continue
    [ -z "${path_regex:-}" ] && continue
    SUP_CODES+=("$code")
    SUP_PATH_REGEX+=("$path_regex")
    SUP_NOTES+=("${owner:-unknown}:${expiry:-unknown}:${note:-}")
  done < "$SUPPRESSIONS_FILE"
fi

is_suppressed() {
  local code="$1"
  local file="$2"
  local i
  for i in "${!SUP_CODES[@]}"; do
    if [ "${SUP_CODES[$i]}" = "*" ] || [ "${SUP_CODES[$i]}" = "$code" ]; then
      if [[ "$file" =~ ${SUP_PATH_REGEX[$i]} ]]; then
        return 0
      fi
    fi
  done
  return 1
}

signals=0
suppressed=0
added=0
dropped=0

_emit_out() {  # code file line detail origin
  if is_suppressed "$1" "$2"; then
    suppressed=$((suppressed + 1))
    return
  fi
  signals=$((signals + 1))
  [ "$5" = "added" ] && added=$((added + 1))
  printf '%s\t%s:%s\t%s\t[%s]\n' "$1" "$2" "$3" "$4" "$5"
}

# Line-specific signals (whole-file grep): tag added-by-this-range vs pre-existing; strict
# mode drops pre-existing so a `signals>0` gate only trips on what the PR introduced.
emit() {
  local origin="added"
  is_added_line "$2" "$3" || origin="pre-existing"
  if [ "$origin" = "pre-existing" ] && [ "$ADDED_ONLY" = "1" ]; then
    dropped=$((dropped + 1))
    return
  fi
  _emit_out "$1" "$2" "$3" "$4" "$origin"
}

# File-level signals (AP021/AP024/AP025) are already diff- or existence-derived — they
# fire only because the file is in this range — so they're always PR-relevant (no line filter).
emit_file() {
  _emit_out "$1" "$2" "$3" "$4" "added"
}

collect() {
  local pattern="$1"
  shift
  # -H forces the filename prefix even when a single file is passed — without it rg emits
  # `line:content` for a one-file list, so the `IFS=:` parse below mis-splits (file="123")
  # and every downstream file:line / added-line lookup is wrong.
  rg -n -H --no-heading -e "$pattern" "$@" 2>/dev/null || true
}

read_lines PY_FILES < <(printf '%s\n' "${CHANGED[@]}" | rg '\.py$' || true)
read_lines TEST_FILES < <(printf '%s\n' "${CHANGED[@]}" | rg '(^|/)test_.*\.py$|(^|/)tests?/.*\.py$' || true)
read_lines WORKFLOW_FILES < <(printf '%s\n' "${CHANGED[@]}" | rg '^\.github/workflows/.*\.ya?ml$' || true)
read_lines TEMPLATE_FILES < <(printf '%s\n' "${CHANGED[@]}" | rg '^src/bootstraps/.*\.(ya?ml|json)$' || true)
read_lines ENV_FILES < <(printf '%s\n' "${CHANGED[@]}" | rg '(^|/)[^/]*\.env$|^src/envs/|\.toml$' || true)

# Keep only paths that still exist at HEAD (deleted files have nothing to grep).
existing_only() {  # usage: existing_only ARRAYNAME
  # `if`, not `[ ] && ...`: a false test as the loop's last command would make the
  # eval return 1 and abort the script under `set -e` when the array is empty.
  local __arr="$1" __f
  local __in=()
  eval "__in=(\"\${$__arr[@]:-}\")"
  eval "$__arr=()"
  for __f in "${__in[@]}"; do
    if [ -n "$__f" ] && [ -f "$__f" ]; then eval "$__arr+=(\"\$__f\")"; fi
  done
}
existing_only PY_FILES
existing_only TEST_FILES
existing_only WORKFLOW_FILES
existing_only TEMPLATE_FILES
existing_only ENV_FILES

# YAML key on a line (`  key: ...` or `- key: ...`), empty if none. Used to tell
# `run:` script lines apart from `with:`/`env:`/`if:` mappings, where `${{ }}` is safe.
yaml_key() {
  sed -nE 's/^[[:space:]]*(-[[:space:]]+)?([A-Za-z0-9_-]+):.*/\2/p' <<<"$1"
}

# ---------------------------------------------------------------- Python

if [ "${#TEST_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP003" "$file" "$line" "pytest.raises(Exception) is overly broad"
  done < <(collect 'pytest\.raises\(Exception\)' "${TEST_FILES[@]}")
fi

if [ "${#PY_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP009" "$file" "$line" "shim/back-compat comment requires caller evidence"
  done < <(collect 'back-compat|shim|existing callers' "${PY_FILES[@]}")
fi

if [ "${#PY_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP010" "$file" "$line" "bare except / except Exception widens caught type"
  done < <(collect '^[[:space:]]*except[[:space:]]*(:|\(?(Exception|BaseException)\b)' "${PY_FILES[@]}")
fi

if [ "${#PY_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP011" "$file" "$line" "operational tunable not env-overridable (no os.environ lookup)"
  done < <(collect "^_*[A-Z][A-Z0-9_]*(SECONDS|TTL|TIMEOUT|MAX_|BATCH|RETRY|LIMIT|INTERVAL|RATE|BACKOFF|WINDOW|CACHE_)[A-Z0-9_]*\s*=\s*[0-9\"']" "${PY_FILES[@]}")
fi

# ---------------------------------------------------------------- env / config

if [ "${#ENV_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP016" "$file" "$line" "credential-looking value committed (src/envs defaults must stay commented placeholders)"
  done < <(rg -n -H -i --no-heading \
    -e '^[[:space:]]*[a-z0-9_]*(password|passwd|secret|token|api_?key|access_?key|private_?key)[a-z0-9_]*[[:space:]]*=[[:space:]]*("[^"]+"|'"'"'[^'"'"']+'"'"'|[^[:space:]"'"'"'#]+)' \
    "${ENV_FILES[@]}" 2>/dev/null || true)
fi

# ---------------------------------------------------------------- GitHub Actions

if [ "${#WORKFLOW_FILES[@]}" -gt 0 ]; then
  # AP020 — action referenced by mutable tag/branch instead of a full commit SHA.
  while IFS=: read -r file line content; do
    [ -z "${file:-}" ] && continue
    ref=$(sed -nE 's/.*uses:[[:space:]]*["'"'"']?[^@[:space:]]+@([^[:space:]"'"'"'#]+).*/\1/p' <<<"$content")
    [ -z "$ref" ] && continue
    grep -qE '^[0-9a-f]{40}$' <<<"$ref" && continue
    emit "AP020" "$file" "$line" "action pinned by mutable ref @$ref (pin full commit SHA + # vX.Y.Z comment)"
  done < <(collect 'uses:[[:space:]]*["'"'"']?[^./[:space:]][^@[:space:]]*@' "${WORKFLOW_FILES[@]}")

  for f in "${WORKFLOW_FILES[@]}"; do
    # AP021 — no top-level permissions block: GITHUB_TOKEN gets the repo default scope.
    if ! rg -q '^permissions:' "$f"; then
      emit_file "AP021" "$f" "1" "no top-level permissions: block (set permissions: {} / contents: read, grant per job)"
    fi

    uses_secrets=0
    # grep without -q drains its input, so no SIGPIPE under pipefail.
    if rg 'secrets\.[A-Za-z_]' "$f" | grep -v 'secrets\.GITHUB_TOKEN' >/dev/null; then uses_secrets=1; fi
    if rg -q 'id-token:[[:space:]]*write' "$f"; then uses_secrets=1; fi

    # AP024 — trigger that runs on attacker-influenced refs while secrets are in reach.
    if [ "$uses_secrets" -eq 1 ]; then
      trig=$(rg -n -m1 'pull_request_target|types:.*labeled|^[[:space:]]*-[[:space:]]*labeled[[:space:]]*$' "$f" | cut -d: -f1 || true)
      if [ -n "$trig" ]; then
        emit_file "AP024" "$f" "$trig" "pull_request_target/labeled trigger in a workflow that reaches secrets or OIDC"
      fi
    fi

    # AP025 — secrets/OIDC reachable from dispatch / PR triggers without any environment gate.
    if [ "$uses_secrets" -eq 1 ] && ! rg -q '^[[:space:]]+environment:' "$f"; then
      trig=$(rg -n -m1 '^[[:space:]]*(workflow_dispatch|pull_request|pull_request_target|workflow_call)[[:space:]]*:' "$f" | cut -d: -f1 || true)
      if [ -n "$trig" ]; then
        emit_file "AP025" "$f" "$trig" "secrets/OIDC reachable from dispatch/PR trigger with no environment: gate (any ref can run it)"
      fi
    fi
  done

  # AP022 — attacker-controllable expression interpolated into a run: script.
  # AP026 — secrets/vars interpolated into a run: script (prefer env: + "$VAR").
  while IFS=: read -r file line content; do
    [ -z "${file:-}" ] && continue
    key=$(yaml_key "$content")
    if [ -n "$key" ] && [ "$key" != "run" ]; then continue; fi
    if grep -qE '\$\{\{[^}]*(github\.event\.|github\.head_ref|inputs\.)' <<<"$content"; then
      emit "AP022" "$file" "$line" "untrusted github.event/head_ref/inputs expression inside run: (pass via env:)"
    fi
    if grep -qE '\$\{\{[^}]*(secrets|vars)\.' <<<"$content"; then
      emit "AP026" "$file" "$line" "secrets/vars expression inside run: script (pass via env: and quote \"\$VAR\")"
    fi
  done < <(collect '\$\{\{' "${WORKFLOW_FILES[@]}")

  # AP023 — long-lived cloud keys instead of OIDC.
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP023" "$file" "$line" "long-lived AWS access key in workflow (use OIDC role-to-assume)"
  done < <(collect 'aws-access-key-id:|aws-secret-access-key:|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY' "${WORKFLOW_FILES[@]}")
fi

# ---------------------------------------------------------------- CloudFormation

if [ "${#TEMPLATE_FILES[@]}" -gt 0 ]; then
  while IFS=: read -r file line _; do
    [ -z "${file:-}" ] && continue
    emit "AP030" "$file" "$line" "wide-open CIDR or wildcard IAM action/resource in customer-deployed template"
  done < <(collect '0\.0\.0\.0/0|::/0|Action"?:[[:space:]]*"?'"'"'?\*|Resource"?:[[:space:]]*"?'"'"'?\*["'"'"']?[[:space:]]*,?$' "${TEMPLATE_FILES[@]}")
fi

echo ""
echo "[summary] signals=$signals (added=$added pre-existing=$((signals - added)) dropped_preexisting=$dropped) suppressed=$suppressed range=$RANGE added_only=$ADDED_ONLY"
echo "[note] heuristic signals only; reviewer must confirm true/false positive by inspection"
echo "[note] each signal is tagged [added] (introduced by this range) or [pre-existing] (matched on an untouched line of a changed file); run with ADDED_ONLY=1 to drop pre-existing for a gate"
