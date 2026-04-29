# rewards-block (14)

> Issues causing DoS in reward distribution, epoch processing, or stake rebalancing operations.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Critical DOS in queue processing if async cancellations are allowed

**Severity:** 🔴 Critical
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableAsyncRedeemVault::cancelRedeemRequest` marks `state.pendingCancelRedeemRequest = true` when a user cancels a redeem. If the strategy returns `false` from `onCancelRedeemRequest` (indicating an async cancellation), the shares are not immediately reduced and `_reduce` is deferred until `fulfillCancelRedeemRequest` is called. When `processUpToShares` or `processUpToRequestID` later iterates the queue, `_processRequest` returns normal request data because `request.shares` was not reduced. The loop then calls `_fulfillRedeemRequest`, which reverts because `state.pendingCancelRedeemRequest == true`. A single async cancellation anywhere in the queue therefore makes the entire batch processing revert, and an attacker can front-run any process call by creating and async-cancelling a request.

**Impact:**
Queue processing can be repeatedly DoSed under normal operations, as well as by an attacker who front-runs a process call with an async cancellation in protocols that allow async cancellations. This prevents any withdrawals from being processed for the duration of the attack.

**Recommended Mitigation:**
Remove support for async cancellations from the system entirely, which eliminates the DoS attack vector.

---

**[中文版本]**

**描述：**
当用户取消赎回时，`AccountableAsyncRedeemVault::cancelRedeemRequest` 会将 `state.pendingCancelRedeemRequest` 设为 `true`。若策略从 `onCancelRedeemRequest` 返回 `false`（表示异步取消），份额不会立即减少，`_reduce` 被延迟至 `fulfillCancelRedeemRequest` 调用时执行。随后当 `processUpToShares` 或 `processUpToRequestID` 遍历队列时，`_processRequest` 返回正常请求数据（因为 `request.shares` 未被减少），进而调用 `_fulfillRedeemRequest`，但后者因 `state.pendingCancelRedeemRequest == true` 而回滚。队列中任意一笔异步取消都会导致整批处理回滚，攻击者可通过抢先创建异步取消请求来反复触发 DoS。

**影響：**
队列处理在正常操作中以及攻击者通过异步取消请求发起抢先攻击时均会被重复 DoS，导致在攻击期间所有提款无法处理。

**修復建議：**
从系统中完全移除对异步取消的支持，彻底消除此 DoS 攻击向量。

---

## 2. Dust limit attack on forceUpdateNodes allows DoS of rebalancing and potential vault insolvency

**Severity:** 🔴 Critical
**Source:** `cyfrin/core.md`

**Description:**
`forceUpdateNodes` is callable by anyone during the final window of each epoch and accepts a `limitStake` parameter with no minimum bound check. An attacker can call `forceUpdateNodes` with a `limitStake` of 1 wei, which sets all validator nodes into a pending update state without meaningfully reducing any stake (precision loss in stake-to-weight conversion prevents any actual weight change). Once nodes are marked as `nodePendingUpdate[validationID] = true`, all subsequent legitimate rebalancing attempts in the same epoch revert. This effectively blocks the entire rebalancing mechanism for the epoch, preventing excess stake from being removed from nodes even when large vault undelegations have occurred.

**Impact:**
Operators with excess stake can exploit this to retain more stake than they are entitled to. Systematic prevention of rebalancing across epochs means operator nodes retain stake that should be liquid in vaults. If multiple large withdrawals occur simultaneously while rebalancing is blocked, the protocol could become insolvent when vault liquid assets are less than pending withdrawal requests.

**Recommended Mitigation:**
Enforce a minimum meaningful `limitStake` value in `forceUpdateNodes` to prevent dust-amount attacks. The minimum should be sufficient to cause at least one unit of weight change in the stake-to-weight conversion.

---

**[中文版本]**

**描述：**
`forceUpdateNodes` 可在每个 epoch 的最后窗口由任何人调用，且 `limitStake` 参数没有最低值检查。攻击者可以用 1 wei 的 `limitStake` 调用该函数，在不实质性减少任何质押的情况下（因精度损失导致实际权重不变），将所有验证节点标记为 `nodePendingUpdate[validationID] = true`。一旦节点被标记为待更新，同一 epoch 内所有后续合法的再平衡尝试均会回滚，整个再平衡机制被封锁。

**影響：**
超额质押的运营商可借此保留超出权益的质押。系统性阻止跨 epoch 再平衡意味着节点持有的质押无法回流至金库。若在再平衡被阻断期间发生大量提款，金库流动资产可能低于待处理提款请求，导致协议资不抵债。

**修復建議：**
在 `forceUpdateNodes` 中强制执行有意义的最低 `limitStake` 值，防止粉尘金额攻击。最低值应足以在权益-权重转换中产生至少一个单位的权重变化。

---

## 3. Transfer/Approval Bypass and DoS Due To Missing Access Control

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/Panini America.txt`

**Description:**
The `setPaniniLock` function in the `SmartValidator` contract lacks any access control modifier, allowing any external address to enable or disable the Panini Lock mechanism. When the Panini Lock is enabled, it enforces that only token owners or whitelisted marketplaces can perform transfers and approvals. By calling `setPaniniLock(false)`, any attacker can disable these restrictions and allow unauthorized transfers of NFTs to any address. Conversely, by calling `setPaniniLock(true)`, an attacker can enable the lock when it should be disabled, preventing legitimate users from transferring their NFTs even to themselves or approved marketplaces.

**Impact:**
The entire security architecture of the NFT protocol is compromised. Attackers can either bypass all transfer restrictions to redirect NFTs to any address, or cause a protocol-wide DoS by locking all NFT transfers and approvals, depending on the current state of the lock.

**Recommended Mitigation:**
Implement proper access control by restricting `setPaniniLock` to authorized roles only, using an appropriate access control modifier such as `onlyRole(ADMIN_ROLE)` or `onlyOwner`.

---

**[中文版本]**

**描述：**
`SmartValidator` 合约中的 `setPaniniLock` 函数缺少任何访问控制修饰符，任何外部地址均可启用或禁用 Panini Lock 机制。该机制启用时，仅代币所有者或白名单市场可执行转账和授权操作。攻击者通过调用 `setPaniniLock(false)` 可绕过所有转账限制，向任意地址转移 NFT；通过调用 `setPaniniLock(true)` 则可阻止所有合法 NFT 转账，包括向自身或已授权市场的转账。

**影響：**
整个 NFT 协议的安全架构被破坏。攻击者可选择绕过所有转账限制将 NFT 重定向至任意地址，或对整个协议的 NFT 转账和授权造成全面 DoS。

**修復建議：**
通过添加适当的访问控制修饰符（如 `onlyRole(ADMIN_ROLE)` 或 `onlyOwner`）将 `setPaniniLock` 限制为仅授权角色可调用。

---

## 4. Allowance-Based Withdrawals Can Revert Due to Cooldown Request Slot Limits

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The tranche withdraw/redeem logic allows third parties to withdraw on behalf of a user via allowance. When such a withdrawal is executed using `SharesLock` exit mode, a redeem request is created via `requestRedeem`. Inside `requestRedeem`, cooldown requests are rate-limited for external receivers: if `initialFrom != to` and the request count reaches `PUBLIC_REQUEST_SLOTS_CAP`, the call reverts. This condition treats any case where `initialFrom != to` as an external receiver, including allowance-based scenarios where a trusted third party withdraws and sets `to = caller`. As a result, legitimate allowance-based withdrawals can unexpectedly hit the public request slot cap and revert, even though they are authorized operations.

**Impact:**
Allowance-based withdrawals using `SharesLock` mode can unexpectedly revert due to cooldown request slot limits, breaking integrations and delegated withdrawal workflows. The constraint is non-obvious and not enforced at the allowance-checking level, making it likely to surprise integrators.

**Recommended Mitigation:**
Explicitly account for allowance-based withdrawals in cooldown request validation so that authorized delegated withdrawals are treated as private requests rather than public external receiver requests.

---

**[中文版本]**

**描述：**
Tranche 的提款/赎回逻辑允许第三方通过授权代表用户提款。当此类提款使用 `SharesLock` 退出模式时，`requestRedeem` 内部会对外部接收方进行速率限制：若 `initialFrom != to` 且请求数量达到 `PUBLIC_REQUEST_SLOTS_CAP` 上限，调用将回滚。这一判断将 `initialFrom != to` 的所有情况均视为外部接收方，包括受信第三方通过授权提款并将 `to` 设为调用方的合法场景，导致合法的授权提款意外触发公共请求槽位上限而回滚。

**影響：**
使用 `SharesLock` 模式的授权委托提款可能因冷却请求槽位限制而意外回滚，破坏集成和委托提款工作流。该限制不明显且未在授权检查层面执行，容易使集成方措手不及。

**修復建議：**
在冷却请求验证中明确区分授权委托提款，将其视为私有请求而非公共外部接收方请求。

---

## 5. Burn and seize functions can be DoSed when investor has several wallets that they control

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
The `burn` function in `TokenLibrary.sol` checks `walletsBalances[_who]` (individual wallet balance) instead of `investorsBalances[investorId]` (total investor balance across all wallets). When an investor transfers tokens from their original wallet to another wallet they control, the `burn` function will fail with "Not enough balance" even though the investor still owns the full amount across their wallets. The same logic flaw affects the `seize` function. An investor who knows a burn or seize is imminent can front-run the transaction by moving their tokens to another wallet, rendering the burn unreachable on the targeted wallet.

**Impact:**
Investors can temporarily prevent token burning or seizure by front-running admin operations to transfer tokens between their own wallets. This prevents compliance-critical operations from being executed unless the protocol uses private mempools or burns all wallets simultaneously.

**Recommended Mitigation:**
Options include routing sensitive admin operations through private mempool services to prevent front-running, removing the `addWalletByInvestor` function to prevent investors from distributing tokens across multiple wallets, or adding `burnAll` and `seizeAll` functions that iterate over every wallet belonging to an investor.

---

**[中文版本]**

**描述：**
`TokenLibrary.sol` 中的 `burn` 函数检查的是 `walletsBalances[_who]`（单个钱包余额）而非 `investorsBalances[investorId]`（投资人在所有钱包的总余额）。当投资人将代币从目标钱包转移至其控制的另一个钱包时，即使投资人仍持有全部代币，`burn` 函数也会因"余额不足"而失败。`seize` 函数存在相同逻辑缺陷。投资人可以通过抢先将代币移至其他钱包来临时阻止销毁操作。

**影響：**
投资人可通过在自己的钱包间转移代币来抢先阻止管理员的销毁或没收操作，导致合规关键操作无法执行，除非协议使用私有内存池或同时处理所有钱包。

**修復建議：**
可选方案包括：通过私有内存池服务（如 Flashbots）路由敏感管理操作以防止抢先攻击；移除 `addWalletByInvestor` 函数以防止投资人分散代币；或添加 `burnAll` 和 `seizeAll` 函数以遍历并处理投资人的所有钱包。

---

## 6. DoS via Concurrent Joint Contributor Invites

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
The `Komiti` contract allows a Primary Contributor to invite a Secondary Contributor to share a slot via `joinGroupWithJointContributor`. The contract enforces a single-slot restriction by checking `s_contributions[groupId][msg.sender] == 0`. However, `s_contributions` is only updated when a Secondary accepts the invite via `acceptInviteForJointContributor`. A Primary Contributor can exploit the timing gap by sending multiple invites concurrently before any are accepted, causing the check to pass multiple times. Each acceptance then pushes the Primary's address into `group.members` multiple times, creating duplicate slots. In the final payout cycle, when the loop encounters the Primary's duplicate slot and they have already been paid, it skips them. The loop eventually completes without finding any eligible winner and reverts with "No eligible winner found", permanently locking the funds collected for that final cycle.

**Impact:**
The final payout cycle of any group where duplicate slots exist becomes permanently unprocessable. The entire pot for that final cycle is irretrievably locked in the contract.

**Recommended Mitigation:**
Update the Primary Contributor's `s_contributions` mapping immediately when `joinGroupWithJointContributor` is called, before any invitation is accepted, to prevent the check from passing on subsequent concurrent calls.

---

**[中文版本]**

**描述：**
`Komiti` 合约允许主要贡献者通过 `joinGroupWithJointContributor` 邀请次要贡献者共享槽位，并通过检查 `s_contributions[groupId][msg.sender] == 0` 强制单槽位限制。但 `s_contributions` 仅在次要贡献者接受邀请时更新，主要贡献者可利用这一时间差并发发送多个邀请，使检查多次通过。每次接受邀请都会将主要贡献者地址多次推入 `group.members`，产生重复槽位。在最终支付周期中，循环遇到已支付的重复槽位时将其跳过，最终找不到符合条件的获奖者而回滚，导致该周期收集的资金永久锁定。

**影響：**
存在重复槽位的任何组的最终支付周期将永久无法处理，该周期的全部资金将不可挽回地锁定在合约中。

**修復建議：**
在 `joinGroupWithJointContributor` 调用时立即更新主要贡献者的 `s_contributions` 映射，无需等待邀请被接受，以防止并发调用时检查多次通过。

---

## 7. Oracle Inconsistency between surplus computation and post-check causes Surplus::processSurplus(collateralAddress,0) DoS

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
`LibSurplus::_computeCollateralSurplus` uses `LibOracle::readMint` to value collateral, which snaps spot prices to the target price when within the `userDeviation` band. The surplus sizing and the subsequent swap in `Swapper::swapExactInput` both use `readMint` and agree on an inflated (snapped) valuation, so the swap succeeds and mints tokenP at the inflated rate. However, the post-check in `Surplus::processSurplus` calls `LibGetters::getCollateralRatio`, which uses `LibOracle::readRedemption` with `deviation=0` — no snapping, always raw spot. Since more tokenP was minted at the inflated rate but the safety check uses the raw (lower) spot price, the resulting collateral ratio drops below `surplusBufferRatio` and the transaction reverts with `Undercollateralized`.

**Impact:**
`Surplus::processSurplus(collateralAddress, 0)` is DoSed whenever the spot price is below the target but within the `userDeviation` band. The governor can work around it by passing a manually reduced `maxCollateralAmount`, but this requires off-chain knowledge of the oracle divergence.

**Recommended Mitigation:**
Align oracle usage across surplus computation, swap execution, and the post-check safety validation. Either use the same conservative oracle (`readRedemption`) throughout, or compute the surplus conservatively enough that the post-check always passes.

---

**[中文版本]**

**描述：**
`LibSurplus::_computeCollateralSurplus` 使用 `LibOracle::readMint` 对抵押物估值，当现货价格在 `userDeviation` 范围内时会将其快照至目标价格。盈余计算和后续在 `Swapper::swapExactInput` 中的互换均使用 `readMint`，因此互换以膨胀（快照）估值成功执行并铸造了对应数量的 tokenP。然而 `Surplus::processSurplus` 的后置检查调用 `LibGetters::getCollateralRatio`，后者使用 `deviation=0` 的 `LibOracle::readRedemption`（无快照，始终使用原始现货价格）。由于以膨胀价格铸造了更多 tokenP，但安全检查使用较低的原始现货价格，计算出的抵押率低于 `surplusBufferRatio`，交易以 `Undercollateralized` 回滚。

**影響：**
当现货价格低于目标但在 `userDeviation` 范围内时，`Surplus::processSurplus(collateralAddress, 0)` 将被 DoS。治理方可通过传入手动降低的 `maxCollateralAmount` 来绕过，但需要链下了解预言机偏差情况。

**修復建議：**
在盈余计算、互换执行和后置安全检查中对齐预言机使用。要么全程使用保守预言机（`readRedemption`），要么以足够保守的方式计算盈余使后置检查始终通过。

---

## 8. Premature zeroing of epoch rewards in claimUndistributedRewards can block legitimate claims

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`claimUndistributedRewards` can be called when `currentEpoch >= epoch + 2`. Simultaneously, regular users can claim their rewards for epoch as long as `epoch < currentEpoch - 1` (equivalent to `epoch <= currentEpoch - 2`). This creates an overlap where, when `currentEpoch == epoch + 2`, both regular claims for the epoch are still permitted and `claimUndistributedRewards` for the same epoch can also be executed. The function zeros out `rewardsAmountPerTokenFromEpoch[epoch]` before transferring, which immediately prevents any subsequent regular claims from reading reward amounts. Users who have not yet claimed but are still within their valid claiming window will receive zero rewards or have their transactions revert.

**Impact:**
If `REWARDS_DISTRIBUTOR_ROLE` calls `claimUndistributedRewards` at the earliest possible moment, legitimate stakers, operators, and curators who have not yet claimed their epoch rewards lose them entirely. The distributor also receives an inflated "undistributed" amount that includes funds that should have gone to users.

**Recommended Mitigation:**
Ensure a distinct non-overlapping period between when regular claims close and when undistributed rewards can be swept. Modify the timing check in `claimUndistributedRewards` to require `currentEpoch >= epoch + 3` or equivalent.

---

**[中文版本]**

**描述：**
`claimUndistributedRewards` 可在 `currentEpoch >= epoch + 2` 时调用，而普通用户对 epoch 的奖励领取窗口为 `epoch < currentEpoch - 1`（即 `epoch <= currentEpoch - 2`）。当 `currentEpoch == epoch + 2` 时，两者窗口重叠——普通领取和未分配奖励的清扫均可在同一时刻执行。该函数在转账前将 `rewardsAmountPerTokenFromEpoch[epoch]` 清零，立即阻止后续普通领取读取奖励金额，导致仍在有效领取窗口内但尚未领取的用户获得零奖励或交易回滚。

**影響：**
若 `REWARDS_DISTRIBUTOR_ROLE` 在最早可能的时刻调用 `claimUndistributedRewards`，尚未领取当轮 epoch 奖励的合法质押者、运营商和策展人将损失全部奖励。分发者还会收到包含本应归属用户资金的膨胀"未分配"金额。

**修復建議：**
确保普通领取窗口关闭与未分配奖励可被清扫之间存在不重叠的间隔。将 `claimUndistributedRewards` 的时间检查修改为要求 `currentEpoch >= epoch + 3` 或等效条件。

---

## 9. Rewards distribution DoS due to uncached secondary asset classes

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`_calculateOperatorShare` directly accesses `totalStakeCache` for all asset classes. However, only the primary asset class (`PRIMARY_ASSET_CLASS`) is automatically cached by `addNode` and `forceUpdateNodes`, and only the specific asset class being slashed is cached by the slash function. Secondary asset classes (2, 3, etc.) are only cached when slashing occurs for that specific asset class or when `calcAndCacheStakes` is called manually. When `distributeRewards` is called for an epoch where secondary asset class stakes have not been cached, `totalStakeCache` returns zero, causing a division-by-zero revert in the share calculation.

**Impact:**
Rewards distribution fails for any epoch where secondary asset class stakes were not explicitly cached. While temporary (manual intervention via `calcAndCacheStakes` can fix it), the DoS affects reward distribution timing and may delay legitimate payouts.

**Recommended Mitigation:**
In `_calculateOperatorShare`, check whether the total stake for each asset class is cached before using it. If `totalStakeCache` returns zero for a secondary asset class, automatically trigger `calcAndCacheStakes` for that class before proceeding.

---

**[中文版本]**

**描述：**
`_calculateOperatorShare` 直接访问所有资产类的 `totalStakeCache`。但只有主资产类（`PRIMARY_ASSET_CLASS`）由 `addNode` 和 `forceUpdateNodes` 自动缓存，其他资产类仅在被 slash 时或手动调用 `calcAndCacheStakes` 时才会缓存。当 `distributeRewards` 被调用而次级资产类质押尚未缓存时，`totalStakeCache` 返回零，导致份额计算中除以零回滚。

**影響：**
任何次级资产类质押未被显式缓存的 epoch 的奖励分发将失败。虽然可通过手动调用 `calcAndCacheStakes` 临时修复，但 DoS 会影响奖励分发时机，可能延迟合法收益发放。

**修復建議：**
在 `_calculateOperatorShare` 中，使用前检查每个资产类的总质押是否已缓存。若次级资产类的 `totalStakeCache` 返回零，则在继续执行前自动触发该资产类的 `calcAndCacheStakes`。

---

## 10. Rewards system DOS due to unchecked asset class share and fee allocations

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`Rewards::setRewardsShareForAssetClass` allows `REWARDS_MANAGER_ROLE` to set reward shares for individual asset classes without validating that the total allocation across all asset classes does not exceed 100%. Similarly, individual fee percentages for protocol, operator, and curator are validated only against 100% individually, not cumulatively. When total asset class shares sum to more than 100%, `_calculateOperatorShare` produces inflated operator share values. In extreme cases this causes insolvency for late claimants: earlier claimers drain all available rewards, leaving nothing for those who claim last.

**Impact:**
An over-allocated rewards system can lead to insolvency where the last batch of claimers receives nothing. Additionally, operator share calculations produce values exceeding the available reward pool, with no bounds checking to prevent this.

**Recommended Mitigation:**
Add cumulative validation in `setRewardsShareForAssetClass` to ensure total shares across all asset classes cannot exceed 100%. Apply similar cumulative validation when setting protocol, operator, and curator fee percentages.

---

**[中文版本]**

**描述：**
`Rewards::setRewardsShareForAssetClass` 允许 `REWARDS_MANAGER_ROLE` 为各资产类设置奖励份额，但没有验证所有资产类的总分配是否超过 100%。同样，协议、运营商和策展人的各个费用百分比仅单独验证不超过 100%，未进行累计验证。当各资产类份额之和超过 100% 时，`_calculateOperatorShare` 会产生膨胀的运营商份额值，在极端情况下导致后期领取者资不抵债——早期领取者耗尽所有可用奖励，留给后续领取者的奖励为零。

**影響：**
过度分配的奖励系统可能导致最后一批领取者颗粒无收。运营商份额计算可能产生超出可用奖励池的值，且没有边界检查加以防止。

**修復建議：**
在 `setRewardsShareForAssetClass` 中添加累计验证，确保所有资产类的总份额不超过 100%。对协议、运营商和策展人费用百分比的设置也应实施类似的累计验证。

---

## 11. SettersGovernor::setWhitelistStatus allows values other than 0 and 1 potentially leading to DOS

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
The legacy `SettersGuardian::toggleWhitelist` function only produces values of 0 or 1 for `onlyWhitelisted`. The newer `SettersGovernor::setWhitelistStatus` however accepts any `uint8` value from 0 to 255. If called with any value greater than 1, it sets `collatInfo.onlyWhitelisted > 1` while simultaneously clearing `collatInfo.whitelistData` to empty bytes (due to the else-branch logic). Any subsequent call to functions that check the whitelist will then attempt to `abi.decode` an empty `whitelistData` bytes array and revert on the first line. All swap and redeem operations are therefore DoSed. While governance can call `setWhitelistStatus(0)` to recover, if an `AccessManager` delay has been configured for the governor role, the DoS persists for the entire duration of the configured delay.

**Impact:**
All swaps and redeems for the affected collateral type are DoSed for the duration between the erroneous call and the recovery call. With access manager delays, this can persist for hours or days.

**Recommended Mitigation:**
Restrict the `whitelistStatus` parameter in `setWhitelistStatus` to only accept values of 0 or 1, reverting on any other input.

---

**[中文版本]**

**描述：**
旧版 `SettersGuardian::toggleWhitelist` 函数对 `onlyWhitelisted` 只产生 0 或 1 两个值。而新版 `SettersGovernor::setWhitelistStatus` 接受任意 `uint8` 值（0-255）。若以大于 1 的值调用，会将 `collatInfo.onlyWhitelisted` 设为大于 1 的值，同时因 else 分支逻辑将 `collatInfo.whitelistData` 清空为空字节。后续任何白名单检查调用都会尝试对空 `whitelistData` 执行 `abi.decode` 并在第一行回滚，导致所有互换和赎回操作被 DoS。虽然治理方可以调用 `setWhitelistStatus(0)` 来恢复，但如果治理角色配置了 `AccessManager` 延迟，则 DoS 将持续整个延迟期。

**影響：**
受影响抵押类型的所有互换和赎回操作在错误调用到恢复调用之间被 DoS。配置了访问管理器延迟时，此状态可持续数小时或数天。

**修復建議：**
在 `setWhitelistStatus` 中将 `whitelistStatus` 参数限制为仅接受 0 或 1，对其他任何输入回滚。

---

## 12. Use unchecked block for increment operations in distributeRewards

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
In `Rewards::distributeRewards`, the loop and associated increment operations use checked arithmetic, resulting in unnecessary gas overhead for each iteration. Since the loop counter and batch index increments are bounded by the operator array length and the batch size, which cannot realistically overflow, using unchecked blocks for these increments is safe and significantly reduces gas consumption per distribution call. The same optimization applies to the epoch tracking increments in related functions.

**Impact:**
While not a security vulnerability, the unnecessary checked arithmetic for loop increments in `distributeRewards` causes elevated gas costs for every reward distribution operation, making frequent or large distributions more expensive than necessary.

**Recommended Mitigation:**
Wrap loop increment operations in `unchecked` blocks in `distributeRewards` and related epoch iteration functions where overflow is impossible by construction, following the Solidity best practice of `unchecked { ++i; }` patterns.

---

**[中文版本]**

**描述：**
`Rewards::distributeRewards` 中的循环及相关递增操作使用了有溢出检查的算术运算，在每次迭代中产生不必要的 gas 开销。由于循环计数器和批次索引的递增受到运营商数组长度和批次大小的约束，在实际中不可能溢出，对这些递增操作使用 `unchecked` 块是安全的，且可显著降低每次分发调用的 gas 消耗。相关函数中的 epoch 跟踪递增也适用同样的优化。

**影響：**
虽然不是安全漏洞，但 `distributeRewards` 中循环递增的不必要溢出检查会导致每次奖励分发操作的 gas 成本偏高，使频繁或大规模分发比必要的更昂贵。

**修復建議：**
在 `distributeRewards` 及相关 epoch 迭代函数中，对构造上不可能溢出的循环递增操作使用 `unchecked` 块，遵循 `unchecked { ++i; }` 模式的 Solidity 最佳实践。

---

## 13. YieldManager::unpauseStaking uses stale lstLiabilityPrincipal causing DoS when external actor repays LST liability

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`YieldManager::unpauseStaking` checks `if ($$.lstLiabilityPrincipal > 0)` and reverts if an LST liability exists. However, unlike other places in the codebase that sync `$$.lstLiabilityPrincipal` via `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` before using it, `unpauseStaking` reads the value without syncing first. LST liabilities can be settled by external parties directly on the Lido contracts. When an external party settles a vault's LST liabilities, the on-chain `lstLiabilityPrincipal` value in the `YieldManager` becomes stale and still shows a non-zero liability even though it has been repaid. Calling `unpauseStaking` then incorrectly reverts with `UnpauseStakingForbiddenWithCurrentLSTLiability`.

**Impact:**
When external actors repay LST liabilities, `YieldManager::unpauseStaking` becomes permanently DoSed until a sync is triggered by another code path. This prevents the protocol from resuming staking operations even after all liabilities have been settled externally.

**Recommended Mitigation:**
Call `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` within `YieldManager::unpauseStaking` before reading `$$.lstLiabilityPrincipal` to ensure the value is up-to-date.

---

**[中文版本]**

**描述：**
`YieldManager::unpauseStaking` 检查 `$$.lstLiabilityPrincipal > 0` 并在存在 LST 负债时回滚。然而与代码库中其他地方在使用前通过 `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` 同步 `$$.lstLiabilityPrincipal` 的做法不同，`unpauseStaking` 直接读取该值而不先同步。外部方可以直接在 Lido 合约上偿还 LST 负债。当外部方偿还金库的 LST 负债后，`YieldManager` 中的链上 `lstLiabilityPrincipal` 值变得过时，仍显示非零负债，导致 `unpauseStaking` 错误地以 `UnpauseStakingForbiddenWithCurrentLSTLiability` 回滚。

**影響：**
当外部行为人偿还 LST 负债后，`YieldManager::unpauseStaking` 将持续 DoS，直到其他代码路径触发同步为止，导致协议即使在所有负债都已外部清偿后也无法恢复质押操作。

**修復建議：**
在 `YieldManager::unpauseStaking` 中，读取 `$$.lstLiabilityPrincipal` 之前调用 `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` 以确保值是最新的。

---

## 14. report(...) may be vulnerable to DoS

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
In the `starknet_vault_kit`, the `report` function is used to advance the cycle and handle the redemption queue. The function includes a check that if `prev_aum` equals zero, then `new_aum` cannot be non-zero (it would be an invalid state). However, the `aum_provider` computes AUM by fetching the underlying token balances of the `vault_allocator`. In a newly created vault, a malicious actor can transfer any amount of underlying tokens directly to the `vault_allocator` before the first `report` call is made. This causes the computed `new_aum` to be non-zero during the first `report` execution, triggering the `invalid_new_aum` error and preventing `report` from ever executing.

**Impact:**
In newly created vaults, a malicious actor can permanently block the first `report` call by transferring tokens to the `vault_allocator`. This causes the vault's profit-and-loss reporting and the redemption queue to be permanently stuck, locking any deposited funds.

**Recommended Mitigation:**
Add logic to handle the edge case where `prev_aum` is zero and tokens have been sent to the `vault_allocator`, for example by treating the first report as a special case that initializes the AUM without the non-zero check.

---

**[中文版本]**

**描述：**
在 `starknet_vault_kit` 中，`report` 函数用于推进周期并处理赎回队列。该函数包含一项检查：若 `prev_aum` 为零，则 `new_aum` 不能为非零（否则视为无效状态）。然而 `aum_provider` 通过获取 `vault_allocator` 的底层代币余额来计算 AUM。在新创建的金库中，恶意行为人可以在第一次 `report` 调用执行前直接向 `vault_allocator` 转入任意数量的底层代币，导致 `new_aum` 在首次 `report` 执行时为非零，触发 `invalid_new_aum` 错误，使 `report` 永远无法执行。

**影響：**
在新创建的金库中，恶意行为人可通过向 `vault_allocator` 转入代币来永久阻断首次 `report` 调用，导致金库的盈亏报告和赎回队列永久卡死，锁定所有已存入资金。

**修復建議：**
添加逻辑以处理 `prev_aum` 为零但代币已被发送至 `vault_allocator` 的边界情况，例如将首次报告作为特殊情况处理，直接初始化 AUM 而不进行非零检查。
