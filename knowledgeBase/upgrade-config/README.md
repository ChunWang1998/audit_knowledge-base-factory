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

## 6. Consider wiping slot 177 on Linea L2MessageService after upgrade

**Severity:** 🔴 Critical
**Source:** `cyfrin/upgrade.md`

**Description:**
After the upgrade of Linea's `L2MessageService`, storage slot 177 is repurposed to serve as `__gap_ReentrancyGuardUpgradeable`. However, prior to the upgrade, slot 177 was used by the `_status` variable of the reentrancy guard and currently holds the value 1 (indicating a non-entered state). Changing the semantic meaning of a slot from an active variable to a gap variable without zeroing the existing value leaves stale data in that slot. Although a gap slot is not directly read by contract logic, the lingering value creates confusion about the storage layout and poses a risk if future upgrades inadvertently reintroduce a variable at that slot position, which would inherit an unexpected initial value.

**Impact:**
Stale non-zero data persists in a slot designated as a gap, which can cause unexpected behavior if any future upgrade assigns a new state variable to that slot. Given that slot 177 previously tracked reentrancy status, any new variable inheriting its value of 1 without a clean initialization could produce incorrect logic.

**Recommended Mitigation:**
Include an explicit storage wipe of slot 177 as part of the upgrade transaction to restore it to zero before it is re-designated as a gap slot.

---

**[中文版本]**

**描述：**
Linea 的 `L2MessageService` 升级后，存储槽 177 被重新用作 `__gap_ReentrancyGuardUpgradeable`。然而，升级前该槽存储的是可重入守卫的 `_status` 变量，当前值为 1（表示未进入状态）。将一个活跃变量槽改为 gap 槽而不清零现有值，会留下过期数据。如果未来升级在该槽引入新变量，新变量将意外继承值 1，导致逻辑错误。

**影響：**
槽 177 中残留的非零值若被未来升级引入的新变量继承，可能产生错误的初始状态，导致不可预期的合约行为。

**修復建議：**
在升级交易中显式将槽 177 清零，然后再将其重新指定为 gap 槽。

---

## 7. AtomicBatcher uses placeholder ERC-7201 namespace

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
`AtomicBatcher` derives its nonce storage slot from an ERC-7201 namespace constant that is still set to the placeholder value `"<namespace>"`. ERC-7201 requires a unique, stable namespace string to guarantee that the derived storage slot does not collide with slots used by other contracts or libraries. Using the generic placeholder means any other contract or tool that also uses `"<namespace>"` as its ERC-7201 namespace will compute an identical storage slot, breaking namespace isolation. This is particularly dangerous in contexts such as EIP-7702 style execution where multiple contracts may share an account's storage space.

**Impact:**
Nonce storage can collide with other code that uses the same placeholder namespace, potentially corrupting replay protection state, causing failed or replayed transactions, or enabling cross-application interference when running in shared storage environments.

**Recommended Mitigation:**
Replace `"<namespace>"` with a unique, project-specific, and immutable identifier such as `"accountable.atomicbatcher.nonce.v1"`, and treat it as permanently fixed across deployments and upgrades.

---

**[中文版本]**

**描述：**
`AtomicBatcher` 通过 ERC-7201 命名空间常量派生 nonce 存储槽，但该常量仍为占位符值 `"<namespace>"`。ERC-7201 要求唯一且稳定的命名空间字符串以避免存储槽碰撞。使用通用占位符意味着任何同样使用 `"<namespace>"` 的合约或工具都会计算出相同的存储槽，破坏命名空间隔离，在 EIP-7702 等共享账户存储的场景中风险尤为突出。

**影響：**
nonce 存储可能与使用相同占位符命名空间的代码发生碰撞，导致重放保护状态损坏、交易失败或重放，或在共享存储环境中产生跨应用干扰。

**修復建議：**
将 `"<namespace>"` 替换为唯一的、项目专属的不可变标识符，例如 `"accountable.atomicbatcher.nonce.v1"`，并在所有部署和升级中保持固定。

---

## 3. ComplianceServiceRegulated and its parent ComplianceServiceWhitelisted uses a chain of initializer modifiers when calling the initialize

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated` inherits from `ComplianceServiceWhitelisted`, and both contracts declare their `initialize()` functions with the `initializer` modifier. OpenZeppelin's documentation specifies that the `initializer` modifier should only appear on the topmost (final) `initialize()` function in an inheritance chain; parent contracts should instead use the `onlyInitializing` modifier on their initialization logic. Having two contracts in the same chain both marked with `initializer` can cause the parent's `initialize()` to be blocked from re-running by the already-set initialization flag, or it may interfere with proper initialization tracking under OpenZeppelin's proxy tooling.

**Impact:**
Under certain proxy upgrade patterns or multiple-inheritance scenarios, the dual use of `initializer` can cause initialization calls to revert unexpectedly or prevent proper re-initialization. This creates fragility in the upgrade and deployment pipeline.

**Recommended Mitigation:**
Refactor `ComplianceServiceWhitelisted` to expose an internal `_initialize()` function with the `onlyInitializing` modifier, keeping its public `initialize()` using `initializer` only at the outermost level. Then have `ComplianceServiceRegulated::initialize()` call the internal `_initialize()` instead of `super.initialize()`, ensuring only one `initializer` guard is active at any point in the chain.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated` 继承自 `ComplianceServiceWhitelisted`，两个合约的 `initialize()` 函数都使用了 `initializer` 修饰器。OpenZeppelin 规范要求 `initializer` 修饰器只应出现在继承链最顶层的 `initialize()` 上，父合约的初始化逻辑应使用 `onlyInitializing` 修饰器。在同一继承链中同时使用两个 `initializer` 可能导致父合约初始化被初始化标志阻塞，或干扰 OpenZeppelin 代理工具的正常初始化跟踪。

**影響：**
在某些代理升级模式或多重继承场景下，双重 `initializer` 可能导致初始化调用意外 revert 或无法正确完成初始化，给升级和部署流程带来脆弱性。

**修復建議：**
将 `ComplianceServiceWhitelisted` 重构为内部 `_initialize()` 函数并使用 `onlyInitializing` 修饰器，仅在最外层保留带 `initializer` 的公开 `initialize()`。让 `ComplianceServiceRegulated::initialize()` 调用内部 `_initialize()` 而非 `super.initialize()`，确保整个链中只有一个 `initializer` 守卫生效。

---

## 4. Disable initializers on upgradeable contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Several upgradeable contracts in the protocol — `yUSDeVault`, `yUSDeDepositor`, `pUSDeVault`, and `pUSDeDepositor` — do not call `_disableInitializers()` in their constructors. For UUPS and transparent proxy patterns, the implementation contract itself is deployed separately from the proxy, and without disabling initializers, someone can call the `initialize()` function directly on the implementation contract. This can lead to the implementation being initialized to a specific state that an attacker controls, potentially enabling storage manipulation or unauthorized ownership.

**Impact:**
An attacker who calls `initialize()` directly on an unprotected implementation contract can set themselves as the owner or configure the contract with malicious parameters. Depending on the contract's logic, this may allow future upgrades through the implementation address directly or other privilege escalation paths.

**Recommended Mitigation:**
Add a constructor to each of the listed upgradeable contracts that calls `_disableInitializers()`, preventing any future calls to `initialize()` on the implementation contract itself.

---

**[中文版本]**

**描述：**
协议中的多个可升级合约（`yUSDeVault`、`yUSDeDepositor`、`pUSDeVault`、`pUSDeDepositor`）在其构造函数中未调用 `_disableInitializers()`。在 UUPS 和透明代理模式下，实现合约作为独立合约部署，若不禁用初始化器，任何人都可以直接在实现合约上调用 `initialize()`，将其初始化为攻击者控制的状态，可能导致存储被篡改或未授权获得所有权。

**影響：**
攻击者可直接在未受保护的实现合约上调用 `initialize()`，将自己设为所有者或注入恶意配置。根据合约逻辑，这可能允许通过实现地址执行升级或进行其他权限提升。

**修復建議：**
为上述每个可升级合约添加调用 `_disableInitializers()` 的构造函数，防止在实现合约上再次调用 `initialize()`。

---

## 5. ERC-7201 Storage Location Comment Does Not Match Actual Value

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
In `Stargate.sol`, the NatSpec comment above the `StargateStorageLocation` constant states that the storage slot is derived from the namespace `"storage.Stargate"`, but the actual hardcoded hash value `0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700` was computed using the old contract name `"storage.StargateStaker"`. This mismatch was introduced when the contract was renamed from `StargateStaker` to `Stargate` and the comment was updated without recalculating the constant. Any developer who trusts the comment and derives a storage slot from `"storage.Stargate"` will compute a completely different hash, leading them to write a new implementation that reads and writes to entirely different storage slots than the deployed proxy expects.

**Impact:**
A future implementation contract created based on the incorrect developer comment would read and write to the wrong storage slots, resulting in complete loss of all existing state data including validator records, delegation mappings, and reward tracking. This would constitute total system failure for any upgraded deployment.

**Recommended Mitigation:**
Recalculate the `StargateStorageLocation` constant using the correct current namespace `"storage.Stargate"`, update the constant value in the contract, and ensure the comment and the value remain synchronized for all future naming changes.

---

**[中文版本]**

**描述：**
`Stargate.sol` 中 `StargateStorageLocation` 常量上方的 NatSpec 注释声明存储槽派生自命名空间 `"storage.Stargate"`，但实际硬编码的哈希值是使用旧合约名称 `"storage.StargateStaker"` 计算得出的。该不一致在合约从 `StargateStaker` 重命名为 `Stargate` 时引入，注释被更新但常量值未重新计算。开发者若信任注释并基于 `"storage.Stargate"` 派生存储槽，将得到完全不同的哈希值，导致新实现合约读写与代理预期完全不同的存储槽。

**影響：**
基于错误注释编写的新实现合约会读写错误的存储槽，导致所有现有状态数据（包括验证人记录、委托映射和奖励跟踪）完全丢失，造成升级部署后系统全面崩溃。

**修復建議：**
使用正确的当前命名空间 `"storage.Stargate"` 重新计算 `StargateStorageLocation` 常量，更新合约中的常量值，并确保后续所有命名变更时注释与值保持同步。

---

## 6. Missing notEmptyURI modifier during initialization

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
The `initialize()` function in `RWASegWrap` does not apply the `notEmptyUri` modifier, even though this modifier exists in the contract and is intended to prevent empty URI strings from being set. During initialization, other parameters such as `liquidationAsset`, `asset`, and `vaultDeployer` are validated with `addressNotZero` modifiers, but the `uriArg` parameter is accepted without any validation. An empty `projectURI` set at initialization time cannot be easily corrected without an upgrade or a separate setter function.

**Impact:**
The `projectURI` may be silently set to an empty string during contract initialization, leading to broken metadata references for all tokens minted under this vault. This represents a misconfiguration that passes undetected at deployment time.

**Recommended Mitigation:**
Add the `notEmptyUri(uriArg)` modifier to the `initialize()` function signature alongside the existing address validation modifiers, so that initialization reverts if an empty URI is provided.

---

**[中文版本]**

**描述：**
`RWASegWrap` 的 `initialize()` 函数未应用已存在的 `notEmptyUri` 修饰器，而该修饰器正是为防止设置空 URI 字符串而设计的。初始化时，`liquidationAsset`、`asset`、`vaultDeployer` 等参数都有 `addressNotZero` 修饰器校验，但 `uriArg` 参数未经任何验证便被接受。初始化时设置的空 `projectURI` 若不经过升级或添加 setter 函数将难以修正。

**影響：**
`projectURI` 可能在合约初始化时被静默设置为空字符串，导致该 vault 下铸造的所有代币的元数据引用失效，且该错误配置在部署时不会被检测到。

**修復建議：**
在 `initialize()` 函数签名中添加 `notEmptyUri(uriArg)` 修饰器，与现有的地址校验修饰器并列，确保传入空 URI 时初始化 revert。

---

## 7. Missing storage gap in upgradeable parent contract causes storage slot collision risk

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
The `VaultDeployer` abstract contract is designed to be inherited by upgradeable child contracts `SegregatedVaultDeployer` and `SecuritizeVaultDeployer`, but it does not declare storage gap variables. `VaultDeployer` currently declares three state variables (`navProvider`, `admin`, `upgradeableBeacon`), and child contracts like `SecuritizeVaultDeployer` add their own state variables directly after the parent's storage. When a new version of `VaultDeployer` adds additional state variables, those variables are allocated to the storage slots immediately following the existing parent variables, which are currently occupied by child contract state variables. This results in a storage collision that corrupts child contract data. The grandparent `BaseContract` correctly implements storage gaps, but `VaultDeployer` breaks this pattern.

**Impact:**
Any future upgrade that adds new state variables to `VaultDeployer` will overwrite storage slots currently used by child contracts, corrupting their state and potentially rendering deployed proxy contracts permanently unusable or insecure.

**Recommended Mitigation:**
Add storage gap variables to `VaultDeployer` to reserve sufficient space for future upgrades, either using a traditional `uint256[N] private __gap` array or by migrating to ERC-7201 namespaced storage for the contract's variables.

---

**[中文版本]**

**描述：**
`VaultDeployer` 抽象合约被可升级的子合约 `SegregatedVaultDeployer` 和 `SecuritizeVaultDeployer` 继承，但未声明存储间隙（storage gap）变量。`VaultDeployer` 当前声明了三个状态变量，子合约紧随其后添加自己的状态变量。当未来版本的 `VaultDeployer` 新增状态变量时，这些变量将占据原本属于子合约变量的存储槽，导致子合约状态损坏。祖父合约 `BaseContract` 正确实现了存储间隙，但 `VaultDeployer` 打破了这一模式。

**影響：**
任何为 `VaultDeployer` 添加新状态变量的升级都会覆盖子合约当前使用的存储槽，损坏子合约状态，可能导致已部署的代理合约永久失效或不安全。

**修復建議：**
为 `VaultDeployer` 添加存储间隙变量，为未来升级预留足够空间，可使用传统的 `uint256[N] private __gap` 数组，或将合约变量迁移至 ERC-7201 命名空间存储。

---

## 8. Missing storage gap on upgradeable base contracts

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
The `BaseContract` in the `bc-securitize-bridge-sc` repository inherits from `UUPSUpgradeable`, `OwnableUpgradeable`, and `PausableUpgradeable`, making it an upgradeable contract that other contracts inherit from. However, `BaseContract` does not declare a storage gap variable. Without a storage gap, any addition of new state variables to `BaseContract` in a future upgrade will shift the storage layout of all inheriting child contracts, causing the child contracts' state variables to be read from and written to incorrect storage slots.

**Impact:**
Adding new state variables to `BaseContract` in any future upgrade will cause storage collisions in all child contracts, corrupting their state and potentially making deployed proxy instances permanently broken.

**Recommended Mitigation:**
Add a storage gap declaration such as `uint256[50] private __gap` to `BaseContract` to reserve space for future state variable additions.

---

**[中文版本]**

**描述：**
`bc-securitize-bridge-sc` 仓库中的 `BaseContract` 继承自 `UUPSUpgradeable`、`OwnableUpgradeable` 和 `PausableUpgradeable`，是被其他合约继承的可升级合约，但未声明存储间隙变量。若未来升级为 `BaseContract` 添加新状态变量，所有继承合约的存储布局将发生偏移，导致子合约状态变量读写错误的存储槽。

**影響：**
任何为 `BaseContract` 添加新状态变量的升级都会导致所有子合约存储碰撞，损坏其状态，可能使已部署的代理实例永久损坏。

**修復建議：**
为 `BaseContract` 添加存储间隙声明，例如 `uint256[50] private __gap`，为未来状态变量添加预留空间。

---

## 9. Missing zero address validation in initialize function

**Severity:** 🟡 Medium
**Source:** `cyfrin/dstokenswap.md`

**Description:**
The `initialize` function in `DSTokenClassSwap` accepts `_sourceDSToken` and `_targetDSToken` as addresses but does not validate that either is a non-zero address before assigning them to state variables and wrapping them in interface casts. Since initialization can only be called once and there is no setter for these critical configuration values, passing `address(0)` for either parameter would permanently configure the contract with invalid token references.

**Impact:**
If either token address is initialized to `address(0)`, all token swap operations will fail or behave incorrectly. Because initialization is a one-time operation and there is no recovery path, the contract would need to be redeployed, causing operational disruption.

**Recommended Mitigation:**
Add zero address validation checks for both `_sourceDSToken` and `_targetDSToken` inside the `initialize` function before assigning them to state variables.

---

**[中文版本]**

**描述：**
`DSTokenClassSwap` 的 `initialize` 函数接受 `_sourceDSToken` 和 `_targetDSToken` 两个地址参数，但在将其赋值给状态变量并包装为接口类型之前，未验证是否为非零地址。由于初始化只能执行一次，且这些关键配置值没有对应的 setter，传入 `address(0)` 会使合约永久配置无效的代币引用。

**影響：**
若任一代币地址被初始化为 `address(0)`，所有代币兑换操作都将失败或产生错误行为。由于初始化是一次性操作且无恢复路径，合约必须重新部署，造成运营中断。

**修復建議：**
在 `initialize` 函数中，对 `_sourceDSToken` 和 `_targetDSToken` 赋值前添加零地址校验检查。

---

## 10. Upgrade script deploys implementation but doesn't execute upgrade

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
The `UpgradeBasisTradeTailor.s.sol` script deploys a new `BasisTradeTailor` implementation contract and logs "Tailor Upgraded", but the actual proxy upgrade call `tailor.upgradeToAndCall(address(newImpl), "")` is commented out. As a result, the proxy still points to the old implementation after the script runs. The `run()` function logs success messaging that implies the upgrade completed, while the `runSafe()` function suggests upgrades are intended to be routed through a Gnosis Safe. This inconsistency can cause operators to believe an upgrade was successfully executed when only the deployment of an unused implementation occurred.

**Impact:**
Operators running the script may be misled into believing the system is running the new implementation when the proxy has not been updated. This can mask critical security fixes or feature deployments, potentially leaving a vulnerable or outdated implementation in production.

**Recommended Mitigation:**
Either uncomment the `upgradeToAndCall` line to execute the upgrade directly in `run()`, or update all console logs and documentation to clearly indicate that this script is in "deploy-only" mode and the actual upgrade must be triggered separately via a Safe transaction or manual `upgradeToAndCall`.

---

**[中文版本]**

**描述：**
`UpgradeBasisTradeTailor.s.sol` 脚本部署了新的实现合约并打印 "Tailor Upgraded"，但实际执行代理升级的 `tailor.upgradeToAndCall(address(newImpl), "")` 调用被注释掉了。脚本运行后，代理仍指向旧实现。`run()` 函数的成功日志让人误以为升级已完成，而实际上仅部署了一个未被使用的新实现。

**影響：**
运行该脚本的操作员可能误以为系统已运行新实现，但代理实际上未更新。这可能掩盖关键安全修复或功能部署，使有漏洞或过时的实现持续运行于生产环境。

**修復建議：**
要么取消注释 `upgradeToAndCall` 以在 `run()` 中直接执行升级，要么更新所有日志和文档，明确说明该脚本为"仅部署"模式，实际升级需通过 Safe 交易或手动 `upgradeToAndCall` 单独触发。

---

## 11. Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collision

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
The Strata protocol contains upgradeable contracts that are inherited by other contracts, but these parent contracts do not employ ERC-7201 namespaced storage layouts or storage gap arrays. Without one of these two techniques, adding new state variables to a parent contract in a future upgrade shifts the storage layout of all inheriting child contracts, causing their existing state variables to be read from and written to incorrect storage slots — a storage collision. ERC-7201 namespaced storage is the modern preferred approach as it completely isolates each contract's storage domain.

**Impact:**
Storage collision can occur during upgrades that add new state variables to parent contracts, potentially corrupting the state of inheriting contracts and breaking protocol invariants.

**Recommended Mitigation:**
Migrate all upgradeable parent contracts to use ERC-7201 namespaced storage layouts. As a minimum alternative, add storage gap arrays to reserve space for future additions.

---

**[中文版本]**

**描述：**
Strata 协议中存在被其他合约继承的可升级父合约，但这些父合约既未使用 ERC-7201 命名空间存储布局，也未使用存储间隙数组。若未来升级为父合约添加新状态变量，所有继承子合约的存储布局将发生偏移，导致子合约状态变量读写错误的存储槽（存储碰撞）。ERC-7201 命名空间存储是现代首选方案，可完全隔离各合约的存储域。

**影響：**
为父合约添加新状态变量的升级可能导致存储碰撞，损坏继承合约的状态，破坏协议不变量。

**修復建議：**
将所有可升级父合约迁移至 ERC-7201 命名空间存储布局。作为最低替代方案，添加存储间隙数组以预留空间。

---

## 12. Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collisions

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
The Accountable Protocol contains upgradeable contracts that are inherited by other contracts, but these parent contracts do not use ERC-7201 namespaced storage layouts or storage gap arrays. The same fundamental problem applies as in similar findings across other codebases: without storage isolation, new state variables added to a parent contract during an upgrade overwrite storage slots that child contracts currently use for their own variables. The `AccountableStrategy` contract was specifically identified as lacking namespaced storage.

**Impact:**
Any upgrade adding new state variables to a parent contract in the Accountable Protocol hierarchy risks corrupting the storage of dependent child contracts, potentially compromising fund accounting, access control state, or other critical invariants.

**Recommended Mitigation:**
Adopt ERC-7201 namespaced storage layouts for all upgradeable contracts that are designed to be inherited from, ensuring each contract's storage variables are isolated to a unique derived slot that cannot be overwritten by inheritance chain modifications.

---

**[中文版本]**

**描述：**
Accountable 协议中存在被其他合约继承的可升级父合约，但这些父合约既未使用 ERC-7201 命名空间存储布局，也未使用存储间隙数组。问题与其他代码库中的类似发现相同：若升级时为父合约添加新状态变量，这些变量将覆盖子合约当前用于自身变量的存储槽。`AccountableStrategy` 合约被明确指出缺少命名空间存储。

**影響：**
任何为 Accountable 协议父合约添加新状态变量的升级都有损坏子合约存储的风险，可能危及资金核算、访问控制状态或其他关键不变量。

**修復建議：**
为所有设计为被继承的可升级合约采用 ERC-7201 命名空间存储布局，确保每个合约的存储变量被隔离在唯一派生槽中，不会因继承链变更而被覆盖。

---

## 13. Use unchained initializers instead

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Throughout the protocol, contracts call standard OpenZeppelin initializer functions such as `__ERC20_init`, `__Ownable_init`, and similar, rather than their unchained equivalents (e.g., `__ERC20_init_unchained`). The unchained variants are designed for use in multiple-inheritance scenarios where a base initializer might otherwise be called multiple times. When standard (chained) initializers are used in a diamond or deep inheritance hierarchy, the same base initialization logic can execute more than once, leading to duplicate event emissions, redundant state writes, or in some cases unexpected reverts if the underlying logic is not idempotent.

**Impact:**
Duplicate initialization of base contract logic can produce redundant state changes or event emissions, and may cause reverts in edge cases where the base initialization is not safe to call multiple times, undermining the reliability of the upgrade and initialization pipeline.

**Recommended Mitigation:**
Replace all standard initializer calls with their unchained equivalents (e.g., replace `__ERC20_init(name, symbol)` with `__ERC20_init_unchained(name, symbol)`) in contracts that use multiple inheritance, to prevent duplicate initialization of shared base contracts.

---

**[中文版本]**

**描述：**
协议中各合约调用 OpenZeppelin 标准初始化函数（如 `__ERC20_init`、`__Ownable_init` 等），而非其 unchained 变体（如 `__ERC20_init_unchained`）。unchained 变体专为多重继承场景设计，防止同一基础初始化逻辑被多次调用。在钻石继承或深层继承体系中使用链式初始化器，可能导致相同的基础初始化逻辑执行多次，产生重复事件、冗余状态写入，或在基础逻辑非幂等时意外 revert。

**影響：**
基础合约逻辑的重复初始化可能产生冗余状态变更或事件，在基础初始化不安全多次调用的边缘情况下可能导致 revert，破坏升级和初始化流程的可靠性。

**修復建議：**
在使用多重继承的合约中，将所有标准初始化调用替换为其 unchained 变体（例如将 `__ERC20_init(name, symbol)` 替换为 `__ERC20_init_unchained(name, symbol)`），防止共享基础合约被重复初始化。

---

## 14. rewardGrowthOutsideX128 is not correctly initialized in PoolRewards::updateAfterLiquidityAdd

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
Following the Uniswap V3/V4 convention, when a tick is first initialized and the current tick is to its right, the tick's `rewardGrowthOutsideX128` value must be set to the current `globalGrowthX128` so that reward calculations correctly attribute prior global growth to positions outside the range. `PoolRewards::updateAfterLiquidityAdd` attempts to replicate this initialization logic, but it is invoked as part of the `afterAddLiquidity` Uniswap hook — at which point the tick has already been initialized by the pool manager. As a result, the tick-initialization check `!pm.isInitialized(...)` always evaluates to false, meaning the initialization body never executes and `rewardGrowthOutsideX128` is never set. A `lastGrowthInsideX128` safeguard partially compensates for this in normal operation, but in specific boundary-tick scenarios combined with an existing bug in `TickIteratorDown`, an attacker can exploit the uninitialized state to steal all rewards in the pool.

**Impact:**
Reward growth outside ticks is never correctly initialized, which in certain configurations causes incorrect reward distribution and swap reverts due to underflow. In the most impactful exploitation path, an attacker can perform a sequence of swaps and liquidity additions to drain all rewards from the pool at a profit.

**Recommended Mitigation:**
Implement the `beforeAddLiquidity()` hook and its corresponding permission flag, and move the `PoolRewards::updateAfterLiquidityAdd` call to run before liquidity is added so that tick initialization state is checked before the pool manager initializes the ticks.

---

**[中文版本]**

**描述：**
根据 Uniswap V3/V4 惯例，当一个 tick 首次被初始化且当前 tick 在其右侧时，该 tick 的 `rewardGrowthOutsideX128` 必须设置为当前 `globalGrowthX128`，以便奖励计算正确将先前的全局增长归因于该范围外的仓位。`PoolRewards::updateAfterLiquidityAdd` 试图复现此初始化逻辑，但它是在 `afterAddLiquidity` 钩子中被调用的——此时 tick 已由池管理器初始化。因此，tick 初始化检查 `!pm.isInitialized(...)` 始终为 false，初始化逻辑从不执行，`rewardGrowthOutsideX128` 永远不会被设置。`lastGrowthInsideX128` 保护机制在正常操作中部分弥补了这一问题，但在特定边界 tick 场景结合 `TickIteratorDown` 中的另一个 bug 时，攻击者可利用未初始化状态窃取池中的全部奖励。

**影響：**
tick 外部的奖励增长从未被正确初始化，在特定配置下导致奖励分配错误和由于下溢引起的交换 revert。在最严重的利用路径中，攻击者可通过一系列交换和流动性添加操作获利并抽走池中的全部奖励。

**修復建議：**
实现 `beforeAddLiquidity()` 钩子及相应的权限标志，将 `PoolRewards::updateAfterLiquidityAdd` 的调用移至流动性添加之前执行，使 tick 初始化状态检查在池管理器初始化 tick 之前完成。

---

## 15. setApprovalForAll() function is double initialized in the child contract

**Severity:** 🟡 Medium
**Source:** `cyfrin/rwasegwrap.md`

**Description:**
The `setApprovalForAll()` function is defined in both the parent contract `RWASegWrap` and the child contract `SecuritizeRWASegWrap` with identical implementations that unconditionally revert with `FeatureNotSupported()`. The override in `SecuritizeRWASegWrap` is completely redundant because it adds no new logic, modifiers, or behavior beyond what is already present in the parent. This pattern of duplicating a function override without any modification serves no functional purpose.

**Impact:**
The redundant function override increases the deployment bytecode size of `SecuritizeRWASegWrap`, resulting in higher deployment gas costs. It also adds unnecessary maintenance surface, since any future changes to this function must be applied in both places to remain consistent.

**Recommended Mitigation:**
Remove the `setApprovalForAll()` override from `SecuritizeRWASegWrap`, relying entirely on the parent contract's implementation to provide the feature-disabled behavior.

---

**[中文版本]**

**描述：**
`setApprovalForAll()` 函数在父合约 `RWASegWrap` 和子合约 `SecuritizeRWASegWrap` 中均有定义，两者实现完全相同，均无条件 revert 并返回 `FeatureNotSupported()`。子合约中的重写完全冗余，未添加任何新逻辑、修饰器或行为，仅是对父合约实现的重复。

**影響：**
冗余的函数重写增加了 `SecuritizeRWASegWrap` 的部署字节码大小，导致更高的部署 gas 成本。同时增加了不必要的维护面，未来若需修改此函数，必须在两处同步修改以保持一致。

**修復建議：**
从 `SecuritizeRWASegWrap` 中移除 `setApprovalForAll()` 重写，完全依赖父合约实现来提供功能禁用行为。

---
