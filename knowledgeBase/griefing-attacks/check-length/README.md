# check-length (11)

> Issues where array length checks, minimum amount checks, or boundary validations were incorrect or missing.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Missing Check for Residual Input Tokens When Route Weights Are Incomplete

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
`CoreAggregator._executeSwap` splits a swap across multiple routes based on their `weight`. Each route consumes a proportional share of the total `amountIn` based on the remaining weight. However, there is no final validation to ensure that the cumulative weights of all provided routes sum to `MAX_WEIGHT` (10,000). If routes are submitted with weights totaling less than `MAX_WEIGHT`, the leftover input tokens that were never routed remain locked in the contract with no path to reclaim or return them. The function neither reverts nor refunds the unrouted residual.

**Impact:**
Users who submit incomplete route weights permanently lose the portion of `amountIn` that was not routed. The tokens are locked in the aggregator contract with no recovery mechanism.

**Recommended Mitigation:**
After the routes loop, validate that the sum of weights for each unique `tokenIn` group equals `MAX_WEIGHT`. If the total weight is not fully allocated, revert with an `InvalidRoutes` error to ensure the full input amount is always either fully routed or the transaction fails cleanly.

---

**[中文版本]**

**描述：**
`CoreAggregator._executeSwap` 根據 `weight` 將兌換拆分到多條路由。每條路由根據剩餘權重消耗 `amountIn` 的相應份額。然而，沒有最終驗證確保所有提供路由的累積權重總和等於 `MAX_WEIGHT`（10,000）。如果提交的路由權重總和小於 `MAX_WEIGHT`，未被路由的剩餘輸入代幣將被鎖定在合約中，沒有任何途徑回收或退還。該函數既不回滾也不退款。

**影響：**
提交不完整路由權重的用戶將永久損失 `amountIn` 中未被路由的部分。這些代幣被鎖定在聚合器合約中，無法回收。

**修復建議：**
在路由循環後，驗證每個唯一 `tokenIn` 組的權重總和等於 `MAX_WEIGHT`。如果總權重未完全分配，以 `InvalidRoutes` 錯誤回滾，確保全部輸入金額要麼完全路由要麼交易清晰失敗。

---

## 2. Array length checks in `FixedRanksReward::getRewards`, `getReward` check against the wrong comparator

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`FixedRanksReward::getRewards` validates ranked rewards existence using `rankedRewards[sessionId].length > 0`, but the meaningful guard should be `>= winners.length` to ensure there are enough reward slots for all winners. Similarly, `FixedRanksReward::getReward` uses `length > 0` where the correct check is `length > position` to confirm the specified winner position has a defined reward. Both current checks can pass even when the reward array is too short to serve all winners or the requested position.

**Impact:**
Games can reach conclusion with insufficient reward slots, causing winner claim transactions to revert with out-of-bounds errors after the game has already concluded. Winners are unable to claim rewards for positions not covered by the ranked reward array.

**Recommended Mitigation:**
Change the comparator in `getRewards` to `rankedRewards[sessionId].length >= winners.length`, and in `getReward` to `rankedRewards[sessionId].length > position`. Update the error name accordingly to reflect the more specific condition.

---

**[中文版本]**

**描述：**
`FixedRanksReward::getRewards` 使用 `rankedRewards[sessionId].length > 0` 驗證排名獎勵是否存在，但有意義的保護應為 `>= winners.length` 以確保所有獲勝者都有足夠的獎勵槽位。類似地，`FixedRanksReward::getReward` 使用 `length > 0`，正確的檢查應為 `length > position` 以確認指定獲勝者位置有已定義的獎勵。當前兩個檢查在獎勵數組不足以服務所有獲勝者或請求位置時均可通過。

**影響：**
遊戲可能以不足的獎勵槽位結束，導致獲勝者的領取交易在遊戲已結束後以越界錯誤回滾。獲勝者無法領取排名獎勵數組未涵蓋位置的獎勵。

**修復建議：**
將 `getRewards` 中的比較符改為 `rankedRewards[sessionId].length >= winners.length`，將 `getReward` 中的改為 `rankedRewards[sessionId].length > position`。相應地更新錯誤名稱以反映更具體的條件。

---

## 3. Balance check for yield claims in `PerpetualBond::_validate` can be easily bypassed

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
In `PerpetualBond::_validate`, a yield claim requires `balanceOf(_caller) > 0`. This check can be trivially satisfied by holding just 1 wei of `PerpetualBond` tokens. A more meaningful threshold aligned with other parts of the contract would require the caller's bond balance (converted via `_convertToBond`) to exceed `minimumTxnThreshold`. The secondary check on `accruedRewardAtCheckpoint[_caller]` is also redundant since `requestYieldClaim` already performs a value-based threshold check before reaching `_validate`.

**Impact:**
Any address holding a dust-level bond position can bypass the intent of the balance guard and initiate yield claims, potentially causing dust-level claims and clogging claim processing.

**Recommended Mitigation:**
Replace `require(balanceOf(_caller) > 0, "!bond balance")` with `require(_convertToBond(balanceOf(_caller)) > minimumTxnThreshold, "!bond balance")` to enforce a meaningful minimum balance requirement.

---

**[中文版本]**

**描述：**
在 `PerpetualBond::_validate` 中，收益領取要求 `balanceOf(_caller) > 0`。持有僅 1 wei 的 `PerpetualBond` 代幣即可輕易滿足此檢查。更有意義的閾值應要求調用者的債券餘額（通過 `_convertToBond` 轉換）超過 `minimumTxnThreshold`，與合約其他部分保持一致。對 `accruedRewardAtCheckpoint[_caller]` 的次要檢查也是多餘的，因為 `requestYieldClaim` 在到達 `_validate` 之前已執行了基於價值的閾值檢查。

**影響：**
持有塵埃級別債券頭寸的任何地址都可繞過餘額保護的預期目的，發起收益領取，可能導致塵埃級別的領取並堵塞領取處理。

**修復建議：**
將 `require(balanceOf(_caller) > 0, "!bond balance")` 替換為 `require(_convertToBond(balanceOf(_caller)) > minimumTxnThreshold, "!bond balance")` 以執行有意義的最低餘額要求。

---

## 4. Enforce minimum transaction amounts in `StakingVault`

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault` does not enforce any minimum transaction size for deposits or withdrawals. Sophisticated vault attacks have historically used dust-level (e.g. 1 wei) transactions to manipulate rounding and vault state variables. Since hBTC uses 8 decimals and is 1:1 redeemable for BTC, tiny amounts correspond to fractions of a cent. A configurable minimum transaction threshold would eliminate this attack vector without impacting legitimate users.

**Impact:**
The vault is exposed to potential precision manipulation attacks via tiny deposit or withdrawal amounts that exploit rounding behavior in the ERC-4626 share calculation.

**Recommended Mitigation:**
Override `ERC4626::_deposit` and `_withdraw` to revert if `assets` is smaller than a configurable minimum transaction amount. Make this minimum a parameter that the admin can adjust as BTC price fluctuates to maintain a floor around $10 or a similarly appropriate value.

---

**[中文版本]**

**描述：**
`StakingVault` 對存款或提款未執行任何最低交易金額限制。歷史上已知複雜的金庫攻擊使用塵埃級別（如 1 wei）交易操縱舍入行為和金庫狀態變量。由於 hBTC 使用 8 位小數且與 BTC 1:1 可兌換，極小金額對應分幣以下的價值。可配置的最低交易閾值將消除此攻擊向量，同時不影響合法用戶。

**影響：**
金庫通過極小存款或提款金額利用 ERC-4626 份額計算中的舍入行為，暴露於潛在的精度操縱攻擊。

**修復建議：**
重寫 `ERC4626::_deposit` 和 `_withdraw`，如果 `assets` 小於可配置的最低交易金額則回滾。使此最低值成為管理員可隨 BTC 價格波動調整的參數，以維持約 $10 或類似合適值的下限。

---

## 5. Invalid `validateRedemptionParams` check

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
`validateRedemptionParams` is intended to provide UX-level slippage protection by ensuring the user-supplied redemption parameters (`exitMode`, `exitFee`, `cooldownSeconds`) match the protocol's current parameters. However, the implementation logic is inverted: the function returns (does nothing) when the parameters do not match, and reverts when the parameters do match. This completely defeats the slippage protection — mismatches are silently accepted and exact matches cause unexpected reverts.

**Impact:**
Users receive no slippage protection on redemptions. Transactions where system parameters have changed since the user assembled their transaction will proceed without warning, and transactions with matching correct parameters will unexpectedly revert.

**Recommended Mitigation:**
Swap the `return` and `revert` statements so that the function reverts with `RedemptionParamsMismatch` when parameters do not match and returns normally when they match.

---

**[中文版本]**

**描述：**
`validateRedemptionParams` 旨在通過確保用戶提供的贖回參數（`exitMode`、`exitFee`、`cooldownSeconds`）與協議當前參數匹配來提供 UX 級別的滑點保護。然而實現邏輯是反的：當參數不匹配時函數返回（什麼都不做），當參數匹配時則回滾。這完全破壞了滑點保護——不匹配被靜默接受，而精確匹配導致意外回滾。

**影響：**
用戶在贖回時無法獲得滑點保護。用戶組裝交易後系統參數發生變化的交易將在無警告的情況下繼續執行，而具有匹配正確參數的交易將意外回滾。

**修復建議：**
交換 `return` 和 `revert` 語句，使函數在參數不匹配時以 `RedemptionParamsMismatch` 回滾，在匹配時正常返回。

---

## 6. Lack of check for 0 shares minted

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`previewDeposit(assets)` can legitimately return 0 shares for tiny deposit amounts due to ERC-4626 rounding and/or deposit fees that consume the entire asset value. If no guard is placed against a zero-share deposit, a user can call `deposit`, transfer assets to the vault, and receive 0 shares in return — effectively making an involuntary donation.

**Impact:**
Users making very small deposits can permanently lose their assets without receiving any vault shares. This is particularly harmful in deployments with deposit fees.

**Recommended Mitigation:**
Add a `require(shares > 0, "0 shares")` assertion inside `previewDeposit` (or the `_deposit` hook) so that any deposit that would mint zero shares reverts explicitly.

---

**[中文版本]**

**描述：**
由於 ERC-4626 的舍入和/或消耗全部資產價值的存款費，`previewDeposit(assets)` 對極小存款金額可合法地返回 0 份額。若無針對零份額存款的保護，用戶可調用 `deposit`，將資產轉入金庫，但收到 0 份額——實際上是被迫捐贈。

**影響：**
進行極小存款的用戶可能永久損失資產而未獲得任何金庫份額。在有存款費的部署中尤為有害。

**修復建議：**
在 `previewDeposit`（或 `_deposit` 鉤子）內添加 `require(shares > 0, "0 shares")` 斷言，確保任何會鑄造零份額的存款明確回滾。

---

## 7. Missing `USER_ROLE` Check Allows Unauthorized Participants in Joint Groups And Payouts

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
`Komiti::joinGroupWithJointContributor()` requires the caller to hold `USER_ROLE` via `onlyRole(USER_ROLE)`, but does not verify that the `secondaryContributor` address also holds `USER_ROLE`. This allows a primary contributor to register a secondary contributor who lacks the necessary system permissions, creating a participant whose role status is inconsistent with the system's access control model.

**Impact:**
Secondary contributors without `USER_ROLE` may be registered, potentially causing permission-related failures or inconsistencies in downstream participation and payout functions that check role membership.

**Recommended Mitigation:**
Add a `hasRole(USER_ROLE, secondaryContributor)` check inside `joinGroupWithJointContributor()` before registering the secondary contributor, and revert if the secondary contributor does not hold the required role.

---

**[中文版本]**

**描述：**
`Komiti::joinGroupWithJointContributor()` 通過 `onlyRole(USER_ROLE)` 要求調用者持有 `USER_ROLE`，但不驗證 `secondaryContributor` 地址是否也持有 `USER_ROLE`。這允許主要貢獻者註冊缺乏必要系統權限的次要貢獻者，創建角色狀態與系統訪問控制模型不一致的參與者。

**影響：**
不具備 `USER_ROLE` 的次要貢獻者可能被註冊，在檢查角色成員資格的下游參與和支付函數中潛在導致與權限相關的失敗或不一致。

**修復建議：**
在 `joinGroupWithJointContributor()` 中，在註冊次要貢獻者之前添加 `hasRole(USER_ROLE, secondaryContributor)` 檢查，如果次要貢獻者未持有所需角色則回滾。

---

## 8. Missing vesting check in `PerpetualBond::setVestingPeriod`

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`YToken::setVestingPeriod` includes a guard `require(getUnvestedAmount() == 0, "!vesting")` before permitting the vesting period to be updated, ensuring the period cannot be changed while rewards are actively vesting. The equivalent function `PerpetualBond::setVestingPeriod` lacks this check entirely, allowing the vesting period to be modified mid-vest — potentially shortening or extending it in ways that produce inconsistent vesting outcomes for current holders.

**Impact:**
An admin can alter the vesting period while rewards are in-flight, leading to unexpected changes in the amount and timing of rewards that users can claim.

**Recommended Mitigation:**
Add `require(getUnvestedAmount() == 0, "!vesting")` to `PerpetualBond::setVestingPeriod` to match the safeguard already present in `YToken::setVestingPeriod`.

---

**[中文版本]**

**描述：**
`YToken::setVestingPeriod` 在允許更新歸屬期前包含保護 `require(getUnvestedAmount() == 0, "!vesting")`，確保在獎勵正在歸屬時不能更改週期。對應函數 `PerpetualBond::setVestingPeriod` 完全缺少此檢查，允許在歸屬中途修改歸屬期——可能以導致當前持有人歸屬結果不一致的方式縮短或延長歸屬期。

**影響：**
管理員可在獎勵進行中更改歸屬期，導致用戶可領取的獎勵金額和時間發生意外變化。

**修復建議：**
在 `PerpetualBond::setVestingPeriod` 中添加 `require(getUnvestedAmount() == 0, "!vesting")`，與 `YToken::setVestingPeriod` 中已有的保護措施保持一致。

---

## 9. Missing zero length check in `AllowedMethodsEnforcer::getTermsInfo()`

**Severity:** 🟡 Medium
**Source:** `cyfrin/DelegationFramework1.md`

**Description:**
`AllowedMethodsEnforcer::getTermsInfo()` correctly validates that the provided terms length is divisible by 4 (since each method selector is 4 bytes). However, it does not reject empty terms where `_terms.length == 0`. An empty byte array satisfies `0 % 4 == 0` and produces an empty array of allowed methods. A delegation created with these empty terms appears to be set up successfully, but every actual method call will be rejected by the enforcer with `AllowedMethodsEnforcer:method-not-allowed` because there are no allowed methods in the list.

**Impact:**
Delegations with empty terms are silently accepted at creation time but can never be exercised, causing a misleading user experience and wasted delegation setup effort.

**Recommended Mitigation:**
Add an explicit length check `require(_terms.length > 0, "AllowedMethodsEnforcer:invalid-terms-length")` before the modulo check to reject empty terms upfront.

---

**[中文版本]**

**描述：**
`AllowedMethodsEnforcer::getTermsInfo()` 正確驗證提供的條款長度可被 4 整除（每個方法選擇器 4 字節）。但它不拒絕 `_terms.length == 0` 的空條款。空字節數組滿足 `0 % 4 == 0` 並產生空的允許方法數組。使用這些空條款創建的委託看似成功設置，但每個實際方法調用都會被執行者以 `AllowedMethodsEnforcer:method-not-allowed` 拒絕，因為允許列表中沒有方法。

**影響：**
帶有空條款的委託在創建時被靜默接受但永遠無法執行，造成誤導性的用戶體驗和浪費的委託設置工作。

**修復建議：**
在模數檢查之前添加明確的長度檢查 `require(_terms.length > 0, "AllowedMethodsEnforcer:invalid-terms-length")`，以提前拒絕空條款。

---

## 10. `STBL_Register::addAsset` does not check for non-empty asset name

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
`STBL_Register::addAsset` allows assets to be created with an empty `_name` string. However, `STBL_AssetDefinitionLib::isValid` marks any asset with an empty name field as invalid. This creates a protocol inconsistency: assets can be successfully registered and enabled in the system but will fail downstream validation checks via `isValid`, causing operations that depend on asset validity to revert for those assets.

**Impact:**
Assets created with empty names are permanently in a state where they pass creation but fail validation, making them unusable in any protocol path that calls `isValid`. This may block downstream operations with no straightforward remediation after deployment.

**Recommended Mitigation:**
Add `require(bytes(_name).length > 0, "empty name")` in `STBL_Register::addAsset` to prevent empty-name assets from being created, or remove the empty-name check from `isValid` if names are not considered a required field.

---

**[中文版本]**

**描述：**
`STBL_Register::addAsset` 允許使用空 `_name` 字符串創建資產。然而，`STBL_AssetDefinitionLib::isValid` 將任何名稱字段為空的資產標記為無效。這造成協議不一致：資產可以成功在系統中註冊和啟用，但在通過 `isValid` 的下游驗證檢查時會失敗，導致依賴資產有效性的操作對這些資產回滾。

**影響：**
使用空名稱創建的資產永久處於創建通過但驗證失敗的狀態，在任何調用 `isValid` 的協議路徑中均無法使用。部署後可能阻塞下游操作且無直接補救措施。

**修復建議：**
在 `STBL_Register::addAsset` 中添加 `require(bytes(_name).length > 0, "empty name")` 以防止創建空名稱資產；或者如果名稱不被視為必填字段，則從 `isValid` 中移除空名稱檢查。

---

## 11. `_receiverGas` check excludes minimum acceptable value

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
In the LayerZero bridge contracts `BridgeLR::send` and `BridgeMB::send`, the user-supplied `_receiverGas` is validated with `require(_receiverGas > MIN_RECEIVER_GAS, "!gas")`. The variable name `MIN_RECEIVER_GAS` semantically implies that the minimum itself is an acceptable value, but the strict `>` comparator excludes it. Users who supply exactly `MIN_RECEIVER_GAS` have their transaction revert despite providing what should be the minimum valid amount. The same off-by-one is present in `Bridge::setMIN_RECEIVER_GAS` and `Bridge::quote`.

**Impact:**
Users providing the exact minimum receiver gas have their transactions unnecessarily rejected, causing a confusing UX discrepancy between the named constant and the actual enforced minimum.

**Recommended Mitigation:**
Change the comparator from `>` to `>=` so that `_receiverGas == MIN_RECEIVER_GAS` is accepted as valid. Apply this change consistently in `BridgeLR::send`, `BridgeMB::send`, and `Bridge::quote`.

---

**[中文版本]**

**描述：**
在 LayerZero 橋接合約 `BridgeLR::send` 和 `BridgeMB::send` 中，用戶提供的 `_receiverGas` 通過 `require(_receiverGas > MIN_RECEIVER_GAS, "!gas")` 驗證。變量名 `MIN_RECEIVER_GAS` 在語義上暗示最小值本身是可接受的，但嚴格的 `>` 比較符排除了它。提供恰好等於 `MIN_RECEIVER_GAS` 的用戶的交易會回滾，儘管他們提供了應為最小有效金額的值。`Bridge::setMIN_RECEIVER_GAS` 和 `Bridge::quote` 中存在相同的差一錯誤。

**影響：**
提供恰好等於最低接收方 Gas 的用戶的交易被不必要地拒絕，在命名常量和實際執行的最低值之間造成令人困惑的 UX 差異。

**修復建議：**
將比較符從 `>` 改為 `>=`，使 `_receiverGas == MIN_RECEIVER_GAS` 被接受為有效。在 `BridgeLR::send`、`BridgeMB::send` 和 `Bridge::quote` 中一致應用此更改。
