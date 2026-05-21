# storage-function (20)

> Storage layout conflicts when adding functions or variables during upgrades. Part of [upgrade-config](../README.md).

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Missing Effective Stake Decrease During Unstake

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
The `unstake()` function in `Stargate.sol` fails to decrease the effective stake from the validator when a user unstakes a token that was previously in `PENDING` or `EXITED` delegation status. When a user unstakes such a token, the function withdraws VET from the protocol, claims rewards, resets delegation mappings, burns the token, and returns VET — but never calls `_updatePeriodEffectiveStake` to reduce the validator's recorded stake. This creates an accounting vulnerability where the validator's `delegatorsEffectiveStake` remains permanently inflated even after the corresponding token is burned.

**Impact:**
The validator's `delegatorsEffectiveStake` is permanently over-reported after each such unstake event. This corrupts reward and delegation accounting, allowing validators to appear as holding more delegated stake than they actually do. This is analogous to the double-stake reduction vulnerability on redelegation.

**Recommended Mitigation:**
Implement additional delegation statuses to differentiate between a validator exit due to failing block production and a conscious user delegation exit. Process each case separately in the `unstake` function, calling `_updatePeriodEffectiveStake` with a decrease flag for all non-ACTIVE delegation statuses before resetting delegation details.

---

**[中文版本]**

**描述：**
`Stargate.sol` 中的 `unstake()` 函数在用户取消质押处于 `PENDING` 或 `EXITED` 委托状态的代币时，未能减少验证器的有效质押量。该函数从协议中提取 VET、认领奖励、重置委托映射、销毁代币并返还 VET，但从未调用 `_updatePeriodEffectiveStake` 来减少验证器的已记录质押量。这导致验证器的 `delegatorsEffectiveStake` 在对应代币销毁后仍永久虚高。

**影響：**
每次此类取消质押操作后，验证器的 `delegatorsEffectiveStake` 持续被高估，破坏奖励与委托核算，使验证器看起来拥有比实际更多的委托质押量。

**修復建議：**
引入额外的委托状态以区分因出块失败导致的验证器退出与用户主动委托退出，在 `unstake` 函数中对所有非 ACTIVE 委托状态分别调用带有减少标志的 `_updatePeriodEffectiveStake`，然后再重置委托详情。

---

## 2. `AccountableYield::setNavGracePeriod` uses `Unauthorized` error for invalid input

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`AccountableYield.setNavGracePeriod()` reverts with `Unauthorized()` when `period < MIN_NAV_GRACE_PERIOD`, even though this condition represents an input validation failure rather than an access control issue. Using an access-control error for a parameter validation scenario is semantically incorrect and misleading — callers and monitoring tools will misattribute the revert cause to a missing authorization rather than an invalid parameter.

**Impact:**
The misleading error code makes it harder to diagnose the root cause of reverts for legitimate callers who provide an out-of-range period. It also undermines the clarity of the protocol's error taxonomy.

**Recommended Mitigation:**
Replace the `Unauthorized()` revert with a dedicated input-validation error such as `InvalidNavGracePeriod()`, or reuse an existing generic invalid-parameter error, to accurately communicate the cause of the revert.

---

**[中文版本]**

**描述：**
`AccountableYield.setNavGracePeriod()` 在 `period < MIN_NAV_GRACE_PERIOD` 时抛出 `Unauthorized()` 错误，但此条件实际上是输入验证失败而非访问控制问题。使用访问控制错误来表示参数验证失败在语义上是错误且具有误导性的。

**影響：**
误导性错误代码使合法调用方更难诊断 revert 根本原因，也破坏了协议错误分类体系的清晰性。

**修復建議：**
将 `Unauthorized()` revert 替换为专用的输入验证错误，如 `InvalidNavGracePeriod()`，或复用现有的通用无效参数错误，以准确传达 revert 原因。

---

## 3. Deactivated Model Still Usable for Sessions and Node Registration

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
When the owner deactivates a model via `deactivateModel`, no enforcement exists in the session creation path to prevent new sessions from being created against that deactivated model. `createSessionJobForModel` and `createSessionJobForModelWithToken` validate that a host supports a model by calling `nodeRegistry.nodeSupportsModel()`, which only checks the host's local `supportedModels` array. Neither function ever calls `modelRegistry.isModelApproved(modelId)` to verify the model is still active. Model approval is checked only at node registration time and model update time, never at session creation. Once a host has the model in its local array, deactivation in `ModelRegistry` has no downstream effect.

**Impact:**
A model deactivated by the owner for security reasons (e.g., compromised weights, harmful outputs) continues to be available for new session creation indefinitely. This renders the emergency deactivation mechanism entirely ineffective and exposes renters to inference from a model the owner explicitly deemed unsafe.

**Recommended Mitigation:**
Add an `isModelApproved` check in `JobMarketplaceWithModelsUpgradeable` during model-aware session creation by querying `ModelRegistry` directly before the host-support validation.

---

**[中文版本]**

**描述：**
当所有者通过 `deactivateModel` 停用模型时，会话创建路径中不存在任何强制措施阻止针对该停用模型创建新会话。会话创建函数通过调用 `nodeRegistry.nodeSupportsModel()` 验证主机是否支持某模型，该函数仅检查主机本地的 `supportedModels` 数组，从不调用 `modelRegistry.isModelApproved(modelId)` 验证模型是否仍处于活跃状态。

**影響：**
出于安全原因（如权重泄露、有害输出）被所有者停用的模型仍可无限期地被用于创建新会话，使紧急停用机制完全失效，并将租用方暴露在所有者明确认为不安全的模型推理风险中。

**修復建議：**
在 `JobMarketplaceWithModelsUpgradeable` 的模型感知会话创建中，通过直接查询 `ModelRegistry` 的 `isModelApproved` 在主机支持验证之前添加检查。

---

## 4. Don't emit misleading events when roles haven't been added or revoked

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`AccessControlUpgradeable::_grantRole` and `_revokeRole` return a `bool` to indicate whether the role was actually granted or revoked. Functions such as `GlobalRegistryService::changeAdmin`, `addOperator`, and `revokeOperator` call these functions but do not check the boolean return value before emitting events. As a result, events are emitted even when no actual role change occurred — for example, when granting a role that was already held or revoking a role that was not held.

**Impact:**
Emitting misleading events when no role change occurred can confuse off-chain monitoring, indexers, and analytics tools that rely on events to track role state, potentially causing incorrect access-control tracking.

**Recommended Mitigation:**
In `changeAdmin`, `addOperator`, and `revokeOperator`, check the boolean return value of `_grantRole` and `_revokeRole` and only emit the corresponding events if the return value is `true`, confirming that a role was actually granted or revoked.

---

**[中文版本]**

**描述：**
`AccessControlUpgradeable::_grantRole` 和 `_revokeRole` 返回布尔值以指示角色是否实际被授予或撤销。`GlobalRegistryService::changeAdmin`、`addOperator` 和 `revokeOperator` 等函数未检查该返回值就直接触发事件，导致即使没有实际角色变更也会发出事件。

**影響：**
在未发生角色变更时发出误导性事件，可能混淆依赖事件追踪角色状态的链下监控、索引工具和分析系统，导致访问控制追踪错误。

**修復建議：**
在 `changeAdmin`、`addOperator` 和 `revokeOperator` 中检查 `_grantRole` 和 `_revokeRole` 的布尔返回值，仅在返回值为 `true` 时才发出相应事件。

---

## 5. Emit missing event information

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
The `YieldDistributed` event is emitted with only the yield amount but omits the `timestamp` parameter. Events are a primary source of off-chain data for protocol analytics, historical querying, and integrations. Without a timestamp embedded in the event, callers must rely on block timestamp lookups which are more expensive and fragile.

**Impact:**
Off-chain tooling and integrations that rely on `YieldDistributed` events cannot directly determine when yield was distributed without additional block-level queries, degrading the quality of protocol observability.

**Recommended Mitigation:**
Add a `timestamp` parameter to the `YieldDistributed` event definition and include `block.timestamp` (or a relevant timestamp value) when emitting it.

---

**[中文版本]**

**描述：**
`YieldDistributed` 事件仅携带收益金额参数，遗漏了 `timestamp` 参数。事件是链下数据分析、历史查询和集成的主要信息来源，缺少时间戳会使调用方需要额外的区块时间戳查询。

**影響：**
依赖 `YieldDistributed` 事件的链下工具和集成无法直接确定收益分配时间，降低了协议可观测性。

**修復建議：**
在 `YieldDistributed` 事件定义中添加 `timestamp` 参数，并在触发时包含 `block.timestamp`。

---

## 6. Emit missing events for storage changes

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
Multiple functions across various contracts modify storage state without emitting corresponding events. Affected functions include `Allowlist::changeUserAccreditation`, `changeAdminStatus`; `ReferralManager::addReferral`; `RemoraIntermediary::setFundingWallet`, `setFeeRecipient`; `TokenBank::changeReferralManager`, `changeStablecoin`, `changeCustodialWallet`; `DividendManager::setPayoutForwardAddress`, `changeWallet`; `RemoraToken::addToWhitelist`, `removeFromWhitelist`, `updateAllowList`; and several `PaymentSettler` functions. Additionally, events like `UserAllowed` and `TokensWithdrawn` are missing important fields.

**Impact:**
Without events for storage changes, off-chain observers cannot detect or react to critical configuration changes, reducing protocol transparency and making monitoring and integration unreliable.

**Recommended Mitigation:**
Add the appropriate events and emit them in all affected functions when storage state is modified.

---

**[中文版本]**

**描述：**
多个合约中的多个函数在修改存储状态时未发出相应事件，涉及 `Allowlist`、`ReferralManager`、`RemoraIntermediary`、`TokenBank`、`DividendManager`、`RemoraToken`、`PaymentSettler` 等合约的多个配置函数。此外，`UserAllowed` 和 `TokensWithdrawn` 等事件也缺少重要字段。

**影響：**
缺少存储变更事件使链下观察者无法检测或响应关键配置更改，降低协议透明度，导致监控和集成不可靠。

**修復建議：**
在所有受影响的函数中添加适当的事件，并在存储状态被修改时发出这些事件。

---

## 7. Fast fail by performing input-related checks first

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
In `SessionManager::createGame`, an array-length consistency check (`require(_promptStrategies.length == _promptHashes.length, ArrayLengthMismatch())`) is performed after multiple storage reads rather than before them. Since reading from storage is expensive, failing on this cheap input check after already paying for storage reads is wasteful. Performing the input-related check first allows the transaction to fail fast with lower gas cost in the invalid-input path.

**Impact:**
Users submitting mismatched array lengths pay unnecessarily for storage reads before the transaction reverts, increasing the gas cost of the failure path.

**Recommended Mitigation:**
Move the `_promptStrategies.length == _promptHashes.length` check to the top of `createGame`, before any storage reads, so invalid inputs revert early and cheaply.

---

**[中文版本]**

**描述：**
`SessionManager::createGame` 中，数组长度一致性检查（`require(_promptStrategies.length == _promptHashes.length, ...)`）在多次存储读取之后才执行，而非在之前。由于存储读取代价高昂，在已付出存储读取开销后才对廉价输入检查失败是浪费的。

**影響：**
提交不匹配数组长度的用户在交易 revert 前已不必要地支付了存储读取的 gas 费用。

**修復建議：**
将长度检查移至 `createGame` 顶部，在任何存储读取之前执行，使无效输入能够早期以低成本 revert。

---

## 8. Missing Gas Tank Auto-Fill for Recipients in Bulk Transfers

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
The `PortfolioSub` contract implements an `autoFillPrivate` mechanism designed to ensure users always have sufficient gas tokens (ALOT) in their Gas Tank to perform transactions on the Dexalot L1. The single-token `transferToken` function correctly calls `autoFillPrivate` for the recipient, upholding the documented invariant that any trader with assets in their portfolio will have gas in their Gas Tank. However, the `bulkTransferTokens` function omits this call entirely, meaning recipients of bulk transfers receive tokens without any gas auto-fill.

**Impact:**
Recipients of bulk transfers cannot perform any transactions on Dexalot L1 immediately after receiving tokens, since their Gas Tank was not filled. This breaks the documented protocol invariant and creates inconsistent behavior between single and bulk transfers.

**Recommended Mitigation:**
Add a call to `autoFillPrivate(_to, _symbols[_symbols.length - 1], Tx.AUTOFILL)` at the end of `bulkTransferTokens` to ensure recipients receive the gas auto-fill consistent with the single-token transfer path.

---

**[中文版本]**

**描述：**
`PortfolioSub` 合约实现了 `autoFillPrivate` 机制，确保用户在 Dexalot L1 上的 Gas Tank 中始终有足够的 ALOT gas 代币。单代币 `transferToken` 函数正确地为接收方调用了 `autoFillPrivate`，但 `bulkTransferTokens` 函数完全省略了这一调用，导致批量转账的接收方在收到代币后 Gas Tank 未被填充。

**影響：**
批量转账的接收方在收到代币后无法立即在 Dexalot L1 上执行任何交易，破坏了协议的已记录不变量，并在单次和批量转账之间造成行为不一致。

**修復建議：**
在 `bulkTransferTokens` 末尾添加对 `autoFillPrivate(_to, _symbols[_symbols.length - 1], Tx.AUTOFILL)` 的调用，确保接收方获得与单代币转账路径一致的 gas 自动补充。

---

## 9. Missing Refund Mechanism for Regular Members Leads To Stuck Assets

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
The smart contract provides a `returnFunds()` function, but it only applies to joint-contributor workflows, allowing a primary contributor to unwind an invitation before payout starts. Regular users who joined via `joinGroup()` have no mechanism to reclaim their funds if the Komiti group does not start, overfills, stalls, or is otherwise abandoned before payouts begin. This contradicts expected user safety guarantees.

**Impact:**
Funds contributed by standard participants who joined via `joinGroup()` can become permanently locked in the contract if the group never starts payouts. There is no path for them to recover their contributions, even in clearly abandoned groups.

**Recommended Mitigation:**
Implement a refund path for regular users that is executable before payouts begin. Ensure the refund mechanism works for both joint and non-joint participants. Consider also adding admin emergency refund capabilities for abandoned or corrupted groups.

---

**[中文版本]**

**描述：**
智能合约提供了 `returnFunds()` 函数，但该函数仅适用于联合贡献者工作流，允许主要贡献者在派息开始前撤销邀请。通过 `joinGroup()` 加入的普通用户在 Komiti 团体未开始、超额填充、停滞或被遗弃时没有任何资金回收机制。

**影響：**
通过 `joinGroup()` 加入的普通参与者的资金在团体从未开始派息时可能被永久锁定在合约中，即使在明显被遗弃的团体中也无法恢复贡献资金。

**修復建議：**
为普通用户实现可在派息开始前执行的退款路径，确保退款机制对联合和非联合参与者都有效，并考虑添加管理员紧急退款功能。

---

## 10. Missing getter function for `SablierBobState::isStakedInAdapter`

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
The `SablierBobState` contract implements getter functionality for all members of the `Vault` struct for a particular `vaultId`, including `token`, `expiry`, `lastSyncedAt`, `shareToken`, `oracle`, `adapter`, `targetPrice`, and `lastSyncedPrice`. However, it does not implement a getter for the `isStakedInAdapter` boolean member of the struct. This field determines whether the vault's funds are currently staked in an adapter and is important for off-chain integration and state monitoring.

**Impact:**
Off-chain tooling and integrations cannot directly query `isStakedInAdapter` without using low-level storage reads, reducing the contract's usability and observability.

**Recommended Mitigation:**
Implement a getter function for the `isStakedInAdapter` member of the `Vault` struct.

---

**[中文版本]**

**描述：**
`SablierBobState` 合约为 `Vault` 结构体的所有成员实现了 getter 函数，但未为布尔成员 `isStakedInAdapter` 实现 getter。该字段指示 vault 资金是否当前质押在适配器中，对链下集成和状态监控很重要。

**影響：**
链下工具和集成无法直接查询 `isStakedInAdapter`，需要使用低级存储读取，降低了合约的可用性和可观测性。

**修復建議：**
为 `Vault` 结构体的 `isStakedInAdapter` 成员实现 getter 函数。

---

## 11. Missing minimum deposit enforcement

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeVault::deposit` does not enforce a minimum deposit amount. Allowing dust deposits can lead to economic unviability — a user might deposit an amount so small that the gas fees for the transaction significantly exceed the value of the deposit itself. It also enables scenarios where an attacker or user spams the vault with many tiny deposits, increasing overhead and complicating accounting.

**Impact:**
Users can submit economically irrational dust deposits where transaction costs far exceed deposited value. Malicious or accidental dust deposits increase vault management overhead.

**Recommended Mitigation:**
Introduce a `minDepositAmount` state variable configurable by an admin. Modify the `deposit` function to require that the deposited `assets` are greater than or equal to this minimum amount.

---

**[中文版本]**

**描述：**
`BasisTradeVault::deposit` 未强制执行最低存款金额。允许粉尘存款可能导致经济不合理——用户存入的金额可能远小于交易的 gas 费用。此外还可能引发攻击者用大量微小存款轰炸 vault 的场景。

**影響：**
用户可以提交经济上不合理的粉尘存款，交易成本远超存入价值；恶意或意外的粉尘存款增加 vault 管理开销。

**修復建議：**
引入可由管理员配置的 `minDepositAmount` 状态变量，并修改 `deposit` 函数以要求存入的 `assets` 大于或等于该最小金额。

---

## 12. More efficient implementation of `SessionManager::joinGame` via better storage packing

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::joinGame` performs up to 4 storage reads to access `games[_gameId].state` (potentially twice), `games[_gameId].numContestants`, and `games[_gameId].verificationRequired`. Since each storage slot read costs 100 gas, these redundant reads are expensive. By refactoring the `Game` struct to pack `state`, `numContestants` (as `uint32`), and `verificationRequired` (as `bool`) into the same storage slot, all three values can be retrieved in a single storage read via a storage reference.

**Impact:**
The current implementation pays for up to 4 storage reads on every `joinGame` call. Better packing reduces this to 1 read, yielding significant gas savings at scale.

**Recommended Mitigation:**
Refactor the `Game` struct to pack `uint32 numContestants`, `SessionState state`, and `bool verificationRequired` into the same storage slot. In `joinGame`, cache the struct reference with `Game storage gameRef = games[_gameId]` and read all three fields at once.

---

**[中文版本]**

**描述：**
`SessionManager::joinGame` 对 `games[_gameId]` 的 `state`（可能两次）、`numContestants` 和 `verificationRequired` 最多执行 4 次存储读取。通过重构 `Game` 结构体，将 `state`、`numContestants`（uint32）和 `verificationRequired`（bool）打包到同一存储槽，可以通过单次存储读取获取所有三个值。

**影響：**
当前实现每次 `joinGame` 调用需要最多 4 次存储读取，更好的打包可将其减少为 1 次，在规模化时节省大量 gas。

**修復建議：**
重构 `Game` 结构体以将 `uint32 numContestants`、`SessionState state` 和 `bool verificationRequired` 打包到同一存储槽，在 `joinGame` 中通过存储引用一次性读取所有三个字段。

---

## 13. Neg-risk events have no void/cancellation path

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
Standalone binary markets support cancellation via `adminVoidMarket`, which sets `resolvedOutcome = -1`, records admin-specified payout ratios in `voidedPayouts`, and allows participants to recover collateral through `ConditionalTokens::redeemVoided`. Neg-risk event markets have no equivalent path: `adminVoidMarket` hard-blocks neg-risk markets and `NegRiskAdapter::resolveEvent` only accepts a winning outcome, not a cancellation. If a neg-risk event must be cancelled, the admin's only options are to leave it unresolved (locking all participant collateral indefinitely) or to resolve it as "Other wins" (forwarding all collateral to treasury rather than refunding participants). Neither option is a fair cancellation.

**Impact:**
If an oracle becomes unavailable, a question is invalidated, or a regulatory action requires event cancellation, there is no safe mechanism to return participant collateral. Funds remain permanently locked or are misdirected to treasury.

**Recommended Mitigation:**
Add a `voidEvent` function to `NegRiskAdapter` that calls `adminVoidMarket` on each underlying market with a provided payout split, sets `evt.resolved = true`, and handles the adapter's minted wcol accounting. This gives participants access to `redeemVoided` for proportional collateral recovery.

---

**[中文版本]**

**描述：**
独立二元市场通过 `adminVoidMarket` 支持取消，设置 `resolvedOutcome = -1` 并允许参与者通过 `ConditionalTokens::redeemVoided` 按比例取回抵押物。但负风险事件市场没有等效路径：`adminVoidMarket` 硬性拒绝负风险市场，而 `NegRiskAdapter::resolveEvent` 只接受获胜结果，不接受取消。如需取消负风险事件，管理员只能让其永久未解决（锁定所有参与者抵押物）或将其解析为"其他获胜"（将所有抵押物转入国库而非退还参与者），两者均不是公平的取消机制。

**影響：**
当预言机不可用、问题无效或监管行动要求取消事件时，没有安全机制返还参与者的抵押物，资金将永久锁定或被错误地转入国库。

**修復建議：**
在 `NegRiskAdapter` 中添加 `voidEvent` 函数，对每个底层市场调用 `adminVoidMarket`，设置 `evt.resolved = true`，并处理适配器的 wcol 核算，使参与者能够按比例取回抵押物。

---

## 14. Prefer `calldata` to `memory` for external read-only function inputs

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Several external functions use `memory` for array parameters that are only read, not modified. Specifically, `SessionManager::createGame` and `QuestionManager::_commitQuestions` declare `bytes32[] memory _promptHashes` and `address[] memory _promptStrategies`, and `DefaultSession::setXPTiers` declares `uint256[] memory _xpTiers`. Using `memory` for read-only external inputs forces an unnecessary copy of the calldata into memory, wasting gas.

**Impact:**
Every call to the affected functions pays extra gas for the memory allocation and copy of input arrays. For large arrays this can be significant.

**Recommended Mitigation:**
Change `memory` to `calldata` for all read-only array parameters in external functions, including `createGame`, `_commitQuestions`, and `setXPTiers`.

---

**[中文版本]**

**描述：**
多个外部函数对仅读取而不修改的数组参数使用了 `memory` 而非 `calldata`，包括 `SessionManager::createGame`、`QuestionManager::_commitQuestions` 和 `DefaultSession::setXPTiers` 中的相关参数。对只读外部输入使用 `memory` 会强制将 calldata 不必要地复制到内存，浪费 gas。

**影響：**
每次调用受影响的函数都需为输入数组的内存分配和复制支付额外 gas，对大型数组影响尤为显著。

**修復建議：**
将所有外部函数中只读数组参数的 `memory` 改为 `calldata`。

---

## 15. Rename all `sessionId` to `gameId` or vice versa for consistency

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Throughout the codebase, `sessionId` and `gameId` are used interchangeably to refer to the same concept — the identifier for a game session. This inconsistency spans multiple contracts including `DefaultSession`, `FixedRanksReward`, `ProportionalToXPReward`, and `SessionResultAsserter`. The mixed naming makes the codebase harder to read, understand, and maintain, and can confuse developers integrating with the protocol.

**Impact:**
Naming inconsistency reduces code readability and maintainability, increases the risk of developer confusion during integration or future modifications.

**Recommended Mitigation:**
Choose one name (`sessionId` or `gameId`) and apply it consistently across all contracts, natspec, events, errors, and mappings.

---

**[中文版本]**

**描述：**
整个代码库中，`sessionId` 和 `gameId` 被互换使用来指代同一概念——游戏会话的标识符。这种不一致性跨越多个合约，使代码库难以阅读、理解和维护。

**影響：**
命名不一致降低了代码可读性和可维护性，增加了集成或未来修改时开发者产生混淆的风险。

**修復建議：**
选择一个名称（`sessionId` 或 `gameId`），并在所有合约、natspec、事件、错误和映射中一致使用。

---

## 16. Storage Inconsistency in `migrateTokenManager` Function Leading to Data Corruption

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
The `migrateTokenManager` function in the `TokenManager` library contains a storage inconsistency bug that corrupts contract state during migration operations. When migrating token managers from `NodeManagementV3` to `StargateNFT`, the function directly sets the new manager without removing the token from the previous manager's `managerToTokenIds` set. It updates `$.managerToTokenIds[_manager].add(_tokenId)` and `$.tokenIdToManager[_tokenId] = _manager`, but omits the cleanup of the existing manager's mapping entry. This creates a state where multiple users appear to manage the same token simultaneously.

**Impact:**
Migration data corruption causes view function inconsistencies where `getTokenManager()` and `isTokenManager()` return correct data but `idsManagedBy()` returns stale entries. Users with stale entries experience increased gas costs, and the corrupted state cannot be easily remediated after migration.

**Recommended Mitigation:**
Update `migrateTokenManager` to include proper cleanup logic: before adding the new manager, remove the token from the previous manager's `managerToTokenIds` set and clear the existing mapping entries.

---

**[中文版本]**

**描述：**
`TokenManager` 库中的 `migrateTokenManager` 函数包含一个存储不一致缺陷，在迁移操作期间会破坏合约状态。该函数直接设置新管理者而不从先前管理者的 `managerToTokenIds` 集合中移除代币，导致多个用户看似同时管理同一代币的异常状态。

**影響：**
迁移数据损坏导致视图函数不一致：`getTokenManager()` 和 `isTokenManager()` 返回正确数据，但 `idsManagedBy()` 返回过时条目，带来额外 gas 开销且损坏状态难以修复。

**修復建議：**
更新 `migrateTokenManager` 以包含适当的清理逻辑：在添加新管理者之前，从先前管理者的 `managerToTokenIds` 集合中移除代币并清除现有映射条目。

---

## 17. Storage read optimizations

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
Multiple functions in `AccountableOpenTerm` and `AccountableFixedTerm` perform redundant identical storage reads that can be cached in local variables. Key patterns include: `_calculateRequiredLiquidity` reading `vault` and `_scaleFactor` multiple times across nested function calls; `_getAvailableLiquidityForProcessing` re-reading `vault`; `_penaltyFee` using an uncached `gracePeriod`; `supply` and `repay` re-reading `vault`; `_sharePrice` re-reading `loanState`; and `acceptBorrowerRole` reading `pendingBorrower` twice. Additionally, `AccountableWithdrawalQueue::_push` could eliminate a conditional read by initializing `_queue.nextRequestId` to 1 at construction.

**Impact:**
Redundant storage reads increase gas costs for all callers of affected functions. Accumulated across the protocol's core vault operations these inefficiencies are non-trivial.

**Recommended Mitigation:**
Cache repeated storage reads in local variables (e.g., `address vault_ = vault`), pass cached values as parameters where feasible, and eliminate redundant conditional reads through appropriate initialization.

---

**[中文版本]**

**描述：**
`AccountableOpenTerm` 和 `AccountableFixedTerm` 中的多个函数对相同存储变量执行了冗余的重复读取，可缓存到局部变量中。关键模式包括：`_calculateRequiredLiquidity` 在嵌套函数调用中多次读取 `vault` 和 `_scaleFactor`；`_getAvailableLiquidityForProcessing` 重复读取 `vault`；`_penaltyFee` 使用未缓存的 `gracePeriod`；`supply` 和 `repay` 重复读取 `vault`；`_sharePrice` 重复读取 `loanState` 等。

**影響：**
冗余存储读取增加了受影响函数所有调用者的 gas 成本，在协议核心 vault 操作中积累的低效影响不可忽视。

**修復建議：**
将重复存储读取缓存到局部变量（如 `address vault_ = vault`），在可行时将缓存值作为参数传递，并通过适当初始化消除冗余条件读取。

---

## 18. Taker receives Aave yield for cancelled pending bets

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
When a bet uses an Aave pool but never becomes `ACTIVE` (the taker never accepts), only the maker's stake is supplied to Aave. In `Bet::cancel`, the recovered Aave balance is still split using maker/taker refund logic: `makerRefund = _min(makerRefund, aTokenBalance)` and `takerRefund = _min(takerRefund, aTokenBalance - makerRefund)`. As a result, the taker can receive part of the maker's accrued Aave yield despite never having deposited.

**Impact:**
Takers who never accepted a bet can receive a portion of the maker's accrued yield upon cancellation, representing an unintended transfer of value from makers to takers.

**Recommended Mitigation:**
Only distribute Aave yield to parties who actually deposited funds. If the taker never accepted the bet, any yield generated should accrue to the maker or to the treasury, not to the taker.

---

**[中文版本]**

**描述：**
当投注使用 Aave 池但从未变为 `ACTIVE`（接受方从未接受）时，只有庄家的质押被供应给 Aave。在 `Bet::cancel` 中，回收的 Aave 余额仍然使用庄家/接受方的退款逻辑进行分配，导致从未存款的接受方可能获得庄家积累的 Aave 收益的一部分。

**影響：**
从未接受投注的接受方在取消时可能获得庄家积累收益的一部分，代表对庄家资金的意外转移。

**修復建議：**
仅向实际存入资金的一方分配 Aave 收益。若接受方从未接受投注，任何产生的收益应归庄家或国库所有，而非接受方。

---

## 19. Use `uint32` for timestamps for better storage packing

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Multiple timestamp-related fields in the protocol are declared as `uint256` when `uint32` would suffice. The maximum value of `uint32` (4,294,967,295) corresponds to year 2106, far beyond the protocol's expected lifetime. Using `uint32` for `SessionManager::Game::startTime`, `endTime`, `originalStartTime` and duration-related fields `minimumStartDelay`, `maxGameDuration`, `revealGracePeriod`, `livenessDuration`, and `DefaultSession::SessionResult::time` allows adjacent timestamp fields to share storage slots, significantly reducing the number of storage slots required.

**Impact:**
Using `uint256` for timestamps wastes storage slots, increasing SLOAD/SSTORE costs across all game lifecycle functions.

**Recommended Mitigation:**
Declare all timestamp and duration fields as `uint32` and arrange them adjacent to other small-type fields in their respective structs to enable storage packing.

---

**[中文版本]**

**描述：**
协议中多个与时间戳相关的字段被声明为 `uint256`，而 `uint32` 已足够（`uint32` 最大值对应 2106 年，远超协议预期生命周期）。将 `startTime`、`endTime`、`originalStartTime` 及各时间相关字段改为 `uint32` 可允许相邻时间戳字段共享存储槽，显著减少所需存储槽数量。

**影響：**
使用 `uint256` 存储时间戳浪费存储槽，增加所有游戏生命周期函数的 SLOAD/SSTORE 成本。

**修復建議：**
将所有时间戳和持续时间字段声明为 `uint32`，并在各自结构体中将其与其他小类型字段相邻排列以实现存储打包。

---

## 20. Use fixed length array for `reSDLTokenIds`

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
`SDLVesting` declares `uint256[] private reSDLTokenIds` as a dynamic array and initializes it in the constructor with a `for`-loop pushing zeros up to `MAX_LOCK_TIME + 1` (5 elements). This incurs a dynamic-array length slot, a pointer slot for array data, and multiple storage writes at deployment. Since the array's length is always exactly `MAX_LOCK_TIME + 1`, a static array `uint256[MAX_LOCK_TIME + 1] private reSDLTokenIds` is entirely equivalent, removes the dynamic-array overhead, and eliminates the initialization loop.

**Impact:**
Using a dynamic array instead of a fixed-length array wastes two storage slots (length + data pointer) and incurs unnecessary storage writes at deployment and slightly higher per-read gas costs throughout the contract's lifetime.

**Recommended Mitigation:**
Replace the dynamic array declaration with `uint256[MAX_LOCK_TIME + 1] private reSDLTokenIds` and remove the constructor initialization loop.

---

**[中文版本]**

**描述：**
`SDLVesting` 将 `uint256[] private reSDLTokenIds` 声明为动态数组，并在构造函数中通过循环将其初始化为 `MAX_LOCK_TIME + 1`（5个）元素。这会产生动态数组长度槽、数据指针槽和多次存储写入。由于数组长度始终恰好为 `MAX_LOCK_TIME + 1`，静态数组 `uint256[MAX_LOCK_TIME + 1]` 完全等效，可消除动态数组开销并省去初始化循环。

**影響：**
使用动态数组而非固定长度数组浪费两个存储槽（长度 + 数据指针），在部署时产生不必要的存储写入，整个合约生命周期内每次读取的 gas 成本也略高。

**修復建議：**
将动态数组声明替换为 `uint256[MAX_LOCK_TIME + 1] private reSDLTokenIds`，并移除构造函数初始化循环。
