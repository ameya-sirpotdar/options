#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# validate-github-config.sh
#
# Local pre-flight validation script for GitHub Actions secrets and variables
# required by the SWA (Static Web App) frontend deployment workflow.
#
# Usage:
#   ./scripts/validate-github-config.sh [--repo OWNER/REPO] [--env ENVIRONMENT]
#
# Requirements:
#   - GitHub CLI (gh) installed and authenticated
#   - Sufficient permissions to read secrets/variables for the target repo
#
# See also: docs/setup/github-secrets-setup.md
# =============================================================================

# ---------------------------------------------------------------------------
# Colour helpers (disabled when not a TTY)
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
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
# Logging helpers
# ---------------------------------------------------------------------------
info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}$*${RESET}"; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REPO=""
ENVIRONMENT=""
SETUP_DOC="docs/setup/github-secrets-setup.md"
EXIT_CODE=0

# ---------------------------------------------------------------------------
# Required repository-level secrets
# ---------------------------------------------------------------------------
REQUIRED_REPO_SECRETS=(
  "AZURE_STATIC_WEB_APPS_API_TOKEN"
)

# ---------------------------------------------------------------------------
# Required repository-level variables
# ---------------------------------------------------------------------------
REQUIRED_REPO_VARIABLES=(
  "SWA_APP_LOCATION"
  "SWA_OUTPUT_LOCATION"
)

# ---------------------------------------------------------------------------
# Required environment-level secrets (checked when --env is supplied)
# ---------------------------------------------------------------------------
REQUIRED_ENV_SECRETS=(
  "AZURE_STATIC_WEB_APPS_API_TOKEN"
)

# ---------------------------------------------------------------------------
# Required environment-level variables (checked when --env is supplied)
# ---------------------------------------------------------------------------
REQUIRED_ENV_VARIABLES=(
  "SWA_APP_LOCATION"
  "SWA_OUTPUT_LOCATION"
)

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Validate that all GitHub secrets and variables required for the SWA frontend
deployment are configured correctly.

Options:
  -r, --repo  OWNER/REPO   GitHub repository to validate (default: auto-detect
                            from 'gh repo view')
  -e, --env   ENVIRONMENT  Also validate the named GitHub environment's secrets
                            and variables (e.g. production, staging)
  -h, --help               Show this help message and exit

Examples:
  $(basename "$0")
  $(basename "$0") --repo myorg/myrepo
  $(basename "$0") --repo myorg/myrepo --env production

See ${SETUP_DOC} for full setup instructions.
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo)
      REPO="$2"
      shift 2
      ;;
    -e|--env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
check_dependencies() {
  header "Checking dependencies"

  local missing=0

  if ! command -v gh &>/dev/null; then
    error "GitHub CLI (gh) is not installed."
    error "Install it from https://cli.github.com/ and run 'gh auth login'."
    missing=1
  else
    success "GitHub CLI (gh) found: $(gh --version | head -1)"
  fi

  if ! command -v jq &>/dev/null; then
    error "jq is not installed."
    error "Install it from https://stedolan.github.io/jq/download/"
    missing=1
  else
    success "jq found: $(jq --version)"
  fi

  if [[ $missing -ne 0 ]]; then
    error "One or more required tools are missing. Aborting."
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# GitHub CLI auth check
# ---------------------------------------------------------------------------
check_gh_auth() {
  header "Checking GitHub CLI authentication"

  if ! gh auth status &>/dev/null; then
    error "GitHub CLI is not authenticated."
    error "Run: gh auth login"
    exit 1
  fi

  local gh_user
  gh_user=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
  success "Authenticated as: ${gh_user}"
}

# ---------------------------------------------------------------------------
# Resolve repository
# ---------------------------------------------------------------------------
resolve_repo() {
  header "Resolving target repository"

  if [[ -z "$REPO" ]]; then
    if REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null); then
      info "Auto-detected repository: ${REPO}"
    else
      error "Could not auto-detect repository. Are you inside a git repo with a GitHub remote?"
      error "Use --repo OWNER/REPO to specify explicitly."
      exit 1
    fi
  else
    info "Using specified repository: ${REPO}"
  fi

  # Verify the repo is accessible
  if ! gh repo view "$REPO" &>/dev/null; then
    error "Repository '${REPO}' is not accessible. Check the name and your permissions."
    exit 1
  fi

  success "Repository accessible: ${REPO}"
}

# ---------------------------------------------------------------------------
# Fetch list of repository secrets (names only — values are never exposed)
# ---------------------------------------------------------------------------
fetch_repo_secret_names() {
  gh api \
    --paginate \
    "repos/${REPO}/actions/secrets" \
    --jq '.secrets[].name' \
    2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Fetch list of repository variables
# ---------------------------------------------------------------------------
fetch_repo_variable_names() {
  gh api \
    --paginate \
    "repos/${REPO}/actions/variables" \
    --jq '.variables[].name' \
    2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Fetch list of environment secrets
# ---------------------------------------------------------------------------
fetch_env_secret_names() {
  local env_name="$1"
  gh api \
    --paginate \
    "repos/${REPO}/environments/${env_name}/secrets" \
    --jq '.secrets[].name' \
    2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Fetch list of environment variables
# ---------------------------------------------------------------------------
fetch_env_variable_names() {
  local env_name="$1"
  gh api \
    --paginate \
    "repos/${REPO}/environments/${env_name}/variables" \
    --jq '.variables[].name' \
    2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Check a single name against a newline-separated list
# Returns 0 if found, 1 if not found
# ---------------------------------------------------------------------------
name_in_list() {
  local needle="$1"
  local haystack="$2"
  echo "$haystack" | grep -qx "$needle"
}

# ---------------------------------------------------------------------------
# Validate a list of required names against an available list
# Prints OK / MISSING for each entry; increments EXIT_CODE on any missing
# ---------------------------------------------------------------------------
validate_names() {
  local label="$1"          # e.g. "secret" or "variable"
  local available="$2"      # newline-separated list of available names
  shift 2
  local required=("$@")

  local any_missing=0

  for name in "${required[@]}"; do
    if name_in_list "$name" "$available"; then
      success "${label}: ${name}"
    else
      error "MISSING ${label}: ${name}"
      any_missing=1
      EXIT_CODE=1
    fi
  done

  return $any_missing
}

# ---------------------------------------------------------------------------
# Validate repository-level secrets and variables
# ---------------------------------------------------------------------------
validate_repo_config() {
  header "Validating repository-level secrets (${REPO})"

  local secret_names
  secret_names=$(fetch_repo_secret_names)

  if [[ -z "$secret_names" ]]; then
    warn "No repository secrets found (or insufficient permissions to list them)."
    warn "You may need 'admin' or 'secrets' permission on the repository."
  fi

  validate_names "repo secret" "$secret_names" "${REQUIRED_REPO_SECRETS[@]}" || true

  header "Validating repository-level variables (${REPO})"

  local variable_names
  variable_names=$(fetch_repo_variable_names)

  if [[ -z "$variable_names" ]]; then
    warn "No repository variables found (or insufficient permissions to list them)."
  fi

  validate_names "repo variable" "$variable_names" "${REQUIRED_REPO_VARIABLES[@]}" || true
}

# ---------------------------------------------------------------------------
# Validate environment-level secrets and variables
# ---------------------------------------------------------------------------
validate_env_config() {
  local env_name="$1"

  header "Validating environment secrets (${env_name})"

  # Verify the environment exists
  if ! gh api "repos/${REPO}/environments/${env_name}" &>/dev/null; then
    error "Environment '${env_name}' does not exist in repository '${REPO}'."
    error "Create it at: https://github.com/${REPO}/settings/environments"
    EXIT_CODE=1
    return
  fi

  success "Environment exists: ${env_name}"

  local env_secret_names
  env_secret_names=$(fetch_env_secret_names "$env_name")

  if [[ -z "$env_secret_names" ]]; then
    warn "No environment secrets found for '${env_name}' (or insufficient permissions)."
  fi

  validate_names "env secret [${env_name}]" "$env_secret_names" "${REQUIRED_ENV_SECRETS[@]}" || true

  header "Validating environment variables (${env_name})"

  local env_variable_names
  env_variable_names=$(fetch_env_variable_names "$env_name")

  if [[ -z "$env_variable_names" ]]; then
    warn "No environment variables found for '${env_name}' (or insufficient permissions)."
  fi

  validate_names "env variable [${env_name}]" "$env_variable_names" "${REQUIRED_ENV_VARIABLES[@]}" || true
}

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print_summary() {
  echo ""
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

  if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✔  All required secrets and variables are configured.${RESET}"
    echo -e "   The SWA frontend deployment workflow should proceed without issues."
  else
    echo -e "${RED}${BOLD}✘  One or more required secrets or variables are MISSING.${RESET}"
    echo ""
    echo -e "   The frontend deployment will be blocked until these are resolved."
    echo ""
    echo -e "   ${BOLD}Setup instructions:${RESET}"
    echo -e "   ${CYAN}${SETUP_DOC}${RESET}"
    echo ""
    echo -e "   ${BOLD}Quick links:${RESET}"
    echo -e "   • Repository secrets:  https://github.com/${REPO}/settings/secrets/actions"
    echo -e "   • Repository variables: https://github.com/${REPO}/settings/variables/actions"
    if [[ -n "$ENVIRONMENT" ]]; then
      echo -e "   • Environment settings: https://github.com/${REPO}/settings/environments"
    fi
  fi

  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo -e "${BOLD}${CYAN}"
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║        GitHub SWA Deployment Config Validator                ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo -e "${RESET}"

  check_dependencies
  check_gh_auth
  resolve_repo
  validate_repo_config

  if [[ -n "$ENVIRONMENT" ]]; then
    validate_env_config "$ENVIRONMENT"
  fi

  print_summary

  exit $EXIT_CODE
}

main "$@"