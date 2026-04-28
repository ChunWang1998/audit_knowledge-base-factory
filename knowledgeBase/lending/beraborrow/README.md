# lending / beraborrow - Fixed Medium Issues

- Count: `4`
- Source report: `Beraborrow.pdf`

## [M-10] InternalizeDonations will never work for asset token
- Severity: `Medium`
- Root-cause: `accounting-invariant`
- Impact: `locked-funds`, `functional-break`
- Source: [Sherlock Issue #43](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/43)

### Detailed Content
The vault calculates donation amount as on-contract token balance minus virtual accounting balance.  
For the main asset, real balance can be near zero because funds are staked externally, while virtual balance remains high. This can underflow and revert in `internalizeDonations` / `receiveDonations`, so donated funds can become stuck.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [blockend/pull/176](https://github.com/Beraborrowofficial/blockend/pull/176)

## [M-11] InfraredCollateralVault::rebalance() can DoS protocol
- Severity: `Medium`
- Root-cause: `validation-missing`
- Impact: `dos`
- Source: [Sherlock Issue #56](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/56)

### Detailed Content
`rebalance()` can consume more than current unlocked balance (including amounts reserved for future emissions).  
An attacker can front-run admin rebalance with withdrawals, causing underflow in unlocked-balance math and making core protocol operations revert.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [blockend/pull/174](https://github.com/Beraborrowofficial/blockend/pull/174)

## [M-13] Missing slippage control for router actions
- Severity: `Medium`
- Root-cause: `slippage-protection`
- Impact: `fund-loss`
- Source: [Sherlock Issue #91](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/91)

### Detailed Content
Some router paths validate slippage only for unwrapped flow.  
When collateral redemption output depends on price movement but no min-out style check exists, users can receive significantly worse redemption amounts during volatility.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [blockend/pull/172](https://github.com/Beraborrowofficial/blockend/pull/172)

## [M-15] Double performance fee on donations when oracle is added
- Severity: `Medium`
- Root-cause: `accounting-invariant`
- Impact: `fund-loss`, `value-mispricing`
- Source: [Sherlock Issue #125](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/125)

### Detailed Content
Donation flow for token without oracle and later internalization after oracle mapping can apply performance fee twice.  
This double-charges escrowed value and reduces user/protocol value unexpectedly.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [blockend/pull/175](https://github.com/Beraborrowofficial/blockend/pull/175)
