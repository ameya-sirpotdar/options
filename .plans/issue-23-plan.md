# Implementation Plan — Issue #23: Fix Bicep Output Name Mismatches & Reduce AKS Node Count

## Approach

Three precise edits across two files:
1. Correct the AKS output reference in `main.bicep` (`clusterId` → `clusterName`).
2. Correct the Storage output reference in `main.bicep` (`tableStorageEndpoint` → `tableServiceEndpoint`).
3. Change the default `aksNodeCount` parameter value from `2` to `1` in `main.bicep`.
4. Update the example parameter file `main.bicepparam.example` to reflect `aksNodeCount = 1`.

No new modules, resources, or logic are introduced — these are purely correctness and cost-optimisation fixes.

---

## Files to Modify

### `infra/bicep/main.bicep`

**Change 1 — Fix AKS output reference (~line 72)**
```bicep
// BEFORE
output aksClusterId string = aks.outputs.clusterId

// AFTER
output aksClusterId string = aks.outputs.clusterName
```
*(If the output is surfaced under a different local name, adjust accordingly — the key fix is replacing `.clusterId` with `.clusterName` to match what `modules/aks.bicep` actually exports.)*

**Change 2 — Fix Storage output reference (~line 78)**
```bicep
// BEFORE
output tableStorageEndpoint string = storage.outputs.tableStorageEndpoint

// AFTER
output tableStorageEndpoint string = storage.outputs.tableServiceEndpoint
```
*(The local output name in main.bicep can stay the same; only the right-hand reference into `storage.outputs` needs correcting.)*

**Change 3 — Reduce default aksNodeCount**
```bicep
// BEFORE
param aksNodeCount int = 2

// AFTER
param aksNodeCount int = 1
```

### `infra/bicep/main.bicepparam.example`

**Change 4 — Update example node count**
```bicep
// BEFORE
aksNodeCount: 2

// AFTER
aksNodeCount: 1
```

---

## Implementation Steps

1. Open `infra/bicep/main.bicep`.
2. Locate the `aksNodeCount` parameter declaration and change the default from `2` to `1`.
3. Locate the output that references `aks.outputs.clusterId` and change it to `aks.outputs.clusterName`.
4. Locate the output that references `storage.outputs.tableStorageEndpoint` and change it to `storage.outputs.tableServiceEndpoint`.
5. Save `main.bicep`.
6. Open `infra/bicep/main.bicepparam.example`.
7. Find the `aksNodeCount` value and change it from `2` to `1`.
8. Save `main.bicepparam.example`.
9. (Optional but recommended) Run `az bicep build --file infra/bicep/main.bicep` locally or in CI to confirm the template compiles without errors.

---

## Test Strategy

- **Bicep lint/build**: Run `az bicep build --file infra/bicep/main.bicep` — must complete with zero errors.
- **What-if deployment** (if Azure credentials available in CI): `az deployment group what-if` against a dev resource group to confirm the template resolves all output references correctly.
- **Manual cross-check**: Verify `modules/aks.bicep` exports `clusterName` (and not `clusterId`) and `modules/storage.bicep` exports `tableServiceEndpoint` (and not `tableStorageEndpoint`) to confirm the fixes align with the actual module definitions.

---

## Edge Cases

- If `main.bicep` uses the AKS `clusterId` output downstream (e.g., passed to another module or used in a `dependsOn`), ensure those references are also updated or that `clusterName` is the correct substitute for the intended purpose.
- If any existing `.bicepparam` files (not just the example) hard-code `aksNodeCount: 2`, those should also be updated — though only the example file is listed in the repo.
- The local output name in `main.bicep` (e.g., `output tableStorageEndpoint`) can remain unchanged; only the right-hand module reference needs fixing.
