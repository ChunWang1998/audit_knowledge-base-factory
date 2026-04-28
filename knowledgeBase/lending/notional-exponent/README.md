# lending / notional-exponent - Fixed Medium/High Issues

- Count: `11`
- Source report: `Notional Exponent.pdf`

## [H-10] Malicious user can alter `TradeType` to steal funds
- Severity: `High`
- Root-cause: `validation-missing`
- Impact: `fund-loss`
- Source: [Sherlock Issue #715](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/715)

### Detailed Content
Redemption trade path expected strict trade mode assumptions, but user-controlled trade parameters could violate those assumptions.  
With crafted trade type/path, attacker could manipulate swap/approval behavior and extract value from vault/withdraw flows.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [H-11] Missing slippage protection in expired PT redemption
- Severity: `High`
- Root-cause: `slippage-protection`
- Impact: `fund-loss`
- Source: [Sherlock Issue #874](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/874)

### Detailed Content
Expired PT redemption path called `sy.redeem(..., minTokenOut = 0, ...)`.  
No minimum output guard allows severe unfavorable execution (including MEV/slippage) during conversion, creating direct user value loss.

### Actual Fix
- Status: `Acknowledged in report (see note in source report)`

## [M-10] Incorrect ETH/WETH asset matching can DoS exit flow
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `dos`
- Source: [Sherlock Issue #581](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/581)

### Detailed Content
Exit logic attempted to skip swap for primary asset by comparing token addresses directly.  
When strategy asset is WETH but pool emits native ETH token marker, mismatch triggers wrong path and can revert/DoS exit workflows.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-11] Rewards claim missing for Curve Gauge staking path
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `functional-break`
- Source: [Sherlock Issue #595](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/595)

### Detailed Content
Reward manager handled Convex reward pool path, but gauge-only path early-returned when reward pool address is zero.  
Users with gauge-staked LP could not realize accrued rewards.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [notional-v4/pull/28](https://github.com/notional-finance/notional-v4/pull/28)

## [M-12] `PendlePTOracle._getPTRate` decimal assumption invalid
- Severity: `Medium`
- Root-cause: `oracle-decimals`
- Impact: `value-mispricing`
- Source: [Sherlock Issue #623](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/623)

### Detailed Content
Code assumed PT rate always 1e18, but `getPtToSyRate` can return different scales in some markets.  
Incorrect scaling creates price distortions and can misprice positions.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-13] ERC20 `approve` incompatibility with USDT-style tokens
- Severity: `Medium`
- Root-cause: `approval-compatibility`
- Impact: `functional-break`
- Source: [Sherlock Issue #652](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/652)

### Detailed Content
Several paths used strict `ERC20(token).approve(...)` assumptions incompatible with non-standard ERC20 return behavior.  
On tokens like USDT, approval interactions can revert and block migration/supply/staking flows.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-14] Etherna withdrawal request valuation is incorrect
- Severity: `Medium`
- Root-cause: `state-machine-flow`, `accounting-invariant`
- Impact: `value-mispricing`
- Source: [Sherlock Issue #665](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/665)

### Detailed Content
Withdrawal request valuation used yield-token market pricing in cases where underlying redemption amount was already fixed.  
This introduces valuation error, especially for cooldown assets whose final amount is deterministic.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-17] User cannot migrate in edge case
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `functional-break`
- Source: [Sherlock Issue #674](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/674)

### Detailed Content
Migration always passed `assetToRepay = type(uint256).max` and relied on repay-share inference path.  
For accounts with no debt, derived values could break flow assumptions and prevent successful migration.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-22] WETH + native ETH Curve pool setup can cause user loss
- Severity: `Medium`
- Root-cause: `state-machine-flow`, `accounting-invariant`
- Impact: `fund-loss`
- Source: [Sherlock Issue #708](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/708)

### Detailed Content
Specific pool/token setup (asset WETH with native ETH in pool) created inconsistent handling across enter/exit/withdraw workflows.  
Under these flows, value accounting and token treatment could diverge and produce user loss.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-23] Unable to support Curve pool with native ETH
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `functional-break`
- Source: [Sherlock Issue #717](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/717)

### Detailed Content
Address rewrite of ALT ETH/native ETH markers interacted poorly with downstream token loops and value lookup logic.  
Pools containing native ETH became unsupported in certain valuation/withdraw paths.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-25] Revert in `getWithdrawRequestValue()` can brick account actions
- Severity: `Medium`
- Root-cause: `error-handling`
- Impact: `dos`
- Source: [Sherlock Issue #779](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/779)

### Detailed Content
`getWithdrawRequestValue()` used strict `require(hasRequest)` while iterating all pool tokens.  
If one token had no request (e.g., zero exit balance case), valuation reverts and blocks dependent operations like exit/repay/liquidation.

### Actual Fix
- Status: `Fixed/Resolved in report`
