# validation-access (11)

> Issues where access control checks were missing, commented out, or improperly validated.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

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

## 3. Commented-Out Blacklist Check Allows Restricted Transfers

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
In `PerpetualBond::_update`, the line intended to restrict transfers involving blacklisted users is currently commented out. The code comment reads "Placeholder for Blacklist check" and the corresponding `require(!IBlackList(administrator).isBlackListed(from) && !IBlackList(administrator).isBlackListed(to), "blacklisted")` statement is inactive. This means the blacklist enforcement on transfers of `PerpetualBond` tokens is completely disabled — the check exists in the codebase as a comment but has no effect on-chain.

**Impact:**
Blacklisted addresses can freely hold and transfer `PerpetualBond` tokens, bypassing any intended access control or compliance restrictions. The blacklist mechanism provides no protection for this token class, which may violate regulatory requirements or protocol compliance rules intended to restrict certain addresses from holding or moving these assets.

**Recommended Mitigation:**
Uncomment the blacklist check in `PerpetualBond::_update` to re-enable transfer restrictions for blacklisted users, ensuring both the `from` and `to` addresses are verified against the blacklist before any transfer is permitted.

---

**[中文版本]**

**描述：**
在 `PerpetualBond::_update` 中，限制黑名單用戶轉帳的代碼行當前被注釋掉了。代碼注釋寫著「黑名單檢查佔位符」，相應的 `require(!IBlackList(administrator).isBlackListed(from) && !IBlackList(administrator).isBlackListed(to), "blacklisted")` 語句處於非活躍狀態。這意味著 `PerpetualBond` 代幣轉帳的黑名單執行被完全禁用——檢查作為注釋存在於代碼庫中，但在鏈上沒有任何效果。

**影響：**
黑名單地址可自由持有和轉移 `PerpetualBond` 代幣，繞過任何預期的訪問控制或合規限制，可能違反旨在限制特定地址持有或移動這些資產的監管要求。

**修復建議：**
取消 `PerpetualBond::_update` 中黑名單檢查的注釋，重新啟用對黑名單用戶的轉帳限制，確保在允許任何轉帳之前驗證 `from` 和 `to` 地址是否在黑名單中。

---

## 4. Minting is Allowed for Frozen and Non-Whitelisted Addresses

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Tokenizer.Estate.txt`

**Description:**
The `RealEstateToken` contract includes compliance and control mechanisms such as freezing accounts (`setFrozen`), locking balances (`lockBalance`), and enforcing a whitelist (`setWhitelistMode`). These are primarily enforced within the overridden `_update` function. However, all compliance checks for frozen accounts and whitelisting are wrapped inside a conditional statement that only executes for regular transfers: `if (from != address(0) && to != address(0))`. When `mint` is called, it internally calls `_update(address(0), to, amount)`. Since `from` is `address(0)`, the condition is `false` and the entire block containing freeze and whitelist checks is skipped. This allows the MINTER role to create new tokens for addresses that are explicitly frozen or not on the whitelist. Similarly, burning (`_update(account, address(0), amount)`) bypasses the freeze check since `to` is `address(0)`.

**Impact:**
The MINTER role can mint tokens directly to frozen addresses (including those flagged for sanctions or fraud), bypassing the intended regulatory controls. Tokens minted to non-whitelisted addresses become permanently untransferable since the whitelist check is enforced on transfers. This can result in permanently stuck tokens in non-compliant wallets and defeats the purpose of the compliance mechanisms.

**Recommended Mitigation:**
Restructure the compliance checks within `_update` so they apply correctly to mint, burn, and transfer operations. Specifically, check the frozen and whitelist status of the `to` address during minting, and the frozen status of the `from` address during burning, rather than only executing these checks during regular (non-zero address) transfers.

---

**[中文版本]**

**描述：**
`RealEstateToken` 合約包含合規控制機制，如凍結賬戶（`setFrozen`）、鎖定餘額（`lockBalance`）和強制白名單（`setWhitelistMode`），主要在覆蓋的 `_update` 函數中執行。然而，所有冷凍賬戶和白名單檢查都包裝在僅針對常規轉帳執行的條件語句中：`if (from != address(0) && to != address(0))`。當調用 `mint` 時，它內部調用 `_update(address(0), to, amount)`，由於 `from` 是 `address(0)`，條件為 `false`，整個包含凍結和白名單檢查的塊被跳過，允許 MINTER 角色向被明確凍結或不在白名單上的地址創建新代幣。

**影響：**
MINTER 角色可直接向凍結地址（包括被標記為制裁或欺詐的地址）鑄造代幣，繞過預期的監管控制；鑄造給非白名單地址的代幣由於轉帳時的白名單檢查將永久無法轉移，導致資金永久滯留在不合規錢包中。

**修復建議：**
重構 `_update` 中的合規檢查，使其正確應用於鑄造、銷毀和轉帳操作，具體而言：在鑄造時檢查 `to` 地址的凍結和白名單狀態，在銷毀時檢查 `from` 地址的凍結狀態，而不是僅在常規轉帳時執行這些檢查。

---

## 5. Missing Access Control on verifyAndMarkComplete Enables Proof Griefing Attack

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The `ProofSystemUpgradeable` contract implements access control for `recordVerifiedProof`, requiring the caller to be either the owner or an authorized caller. However, `verifyAndMarkComplete` and `verifyBatch` — both of which also write to the `verifiedProofs` mapping — have no access control whatsoever. Any address can call these functions. Since `_verifyHostSignature` rejects proofs whose hash is already in the `verifiedProofs` mapping, and `submitProofOfWork` in `JobMarketplaceWithModelsUpgradeable` requires `verifyAndMarkComplete` to return `true`, an attacker who observes a valid proof in the mempool can front-run the host's `submitProofOfWork` call by directly invoking `verifyAndMarkComplete`. This marks the `proofHash` as consumed before the legitimate submission, causing the host's transaction to revert. The proof hash is permanently consumed; the host must generate an entirely new inference output to try again.

**Impact:**
Attackers can persistently prevent hosts from submitting valid proofs by front-running and consuming their proof hashes. Hosts unable to submit proofs cannot claim payment for legitimate computational work. Sessions time out with zero payment, causing irreversible economic loss to hosts while renters receive refunds. The attack is economically asymmetric: cheap for the attacker, devastating for the host.

**Recommended Mitigation:**
Add access control to `verifyAndMarkComplete` and `verifyBatch`, restricting callers to authorized addresses only — specifically the `JobMarketplace` contract and any other explicitly trusted contracts. This is consistent with the access control already applied to `recordVerifiedProof`.

---

**[中文版本]**

**描述：**
`ProofSystemUpgradeable` 合約對 `recordVerifiedProof` 實作了訪問控制（要求調用者為所有者或授權調用者），但 `verifyAndMarkComplete` 和 `verifyBatch`——兩者同樣向 `verifiedProofs` 映射寫入——完全沒有訪問控制。任何地址都可以調用這些函數。攻擊者可從內存池中觀察到有效證明，通過搶先調用 `verifyAndMarkComplete` 消耗證明哈希，導致主機的合法提交回滾，主機無法收到工作報酬。

**影響：**
攻擊者可持續阻止主機提交有效證明，主機無法為合法的計算工作索取報酬，會話超時且支付為零，造成主機不可挽回的經濟損失，而攻擊者的成本極低。

**修復建議：**
為 `verifyAndMarkComplete` 和 `verifyBatch` 添加訪問控制，僅限授權地址（特別是 `JobMarketplace` 合約）調用，與 `recordVerifiedProof` 現有的訪問控制保持一致。

---

## 6. Missing Access Control in SDLVesting::stakeReleasableTokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
`SDLVesting::stakeReleasableTokens` is designed to be driven exclusively by a trusted staking bot operated by the Stake.Link team. The function periodically takes newly-vested SDL tokens and locks them into the SDLPool under the beneficiary's chosen duration. However, the function currently has no access control — it is `external` with no modifier restricting who may call it. This means any arbitrary address can call `stakeReleasableTokens` at any time. An attacker can exploit this by front-running the beneficiary's `release()` transaction: before the beneficiary can claim their vested tokens as liquid funds, the attacker calls `stakeReleasableTokens`, which forces all releasable tokens into a locked staking position with the beneficiary's chosen lock duration (e.g. 4 years). The beneficiary's liquid release then yields almost nothing, and the staked position remains locked for the full duration.

**Impact:**
An adversary can repeatedly deny the beneficiary access to vested tokens by front-running their `release()` transactions and forcing all releasable tokens into long-term locked staking positions. The beneficiary retains ownership of the staked position but cannot access the tokens as liquid funds until the lock expires, which may be years away.

**Recommended Mitigation:**
Restrict `stakeReleasableTokens` to be callable only by the beneficiary or a designated trusted bot address. Introduce a `stakingBot` address variable set at construction, a setter restricted to the owner, and a combined `onlyBeneficiaryOrBot` modifier applied to `stakeReleasableTokens`.

---

**[中文版本]**

**描述：**
`SDLVesting::stakeReleasableTokens` 設計為僅由 Stake.Link 團隊運營的受信任質押機器人驅動，定期將新歸屬的 SDL 代幣鎖定到 SDLPool 中。然而，該函數目前沒有任何訪問控制——它是 `external` 且沒有任何限制調用者的修飾符。攻擊者可通過搶先執行受益人的 `release()` 交易來利用此漏洞：在受益人以流動性資金形式領取已歸屬代幣之前，攻擊者調用 `stakeReleasableTokens`，強制將所有可釋放代幣鎖定到受益人選擇的鎖定期（例如 4 年）的質押位置中。

**影響：**
對手可通過搶先執行受益人的 `release()` 交易並強制將所有可釋放代幣鎖定到長期質押位置，反復阻止受益人獲得已歸屬代幣的流動性訪問，受益人可能需要等待數年才能獲得流動資金。

**修復建議：**
限制 `stakeReleasableTokens` 僅可由受益人或指定的受信任機器人地址調用；在構建時引入 `stakingBot` 地址變量，添加所有者限制的設置函數，並將組合的 `onlyBeneficiaryOrBot` 修飾符應用於 `stakeReleasableTokens`。

---

## 7. Missing Check if Receiver is Whitelisted in StakingVault::mint, deposit

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::mint` and `StakingVault::deposit` apply the `onlyWhitelisted(msg.sender)` modifier to verify that the caller is whitelisted. However, neither function checks whether the `receiver` parameter — the address that will actually receive the minted shares — is also whitelisted. Since non-whitelisted addresses cannot withdraw, redeem, or transfer shares due to whitelist enforcement on those operations, any shares minted to a non-whitelisted receiver become permanently locked and unusable. The receiver has no way to move or redeem these shares unless they are subsequently added to the whitelist.

**Impact:**
A whitelisted user who accidentally or intentionally mints shares to a non-whitelisted `receiver` address causes permanent loss of the deposited funds for that receiver. The shares are locked in the vault with no ability to withdraw until the owner grants whitelist access to that address. This creates a pathway for funds to become permanently inaccessible through a simple input error.

**Recommended Mitigation:**
Add a whitelist check for the `receiver` parameter in both `StakingVault::mint` and `StakingVault::deposit` to ensure that shares cannot be minted to addresses that are not authorized to withdraw them.

---

**[中文版本]**

**描述：**
`StakingVault::mint` 和 `StakingVault::deposit` 應用 `onlyWhitelisted(msg.sender)` 修飾符驗證調用者是否在白名單中，但這兩個函數均未檢查 `receiver` 參數（實際接收鑄造份額的地址）是否也在白名單中。由於非白名單地址無法提款、贖回或轉移份額，任何鑄造給非白名單接收者的份額都將永久鎖定且無法使用，接收者無法在被添加到白名單之前移動或贖回這些份額。

**影響：**
在白名單中的用戶若意外或故意將份額鑄造給非白名單的 `receiver` 地址，會造成該接收者存入資金的永久損失，資金在金庫中被鎖定，直到所有者授予該地址白名單訪問權限。

**修復建議：**
在 `StakingVault::mint` 和 `StakingVault::deposit` 中為 `receiver` 參數添加白名單檢查，確保份額不能被鑄造給無授權提款的地址。

---

## 8. Missing Zero Address Validation for Authorized Signer in WorldLibertyFinancialV2.initialize()

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The `WorldLibertyFinancialV2::initialize()` function accepts an `_authorizedSigner` parameter that is critical for the `activateAccount()` function — the mechanism that allows legacy users to self-activate their accounts. The `initialize()` function passes this parameter directly to `_ownerSetAuthorizedSigner` without validating that it is not the zero address. The same missing validation exists in `ownerSetAuthorizedSigner`. If the zero address is ever set as the authorized signer — whether by mistake during deployment or through an erroneous admin call — the `activateAccount()` function becomes permanently broken: `ECDSA.recover()` never returns the zero address for any valid signature, so the `authorizedSigner() != ECDSA.recover(hash, _signature)` check will always fail, causing every `activateAccount()` call to revert with `InvalidSignature()`.

**Impact:**
If the authorized signer is set to the zero address, the `activateAccount()` function permanently reverts for all callers, completely disabling the legacy user account activation mechanism. There is no way for any legacy user to activate their account through this path until the authorized signer is corrected via an owner transaction.

**Recommended Mitigation:**
Add a zero address validation check in both `initialize()` and `ownerSetAuthorizedSigner()` that reverts if the provided `_authorizedSigner` is `address(0)`.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialV2::initialize()` 函數接受一個 `_authorizedSigner` 參數，這對 `activateAccount()` 函數至關重要——該機制允許遺留用戶自行激活賬戶。`initialize()` 函數將此參數直接傳遞給 `_ownerSetAuthorizedSigner`，未驗證其是否為零地址。`ownerSetAuthorizedSigner` 中也存在同樣的缺失驗證。若零地址被設置為授權簽名者，`activateAccount()` 函數將永久失效：`ECDSA.recover()` 對任何有效簽名都不會返回零地址，導致所有 `activateAccount()` 調用以 `InvalidSignature()` 回滾。

**影響：**
若授權簽名者被設置為零地址，`activateAccount()` 函數將對所有調用者永久回滾，完全禁用遺留用戶賬戶激活機制，直到所有者更正授權簽名者。

**修復建議：**
在 `initialize()` 和 `ownerSetAuthorizedSigner()` 中添加零地址驗證檢查，若提供的 `_authorizedSigner` 為 `address(0)` 則回滾。

---

## 9. Reusable Authentication Signatures Due to Missing Nonce

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**
The `DIDContract` implements an `authenticate` function that verifies user authentication through an ECDSA signature constructed from the DID, verification method, timestamp, and `msg.sender`. However, the function incorporates no nonce, replay counter, or signature-tracking mechanism. The message hash is fully deterministic for any given set of inputs and contains no unique per-request value. As a result, any valid signature remains reusable for the entire duration of the `proof.timestamp` window (5 minutes). Any actor who obtains a valid authentication signature — whether the original signer or an attacker who captures it — can replay that same signature multiple times against the contract, and each replay will succeed. Each successful replay triggers `_updateUserStats(msg.sender)`, inflating on-chain activity records.

**Impact:**
Repeated reuse of the same authentication signature enables unauthorized replay of authentication attempts, artificially inflates user activity statistics through repeated updates to internal stats, and produces misleading and noisy audit trails. Although the attack does not directly grant elevated privileges, it degrades the reliability of authentication records and may enable secondary misuse such as spamming contract events or triggering unintended rate-dependent logic that relies on authentication frequency.

**Recommended Mitigation:**
Incorporate a per-user nonce parameter in the `authenticate` function and include it in the signature validation hash. Each successful authentication should increment the nonce, ensuring that previously issued signatures immediately become invalid after use.

---

**[中文版本]**

**描述：**
`DIDContract` 實作的 `authenticate` 函數通過由 DID、驗證方法、時間戳和 `msg.sender` 構成的 ECDSA 簽名驗證用戶身份。然而，該函數未包含任何 nonce、重放計數器或簽名跟踪機制。消息哈希對於任何給定的輸入集合完全確定，不包含任何唯一的每請求值。因此，任何有效簽名在 `proof.timestamp` 窗口（5 分鐘）內均可被重用。獲得有效認證簽名的任何人（無論是原始簽名者還是攻擊者）都可以多次重放該簽名，每次重放都會成功並觸發 `_updateUserStats(msg.sender)`。

**影響：**
重復重用相同的認證簽名可實現未授權的認證重放，人為地虛報鏈上活動統計數據，產生誤導性的審計跟蹤，並可能觸發依賴認證頻率的速率相關邏輯。

**修復建議：**
在 `authenticate` 函數中加入每用戶 nonce 參數，並將其包含在簽名驗證哈希中；每次成功認證後遞增 nonce，確保先前發出的簽名在使用後立即失效。

---

## 10. Vault Initialization Allows Deposit Whitelist with No Management Capability

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
The `VaultTokenized` contract initialization logic contains a gap in its whitelist configuration validation. When `params.depositWhitelistSetRoleHolder` is set to a non-zero address (granting someone the ability to toggle the whitelist on or off), the validation that would ensure consistent whitelist management is bypassed. Specifically, the check that verifies a `depositorWhitelistRoleHolder` is present when the whitelist is enabled only runs when `params.depositWhitelistSetRoleHolder == address(0)`. This means a vault can be initialized with `depositWhitelist = true` (deposits restricted to whitelisted addresses), `depositWhitelistSetRoleHolder = someAddress` (someone can toggle the whitelist), and `depositorWhitelistRoleHolder = address(0)` (no one can add addresses to the whitelist) — all at once, without triggering any validation error.

**Impact:**
When a vault is initialized in this inconsistent state, deposits are restricted to whitelisted addresses but no address can be added to the whitelist. All deposit attempts revert immediately. The only recourse is to use the `depositWhitelistSetRoleHolder` to disable the whitelist entirely, which defeats the purpose of having a whitelist. The vault is effectively bricked for deposits until the whitelist is turned off.

**Recommended Mitigation:**
Modify the initialization validation logic to check for consistent whitelist configuration regardless of whether `depositWhitelistSetRoleHolder` is set. Specifically, if `depositWhitelist = true` and `depositorWhitelistRoleHolder = address(0)`, the initialization should revert with `Vault__MissingRoles`.

---

**[中文版本]**

**描述：**
`VaultTokenized` 合約初始化邏輯在白名單配置驗證中存在缺口。當 `params.depositWhitelistSetRoleHolder` 被設置為非零地址時，確保一致白名單管理的驗證被繞過。具體來說，在白名單啟用時驗證 `depositorWhitelistRoleHolder` 是否存在的檢查，僅在 `params.depositWhitelistSetRoleHolder == address(0)` 時才運行。這意味著金庫可以在以下狀態下初始化：`depositWhitelist = true`（存款限制於白名單地址）、`depositWhitelistSetRoleHolder = someAddress`（某人可以切換白名單）、`depositorWhitelistRoleHolder = address(0)`（沒有人可以向白名單添加地址）——三者同時存在，而不觸發任何驗證錯誤。

**影響：**
在此不一致狀態下初始化的金庫，存款被限制於白名單地址，但沒有地址可以被添加到白名單，導致所有存款嘗試立即回滾。唯一的解決方法是完全禁用白名單，這使得白名單的存在失去意義。

**修復建議：**
修改初始化驗證邏輯，無論 `depositWhitelistSetRoleHolder` 是否被設置，都檢查白名單配置的一致性；具體而言，若 `depositWhitelist = true` 且 `depositorWhitelistRoleHolder = address(0)`，初始化應以 `Vault__MissingRoles` 回滾。

---

## 11. Weak Signature Validation in Account Activation

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The `WorldLibertyFinancialV2::activateAccount` function uses a simple `keccak256(abi.encode(account))` hash for signature validation instead of following EIP-712 typed data standards. Although the contract initializes the EIP-712 infrastructure during setup via `__EIP712_init`, the activation function bypasses this infrastructure entirely and constructs its own non-standard digest from only the account address. This deviation from established security best practices means the signature does not incorporate domain separation data such as the chain ID or the verifying contract address. Signatures generated for one deployment or one chain can therefore be replayed against any other deployment of the same contract on the same chain, or — if the protocol expands to multiple chains in the future — against deployments on different chains.

**Impact:**
If the protocol is ever deployed on multiple chains, account activation signatures generated for one chain can be replayed on any other chain where the same contract is deployed. Similarly, if the contract is migrated to a new proxy or implementation address, activation signatures generated for the current deployment would remain valid against the new deployment. The practical risk is currently limited by single-chain deployment and double-activation protection, but the design introduces unnecessary future risk.

**Recommended Mitigation:**
Replace the simple hash with a proper EIP-712 typed data digest that includes the domain separator (embedding chain ID and verifying contract address). Use the already-initialized `_hashTypedDataV4` infrastructure that the contract has set up, ensuring activation signatures are bound to a specific chain and contract deployment.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialV2::activateAccount` 函數使用簡單的 `keccak256(abi.encode(account))` 哈希進行簽名驗證，而非遵循 EIP-712 類型化數據標準。雖然合約在設置期間通過 `__EIP712_init` 初始化了 EIP-712 基礎設施，但激活函數完全繞過了這一基礎設施，僅從賬戶地址構建了自己的非標準摘要。這種偏離不包含域分隔數據（如鏈 ID 或驗證合約地址），導致簽名可在同一合約的任何其他部署之間被重放。

**影響：**
若協議部署到多條鏈上，為一條鏈生成的賬戶激活簽名可在任何其他鏈上重放；若合約遷移到新的代理或實作地址，當前部署的激活簽名對新部署仍然有效。目前由於單鏈部署和雙重激活保護，實際風險有限，但此設計引入了不必要的未來風險。

**修復建議：**
將簡單哈希替換為適當的 EIP-712 類型化數據摘要，包含域分隔符（嵌入鏈 ID 和驗證合約地址）；使用合約已設置的 `_hashTypedDataV4` 基礎設施，確保激活簽名綁定到特定的鏈和合約部署。
