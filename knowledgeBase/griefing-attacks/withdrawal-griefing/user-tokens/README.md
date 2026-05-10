# user-tokens (17)

> Issues where user funds, NFTs, or token operations can be griefed, bricked, or exploited by attackers or contract logic.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Fees can be stolen from partially unwrapped UniswapV4Wrapper positions

**Severity:** 🟠 High
**Source:** `cyfrin/vii.md`

**Description:**
`ERC721WrapperBase` exposes two overloads of `unwrap()` for full and partial unwrap of ERC-6909 positions. For `UniswapV4Wrapper`, partial unwraps accumulate LP fees in a `tokensOwed` mapping that is never decremented. When a user fully unwraps using the partial-unwrap overload and then re-wraps the same position, the stale `tokensOwed` state persists. Combined with the ability to re-wrap an already-fully-unwrapped position, an attacker can chain wrap/unwrap cycles to siphon fees that are intended for holders of other partially unwrapped positions.

**Impact:**
Fees belonging to ERC-6909 holders of partially unwrapped positions can be stolen. The attack also causes a denial-of-service for other holders attempting to fully unwrap their balance, potentially blocking liquidations and causing bad debt to accrue in the vault.

**Recommended Mitigation:**
Decrement the `tokensOwed` mapping appropriately when fees are collected during a partial unwrap, so that stale accumulated fee state cannot be reused after a wrap/unwrap cycle.

---

**[中文版本]**

**描述：**
`ERC721WrapperBase` 暴露了两种 `unwrap()` 重载用于全量和部分解包 ERC-6909 仓位。对于 `UniswapV4Wrapper`，部分解包会将 LP 手续费累积到 `tokensOwed` 映射中，但该映射的值从不递减。当用户使用部分解包重载执行全量解包后再重新包装同一仓位时，过期的 `tokensOwed` 状态仍然保留，攻击者可通过反复包装/解包循环窃取其他部分解包仓位持有者的手续费。

**影響：**
部分解包仓位的 ERC-6909 持有者的手续费可能被盗取，同时导致其他持有者无法完成全量解包，可能阻碍清算并造成坏账。

**修復建議：**
在部分解包收取手续费时，适当递减 `tokensOwed` 映射，以防止过期的累积手续费状态在包装/解包循环后被重复使用。

---

## 2. Users Can Perform New Tokens Purchase After autoRefund() Leading to Underflow in claim()

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
`F-2025-11617` — The `BondingCurve` contract allows users to purchase project tokens via a bonding mechanism. The `BondingCurveWritable::autoRefund()` function enables the admin to issue automatic refunds when the soft cap is not reached; however, it does not update the user's `isRefunded` flag or adjust the `amountToClaim`/`amountClaimed` fields. As a result, a user who is auto-refunded can purchase tokens again in the same bonding curve. Because `amountClaimed` is set to `type(uint256).max` during the refund process, any subsequent purchase by that user causes an underflow in `claim()`, making it impossible for them to claim newly purchased tokens.

**Impact:**
Users who are auto-refunded can lose bonded tokens and claimable project token amounts. Their newly purchased tokens become permanently unclaimable due to the underflow condition in `claim()`.

**Recommended Mitigation:**
After executing `autoRefund()`, set the user's `isRefunded` flag to `true` and block further purchases by refunded users in the same bonding curve. Ensure `amountToClaim` and `amountClaimed` are reset or validated before permitting re-entry.

---

**[中文版本]**

**描述：**
`F-2025-11617` — `BondingCurve` 合约允许用户通过绑定机制购买项目代币。`BondingCurveWritable::autoRefund()` 函数允许管理员在软上限未达到时发起自动退款，但未正确更新用户的 `isRefunded` 标志，也未调整 `amountToClaim` 或 `amountClaimed` 字段。被自动退款的用户可在同一绑定曲线中再次购买代币，但由于退款时 `amountClaimed` 已被设置为 `type(uint256).max`，后续购买会在 `claim()` 中导致下溢，使新购代币无法领取。

**影響：**
被自动退款的用户将损失已绑定的代币和可领取的项目代币数量，新购代币因 `claim()` 下溢而永久无法领取。

**修復建議：**
在执行 `autoRefund()` 后，将用户 `isRefunded` 标志设置为 `true`，并阻止被退款用户在同一绑定曲线中再次购买代币，同时确保在允许重新参与前对 `amountToClaim` 和 `amountClaimed` 进行重置或验证。

---

## 3. Active and pending bets can be cancelled by anyone

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`Bet::cancel` only prevents the `maker` from cancelling an `ACTIVE` bet, but does not restrict any other address. This means any arbitrary caller, including the `taker`, can cancel both `PENDING` and `ACTIVE` bets at any time without restriction.

**Impact:**
Any user can grief a bet by cancelling it. More critically, the taker can unilaterally back out of an already-accepted `ACTIVE` bet — for example, once the outcome appears unfavorable — allowing them to reclaim their stake while undermining the integrity of the betting mechanism.

**Recommended Mitigation:**
Do not allow anyone other than a designated judge (or the maker before acceptance) to cancel an `ACTIVE` bet. Restrict cancellation of `ACTIVE` bets to an authorized role or remove the ability entirely during the active phase.

---

**[中文版本]**

**描述：**
`Bet::cancel` 仅限制 `maker` 不能取消 `ACTIVE` 状态的投注，但未限制其他地址。这意味着任意调用者（包括 `taker`）可随时取消 `PENDING` 和 `ACTIVE` 状态的投注。

**影響：**
任何用户均可通过取消投注进行骚扰（griefing）。更严重的是，taker 可在投注已接受后单方面退出，例如当结果对其不利时，通过调用 `cancel()` 收回质押资金，破坏投注机制的完整性。

**修復建議：**
不允许除指定裁判（或接受前的 maker）外的任何人取消 `ACTIVE` 状态的投注，限制活跃阶段的取消权限至授权角色，或完全移除活跃阶段的取消功能。

---

## 4. AngstromL2::_computeAndCollectProtocolSwapFee computation can be simplified

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2::_computeAndCollectProtocolSwapFee` uses a complex expression for the exact-output fee path: `absTargetAmount * FACTOR_E6 / (FACTOR_E6 - protocolFeeE6) - absTargetAmount`. This is mathematically equivalent to the simpler form `absTargetAmount * protocolFeeE6 / (FACTOR_E6 - protocolFeeE6)`, which reduces the number of arithmetic operations.

**Impact:**
No direct security risk, but the unnecessarily complex arithmetic increases the chance of misreading or misverifying the fee calculation logic during audits or future modifications.

**Recommended Mitigation:**
Simplify the exact-output fee computation to `absTargetAmount * protocolFeeE6 / (FACTOR_E6 - protocolFeeE6)`.

---

**[中文版本]**

**描述：**
`AngstromL2::_computeAndCollectProtocolSwapFee` 在精确输出手续费路径中使用了复杂表达式：`absTargetAmount * FACTOR_E6 / (FACTOR_E6 - protocolFeeE6) - absTargetAmount`，该表达式与更简洁的形式 `absTargetAmount * protocolFeeE6 / (FACTOR_E6 - protocolFeeE6)` 数学等价，但算术操作更多。

**影響：**
无直接安全风险，但不必要的复杂算术增加了审计或未来修改时误读费用计算逻辑的可能性。

**修復建議：**
将精确输出费用计算简化为 `absTargetAmount * protocolFeeE6 / (FACTOR_E6 - protocolFeeE6)`。

---

## 5. BridgeCCIP.isL1 can be immutable

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
The `BridgeCCIP` contract contains a storage slot for `isL1` that determines whether the bridge is operating on Layer 1 or Layer 2. This value is set during initialization and is never subsequently changed, making it a candidate for an `immutable` variable. Keeping it as a mutable storage variable incurs unnecessary `SLOAD` gas costs on every access.

**Impact:**
Every read of `isL1` costs 100 gas (cold `SLOAD`) instead of the 3 gas cost of reading an immutable. Over the lifetime of the contract, this represents unnecessary gas expenditure for users.

**Recommended Mitigation:**
Declare `isL1` as an `immutable` variable and initialize it in the constructor rather than in a separate storage slot.

---

**[中文版本]**

**描述：**
`BridgeCCIP` 合约包含一个 `isL1` 存储槽，用于标识桥接合约运行在 Layer 1 还是 Layer 2。该值在初始化时设置且之后从未更改，可作为 `immutable` 变量。保持为可变存储变量会在每次访问时产生不必要的 `SLOAD` 燃气成本。

**影響：**
每次读取 `isL1` 消耗 100 gas（冷 `SLOAD`），而读取 immutable 仅需 3 gas，在合约生命周期内造成不必要的用户燃气支出。

**修復建議：**
将 `isL1` 声明为 `immutable` 变量，并在构造函数中初始化，而不是使用独立的存储槽。

---

## 6. Buyers can pledge for tokens without having signed all documents that are required to be signed

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
When a buyer calls `pledge()` during the pledge round, `_verifyDocumentSignature` checks whether all required documents have been signed via `hasSignedDocs()`. If not all documents are signed, instead of reverting, the function attempts to verify one document signature provided in the call data. Since `hasSignedDocs()` returns `false` as soon as any required document is unsigned, a user can provide a signature for just one document while leaving the others unsigned, and the check passes, bypassing the requirement to sign all documents.

**Impact:**
Buyers can enter the pledge round without signing all legally required documents, violating the intended compliance mechanism of the platform.

**Recommended Mitigation:**
Separate the document verification from signature registration. If `hasSignedDocs()` returns `false`, revert rather than attempting to verify and register a single document signature in the same call.

---

**[中文版本]**

**描述：**
当买家在认购轮调用 `pledge()` 时，`_verifyDocumentSignature` 通过 `hasSignedDocs()` 检查是否所有必要文件已被签署。若未签全，函数不会回滚，而是尝试验证调用数据中提供的单个文件签名。由于 `hasSignedDocs()` 在有任意文件未签时返回 `false`，用户只需提供一份文件签名即可绕过全部签署要求。

**影響：**
买家无需签署所有法律要求的文件即可参与认购轮，违反了平台预期的合规机制。

**修復建議：**
将文件验证与签名注册分离。若 `hasSignedDocs()` 返回 `false`，应直接回滚，而不是在同一次调用中尝试验证并注册单个文件签名。

---

## 7. Duplicate vaults can be pushed to assetsArr

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`MetaVault::addVault` does not check whether a vault address already exists in `assetsArr` before appending. If the owner calls `addVault` with the same vault address multiple times, duplicate entries are created. While `redeemMetaVaults` handles duplicates gracefully during the yield phase (the second iteration finds zero balance and removes the duplicate entry), attempting to manually remove a duplicate with `removeVault` will revert because the vault's `assetsMap` entry is already cleared on the first removal.

**Impact:**
Duplicate vaults in `assetsArr` can cause unexpected gas overhead during redemption iterations and prevent the owner from cleanly removing a duplicate via `removeVault`, which requires the mapping entry to still be valid.

**Recommended Mitigation:**
Add a duplicate check inside `addVaultInner` that reverts if the vault is already present in `assetsMap`.

---

**[中文版本]**

**描述：**
`MetaVault::addVault` 在追加前不检查 vault 地址是否已存在于 `assetsArr` 中。若 owner 多次以相同 vault 地址调用 `addVault`，会产生重复条目。虽然 `redeemMetaVaults` 在收益阶段能优雅处理重复（第二次迭代发现余额为零并移除重复条目），但通过 `removeVault` 手动移除重复条目时会回滚，因为映射条目在第一次移除时已被清空。

**影響：**
`assetsArr` 中的重复 vault 会在赎回迭代中产生意外的燃气开销，并阻止 owner 通过 `removeVault` 干净地移除重复条目。

**修復建議：**
在 `addVaultInner` 内添加重复检查，若 vault 已存在于 `assetsMap` 中则回滚。

---

## 8. Effective price calculations can be affected by edge cases in Math512Lib::sqrt512 and Math512Lib::div512by256

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`Math512Lib::sqrt512` implements a Newton-Raphson square root for 512-bit integers. The algorithm requires the initial guess to be larger than the upper limb; however, when the most significant bit of the upper limb is set, floor division by two can produce an initial guess smaller than the upper limb, causing the long-division result to exceed 256 bits and diverge. Additionally, `Math512Lib::div512by256` has an error in synthesizing `2^256` during remainder computation, deviating from the Solady implementation it was adapted from.

**Impact:**
These edge cases can produce incorrect square root or division results, leading to inaccurate effective price calculations for swaps and potentially enabling users to receive incorrect swap rates.

**Recommended Mitigation:**
Fix the initial guess logic in `sqrt512` to ensure it is always strictly larger than the upper limb. Audit and correct the `div512by256` remainder synthesis to match the reference Solady implementation.

---

**[中文版本]**

**描述：**
`Math512Lib::sqrt512` 实现了 512 位整数的牛顿-拉弗森平方根算法，要求初始猜测值严格大于高位字。然而当高位字最高位为 1 时，整除 2 可能产生小于高位字的初始猜测，导致长除法结果超过 256 位并发散。此外，`Math512Lib::div512by256` 在余数计算中合成 `2^256` 时存在错误，与其参考的 Solady 实现不一致。

**影響：**
这些边缘案例可能产生不正确的平方根或除法结果，导致交换的有效价格计算不准确，用户可能获得错误的兑换比率。

**修復建議：**
修复 `sqrt512` 中的初始猜测逻辑，确保其始终严格大于高位字；审查并纠正 `div512by256` 的余数合成，使其与 Solady 参考实现一致。

---

## 9. Overriding fees can't be switched back once set

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`TokenBank::setBaseFee` has a conditional `if (overrideFee)` block that only updates the `overrideFees` storage variable when the parameter is `true`. Once `overrideFees` is set to `true` (meaning the base fee is applied to all tokens instead of per-token fees), there is no way to set it back to `false`. The `if` block prevents the assignment from executing when `overrideFee` is `false`.

**Impact:**
Once the fee override is activated, the protocol cannot revert to per-token fee configuration. This removes governance flexibility and may cause unintended uniform fee application across all tokens permanently.

**Recommended Mitigation:**
Remove the conditional and always assign `overrideFees = overrideFee` directly, regardless of its value.

---

**[中文版本]**

**描述：**
`TokenBank::setBaseFee` 包含一个 `if (overrideFee)` 条件块，仅在参数为 `true` 时更新 `overrideFees` 存储变量。一旦 `overrideFees` 被设置为 `true`（即对所有代币应用基础费用而非逐代币费用），就无法将其恢复为 `false`，因为 `if` 块阻止了在参数为 `false` 时执行赋值。

**影響：**
费用覆盖一旦激活，协议将无法恢复到逐代币费用配置，永久失去治理灵活性。

**修復建議：**
移除条件判断，无论参数值如何，始终直接执行 `overrideFees = overrideFee` 赋值。

---

## 10. Recover Function Can Steal User Funds

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/A Two Tech Limited.txt`

**Description:**
`F-2025-14057` — The `recover()` function in `ATWODistributor` allows the admin to withdraw any amount of ATWO tokens from the contract at any time without any restriction on user entitlements. The admin can drain all tokens that are rightfully owed to presale participants, rendering the contract insolvent. Since `amountClaimed` is not compared against available balances before admin withdrawals, all user `claim()` calls would fail after a malicious recovery.

**Impact:**
Admin can withdraw ATWO tokens that belong to presale users, rendering the contract insolvent. Users will be unable to claim their purchased tokens after TGE. The contract has no safeguard or circuit breaker to prevent this centralization risk.

**Recommended Mitigation:**
Add a check in `recover()` that prevents the admin from withdrawing tokens that are reserved for user claims. Track the total claimable amount and ensure the contract balance always exceeds this reserved amount.

---

**[中文版本]**

**描述：**
`F-2025-14057` — `ATWODistributor` 中的 `recover()` 函数允许管理员随时从合约提取任意数量的 ATWO 代币，不受任何用户权益约束。管理员可抽走属于预售参与者的所有代币，导致合约资不抵债。由于管理员提款前不检查用户应得余额，恶意提款后所有用户的 `claim()` 调用都将失败。

**影響：**
管理员可提走属于预售用户的代币，使合约资不抵债，用户在 TGE 后无法领取已购代币，合约缺乏防止此类中心化风险的保护机制。

**修復建議：**
在 `recover()` 中添加检查，防止管理员提取用户认购所预留的代币。追踪总可领取金额，确保合约余额始终不低于该预留金额。

---

## 11. SDLVesting::claimRESDLRewards() can be used to drain the entire vesting contract balance in edge case

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
`SDLVesting::claimRESDLRewards` transfers the entire token balance for each specified reward token to the beneficiary. If the admin mistakenly adds the SDL token itself as a reward token in the `RewardsPoolController`, the beneficiary can call `claimRESDLRewards([sdlToken])` to instantly withdraw all SDL tokens held by the vesting contract — including both vested and unvested amounts — completely bypassing the vesting schedule.

**Impact:**
In the edge case where SDL is added as a reward token, the beneficiary can drain the entire vesting balance in a single transaction, defeating the purpose of the vesting contract.

**Recommended Mitigation:**
Add a check inside `claimRESDLRewards` to skip any token that matches the SDL token address (e.g., `if (_tokens[i] == address(sdlToken)) continue;`).

---

**[中文版本]**

**描述：**
`SDLVesting::claimRESDLRewards` 将每个指定奖励代币的全部合约余额转给受益人。若管理员误将 SDL 代币本身添加为 `RewardsPoolController` 的奖励代币，受益人可调用 `claimRESDLRewards([sdlToken])` 立即提取合约持有的全部 SDL 代币（包括已归属和未归属部分），完全绕过归属计划。

**影響：**
在 SDL 被添加为奖励代币的边缘情况下，受益人可通过单笔交易抽空整个归属余额，使归属合约失去意义。

**修復建議：**
在 `claimRESDLRewards` 内添加检查，跳过与 SDL 代币地址匹配的代币（例如：`if (_tokens[i] == address(sdlToken)) continue;`）。

---

## 12. Superfluous vault support validation can be removed from pUSDeDepositor::deposit

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeDepositor::deposit` performs a `MetaVault::isAssetSupported` check before calling `MetaVault::deposit`. This check is redundant because `MetaVault::deposit` already calls `requireSupportedVault` internally for non-USDe assets, which would revert with `UnsupportedAsset` on unsupported tokens. The pre-check in the depositor is therefore a duplicated validation that adds unnecessary gas overhead.

**Impact:**
No security risk, but the redundant check wastes gas on each deposit for non-USDe vault tokens.

**Recommended Mitigation:**
Remove the `isAssetSupported` call from `pUSDeDepositor::deposit` and rely on `MetaVault::deposit`'s internal `requireSupportedVault` validation.

---

**[中文版本]**

**描述：**
`pUSDeDepositor::deposit` 在调用 `MetaVault::deposit` 之前执行 `MetaVault::isAssetSupported` 检查。此检查是冗余的，因为 `MetaVault::deposit` 内部已通过 `requireSupportedVault` 对非 USDe 资产进行相同验证，不支持的代币会以 `UnsupportedAsset` 回滚。存款合约中的预检查是重复验证，徒增燃气开销。

**影響：**
无安全风险，但冗余检查在每次非 USDe vault 代币存款时浪费燃气。

**修復建議：**
从 `pUSDeDepositor::deposit` 中移除 `isAssetSupported` 调用，依赖 `MetaVault::deposit` 内部的 `requireSupportedVault` 验证。

---

## 13. Unnecessarily complex iteration logic in MetaVault::redeemMetaVaults can be simplified

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`MetaVault::redeemMetaVaults` uses a `while` loop that always indexes the first element of `assetsArr` and calls `removeVaultAndRedeemInner`, which in turn performs a replace-and-pop search through the entire array. This means every iteration performs unnecessary storage writes and the array ordering changes unpredictably. Walking backwards from the last element and simply popping would be more gas-efficient and preserve ordering.

**Impact:**
The complex iteration pattern causes unnecessary storage writes and gas overhead during the yield phase redemption.

**Recommended Mitigation:**
Rewrite `redeemMetaVaults` to iterate from the last element backwards and pop each element after redemption, avoiding the replace-and-pop overhead.

---

**[中文版本]**

**描述：**
`MetaVault::redeemMetaVaults` 使用 `while` 循环始终从 `assetsArr` 第一个元素开始索引，并调用 `removeVaultAndRedeemInner`，后者在整个数组中执行替换弹出（replace-and-pop）搜索。这导致每次迭代产生不必要的存储写入且数组顺序不可预测。从最后一个元素向前遍历并逐一弹出会更节省燃气且保持顺序。

**影響：**
复杂的迭代模式在收益阶段赎回时产生不必要的存储写入和燃气开销。

**修復建議：**
重写 `redeemMetaVaults`，从最后一个元素向前遍历，赎回后逐一弹出，避免替换弹出的额外开销。

---

## 14. Unnecessary arithmetic validation within AngstromL2::withdrawProtocolRevenue can be removed

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2::withdrawProtocolRevenue` validates `if (!(amount <= unclaimedProtocolRevenueInEther))` before performing `unclaimedProtocolRevenueInEther -= amount`. This explicit check is unnecessary because Solidity 0.8+ automatically reverts with a panic on unsigned integer underflow. The double validation adds dead code and a redundant custom error path.

**Impact:**
Minor code quality issue with no security impact. The explicit check is unnecessary but harmless.

**Recommended Mitigation:**
Remove the explicit bound check and rely on Solidity's built-in underflow protection for the subtraction.

---

**[中文版本]**

**描述：**
`AngstromL2::withdrawProtocolRevenue` 在执行 `unclaimedProtocolRevenueInEther -= amount` 之前验证 `if (!(amount <= unclaimedProtocolRevenueInEther))`。这个显式检查是多余的，因为 Solidity 0.8+ 在无符号整数下溢时会自动触发 panic 回滚，双重验证增加了死代码和冗余的自定义错误路径。

**影響：**
轻微代码质量问题，无安全影响。显式检查多余但无害。

**修復建議：**
移除显式边界检查，依赖 Solidity 内置的减法下溢保护。

---

## 15. Unsafe external calls made during proportional LP fee transfers can be used to reenter wrapper contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/vii.md`

**Description:**
In `ERC721WrapperBase`, the partial `unwrap()` overload calls `_unwrap` (which transfers tokens including native ETH or ERC-777 tokens) before `_burnFrom`, which reduces the sender's ERC-6909 balance. For wrappers using positions with transfer-hooks (ERC-777) or native ETH (Uniswap V4), the external call to the user-supplied `to` address can reenter execution before the balance is reduced. Despite the `callThroughEVC` modifier, reentrancy is possible because control collateral is not in progress during the transfer, allowing the EVC's `nonReentrantChecksAndControlCollateral` modifier to be bypassed.

**Impact:**
Reentrancy is possible during partial unwraps. While draining the vault via an undercollateralized borrow appears blocked by deferred check reverts, the attack surface exists for future protocol states or configurations that include native ETH positions.

**Recommended Mitigation:**
Apply the checks-effects-interactions pattern: call `_burnFrom` before `_unwrap` in the partial unwrap path, or add an explicit reentrancy guard covering the unwrap sequence.

---

**[中文版本]**

**描述：**
在 `ERC721WrapperBase` 中，部分 `unwrap()` 重载在 `_burnFrom`（减少发送者 ERC-6909 余额）之前调用 `_unwrap`（转账代币，包括原生 ETH 或 ERC-777 代币）。对于使用具有转账回调（ERC-777）或原生 ETH（Uniswap V4）的包装器，外部调用到用户提供的 `to` 地址可在余额减少前重入执行。尽管有 `callThroughEVC` 修饰符，但由于转账期间控制抵押品未进行中，EVC 的 `nonReentrantChecksAndControlCollateral` 修饰符可被绕过。

**影響：**
部分解包期间存在重入可能。虽然通过欠抵押借款耗尽 vault 的攻击受延迟检查回滚的阻挡，但对于包含原生 ETH 仓位的未来协议状态或配置，攻击面依然存在。

**修復建議：**
遵循检查-效果-交互模式：在部分解包路径中先调用 `_burnFrom` 再调用 `_unwrap`，或在解包序列上添加显式重入保护。

---

## 16. burnFrom Can Brick User Accounts

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Tokenizer.Estate.txt`

**Description:**
`F-2025-14165` — `RealEstateToken` implements a locking mechanism where users cannot transfer more than their `balance - locked` amount. The `burnFrom` function reduces a user's token balance by calling `_burn`, which invokes `_update(account, address(0), amount)`. The `_update` override skips the lock validation check when the recipient is `address(0)` (burning). This allows an admin with `ROLE_BURNER` to burn tokens such that `balanceOf(account) < _locked[account]`. When the user subsequently attempts to transfer any tokens, the calculation `unlocked = fromBal - _locked[from]` underflows in Solidity 0.8+, causing a panic revert and permanently bricking the account.

**Impact:**
A `ROLE_BURNER` admin can permanently freeze any user's account, preventing all token transfers even of unlocked tokens, until the lock amount is manually corrected.

**Recommended Mitigation:**
In `burnFrom` (and `burn`), either adjust the locked balance proportionally when burning, or add a check to ensure the remaining balance after burning does not fall below the locked amount.

---

**[中文版本]**

**描述：**
`F-2025-14165` — `RealEstateToken` 实现了锁定机制，用户不能转移超过 `balance - locked` 的代币。`burnFrom` 函数通过调用 `_burn` 减少用户余额，后者调用 `_update(account, address(0), amount)`，而该重载在接收方为 `address(0)`（销毁）时跳过了锁定验证检查。这允许具有 `ROLE_BURNER` 权限的管理员销毁代币，使 `balanceOf(account) < _locked[account]`。当用户随后尝试转账时，Solidity 0.8+ 中的 `unlocked = fromBal - _locked[from]` 计算会发生下溢 panic 回滚，永久冻结账户。

**影響：**
具有 `ROLE_BURNER` 权限的管理员可永久冻结任意用户账户，阻止所有代币转账（包括未锁定部分），直至手动修正锁定金额。

**修復建議：**
在 `burnFrom`（及 `burn`）中，销毁时按比例调整锁定余额，或添加检查确保销毁后剩余余额不低于锁定金额。

---

## 17. collatInfo.stablecoinCap hardcap can be bypassed via SettersGovernor::adjustStablecoins

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
The `stablecoinCap` field in the `Collateral` struct is intended to cap the maximum stablecoins a collateral asset can back. This limit is enforced correctly during user mint operations in the `Swapper` facet. However, `SettersGovernor::adjustStablecoins` can increase `normalizedStables` arbitrarily without checking against `stablecoinCap`. This allows the Governor to push the system into a state where a collateral backs more stablecoins than its configured maximum.

**Impact:**
The Governor can bypass the hardcap mechanism, allowing collateral to back an unbounded amount of stablecoins. This can undermine the collateral safety ratios that the cap was designed to enforce.

**Recommended Mitigation:**
Add a cap enforcement check in the increase path of `LibSetters::adjustStablecoins`: after incrementing `newCollateralNormalizedStable`, revert if `newCollateralNormalizedStable * ts.normalizer / BASE_27 > collatInfo.stablecoinCap`.

---

**[中文版本]**

**描述：**
`Collateral` 结构体中的 `stablecoinCap` 字段旨在限制单一抵押资产可支撑的最大稳定币数量，并在 `Swapper` facet 中用户铸造时正确执行。然而，`SettersGovernor::adjustStablecoins` 可任意增加 `normalizedStables` 而不检查 `stablecoinCap`，允许 Governor 将系统推入某抵押资产支撑超过其配置上限的稳定币数量的状态。

**影響：**
Governor 可绕过硬上限机制，允许抵押资产支撑无限量的稳定币，破坏了该上限所设计的抵押安全比率。

**修復建議：**
在 `LibSetters::adjustStablecoins` 的增加路径中添加上限检查：递增 `newCollateralNormalizedStable` 后，若 `newCollateralNormalizedStable * ts.normalizer / BASE_27 > collatInfo.stablecoinCap` 则回滚。
