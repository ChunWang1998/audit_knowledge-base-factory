# lending / native-v2 - Fixed Medium Issues

- Count: `1`
- Source report: `Native Smart Contract V2.pdf`

## [M-10] Valid trades fail due to incorrect slippage validation
- Severity: `Medium`
- Root-cause: `slippage-protection`, `validation-missing`
- Impact: `functional-break`
- Source: [Sherlock Issue #124](https://github.com/sherlock-audit/2025-05-native-smart-contract-v2-judging/issues/124)

### Detailed Content
External swap path compared output amount against `buyerTokenAmount` instead of user-provided `amountOutMinimum`.  
Trades that satisfy user slippage tolerance could still revert, breaking valid routing behavior and reducing router usability during normal price movement.

### Actual Fix
- Status: `Fixed/Resolved in report`
- Commit: [6745b1d](https://github.com/Native-org/v2-core/commit/6745b1deb50eda266ebcc4d724cff0c79448df83)
