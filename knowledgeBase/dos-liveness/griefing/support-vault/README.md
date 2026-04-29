# support-vault (18)

> Issues affecting vault support mechanisms — ERC-165 compliance, smart contract wallet compatibility, and vault limit constraints.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Rewards Drain due to Invalid Last Claimed Period Update

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
The `_claimRewards` function in `Stargate.sol` calls `_claimableDelegationPeriods` to identify the period range for which delegation rewards are claimable, and then unconditionally stores `lastClaimablePeriod` as the new `lastClaimedPeriod`. However, `_claimableDelegationPeriods` may return `(0, 0)` under certain conditions — for instance when `endPeriod <= lastClaimedPeriod`, meaning all periods have already been claimed. When `(0, 0)` is returned and then written to `lastClaimedPeriod`, it effectively resets the pointer to the very beginning. The next call to `_claimRewards` will then treat all previously distributed periods as unclaimed, causing the full reward history to be distributed again. This loop can be repeated to drain the entire reward pool.

**Impact:**
An attacker can drain the entire protocol reward pool by repeatedly triggering `_claimRewards` when the `(0, 0)` condition is met, resetting `lastClaimedPeriod` to zero and re-claiming already-distributed rewards. This leads to infinite rewards drainage.

**Recommended Mitigation:**
Treat a `(0, 0)` return value from `_claimableDelegationPeriods` as invalid input and revert rather than writing it to storage. Add a guard: if `firstClaimablePeriod == 0 && lastClaimablePeriod == 0`, revert with `InvalidPeriod()`.

---

**[中文版本]**

**描述：**
`_claimRewards` 函数会将 `_claimableDelegationPeriods` 的返回值无条件写入 `lastClaimedPeriod`，但该函数在特定情况下可返回 `(0, 0)`。将 `(0, 0)` 写入后，`lastClaimedPeriod` 被重置为零，下次调用将重新分发所有已发放奖励，形成无限循环导致奖励池被耗尽。

**影響：**
攻击者可反复触发奖励重置，无限次重新领取已发放奖励，耗尽整个奖励池。

**修復建議：**
对 `_claimableDelegationPeriods` 返回 `(0, 0)` 的情况进行判断，直接回滚并抛出 `InvalidPeriod()` 错误，而非写入存储。

---

## 2. Security Mechanisms Inoperative due to OpenZeppelin v5 Hook Incompatibility

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
The `RYTStablecoin` contract uses OpenZeppelin v5.4.0 but implements the `_beforeTokenTransfer` hook that was removed in OpenZeppelin v5.0, replaced by `_update`. Since the parent ERC20 implementation in v5 never calls `_beforeTokenTransfer`, the contract's custom security logic — pausability and blocklisting — is effectively dead code. The `_pause()` function updates the pause state variable, but the `whenNotPaused` modifier on `_beforeTokenTransfer` is never triggered. Similarly, `addToBlocklist()` updates the mapping but the check inside `_beforeTokenTransfer` is never executed. This renders both security features completely non-functional.

**Impact:**
Both critical security features are inoperable: the PAUSER_ROLE cannot stop token transfers during emergencies such as bridge hacks or private key compromises, and blocklisted addresses can continue transferring tokens freely. This could lead to complete draining of liquidity pools or theft of user funds.

**Recommended Mitigation:**
Override the `_update` function (instead of `_beforeTokenTransfer`) to implement the pausability and blocklist checks, consistent with OpenZeppelin v5's hook architecture.

---

**[中文版本]**

**描述：**
`RYTStablecoin` 使用 OpenZeppelin v5.4.0，但实现了在 v5 中已被移除的 `_beforeTokenTransfer` 钩子（已由 `_update` 替代）。由于父合约不再调用 `_beforeTokenTransfer`，合约中的暂停和黑名单功能完全失效，成为死代码。

**影響：**
PAUSER_ROLE 无法在紧急情况下停止转账，黑名单地址可自由转账，可能导致流动性池被耗尽或用户资金被盗。

**修復建議：**
覆盖 `_update` 函数（而非 `_beforeTokenTransfer`）来实现暂停和黑名单检查，与 OpenZeppelin v5 的钩子架构保持一致。

---

## 3. Winner Selection Ignores Assigned Payout Positions Due To A Faulty If Condition

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
The `distributeFunds()` function in `Komiti.sol` is intended to select winners according to the order defined in `s_payoutPositions` mapping. The selection loop has a compound condition: `!s_hasReceivedPayout[groupId][member] && (winner == address(0) || s_payoutPositions[groupId][member] == selectedGroup.currentPayoutIndex)`. Because `winner == address(0)` is always true at the start of each payout round, the condition short-circuits and selects the first unpaid member unconditionally — completely ignoring the `s_payoutPositions` mapping. This means the payout order assignment via `setPayoutPositions()` has no practical effect on who receives funds first.

**Impact:**
The configured payout order is entirely bypassed. The first member in the array always wins regardless of their assigned position, violating the core invariant that payouts must follow the configured sequential or randomized order.

**Recommended Mitigation:**
Remove the `winner == address(0)` short-circuit condition from the selection logic so that `s_payoutPositions[groupId][member] == selectedGroup.currentPayoutIndex` is always evaluated as the sole selection criterion.

---

**[中文版本]**

**描述：**
`distributeFunds()` 中的胜者选择条件包含 `winner == address(0)` 短路逻辑，每轮开始时该条件始终为真，导致选择过程完全忽略 `s_payoutPositions` 映射，直接选出数组中第一个未付款成员，`setPayoutPositions()` 配置的付款顺序毫无作用。

**影響：**
付款顺序配置完全失效，数组中首位未付款成员始终获胜，违反核心不变量。

**修復建議：**
移除 `winner == address(0)` 短路条件，确保 `s_payoutPositions` 映射始终作为唯一选择标准被评估。

---

## 4. AUM inflated in vault kit strategies due to missing redemption fee deductions

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
In the `_get_aum` function of `aum_provider.cairo`, the vault allocator's share value in vault kit strategies is calculated using `convert_to_assets(balance_of(vault_allocator))`. However, `vault.cairo` is not fully ERC-4626 compatible and does not account for redemption fees in `preview_redeem`. The `convert_to_assets` implementation returns gross share values without deducting redemption fees. Since redemption fees are always charged when redemptions occur (if set), the AUM is consistently overstated by the amount of redemption fees that would be deducted on exit.

**Impact:**
The AUM is inflated because `convert_to_assets` returns values that do not account for redemption fees. This leads to overestimation of vault strategy value, distorting reporting and potentially misleading stakeholders about actual redeemable asset values.

**Recommended Mitigation:**
Subtract redemption fees from the share value when computing AUM for vault kit strategy positions.

---

**[中文版本]**

**描述：**
`aum_provider.cairo` 中的 `_get_aum` 函数使用 `convert_to_assets` 计算份额价值，但该函数不扣除赎回手续费。由于 `vault.cairo` 不完全兼容 ERC-4626，`preview_redeem` 也未考虑手续费，导致 AUM 被持续高估。

**影響：**
AUM 因未扣除赎回手续费而被虚高，导致 vault 策略价值估算失真。

**修復建議：**
在计算 vault 策略持仓的 AUM 时，从份额价值中扣除赎回手续费。

---

## 5. Accumulative reward setting to prevent overwrite and support incremental updates

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`Rewards::setRewardsAmountForEpochs` allows an authorized distributor to set a fixed reward amount for a range of future epochs. However, the function does not check whether rewards have already been set for the target epochs. Calling this function again for the same epochs silently overwrites the existing rewards: the previous reward amount remains locked in the contract with no mechanism to recover or redistribute the original tokens, while only the new amount will actually be distributed.

**Impact:**
Previously allocated rewards are overwritten and the corresponding tokens become permanently stranded in the contract with no mechanism to recover them. Distributors calling the function twice for the same epoch unintentionally lose the first batch of tokens.

**Recommended Mitigation:**
Add a guard clause to prevent overwriting rewards for epochs that already have a value set, or implement accumulative behavior by adding the new amount to any existing value rather than replacing it.

---

**[中文版本]**

**描述：**
`Rewards::setRewardsAmountForEpochs` 不检查目标 epoch 是否已设置奖励，重复调用会静默覆盖旧奖励，原代币被锁定在合约中无法取回，只有新金额会被分发。

**影響：**
旧奖励代币被永久锁死在合约中，分发者重复设置同一 epoch 时会不知不觉损失首批代币。

**修復建議：**
添加防覆盖保护，或实现累积模式将新金额叠加到现有值而非替换。

---

## 6. `BasisTradeTailor` is ERC-165 non compliant

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeTailor` inherits from and implements the `ITailor` interface but its `supportsInterface` implementation only calls `super.supportsInterface(interfaceId)`, which delegates to `AccessControlUpgradeable`. The parent contract has no knowledge of `ITailor` or `IERC1822Proxiable` (from `UUPSUpgradeable`) and returns `false` for their interface IDs. As a result, the contract incorrectly reports that it does not support interfaces it actually implements, breaking any integrations that rely on ERC-165 interface detection.

**Impact:**
External contracts and tools performing ERC-165 interface detection will incorrectly conclude that `BasisTradeTailor` does not implement `ITailor` or `IERC1822Proxiable`, potentially blocking integrations or upgrade proxy operations that depend on this check.

**Recommended Mitigation:**
Update `supportsInterface` to explicitly check for `ITailor` and `IERC1822Proxiable` interface IDs before delegating to `super.supportsInterface`.

---

**[中文版本]**

**描述：**
`BasisTradeTailor` 实现了 `ITailor` 接口，但 `supportsInterface` 仅委托给 `AccessControlUpgradeable`，后者不了解 `ITailor` 或 `IERC1822Proxiable`，导致接口查询始终返回 `false`，违反 ERC-165 标准。

**影響：**
依赖 ERC-165 接口检测的外部合约和工具会误认为合约不支持其已实现的接口，可能阻断集成或升级代理操作。

**修復建議：**
在 `supportsInterface` 中显式检查 `ITailor` 和 `IERC1822Proxiable` 接口 ID，再委托给 `super.supportsInterface`。

---

## 7. Decompression Bomb due to lack of post decompression size check

**Severity:** 🟡 Medium
**Source:** `cyfrin/connect.md`

**Description:**
The deeplink connection flow in MetaMask Mobile enforces a 1 MB size limit on the compressed, base64-encoded payload but never validates the size of the decompressed output. A crafted ~26 KB deeplink trivially passes the guard and forces `pako.inflate()` to allocate an unbounded amount of heap memory. The wallet processes the bomb silently, establishing a full connection and persisting it to storage, with no error surfaced to the user. A 1 MB compressed stream encodes to ~1.33 MB base64, so the effective compressed budget is ~750 KB. A single maximum-budget deeplink can force up to ~578 MB of heap allocation in one call. No authentication, no user account, and no existing session are required — the entire attack surface is reachable with a tap on a malicious `metamask://` URL.

**Impact:**
A crafted compressed payload of ~750 KB (which passes the 1 MB base64 check) can expand to 500 MB+ of JSON data. `JSON.parse()` on the resulting oversized string exhausts mobile process memory and crashes the MetaMask app. The attack requires no authentication and is exploitable by any party that can deliver a deeplink to the target device.

**Recommended Mitigation:**
After decompression, validate the output size against a reasonable limit (e.g., 5 MB) before proceeding with JSON parsing. Pass a `chunkSize` or `maxOutputLength` parameter to `pako.inflate()` if supported, or implement a streaming approach that rejects oversized outputs early.

---

**[中文版本]**

**描述：**
MetaMask Mobile 的深链接连接流程对压缩后 base64 编码的载荷限制 1 MB，但从不验证解压后的大小。精心构造的 ~26 KB 深链接轻松通过检查，迫使 `pako.inflate()` 分配无限堆内存。最大预算的深链接可触发高达 ~578 MB 的内存分配，无需认证即可通过 `metamask://` URL 发起攻击。

**影響：**
~750 KB 的压缩载荷可扩展为 500 MB 以上的 JSON 数据，`JSON.parse()` 耗尽移动端内存并崩溃 MetaMask 应用。

**修復建議：**
解压后验证输出大小（如限制 5 MB），在 JSON 解析前拒绝过大输出；或为 `pako.inflate()` 传入 `chunkSize` 参数实现流式拒绝。

---

## 8. `DelegationManager` is incompatible with smart contract wallets with Approved hashes

**Severity:** 🟡 Medium
**Source:** `cyfrin/DelegationFramework1.md`

**Description:**
`DelegationManager::redeemDelegations` rejects any delegation where `delegation_.signature.length == 0` by reverting with `EmptySignature()`. This happens before the smart contract wallet branch. Safe wallets (and similar smart contract wallets) use a pattern where an empty signature triggers checking of pre-approved hashes — calling `isValidSignature` with an empty signature is the intended mechanism. Since `DelegationManager` rejects empty signatures before ever calling `isValidSignature`, Safe wallets cannot use their pre-approved hash mechanism to authorize delegations.

**Impact:**
Safe wallets and other smart contract wallets that rely on pre-approved hashes for authorization cannot use them with delegations. This limits compatibility with one of the most widely used smart contract wallet patterns for institutional and DAO use cases.

**Recommended Mitigation:**
Apply the empty signature check only to EOAs (i.e., check `delegation_.delegator.code.length == 0` first and only then check `signature.length == 0`). Alternatively, explicitly document that Safe wallet pre-approved hashes are not supported.

---

**[中文版本]**

**描述：**
`redeemDelegations` 在检查智能合约钱包分支前，就以 `EmptySignature()` 拒绝所有空签名委托。Safe 等智能合约钱包的预批准哈希机制依赖空签名触发 `isValidSignature` 检查，但这在 `DelegationManager` 中被提前拦截，导致无法使用该机制。

**影響：**
依赖预批准哈希的智能合约钱包无法授权委托，影响机构和 DAO 用例的兼容性。

**修復建議：**
仅对 EOA 执行空签名检查（先判断 `code.length == 0`），或明确文档说明不支持预批准哈希机制。

---

## 9. Double Fee Charged in Limit Order Execution Due to Aggregator Fee Overlap

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
The `LimitOrderModule::fillOrder` function executes a swap via `aggregator.swap(swapParams)` and then independently calculates a 10 bps (0.1%) fee on the returned `amountOut`, transferring it to `feeRecipient`. However, `CoreAggregator.swap()` already deducts its own protocol-level fee from the output amount before returning it. This results in two separate fees being charged on the same output: the aggregator deducts its configurable `feeBps` first, and then `LimitOrderModule` deducts an additional 10 bps on top — contradicting the architecture described in the README which presents them as separate, non-overlapping fees.

**Impact:**
Users executing limit orders are charged both the aggregator fee and the limit order fee, resulting in higher-than-expected total fees and a net output amount below the stated minimum.

**Recommended Mitigation:**
Ensure `LimitOrderModule` disables the aggregator fee (e.g., by setting `feeBps = 0`) before the swap, using a fee-free aggregator path or an internal flag, to prevent double-counting.

---

**[中文版本]**

**描述：**
`LimitOrderModule::fillOrder` 调用 `aggregator.swap` 后再次对返回的 `amountOut` 收取 10 bps 手续费，但 `CoreAggregator.swap()` 已在返回前扣除了自己的协议手续费，导致同一笔输出被双重收费。

**影響：**
执行限价订单的用户承担聚合器手续费和限价订单手续费双重费用，实际输出低于预期。

**修復建議：**
`LimitOrderModule` 调用聚合器前将 `feeBps` 设为 0（使用无费用路径或内部标志），避免双重计费。

---

## 10. ERC 1155 `safeTransferFrom` callbacks forward unbounded gas to EIP 7702 EOAs

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
When `MyriadCTFExchange` distributes outcome tokens to traders, every transfer calls ERC-1155 `safeTransferFrom`, which checks if the recipient has code and invokes `onERC1155Received` with no explicit gas cap. With EIP-7702, an EOA can set a delegation designator, causing `to.code.length > 0` to evaluate to `true`. This triggers a full callback. In `matchCrossMarketOrders`, the most dangerous path iterates over every order in a loop — an attacker at index `i=0` receives the callback first and can burn enough gas to starve all subsequent iterations, reverting the entire batch. The same applies to `_settleMintMatch` (sequential transfers) and `_settleDirectMatch` (single transfer).

**Impact:**
An EIP-7702-enabled EOA can siphon the operator's gas to subsidize expensive on-chain operations, or burn enough gas to revert the entire settlement transaction, causing honest traders' fills to fail with an out-of-gas error.

**Recommended Mitigation:**
Wrap each `safeTransferFrom` where `to` is an arbitrary trader in a low-level call with an explicit gas cap, so that no single callback can consume the gas budget needed for subsequent iterations.

---

**[中文版本]**

**描述：**
`MyriadCTFExchange` 分发代币时，ERC-1155 `safeTransferFrom` 对有代码的接收方调用 `onERC1155Received` 且无 gas 上限。EIP-7702 使 EOA 也可拥有代码，攻击者可在批量结算循环中消耗大量 gas 导致整批交易回滚。

**影響：**
攻击者可消耗操作员 gas 或触发 out-of-gas 回滚，导致诚实交易者的成交失败。

**修復建議：**
对任意交易者的 `safeTransferFrom` 使用低层调用并设置明确 gas 上限，防止单次回调耗尽后续迭代的 gas 预算。

---

## 11. `FeeModule::_lookupFees` returns zero fees at price = 1e18 due to strict less-than comparison

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`FeeModule::_lookupFees` iterates over fee tiers using a strict less-than comparison (`price < tiers[i].maxPrice`). Since the maximum tier boundary is validated as `<= 1e18`, a trade at exactly `price = 1e18` (representing a 100% probability outcome) will not match any tier and fall through to the default `return (0, 0)`. A price of 1e18 is explicitly allowed by `_matchOrders` which validates `maker.price <= ONE && taker.price <= ONE`.

**Impact:**
Trades at `price = 1e18` pay zero fees even when the fee admin intended them to be covered by the highest configured tier. This represents fee revenue leakage for the protocol.

**Recommended Mitigation:**
Change the comparison to less-than-or-equal (`price <= tiers[i].maxPrice`) so that the highest tier correctly captures trades at exactly `price = 1e18`.

---

**[中文版本]**

**描述：**
`_lookupFees` 使用严格小于比较 `price < tiers[i].maxPrice`，当 `price` 恰好等于 1e18（最高层边界）时无法匹配任何层级，返回零手续费。`_matchOrders` 允许 `price <= ONE`，因此 `price = 1e18` 是合法价格。

**影響：**
`price = 1e18` 的交易免费执行，导致协议手续费收入泄漏。

**修復建議：**
将比较改为小于等于 `price <= tiers[i].maxPrice`，确保最高层级正确捕获 `price = 1e18` 的交易。

---

## 12. Lack of multicall support for `FeeOverrideHooklet::setFeeOverride`

**Severity:** 🟡 Medium
**Source:** `cyfrin/hooklet.md`

**Description:**
`FeeOverrideHooklet::setFeeOverride` relies on `msg.sender` when validating ownership of the corresponding `BunniToken`. When invoked through a multicaller contract, `msg.sender` becomes the multicaller's address rather than the original caller's address, causing the ownership validation to fail even when the actual pool owner initiates the call. Since `LibMulticaller` is used extensively throughout the core Bunni contracts, pool owners interacting via multicall would be systematically blocked from using `setFeeOverride`.

**Impact:**
Any legitimate pool owner interacting with `FeeOverrideHooklet` via a multicaller contract is incorrectly prevented from doing so, breaking external integrations that rely on multicall batching.

**Recommended Mitigation:**
Replace direct `msg.sender` usage with `LibMulticaller::senderOrSigner` to remain consistent with the core Bunni contracts, preserving compatibility with both direct and batched calls.

---

**[中文版本]**

**描述：**
`setFeeOverride` 使用 `msg.sender` 验证 `BunniToken` 所有权，通过 multicaller 合约调用时 `msg.sender` 变为 multicaller 地址，导致所有权验证失败，即便原始调用者是真正的 pool owner。

**影響：**
通过 multicall 批量操作的合法 pool owner 无法使用 `setFeeOverride`，破坏依赖 multicall 的外部集成。

**修復建議：**
将 `msg.sender` 替换为 `LibMulticaller::senderOrSigner`，与核心 Bunni 合约保持一致，支持直接调用和批量调用。

---

## 13. Malicious investor can register wallets that belong to other investors

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
The `addWalletByInvestor` function in `RegistryService.sol` allows any registered investor to claim ownership of any wallet address not currently in the `investorsWallets` mapping. The function only checks that the caller is a registered investor and that the wallet is not a special wallet — it does not verify that the caller actually controls the wallet being registered. A malicious registered investor can front-run legitimate wallet registration transactions, claiming the target wallet address before the rightful owner.

**Impact:**
A malicious investor can front-run `addWallet`, `updateInvestor`, and `addWalletByInvestor` calls to hijack wallet ownership. This DoS-es those functions for the legitimate owner and can redirect token issuances meant for other investors to the attacker's registered wallet, as `issueTokensCustom` uses the stored wallet mapping to mint tokens.

**Recommended Mitigation:**
Remove `addWalletByInvestor` entirely, or require proof-of-ownership verification (e.g., a signature from the wallet being registered) to ensure only the controller of an address can register it.

---

**[中文版本]**

**描述：**
`addWalletByInvestor` 允许任何已注册投资者将任意未注册地址声称为自己的钱包，而不验证调用者是否实际控制该地址。恶意投资者可抢先注册受害者即将使用的钱包地址。

**影響：**
攻击者可劫持钱包所有权，对合法用户的注册操作发起 DoS，并将原本应发给受害者的代币铸造至自己控制的钱包。

**修復建議：**
完全移除 `addWalletByInvestor`，或要求提供被注册地址的签名以证明控制权。

---

## 14. `PoketFactory` is ERC-165 non compilant

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`PocketFactory` implements `IPocketFactory` but its `supportsInterface` function does not check for the `IPocketFactory` interface ID. The implementation only calls `super.supportsInterface(interfaceId)`, which delegates to `AccessControlEnumerable`. That parent has no knowledge of `IPocketFactory`, so `pocketFactory.supportsInterface(type(IPocketFactory).interfaceId)` returns `false` even though the contract fully implements the interface, violating the ERC-165 standard.

**Impact:**
External contracts and tooling that rely on ERC-165 for interface detection will incorrectly conclude that `PocketFactory` does not implement `IPocketFactory`, potentially preventing integration with systems that verify interface support before interacting.

**Recommended Mitigation:**
Update `supportsInterface` to explicitly check for `IPocketFactory` in addition to delegating to `super.supportsInterface`.

---

**[中文版本]**

**描述：**
`PocketFactory` 实现了 `IPocketFactory` 但 `supportsInterface` 只委托给 `AccessControlEnumerable`，后者不了解 `IPocketFactory`，导致接口查询返回 `false`，违反 ERC-165 标准。

**影響：**
依赖 ERC-165 接口检测的外部合约和工具会误认为合约不支持其已实现的接口。

**修復建議：**
在 `supportsInterface` 中显式添加对 `IPocketFactory` 接口 ID 的检查。

---

## 15. Smart contract wallets cannot sign orders due to missing ERC 1271 support

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`MyriadCTFExchange::_validateOrder` uses `ECDSA.tryRecover` exclusively to validate order signatures. This means only EOAs can sign orders — smart contract wallets (Safe multisigs, Argent, ERC-4337 accounts) cannot participate in the CLOB because they cannot produce ECDSA signatures that recover to their contract address.

**Impact:**
All smart contract wallets — including institutional multisigs, DAOs, and account-abstracted wallets — are excluded from trading on the CLOB. This reduces the protocol's addressable market and excludes participants who use smart contract wallets for security best practices.

**Recommended Mitigation:**
Use OpenZeppelin's `SignatureChecker.isValidSignatureNow` which transparently handles both ECDSA and ERC-1271 validation, enabling smart contract wallets to participate.

---

**[中文版本]**

**描述：**
`_validateOrder` 仅使用 `ECDSA.tryRecover` 验证签名，无法恢复到合约地址，导致智能合约钱包（Safe 多签、Argent、ERC-4337 账户等）无法在 CLOB 上下单。

**影響：**
所有智能合约钱包被排除在外，包括机构多签和 DAO，减少协议可触达市场并排斥安全最佳实践用户。

**修復建議：**
使用 OpenZeppelin 的 `SignatureChecker.isValidSignatureNow`，同时支持 ECDSA 和 ERC-1271 验证。

---

## 16. Some SherpaUSD can never be unstaked due to `minimumSupply` check

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault::_unstake` includes a check ensuring total staked assets never fall below `minimumSupply` while remaining above zero. If `minimumSupply` is non-trivial (e.g., 1000 SherpaUSD), a malicious user can deposit a tiny amount (e.g., 1 wei) on top of the minimum deposit, permanently preventing another user from withdrawing their funds. For example: Alice deposits exactly 1000 SherpaUSD (equal to `minimumSupply`). Bob deposits 1 wei. Alice now cannot exit because withdrawing her full stake would leave `1 wei` — which is greater than 0 but less than `minimumSupply`, triggering the `MinimumSupplyNotMet` revert.

**Impact:**
A malicious actor can permanently lock another user's staked tokens by depositing a negligible amount that keeps the vault above zero but within the minimum supply threshold. Alice can only withdraw 1 wei while the rest is permanently locked.

**Recommended Mitigation:**
Implement a setter function to keep `minimumSupply` configurable (allowing it to be reduced to zero to unlock stuck funds), and/or add a per-deposit minimum check to prevent dust deposits from causing this condition.

---

**[中文版本]**

**描述：**
`_unstake` 的最小供应量检查要求总质押量不能低于 `minimumSupply` 且大于零。恶意用户只需存入 1 wei，就能使 Alice 无法完全提取资金——因为提款后剩余 1 wei 大于 0 但小于 `minimumSupply`，触发 `MinimumSupplyNotMet` 回滚。

**影響：**
攻击者可用极少量存款永久锁定他人质押资金，受害者只能提取 1 wei，其余全部永久锁定。

**修復建議：**
实现 `minimumSupply` 可配置的 setter 函数（允许降为零以解锁卡住资金），并/或添加最小存款检查防止粉尘存款引发此问题。

---

## 17. Use `SignatureChecker` library and optionally support `EIP7702` accounts which use their private key to sign

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DocumentManager::verifySignature` uses a manual EOA/SCA branching pattern: if `signer.code.length == 0` it uses `ECDSA.tryRecover`, otherwise it manually calls `isValidSignature` via a raw static call. This is more error-prone than using OpenZeppelin's `SignatureChecker`. Additionally, with EIP-7702, an EOA can have `code.length > 0` while still signing with its private key. The current branching logic would incorrectly route these accounts to the SCA path, causing their ECDSA signatures to fail against the `isValidSignature` interface.

**Impact:**
EIP-7702 accounts using their private key to sign will fail verification in `DocumentManager::verifySignature` due to incorrect routing to the SCA branch. This excludes a valid and increasingly common account type from the protocol.

**Recommended Mitigation:**
Replace the manual branching with `SignatureChecker.isValidSignatureNow` for simplicity. For full EIP-7702 support, first attempt `ECDSA.tryRecover` and only fall back to `SignatureChecker.isValidERC1271SignatureNow` if ECDSA recovery fails.

---

**[中文版本]**

**描述：**
`verifySignature` 使用手动 EOA/SCA 分支逻辑，通过 `code.length` 区分账户类型。EIP-7702 使 EOA 也可有 `code.length > 0` 但仍使用私钥签名，这类账户会被错误路由到 SCA 分支，导致 ECDSA 签名验证失败。

**影響：**
使用私钥签名的 EIP-7702 账户无法通过验证，被排除在协议之外。

**修復建議：**
使用 `SignatureChecker.isValidSignatureNow` 替代手动分支；完整支持 EIP-7702 时，先尝试 `ECDSA.tryRecover`，失败后再回退到 `SignatureChecker.isValidERC1271SignatureNow`。

---

## 18. Vault limit cannot be modified if vault is already enabled

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
The `updateVaultMaxL1Limit` function reverts with `MapWithTimeData__AlreadyEnabled` when attempting to update a vault's limit if the vault is already enabled. This occurs because the function unconditionally calls `vaults.enable(vault)` for any non-zero limit, and `enable()` fails when the vault is already in an enabled state. This means the owner cannot adjust vault limits upward or downward without first explicitly disabling the vault.

**Impact:**
The contract owner cannot update vault limits for already-enabled vaults without first disabling them, introducing unintuitive two-step friction and potentially blocking timely limit adjustments needed for operational management.

**Recommended Mitigation:**
Modify `updateVaultMaxL1Limit` to check the vault's current enabled state before calling `vaults.enable` or `vaults.disable`, only triggering a state transition when an actual change is needed.

---

**[中文版本]**

**描述：**
`updateVaultMaxL1Limit` 对非零限额无条件调用 `vaults.enable(vault)`，但 vault 已处于启用状态时 `enable()` 会回滚并抛出 `MapWithTimeData__AlreadyEnabled`，导致所有者无法直接更新已启用 vault 的限额。

**影響：**
合约所有者无法在不先禁用 vault 的情况下调整限额，引入不直观的两步操作，可能阻碍及时的运营管理。

**修復建議：**
在 `updateVaultMaxL1Limit` 中先检查 vault 当前启用状态，仅在需要实际状态转换时才调用 `enable` 或 `disable`。
