# assets-withdraw (10)

> Issues where asset withdrawal, emergency extraction, or fund recovery functions can be exploited or blocked.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Partial redemptions can be used to steal assets

**Severity:** 🔴 Critical
**Source:** `cyfrin/accountable.md`

**Description:**
When a redemption request is partially filled, the `totalValue` field of the withdrawal request is never decreased while `request.shares` is correctly reduced. When a subsequent redemption is pushed onto the same `requestId`, the average `sharePrice` is recalculated using the outdated (inflated) `totalValue` together with the updated, reduced `request.shares`. This produces an artificially elevated average share price, which entitles the controller to claim more assets than they deposited.

**Impact:**
An attacker can exploit the accounting gap introduced by partial fills to redeem shares at a price higher than the true average, effectively stealing assets from other vault depositors and rendering the vault insolvent.

**Recommended Mitigation:**
When `_reduce` partially fills a request, proportionally decrease `request.totalValue` by the ratio of shares filled to total shares. This keeps the stored average share price consistent with the remaining share balance.

---

**[中文版本]**

**描述：**
当赎回请求被部分填充时，提款请求的 `totalValue` 字段从未减少，而 `request.shares` 已正确减少。当后续赎回被推送到同一 `requestId` 时，系统使用已过时（虚高）的 `totalValue` 和更新后减少的 `request.shares` 重新计算平均 `sharePrice`，从而产生人为抬高的平均价格，使控制者得以申领超过其存入资产的金额。

**影響：**
攻击者可利用部分填充引入的会计漏洞，以高于真实均价的价格赎回份额，实质上从其他金库存款人处窃取资产，导致金库资不抵债。

**修復建議：**
当 `_reduce` 部分填充请求时，按已填充份额与总份额之比等比减少 `request.totalValue`，确保存储的平均份额价格与剩余份额余额保持一致。

---

## 2. Disabled operators can register new validator nodes

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::addNode` only checks whether `msg.sender` is present in the operators set but does not verify whether the operator is in an active (non-disabled) state. Before an operator can be permanently removed via `removeOperator`, it must first be disabled via `disableOperator`. During the disabled period the operator is expected to be inactive, but the missing state check in `addNode` allows a disabled operator to continue registering new validator nodes.

**Impact:**
A disabled operator — one that should be barred from participating — can still expand its validator set. This undermines the operator lifecycle enforcement and may expose the protocol to validators attached to an operator that governance has intentionally restricted.

**Recommended Mitigation:**
Update `addNode` to check both operator existence and enabled status. If `disabledTime > 0`, revert with `AvalancheL1Middleware__OperatorNotActive`.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware::addNode` 仅检查 `msg.sender` 是否在 operators 集合中，而不验证运营商是否处于活跃（非禁用）状态。在通过 `removeOperator` 永久移除之前，运营商必须先通过 `disableOperator` 进入"禁用"状态。禁用期间运营商应处于非活跃状态，但 `addNode` 中缺少状态检查，允许被禁用的运营商继续注册新的验证节点。

**影響：**
被禁用的运营商——本应被禁止参与的一方——仍可扩展其验证节点集，破坏了运营商生命周期管理，可能使协议暴露于治理机构有意限制的运营商所关联的验证节点之下。

**修復建議：**
更新 `addNode`，同时检查运营商的存在性与启用状态。若 `disabledTime > 0`，则以 `AvalancheL1Middleware__OperatorNotActive` 进行回滚。

---

## 3. Excessive Emergency Withdraw Can Steal User Funds

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/A Two Tech Limited.txt`

**Description:**
`ATWOVesting::emergencyWithdraw` allows the admin to withdraw any amount of tokens from the vesting contract at any time without any restrictions on reserved amounts. The function performs a `safeTransfer` directly without checking whether the requested amount exceeds tokens already vested or promised to beneficiaries. Although named "emergency," no actual emergency conditions are verified before execution.

**Impact:**
The admin can drain tokens reserved for user vesting schedules, making the contract insolvent. Users will be unable to claim their entitled vested tokens because the contract will have insufficient balance. The function entirely defeats the purpose of a vesting contract and represents a critical centralization risk.

**Recommended Mitigation:**
Add a check ensuring that `amount` does not exceed `token.balanceOf(address(this)) - totalReservedAmount`, where `totalReservedAmount` tracks all scheduled but unclaimed vesting allocations.

---

**[中文版本]**

**描述：**
`ATWOVesting::emergencyWithdraw` 允许管理员随时从归属合约中提取任意数量的代币，对已预留金额毫无限制。该函数直接执行 `safeTransfer`，不检查请求金额是否超过已归属或已承诺给受益人的代币。尽管名为"紧急"提款，执行前未验证任何实际紧急条件。

**影響：**
管理员可清空为用户归属计划预留的代币，导致合约资不抵债。用户将因合约余额不足而无法领取其应得的已归属代币，完全违背了归属合约的目的，属于严重的中心化风险。

**修復建議：**
添加检查，确保 `amount` 不超过 `token.balanceOf(address(this)) - totalReservedAmount`，其中 `totalReservedAmount` 跟踪所有已计划但未领取的归属分配。

---

## 4. If zero xp is earned by all users, claimRewards panic reverts due to division by zero but game also can't be cancelled resulting in locked tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`ProportionalToXPReward::getReward` divides by `totalXP` to compute each user's prize share. If all players earn zero XP — which is possible because `DefaultSession::setXPTiers` only enforces a minimum of two tiers but does not enforce non-zero values — `totalXP` will be zero, causing a panic revert via division by zero when `claimRewards` is called. Furthermore, once a game transitions to the `Concluded` state, `cancelGame` is no longer available, permanently locking all deposited funds in the contract.

**Impact:**
All entry-fee tokens deposited for a concluded game become permanently locked if every participant earned zero XP, since `claimRewards` always panics and the game cannot be cancelled.

**Recommended Mitigation:**
Enforce a minimum value of 1 for every XP tier in `DefaultSession::setXPTiers` to prevent the zero-division scenario.

---

**[中文版本]**

**描述：**
`ProportionalToXPReward::getReward` 通过除以 `totalXP` 来计算每位用户的奖金份额。如果所有玩家获得的 XP 均为零——因为 `DefaultSession::setXPTiers` 仅要求至少两个层级而不强制非零值，这种情况是可能发生的——则 `totalXP` 将为零，导致调用 `claimRewards` 时因除零而发生 panic 回滚。此外，一旦游戏进入 `Concluded` 状态，`cancelGame` 将不再可用，导致所有已存入资金永久锁定在合约中。

**影響：**
若已结束游戏中所有参与者均获得零 XP，则所有存入的入场费代币将永久锁定，因为 `claimRewards` 始终 panic 回滚，且游戏无法取消。

**修復建議：**
在 `DefaultSession::setXPTiers` 中强制每个 XP 层级的最小值为 1，以防止零除场景。

---

## 5. Inline small internal functions only used once

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeDepositor::getPhase` is a small internal function only called by `deposit_sUSDe`. Keeping it as a separate function incurs unnecessary function call overhead and an extra storage read. Inlining the logic of `getPhase` directly into `deposit_sUSDe` — while also caching the `pUSDe` storage slot — saves one storage read plus the overhead of an internal function call.

**Impact:**
Unnecessary gas consumption on every deposit. While not directly exploitable, it reduces protocol efficiency and increases user transaction costs.

**Recommended Mitigation:**
Inline `pUSDeDepositor::getPhase` into its sole caller `deposit_sUSDe`, caching the `pUSDe` state variable and passing it directly to `PreDepositPhaser::currentPhase` to eliminate the redundant storage read and function call overhead.

---

**[中文版本]**

**描述：**
`pUSDeDepositor::getPhase` 是一个仅被 `deposit_sUSDe` 调用的小型内部函数。保留其为独立函数会产生不必要的函数调用开销和额外的存储读取。将 `getPhase` 的逻辑直接内联到 `deposit_sUSDe` 中——同时缓存 `pUSDe` 存储槽——可节省一次存储读取及内部函数调用开销。

**影響：**
每次存款都会产生不必要的 gas 消耗。虽不可直接利用，但会降低协议效率并增加用户交易成本。

**修復建議：**
将 `pUSDeDepositor::getPhase` 内联到其唯一调用者 `deposit_sUSDe` 中，缓存 `pUSDe` 状态变量并直接传递给 `PreDepositPhaser::currentPhase`，以消除冗余存储读取和函数调用开销。

---

## 6. LockUpManager::LockUpStorage::_regLockUpTime is never used

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
The field `LockUpManager::LockUpStorage::_regLockUpTime` — defined as the lock-up time for foreign-to-domestic trades — is declared in storage but never read or written anywhere in the codebase. Dead storage slots waste gas on deployment and confuse future developers and auditors about the intended functionality of the field.

**Impact:**
Misleading dead code increases cognitive overhead for developers and auditors. The unused storage slot also wastes gas unnecessarily during contract deployment.

**Recommended Mitigation:**
Either remove `_regLockUpTime` if it serves no purpose, or add a clear comment indicating it is reserved for future use but currently inactive.

---

**[中文版本]**

**描述：**
字段 `LockUpManager::LockUpStorage::_regLockUpTime`——定义为境外到境内交易的锁定期——在存储中声明但在代码库中从未被读取或写入。无效的存储槽在部署时浪费 gas，并使未来的开发者和审计人员对该字段的预期功能产生困惑。

**影響：**
误导性的无效代码增加了开发者和审计人员的认知负担。未使用的存储槽在合约部署时也会不必要地浪费 gas。

**修復建議：**
若 `_regLockUpTime` 无实际用途，则将其删除；或添加明确注释说明其为未来使用预留但当前未激活。

---

## 7. No way to compound deposited supported vault assets into sUSDe stake during yield phase

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Once the yield phase is enabled, `pUSDeVault` still allows new supported vaults to be added and accepts deposits via supported vaults. However, for supported vaults whose underlying asset is not `sUSDe`, there is no mechanism to withdraw the base token (`USDe`) and compound it into the main `sUSDe` vault stake. Assets deposited through non-`sUSDe` supported vaults during the yield phase therefore sit idle and do not generate yield.

**Impact:**
Deposited assets via non-`sUSDe` supported vaults are unable to participate in yield generation once the yield phase is active, resulting in lost yield for those depositors.

**Recommended Mitigation:**
Either prevent adding non-`sUSDe` supported vaults once the yield phase is enabled, or implement a function that withdraws the base token from non-`sUSDe` supported vaults and compounds it into the main `sUSDe` stake.

---

**[中文版本]**

**描述：**
一旦收益阶段启用，`pUSDeVault` 仍允许添加新的支持金库并通过支持金库接受存款。然而，对于底层资产不是 `sUSDe` 的支持金库，没有任何机制可以提取基础代币（`USDe`）并将其复投到主 `sUSDe` 金库质押中。因此，在收益阶段通过非 `sUSDe` 支持金库存入的资产将闲置，无法产生收益。

**影響：**
通过非 `sUSDe` 支持金库存入的资产在收益阶段激活后无法参与收益生成，导致相关存款人的收益损失。

**修復建議：**
在收益阶段启用后，要么禁止添加非 `sUSDe` 支持金库，要么实现一个函数，将非 `sUSDe` 支持金库中的基础代币提取并复投到主 `sUSDe` 质押中。

---

## 8. Non-compliant users can claim withdrawn assets after the cooldown period

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::redeem` and `withdraw` use the `onlyWhitelisted` modifier to ensure the caller is whitelisted or compliant at the time of initiating a withdrawal. However, `StakingVault::claimWithdraw` — which is called after the cooldown period to actually receive the assets — does not apply the same modifier. If a user's whitelist status or compliance status is revoked between the time of initiating the withdrawal and the cooldown expiry, they can still successfully call `claimWithdraw` and receive their assets.

**Impact:**
Non-compliant or de-whitelisted users can bypass compliance controls by initiating a withdrawal while compliant and then claiming the assets after becoming non-compliant, undermining the intent of the whitelist/compliance enforcement.

**Recommended Mitigation:**
Apply the `onlyWhitelisted(msg.sender)` modifier to `StakingVault::claimWithdraw` to re-verify compliance at the point of actual asset claim. Additionally, consider applying `onlyWhitelisted(receiver)` to enforce that the destination address is also compliant.

---

**[中文版本]**

**描述：**
`StakingVault::redeem` 和 `withdraw` 使用 `onlyWhitelisted` 修饰符确保调用者在发起提款时已被白名单认可或符合合规要求。然而，`StakingVault::claimWithdraw`——在冷却期后实际提取资产的函数——未应用相同的修饰符。如果用户的白名单或合规状态在发起提款到冷却期到期之间被撤销，其仍可成功调用 `claimWithdraw` 并提取资产。

**影響：**
不合规或已被移除白名单的用户可通过在合规时发起提款、变为不合规后再提取资产来绕过合规控制，破坏白名单/合规执行的意图。

**修復建議：**
在 `StakingVault::claimWithdraw` 上应用 `onlyWhitelisted(msg.sender)` 修饰符，在实际资产领取时重新验证合规性。此外，考虑应用 `onlyWhitelisted(receiver)` 以确保目标地址也符合合规要求。

---

## 9. Reserved assets could be extracted from the Vault

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
Several `FixedTerm` strategy functions (`acceptLoanLocked`, `borrow`, `pay`, `acceptLoanDynamic`, `claimInterest`) can release assets without verifying whether those assets are part of the vault's `reservedLiquidity`. The `AccountableFixedTerm._loan.drawableFunds` value is not synchronized with the withdrawal queue's `reservedLiquidity`, allowing a borrower to inadvertently access funds that the vault has already reserved for pending withdrawals.

**Impact:**
The vault can become insolvent by releasing funds needed to honor pending withdrawals. A formal verification invariant (`reservedLiquidityBacked`) confirms this violation is possible: `ghostReservedLiquidity256` can exceed `ghostTotalAssets256`.

**Recommended Mitigation:**
When `reservedLiquidity` is increased in the withdrawal queue, this update must be synchronized with the `FixedTerm` strategy's `drawableFunds` to prevent over-borrowing against reserved assets.

---

**[中文版本]**

**描述：**
多个 `FixedTerm` 策略函数（`acceptLoanLocked`、`borrow`、`pay`、`acceptLoanDynamic`、`claimInterest`）可在不验证相关资产是否属于金库 `reservedLiquidity` 的情况下释放资产。`AccountableFixedTerm._loan.drawableFunds` 与提款队列的 `reservedLiquidity` 不同步，允许借款人无意间访问金库已为待处理提款预留的资金。

**影響：**
金库可能因释放了用于兑现待处理提款的资金而资不抵债。形式化验证不变量（`reservedLiquidityBacked`）确认了此违规的可能性：`ghostReservedLiquidity256` 可超过 `ghostTotalAssets256`。

**修復建議：**
当提款队列中的 `reservedLiquidity` 增加时，必须将此更新同步到 `FixedTerm` 策略的 `drawableFunds`，以防止对预留资产的过度借贷。

---

## 10. Treasury cannot withdraw expired assets if NFT is disabled

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
`STBL_LT1_Issuer::withdrawExpired` contains a logic inversion: it calls `iSTBL_LT1_AssetYieldDistributor(AssetData.rewardDistributor).claim(_tokenID)` only when `MetaData.isDisabled == true`. However, `STBL_LT1_YieldDistributor::claim` explicitly reverts with `STBL_YLDDisabled(id)` when the metadata is disabled. This means `withdrawExpired` will always revert for disabled NFTs, preventing the treasury from recovering expired assets.

**Impact:**
The treasury is permanently blocked from calling `withdrawExpired` on any NFT whose metadata is disabled, creating a denial of service for asset recovery on the full set of disabled NFTs.

**Recommended Mitigation:**
Modify `STBL_LT1_YieldDistributor::claim` to allow calls from the issuer address even when the NFT is disabled, while still blocking regular user claims. Alternatively, fix the conditional in `withdrawExpired` to skip the `claim` call for disabled NFTs.

---

**[中文版本]**

**描述：**
`STBL_LT1_Issuer::withdrawExpired` 存在逻辑反转：仅当 `MetaData.isDisabled == true` 时才调用 `iSTBL_LT1_AssetYieldDistributor(AssetData.rewardDistributor).claim(_tokenID)`。然而，`STBL_LT1_YieldDistributor::claim` 在元数据被禁用时会显式以 `STBL_YLDDisabled(id)` 回滚。这意味着 `withdrawExpired` 对于已禁用的 NFT 始终会回滚，阻止财政部收回过期资产。

**影響：**
财政部对任何元数据已禁用的 NFT 调用 `withdrawExpired` 都会被永久阻止，对所有已禁用 NFT 的资产恢复造成拒绝服务。

**修復建議：**
修改 `STBL_LT1_YieldDistributor::claim`，允许发行人地址在 NFT 被禁用时仍可调用，同时继续阻止普通用户的调用。或者，修复 `withdrawExpired` 中的条件逻辑，对已禁用 NFT 跳过 `claim` 调用。
