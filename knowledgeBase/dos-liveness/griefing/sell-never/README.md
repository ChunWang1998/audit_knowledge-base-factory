# sell-never (13)

> Issues where sell operations, unstaking, or exits are permanently or temporarily blocked.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Excessive Initial Sell Tax Can Severely Restrict Exits and Is Inconsistent With the Contract's Tax Limit Invariants

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
KnoxNet is deployed with `marketingSellTaxBps = 9000`, producing an effective sell tax of 90%. Sellers retain only 10% of any gross sell amount. The same contract enforces a 65% cap on sell taxes via `setTaxConfig` for all subsequent administrative updates, but this invariant is not applied to the initial deployment values. The initial configuration therefore violates the contract's own stated constraint from the moment of deployment.

**Impact:**
During the initial deployment state, selling is economically impractical — sellers receive only 10 cents per dollar sold. The inconsistency between the initial 90% effective rate and the 65% administrative cap invalidates assumptions made by users, auditors, and integrators about the maximum possible sell tax.

**Recommended Mitigation:**
Align the initial tax configuration with the same bounds enforced by `setTaxConfig`. The deployment-time `marketingSellTaxBps` and all related values should satisfy the 65% sell-tax maximum from the outset. Maintain a single invariant across both initialisation and the `setTaxConfig` update path.

---

**[中文版本]**

**描述：**
KnoxNet 部署时将 `marketingSellTaxBps` 设为 9000，实际卖出税率高达 90%，而 `setTaxConfig` 对后续更新强制执行 65% 上限，初始部署值违反了合约自身声明的约束。

**影響：**
初始状态下卖出极不划算，卖家每笔交易仅能保留10%。不一致性使用户、审计方和集成方对最大卖出税率的假设失效。

**修復建議：**
将初始税收配置与 `setTaxConfig` 执行的边界对齐，从部署之初就满足65%卖出税上限，保持初始化与管理更新路径的单一约束。

---

## 2. Unvalidated taxDenominator Breaks Tax Cap Invariants and Causes Hardcoded Limits to Misapply in Both Directions

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
`setTaxConfig` allows the owner to update `taxDenominator` to any value without validation, while tax cap checks compare raw tax values against the hardcoded constant `6500`. The effective tax rate is `taxBps / taxDenominator`, not `taxBps / 10000`, so when `taxDenominator` is set below `10000`, the actual effective rate can exceed 100% (causing reverts) even though the raw numerator passes the `6500` check. When `taxDenominator` is set above `10000`, the cap becomes stricter than intended. The limit checks are completely decoupled from the denominator used in actual tax calculation.

**Impact:**
The effective buy and sell tax can exceed the stated 65% cap when `taxDenominator < 10000`, potentially making transfers confiscatory or reverting entirely. When `taxDenominator > 10000`, the limits are effectively tighter than documented, creating unexpected behaviour in both directions.

**Recommended Mitigation:**
Either fix `taxDenominator` to `10000` and remove it from `setTaxConfig`, or normalise all cap checks to use the configured denominator (e.g., `require(_liquiditySellTaxBps + _marketingSellTaxBps <= 6500 * _taxDenominator / 10000)`) so that percentage-based invariants remain meaningful regardless of the denominator value.

---

**[中文版本]**

**描述：**
`setTaxConfig` 允许所有者任意修改 `taxDenominator`，而税率上限检查使用固定常量 `6500` 而非百分比。当 `taxDenominator < 10000` 时，即使通过 `6500` 检查的原始值也可能产生超过100%的实际税率；当 `taxDenominator > 10000` 时，限制比预期更严格。

**影響：**
实际有效税率可能超过声明的65%上限或低于预期，分别造成转账混乱/回滚或限制比文档严格。

**修復建議：**
将 `taxDenominator` 固定为 `10000` 并从 `setTaxConfig` 中移除；或将上限检查归一化为使用配置的分母，确保百分比约束始终有效。

---

## 3. AccountableOpenTerm manual interest rate proposal is unbounded

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`AccountableOpenTerm` has two paths for setting interest rates. The DVN publishing path enforces a cap: `publishRate(uint256 newRate)` checks `newRate` against `MAX_PUBLISH_RATE` before applying. The manual path — `proposeInterestRate(...)` queuing a pending rate followed by `approveInterestRateChange()` applying it — does not cap the queued rate. As a result, an extremely high rate could be queued and approved through the manual flow without any bound check.

**Impact:**
An uncapped manual interest rate proposal could result in a rate far exceeding the DVN-enforced maximum being applied, causing disproportionate interest accrual, unexpected borrower liabilities, and deviation from protocol safety parameters.

**Recommended Mitigation:**
Add the same `MAX_PUBLISH_RATE` bounds check inside `proposeInterestRate(...)` so that invalid or extreme rates cannot be queued in the first place.

---

**[中文版本]**

**描述：**
`AccountableOpenTerm` 的 DVN 发布路径在应用新利率前检查 `MAX_PUBLISH_RATE`，但手动路径 `proposeInterestRate` + `approveInterestRateChange` 不对待审利率做任何上限检查，可能排入极端利率。

**影響：**
过高的利率被批准后会导致利息过度累积，给借款人带来非预期负债，偏离协议安全参数。

**修復建議：**
在 `proposeInterestRate(...)` 中增加与 DVN 路径一致的 `MAX_PUBLISH_RATE` 边界检查，防止极端利率被排入队列。

---

## 4. Auto-Swap Reverts During Sell Execution Can Deny User Exits

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
In KnoxNet's `_transferFrom`, the `_autoSwapBack` function is called synchronously inline during qualifying sell transactions. This function performs external Uniswap router calls (`swapExactTokensForETHSupportingFeeOnTransferTokens` and optionally `addLiquidityETH`) that are not wrapped in a try/catch. If either call reverts — for example due to rounding reducing the swap amount to zero, or an invalid ETH/token ratio for liquidity addition — the entire user sell transaction reverts. Users cannot complete their exit independently of the tax-processing logic.

**Impact:**
User sell transactions can be blocked whenever the auto-swap path is temporarily invalid, regardless of whether the user's transfer itself is valid. All sellers are denied exit until privileged configuration is updated or auto-swap conditions change.

**Recommended Mitigation:**
Decouple the tax-processing path from the user sell path. Wrap external router calls inside `_autoSwapBack` in a `try/catch` block so that a failed auto-swap is skipped and deferred rather than propagating a revert to the seller's transaction.

---

**[中文版本]**

**描述：**
KnoxNet 在用户卖出时同步调用 `_autoSwapBack`，其内部的外部路由器调用（swap + 可选的流动性添加）没有 try/catch 保护。任何路由调用失败都会导致整个用户卖出交易回滚，用户无法独立完成退出。

**影響：**
任何时候自动换回路径失效，所有卖家的交易都会被阻塞，直到特权配置更新或自动换回条件恢复正常。

**修復建議：**
将税收处理路径与用户卖出路径解耦，在 `_autoSwapBack` 中对外部路由调用使用 try/catch，失败时跳过并推迟处理而非使卖出交易回滚。

---

## 5. Buy and Sell Fees Unexpectedly Applied During Liquidity Provision Operations

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The NTE token's tax logic classifies any token transfer to an AMM pair as a sell (applying `sellTaxBps`) and any transfer from an AMM pair to a user as a buy (applying `buyTaxBps`). This causes liquidity providers who add tokens to the AMM pool to pay a sell tax, and to pay a buy tax when withdrawing their liquidity. These are internal liquidity management operations that should not be subject to trading taxes, but the current implementation treats them identically to market-order sells and buys.

**Impact:**
Liquidity providers are taxed on both deposit and withdrawal, creating significant unexpected losses — for example a 2.5% tax on both sides produces an effective position cost of approximately 95.06% of the intended value. This may discourage liquidity provisioning, reducing pool depth and worsening price volatility for all users.

**Recommended Mitigation:**
Adjust the tax logic to exempt liquidity provision and removal operations from buy and sell tax application. This can be achieved by detecting whether a transfer to/from the AMM pair originates from a liquidity management router function, or by providing dedicated wrapper functions that explicitly bypass tax accumulation for liquidity providers.

---

**[中文版本]**

**描述：**
NTE 代币的税收逻辑将所有向 AMM 池的转账视为卖出（收取卖出税），将从 AMM 池到用户的转账视为买入（收取买入税），导致流动性提供者在添加和移除流动性时均需缴税，而非仅在市场交易时。

**影響：**
流动性提供者在存入和提取时均被征税，产生意外损失（如双侧2.5%税率下约损失4.94%），可能严重抑制流动性提供意愿。

**修復建議：**
将流动性添加和移除操作从买卖税逻辑中豁免，可通过检测转账是否来自流动性管理路由，或提供专用包装函数明确绕过税收累积。

---

## 6. Fee Distribution in _autoSwapBack Uses Configured Tax Rates as Proxy for Actual Fee Composition, Causing Systematic Misallocation Between Marketing and Liquidity

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
KnoxNet collects all taxed tokens — from both buys and sells — into a single undifferentiated balance. When `_autoSwapBack` distributes this pool, it estimates the liquidity share using the ratio of configured buy/sell liquidity tax rates to total tax rates. This estimate is only accurate when buy volume and sell volume are equal. In practice, because buy-side and sell-side tax structures typically differ, the ratio systematically over-allocates to one receiver or under-allocates to the other depending on real trading volumes, which the contract does not track.

**Impact:**
Fee distribution between marketing and liquidity receivers deviates materially from the actual fee composition collected from each source. The error magnitude scales with the asymmetry between buy and sell tax configurations and the imbalance in trading volumes. In extreme configurations the misallocation can be several times the correct amount.

**Recommended Mitigation:**
Track fee accrual separately by purpose using distinct counters (e.g., `accumulatedMarketingTokens` and `accumulatedLiquidityTokens`) updated in `_applyTax` at the point of collection. `_autoSwapBack` should then consume these tracked amounts directly rather than estimating from tax rate ratios.

---

**[中文版本]**

**描述：**
KnoxNet 将所有税收代币汇入单一资金池，分发时以配置税率之比估算营销/流动性分配比例。此估算仅在买卖量相等时准确，实际上买卖税率结构不同导致系统性错误分配。

**影響：**
营销和流动性接收方所获费用与实际收取费用严重偏差，在极端配置下偏差可达数倍。

**修復建議：**
在 `_applyTax` 中按用途分别追踪费用累积（如专用计数器），`_autoSwapBack` 直接消耗追踪量而非从税率比例估算。

---

## 7. Judge can designate arbitrary winner who is neither maker nor taker

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
When calling `Bet::resolve`, the nominated judge has the authority to designate any arbitrary address as the winner to receive the bet winnings. The function does not enforce that the designated winner is either the `maker` or the `taker` of the bet. A judge can therefore direct the entire winnings to themselves or to any third party unrelated to the bet.

**Impact:**
The judge can steal winnings by designating themselves as the winner, or redirect winnings to any arbitrary address, defeating the fundamental purpose of a two-party bet contract between maker and taker.

**Recommended Mitigation:**
`Bet::resolve` should enforce that the designated winner is either the `maker` or the `taker` by adding an explicit check before executing the payout.

---

**[中文版本]**

**描述：**
`Bet::resolve` 中，被指定的裁判可以将赌注奖励分配给任意地址，不限于 `maker` 或 `taker`。裁判可将奖励分配给自己或任何不相关的第三方。

**影響：**
裁判可窃取赌注奖励或将其重定向至任意地址，完全违背双方约定的博彩合约的基本目的。

**修復建議：**
在 `Bet::resolve` 中增加检查，确保指定的获胜者只能是 `maker` 或 `taker`。

---

## 8. MintType is almost never enforced

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
The contract defines a `MintType` enum with values `OpenMint`, `Whitelist`, `Claim`, and `Burn` to distinguish different minting modes. However, none of the minting functions enforce the actual mint type: there is no whitelist check for `MintType.Whitelist`, the `claim` function does not require `data.mintType == MintType.Claim`, and `burnAndMint` does not require `data.mintType == MintType.Burn`. The only usage of `data.mintType` is within `_validateSignature` to ensure the signed value matches the input, but the business-logic enforcement for each type is absent.

**Impact:**
The `MintType` system provides no actual runtime enforcement, meaning any mint function can be called with any `MintType` value as long as the signature is valid. Whitelist restrictions, burn requirements, and claim conditions are not enforced, allowing unintended minting paths.

**Recommended Mitigation:**
Add explicit mint type validation in each minting function. For example, ensure `claim` reverts unless `data.mintType == MintType.Claim`, and `burnAndMint` reverts unless `data.mintType == MintType.Burn`, and so on.

---

**[中文版本]**

**描述：**
合约定义了 `MintType` 枚举（`OpenMint`/`Whitelist`/`Claim`/`Burn`），但各铸造函数实际上均未执行对应类型检查：无白名单校验、`claim` 不检查 `MintType.Claim`、`burnAndMint` 不检查 `MintType.Burn`。`MintType` 仅在签名验证中使用，缺乏业务逻辑层面的强制执行。

**影響：**
`MintType` 系统无实际运行时约束，任何铸造函数可使用任意 `MintType` 值，白名单、销毁和领取条件均形同虚设。

**修復建議：**
在各铸造函数中增加显式类型检查，如 `claim` 要求 `data.mintType == MintType.Claim`，`burnAndMint` 要求 `data.mintType == MintType.Burn`。

---

## 9. Pledge can't successfully complete unless RemoraToken is paused

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`PledgeManager::checkPledgeStatus` calls `IRemoraRWAToken(propertyToken).unpause()` when the funding goal is reached. However, OpenZeppelin's `PausableUpgradeable::_unpause` has a `whenPaused` modifier and reverts if the contract is not already paused. If `RemoraToken` is deployed in an unpaused state — or was previously unpaused — the call to `unpause()` will revert, causing `checkPledgeStatus` to revert and blocking the pledge from ever completing.

**Impact:**
The pledge flow cannot conclude successfully unless the `RemoraToken` is in a paused state at the time `checkPledgeStatus` is called. This creates a silent operational dependency that can prevent the pledge from reaching its `Concluded` state.

**Recommended Mitigation:**
Guard the `unpause()` call with a check that the token is actually paused before attempting to unpause it, or use a try/catch to handle the case where the token is already unpaused.

---

**[中文版本]**

**描述：**
`PledgeManager::checkPledgeStatus` 在达到募资目标时调用 `unpause()`，但 OpenZeppelin 的 `_unpause` 带有 `whenPaused` 修饰器，若代币未处于暂停状态则会回滚，导致质押无法完成。

**影響：**
除非 `RemoraToken` 处于暂停状态，否则质押流程无法正常完成，产生隐性操作依赖。

**修復建議：**
在调用 `unpause()` 前检查代币是否处于暂停状态；或使用 try/catch 处理已解除暂停的情况。

---

## 10. Prompt::finalizedAnswer is never set

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
The `Prompt` struct contains a `finalizedAnswer` field intended to record the final answer for a question once all votes are revealed. The session manager reveals questions and decodes prompts into `revealedQuestions[questionId]`, but no strategy contract exposes a function to set `finalizedAnswer` after vote revelation. The field is populated in the struct but its setter pathway is entirely absent.

**Impact:**
`Prompt::finalizedAnswer` is never set after answers are revealed, meaning any downstream logic or integration relying on this field to determine the final outcome of a question receives an empty string rather than the actual answer.

**Recommended Mitigation:**
Either implement a function in the relevant strategy contracts to set `finalizedAnswer` during or after vote resolution, or remove the field from the struct if it serves no functional purpose.

---

**[中文版本]**

**描述：**
`Prompt` 结构体中的 `finalizedAnswer` 字段用于记录问题的最终答案，但所有策略合约均未提供在投票揭示后设置该字段的函数，导致该字段始终为空字符串。

**影響：**
任何依赖 `finalizedAnswer` 获取问题最终结果的下游逻辑或集成都将收到空字符串。

**修復建議：**
在相关策略合约中实现设置 `finalizedAnswer` 的函数；或若该字段无实际用途则从结构体中移除。

---

## 11. StakedTrUSD.reportLoss is blocked during vesting, preventing handling of bad debt and allowing users to exit fully, forcing remaining stakers to bear the loss

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Tori Finance.txt`

**Description:**
`StakedTrUSD::reportLoss` includes a guard `if (getUnvestedAmount() > 0) revert StillVesting()` that prevents loss reporting whenever rewards are actively vesting (the vesting period is 8 hours). When a collateral default occurs during a vesting window, the admin cannot burn assets to reflect the loss. Informed users can exploit this delay by calling `cooldownShares` or `cooldownAssets`, which compute their exit value at the current inflated share price and transfer underlying assets to the `TrUsdSilo` before the loss is recorded. Once assets are in the silo they are no longer subject to exchange rate changes. After the vesting window ends and the loss is reported, only the remaining assets in the vault are burned, while early exits suffer no loss.

**Impact:**
The protocol's risk-sharing mechanism is broken. Users who detect the vesting-blocked loss early can exit at full value, while remaining stakers absorb 100% of the bad debt. This creates a first-mover advantage that incentivises bank-run behaviour during bad debt events.

**Recommended Mitigation:**
Remove the `getUnvestedAmount() > 0` check from `reportLoss`. Loss reporting is a critical risk management operation that must not be blocked by the vesting schedule. Allow the admin to intervene at any time; if necessary, implement logic to proportionally deduct from both vested and unvested reward balances when reporting a loss.

---

**[中文版本]**

**描述：**
`StakedTrUSD::reportLoss` 在奖励归属期（8小时）内会因 `StillVesting` 错误而回滚。当抵押品违约发生在归属期内，管理员无法报告损失。知情用户可利用这一延迟以当前虚高份额价格提前退出，将损失转嫁给剩余质押者。

**影響：**
协议风险共担机制失效。先行退出的用户零损失，剩余质押者承担全部坏账，造成挤兑激励。

**修復建議：**
从 `reportLoss` 中移除 `getUnvestedAmount() > 0` 检查，允许管理员随时报告损失，不受归属期限制。

---

## 12. TrustService::changeEntityOwner can overwrite existing _newOwner record, breaking 1-1 relationship between owners and addresses

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`TrustService::changeEntityOwner` updates the forward mapping from entity to owner but also writes the reverse mapping from owner address to entity. When called with a `_newOwner` address that already owns another entity, the reverse mapping entry for `_newOwner` is overwritten, orphaning the second entity. The two-step ownership transfer process does not check whether `_newOwner` is already recorded as an owner of a different entity, breaking the intended 1-to-1 relationship between owner addresses and entities.

**Impact:**
After the ownership transfer, the `_newOwner` address is associated with the transferred entity in the reverse mapping, while its previously owned entity becomes unreachable via `getEntityByOwner`. This orphaned entity can no longer be managed correctly by owner-based access paths.

**Recommended Mitigation:**
Add a modifier or check in `changeEntityOwner` that reverts if the `_newOwner` address is already registered as an owner of any existing entity (`onlyNewEntityOwner(_newOwner)`).

---

**[中文版本]**

**描述：**
`TrustService::changeEntityOwner` 在更新实体到所有者的正向映射时，也会覆盖所有者地址到实体的反向映射。若 `_newOwner` 已拥有另一实体，反向映射被覆盖后，原实体变成孤儿，无法通过 `getEntityByOwner` 访问，破坏了所有者与实体的一对一关系。

**影響：**
所有权转移后，`_newOwner` 的原实体变为孤儿，无法通过所有者地址路径管理，导致数据不一致。

**修復建議：**
在 `changeEntityOwner` 中增加检查（如修饰器 `onlyNewEntityOwner(_newOwner)`），若 `_newOwner` 已是某实体的所有者则回滚。

---

## 13. Wrong value is returned in upperLookupRecentCheckpoint

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`Checkpoint::upperLookupRecentCheckpoint` is designed to return the key, value, and position of the most recent checkpoint whose key is less than or equal to the search key. The hinted code path contains a bug: when a valid hint is provided, the function reads the checkpoint position using `at()` (which correctly resolves the stored value from `self._values[checkpoint._value]`), but then constructs the return value by re-indexing into `self._values[checkpoint._value]` a second time, treating the already-resolved value as an index. This causes an array-bounds panic or returns a completely wrong value.

**Impact:**
When a hint is provided to `upperLookupRecentCheckpoint`, the function reverts with an array out-of-bounds error or returns an incorrect value, undermining the reliability of the checkpoint lookup mechanism and any protocol logic that depends on it.

**Recommended Mitigation:**
Modify the hinted code path to use `checkpoint._value` directly (the value already returned by `at()`) rather than re-indexing into `self._values[checkpoint._value]`.

---

**[中文版本]**

**描述：**
`Checkpoint::upperLookupRecentCheckpoint` 在提供有效提示时，代码错误地将 `at()` 已返回的已解析值再次作为索引访问 `self._values[]`，导致数组越界panic或返回错误值。

**影響：**
提供提示时，检查点查询函数会以数组越界错误回滚或返回错误值，破坏依赖此查找机制的所有协议逻辑。

**修復建議：**
在提示代码路径中直接使用 `at()` 返回的 `checkpoint._value`，不再对其做二次索引。
