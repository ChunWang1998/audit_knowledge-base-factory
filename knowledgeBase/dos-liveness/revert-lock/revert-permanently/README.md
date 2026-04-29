# revert-permanently (18)

> Issues causing permanent irrecoverable locks — tokens permanently trapped, functions always reverting, or state with no exit path.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Expired Tokens Permanently Trapped

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/S3 Markets.txt`

**Description:**
The `CustodyVault` contract acts as a centralized custodian for EAC1155 tokens and maintains internal ledgers (`freeBalance`, `lockedBalance`) for buyers. A logic flaw in the vault prevents any action on expired tokens — once a token reaches its expiration timestamp, every state-changing function that touches token balances enforces a strict `require(!token.isExpired(id))` check at the very beginning. This includes `withdrawToExternal`, all variants of `retire`, `unlock`, and `internalTransfer`. As a result tokens that expire while sitting in the vault can never be withdrawn, retired, unlocked, or internally moved again.

**Impact:**
User balances for expired tokens are permanently bricked. Tokens cannot be utilized, claimed, or removed from the vault, effectively turning the vault into a one-way trap for any asset that reaches its expiry. Storage slots remain occupied indefinitely and the OPS_ROLE has no administrative cleanup path.

**Recommended Mitigation:**
Remove the `require(!token.isExpired(id))` check from the retire family of functions. Retirement is the standard way to handle expired or used assets. Ensure the underlying EAC1155 burn function also permits burning expired tokens. Alternatively, introduce dedicated `resolveExpired` / `resolveExpiredBatch` functions restricted to `OPS_ROLE` that allow burning expired tokens outside the normal accounting flow.

---

**[中文版本]**

**描述：**
`CustodyVault` 合約作為 EAC1155 代幣的中央託管方，在內部為買家維護 `freeBalance`、`lockedBalance` 帳本。合約的邏輯缺陷在於：幾乎所有涉及代幣餘額的狀態變更函數（`withdrawToExternal`、全系列 `retire`、`unlock`、`internalTransfer`）在入口處都強制執行 `require(!token.isExpired(id))` 驗證。一旦代幣到期，上述所有操作均會立即 revert，導致已到期的代幣永遠無法被提取、銷毀、解鎖或移動。

**影響：**
用戶持有的已到期代幣餘額被永久凍結在 vault 中，無法取出或清理，使 vault 成為資產的單向陷阱，存儲槽永遠被佔用，`OPS_ROLE` 亦無任何管理清理路徑。

**修復建議：**
從 retire 系列函數中移除 `require(!token.isExpired(id))` 檢查；確保底層 EAC1155 的 burn 函數同樣允許銷毀已到期代幣。或引入僅限 `OPS_ROLE` 調用的 `resolveExpired` / `resolveExpiredBatch` 函數，允許在正常計費流程之外對已到期代幣進行清理銷毀。

---

## 2. Permanent Phantom Stake Accumulation Due to Missing Effective Stake Cleanup on Re-delegation

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
A significant accounting vulnerability exists in the `Stargate.sol` contract's delegation mechanism. When users re-delegate their tokens from `EXITED` or `PENDING` status to a new validator, the `_delegate()` function correctly increases the effective stake for the new validator but fails to decrease the effective stake from the old validator. This creates a permanent inflation of `delegatorsEffectiveStake` that can never be cleaned up without a contract upgrade. The contrast with the correct implementation is visible in `requestDelegationExit`, which properly calls `_updatePeriodEffectiveStake` with `false` to decrement the old validator's stake.

**Impact:**
The total effective stake across all validators becomes permanently inflated by phantom stake amounts. The fundamental protocol invariant — that total effective stake should equal the sum of all active delegations — is broken. Phantom stake dilutes rewards for all honest validators, and the effect worsens cumulatively with every re-delegation event.

**Recommended Mitigation:**
Add effective stake cleanup logic inside `_delegate` when re-delegating from `EXITED` or `PENDING` status. Before increasing the new validator's effective stake, call `_updatePeriodEffectiveStake` with `false` for the old validator, mirroring the logic already present in `requestDelegationExit`.

---

**[中文版本]**

**描述：**
`Stargate.sol` 的委派機制存在嚴重的計費漏洞。當用戶從 `EXITED` 或 `PENDING` 狀態重新委派至新驗證者時，`_delegate()` 函數正確地增加了新驗證者的有效質押，但卻沒有相應地減少舊驗證者的有效質押。對比正確實現（`requestDelegationExit` 中通過 `false` 參數調用 `_updatePeriodEffectiveStake` 完成清理），可以清楚看到缺失的邏輯，導致 `delegatorsEffectiveStake` 永久膨脹且無法在不升級合約的情況下修正。

**影響：**
所有驗證者的總有效質押量被幽靈質押永久虛增，「總有效質押 = 所有活躍委派之和」的基本不變量被打破，所有誠實驗證者的獎勵因此被稀釋，且每次重新委派都會累積加劇此問題。

**修復建議：**
在 `_delegate` 函數內處理從 `EXITED` 或 `PENDING` 狀態重新委派的場景時，在增加新驗證者有效質押之前，先以 `false` 參數對舊驗證者調用 `_updatePeriodEffectiveStake`，鏡像 `requestDelegationExit` 中的現有邏輯。

---

## 3. Proposal Fee Permanently Locked on Rejection

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
In the `ModelRegistryUpgradeable` contract, users proposing a new model for community approval must pay a 100 FAB token proposal fee to prevent spam. The fee is only returned to the proposer if the proposal is approved — `executeProposal` contains a `governanceToken.safeTransfer` call to the proposer inside the `if (approved)` branch. When a proposal is rejected the 100 FAB fee remains permanently locked in the contract. The contract has no `rescueTokens` function, no owner sweep function, no treasury forwarding, and no burn mechanism for accumulated rejected fees.

**Impact:**
Every rejected proposal irreversibly locks 100 FAB tokens inside the contract. Over the protocol lifetime, significant amounts of FAB become permanently inaccessible, constituting a compounding loss for the ecosystem.

**Recommended Mitigation:**
Track rejected proposal fees with a dedicated accumulator and add an owner-callable sweep function. In `executeProposal`, when the proposal is not approved, increment `accumulatedRejectedFees` and provide a governance function to transfer or burn those funds.

---

**[中文版本]**

**描述：**
`ModelRegistryUpgradeable` 合約中，用戶提議新模型時需支付 100 FAB 提案費用以防止垃圾提案。`executeProposal` 中只有在提案被批准的 `if (approved)` 分支裡才將費用退還給提案人。提案被拒絕時，100 FAB 費用永久滯留在合約中；合約既無 `rescueTokens` 函數，也無擁有者提款、國庫轉帳或銷毀機制。

**影響：**
每次被拒絕的提案都會不可逆地鎖定 100 FAB，隨著協議運行時間增長，合約中積累的永久不可訪問 FAB 數量將持續增加，造成生態系統的累積損失。

**修復建議：**
使用專用計數器追蹤被拒絕的提案費用，並新增一個只有擁有者可調用的提款函數。在 `executeProposal` 的非批准分支中，遞增 `accumulatedRejectedFees`，並提供治理函數以轉移或銷毀這些資金。

---

## 4. Staking Capacity Permanently Lost as Stakes Complete

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The `totalStaked` counter in `StakingAndRewards.sol` is never decremented when stakes complete naturally by reaching the 2x reward limit. When `_processFIFOStakeInactivity` marks a stake as inactive and removes it from active accounting, only `totalActiveStaked` is decremented. However, the staking validation checks use `totalStaked` (not `totalActiveStaked`) to determine whether new stakes are allowed: `require(totalStaked + amount <= contractBalance, ...)` and `require(potentialTotalStaked <= contractBalance / 2, ...)`. As more stakes complete, `totalStaked` accumulates while actual locked tokens decrease, progressively tightening the cap until no new stakes are possible.

**Impact:**
The system degrades progressively: as stakes complete naturally, the inflated `totalStaked` counter causes staking validation to fail even when the contract holds ample free capacity. Eventually the staking system becomes completely unusable for new participants, constituting a permanent protocol death for the staking module.

**Recommended Mitigation:**
Replace `totalStaked` with `totalActiveStaked` in the staking validation checks. The correctly maintained `totalActiveStaked` counter accurately reflects currently locked tokens and should be the basis for capacity enforcement.

---

**[中文版本]**

**描述：**
`StakingAndRewards.sol` 中的 `totalStaked` 計數器在質押自然到期（達到 2x 獎勵上限）時從未被遞減。`_processFIFOStakeInactivity` 將質押標記為非活躍時只遞減 `totalActiveStaked`，而質押驗證邏輯使用的是 `totalStaked` 來判斷是否允許新質押。隨著越來越多的質押完成，`totalStaked` 持續累積但實際鎖定代幣減少，逐步收緊容量限制。

**影響：**
系統漸進式降級——隨著質押自然完成，虛增的 `totalStaked` 導致質押驗證失敗，即使合約持有充足的空閒容量。最終質押系統對新參與者完全不可用，質押模塊永久失效。

**修復建議：**
將質押驗證邏輯中的 `totalStaked` 替換為 `totalActiveStaked`。`totalActiveStaked` 計數器維護正確，準確反映當前鎖定代幣數量，應作為容量執行的依據。

---

## 5. `AdminRegistry::proposeAdmin` Self-Proposal Permanently Removes `DEFAULT_ADMIN_ROLE`

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`AdminRegistry::proposeAdmin` has no guard against an admin proposing their own address as the new admin. When the current admin subsequently calls `acceptAdmin`, the sequence `_grantRole(DEFAULT_ADMIN_ROLE, pendingAdmin)` is a no-op because the pending admin (same address) already holds the role, then `_revokeRole(DEFAULT_ADMIN_ROLE, oldAdmin)` strips it. After the call the `admin` state variable still points to the address, but it no longer holds `DEFAULT_ADMIN_ROLE`. Every `hasRole(DEFAULT_ADMIN_ROLE, ...)` check fails permanently. There is no recovery path. This can happen accidentally (e.g., admin testing the mechanism) or maliciously (a compromised key griefing the protocol).

**Impact:**
Permanent loss of all `DEFAULT_ADMIN_ROLE`-gated functions: upgrading contracts, role management, setting exchange/treasury addresses. The protocol becomes permanently non-upgradeable and unmanageable.

**Recommended Mitigation:**
Add a self-proposal guard in `proposeAdmin` that reverts if `newAdmin == admin` (i.e., `require(newAdmin != admin, "cannot self-propose")`).

---

**[中文版本]**

**描述：**
`AdminRegistry::proposeAdmin` 沒有防止管理員將自身地址提議為新管理員的保護。當前管理員隨後調用 `acceptAdmin` 時，`_grantRole(DEFAULT_ADMIN_ROLE, pendingAdmin)` 是空操作（因為待定管理員即當前地址，已持有該角色），緊接著 `_revokeRole(DEFAULT_ADMIN_ROLE, oldAdmin)` 將該角色從同一地址撤銷。調用後 `admin` 狀態變量仍指向該地址，但其已不再持有 `DEFAULT_ADMIN_ROLE`，且沒有任何恢復路徑。此操作可能為誤操作（如管理員測試機制）或惡意行為（被盜私鑰破壞協議）。

**影響：**
永久喪失所有 `DEFAULT_ADMIN_ROLE` 守護的功能：合約升級、角色管理、設置交易所/財庫地址等。協議永久無法升級和管理。

**修復建議：**
在 `proposeAdmin` 中增加自提議保護，當 `newAdmin == admin` 時 revert（即 `require(newAdmin != admin, "cannot self-propose")`）。

---

## 6. Don't Add Duplicate `documentHash` to `DocumentManager::DocumentStorage::_docHashes` When Overwriting via `_setDocument` as This Causes Panic Revert When Calling `_removeDocument`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DocumentManager::_setDocument` intentionally allows overwriting an existing document, but when overwriting it unconditionally calls `$._docHashes.push(documentHash)`, appending the same hash a second time to `_docHashes`. The `_removeDocument` function iterates the array to find and swap-pop the matching hash, but when the hash appears twice it leaves a stale duplicate after the first removal and causes an array out-of-bounds panic on the second occurrence.

**Impact:**
Once a document hash has been duplicated in `_docHashes`, calling `_removeDocument` with that hash causes a panic revert. The document becomes impossible to remove, permanently occupying storage and blocking any downstream logic that depends on document removal.

**Recommended Mitigation:**
In `_setDocument`, check whether `documentHash` already exists in `_docHashes` before pushing and skip the push if already present. Alternatively use OpenZeppelin `EnumerableSet` for `_docHashes` which inherently prevents duplicates. Additionally add a `break` in `_removeDocument` to exit the loop once the element has been found and removed.

---

**[中文版本]**

**描述：**
`DocumentManager::_setDocument` 允許覆寫已有文件，但覆寫時無條件調用 `$._docHashes.push(documentHash)`，將相同的哈希值第二次追加到 `_docHashes` 數組。`_removeDocument` 通過遍歷找到並 swap-pop 對應哈希，但當哈希出現兩次時，第一次移除後留下舊副本，在第二次訪問時引發數組越界 panic。

**影響：**
一旦文件哈希在 `_docHashes` 中出現重複，調用 `_removeDocument` 會觸發 panic revert，該文件無法被移除，永久佔用存儲，並阻塞所有依賴文件移除的下游邏輯。

**修復建議：**
在 `_setDocument` 中，push 之前先檢查 `documentHash` 是否已存在於 `_docHashes`，若存在則跳過追加。或改用 OpenZeppelin `EnumerableSet` 存儲 `_docHashes` 以天然防止重複。同時在 `_removeDocument` 的遍歷中找到並刪除目標元素後立即 `break`。

---

## 7. Excess Contributions Become Permanently Locked Due to Non-Exact Deposit Enforcement

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
The `Komiti` contract's join and contribute functions all validate user deposits using a greater-than-or-equal check (`require(msg.value >= group.perShareAmount)`), allowing users to send more funds than required. However, the payout mechanism in `Komiti::distributeFunds` only distributes `perShareAmount * members.length` — the exact minimum. Any amount contributed above `perShareAmount` is not refunded, not redistributed, and not withdrawable. These surplus funds accumulate inside the contract with no recovery mechanism.

**Impact:**
All excess contributions become permanently locked in the contract as unrecoverable ether, effectively an unintentional ether sink growing with every overpayment.

**Recommended Mitigation:**
Enforce exact contribution amounts by replacing all `>=` checks with strict equality (`require(msg.value == group.perShareAmount)`). Alternatively, redesign the distribution mechanism to distribute all collected funds, or introduce an admin refund mechanism that can sweep leftover amounts after distribution.

---

**[中文版本]**

**描述：**
`Komiti` 合約的加入和貢獻函數均使用大於等於驗證（`require(msg.value >= group.perShareAmount)`），允許用戶多付款。但 `distributeFunds` 的派發機制只分配 `perShareAmount * 成員數`，任何超出 `perShareAmount` 的餘額既不退款、不再分配，也無法提取，在合約中持續累積。

**影響：**
所有超額貢獻永久鎖定在合約中，成為隨每次多付而增長的不可恢復的以太幣沉洞。

**修復建議：**
將所有 `>=` 校驗改為嚴格相等（`require(msg.value == group.perShareAmount)`）以強制精確付款；或重新設計分配機制確保所有收款均被分配；或引入管理員退款機制，允許在分配後清掃剩餘金額。

---

## 8. Excessive `maximumContestants` Could Make Games Revert in `DefaultSession::recordResults` Due to Out of Gas

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::maximumContestants` is initialized to 1,000,000. `DefaultSession::recordResults` iterates over all winners in a nested loop — for each winner it iterates over all question IDs and calls `IPromptStrategy(promptStrategy).recordResult(...)`. With a 30M block gas limit and approximately 280,587 gas per winner with two questions, the practical maximum is roughly 100 winners. Conservative estimates for games with 10 questions yield approximately 296 winners maximum before hitting the block gas limit.

**Impact:**
Games with more contestants than can be processed in a single block will be unable to conclude. `recordResults` will always revert due to out of gas, permanently trapping participant funds and preventing reward distribution.

**Recommended Mitigation:**
Set a realistic `maximumContestants` limit of approximately 1,000 participants. Alternatively, keep the winners array but introduce a chunked `recordResult` function that allows processing winners in batches across multiple transactions.

---

**[中文版本]**

**描述：**
`SessionManager::maximumContestants` 初始化為 1,000,000。`DefaultSession::recordResults` 對所有獲勝者進行嵌套循環——每位獲勝者都要遍歷所有問題 ID 並調用 `recordResult`。在 30M 的區塊 Gas 限制下，兩道題目情況下每位獲勝者消耗約 280,587 gas，實際最大可處理約 100 名獲勝者；10 題情況下約 296 名。

**影響：**
參賽者超出單區塊可處理上限的遊戲將無法完成，`recordResults` 會因 out-of-gas 永久 revert，參與者資金被永久鎖定，獎勵無法分配。

**修復建議：**
將 `maximumContestants` 設置為約 1,000 的合理上限；或保留獲勝者數組，引入分塊 `recordResult` 函數，允許跨多個交易分批處理獲勝者。

---

## 9. `Getters::getCollateralSurplus` Returns Positive Values Even When `Surplus::processSurplus` Is Guaranteed to Revert

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
The view function `Getters::getCollateralSurplus` computes and returns a positive surplus value for a collateral even when the global collateral ratio is below the `surplusBufferRatio`. However, `Surplus::processSurplus` always reverts in this situation due to an explicit post-swap check: `if (collatRatio < ts.surplusBufferRatio) revert Undercollateralized()`. This means a positive return from the getter does not guarantee that the process call will succeed, creating a misleading interface that can cause governance actors to waste gas and time triggering always-reverting transactions.

**Impact:**
Governance actors relying on `getCollateralSurplus` returning a positive value as a signal that surplus can be processed will repeatedly trigger transactions that always revert when the system is globally under-buffered. Strategy yield accumulates in the manager but can never be captured as distributable tokenP.

**Recommended Mitigation:**
Update `Getters::getCollateralSurplus` to revert with a custom error (e.g., `SurplusNotProcessable`) when the global collateral ratio is below `surplusBufferRatio`, making the getter accurately signal whether the corresponding process call can succeed.

---

**[中文版本]**

**描述：**
視圖函數 `Getters::getCollateralSurplus` 在全局抵押率低於 `surplusBufferRatio` 時仍然返回正的盈餘值，但 `Surplus::processSurplus` 在此情況下因 `if (collatRatio < ts.surplusBufferRatio) revert Undercollateralized()` 的後置校驗而必然 revert。這造成 getter 的返回值具有誤導性，使治理操作者誤以為可以處理盈餘。

**影響：**
依賴 `getCollateralSurplus` 返回正值作為可處理信號的治理操作者，在系統全局抵押不足時將反覆觸發必然 revert 的交易；策略收益在管理器中累積卻永遠無法被捕獲為可分配的 tokenP。

**修復建議：**
更新 `Getters::getCollateralSurplus`，當全局抵押率低於 `surplusBufferRatio` 時以自定義錯誤（如 `SurplusNotProcessable`）revert，使 getter 準確反映對應的 process 調用是否可以成功。

---

## 10. `IERC7160` Specification Requires `hasPinnedTokenURI` to Revert for Non-Existent `tokenId`

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
Per the `IERC7160` specification, `hasPinnedTokenURI` MUST revert if the token does not exist. The current implementation simply reads `_hasPinnedTokenURI[tokenId]` and returns `false` for non-existent tokens (or even `true` if a token was burned while pinned, since burning does not clear `_hasPinnedTokenURI`). This violates the specification and can mislead callers that rely on a revert to detect non-existent tokens.

**Impact:**
Off-chain clients and on-chain integrators conforming to the IERC7160 specification will receive incorrect data for non-existent token IDs rather than the expected revert, leading to silent misinformation about token pin state.

**Recommended Mitigation:**
Add the `onlyIfTokenExists` modifier to `hasPinnedTokenURI` so it reverts for non-existent token IDs, bringing the implementation into compliance with the IERC7160 specification.

---

**[中文版本]**

**描述：**
`IERC7160` 規範要求 `hasPinnedTokenURI` 在代幣不存在時必須 revert。當前實現直接讀取 `_hasPinnedTokenURI[tokenId]` 映射：對不存在的代幣返回 `false`（或若代幣在 pin 狀態下被銷毀則返回 `true`，因銷毀不清除該映射），違反了規範，可能誤導依賴 revert 來檢測不存在代幣的調用方。

**影響：**
遵循 IERC7160 規範的鏈下客戶端和鏈上集成方，對不存在的 tokenId 會收到錯誤數據而非預期的 revert，導致關於代幣 pin 狀態的靜默誤報。

**修復建議：**
為 `hasPinnedTokenURI` 添加 `onlyIfTokenExists` 修飾符，使其對不存在的 tokenId revert，使實現符合 IERC7160 規範。

---

## 11. `IERC7160` Specification Requires `pinTokenURI` to Revert for Non-Existent `tokenId`

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
Per the `IERC7160` specification, `pinTokenURI` MUST revert if the token does not exist. The current implementation does not enforce this — `_tokenURIs` is a mapping to a fixed-size `string[2]` array, so `_tokenURIs[tokenId].length` always equals 2 for any `tokenId`, including non-existent ones. The bounds check `if (index >= _tokenURIs[tokenId].length)` therefore never reverts for valid index values (0 or 1), allowing the pin state of non-existent tokens to be silently modified.

**Impact:**
Pinning a non-existent token ID silently succeeds and emits `TokenUriPinned` and `MetadataUpdate` events for phantom tokens, violating the specification and potentially corrupting metadata state for future tokens minted with the same ID.

**Recommended Mitigation:**
Add the `onlyIfTokenExists` modifier to `pinTokenURI` so it reverts for non-existent token IDs, bringing the implementation into compliance with the IERC7160 specification.

---

**[中文版本]**

**描述：**
`IERC7160` 規範要求 `pinTokenURI` 在代幣不存在時必須 revert。當前實現無此保護——`_tokenURIs` 映射值為固定大小 `string[2]` 數組，`_tokenURIs[tokenId].length` 對任何 `tokenId`（包括不存在的）始終等於 2，因此 `index < 2` 的邊界校驗永遠不會 revert，允許靜默修改不存在代幣的 pin 狀態。

**影響：**
對不存在的 tokenId 執行 pin 操作會靜默成功並觸發 `TokenUriPinned` 和 `MetadataUpdate` 事件，違反規範，並可能污染未來以相同 ID 鑄造的代幣的元數據狀態。

**修復建議：**
為 `pinTokenURI` 添加 `onlyIfTokenExists` 修飾符，使其對不存在的 tokenId revert，以符合 IERC7160 規範。

---

## 12. Insufficient Validation in `AvalancheL1Middleware::removeOperator` Can Create Permanent Validator Lockup

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::disableOperator` and `removeOperator` lack validation to ensure operators have no active nodes before removal. Once an operator is removed from the `operators` set, the `onlyRegisteredOperatorNode` modifier and the `forceUpdateNodes` function both check `operators.contains(operator)` and revert for removed operators. Node management functions — including `removeNode` — become permanently inaccessible for removed operators because the access modifier blocks them. The operator's nodes remain in storage with cached stake but can never be cleaned up.

**Impact:**
Premature removal of an operator with active nodes creates three permanent problems: (1) validator nodes are locked on the P-Chain and cannot exit; (2) remaining operators suffer disproportionate stake reductions during undelegations because orphaned nodes are not properly accounted for; (3) removed operators' nodes cannot be rebalanced.

**Recommended Mitigation:**
Allow operator removal only if all active nodes of that operator have already been removed. Add a check in `removeOperator` that reverts if `operatorNodes[operator].length() > 0`.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware::disableOperator` 和 `removeOperator` 缺少在移除前確認運營商無活躍節點的驗證。一旦運營商從 `operators` 集合中移除，`onlyRegisteredOperatorNode` 修飾符和 `forceUpdateNodes` 函數均會對已移除運營商 revert，所有節點管理函數（包括 `removeNode`）永久無法訪問，運營商的節點和緩存質押保留在存儲中無法清理。

**影響：**
過早移除有活躍節點的運營商造成三個永久問題：(1) 驗證節點在 P-Chain 上被鎖定無法退出；(2) 孤立節點未被正確計入，導致其餘運營商在解除委派時承受不成比例的質押減少；(3) 已移除運營商的節點無法重新平衡。

**修復建議：**
僅在運營商的所有活躍節點均已移除後才允許移除運營商；在 `removeOperator` 中增加校驗，若 `operatorNodes[operator].length() > 0` 則 revert。

---

## 13. No Way to Revert `setInvestorLiquidateOnly`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`InvestorLockManagerBase::setInvestorLiquidateOnly` contains a logic error that prevents disabling liquidate-only mode once it has been enabled. The function has a `require(!investorsLiquidateOnly[_investorId], "Investor is already in liquidate only mode")` check that reverts whenever the investor is already in liquidate-only mode — regardless of whether the caller is trying to disable it. This means the `_enabled` parameter is effectively ignored when the current state is `true`, making the toggle one-directional.

**Impact:**
Once an investor is placed in liquidate-only mode there is no way to restore normal trading access. The restriction is irreversible through the normal admin API, permanently affecting the investor's ability to perform non-liquidate operations.

**Recommended Mitigation:**
Remove the `require(!investorsLiquidateOnly[_investorId], ...)` check entirely to allow free toggling of the state. Alternatively replace it with `require(investorsLiquidateOnly[_investorId] != _enabled, "State unchanged")` to prevent redundant calls while still allowing disabling.

---

**[中文版本]**

**描述：**
`InvestorLockManagerBase::setInvestorLiquidateOnly` 存在邏輯錯誤，導致一旦啟用「僅清算」模式後便無法禁用。函數中的 `require(!investorsLiquidateOnly[_investorId], ...)` 在投資者當前已處於僅清算模式時始終 revert——無論調用者是否意圖禁用該狀態——使 `_enabled` 參數在 `true` 狀態下形同虛設。

**影響：**
投資者一旦被設置為僅清算模式，就無法通過正常管理 API 恢復，永久限制其進行非清算操作的能力。

**修復建議：**
刪除 `require(!investorsLiquidateOnly[_investorId], ...)` 校驗以允許自由切換狀態；或將其替換為 `require(investorsLiquidateOnly[_investorId] != _enabled, "State unchanged")` 以防止冗餘調用，同時允許禁用操作。

---

## 14. Revert Fast by Performing Input-Related Checks Prior to Storage Reads and External Calls

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
Several functions in the Sablier Bob codebase perform storage reads and external calls before validating basic input parameters. Specifically, `SablierBob::enter` reads storage before checking the `amount` parameter, and `SablierBob::updateStakedTokenBalance` reads storage before checking `userShareBalanceBeforeTransfer`. Failing fast on input validation is a best practice that saves gas for callers providing invalid inputs and makes revert reasons clearer.

**Impact:**
Callers providing invalid inputs pay unnecessary gas for storage reads and external calls before the transaction reverts. The revert message may be less informative since the failure occurs at a later step rather than at the input boundary.

**Recommended Mitigation:**
Move all input-related validation checks to the top of each function, before any storage reads or external calls, so that invalid inputs fail fast with a clear revert reason and minimal gas cost.

---

**[中文版本]**

**描述：**
Sablier Bob 代碼庫中的多個函數在驗證基本輸入參數之前就已進行存儲讀取和外部調用：`SablierBob::enter` 在校驗 `amount` 前讀取存儲，`SablierBob::updateStakedTokenBalance` 在校驗 `userShareBalanceBeforeTransfer` 前讀取存儲。盡早失敗（fail-fast）是節省 gas 並使 revert 原因更清晰的最佳實踐。

**影響：**
提供無效輸入的調用者需為不必要的存儲讀取和外部調用支付多餘的 gas；且由於失敗發生在較後的步驟，revert 信息可能不夠直觀。

**修復建議：**
將所有輸入相關的校驗移至每個函數最頂部，在任何存儲讀取或外部調用之前執行，確保無效輸入以最低 gas 成本和清晰的 revert 原因快速失敗。

---

## 15. `RewardHandler` May Revert Due to Receiving Less Than Expected

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
`RewardHandler::sellRewards` calls the ODOS router and decodes the returned `amountOut`. For managed collateral, it then calls `IERC20(collateral).safeTransfer(LibManager.transferRecipient(...), amountOut)`. The ODOS router calculates `amountOut` as the balance change in its own contract but then performs a referral fee transfer to a beneficiary that can silently send 1–2 wei less than expected due to fee-on-transfer or rounding behavior in some tokens. This means the actual amount transferred to the Parallelizer is lower than `amountOut`, causing `safeTransfer` with that `amountOut` to revert because the contract holds insufficient balance.

**Impact:**
`RewardHandler::sellRewards` becomes permanently DOSed for managed collateral whenever the ODOS router's reported `amountOut` overstates the amount actually received. Strategy rewards cannot be sold and converted, permanently blocking yield capture for managed collateral.

**Recommended Mitigation:**
Use a balance-before / balance-after pattern to determine the actual amount received from the ODOS router rather than trusting the returned `amountOut` value. Transfer only what was actually received.

---

**[中文版本]**

**描述：**
`RewardHandler::sellRewards` 調用 ODOS 路由器後解碼返回的 `amountOut`，對托管抵押品隨即調用 `safeTransfer(recipient, amountOut)`。然而 ODOS 路由器以自身合約的餘額變化計算 `amountOut`，並在之後向推薦人轉賬，由於部分代幣的手續費或捨入行為，實際轉給 Parallelizer 的金額可能比 `amountOut` 少 1-2 wei，導致 `safeTransfer` 因餘額不足而 revert。

**影響：**
只要 ODOS 路由器報告的 `amountOut` 高於實際收到金額，`RewardHandler::sellRewards` 對托管抵押品就會永久 revert，策略獎勵無法被出售和轉換，托管抵押品的收益捕獲被永久阻塞。

**修復建議：**
使用余額前/后模式（balance-before/balance-after）確定從 ODOS 路由器實際收到的金額，而非信任返回的 `amountOut`，僅轉移實際收到的數量。

---

## 16. Same Wallet Can Be Added Multiple Times to an Investor, Artificially Increasing Their Wallet Count Causing Adding New Wallets to Revert

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`GlobalRegistryService::_updateInvestor` calls `_addWallet` for every address in the input list — even if that wallet is already registered to the same investor. `_addWallet` always increments `investors[id].walletCount` and reverts once `MAX_WALLETS_PER_INVESTOR` is reached. There is no duplicate-wallet guard, so calling `updateInvestor` with an investor's existing data repeatedly inflates the wallet count. Once `MAX_WALLETS_PER_INVESTOR` is reached, no further updates are possible and `removeInvestor` also becomes permanently blocked because it requires `walletCount == 0`.

**Impact:**
An investor's wallet count can be artificially inflated to the maximum, after which no further wallet additions or investor updates are possible. `removeInvestor` also becomes permanently reverted because the inflated count can never be decremented back to zero through the normal `removeWallet` path.

**Recommended Mitigation:**
In `_updateInvestor`, check whether the wallet being added is already registered to the same investor before calling `_addWallet`, and skip the call if it is already associated.

---

**[中文版本]**

**描述：**
`GlobalRegistryService::_updateInvestor` 對輸入列表中每個地址都調用 `_addWallet`——即使該錢包已屬於同一投資者。`_addWallet` 始終遞增 `walletCount`，並在達到 `MAX_WALLETS_PER_INVESTOR` 時 revert。缺乏重複錢包保護，使用投資者的現有數據調用 `updateInvestor` 會反覆虛增錢包計數，達到上限後任何更新均不可能，且 `removeInvestor` 因要求 `walletCount == 0` 也被永久阻塞。

**影響：**
投資者的錢包計數可被人為虛增至上限，之後無法添加新錢包或更新投資者信息；`removeInvestor` 因計數永遠無法歸零而被永久 revert。

**修復建議：**
在 `_updateInvestor` 中，調用 `_addWallet` 前先校驗該錢包是否已屬於同一投資者，若已關聯則跳過調用。

---

## 17. Unbounded `depositAddresses` Can Cause `CompliantDepositRegistry::challengeLatestBatch` to Revert Due to Out of Gas

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`CompliantDepositRegistry::challengeLatestBatch` removes challenged deposit addresses by calling `depositAddresses.pop()` in a loop for the entire batch length. When a large batch of deposit addresses is added via `addDepositAddresses` with no size limit, the loop to remove them can consume more gas than the block limit, causing the challenge transaction to revert due to out of gas.

**Impact:**
Large batches become unchallengeable — the `CANCELER_ROLE` cannot remove them even if they contain malicious or incorrect deposit addresses. Such batches will finalize unchallenged, permanently admitting unauthorized addresses into the compliant deposit registry.

**Recommended Mitigation:**
Implement an upper limit on the number of addresses that can be added in a single `addDepositAddresses` call. Alternatively, modify `challengeLatestBatch` to support partial cancellation across multiple transactions (batch-by-batch challenge).

---

**[中文版本]**

**描述：**
`CompliantDepositRegistry::challengeLatestBatch` 通過循環調用 `depositAddresses.pop()` 移除整個批次的存款地址。`addDepositAddresses` 沒有批次大小限制，當批次過大時，移除循環的 gas 消耗可能超過區塊上限，導致 challenge 交易因 out-of-gas 而 revert。

**影響：**
過大的批次無法被質疑——即使批次中包含惡意或錯誤的存款地址，`CANCELER_ROLE` 也無法移除。這些批次將在未受質疑的情況下最終確定，永久將未授權地址纳入合規存款登記冊。

**修復建議：**
對單次 `addDepositAddresses` 調用可添加的地址數量設置上限；或修改 `challengeLatestBatch` 支持跨多個交易的分批取消（逐批挑戰）。

---

## 18. Users Can Reset the Status of Their `firstPurchase` on the `referralData` When the Stablecoin Doesn't Revert on Transfers to `address(0)`

**Severity:** 🟡 Medium
**Source:** `cyfrin/final.md`

**Description:**
`ReferralManager::createReferral` intends to grant each user a discount only on their first purchase. The system checks whether the user has already set a referrer, but it does not validate that the `referrer` argument is non-zero. When the stablecoin allows transfers to `address(0)`, a user can call `createReferral` with `referrer = address(0)`, which bypasses the existing-referrer check and resets `referralData.isFirstPurchase` to `true`. This allows the user to repeatedly claim the first-purchase discount.

**Impact:**
Users can game the referral discount system to receive the first-purchase discount on every purchase by resetting `isFirstPurchase` before each transaction, leading to unintended economic losses for the protocol.

**Recommended Mitigation:**
Add a `require(referrer != address(0), "zero referrer")` validation in `createReferral`. Alternatively, ensure that signers never generate a valid signature for `referrer = address(0)`.

---

**[中文版本]**

**描述：**
`ReferralManager::createReferral` 設計意圖是僅在用戶首次購買時給予折扣。系統校驗用戶是否已設置推薦人，但未驗證 `referrer` 參數非零。當穩定幣允許向 `address(0)` 轉賬時，用戶可傳入 `referrer = address(0)` 調用 `createReferral`，繞過已有推薦人校驗，將 `referralData.isFirstPurchase` 重置為 `true`，從而在每次購買前重置，反覆享受首次購買折扣。

**影響：**
用戶可通過在每次交易前重置 `isFirstPurchase` 來反覆享受首次購買折扣，對協議造成不可預期的經濟損失。

**修復建議：**
在 `createReferral` 中增加 `require(referrer != address(0), "zero referrer")` 校驗；或確保簽名者永遠不為 `referrer = address(0)` 生成有效簽名。
