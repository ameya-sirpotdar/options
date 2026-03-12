# Implementation Plan: Remove Dead `fetchOptionsChain` Export from client.js

## Approach

Delete the `fetchOptionsChain` function (lines 11-18) from `client.js`. Since the issue confirms via grep that nothing imports this function, the removal is safe and isolated. No other files need to change.

## Files to Modify

### `frontend/vue-app/src/api/client.js`
- Remove the `fetchOptionsChain` function definition and its export
- Ensure the remaining code (axios instance setup, `pollOptions` or other exports) is intact and properly formatted
- Verify no trailing commas or syntax issues after removal

## Implementation Steps

1. Open `frontend/vue-app/src/api/client.js`
2. Locate the `fetchOptionsChain` function (lines 11-18)
3. Delete those lines entirely
4. Confirm the file still has valid JS syntax (no dangling commas, correct module exports)
5. Run a project-wide grep for `fetchOptionsChain` to confirm zero remaining references
6. Run frontend unit tests to confirm no regressions

## Test Strategy

- Run existing Vitest unit tests: `cd frontend/vue-app && npm run test:unit`
- Confirm all component and composable tests pass (BestTradeCard, InputPanel, OptionsTable, useMarketData)
- Optionally run a quick grep: `grep -r 'fetchOptionsChain' frontend/` should return no results

## Edge Cases

- Confirm `client.js` does not re-export `fetchOptionsChain` via a barrel/index file
- Confirm no dynamic import or string-based reference to `fetchOptionsChain` exists anywhere in the codebase
