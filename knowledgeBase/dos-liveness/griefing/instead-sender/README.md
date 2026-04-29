# instead-sender (16)

> Issues where msg.sender was used incorrectly instead of a delegated caller, or where gas/storage optimizations were missing.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Consider emitting events early to save gas

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
Several setter functions in `DVNPublisherFactory`, `DVNPublisher`, and `AccountableYield` store the old value in a memory variable solely to emit it in an event, then update the storage variable. By emitting the event before the state change, the memory variable can be eliminated: the event can be emitted with the current storage value (the old value) and the parameter (the new value), and the storage update follows immediately.

**Impact:**
No security risk. The pattern wastes a small amount of gas on every invocation of these setter functions due to the unnecessary memory allocation.

**Recommended Mitigation:**
Restructure each affected setter to emit the event first (using the current storage value as the old value and the parameter as the new value), then update the storage variable.

---

**[中文版本]**

**描述：**
`DVNPublisherFactory`、`DVNPublisher` 和 `AccountableYield` 中的多个设置函数将旧值存入内存变量仅为在事件中发出，然后更新存储变量。通过先于状态更改发出事件，可消除内存变量：使用当前存储值（旧值）和参数（新值）发出事件，随后立即更新存储。

**影響：**
无安全风险，但每次调用这些设置函数时，不必要的内存分配会浪费少量燃气。

**修復建議：**
重构每个受影响的设置函数，先发出事件（以当前存储值为旧值，参数为新值），再更新存储变量。

---

## 2. Gas optimization for getVaults function

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
The `getVaults` function iterates over an unbounded list and performs repeated storage reads. The function can be optimized by caching the array length before the loop and reading storage variables into memory rather than accessing them on every iteration.

**Impact:**
No security risk. Callers pay excess gas when retrieving vault lists, which increases operational costs.

**Recommended Mitigation:**
Cache `array.length` in a local variable before the loop and load frequently accessed storage values into memory at the start of each iteration.

---

**[中文版本]**

**描述：**
`getVaults` 函数遍历无界列表并重复读取存储变量。通过在循环前缓存数组长度，并将频繁访问的存储变量读入内存，可优化该函数。

**影響：**
无安全风险，但调用者在获取 vault 列表时支付多余燃气，增加运营成本。

**修復建議：**
在循环前将 `array.length` 缓存到局部变量，并在每次迭代开始时将频繁访问的存储值加载到内存中。

---

## 3. Meta transactions will not work due to direct msg.sender usage in validateLockedTokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/dstokenswap.md`

**Description:**
The `validateLockedTokens` function passes `msg.sender` directly to `complianceService.getComplianceTransferableTokens`. In a meta-transaction context, `msg.sender` is the relayer's address, not the actual token holder. The protocol uses `_msgSender()` correctly elsewhere, but this specific path bypasses the ERC-2771 context, causing compliance checks to evaluate the relayer's balance and investor record instead of the actual holder's, resulting in incorrect validation.

**Impact:**
Meta transactions cannot be used for token transfers. Users cannot have gas-free transactions relayed on their behalf because the compliance check always evaluates the relayer rather than the real investor, causing transfers to revert or apply incorrect lock period validations.

**Recommended Mitigation:**
Replace `msg.sender` with `_msgSender()` in `validateLockedTokens` to correctly identify the actual token holder in both direct and meta-transaction contexts.

---

**[中文版本]**

**描述：**
`validateLockedTokens` 函数将 `msg.sender` 直接传递给 `complianceService.getComplianceTransferableTokens`。在元交易上下文中，`msg.sender` 是中继者地址而非实际代币持有人。协议在其他地方正确使用 `_msgSender()`，但此特定路径绕过了 ERC-2771 上下文，导致合规检查评估中继者而非实际持有人的余额和投资者记录，引发错误验证。

**影響：**
元交易无法用于代币转账，用户无法通过中继者进行免燃气交易，因为合规检查始终评估中继者而非真正的投资者，导致转账回滚或应用错误的锁定期验证。

**修復建議：**
将 `validateLockedTokens` 中的 `msg.sender` 替换为 `_msgSender()`，以在直接调用和元交易上下文中正确识别实际代币持有人。

---

## 4. Reuse fm Instead of re-instantiating IFeeManager in AccountableOpenTerm::_mintFeeShares

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
In `AccountableOpenTerm::_mintFeeShares`, the treasury address is obtained by re-casting `feeManager` to `IFeeManager` via `IFeeManager(feeManager).treasury()`. However, an `IFeeManager fm` interface instance is already passed as a parameter into the function. The re-instantiation is redundant and wastes gas on an unnecessary interface cast and storage load.

**Impact:**
No security risk. Minor gas inefficiency on each fee share minting call.

**Recommended Mitigation:**
Replace `IFeeManager(feeManager).treasury()` with `fm.treasury()` to reuse the already-available interface instance.

---

**[中文版本]**

**描述：**
在 `AccountableOpenTerm::_mintFeeShares` 中，通过 `IFeeManager(feeManager).treasury()` 重新将 `feeManager` 转换为 `IFeeManager` 来获取金库地址。然而，`IFeeManager fm` 接口实例已作为参数传入该函数，重新实例化是多余的，浪费了不必要的接口转换和存储加载的燃气。

**影響：**
无安全风险，每次铸造手续费份额时存在轻微燃气低效。

**修復建議：**
将 `IFeeManager(feeManager).treasury()` 替换为 `fm.treasury()`，以复用已有的接口实例。

---

## 5. Subscription Renewal Resets Timer Instead of Extending Causing User Fund Loss

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
`F-2025-14457` — `Subscription::renewSubscription()` and `subscribeToLevel()` reset the subscription expiry to `block.timestamp + duration` rather than extending from the existing expiry time. A user who renews before their current subscription expires loses the remaining paid time. For example, if a user pays for a 30-day subscription and renews on Day 5, the subscription is reset to Day 35 instead of being extended to Day 60, causing the user to lose 25 days of paid subscription time.

**Impact:**
Users who renew their subscriptions before expiry lose the remaining paid-for time, resulting in a direct financial loss proportional to the time remaining in their current subscription period.

**Recommended Mitigation:**
When renewing, use `max(currentExpiry, block.timestamp) + duration` as the new expiry time, so renewals always extend from the later of the current expiry or the current timestamp.

---

**[中文版本]**

**描述：**
`F-2025-14457` — `Subscription::renewSubscription()` 和 `subscribeToLevel()` 将订阅到期时间重置为 `block.timestamp + duration`，而非从现有到期时间延伸。在订阅未到期时续费的用户将损失剩余已付费时间。例如，用户购买 30 天订阅后在第 5 天续费，订阅被重置为第 35 天而非延伸至第 60 天，用户损失 25 天已付费订阅时间。

**影響：**
在到期前续费的用户将损失剩余已付费时间，造成与当前订阅周期剩余时间成比例的直接经济损失。

**修復建議：**
续费时使用 `max(currentExpiry, block.timestamp) + duration` 作为新到期时间，确保续费始终从当前到期时间或当前时间戳中的较大值延伸。

---

## 6. To prevent duplicate ids in _batchBurn, enforce ascending order instead of nested for loops

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
`_batchBurn` uses nested `for` loops to detect duplicate token IDs before burning. This O(n²) approach is inefficient. A more gas-efficient alternative is to enforce that token IDs be provided in strictly ascending order, which allows duplicate detection in a single O(n) pass. Furthermore, the duplicate check can be removed entirely since attempting to burn an already-burned token ID will revert with `ERC721NonexistentToken`.

**Impact:**
No security risk. The nested loop approach wastes gas for callers, especially for large batches.

**Recommended Mitigation:**
Replace the nested loops with an ascending-order enforcement check: require each token ID to be strictly greater than the previous one in the batch.

---

**[中文版本]**

**描述：**
`_batchBurn` 在销毁前使用嵌套 `for` 循环检测重复代币 ID，时间复杂度为 O(n²)，效率低下。更节省燃气的替代方案是强制代币 ID 以严格升序提供，仅需 O(n) 单次遍历即可检测重复。此外，由于重复销毁已销毁的代币 ID 会触发 `ERC721NonexistentToken` 回滚，重复检查也可完全移除。

**影響：**
无安全风险，但嵌套循环方法对调用者造成燃气浪费，大批量时尤为明显。

**修復建議：**
用升序强制检查替换嵌套循环：要求批次中每个代币 ID 严格大于前一个。

---

## 7. Unimplemented pendingReward State Variable Results in Dead Code and Potential Reward Accounting Issues

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
`F-2026-14510` — The `StakingAndRewards` contract defines a `pendingReward` field in the `Stake` struct that is initialized to zero during stake creation and is never subsequently updated throughout the contract's lifecycle. This represents dead code that implies an incomplete implementation of reward accumulation logic. In edge cases, unclaimed rewards may not be properly accounted for, and the unused field wastes storage gas.

**Impact:**
The unimplemented field introduces dead code, potentially misleads developers about the contract's reward accounting mechanism, and wastes storage gas on every stake creation.

**Recommended Mitigation:**
Either implement the `pendingReward` field with proper accumulation logic, or remove it entirely from the `Stake` struct if it is not needed.

---

**[中文版本]**

**描述：**
`F-2026-14510` — `StakingAndRewards` 合约在 `Stake` 结构体中定义了 `pendingReward` 字段，该字段在质押创建时初始化为零，在整个合约生命周期内从未更新。这是死代码，暗示奖励累积逻辑未完整实现。在边缘情况下，未领取奖励可能未被正确核算，且未使用的字段在每次质押创建时浪费存储燃气。

**影響：**
未实现的字段引入死代码，可能误导开发者对合约奖励核算机制的理解，并在每次质押创建时浪费存储燃气。

**修復建議：**
要么使用正确的累积逻辑实现 `pendingReward` 字段，要么若不需要则从 `Stake` 结构体中完全移除。

---

## 8. Use Ownable2Step instead of Ownable

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
The contract uses OpenZeppelin's single-step `Ownable`, where calling `transferOwnership` immediately transfers ownership to the new address. If the new address is incorrect or inaccessible, ownership is permanently lost. The two-step `Ownable2Step` pattern requires the new owner to call `acceptOwnership`, providing a safety check against accidental or erroneous transfers.

**Impact:**
Ownership can be permanently lost or transferred to an unintended address in a single transaction, with no recovery path.

**Recommended Mitigation:**
Replace `Ownable` with `Ownable2Step` to require explicit acceptance of ownership transfers.

---

**[中文版本]**

**描述：**
合约使用 OpenZeppelin 的单步 `Ownable`，调用 `transferOwnership` 会立即将所有权转移到新地址。若新地址不正确或无法访问，所有权将永久丢失。双步 `Ownable2Step` 模式要求新 owner 调用 `acceptOwnership`，为意外或错误转移提供安全检查。

**影響：**
所有权可能在单笔交易中永久丢失或转移到非预期地址，且无法恢复。

**修復建議：**
将 `Ownable` 替换为 `Ownable2Step`，要求显式接受所有权转移。

---

## 9. Use SafeERC20::forceApprove instead of standard IERC20::approve

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Multiple locations in `yUSDeDepositor`, `pUSDeVault`, `pUSDeDepositor`, and related contracts use the standard `IERC20::approve` for approvals. Some ERC-20 tokens (notably USDT on mainnet) do not support changing a non-zero allowance directly and require the allowance to be set to zero first. Using `SafeERC20::forceApprove` handles this edge case by automatically setting the allowance to zero before setting the new value.

**Impact:**
Deposits or swaps involving tokens like USDT may silently fail or revert if a non-zero allowance already exists, leading to stuck funds or failed operations.

**Recommended Mitigation:**
Replace all `IERC20::approve` calls with `SafeERC20::forceApprove` to handle non-standard ERC-20 approval behavior.

---

**[中文版本]**

**描述：**
`yUSDeDepositor`、`pUSDeVault`、`pUSDeDepositor` 及相关合约中的多处位置使用标准 `IERC20::approve` 进行授权。部分 ERC-20 代币（尤其是主网 USDT）不支持直接修改非零授权额度，需先将额度设为零。`SafeERC20::forceApprove` 通过在设置新值前自动将授权置零来处理此边缘情况。

**影響：**
涉及 USDT 等代币的存款或交换，若已存在非零授权额度，可能静默失败或回滚，导致资金卡死或操作失败。

**修復建議：**
将所有 `IERC20::approve` 调用替换为 `SafeERC20::forceApprove`，以处理非标准 ERC-20 授权行为。

---

## 10. Use msg.sender instead of accessing comptroller state variable to save gas

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
In `SablierEscrow::setTradeFee`, the emitted `SetTradeFee` event includes the comptroller address obtained by reading the `comptroller` storage variable (`SLOAD` = 100 gas). Since the function is protected by `onlyComptroller`, `msg.sender` is guaranteed to be the comptroller address. Using `msg.sender` (the `CALLER` opcode = 2 gas) instead avoids the expensive storage read.

**Impact:**
No security risk. Minor gas inefficiency on every `setTradeFee` call.

**Recommended Mitigation:**
Replace `address(comptroller)` in the event emission with `msg.sender`.

---

**[中文版本]**

**描述：**
在 `SablierEscrow::setTradeFee` 中，`SetTradeFee` 事件通过读取 `comptroller` 存储变量（`SLOAD` = 100 gas）获取其地址。由于该函数受 `onlyComptroller` 保护，`msg.sender` 必然是 comptroller 地址。使用 `msg.sender`（`CALLER` 操作码 = 2 gas）可避免昂贵的存储读取。

**影響：**
无安全风险，每次 `setTradeFee` 调用时存在轻微燃气低效。

**修復建議：**
将事件发出中的 `address(comptroller)` 替换为 `msg.sender`。

---

## 11. Use constants instead of magic numbers

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
The values `1000000`, `1e6`, and `10 ** 6` are used interchangeably across `TokenBank.sol`, `PledgeManager.sol`, `DividendManager.sol`, and `RemoraToken.sol` for fee basis point calculations. These identical magic numbers should be declared as a single named constant and imported across all files to improve readability, prevent divergence, and ease future maintenance.

**Impact:**
No security risk. The inconsistent use of numeric literals increases the risk of future divergence if one instance is updated without updating the others.

**Recommended Mitigation:**
Define a shared constant (e.g., `uint256 constant FEE_DENOMINATOR = 1_000_000`) and import it across all contracts that use this value.

---

**[中文版本]**

**描述：**
`TokenBank.sol`、`PledgeManager.sol`、`DividendManager.sol` 和 `RemoraToken.sol` 中 `1000000`、`1e6` 和 `10 ** 6` 被互换使用于手续费基点计算。这些相同的魔法数字应声明为单一命名常量并跨文件导入，以提高可读性、防止分歧并便于未来维护。

**影響：**
无安全风险，但不一致使用数字字面量增加了未来更新时漏改某处的风险。

**修復建議：**
定义共享常量（例如 `uint256 constant FEE_DENOMINATOR = 1_000_000`）并在所有使用该值的合约中导入。

---

## 12. Use explicit sizes instead of uint

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Multiple variables and loop counters in `yUSDeDepositor.sol`, `MetaVault.sol`, and `pUSDeVault.sol` use `uint` (which defaults to `uint256`) instead of the explicit type `uint256`. While functionally equivalent, using `uint` rather than `uint256` departs from Solidity best practices, reduces code clarity, and can cause confusion when mixed with explicitly typed variables.

**Impact:**
No security risk. Style and readability issue.

**Recommended Mitigation:**
Replace all `uint` declarations with the explicit `uint256` type throughout the codebase.

---

**[中文版本]**

**描述：**
`yUSDeDepositor.sol`、`MetaVault.sol` 和 `pUSDeVault.sol` 中的多个变量和循环计数器使用 `uint`（默认为 `uint256`）而非显式类型 `uint256`。虽然功能等价，但使用 `uint` 偏离了 Solidity 最佳实践，降低代码清晰度，与显式类型变量混用时可能造成混淆。

**影響：**
无安全风险，为代码风格和可读性问题。

**修復建議：**
将代码库中所有 `uint` 声明替换为显式 `uint256` 类型。

---

## 13. Use explicit unsigned integer sizing instead of uint

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
In `Accounting.sol` and `StrataCDO.sol`, variables are declared as `uint` rather than `uint256`. While Solidity treats these as identical, using the implicit form is considered a code quality issue and can make code harder to review alongside explicitly sized integer types.

**Impact:**
No security risk. Style issue affecting code readability and consistency.

**Recommended Mitigation:**
Replace all `uint` variable declarations with `uint256` for explicitness and consistency.

---

**[中文版本]**

**描述：**
`Accounting.sol` 和 `StrataCDO.sol` 中变量声明为 `uint` 而非 `uint256`。虽然 Solidity 将二者视为相同，但使用隐式形式被视为代码质量问题，与显式大小整数类型混用时会降低可读性。

**影響：**
无安全风险，为影响代码可读性和一致性的风格问题。

**修復建議：**
将所有 `uint` 变量声明替换为 `uint256` 以保持显式性和一致性。

---

## 14. Use of msg.sender instead of _msgSender() prevents meta-transaction support

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
Several functions in `BaseContract`, `SecuritizeOffRamp`, and `SecuritizeBridge` use `msg.sender` directly instead of `_msgSender()`. Since the protocol explicitly supports meta-transactions via ERC-2771 and uses `_msgSender()` elsewhere, these inconsistent usages mean that when a relayer submits a meta-transaction, the forwarder's address is used instead of the actual user's, causing authorization and business logic failures.

**Impact:**
Meta-transactions do not work for the affected functions. Users must hold native ETH to pay gas, defeating the purpose of the meta-transaction infrastructure already in place.

**Recommended Mitigation:**
Replace all `msg.sender` usages in affected functions with `_msgSender()` for consistent meta-transaction support.

---

**[中文版本]**

**描述：**
`BaseContract`、`SecuritizeOffRamp` 和 `SecuritizeBridge` 的多个函数直接使用 `msg.sender` 而非 `_msgSender()`。由于协议通过 ERC-2771 显式支持元交易且在其他地方使用 `_msgSender()`，这些不一致的用法导致中继者提交元交易时使用转发者地址而非实际用户地址，造成授权和业务逻辑失败。

**影響：**
元交易对受影响函数不起作用，用户必须持有原生 ETH 支付燃气，违背了已有元交易基础设施的目的。

**修復建議：**
将受影响函数中的所有 `msg.sender` 用法替换为 `_msgSender()`，以保持一致的元交易支持。

---

## 15. Use preview_redeem(...) instead of convert_to_assets(...)

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
`Issue M-5` — The `aum_provider` in Vesu Vaults retrieves asset amounts corresponding to owned shares in ERC-4626 strategies by calling `convert_to_assets(shares)`. This method returns the share-to-asset conversion at the current share price but does not account for redemption fees that may apply during `redeem()`. The ERC-4626 standard provides `preview_redeem()` specifically to return the amount receivable after fees, making it the correct function to use for AUM calculations.

**Impact:**
Using `convert_to_assets` instead of `preview_redeem` leads to overestimation of collateral assets in strategies that charge redemption fees. This causes incorrect pricing of vault shares and misleading AUM calculations that may affect protocol solvency assessments.

**Recommended Mitigation:**
Replace `convert_to_assets(shares)` with `preview_redeem(shares)` in the `aum_provider` to ensure redemption fees are properly factored into asset valuations.

---

**[中文版本]**

**描述：**
`Issue M-5` — Vesu Vaults 中的 `aum_provider` 通过调用 `convert_to_assets(shares)` 获取 ERC-4626 策略中已持有份额对应的资产数量。此方法按当前份额价格换算，但不考虑 `redeem()` 时可能适用的赎回手续费。ERC-4626 标准提供了 `preview_redeem()` 专门用于返回扣除手续费后的实际可领取金额，是 AUM 计算的正确函数。

**影響：**
在收取赎回手续费的策略中，使用 `convert_to_assets` 而非 `preview_redeem` 会高估抵押资产，导致 vault 份额定价错误和误导性的 AUM 计算，可能影响协议偿债能力评估。

**修復建議：**
将 `aum_provider` 中的 `convert_to_assets(shares)` 替换为 `preview_redeem(shares)`，确保赎回手续费在资产估值中被正确纳入。

---

## 16. Using explicit unsigned integer sizing instead of uint

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
Loop indices and variables in `PaymentSettler.sol`, `DocumentManager.sol`, and `TokenBank.sol` are declared as `uint` instead of `uint256`. While functionally identical, using the implicit type reduces code consistency and clarity, particularly when reviewing contracts that mix both forms.

**Impact:**
No security risk. Code quality and style issue.

**Recommended Mitigation:**
Replace all `uint` loop variables and declarations with `uint256` for consistency with the rest of the codebase.

---

**[中文版本]**

**描述：**
`PaymentSettler.sol`、`DocumentManager.sol` 和 `TokenBank.sol` 中的循环索引和变量声明为 `uint` 而非 `uint256`。虽然功能相同，但使用隐式类型降低了代码一致性和清晰度，在审查混用两种形式的合约时尤为明显。

**影響：**
无安全风险，为代码质量和风格问题。

**修復建議：**
将所有 `uint` 循环变量和声明替换为 `uint256`，以与代码库其余部分保持一致。
