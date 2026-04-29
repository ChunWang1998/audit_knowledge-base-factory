# lending / malda - Fixed Medium Issues

- Count: `7`
- Source report: `Malda.pdf`

## [M-10] Unenforced `max Fee` and `ttl` in `send Msg`
- Severity: `Medium`
- Root-cause: `validation-missing`, `bridge-integration`
- Impact: `functional-break`
- Source: [Sherlock Issue #317](https://github.com/sherlock-audit/2025-07-malda-judging/issues/317)

### Detailed Content
Everclear netting path requires `maxFee == 0` and `ttl == 0`, but bridge message path did not enforce those constraints.  
Non-zero values can route to unsupported solver pathway and break intended cross-chain behavior.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-11] Missing endpoint to trigger `liquidate External` from extension chain
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `functional-break`
- Source: [Sherlock Issue #370](https://github.com/sherlock-audit/2025-07-malda-judging/issues/370)

### Detailed Content
Host chain had liquidation execution path, but gateway lacked endpoint/data path for extension-chain callers to target borrower liquidation.  
Result: some expected liquidation flows were impossible, especially under permission constraints.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [malda-lending/pull/106](https://github.com/malda-protocol/malda-lending/pull/106/files)

## [M-12] Rebalancer can drain market funds via excessive bridge fees
- Severity: `Medium`
- Root-cause: `validation-missing`, `bridge-integration`
- Impact: `fund-loss`
- Source: [Sherlock Issue #686](https://github.com/sherlock-audit/2025-07-malda-judging/issues/686)

### Detailed Content
`REBALANCER_EOA` could pass unchecked message data, including extreme `maxFee`, to Everclear adapter.  
This allows repeated value extraction via excessive bridge fees, violating trust assumptions that rebalancer cannot transfer user value.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-13] `wrap And Supply On Extension Market` blocks host supply when gas Fee set
- Severity: `Medium`
- Root-cause: `state-machine-flow`
- Impact: `functional-break`
- Source: [Sherlock Issue #741](https://github.com/sherlock-audit/2025-07-malda-judging/issues/741)

### Detailed Content
Wrap helper consumed all `msg.value` during wrapping and left no value for gateway `gasFee` in same transaction.  
When gas fee is non-zero, flow reverts and core wrap+supply user path breaks.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-14] Mixed Price Oracle V4 decimal mismatch causes wrong branch / Do S risk
- Severity: `Medium`
- Root-cause: `oracle-decimals`
- Impact: `dos`, `value-mispricing`
- Source: [Sherlock Issue #945](https://github.com/sherlock-audit/2025-07-malda-judging/issues/945)

### Detailed Content
API3 and eOracle feeds can use different decimals, but delta comparison logic treated values as if same scale.  
This can bias feed selection, break expected staleness/delta behavior, and in edge cases trigger broader protocol instability.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-15] Across bridge failure locks funds
- Severity: `Medium`
- Root-cause: `bridge-integration`
- Impact: `locked-funds`
- Source: [Sherlock Issue #1309](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1309)

### Detailed Content
Across refund path returns failed transfer funds to depositor. Depositor was set to rebalancer contract without proper recovery flow.  
If fill fails/intent expires, refunded tokens become trapped and not routed back to market/users.

### Actual Fix
- Status: `Fixed/Resolved in report`

## [M-16] Bridges do not support all listed assets
- Severity: `Medium`
- Root-cause: `bridge-integration`
- Impact: `functional-break`
- Source: [Sherlock Issue #1477](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1477)

### Detailed Content
Protocol declared support for asset set that selected bridges (Across/Everclear) could not actually transfer.  
Affected markets could not be rebalanced, creating operational dead-ends.

### Actual Fix
- Status: `Fixed/Resolved in report`
- PR: [malda-lending/pull/100](https://github.com/malda-protocol/malda-lending/pull/100)
