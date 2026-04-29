# return-remove (7)

> Issues where obsolete return statements or named return variables created ambiguity or incorrect behavior.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Remove obsolete return statements when already using named return variables — cyfrin/rebasing.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
Two functions in the Securitize token contracts use named return variables and also contain explicit `return` statements that repeat the named variable, making the final `return` redundant. In `BulkBalanceChecker.sol` the final `return balances;` statement is unnecessary because `balances` is already declared as the named return. In `SecuritizeSwap.sol` the final `return (dsTokenAmount, currentNavRate);` is similarly redundant. Solidity will automatically return the named variables when execution reaches the end of the function.

**Impact:**
Redundant return statements add minor bytecode bloat and cognitive overhead for developers reading the functions. They can also create confusion about whether the function uses explicit or implicit return semantics, leading to maintenance errors in future modifications.

**Recommended Mitigation:**
Remove the final `return balances;` statement from `BulkBalanceChecker` and the final `return (dsTokenAmount, currentNavRate);` statement from `SecuritizeSwap` since the named return variables are automatically returned.

---

**[中文版本]**

**描述：**
Securitize 代币合约中的两个函数使用了命名返回变量，同时还包含重复命名变量的显式 `return` 语句，使最终的 `return` 成为冗余。在 `BulkBalanceChecker.sol` 中，最终的 `return balances;` 语句是不必要的，因为 `balances` 已声明为命名返回。在 `SecuritizeSwap.sol` 中，最终的 `return (dsTokenAmount, currentNavRate);` 同样是冗余的。当执行到函数末尾时，Solidity 会自动返回命名变量。

**影響：**
冗余的返回语句增加了少量字节码膨胀，并为阅读函数的开发者增加了认知负担。它们还可能造成对函数使用显式还是隐式返回语义的困惑，在未来修改中引发维护错误。

**修復建議：**
从 `BulkBalanceChecker` 中移除最终的 `return balances;` 语句，从 `SecuritizeSwap` 中移除最终的 `return (dsTokenAmount, currentNavRate);` 语句，因为命名返回变量会被自动返回。

---

## 2. Remove obsolete return statements when already using named return variables — cyfrin/wannabetv2.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`Bet::bet` declares a named return variable but also contains an explicit `return` statement at the end of the function body that restates the named return variable. When a function declares a named return variable and assigns it throughout the function body, the final explicit `return` statement is redundant — Solidity will automatically return the named variable when execution reaches the closing brace.

**Impact:**
The redundant `return` statement adds minor bytecode bloat and can confuse developers about whether the function relies on explicit or implicit return semantics. Future modifications to the function may inadvertently introduce bugs if the dual-return pattern is misunderstood.

**Recommended Mitigation:**
Remove the final explicit `return` statement from `Bet::bet` and rely on the implicit return of the named return variable.

---

**[中文版本]**

**描述：**
`Bet::bet` 声明了命名返回变量，但函数体末尾也包含一个显式的 `return` 语句，重述了命名返回变量。当函数声明命名返回变量并在函数体中赋值时，最终的显式 `return` 语句是冗余的——当执行到闭括号时，Solidity 会自动返回命名变量。

**影響：**
冗余的 `return` 语句增加了少量字节码膨胀，可能使开发者对函数是依赖显式还是隐式返回语义产生困惑。如果双重返回模式被误解，未来对函数的修改可能无意间引入错误。

**修復建議：**
从 `Bet::bet` 中移除最终的显式 `return` 语句，依靠命名返回变量的隐式返回。

---

## 3. Remove obsolete return statements when using named return values — cyfrin/protocol.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::_calculatePlayerSessionResult` declares named return values but also contains a final explicit `return` statement that restates those named values. Since the function already assigns to the named return variables throughout its body, the final `return` is entirely redundant. The presence of both a named return declaration and an explicit `return` at the end is a common source of confusion and inconsistency.

**Impact:**
The redundant `return` statement creates minor code quality issues and adds unnecessary complexity. Developers modifying the function in the future may be confused about whether the named returns or the explicit return statement is the intended mechanism, increasing the risk of introducing subtle bugs.

**Recommended Mitigation:**
Remove the final explicit `return` statement from `DefaultSession::_calculatePlayerSessionResult` and rely on the implicit return of the named return variables.

---

**[中文版本]**

**描述：**
`DefaultSession::_calculatePlayerSessionResult` 声明了命名返回值，但也包含一个在末尾重述这些命名值的显式 `return` 语句。由于函数在整个函数体中已对命名返回变量进行赋值，最终的 `return` 完全是冗余的。同时存在命名返回声明和末尾显式 `return` 语句是常见的混淆和不一致来源。

**影響：**
冗余的 `return` 语句造成轻微的代码质量问题，增加了不必要的复杂性。未来修改函数的开发者可能对命名返回还是显式 `return` 语句是预期机制产生困惑，增加了引入细微错误的风险。

**修復建議：**
从 `DefaultSession::_calculatePlayerSessionResult` 中移除最终的显式 `return` 语句，依靠命名返回变量的隐式返回。

---

## 4. Remove obsolete return statements when using named return variables — cyfrin/syntetika.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault::_withdrawTo` and `StakingVault::redeemTo` both declare named return variables and assign to them throughout their function bodies. Both functions also contain final explicit `return` statements that are redundant given the named return declarations. Mixing named returns with explicit return statements in the same function creates an inconsistent coding style and can mislead readers about the actual return semantics.

**Impact:**
The redundant explicit `return` statements add minor bytecode overhead and reduce code clarity. Inconsistent use of return conventions within a file makes the codebase harder to maintain and may introduce bugs during future refactors.

**Recommended Mitigation:**
Remove the redundant explicit `return` statements from `StakingVault::_withdrawTo` and `redeemTo`, using only the named return variables.

---

**[中文版本]**

**描述：**
`StakingVault::_withdrawTo` 和 `StakingVault::redeemTo` 都声明了命名返回变量并在函数体中赋值。两个函数还包含最终的显式 `return` 语句，鉴于命名返回声明的存在，这些语句是冗余的。在同一函数中混用命名返回和显式返回语句会造成不一致的编码风格，可能误导读者对实际返回语义的理解。

**影響：**
冗余的显式 `return` 语句增加了少量字节码开销并降低了代码清晰度。文件中返回约定的不一致使代码库更难维护，可能在未来重构时引入错误。

**修復建議：**
从 `StakingVault::_withdrawTo` 和 `redeemTo` 中移除冗余的显式 `return` 语句，只使用命名返回变量。

---

## 5. Remove obsolete return statements when using named returns — cyfrin/wlf.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
`WorldLibertyFinancialV2::getVotes` declares a named return variable `votingPower` and assigns to it throughout the function. At the end of the function body, a final explicit `return votingPower;` statement is present, which is redundant given the named return declaration. The redundant statement neither changes behavior nor adds clarity.

**Impact:**
The redundant `return` statement adds a small amount of unnecessary bytecode and can mislead developers about the return mechanism of the function. It is a minor code quality issue that increases maintenance overhead.

**Recommended Mitigation:**
Remove the final `return votingPower;` statement from `WorldLibertyFinancialV2::getVotes` and rely on the implicit named return.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialV2::getVotes` 声明了命名返回变量 `votingPower` 并在函数中赋值。在函数体末尾，存在最终的显式 `return votingPower;` 语句，鉴于命名返回声明的存在，这是冗余的。冗余语句既不改变行为，也不增加清晰度。

**影響：**
冗余的 `return` 语句增加了少量不必要的字节码，可能误导开发者对函数返回机制的理解。这是一个轻微的代码质量问题，增加了维护开销。

**修復建議：**
从 `WorldLibertyFinancialV2::getVotes` 中移除最终的 `return votingPower;` 语句，依靠隐式命名返回。

---

## 6. Remove obsolete final return statement when already using named returns — cyfrin/harbor.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/harbor.md`

**Description:**
`AgreementFactory::create` uses named return variables but also contains a final explicit `return` statement at the end of the function that redundantly restates the named return variable. Since named return variables are automatically returned at the end of function execution, the final explicit `return` statement serves no purpose and should be removed for consistency.

**Impact:**
The obsolete `return` statement adds minor bytecode overhead and creates an inconsistency in the return style of the codebase. It may confuse future contributors about whether the named return or the explicit return is the source of truth.

**Recommended Mitigation:**
Remove the final explicit `return` statement from `AgreementFactory::create` and use only the implicit named return.

---

**[中文版本]**

**描述：**
`AgreementFactory::create` 使用命名返回变量，但也在函数末尾包含一个显式的 `return` 语句，冗余地重述了命名返回变量。由于命名返回变量在函数执行结束时会自动返回，最终的显式 `return` 语句没有任何用途，应为保持一致性而删除。

**影響：**
过时的 `return` 语句增加了少量字节码开销，并在代码库的返回风格中造成不一致。可能使未来的贡献者对命名返回还是显式返回是真实来源产生困惑。

**修復建議：**
从 `AgreementFactory::create` 中移除最终的显式 `return` 语句，仅使用隐式命名返回。

---

## 7. Remove obsolete return statements when using named return variables — cyfrin/trade.md

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
Three functions in the Button Protocol vault contracts use named return variables but also contain explicit `return` statements. `BasisTradeVault::requestWithdraw` declares `returns (uint256 queuePosition)` as its named return but also ends with `return requestRedeem(shares);`. `BasisTradeVault::requestRedeem` declares `returns (uint256 queuePosition)` but also ends with `return queuePosition;`. `Pocket::exec` declares `returns (bytes memory result)` but also ends with an explicit `return result;`. In each case the explicit `return` is redundant given the named declaration.

**Impact:**
The redundant explicit return statements add minor bytecode size and code style inconsistency. They indicate a coding practice issue that can confuse readers and cause errors when functions are modified in the future.

**Recommended Mitigation:**
Remove the explicit `return` statements from `BasisTradeVault::requestWithdraw`, `BasisTradeVault::requestRedeem`, and `Pocket::exec`, relying on the implicit named return in each case.

---

**[中文版本]**

**描述：**
Button Protocol 金库合约中的三个函数使用命名返回变量，但也包含显式 `return` 语句。`BasisTradeVault::requestWithdraw` 声明 `returns (uint256 queuePosition)` 作为命名返回，但也以 `return requestRedeem(shares);` 结尾。`BasisTradeVault::requestRedeem` 声明 `returns (uint256 queuePosition)`，但也以 `return queuePosition;` 结尾。`Pocket::exec` 声明 `returns (bytes memory result)`，但也以显式 `return result;` 结尾。在每种情况下，鉴于命名声明的存在，显式 `return` 都是冗余的。

**影響：**
冗余的显式返回语句增加了少量字节码大小和代码风格不一致性。它们表明一种编码实践问题，可能使读者困惑，并在未来修改函数时导致错误。

**修復建議：**
从 `BasisTradeVault::requestWithdraw`、`BasisTradeVault::requestRedeem` 和 `Pocket::exec` 中移除显式 `return` 语句，在每种情况下依靠隐式命名返回。
