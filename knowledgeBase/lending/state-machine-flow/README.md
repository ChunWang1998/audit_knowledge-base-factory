# lending / state-machine-flow

- Count: `9`
- Definition: valid system states/transitions are incomplete or inconsistent across multi-step flows.

## [Malda][M-11] Missing endpoint for extension-chain liquidation trigger
- Severity: `Medium`
- Source: [Issue #370](https://github.com/sherlock-audit/2025-07-malda-judging/issues/370)
- Impact: `functional-break`

### Detailed Content
- Summary: host-side liquidation primitive existed, but gateway did not expose equivalent extension-chain trigger carrying borrower context.
- Root Cause: interface/state transition gap between `supplyOnHost` path and `liquidateExternal` execution requirements.
- Trigger Conditions: extension chain attempts to initiate liquidation through proof-forwarder route.
- Impact Detail: critical liquidation workflow becomes unreachable for specific cross-chain execution paths.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-13] wrap+supply flow breaks with gas fee
- Severity: `Medium`
- Source: [Issue #741](https://github.com/sherlock-audit/2025-07-malda-judging/issues/741)
- Impact: `functional-break`

### Detailed Content
- Summary: helper wraps native asset using full `msg.value`, then immediately calls host supply that also requires `msg.value >= gasFee`.
- Root Cause: single-transaction value budgeting omitted reservation for gateway fee.
- Trigger Conditions: owner configures non-zero `gasFee` and user uses wrap-and-supply helper path.
- Impact Detail: wrap+supply on extension market reverts consistently, disabling a primary UX flow.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-10] Incorrect ETH/WETH matching can DoS exit flow
- Severity: `Medium`
- Source: [Issue #581](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/581)
- Impact: `dos`

### Detailed Content
- Summary: redemption flow intended to skip swap for primary token, but ETH marker and WETH address mismatch broke identity check.
- Root Cause: token comparison relied on raw address equality without canonical ETH/WETH equivalence handling across all stages.
- Trigger Conditions: strategy asset is WETH and one pool token is native ETH marker.
- Impact Detail: unnecessary/invalid trade path can execute and revert, producing exit-flow DoS.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-11] Missing gauge branch reward claim path
- Severity: `Medium`
- Source: [Issue #595](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/595)
- Impact: `functional-break`

### Detailed Content
- Summary: reward manager supports booster and gauge modes, but claim logic short-circuited when reward pool unset.
- Root Cause: gauge branch was not implemented in claim path and `rewardPool == address(0)` returned early.
- Trigger Conditions: LP is staked directly in Curve Gauge (no Convex booster path).
- Impact Detail: users accrue but cannot claim gauge rewards.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-14] Withdrawal valuation flow uses wrong pricing mode
- Severity: `Medium`
- Source: [Issue #665](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/665)
- Impact: `value-mispricing`

### Detailed Content
- Summary: once cooldown converts shares into fixed underlying amount, valuation still priced request via yield-token market value.
- Root Cause: valuation logic did not switch to deterministic-underlying mode after cooldown conversion state transition.
- Trigger Conditions: assets like USDe-style cooldown where resulting underlying is fixed and held in escrow/silo.
- Impact Detail: withdrawal request value is misstated and can propagate to risk and accounting decisions.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-17] Migration fails in debt-free edge case
- Severity: `Medium`
- Source: [Issue #674](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/674)
- Impact: `functional-break`

### Detailed Content
- Summary: migration path always passed `assetToRepay = uint256.max` and relied on debt-share derivation inside exit flow.
- Root Cause: edge case with zero borrow shares was not handled cleanly in max-sentinel repay branch.
- Trigger Conditions: user migrates collateral-only position (no debt) between routers.
- Impact Detail: migration can fail despite valid user state.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-22] WETH/native ETH setup causes loss in some exits
- Severity: `Medium`
- Source: [Issue #708](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/708)
- Impact: `fund-loss`

### Detailed Content
- Summary: for `asset=WETH` and Curve pool containing native ETH, lifecycle flows (exit/liquidation/init withdraw) use mixed wrapped/native assumptions.
- Root Cause: token-index and wrapping logic are not consistently aligned across all branches of the state machine.
- Trigger Conditions: proportional exits and request creation in this specific pool configuration.
- Impact Detail: inconsistent treatment can leak value and cause user loss.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-23] Curve pool with native ETH unsupported in valuation path
- Severity: `Medium`
- Source: [Issue #717](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/717)
- Impact: `functional-break`

### Detailed Content
- Summary: constructor rewrites Curve ALT ETH marker to internal ETH representation, but later valuation loops assume manager/request paths exist for each token uniformly.
- Root Cause: native ETH representation is not fully supported by downstream withdraw-request value retrieval flow.
- Trigger Conditions: pool includes native ETH token and code iterates token list to aggregate request values.
- Impact Detail: unsupported branch/revert behavior prevents proper pool support.

### Fix Status
- `Fixed/Resolved in report`

## [USG-Tangent][M-13] Reward cut update applies with two-cycle lag
- Severity: `Medium`
- Source: [Issue #697](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/697)
- Impact: `value-mispricing`, `functional-break`

### Detailed Content
- Summary: admin updates reward-cut params, but function processes rewards first and only then stores new params.
- Root Cause: operation ordering in `updateRCParams()` causes `lastRewardCuts` and current processing to use stale params.
- Trigger Conditions: first cycle after update still uses old cached values; effective change appears after additional cycle.
- Impact Detail: two-cycle enforcement lag creates policy-control mismatch and temporary mispricing/distribution drift.

### Fix Status
- `Fixed/Resolved in report`
