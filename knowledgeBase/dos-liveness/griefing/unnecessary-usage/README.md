# unnecessary-usage (18)

> Issues involving unnecessary or unsafe usage patterns — reentrancy guards, external calls, or redundant code paths that can be exploited.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Adapter vault `_userWstETH` not cleared after redemption enables theft of other users' funds

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

## 2. Attacker can make pledge on behalf of users if those users have approved `PledgeManager` to spend their tokens

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

## 3. Double Taxation on Liquidity ETH Removal via Router

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The NTE token implements two taxation mechanisms: an AMM tax applied to buy/sell operations involving the liquidity pair, and a transfer tax for direct P2P transfers. During liquidity ETH removal via `removeLiquidityETHSupportingFeeOnTransferTokens`, tokens flow from the pair to the router (triggering buy tax) and then from the router to the user (triggering transfer tax). This results in double taxation for a single liquidity removal operation, as the same token transfer is taxed twice under two different tax categories.

**Impact:**
Liquidity providers pay both the buy tax and the transfer tax when removing liquidity with ETH, effectively suffering double fees on a single operation. This discourages liquidity provision and causes more tokens to be burned/collected than intended.

**Recommended Mitigation:**
Exempt the router address from the transfer tax when acting as an intermediary during liquidity removal, or detect the router-to-user transfer and apply only one tax tier.

---

**[中文版本]**

**描述：**
NTE 代币在流动性 ETH 移除时被双重征税：代币从交易对转到路由器触发买入税，再从路由器转给用户触发转账税，同一流动性移除操作被征税两次。

**影響：**
流动性提供者在移除 ETH 流动性时需承担买入税和转账税双重费用，严重影响流动性激励。

**修復建議：**
在流动性移除操作中豁免路由器地址的转账税，或检测路由器中转场景，只应用一种税率。

---

## 4. Native Balance Sweep via Absolute Balance on NATIVE

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
In the aggregator's `_executeSwap`, the per-route input amount for `NATIVE` legs is derived from `address(this).balance` (the contract's total raw ETH balance) rather than the delta from the user's `msg.value`. When any pre-existing ETH is on the contract (from prior operations, accidental transfers, or owner funding), a malicious caller can send 1 wei with `tokenIn = NATIVE` and route it through a path that sends native ETH. The contract uses its entire ETH balance as the route input, forwarding all existing ETH to the destination router.

**Impact:**
An attacker can drain all ETH currently held in the aggregator contract with a minimal input (1 wei), receiving the entire native balance as their swap output.

**Recommended Mitigation:**
Track per-swap NATIVE input using the delta between pre-swap and post-swap balances, or use wrapped WETH and unwrap as needed, avoiding absolute balance reads for NATIVE inputs.

---

**[中文版本]**

**描述：**
聚合器的 `_executeSwap` 对 NATIVE 路由使用 `address(this).balance` 计算输入金额，而非用户提供的增量。如果合约持有任何 ETH，攻击者只需发送 1 wei 即可触发路由，使用合约全部 ETH 余额作为输入。

**影響：**
攻击者仅需 1 wei 即可耗尽合约中全部 ETH 余额。

**修復建議：**
使用交换前后余额差值追踪 NATIVE 输入，避免使用绝对余额读取。

---

## 5. [DualDefense] Double Effective Stake Reduction on Redelegation Leading to Arithmetic Underflow

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

## 6. Auto-draw on `AccountableFixedTerm::pay` lets third parties force unwanted borrowing

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableFixedTerm::pay` automatically draws any positive `drawableFunds` before processing the interest payment. Since `drawableFunds` increases when users deposit into the vault, a third party can deposit into the vault immediately before the borrower calls `pay`. This causes `pay` to automatically draw the new liquidity, increasing `_loan.outstandingPrincipal` and adding interest on the added principal for the remaining term — all without borrower consent.

**Impact:**
Borrowers lose discretion over their principal size. Attackers or any vault depositor can repeatedly "stuff" the vault before each payment window, forcing unwanted draws and increasing future interest obligations. This enables griefing and economic denial-of-service against borrowers.

**Recommended Mitigation:**
Remove the auto-draw from `AccountableFixedTerm::pay`. Loan increases should only occur via an explicit borrower action (e.g., a dedicated `draw(uint256)` function), not implicitly during interest payments.

---

**[中文版本]**

**描述：**
`AccountableFixedTerm::pay` 在处理利息前会自动提取 `drawableFunds`。任何人可在借款人调用 `pay` 前向 vault 存款，强制增大贷款本金，在借款人不知情下增加未来利息负担。

**影響：**
借款人失去对本金规模的控制权；攻击者可通过反复注入流动性进行经济拒绝服务攻击。

**修復建議：**
从 `pay` 中移除自动提取逻辑，贷款增加应仅通过借款人显式操作（如 `draw(uint256)`）触发。

---

## 7. Changing stablecoin on `TokenBank` can mess up fees collection

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
The `TokenBank` stores fee amounts (`feeAmount`) computed using the decimals of the current stablecoin. If the stablecoin is changed to one with different decimals, any pending fees accumulated before the change are denominated in the old stablecoin's decimal precision. When those fees are eventually collected, they are transferred using the new stablecoin — resulting in either gross underpayment or overpayment depending on the decimal difference.

**Impact:**
Collected fees can be vastly different from expected when the stablecoin changes decimals. For example, 10 USDC (6 decimals, stored as `10e6`) collected as USDT (8 decimals) would be only 0.1 USDT.

**Recommended Mitigation:**
Normalize pending fees to the new stablecoin's decimals when the stablecoin is changed, similar to how `PledgeManager` handles decimal normalization.

---

**[中文版本]**

**描述：**
`TokenBank` 中存储的 `feeAmount` 使用当前稳定币的小数位计算。若稳定币被换为不同小数位的代币，之前积累的未领取手续费在新稳定币中代表不同金额。

**影響：**
稳定币更换后收取的手续费金额可能与预期严重偏差（例如从 6 位精度变为 8 位精度导致 100 倍差异）。

**修復建議：**
更换稳定币时将待领取手续费转换为新稳定币的小数位精度，与 `PledgeManager` 的处理方式保持一致。

---

## 8. Incorrect `chainid` prevents correct Strategy deployment on Berachain

**Severity:** 🟡 Medium
**Source:** `cyfrin/d2.md`

**Description:**
The `Strategy` constructor includes chain-specific facet configuration logic. The condition for Berachain uses `block.chainid == 80000`, but the official chain ID for Berachain mainnet is `80094` according to its documentation. This typo means the Berachain-specific facets are never initialized when the contract is deployed on Berachain.

**Impact:**
Strategy facets intended for Berachain deployment are never activated, preventing expected functionality from executing on the Berachain mainnet.

**Recommended Mitigation:**
Change `block.chainid == 80000` to `block.chainid == 80094` to match the correct Berachain mainnet chain ID.

---

**[中文版本]**

**描述：**
`Strategy` 构造函数中针对 Berachain 的条件使用 `block.chainid == 80000`，但官方 Berachain 主网 chain ID 为 `80094`，导致 Berachain 专用 facet 永远无法初始化。

**影響：**
部署在 Berachain 上的 Strategy 合约无法激活预期功能。

**修復建議：**
将 `block.chainid == 80000` 改为 `block.chainid == 80094`。

---

## 9. Incorrect usage of `minOutputAmount` in `executeTwoStepRedemption` can cause unnecessary reverts

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
In `RedemptionManager::executeTwoStepRedemption`, `supplyTo` is called with `params.minOutputAmount` as the minimum expected return. Immediately after, the slippage check computes `offRampBalance - fee < params.minOutputAmount` where `fee` is deducted from the actual received balance. If `supplyTo` returns exactly `minOutputAmount`, the subsequent fee deduction causes the check to fail — even though the liquidity provider met the minimum requirement. The discrepancy arises because `minOutputAmount` passed to `supplyTo` does not account for the fee that will be deducted in the slippage check.

**Impact:**
Transactions revert unnecessarily when the liquidity provider delivers exactly the requested minimum amount, causing unexpected failures for users who specified valid slippage tolerances.

**Recommended Mitigation:**
Add the expected fee to `minOutputAmount` when calling `supplyTo`, so the post-fee balance is guaranteed to meet the slippage check threshold.

---

**[中文版本]**

**描述：**
`executeTwoStepRedemption` 中 `supplyTo` 以 `minOutputAmount` 作为最低期望返回值，但后续滑点检查从余额中扣除手续费再与 `minOutputAmount` 比较。当 `supplyTo` 恰好返回 `minOutputAmount` 时，扣费后低于阈值，触发不必要的回滚。

**影響：**
流动性提供商满足最低要求时，交易仍会意外回滚。

**修復建議：**
调用 `supplyTo` 时，在 `minOutputAmount` 基础上加入预期手续费。

---

## 10. Missing modifiers on `YieldStrategyFactory.createYieldStrategy` can lead to deployment of unverified strategies

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`YieldStrategyFactory.createYieldStrategy` is a permissionless function that creates new `AccountableYield` strategies. Unlike `OpenTermFactory::createOpenTermLoan` and `FixedTermFactory::createFixedTermLoan`, which both apply `whenNotPaused`, `onlyVerified`, and `onlyWhitelistedAsset` modifiers, `createYieldStrategy` has none of these checks. This means anyone can deploy a yield strategy even when the protocol is paused, without passing identity verification, and with any asset regardless of whitelist status.

**Impact:**
Unverified parties can create yield strategies bypassing all protocol safeguards. Assets not approved for use can be introduced into the system. Strategies can be deployed during emergency pauses when deployments should be blocked.

**Recommended Mitigation:**
Apply `whenNotPaused`, `onlyVerified`, and `onlyWhitelistedAsset(params.asset)` modifiers to `createYieldStrategy`, consistent with the other factory functions.

---

**[中文版本]**

**描述：**
`YieldStrategyFactory.createYieldStrategy` 是无权限控制的函数，缺少 `whenNotPaused`、`onlyVerified` 和 `onlyWhitelistedAsset` 修饰符，而其他工厂函数均具备这些检查。

**影響：**
任何人都可以在协议暂停期间部署未经验证的 yield 策略，引入未白名单资产。

**修復建議：**
为 `createYieldStrategy` 添加 `whenNotPaused`、`onlyVerified` 和 `onlyWhitelistedAsset(params.asset)` 修饰符。

---

## 11. Remove unnecessary imports and inheritance

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`BurnStateManager` unnecessarily imports and inherits from contracts beyond `Initializable`. These superfluous imports and inheritance relationships increase bytecode size, add unexpectedly available functions to the contract's interface, and create confusion about the intended contract hierarchy and capabilities.

**Impact:**
Unnecessary inheritance can expose unintended functions or storage layout concerns. It increases bytecode size and complicates security reviews by enlarging the contract's effective attack surface.

**Recommended Mitigation:**
Remove all unnecessary imports and inheritance from `BurnStateManager`, keeping only the `Initializable` base contract as intended.

---

**[中文版本]**

**描述：**
`BurnStateManager` 不必要地导入并继承了除 `Initializable` 以外的合约，增加了字节码体积和合约接口复杂度。

**影響：**
多余的继承可能暴露非预期函数，增加审计难度和潜在攻击面。

**修復建議：**
移除 `BurnStateManager` 中所有不必要的导入和继承，仅保留 `Initializable` 基类。

---

## 12. Unnecessary `onlyRegisteredOperatorNode` on `completeStakeUpdate` function

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`completeStakeUpdate` has the `onlyRegisteredOperatorNode` modifier applied to it, but internally it delegates to `_completeStakeUpdate` which already has the same modifier. This results in the access control check being executed twice for every call: once at the public function boundary and once inside the internal function.

**Impact:**
The redundant modifier check wastes gas on every call without providing any additional security benefit.

**Recommended Mitigation:**
Remove the `onlyRegisteredOperatorNode` modifier from either the public `completeStakeUpdate` wrapper or from the internal `_completeStakeUpdate` function to avoid the double check.

---

**[中文版本]**

**描述：**
`completeStakeUpdate` 公开函数和其调用的内部函数 `_completeStakeUpdate` 都有 `onlyRegisteredOperatorNode` 修饰符，导致每次调用都执行两次相同的访问控制检查。

**影響：**
冗余修饰符检查浪费 gas，无额外安全收益。

**修復建議：**
从公开函数或内部函数中移除一个重复的 `onlyRegisteredOperatorNode` 修饰符。

---

## 13. Unnecessary `override` keywords on interface implementation functions

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
Multiple functions in `SecuritizeOnRamp` use the `override` keyword when implementing interface functions. In Solidity, `override` is required only when overriding a function from a parent contract. For functions that implement interface methods without any parent contract providing a concrete implementation, `override` is unnecessary and misleading, falsely implying the function is replacing a parent class implementation.

**Impact:**
The unnecessary `override` keywords create confusion about the contract's inheritance structure, making code reviews harder and potentially misleading about the contract's behavior.

**Recommended Mitigation:**
Remove the `override` keyword from functions that implement interface methods without overriding a concrete parent implementation.

---

**[中文版本]**

**描述：**
`SecuritizeOnRamp` 中多个实现接口方法的函数使用了 `override` 关键字，但这些函数并未覆盖父合约的具体实现，`override` 在此不必要且具有误导性。

**影響：**
不必要的 `override` 关键字使继承结构混乱，增加代码审查难度。

**修復建議：**
从仅实现接口方法而未覆盖父合约具体实现的函数中移除 `override` 关键字。

---

## 14. Unnecessary usage of `_msgSender()` to validate if caller is the `Issuer` on the `STBL_PT1_YieldDistributor`

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
The `isIssuer` modifier in `STBL_PT1_YieldDistributor` uses `_msgSender()`, which routes through `ERC2771ContextUpgradeable._msgSender()` and ultimately through `ContextUpgradeable._msgSender()`. Since the `TrustedForwarder` will never be the `YieldDistributor` itself, the issuer always calls the function directly — meaning the ERC2771 context routing is unnecessary. Using `msg.sender` directly is more efficient and semantically clearer in this context. The same applies to `distributeReward()`.

**Impact:**
Unnecessary gas overhead from the multi-step `_msgSender()` resolution on every call where direct `msg.sender` is sufficient.

**Recommended Mitigation:**
Replace `_msgSender()` with `msg.sender` in the `isIssuer` modifier and `distributeReward` function, since ERC2771 meta-transaction forwarding is not applicable in these call paths.

---

**[中文版本]**

**描述：**
`isIssuer` 修饰符使用 `_msgSender()` 通过 ERC2771 上下文解析调用者，但 `TrustedForwarder` 永远不会是 `YieldDistributor` 本身，issuer 总是直接调用，多层解析完全不必要。

**影響：**
不必要的多层 `_msgSender()` 解析产生额外 gas 消耗。

**修復建議：**
在 `isIssuer` 修饰符和 `distributeReward` 函数中将 `_msgSender()` 替换为 `msg.sender`。

---

## 15. Unnecessary usage of `nonReentrant` modifier on `ReferralManager::completeFirstPurchase`

**Severity:** 🟡 Medium
**Source:** `cyfrin/final.md`

**Description:**
`ReferralManager::completeFirstPurchase` applies the `nonReentrant` modifier from `ReentrancyGuardTransientUpgradeable`. However, this function is only callable by the `TokenBank` contract, and its only external interaction is a stablecoin transfer to the referrer. Since the caller is restricted to a trusted contract and there is no complex state mutation vulnerable to reentrancy, the modifier is unnecessary.

**Impact:**
Unnecessary gas cost on every call to `completeFirstPurchase` from the transient reentrancy guard slot operations.

**Recommended Mitigation:**
Remove the `nonReentrant` modifier from `completeFirstPurchase` and also remove the now-unused `ReentrancyGuardTransientUpgradeable` import.

---

**[中文版本]**

**描述：**
`ReferralManager::completeFirstPurchase` 应用了 `nonReentrant` 修饰符，但该函数仅由受信任的 `TokenBank` 合约调用，唯一的外部交互是向推荐人转账稳定币，不存在重入风险。

**影響：**
每次调用产生不必要的 transient 重入锁 gas 消耗。

**修復建議：**
移除 `completeFirstPurchase` 的 `nonReentrant` 修饰符，并删除不再使用的 `ReentrancyGuardTransientUpgradeable` 导入。

---

## 16. Usage of unofficial `wormhole-solidity-sdk` npm package poses security and maintenance risks

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
The bridge contracts depend on `wormhole-solidity-sdk@^0.9.0` from npm, which has been confirmed by the Wormhole team to be an unofficial package published by a third party. The Wormhole team's only approved release is v0.1.0 available on GitHub. The unofficial npm package is used throughout critical bridge infrastructure including `SecuritizeBridge.sol`, `WormholeCCTPUpgradeable.sol`, `USDCBridge.sol`, and test mocks.

**Impact:**
Relying on an unofficial, unverified package introduces potential security vulnerabilities in critical cross-chain bridge code. The package could contain malicious code, incorrect implementations, or be removed/altered at any time, creating maintenance and supply-chain risks.

**Recommended Mitigation:**
Replace the unofficial npm package with the official GitHub release: `forge install wormhole-foundation/wormhole-solidity-sdk@v0.1.0` and update all imports accordingly.

---

**[中文版本]**

**描述：**
桥接合约依赖 npm 上的非官方 `wormhole-solidity-sdk@^0.9.0` 包，Wormhole 团队已确认该包由第三方发布，官方版本仅在 GitHub 发布 v0.1.0。非官方包被用于多个关键桥接合约。

**影響：**
依赖未经验证的第三方包会在关键跨链桥代码中引入安全漏洞、供应链风险和维护隐患。

**修復建議：**
使用官方 GitHub 发布版本替换：`forge install wormhole-foundation/wormhole-solidity-sdk@v0.1.0`。

---

## 17. Use `ReentrancyGuardTransient` for faster `nonReentrant` modifiers

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
The `Minter` contract uses the standard `ReentrancyGuard` (storage-based reentrancy protection). OpenZeppelin provides `ReentrancyGuardTransient` which uses transient storage (EIP-1153) for the reentrancy lock. Transient storage is reset at the end of every transaction and is significantly cheaper in gas compared to persistent storage reads/writes used by the standard guard.

**Impact:**
Every call to a `nonReentrant` function pays unnecessary gas for persistent storage slot reads/writes when transient storage would be more efficient.

**Recommended Mitigation:**
Replace `ReentrancyGuard` with `ReentrancyGuardTransient` in `Minter.sol` to benefit from cheaper transient storage reentrancy protection.

---

**[中文版本]**

**描述：**
`Minter` 合约使用基于存储的标准 `ReentrancyGuard`，而 OpenZeppelin 的 `ReentrancyGuardTransient` 使用 EIP-1153 瞬态存储，每笔交易结束时自动重置，gas 成本更低。

**影響：**
每次调用 `nonReentrant` 函数都需支付不必要的持久存储读写 gas 费用。

**修復建議：**
在 `Minter.sol` 中将 `ReentrancyGuard` 替换为 `ReentrancyGuardTransient`。

---

## 18. `nonReentrant` is not the first modifier

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
In `FeeManager::withdrawProtocolFee`, the `nonReentrant` modifier is not listed as the first modifier. Best practice dictates that `nonReentrant` should be the first modifier in any function that uses it, so that the reentrancy lock is acquired before any other modifier logic executes. If a preceding modifier makes an external call or reads state before `nonReentrant` locks execution, reentrancy attacks could exploit the window before the guard is active.

**Impact:**
Inconsistent modifier ordering creates a potential reentrancy window if earlier modifiers involve external interactions. Even without immediate exploitability, it contradicts security best practices and creates audit confusion.

**Recommended Mitigation:**
Move `nonReentrant` to be the first modifier in `FeeManager::withdrawProtocolFee`'s modifier list, ensuring the reentrancy lock is set before any other logic in the function or its modifiers.

---

**[中文版本]**

**描述：**
`FeeManager::withdrawProtocolFee` 中，`nonReentrant` 修饰符不是第一个修饰符。最佳实践要求 `nonReentrant` 应排在所有修饰符的最前面，确保重入锁在任何其他修饰符逻辑执行前就被设置。

**影響：**
修饰符顺序不一致可能导致重入窗口，若前面的修饰符有外部调用则尤为危险；同时违反安全最佳实践，增加审计混乱。

**修復建議：**
将 `nonReentrant` 移到 `withdrawProtocolFee` 修饰符列表的首位。
