# withdrawal-requests (14)

> Issues where withdrawal requests can be stuck, front-run, overwritten, or improperly finalized.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Single reverting withdrawal can block the BasisTradeVault withdrawal queue

**Severity:** 🟠 High
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeVault::processWithdrawal` processes exactly one request at the queue head and performs the final ERC20 `safeTransfer` to the request's user. If that transfer reverts, the whole transaction reverts and the head entry remains in place. Because the function always targets `queueHead` and provides no way to skip, quarantine, or edit the failing entry, a single reverting withdrawal permanently blocks the entire queue (head-of-line blocking). Common revert causes include the receiver being blacklisted by the token (e.g., USDC/USDT compliance lists) or the computed assets for a request becoming zero due to rounding/fees and the token reverting on zero-amount transfers. This can happen accidentally or be used to grief the protocol by placing an unprocessable request at the head.

**Impact:**
Withdrawal processing can be indefinitely halted for all users behind the stuck request, causing severe withdrawal delays for all other depositors. The queue remains stuck until a contract upgrade or manual intervention.

**Recommended Mitigation:**
Redesign away from a strict queue to a timelock plus user-pull model where each user calls `processWithdrawal` themselves after the timelock. Alternatively add a skip/quarantine mechanism: if a head withdrawal fails, move it into a frozen set keeping shares escrowed, advance `queueHead`, and allow others to proceed. Provide functions for the user to update their payout address and for agents to retry or cancel within policy.

---

**[中文版本]**

**描述：**
`BasisTradeVault::processWithdrawal` 每次仅处理队列头部的一条请求，并向用户地址发起最终的 ERC20 `safeTransfer`。若该转账回滚，整笔交易将随之回滚，队列头部条目保持不变。由于该函数始终针对 `queueHead` 且不提供任何跳过或隔离机制，一笔无法处理的提款将永久阻塞整个队列（队首阻塞）。常见回滚原因包括接收者被代币黑名单（如 USDC/USDT）或因舍入/费用导致 assets 计算为零而触发零值转账回滚。

**影響：**
所有排在阻塞请求后面的用户的提款处理将被无限期暂停，导致严重的提款延迟，直到合约升级或人工干预为止。

**修復建議：**
将严格队列重新设计为时间锁加用户主动拉取模式，让每位用户在时间锁到期后自行调用 `processWithdrawal`。或添加跳过/隔离机制：若队首提款失败，将其移入冻结集合并保留份额托管，推进 `queueHead`，允许其他人继续。同时提供允许用户更新收款地址及代理人在策略内重试/取消的函数。

---

## 2. APR Targets are not updated when withdrawal requests are sent to the SharesCooldown to reflect the change on NAVs caused by the charged fees for the withdrawal

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The execution path for processing a withdrawal request sent to the `SharesCooldown` charges fees by burning tranche shares and updating the Tranche NAV and `reserveNav` accordingly (via `SharesCooldown::requestRedeem` → `accrueFee` → `Tranche::burnSharesAsFee` → `CDO::accrueFee` → `Accounting::accrueFee`). The problem is that the APR Targets for the Tranches are not recalculated to reflect the changes to the NAVs after this fee accrual. The system will therefore use outdated APR targets until a new operation is performed that updates them.

**Impact:**
Outdated APR targets — especially outdated and higher-than-actual APR Targets for the SR Tranche — will cause Junior Tranche holders to earn less interest than they should, as the system incorrectly estimates the senior tranche's expected yield.

**Recommended Mitigation:**
Refactor the `Accounting::accrueFee` function to update the APR Target after each fee accrual, similar to how `Accounting::updateBalanceFlow` already does.

---

**[中文版本]**

**描述：**
处理发送至 `SharesCooldown` 的提款请求时，系统会按已赎回的 Tranche Shares 总量收取费用，以燃烧份额的形式更新 Tranche NAV 和 `reserveNav`（执行路径：`SharesCooldown::requestRedeem` → `accrueFee` → `Tranche::burnSharesAsFee` → `CDO::accrueFee` → `Accounting::accrueFee`）。问题在于 NAV 发生变化后，各 Tranche 的 APR 目标并未随之重新计算，系统将继续使用过时的 APR 目标，直到下一次触发更新操作。

**影響：**
过时且偏高的 SR Tranche APR 目标将导致 JR Tranche 持有者获得的利息少于应得数额，因为系统错误估计了高级份额的预期收益。

**修復建議：**
重构 `Accounting::accrueFee` 函数，在每次费用累计后更新 APR 目标，参考 `Accounting::updateBalanceFlow` 的实现方式。

---

## 3. BasisTradeTailor withdrawal request overwrite enables race conditions

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`BasisTradeTailor::requestWithdrawal` unconditionally overwrites any existing withdrawal request with a new amount and provides no explicit cancellation mechanism. When a user attempts to modify an existing request, the final outcome depends entirely on the transaction ordering relative to the agent's `processWithdrawal` call. If the agent processes the original request first before the user's modification transaction executes, the modification creates a brand-new request rather than replacing the old one, causing both amounts to be withdrawn in sequence. A user intending to reduce a 100-unit withdrawal to 50 units could end up withdrawing 150 units total if the agent processes the original request before the modification lands.

**Impact:**
Users may withdraw significantly more than intended due to race conditions between their modification transactions and the agent's processing calls. This can result in unintended over-withdrawal and unexpected fund movements.

**Recommended Mitigation:**
Prevent changing a non-zero request to another non-zero value directly. Require explicit cancellation first by adding a dedicated `cancelWithdrawal` function that sets the request to zero. The `requestWithdrawal` function should revert if a pending request already exists, forcing users to cancel before creating a new request.

---

**[中文版本]**

**描述：**
`BasisTradeTailor::requestWithdrawal` 会无条件覆盖任何已有的提款请求，且没有提供明确的取消机制。当用户尝试修改已有请求时，最终结果完全取决于其修改交易与代理人 `processWithdrawal` 调用的执行顺序。若代理先处理原始请求，则用户的修改将创建一个全新请求，导致两笔金额被依次提取。原本想把 100 单位请求改为 50 单位的用户，可能最终提取了 150 单位。

**影響：**
由于用户修改交易与代理处理调用之间存在竞态条件，用户可能提取远超预期的金额，造成非预期的资金流出。

**修復建議：**
禁止直接将非零请求修改为另一个非零值，要求先通过专用 `cancelWithdrawal` 函数显式取消现有请求。`requestWithdrawal` 函数在存在待处理请求时应回滚，强制用户先取消再创建新请求。

---

## 4. DOS for certain scenarios depending on the LTVs of the 2 positions

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu.txt`

**Description:**
The `Migrate.cairo` contract allows existing users to migrate their positions and requires them to choose a `max_ltv_delta` value to ensure their new position remains solvent. The final check in `create_v2_position` asserts that the resulting LTV falls within the range `from_ltv - max_ltv_delta` to `from_ltv + max_ltv_delta`. However, when `from_ltv` is zero (a position with collateral only and no debt), `max_ltv_delta` can only be zero to avoid an underflow revert. If the target position has any non-zero LTV after migration, the assertion `to_ltv <= from_ltv + max_ltv_delta` can never be satisfied since both terms are zero. This means migrations from debt-free positions into positions with existing debt are mathematically impossible under the current check.

**Impact:**
Migrations can never complete for certain position configurations depending on the LTVs before migration begins. Users with collateral-only positions migrating to pools where they would take on debt are permanently blocked.

**Recommended Mitigation:**
If `max_ltv_delta` is larger than `from_ltv`, skip the lower bound check to allow larger `max_ltv_delta` values for the upper bound check, enabling debt-free positions to migrate to positions with higher LTV.

---

**[中文版本]**

**描述：**
`Migrate.cairo` 合约要求用户在迁移仓位时选择 `max_ltv_delta` 值以确保新仓位不会被清算。`create_v2_position` 中的最终检查要求迁移后的 LTV 落在 `from_ltv - max_ltv_delta` 至 `from_ltv + max_ltv_delta` 范围内。当 `from_ltv` 为零（纯抵押物仓位，无债务）时，为避免下溢回滚，`max_ltv_delta` 只能为零。若目标仓位迁移后的 LTV 大于零，则 `to_ltv <= from_ltv + max_ltv_delta` 永远无法满足，导致迁移操作不可能完成。

**影響：**
根据迁移前后仓位的 LTV 配置，某些仓位的迁移永远无法成功。纯抵押物仓位无法迁移至带债务的仓位。

**修復建議：**
若 `max_ltv_delta` 大于 `from_ltv`，则跳过下界检查，允许更大的 `max_ltv_delta` 值用于上界检查，使零债务仓位能够迁移至较高 LTV 的仓位。

---

## 5. Direct YToken deposits can lock funds below minimum withdrawal threshold

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`Manager::deposit` enforces a minimum deposit amount check requiring that the resulting shares meet a `minSharesInYToken` threshold. Similarly, the redeem flow requires the redemption amount to meet the same minimum. However, no such minimum is enforced when depositing directly into a `YToken` contract, where `YToken::_deposit` and `YTokenL2::_deposit` only require the receiver to be non-zero and the amounts to be positive. As a result, a user can deposit an amount that results in fewer shares than `minSharesInYToken`, which cannot be withdrawn through the `Manager` due to its minimum withdrawal check. The stuck shares cannot be accessed through the normal exit path.

**Impact:**
Users can bypass the minimum share threshold by depositing directly into a `YToken`. If the resulting share amount is below the minimum allowed for withdrawal via the `Manager`, the user will be unable to exit their position. This leads to unintentionally locked funds and a degraded user experience.

**Recommended Mitigation:**
Enforce the `minSharesInYToken` threshold in `YToken::_deposit` and `YTokenL2::_deposit` to prevent sub-threshold deposits. Additionally, validate post-withdrawal balances to ensure users are not left with non-withdrawable dust (require remaining shares to be either zero or above the minimum threshold).

---

**[中文版本]**

**描述：**
`Manager::deposit` 通过最低份额检查强制要求存款产生的份额达到 `minSharesInYToken` 阈值，赎回流程也有相同要求。然而，直接向 `YToken` 合约存款时没有此类最低限制，`YToken::_deposit` 和 `YTokenL2::_deposit` 仅要求接收方非零且金额大于零。因此用户可以存入一笔导致份额低于 `minSharesInYToken` 的金额，由于 `Manager` 的最低提款检查，这些份额将无法通过正常途径提取。

**影響：**
用户可以绕过最低份额门槛直接向 `YToken` 存款，若产生的份额低于 `Manager` 允许提款的最低值，用户将无法退出仓位，导致资金被无意中锁定。

**修復建議：**
在 `YToken::_deposit` 和 `YTokenL2::_deposit` 中强制执行 `minSharesInYToken` 阈值，防止低于门槛的存款。同时在提款后验证剩余余额，确保用户不会留下无法提取的零碎份额（要求剩余份额为零或高于最低阈值）。

---

## 6. Finalizing withdrawal requests on the SharesCooldown contract allows for third-parties to override user's chosen output token

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
During `Tranche::withdraw/redeem`, the user can select a desired output token. When the exit mode is `SharesLock`, however, the final token received by the user is no longer under their control because `SharesCooldown::finalize` is permissionless — any caller can choose the output token at finalization time. This enables third parties to finalize a user's claim using a different token than originally intended. For example, if a user selected `sUSDe` as the output token, a permissionless finalizer could instead specify `USDe`, forcing the user to wait through an additional unstaking period on the `sUSDe` contract before receiving their assets, extending their wait time well beyond what they agreed to.

**Impact:**
Users' intended output token preferences are overridable by any third party at finalization time. This can substantially extend the time users must wait to receive their assets, as they may be forced into longer cooldown or unstaking periods than they chose.

**Recommended Mitigation:**
Persist the user's chosen output token when creating the cooldown request and enforce it during permissionless finalization. Only the user themselves should be able to override their token choice via a permissioned finalization path.

---

**[中文版本]**

**描述：**
在 `Tranche::withdraw/redeem` 流程中，用户可以选择所需的输出代币。但当退出模式为 `SharesLock` 时，最终收到的代币不再由用户控制，因为 `SharesCooldown::finalize` 是无许可的——任何调用者都可以在最终结算时选择输出代币。第三方可以使用与用户原始意图不同的代币完成用户的提款请求。例如，若用户选择 `sUSDe` 作为输出代币，无许可的最终结算者可以指定 `USDe`，迫使用户在 `sUSDe` 合约上额外等待 unstaking 时间。

**影響：**
任何第三方均可在最终结算时覆盖用户的输出代币偏好，可能显著延长用户等待资产的时间，迫使其承担超出预期的冷却或解锁期。

**修復建議：**
在创建冷却请求时持久化用户选择的输出代币，并在无许可最终结算时强制执行该选择。只有用户本人应通过有许可的最终结算路径覆盖其代币选择。

---

## 7. Forced Withdrawal Flow Is Not Fully Censorship-Resistant

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `InclusionQueue` contract is described as a core anti-censorship tool allowing users to register on-chain withdrawal requests that the Sequencer cannot ignore. However, the forced withdrawal flow has two critical weaknesses. First, the creation of forced withdrawal requests can be restricted or rendered economically infeasible because `feeAmount` and `minWithdrawAmount` parameters are controlled by a privileged role without upper bounds, enabling the role holder to set them to arbitrarily high values and block withdrawals entirely. Second, even if a withdrawal request is created, its finalization depends on the off-chain sequencer: if the internal balance is reduced after the request is created, the withdrawal path is skipped. The sequencer can also selectively process only specific users' requests while effectively delaying others, and can manipulate internal balances via `submitPoolUpdateBatch` or `submitVaultUpdateBatch` without user consent.

**Impact:**
The forced withdrawal mechanism that is advertised as censorship-resistant can in practice be blocked or indefinitely delayed by privileged roles and the off-chain sequencer. Withdrawal requests can be rendered unexecutable through balance manipulation, and users have no guaranteed fallback.

**Recommended Mitigation:**
Decouple forced withdrawals from cached balance snapshots and execute withdrawals based on the current internal balance at finalization time. When the balance is lower than the cached request amount, the withdrawal should succeed for the available balance rather than reverting or skipping execution.

---

**[中文版本]**

**描述：**
`InclusionQueue` 合约被描述为核心抗审查工具，允许用户注册无法被 Sequencer 忽略的链上提款请求。然而该强制提款流程存在两个关键缺陷：其一，`feeAmount` 和 `minWithdrawAmount` 由特权角色控制且无上限，可被设置为极高值，从而封锁所有提款；其二，即使请求已创建，其最终执行仍依赖链下 Sequencer——若请求创建后余额减少，提款路径将被跳过。Sequencer 还可以选择性地仅处理特定用户的请求，并通过 `submitPoolUpdateBatch` 或 `submitVaultUpdateBatch` 在无用户同意的情况下修改内部余额。

**影響：**
标榜为抗审查的强制提款机制实际上可以被特权角色和链下 Sequencer 封锁或无限期延迟，提款请求可通过余额操控变为无法执行，用户没有有保障的后备手段。

**修復建議：**
将强制提款与缓存余额快照解耦，在最终结算时基于当前内部余额执行提款。当余额低于请求金额时，应按可用余额成功执行提款，而非回滚或跳过。

---

## 8. Front-Running DoS on Batch Settlement via Rolling Hash Invalidation

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
The `OmniVaultManager` employs a rolling hash mechanism where each deposit and withdrawal request appends to a shared hash. During settlement, the `SETTLER_ROLE` must provide data that exactly reconstructs the rolling hash. The vulnerability arises because any user can submit a new deposit or withdrawal request that changes the rolling hash. If this occurs after the settler has prepared their settlement transaction but before it confirms on-chain, the settlement reverts due to hash mismatch. An attacker can therefore front-run settlement transactions to indefinitely block settlements, preventing users from receiving vault shares or withdrawing assets. The only recovery mechanisms are waiting for `MAX_PENDING_REQUESTS` to be exhausted or waiting for the `RECLAIM_DELAY` period.

**Impact:**
Batch settlement can be indefinitely blocked by any user who submits a new request in the same block as the settlement transaction. This prevents deposits from being settled (users cannot receive vault shares) and withdrawals from being settled (users cannot receive their assets), causing temporary fund lockup.

**Recommended Mitigation:**
Either decouple individual requests from the shared rolling hash using per-request settlement isolation, or separate request submission and settlement into distinct time periods where new requests are blocked during settlement processing to ensure stable batch state.

---

**[中文版本]**

**描述：**
`OmniVaultManager` 采用滚动哈希机制，每笔存款和提款请求都会追加到共享哈希中。结算时，`SETTLER_ROLE` 必须提供能精确重建滚动哈希的数据。任何用户均可提交新请求来改变滚动哈希——若此操作发生在结算方准备好结算交易之后但确认上链之前，结算交易将因哈希不匹配而回滚。攻击者因此可以抢先交易来无限期阻止结算，使用户无法收到份额或提取资产。

**影響：**
任何在结算交易同一区块内提交新请求的用户均可无限期阻塞批量结算，导致存款无法结算（用户无法获得份额）和提款无法结算（用户无法取回资产），造成临时资金锁定。

**修復建議：**
通过逐请求独立结算将各请求与共享滚动哈希解耦，或将请求提交与结算分为不同的时间窗口，在结算处理期间阻止新请求提交，以确保批量状态稳定。

---

## 9. Increase in coverage can lead to a grief attack causing a DoS for previous withdrawal requests

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
An increment in `coverage` — caused by a large SR Tranche withdrawal or an increase in JR deposits — can be exploited to grief legitimate users' cooldown withdrawal requests. When coverage improves, subsequent withdrawals receive shorter cooldown periods. An attacker aware of a victim's pending SR Tranche withdrawal requesting `USDe` can create many small SR Tranche withdrawal requests designating the victim as receiver. These attacker requests have a shorter cooldown (due to the improved coverage) and, once finalized, increment the victim's `UnstakeCooldown` queue. By repeatedly creating and finalizing such requests before the victim's original request expires, the attacker can drive the victim's `UnstakeCooldown` queue to its limit. When the victim finally attempts to finalize their original withdrawal, the transaction reverts with `ExternalReceiverRequestLimitReached`.

**Impact:**
Legitimate SR Tranche withdrawals requesting `USDe` can be temporarily DoSed by griefing the victim's `UnstakeCooldown` slot limit. The victim cannot finalize their withdrawal until the attacker's requests expire and free up slots.

**Recommended Mitigation:**
Create a new permissioned `finalize` function that only allows the withdrawer to call it and that allows the withdrawer to specify the output token. The permissionless version should preserve the original token choice while preventing the griefing attack vector.

---

**[中文版本]**

**描述：**
`coverage` 的增加（由大额 SR Tranche 提款或 JR 存款增加引起）可被用来攻击合法用户的冷却提款请求。当 coverage 改善时，后续提款会获得更短的冷却期。攻击者可以以受害者为接收方创建大量小额 SR Tranche 提款请求，这些请求冷却期较短，完成后会占用受害者的 `UnstakeCooldown` 队列槽位。通过反复创建并最终结算此类请求，攻击者可将受害者的 `UnstakeCooldown` 队列填满至上限，使受害者的原始提款在尝试最终结算时因 `ExternalReceiverRequestLimitReached` 错误而回滚。

**影響：**
请求 `USDe` 的合法 SR Tranche 提款可被临时 DoS 攻击。受害者的 `UnstakeCooldown` 槽位被占满，直到攻击者的请求到期释放槽位后才能完成最终结算。

**修復建議：**
创建一个新的有许可 `finalize` 函数，仅允许提款人调用并允许其指定输出代币；无许可版本应保留用户的原始代币选择，同时防止此类攻击。

---

## 10. Investors transferring all their balances among their wallets or self-transferring on the same wallet causes incorrectly decremented investor counters causing DoS for other investors' transfers

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::recordTransfer` adjusts investor counters when a receiver's investor is new or when a sender's investor is transferring their entire balance. However, the function does not check whether the sender and receiver belong to the same investor. When an investor transfers their full balance between their own wallets, or performs a self-transfer, the function incorrectly decrements the investor counter as if that investor is leaving the system entirely, even though they are merely moving tokens between their own addresses.

**Impact:**
Investor counters are decremented when they should not be, leading to DoS for other investors' transfers if the counter underflows or reaches an incorrect value. An additional impact is that investor limits can be bypassed because the counters no longer accurately track the real number of unique investors in the system.

**Recommended Mitigation:**
Add a check in `recordTransfer` to determine whether the sender and receiver belong to the same investor before decrementing the total investor count. If the sender and receiver are the same investor, no counter adjustment should be made.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::recordTransfer` 在接收方为新投资人或发送方正在转移全部余额时调整投资人计数器。但该函数没有检查发送方和接收方是否属于同一投资人。当投资人在自己的钱包之间转移全部余额，或向自身转账时，函数会错误地递减投资人计数器，误判该投资人已离开系统。

**影響：**
投资人计数器被错误递减，可能导致其他投资人转账 DoS。同时由于计数器不再准确追踪真实投资人数量，投资人数量限制也可能被绕过。

**修復建議：**
在 `recordTransfer` 中添加检查，判断发送方和接收方是否属于同一投资人，若是则不做计数器调整。

---

## 11. Lack of Limits and Delay in Forced Withdrawal Parameter Updates

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `InclusionQueue` contract's `setAmount` function allows the owner to update `minWithdrawAmount` and `feeAmount` without enforcing any upper bounds on either parameter. Additionally, changes take effect immediately upon execution without any delay or timelock. This creates two risks: first, setting excessively high values can prevent withdrawals of smaller deposits or block all withdrawals entirely; second, immediate application enables front-running scenarios where withdrawal requests submitted with one fee expectation are executed under a newly updated (and potentially much higher) fee amount.

**Impact:**
The owner can set `feeAmount` and `minWithdrawAmount` to arbitrarily large values, making it economically infeasible for users to submit forced withdrawal requests. Immediate parameter changes also allow front-running that results in users paying higher fees than expected or having their requests rejected by newly enforced minimum thresholds.

**Recommended Mitigation:**
Enforce reasonable upper bounds for `feeAmount` and `minWithdrawAmount`, and introduce a timelock or delay mechanism for parameter updates to improve predictability and reduce front-running risk.

---

**[中文版本]**

**描述：**
`InclusionQueue` 合约的 `setAmount` 函数允许所有者在没有任何上限限制的情况下更新 `minWithdrawAmount` 和 `feeAmount`，且更改立即生效，没有任何延迟或时间锁。这带来两重风险：一是设置过高的值可阻止小额存款提款或完全封锁所有提款；二是即时生效使得抢先交易成为可能，用户提交请求时基于旧费率，执行时却面对被提高的费率。

**影響：**
所有者可以将 `feeAmount` 和 `minWithdrawAmount` 设置为任意高值，使强制提款请求在经济上不可行。即时参数变更还允许抢先交易，导致用户支付超预期的手续费或请求因新阈值而被拒绝。

**修復建議：**
为 `feeAmount` 和 `minWithdrawAmount` 设置合理上限，并引入时间锁或延迟机制用于参数更新，以提高可预期性并降低抢先交易风险。

---

## 12. Missing revert of LST withdrawal when L1MessageService balance is exactly equal to required value

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`LineaRollupYieldExtension::claimMessageWithProofAndWithdrawLST` is designed to withdraw LST tokens from a yield provider only when the `L1MessageService` balance is insufficient to fulfil message delivery. The function documentation states it should revert if the `L1MessageService` has sufficient balance. However, the balance check uses a strict less-than operator (`<`) rather than less-than-or-equal-to (`<=`). As a result, when `_params.value` is exactly equal to `address(this).balance`, the condition evaluates to false and the function proceeds with LST withdrawal despite the contract having exactly sufficient balance to fulfil the claim without touching the yield provider.

**Impact:**
When the contract balance exactly matches the claim value, the function incorrectly withdraws LST from the yield provider instead of reverting. This results in unnecessary LST withdrawal when funds are already available, gas waste for the caller, violation of the stated invariant, and potential operational inefficiencies in the yield management system.

**Recommended Mitigation:**
Change the comparison operator from `<` to `<=` to ensure the function reverts when the balance is sufficient, including the edge case where it is exactly equal to the required value.

---

**[中文版本]**

**描述：**
`LineaRollupYieldExtension::claimMessageWithProofAndWithdrawLST` 设计用于仅在 `L1MessageService` 余额不足以完成消息投递时才从收益提供方提取 LST。但余额检查使用了严格小于运算符 `<` 而非小于等于 `<=`。当 `_params.value` 恰好等于 `address(this).balance` 时，条件为假，函数继续执行 LST 提取，尽管合约余额已足够完成提款请求。

**影響：**
当合约余额恰好等于提款所需金额时，函数错误地从收益提供方提取 LST，造成不必要的 LST 提取、调用方浪费 gas、违反设计不变量，以及收益管理系统的潜在运营效率损失。

**修復建議：**
将比较运算符从 `<` 改为 `<=`，确保在余额充足（包括恰好相等的边界情况）时函数正确回滚。

---

## 13. Pending Force Withdrawal Requests Removed On Balance Update

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `Vault` contract implements a force withdrawal flow for use when the off-chain Sequencer is inactive. During `initiateForceWithdrawal`, a `ForcedWithdrawalRequest` is created and stored, caching the user's balance at that time. After a `forceWithdrawDelay`, the user can call `finalizeForceWithdrawal` to receive those cached funds. However, between initiation and finalization, the `applyStateChanges` function — callable only by the Verifier — deletes the `forcedWithdrawalRequests` mapping entry for any user whose balance is modified, even if the modification is a credit (balance increase). Any balance change at all, even by 1 wei, silently removes the pending forced withdrawal request, requiring the user to restart the entire process and wait through the delay again.

**Impact:**
The Sequencer can arbitrarily affect the forced withdrawal flow by applying minimal balance changes to users with pending requests. Even legitimate balance updates can inadvertently destroy pending force withdrawal requests, undermining the censorship-resistant guarantees of the mechanism.

**Recommended Mitigation:**
Remove the deletion of `ForcedWithdrawalRequest` entries within `applyStateChanges`. The `finalizeForceWithdrawal` function should withdraw the user's current balance rather than the cached balance from initiation, ensuring that pending requests are not removed when balances change.

---

**[中文版本]**

**描述：**
`Vault` 合约实现了用于链下 Sequencer 不活跃时的强制提款流程。`initiateForceWithdrawal` 创建 `ForcedWithdrawalRequest` 并缓存用户当时的余额，经过 `forceWithdrawDelay` 后用户可调用 `finalizeForceWithdrawal` 提取缓存资金。但在发起和最终结算之间，仅由 Verifier 可调用的 `applyStateChanges` 函数会删除余额发生变更的用户的 `forcedWithdrawalRequests` 条目，即使变更是充值（余额增加）也不例外。任何余额变动（哪怕 1 wei）都会悄无声息地删除待处理的强制提款请求，迫使用户重新发起并再次等待延迟时间。

**影響：**
Sequencer 可通过对持有待处理请求的用户施加微小余额变动来任意影响强制提款流程，合法的余额更新也可能无意中销毁待处理的强制提款请求，破坏该机制的抗审查性保证。

**修復建議：**
在 `applyStateChanges` 中移除对 `ForcedWithdrawalRequest` 条目的删除操作。`finalizeForceWithdrawal` 应基于用户当前余额而非发起时的缓存余额执行提款，确保余额变化时待处理请求不被删除。

---

## 14. Withdrawal queue RequestPrice can be front run in case of defaults

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
When `processingMode == ProcessingMode.RequestPrice` in `AccountableWithdrawalQueue`, a redeem request's value is fixed at the request-time share price, regardless of the price at which it is eventually processed. In normal operation, requesters are typically disadvantaged because the price usually rises as interest accrues, meaning locking in a request-time price forfeits subsequent gains. More critically, in a default scenario, informed requesters can front-run the delinquency or default event by submitting withdrawal requests just before it occurs, locking in the pre-default (higher) price. This allows them to drain liquidity at the higher price, pushing losses onto remaining liquidity providers.

**Impact:**
Front-running a default with a withdrawal request at `RequestPrice` mode allows sophisticated actors to extract value at the pre-default share price, worsening loss socialization at precisely the moment fairness matters most for the remaining depositors.

**Recommended Mitigation:**
Remove `ProcessingMode.RequestPrice` and the associated `processingMode` configuration entirely so that redemption value is always determined at processing time. Alternatively implement a safeguard for large price movements that invalidates redeem requests created when the share price was significantly higher than the current processing price.

---

**[中文版本]**

**描述：**
当 `AccountableWithdrawalQueue` 处于 `ProcessingMode.RequestPrice` 模式时，赎回请求的价值在请求发起时即被锁定，与最终处理时的价格无关。在正常操作中，请求者通常处于不利地位（因利息累计价格上涨，锁定请求时价格意味着错失后续收益）。更危险的是，在违约场景下，知情请求者可以在违约发生前抢先提交提款请求，锁定违约前（较高）的价格，以较高价格耗尽流动性，将损失转嫁给剩余流动性提供者。

**影響：**
在 `RequestPrice` 模式下通过抢先交易在违约前提交提款请求，使成熟参与者能以违约前的份额价格提取价值，在最需要公平损失分担的时刻加剧了损失集中化。

**修復建議：**
完全移除 `ProcessingMode.RequestPrice` 及相关的 `processingMode` 配置，使赎回价值始终在处理时确定。或者实现大幅价格波动保护机制，使在份额价格显著高于当前处理价格时创建的赎回请求自动失效。
