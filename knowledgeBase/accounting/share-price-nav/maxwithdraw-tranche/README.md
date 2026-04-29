# maxwithdraw-tranche (7)

> Issues where maxWithdraw, maxRedeem, or tranche NAV calculations were incorrect, stale, or violated EIP-4626.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Deposits using lagging Vested NAV cause dilution of existing shareholders

**Severity:** 🟡 Medium  **Source:** `sherlockPDFTXT/YieldFi.txt`

**Description:**
The `Manager` contract in YieldFi uses `currentNav` — a linearly vested value that slowly approaches the target NAV (`endNav`) over time — as the share price for calculating how many new shares to mint on deposit. This vesting mechanism is designed to prevent front-running. However, OTC lending operations often generate "Bullet Repayments" that cause the NAV to jump significantly in a single update. When a large repayment occurs, `endNav` jumps immediately while `currentNav` still reflects the old, lower value. An attacker who monitors the chain for such profit settlement events can deposit before vesting completes, receiving shares priced at the artificially low `currentNav` instead of the true `endNav`. When vesting concludes and NAV reaches `endNav`, the attacker's shares are worth significantly more than what was paid — capturing yield that rightfully belongs to existing long-term holders.

**Impact:**
Attackers can perform risk-free arbitrage around NAV jump events, minting excessive shares at discounted prices that dilute the stake of existing depositors. Existing shareholders lose a portion of their earned yield proportional to the attacker's inflated share allocation.

**Recommended Mitigation:**
Modify the share calculation logic for deposits so that the target NAV (`endNav`) is used instead of the lagging `currentNav` when the NAV is in an increasing state. Using the higher, honest NAV prevents attackers from acquiring shares below fair value during vesting gaps.

---

**[中文版本]**

**描述：**
`Manager` 合约使用线性归属中的 `currentNav`（当前 NAV，慢慢接近目标 `endNav`）作为铸造份额的价格。当一笔大额子弹还款导致 `endNav` 突然跳升时，`currentNav` 仍处于旧的低值。攻击者监控链上事件，在 NAV 归属完成前按低价存款，以低于公允价值的价格获取份额，待 NAV 完成归属后套利。

**影響：**
攻击者以折扣价铸造过多份额，稀释现有存款人的质押比例，捕获本属于长期持有者的收益。

**修復建議：**
当 NAV 处于上升状态时，使用目标 NAV（`endNav`）而非滞后的 `currentNav` 计算铸造份额，防止攻击者在归属间隙以低于公允价值获取份额。

---

## 2. Immediate withdrawals possible even when NAV is stale through `AccountableYield::accrueAndProcess`

**Severity:** 🟡 Medium  **Source:** `cyfrin/pr50.md`

**Description:**
`AccountableYield` implements NAV staleness protection by checking `_navIsStale()` in `onRequestRedeem` to disable "instant fulfill" when NAV data is outdated. When NAV is stale, redemption requests are queued for deferred processing rather than immediately settled. However, `AccountableYield::accrueAndProcess` — which processes the withdrawal queue — is publicly callable with no staleness gate. A user can submit a redeem request and, in the same transaction or immediately afterward, call `accrueAndProcess()` to process the queue and receive their withdrawal even while NAV is stale. The protection in `onRequestRedeem` is therefore trivially bypassed.

**Impact:**
The intended NAV staleness protection is defeated. Users can withdraw at the last known (potentially stale) NAV-derived price during periods when NAV updates are unavailable, potentially extracting value at incorrect prices if the true NAV has declined significantly since the last update.

**Recommended Mitigation:**
Apply the `whenNotStale` modifier (or equivalent staleness check) to `accrueAndProcess()` and any other public entrypoints that trigger `_processAvailableWithdrawals()`, such as `AccountableYield::repay`. This ensures the queue is never processed with a stale NAV regardless of which code path triggers processing.

---

**[中文版本]**

**描述：**
`AccountableYield` 在 `onRequestRedeem` 中通过 `_navIsStale()` 检查来禁用 NAV 过期时的即时赎回。然而，处理提款队列的 `accrueAndProcess()` 函数是公开可调用的，且没有过期检查守卫。用户可以在提交赎回请求后立即调用 `accrueAndProcess()`，绕过保护机制在 NAV 过期时立即结算提款。

**影響：**
NAV 过期保护被轻易绕过，用户可以在 NAV 真实值可能已大幅下降的情况下按过期价格提款，从协议中提取不当价值。

**修復建議：**
为 `accrueAndProcess()` 及所有可触发 `_processAvailableWithdrawals()` 的公开入口添加 `whenNotStale` 修饰符，确保队列处理始终在 NAV 有效时进行。

---

## 3. Invalid `maxWithdraw()` check in `withdraw()`

**Severity:** 🟡 Medium  **Source:** `cyfrin/accountable.md`

**Description:**
`AccountableAsyncRedeemVault::withdraw` enforces an upper bound on the withdrawal amount by checking `if (assets > maxWithdraw(receiver)) revert ExceedsMaxRedeem()`. However, the correct check per EIP-4626 is against the `owner` (the share holder authorizing the withdrawal), not the `receiver` (the destination address for the assets). Using `receiver` instead of `owner` means the check validates the receiver's withdrawal limits rather than the controller's available balance. This violates EIP-4626's invariant that withdrawals above `maxWithdraw(owner)` must revert, and can be exploited: an owner whose `maxWithdraw` would be exceeded can still call `withdraw` if the receiver's `maxWithdraw` is large enough.

**Impact:**
Unauthorized withdrawals above the owner's legitimate limit may succeed if the receiver has a higher `maxWithdraw`. Additionally, the receiver's withdrawal capacity can be erroneously capped by this check, creating a denial-of-service condition for `withdraw()` unrelated to the owner's position.

**Recommended Mitigation:**
Change the check to validate `maxWithdraw(controller)` rather than `maxWithdraw(receiver)`. The controller (or owner) is the party whose share position and withdrawal limits should constrain the operation.

---

**[中文版本]**

**描述：**
`AccountableAsyncRedeemVault::withdraw` 检查 `maxWithdraw(receiver)` 而非正确的 `maxWithdraw(owner/controller)`。EIP-4626 规范要求超过 `maxWithdraw(owner)` 的提款必须回滚，但实现中验证的是接收方的上限，导致所有者可能绕过其份额限制，或接收方的限制被错误地应用于所有者的操作。

**影響：**
所有者可以绕过其合法提款上限（若接收方的上限更高），同时接收方的提款容量可能因此被错误限制，对 `withdraw()` 造成 DoS。

**修復建議：**
将检查改为 `assets > maxWithdraw(controller)`，使用控制者（所有者）的上限进行验证。

---

## 4. `Tranche::burnSharesAsFee` can be used to manipulate the exchange rate to cause withdrawals to revert for legitimate users

**Severity:** 🟡 Medium  **Source:** `cyfrin/cooldown.md`

**Description:**
`Tranche::burnSharesAsFee` is a function that allows burning shares as a fee collection mechanism, distributing the corresponding NAV proportionally between the Tranche and a Reserve. The function does not check whether the remaining shares after burning fall below the `MIN_SHARES` threshold enforced in normal withdrawal flows. An attacker can exploit this to inflate the exchange rate before any legitimate deposit: first deposit 1 full share, then burn all of it via `burnSharesAsFee`. At this point `totalSupply == 0` while `Tranche_NAV > 0` due to `retentionBps`. The attacker then mints 1 wei of shares, setting an extreme exchange rate. When a legitimate user then deposits a large amount, they receive only a few wei of shares due to the inflated rate — an amount below `MIN_SHARES` — and their subsequent withdrawal attempt reverts with `MinSharesViolation`, permanently locking their funds.

**Impact:**
An attacker can front-run the first legitimate deposit and execute this exchange rate manipulation to permanently trap another user's funds in the Tranche, as their share count is too small to satisfy the `MIN_SHARES` withdrawal threshold.

**Recommended Mitigation:**
Call `_onAfterWithdrawalChecks` at the end of `Tranche::burnSharesAsFee` to enforce the `MIN_SHARES` invariant after fee burning. This prevents the post-burn state from falling below the safety threshold that enables exchange rate manipulation.

---

**[中文版本]**

**描述：**
`Tranche::burnSharesAsFee` 不验证燃烧后剩余份额是否低于 `MIN_SHARES` 阈值。攻击者可以先存入 1 份份额，通过此函数全部销毁，此时 `totalSupply == 0` 但 `Tranche_NAV > 0`（因 `retentionBps`）。攻击者再铸造 1 wei 份额，设置极端兑换率。合法用户随后的大额存款因兑换率极高只能获得极少量份额（低于 `MIN_SHARES`），导致提款因 `MinSharesViolation` 回滚，资金被永久锁定。

**影響：**
攻击者通过抢先操控兑换率，可以永久锁定其他用户的存款资金。

**修復建議：**
在 `Tranche::burnSharesAsFee` 末尾调用 `_onAfterWithdrawalChecks`，确保燃烧费用后份额数量不低于 `MIN_SHARES` 安全阈值。

---

## 5. `Tranche::maxWithdraw` can understate the max withdrawal for the `SharesCooldown` contract

**Severity:** 🟡 Medium  **Source:** `cyfrin/cooldown.md`

**Description:**
`Tranche::maxWithdraw(owner)` computes the net assets available to withdraw by calling `previewRedeem(sharesGross)`. The `previewRedeem` function internally calls `cdo.calculateExitMode(address(this), address(0))` — passing `address(0)` as the owner — and applies exit fees based on that lookup. However, when the `owner` is the `SharesCooldown` contract, the CDO explicitly exempts `SharesCooldown` from exit fees, returning a zero fee. Because `previewRedeem` always uses `address(0)` rather than the actual owner, `maxWithdraw(address(sharesCooldown))` computes a fee-inclusive asset amount that is lower than the fee-exempt amount `SharesCooldown` would actually receive during redemption. The result is that `maxWithdraw` understates the true maximum withdrawal for `SharesCooldown`.

**Impact:**
Off-chain integrations, front-ends, and protocols that query `maxWithdraw` for the `SharesCooldown` contract to determine available liquidity will receive a lower value than the actual withdrawal capacity. This can result in unnecessary rejection of valid withdrawal requests or incorrect UI displays showing less available balance than users can actually access.

**Recommended Mitigation:**
Update `maxWithdraw(owner)` to pass the actual `owner` address to `calculateExitMode` rather than `address(0)`, so that the exit fee calculation accurately reflects the fee exemption granted to `SharesCooldown`. Alternatively, document clearly that the public `maxWithdraw` and `previewRedeem` functions do not account for the `SharesCooldown` fee exemption.

---

**[中文版本]**

**描述：**
`Tranche::maxWithdraw` 通过 `previewRedeem` 计算可提款资产，而 `previewRedeem` 在查询退出费率时始终传递 `address(0)` 而非实际所有者地址。当所有者为 `SharesCooldown` 时，CDO 明确豁免其退出费，但 `address(0)` 的查询不享有此豁免，导致 `maxWithdraw(address(sharesCooldown))` 返回的值低于 `SharesCooldown` 实际可以提取的金额。

**影響：**
链下集成和前端查询 `maxWithdraw` 时会获得低于实际的可提款金额，导致有效提款请求被错误拒绝或 UI 显示余额不准确。

**修復建議：**
将 `maxWithdraw` 中的 `calculateExitMode` 调用改为传递实际 `owner` 地址，使退出费计算能正确反映 `SharesCooldown` 的费用豁免。

---

## 6. When Senior's `TargetGain` is negative, the transaction reverts because the senior loss is not accounted for on the Junior Tranche as profit

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
The NAV split logic in the CDO handles the case where the Senior Tranche's target gain is negative (the Senior is experiencing a loss) by transferring the loss amount from the Senior NAV to the Junior NAV as profit — since the Junior is supposed to absorb Senior losses. The code correctly decrements `srtNavT0` but incorrectly increments `jrtNavT0` (the initial Junior NAV) instead of `jrtNavT1` (the computed final Junior NAV). Because `jrtNavT1` was already computed before this branch executes, the Senior loss is never reflected in the final Junior NAV. When the function subsequently validates that `navT1 == jrtNavT1 + srtNavT1 + reserveNavT1`, the sum does not match because `jrtNavT1` is missing the senior loss addition, and the transaction reverts with `InvalidNavSpit`.

**Impact:**
Any NAV update that triggers a negative Senior target gain will revert, blocking the NAV accounting for the affected epoch. This can occur in market downturns or when yield falls below the Senior's target rate, preventing the protocol from properly settling the epoch's accounting and potentially blocking all downstream operations that depend on the updated NAVs.

**Recommended Mitigation:**
Change `jrtNavT0 += srtLoss` to `jrtNavT1 += srtLoss` in the negative Senior gain branch. This ensures the senior loss is propagated to the final Junior NAV value that participates in the invariant check.

---

**[中文版本]**

**描述：**
CDO NAV 分配逻辑在 Senior 目标收益为负时，将 Senior 损失转移给 Junior 作为收益。代码正确地递减了 `srtNavT0`，但错误地递增了 `jrtNavT0`（初始 Junior NAV）而非 `jrtNavT1`（最终 Junior NAV）。由于 `jrtNavT1` 在该分支执行前已计算完毕，Senior 损失未被反映到最终 NAV，导致后续的 NAV 总和验证失败，交易回滚。

**影響：**
任何触发 Senior 负目标收益的 NAV 更新都会回滚，阻止该纪元的会计结算，可能引发依赖更新后 NAV 的所有下游操作失败。

**修復建議：**
将 `jrtNavT0 += srtLoss` 改为 `jrtNavT1 += srtLoss`，确保 Senior 损失被传播到参与不变量检验的最终 Junior NAV 值。

---

## 7. `pUSDeVault::maxWithdraw` doesn't account for withdrawal pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`

**Severity:** 🟡 Medium  **Source:** `cyfrin/predeposit.md`

**Description:**
EIP-4626 specifies that `maxWithdraw(owner)` must return zero when the vault is in a state where withdrawals would fail — including when the vault is paused. `pUSDeVault` implements a withdrawal pause mechanism through `PreDepositVault`, but `maxWithdraw` does not check whether withdrawals are paused before returning the computed maximum. When withdrawals are paused, any amount returned by `maxWithdraw` is misleading because an actual `withdraw` call will revert. Protocols and smart contracts that integrate with `pUSDeVault` — such as aggregators or yield strategies — typically call `maxWithdraw` before attempting a withdrawal to verify feasibility. Receiving a non-zero value while withdrawals are actually blocked can cause those integrating protocols to fail with unexpected reverts, destabilize their own accounting, or misallocate liquidity.

**Impact:**
Integrating protocols that rely on EIP-4626 compliance for liquidity management will receive incorrect `maxWithdraw` values during pause periods, potentially causing their own operations to fail or produce incorrect state transitions.

**Recommended Mitigation:**
Override `maxWithdraw` in `PreDepositVault` (where the pause functionality lives) to return zero when withdrawals are paused. This ensures the function accurately reflects the actual withdrawal capacity at all times, maintaining EIP-4626 compliance.

---

**[中文版本]**

**描述：**
EIP-4626 规定当金库处于提款会失败的状态（包括暂停时），`maxWithdraw` 必须返回零。`pUSDeVault` 实现了提款暂停机制，但 `maxWithdraw` 未检查暂停状态，在提款暂停时仍返回非零值。集成 `pUSDeVault` 的协议通常先调用 `maxWithdraw` 验证可行性，收到非零值后发起提款却因暂停而回滚，导致集成协议状态错误或流动性分配失误。

**影響：**
依赖 EIP-4626 合规性进行流动性管理的集成协议，在提款暂停期间会收到错误的 `maxWithdraw` 值，导致其自身操作失败或产生错误状态转换。

**修復建議：**
在 `PreDepositVault`（暂停功能所在处）中重写 `maxWithdraw`，当提款暂停时返回零，确保函数始终准确反映实际可提款容量，符合 EIP-4626 规范。
