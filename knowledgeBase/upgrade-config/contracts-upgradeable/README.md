# contracts-upgradeable (19)

> Issues specific to upgradeable contract patterns — missing modifiers, incorrect inheritance, or interface non-compliance. Part of [upgrade-config](../README.md).

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. `AllowList::hasTradeRestriction` mutability should be set to `view`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`AllowList::hasTradeRestriction` modifies no state and reads data only, yet it is not declared `view`. As a result, any contract or off-chain caller treating it as state-modifying must issue an actual transaction to call it, paying unnecessary gas costs. Marking the function `view` signals to callers that it is safe to call without a transaction and allows compilers to optimize call paths accordingly.

**Impact:**
Callers pay unnecessary gas costs by issuing transactions to what is effectively a read-only function. This can complicate integrations with off-chain systems that query trade restriction status frequently.

**Recommended Mitigation:**
Add the `view` modifier to `AllowList::hasTradeRestriction`.

---

**[中文版本]**

**描述：**
`AllowList::hasTradeRestriction` 不修改任何状态，仅读取数据，但未声明为 `view`。因此任何将其视为状态修改函数的调用方必须发起实际交易，产生不必要的 gas 费用。将函数标记为 `view` 可向调用方表明可安全地无需交易调用，并允许编译器优化调用路径。

**影響：**
调用方通过发起交易调用实际上只读的函数而产生不必要的 gas 成本，这可能使频繁查询交易限制状态的链下系统集成复杂化。

**修復建議：**
为 `AllowList::hasTradeRestriction` 添加 `view` 修饰符。

---

## 2. Anyone should be able to conclude the game once winners have been determined

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
Once winners have been fully determined for a game session, the final step of concluding the game and distributing rewards should be permissionless. Currently, only certain privileged roles can call the `concludeGame` function even after all the results are known. This creates a liveness dependency on a trusted actor. If that actor becomes unavailable, unresponsive, or malicious, game conclusion can be indefinitely delayed, locking winner funds.

**Impact:**
Players whose game results are fully determined cannot receive their rewards without cooperation from a privileged role. Indefinite delay of game conclusion locks the winner's earned rewards, reducing trust in the protocol.

**Recommended Mitigation:**
Allow any address to call `concludeGame` once the game results have been finalized, removing the role restriction for this terminal state transition.

---

**[中文版本]**

**描述：**
一旦游戏会话的获胜者被完全确定，结束游戏和分配奖励的最终步骤应该是无许可的。目前即使结果已知，仍只有特定特权角色可调用 `concludeGame` 函数，形成对受信任行为者的活跃性依赖，若该行为者不可用、无响应或恶意，游戏结束可能无限期推迟，锁定获胜者资金。

**影響：**
游戏结果已完全确定的玩家在没有特权角色配合的情况下无法获得奖励，游戏结束的无限期延迟锁定了获胜者已赚取的奖励，降低对协议的信任。

**修復建議：**
一旦游戏结果最终确定，允许任何地址调用 `concludeGame`，移除此终态转换的角色限制。

---

## 3. `ComplianceServiceRegulated::getComplianceTransferableTokens` should call `IDSLockManager::getTransferableTokensForInvestor`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::getComplianceTransferableTokens` is used to determine how many tokens an investor can transfer. The current implementation computes transferable tokens by subtracting locked amounts via `IDSLockManager::getLockedTokens`, but the `IDSLockManager` interface also exposes a purpose-built function `getTransferableTokensForInvestor` that already correctly encapsulates this logic. Using the lower-level call bypasses any special handling in `getTransferableTokensForInvestor` (e.g., edge cases, future extensions), creating a divergence risk between the two codepaths.

**Impact:**
Future changes to locking logic in `IDSLockManager::getTransferableTokensForInvestor` would not be reflected in `ComplianceServiceRegulated`, leading to incorrect compliance checks and potential unauthorized transfers or over-blocking.

**Recommended Mitigation:**
Replace the lower-level computation with a direct call to `IDSLockManager::getTransferableTokensForInvestor` to ensure consistent behavior.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::getComplianceTransferableTokens` 用于确定投资者可转账的代币数量。当前实现通过 `IDSLockManager::getLockedTokens` 减去锁定金额计算可转账代币，但 `IDSLockManager` 接口还提供了专门为此目的构建的 `getTransferableTokensForInvestor` 函数。使用低层调用绕过了 `getTransferableTokensForInvestor` 中的特殊处理，造成两个代码路径之间的发散风险。

**影響：**
`IDSLockManager::getTransferableTokensForInvestor` 中锁定逻辑的未来变更不会反映在 `ComplianceServiceRegulated` 中，导致合规检查不正确，可能产生未授权转账或过度阻止。

**修復建議：**
将低层计算替换为对 `IDSLockManager::getTransferableTokensForInvestor` 的直接调用，以确保行为一致。

---

## 4. `DefaultSession::assertResults` should verify input `sessionId` belongs to a game associated with its instance

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::assertResults` accepts a caller-supplied `sessionId` and processes it without verifying that the provided `sessionId` is actually associated with the `DefaultSession` instance's own game. An attacker or integration mistake could pass an arbitrary `sessionId` belonging to a different game, causing result assertions and state changes to be applied to the wrong game context.

**Impact:**
Results from one game can be incorrectly asserted for a different game's session, corrupting game state and potentially causing incorrect payouts or outcomes to be recorded.

**Recommended Mitigation:**
At the start of `assertResults`, verify that `sessionId` belongs to the game associated with this `DefaultSession` instance by checking the game registry or the session's game reference.

---

**[中文版本]**

**描述：**
`DefaultSession::assertResults` 接受调用者提供的 `sessionId` 并处理，但不验证该 `sessionId` 是否实际与该 `DefaultSession` 实例自身的游戏关联。攻击者或集成错误可能传入属于不同游戏的任意 `sessionId`，导致结果断言和状态变更应用于错误的游戏上下文。

**影響：**
一个游戏的结果可能被错误地断言到另一个游戏的会话中，破坏游戏状态并可能导致记录错误的赔付或结果。

**修復建議：**
在 `assertResults` 开始时，通过检查游戏注册表或会话的游戏引用，验证 `sessionId` 是否属于与此 `DefaultSession` 实例关联的游戏。

---

## 5. Extra data should only be decoded when its length is exactly 96 bytes

**Severity:** 🟡 Medium
**Source:** `cyfrin/vii.md`

**Description:**
In `VII`, the extra data field appended to certain messages is decoded under the assumption that its length is always 96 bytes (encoding three 32-byte values). However, the code does not validate the actual length before decoding. If the extra data field contains fewer or more than 96 bytes, ABI decoding will either revert unexpectedly or decode garbage values. The inconsistency between expected and actual extra data length can arise from versioning issues, protocol upgrades, or integration bugs.

**Impact:**
Transactions that include malformed extra data (not exactly 96 bytes) will revert unexpectedly, causing liveness failures. Alternatively, incorrectly sized extra data that doesn't revert during decoding may inject garbage values into protocol state.

**Recommended Mitigation:**
Add a length check before decoding: only proceed with decoding the extra data if `extraData.length == 96`; otherwise handle the case gracefully (revert with a clear error or skip decoding).

---

**[中文版本]**

**描述：**
在 `VII` 中，附加到某些消息的额外数据字段被解码时假设其长度始终为 96 字节（编码三个 32 字节值）。但代码在解码前不验证实际长度。若额外数据字段包含少于或多于 96 字节，ABI 解码将意外 revert 或解码出垃圾值，这种不一致可能由版本问题、协议升级或集成错误引起。

**影響：**
包含格式错误额外数据（不完全是 96 字节）的交易将意外 revert，造成活跃性故障；或未在解码时 revert 的错误大小额外数据可能向协议状态注入垃圾值。

**修復建議：**
在解码前添加长度检查：仅在 `extraData.length == 96` 时进行解码，否则优雅处理（以清晰错误 revert 或跳过解码）。

---

## 6. `IBeforeInitializeHook` should be added to the `AngstromL2` inheritance chain

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`AngstromL2` implements the `beforeInitialize` hook function, which is intended to satisfy the `IBeforeInitializeHook` interface required by Uniswap v4's pool manager. However, `AngstromL2` does not explicitly declare `IBeforeInitializeHook` in its inheritance list. Without the explicit interface declaration, the Uniswap v4 pool manager's interface-detection mechanism (via `ERC165` or hook flags inspection) may not recognize `AngstromL2` as implementing the before-initialize hook, potentially causing hook calls to be silently skipped.

**Impact:**
The `beforeInitialize` hook in `AngstromL2` may not be called by the Uniswap v4 pool manager if the interface is not properly declared, bypassing any validation or setup logic intended to run during pool initialization.

**Recommended Mitigation:**
Add `IBeforeInitializeHook` to the `AngstromL2` inheritance chain explicitly.

---

**[中文版本]**

**描述：**
`AngstromL2` 实现了 `beforeInitialize` 钩子函数以满足 Uniswap v4 池管理器要求的 `IBeforeInitializeHook` 接口，但未在继承列表中明确声明该接口。没有明确的接口声明，Uniswap v4 池管理器的接口检测机制可能无法识别 `AngstromL2` 实现了 before-initialize 钩子，可能导致钩子调用被静默跳过。

**影響：**
若接口未正确声明，`AngstromL2` 中的 `beforeInitialize` 钩子可能不会被 Uniswap v4 池管理器调用，绕过任何预期在池初始化期间运行的验证或设置逻辑。

**修復建議：**
明确将 `IBeforeInitializeHook` 添加到 `AngstromL2` 继承链中。

---

## 7. In `RemoraToken::adminClaimPayout, adminTransferFrom` don't call `hasSignedDocs` when `checkTC == false`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`RemoraToken::adminClaimPayout` correctly wraps the `hasSignedDocs` call in a `if (checkTC)` conditional, avoiding an unnecessary check when terms-and-conditions enforcement is disabled. However, `RemoraToken::adminTransferFrom` calls `hasSignedDocs` unconditionally, regardless of the `checkTC` flag. This inconsistency means that even when the admin disables TC checks via `setCheckTC(false)`, the `adminTransferFrom` path still performs and may revert on the signed docs check, causing unexpected failures.

**Impact:**
`adminTransferFrom` reverts unnecessarily when `checkTC == false`, making admin-initiated transfers fail even when TC enforcement is intentionally disabled. This inconsistency also creates confusion about the effective state of TC enforcement.

**Recommended Mitigation:**
Wrap the `hasSignedDocs` call inside `adminTransferFrom` with the same `if (checkTC)` conditional used in `adminClaimPayout`.

---

**[中文版本]**

**描述：**
`RemoraToken::adminClaimPayout` 正确地将 `hasSignedDocs` 调用包裹在 `if (checkTC)` 条件中，避免在禁用条款和条件强制执行时进行不必要检查。但 `RemoraToken::adminTransferFrom` 无条件调用 `hasSignedDocs`，忽略 `checkTC` 标志。这种不一致意味着即使管理员通过 `setCheckTC(false)` 禁用 TC 检查，`adminTransferFrom` 路径仍执行签名文档检查并可能 revert。

**影響：**
当 `checkTC == false` 时 `adminTransferFrom` 不必要地 revert，使管理员发起的转账在 TC 强制执行被有意禁用时也会失败，还会造成对 TC 强制执行有效状态的混淆。

**修復建議：**
在 `adminTransferFrom` 中用与 `adminClaimPayout` 相同的 `if (checkTC)` 条件包裹 `hasSignedDocs` 调用。

---

## 8. Incorrect link to Angle contracts across protocol

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
Several contracts in the Parallel protocol contain hardcoded or configured references to Angle protocol contracts (e.g., governor, treasury, or core addresses). An audit revealed that some of these links point to outdated or incorrect contract addresses — either stale addresses from a previous deployment or addresses from the wrong Angle deployment (e.g., mainnet vs. testnet, or a different version). These incorrect links cause calls to silently fail or interact with the wrong contract, producing no useful effect or unexpected behavior.

**Impact:**
Protocol functions that depend on Angle contracts may silently fail or interact with incorrect contracts, undermining the correctness of governance, treasury, or other cross-protocol operations.

**Recommended Mitigation:**
Audit all contract address references to Angle contracts and update them to the correct, current deployment addresses. Consider using a registry pattern to manage external contract addresses to simplify future updates.

---

**[中文版本]**

**描述：**
Parallel 协议中的多个合约包含对 Angle 协议合约（如治理、财库或核心地址）的硬编码或配置引用。审计发现部分引用指向过时或错误的合约地址，可能是过期地址或来自错误 Angle 部署（如主网与测试网，或不同版本）。这些不正确的引用导致调用静默失败或与错误合约交互。

**影響：**
依赖 Angle 合约的协议函数可能静默失败或与不正确的合约交互，破坏治理、财库或其他跨协议操作的正确性。

**修復建議：**
审计所有对 Angle 合约的地址引用并更新为正确的当前部署地址，考虑使用注册表模式管理外部合约地址以简化未来更新。

---

## 9. Lack of `_disableInitializers` in upgradeable contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
Several upgradeable contracts in YieldFi do not call `_disableInitializers()` in their constructor. The OpenZeppelin upgradeable pattern recommends calling `_disableInitializers()` in constructors of implementation contracts to prevent uninitialized implementation contracts from being directly initialized by an attacker. Without this safeguard, an attacker can call `initialize()` directly on the implementation contract (not the proxy), setting themselves as the owner or admin, and potentially using the initialized implementation for malicious purposes.

**Impact:**
Unprotected implementation contracts can be directly initialized by attackers, potentially granting them ownership or admin rights over the implementation. While the proxy's state is unaffected, a compromised implementation may be used in delegate-call attacks or reputation damage scenarios.

**Recommended Mitigation:**
Add `_disableInitializers()` to the constructor of all upgradeable implementation contracts, following OpenZeppelin's recommended pattern.

---

**[中文版本]**

**描述：**
YieldFi 中的多个可升级合约在构造函数中没有调用 `_disableInitializers()`。OpenZeppelin 可升级模式建议在实现合约的构造函数中调用 `_disableInitializers()`，以防止攻击者直接初始化未初始化的实现合约。没有此保护，攻击者可直接对实现合约（而非代理）调用 `initialize()`，将自己设置为所有者或管理员。

**影響：**
未受保护的实现合约可被攻击者直接初始化，可能授予其对实现的所有权或管理员权限。虽然代理的状态不受影响，但被攻击的实现可能被用于委托调用攻击。

**修復建議：**
按照 OpenZeppelin 推荐模式，为所有可升级实现合约的构造函数添加 `_disableInitializers()`。

---

## 10. Lack of `_lockTime` validation in constructor

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
The constructor of the vesting contract accepts a `_lockTime` parameter without validating that it is greater than zero. If `_lockTime` is set to zero or an unreasonably small value, the lock period is effectively disabled or trivially bypassable. Unlike setters for this parameter (which typically include validation), the constructor does not enforce a minimum, allowing the vesting contract to be deployed with a misconfigured or ineffective lock duration.

**Impact:**
A vesting contract deployed with `_lockTime = 0` has no effective lock period, allowing immediate withdrawal of vested tokens regardless of the intended vesting schedule. This defeats the purpose of the lock mechanism.

**Recommended Mitigation:**
Add a `require(_lockTime > 0)` check in the constructor to ensure a valid lock duration is set at deployment time.

---

**[中文版本]**

**描述：**
锁仓合约的构造函数在不验证 `_lockTime` 大于零的情况下接受该参数。若 `_lockTime` 设为零或不合理的小值，锁定期实际上被禁用或可被轻易绕过。不同于此参数的 setter 函数（通常包含验证），构造函数不强制执行最小值，允许以错误配置或无效锁定期限部署合约。

**影響：**
以 `_lockTime = 0` 部署的锁仓合约没有有效锁定期，允许立即提取锁仓代币，无论预期锁仓计划如何，完全违背了锁定机制的目的。

**修復建議：**
在构造函数中添加 `require(_lockTime > 0)` 检查，确保在部署时设置有效的锁定期限。

---

## 11. Misleading comments and documentation inconsistencies in on-ramp contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
Multiple on-ramp contracts in the bridge system contain NatSpec comments and inline documentation that do not accurately describe the current behavior of the functions. These inconsistencies include references to deprecated parameters, incorrect descriptions of return values, outdated event descriptions, and comments describing behavior that was changed in a previous refactor but the comments were not updated. Misleading documentation increases the risk of integration errors by external developers and complicates future audits.

**Impact:**
Developers and auditors relying on NatSpec documentation may build incorrect assumptions about function behavior, leading to integration bugs or missing security checks that should be applied based on documented behavior.

**Recommended Mitigation:**
Conduct a systematic review of all NatSpec and inline comments in on-ramp contracts, correcting or removing any that do not accurately reflect current function behavior.

---

**[中文版本]**

**描述：**
桥接系统中的多个 on-ramp 合约包含不能准确描述当前函数行为的 NatSpec 注释和内联文档，包括对已废弃参数的引用、返回值的错误描述、过时的事件描述，以及描述在之前重构中已更改但注释未更新的行为。误导性文档增加了外部开发者集成错误的风险并使未来审计复杂化。

**影響：**
依赖 NatSpec 文档的开发者和审计员可能对函数行为形成错误假设，导致集成错误或遗漏应根据文档行为应用的安全检查。

**修復建議：**
对 on-ramp 合约中的所有 NatSpec 和内联注释进行系统审查，纠正或删除任何不能准确反映当前函数行为的注释。

---

## 12. Outdated reference to rebalance in `IHooklet::afterSwap` should be removed

**Severity:** 🟡 Medium
**Source:** `cyfrin/hooklet.md`

**Description:**
The `IHooklet::afterSwap` interface function contains a comment or parameter that references `rebalance` — a concept or function that has since been removed or renamed in the protocol. This stale reference creates confusion about the current purpose of the `afterSwap` hook and may cause implementors to incorrectly assume that rebalancing logic is expected to be triggered here. Outdated references in interfaces are particularly problematic because they influence how external integrators implement the interface.

**Impact:**
External implementors of `IHooklet` may incorrectly implement `afterSwap` with rebalance logic, creating undefined behavior. The stale reference also complicates maintenance and auditing.

**Recommended Mitigation:**
Remove the outdated `rebalance` reference from `IHooklet::afterSwap` and update the documentation to accurately reflect the current expected behavior of the hook.

---

**[中文版本]**

**描述：**
`IHooklet::afterSwap` 接口函数包含引用 `rebalance` 的注释或参数，而该概念或函数已从协议中删除或重命名。这个过时的引用造成对 `afterSwap` 钩子当前目的的混淆，可能导致实现者错误地假设这里应触发再平衡逻辑。接口中的过时引用尤为有问题，因为它们影响外部集成者实现接口的方式。

**影響：**
`IHooklet` 的外部实现者可能错误地在 `afterSwap` 中实现再平衡逻辑，造成未定义行为。过时引用还会使维护和审计复杂化。

**修復建議：**
从 `IHooklet::afterSwap` 中删除过时的 `rebalance` 引用，并更新文档以准确反映钩子当前预期的行为。

---

## 13. `SablierLidoAdapter::unstakeFullAmount` should return `totalWstETH`

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierLidoAdapter::unstakeFullAmount` is responsible for unstaking all wstETH held by the adapter. However, the function does not return the actual total amount of wstETH that was unstaked. The calling code in the vault relies on the return value of this function to correctly update internal accounting. When the return value is missing or incorrect (e.g., returning 0 or a partial amount), downstream state updates in the vault compute incorrect balances, causing accounting drift between the vault's internal state and the actual wstETH held.

**Impact:**
Incorrect return values from `unstakeFullAmount` cause the vault to record incorrect wstETH balance states, leading to incorrect payout calculations and potential under- or over-payment to users on vault settlement.

**Recommended Mitigation:**
Modify `SablierLidoAdapter::unstakeFullAmount` to return `totalWstETH` — the full amount of wstETH that was unstaked — ensuring the caller can correctly update its internal accounting.

---

**[中文版本]**

**描述：**
`SablierLidoAdapter::unstakeFullAmount` 负责解质押适配器持有的所有 wstETH，但该函数不返回实际解质押的 wstETH 总量。vault 中的调用代码依赖此函数的返回值正确更新内部核算。当返回值缺失或不正确时，vault 中的下游状态更新计算出错误的余额，导致 vault 内部状态与实际持有的 wstETH 之间的核算偏差。

**影響：**
`unstakeFullAmount` 的错误返回值导致 vault 记录错误的 wstETH 余额状态，在 vault 结算时产生错误的赔付计算，可能对用户少付或多付。

**修復建議：**
修改 `SablierLidoAdapter::unstakeFullAmount` 以返回 `totalWstETH`——已解质押的 wstETH 全额——确保调用方可正确更新其内部核算。

---

## 14. Skip call to `CDO::accrueFee` when there are no fees to charge

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
`CDO::accrueFee` is called in multiple flows to update accumulated fee state. However, in scenarios where there are no fees to charge (e.g., fee rate is 0 or the time delta is 0), the function is still invoked unnecessarily, performing state reads and writes with no effective change. This wastes gas and, more importantly, can trigger unnecessary state mutations including timestamp updates that may interfere with time-based fee calculations if called at unintended times.

**Impact:**
Unnecessary calls to `accrueFee` waste gas and may cause subtle accounting issues if the function updates timestamps or fee accumulators even when no fees are owed.

**Recommended Mitigation:**
Add an early return in `CDO::accrueFee` (or in its callers) when there are no fees to accrue, checking that the fee rate is non-zero and that sufficient time has passed before proceeding.

---

**[中文版本]**

**描述：**
`CDO::accrueFee` 在多个流程中被调用以更新累积费用状态。但在没有费用需要收取的情况下（如费率为 0 或时间增量为 0），该函数仍被不必要地调用，执行无实际变更的状态读写。这浪费了 gas，更重要的是可能触发不必要的状态变更，包括时间戳更新，若在意外时间调用可能干扰基于时间的费用计算。

**影響：**
对 `accrueFee` 的不必要调用浪费 gas，若函数在无费用到期时仍更新时间戳或费用累积器，可能导致细微的核算问题。

**修復建議：**
在 `CDO::accrueFee` 中（或在其调用方中）添加提前返回，在继续处理之前检查费率是否非零且已过足够时间。

---

## 15. Upgradeable contracts missing `_disableInitializers()` in constructors

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
Several upgradeable contracts within the bridge system do not call `_disableInitializers()` in their constructors. Per OpenZeppelin's upgradeable contract guidelines, implementation contracts should call `_disableInitializers()` in their constructor to prevent direct initialization of the implementation, which could allow an attacker to take over the implementation contract by calling `initialize()` directly. Without this protection, implementation contracts remain vulnerable to initialization attacks.

**Impact:**
Attackers can directly initialize unprotected implementation contracts, potentially granting themselves ownership or admin rights. Although the proxy's storage is unaffected, a malicious actor controlling the implementation can cause reputational damage or mount sophisticated attacks using delegate calls.

**Recommended Mitigation:**
Add `_disableInitializers()` to the constructor of all upgradeable implementation contracts in the bridge system.

---

**[中文版本]**

**描述：**
桥接系统中的多个可升级合约在构造函数中没有调用 `_disableInitializers()`。根据 OpenZeppelin 可升级合约指南，实现合约应在构造函数中调用 `_disableInitializers()` 防止直接初始化实现，这可能允许攻击者通过直接调用 `initialize()` 接管实现合约。没有此保护，实现合约仍易受初始化攻击。

**影響：**
攻击者可直接初始化未受保护的实现合约，可能授予自己所有权或管理员权限。虽然代理的存储不受影响，但控制实现的恶意行为者可能造成声誉损害或利用委托调用发起复杂攻击。

**修復建議：**
为桥接系统中所有可升级实现合约的构造函数添加 `_disableInitializers()`。

---

## 16. Upgradeable contracts should call `_disableInitializers` in constructor

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
Upgradeable contracts within the rebasing token system do not invoke `_disableInitializers()` in their constructors. This pattern is mandated by OpenZeppelin's upgradeable security guide to prevent malicious actors from calling `initialize()` directly on the implementation contract (as opposed to the proxy). Without `_disableInitializers()`, the implementation remains initializable and can be claimed by an attacker.

**Impact:**
A malicious actor could call `initialize()` on the deployed implementation contract, granting themselves privileged roles. This creates a backdoor that could be exploited to manipulate token or compliance behavior via `delegatecall` vectors.

**Recommended Mitigation:**
Add a constructor to all affected upgradeable implementation contracts that calls `_disableInitializers()`, following OpenZeppelin's recommended pattern for upgradeable contracts.

---

**[中文版本]**

**描述：**
rebasing 代币系统中的可升级合约在构造函数中没有调用 `_disableInitializers()`。这种模式是 OpenZeppelin 可升级安全指南强制要求的，旨在防止恶意行为者直接在实现合约（而非代理）上调用 `initialize()`。没有 `_disableInitializers()`，实现合约仍可被初始化并被攻击者占有。

**影響：**
恶意行为者可在已部署的实现合约上调用 `initialize()`，授予自己特权角色，形成可通过 `delegatecall` 向量被利用的后门。

**修復建議：**
按照 OpenZeppelin 推荐的可升级合约模式，为所有受影响的可升级实现合约添加调用 `_disableInitializers()` 的构造函数。

---

## 17. Variables in non-upgradeable contracts which are only set once in `constructor` should be declared `immutable`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
Several variables in non-upgradeable contracts are assigned exactly once in the `constructor` and never modified afterward. These variables should be declared `immutable`, which encodes their values directly into the contract bytecode. Using `immutable` for such variables eliminates the need for `SLOAD` operations when they are read, reducing gas costs significantly for any code path that accesses them.

**Impact:**
Using storage variables for values that never change after construction results in unnecessarily high gas costs for every read operation. Depending on usage frequency, this can substantially increase the gas cost of common operations.

**Recommended Mitigation:**
Declare all constructor-only-assigned variables as `immutable` in the affected non-upgradeable contracts.

---

**[中文版本]**

**描述：**
非可升级合约中的多个变量在构造函数中只被赋值一次且之后从不修改，这些变量应声明为 `immutable`，将其值直接编码到合约字节码中。对此类变量使用 `immutable` 消除了读取时 `SLOAD` 操作的需要，显著降低访问它们的任何代码路径的 gas 成本。

**影響：**
对构造后从不更改的值使用存储变量导致每次读取操作的 gas 成本不必要地高，根据使用频率，这可能显著增加常见操作的 gas 成本。

**修復建議：**
在受影响的非可升级合约中将所有仅在构造函数中赋值的变量声明为 `immutable`。

---

## 18. Variables only set once in constructor of non-upgradeable contracts should be declared `immutable`

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
In non-upgradeable contracts within the Syntetika protocol, certain state variables are written only during contract construction and are never modified afterward. These variables are currently declared as regular storage variables (`uint256`, `address`, etc.), incurring a cold `SLOAD` gas cost on every read. Since the contracts are not upgradeable, there is no reason to store these values in contract storage — they should be declared `immutable` to be embedded in the contract's bytecode, enabling cheaper reads and preventing any accidental future modifications.

**Impact:**
Every access to these variables costs an unnecessary `SLOAD` (cold: 2,100 gas; warm: 100 gas), increasing the gas cost of every operation that reads them. Marking them `immutable` would reduce read costs to near zero.

**Recommended Mitigation:**
Change the declaration of all variables that are only assigned in the constructor and never modified afterward to `immutable` in non-upgradeable contracts.

---

**[中文版本]**

**描述：**
Syntetika 协议中非可升级合约的某些状态变量仅在合约构建期间被写入且之后从不修改，目前被声明为常规存储变量，每次读取产生冷 `SLOAD` gas 成本。由于合约不可升级，无需将这些值存储在合约存储中——应声明为 `immutable` 以嵌入合约字节码，实现更便宜的读取并防止任何意外的未来修改。

**影響：**
每次访问这些变量产生不必要的 `SLOAD`（冷：2,100 gas；热：100 gas），增加每次读取操作的 gas 成本，将其标记为 `immutable` 可将读取成本降至接近零。

**修復建議：**
在非可升级合约中将所有仅在构造函数中赋值且之后从不修改的变量声明更改为 `immutable`。

---

## 19. `pUSDeVault::startYieldPhase` should not remove supported vaults from being supported or should prevent new supported vaults once in the yield phase

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeVault::startYieldPhase` transitions the vault from the deposit phase to the yield phase. During or after this transition, the function either removes previously supported vaults from the supported list, or it allows new vaults to be added after entering the yield phase — creating two possible protocol inconsistencies. If existing supported vaults are removed upon yield phase start, users whose deposits were directed to those vaults lose their expected yield source. If new vaults can be added during the yield phase, the accounting assumptions made at yield phase start (total deposits, yield distribution, etc.) are violated.

**Impact:**
Either path — removing existing vaults or adding new ones during yield phase — disrupts vault accounting and can cause incorrect yield distribution or user fund misallocation. Users depositing to removed vaults or expecting stable allocations are adversely affected.

**Recommended Mitigation:**
Ensure that `startYieldPhase` does not remove any currently supported vaults from the supported list. Additionally, add a check in the vault registration function to prevent new vaults from being added once the yield phase has started.

---

**[中文版本]**

**描述：**
`pUSDeVault::startYieldPhase` 将 vault 从存款阶段过渡到收益阶段。在此转换期间或之后，函数要么从支持列表中删除之前支持的 vault，要么允许在进入收益阶段后添加新 vault，造成两种可能的协议不一致。若现有支持的 vault 在收益阶段开始时被删除，存款被定向到这些 vault 的用户会失去预期的收益来源；若在收益阶段期间可添加新 vault，则在收益阶段开始时做出的核算假设被违反。

**影響：**
无论哪种情况——在收益阶段删除现有 vault 或添加新 vault——都会破坏 vault 核算，可能导致错误的收益分配或用户资金错误分配，存款到已删除 vault 或期望稳定分配的用户受到不利影响。

**修復建議：**
确保 `startYieldPhase` 不从支持列表中删除任何当前支持的 vault；同时在 vault 注册函数中添加检查，防止在收益阶段开始后添加新 vault。
