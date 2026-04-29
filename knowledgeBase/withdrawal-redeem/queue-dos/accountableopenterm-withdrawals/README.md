# accountableopenterm-withdrawals (11)

> Issues in AccountableOpenTerm and related vault withdrawal flows — cancellation races, period changes, and stuck funds.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Mechanism to prevent donation attack can be gamed to cause withdrawals to revert causing assets to get stuck on the Strategy

**Severity:** 🟠 High
**Source:** `cyfrin/tranches.md`

**Description:**
Each time a withdrawal occurs from a Tranche, a check is performed to ensure that TrancheShares `totalSupply()` does not fall below a pre-defined boundary (`MIN_SHARES`). However, this mechanism can be gamed using a classic donation attack. An attacker donates sUSDe directly to the Strategy contract, which inflates `totalAssets` in the system. The attacker then makes a small deposit (for example 1.1 USDe), which causes the share-to-assets exchange rate to be heavily manipulated — for that 1.1e18 USDe deposit, the Tranche mints only 1 wei of shares. As a result, all subsequent deposits also mint shares at the manipulated rate. The problem arises during withdrawals because `_onAfterWithdrawalChecks()` requires `totalSupply() >= MIN_SHARES`. Since subsequent deposits mint only dust amounts of shares, the remaining `totalSupply()` after any withdrawal will not exceed `MIN_SHARES`, causing all withdrawals to revert.

**Impact:**
The withdrawal mechanism can be completely broken, causing all user-deposited assets to become irretrievably stuck on the Strategy contract until the attacker's manipulation is reversed.

**Recommended Mitigation:**
Implement a soft limit on donations or track the share-to-assets ratio to detect abnormal inflation. Consider requiring a minimum amount of shares to be minted per deposit, and validate the exchange rate against a maximum deviation threshold to make share-price manipulation attacks economically infeasible.

---

**[中文版本]**

**描述：**
每次从 Tranche 提款时，系统会检查 TrancheShares 的 `totalSupply()` 是否低于预设边界（`MIN_SHARES`）。然而，攻击者可通过经典捐款攻击绕过此机制：向 Strategy 合约直接捐款 sUSDe 以膨胀 `totalAssets`，再以少量 USDe（如 1.1 USDe）存款，使份额-资产兑换率被大幅操纵——1.1e18 USDe 存款仅铸造 1 wei 份额。此后所有存款均以被操纵的兑换率铸造份额，提款时 `_onAfterWithdrawalChecks()` 要求 `totalSupply() >= MIN_SHARES`，但由于存款只能铸造少量份额，提款后剩余 `totalSupply()` 无法超过 `MIN_SHARES`，导致所有提款回滚。

**影響：**
提款机制被完全破坏，所有用户存入的资产将被永久困在 Strategy 合约中，直到攻击者的操纵被逆转为止。

**修復建議：**
对捐款实施软限制或追踪份额-资产比率以检测异常膨胀。考虑要求每次存款铸造最低数量的份额，并验证兑换率不超过最大偏差阈值，使份额价格操纵攻击在经济上不可行。

---

## 2. PaymentSettler can change stablecoin but RemoraToken can't resulting in corrupted state with DoS for core functions

**Severity:** 🟠 High
**Source:** `cyfrin/pledge.md`

**Description:**
`RemoraToken` has a `stablecoin` member with a comment indicating it must match `PaymentSettler`. However, in the updated code there is no way to update `RemoraToken::stablecoin` — previously `DividendManager` (which `RemoraToken` inherits from) had a `changeStablecoin` function, but this was commented out when `PaymentSettler` was introduced. Meanwhile `PaymentSettler` retains a `changeStablecoin(address newStablecoin)` function callable by restricted roles. When `PaymentSettler` changes its stablecoin, it immediately diverges from `RemoraToken::stablecoin`, which cannot be updated. Functions in `RemoraToken` that reference `stablecoin` for token transfers or approvals will now use a stale address, causing core transfer and payout functions that depend on consistent stablecoin state across both contracts to revert.

**Impact:**
When `PaymentSettler` changes its stablecoin, the resulting state inconsistency causes key functions in `RemoraToken` to revert, including token transfer fee settlement and payout processing, producing a protocol-wide DoS for all holders until the inconsistency is corrected.

**Recommended Mitigation:**
Enforce that `RemoraToken` and `PaymentSettler` always reference the same stablecoin. The simplest solution is to remove `stablecoin` from `RemoraToken` entirely and have `PaymentSettler` perform all necessary stablecoin transfers, so there is only one source of truth.

---

**[中文版本]**

**描述：**
`RemoraToken` 有一个 `stablecoin` 成员，注释说明其必须与 `PaymentSettler` 保持一致。但在更新后的代码中，无法更新 `RemoraToken::stablecoin`——之前 `DividendManager`（`RemoraToken` 继承自该合约）有一个 `changeStablecoin` 函数，但在引入 `PaymentSettler` 时被注释掉了。与此同时，`PaymentSettler` 仍保留了受限角色可调用的 `changeStablecoin(address newStablecoin)` 函数。当 `PaymentSettler` 更换稳定币时，其状态立即与无法更新的 `RemoraToken::stablecoin` 产生偏差，导致 `RemoraToken` 中引用 `stablecoin` 的转账和授权操作使用过时地址，核心函数回滚。

**影響：**
当 `PaymentSettler` 更换稳定币后，状态不一致导致 `RemoraToken` 中的关键函数（包括代币转账费用结算和支出处理）回滚，对所有持有人产生全协议级别的 DoS，直至不一致被纠正。

**修復建議：**
强制 `RemoraToken` 和 `PaymentSettler` 始终引用同一稳定币。最简单的解决方案是从 `RemoraToken` 中完全移除 `stablecoin`，让 `PaymentSettler` 负责所有必要的稳定币转账，形成单一数据源。

---

## 3. Cancelling a later-batch request in AccountableOpenTerm can delay earlier withdrawals

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
The Vault allows cancelling any queued redeem request via `AccountableAsyncRedeemVault::cancelRedeemRequest(controller, receiver)`. To keep batching metadata in sync, the Vault calls the strategy hook `AccountableOpenTerm::onCancelRedeemRequest`. However, the strategy reduces batch totals starting from `pendingBatch` (the oldest batch) and walks forward, without knowing which batch the cancelled request actually belonged to. If a user cancels a request that was created in a later batch, this logic subtracts the cancelled shares from the earliest batch's `totalShares`. That makes `pendingBatch.totalShares` smaller than the actual FIFO-queued shares at the head of the Vault queue. During processing, the strategy limits processing by `min(queueMaxShares, batch.totalShares)` and stops once it reaches the next not-yet-expired batch. The result is that earlier-batch shares that were supposed to be processed are understated, causing processing to advance to a future batch and leaving earlier-batch shares stranded.

**Impact:**
Queued withdrawals that should be eligible (earlier batch already expired and liquidity exists) can be artificially delayed until a later batch expires, because the strategy advances to a future batch while some earlier-batch shares still remain in the queue head. This degrades withdrawal liveness and creates unexpected waiting periods for lenders.

**Recommended Mitigation:**
Ensure cancellations decrement the correct batch. Track the batch ID for each redeem request at queue time and subtract from that specific batch upon cancellation, rather than walking from the oldest batch forward.

---

**[中文版本]**

**描述：**
金库允许通过 `AccountableAsyncRedeemVault::cancelRedeemRequest` 取消任何排队的赎回请求。为保持批次元数据同步，金库调用策略钩子 `AccountableOpenTerm::onCancelRedeemRequest`。但策略从 `pendingBatch`（最旧批次）开始向前递减批次总量，而不知道被取消的请求实际属于哪个批次。若用户取消了较新批次中的请求，该逻辑会从最旧批次的 `totalShares` 中减去已取消的份额，导致 `pendingBatch.totalShares` 小于队列头部实际排队的份额数量。处理时，策略按 `min(queueMaxShares, batch.totalShares)` 限制处理量，并在到达未到期批次时停止，导致早批次份额被少计，处理提前跳转至未来批次，早批次份额滞留。

**影響：**
本应符合条件的排队提款（早批次已到期且存在流动性）可能被人为延迟至更晚批次到期，降低提款活跃度，给贷款方带来意外等待期。

**修復建議：**
确保取消操作递减正确的批次。在请求入队时追踪批次 ID，取消时从该特定批次中减去份额，而非从最旧批次向前遍历。

---

## 4. Delinquency status update in AccountableOpenTerm hooks uses pre-queue state

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
The Vault calls strategy hooks (such as `AccountableStrategy::onRequestRedeem`, `onDeposit`, `onMint`) before the Vault updates the state that these actions affect — queue totals for redeem requests, and `totalAssets` or liquidity for deposits and mints. However, `AccountableOpenTerm` updates delinquency status inside these hooks. As a result, delinquency calculations that depend on Vault-side values (queued shares, available liquidity derived from `totalAssets`, `reservedLiquidity`, `totalQueuedShares`, etc.) are evaluated using a pre-action snapshot. For `onRequestRedeem`, delinquency is checked before the new queued shares are reflected. For `onDeposit` and `onMint`, delinquency is checked before the new liquidity from the deposit or mint is reflected.

**Impact:**
Delinquency status may lag by one interaction. A queued redeem may not immediately mark the loan delinquent, and a deposit or mint that would restore liquidity may not immediately clear delinquency. This is primarily a correctness and timing issue, but it can affect monitoring and automation that relies on delinquency state being accurate immediately after rate changes.

**Recommended Mitigation:**
Consider passing the changes in shares and assets to the delinquency calculation so that it can account for the added or removed shares and assets. Alternatively, use the same pattern as `Vault::cancelRedeemRequest` where `strategy.updateLateStatus()` is called at the end of the function after all state changes are complete.

---

**[中文版本]**

**描述：**
金库在更新受操作影响的状态（赎回请求的队列总量，以及存款和铸造的 `totalAssets` 或流动性）之前调用策略钩子（如 `AccountableStrategy::onRequestRedeem`、`onDeposit`、`onMint`）。但 `AccountableOpenTerm` 在这些钩子内部更新逾期状态，导致依赖金库侧数值（排队份额、来自 `totalAssets`、`reservedLiquidity`、`totalQueuedShares` 的可用流动性等）的逾期计算使用操作前的快照。对于 `onRequestRedeem`，逾期检查在新排队份额反映之前进行；对于 `onDeposit` 和 `onMint`，逾期检查在新流动性反映之前进行。

**影響：**
逾期状态可能滞后一次交互——排队赎回可能不会立即将贷款标记为逾期，存款或铸造恢复流动性也可能不会立即清除逾期状态。这主要是正确性和时机问题，但会影响依赖利率变更后即时准确逾期状态的监控和自动化系统。

**修復建議：**
考虑将份额和资产的变化传递给逾期计算，使其能够考虑新增或移除的份额和资产。或采用与 `Vault::cancelRedeemRequest` 相同的模式，在所有状态变更完成后于函数末尾调用 `strategy.updateLateStatus()`。

---

## 5. Fees can become stuck in UniswapV4Wrapper

**Severity:** 🟡 Medium
**Source:** `cyfrin/vii.md`

**Description:**
When a modification is made to a Uniswap V4 position's liquidity (such as during a partial `UniswapV4Wrapper` unwrap), any outstanding fees are transferred and required to be completely settled. For multiple holders of a given ERC-6909 `tokenId`, a proportional share is escrowed in the wrapper and paid out during each holder's next interaction. However, there is an edge case in which fees can become permanently stuck in `UniswapV4Wrapper`. Consider the following scenario: Alice has full ownership of a position and partially unwraps it to remove some liquidity, which causes LP fees for the remainder to be escrowed in the wrapper. Alice then gets fully liquidated. The liquidator receives the underlying NFT via full unwrap but loses their share of the previously-accrued escrowed fees. The liquidator removes all liquidity and burns the position. Because the original position is burnt and a new mint of the same `tokenId` is impossible, the fees remaining in the wrapper can never be retrieved.

**Impact:**
LP fees can become permanently stuck in the `UniswapV4Wrapper` contract whenever the final holder performs a full unwrap through the direct-transfer overload after a partial unwrap has escrowed fees. The loss represents medium-to-high impact with medium likelihood, particularly in liquidation scenarios.

**Recommended Mitigation:**
When the final holder performs a full unwrap, ensure any remaining escrowed fees in the `tokensOwed` mapping are distributed to the unwrapper before transferring the underlying position. Alternatively, add a mechanism to flush escrowed fees to the final holder during the full-unwrap path.

---

**[中文版本]**

**描述：**
对 Uniswap V4 仓位流动性进行修改时（如部分 `UniswapV4Wrapper` 解包），任何未结算费用都会被转移并要求完全结算。对于同一 ERC-6909 `tokenId` 的多个持有人，比例份额会被托管在包装合约中，在每个持有人下次交互时支付。但存在一种费用可能永久卡在 `UniswapV4Wrapper` 中的边界情况：Alice 部分解包仓位移除部分流动性，剩余仓位的 LP 费用被托管在包装合约中；Alice 随后被全额清算，清算方通过完整解包获得底层 NFT，但损失了之前托管的费用份额；清算方移除所有流动性并销毁仓位。由于原始仓位已被销毁且无法重新铸造同一 `tokenId`，包装合约中剩余的费用永远无法取回。

**影響：**
在部分解包已托管费用后，最终持有人通过直接转账重载执行完整解包时，LP 费用可能永久卡在 `UniswapV4Wrapper` 合约中，尤其在清算场景中影响程度为中高，发生概率为中等。

**修復建議：**
当最终持有人执行完整解包时，确保 `tokensOwed` 映射中任何剩余的托管费用在转移底层仓位之前分配给解包方。或添加机制在完整解包路径中将托管费用清算给最终持有人。

---

## 6. In pUSDeDepositor::deposit_viaSwap, using block.timestamp in swap deadline is not very effective

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
In `pUSDeDepositor::deposit_viaSwap`, the swap deadline is set to `block.timestamp`. Using `block.timestamp` as a deadline is ineffective because `block.timestamp` is evaluated at the time the transaction is included in a block, not when the user signs and submits the transaction. This means the deadline is always set to "now" at execution time and can never expire in the conventional sense. A transaction that sits in the mempool for an extended period — even days or weeks — will still pass the deadline check the moment it is eventually mined. The purpose of a swap deadline is to allow users to set a maximum acceptable age for their transaction, protecting them from executing a swap under market conditions that have significantly changed from when they submitted it.

**Impact:**
Users have no protection against stale swap execution. A deposit-via-swap transaction sitting in the mempool for hours or days will still execute when eventually included, potentially at a much worse exchange rate than when the user submitted the transaction. This exposes users to unexpected slippage and market movement risk.

**Recommended Mitigation:**
Retrieve the desired deadline off-chain and pass it as an explicit input parameter to the swap transaction. Allow callers to override the default swap deadline so they can express a meaningful expiry based on when they submitted the transaction.

---

**[中文版本]**

**描述：**
在 `pUSDeDepositor::deposit_viaSwap` 中，互换截止时间被设置为 `block.timestamp`。使用 `block.timestamp` 作为截止时间实际上无效，因为 `block.timestamp` 在交易被打包进区块时才被评估，而非用户签署并提交交易时。这意味着截止时间始终被设为执行时的"当下"，从常规意义上永远不会过期。一笔在内存池中滞留数天或数周的交易，在最终被打包时仍能通过截止时间检查。互换截止时间的目的是允许用户设置交易可接受的最大"过期时间"，保护用户免于在与提交时相比市场条件已大幅变化的情况下执行互换。

**影響：**
用户对过期互换执行毫无防护。一笔在内存池中滞留数小时或数天的存款交互交易，最终被打包时仍会执行，可能以远差于用户提交时的汇率进行互换，使用户面临意外滑点和市场波动风险。

**修復建議：**
在链下获取期望的截止时间，并作为显式输入参数传递给互换交易，允许调用方覆盖默认互换截止时间，以便基于提交时间表达有意义的过期设置。

---

## 7. Inability to remove and redeem from vaults with withdrawal issues could result in a bank-run

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
When deposits are made to `pUSDeVault`, `depositedBase` is incremented based on the previewed quote amount of USDe underlying the external ERC-4626 vaults. However, per ERC-4626 specification, preview functions must not account for withdrawal limits like `maxWithdraw` or `maxRedeem`, so the previewed value could be larger than the actually withdrawable amount. The `depositedBase` state is therefore incremented assuming the underlying USDe is fully redeemable, but the actual redeemability is only tested when removing and redeeming from the vault. Currently, the only way to pause new deposits for a given vault is to remove the asset from the supported list, but this also triggers a full withdrawal of USDe, which can fail if the third-party vault malfunctions or restricts withdrawals. This prevents the asset from ever being removed. Combined with the fact that users can freely withdraw into any supported vault token regardless of which they supplied, other users draining unaffected vaults via `redeemRequiredBaseAssets` could leave a subset of users holding only bad debt from the malfunctioning vault.

**Impact:**
The inability to remove and redeem from vaults with withdrawal issues could trigger a bank-run where a subset of users are left with un-redeemable tokens backed only by assets in a compromised or malfunctioning vault.

**Recommended Mitigation:**
Implement a mechanism to disable new deposits to a vault without having to remove it and immediately redeem the underlying tokens. To amortize any losses from a faulty vault, track individual vault contributions to `depositedBase` so they can be accounted for separately in redemption calculations.

---

**[中文版本]**

**描述：**
向 `pUSDeVault` 存款时，`depositedBase` 基于外部 ERC-4626 金库底层 USDe 的预览报价增量。但按 ERC-4626 规范，预览函数不得考虑 `maxWithdraw` 或 `maxRedeem` 等提款限制，因此预览值可能大于实际可提取量。`depositedBase` 状态以假定底层 USDe 完全可赎回的方式递增，但实际可赎回性仅在移除并赎回金库时才得到验证。目前，暂停特定金库新存款的唯一方式是将该资产从支持列表中移除，但这也会触发 USDe 的完全提款，若第三方金库出现故障或限制提款则会失败，导致资产永远无法被移除。结合用户可自由向任何受支持金库代币提款的特性，其他用户通过 `redeemRequiredBaseAssets` 耗尽正常金库的行为可能使部分用户只剩下故障金库的坏账。

**影響：**
无法从有提款问题的金库中移除和赎回，可能引发银行挤兑，使部分用户持有的代币只有故障或受损金库资产作为支撑，无法赎回。

**修復建議：**
实施机制以禁用特定金库的新存款而无需立即移除并赎回底层代币。为摊销故障金库的损失，追踪各金库对 `depositedBase` 的单独贡献，以便在赎回计算中分别核算。

---

## 8. Increasing AccountableOpenTerm.loan.withdrawalPeriod from 0 can cause withdrawals to become stuck

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
When `LoanTerms.withdrawalPeriod == 0`, `AccountableOpenTerm::_createOrAddWithdrawalBatch` returns immediately and does not create or update any batch metadata. However, users can still end up queued (for example when insufficient liquidity prevents immediate fulfillment of `requestRedeem`). If loan terms are later updated to a non-zero `withdrawalPeriod`, `_processAvailableWithdrawals` switches into batch mode and processes shares bounded by `WithdrawalBatch.totalShares`. Queued shares accumulated while `withdrawalPeriod == 0` have no corresponding batch metadata, meaning batch-mode processing finds nothing to process for those requests and skips them. The stuck withdrawals remain in the queue but cannot advance until someone takes manual corrective action.

**Impact:**
Queued withdrawals created while `withdrawalPeriod == 0` can become stuck or perceived as stuck after the term is changed to `withdrawalPeriod > 0`, because batch-mode processing depends on batch metadata that was never created for those queued shares. This leads to delayed withdrawals and requires operational intervention or term toggling to recover.

**Recommended Mitigation:**
Either disallow increases to `withdrawalPeriod` when there are still queued shares, or when transitioning from `withdrawalPeriod == 0` to `withdrawalPeriod > 0`, initialize batch metadata for the currently queued shares so they are covered by the new batch processing logic.

---

**[中文版本]**

**描述：**
当 `LoanTerms.withdrawalPeriod == 0` 时，`AccountableOpenTerm::_createOrAddWithdrawalBatch` 立即返回，不创建或更新任何批次元数据。但用户仍可能因流动性不足无法即时完成 `requestRedeem` 而排队。若贷款条款后来更新为非零的 `withdrawalPeriod`，`_processAvailableWithdrawals` 切换为批次模式，按 `WithdrawalBatch.totalShares` 限制处理份额。在 `withdrawalPeriod == 0` 期间积累的排队份额没有对应批次元数据，批次模式处理找不到可处理的内容而跳过它们，这些滞留的提款留在队列中但无法推进，直到有人手动干预。

**影響：**
在 `withdrawalPeriod == 0` 期间创建的排队提款在条款更改为 `withdrawalPeriod > 0` 后可能卡死或被认为已卡死，因为批次模式处理依赖于这些排队份额从未创建过的批次元数据，导致提款延迟并需要运营干预或条款切换才能恢复。

**修復建議：**
当存在排队份额时禁止增加 `withdrawalPeriod`；或在从 `withdrawalPeriod == 0` 过渡到 `withdrawalPeriod > 0` 时，为当前排队份额初始化批次元数据，确保其受新批次处理逻辑覆盖。

---

## 9. Negative yield never accounted in YieldManager::_getTotalSystemBalance can result in temporary DoS

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`YieldManager::reportYield` receives `outstandingNegativeYield` from providers but only emits an event without decrementing `$$.userFunds`. While intentional (`$$.userFunds` is a liability ledger, not an asset tracker), the negative yield is not accounted for anywhere. As a result, `_getTotalSystemBalance` returns inflated values by summing `L1_MESSAGE_SERVICE.balance`, `address(this).balance`, and `$.userFundsInYieldProvidersTotal` without deducting outstanding negative yield. This inflated balance is used to calculate reserve thresholds, producing incorrect operational decisions after slashing events.

**Impact:**
After slashing events, inflated `_getTotalSystemBalance` causes incorrect reserve threshold calculations. Operations that should be permitted are incorrectly blocked: `receiveFundsFromReserve` cannot receive funds even when the reserve is sufficient, `fundYieldProvider` cannot stake funds, and `unpauseStaking` cannot resume staking. Conversely, `unstakePermissionless` may be allowed when the reserve is actually adequate, and `replenishWithdrawalReserve` may attempt replenishment unnecessarily. All impacts are temporary until positive yield normalizes accounting.

**Recommended Mitigation:**
Store the individual yield provider `outstandingNegativeYield` in `YieldProviderStorage` and incorporate it into the relevant balance checks in `YieldManager::withdrawLST` and `YieldManager::withdrawableValue` to return more accurate figures.

---

**[中文版本]**

**描述：**
`YieldManager::reportYield` 从提供方接收 `outstandingNegativeYield`，但仅触发事件而不递减 `$$.userFunds`。虽然这是有意为之（`$$.userFunds` 是负债账本而非资产追踪），但负收益没有在任何地方被计入，导致 `_getTotalSystemBalance` 在累加 `L1_MESSAGE_SERVICE.balance`、`address(this).balance` 和 `$.userFundsInYieldProvidersTotal` 时不扣除未偿负收益，返回膨胀值，用于计算储备阈值，在削减事件后产生错误的运营决策。

**影響：**
削减事件后，膨胀的 `_getTotalSystemBalance` 导致储备阈值计算错误：应允许的操作被错误阻止（`receiveFundsFromReserve` 无法接收资金，`fundYieldProvider` 无法质押资金，`unpauseStaking` 无法恢复质押）；应禁止的操作被错误允许（`unstakePermissionless` 在储备充足时允许解押，`replenishWithdrawalReserve` 不必要地尝试补充）。所有影响在正收益恢复正常核算前均为临时性的。

**修復建議：**
将各收益提供方的 `outstandingNegativeYield` 存储在 `YieldProviderStorage` 中，并在 `YieldManager::withdrawLST` 的 `LSTWithdrawalExceedsYieldProviderFunds` 检查和 `YieldManager::withdrawableValue` 中加以考虑，以返回更准确的数值。

---

## 10. Vester template misconfiguration can potentially block token claims

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The `WorldLibertyFinancialVester` contract can make user tokens temporarily inaccessible when template `capPerUser` values do not sum to the user's total allocation. Users transfer their full allocation to the vester during activation, but can only claim back the portion covered by template caps. In `_unlockedTotal`, the loop reduces `remainingCap` by each template's `capPerUser` rather than by the allocation itself. If the total of all template `capPerUser` values is less than the user's allocation, the remaining allocation is silently ignored and becomes uncollectable by the user. There is no validation ensuring template caps cover the full user allocation, and the contract's design allows the owner to add or modify templates at any time without requiring that existing allocations are fully covered.

**Impact:**
If the contract owner incorrectly configures or modifies the template user cap such that the sum of caps does not equal or exceed a user's full allocation, the user cannot claim the uncovered portion of their tokens inside the Vester contract until the owner adds additional templates or increases existing cap values.

**Recommended Mitigation:**
Add documentation and validation requiring that template caps cover expected user allocations. Consider making it mandatory to include a remainder template as the last template in every category, which would capture any allocation not covered by earlier templates. Alternatively, add inline validation when activating a vest to verify that the total template cap at least equals the user's allocation.

---

**[中文版本]**

**描述：**
当模板 `capPerUser` 值之和不等于用户总分配量时，`WorldLibertyFinancialVester` 合约可能使用户代币暂时无法访问。用户在激活时将全部分配量转入 vester，但只能取回模板上限覆盖的部分。在 `_unlockedTotal` 中，循环按每个模板的 `capPerUser` 递减 `remainingCap` 而非按分配量递减。若所有模板 `capPerUser` 之和小于用户分配量，剩余分配量将被静默忽略，用户无法领取。系统对模板上限必须覆盖全部用户分配量没有任何验证，且合约设计允许所有者随时添加或修改模板，而不要求现有分配量被完全覆盖。

**影響：**
若合约所有者配置或修改模板用户上限时使上限总和未能达到或超过用户的全部分配量，用户将无法领取 Vester 合约内未被覆盖部分的代币，直到所有者添加更多模板或增加现有上限值。

**修復建議：**
添加文档和验证，要求模板上限覆盖预期的用户分配量。考虑强制要求每个类别的最后一个模板为余量模板，以捕获早期模板未覆盖的任何分配量。或在激活归属时添加内联验证，确认模板总上限至少等于用户分配量。

---

## 11. feeAmount never set when no vault adapter used in SablierBob::redeem

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
When no vault adapter is used in `SablierBob::redeem`, the output variable `feeAmount` is never assigned even though the user does pay a fee as `msg.value` and `feeAmount` is both returned as an output variable and emitted in the `Redeem` event. The code paths that handle adapter vaults correctly assign `feeAmount` from the adapter's fee deduction logic, but the non-adapter path simply processes the redemption without setting `feeAmount`. The emitted `Redeem` event and the returned value therefore always show zero for `feeAmount` in non-adapter redemptions, creating a discrepancy between the actual fee paid by the user and the fee amount recorded on-chain.

**Impact:**
The `Redeem` event emits an inaccurate `feeAmount` of zero for all non-adapter vault redemptions, even when the user paid `msg.value` as a fee. Any off-chain monitoring, analytics, or fee accounting that relies on this event will report incorrect fee data. The misleading event data can lead to revenue tracking errors or disputes about fees charged.

**Recommended Mitigation:**
Assign `feeAmount` in the non-adapter code path of `SablierBob::redeem` to reflect the fee actually paid by the user. The variable name should be updated to make it clear whether it represents fees deducted from yield (adapter path) or fees paid as ETH (non-adapter path). Alternatively, rename the variable to `feeAmountDeductedFromYield` to make its scope explicit and add a separate field for ETH fees.

---

**[中文版本]**

**描述：**
当 `SablierBob::redeem` 没有使用金库适配器时，即使用户以 `msg.value` 支付了费用，且 `feeAmount` 既作为输出变量返回又在 `Redeem` 事件中触发，该输出变量也永远不会被赋值。处理适配器金库的代码路径正确地从适配器的费用扣除逻辑中赋值 `feeAmount`，但非适配器路径只处理赎回而不设置 `feeAmount`。因此，非适配器赎回中触发的 `Redeem` 事件和返回值始终显示 `feeAmount` 为零，造成用户实际支付的费用与链上记录的费用金额之间的差异。

**影響：**
即使用户支付了 `msg.value` 作为费用，所有非适配器金库赎回的 `Redeem` 事件都会触发不准确的零 `feeAmount`。任何依赖此事件的链下监控、分析或费用核算都将报告错误的费用数据，可能导致收入追踪错误或费用争议。

**修復建議：**
在 `SablierBob::redeem` 的非适配器代码路径中赋值 `feeAmount` 以反映用户实际支付的费用。应更新变量名以明确其表示的是从收益中扣除的费用（适配器路径）还是以 ETH 支付的费用（非适配器路径）。或将变量重命名为 `feeAmountDeductedFromYield` 以明确其适用范围，并为 ETH 费用添加单独字段。
