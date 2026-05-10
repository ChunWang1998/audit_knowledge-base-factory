# rewards-referral (18)

> Issues in reward distribution, referral mechanics, and fee calculation that cause incorrect payouts or griefing.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. `DepositManager::_refundEntryFee` doesn't deduct referral rewards allowing users to join then leave games to drain tokens via inflated referral rewards they aren't entitled to

**Severity:** 🔴 Critical
**Source:** `cyfrin/protocol.md`

**Description:**
`DepositManager::_payEntryFee` increments the referral rewards for the user's referrer when a player joins a game. However, `DepositManager::_refundEntryFee` does not deduct the referral rewards when a user leaves the game and their fee is refunded. This asymmetry means that every join-leave cycle permanently inflates referral reward balances, even though no lasting economic participation occurred.

**Impact:**
Malicious users can intentionally join then leave rescheduled games to drain tokens from the contract via inflated referral rewards they aren't entitled to. This bug can also occur naturally without malicious users: users who join then leave give referrers more reward allocation than they are entitled to. Once the game ends and referrers claim their inflated rewards, there will not be enough tokens to distribute to winners or for creator/protocol fees.

**Recommended Mitigation:**
`DepositManager::_refundEntryFee` should deduct from the referral rewards when refunding the game fee, symmetrically to how `_payEntryFee` adds to the referral rewards when receiving the game fee.

---

**[中文版本]**

**描述：**
`DepositManager::_payEntryFee` 在玩家加入游戏时增加推荐人的奖励，但 `DepositManager::_refundEntryFee` 在玩家退出游戏退款时不扣减推荐奖励。这一非对称设计意味着每次加入-离开循环都会永久增大推荐奖励余额，即使没有实际参与游戏。

**影響：**
恶意用户可以故意加入再离开重新安排的游戏，通过虚增的推荐奖励耗尽合约代币。即使没有恶意行为，正常的加入-离开行为也会给推荐人分配超额奖励，导致游戏结束后缺乏足够代币支付获奖者和手续费。

**修復建議：**
`_refundEntryFee` 在退款时应对称地扣减推荐奖励，与 `_payEntryFee` 增加推荐奖励的逻辑保持对称。

---

## 2. Instant withdrawals in priority pool can result in loss of funds for StakingProxy contract

**Severity:** 🔴 Critical
**Source:** `cyfrin/stakingproxy.md`

**Description:**
When instant withdrawals are enabled in the priority pool, stakers can permanently lose funds when withdrawing through the `StakingProxy` contract. In `PriorityPool::_withdraw`, when tokens are withdrawn from the staking pool via the instant withdrawal path, the `withdrawn` variable is not updated after the withdrawal succeeds. The function tracks withdrawn amounts in `withdrawn` for subsequent token transfers to the caller, so since `withdrawn` remains zero from the instant path, the actual tokens are never transferred to `StakingProxy`.

**Impact:**
`StakingProxy` permanently loses access to its liquid staking tokens. The withdrawn tokens accumulate inside the `PriorityPool` contract with no mechanism for the staker to retrieve them, while the LSTs are already burned from `StakingProxy`.

**Recommended Mitigation:**
Update the `withdrawn` variable when processing instant withdrawals in `PriorityPool::_withdraw`, symmetrically to how it is updated in the queue-based path.

---

**[中文版本]**

**描述：**
优先池启用即时提款时，用户通过 `StakingProxy` 提款会导致永久资金损失。`PriorityPool::_withdraw` 的即时提款路径在成功从质押池提款后，没有更新 `withdrawn` 变量。由于 `withdrawn` 保持为零，实际代币不会转移给 `StakingProxy`。

**影響：**
`StakingProxy` 永久失去流动性质押代币，被提取的代币滞留在 `PriorityPool` 合约内，同时 LST 已经从 `StakingProxy` 销毁。

**修復建議：**
在 `PriorityPool::_withdraw` 处理即时提款时，对称地更新 `withdrawn` 变量。

---

## 3. [DualDefense] Exited Delegator Receives Rewards

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
In the Hayabusa Stargate protocol, a delegator who has already exited can continue claiming VTHO rewards from future periods they are no longer part of. The bug sits in `_claimableDelegationPeriods`, where the equality case `endPeriod == nextClaimablePeriod` is not treated as an ended delegation. When `endPeriod == nextClaimablePeriod`, the "delegation ended" branch is bypassed and the function falls through to the active delegation path, returning a positive claimable range for an exited NFT. This allows the exited NFT to claim rewards from periods where it is no longer part of the delegator set.

**Impact:**
Exited delegators can drain VTHO from periods where they have no stake, directly at the expense of active delegators whose rewards are diluted. Since the total reward pool for a period is fixed, each illegitimate claim reduces what honest active delegators receive.

**Recommended Mitigation:**
Change the boundary check in `_claimableDelegationPeriods` from `endPeriod > nextClaimablePeriod` to `endPeriod >= nextClaimablePeriod` so that the equality case is correctly treated as an ended delegation.

---

**[中文版本]**

**描述：**
在 Hayabusa Stargate 协议中，已退出的委托人可以继续领取未来周期的 VTHO 奖励。漏洞位于 `_claimableDelegationPeriods` 函数，`endPeriod == nextClaimablePeriod` 的边界情况没有被识别为已结束的委托，导致函数错误地返回正数可领取周期范围。

**影響：**
已退出的委托人可以从他们不再参与的周期中窃取 VTHO，直接稀释仍在活跃委托人的奖励。

**修復建議：**
将 `_claimableDelegationPeriods` 中的边界检查从 `endPeriod > nextClaimablePeriod` 改为 `endPeriod >= nextClaimablePeriod`，正确处理边界相等情况。

---

## 4. Incorrect BeforeSwapDelta Mapping Causes Fee To Be Applied To Wrong Swap Side

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Launchly.txt`

**Description:**
`LaunchlyBNBHook` collects a 2% fee on native currency input in its `_beforeSwap` callback. When returning the `BeforeSwapDelta` to account for this fee, the hook chooses between placing the delta in the first or second field based on whether native currency is `currency0` or `currency1`. However, in Uniswap v4, `BeforeSwapDelta(specifiedDelta, unspecifiedDelta)` corresponds to the specified and unspecified currencies, not to `currency0` and `currency1`. When native is `currency1` and is also the input (specified) currency, the hook incorrectly places the delta in the unspecified component, creating an accounting mismatch between the `take()` call and the returned delta.

**Impact:**
The fee delta is applied to the wrong leg of the swap. The specified amount sent to the pool does not correctly reflect the deducted fee, potentially reverting swaps (denial of service) or mischarging users by affecting the wrong side of the trade.

**Recommended Mitigation:**
Return the `BeforeSwapDelta` based on whether native currency is the specified or unspecified currency in the swap, not based on whether it is `currency0` or `currency1`.

---

**[中文版本]**

**描述：**
`LaunchlyBNBHook` 在收取原生货币输入的 2% 手续费后，根据原生货币是 `currency0` 还是 `currency1` 来决定 `BeforeSwapDelta` 字段位置。但 Uniswap v4 中两个字段对应的是 specified/unspecified 货币，而非 currency0/currency1，导致费用 delta 被放入错误字段。

**影響：**
手续费 delta 应用到错误的交易方，导致池端交易金额与实际扣除不匹配，可能引发交易回滚或对用户错误收费。

**修復建議：**
根据原生货币是否为 specified 货币（而非其在 currency0/currency1 中的位置）来决定 delta 字段。

---

## 5. Incorrect summation of curator shares in `claimUndistributedRewards` leads to deficit in claimed undistributed rewards

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
`claimUndistributedRewards` calculates `totalDistributedShares` by summing curator shares across all vaults. For each vault, it adds `curatorShares[epoch][curator]` to the total. However, `curatorShares[epoch][curator]` already stores the total accumulated share for that curator across all their vaults and all operators. When a curator owns multiple vaults, their aggregate share is added multiple times — once for each vault they own — vastly overestimating the total distributed shares.

**Impact:**
The denominator used to calculate claimable undistributed rewards is inflated, causing the `REWARDS_DISTRIBUTOR_ROLE` to receive a fraction of what they should. The protocol permanently underrecovers unclaimed rewards.

**Recommended Mitigation:**
Track curator shares per vault (not aggregated per curator) when summing for `totalDistributedShares`, or deduplicate curators before summing their per-curator aggregate shares.

---

**[中文版本]**

**描述：**
`claimUndistributedRewards` 计算 `totalDistributedShares` 时，对每个 vault 都将 `curatorShares[epoch][curator]` 加入总量。但该映射已存储了 curator 在该 epoch 所有 vault 的累计份额。当一个 curator 拥有多个 vault 时，其总份额被多次叠加，极大高估了已分配份额。

**影響：**
可领取的未分配奖励被严重低估，协议无法正确回收未领取的奖励。

**修復建議：**
按 vault 追踪 curator 份额而非聚合值，或在加总前对 curator 地址去重。

---

## 6. Team Rewards Accumulate Without Required Active Stake

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The protocol documentation states "The user must have an active stake" to receive team rewards. However, `_processTeamRewards()` does not verify whether the referrer has an active stake before accumulating team rewards. This allows users to register and subscribe without staking, accumulate team rewards from their downlines' claims over time, then stake a minimal amount and immediately claim all accumulated rewards.

**Impact:**
Users can bypass the staking requirement entirely: accumulate large team rewards without real staking commitment, then stake minimally and extract all accumulated rewards. This undermines the staking incentive model and violates the documented requirement.

**Recommended Mitigation:**
Add an active stake check for the referrer inside `_processTeamRewards()` before accumulating rewards, consistent with the documented invariant.

---

**[中文版本]**

**描述：**
协议文档规定"用户必须有有效质押"才能获取团队奖励，但 `_processTeamRewards()` 在累积团队奖励前不检查推荐人是否持有有效质押。用户可注册后不质押，仅通过下线的领取积累奖励，最后用最少量质押一次性领取全部奖励。

**影響：**
用户可完全绕过质押要求，从团队奖励系统中套利，破坏质押激励模型。

**修復建議：**
在 `_processTeamRewards()` 中，累积奖励前对推荐人添加有效质押检查。

---

## 7. Incorrect Handling of `reserveFee` During `dex()` Execution

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
The `BondingCurve` contract defines a fee structure with several components including `reserveFee`, `teamFee`, `ecosystemFee`, and others. When `dex()` is called, all fees are intended to be distributed to their respective beneficiaries. However, while most fee components (`teamFee`, `ecosystemFee`) are transferred correctly, `reserveFee` is never transferred — it remains permanently locked inside the bonding curve contract.

**Impact:**
`reserveFee` accumulates in the bonding curve contract without any mechanism for the intended recipient to retrieve it, representing a permanent loss of funds intended for the reserve.

**Recommended Mitigation:**
Add the transfer of `reserveFee` amount to the appropriate recipient address within the `dex()` function, parallel to how other fees are distributed.

---

**[中文版本]**

**描述：**
`BondingCurve` 合约定义了包含 `reserveFee` 的费用结构。调用 `dex()` 时，其他费用分发正常，但 `reserveFee` 从未被转账，永久锁定在合约中。

**影響：**
`reserveFee` 永久锁定在合约内，预定接收人无法提取，造成资金损失。

**修復建議：**
在 `dex()` 函数中添加 `reserveFee` 向指定受益人的转账逻辑。

---

## 8. Incorrect Progressive-TGE Calculation Order Leads to Unintended Token Unlocks

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
In the `_buy` function, `totalProjectTokenSold` is incremented before the progressive TGE percentage is calculated via `_calculateTGEPercent`. The TGE percentage is designed to be progressive, scaling from a base percentage toward 100% as more tokens are sold. Because the state is updated first, `_calculateTGEPercent` always uses the post-purchase sold amount, making each buyer receive a slightly larger TGE allocation than intended. More critically, a user who buys all remaining tokens in a single transaction causes `totalProjectTokenSold` to equal `totalTokenToSell`, resulting in a 100% TGE unlock on their entire purchase and bypassing the vesting schedule entirely.

**Impact:**
Every buyer receives a slightly inflated TGE unlock. A buyer who purchases all remaining tokens in one transaction can bypass the vesting schedule entirely and receive 100% of their allocation immediately.

**Recommended Mitigation:**
Calculate the TGE percentage before incrementing `totalProjectTokenSold`, so the calculation reflects the pre-purchase token sold state.

---

**[中文版本]**

**描述：**
在 `_buy` 函数中，`totalProjectTokenSold` 在计算渐进式 TGE 百分比之前就已递增。这导致每位买家收到的 TGE 解锁额度略高于预期。更严重的是，一次性购买所有剩余代币的用户会使比率达到 100%，完全绕过归属计划。

**影響：**
每位买家都会收到略微超额的 TGE 解锁；单次购买全部剩余代币的用户可完全规避归属计划。

**修復建議：**
在递增 `totalProjectTokenSold` 之前先计算 TGE 百分比。

---

## 9. Incorrect Referral Traversal in `_addDownlines()` Skips Intermediate Uplines

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
`Subscription::_addDownlines()` traverses the referral hierarchy to propagate a new user's registration upward. At each iteration it advances with `current = users[current.referrers[level]]`. This uses the level-th referrer of the current node instead of following the direct parent chain. As a result, intermediate uplines in the hierarchy are skipped and never updated with the new downline entry.

**Impact:**
The downline propagation is incorrect — intermediate uplines in the referral tree do not receive the newly registered downline in their records. This breaks referral tracking and can affect reward eligibility calculations that depend on downline counts.

**Recommended Mitigation:**
Fix the traversal to always follow the direct parent's referrer at each level, ensuring no intermediate uplines are skipped.

---

**[中文版本]**

**描述：**
`_addDownlines()` 在遍历推荐层级时使用 `current.referrers[level]` 作为下一个节点，而不是沿着直接父节点链向上遍历。这导致中间层的推荐人被跳过，无法收到新注册用户的下线记录。

**影響：**
推荐树的传播不正确，中间层推荐人的下线记录缺失，影响依赖下线计数的奖励资格计算。

**修復建議：**
修正遍历逻辑，始终沿直接父节点链向上，确保不跳过中间推荐人。

---

## 10. Incorrect `recordResult` recorded for each question in `recordResults`

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
When an UMA oracle assertion is resolved truthfully, `DefaultSession::recordResults` is called to persist player performance data. For each winner and each question, `IPromptStrategy::recordResult` is called with `assertion.totalXPs[i]` and `assertion.totalTimes[i]` — which are the *total average* XP and time across all questions for that player. The `recordResult` function is intended to store the xp and time for a specific question, but it receives the aggregate player values instead.

**Impact:**
Incorrect xp and time values are stored per question for every player. Downstream calls to `getResult`, used in `_calculatePlayerSessionResult`, return inaccurate data, potentially affecting reward distribution or score calculations.

**Recommended Mitigation:**
Pass the question-specific xp and time values when calling `recordResult`, rather than the per-player totals.

---

**[中文版本]**

**描述：**
UMA 预言机断言解决后，`recordResults` 为每个问题调用 `recordResult`，但传入的是玩家在所有问题上的平均总 XP 和时间，而非该题的具体数据。

**影響：**
每个问题存储了错误的 xp/time 值，影响 `getResult` 的返回值和 `_calculatePlayerSessionResult` 的奖励计算。

**修復建議：**
调用 `recordResult` 时传入问题特定的 xp 和时间值，而非玩家总量。

---

## 11. Incorrect error message in `_checkNotBlacklisted`

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The internal function `_checkNotBlacklisted(address _account)` validates that the provided `_account` is not blacklisted. However, the require error message reads `"WLFI: caller is blacklisted"`, which incorrectly describes the blacklisted entity as the caller rather than the input `_account`. The function is often called with a non-caller address (e.g., a token recipient), so the misleading message causes confusion when debugging or auditing.

**Impact:**
Developers and users who encounter this revert message will be misled about which address triggered the blacklist check, complicating debugging and incident response.

**Recommended Mitigation:**
Change the error message from `"WLFI: caller is blacklisted"` to `"WLFI: account is blacklisted"`.

---

**[中文版本]**

**描述：**
`_checkNotBlacklisted(address _account)` 函数验证 `_account` 是否被黑名单列出，但错误信息显示 "WLFI: caller is blacklisted"（调用者被黑名单），而实际被检查的是输入参数 `_account`，两者可能不同。

**影響：**
错误信息会误导开发者和用户，使其认为触发黑名单的是调用者，增加调试和事件响应的难度。

**修復建議：**
将错误信息改为 "WLFI: account is blacklisted"。

---

## 12. Incorrect haircut asset value conversion in `STBL_PT1_Issuer::generateMetaData`

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
In `STBL_PT1_Issuer::generateMetaData`, `haircutAmountAssetValue` is calculated by calling `fetchForwardPrice(MetaData.haircutAmount)`. The problem is that `haircutAmount` is denominated in USD (computed as a percentage of `stableValueGross` which is USD), but `fetchForwardPrice` expects an asset amount as input and returns a USD value. Passing a USD amount to a function expecting an asset amount produces a mathematically incorrect result — the correct conversion should apply the inverse of the oracle price.

**Impact:**
`haircutAmountAssetValue` stored in NFT metadata is incorrect. Off-chain systems reading this metadata receive wrong values, which may affect display, pricing, or downstream integrations.

**Recommended Mitigation:**
Use the inverse of the oracle price (i.e., call `fetchInversePrice` or divide by the oracle price) to convert the USD-denominated `haircutAmount` to its asset denomination.

---

**[中文版本]**

**描述：**
`generateMetaData` 中计算 `haircutAmountAssetValue` 时，调用了 `fetchForwardPrice(haircutAmount)`，但 `haircutAmount` 已是 USD 计价，而该函数期望资产数量作为输入。将 USD 金额传给期望资产金额的函数会产生错误结果，正确做法是使用预言机价格的倒数进行转换。

**影響：**
NFT 元数据中 `haircutAmountAssetValue` 值不正确，影响依赖此元数据的链下系统。

**修復建議：**
使用预言机价格的倒数将 USD 计价的 `haircutAmount` 转换为资产计价。

---

## 13. Incorrect inclusion of removed nodes in `_requireMinSecondaryAssetClasses` during `forceUpdateNodes`

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
During `forceUpdateNodes`, if a node is removed in an early iteration, subsequent iterations still include that node in the `_requireMinSecondaryAssetClasses` calculation because the removal is not immediately reflected in the node list. This means the function evaluates secondary asset class requirements using a stale node set that includes nodes already flagged for removal.

**Impact:**
Inaccurate node removal decisions: nodes that should remain active may be incorrectly removed because the apparent secondary asset class coverage is reduced by including already-removed nodes in the check. In pathological cases all nodes for an operator could be removed. This only manifests when operator stake dropped from the last epoch and `limitStake` is small.

**Recommended Mitigation:**
Filter out nodes already flagged for removal before calling `_requireMinSecondaryAssetClasses` in each iteration, ensuring the function operates on the current effective node set.

---

**[中文版本]**

**描述：**
`forceUpdateNodes` 遍历节点时，早期迭代中被删除的节点在后续迭代的 `_requireMinSecondaryAssetClasses` 计算中仍被包含，因为节点列表未立即更新。这导致次级资产类别要求基于包含已删除节点的过期集合进行评估。

**影響：**
节点移除决策不准确，本应保留的节点可能被错误移除。在最坏情况下可导致运营商的所有节点都被移除。

**修復建議：**
在每次迭代调用 `_requireMinSecondaryAssetClasses` 之前，过滤掉已标记为移除的节点。

---

## 14. Incorrect `maxSellAmount` Calculation Allows Selling Up to Total Supply Amount

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The NTE token's anti-dump mechanism limits sell amounts based on `maxSellPercentage`, which is validated to be at most 100 (representing 1% in basis points). Inside `_transferWithTax`, the calculation `maxSellAmount = (_totalSupply * maxSellPercentage) / 100` uses the wrong denominator. A value of 100 for `maxSellPercentage` should represent 1%, so the denominator should be 10000 (basis points). Using 100 as denominator means `maxSellPercentage = 100` yields `maxSellAmount = _totalSupply`, completely defeating the anti-dump protection.

**Impact:**
The anti-dump mechanism is effectively bypassed — users can sell up to the entire token supply in a single transaction even with `antiDumpEnabled = true`, leading to potential tokenomics disruption and market instability.

**Recommended Mitigation:**
Change the denominator from `100` to `10000` in the `maxSellAmount` calculation to correctly interpret basis-point values.

---

**[中文版本]**

**描述：**
NTE 代币的防抛售机制在计算 `maxSellAmount` 时使用除数 100，但 `maxSellPercentage` 是用基点（10000）表示的百分比值（100 = 1%）。错误的除数导致当 `maxSellPercentage = 100` 时，`maxSellAmount = totalSupply`，完全失去限制作用。

**影響：**
即使启用了防抛售功能，用户仍可在单笔交易中出售全部代币供应量，破坏代币经济模型。

**修復建議：**
将 `maxSellAmount` 计算中的除数从 `100` 改为 `10000`。

---

## 15. Incorrect vault status determination in `MiddlewareVaultManager`

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`MiddlewareVaultManager::_wasActiveAt` returns `true` when `disabledTime >= timestamp`, meaning a vault disabled at exactly the epoch boundary timestamp is considered active for that epoch. The intended semantics should be that disabling a vault at timestamp T makes it inactive from T onward. The off-by-one boundary condition `>=` vs `>` causes the vault to be incorrectly included in epoch-boundary queries.

**Impact:**
Vaults disabled at an epoch boundary are incorrectly classified as active for that epoch and included in reward distributions, stake accounting, and other epoch-based calculations for one extra epoch.

**Recommended Mitigation:**
Change `disabledTime >= timestamp` to `disabledTime > timestamp` so that a vault disabled exactly at the epoch timestamp is treated as inactive from that point forward.

---

**[中文版本]**

**描述：**
`_wasActiveAt` 函数使用 `disabledTime >= timestamp` 判断，导致在 epoch 边界时间戳恰好被禁用的 vault 仍被认为是活跃的。正确语义应为：在时间戳 T 禁用的 vault 从 T 起即为非活跃。

**影響：**
在 epoch 边界被禁用的 vault 被错误地包含在该 epoch 的奖励分发和权益核算中。

**修復建議：**
将 `disabledTime >= timestamp` 改为 `disabledTime > timestamp`。

---

## 16. Reducing reserves requesting `USDe` as the asset to receive causes the Strategy to release more `sUSDe` than necessary

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
In `sUSDeStrategy::reduceReserve`, when the caller requests `USDe` as the asset to receive, the function transfers `tokenAmount` units of `sUSDe` directly to the receiver. However, `tokenAmount` is denominated in `USDe`, not `sUSDe`. Since the `sUSDe`/`USDe` exchange rate is greater than 1:1 (sUSDe accrues yield), transferring `tokenAmount` sUSDe releases far more USDe-equivalent value than requested.

**Impact:**
The strategy releases excess sUSDe to cover the requested USDe amount. Depositors incur a loss because the strategy is left with less sUSDe than it should have.

**Recommended Mitigation:**
Call `sUSDe.previewWithdraw(tokenAmount)` to determine the correct number of sUSDe shares needed to cover the requested `tokenAmount` of USDe, and transfer that amount instead.

---

**[中文版本]**

**描述：**
`sUSDeStrategy::reduceReserve` 在请求 `USDe` 时，直接将 `tokenAmount`（USDe 计价）数量的 sUSDe 转出。由于 sUSDe 的汇率高于 1:1，转出的 sUSDe 实际价值远超所请求的 USDe。

**影響：**
策略释放了超额的 sUSDe，导致存款人蒙受损失，策略持有的 sUSDe 低于应有数量。

**修復建議：**
调用 `sUSDe.previewWithdraw(tokenAmount)` 获取所需 sUSDe 数量，再进行转账。

---

## 17. Unclaimable rewards for removed vaults in `Rewards::claimRewards`

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
In `Rewards::claimRewards`, stakers iterate over epochs and claim rewards via `_getStakerVaults`, which calls `middlewareVaultManager.getVaults(epoch)`. If a vault is removed from the system after rewards are distributed for an epoch but before a staker claims those rewards, `getVaults(epoch)` no longer returns the removed vault. The staker's iteration skips the removed vault entirely, and any rewards associated with it remain permanently locked in the contract.

**Impact:**
Rewards become permanently unclaimable for stakers who were active in vaults that were subsequently removed. These tokens are permanently stuck in the `Rewards` contract.

**Recommended Mitigation:**
Maintain a historical registry of vaults per epoch that is immutable once set, so that even removed vaults remain queryable for past epoch reward claims.

---

**[中文版本]**

**描述：**
`claimRewards` 通过 `getVaults(epoch)` 获取 vault 列表。如果奖励分发后、用户领取前某 vault 被移除，`getVaults` 不再返回该 vault，相关奖励永久锁定在合约中无法领取。

**影響：**
曾在已移除 vault 中质押的用户无法领取对应奖励，相关代币永久锁定在 `Rewards` 合约中。

**修復建議：**
为每个 epoch 维护不可变的历史 vault 注册表，确保移除的 vault 仍可用于历史 epoch 奖励查询。

---

## 18. Uptime loss due to integer division in `UptimeTracker::computeValidatorUptime` can make validator lose entire rewards for an epoch

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
In `UptimeTracker::computeValidatorUptime`, uptime is distributed across multiple epochs using `uptimePerEpoch = uptimeToDistribute / elapsedEpochs`. Solidity integer division truncates the remainder, discarding up to `elapsedEpochs - 1` seconds per computation. This truncation is never recovered. If the resulting per-epoch uptime falls even 1 second below `minRequiredUptime`, the `Rewards` contract sets the operator's share to zero for that epoch, causing complete loss of epoch rewards due to a minor precision loss.

**Impact:**
Precision loss from integer division can eliminate all rewards for a validator for one or more epochs, even when the validator legitimately accumulated sufficient total uptime.

**Recommended Mitigation:**
Add the truncated remainder to one epoch (e.g., the most recent epoch) so total uptime is never lost. Alternatively, round up per-epoch distribution to avoid shortfall near the threshold.

---

**[中文版本]**

**描述：**
`computeValidatorUptime` 将总运行时间均分到各 epoch 时，使用整数除法 `uptimeToDistribute / elapsedEpochs`，余数被丢弃且永不恢复。若每 epoch 的运行时间因此低于 `minRequiredUptime` 哪怕 1 秒，该 epoch 的全部奖励都会归零。

**影響：**
整数除法导致的精度损失可使验证人在某些 epoch 完全失去奖励，即使实际总运行时间已足够。

**修復建議：**
将截断的余数加到某个 epoch（如最新 epoch），确保总运行时间不丢失；或对每 epoch 分配值向上取整以避免阈值不足。
