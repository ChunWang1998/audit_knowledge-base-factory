# tranche-withdrawers (13)

> Issues affecting tranche withdrawal mechanics, investor transfer restrictions, or game refund flows.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Primary Contributor Deposits Are Not Recorded, Leading to Permanent Fund Loss and Incorrect Payouts

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
In the Komiti ROSCA (Rotating Savings and Credit Association) contract, `joinGroupWithJointContributor` allows a primary contributor to invite a secondary contributor, with both parties contributing half the required share. The function accepts `msg.value` from the primary contributor but the line that records the deposit in the `s_contributions` mapping is commented out. Consequently, the primary contributor's deposit is accepted but never stored. When the primary contributor attempts to cancel and recover their funds via `returnFunds`, the contract reads `s_contributions[groupId][msg.sender]` which returns 0 and transfers nothing. During payout, `distributeJointPayout` calculates the secondary's share as `secondaryContribution / totalContributions` where `totalContributions` equals only the secondary's recorded contribution, producing a ratio of 1 — awarding the entire payout to the secondary contributor.

**Impact:**
Primary contributors permanently lose their deposited funds on cancellation. In successful group cycles, the primary contributor receives zero payout while the secondary contributor unknowingly receives double their intended share. This is a direct and permanent loss of user funds.

**Recommended Mitigation:**
Re-enable the commented-out line in `joinGroupWithJointContributor` that updates `s_contributions[groupId][msg.sender]` with `msg.value`, ensuring the primary contributor's deposit is properly recorded for both refund and payout calculations.

---

**[中文版本]**

**描述：**
Komiti 合约中 `joinGroupWithJointContributor` 接受主要贡献者的 `msg.value` 但未将存款记录到 `s_contributions` 映射（对应代码行被注释掉）。取消时退款返回0；分配时次要贡献者获得全部收益，主要贡献者分文未得。

**影響：**
主要贡献者永久损失存款；成功轮次中主要贡献者获零分配，次要贡献者意外获得双份回报。

**修復建議：**
恢复 `joinGroupWithJointContributor` 中被注释掉的 `s_contributions[groupId][msg.sender] += msg.value` 语句。

---

## 2. Withdrawers of sUSDe always incur a loss because parameters passed from Tranche::_withdraw to CDO::withdraw are inverted

**Severity:** 🔴 Critical
**Source:** `cyfrin/tranches.md`

**Description:**
`Tranche::_withdraw` calls `cdo.withdraw(address(this), token, baseAssets, tokenAssets, receiver)`, but `CDO::withdraw` expects `(tranche, token, tokenAmount, baseAssets, receiver)` — the `tokenAssets` and `baseAssets` parameters are swapped. Because of this inversion, the `Strategy::withdraw` function receives `baseAssets` (the USDe equivalent value) in the position where it expects `tokenAmount` (the sUSDe amount), and vice versa. The strategy then calls `sUSDe.previewWithdraw(baseAssets)` to calculate shares, using the wrong value, and transfers far fewer sUSDe tokens to the user than the amount requested. For example, given a sUSDe/USDe rate of 1:1.5, a user requesting 100 sUSDe will receive only approximately 66 sUSDe while 150 JRTranche shares are burned.

**Impact:**
Every withdrawal of sUSDe incurs a guaranteed loss. Users receive significantly fewer sUSDe tokens than requested while the full corresponding TrancheShares are burned. The loss magnitude increases as the sUSDe/USDe exchange rate diverges from 1:1.

**Recommended Mitigation:**
Correct the parameter order in `Tranche::_withdraw` when calling `CDO::withdraw`, passing `tokenAssets` before `baseAssets` to match the expected function signature.

---

**[中文版本]**

**描述：**
`Tranche::_withdraw` 调用 `cdo.withdraw` 时将 `baseAssets` 和 `tokenAssets` 参数顺序反转，导致策略合约用错误的值计算 sUSDe 份额，用户收到的 sUSDe 远少于请求量，而 TrancheShares 全额被销毁。

**影響：**
所有 sUSDe 提款均必然亏损，损失程度随 sUSDe/USDe 汇率偏离1:1而加剧。

**修復建議：**
修正 `Tranche::_withdraw` 中调用 `CDO::withdraw` 的参数顺序，将 `tokenAssets` 放在 `baseAssets` 之前。

---

## 3. Impossible for user to get refund after re-joining a rescheduled game which is subsequently cancelled

**Severity:** 🟠 High
**Source:** `cyfrin/protocol.md`

**Description:**
When a game is rescheduled, users may call `leaveRescheduledGame` to receive a refund, which sets `hasRefunded[gameId][player] = true`. If the user chooses to re-join the same game after rescheduling, and the game is subsequently cancelled, `refundCancelledGame` reverts because `hasRefunded` is still set to `true` from the earlier refund. The user's second entry fee is permanently locked in the immutable `SessionManager` contract with no recovery path.

**Impact:**
Users who exercise their right to leave and re-join a rescheduled game are silently prevented from recovering their entry fee if the game is subsequently cancelled. The funds are permanently locked.

**Recommended Mitigation:**
Reset `hasRefunded[gameId][player]` to `false` in `DepositManager::_payEntryFee` when a user re-joins a game, so that their refund eligibility is reinstated for the new entry fee they paid.

---

**[中文版本]**

**描述：**
用户离开改期游戏并退款后 `hasRefunded` 被设为 true。若用户重新加入同一游戏且游戏随后被取消，`refundCancelledGame` 因 `hasRefunded == true` 而回滚，第二次报名费永久锁定在合约中。

**影響：**
行使"离开改期游戏"权利后重新加入的用户，若游戏取消将无法取回报名费，资金永久锁定。

**修復建議：**
在 `_payEntryFee` 中，当用户重新加入时将 `hasRefunded[gameId][player]` 重置为 false，恢复其退款资格。

---

## 4. Cheaper not to cache calldata array length

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`BulkBalanceChecker::getTokenBalances` caches the `calldata` array length into a local variable before iterating, but it is cheaper in EVM gas terms not to cache `calldata` length. Accessing `calldata` length directly in the loop condition avoids a memory write and the associated overhead, as `calldata` length reads are already cheap.

**Impact:**
Minor unnecessary gas overhead on each call to the affected function, marginally increasing the cost for callers.

**Recommended Mitigation:**
Remove the cached length variable in `BulkBalanceChecker::getTokenBalances` and access `calldata` array length directly in the loop condition.

---

**[中文版本]**

**描述：**
`BulkBalanceChecker::getTokenBalances` 将 `calldata` 数组长度缓存到局部变量，但直接在循环中访问 `calldata` 长度在 EVM 中更省 gas，因为 `calldata` 长度读取本身已很廉价。

**影響：**
每次调用产生轻微的额外 gas 开销。

**修復建議：**
移除缓存长度变量，在循环条件中直接访问 `calldata` 数组长度。

---

## 5. Code duplication in function overrides that only add modifiers

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
`SecuritizeRWASegWrap` overrides four functions (`deposit`, `redeem`, `redeemById`, `depositById`) from its parent `RWASegWrap`, each containing an identical copy of the parent's implementation logic with the only addition being the `receiverIsSender` modifier. Rather than calling `super.deposit(...)` with the additional modifier applied, the entire function body is duplicated. This means any future changes to the parent implementation must also be manually replicated in the child contract.

**Impact:**
Code duplication increases maintenance burden and creates a divergence risk: changes to the parent implementation will not automatically propagate to the overrides, potentially introducing inconsistencies or missing bug fixes.

**Recommended Mitigation:**
Refactor each overridden function to simply call the corresponding `super` function, applying the `receiverIsSender` modifier at the override level rather than duplicating the entire implementation.

---

**[中文版本]**

**描述：**
`SecuritizeRWASegWrap` 重写了四个父合约函数，每个重写版本仅添加了 `receiverIsSender` 修饰器，但完整复制了父合约的实现逻辑，而非调用 `super`。未来父合约变更需要手动同步到子合约。

**影響：**
代码重复增加维护负担，存在父子合约逻辑分歧风险，可能遗漏 bug 修复或引入不一致。

**修復建議：**
将每个重写函数重构为调用对应的 `super` 函数，在重写层应用 `receiverIsSender` 修饰器。

---

## 6. Consider switching to ReentrancyGuardTransient

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`NegRiskAdapter`, `MyriadCTFExchange`, and `PredictionMarketV3ManagerCLOB` inherit from `ReentrancyGuard` or `ReentrancyGuardUpgradeable`, which store the lock flag in a regular storage slot. Each guarded call must perform a cold read and write on this slot. OpenZeppelin ≥ 5.1.0 (the project already uses v5.3.0) provides `ReentrancyGuardTransient` and `ReentrancyGuardTransientUpgradeable`, which store the flag in transient storage, avoiding persistent storage writes and reducing gas cost per guarded call.

**Impact:**
Every call to a `nonReentrant` function incurs unnecessary cold storage overhead. Switching to transient storage would reduce gas costs across all guarded functions.

**Recommended Mitigation:**
Replace `ReentrancyGuard` with `ReentrancyGuardTransient` for `NegRiskAdapter` and `ReentrancyGuardUpgradeable` with `ReentrancyGuardTransientUpgradeable` for `MyriadCTFExchange` and `PredictionMarketV3ManagerCLOB`. Remove the `__ReentrancyGuard_init()` call from `initialize()` for the upgradeable variants since the transient variant requires no initialisation.

---

**[中文版本]**

**描述：**
三个合约继承了将重入锁存储在普通存储槽的 `ReentrancyGuard`，每次受保护调用都需要对冷存储槽进行读写。OpenZeppelin ≥ 5.1.0（项目已使用v5.3.0）提供了基于瞬态存储的 `ReentrancyGuardTransient`，可降低每次调用的 gas 成本。

**影響：**
每次 `nonReentrant` 函数调用产生不必要的冷存储开销。

**修復建議：**
将相关合约替换为对应的 Transient 变体，并移除升级版合约中的 `__ReentrancyGuard_init()` 调用。

---

## 7. Don't cache calldata array length

**Severity:** 🟡 Medium
**Source:** `cyfrin/harbor.md`

**Description:**
`ChainValidator::setValidChains` and `setInvalidChains` cache `calldata` array lengths into local variables before iterating. Reading `calldata` length directly in the loop condition is cheaper than caching it, because `calldata` is not stored in memory and its length is directly accessible without a memory allocation.

**Impact:**
Minor unnecessary gas overhead on each call to the affected functions.

**Recommended Mitigation:**
Remove the cached length variables in the affected functions and access `calldata` array length directly in the loop conditions.

---

**[中文版本]**

**描述：**
`ChainValidator::setValidChains` 和 `setInvalidChains` 将 `calldata` 数组长度缓存至局部变量，而直接在循环中读取 `calldata` 长度更省 gas。

**影響：**
每次调用产生轻微额外 gas 开销。

**修復建議：**
移除缓存长度变量，在循环条件中直接访问 `calldata` 数组长度。

---

## 8. JR Tranche is susceptible to bankrun scenarios given that SharesCooldown finalization allows to bypass minimumJrtSrtRatio and first withdrawers from JR Tranche get a better cooldown and fees compared to late withdrawers

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The protocol enforces a `minimumJrtSrtRatio` hard floor to ensure the Junior Tranche always retains sufficient buffer relative to the Senior Tranche. This constraint is applied in `Accounting::maxWithdrawInner` but is explicitly bypassed when the share owner is the `SharesCooldown` contract. Users who lock JRT shares in `SharesCooldown` can redeem them via `finalize` without the hard-floor check, withdrawing up to the full JRT NAV and violating `minimumJrtSrtRatio`. Additionally, because cooldown periods and fees increase with `coverage`, early withdrawers pay lower fees and wait shorter periods than late withdrawers, incentivising a rush to exit before coverage degrades further.

**Impact:**
The `minimumJrtSrtRatio` solvency constraint can be bypassed via `SharesCooldown`, leaving the system below the hard floor. This creates bank-run dynamics where first-movers exit cheaply and late withdrawers face higher costs, trapped liquidity, and magnified losses.

**Recommended Mitigation:**
Enforce the `minimumJrtSrtRatio` constraint within `finalizeWithFee` to prevent early exit from bypassing the hard floor. Additionally, consider inverting the fee/cooldown structure so that first withdrawers (when coverage is high) pay higher fees than late withdrawers, disincentivising premature exits.

---

**[中文版本]**

**描述：**
`minimumJrtSrtRatio` 硬下限在 `SharesCooldown` 合约持有份额时被绕过，用户可通过 `finalize` 提取超出安全阈值的 JRT NAV。同时，先提款者因 `coverage` 较高而享受更低费率和更短冷却期，产生银行挤兑动机。

**影響：**
`minimumJrtSrtRatio` 约束被绕过，系统跌破硬下限；早期提款者以低成本退出，晚期提款者面临更高费用、锁定流动性和更大损失。

**修復建議：**
在 `finalizeWithFee` 中强制执行 `minimumJrtSrtRatio` 约束；考虑调整费率结构，使早期提款者（`coverage` 高时）缴纳更高费用以抑制提前退出。

---

## 9. Misleading variable name to set the asset for the Tranche

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
The variable used to configure the `asset` that a `Tranche` will operate with is named `stakedAsset`. The two assets in the system are `USDe` (the base asset) and `sUSDe` (the staked version). The name `stakedAsset` misleads readers into thinking the Tranche's underlying asset is `sUSDe` rather than `USDe`, which is the actual base asset used in calculations and withdrawals.

**Impact:**
The misleading variable name increases the risk of developer errors during integration, review, or future maintenance, as the implied semantics of `stakedAsset` conflict with the actual role of the variable.

**Recommended Mitigation:**
Rename the variable to `baseAsset` or another name that does not suggest staking, to accurately reflect that it refers to the base underlying asset (`USDe`) of the Tranche.

---

**[中文版本]**

**描述：**
用于设置 `Tranche` 资产的变量被命名为 `stakedAsset`，但系统的两种资产是 `USDe`（基础资产）和 `sUSDe`（质押版本），该命名误导读者认为 Tranche 的底层资产是 `sUSDe` 而非实际的 `USDe`。

**影響：**
误导性命名增加集成、审计或维护时的开发者错误风险，隐含语义与变量实际作用相矛盾。

**修復建議：**
将变量重命名为 `baseAsset` 或其他不含质押含义的名称，准确反映其为 Tranche 的基础底层资产（`USDe`）。

---

## 10. SessionManager::revealGameQuestion doesn't validate that input _questionId belongs to input _gameId

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::revealGameQuestion` takes `_gameId` and `_questionId` as inputs and checks that `_gameId` is in the `Ongoing` state, then delegates to `QuestionManager::_revealPrompt`. Neither `_revealPrompt` nor the prompt contracts verify that `_questionId` actually belongs to `_gameId`. A game creator whose game is not in `Ongoing` state can bypass this check by passing a `_gameId` of any other ongoing game, revealing their question using the ongoing status of a different game.

**Impact:**
Game creators can bypass the `Ongoing` state requirement by referencing an unrelated ongoing game's ID, allowing questions to be revealed for games that are not yet in the correct state.

**Recommended Mitigation:**
Add a validation step in `QuestionManager::_revealPrompt` (or in `SessionManager::revealGameQuestion`) that verifies the `_questionId` belongs to the provided `_gameId`. Apply the same fix to `startAndRevealGameQuestion`.

---

**[中文版本]**

**描述：**
`SessionManager::revealGameQuestion` 检查 `_gameId` 是否处于 `Ongoing` 状态，但不验证 `_questionId` 是否属于 `_gameId`。游戏创建者可通过传入其他正在进行的游戏 ID 来绕过状态检查，揭示其本不应公开的问题。

**影響：**
游戏创建者可绕过 `Ongoing` 状态要求，提前揭示其游戏问题，破坏游戏公平性。

**修復建議：**
在 `_revealPrompt` 或 `revealGameQuestion` 中增加验证，确认 `_questionId` 确实属于 `_gameId`。

---

## 11. Tokens that were locked when lockUpTime > 0 will be impossible to unlock if lockUpTime is set to zero

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`LockUpManager::_unlockTokens` returns early if `lockUpTime == 0`, skipping the loop that clears individual token locks. If tokens were locked under a previous `lockUpTime > 0` configuration and `lockUpTime` is subsequently set to zero, those locks are never cleared. Users can still transfer their tokens normally (since the zero lockUpTime causes no lock enforcement), but if `lockUpTime` is later set back above zero, the stale lock entries violate the invariant that `tokensLocked <= tokenBalance`, causing underflow reverts in transfer logic when computing unlocked balance.

**Impact:**
Tokens locked under a non-zero `lockUpTime` cannot be programmatically unlocked if `lockUpTime` is later set to zero. If `lockUpTime` is subsequently re-enabled, the stale locks cause transfer reverts for affected users.

**Recommended Mitigation:**
In `_unlockTokens`, process the lock-clearing loop regardless of whether `lockUpTime == 0`, so that existing locks are always cleared when the unlock function is called.

---

**[中文版本]**

**描述：**
`LockUpManager::_unlockTokens` 在 `lockUpTime == 0` 时提前返回，跳过清除代币锁定的循环。若代币在 `lockUpTime > 0` 时被锁定后 `lockUpTime` 被设为零，这些锁定永远不会被清除，若 `lockUpTime` 后续重新设为非零值，残留锁定会导致转账下溢回滚。

**影響：**
在非零 `lockUpTime` 下锁定的代币在 `lockUpTime` 设为零后无法被程序解锁；重新启用锁定机制后，受影响用户的转账会回滚。

**修復建議：**
在 `_unlockTokens` 中，无论 `lockUpTime` 是否为零，都应执行锁定清除循环。

---

## 12. Transferring all the investor balance from a non-us investor to a new us investor allows to bypass the usInvestorLimit

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceLibrary::completeTransferCheck()` checks the US investor limit only when `_args.fromInvestorBalance > _args.value`, i.e., when the sender does not transfer their entire balance. If a non-US investor transfers their entire balance to a new US investor, the condition `_args.fromInvestorBalance > _args.value` evaluates to false and the entire conditional block is short-circuited, bypassing the limit check. The new US investor is then added by `adjustInvestorsCountsByCountry`, incrementing the US investor count beyond the configured limit.

**Impact:**
US securities regulations requiring a strict investor headcount limit can be bypassed by routing full-balance transfers from non-US investors to new US investors. This could lead to regulatory non-compliance and violations of country-specific transfer restrictions.

**Recommended Mitigation:**
Update the conditional in `completeTransferCheck` to also trigger the limit check when the sender is a US investor transferring their full balance, since in that case the US investor count would decrease by one and offset the new addition. The specific fix is to replace `_args.fromInvestorBalance > _args.value` with `(_args.fromRegion != US || _args.fromInvestorBalance > _args.value)`.

---

**[中文版本]**

**描述：**
`completeTransferCheck()` 仅在 `fromInvestorBalance > value`（即未转出全部余额）时检查美国投资者限制。非美国投资者转出全部余额时，该条件为假，整个条件块被短路，绕过人数上限检查，新美国投资者被添加后超出限制。

**影響：**
可通过非美国投资者全额转账至新美国投资者来绕过美国投资者人数上限，违反证券监管要求。

**修復建議：**
将条件 `_args.fromInvestorBalance > _args.value` 改为 `(_args.fromRegion != US || _args.fromInvestorBalance > _args.value)`，确保在所有场景下都正确执行人数上限检查。

---

## 13. User can join after the first question is revealed to gain an advantage over other users

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::joinGame` permits joining when the game state is either `Created` or `Ongoing`. `SessionManager::startAndRevealGameQuestion` atomically moves the game to `Ongoing` and reveals the first question. As a result, a user can observe the revealed first question and only join games where they know the answer, gaining an informational advantage over players who joined before the question was disclosed.

**Impact:**
A user can always guarantee they know the answer to the first question before committing to join, providing a systematic unfair advantage over honest participants who joined during the `Created` phase without knowing any questions.

**Recommended Mitigation:**
Disallow joining a game once it is in the `Ongoing` state by restricting `joinGame` to only accept games in the `Created` state.

---

**[中文版本]**

**描述：**
`joinGame` 允许在游戏 `Created` 或 `Ongoing` 状态时加入。由于 `startAndRevealGameQuestion` 在启动游戏的同时揭示第一道题，用户可以观察到题目后再决定是否加入，享有信息优势。

**影響：**
用户可在了解第一道题答案后再加入游戏，对在 `Created` 阶段未知题目加入的诚实玩家形成系统性不公平优势。

**修復建議：**
在 `joinGame` 中只允许加入 `Created` 状态的游戏，禁止在 `Ongoing` 状态下加入。
