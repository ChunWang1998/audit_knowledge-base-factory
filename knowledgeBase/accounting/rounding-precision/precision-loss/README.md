# precision-loss (10)

> Issues where precision is silently lost in bonding curves, fee math, or multi-step arithmetic.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Precision Loss in Bonding Curve Calculations

**Severity:** 🟠 High  **Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
The `calculateBuyCost` function in `BondingCurveLibrary` is designed to compute the cost of purchasing a precise amount of tokens from an exponential bonding curve. The curve is intended to be continuous — meaning the price should reflect the exact number of tokens sold so far, including fractional amounts expressed in wei. However, the core computation inside `_area0` discards all sub-token precision before entering fixed-point mathematics. Specifically, `sWei / SCALE` converts a wei-precision token amount (e.g., `10.5 * 1e18`) into an integer token count (e.g., `10`) by truncating the fractional portion. The high-precision fixed-point operations then operate on this truncated integer rather than the precise wei value. This fundamentally transforms the intended smooth exponential curve into a discrete step function where the price only changes when a full integer token boundary is crossed. The price for buying when 10.01 tokens have been sold is identical to the price when 10.99 tokens have been sold.

**Impact:**
Users are consistently overcharged or undercharged depending on where their purchase falls within the step. Over time, total funds held in the contract diverge from the theoretical value predicted by the bonding curve integral, representing either a systematic drain from the protocol or from users. The mismatch grows with transaction volume.

**Recommended Mitigation:**
Modify the `_area0` function to pass the full wei-precision value into the fixed-point computation using the `divu` function from the `ABDKMath64x64` library, which performs division on unsigned integers and returns a high-precision fixed-point number. This preserves the continuous nature of the curve without requiring changes to the external interface.

---

**[中文版本]**

**描述：**
`BondingCurveLibrary` 中 `_area0` 函数在进入高精度定点运算之前，将 wei 精度的代币数量通过 `sWei / SCALE` 截断为整数。这将连续指数曲线变成了离散阶梯函数——每当累计销售量从 10.01 到 10.99 之间时，价格保持不变，只有跨越整数边界才更新。

**影響：**
用户被系统性地多收或少收费用，合约持有资金与理论曲线积分预测值持续偏离，随交易量增加积累为实质性损失。

**修復建議：**
修改 `_area0` 将完整 wei 精度值传入 `ABDKMath64x64` 的 `divu` 函数进行高精度定点除法，保留曲线的连续性。

---

## 2. `AprPairFeed::getRoundData` can return data for a different round than the specified

**Severity:** 🟡 Medium  **Source:** `cyfrin/tranches.md`

**Description:**
`AprPairFeed` stores round data in a circular buffer of size `roundsCap` (20 entries). When saving a new round, the storage index is computed as `roundId % roundsCap`, which cycles through slots 0–19 and then repeats. After 20 updates, `roundId 21` is stored in the same slot as `roundId 1`, overwriting it. When `getRoundData(roundId)` retrieves data, it uses the same modulo index without verifying that the returned data's `answeredInRound` field actually matches the requested `roundId`. A caller requesting historical data for `roundId 1` after `roundId 21` has been written will silently receive data for `roundId 21` instead — a completely different and potentially very recent data point.

**Impact:**
Any protocol component that relies on `AprPairFeed::getRoundData` for historical round verification — such as interest rate consistency checks or APR-based accounting updates — can receive silently incorrect data. This could lead to miscalculated yields, incorrect NAV splits between tranches, or accounting state corruption.

**Recommended Mitigation:**
In `getRoundData`, after reading the round from storage, add a validation check that `round.answeredInRound == roundId`. If they do not match, the historical round data has been overwritten and the function should revert with an informative error rather than returning stale data.

---

**[中文版本]**

**描述：**
`AprPairFeed` 使用大小为 20 的循环缓冲区存储轮次数据，索引通过 `roundId % roundsCap` 计算。经过 20 次更新后，新轮次会覆盖旧轮次的存储槽，但 `getRoundData` 在返回数据前不验证 `answeredInRound` 是否与请求的 `roundId` 一致，导致历史数据查询可能静默返回最新轮次的数据。

**影響：**
依赖历史轮次数据的协议组件（如利率一致性检查、APR 会计更新）可能收到错误数据，导致收益计算错误或会计状态损坏。

**修復建議：**
在 `getRoundData` 中添加 `round.answeredInRound == roundId` 验证，不匹配时回滚。

---

## 3. Decimal mismatch in `BasisTradeTailor:transferHypeToCore` causes precision loss

**Severity:** 🟡 Medium  **Source:** `cyfrin/update.md`

**Description:**
`BasisTradeTailor::transferHypeToCore` accepts a `uint256 amount` parameter that represents HYPE in HyperEVM's native 18-decimal format. When the function bridges this amount to HyperCore, the underlying bridge infrastructure automatically truncates to 8 decimal places — since HYPE on HyperCore uses only 8 decimals. The function does not validate that the provided amount is a multiple of `1e10` before passing it to the bridge. Any precision beyond the 8th decimal place is silently discarded by the bridge without any warning or revert. The function also emits an event with the full 18-decimal amount, which misrepresents the actual amount transferred and creates an off-chain accounting mismatch.

**Impact:**
Every bridge transaction silently loses the fractional amount below 8 decimal precision. While each individual loss is small (up to `~9e-10` HYPE per transaction), repeated bridging accumulates into permanent fund loss. The misleading event emission also corrupts off-chain accounting systems that rely on event data.

**Recommended Mitigation:**
Add a `require(amount % 1e10 == 0, "Amount must be multiple of 1e10 for 8-decimal precision")` validation before the bridge call. This forces callers to specify precision-aligned amounts, making any sub-8-decimal intent explicit and rejected rather than silently truncated.

---

**[中文版本]**

**描述：**
`BasisTradeTailor::transferHypeToCore` 接收 18 位精度的 HYPE 金额，但跨链桥将其截断为 8 位精度（HyperCore 上 HYPE 的精度）。函数未验证金额是否为 `1e10` 的整数倍，导致超过 8 位精度的部分被静默丢弃。事件也以完整 18 位精度记录金额，造成链下会计失真。

**影響：**
每次跨链转账都会静默丢失低于 8 位精度的金额，累积成永久性资金损失，同时误导事件数据。

**修復建議：**
在桥接调用前添加 `require(amount % 1e10 == 0)` 验证，强制调用者提供精度对齐的金额。

---

## 4. Fee refund can lose precision

**Severity:** 🟡 Medium  **Source:** `cyfrin/pledge.md`

**Description:**
`PledgeManager::refundTokens` calculates the fee to be refunded to a user when they return tokens using the formula `fee = (userPay.fee / userPay.tokensBought) * numTokens`. This performs division before multiplication — a classic precision-loss anti-pattern. Integer division in Solidity truncates fractions, so `userPay.fee / userPay.tokensBought` is computed first and rounded down, and only then multiplied by `numTokens`. The correct order is multiplication before division: `fee = userPay.fee * numTokens / userPay.tokensBought`. The difference can be significant when `userPay.fee` is not perfectly divisible by `userPay.tokensBought`, causing users to consistently receive a smaller fee refund than they are entitled to.

**Impact:**
Every fee refund is rounded down beyond what EVM integer arithmetic requires. Users systematically receive less than their pro-rata fee refund on partial token returns. The protocol retains the excess, which constitutes an unintended transfer of value from users.

**Recommended Mitigation:**
Reorder the arithmetic to multiply before dividing: `fee = userPay.fee * numTokens / userPay.tokensBought`. This eliminates the premature truncation and ensures the full precision of the fee is maintained until the final division.

---

**[中文版本]**

**描述：**
`PledgeManager::refundTokens` 使用 `fee = (userPay.fee / userPay.tokensBought) * numTokens` 计算退款费用，先除后乘导致精度过早损失。正确做法应为 `fee = userPay.fee * numTokens / userPay.tokensBought`（先乘后除），以保留最大精度。

**影響：**
每笔退款费用都被过度向下取整，用户系统性少收退款，多余部分被协议截留。

**修復建議：**
将运算顺序改为先乘后除：`fee = userPay.fee * numTokens / userPay.tokensBought`。

---

## 5. Incorrect Fee Math Allows Users to Exceed Allocation

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Seedify.fund.txt`

**Description:**
`BondingCurveWritable::_authenticateUser` enforces per-user purchase allocation limits during private sale rounds. To check whether a user's cumulative spend is within their allowed allocation, the function reconstructs their total gross (pre-fee) spending from their stored net (post-fee) amount using the formula `storedNetAmount * (1 + feeRate)`. This is mathematically incorrect. The correct way to derive gross from net when a fee was deducted is `gross = net / (1 - feeRate)`. The contract's formula always produces a value lower than the true gross, creating a systematic underestimate of how much the user has already spent. Because the allocation check compares against this underestimated gross, users can spend slightly more than their official cap across multiple transactions without triggering the `ExceedAllocation` revert.

**Impact:**
Every user in a private sale round can systematically exceed their purchase allocation by a small percentage per transaction. Multiplied across many users and transactions, this allows the total tokens sold to exceed the intended private sale cap, undermining fair distribution guarantees.

**Recommended Mitigation:**
Refactor the allocation tracking to store and compare cumulative gross (pre-fee) amounts directly rather than reconstructing gross from net. This eliminates the mathematically flawed reconstruction and the precision loss that enables the bypass.

---

**[中文版本]**

**描述：**
`BondingCurveWritable::_authenticateUser` 通过 `storedNetAmount * (1 + feeRate)` 从净额重建总额来检查分配上限。这在数学上是错误的：正确公式为 `gross = net / (1 - feeRate)`。错误公式始终低估用户已花费的实际总额，导致分配检查产生漏洞，用户可以超出其官方上限购买代币。

**影響：**
私募轮中所有用户都可以系统性地小幅超出购买上限，累积导致销售代币总量超过预设的私募上限，破坏公平分配机制。

**修復建議：**
改为直接记录和比较累计总额（税前金额），避免从净额重建总额的错误做法。

---

## 6. Insufficient fee validation in `STBL_Register::setupAsset` can cause underflow

**Severity:** 🟡 Medium  **Source:** `cyfrin/stbl.md`

**Description:**
`STBL_Register::setupAsset` and `STBL_Register::setFees` validate each fee parameter individually against its own maximum, but never check their cumulative sum. The deposit metadata computation in `STBL_MetadataLib.calculateDepositFees` calculates all three fees — `depositfeeAmount`, `haircutAmount`, and `insurancefeeAmount` — as separate percentages of `stableValueGross`. When calculating the net stable value, the contract subtracts all three fees simultaneously: `stableValueNet = stableValueGross - (depositfeeAmount + haircutAmount + insurancefeeAmount)`. If the combined fee percentages expressed in basis points exceed 10000 (100%), the sum of the three fee amounts exceeds `stableValueGross`, and the subtraction underflows.

**Impact:**
A misconfigured combination of fees where the sum of deposit fee, haircut, and insurance fee exceeds 10,000 basis points will cause all deposit operations to revert with an arithmetic underflow, permanently blocking deposits to the vault. This can result from a configuration mistake or a malicious admin setting excessive combined fees.

**Recommended Mitigation:**
Introduce a cumulative fee validation in both `STBL_Register::setupAsset` and `STBL_Register::setFees` that checks whether the sum of `depositFee + hairCut + insuranceFee` exceeds 10,000 basis points and reverts if so, preventing the invalid configuration from being set.

---

**[中文版本]**

**描述：**
`STBL_Register::setupAsset` 和 `setFees` 对每项费用参数单独验证，但未检查三项费用（存款费、haircut、保险费）的累计之和。当三项费用之和超过 10000 个基点（100%）时，存款净值计算中的减法会下溢，导致所有存款回滚。

**影響：**
费用配置错误（三项费用之和超过 100%）将导致所有存款操作永久回滚，封锁金库存款功能。

**修復建議：**
在 `setupAsset` 和 `setFees` 中添加累计费用验证，确保 `depositFee + hairCut + insuranceFee <= 10000`，否则回滚。

---

## 7. Probability overflow can bypass `MaxProbabilityExceeded` check

**Severity:** 🟡 Medium  **Source:** `cyfrin/spingame.md`

**Description:**
`Spin::_addPrizes` accumulates individual prize probabilities into `totalProbIncrease` and then into `totalProbabilities`, with both operations wrapped in `unchecked` blocks to save gas. The subsequent check `if (totalProbabilities > BASE_POINT) revert MaxProbabilityExceeded(totalProbabilities)` is intended to prevent the total from exceeding 100%. However, because the additions occur within `unchecked` blocks, an extremely large probability value (close to `type(uint256).max`) will cause the accumulation to overflow and wrap around to a small number. The post-addition `totalProbabilities` appears to be below `BASE_POINT` even though the true mathematical sum far exceeds 100%. The overflow bypass is most likely a mistake or misconfiguration risk rather than intentional, but a compromised or careless admin could trigger it.

**Impact:**
If the overflow is triggered, the prize distribution probabilities become meaningless — the game's internal probability accounting is corrupted and no longer reflects actual win chances. This could cause the game to misbehave in ways that are unpredictable to players, potentially enabling exploits of the distorted distribution.

**Recommended Mitigation:**
Remove the `unchecked` blocks from the probability accumulation operations. Solidity 0.8+ overflow protection has negligible cost in non-loop contexts and provides essential safety against this type of misconfiguration.

---

**[中文版本]**

**描述：**
`Spin::_addPrizes` 在 `unchecked` 块中累积奖品概率，绕过了 Solidity 0.8+ 的溢出保护。当概率值接近 `type(uint256).max` 时，累加溢出后的值看起来低于 `BASE_POINT`，绕过 `MaxProbabilityExceeded` 检查，导致游戏概率分布完全损坏。

**影響：**
游戏内部概率记账被破坏，实际中奖概率无法反映设定值，可能被用于扭曲奖品分配。

**修復建議：**
移除概率累积操作中的 `unchecked` 块，使用 Solidity 0.8+ 的内置溢出保护。

---

## 8. Rounding errors in boosted probability calculation can cause guaranteed wins to fail

**Severity:** 🟡 Medium  **Source:** `cyfrin/spingame.md`

**Description:**
`Spin::_fulfillRandomness` supports a boosting feature that multiplies prize probabilities for specific users. When the total boosted probabilities exceed 100%, the system adjusts the `winningThreshold` upward proportionally. However, individual prize probabilities are scaled independently in a loop, and each scaling operation introduces a floor-rounding loss (`prize.probability * userBoost / BASE_POINT`). The cumulative sum of individually rounded prize probabilities (`cumulativeProbability`) can end up slightly less than `boostedTotalProbabilities` due to the accumulated rounding errors. In a scenario where `boostedTotalProbabilities >= BASE_POINT` (the user should be guaranteed a win), the condition `winningThreshold < cumulativeProbability` can fail because `cumulativeProbability` is one or a few wei too small compared to the adjusted `winningThreshold`.

**Impact:**
A user who theoretically has a 100% chance of winning due to boosting can still lose because of accumulated rounding errors in the probability scaling. This is a rare but non-zero edge case that would be highly disruptive to the affected user and difficult to explain or compensate.

**Recommended Mitigation:**
In the final iteration of the prize loop, if `boostedTotalProbabilities >= BASE_POINT`, treat it as a guaranteed win regardless of the cumulative probability comparison. This can be implemented as an additional condition: `if (winningThreshold < cumulativeProbability || (boostedTotalProbabilities >= BASE_POINT && i == prizeLen - 1))`.

---

**[中文版本]**

**描述：**
`Spin::_fulfillRandomness` 中的加成机制对每个奖品概率独立进行定点数缩放，每次缩放都产生向下取整误差。各奖品缩放概率的累计和可能略小于 `boostedTotalProbabilities`，导致在用户理应必赢（100% 概率）的情况下，赢奖条件仍可能不满足。

**影響：**
享有 100% 加成概率的用户因舍入误差仍可能输掉游戏，这一罕见但真实存在的边缘情况严重损害用户体验。

**修復建議：**
在奖品循环的最后一次迭代中，若 `boostedTotalProbabilities >= BASE_POINT`，则无论累积概率是否满足条件，都视为必赢。

---

## 9. Rounding errors in ratio calculations can leave unaccounted tokens in the contract

**Severity:** 🟡 Medium  **Source:** `sherlockPDFTXT/Tori Finance.txt`

**Description:**
`ToriMinting::transferToCustody` distributes tokens to multiple custodian addresses based on ratio-weighted portions of the total amount. Each portion is computed as `(amount * route.ratios[i]) / 10_000`. Since integer division rounds down, the sum of all individual portions is almost always less than the total `amount` when the ratios do not perfectly divide it. The dust remainder stays locked in the contract with no mechanism to recover or redistribute it. This contrasts with `_transferCollateral`, a function in the same contract that correctly handles remainders by sending any residual balance to the last address in the route.

**Impact:**
Over time, small amounts of tokens accumulate in the contract from every `transferToCustody` call. The funds are permanently inaccessible unless an explicit recovery mechanism is added, representing a slow drain of value from the system.

**Recommended Mitigation:**
Add remainder handling to `transferToCustody` that mirrors the approach in `_transferCollateral`: after distributing all ratio-weighted portions, compute the remaining balance as `amount - totalDistributed` and send it to the last custodian address. This ensures no dust is permanently stranded in the contract.

---

**[中文版本]**

**描述：**
`ToriMinting::transferToCustody` 按比例分配代币给多个托管地址，每份计算为 `(amount * ratios[i]) / 10_000`。整除向下取整导致各份额之和小于总量，剩余的"尘埃"滞留在合约中无法回收。同合约的 `_transferCollateral` 函数通过将余额发送给最后一个地址的方式正确处理了此问题。

**影響：**
每次 `transferToCustody` 调用都在合约中积累少量无法取回的代币，长期积累成实质性损失。

**修復建議：**
参照 `_transferCollateral` 的做法，在分配所有份额后，将剩余余额发送给最后一个托管地址。

---

## 10. Unbounded weight scale factor causes precision loss in stake conversion, potentially leading to loss of operator funds

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware` uses a `WEIGHT_SCALE_FACTOR` to convert between the 256-bit stake amounts stored on HyperEVM and the 64-bit validator weights required by the Avalanche P-Chain. The conversion `stakeToWeight()` computes `weight = stakeAmount / scaleFactor`, and `weightToStake()` computes the inverse `recoveredStake = weight * scaleFactor`. If `WEIGHT_SCALE_FACTOR` is set too high relative to actual stake amounts, integer division truncates the weight to zero — meaning the validator is registered with zero weight on the P-Chain even though stakers have deposited real value. There is no constructor validation enforcing a reasonable maximum bound on this scale factor.

**Impact:**
With an inappropriately large `WEIGHT_SCALE_FACTOR`, validators can be registered with zero P-Chain weight, rendering them invisible to the Avalanche consensus mechanism while operator funds are still locked in the vault. Operators suffer fund loss while receiving no validation participation.

**Recommended Mitigation:**
Implement reasonable maximum bounds for `WEIGHT_SCALE_FACTOR` in the constructor, derived from the minimum expected stake amount and the maximum representable 64-bit weight. Revert deployment if the configured scale factor would truncate meaningful stake amounts to zero.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware` 使用 `WEIGHT_SCALE_FACTOR` 将 256 位质押量转换为 64 位验证者权重。若 `WEIGHT_SCALE_FACTOR` 设置过大，整除会将权重截断为零，导致验证者以零权重注册到 P 链，但质押资金仍被锁定在金库中。构造函数中没有对缩放因子的上限进行验证。

**影響：**
不当的缩放因子导致验证者以零权重注册，无法参与共识，而运营者资金却被锁定。运营者损失资金但获得零验证收益。

**修復建議：**
在构造函数中根据最小预期质押量和最大 64 位权重为 `WEIGHT_SCALE_FACTOR` 设置合理上限，超出范围时回滚部署。
