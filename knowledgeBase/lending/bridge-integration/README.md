# lending / bridge-integration

- Count: `4`
- Definition: bridge adapter assumptions do not match actual bridge behavior/constraints.

## [Malda][M-10] Unenforced `maxFee` and `ttl` in `sendMsg`
- Severity: `Medium`
- Source: [Issue #317](https://github.com/sherlock-audit/2025-07-malda-judging/issues/317)
- Impact: `functional-break`

### Detailed Content
- Summary: netting-mode intent in Everclear requires `maxFee=0` and `ttl=0`, but bridge adapter accepted arbitrary values from decoded payload.
- Root Cause: `sendMsg` validated token/destination but did not enforce netting-specific protocol constraints before calling `newIntent`.
- Trigger Conditions: rebalancer submits non-zero fee/ttl in `_message`; transaction remains syntactically valid.
- Impact Detail: rebalance can be sent through unsupported solver semantics or misrouted, reducing cross-chain reliability.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-12] Excessive bridge fee can drain market funds
- Severity: `Medium`
- Source: [Issue #686](https://github.com/sherlock-audit/2025-07-malda-judging/issues/686)
- Impact: `fund-loss`

### Detailed Content
- Summary: bridge fee cap was effectively controlled by message payload, allowing outsized fee authorization.
- Root Cause: no protocol max bound/sanity check on `maxFee` before forwarding to external bridge fee adapter.
- Attack Path: repeated rebalance operations with extreme fee settings transfer little net value to destination while consuming source liquidity.
- Impact Detail: cumulative drain from market reserves through fee channel.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-15] Across failure locks bridged funds
- Severity: `Medium`
- Source: [Issue #1309](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1309)
- Impact: `locked-funds`

### Detailed Content
- Summary: Across refunds failed/expired deposits to depositor on origin chain; depositor was rebalancer contract.
- Root Cause: integration did not include reclaim/redispatch mechanism for refunded assets held by rebalancer.
- Trigger Conditions: relayer does not fill intent or fill expires; optimistic verification completes and refund executes.
- Impact Detail: bridge funds return to non-user-facing contract and become inaccessible to intended market flow.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-16] Bridges do not support all listed assets
- Severity: `Medium`
- Source: [Issue #1477](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1477)
- Impact: `functional-break`

### Detailed Content
- Summary: protocol asset support list and bridge-supported asset set diverged.
- Root Cause: capability matrix for Across/Everclear was not enforced at listing/rebalance routing boundary.
- Trigger Conditions: rebalance requested for listed token unsupported by selected bridge.
- Impact Detail: deterministic rebalance failure for affected markets, creating operational dead zones.

### Fix Status
- `Fixed/Resolved in report`
