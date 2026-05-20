# missing-checks (6)

> Missing or weak validation and stale state — access checks, cross-chain peers, vault accounting, and surplus paths that enable drain or permanent DoS.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Attacker can drain all tokens from cancelled game since `SessionManager::refundCancelledGame` doesn't validate caller actually joined the game

**Severity:** 🔴 Critical
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::refundCancelledGame` does not check whether the caller actually participated in the game before issuing a refund. Any address — including one that never deposited any tokens — can call the function and receive a refund from a cancelled game's pool. By repeating the call from multiple addresses, an attacker can drain the entire token balance of a cancelled game contract.

**Impact:**
Any cancelled game can be completely drained of tokens by a permissionless attacker. Legitimate participants who did join the game will be left with nothing to claim once the contract balance reaches zero.

**Recommended Mitigation:**
Add a check inside `refundCancelledGame` that verifies `contestants[gameId][msg.sender]` is true before processing the refund, ensuring only users who actually joined can claim a refund.

---

**[中文版本]**

**描述：**
`SessionManager::refundCancelledGame` 在退款前未驗證調用者是否實際參與了該遊戲。任何地址——包括從未存入代幣的地址——均可調用此函數並從已取消遊戲的資金池中獲取退款。攻擊者可通過使用多個不同地址重複調用的方式，徹底清空合約中的所有代幣。

**影響：**
任何已取消的遊戲都可能被無需許可的攻擊者完全清空。一旦合約餘額歸零，真正參與遊戲的合法用戶將無法獲得任何退款。

**修復建議：**
在 `refundCancelledGame` 中添加驗證：確認 `contestants[gameId][msg.sender]` 為 true 後再處理退款，確保只有真正參與遊戲的用戶才能申請退款。

---

## 2. Missing source validation in CCIP message handling

**Severity:** 🔴 Critical
**Source:** `cyfrin/yieldfi.md`

**Description:**
YieldFi integrates with Chainlink CCIP to facilitate cross-chain transfers of its yield tokens. In `BridgeCCIP::_ccipReceive`, there is no validation of the message sender from the source chain. The function decodes the payload and processes it solely based on the message content, without verifying that the originating sender on the source chain is a trusted peer. An attacker could craft a malicious `Any2EVMMessage` containing valid-looking data and trigger token minting or unlocking on the destination chain by sending it through CCIP to `BridgeCCIP`.

**Impact:**
An attacker could drain the bridge of tokens on L1 or mint an unlimited amount of tokens on L2. While a two-step redeem process provides some mitigation, such an exploit would severely disrupt protocol accounting and could be abused for yield theft.

**Recommended Mitigation:**
Implement a mapping of allowed peers per source chain and validate in `_ccipReceive` that the message sender on the source chain is in the allowed peers list before processing.

---

**[中文版本]**

**描述：**
YieldFi 通过 Chainlink CCIP 实现跨链收益代币转移。`BridgeCCIP::_ccipReceive` 中没有对来源链消息发送者的验证，仅基于消息内容处理，攻击者可伪造 `Any2EVMMessage` 触发目标链上的代币铸造或解锁操作。

**影響：**
攻击者可耗尽 L1 桥接的代币或在 L2 无限铸造代币，严重破坏协议核算并可能被用于窃取收益。

**修復建議：**
实现按来源链的允许对等节点映射，在 `_ccipReceive` 中验证来源链上的消息发送者是否在允许列表中，然后再处理消息。

---

## 3. `Surplus::processSurplus` always reverts for managed collateral - diamond holds zero balance

**Severity:** 🟠 High
**Source:** `cyfrin/parallel3.1.md`

**Description:**
`LibSurplus::_computeCollateralSurplus` reads the collateral balance from `LibManager::totalAssets` for managed collateral, which returns the balance held by the external strategy. It computes a `collateralSurplus` based on this. `Surplus::processSurplus` then attempts a self-swap via `ISwapper(address(this)).swapExactInput(collateralSurplus, ...)`. Inside `Swapper::_swap` for managed collateral, the swap tries to `safeTransferFrom` the diamond to the manager. However, the diamond's balance is always 0 for managed collateral — during normal mints, tokens go directly from user to manager, and during burns, the manager sends directly to the user. The diamond never holds managed collateral tokens. The `transferFrom` call reverts because the diamond has insufficient balance.

**Impact:**
Permanent DoS on surplus processing for all managed collateral. Strategy yield (the primary surplus source for managed assets) accumulates in the manager but can never be captured as distributable tokenP.

**Recommended Mitigation:**
Before the self-swap in `Surplus::processSurplus`, release the surplus amount from the external strategy to the diamond: `LibManager.release(collateral, address(this), collateralSurplus, collatInfo.managerData.config)`.

---

**[中文版本]**

**描述：**
`LibSurplus::_computeCollateralSurplus` 从外部策略获取托管抵押品余额并计算盈余，`Surplus::processSurplus` 随后通过自调用执行交换。但在 `Swapper::_swap` 中，交换尝试从 diamond 合约向管理器转账，而 diamond 对托管抵押品的余额始终为 0（正常铸造时代币直接从用户到管理器，赎回时从管理器直接到用户）。`transferFrom` 调用因 diamond 余额不足而 revert。

**影響：**
对所有托管抵押品的盈余处理造成永久性拒绝服务。策略收益（托管资产的主要盈余来源）在管理器中积累但永远无法作为可分配的 tokenP 被捕获。

**修復建議：**
在 `Surplus::processSurplus` 的自调用交换之前，先将盈余金额从外部策略释放到 diamond：`LibManager.release(collateral, address(this), collateralSurplus, collatInfo.managerData.config)`。

---

## 4. Adapter vault `_userWstETH` not cleared after redemption enables theft of other users' funds

**Severity:** 🔴 Critical
**Source:** `cyfrin/escrow.md`

**Description:**
When a user redeems shares from a `SablierBob` adapter vault via `SablierBob::redeem`, shares are burned but the `_userWstETH` mapping in `SablierLidoAdapter` is never cleared or decremented. This contrasts with `exitWithinGracePeriod`, which correctly clears `_userWstETH` and decrements `_vaultTotalWstETH`. Because burns do not trigger `onERC1155Received`, `updateStakedTokenBalance` is never called during redemption. Subsequent calls to `calculateAmountToTransferWithYield` read the stale (non-zero) `_userWstETH` balance. An attacker with two addresses can exploit this: redeem from address A (stale balance persists), transfer shares from address B to A (wstETH compounds on stale data), then redeem again with inflated wstETH ratio.

**Impact:**
An attacker controlling two addresses can drain the entire vault by exploiting the stale `_userWstETH` balance. Victim users who redeem afterward find the vault empty and their redemption reverts with insufficient funds.

**Recommended Mitigation:**
Clear `_userWstETH[vaultId][user]` and decrement `_vaultTotalWstETH[vaultId]` at the beginning of the redemption path in `SablierBob::redeem`, symmetrically to how `exitWithinGracePeriod` handles this.

---

**[中文版本]**

**描述：**
用户通过 `SablierBob::redeem` 赎回时，份额被销毁，但 `SablierLidoAdapter` 中的 `_userWstETH` 映射从未被清零。攻击者可利用两个地址：先从地址 A 赎回（保留旧余额），再将地址 B 的份额转给 A（wstETH 叠加在旧数据上），再次赎回以获取超额资金。

**影響：**
攻击者可耗尽整个 vault，导致后续赎回的用户因资金不足而回滚。

**修復建議：**
在 `SablierBob::redeem` 的赎回路径开始时清零 `_userWstETH` 并递减 `_vaultTotalWstETH`，与 `exitWithinGracePeriod` 的处理保持对称。

---

## 5. Attacker can make pledge on behalf of users if those users have approved `PledgeManager` to spend their tokens

**Severity:** 🟠 High
**Source:** `cyfrin/pledge.md`

**Description:**
`PledgeManager::pledge` accepts a `signer` parameter (the address whose tokens are pledged) but never enforces that `msg.sender == data.signer` when not using `IERC20Permit::permit`. If a user manually called `IERC20::approve` and left an open token approval, any third party can call `pledge` with that user's address as `signer` and spend their tokens. This is particularly dangerous as users commonly leave max approvals for protocols they frequently interact with.

**Impact:**
An attacker can forcibly pledge tokens from any user who has a standing approval to `PledgeManager`, spending their tokens without consent and potentially locking funds in an undesired pledge.

**Recommended Mitigation:**
When not using `permit`, add a check `require(msg.sender == signer)` in `PledgeManager::pledge`, or always use `msg.sender` as the effective signer, consistent with how `PledgeManager::refundTokens` operates.

---

**[中文版本]**

**描述：**
`PledgeManager::pledge` 不强制 `msg.sender == data.signer`（在非 permit 模式下），任何人都可以用持有 `PledgeManager` 授权额度的用户地址作为 `signer` 强制质押其代币。

**影響：**
攻击者可在未经同意的情况下强制质押他人代币，锁定资金于不想要的质押中。

**修復建議：**
非 permit 模式下添加 `require(msg.sender == signer)` 检查，或始终使用 `msg.sender` 作为有效签名者。

---

## 6. [DualDefense] Double Effective Stake Reduction on Redelegation Leading to Arithmetic Underflow

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
In the Hayabusa Stargate protocol, both `requestDelegationExit()` and `unstake()` independently call `_updatePeriodEffectiveStake()` to decrease the effective stake for a validator when a user holds a token. When a user first calls `requestDelegationExit()`, the effective stake is reduced. Later, if the user calls `unstake()` after the validator has reached `VALIDATOR_STATUS_EXITED`, the function reduces the effective stake again for the same token and the same period — causing a double reduction.

**Impact:**
The double reduction leads to an arithmetic underflow in the effective stake calculation, corrupting stake accounting for the validator and potentially causing reverts in stake-dependent operations.

**Recommended Mitigation:**
Track whether `_updatePeriodEffectiveStake` has already been applied for a given token before calling it in `unstake()`, and skip the call if the reduction was already applied by `requestDelegationExit()`.

---

**[中文版本]**

**描述：**
`requestDelegationExit()` 和 `unstake()` 都独立调用 `_updatePeriodEffectiveStake()` 来减少有效质押，对同一 token 同一周期执行两次减量，导致算术下溢。

**影響：**
有效质押核算被破坏，依赖质押量的操作可能发生回滚。

**修復建議：**
记录某 token 的质押减量是否已被 `requestDelegationExit()` 应用，在 `unstake()` 中跳过已处理的减量。

---

---
