# storage-prior (9)

> Issues where storage reads/writes or state updates were not correctly ordered, causing stale data or reentrancy risk.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Allow custom Creator and Collector names to be emitted in IStory events to build artwork provenance

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
The `IStory` interface is designed to allow custom names to be passed for Creator and Collector events, enabling on-chain provenance with human-readable identifiers. CryptoArt's implementation, however, ignores the `creatorName` and `collectorName` parameters entirely, always emitting the caller's raw hex string instead. The parameters are declared but immediately discarded with a comment (`/*creatorName*/`), resulting in provenance events that show machine addresses rather than artist identities.

**Impact:**
Artworks on CryptoArt cannot build a meaningful provenance story using custom names. Collectors and creators lose the ability to associate human-readable identities with ownership history, reducing the cultural and commercial value of the provenance trail compared to compliant implementations of the `IStory` interface.

**Recommended Mitigation:**
Use the supplied `creatorName` / `collectorName` calldata parameters inside the event emissions instead of always substituting `msg.sender.toHexString()`.

---

**[中文版本]**

**描述：**
`IStory` 接口设计用于允许为创作者和收藏者事件传入自定义名称，从而实现具有人类可读标识符的链上溯源。然而，CryptoArt 的实现完全忽略了 `creatorName` 和 `collectorName` 参数，始终发出调用者的原始十六进制字符串。参数虽已声明但立即被丢弃（注释为 `/*creatorName*/`），导致溯源事件显示的是机器地址而非艺术家身份。

**影響：**
CryptoArt 上的艺术品无法使用自定义名称构建有意义的溯源故事。收藏者和创作者失去了将人类可读身份与所有权历史关联的能力，与符合 `IStory` 接口规范的实现相比，溯源链的文化和商业价值大打折扣。

**修復建議：**
在事件发出时使用提供的 `creatorName` / `collectorName` calldata 参数，而非总是替换为 `msg.sender.toHexString()`。

---

## 2. Consider reverting in publishedDataByBatchId for invalid batch IDs

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`publishedDataByBatchId` returns a `PublishedData` struct for any provided `id` without validating whether the `id` is less than `currentBatchId`. For IDs that have never been published, the function silently returns an empty zero-value struct instead of reverting. While this does not present an immediate security risk, integrations relying on this function to confirm data existence may interpret the empty return as valid published data, introducing subtle bugs.

**Impact:**
Downstream integrations may silently process empty `PublishedData` structs for non-existent batch IDs, potentially leading to incorrect behavior or incorrect assumptions about data availability.

**Recommended Mitigation:**
Add a check at the top of `publishedDataByBatchId` to revert if `id >= currentBatchId`, ensuring callers receive an explicit error rather than silent zero-value data.

---

**[中文版本]**

**描述：**
`publishedDataByBatchId` 在不验证 `id` 是否小于 `currentBatchId` 的情况下，为任何提供的 `id` 返回 `PublishedData` 结构体。对于从未发布过的 ID，该函数静默返回空的零值结构体而非回滚。虽然这不会带来直接的安全风险，但依赖此函数确认数据存在性的集成可能将空返回解释为有效的已发布数据，从而引入细微错误。

**影響：**
下游集成可能为不存在的批次 ID 静默处理空的 `PublishedData` 结构体，可能导致不正确的行为或对数据可用性的错误假设。

**修復建議：**
在 `publishedDataByBatchId` 顶部添加检查，若 `id >= currentBatchId` 则回滚，确保调用者收到明确的错误而非静默的零值数据。

---

## 3. Don't copy entire Assertion struct from storage to memory in DefaultSession::assertionResolvedCallback

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::assertionResolvedCallback` copies the full `Assertion` struct from storage to memory even though it only needs four fields from it (`sessionId`, `resultCid`, `calculationCid`, `asserter`). The `Assertion` struct contains dynamic arrays (`winners`, `totalXPs`, `totalTimes`) and multiple strings, making the full copy very expensive. Additionally, the code first writes `assertions[assertionId].resolved = true` to storage, then reads the same struct back into memory, incurring the write cost before the expensive read.

**Impact:**
Every resolved assertion pays unnecessarily high gas costs for copying large dynamic structs from storage when only a fraction of the data is needed, increasing the cost of normal protocol operations.

**Recommended Mitigation:**
Instead of copying the full struct, read individual fields directly from storage (`assertions[assertionId].sessionId`, etc.) or use storage references. Alternatively, separate the static and dynamic fields of `Assertion` so the expensive arrays do not need to be copied.

---

**[中文版本]**

**描述：**
`DefaultSession::assertionResolvedCallback` 将完整的 `Assertion` 结构体从存储复制到内存，即使它只需要其中四个字段（`sessionId`、`resultCid`、`calculationCid`、`asserter`）。`Assertion` 结构体包含动态数组（`winners`、`totalXPs`、`totalTimes`）和多个字符串，使完整复制开销极大。此外，代码先将 `assertions[assertionId].resolved = true` 写入存储，再将相同结构体读回内存，在昂贵的读取之前产生了写入成本。

**影響：**
每次已解决的断言都因将大型动态结构体从存储复制而支付不必要的高额 gas 成本，而实际上只需要一小部分数据，增加了正常协议操作的成本。

**修復建議：**
不要复制完整结构体，而是直接从存储读取单个字段（如 `assertions[assertionId].sessionId` 等）或使用存储引用。或者，将 `Assertion` 的静态字段和动态字段分开，使昂贵的数组不必被复制。

---

## 4. Don't write to the same storage slot multiple times

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::cleanupInvestorIssuances` decrements `issuancesCounters[investor]` inside a loop with `issuancesCounters[investor]--` and then immediately reads the updated value back from storage with `currentIssuancesCount = issuancesCounters[investor]`. This results in one storage write followed immediately by a storage read on the same slot per loop iteration. The correct pattern is to use a local counter, decrement it in memory throughout the loop, and write the final value to storage only once when the loop completes.

**Impact:**
Excessive storage reads and writes inside a loop increase gas costs proportional to the number of issuances being cleaned up, which can be significant for users with large issuance histories.

**Recommended Mitigation:**
Cache `issuancesCounters[investor]` in a local variable, decrement the local variable within the loop, and write it back to storage once after the loop exits.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::cleanupInvestorIssuances` 在循环内通过 `issuancesCounters[investor]--` 递减计数器，然后立即从存储读回更新后的值 `currentIssuancesCount = issuancesCounters[investor]`。这导致每次循环迭代在同一存储槽上产生一次写入后紧接一次读取。正确的模式是使用本地计数器，在循环中于内存中递减，循环完成后仅写入一次最终值。

**影響：**
循环内过多的存储读写使 gas 成本与需要清理的发行记录数量成正比增加，对于发行历史较多的用户而言开销可能相当显著。

**修復建議：**
将 `issuancesCounters[investor]` 缓存在本地变量中，在循环内递减本地变量，循环结束后将其写回存储一次。

---

## 5. In Bet::accept,resolve,cancel update Bet state prior to external calls

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
In `Bet::accept`, `Bet::resolve`, and `Bet::cancel`, critical state changes — respectively setting `_bet.status = Status.ACTIVE`, `_bet.winner`, `_bet.status = Status.RESOLVED`, and `_bet.status = Status.CANCELLED` — occur after external token transfer calls. This violates the Checks-Effects-Interactions (CEI) pattern. If any external call is to a contract that can re-enter these functions before the state is updated, the reentrancy could allow the attacker to exploit the stale state.

**Impact:**
Violation of CEI introduces reentrancy risk: a malicious token or Aave pool integration could re-enter `accept`, `resolve`, or `cancel` before the bet status is updated, potentially allowing double-execution or exploitation of stale state.

**Recommended Mitigation:**
Move all storage state updates (`_bet.status`, `_bet.winner`) to before any external calls in `Bet::accept`, `Bet::resolve`, and `Bet::cancel`.

---

**[中文版本]**

**描述：**
在 `Bet::accept`、`Bet::resolve` 和 `Bet::cancel` 中，关键的状态变更——分别设置 `_bet.status = Status.ACTIVE`、`_bet.winner`、`_bet.status = Status.RESOLVED` 和 `_bet.status = Status.CANCELLED`——发生在外部代币转账调用之后。这违反了检查-效果-交互（CEI）模式。如果任何外部调用是针对在状态更新前可重入这些函数的合约，则重入攻击可能利用过时状态。

**影響：**
违反 CEI 引入重入风险：恶意代币或 Aave 池集成可在投注状态更新前重入 `accept`、`resolve` 或 `cancel`，可能允许双重执行或利用过时状态。

**修復建議：**
将所有存储状态更新（`_bet.status`、`_bet.winner`）移至 `Bet::accept`、`Bet::resolve` 和 `Bet::cancel` 中任何外部调用之前。

---

## 6. In tokenURI avoid copying entire _tokenURIs[tokenId] from storage into memory

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
`CryptoartNFT::tokenURI` copies both token URIs from the `_tokenURIs[tokenId]` storage mapping into a `string[2] memory uris` array, even though it only ever accesses one of the two URIs (the pinned index). Copying a dynamic `string[2]` array from storage to memory is significantly more expensive than reading only the single needed element via a storage reference.

**Impact:**
Every call to `tokenURI` pays extra gas for copying an unneeded URI string from storage into memory, increasing the cost for any user or protocol that reads NFT metadata.

**Recommended Mitigation:**
Use a `storage` reference (`string[2] storage uris = _tokenURIs[tokenId]`) instead of a `memory` copy so that only the accessed element is loaded.

---

**[中文版本]**

**描述：**
`CryptoartNFT::tokenURI` 将 `_tokenURIs[tokenId]` 存储映射中的两个代币 URI 都复制到 `string[2] memory uris` 数组中，即使它实际上只访问其中一个 URI（固定索引）。将动态 `string[2]` 数组从存储复制到内存比通过存储引用仅读取所需的单个元素要昂贵得多。

**影響：**
每次调用 `tokenURI` 都要为从存储复制不需要的 URI 字符串到内存支付额外的 gas，增加了读取 NFT 元数据的任何用户或协议的成本。

**修復建議：**
使用存储引用（`string[2] storage uris = _tokenURIs[tokenId]`）而非内存副本，以便仅加载被访问的元素。

---

## 7. Perform input-related checks prior to reading storage

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::createGame` performs several storage reads before reaching the array-length validation check `require(_promptStrategies.length == _promptHashes.length, ArrayLengthMismatch())`. Since this check depends only on input parameters — not on any storage state — it should be moved to the very beginning of the function, before any storage reads occur, to fail fast and save gas on invalid inputs.

**Impact:**
Transactions with mismatched array lengths pay unnecessary gas for storage reads before reverting on the input validation check, wasting user funds on failed transactions.

**Recommended Mitigation:**
Move all pure input-related checks that do not depend on storage state to the top of the function, before any storage reads are performed.

---

**[中文版本]**

**描述：**
`SessionManager::createGame` 在到达数组长度验证检查 `require(_promptStrategies.length == _promptHashes.length, ArrayLengthMismatch())` 之前执行了多次存储读取。由于此检查仅依赖于输入参数而非任何存储状态，应将其移至函数最开始处，在任何存储读取发生之前，以便对无效输入快速失败并节省 gas。

**影響：**
数组长度不匹配的交易在触发输入验证检查回滚之前，为不必要的存储读取支付了 gas，浪费了用户在失败交易上的资金。

**修復建議：**
将所有不依赖存储状态的纯输入相关检查移至函数顶部，在执行任何存储读取之前。

---

## 8. Perform storage updates prior to external calls

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
In `DepositManager::_refundEntryFee`, a `safeTransfer` to the player precedes the decrement of `pool.totalCollectedAmount`. In `SessionManager::joinGame`, the external call to `_payEntryFee` precedes the storage updates `contestants[_gameId][msg.sender] = true` and `games[_gameId].numContestants++`. Both patterns violate the CEI principle by performing external interactions before finalising the relevant state changes.

**Impact:**
External calls before state updates create reentrancy windows. A malicious token contract interacting with `_refundEntryFee` or `_payEntryFee` could re-enter the function before state is updated, potentially enabling double-refunds or double-joins.

**Recommended Mitigation:**
Reorder the operations so all storage state changes (contestant tracking, fee accounting) occur before any external token transfer calls.

---

**[中文版本]**

**描述：**
在 `DepositManager::_refundEntryFee` 中，向玩家的 `safeTransfer` 发生在 `pool.totalCollectedAmount` 递减之前。在 `SessionManager::joinGame` 中，外部调用 `_payEntryFee` 发生在存储更新 `contestants[_gameId][msg.sender] = true` 和 `games[_gameId].numContestants++` 之前。两种模式都通过在最终确定相关状态变更之前执行外部交互而违反了 CEI 原则。

**影響：**
在状态更新之前进行外部调用会产生重入窗口。与 `_refundEntryFee` 或 `_payEntryFee` 交互的恶意代币合约可在状态更新前重入函数，可能实现双重退款或双重加入。

**修復建議：**
重新排序操作，使所有存储状态变更（参与者跟踪、费用核算）在任何外部代币转账调用之前发生。

---

## 9. State changes without events

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
Several critical state-changing functions in `GlobalRegistry` — `setSecurityAdmin`, `setOperationsAdmin`, `setTreasury`, `setVaultFactory`, and related setters — modify important protocol addresses without emitting any events. Off-chain indexers, monitoring systems, and front-end interfaces rely on events to track state changes. Without emitted events, changes to core protocol configuration are invisible to off-chain infrastructure.

**Impact:**
Silent state changes to critical protocol addresses cannot be monitored or indexed off-chain. This reduces transparency, hampers incident response, and makes it difficult for external parties to detect unauthorized or accidental configuration changes.

**Recommended Mitigation:**
Emit a dedicated event in each state-changing function that records both the old and new values of the modified address, enabling off-chain systems to track and verify configuration changes.

---

**[中文版本]**

**描述：**
`GlobalRegistry` 中几个关键的状态变更函数——`setSecurityAdmin`、`setOperationsAdmin`、`setTreasury`、`setVaultFactory` 及相关 setter——在修改重要协议地址时未发出任何事件。链下索引器、监控系统和前端界面依赖事件来跟踪状态变化。没有发出事件，对核心协议配置的更改对链下基础设施是不可见的。

**影響：**
对关键协议地址的静默状态变更无法被链下监控或索引。这降低了透明度，妨碍了事件响应，并使外部方难以检测未经授权或意外的配置更改。

**修復建議：**
在每个状态变更函数中发出专用事件，记录被修改地址的新旧两个值，使链下系统能够跟踪和验证配置更改。
