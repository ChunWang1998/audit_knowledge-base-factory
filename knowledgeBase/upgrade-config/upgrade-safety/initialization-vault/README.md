# initialization-vault (6)

> Issues where vault or proxy initialization was incomplete, missing zero-address checks, or allowed re-initialization.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. Missing zero-address validation for burner address during initialization can break slashing

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
The `VaultTokenized` contract's `_initialize` function assigns `params.burner` directly to the storage variable `vs.burner` without checking that the value is a non-zero address. Other critical parameters such as `collateral` are validated against zero before assignment, but `burner` is treated differently and accepted without any guard. The `onSlash` function subsequently calls `IERC20(vs.collateral).safeTransfer(vs.burner, slashedAmount)`, which will revert for most ERC-20 implementations when the recipient is `address(0)`, because `safeTransfer` internally validates the target address.

**Impact:**
If `burner` is inadvertently or maliciously set to `address(0)` during vault initialization, every future slashing operation will revert. This permanently disables the slashing mechanism for the affected vault, breaking a core security function that is critical for protecting the protocol's collateral guarantees.

**Recommended Mitigation:**
Add a zero-address check for `params.burner` inside the `_initialize` function, consistent with the validation already applied to other critical address parameters.

---

**[中文版本]**

**描述：**
`VaultTokenized` 合约的 `_initialize` 函数直接将 `params.burner` 赋值给存储变量 `vs.burner`，未检查其是否为非零地址。其他关键参数（如 `collateral`）在赋值前均有零地址校验，但 `burner` 未受相同保护。`onSlash` 函数随后调用 `IERC20(vs.collateral).safeTransfer(vs.burner, slashedAmount)`，对大多数 ERC-20 实现而言，当接收地址为 `address(0)` 时此调用将 revert。

**影響：**
若 `burner` 在 vault 初始化时被设置为 `address(0)`（无论出于疏忽还是恶意），所有后续的 slash 操作都将 revert，永久禁用受影响 vault 的 slash 机制，破坏协议抵押品保障的核心安全功能。

**修復建議：**
在 `_initialize` 函数中为 `params.burner` 添加零地址检查，与已对其他关键地址参数应用的校验保持一致。

---

## 2. Proxy reuse without implementation check inside UnstakeCooldown leads to execution on outdated/vulnerable logic

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
The `UnstakeCooldown` contract maintains a pool of previously used minimal proxies (`proxiesPool`) for each user and reuses them across new transfer requests. However, a clone's target implementation address is permanently embedded in its bytecode at creation time and cannot be updated without creating a new clone. When the owner updates `implementations[token]` via `setImplementations`, any proxies already in a user's pool continue to delegate to the old implementation. The contract does not verify that a reused proxy's implementation matches the current `implementations[token]` before reuse, meaning users may unknowingly execute against a stale or vulnerable code path even after the owner has deployed a security fix.

**Impact:**
Users can continue operating through outdated or vulnerable implementations even after the owner has applied an update. This creates inconsistent behavior across requests — some proxies use the new implementation while others use the old one — and creates a security risk if the prior implementation contains an exploitable vulnerability that the update was intended to fix.

**Recommended Mitigation:**
When dequeuing a proxy from the user's pool for reuse, verify that the proxy's embedded implementation address matches the current `implementations[token]`. If it does not match, discard the stale proxy and create a new clone targeting the current implementation.

---

**[中文版本]**

**描述：**
`UnstakeCooldown` 合约为每个用户维护一个曾用最小代理（minimal proxy）池（`proxiesPool`），并在新的转账请求中复用这些代理。然而，克隆合约的目标实现地址在创建时已永久嵌入字节码，无法在不创建新克隆的情况下更新。当所有者通过 `setImplementations` 更新 `implementations[token]` 后，用户池中已有的代理仍然委托给旧实现。合约在复用代理前不验证其实现地址是否与当前 `implementations[token]` 匹配，用户可能在所有者部署安全修复后仍无感知地在过期或有漏洞的代码路径上执行。

**影響：**
即使所有者已应用更新，用户仍可能通过过期或有漏洞的实现继续操作。这导致请求间行为不一致（部分代理使用新实现，其余使用旧实现），若旧实现存在可利用漏洞，将构成安全风险。

**修復建議：**
从用户池中取出代理复用时，验证代理嵌入的实现地址是否与当前 `implementations[token]` 匹配。若不匹配，丢弃过期代理并创建指向当前实现的新克隆。

---

## 3. Vault governor cannot upgrade target

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Vesu Vaults.txt`

**Description:**
The `vault_governor` contract exposes an `upgrade_contract_setup` function that is documented as upgrading a specified target contract to a new class hash. The function accepts both a `target` contract address and a `new_class_hash` argument. However, the implementation calls `self.upgradeable.upgrade(new_class_hash)` on the `vault_governor`'s own upgradeable component rather than dispatching the upgrade call to the provided `target` address. The `target` parameter is effectively ignored, and every invocation of `upgrade_contract_setup` upgrades the governance contract itself rather than the intended peripheral contract.

**Impact:**
The intended functionality of upgrading peripheral or vault contracts through the governor is completely broken. Any call to `upgrade_contract_setup` with a legitimate target will silently upgrade the governor itself instead, potentially disrupting governance logic or introducing unintended state changes to the governor contract.

**Recommended Mitigation:**
Update the implementation of `upgrade_contract_setup` so that the upgrade call is dispatched to the provided `target` contract address rather than applied to `self`. The function should call the upgrade entrypoint on the target contract, respecting the intended delegation pattern.

---

**[中文版本]**

**描述：**
`vault_governor` 合约提供的 `upgrade_contract_setup` 函数，按文档说明应将指定目标合约升级至新的 class hash。函数接受 `target` 合约地址和 `new_class_hash` 两个参数。然而，实现中调用的是 `self.upgradeable.upgrade(new_class_hash)`，即对 `vault_governor` 自身的可升级组件执行升级，而非将升级调用分发至 `target` 地址。`target` 参数实际上被完全忽略，每次调用都会升级治理合约本身而非预期的目标合约。

**影響：**
通过 governor 升级外围合约或 vault 合约的预期功能完全失效。任何携带合法目标地址的 `upgrade_contract_setup` 调用都会静默地升级 governor 本身，可能破坏治理逻辑或对 governor 合约引入非预期的状态变更。

**修復建議：**
修改 `upgrade_contract_setup` 的实现，使升级调用被分发至提供的 `target` 合约地址，而非应用于 `self`，遵循预期的委托升级模式。

---

## 4. Vault initialization allows zero deposit limit with no ability to modify causing denial of service

**Severity:** 🟡 Medium
**Source:** `cyfrin/core.md`

**Description:**
The `VaultTokenized` contract's `_initialize` function contains a conditional validation path that only checks deposit limit consistency when `params.isDepositLimitSetRoleHolder == address(0)`. This creates a gap: a vault can be initialized with deposit limit enabled (`isDepositLimit = true`), a zero deposit limit (`depositLimit = 0`), an address assigned to `isDepositLimitSetRoleHolder` (who can toggle the feature on/off), but no address assigned to `depositLimitSetRoleHolder` (who would be able to modify the limit value). Because `isDepositLimitSetRoleHolder` is non-zero, the validation logic is skipped entirely, allowing this inconsistent configuration to pass without revert. The result is a vault where deposits are perpetually blocked at zero, and no role exists to change the limit — only the ability to disable the feature entirely.

**Impact:**
Vaults initialized in this misconfigured state have all deposits permanently blocked unless the `isDepositLimitSetRoleHolder` explicitly disables the deposit limit feature entirely. This constitutes a denial of service for vault deposits and could trap any collateral already inside the vault.

**Recommended Mitigation:**
Remove the outer condition gating on `isDepositLimitSetRoleHolder` and instead perform deposit limit consistency validation unconditionally whenever `defaultAdminRoleHolder` is not set. Specifically, revert if `isDepositLimit` is true, `depositLimit` is zero, and `depositLimitSetRoleHolder` is `address(0)`, regardless of whether `isDepositLimitSetRoleHolder` is assigned.

---

**[中文版本]**

**描述：**
`VaultTokenized` 的 `_initialize` 函数仅在 `params.isDepositLimitSetRoleHolder == address(0)` 时才检查存款限制一致性，留下了一个缺口：vault 可以在开启存款限制（`isDepositLimit = true`）、存款限额为零（`depositLimit = 0`）、已分配 `isDepositLimitSetRoleHolder`（可切换功能开关）但未分配 `depositLimitSetRoleHolder`（可修改限额值）的情况下初始化。由于 `isDepositLimitSetRoleHolder` 非零，校验逻辑被完全跳过，错误配置得以通过。结果是一个存款永久被限制为零、且没有任何角色能修改限额的 vault。

**影響：**
以此错误配置初始化的 vault，除非 `isDepositLimitSetRoleHolder` 主动完全禁用存款限制功能，否则所有存款操作将永久被阻塞，对存款造成拒绝服务，并可能使已存入的抵押品被困在 vault 中。

**修復建議：**
去除以 `isDepositLimitSetRoleHolder` 为外层条件的校验分支，改为在 `defaultAdminRoleHolder` 未设置时无条件执行存款限制一致性校验。具体地，无论 `isDepositLimitSetRoleHolder` 是否已分配，只要 `isDepositLimit` 为 true、`depositLimit` 为零且 `depositLimitSetRoleHolder` 为 `address(0)`，均应 revert。

---

## 5. liquidityProviderWallet is not set during initialization

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
In `AllowanceLiquidityProvider::initialize`, the public state variable `liquidityProviderWallet` is declared but never assigned during contract initialization. The `initialize` function does not accept a parameter for this value and contains no assignment statement for it, leaving it at its default value of `address(0)`. Functions that depend on this variable, including `_availableLiquidity()` and `supplyTo()`, will silently operate against the zero address until a separate setter is called post-initialization. However, `transferFrom(address(0), ...)` calls will fail for standard ERC-20 tokens, meaning the contract is non-functional from the moment it is deployed until `liquidityProviderWallet` is explicitly set.

**Impact:**
Any functionality that reads `liquidityProviderWallet` — including liquidity availability queries and the core supply mechanism — will behave incorrectly or fail outright immediately after deployment. Redemption flows will revert when attempting to transfer from `address(0)`, rendering the liquidity provider contract inoperable until a separate configuration step is performed.

**Recommended Mitigation:**
Add a `_liquidityProviderWallet` parameter to the `initialize` function, validate that it is non-zero, and assign it to the state variable during initialization to ensure the contract is fully configured and operational upon deployment.

---

**[中文版本]**

**描述：**
`AllowanceLiquidityProvider::initialize` 中声明了公开状态变量 `liquidityProviderWallet`，但在合约初始化期间从未被赋值。`initialize` 函数不接受该值的参数，也无对应的赋值语句，使其保持默认值 `address(0)`。依赖该变量的函数（包括 `_availableLiquidity()` 和 `supplyTo()`）将在单独的 setter 被调用之前静默对零地址操作。对标准 ERC-20 代币而言，`transferFrom(address(0), ...)` 调用将失败，意味着合约从部署起就无法正常运行。

**影響：**
所有读取 `liquidityProviderWallet` 的功能（包括流动性可用性查询和核心供应机制）在部署后立即无法正常工作或直接失败。赎回流程在尝试从 `address(0)` 转账时会 revert，使流动性提供者合约在单独完成配置步骤之前完全无法使用。

**修復建議：**
在 `initialize` 函数中添加 `_liquidityProviderWallet` 参数，验证其为非零地址，并在初始化期间赋值给状态变量，确保合约在部署时即完全配置、可正常使用。

---

## 6. pancakeRouter and pancakePair Initialization Can Be Skipped in Constructor With No Recovery Mechanism

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The `NTE` contract's constructor accepts `_pancakeRouter` as an optional parameter and explicitly allows it to be `address(0)`. When the zero address is passed, the entire router and pair initialization block is skipped — both `pancakeRouter` and `pancakePair` remain at their default zero-address values. Critically, the contract does not expose any setter functions to update these variables after deployment, meaning there is no recovery path if they are not set at construction time. These variables are required for runtime validations including price impact limit enforcement; without them, those protections become silently ineffective.

**Impact:**
A deployment with `_pancakeRouter == address(0)` results in a contract where core DEX functionality (price impact validation, pair-based routing) is permanently disabled. The only remediation is a full redeployment, which causes operational disruption and unnecessary proliferation of contract instances. Protocol guarantees around price impact protection become unenforceable.

**Recommended Mitigation:**
Either enforce a non-zero `_pancakeRouter` address in the constructor by reverting on zero input, or introduce access-controlled setter functions for `pancakeRouter` and `pancakePair` that allow post-deployment configuration — which was the approach taken in the fix by adding `setPancakeRouter()` and `setPancakePair()`.

---

**[中文版本]**

**描述：**
`NTE` 合约构造函数接受可选的 `_pancakeRouter` 参数，并明确允许其为 `address(0)`。当传入零地址时，路由器和交易对初始化块被完全跳过，`pancakeRouter` 和 `pancakePair` 均保持默认零地址值。更关键的是，合约未提供任何在部署后更新这些变量的 setter 函数，若构造时未设置则无恢复路径。这些变量是运行时校验（包括价格影响限制执行）所必需的，缺失时相关保护将静默失效。

**影響：**
以 `_pancakeRouter == address(0)` 部署的合约中，核心 DEX 功能（价格影响校验、基于交易对的路由）将被永久禁用。唯一的补救措施是重新部署，造成运营中断并产生不必要的多余合约实例。协议的价格影响保护承诺将无法执行。

**修復建議：**
在构造函数中强制要求 `_pancakeRouter` 为非零地址（传入零地址时 revert），或引入受访问控制保护的 `pancakeRouter` 和 `pancakePair` setter 函数以支持部署后配置——修复方案采用了后一种方式，添加了 `setPancakeRouter()` 和 `setPancakePair()`。

---
