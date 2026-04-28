# lending / error-handling

- Count: `2`
- Definition: error path handling is too strict or missing, causing avoidable reverts/system blockage.

## [Notional][M-25] `getWithdrawRequestValue()` revert can brick account actions
- Severity: `Medium`
- Source: [Issue #779](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/779)
- Impact: `dos`

### Detailed Content
- Summary: `getWithdrawRequestValue()` iterates all pool tokens and enforces `require(hasRequest)` for each lookup.
- Root Cause: strict all-token request assumption with no graceful handling for zero-balance tokens where request is legitimately absent.
- Trigger Conditions: one token exits with zero amount so request manager does not create request entry for that token.
- Impact Detail: valuation function reverts; dependent `price()` reads fail and can brick exit/repay/withdraw/liquidation actions for account.

### Fix Status
- `Fixed/Resolved in report`

## [USG-Tangent][M-14] Edge-case IR math reaches `log_2(0)` and reverts
- Severity: `Medium`
- Source: [Issue #727](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/727)
- Impact: `dos`

### Detailed Content
- Summary: IR calculation edge case passes zero into logarithm in fixed-point math path.
- Root Cause: integer division truncation to zero before `ABDKMath64x64.divu`/`_pow` pipeline; later `log_2(0)` hard-reverts.
- Trigger Conditions: oracle price approaches configured upper boundary where numerator is positive but smaller than denominator after integer division.
- Impact Detail: all workflows requiring `_computeIR()` can revert, creating broad temporary DoS.

### Fix Status
- `Fixed/Resolved in report`
