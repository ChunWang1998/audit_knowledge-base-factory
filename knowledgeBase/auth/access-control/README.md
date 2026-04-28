# auth/access-control - Issues

- Count: 23

## F-2026-15149 - Missing Access Control on verifyAndMarkCompleteEnables Proof Grie ng A ack
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The ProofSystemUpgradeable contract implements access control for recordVerifiedProof but fails to implement the same protection for verifyAndMarkComplete and verifyBatch. The recordVerifiedProof function requires authorization: function `recordVerifiedProof(bytes32 proofHash)` external { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unau thorized"); verifiedProofs[proofHash] = true; emit ProofVerified(proofHash, `msg.sender`, 0); } However, verifyAndMarkComplete has no access control: function `verifyAndMarkComplete(bytes calldata proof, address prover, uint256 claimedTokens)` external returns (bool) { // First verify using internal function if (!`_verifyHostSignature`(proof, prover, claimedTokens)) { return false; emit `ProofVerified(proofHash, prover, claimedTokens)`; return true; } Similarly, verifyBatch lacks access control: function `verifyBatch(bytes[] calldata proofs, address prover, uint256[] calld ata tokenCounts)` external returns (bool) { … 49 for (uint256 i = 0; i < proofs.length; i++) { // Verify each proof using internal function require(`_verifyHostSignatureInternal`(proofs[i], prover, tokenCoun ts[i]), "Invalid proof at index"); proofHashes[i] = proofHash; totalTokens += tokenCounts[i]; } emit `BatchProofVerified(proofHashes, prover, totalTokens)`; } The replay prevention mechanism (verifiedProofs mapping) becomes adenial-of-service vector when anyone can mark proofs as “verified.” Front-Running Griefing Attack Scenario: Host creates a valid proof and signs it Host submits submitProofOfWork transaction to mempool Attacker observes the pending transaction and extracts proof data Attacker front-runs with direct call `toproofSystem.verifyAndMarkComplete(proof, host, tokens)` Attacker's transaction executes first, markingverifiedProofs[proofHash] = true Host's `submitProofOfWork()` transaction executes but fails at thereplay check in `_verifyHostSignature`(): if (verifiedProofs[proofHash]) return false; Host's legitimate proof submission reverts with "Invalid proofsignature" Host must generate a completely new proof with different data to tryagain Attacker can repeat this indefinitely, preventing the host from eversubmitting proofs Attackers can prevent hosts from submitting valid proofs by front-runningand "burning" their proof hashes. Hosts unable to submit proofs cannotearn payment for legitimate work performed. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#]src/ProofSystemUpgradeable.sol [https://github.com/Fabstir/fabstir-compute-contracts#] 50 Status: Fixed

### 修補方式（建議）
Add access control to verifyAndMarkComplete and verifyBatch to ensure onlyJobMarketplaceWithModelsUpgradeable contract can call them. Resolution: Fixed in 0606d07: verifyAndMarkComplete and verifyBatch are no longer present inProofSystemUpgradeable. The replay-protection write path has beenconsolidated into markProofUsed, which enforces access control through authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`. function `markProofUsed( bytes32 proofHash, address prover, uint256 claimedTokens, bytes32 modelId )` external override returns (bool) { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unauthor ized"); } JobMarketplaceWithModelsUpgradeable now calls markProofUsed duringproof submission, removing the previously exposed public verificationendpoints that enabled front-running griefing through unauthorized proofpre-marking.

### 修補方式（實際）
Fixed in 0606d07: verifyAndMarkComplete and verifyBatch are no longer present inProofSystemUpgradeable. The replay-protection write path has beenconsolidated into markProofUsed, which enforces access control through authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`. function `markProofUsed( bytes32 proofHash, address prover, uint256 claimedTokens, bytes32 modelId )` external override returns (bool) { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unauthor ized"); } JobMarketplaceWithModelsUpgradeable now calls markProofUsed duringproof submission, removing the previously exposed public verificationendpoints that enabled front-running griefing through unauthorized proofpre-marking.

## F-2026-15235 - Users Can Renounce BLACKLISTED_ROLE and BypassAdministrative Restrictions
- 嚴重度：High
- Report source：Overlayer.pdf

### 問題內容（完整）
The OverlayerWrap stablecoin contract implements a `BLACKLISTED_ROLE` mechanism to restrict specific accounts from transferring tokens. Thisrestriction is enforced using OpenZeppelinʼs AccessControl library. function `disableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_grantRole`(`BLACKLISTED_ROLE`, account_); emit `DisableAccount(account_)`; } The OverlayerWrap contract inherits from SingleAdminAccessControl,which itself utilizes OpenZeppelinʼs AccessControl library. OpenZeppelinʼsAccessControl includes a public `renounceRole()` function that allows anyaccount to renounce a role assigned to itself. WhileSingleAdminAccessControl overrides `renounceRole()` to prevent directrenouncement of the `DEFAULT_ADMIN_ROLE`, there is no additional override orrestriction in the current OverlayerWrap implementation to preventrenouncement of the `BLACKLISTED_ROLE`. // `SingleAdminAccessControl.sol` function `renounceRole( bytes32 role_, address account_ )` public virtual override `notAdmin(role_)` { `super.renounceRole(role_, account_)`; } modifier `notAdmin(bytes32 role_)` { if (role_ == `DEFAULT_ADMIN_ROLE`) revert `InvalidAdminChange()`; _; } An account that has been assigned the `BLACKLISTED_ROLE` can call renounceRole(`BLACKLISTED_ROLE`, `msg.sender`) and independently remove the 10 restriction, effectively bypassing the blacklist mechanism. Given that,blacklisted users can remove their blacklist status and regain full transfer,mint and reedem functionality, effectively bypassing the administrativecontrol mechanism. This behavior undermines the intended blacklist enforcement logic. Theblacklist is expected to be an administrative control used to restrictmalicious, sanctioned, or non-compliant accounts. If users can removetheir own blacklist status, the restriction becomes ineffective and cannotbe reliably enforced. Assets: `contracts/overlayer/OverlayerWrap.sol`[https://github.com/Overlayerfi/contracts/tree/main]contracts/shared/SingleAdminAccessControl.sol[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed

### 修補方式（建議）
Consider overriding the `renounceRole()` function in the OverlayerWrapcontract to prevent accounts from renouncing the `BLACKLISTED_ROLE` themselves. Alternatively, disable `renounceRole()` entirely if self-removal of roles is notrequired within the protocolʼs access control design. This ensures that onlyauthorized administrators can manage blacklist assignments andpreserves the integrity of the restriction mechanism. Resolution: Fixed in 2f2f9d4, the `renounceRole()` function was overridden to preventaccounts from renouncing the `BLACKLISTED_ROLE` themselves: function `renounceRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotRenounceBlacklist()`; 11 `super.renounceRole(role_, account_)`;

### 修補方式（實際）
Fixed in 2f2f9d4, the `renounceRole()` function was overridden to preventaccounts from renouncing the `BLACKLISTED_ROLE` themselves: function `renounceRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotRenounceBlacklist()`; 11 `super.renounceRole(role_, account_)`;

## F-2026-15242 - Default Admin Can Assign Blacklisted Role WithoutEnforcing Blacklist Activation Constraints
- 嚴重度：Medium
- Report source：Overlayer.pdf

### 問題內容（完整）
The OverlayerWrap token implements a blacklisting mechanism byassigning the `BLACKLISTED_ROLE` using OpenZeppelinʼs AccessControllibrary. Accounts that are granted the blacklisted role are restricted fromperforming minting, redeeming, and transfer operations. The contractintroduces the blacklistActivationTime variable, which defines when theblacklist functionality becomes active. Until the activation time is reached,blacklist operations are not intended to be applied to any account. The `disableAccount()` function allows accounts to be added to the blacklistby the `CONTROLLER_ROLE`: function `disableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_grantRole`(`BLACKLISTED_ROLE`, account_); emit `DisableAccount(account_)`; } function `enableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_revokeRole`(`BLACKLISTED_ROLE`, account_); emit `EnableAccount(account_)`; } The blacklistAllowed modifier enforces the activation timing restriction: modifier `blacklistAllowed()` { if ( blacklistActivationTime == 0 || blacklistActivationTime + `BLACKLIST_ACTIVATION_TIME` > `block.timestamp` ) { revert `OverlayerWrapBlacklistNotActive()`; } _; } However, the contract inherits OpenZeppelinʼs AccessControl, whichexposes the public `grantRole()` and `revokeRole()` functions. The `DEFAULT_ADMIN_ROLE` can therefore call grantRole(`BLACKLISTED_ROLE`, account) 21 directly. This direct call does not enforce the blacklistAllowed modifier andtherefore does not apply the intended activation-time restriction.. As aresult, the default admin can blacklist (or remove blacklist via `revokeRole()`)accounts at any time, regardless of the configured activation logic. The same pattern is applied in the StakedOverlayerWrapCore contract forblacklisting functionality. The contract exposes `addToBlacklist()` and `removeFromBlacklist()` functions,which are restricted to accounts holding the `CONTROLLER_ROLE`. Thesefunctions are additionally protected by the blacklistAllowed modifier, whichensures that the blacklist mechanism is active. The blacklistAllowed modifier verifies that blacklistActivationTime > 0 and that redistribution is notenabled, thereby enforcing that blacklist operations can only be performedwhen the blacklist functionality is properly activated. function `addToBlacklist( address target_, bool isFullBlacklisting_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) `notOwner(target_)` { bytes32 role = isFullBlacklisting_ ? `WHOLE_RESTRICTED_ROLE` : `STAKE_RESTRICTED_ROLE`; `_grantRole`(role, target_); } function `removeFromBlacklist( address target_, bool isFullBlacklisting_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { bytes32 role = isFullBlacklisting_ ? `WHOLE_RESTRICTED_ROLE` : `_revokeRole`(role, target_); } modifier `blacklistAllowed()` { if (blacklistActivationTime == 0) { revert `StakedOverlayerWrapCannotBlacklist()`; } if ( blacklistActivationTime + `BLACKLIST_ACTIVATION_TIME` > `block.timestamp` || redistributionActivationTime > 0 ) { revert `StakedOverlayerWrapCannotBlacklist()`; } 22 _; } The default admin may directly invoke `grantRole()` or `revokeRole()` for `STAKE_RESTRICTED_ROLE` or `WHOLE_RESTRICTED_ROLE`. Consequently, the admin canassign blacklist-related roles at any time, regardless of whether blacklistActivationTime has been reached, thereby circumventing theintended activation restrictions. This can lead to: The intended blacklist activation delay restriction logic is notconsistently enforced.A mismatch between declared behavior and actual enforceablebehavior, potentially impacting user trust and protocol transparency. Assets: `contracts/overlayer/OverlayerWrap.sol`[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed

### 修補方式（建議）
To ensure consistent enforcement of blacklist activation rules: Override `grantRole()` and `revokeRole()` in the OverlayerWrap andStakedOverlayerWrapCore contract to prevent direct assignment orremoval of `BLACKLISTED_ROLE` / `WHOLE_RESTRICTED_ROLE` / `STAKE_RESTRICTED_ROLE` via the public AccessControl interface by the `DEFAULT_ADMIN_ROLE`.Enforce the blacklistAllowed restriction within any logic path thatassigns `BLACKLISTED_ROLE` / `WHOLE_RESTRICTED_ROLE` / `STAKE_RESTRICTED_ROLE`. This ensures that all blacklisting actions follow the intended activationconstraints and preserves the integrity of the protocolʼs expected behavior. 23 Resolution: Fixed in e9f1389, `grantRole()` and `revokeRole()` functions were overridden inthe OverlayerWrap and StakedOverlayerWrapCore contract to preventdirect assignment or the custom role that reguire blacklistAllowed validation: // `OverlayerWrap.sol` function `grantRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.grantRole(role_, account_)`; } function `revokeRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.revokeRole(role_, account_)`; } // `StakedOverlayerWrapCore.sol` function `grantRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } function `revokeRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } 24

### 修補方式（實際）
Fixed in e9f1389, `grantRole()` and `revokeRole()` functions were overridden inthe OverlayerWrap and StakedOverlayerWrapCore contract to preventdirect assignment or the custom role that reguire blacklistAllowed validation: // `OverlayerWrap.sol` function `grantRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.grantRole(role_, account_)`; } function `revokeRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.revokeRole(role_, account_)`; } // `StakedOverlayerWrapCore.sol` function `grantRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } function `revokeRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } 24

## F-2025-13782 - Unauthorized Delegation via `migrateAndDelegate()`Function
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `migrateAndDelegate()` function in the `Stargate.sol` contract lacksownership verification, allowing any user to migrate another user's legacytoken and delegate it to an arbitrary validator of the attacker's choice.While the token ownership is correctly assigned to the legitimate ownerafter migration, the delegation is controlled by the attacker. The token owner is able to stop the token delegation. The migrateAndDelegate requires `VET` to be attached and the `VET` can bewithdrawn only by the legitimate token owner via unstake. However, theattacker may receive profit by migrating abandoned X tokens whichprovide the 1.5x validator rewards multiplier. `Stargate.sol`: function migrateAndDelegate( uint256 `_tokenId`, address `_validator` ) external payable whenNotPaused nonReentrant { StargateStorage storage $ = `_getStargateStorage`(); // `VULNERABLE` `ENTRY` `POINT`: No ownership verification // Anyone can call this function with any `_tokenId` // get the level of the node from the legacy nodes contract (, uint8 level, , , , , ) = $.`stargateNFTContract.legacyNodes()`.getMetada ta(`_tokenId`); // get the vet amount required to stake for the level uint256 vetAmountRequiredToStake = $ .stargateNFTContract .`getLevel(level)` .vetAmountRequiredToStake; // validate the `msg.value` if (`msg.value` != vetAmountRequiredToStake) { revert VetAmountMismatch(level, vetAmountRequiredToStake, `msg.value`); } // migrate the token to the StargateNFT contract // [!] No check that `msg.sender` owns `_tokenId` $.stargateNFTContract.migrate(`_tokenId`); // delegate the token to the validator 42 // [!] Allows attacker to choose the validator `_delegate`($, `_tokenId`, `_validator`); } The function performs the following actions without verifying that `msg.sender` owns the legacy token: Retrieves metadata from the legacy token contract Validates that `msg.value` matches the required `VET` amount Calls migrate(`_tokenId`) which mints the new token to the legacy `owner(correct)` Calls `_delegate`($, `_tokenId`, `_validator`) which delegates to the caller'schosen validator (incorrect) The `_delegate`() internal function assumes that the calling function hasalready verified ownership, but `migrateAndDelegate()` violates thisassumption. In contrast, the public `delegate()` function properly enforcesownership through the onlyTokenOwner(`_tokenId`) modifier. Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
Add ownership verification at the beginning of the `migrateAndDelegate()` function to ensure only the legitimate legacy token owner can migrate anddelegate their token. This aligns the function's access control with otherdelegation-related functions in the contract: modifier onlyLegacyTokenOwner(uint256 `_tokenId`) { StargateStorage storage $ = `_getStargateStorage`(); address legacyOwner = $.`stargateNFTContract.legacyNodes()`.idToOwner(`_toke` nId); 43 if (legacyOwner != `msg.sender`) { revert UnauthorizedUser(`msg.sender`); } _; } function migrateAndDelegate( uint256 `_tokenId`, address `_validator` ) external payable onlyLegacyTokenOwner(`_tokenId`) whenNotPaused nonReentrant { StargateStorage storage $ = `_getStargateStorage`(); rest of the function implementation … } Resolution: The finding is fixed in commit hash 4574d8b after adding the onlyLegacyTokenOwner(`_tokenId`) modifier to the `migrateAndDelegate()` function.The new modifier validates that `msg.sender` is the legitimate owner of thelegacy token by checking `legacyNodes()`.idToOwner(`_tokenId`), preventingunauthorized users from migrating and delegating other users' tokens toarbitrary validators.

### 修補方式（實際）
The finding is fixed in commit hash 4574d8b after adding the onlyLegacyTokenOwner(`_tokenId`) modifier to the `migrateAndDelegate()` function.The new modifier validates that `msg.sender` is the legitimate owner of thelegacy token by checking `legacyNodes()`.idToOwner(`_tokenId`), preventingunauthorized users from migrating and delegating other users' tokens toarbitrary validators.

## F-2026-15334 - Delegate Spending Cap Bypass via Token SelectionAllows Draining Payer Funds Beyond Intended Limits
- 嚴重度：High
- Report source：Fabstir.pdf

### 問題內容（完整）
The DelegateConfig struct provides spending controls (maxPerSession, totalCap, spent) to protect payers against delegate overspending or keycompromise. However, these controls compare raw token amounts withoutany reference to which token is being used. The struct has no allowedToken field, and the delegate freely selects the payment token at sessioncreation: function `createSessionForModelAsDelegate( address payer, bytes32 modelId, address host, address paymentToken, uint256 amount, uint256 pricePerToken, uint256 maxDuration, uint256 proofInterval, uint256 proofTimeoutWindow )` external nonReentrant whenNotPaused returns (uint256 sessionId) { require(payer != `address(0)`, "No payer"); if (`msg.sender` != payer) { DelegateConfig storage dc = delegateConfigs[payer][`msg.sender`]; `require(dc.active, "Not delegate")`; if (dc.validUntil > 0) require(`block.timestamp` <= dc.validUntil, " Expired"); if (dc.maxPerSession > 0) `require(amount <= dc.maxPerSession, "Ove r limit")`; if (dc.totalCap > 0) `require(dc.spent + amount <= dc.totalCap, "Ov er cap")`; if (dc.allowedHost != `address(0)`) `require(host == dc.allowedHost, "Wrong host")`; if (dc.allowedModel != `bytes32(0)`) `require(modelId == dc.allowedMo del, "Wrong model")`; `require(amount <= type(uint128)`.max, "Overflow"); dc.spent += `uint128(amount)`; } // … rest of the code } Since accepted tokens can have different decimals (e.g., `USDC` with 6, DAIwith 18 , the same raw totalCap value represents vastly different tokenquantities depending on which token the delegate chooses. The 25 cumulative spent counter compounds the problem by summing rawamounts across sessions that may use entirely different tokens. The spending cap is the primary safeguard protecting payers whendelegating session creation to third-party accounts. A malicious delegatecan bypass the intended limit by selecting a token with fewer decimalsthan what the payer calibrated the cap for, pulling funds up to the payer'stoken approval and tokenMaxDeposits ceiling rather than the intended cap.The spent counter also becomes a meaningless accounting record since itsums raw amounts of tokens with different decimals. Found in commit : df1f2e4. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
Restructure the delegate config mapping to be per-token, so that spendingcontrols are always denominated in the same token they apply to: // payer => delegate => token => DelegateConfig `mapping(address => mapping(address => mapping(address => DelegateConfig)`)) pu blic delegateConfigs; Update `configureDelegate()` to accept a token parameter, allowing payers toset separate limits for each token: function `configureDelegate( address delegate, address token, uint128 maxPerSession, uint128 totalCap, uint64 validUntil, 26 address[] allowedHost, bytes32[] allowedModel )` external { … } Resolution: An allowedToken field has been added to DelegateConfig and is enforced in `createSessionForModelAsDelegate()`, allowing payers to restrict delegates to aspecific payment token and ensuring spending caps are denominated in asingle token's units. However, it should be noted that this approach onlyallows configuring a delegate for a single token, host, and model perdelegate address — payers who need a delegate to operate acrossmultiple tokens, hosts, or models must either grant unrestricted access ormanage separate delegate addresses for each combination. function `createSessionForModelAsDelegate(…)` external nonReentrant whenN otPaused returns (uint256 sessionId) { require(payer != `address(0)`, "No payer"); if (`msg.sender` != payer) { DelegateConfig storage dc = delegateConfigs[payer][`msg.sender`]; `require(dc.active, "Not delegate")`; if (dc.validUntil > 0) require(`block.timestamp` <= dc.validUntil, " Expired"); if (dc.maxPerSession > 0) `require(amount <= dc.maxPerSession, "Ove r limit")`; if (dc.totalCap > 0) `require(dc.spent + amount <= dc.totalCap, "Ov er cap")`; if (dc.allowedHost != `address(0)`) `require(host == dc.allowedHost, "Wrong host")`; if (dc.allowedModel != `bytes32(0)`) `require(modelId == dc.allowedMo del, "Wrong model")`; if (dc.allowedToken != `address(0)`) `require(paymentToken == dc.allo wedToken, "Wrong token")`; `require(amount <= type(uint128)`.max, "Overflow"); dc.spent += `uint128(amount)`; rest of the code } Revised commit: fba54b2. 27

### 修補方式（實際）
An allowedToken field has been added to DelegateConfig and is enforced in `createSessionForModelAsDelegate()`, allowing payers to restrict delegates to aspecific payment token and ensuring spending caps are denominated in asingle token's units. However, it should be noted that this approach onlyallows configuring a delegate for a single token, host, and model perdelegate address — payers who need a delegate to operate acrossmultiple tokens, hosts, or models must either grant unrestricted access ormanage separate delegate addresses for each combination. function `createSessionForModelAsDelegate(…)` external nonReentrant whenN otPaused returns (uint256 sessionId) { require(payer != `address(0)`, "No payer"); if (`msg.sender` != payer) { DelegateConfig storage dc = delegateConfigs[payer][`msg.sender`]; `require(dc.active, "Not delegate")`; if (dc.validUntil > 0) require(`block.timestamp` <= dc.validUntil, " Expired"); if (dc.maxPerSession > 0) `require(amount <= dc.maxPerSession, "Ove r limit")`; if (dc.totalCap > 0) `require(dc.spent + amount <= dc.totalCap, "Ov er cap")`; if (dc.allowedHost != `address(0)`) `require(host == dc.allowedHost, "Wrong host")`; if (dc.allowedModel != `bytes32(0)`) `require(modelId == dc.allowedMo del, "Wrong model")`; if (dc.allowedToken != `address(0)`) `require(paymentToken == dc.allo wedToken, "Wrong token")`; `require(amount <= type(uint128)`.max, "Overflow"); dc.spent += `uint128(amount)`; rest of the code } Revised commit: fba54b2. 27

## F-2025-14057 - Recover Function Can Steal User Funds - Medium
- 嚴重度：Medium
- Report source：A Two Tech Limited.pdf

### 問題內容（摘要）
The recover() function allows the admin to withdraw any amount of ATWOtokens from the contract at any time without restrictions. This creates thesame risk as ATWODistributor's emergency withdraw - the malicious admincan steal tokens that are rightfully owed to users based on their presalecontributions, rendering the contract insolvent. Impact: Admin can withdraw ATWO tokens that belong to users whopurchased in the presaleUsers will be unable to claim their purchased tokens after TGEContract becomes insolvent without warningDefeats the purpose of a fair distribution mechanismHigh centralization risk that users should be aware of Example Scenario:    Users purchased 100,000 ATWO total in presale   Contract is seeded with 100,000 ATWO for distribution   Admin calls recover(adminAddress, 100000)    TGE happens, users try to claim   All claim() calls fail due to insufficient balance   Users lost their purchased tokens ATWODistributor.sol: function recover(address to, uint256 amount) external onlyRole(ADMIN_ROLE) { atwo.safeTransfer(to, amount); // No checks on user entitlements }

### 修補方式（實際）
The finding is fixed in commit e069e6f after the suggested fix wasimplemented in the code. Grace period check was added for the recover() function. 10


## F-2025-14066 - Excessive Emergency Withdraw Can Steal UserFunds - Medium
- 嚴重度：Medium
- Report source：A Two Tech Limited.pdf

### 問題內容（摘要）
The ATWOVesting.emergencyWithdraw() function allows the admin to withdrawany amount of tokens from the contract at any time, with no restrictions.This can be used to steal vested tokens that rightfully belong to users,rendering the contract insolvent and preventing users from claiming theirentitled tokens. Impact: Admin can withdraw tokens reserved for user vesting schedulesUsers will be unable to claim vested tokens when the contract hasinsufficient balanceContract becomes insolvent without any warning or recourse for usersWhile named "emergency," there are no actual emergency conditionscheckedComplete centralization risk that defeats the purpose of a vestingcontract ATWOVesting.sol: function emergencyWithdraw(address to, uint256 amount) external onlyRole(ADMI N_ROLE) { if (to == address(0)) revert ZeroAddress(); if (amount == 0) revert AmountZero(); vestedToken.safeTransfer(to, amount); // No checks on reserved amounts emit EmergencyWithdraw(to, amount); }

### 修補方式（實際）
The finding is fixed in commit e069e6f after the suggested fix (removal of emergencyWithdraw() function) was applied in the code. 16


## F-2025-14074 - Admin Can Arbitrarily Decrease User’s VestingAmount Bypassing User Entitlement - Medium
- 嚴重度：Medium
- Report source：A Two Tech Limited.pdf

### 問題內容（摘要）
The ATWOVesting contract allows the admin to create linear vestingschedules via the setSchedule() function. This function can be called toupdate the total vesting amount for an existing schedule at any time. However, there is no restriction preventing the admin from reducing thetotal vesting amount of an ongoing schedule below the amount alreadyaccrued but not yet claimed by the beneficiary. This effectively allows theadmin to revoke a userʼs legitimate entitlement, resulting in loss of tokensthat the user has already vested by time progression. function setSchedule( address user, uint64 startTime, uint64 cliffDuration, uint64 vestingDuration, uint256 total ) external onlyRole(ADMIN_ROLE) { if (user == address(0)) revert ZeroAddress(); // Requirements: startTime > 0, vestingDuration > 0; cliffDuration can be 0 if (!(startTime > 0 && vestingDuration > 0)) revert InvalidSchedule(start Time, cliffDuration, vestingDuration); VestingSchedule storage schedule = scheduleByUser[user]; // Preserve claimed value if schedule already exists uint256 alreadyClaimed = schedule.claimed; // New total must be >= already claimed if (total < alreadyClaimed) { // Treat as invalid schedule if trying to

### 修補方式（實際）
The finding is fixed in commit e069e6f after the suggested fix wasimplemented in the code. New check now ensure the new total cannot fallbelow already vested amount. 21


## F-2025-14436 - Blacklisted Token Recipient Permanently Blocks FIFOForced Withdrawals - High
- 嚴重度：High
- Report source：BullBit.pdf

### 問題內容（摘要）
The protocol implements a forced withdrawal queue (InclusionQueue) as anescape hatch mechanism, allowing users to bypass sequencer controlwhen needed. The Verifier contract processes these requests in strictFIFO order, requiring:    Processing must start from the next unprocessed index(nextPoolRequestToProcessIndex / nextVaultRequestToProcessIndex)   Requests must be processed contiguously (no skipping) The vulnerability arises because:    Token transfers use safeTransfer which reverts on failure   Tokens like USDC/USDT implement address blacklisting (for OFACsanctions, fraud, etc.)   If a blacklisted address is at the front of the queue, the transfer reverts   Due to FIFO constraints, no subsequent requests can be processed   There is no mechanism to skip or mark failed requests Pool.sol - executeOnChainWithdrawal() function executeOnChainWithdrawal( address user, address token, uint256 amount ) external onlyWMOrVRF { require(user != address(0), "Pool: user 0x"); require(token != address(0), "Pool: token 0x"); require(amount > 0, "Pool: amount = 0"); uint256 bal = balances[user][token]; require(bal >= amount, "Pool: insufficient"); balances[user][token] = bal - amount; IERC20(toke

### 修補方式（實際）
The submitPoolUpdateBatch() and submitVaultUpdateBatch() functions nowimplement try-catch mechanisms. In case of any failure, the transaction 15 just emits an event and continues with the execution by deleting the forcedwithdrawal request from the system. Revised commit: 322258e function submitPoolUpdateBatch(…) { //... rest of the code if (forcedCount > 0) { uint256 nextIdx = IQueueForVerifier(inclusionQueueContract).nextPo olRequestToProcessIndex(); for (uint256 k = 0; k < forcedCount; k++) { uint256 queueIndex = nextIdx + k; (, address u, address token, uint256 amount, uint256 ts) = IQu eueForVerifier(inclusionQueueContract).poolQueue(queueIndex); if (block.timestamp < ts + forcedDeadline) { revert Verifier_N otOverDue(); } uint256 bal = IPoolForVerifier(poolContract).balances(u, token ); uint256 execAmount = bal < amount ? bal : amount; if (execAmount == 0) { emit OverdueRequestProce


## F-2025-14487 - Forced Withdrawal Flow Is Not Fully Censorship-Resistant - Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
According to the documentation, the InclusionQueue contract is describedas a dedicated mechanism allowing on-chain withdrawal requests thatcannot be ignored, intended to function as an anti-censorship tool. A dedicated contract allowing users to register on-chainwithdrawal requests that the Sequencer cannot ignore. Core anti-censorship tool. However, based on the current implementation and design choices, theforced withdrawal flow is not fully independent and may be censored orblocked by the sequencer or privileged roles. First, the creation of forced withdrawal requests can be restricted orrendered economically infeasible due to unbounded and immediatelyapplied values of feeAmount and minWithdrawAmount. These parameters arecontrolled by a privileged role and lack reasonable upper limits. As a result,withdrawal requests for smaller balances can be prevented, or allwithdrawals can be effectively blocked by setting excessively high values.Reported in F-2025-14485 Second, regardless of whether a withdrawal request is finalized throughnormal sequencing or through the processOverdueQueueItem(), successfulexecution remains dependent on the off-chain sequencer component. Ifthe internal ba

### 修補方式（實際）
The issue was fixed in commit 322258e. In the forced withdrawal flow, if auserʼs balance is decreased after the request is created, the remaininginternal balance will be transferred instead of reverting. 35


## F-2025-13556 - Unvalidated Market Address Leads To ArbitraryToken Approvals - Medium
- 嚴重度：Medium
- Report source：Dirol.pdf

### 問題內容（摘要）
In the Crystal path, market is decoded from untrusted pathData andused as the spender in _ensureAllowance. There’s no check that marketis valid for the selected router/pair. This lets callers set approvals toany address. (address market, address referrer) = abi.decode(pathData, (address, address)) ; // ... _ensureAllowance(tokenIn, market, amountIn); ICrystalRouter(router).swapExactTokensForTokens( amountIn, minAmountOut, path, address(this), block.timestamp, referrer ); function _ensureAllowance(address token, address spender, uint256 amount) pri vate { if (token == NATIVE || amount == 0) return; IERC20(token).forceApprove(spender, amount); } This allows arbitrary address to gain allowance from the aggregatorfor tokenIn. If any tokenIn remains (dust, partial ﬁlls, future deposits),that address can call transferFrom the aggregator.

### 修補方式（實際）
The Finding was ﬁxed in commit 951c013. The _ensureAllowance(tokenIn, market, amountIn); call was removed. 42


## F-2024-7557 - Stuck Order Matching Due to Blacklisted Addresses- High
- 嚴重度：High
- Report source：EverValue Coin.pdf

### 問題內容（摘要）
The OrderBookFactory contract faces an issue when matching buy or sellorders. If an order involves a creator's address that has beenblacklisted by the token contract (e.g., a token implementingblacklist functionality), the transfer of funds between the buyer andseller will fail. This failure prevents the system from proceeding tothe next price point, eﬀectively causing the matching process to haltindeﬁnitely at the problematic price level. Stalled Order Matching: The matching process cannot move past the blacklisted order,blocking all subsequent orders at that price point or higher/lower(depending on buy/sell direction).This creates a signiﬁcant bottleneck in the order book, reducingits eﬃciency and usability. Permanent Price Point Blockage: Price points with blacklisted addresses become unusable,causing funds to remain locked and orders to stay unresolvedindeﬁnitely. Aﬀected functions: function fillOrder(Pair storage pair, OrderBookLib.Order storage matc hedOrder, OrderBookLib.Order memory takerOrder) private { // Update the last trade price for the pair pair.lastTradePrice = matchedOrder.price; // Determine which tokens are being received and sent by the taker, a nd their amounts

### 修補方式（實際）
The EverValue Coin team implemented a pull-over-push pattern toprevent stuck orders that disrupt the orderbook mechanism. 11 (Revised commit: a958f6e) Evidences PoC


## F-2025-13251 - Lack of Contract Address in Signed Payload Leadsto Cross-Collection Replay Risk - Medium
- 嚴重度：Medium
- Report source：Panini America.pdf

### 問題內容（摘要）
The PaniniNFTs contract’s signature veriﬁcation logic in _verifySignature() internal function builds the signed message withoutincluding the current collection’s own contract address (address(this))in the signature payload. The current encoded message is: bytes memory message = abi.encode( block.chainid, _msgSender(), tokenIds, tokenURIs, requestNonce, expiredAt ); require(_verifySignature(message, signature), "Invalid signature"); ... function _verifySignature( bytes memory message, bytes memory signature ) internal view returns (bool) { bytes32 messageHash = keccak256(message); bytes32 digest = MessageHashUtils.toEthSignedMessageHash(messageHash) ; address signer = ECDSA.recover(digest, signature); return hasRole(PANINI_NFT_OPERATOR, signer); } The _verifySignature() ECDSA-recovers an address with toEthSignedMessageHash and checks the PANINI_NFT_OPERATOR role. Because address(this) is omitted, the recovered signature is not bound to aspeciﬁc contract instance. This design means signatures are onlybound to the chain ID, sender, and parameters, but not to thespeciﬁc NFT collection contract. If the same operator key is used across multiple collections on thesame chain, (e.g., new de

### 修補方式（實際）
The ﬁnding was ﬁxed in commit hash f070187. The suggested ﬁx wasimplemented for extra prevention. 18


## F-2025-14257 - Owner Authorization Allows Arbitrary Burning ofSoulbound Tokens - Medium
- 嚴重度：Medium
- Report source：RYT-2.pdf

### 問題內容（摘要）
The SoulboundCredential contract extends the ERC721 standard and disablesany token transfer after minting to ensure that each credential remainsbound to the original recipient. The contract includes a burnCredential() function for destroying existing credentials. function burnCredential(uint256 tokenId) external validCredential(tokenId) whenNotPaused nonReentrant { require( ownerOf(tokenId) == msg.sender || credentialInfo[tokenId].issuer == msg.sender || msg.sender == owner(), "SoulboundCredential: Not authorized to burn this credential" ); // ... } The access control logic in this function grants the contract owner theability to burn tokens belonging to any address. As a result, soulboundtokens can be destroyed at any time by the owner. In the event of ownerkey compromise, the likelihood of unauthorized token destructionincreases.

### 修補方式（實際）
Fixed in a695108, the owner of the contract was excluded from theauthorized accounts who can burn the credentials. Only owner of thecredential or the credential issuer can burn: if ( ownerOf(tokenId) != msg.sender && credentialInfo[tokenId].issuer != msg.sender ) { revert NotAuthorizedBurn(); } 14


## F-2025-14229 - Missing USER_ROLE Check Allows UnauthorizedParticipants in Joint Groups And Payouts - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The function joinGroupWithJointContributor() allows a user to join a groupwith a secondary contributor but lacks a check to verify that the secondarycontributor has been granted the required USER_ROLE. This allowsregistration of secondary contributors who do not have the necessarypermissions to participate in the system, potentially causing permissioninconsistencies and unexpected behavior. function joinGroupWithJointContributor(uint256 groupId, address secondaryCon tributor) external payable whenNotPaused checkIfGroupExit(groupId) onlyRole(USER_ROLE) { require(secondaryContributor != address(0), "Komiti: Zero Address not allowed"); Group storage group = s_groups[groupId]; require(!group.isPayoutStarted, "Komiti: Cannot join after payout sta rts"); require(block.timestamp < group.joinDeadline, "Komiti: Cannot join af ter deadline"); require(s_contributions[groupId][msg.sender] == 0, "Komiti: User alre ady joined"); require(msg.value >= group.perShareAmount / 2, "Komiti: Incorrect amo unt sent"); // Half for this user and half for secondary contributor require( !s_isJointContributor[groupId][secondaryContributor], "Komiti: Se condary contributor already registered" ); s_jointContrib

### 修補方式（實際）
Fixed in 1829f31. The codebase no longer contains the joinGroupWithJointContributor() functionality. In addition to that, the following USER_ROLE check was implemented in the setPayoutPositions() function: ... if (!hasRole(USER_ROLE, users[i])) revert UserHasNotJoined(); ... 32


## F-2025-14253 - Missing Refund Mechanism for Regular MembersLeads To Stuck Assets - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The smart-contract provides a returnFunds() function, but it only applies tojoint-contributor workflows, allowing a primary contributor to unwind aninvitation before payout starts. function returnFunds(uint256 groupId, address secondaryContributor) external payable checkIfGroupExit(groupId) onlyRole(USER_ROLE) { Group storage group = s_groups[groupId]; require(!group.isPayoutStarted, "Komiti: Cannot return funds after pa yout starts"); require( s_jointContributorPrimary[groupId][secondaryContributor] == msg.s ender, "Komiti: Only primary contributor can return amount" ); require(s_contributionShares[groupId][secondaryContributor] == 0, "Ko miti: Invite already accepted"); s_jointContributorPrimary[groupId][secondaryContributor] = address(0) ; s_isJointContributor[groupId][secondaryContributor] = false; address[] storage secondaryContributors = s_jointContributorsDetails[ groupId][msg.sender].secondaryContributors; for (uint256 i = 0; i < secondaryContributors.length; i++) { if (secondaryContributors[i] == secondaryContributor) { secondaryContributors[i] = secondaryContributors[secondaryCon tributors.length - 1]; secondaryContributors.pop(); break; } } delete s_jointContributorsDeta

### 修補方式（實際）
In commit 1829f31, the public refundMember function that allows anycontributing member to withdraw their funds before the payout cycle starts 36 is introduced, resolving the issue where regular users had no mechanismto reclaim funds from stalled or inactive groups. 37


## F-2025-11617 - Users Can Perform New Tokens Purchase AfterautoRefund() Leading to Underﬂow in claim() - High
- 嚴重度：High
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract enables users to purchase project tokensusing a bonding mechanism and later claim them once the vestingperiod begins. The BondingCurveWritable extension allows the defaultadmin to initiate an automatic refund of the bonded token via the autoRefund() function if the soft cap is not reached. However, during autoRefund(), the user's state is not properly updatedto reﬂect the refund. Speciﬁcally, the user.isRefunded ﬂag is not set totrue, and no adjustments are made to the amountToClaim or amountClaimed ﬁelds. This allows users to buy tokens again in the same bondingcurve after being automatically refunded. But because amountClaimed isset to type(uint256).max during the refund process, it becomesimpossible for that user to claim any newly purchased tokens,leading to a loss of bonded tokens and claimable project tokenamount. BondingCurveWritable::autoRefund(): function autoRefund( address[] calldata userAddresses ) external whenNotPaused onlyRole(DEFAULT_ADMIN_ROLE) { if (userAddresses.length == 0) revert EmptyArray(); BondingCurveStorage.Storage storage strg = BondingCurveStorage.layout (); if (strg.ledger.raisedTokenAmount >= strg.setUp.softCap) revert Refund

### 修補方式（實際）
Fixed in 90b3457: added ﬂag user.isRefunded = true to the autoRefund() function that prevents users from purchasing again on a refundedcurve. Evidences PoC


## F-2025-11742 - Incorrect Handling of reserveFee During dex()Execution - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract deﬁnes a fee structure for the project tokenthat includes several components like reserveFee, teamFee, ecosystemFee, tokenToSellPercent, and lPPercent. These fees are intended to bedistributed to their respective beneﬁciaries when the dex() functionis called, with the exception of tokenToSellPercent, which follows avesting schedule. According to the contract’s logic and documentation, the dex() function should handle the full distribution of fees, including the reserveFee. However, during execution, while most fee componentsare transferred correctly, the reserveFee is not transferred and insteadremains locked in the bonding curve contract. function dex() public onlyRole(DEFAULT_ADMIN_ROLE) { ... IRouter_ETH_BNB_AVAX(router).addLiquidity( ... ) _giveToken(bondedToken, setUp.platformOwner, bondedTaxAmount); _giveToken(bondedToken, setUp.projectOwner, remainingAmount); if (curatorAmount > 0) { _giveToken(bondedToken, setUp.curatorAddress, curatorAmount); } _giveToken(projectToken, setUp.teamWallet, ledger.teamAmount); _giveToken(projectToken, setUp.ecosystemWallet, ledger.ecosystemAmount); uint256 remainingProjectToken = ledger.tokenToSell - ledger.totalProje

### 修補方式（實際）
Fixed in eb0e63e: reservedFee is transferring to the platformOwner addressonce dex() function is called. 26


## F-2025-11752 - Incorrect Fee Math Allows Users to ExceedAllocation - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurveWritable contract facilitates a multi-tiered token salewhere diﬀerent user groups (Tiers, Whitelist, Public Sale.) are givenspeciﬁc purchase allocations. Participation in these private rounds ismanaged by a Merkle tree, where each leaf contains a user'saddress, their maximum allocation, and their designated round.When a user calls the buy function, the _authenticateUser internalfunction is invoked to verify their Merkle proof and check if theircumulative purchase amount is within their speciﬁed allocation.amount.This check is critical for enforcing the sale rules and ensuring a fairdistribution. The mathematical formula used within _authenticateUser to calculate auser's cumulative spend is incorrect. It attempts to reconstruct theuser's total gross (pre-fee) contribution by applying a multiplicativefee factor to their stored net (post-fee) contribution, which under-estimates the true amount spent. This ﬂaw allows any user in aprivate round to systematically purchase more tokens than theiroﬃcial allocation without triggering the ExceedAllocation error, therebybypassing a core security mechanism of the sale. When a user makes a purchase, the contract stores theircontr

### 修補方式（實際）
In commit 5529582, the allocation tracking mechanism is implementedbased on gross amounts. Evidences PoC


## F-2025-14081 - Minting is Allowed for Frozen and Non-WhitelistedAddresses - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken contract includes several compliance and controlmechanisms, such as freezing accounts (setFrozen), locking balances(lockBalance), and enforcing a whitelist (setWhitelistMode). These areprimarily enforced within the overridden _update function, which isthe central hub for all token balance changes, including transfers,minting, and burning. The core compliance checks for frozen accounts and whitelisting areincorrectly scoped, causing them to be completely bypassed duringminting and burning operations. This allows the MINTER role to createnew tokens for addresses that are explicitly frozen or not on thewhitelist, and allows the BURNER role to destroy tokens from a frozenaccount. This undermines the contract's intended regulatory controlsand can lead to tokens becoming permanently stuck in non-compliant wallets. In RealEstateToken.sol, the _update function contains the logic to verify ifan account is frozen or whitelisted. However, all of these checks arewrapped inside a conditional statement that only executes forregular transfers: function _update(address from, address to, uint256 amount) internal override(ERC20Upgradeable, ERC20PausableUpgradeable, ERC20VotesUpgr

### 修補方式（實際）
Fixed in commit ID 8593776: the mint(), burn() and burnFrom() methodswere updated in order to properly avoid minting and burning tokensfrom frozen and non-whitelisted addresses. if (_frozen[to]) revert AccountFrozen(to); if (whitelistEnabled && !_whitelisted[to]) revert NotWhitelisted(to); Evidences PoC


## F-2025-14099 - Compliance Status is Decoupled from VotingPower - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken contract integrates features for on-chaingovernance using OpenZeppelin's ERC20VotesUpgradeable. It alsoimplements several compliance mechanisms, such as freezingaccounts (setFrozen), locking a portion of a user's balance(lockBalance), and enforcing a transfer whitelist which restrictsunwhitelisted accounts. These features are intended to giveadministrators control over token movement to comply withpotential real-world regulations. The contract's compliance mechanisms are completely decoupledfrom its governance logic. When an administrator freezes anaccount, locks its balance, or when an account is un-whitelistedwhile the whitelist is active, these actions only restrict the ability totransfer tokens. The account's voting power, as tracked by the ERC20VotesUpgradeable checkpoints, remains unchanged. This can lead toa dangerous governance scenario where accounts that are restrictedfor compliance reasons can still fully participate in and inﬂuencevotes. Voting power in ERC20VotesUpgradeable is determined by an account'stoken balance at a speciﬁc block, recorded in a series of checkpoints.These checkpoints are only updated when tokens are moved,speciﬁcally through th

### 修補方式（實際）
In commit 364e745, the _updateVotingPower function is introduced andused in checkpoints. 14


## F-2025-14165 - burnFrom Can Brick User Accounts - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken allows the admin (ROLE_BURNER) to burn tokens fromusers. It also implements a locking mechanism (_locked) where userscannot transfer more than their balance - locked amount. Thisinvariant is enforced in the _update function. The burnFrom function reduces a user's token balance withoutchecking or adjusting their locked balance. This can lead to anarithmetic underﬂow in subsequent transfers, eﬀectively freezing theuser's account and preventing them from moving any remainingunlocked tokens until the deﬁcit is manually corrected. The burnFrom function calls _burn, which invokes _update(account, address(0), amount). Inside _update, the critical check that ensures amount <= unlocked is skipped because the recipient is address(0) (burning). function _update(address from, address to, uint256 amount) ... { if (from != address(0) && to != address(0) && !_forceBypass) { uint256 unlocked = fromBal - _locked[from]; if (amount > unlocked) revert LockExceedsUnlocked(...); } // ... } Consequently, an admin can burn tokens such that balanceOf(account) < _locked[account]. When the user later attempts to transfer tokens, _update is called with a non-zero to address. The contract a

### 修補方式（實際）
Fixed in commit ID 8593776: The code automatically reduces a user's _locked amount to match their new balance whenever tokens areburned, preventing the locked amount from ever exceeding the totalbalance and avoiding arithmetic underﬂows in future transfers. uint256 bal = balanceOf(account); uint256 locked = _locked[account]; if (locked > bal) { uint256 diff = locked - bal; _locked[account] = bal; emit BalanceUnlocked(account, diff); } Evidences


## F-2025-14166 - forceTransfer is Blocked by Pause - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The contract features a forceTransfer function accessible only to the ROLE_TRANSFER admin. This function is intended to bypass standardrestrictions like locks and whitelists (_forceBypass = true) to move fundsin exceptional circumstances (e.g., lost keys, legal compliance). Thecontract also inherits ERC20PausableUpgradeable. The forceTransfer function fails if the contract is paused. This defeatsthe purpose of an emergency administrative override, as the admincannot rescue funds or rectify state during a security incident (pause)without ﬁrst unpausing the contract, which could expose thecontract to further exploitation. forceTransfer calls _transfer, which calls _update. The RealEstateToken overrides _update to add custom logic but also calls super._update tomaintain ERC20Pausable functionality. function _update(address from, address to, uint256 amount) internal override( ...) { ... super._update(from, to, amount); } ERC20PausableUpgradeable._update contains the whenNotPaused modiﬁer check.Even though forceTransfer sets _forceBypass = true, this ﬂag is notrecognized by the parent ERC20PausableUpgradeable contract. Therefore, ifthe contract is paused, super._update reverts with Enfo

### 修補方式（實際）
Fixed in commit ID 8593776: the contract overrides the paused functionto return false speciﬁcally when the forceTransfer operation is active,which tricks the parent contract's pause check into allowing thetransfer even if the contract is actually paused. function paused() public view override(PausableUpgradeable) returns (bool) { if (_forceBypass) { return false; } return super.paused(); } Evidences PoC

