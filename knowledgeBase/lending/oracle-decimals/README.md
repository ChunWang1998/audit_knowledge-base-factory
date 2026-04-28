# lending / oracle-decimals

- Count: `2`
- Definition: oracle values from different feeds/scales are compared or consumed without normalization.

## [Malda][M-14] MixedPriceOracleV4 decimal mismatch
- Severity: `Medium`
- Source: [Issue #945](https://github.com/sherlock-audit/2025-07-malda-judging/issues/945)
- Impact: `dos`, `value-mispricing`

### Detailed Content
- Summary: oracle aggregator compares API3 and eOracle prices directly although feeds can return different decimal precision.
- Root Cause: `_getLatestPrice` computes absolute delta and bps delta before normalizing feed scales.
- Trigger Conditions: one feed uses larger decimals; raw numeric delta appears inflated and branch logic disproportionately prefers one source.
- Impact Detail: wrong oracle branch selection and stale/delta checks can misbehave, leading to mispricing and potential DoS side effects.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-12] `PendlePTOracle._getPTRate` decimal assumption invalid
- Severity: `Medium`
- Source: [Issue #623](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/623)
- Impact: `value-mispricing`

### Detailed Content
- Summary: `PendlePTOracle._getPTRate` comment/logic assumed PT rate always `1e18`.
- Root Cause: `getPtToAssetRate` is `1e18`-scaled, but `getPtToSyRate` can be higher-scale in specific markets; code converts directly without normalization.
- Trigger Conditions: markets where SY rate decimals differ from assumed 18.
- Impact Detail: PT valuation is skewed, which propagates to collateral/pricing decisions.

### Fix Status
- `Fixed/Resolved in report`
