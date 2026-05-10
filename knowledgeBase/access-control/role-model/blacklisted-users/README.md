# blacklisted-users (9)

> Issues involving blacklisted users bypassing restrictions and nonce/signature weaknesses.

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

## 3. Blacklisted Users Can Claim Withdrawn Assets After the Cooldown Period

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

## 4. ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens Returns Positive Token Amount for Blacklisted Users

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

## 5. Remove Unused ExecutePreApprovedTransaction::nonce

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

## 6. Shared Proof Replay-Prevention State Across Multiple Uncoordinated Entry Points Causes Proof Submission Failure

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

## 7. Token Name Update Breaks EIP-712 Domain Separator for Permit Functionality

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

## 8. Transport-Layer Nonce Poisoning Causes Permanent Session Denial of Service

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

## 9. ownerSetVotingPowerExcludedStatus() Applies onlyOwner Modifier Twice

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
