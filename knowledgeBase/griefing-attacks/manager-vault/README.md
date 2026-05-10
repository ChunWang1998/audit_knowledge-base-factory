# manager-vault (9)

> Issues in fee manager and vault manager contracts — naming, configuration, and calculation inconsistencies.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Confusing variable naming in fee manager contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
In `MbpsFeeManager`, the variable named `fee` actually represents a fee percentage expressed in milli basis points (MBPS), not an absolute fee amount. The inline comment clarifies "Fee expressed in mbps (1000 mbps = 1%)" and the calculation formula confirms `fee` is used as a rate, yet the variable name `fee` strongly implies an actual monetary amount to most developers. The exposed `getFee(uint256 amount)` function further compounds the confusion because the word "fee" in its return context implies an amount, not a rate.

**Impact:**
Integrators or developers who read `fee` as an amount rather than a percentage rate may introduce fee calculation errors in downstream contracts. Misconfigured integrations could charge incorrect fees or produce unintended economic outcomes.

**Recommended Mitigation:**
Rename the variable from `fee` to `feeMBPS` (or `feePercentageMBPS` for additional clarity) across all fee manager contracts to clearly communicate its semantics as a percentage rate denominated in milli basis points.

---

**[中文版本]**

**描述：**
在 `MbpsFeeManager` 中，名为 `fee` 的变量实际上表示以毫基点（MBPS）表示的费率百分比，而非绝对费用金额。内联注释明确说明"费用以 mbps 表示（1000 mbps = 1%）"，计算公式也证实 `fee` 被用作比率，但变量名 `fee` 对大多数开发者而言强烈暗示其为实际货币金额。暴露的 `getFee(uint256 amount)` 函数进一步加剧了混淆，因为其返回上下文中的"fee"暗示是金额而非比率。

**影響：**
将 `fee` 读作金额而非百分比比率的集成商或开发者可能在下游合约中引入费用计算错误。配置错误的集成可能收取不正确的费用或产生意外的经济后果。

**修復建議：**
将所有费用管理合约中的变量从 `fee` 重命名为 `feeMBPS`（或 `feePercentageMBPS` 以获得更清晰的表达），以明确传达其作为以毫基点计价的百分比比率的语义。

---

## 2. Early Cancel Fee Applied on Depositor-Triggered Timeouts

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
`_settleSessionPayments` applies the early cancellation fee whenever `completedBy == session.depositor && session.proofs.length == 0 && minTokensFee > 0`. This same logic is shared by both `completeSessionJob` (voluntary cancellation) and `triggerSessionTimeout` (forced termination due to host inactivity). When the depositor calls `triggerSessionTimeout` because a host failed to submit any proof within the `proofTimeoutWindow`, the condition evaluates to true and the early cancellation fee is incorrectly charged to the depositor and forwarded to the inactive host. The early cancel fee should penalize depositors who abandon sessions, not depositors who are forced to time out a non-performing host.

**Impact:**
Depositors who legitimately trigger a timeout against a host that provided no service are penalized with the early cancellation fee. This inverts the economic incentive: inactive hosts are rewarded with a fee for their non-performance, while depositors bear a financial loss for enforcing the timeout.

**Recommended Mitigation:**
Distinguish between the two termination paths in `_settleSessionPayments`. Only apply the early cancellation fee when the session is terminated via `completeSessionJob` (voluntary cancellation by depositor), not when it is terminated via `triggerSessionTimeout`.

---

**[中文版本]**

**描述：**
`_settleSessionPayments` 在 `completedBy == session.depositor && session.proofs.length == 0 && minTokensFee > 0` 时应用提前取消费用。`completeSessionJob`（主动取消）和 `triggerSessionTimeout`（因主机不活跃导致的强制终止）共享相同的逻辑。当存款人因主机在 `proofTimeoutWindow` 内未提交任何证明而调用 `triggerSessionTimeout` 时，该条件评估为 true，导致提前取消费用被错误地从存款人处收取并转发给不活跃的主机。提前取消费用应惩罚放弃会话的存款人，而非被迫对不履职主机执行超时的存款人。

**影響：**
合法地对未提供服务的主机触发超时的存款人被错误地收取了提前取消费用。这颠倒了经济激励：不活跃的主机因不履职而获得奖励，存款人则因执行超时而蒙受财务损失。

**修復建議：**
在 `_settleSessionPayments` 中区分两种终止路径。仅在通过 `completeSessionJob`（存款人主动取消）终止会话时应用提前取消费用，而非通过 `triggerSessionTimeout` 终止时。

---

## 3. FeeModule::setMarketFees permits 100% fee rates

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`FeeModule::setMarketFees` validates individual fee rates only against the maximum value of `BPS` (10,000 basis points = 100%). This allows the `FEE_ADMIN` to configure `makerFeeBps = 10000` and `takerFeeBps = 10000`, meaning a seller would receive zero proceeds from a match and a buyer would pay double the notional value (all proceeds going to fees). Even without malicious intent, misconfiguration by entering basis point values instead of the intended percentages could produce catastrophic fee rates.

**Impact:**
A fee admin with malicious or mistaken intent can configure fee tiers that make trading economically non-viable. Traders would receive nothing while all funds are extracted as fees, effectively shutting down the exchange for any affected market.

**Recommended Mitigation:**
Introduce a protocol-level maximum fee constant (e.g., `MAX_FEE_BPS = 500` for 5%) and enforce it in the validation check. Make this constant configurable by `DEFAULT_ADMIN_ROLE` through a separate governance process.

---

**[中文版本]**

**描述：**
`FeeModule::setMarketFees` 仅将各个费率与 `BPS` 的最大值（10,000 基点 = 100%）进行验证。这允许 `FEE_ADMIN` 将 `makerFeeBps = 10000` 和 `takerFeeBps = 10000`，意味着卖方从成交中获得零收益，买方支付名义价值的两倍（所有收益都作为费用）。即使没有恶意意图，因误将基点值输入为预期百分比而导致的错误配置也可能产生灾难性的费率。

**影響：**
具有恶意或错误意图的费用管理员可以配置使交易在经济上不可行的费用层级。交易者将一无所获，而所有资金都被提取为费用，实际上关闭了任何受影响市场的交易所。

**修復建議：**
引入协议级最大费用常量（例如，`MAX_FEE_BPS = 500` 对应 5%），并在验证检查中强制执行。通过单独的治理流程使此常量可由 `DEFAULT_ADMIN_ROLE` 配置。

---

## 4. In zero-fee case, flashloan can result in a few wei profit

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
When the flash loan fee is zero, a rounding discrepancy in `LibHelpers::convertDecimalsTo` (which favors the user on exact-out mint and burn operations for certain collateral decimal configurations) allows a flash loan to return slightly more than was borrowed. Over repeated executions, this allows an attacker to extract small but non-zero amounts of value from the protocol at essentially zero cost.

**Impact:**
Each zero-fee flashloan iteration can extract a few wei of value. While individually tiny, this can be executed in loops to drain small amounts of collateral from the protocol, and represents a violation of the invariant that a zero-fee flashloan should always be neutral for the protocol.

**Recommended Mitigation:**
Fix the rounding direction in `LibHelpers::convertDecimalsTo` to always round in favor of the protocol (round down for exact-out operations), ensuring that the protocol never loses value in a zero-fee flashloan scenario.

---

**[中文版本]**

**描述：**
当闪电贷费用为零时，`LibHelpers::convertDecimalsTo` 中的舍入误差（在某些抵押品小数位配置下，精确输出铸造和销毁操作有利于用户）允许闪电贷返还的金额略多于借入金额。通过重复执行，这使攻击者能够以几乎零成本从协议中提取少量价值。

**影響：**
每次零费率闪电贷迭代都可以提取几个 wei 的价值。虽然单次提取金额微小，但可以循环执行以从协议中逐渐提取少量抵押品，并违反了零费率闪电贷对协议应始终中性的不变量。

**修復建議：**
修复 `LibHelpers::convertDecimalsTo` 中的舍入方向，始终向有利于协议的方向舍入（精确输出操作向下取整），确保协议在零费率闪电贷场景中永远不会损失价值。

---

## 5. Manager::_transferFee returns invalid feeShares when fee is zero

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`Manager::_transferFee` is designed to return `feeShares` — the actual number of shares transferred as fees. When `_fee == 0`, no fee transfer occurs and the function should return `0`. Instead it returns the full `_shares` input value. Downstream in `Manager::_deposit`, the returned value is subtracted from `adjustedShares` to compute `sharesAfterAllFee`. When `_fee == 0` but `_gasFeeShares > 0`, the subtraction `adjustedShares - adjustedFeeShares - adjustedGasFeeShares` causes an underflow revert because `adjustedFeeShares` equals the full share amount rather than zero.

**Impact:**
Any deposit into the `Manager` contract under a zero-fee configuration with a non-zero gas fee will always revert. This completely blocks user deposits in the zero-fee scenario, even though the protocol should be fully functional.

**Recommended Mitigation:**
Change the early return in `_transferFee` from `return _shares` to `return 0` when `_fee == 0`.

---

**[中文版本]**

**描述：**
`Manager::_transferFee` 旨在返回 `feeShares`——实际作为费用转移的份额数量。当 `_fee == 0` 时，不发生费用转移，函数应返回 `0`。但实际上它返回了完整的 `_shares` 输入值。在 `Manager::_deposit` 的下游，返回值从 `adjustedShares` 中减去以计算 `sharesAfterAllFee`。当 `_fee == 0` 但 `_gasFeeShares > 0` 时，减法 `adjustedShares - adjustedFeeShares - adjustedGasFeeShares` 因 `adjustedFeeShares` 等于完整份额量而非零导致下溢回滚。

**影響：**
在零费率配置且 gas 费非零的情况下，向 `Manager` 合约进行的任何存款都将始终回滚。这在零费率场景下完全阻止了用户存款，尽管协议本应完全正常运行。

**修復建議：**
将 `_transferFee` 中 `_fee == 0` 时的提前返回从 `return _shares` 改为 `return 0`。

---

## 6. Mismatching variable naming for Metadata.depositBlock

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
The inline documentation for `Metadata.depositBlock` describes it as storing the block number at which the deposit was created. However, the actual implementation stores `block.timestamp` (a Unix timestamp in seconds) rather than `block.number`. This naming mismatch creates a semantic disconnect that could mislead developers and off-chain systems expecting a block number into processing an incorrect value.

**Impact:**
Off-chain integrations, analytics, or future contract code that interpret `depositBlock` as a block number will process incorrect values, potentially leading to wrong time-based calculations or incorrect data displayed to users.

**Recommended Mitigation:**
Rename `Metadata.depositBlock` to `Metadata.depositTimestamp` to accurately reflect the stored value type.

---

**[中文版本]**

**描述：**
`Metadata.depositBlock` 的内联文档将其描述为存储存款创建时的区块编号。然而，实际实现存储的是 `block.timestamp`（Unix 时间戳，以秒为单位）而非 `block.number`。这种命名不匹配创造了语义上的脱节，可能误导预期区块编号的开发者和链下系统处理不正确的值。

**影響：**
将 `depositBlock` 解释为区块编号的链下集成、分析工具或未来合约代码将处理不正确的值，可能导致错误的基于时间的计算或向用户显示不正确的数据。

**修復建議：**
将 `Metadata.depositBlock` 重命名为 `Metadata.depositTimestamp`，以准确反映存储的值类型。

---

## 7. Order read twice in Manager::executeOrder

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`Manager::executeOrder` reads the `Order` struct from the `Receipt` contract via `IReceipt(receipt).readOrder(_receiptId)` to check `order.eligibleAt` and `order.orderType`. It then passes `_receiptId` to either `Manager::_deposit` or `Manager::_withdraw`, both of which immediately read the same `Order` struct again from the `Receipt` contract. This results in two external calls to the receipt contract for the same data when only one call is needed.

**Impact:**
Every order execution pays for two external calls to the `Receipt` contract instead of one, wasting gas proportional to the external call overhead on every executed order.

**Recommended Mitigation:**
Pass the already-read `Order memory order` as a parameter to both `Manager::_deposit` and `Manager::_withdraw` to eliminate the redundant second external call.

---

**[中文版本]**

**描述：**
`Manager::executeOrder` 通过 `IReceipt(receipt).readOrder(_receiptId)` 从 `Receipt` 合约读取 `Order` 结构体以检查 `order.eligibleAt` 和 `order.orderType`。然后将 `_receiptId` 传递给 `Manager::_deposit` 或 `Manager::_withdraw`，两者都会立即再次从 `Receipt` 合约读取相同的 `Order` 结构体。这导致对同一数据的 `Receipt` 合约进行两次外部调用，而实际上只需要一次。

**影響：**
每次订单执行都为两次外部调用 `Receipt` 合约付费而非一次，在每次订单执行时浪费与外部调用开销成比例的 gas。

**修復建議：**
将已读取的 `Order memory order` 作为参数传递给 `Manager::_deposit` 和 `Manager::_withdraw`，以消除冗余的第二次外部调用。

---

## 8. Shared configuration parameters across different asset types in vault deployers leads to incorrect pricing and fee calculations

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
`SecuritizeVaultDeployer` maintains shared configuration parameters — `navProvider`, `feeManager`, and `redemptionAddress` — that are applied to all deployed vaults regardless of the underlying asset type. When `SecuritizeVaultDeployer::deploy()` is called with different `assetToken` parameters to support various real-world assets, the same `navProvider` is used for all deployments. Since `navProvider.rate()` is used in `_convertToShares()`, `_convertToAssets()`, and `getShareValue()`, vaults for different assets that share the same NAV provider will produce incorrect pricing calculations for at least one of the asset types.

**Impact:**
Users depositing into vaults with incorrect NAV providers receive wrong share amounts, leading to economic losses. Attackers can exploit the misconfiguration by depositing low-value assets and receiving shares calculated using a high-value asset's NAV rate.

**Recommended Mitigation:**
Introduce per-asset-type configuration mappings (`mapping(address => address) public assetNavProviders`, etc.) and update the `deploy` function to use asset-specific parameters rather than global shared ones.

---

**[中文版本]**

**描述：**
`SecuritizeVaultDeployer` 维护共享配置参数——`navProvider`、`feeManager` 和 `redemptionAddress`——这些参数被应用于所有已部署的金库，无论底层资产类型如何。当以不同的 `assetToken` 参数调用 `SecuritizeVaultDeployer::deploy()` 以支持各种现实世界资产时，所有部署都使用相同的 `navProvider`。由于 `navProvider.rate()` 在 `_convertToShares()`、`_convertToAssets()` 和 `getShareValue()` 中使用，共享相同 NAV 提供商的不同资产金库对至少一种资产类型将产生不正确的定价计算。

**影響：**
向 NAV 提供商不正确的金库存款的用户会收到错误的份额数量，导致经济损失。攻击者可以通过存入低价值资产并以高价值资产的 NAV 比率计算收到份额来利用这一错误配置。

**修復建議：**
引入按资产类型的配置映射（如 `mapping(address => address) public assetNavProviders` 等），并更新 `deploy` 函数以使用特定于资产的参数，而非全局共享参数。

---

## 9. Vault fee distribution incorrectly incurs redemption fees

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
The original design of `vault.cairo` exempts the `fees_recipient` address from redemption fees by returning zero fees when `owner == fees_recipient`. However, in the deployed governor architecture, the `fees_recipient` is always set to the `vault_governor` contract rather than the end recipient. As a result, when the `vault_governor` calls `request_redeem` to distribute collected fees to beneficiaries, the `owner` parameter is not the `fees_recipient` address, causing the zero-fee exemption to never trigger. Fee distributions from the governor therefore incur redemption fees on top of the fees already collected.

**Impact:**
Every fee distribution call through the vault governor pays additional redemption fees, reducing the actual fees delivered to recipients. This creates an unintended double-dip on fees and increases the economic cost of protocol fee collection.

**Recommended Mitigation:**
Update the fee distribution architecture so that when the vault governor redeems on behalf of fee recipients, the `owner` parameter correctly resolves to the `fees_recipient` address, or extend the exemption logic to recognize the governor contract as an exempt caller.

---

**[中文版本]**

**描述：**
`vault.cairo` 的原始设计通过在 `owner == fees_recipient` 时返回零费用，对 `fees_recipient` 地址免征赎回费用。然而，在已部署的 governor 架构中，`fees_recipient` 始终被设置为 `vault_governor` 合约而非最终接收方。因此，当 `vault_governor` 调用 `request_redeem` 向受益人分发已收取的费用时，`owner` 参数不是 `fees_recipient` 地址，导致零费用豁免从未触发。通过 governor 的费用分发因此在已收取的费用之上额外承担赎回费用。

**影響：**
每次通过 vault governor 的费用分发调用都支付额外的赎回费用，减少了实际交付给接收方的费用。这造成了意外的双重收费，并增加了协议费用收取的经济成本。

**修復建議：**
更新费用分发架构，使 vault governor 代表费用接收方赎回时，`owner` 参数能正确解析为 `fees_recipient` 地址，或扩展豁免逻辑以将 governor 合约识别为豁免调用者。
