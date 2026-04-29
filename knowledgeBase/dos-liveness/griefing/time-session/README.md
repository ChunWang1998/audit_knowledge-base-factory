# time-session (8)

> Issues involving time-based logic, session management, or dispute windows that can be exploited or griefed.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Assembly blocks could benefit from memory-safe annotation

**Severity:** 🟡 Medium
**Source:** `cyfrin/spingame.md`

**Description:**
`Spin::_hashParticipation` and `Spin::_hashClaim` use inline assembly blocks to efficiently compute EIP-712 hashes. Both blocks only read from and write to memory after the free memory pointer (`0x40`), which means they conform to the Solidity `"memory-safe"` memory model. Without the `"memory-safe"` annotation, the compiler treats these assembly blocks as potentially unsafe and skips additional code generation optimizations that are valid for memory-safe assembly.

**Impact:**
Missing `"memory-safe"` annotations prevent the Solidity compiler from applying valid optimizations to the hashing functions, resulting in slightly higher gas costs for every participation and claim hash computation.

**Recommended Mitigation:**
Add the `"memory-safe"` annotation to both assembly blocks: `assembly ("memory-safe") { ... }`.

---

**[中文版本]**

**描述：**
`Spin::_hashParticipation` 和 `Spin::_hashClaim` 使用内联汇编块高效计算 EIP-712 哈希。两个块仅读取和写入空闲内存指针（`0x40`）之后的内存，符合 Solidity `"memory-safe"` 内存模型。没有 `"memory-safe"` 注解，编译器将这些汇编块视为潜在不安全并跳过对内存安全汇编有效的额外代码生成优化。

**影響：**
缺少 `"memory-safe"` 注解会阻止 Solidity 编译器对哈希函数应用有效优化，导致每次参与和领取哈希计算的 gas 成本略高。

**修復建議：**
在两个汇编块中添加 `"memory-safe"` 注解：`assembly ("memory-safe") { ... }`。

---

## 2. Compliance Status is Decoupled from Voting Power

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Tokenizer.Estate.txt`

**Description:**
`RealEstateToken` integrates OpenZeppelin's `ERC20VotesUpgradeable` for on-chain governance and also implements compliance mechanisms including `setFrozen`, `lockBalance`, and a transfer whitelist. However, the compliance functions operate on separate storage mappings (`_frozen`, `_locked`, `_whitelisted`) and have no interaction with the voting checkpoint system. When an account is frozen, has its balance locked, or is removed from the whitelist, its token transfer ability is restricted — but its voting power checkpoints remain unchanged. The compliance restrictions and governance rights are completely decoupled.

**Impact:**
Accounts that governance has restricted for compliance reasons (e.g., frozen or de-whitelisted accounts) can still fully participate in and influence on-chain votes. This undermines the purpose of the compliance controls and can allow non-compliant actors to manipulate governance outcomes.

**Recommended Mitigation:**
Update the compliance functions (`setFrozen`, `lockBalance`, whitelist management) to also update the voting checkpoints, or override the voting functions to return zero for accounts that are in a non-compliant state.

---

**[中文版本]**

**描述：**
`RealEstateToken` 集成了 OpenZeppelin 的 `ERC20VotesUpgradeable` 用于链上治理，同时实现了包括 `setFrozen`、`lockBalance` 和转账白名单的合规机制。然而，合规函数在独立的存储映射（`_frozen`、`_locked`、`_whitelisted`）上运作，与投票检查点系统没有任何交互。当账户被冻结、余额被锁定或从白名单中移除时，其代币转账能力受到限制——但其投票权检查点保持不变。合规限制和治理权利完全脱耦。

**影響：**
因合规原因被治理机构限制的账户（例如，被冻结或从白名单移除的账户）仍可完全参与并影响链上投票。这破坏了合规控制的目的，可能允许不合规行为者操纵治理结果。

**修復建議：**
更新合规函数（`setFrozen`、`lockBalance`、白名单管理）以同时更新投票检查点，或覆盖投票函数，对处于不合规状态的账户返回零。

---

## 3. Dispute Window Calculated From Session Start Time Instead of Last Proof Submission

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
`completeSessionJob` enforces a dispute window by requiring `block.timestamp >= session.startTime + disputeWindow` before a non-depositor can complete the job. Using `session.startTime` as the reference is semantically incorrect and architecturally flawed. First, the `disputeWindow` is a global constant ranging from 30 seconds to 7 days, while `maxDuration` is a per-session variable set by the user — comparing them against the same reference point is meaningless. Second, using the start time means that for long sessions, the dispute window expires early in the session lifecycle, while for short sessions it may block completion for most of the session duration.

**Impact:**
The dispute window mechanism does not function as designed. For sessions shorter than the `disputeWindow`, the function permanently blocks non-depositor completion. For sessions much longer than the `disputeWindow`, the window is effectively useless as it expires almost immediately relative to the session's total runtime.

**Recommended Mitigation:**
Calculate the dispute window from the time of last proof submission (`lastProofTime`) rather than `session.startTime`, so the window represents a meaningful post-proof dispute period.

---

**[中文版本]**

**描述：**
`completeSessionJob` 通过要求 `block.timestamp >= session.startTime + disputeWindow` 来执行争议窗口，非存款人完成工作前必须满足此条件。使用 `session.startTime` 作为参考在语义上不正确且架构上有缺陷。首先，`disputeWindow` 是一个范围从 30 秒到 7 天的全局常量，而 `maxDuration` 是用户设置的每会话变量——将它们与同一参考点比较没有意义。其次，使用开始时间意味着对于长会话，争议窗口在会话生命周期早期就过期；对于短会话，可能在大部分会话持续时间内阻止完成。

**影響：**
争议窗口机制未按设计运行。对于比 `disputeWindow` 短的会话，函数永久阻止非存款人完成。对于比 `disputeWindow` 长得多的会话，窗口实际上毫无用处，因为相对于会话的总运行时间几乎立即过期。

**修復建議：**
从最后一次证明提交时间（`lastProofTime`）而非 `session.startTime` 计算争议窗口，使窗口代表有意义的证明后争议期。

---

## 4. Insufficient update window validation can cause denial of service in forceUpdateNodes

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware` constructor does not validate that `UPDATE_WINDOW < EPOCH_DURATION`. The `onlyDuringFinalWindowOfEpoch` modifier creates a valid execution window only when `timeNow >= epochStartTs + UPDATE_WINDOW` and `timeNow <= epochStartTs + EPOCH_DURATION`. If `UPDATE_WINDOW >= EPOCH_DURATION`, the first condition can never be satisfied within the same epoch as the second, making it mathematically impossible to satisfy both conditions simultaneously and causing the modifier to always revert. Functions protected by this modifier — including the stake management functionality used for `forceUpdateNodes` — become permanently inaccessible.

**Impact:**
If `UPDATE_WINDOW` is misconfigured to be greater than or equal to `EPOCH_DURATION` at deployment, all functions protected by `onlyDuringFinalWindowOfEpoch` are permanently bricked, preventing any stake management operations for the lifetime of the contract.

**Recommended Mitigation:**
Add a constructor validation that reverts if `UPDATE_WINDOW >= EPOCH_DURATION`, similar to the existing `slashingWindow` validation.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware` 构造函数未验证 `UPDATE_WINDOW < EPOCH_DURATION`。`onlyDuringFinalWindowOfEpoch` 修饰符仅在 `timeNow >= epochStartTs + UPDATE_WINDOW` 且 `timeNow <= epochStartTs + EPOCH_DURATION` 时创建有效的执行窗口。如果 `UPDATE_WINDOW >= EPOCH_DURATION`，则第一个条件在与第二个条件相同的轮次内永远无法满足，使两个条件同时满足在数学上不可能，导致修饰符始终回滚。受此修饰符保护的函数——包括用于 `forceUpdateNodes` 的质押管理功能——将永久无法访问。

**影響：**
如果在部署时 `UPDATE_WINDOW` 被错误配置为大于或等于 `EPOCH_DURATION`，所有受 `onlyDuringFinalWindowOfEpoch` 保护的函数将永久失效，阻止合约整个生命周期内的任何质押管理操作。

**修復建議：**
添加构造函数验证，若 `UPDATE_WINDOW >= EPOCH_DURATION` 则回滚，类似于现有的 `slashingWindow` 验证。

---

## 5. Refund Failure Prevents Host Payment and Locks Session

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
`_settleSessionPayments` processes both the host payment and the user refund in a single atomic transaction. The execution order is: (1) calculate `hostPayment` and `userRefund`, (2) transfer `hostPayment` to the `HostEarningsUpgradeable` contract, (3) transfer `userRefund` to `session.depositor`. If step 3 fails — because the depositor is a smart contract that rejects transfers, or the depositor's address is blacklisted by the payment token (e.g., USDC, USDT) — the entire transaction reverts, including the host payment in step 2. Both `completeSessionJob` and `triggerSessionTimeout` call this function, so if it always reverts, the session remains permanently in the Active state with all funds locked.

**Impact:**
A depositor using a contract wallet that rejects transfers, or a depositor whose address is token-blacklisted, can permanently freeze a session: the host can never collect earned payment, and the depositor can never recover their deposit. All session funds are permanently locked.

**Recommended Mitigation:**
Separate the host payment from the user refund into independent operations. Use a pull-payment pattern for the user refund, recording the amount owed and allowing the depositor to claim it separately, so that a failed refund transfer does not revert the host payment.

---

**[中文版本]**

**描述：**
`_settleSessionPayments` 在单个原子交易中处理主机付款和用户退款。执行顺序为：（1）计算 `hostPayment` 和 `userRefund`，（2）将 `hostPayment` 转移到 `HostEarningsUpgradeable` 合约，（3）将 `userRefund` 转移给 `session.depositor`。如果步骤 3 失败——因为存款人是拒绝转账的智能合约钱包，或存款人地址被支付代币（如 USDC、USDT）列入黑名单——整个交易回滚，包括步骤 2 中的主机付款。`completeSessionJob` 和 `triggerSessionTimeout` 都调用此函数，因此如果始终回滚，会话将永久处于 Active 状态，所有资金被锁定。

**影響：**
使用拒绝转账的合约钱包的存款人，或地址被代币列入黑名单的存款人，可以永久冻结会话：主机永远无法收到已赚取的付款，存款人也永远无法取回存款。所有会话资金被永久锁定。

**修復建議：**
将主机付款与用户退款分离为独立操作。对用户退款使用拉取付款模式，记录欠款金额并允许存款人单独领取，使失败的退款转账不会回滚主机付款。

---

## 6. SessionManager::rescheduleGame advances the start time but not the end time allowing for a griefing attack

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`SessionManager::rescheduleGame` updates `game.startTime` to a new value but never updates `game.endTime`. Since the maximum game duration is 10 minutes and `minimumRescheduleTime` is 15 minutes, rescheduling always sets the new start time past the existing end time. A malicious game creator can exploit this by: rescheduling the game, then immediately revealing all questions with minimum reaction deadlines (5 seconds each), concluding the game in minutes, and collecting all entry fees — while players had insufficient time to participate and cannot get refunds because the game is in the `Concluded` state.

**Impact:**
Game creators can conduct "speed-run" games that prevent genuine player participation. By exploiting the discrepancy between start and end time after rescheduling, creators can steal player entry fees while players have no meaningful ability to participate or claim refunds.

**Recommended Mitigation:**
In `rescheduleGame`, also update `game.endTime` by adding the original game duration (original end time minus original start time) to the new start time, ensuring the game window remains consistent.

---

**[中文版本]**

**描述：**
`SessionManager::rescheduleGame` 将 `game.startTime` 更新为新值，但从不更新 `game.endTime`。由于最大游戏时长为 10 分钟，`minimumRescheduleTime` 为 15 分钟，重新安排时间总是将新开始时间设定在现有结束时间之后。恶意游戏创建者可以利用此漏洞：重新安排游戏时间，然后立即以最短反应截止时间（每个 5 秒）揭示所有问题，在几分钟内完成游戏，并收取所有入场费——而玩家没有足够的时间参与，且因游戏处于 `Concluded` 状态无法获得退款。

**影響：**
游戏创建者可以进行"速通"游戏，阻止真正的玩家参与。通过利用重新安排后开始时间和结束时间之间的差异，创建者可以在玩家几乎没有实质性参与机会且无法申请退款的情况下窃取玩家入场费。

**修復建議：**
在 `rescheduleGame` 中，同时更新 `game.endTime`，方法是将原始游戏时长（原始结束时间减去原始开始时间）加到新开始时间上，确保游戏窗口保持一致。

---

## 7. Testnet Time Constants Used in Production Code

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
`Subscription.sol` and `StakingAndRewards.sol` use time-duration constants configured for testnet/development purposes (minutes/seconds) rather than appropriate production values (days/months). Specifically, `SUBSCRIPTION_PERIOD = 30 minutes` should be `30 days`, and reward calculation periods are in minutes instead of days. This makes the entire economic model and subscription system non-functional on mainnet, with subscriptions expiring in 30 minutes and rewards accruing at a rate thousands of times faster than intended.

**Impact:**
On mainnet deployment, users pay for a "monthly" subscription that expires in 30 minutes, requiring 1,440 renewals per month. Monthly staking rewards (10%/month) accrue over 15 minutes instead of 30 days, draining the contract's funds almost immediately after deployment.

**Recommended Mitigation:**
Replace all testnet time constants with their production equivalents. Set `SUBSCRIPTION_PERIOD = 30 days`, and adjust all reward calculation period constants to reflect correct mainnet timeframes before deployment.

---

**[中文版本]**

**描述：**
`Subscription.sol` 和 `StakingAndRewards.sol` 使用为测试网/开发目的配置的时间常量（分钟/秒）而非适当的生产值（天/月）。具体地，`SUBSCRIPTION_PERIOD = 30 minutes` 应为 `30 days`，奖励计算周期以分钟而非天计算。这使整个经济模型和订阅系统在主网上无法正常运行，订阅在 30 分钟后过期，奖励以比预期快数千倍的速度累积。

**影響：**
在主网部署后，用户为 30 分钟后过期的"月度"订阅付费，每月需要 1,440 次续订。月度质押奖励（10%/月）在 15 分钟内而非 30 天内累积，几乎在部署后立即耗尽合约资金。

**修復建議：**
将所有测试网时间常量替换为生产等效值。在部署前将 `SUBSCRIPTION_PERIOD = 30 days`，并调整所有奖励计算周期常量以反映正确的主网时间范围。

---

## 8. Users can bypass vault lock and withdraw at any time

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierBob::exitWithinGracePeriod` burns the caller's entire share balance and allows immediate withdrawal if the caller has a `_firstDepositTimes` entry and is within the grace period. A user whose shares are locked (grace period expired) can bypass this lock by: (1) transferring their `BobVaultShare` tokens to a fresh address, (2) calling `enter` from the new address with even 1 wei of tokens to create a new `_firstDepositTimes` entry, and (3) calling `exitWithinGracePeriod` from the new address, which burns the entire transferred share balance and returns all underlying assets. The lock mechanism is completely circumvented at the cost of 1 token.

**Impact:**
The vault's core value proposition — locking tokens until a price target is reached or expiry passes — is completely defeated. Any user can withdraw at any time while the vault is active, undermining all lock commitments and potentially destabilizing the vault's price-targeting mechanism.

**Recommended Mitigation:**
When checking `exitWithinGracePeriod`, verify that the shares being withdrawn were all deposited within the grace window (e.g., by tracking per-address deposit timestamps). Do not allow withdrawal of shares that were received via transfer rather than direct deposit within the grace period.

---

**[中文版本]**

**描述：**
`SablierBob::exitWithinGracePeriod` 销毁调用者的全部份额余额，并在调用者有 `_firstDepositTimes` 记录且在宽限期内时允许立即提款。份额被锁定的用户（宽限期已过期）可以通过以下方式绕过此锁定：（1）将其 `BobVaultShare` 代币转移到新地址，（2）从新地址以哪怕 1 wei 的代币调用 `enter` 以创建新的 `_firstDepositTimes` 记录，（3）从新地址调用 `exitWithinGracePeriod`，销毁所有已转移的份额余额并返还全部底层资产。锁定机制以 1 个代币的成本被完全规避。

**影響：**
金库的核心价值主张——在达到价格目标或到期之前锁定代币——被完全破坏。任何用户都可以在金库激活时随时提款，破坏了所有锁定承诺，可能使金库的价格目标机制不稳定。

**修復建議：**
在检查 `exitWithinGracePeriod` 时，验证被提取的份额是否都在宽限期内存入（例如，通过跟踪每个地址的存款时间戳）。不允许提取通过转账而非在宽限期内直接存款收到的份额。
