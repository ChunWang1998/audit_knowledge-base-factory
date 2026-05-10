# calls-redundant (12)

> Issues where redundant external calls, duplicate logic, or unnecessary operations waste gas or cause unexpected behavior.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. ZkSwap Router Mismatch: Calls Non-Existent exactInputSingle On Monad

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
The `CoreAggregator` adapter targets zkSwap on Monad using a Uniswap V3-style `IZkSwapV3Router` interface and calls `exactInputSingle`. However, zkSwap on Monad exposes a Universal/Smart router, not a standalone V3 SwapRouter. The `exactInputSingle` function does not exist on the deployed zkSwap router, so every swap routed through this adapter reverts at runtime with a call to a non-existent function selector.

**Impact:**
The zkSwap routing path is completely unusable on Monad. Any swap that attempts to use the zkSwap adapter will revert, effectively causing a denial-of-service for that router type. Users cannot execute trades through this path.

**Recommended Mitigation:**
Switch to zkSwap's Universal Router ABI for Monad, encoding the route type (V2/V3/Stable) in `pathData` or via a distinct `RouterType`. Bind router addresses to their expected ABIs in a registry and validate compatibility at registration time to reject mismatches before deployment.

---

**[中文版本]**

**描述：**
`CoreAggregator` 适配器使用 Uniswap V3 风格的 `IZkSwapV3Router` 接口并调用 `exactInputSingle`，但 Monad 上的 zkSwap 部署的是 Universal/Smart 路由器而非独立的 V3 SwapRouter，不存在 `exactInputSingle` 函数，导致所有 zkSwap 路由在运行时回滚。

**影響：**
zkSwap 路由路径在 Monad 上完全不可用，所有通过该适配器的交换均会回滚，造成该路由类型的拒绝服务。

**修復建議：**
改用 zkSwap 的 Universal Router ABI，在 `pathData` 或专用 `RouterType` 中编码路由类型；在注册中心将路由器地址与期望的 ABI 绑定并在注册时验证兼容性。

---

## 2. BasisTradeTailor::coreDepositWallet is not blocked for adapters calls

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`BasisTradeTailor::executeAdapter` blocks adapters from calling `coreWriter` with an explicit `require(target != coreWriter, "Adapter cannot call coreWriter")` check, presumably as a defence-in-depth measure against adapters interacting with sensitive Core contracts. However, no equivalent restriction is applied to `coreDepositWallet`, even though `CoreDepositWallet::depositFor` can send pocket USDC to arbitrary Core addresses. The inconsistency means the defence-in-depth rationale for blocking `coreWriter` is not consistently applied.

**Impact:**
Adapters can call `coreDepositWallet` to deposit pocket USDC to Core addresses in ways that were presumably not intended, creating a potential attack vector or unexpected state changes. While adapters are trusted, the missing restriction creates an inconsistent security boundary.

**Recommended Mitigation:**
Add `coreDepositWallet` to the blocked target list in `executeAdapter`, alongside `coreWriter`, so that both Core-interacting contracts are consistently restricted from adapter calls.

---

**[中文版本]**

**描述：**
`BasisTradeTailor::executeAdapter` 阻止适配器调用 `coreWriter` 以实现纵深防御，但未对 `coreDepositWallet` 施加同等限制，尽管 `CoreDepositWallet::depositFor` 同样可与 Core 合约交互，将 pocket USDC 发送至任意 Core 地址。

**影響：**
适配器可调用 `coreDepositWallet` 以非预期方式操作 Core 合约，安全边界不一致，存在潜在风险。

**修復建議：**
在 `executeAdapter` 的受限目标列表中增加 `coreDepositWallet`，与 `coreWriter` 保持一致的限制。

---

## 3. Cache result of external calls when result can't change between calls and is used multiple times

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
In `Tranche::configure()`, `cdo.strategy()` is called twice in consecutive lines: once to retrieve `getSupportedTokens()` and once to obtain the `address` of the strategy. Both calls access the same immutable external contract reference, producing identical return values. Each external call incurs gas overhead, and both could be replaced with a single call whose result is cached in a local variable.

**Impact:**
Unnecessary double external call on every `configure()` invocation, wasting gas proportional to the cost of the external call (warm CALL opcode plus the called function's execution cost).

**Recommended Mitigation:**
Cache the result of the first `cdo.strategy()` call into a local variable (e.g., `address strategy = address(cdo.strategy())`), then use that cached address to call `IStrategy(strategy).getSupportedTokens()`, eliminating the redundant second external call.

---

**[中文版本]**

**描述：**
`Tranche::configure()` 中 `cdo.strategy()` 被连续调用两次：一次获取支持的代币列表，一次获取策略地址。两次调用返回相同结果但各自产生 gas 开销。

**影響：**
每次 `configure()` 调用产生不必要的双重外部调用，浪费 gas。

**修復建議：**
将第一次 `cdo.strategy()` 的结果缓存到局部变量，然后用该缓存地址调用 `getSupportedTokens()`，消除冗余的第二次外部调用。

---

## 4. Cooldown Timer Reset on Repeated Calls Leads to Extended Staking on Previously Queued Assets

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
The cooldown functions in `StakedOverlayerWrap` store a per-user struct containing a `cooldownEnd` timestamp and an `underlyingAmount`. On each invocation the timestamp is overwritten with a fresh countdown (`block.timestamp + cooldownDuration`) while the asset amount is incremented. A user who queues assets for cooldown twice — for example 100 tokens initially and 50 more tokens 30 days later — will have their entire 100-token cooldown reset to a new full 90-day period from the second call, losing the 30 days already accrued. There is no cancel function and no partial claim, so the first batch of tokens must wait a second full cooldown period. Assets sit in the yield-bearing-free `Silo` contract during the entire cooldown window.

**Impact:**
Users who add to their cooldown queue lose previously elapsed cooldown time on all earlier-queued assets. Assets earn no yield in the Silo, so each reset represents direct economic loss proportional to the cooldown duration (up to 90 days of foregone staking rewards).

**Recommended Mitigation:**
Reject cooldown calls when an active cooldown already exists (short-term), or implement per-cooldown tracking using distinct cooldown IDs so each batch has an independent timer, or add a `cancelCooldown()` function to allow users to recover assets and restart.

---

**[中文版本]**

**描述：**
`StakedOverlayerWrap` 的冷却函数在每次调用时覆盖 `cooldownEnd` 时间戳（重置为新的完整冷却期），同时累加资产。第二次冷却请求会使第一批代币的已计时间归零，且无取消功能或部分提取机制，资产在无收益的 Silo 中等待整个冷却期。

**影響：**
重复排队的用户丢失已累积的冷却时间，无法获得最多90天的质押收益，造成直接经济损失。

**修復建議：**
短期：当用户已有活跃冷却时拒绝新冷却请求。中期：为每个冷却批次分配独立ID和计时器。或添加 `cancelCooldown()` 函数允许用户取回资产重新开始。

---

## 5. Frequent AccountableOpenTerm::accrueInterest calls reduce interest accrual

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableOpenTerm::_linearInterest` computes `rate * timeDelta / DAYS_360_SECONDS` using integer division. For small `timeDelta` values the result rounds to zero, but `accrueInterest()` still updates `_accruedAt = block.timestamp` even when the computed increment is zero. Any actor — without privileged access — can call `accrueInterest()` at short intervals (e.g., every few minutes for a 15% APY loan) to keep `timeDelta` below the rounding threshold, causing each call to consume elapsed time without accruing any interest. Over the same wall-clock period, a single accrual call would have produced a materially higher `_scaleFactor`.

**Impact:**
Repeated calls at short intervals suppress interest growth, underpaying LPs (lower share price and fewer assets owed by the borrower) and reducing protocol fee bases. The effect compounds over time and requires no privileged access to exploit.

**Recommended Mitigation:**
Increase the internal precision of `_linearInterest` by scaling the computation with a higher-precision factor (e.g., 1e18 or 1e36) to ensure small time intervals still accumulate fractional interest before being committed to `_accruedAt`.

---

**[中文版本]**

**描述：**
`_linearInterest` 使用整数除法，小 `timeDelta` 时结果舍入为零，但 `accrueInterest()` 仍会更新 `_accruedAt`。任何人可频繁调用 `accrueInterest()` 消耗时间而不产生利息增量，导致实际利率累积远低于单次完整调用的结果。

**影響：**
无需特权即可压制利息增长，LP 获得更低的份额价格和更少的应收资产，协议手续费基数也受到影响。

**修復建議：**
在 `_linearInterest` 中增加精度因子（如乘以1e18或1e36），确保小时间间隔仍能累积分数利息。

---

## 6. Impossible to remove a document added with zero uri length

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DocumentManager::_setDocument` accepts documents with an empty `uri` string and stores them normally. However, `_removeDocument` checks for `EmptyDocument()` — presumably triggered when the document lookup finds an empty-URI entry — and reverts. As a result, any document added with a zero-length `uri` can never be removed, permanently persisting in the document storage even if the intent was to overwrite or clean it up.

**Impact:**
Documents with empty URIs permanently accumulate in storage and cannot be removed, creating unbounded state growth and leaving stale entries that may confuse off-chain indexers or document management logic.

**Recommended Mitigation:**
Prevent adding documents with empty URIs by adding a `require(bytes(uri).length > 0)` check in `_setDocument`, ensuring the inability to remove condition can never be reached.

---

**[中文版本]**

**描述：**
`_setDocument` 接受空 `uri` 字符串的文档并正常存储，但 `_removeDocument` 对空 URI 文档会触发 `EmptyDocument()` 错误回滚，导致空 URI 文档永远无法被移除。

**影響：**
空 URI 文档在存储中永久累积，无法清理，可能扰乱链下索引或文档管理逻辑，造成无界状态增长。

**修復建議：**
在 `_setDocument` 中增加 `require(bytes(uri).length > 0)` 检查，从源头防止添加无法删除的文档。

---

## 7. MyriadCTFExchange::_requireMarketOpen makes two external calls to manager

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`MyriadCTFExchange::_requireMarketOpen` issues two separate external calls to the `manager` contract on every invocation: one to `getMarketState(marketId)` and one to `isMarketPaused(marketId)`. This function is called once per order in `matchCrossMarketOrders` (N times for an N-outcome event) and once per `_matchOrders` call in the single-market path, making the combined overhead cumulative. Each external call costs a minimum of 100 gas (warm) or 2100 gas (cold) for the `CALL` opcode alone.

**Impact:**
Unnecessary double external call on every market validation increases gas costs for all order matching operations. The overhead scales with the number of outcomes in cross-market order scenarios.

**Recommended Mitigation:**
Add a combined `isMarketTradeable(uint256 marketId)` view function to `IMyriadMarketManager` and its implementation that atomically checks both state and pause status. Simplify `_requireMarketOpen` to a single external call to this combined function.

---

**[中文版本]**

**描述：**
`_requireMarketOpen` 每次调用都对 `manager` 合约发出两个独立的外部调用（`getMarketState` 和 `isMarketPaused`），在批量订单匹配中此开销会成倍累积。

**影響：**
每次市场验证产生不必要的双重外部调用，增加所有订单匹配操作的 gas 成本，在多结果跨市场场景中尤为明显。

**修復建議：**
在 `IMyriadMarketManager` 中增加合并视图函数 `isMarketTradeable(uint256 marketId)` 同时检查状态和暂停标志，将 `_requireMarketOpen` 简化为单次外部调用。

---

## 8. Optimize _getStakerVaults to Avoid Redundant External Calls to activeBalanceOfAt

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`Rewards::_getStakerVaults` uses a two-pass approach to build the list of vaults with non-zero staker balances. The first pass counts qualifying vaults and the second pass populates the result array. Both passes call `IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0))` for each vault, doubling the number of external calls. Since the return value cannot change between the two passes within the same call, the second pass is entirely redundant.

**Impact:**
Every call to `_getStakerVaults` (triggered on each `claimRewards` invocation) doubles the external call overhead for vault balance queries. For `N` vaults the cost is 2N external calls instead of N.

**Recommended Mitigation:**
Replace the two-pass approach with a single-pass that uses a temporary oversized array to accumulate qualifying vault addresses, then creates a correctly-sized result array by copying the populated entries. This reduces external calls from 2N to N.

---

**[中文版本]**

**描述：**
`Rewards::_getStakerVaults` 使用两遍遍历：第一遍统计合格 vault 数量，第二遍填充结果数组，两遍都对每个 vault 调用 `activeBalanceOfAt`，将外部调用数量翻倍。两遍之间返回值不会改变，第二遍完全冗余。

**影響：**
每次 `claimRewards` 调用的 vault 余额查询外部调用数量翻倍，N个 vault 产生2N次外部调用而非N次。

**修復建議：**
改用单遍遍历，使用临时超大数组收集合格 vault 地址，最后截取有效部分，将外部调用从2N降至N。

---

## 9. Redundant FUNDER_ROLE in LineaRollupYieldExtension

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`LineaRollupYieldExtension` defines a `FUNDER_ROLE` constant with a comment indicating it controls access to the `fund()` function. However, `fund()` is intentionally permissionless — it accepts both permissionless donations and YieldManager withdrawals — and has no `onlyRole(FUNDER_ROLE)` modifier. The defined role constant is never used anywhere in the contract, creating a misleading documentation artefact.

**Impact:**
While not a security vulnerability, the unused `FUNDER_ROLE` constant creates confusion: developers and auditors may assume access control is enforced on `fund()` when it is not. Future maintainers might grant or revoke the role expecting it to have an effect, or might incorrectly add the modifier thinking they are fulfilling the documented intent.

**Recommended Mitigation:**
Remove the unused `FUNDER_ROLE` constant and its associated comment to eliminate the inconsistency between documentation and implementation. If access control on `fund()` is desired, add the `onlyRole(FUNDER_ROLE)` modifier and update the associated documentation accordingly.

---

**[中文版本]**

**描述：**
`LineaRollupYieldExtension` 定义了 `FUNDER_ROLE` 常量并注释其控制 `fund()` 的访问，但 `fund()` 函数故意设计为无访问控制（接受无许可捐款），没有 `onlyRole(FUNDER_ROLE)` 修饰器，该角色常量从未被使用。

**影響：**
未使用的角色常量造成混淆，使开发者和审计方误以为 `fund()` 有访问控制，可能导致未来维护中的错误操作。

**修復建議：**
移除未使用的 `FUNDER_ROLE` 常量及相关注释；若需要对 `fund()` 实施访问控制，则添加 `onlyRole(FUNDER_ROLE)` 修饰器并更新文档。

---

## 10. Redundant approve(0) in BasisTradeVault::depositToTailor

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeVault::depositToTailor` approves `tailor` for exactly `amount`, calls `tailor.deposit(pocket, amount)`, and then calls `IERC20(asset()).forceApprove(address(tailor), 0)`. Because `BasisTradeTailor::deposit` pulls exactly `amount` via `safeTransferFrom`, the allowance is already consumed to zero after the deposit call. The trailing `forceApprove(..., 0)` therefore performs an unnecessary storage write and external call on an already-zero allowance.

**Impact:**
Minor gas waste on every `depositToTailor` call from an unnecessary storage write (`SSTORE` to a slot already at zero) and an extra external call.

**Recommended Mitigation:**
Remove the trailing `IERC20(asset()).forceApprove(address(tailor), 0)` call from `BasisTradeVault::depositToTailor`, as the allowance is guaranteed to be zero after `tailor.deposit` completes.

---

**[中文版本]**

**描述：**
`depositToTailor` 在授权后调用 `tailor.deposit` 再调用 `forceApprove(..., 0)`。由于 `deposit` 通过 `safeTransferFrom` 精确消耗了全部授权额度，调用后授权已为零，尾部的 `forceApprove(..., 0)` 对已为零的存储槽做了不必要的写操作。

**影響：**
每次 `depositToTailor` 调用产生不必要的 `SSTORE` 和额外外部调用，浪费 gas。

**修復建議：**
从 `depositToTailor` 中移除尾部的 `forceApprove(address(tailor), 0)` 调用。

---

## 11. Redundant variable statements

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
In `BasisTradeVault`, several functions override ERC4626 standard interface functions (`maxMint`, `mint`, `withdraw`, `redeem`) to intentionally disable them. Because the functions immediately revert or return fixed values, their parameters are unused. The code silences the compiler warnings about unused parameters by placing each parameter name on its own line as a bare statement (e.g., `receiver;`). While this compiles without warnings, it is not idiomatic Solidity and clutters the code unnecessarily.

**Impact:**
No security or gas impact. The redundant bare statements add noise to the code and are less clear than the conventional approach of using unnamed parameters in the function signature.

**Recommended Mitigation:**
Replace the bare parameter statements with unnamed parameters in the function signature (e.g., `function mint(uint256 /*shares*/, address /*receiver*/)`) to signal intentionally unused parameters in a conventional, cleaner way.

---

**[中文版本]**

**描述：**
`BasisTradeVault` 中重写的多个 ERC4626 函数用裸语句（如 `receiver;`）来消除未使用参数的编译器警告，而非使用 Solidity 惯例的无名参数写法，代码不够简洁。

**影響：**
无安全或 gas 影响，仅增加代码噪音，可读性低于惯例写法。

**修復建議：**
将裸参数语句替换为函数签名中的无名参数写法（如 `function mint(uint256 /*shares*/, address /*receiver*/)`），以惯用方式标示有意未使用的参数。

---

## 12. Remove redundant calls to EnumerableSet::contains

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`BlackListManager::_addToBlacklist` and `_removeFromBlacklist` each call `EnumerableSet::contains` to check membership before calling `_add` or `_remove`. However, OpenZeppelin's `EnumerableSet::_add` and `_remove` internally perform an equivalent membership check themselves. The explicit prior call to `contains` is therefore redundant, performing the same lookup twice for every add or remove operation.

**Impact:**
Minor gas waste on every blacklist add and remove operation due to a redundant storage lookup (the `contains` check reads the same storage slot that `_add`/`_remove` will read internally).

**Recommended Mitigation:**
Remove the explicit `EnumerableSet::contains` calls and instead call `EnumerableSet::add` or `remove` directly, reverting if they return `false` to maintain the same error-handling behaviour.

---

**[中文版本]**

**描述：**
`BlackListManager::_addToBlacklist` 和 `_removeFromBlacklist` 在调用 `EnumerableSet::_add`/`_remove` 前各自先调用 `contains` 检查成员资格，而 OpenZeppelin 的 `_add`/`_remove` 内部已执行相同检查，导致每次操作进行两次相同的存储查询。

**影響：**
每次黑名单增删操作因冗余的存储查询浪费 gas。

**修復建議：**
移除显式的 `contains` 调用，直接调用 `EnumerableSet::add` 或 `remove`，若返回 `false` 则回滚以保持相同的错误处理行为。
