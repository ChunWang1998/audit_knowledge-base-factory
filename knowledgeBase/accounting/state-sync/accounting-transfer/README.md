# accounting-transfer (5)

> Issues where transfer operations caused accounting desynchronisation, including fee-on-transfer and rebasing token edge cases.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. `AccountableAsyncRedeemVault::fulfillCancelRedeemRequest` can de-sync request data causing permanent DOS for queue processing

**Severity:** 🔴 Critical  **Source:** `cyfrin/accountable.md`

**Description:**
`fulfillCancelRedeemRequest(controller)` is designed to finalize a cancellation of a pending redeem request. The function first calls `_fulfillCancelRedeemRequest(_requestIds[controller], controller)`, which sets `state.pendingRedeemRequest = 0` as part of finalizing the cancellation. It then calls `_reduce(controller, _vaultStates[controller].pendingRedeemRequest)` to update the queue state and `totalQueuedShares`. Because `pendingRedeemRequest` has already been zeroed by the first call, `_reduce` is always invoked with zero shares. The `_reduce` function does not revert on a zero-share input, but it still writes to the request struct. This corrupts the data: the request still exists in the queue with its original non-zero `request.shares` value and a `_queue.nextRequestID` pointing into a valid queue range, but `state.pendingRedeemRequest` is now zero — an inconsistent state.

When the queue's batch processing subsequently reaches this request via `processUpToShares()`, it calls `_fulfillRedeemRequest()`, which checks `if (state.pendingRedeemRequest == 0) revert NoRedeemRequest()`. Since `pendingRedeemRequest` is zero, the revert fires, permanently blocking queue processing for all subsequent requests that come after this corrupted entry. The queue is irrecoverably jammed.

**Impact:**
Any invocation of `fulfillCancelRedeemRequest` on a vault that offers async cancellation processing permanently corrupts the withdrawal queue. The queue becomes stuck: the corrupted entry causes every subsequent `processUpToShares` call to revert, blocking all future withdrawals for all users in the queue. There is no recovery path without a contract upgrade.

**Recommended Mitigation:**
Capture `state.pendingRedeemRequest` into a local variable before calling `_fulfillCancelRedeemRequest`, then pass that saved value to `_reduce`:

```
uint256 pendingShares = _vaultStates[controller].pendingRedeemRequest;
_fulfillCancelRedeemRequest(_requestIds[controller], controller);
_reduce(controller, pendingShares);
```

This ensures `_reduce` receives the correct pre-zeroed share count regardless of the order of state updates.

---

**[中文版本]**

**描述：**
`fulfillCancelRedeemRequest` 先调用 `_fulfillCancelRedeemRequest`（将 `pendingRedeemRequest` 清零），再调用 `_reduce(controller, _vaultStates[controller].pendingRedeemRequest)`。由于此时 `pendingRedeemRequest` 已被清零，`_reduce` 总是以零份额调用。`_reduce` 不在零份额时回滚，但仍写入请求结构，造成请求状态不一致：请求仍存在于队列中（含原始份额数据），但 `pendingRedeemRequest` 为零。后续批量处理到达此条目时，`_fulfillRedeemRequest` 检查到 `pendingRedeemRequest == 0` 便回滚，永久阻塞队列处理。

**影響：**
调用此函数后，提款队列被永久损坏。所有后续用户的提款请求无法被处理，无法在不升级合约的情况下恢复，属于关键级别的 DoS 漏洞。

**修復建議：**
在调用 `_fulfillCancelRedeemRequest` 前将 `pendingRedeemRequest` 保存到局部变量，再将该保存值传给 `_reduce`，确保 `_reduce` 收到正确的份额数量。

---

## 2. DoS on stake accounting functions by bloating `operatorNodesArray` with irremovable nodes

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
When a node is removed and finalized via `completeValidatorRemoval()` within the same epoch as its registration (before `calcAndCacheNodeStakeForAllOperators` runs for that epoch), an inconsistent state arises. `completeValidatorRemoval()` deletes the `_registeredValidators[validator.nodeID]` mapping entry in `BalancerValidatorManager`. From that point on, querying `registeredValidators(abi.encodePacked(uint160(uint256(nodeId))))` returns `bytes32(0)`. In the next epoch's call to `_calcAndCacheNodeStakeForOperatorAtEpoch`, the code uses this `valID == bytes32(0)`, so neither `nodePendingRemoval[bytes32(0)]` nor `nodePendingUpdate[bytes32(0)]` is true — the removal branch is skipped, and the stale `nodeId` remains permanently stuck in `operatorNodesArray`.

An operator can deliberately repeat this pattern — register a node, complete its removal in the same epoch, repeat — to inflate `operatorNodesArray` with arbitrarily many ghost entries. All O(n) loops over this array (`forceUpdateNodes`, `_calcAndCacheNodeStakeForAllOperators`, various view helpers) grow without bound, eventually exhausting block gas and causing permanent DoS for that operator's stake accounting and all global maintenance functions that iterate over all operators.

**Impact:**
Oversized `operatorNodesArray` causes epoch maintenance and stake rebalance functions to revert out-of-gas. Stake updates, slashing, reward distribution, and emergency withdrawals dependent on these functions can all be frozen for the affected operator and, indirectly, for protocol-wide maintenance.

**Recommended Mitigation:**
Track pending removals by `nodeId` rather than by `validationID`, or store an auxiliary mapping `nodeId => validationID` before the mapping entry is deleted so the middleware can still correlate and clean up phantom nodes in subsequent epochs.

---

**[中文版本]**

**描述：**
当节点在同一纪元内被注册并完成移除（在 `calcAndCacheNodeStakeForAllOperators` 执行前），`completeValidatorRemoval` 删除 `_registeredValidators` 映射条目后，`valID` 变为 `bytes32(0)`，下一纪元的清理分支因条件不满足而跳过，节点永久滞留在 `operatorNodesArray` 中。攻击者可重复此操作，无限膨胀数组，最终使所有 O(n) 循环因超出区块 gas 上限而 DoS。

**影響：**
`operatorNodesArray` 过度膨胀导致纪元维护和质押再平衡函数耗尽 gas，质押更新、惩没、奖励分配和紧急提款均可能被冻结。

**修復建議：**
通过 `nodeId` 而非 `validationID` 追踪待移除节点，或在映射条目删除前维护 `nodeId => validationID` 辅助映射，使中间件在后续纪元仍能清理幽灵节点。

---

## 3. Fee-On-Transfer And Rebasing Tokens Break Accounting And Can Cause Loss Of Funds

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/Fabstir.txt`

**Description:**
Multiple contracts in the Fabstir compute marketplace — `NodeRegistryWithModelsUpgradeable`, `JobMarketplaceWithModelsUpgradeable`, `ModelRegistryUpgradeable`, and `HostEarningsUpgradeable` — accept ERC-20 token deposits using `safeTransferFrom`. After each transfer, internal accounting records the full nominal amount specified by the caller. For fee-on-transfer tokens, the actual amount received by the contract is less than the nominal amount (a fee is deducted by the token contract during transfer). For rebasing tokens, holder balances can change passively without any transfer event. In both cases, the contract's internal accounting records a higher balance than the contract actually holds on-chain. Over time, when the contract attempts to pay out based on these inflated internal balances, the transfers fail because the contract does not hold the required tokens.

**Impact:**
Node stake slashing, session payment settlements, vote withdrawals, and host earnings distributions can all fail or revert when the contract's actual token balance falls below what internal accounting records. Funds belonging to other users effectively subsidize the accounting inflation, and some users may find their withdrawals permanently blocked.

**Recommended Mitigation:**
Either explicitly disallow fee-on-transfer and rebasing tokens by documenting and enforcing token restrictions, or implement delta accounting: record the token balance before each `safeTransferFrom`, execute the transfer, compute the received amount as `balanceAfter - balanceBefore`, and use that actual received amount (not the nominal amount) for all internal balance updates.

---

**[中文版本]**

**描述：**
Fabstir 计算市场中多个合约在接受 ERC-20 代币存款时，使用 `safeTransferFrom` 后直接以调用者指定的名义金额更新内部会计，未验证实际收到金额。对于转账税代币，合约实际收到金额少于名义金额；对于 rebase 代币，余额可被动改变。内部会计持续记录高于实际余额的数字，导致后续支付时余额不足。

**影響：**
节点质押惩没、会话支付结算、投票取回和主机收益分配均可能因实际余额不足而失败，其他用户的资金被用于填补会计膨胀，部分用户提款被永久阻塞。

**修復建議：**
明确禁止转账税和 rebase 代币，或实施增量会计：在每次 `safeTransferFrom` 前后计算余额差值，以实际收到金额更新内部会计。

---

## 4. Fee-on-Transfer / Rebasing Tokens Break Accounting

**Severity:** 🟡 Medium  **Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
`BullBit::Pool::depositToken` accepts any ERC-20 token from users by calling `IERC20(token).safeTransferFrom(msg.sender, address(this), amount)` and then crediting the user's internal balance with the full `amount` parameter: `balances[msg.sender][token] += amount`. For fee-on-transfer tokens, the pool receives less than `amount` due to the transfer fee deducted by the token contract. For deflationary tokens (which burn a portion of each transfer), the same shortfall occurs. The contract records `amount` in internal accounting but only holds `amount - fee` in its real balance. When multiple users deposit and later attempt to withdraw, the pool's actual token holdings cannot satisfy all recorded balances, and late withdrawers will find their withdrawals failing or reverting.

**Impact:**
Internal user balances are inflated relative to the pool's actual token holdings. On-chain withdrawals, forced withdrawals, and emergency exit flows may revert when the pool attempts to transfer tokens it does not hold, effectively causing loss of funds for the last users to withdraw from an affected token pool.

**Recommended Mitigation:**
Implement delta accounting: capture the pool's token balance before `safeTransferFrom`, execute the transfer, compute `received = balanceAfter - balanceBefore`, and credit `balances[msg.sender][token] += received`. This ensures the internal accounting always reflects the actual amount held, regardless of the token's transfer behavior.

---

**[中文版本]**

**描述：**
`BullBit::Pool::depositToken` 以名义金额 `amount` 更新用户内部余额，但转账税代币或通缩代币在转账时会扣除费用，合约实际收到的金额少于 `amount`。随时间推移，所有内部余额之和超过合约实际持有量，最后提款的用户会发现余额不足而失败。

**影響：**
用户内部余额虚高，链上提款、强制提款和紧急退出流程可能因合约实际持有量不足而回滚，最后提款的用户实质损失资金。

**修復建議：**
实施增量会计：在 `safeTransferFrom` 前后测量余额差值，以实际收到金额（`balanceAfter - balanceBefore`）更新内部余额。

---

## 5. Inconsistent stake calculation due to mutable `vaultManager` reference in `AvalancheL1Middleware`

**Severity:** 🟡 Medium  **Source:** `cyfrin/core.md`

**Description:**
`AvalancheL1Middleware` allows the `vaultManager` reference to be updated via `setVaultManager()`. However, the vault registry is stateful: vaults registered in the original `vaultManager` are not migrated to the new one, and re-registering them in the new manager resets their `enabledTime` and `disabledTime` metadata. The core stake calculation in `getOperatorStake()` depends on `_wasActiveAt()`, which checks whether a vault was active at a specific historical epoch timestamp using these time fields. After replacing the `vaultManager`, previously valid historical queries return wrong results: vaults that were active in past epochs appear inactive because their time metadata has been reset. This silently corrupts all stake calculations, reward attributions, and slashing computations for historical epochs.

**Impact:**
After a `vaultManager` replacement, `getOperatorStake()` returns incorrect values for any epoch prior to the replacement. Stake tracking, reward distribution, and slashing logic that relies on historical epoch data become unreliable, potentially causing operators to lose rewards or avoid slashing they should have been subject to.

**Recommended Mitigation:**
Remove the ability to arbitrarily update the `vaultManager` once the middleware has been initialized. If migration is genuinely needed, implement a dedicated migration path that preserves all historical time metadata and vault registrations, or freeze historical queries at the time of migration.

---

**[中文版本]**

**描述：**
`AvalancheL1Middleware` 允许通过 `setVaultManager()` 更新 `vaultManager` 引用。原 `vaultManager` 中注册的金库不会迁移到新实例，重新注册会重置 `enabledTime` 和 `disabledTime`。`getOperatorStake()` 通过 `_wasActiveAt()` 检查金库在特定历史纪元是否活跃，切换 `vaultManager` 后，历史纪元的时间元数据被重置，导致原本活跃的金库在历史查询中显示为不活跃，所有历史质押计算结果被静默损坏。

**影響：**
`vaultManager` 切换后，所有替换前纪元的 `getOperatorStake()` 返回错误结果，质押追踪、奖励分配和惩没逻辑基于不可靠的历史数据，运营者可能损失奖励或规避应受的惩没。

**修復建議：**
禁止在中间件初始化后任意更新 `vaultManager`。若确实需要迁移，实施保留所有历史时间元数据和金库注册信息的专用迁移路径，或在迁移时冻结历史查询。
