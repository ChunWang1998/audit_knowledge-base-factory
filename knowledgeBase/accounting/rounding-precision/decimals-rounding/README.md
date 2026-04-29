# decimals-rounding (17)

> Issues from incorrect decimal assumptions, rounding direction favouring wrong party, or overflow in decimal conversions.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Arithmetic underflow in `withdrawERC20` when there is a negative rebasing of asset tokens

**Severity:** 🟡 Medium  **Source:** `cyfrin/stbl.md`

**Description:**
The STBL vault tracks deposits using deposit-time pricing but calculates withdrawals using the current market price of the underlying collateral. The system assumes that collateral prices can only increase, since the underlying assets are yield-bearing instruments. However, if the underlying protocol (e.g., ONDO) is forced to sell bonds before maturity at a market price below purchase price, a negative rebase occurs. In `withdrawERC20`, the vault calls the asset oracle to compute `withdrawAssetValue` using the current inverse price. When the price has declined, the oracle returns a larger asset unit count for the same USD value — meaning more tokens must be discounted from `VaultData.assetDepositNet` than were originally deposited. The subsequent subtraction `VaultData.assetDepositNet -= (withdrawAssetValue + withdrawFeeAssetValue)` then underflows, causing the transaction to revert.

**Impact:**
Under a negative rebasing event, all user withdrawal attempts will revert due to arithmetic underflow, creating a denial-of-service on withdrawals. Early users may successfully withdraw before the accounting balance reaches zero, while later users are completely blocked from accessing their funds.

**Recommended Mitigation:**
Modify `withdrawERC20` to cap the total withdrawal against the available accounting balance. When `totalWithdrawal` exceeds `VaultData.assetDepositNet`, the available net should be consumed entirely and set to zero rather than allowing underflow. This prevents the revert while still allowing partial recovery during insolvency scenarios.

---

**[中文版本]**

**描述：**
STBL 金库以存款时的价格记录存款，但提款时使用当前市价的反价（inversPrice）计算要扣除的资产单位数量。系统假设抵押品价格只会上升，但当底层协议被迫提前出售债券并产生亏损时，会发生负向 rebase：预言机会返回比原始存款更大的资产单位数量。`withdrawERC20` 中将这一更大数量从 `VaultData.assetDepositNet` 中扣除时会发生下溢（underflow），导致交易回滚。

**影響：**
在负向 rebase 期间，所有提款都会因算术下溢而回滚，造成提款 DoS。先提款的用户可能可以成功提取，而后续用户则完全无法取回资金。

**修復建議：**
修改 `withdrawERC20`，当 `totalWithdrawal` 超过 `VaultData.assetDepositNet` 时，将可用余额直接归零而非产生下溢，允许金库在资不抵债时进行有限度的资金回收。

---

## 2. Consider implementing explicit rounding behaviour instead of default round down

**Severity:** 🟡 Medium  **Source:** `cyfrin/sherpa.md`

**Description:**
All functions in `ShareMath.sol` round down by default using integer division. For example, `ShareMath.pricePerShare` computes `(singleShare * (totalBalance - pendingAmount)) / totalSupply`, which silently truncates fractional results. While rounding down is appropriate in some contexts — such as minting shares to users, where the protocol should keep the remainder — it is harmful in others, such as computing share prices where underestimation propagates to all subsequent calculations. The codebase provides no explicit rounding direction and no inline comments explaining why rounding down is correct in each call site, which makes the code error-prone and hard to audit for future maintainers.

**Impact:**
The price per share is consistently underestimated, leading to a slow and continuous value leak. Over thousands of transactions, wei-level precision losses accumulate into material discrepancies between reported and actual share values. Depending on which direction the rounding error compounds, either depositors or the protocol suffer systematic losses.

**Recommended Mitigation:**
Add an explicit rounding direction parameter to all `ShareMath` functions following the OpenZeppelin `Math.Rounding` pattern. Each call site should pass the appropriate rounding direction and include a comment explaining why that direction is correct for that specific context, as is standard practice in modern ERC-4626 implementations.

---

**[中文版本]**

**描述：**
`ShareMath.sol` 中所有函数都默认采用整除（向下取整）。例如 `pricePerShare` 直接使用 `/ totalSupply`，不区分上下文。在某些场景中（如向用户发行份额）向下取整有利于协议，但在计算份额价格时则会导致持续低估。代码库中没有明确的舍入方向，也没有解释每个调用点为何采用该舍入方向的注释。

**影響：**
份额价格被持续低估，每笔交易都会产生 wei 级别的精度损失，随着交易量增加而积累成实质性差异。

**修復建議：**
参照 OpenZeppelin `Math.Rounding` 模式，为所有 `ShareMath` 函数添加明确的舍入方向参数，并在每个调用点注释说明该方向的合理性。

---

## 3. Consider reverting in `RebasingLibrary` functions if rounding down to zero occurs

**Severity:** 🟡 Medium  **Source:** `cyfrin/rebasing.md`

**Description:**
`RebasingLibrary` exposes two functions, `convertTokensToShares` and `convertSharesToTokens`, which perform fixed-point arithmetic to convert between token amounts and rebasing shares. Both functions can silently return zero when the input is a very small positive value and the rebasing multiplier causes the result to floor to zero. Continuing execution after a non-zero input produces a zero output is semantically incorrect: it means an operation that should be meaningful is treated as a no-op, which can corrupt accounting state downstream. For instance, issuing zero shares for a non-zero token deposit would credit the depositor nothing while still taking their tokens.

**Impact:**
If rounding down to zero occurs, token minting or burning operations proceed with zero output, meaning users can lose funds silently. The protocol's internal accounting can diverge from actual balances without any visible error.

**Recommended Mitigation:**
Add explicit zero-output guards to both functions: `convertTokensToShares` should revert if `_tokens > 0 && shares == 0`, and `convertSharesToTokens` should revert if `_shares > 0 && tokens == 0`. Note that the revert in `convertSharesToTokens` may need to be skipped for view-only paths such as `balanceOf`.

---

**[中文版本]**

**描述：**
`RebasingLibrary` 中的 `convertTokensToShares` 和 `convertSharesToTokens` 在输入非零但结果因定点数除法被取整为零时，会静默返回 0。这意味着用户可能为非零数量的代币获得零份额，或者以零代币兑换非零份额，导致资金无声损失。

**影響：**
代币发行或销毁操作在零输出情况下静默完成，用户可能损失资金，协议内部会计状态与实际余额产生偏差。

**修復建議：**
在两个函数中添加零输出断言：若输入非零而输出为零则回滚。注意在只读路径（如 `balanceOf`）中可跳过此检查。

---

## 4. Duplicated `Math` import should be removed from `ERC721WrapperBase`

**Severity:** 🟡 Medium  **Source:** `cyfrin/vii.md`

**Description:**
The OpenZeppelin `Math` library is imported twice in `ERC721WrapperBase`. Duplicate imports do not cause compilation failure in Solidity but represent dead code that increases the risk of confusion during maintenance, audits, and tooling analysis. When two import paths for the same library exist, developers may add logic referencing one import while a different instance exists in scope, creating subtle aliasing risks in complex inheritance chains. The duplication also signals that the import history was not carefully managed, which may indicate other housekeeping issues.

**Impact:**
No direct exploit risk, but the redundant import adds noise to the codebase, may confuse static analysis tools, and increases maintenance overhead. Over time, such code hygiene issues can mask real problems during security reviews.

**Recommended Mitigation:**
Remove one of the two duplicate `Math` library import statements from `ERC721WrapperBase` so that only a single canonical import remains.

---

**[中文版本]**

**描述：**
`ERC721WrapperBase` 中 OpenZeppelin `Math` 库被导入了两次。重复导入虽不影响编译，但会增加维护混乱风险：开发者可能引用错误的别名，静态分析工具也可能产生误报。

**影響：**
无直接利用风险，但增加维护成本，可能在安全审查中掩盖真实问题。

**修復建議：**
删除 `ERC721WrapperBase` 中重复的 `Math` 库导入语句，只保留一个规范导入。

---

## 5. Enforce that `StakingVault::decimals` is greater or equal to the underlying asset decimals

**Severity:** 🟡 Medium  **Source:** `cyfrin/syntetika.md`

**Description:**
EIP-4626 strongly recommends that a vault's share token decimals be greater than or equal to the underlying asset's decimals to avoid precision loss in share-to-asset conversions. Standard property tests from Crytic's ERC-4626 test suite enforce this invariant explicitly. `StakingVault` does not validate this in its constructor, meaning a vault could be deployed with a decimal value lower than its underlying asset, causing the `convertToShares` and `convertToAssets` functions to silently truncate precision in all subsequent calculations. This violates both the EIP-4626 specification and common security practice.

**Impact:**
If `StakingVault::decimals` is smaller than the underlying asset's decimals, share-to-asset conversions permanently lose precision, causing depositors to receive fewer shares than they should or withdraw fewer assets than entitled. The error compounds over multiple operations.

**Recommended Mitigation:**
In `StakingVault::constructor`, add a validation check that reverts if `IERC20Metadata(_asset).decimals() > decimals()`, enforcing that vault shares always have at least as many decimal places as the underlying asset.

---

**[中文版本]**

**描述：**
EIP-4626 强烈建议金库份额代币的精度（decimals）应大于等于底层资产的精度，以避免份额与资产换算时的精度损失。`StakingVault` 构造函数中未对此进行验证，可能部署出精度低于底层资产的金库，导致所有换算操作静默截断精度。

**影響：**
若金库精度小于底层资产精度，存款人获得的份额或提款时取回的资产会系统性偏少，误差随操作次数积累。

**修復建議：**
在 `StakingVault` 构造函数中添加检查，若 `IERC20Metadata(_asset).decimals() > decimals()` 则回滚部署。

---

## 6. Flawed Rounding Logic in `calculateBuyAmount` Leads to Loss of Funds

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
The `calculateBuyAmount` function in `BondingCurveLibrary` is designed to compute how many tokens a user can purchase for a given cost. Internally it calls `_inverseArea0`, which after correctly computing the fractional token amount in wei applies a "smart rounding" step that rounds to the nearest whole token. When the computed amount falls below 0.5 tokens (i.e., a sub-half-token purchase), the logic rounds down to zero. Because the calling `buy()` or `buyPublic()` function has already accepted the user's payment before calling `calculateBuyAmount`, a user who pays for between 0 and 0.5 tokens receives zero tokens but loses their entire payment. The comment in the code incorrectly describes this as rounding to the "nearest wei" when it actually rounds to the nearest full token.

**Impact:**
Any transaction where a user intends to purchase a fractional amount less than 0.5 tokens results in a total and irreversible loss of the user's payment. The user pays a real cost but receives zero tokens, effectively constituting theft.

**Recommended Mitigation:**
Remove the rounding logic from `_inverseArea0` entirely. The underlying fixed-point math library already provides sufficient precision to return an accurate fractional token amount. Eliminating the artificial rounding step resolves the dead-zone exploit without any precision loss.

---

**[中文版本]**

**描述：**
`BondingCurveLibrary` 中的 `calculateBuyAmount` 通过 `_inverseArea0` 计算购买数量后，应用了"智能取整"逻辑：将计算出的代币量四舍五入到最近的整数代币。当结果不足 0.5 个代币时，四舍五入为 0。由于合约在调用计算函数前已接受用户付款，付款金额对应不足半个代币的用户将得到零代币但损失全部付款。

**影響：**
购买不足 0.5 个代币的用户完全损失付款，实质等同于资金被窃取。

**修復建議：**
完全移除 `_inverseArea0` 中的取整逻辑。底层定点数学库已提供足够精度返回精确的小数代币量。

---

## 7. Inaccurate stake calculation due to decimal mismatch across multitoken asset classes

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::getOperatorStake` iterates over all vaults associated with a given asset class and sums their staked amounts directly. However, an asset class can contain multiple collateral tokens with different decimal precisions — for example, USDC (6 decimals) alongside DAI (18 decimals). The summation logic adds raw token amounts without normalizing to a common decimal base. As a result, 10,000 USDC (represented as `10,000 * 10^6 = 10^10`) adds negligibly to the total when compared with even a small amount of DAI (e.g., 10 DAI = `10 * 10^18`). The USDC stake is effectively invisible in the calculation.

**Impact:**
Tokens with fewer decimals are severely underrepresented or entirely ignored in stake calculations. This breaks operator stake reporting, reward distribution, slashing proportions, and any governance or security threshold derived from stake amounts.

**Recommended Mitigation:**
Before summing vault stakes in `getOperatorStake`, normalize each vault's raw stake amount to a common 18-decimal base using the vault token's `decimals()` value. Multiply by `10^(18 - decimals)` for tokens with fewer than 18 decimals, and divide by `10^(decimals - 18)` for tokens with more.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware::getOperatorStake` 在汇总资产类别中各金库的质押量时，直接将不同精度代币的原始数量相加。例如 USDC（6位精度）的质押量与 DAI（18位精度）相加时，USDC 的数值量级远小于 DAI，实际上被忽略。

**影響：**
精度较低的代币在质押计算中严重被低估或完全忽略，破坏质押报告、奖励分配和基于质押量的安全阈值。

**修復建議：**
在 `getOperatorStake` 汇总前，通过代币的 `decimals()` 将各金库质押量归一化为 18 位精度。

---

## 8. Incorrect Assumption of USDT Decimals Leads to Fee Miscalculations

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The `Subscription` contract hardcodes fee constants using 18-decimal units — for example, `uint256 public constant MAX_FEE = 3 * 1e18` and `defaultFee = 1e18` — with comments indicating these represent 3 USDT and 1 USDT respectively. In reality, USDT uses 6 decimals on-chain, so 1 USDT is `1e6`, not `1e18`. The protocol-wide assumption that USDT equals `1e18` means all fee-related logic — registration, subscription renewal, level access, and custom fee configuration — operates with values 10^12 times larger than intended. Users would need to approve and transfer impossibly large USDT amounts to interact with the protocol.

**Impact:**
All fee-gated operations become practically inaccessible. Users cannot register, subscribe, or renew subscriptions because the required approvals and token transfers are infeasibly large. The protocol is completely non-functional with real USDT from deployment, not just in edge cases.

**Recommended Mitigation:**
Replace all fee constants that assume 18 decimals with 6-decimal equivalents: change `MAX_FEE = 3 * 1e18` to `MAX_FEE = 3 * 1e6`, and similarly adjust `defaultFee` and all other USDT-denominated constants. Additionally, consider fetching the token's decimals dynamically via `IERC20Metadata.decimals()` to prevent recurrence if the accepted token changes.

---

**[中文版本]**

**描述：**
`Subscription` 合约将 USDT 费用常量硬编码为 18 位精度（如 `MAX_FEE = 3 * 1e18`），但 USDT 实际上使用 6 位精度（1 USDT = 1e6）。这导致所有费用相关逻辑的计算值比预期高出 10^12 倍，用户需要批准和转移天文数字级别的 USDT 才能与协议交互。

**影響：**
注册、续订和级别访问等所有收费操作实际上无法进行，协议从部署之日起即无法正常运行。

**修復建議：**
将所有费用常量从 `1e18` 精度改为 `1e6` 精度，并考虑通过 `IERC20Metadata.decimals()` 动态获取代币精度。

---

## 9. `LibHelpers.convertDecimalsTo` favours the user on an exact-out mint and burn for certain collateral decimals

**Severity:** 🟡 Medium  **Source:** `cyfrin/parallel3.1.md`

**Description:**
`LibHelpers.convertDecimalsTo` always rounds down when converting amounts from higher to lower decimal precision, regardless of the calling context. In `Swapper::swap` on the exact-out mint path (`_quoteMintExactOutput`), collateral input amounts are converted from 18 decimals down to the collateral's native decimals. Rounding down here means the user is charged slightly less collateral than mathematically required for the minted output — giving the user a small discount at the protocol's expense. Similarly, on the exact-out burn path (`_quoteBurnExactOutput`), collateral with decimals higher than 18 also benefits from rounding in the user's favor. The issue violates the principle that rounding should always favor the protocol.

**Impact:**
While individually negligible, the rounding error grants every user on the affected mint and burn paths a small discount. Over large volumes this constitutes value leakage from the protocol to users. Future feature additions that build on this conversion function may amplify the exploitability.

**Recommended Mitigation:**
Add a rounding direction parameter to `convertDecimalsTo` and update all call sites to pass the appropriate direction. Callers on the exact-out mint and burn paths should round up (in favor of the protocol) when charging collateral from users.

---

**[中文版本]**

**描述：**
`LibHelpers.convertDecimalsTo` 在将金额从高精度转换为低精度时始终向下取整，不区分调用上下文。在精确输出铸造路径中，向下取整意味着协议收取的抵押品略少于数学上所需，给予用户小额折扣，损害协议利益。精确输出销毁路径中高精度抵押品同样存在此问题。

**影響：**
每笔涉及该转换的铸造和销毁操作都给用户少量折扣，大量交易后积累为协议的实质性价值损失。

**修復建議：**
为 `convertDecimalsTo` 添加舍入方向参数，精确输出铸造和销毁路径上应采用向上取整（有利于协议）。

---

## 10. Multiplication could overflow in `RebasingLibrary` for tokens with greater than 18 decimals

**Severity:** 🟡 Medium  **Source:** `cyfrin/rebasing.md`

**Description:**
`RebasingLibrary` includes special handling for tokens with more than 18 decimals. In the `convertTokensToShares` path for such tokens, the computation `_shares * _rebasingMultiplier * scale` is performed inline where `scale = 10^(_tokenDecimals - 18)`. When `_tokenDecimals` is significantly above 18 and both `_shares` and `_rebasingMultiplier` are large, the product of three large uint256 values can exceed the maximum uint256 value and silently wrap to a small number. In Solidity 0.8+ this is a revert rather than a silent overflow, but the effect is a denial of service on all operations using tokens with high decimal values.

**Impact:**
Any vault or protocol using tokens with more than 18 decimals will experience denial-of-service failures in token conversion operations whenever the product of the three values overflows uint256.

**Recommended Mitigation:**
Replace the raw multiplication with OpenZeppelin's `Math.mulDiv`, which performs overflow-safe multiplication-division. The suggested fix restructures the intermediate computation to avoid the triple product: for example, `Math.mulDiv(_shares * scale, _rebasingMultiplier, DECIMALS_FACTOR)`.

---

**[中文版本]**

**描述：**
`RebasingLibrary` 对超过 18 位精度的代币有特殊处理逻辑，其中 `_shares * _rebasingMultiplier * scale` 三数连乘可能导致 uint256 溢出。在 Solidity 0.8+ 中溢出会回滚，造成使用高精度代币的所有转换操作 DoS。

**影響：**
使用超过 18 位精度代币的协议，在代币转换操作中会遭遇 DoS 故障。

**修復建議：**
使用 OpenZeppelin 的 `Math.mulDiv` 替代内联三数乘法，避免中间乘法溢出。

---

## 11. Potential underflow in slashing logic

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
`VaultTokenized::onSlash` implements a cascading slashing mechanism: when the amount to be slashed from current-epoch withdrawals (`withdrawalsSlashed`) exceeds available withdrawals (`withdrawals_`), the excess is added to `nextWithdrawalsSlashed` for the following epoch. Due to integer division rounding in the proportional distribution calculation, `withdrawalsSlashed` can exceed `withdrawals_` in normal operation. The cascaded excess is then added to `nextWithdrawalsSlashed`, but if `nextWithdrawals` is zero or smaller than `nextWithdrawalsSlashed`, the operation `nextWithdrawals - nextWithdrawalsSlashed` underflows and reverts. This happens when future withdrawals are minimal and slashing amounts are close to total stake.

**Impact:**
The slashing transaction reverts, preventing any slashing from occurring in affected scenarios. A malicious actor can engineer the conditions (e.g., minimal pending withdrawals in future epochs) to block their own position from being slashed.

**Recommended Mitigation:**
Add an explicit guard before the subtraction: check whether `nextWithdrawalsSlashed > nextWithdrawals` and if so, cap `nextWithdrawalsSlashed` to `nextWithdrawals` and carry the remaining excess forward or set it to zero. This prevents underflow while ensuring the slashing logic remains consistent.

---

**[中文版本]**

**描述：**
`VaultTokenized::onSlash` 中的级联惩没逻辑在将超额惩没量级联至下一纪元时，若 `nextWithdrawals` 为零或小于 `nextWithdrawalsSlashed`，减法操作会下溢导致回滚。在整数除法取整和质押量接近总额时，这种情况可以在正常操作中自然发生。

**影響：**
惩没交易回滚，导致受影响场景下的惩没完全无法执行。恶意行为者可通过制造条件（如最小化未来纪元提款）来阻止自己的仓位被惩没。

**修復建議：**
在减法前添加显式保护：若 `nextWithdrawalsSlashed > nextWithdrawals`，将其上限设为 `nextWithdrawals`，并将剩余超额归零或向前级联处理。

---

## 12. Redundant overflow checks in safe arithmetic operations

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
In `UptimeTracker::computeValidatorUptime`, loop increments (`i++`) and additions (`lastUptimeEpoch + i`) are wrapped in standard Solidity 0.8+ arithmetic that includes automatic overflow checks. Because the loop counter is typed as `uint48` with controlled bounds, and `lastUptimeEpoch` values are protocol-managed and guaranteed within safe ranges, these operations can never actually overflow. The automatic overflow checks therefore consume approximately 20–30 unnecessary gas per operation inside a potentially unbounded loop, making epoch processing more expensive than necessary.

**Impact:**
Gas inefficiency: every epoch processing call pays unnecessary overhead. For protocols with large numbers of validators processed per epoch, this compounds into significant wasted gas over the contract's lifetime.

**Recommended Mitigation:**
Wrap the loop increment and the epoch index calculation in `unchecked` blocks to bypass the redundant overflow checks, reducing gas consumption without any safety risk given the proven bounds on the operands.

---

**[中文版本]**

**描述：**
`UptimeTracker::computeValidatorUptime` 中的循环计数器和纪元加法使用了 Solidity 0.8+ 的自动溢出检查。由于操作数类型为 `uint48` 且由协议控制，实际不可能溢出，这些检查是多余的，每次操作浪费约 20-30 gas。

**影響：**
Gas 效率低下，对于处理大量验证者的协议，长期累积成显著的 gas 浪费。

**修復建議：**
将循环自增和纪元索引计算放入 `unchecked` 块中，消除多余的溢出检查。

---

## 13. Remove `decimals` from initial `RemoraToken` mint

**Severity:** 🟡 Medium  **Source:** `cyfrin/pledge.md`

**Description:**
`RemoraToken` overrides `decimals()` to return `0` because RWA tokens are non-fractional and operate in whole units only. However, `RemoraToken::initialize` mints the initial supply as `_initialSupply * 10 ** decimals()`. Since `decimals()` always returns `0`, the expression `10 ** 0 = 1`, meaning the multiplication is always `_initialSupply * 1`. This is mathematically a no-op, but is semantically confusing: readers may incorrectly assume the multiplication scales by a non-trivial factor when processing the initial supply. The redundant scaling expression can also mislead future maintainers into thinking decimals scaling is necessary or meaningful here.

**Impact:**
No direct financial impact since the multiplication by 1 is a no-op. However, the confusing code pattern creates maintenance risk: future changes to the `decimals()` function or a misreading of the initialization logic could inadvertently introduce a scaling error in a fork or upgrade.

**Recommended Mitigation:**
Remove the `10 ** decimals()` multiplication from `RemoraToken::initialize` and mint `_initialSupply` directly, since `decimals()` is always `0` and the factor always evaluates to 1.

---

**[中文版本]**

**描述：**
`RemoraToken::initialize` 在铸造初始供应量时使用 `_initialSupply * 10 ** decimals()`，而 `decimals()` 始终返回 `0`，因此 `10 ** 0 = 1`，该乘法是多余的无操作。此冗余表达式具有误导性，可能使维护者误认为精度缩放在此处有实际意义。

**影響：**
无直接财务影响，但存在维护风险：若 `decimals()` 在分叉或升级中被修改，此处的缩放逻辑可能产生意外的铸造放大效果。

**修復建議：**
将 `_mint(tokenOwner, _initialSupply * 10 ** decimals())` 改为 `_mint(tokenOwner, _initialSupply)`。

---

## 14. Rounding in favor of the violator can subject liquidators to losses during partial liquidation

**Severity:** 🟡 Medium  **Source:** `cyfrin/vii.md`

**Description:**
`ERC721WrapperBase::transfer` uses `Math.mulDiv` to compute the proportional number of ERC-6909 tokens to transfer from the sender (violator) to the liquidator. The formula `Math.mulDiv(amount, totalSupply(tokenId), currentBalance)` performs floor rounding, meaning the calculation always rounds in favor of the sender (the violator). In a partial liquidation, this means the liquidator receives slightly fewer ERC-6909 tokens than the economic proportionality dictates. A malicious violator can exploit this by reducing their ERC-6909 balance to 1 wei — by unwrapping almost their entire position — and then allowing fees to accrue to inflate the value of that 1 wei. Subsequent partial liquidations transfer zero ERC-6909 tokens to the liquidator due to floor rounding, forcing liquidators to either accept zero recovery or attempt expensive full liquidations.

**Impact:**
Liquidators can suffer direct losses during partial liquidations when the violator's ERC-6909 token supply is reduced to small values. This can discourage liquidators from acting, allowing undercollateralized positions to persist and bad debt to accrue in the vault.

**Recommended Mitigation:**
Change `normalizedToFull` to use ceiling rounding (`Math.Rounding.Ceil`) when computing the number of ERC-6909 tokens to transfer to the liquidator, ensuring that any rounding favors the liquidator rather than the violator.

---

**[中文版本]**

**描述：**
`ERC721WrapperBase::transfer` 使用 `Math.mulDiv`（向下取整）计算清算转移给清算人的 ERC-6909 代币数量，取整始终有利于发送方（违规者）。恶意违规者可将自己的 ERC-6909 余额降至 1 wei，然后通过费用积累放大其价值，导致后续部分清算中向清算人转移的代币为零。

**影響：**
清算人在部分清算中可能遭受直接损失，清算激励减弱，导致抵押不足仓位持续存在，金库积累坏账。

**修復建議：**
将 `normalizedToFull` 中的 `Math.mulDiv` 改为使用向上取整（`Math.Rounding.Ceil`），确保舍入有利于清算人。

---

## 15. `Tranche::maxMint` for Junior Tranches is at risk of overflow when the `jrNav` falls below `1:1` rate to `JR_Shares`

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
In a two-tranche system (Senior and Junior), the Junior Tranche can cover Senior losses or fund Senior's target APR when actual returns fall short. Both events decrease the Junior Tranche NAV (`jrtNav`). When `jrtNav` falls below the 1:1 share-to-asset rate, `Tranche::maxMint` attempts to convert `type(uint256).max` assets to shares via `convertToShares`. The conversion formula divides by `totalAssets()` which at this point is smaller than `totalSupply()`, causing the share calculation to produce a value that overflows uint256 when multiplied by the initial `type(uint256).max` input.

**Impact:**
Any call to `Tranche::maxMint` or `Tranche::mint` reverts with overflow when the Junior Tranche NAV drops below 1:1. This denies Junior Tranche users the ability to mint new shares and blocks integrating protocols that rely on `maxMint` for liquidity checks.

**Recommended Mitigation:**
In `Tranche::maxMint`, check whether `cdo.maxDeposit(address(this))` returns `type(uint256).max` and if so, return `type(uint256).max` directly without performing the `convertToShares` conversion, since unlimited deposits imply unlimited minting.

---

**[中文版本]**

**描述：**
当 Junior Tranche 的 `jrtNav` 下降至低于 1:1 份额-资产比率时，`Tranche::maxMint` 尝试将 `type(uint256).max` 资产转换为份额。由于此时 `totalAssets() < totalSupply()`，份额计算结果溢出 uint256，导致交易回滚。

**影響：**
Junior Tranche NAV 低于 1:1 时，所有 `maxMint` 和 `mint` 调用都会因溢出而回滚，阻止用户存款并阻塞依赖 `maxMint` 的集成协议。

**修復建議：**
在 `Tranche::maxMint` 中，若 `cdo.maxDeposit` 返回 `type(uint256).max`，则直接返回 `type(uint256).max`，跳过 `convertToShares` 转换。

---

## 16. Value leakage due to pUSDe redemptions rounding against the protocol/yUSDe depositors

**Severity:** 🟡 Medium  **Source:** `cyfrin/predeposit.md`

**Description:**
After entering the yield phase, `pUSDeVault::_withdraw` computes the sUSDe balance required to cover a redemption by calling `sUSDe.previewWithdraw(assets)`. Per ERC-4626 spec, `previewWithdraw` rounds up to ensure the protocol retains enough sUSDe to fulfill the withdrawal. However, in this implementation the rounded-up sUSDe value is then transferred directly to the receiver rather than used as an internal input for the actual sUSDe redemption. This means the extra sUSDe created by the rounding-up goes to the user rather than staying in the protocol, causing the redemption to round in the user's favor and against the remaining yUSDe depositors.

**Impact:**
Every pUSDe redemption transfers slightly more sUSDe to the redeeming user than mathematically warranted. Over many redemptions, value is continuously leaked from the protocol's sUSDe pool, reducing the returns available to remaining yUSDe depositors.

**Recommended Mitigation:**
Replace the call to `previewWithdraw` (which rounds up) with `convertToShares` (which rounds down) when computing the sUSDe amount to transfer out. `previewWithdraw` is appropriate for determining how much sUSDe must be burned to receive a given USDe amount, but `convertToShares` should be used when computing how much sUSDe to transfer to the user.

---

**[中文版本]**

**描述：**
`pUSDeVault::_withdraw` 通过 `sUSDe.previewWithdraw(assets)` 计算需要转出的 sUSDe 数量。`previewWithdraw` 按 ERC-4626 规范向上取整（以确保协议有足够 sUSDe 支付赎回），但此处将向上取整后的值直接转给接收者，导致赎回方向有利于用户而非协议/yUSDe 存款人。

**影響：**
每笔 pUSDe 赎回都将略多于数学上应有的 sUSDe 转给用户，随着赎回次数增加持续从 sUSDe 池中漏出价值，损害剩余 yUSDe 存款人收益。

**修復建議：**
将 `previewWithdraw`（向上取整）替换为 `convertToShares`（向下取整）来计算转出给用户的 sUSDe 数量，使舍入方向有利于协议。

---

## 17. `YtokenL2::previewMint` and `YTokenL2::previewWithdraw` round in favor of user

**Severity:** 🟡 Medium  **Source:** `cyfrin/yieldfi.md`

**Description:**
For L2 `YToken` contracts, the vault exchange rate is provided by an off-chain oracle rather than local accounting. Custom implementations of `previewMint` and `previewWithdraw` rely on this oracle rate. `previewMint` computes shares from an asset amount using `(grossShares * exchangeRate()) / Constants.PINT`, and `previewWithdraw` computes shares needed for assets using `(assets * Constants.PINT) / exchangeRate()`. Both computations use plain integer division which rounds toward zero — i.e., in favor of the user. EIP-4626 security considerations explicitly state that these functions should round against the caller: `previewMint` should round up (user pays more) and `previewWithdraw` should round up (user burns more shares).

**Impact:**
Users receive slightly more favorable terms than the vault's accounting warrants on every mint and withdrawal operation. Although the two-step withdrawal flow limits immediate exploitation, the consistent rounding bias causes a slow, continuous value leak from the vault, especially under high transaction volume or automation.

**Recommended Mitigation:**
Update `previewMint` and `previewWithdraw` to round in favor of the vault using the modified `_convertToShares` and `_convertToAssets` internal functions with an explicit `Math.Rounding.Ceil` direction, following the OpenZeppelin ERC-4626 reference implementation.

---

**[中文版本]**

**描述：**
L2 `YToken` 合约中 `previewMint` 和 `previewWithdraw` 的自定义实现使用整除（向零取整），取整方向有利于用户。EIP-4626 安全建议明确规定这两个函数应向上取整（有利于金库），以防止价值漏损。

**影響：**
每笔铸造和提款操作都给用户略微有利的条件，在高交易量或自动化场景下积累为持续的价值泄漏。

**修復建議：**
更新 `previewMint` 和 `previewWithdraw`，使用 `Math.Rounding.Ceil` 方向，确保取整有利于金库，参照 OpenZeppelin ERC-4626 参考实现。
