# function-voting (3)

> Issues where governance functions, voting power calculations, or unstake mechanics behaved contrary to documentation.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. transferToCustody() function always reverts due to incorrect validation of ERC20 token address against EOA check

**Severity:** 🟠 High
**Source:** `sherlockPDFTXT/Tori Finance.txt`

**Description:**
`ToriFinance::transferToCustody` validates the `asset` parameter (an ERC20 token address) using `_validCustodyAddress(asset)`, which checks if the address has no bytecode (`addr.code.length == 0`) or is the contract itself. Since all ERC20 tokens are deployed contracts and therefore have bytecode, `_validCustodyAddress(asset)` always returns `false` for any valid ERC20 address. The function then reverts with `InvalidAddress`. Simultaneously, `IERC20(asset).safeTransfer` requires `asset` to be a contract with bytecode to function. The validation logic and the intended usage are in direct contradiction: any address that passes the validation cannot be an ERC20 token, and any valid ERC20 token will always fail the validation.

**Impact:**
`transferToCustody` is completely non-functional. Any call to this function with any valid ERC20 token address will always revert with `InvalidAddress`, making it impossible to transfer tokens to custody through this function. All custody transfer functionality is permanently broken.

**Recommended Mitigation:**
Fix `_validCustodyAddress` to validate the `route.addresses` custody destination addresses (which should be EOAs or approved custodians), not the `asset` ERC20 token address. The `asset` parameter should be validated as a contract address with bytecode, not the opposite.

---

**[中文版本]**

**描述：**
`ToriFinance::transferToCustody` 使用 `_validCustodyAddress(asset)` 验证 `asset` 参数（ERC20 代币地址），该函数检查地址是否没有字节码（`addr.code.length == 0`）或是合约本身。由于所有 ERC20 代币都是已部署的合约，因此都有字节码，`_validCustodyAddress(asset)` 对任何有效的 ERC20 地址始终返回 `false`。函数随后以 `InvalidAddress` 回滚。同时，`IERC20(asset).safeTransfer` 要求 `asset` 是一个有字节码的合约才能正常工作。验证逻辑和预期用途直接矛盾：任何通过验证的地址都不能是 ERC20 代币，任何有效的 ERC20 代币都会失败验证。

**影響：**
`transferToCustody` 完全无法运行。任何以有效 ERC20 代币地址调用此函数都将始终以 `InvalidAddress` 回滚，使通过此函数将代币转移到托管变得不可能。所有托管转移功能永久失效。

**修復建議：**
修复 `_validCustodyAddress`，使其验证 `route.addresses` 托管目标地址（应为 EOA 或已批准的托管方），而非 `asset` ERC20 代币地址。`asset` 参数应被验证为有字节码的合约地址，而非相反。

---

## 2. Addresses excluded from voting power can re-gain their voting power via a delegatee or by transferring tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
`WorldLibertyFinancialV2` implements an `excludedVotingPower` mechanism intended to permanently remove certain accounts from governance participation. When an account is excluded, its current balance is delegated to `address(0)` and `getVotes()` returns zero for that account. However, the `_delegate` function only enforces blacklist restrictions (`notBlacklisted` modifier) and has no check for `excludedVotingPower`. A excluded account can call `delegate()` to re-delegate to any address X, restoring its full voting power via X's checkpoints. Alternatively, the excluded account can transfer its tokens to a fresh non-excluded address, transferring the voting power with the tokens.

**Impact:**
The `excludedVotingPower` mechanism is fully bypassed, allowing excluded accounts to continue participating in governance by either delegating to a third party or transferring tokens. Governance decisions that should exclude certain parties remain vulnerable to manipulation by those parties.

**Recommended Mitigation:**
Override `_delegate()` to revert if the account's `excludedVotingPower` is set to true, preventing re-delegation. Override `_update()` (the internal transfer hook) to block token transfers from excluded accounts, preventing vote transfer via token movement.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialV2` 实现了 `excludedVotingPower` 机制，旨在永久将某些账户从治理参与中移除。当账户被排除时，其当前余额被委托给 `address(0)`，`getVotes()` 对该账户返回零。然而，`_delegate` 函数只执行黑名单限制（`notBlacklisted` 修饰符），不检查 `excludedVotingPower`。被排除的账户可以调用 `delegate()` 重新委托给任何地址 X，通过 X 的检查点恢复其完整的投票权。或者，被排除的账户可以将代币转移到新的未排除地址，随代币一起转移投票权。

**影響：**
`excludedVotingPower` 机制被完全绕过，允许被排除的账户通过委托给第三方或转移代币继续参与治理。应排除某些方的治理决策仍然容易受到这些方的操纵。

**修復建議：**
覆盖 `_delegate()`，若账户的 `excludedVotingPower` 被设置为 true 则回滚，防止重新委托。覆盖 `_update()`（内部转账钩子），阻止被排除账户的代币转账，防止通过代币转移来转移投票权。

---

## 3. Unstake() Function Behaves Differently Than Documented

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The project documentation explicitly states that the contract verifies its token balance on every stake and claim/withdraw operation. The `stake()` function indeed enforces strict balance constraints, checking `totalStaked + amount <= contractBalance` and blocking new stakes when the protection system is active. However, `StakingAndRewards::unstake()` performs no explicit contract-balance validation before transferring tokens back to the user. Similarly, `claimRewards()` routes through additional safeguards under constrained liquidity, but `unstake()` bypasses these protections entirely, creating a discrepancy between documented behavior and implementation.

**Impact:**
Users can call `unstake()` even when the contract has insufficient token balance to honor the withdrawal, potentially causing reverts or allowing the contract to enter an insolvent state inconsistent with the documented safety guarantees. The missing balance validation also breaks the security property that the documentation promises.

**Recommended Mitigation:**
Add an explicit contract balance check in `unstake()` before performing the token transfer, consistent with the pattern used in `stake()`. Verify that `contractBalance >= unstakeAmount` before proceeding with the transfer.

---

**[中文版本]**

**描述：**
项目文档明确说明合约在每次质押和领取/提款操作时验证其代币余额。`stake()` 函数确实执行了严格的余额约束，检查 `totalStaked + amount <= contractBalance` 并在保护系统激活时阻止新的质押。然而，`StakingAndRewards::unstake()` 在将代币返还给用户之前不进行显式的合约余额验证。类似地，`claimRewards()` 在流动性受限时经过额外的保护措施，但 `unstake()` 完全绕过了这些保护，在文档行为和实现之间造成了差异。

**影響：**
用户可以在合约没有足够代币余额来处理提款时调用 `unstake()`，可能导致回滚或允许合约进入与文档安全保证不一致的资不抵债状态。缺失的余额验证也破坏了文档承诺的安全属性。

**修復建議：**
在 `unstake()` 中执行代币转账之前添加显式的合约余额检查，与 `stake()` 中使用的模式一致。在继续转账之前验证 `contractBalance >= unstakeAmount`。
