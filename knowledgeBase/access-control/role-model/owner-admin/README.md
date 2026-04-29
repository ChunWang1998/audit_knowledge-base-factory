# owner-admin (20)

> Issues where owner, admin, or privileged role boundaries were misconfigured, conflated, or failed to enforce intended restrictions.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. In `DelegatorFactory` new entity can be created for a blacklisted implementation

**Severity:** 🟠 High
**Source:** `cyfrin/core.md`

**Description:**
`DelegatorFactory::create` does not check whether the specified implementation type has been blacklisted before deploying a new entity. When an implementation is blacklisted — typically because it was found unsafe, deprecated, or otherwise restricted — the governance intent is to prevent further deployment using that version. The missing check means the factory silently bypasses this restriction: it will deploy a new entity using a blacklisted implementation type without reverting.

**Impact:**
If an implementation is blacklisted due to a security vulnerability, vault owners can still expose themselves to those vulnerabilities by creating new entities or migrating to the blacklisted version. The intended security barrier provided by blacklisting is fully defeated.

**Recommended Mitigation:**
Add an explicit blacklist check inside `DelegatorFactory::create` that reverts if the requested implementation type is currently blacklisted before proceeding with deployment.

---

## 2. Incorrect `owner` passed to `Manager::redeem` in YToken withdrawal flow

**Severity:** 🟠 High
**Source:** `cyfrin/yieldfi.md`

**Description:**
YieldFi's yield tokens implement a deferred withdrawal mechanism via a central `Manager` contract. In `YToken::_withdraw` (and identically in `YTokenL2::_withdraw`), `msg.sender` is incorrectly passed as the `owner` parameter to `manager.redeem`, even though the correct `owner` is already available in the function signature. This works when the caller and owner are the same address, but breaks in delegated withdrawal scenarios where a third party holds an allowance and initiates the withdrawal on behalf of the token owner.

**Impact:**
When a third party (`caller != owner`) initiates a withdrawal on behalf of another user, the call to `manager.redeem` receives `msg.sender` (the caller) as the owner instead of the actual share owner. This causes the call to revert, blocking the withdrawal. In a worst-case scenario, if the caller also holds shares, the wrong user's tokens may be burned instead of the intended owner's.

**Recommended Mitigation:**
Replace the `msg.sender` argument passed to `manager.redeem` with the `owner` parameter that is already available in the `_withdraw` function signature.

---

## 3. Users Can Renounce BLACKLISTED_ROLE and Bypass Administrative Restrictions

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
`OverlayerWrap` implements a `BLACKLISTED_ROLE` mechanism via OpenZeppelin's `AccessControl` to restrict sanctioned or non-compliant accounts from transferring, minting, or redeeming tokens. The `SingleAdminAccessControl` parent contract overrides `renounceRole()` to prevent renouncing `DEFAULT_ADMIN_ROLE`, but provides no similar restriction on `BLACKLISTED_ROLE`. Any blacklisted account can call `renounceRole(BLACKLISTED_ROLE, self)` to independently remove its own restriction. The blacklist is expected to be an administrative control used to restrict malicious, sanctioned, or non-compliant accounts, but this mechanism is entirely ineffective against accounts that know to exploit this path.

**Impact:**
Blacklisted users can independently remove their blacklist status and regain full transfer, mint, and redeem functionality, completely defeating the compliance controls.

**Recommended Mitigation:**
Override `renounceRole()` in `OverlayerWrap` to also block renouncement of `BLACKLISTED_ROLE`, similar to how the parent contract blocks `DEFAULT_ADMIN_ROLE` renouncement.

---

## 4. Admin Can Arbitrarily Decrease User's Vesting Amount

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/A Two Tech Limited.txt`

**Description:**
`ATWOVesting::setSchedule()` allows the admin to update a user's linear vesting schedule at any time, including the `total` vesting amount. While the function does prevent reducing `total` below already-claimed amounts, it does not prevent reducing it below the currently accrued (vested-but-unclaimed) amount. Because claimable tokens are computed as `vestedToDate - claimed`, reducing `total` retroactively reduces the amount the user can claim — even for time that has already elapsed in the vesting schedule. The absence of proper validation enables the admin to unilaterally reduce vested amounts, leading to inconsistency between the vesting state and the actual accrued balance.

**Impact:**
Admin can revoke a user's legitimate vested entitlement, resulting in loss of tokens that the user should already be able to claim. This creates significant trust risk and the potential for abuse of administrative privileges.

**Recommended Mitigation:**
Add a check ensuring the new `total` is at least equal to the already-accrued amount at the time of update (tokens vested to-date minus claimed), preventing retroactive reduction of entitled amounts.

---

## 5. Blacklist Enforcement Bypassed When Recipient Is Transaction-Limit Exempt

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
`KnoxNet._enforceTxLimit` combines two logically separate concerns — transaction size limits and blacklist enforcement — under a single exemption guard. The function opens with an early return if either the sender or recipient is `isTxLimitExempt`. The blacklist check (`require(blacklist[sender] == 0)`) is placed after this early return. Several addresses are marked as tx-limit exempt during construction, including the contract itself, the owner, and the router address. If the recipient holds `isTxLimitExempt` status, the function returns before the blacklist check is ever evaluated, allowing a blacklisted sender to transfer freely to those exempt addresses.

**Impact:**
Blacklist enforcement is circumvented whenever the recipient has tx-limit exemption, allowing blacklisted accounts to transfer tokens to privileged addresses (owner, router, contract) without restriction, completely defeating the blacklist mechanism for those transfer paths.

**Recommended Mitigation:**
Separate the blacklist check from the tx-limit exemption guard so that blacklist status is always evaluated regardless of whether either party is tx-limit exempt.

---

## 6. Combination of Ownable and AccessControl Can Cause Loss of Admin Functionality

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeTailor` and `BasisTradeVault` inherit both `Ownable(2Step)Upgradeable` and `AccessControlUpgradeable`. Several admin wrapper functions are guarded by `onlyOwner` but internally call `grantRole`/`revokeRole`, which themselves require the caller to hold `DEFAULT_ADMIN_ROLE`. This creates a dual requirement: the caller must simultaneously be both the `owner` and a `DEFAULT_ADMIN_ROLE` holder. When ownership is transferred via `transferOwnership` without also transferring `DEFAULT_ADMIN_ROLE`, the new owner cannot call `grantAdmin`, `revokeAdmin`, or similar role management functions. Conversely, a `DEFAULT_ADMIN_ROLE` holder who is not the owner cannot authorize upgrades since `_authorizeUpgrade` is `onlyOwner`. The extra wrappers also duplicate functionality and enlarge the attack surface.

**Impact:**
A realistically common ownership transfer that forgets to synchronize roles causes a partial loss of admin functionality with no on-chain remedy. The new owner may be completely unable to manage roles, and the existing `DEFAULT_ADMIN_ROLE` holder cannot upgrade the contract.

**Recommended Mitigation:**
Unify on `AccessControl` by removing `Ownable` entirely. Gate all privileged functions including `_authorizeUpgrade` with `onlyRole(DEFAULT_ADMIN_ROLE)`. If keeping `Ownable`, add logic to automatically synchronize `DEFAULT_ADMIN_ROLE` on every ownership transfer.

---

## 7. `DEFAULT_ADMIN_ROLE` Can Be Mistakenly Granted When Granting `fallback` Permission on Any Contract

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
`AccessControlManager::grantCall` computes a role as `roleFor(contractAddress, selector)` using bitwise operations: the contract address occupies the upper bits and the function selector occupies the lower bits. There is an edge case when granting permission to call the `fallback()` function (selector `bytes4(0)`) on any contract (address `address(0)`). The combination of these two zero inputs results in a computed role of `bytes32(0)`, which is precisely the value assigned to `DEFAULT_ADMIN_ROLE`. The function proceeds to grant this computed role to the recipient, inadvertently granting full admin rights.

**Impact:**
An account given permission to call fallback on any contract inadvertently receives `DEFAULT_ADMIN_ROLE`, which it can then use to grant arbitrary permissions to other accounts and take complete control of the access control system.

**Recommended Mitigation:**
Add a validation in `grantCall` that reverts if the computed role equals `DEFAULT_ADMIN_ROLE`. Alternatively, revert when `contractAddress == address(0)` or `selector == bytes4(0)` to block this specific edge case entirely.

---

## 8. Default Admin Can Assign Blacklisted Role Without Enforcing Blacklist Activation Constraints

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Overlayer.txt`

**Description:**
`OverlayerWrap` implements a `blacklistActivationTime` variable controlling when blacklisting becomes active. The `disableAccount()` function correctly enforces this timing restriction via the `blacklistAllowed` modifier, which reverts if the activation time has not yet been reached. However, since the contract inherits OpenZeppelin's `AccessControl`, which exposes a public `grantRole()` function, the `DEFAULT_ADMIN_ROLE` holder can bypass the activation timing entirely by calling `grantRole(BLACKLISTED_ROLE, account)` directly. This direct call does not pass through the `blacklistAllowed` modifier and therefore does not apply the intended activation-time restriction.

**Impact:**
The `DEFAULT_ADMIN_ROLE` can blacklist accounts before the intended activation time, violating the protocol's commitment to users about when blacklisting is active, and creating inconsistent state between what users expect and what the contract enforces.

**Recommended Mitigation:**
Override `grantRole` in `OverlayerWrap` to enforce the `blacklistAllowed` timing check specifically for `BLACKLISTED_ROLE` assignments, preventing the bypass via direct role granting.

---

## 9. Guardian Can Override Owner's Emergency Pause

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
The WLFI contract grants both the owner and guardians symmetric pause and unpause capabilities. The `guardianUnpause()` function allows any guardian to unpause the contract, even when the owner has deliberately paused it in response to a security incident or operational concern. The code itself contains a developer comment flagging this as a potential design concern. Common security practice dictates that pausing (a defensive action with low risk) should be permitted among multiple authorized parties, but unpausing (a higher-risk operation that restores service) should require the highest authority level only.

**Impact:**
A guardian can override the owner's emergency security response by unpausing the contract, potentially restoring service while an attack or vulnerability is still active, undermining the authority hierarchy and the effectiveness of the emergency response mechanism.

**Recommended Mitigation:**
Remove the unpause capability from guardians, restricting the ability to unpause to the owner only.

---

## 10. Misleading `owner` Field in `OnMetaWithdraw` Event

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
The `OnMetaWithdraw` event emits `receiver` as its first argument, but the parameter is named `owner` in the event definition. In ERC-4626, `owner` (the share holder), `caller` (the initiator of the withdrawal), and `receiver` (the recipient of the withdrawn assets) are three semantically distinct addresses that can all differ in a delegated withdrawal scenario. Naming the `receiver` as `owner` in the event creates a semantic mismatch that will mislead off-chain indexers, analytics dashboards, and monitoring tools that parse event data by parameter name.

**Impact:**
Off-chain systems incorrectly attribute withdrawal ownership, leading to incorrect accounting in analytics, wrong attribution in user-facing dashboards, and potentially flawed risk monitoring that relies on the `owner` field to track fund movements.

**Recommended Mitigation:**
Rename the event parameter from `owner` to `receiver`, or restructure the event to include both `owner` and `receiver` as distinct fields to accurately represent all parties involved in a delegated withdrawal.

---

## 11. Owner Authorization Allows Arbitrary Burning of Soulbound Tokens

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**
`SoulboundCredential::burnCredential()` grants the contract owner the ability to burn any token belonging to any address, in addition to the token holder and the issuer. Soulbound tokens are designed to be permanently bound to the original recipient and non-transferable, guaranteeing credential permanence. The owner's unrestricted burn capability fundamentally undermines this guarantee. In the event of owner key compromise, any credential in the system can be destroyed without the holder's knowledge or consent.

**Impact:**
Any credential held by any user can be unilaterally destroyed by the owner or an attacker who compromises the owner key, undermining the permanence guarantee of soulbound tokens and the integrity of the entire DID credential system.

**Recommended Mitigation:**
Remove the owner's ability to burn tokens that were not issued by or do not belong to them. If administrative burn capability is required, add multi-sig requirements, governance approval thresholds, or time delays to prevent unilateral destruction.

---

## 12. Owner Rights Can Be Renounced While Contract Is Paused

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Node Meta.txt`

**Description:**
The NTE contract implements pausable token transfers and allows the owner to call `renounceOwnership()` after 30 days from deployment. The `renounceOwnership` function validates only the time constraint but does not check whether the contract is currently paused. If the owner renounces ownership while the contract is paused, ownership is permanently transferred to the zero address. Since only the owner can unpause the contract, and the owner address is now `address(0)` which cannot sign transactions, no entity retains the ability to resume transfers. The result is a permanently paralyzed protocol.

**Impact:**
All token transfers become permanently frozen with no recovery path, effectively rendering the protocol permanently unusable and permanently locking all user funds in a state with no administrative remedy.

**Recommended Mitigation:**
Add a check in `renounceOwnership()` that reverts if the contract is currently paused, preventing ownership renouncement from being used to create an unrecoverable frozen state.

---

## 13. Owner Can Chain Admin Calls for Same-Block Drains

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
Multiple owner-privileged admin functions in `SherpaVault` and `SherpaUSD` have no built-in time delays, allowing the owner to atomically chain multiple privileged calls within the same block. Three distinct drain paths exist: (1) Vault drain — call `setStableWrapper` to change the token that is protected from rescue, then immediately call `rescueTokens` to extract the old wrapper balance from the vault; (2) Wrapper operator drain — call `setOperator`, then use `SherpaUSD::transferAsset` to move USDC out of the wrapper; (3) Wrapper keeper drain — call `setKeeper`, then use `depositToVault` to pull USDC from users with existing approvals and extract value via `transferAsset`. Despite code comments stressing limited owner power, the actual on-chain authority is far-reaching and exercisable atomically.

**Impact:**
Owner or a compromised owner key can immediately redirect custody and drain user funds with no warning or reaction time for users, creating a significant gap between the stated design intent and the actual on-chain risk profile.

**Recommended Mitigation:**
Add minimum time delays (at least one withdrawal epoch) to sensitive admin functions such as `setStableWrapper`, `rescueTokens`, `setOperator`, and `setKeeper`. Make `stableWrapper` and `keeper` immutable after initial deployment to eliminate the vault drain and keeper drain paths entirely.

---

## 14. Owner Can Front-Run Depositors by Setting Yield Value to Dust

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Prodigy Finance.txt`

**Description:**
The owner can monitor the mempool for pending deposit transactions and front-run them by calling `adjustYieldValue` to reduce the yield value to a dust amount just before the deposit transaction executes. The depositor's transaction then executes with near-zero yield, and no trading fee is applied to the owner for the same deposit. The owner can then back-run the deposit transaction to restore the original yield value. The contracts are planned for mainnet deployment where MEV-style attacks of this nature are straightforwardly executable. Victims must wait for the vault to close via `VaultCore::execute` to recover their funds, with no yield received.

**Impact:**
Depositors have their funds effectively frozen until vault closure while receiving no yield — they deposited in expectation of yield but receive none due to the owner's front-running manipulation. Users lose confidence in the protocol and cannot exit until the vault closes.

**Recommended Mitigation:**
Add a `minYieldValue` parameter to the deposit function allowing depositors to specify the minimum acceptable yield, causing the transaction to revert if the current yield value falls below their threshold. Alternatively, implement a timelock on `adjustYieldValue` so changes only take effect after a minimum delay.

---

## 15. Owner Cannot Burn Tokens From Blacklisted Addresses

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
`HilBTC::burnFrom()` contains a special case allowing the owner to burn tokens from any address without requiring an allowance, bypassing `_spendAllowance`. However, the internal `_burn()` calls `_update()`, which applies the `notBlacklisted(from)` modifier. This modifier blocks any update operation involving a blacklisted `from` address, including owner-initiated burns. The result is a functional inconsistency: the owner has a special `burnFrom` privilege that is silently negated for the specific addresses where it is most likely to be operationally needed — blacklisted addresses requiring administrative remediation.

**Impact:**
Owner cannot exercise intended administrative control to burn tokens from blacklisted addresses, defeating a key purpose of the owner's elevated burn privilege. Administrative remediation of blacklisted accounts becomes impossible.

**Recommended Mitigation:**
Create a separate, explicitly privileged function for owner burns of blacklisted addresses that bypasses the `notBlacklisted` modifier, making the intended capability explicit and safe. Alternatively, restructure `_update` to allow an owner-override path for burn operations.

---

## 16. Owner Can Rescue the Vault's Own Share Tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/sherpa.md`

**Description:**
`SherpaVault::rescueTokens` correctly blocks rescuing the `stableWrapper` token to protect user deposits, but does not block the vault's own share token. When deposits are processed, the vault mints new shares to itself (`address(this)`) as custody for pending deposits and redemptions — `accountingSupply` is incremented and shares are minted to `address(this)`. User redemptions are later fulfilled from this custodied share balance. The owner can call `rescueTokens` on the vault's own share token address to transfer these custodied shares out of the vault, after which they can be redeemed for the underlying assets.

**Impact:**
Owner or a compromised owner key can extract vault-custodied shares that back users' pending deposits and redemption balances, effectively stealing those funds from users who are awaiting settlement.

**Recommended Mitigation:**
Extend the rescue token restriction to also prohibit rescuing the vault's own share token by adding `address(this)` to the rescue blacklist alongside `stableWrapper`.

---

## 17. `StandardToken::transferWithPermit` Can Be DoS Attacked by Front-Running `permit`

**Severity:** 🟡 Medium
**Source:** `cyfrin/registry.md`

**Description:**
`StandardToken::transferWithPermit` atomically executes two sequential calls: first `ERC20PermitMixin::permit` (to grant spending approval), then `StandardToken::transferFrom` (to execute the token transfer). Since the permit signature and all its parameters are fully visible in the mempool before the original transaction is mined, any observer can extract the signature and front-run the original transaction by calling `permit` directly. This front-run consumes the user's nonce, causing the original `transferWithPermit` transaction to revert when it attempts to use the now-invalidated signature, making it impossible to atomically grant the approval and execute the transfer.

**Impact:**
The atomic approve-and-transfer pattern is permanently broken by the front-running attack. The intended UX flow for users relying on `transferWithPermit` is completely disrupted, and the transaction cannot be completed through this path after the nonce is consumed.

**Recommended Mitigation:**
Wrap the `permit` call in a try/catch: if it reverts (because the nonce has already been consumed by a front-runner), proceed to check whether the existing allowance is sufficient and continue with `transferFrom` if so, rather than reverting the entire operation.

---

## 18. `TrustService::removeRole` Doesn't Delete Already Owned Entities

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
When `TrustService::removeRole` strips an address of its role (setting it to `NONE`), it does not clean up the entity ownership mappings. The address remains recorded as the owner of any entities it created while holding the role, and all related operators and resources remain linked to those entities. The `onlyEntityOwnerOrAbove` modifier checks entity ownership mappings rather than role status directly, so the role-stripped address still passes the modifier check and can continue calling entity management functions such as `addOperator` and `addResource` for entities it previously owned.

**Impact:**
An address that has been stripped of its role retains unauthorized control over all entities it previously owned, maintaining the ability to add and remove operators and resources from those entities despite having no valid role in the system.

**Recommended Mitigation:**
When removing a role, explicitly clear all entity ownership mappings associated with the address — including `ownersEntities`, `entityByOperator`, and `entityByResource` — to ensure the address fully loses all entity management access upon role removal.

---

## 19. Untrusted Contract Remains Callable via Whitelisted Function After Trust Revocation

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Dexalot.txt`

**Description:**
`OmniVaultExecutor` maintains a `whitelistedFunctions` mapping (function selector → contract address) that `OMNITRADER_ROLE` holders can invoke via the contract's `fallback` handler. When adding a new whitelisted function via `_setWhitelistedFunction`, the contract correctly verifies that the target is currently trusted. However, when an admin calls `setTrustedContract(_contract, ContractAccess.NONE)` to revoke trust from a contract, the revocation only updates the `trustedContracts` mapping — it does not remove the contract's entries from `whitelistedFunctions`. The `fallback` function only checks that `whitelistedFunctions[sig] != address(0)` and does not re-verify the current trust status of the target, so `OMNITRADER_ROLE` can still call functions on the now-untrusted contract.

**Impact:**
Trust revocation is ineffective at preventing `OMNITRADER_ROLE` from calling functions on a contract that the admin has explicitly designated as untrusted. The entire purpose of the trust control system is defeated for previously-whitelisted functions.

**Recommended Mitigation:**
Either clean up all `whitelistedFunctions` entries pointing to a contract when its trust is revoked, or add a current trust status re-check in the `fallback` function before delegating execution to the target contract.

---

## 20. WLFI Owner Can DoS Legacy Users Through Direct Vester Activation

**Severity:** 🟡 Medium
**Source:** `cyfrin/wlf.md`

**Description:**
`WorldLibertyFinancialVester::ownerActivateVest` allows the owner to directly activate a user's vesting with arbitrary `category` and `amount` parameters, bypassing the normal coordinated activation flow that reads these parameters from the registry (`WLFI V2 → Registry::wlfiActivateAccount → Vester::wlfiActivateVest`). The vester's `_activateVest` function prevents double-initialization by reverting with `AlreadyInitialized` if a user's record has already been set. If the owner uses `ownerActivateVest` to activate a legacy user — whether with incorrect parameters, or even with correct ones but ahead of the user — the user is permanently locked out of the normal activation path. In the case of incorrect parameters, the user is stuck with wrong vesting terms and cannot self-correct.

**Impact:**
Owner can cause a permanent denial-of-service for any legacy user's activation, leaving them with incorrectly configured vesting parameters (wrong category, wrong allocation amount) they have no mechanism to override or correct.

**Recommended Mitigation:**
For legacy users, add validation in `ownerActivateVest` to verify that the provided parameters match the registry data before proceeding. Automatically sync registry state to mark the account as activated. Alternatively, remove `ownerActivateVest` entirely to eliminate this attack surface.
