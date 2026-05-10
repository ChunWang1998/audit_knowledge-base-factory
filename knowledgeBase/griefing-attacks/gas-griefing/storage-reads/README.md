# storage-reads (9)

> Gas optimization issues from redundant storage reads that can also mask logical errors or state inconsistencies.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Cache identical storage reads — cyfrin/pledge.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
Multiple functions in the Remora pledge contracts repeatedly read the same storage slots without caching. In `PledgeManager::_fixDecimals`, `stablecoinDecimals` is read from storage multiple times within a single expression. In `PledgeManager::_verifyDocumentSignature`, `propertyToken` is read twice in adjacent lines. In `TokenBank::removeToken` and related functions, `developments.length` is repeatedly accessed in loop conditions and bodies. In `LockUpManager`, `userData.endInd` is read on every loop iteration.

**Impact:**
Unnecessary repeated storage reads increase gas costs for users on every invocation of the affected functions. In protocols with frequent interactions, these costs accumulate significantly over time.

**Recommended Mitigation:**
Cache `stablecoinDecimals`, `propertyToken`, `developments.length`, and `userData.endInd` into local variables at the start of each function, and reference the cached values throughout the function body.

---

**[中文版本]**

**描述：**
Remora 质押合约中的多个函数在不缓存的情况下重复读取相同的存储槽。在 `PledgeManager::_fixDecimals` 中，`stablecoinDecimals` 在单个表达式中被多次从存储读取。在 `PledgeManager::_verifyDocumentSignature` 中，`propertyToken` 在相邻行被读取两次。在 `TokenBank::removeToken` 及相关函数中，`developments.length` 在循环条件和循环体中被反复访问。在 `LockUpManager` 中，`userData.endInd` 在每次循环迭代时被读取。

**影響：**
不必要的重复存储读取增加了受影响函数每次调用时用户的 gas 成本。在交互频繁的协议中，这些成本会随时间显著累积。

**修復建議：**
在每个函数开始时将 `stablecoinDecimals`、`propertyToken`、`developments.length` 和 `userData.endInd` 缓存到本地变量中，并在整个函数体中引用缓存的值。

---

## 2. Cache identical storage reads — cyfrin/predeposit.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
In `pUSDeDepositor`, multiple storage variables are read from storage multiple times within the same function calls. `deposit_sUSDe` reads `sUSDe` from storage three times and `pUSDe` twice. `deposit_USDe` similarly reads `USDe` three times and `pUSDe` twice. `deposit_viaSwap` reads `USDe` three times and `autoSwaps[address(asset)]` twice. In `PreDepositPhaser`, `currentPhase` reads a storage variable that could be cached. Each redundant read costs a full warm/cold SLOAD.

**Impact:**
Every deposit transaction pays for several unnecessary storage reads, increasing user transaction costs and reducing deposit throughput efficiency on a per-user basis.

**Recommended Mitigation:**
Cache `sUSDe`, `USDe`, `pUSDe`, and `autoSwaps[address(asset)]` into local variables at the start of each respective function, then pass cached values where needed rather than re-reading from storage.

---

**[中文版本]**

**描述：**
在 `pUSDeDepositor` 中，多个存储变量在同一函数调用中被多次从存储读取。`deposit_sUSDe` 从存储读取 `sUSDe` 三次、`pUSDe` 两次。`deposit_USDe` 类似地读取 `USDe` 三次、`pUSDe` 两次。`deposit_viaSwap` 读取 `USDe` 三次、`autoSwaps[address(asset)]` 两次。在 `PreDepositPhaser` 中，`currentPhase` 读取一个本可缓存的存储变量。每次冗余读取都要消耗一次完整的热/冷 SLOAD 费用。

**影響：**
每笔存款交易都为多次不必要的存储读取付费，增加了用户的交易成本，降低了每位用户的存款吞吐效率。

**修復建議：**
在各自函数开始时将 `sUSDe`、`USDe`、`pUSDe` 和 `autoSwaps[address(asset)]` 缓存到本地变量中，然后在需要时传递缓存值而非重新从存储读取。

---

## 3. Cache identical storage reads and only write to storage once — cyfrin/protocol.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Across the `DepositManager` contract, multiple functions perform avoidable repeated storage reads. `sponsorGame` reads `pool.token` twice. `_claimReferralReward` reads `gamePools[gameId].token` twice. `_distributeFees` reads `pool.token`, `pool.totalCollectedAmount * pool.creatorFee / BASIS_POINTS`, and `pool.totalCollectedAmount * pool.protocolFee / BASIS_POINTS` multiple times each. `_refundSponsorFunds` reads `sponsorAmounts[sponsor][gameId]` and `pool.token` each twice. `_refundEntryFee` reads `pool.ticketPrice` twice. Additionally, some loop-based counters are written to storage on every iteration rather than being accumulated in memory and written once at loop completion.

**Impact:**
Each redundant SLOAD costs significant gas. Over many transactions across a busy protocol, the cumulative wasted gas is substantial for both individual users and overall protocol efficiency.

**Recommended Mitigation:**
Cache repeated storage reads into local variables at the start of each function. For loop-based counters, accumulate in local variables and write to storage only once after the loop completes.

---

**[中文版本]**

**描述：**
在 `DepositManager` 合约中，多个函数执行了可避免的重复存储读取。`sponsorGame` 读取 `pool.token` 两次。`_claimReferralReward` 读取 `gamePools[gameId].token` 两次。`_distributeFees` 分别多次读取 `pool.token`、`pool.totalCollectedAmount * pool.creatorFee / BASIS_POINTS` 和 `pool.totalCollectedAmount * pool.protocolFee / BASIS_POINTS`。`_refundSponsorFunds` 各读取 `sponsorAmounts[sponsor][gameId]` 和 `pool.token` 两次。`_refundEntryFee` 读取 `pool.ticketPrice` 两次。此外，一些基于循环的计数器在每次迭代时都写入存储，而非在内存中累积后在循环结束时一次性写入。

**影響：**
每次冗余的 SLOAD 消耗大量 gas。在繁忙协议的众多交易中，累计浪费的 gas 对个别用户和整体协议效率都相当可观。

**修復建議：**
在每个函数开始时将重复的存储读取缓存到本地变量中。对于基于循环的计数器，在本地变量中累积并在循环完成后只向存储写入一次。

---

## 4. Cache repeated storage reads — cyfrin/clob.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
Across matching functions in `MyriadCTFExchange`, several storage variables are read an excessive number of times. `conditionalTokens` is accessed 6 times in `_settleMintMatch`, 5 times in `_settleMergeMatch`, and 2×N times in the distribution loop of `matchCrossMarketOrders`. `manager` is read 2×N+2 times in `matchCrossMarketOrders`. `feeModule` is accessed N+2 times in `matchCrossMarketOrders` and 3 times in `matchOrdersWithFees`. `negRiskAdapter` is accessed 4 times in `matchCrossMarketOrders`. Each access incurs an SLOAD even when the values are constant within the function scope.

**Impact:**
The matching engine — the most frequently called part of the exchange — pays for a large number of redundant SLOADs on every match execution. This significantly increases the gas cost per trade, reducing competitiveness and user experience.

**Recommended Mitigation:**
Cache `conditionalTokens`, `manager`, `feeModule`, and `negRiskAdapter` into local variables at the top of each matching function to eliminate all redundant SLOADs.

---

**[中文版本]**

**描述：**
在 `MyriadCTFExchange` 的撮合函数中，多个存储变量被过多次读取。`conditionalTokens` 在 `_settleMintMatch` 中被访问 6 次，在 `_settleMergeMatch` 中被访问 5 次，在 `matchCrossMarketOrders` 的分发循环中被访问 2×N 次。`manager` 在 `matchCrossMarketOrders` 中被读取 2×N+2 次。`feeModule` 在 `matchCrossMarketOrders` 中被访问 N+2 次，在 `matchOrdersWithFees` 中被访问 3 次。`negRiskAdapter` 在 `matchCrossMarketOrders` 中被访问 4 次。即使值在函数范围内是常量，每次访问也会产生 SLOAD 费用。

**影響：**
撮合引擎——交易所中调用最频繁的部分——在每次撮合执行时为大量冗余 SLOAD 付费。这显著增加了每笔交易的 gas 成本，降低了竞争力和用户体验。

**修復建議：**
在每个撮合函数顶部将 `conditionalTokens`、`manager`、`feeModule` 和 `negRiskAdapter` 缓存到本地变量中，以消除所有冗余 SLOAD。

---

## 5. Cache storage slots to prevent identical storage reads — cyfrin/wannabetv2.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
In `Bet::accept`, `Bet::cancel`, and `Bet::resolve`, the `_aavePool` storage slot is read multiple times. Since `_aavePool` does not change during execution of any of these functions, it can be safely read once and cached in a local variable. When the Aave pool is configured (non-zero), `accept` performs 1 redundant SLOAD and `resolve`/`cancel` each perform 2 redundant SLOADs.

**Impact:**
Every Aave-integrated bet operation pays for 1–2 unnecessary storage reads per call, increasing user transaction costs in the most common execution path.

**Recommended Mitigation:**
At the start of `accept`, `cancel`, and `resolve`, read `_aavePool` once into a local variable and use the cached value throughout the function. Include a branch only if the cached value is non-zero to avoid wasting gas when Aave is not configured.

---

**[中文版本]**

**描述：**
在 `Bet::accept`、`Bet::cancel` 和 `Bet::resolve` 中，`_aavePool` 存储槽被多次读取。由于 `_aavePool` 在这些函数的任何执行过程中都不会改变，可以安全地读取一次并缓存在本地变量中。当 Aave 池已配置（非零）时，`accept` 执行 1 次冗余 SLOAD，`resolve`/`cancel` 各执行 2 次冗余 SLOAD。

**影響：**
每次 Aave 集成的投注操作在最常见的执行路径中每次调用都要为 1-2 次不必要的存储读取付费，增加了用户的交易成本。

**修復建議：**
在 `accept`、`cancel` 和 `resolve` 开始时，将 `_aavePool` 读取一次到本地变量中，并在整个函数中使用缓存值。仅在缓存值非零时进入分支，以避免 Aave 未配置时浪费 gas。

---

## 6. Cache storage to prevent identical storage reads — cyfrin/escrow.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
In `SablierBob`, multiple functions repeatedly read the same storage slots without caching. `exitWithinGracePeriod` and `redeem` both read `vault.shareToken` multiple times. `redeem` also reads `comptroller` multiple times in the branch where no vault adapter exists, if `minFeeWei` is likely non-zero. `unstakeTokensViaAdapter` and `onShareTransfer` both read `vault.adapter` (and `_vaults[vaultId].adapter` respectively) multiple times.

**Impact:**
Repeated cold and warm SLOAD costs are incurred unnecessarily on every call to the affected functions, increasing user transaction costs for common vault operations including redemption and share transfers.

**Recommended Mitigation:**
Cache `vault.shareToken`, `vault.adapter`, `comptroller`, and `_vaults[vaultId].adapter` into local variables at the start of each respective function and use the cached values throughout.

---

**[中文版本]**

**描述：**
在 `SablierBob` 中，多个函数在不缓存的情况下重复读取相同的存储槽。`exitWithinGracePeriod` 和 `redeem` 都多次读取 `vault.shareToken`。`redeem` 在不存在金库适配器的分支中也多次读取 `comptroller`（如果 `minFeeWei` 可能非零）。`unstakeTokensViaAdapter` 和 `onShareTransfer` 都多次读取 `vault.adapter`（分别是 `_vaults[vaultId].adapter`）。

**影響：**
在受影响函数的每次调用中，都会产生不必要的重复冷热 SLOAD 费用，增加了赎回和份额转移等常见金库操作的用户交易成本。

**修復建議：**
在各自函数开始时将 `vault.shareToken`、`vault.adapter`、`comptroller` 和 `_vaults[vaultId].adapter` 缓存到本地变量中，并在整个函数中使用缓存值。

---

## 7. Cache storage to prevent identical storage reads — cyfrin/harbor.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/harbor.md`

**Description:**
In the `Agreement` contract, `Agreement::getDetails` reads `accts.length` on both the outer loop array size check and on the inner initialization, causing two storage reads per outer iteration. `Agreement::_findAccountIndex` reads `chainAccounts.length` on every iteration of its loop rather than caching the value before the loop.

**Impact:**
Functions that iterate over chain accounts perform O(N) redundant storage reads, where N is the number of accounts. For protocols with many accounts, this scales poorly and wastes user gas.

**Recommended Mitigation:**
Cache `accts.length` before the inner loop in `getDetails` and cache `chainAccounts.length` before the loop in `_findAccountIndex`.

---

**[中文版本]**

**描述：**
在 `Agreement` 合约中，`Agreement::getDetails` 在外层循环数组大小检查和内层初始化时都读取 `accts.length`，导致每次外层迭代产生两次存储读取。`Agreement::_findAccountIndex` 在每次循环迭代时读取 `chainAccounts.length`，而非在循环前缓存该值。

**影響：**
遍历链账户的函数执行 O(N) 次冗余存储读取，其中 N 是账户数量。对于账户较多的协议，这种扩展性很差，浪费用户 gas。

**修復建議：**
在 `getDetails` 的内层循环前缓存 `accts.length`，在 `_findAccountIndex` 的循环前缓存 `chainAccounts.length`。

---

## 8. Don't perform storage reads unless necessary — cyfrin/rebasing.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ServiceConsumer::onlyMaster` unconditionally loads the trust manager from storage via `getTrustService()` and then calls `trustManager.getRole(msg.sender)` regardless of whether `msg.sender` is the owner. When `msg.sender == owner()`, the storage read and external call are completely unnecessary because the modifier should short-circuit immediately. The current pattern wastes one storage read and one external call on every owner-initiated transaction.

**Impact:**
Owner-initiated transactions pay for an unnecessary storage read and external call in the `onlyMaster` modifier, increasing gas costs for the most privileged caller in the system.

**Recommended Mitigation:**
Restructure the modifier to check `owner() == msg.sender` first. Only if that check fails, load the trust service and check the role. This eliminates the wasted storage read and external call on all owner transactions.

---

**[中文版本]**

**描述：**
`ServiceConsumer::onlyMaster` 无条件地通过 `getTrustService()` 从存储加载信任管理器，然后无论 `msg.sender` 是否为所有者都调用 `trustManager.getRole(msg.sender)`。当 `msg.sender == owner()` 时，存储读取和外部调用完全没有必要，因为修饰符应立即短路。当前模式在每次所有者发起的交易中都浪费一次存储读取和一次外部调用。

**影響：**
所有者发起的交易在 `onlyMaster` 修饰符中为不必要的存储读取和外部调用付费，增加了系统中最高权限调用者的 gas 成本。

**修復建議：**
重构修饰符以首先检查 `owner() == msg.sender`。只有该检查失败时，才加载信任服务并检查角色。这消除了所有所有者交易中浪费的存储读取和外部调用。

---

## 9. Fast fail without performing unnecessary storage reads or external calls — cyfrin/rebasing.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::preIssuanceCheck` begins by loading several external services from storage and performing expensive external calls (country lookup, compliance configuration reads) before checking whether `_to` is whitelisted. If `_to` is not whitelisted, the function returns early with an error code — but only after paying the gas for all the preceding reads and calls. The whitelist check depends only on the compliance service (already loaded) and can be performed immediately after minimal setup.

**Impact:**
Calls that fail the whitelist check pay the full gas cost of several storage reads and external calls that serve no purpose when the caller is not whitelisted, wasting gas on every rejected compliance check.

**Recommended Mitigation:**
Reorder `preIssuanceCheck` to perform the whitelist check as early as possible, immediately after loading the compliance service. All other storage reads and external calls should be deferred until after the fast-fail checks pass.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::preIssuanceCheck` 在检查 `_to` 是否已白名单之前，先从存储加载多个外部服务并执行昂贵的外部调用（国家查找、合规配置读取）。如果 `_to` 未被白名单，函数以错误代码提前返回——但已支付了所有前置读取和调用的 gas 费用。白名单检查仅依赖于合规服务（已加载），可以在最少的设置后立即执行。

**影響：**
未通过白名单检查的调用为多次存储读取和外部调用支付全额 gas 成本，而当调用者未被白名单时这些操作毫无意义，在每次被拒绝的合规检查中都浪费 gas。

**修復建議：**
重新排序 `preIssuanceCheck`，在加载合规服务后立即尽早执行白名单检查。所有其他存储读取和外部调用应推迟到快速失败检查通过之后再执行。
