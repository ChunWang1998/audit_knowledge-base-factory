# timestamp-oracle (8)

> Issues involving stale oracle data, timestamp boundary conditions, or missing freshness validation.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Oracle void outcome leaves PredictionMarketV3ManagerCLOB.voidedPayouts unset, locking collateral

**Severity:** 🟠 High
**Source:** `cyfrin/clob.md`

**Description:**
`PredictionMarketV3ManagerCLOB::resolveMarket` accepts `outcome == -1` from an oracle (the value returned by reality.eth for invalid or unanswered questions) and marks the market as resolved with `resolvedOutcome = -1`, but it never populates `voidedPayouts[marketId]`. When token holders later call `ConditionalTokens::redeemVoided`, the function fetches the payout ratios via `getVoidedPayouts` and asserts they sum to `1e18`. Because `voidedPayouts` was never set, both values remain zero, and the assertion always reverts. Every oracle-voided market therefore has permanently unrecoverable collateral through the normal redemption path.

**Impact:**
All collateral deposited by position holders in oracle-voided markets is locked in `ConditionalTokens` with no immediate recovery path. Because the manager is UUPS upgradeable, the funds are not permanently lost — a patched implementation can unblock redemptions — but users cannot access their collateral until a full development, audit, and deployment cycle is completed.

**Recommended Mitigation:**
Reject `outcome == -1` from the oracle in `resolveMarket` and force all void resolutions through `adminVoidMarket`, which correctly sets the `voidedPayouts` ratios. Alternatively, have `resolveMarket` populate `voidedPayouts` with a default 50/50 split when it encounters `outcome == -1`.

---

**[中文版本]**

**描述：**
`PredictionMarketV3ManagerCLOB::resolveMarket` 接受预言机返回的 `outcome == -1`（reality.eth 对无效或无答案问题的编码）并将市场标记为已解决，但从未设置 `voidedPayouts[marketId]`。持仓用户调用 `ConditionalTokens::redeemVoided` 时，断言赔付比之和等于 `1e18`，由于赔付值始终为零，断言必然回滚，相关抵押品无法赎回。

**影響：**
预言机作废市场中所有持仓用户的抵押品被锁定在 `ConditionalTokens` 合约中，在部署修复实现之前无法取回。

**修復建議：**
在 `resolveMarket` 中拒绝 `outcome == -1`，强制所有作废操作通过 `adminVoidMarket` 进行（该函数会正确设置赔付比例）；或在遇到 `outcome == -1` 时，直接以 50/50 填充 `voidedPayouts`。

---

## 2. Timestamp boundary condition causes reward dilution for active operators

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::_wasActiveAt` uses `>=` for the disabled-time comparison: an operator is considered active when `disabledTime >= timestamp`. This means that when an operator is disabled at the exact epoch start timestamp, the function incorrectly treats them as still active during `calcAndCacheStakes`. Their stake is therefore included in `totalStake`, inflating the denominator used for reward distribution and diluting the rewards of all legitimate active operators.

**Impact:**
Operators disabled at the exact epoch boundary remain active in the stake calculation for that epoch, reducing the reward share of every genuine active operator. The magnitude of dilution is proportional to the stake of disabled-at-boundary operators relative to total stake.

**Recommended Mitigation:**
Change the disabled-time comparison in `_wasActiveAt` from `>=` to `>` so that an operator disabled exactly at epoch start is correctly excluded from that epoch's stake accounting.

---

**[中文版本]**

**描述：**
`_wasActiveAt` 中对禁用时间的比较使用 `>=`，导致恰好在 epoch 起始时间点被禁用的运营商仍被视为活跃，其权益被纳入 `calcAndCacheStakes` 的总权益计算，虚增了奖励分母，稀释了所有合法活跃运营商的奖励。

**影響：**
在 epoch 边界点被禁用的运营商仍会参与该 epoch 的权益计算，导致每个真正活跃运营商的奖励份额被按比例缩小。

**修復建議：**
将 `_wasActiveAt` 中的禁用时间比较从 `>=` 改为 `>`，确保在 epoch 起始时间点被禁用的运营商从该 epoch 的权益统计中被正确排除。

---

## 3. Lack of on-chain oracle circuit breaker

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Tori Finance.txt`

**Description:**
The `ToriMinting.sol` contract validates mint and redeem requests through `verifyOrder`, which relies solely on an EIP-712 signature from a trusted off-chain backend and a `verifyStablesLimit` check that confirms the collateral-to-TrUSD ratio is approximately 1:1. The contract has no on-chain oracle integration and permanently assumes that every supported collateral token (e.g., USDC) is worth exactly 1 USD. If a collateral asset de-pegs, an attacker can present a valid unexpired signature obtained before or during the backend's reaction window and mint TrUSD at face value using devalued collateral, then redeem it for healthy assets.

**Impact:**
When collateral de-pegs, the protocol receives devalued assets while minting stablecoins at full face value, creating immediate bad debt. The longer the backend takes to react and stop signing, the larger the exploitable window, directly threatening TrUSD's peg stability and protocol solvency.

**Recommended Mitigation:**
Integrate an on-chain oracle (e.g., Chainlink) as a circuit breaker inside `verifyOrder` or the mint function. Add a check that the collateral's market price is within a safe band (e.g., above $0.98) and revert if the price falls below the threshold, even when a valid off-chain signature is present.

---

**[中文版本]**

**描述：**
`ToriMinting.sol` 的 `verifyOrder` 函数仅依赖链下后端生成的 EIP-712 签名和 1:1 比例检查，不使用任何链上预言机。如果抵押资产脱锚，攻击者可凭借脱锚前或后端反应窗口内获取的有效签名，以贬值的抵押品铸造等额 TrUSD，再换取其他健康资产。

**影響：**
脱锚发生时协议以面值铸造稳定币但收到贬值资产，立即产生坏账，直接威胁 TrUSD 的锚定稳定性和协议偿付能力。

**修復建議：**
在 `verifyOrder` 或铸造逻辑中集成链上预言机（如 Chainlink）作为断路器，当抵押品市场价格低于安全阈值（如 $0.98）时，即使存在有效签名也应回滚交易。

---

## 4. Missing event emissions for critical oracle parameter changes

**Severity:** 🟡 Medium
**Source:** `cyfrin/stbl.md`

**Description:**
The oracle contracts `STBL_PT1_Oracle` and `STBL_LT1_Oracle` expose several admin functions that modify critical operational parameters — `setPriceDecimals`, `setPriceThreshold`, `enableOracle`, and `disableOracle` — but none of these functions emit events. Without events, off-chain monitoring systems, indexers, and governance tools have no way to detect or audit changes to oracle configuration in a timely manner.

**Impact:**
Undetected or delayed discovery of oracle parameter changes reduces transparency and makes it harder to catch misconfigurations or malicious admin actions that could affect price accuracy and downstream protocol behavior.

**Recommended Mitigation:**
Add event declarations for each of the four admin functions and emit them upon state changes, logging at minimum the old and new parameter values so that off-chain consumers can react to configuration changes promptly.

---

**[中文版本]**

**描述：**
`STBL_PT1_Oracle` 和 `STBL_LT1_Oracle` 的管理函数 `setPriceDecimals`、`setPriceThreshold`、`enableOracle` 和 `disableOracle` 均未发出任何事件，链下监控系统和治理工具无法及时检测预言机配置变更。

**影響：**
预言机参数变更不透明，难以及时发现错误配置或恶意管理员操作，影响价格准确性及下游协议行为。

**修復建議：**
为上述四个管理函数添加事件声明，并在状态变更时发出事件，至少记录旧值和新值，使链下消费者能及时响应配置更改。

---

## 5. Order expiration check uses inclusive bound so order remains valid at the expiration timestamp

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
`MyriadCTFExchange::_validateOrder` checks order validity with `order.expiration == 0 || order.expiration >= block.timestamp`. This treats the order as valid when `block.timestamp` equals `order.expiration`, meaning an order is still executable at the exact moment it is supposed to expire. The field is named `expiration`, which conventionally denotes the first instant at which the order is no longer valid, not the last instant it is valid. This off-by-one behavior can surprise users and integrators who assume the expiration timestamp is exclusive.

**Impact:**
Orders that users believe have expired can still be matched at the exact expiration timestamp, potentially resulting in unintended trade executions that users expected to be blocked.

**Recommended Mitigation:**
Change the expiration check to a strict inequality: `order.expiration == 0 || order.expiration > block.timestamp`, so the order is invalid at and after the exact expiration moment.

---

**[中文版本]**

**描述：**
`MyriadCTFExchange::_validateOrder` 使用 `order.expiration >= block.timestamp` 检查订单有效性，导致在 `block.timestamp == order.expiration` 的精确时刻，订单仍被视为有效可执行。这与 `expiration` 字段的常规语义（到达该时刻即失效）相悖，会给用户和集成方带来误解。

**影響：**
用户认为已过期的订单在精确过期时间戳处仍可被撮合，可能导致用户预期被阻止的意外交易执行。

**修復建議：**
将过期检查改为严格不等式：`order.expiration == 0 || order.expiration > block.timestamp`，确保在过期时间点及其之后订单均失效。

---

## 6. Remove redundant timestamp check in Bet::resolve

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`Bet::resolve` contains a redundant timestamp check. The function first calls `_status(b)` which internally evaluates `block.timestamp > b.resolveBy` to determine whether the bet has expired; if expired, it returns `Status.EXPIRED`, which then triggers the revert on the `!= Status.ACTIVE` check. Separately, the same `block.timestamp > b.resolveBy` condition is also checked explicitly in the if-block. This duplication adds gas overhead and code confusion without providing any additional safety.

**Impact:**
Minor gas waste and reduced code clarity; no security impact, but the redundancy can confuse auditors and maintainers into believing the two checks serve different purposes.

**Recommended Mitigation:**
Remove the explicit `block.timestamp > b.resolveBy` condition from the if-block, relying solely on the `_status(b) != IBet.Status.ACTIVE` check to handle the expiry revert.

---

**[中文版本]**

**描述：**
`Bet::resolve` 中存在冗余的时间戳检查。`_status(b)` 内部已通过 `block.timestamp > b.resolveBy` 判断 bet 是否过期并返回 `EXPIRED` 状态触发回滚，而 if-block 中又重复了相同的时间戳条件，造成双重判断。

**影響：**
轻微的 gas 浪费和代码可读性下降；无安全影响，但冗余逻辑会误导审计人员和维护者。

**修復建議：**
从 if-block 中移除显式的 `block.timestamp > b.resolveBy` 条件，仅依赖 `_status(b) != IBet.Status.ACTIVE` 检查来处理过期回滚。

---

## 7. Use timestamp instead of uri length to test of existing document in DocumentManager

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DocumentManager` uses `bytes($._documents[docHash].docURI).length == 0` as the sentinel check to determine whether a document exists. This approach is fragile: a document intentionally added with an empty URI would pass the check even though the document record exists in storage, and future code changes could inadvertently set empty URIs. The `timestamp` field in `DocData` is a more reliable existence indicator because it is set to `block.timestamp` at document creation and is zero only if the document record was never written.

**Impact:**
Documents with empty URIs bypass the existence guard, potentially allowing operations on document records that should be considered absent, leading to unexpected behavior in upstream access control and signature verification flows.

**Recommended Mitigation:**
Replace the URI length check with a timestamp check: `if ($._documents[docHash].timestamp == 0) revert EmptyDocument()`. The `timestamp` field provides a more robust and semantically clear existence sentinel.

---

**[中文版本]**

**描述：**
`DocumentManager` 使用 `docURI` 的字节长度为零作为文档不存在的哨兵检查，但空 URI 的文档记录同样可以通过此检查，导致存在性判断不可靠。`DocData` 中的 `timestamp` 字段在文档创建时被赋值为 `block.timestamp`，仅在记录从未写入时才为零，是更可靠的存在性标志。

**影響：**
空 URI 的文档记录绕过存在性检查，可能导致上游访问控制和签名验证流程出现意外行为。

**修復建議：**
将 URI 长度检查替换为时间戳检查：`if ($._documents[docHash].timestamp == 0) revert EmptyDocument()`，使用语义更清晰的存在性哨兵。

---

## 8. lastTotalAssets stores stale value due to update before penalty accrual

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
Across the `AccountableYield` strategy, `lastTotalAssets` is updated by reading `_totalAssets()`, which includes `accruedPenalties` in its calculation. However, in all instances where `lastTotalAssets` is set — `borrow`, `onDeposit`, `onMint`, and `_accrueFees/_accruedFeeShares` — penalties are never accrued before the update. This means `lastTotalAssets` captures a value that does not yet reflect any pending penalties, resulting in a stale reading. `_accruedFeeShares` also returns this `newTotalAssets` to `_sharePrice`, propagating the staleness into share price calculations.

**Impact:**
`lastTotalAssets` consistently understates true total assets by the amount of unaccrued penalties, leading to slightly incorrect fee share calculations and stale share prices. Over time, accumulated penalties compound the inaccuracy.

**Recommended Mitigation:**
Accrue penalties before updating `lastTotalAssets` in every function that reads `_totalAssets()` and stores the result, as well as before directly accessing the value returned from `_totalAssets()` elsewhere in `AccountableYield`.

---

**[中文版本]**

**描述：**
`AccountableYield` 策略中，`lastTotalAssets` 通过读取包含 `accruedPenalties` 的 `_totalAssets()` 来更新，但在所有更新 `lastTotalAssets` 的函数（`borrow`、`onDeposit`、`onMint`、`_accrueFees/_accruedFeeShares`）中，均未在更新前先计提罚款，导致读取的值不反映待计提的罚款，产生陈旧数据。`_accruedFeeShares` 还将此 `newTotalAssets` 传递给 `_sharePrice`，进一步传播了数据的陈旧性。

**影響：**
`lastTotalAssets` 持续低估真实总资产（差额为未计提罚款），导致手续费份额计算和份额价格轻微失准，随时间累积误差加剧。

**修復建議：**
在所有读取 `_totalAssets()` 并存储结果的函数中，以及在 `AccountableYield` 其他地方直接访问该值之前，先计提罚款，再更新 `lastTotalAssets`。
