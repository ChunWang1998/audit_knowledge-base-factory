# lending / validation-missing

- Count: `5`
- Definition: required checks are absent or insufficient before critical state transitions or external calls.

## [Beraborrow][M-11] InfraredCollateralVault::rebalance() can DoS protocol
- Severity: `Medium`
- Source: [Issue #56](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/56)
- Impact: `dos`

### Detailed Content
- Summary: `InfraredCollateralVault::rebalance()` decreases the sent currency without bounding it to currently unlocked balance.
- Root Cause: validation missing on rebalance amount before subtracting balances that exclude future-emission allocations.
- Attack Path: attacker front-runs admin rebalance with withdrawal in the outgoing token so rebalance consumes too much; later `totalAssets()` unlocked-balance math underflows.
- Impact Detail: protocol-wide DoS because core paths depend on these accounting reads and revert after underflow.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-10] Unenforced `maxFee` and `ttl` in `sendMsg`
- Severity: `Medium`
- Source: [Issue #317](https://github.com/sherlock-audit/2025-07-malda-judging/issues/317)
- Impact: `functional-break`

### Detailed Content
- Summary: Everclear netting flow requires `maxFee == 0` and `ttl == 0`, but `EverclearBridge.sendMsg` accepted arbitrary values.
- Root Cause: decoded `IntentParams` are forwarded to `everclearFeeAdapter.newIntent(...)` without protocol-side enforcement of documented invariants.
- Trigger Conditions: rebalancer submits a message with non-zero fee/ttl; message passes existing token/destination checks but violates netting constraints.
- Impact Detail: intent can be routed to unsupported solver pathway or otherwise misprocessed, breaking intended rebalance execution guarantees.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-12] Rebalancer can drain market funds via excessive bridge fees
- Severity: `Medium`
- Source: [Issue #686](https://github.com/sherlock-audit/2025-07-malda-judging/issues/686)
- Impact: `fund-loss`

### Detailed Content
- Summary: semi-trusted `REBALANCER_EOA` can set arbitrarily high `maxFee` in bridge intent payload.
- Root Cause: `Rebalancer.sendMsg` forwards unchecked blob; `EverclearBridge.sendMsg` decodes and relays `maxFee` without protocol max bound.
- Attack Path: extract market liquidity, set amount (e.g. 10 WETH) and extreme `maxFee` (e.g. 9.9 WETH), bridge executes with most value consumed by fees.
- Impact Detail: slow but repeatable permanent fund drain from market pools, violating trust model that rebalancer cannot transfer user value.

### Fix Status
- `Fixed/Resolved in report`

## [Native-V2][M-10] Valid trades fail due to incorrect slippage validation
- Severity: `Medium`
- Source: [Issue #124](https://github.com/sherlock-audit/2025-05-native-smart-contract-v2-judging/issues/124)
- Impact: `functional-break`

### Detailed Content
- Summary: external swap success condition checked output against quoted `buyerTokenAmount` instead of caller-defined minimum.
- Root Cause: `ExternalSwap.externalSwap` used overly strict comparator and ignored `amountOutMinimum` semantics already enforced at router layer.
- Trigger Conditions: market moves slightly between quote and execution; output remains above user min but below original expected amount.
- Impact Detail: economically valid trades revert, causing user-visible routing failures and unnecessary transaction loss.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][H-10] Malicious user can alter `TradeType` to steal funds
- Severity: `High`
- Source: [Issue #715](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/715)
- Impact: `fund-loss`

### Detailed Content
- Summary: redemption logic assumes exact trade mode constraints, but user-supplied `TradeParams.tradeType` can violate those assumptions.
- Root Cause: missing enforcement that redemption should sell full secondary token balance using exact-in semantics in `_executeRedemptionTrades`.
- Attack Path: attacker crafts trade mode/path (including adapters with flexible calldata) so approval/amount behavior diverges from intended flow and extracts value.
- Impact Detail: direct theft from strategy vault or withdrawal request manager under manipulated redemption execution.

### Fix Status
- `Fixed/Resolved in report`
