# revert-permanently (4)

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
