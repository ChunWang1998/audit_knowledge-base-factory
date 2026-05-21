# revert-rewards (2)

> Issues where reward distribution or claim functions can permanently revert, blocking all future payouts.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Division by Zero in Rewards Distribution Can Cause Permanent Lock of Epoch Rewards

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
In `Rewards::_calculateOperatorShare`, the function fetches the current list of asset class IDs but attempts to calculate rewards for a historical epoch. This creates a mismatch: newly added asset classes are included in the current list but have no historical stake data, while deactivated asset classes may remain but have zero total stake. The calculation `Math.mulDiv(operatorStake, BASIS_POINTS_DENOMINATOR, totalStake)` performs a division where `totalStake` can be zero — for any asset class added after the target epoch, `totalStakeCache[epoch][newAssetClass]` is 0. Division by zero causes the entire reward distribution transaction to revert. The same division-by-zero issue exists in `_calculateAndStoreVaultShares` when `operatorActiveStake == 0`.

**Impact:**
Adding a new asset class ID, deactivating or migrating an existing asset class, or simply having zero stake for a given asset class are all scenarios that permanently DOS reward distribution for the affected epoch. Rewards already earned for that epoch become unclaimable and permanently locked.

**Recommended Mitigation:**
Add a zero-check for `totalStake` before the `Math.mulDiv` division and skip (continue) to the next asset class if `totalStake == 0`. Apply the same guard to `operatorActiveStake` in `_calculateAndStoreVaultShares`.

---

**[中文版本]**

**描述：**
`Rewards::_calculateOperatorShare` 獲取當前資產類別列表，但試圖計算歷史 epoch 的獎勵。新增的資產類別包含在當前列表中卻沒有歷史質押數據，已停用的資產類別可能總質押為零。計算 `Math.mulDiv(operatorStake, BASIS_POINTS_DENOMINATOR, totalStake)` 中 `totalStake` 可為零——任何在目標 epoch 之後添加的資產類別的 `totalStakeCache[epoch][newAssetClass]` 都為 0，引發除零錯誤導致整個獎勵分配交易 revert。

**影響：**
添加新資產類別、停用或遷移現有資產類別、或特定資產類別的質押量為零，均會永久阻塞對應 epoch 的獎勵分配，已賺取的獎勵變得不可認領並永久被鎖定。

**修復建議：**
在 `Math.mulDiv` 除法之前添加 `totalStake` 的零值檢查，若為零則跳過（continue）到下一個資產類別；對 `_calculateAndStoreVaultShares` 中的 `operatorActiveStake` 施加同樣的保護。

---

## 2. Impossible to Claim Rewards When `XPTiers` Are Not Set, Resulting in Permanently Locked Tokens Once Game Has Concluded

**Severity:** 🟠 High
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::setXPTiers` only allows XP tiers to be set when the game is in the `Created` state, but `SessionManager::startAndRevealGameQuestion` will start the game even if XP tiers have never been set. The game then progresses through all states to `Concluded`. Prompt strategies (`SPBinaryPrompt`, `TriviaChoicePrompt`) use XP tiers to compute results in `getResult` — when tiers are absent, all XP values are zero. `assertResults` accepts these zero values and `ProportionalToXpReward` distributes rewards proportional to XP, meaning winners with zero XP receive zero rewards. Their token share remains in the contract and cannot be re-triggered.

**Impact:**
When XP tiers are not set before game start, winners receive zero rewards even though the game concludes normally. The reward tokens remain permanently locked in the `DepositManager` contract with no mechanism to redistribute or recover them.

**Recommended Mitigation:**
In `SessionManager::startAndRevealGameQuestion` (or `startGame`), require that XP tiers have been set before allowing the game to start. Alternatively allow XP tiers to be updated at any point before the game reaches the `Ended` state.

---

**[中文版本]**

**描述：**
`DefaultSession::setXPTiers` 只允許在遊戲處於 `Created` 狀態時設置 XP 等級，但 `SessionManager::startAndRevealGameQuestion` 即使從未設置 XP 等級也會啟動遊戲，遊戲隨後正常推進至 `Concluded`。`SPBinaryPrompt`、`TriviaChoicePrompt` 使用 XP 等級計算結果——等級缺失時所有 XP 值為零，`ProportionalToXpReward` 按 XP 比例分配獎勵，零 XP 的獲勝者獲得零獎勵，代幣份額留存合約中無法再次觸發。

**影響：**
遊戲開始前未設置 XP 等級時，獲勝者獲得零獎勵，獎勵代幣被永久鎖定在 `DepositManager` 合約中，無法重新分配或恢復。

**修復建議：**
在 `SessionManager::startAndRevealGameQuestion`（或 `startGame`）中，要求 XP 等級已設置才允許遊戲開始；或允許在遊戲達到 `Ended` 狀態前的任意時點更新 XP 等級。

---