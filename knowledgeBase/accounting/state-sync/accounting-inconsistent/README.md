# accounting-inconsistent 

> Issues where protocol state diverged from reality due to missing updates or incorrect logic.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. An attacker can drain the entire protocol balance of sUSDe during the yield phase due to incorrect redemption accounting logic in `pUSDeVault::_withdraw`

**Severity:** 🔴 Critical  **Source:** `cyfrin/predeposit.md`

**Description:**
After entering the yield phase, `pUSDeVault::_withdraw` processes yUSDe redemptions by first computing the yield component via `previewYield(caller, shares)` and then adding it to the base `assets` parameter. This augmented total is passed as `baseAssets` to the internal `_withdraw` call, which decrements `depositedBase` by that amount. However, `depositedBase` should only be decremented by the original base asset amount, not the base plus yield. Since `previewYield` computes yield using `total_USDe - depositedBase`, each erroneous over-decrement of `depositedBase` makes the protocol perceive a larger yield on subsequent calls. This creates a feedback loop: each yUSDe redemption inflates the apparent yield for subsequent redeemers, allowing the first redeemer (or any attacker who monitors for yield accrual events) to redeem their shares for an amount of sUSDe far exceeding their actual entitlement — potentially draining the entire protocol's sUSDe balance at the expense of all other depositors.

**Impact:**
An attacker can drain the entire sUSDe balance held by the protocol, destroying the collateral backing all pUSDe and yUSDe depositors. Remaining depositors lose their principal and any accrued yield.

**Recommended Mitigation:**
Separate the yield augmentation from the base asset decrement: compute the full sUSDe amount (base + yield) for the withdrawal transfer, but pass only the original base `assets` (without yield) to the `_withdraw` call that decrements `depositedBase`. This preserves correct accounting for `depositedBase` while still paying out the user's full entitled amount.

---

**[中文版本]**

**描述：**
`pUSDeVault::_withdraw` 在处理 yUSDe 赎回时，将 `previewYield` 返回的收益加到 `assets` 后传递给内部 `_withdraw`，导致 `depositedBase` 被过度递减（本息合并减扣）。由于 `previewYield` 用 `total_USDe - depositedBase` 计算收益，每次过度减扣都会使下一次赎回看到更大的"收益"，形成正反馈循环。攻击者可通过监控收益积累事件抢先赎回，以远超其应得份额的 sUSDe 清空协议余额。

**影響：**
攻击者可以清空协议持有的全部 sUSDe，销毁所有 pUSDe 和 yUSDe 存款人的抵押品，导致剩余存款人损失本金和收益。

**修復建議：**
将收益计算与 `depositedBase` 递减解耦：计算完整的 sUSDe 转出金额（本金+收益），但传给递减 `depositedBase` 的 `_withdraw` 调用时只传原始基础资产量（不含收益）。

---

## 3. Direct amount assignment in `SherpaUSD::ownerMint`/`ownerBurn` can break accounting for `totalStaked` and `accountingSupply`

**Severity:** 🟡 Medium  **Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaUSD::ownerMint` and `ownerBurn` are operator-controlled functions for manual cross-chain rebalancing. After minting or burning tokens, each function records an approval for the vault to adjust its accounting via `approvedTotalStakedAdjustment[to] = amount` and `approvedAccountingAdjustment[to] = amount`. These are direct assignment operations (using `=`), not increments. If the operator calls `ownerMint` twice before the vault has consumed the first approval, the second call overwrites the first: the vault will only see the second mint's adjustment amount rather than the cumulative total of both mints. The first adjustment is silently lost, creating a permanent discrepancy between the actual minted amount and the recorded adjustment, corrupting `totalStaked` and `accountingSupply`.

**Impact:**
If multiple `ownerMint` or `ownerBurn` operations are performed before the vault processes them, only the most recent operation's adjustment is recorded. The vault's `totalStaked` and `accountingSupply` will diverge from the true supply, breaking yield calculations, share pricing, and rebalancing logic that depends on accurate accounting.

**Recommended Mitigation:**
Replace the direct assignments with increment/decrement operators: `approvedTotalStakedAdjustment[to] += amount` in `ownerMint` and `approvedTotalStakedAdjustment[from] -= amount` in `ownerBurn` (and equivalently for `approvedAccountingAdjustment`). This ensures pending approvals accumulate correctly across multiple calls.

---

**[中文版本]**

**描述：**
`SherpaUSD::ownerMint` 和 `ownerBurn` 使用直接赋值（`=`）而非累加（`+=`）记录待处理的会计调整。若在金库消费第一次审批前再次调用，第二次调用会覆盖第一次的记录，导致第一次铸造/销毁的调整量永久丢失，使 `totalStaked` 和 `accountingSupply` 与实际供应量产生偏差。

**影響：**
多次操作后金库的 `totalStaked` 和 `accountingSupply` 与真实值不符，破坏收益计算、份额定价和依赖准确会计的再平衡逻辑。

**修復建議：**
将 `ownerMint` 中的赋值改为 `+=`，`ownerBurn` 中改为 `-=`，确保待处理调整量跨多次调用正确累积。

---

## 4. Incomplete Transfer Classification Causes Inconsistent Limit and Tax Behavior for Wallet-to-Wallet Transfers

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
KnoxNet's transfer logic uses two independent and inconsistent binary classifications for different subsystems. The transaction limit enforcement in `_enforceTxLimit` classifies transfers based solely on whether the `sender` is a liquidity pool: if not, it applies `_maxSellTxAmount`. Separately, the tax subsystem in `_applyTax` classifies based on whether the `recipient` is a liquidity pool: if not, it applies the buy-side tax rate. This means a wallet-to-wallet transfer (where neither party is a pool) is simultaneously subject to sell-side limits and buy-side taxes. The two subsystems use opposite criteria, creating internally contradictory behavior for any non-DEX transfer. No third transfer category exists for regular wallet-to-wallet movements.

**Impact:**
Wallet-to-wallet transfers may be unexpectedly blocked by the sell-side transaction limit even though no pool interaction is occurring. When `transferTax` is enabled, the same transfers are taxed at the lower buy rate rather than a rate appropriate for direct transfers. This dual misclassification produces confusing and unpredictable behavior for users and integrators.

**Recommended Mitigation:**
Introduce a three-way transfer classification that explicitly identifies buy, sell, and wallet-to-wallet operations. Both the limit enforcement and tax subsystems should use the same classification logic to ensure consistent treatment of all transfer types.

---

**[中文版本]**

**描述：**
KnoxNet 的交易限额和税率子系统使用不同的二元分类逻辑：限额子系统基于 `sender` 是否为流动性池（非池时适用卖出限额），税率子系统基于 `recipient` 是否为流动性池（非池时适用买入税率）。钱包对钱包转账同时被当作"卖出"限额和"买入"税率处理，两个子系统标准相互矛盾。

**影響：**
钱包间转账可能被卖出限额意外阻止，或被低于应有水平的买入税率错误征税，给用户和集成方带来混乱。

**修復建議：**
引入三分类逻辑，明确区分买入、卖出和钱包对钱包转账，两个子系统使用统一的分类逻辑。

---

## 5. Inconsistent APR boundary validation between `AprPairFeed` and `Accounting`

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
`AprPairFeed` validates incoming APR data against bounds of `[-50%, +200%]`, accepting negative APR values as low as -50%. However, `Accounting::normalizeAprFromFeed` applies its own validation with bounds of `[0, 200%]`, rejecting any negative APR. When the APR feed reports a valid negative value (between -50% and 0%), the feed's validation passes, but the accounting normalization reverts with "invalid apr". This creates a scenario where the oracle can report data that the protocol considers valid at the feed level but immediately rejects during the accounting update step.

**Impact:**
When the APR feed reports a valid negative value, `normalizeAprFromFeed` reverts, blocking APR updates via `updateAprs()` and index calculations via `updateIndexes()`. This prevents proper accounting updates during deposit/withdrawal flows for the duration of the negative APR period, causing a protocol-wide DoS on yield accounting.

**Recommended Mitigation:**
Align the two contracts by either updating `Accounting`'s `APR_BOUNDARY_MIN` to match `AprPairFeed`'s `-0.5e12`, or explicitly capping negative APRs at zero in `Accounting::normalizeAprFromFeed` before processing, treating negative market APRs as zero-yield periods rather than errors.

---

**[中文版本]**

**描述：**
`AprPairFeed` 接受 `[-50%, +200%]` 范围内的 APR（含负值），而 `Accounting::normalizeAprFromFeed` 的验证边界为 `[0, 200%]`，直接拒绝负 APR。当预言机报告有效的负 APR 时，feed 层验证通过但会计层回滚，造成系统不一致。

**影響：**
负 APR 期间 `normalizeAprFromFeed` 回滚，阻塞 APR 更新和指数计算，导致存款/提款流程的会计更新全面 DoS。

**修復建議：**
统一两个合约的 APR 边界，或在 `Accounting` 中将负 APR 视为零收益期处理而非错误。

---

## 6. Inconsistent Risk Premium Validation in `Accounting` Allows Future Underflows or Zero APR

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
`Accounting::setRiskParameters` validates risk parameters by checking that the computed `risk < 1e18` using the current TVL at the time of configuration. However, TVL can change after configuration, so the risk value is not static — it depends on the current TVL ratio. If TVL changes such that `risk` increases to `1e18` or above, two problems emerge in `Accounting::updateIndexes`: when `risk == 1e18`, the expression `UD60x18.wrap(1e18) - risk` evaluates to zero, making `aprSrt1` zero and potentially zeroing senior APR; when `risk > 1e18`, the subtraction underflows and reverts. The one-time validation at configuration time provides no ongoing protection against this.

**Impact:**
If risk exceeds `1e18` after TVL changes, all `updateIndexes` calls revert, blocking tranche accounting updates, deposits, withdrawals, and NAV calculations. If risk equals exactly `1e18`, senior APR is set to zero, causing seniors to receive no yield regardless of market conditions.

**Recommended Mitigation:**
In `Accounting::updateIndexes`, cap `risk` to a value strictly below `1e18` before the subtraction, or add an explicit revert with a descriptive error if `risk >= 1e18`. Optionally, compute the risk using the maximum possible TVL ratio (1.0) at configuration time to provide a stronger upfront bound.

---

**[中文版本]**

**描述：**
`Accounting::setRiskParameters` 使用当前 TVL 验证风险参数，但 TVL 变化后风险值可能超出安全范围。当 `risk == 1e18` 时，Senior APR 计算被归零；当 `risk > 1e18` 时，减法溢出导致 `updateIndexes` 回滚。单次配置时验证无法防止运行时的风险超限。

**影響：**
TVL 变化后若风险超过 `1e18`，所有会计更新操作回滚，阻塞存款、提款和 NAV 计算；若风险等于 `1e18`，Senior 收益率被归零。

**修復建議：**
在 `updateIndexes` 中对 `risk` 进行上限约束，或在超限时以描述性错误显式回滚，可选地在配置时用最大 TVL 比率（1.0）预先计算上界。

---

## 7. Inconsistent State Change in `autoRefund()` Affects TGE Unlock and Price Logic

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
The `BondingCurve::autoRefund()` function is designed to refund bonded tokens to users when the soft cap has not been reached. On refund, the function should restore the available token pool by reducing `totalProjectTokenSold` (the amount of tokens sold so far). Instead, it incorrectly adds the refunded token claims back to `tokenToSell` — the fixed total supply available for sale. This means `tokenToSell` grows beyond its originally intended fixed value. Every downstream calculation that uses `tokenToSell` as a denominator or reference is affected: the bonding curve pricing formula uses `tokenToSell` to compute the position ratio, TGE unlock percentages are calculated using `tokenToSell`, and the `_inverseArea0` function uses `sellableSupply` (derived from `tokenToSell`) for inverse curve calculations.

**Impact:**
After `autoRefund()` is called, the effective sale cap appears inflated, prices on the bonding curve become too high (the position ratio denominator is larger than intended), TGE unlock amounts are incorrectly reduced for all future buyers, and inverse curve calculations produce wrong results. The individual refund function `refund()` correctly updates only `totalProjectTokenSold`, making the two refund paths inconsistent.

**Recommended Mitigation:**
In `autoRefund()`, decrement `totalProjectTokenSold` by the total refunded claim amount instead of incrementing `tokenToSell`. This mirrors the correct behavior of the individual `refund()` function and preserves the integrity of all bonding curve calculations.

---

**[中文版本]**

**描述：**
`BondingCurve::autoRefund()` 在退款时错误地将退款的代币认领量加回 `tokenToSell`（固定销售总量），而非从 `totalProjectTokenSold`（已售量）中减去。这使 `tokenToSell` 超出其原始固定值，破坏所有使用它作为分母的下游计算：债券曲线定价、TGE 解锁金额和反向曲线计算均受影响。与之对比，用户自行调用的 `refund()` 函数正确地只更新 `totalProjectTokenSold`。

**影響：**
`autoRefund()` 执行后，有效销售上限虚增，债券曲线价格偏高，TGE 解锁量减少，所有后续购买者均受波及。

**修復建議：**
将 `autoRefund()` 中的 `strg.ledger.tokenToSell += totalClaimAmount` 改为 `strg.ledger.totalProjectTokenSold -= totalClaimAmount`，与 `refund()` 的正确逻辑保持一致。

---

## 8. Inconsistent pause functionality allows certain state-changing operations when contract is paused

**Severity:** 🟡 Medium  **Source:** `cyfrin/cryptoart.md`

**Description:**
`CryptoartNFT` uses OpenZeppelin's `PausableUpgradeable` to implement an emergency pause mechanism. While minting and burning are properly protected with the `whenNotPaused` modifier, several other state-changing functions lack this protection. These include token transfers and approvals (inherited from ERC-721), metadata management functions (`updateMetadata`, `pinTokenURI`, `markAsRedeemable`), and story-related functions (`addCollectionStory`, `addCreatorStory`, `addStory`, `toggleStoryVisibility`). During an emergency pause — typically triggered by a security incident or upgrade — users can still perform these operations, potentially creating inconsistent state that complicates recovery or upgrade procedures.

**Impact:**
During a pause period intended to freeze the contract state, users can still transfer tokens, modify metadata, and add story entries. This can lead to unexpected state changes during contract upgrades or emergency situations, undermining the intent of the pause mechanism.

**Recommended Mitigation:**
Add the `whenNotPaused` modifier to all state-changing functions, including token transfer hooks and all metadata management and story functions, to ensure that the pause mechanism comprehensively freezes contract state.

---

**[中文版本]**

**描述：**
`CryptoartNFT` 的暂停机制只保护了铸造和销毁操作，但代币转账、授权、元数据管理（`updateMetadata`、`pinTokenURI`、`markAsRedeemable`）和故事相关函数（`addCollectionStory` 等）均未添加 `whenNotPaused` 修饰符。紧急暂停期间，用户仍可执行这些状态变更操作。

**影響：**
紧急暂停期间产生意外的状态变更，使合约升级或安全恢复复杂化，削弱暂停机制的保护意图。

**修復建議：**
为所有状态变更函数（包括代币转账钩子和元数据/故事函数）添加 `whenNotPaused` 修饰符，确保暂停机制全面冻结合约状态。
---

## 11. Incorrect yield accounting when `_payNodeOperatorFees` reverts in `LidoStVaultYieldProvider::reportYield`

**Severity:** 🟡 Medium  **Source:** `cyfrin/manager.md`

**Description:**
`LidoStVaultYieldProvider::reportYield` invokes `_payNodeOperatorFees` to distribute operator fees before reporting yield to the `YieldManager`. If `_payNodeOperatorFees` reverts — for example due to insufficient funds to pay operators — the parent `reportYield` function catches or continues without the fee payment but still updates `userFunds` as if the full fee had been paid. Because operator fees are deducted from yield before crediting users, silently skipping the fee payment while still crediting the full yield amount causes `userFunds` to be overstated by the unpaid operator fee amount.

**Impact:**
If `_payNodeOperatorFees` reverts silently, users are credited with yield that includes unpaid operator fees. This overstates user fund balances, creating a discrepancy between the vault's real balance and its reported user funds. Subsequent withdrawals may fail or steal from other users' allocations to cover the inflated credits.

**Recommended Mitigation:**
Ensure that if `_payNodeOperatorFees` fails, the `nodeOperatorFees` value is still properly tracked and accounted for in subsequent yield or withdrawal calculations. The fix should either propagate the revert (so no yield is reported on a failed fee payment) or defer the fee payment but correctly subtract it from the user yield amount.

---

**[中文版本]**

**描述：**
`LidoStVaultYieldProvider::reportYield` 在调用 `_payNodeOperatorFees` 分配运营者费用时，若该调用回滚，父函数仍继续执行并将完整收益（包含未支付的运营者费用）记入 `userFunds`，导致用户资金虚高。

**影響：**
运营者费用支付失败后，用户被错误地计入包含未支付费用的收益，`userFunds` 与金库实际余额产生偏差，后续提款可能失败或从其他用户份额中抽取资金。

**修復建議：**
确保 `_payNodeOperatorFees` 失败时，相关费用仍被正确记录和扣除。可以选择将失败传播（中止收益报告）或延迟支付但从用户收益中正确减扣。

---

## 14. Output Accounting Uses Absolute Balance

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
In `CoreAggregator::_executeSwap`, after executing a sequence of swap routes, the total output amount is computed by reading the contract's entire current balance of the output token: `totalAmountOut = IERC20(params.tokenOut).balanceOf(address(this))`. This includes any tokens that were present in the contract before the current swap — from prior transactions, accidental direct transfers, or third-party deposits. By using the absolute balance rather than the delta (balance-after minus balance-before), the swap output accounting is inflated. The caller can receive tokens that do not belong to the current swap's output.

**Impact:**
Users who call the aggregator may receive more tokens than the swap actually produced, drawing from pre-existing contract balances. This drains reserves belonging to other users or operations and can be exploited by any party that knows the contract holds a balance of the output token before calling the swap.

**Recommended Mitigation:**
Use delta accounting: capture the output token balance before executing the swap routes, then compute the actual output as `balanceAfter - balanceBefore`. This ensures only the tokens generated by the current swap are credited to the caller, regardless of any pre-existing balance.

---

**[中文版本]**

**描述：**
`CoreAggregator::_executeSwap` 通过读取合约当前全部余额来计算交换输出量，而非计算本次交换产生的增量。合约在交换前持有的任何代币（来自历史操作、意外转入或第三方存款）都会被计入输出，使调用者能获取不属于本次交换的代币。

**影響：**
调用者可能获得超过本次交换实际产出的代币，从合约预存余额中提取资金，损害其他用户或操作。

**修復建議：**
使用增量会计：在执行交换路由前记录输出代币余额，之后以"后-前"差值计算实际输出，确保只有本次交换产生的代币归入调用者。
