# replay-protocol (8)

> Issues involving cross-chain or cross-session signature replay, and admin role transfer guard bypasses.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

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

## 4. AdminRegistry::acceptAdmin Leaves Other Roles on the Outgoing Admin

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
When the pending admin calls `AdminRegistry::acceptAdmin`, the function revokes `DEFAULT_ADMIN_ROLE` from the previous admin and grants it to the new admin. However, the outgoing admin may have granted themselves other protocol roles during their tenure — specifically `MARKET_ADMIN_ROLE`, `OPERATOR_ROLE`, `FEE_ADMIN_ROLE`, or `RESOLUTION_ADMIN_ROLE` — using the privileges of their `DEFAULT_ADMIN_ROLE`. These non-default roles are not revoked as part of the `acceptAdmin` process. After the handoff completes, the former admin retains any additional roles they had assigned to themselves. The new admin may not be aware of this residual access and may not know to revoke those roles, leaving the outgoing admin with ongoing operational privileges they should no longer hold.

**Impact:**
An outgoing admin retains all non-default protocol roles after the admin transfer completes. This is inconsistent with the intent of a full admin transition. The former admin continues to hold market administration, operator, fee administration, or resolution administration capabilities, which could be exploited or create conflicts with the new admin's operations.

**Recommended Mitigation:**
Explicitly revoke all protocol roles from the outgoing admin within `acceptAdmin` before completing the handoff. Revoke `DEFAULT_ADMIN_ROLE`, `MARKET_ADMIN_ROLE`, `OPERATOR_ROLE`, `FEE_ADMIN_ROLE`, and `RESOLUTION_ADMIN_ROLE` from `oldAdmin` to ensure a clean transfer of all privileges to the incoming admin.

---

**[中文版本]**

**描述：**
當待定管理員調用 `AdminRegistry::acceptAdmin` 時，函數從前任管理員撤銷 `DEFAULT_ADMIN_ROLE` 並授予新管理員。然而，離任管理員在任期間可能通過其 `DEFAULT_ADMIN_ROLE` 特權向自己授予了其他協議角色，如 `MARKET_ADMIN_ROLE`、`OPERATOR_ROLE`、`FEE_ADMIN_ROLE` 或 `RESOLUTION_ADMIN_ROLE`。這些非默認角色在 `acceptAdmin` 過程中不會被撤銷，離任管理員在交接完成後仍保留這些附加角色，新管理員可能不知道需要撤銷這些角色。

**影響：**
離任管理員在管理員轉移完成後保留所有非默認協議角色，與完整管理員過渡的意圖不符，可能被利用或與新管理員的操作產生衝突。

**修復建議：**
在 `acceptAdmin` 完成移交之前，從離任管理員撤銷所有協議角色，包括 `DEFAULT_ADMIN_ROLE`、`MARKET_ADMIN_ROLE`、`OPERATOR_ROLE`、`FEE_ADMIN_ROLE` 和 `RESOLUTION_ADMIN_ROLE`，確保所有特權的乾淨轉移。

---

## 5. AdminRegistry Inherited grantRole/revokeRole Bypass the Two-Step Transfer Guard

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`AdminRegistry` inherits from OpenZeppelin `AccessControl`, which exposes public `grantRole` and `revokeRole` functions callable by the role admin. For `DEFAULT_ADMIN_ROLE`, the role admin is itself, meaning the current admin can call `grantRole(DEFAULT_ADMIN_ROLE, newAdmin)` followed by `revokeRole(DEFAULT_ADMIN_ROLE, address(this))` in two direct transactions, completely bypassing the two-step `proposeAdmin` / `acceptAdmin` mechanism. The two-step transfer guard intended to prevent accidental handoffs and ensure the new admin actively accepts the role provides no protection because the inherited one-step paths remain accessible and unoverride. Additionally, the inherited `grantRole` allows `DEFAULT_ADMIN_ROLE` to be granted to multiple addresses simultaneously, creating a split-brain state where multiple addresses hold `DEFAULT_ADMIN_ROLE` but the `admin` state variable tracks only one.

**Impact:**
The two-step transfer safety guarantee is illusory. Any admin can intentionally or accidentally complete a role transfer in a single transaction, skipping the confirmation step that validates the new admin has correct access and intention to accept. The `admin` state variable can diverge from the true `DEFAULT_ADMIN_ROLE` holder(s), creating inconsistency between on-chain role state and the tracked admin.

**Recommended Mitigation:**
Override `grantRole` and `revokeRole` to revert when called with `DEFAULT_ADMIN_ROLE`, forcing all `DEFAULT_ADMIN_ROLE` transfers through the two-step `proposeAdmin`/`acceptAdmin` mechanism. This ensures the safety guard cannot be circumvented via the inherited OpenZeppelin paths.

---

**[中文版本]**

**描述：**
`AdminRegistry` 繼承自 OpenZeppelin 的 `AccessControl`，後者公開了可由角色管理員調用的 `grantRole` 和 `revokeRole` 函數。對於 `DEFAULT_ADMIN_ROLE`，角色管理員是自身，這意味著當前管理員可直接調用 `grantRole(DEFAULT_ADMIN_ROLE, newAdmin)` 再調用 `revokeRole(DEFAULT_ADMIN_ROLE, address(this))`，完全繞過旨在防止意外移交的兩步 `proposeAdmin`/`acceptAdmin` 機制。此外，繼承的 `grantRole` 允許將 `DEFAULT_ADMIN_ROLE` 同時授予多個地址，導致多個地址持有該角色但 `admin` 狀態變量只跟蹤一個地址的分裂腦狀態。

**影響：**
兩步移交安全保障是虛幻的——任何管理員可在單筆交易中完成角色移交，跳過確認新管理員具有正確訪問和接受意圖的確認步驟；`admin` 狀態變量可能與真實的 `DEFAULT_ADMIN_ROLE` 持有者不一致。

**修復建議：**
覆蓋 `grantRole` 和 `revokeRole`，使其在以 `DEFAULT_ADMIN_ROLE` 調用時回滾，強制所有 `DEFAULT_ADMIN_ROLE` 轉移通過兩步 `proposeAdmin`/`acceptAdmin` 機制，確保安全防護無法通過繼承的 OpenZeppelin 路徑被繞過。

---

## 6. All Swaps Will Revert if the Dynamic Protocol Fee Is Enabled Since hook-config.sol Does Not Encode the afterSwapReturnDelta Permission

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
If `AngstromL2::setPoolHookSwapFee` is called by the owner to configure a non-zero dynamic hook protocol fee, the Uniswap V4 delta accounting mechanism will result in a revert with `CurrencyNotSettled()` for all swaps. The issue is that `AngstromL2`'s `afterSwap` callback mints fee amounts to itself via `UNI_V4.mint(address(this), ...)`, which creates an unspecified hook delta in the Uniswap V4 accounting system. For this delta to be correctly parsed and applied, the hook must declare the `afterSwapReturnDelta` permission by encoding it into the hook address bits. However, `hook-config.sol` does not specify that `afterSwapReturnDelta` should be included in the required hook permissions. Without this permission, Uniswap V4 does not parse the return delta from `afterSwap`, causing the unaccounted fee delta to leave the currency unsettled, which triggers a revert on every swap when the dynamic fee is active.

**Impact:**
All swaps through pools that have the dynamic protocol fee enabled will revert with `CurrencyNotSettled()`. This completely disables the swap functionality for any pool where the hook swap fee has been set to a non-zero value, effectively shutting down trading on affected pools.

**Recommended Mitigation:**
Add `afterSwapReturnDelta = true` to the required hook permissions in `hook-config.sol` so that the hook address is constructed with this permission bit encoded, enabling Uniswap V4 to correctly parse and settle the return delta from `afterSwap`.

---

**[中文版本]**

**描述：**
若所有者調用 `AngstromL2::setPoolHookSwapFee` 配置非零的動態鉤子協議費用，Uniswap V4 的 delta 會計機制將對所有兌換以 `CurrencyNotSettled()` 回滾。問題在於 `AngstromL2` 的 `afterSwap` 回調通過 `UNI_V4.mint(address(this), ...)` 將費用鑄造給自身，在 Uniswap V4 會計系統中創建了未指定的鉤子 delta。為使此 delta 被正確解析和應用，鉤子必須通過在鉤子地址位中編碼來聲明 `afterSwapReturnDelta` 權限。然而，`hook-config.sol` 未指定需要包含 `afterSwapReturnDelta`，導致 Uniswap V4 不解析 `afterSwap` 的返回 delta，使未結算的費用 delta 觸發回滾。

**影響：**
所有啟用了動態協議費用的池中的兌換都將以 `CurrencyNotSettled()` 回滾，完全禁用了任何設置了非零鉤子兌換費用的池的交易功能。

**修復建議：**
在 `hook-config.sol` 的所需鉤子權限中添加 `afterSwapReturnDelta = true`，使鉤子地址以此權限位編碼構建，讓 Uniswap V4 能夠正確解析和結算 `afterSwap` 的返回 delta。

---

## 7. Automation DoS via Blacklisted or Reverting Fee Recipients

**Severity:** 🟡 Medium
**Source:** `cyfrin/octodefi.md`

**Description:**
`FeeHandler.handleFee()` uses `safeTransferFrom()` to push ERC-20 tokens to multiple recipients in sequence: `beneficiary`, `creator`, `vault`, and `burnerAddress`. If any of these addresses is blacklisted by a token like USDT or USDC, the `safeTransferFrom()` call reverts, and since there is no error handling, the entire `executeAutomation()` call fails. Similarly, `handleFeeETH()` uses the `transfer()` function (limited to 2300 gas units) to push native ETH to these recipients. If any recipient is a smart contract whose `receive()` function requires more than 2300 gas (for example a multi-sig or a contract wallet with custom logic), the native transfer reverts and blocks all automation execution. Because fees are pushed to all recipients in a single sequential loop with no fallback, a single failing or malicious fee recipient permanently blocks all future automated strategy executions for any strategy that routes fees through that recipient.

**Impact:**
Any strategy whose `creator`, `beneficiary`, `vault`, or `burnerAddress` gets blacklisted by a supported token, or is a contract that reverts on ETH receipt, will have all future `executeAutomation()` calls permanently blocked. Denial of service is trivially achievable by any party who can influence one of these address registrations, and is also achievable through external token blacklisting actions (e.g., OFAC sanctions).

**Recommended Mitigation:**
Switch from a push pattern to a pull pattern where each fee recipient accumulates their balance on-chain and withdraws independently. This ensures that a failing transfer to one recipient does not block distributions to others. Additionally, replace `transfer()` with a safe native transfer library that handles revert cases gracefully.

---

**[中文版本]**

**描述：**
`FeeHandler.handleFee()` 使用 `safeTransferFrom()` 順序向多個接收者推送 ERC-20 代幣：`beneficiary`、`creator`、`vault` 和 `burnerAddress`。若這些地址中任何一個被 USDT 或 USDC 等代幣列入黑名單，`safeTransferFrom()` 調用回滾，由於沒有錯誤處理，整個 `executeAutomation()` 調用失敗。同樣，`handleFeeETH()` 使用限制為 2300 gas 的 `transfer()` 函數推送原生 ETH，若任何接收者是需要超過 2300 gas 的智能合約（如多簽或具有自定義邏輯的合約錢包），原生轉帳回滾並阻塞所有自動化執行。

**影響：**
任何 `creator`、`beneficiary`、`vault` 或 `burnerAddress` 被代幣列入黑名單或是在接收 ETH 時回滾的合約的策略，其所有未來的 `executeAutomation()` 調用將被永久阻塞，拒絕服務可由任何能影響這些地址註冊的方輕易實現。

**修復建議：**
從推送模式切換到拉取模式，每個費用接收者在鏈上積累其餘額並獨立提取，確保向一個接收者的失敗轉帳不會阻塞向其他接收者的分配；同時將 `transfer()` 替換為能夠優雅處理回滾情況的安全原生轉帳庫。

---

## 8. Protocol Vulnerable to Cross-Chain Signature Replay

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
Signatures generated by the CryptoArt protocol do not include `chainId` as a parameter in the signed message payload. The absence of chain ID binding means that a valid signature produced for one chain is cryptographically identical to a signature that would be accepted on any other chain where the same contract is deployed. This is a classic cross-chain replay vulnerability: if a user signs a transaction authorizing an action on chain A, that same signature can be submitted on chain B to authorize the same action on behalf of that user, without any further consent from them. Although at the time of this audit the protocol is only planned for single-chain deployment (making the attack path currently non-exploitable), the design flaw creates material future risk if the protocol expands to multiple chains without this being remediated first.

**Impact:**
If the protocol is ever deployed on multiple chains, any valid signature from one chain can be replayed on any other chain where the contract is deployed. Users who authorize a specific action on one chain would inadvertently authorize the same action across all other chains, exposing them to unauthorized operations on chains they may never interact with.

**Recommended Mitigation:**
Include `block.chainid` as a required parameter in all signature construction and verification flows. This binds each signature to a specific chain, ensuring that cross-chain replay is cryptographically impossible even if the same contract is deployed across multiple networks.

---

**[中文版本]**

**描述：**
CryptoArt 協議生成的簽名在簽名消息載荷中不包含 `chainId` 參數。缺乏鏈 ID 綁定意味著為一條鏈生成的有效簽名在密碼學上與部署了相同合約的任何其他鏈上可接受的簽名完全相同。這是典型的跨鏈重放漏洞：若用戶在鏈 A 上簽署授權某操作的交易，同一簽名可在鏈 B 上提交以代表該用戶授權相同操作，無需其進一步同意。雖然審計時協議僅計劃單鏈部署（使攻擊路徑目前不可利用），但若協議在修復前擴展到多條鏈，此設計缺陷將帶來重大未來風險。

**影響：**
若協議部署到多條鏈上，來自一條鏈的任何有效簽名可在部署了合約的任何其他鏈上被重放，在用戶從未交互的鏈上使其面臨未授權操作的風險。

**修復建議：**
在所有簽名構建和驗證流程中將 `block.chainid` 作為必需參數包含進去，將每個簽名綁定到特定鏈，確保即使相同合約部署在多個網絡上，跨鏈重放在密碼學上也是不可能的。
