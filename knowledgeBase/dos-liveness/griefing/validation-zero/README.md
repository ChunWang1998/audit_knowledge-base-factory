# validation-zero (19)

> Issues where missing zero-checks or insufficient input validation allow invalid states or exploitable conditions.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Missing source validation in CCIP message handling

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

## 2. Native Input Routed as Zero for Native-Send Routes

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
When `tokenIn == NATIVE`, `swap()` wraps all ETH to WETH up-front, setting the contract's native ETH balance to zero. Later, `_executeSwap` computes each route's input amount using the native ETH balance for `NATIVE` legs (`address(this).balance`), which is now zero after wrapping. For Kuru routes marked to send native ETH (`isNativeSend[0] == true`) with `tokenIn == NATIVE`, the computed `routeAmountIn` becomes zero, and the call is made with `{value: 0}`. The user's provided ETH was wrapped to WETH and is never consumed; the route produces no output, and the user receives nothing while their WETH remains trapped inside the aggregator.

**Impact:**
Users sending native ETH through native-send routes receive no swap output. Their ETH is converted to WETH inside the aggregator contract and cannot be recovered through the normal swap flow.

**Recommended Mitigation:**
Make routing WETH-centric internally and explicitly unwrap for native-send legs: use WETH balance to compute route amounts, and unwrap WETH to ETH only for legs that require native ETH delivery.

---

**[中文版本]**

**描述：**
当 `tokenIn == NATIVE` 时，`swap()` 将所有 ETH 预先封装为 WETH，使合约的原生 ETH 余额归零。之后 `_executeSwap` 使用原生 ETH 余额计算 `NATIVE` 路由的输入量，但该余额已为零。对于标记为发送原生 ETH 的 Kuru 路由，计算出的 `routeAmountIn` 为零，调用以 `{value: 0}` 执行。用户提供的 ETH 被封装为 WETH 后被困在聚合器中，无法通过正常交换流程取回。

**影響：**
通过原生发送路由发送原生 ETH 的用户不会收到任何交换输出，其 ETH 被转换为 WETH 滞留在聚合器合约中。

**修復建議：**
在内部以 WETH 为中心进行路由，仅在需要原生 ETH 交付的路段明确解封装：使用 WETH 余额计算路由金额，仅为需要原生 ETH 的路段解封装。

---

## 3. Improper Weight Reset on tokenIn Change Allows Bypassing MAX_WEIGHT Cap

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
The `_executeSwap()` function in `CoreAggregator` enforces a `MAX_WEIGHT = 10,000` cap per contiguous sequence of routes using the same `tokenIn` via a `remainingWeight` variable. When `routeTokenIn != currentTokenIn`, `remainingWeight` is reset back to `MAX_WEIGHT`. While intended for legitimate token chaining (e.g., WETH → USDC → DAI), this logic can be exploited by a malicious user who oscillates `tokenIn` values between routes, resetting the weight allowance repeatedly. This results in unbounded cumulative weight usage across multiple routes, far exceeding the intended 100%.

**Impact:**
An attacker can cause the aggregator to use more tokens than the user expected or authorized across a swap execution. The total tokens consumed can far exceed the `MAX_WEIGHT` cap, potentially draining more funds than intended.

**Recommended Mitigation:**
Track cumulative weight per `tokenIn` using a mapping and enforce global `MAX_WEIGHT` constraints per `tokenIn` instead of resetting blindly on each token change.

---

**[中文版本]**

**描述：**
`CoreAggregator` 中的 `_executeSwap()` 通过 `remainingWeight` 变量对同一 `tokenIn` 的连续路由序列强制执行 `MAX_WEIGHT = 10,000` 上限。当 `tokenIn` 改变时 `remainingWeight` 被重置为 `MAX_WEIGHT`，恶意用户可通过在路由间交替切换 `tokenIn` 值来反复重置权重配额，导致无限制的累计权重使用量，远超预期的 100% 上限。

**影響：**
攻击者可导致聚合器在交换执行中消耗超出用户预期或授权的代币，累计消耗量可远超 `MAX_WEIGHT` 上限。

**修復建議：**
使用映射按 `tokenIn` 追踪累计权重，并为每个 `tokenIn` 强制执行全局 `MAX_WEIGHT` 约束，而不是在每次代币变更时盲目重置。

---

## 4. `Surplus::processSurplus` always reverts for managed collateral - diamond holds zero balance

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

## 5. Auction Mode Bypass in `bulkTransferTokens` Allows Transfers During Active Auctions

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
The `bulkTransferTokens` function does not validate auction mode before transferring tokens, unlike the public `transferToken` function which includes `require(tokenDetailsMap[_symbol].auctionMode == ITradePairs.AuctionMode.OFF, "P-AUCT-01")`. The bulk function calls the private `transferToken` overload directly without this validation, creating an inconsistency where single-token transfers respect auction restrictions while bulk transfers bypass them entirely.

**Impact:**
Tokens under active auction restrictions can be transferred via `bulkTransferTokens` before the auction concludes, undermining auction integrity and enabling early distribution of auction tokens to unauthorized recipients.

**Recommended Mitigation:**
Add an auction mode check for each symbol within the `bulkTransferTokens` loop, consistent with the check applied in the public `transferToken` function.

---

**[中文版本]**

**描述：**
`bulkTransferTokens` 函数在转账前未验证拍卖模式，而公共 `transferToken` 函数包含拍卖模式检查。批量函数直接调用私有 `transferToken` 重载而不进行此验证，造成单代币转账遵守拍卖限制而批量转账完全绕过的不一致性。

**影響：**
处于活跃拍卖限制的代币可通过 `bulkTransferTokens` 在拍卖结束前转账，破坏拍卖完整性，使拍卖代币被提前分配给未授权接收方。

**修復建議：**
在 `bulkTransferTokens` 循环中为每个 symbol 添加拍卖模式检查，与公共 `transferToken` 函数中的检查保持一致。

---

## 6. `DividendManager::distributePayout` records a new payout record increasing the current payout index for zero `payoutAmount`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DividendManager::distributePayout` does not validate that `payoutAmount > 0` before recording a new payout. When called with `payoutAmount = 0`, it records a `PayoutInfo` entry with `amount = 0` and increments `_currentPayoutIndex`. This wastes a payout index slot, corrupts payout accounting (users iterate through all payout records), and — combined with the `uint8` type limit of 255 — can accelerate exhaustion of the payout index counter.

**Impact:**
Zero-amount payout records waste index slots and add unnecessary overhead to payout balance calculations. In the worst case they accelerate the exhaustion of the 255-slot payout index limit.

**Recommended Mitigation:**
Add a check at the beginning of `DividendManager::distributePayout` that reverts when `payoutAmount == 0`.

---

**[中文版本]**

**描述：**
`DividendManager::distributePayout` 在记录新派息之前未验证 `payoutAmount > 0`。以 `payoutAmount = 0` 调用时，仍会记录一个 `amount = 0` 的 `PayoutInfo` 条目并递增 `_currentPayoutIndex`，浪费派息索引槽并破坏派息核算。

**影響：**
零金额派息记录浪费索引槽，为派息余额计算增加不必要开销，在最坏情况下加速耗尽 255 槽的派息索引限制。

**修復建議：**
在 `DividendManager::distributePayout` 开头添加检查，当 `payoutAmount == 0` 时 revert。

---

## 7. Floor division in `SablierLidoAdapter::updateStakedTokenBalance` allows transferring `BobVaultShares` without moving wstETH backing

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
In `SablierLidoAdapter::updateStakedTokenBalance`, the wstETH to transfer is computed as `(fromWstETH * shareAmountTransferred / userShareBalanceBeforeTransfer)` using floor division. Because the wstETH exchange rate is less than 1:1 with shares (a deposit of N WETH mints N shares but produces less than N wstETH), any 1-wei share transfer satisfies the rounding-to-zero condition. By transferring `BobVaultShares` in 1-wei increments, a sender can move an arbitrary number of shares to a recipient while retaining all of their wstETH backing. The recipient ends up with shares but zero wstETH attribution, and `calculateAmountToTransferWithYield` computes their WETH payout based on `_userWstETH`, so they receive zero WETH on redemption.

**Impact:**
Users who receive `BobVaultShares` via incremental small transfers have shares with no wstETH backing. Upon vault settlement they receive zero WETH despite holding valid shares. The sender retains all wstETH and receives a disproportionately large payout.

**Recommended Mitigation:**
Revert in `SablierLidoAdapter::updateStakedTokenBalance` if `wstETHToTransfer == 0` to prevent transfers that move no backing.

---

**[中文版本]**

**描述：**
`SablierLidoAdapter::updateStakedTokenBalance` 使用向下取整除法计算需转移的 wstETH 量。由于 wstETH 汇率低于 1:1（存入 N WETH 铸造 N 份额但产生少于 N 的 wstETH），任何 1 wei 的份额转账都会使计算结果取整为零。通过以 1 wei 为单位逐步转移 `BobVaultShares`，发送方可将任意数量的份额转给接收方，同时保留全部 wstETH 支撑，接收方持有份额但无 wstETH 归属，赎回时获得零 WETH。

**影響：**
通过小额增量转账接收 `BobVaultShares` 的用户持有无 wstETH 支撑的份额，vault 结算时尽管持有有效份额也会收到零 WETH；发送方保留全部 wstETH 并获得不成比例的高额赔付。

**修復建議：**
在 `SablierLidoAdapter::updateStakedTokenBalance` 中，若 `wstETHToTransfer == 0` 则 revert，防止不转移任何支撑的转账。

---

## 8. Incomplete mapping updates in `setVault` function cause vault address inconsistencies

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
`RWASegWrap::setVault` allows admins to update the vault address for a specific vault ID, but only updates `vaults[id] = vault` without maintaining the bidirectional `vaultIds` mapping. The old vault address remains mapped to the vault ID in `vaultIds`, while the new vault address is not registered. The `vaultIds` mapping is critical for vault validation in `isValidVault` and `getAssetId`, and is also used in `_addVault` to prevent duplicate vault registrations. The same issue exists in `SecuritizeRWASegWrap`.

**Impact:**
After a vault address update, the new vault address is not recognized as valid by the system, causing vault operations to fail or behave unexpectedly, while the old vault address may still appear valid even though it is no longer active.

**Recommended Mitigation:**
Update `setVault` to also delete the old vault's `vaultIds` entry and add the new vault's `vaultIds` entry: `delete vaultIds[oldVault]; vaultIds[vault] = id;`.

---

**[中文版本]**

**描述：**
`RWASegWrap::setVault` 允许管理员更新特定 vault ID 的地址，但仅更新 `vaults[id]` 而不维护双向 `vaultIds` 映射。旧 vault 地址仍映射到 vault ID，而新地址未被注册。`vaultIds` 映射对 `isValidVault`、`getAssetId` 和 `_addVault` 等函数的 vault 验证至关重要。

**影響：**
vault 地址更新后，新地址不被系统识别为有效，导致 vault 操作失败或行为异常，而旧地址可能仍被视为有效。

**修復建議：**
更新 `setVault` 以同时删除旧 vault 的 `vaultIds` 条目并添加新 vault 的条目：`delete vaultIds[oldVault]; vaultIds[vault] = id;`。

---

## 9. Insufficient duration validation in `STBL_Register::setupAsset` can lock user withdrawals

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
`STBL_Register::setupAsset` and `STBL_Register::setDurations` accept asset duration configurations without validating the relationship between `yieldDuration` and `duration`. The withdrawal logic in `iWithdraw` requires users to wait at least `yieldDuration` before withdrawing and also to withdraw before `duration` expires. When `yieldDuration > duration`, no valid time window exists within which a user can withdraw — the `yieldDuration` has not yet passed by the time `duration` expires. This creates a mathematically impossible withdrawal condition.

**Impact:**
Incorrectly configured asset durations permanently prevent user withdrawals. All deposited funds become inaccessible for the duration of the asset's lifecycle.

**Recommended Mitigation:**
Add a validation in `setupAsset` and `setDurations` that requires `yieldDuration <= duration` before accepting the configuration.

---

**[中文版本]**

**描述：**
`STBL_Register::setupAsset` 和 `setDurations` 在接受资产持续时间配置时未验证 `yieldDuration` 与 `duration` 的关系。提款逻辑要求用户等待至少 `yieldDuration`，同时必须在 `duration` 到期前提款。当 `yieldDuration > duration` 时，不存在有效的提款时间窗口，创造了数学上不可能的提款条件。

**影響：**
配置错误的资产持续时间会永久阻止用户提款，所有存入资金在资产生命周期内均无法访问。

**修復建議：**
在 `setupAsset` 和 `setDurations` 中添加验证，要求 `yieldDuration <= duration` 才接受配置。

---

## 10. Lack of Contract Address in Signed Payload Leads to Cross-Collection Replay Risk

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Panini America.txt`

**Description:**
`PaniniNFTs`' signature verification logic in `_verifySignature()` builds the signed message from `chainId`, `msg.sender`, `tokenIds`, `tokenURIs`, `requestNonce`, and `expiredAt` — but omits `address(this)`. Because the contract address is not included, the ECDSA signature is not bound to a specific collection instance. If the same operator key is used across multiple collections on the same chain (e.g., new deployments or upgradeable clones), a valid signature generated for Contract A can be replayed against Contract B as long as nonce conditions permit.

**Impact:**
Signatures can be replayed across different NFT contracts on the same chain, enabling unauthorized minting, unlocking, or locking actions on other collections that share operator keys. Trust boundaries between collections are weakened.

**Recommended Mitigation:**
Include `address(this)` in the encoded message payload within `_verifySignature()` to bind signatures to the specific contract instance.

---

**[中文版本]**

**描述：**
`PaniniNFTs` 的 `_verifySignature()` 构建签名消息时包含 `chainId`、`msg.sender`、`tokenIds` 等字段但遗漏了 `address(this)`。由于合约地址未包含在内，ECDSA 签名未绑定到特定合约实例。若同一运营商密钥用于同一链上的多个合约，为合约 A 生成的有效签名可在 nonce 条件允许时重放到合约 B。

**影響：**
签名可在同一链上不同 NFT 合约间重放，在共享运营商密钥的其他合约上实现未授权铸造、解锁或锁定操作，削弱合约间的信任边界。

**修復建議：**
在 `_verifySignature()` 的编码消息载荷中包含 `address(this)`，将签名绑定到特定合约实例。

---

## 11. Missing State Validation Enables Re-Subscription to An Active Level

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The `subscribeToLevel(uint256 level)` function allows a user to subscribe to the same level multiple times without any restriction. The function validates that the user is registered, that the main subscription is active, and that the previous level is active — but does not check whether the target `level` is already active for the caller. As a result, an already active level can be subscribed to again, overwriting the existing `LevelInfo` (resetting its activation timestamp) and re-charging the subscription fee.

**Impact:**
Users can be charged the subscription fee multiple times for the same level. Each re-subscription resets the level's activation timestamp, potentially resetting any time-based benefits or reward windows associated with that level.

**Recommended Mitigation:**
Add an explicit check before processing the subscription: `require(!isLevelActive(msg.sender, level), LevelAlreadySubscribed())`.

---

**[中文版本]**

**描述：**
`subscribeToLevel(uint256 level)` 函数允许用户无限制地重复订阅同一级别。函数验证了用户已注册、主订阅处于活跃状态、前一级别处于活跃状态，但未检查目标 `level` 是否已对调用者处于活跃状态。已活跃的级别可被再次订阅，覆盖现有 `LevelInfo`（重置激活时间戳）并重新收取订阅费。

**影響：**
用户可能为同一级别被多次收费，每次重新订阅都会重置级别的激活时间戳，可能重置与该级别相关的基于时间的权益或奖励窗口。

**修復建議：**
在处理订阅之前添加明确检查：`require(!isLevelActive(msg.sender, level), LevelAlreadySubscribed())`。

---

## 12. Missing Validation of Fallback APR Values in `AprPairFeed::latestRoundData`

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
`AprPairFeed::latestRoundData` fetches APRs from a preferred source (feed or strategy provider). When the feed is stale, it falls back to the strategy provider via `provider.getAprPair()`. However, unlike the primary feed path which may apply bounds validation, the fallback path returns the provider's values directly without any validation — not even the `ensureValidAprs` check or equivalent bounds enforcement. This allows potentially invalid or out-of-range APR values to be used by the protocol when the primary feed is unavailable.

**Impact:**
Invalid APR values from the fallback provider can corrupt yield calculations, causing incorrect distributions between senior and junior tranches.

**Recommended Mitigation:**
After fetching from the fallback provider, apply the same bounds validation that is used for the primary feed path (e.g., `ensureValidAprs` or equivalent checks).

---

**[中文版本]**

**描述：**
`AprPairFeed::latestRoundData` 在主要 feed 过期时回退到策略提供者获取 APR，但回退路径直接返回提供者的值而不进行任何验证，不像主要 feed 路径可能应用边界验证。这允许无效或超出范围的 APR 值在主要 feed 不可用时被协议使用。

**影響：**
回退提供者的无效 APR 值可能破坏收益计算，导致高级和初级 tranche 之间的分配不正确。

**修復建議：**
从回退提供者获取数据后，应用与主要 feed 路径相同的边界验证（如 `ensureValidAprs` 或等效检查）。

---

## 13. Missing controller validation in `AccountableAsyncRedeemVault::requestRedeem` allows zero address state

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
The `requestRedeem()` function fails to call `_checkController(controller)` validation before processing the request. Other similar functions in the vault that modify controller-keyed state call this validation, which enforces the `zeroControllerEmptyState` invariant ensuring that the zero address cannot accumulate vault state. Without this check, calling `requestRedeem` with `controller = address(0)` allows vault state fields (pending redeem requests, redeem shares, etc.) to be attributed to the zero address.

**Impact:**
The `zeroControllerEmptyState` invariant is violated, allowing the zero address to accumulate vault state including pending redeem requests. This can corrupt accounting and may be exploitable in certain vault state transitions.

**Recommended Mitigation:**
Add a call to `_checkController(controller)` at the beginning of `AccountableAsyncRedeemVault::requestRedeem`, consistent with other functions that modify controller-keyed vault state.

---

**[中文版本]**

**描述：**
`requestRedeem()` 函数在处理请求前未调用 `_checkController(controller)` 验证。其他修改 controller 键控状态的类似函数都调用此验证，以强制执行 `zeroControllerEmptyState` 不变量，确保零地址不能积累 vault 状态。缺少此检查使得以 `controller = address(0)` 调用 `requestRedeem` 可将 vault 状态归属于零地址。

**影響：**
违反 `zeroControllerEmptyState` 不变量，允许零地址积累 vault 状态，可能破坏核算并在某些 vault 状态转换中被利用。

**修復建議：**
在 `AccountableAsyncRedeemVault::requestRedeem` 开头添加 `_checkController(controller)` 调用，与其他修改 controller 键控 vault 状态的函数保持一致。

---

## 14. Missing mode field validation in walletclient allows handler selection via untrusted input

**Severity:** 🟡 Medium
**Source:** `cyfrin/connect.md`

**Description:**
The `WalletClient.connect()` method uses the dApp-provided `sessionRequest.mode` field to select between `TrustedConnectionHandler` (no OTP) and `UntrustedConnectionHandler` (OTP required) without any input validation or runtime type check. The `mode` field originates entirely from the dApp side and is embedded directly into the `SessionRequest`. No enum check, type guard, or wallet-side policy enforcement exists before handler selection. Any third-party wallet integrating the raw `WalletClient` library without independent security policy would allow a malicious dApp to set `mode: 'trusted'` and skip OTP verification.

**Impact:**
Third-party wallets using the library without independent policy enforcement are vulnerable to dApp-controlled bypassing of OTP security. This is a defense-in-depth gap in the library's public API.

**Recommended Mitigation:**
Add runtime validation of the `mode` field before handler selection: verify that `mode` is one of the expected enum values (`"trusted"` or `"untrusted"`) and throw an error for any other value.

---

**[中文版本]**

**描述：**
`WalletClient.connect()` 使用来自 dApp 的 `sessionRequest.mode` 字段在无 OTP 和需要 OTP 的连接处理器之间选择，但没有任何输入验证或运行时类型检查。`mode` 字段完全来自 dApp 侧，直接嵌入 `SessionRequest`，在处理器选择前不存在枚举检查或策略强制。任何未实现独立安全策略就集成原始 `WalletClient` 库的第三方钱包都会允许恶意 dApp 设置 `mode: 'trusted'` 跳过 OTP 验证。

**影響：**
未实现独立策略的第三方钱包易受 dApp 控制的 OTP 安全绕过攻击，这是库公共 API 中的深度防御缺口。

**修復建議：**
在处理器选择前添加 `mode` 字段的运行时验证：验证 `mode` 是预期枚举值之一（`"trusted"` 或 `"untrusted"`），对其他任何值抛出错误。

---

## 15. Missing zero address checks in `STBL_Register::setupAsset`

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
`STBL_Register::setupAsset` initializes several critical asset addresses — `_contractAddr`, `_issuanceAddr`, `_distAddr`, `_vaultAddr`, and `_oracle` — without any zero address validation. Notably, the corresponding setter functions (e.g., `setOracle`) do perform zero address checks. Since an asset can only be set up once, a misconfiguration with a zero address at setup time cannot be corrected by the setter functions.

**Impact:**
An accidental or malicious call to `setupAsset` with zero address parameters permanently misconfigures the asset, as there is no correction path. Subsequent protocol operations using the misconfigured asset will fail or behave unpredictably.

**Recommended Mitigation:**
Add zero address checks for all address parameters in `setupAsset`, consistent with the validation already present in the setter functions.

---

**[中文版本]**

**描述：**
`STBL_Register::setupAsset` 在初始化 `_contractAddr`、`_issuanceAddr`、`_distAddr`、`_vaultAddr` 和 `_oracle` 等关键资产地址时没有零地址验证。值得注意的是，相应的 setter 函数（如 `setOracle`）确实执行零地址检查。由于资产只能设置一次，在设置时使用零地址的错误配置无法通过 setter 函数纠正。

**影響：**
以零地址参数意外或恶意调用 `setupAsset` 会永久错误配置资产，且没有纠正路径，后续使用该错误配置资产的协议操作将失败或行为不可预测。

**修復建議：**
在 `setupAsset` 中为所有地址参数添加零地址检查，与 setter 函数中已有的验证保持一致。

---

## 16. Missing zero deposit amount validation

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeDepositor::deposit_USDe` enforces `require(amount > 0, "Deposit is zero")` to prevent zero-amount deposits, but the sister function `pUSDeDepositor::deposit_sUSDe` lacks this check. A similar inconsistency exists between `yUSDeDepositor::deposit_pUSDeDepositor` and `yUSDeDepositor::deposit_pUSDe`. Zero-amount deposits create vacuous storage operations and can corrupt vault share accounting if not handled properly.

**Impact:**
Users can submit zero-amount deposits that pass validation and trigger storage modifications without providing any actual value, potentially complicating accounting and wasting gas.

**Recommended Mitigation:**
Add `require(amount > 0, "Deposit is zero")` to `pUSDeDepositor::deposit_sUSDe` and the equivalent check to `yUSDeDepositor::deposit_pUSDe` for consistency across all deposit paths.

---

**[中文版本]**

**描述：**
`pUSDeDepositor::deposit_USDe` 强制执行 `require(amount > 0, "Deposit is zero")` 防止零金额存款，但其姐妹函数 `deposit_sUSDe` 缺少此检查。`yUSDeDepositor` 中也存在类似不一致。零金额存款会触发空洞的存储操作，可能破坏 vault 份额核算。

**影響：**
用户可提交通过验证的零金额存款，在不提供任何实际价值的情况下触发存储修改，可能复杂化核算并浪费 gas。

**修復建議：**
向 `pUSDeDepositor::deposit_sUSDe` 和 `yUSDeDepositor::deposit_pUSDe` 添加 `require(amount > 0, "Deposit is zero")` 检查，使所有存款路径保持一致。

---

## 17. `NegRiskAdapter::createEvent` allows different `closesAt` across outcome markets

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`NegRiskAdapter::createEvent` iterates over caller-supplied `marketParams` and creates one market per outcome without validating that all `marketParams[i].closesAt` values are identical. `MyriadCTFExchange::matchCrossMarketOrders` calls `_requireMarketOpen` for every order in the batch. The moment the earliest-closing market transitions to `closed`, any cross-market fill for the event reverts. Users holding YES positions in still-open markets lose their primary exit mechanism before the event has actually concluded.

**Impact:**
If outcome markets have different close times, early-closing markets prematurely break cross-market order matching for the entire event, stranding users in still-open markets without a functional exit path.

**Recommended Mitigation:**
In `createEvent`, validate that all `marketParams[i].closesAt` values are equal to `marketParams[0].closesAt` before creating any markets.

---

**[中文版本]**

**描述：**
`NegRiskAdapter::createEvent` 在不验证所有 `marketParams[i].closesAt` 值是否相同的情况下为每个结果创建市场。`MyriadCTFExchange::matchCrossMarketOrders` 对批次中每个订单调用 `_requireMarketOpen`，一旦最早关闭的市场进入 `closed` 状态，该事件的任何跨市场成交都会 revert。

**影響：**
若结果市场有不同的关闭时间，最早关闭的市场会过早破坏整个事件的跨市场订单匹配，使持有仍开放市场 YES 仓位的用户失去主要退出机制。

**修復建議：**
在 `createEvent` 中，在创建任何市场之前验证所有 `marketParams[i].closesAt` 值均等于 `marketParams[0].closesAt`。

---

## 18. Referral rewards accumulate to `address(0)` when players aren't referred

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DepositManager::_payEntryFee` unconditionally increments `referralRewards[gameId][Registry(registry).referrers(player)]` for every game entry. However, `Registry(registry).referrers(player)` returns `address(0)` when `player` has not been referred by anyone. As a result, all entry fees from non-referred players contribute to the `referralRewards` balance of `address(0)`, which can never be claimed by any legitimate referrer.

**Impact:**
Referral fee funds accumulate at `address(0)` and become permanently unclaimable, representing a leak of funds out of the game reward pool.

**Recommended Mitigation:**
Only allocate referral rewards when the player has actually been referred: wrap the increment in a check `if (Registry(registry).referrers(player) != address(0))`.

---

**[中文版本]**

**描述：**
`DepositManager::_payEntryFee` 无条件为每次游戏入场递增 `referralRewards[gameId][Registry(registry).referrers(player)]`。但当 `player` 没有推荐人时，`Registry(registry).referrers(player)` 返回 `address(0)`，导致未被推荐玩家的所有入场费积累到 `address(0)` 的推荐奖励余额中，永远无法被任何合法推荐人领取。

**影響：**
推荐费资金积累在 `address(0)` 处并永久无法领取，代表资金从游戏奖励池中泄漏。

**修復建議：**
仅在玩家实际上有推荐人时分配推荐奖励：用 `if (Registry(registry).referrers(player) != address(0))` 条件包裹递增操作。

---

## 19. Uninitialized `minWithdrawAmount` Allows Zero-Amount Forced Withdrawal Requests To Block Queue Processing

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `minWithdrawAmount` state variable in `InclusionQueue.sol` is never initialized during contract deployment, defaulting to 0. The `forceWithdrawalFromPool` function checks `require(amount >= minWithdrawAmount)`, which passes trivially for any amount including zero. However, when the zero-amount request reaches the queue processor, `Pool.executeOnChainWithdrawal()` requires `amount > 0` and reverts. Due to the strict FIFO queue enforcement in `Verifier.sol`, this zero-amount request permanently blocks all subsequent forced withdrawal requests. Although `setAmount()` can later configure a proper minimum, the window between deployment and that configuration allows attackers to poison the queue.

**Impact:**
An attacker can permanently block the forced withdrawal escape-hatch mechanism by queuing a zero-amount request before `minWithdrawAmount` is initialized. This creates a critical DoS on the forced withdrawal path with no on-chain recovery mechanism.

**Recommended Mitigation:**
Initialize `minWithdrawAmount` in the `initialize()` function with a value greater than zero, and add an explicit zero check in `forceWithdrawalFromPool` for the `amount` parameter.

---

**[中文版本]**

**描述：**
`InclusionQueue.sol` 中的 `minWithdrawAmount` 状态变量在合约部署时从未初始化，默认为 0。`forceWithdrawalFromPool` 检查 `require(amount >= minWithdrawAmount)` 对包括零在内的任何金额都能通过。但当零金额请求到达队列处理器时，`Pool.executeOnChainWithdrawal()` 要求 `amount > 0` 而 revert。由于 `Verifier.sol` 中严格的 FIFO 队列强制执行，这个零金额请求会永久阻塞所有后续的强制提款请求。

**影響：**
攻击者可在 `minWithdrawAmount` 初始化之前通过排队零金额请求永久阻塞强制提款紧急出口机制，造成对强制提款路径的关键拒绝服务，且没有链上恢复机制。

**修復建議：**
在 `initialize()` 函数中将 `minWithdrawAmount` 初始化为大于零的值，并在 `forceWithdrawalFromPool` 中对 `amount` 参数添加明确的零值检查。
