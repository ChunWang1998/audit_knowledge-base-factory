# event-updates (15)

> Issues where events were missing, emitted with wrong data, or state updates were incorrectly ordered.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Immediate stake cache updates enable reward distribution without P-Chain confirmation

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
When operators call `initializeValidatorStakeUpdate()`, the middleware immediately writes the new stake value into `nodeStakeCache[currentEpoch + 1][validationID]`, even though the P-Chain has not yet confirmed the update. Reward calculations via `getOperatorUsedStakeCachedPerEpoch` use this cached value without checking whether the P-Chain update is confirmed. This creates a window where rewards are distributed based on an unconfirmed, potentially invalid stake increase.

**Impact:**
Operators can receive inflated epoch rewards based on unconfirmed stake increases. The reward distribution diverges from actual validated P-Chain state, allowing potential manipulation of reward eligibility.

**Recommended Mitigation:**
Gate reward calculations on P-Chain confirmation status. Do not update `nodeStakeCache` until `completeValidatorWeightUpdate` confirms the P-Chain acknowledgment, or explicitly exclude validators with pending updates from reward calculations.

---

**[中文版本]**

**描述：**
当操作员调用 `initializeValidatorStakeUpdate()` 时，中间件立即将新质押值写入 `nodeStakeCache[currentEpoch + 1][validationID]`，尽管 P-Chain 尚未确认此更新。通过 `getOperatorUsedStakeCachedPerEpoch` 进行的奖励计算使用此缓存值而不检查 P-Chain 更新是否已确认，在奖励基于未确认（可能无效）的质押增加进行分配的时间窗口内存在漏洞。

**影響：**
操作员可基于未确认的质押增加获得虚高的 epoch 奖励，奖励分配偏离实际验证的 P-Chain 状态，允许潜在的奖励资格操纵。

**修復建議：**
将奖励计算限制在 P-Chain 确认状态后。在 `completeValidatorWeightUpdate` 确认 P-Chain 确认前不更新 `nodeStakeCache`，或明确将有待处理更新的验证者排除在奖励计算之外。

---

## 2. Weights Misapplied When Routes Are Not Grouped By TokenIn

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
`F-2025-13566` — In `CoreAggregator::_executeSwap`, the splitter renormalizes weights each time `tokenIn` changes, creating separate per-`tokenIn` weight blocks. If routes with the same `tokenIn` are interleaved rather than grouped contiguously, their allocations are computed across multiple blocks with independent normalization. This makes allocations order-dependent: for example, two routes with weight 5000 each for token A will not produce a 50%/50% split if a route for token B appears between them; instead, the second A-block treats the remaining A balance with fresh normalization, resulting in under-allocation and residual balances stuck on the aggregator.

**Impact:**
Swap routes with interleaved `tokenIn` groups produce incorrect allocations deviating from the planner's intent. Residual token balances may be left on the aggregator contract and are not returned to users.

**Recommended Mitigation:**
Enforce that routes are grouped contiguously by `tokenIn` — revert if the same `tokenIn` reappears after a different `tokenIn` has been processed. Alternatively, pre-aggregate per-`tokenIn` weights before execution.

---

**[中文版本]**

**描述：**
`F-2025-13566` — 在 `CoreAggregator::_executeSwap` 中，分割器在每次 `tokenIn` 变化时重新归一化权重，为每个 `tokenIn` 创建独立的权重块。若相同 `tokenIn` 的路由交错排列而非连续分组，其分配在多个具有独立归一化的块中计算，使分配结果依赖于顺序：例如两条各权重 5000 的 token A 路由之间插入一条 token B 路由，第二个 A 块以剩余 A 余额重新归一化，导致分配不足和残余余额滞留在聚合器中。

**影響：**
`tokenIn` 组交错的交换路由产生偏离规划者意图的错误分配，残余代币余额可能滞留在聚合器合约中，无法返还给用户。

**修復建議：**
强制路由按 `tokenIn` 连续分组——若同一 `tokenIn` 在不同 `tokenIn` 处理后再次出现则回滚。或在执行前预先聚合每个 `tokenIn` 的权重。

---

## 3. Consider emitting event when synchronizing lstLiabilityPrincipal

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` synchronizes `$$.lstLiabilityPrincipal`, which may change due to positive or negative `stETH` rebasing. This function modifies a critical state variable but emits no event. Off-chain monitors and auditors have no visibility into when and by how much `lstLiabilityPrincipal` changes.

**Impact:**
No direct security risk, but the absence of an event for state changes to `lstLiabilityPrincipal` reduces protocol observability, making it harder to detect anomalies or track yield provider accounting off-chain.

**Recommended Mitigation:**
Emit an event from `_syncExternalLiabilitySettlement` that includes at least the delta change (or old and new values) of `lstLiabilityPrincipal`.

---

**[中文版本]**

**描述：**
`LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` 同步 `$$.lstLiabilityPrincipal`，该值可能因 `stETH` 正负 rebase 而变化。此函数修改了关键状态变量但不发出任何事件，链下监控和审计人员无法了解 `lstLiabilityPrincipal` 何时变化及变化幅度。

**影響：**
无直接安全风险，但缺少 `lstLiabilityPrincipal` 状态变更事件降低了协议可观察性，使链下检测异常或追踪收益提供者核算更加困难。

**修復建議：**
在 `_syncExternalLiabilitySettlement` 中发出事件，至少包含 `lstLiabilityPrincipal` 的增量变化（或新旧值）。

---

## 4. Country updates is not reducing from the storage the prev country

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`RegistryService::setCountry` calls `adjustInvestorCountsAfterCountryChange` with the previous country as a parameter; however, the function ignores the `_prevCountry` parameter. When an investor's country is updated, the investor count for the new country is incremented, but the count for the previous country is never decremented. Over time, country-level investor counts diverge from reality, becoming permanently inflated for countries that investors have left.

**Impact:**
Country-level investor counts become inaccurate over time. Any compliance logic, limits, or reporting that relies on these counts will produce incorrect results, potentially allowing compliance breaches.

**Recommended Mitigation:**
In `adjustInvestorCountsAfterCountryChange`, add a call to decrement the investor count for `_prevCountry` when the investor holds a non-zero balance: `adjustInvestorsCountsByCountry(_prevCountry, _id, CommonUtils.IncDec.Decrease)`.

---

**[中文版本]**

**描述：**
`RegistryService::setCountry` 将旧国家作为参数传递给 `adjustInvestorCountsAfterCountryChange`，但该函数忽略了 `_prevCountry` 参数。更新投资者国家时，新国家的投资者计数被递增，但旧国家的计数从不递减。随时间推移，国家级投资者计数与实际情况出现偏差，离开的国家计数被永久虚高。

**影響：**
国家级投资者计数随时间变得不准确，任何依赖这些计数的合规逻辑、限额或报告将产生错误结果，可能导致合规违规。

**修復建議：**
在 `adjustInvestorCountsAfterCountryChange` 中添加对 `_prevCountry` 投资者计数的递减调用：`adjustInvestorsCountsByCountry(_prevCountry, _id, CommonUtils.IncDec.Decrease)`。

---

## 5. DVNPublisher::publish does not enforce a maximum age for updates

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`DVNPublisher::publish` validates that `request.timestamp` is not in the future but does not check whether the request is already stale at submission time. Staleness is only enforced during `DVNPublisher::execute`. This means already-expired update requests can be published and will clutter `_pendingRequests` until they are eventually rejected at execution time, wasting storage and computation.

**Impact:**
No direct security risk, but stale requests pollute the pending queue, adding unnecessary gas overhead when iterating pending requests and increasing confusion for off-chain consumers.

**Recommended Mitigation:**
Add a staleness check in `publish()`: require `request.timestamp + maxStaleness >= block.timestamp` before accepting the request.

---

**[中文版本]**

**描述：**
`DVNPublisher::publish` 验证 `request.timestamp` 不在未来，但不检查提交时请求是否已经过时。过时性仅在 `DVNPublisher::execute` 时才执行。这意味着已过期的更新请求可以被发布，并在 `_pendingRequests` 中堆积，直到执行时最终被拒绝，浪费存储和计算资源。

**影響：**
无直接安全风险，但过时请求污染待处理队列，在遍历待处理请求时增加不必要的燃气开销，并增加链下消费者的混淆。

**修復建議：**
在 `publish()` 中添加过时性检查：在接受请求前要求 `request.timestamp + maxStaleness >= block.timestamp`。

---

## 6. ExitWithinGracePeriod event emits inaccurate amountReceived for adapter vaults

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
In `SablierBob::exitWithinGracePeriod`, the `ExitWithinGracePeriod` event always emits the share balance as `amountReceived`, regardless of whether an adapter vault was used. For adapter vaults, the actual WETH received depends on a Curve stETH→ETH swap subject to slippage, so the emitted value does not reflect what the user actually received. The adapter emits its own separate event with the accurate amount, but the parent event is misleading.

**Impact:**
Off-chain indexers and users relying on the `ExitWithinGracePeriod` event will see an incorrect `amountReceived` for adapter vault exits, leading to inaccurate accounting or user-facing reporting.

**Recommended Mitigation:**
Have `SablierLidoAdapter::unstakeForUserWithinGracePeriod` return the WETH amount received, and use that return value in the `ExitWithinGracePeriod` event for adapter vault exits.

---

**[中文版本]**

**描述：**
在 `SablierBob::exitWithinGracePeriod` 中，无论是否使用适配器 vault，`ExitWithinGracePeriod` 事件始终将份额余额作为 `amountReceived` 发出。对于适配器 vault，实际收到的 WETH 取决于受滑点影响的 Curve stETH→ETH 交换，因此发出的值与用户实际收到的不符。适配器会发出包含准确金额的独立事件，但父事件具有误导性。

**影響：**
依赖 `ExitWithinGracePeriod` 事件的链下索引器和用户将看到适配器 vault 退出的错误 `amountReceived`，导致核算或面向用户的报告不准确。

**修復建議：**
让 `SablierLidoAdapter::unstakeForUserWithinGracePeriod` 返回收到的 WETH 金额，并在适配器 vault 退出的 `ExitWithinGracePeriod` 事件中使用该返回值。

---

## 7. Fee structure updates can trigger accrual after loan has ended

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
Both `AccountableYield` and `AccountableOpenTerm` implement `onFeeStructureChange()` which calls `_accrueFees()` or `_accrueInterest()` when `_loan.startTime != 0`. Since `startTime` is set once at loan initiation and is never reset when a loan is repaid or defaults, fee structure changes after loan termination still trigger the accrual hooks. For `AccountableYield`, this can cause large catch-up fee share minting for elapsed time since the last accrual, unexpectedly diluting holders.

**Impact:**
Fee structure updates after a loan has ended can trigger unintended fee accrual on terminated loans, minting excess fee shares and diluting vault token holders.

**Recommended Mitigation:**
Gate `onFeeStructureChange()` on the current loan state rather than `startTime != 0`. Only accrue when the loan is in an active/ongoing state (e.g., `loanState == LoanState.OngoingDynamic`).

---

**[中文版本]**

**描述：**
`AccountableYield` 和 `AccountableOpenTerm` 均实现了 `onFeeStructureChange()`，当 `_loan.startTime != 0` 时调用 `_accrueFees()` 或 `_accrueInterest()`。由于 `startTime` 在贷款发起时设置且在贷款偿还或违约时从不重置，贷款终止后的费用结构变更仍会触发应计钩子。对于 `AccountableYield`，这可能导致自上次应计以来经过时间的大量追补费用份额铸造，意外稀释持有者。

**影響：**
贷款结束后的费用结构更新可能在已终止贷款上触发意外费用应计，铸造过多费用份额并稀释 vault 代币持有者。

**修復建議：**
将 `onFeeStructureChange()` 的条件改为当前贷款状态而非 `startTime != 0`，仅在贷款处于活跃/进行中状态时应计（例如 `loanState == LoanState.OngoingDynamic`）。

---

## 8. Game creator can call TriviaChoicePrompt::revealSolutions before the reactionDeadline or end of game, griefing players from submitting answers while still retaining player entry fees

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`TriviaChoicePrompt::revealSolutions` does not validate that the `reactionDeadline` has passed before revealing solutions. Once solutions are revealed, `commitReaction` reverts with `SolutionAlreadyRevealed`, preventing any further answer submissions. A malicious game creator can immediately reveal solutions after revealing the question, blocking players from submitting answers while still retaining all entry fees paid by players.

**Impact:**
A malicious game creator can grief players by revealing solutions early, preventing participation and earning points, while keeping the entry fees paid by all participants.

**Recommended Mitigation:**
Add a check in `revealSolutions` to prevent early revelation — for example, require that the game has ended (checking `sessionManager.games(_gameId).state == SessionState.Ended`) before solutions can be revealed.

---

**[中文版本]**

**描述：**
`TriviaChoicePrompt::revealSolutions` 在揭晓答案前不验证 `reactionDeadline` 是否已过。一旦答案被揭晓，`commitReaction` 将以 `SolutionAlreadyRevealed` 回滚，阻止任何后续答案提交。恶意游戏创建者可在揭示问题后立即揭晓答案，阻止玩家提交答案，同时保留所有玩家支付的入场费。

**影響：**
恶意游戏创建者可通过提前揭晓答案骚扰玩家，阻止参与和获取积分，同时保留所有参与者支付的入场费。

**修復建議：**
在 `revealSolutions` 中添加检查以防止提前揭晓——例如，要求游戏已结束（检查 `sessionManager.games(_gameId).state == SessionState.Ended`）才能揭晓答案。

---

## 9. Lack of event emissions on important state changes

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
Multiple setter and configuration functions across `Access`, `Administrator`, `Bridge`, `BridgeMB`, `BridgeCCIP`, `Manager`, `OracleAdapter`, `LockBox`, `YToken`, and `YTokenL2` modify critical state variables — including administrator roles, treasury addresses, custody wallets, oracle parameters, and bridge configurations — without emitting any events. This makes all such changes invisible to off-chain monitoring systems and auditors.

**Impact:**
Critical protocol configuration changes are invisible to off-chain monitoring. This significantly increases the risk that malicious or erroneous configuration changes go undetected until they affect user operations.

**Recommended Mitigation:**
Add and emit appropriate events in all setter functions that modify protocol-critical state variables.

---

**[中文版本]**

**描述：**
`Access`、`Administrator`、`Bridge`、`BridgeMB`、`BridgeCCIP`、`Manager`、`OracleAdapter`、`LockBox`、`YToken` 和 `YTokenL2` 中的多个设置和配置函数修改关键状态变量（包括管理员角色、金库地址、托管钱包、预言机参数和桥接配置），但不发出任何事件，使所有此类变更对链下监控系统和审计人员不可见。

**影響：**
关键协议配置变更对链下监控不可见，显著增加了恶意或错误配置变更在影响用户操作前未被检测到的风险。

**修復建議：**
在所有修改协议关键状态变量的设置函数中添加并发出适当事件。

---

## 10. Market pause flag not enforced by ConditionalTokens::splitPosition

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`PredictionMarketV3ManagerCLOB::pauseMarket` sets a per-market `paused` flag. The exchange enforces this flag via `_requireMarketOpen`, which checks `manager.isMarketPaused`. However, `ConditionalTokens::splitPosition` only checks the market state (open/closed) and never checks the pause flag. Any user can call `splitPosition` directly to mint fresh YES/NO tokens on a market that the admin intended to freeze, bypassing the pause.

**Impact:**
Users can create new market exposure on paused markets, undermining emergency pause mechanisms designed to prevent new positions during incidents.

**Recommended Mitigation:**
Add a pause guard to `ConditionalTokens::splitPosition`: `require(!manager.isMarketPaused(marketId), "market paused")`.

---

**[中文版本]**

**描述：**
`PredictionMarketV3ManagerCLOB::pauseMarket` 为每个市场设置 `paused` 标志，交易所通过检查 `manager.isMarketPaused` 的 `_requireMarketOpen` 执行此标志。然而，`ConditionalTokens::splitPosition` 仅检查市场状态（开放/关闭），从不检查暂停标志。任何用户可直接调用 `splitPosition` 在管理员预期冻结的市场上铸造新的 YES/NO 代币，绕过暂停机制。

**影響：**
用户可在已暂停的市场上创建新的市场敞口，破坏旨在阻止事件期间新建仓位的紧急暂停机制。

**修復建議：**
为 `ConditionalTokens::splitPosition` 添加暂停保护：`require(!manager.isMarketPaused(marketId), "market paused")`。

---

## 11. Off-By-One Error in _exceedsMaxClaimablePeriods()

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
`F-2025-13597` — The `_exceedsMaxClaimablePeriods()` function in `Stargate.sol` uses strict greater-than (`>`) comparison when checking if a token has exceeded the configured maximum claimable periods, but the period counting formula requires greater-than-or-equal (`>=`). When counting inclusively from `firstClaimablePeriod` to `lastClaimablePeriod`, the total is `lastClaimablePeriod - firstClaimablePeriod + 1`. The function omits the `+1`, so the check `(difference > maxClaimablePeriods)` only returns `true` when there are at least `maxClaimablePeriods + 1` periods — allowing exactly one extra period beyond the intended maximum.

**Impact:**
Users can claim rewards for one period beyond the configured maximum `maxClaimablePeriods`, resulting in unintended over-distribution of rewards.

**Recommended Mitigation:**
Change the comparison from `difference > maxClaimablePeriods` to `difference >= maxClaimablePeriods` to correctly enforce the inclusive period limit.

---

**[中文版本]**

**描述：**
`F-2025-13597` — `Stargate.sol` 中的 `_exceedsMaxClaimablePeriods()` 函数使用严格大于（`>`）比较来检查代币是否超过配置的最大可领取周期数，但周期计数公式需要大于等于（`>=`）。从 `firstClaimablePeriod` 到 `lastClaimablePeriod` 的包含计数总数为 `lastClaimablePeriod - firstClaimablePeriod + 1`，函数遗漏了 `+1`，导致检查 `(difference > maxClaimablePeriods)` 仅在至少有 `maxClaimablePeriods + 1` 个周期时返回 `true`，允许比预期最大值多一个周期。

**影響：**
用户可在配置的最大 `maxClaimablePeriods` 之外多领取一个周期的奖励，导致意外的超额奖励分发。

**修復建議：**
将比较从 `difference > maxClaimablePeriods` 改为 `difference >= maxClaimablePeriods`，以正确执行包含性周期限制。

---

## 12. Optimize setters by emitting event before state updates

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaUSD::setKeeper`, `SherpaUSD::setOperator`, `SherpaUSD::setAutoTransfer`, `SherpaVault::setDepositsEnabled`, and `SherpaVault::setStableWrapper` each create an unnecessary memory variable to store the old value before updating storage, solely to include it in the event emission. By emitting the event before the state update, the current storage value (old value) can be read directly and the memory variable can be eliminated.

**Impact:**
No security risk. Minor gas inefficiency due to unnecessary memory variable allocation on every setter call.

**Recommended Mitigation:**
Restructure each affected setter to emit the event first with the current storage value as the old value, then update the storage variable, eliminating the intermediate memory variable.

---

**[中文版本]**

**描述：**
`SherpaUSD::setKeeper`、`SherpaUSD::setOperator`、`SherpaUSD::setAutoTransfer`、`SherpaVault::setDepositsEnabled` 和 `SherpaVault::setStableWrapper` 各自创建不必要的内存变量存储旧值，仅为在事件发出时使用。通过在状态更新前发出事件，可直接读取当前存储值（旧值），消除内存变量。

**影響：**
无安全风险，每次设置函数调用时因不必要的内存变量分配存在轻微燃气低效。

**修復建議：**
重构每个受影响的设置函数，先以当前存储值为旧值发出事件，再更新存储变量，消除中间内存变量。

---

## 13. SherpaUSD::consumeTotalStakedApproval and SherpaUSD::consumeAccountingApproval callable by anyone

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaUSD::consumeTotalStakedApproval` and `consumeAccountingApproval` are externally callable by any address. They accept a `vault` parameter and gate state changes with `if (msg.sender != vault) revert OnlyVaultCanConsume()`. Because approvals are keyed by caller address, any address can call these functions using its own address as `vault` and clear its own (likely empty) approval entry. While this is not exploitable to clear a real vault's approvals, the open callable surface with an explicit `vault` parameter creates confusion about the intended access control.

**Impact:**
No direct exploitability. However, the misleading interface design can confuse integrators and reviewers about who is authorized to consume approvals and may lead to errors in future integrations.

**Recommended Mitigation:**
Remove the `vault` parameter and restrict the functions to be callable only by the authorized keeper via the `onlyKeeper` modifier, following the principle of least privilege.

---

**[中文版本]**

**描述：**
`SherpaUSD::consumeTotalStakedApproval` 和 `consumeAccountingApproval` 可被任意地址从外部调用。它们接受 `vault` 参数并通过 `if (msg.sender != vault) revert OnlyVaultCanConsume()` 限制状态更改。由于授权以调用者地址为键，任意地址可将自己的地址作为 `vault` 调用这些函数，清除自己的（可能为空的）授权条目。虽然这无法清除真实 vault 的授权，但带有显式 `vault` 参数的开放调用面会对预期访问控制产生混淆。

**影響：**
无直接可利用性，但误导性的接口设计可能使集成者和审查者对授权消费者产生混淆，并在未来集成中导致错误。

**修復建議：**
移除 `vault` 参数，通过 `onlyKeeper` 修饰符将函数限制为仅由授权 keeper 调用，遵循最小权限原则。

---

## 14. State change without event

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
Four critical setter functions — `MyriadCTFExchange::setNegRiskAdapter`, `NegRiskAdapter::setExchange`, `NegRiskAdapter::setTreasury`, and `PredictionMarketV3ManagerCLOB::setNegRiskAdapter` — update addresses that gate core protocol functionality (cross-market matching, treasury routing, and admin resolution) without emitting any events. Off-chain monitors cannot detect changes to these privileged addresses.

**Impact:**
Unauthorized or malicious changes to critical protocol addresses go undetected by off-chain monitoring systems, increasing the risk of undetected attacks or configuration errors.

**Recommended Mitigation:**
Add and emit dedicated events in each of the four setter functions to log the old and new address values on every update.

---

**[中文版本]**

**描述：**
四个关键设置函数——`MyriadCTFExchange::setNegRiskAdapter`、`NegRiskAdapter::setExchange`、`NegRiskAdapter::setTreasury` 和 `PredictionMarketV3ManagerCLOB::setNegRiskAdapter`——在更新控制核心协议功能（跨市场匹配、金库路由和管理员解析）的地址时不发出任何事件，链下监控无法检测到这些特权地址的变更。

**影響：**
对关键协议地址的未授权或恶意更改不会被链下监控系统发现，增加了未被发现的攻击或配置错误的风险。

**修復建議：**
在四个设置函数中各添加并发出专用事件，在每次更新时记录旧值和新值。

---

## 15. forceTransfer is Blocked by Pause

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Tokenizer.Estate.txt`

**Description:**
`F-2025-14166` — `RealEstateToken` has a `forceTransfer` function accessible only to `ROLE_TRANSFER` that is intended to bypass standard restrictions (locks, whitelists) via `_forceBypass = true` for emergency situations such as lost keys or legal compliance. However, the contract inherits `ERC20PausableUpgradeable`, and `forceTransfer` internally calls `_transfer → _update → super._update`, which checks `whenNotPaused`. The `_forceBypass` flag is not recognized by the parent `ERC20PausableUpgradeable` contract, so if the contract is paused, `forceTransfer` reverts with `EnforcedPause()`. An admin who pauses the contract during a security incident cannot use `forceTransfer` to rescue funds without first unpausing, potentially exposing the contract to further exploitation.

**Impact:**
Emergency administrative fund recovery via `forceTransfer` is blocked when the contract is paused, defeating the purpose of the emergency override and forcing admins to unpause before performing emergency actions.

**Recommended Mitigation:**
Override the `_update` function to also bypass the pause check when `_forceBypass` is `true`, or implement a dedicated transfer path for `forceTransfer` that does not go through the pausable `super._update`.

---

**[中文版本]**

**描述：**
`F-2025-14166` — `RealEstateToken` 拥有仅限 `ROLE_TRANSFER` 访问的 `forceTransfer` 函数，旨在通过 `_forceBypass = true` 绕过标准限制（锁定、白名单）用于紧急情况（如钥匙丢失或法律合规）。然而合约继承自 `ERC20PausableUpgradeable`，`forceTransfer` 内部调用 `_transfer → _update → super._update`，后者检查 `whenNotPaused`。`_forceBypass` 标志不被父合约 `ERC20PausableUpgradeable` 识别，因此合约暂停时 `forceTransfer` 以 `EnforcedPause()` 回滚。在安全事件中暂停合约的管理员无法使用 `forceTransfer` 救援资金，不得不先取消暂停，可能使合约面临进一步利用。

**影響：**
合约暂停时，通过 `forceTransfer` 进行的紧急行政资金救援被阻止，违背了紧急覆盖的目的，迫使管理员在执行紧急操作前取消暂停。

**修復建議：**
重写 `_update` 函数，在 `_forceBypass` 为 `true` 时同样绕过暂停检查，或为 `forceTransfer` 实现不经过可暂停 `super._update` 的专用转账路径。
