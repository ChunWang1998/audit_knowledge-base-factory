# redeem-function (11)

> Issues in redeem/withdraw function implementations — incorrect super calls, missing checks, or ERC-4626 violations.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. All swaps other than the top-of-block swap will revert

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
In `AngstromL2::afterSwap`, `_getSwapTaxAmount` is called unconditionally for every swap, returning a non-zero `taxInEther` regardless of whether the swap is the top-of-block swap. This non-zero value is then passed to `_computeAndCollectProtocolSwapFee`, which creates a currency debt. The function then short-circuits when it detects the swap is not top-of-block (by checking `taxInEther == 0 || blockNumber == _blockOfLastTopOfBlock`), but it does so too late — after the debt has already been created. The returned `hookDeltaUnspecified` carries the erroneous debt value, causing all non-top-of-block swaps to fail with `CurrencyNotSettled` as the hook delta cannot be resolved.

**Impact:**
Only one top-of-block swap can be executed per block; all subsequent swaps within the same block will revert. This effectively breaks the protocol for any block where more than one swap is attempted.

**Recommended Mitigation:**
Ensure that a zero `taxInEther` is passed to `_computeAndCollectProtocolSwapFee` when the given swap is not a top-of-block swap, preventing the currency debt from being created for non-qualifying swaps.

---

**[中文版本]**

**描述：**
在 `AngstromL2::afterSwap` 中，`_getSwapTaxAmount` 无论是否为区块顶部交换均被无条件调用，返回非零的 `taxInEther`。该值随即传入 `_computeAndCollectProtocolSwapFee`，产生货币债务。函数在检测到非区块顶部交换后才短路返回，但为时已晚——债务已经创建。返回的 `hookDeltaUnspecified` 携带错误的债务值，导致所有非区块顶部交换因 `CurrencyNotSettled` 而失败。

**影響：**
每个区块只有一笔区块顶部交换可以执行，同一区块内所有后续交换均会回滚，实际上使得任何尝试多笔交换的区块的协议功能失效。

**修復建議：**
当交换不是区块顶部交换时，确保向 `_computeAndCollectProtocolSwapFee` 传入零值 `taxInEther`，防止为不符合条件的交换创建货币债务。

---

## 2. DoS of meta vault withdrawals during points phase if one vault is paused or attempted redemption exceeds the maximum

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeVault::_withdraw` assumes any USDe shortfall is covered by the multi-vaults, but `redeemRequiredBaseAssets` does not guarantee that the required assets are available or actually withdrawn. The function uses `ERC4626Upgradeable::previewRedeem` to determine how many shares to redeem from external vaults, but per ERC-4626 specification, `previewRedeem` must not account for redemption limits such as those returned from `maxRedeem` and should act as though the redemption would be accepted regardless. If one of the supported meta vaults is paused or has a custom limit that causes `previewRedeem` to return a value exceeding what is actually withdrawable, the subsequent ERC-20 token transfer will fail. The withdrawal is then DoSed even if it would have been possible to process by redeeming from another non-paused vault.

**Impact:**
If any supported meta vault is paused or experiences a hack that decreases its share price or limits withdrawals during the points phase, all withdrawals from the meta vault are blocked even if other unaffected vaults could supply the required USDe.

**Recommended Mitigation:**
Use `maxWithdraw` instead of `previewRedeem` in `redeemRequiredBaseAssets` to respect vault-specific limits and pause states when determining how many assets can actually be withdrawn from each vault.

---

**[中文版本]**

**描述：**
`pUSDeVault::_withdraw` 假定任何 USDe 缺口均由多金库覆盖，但 `redeemRequiredBaseAssets` 并不保证所需资产可用或已实际提取。该函数使用 `ERC4626Upgradeable::previewRedeem` 确定从外部金库赎回多少份额，但按 ERC-4626 规范，`previewRedeem` 不得考虑 `maxRedeem` 等赎回限制，应无条件视赎回请求为可接受。若某支持金库被暂停或其自定义限制导致 `previewRedeem` 返回值超过实际可提取量，后续 ERC-20 代币转账将失败，即使其他金库可以提供所需 USDe，提款也会被 DoS。

**影響：**
若任何受支持的元金库在积分阶段被暂停或遭遇黑客攻击（导致份额价格下降或提款受限），所有元金库的提款将被阻断，即使其他正常金库可以提供所需 USDe。

**修復建議：**
在 `redeemRequiredBaseAssets` 中使用 `maxWithdraw` 而非 `previewRedeem`，以考虑各金库特定的限制和暂停状态，准确确定实际可提取的资产数量。

---

## 3. Frontrunning to Block Junior Tranche Withdrawals

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
In `Accounting.sol`, the junior tranche's `maxWithdraw` is capped to ensure the post-withdrawal Junior NAV (`jrtNav`) remains at least `srtNav * minimumJrtSrtRatio / 1e18`. An attacker can front-run a victim's junior withdrawal transaction by depositing a calculated amount into the senior tranche, which inflates `srtNav` through the `updateBalanceFlow` call during deposit. This raises the `minJrt` threshold, causing the victim's withdrawal to fail the `maxWithdraw` check and revert with `ERC4626ExceededMaxWithdraw`. The attacker does not need to deposit a very large amount — only enough to push the `maxWithdraw` for the victim's requested amount to zero.

**Impact:**
Victims' legitimate junior tranche withdrawals are blocked and their liquidity is trapped. The attacker can repeatedly apply this pattern to indefinitely prevent any junior tranche withdrawal from completing.

**Recommended Mitigation:**
Implement a soft limit for SR Tranche deposits to prevent new deposits from pushing the system to the minimum JRT-SRT ratio boundary. This removes the attacker's ability to artificially inflate `srtNav` through deposits immediately before victim transactions.

---

**[中文版本]**

**描述：**
在 `Accounting.sol` 中，初级份额的 `maxWithdraw` 被限制以确保提款后 JRT NAV（`jrtNav`）不低于 `srtNav * minimumJrtSrtRatio / 1e18`。攻击者可以通过向高级份额存入计算好的金额来抢先受害者的初级提款交易——存款过程中的 `updateBalanceFlow` 调用会膨胀 `srtNav`，提高 `minJrt` 阈值，导致受害者的提款在 `maxWithdraw` 检查中失败并以 `ERC4626ExceededMaxWithdraw` 回滚。攻击者只需存入足够将受害者请求金额对应的 `maxWithdraw` 推至零的金额即可。

**影響：**
受害者的合法初级份额提款被阻断，流动性被困。攻击者可以反复使用此模式，无限期阻止任何初级份额提款完成。

**修復建議：**
为 SR Tranche 存款实施软限制，防止新存款将系统推至最低 JRT-SRT 比率边界，消除攻击者在受害者交易前通过存款人为膨胀 `srtNav` 的能力。

---

## 4. Function execute overwrites seenSigner values irrespective of request age

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
The `publish` function allows authenticated signers to publish multiple requests in a single batch, each with its own distinct timestamp. When `execute` processes the batch and encounters multiple requests from the same signer, it updates the signer's value entry to the latest-encountered request's value regardless of timestamp order. If a signer's earlier request has a higher timestamp (i.e., was published more recently) than a later-encountered request, the execute function overwrites the fresher value with the stale one. This means the deduplication logic uses the older value rather than the most recently published one, leading to slightly inaccurate rates being published.

**Impact:**
When a signer has multiple requests in the same batch and they arrive in reverse timestamp order, the execute function uses a stale value instead of the most recent one. This can result in inaccurate rate publications that deviate from the signer's actual latest intent.

**Recommended Mitigation:**
In the deduplication loop, only overwrite the stored signer value if the incoming request's timestamp is strictly newer than the currently stored value's timestamp. This ensures the most recent submission is always used.

---

**[中文版本]**

**描述：**
`publish` 函数允许已认证的签名者在单个批次中发布多个请求，每个请求都有独立的时间戳。当 `execute` 处理批次并遇到同一签名者的多个请求时，无论时间戳顺序如何，它都会用最新遇到的请求值更新签名者的值条目。若签名者的较早请求的时间戳较新（即更近发布），而较晚遇到的请求时间戳较旧，execute 函数会用旧值覆盖新值，导致去重逻辑使用过时的值而非最新发布的值。

**影響：**
当签名者在同一批次中拥有多个请求且以逆时间戳顺序到达时，execute 函数使用过时值而非最新值，可能导致发布的利率偏离签名者的实际最新意图。

**修復建議：**
在去重循环中，仅当传入请求的时间戳严格新于当前存储值的时间戳时才覆盖存储值，确保始终使用最新提交的值。

---

## 5. MetaVault::redeem erroneously calls ERC4626Upgradeable::withdraw when attempting to redeem USDe from pUSDeVault

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`MetaVault::deposit`, `MetaVault::mint`, and `MetaVault::withdraw` all correctly invoke the corresponding `IERC4626` function on the underlying vault. However, `MetaVault::redeem` contains a bug where, when the token is the native asset (USDe), it calls `withdraw(shares, receiver, owner)` instead of `redeem(shares, receiver, owner)`. This causes the function to treat the `shares` parameter as an `assets` parameter, resulting in entirely different semantics: withdraw redeems an asset-denominated quantity while redeem should burn a share-denominated quantity. The two functions produce different outputs and burn different amounts of shares.

**Impact:**
When `MetaVault::redeem` is called with USDe as the token, users receive fewer assets than expected because the function is treating their share count as an asset amount and running the withdrawal path instead of the correct redeem path. This violates the ERC-4626 contract and leads to systematic under-payment to users who redeem using this path.

**Recommended Mitigation:**
Replace the `withdraw(shares, receiver, owner)` call inside `MetaVault::redeem` with `redeem(shares, receiver, owner)` to ensure the correct ERC-4626 function is called when processing USDe redemptions.

---

**[中文版本]**

**描述：**
`MetaVault::deposit`、`MetaVault::mint` 和 `MetaVault::withdraw` 均正确调用底层金库对应的 `IERC4626` 函数。但 `MetaVault::redeem` 存在一个 bug：当代币为原生资产（USDe）时，它调用 `withdraw(shares, receiver, owner)` 而非 `redeem(shares, receiver, owner)`，将 `shares` 参数当作 `assets` 参数处理，导致语义完全不同——withdraw 按资产数量赎回，而 redeem 应按份额数量销毁。两个函数产生不同的输出并销毁不同数量的份额。

**影響：**
当 `MetaVault::redeem` 以 USDe 为代币被调用时，用户收到的资产少于预期，因为函数将用户的份额数量视为资产数量，走了提款路径而非正确的赎回路径。这违反了 ERC-4626 规范，导致通过此路径赎回的用户系统性地少收资产。

**修復建議：**
将 `MetaVault::redeem` 内的 `withdraw(shares, receiver, owner)` 调用替换为 `redeem(shares, receiver, owner)`，确保处理 USDe 赎回时调用正确的 ERC-4626 函数。

---

## 6. Missing redeem convenience function in the StakingVault.sol

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`StakingVault.sol` implements several convenience functions for common operations: `stake(uint256 assets)` as a shorthand for `deposit(assets, msg.sender)`, `unstake(uint256 assets)` for `withdraw(assets, msg.sender, msg.sender)`, and `mint(uint256 shares)` for `mint(shares, msg.sender)`. However, there is no corresponding convenience function for `redeem`, forcing users who want to redeem shares to manually specify all three parameters. This creates an inconsistency in the contract's API surface and makes the redeem operation less user-friendly compared to the other vault operations.

**Impact:**
Users must specify all three parameters when calling `redeem` directly, increasing the risk of accidentally passing incorrect receiver or owner addresses and resulting in a less consistent developer and user experience compared to the other vault functions.

**Recommended Mitigation:**
Add a convenience function `redeem(uint256 shares)` that internally calls `redeem(shares, msg.sender, msg.sender)`, providing the same ergonomic shorthand available for the other vault operations.

---

**[中文版本]**

**描述：**
`StakingVault.sol` 为常用操作实现了多个便捷函数：`stake(uint256 assets)` 作为 `deposit(assets, msg.sender)` 的简写，`unstake(uint256 assets)` 对应 `withdraw(assets, msg.sender, msg.sender)`，`mint(uint256 shares)` 对应 `mint(shares, msg.sender)`。然而，`redeem` 没有对应的便捷函数，迫使用户在赎回份额时必须手动指定所有三个参数。这在合约 API 接口中造成不一致，使赎回操作相比其他金库操作更不友好。

**影響：**
用户在直接调用 `redeem` 时必须指定所有三个参数，增加了意外传入错误接收方或所有者地址的风险，与其他金库函数相比开发者和用户体验不一致。

**修復建議：**
添加便捷函数 `redeem(uint256 shares)`，内部调用 `redeem(shares, msg.sender, msg.sender)`，提供与其他金库操作相同的人机工程学简写。

---

## 7. Remove from parameter from Minter:redeem and _onlySender function

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`Minter::redeem` accepts a `from` input parameter but then calls `_onlySender` to enforce that `from == msg.sender`. Since `_onlySender` will always revert if `from != msg.sender`, the `from` parameter is effectively redundant — callers can never pass any value for `from` other than their own address. Having an input parameter that must equal `msg.sender` is misleading to callers and adds unnecessary function signature complexity. The `_onlySender` helper function exists solely to support this pattern and is also unnecessary.

**Impact:**
The redundant `from` parameter creates a misleading API — callers might assume they can redeem on behalf of another address, only to discover at runtime that the call will revert. This reduces clarity and increases the surface area for integration mistakes.

**Recommended Mitigation:**
Remove the `from` parameter from `Minter::redeem` and the `_onlySender` function entirely. Use `msg.sender` directly inside `redeem` for all operations that currently reference `from`.

---

**[中文版本]**

**描述：**
`Minter::redeem` 接受 `from` 输入参数，但随后调用 `_onlySender` 强制要求 `from == msg.sender`。由于 `_onlySender` 在 `from != msg.sender` 时始终回滚，该 `from` 参数实际上是冗余的——调用方永远无法传入自己地址以外的值。拥有一个必须等于 `msg.sender` 的输入参数会误导调用方，并增加不必要的函数签名复杂性。`_onlySender` 辅助函数仅用于支持此模式，同样是多余的。

**影響：**
冗余的 `from` 参数创造了一个具有误导性的 API——调用方可能以为可以代表其他地址赎回，直到运行时才发现调用会回滚，降低了代码清晰度并增加了集成错误的可能性。

**修復建議：**
从 `Minter::redeem` 中完全移除 `from` 参数和 `_onlySender` 函数，在 `redeem` 内部直接使用 `msg.sender` 替代所有当前引用 `from` 的操作。

---

## 8. Revert if StakingVault::deposit, mint, redeem, withdraw would return zero

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
A common vault exploit pattern relies on manipulating the vault's exchange rate such that certain operations return zero: deposits return zero shares (effectively a donation), mints return zero assets (free share creation), redeems return zero assets (burning shares for nothing), or withdrawals return zero shares (withdrawing assets without burning shares). None of these conditions correspond to a legitimate user transaction. Failing to revert in these cases opens the vault to share-price manipulation attacks that can drain assets from other depositors.

**Impact:**
Without zero-return checks, attackers can manipulate the vault state to trigger these degenerate conditions, enabling donation attacks, free share creation, or draining assets through crafted exchange rate manipulation.

**Recommended Mitigation:**
Add explicit zero-value checks in `StakingVault::deposit`, `mint`, `redeem`, and `withdraw` that revert if the computed return value (shares for deposit/mint, assets for redeem/withdraw) would be zero.

---

**[中文版本]**

**描述：**
常见的金库攻击模式依赖于操纵兑换率使某些操作返回零：存款返回零份额（实质为捐款）、铸造返回零资产（免费获取份额）、赎回返回零资产（销毁份额换不到任何东西）或提款返回零份额（提取资产而不销毁份额）。以上任何情况均不对应合法的用户交易，不回滚则会使金库暴露于利用兑换率操纵攻击的风险中，可能耗尽其他存款人的资产。

**影響：**
若无零值返回检查，攻击者可操纵金库状态触发这些退化条件，实现捐款攻击、免费份额创建或通过精心设计的兑换率操纵来耗尽资产。

**修復建議：**
在 `StakingVault::deposit`、`mint`、`redeem` 和 `withdraw` 中添加明确的零值检查，若计算出的返回值（存款/铸造时的份额，赎回/提款时的资产）为零则回滚。

---

## 9. SharesCooldown instant finalization can be DoSed because of the UnstakeCooldown request limits

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
Instant finalization of a `SharesCooldown` position via `finalizeWithFee` forces the user to receive `USDe`, routing through `strategy.withdraw` which creates an `UnstakeCooldown` request. Inside `UnstakeCooldown.transfer`, there is a strict `PUBLIC_REQUEST_SLOTS_CAP` of 40 slots for external receiver requests (where `initialFrom != to`). Since `SharesCooldown` is the sender, every USDe finalization consumes one of the 40 public slots for the user. However, `SharesCooldown` itself allows up to 70 active requests per user — a mismatch that means up to 30 valid `SharesCooldown` requests can become unfinalizable in USDe, reverting due to the 40-slot cap. An attacker can exploit this by creating 40 small withdrawal requests targeting the victim as receiver, filling their `UnstakeCooldown` queue, and preventing all instant finalizations via `finalizeWithFee` for the duration of the sUSDe unstake delay.

**Impact:**
Instant finalizations via `finalizeWithFee` are vulnerable to DoS when the victim's `UnstakeCooldown` public slot quota is exhausted by an attacker. The victim is forced to wait until the attacker's requests expire before resuming instant finalizations.

**Recommended Mitigation:**
Allow users to select which asset to receive when calling `finalizeWithFee`. If the user can select `sUSDe` directly, the `UnstakeCooldown` queue is bypassed entirely, eliminating the DoS attack vector.

---

**[中文版本]**

**描述：**
通过 `finalizeWithFee` 进行即时最终结算时，用户被迫接收 `USDe`，执行路径经由 `strategy.withdraw` 创建 `UnstakeCooldown` 请求。`UnstakeCooldown.transfer` 内部对外部接收方请求（`initialFrom != to`）设有严格的 `PUBLIC_REQUEST_SLOTS_CAP`（40个槽位）。由于 `SharesCooldown` 是发送方，每次 USDe 最终结算都会占用用户的一个公共槽位。但 `SharesCooldown` 本身每用户最多允许 70 个活跃请求——这一不匹配意味着最多 30 个有效 `SharesCooldown` 请求会因 40 槽位上限而无法以 USDe 完成最终结算。攻击者可创建 40 个以受害者为接收方的小额提款请求来填满其 `UnstakeCooldown` 队列，阻止受害者在 sUSDe 解锁延迟期间进行所有即时最终结算。

**影響：**
当受害者的 `UnstakeCooldown` 公共槽位配额被攻击者耗尽时，`finalizeWithFee` 的即时最终结算易受 DoS 攻击，受害者被迫等待攻击者的请求到期后才能恢复即时最终结算。

**修復建議：**
允许用户在调用 `finalizeWithFee` 时选择接收哪种资产。若用户可直接选择 `sUSDe`，则绕过 `UnstakeCooldown` 队列，彻底消除 DoS 攻击向量。

---

## 10. SherpaVault::redeem naming ambiguous

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault` uses ERC-4626-adjacent terminology but with different semantics. In ERC-4626, `redeem` means burning shares to withdraw underlying assets. In `SherpaVault`, the `redeem` function means finalizing a prior deposit by moving unredeemed pending shares into the user's wallet — conceptually closer to `claimShares` or `finalizeDeposit`. This naming mismatch can mislead integrators, tooling, and end users who assume ERC-4626 behavior and expect that calling `redeem` would burn their shares and return underlying assets.

**Impact:**
Integrators and users familiar with ERC-4626 may invoke `redeem` expecting to exit their position, but instead receive pending shares rather than underlying assets. This can lead to misuse, confusion, and integration bugs in any system that treats `SherpaVault` as an ERC-4626-compatible vault.

**Recommended Mitigation:**
Rename the `redeem` function to `claimShares` or `finalizeDeposit` to make its semantics explicit and prevent confusion with the standard ERC-4626 redeem operation.

---

**[中文版本]**

**描述：**
`SherpaVault` 使用类 ERC-4626 术语但语义不同。在 ERC-4626 中，`redeem` 意味着销毁份额以提取底层资产。但在 `SherpaVault` 中，`redeem` 函数意味着通过将待领取的待处理份额转入用户钱包来完成之前的存款，更接近于 `claimShares` 或 `finalizeDeposit` 的概念。这种命名不一致会误导假设 ERC-4626 行为的集成方、工具和用户，使他们以为调用 `redeem` 会销毁份额并返回底层资产。

**影響：**
熟悉 ERC-4626 的集成方和用户可能调用 `redeem` 期望退出仓位，却收到待处理份额而非底层资产，导致任何将 `SherpaVault` 视为 ERC-4626 兼容金库的系统出现误用、混乱和集成 bug。

**修復建議：**
将 `redeem` 函数重命名为 `claimShares` 或 `finalizeDeposit`，明确其语义，防止与标准 ERC-4626 赎回操作混淆。

---

## 11. Tranche::redeem calls super.withdraw instead of super.redeem causing users to receive fewer assets

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
`Tranche::redeem` contains a bug where it calls `super.withdraw(shares, receiver, owner)` instead of `super.redeem(shares, receiver, owner)`. According to EIP-4626, `redeem(uint256 shares, ...)` should burn exactly the specified number of shares and return the corresponding asset amount, while `withdraw(uint256 assets, ...)` should withdraw exactly the specified asset amount and return the shares burned. By calling `super.withdraw` with the `shares` value, the function treats the share count as an asset denomination. When the exchange rate is not 1:1 (e.g., after yield accrual), this results in the user burning more shares than expected for fewer assets than they should receive, violating the fundamental redeem/withdraw distinction of ERC-4626.

**Impact:**
Users receive significantly fewer assets than expected when calling `redeem` because the function processes their share count as an asset amount. The function also violates the ERC-4626 standard by not burning the exact number of shares specified and by returning incorrect values.

**Recommended Mitigation:**
Replace `super.withdraw(shares, receiver, owner)` with `super.redeem(shares, receiver, owner)` in `Tranche::redeem` to correctly implement ERC-4626 redeem semantics.

---

**[中文版本]**

**描述：**
`Tranche::redeem` 存在 bug：它调用 `super.withdraw(shares, receiver, owner)` 而非 `super.redeem(shares, receiver, owner)`。按照 EIP-4626，`redeem(uint256 shares, ...)` 应精确销毁指定数量的份额并返回对应资产，而 `withdraw(uint256 assets, ...)` 应精确提取指定数量的资产并返回已销毁份额。通过以 `shares` 值调用 `super.withdraw`，函数将份额数量作为资产单位处理。当兑换率不为 1:1 时（例如收益累积后），这导致用户销毁超出预期的份额换取少于应得的资产，违反了 ERC-4626 赎回/提款的基本区别。

**影響：**
调用 `redeem` 时用户收到的资产显著少于预期，因为函数将其份额数量当作资产数量处理。该函数还违反了 ERC-4626 标准，未精确销毁指定数量的份额且返回值不正确。

**修復建議：**
在 `Tranche::redeem` 中将 `super.withdraw(shares, receiver, owner)` 替换为 `super.redeem(shares, receiver, owner)`，正确实现 ERC-4626 赎回语义。
