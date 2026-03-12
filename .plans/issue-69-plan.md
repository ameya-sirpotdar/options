# Implementation Plan: Fix package-lock.json Out of Sync (Issue #69)

## Approach

The root cause is simple: `package.json` was updated with Playwright dependencies in PR #68 but `package-lock.json` was not regenerated. The fix is to run `npm install` in the `frontend/vue-app/` directory to regenerate the lock file with all required entries.

## Files to Modify

### `frontend/vue-app/package-lock.json`
- Regenerate by running `npm install` in `frontend/vue-app/`
- This will add the missing entries for:
  - `@playwright/test@1.58.2`
  - `playwright@1.58.2`
  - `playwright-core@1.58.2`
  - `fsevents@2.3.2`

## Implementation Steps

1. Navigate to `frontend/vue-app/` directory
2. Run `npm install` to regenerate `package-lock.json` in sync with `package.json`
3. Verify the lock file now contains entries for all four missing packages
4. Commit the updated `package-lock.json`
5. Verify the CI pipeline passes with `npm ci`

## Verification

After regenerating the lock file:
- Run `npm ci` locally in `frontend/vue-app/` to confirm it succeeds without errors
- Confirm the four previously missing packages are present in the lock file
- Confirm the Deploy Frontend GitHub Actions job passes

## Test Strategy

- The primary test is that `npm ci` completes without error in the `frontend/vue-app/` directory
- The GitHub Actions Deploy Frontend workflow should pass after the fix
- Existing unit tests (`vitest`) and e2e tests (`playwright`) should continue to run as before

## Edge Cases

- Ensure `npm install` is run with the same Node.js version used in CI to avoid lock file format discrepancies
- Do not run `npm update` — only `npm install` to avoid unintentionally upgrading other dependencies
- Confirm `.gitignore` in `frontend/vue-app/` does not exclude `package-lock.json` (it should not)
