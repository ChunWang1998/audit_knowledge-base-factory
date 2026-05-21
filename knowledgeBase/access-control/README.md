# access-control (50)

> Issues where privilege checks, elevated roles, signature/permit enforcement, or `msg.sender` validation were bypassed or misconfigured.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

## Subcategories

- [instead-sender](./instead-sender/) (16) — incorrect `msg.sender` vs delegated caller checks, caller permission griefing
- [manager-vault](./manager-vault/) (9) — vault/fee manager role misconfiguration enabling withdrawal griefing
- [support-vault](./support-vault/) (18) — support/vault role permission issues enabling withdrawal griefing
- `role-model` (7) — see sections below

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

### validation-access (2)

> Issues where access control checks were missing, commented out, or improperly validated.

---

## 1. Missing Nonce Validation in Signature Verification Allows Transaction Replay Attacks

**Severity:** 🔴 Critical
**Source:** `cyfrin/bridge.md`

**Description:**
The `SecuritizeOnRamp::executePreApprovedTransaction` function fails to validate that the nonce provided in the transaction data (`txData.nonce`) matches the expected nonce stored on-chain for the investor (`noncePerInvestor[txData.senderInvestor]`) before executing the transaction. While the function correctly verifies the EIP-712 signature — which includes the nonce as part of the signed message — it never checks that the nonce embedded in the transaction data equals the current on-chain nonce. The function only increments the stored nonce after signature verification succeeds. This means any previously valid signed transaction retains a valid signature for the old nonce value, but because the contract does not reject transactions with a stale nonce, the same signed transaction can be replayed with its original nonce value any number of times.

**Impact:**
An attacker can replay any previously valid EIP-712 signed transaction to execute duplicate subscription operations, leading to double (or multiple) unintended token swaps and accounting failures. Each replay drains the investor's approved USDC and issues additional DS tokens without the investor's consent for subsequent transactions.

**Recommended Mitigation:**
Add an explicit nonce validation check at the beginning of `executePreApprovedTransaction` that reverts if `txData.nonce != noncePerInvestor[txData.senderInvestor]`. This ensures that only the signature constructed with the current on-chain nonce can be executed, and once consumed the nonce increment prevents reuse.

---

**[中文版本]**

**描述：**
`SecuritizeOnRamp::executePreApprovedTransaction` 函數在執行交易前未驗證交易數據中提供的 nonce（`txData.nonce`）是否與投資者的鏈上存儲 nonce（`noncePerInvestor[txData.senderInvestor]`）相匹配。雖然函數正確驗證了包含 nonce 的 EIP-712 簽名，但從未檢查交易數據中嵌入的 nonce 是否等於當前鏈上 nonce。函數僅在簽名驗證成功後才遞增存儲的 nonce，這意味著任何舊的有效簽名仍可用原始 nonce 值被無限次重放。

**影響：**
攻擊者可重放任何先前有效的 EIP-712 簽名交易，執行重複的認購操作，導致雙重或多重意外的代幣兌換和賬目混亂，在投資者不知情的情況下耗盡其授權的 USDC 並發行額外的 DS 代幣。

**修復建議：**
在 `executePreApprovedTransaction` 開頭添加顯式的 nonce 驗證檢查，若 `txData.nonce != noncePerInvestor[txData.senderInvestor]` 則回滾，確保只有使用當前鏈上 nonce 構建的簽名才能被執行。

---

## 2. Incomplete Blacklist Enforcement in transferFrom Allows Blacklisted Callers to Bypass Transfer Restrictions

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
In KnoxNet, blacklist enforcement is applied only to the `sender` parameter and does not cover either `msg.sender` (the spender) or the `recipient`. The `transferFrom` function forwards execution to `_transferFrom`, which applies blacklist checks through `_enforceTxLimit`. However, `_enforceTxLimit` only checks `require(blacklist[sender] == 0, "Wallet blacklisted!")` — it checks the token owner from whose balance the transfer is drawn, but not the address initiating the call. In a `transferFrom` scenario, `msg.sender` is the approved spender and may be a completely different address from `sender`. A blacklisted address can therefore obtain an allowance from a non-blacklisted wallet and call `transferFrom` to move that wallet's tokens, completely circumventing the blacklist. Additionally, since `recipient` is not checked either, blacklisted addresses may still receive tokens as the destination of any transfer.

**Impact:**
Blacklisted addresses remain fully able to operate through the allowance flow and are not effectively excluded from token activity. The anti-bot and administrative restriction mechanism can be bypassed in practice by any blacklisted address that can obtain a token approval. Blacklisted recipients may also continue accumulating tokens.

**Recommended Mitigation:**
Extend the blacklist validation in `_enforceTxLimit` to cover all three relevant actors: `sender`, `recipient`, and `msg.sender`. None of these three addresses should be permitted to participate in a transfer if any of them is blacklisted.

---

**[中文版本]**

**描述：**
在 KnoxNet 中，黑名單執行僅應用於 `sender` 參數，未涵蓋 `msg.sender`（支出者）或 `recipient`。`transferFrom` 函數通過 `_enforceTxLimit` 應用黑名單檢查，但 `_enforceTxLimit` 僅檢查 `require(blacklist[sender] == 0, "Wallet blacklisted!")`——只檢查代幣所有者，不檢查發起調用的地址。在 `transferFrom` 場景中，`msg.sender` 是授權的支出者，可能與 `sender` 完全不同。黑名單地址可以從未列入黑名單的錢包獲得授權，通過 `transferFrom` 轉移該錢包的代幣，完全繞過黑名單。此外，由於 `recipient` 也未被檢查，黑名單地址仍可作為轉帳目標繼續累積代幣。

**影響：**
黑名單地址通過授權流程仍可完全操作代幣活動，使反機器人和管理限制機制形同虛設，黑名單接收者也可繼續累積代幣。

**修復建議：**
將 `_enforceTxLimit` 中的黑名單驗證擴展至涵蓋所有三個相關參與者：`sender`、`recipient` 和 `msg.sender`，任一地址在黑名單中均應禁止參與轉帳。

---

### replay-protocol (3)

> Issues involving cross-chain or cross-session signature replay and hook/fee automation failures.

---

## 1. After the Upgrade Permissionless Attacker Can Fully Drain the L1 TokenBridge of ERC20 Tokens Currently Valued Around $29M USD

**Severity:** 🔴 Critical
**Source:** `cyfrin/upgrade.md`

**Description:**
A careful analysis of the storage layouts of both the old and new `TokenBridge` contracts reveals a critical slot displacement introduced during a dependency change. Slot 0, which previously held the initialization slot, becomes a gap in the new layout. Slot 50, which was previously a gap, becomes the new initialization slot. This shift means that immediately after the upgrade, the on-chain data at slot 0 (set to 1 by the previous `_initialized` state) no longer represents the initialization flag. The new contract therefore reads slot 50 as its initialization status, which contains zero — meaning the contract believes it has never been initialized. This allows any permissionless attacker to call `TokenBridge::initialize` on the upgraded contract and set themselves as the default admin. The attacker can then grant themselves the `SET_MESSAGE_SERVICE_ROLE`, deploy a malicious messaging service contract that spoofs the `remoteSender` check, set it via `setMessageService`, and call its drain function to invoke `completeBridging` for every token locked in the L1 `TokenBridge`, transferring all locked assets to themselves. This entire attack can be executed atomically via a private mempool such as Flashbots, making it unstoppable.

**Impact:**
Immediately following the upgrade, an attacker can atomically drain the entire L1 `TokenBridge` contract of all locked ERC20 tokens, which at the time of the audit were valued at approximately $29M USD. The attack is fully permissionless, requires no privileged access, and can be executed in a single transaction with no possibility of front-running defense.

**Recommended Mitigation:**
`TokenBridgeBase` should inherit from `Initializable` to ensure the initialization slot is consistently positioned. The bug was introduced when `ReentrancyGuardUpgradeable` (which inherited `Initializable`) was replaced with a custom `TransientStorageReentrancyGuardUpgradeable` that does not inherit `Initializable`, inadvertently shifting the storage layout. Restoring the `Initializable` inheritance ensures the slot is preserved at slot 0.

---

**[中文版本]**

**描述：**
對新舊 `TokenBridge` 合約存儲佈局的仔細分析揭示了依賴項變更引入的關鍵插槽位移：原來位於插槽 0 的初始化插槽在新佈局中變成了間隙，而原來的間隙插槽 50 成為了新的初始化插槽。這意味著升級後，插槽 0 處的鏈上數據（由先前 `_initialized` 狀態設置為 1）不再代表初始化標誌，新合約將插槽 50 讀取為其初始化狀態（值為零），認為自己從未被初始化。這允許任何無許可的攻擊者在升級後的合約上調用 `TokenBridge::initialize`，將自己設置為默認管理員，進而授予自己相關角色，部署惡意消息服務合約，並通過 `completeBridging` 排空 L1 `TokenBridge` 中鎖定的所有代幣。

**影響：**
升級後，攻擊者可原子性地排空整個 L1 `TokenBridge` 合約中所有鎖定的 ERC20 代幣，審計時價值約 2900 萬美元。攻擊完全無許可，可在單筆交易中執行，且可通過私有內存池實現，無法防範。

**修復建議：**
`TokenBridgeBase` 應繼承 `Initializable` 以確保初始化插槽位置一致。該漏洞是在將繼承自 `Initializable` 的 `ReentrancyGuardUpgradeable` 替換為不繼承 `Initializable` 的自定義重入鎖時無意中引入的，恢復 `Initializable` 繼承可確保插槽保持在插槽 0。

---

## 2. LivenessRecovery::setLivenessRecoveryOperator Will Emit Misleading Event When Role Is Not Granted

**Severity:** 🔴 Critical
**Source:** `cyfrin/upgrade.md`

**Description:**
`LivenessRecovery::setLivenessRecoveryOperator` can be called multiple times as long as its first two preconditions are satisfied. When the function calls `_grantRole(OPERATOR_ROLE, livenessRecoveryOperatorAddress)`, OpenZeppelin's `AccessControlUpgradeable::_grantRole` returns `false` if the role has already been granted to that address (i.e., the grantee already holds the role). The function does not check the boolean return value of `_grantRole`. As a result, when `setLivenessRecoveryOperator` is called for an address that already holds `OPERATOR_ROLE`, the `_grantRole` call is a no-op — no state change occurs — but the `LivenessRecoveryOperatorRoleGranted` event is still emitted unconditionally, falsely indicating that the role was freshly granted. This misleads off-chain monitoring systems and audit trails into believing a new role grant occurred when none did.

**Impact:**
Off-chain systems, indexers, and security monitoring tools that watch for `LivenessRecoveryOperatorRoleGranted` events to track role assignments will receive false signals. This can obscure the true history of role grants, complicate incident response, and undermine the integrity of audit logs. In a security-critical context where liveness recovery operations are being monitored, misleading events introduce material operational risk.

**Recommended Mitigation:**
Condition the event emission on the boolean return value of `_grantRole`: only emit the `LivenessRecoveryOperatorRoleGranted` event if `_grantRole` returned `true`, indicating the role was actually newly granted.

---

**[中文版本]**

**描述：**
`LivenessRecovery::setLivenessRecoveryOperator` 可在滿足前兩個前提條件的情況下多次調用。當函數調用 `_grantRole(OPERATOR_ROLE, livenessRecoveryOperatorAddress)` 時，若該地址已持有該角色，OpenZeppelin 的 `_grantRole` 返回 `false`（表示未發生任何狀態更改）。然而，函數未檢查 `_grantRole` 的布爾返回值，導致在角色已被授予的情況下，`LivenessRecoveryOperatorRoleGranted` 事件仍被無條件觸發，虛假表明角色剛被授予。

**影響：**
監控 `LivenessRecoveryOperatorRoleGranted` 事件以跟蹤角色分配的鏈下系統、索引器和安全監控工具將收到虛假信號，混淆角色授予的真實歷史，複雜化事件響應，損害審計日誌的完整性。在監控活躍恢復操作的安全關鍵環境中，誤導性事件會引入重大運營風險。

**修復建議：**
將事件觸發條件改為基於 `_grantRole` 的布爾返回值：僅在 `_grantRole` 返回 `true`（表示角色實際被新授予）時才觸發 `LivenessRecoveryOperatorRoleGranted` 事件。

---

## 3. EntryPoint Not Included in User Operation Hash Creates the Possibility of Replay Attacks

**Severity:** 🟠 High
**Source:** `cyfrin/DelegationFramework1.md`

**Description:**
According to EIP-4337, the user operation hash must depend on both `chainId` and the `EntryPoint` address to prevent replay attacks across chains and across different EntryPoint implementations. In the current `DeleGatorCore` and `EIP7702DeleGatorCore` implementations, the `validateUserOp` function ignores the `userOpHash` parameter passed by the EntryPoint and instead computes its own hash via `getPackedUserOperationTypedDataHash`. This computed hash is derived from `getPackedUserOperationHash`, which encodes the user operation fields (sender, nonce, callData, etc.) but does not include the EntryPoint address. The domain separator `_domainSeparatorV4()` incorporates `chainId` and `address(this)` (the delegator contract address) but not the EntryPoint. As a result, a user operation signed under one EntryPoint deployment remains valid under any other EntryPoint deployment on the same chain that processes operations for the same delegator contract.

**Impact:**
When the delegator contract is upgraded to use a new EntryPoint address, previously executed user operations can be replayed against the new EntryPoint. An attacker who has observed a previously executed user operation (e.g. a native transfer) can replay it through the new EntryPoint, executing the same action again without the account holder's consent.

**Recommended Mitigation:**
Include the EntryPoint address in the user operation hash computation, consistent with the EIP-4337 specification. The simplest approach is to use the `userOpHash` parameter provided by the EntryPoint in `validateUserOp` rather than computing a custom hash that omits the EntryPoint address.

---

**[中文版本]**

**描述：**
根據 EIP-4337，用戶操作哈希必須依賴 `chainId` 和 `EntryPoint` 地址，以防止跨鏈和跨不同 EntryPoint 實作的重放攻擊。當前 `DeleGatorCore` 和 `EIP7702DeleGatorCore` 實作在 `validateUserOp` 中忽略了 EntryPoint 傳遞的 `userOpHash` 參數，自行計算哈希，而計算的哈希中不包含 EntryPoint 地址。域分隔符包含 `chainId` 和 `address(this)`，但不包含 EntryPoint。因此，在一個 EntryPoint 部署下簽署的用戶操作在同一鏈上任何其他 EntryPoint 部署中對同一委托者合約仍然有效。

**影響：**
當委托者合約升級以使用新的 EntryPoint 地址時，先前執行的用戶操作可通過新的 EntryPoint 被重放，攻擊者可在未獲賬戶持有人同意的情況下再次執行相同操作。

**修復建議：**
在用戶操作哈希計算中包含 EntryPoint 地址，與 EIP-4337 規範一致；最簡單的方法是在 `validateUserOp` 中使用 EntryPoint 提供的 `userOpHash` 參數，而非計算省略了 EntryPoint 地址的自定義哈希。

---
