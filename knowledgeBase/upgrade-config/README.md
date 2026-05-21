# upgrade-config (49)

> Issues related to upgradeable contracts, proxy storage layout, slot collisions, and configuration management.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

## Subcategories

- [contracts-upgradeable](./contracts-upgradeable/) (19) — missing modifiers, incorrect inheritance, interface non-compliance
- [storage-function](./storage-function/) (20) — storage layout conflicts when adding functions or variables during upgrades
- [storage-prior](./storage-prior/) (9) — storage slot ordering and priority collisions across upgrade versions

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
