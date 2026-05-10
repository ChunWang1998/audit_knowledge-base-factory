# payouts-holder (14)

> Issues where payout or reward distribution logic can be griefed, manipulated, or incorrectly attributed.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. A single holder can grief the payouts of all holders forwarding their payouts to the same forwarder

**Severity:** 🔴 Critical
**Source:** `cyfrin/pledge.md`

**Description:**
When multiple holders designate the same address as their payout forwarder, a single holder can destroy the accumulated payouts for all of them. The attack works as follows: after the forwarder claims all payouts and zeroes out their PropertyToken balance (losing `isHolder` status), further distributions are credited to the forwarder's `calculatedPayout`. If any holder then removes the forwarder while the forwarder still has no token balance and is a non-holder, the contract deletes the forwarder's entire data record, including the unclaimed `calculatedPayout` that was accumulated on behalf of all forwarding holders.

**Impact:**
All holders who were forwarding payouts to the same forwarder lose their accumulated unclaimed payouts. A single holder who removes the non-holder forwarder inadvertently (or maliciously) triggers the deletion of all other holders' pending payouts credited to that forwarder.

**Recommended Mitigation:**
In the logic that removes or deletes forwarder data, check that `calculatedPayout == 0` before calling `deleteUser()`. Specifically, when evaluating whether to delete the forwarded address upon removal, add the condition `$._holderStatus[forwardedAddress].calculatedPayout == 0` alongside the existing balance and `payoutBalance` checks.

---

**[中文版本]**

**描述：**
当多个持有者将同一地址设为其收益转发地址时，单个持有者就可能摧毁所有持有者的未领取收益。攻击路径：转发人领取所有收益后将 PropertyToken 余额清零（失去 `isHolder` 状态），此后的分发款会累积到转发人的 `calculatedPayout` 中。若任何一个持有者在转发人余额为零且不再是持有者时将其从转发列表移除，合约会删除该转发人的全部数据记录，包括所有转发持有者的未领累计收益。

**影響：**
所有向同一转发人转发收益的持有者都会丢失其累积未领收益。

**修復建議：**
在移除或删除转发人数据的逻辑中，删除用户前检查 `calculatedPayout == 0`，补充条件 `$._holderStatus[forwardedAddress].calculatedPayout == 0`。

---

## 2. All rewards can be stolen due to incorrect active liquidity calculations when the current tick is an exact multiple of the tick spacing at the upper end of a liquidity range

**Severity:** 🟠 High
**Source:** `cyfrin/angstrom.md`

**Description:**
When the current tick `t` is an exact multiple of the tick spacing and sits at the upper boundary of an active liquidity range, `TickIteratorLib::initDown` initialises the iterator with `currentTick - 1` instead of `currentTick`. This causes the boundary tick to be skipped, so the net liquidity delta of crossing that tick is never applied. In certain configurations with overlapping liquidity positions, this results in `_zeroForOneCreditRewards` computing cumulative growth using a smaller-than-correct liquidity value, which amplifies growth per unit of liquidity. An attacker who adds JIT liquidity to the boundary range can exploit this inflated growth to collect the entire pool reward balance at a profit.

**Impact:**
The active liquidity is calculated incorrectly when the current tick is an exact multiple of the tick spacing at the upper end of a liquidity range. In some cases swaps revert due to underflow; in others rewards are distributed incorrectly; in the most severe case an attacker can steal all rewards at a profit.

**Recommended Mitigation:**
Resolve the off-by-one error by seeding the iterator from within `reset()` with `currentTick + 1` so that the boundary tick is included and its net liquidity delta is applied before any further calculations.

---

**[中文版本]**

**描述：**
当当前 tick `t` 恰好是 tick spacing 的整数倍并位于流动性范围的上边界时，`TickIteratorLib::initDown` 用 `currentTick - 1` 初始化迭代器，导致边界 tick 被跳过，其净流动性 delta 未被计入。在存在重叠流动性仓位的情况下，这会导致每单位流动性的累计增长被虚高，攻击者可通过 JIT 流动性利用此漏洞窃取全部奖励。

**影響：**
活跃流动性计算错误，轻则导致 swap 因下溢回滚，重则使攻击者盈利性地窃取全部奖励。

**修復建議：**
在 `reset()` 中以 `currentTick + 1` 初始化迭代器，确保边界 tick 被包含在内。

---

## 3. If multiple users call DefaultSession::assertResults all but the first caller lose their bonds

**Severity:** 🟠 High
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::assertResults` is a permissionless function that accepts a USDC bond (minimum $250) from each caller to assert game results via the UMA optimistic oracle. The function does not prevent multiple callers from submitting assertions for the same `sessionId`. When the first assertion resolves positively and `recordResults` sets `winners[sessionId]`, any subsequent resolved assertion callback for the same `sessionId` causes `recordResults` to revert with `WinnersAlreadyRecorded`. Because the UMA protocol recommends that assertion callbacks never revert, this revert leaves the bond of every non-first caller permanently locked with no recovery path.

**Impact:**
Any user who calls `assertResults` for a `sessionId` that was already asserted by another user loses their USDC bond permanently. In concurrent submission scenarios all but the first caller lose their funds.

**Recommended Mitigation:**
Either prevent multiple in-progress assertions for the same `sessionId` (e.g., track a pending assertion ID per session and revert if one already exists), or handle the `WinnersAlreadyRecorded` case in the callback by returning gracefully instead of reverting.

---

**[中文版本]**

**描述：**
`DefaultSession::assertResults` 是一个无访问控制的函数，调用者须支付至少 $250 的 USDC 保证金。该函数不阻止多个调用者为同一 `sessionId` 提交断言。当第一个断言成功后，后续断言的回调中 `recordResults` 因 `WinnersAlreadyRecorded` 回滚，导致后续调用者保证金永久锁定。

**影響：**
除第一个调用者外，所有为同一 `sessionId` 提交断言的用户将永久丢失 USDC 保证金。

**修復建議：**
跟踪每个 `sessionId` 是否已有进行中的断言并在重复提交时回滚；或在回调中优雅返回而非回滚以处理已记录结果的情况。

---

## 4. Burning ALL PropertyTokens of a frozen holder results in the holder losing the payouts distribution while he was frozen

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
When all PropertyTokens owned by a frozen holder are burned, the holder loses access to all dividend distributions accrued during the freeze period. However, if only some tokens are burned, the holder retains access to those distributions. The discrepancy arises because burning the entire balance causes the holder's data record to be effectively reset, dropping the reference to frozen-period payouts. A user with 1 token who has all tokens burned loses payouts for the frozen period, while a user with 2 tokens who has only 1 burned retains access to all accrued payouts.

**Impact:**
Burning ALL PropertyTokens owned by a frozen holder causes that holder to lose all accrued payouts for the distributions occurring during the freeze period, creating an inconsistent and unfair outcome compared to partial burns.

**Recommended Mitigation:**
Add a check in `burnFrom` that reverts if the account would be left with zero balance while still frozen, or alternatively revert on `burnFrom` whenever the account is frozen, preventing the edge case entirely.

---

**[中文版本]**

**描述：**
当冻结持有者的所有 PropertyToken 被销毁时，持有者会丢失冻结期间产生的所有分红。但如果只销毁部分 token，持有者仍可访问这些分红。这种差异导致了不公平的边界情况。

**影響：**
冻结持有者的全部代币被销毁后，持有者会丢失冻结期间所有分红，与部分销毁的行为不一致。

**修復建議：**
在 `burnFrom` 中增加检查，若账户销毁后余额为零且仍处于冻结状态则回滚；或在账户冻结时禁止任何 `burnFrom` 操作。

---

## 5. Collector can add CreatorStory, corrupting the provenance of an artwork

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
The `IStory` interface mandates that `addCreatorStory` is callable only by the original creator of an artwork. The CryptoArt implementation overrides this with `onlyTokenOwner`, meaning any current owner of the NFT can emit `CreatorStory` events. As NFTs are sold, each successive owner — who is a Collector, not the Creator — can continue appending creator-level provenance entries.

**Impact:**
Collectors can corrupt the provenance of an artwork by emitting `CreatorStory` events as if they were the original Creator. This undermines the integrity of on-chain provenance records, which can affect the artwork's perceived authenticity and value.

**Recommended Mitigation:**
Restrict `addCreatorStory` to the original creator of the artwork. Either record the creator address on-chain at mint time and check it in `addCreatorStory`, or delegate creator authority to the contract owner acting as a proxy for the creator.

---

**[中文版本]**

**描述：**
`IStory` 接口要求 `addCreatorStory` 只能由原创作者调用，但 CryptoArt 实现使用 `onlyTokenOwner`，导致 NFT 的任何当前持有者（收藏者）都能发出 `CreatorStory` 事件。

**影響：**
收藏者可以伪装成创作者发出创作者级别的溯源记录，破坏作品链上溯源的真实性，影响作品认可度和价值。

**修復建議：**
限制 `addCreatorStory` 只能由原创作者地址调用，可在铸造时记录创作者地址并在函数中校验。

---

## 6. Consider limiting max royalty to prevent large amount or all of the sale fee being taken as royalty

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
`updateRoyalties` and `setTokenRoyalty` allow the contract owner to configure royalty rates up to `10_000` basis points (100%). There is no upper-bound guard, meaning the entire sale fee could be consumed as royalty. The runtime administrative function `setTaxConfig` in other parts of the system enforces a 65% cap, but no equivalent protection exists on royalty configuration.

**Impact:**
The contract owner can set royalties to 100%, causing buyers to receive nothing from a sale while the entire proceeds go to the royalty recipient. This is economically harmful to buyers and secondary market participants and inconsistent with marketplace expectations.

**Recommended Mitigation:**
Limit the maximum allowable royalty to a reasonable percentage — for example 1000 basis points (10%) — by adding a `require` check in `updateRoyalties` and `setTokenRoyalty`.

---

**[中文版本]**

**描述：**
`updateRoyalties` 和 `setTokenRoyalty` 允许合约所有者设置版税至 `10_000`（即100%），没有上限保护，合约所有者可将全部交易收入作为版税收取。

**影響：**
合约所有者可将版税设为100%，买家在二级市场交易中将颗粒无收，损害买家利益且与市场预期不符。

**修復建議：**
在 `updateRoyalties` 和 `setTokenRoyalty` 中增加 `require` 限制最大版税，例如不超过 1000 基点（10%）。

---

## 7. Forwarders can lose payouts of the holders forwarding to them

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
A forwarder who first claims all payouts (setting `payoutBalance` to 0), then zeroes out their token balance (losing `isHolder` status), and later receives new forwarded payouts (incrementing `calculatedPayout`) can lose those payouts if they subsequently regain tokens (becoming a holder again on the same `distributionIndex`) and immediately zero out their balance a second time. On the second zeroing, `payoutBalance()` returns 0 because `lastPayoutIndexCalculated == currentPayoutIndex`, so `deleteUser()` is called, deleting all accumulated `calculatedPayout` entries including those belonging to forwarding holders.

**Impact:**
Forwarders can lose the accumulated payouts of the holders who are forwarding to them, resulting in those payouts being permanently destroyed.

**Recommended Mitigation:**
In `_updateHolders()`, check that `holderStatus.calculatedPayout == 0` before calling `deleteUser()`. If it is non-zero, do not delete the user's data even if their balance and `payoutBalance` are both zero.

---

**[中文版本]**

**描述：**
转发人在特定操作序列下（领取收益→清零余额→重获代币→再次清零余额）会触发 `deleteUser()`，删除包括转发持有者累计收益在内的所有数据，导致这些收益永久丢失。

**影響：**
转发人的操作可能导致向其转发收益的持有者丢失全部未领收益。

**修復建議：**
在 `_updateHolders()` 中，调用 `deleteUser()` 前检查 `holderStatus.calculatedPayout == 0`，非零时不删除用户数据。

---

## 8. Forwarders who aren't also holders are unable to claim forwarded payouts

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DividendManager::payoutBalance` returns 0 early whenever `!rHolderStatus.isHolder` is true. A forwarder who receives forwarded payouts from another holder but does not hold any PropertyTokens themselves is not a holder, so `payoutBalance` always returns 0 for them, making their accumulated forwarded payouts uncollectable.

**Impact:**
Forwarders who do not themselves hold PropertyTokens are permanently unable to claim payouts that have been forwarded to them, effectively locking those funds.

**Recommended Mitigation:**
Remove the `(!rHolderStatus.isHolder)` guard from `DividendManager::payoutBalance` so that non-holder forwarders can still have their accumulated `calculatedPayout` balance returned and claimed.

---

**[中文版本]**

**描述：**
`DividendManager::payoutBalance` 在 `!rHolderStatus.isHolder` 为真时提前返回0。不持有 PropertyToken 的转发人不属于持有者，因此其收益余额始终返回0，无法领取。

**影響：**
不持有代币的转发人无法领取已转发给他们的收益，资金永久锁定。

**修復建議：**
从 `DividendManager::payoutBalance` 中移除 `(!rHolderStatus.isHolder)` 检查，使非持有人转发人也能查询和领取收益。

---

## 9. NegRisk market creator is set to adapter address instead of the initiator

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`PredictionMarketV3ManagerCLOB::createNegRiskMarket` is restricted to the registered `NegRiskAdapter`. When the adapter calls the manager in a loop to create neg-risk markets, `market.creator` is set to `msg.sender`, which is the adapter contract address. The actual initiator — the admin who called `NegRiskAdapter::createEvent` — is never recorded. All neg-risk markets therefore have an incorrect `creator` field pointing to the adapter contract.

**Impact:**
Any protocol logic, UI, or analytics that relies on `market.creator` to identify the human or admin who created a neg-risk market will receive incorrect data. This could affect permissions, royalties, display, or off-chain integrations.

**Recommended Mitigation:**
Pass the actual initiator address into `createNegRiskMarket` as a parameter and use it to set `market.creator`. Also consider including the creator in the `MarketCreated` event.

---

**[中文版本]**

**描述：**
`createNegRiskMarket` 将 `market.creator` 设为 `msg.sender`，而此时的调用者是适配器合约而非真正的发起人。所有 neg-risk 市场的 `creator` 字段均错误地指向适配器合约地址。

**影響：**
依赖 `market.creator` 字段的逻辑、界面或分析工具将获得错误数据，可能影响权限、显示或链下集成。

**修復建議：**
将真实发起人地址作为参数传入 `createNegRiskMarket` 并用于设置 `market.creator`。

---

## 10. Operators can lose their reward share

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`Rewards::distributeRewards` distributes rewards for epochs at least two epochs old, but fetches the current operator list via `l1Middleware.getAllOperators()` rather than the historical operator set at the target epoch. If an operator was active during the target epoch but has since been disabled and removed — which can happen when `SLASHING_WINDOW < 2 * epochDuration` — they are excluded from the current list and receive no rewards for the epoch they legitimately participated in.

**Impact:**
Operators active during a given epoch lose their rewards if they are removed before distribution occurs. This creates an unfair loss and allows anyone with authority to remove operators (including the contract owner) to manipulate reward distribution, intentionally or otherwise.

**Recommended Mitigation:**
When distributing rewards for a past epoch, query the operator set as it existed at that epoch rather than the current set. Additionally, ensure that `SLASHING_WINDOW >= 2 * epochDuration` so operators cannot be removed before their rewards are distributed.

---

**[中文版本]**

**描述：**
`Rewards::distributeRewards` 在分发历史轮次奖励时使用当前运营商列表，若运营商在目标轮次后被移除（可能因 `SLASHING_WINDOW < 2 * epochDuration`），则其奖励会被跳过，永久丢失。

**影響：**
活跃于某一轮次的运营商若在奖励分发前被移除，将丢失应得奖励；合约所有者可借此操纵奖励分配。

**修復建議：**
在分发历史轮次奖励时查询该轮次的历史运营商集合；同时确保 `SLASHING_WINDOW >= 2 * epochDuration`。

---

## 11. PaymentSettler::claimAllPayouts doesn't validate input tokens addresses are legitimate contracts before calling adminClaimPayout on them

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`PaymentSettler::initiateBurning` and `distributePayment` both verify that input token addresses are active via `if (!tokenData[token].active) revert InvalidTokenAddress()`. However, `PaymentSettler::claimAllPayouts` iterates over a caller-supplied `tokens` array and calls `IRemoraToken(tokens[i]).adminClaimPayout(...)` on each address without performing any such validation. An attacker can supply a custom contract that implements the `adminClaimPayout` interface but contains arbitrary code.

**Impact:**
Execution flow is transferred to an attacker-controlled contract, enabling potential reentrancy, state corruption, or other arbitrary on-chain behaviour within the same call context.

**Recommended Mitigation:**
Verify that each address in the input `tokens` array is an active, whitelisted `RemoraToken` contract (e.g., by checking `tokenData[token].active`) before calling any function on it.

---

**[中文版本]**

**描述：**
`claimAllPayouts` 遍历调用者提供的 `tokens` 数组并调用 `adminClaimPayout`，但未检查这些地址是否为合法的活跃代币合约，攻击者可提供含有任意逻辑的自定义合约。

**影響：**
执行流被转移至攻击者控制的合约，可能导致重入、状态破坏或其他恶意链上操作。

**修復建議：**
在对每个 token 地址调用函数前，检查 `tokenData[token].active` 确认其为合法的活跃代币合约。

---

## 12. Same user can join the same game multiple times increasing their chance of winning by preventing other players from participating

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::joinGame` does not track whether a given address has already joined a game. A user can call `joinGame` repeatedly while the game is in the `Created` state, incrementing `numContestants` each time and effectively filling up the available slots. This works even when `verificationRequired` is enabled, because the same whitelisted address can occupy multiple contestant slots.

**Impact:**
A malicious or opportunistic user can monopolise all or most of the available player slots in a game, preventing legitimate participants from joining and dramatically increasing their own probability of winning.

**Recommended Mitigation:**
In `SessionManager::joinGame`, revert if `contestants[_gameId][msg.sender] == true`. Consider wrapping this into a dedicated `onlyNotJoinedGame` modifier.

---

**[中文版本]**

**描述：**
`SessionManager::joinGame` 不检查用户是否已加入游戏，同一地址可反复调用占据多个参赛名额，即使启用了 `verificationRequired` 白名单也无法防止。

**影響：**
恶意用户可垄断全部或大部分参赛名额，阻止其他玩家加入，大幅提高自己的获胜概率。

**修復建議：**
在 `joinGame` 中，若 `contestants[_gameId][msg.sender] == true` 则回滚，可封装为 `onlyNotJoinedGame` 修饰器。

---

## 13. Seizing payouts for frozen users can lead to double spending if the holder is unfrozen in subsequent distributions

**Severity:** 🟡 Medium
**Source:** `cyfrin/final.md`

**Description:**
`ChildToken::seizeFrozenFunds` correctly sends frozen-period payouts to a custodian. However, if `DividendManager::payoutBalance` is called while the holder is still frozen after a seizure, it forcibly resets `lastPayoutIndexCalculated` to `frozenIndex`. When the holder is subsequently unfrozen, their `lastPayoutIndexCalculated` is at `frozenIndex`, so the payout routine re-credits all distributions from `frozenIndex` to the current index — the same payouts that were already seized and sent to the custodian.

**Impact:**
A frozen user can re-claim payouts that were already seized and forwarded to the custodian, effectively double-spending funds that belong to other protocol participants.

**Recommended Mitigation:**
When unfreezing a holder after seizure, update `holderStatus.frozenIndex` to `$._currentPayoutIndex` to prevent the restarting of payout credit from the old frozen index.

---

**[中文版本]**

**描述：**
`seizeFrozenFunds` 将冻结期收益转给保管人后，若在用户仍处于冻结状态时调用 `payoutBalance`，会将 `lastPayoutIndexCalculated` 重置为 `frozenIndex`。解冻后，用户可从 `frozenIndex` 重新领取已被没收的收益，造成双重支出。

**影響：**
被冻结用户可重新领取已转给保管人的收益，从协议其他参与者处双重支出资金。

**修復建議：**
解冻后将 `holderStatus.frozenIndex` 更新为 `$._currentPayoutIndex`，防止从旧冻结索引重新计算收益。

---

## 14. Withdrawals can effectively only happen on the primary chain after any yield has accrued

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
In the SherpaVault multi-chain system, yield is only realised on the primary chain via `SherpaVault::_adjustBalanceAndEmit`. When a user withdraws from a secondary chain after yield has accrued, the protocol must rebalance assets from the primary to the secondary chain by calling `SherpaUSD::ownerBurn` on the primary and `ownerMint` on the secondary. This write sets `approvedAccountingAdjustment` on both chains. However, there is no mechanism to clear `approvedAccountingAdjustment` from the secondary chain without also calling `SherpaVault::adjustAccountingSupply`, which incorrectly decrements `accountingSupply` (since no shares were actually moved), permanently corrupting vault state and potentially causing underflow reverts on the primary chain.

**Impact:**
Withdrawals from secondary chains after any yield accrual will either leave `approvedAccountingAdjustment` permanently corrupted or corrupt `accountingSupply`, potentially bricking funds on the primary chain.

**Recommended Mitigation:**
Split rebalancing into two distinct approval modes: an asset-only rebalance (sets `approvedTotalStakedAdjustment` only) and a share-sync rebalance (sets both `approvedTotalStakedAdjustment` and `approvedAccountingAdjustment`), so that asset transfers across chains are not conflated with share accounting changes.

---

**[中文版本]**

**描述：**
SherpaVault 多链架构中，收益仅在主链实现。用户在收益累积后从辅链提款时，协议需通过资产再平衡（主链 burn + 辅链 mint）来完成，但此操作同时设置了 `approvedAccountingAdjustment`，且无机制清除辅链上的此状态（调用 `adjustAccountingSupply` 会因未发生份额变动而错误递减 `accountingSupply`），导致链上状态永久损坏。

**影響：**
任何收益产生后从辅链提款都会导致 `approvedAccountingAdjustment` 永久损坏或 `accountingSupply` 被错误递减，可能使主链资金被锁定。

**修復建議：**
将资产再平衡拆分为两种模式：仅资产转移模式（只设置 `approvedTotalStakedAdjustment`）和份额同步模式（同时设置两者），避免资产转移与份额会计混用。
