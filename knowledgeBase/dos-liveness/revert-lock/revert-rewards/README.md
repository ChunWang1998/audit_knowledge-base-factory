# revert-rewards (14)

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

## 3. `DefaultSession::assertResults` Should Revert if `proposedWinners`, `totalXPs` and `totalTimes` Array Lengths Don't Match

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::assertResults` accepts three parallel arrays — `proposedWinners`, `totalXPs`, and `totalTimes` — but does not validate that they have the same length. If an asserter accidentally submits arrays of different lengths, the assertion is accepted without error and proceeds to the UMA oracle. Since the asserter posts a bond, an incorrect assertion will cause them to lose their bond when the oracle resolves the dispute.

**Impact:**
If an asserter makes a mistake by providing arrays of different lengths, they will lose their bond. The mismatched assertion may also corrupt downstream reward processing for the game.

**Recommended Mitigation:**
Add an explicit length equality check at the start of `assertResults` that reverts if `proposedWinners.length != totalXPs.length || proposedWinners.length != totalTimes.length`.

---

**[中文版本]**

**描述：**
`DefaultSession::assertResults` 接受三個並行數組 `proposedWinners`、`totalXPs`、`totalTimes`，但未驗證它們的長度是否相等。若斷言者意外提交長度不一致的數組，斷言會被無錯誤地接受並提交至 UMA 預言機，導致斷言者的保證金在預言機解決爭議時被沒收。

**影響：**
斷言者因數組長度不匹配而損失保證金；不匹配的斷言還可能破壞遊戲的後續獎勵處理。

**修復建議：**
在 `assertResults` 開頭增加明確的長度相等校驗，若 `proposedWinners.length != totalXPs.length || proposedWinners.length != totalTimes.length` 則 revert。

---

## 4. `DepositManager::sponsorGame` Should Revert if the Game Is `Cancelled` or `Concluded`

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DepositManager::sponsorGame` does not verify the state of the game when accepting sponsorship amounts. It simply records `pool.totalCollectedAmount += amount` and transfers tokens from the sponsor without checking whether the game is still active. This allows sponsors to fund games that are already `Cancelled` or `Concluded`. For `Concluded` games, there is no mechanism to retrieve the locked sponsorship tokens. The function also does not validate that `gameId` belongs to an actual game.

**Impact:**
Sponsors who send tokens to a `Concluded` game have no way to retrieve them — the tokens are permanently locked. Sponsors of `Cancelled` games may also be unable to recover funds depending on the refund logic.

**Recommended Mitigation:**
Add a game state check at the start of `sponsorGame` that reverts if the game is `Cancelled` or `Concluded`. Also add a `gameId` existence validation.

---

**[中文版本]**

**描述：**
`DepositManager::sponsorGame` 接受贊助金額時未校驗遊戲狀態，直接累加 `totalCollectedAmount` 並從贊助者轉賬，允許向已 `Cancelled` 或 `Concluded` 的遊戲贊助。對 `Concluded` 遊戲而言，沒有任何機制可取回被鎖定的贊助代幣；函數也未驗證 `gameId` 是否對應真實遊戲。

**影響：**
向已 `Concluded` 遊戲發送代幣的贊助者無法取回資金，代幣被永久鎖定。向 `Cancelled` 遊戲的贊助者也可能無法根據退款邏輯恢復資金。

**修復建議：**
在 `sponsorGame` 開頭添加遊戲狀態校驗，若遊戲為 `Cancelled` 或 `Concluded` 則 revert；同時添加 `gameId` 的存在性校驗。

---

## 5. `DividendManager::distributePayout` Will Always Revert After 255 Payouts, Preventing Any Future Payout Distributions

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DividendManager::HolderManagementStorage::_currentPayoutIndex` is declared as `uint8`. Every call to `distributePayout` increments this counter via `$._payouts[$._currentPayoutIndex++]`. The maximum value of `uint8` is 255, so after 255 successful calls to `distributePayout`, the 256th increment causes an arithmetic overflow. All further calls to `distributePayout` will always revert due to the overflow.

**Impact:**
After 255 payout distributions the `distributePayout` function permanently reverts, making it impossible to distribute any further dividends to token holders. The protocol's dividend mechanism becomes permanently frozen after 255 payouts.

**Recommended Mitigation:**
Increase `_currentPayoutIndex` to a larger type such as `uint16` or `uint256`. Update the corresponding `uint8` keys in `_balanceHistory` and `_payouts` mappings to match the new type. Using `uint56` would use no additional storage slot given the current struct layout.

---

**[中文版本]**

**描述：**
`DividendManager::HolderManagementStorage::_currentPayoutIndex` 聲明為 `uint8`，每次調用 `distributePayout` 時通過 `$._payouts[$._currentPayoutIndex++]` 遞增此計數器。`uint8` 最大值為 255，第 256 次調用時算術溢出，所有後續 `distributePayout` 調用均因溢出而永久 revert。

**影響：**
255 次派息分配後 `distributePayout` 函數永久 revert，無法再向代幣持有者分配股息，協議的股息機制在 255 次派息後永久凍結。

**修復建議：**
將 `_currentPayoutIndex` 升級為更大的類型（如 `uint16` 或 `uint256`）；更新 `_balanceHistory` 和 `_payouts` 映射中對應的 `uint8` 鍵類型；考慮到當前結構體佈局，使用 `uint56` 無需額外存儲槽。

---

## 6. Investor Can Prevent Themselves From Being Removed by Making `removeInvestor` Revert

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`RegistryService::removeInvestor` requires `investors[_id].walletCount == 0` before proceeding. Investors can call `addWalletByInvestor` to add wallets without any restriction, while only `EXCHANGE` role accounts can remove wallets via `removeWallet`. A malicious investor can therefore add enough wallets to inflate `walletCount` to `MAX_WALLETS_PER_INVESTOR`, making `removeInvestor` permanently revert with "Investor has wallets". The attacker retains their registered status indefinitely.

**Impact:**
`removeInvestor` can be permanently DOSed by the investor themselves, making any investor unremovable by adding wallets. This undermines compliance and administrative controls that depend on the ability to remove investors.

**Recommended Mitigation:**
Remove the `addWalletByInvestor` function to eliminate the unrestricted wallet-addition path that investors can exploit to prevent their own removal.

---

**[中文版本]**

**描述：**
`RegistryService::removeInvestor` 要求 `walletCount == 0` 才能繼續執行。投資者可不受限制地通過 `addWalletByInvestor` 添加錢包，而只有 `EXCHANGE` 角色賬戶才能通過 `removeWallet` 刪除錢包。惡意投資者因此可添加足夠數量的錢包，使 `walletCount` 達到 `MAX_WALLETS_PER_INVESTOR`，使 `removeInvestor` 永久因「Investor has wallets」而 revert。

**影響：**
投資者可通過添加錢包永久 DOS `removeInvestor`，使自身無法被移除，破壞依賴投資者移除能力的合規和管理控制。

**修復建議：**
移除 `addWalletByInvestor` 函數，消除投資者可利用的不受限制的錢包添加路徑。

---

## 7. Misleading Revert Message in `onlyUser` Modifier

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The `onlyUser` modifier restricts access by checking `msg.sender == user`. However, when the check fails it reverts with the message "OnlyOwner" — a misleading string, since the restricted role is not an owner but a specific user address. This semantic mismatch makes debugging and error interpretation harder and can confuse off-chain tooling, auditors, and end users who encounter the error.

**Impact:**
Incorrect revert messages obscure the actual access control restriction, making it harder to diagnose failures. Callers and monitoring tools will attribute access failures to an owner restriction rather than the correct user-specific restriction.

**Recommended Mitigation:**
Update the revert message in the `onlyUser` modifier to accurately reflect the enforced role, e.g., "OnlyUser" or "Unauthorized".

---

**[中文版本]**

**描述：**
`onlyUser` 修飾符通過校驗 `msg.sender == user` 限制訪問，但校驗失敗時以 "OnlyOwner" 的錯誤信息 revert——這是具有誤導性的字符串，因受限角色不是 owner 而是特定用戶地址。此語義不匹配使調試和錯誤解讀更加困難，並可能混淆鏈下工具、審計員和最終用戶。

**影響：**
不正確的 revert 信息遮蔽了真實的訪問控制限制，使故障診斷更困難；調用者和監控工具會將訪問失敗歸因於 owner 限制而非實際的用戶特定限制。

**修復建議：**
將 `onlyUser` 修飾符中的 revert 信息更新為準確反映所執行角色的描述，例如 "OnlyUser" 或 "Unauthorized"。

---

## 8. `RegistryService::addWallet` Should Revert if the Wallet Being Added Has Positive Balance of `DSToken`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`RegistryService::addWallet` does not update investor wallet or total balances when adding a wallet that already holds a positive `DSToken` balance. This creates multiple inconsistent states: investor totals do not reflect the wallet's existing balance; investor count thresholds may not be triggered; compliance checks that compare investor balance to transfer amounts may behave incorrectly; and the "new investor" logic may fire incorrectly. Transfers can also revert due to underflow when subtracting from internal wallet or investor balances that do not account for the pre-existing tokens.

**Impact:**
Adding a wallet with a pre-existing token balance produces incorrect accounting state that can cause compliance checks to be bypassed or transfers to revert with underflow errors, resulting in tokens being stuck.

**Recommended Mitigation:**
`RegistryService::addWallet` should revert if the wallet being added has a positive balance of `DSToken`. Alternatively, update internal accounting state to register the existing tokens by calling `DSToken::updateInvestorBalance` and `addWalletToList` before associating the wallet.

---

**[中文版本]**

**描述：**
`RegistryService::addWallet` 在添加持有正 `DSToken` 餘額的錢包時，不更新投資者的錢包或總餘額，導致多種不一致狀態：投資者總量未反映錢包現有餘額；投資者計數閾值可能未被觸發；將投資者餘額與轉賬金額比較的合規校驗可能行為異常；「新投資者」邏輯可能錯誤觸發；內部扣除時也可能因未計入已有代幣而發生下溢 revert，導致代幣被卡住。

**影響：**
添加持有已有代幣餘額的錢包產生錯誤的計費狀態，可能導致合規校驗被繞過或轉賬因下溢錯誤而 revert，使代幣被永久鎖定。

**修復建議：**
若待添加錢包持有正 `DSToken` 餘額，`RegistryService::addWallet` 應 revert；或在關聯錢包前調用 `DSToken::updateInvestorBalance` 和 `addWalletToList` 更新內部計費狀態以登記現有代幣。

---

## 9. Remove Unused Return Value from `pUSDeVault::stakeUSDe` and Explicitly Revert if `USDeAssets == 0`

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeVault::stakeUSDe` has an unused return value that is never checked by callers. Additionally, the function does not explicitly revert when `USDeAssets == 0`, meaning zero-value stake operations silently succeed without performing any meaningful state change. This can lead to misleading event emissions and wasted gas for callers who inadvertently pass zero.

**Impact:**
Zero-value staking operations succeed silently, emitting events without any real state change and wasting gas. The unused return value means callers cannot rely on the function's output for success verification.

**Recommended Mitigation:**
Remove the unused return value from `pUSDeVault::stakeUSDe` and add an explicit `require(USDeAssets > 0)` check at the start of the function to revert for zero-value inputs.

---

**[中文版本]**

**描述：**
`pUSDeVault::stakeUSDe` 有一個未使用的返回值且調用方從未校驗；此外函數在 `USDeAssets == 0` 時未明確 revert，零值質押操作靜默成功但不執行任何有意義的狀態變更，可能導致誤導性的事件觸發和不必要的 gas 消耗。

**影響：**
零值質押操作靜默成功，觸發事件卻無真實狀態變更，浪費 gas；未使用的返回值使調用方無法依賴函數輸出進行成功驗證。

**修復建議：**
移除 `pUSDeVault::stakeUSDe` 中未使用的返回值，並在函數開頭添加顯式的 `require(USDeAssets > 0)` 校驗，對零值輸入進行 revert。

---

## 10. `SessionManager::cancelGameIfCreatorMissing, endGame` Could Revert Due to Out of Gas if There Are Too Many Questions in a Game

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Both `SessionManager::endGame` and `cancelGameIfCreatorMissing` iterate over all questions in `gameQuestions[_gameId]` in an unbounded loop. There is no restriction on the number of questions a game can have. When the total gas consumed by iterating over a very large question list exceeds the block gas limit, both functions permanently revert due to out of gas. Neither function supports partial execution or pagination.

**Impact:**
If `endGame` cannot complete, users and the game creator lose their funds and fees since the game cannot transition to the `Ended` state. If `cancelGameIfCreatorMissing` reverts, users cannot cancel and recover their entry fees even when the creator is absent and the game has expired.

**Recommended Mitigation:**
Limit the maximum number of questions that can be added to a game. Enforce this cap in `QuestionManager` when questions are added.

---

**[中文版本]**

**描述：**
`SessionManager::endGame` 和 `cancelGameIfCreatorMissing` 都對 `gameQuestions[_gameId]` 中的所有問題進行無界循環遍歷，且沒有對遊戲問題數量的限制。當問題列表過大導致迭代消耗的總 gas 超過區塊 gas 上限時，兩個函數均因 out-of-gas 永久 revert，且均不支持部分執行或分頁。

**影響：**
`endGame` 無法完成時，用戶和遊戲創建者的資金和費用被鎖定；`cancelGameIfCreatorMissing` revert 時，即使創建者缺席且遊戲已過期，用戶也無法取消並取回入場費。

**修復建議：**
限制每個遊戲可添加的最大問題數量，在 `QuestionManager` 添加問題時強制執行此上限。

---

## 11. `StakingVault::claimWithdraw` Should Revert if `assets` Are Zero

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::claimWithdraw` does not validate that the `assets` amount to be claimed is greater than zero. Allowing zero-value withdraw claims means callers can trigger state transitions and event emissions without any economic effect, wasting gas and potentially creating misleading on-chain records.

**Impact:**
Zero-value withdrawal claims succeed silently, emitting events and advancing state without economic meaning, leading to wasted gas and potentially misleading tracking data.

**Recommended Mitigation:**
Add an explicit `require(assets > 0)` check at the start of `claimWithdraw` to revert zero-value inputs.

---

**[中文版本]**

**描述：**
`StakingVault::claimWithdraw` 未驗證待認領的 `assets` 金額是否大於零，允許零值提款認領會觸發狀態轉換和事件觸發卻無任何經濟效果，浪費 gas 並可能產生誤導性的鏈上記錄。

**影響：**
零值提款認領靜默成功，觸發事件並推進狀態卻無實際意義，導致 gas 浪費和潛在的誤導性跟蹤數據。

**修復建議：**
在 `claimWithdraw` 開頭添加顯式的 `require(assets > 0)` 校驗，對零值輸入進行 revert。

---

## 12. `StakingVault::distributeYield` Should Revert When There Are No Vault Shares

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::distributeYield` does not check whether any vault shares exist before distributing yield. If called when `totalSupply()` is zero or only equals `DEAD_SHARES`, the yield distribution is economically meaningless — there are no real stakers to receive it. The yield amount is still consumed from the caller but has no beneficiaries, effectively burning or misallocating yield.

**Impact:**
Yield distributed when there are no stakers (or only dead shares) is wasted with no actual recipients. This is a silent loss for the protocol and/or the yield distributor.

**Recommended Mitigation:**
Add a check at the start of `distributeYield` that reverts with a custom error (e.g., `NoStakers()`) if `totalSupply() <= DEAD_SHARES`, preventing yield distribution to empty vaults.

---

**[中文版本]**

**描述：**
`StakingVault::distributeYield` 在分配收益前未校驗是否存在任何 vault 份額。若在 `totalSupply()` 為零或僅等於 `DEAD_SHARES` 時調用，收益分配在經濟上毫無意義——沒有真實的質押者可以接收，收益金額仍從調用方消耗，卻無受益人，實際上等同於損耗。

**影響：**
在沒有質押者（或僅有 dead shares）的情況下分配的收益被白白消耗，無實際受益者，是協議和/或收益分配方的靜默損失。

**修復建議：**
在 `distributeYield` 開頭添加校驗，若 `totalSupply() <= DEAD_SHARES` 則以自定義錯誤（如 `NoStakers()`）revert，防止向空 vault 分配收益。

---

## 13. Swaps Will Revert When `A = B + Xhat - x = 0`

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`CompensationPriceFinder::_zeroForOneGetFinalCompensationPrice` has two branches based on the sign of `A`. When `sumX == rangeVirtualReserves0`, the value `A = sumX - rangeVirtualReserves0` equals exactly zero. The positive branch is taken (since `sumX >= rangeVirtualReserves0`), and eventually `Math512Lib::div512by256(d1, d0, a)` is called with `a = 0`. This reverts with `DivisorZero()`. The mathematically correct behavior for `A = 0` is to solve the linear equation `p_star = (Ŷ + y) / 2L` rather than the quadratic.

**Impact:**
Swaps that happen to produce `sumX == rangeVirtualReserves0` will always revert, making a class of economically valid swaps permanently unexecutable.

**Recommended Mitigation:**
Handle the `A = 0` edge case separately. When `A == 0`, compute `p_star` using the linear formula `(sumUpToThisRange1 + sumY) / (2 * liquidity)` instead of the quadratic solver.

---

**[中文版本]**

**描述：**
`CompensationPriceFinder::_zeroForOneGetFinalCompensationPrice` 依據 `A` 的符號分為兩個分支。當 `sumX == rangeVirtualReserves0` 時，`A = sumX - rangeVirtualReserves0` 恰好為零；正數分支被執行（因 `sumX >= rangeVirtualReserves0`），最終調用 `Math512Lib::div512by256(d1, d0, a)`，其中 `a = 0`，觸發 `DivisorZero()` revert。`A = 0` 時數學上正確的解法是求解線性方程 `p_star = (Ŷ + y) / 2L` 而非二次方程。

**影響：**
恰好產生 `sumX == rangeVirtualReserves0` 的交換會始終 revert，使一類在經濟上有效的交換永久無法執行。

**修復建議：**
單獨處理 `A = 0` 的邊界情況：當 `A == 0` 時，使用線性公式 `(sumUpToThisRange1 + sumY) / (2 * liquidity)` 計算 `p_star`，而非調用二次求解器。

---

## 14. Wrong Revert Reason in `onSlash` Functionality

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
In `VaultTokenized::onSlash`, the `captureEpoch` parameter is validated with: `if ((currentEpoch_ > 0 && captureEpoch < currentEpoch_ - 1) || captureEpoch > currentEpoch_)`. When `currentEpoch_` is 0, the subexpression `currentEpoch_ - 1` underflows (becomes `type(uint48).max`), causing the condition `captureEpoch < currentEpoch_ - 1` to always be false due to the `currentEpoch_ > 0` guard. However, the broader arithmetic underflow itself can cause the transaction to revert with a generic panic rather than the intended `Vault__InvalidCaptureEpoch` custom error, making debugging more difficult.

**Impact:**
When `currentEpoch_` is 0 and an invalid `captureEpoch` is passed, the transaction reverts with a generic arithmetic error instead of the intended custom error `Vault__InvalidCaptureEpoch`, obscuring the cause of the failure.

**Recommended Mitigation:**
Rewrite the condition to avoid arithmetic underflow by changing `captureEpoch < currentEpoch_ - 1` to `captureEpoch + 1 < currentEpoch_`. This ensures safe evaluation for all values of `currentEpoch_` and always reverts with the correct custom error.

---

**[中文版本]**

**描述：**
`VaultTokenized::onSlash` 中的 `captureEpoch` 驗證條件為 `(currentEpoch_ > 0 && captureEpoch < currentEpoch_ - 1) || captureEpoch > currentEpoch_`。當 `currentEpoch_` 為 0 時，子表達式 `currentEpoch_ - 1` 發生下溢（變為 `type(uint48).max`），儘管有 `currentEpoch_ > 0` 守衛防止條件為真，但算術下溢本身可能導致交易以通用 panic 錯誤 revert，而非預期的 `Vault__InvalidCaptureEpoch` 自定義錯誤。

**影響：**
當 `currentEpoch_` 為 0 且傳入無效 `captureEpoch` 時，交易以通用算術錯誤而非自定義錯誤 `Vault__InvalidCaptureEpoch` revert，遮蔽了失敗的真實原因，增加調試難度。

**修復建議：**
將條件 `captureEpoch < currentEpoch_ - 1` 改寫為 `captureEpoch + 1 < currentEpoch_` 以避免算術下溢，確保對 `currentEpoch_` 的所有值都能安全求值，並始終以正確的自定義錯誤 revert。
