# hardcoded-overpayment (14)

> Issues from hardcoded values, static gas limits, or misconfigured parameters causing overpayment or incorrect behavior.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Secondary Contributions Not Recorded in Slot Total, Leading to Incorrect Payout Ratios

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**
`F-2025-14280` — The `Komiti` contract supports "Joint Contributors" where two users share a single slot. The Primary Contributor's total slot balance is tracked in `s_contributions[groupId][primary]`, and the Secondary Contributor's equity is tracked separately in `s_contributionShares[groupId][secondary]`. Payouts to the Secondary are calculated as `SecondaryEquity / TotalSlotBalance`. However, `contributeAsJointMember` updates only `s_contributionShares` when the Secondary contributes, without adding the contribution to `s_contributions[primary]`. This breaks the invariant that `s_contributions[primary]` equals the sum of both users' deposits. In payout calculations, `totalContributions` is understated, making the ratio `secondaryContribution / totalContributions` artificially high — in extreme cases, the Secondary could receive 100% of the slot payout.

**Impact:**
Secondary Contributors receive inflated payouts at the expense of Primary Contributors. In extreme cases (e.g., when the Primary has not yet contributed to the current cycle), the Secondary may receive 100% of the payout while the Primary receives nothing.

**Recommended Mitigation:**
In `contributeAsJointMember`, when the Secondary Contributor deposits, also add the contribution amount to `s_contributions[groupId][primaryContributor]` to maintain the total slot balance invariant.

---

**[中文版本]**

**描述：**
`F-2025-14280` — `Komiti` 合约支持"联合贡献者"，两个用户共享一个名额。主贡献者的总名额余额在 `s_contributions[groupId][primary]` 中追踪，次贡献者的权益在 `s_contributionShares[groupId][secondary]` 中单独追踪。对次贡献者的支付计算为 `SecondaryEquity / TotalSlotBalance`。然而，`contributeAsJointMember` 在次贡献者存款时仅更新 `s_contributionShares`，而不将贡献加入 `s_contributions[primary]`，破坏了 `s_contributions[primary]` 等于两位用户存款总和的不变量。在支付计算中，`totalContributions` 被低估，使 `secondaryContribution / totalContributions` 比率人为偏高——极端情况下次贡献者可获得 100% 的名额支付。

**影響：**
次贡献者以主贡献者的损失为代价获得虚高支付。在极端情况下（例如主贡献者尚未向当前周期贡献时），次贡献者可能获得 100% 的支付而主贡献者分文未得。

**修復建議：**
在 `contributeAsJointMember` 中，当次贡献者存款时，同时将贡献金额加入 `s_contributions[groupId][primaryContributor]`，以维护总名额余额不变量。

---

## 2. Fix comment in revealSolution

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
The NatSpec comment above `revealSolutions` states that the function is intended to be called by the session manager; however, the implementation is callable by anyone. The comment is outdated and misleads developers and reviewers about the access control model of the function.

**Impact:**
No security risk from the comment itself. However, an incorrect NatSpec comment can mislead developers into assuming the function has access control, potentially causing them to overlook the open callable surface during reviews or audits.

**Recommended Mitigation:**
Update the NatSpec comment for `revealSolutions` to accurately reflect that the function is publicly callable and not restricted to the session manager.

---

**[中文版本]**

**描述：**
`revealSolutions` 上方的 NatSpec 注释说明该函数意图由会话管理器调用，但实现中任何人均可调用。注释已过时，误导开发者和审查者对函数访问控制模型的理解。

**影響：**
注释本身无安全风险，但错误的 NatSpec 注释可能误导开发者认为函数有访问控制，可能导致在审查或审计时忽视开放的调用面。

**修復建議：**
更新 `revealSolutions` 的 NatSpec 注释，准确反映该函数可公开调用，不限于会话管理器。

---

## 3. Hardcoded Primary Pair In _calculatePriceImpact() Leads To Price Impact Limit Bypass On Secondary DEX Pairs

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
`F-2026-15004` — The `NTE` contract enforces a price impact limit on sells to registered DEX pairs. The sell detection logic correctly identifies sells to any registered pair using `isPancakePair[to]`. However, `_calculatePriceImpact()` always reads reserves from the hardcoded primary pair (`pancakePair`), never from the actual destination pair. A sell to a shallow secondary pair (e.g., 100,000 NTE liquidity) is evaluated against the deep primary pair (e.g., 10,000,000 NTE liquidity), significantly underestimating the real price impact and allowing the secondary pair to be exploited without triggering the protection.

**Impact:**
Large sells routed to shallow secondary DEX pairs bypass the price impact protection mechanism, allowing trades that would crash the token price on secondary markets to proceed unchecked.

**Recommended Mitigation:**
Pass the destination pair address to `_calculatePriceImpact()` and read reserves from the actual destination pair rather than the hardcoded primary pair.

---

**[中文版本]**

**描述：**
`F-2026-15004` — `NTE` 合约对向已注册 DEX 对的卖出强制执行价格影响限制。卖出检测逻辑通过 `isPancakePair[to]` 正确识别所有已注册对的卖出。然而，`_calculatePriceImpact()` 始终从硬编码的主对（`pancakePair`）读取储备量，而非实际目标对。向流动性浅的次级对卖出（例如 100,000 NTE 流动性）被与深度主对（例如 10,000,000 NTE 流动性）对比评估，大幅低估真实价格影响，允许次级对在不触发保护的情况下被利用。

**影響：**
路由至流动性浅的次级 DEX 对的大额卖出绕过了价格影响保护机制，允许会导致次级市场代币价格崩溃的交易未受检查地通过。

**修復建議：**
将目标对地址传递给 `_calculatePriceImpact()` 并从实际目标对读取储备量，而非使用硬编码的主对。

---

## 4. Hardcoded Private Key Exposure in Test Scripts Enables Unauthorized Account Control

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
`F-2026-15280` — Private keys are hardcoded as literal constants in repository integration test scripts (`tests/integration/usdc-payment-flow.js`, `tests/integration/usdc-complete-cycle.js`, `tests/examples/usdc-job-parsing-example.js`). The derived wallet addresses show on-chain activity from October 2025, indicating these are not purely synthetic test keys. Any actor with repository access can derive the same accounts and produce valid signatures, potentially impersonating trusted signers or executing unauthorized transactions if the keys were reused in operational contexts.

**Impact:**
Exposure of private keys in version control history grants full signing authority over the derived accounts to any repository reader. If the same credentials were reused in deployment pipelines, relayers, or privileged off-chain services, unauthorized transactions could be executed. The exposure persists in Git history even after file-level replacement.

**Recommended Mitigation:**
Immediately rotate all exposed keys. Rewrite Git history to remove the sensitive data (e.g., using `git filter-branch` or BFG Repo Cleaner). Use environment variables or secret managers for all sensitive credentials in test scripts going forward.

---

**[中文版本]**

**描述：**
`F-2026-15280` — 私钥以字面常量形式硬编码在仓库集成测试脚本中（`tests/integration/usdc-payment-flow.js`、`tests/integration/usdc-complete-cycle.js`、`tests/examples/usdc-job-parsing-example.js`）。派生的钱包地址显示 2025 年 10 月有链上活动，表明这些不是纯合成测试密钥。任何有仓库访问权限的人员可派生相同账户并生成有效签名，若密钥在运营环境中被复用，可能冒充受信任签署者或执行未授权交易。

**影響：**
版本控制历史中的私钥暴露将派生账户的完整签名权限授予任意仓库读者。若相同凭证在部署管道、中继者或特权链下服务中被复用，可能执行未授权交易。即使文件级替换后，敏感数据仍存在于 Git 历史中。

**修復建議：**
立即轮换所有暴露的密钥，重写 Git 历史以删除敏感数据（例如使用 `git filter-branch` 或 BFG Repo Cleaner），并在测试脚本中改用环境变量或密钥管理器存储所有敏感凭证。

---

## 5. High centralization risk in STBL_USST::bridgeBurn

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
`STBL_USST::bridgeBurn` allows the `BRIDGE_ROLE` (initialized to `DEFAULT_ADMIN`) to burn tokens from any arbitrary address without requiring user approval or consent. This contrasts with the safer `STBL_Token::bridgeBurn` implementation that only burns the caller's (bridge's) own tokens. A compromise of the bridge contract or admin key could result in mass token burning from arbitrary user accounts in a single transaction.

**Impact:**
If the bridge contract or admin key is compromised, an attacker can burn tokens from any user's account, destroying user holdings and rendering the token ecosystem insolvent. This represents a severe centralization risk and single point of failure.

**Recommended Mitigation:**
Adopt the `STBL_Token` approach: have `bridgeBurn` only burn the caller's own tokens (`_burn(_msgSender(), _amt)`), or require explicit user-signed approvals before burning from arbitrary addresses.

---

**[中文版本]**

**描述：**
`STBL_USST::bridgeBurn` 允许 `BRIDGE_ROLE`（初始化为 `DEFAULT_ADMIN`）在不需要用户授权或同意的情况下从任意地址销毁代币。这与更安全的 `STBL_Token::bridgeBurn` 实现（仅销毁调用者/桥接者自身的代币）形成对比。若桥接合约或管理员密钥被攻破，可能导致在单笔交易中大规模销毁任意用户账户的代币。

**影響：**
若桥接合约或管理员密钥被攻破，攻击者可销毁任意用户账户的代币，摧毁用户持仓并使代币生态资不抵债，构成严重的中心化风险和单点故障。

**修復建議：**
采用 `STBL_Token` 方式：让 `bridgeBurn` 仅销毁调用者自身的代币（`_burn(_msgSender(), _amt)`），或在从任意地址销毁前要求用户明确签署授权。

---

## 6. Overpayment vulnerability in registerL1

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`L1Registry::registerL1` does not handle excess Ether sent by users. If `registerFee` is non-zero and a user sends more Ether than required, the contract retains the entire amount with no refund logic. If `registerFee` is zero and any Ether is sent, it becomes permanently trapped because the fee collector can only withdraw tracked unclaimed fees and has no path to recover untracked amounts.

**Impact:**
Users can unintentionally lose funds by sending more Ether than required for registration. With a zero `registerFee`, any Ether sent is permanently locked in the contract with no recovery path.

**Recommended Mitigation:**
Add refund logic to return excess Ether above the required `registerFee` to the sender. If `registerFee` is zero, revert the transaction if any Ether is sent to prevent accidental loss.

---

**[中文版本]**

**描述：**
`L1Registry::registerL1` 不处理用户多发送的以太币。若 `registerFee` 非零且用户发送超出所需的以太币，合约保留全部金额而无退款逻辑。若 `registerFee` 为零且发送了任何以太币，该金额将永久锁定在合约中，因为手续费收集者只能提取被追踪的未领取手续费，无法恢复未追踪的金额。

**影響：**
用户可能因发送超出注册所需的以太币而无意中损失资金。当 `registerFee` 为零时，任何发送的以太币将永久锁定在合约中且无法恢复。

**修復建議：**
添加退款逻辑，将超出所需 `registerFee` 的多余以太币退还给发送者。若 `registerFee` 为零，在发送任何以太币时回滚交易，以防止意外损失。

---

## 7. PerpetualBond.epoch not updated after yield distribution

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`PerpetualBond::distributeBondYield` requires the caller to provide a `nonce` equal to `epoch + 1` to sequence yield distributions. However, `epoch` is never incremented after the distribution executes. This means the `epoch` counter remains permanently at its initial value, and subsequent calls will always require `nonce == epoch + 1` (the same value), potentially enabling repeated calls with the same nonce or breaking the sequencing invariant.

**Impact:**
The epoch counter does not advance, breaking the intended sequencing of yield distributions and potentially allowing the same nonce to be reused or creating unexpected state in the bond accounting.

**Recommended Mitigation:**
Add `epoch = nonce` (or `epoch++`) at the end of `distributeBondYield` to increment the epoch counter after each successful distribution.

---

**[中文版本]**

**描述：**
`PerpetualBond::distributeBondYield` 要求调用者提供等于 `epoch + 1` 的 `nonce` 以对收益分配进行排序。然而，分配执行后 `epoch` 从不递增，意味着 `epoch` 计数器永久保持初始值，后续调用将始终需要相同的 `nonce == epoch + 1`，可能允许使用相同 nonce 重复调用或破坏排序不变量。

**影響：**
epoch 计数器不递进，破坏收益分配的预期排序，可能允许相同 nonce 被重复使用或在债券核算中创建意外状态。

**修復建議：**
在 `distributeBondYield` 末尾添加 `epoch = nonce`（或 `epoch++`），以在每次成功分配后递增 epoch 计数器。

---

## 8. Precompute baseSlot in AtomicBatcher::_getNonceSlot

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`AtomicBatcher::_getNonceSlot` recomputes the ERC-7201 namespace base slot at runtime on every call: it hashes `_NAMESPACE` and derives `baseSlot` via `keccak256`. Since `_NAMESPACE` is a constant, the `baseSlot` value is also a constant and can be precomputed and stored as a `bytes32` constant, saving the hash computation overhead on every call.

**Impact:**
No security risk. Minor gas inefficiency on every nonce slot lookup.

**Recommended Mitigation:**
Precompute `baseSlot` as a `bytes32 private constant` initialized at compile time using the ERC-7201 derivation formula, and use the constant directly in `_getNonceSlot`.

---

**[中文版本]**

**描述：**
`AtomicBatcher::_getNonceSlot` 在每次调用时运行时重新计算 ERC-7201 命名空间基础槽：对 `_NAMESPACE` 进行哈希并通过 `keccak256` 派生 `baseSlot`。由于 `_NAMESPACE` 是常量，`baseSlot` 值也是常量，可预先计算并存储为 `bytes32` 常量，节省每次调用的哈希计算开销。

**影響：**
无安全风险，每次 nonce 槽查找时存在轻微燃气低效。

**修復建議：**
使用 ERC-7201 派生公式在编译时预先计算 `baseSlot` 为 `bytes32 private constant`，并在 `_getNonceSlot` 中直接使用该常量。

---

## 9. Precompute callTypeHash in AtomicBatcher::_hashCallArray

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`AtomicBatcher::_hashCallArray` recomputes `callTypeHash = keccak256("Call(address target,uint256 value,bytes data)")` on every invocation. Since this string is a compile-time constant, the resulting hash is also a constant and can be stored as a `bytes32 private constant _CALL_TYPEHASH` to avoid the redundant hash computation on each call.

**Impact:**
No security risk. Minor gas inefficiency on every call array hash computation.

**Recommended Mitigation:**
Define `bytes32 private constant _CALL_TYPEHASH = keccak256("Call(address target,uint256 value,bytes data)")` and use `_CALL_TYPEHASH` in `_hashCallArray` instead of recomputing.

---

**[中文版本]**

**描述：**
`AtomicBatcher::_hashCallArray` 在每次调用时重新计算 `callTypeHash = keccak256("Call(address target,uint256 value,bytes data)")`。由于该字符串是编译时常量，结果哈希也是常量，可存储为 `bytes32 private constant _CALL_TYPEHASH` 以避免每次调用时的冗余哈希计算。

**影響：**
无安全风险，每次调用数组哈希计算时存在轻微燃气低效。

**修復建議：**
定义 `bytes32 private constant _CALL_TYPEHASH = keccak256("Call(address target,uint256 value,bytes data)")` 并在 `_hashCallArray` 中使用 `_CALL_TYPEHASH` 替代重新计算。

---

## 10. Prevent negative assertion following previous truthful assertion in DefaultSession::assertionResolvedCallback

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DefaultSession::assertionResolvedCallback` does not guard against being called a second time with `assertedTruthfully = false` for an `assertionId` that was already resolved truthfully. If this occurs, `delete assertions[assertionId]` executes even though results have already been recorded based on the first truthful assertion, silently deleting the assertion record and potentially allowing the assertion to be re-submitted.

**Impact:**
A second callback with `assertedTruthfully = false` on an already-resolved assertion deletes the assertion record, undermining the finality of resolved game outcomes and potentially enabling re-assertion manipulation.

**Recommended Mitigation:**
Add a guard at the start of `assertionResolvedCallback`: revert if `assertions[assertionId].resolved` is already `true`, preventing any further callbacks on a resolved assertion.

---

**[中文版本]**

**描述：**
`DefaultSession::assertionResolvedCallback` 不防范对已真实解析的 `assertionId` 以 `assertedTruthfully = false` 进行第二次调用。若发生此情况，即使结果已基于第一次真实断言记录，`delete assertions[assertionId]` 也会执行，静默删除断言记录并可能允许断言被重新提交。

**影響：**
对已解析断言以 `assertedTruthfully = false` 进行第二次回调会删除断言记录，破坏已解析游戏结果的最终性，并可能启用重新断言操纵。

**修復建議：**
在 `assertionResolvedCallback` 开头添加保护：若 `assertions[assertionId].resolved` 已为 `true`，则回滚，防止对已解析断言进行任何后续回调。

---

## 11. Rename isAllowed to wasAllowed in Allowlist::allowUser, disallowUser

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`Allowlist::allowUser` and `disallowUser` return the existing `allowed` status into a named return variable called `isAllowed`, before potentially modifying the `allowed` status. The name `isAllowed` implies the current state, but the function may change the state before returning, making the variable name misleading. The returned value reflects what the status was before the call, not what it is after.

**Impact:**
No security risk. Misleading variable name can cause callers to misinterpret the return value as the post-call state rather than the pre-call state.

**Recommended Mitigation:**
Rename the named return variable from `isAllowed` to `wasAllowed` to accurately reflect that it captures the prior state before the modification.

---

**[中文版本]**

**描述：**
`Allowlist::allowUser` 和 `disallowUser` 将现有 `allowed` 状态返回到名为 `isAllowed` 的命名返回变量中，然后可能修改 `allowed` 状态。名称 `isAllowed` 暗示当前状态，但函数可能在返回前更改状态，使变量名具有误导性。返回值反映的是调用前的状态，而非调用后的状态。

**影響：**
无安全风险，但误导性变量名可能导致调用者将返回值误解为调用后状态而非调用前状态。

**修復建議：**
将命名返回变量从 `isAllowed` 重命名为 `wasAllowed`，以准确反映其捕获的是修改前的先前状态。

---

## 12. Static gasLimit will result in overpayment

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`BridgeCCIP::send` hardcodes `gasLimit: 200_000` in the `extraArgs` of every CCIP message. Chainlink does not refund unspent gas on the destination chain. Since the actual gas consumed by `_ccipReceive` is significantly less than 200,000, every cross-chain message consistently overpays for execution on the destination chain. Additionally, hardcoding `extraArgs` prevents future adjustments if execution costs change due to protocol upgrades or EIPs.

**Impact:**
Every user bridging tokens consistently overpays for CCIP execution gas. Over the lifetime of the bridge, this represents a significant aggregate overpayment that harms all bridge users.

**Recommended Mitigation:**
Measure actual gas consumption of `_ccipReceive` and set the `gasLimit` to a value close to the actual cost plus a safety margin. Make `extraArgs` configurable (e.g., pass as a parameter or store in contract state) to allow future adjustments.

---

**[中文版本]**

**描述：**
`BridgeCCIP::send` 在每条 CCIP 消息的 `extraArgs` 中硬编码 `gasLimit: 200_000`。Chainlink 不退还目标链上未使用的燃气。由于 `_ccipReceive` 的实际燃气消耗远低于 200,000，每条跨链消息都会持续为目标链执行过度支付。此外，硬编码 `extraArgs` 还阻止了在协议升级或 EIP 导致执行成本变化时进行未来调整。

**影響：**
每个桥接代币的用户持续为 CCIP 执行燃气过度支付，在桥接合约生命周期内累计造成对所有桥接用户的重大损失。

**修復建議：**
测量 `_ccipReceive` 的实际燃气消耗，将 `gasLimit` 设置为接近实际成本加安全边际的值，并使 `extraArgs` 可配置（例如作为参数传递或存储在合约状态中），以允许未来调整。

---

## 13. Zero-Duration vesting edge case

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
When `duration == 0`, calling `vestedAmount(start)` with `_timestamp == start` evaluates the condition `_timestamp > start + duration` as `start > start`, which is `false`. Execution falls through to the linear-vest branch and attempts to compute `(totalAllocation * (start - start)) / duration`, which is a division by zero. This creates a one-second window at exactly `_timestamp == start` where the function reverts, even though any later timestamp correctly returns full allocation.

**Impact:**
For zero-duration vesting schedules, the `vestedAmount` function reverts when queried at exactly the start timestamp, creating a brief but avoidable edge case failure.

**Recommended Mitigation:**
Change the comparison from `_timestamp > start + duration` to `_timestamp >= start + duration`, so that zero-duration schedules immediately return full allocation without going through the linear division.

---

**[中文版本]**

**描述：**
当 `duration == 0` 时，以 `_timestamp == start` 调用 `vestedAmount(start)`，条件 `_timestamp > start + duration` 等价于 `start > start`，为 `false`，执行流落入线性归属分支，尝试计算 `(totalAllocation * (start - start)) / duration`，发生除零错误。这在 `_timestamp == start` 时创建了一个一秒的窗口期，函数在此期间回滚，尽管任何后续时间戳都能正确返回完整分配量。

**影響：**
对于零时长归属计划，在恰好查询开始时间戳时 `vestedAmount` 函数回滚，产生短暂但可避免的边缘案例失败。

**修復建議：**
将比较从 `_timestamp > start + duration` 改为 `_timestamp >= start + duration`，使零时长计划立即返回完整分配量，无需经过线性除法。

---

## 14. bondFaceValue read in PerpetualBond::_convertToBond can be cached

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`PerpetualBond::_convertToBond` reads the storage variable `bondFaceValue` twice in the same function: once for the zero-check and once for the division. Since storage reads cost 100 gas (cold) or 100 gas (warm), reading the same slot twice can be avoided by caching the value in a local memory variable after the first read.

**Impact:**
No security risk. Minor gas inefficiency on every call to `_convertToBond`.

**Recommended Mitigation:**
Cache `bondFaceValue` in a local `uint256 _bondFaceValue` variable at the start of the function and use the cached value for both the zero-check and the arithmetic.

---

**[中文版本]**

**描述：**
`PerpetualBond::_convertToBond` 在同一函数中两次读取存储变量 `bondFaceValue`：一次用于零值检查，一次用于除法。由于存储读取每次消耗 100 gas，可通过在第一次读取后将值缓存到局部内存变量来避免重复读取同一存储槽。

**影響：**
无安全风险，每次调用 `_convertToBond` 时存在轻微燃气低效。

**修復建議：**
在函数开始时将 `bondFaceValue` 缓存到局部变量 `uint256 _bondFaceValue` 中，并在零值检查和算术运算中均使用缓存值。
