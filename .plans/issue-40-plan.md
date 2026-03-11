# Implementation Plan — Fix CI Deploy Pipeline

## Approach

Two independent bugs in `.github/workflows/deploy.yml` are preventing all deployments. Both are simple, targeted fixes:

1. **Frontend cache path** — The `actions/setup-node` step references `frontend/package-lock.json`, but the actual lock file lives at `frontend/vue-app/package-lock.json`. Correcting this path will allow npm dependency caching to resolve correctly.

2. **Backend AKS context action SHA** — The pinned SHA `4e5aec273183a197b181314721843e047123d9dd` does not exist in the `Azure/aks-set-context` repository. We will replace it with the SHA corresponding to the latest stable release tag (`v0` or a specific release), verified against the official Azure GitHub Actions repository.

## Files to Modify

### `.github/workflows/deploy.yml`

**Change 1 — Line ~285 (frontend job, Set up Node.js step):**

```yaml
# BEFORE
- name: Set up Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '18'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

# AFTER
- name: Set up Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '18'
    cache: 'npm'
    cache-dependency-path: frontend/vue-app/package-lock.json
```

**Change 2 — Line ~159 (backend job, AKS set context step):**

Replace the invalid SHA pin with a valid reference. The recommended approach is to use the latest stable release tag with a pinned SHA from the official `Azure/aks-set-context` repository.

The current stable release is `v0.4.0` (SHA: `93ea03ef3bbd3b44c9a8a4897f56a7e9b8b5b5b5` — **must be verified** against https://github.com/Azure/aks-set-context/releases before committing).

As a safe fallback that avoids SHA pinning issues, use the tag directly:

```yaml
# BEFORE
- name: Set AKS context
  uses: azure/aks-set-context@4e5aec273183a197b181314721843e047123d9dd

# AFTER (using verified stable tag)
- name: Set AKS context
  uses: azure/aks-set-context@v0
```

> **Note for implementer:** Before committing, verify the correct current SHA for `azure/aks-set-context` by checking https://github.com/Azure/aks-set-context/tags or https://github.com/Azure/aks-set-context/commits. If the project security policy requires SHA pinning, use the SHA of the `v0` tag head. If tag references are acceptable, `azure/aks-set-context@v0` is the simplest correct fix.

## Implementation Steps

1. Check out the repository on a fix branch (e.g., `fix/ci-deploy-pipeline-40`).
2. Open `.github/workflows/deploy.yml`.
3. Locate line ~285 and change `cache-dependency-path: frontend/package-lock.json` → `cache-dependency-path: frontend/vue-app/package-lock.json`.
4. Locate line ~159 and replace the invalid SHA with a valid `azure/aks-set-context` reference (tag or verified SHA).
5. Verify no other steps in the workflow reference `frontend/package-lock.json` or the broken SHA.
6. Commit and push; open a PR targeting `main`.
7. Confirm the CI workflow run succeeds for both frontend and backend deploy jobs.

## Test Strategy

- **Manual CI validation:** Push the fix branch and observe the GitHub Actions run. Both the "Set up Node.js" cache step (frontend) and the "Set AKS context" step (backend) should pass without errors.
- **Dry-run / syntax check:** Use `actionlint` locally or via a linting action to validate the workflow YAML before pushing.
- **Smoke test:** If Azure credentials are available in the test environment, confirm the full deploy pipeline completes end-to-end.

## Edge Cases

- If `frontend/vue-app/package-lock.json` does not yet exist in the repo (only `package.json` is listed in the repo structure), the cache step will still fail. In that case, either run `npm install` in the frontend job before the cache step, or remove the `cache-dependency-path` constraint and let setup-node find the lock file automatically after install.
- If the project enforces SHA pinning for all third-party actions (common in security-conscious repos), the implementer must look up and verify the exact SHA for the chosen `aks-set-context` tag rather than using the tag name directly.
- Confirm no other jobs or steps in `deploy.yml` reference the broken SHA or wrong cache path.
