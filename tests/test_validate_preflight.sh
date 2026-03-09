#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# tests/test_validate_preflight.sh
#
# Unit tests for the pre-flight secret/variable validation logic used in
# .github/workflows/deploy.yml (deploy-frontend job).
#
# These tests simulate the validation behaviour locally without requiring a
# real GitHub Actions environment or live Azure credentials.
#
# Usage:
#   bash tests/test_validate_preflight.sh
#   # or, if executable:
#   ./tests/test_validate_preflight.sh
#
# Exit codes:
#   0  – all tests passed
#   1  – one or more tests failed
# =============================================================================

# ---------------------------------------------------------------------------
# Colour helpers (disabled when not writing to a terminal)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

# ---------------------------------------------------------------------------
# Test counters
# ---------------------------------------------------------------------------
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

pass() {
  local name="$1"
  TESTS_RUN=$((TESTS_RUN + 1))
  TESTS_PASSED=$((TESTS_PASSED + 1))
  echo -e "  ${GREEN}✔${RESET}  ${name}"
}

fail() {
  local name="$1"
  local reason="${2:-}"
  TESTS_RUN=$((TESTS_RUN + 1))
  TESTS_FAILED=$((TESTS_FAILED + 1))
  FAILED_TESTS+=("${name}")
  echo -e "  ${RED}✘${RESET}  ${name}"
  if [ -n "${reason}" ]; then
    echo -e "       ${RED}↳ ${reason}${RESET}"
  fi
}

# assert_exit_zero <description> <exit-code>
assert_exit_zero() {
  local desc="$1"
  local code="$2"
  if [ "${code}" -eq 0 ]; then
    pass "${desc}"
  else
    fail "${desc}" "expected exit 0, got ${code}"
  fi
}

# assert_exit_nonzero <description> <exit-code>
assert_exit_nonzero() {
  local desc="$1"
  local code="$2"
  if [ "${code}" -ne 0 ]; then
    pass "${desc}"
  else
    fail "${desc}" "expected non-zero exit, got 0"
  fi
}

# assert_output_contains <description> <haystack> <needle>
assert_output_contains() {
  local desc="$1"
  local haystack="$2"
  local needle="$3"
  if echo "${haystack}" | grep -qF "${needle}"; then
    pass "${desc}"
  else
    fail "${desc}" "expected output to contain: '${needle}'"
  fi
}

# assert_output_not_contains <description> <haystack> <needle>
assert_output_not_contains() {
  local desc="$1"
  local haystack="$2"
  local needle="$3"
  if ! echo "${haystack}" | grep -qF "${needle}"; then
    pass "${desc}"
  else
    fail "${desc}" "expected output NOT to contain: '${needle}'"
  fi
}

# ---------------------------------------------------------------------------
# The validation function under test
#
# This is a self-contained reimplementation of the logic that lives inside
# the deploy-frontend job's "Validate required secrets and variables" step.
# Keeping it here (rather than sourcing the workflow YAML) means the tests
# run without any GitHub Actions tooling.
#
# Parameters are passed via environment variables so that each test can
# control exactly which values are present or absent.
# ---------------------------------------------------------------------------

# Required secret names (mirrors deploy.yml)
REQUIRED_SECRETS=(
  "AZURE_STATIC_WEB_APPS_API_TOKEN"
  "AZURE_CLIENT_ID"
  "AZURE_TENANT_ID"
  "AZURE_SUBSCRIPTION_ID"
)

# Required variable names (mirrors deploy.yml)
REQUIRED_VARIABLES=(
  "VITE_API_BASE_URL"
  "AZURE_SWA_NAME"
  "AZURE_RESOURCE_GROUP"
)

# run_preflight_check
#
# Reads the values of REQUIRED_SECRETS and REQUIRED_VARIABLES from the
# current environment (prefixed with SECRET_ and VAR_ respectively) and
# prints diagnostics to stdout.
#
# Returns 0 if all required values are present and non-empty, 1 otherwise.
#
# Environment variable naming convention used by the tests:
#   SECRET_<NAME>   – simulates a GitHub secret called <NAME>
#   VAR_<NAME>      – simulates a GitHub variable called <NAME>
run_preflight_check() {
  local missing=()
  local output=""

  # Check secrets
  for secret_name in "${REQUIRED_SECRETS[@]}"; do
    local env_key="SECRET_${secret_name}"
    local value="${!env_key:-}"
    if [ -z "${value}" ]; then
      missing+=("secret: ${secret_name}")
      output+="[ERROR] Missing secret: ${secret_name}"$'\n'
    else
      output+="[OK]    Secret present: ${secret_name}"$'\n'
    fi
  done

  # Check variables
  for var_name in "${REQUIRED_VARIABLES[@]}"; do
    local env_key="VAR_${var_name}"
    local value="${!env_key:-}"
    if [ -z "${value}" ]; then
      missing+=("variable: ${var_name}")
      output+="[ERROR] Missing variable: ${var_name}"$'\n'
    else
      output+="[OK]    Variable present: ${var_name}"$'\n'
    fi
  done

  # Summary
  if [ "${#missing[@]}" -gt 0 ]; then
    output+=""$'\n'
    output+="Pre-flight check FAILED. The following required secrets/variables are missing:"$'\n'
    for item in "${missing[@]}"; do
      output+="  - ${item}"$'\n'
    done
    output+=""$'\n'
    output+="See docs/setup/github-secrets-setup.md for setup instructions."$'\n'
    echo "${output}"
    return 1
  fi

  output+=""$'\n'
  output+="Pre-flight check PASSED. All required secrets and variables are present."$'\n'
  echo "${output}"
  return 0
}

# ---------------------------------------------------------------------------
# Helper: build a fully-populated environment for run_preflight_check
# ---------------------------------------------------------------------------
set_all_valid_env() {
  export SECRET_AZURE_STATIC_WEB_APPS_API_TOKEN="fake-swa-token"
  export SECRET_AZURE_CLIENT_ID="fake-client-id"
  export SECRET_AZURE_TENANT_ID="fake-tenant-id"
  export SECRET_AZURE_SUBSCRIPTION_ID="fake-subscription-id"
  export VAR_VITE_API_BASE_URL="https://api.example.com"
  export VAR_AZURE_SWA_NAME="my-swa-app"
  export VAR_AZURE_RESOURCE_GROUP="my-resource-group"
}

# ---------------------------------------------------------------------------
# Helper: unset all simulated secrets/variables
# ---------------------------------------------------------------------------
unset_all_env() {
  unset SECRET_AZURE_STATIC_WEB_APPS_API_TOKEN \
        SECRET_AZURE_CLIENT_ID \
        SECRET_AZURE_TENANT_ID \
        SECRET_AZURE_SUBSCRIPTION_ID \
        VAR_VITE_API_BASE_URL \
        VAR_AZURE_SWA_NAME \
        VAR_AZURE_RESOURCE_GROUP 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

echo ""
echo -e "${BOLD}${CYAN}=== Pre-flight Validation Tests ===${RESET}"
echo ""

# ── Suite 1: Happy path ────────────────────────────────────────────────────
echo -e "${BOLD}Suite 1: All secrets and variables present${RESET}"

unset_all_env
set_all_valid_env

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_zero \
  "exits 0 when all secrets and variables are present" \
  "${exit_code}"

assert_output_contains \
  "reports PASSED in summary" \
  "${output}" \
  "Pre-flight check PASSED"

assert_output_contains \
  "confirms AZURE_STATIC_WEB_APPS_API_TOKEN is present" \
  "${output}" \
  "[OK]    Secret present: AZURE_STATIC_WEB_APPS_API_TOKEN"

assert_output_contains \
  "confirms AZURE_CLIENT_ID is present" \
  "${output}" \
  "[OK]    Secret present: AZURE_CLIENT_ID"

assert_output_contains \
  "confirms AZURE_TENANT_ID is present" \
  "${output}" \
  "[OK]    Secret present: AZURE_TENANT_ID"

assert_output_contains \
  "confirms AZURE_SUBSCRIPTION_ID is present" \
  "${output}" \
  "[OK]    Secret present: AZURE_SUBSCRIPTION_ID"

assert_output_contains \
  "confirms VITE_API_BASE_URL is present" \
  "${output}" \
  "[OK]    Variable present: VITE_API_BASE_URL"

assert_output_contains \
  "confirms AZURE_SWA_NAME is present" \
  "${output}" \
  "[OK]    Variable present: AZURE_SWA_NAME"

assert_output_contains \
  "confirms AZURE_RESOURCE_GROUP is present" \
  "${output}" \
  "[OK]    Variable present: AZURE_RESOURCE_GROUP"

assert_output_not_contains \
  "does not print any [ERROR] lines when all values present" \
  "${output}" \
  "[ERROR]"

echo ""

# ── Suite 2: All secrets and variables missing ─────────────────────────────
echo -e "${BOLD}Suite 2: All secrets and variables missing${RESET}"

unset_all_env

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when all secrets and variables are missing" \
  "${exit_code}"

assert_output_contains \
  "reports FAILED in summary" \
  "${output}" \
  "Pre-flight check FAILED"

assert_output_contains \
  "lists missing AZURE_STATIC_WEB_APPS_API_TOKEN" \
  "${output}" \
  "secret: AZURE_STATIC_WEB_APPS_API_TOKEN"

assert_output_contains \
  "lists missing AZURE_CLIENT_ID" \
  "${output}" \
  "secret: AZURE_CLIENT_ID"

assert_output_contains \
  "lists missing AZURE_TENANT_ID" \
  "${output}" \
  "secret: AZURE_TENANT_ID"

assert_output_contains \
  "lists missing AZURE_SUBSCRIPTION_ID" \
  "${output}" \
  "secret: AZURE_SUBSCRIPTION_ID"

assert_output_contains \
  "lists missing VITE_API_BASE_URL" \
  "${output}" \
  "variable: VITE_API_BASE_URL"

assert_output_contains \
  "lists missing AZURE_SWA_NAME" \
  "${output}" \
  "variable: AZURE_SWA_NAME"

assert_output_contains \
  "lists missing AZURE_RESOURCE_GROUP" \
  "${output}" \
  "variable: AZURE_RESOURCE_GROUP"

assert_output_contains \
  "references the setup documentation" \
  "${output}" \
  "docs/setup/github-secrets-setup.md"

assert_output_not_contains \
  "does not report PASSED when values are missing" \
  "${output}" \
  "Pre-flight check PASSED"

echo ""

# ── Suite 3: Individual missing secrets ────────────────────────────────────
echo -e "${BOLD}Suite 3: Individual missing secrets${RESET}"

# 3a: Missing AZURE_STATIC_WEB_APPS_API_TOKEN only
unset_all_env
set_all_valid_env
unset SECRET_AZURE_STATIC_WEB_APPS_API_TOKEN

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_STATIC_WEB_APPS_API_TOKEN is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_STATIC_WEB_APPS_API_TOKEN as missing" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_STATIC_WEB_APPS_API_TOKEN"

assert_output_not_contains \
  "does not flag AZURE_CLIENT_ID when it is present" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_CLIENT_ID"

# 3b: Missing AZURE_CLIENT_ID only
unset_all_env
set_all_valid_env
unset SECRET_AZURE_CLIENT_ID

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_CLIENT_ID is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_CLIENT_ID as missing" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_CLIENT_ID"

# 3c: Missing AZURE_TENANT_ID only
unset_all_env
set_all_valid_env
unset SECRET_AZURE_TENANT_ID

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_TENANT_ID is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_TENANT_ID as missing" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_TENANT_ID"

# 3d: Missing AZURE_SUBSCRIPTION_ID only
unset_all_env
set_all_valid_env
unset SECRET_AZURE_SUBSCRIPTION_ID

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_SUBSCRIPTION_ID is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_SUBSCRIPTION_ID as missing" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_SUBSCRIPTION_ID"

echo ""

# ── Suite 4: Individual missing variables ──────────────────────────────────
echo -e "${BOLD}Suite 4: Individual missing variables${RESET}"

# 4a: Missing VITE_API_BASE_URL only
unset_all_env
set_all_valid_env
unset VAR_VITE_API_BASE_URL

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when VITE_API_BASE_URL is missing" \
  "${exit_code}"

assert_output_contains \
  "reports VITE_API_BASE_URL as missing" \
  "${output}" \
  "[ERROR] Missing variable: VITE_API_BASE_URL"

assert_output_not_contains \
  "does not flag AZURE_SWA_NAME when it is present" \
  "${output}" \
  "[ERROR] Missing variable: AZURE_SWA_NAME"

# 4b: Missing AZURE_SWA_NAME only
unset_all_env
set_all_valid_env
unset VAR_AZURE_SWA_NAME

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_SWA_NAME is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_SWA_NAME as missing" \
  "${output}" \
  "[ERROR] Missing variable: AZURE_SWA_NAME"

# 4c: Missing AZURE_RESOURCE_GROUP only
unset_all_env
set_all_valid_env
unset VAR_AZURE_RESOURCE_GROUP

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when AZURE_RESOURCE_GROUP is missing" \
  "${exit_code}"

assert_output_contains \
  "reports AZURE_RESOURCE_GROUP as missing" \
  "${output}" \
  "[ERROR] Missing variable: AZURE_RESOURCE_GROUP"

echo ""

# ── Suite 5: Mixed missing (secrets + variables) ───────────────────────────
echo -e "${BOLD}Suite 5: Mixed missing secrets and variables${RESET}"

unset_all_env
set_all_valid_env
unset SECRET_AZURE_CLIENT_ID
unset VAR_VITE_API_BASE_URL

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when both a secret and a variable are missing" \
  "${exit_code}"

assert_output_contains \
  "reports missing secret AZURE_CLIENT_ID" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_CLIENT_ID"

assert_output_contains \
  "reports missing variable VITE_API_BASE_URL" \
  "${output}" \
  "[ERROR] Missing variable: VITE_API_BASE_URL"

assert_output_contains \
  "references setup doc in mixed-missing scenario" \
  "${output}" \
  "docs/setup/github-secrets-setup.md"

echo ""

# ── Suite 6: Empty-string values treated as missing ────────────────────────
echo -e "${BOLD}Suite 6: Empty-string values treated as missing${RESET}"

unset_all_env
set_all_valid_env
export SECRET_AZURE_STATIC_WEB_APPS_API_TOKEN=""

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when a secret is set to an empty string" \
  "${exit_code}"

assert_output_contains \
  "treats empty-string secret as missing" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_STATIC_WEB_APPS_API_TOKEN"

unset_all_env
set_all_valid_env
export VAR_AZURE_SWA_NAME=""

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero when a variable is set to an empty string" \
  "${exit_code}"

assert_output_contains \
  "treats empty-string variable as missing" \
  "${output}" \
  "[ERROR] Missing variable: AZURE_SWA_NAME"

echo ""

# ── Suite 7: Whitespace-only values treated as missing ─────────────────────
echo -e "${BOLD}Suite 7: Whitespace-only values treated as missing${RESET}"

# The validation logic uses [ -z "${value}" ] which does NOT strip whitespace.
# A value of "   " is technically non-empty, so the check passes.
# This suite documents that known behaviour explicitly.

unset_all_env
set_all_valid_env
export SECRET_AZURE_CLIENT_ID="   "

output=$(run_preflight_check 2>&1)
exit_code=$?

# Whitespace-only is non-empty from bash's perspective — document this.
assert_exit_zero \
  "whitespace-only secret is treated as present (known limitation)" \
  "${exit_code}"

assert_output_contains \
  "whitespace-only secret shows as [OK] (known limitation)" \
  "${output}" \
  "[OK]    Secret present: AZURE_CLIENT_ID"

echo ""

# ── Suite 8: Output structure / formatting ─────────────────────────────────
echo -e "${BOLD}Suite 8: Output structure and formatting${RESET}"

unset_all_env
set_all_valid_env

output=$(run_preflight_check 2>&1)

# Every required secret should appear exactly once in [OK] lines
for secret_name in "${REQUIRED_SECRETS[@]}"; do
  count=$(echo "${output}" | grep -cF "[OK]    Secret present: ${secret_name}" || true)
  if [ "${count}" -eq 1 ]; then
    pass "secret ${secret_name} appears exactly once in output"
  else
    fail "secret ${secret_name} appears exactly once in output" \
         "found ${count} occurrences"
  fi
done

# Every required variable should appear exactly once in [OK] lines
for var_name in "${REQUIRED_VARIABLES[@]}"; do
  count=$(echo "${output}" | grep -cF "[OK]    Variable present: ${var_name}" || true)
  if [ "${count}" -eq 1 ]; then
    pass "variable ${var_name} appears exactly once in output"
  else
    fail "variable ${var_name} appears exactly once in output" \
         "found ${count} occurrences"
  fi
done

echo ""

# ── Suite 9: Exactly the right items are flagged ───────────────────────────
echo -e "${BOLD}Suite 9: Only missing items are flagged as errors${RESET}"

unset_all_env
set_all_valid_env
unset SECRET_AZURE_TENANT_ID

output=$(run_preflight_check 2>&1)
exit_code=$?

assert_exit_nonzero \
  "exits non-zero with exactly one missing secret" \
  "${exit_code}"

# Count total [ERROR] lines — should be exactly 1
error_count=$(echo "${output}" | grep -c "\[ERROR\]" || true)
if [ "${error_count}" -eq 1 ]; then
  pass "exactly one [ERROR] line when exactly one item is missing"
else
  fail "exactly one [ERROR] line when exactly one item is missing" \
       "found ${error_count} [ERROR] lines"
fi

# The one error should be for the missing secret
assert_output_contains \
  "the single error is for AZURE_TENANT_ID" \
  "${output}" \
  "[ERROR] Missing secret: AZURE_TENANT_ID"

echo ""

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}=== Results ===${RESET}"
echo ""
echo -e "  Tests run:    ${BOLD}${TESTS_RUN}${RESET}"
echo -e "  ${GREEN}Passed:       ${TESTS_PASSED}${RESET}"

if [ "${TESTS_FAILED}" -gt 0 ]; then
  echo -e "  ${RED}Failed:       ${TESTS_FAILED}${RESET}"
  echo ""
  echo -e "${RED}Failed tests:${RESET}"
  for t in "${FAILED_TESTS[@]}"; do
    echo -e "  ${RED}•${RESET} ${t}"
  done
  echo ""
  exit 1
else
  echo -e "  Failed:       0"
  echo ""
  echo -e "${GREEN}All tests passed.${RESET}"
  echo ""
  exit 0
fi