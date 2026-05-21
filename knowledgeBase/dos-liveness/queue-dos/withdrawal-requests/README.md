# withdrawal-requests (9)

> Issues where withdrawal requests can be stuck, front-run, overwritten, or improperly finalized.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Single reverting withdrawal can block the BasisTradeVault withdrawal queue

**Severity:** 🟠 High
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeVault::processWithdrawal` processes exactly one request at the queue head and performs the final ERC20 `safeTransfer` to the request's user. If that transfer reverts, the whole transaction reverts and the head entry remains in place. Because the function always targets `queueHead` and provides no way to skip, quarantine, or edit the failing entry, a single reverting withdrawal permanently blocks the entire queue (head-of-line blocking). Common revert causes include the receiver being blacklisted by the token (e.g., USDC/USDT compliance lists) or the computed assets for a request becoming zero due to rounding/fees and the token reverting on zero-amount transfers. This can happen accidentally or be used to grief the protocol by placing an unprocessable request at the head.

**Impact:**
Withdrawal processing can be indefinitely halted for all users behind the stuck request, causing severe withdrawal delays for all other depositors. The queue remains stuck until a contract upgrade or manual intervention.

**Recommended Mitigation:**
Redesign away from a strict queue to a timelock plus user-pull model where each user calls `processWithdrawal` themselves after the timelock. Alternatively add a skip/quarantine mechanism: if a head withdrawal fails, move it into a frozen set keeping shares escrowed, advance `queueHead`, and allow others to proceed. Provide functions for the user to update their payout address and for agents to retry or cancel within policy.

---

**[中文版本]**

**描述：**
`BasisTradeVault::processWithdrawal` 每次僅處理隊列頭部的一筆請求，並向用戶地址發起最終的 ERC20 `safeTransfer`。如果這筆轉賬回滾，整個交易將回滾，隊列頭部條目保持不變。由於該函數始終針對 `queueHead` 並且不提供任何跳過或隔離機制，單筆無法處理的提現將永久阻塞整個隊列（隊首阻塞）。常見回滾原因包括接收方被代幣黑名單（如 USDC/USDT）或因捨入/手續費導致 assets 為零而觸發零額轉賬回滾。

**影響：**
所有排在被阻塞請求之後的用戶的提現處理將被無限期暫停，造成其他存款人嚴重的提現延遲。直到合約升級或人工干預，隊列才會恢復。

**修復建議：**
將嚴格隊列模式重設為時間鎖+用戶主動拉取模式，每位用戶在時間鎖期後自行調用 `processWithdrawal`。或增加跳過/隔離機制：隊首提現失敗時將其移入凍結集合並保留份額託管，推進 `queueHead`，允許其他用戶繼續。提供用戶更新收款地址和代理人重試/取消的函數。

---

## 2. APR Targets are not updated when withdrawal requests are sent to the SharesCooldown to reflect the change on NAVs caused by the charged fees for the withdrawal

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The execution path for processing a withdrawal request sent to the `SharesCooldown` charges fees by burning tranche shares and updating the Tranche NAV and `reserveNav` accordingly (via `SharesCooldown::requestRedeem` → `accrueFee` → `Tranche::burnSharesAsFee` → `CDO::accrueFee` → `Accounting::accrueFee`). The problem is that the APR Targets for the Tranches are not recalculated to reflect the changes to the NAVs after this fee accrual. The system will therefore use outdated APR targets until a new operation is performed that updates them.

**Impact:**
Outdated APR targets — especially outdated and higher-than-actual APR Targets for the SR Tranche — will cause Junior Tranche holders to earn less interest than they should, as the system incorrectly estimates the senior tranche's expected yield.

**Recommended Mitigation:**
Refactor the `Accounting::accrueFee` function to update the APR Target after each fee accrual, similar to how `Accounting::updateBalanceFlow` already does.

---

**[中文版本]**

**描述：**
處理發送至 `SharesCooldown` 的提現請求時，系統會根據贖回的 Tranche Shares 數量收取費用，以銷毀份額的形式更新 Tranche NAV 和 `reserveNav`（執行路徑：`SharesCooldown::requestRedeem` → `accrueFee` → `Tranche::burnSharesAsFee` → `CDO::accrueFee` → `Accounting::accrueFee`）。問題在於 NAV 變化後，各 Tranche 的 APR 目標並未重新計算，系統會持續使用過時 APR 目標直到有新操作觸發更新。

**影響：**
過時且高於實際值的 SR Tranche APR 目標使 JR Tranche 持有人獲得的利息少於應得，因系統誤估 senior tranche 的預期收益。

**修復建議：**
重構 `Accounting::accrueFee` 函數，使其在每次費用累計後更新 APR 目標，參考 `Accounting::updateBalanceFlow` 的做法。

---

## 3. BasisTradeTailor withdrawal request overwrite enables race conditions

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`BasisTradeTailor::requestWithdrawal` unconditionally overwrites any existing withdrawal request with a new amount and provides no explicit cancellation mechanism. When a user attempts to modify an existing request, the final outcome depends entirely on the transaction ordering relative to the agent's `processWithdrawal` call. If the agent processes the original request first before the user's modification transaction executes, the modification creates a brand-new request rather than replacing the old one, causing both amounts to be withdrawn in sequence. A user intending to reduce a 100-unit withdrawal to 50 units could end up withdrawing 150 units total if the agent processes the original request before the modification lands.

**Impact:**
Users may withdraw significantly more than intended due to race conditions between their modification transactions and the agent's processing calls. This can result in unintended over-withdrawal and unexpected fund movements.

**Recommended Mitigation:**
Prevent changing a non-zero request to another non-zero value directly. Require explicit cancellation first by adding a dedicated `cancelWithdrawal` function that sets the request to zero. The `requestWithdrawal` function should revert if a pending request already exists, forcing users to cancel before creating a new request.

---

**[中文版本]**

**描述：**
`BasisTradeTailor::requestWithdrawal` 會無條件覆蓋任何已有的提現請求，且未提供明確的取消機制。當用戶試圖修改現有請求時，最終結果完全取決於該修改交易和代理人 `processWithdrawal` 調用的順序。若代理人先處理原請求後用戶的修改才到，則用戶的修改會生成一筆全新請求，導致兩筆金額被依序提取。比如，想把 100 單位請求改成 50 的用戶，若代理先處理舊請求則實際總共會提取 150 單位。

**影響：**
用戶修改交易與代理人調用之間的競態條件可能導致超額提款，產生非預期資金流動。

**修復建議：**
禁止直接將非零請求改為另一非零值，要求用戶先顯式通過 `cancelWithdrawal` 函數取消，`requestWithdrawal` 檢查如有待處理請求則回滾，強制先取消後提交新請求。

---

## 4. Direct YToken deposits can lock funds below minimum withdrawal threshold

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`Manager::deposit` enforces a minimum deposit amount check requiring that the resulting shares meet a `minSharesInYToken` threshold. Similarly, the redeem flow requires the redemption amount to meet the same minimum. However, no such minimum is enforced when depositing directly into a `YToken` contract, where `YToken::_deposit` and `YTokenL2::_deposit` only require the receiver to be non-zero and the amounts to be positive. As a result, a user can deposit an amount that results in fewer shares than `minSharesInYToken`, which cannot be withdrawn through the `Manager` due to its minimum withdrawal check. The stuck shares cannot be accessed through the normal exit path.

**Impact:**
Users can bypass the minimum share threshold by depositing directly into a `YToken`. If the resulting share amount is below the minimum allowed for withdrawal via the `Manager`, the user will be unable to exit their position. This leads to unintentionally locked funds and a degraded user experience.

**Recommended Mitigation:**
Enforce the `minSharesInYToken` threshold in `YToken::_deposit` and `YTokenL2::_deposit` to prevent sub-threshold deposits. Additionally, validate post-withdrawal balances to ensure users are not left with non-withdrawable dust (require remaining shares to be either zero or above the minimum threshold).

---

**[中文版本]**

**描述：**
`Manager::deposit` 透過最低份額檢查強制要求存款產生的份額達到 `minSharesInYToken` 閾值，贖回也有同門檻。但直接向 `YToken` 合約存款時沒有此限制，`YToken::_deposit` 和 `YTokenL2::_deposit` 僅要求接收方非零且金額大於零。因此可存入導致份額低於 `minSharesInYToken` 的金額，而這些份額因 Manager 限制將無法正常提取。

**影響：**
用戶可繞過最低份額門檻存款，若產生份額低於 Manager 能提取的最低額，則無法退出資產造成資金鎖死。

**修復建議：**
在 `YToken::_deposit` 與 `YTokenL2::_deposit` 強制檢查 `minSharesInYToken`，防止低於門檻的直接存款。提款後亦驗證餘額，確保剩餘份額為零或達門檻，無無法提取之零碎份額。

---

## 5. Finalizing withdrawal requests on the SharesCooldown contract allows for third-parties to override user's chosen output token

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
During `Tranche::withdraw/redeem`, the user can select a desired output token. When the exit mode is `SharesLock`, however, the final token received by the user is no longer under their control because `SharesCooldown::finalize` is permissionless — any caller can choose the output token at finalization time. This enables third parties to finalize a user's claim using a different token than originally intended. For example, if a user selected `sUSDe` as the output token, a permissionless finalizer could instead specify `USDe`, forcing the user to wait through an additional unstaking period on the `sUSDe` contract before receiving their assets, extending their wait time well beyond what they agreed to.

**Impact:**
Users' intended output token preferences are overridable by any third party at finalization time. This can substantially extend the time users must wait to receive their assets, as they may be forced into longer cooldown or unstaking periods than they chose.

**Recommended Mitigation:**
Persist the user's chosen output token when creating the cooldown request and enforce it during permissionless finalization. Only the user themselves should be able to override their token choice via a permissioned finalization path.

---

**[中文版本]**

**描述：**
`Tranche::withdraw/redeem` 流程中，用戶可選擇輸出代幣。但退出模式為 `SharesLock` 時，實際收到的代幣不再完全由用戶決定，原因是 `SharesCooldown::finalize` 是無權限限制的：任何人可選擇輸出代幣實施最終結算。第三方因此可覆蓋用戶原初偏好。例如用戶選擇 `sUSDe` 作為輸出，無許可執行者可以改為 `USDe`，強迫用戶再經歷一輪 sUSDe 解鎖等待。

**影響：**
用戶提現時的目標代幣偏好可能被第三方覆蓋，造成用戶等待超預期時間甚至二次冷卻。

**修復建議：**
在創建冷卻請求時保存用戶選擇的代幣，並在無權限 finalize 強制執行此選擇，僅允許用戶本身有額外權限覆蓋其選擇。

---

## 6. Front-Running DoS on Batch Settlement via Rolling Hash Invalidation

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
The `OmniVaultManager` employs a rolling hash mechanism where each deposit and withdrawal request appends to a shared hash. During settlement, the `SETTLER_ROLE` must provide data that exactly reconstructs the rolling hash. The vulnerability arises because any user can submit a new deposit or withdrawal request that changes the rolling hash. If this occurs after the settler has prepared their settlement transaction but before it confirms on-chain, the settlement reverts due to hash mismatch. An attacker can therefore front-run settlement transactions to indefinitely block settlements, preventing users from receiving vault shares or withdrawing assets. The only recovery mechanisms are waiting for `MAX_PENDING_REQUESTS` to be exhausted or waiting for the `RECLAIM_DELAY` period.

**Impact:**
Batch settlement can be indefinitely blocked by any user who submits a new request in the same block as the settlement transaction. This prevents deposits from being settled (users cannot receive vault shares) and withdrawals from being settled (users cannot receive their assets), causing temporary fund lockup.

**Recommended Mitigation:**
Either decouple individual requests from the shared rolling hash using per-request settlement isolation, or separate request submission and settlement into distinct time periods where new requests are blocked during settlement processing to ensure stable batch state.

---

**[中文版本]**

**描述：**
`OmniVaultManager` 採用滾動哈希機制，每次存款與提現請求都會加入共用哈希。結算時，`SETTLER_ROLE` 必須提交可精確對上滾動哈希的數據。任何用戶均可插入新請求改變滾動哈希——如果這發生在結算方已準備好交易但尚未鏈上確認之間，結算會因哈希不符而失敗。攻擊者可以用搶跑方式無限期阻礙結算，致用戶無法獲得份額或資產。唯一恢復手段是等待 `MAX_PENDING_REQUESTS` 耗盡或 `RECLAIM_DELAY` 結束。

**影響：**
任何用戶在結算同區塊提交新請求時可永遠阻礙結算，導致存款、提現暫時鎖死。

**修復建議：**
逐請求獨立結算解耦哈希連動，或強制將提交請求與結算分爲不同時段，在批結算期間禁止新請求提交，確保批結算狀態穩定。

---

## 7. Increase in coverage can lead to a grief attack causing a DoS for previous withdrawal requests

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
An increment in `coverage` — caused by a large SR Tranche withdrawal or an increase in JR deposits — can be exploited to grief legitimate users' cooldown withdrawal requests. When coverage improves, subsequent withdrawals receive shorter cooldown periods. An attacker aware of a victim's pending SR Tranche withdrawal requesting `USDe` can create many small SR Tranche withdrawal requests designating the victim as receiver. These attacker requests have a shorter cooldown (due to the improved coverage) and, once finalized, increment the victim's `UnstakeCooldown` queue. By repeatedly creating and finalizing such requests before the victim's original request expires, the attacker can drive the victim's `UnstakeCooldown` queue to its limit. When the victim finally attempts to finalize their original withdrawal, the transaction reverts with `ExternalReceiverRequestLimitReached`.

**Impact:**
Legitimate SR Tranche withdrawals requesting `USDe` can be temporarily DoSed by griefing the victim's `UnstakeCooldown` slot limit. The victim cannot finalize their withdrawal until the attacker's requests expire and free up slots.

**Recommended Mitigation:**
Create a new permissioned `finalize` function that only allows the withdrawer to call it and that allows the withdrawer to specify the output token. The permissionless version should preserve the original token choice while preventing the griefing attack vector.

---

**[中文版本]**

**描述：**
`coverage` 的提升（如大額 SR Tranche 提現或 JR 存款增加）可被用來攻擊其他用戶的冷卻期提現請求。當 coverage 增加時，之後的提現冷卻期更短。攻擊者可為受害者持續創建多筆較短冷卻期的小額 SR Tranche 提現請求，並設其為接收方，每次 finalize 都會佔用 UnstakeCooldown 槽位，持續填滿受害者隊列直到其原始請求失效（ExternalReceiverRequestLimitReached）。

**影響：**
合法 SR Tranche 提現（如請求 USDe）可被暫時 DoS，受害者必須等攻擊者的請求過期才能繼續完成原始提現。

**修復建議：**
新增有權限 finalize 函數，僅允許請求人自行 finalize 並自選輸出代幣；無權限路徑保存原始代幣選擇，避免遭濫用攻擊。

---

## 8. Investors transferring all their balances among their wallets or self-transferring on the same wallet causes incorrectly decremented investor counters causing DoS for other investors' transfers

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::recordTransfer` adjusts investor counters when a receiver's investor is new or when a sender's investor is transferring their entire balance. However, the function does not check whether the sender and receiver belong to the same investor. When an investor transfers their full balance between their own wallets, or performs a self-transfer, the function incorrectly decrements the investor counter as if that investor is leaving the system entirely, even though they are merely moving tokens between their own addresses.

**Impact:**
Investor counters are decremented when they should not be, leading to DoS for other investors' transfers if the counter underflows or reaches an incorrect value. An additional impact is that investor limits can be bypassed because the counters no longer accurately track the real number of unique investors in the system.

**Recommended Mitigation:**
Add a check in `recordTransfer` to determine whether the sender and receiver belong to the same investor before decrementing the total investor count. If the sender and receiver are the same investor, no counter adjustment should be made.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::recordTransfer` 在接收方為新投資人或發送方全部轉移餘額時調整投資人計數器，但未檢查發送方和接收方是否同為一投資人。若投資人在自有錢包間全部轉移或自轉，會錯誤遞減計數，實際上該投資人未離開系統。

**影響：**
投資人計數可能被錯誤遞減，造成其他人轉賬 DoS，另因計數錯誤可繞過投資人數上限。

**修復建議：**
在 `recordTransfer` 增加同投資人檢查，若雙方同屬一投資人則不調整計數。

---

## 9. Lack of Limits and Delay in Forced Withdrawal Parameter Updates

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `InclusionQueue` contract's `setAmount` function allows the owner to update `minWithdrawAmount` and `feeAmount` without enforcing any upper bounds on either parameter. Additionally, changes take effect immediately upon execution without any delay or timelock. This creates two risks: first, setting excessively high values can prevent withdrawals of smaller deposits or block all withdrawals entirely; second, immediate application enables front-running scenarios where withdrawal requests submitted with one fee expectation are executed under a newly updated (and potentially much higher) fee amount.

**Impact:**
The owner can set `feeAmount` and `minWithdrawAmount` to arbitrarily large values, making it economically infeasible for users to submit forced withdrawal requests. Immediate parameter changes also allow front-running that results in users paying higher fees than expected or having their requests rejected by newly enforced minimum thresholds.

**Recommended Mitigation:**
Enforce reasonable upper bounds for `feeAmount` and `minWithdrawAmount`, and introduce a timelock or delay mechanism for parameter updates to improve predictability and reduce front-running risk.

---

**[中文版本]**

**描述：**
`InclusionQueue` 合約中的 `setAmount` 函數允許所有人無上限設定 `minWithdrawAmount` 及 `feeAmount`，且新值立即生效無延遲或時鎖。兩大風險：一、可將數值設過高完全阻止小額提現或封禁所有提款；二、即時生效造成搶跑，申請時與兌現時費率差異極大。

**影響：**
合約所有者可以隨意設定 `feeAmount` 及 `minWithdrawAmount`，讓強制提現申請在經濟上無法實現。參數即時變更還可能導致使用者支付超預期手續費或因新門檻被拒。

**修復建議：**
對 `feeAmount` 及 `minWithdrawAmount` 設定合理上限，並新增參數時鎖/延遲機制以減少搶跑風險並提升預測性。
