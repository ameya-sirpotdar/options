# Implementation Plan: Fix SWA Deploy to Serve Built Dist Output

## Approach

The Azure Static Web Apps GitHub Action behaves differently when `skip_app_build: true` is set — it uploads directly from `app_location` rather than combining `app_location` + `output_location`. The current config points `app_location` at the Vue source directory, so raw source files are served instead of the Vite-built assets.

The fix is a two-line change in `.github/workflows/deploy.yml`:
- Set `app_location` to `frontend/vue-app/dist` (the Vite build output directory)
- Set `output_location` to `""` (empty, since we're pointing directly at the built output)
- Leave `skip_app_build: true` unchanged

## Files to Modify

### `.github/workflows/deploy.yml`

Locate the SWA deploy step (likely using `Azure/static-web-apps-deploy@v1` or similar action) and update the `with:` block:

```yaml
# Before
app_location: frontend/vue-app
output_location: dist
skip_app_build: true

# After
app_location: frontend/vue-app/dist
output_location: ""
skip_app_build: true
```

## Implementation Steps

1. Open `.github/workflows/deploy.yml`
2. Find the SWA deploy step — look for the `Azure/static-web-apps-deploy` action
3. In the `with:` block of that step, change:
   - `app_location: frontend/vue-app` → `app_location: frontend/vue-app/dist`
   - `output_location: dist` → `output_location: ""`
4. Leave all other fields (including `skip_app_build: true`, `azure_static_web_apps_api_token`, etc.) unchanged
5. Commit and push — the next workflow run will deploy the built assets

## Test Strategy

- **Post-deploy verification:** After merge and workflow run completes, `curl -sS https://lively-plant-0fa95be0f.4.azurestaticapps.net/` should return HTML containing `/assets/index-*.js` references (hashed Vite output filenames), not `/src/main.js`
- **Browser smoke test:** Navigate to the URL and confirm the page renders with header, input panel, and footer visible
- **Workflow run check:** Confirm the GitHub Actions workflow completes successfully without errors on the deploy step

## Edge Cases to Handle

- Ensure the `dist/` directory is actually built before the SWA deploy step runs — verify the workflow has a prior build step (`npm run build` or equivalent) that produces `frontend/vue-app/dist/`
- If `output_location: ""` causes any action validation warnings, an alternative is to omit the `output_location` key entirely
- Confirm `frontend/vue-app/dist` is not in `.gitignore` for the workflow context (it shouldn't be committed, but the build step must produce it in the runner's workspace before the deploy step)
