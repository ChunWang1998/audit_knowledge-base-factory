# variables-return (7)

> Issues where named return variables were underutilized or local variables could be eliminated for clarity and gas savings.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Refactor LidoStVaultYieldProvider::_syncExternalLiabilitySettlement to eliminate liabilityETH

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` already declares a named return variable `lstLiabilityPrincipalSynced`. The function body could be written entirely in terms of this named return variable, eliminating the need for a separate intermediate local variable `liabilityETH`. Currently the logic assigns to `lstLiabilityPrincipalSynced` in the initial call but then introduces `liabilityETH` as a redundant alias, increasing stack depth and obscuring the control flow without adding clarity.

**Impact:**
The redundant local variable adds unnecessary bytecode and stack usage per call, and increases cognitive overhead for developers reading or maintaining the function. While the impact is minor, clean elimination of avoidable local variables improves contract readability and slightly reduces gas costs.

**Recommended Mitigation:**
Rewrite `_syncExternalLiabilitySettlement` to use only the named return variable `lstLiabilityPrincipalSynced` throughout, eliminating the intermediate `liabilityETH` local variable entirely.

---

**[中文版本]**

**描述：**
`LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` 已声明了命名返回变量 `lstLiabilityPrincipalSynced`。函数体可以完全用这个命名返回变量编写，无需单独的中间局部变量 `liabilityETH`。目前逻辑在初始调用中赋值给 `lstLiabilityPrincipalSynced`，但随后引入 `liabilityETH` 作为冗余别名，增加了栈深度并混淆了控制流，没有增加任何清晰度。

**影響：**
冗余局部变量在每次调用时增加了不必要的字节码和栈使用，并增加了阅读或维护函数的开发者的认知负担。虽然影响较小，但干净地消除可避免的局部变量可以提高合约可读性并略微降低 gas 成本。

**修復建議：**
重写 `_syncExternalLiabilitySettlement` 以在整个函数中只使用命名返回变量 `lstLiabilityPrincipalSynced`，完全消除中间局部变量 `liabilityETH`。

---

## 2. SDLVesting::stakeReleasableTokens gas optimization by caching variables

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
`SDLVesting::stakeReleasableTokens` reads `lockTime` from storage multiple times and reads `reSDLTokenIds[lockTime]` from storage multiple times. Specifically, `lockTime` is used as a mapping key to access `reSDLTokenIds[lockTime]` twice, and `lockTime` itself is read in the `abi.encode` call. Since neither `lockTime` nor `reSDLTokenIds[lockTime]` changes during the function execution, both should be cached in local variables to avoid redundant storage reads.

**Impact:**
Every call to `stakeReleasableTokens` pays for several unnecessary storage reads. In a staking system with frequent token staking operations, the cumulative gas waste across many calls is significant.

**Recommended Mitigation:**
Cache `lockTime` into a local `uint256 _lockTime` variable and cache `reSDLTokenIds[lockTime]` into a local `uint256 _tokenId` variable at the start of the function, then use the cached values throughout.

---

**[中文版本]**

**描述：**
`SDLVesting::stakeReleasableTokens` 多次从存储读取 `lockTime`，并多次从存储读取 `reSDLTokenIds[lockTime]`。具体地，`lockTime` 被用作映射键两次访问 `reSDLTokenIds[lockTime]`，`lockTime` 本身也在 `abi.encode` 调用中被读取。由于 `lockTime` 和 `reSDLTokenIds[lockTime]` 在函数执行期间都不会改变，两者都应缓存在局部变量中以避免冗余的存储读取。

**影響：**
每次调用 `stakeReleasableTokens` 都为多次不必要的存储读取付费。在频繁进行代币质押操作的质押系统中，许多次调用累积的 gas 浪费是可观的。

**修復建議：**
在函数开始时将 `lockTime` 缓存到局部 `uint256 _lockTime` 变量中，将 `reSDLTokenIds[lockTime]` 缓存到局部 `uint256 _tokenId` 变量中，然后在整个函数中使用缓存值。

---

## 3. TickIterator::_advanceToNextUp sets uninitialized end tick as the current tick which causes TickIterator::hasNext to return true when this is not actually the case

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`TickIterator::_advanceToNextUp` uses a do-while loop to advance the iterator to the next initialized tick. The loop's exit condition terminates once `self.currentTick >= self.endTick`. However, when no initialized tick exists between the current tick and the end tick, the loop sets `self.currentTick` to the end tick even if that end tick is not initialized. `TickIterator::hasNext` checks `self.currentTick <= self.endTick`, which evaluates to true when `currentTick == endTick`, incorrectly indicating there is a next tick. Calling `getNext` in this state returns the uninitialized end tick rather than reverting with `NoNext`.

**Impact:**
Downstream code that relies on `hasNext` to determine whether to call `getNext` will process an uninitialized phantom tick at the word boundary. While current evaluations appear to produce zero-value results for the phantom tick (acting as a no-op), this is not guaranteed and could produce incorrect pricing or reward calculations in edge cases.

**Recommended Mitigation:**
When `_advanceToNextUp` exhausts all initialized ticks before reaching the end tick, mark the iterator as exhausted by setting `self.currentTick = type(int24).max`. Update `hasNext` to use a strict less-than comparison (`self.currentTick < self.endTick`) so that a non-initialized boundary is not considered a valid next tick.

---

**[中文版本]**

**描述：**
`TickIterator::_advanceToNextUp` 使用 do-while 循环将迭代器推进到下一个已初始化的刻度。循环的退出条件在 `self.currentTick >= self.endTick` 时终止。然而，当当前刻度和结束刻度之间不存在已初始化的刻度时，循环将 `self.currentTick` 设置为结束刻度，即使该结束刻度未被初始化。`TickIterator::hasNext` 检查 `self.currentTick <= self.endTick`，当 `currentTick == endTick` 时评估为 true，错误地指示存在下一个刻度。在此状态下调用 `getNext` 会返回未初始化的结束刻度而非以 `NoNext` 回滚。

**影響：**
依赖 `hasNext` 来确定是否调用 `getNext` 的下游代码将在字边界处理未初始化的幻影刻度。虽然当前评估似乎为幻影刻度产生零值结果（作为无操作），但这不能保证，在边缘情况下可能产生不正确的定价或奖励计算。

**修復建議：**
当 `_advanceToNextUp` 在到达结束刻度之前耗尽所有已初始化的刻度时，通过将 `self.currentTick = type(int24).max` 将迭代器标记为已耗尽。将 `hasNext` 更新为使用严格的小于比较（`self.currentTick < self.endTick`），使未初始化的边界不被视为有效的下一个刻度。

---

## 4. Use named return variables when this eliminates local variables — cyfrin/syntetika.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
In `CompliantDepositRegistry::getDepositAddresses` and `StakingVault::redeem`, local return variables are declared and populated but could be replaced with named return variables. Using named return variables in these functions would eliminate the need for the separate local variable declarations, reducing stack depth and slightly improving gas efficiency, particularly for memory-type returns where the named return avoids an extra allocation.

**Impact:**
Unnecessary local variable declarations add minor stack and gas overhead. For memory return types, eliminating the intermediate local variable in favor of a named return is measurably more gas-efficient, especially for functions that return arrays or structs.

**Recommended Mitigation:**
Convert `CompliantDepositRegistry::getDepositAddresses` and `StakingVault::redeem` to use named return variables, removing the intermediate local declarations that the named returns would replace.

---

**[中文版本]**

**描述：**
在 `CompliantDepositRegistry::getDepositAddresses` 和 `StakingVault::redeem` 中，局部返回变量被声明并填充，但可以用命名返回变量替换。在这些函数中使用命名返回变量将消除对单独局部变量声明的需求，减少栈深度并略微提高 gas 效率，特别是对于内存类型返回，命名返回可以避免额外的分配。

**影響：**
不必要的局部变量声明增加了少量栈和 gas 开销。对于内存返回类型，将中间局部变量改为命名返回在 gas 效率上是可测量的提升，尤其是对于返回数组或结构体的函数。

**修復建議：**
将 `CompliantDepositRegistry::getDepositAddresses` 和 `StakingVault::redeem` 转换为使用命名返回变量，移除命名返回将替换的中间局部声明。

---

## 5. Use named return variables where this can eliminate local variables — cyfrin/wannabetv2.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`BetFactory::createBet` and `Bet::_status` both declare local variables that are assigned once and then immediately returned. In both cases, replacing the local variable with a named return variable would eliminate the intermediate declaration entirely, reduce stack usage, and produce slightly more gas-efficient bytecode — especially for `_status` which is a view function called frequently.

**Impact:**
Unnecessary local variable declarations in frequently called functions accumulate gas overhead over many transactions. The impact is minor per call but measurable at scale for a protocol with active bet creation and status queries.

**Recommended Mitigation:**
Convert `BetFactory::createBet` and `Bet::_status` to use named return variables instead of intermediate local variables, allowing the compiler to optimize away the extra local slot.

---

**[中文版本]**

**描述：**
`BetFactory::createBet` 和 `Bet::_status` 都声明了被赋值一次然后立即返回的局部变量。在两种情况下，用命名返回变量替换局部变量将完全消除中间声明，减少栈使用，并产生略微更高效的字节码——尤其是对于频繁调用的视图函数 `_status`。

**影響：**
在频繁调用的函数中不必要的局部变量声明在许多交易中累积了 gas 开销。每次调用的影响较小，但对于有大量投注创建和状态查询活动的协议，规模化后是可测量的。

**修復建議：**
将 `BetFactory::createBet` 和 `Bet::_status` 转换为使用命名返回变量而非中间局部变量，允许编译器优化掉额外的局部槽。

---

## 6. Use named return variables where this can optimize away local variables — cyfrin/escrow.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierBob::_safeTokenSymbol` declares and assigns a local return variable that could be replaced with a named return variable. For memory return types like `string`, using a named return variable allows the compiler to treat the allocation as the return slot directly, potentially saving a memory allocation step compared to declaring a separate local variable and then returning it.

**Impact:**
The minor gas overhead per call accumulates across the many calls to `_safeTokenSymbol` in a protocol handling multiple vault types with different tokens. While the savings per call are small, adopting the pattern consistently improves overall code quality.

**Recommended Mitigation:**
Convert `SablierBob::_safeTokenSymbol` to use a named return variable `(string memory symbol)`, eliminating the intermediate local variable and enabling compiler optimization of the return memory allocation.

---

**[中文版本]**

**描述：**
`SablierBob::_safeTokenSymbol` 声明并赋值了一个可以用命名返回变量替换的局部返回变量。对于像 `string` 这样的内存返回类型，使用命名返回变量允许编译器将分配直接视为返回槽，与声明单独局部变量然后返回相比，可能节省一个内存分配步骤。

**影響：**
每次调用的少量 gas 开销在处理多种不同代币金库类型的协议中 `_safeTokenSymbol` 的许多次调用中累积。虽然每次调用的节省很小，但一致地采用此模式可提高整体代码质量。

**修復建議：**
将 `SablierBob::_safeTokenSymbol` 转换为使用命名返回变量 `(string memory symbol)`，消除中间局部变量并启用编译器对返回内存分配的优化。

---

## 7. Use named returns where this eliminates a local variable and especially for memory returns — cyfrin/pledge.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`TokenBank::viewAllFees` declares a local variable that is populated and then returned at the end of the function. Using a named return variable instead would eliminate the intermediate local declaration. The benefit is especially significant for `memory` return types (arrays, structs, strings) because named returns allow the compiler to use the return memory slot directly, avoiding the overhead of declaring, populating, and then returning a separately allocated local variable.

**Impact:**
The extra local variable in `viewAllFees` results in slightly higher gas costs per call, particularly because the return type involves memory allocation. For a view function that may be called frequently by front-ends and integrators, the savings from adopting named returns are meaningful.

**Recommended Mitigation:**
Refactor `TokenBank::viewAllFees` to declare the return value as a named return variable, allowing the compiler to eliminate the separate local declaration and optimize the memory allocation for the return value.

---

**[中文版本]**

**描述：**
`TokenBank::viewAllFees` 声明了一个局部变量，该变量被填充后在函数末尾返回。使用命名返回变量代替将消除中间局部声明。对于 `memory` 返回类型（数组、结构体、字符串），好处尤为显著，因为命名返回允许编译器直接使用返回内存槽，避免了声明、填充然后返回单独分配的局部变量的开销。

**影響：**
`viewAllFees` 中的额外局部变量导致每次调用的 gas 成本略高，特别是因为返回类型涉及内存分配。对于可能被前端和集成商频繁调用的视图函数，采用命名返回所节省的成本是有意义的。

**修復建議：**
重构 `TokenBank::viewAllFees`，将返回值声明为命名返回变量，允许编译器消除单独的局部声明并优化返回值的内存分配。
