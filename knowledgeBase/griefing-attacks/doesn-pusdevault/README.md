# doesn-pusdevault (12)

> Issues where missing checks, validations, or pausing flags cause incorrect behavior in vault and deposit flows.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Attacker can drain all tokens from cancelled game since `SessionManager::refundCancelledGame` doesn't validate caller actually joined the game

**Severity:** 🔴 Critical
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::refundCancelledGame` does not check whether the caller actually participated in the game before issuing a refund. Any address — including one that never deposited any tokens — can call the function and receive a refund from a cancelled game's pool. By repeating the call from multiple addresses, an attacker can drain the entire token balance of a cancelled game contract.

**Impact:**
Any cancelled game can be completely drained of tokens by a permissionless attacker. Legitimate participants who did join the game will be left with nothing to claim once the contract balance reaches zero.

**Recommended Mitigation:**
Add a check inside `refundCancelledGame` that verifies `contestants[gameId][msg.sender]` is true before processing the refund, ensuring only users who actually joined can claim a refund.

---

**[中文版本]**

**描述：**
`SessionManager::refundCancelledGame` 在退款前未驗證調用者是否實際參與了該遊戲。任何地址——包括從未存入代幣的地址——均可調用此函數並從已取消遊戲的資金池中獲取退款。攻擊者可通過使用多個不同地址重複調用的方式，徹底清空合約中的所有代幣。

**影響：**
任何已取消的遊戲都可能被無需許可的攻擊者完全清空。一旦合約餘額歸零，真正參與遊戲的合法用戶將無法獲得任何退款。

**修復建議：**
在 `refundCancelledGame` 中添加驗證：確認 `contestants[gameId][msg.sender]` 為 true 後再處理退款，確保只有真正參與遊戲的用戶才能申請退款。

---

## 2. `BridgeableTokenP::getMaxDebitableAmount` doesn't account for isolate mode, returning inflated values

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
When isolate mode is enabled, `BridgeableTokenP::_debit` enforces that `creditDebitBalance` remains non-negative after a debit, effectively capping the max debit at the current balance. However, `getMaxDebitableAmount` does not factor this constraint in — it only considers global and daily limits. As a result, the view function can report a maximum debitable amount far larger than what `_debit` will actually accept. Additionally, the early-return guard uses `< 0` instead of `<= 0`, meaning a balance of exactly zero still produces a non-zero max value despite any debit reverting.

**Impact:**
Integrators and users who rely on `getMaxDebitableAmount` to size their transactions will build calls that revert on-chain, wasting gas and causing unexpected failures.

**Recommended Mitigation:**
Fix the early-return guard from `creditDebitBalance < 0` to `creditDebitBalance <= 0`, and when in isolate mode cap the returned value by `creditDebitBalance` using `MathLib.min(result, uint256(creditDebitBalance))`.

---

**[中文版本]**

**描述：**
啟用隔離模式時，`_debit` 強制要求扣款後 `creditDebitBalance` 保持非負，實際上將最大可扣金額限制為當前餘額。但 `getMaxDebitableAmount` 不考慮此約束，僅根據全局和每日限額計算返回值，導致視圖函數報告的最大可扣金額遠超實際可接受金額。此外，提前返回判斷使用 `< 0` 而非 `<= 0`，使餘額恰好為零時仍返回非零值，但任何扣款都會回滾。

**影響：**
依賴 `getMaxDebitableAmount` 來確定交易金額的集成商和用戶將構建在鏈上回滾的調用，浪費 Gas 並導致意外失敗。

**修復建議：**
將提前返回判斷從 `creditDebitBalance < 0` 改為 `creditDebitBalance <= 0`，並在隔離模式下使用 `MathLib.min(result, uint256(creditDebitBalance))` 對返回值進行上限限制。

---

## 3. ETH sent with adapter vault redemption is trapped in `SablierBob`

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierBob::redeem` is declared `payable` unconditionally, but only the non-adapter path handles `msg.value`. When a user calls `redeem` on an adapter vault and includes `msg.value > 0`, the adapter execution path never checks, forwards, or refunds the ETH. The ETH remains trapped in the contract until `transferFeesToComptroller` sweeps the entire ETH balance to the comptroller — not back to the sending user.

**Impact:**
Users who mistakenly send ETH when redeeming from adapter vaults permanently lose that ETH. The `payable` modifier provides no indication that ETH is unnecessary and will be lost.

**Recommended Mitigation:**
Add an early revert at the start of the adapter path: if `msg.value > 0`, revert with a descriptive error such as `SablierBob_UnexpectedNativeToken(vaultId)`.

---

**[中文版本]**

**描述：**
`SablierBob::redeem` 無條件標記為 `payable`，但只有非適配器路徑才處理 `msg.value`。當用戶在適配器金庫上調用 `redeem` 並附帶 `msg.value > 0` 時，適配器執行路徑從不檢查、轉發或退還 ETH。該 ETH 將被鎖在合約中，直到 `transferFeesToComptroller` 將整個 ETH 餘額掃入財務控制器——而非退還給發送用戶。

**影響：**
誤發送 ETH 進行適配器金庫贖回的用戶將永久損失該 ETH。`payable` 修飾符未提供 ETH 不必要且會丟失的提示。

**修復建議：**
在適配器路徑開始處添加提前回滾：如果 `msg.value > 0`，則以描述性錯誤（如 `SablierBob_UnexpectedNativeToken(vaultId)`）回滾。

---

## 4. Inconsistency in `currentPhase` between `pUSDeVault` and `yUSDeVault`

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Both `pUSDeVault` and `yUSDeVault` inherit `PreDepositVault` which inherits `PreDepositPhaser`. The `pUSDe::currentPhase` state variable is updated whenever the phase transitions, but `yUSDe::currentPhase` is never updated and always returns the default `PointsPhase` variant. Because `currentPhase` is a public state variable, a view function is automatically exposed for `yUSDeVault` that always returns a stale default value regardless of the actual protocol phase.

**Impact:**
External integrators or monitoring tools reading `yUSDeVault.currentPhase()` will receive an incorrect (always-default) phase value, potentially causing incorrect downstream logic.

**Recommended Mitigation:**
Make the `currentPhase` state variable internal in `PreDepositPhaser` and only expose the corresponding view function within `pUSDeVault`, or override the view function in `yUSDeVault` to return `pUSDeVault`'s phase.

---

**[中文版本]**

**描述：**
`pUSDeVault` 和 `yUSDeVault` 均繼承 `PreDepositVault`（後者繼承 `PreDepositPhaser`）。`pUSDe::currentPhase` 狀態變量在階段切換時會被更新，但 `yUSDe::currentPhase` 從不更新，始終返回默認的 `PointsPhase` 變體。由於 `currentPhase` 是公共狀態變量，`yUSDeVault` 會自動暴露一個始終返回過期默認值的視圖函數。

**影響：**
讀取 `yUSDeVault.currentPhase()` 的外部集成商或監控工具將獲得錯誤（始終為默認值）的階段信息，可能導致下游邏輯錯誤。

**修復建議：**
在 `PreDepositPhaser` 中將 `currentPhase` 狀態變量設為 internal，僅在 `pUSDeVault` 中暴露對應的視圖函數；或在 `yUSDeVault` 中重寫視圖函數，返回 `pUSDeVault` 的階段值。

---

## 5. Manual/Instant `fulfillRedeemRequest` doesn't reserve liquidity

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableAsyncRedeemVault` only increments `reservedLiquidity` when processing the withdrawal queue via `processUpToShares` or `processUpToRequestId`. The manual fulfillment path (`fulfillRedeemRequest`) and the instant branch of `requestRedeem` mark shares as claimable without updating `reservedLiquidity`. When these paths are mixed, multiple fulfillments can each independently pass the liquidity check, producing a state where the sum of claimable assets across users exceeds `vault.totalAssets() - reservedLiquidity`.

**Impact:**
The vault can end up with more claimable redemptions than available assets, causing later withdrawals to revert and creating fairness and accounting discrepancies between users.

**Recommended Mitigation:**
Increment `reservedLiquidity` in all fulfillment paths — including the manual `fulfillRedeemRequest` and the instant branch of `requestRedeem` — to ensure the reserved liquidity accounting stays consistent.

---

**[中文版本]**

**描述：**
`AccountableAsyncRedeemVault` 僅在通過 `processUpToShares` 或 `processUpToRequestId` 處理提款隊列時才遞增 `reservedLiquidity`。手動履行路徑（`fulfillRedeemRequest`）和 `requestRedeem` 的即時分支在標記份額為可領取時不更新 `reservedLiquidity`。當這些路徑混合使用時，多次履行各自獨立通過流動性檢查，導致所有用戶可領取資產之和超過 `vault.totalAssets() - reservedLiquidity`。

**影響：**
金庫的可兌換贖回量可能超過可用資產，導致後續提款回滾，並在用戶間產生公平性和記賬差異。

**修復建議：**
在所有履行路徑中均遞增 `reservedLiquidity`——包括手動 `fulfillRedeemRequest` 和 `requestRedeem` 的即時分支——確保預留流動性賬目保持一致。

---

## 6. More efficient way of checking for empty string in `CommonUtils::isEmptyString`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
The current `CommonUtils::isEmptyString` function can be made more gas-efficient. Rather than comparing against an empty string literal, the function should check the byte length of the string directly using `bytes(_str).length == 0`. This avoids unnecessary memory allocation associated with constructing an empty string comparand.

**Impact:**
Every call-site that invokes `isEmptyString` incurs slightly higher gas than necessary. Since this utility is called frequently throughout the codebase, the aggregate cost is non-trivial over time.

**Recommended Mitigation:**
Replace the implementation with `return bytes(_str).length == 0;` to eliminate the extra memory allocation.

---

**[中文版本]**

**描述：**
現有的 `CommonUtils::isEmptyString` 函數可通過直接比較字符串的字節長度（`bytes(_str).length == 0`）來提高 Gas 效率，而不是與空字符串字面量進行比較，避免構造比較操作數時產生的額外內存分配。

**影響：**
每個調用 `isEmptyString` 的地方都比必要消耗更多 Gas。由於整個代碼庫中頻繁調用此工具函數，累積成本不可忽視。

**修復建議：**
將實現替換為 `return bytes(_str).length == 0;` 以消除額外的內存分配。

---

## 7. Pausing Disables Allowance Revocation Leaving Users Exposed During Emergencies

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/NEBA Token.txt`

**Description:**
The `NEBAToken` contract overrides `_approve()` with a `whenNotPaused` modifier, which blocks all allowance changes — including reductions to zero — while the token is paused. This deviates from OpenZeppelin's default `ERC20Pausable` behavior, which only pauses transfers. During a pause (typically triggered during an emergency such as an exploit discovery or key compromise), users are unable to revoke or reduce allowances they previously granted to DEXs, routers, custodians, or other third parties.

**Impact:**
Users remain exposed to stale or compromised spender allowances for the entire duration of a pause, precisely when the risk from those allowances is highest.

**Recommended Mitigation:**
Remove the `whenNotPaused` guard from the `_approve()` override, or at minimum permit allowance decreases (particularly to zero) during a pause while still blocking increases or new approvals.

---

**[中文版本]**

**描述：**
`NEBAToken` 合約在 `_approve()` 的重寫中添加了 `whenNotPaused` 修飾符，導致代幣暫停期間所有授權變更——包括將授權減少至零——均被阻止。這偏離了 OpenZeppelin 默認的 `ERC20Pausable` 行為（默認僅暫停轉賬）。在暫停期間（通常因漏洞發現或密鑰洩露等緊急情況觸發），用戶無法撤銷或降低此前授予 DEX、路由器、託管方或其他第三方的授權額度。

**影響：**
用戶在整個暫停期間仍暴露於過期或被盜用的支出方授權，而此時此類授權帶來的風險恰恰最高。

**修復建議：**
從 `_approve()` 的重寫中移除 `whenNotPaused` 限制；或至少允許在暫停期間進行授權減少（尤其是減少至零），同時繼續阻止增加或新建授權。

---

## 8. `PocketFactory::approveTailor` doesn't verify `ITailor` interface implementation

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`PocketFactory::approveTailor()` validates that the tailor address is non-zero and has contract code, but does not verify that the contract implements the `ITailor` interface required for pocket management operations. Any contract with bytecode — regardless of whether it supports the required interface — can be approved as a tailor.

**Impact:**
A non-compliant contract could be approved and later used as a tailor, causing downstream calls to pocket management functions to revert unexpectedly.

**Recommended Mitigation:**
Add an ERC-165 `supportsInterface(type(ITailor).interfaceId)` check inside `approveTailor()` and revert if the target does not declare support for the interface. Apply the same check in the `ApproveTailorInFactory.s.sol` deployment script as an additional safety layer.

---

**[中文版本]**

**描述：**
`PocketFactory::approveTailor()` 驗證 tailor 地址非零且含有合約代碼，但不驗證該合約是否實現了 Pocket 管理操作所需的 `ITailor` 接口。任何含有字節碼的合約——無論是否支持所需接口——均可被批准為 tailor。

**影響：**
不符合規範的合約可能被批准並在後續 Pocket 管理函數調用中使用，導致意外回滾。

**修復建議：**
在 `approveTailor()` 中添加 ERC-165 的 `supportsInterface(type(ITailor).interfaceId)` 檢查，若目標合約未聲明支持該接口則回滾。同時在 `ApproveTailorInFactory.s.sol` 部署腳本中添加同樣的檢查作為額外安全層。

---

## 9. Prefix internal and private function names with `_` character

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Solidity convention and widely adopted best practice is to prefix internal and private function names with an underscore (`_`) to distinguish them from public and external functions. The pre-deposit contracts apply this prefix inconsistently: `PreDepositPhaser::setYieldPhaseInner`, `yUSDeDepositor::deposit_pUSDe` and `deposit_pUSDeDepositor`, `PreDepositVault::onAfterDepositChecks` and `onAfterWithdrawalChecks`, and several functions in `pUSDeVault` and `yUSDeVault` are internal but lack the prefix.

**Impact:**
Inconsistent naming reduces code readability and makes it harder to distinguish visibility at a glance, increasing the risk of accidental exposure or incorrect overrides.

**Recommended Mitigation:**
Apply the `_` prefix consistently to all internal and private function names across the pre-deposit contract suite.

---

**[中文版本]**

**描述：**
Solidity 的慣例和廣泛採用的最佳實踐是為 internal 和 private 函數名稱添加下劃線前綴（`_`），以區分其與 public 和 external 函數。pre-deposit 合約中此前綴應用不一致：`PreDepositPhaser::setYieldPhaseInner`、`yUSDeDepositor::deposit_pUSDe` 和 `deposit_pUSDeDepositor`、`PreDepositVault::onAfterDepositChecks` 和 `onAfterWithdrawalChecks`，以及 `pUSDeVault` 和 `yUSDeVault` 中的多個函數均為 internal 但缺少前綴。

**影響：**
命名不一致降低代碼可讀性，使可見性難以一眼識別，增加了意外暴露或錯誤覆蓋的風險。

**修復建議：**
在整個 pre-deposit 合約套件中對所有 internal 和 private 函數名稱一致地應用 `_` 前綴。

---

## 10. Roles not set in `deposit-registry` contract constructors

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
Contracts in the `issuance` module properly initialize their operational roles (such as `MINTER_ROLE`) in their constructors, ensuring the necessary role holders exist from deployment. In contrast, `deposit-registry` contracts (`ComplianceChecker` and `CompliantDepositRegistry`) only grant `DEFAULT_ADMIN_ROLE` in their constructors but do not initialize `COMPLIANCE_ADMIN_ROLE` or `CANCELER_ROLE` respectively. These roles must be granted separately after deployment.

**Impact:**
Between deployment and the separate role-granting transaction, the contracts have no holders for `COMPLIANCE_ADMIN_ROLE` or `CANCELER_ROLE`, creating a deployment risk window where these functions are inaccessible.

**Recommended Mitigation:**
Initialize `COMPLIANCE_ADMIN_ROLE` in the `ComplianceChecker` constructor and `CANCELER_ROLE` in the `CompliantDepositRegistry` constructor, granting them to the `defaultAdmin` or a designated address at deployment time.

---

**[中文版本]**

**描述：**
`issuance` 模塊中的合約在構造函數中正確初始化了操作角色（如 `MINTER_ROLE`），確保必要的角色持有人從部署起就存在。相比之下，`deposit-registry` 合約（`ComplianceChecker` 和 `CompliantDepositRegistry`）在構造函數中僅授予 `DEFAULT_ADMIN_ROLE`，未分別初始化 `COMPLIANCE_ADMIN_ROLE` 和 `CANCELER_ROLE`，這些角色必須在部署後單獨授予。

**影響：**
在部署與單獨授予角色的交易之間，這些合約的 `COMPLIANCE_ADMIN_ROLE` 和 `CANCELER_ROLE` 沒有持有人，產生部署風險窗口期，相關功能在此期間無法訪問。

**修復建議：**
在 `ComplianceChecker` 構造函數中初始化 `COMPLIANCE_ADMIN_ROLE`，在 `CompliantDepositRegistry` 構造函數中初始化 `CANCELER_ROLE`，並在部署時授予給 `defaultAdmin` 或指定地址。

---

## 11. `pUSDeVault::maxDeposit` doesn't account for deposit pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
EIP-4626 specifies that `maxDeposit` must factor in both global and user-specific limits and must return 0 if deposits are entirely disabled (even temporarily). `pUSDeVault::maxDeposit` does not account for the `depositsEnabled` flag. When deposits are paused, the function still returns `type(uint256).max`, misrepresenting the actual deposit capacity to integrating protocols.

**Impact:**
Protocols that rely on `maxDeposit` to determine deposit availability will attempt deposits that revert, causing unexpected failures in integrations and breaking EIP-4626 compatibility guarantees.

**Recommended Mitigation:**
Override `maxDeposit` in `PreDepositVault` (where the `depositsEnabled` flag lives) to return 0 when deposits are paused.

---

**[中文版本]**

**描述：**
EIP-4626 規定 `maxDeposit` 必須考慮全局和用戶特定限制，且在存款被完全禁用（即使是臨時的）時必須返回 0。`pUSDeVault::maxDeposit` 未考慮 `depositsEnabled` 標誌。當存款暫停時，該函數仍返回 `type(uint256).max`，向集成協議錯誤傳達了實際存款容量。

**影響：**
依賴 `maxDeposit` 判斷存款可用性的協議將嘗試會回滾的存款操作，導致集成中的意外失敗並破壞 EIP-4626 兼容性保證。

**修復建議：**
在 `PreDepositVault`（`depositsEnabled` 標誌所在處）中重寫 `maxDeposit`，當存款暫停時返回 0。

---

## 12. `pUSDeVault::maxRedeem` doesn't account for redemption pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
EIP-4626 specifies that `maxRedeem` must return 0 if redemption is entirely disabled (even temporarily). `pUSDeVault::maxRedeem` does not account for the `withdrawalsEnabled` flag. Since `MetaVault::redeem` internally calls `_withdraw`, redemptions are effectively paused when withdrawals are disabled, but `maxRedeem` continues to return the full share balance of the querying user.

**Impact:**
Integrating protocols that inspect `maxRedeem` to determine redemption availability will attempt redemptions that revert, causing unexpected failures and breaking EIP-4626 compatibility.

**Recommended Mitigation:**
Override `maxRedeem` in `PreDepositVault` to return 0 when withdrawals are paused.

---

**[中文版本]**

**描述：**
EIP-4626 規定 `maxRedeem` 在贖回被完全禁用（即使是臨時的）時必須返回 0。`pUSDeVault::maxRedeem` 未考慮 `withdrawalsEnabled` 標誌。由於 `MetaVault::redeem` 內部調用 `_withdraw`，提款禁用時贖回實際上也被暫停，但 `maxRedeem` 仍持續返回查詢用戶的完整份額餘額。

**影響：**
通過檢查 `maxRedeem` 判斷贖回可用性的集成協議將嘗試會回滾的贖回操作，導致意外失敗並破壞 EIP-4626 兼容性。

**修復建議：**
在 `PreDepositVault` 中重寫 `maxRedeem`，當提款暫停時返回 0。
