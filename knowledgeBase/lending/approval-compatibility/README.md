# lending / approval-compatibility

- Count: `1`
- Definition: token approval flow assumes ERC20 behavior that is not universal.

## [Notional][M-13] ERC20 `approve` incompatibility with USDT-style tokens
- Severity: `Medium`
- Source: [Issue #652](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/652)
- Impact: `functional-break`

### Detailed Content
- Summary: several routers/strategies call high-level `ERC20(...).approve(...)` expecting standard boolean return behavior.
- Root Cause: non-standard tokens (e.g., USDT-style implementations) do not follow canonical return conventions, causing decode/revert issues.
- Affected Flow Examples: enter/migrate router path, collateral supply to Morpho path, staking/withdraw-request manager approval path.
- Impact Detail: approvals fail on major tokens, blocking migration, collateral supply, and staking operations.

### Fix Status
- `Fixed/Resolved in report`
