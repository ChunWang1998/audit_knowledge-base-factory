# gas-griefing (12)

> Griefing via gas-heavy paths, routing failures, or validation gaps that block users or drain protocol funds.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

## Subcategories

| Folder | Issues | Focus |
|--------|--------|-------|
| [aggregator-routing](./aggregator-routing/) | 6 | DEX/aggregator routing, native balance, weight caps, router ABI mismatch |
| [missing-checks](./missing-checks/) | 6 | Missing caller/peer validation, stale vault state, surplus DoS |

### Former folders (reclassified)

| Old folder | New location |
|------------|--------------|
| `calls-redundant` | `aggregator-routing` |
| `check-length` | `aggregator-routing` |
| `unnecessary-usage` (#3–4) | `aggregator-routing` |
| `validation-zero` (#2–3) | `aggregator-routing` |
| `doesn-pusdevault` | `missing-checks` |
| `unnecessary-usage` (#1–2, #5) | `missing-checks` |
| `validation-zero` (#1, #4) | `missing-checks` |
| `storage-reads`, `unused-remove`, `validation-weak` | removed (not in curated set) |
