# logic-reward (11)

> Issues in reward claim logic, epoch boundaries, and distribution calculations causing incorrect or inaccessible rewards.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. `DepositManager::getRewards` always includes `REFERRER_FEE` resulting in 2 percent of every games' rewards not being distributed to winners when there were no referrers

**Severity:** 🟠 High
**Source:** `cyfrin/protocol.md`

**Description:**
`DepositManager::getRewards` computes the distributable reward pool by deducting `creatorFee + protocolFee + REFERRER_FEE` from `totalCollectedAmount` in every case, regardless of whether any referral rewards were actually accrued for the game. When a game has no referrers, the `REFERRER_FEE` allocation (2%) is still deducted from the winner pool but is never claimed, leaving those tokens permanently stranded in the contract.

**Impact:**
For every game with no active referrers, exactly 2% of the collected prize pool is permanently locked in the contract and can never be paid to winners, retrieved by the creator, or otherwise recovered.

**Recommended Mitigation:**
Replace the use of the constant `REFERRER_FEE` in `getRewards` with a per-game storage variable that tracks the total referral rewards actually accrued for that game. Increment and decrement this variable in `_payEntryFee` and `_refundEntryFee` respectively, and deduct only the actual accrued referral amount in `getRewards`.

---

**[中文版本]**

**描述：**
`DepositManager::getRewards` 在任何情況下均從 `totalCollectedAmount` 中扣除 `creatorFee + protocolFee + REFERRER_FEE` 來計算可分配獎勵池，無論該遊戲是否實際產生了推薦獎勵。當遊戲沒有推薦人時，`REFERRER_FEE`（2%）的分配仍從獎勵池中扣除，但永遠不會被認領，導致這些代幣永久滯留在合約中。

**影響：**
對於每個沒有活躍推薦人的遊戲，恰好 2% 的獎池永久鎖定在合約中，無法支付給獲勝者、被創建者取回或以任何方式回收。

**修復建議：**
在 `getRewards` 中用每個遊戲的存儲變量替換常量 `REFERRER_FEE`，該變量追踪該遊戲實際產生的推薦獎勵總額。在 `_payEntryFee` 中遞增、在 `_refundEntryFee` 中遞減，並在 `getRewards` 中僅扣除實際產生的推薦金額。

---

## 2. Incorrect reward claim logic causes loss of access to intermediate epoch rewards

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
In `Rewards::distributeRewards`, all shares are calculated for participants after a 3-epoch delay. When an operator claims rewards, `lastEpochClaimedOperator[msg.sender]` is unconditionally updated to `currentEpoch - 1`, regardless of which epoch was actually claimed. If rewards for an intermediate epoch (e.g. epoch 2) are distributed after the operator has already claimed for a later epoch (advancing the pointer to `currentEpoch - 1`), the operator can no longer claim for that intermediate epoch because `lastEpochClaimedOperator > 2`.

**Impact:**
Operators permanently lose access to claimable rewards from intermediate epochs that were distributed out of order relative to their claim history. This constitutes a direct loss of funds.

**Recommended Mitigation:**
Update `lastEpochClaimedOperator` to the epoch that was actually just claimed rather than unconditionally setting it to `currentEpoch - 1`, ensuring that future claims for lower-numbered epochs remain possible.

---

**[中文版本]**

**描述：**
在 `Rewards::distributeRewards` 中，所有份額均在 3 個 epoch 延遲後計算。當 operator 領取獎勵時，`lastEpochClaimedOperator[msg.sender]` 無條件更新為 `currentEpoch - 1`，無論實際領取了哪個 epoch。若中間某個 epoch（如 epoch 2）的獎勵在 operator 已為較後 epoch 領取後才被分配（指針已推進至 `currentEpoch - 1`），operator 將因 `lastEpochClaimedOperator > 2` 而無法再領取該中間 epoch 的獎勵。

**影響：**
Operator 永久失去對亂序分配的中間 epoch 可領取獎勵的訪問權限，構成直接資金損失。

**修復建議：**
將 `lastEpochClaimedOperator` 更新為實際剛剛領取的 epoch，而非無條件設置為 `currentEpoch - 1`，確保未來仍可領取編號較小的 epoch 的獎勵。

---

## 3. Vault rewards incorrectly scaled by cross-asset-class operator totals instead of asset class specific shares causing rewards leakage

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
`Rewards::_calculateAndStoreVaultShares` uses `operatorBeneficiariesShares[epoch][operator]`, which represents the operator's total reward share across all asset classes, to scale per-vault rewards. Individual vaults belong to specific asset classes, and their rewards should be scaled only by the operator's participation in that asset class. Using the cross-asset total creates an inappropriate dilution effect where vault rewards are reduced by the operator's involvement in other unrelated asset classes.

**Impact:**
Systematic under-distribution of rewards to vault stakers in every epoch. The excess reward that should reach vault stakers is instead reclaimed as undistributed rewards, meaning the actual distribution does not match the intended asset class allocations.

**Recommended Mitigation:**
Store per-asset-class operator shares separately and use the asset-class-specific operator share (not the cross-asset total) when computing vault reward allocations in `_calculateAndStoreVaultShares`.

---

**[中文版本]**

**描述：**
`Rewards::_calculateAndStoreVaultShares` 使用 `operatorBeneficiariesShares[epoch][operator]`（代表 operator 跨所有資產類別的總獎勵份額）來縮放每個金庫的獎勵。各個金庫屬於特定資產類別，其獎勵應僅根據 operator 在該資產類別中的參與度進行縮放。使用跨資產總量創造了不恰當的稀釋效應，使金庫獎勵因 operator 在其他無關資產類別中的參與而被降低。

**影響：**
每個 epoch 中金庫質押者的獎勵系統性地低於應有水平。應流向金庫質押者的超額獎勵被作為未分配獎勵回收，導致實際分配與預期的資產類別分配不符。

**修復建議：**
單獨存儲每個資產類別的 operator 份額，在 `_calculateAndStoreVaultShares` 中計算金庫獎勵分配時使用特定資產類別的 operator 份額（而非跨資產總量）。

---

## 4. Winner-Selection Logic Flaw Allows The Group Creator To Capture All Contributed Funds

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
In `Komiti::distributeFunds()`, members are iterated from index 0. The ADMIN/ORGANIZER is always inserted first into the `members` array. The winner selection logic favors the first member whose `s_hasReceivedPayout` is false and whose `s_payoutPositions` matches `currentPayoutIndex`. Because the default/unset payout position value is 0, which equals the initial `currentPayoutIndex`, the ADMIN/ORGANIZER always satisfies the condition and is selected as winner during the first distribution cycle — even if they have no legitimate assigned payout position.

**Impact:**
The group creator can illegitimately receive all pooled funds during the first payout distribution, depriving all other contributors of their rightful payouts.

**Recommended Mitigation:**
Require payout positions to be explicitly set before distribution can proceed, and distinguish between an unset position (e.g. using a sentinel value) and a legitimate position of 0. Validate that the selected winner holds an explicitly assigned position matching `currentPayoutIndex`.

---

**[中文版本]**

**描述：**
在 `Komiti::distributeFunds()` 中，成員從索引 0 開始迭代。ADMIN/ORGANIZER 始終是第一個插入 `members` 數組的。獲勝者選擇邏輯偏向第一個 `s_hasReceivedPayout` 為 false 且 `s_payoutPositions` 與 `currentPayoutIndex` 匹配的成員。由於默認/未設置的支付位置值為 0，等於初始 `currentPayoutIndex`，ADMIN/ORGANIZER 始終滿足條件並在第一個分配週期被選為獲勝者——即使他們沒有合法的分配支付位置。

**影響：**
小組創建者可在第一次支付分配時非法獲得所有資金池資金，剝奪所有其他貢獻者的合法支付權利。

**修復建議：**
在分配開始前要求明確設置支付位置，並區分未設置位置（使用哨兵值）和合法的位置 0。驗證選定的獲勝者持有與 `currentPayoutIndex` 匹配的明確分配位置。

---

## 5. Access to `LockBox::unlock` doesn't follow principle of least privilege

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`LockBox::unlock` is guarded by the `onlyBridgeOrLockBox` modifier which grants access to addresses holding either `BRIDGE_ROLE` or `LOCKBOX_ROLE`. However, in practice this function is only ever called from bridge contracts. Granting `LOCKBOX_ROLE` access to `unlock` grants more privilege than is necessary for the intended callers.

**Impact:**
Any address granted `LOCKBOX_ROLE` — even for other purposes — gains the ability to unlock assets, expanding the attack surface unnecessarily.

**Recommended Mitigation:**
Remove `LOCKBOX_ROLE` from the access modifier on `unlock` and restrict it to `BRIDGE_ROLE` only, applying the principle of least privilege.

---

**[中文版本]**

**描述：**
`LockBox::unlock` 受 `onlyBridgeOrLockBox` 修飾符保護，允許持有 `BRIDGE_ROLE` 或 `LOCKBOX_ROLE` 的地址訪問。但實際上此函數僅從橋接合約調用，授予 `LOCKBOX_ROLE` 訪問 `unlock` 超出了預期調用者所需的權限。

**影響：**
任何被授予 `LOCKBOX_ROLE` 的地址——即使是出於其他目的——也獲得了解鎖資產的能力，不必要地擴大了攻擊面。

**修復建議：**
從 `unlock` 的訪問修飾符中移除 `LOCKBOX_ROLE`，僅限制為 `BRIDGE_ROLE`，遵循最小權限原則。

---

## 6. `AngstromL2::_oneForZeroCreditRewards` should skip execution of range reward logic if there is no liquidity

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2::_zeroForOneCreditRewards` correctly uses `if (tickNext >= lastTick && liquidity != 0)` to skip range reward calculation when there is no liquidity. The symmetric function `_oneForZeroCreditRewards` uses the inverted condition `if (tickNext <= lastTick || liquidity == 0)`, which incorrectly enters the reward calculation block even when `liquidity == 0`. The net effect is a no-op since all calculated values resolve to zero, but the code path is still executed unnecessarily.

**Impact:**
Unnecessary computation per tick iteration when liquidity is zero. While it does not produce incorrect state due to `PoolRewardsLib::getGrowthDelta` returning zero for zero liquidity, it diverges from the intended logic of `_zeroForOneCreditRewards` and is fragile.

**Recommended Mitigation:**
Change the condition in `_oneForZeroCreditRewards` from `if (tickNext <= lastTick || liquidity == 0)` to `if (tickNext <= lastTick && liquidity != 0)` to align with the logic in `_zeroForOneCreditRewards`.

---

**[中文版本]**

**描述：**
`AngstromL2::_zeroForOneCreditRewards` 正確使用 `if (tickNext >= lastTick && liquidity != 0)` 在無流動性時跳過範圍獎勵計算。對稱函數 `_oneForZeroCreditRewards` 使用了反轉條件 `if (tickNext <= lastTick || liquidity == 0)`，在 `liquidity == 0` 時仍會錯誤地進入獎勵計算塊。由於所有計算值解析為零，淨效果為空操作，但代碼路徑仍被不必要地執行。

**影響：**
流動性為零時每個 tick 迭代存在不必要的計算。雖然由於 `PoolRewardsLib::getGrowthDelta` 對零流動性返回零而不會產生錯誤狀態，但與 `_zeroForOneCreditRewards` 的預期邏輯不一致且脆弱。

**修復建議：**
將 `_oneForZeroCreditRewards` 中的條件從 `if (tickNext <= lastTick || liquidity == 0)` 改為 `if (tickNext <= lastTick && liquidity != 0)`，使其與 `_zeroForOneCreditRewards` 中的邏輯保持一致。

---

## 7. Consider burning `ERC-6909` claim tokens within `AngstromL2::withdrawProtocolRevenue` and transferring the underlying asset instead

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2::withdrawProtocolRevenue` currently transfers ERC-6909 claim token balance to the recipient via `UNI_V4.transfer(to, assetId, amount)`. The recipient may not have the infrastructure to burn the claim token and redeem the underlying asset from the Uniswap V4 `PoolManager`. Performing the burn-and-transfer within the `withdrawProtocolRevenue` call itself, via a `PoolManager` callback, would deliver the underlying asset directly and simplify the recipient's experience.

**Impact:**
Revenue recipients who lack experience with ERC-6909 claim token mechanics may be unable to easily access the underlying asset, reducing the practical usability of the protocol fee withdrawal.

**Recommended Mitigation:**
Implement the ERC-6909 burn and underlying asset transfer inside a `PoolManager` callback within `withdrawProtocolRevenue`, delivering the underlying currency directly to the recipient instead of the claim token.

---

**[中文版本]**

**描述：**
`AngstromL2::withdrawProtocolRevenue` 目前通過 `UNI_V4.transfer(to, assetId, amount)` 將 ERC-6909 索取代幣餘額轉移給接收方。接收方可能沒有能力燃燒索取代幣並從 Uniswap V4 `PoolManager` 兌換底層資產。通過 `PoolManager` 回調在 `withdrawProtocolRevenue` 調用本身內執行燃燒和轉移，可直接交付底層資產並簡化接收方的操作體驗。

**影響：**
不熟悉 ERC-6909 索取代幣機制的收益接收方可能無法輕鬆訪問底層資產，降低了協議費用提款的實際可用性。

**修復建議：**
在 `withdrawProtocolRevenue` 的 `PoolManager` 回調中實現 ERC-6909 燃燒和底層資產轉移，直接將底層貨幣交付給接收方，而非索取代幣。

---

## 8. Historical reward loss due to `NodeId` reuse in `AvalancheL1Middleware`

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
If Operator B registers a node using the same `bytes32 nodeId` that Operator A previously used (after Operator A's node was decommissioned), `getActiveNodesForEpoch` for Operator A will locate the historical `nodeId` in `operatorNodes[A]`, convert it to P-Chain NodeID `P_X`, and call `balancerValidatorManager.registeredValidators(P_X)` — which now returns Operator B's new `validationID`. The function then reads `nodeStakeCache` for Operator B's validation ID and incorrectly counts Operator B's stake as part of Operator A's used stake.

**Impact:**
Operator A's used stake is artificially inflated by Operator B's stake, causing Operator A to receive rewards disproportionate to their actual contribution. Operator B's legitimate rewards may also be misattributed.

**Recommended Mitigation:**
Record the specific `validationID` alongside each node entry when `addNode` is called, so that historical lookups use the original `validationID` rather than re-querying `registeredValidators` which can return a different operator's ID after reuse.

---

**[中文版本]**

**描述：**
如果 Operator B 使用與 Operator A 之前相同的 `bytes32 nodeId` 註冊節點（在 Operator A 的節點被停用後），`getActiveNodesForEpoch` 對 Operator A 的查詢將在 `operatorNodes[A]` 中找到歷史 `nodeId`，將其轉換為 P-Chain NodeID `P_X`，並調用 `balancerValidatorManager.registeredValidators(P_X)`——此時返回的是 Operator B 的新 `validationID`。函數隨後讀取 Operator B 驗證 ID 的 `nodeStakeCache`，錯誤地將 Operator B 的質押計入 Operator A 的已用質押。

**影響：**
Operator A 的已用質押被 Operator B 的質押人為抬高，導致 Operator A 獲得與其實際貢獻不相稱的獎勵。Operator B 的合法獎勵也可能被錯誤歸因。

**修復建議：**
在調用 `addNode` 時將特定 `validationID` 與每個節點條目一併記錄，使歷史查找使用原始 `validationID`，而不是重新查詢可能在重用後返回不同 operator ID 的 `registeredValidators`。

---

## 9. L2 Sequencer Status Check Logic Inversion Leading to Denial of Service

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/YieldFi.txt`

**Description:**
In `ChainlinkOracleAdapter::_checkSequencerUptime`, the contract checks L2 sequencer health using the Chainlink Sequencer Uptime Feed. Per Chainlink documentation, `answer == 0` means the sequencer is active (up) and `answer == 1` means it is down. The contract however reverts when `answer == 0`, treating a healthy sequencer as a failure condition. This inverts the intended logic entirely.

**Impact:**
All price-dependent protocol operations — including deposits, redemptions, and lending LTV checks — are unusable on L2 chains whenever the sequencer is in a normal healthy state, which is the vast majority of the time.

**Recommended Mitigation:**
Correct the check to revert when `answer == 1` (sequencer is down) rather than when `answer == 0`.

---

**[中文版本]**

**描述：**
在 `ChainlinkOracleAdapter::_checkSequencerUptime` 中，合約使用 Chainlink 序列器正常運行時間 Feed 檢查 L2 序列器健康狀態。根據 Chainlink 文檔，`answer == 0` 表示序列器活躍（正常），`answer == 1` 表示序列器宕機。然而合約在 `answer == 0` 時回滾，將健康的序列器視為故障條件，完全顛倒了預期邏輯。

**影響：**
所有依賴價格的協議操作——包括存款、贖回和借貸 LTV 檢查——在 L2 鏈上序列器處於正常健康狀態（即絕大多數時間）時均無法使用。

**修復建議：**
將檢查修正為在 `answer == 1`（序列器宕機）時回滾，而非在 `answer == 0` 時回滾。

---

## 10. Operator can over allocate the same stake to unlimited nodes within one epoch causing weight inflation and reward theft

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::addNode` checks available stake via `_getOperatorAvailableStake`, which subtracts only `operatorLockedStake[operator]` from total stake. Within the same epoch, an operator can call `addNode` multiple times before the locked stake accounting is updated, allocating the same collateral to multiple validator nodes. This allows an operator to register far more stake-backed nodes than they have actual collateral for.

**Impact:**
Operators can artificially inflate their active weight across multiple nodes, causing them to receive disproportionately large reward allocations at the expense of other operators whose stake calculations are correctly constrained.

**Recommended Mitigation:**
Update `operatorLockedStake` immediately when `addNode` is called, before the available stake check, to prevent the same collateral from being counted multiple times within an epoch.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware::addNode` 通過 `_getOperatorAvailableStake` 檢查可用質押，該函數僅從總質押中扣除 `operatorLockedStake[operator]`。在同一個 epoch 內，operator 可以在鎖定質押賬目更新前多次調用 `addNode`，將同一抵押品分配給多個驗證器節點，從而使 operator 能夠以少於實際抵押品的質押量註冊更多節點。

**影響：**
Operator 可人為抬高跨多個節點的活躍權重，獲得不成比例的大量獎勵分配，損害其他質押計算正確受限的 operator 的利益。

**修復建議：**
在 `addNode` 調用時，在可用質押檢查之前立即更新 `operatorLockedStake`，防止同一抵押品在一個 epoch 內被多次計算。

---

## 11. Optimisation of elapsed epoch calculation

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
In `UptimeTracker::computeValidatorUptime`, the elapsed epoch count is computed by first retrieving both epoch indices and their corresponding start timestamps, then dividing the elapsed time by `epochDuration`. Since the epoch indices `lastUptimeEpoch` and `currentEpoch` are already known, the number of elapsed epochs can be calculated directly as `currentEpoch - lastUptimeEpoch`, avoiding the unnecessary calls to `getEpochStartTs`.

**Impact:**
Redundant external calls to `getEpochStartTs` add unnecessary gas overhead to every uptime computation.

**Recommended Mitigation:**
Replace the timestamp-based elapsed epoch calculation with direct subtraction of epoch indices: `uint256 elapsedEpochs = currentEpoch - lastUptimeEpoch;`, eliminating the redundant `getEpochStartTs` calls.

---

**[中文版本]**

**描述：**
在 `UptimeTracker::computeValidatorUptime` 中，經過的 epoch 數量通過先獲取兩個 epoch 索引及其對應的起始時間戳，再除以 `epochDuration` 來計算。由於 epoch 索引 `lastUptimeEpoch` 和 `currentEpoch` 已知，可直接通過 `currentEpoch - lastUptimeEpoch` 計算經過的 epoch 數量，無需調用 `getEpochStartTs`。

**影響：**
對 `getEpochStartTs` 的冗余外部調用為每次正常運行時間計算增加了不必要的 Gas 開銷。

**修復建議：**
用 epoch 索引的直接相減替換基於時間戳的 epoch 計算：`uint256 elapsedEpochs = currentEpoch - lastUptimeEpoch;`，消除冗余的 `getEpochStartTs` 調用。
