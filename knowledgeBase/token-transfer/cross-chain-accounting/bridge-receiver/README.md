# bridge-receiver (4)

> Issues where bridge receiver functions fail due to pausing, missing fee handling, or supply reduction side effects.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Hub Chain OverLayer Supply Reduction After OFT Transfers

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
`OverlayerWrap` implements LayerZero's OFT standard, which performs a burn-on-source / mint-on-destination cross-chain transfer. Each time tokens are bridged away from the hub chain (Ethereum), `totalSupply()` on the hub decreases by the bridged amount. `AaveHandler::supply()` uses the current `totalSupply()` as a cap when computing how much additional collateral can be supplied to Aave, calculating `normalizedSupply - totalSuppliedCollateral` to determine headroom. When cross-chain transfers reduce `totalSupply()` below `totalSuppliedCollateral`, this delta underflows, reverting every future call to `supply()`. Since `supply()` is the mechanism by which deposited collateral begins generating yield, this permanently blocks yield generation on the hub chain until a fix is deployed.

**Impact:**
After cross-chain OFT transfers reduce the hub chain's `totalSupply()`, the `AaveHandler::supply()` function reverts with an arithmetic underflow, causing a denial-of-service on all Aave supply operations. The protocol cannot earn yield on any subsequently deposited collateral, and existing integrations relying on the supply flow are broken.

**Recommended Mitigation:**
Revise the `AaveHandler::supply()` delta calculation for `totalSuppliedCollateral` to account for OFT burn/mint behavior. Track the total amount bridged out separately in a `totalBridgedOut` variable and use `totalSupply() + totalBridgedOut` as the effective global supply cap, ensuring the arithmetic cannot underflow due to cross-chain supply changes.

---

**[中文版本]**

**描述：**
`OverlayerWrap` 实现了 LayerZero OFT 标准，跨链转账时在源链执行销毁、在目标链执行铸造。每次从枢纽链（Ethereum）跨链转出代币，`totalSupply()` 就会减少对应数量。`AaveHandler::supply()` 以 `totalSupply()` 为上限，通过 `normalizedSupply - totalSuppliedCollateral` 计算可供给 Aave 的额度。当跨链转账使 `totalSupply()` 降至 `totalSuppliedCollateral` 以下时，该差值下溢，导致所有后续 `supply()` 调用回滚，彻底阻断枢纽链上的收益生成。

**影響：**
跨链 OFT 转账后，`AaveHandler::supply()` 因算术下溢而回滚，造成所有 Aave 供给操作的拒绝服务，协议无法对新存入的抵押品产生收益，相关集成流程全部中断。

**修復建議：**
修改 `AaveHandler::supply()` 中 `totalSuppliedCollateral` 的差值计算逻辑，单独追踪已跨链转出的总量 `totalBridgedOut`，使用 `totalSupply() + totalBridgedOut` 作为有效的全局供给上限，防止跨链供给变化导致算术下溢。

---

## 2. Pause modifier in bridge receiver functions causes receiver failures for in-flight messages

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
`USDCBridge::receivePayloadAndUSDC` and `SecuritizeBridge::receiveWormholeMessages` are both protected by the `whenNotPaused` modifier. When either bridge contract is paused, these receiver functions revert. According to Wormhole documentation, when receiver functions revert the message status becomes "Receiver Failure" and there is no automatic retry mechanism. The only recovery path is to restart the entire cross-chain process from the source chain. This creates a scenario where funds associated with messages that were already in-flight at the time of pausing become stuck, requiring manual intervention to recover.

**Impact:**
Funds associated with in-flight cross-chain messages that arrive while the bridge contract is paused are permanently stuck in a "Receiver Failure" state. Users cannot retrieve their tokens without manual admin action and potentially a new source-chain transaction, resulting in a degraded user experience and potential fund loss if the recovery mechanism is unavailable.

**Recommended Mitigation:**
Remove the `whenNotPaused` modifier from receiver functions to prevent receiver failures for in-flight messages. Additionally, consider implementing a message tracking mechanism that records failed receipts and allows the admin to retry them after the pause is lifted.

---

**[中文版本]**

**描述：**
`USDCBridge::receivePayloadAndUSDC` 和 `SecuritizeBridge::receiveWormholeMessages` 均受 `whenNotPaused` 修饰符保护。当桥接合约被暂停时，这些接收函数会回滚。根据 Wormhole 文档，接收函数回滚后消息状态变为"接收失败"，且没有自动重试机制，唯一恢复路径是从源链重新发起整个跨链流程，导致暂停期间在途消息关联的资金被卡死。

**影響：**
暂停期间到达的在途跨链消息相关资金陷入"接收失败"状态，用户无法在没有管理员人工干预的情况下取回代币，可能导致资金损失。

**修復建議：**
从接收函数中移除 `whenNotPaused` 修饰符，防止在途消息接收失败。同时考虑实现消息追踪机制，记录失败接收并允许管理员在解除暂停后重试。

---

## 3. Settlement of liabilities and obligations lacks optimization for priority repayment, leading to accumulation of unpaid negative yield in the system

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
The `YieldManager` settlement architecture is designed to use yield generated from staked ETH to prioritize repayment of `lstLiabilities` and operational obligations before reporting positive yield to Linea L2. However, the settlement logic is gated by the `stVault`'s available balance. When 100% of ETH is allocated to staking, the vault has zero available balance, so even if positive yield accrues, liability payments are deferred and the full gross yield is reported to L2. Obligations therefore remain unpaid and accumulate as negative yield without being tracked, compounding over time and creating an increasingly large settlement gap between reported and actual yield.

**Impact:**
Negative yield accumulates in the system, reducing the effective staking yield as interest on `lstLiabilities` compounds. Downstream effects include inflated `_getTotalSystemBalance` readings, incorrect reserve threshold calculations, and exacerbation of related accounting issues across multiple protocol functions.

**Recommended Mitigation:**
Before reporting positive yield to L2, check whether all outstanding obligations and liabilities can be settled. Only report the net yield after fully accounting for debts. In code, this means modifying `reportYield` to require `totalVaultFunds > lastUserFunds + ALL_OBLIGATIONS` before treating any surplus as distributable yield.

---

**[中文版本]**

**描述：**
`YieldManager` 的结算架构旨在优先使用质押 ETH 产生的收益偿还 `lstLiabilities` 和运营义务，然后才向 Linea L2 报告正收益。但结算逻辑受限于 `stVault` 的可用余额。当所有 ETH 均被质押时，金库可用余额为零，即便产生了正收益，负债偿还也会被推迟，全额收益被直接上报 L2，负债持续累积，形成越来越大的结算缺口。

**影響：**
系统内负收益持续积累，`lstLiabilities` 上的利息复利增长，降低实际质押收益；同时导致 `_getTotalSystemBalance` 读数虚高、准备金阈值计算错误，加剧多个协议函数的相关会计问题。

**修復建議：**
在向 L2 报告正收益前，检查所有未结清义务和负债是否可以被结算；仅在扣除全部债务后，才将剩余部分作为可分配收益上报。在代码层面，修改 `reportYield` 使其要求 `totalVaultFunds > lastUserFunds + ALL_OBLIGATIONS` 才将盈余视为可分配收益。

---

## 4. depositTokenFromContract Cannot Pay Bridge Fees

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
`depositTokenFromContract` is used by trusted contracts to deposit tokens on behalf of users. Following the v2.6.3 upgrade, the deposit flow now requires native bridge fees to be paid via `msg.value`, forwarded to `portfolioBridge.sendXChainMessage{value: _nativeBridgeFee}(...)`. However, `depositTokenFromContract` is not marked `payable` and does not forward any ETH value when calling the internal `depositToken` function. As a result, `msg.value` is always zero when the bridge fee check is reached, causing the transaction to fail with every bridge provider that requires a fee (`userPaysFee` returns true).

**Impact:**
Trusted contracts that previously used `depositTokenFromContract` will consistently fail when bridge fees are enabled for the default bridge provider, breaking existing integrations and causing a denial of service for all trusted contract deposit flows. Direct calls to `depositToken` can still pay fees, creating an inconsistent API surface.

**Recommended Mitigation:**
Mark `depositTokenFromContract` as `payable` and update it to forward `msg.value` to the internal `depositToken` call, allowing trusted contracts to include the required native bridge fee in their deposit transactions.

---

**[中文版本]**

**描述：**
`depositTokenFromContract` 供受信合约代替用户存款，但在 v2.6.3 升级后，存款流程要求通过 `msg.value` 支付原生桥接费用。该函数未标记为 `payable`，也不向内部 `depositToken` 转发任何 ETH，导致到达桥接费用检查时 `msg.value` 始终为零，在所有需要费用的桥接提供商场景下交易均会失败。

**影響：**
当默认桥接提供商启用费用后，所有通过 `depositTokenFromContract` 操作的受信合约集成将持续失败，造成拒绝服务，而直接调用 `depositToken` 仍可正常支付费用，形成不一致的 API 接口。

**修復建議：**
将 `depositTokenFromContract` 标记为 `payable`，并将 `msg.value` 转发至内部 `depositToken` 调用，允许受信合约在存款交易中附带所需的原生桥接费用。
