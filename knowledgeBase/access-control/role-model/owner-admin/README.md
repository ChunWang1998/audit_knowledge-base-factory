# owner-admin (20)

> Issues where owner, admin, or privileged role boundaries were misconfigured, conflated, or failed to enforce intended restrictions.

**（中文）** 与所有者、管理员或特权角色边界配置错误、混用或未能落实预期限制相关的问题。

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

严重级别说明：🔴 严重  🟠 高  🟡 中

---

## 1. In `DelegatorFactory` new entity can be created for a blacklisted implementation

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
`DelegatorFactory::create` does not check whether the specified implementation type has been blacklisted before deploying a new entity. When an implementation is blacklisted — typically because it was found unsafe, deprecated, or otherwise restricted — the governance intent is to prevent further deployment using that version. The missing check means the factory silently bypasses this restriction: it will deploy a new entity using a blacklisted implementation type without reverting.

**Impact:**
If an implementation is blacklisted due to a security vulnerability, vault owners can still expose themselves to those vulnerabilities by creating new entities or migrating to the blacklisted version. The intended security barrier provided by blacklisting is fully defeated.

**Recommended Mitigation:**
Add an explicit blacklist check inside `DelegatorFactory::create` that reverts if the requested implementation type is currently blacklisted before proceeding with deployment.

---

**[中文版本]**

**描述：**
`DelegatorFactory::create` 在部署新实体前未检查所选实现类型是否已被列入黑名单。实现被拉黑通常表示不安全、已废弃或治理禁止再使用该版本；缺少检查则工厂可静默绕过限制，仍用被禁用的实现类型部署。

**影响：**
若因漏洞拉黑某实现，金库所有者仍可能创建新实体或迁移到该版本，黑名单本应提供的安全隔离完全失效。

**修复建议：**
在 `DelegatorFactory::create` 内显式校验：若请求的实现类型当前处于黑名单则回滚，然后再继续部署。

---

## 2. Incorrect `owner` passed to `Manager::redeem` in YToken withdrawal flow

**Severity:** 🟠 High
**Source:** `cyfrin/yieldfi.md`

**Description:**
YieldFi's yield tokens implement a deferred withdrawal mechanism via a central `Manager` contract. In `YToken::_withdraw` (and identically in `YTokenL2::_withdraw`), `msg.sender` is incorrectly passed as the `owner` parameter to `manager.redeem`, even though the correct `owner` is already available in the function signature. This works when the caller and owner are the same address, but breaks in delegated withdrawal scenarios where a third party holds an allowance and initiates the withdrawal on behalf of the token owner.

**Impact:**
When a third party (`caller != owner`) initiates a withdrawal on behalf of another user, the call to `manager.redeem` receives `msg.sender` (the caller) as the owner instead of the actual share owner. This causes the call to revert, blocking the withdrawal. In a worst-case scenario, if the caller also holds shares, the wrong user's tokens may be burned instead of the intended owner's.

**Recommended Mitigation:**
Replace the `msg.sender` argument passed to `manager.redeem` with the `owner` parameter that is already available in the `_withdraw` function signature.

---

**[中文版本]**

**描述：**
YieldFi 收益代币通过中央 `Manager` 合约实现延期赎回。`YToken::_withdraw`（与 `YTokenL2::_withdraw` 相同）错误地将 `msg.sender` 作为 `manager.redeem` 的 `owner` 参数，而函数签名中已有正确的 `owner`。当调用者与所有者同一地址时尚可工作，但在第三方代领（持有 allowance）场景下会出错。

**影响：**
第三方代用户发起赎回时，`manager.redeem` 将调用者当作份额所有者，导致回滚无法赎回；极端情况下若调用者也持有份额，可能错误销毁非目标用户的份额。

**修复建议：**
将传给 `manager.redeem` 的参数由 `msg.sender` 改为 `_withdraw` 中已有的 `owner`。

---

## 3. Users Can Renounce BLACKLISTED_ROLE and Bypass Administrative Restrictions

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
`OverlayerWrap` implements a `BLACKLISTED_ROLE` mechanism via OpenZeppelin's `AccessControl` to restrict sanctioned or non-compliant accounts from transferring, minting, or redeeming tokens. The `SingleAdminAccessControl` parent contract overrides `renounceRole()` to prevent renouncing `DEFAULT_ADMIN_ROLE`, but provides no similar restriction on `BLACKLISTED_ROLE`. Any blacklisted account can call `renounceRole(BLACKLISTED_ROLE, self)` to independently remove its own restriction. The blacklist is expected to be an administrative control used to restrict malicious, sanctioned, or non-compliant accounts, but this mechanism is entirely ineffective against accounts that know to exploit this path.

**Impact:**
Blacklisted users can independently remove their blacklist status and regain full transfer, mint, and redeem functionality, completely defeating the compliance controls.

**Recommended Mitigation:**
Override `renounceRole()` in `OverlayerWrap` to also block renouncement of `BLACKLISTED_ROLE`, similar to how the parent contract blocks `DEFAULT_ADMIN_ROLE` renouncement.

---

**[中文版本]**

**描述：**
`OverlayerWrap` 通过 OpenZeppelin `AccessControl` 实现 `BLACKLISTED_ROLE`，用于限制受制裁或不合规账户的转账、铸造与赎回。父合约 `SingleAdminAccessControl` 重写了 `renounceRole()` 以禁止放弃 `DEFAULT_ADMIN_ROLE`，但未对 `BLACKLISTED_ROLE` 做同类限制。任何被列入黑名单的账户都可调用 `renounceRole(BLACKLISTED_ROLE, self)` 自行解除限制。

**影响：**
被列入黑名单的用户可单方面恢复转账、铸造与赎回能力，合规控制完全失效。

**修复建议：**
在 `OverlayerWrap` 中重写 `renounceRole()`，同样禁止放弃 `BLACKLISTED_ROLE`，与父合约对 `DEFAULT_ADMIN_ROLE` 的处理一致。

---

## 4. Admin Can Arbitrarily Decrease User's Vesting Amount

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/A Two Tech Limited.txt`

**Description:**
`ATWOVesting::setSchedule()` allows the admin to update a user's linear vesting schedule at any time, including the `total` vesting amount. While the function does prevent reducing `total` below already-claimed amounts, it does not prevent reducing it below the currently accrued (vested-but-unclaimed) amount. Because claimable tokens are computed as `vestedToDate - claimed`, reducing `total` retroactively reduces the amount the user can claim — even for time that has already elapsed in the vesting schedule. The absence of proper validation enables the admin to unilaterally reduce vested amounts, leading to inconsistency between the vesting state and the actual accrued balance.

**Impact:**
Admin can revoke a user's legitimate vested entitlement, resulting in loss of tokens that the user should already be able to claim. This creates significant trust risk and the potential for abuse of administrative privileges.

**Recommended Mitigation:**
Add a check ensuring the new `total` is at least equal to the already-accrued amount at the time of update (tokens vested to-date minus claimed), preventing retroactive reduction of entitled amounts.

---

**[中文版本]**

**描述：**
`ATWOVesting::setSchedule()` 允许管理员随时更新用户线性归属计划，包括 `total` 归属总量。函数虽防止将 `total` 降到已领取量以下，但未防止降到「已归属未领取」量以下。可领取量为 `vestedToDate - claimed`，降低 `total` 会追溯减少用户可领取额，包括已随时间归属的部分。

**影响：**
管理员可单方面削减用户已应得归属，导致用户本应能领取的代币损失，存在信任风险与权限滥用空间。

**修复建议：**
增加校验：新的 `total` 至少不低于更新时刻已归属未领取的量（已归属至今减去已领取），禁止追溯削减应得份额。

---

## 5. Blacklist Enforcement Bypassed When Recipient Is Transaction-Limit Exempt

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
`KnoxNet._enforceTxLimit` combines two logically separate concerns — transaction size limits and blacklist enforcement — under a single exemption guard. The function opens with an early return if either the sender or recipient is `isTxLimitExempt`. The blacklist check (`require(blacklist[sender] == 0)`) is placed after this early return. Several addresses are marked as tx-limit exempt during construction, including the contract itself, the owner, and the router address. If the recipient holds `isTxLimitExempt` status, the function returns before the blacklist check is ever evaluated, allowing a blacklisted sender to transfer freely to those exempt addresses.

**Impact:**
Blacklist enforcement is circumvented whenever the recipient has tx-limit exemption, allowing blacklisted accounts to transfer tokens to privileged addresses (owner, router, contract) without restriction, completely defeating the blacklist mechanism for those transfer paths.

**Recommended Mitigation:**
Separate the blacklist check from the tx-limit exemption guard so that blacklist status is always evaluated regardless of whether either party is tx-limit exempt.

---

**[中文版本]**

**描述：**
`KnoxNet._enforceTxLimit` 将交易规模限制与黑名单 enforcement 混在同一豁免判断下。若发送方或接收方任一为 `isTxLimitExempt` 则提前返回；黑名单检查（`require(blacklist[sender] == 0)`）位于该提前返回之后。构造时合约自身、所有者、路由器等被标为限额豁免；若接收方为豁免地址，函数在检查黑名单前即返回，被列入黑名单的发送方仍可向这些地址自由转账。

**影响：**
只要接收方具有交易限额豁免，黑名单即被绕过，被列入黑名单的账户仍可向所有者、路由器、合约等特权地址转账，黑名单在这些路径上失效。

**修复建议：**
将黑名单检查与交易限额豁免解耦，无论任一方是否限额豁免，都应先（或始终）评估黑名单状态。

---

## 6. Combination of Ownable and AccessControl Can Cause Loss of Admin Functionality

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeTailor` and `BasisTradeVault` inherit both `Ownable(2Step)Upgradeable` and `AccessControlUpgradeable`. Several admin wrapper functions are guarded by `onlyOwner` but internally call `grantRole`/`revokeRole`, which themselves require the caller to hold `DEFAULT_ADMIN_ROLE`. This creates a dual requirement: the caller must simultaneously be both the `owner` and a `DEFAULT_ADMIN_ROLE` holder. When ownership is transferred via `transferOwnership` without also transferring `DEFAULT_ADMIN_ROLE`, the new owner cannot call `grantAdmin`, `revokeAdmin`, or similar role management functions. Conversely, a `DEFAULT_ADMIN_ROLE` holder who is not the owner cannot authorize upgrades since `_authorizeUpgrade` is `onlyOwner`. The extra wrappers also duplicate functionality and enlarge the attack surface.

**Impact:**
A realistically common ownership transfer that forgets to synchronize roles causes a partial loss of admin functionality with no on-chain remedy. The new owner may be completely unable to manage roles, and the existing `DEFAULT_ADMIN_ROLE` holder cannot upgrade the contract.

**Recommended Mitigation:**
Unify on `AccessControl` by removing `Ownable` entirely. Gate all privileged functions including `_authorizeUpgrade` with `onlyRole(DEFAULT_ADMIN_ROLE)`. If keeping `Ownable`, add logic to automatically synchronize `DEFAULT_ADMIN_ROLE` on every ownership transfer.

---

**[中文版本]**

**描述：**
`BasisTradeTailor` 与 `BasisTradeVault` 同时继承 `Ownable(2Step)Upgradeable` 与 `AccessControlUpgradeable`。若干管理员封装函数使用 `onlyOwner`，内部却调用需要 `DEFAULT_ADMIN_ROLE` 的 `grantRole`/`revokeRole`，形成双重条件：调用者须同时是所有者与默认管理员。仅转移所有权而未同步 `DEFAULT_ADMIN_ROLE` 时，新所有者无法调用 `grantAdmin` 等；仅有默认管理员而非所有者则无法授权升级（`_authorizeUpgrade` 为 `onlyOwner`）。

**影响：**
常见的「只转所有权未同步角色」会导致部分管理功能永久不可用；新所有者可能完全无法管理角色，而持有默认管理员者无法升级合约。

**修复建议：**
统一采用 `AccessControl`，移除 `Ownable`，所有特权（含 `_authorizeUpgrade`）用 `onlyRole(DEFAULT_ADMIN_ROLE)`。若保留 `Ownable`，在每次所有权转移时自动同步 `DEFAULT_ADMIN_ROLE`。

---

## 7. `DEFAULT_ADMIN_ROLE` Can Be Mistakenly Granted When Granting `fallback` Permission on Any Contract

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
`AccessControlManager::grantCall` computes a role as `roleFor(contractAddress, selector)` using bitwise operations: the contract address occupies the upper bits and the function selector occupies the lower bits. There is an edge case when granting permission to call the `fallback()` function (selector `bytes4(0)`) on any contract (address `address(0)`). The combination of these two zero inputs results in a computed role of `bytes32(0)`, which is precisely the value assigned to `DEFAULT_ADMIN_ROLE`. The function proceeds to grant this computed role to the recipient, inadvertently granting full admin rights.

**Impact:**
An account given permission to call fallback on any contract inadvertently receives `DEFAULT_ADMIN_ROLE`, which it can then use to grant arbitrary permissions to other accounts and take complete control of the access control system.

**Recommended Mitigation:**
Add a validation in `grantCall` that reverts if the computed role equals `DEFAULT_ADMIN_ROLE`. Alternatively, revert when `contractAddress == address(0)` or `selector == bytes4(0)` to block this specific edge case entirely.

---

**[中文版本]**

**描述：**
`AccessControlManager::grantCall` 用位运算将合约地址与函数选择器组合为角色 `roleFor(contract, selector)`。当对任意合约（`address(0)`）授权调用 `fallback()`（选择器为 `bytes4(0)`）时，两路零输入组合为 `bytes32(0)`，恰好等于 `DEFAULT_ADMIN_ROLE`，函数随后将该「角色」授予接收者，等同于误授完整管理员权限。

**影响：**
被授权「对任意合约调用 fallback」的账户会意外获得 `DEFAULT_ADMIN_ROLE`，可进一步为任意账户授予权限并完全控制访问控制系统。

**修复建议：**
在 `grantCall` 中若计算出的角色等于 `DEFAULT_ADMIN_ROLE` 则回滚；或直接禁止 `contractAddress == address(0)` 或 `selector == bytes4(0)` 的组合。

---

## 8. Default Admin Can Assign Blacklisted Role Without Enforcing Blacklist Activation Constraints

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
`OverlayerWrap` implements a `blacklistActivationTime` variable controlling when blacklisting becomes active. The `disableAccount()` function correctly enforces this timing restriction via the `blacklistAllowed` modifier, which reverts if the activation time has not yet been reached. However, since the contract inherits OpenZeppelin's `AccessControl`, which exposes a public `grantRole()` function, the `DEFAULT_ADMIN_ROLE` holder can bypass the activation timing entirely by calling `grantRole(BLACKLISTED_ROLE, account)` directly. This direct call does not pass through the `blacklistAllowed` modifier and therefore does not apply the intended activation-time restriction.

**Impact:**
The `DEFAULT_ADMIN_ROLE` can blacklist accounts before the intended activation time, violating the protocol's commitment to users about when blacklisting is active, and creating inconsistent state between what users expect and what the contract enforces.

**Recommended Mitigation:**
Override `grantRole` in `OverlayerWrap` to enforce the `blacklistAllowed` timing check specifically for `BLACKLISTED_ROLE` assignments, preventing the bypass via direct role granting.

---

**[中文版本]**

**描述：**
`OverlayerWrap` 用 `blacklistActivationTime` 控制黑名单何时生效；`disableAccount()` 通过 `blacklistAllowed` 修饰符在未到时间时回滚。但继承的 OpenZeppelin `AccessControl` 暴露公开 `grantRole()`，`DEFAULT_ADMIN_ROLE` 持有者可绕过修饰符直接 `grantRole(BLACKLISTED_ROLE, account)`，不经过激活时间限制。

**影响：**
默认管理员可在承诺的激活时间之前将账户列入黑名单，违背对用户关于黑名单何时生效的约定，链上状态与用户预期不一致。

**修复建议：**
在 `OverlayerWrap` 中重写 `grantRole`，对 `BLACKLISTED_ROLE` 的授予同样执行 `blacklistAllowed` 时间校验，禁止通过直接授权绕过。

---

## 9. Guardian Can Override Owner's Emergency Pause

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The WLFI contract grants both the owner and guardians symmetric pause and unpause capabilities. The `guardianUnpause()` function allows any guardian to unpause the contract, even when the owner has deliberately paused it in response to a security incident or operational concern. The code itself contains a developer comment flagging this as a potential design concern. Common security practice dictates that pausing (a defensive action with low risk) should be permitted among multiple authorized parties, but unpausing (a higher-risk operation that restores service) should require the highest authority level only.

**Impact:**
A guardian can override the owner's emergency security response by unpausing the contract, potentially restoring service while an attack or vulnerability is still active, undermining the authority hierarchy and the effectiveness of the emergency response mechanism.

**Recommended Mitigation:**
Remove the unpause capability from guardians, restricting the ability to unpause to the owner only.

---

**[中文版本]**

**描述：**
WLFI 合约赋予所有者与守护者对称的暂停/恢复能力。`guardianUnpause()` 允许任意守护者在所有者因安全事件主动暂停后仍恢复合约；注释中亦指出这是设计疑虑。通常暂停（防御、低风险）可多方执行，而恢复服务（高风险）应仅最高权限方可执行。

**影响：**
守护者可覆盖所有者的紧急安全响应，在攻击或漏洞仍存在时恢复服务，削弱层级权威与应急响应有效性。

**修复建议：**
取消守护者的 unpause 权限，仅允许所有者恢复运行。

---

## 10. Misleading `owner` Field in `OnMetaWithdraw` Event

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The `OnMetaWithdraw` event emits `receiver` as its first argument, but the parameter is named `owner` in the event definition. In ERC-4626, `owner` (the share holder), `caller` (the initiator of the withdrawal), and `receiver` (the recipient of the withdrawn assets) are three semantically distinct addresses that can all differ in a delegated withdrawal scenario. Naming the `receiver` as `owner` in the event creates a semantic mismatch that will mislead off-chain indexers, analytics dashboards, and monitoring tools that parse event data by parameter name.

**Impact:**
Off-chain systems incorrectly attribute withdrawal ownership, leading to incorrect accounting in analytics, wrong attribution in user-facing dashboards, and potentially flawed risk monitoring that relies on the `owner` field to track fund movements.

**Recommended Mitigation:**
Rename the event parameter from `owner` to `receiver`, or restructure the event to include both `owner` and `receiver` as distinct fields to accurately represent all parties involved in a delegated withdrawal.

---

**[中文版本]**

**描述：**
`OnMetaWithdraw` 事件第一个参数实际为 `receiver`，但事件定义中参数名为 `owner`。在 ERC-4626 中，`owner`（份额持有人）、`caller`（发起赎回者）与 `receiver`（资产接收方）在代领场景下可各不相同。将接收方命名为 `owner` 会使链下索引、分析与监控按名称解析时产生语义错误。

**影响：**
链下系统错误归因赎回归属，分析面板与风控监控可能误判资金流向。

**修复建议：**
将参数由 `owner` 更名为 `receiver`，或同时包含 `owner` 与 `receiver` 两个独立字段以准确表达代领各方。

---

## 11. Owner Authorization Allows Arbitrary Burning of Soulbound Tokens

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**
`SoulboundCredential::burnCredential()` grants the contract owner the ability to burn any token belonging to any address, in addition to the token holder and the issuer. Soulbound tokens are designed to be permanently bound to the original recipient and non-transferable, guaranteeing credential permanence. The owner's unrestricted burn capability fundamentally undermines this guarantee. In the event of owner key compromise, any credential in the system can be destroyed without the holder's knowledge or consent.

**Impact:**
Any credential held by any user can be unilaterally destroyed by the owner or an attacker who compromises the owner key, undermining the permanence guarantee of soulbound tokens and the integrity of the entire DID credential system.

**Recommended Mitigation:**
Remove the owner's ability to burn tokens that were not issued by or do not belong to them. If administrative burn capability is required, add multi-sig requirements, governance approval thresholds, or time delays to prevent unilateral destruction.

---

**[中文版本]**

**描述：**
`SoulboundCredential::burnCredential()` 除持有人与发行方外，还允许合约所有者销毁任意地址的代币。灵魂绑定代币设计上应永久绑定、不可转让，以保证凭证持久性；所有者无限制销毁权从根本上破坏该保证。所有者密钥泄露时，系统内任意凭证可在持有人不知情的情况下被销毁。

**影响：**
所有者或窃取密钥者可单方面销毁任意用户的凭证，破坏灵魂绑定承诺与整个 DID 凭证体系的完整性。

**修复建议：**
移除所有者销毁非本人发行或非本人持有代币的能力；若需行政销毁，应引入多签、治理阈值或时间锁。

---

## 12. Owner Rights Can Be Renounced While Contract Is Paused

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The NTE contract implements pausable token transfers and allows the owner to call `renounceOwnership()` after 30 days from deployment. The `renounceOwnership` function validates only the time constraint but does not check whether the contract is currently paused. If the owner renounces ownership while the contract is paused, ownership is permanently transferred to the zero address. Since only the owner can unpause the contract, and the owner address is now `address(0)` which cannot sign transactions, no entity retains the ability to resume transfers. The result is a permanently paralyzed protocol.

**Impact:**
All token transfers become permanently frozen with no recovery path, effectively rendering the protocol permanently unusable and permanently locking all user funds in a state with no administrative remedy.

**Recommended Mitigation:**
Add a check in `renounceOwnership()` that reverts if the contract is currently paused, preventing ownership renouncement from being used to create an unrecoverable frozen state.

---

**[中文版本]**

**描述：**
NTE 合约实现可暂停的转账，并允许所有者在部署 30 天后调用 `renounceOwnership()`。该函数仅校验时间，未校验合约是否处于暂停。若在暂停期间放弃所有权，所有者变为零地址；仅所有者可 unpause，而 `address(0)` 无法签名，无人再能恢复转账。

**影响：**
所有转账永久冻结且无恢复路径，用户资金锁死，协议实质报废。

**修复建议：**
在 `renounceOwnership()` 中若合约当前为暂停状态则回滚，避免通过放弃所有权制造不可恢复的冻结状态。

---

## 13. Owner Can Chain Admin Calls for Same-Block Drains

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
Multiple owner-privileged admin functions in `SherpaVault` and `SherpaUSD` have no built-in time delays, allowing the owner to atomically chain multiple privileged calls within the same block. Three distinct drain paths exist: (1) Vault drain — call `setStableWrapper` to change the token that is protected from rescue, then immediately call `rescueTokens` to extract the old wrapper balance from the vault; (2) Wrapper operator drain — call `setOperator`, then use `SherpaUSD::transferAsset` to move USDC out of the wrapper; (3) Wrapper keeper drain — call `setKeeper`, then use `depositToVault` to pull USDC from users with existing approvals and extract value via `transferAsset`. Despite code comments stressing limited owner power, the actual on-chain authority is far-reaching and exercisable atomically.

**Impact:**
Owner or a compromised owner key can immediately redirect custody and drain user funds with no warning or reaction time for users, creating a significant gap between the stated design intent and the actual on-chain risk profile.

**Recommended Mitigation:**
Add minimum time delays (at least one withdrawal epoch) to sensitive admin functions such as `setStableWrapper`, `rescueTokens`, `setOperator`, and `setKeeper`. Make `stableWrapper` and `keeper` immutable after initial deployment to eliminate the vault drain and keeper drain paths entirely.

---

**[中文版本]**

**描述：**
`SherpaVault` 与 `SherpaUSD` 中多项所有者特权函数无内置延迟，可在同一区块内原子串联。(1) 金库排空：先 `setStableWrapper` 再 `rescueTokens` 转走旧包装代币；(2) 包装 operator：先 `setOperator` 再 `transferAsset` 转出 USDC；(3) keeper：先 `setKeeper` 再利用 `depositToVault` 与用户授权抽走资金。注释强调所有者权力有限，但链上权限实际很大且可瞬时执行。

**影响：**
所有者或泄露的密钥可无预警立即改变托管并抽走用户资金，设计意图与实际风险严重不符。

**修复建议：**
对 `setStableWrapper`、`rescueTokens`、`setOperator`、`setKeeper` 等敏感操作设置最短延迟（至少一个提现周期）；部署后将 `stableWrapper` 与 `keeper` 设为不可变以消除部分排空路径。

---

## 14. Owner Can Front-Run Depositors by Setting Yield Value to Dust

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Prodigy Finance.txt`

**Description:**
The owner can monitor the mempool for pending deposit transactions and front-run them by calling `adjustYieldValue` to reduce the yield value to a dust amount just before the deposit transaction executes. The depositor's transaction then executes with near-zero yield, and no trading fee is applied to the owner for the same deposit. The owner can then back-run the deposit transaction to restore the original yield value. The contracts are planned for mainnet deployment where MEV-style attacks of this nature are straightforwardly executable. Victims must wait for the vault to close via `VaultCore::execute` to recover their funds, with no yield received.

**Impact:**
Depositors have their funds effectively frozen until vault closure while receiving no yield — they deposited in expectation of yield but receive none due to the owner's front-running manipulation. Users lose confidence in the protocol and cannot exit until the vault closes.

**Recommended Mitigation:**
Add a `minYieldValue` parameter to the deposit function allowing depositors to specify the minimum acceptable yield, causing the transaction to revert if the current yield value falls below their threshold. Alternatively, implement a timelock on `adjustYieldValue` so changes only take effect after a minimum delay.

---

**[中文版本]**

**描述：**
所有者可监控内存池中待确认的存款交易，在存款执行前抢先调用 `adjustYieldValue` 将收益率降至极小值；存款成交时几乎无收益且所有者不对该笔存款收取交易费；随后再抢后恢复收益率。主网上此类 MEV 攻击易实施；受害者须等 `VaultCore::execute` 关闭金库才能取回资金且无收益。

**影响：**
存款人资金在关闭前实质被冻结且得不到预期收益，因所有者抢跑操纵收益率；用户信心受损且无法提前退出。

**修复建议：**
在存款函数中增加 `minYieldValue`，若当前收益率低于用户阈值则回滚；或对 `adjustYieldValue` 设置时间锁，使变更在延迟后生效。

---

## 15. Owner Cannot Burn Tokens From Blacklisted Addresses

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`HilBTC::burnFrom()` contains a special case allowing the owner to burn tokens from any address without requiring an allowance, bypassing `_spendAllowance`. However, the internal `_burn()` calls `_update()`, which applies the `notBlacklisted(from)` modifier. This modifier blocks any update operation involving a blacklisted `from` address, including owner-initiated burns. The result is a functional inconsistency: the owner has a special `burnFrom` privilege that is silently negated for the specific addresses where it is most likely to be operationally needed — blacklisted addresses requiring administrative remediation.

**Impact:**
Owner cannot exercise intended administrative control to burn tokens from blacklisted addresses, defeating a key purpose of the owner's elevated burn privilege. Administrative remediation of blacklisted accounts becomes impossible.

**Recommended Mitigation:**
Create a separate, explicitly privileged function for owner burns of blacklisted addresses that bypasses the `notBlacklisted` modifier, making the intended capability explicit and safe. Alternatively, restructure `_update` to allow an owner-override path for burn operations.

---

**[中文版本]**

**描述：**
`HilBTC::burnFrom()` 允许所有者不经 allowance 从任意地址销毁代币，绕过 `_spendAllowance`。但内部 `_burn()` 调用 `_update()`，其受 `notBlacklisted(from)` 限制，阻止涉及被列入黑名单的 `from` 的更新，包括所有者发起的销毁。结果：最需要行政销毁黑名单地址代币时，所有者的特殊 `burnFrom` 权限反而被静默抵消。

**影响：**
所有者无法按预期对黑名单地址执行销毁，行政补救无法实现。

**修复建议：**
新增显式特权函数，供所有者对黑名单地址销毁并绕过 `notBlacklisted`；或重构 `_update`，为销毁提供所有者覆盖路径。

---

## 16. Owner Can Rescue the Vault's Own Share Tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault::rescueTokens` correctly blocks rescuing the `stableWrapper` token to protect user deposits, but does not block the vault's own share token. When deposits are processed, the vault mints new shares to itself (`address(this)`) as custody for pending deposits and redemptions — `accountingSupply` is incremented and shares are minted to `address(this)`. User redemptions are later fulfilled from this custodied share balance. The owner can call `rescueTokens` on the vault's own share token address to transfer these custodied shares out of the vault, after which they can be redeemed for the underlying assets.

**Impact:**
Owner or a compromised owner key can extract vault-custodied shares that back users' pending deposits and redemption balances, effectively stealing those funds from users who are awaiting settlement.

**Recommended Mitigation:**
Extend the rescue token restriction to also prohibit rescuing the vault's own share token by adding `address(this)` to the rescue blacklist alongside `stableWrapper`.

---

**[中文版本]**

**描述：**
`SherpaVault::rescueTokens` 正确禁止救援 `stableWrapper` 以保护存款，但未禁止救援金库自身的份额代币。处理存款时金库向自身（`address(this)`）铸造份额作为待处理存取与赎回的托管，`accountingSupply` 增加。用户赎回最终从该托管份额中兑付。所有者可对金库份额代币调用 `rescueTokens` 转走托管份额，再赎回底层资产。

**影响：**
所有者或泄露密钥者可抽走用于待结算的托管份额，窃取等待结算的用户资金。

**修复建议：**
将金库自身份额代币地址与 `stableWrapper` 一并列入禁止救援名单（例如禁止对 `address(this)` 作为份额合约的救援）。

---

## 17. `StandardToken::transferWithPermit` Can Be DoS Attacked by Front-Running `permit`

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`StandardToken::transferWithPermit` atomically executes two sequential calls: first `ERC20PermitMixin::permit` (to grant spending approval), then `StandardToken::transferFrom` (to execute the token transfer). Since the permit signature and all its parameters are fully visible in the mempool before the original transaction is mined, any observer can extract the signature and front-run the original transaction by calling `permit` directly. This front-run consumes the user's nonce, causing the original `transferWithPermit` transaction to revert when it attempts to use the now-invalidated signature, making it impossible to atomically grant the approval and execute the transfer.

**Impact:**
The atomic approve-and-transfer pattern is permanently broken by the front-running attack. The intended UX flow for users relying on `transferWithPermit` is completely disrupted, and the transaction cannot be completed through this path after the nonce is consumed.

**Recommended Mitigation:**
Wrap the `permit` call in a try/catch: if it reverts (because the nonce has already been consumed by a front-runner), proceed to check whether the existing allowance is sufficient and continue with `transferFrom` if so, rather than reverting the entire operation.

---

**[中文版本]**

**描述：**
`StandardToken::transferWithPermit` 顺序执行 `permit` 再 `transferFrom`。Permit 签名与参数在内存池中对观察者可见，可先抢跑直接调用 `permit` 消耗用户 nonce，导致原交易的 `transferWithPermit` 在使用已失效签名时回滚，无法原子完成授权加转账。

**影响：**
抢跑使「授权并转账」原子流程被破坏，依赖该路径的用户体验完全失效，nonce 被消耗后该路径无法完成交易。

**修复建议：**
将 `permit` 包在 try/catch 中：若因 nonce 已被占用而回滚，则检查现有 allowance 是否足够并继续 `transferFrom`，避免整笔交易失败。

---

## 18. `TrustService::removeRole` Doesn't Delete Already Owned Entities

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
When `TrustService::removeRole` strips an address of its role (setting it to `NONE`), it does not clean up the entity ownership mappings. The address remains recorded as the owner of any entities it created while holding the role, and all related operators and resources remain linked to those entities. The `onlyEntityOwnerOrAbove` modifier checks entity ownership mappings rather than role status directly, so the role-stripped address still passes the modifier check and can continue calling entity management functions such as `addOperator` and `addResource` for entities it previously owned.

**Impact:**
An address that has been stripped of its role retains unauthorized control over all entities it previously owned, maintaining the ability to add and remove operators and resources from those entities despite having no valid role in the system.

**Recommended Mitigation:**
When removing a role, explicitly clear all entity ownership mappings associated with the address — including `ownersEntities`, `entityByOperator`, and `entityByResource` — to ensure the address fully loses all entity management access upon role removal.

---

**[中文版本]**

**描述：**
`TrustService::removeRole` 将地址角色设为 `NONE` 时，未清理实体所有权映射。该地址在持角色期间创建的实体仍记录为其所有，相关 operator 与资源仍关联。`onlyEntityOwnerOrAbove` 检查的是实体所有权映射而非当前角色，故被撤角色后仍可通过修饰符并调用 `addOperator`、`addResource` 等。

**影响：**
已撤角色的地址仍保留对原实体的未授权控制，可继续增删 operator 与资源。

**修复建议：**
撤角色时显式清除该地址相关的 `ownersEntities`、`entityByOperator`、`entityByResource` 等映射，确保完全失去实体管理权限。

---

## 19. Untrusted Contract Remains Callable via Whitelisted Function After Trust Revocation

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
`OmniVaultExecutor` maintains a `whitelistedFunctions` mapping (function selector → contract address) that `OMNITRADER_ROLE` holders can invoke via the contract's `fallback` handler. When adding a new whitelisted function via `_setWhitelistedFunction`, the contract correctly verifies that the target is currently trusted. However, when an admin calls `setTrustedContract(_contract, ContractAccess.NONE)` to revoke trust from a contract, the revocation only updates the `trustedContracts` mapping — it does not remove the contract's entries from `whitelistedFunctions`. The `fallback` function only checks that `whitelistedFunctions[sig] != address(0)` and does not re-verify the current trust status of the target, so `OMNITRADER_ROLE` can still call functions on the now-untrusted contract.

**Impact:**
Trust revocation is ineffective at preventing `OMNITRADER_ROLE` from calling functions on a contract that the admin has explicitly designated as untrusted. The entire purpose of the trust control system is defeated for previously-whitelisted functions.

**Recommended Mitigation:**
Either clean up all `whitelistedFunctions` entries pointing to a contract when its trust is revoked, or add a current trust status re-check in the `fallback` function before delegating execution to the target contract.

---

**[中文版本]**

**描述：**
`OmniVaultExecutor` 维护 `whitelistedFunctions`（选择器 → 合约地址），`OMNITRADER_ROLE` 可通过 `fallback` 调用。`_setWhitelistedFunction` 会校验目标当前受信；但 `setTrustedContract(..., NONE)` 撤销信任时只更新 `trustedContracts`，未从 `whitelistedFunctions` 移除。`fallback` 仅检查 `whitelistedFunctions[sig] != address(0)`，不再次校验目标当前信任状态，故仍可调用已标记为不受信的合约。

**影响：**
撤销信任无法阻止 `OMNITRADER_ROLE` 对已显式取消信任的合约调用先前白名单函数，信任控制对该路径失效。

**修复建议：**
撤销合约信任时同步清除指向该合约的所有 `whitelistedFunctions` 项，或在 `fallback` 委托执行前重新校验目标当前是否受信。

---

## 20. WLFI Owner Can DoS Legacy Users Through Direct Vester Activation

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
`WorldLibertyFinancialVester::ownerActivateVest` allows the owner to directly activate a user's vesting with arbitrary `category` and `amount` parameters, bypassing the normal coordinated activation flow that reads these parameters from the registry (`WLFI V2 → Registry::wlfiActivateAccount → Vester::wlfiActivateVest`). The vester's `_activateVest` function prevents double-initialization by reverting with `AlreadyInitialized` if a user's record has already been set. If the owner uses `ownerActivateVest` to activate a legacy user — whether with incorrect parameters, or even with correct ones but ahead of the user — the user is permanently locked out of the normal activation path. In the case of incorrect parameters, the user is stuck with wrong vesting terms and cannot self-correct.

**Impact:**
Owner can cause a permanent denial-of-service for any legacy user's activation, leaving them with incorrectly configured vesting parameters (wrong category, wrong allocation amount) they have no mechanism to override or correct.

**Recommended Mitigation:**
For legacy users, add validation in `ownerActivateVest` to verify that the provided parameters match the registry data before proceeding. Automatically sync registry state to mark the account as activated. Alternatively, remove `ownerActivateVest` entirely to eliminate this attack surface.

---

**[中文版本]**

**描述：**
`WorldLibertyFinancialVester::ownerActivateVest` 允许所有者以任意 `category`、`amount` 直接激活用户归属，绕过正常从注册表读取参数的协调流程。`_activateVest` 若用户记录已设置会以 `AlreadyInitialized` 回滚。若所有者对遗留用户抢先或错误参数调用 `ownerActivateVest`，用户将永久无法走正常激活路径；错误参数下用户无法自行纠正。

**影响：**
所有者可对任意遗留用户造成激活永久拒绝服务，或使其锁定在错误的归属条款（类别、额度）下。

**修复建议：**
对遗留用户在 `ownerActivateVest` 中校验参数与注册表一致后再执行；同步注册表标记账户已激活；或完全移除 `ownerActivateVest` 以消除该攻击面。
