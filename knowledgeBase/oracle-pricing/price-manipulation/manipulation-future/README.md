# manipulation-future (3)

> Issues where future-epoch caches or unbounded values can be manipulated to skew rewards or prices.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Future epoch cache manipulation via calcAndCacheStakes allows reward manipulation

**Severity:** 🔴 Critical
**Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware::calcAndCacheStakes` lacks epoch validation, allowing any caller to cache stake values for future epochs. The function does not verify that the provided epoch is not in the future before writing to `operatorStakeCache` and setting the `totalStakeCached` flag. Once the flag is set for a given epoch and asset class, every subsequent call to `getOperatorStake` for that epoch returns the stale cached value and ignores any deposits or withdrawals that occur between the caching moment and the epoch's actual start. Because `calcAndCacheStakes` queries current checkpoint data using `upperLookupRecent`, which returns the latest available values for future timestamps, an attacker can lock in artificially high stake figures while they still have large deposits, then reduce their stake before the epoch arrives.

**Impact:**
Attackers can inflate their reward shares by locking in high stake values before their actual stakes decrease; all subsequent deposits and withdrawals are ignored for the cached epoch. Additionally, the `forceUpdateNodes` mechanism can be compromised: critical node rebalancing operations can be incorrectly skipped, leaving the system in an inconsistent state and potentially causing bad debt or loss of staking rewards for honest operators.

**Recommended Mitigation:**
Add epoch validation inside `calcAndCacheStakes` that reverts if the requested epoch is strictly greater than `getCurrentEpoch()`. This ensures that only current or past epochs can have their stakes cached, eliminating the window for future-epoch manipulation.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware::calcAndCacheStakes` 缺少对 epoch 参数的合法性校验，任何调用者都可以为未来 epoch 缓存权益数据。一旦 `totalStakeCached` 标志被设置，该 epoch 后续所有对 `getOperatorStake` 的调用都会直接返回缓存的过期数值，忽略之间发生的所有存款和取款。攻击者可以在仍持有大量质押时提前为未来 epoch 写入高额权益，之后再减少质押，以此锁定虚高的奖励份额。

**影響：**
攻击者可通过锁定高权益值来虚增奖励份额；`forceUpdateNodes` 节点再平衡机制也可能因缓存数据错误而被跳过，导致系统状态不一致，诚实运营商损失奖励。

**修復建議：**
在 `calcAndCacheStakes` 函数内部增加 epoch 验证逻辑，当请求的 epoch 严格大于 `getCurrentEpoch()` 时回滚交易，确保只有当前或过去的 epoch 可以被缓存。

---

## 2. Hard-coded slippage in pUSDeDepositor::deposit_viaSwap can lead to denial of service

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
`pUSDeDepositor::deposit_viaSwap` uses a hard-coded slippage tolerance when executing the underlying DEX swap. Hard-coded slippage values are a well-known attack vector: during periods of high volatility or low liquidity, the on-chain price can deviate beyond the fixed tolerance, causing every call to `deposit_viaSwap` to revert. Unlike dynamic slippage that is computed off-chain and passed as an argument, a static value cannot adapt to market conditions. In extreme cases, funds committed to the swap path may become temporarily locked if the function is the only redemption route.

**Impact:**
Users and integrators calling `deposit_viaSwap` may face a sustained denial of service during volatile market periods. In dramatic scenarios, user funds can be temporarily locked if the swap consistently exceeds the hardcoded tolerance and no alternative deposit path exists.

**Recommended Mitigation:**
Remove the hard-coded slippage and instead accept a caller-supplied slippage parameter that is computed off-chain based on current market conditions. This allows individual callers to choose an appropriate tolerance for each transaction.

---

**[中文版本]**

**描述：**
`pUSDeDepositor::deposit_viaSwap` 在执行底层 DEX 兑换时使用硬编码的滑点容差。在市场波动剧烈或流动性不足期间，链上价格可能偏离固定阈值，导致每次调用都会回滚。与动态滑点不同，静态值无法适应市场变化，极端情况下可能导致用户资金暂时锁定。

**影響：**
市场波动期间调用 `deposit_viaSwap` 的用户和集成方将面临持续的拒绝服务，资金可能因兑换持续超出硬编码容差而暂时被锁定。

**修復建議：**
移除硬编码的滑点参数，改为接受调用者传入的、根据当前市场状况在链下计算的滑点值，让每笔交易的调用者自主选择合适的容差。

---

## 3. User can set their answer's probability value to uint16.max, manipulating result.probabilityAverage in their favor

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
In `SPBinaryPrompt.sol`, users commit a hashed answer and probability value during the commit phase. When revealing via `revealReaction`, the function decodes the probability as a `uint16` but does not validate that it falls within the expected range of 0 to 10,000 (representing 0–100%). The uncapped probability is added directly to `result.probabilityTotal`, and `result.probabilityAverage` is recalculated as `probabilityTotal / respondents`. A malicious user can commit with `probability = type(uint16).max` (65,535), which is far above the 10,000 maximum used in score calculations, inflating the `probabilityAverage` for all participants and skewing the scoring distribution.

**Impact:**
A malicious user can manipulate the `probabilityAverage` upward, distorting the score calculation for all other participants and securing a disproportionately higher ranking among winners. Honest participants who submitted valid probability values are penalized by the corrupted average.

**Recommended Mitigation:**
Add a cap inside `revealReaction` that clamps the decoded probability to the `PRECISION` constant (10,000) before using it in any aggregate calculation, preventing any single user from inflating the shared average.

---

**[中文版本]**

**描述：**
`SPBinaryPrompt.sol` 中，用户在揭示阶段通过 `revealReaction` 提交概率值，但合约未检查该值是否在 0 至 10,000 的有效范围内。恶意用户可以提交 `uint16.max`（65,535），直接加入 `probabilityTotal` 后重新计算 `probabilityAverage`，导致所有参与者的共享平均值被严重虚高。

**影響：**
恶意用户可操纵 `probabilityAverage`，使评分分布扭曲，自己获得不成比例的高排名，诚实提交有效概率值的用户因此受损。

**修復建議：**
在 `revealReaction` 中，在将解码后的概率用于任何聚合计算之前，将其截断至 `PRECISION`（10,000），防止单个用户虚高共享平均值。
