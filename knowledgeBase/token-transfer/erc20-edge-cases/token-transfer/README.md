# token-transfer (20)

> Issues where token transfer logic fails for non-standard tokens, incorrect value calculations, or missing validations.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Inverted isDirect Flag Logic Causes ERC20 Tokens to Not Be Collected in Direct Swaps

**Severity:** 🔴 Critical
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
In `_executeOrder`, the `isDirect` flag in `SwapData` is set to `_sender == trustedForwarder`. When a user calls `simpleSwap` or `partialSwap` directly, `_sender` is the user's own address, not the trusted forwarder, so `isDirect` evaluates to `false`. In `_takeFunds`, ERC20 token collection only executes when `isDirect` is `true`. As a result, when users call swap functions directly, the contract skips collecting ERC20 tokens from the user entirely, releases maker tokens to the user without receiving taker tokens in return, and allows drainage of all pre-funded ERC20 liquidity.

**Impact:**
Any user calling `simpleSwap` or `partialSwap` directly can receive maker tokens without paying taker tokens, enabling complete drainage of any pre-funded ERC20 liquidity pool. This is a critical fund loss vulnerability.

**Recommended Mitigation:**
Invert the flag assignment to correctly identify direct calls: `isDirect: _sender != trustedForwarder`, so that ERC20 collection is performed for direct user calls as intended.

---

**[中文版本]**

**描述：**
`_executeOrder` 中 `isDirect` 标志被错误地设置为 `_sender == trustedForwarder`，当用户直接调用兑换函数时该值为 `false`。`_takeFunds` 中的 ERC20 代币收取逻辑仅在 `isDirect` 为 `true` 时执行，导致直接调用时跳过代币收取，合约在未收到用户代币的情况下释放出 maker 代币，允许任意用户耗尽预存的 ERC20 流动性。

**影響：**
任何直接调用兑换函数的用户均可在不付出代币的情况下获得 maker 代币，导致预存 ERC20 流动性被完全耗尽，属于严重资金损失漏洞。

**修復建議：**
将标志赋值修改为 `isDirect: _sender != trustedForwarder`，确保直接调用时正确执行 ERC20 代币收取。

---

## 2. Delegate Spending Cap Bypass via Token Selection Allows Draining Payer Funds Beyond Intended Limits

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The `DelegateConfig` struct tracks spending controls (`maxPerSession`, `totalCap`, `spent`) to protect payers against delegate overspending, but these controls compare raw token amounts without any reference to which token is being used. The struct has no `allowedToken` field, and the delegate freely selects the payment token at session creation via `createSessionForModelAsDelegate`. A delegate can first deplete the cap using a low-value token (e.g., one with 2 decimals) and then switch to a high-value token in subsequent sessions, effectively spending far more in economic terms than the payer intended to authorize.

**Impact:**
Delegates can drain payer funds well beyond the intended spending limit by selecting tokens with different decimal counts or market values, circumventing the economic protections the cap is designed to provide.

**Recommended Mitigation:**
Add an `allowedToken` field to `DelegateConfig` that the payer specifies when granting a delegation. Enforce that `session.paymentToken` matches `DelegateConfig.allowedToken` before applying the spending cap check, preventing cross-token cap bypass.

---

**[中文版本]**

**描述：**
`DelegateConfig` 结构体通过原始代币数量追踪支出限额，但未限定可使用的代币类型，委托人可在创建会话时自由选择支付代币。攻击者可先使用低价值代币耗尽限额，再切换高价值代币，实际消耗的经济价值远超付款人的授权意图。

**影響：**
委托人可通过选择不同精度或市值的代币，绕过支出限额保护，从付款人账户取走远超预期的资金。

**修復建議：**
在 `DelegateConfig` 中增加 `allowedToken` 字段，要求付款人在授权时指定允许使用的代币，并在支出限额检查前验证 `session.paymentToken` 与 `DelegateConfig.allowedToken` 一致，防止跨代币绕过。

---

## 3. More value can be extracted by liquidations than expected due to incorrect transfer calculations when the violator does not own the total ERC-6909 supply for each tokenId enabled as collateral

**Severity:** 🟠 High
**Source:** `cyfrin/vii.md`

**Description:**
`ERC721WrapperBase::transfer` calculates the proportional amount of ERC-6909 tokens to transfer from sender to receiver using `normalizedToFull`. The function multiplies by `totalSupply(tokenId)` instead of the sender's actual ERC-6909 balance for that token. When the sender owns less than 100% of the total supply for a given `tokenId`, the calculated transfer amount is inflated relative to the sender's actual proportional share, causing the liquidator to extract more value in unit-of-account terms than was requested.

**Impact:**
Liquidated accounts incur larger losses than expected because the transfer overcalculates collateral seized. This can be triggered by partial liquidation or by a borrower transferring a portion of their position to a separate address. In extreme cases, repeated partial liquidation extracts a disproportionate share of a borrower's collateral.

**Recommended Mitigation:**
In `normalizedToFull`, replace `totalSupply(tokenId)` with the sender's ERC-6909 balance for that specific `tokenId`, so the proportional transfer amount correctly reflects the sender's fractional ownership rather than the total supply.

---

**[中文版本]**

**描述：**
`ERC721WrapperBase::transfer` 通过 `normalizedToFull` 计算应转移的 ERC-6909 代币数量时，错误地乘以 `totalSupply(tokenId)` 而非发送方对该 token 的实际 ERC-6909 余额。当发送方持有的 ERC-6909 占比不足 100% 时，计算出的转移量被虚高，导致清算方提取的价值超过请求数量。

**影響：**
被清算账户承受超出预期的损失，可通过部分清算或借款人将部分仓位转移至其他地址来触发，极端情况下反复局部清算可耗尽借款人的过多抵押品。

**修復建議：**
在 `normalizedToFull` 中将 `totalSupply(tokenId)` 替换为发送方对该特定 `tokenId` 的 ERC-6909 余额，使比例转移量正确反映发送方的分数所有权。

---

## 4. Not all reward token rewards are claimable

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
In the `Rewards` contract, the mappings `lastEpochClaimedStaker`, `lastEpochClaimedCurator`, and `lastEpochClaimedOperator` track the last epoch for which each address has claimed rewards, but are keyed only by address and not by reward token. When a staker, curator, or operator claims rewards for a given epoch and reward token, the contract updates the last-claimed epoch for all tokens simultaneously. If the same address is eligible for rewards from multiple tokens across the same epoch range, claiming for one token permanently marks all those epochs as claimed for every other token, making the remaining token rewards unclaimable.

**Impact:**
Stakers, curators, and operators eligible for multi-token rewards lose all but the first token's rewards for any epoch range once they initiate a claim. This constitutes a direct loss of earned rewards and breaks the expected multi-token reward distribution behavior.

**Recommended Mitigation:**
Change the last-claimed mappings to be keyed by `(address, rewardToken)` rather than just `address`, so that claiming for one token does not mark epochs as claimed for other tokens.

---

**[中文版本]**

**描述：**
`Rewards` 合约中追踪最后领取 epoch 的映射仅以地址为键，而非以 `(地址, 奖励代币)` 为键。当用户针对某一 epoch 范围和某一奖励代币发起领取时，合约同时更新该地址在所有代币上的最后领取 epoch，导致同一 epoch 范围内其他代币的奖励无法再被领取。

**影響：**
符合多代币奖励资格的质押者、策展人和运营商，在首次领取后将永久失去同一 epoch 范围内其他所有代币的奖励，属于直接的已赚奖励损失。

**修復建議：**
将最后领取映射的键从单一地址改为 `(地址, 奖励代币)` 的组合，确保对一种代币的领取不影响其他代币的 epoch 记录。

---

## 5. Token Pricing Assumes All Payment Tokens Have Same Decimals And Price

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The pricing logic in `NodeRegistryWithModelsUpgradeable` treats multiple ERC20 payment tokens as if they share the same decimal convention and stable price. When no token-specific price is configured, the same fallback value is applied to every accepted token. The contract never normalizes for token decimals or distinct economic values, so minimum-price checks and session economics can be completely wrong for any token differing in decimals or price from the stable-coin assumption. For example, a token with 18 decimals produces a `maxTokens` calculation 10^12 times larger than one with 6 decimals for the same economic deposit.

**Impact:**
Session economics are incorrectly calculated for any non-18-decimal or non-$1 token. Payers can create sessions that consume far more or far fewer tokens than intended, causing broken incentive accounting, potential underpayment to hosts, and systematic manipulation of the pricing system.

**Recommended Mitigation:**
Normalize all token amounts to a common unit of account (e.g., USD with 18 decimal precision) using each token's price and decimal count before applying pricing logic. Require per-token price configuration and reject sessions for tokens without an explicit price setting.

---

**[中文版本]**

**描述：**
`NodeRegistryWithModelsUpgradeable` 的定价逻辑对所有 ERC20 支付代币使用相同的回退值，既不区分代币精度也不区分经济价值。以 18 位精度代币与 6 位精度代币为例，在相同经济存款下，前者计算出的 `maxTokens` 是后者的 10^12 倍，导致会话经济完全错误。

**影響：**
对任何非 18 精度或非 $1 价值的代币，会话经济计算均失误，付款人可创建严重低付或高付的会话，破坏激励机制并导致主机收益错误。

**修復建議：**
在应用定价逻辑前，利用每种代币的价格和精度将所有代币数量归一化为统一记账单位（如 18 精度的 USD），并要求为每种代币单独配置价格，拒绝未明确设置价格的代币创建会话。

---

## 6. BetFactory::setPool should validate input pool is legitimate AaveV3 pool and supports input token

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`BetFactory::setPool` allows the owner to associate any address as an Aave pool for a given token without any on-chain validation. There is no check that the input `_pool` matches the canonical `PoolAddressesProvider::getPool` address, nor that the input `_token` is actually supported by the pool via `Pool::getReserveAToken`. This means the owner could inadvertently or maliciously configure a non-Aave or incompatible pool, causing all bets using that token and pool to behave unexpectedly.

**Impact:**
An illegitimate or misconfigured pool can cause bet initialization to silently accept an unsafe pool, leading to loss of funds for makers and takers whose assets are deposited into an unintended contract.

**Recommended Mitigation:**
In `BetFactory::setPool`, verify that `_pool` equals `AAVE_ADDRESSES_PROVIDER.getPool()` and that `_pool.getReserveAToken(_token)` returns a non-zero address, ensuring only a legitimate AaveV3 pool supporting the specified token can be configured.

---

**[中文版本]**

**描述：**
`BetFactory::setPool` 允许所有者为指定代币关联任意地址作为 Aave 池，但未进行任何链上验证，既不检查 `_pool` 是否为 `PoolAddressesProvider::getPool` 的规范地址，也不验证 `_token` 是否被该池支持，可能导致错误配置不兼容的池。

**影響：**
非法或错误配置的池会导致 bet 初始化静默接受不安全池，maker 和 taker 的资产被存入非预期合约，造成资金损失。

**修復建議：**
在 `BetFactory::setPool` 中验证 `_pool` 等于 `AAVE_ADDRESSES_PROVIDER.getPool()`，并且 `_pool.getReserveAToken(_token)` 返回非零地址，确保只能配置支持指定代币的合法 AaveV3 池。

---

## 7. Expired Tokens Permanently Locked Due to Burn Restriction

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/S3 Markets.txt`

**Description:**
The `EAC1155` contract manages Environmental Attribute Certificates with expiration dates. The `burn` and `burnBatch` functions are restricted to the `BURNER_ROLE` but also enforce `_checkExpiry(id)` before executing any burn logic, which reverts if `block.timestamp > expiry`. Once a certificate token reaches its expiry timestamp, neither authorized burners nor any other party can remove it from circulation: the burn function itself enforces the same expiry check that prevents transfers, creating a permanent deadlock where expired tokens can never be cleaned up.

**Impact:**
Expired EAC tokens become permanently locked in user wallets and the ledger, accumulating over time as "zombie" tokens. The growing backlog of unclearable expired tokens wastes gas on iteration, pollutes the ledger, and prevents the protocol from maintaining a clean token state.

**Recommended Mitigation:**
Remove the expiry check from the `burn` and `burnBatch` functions, or add a separate `burnExpired` function accessible to the `BURNER_ROLE` that skips the expiry restriction, allowing authorized parties to clean up expired tokens.

---

**[中文版本]**

**描述：**
`EAC1155` 合约中，`burn` 和 `burnBatch` 函数在执行销毁逻辑前同样调用 `_checkExpiry(id)`，若 `block.timestamp > expiry` 则回滚。一旦证书到期，即便是持有 `BURNER_ROLE` 的授权角色也无法销毁该代币，形成永久僵局，过期代币永远无法从账本中清除。

**影響：**
过期的 EAC 代币作为"僵尸代币"永久锁定在用户钱包和账本中，随时间积累，浪费遍历 gas，污染账本，阻碍协议维护清洁的代币状态。

**修復建議：**
从 `burn` 和 `burnBatch` 函数中移除过期检查，或为 `BURNER_ROLE` 添加一个跳过过期限制的独立 `burnExpired` 函数，允许授权方清理过期代币。

---

## 8. InvestmentManager can use AccountableFixedTerm::coverDefault to misuse token approvals from anyone

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
`AccountableFixedTerm::coverDefault` allows the `InvestmentManager` of a loan to call `IAccountableVault.lockAssets(assets, provider)`, which pulls tokens from the `provider` address and transfers them into the vault. There is no validation that the `provider` address has consented to acting as a provider for this specific default coverage. Any user who has ever approved the vault for token spending — including old approvals from unrelated operations — is at risk of having their tokens silently pulled without any permission for this specific action.

**Impact:**
The Investment Manager can drain token balances from any address that holds an outstanding approval to the vault, without any consent from the token holder. This is a significant centralization and trust risk that can result in unilateral loss of user funds.

**Recommended Mitigation:**
Add an explicit consent mechanism for `coverDefault` providers, such as requiring the provider to call an acknowledgment function before their tokens can be pulled, or restricting valid providers to a pre-approved set configured by the provider themselves.

---

**[中文版本]**

**描述：**
`AccountableFixedTerm::coverDefault` 允许贷款的 `InvestmentManager` 调用 `lockAssets(assets, provider)`，从 `provider` 地址拉取代币并转入金库，但未验证 `provider` 是否同意为本次违约提供覆盖。任何曾向金库授权过代币花费的地址（包括历史遗留的无关授权）均面临代币被静默取走的风险。

**影響：**
投资管理员可在未获代币持有人同意的情况下，从任何持有金库授权的地址耗尽代币余额，属于严重的中心化风险，可导致用户资金单方面损失。

**修復建議：**
为 `coverDefault` 提供者添加明确的同意机制，例如要求提供者在代币被拉取前调用确认函数，或将有效提供者限制在提供者自己预先配置的预批准集合内。

---

## 9. Missing Unstaked event for immediate unstake in UnstakeCooldown::transfer

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
When `UnstakeCooldown::transfer` triggers an immediate unstake (the handler's call to `proxy.request()` returns `unlockAt <= block.timestamp`), the function returns early after returning the proxy to the pool without emitting the `Unstaked` event. As a result, the on-chain event log has a gap for the flow where redemption happens immediately without any cooldown period.

**Impact:**
Off-chain systems relying on events for tracking withdrawals will silently miss these immediate unstake operations, leading to incorrect accounting in dashboards, indexers, and monitoring tools. There is no on-chain security impact; users still receive their funds correctly.

**Recommended Mitigation:**
Emit an `Unstaked` or dedicated `ImmediateUnstake` event in the immediate-return branch of `transfer()`, using the `amount` parameter, to ensure complete event coverage for all unstake flows.

---

**[中文版本]**

**描述：**
当 `UnstakeCooldown::transfer` 触发即时解质押时（`proxy.request()` 返回 `unlockAt <= block.timestamp`），函数在归还代理后提前返回，未发出 `Unstaked` 事件，导致链上事件日志对即时赎回流程存在缺口。

**影響：**
依赖事件追踪提款的链下系统会静默遗漏这些即时解质押操作，导致看板、索引器和监控工具的统计不准确；链上安全无影响，用户仍能正确收到资金。

**修復建議：**
在 `transfer()` 的即时返回分支中使用 `amount` 参数发出 `Unstaked` 或专用的 `ImmediateUnstake` 事件，确保所有解质押流程的事件完整性。

---

## 10. Missing validation allows userDeviation > burnRatioDeviation, silently disabling burn ratio protection

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
In `LibOracle::readBurn`, `readSpotAndTarget` snaps `oracleValue` to `targetPrice` when the spot price is within `userDeviation`. The burn ratio check then compares the already-snapped value against `burnRatioDeviation`. If `userDeviation > burnRatioDeviation`, any depeg between the two thresholds is invisibly absorbed by the snap, and the ratio check always passes because it compares `targetPrice` against itself. `LibSetters::setOracle` only validates the oracle configuration via `readMint`, which ignores `burnRatioDeviation`, so nothing prevents an operator from setting `userDeviation > burnRatioDeviation`.

**Impact:**
When triggered, the burn ratio penalty is silently disabled — `getBurnOracle` returns `minRatio = BASE_18` and all burns proceed at full value during a depeg that should have activated the penalty, exposing the protocol to under-collateralized redemptions.

**Recommended Mitigation:**
Add a validation check in `LibSetters::setOracle` that reverts if the decoded `userDeviation > burnRatioDeviation`, ensuring the ordering invariant is enforced at configuration time.

---

**[中文版本]**

**描述：**
`LibOracle::readBurn` 中，当现货价格在 `userDeviation` 范围内时，`readSpotAndTarget` 将价格归零至目标价。若 `userDeviation > burnRatioDeviation`，两个阈值之间的脱锚被无形吸收，比率检查始终通过，销毁比率惩罚被静默禁用。`LibSetters::setOracle` 仅通过 `readMint` 验证配置，无法防止此错误设置。

**影響：**
销毁比率惩罚被静默禁用，所有销毁在应触发惩罚的脱锚期间均以全额价值执行，导致协议面临抵押不足的赎回风险。

**修復建議：**
在 `LibSetters::setOracle` 中增加验证，若解码后的 `userDeviation > burnRatioDeviation` 则回滚，在配置阶段强制执行排序不变量。

---

## 11. Native token prizes cannot be funded due to missing receive() function

**Severity:** 🟡 Medium
**Source:** `cyfrin/spingame.md`

**Description:**
`SpinGame` supports multiple prize types including native tokens (represented as `prize.tokenAddress = address(0)`). The protocol team is responsible for maintaining a sufficient native token balance in the contract. However, the Spin contract has no `receive()` or `fallback()` function and none of its functions are `payable`, making it impossible to deposit native tokens via a standard transfer. The only way to fund the contract with native tokens would be an esoteric workaround such as using `selfdestruct`, which is not a viable operational mechanism.

**Impact:**
Native token prizes can never be funded or claimed; users who win native token prizes cannot receive them. The entire native token prize type is non-functional as shipped.

**Recommended Mitigation:**
Add a `receive() external payable {}` function to the contract to allow the protocol team to deposit native tokens and enable the native token prize flow to function as designed.

---

**[中文版本]**

**描述：**
`SpinGame` 支持原生代币奖品（`prize.tokenAddress = address(0)`），但合约既无 `receive()` 也无 `fallback()` 函数，且没有任何 `payable` 函数，无法通过标准转账向合约存入原生代币，导致原生代币奖品永远无法充值。

**影響：**
原生代币奖品无法充值和领取，中奖用户无法收到原生代币奖励，该奖品类型功能完全失效。

**修復建議：**
在合约中添加 `receive() external payable {}` 函数，允许协议团队存入原生代币，使原生代币奖品流程正常运作。

---

## 12. Native token transfers lack explicit balance check

**Severity:** 🟡 Medium
**Source:** `cyfrin/spingame.md`

**Description:**
In `Spin::_transferPrize`, native token prizes are sent via `_winner.call{value: prize.amount}("")` without a prior explicit balance check. For ERC20 and ERC721 prizes, the contract explicitly checks whether it holds sufficient balance or ownership before attempting the transfer. While a failed native transfer would still revert via the `NativeTokenTransferFailed` error, the absence of a pre-flight balance check creates inconsistency in the error path and makes debugging harder.

**Impact:**
Minor: the transaction would still revert on insufficient native balance, but the error message and code path are inconsistent with ERC20 and ERC721 handling, reducing code clarity and making error diagnosis harder for users and integrators.

**Recommended Mitigation:**
Add an explicit `address(this).balance >= prize.amount` check before the native transfer, consistent with the balance/ownership checks used for other prize types, providing a uniform and informative error path.

---

**[中文版本]**

**描述：**
`Spin::_transferPrize` 在发送原生代币奖品时未进行显式余额检查，而 ERC20 和 ERC721 奖品均有相应的余额/所有权前置检查，处理方式不一致，增加了调试难度。

**影響：**
轻微：原生余额不足时交易仍会回滚，但错误路径与其他奖品类型不一致，降低代码可读性和错误诊断效率。

**修復建議：**
在原生转账前增加 `address(this).balance >= prize.amount` 的显式检查，与其他奖品类型的余额检查保持一致，提供统一且信息丰富的错误路径。

---

## 13. Pocket::execWithValue does not emit native transfer event

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
`Pocket::execWithValue` sends native tokens via the `value` parameter but only emits `Executed(target, selector)`, not `NativeTransferred(to, amount)`. In contrast, `Pocket::transferNative` correctly emits `NativeTransferred(to, amount)`. Off-chain systems that track native token movements by listening for `NativeTransferred` events will silently miss all transfers made via `execWithValue`, since the `Executed` event does not include the value amount.

**Impact:**
Off-chain tracking systems, wallets, and indexers that rely on `NativeTransferred` events for accounting will have incomplete records of native token outflows, potentially leading to incorrect balance calculations and missed audit trails.

**Recommended Mitigation:**
Emit `NativeTransferred(target, value)` in `execWithValue` when `value > 0`, consistent with `transferNative`'s event emission, to ensure complete event coverage for all native transfer paths.

---

**[中文版本]**

**描述：**
`Pocket::execWithValue` 通过 `value` 参数发送原生代币，但只发出 `Executed(target, selector)` 事件，未发出 `NativeTransferred(to, amount)`，而 `Pocket::transferNative` 正确发出了后者。依赖 `NativeTransferred` 事件追踪原生代币流向的链下系统会静默遗漏通过 `execWithValue` 产生的所有转账。

**影響：**
依赖 `NativeTransferred` 事件进行账务统计的链下系统、钱包和索引器将得到不完整的原生代币流出记录，可能导致余额计算错误和审计轨迹缺失。

**修復建議：**
在 `execWithValue` 中当 `value > 0` 时发出 `NativeTransferred(target, value)` 事件，与 `transferNative` 的事件发出保持一致，确保所有原生转账路径的事件完整性。

---

## 14. Possibility of Burning Incorrect Token Because of Mutable Credential Contract Address

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**
The `DIDContract` stores the address of the `SoulboundCredential` contract in a mutable state variable that the contract owner can update at any time. The `revokeSBTCredential` function burns a credential token by calling `sbtContract.burnCredential(tokenId)` using the currently stored address. If the owner changes `sbtContract` after a credential was issued against the original contract, a subsequent revocation call could burn a token from the new contract rather than the one for which the credential was originally issued, potentially burning an incorrect or unrelated token.

**Impact:**
Token ID collisions between the old and new credential contracts could result in burning tokens from the wrong contract, causing unintended revocation of credentials that should remain valid or missing revocation of credentials that should be burned.

**Recommended Mitigation:**
Make the credential contract address immutable after deployment, or implement a migration mechanism that ensures all existing credentials are migrated or invalidated before the address can be changed, preventing cross-contract token ID confusion.

---

**[中文版本]**

**描述：**
`DIDContract` 将 `SoulboundCredential` 合约地址存储在可变状态变量中，合约所有者可随时更新。`revokeSBTCredential` 使用当前存储的地址调用 `sbtContract.burnCredential(tokenId)`。若所有者在凭证颁发后更换了 `sbtContract`，后续撤销操作可能从新合约销毁代币，而非原始合约，导致销毁错误的或无关的代币。

**影響：**
新旧凭证合约间的 token ID 碰撞可能导致从错误合约销毁代币，造成对应凭证的意外撤销或应被销毁的凭证未被撤销。

**修復建議：**
将凭证合约地址设为部署后不可变，或在允许地址变更前实施迁移机制，确保所有现有凭证被迁移或废止，防止跨合约 token ID 混淆。

---

## 15. Redundant balance check in safeTransferFrom before calling underlying transfer function

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
`RWASegWrap::safeTransferFrom` performs an explicit balance check (`balanceOf(from) < value → revert`) before calling `ISegregatedVault.internalTransferFrom`. The underlying vault's transfer function internally calls ERC20 `_transfer`, which itself calls `_update` and performs the same balance check with `ERC20InsufficientBalance`. The outer check is therefore fully redundant: it adds gas cost without providing any safety guarantee that the inner check does not already provide.

**Impact:**
Minor gas waste and code duplication; no security impact. The redundancy can mislead reviewers into thinking the outer check serves a distinct purpose.

**Recommended Mitigation:**
Remove the redundant balance check from `RWASegWrap::safeTransferFrom` and rely solely on the balance validation within the underlying ERC20 `_update` function.

---

**[中文版本]**

**描述：**
`RWASegWrap::safeTransferFrom` 在调用底层 `internalTransferFrom` 前进行了显式余额检查，但底层 ERC20 `_update` 函数本身已包含相同的 `ERC20InsufficientBalance` 检查，外层检查完全冗余，只增加 gas 消耗而无额外安全保障。

**影響：**
轻微的 gas 浪费和代码重复；无安全影响。冗余检查可能误导审计人员认为外层检查有独立目的。

**修復建議：**
从 `RWASegWrap::safeTransferFrom` 中移除冗余的余额检查，完全依赖底层 ERC20 `_update` 函数中的余额验证。

---

## 16. TokenBank::withdrawFunds resets memory not storage fee and sale amounts allowing multiple withdraws for the same token

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`TokenBank::withdrawFunds` copies `tokenData[tokenAddress]` into a `memory` variable `curData`, sets `curData.feeAmount = 0` or `curData.saleAmount = 0` on the memory copy, and then transfers tokens. Because the zero-reset is applied to the memory copy rather than to `storage`, `tokenData[tokenAddress].feeAmount` and `tokenData[tokenAddress].saleAmount` remain unchanged after the transfer. A caller can repeatedly invoke `withdrawFunds` to drain the same token amount multiple times, effectively stealing protocol fees and sale proceeds.

**Impact:**
A privileged caller with the `restricted` role can invoke `withdrawFunds` repeatedly to drain all fee and sale proceeds multiple times, resulting in significant financial loss to the protocol.

**Recommended Mitigation:**
Reset the fee or sale amount directly on the storage variable `tokenData[tokenAddress].feeAmount = 0` / `tokenData[tokenAddress].saleAmount = 0` before or immediately after the transfer, not on a local memory copy.

---

**[中文版本]**

**描述：**
`TokenBank::withdrawFunds` 将 `tokenData[tokenAddress]` 复制至 `memory` 变量 `curData`，在内存副本上将 `feeAmount` 或 `saleAmount` 置零后执行转账。由于置零操作作用于内存副本而非 storage，存储中的值保持不变，允许调用者反复调用 `withdrawFunds` 多次提取相同的代币金额。

**影響：**
持有 `restricted` 角色的特权调用者可反复调用 `withdrawFunds`，多次耗尽相同的手续费和销售收益，对协议造成重大财务损失。

**修復建議：**
在转账前或转账后直接对 storage 变量 `tokenData[tokenAddress].feeAmount = 0` / `tokenData[tokenAddress].saleAmount = 0` 进行置零，而非操作本地内存副本。

---

## 17. Unlimited token reallocation power creates centralization risk

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
`WorldLibertyFinancialV::ownerReallocateFrom` gives the contract owner unlimited power to burn tokens from any address and mint them to any other address, bypassing all security mechanisms including blacklisting, pausing, timelocks, and rate limiting. While the function may be intended for legal compliance scenarios, the absence of any safeguards means a compromised or malicious owner can instantly and silently move any token balance to any address without on-chain transparency, governance delay, or user recourse.

**Impact:**
A compromised or malicious owner can seize tokens from any holder, including blacklisted addresses, and redistribute them arbitrarily, undermining the decentralized nature of the token and creating an existential governance risk.

**Recommended Mitigation:**
Implement timelocks, multi-sig requirements, or governance-controlled execution for `ownerReallocateFrom`. Emit a dedicated `Reallocated` event with meaningful metadata. Consider whether the function is truly necessary or whether legal compliance can be achieved through less privileged mechanisms.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialV::ownerReallocateFrom` 赋予合约所有者无限制地从任意地址销毁代币并铸造至任意地址的权力，绕过所有安全机制（包括黑名单、暂停、时间锁和速率限制）。被攻击或恶意的所有者可立即、静默地转移任意持有人的代币余额。

**影響：**
被攻击或恶意的所有者可没收任意持有人（包括黑名单地址）的代币并任意重新分配，从根本上破坏代币的去中心化特性，形成存在性治理风险。

**修復建議：**
为 `ownerReallocateFrom` 实施时间锁、多签要求或治理控制执行；发出带有详细元数据的专用 `Reallocated` 事件；评估该函数的必要性，考虑通过权限更低的机制实现合规目标。

---

## 18. Unvalidated Market Address Leads To Arbitrary Token Approvals

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dirol.txt`

**Description:**
In the Crystal swap path, `market` is decoded from caller-supplied `pathData` and used as the spender in `_ensureAllowance(tokenIn, market, amountIn)` without any validation that `market` is a legitimate registered router or pair for the selected swap route. This allows callers to specify an arbitrary address as `market`, triggering unlimited ERC20 approvals to any address they choose under the guise of a valid swap operation.

**Impact:**
Attackers can obtain unlimited ERC20 approvals to attacker-controlled addresses by crafting malicious `pathData`, enabling future token drainage from the contract or from users who have approved the aggregator.

**Recommended Mitigation:**
Validate `market` against a registry of known legitimate Crystal routers/pairs before calling `_ensureAllowance`, rejecting any `pathData` that references an unregistered market address.

---

**[中文版本]**

**描述：**
Crystal 兑换路径中，`market` 从调用者提供的 `pathData` 中解码后直接用作 `_ensureAllowance(tokenIn, market, amountIn)` 的被授权方，未验证其是否为合法注册的路由器或交易对。攻击者可将任意地址指定为 `market`，以合法兑换操作为幌子，触发对任意地址的无限 ERC20 授权。

**影響：**
攻击者可通过构造恶意 `pathData` 获取对攻击者控制地址的无限 ERC20 授权，为后续耗尽合约或已授权用户的代币埋下后门。

**修復建議：**
在调用 `_ensureAllowance` 前，对照已知合法 Crystal 路由器/交易对的注册表验证 `market`，拒绝包含未注册市场地址的 `pathData`。

---

## 19. Unverified _receiver can cause irrecoverable token loss

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`BridgeCCIP::send` accepts a `_receiver` parameter intended to be the destination bridge contract on the receiving chain. The parameter is passed directly as the CCIP message receiver via `abi.encode(_receiver)` without any validation that it is a known legitimate bridge contract on the destination chain. If a user inadvertently passes an incorrect or zero address as `_receiver`, the CCIP message is sent to that address. On the destination chain, if `_receiver` is not a valid bridge contract, the message payload cannot be processed and the bridged tokens cannot be delivered, resulting in irrecoverable loss.

**Impact:**
Users who pass an incorrect `_receiver` address will have their tokens permanently lost, as CCIP messages delivered to non-bridge addresses cannot be replayed or recovered without protocol-level intervention.

**Recommended Mitigation:**
Maintain an on-chain registry of authorized bridge receiver addresses keyed by destination chain ID, and validate that `_receiver` matches the registered address for `_dstChain` before constructing the CCIP message.

---

**[中文版本]**

**描述：**
`BridgeCCIP::send` 接受 `_receiver` 参数作为目标链桥接合约地址，但该参数直接被编码为 CCIP 消息接收方，未验证其是否为目标链上的合法桥接合约。若用户传入错误或零地址，CCIP 消息会被发送至该地址，目标链上若 `_receiver` 不是有效桥接合约，消息无法被处理，桥接代币无法送达，导致不可恢复的损失。

**影響：**
传入错误 `_receiver` 的用户将永久损失代币，发送至非桥接地址的 CCIP 消息无法被重播或恢复，需要协议层面的人工干预。

**修復建議：**
在链上维护以目标链 ID 为键的授权桥接接收地址注册表，在构建 CCIP 消息前验证 `_receiver` 与 `_dstChain` 对应的注册地址一致。

---

## 20. proofInterval Validated as Token Count but Used as Seconds

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
The `proofInterval` parameter has conflicting interpretations in the contract. During session creation, `_validateProofRequirements` validates it as a token count with a minimum of `MIN_PROVEN_TOKENS` (100 tokens). However, in `triggerSessionTimeout()`, `proofInterval` is used as a time duration in seconds to determine when a session can be timed out. This means the timeout window is directly tied to the token count rather than an intended time period, producing unpredictable and incorrect timeout behavior depending on the token denomination used.

**Impact:**
Session timeout windows are calculated using a token count as if it were a duration in seconds, resulting in sessions that time out far too quickly (for large-denomination tokens) or too slowly (for small-denomination tokens), breaking the expected session lifecycle behavior.

**Recommended Mitigation:**
Separate `proofInterval` into two distinct parameters: one for token count validation and one for time duration, each with appropriate validation. Alternatively, clarify and enforce a single consistent interpretation across all usages in the contract.

---

**[中文版本]**

**描述：**
`proofInterval` 参数存在两种相互冲突的语义：在会话创建的 `_validateProofRequirements` 中被作为代币数量（最小值 `MIN_PROVEN_TOKENS = 100`）验证；但在 `triggerSessionTimeout()` 中被作为秒数时长来确定会话何时可超时。这导致超时窗口直接绑定于代币数量而非预期时长，产生不可预测的错误超时行为。

**影響：**
会话超时窗口使用代币数量（而非秒数）计算，导致大面值代币对应的会话超时过快、小面值代币超时过慢，破坏预期的会话生命周期行为。

**修復建議：**
将 `proofInterval` 拆分为两个独立参数，分别用于代币数量验证和时间时长，各自进行适当验证；或明确并统一合约中所有用法的单一语义解释。
