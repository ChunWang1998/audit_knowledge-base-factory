# lending / slippage-protection

- Count: `3`
- Definition: price-sensitive exchange/redemption path lacks proper min-out protection.

## [Beraborrow][M-13] Missing slippage control for router actions
- Severity: `Medium`
- Source: [Issue #91](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/91)
- Impact: `fund-loss`

### Detailed Content
- Summary: router applied slippage checks only when collateral was unwrapped, leaving other redemption modes unchecked.
- Root Cause: output amount validation was conditionally enforced based on action mode, not on whether price-sensitive conversion occurred.
- Attack/Trigger Path: user redeems without unwrap during adverse price move; returned collateral deviates heavily from user expectation.
- Impact Detail: users can suffer material value loss despite using router flow that appears protected.

### Fix Status
- `Fixed/Resolved in report`

## [Native-V2][M-10] Valid trades fail due to incorrect slippage validation
- Severity: `Medium`
- Source: [Issue #124](https://github.com/sherlock-audit/2025-05-native-smart-contract-v2-judging/issues/124)
- Impact: `functional-break`

### Detailed Content
- Summary: external swap path compared received amount to quoted buyer amount instead of caller minimum-out threshold.
- Root Cause: validation duplicated and tightened the wrong invariant at lower layer, conflicting with router-level slippage contract.
- Trigger Conditions: execution output drops below quote but remains above `amountOutMinimum`.
- Impact Detail: valid trades revert, increasing failed transactions and reducing execution reliability.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][H-11] Missing slippage protection in expired PT redemption
- Severity: `High`
- Source: [Issue #874](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/874)
- Impact: `fund-loss`

### Detailed Content
- Summary: expired PT redemption calls `sy.redeem(..., minTokenOut: 0, ...)` in both instant redemption and withdraw-initiation paths.
- Root Cause: no user/system-specified minimum output protection in redemption path when SY performs external swap.
- Attack/Trigger Path: during redemption, adverse DEX price movement or MEV causes poor fill while call still succeeds due to zero bound.
- Impact Detail: direct user fund loss with no on-chain guardrail; issue was acknowledged in report at that time.

### Fix Status
- `Acknowledged in report (not fixed at that time)`
