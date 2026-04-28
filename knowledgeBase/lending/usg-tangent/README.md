# lending / usg-tangent - Fixed Medium Issues

- Count: `3`
- Source report: `USG - Tangent.pdf`

## [M-12] Liquidation fee computed from repaid debt instead of liquidation profit
- Severity: `Medium`
- Root-cause: `accounting-invariant`
- Impact: `value-mispricing`, `functional-break`
- Source: [Sherlock Issue #651](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/651)

### Detailed Content
Fee logic computed liquidation fee as a percentage of repaid debt rather than liquidator profit/bonus.  
This can make profitable liquidations unattractive or loss-making, reducing liquidation participation and harming market health.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-13] Delayed reward-cut parameter effect (two-cycle lag)
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `value-mispricing`, `functional-break`
- Source: [Sherlock Issue #697](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/697)

### Detailed Content
`updateRCParams()` processed rewards before persisting new params, so newly set values did not take effect on the expected next cycle.  
Effective behavior lagged by two cycles, creating governance/control mismatch and delayed policy enforcement.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-14] Edge-case USG prices can force IRCalculator-dependent reverts
- Severity: `Medium`
- Root-cause: `accounting-invariant`, `error-handling`
- Impact: `dos`
- Source: [Sherlock Issue #727](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/727)

### Detailed Content
Integer truncation in IR math could reduce an intermediate fixed-point ratio to zero near edge-case prices.  
That zero later reached logarithm path (`log_2(0)`), causing revert and blocking borrow/repay/liquidate and related flows that depend on interest-rate computation.

### Actual Fix
- Status: `Fixed/Resolved in report`
