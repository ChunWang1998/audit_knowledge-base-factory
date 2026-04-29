# transfer-token (16)

> Issues where unsafe ERC-20 transfer patterns, missing SafeERC20, or approval mechanisms cause unexpected failures.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Investors can steal tokens from other investors since StandardToken::transferFrom never checks spending approvals

**Severity:** 🔴 Critical
**Source:** `cyfrin/rebasing.md`

**Description:**
`StandardToken::transferFrom` executes a token transfer from one investor to another without ever checking whether the caller has been granted an allowance by the `from` address. Standard ERC-20 `transferFrom` must verify that `spender` has been approved by `from` for at least the requested amount. The missing approval check means any registered investor can call `transferFrom(victim, attacker, amount)` and drain tokens from any other investor's balance without any prior authorization.

**Impact:**
Any investor can steal the full token balance of any other investor using a single `transferFrom` call. This is a critical fund theft vulnerability affecting every token holder in the system.

**Recommended Mitigation:**
Implement standard ERC-20 allowance enforcement in `StandardToken::transferFrom`: check that `allowance[from][msg.sender] >= amount` before executing the transfer, and decrement the allowance accordingly.

---

**[中文版本]**

**描述：**
`StandardToken::transferFrom` 在执行代币转账时从未检查调用者是否获得了 `from` 地址的授权。标准 ERC-20 的 `transferFrom` 必须验证花费者已被 `from` 授权至少请求的数量。缺少此检查意味着任何已注册的投资者都可以调用 `transferFrom(受害者, 攻击者, 数量)` 来耗尽其他投资者的代币余额，无需任何事先授权。

**影響：**
任何投资者均可通过单次 `transferFrom` 调用窃取任何其他投资者的全部代币余额，属于影响系统中所有持有人的严重资金盗窃漏洞。

**修復建議：**
在 `StandardToken::transferFrom` 中实施标准 ERC-20 授权验证：在执行转账前检查 `allowance[from][msg.sender] >= amount`，并相应递减授权额度。

---

## 2. Funds Loss via Direct Transfer in CustodyVault

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/S3 Markets.txt`

**Description:**
`CustodyVault` implements `IERC1155Receiver` to accept ERC1155 token transfers, but its `onERC1155Received` and `onERC1155BatchReceived` hooks only update the internal `unassigned` balance when the `from` address is `address(0)` (i.e., minting). When any non-zero address sends ERC1155 tokens directly to the vault via `safeTransferFrom`, the vault accepts the tokens but does not credit them to any internal ledger (`freeBalance`, `unassigned`). The tokens are permanently locked in the vault with no mechanism for recovery, withdrawal, or allocation.

**Impact:**
Any ERC1155 tokens sent directly to the `CustodyVault` by users are permanently locked. They cannot be withdrawn, allocated, or retrieved through any standard protocol function. The affected tokens are irretrievably lost.

**Recommended Mitigation:**
Update `onERC1155Received` and `onERC1155BatchReceived` to credit incoming tokens from non-zero addresses to the internal accounting (`unassigned` or `freeBalance`), or revert on direct transfers to prevent unaccounted token ingestion.

---

**[中文版本]**

**描述：**
`CustodyVault` 实现了 `IERC1155Receiver` 以接受 ERC1155 代币转账，但其 `onERC1155Received` 和 `onERC1155BatchReceived` 回调仅在 `from` 为零地址（即铸造）时更新内部 `unassigned` 余额。当任何非零地址通过 `safeTransferFrom` 直接向金库发送 ERC1155 代币时，金库接受代币但不在任何内部账本中记账，代币被永久锁定。

**影響：**
用户直接发送至 `CustodyVault` 的任何 ERC1155 代币将被永久锁定，无法通过任何标准协议函数提取、分配或找回，代币不可逆地丢失。

**修復建議：**
更新 `onERC1155Received` 和 `onERC1155BatchReceived`，将来自非零地址的代币计入内部账本（`unassigned` 或 `freeBalance`），或对直接转账执行回滚以防止未记账的代币进入。

---

## 3. Use of IERC20.transfer() Instead of SafeERC20.safeTransfer() in Refund Path

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The `_settleSessionPayments` function uses a raw `IERC20.transfer` call inside a `try/catch` block for ERC20 refunds, while all other ERC20 transfer operations across the codebase consistently use `SafeERC20.safeTransfer`. Non-standard ERC20 tokens (such as USDT on Ethereum mainnet) do not return a boolean from `transfer`, causing the raw call to revert unexpectedly due to ABI decoding failure. The `try/catch` would catch this revert and credit the refund to the deposit mapping, but the failure mode is fragile and inconsistent with the rest of the codebase.

**Impact:**
Refunds for sessions using non-standard ERC20 tokens (no boolean return) will silently fail via the catch branch, crediting the refund to the deposit mapping instead of transferring it directly. While this avoids an outright fund loss, it creates an inconsistent refund experience and can break integrations that expect direct refund transfers.

**Recommended Mitigation:**
Replace the raw `IERC20.transfer` call in `_settleSessionPayments` with `SafeERC20.safeTransfer`, consistent with all other ERC20 transfer operations in the codebase. This ensures non-standard token transfers are handled correctly.

---

**[中文版本]**

**描述：**
`_settleSessionPayments` 在 ERC20 退款路径的 `try/catch` 块中使用原生 `IERC20.transfer` 调用，而代码库其他所有 ERC20 转账操作均使用 `SafeERC20.safeTransfer`。不返回布尔值的非标准 ERC20 代币（如主网 USDT）会因 ABI 解码失败导致原生调用意外回滚，被 `catch` 捕获后将退款计入存款映射而非直接转账，处理方式不一致。

**影響：**
使用不返回布尔值的非标准 ERC20 代币的会话退款将通过 catch 分支静默失败，退款被计入存款映射而非直接转出，破坏退款体验并可能中断期望直接退款转账的集成。

**修復建議：**
将 `_settleSessionPayments` 中的原生 `IERC20.transfer` 调用替换为 `SafeERC20.safeTransfer`，与代码库中所有其他 ERC20 转账操作保持一致，确保非标准代币转账被正确处理。

---

## 4. Complete bypass of transfer restrictions on vault share token is possible

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableVault` enforces transfer restrictions (KYC checks, throttle timestamps) in `_checkTransfer`, which is applied to `transfer()` and `transferFrom()`. However, a user can completely bypass these restrictions by exploiting the `cancelRedeemRequest` / `claimCancelRedeemRequest` flow. A controller places a redeem request, immediately cancels it, then calls `claimCancelRedeemRequest` specifying any `receiver` address. The internal `_transfer` used in this path does not go through `_checkTransfer`, allowing share tokens to reach non-KYC'd addresses.

**Impact:**
Any KYC'd user can transfer vault share tokens to any non-KYC'd address by cycling through the cancel-redeem flow, completely defeating the intended access control restrictions on share token transfers.

**Recommended Mitigation:**
Apply the same `_checkTransfer` restrictions inside `claimCancelRedeemRequest` when executing the share token transfer to the `receiver`, ensuring that KYC and throttle checks are enforced for all transfer paths including cancellation flows.

---

**[中文版本]**

**描述：**
`AccountableVault` 通过 `_checkTransfer` 对 `transfer()` 和 `transferFrom()` 执行转账限制（KYC 检查、节流时间戳）。但用户可通过利用 `cancelRedeemRequest` / `claimCancelRedeemRequest` 流程完全绕过这些限制：控制者提交赎回请求，立即取消，再调用 `claimCancelRedeemRequest` 并指定任意 `receiver` 地址；此路径使用的内部 `_transfer` 不经过 `_checkTransfer`，允许份额代币到达未经 KYC 的地址。

**影響：**
任何已 KYC 的用户均可通过取消赎回流程将金库份额代币转移给任何未 KYC 的地址，完全规避份额代币转账上的访问控制限制。

**修復建議：**
在 `claimCancelRedeemRequest` 执行向 `receiver` 的份额代币转账时，应用与 `_checkTransfer` 相同的限制，确保 KYC 和节流检查在所有转账路径（包括取消流程）中均被执行。

---

## 5. ERC20 zero amount transfer rejection

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableVault::_checkTransfer` reverts on zero-amount transfers. The ERC-20 standard explicitly states that "transfers of 0 values MUST be treated as normal transfers and fire the Transfer event." By reverting instead of silently succeeding, the vault violates this mandatory requirement, breaking compatibility with any ERC-20 tooling, wallet, or protocol that sends zero-value transfers as part of standard operations (e.g., allowance checks, event triggers, or compatibility probes).

**Impact:**
Protocols and tools that send zero-value ERC-20 transfers as a compatibility probe or operational pattern will fail when interacting with the vault's share token, reducing composability and integration compatibility.

**Recommended Mitigation:**
Remove the zero-amount revert from `_checkTransfer` and allow zero-value transfers to proceed normally, emitting the `Transfer` event as required by EIP-20.

---

**[中文版本]**

**描述：**
`AccountableVault::_checkTransfer` 对零金额转账执行回滚。ERC-20 标准明确规定"零值转账必须被视为正常转账并触发 Transfer 事件"。通过回滚而非静默成功，金库违反了此强制性要求，破坏了与任何以零值转账作为标准操作（如授权检查、事件触发或兼容性探测）的 ERC-20 工具、钱包或协议的兼容性。

**影響：**
将零值 ERC-20 转账作为兼容性探测或操作模式的协议和工具，在与金库份额代币交互时将失败，降低可组合性和集成兼容性。

**修復建議：**
从 `_checkTransfer` 中移除零金额回滚逻辑，允许零值转账正常处理，并按 EIP-20 要求触发 `Transfer` 事件。

---

## 6. In Bet::cancel if one transfer reverts but the other succeeds, one user's tokens are permanently locked in the Bet contract

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`Bet::cancel` attempts to refund both the maker and taker using `try/catch` blocks. If the first refund transfer (e.g., to the maker) succeeds but the second (e.g., to the taker) reverts, the maker has already received their refund. However, the second user's tokens remain stuck in the contract because the `try/catch` suppresses the revert, the bet state is already marked as cancelled, and there is no retry mechanism or recovery path for the stranded funds.

**Impact:**
One user's tokens can be permanently locked in the Bet contract if their transfer reverts while the other user's transfer succeeds, with no recovery path available through normal protocol operations.

**Recommended Mitigation:**
Use `SafeERC20.safeTransfer` for both refund transfers instead of the `try/catch` pattern, ensuring that if either refund fails the entire transaction reverts and both users retain their positions until a successful cancel can be executed.

---

**[中文版本]**

**描述：**
`Bet::cancel` 使用 `try/catch` 块尝试向 maker 和 taker 退款。若第一笔退款成功而第二笔回滚，`try/catch` 压制了回滚，bet 状态已被标记为已取消，第二个用户的代币被永久锁定在合约中且无任何恢复路径。

**影響：**
若一方退款转账回滚而另一方成功，受影响方的代币被永久锁定在 Bet 合约中，通过正常协议操作无法找回。

**修復建議：**
用 `SafeERC20.safeTransfer` 替代 `try/catch` 模式处理两笔退款转账，确保任意一笔退款失败时整个交易回滚，双方均保留仓位直到取消操作能成功执行。

---

## 7. In RemoraToken::transfer, transferFrom and _exchangeAllowed perform all checks for each user together in order to prevent unnecessary work

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`RemoraToken::transfer`, `transferFrom`, and `_exchangeAllowed` call `Allowlist::exchangeAllowed` to validate both parties but do not check the boolean return value of `_exchangeAllowed` after it is called. `Allowlist::exchangeAllowed` returns `false` when both parties are allowed but have a domestic/foreign mismatch. Because `RemoraToken::_exchangeAllowed` propagates this return value but neither `transfer` nor `transferFrom` checks it, transfers are permitted even when `exchangeAllowed` returns `false`, defeating the intent of the domestic/foreign trading restriction.

**Impact:**
Transfers that should be blocked due to domestic/foreign mismatch between sender and receiver are allowed through without restriction, violating the intended compliance controls on cross-type token transfers.

**Recommended Mitigation:**
Check the boolean return value of `_exchangeAllowed` in `transfer` and `transferFrom` and revert if it returns `false`, or change `Allowlist::exchangeAllowed` to revert directly on mismatch rather than returning a boolean.

---

**[中文版本]**

**描述：**
`RemoraToken::transfer`、`transferFrom` 和 `_exchangeAllowed` 均调用 `Allowlist::exchangeAllowed` 验证双方，但均不检查 `_exchangeAllowed` 的布尔返回值。当双方均已注册但存在境内/境外不匹配时，`exchangeAllowed` 返回 `false`，但由于返回值未被检查，转账仍被允许，违反了境内/境外交易限制的设计意图。

**影響：**
因境内/境外不匹配而本应被阻止的转账得以通过，违反了跨类型代币转账上的合规控制。

**修復建議：**
在 `transfer` 和 `transferFrom` 中检查 `_exchangeAllowed` 的布尔返回值，若为 `false` 则回滚；或将 `Allowlist::exchangeAllowed` 改为在不匹配时直接回滚而非返回布尔值。

---

## 8. Missing Transfer Event for Taxed Amount Breaks ERC20 Compliance and Causes Balance Tracking Mismatches

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
In KnoxNet's transfer flow (`_transferFrom`), a portion of the transferred amount is deducted as a tax and credited to the contract balance. Only a single `Transfer` event is emitted for the post-tax net amount sent to the recipient. No `Transfer` event is emitted for the taxed portion credited to the contract. This breaks the ERC-20 event model, which requires a `Transfer` event for every balance change. Off-chain tools and indexers that rely on `Transfer` events to reconstruct balances will produce divergent results from actual on-chain state.

**Impact:**
Balance tracking by explorers, wallets, and indexers becomes incorrect for KnoxNet tokens, as the taxed portion of every transfer is never reflected in the event log. This can cause integration failures and incorrect balance displays.

**Recommended Mitigation:**
Emit a separate `Transfer(sender, address(this), taxAmount)` event for the taxed portion in `_transferFrom`, ensuring that every balance change is represented by a corresponding Transfer event as required by ERC-20.

---

**[中文版本]**

**描述：**
KnoxNet 的转账流程（`_transferFrom`）将部分金额作为税款扣除并计入合约余额，但只为扣税后的净金额发出一个 `Transfer` 事件，税款部分没有对应的 `Transfer` 事件。ERC-20 标准要求每次余额变化都发出 `Transfer` 事件，此缺失导致链下工具和索引器无法正确重建余额。

**影響：**
区块链浏览器、钱包和索引器对 KnoxNet 代币的余额追踪将不准确，因为每笔转账的税款部分永远不会反映在事件日志中，可能导致集成失败和余额显示错误。

**修復建議：**
在 `_transferFrom` 中为税款部分单独发出 `Transfer(sender, address(this), taxAmount)` 事件，确保每次余额变化都有对应的 Transfer 事件，符合 ERC-20 标准要求。

---

## 9. TokenBank::removeToken reverts when token balance is zero, making it impossible to remove tokens from the developments array

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`TokenBank::removeToken` calls `withdrawTokens(tokenAddress, custodialWallet, 0)` as part of the removal flow, but `withdrawTokens` reverts when the token balance in the contract is zero. As a result, once a token's balance has been fully withdrawn or was never deposited, it becomes impossible to clean it out of the `developments` array. Over time the array grows indefinitely with stale entries that waste gas during fee claiming iterations.

**Impact:**
The `developments` array accumulates unbounded stale token entries, increasing gas costs for all operations that iterate over it (primarily fee claiming). Protocol administrators cannot perform routine ledger cleanup without deploying a fix.

**Recommended Mitigation:**
In `removeToken`, add a balance check before calling `withdrawTokens`: only call `withdrawTokens` if `IERC20(tokenAddress).balanceOf(address(this)) > 0`, otherwise skip the withdrawal and proceed directly to removing the token from the `developments` array.

---

**[中文版本]**

**描述：**
`TokenBank::removeToken` 在移除流程中调用 `withdrawTokens(tokenAddress, custodialWallet, 0)`，但当合约中的代币余额为零时，`withdrawTokens` 会回滚。因此，一旦代币余额被完全提取或从未存入，就无法将其从 `developments` 数组中清除，该数组会无限增长，充满陈旧条目，在手续费领取迭代中浪费 gas。

**影響：**
`developments` 数组无界积累陈旧代币条目，增加所有迭代操作（主要是手续费领取）的 gas 成本，协议管理员无法在不部署修复的情况下执行常规账本清理。

**修復建議：**
在 `removeToken` 中调用 `withdrawTokens` 前增加余额检查：仅当 `IERC20(tokenAddress).balanceOf(address(this)) > 0` 时才调用 `withdrawTokens`，否则跳过提款步骤，直接将代币从 `developments` 数组中移除。

---

## 10. Transfer Amount enforcer for ERC20 and Native transfers increase spend limit without checking actual transfers

**Severity:** 🟡 Medium
**Source:** `cyfrin/DelegationFramework1.md`

**Description:**
The `ERC20TransferAmountEnforcer` and native transfer enforcer increment the `spentMap` counter in their `beforeHook`, which executes before the actual token transfer. When the delegation uses `EXECTYPE_TRY` execution mode, a failed token transfer does not cause the transaction to revert; instead, execution continues. The spending counter has already been incremented even though no tokens were actually transferred, permanently reducing the delegation's remaining allowance without any corresponding value movement.

**Impact:**
Repeated failed transfers under `EXECTYPE_TRY` mode silently exhaust a delegation's spending limit without any actual token movement, effectively denying legitimate future use of the delegation's spending allowance after a series of failed executions.

**Recommended Mitigation:**
Move the spend limit increment to the `afterHook` so it only fires after the actual transfer has confirmed success, or add a post-execution check that verifies the transfer occurred before incrementing the counter.

---

**[中文版本]**

**描述：**
`ERC20TransferAmountEnforcer` 和原生转账执行器在 `beforeHook` 中递增 `spentMap` 计数器（在实际转账前执行）。当委托使用 `EXECTYPE_TRY` 执行模式时，转账失败不会导致交易回滚，执行继续进行，但计数器已被递增。这意味着即使没有实际代币转移，支出限额也被永久消耗。

**影響：**
在 `EXECTYPE_TRY` 模式下反复失败的转账会静默耗尽委托的支出限额，而没有任何实际代币移动，在一系列失败执行后有效地阻止了委托支出授权的合法使用。

**修復建議：**
将支出限额递增移至 `afterHook`，使其仅在实际转账确认成功后触发；或在递增计数器前增加后置执行检查，验证转账已发生。

---

## 11. Unsafe ERC20 operations can cause unexpected failures with non-standard tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
`RWASegWrap::_pullAndApprove` uses direct `IERC20.transferFrom` and `IERC20.approve` calls instead of `SafeERC20` wrappers. This is a critical internal function used during deposit and mint operations. Tokens like USDT do not return a boolean from `transfer` and revert when `approve` is called from a non-zero existing allowance to another non-zero value. Similar unsafe patterns appear in `SecuritizeVault::liquidate` and `SecuritizeVaultV2::_liquidateTo`. These core operations — deposits, mints, and liquidations — become unreliable for any token with non-standard ERC-20 behavior.

**Impact:**
Users attempting to deposit or mint using non-standard ERC-20 tokens (e.g., USDT) will face unexpected transaction reverts, making the protocol non-functional for a broad class of commonly used tokens. Liquidation paths are similarly affected, potentially leaving undercollateralized positions un-liquidated.

**Recommended Mitigation:**
Replace all direct `IERC20.transferFrom` and `IERC20.approve` calls in `RWASegWrap`, `SecuritizeVault`, and `SecuritizeVaultV2` with their `SafeERC20` equivalents (`safeTransferFrom`, `forceApprove`), ensuring compatibility with tokens that have non-standard return value behavior.

---

**[中文版本]**

**描述：**
`RWASegWrap::_pullAndApprove` 使用原生 `IERC20.transferFrom` 和 `IERC20.approve` 调用而非 `SafeERC20` 包装器，这是存款和铸造操作中使用的关键内部函数。USDT 等代币的 `transfer` 不返回布尔值，且从非零现有授权量调用 `approve` 时会回滚。类似的不安全模式也出现在 `SecuritizeVault::liquidate` 和 `SecuritizeVaultV2::_liquidateTo` 中，使这些核心操作对任何非标准 ERC-20 代币均不可靠。

**影響：**
使用非标准 ERC-20 代币（如 USDT）进行存款或铸造的用户将面临意外交易回滚，使协议对广泛使用的代币类别无法正常工作。清算路径同样受到影响，可能导致抵押不足的仓位无法被清算。

**修復建議：**
将 `RWASegWrap`、`SecuritizeVault` 和 `SecuritizeVaultV2` 中所有原生 `IERC20.transferFrom` 和 `IERC20.approve` 调用替换为 `SafeERC20` 等价函数（`safeTransferFrom`、`forceApprove`），确保与具有非标准返回值行为的代币兼容。

---

## 12. Use SafeERC20 functions instead of standard ERC20 functions

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`Bet.sol` uses standard `IERC20.transferFrom`, `IERC20.transfer`, and `IERC20.approve` calls throughout its lifecycle functions (`initialize`, `accept`, `resolve`, `cancel`). These direct calls will fail for tokens that do not return a boolean value (e.g., USDT), return `false` without reverting, or require resetting approval to zero before setting a new value. Because `Bet` is designed to work with arbitrary `asset` tokens specified at creation, any of these non-standard behaviors can silently fail or revert at critical points in a bet's lifecycle.

**Impact:**
Bets using non-standard ERC-20 tokens may become stuck at initialization, resolution, or cancellation. In `cancel`, the existing `try/catch` around transfers may mask failures and leave one party unable to recover their stake.

**Recommended Mitigation:**
Replace all direct `IERC20` transfer and approval calls in `Bet.sol` with `SafeERC20.safeTransfer`, `SafeERC20.safeTransferFrom`, and `SafeERC20.forceApprove` to handle non-standard token behavior safely across all bet lifecycle operations.

---

**[中文版本]**

**描述：**
`Bet.sol` 在整个生命周期函数（`initialize`、`accept`、`resolve`、`cancel`）中使用原生的 `IERC20.transferFrom`、`IERC20.transfer` 和 `IERC20.approve` 调用。这些直接调用对不返回布尔值的代币（如 USDT）、返回 `false` 而不回滚的代币，以及需要先将授权清零再设置新值的代币均会失败。由于 `Bet` 设计为与创建时指定的任意 `asset` 代币配合使用，这些非标准行为可能在 bet 生命周期的关键节点静默失败或回滚。

**影響：**
使用非标准 ERC-20 代币的 bet 可能在初始化、结算或取消时陷入停滞；`cancel` 中的 `try/catch` 可能掩盖失败，导致一方无法取回质押资金。

**修復建議：**
将 `Bet.sol` 中所有直接的 `IERC20` 转账和授权调用替换为 `SafeERC20.safeTransfer`、`SafeERC20.safeTransferFrom` 和 `SafeERC20.forceApprove`，安全处理所有 bet 生命周期操作中的非标准代币行为。

---

## 13. Use SafeERC20 functions instead of standard ERC20 transfer functions

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
Several functions in the Remora protocol (`DividendManager`, `RemoraToken`) use standard `IERC20.transfer` and `IERC20.transferFrom` calls instead of `SafeERC20` wrappers. This creates compatibility issues with non-standard ERC-20 tokens that either do not return a boolean from `transfer`/`transferFrom` or return `false` without reverting. These functions handle core protocol operations including stablecoin payouts and property token transfers.

**Impact:**
Stablecoin payout distributions and property token transfer operations will silently fail or revert when using non-standard ERC-20 tokens, breaking core protocol functionality for any deployment that relies on such tokens.

**Recommended Mitigation:**
Replace all direct `IERC20.transfer` and `IERC20.transferFrom` calls in `DividendManager.sol` and `RemoraToken.sol` with `SafeERC20.safeTransfer` and `SafeERC20.safeTransferFrom` to ensure reliable behavior across all ERC-20 token implementations.

---

**[中文版本]**

**描述：**
Remora 协议中多个函数（`DividendManager`、`RemoraToken`）使用原生 `IERC20.transfer` 和 `IERC20.transferFrom` 调用而非 `SafeERC20` 包装器，与不返回布尔值或返回 `false` 而不回滚的非标准 ERC-20 代币存在兼容性问题，影响稳定币分红和房产代币转账等核心协议操作。

**影響：**
使用非标准 ERC-20 代币时，稳定币分红分发和房产代币转账操作将静默失败或回滚，破坏依赖此类代币的所有部署的核心协议功能。

**修復建議：**
将 `DividendManager.sol` 和 `RemoraToken.sol` 中所有原生 `IERC20.transfer` 和 `IERC20.transferFrom` 调用替换为 `SafeERC20.safeTransfer` 和 `SafeERC20.safeTransferFrom`，确保在所有 ERC-20 代币实现中的可靠行为。

---

## 14. Zero token transfers record receiving user as a holder in DividendManager::HolderStatus even if they have zero token balance

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DividendManager::_updateHolders` is called on every token transfer to update holder status. When a zero-amount transfer is executed, the receiving address is recorded as a holder in `_holderStatus` even though their token balance remains zero. This creates phantom holders in the registry who have zero balance but are tracked as holders. Phantom holders can potentially claim payout distributions they are not entitled to, and their presence inflates the holder set, increasing gas costs for operations that iterate over holders.

**Impact:**
Zero-amount transfers create phantom holder records, potentially enabling unentitled payout claims and inflating gas costs for holder-iterating operations. The integrity of the holder registry is compromised.

**Recommended Mitigation:**
In `_updateHolders`, only add an address to the holder registry if the transfer amount is greater than zero and the resulting balance is greater than zero. Alternatively, add a zero-amount transfer guard at the entry point of `transfer` and `transferFrom` that skips holder updates for zero-value movements.

---

**[中文版本]**

**描述：**
`DividendManager::_updateHolders` 在每次代币转账时被调用以更新持有人状态。当执行零金额转账时，接收地址被记录为持有人（`_holderStatus`），尽管其代币余额仍为零。这在注册表中创建了余额为零但被追踪为持有人的"幽灵持有人"，可能不当领取分红并增加迭代持有人操作的 gas 成本。

**影響：**
零金额转账创建幽灵持有人记录，可能使无权用户获得分红，并因持有人集合虚增而提高相关操作的 gas 成本，损害持有人注册表的完整性。

**修復建議：**
在 `_updateHolders` 中，仅当转账金额大于零且接收方余额大于零时才将地址添加至持有人注册表；或在 `transfer` 和 `transferFrom` 入口处为零值移动跳过持有人更新。

---

## 15. burn should delete tokenURI related data and emit TokenUriUnpinned event

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
The `CryptoartNFT::burn` function destroys the NFT and resets royalty data, but does not delete the associated `_tokenURIs`, `_pinnedURIIndex`, or `_hasPinnedTokenURI` mappings for the burned token. As a result, burned tokens leave behind stale metadata in storage, wasting gas slots and causing `hasPinnedTokenURI` to return `true` for a token that no longer exists. The `TokenUriUnpinned` event is also never emitted on burn, breaking the expected lifecycle event sequence for IERC7160 implementors.

**Impact:**
Burned tokens leave stale metadata in storage, causing `hasPinnedTokenURI` to incorrectly return `true` for non-existent tokens and wasting gas slots. External integrators relying on `TokenUriUnpinned` events to track URI lifecycle will miss the burn-time unpin.

**Recommended Mitigation:**
In `burn`, after burning the NFT, delete `_tokenURIs[tokenId]`, `_pinnedURIIndex[tokenId]`, and `_hasPinnedTokenURI[tokenId]`, and emit `TokenUriUnpinned(tokenId)`. This provides a gas refund, cleans up stale state, and ensures correct event history.

---

**[中文版本]**

**描述：**
`CryptoartNFT::burn` 销毁 NFT 并重置版税数据，但未删除已销毁代币对应的 `_tokenURIs`、`_pinnedURIIndex` 和 `_hasPinnedTokenURI` 映射条目，导致已销毁代币在存储中留下陈旧元数据，`hasPinnedTokenURI` 对不存在的代币错误返回 `true`，且未发出 `TokenUriUnpinned` 事件，破坏了 IERC7160 实现者期望的生命周期事件序列。

**影響：**
已销毁代币在存储中留下陈旧元数据，`hasPinnedTokenURI` 对不存在的代币错误返回 `true`，浪费 gas 槽位；依赖 `TokenUriUnpinned` 事件追踪 URI 生命周期的外部集成将错过销毁时的解绑事件。

**修復建議：**
在 `burn` 中，销毁 NFT 后删除 `_tokenURIs[tokenId]`、`_pinnedURIIndex[tokenId]` 和 `_hasPinnedTokenURI[tokenId]`，并发出 `TokenUriUnpinned(tokenId)`，从而获得 gas 退款、清理陈旧状态并确保正确的事件历史记录。

---

## 16. pUSDeVault::maxMint doesn't account for mint pausing, in violation of EIP-4626 which can break protocols integrating with pUSDeVault

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
EIP-4626 requires that `maxMint` "MUST factor in both global and user-specific limits, like if mints are entirely disabled (even temporarily) it MUST return 0." `pUSDeVault::maxMint` does not account for deposit or mint pausing. Because `MetaVault::mint` uses `_deposit` internally, minting is effectively paused when deposits are paused. However, `maxMint` continues to return `type(uint256).max` even when deposits are disabled, falsely advertising that minting is available. Any protocol that calls `maxMint` to determine whether to proceed with a mint will be misled and will fail on the subsequent `mint` call.

**Impact:**
Protocols integrating with `pUSDeVault` that query `maxMint` before minting will receive incorrect availability data, potentially triggering failed transactions and causing integration-level bugs that are difficult to diagnose.

**Recommended Mitigation:**
Override `maxMint` in `PreDepositVault` (where pausing is implemented) to return 0 when deposits are paused, ensuring EIP-4626 compliance and accurate availability reporting to integrators.

---

**[中文版本]**

**描述：**
EIP-4626 要求 `maxMint` 必须考虑全局和用户级别的限制，如果铸造被完全禁用（即使是暂时的）则必须返回 0。`pUSDeVault::maxMint` 未考虑存款或铸造暂停状态。由于 `MetaVault::mint` 内部使用 `_deposit`，存款暂停时铸造实际上也被暂停，但 `maxMint` 在存款禁用时仍返回 `type(uint256).max`，错误地宣告铸造可用，误导任何在铸造前查询 `maxMint` 的集成协议。

**影響：**
在铸造前查询 `maxMint` 的集成协议将收到不准确的可用性数据，可能触发失败的交易，造成难以诊断的集成级错误。

**修復建議：**
在 `PreDepositVault`（实现暂停功能的地方）中覆盖 `maxMint`，使其在存款暂停时返回 0，确保符合 EIP-4626 规范并向集成方提供准确的可用性信息。
