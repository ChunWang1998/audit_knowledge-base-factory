# parameter-validation (5)

> Issues where governance parameters lacked validation, allowing zero addresses, incorrect inputs, or missing ownership checks.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Missing ownership validation of positions

**Severity:** 🟠 High
**Source:** `sherlockPDFTXT/Vesu.txt`

**Description:**
The migrator contract does not verify whether the caller is the actual owner of the position being migrated. The function `migrate_position_from_v2` accepts a `from_user` parameter but never checks that `get_contract_address() == from_user`. If a user previously delegated the migrator contract to manage their V1/V2 position, an attacker can exploit this oversight to trigger a migration on behalf of any delegating user without that user's consent, passing an arbitrary victim address as `from_user` and having the flash loan mechanism execute against the victim's position.

**Impact:**
Any attacker can steal previously delegated user positions by triggering unauthorized migrations. Users who granted delegation to the migrator and did not subsequently revoke it remain permanently vulnerable to having their positions migrated and their assets drained to the attacker.

**Recommended Mitigation:**
Add a strict ownership assertion inside the migration function to ensure that the operation can only be initiated by the actual position owner. Additionally, consider revoking migrator permissions automatically after a successful migration or enforcing explicit re-authorization to minimize the attack surface for future calls.

---

**[中文版本]**

**描述：**
迁移合约（migrator）在执行仓位迁移时，未验证调用者是否为仓位的实际所有者。`migrate_position_from_v2` 接受 `from_user` 参数，却没有检查 `get_contract_address() == from_user`。若用户曾将迁移合约委托（delegate）管理其 V1/V2 仓位，攻击者可传入任意受害者地址作为 `from_user`，借助闪电贷机制在无授权的情况下对受害者的仓位执行迁移。

**影響：**
攻击者可在未经授权的情况下迁移任何曾经委托过迁移合约的用户仓位，导致用户资产被窃取。所有尚未撤销委托授权的用户都面临持续风险。

**修復建議：**
在迁移函数内部添加严格的所有权断言，确保只有仓位实际所有者才能发起迁移。同时，建议在迁移成功后自动撤销迁移合约权限，或强制要求用户显式重新授权，以减少后续攻击面。

---

## 2. SablierBob::_unstakeFullAmountViaAdapter should take vault.adapter as input parameter

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierBob::_unstakeFullAmountViaAdapter` performs a redundant storage read of `vault.adapter` when both of its callers already load this value from storage before invoking the function. There is also a secondary redundancy where `SablierBob::_unstakeFullAmountViaAdapter` calls `SablierLidoAdapter::getTotalYieldBearingTokenBalance` to read `_vaultTotalWstETH[vaultId]`, and then `SablierLidoAdapter::unstakeFullAmount` immediately performs an identical storage read of the same variable. Both inefficiencies can be eliminated by passing the already-loaded `vault.adapter` value as a parameter and having `unstakeFullAmount` return `totalWstETH` directly.

**Impact:**
The unnecessary storage reads result in additional gas consumption on every call to `_unstakeFullAmountViaAdapter`. The pattern also reduces code clarity, since the function internally sources a value that callers already possess, creating an implicit dependency on the storage state rather than the passed context.

**Recommended Mitigation:**
Update `SablierBob::_unstakeFullAmountViaAdapter` to accept `vault.adapter` as an explicit input parameter, eliminating the internal storage read. Additionally, modify `SablierLidoAdapter::unstakeFullAmount` to return `totalWstETH` alongside `amountReceivedFromUnstaking`, so the caller can eliminate the separate `getTotalYieldBearingTokenBalance` call entirely.

---

**[中文版本]**

**描述：**
`SablierBob::_unstakeFullAmountViaAdapter` 的两个调用者在调用前都已从存储中加载了 `vault.adapter`，但函数内部仍重复读取该存储值，造成冗余。此外，函数还额外调用 `SablierLidoAdapter::getTotalYieldBearingTokenBalance` 读取 `_vaultTotalWstETH[vaultId]`，而紧接其后的 `SablierLidoAdapter::unstakeFullAmount` 又执行了完全相同的存储读取。两处冗余均可通过将已加载的值作为参数传入来消除。

**影響：**
每次调用 `_unstakeFullAmountViaAdapter` 时都会消耗多余的 gas，且代码逻辑不够清晰，函数内部依赖存储状态而非传入的上下文参数。

**修復建議：**
将 `vault.adapter` 作为显式输入参数传入 `_unstakeFullAmountViaAdapter`，消除内部存储读取。同时让 `SablierLidoAdapter::unstakeFullAmount` 同时返回 `totalWstETH` 和 `amountReceivedFromUnstaking`，从而去掉多余的 `getTotalYieldBearingTokenBalance` 调用。

---

## 3. Unnecessary _msgSender() call in _resolveVaultId when caller parameter is available

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
In `RWASegWrap::_resolveVaultId()`, the function receives a `caller` parameter representing the address for which a vault ID should be resolved. However, when the vault does not yet exist and `_addVault()` is called to register the newly deployed vault, the function uses `_msgSender()` instead of the provided `caller` parameter. This creates an unnecessary external call and introduces a potential inconsistency, since `_msgSender()` and `caller` should represent the same address but are sourced differently. If any meta-transaction or context layer causes them to diverge, the vault would be registered under a different owner than intended.

**Impact:**
The unnecessary `_msgSender()` call consumes additional gas and reduces code clarity. In contexts where `_msgSender()` and `caller` could differ, the vault may be registered under an unintended address, creating an ownership mismatch that could break downstream logic relying on the vault-to-owner mapping.

**Recommended Mitigation:**
Replace the `_msgSender()` argument in the `_addVault()` call with the `caller` parameter that is already available in the function signature.

---

**[中文版本]**

**描述：**
`RWASegWrap::_resolveVaultId()` 接收代表目标地址的 `caller` 参数，但在调用 `_addVault()` 注册新建 vault 时，却使用 `_msgSender()` 而非已有的 `caller` 参数。这造成了一次不必要的函数调用，并在存在 meta-transaction 或上下文层的情况下可能导致两个值不一致，从而将 vault 注册到错误的所有者名下。

**影響：**
多余的 `_msgSender()` 调用消耗额外 gas，降低代码清晰度。在 `_msgSender()` 与 `caller` 可能不同的场景下，vault 可能被注册到非预期地址，破坏依赖 vault 所有者映射的下游逻辑。

**修復建議：**
将 `_addVault()` 调用中的 `_msgSender()` 替换为函数签名中已有的 `caller` 参数。

---

## 4. Unused parameter in address validation modifier SecuritizeOffRamp::addressNonZero

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
The `addressNonZero` modifier in `SecuritizeOffRamp` accepts a `string memory parameter` argument intended to provide context about which address is being validated, but this string is never used in the modifier's body or error handling. The modifier is invoked with descriptive strings such as "asset", "navProvider", "feeManager", and "liquidityProvider", yet none of this information is surfaced in the revert reason — the modifier unconditionally emits `NonZeroAddressError()` without including the parameter name. This contrasts with other contracts in the codebase that correctly implement address validation without unnecessary parameters.

**Impact:**
The unused parameter creates inconsistent code patterns across the codebase, increases calldata size and gas cost slightly on every invocation, and represents a missed opportunity to provide meaningful error context when address validation fails, making debugging harder.

**Recommended Mitigation:**
Remove the unused `string memory parameter` argument from the `addressNonZero` modifier and update all call sites to omit the string parameter.

---

**[中文版本]**

**描述：**
`SecuritizeOffRamp` 的 `addressNonZero` 修饰器接受一个 `string memory parameter` 参数，原意是提供被校验地址的上下文信息，但该字符串在修饰器逻辑和错误处理中从未被使用。修饰器调用时传入了 "asset"、"navProvider" 等描述字符串，但最终的 revert 信息 `NonZeroAddressError()` 并不包含任何参数名称，信息完全被丢弃。

**影響：**
未使用的参数导致代码风格不一致，每次调用略微增加 calldata 大小和 gas 消耗，同时错过了在地址校验失败时提供有意义错误上下文的机会，增加了调试难度。

**修復建議：**
从 `addressNonZero` 修饰器中移除未使用的 `string memory parameter` 参数，并更新所有调用点以去掉该字符串参数。

---

## 5. Use event indexing for faster off-chain parameter lookup

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
Events defined in `IGlobalRegistryService` do not use the `indexed` keyword on their most important parameters. In Ethereum, only indexed event parameters are stored in log topics and can be efficiently queried by off-chain tools such as subgraphs, indexers, and block explorers. Without indexing, consumers must scan and decode all event data, which is significantly slower and more resource-intensive, especially as the number of emitted events grows over time.

**Impact:**
Off-chain components that rely on event filtering — including monitoring tools, analytics dashboards, and compliance systems — experience slower and less efficient queries. This increases infrastructure costs and latency for any system that needs to track specific addresses or roles across the registry's event history.

**Recommended Mitigation:**
Add the `indexed` keyword to the three most important parameters in each event defined in `IGlobalRegistryService`, prioritizing parameters that are most commonly used as filter criteria in off-chain queries, such as addresses and role identifiers.

---

**[中文版本]**

**描述：**
`IGlobalRegistryService` 中定义的事件没有对最重要的参数使用 `indexed` 关键字。以太坊中，只有 indexed 参数才会被存入日志主题（log topics），可被链下工具（如子图、索引器、区块浏览器）高效查询。缺少索引时，消费者必须扫描并解码所有事件数据，随着事件数量增长，查询效率会显著下降。

**影響：**
依赖事件过滤的链下组件（包括监控工具、分析仪表板和合规系统）会遭遇更慢、效率更低的查询，增加基础设施成本和延迟。

**修復建議：**
为 `IGlobalRegistryService` 中每个事件的最多三个最重要参数添加 `indexed` 关键字，优先对地址和角色标识符等常用过滤条件进行索引。

---
