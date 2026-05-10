# validation-weak (3)

> Issues where structural or input validation was weak, allowing edge cases to bypass intended constraints.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Consider removing redundant zero address check from createYieldStrategy

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`createYieldStrategy` deploys instances of the `AccountableYield` strategy using OpenZeppelin's `Create2.deploy`. After the deployment call, it checks if the returned `strategyProxy` address is `address(0)` and reverts with `FailedDeployment` if so. However, OpenZeppelin's `Create2.deploy` already performs this identical check internally — it reverts with `Create2FailedDeployment` if the deployed address is zero. The post-deployment zero-address check in `createYieldStrategy` is therefore unreachable: if `Create2.deploy` succeeds, the returned address will never be zero, and if it fails, `Create2.deploy` will have already reverted before `createYieldStrategy` has a chance to run its check.

**Impact:**
The redundant check adds minor gas overhead and dead code to `createYieldStrategy`. More importantly, the dual error paths (`FailedDeployment` from the outer check vs `Create2FailedDeployment` from the library) can confuse developers and auditors about which error is actually thrown on deployment failure.

**Recommended Mitigation:**
Remove the `if (strategyProxy == address(0)) revert FailedDeployment(ZERO_LOAN_PROXY_ADDRESS);` check from `createYieldStrategy`, relying entirely on `Create2.deploy`'s built-in revert for deployment failures.

---

**[中文版本]**

**描述：**
`createYieldStrategy` 使用 OpenZeppelin 的 `Create2.deploy` 部署 `AccountableYield` 策略实例。部署调用后，它检查返回的 `strategyProxy` 地址是否为 `address(0)`，如果是则以 `FailedDeployment` 回滚。然而，OpenZeppelin 的 `Create2.deploy` 已在内部执行了相同的检查——如果部署地址为零，它会以 `Create2FailedDeployment` 回滚。因此，`createYieldStrategy` 中的部署后零地址检查是无法到达的：如果 `Create2.deploy` 成功，返回地址永远不会是零；如果失败，`Create2.deploy` 已经在 `createYieldStrategy` 有机会运行其检查之前回滚了。

**影響：**
冗余检查为 `createYieldStrategy` 增加了少量 gas 开销和死代码。更重要的是，双重错误路径（外部检查的 `FailedDeployment` vs 库的 `Create2FailedDeployment`）可能使开发者和审计人员对部署失败时实际抛出哪个错误感到困惑。

**修復建議：**
从 `createYieldStrategy` 中移除 `if (strategyProxy == address(0)) revert FailedDeployment(ZERO_LOAN_PROXY_ADDRESS);` 检查，完全依赖 `Create2.deploy` 内置的部署失败回滚。

---

## 2. No validation on reactionDeadline allows multiple griefing scenarios

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
When a game creator creates a game, they commit to an array of `promptHash` values that are later revealed as `Prompt` structs. Each `Prompt` contains a `reactionDeadline` field that controls how long players have to submit answers after a question is revealed. The `reactionDeadline` value is never validated: a game creator can set it to `0` (causing all answer commitments to immediately fail since `revealedAt + 0 < block.timestamp` always) or to `type(uint256).max` (permanently locking the answering window open). Additionally, `media` and `choices` arrays within the prompt are never validated to have matching lengths, which can cause undefined rendering behavior.

**Impact:**
A game creator can set `reactionDeadline = 0` to prevent all users from submitting answers while still being able to conclude the game and collect all entry fees. Setting `reactionDeadline = type(uint256).max` keeps the window permanently open, allowing creators to manipulate game timing. In both cases, users lose their entry fees without being able to participate meaningfully.

**Recommended Mitigation:**
In `revealQuestion`, validate that `reactionDeadline` is within an admin-controlled minimum and maximum range, and that `reactionDeadline` does not extend past the game's `endTime`. Also validate that `media.length == choices.length`.

---

**[中文版本]**

**描述：**
当游戏创建者创建游戏时，他们承诺一组 `promptHash` 值，这些值后来作为 `Prompt` 结构体被揭示。每个 `Prompt` 包含一个 `reactionDeadline` 字段，控制玩家在问题揭示后有多长时间提交答案。`reactionDeadline` 值从未被验证：游戏创建者可以将其设置为 `0`（导致所有答案提交立即失败，因为 `revealedAt + 0 < block.timestamp` 始终成立）或 `type(uint256).max`（永久保持回答窗口开放）。此外，提示中的 `media` 和 `choices` 数组从未被验证具有匹配的长度，可能导致未定义的渲染行为。

**影響：**
游戏创建者可以将 `reactionDeadline = 0` 以阻止所有用户提交答案，同时仍能结束游戏并收取所有入场费。将 `reactionDeadline = type(uint256).max` 使窗口永久开放，允许创建者操纵游戏时序。在两种情况下，用户都在无法有意义参与的情况下损失了入场费。

**修復建議：**
在 `revealQuestion` 中，验证 `reactionDeadline` 在管理员控制的最小值和最大值范围内，且 `reactionDeadline` 不超过游戏的 `endTime`。同时验证 `media.length == choices.length`。

---

## 3. Weak structural validation of connectionRequest from deeplink

**Severity:** 🟡 Medium
**Source:** `cyfrin/connect.md`

**Description:**
`ConnectionRequest` objects parsed from deeplinks in the MetaMask mobile client undergo minimal structural validation. The `mode` field is only checked as `typeof string` without validating against the allowed enum values `["trusted", "untrusted"]`. The `id` field is checked as `typeof string` without UUID format validation. The `publicKeyB64` field is checked for presence but without format or length validation. The `channel` field is typed but not validated against the expected `handshake:{uuid}` format. The `expiresAt` field is checked as `typeof number` but without `isNaN` guard or future-timestamp validation. String fields like `dapp.name` and `dapp.url` have no length cap. An invalid `mode` value (e.g., `"invalid"`) silently defaults to the `UntrustedConnectionHandler` path rather than being rejected outright.

**Impact:**
Malformed but structurally valid connection requests proceed into the full connection flow. An adversary could supply an arbitrarily long `dapp.name` (megabytes) causing UI rendering issues. `NaN` values in `expiresAt` bypass expiry checks. Invalid `mode` values enter the system without explicit rejection, increasing the attack surface and potentially causing unexpected behavior in future protocol changes.

**Recommended Mitigation:**
Add explicit validation: check `mode` against `['trusted', 'untrusted']`; add UUID format validation for `id` and `channel`; add `isNaN` guard and future-timestamp check for `expiresAt`; add `publicKeyB64` format and length validation; enforce maximum length bounds (e.g., 256 characters) on all string fields.

---

**[中文版本]**

**描述：**
从 MetaMask 移动客户端深度链接解析的 `ConnectionRequest` 对象仅经过最少的结构验证。`mode` 字段仅被检查为 `typeof string`，而未对允许的枚举值 `["trusted", "untrusted"]` 进行验证。`id` 字段被检查为 `typeof string`，没有 UUID 格式验证。`publicKeyB64` 字段被检查是否存在，但没有格式或长度验证。`channel` 字段有类型检查但未对预期的 `handshake:{uuid}` 格式进行验证。`expiresAt` 字段被检查为 `typeof number`，但没有 `isNaN` 保护或未来时间戳验证。`dapp.name` 和 `dapp.url` 等字符串字段没有长度上限。无效的 `mode` 值（例如 `"invalid"`）默默地默认为 `UntrustedConnectionHandler` 路径，而非直接被拒绝。

**影響：**
格式错误但结构上有效的连接请求会进入完整的连接流程。攻击者可以提供任意长的 `dapp.name`（数兆字节），导致 UI 渲染问题。`expiresAt` 中的 `NaN` 值绕过了过期检查。无效的 `mode` 值在没有明确拒绝的情况下进入系统，增加了攻击面，并可能在未来的协议变更中造成意外行为。

**修復建議：**
添加显式验证：对照 `['trusted', 'untrusted']` 检查 `mode`；为 `id` 和 `channel` 添加 UUID 格式验证；为 `expiresAt` 添加 `isNaN` 保护和未来时间戳检查；添加 `publicKeyB64` 格式和长度验证；对所有字符串字段强制执行最大长度限制（例如 256 个字符）。
