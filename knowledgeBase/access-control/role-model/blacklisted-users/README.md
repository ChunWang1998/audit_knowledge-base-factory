# blacklisted-users (16)

> Issues involving blacklisted users bypassing restrictions, nonce/signature weaknesses, and excessive admin control over user funds.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Lack of Access Control Enabling Unauthorized Credential Issuance and Revocation

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**
The `DIDContract` is intended to manage decentralized identity documents and to issue two types of credentials: simple credentials and Soulbound Token (SBT) credentials. In the current implementation, the core functions that control this lifecycle — `issueCredential()`, `issueSBTCredential()`, and `revokeSBTCredential()` — are exposed without any meaningful access control. Any arbitrary address can act as an issuer or revoker inside the system. The `issueCredential()` function allows arbitrary callers to create unlimited credentials for any subject due to the absence of an issuer check. A similar issue exists in `issueSBTCredential()`: although the underlying `SoulboundCredential` contract enforces an authorized-issuer rule on `mintCredential()`, the wrapper function in `DIDContract` performs no access validation, effectively bypassing the expected authorization model. Revocation suffers from the same problem — `revokeSBTCredential()` can be triggered by any address, enabling unauthorized destruction of SBTs.

**Impact:**
Without proper access control, the entire trust model of the credential system collapses. Fake or misleading credentials can be issued freely by any attacker. Legitimate SBTs belonging to users can be revoked without authorization. User credential histories can be manipulated arbitrarily. The system becomes unreliable for verification or reputation purposes, which restricts protocol functionality and destroys user trust.

**Recommended Mitigation:**
Implement an `authorizedIssuers` mapping and a corresponding admin-controlled setter. Add an `onlyAuthorizedIssuer()` modifier and apply it to `issueCredential()`, `issueSBTCredential()`, and `revokeSBTCredential()`, ensuring only explicitly approved addresses may perform these sensitive operations.

---

**[中文版本]**

**描述：**
`DIDContract` 用於管理去中心化身份文件，並發行兩種憑證：普通憑證和靈魂綁定代幣（SBT）憑證。當前實作中，控制憑證生命週期的核心函數——`issueCredential()`、`issueSBTCredential()` 和 `revokeSBTCredential()`——完全沒有任何訪問控制。任意地址均可充當發行者或撤銷者。`issueCredential()` 因缺乏發行者檢查，允許任意調用者為任何主體創建無限憑證。`issueSBTCredential()` 雖然底層 `SoulboundCredential` 合約對 `mintCredential()` 進行了授權發行者限制，但 `DIDContract` 的封裝函數未進行任何訪問驗證，有效繞過了預期的授權模型。撤銷操作同樣存在問題，任何地址均可調用 `revokeSBTCredential()`。

**影響：**
缺乏訪問控制導致整個憑證系統的信任模型崩潰。攻擊者可任意發行虛假憑證，未授權撤銷合法用戶的 SBT，隨意篡改用戶的憑證歷史記錄，使系統失去驗證和聲譽管理的可靠性。

**修復建議：**
實作 `authorizedIssuers` 映射及相應的管理員控制設置函數，添加 `onlyAuthorizedIssuer()` 修飾符，並應用於 `issueCredential()`、`issueSBTCredential()` 和 `revokeSBTCredential()`，確保只有明確授權的地址才能執行這些敏感操作。

---

## 2. Blacklisted Token Recipient Permanently Blocks FIFO Forced Withdrawals

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The protocol implements a forced withdrawal queue (`InclusionQueue`) as an escape hatch mechanism, allowing users to bypass sequencer control when needed. The `Verifier` contract processes these requests in strict FIFO order, requiring that processing starts from the next unprocessed index and that requests are handled contiguously without skipping. The vulnerability arises from the interaction between this FIFO constraint and USDC/USDT address blacklisting. Token transfers use `safeTransfer`, which reverts when the recipient is blacklisted (e.g. for OFAC sanctions or fraud). If a blacklisted address occupies the front of the queue, the transfer reverts. Because the queue pointer only advances after all transfers succeed, no subsequent requests behind the blacklisted entry can ever be processed. There is no mechanism to skip or mark a failed request. The public `processOverdueQueueItem()` escape-hatch function suffers from the same flaw — it always processes from the current queue pointer and only advances after a successful execution, so a blacklisted address at the front permanently blocks even the emergency escape hatch.

**Impact:**
A single blacklisted address at the front of the forced withdrawal queue permanently prevents all subsequent users from withdrawing funds through the forced withdrawal path. The escape-hatch mechanism itself becomes permanently non-functional, eliminating the only permissionless withdrawal route when the sequencer is unresponsive.

**Recommended Mitigation:**
Wrap transfer calls in try-catch blocks and advance the queue pointer regardless of transfer success. Alternatively, switch to a pull pattern where amounts are credited to a claimable mapping and users retrieve their funds individually rather than the protocol pushing tokens during batch processing.

---

**[中文版本]**

**描述：**
協議實作了強制提款隊列（`InclusionQueue`）作為逃生艙機制，允許用戶在需要時繞過序列器控制。`Verifier` 合約以嚴格的先進先出（FIFO）順序處理這些請求，要求從下一個未處理的索引開始並連續處理，不允許跳過。漏洞源於 FIFO 約束與 USDC/USDT 地址黑名單機制的交互。代幣轉帳使用 `safeTransfer`，當接收方在黑名單上時會回滾。若黑名單地址位於隊列首位，轉帳回滾，由於隊列指針僅在所有轉帳成功後才前進，隊列後面所有請求均被永久阻塞。公開的 `processOverdueQueueItem()` 緊急逃生函數也存在同樣問題。

**影響：**
隊列首位的單個黑名單地址會永久阻止所有後續用戶通過強制提款通道取回資金，在序列器無響應時，唯一的免許可提款路徑也被徹底堵死。

**修復建議：**
在轉帳調用周圍使用 try-catch 塊，無論轉帳成功與否都推進隊列指針；或改用拉取模式，將金額記錄至可領取映射，由用戶自行領取，而非協議在批處理中主動推送代幣。

---

## 3. Admin Void with Arbitrary Payout Ratios Allows Buy Then Redeem Profit

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`PredictionMarketV3ManagerCLOB::adminVoidMarket` lets a resolution admin set custom payout ratios `outcome0Payout` and `outcome1Payout` (which must sum to `1e18`) and immediately marks the market as resolved. Critically, the function does not require the market to be closed first, and it does not tie the void payouts to the current market prices. An admin can therefore void at any time with any valid split — for example 50/50 — regardless of the prevailing yes/no ratio in the order book. If the void payouts differ from the prices at which users can still trade, a user can buy the cheaper outcome and then, after voiding, redeem at the void ratio for a risk-free profit. For instance, if YES trades at 60 and NO at 40, and the admin voids with 50/50, a user can front-run the void call, buy NO at 40, and immediately after voiding receive 50 per share on redemption — gaining 10 per share. The same arbitrage applies in reverse.

**Impact:**
Users can lock in risk-free profit by buying at current market prices and redeeming at admin-chosen void ratios when those ratios differ from market prices. Void resolution creates a step change in share value relative to the last tradable prices, enabling predictable value extraction by anyone who observes the pending void transaction.

**Recommended Mitigation:**
Make voiding a two-step process. In the first step, close the market so that no further buys or sells can occur. In the second step, set the void payouts using the current yes/no ratio from a snapshot of the order book or the last traded prices at close, so that the void ratios align with the market at the time trading stopped, eliminating the buy-then-redeem arbitrage.

---

**[中文版本]**

**描述：**
`PredictionMarketV3ManagerCLOB::adminVoidMarket` 允許解析管理員設置自定義賠付比例（兩者之和必須為 `1e18`）並立即將市場標記為已解析。關鍵問題在於：該函數不要求先關閉市場，也不將作廢賠付與當前市場價格掛鉤。因此管理員可以在任何時間以任意有效分配作廢市場，例如 50/50，無論訂單簿中的當前比例如何。若作廢賠付與可交易價格不同，用戶可以購買較便宜的結果，在作廢後以作廢比例贖回從而獲得無風險利潤。

**影響：**
用戶可通過以當前市場價格買入並以管理員選定的作廢比例贖回來獲得無風險利潤，當兩者存在差異時，作廢解析在相對於最後可交易價格的份額價值上製造了階躍變化。

**修復建議：**
將作廢設計為兩步流程：第一步關閉市場停止交易；第二步設置賠付比例，使用市場關閉時的最後交易價格快照，確保作廢比例與市場最後狀態一致，消除套利空間。

---

## 4. Allow Users to Increment Their Nonce to Void Their Signatures

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
In the current implementation, `NoncesUpgradeable::_useNonce` is declared `internal` and is only called during operations that verify user signatures. There is no publicly accessible function that allows a user to voluntarily increment their own nonce. As a result, a user who has already signed a message has no way to invalidate that signature before it is consumed — they cannot cancel or revoke a pending signed authorization.

**Impact:**
Users are unable to invalidate previous signatures before they are used. If a user changes their mind about an authorized action, or if a signed message is leaked or intercepted, the signature remains valid and cannot be revoked until it is actually consumed by an on-chain call.

**Recommended Mitigation:**
Expose `NoncesUpgradeable::_useNonce` via a `public` wrapper function that allows users to increment their own nonce, invalidating any signatures they have previously issued.

---

**[中文版本]**

**描述：**
當前實作中，`NoncesUpgradeable::_useNonce` 被聲明為 `internal`，僅在驗證用戶簽名的操作期間被調用。沒有公開可訪問的函數允許用戶自願遞增自己的 nonce。因此，已簽名消息的用戶無法在簽名被消耗之前使其失效——他們無法取消或撤銷待處理的簽名授權。

**影響：**
用戶無法在簽名被使用前使先前的簽名失效。若用戶改變主意，或已簽名的消息被洩露或截獲，該簽名在被鏈上調用消耗之前仍然有效。

**修復建議：**
通過公開的包裝函數暴露 `NoncesUpgradeable::_useNonce`，允許用戶遞增自己的 nonce，從而使之前簽發的任何簽名失效。

---

## 5. Authorizable::_verify Should Use EIP-712 Typed Structured Data Hashing

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`Authorizable::_verify` signs ad-hoc payloads that include `chainId`, but the flow is not EIP-712 typed-data compliant. The current implementation mixes domain data (`chainId`) directly into the message payload rather than placing it in the EIP-712 domain separator where it belongs. This non-standard approach limits wallet UX and visibility — users see an opaque byte blob rather than a human-readable structured prompt — and reduces interoperability with tooling and integrations that expect EIP-712 signing flows. The mixing of domain and message data also increases the risk of encoding or packing mistakes and replay bugs across contracts or chains.

**Impact:**
Users are more susceptible to ambiguous and potentially phishable signing prompts. The system has weaker ecosystem compatibility with standard tooling. Future audits and upgrades are harder to reason about. There is a higher risk of encoding or packing mistakes and replay vulnerabilities across contracts or chains when the domain separator is not properly separated from the message struct.

**Recommended Mitigation:**
Adopt EIP-712 and move `chainId` to the domain separator, removing it from the message struct. Define a proper typed struct (`TxAuthData`) with a corresponding `TYPEHASH`, use `_hashTypedDataV4` for digest computation, and validate using `SignatureChecker.isValidSignatureNow`.

---

**[中文版本]**

**描述：**
`Authorizable::_verify` 對包含 `chainId` 的臨時載荷進行簽名，但該流程不符合 EIP-712 類型化數據規範。當前實作將域數據（`chainId`）直接混入消息載荷，而非放入應有的 EIP-712 域分隔符中。這種非標準方式限制了錢包 UX 和可見性，用戶看到的是不透明的字節塊而非人類可讀的結構化提示，降低了與期望 EIP-712 簽名流程的工具和集成的互操作性，同時增加了跨合約或跨鏈的編碼錯誤和重放漏洞風險。

**影響：**
用戶更容易受到模糊甚至釣魚式簽名提示的影響，系統與標準工具的生態兼容性較弱，未來審計和升級更難以推理，跨合約或跨鏈的重放漏洞風險更高。

**修復建議：**
採用 EIP-712 規範，將 `chainId` 移至域分隔符，從消息結構中移除。定義適當的類型化結構體（`TxAuthData`）及相應的 `TYPEHASH`，使用 `_hashTypedDataV4` 計算摘要，並通過 `SignatureChecker.isValidSignatureNow` 進行驗證。

---

## 6. Blacklisted Shares Continue Earning Rewards During Vesting Period

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Tori Finance.txt`

**Description:**
When an admin attempts to burn a blacklisted user's shares via `redistributeLockedAmount(from, address(0))`, the function internally calls `_updateVestingAmount` to finalize the redistribution. However, `_updateVestingAmount` reverts with `StillVesting()` whenever `getUnvestedAmount() > 0` — that is, whenever there is an active vesting period in progress. Because vesting periods can last up to 8 hours, the admin is unable to execute the blacklist enforcement action during that window. The blacklisted user's shares remain intact and continue earning rewards from the vesting schedule for the entire duration of the vesting period before the admin can successfully burn them.

**Impact:**
Blacklisted users whose shares should be seized and redistributed can continue earning protocol rewards for up to 8 hours due to the vesting mechanism blocking the admin action. This undermines the effectiveness of the blacklist enforcement and allows restricted users to extract additional value.

**Recommended Mitigation:**
Modify `redistributeLockedAmount` to handle the vesting case gracefully — for example by allowing the admin to queue the redistribution to execute automatically once the vesting period ends, or by providing a way to force-complete the vesting early in the context of a blacklist enforcement action.

---

**[中文版本]**

**描述：**
當管理員嘗試通過 `redistributeLockedAmount(from, address(0))` 銷毀黑名單用戶的份額時，函數內部調用 `_updateVestingAmount` 完成重新分配。然而，`_updateVestingAmount` 在 `getUnvestedAmount() > 0`（即存在活躍的歸屬期）時會以 `StillVesting()` 錯誤回滾。由於歸屬期可持續長達 8 小時，管理員在此期間無法執行黑名單強制操作。黑名單用戶的份額在整個歸屬期內繼續累積獎勵。

**影響：**
應被沒收和重新分配的黑名單用戶份額，由於歸屬機制阻塞了管理員操作，可繼續在長達 8 小時內賺取協議獎勵，破壞了黑名單執行的有效性。

**修復建議：**
修改 `redistributeLockedAmount` 以優雅地處理歸屬期情況，例如允許管理員將重新分配操作排隊，在歸屬期結束後自動執行，或在黑名單執行場景中提供提前強制完成歸屬的方式。

---

## 7. Blacklisted Users Can Claim Withdrawn Assets After the Cooldown Period

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::_update` uses `notBlacklisted(from)` and `notBlacklisted(to)` modifiers to prevent blacklisted users from performing most actions, including transfers and redemptions. However, `StakingVault::claimWithdraw` does not apply the `notBlacklisted` modifier. As a result, a user who initiates a withdrawal or redemption while not blacklisted, but is subsequently added to the blacklist before the cooldown period expires, can still call `claimWithdraw` once the cooldown period has elapsed and receive their assets. The blacklisting that was intended to freeze the user's access to funds does not apply to the final step of the withdrawal flow.

**Impact:**
Users who are blacklisted after initiating a withdrawal can still successfully retrieve their assets once the cooldown period expires. Blacklisting therefore fails to freeze funds that are already in the withdrawal pipeline, undermining the completeness of the compliance restriction.

**Recommended Mitigation:**
Add at least `notBlacklisted(msg.sender)` to `StakingVault::claimWithdraw`. Additionally consider adding `notBlacklisted(receiver)` to prevent withdrawals to blacklisted destination addresses, though this is less critical since the user can specify an arbitrary receiver address.

---

**[中文版本]**

**描述：**
`StakingVault::_update` 使用 `notBlacklisted(from)` 和 `notBlacklisted(to)` 修飾符防止黑名單用戶執行大多數操作，包括轉帳和贖回。然而，`StakingVault::claimWithdraw` 未應用 `notBlacklisted` 修飾符。因此，在未被列入黑名單時發起提款的用戶，若在冷卻期結束前被加入黑名單，仍可在冷卻期到期後調用 `claimWithdraw` 並取回資產。

**影響：**
在發起提款後被列入黑名單的用戶，仍可在冷卻期結束後成功取回資產，黑名單機制無法凍結已進入提款流程的資金，損害了合規限制的完整性。

**修復建議：**
在 `StakingVault::claimWithdraw` 中至少添加 `notBlacklisted(msg.sender)` 修飾符；同時考慮添加 `notBlacklisted(receiver)` 以防止向黑名單目標地址提款。

---

## 8. ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens Returns Positive Token Amount for Blacklisted Users

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens` is inherited from `ComplianceServiceWhitelisted` and delegates directly to `getLockManager().getTransferableTokens(_who, _time)`. This underlying call returns a positive amount of transferable tokens based purely on lock schedules, without consulting the blacklist. As a result, when this function is called for a blacklisted address, it returns a positive transferable token amount even though the address actually has zero transferable tokens due to being blacklisted. This is misleading because any consuming system that relies on this function to determine how many tokens an address can transfer will receive incorrect data.

**Impact:**
Systems and integrations that query `getComplianceTransferableTokens` for blacklisted addresses will believe those addresses can transfer tokens when in fact they cannot. This incorrect state representation may lead to improper downstream decisions about compliance status and transferability, potentially allowing incorrect transactions to be approved or incorrect reports to be generated.

**Recommended Mitigation:**
Modify `getComplianceTransferableTokens` to first check whether the queried address is blacklisted. If the address is blacklisted, the function should return 0 rather than delegating to the lock manager.

---

**[中文版本]**

**描述：**
`ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens` 繼承自 `ComplianceServiceWhitelisted`，直接委托給 `getLockManager().getTransferableTokens(_who, _time)`。這個底層調用僅根據鎖定計劃返回可轉帳代幣數量，而不查詢黑名單。因此，當對黑名單地址調用此函數時，它返回正數，儘管該地址實際上由於被列入黑名單而具有零可轉帳代幣。任何依賴此函數確定地址可轉帳代幣數量的消費系統都將收到不正確的數據。

**影響：**
查詢黑名單地址的 `getComplianceTransferableTokens` 的系統和集成將錯誤地認為這些地址可以轉帳代幣，可能導致錯誤的合規決策。

**修復建議：**
修改 `getComplianceTransferableTokens`，首先檢查被查詢地址是否在黑名單中。若是，函數應返回 0 而非委托給鎖定管理器。

---

## 9. Excessive Admin Control Over Critical Staking Parameters

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/A Two Tech Limited.txt`

**Description:**
The `ATWOStaking` contract grants the admin unrestricted, immediate control over multiple critical parameters that directly affect user financial outcomes and contract functionality. These parameters can be changed at any time without timelocks, user consent, or validation constraints, creating significant trust risks and potential for abuse. Specifically: the stable token can be swapped at any moment via `setStableToken`, which invalidates existing price configurations and can create a decimal mismatch of up to 10^12x if switching between USDC (6 decimals) and DAI (18 decimals); the membership price can be set to any value including zero or astronomically high amounts via `setMembershipPriceStable` with no bounds; the team treasury can be redirected to any address via `setTeamTreasury`, diverting all future membership fees; and the NFT contract can be swapped via `setMemberNft`, making previous memberships unrecognizable and breaking the staking function that checks `hasMembership()`.

**Impact:**
Admins can exploit these unconstrained controls to manipulate prices to favor specific users, redirect fees to their personal wallets, render existing memberships worthless, or exploit token decimal mismatches to charge wrong amounts. All of these actions can be executed immediately without any advance notice or time window for users to react.

**Recommended Mitigation:**
Implement governance controls, timelocks, and validation constraints for all critical parameter setters. Add minimum/maximum bounds for prices, require multi-signature approval for treasury changes, and introduce a minimum timelock delay for parameter updates so that users have sufficient warning before sensitive changes take effect.

---

**[中文版本]**

**描述：**
`ATWOStaking` 合約授予管理員對多個關鍵參數的無限制即時控制權，這些參數直接影響用戶的財務結果和合約功能，可以在沒有時間鎖、用戶同意或驗證約束的情況下隨時更改。具體包括：通過 `setStableToken` 隨時更換穩定代幣（可造成最高 10^12 倍的小數點精度差異）；通過 `setMembershipPriceStable` 無限制地設置會員價格；通過 `setTeamTreasury` 將所有未來費用轉移至任意地址；通過 `setMemberNft` 更換 NFT 合約使現有會員資格失效。

**影響：**
管理員可利用這些無約束的控制權操縱價格、轉移費用至個人錢包、使現有會員資格失效，或利用代幣小數點不匹配收取錯誤金額，所有這些操作均可立即執行，無任何提前通知。

**修復建議：**
為所有關鍵參數設置函數實作治理控制、時間鎖和驗證約束；為價格添加最小值/最大值邊界；對財庫變更要求多重簽名審批；引入最小時間鎖延遲，讓用戶在敏感變更生效前有充足的反應時間。

---

## 10. Inability for Users to Permissionlessly Stake and Earn Yield

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
The stated protocol intention is that users should be able to permissionlessly buy hBTC from a decentralized exchange and then immediately stake it in `StakingVault` to earn yield. However, the current implementation uses `onlyWhitelisted` modifiers on many core functions including `deposit`, `mint`, `redeem`, and `withdraw`. This means any user who buys hBTC on a DEX without going through the whitelist process is unable to stake their tokens and earn yield. The only workaround is for the admin to call `setGlobalWhitelist(true)`, which globally disables the whitelist enforcement — effectively negating the entire compliance framework rather than enabling permissionless access in a targeted way.

**Impact:**
Users who permissionlessly acquire hBTC through a decentralized exchange are blocked from the core protocol function of staking to earn yield. The existing design requires every user to be individually whitelisted, creating a permissioned experience that contradicts the protocol's stated permissionless design intent and restricts user access.

**Recommended Mitigation:**
Remove the whitelist functionality from `StakingVault` entirely while retaining the blacklist functionality. This allows permissionless participation in staking and earning yield, while still enabling the protocol to restrict specific addresses that have been explicitly identified for exclusion.

---

**[中文版本]**

**描述：**
協議的既定意圖是用戶應能夠免許可地從去中心化交易所購買 hBTC，然後立即在 `StakingVault` 中質押以賺取收益。然而，當前實作在許多核心函數（包括 `deposit`、`mint`、`redeem` 和 `withdraw`）上使用了 `onlyWhitelisted` 修飾符。這意味著通過 DEX 購買 hBTC 而未進行白名單認證的任何用戶都無法質押代幣並賺取收益。唯一的解決方法是管理員調用 `setGlobalWhitelist(true)`，這會全局禁用白名單執行，實際上否定了整個合規框架。

**影響：**
通過去中心化交易所免許可獲得 hBTC 的用戶被阻止使用質押賺取收益的核心協議功能，現有設計要求每個用戶單獨加入白名單，與協議聲明的免許可設計意圖相悖。

**修復建議：**
完全從 `StakingVault` 中移除白名單功能，同時保留黑名單功能。這允許用戶免許可參與質押和賺取收益，同時仍能限制已被明確識別排除的特定地址。

---

## 11. Prevent Accidental Ownership and Admin Renouncement

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
The `TokenAirdrop` contract inherits `renounceOwnership()` from OpenZeppelin's `Ownable`. This function allows the current owner to call it and permanently remove themselves as owner, leaving the contract in a permanently ownerless state. Similarly, inherited admin functionality allows the last admin to remove themselves. If this happens — whether accidentally or maliciously — all owner-gated and admin-gated functions become permanently inaccessible. There is no recovery mechanism once the contract is in this state.

**Impact:**
If the owner or admin calls `renounceOwnership()` or its equivalent, all critical admin functions such as configuration updates, emergency controls, and privileged operations become permanently blocked. This constitutes an irreversible self-inflicted denial of service on all governance and administrative capabilities.

**Recommended Mitigation:**
Override `renounceOwnership()` in `TokenAirdrop` to always revert, preventing the possibility of an accidentally or intentionally ownerless contract. Additionally consider using `Ownable2Step` consistently across all contracts to prevent accidental ownership loss through a single-step transfer.

---

**[中文版本]**

**描述：**
`TokenAirdrop` 合約從 OpenZeppelin 的 `Ownable` 繼承了 `renounceOwnership()` 函數。該函數允許當前所有者調用它並永久移除自己的所有者身份，使合約處於永久無所有者狀態。同樣，繼承的管理員功能允許最後一個管理員移除自己。一旦發生這種情況——無論是意外還是惡意——所有所有者控制和管理員控制的函數都將永久無法訪問，且沒有恢復機制。

**影響：**
若所有者或管理員調用 `renounceOwnership()` 或其等價物，所有關鍵管理函數（如配置更新、緊急控制和特權操作）都將永久被阻塞，這構成對所有治理和管理能力不可逆的自我造成的拒絕服務。

**修復建議：**
在 `TokenAirdrop` 中覆蓋 `renounceOwnership()` 使其始終回滾，防止合約意外或故意進入無所有者狀態；同時考慮在所有合約中統一使用 `Ownable2Step`，通過兩步轉移機制防止意外失去所有者身份。

---

## 12. Remove Unused ExecutePreApprovedTransaction::nonce

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
The `ExecutePreApprovedTransaction` struct contains a `nonce` field that is never actually used in the validation logic. `GlobalRegistryService::hashTx` always reads the current nonce directly from storage via `noncePerInvestor[txData.senderInvestor]` when constructing the signature hash. The caller must use the current on-chain nonce in their signed message — otherwise signature validation fails. Upon successful validation, `executePreApprovedTransaction` increments the stored nonce so it can never be reused. The struct's `nonce` field plays no part in any of these steps; it is present in the struct but never referenced during execution.

**Impact:**
The unused `nonce` field creates confusion about the actual nonce validation mechanism. Developers and integrators reading the struct definition may incorrectly believe they need to supply a specific nonce value in the struct, potentially leading to incorrect transaction construction or a misunderstanding of the replay-protection model.

**Recommended Mitigation:**
Remove the `nonce` field from the `ExecutePreApprovedTransaction` struct, since the actual nonce is always sourced from on-chain storage rather than from the transaction data itself.

---

**[中文版本]**

**描述：**
`ExecutePreApprovedTransaction` 結構體包含一個 `nonce` 字段，但在驗證邏輯中從未被實際使用。`GlobalRegistryService::hashTx` 在構建簽名哈希時始終通過 `noncePerInvestor[txData.senderInvestor]` 從存儲中直接讀取當前 nonce。調用者必須在其簽名消息中使用當前鏈上 nonce，否則簽名驗證失敗。驗證成功後，`executePreApprovedTransaction` 遞增存儲的 nonce 使其無法被重用。結構體的 `nonce` 字段在這些步驟中均不起任何作用。

**影響：**
未使用的 `nonce` 字段造成對實際 nonce 驗證機制的混淆，開發者和集成者可能錯誤地認為需要在結構體中提供特定的 nonce 值，導致錯誤的交易構建或對重放保護模型的誤解。

**修復建議：**
從 `ExecutePreApprovedTransaction` 結構體中移除 `nonce` 字段，因為實際的 nonce 始終來自鏈上存儲而非交易數據本身。

---

## 13. Shared Proof Replay-Prevention State Across Multiple Uncoordinated Entry Points Causes Proof Submission Failure

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The `ProofSystemUpgradeable` contract exposes multiple functions that all write to the same `verifiedProofs` mapping: `verifyAndMarkComplete` (no access control), `verifyBatch` (no access control), and `recordVerifiedProof` (restricted to owner or authorized callers). The internal `_verifyHostSignature` function, used by all verification paths, rejects any proof whose hash is already in this mapping. `JobMarketplaceWithModelsUpgradeable::submitProofOfWork` depends on `verifyAndMarkComplete` returning `true`. Since `verifyAndMarkComplete` and `verifyBatch` are publicly callable by anyone, an attacker who observes a host's pending `submitProofOfWork` transaction in the mempool can front-run it by calling `verifyAndMarkComplete` directly with the extracted proof data. This marks the `proofHash` as consumed before the host's transaction executes. When the host's transaction runs, `verifyAndMarkComplete` returns `false` because the hash is already marked, and `submitProofOfWork` reverts. The host receives no payment for the computational work performed. The only option is to generate an entirely new inference output, which is immediately vulnerable to the same attack.

**Impact:**
Hosts who have legitimately performed AI inference work are permanently unable to submit their proofs and claim payment whenever an attacker front-runs their submission. Sessions time out with `tokensUsed = 0` for the blocked proofs, resulting in irrecoverable economic loss for the host (wasted GPU resources). Attackers can repeat this pattern indefinitely at low cost, causing systematic disruption to the payment mechanism.

**Recommended Mitigation:**
Restrict `verifyAndMarkComplete` and `verifyBatch` to authorized callers only, consistent with `recordVerifiedProof`. Only the `JobMarketplace` contract or other explicitly authorized contracts should be permitted to mark proof hashes as consumed.

---

**[中文版本]**

**描述：**
`ProofSystemUpgradeable` 合約暴露了多個函數，都對同一個 `verifiedProofs` 映射進行寫操作：`verifyAndMarkComplete`（無訪問控制）、`verifyBatch`（無訪問控制）和 `recordVerifiedProof`（限制為所有者或授權調用者）。所有驗證路徑使用的內部 `_verifyHostSignature` 函數會拒絕哈希已在映射中的任何證明。攻擊者可從內存池中觀察主機待處理的 `submitProofOfWork` 交易，通過直接調用 `verifyAndMarkComplete` 搶先執行，將 `proofHash` 標記為已消耗，導致主機的合法提交回滾並無法收到報酬。

**影響：**
合法執行了 AI 推理工作的主機，每當攻擊者搶先執行其提交時都將永久無法提交證明和索取報酬，造成不可恢復的 GPU 資源經濟損失。攻擊者可以低成本無限重複此攻擊模式。

**修復建議：**
將 `verifyAndMarkComplete` 和 `verifyBatch` 限制為僅授權調用者，與 `recordVerifiedProof` 保持一致，只允許 `JobMarketplace` 合約或其他明確授權的合約將證明哈希標記為已消耗。

---

## 14. Token Name Update Breaks EIP-712 Domain Separator for Permit Functionality

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
The EIP-712 domain separator is initialized once during contract deployment in `__ERC20PermitMixin_init()` with the initial token name, using `__EIP712_init(name_, "1")`. However, `StandardToken` allows the Master role to update the token name via `updateNameAndSymbol`. When this happens, the EIP-712 domain separator is not recalculated — it retains the original deployment-time name. This creates a persistent mismatch: wallets and dApps that fetch the current `token.name()` to construct permit signatures will use the new name, while the contract validates signatures against the domain separator built with the old name. This mismatch causes 100% of newly generated permit signatures to fail with an invalid signature error.

**Impact:**
After any token name change, all newly generated permit signatures fail validation. Existing permits signed before the name change continue to work, creating a confusing split-state. All dApps that fetch the current token name to generate permit signatures automatically break after a name update. There is no easy recovery path — fixing this requires either a contract upgrade or instructing all users and integrations to use the deprecated original name.

**Recommended Mitigation:**
Update the EIP-712 domain separator whenever `updateNameAndSymbol` is called. Since OpenZeppelin's EIP-712 implementation caches the domain separator, consider switching to a dynamic domain separator implementation that recomputes the separator on every call using the current token name.

---

**[中文版本]**

**描述：**
EIP-712 域分隔符在合約部署期間通過 `__ERC20PermitMixin_init()` 使用初始代幣名稱一次性初始化。然而，`StandardToken` 允許 Master 角色通過 `updateNameAndSymbol` 更新代幣名稱。發生這種情況時，EIP-712 域分隔符不會重新計算，仍保留原始部署時的名稱。這造成持久不匹配：獲取當前 `token.name()` 構建許可簽名的錢包和 dApp 將使用新名稱，而合約使用基於舊名稱構建的域分隔符驗證簽名，導致所有新生成的許可簽名均驗證失敗。

**影響：**
代幣名稱更改後，所有新生成的許可簽名均驗證失敗；更改前簽署的現有許可繼續有效，造成令人困惑的分裂狀態；所有自動獲取當前代幣名稱生成許可簽名的 dApp 在名稱更新後立即失效。

**修復建議：**
每次調用 `updateNameAndSymbol` 時更新 EIP-712 域分隔符；考慮切換到動態域分隔符實作，每次調用時使用當前代幣名稱重新計算分隔符。

---

## 15. Transport-Layer Nonce Poisoning Causes Permanent Session Denial of Service

**Severity:** 🟡 Medium
**Source:** `cyfrin/connect.md`

**Description:**
The WebSocket transport layer wraps every E2E-encrypted payload in a plaintext `TransportMessage` envelope containing a `clientId` (UUID) and a monotonically-increasing nonce. The deduplication logic on the receiving side accepts any message whose nonce exceeds the highest previously seen nonce for a given `clientId`, then persists the new nonce to storage before the encrypted payload is validated. The Centrifugo relay server allows anonymous connections with no authentication (`allow_anonymous_connect_without_token: true`), meaning any attacker can subscribe to a known channel and read the plaintext `clientId` and `nonce` from any published message. The attacker then publishes a single spoofed message with the victim's `clientId` and `nonce` set to `Number.MAX_SAFE_INTEGER` (9007199254740991). This permanently advances the stored nonce so that all subsequent legitimate messages — which have lower, sequential nonces — are silently dropped as "duplicates." The poisoned nonce is persisted to MMKV (persistent key-value storage), so it survives app restarts and device reboots. The victim sees no error as messages are silently dropped.

**Impact:**
On the handshake channel, an attacker who observes the deeplink URL can subscribe, extract the `clientId` from a published message, and inject a nonce-poisoning message to permanently prevent dApp-wallet communication before any session is established. On a session channel, an attacker who discovers the session UUID can permanently kill an active 30-day session. Neither side can communicate until one creates a completely new session. The DoS is permanent and persists across app restarts.

**Recommended Mitigation:**
Only persist the nonce after the E2E-encrypted payload has been successfully validated and decrypted. Additionally require authenticated Centrifugo connections to prevent anonymous attackers from publishing to channels; authentication should be enforced at the relay server level.

---

**[中文版本]**

**描述：**
WebSocket 傳輸層將每個端到端加密的載荷包裝在一個包含 `clientId`（UUID）和單調遞增 nonce 的明文 `TransportMessage` 信封中。接收端的去重邏輯接受任何 nonce 超過給定 `clientId` 最近看到的最高 nonce 的消息，並在驗證加密載荷之前將新 nonce 持久化到存儲。Centrifugo 中繼服務器允許匿名連接（`allow_anonymous_connect_without_token: true`），任何攻擊者都可以訂閱已知頻道並從任何發布的消息中讀取明文 `clientId` 和 `nonce`。攻擊者發布一條受害者 `clientId` 的消息，將 nonce 設置為 `Number.MAX_SAFE_INTEGER`，永久推進存儲的 nonce，使所有後續合法消息被靜默丟棄。毒化的 nonce 持久化到 MMKV，在應用重啟和設備重啟後仍然存在。

**影響：**
攻擊者可永久阻止 dApp-錢包通信（握手頻道攻擊），或殺死活躍的 30 天會話（會話頻道攻擊），且 DoS 在應用重啟後持續存在，受害者不會看到任何錯誤提示。

**修復建議：**
僅在端到端加密載荷成功驗證和解密後才持久化 nonce；同時在 Centrifugo 中繼服務器層面要求認證連接，防止匿名攻擊者向頻道發布消息。

---

## 16. ownerSetVotingPowerExcludedStatus() Applies onlyOwner Modifier Twice

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
In the WLF V2 contract, the function `ownerSetVotingPowerExcludedStatus()` applies the `onlyOwner` modifier twice in the same call flow: once on the external function `ownerSetVotingPowerExcludedStatus()` itself, and again on the internal function `_ownerSetVotingPowerExcludedStatus()` that it delegates to. Since the external function has already verified that `msg.sender` is the owner before calling the internal function, the second `onlyOwner` check in `_ownerSetVotingPowerExcludedStatus()` is entirely redundant and has no additional security benefit.

**Impact:**
The redundant modifier wastes gas on every call to `ownerSetVotingPowerExcludedStatus()` by performing the `Ownable` check twice. It also makes the code harder to reason about and maintain, potentially creating confusion for future developers about whether the internal function is intended to be called from non-owner contexts.

**Recommended Mitigation:**
Remove the `onlyOwner` modifier from `_ownerSetVotingPowerExcludedStatus()`. The access control is already enforced by the external wrapper function, so the internal function does not need to re-verify it.

---

**[中文版本]**

**描述：**
在 WLF V2 合約中，函數 `ownerSetVotingPowerExcludedStatus()` 在同一調用流程中重複應用了兩次 `onlyOwner` 修飾符：一次在外部函數 `ownerSetVotingPowerExcludedStatus()` 本身，另一次在其委托的內部函數 `_ownerSetVotingPowerExcludedStatus()` 上。由於外部函數在調用內部函數之前已經驗證了 `msg.sender` 是所有者，內部函數中的第二個 `onlyOwner` 檢查完全多餘，沒有任何額外的安全意義。

**影響：**
冗餘的修飾符在每次調用 `ownerSetVotingPowerExcludedStatus()` 時都通過執行兩次 `Ownable` 檢查浪費 gas，同時也使代碼更難以推理和維護，可能對未來的開發者造成混淆。

**修復建議：**
從 `_ownerSetVotingPowerExcludedStatus()` 中移除 `onlyOwner` 修飾符，訪問控制已由外部包裝函數強制執行，內部函數無需重新驗證。
