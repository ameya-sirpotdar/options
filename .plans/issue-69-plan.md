# Implementation Plan: Fix package-lock.json Out of Sync (#69)

## Approach

The root cause is straightforward: `frontend/vue-app/package.json` references Playwright packages that are not reflected in `frontend/vue-app/package-lock.json`. The fix is to regenerate the lock file by running `npm install` inside `frontend/vue-app/`, then commit the updated `package-lock.json`.

No code changes are required — this is purely a dependency lock file regeneration.

## Files to Modify

### `frontend/vue-app/package-lock.json`
- Regenerate by running `npm install` in `frontend/vue-app/`
- This will add the missing entries for:
  - `@playwright/test@1.58.2`
  - `playwright@1.58.2`
  - `playwright-core@1.58.2`
  - `fsevents@2.3.2` (macOS-specific optional dep)
- The lock file version, integrity hashes, and resolved URLs for all new packages will be populated

## Implementation Steps

1. **Check out the repository** on a machine with Node.js installed (matching the version used in CI — check `.github/workflows/deploy.yml` for the Node version)
2. **Navigate to the frontend directory**:
   ```bash
   cd frontend/vue-app
   ```
3. **Regenerate the lock file**:
   ```bash
   npm install
   ```
   This reads `package.json`, resolves all dependencies (including the new Playwright ones), and writes an updated `package-lock.json`.
4. **Verify the lock file is now in sync**:
   ```bash
   npm ci
   ```
   This should complete without errors.
5. **Verify Playwright entries are present** in the new lock file:
   ```bash
   grep -c 'playwright' package-lock.json
   ```
   Should return a non-zero count.
6. **Commit and push** the updated `package-lock.json`:
   ```bash
   git add frontend/vue-app/package-lock.json
   git commit -m "fix: regenerate package-lock.json to include Playwright deps"
   git push
   ```

## Test Strategy

- The primary validation is that the `Deploy Frontend` GitHub Actions job passes `npm ci` without errors
- Locally, running `npm ci` in `frontend/vue-app/` after the fix should exit with code 0
- Optionally run `npm run test` (Vitest unit tests) to confirm no regressions

## Edge Cases to Handle

- **Node version mismatch**: Ensure the Node.js version used to regenerate the lock file matches what CI uses (check `deploy.yml`). A mismatch can cause subtle differences in resolved package versions.
- **`fsevents` platform dependency**: `fsevents` is macOS-only. If regenerating on Linux/Windows, it may appear as an optional dependency with `"optional": true` — this is expected and correct.
- **Lock file format version**: Ensure `lockfileVersion` in the regenerated file matches what the CI Node version expects (v2 or v3). `npm install` will use the version appropriate for the installed npm.
- **No unintended upgrades**: After running `npm install`, review the diff to confirm only Playwright-related entries were added and no other packages were inadvertently upgraded.
