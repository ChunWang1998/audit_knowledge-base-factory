# unused-remove (10)

> Issues where unused imports, constants, errors, or variables increase bytecode size or obscure intent.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Remove `< 0` comparison for unsigned integers

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
In `PledgeManager.sol`, the condition `if (numTokens <= 0 || _propertyToken.balanceOf(signer) < numTokens)` uses `<= 0` on an unsigned integer. Since unsigned integers cannot be negative, the `< 0` portion of `<= 0` is dead code that can never evaluate to true. The equivalent and accurate check is `== 0`. Leaving the `<= 0` form in place obscures intent and may mislead readers about the type of `numTokens`.

**Impact:**
The dead `< 0` branch adds noise to the code and could confuse reviewers about whether `numTokens` is actually signed, indirectly increasing review difficulty and audit surface.

**Recommended Mitigation:**
Replace `numTokens <= 0` with `numTokens == 0` to accurately reflect that only the zero-value case is being guarded against.

---

**[中文版本]**

**描述：**
在 `PledgeManager.sol` 中，條件 `if (numTokens <= 0 || ...)` 對無符號整數使用 `<= 0`。由於無符號整數不能為負，`<= 0` 中的 `< 0` 部分是永遠不會為 true 的死代碼。等效且準確的檢查是 `== 0`。保留 `<= 0` 形式會模糊意圖，可能誤導讀者認為 `numTokens` 是有符號類型。

**影響：**
死代碼的 `< 0` 分支為代碼增加噪音，可能使審計者對 `numTokens` 是否為有符號類型產生困惑，間接增加審計難度和範圍。

**修復建議：**
將 `numTokens <= 0` 替換為 `numTokens == 0`，準確反映僅針對零值情況進行保護。

---

## 2. Remove setting deprecated `lastUpdatedBy` in `RegistryService`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`RegistryService` continues to write to `investors[_id].lastUpdatedBy` in at least two places, even though the client has confirmed this field is deprecated and should no longer be populated. The corresponding storage slot in `RegistryServiceDataStore` also still exposes the field without any indication of its deprecated status, which could mislead future maintainers into treating it as a live field.

**Impact:**
Unnecessary storage write costs are incurred on every affected `RegistryService` call. The lack of deprecation marking risks the field being misused in future development.

**Recommended Mitigation:**
Remove the writes to `lastUpdatedBy` in `RegistryService`. Rename the storage field in `RegistryServiceDataStore` to `DEPRECATED_lastUpdatedBy` (consistent with how other deprecated slots are handled in the codebase) to make the deprecation explicit.

---

**[中文版本]**

**描述：**
`RegistryService` 在至少兩處繼續向 `investors[_id].lastUpdatedBy` 寫入，儘管客戶已確認此字段已被棄用且不應再填充。`RegistryServiceDataStore` 中對應的存儲槽也未顯示任何棄用狀態標示，可能誤導未來的維護者將其視為活躍字段。

**影響：**
每次受影響的 `RegistryService` 調用都會產生不必要的存儲寫入成本。缺乏棄用標記存在該字段在未來開發中被誤用的風險。

**修復建議：**
移除 `RegistryService` 中對 `lastUpdatedBy` 的寫入。將 `RegistryServiceDataStore` 中的存儲字段重命名為 `DEPRECATED_lastUpdatedBy`（與代碼庫中其他已棄用槽的處理方式一致），使棄用狀態明確。

---

## 3. Remove unused constant `CryptoartNFT::ROYALTY_BASE`

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
`CryptoartNFT` defines a constant `ROYALTY_BASE` with value 10,000, which is intended to serve as the denominator for royalty percentage calculations (where 10,000 equals 100%). However, the constant is not referenced anywhere in the contract's implementation. All royalty logic operates without using this constant, making it entirely dead code.

**Impact:**
The unused constant adds deployment gas overhead and reduces code clarity by suggesting functionality that is either not implemented or implemented through other means.

**Recommended Mitigation:**
Remove the `ROYALTY_BASE` constant declaration from `CryptoartNFT` to reduce deployment cost and eliminate the misleading suggestion of an unused royalty calculation base.

---

**[中文版本]**

**描述：**
`CryptoartNFT` 定義了值為 10,000 的常量 `ROYALTY_BASE`，旨在作為版稅百分比計算的分母（10,000 等於 100%）。然而，該常量在合約實現中任何地方均未被引用。所有版稅邏輯均在不使用此常量的情況下運行，使其完全成為死代碼。

**影響：**
未使用的常量增加了部署 Gas 開銷，並通過暗示未實現或通過其他方式實現的功能降低了代碼清晰度。

**修復建議：**
從 `CryptoartNFT` 中移除 `ROYALTY_BASE` 常量聲明，以降低部署成本並消除對未使用版稅計算基礎的誤導性暗示。

---

## 4. Remove useless function `ComplianceServiceRegulated::adjustTransferCounts`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::adjustTransferCounts` is a thin wrapper function that simply calls `adjustTotalInvestorsCounts` with its two parameters unchanged. It performs no additional logic, adds no value, and serves no purpose. All call-sites that invoke `adjustTransferCounts` could directly call `adjustTotalInvestorsCounts` instead, and the wrapper function can be safely removed.

**Impact:**
The unnecessary wrapper adds a superfluous call frame on every transfer, marginally increasing gas cost. More importantly, it adds indirection that reduces code readability and increases cognitive overhead during review.

**Recommended Mitigation:**
Remove the `adjustTransferCounts` function and replace all call-sites with direct calls to `adjustTotalInvestorsCounts`.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::adjustTransferCounts` 是一個僅以原始參數調用 `adjustTotalInvestorsCounts` 的薄包裝函數，不執行任何額外邏輯，不增加任何價值，也沒有任何用途。所有調用 `adjustTransferCounts` 的地方都可以直接調用 `adjustTotalInvestorsCounts`，包裝函數可以安全移除。

**影響：**
不必要的包裝在每次轉賬時增加了多餘的調用幀，略微增加 Gas 成本。更重要的是，它增加了間接層，降低代碼可讀性並增加審查時的認知開銷。

**修復建議：**
移除 `adjustTransferCounts` 函數，並將所有調用點替換為直接調用 `adjustTotalInvestorsCounts`。

---

## 5. Unused constants

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`Constants.sol` in the YieldFi codebase defines several constants that are never referenced anywhere in the implementation: `SIGNER_ROLE`, `VESTING_PERIOD`, `MAX_COOLDOWN_PERIOD`, `MIN_COOLDOWN_PERIOD`, `ETH_SIGNED_MESSAGE_PREFIX`, and `REWARD_HASH`. These constants suggest functionality that was planned or previously existed but is no longer active, leaving behind misleading symbols in the codebase.

**Impact:**
Unused constants increase deployment gas overhead and create misleading signals about active protocol features (e.g. `ETH_SIGNED_MESSAGE_PREFIX` and `REWARD_HASH` suggest signature-based reward logic that may not be present).

**Recommended Mitigation:**
Remove all confirmed unused constants from `Constants.sol`. If any are planned for future use, document that intent explicitly rather than leaving them silently undefined.

---

**[中文版本]**

**描述：**
YieldFi 代碼庫中的 `Constants.sol` 定義了多個在實現中任何地方均未被引用的常量：`SIGNER_ROLE`、`VESTING_PERIOD`、`MAX_COOLDOWN_PERIOD`、`MIN_COOLDOWN_PERIOD`、`ETH_SIGNED_MESSAGE_PREFIX` 和 `REWARD_HASH`。這些常量暗示曾計劃或之前存在但不再活躍的功能，在代碼庫中留下了誤導性符號。

**影響：**
未使用的常量增加部署 Gas 開銷，並對活躍的協議功能產生誤導性信號（例如 `ETH_SIGNED_MESSAGE_PREFIX` 和 `REWARD_HASH` 暗示可能不存在的基於簽名的獎勵邏輯）。

**修復建議：**
從 `Constants.sol` 中移除所有確認未使用的常量。如果任何常量計劃用於未來，請明確記錄該意圖，而不是靜默地保留未定義用途的常量。

---

## 6. Unused custom error should be removed if not required

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2` defines the custom error `NegationOverflow()` but never emits or references it anywhere in the contract implementation. Custom errors that are defined but never used increase bytecode size unnecessarily and can confuse readers about the conditions under which they might be thrown.

**Impact:**
Marginally increased deployment gas cost from the unused error definition. More significantly, the presence of `NegationOverflow` in the ABI suggests an error state that the contract never actually generates, creating false documentation.

**Recommended Mitigation:**
Remove the `NegationOverflow()` custom error declaration from `AngstromL2` unless it is genuinely needed and its usage points are identified.

---

**[中文版本]**

**描述：**
`AngstromL2` 定義了自定義錯誤 `NegationOverflow()`，但在合約實現中任何地方均未觸發或引用。定義但從不使用的自定義錯誤不必要地增加了字節碼大小，並可能使讀者對其可能被拋出的條件感到困惑。

**影響：**
未使用的錯誤定義略微增加部署 Gas 成本。更重要的是，`NegationOverflow` 出現在 ABI 中表明合約實際上從不生成的錯誤狀態，創建了虛假文檔。

**修復建議：**
從 `AngstromL2` 中移除 `NegationOverflow()` 自定義錯誤聲明，除非確實需要並已識別其使用點。

---

## 7. Unused error `IBet::InvalidAmount`

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
The interface `IBet` declares the custom error `InvalidAmount` but it is never used in any of the implementation contracts. The error appears to have been intended for amount validation logic but was either never wired up or the validation was implemented differently. Its presence in the interface creates a false expectation that amount-related reverts will surface with this specific error type.

**Impact:**
The unused error declaration increases bytecode size marginally and misleads integrators about what errors the contract emits, potentially breaking error-catching code that listens for `InvalidAmount`.

**Recommended Mitigation:**
Either remove the `InvalidAmount` declaration from `IBet`, or wire it into the appropriate amount validation check in the implementation contracts.

---

**[中文版本]**

**描述：**
接口 `IBet` 聲明了自定義錯誤 `InvalidAmount`，但在任何實現合約中均未使用。該錯誤似乎原本計劃用於金額驗證邏輯，但可能從未接入或以不同方式實現了驗證。其在接口中的存在對金額相關的回滾將以此特定錯誤類型出現創建了錯誤預期。

**影響：**
未使用的錯誤聲明略微增加字節碼大小，並誤導集成商關於合約觸發的錯誤，可能破壞監聽 `InvalidAmount` 的錯誤捕獲代碼。

**修復建議：**
從 `IBet` 中移除 `InvalidAmount` 聲明，或在實現合約中將其接入適當的金額驗證檢查。

---

## 8. Unused errors

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
The `Common` library in YieldFi defines two custom errors — `SignatureVerificationFailed()` and `BadSignature()` — that are never used anywhere in the codebase. These errors suggest that signature verification logic was planned or previously existed but was either never implemented or has since been removed.

**Impact:**
The unused error definitions add unnecessary bytecode. Their presence implies signature verification features that do not exist, potentially misleading integrators or auditors about the contract's actual capabilities.

**Recommended Mitigation:**
Remove `SignatureVerificationFailed()` and `BadSignature()` from the `Common` library. If signature verification is a planned future feature, defer error definition until the feature is implemented.

---

**[中文版本]**

**描述：**
YieldFi 的 `Common` 庫定義了兩個自定義錯誤——`SignatureVerificationFailed()` 和 `BadSignature()`——在整個代碼庫中均未使用。這些錯誤暗示計劃或之前存在的簽名驗證邏輯，但可能從未實現或已被移除。

**影響：**
未使用的錯誤定義增加不必要的字節碼。它們的存在暗示不存在的簽名驗證功能，可能誤導集成商或審計者對合約實際能力的判斷。

**修復建議：**
從 `Common` 庫中移除 `SignatureVerificationFailed()` 和 `BadSignature()`。如果簽名驗證是計劃中的未來功能，請將錯誤定義推遲到功能實現時。

---

## 9. Unused imports

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
Multiple files across the YieldFi codebase contain unused import statements. Affected files include bridge contracts (`Bridge.sol`, `BridgeMB.sol`, `BridgeCCIP.sol`), core contracts (`Manager.sol`, `OracleAdapter.sol`, `PerpetualBond.sol`), and interfaces (`IPerpetualBond.sol`, `LockBox.sol`). Unused imports inflate compilation time and obscure the actual dependencies of each module.

**Impact:**
Increased compilation time, larger dependency graphs, and reduced code clarity. Unused imports make it harder to understand which libraries and interfaces a contract actually depends on.

**Recommended Mitigation:**
Remove all identified unused import statements from the affected files. Use compiler warnings or a linter to catch and prevent future unused imports.

---

**[中文版本]**

**描述：**
YieldFi 代碼庫的多個文件包含未使用的 import 語句。受影響的文件包括橋接合約（`Bridge.sol`、`BridgeMB.sol`、`BridgeCCIP.sol`）、核心合約（`Manager.sol`、`OracleAdapter.sol`、`PerpetualBond.sol`）和接口（`IPerpetualBond.sol`、`LockBox.sol`）。未使用的 import 增加編譯時間並模糊每個模塊的實際依賴關係。

**影響：**
增加編譯時間、更大的依賴圖和降低的代碼清晰度。未使用的 import 使理解合約實際依賴哪些庫和接口變得更加困難。

**修復建議：**
從受影響文件中移除所有已識別的未使用 import 語句。使用編譯器警告或 linter 捕獲並防止未來的未使用 import。

---

## 10. Unused library and struct definitions increase deployment costs and reduce code clarity

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
The `CCTPMessageLib` library and its associated `CCTPMessage` struct (containing `message` and `signature` fields) are defined in `WormholeCCTPUpgradeable.sol` and the contract declares `using CCTPMessageLib for *`. However, `CCTPBase::redeemUSDC` manually decodes CCTP messages via `abi.decode(cctpMessage, (bytes, bytes))` instead of utilizing the struct. The library and struct are entirely unused, apparently copied from the upstream wormhole SDK without cleanup.

**Impact:**
The unused library and struct unnecessarily increase deployment gas costs. Their presence also reduces code clarity by suggesting an abstraction layer that is not actually used, and complicates maintenance.

**Recommended Mitigation:**
Remove the `CCTPMessageLib` library definition, the `CCTPMessage` struct, and the `using CCTPMessageLib for *` statement from the affected contracts.

---

**[中文版本]**

**描述：**
`CCTPMessageLib` 庫及其關聯的 `CCTPMessage` 結構體（包含 `message` 和 `signature` 字段）在 `WormholeCCTPUpgradeable.sol` 中定義，合約聲明了 `using CCTPMessageLib for *`。然而，`CCTPBase::redeemUSDC` 通過 `abi.decode(cctpMessage, (bytes, bytes))` 手動解碼 CCTP 消息，而不使用該結構體。該庫和結構體完全未被使用，顯然是從上游 wormhole SDK 複製而未清理。

**影響：**
未使用的庫和結構體不必要地增加部署 Gas 成本。它們的存在還通過暗示實際未使用的抽象層降低代碼清晰度，並增加維護複雜度。

**修復建議：**
從受影響的合約中移除 `CCTPMessageLib` 庫定義、`CCTPMessage` 結構體及 `using CCTPMessageLib for *` 語句。
