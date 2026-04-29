# accounting-inconsistent (18)

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

## 2. `Accounting::setMinimumJrtSrtRatio` sets `reserveBps` instead of `minimumJrtSrtRatio` making ratio configuration impossible

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
`Accounting::setMinimumJrtSrtRatio` is intended to configure the minimum ratio of Junior-to-Senior Tranche TVL, a critical risk management parameter. However, the function body contains an implementation error: it sets `reserveBps` instead of `minimumJrtSrtRatio`. The function even validates the input against `RESERVE_BPS_MAX` (the reserve percentage bound) rather than the appropriate ratio bound. As a result, `minimumJrtSrtRatio` can only be set during contract initialization (hardcoded to 5%) and cannot be updated afterward. Every subsequent call to `setMinimumJrtSrtRatio` silently modifies the reserve percentage instead, causing unintended reserve allocation changes while leaving the actual ratio unchanged.

**Impact:**
The protocol cannot adjust its minimum Junior-to-Senior ratio for risk management. Simultaneously, administrators calling this function to adjust the ratio will inadvertently corrupt the reserve configuration. Both the ratio and reserve settings become mismanaged, potentially compromising solvency protections.

**Recommended Mitigation:**
Fix the function to set `minimumJrtSrtRatio` instead of `reserveBps`, use an appropriate ratio bound for validation (e.g., `<= 1e18`), and emit a dedicated `MinimumJrtSrtRatioChanged` event to distinguish it from reserve changes.

---

**[中文版本]**

**描述：**
`Accounting::setMinimumJrtSrtRatio` 本应配置 Junior-to-Senior Tranche 最小 TVL 比率，但函数体错误地设置了 `reserveBps` 而非 `minimumJrtSrtRatio`，且验证逻辑使用储备比例的边界常量。`minimumJrtSrtRatio` 只能在初始化时设置（硬编码为 5%），后续所有调用都静默修改储备配置，留下风险管理漏洞。

**影響：**
协议无法调整 Junior-to-Senior 最小比率，而管理员误以为在调整比率时实际上在破坏储备配置，双重误配置危及偿付保护。

**修復建議：**
修正函数以设置 `minimumJrtSrtRatio`，使用合适的验证边界，并发出专用的 `MinimumJrtSrtRatioChanged` 事件。

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

## 9. Inconsistent storage location namespace root in `YieldManagerStorageLayout`

**Severity:** 🟡 Medium  **Source:** `cyfrin/manager.md`

**Description:**
`YieldManagerStorageLayout` annotates its `YieldManagerStorage` struct with the ERC-7201 tag `@custom:storage-location erc7201:linea.storage.YieldManager`. However, the actual storage slot constant in the contract is derived from and documented for the identifier `"linea.storage.YieldManagerStorage"` — note the trailing `Storage` suffix. These are two different namespace identifiers that produce different storage slot values under the ERC-7201 formula. Per the standard, the annotation must use the exact same identifier that was used to compute the storage slot; otherwise the annotation misleads tooling into inspecting the wrong slot.

**Impact:**
Off-chain tooling (storage analyzers, upgrade safety validators, block explorers) that reads the ERC-7201 annotation and computes `erc7201("linea.storage.YieldManager")` will inspect a completely different storage root than the one actually in use. This can cause silent failures in upgrade safety checks, incorrect state decoding, and confusion during audits or incident response.

**Recommended Mitigation:**
Synchronize the annotation, the inline comment, and the constant. Either update the annotation to `@custom:storage-location erc7201:linea.storage.YieldManagerStorage` to match the computed slot, or recompute the constant using the ERC-7201 formula for `"linea.storage.YieldManager"` and update the comment and constant accordingly.

---

**[中文版本]**

**描述：**
`YieldManagerStorageLayout` 的 ERC-7201 注解使用标识符 `linea.storage.YieldManager`，但存储槽常量实际上是基于 `linea.storage.YieldManagerStorage`（带 `Storage` 后缀）计算的。两个标识符在 ERC-7201 公式下产生不同的存储根，注解与实际存储槽不匹配。

**影響：**
链下工具（存储分析器、升级安全验证器）读取注解后计算出错误的存储根，导致升级安全检查静默失败、状态解码错误和审计混乱。

**修復建議：**
将注解、注释和常量三者保持一致，选择统一的标识符并确保 ERC-7201 计算与注解完全匹配。

---

## 10. Incorrect Comment and Missing Lower Bound for `minimumJrtSrtRatio` in `Accounting`

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
The `Accounting` contract initializes `minimumJrtSrtRatio = 0.05e18` (5%) but the NatSpec comment above it states `>= 0.05%`, which would imply `0.0005e18`. The comment is off by a factor of 100 from the actual value. Additionally, the setter for this parameter (`setMinimumJrtSrtRatio`, once fixed per a related issue) has no lower bound validation, meaning an operator could accidentally set the ratio to an extremely small value approaching zero, potentially disabling the solvency protection that the minimum ratio is supposed to enforce.

**Impact:**
The misleading comment can cause developers or auditors to misread the intended ratio, potentially treating a 5% constraint as if it were 0.05%. The missing lower bound allows the ratio to be set so low as to be meaningless, compromising the Junior-to-Senior solvency safeguard.

**Recommended Mitigation:**
Update the NatSpec comment to accurately reflect the 5% ratio (e.g., `>= 5%`). Add a minimum bound check in the setter (e.g., `require(bps >= 0.0005e18, "RatioTooLow")`) to prevent inadvertent zeroing of the solvency protection.

---

**[中文版本]**

**描述：**
`Accounting` 将 `minimumJrtSrtRatio` 初始化为 `0.05e18`（5%），但 NatSpec 注释写的是 `>= 0.05%`，与实际值相差 100 倍。同时，该参数的设置函数没有下限验证，允许将比率设置为接近零的值，实质上禁用偿付保护。

**影響：**
误导性注释可能导致开发者或审计员误读预期比率；缺少下限允许意外将偿付保护归零。

**修復建議：**
更新注释为准确反映 5% 的值，并在 setter 中添加 `require(bps >= 0.0005e18)` 的下限验证。

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

## 12. Misconfigured decimal scale can skew vault accounting

**Severity:** 🟡 Medium  **Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault` performs all share-to-asset conversions assuming that the vault's configured `decimals` parameter matches the underlying asset's decimals (USDC, 6 decimals) and the `globalPricePerShare` oracle value's precision. While the deployment configuration correctly sets `vaultParams.decimals = 6`, there is no constructor-level enforcement of this constraint. An operator deploying or upgrading the vault with a different `decimals` value would silently skew all conversion mathematics, causing share prices, deposit amounts, and withdrawal amounts to be calculated with incorrect scaling factors relative to the actual USDC token precision.

**Impact:**
A misconfigured `decimals` value causes all vault accounting to be off by a power of ten. Deposits and withdrawals would either dramatically overpay or underpay users relative to their true share values, potentially making the vault insolvent or draining it through arbitrage.

**Recommended Mitigation:**
Lock the vault's `_vaultParams.decimals` to 6 in the constructor, or add a validation check that reverts if `_vaultParams.decimals != 6` (matching USDC's decimal precision). This prevents misconfiguration from silently corrupting accounting.

---

**[中文版本]**

**描述：**
`SherpaVault` 假设 `vaultParams.decimals` 与底层资产（USDC，6位精度）和 `globalPricePerShare` 精度一致，但构造函数中没有强制验证此约束。若部署时使用错误的精度值，所有份额-资产换算都将以错误的缩放因子计算，导致存款和提款金额系统性偏差。

**影響：**
错误的 `decimals` 配置使所有会计计算偏差一个数量级，存款人可能大幅超额或不足额获得份额，金库面临套利攻击或资不抵债风险。

**修復建議：**
在构造函数中将 `_vaultParams.decimals` 锁定为 6，或添加验证确保其与 USDC 精度一致，配置错误时回滚。

---

## 13. Missing debt asset APPROVAL leafs in `_add_vesu_v1_leafs(...)` and `_add_vesu_v2_leafs(...)`

**Severity:** 🟡 Medium  **Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
When `_set_vault_config(...)` is called to configure VesuV1 or VesuV2 strategies, the functions `_add_vesu_v1_leafs(...)` and `_add_vesu_v2_leafs(...)` generate the Merkle root that authorizes the vault strategist for related operations. These functions correctly add authorization leaves for collateral asset approvals and `modify_position(...)` calls. However, they do not add authorization leaves for the `approve(...)` operation on the debt asset. Without debt asset approval, the strategist can borrow debt tokens (since borrow operations are authorized through `modify_position`) but cannot call `approve(debt_asset, ...)` to subsequently repay the debt. The borrowed debt tokens become permanently unrepayable within the current Merkle authorization framework.

**Impact:**
The strategist can borrow debt tokens from Vesu positions but is structurally unable to repay them due to the missing approval authorization. Outstanding debt grows indefinitely without any path to settlement, potentially leading to liquidation of collateral positions or bad debt accumulation.

**Recommended Mitigation:**
Add APPROVAL authorization leaves for each debt asset in both `_add_vesu_v1_leafs(...)` and `_add_vesu_v2_leafs(...)`, symmetrically with the existing collateral asset approval leaves.

---

**[中文版本]**

**描述：**
`_add_vesu_v1_leafs` 和 `_add_vesu_v2_leafs` 在生成 Merkle 授权根时，正确添加了抵押资产的 approve 授权叶子，但遗漏了债务资产的 approve 授权。策略师可以借入债务代币（通过 `modify_position` 授权），但无法调用 `approve(debt_asset, ...)` 来偿还债务。

**影響：**
策略师可以借入但无法偿还债务，未偿债务无限累积，可能导致抵押仓位被清算或坏账积累。

**修復建議：**
在 `_add_vesu_v1_leafs` 和 `_add_vesu_v2_leafs` 中对每个债务资产添加 APPROVAL 授权叶子，与现有抵押资产授权叶子对称。

---

## 14. Onchain governance integration breaks due to inconsistent implementation of voting power

**Severity:** 🟡 Medium  **Source:** `cyfrin/wlf.md`

**Description:**
World Liberty Financial's governance token overrides `getVotes` to include additional voting power from vesting tokens and to respect blacklist/exclusion rules. However, `getPastVotes` is not overridden. OpenZeppelin's `GovernorVotesUpgradeable` uses `getPastVotes` for all actual voting weight calculations during proposal execution, not `getVotes`. As a result, the on-chain governance mechanism uses a different, less comprehensive voting power calculation than what the UI displays to users: vesting tokens are excluded from governance voting, and blacklisted or excluded accounts retain valid voting power in on-chain proposals.

**Impact:**
Users see their full voting power (including vesting tokens) in the UI via `getVotes`, but actual on-chain governance uses `getPastVotes`, which excludes vesting tokens. This discrepancy undermines governance integrity — blacklisted accounts can vote, excluded accounts retain voting power, and token holders with large vesting balances have less influence than they expect.

**Recommended Mitigation:**
Override `getPastVotes` with the same custom logic as `getVotes` to include vesting token balances and enforce blacklist/exclusion rules. Alternatively, document and implement off-chain governance with an explicit on-chain veto mechanism, and revert on `getPastVotes` to prevent inadvertent use in on-chain voting.

---

**[中文版本]**

**描述：**
WLFI 的治理代币重写了 `getVotes` 以包含归属代币投票权和黑名单/排除规则，但未重写 `getPastVotes`。OpenZeppelin 的 `GovernorVotesUpgradeable` 使用 `getPastVotes` 进行实际投票权计算，导致链上治理和 UI 显示使用不同的投票权逻辑：归属代币不计入链上投票，黑名单账户仍持有有效投票权。

**影響：**
用户在 UI 中看到完整投票权（含归属代币），但实际链上治理排除了归属代币；黑名单账户可参与投票，破坏治理完整性。

**修復建議：**
重写 `getPastVotes` 以应用与 `getVotes` 相同的自定义逻辑，或实现链下治理并对 `getPastVotes` 添加回滚以防止链上误用。

---

## 15. Output Accounting Uses Absolute Balance

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

---

## 16. Reuse `aum_` in `_accrueFeeShares` to avoid recomputing debt

**Severity:** 🟡 Medium  **Source:** `cyfrin/pr50.md`

**Description:**
In `AccountableOpenTerm::_accrueFeeShares`, the outstanding debt is recomputed from scratch as `uint256 debt = _loan.outstandingPrincipal.mulDiv(scaleFactor_, PRECISION)`. However, the exact same value was already computed in `_accrueInterest()` as `aum_` and passed down through the call chain. This redundant recomputation requires `scaleFactor_` to be threaded through as an additional function parameter even though it is only used to reproduce a value that already exists. Beyond the gas inefficiency, maintaining two separate computation paths for the same value creates a subtle divergence risk: if the two computations ever produce different results due to rounding or a future code change, the fee accrual will be based on an inconsistent debt amount.

**Impact:**
Minor gas inefficiency and code complexity from the redundant computation and the unnecessary `scaleFactor_` parameter. The risk of accounting inconsistency if the two debt calculation paths diverge in a future refactor.

**Recommended Mitigation:**
Use `aum_` directly as the debt value in `_accrueFeeShares` (i.e., `uint256 debt = aum_`) and remove the `scaleFactor_` parameter from the function signature and all call sites, simplifying the code and eliminating the duplicate computation.

---

**[中文版本]**

**描述：**
`AccountableOpenTerm::_accrueFeeShares` 中通过 `_loan.outstandingPrincipal.mulDiv(scaleFactor_, PRECISION)` 重新计算债务，而该值已在 `_accrueInterest()` 中以 `aum_` 的形式计算并传入。这一冗余计算额外引入了 `scaleFactor_` 参数，并产生两条独立的计算路径，若未来代码修改导致两路计算结果不一致，会产生会计偏差风险。

**影響：**
轻微的 gas 浪费和代码复杂性，以及若两条计算路径在未来发生分歧时产生会计不一致的风险。

**修復建議：**
在 `_accrueFeeShares` 中直接使用 `aum_` 作为债务值，移除 `scaleFactor_` 参数，消除冗余计算。

---

## 17. `SherpaVault::_rollInternal` price calculation comment and math inconsistent

**Severity:** 🟡 Medium  **Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault::_rollInternal` calculates the new price per share at round rollover. It builds `globalBalance` to include `globalTotalPending` amounts and passes it to `ShareMath.pricePerShare`. The comment states: "globalBalance must include pending deposits for correct price calculation." However, `ShareMath.pricePerShare` immediately subtracts the `pendingAmount` from `totalBalance` before dividing: the formula is `(singleShare * (totalBalance - pendingAmount)) / totalSupply`. The net effect is that the pending amount is added and then immediately subtracted, making its inclusion in `globalBalance` a no-op. Either the comment is wrong (the pending amount does not need to be included, and the final price is equivalent to `(singleShare * globalTotalStaked) / globalShareSupply`) or the math is wrong (the subtraction in `pricePerShare` should not occur).

**Impact:**
The code produces a correct price (because the add and subtract cancel out), but the misleading comment can lead future maintainers to incorrectly believe the pending amount contributes to the price. A developer acting on the comment's guidance could introduce a real pricing error in a future modification.

**Recommended Mitigation:**
Correct the comment to accurately describe what the math actually computes, or if the original intent was to include pending amounts in the price, fix `ShareMath.pricePerShare` to not subtract them.

---

**[中文版本]**

**描述：**
`SherpaVault::_rollInternal` 注释声称 `globalBalance` 必须包含待处理存款以正确计算价格，但 `ShareMath.pricePerShare` 在计算中立即将 `pendingAmount` 减去，导致加入再减去等于白加。注释与数学逻辑不一致：代码产生正确结果（两者相消），但注释具有误导性。

**影響：**
代码功能正确，但误导性注释可能导致未来维护者基于错误理解做出修改，引入真实的定价错误。

**修復建議：**
修正注释以准确描述实际数学运算，或若原意是将待处理金额纳入价格，则修改 `ShareMath.pricePerShare` 不再减去该值。

---

## 18. Unused Import of `OwnableUpgradeable` in `Accounting.sol`

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
`Accounting.sol` imports `OwnableUpgradeable` from OpenZeppelin but does not use this import directly within the file. The import is likely a remnant from a prior version of the contract where ownership was managed differently. Unused imports do not cause compilation errors in Solidity, but they add noise to the codebase, can confuse static analysis tools, and may mislead reviewers into believing `OwnableUpgradeable` functionality is actually used or relied upon within `Accounting`.

**Impact:**
No direct security or functional impact. The unused import adds code noise, increases the cognitive burden during audits, and may cause static analysis tools to flag false dependency relationships.

**Recommended Mitigation:**
Remove the unused `import { OwnableUpgradeable } from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol"` statement from `Accounting.sol` to keep the imports clean and accurate.

---

**[中文版本]**

**描述：**
`Accounting.sol` 导入了 `OwnableUpgradeable` 但在文件中未直接使用，可能是旧版本代码的残留。未使用的导入不影响编译，但增加代码噪音，可能误导审计人员认为该合约依赖所有权功能。

**影響：**
无直接安全或功能影响，但增加审计认知负担，可能导致静态分析工具产生错误的依赖关系报告。

**修復建議：**
从 `Accounting.sol` 中移除未使用的 `OwnableUpgradeable` 导入语句，保持代码整洁。
