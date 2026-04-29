# auth/access-control - Issues

- Count: 23

## F-2026-15149 - Missing Access Control on verify And Mark Complete Enables Proof Grie ng A ack
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The ProofSystemUpgradeable contract implements access control for recordVerifiedProof but fails to implement the same protection for verifyAndMarkComplete and verifyBatch. The recordVerifiedProof function requires authorization: function `recordVerifiedProof(bytes32 proofHash)` external { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unau thorized"); verifiedProofs[proofHash] = true; emit ProofVerified(proofHash, `msg.sender`, 0); } However, verifyAndMarkComplete has no access control: function `verifyAndMarkComplete(bytes calldata proof, address prover, uint256 claimedTokens)` external returns (bool) { // First verify using internal function if (!`_verifyHostSignature`(proof, prover, claimedTokens)) { return false; emit `ProofVerified(proofHash, prover, claimedTokens)`; return true; } Similarly, verifyBatch lacks access control: function `verifyBatch(bytes[] calldata proofs, address prover, uint256[] calld ata tokenCounts)` external returns (bool) { … 49 for (uint256 i = 0; i < proofs.length; i++) { // Verify each proof using internal function require(`_verifyHostSignatureInternal`(proofs[i], prover, tokenCoun ts[i]), "Invalid proof at index"); proofHashes[i] = proofHash; totalTokens += tokenCounts[i]; } emit `BatchProofVerified(proofHashes, prover, totalTokens)`; } The replay prevention mechanism (verifiedProofs mapping) becomes adenial-of-service vector when anyone can mark proofs as “verified.” Front-Running Griefing Attack Scenario: Host creates a valid proof and signs it Host submits submitProofOfWork transaction to mempool Attacker observes the pending transaction and extracts proof data Attacker front-runs with direct call `toproofSystem.verifyAndMarkComplete(proof, host, tokens)` Attacker's transaction executes first, markingverifiedProofs[proofHash] = true Host's `submitProofOfWork()` transaction executes but fails at thereplay check in `_verifyHostSignature`(): if (verifiedProofs[proofHash]) return false; Host's legitimate proof submission reverts with "Invalid proofsignature" Host must generate a completely new proof with different data to tryagain Attacker can repeat this indefinitely, preventing the host from eversubmitting proofs Attackers can prevent hosts from submitting valid proofs by front-runningand "burning" their proof hashes. Hosts unable to submit proofs cannotearn payment for legitimate work performed. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#]src/ProofSystemUpgradeable.sol [https://github.com/Fabstir/fabstir-compute-contracts#] 50 Status: Fixed

### 修補方式（建議）
Add access control to verifyAndMarkComplete and verifyBatch to ensure onlyJobMarketplaceWithModelsUpgradeable contract can call them. Resolution: Fixed in 0606d07: verifyAndMarkComplete and verifyBatch are no longer present inProofSystemUpgradeable. The replay-protection write path has beenconsolidated into markProofUsed, which enforces access control through authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`. function `markProofUsed( bytes32 proofHash, address prover, uint256 claimedTokens, bytes32 modelId )` external override returns (bool) { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unauthor ized"); } JobMarketplaceWithModelsUpgradeable now calls markProofUsed duringproof submission, removing the previously exposed public verificationendpoints that enabled front-running griefing through unauthorized proofpre-marking.

### 修補方式（實際）
Fixed in 0606d07: verifyAndMarkComplete and verifyBatch are no longer present inProofSystemUpgradeable. The replay-protection write path has beenconsolidated into markProofUsed, which enforces access control through authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`. function `markProofUsed( bytes32 proofHash, address prover, uint256 claimedTokens, bytes32 modelId )` external override returns (bool) { require(authorizedCallers[`msg.sender`] || `msg.sender` == `owner()`, "Unauthor ized"); } JobMarketplaceWithModelsUpgradeable now calls markProofUsed duringproof submission, removing the previously exposed public verificationendpoints that enabled front-running griefing through unauthorized proofpre-marking.

## F-2026-15235 - Users Can Renounce BLACKLISTED_ROLE and Bypass Administrative Restrictions
- 嚴重度：High
- Report source：Overlayer.pdf

### 問題內容（完整）
The OverlayerWrap stablecoin contract implements a `BLACKLISTED_ROLE` mechanism to restrict specific accounts from transferring tokens. Thisrestriction is enforced using OpenZeppelinʼs AccessControl library. function `disableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_grantRole`(`BLACKLISTED_ROLE`, account_); emit `DisableAccount(account_)`; } The OverlayerWrap contract inherits from SingleAdminAccessControl,which itself utilizes OpenZeppelinʼs AccessControl library. OpenZeppelinʼsAccessControl includes a public `renounceRole()` function that allows anyaccount to renounce a role assigned to itself. WhileSingleAdminAccessControl overrides `renounceRole()` to prevent directrenouncement of the `DEFAULT_ADMIN_ROLE`, there is no additional override orrestriction in the current OverlayerWrap implementation to preventrenouncement of the `BLACKLISTED_ROLE`. // `SingleAdminAccessControl.sol` function `renounceRole( bytes32 role_, address account_ )` public virtual override `notAdmin(role_)` { `super.renounceRole(role_, account_)`; } modifier `notAdmin(bytes32 role_)` { if (role_ == `DEFAULT_ADMIN_ROLE`) revert `InvalidAdminChange()`; _; } An account that has been assigned the `BLACKLISTED_ROLE` can call renounceRole(`BLACKLISTED_ROLE`, `msg.sender`) and independently remove the 10 restriction, effectively bypassing the blacklist mechanism. Given that,blacklisted users can remove their blacklist status and regain full transfer,mint and reedem functionality, effectively bypassing the administrativecontrol mechanism. This behavior undermines the intended blacklist enforcement logic. Theblacklist is expected to be an administrative control used to restrictmalicious, sanctioned, or non-compliant accounts. If users can removetheir own blacklist status, the restriction becomes ineffective and cannotbe reliably enforced. Assets: `contracts/overlayer/OverlayerWrap.sol`[https://github.com/Overlayerfi/contracts/tree/main]contracts/shared/SingleAdminAccessControl.sol[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed

### 修補方式（建議）
Consider overriding the `renounceRole()` function in the OverlayerWrapcontract to prevent accounts from renouncing the `BLACKLISTED_ROLE` themselves. Alternatively, disable `renounceRole()` entirely if self-removal of roles is notrequired within the protocolʼs access control design. This ensures that onlyauthorized administrators can manage blacklist assignments andpreserves the integrity of the restriction mechanism. Resolution: Fixed in 2f2f9d4, the `renounceRole()` function was overridden to preventaccounts from renouncing the `BLACKLISTED_ROLE` themselves: function `renounceRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotRenounceBlacklist()`; 11 `super.renounceRole(role_, account_)`;

### 修補方式（實際）
Fixed in 2f2f9d4, the `renounceRole()` function was overridden to preventaccounts from renouncing the `BLACKLISTED_ROLE` themselves: function `renounceRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotRenounceBlacklist()`; 11 `super.renounceRole(role_, account_)`;

## F-2026-15242 - Default Admin Can Assign Blacklisted Role Without Enforcing Blacklist Activation Constraints
- 嚴重度：Medium
- Report source：Overlayer.pdf

### 問題內容（完整）
The OverlayerWrap token implements a blacklisting mechanism byassigning the `BLACKLISTED_ROLE` using OpenZeppelinʼs AccessControllibrary. Accounts that are granted the blacklisted role are restricted fromperforming minting, redeeming, and transfer operations. The contractintroduces the blacklistActivationTime variable, which defines when theblacklist functionality becomes active. Until the activation time is reached,blacklist operations are not intended to be applied to any account. The `disableAccount()` function allows accounts to be added to the blacklistby the `CONTROLLER_ROLE`: function `disableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_grantRole`(`BLACKLISTED_ROLE`, account_); emit `DisableAccount(account_)`; } function `enableAccount( address account_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { `_revokeRole`(`BLACKLISTED_ROLE`, account_); emit `EnableAccount(account_)`; } The blacklistAllowed modifier enforces the activation timing restriction: modifier `blacklistAllowed()` { if ( blacklistActivationTime == 0 || blacklistActivationTime + `BLACKLIST_ACTIVATION_TIME` > `block.timestamp` ) { revert `OverlayerWrapBlacklistNotActive()`; } _; } However, the contract inherits OpenZeppelinʼs AccessControl, whichexposes the public `grantRole()` and `revokeRole()` functions. The `DEFAULT_ADMIN_ROLE` can therefore call grantRole(`BLACKLISTED_ROLE`, account) 21 directly. This direct call does not enforce the blacklistAllowed modifier andtherefore does not apply the intended activation-time restriction.. As aresult, the default admin can blacklist (or remove blacklist via `revokeRole()`)accounts at any time, regardless of the configured activation logic. The same pattern is applied in the StakedOverlayerWrapCore contract forblacklisting functionality. The contract exposes `addToBlacklist()` and `removeFromBlacklist()` functions,which are restricted to accounts holding the `CONTROLLER_ROLE`. Thesefunctions are additionally protected by the blacklistAllowed modifier, whichensures that the blacklist mechanism is active. The blacklistAllowed modifier verifies that blacklistActivationTime > 0 and that redistribution is notenabled, thereby enforcing that blacklist operations can only be performedwhen the blacklist functionality is properly activated. function `addToBlacklist( address target_, bool isFullBlacklisting_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) `notOwner(target_)` { bytes32 role = isFullBlacklisting_ ? `WHOLE_RESTRICTED_ROLE` : `STAKE_RESTRICTED_ROLE`; `_grantRole`(role, target_); } function `removeFromBlacklist( address target_, bool isFullBlacklisting_ )` external blacklistAllowed onlyRole(`CONTROLLER_ROLE`) { bytes32 role = isFullBlacklisting_ ? `WHOLE_RESTRICTED_ROLE` : `_revokeRole`(role, target_); } modifier `blacklistAllowed()` { if (blacklistActivationTime == 0) { revert `StakedOverlayerWrapCannotBlacklist()`; } if ( blacklistActivationTime + `BLACKLIST_ACTIVATION_TIME` > `block.timestamp` || redistributionActivationTime > 0 ) { revert `StakedOverlayerWrapCannotBlacklist()`; } 22 _; } The default admin may directly invoke `grantRole()` or `revokeRole()` for `STAKE_RESTRICTED_ROLE` or `WHOLE_RESTRICTED_ROLE`. Consequently, the admin canassign blacklist-related roles at any time, regardless of whether blacklistActivationTime has been reached, thereby circumventing theintended activation restrictions. This can lead to: The intended blacklist activation delay restriction logic is notconsistently enforced.A mismatch between declared behavior and actual enforceablebehavior, potentially impacting user trust and protocol transparency. Assets: `contracts/overlayer/OverlayerWrap.sol`[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed

### 修補方式（建議）
To ensure consistent enforcement of blacklist activation rules: Override `grantRole()` and `revokeRole()` in the OverlayerWrap andStakedOverlayerWrapCore contract to prevent direct assignment orremoval of `BLACKLISTED_ROLE` / `WHOLE_RESTRICTED_ROLE` / `STAKE_RESTRICTED_ROLE` via the public AccessControl interface by the `DEFAULT_ADMIN_ROLE`.Enforce the blacklistAllowed restriction within any logic path thatassigns `BLACKLISTED_ROLE` / `WHOLE_RESTRICTED_ROLE` / `STAKE_RESTRICTED_ROLE`. This ensures that all blacklisting actions follow the intended activationconstraints and preserves the integrity of the protocolʼs expected behavior. 23 Resolution: Fixed in e9f1389, `grantRole()` and `revokeRole()` functions were overridden inthe OverlayerWrap and StakedOverlayerWrapCore contract to preventdirect assignment or the custom role that reguire blacklistAllowed validation: // `OverlayerWrap.sol` function `grantRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.grantRole(role_, account_)`; } function `revokeRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.revokeRole(role_, account_)`; } // `StakedOverlayerWrapCore.sol` function `grantRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } function `revokeRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } 24

### 修補方式（實際）
Fixed in e9f1389, `grantRole()` and `revokeRole()` functions were overridden inthe OverlayerWrap and StakedOverlayerWrapCore contract to preventdirect assignment or the custom role that reguire blacklistAllowed validation: // `OverlayerWrap.sol` function `grantRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.grantRole(role_, account_)`; } function `revokeRole(bytes32 role_, address account_)` public override { if (role_ == `BLACKLISTED_ROLE`) revert `OverlayerWrapCannotDirectlyAssignBlacklist()`; `super.revokeRole(role_, account_)`; } // `StakedOverlayerWrapCore.sol` function `grantRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } function `revokeRole( bytes32 role_, address account_ )` public virtual override { if (role_ == `STAKE_RESTRICTED_ROLE` || role_ == `WHOLE_RESTRICTED_ROLE`) revert `StakedOverlayerWrapCannotDirectlyAssignBlacklist()`; } 24

## F-2025-13782 - Unauthorized Delegation via `migrate And Delegate()`Function
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `migrateAndDelegate()` function in the `Stargate.sol` contract lacksownership verification, allowing any user to migrate another user's legacytoken and delegate it to an arbitrary validator of the attacker's choice.While the token ownership is correctly assigned to the legitimate ownerafter migration, the delegation is controlled by the attacker. The token owner is able to stop the token delegation. The migrateAndDelegate requires `VET` to be attached and the `VET` can bewithdrawn only by the legitimate token owner via unstake. However, theattacker may receive profit by migrating abandoned X tokens whichprovide the 1.5x validator rewards multiplier. `Stargate.sol`: function migrateAndDelegate( uint256 `_tokenId`, address `_validator` ) external payable whenNotPaused nonReentrant { StargateStorage storage $ = `_getStargateStorage`(); // `VULNERABLE` `ENTRY` `POINT`: No ownership verification // Anyone can call this function with any `_tokenId` // get the level of the node from the legacy nodes contract (, uint8 level, , , , , ) = $.`stargateNFTContract.legacyNodes()`.getMetada ta(`_tokenId`); // get the vet amount required to stake for the level uint256 vetAmountRequiredToStake = $ .stargateNFTContract .`getLevel(level)` .vetAmountRequiredToStake; // validate the `msg.value` if (`msg.value` != vetAmountRequiredToStake) { revert VetAmountMismatch(level, vetAmountRequiredToStake, `msg.value`); } // migrate the token to the StargateNFT contract // [!] No check that `msg.sender` owns `_tokenId` $.stargateNFTContract.migrate(`_tokenId`); // delegate the token to the validator 42 // [!] Allows attacker to choose the validator `_delegate`($, `_tokenId`, `_validator`); } The function performs the following actions without verifying that `msg.sender` owns the legacy token: Retrieves metadata from the legacy token contract Validates that `msg.value` matches the required `VET` amount Calls migrate(`_tokenId`) which mints the new token to the legacy `owner(correct)` Calls `_delegate`($, `_tokenId`, `_validator`) which delegates to the caller'schosen validator (incorrect) The `_delegate`() internal function assumes that the calling function hasalready verified ownership, but `migrateAndDelegate()` violates thisassumption. In contrast, the public `delegate()` function properly enforcesownership through the onlyTokenOwner(`_tokenId`) modifier. Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
Add ownership verification at the beginning of the `migrateAndDelegate()` function to ensure only the legitimate legacy token owner can migrate anddelegate their token. This aligns the function's access control with otherdelegation-related functions in the contract: modifier onlyLegacyTokenOwner(uint256 `_tokenId`) { StargateStorage storage $ = `_getStargateStorage`(); address legacyOwner = $.`stargateNFTContract.legacyNodes()`.idToOwner(`_toke` nId); 43 if (legacyOwner != `msg.sender`) { revert UnauthorizedUser(`msg.sender`); } _; } function migrateAndDelegate( uint256 `_tokenId`, address `_validator` ) external payable onlyLegacyTokenOwner(`_tokenId`) whenNotPaused nonReentrant { StargateStorage storage $ = `_getStargateStorage`(); rest of the function implementation … } Resolution: The finding is fixed in commit hash 4574d8b after adding the onlyLegacyTokenOwner(`_tokenId`) modifier to the `migrateAndDelegate()` function.The new modifier validates that `msg.sender` is the legitimate owner of thelegacy token by checking `legacyNodes()`.idToOwner(`_tokenId`), preventingunauthorized users from migrating and delegating other users' tokens toarbitrary validators.

### 修補方式（實際）
The finding is fixed in commit hash 4574d8b after adding the onlyLegacyTokenOwner(`_tokenId`) modifier to the `migrateAndDelegate()` function.The new modifier validates that `msg.sender` is the legitimate owner of thelegacy token by checking `legacyNodes()`.idToOwner(`_tokenId`), preventingunauthorized users from migrating and delegating other users' tokens toarbitrary validators.

## F-2026-15334 - Delegate Spending Cap Bypass via Token Selection Allows Draining Payer Funds Beyond Intended Limits
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


## F-2025-14066 - Excessive Emergency Withdraw Can Steal User Funds - Medium
- 嚴重度：Medium
- Report source：A Two Tech Limited.pdf

### 問題內容（摘要）
The ATWOVesting.emergencyWithdraw() function allows the admin to withdrawany amount of tokens from the contract at any time, with no restrictions.This can be used to steal vested tokens that rightfully belong to users,rendering the contract insolvent and preventing users from claiming theirentitled tokens. Impact: Admin can withdraw tokens reserved for user vesting schedulesUsers will be unable to claim vested tokens when the contract hasinsufficient balanceContract becomes insolvent without any warning or recourse for usersWhile named "emergency," there are no actual emergency conditionscheckedComplete centralization risk that defeats the purpose of a vestingcontract ATWOVesting.sol: function emergencyWithdraw(address to, uint256 amount) external onlyRole(ADMI N_ROLE) { if (to == address(0)) revert ZeroAddress(); if (amount == 0) revert AmountZero(); vestedToken.safeTransfer(to, amount); // No checks on reserved amounts emit EmergencyWithdraw(to, amount); }

### 修補方式（實際）
The finding is fixed in commit e069e6f after the suggested fix (removal of emergencyWithdraw() function) was applied in the code. 16


## F-2025-14074 - Admin Can Arbitrarily Decrease User’s Vesting Amount Bypassing User Entitlement - Medium
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


## F-2025-13556 - Unvalidated Market Address Leads To Arbitrary Token Approvals - Medium
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


## F-2025-14257 - Owner Authorization Allows Arbitrary Burning of Soulbound Tokens - Medium
- 嚴重度：Medium
- Report source：RYT-2.pdf

### 問題內容（摘要）
The SoulboundCredential contract extends the ERC721 standard and disablesany token transfer after minting to ensure that each credential remainsbound to the original recipient. The contract includes a burnCredential() function for destroying existing credentials. function burnCredential(uint256 tokenId) external validCredential(tokenId) whenNotPaused nonReentrant { require( ownerOf(tokenId) == msg.sender || credentialInfo[tokenId].issuer == msg.sender || msg.sender == owner(), "SoulboundCredential: Not authorized to burn this credential" ); // ... } The access control logic in this function grants the contract owner theability to burn tokens belonging to any address. As a result, soulboundtokens can be destroyed at any time by the owner. In the event of ownerkey compromise, the likelihood of unauthorized token destructionincreases.

### 修補方式（實際）
Fixed in a695108, the owner of the contract was excluded from theauthorized accounts who can burn the credentials. Only owner of thecredential or the credential issuer can burn: if ( ownerOf(tokenId) != msg.sender && credentialInfo[tokenId].issuer != msg.sender ) { revert NotAuthorizedBurn(); } 14


## F-2025-14229 - Missing USER_ROLE Check Allows Unauthorized Participants in Joint Groups And Payouts - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The function joinGroupWithJointContributor() allows a user to join a groupwith a secondary contributor but lacks a check to verify that the secondarycontributor has been granted the required USER_ROLE. This allowsregistration of secondary contributors who do not have the necessarypermissions to participate in the system, potentially causing permissioninconsistencies and unexpected behavior. function joinGroupWithJointContributor(uint256 groupId, address secondaryCon tributor) external payable whenNotPaused checkIfGroupExit(groupId) onlyRole(USER_ROLE) { require(secondaryContributor != address(0), "Komiti: Zero Address not allowed"); Group storage group = s_groups[groupId]; require(!group.isPayoutStarted, "Komiti: Cannot join after payout sta rts"); require(block.timestamp < group.joinDeadline, "Komiti: Cannot join af ter deadline"); require(s_contributions[groupId][msg.sender] == 0, "Komiti: User alre ady joined"); require(msg.value >= group.perShareAmount / 2, "Komiti: Incorrect amo unt sent"); // Half for this user and half for secondary contributor require( !s_isJointContributor[groupId][secondaryContributor], "Komiti: Se condary contributor already registered" ); s_jointContrib

### 修補方式（實際）
Fixed in 1829f31. The codebase no longer contains the joinGroupWithJointContributor() functionality. In addition to that, the following USER_ROLE check was implemented in the setPayoutPositions() function: ... if (!hasRole(USER_ROLE, users[i])) revert UserHasNotJoined(); ... 32


## F-2025-14253 - Missing Refund Mechanism for Regular Members Leads To Stuck Assets - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The smart-contract provides a returnFunds() function, but it only applies tojoint-contributor workflows, allowing a primary contributor to unwind aninvitation before payout starts. function returnFunds(uint256 groupId, address secondaryContributor) external payable checkIfGroupExit(groupId) onlyRole(USER_ROLE) { Group storage group = s_groups[groupId]; require(!group.isPayoutStarted, "Komiti: Cannot return funds after pa yout starts"); require( s_jointContributorPrimary[groupId][secondaryContributor] == msg.s ender, "Komiti: Only primary contributor can return amount" ); require(s_contributionShares[groupId][secondaryContributor] == 0, "Ko miti: Invite already accepted"); s_jointContributorPrimary[groupId][secondaryContributor] = address(0) ; s_isJointContributor[groupId][secondaryContributor] = false; address[] storage secondaryContributors = s_jointContributorsDetails[ groupId][msg.sender].secondaryContributors; for (uint256 i = 0; i < secondaryContributors.length; i++) { if (secondaryContributors[i] == secondaryContributor) { secondaryContributors[i] = secondaryContributors[secondaryCon tributors.length - 1]; secondaryContributors.pop(); break; } } delete s_jointContributorsDeta

### 修補方式（實際）
In commit 1829f31, the public refundMember function that allows anycontributing member to withdraw their funds before the payout cycle starts 36 is introduced, resolving the issue where regular users had no mechanismto reclaim funds from stalled or inactive groups. 37


## F-2025-11617 - Users Can Perform New Tokens Purchase Afterauto Refund() Leading to Underﬂow in claim() - High
- 嚴重度：High
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract enables users to purchase project tokensusing a bonding mechanism and later claim them once the vestingperiod begins. The BondingCurveWritable extension allows the defaultadmin to initiate an automatic refund of the bonded token via the autoRefund() function if the soft cap is not reached. However, during autoRefund(), the user's state is not properly updatedto reﬂect the refund. Speciﬁcally, the user.isRefunded ﬂag is not set totrue, and no adjustments are made to the amountToClaim or amountClaimed ﬁelds. This allows users to buy tokens again in the same bondingcurve after being automatically refunded. But because amountClaimed isset to type(uint256).max during the refund process, it becomesimpossible for that user to claim any newly purchased tokens,leading to a loss of bonded tokens and claimable project tokenamount. BondingCurveWritable::autoRefund(): function autoRefund( address[] calldata userAddresses ) external whenNotPaused onlyRole(DEFAULT_ADMIN_ROLE) { if (userAddresses.length == 0) revert EmptyArray(); BondingCurveStorage.Storage storage strg = BondingCurveStorage.layout (); if (strg.ledger.raisedTokenAmount >= strg.setUp.softCap) revert Refund

### 修補方式（實際）
Fixed in 90b3457: added ﬂag user.isRefunded = true to the autoRefund() function that prevents users from purchasing again on a refundedcurve. Evidences PoC


## F-2025-11742 - Incorrect Handling of reserve Fee During dex()Execution - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract deﬁnes a fee structure for the project tokenthat includes several components like reserveFee, teamFee, ecosystemFee, tokenToSellPercent, and lPPercent. These fees are intended to bedistributed to their respective beneﬁciaries when the dex() functionis called, with the exception of tokenToSellPercent, which follows avesting schedule. According to the contract’s logic and documentation, the dex() function should handle the full distribution of fees, including the reserveFee. However, during execution, while most fee componentsare transferred correctly, the reserveFee is not transferred and insteadremains locked in the bonding curve contract. function dex() public onlyRole(DEFAULT_ADMIN_ROLE) { ... IRouter_ETH_BNB_AVAX(router).addLiquidity( ... ) _giveToken(bondedToken, setUp.platformOwner, bondedTaxAmount); _giveToken(bondedToken, setUp.projectOwner, remainingAmount); if (curatorAmount > 0) { _giveToken(bondedToken, setUp.curatorAddress, curatorAmount); } _giveToken(projectToken, setUp.teamWallet, ledger.teamAmount); _giveToken(projectToken, setUp.ecosystemWallet, ledger.ecosystemAmount); uint256 remainingProjectToken = ledger.tokenToSell - ledger.totalProje

### 修補方式（實際）
Fixed in eb0e63e: reservedFee is transferring to the platformOwner addressonce dex() function is called. 26


## F-2025-11752 - Incorrect Fee Math Allows Users to Exceed Allocation - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurveWritable contract facilitates a multi-tiered token salewhere diﬀerent user groups (Tiers, Whitelist, Public Sale.) are givenspeciﬁc purchase allocations. Participation in these private rounds ismanaged by a Merkle tree, where each leaf contains a user'saddress, their maximum allocation, and their designated round.When a user calls the buy function, the _authenticateUser internalfunction is invoked to verify their Merkle proof and check if theircumulative purchase amount is within their speciﬁed allocation.amount.This check is critical for enforcing the sale rules and ensuring a fairdistribution. The mathematical formula used within _authenticateUser to calculate auser's cumulative spend is incorrect. It attempts to reconstruct theuser's total gross (pre-fee) contribution by applying a multiplicativefee factor to their stored net (post-fee) contribution, which under-estimates the true amount spent. This ﬂaw allows any user in aprivate round to systematically purchase more tokens than theiroﬃcial allocation without triggering the ExceedAllocation error, therebybypassing a core security mechanism of the sale. When a user makes a purchase, the contract stores theircontr

### 修補方式（實際）
In commit 5529582, the allocation tracking mechanism is implementedbased on gross amounts. Evidences PoC


## F-2025-14081 - Minting is Allowed for Frozen and Non-Whitelisted Addresses - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken contract includes several compliance and controlmechanisms, such as freezing accounts (setFrozen), locking balances(lockBalance), and enforcing a whitelist (setWhitelistMode). These areprimarily enforced within the overridden _update function, which isthe central hub for all token balance changes, including transfers,minting, and burning. The core compliance checks for frozen accounts and whitelisting areincorrectly scoped, causing them to be completely bypassed duringminting and burning operations. This allows the MINTER role to createnew tokens for addresses that are explicitly frozen or not on thewhitelist, and allows the BURNER role to destroy tokens from a frozenaccount. This undermines the contract's intended regulatory controlsand can lead to tokens becoming permanently stuck in non-compliant wallets. In RealEstateToken.sol, the _update function contains the logic to verify ifan account is frozen or whitelisted. However, all of these checks arewrapped inside a conditional statement that only executes forregular transfers: function _update(address from, address to, uint256 amount) internal override(ERC20Upgradeable, ERC20PausableUpgradeable, ERC20VotesUpgr

### 修補方式（實際）
Fixed in commit ID 8593776: the mint(), burn() and burnFrom() methodswere updated in order to properly avoid minting and burning tokensfrom frozen and non-whitelisted addresses. if (_frozen[to]) revert AccountFrozen(to); if (whitelistEnabled && !_whitelisted[to]) revert NotWhitelisted(to); Evidences PoC


## F-2025-14099 - Compliance Status is Decoupled from Voting Power - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken contract integrates features for on-chaingovernance using OpenZeppelin's ERC20VotesUpgradeable. It alsoimplements several compliance mechanisms, such as freezingaccounts (setFrozen), locking a portion of a user's balance(lockBalance), and enforcing a transfer whitelist which restrictsunwhitelisted accounts. These features are intended to giveadministrators control over token movement to comply withpotential real-world regulations. The contract's compliance mechanisms are completely decoupledfrom its governance logic. When an administrator freezes anaccount, locks its balance, or when an account is un-whitelistedwhile the whitelist is active, these actions only restrict the ability totransfer tokens. The account's voting power, as tracked by the ERC20VotesUpgradeable checkpoints, remains unchanged. This can lead toa dangerous governance scenario where accounts that are restrictedfor compliance reasons can still fully participate in and inﬂuencevotes. Voting power in ERC20VotesUpgradeable is determined by an account'stoken balance at a speciﬁc block, recorded in a series of checkpoints.These checkpoints are only updated when tokens are moved,speciﬁcally through th

### 修補方式（實際）
In commit 364e745, the _updateVotingPower function is introduced andused in checkpoints. 14


## F-2025-14165 - burn From Can Brick User Accounts - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The RealEstateToken allows the admin (ROLE_BURNER) to burn tokens fromusers. It also implements a locking mechanism (_locked) where userscannot transfer more than their balance - locked amount. Thisinvariant is enforced in the _update function. The burnFrom function reduces a user's token balance withoutchecking or adjusting their locked balance. This can lead to anarithmetic underﬂow in subsequent transfers, eﬀectively freezing theuser's account and preventing them from moving any remainingunlocked tokens until the deﬁcit is manually corrected. The burnFrom function calls _burn, which invokes _update(account, address(0), amount). Inside _update, the critical check that ensures amount <= unlocked is skipped because the recipient is address(0) (burning). function _update(address from, address to, uint256 amount) ... { if (from != address(0) && to != address(0) && !_forceBypass) { uint256 unlocked = fromBal - _locked[from]; if (amount > unlocked) revert LockExceedsUnlocked(...); } // ... } Consequently, an admin can burn tokens such that balanceOf(account) < _locked[account]. When the user later attempts to transfer tokens, _update is called with a non-zero to address. The contract a

### 修補方式（實際）
Fixed in commit ID 8593776: The code automatically reduces a user's _locked amount to match their new balance whenever tokens areburned, preventing the locked amount from ever exceeding the totalbalance and avoiding arithmetic underﬂows in future transfers. uint256 bal = balanceOf(account); uint256 locked = _locked[account]; if (locked > bal) { uint256 diff = locked - bal; _locked[account] = bal; emit BalanceUnlocked(account, diff); } Evidences


## F-2025-14166 - force Transfer is Blocked by Pause - Medium
- 嚴重度：Medium
- Report source：Tokenizer.Estate.pdf

### 問題內容（摘要）
The contract features a forceTransfer function accessible only to the ROLE_TRANSFER admin. This function is intended to bypass standardrestrictions like locks and whitelists (_forceBypass = true) to move fundsin exceptional circumstances (e.g., lost keys, legal compliance). Thecontract also inherits ERC20PausableUpgradeable. The forceTransfer function fails if the contract is paused. This defeatsthe purpose of an emergency administrative override, as the admincannot rescue funds or rectify state during a security incident (pause)without ﬁrst unpausing the contract, which could expose thecontract to further exploitation. forceTransfer calls _transfer, which calls _update. The RealEstateToken overrides _update to add custom logic but also calls super._update tomaintain ERC20Pausable functionality. function _update(address from, address to, uint256 amount) internal override( ...) { ... super._update(from, to, amount); } ERC20PausableUpgradeable._update contains the whenNotPaused modiﬁer check.Even though forceTransfer sets _forceBypass = true, this ﬂag is notrecognized by the parent ERC20PausableUpgradeable contract. Therefore, ifthe contract is paused, super._update reverts with Enfo

### 修補方式（實際）
Fixed in commit ID 8593776: the contract overrides the paused functionto return false speciﬁcally when the forceTransfer operation is active,which tricks the parent contract's pause check into allowing thetransfer even if the contract is actually paused. function paused() public view override(PausableUpgradeable) returns (bool) { if (_forceBypass) { return false; } return super.paused(); } Evidences PoC

## Cyfrin Fixed Issues (Merged)
- Count: `48`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] If multiple users call `Default Session::assert Results` all but the first caller lose their bonds
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** The `assertResults` is a permissionless function that allow anyone to assert a result for a `gameId` (sessionId):

```solidity
function assertResults(
        uint256 sessionId,
        string calldata resultCid,
        address[] calldata proposedWinners,
        uint256[] calldata totalXPs,
        uint256[] calldata totalTimes
    ) external returns (bytes32 assertionId) {
        require(SessionManager(sessionManager).getSessionState(sessionId) == SessionState.Ended, GameNotEnded());
        return assertDataFor(
            sessionId, resultCid, resolutionGitRepoAtCommitHash, proposedWinners, totalXPs, totalTimes, msg.sender
        );
    }
```

Users that call this function have to pay a usdc bond of 250 dollars, see [minimum bonds value](https://docs.uma.xyz/resources/approved-collateral-types).

```solidity
 function assertDataFor(
        uint256 sessionId,
        string calldata resultCid,
        string memory resolutionGitRepoAtCommitHash,
        address[] calldata winners,
        uint256[] calldata totalXPs,
        uint256[] calldata totalTimes,
        address asserter
    ) internal returns (bytes32 assertionId) {
        asserter = asserter == address(0) ? msg.sender : asserter;
        uint256 bond = optimisticOracle.getMinimumBond(address(usdc)); /
        usdc.safeTransferFrom(msg.sender, address(this), bond);  <--------
        usdc.forceApprove(address(optimisticOracle), bond); <-------
}
```

The problem is that this function is not restricting users to call `assertResults` more than once for the same `sessionId` with that being say lets explore what would happen if `assertResults` is called twice for the same `sessionId`, `winners`, `totalXPs` and `TotalTimes` ; note that since the `assertResults` function is permissionless it can naturally be called twice by two different users at the same time:

1. A game has ended
2. User A call `assertResults` passing the session ID and the correct values.
3. User B didn't notice that that user A already call `assertResults` and call again `assertResults`
4. User A true is resolver positive and the `recordResults` function is called setting ` winners[sessionId] = assertion.winners;`
5. User B assertion is resolved positive, the oracle call revert in `recordResults` making the user loss his funds

```solidity
 function recordResults(uint256 sessionId, bytes32 assertionId) public {

        require(SessionManager(sessionManager).getSessionState(sessionId) == SessionState.Ended, GameNotEnded());
        require(
            sessionId == assertions[assertionId].sessionId,
            SessionIdMismatch(sessionId, assertions[assertionId].sessionId)
        );
        require(assertions[assertionId].resolved, AssertionNotInitialized(assertionId));
        require(winners[sessionId].length == 0, WinnersAlreadyRecorded(sessionId));
        ...

        winners[sessionId] = assertion.winners;
    }
```

Note that the UMA protocol recommends [don't revert in the callback](https://github.com/UMAprotocol/protocol/blob/6a23be19d8a0dbee4475db9ff52ce4d9572212b5/packages/core/contracts/optimistic-oracle-v3/implementation/OptimisticOracleV3.sol#L122):
```
recipient _must_ implement these callbacks and not revert or the assertion resolution will be blocked.
```

**Impact:** If `assertResults` is called more than once by different users just the first caller will recover their bond; the other users end up losing their money.

**Proof of Concept:** Run the next proof of concept in `file:test/session/DefaultSession.sol`
```solidity
 function test_RecordResults_double() public { //@audit
        // Mock SessionManager to return Ended state
        vm.mockCall(
            sessionManager, abi.encodeCall(SessionManager.getSessionState, gameId), abi.encode(SessionState.Ended)
        );

        string memory resultCid = "QmTestResultCID";
        address[] memory proposedWinners = new address[](2);
        proposedWinners[0] = player1;
        proposedWinners[1] = player2;

        uint256[] memory totalXPs = new uint256[](2);
        totalXPs[0] = 200;
        totalXPs[1] = 150;

        uint256[] memory totalTimes = new uint256[](2);
        totalTimes[0] = 30;
        totalTimes[1] = 45;

        vm.mockCall(
            optimisticOracle,
            abi.encodeWithSelector(OptimisticOracleV3Interface.assertTruth.selector),
            abi.encode(keccak256("assertionId43"))
        );
        bytes32 assertionId =
            defaultSession.assertResults(gameId, resultCid, proposedWinners, Solarray.uint256s(200, 150), totalTimes);

        vm.mockCall(
            optimisticOracle,
            abi.encodeWithSelector(OptimisticOracleV3Interface.assertTruth.selector),
            abi.encode(keccak256("assertionId44"))
        );
        bytes32 assertionIdtwo =
            defaultSession.assertResults(gameId, resultCid, proposedWinners, Solarray.uint256s(200, 150), totalTimes); //second assertion with the same values

        // 2. Call the callback to mark the assertion as resolved
        vm.prank(address(optimisticOracle));
        defaultSession.assertionResolvedCallback(assertionId, true);

        vm.startPrank(address(optimisticOracle));
        vm.expectRevert();
        defaultSession.assertionResolvedCallback(assertionIdtwo, true);
    }
```

**Recommended Mitigation:** Either prevent multiple in-process assertions for the same `sessionId`, or just return in the callback without reverting if it was already processed.

**Majority Games:**
Fixed in commit [4c5483f](https://github.com/Engage-Protocol/engage-protocol/commit/4c5483fd6f39b49f2fcd93055151244b4b6cd262) by returning in the callback without reverting if the assertion has already been processed.

**Cyfrin:** Verified.

\clearpage

## [C-2] Users can get their withdrawal active requests Do Sed by malicious users
- Severity: `Critical`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** Users can opt to withdraw either `USDe` or `sUSDe`.
- When withdrawing `sUSDe`, the assets can be put on a cooldown period depending on the Tranche from which the withdrawal is requested.
- When withdrawing `USDe`, regardless of the Tranche from which the withdrawal is requested, a new withdrawal request will be created on the `UnstakeCooldown` contract because to receive `USDe`, it is required to unstake `sUSDe` on the Ethena contract.

The problem this issue reports is a grief attack that allows malicious users to cause a DoS to other users' active withdrawal requests, effectively causing their assets to get stuck on the system.

The grief attack is achieved by withdrawing as low as 1 wei and setting the `receiver` as the victim user that the attacker wants to damage.
Given that neither the `Tranche` nor the `CDO` nor the `Strategy` contracts validate if the withdrawer is authorized by the `receiver` to request withdrawals on their behalf, this allows anybody to make new withdrawal requests on behalf of anybody.
- Each new withdrawal request is pushed to an array on the `UnstakingContract`, which, once the cooldown period is over, the `UnstakingContract.finalize()` iterates over such an array to process all the ready requests. The attack inflates this array to a point that causes an `out of gas error` because of iterating over thousands of active requests (inflated by an attacker).

Since the unstaking contracts lack access control, an alternative approach is to directly call the `request()` method of the unstaking contracts. This allows circumventing the system's core contracts and directly inflating the user's withdrawal requests on the unstaking contracts.

```solidity
    function transfer(IERC20 token, address to, uint256 amount) external {
@>      address from = msg.sender;
        ...
        SafeERC20.safeTransferFrom(token, from, address(proxy), amount);
        ...

@>      requests.push(TRequest(uint64(unlockAt), proxy));
        emit Requested(address(token), to, amount, unlockAt);
    }

```

**Impact:** Malicious users can cause a DoS for other users to complete the withdrawal of their assets when they are withdrawing USDe via the UnstakeCooldown contract.

**Proof of Concept:** Add the next PoC on the `CDO.t.sol` file.
The PoC demonstrates how a malicious user can fully DoS the withdrawal of active requests for another user by requesting a huge amount of withdrawals for as low as one wei. As a result, a malicious user can fully DoS the active withdrawals for a small amount of resources, mostly covering the gas costs.

```solidity
    function test_DoSUserActiveRequests() public {
        address alice = makeAddr("Alice");
        address bob = makeAddr("Bob");

        uint256 initialDeposit = 1000 ether;
        USDe.mint(alice, initialDeposit);
        USDe.mint(bob, initialDeposit);

        vm.startPrank(alice);
        USDe.approve(address(jrtVault), type(uint256).max);
        jrtVault.deposit(initialDeposit, alice);
        vm.stopPrank();

        vm.startPrank(bob);
        USDe.approve(address(jrtVault), type(uint256).max);
        jrtVault.deposit(initialDeposit, bob);
        vm.stopPrank();

        //@audit => Alice requests to withdraw its full USDe balance
        uint256 totalWithdrawableAssets = jrtVault.maxWithdraw(alice);
        vm.prank(alice);
        jrtVault.withdraw(totalWithdrawableAssets, alice, alice);

        //@audit => Bob does a huge amount of tiny withdrawals to inflate the activeRequests array of Alice
        vm.pauseGasMetering();
            for(uint i = 0; i < 35_000; i++) {
                vm.prank(bob);
                jrtVault.withdraw(1, alice, bob);
            }
        vm.resumeGasMetering();

        //@audit-info => Skip till a timestamp where the requests can be finalized
        skip(1_000_000);

        //@audit-issue => Alice gets DoS her tx to finalize the withdrawal of her USDe balance
        vm.prank(alice);
        unstakeCooldown.finalize(sUSDe, alice);
    }
```

**Recommended Mitigation:** A combination of a minimum withdrawal amount and a permission mechanism to allow users to specify who can request new withdrawals on their behalf.

In addition to the above mitigations, restrict who can call the `transfer()` on the `UnstakeCooldown` and `ERC20Cooldown` contracts. If anybody can call the `transfer()` function, the mitigations mentioned previously can be circumvented by directly calling the `transfer()` on any of the two Cooldown contracts.

**Strata:**
Fixed in commits ea7371d, da327dc, and, 9b5ac62 by:
1. Adding access control to `UnstakeCooldown::transfer` and `ERC20Cooldown::transfer`.
2. Setting a soft limit for requests created by an account other than the receiver, and a hard limit for requests created by the actual receiver. Once the hard limit is reached, any subsequent request is added to the last request on the list.

**Cyfrin:** Verified. Implemented access control to prevent grief by calling functions directly. Implemented limits to prevent unauthorized users from spamming fake requests and filling up the withdrawer's requests queue.

## [C-3] `Liveness Recovery::set Liveness Recovery Operator` will emit misleading event when role is not granted
- Severity: `Critical`
- Source report: `upgrade.md`

### Detailed Content (from source)
**Description:** `LivenessRecovery::setLivenessRecoveryOperator` can be called multiple times as long as the first two preconditions are met.

However if `OPERATOR_ROLE` has already been granted to `livenessRecoveryOperator` then `AccessControlUpgradeable::_grantRole` [returns](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/access/AccessControlUpgradeable.sol#L205-L211) `false`.

But the boolean return value of `_grantRole` is not checked so the misleading event will still be emitted.

**Recommended Mitigation:** Only emit the event if `_grantRole` returned true:
```diff
-   _grantRole(OPERATOR_ROLE, livenessRecoveryOperatorAddress);
+   if(_grantRole(OPERATOR_ROLE, livenessRecoveryOperatorAddress))
    emit LivenessRecoveryOperatorRoleGranted(msg.sender, livenessRecoveryOperatorAddress);
```

**Linea:** Fixed in commit [66050d2](https://github.com/Consensys/linea-monorepo/pull/2007/commits/66050d2689a6b817b29f2de6b0a3fda2c69c42d9).

**Cyfrin:** Verified.

## [C-4] After the upgrade permissionless attacker can fully drain the L1 `Token Bridge` of `ERC20` tokens currently valued around $29M USD
- Severity: `Critical`
- Source report: `upgrade.md`

### Detailed Content (from source)
**Description:** Using `forge inspect -R "@openzeppelin/=contracts/node_modules/@openzeppelin/" --hardhat TokenBridge storageLayout` on both the new and old `TokenBridge` contracts to carefully examine their exact storage layout showed that:
* slot 0 which used to be initialization slot becomes a gap
* slot 50 which used to be a gap becomes the new initialization slot

**Impact:** Immediately following the upgrade, the `TokenBridge` contract will believe it is not initialized allowing a permissionless attacker to initialize it. An attacker can weaponize this to completely drain the L1 `TokenBridge` contract of ERC20 tokens which at the time of this audit are [valued around $29M USD](https://etherscan.io/address/0x051F1D88f0aF5763fB888eC4378b4D8B29ea3319).

**Proof of Concept:** Immediately following the upgrade:
1. Attacker calls `TokenBridge::initialize` to set themselves as default admin
2. Attacker calls `TokenBridge::grantRole(SET_MESSAGE_SERVICE_ROLE, attacker)` to give themselves permission to set messaging service address
3. Attacker deploys a malicious messaging service contract such as:
```solidity
contract MaliciousMessageService {
    address public targetRemoteSender;

    constructor(address _remoteSender) {
        targetRemoteSender = _remoteSender;
    }

    // Spoofs the remoteSender check
    function sender() external view returns (address) {
        return targetRemoteSender;
    }

    // Calls TokenBridge as msg.sender to pass onlyMessagingService
    function drain(
        ITokenBridge bridge,
        address token,
        uint256 amount,
        address recipient,
        uint256 chainId
    ) external {
        bridge.completeBridging(token, amount, recipient, chainId, "");
    }
}
```
4. Attacker sets it by calling `TokenBridge::setMessageService(maliciousMessageService)`
5. Attacker calls the `drain` function on their malicious messaging service for every token locked in the L1 `TokenBridge`
6. `TokenBridge::_completeBridging` calls `IERC20Upgradeable(_nativeToken).safeTransfer(_recipient, _amount)` to send the attacker the locked tokens

This attack can be executed atomically and via a private mempool such as flashbots (to prevent front-running) making it unstoppable and completely draining the L1 `TokenBridge`.

**Recommended Mitigation:** `TokenBridgeBase` should inherit from `Initializable`. In an older version `TokenBridge` inherited from `Initializable` but this was later changed to inherit from OZ `ReentrancyGuardUpgradeable`, which itself inherits from `Initializable` so everything was still OK.

The bug appears to have been introduced on Nov 7th 2025 in commit [0c8bee7](https://github.com/Consensys/linea-monorepo/commit/0c8bee77311c694ba9c8643356f9703b9c88394b#diff-aff2d4ab7e0847d160464ca3171cd9a427be1e9503a4feffaaa6207fc83237efL31-R31) which swapped out OZ `ReentrancyGuardUpgradeable` for the new custom `TransientStorageReentrancyGuardUpgradeable`. This new contract doesn't inherit from `Initializable` which changed the `TokenBridge` inheritance hierarchy and hence storage slots.

**Linea:** Fixed in commit [4882f33](https://github.com/Consensys/linea-monorepo/pull/2007/commits/4882f33de707085f01e54c89d090c6fba76f33a4).

**Cyfrin:** Verified; the fix results in the initialization slot being preserved at slot 0. Slot 1 which used to be `_status` now becomes a gap and using `cast storage 0x051F1D88f0aF5763fB888eC4378b4D8B29ea3319 1` shows that on Mainnet L1 `TokenBridge`, slot 1 (currently `_status`) is already set to 1. Consider using a `reinitializer` to wipe slot 1 "clean" as it becomes a gap.

**Linea:** Added the wiping of slot 1 in commit [d99f590](https://github.com/Consensys/linea-monorepo/pull/2007/commits/d99f5906ec95102cdc67fb27039b26d15ef52a1e).

\clearpage

## [C-5] Incorrect `owner` passed to `Manager::redeem` in YToken withdrawal flow
- Severity: `Critical`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** YieldFi’s yield tokens (`YTokens`) implement a more complex withdrawal mechanism than a standard ERC-4626 vault. Instead of executing withdrawals immediately, they defer them to a central `Manager` contract, which queues the request for off-chain processing and later execution on-chain.

As with any ERC-4626 vault, third parties are allowed to initiate a withdrawal or redemption on behalf of a user, provided the appropriate allowances are in place.

However, in [`YToken::_withdraw`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L161-L172), the wrong address is passed to the `manager.redeem` function. The same issue is also present in [`YTokenL2::_withdraw`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L170-L180):
```solidity
// Override _withdraw to request funds from manager
function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal override nonReentrant notPaused {
    require(receiver != address(0) && owner != address(0) && assets > 0 && shares > 0, "!valid");
    require(!IBlackList(administrator).isBlackListed(caller) && !IBlackList(administrator).isBlackListed(receiver), "blacklisted");
    if (caller != owner) {
        _spendAllowance(owner, caller, shares);
    }
    // Instead of burning shares here, just redirect to Manager
    // The share burning will happen during order execution
    // Don't update totAssets here either, as the assets haven't left the system yet
    // @audit-issue `msg.sender` passed as owner
    IManager(manager).redeem(msg.sender, address(this), asset(), shares, receiver, address(0), "");
}
```

In this call, `msg.sender` is passed as the `owner` to `manager.redeem`, even though the correct `owner` is already passed into `_withdraw`. This works as expected when `msg.sender == owner`, but fails in delegated withdrawal scenarios where a third party is acting on the owner's behalf. In such cases, the `manager.redeem` call may revert, or worse, may burn the wrong user’s tokens if `msg.sender` happens to have shares.


**Impact:** When a third party initiates a withdrawal on behalf of another user (`caller != owner`), the incorrect owner is passed to `manager.redeem`. This can cause the call to revert, blocking the withdrawal. In a worst-case scenario, if `msg.sender` (the caller) also holds shares, it may result in unintended burning of their tokens instead of the intended owner's.

**Proof of Concept:** Place the following test in `yToken.ts` under `describe("Withdraw and Redeem")`, it should pass but fails with `"!balance"`:
```javascript
it("Should handle redeem request through third party", async function () {
  // Grant manager role to deployer for manager operations
  await administrator.grantRoles(MINTER_AND_REDEEMER, [deployer.address]);

  const sharesToRedeem = toN(50, 18); // 18 decimals for shares

  await ytoken.connect(user).approve(u1.address, sharesToRedeem);

  // Spy on manager.redeem call
  const redeemTx = await ytoken.connect(u1).redeem(sharesToRedeem, user.address, user.address);

  // Wait for transaction
  await redeemTx.wait();

  // to check if manager.redeem was called we can check the event of manager contract
  const events = await manager.queryFilter("OrderRequest");
  expect(events.length).to.be.greaterThan(0);
  expect(events[0].args[0]).to.equal(user.address); // owner, who's tokens should be burnt
  expect(events[0].args[1]).to.equal(ytoken.target); // yToken
  expect(events[0].args[2]).to.equal(usdc.target); // Asset
  expect(events[0].args[4]).to.equal(sharesToRedeem); // Amount
  expect(events[0].args[3]).to.equal(user.address); // Receiver
  expect(events[0].args[5]).to.equal(false); // isDeposit (false for redeem)
});
```

**Recommended Mitigation:** Pass the correct `owner` to `manager.redeem` in both `YToken::_withdraw` and `YTokenL2::_withdraw`, instead of using `msg.sender`.

**YieldFi:** Fixed in commit [`adbb6fb`](https://github.com/YieldFiLabs/contracts/commit/adbb6fb27bd23cdedccdaf9c1f484f7780cb354c)

**Cyfrin:** Verified. `owner` is now passed to `manager.redeem`.

\clearpage

## [M-6] `Accountable Async Redeem Vault` allows deposits for non-whitelisted or non-KYCed addresses
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** Almost all functions in `AccountableAsyncRedeemVault` use an `onlyAuth()` modifier to verify that the caller is KYC-ed or Whitelisted (according to the vault's own policy).

This logic can be seen in `isVerified()` function in AccessBase.sol

Here is the `AccountableAsyncRedeemVault::onlyAuth` modifier :

```solidity
    modifier onlyAuth() {
        if (!isVerified(msg.sender, msg.data)) revert Unauthorized();
        _;
    }

```

This passes `msg.sender` as the "Account" address to be verified, but these checks are not working.

If we look at the `deposit()` function here, `msg.sender` is not the actual account address, for whom the deposit will be done, instead the "receiver" address here is the actual account. The "Receiver" address receives the shares but it is not verified that they are whitelisted/ KYC-ed.

```solidity
    function deposit(uint256 assets, address receiver, address controller) public onlyAuth returns (uint256 shares) {
        _checkController(controller);
        if (assets == 0) revert ZeroAmount();
        if (assets > maxDeposit(controller)) revert ExceedsMaxDeposit();

        uint256 price = strategy.onDeposit(address(this), assets, receiver, controller);
        shares = _convertToShares(assets, price, Math.Rounding.Floor);

        _mint(receiver, shares);
        _deposit(controller, assets);

```

This means that a KYC'ed user can call `deposit()` and mint new share tokens for random "receiver" addresses (who have set the KYC'ed user as their operator using `setOperator()` and for the input params `controller == receiver` can be used). This "receiver" can then take part in the vault by holding vault shares, redeeming them via the operator etc.

**Impact:** The KYC/ Whitelist configuration does not prevent KYC’ed addresses from minting shares to non-KYCed addresses.

Similar problems might exist in the access control for other methods in the vault, the reason being `onlyAuth()` only checks the msg.sender and not the other address holding the position.

**Recommended Mitigation:** Consider documenting what is the intended permissions granted to a KYC-ed/ Whitelisted user. If they should not be allowed to open positions for other non KYC-ed addresses, then the auth checks need to be done for actual receiver/ controller addresses.

**Accountable:** Fixed in commits [`c804a31`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/c804a31d3e5b161065b775fa57f3590be3581e5a) and [`2eeb273`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/2eeb2736eb5ba8dafa2c9f2f458b31fd8eb2d6bf)

**Cyfrin:** Verified. Both `reciever` and `controller` are verified to be KYC'd throughout the calls.

## [M-7] Investment Manager can use `Accountable Fixed Term::cover Default` to misuse token approvals from anyone
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** `AccountableFixedTerm::coverDefault` allows InvestmentManager of the loan to add additional assets to the system.

```solidity
    function coverDefault(uint256 assets, address provider) external onlySafetyModuleOrManager whenNotPaused {
        _requireLoanInDefault();

        loanState = LoanState.InDefaultClaims;

        IAccountableVault(vault).lockAssets(assets, provider);

        emit DefaultCovered(safetyModule, provider, assets);
    }
```

And `lockAssets()` pulls assets from the input "provider" address, transferring them to the vault.

This means any user address who had asset token balance, and approved the vault contract (potential pending approvals from the past) is at risk of losing their funds here.

The Manager can pull funds from a random provider address without any permissions, and the "provider" would lose his approved funds without getting anything in return.

**Impact:** Any pending asset approvals from user => vault contract, can be misused to cover loan default.

The same problem also exists in AccountableOpenTerm.

**Recommended Mitigation:** Consider removing the "provider" address logic from `coverDefault()`, and simply pull assets from `msg.sender`.

**Accountable:** Fixed in commit [`014d7fb`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/014d7fb6f11766fada9054a736a264cf1d95c9f6)

**Cyfrin:** Verified. `provider` is removed.

## [M-8] Prevent accidental ownership and admin renouncement
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The inherited `renounceOwnership()` and allow the last authority to remove themselves, potentially leaving the contract permanently ownerless or admin‑less, blocking critical functions.

Consider override `renounceOwnership()` in `TokenAirdrop` to always revert.

**Accountable:** Fixed in commit [`be75091`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/be7509165d468fd19bf48bab3fa87e565412a5b6)

**Cyfrin:** Verified.

## [M-9] Upgradeable contracts missing _disable Initializers() in constructors
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The following contracts are upgradeable but do not call `_disableInitializers()` in their constructors:
- `MintingAssetProvider`
- `AllowanceAssetProvider`
- `SecuritizeOnRamp`
- `MbpsFeeManager`
- `SecuritizeOffRamp`
- `AllowanceLiquidityProvider`
- `CollateralLiquidityProvider`

In upgradeable contract patterns (such as those using OpenZeppelin's UUPS or Transparent proxies), the implementation (logic) contract is deployed independently from the proxy. If the implementation contract does not call `_disableInitializers()` in its constructor, it can be initialized directly by anyone, which is not intended and can lead to security risks. ([reference](https://docs.openzeppelin.com/upgrades-plugins/writing-upgradeable#initializing_the_implementation_contract))

**Impact:** If the implementation contract is initialized directly, an attacker could set themselves as the owner or assign other privileged roles, potentially interfering with the upgrade process or causing confusion. While this does not directly affect the proxy's state, it can break upgradeability, allow denial of service, or create unexpected behaviors in the system.

**Recommended Mitigation:** Add a constructor to each affected contract that calls `_disableInitializers()`. This ensures the implementation contract cannot be initialized or reinitialized, preventing any unauthorized or accidental initialization outside the proxy context.

```solidity
constructor() {
    _disableInitializers();
}
```

Add this to each of the affected contracts.

**Securitize:** Fixed in commit [088048](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/0880486f4e75df252c5e6a773b2f09a4956fdb87).

**Cyfrin:** Verified.

## [M-10] `Admin Registry::accept Admin` leaves other roles on the outgoing admin
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** When the pending admin calls `AdminRegistry::acceptAdmin`, we revoke `DEFAULT_ADMIN_ROLE` from the previous admin and grant it to the new admin. However, the outgoing admin may have granted themselves other protocol roles, `MARKET_ADMIN_ROLE`, `OPERATOR_ROLE`, `FEE_ADMIN_ROLE`, or `RESOLUTION_ADMIN_ROLE`, while they held `DEFAULT_ADMIN_ROLE`, which are not revoked in `acceptAdmin`.

The result is that after a handoff, the old admin retains any non-default roles they had assigned to themselves. This is inconsistent with the intent of a full admin transition and can leave the former admin with operational privileges (e.g. market or resolution admin) that the new admin may not expect.

```solidity
function acceptAdmin() external {
    require(msg.sender == pendingAdmin, "not pending admin");
    address oldAdmin = admin;
    _grantRole(DEFAULT_ADMIN_ROLE, pendingAdmin);
    _revokeRole(DEFAULT_ADMIN_ROLE, oldAdmin);
    admin = pendingAdmin;
    pendingAdmin = address(0);
    emit AdminAccepted(admin, oldAdmin);
}
```

**Recommended Mitigation:** Consider revoking all roles from the old admin when `acceptAdmin` completes. For example, explicitly revoke each protocol role from `oldAdmin` before updating state:

```solidity
_revokeRole(DEFAULT_ADMIN_ROLE, oldAdmin);
_revokeRole(MARKET_ADMIN_ROLE, oldAdmin);
_revokeRole(OPERATOR_ROLE, oldAdmin);
_revokeRole(FEE_ADMIN_ROLE, oldAdmin);
_revokeRole(RESOLUTION_ADMIN_ROLE, oldAdmin);
```

**Myriad:** Fixed in commit [`b2fc41f`](https://github.com/Polkamarkets/polkamarkets-js/commit/b2fc41fb0b3ff7f569bfabae8d06ed0becbcbb93)

**Cyfrin:** Verified.

## [M-11] `Admin Registry::propose Admin` self-proposal permanently removes `DEFAULT_ADMIN_ROLE`
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `proposeAdmin` has no guard against an admin proposing their own address:

```solidity
// AdminRegistry.sol:33-38
function proposeAdmin(address newAdmin) external {
    require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "not admin");
    require(newAdmin != address(0), "zero address");
    pendingAdmin = newAdmin; // no check: newAdmin != admin
    emit AdminProposed(newAdmin);
}
```

When the current admin then calls `acceptAdmin()`:

```solidity
address oldAdmin = admin;                          // == msg.sender
_grantRole(DEFAULT_ADMIN_ROLE, pendingAdmin);      // no-op — already held
_revokeRole(DEFAULT_ADMIN_ROLE, oldAdmin);         // REMOVES the role from the same address
admin = pendingAdmin;                              // no change to state variable
pendingAdmin = address(0);
```

The `_grantRole` is a no-op because the pending admin already holds the role. `_revokeRole` then strips it. After the call the `admin` state variable still points to the address, but it no longer holds `DEFAULT_ADMIN_ROLE`. Every `hasRole(DEFAULT_ADMIN_ROLE, ...)` check fails permanently. There is no recovery path.

This can happen accidentally (e.g., admin testing the mechanism) or maliciously (a compromised key griefing the protocol).

**Impact:** Permanent loss of all `DEFAULT_ADMIN_ROLE`-gated functions: upgrading contracts, role management, setting exchange/treasury addresses. Protocol becomes permanently non-upgradeable and unmanageable.

**Recommended Mitigation:** Add a self-proposal guard in `proposeAdmin`:

```solidity
require(newAdmin != admin, "cannot self-propose");
```

**Myriad:** Fixed in commit [`3b4311d`](https://github.com/Polkamarkets/polkamarkets-js/commit/3b4311db173a492be10cf6b83f19f85699e9d064)

**Cyfrin:** Verified.

## [M-12] `Admin Registry` inherited `grant Role`/`revoke Role` bypass the two-step transfer guard
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `AdminRegistry` inherits from OpenZeppelin `AccessControl`, which exposes public `grantRole` and `revokeRole` functions callable by the role admin (which for `DEFAULT_ADMIN_ROLE` is itself). A current admin can call `grantRole(DEFAULT_ADMIN_ROLE, newAdmin)` and then `revokeRole(DEFAULT_ADMIN_ROLE, address(this))` directly, bypassing `proposeAdmin` / `acceptAdmin` entirely. The two-step mechanism intended to prevent accidental handoffs provides no protection because the inherited one-step path remains accessible.

Additionally, the inherited functions allow granting `DEFAULT_ADMIN_ROLE` to multiple addresses simultaneously, which the `admin` state variable (which tracks only one address) would not reflect — creating a split-brain state between actual role holders and the tracked admin.

**Impact:** The two-step transfer safety guarantee is illusory. Admins can accidentally or maliciously transfer the role in a single transaction. The `admin` state variable can diverge from the true `DEFAULT_ADMIN_ROLE` holder(s).

**Recommended Mitigation:** Override `grantRole` and `revokeRole` to revert when called with `DEFAULT_ADMIN_ROLE`, forcing all `DEFAULT_ADMIN_ROLE` transfers through the two-step mechanism:

```solidity
function grantRole(bytes32 role, address account) public override {
    require(role != DEFAULT_ADMIN_ROLE, "use proposeAdmin/acceptAdmin");
    super.grantRole(role, account);
}

function revokeRole(bytes32 role, address account) public override {
    require(role != DEFAULT_ADMIN_ROLE, "use proposeAdmin/acceptAdmin");
    super.revokeRole(role, account);
}
```

**Myriad:** Fixed in commit [`dabc0d7`](https://github.com/Polkamarkets/polkamarkets-js/commit/dabc0d791e0a770f78f160d4ca2537881962d496)

**Cyfrin:** Verified.

## [M-13] Misleading revert message in only User modifier
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** The `onlyUser` modifier restricts access by checking `msg.sender == user`, however the revert message uses "OnlyOwner", which is misleading since the restricted role is not an owner but a specific user address.

**Recommended Mitigation:** Update the revert message to accurately reflect the enforced role (e.g. "OnlyUser" or "Unauthorized")

**Strata:** Fixed in commit [b2ddea9](https://github.com/Strata-Money/contracts-tranches/commit/b2ddea94d22b1dc791ffada5d8afb32e8e2a579e).

**Cyfrin:** Verified.

## [M-14] Premature zeroing of epoch rewards in `claim Undistributed Rewards` can block legitimate claims
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `claimUndistributedRewards` function allows the `REWARDS_DISTRIBUTOR_ROLE` to collect any rewards for an `epoch` that were not claimed. It includes a check: `if (currentEpoch < epoch + 2) revert EpochStillClaimable(epoch)`. This means it can be called when `currentEpoch >= epoch + 2`.

```solidity
/// @inheritdoc IRewards
function claimUndistributedRewards(
    uint48 epoch,
    address rewardsToken,
    address recipient
) external onlyRole(REWARDS_DISTRIBUTOR_ROLE) {
    if (recipient == address(0)) revert InvalidRecipient(recipient);

    // Check if epoch distribution is complete
    DistributionBatch storage batch = distributionBatches[epoch];
    if (!batch.isComplete) revert DistributionNotComplete(epoch);

    // Check if current epoch is at least 2 epochs ahead (to ensure all claims are done)
    uint48 currentEpoch = l1Middleware.getCurrentEpoch();
    if (currentEpoch < epoch + 2) revert EpochStillClaimable(epoch);
```

Simultaneously, regular users (stakers, operators, curators) can claim their rewards for a given `epoch` as long as `epoch < currentEpoch - 1` (which is equivalent to `epoch <= currentEpoch - 2`).

```solidity
// Claiming functions
/// @inheritdoc IRewards
function claimRewards(address rewardsToken, address recipient) external {
    if (recipient == address(0)) revert InvalidRecipient(recipient);

    uint48 lastClaimedEpoch = lastEpochClaimedStaker[msg.sender];
    uint48 currentEpoch = l1Middleware.getCurrentEpoch();

    if (currentEpoch > 0 && lastClaimedEpoch >= currentEpoch - 1) {
        revert AlreadyClaimedForLatestEpoch(msg.sender, lastClaimedEpoch);
    }
```

```solidity
/// @inheritdoc IRewards
function claimOperatorFee(address rewardsToken, address recipient) external {
    if (recipient == address(0)) revert InvalidRecipient(recipient);

    uint48 currentEpoch = l1Middleware.getCurrentEpoch();
    uint48 lastClaimedEpoch = lastEpochClaimedOperator[msg.sender];

    if (currentEpoch > 0 && lastClaimedEpoch >= currentEpoch - 1) {
        revert AlreadyClaimedForLatestEpoch(msg.sender, lastClaimedEpoch);
    }
```

This creates a critical overlap: when `currentEpoch == epoch + 2`, both regular claims for `epoch` are still permitted, AND `claimUndistributedRewards` for the same `epoch` can be executed.

The `claimUndistributedRewards` function, after calculating the undistributed amount but *before* transferring it, executes `rewardsAmountPerTokenFromEpoch[epoch].set(rewardsToken, 0);`. This action immediately zeroes out the record of available rewards for that `epoch` and `rewardsToken`.

**Impact:** If the `REWARDS_DISTRIBUTOR_ROLE` calls `claimUndistributedRewards` at the earliest possible moment (i.e., when `currentEpoch == epoch + 2`):

1.  The `rewardsAmountPerTokenFromEpoch[epoch]` for the specified token is set to zero.
2.  Any staker, operator, or curator who has not yet claimed their rewards for that `epoch` (but is still within their valid claiming window) will subsequently find that their respective claim functions (`claimRewards`, `claimOperatorFee`, `claimCuratorFee`) read zero available rewards from `rewardsAmountPerTokenFromEpoch[epoch]`.
3.  This leads to these legitimate claimants receiving zero rewards or their claim transactions reverting, effectively denying them their earned rewards.
4.  Critically, the "undistributed" amount claimed by the `REWARDS_DISTRIBUTOR_ROLE` will now be inflated, as it will include the rewards that *should* have gone to those users but were blocked from being claimed. This constitutes a mechanism for a privileged role to grief users and divert funds.

**Recommended Mitigation:** Ensure there is a distinct period after the regular claiming window closes before undistributed rewards can be swept. This prevents the overlap where both actions are permissible.

Modify the timing check in `claimUndistributedRewards`:
Change the condition from:
```solidity
if (currentEpoch < epoch + 2) revert EpochStillClaimable(epoch);
```

**Suzaku:**
Fixed in commit [71e9093](https://github.com/suzaku-network/suzaku-core/pull/155/commits/71e9093a53160b0b641e170429a7dd56d36f272c).

**Cyfrin:** Verified.

## [M-15] Use unchecked block for increment operations in `distribute Rewards`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description**

In `Rewards::distributeRewards`, an `unchecked` block can be used to optimize gas consumption for increment operations inside the loop.

```solidity
function distributeRewards(uint48 epoch, uint48 batchSize) external onlyRole(REWARDS_DISTRIBUTOR_ROLE) {
    DistributionBatch storage batch = distributionBatches[epoch];
    uint48 currentEpoch = l1Middleware.getCurrentEpoch();

    if (batch.isComplete) revert AlreadyCompleted(epoch);
    // Rewards can only be distributed after a 2-epoch delay
    if (epoch >= currentEpoch - 2) revert RewardsDistributionTooEarly(epoch, currentEpoch - 2);

    address[] memory operators = l1Middleware.getAllOperators();
    uint256 operatorCount = 0;

    for (uint256 i = batch.lastProcessedOperator; i < operators.length && operatorCount < batchSize; i++) {
        // Calculate operator's total share based on stake and uptime
        _calculateOperatorShare(epoch, operators[i]);

        // Calculate and store vault shares
        _calculateAndStoreVaultShares(epoch, operators[i]);

        batch.lastProcessedOperator = i + 1;
        operatorCount++;
    }

    if (batch.lastProcessedOperator >= operators.length) {
        batch.isComplete = true;
    }
}
```

**Recommended Mitigation**

Introduce an `unchecked` block for increment operations to optimize gas usage.

```diff
function distributeRewards(uint48 epoch, uint48 batchSize) external onlyRole(REWARDS_DISTRIBUTOR_ROLE) {
    DistributionBatch storage batch = distributionBatches[epoch];
    uint48 currentEpoch = l1Middleware.getCurrentEpoch();

    if (batch.isComplete) revert AlreadyCompleted(epoch);
    // Rewards can only be distributed after a 2-epoch delay
    if (epoch >= currentEpoch - 2) revert RewardsDistributionTooEarly(epoch, currentEpoch - 2);

    address[] memory operators = l1Middleware.getAllOperators();
    uint256 operatorCount = 0;

-   for (uint256 i = batch.lastProcessedOperator; i < operators.length && operatorCount < batchSize; i++) {
+   for (uint256 i = batch.lastProcessedOperator; i < operators.length && operatorCount < batchSize;) {
        // Calculate operator's total share based on stake and uptime
        _calculateOperatorShare(epoch, operators[i]);

        // Calculate and store vault shares
        _calculateAndStoreVaultShares(epoch, operators[i]);

+       unchecked {
            batch.lastProcessedOperator = i + 1;
            operatorCount++;
+          i++;
+       }
    }

    if (batch.lastProcessedOperator >= operators.length) {
        batch.isComplete = true;
    }
}
```

**Suzaku:**
Fixed in commit [2fb0daf](https://github.com/suzaku-network/suzaku-core/commit/2fb0dafd684eeaf11b177602c5047d1e6ce2d715).

**Cyfrin:** Verified.

## [M-16] Vault initialization allows deposit whitelist with no management capability
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `VaultTokenized` contract can be initialized with deposit whitelist enabled but without any ability to add addresses to the whitelist. This creates a state where deposits are restricted to whitelisted addresses, but no addresses can be whitelisted, effectively blocking all deposits.

The issue occurs in the initialization validation logic that checks for role consistency:

```solidity
// File: VaultTokenized.sol
function _initialize(uint64, /* initialVersion */ address, /* owner */ bytes memory data) internal onlyInitializing {
    VaultStorageStruct storage vs = _vaultStorage();
    (InitParams memory params) = abi.decode(data, (InitParams));
    // [...truncated for brevity...]

    if (params.defaultAdminRoleHolder == address(0)) {
        if (params.depositWhitelistSetRoleHolder == address(0)) {
            if (params.depositWhitelist) {
                if (params.depositorWhitelistRoleHolder == address(0)) {
                    revert Vault__MissingRoles();
                }
            } else if (params.depositorWhitelistRoleHolder != address(0)) {
                revert Vault__InconsistentRoles();
            }
        }
        // [...code...]
    }
    // [...code...]
}
```
The vulnerability exists because the validation for ensuring consistent whitelist management only occurs when `params.depositWhitelistSetRoleHolder == address(0)`. If caller sets a `depositWhitelistSetRoleHolder` (who can toggle whitelist on/off) but doesn't set a `depositorWhitelistRoleHolder` (who can add addresses to the whitelist), the validation is bypassed completely.

This gap allows a vault to be created with:

- `depositWhitelist = true` (whitelist enabled)
- `depositWhitelistSetRoleHolder = someAddress` (someone can toggle the whitelist)
- `depositorWhitelistRoleHolder = address(0)` (no one can add addresses to the whitelist)


**Impact:** When a vault is initialized in this state:

- Deposits are restricted to whitelisted addresses only
- No one has the ability to add addresses to the whitelist
- No deposits can be made until whitelist is disabled completely
- The only recourse is to use the depositWhitelistSetRoleHolder to turn off whitelist entirely

**Proof of Concept:** Add following to `vaultTokenizedTest.t.sol`

```solidity
     // This demonstrates that when the vault is created with depositWhitelist=true
     // and depositWhitelistSetRoleHolder set but depositorWhitelistRoleHolder NOT set,
     // no deposits can be made until whitelist is turned off, because no one can add
     // addresses to the whitelist.
    function test_WhitelistInconsistency() public {
        // Create a vault with whitelisting enabled but no way to add addresses to the whitelist
        uint64 lastVersion = vaultFactory.lastVersion();

        // configuration:
        // 1. depositWhitelist = true (whitelist is enabled)
        // 2. depositWhitelistSetRoleHolder = alice (someone can toggle whitelist)
        // 3. depositorWhitelistRoleHolder = address(0) (no one can add to whitelist)
        address vaultAddress = vaultFactory.create(
            lastVersion,
            alice,
            abi.encode(
                IVaultTokenized.InitParams({
                    collateral: address(collateral),
                    burner: address(0xdEaD),
                    epochDuration: 7 days,
                    depositWhitelist: true, // Whitelist ENABLED
                    isDepositLimit: false,
                    depositLimit: 0,
                    defaultAdminRoleHolder: address(0), // No default admin
                    depositWhitelistSetRoleHolder: alice, // Alice can toggle whitelist
                    depositorWhitelistRoleHolder: address(0), // No one can add to whitelist
                    isDepositLimitSetRoleHolder: alice,
                    depositLimitSetRoleHolder: alice,
                    name: "Test",
                    symbol: "TEST"
                })
            ),
            address(delegatorFactory),
            address(slasherFactory)
        );

        vault = VaultTokenized(vaultAddress);

        assertEq(vault.depositWhitelist(), true);
        assertEq(vault.hasRole(vault.DEPOSIT_WHITELIST_SET_ROLE(), alice), true);
        assertEq(vault.hasRole(vault.DEPOSITOR_WHITELIST_ROLE(), address(0)), false);
        assertEq(vault.isDepositorWhitelisted(alice), false);
        assertEq(vault.isDepositorWhitelisted(bob), false);

        // Step 1: Try to make a deposit as bob - should fail because whitelist is on
        // and bob is not whitelisted
        collateral.transfer(bob, 100 ether);
        vm.startPrank(bob);
        collateral.approve(address(vault), 100 ether);
        vm.expectRevert(IVaultTokenized.Vault__NotWhitelistedDepositor.selector);
        vault.deposit(bob, 100 ether);
        vm.stopPrank();

        // Step 2: Alice tries to add bob to the whitelist - should fail because
        // she has the role to toggle whitelist but not to add addresses to it
        vm.startPrank(alice);
        vm.expectRevert(); // Access control error (alice doesn't have DEPOSITOR_WHITELIST_ROLE)
        vault.setDepositorWhitelistStatus(bob, true);
        vm.stopPrank();

        // Step 3: Alice tries to turn off whitelist (which she can do)
        vm.startPrank(alice);
        vault.setDepositWhitelist(false);
        vm.stopPrank();

        // Step 4: Now bob should be able to deposit
        vm.startPrank(bob);
        vault.deposit(bob, 100 ether);
        vm.stopPrank();

        // Verify final state
        assertEq(vault.activeBalanceOf(bob), 100 ether);
    }
```

**Recommended Mitigation:** Consider modifying the initialization validation logic to check for the consistency of whitelist configuration regardless of whether `depositWhitelistSetRoleHolder` is set.

```solidity
if (params.defaultAdminRoleHolder == address(0)) {
    if (params.depositWhitelist && params.depositorWhitelistRoleHolder == address(0)) {
        revert Vault__MissingRoles();
    }

    if (!params.depositWhitelist && params.depositorWhitelistRoleHolder != address(0)) {
        revert Vault__InconsistentRoles();
    }
     // [...code...]

}
```


**Suzaku:**
Fixed in commit [6b7f870](https://github.com/suzaku-network/suzaku-core/pull/155/commits/6b7f87075ae366f95fb2ebad4875f2802961799c).

**Cyfrin:** Verified.

## [M-17] Vault initialization allows zero deposit limit with no ability to modify causing denial of service
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `VaultTokenized` contract's initialization procedure allows a vault to be created with deposit limit feature enabled at a value of zero, but without any ability to change this limit. This creates a state where all deposits are effectively blocked, as the limit is set to zero, and no role exists to modify this limit.

The issue occurs in the initialization validation logic that checks for role consistency:

```solidity
// File: VaultTokenized.sol
function _initialize(uint64, /* initialVersion */ address, /* owner */ bytes memory data) internal onlyInitializing {
    VaultStorageStruct storage vs = _vaultStorage();
    (InitParams memory params) = abi.decode(data, (InitParams));
    // [...code...]

    if (params.defaultAdminRoleHolder == address(0)) {
        // [...code...]

        if (params.isDepositLimitSetRoleHolder == address(0)) { //@audit check only happens when deposit limit set holder is zero address
            if (params.isDepositLimit) {
                if (params.depositLimit == 0 && params.depositLimitSetRoleHolder == address(0)) {
                    revert Vault__MissingRoles();
                }
            } else if (params.depositLimit != 0 || params.depositLimitSetRoleHolder != address(0)) {
                revert Vault__InconsistentRoles();
            }
        }
    }
    // [...code...]
}
```
The vulnerability exists because the validation for ensuring a consistent deposit limit configuration only occurs when `params.isDepositLimitSetRoleHolder == address(0)`. If someone sets an `isDepositLimitSetRoleHolder` (who can toggle deposit limit on/off) but doesn't set a `depositLimitSetRoleHolder` (who can modify the limit value) while setting `depositLimit = 0`, the validation is bypassed completely.

This gap allows a vault to be created with:

- `isDepositLimit = true` (deposit limit enabled)
- `depositLimit = 0` (no deposits allowed)
- `isDepositLimitSetRoleHolder = someAddress` (someone can toggle the limit feature)
- `depositLimitSetRoleHolder = address(0)` (no one can modify the limit value)

**Impact:** When a vault is initialized in this state:

- Deposits are limited to a maximum of 0 (effectively blocking all deposits)
- No one has the ability to change the deposit limit
- No deposits can be made until the deposit limit feature is disabled completely
- The only recourse is to use the isDepositLimitSetRoleHolder to turn off the deposit limit feature entirely

This could lead to denial of service for vault deposits, especially if the vault design assumes that limit management would be available when the deposit limit feature is enabled.

**Proof of Concept:** Add following to `vaultTokenizedTest.t.sol`
```solidity
  // This demonstrates that when the vault is created with isDepositLimitSetRoleHolder
    // set but depositLimitSetRoleHolder NOT set,
    // deposit limit is enabled but no one can set the limit.
    function test_DepositLimitInconsistency() public {
        // Create a vault with deposit limit enabled but no way to change the limit
        uint64 lastVersion = vaultFactory.lastVersion();

        // configuration:
        // 1. isDepositLimit = true (deposit limit is enabled)
        // 2. depositLimit = 0 (zero limit)
        // 3. isDepositLimitSetRoleHolder = alice (alice can toggle the feature)
        // 4. depositLimitSetRoleHolder = address(0) (no one can set the limit)
        address vaultAddress = vaultFactory.create(
            lastVersion,
            alice,
            abi.encode(
                IVaultTokenized.InitParams({
                    collateral: address(collateral),
                    burner: address(0xdEaD),
                    epochDuration: 7 days,
                    depositWhitelist: false,
                    isDepositLimit: true, // Deposit limit ENABLED
                    depositLimit: 0, // Zero limit
                    defaultAdminRoleHolder: address(0), // No default admin
                    depositWhitelistSetRoleHolder: alice,
                    depositorWhitelistRoleHolder: alice,
                    isDepositLimitSetRoleHolder: alice, // Alice can toggle limit feature
                    depositLimitSetRoleHolder: address(0), // No one can set the limit
                    name: "Test",
                    symbol: "TEST"
                })
            ),
            address(delegatorFactory),
            address(slasherFactory)
        );

        vault = VaultTokenized(vaultAddress);

        // Verify initial state
        assertEq(vault.isDepositLimit(), true);
        assertEq(vault.depositLimit(), 0);
        assertEq(vault.hasRole(vault.IS_DEPOSIT_LIMIT_SET_ROLE(), alice), true);
        assertEq(vault.hasRole(vault.DEPOSIT_LIMIT_SET_ROLE(), address(0)), false);

        // Step 1: Try to make a deposit - should fail because limit is 0
        collateral.transfer(bob, 100 ether);
        vm.startPrank(bob);
        collateral.approve(address(vault), 100 ether);
        vm.expectRevert(IVaultTokenized.Vault__DepositLimitReached.selector);
        vault.deposit(bob, 100 ether);
        vm.stopPrank();

        // Step 2: Alice tries to set a deposit limit - should fail because
        // she can toggle the feature but not set the limit
        vm.startPrank(alice);
        vm.expectRevert(); // Access control error
        vault.setDepositLimit(1000 ether);
        vm.stopPrank();

        // Step 3: Alice turns off the deposit limit feature
        vm.startPrank(alice);
        vault.setIsDepositLimit(false);
        vm.stopPrank();

        // Step 4: Now bob should be able to deposit
        vm.startPrank(bob);
        vault.deposit(bob, 100 ether);
        vm.stopPrank();

        // Verify final state
        assertEq(vault.activeBalanceOf(bob), 100 ether);
    }
```

**Recommended Mitigation:** Consider modifying the initialization validation logic to check for the consistency of deposit limit configuration regardless of whether `isDepositLimitSetRoleHolder` is set.

```solidity
if (params.defaultAdminRoleHolder == address(0)) {
    // [...whitelist code...]

    if (params.isDepositLimit && params.depositLimit == 0 && params.depositLimitSetRoleHolder == address(0)) {
        revert Vault__MissingRoles();
    }

    if (!params.isDepositLimit && (params.depositLimit != 0 || params.depositLimitSetRoleHolder != address(0))) {
        revert Vault__InconsistentRoles();
    }
}
```

**Suzaku:**
Fixed in commit [6b7f870](https://github.com/suzaku-network/suzaku-core/pull/155/commits/6b7f87075ae366f95fb2ebad4875f2802961799c).

**Cyfrin:** Verified.

## [M-18] `change_points_program_expiration` is permissionless
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `change_points_program_expiration` function fails to verify that the `admin` account has actually signed the transaction. While the function checks that the provided admin account key matches the expected `operator_address` in the root state, it does not verify that the account is a signer using `admin.is_signer`. The comment indicates that the admin should be a signer (// [*`create_account` can be dosed with pre-funding*](#createaccount-can-be-dosed-with-prefunding) - Admin (Signer)), but this requirement is not enforced in the code so any normal user can pass admin pubkey and execute this instruction without even real admin signing it.
```rust
// Only checks that the admin key matches, but not checking if the admin has actually signed the transaction;
if root_state.operator_address != *admin.key {
    bail!(InvalidAdminAccount {
        expected_address: root_state.operator_address,
        actual_address: *admin.key,
    });
}
// Missing: if !admin.is_signer { ... }
```
**Impact:** Unauthorised access to supposiely admin gated functionality.

**Recommended Mitigation:** Make sure the `admin` adress not only matches the stored address but also is the signer
```rust
    if !admin.is_signer {
        bail!(InvalidAdminAccount {
            expected_address: root_state.operator_address,
            actual_address: *admin.key,
        });
    }
```
**Deriverse:** Fixed in commit: [8a479a](https://github.com/deriverse/protocol-v1/commit/8a479a06d86536deeb65eeeb2379df5520ba4595)

**Cyfrin:** Verified.

## [M-19] Users Cannot Change Their Vote Once Cast in a Voting Period
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The voting system prevents users from changing or revoking their votes once they have voted in a voting round. While this maybe an intentional design to prevent duplicate voting, it may impact user experience if users make mistakes or want to change their vote before the voting period ends.

In `voting`, the system checks if a user has already voted:

```rust
if client_community_state.header.last_voting_counter
    >= client_community_state.header.current_voting_counter
{
    bail!(AlreadyVoted);
}
```

After a successful `vote`, `last_voting_counter` is set to the current `voting_counter`, which prevents the user from voting again in the same round, even if they want to:
- Correct a mistaken vote
- Change their vote choice (e.g., from INCREMENT to DECREMENT)
- Revoke their vote

**Impact:** Users who make mistakes cannot correct them or they cannot change their vote if they change their mind during the voting period.

**Recommended Mitigation:** Consider allow vote changes with proper accounting.

**Deriverse:** Fixed in commit [1689196](https://github.com/deriverse/protocol-v1/commit/1689196a00d0f06adc8de510dc5f2806fbd7c0d9).

**Cyfrin:** Verified.

## [M-20] Redundant `FUNDER_ROLE` in `Linea Rollup Yield Extension`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** The `LineaRollupYieldExtension` contract defines a `FUNDER_ROLE` constant  with a comment indicating it is "The role required to call fund()". However, the `fund` function does not implement any access control and is callable by anyone:

```solidity
function fund() external payable virtual {
  if (msg.value == 0) revert NoEthSent();
  emit FundingReceived(msg.value);
}
```

The function lacks the `onlyRole(FUNDER_ROLE)` modifier, making the defined role constant redundant and potentially misleading to developers, auditors, and users reviewing the code.

**Impact:** While the `FUNDER_ROLE` definition does not create a security vulnerability on its own, it introduces misleading documentation that conflicts with the actual implementation. This could lead to:

1. Confusion for developers maintaining the codebase who might assume access control is enforced when it is not

2. Potential future implementation errors if developers attempt to grant/revoke the `FUNDER_ROLE` expecting it to control access to the `fund` function

According to another comment in the contract, the `fund` function is intentionally designed to "accept both permissionless donations and YieldManager withdrawals," which suggests the lack of access control is deliberate. However, this contradicts the presence of the `FUNDER_ROLE` constant and its associated documentation.

**Recommended Mitigation:** Remove the unused `FUNDER_ROLE` constant and its associated comment since the `fund` function is intentionally permissionless. This will eliminate the inconsistency between the documentation and implementation.

If access control on the `fund` function is desired, add the `onlyRole(FUNDER_ROLE)` modifier. However, this would conflict with the stated intent to accept permissionless donations.

**Linea:** Fixed in commit [9876bc5](https://github.com/Consensys/linea-monorepo/commit/9876bc50dec4e614ad103d336361592a36a007bc).

**Cyfrin:** Verified.

## [M-21] Remove todo comments
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Remove "todo" comments:
```solidity
LineaRollup.sol
38:  // TODO - Add access control to proxy admin only
```

**Linea:** Fixed in commit [d8f57d5](https://github.com/Consensys/linea-monorepo/commit/d8f57d5d7f6abf043502a3e2e9c04b40b8a2df19).

**Cyfrin:** Verified.

## [M-22] `Setters Governor::set Whitelist Status` allows values other than 0 and 1 potentially leading to DOS
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** Until Parallel protocol added `setWhitelistStatus` the only way to change the `whitelistStatus` in the `isWhitelistedForType` mapping was to use `SettersGuardian::toggleWhitelist`.

It is clear from this code that the only "reachable" values values are `0` and `1`, since the value starts initialised at `0` and `1 - 0 == 1` and `1 - 1 == 0`.

However `setWhitelistStatus` actually allows values in the range 2 - 255. If a governor were to call it with any of these values this leads to a DOS on any function that indirectly calls `LibWhitelist::checkWhitelist`

The root causes are marked lines in `LibSetters::setWhitelistStatus`.

```solidity
    if (whitelistStatus == 1) {
    ...
    } else {
        // If whitelist is revoked, clear the whitelist data
@>      collatInfo.whitelistData = "";
    }
@>  collatInfo.onlyWhitelisted = whitelistStatus;
```

If called with `whitelistStatus > 1` then `collatInfo.whitelistData` is set to empty bytes and `collatInfo.onlyWhitelisted > 1` after execution.

If we later call a function that indirectly calls `_redeem` or `_swap` then the following following statement is executed

```solidity
if (collatInfo.onlyWhitelisted > 0 && !LibWhitelist.checkWhitelist(collatInfo.whitelistData, to)) {
    revert NotWhitelisted();
}
```

Since `collatInfo.onlyWhitelisted > 1` we now call `LibWhitelist.checkWhitelist`

Unfortunately this will revert on the first line in the `abi.decode`

```solidity
function checkWhitelist(bytes memory whitelistData, address sender) internal returns (bool) {
@>  (WhitelistType whitelistType, bytes memory data) = abi.decode(whitelistData, (WhitelistType, bytes));
```
**Impact:** The protocol will be DOSed for any swaps or redeems. The impact is low since governance can just call it again with `whitelistStatus == 0` and the chance of making this mistake in the first place is low.

However, if `SettersGovernor::setAccessManager` were called with an `AccessManager` that were configured to impose delays the DOS could be more serious. See [LibDiamond::checkCanCall](https://github.com/parallel-protocol/parallel-core/blob/main/Parallel-Parallelizer/contracts/parallelizer/libraries/LibDiamond.sol#L31-L46) and the `delay > 0` branch.

**Proof of Concept:** In `tests/units/parallel-protocolWhitelistStatusDos.t.sol` we have
- [test_parallel-protocol_WhitelistStatusTwo_DOSesBurnSwapExactInput](https://github.com/parallel-protocol/parallel-core/blob/audit/100proof/Parallel-Parallelizer/tests/units/parallel-protocolWhitelistStatusDos.t.sol#L20-L46) which tests
- [test_parallel-protocol_WhitelistStatusTwo_DOS_RequiresDelayToUndo](https://github.com/parallel-protocol/parallel-core/blob/audit/100proof/Parallel-Parallelizer/tests/units/parallel-protocolWhitelistStatusDos.t.sol#L48C12-L104) which shows delays can make the DOS more serious. It lasts as long as the `delay` set for the `GOVERNOR_ROLE`.
```solidity
// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.28;

import "contracts/parallelizer/Storage.sol";
import "contracts/utils/Constants.sol";
import { ISettersGovernor } from "contracts/interfaces/ISetters.sol";
import { MockChainlinkOracle } from "tests/mock/MockChainlinkOracle.sol";
import { Fixture } from "../Fixture.sol";

contract CyfrinWhitelistStatusDos is Fixture {
  function _refreshOracles() internal {
    // The oracle configs use a 1-hour stale period. We warp a full day to model the delay,
    // so we must refresh all collateral oracles or burns will revert with InvalidChainlinkRate.
    MockChainlinkOracle(address(oracleA)).setLatestAnswer(int256(BASE_8));
    MockChainlinkOracle(address(oracleB)).setLatestAnswer(int256(BASE_8));
    MockChainlinkOracle(address(oracleY)).setLatestAnswer(int256(BASE_8));
  }

  function test_cyfrin_WhitelistStatusTwo_DOSesBurnSwapExactInput() public {
    uint256 amountIn = 100 * BASE_6;

    vm.startPrank(alice);
    deal(address(eurA), alice, amountIn);
    eurA.approve(address(parallelizer), type(uint256).max);
    uint256 minted = parallelizer.swapExactInput(
      amountIn, 0, address(eurA), address(tokenP), alice, block.timestamp + 1
    );
    tokenP.approve(address(parallelizer), type(uint256).max);
    vm.stopPrank();

    uint256 snap = vm.snapshotState();
    vm.startPrank(alice);
    parallelizer.swapExactInput(minted, 0, address(tokenP), address(eurA), alice, block.timestamp + 1);
    vm.stopPrank();
    vm.revertToState(snap);

    bytes memory whitelistData = abi.encode(WhitelistType.BACKED, bytes(""));
    hoax(governor);
    parallelizer.setWhitelistStatus(address(eurA), 2, whitelistData);

    vm.startPrank(alice);
    vm.expectRevert();
    parallelizer.swapExactInput(minted, 0, address(tokenP), address(eurA), alice, type(uint256).max);
    vm.stopPrank();
  }

  function test_cyfrin_WhitelistStatusTwo_DOS_RequiresDelayToUndo() public {
    uint256 amountIn = 100 * BASE_6;

    vm.startPrank(alice);
    deal(address(eurA), alice, amountIn);
    eurA.approve(address(parallelizer), type(uint256).max);
    uint256 minted = parallelizer.swapExactInput(
      amountIn, 0, address(eurA), address(tokenP), alice, block.timestamp + 1
    );
    tokenP.approve(address(parallelizer), type(uint256).max);
    vm.stopPrank();

    // Set a 1-day delay for governor actions.
    vm.startPrank(governor);
    accessManager.grantRole(GOVERNOR_ROLE, governor, 86400);
    vm.stopPrank();
    (,, uint32 pendingDelay, uint48 effect) = accessManager.getAccess(GOVERNOR_ROLE, governor);
    if (pendingDelay > 0 && effect > block.timestamp) {
      vm.warp(effect);
    }
    (, uint32 currentDelay,,) = accessManager.getAccess(GOVERNOR_ROLE, governor);

    bytes memory whitelistData = abi.encode(WhitelistType.BACKED, bytes(""));
    bytes memory setToTwo =
      abi.encodeCall(ISettersGovernor.setWhitelistStatus, (address(eurA), uint8(2), whitelistData));

    vm.startPrank(governor);
    accessManager.schedule(address(parallelizer), setToTwo, 0);
    // Must wait the delay before executing the scheduled op.
    vm.warp(block.timestamp + currentDelay);
    accessManager.execute(address(parallelizer), setToTwo);
    vm.stopPrank();

    _refreshOracles();
    vm.startPrank(alice);
    vm.expectRevert();
    parallelizer.swapExactInput(minted, 0, address(tokenP), address(eurA), alice, type(uint256).max);
    vm.stopPrank();

    bytes memory clearWhitelist =
      abi.encodeCall(ISettersGovernor.setWhitelistStatus, (address(eurA), uint8(0), bytes("")));

    vm.startPrank(governor);
    accessManager.schedule(address(parallelizer), clearWhitelist, 0);
    // Cannot execute immediately; must wait the delay.
    vm.expectRevert();
    accessManager.execute(address(parallelizer), clearWhitelist);
    vm.warp(block.timestamp + currentDelay);
    accessManager.execute(address(parallelizer), clearWhitelist);
    vm.stopPrank();

    _refreshOracles();
    vm.startPrank(alice);
    parallelizer.swapExactInput(minted, 0, address(tokenP), address(eurA), alice, type(uint256).max);
    vm.stopPrank();
  }
}
```

**Recommended Mitigation:** Add a check at the beginning of `LibSetters::setWhitelistStatus`

```diff
  function setWhitelistStatus(address collateral, uint8 whitelistStatus, bytes memory whitelistData) internal {
+   if (whitelistStatus > 1) revert InvalidWhitelistStatus();
    Collateral storage collatInfo = s.transmuterStorage().collaterals[collateral];
    if (collatInfo.decimals == 0) revert NotCollateral();
```

**Parallel:** Fixed in commit [3010a17](https://github.com/parallel-protocol/parallel-parallelizer/commit/3010a17b3780a508e27d4a8200e9c73a61addf99#diff-41e3c405851499899c192341a0bd4b5587ba64730ba738b5db5ebba0a08de5c2).

**Cyfrin:** Verified. Implemented recommended mitigation.

## [M-23] Check return value when calling `Allowlist::exchange Allowed` and `Remora Token::_exchange Allowed` to prevent unauthorized transfers
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `Allowlist::exchangeAllowed` will revert if the users are not allowed but when the users are both allowed, it will return a boolean determined by whether the `domestic` field of both users match:
```solidity
function exchangeAllowed(
    address from,
    address to
) external view returns (bool) {
    HolderInfo memory fromUser = _allowed[from];
    HolderInfo memory toUser = _allowed[to];
    if (from != address(0) && !fromUser.allowed)
        revert UserNotRegistered(from);
    if (to != address(0) && !toUser.allowed) revert UserNotRegistered(to);
    return fromUser.domestic == toUser.domestic; //logic to be edited later on
}
```

But `RemoraToken::adminTransferFrom` doesn't check the boolean return when calling `Allowlist::exchangeAllowed`:
```solidity
function adminTransferFrom(
    address from,
    address to,
    uint256 value,
    bool checkTC,
    bool enforceLock
) external restricted returns (bool) {
    // @audit boolean return not checked
    IAllowlist(allowlist).exchangeAllowed(from, to);
```

Similary `RemoraToken::_exchangeAllowed` returns the boolean output of `Allowlist::exchangeAllowed`, but this is never checked in `RemoraToken::transfer`, `transferFrom`.

**Impact:** Transfers are allowed even when `Allowlist::exchangeAllowed` returns `false`.

**Recommended Mitigation:** Check the boolean return of `Allowlist::exchangeAllowed`, `RemoraToken::_exchangeAllowed` and only allow transfers when they return `true`.

Alternatively change `Allowlist::exchangeAllowed` and `RemoraToken::_exchangeAllowed` to not return anything but to always revert.

**Remora:** Fixed in commit [13cf261](https://github.com/remora-projects/remora-smart-contracts/commit/13cf261d37f5756cac480aa1e0c8ecf756fd3af5).

**Cyfrin:** Verified.

## [M-24] `Accountable Yield::set Nav Grace Period` uses `Unauthorized` error for invalid input
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `AccountableYield.setNavGracePeriod()` reverts with `Unauthorized()` when `period < MIN_NAV_GRACE_PERIOD`, even though this is an input validation failure rather than an access control issue.

Consider using a dedicated error for invalid parameters (e.g., `InvalidNavGracePeriod()`), or reuse a generic input-validation error.

**Accountable:** Fixed in commit [`d051169`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/d05116991e253ad2e348604c3ca50770ee554607)

**Cyfrin:** Verified.

## [M-25] Consider emitting events early to save gas
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Function `DVNPublisherFactory.setImplementation` can emit event `ImplementationSet` before the `implementation` state change to avoid creating and accessing an unnecessary memory variable.

[`DVNPublisherFactory.sol#L34`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/factory/DVNPublisherFactory.sol#L34)
```solidity
function setImplementation(address implementation_) external onlyOwner {
        address oldImplementation = implementation;
        implementation = implementation_;
        emit ImplementationSet(oldImplementation, implementation_);
    }
```

Similar instances exist in the `DVNPublisher` and `AccountableYield` contract:

[`DVNPublisher.sol#L125`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/publisher/DVNPublisher.sol#L125)
```solidity
function setThreshold(uint256 threshold_) external onlyManager {
        if (threshold_ > MAX_THRESHOLD || threshold_ == 0) revert InvalidThreshold();

        uint256 oldThreshold = threshold;
        threshold = threshold_;

        emit ThresholdSet(oldThreshold, threshold_);
    }
```

[`DVNPublisher.sol#L153`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/publisher/DVNPublisher.sol#L153)

```solidity
function setMaxStaleness(uint256 maxStaleness_) external onlyManager {
        if (maxStaleness_ == 0) revert ZeroValue();

        uint256 oldMaxStaleness = maxStaleness;
        maxStaleness = maxStaleness_;

        emit MaxStalenessSet(oldMaxStaleness, maxStaleness_);
    }
```

[`DVNPublisher.sol#L163`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/publisher/DVNPublisher.sol#L163)
```solidity
    /// @inheritdoc IDVNPublisher
    function setMaxDeviation(uint256 maxDeviation_) external onlyManager {
        uint256 oldMaxDeviation = maxDeviation;
        maxDeviation = maxDeviation_;

        emit MaxDeviationSet(oldMaxDeviation, maxDeviation_);
    }
```

[`AccountableYield.sol#L226`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L226)
```solidity
function setNavGracePeriod(uint256 period) external onlyManager {
        if (period < MIN_NAV_GRACE_PERIOD) revert Unauthorized();

        uint256 oldPeriod = navGracePeriod;
        navGracePeriod = period;

        emit NavGracePeriodSet(oldPeriod, period);
    }
```

**Recommended Mitigation:** Consider emitting the event early before the state update.

**Accountable:** Fixed in commit [`1a7ce24`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/1a7ce24cd0a84ed56386c8061778480640ab8364)

**Cyfrin:** Verified.

\clearpage

## [M-26] Missing modifiers on `Yield Strategy Factory.create Yield Strategy` can lead to deployment of unverified strategies
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Function `createYieldStrategy` enables permissionless deployment of `AccountableYield` strategies. However, during the deployment process, the function does not:
1. Verify the paused status using the `whenNotPaused` modifier
2. Verify the transaction authentication data using `onlyVerified` (if a signer is set)
3. Verify whether the asset is whitelisted using `onlyWhitelistedAsset`

**Proof of Concept:** As we can observe, other strategy factories such as `OpenTermFactory` and `FixedTermFactory` implement this verification.

[`YieldStrategyFactory.sol`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/main2/src/factory/YieldStrategyFactory.sol)
```solidity
function createYieldStrategy(YieldFactoryParams memory params)
        external
        returns (address strategyProxy, address vault)
    {
```

[`OpenTermFactory.sol`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/main2/src/factory/OpenTermFactory.sol)
```solidity
function createOpenTermLoan(OpenTermFactoryParams memory params)
        external
        whenNotPaused
        onlyVerified
        onlyWhitelistedAsset(params.asset)
        returns (address strategyProxy, address vault)
    {
```

[`FixedTermFactory.sol`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/main2/src/factory/FixedTermFactory.sol)
```solidity
function createFixedTermLoan(FixedTermFactoryParams memory params)
        external
        whenNotPaused
        onlyVerified
        onlyWhitelistedAsset(params.asset)
        returns (address strategyProxy, address vault)
    {
```

**Recommended Mitigation:** Consider applying the `whenNotPaused`, `onlyVerified` and `onlyWhitelistedAsset` modifiers on the function `createYieldStrategy`.

**Accountable:** Fixed in commit [`f8d4a3f`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/f8d4a3fbb19ea995cc27a7a8fb4a9896129247e7)

**Cyfrin:** Verified. Modifiers now applied.

\clearpage

## [M-27] Prefix internal and private function names with `_` character
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** It is considered good practice in Solidity to prefix internal and private function names with `_` character. This is done sometimes but not other times; ideally apply this consistently:
```solidity
predeposit/PreDepositPhaser.sol
15:    function setYieldPhaseInner () internal {

predeposit/yUSDeDepositor.sol
54:    function deposit_pUSDe (address from, uint256 amount, address receiver) internal returns (uint256) {
62:    function deposit_pUSDeDepositor (address from, IERC20 asset, uint256 amount, address receiver) internal returns (uint256) {

predeposit/PreDepositVault.sol
59:    function onAfterDepositChecks () internal view {
64:    function onAfterWithdrawalChecks () internal view {

predeposit/pUSDeVault.sol
93:    function _deposit(address caller, address receiver, uint256 assets, uint256 shares) internal override {
115:    function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal override {
177:    function stakeUSDe(uint256 USDeAssets) internal returns (uint256) {

predeposit/yUSDeVault.sol
43:    function _convertAssetsToUSDe (uint pUSDeAssets, bool withYield) internal view returns (uint256) {
79:    function _deposit(address caller, address receiver, uint256 pUSDeAssets, uint256 shares) internal override {
86:    function _withdraw(address caller, address receiver, address owner, uint256 pUSDeAssets, uint256 shares) internal override {
101:    function _valueMulDiv(uint256 value, uint256 mulValue, uint256 divValue, Math.Rounding rounding) internal view virtual returns (uint256) {

predeposit/MetaVault.sol
84:    function _deposit(address token, address caller, address receiver, uint256 baseAssets, uint256 tokenAssets, uint256 shares) internal virtual {
160:    ) internal virtual {
175:    function requireSupportedVault(address token) internal view {
191:    function addVaultInner (address vaultAddress) internal {
209:    function removeVaultAndRedeemInner (address vaultAddress) internal {
231:    function redeemMetaVaults () internal {
240:    function redeemRequiredBaseAssets (uint baseTokens) internal {

predeposit/pUSDeDepositor.sol
92:    function deposit_sUSDe (address from, uint256 amount, address receiver) internal returns (uint256) {
102:    function deposit_USDe (address from, uint256 amount, address receiver) internal returns (uint256) {
114:    function deposit_viaSwap (address from, IERC20 token, uint256 amount, address receiver) internal returns (uint256) {
146:    function getPhase () internal view returns (PreDepositPhase phase) {

test/ethena/StakedUSDe.sol
190:  function _checkMinShares() internal view {
203:    internal
225:    internal
239:  function _updateVestingAmount(uint256 newVestingAmount) internal {
251:  function _beforeTokenTransfer(address from, address to, uint256) internal virtual {

test/ethena/SingleAdminAccessControl.sol
72:  function _grantRole(bytes32 role, address account) internal override returns (bool) {
```

**Strata:** Fixed in commit [b154fec](https://github.com/Strata-Money/contracts/commit/b154fec8957a81b3c0cf6e204e894d60bb0d852b).

**Cyfrin:** Verified.

## [M-28] `Securitize On Ramp::swap` and `Securitize Off Ramp::redeem` pass operator as investor address resulting in denial of service
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `SecuritizeOnRamp::swap` and `SecuritizeOffRamp::redeem` have modifier `onlyRole(OPERATOR_ROLE)` meaning only an operator can call these functions.

But when calling child functions such as `BaseOnRamp::_swap` or `BaseOffRamp::_redeem`, they pass `_msgSender()` as the investor wallet which is incorrect since the operator and the investor are not the same entities.

**Impact:** The most likely impact is temporary denial of service; these functions will revert as the operator is not also an investor. But the contracts are upgradeable so can be fixed or in a worst-case scenario re-deployed.

**Recommended Mitigation:** If these functions are designed to be called by investors then remove the modifier `onlyRole(OPERATOR_ROLE)`.

Otherwise if they are supposed to be called by an operator, then add an input parameter to specify the investor address.

Also see the related issue M-1 "Incorrect use of `investorExists` modifier in `PublicStockOnRamp::swap`" which may also be relevant here.

**Securitize:** Fixed in commit [5cbd6d8](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/5cbd6d82e9bff57c6441334897e8ef0c9c594825) by removing the `onlyRole` as these functions are intended to be directly called by investors.

**Cyfrin:** Verified.

\clearpage

## [M-29] Incorrect use of `investor Exists` modifier in `Public Stock On Ramp::swap`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `PublicStockOnRamp::swap` functions incorrectly validates investor registration. These functions use the `investorExists` modifier which checks if `msg.sender` is a registered wallet, but they also have the `onlyRole(OPERATOR_ROLE)` modifier, meaning `msg.sender` is always the operator, not the actual investor.
The actual investor is passed as the `_investorWallet` , but this address is never validated against the registry:

```solidity
 function swap(
        uint256 _liquidityAmount,
        uint256 _minOutAmount,
        address _investorWallet,
        bytes memory _investorSignature,
        uint8 _marketStatus,
        uint256 _anchorPrice,
        uint256 _anchorPriceExpiresAt
    )
        public
        whenNotPaused
        investorExists <--------
        initializedNavProvider
        validateMinSubscriptionAmount(_liquidityAmount)
        nonZeroAnchorPrice(_anchorPrice)
        onlyRole(OPERATOR_ROLE)
    {...}
```
The `investorExists` modifier checks `_msgSender()` which resolves to `msg.sender`:

```solidity
 modifier investorExists() {
        IDSRegistryService registryService = IDSRegistryService(dsToken.getDSService(dsToken.REGISTRY_SERVICE()));
        if (!registryService.isWallet(_msgSender())) {
            revert InvestorNotRegisteredError();
        }
        _;
    }

```

Since the operator calls the function, the modifier validates whether the operator is registered, not whether `_investorWallet` (the actual investor receiving the tokens) is registered.

**Impact:** * If operators themselves had valid investor wallets, then they could execute swaps for completely unregistered investors, bypassing the entire investor registration system
* If operators don't themselves have valid investor wallets then calls to `PublicStockOnRamp::swap` will revert resulting in denial of service

**Recommended Mitigation:** Replace the `investorExists` modifier with an inline check that validates the `_investorWallet` parameter instead of `msg.sender`:

```solidity
modifier investorWalletExists(address _wallet) {
    IDSRegistryService registryService = IDSRegistryService(
        dsToken.getDSService(dsToken.REGISTRY_SERVICE())
    );
    if (!registryService.isWallet(_wallet)) {
        revert InvestorNotRegisteredError();
    }
    _;
}
```

**Securitize:** Fixed in commit [090cd62](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/090cd62fd656fb0aaf969de1bcc0a84db5523581).

**Cyfrin:** Verified.

## [M-30] Missing `liquidity Token` validation in `Collateral Liquidity Provider::initialize`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The `CollateralLiquidityProvider::setExternalCollateralRedemption` function includes a validation check to ensure the liquidity token of the new external collateral redemption contract matches the existing `liquidityToken`:

```solidity
function setExternalCollateralRedemption(address _externalCollateralRedemption) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_externalCollateralRedemption == address(0)) {
            revert NonZeroAddressError();
        }

        if (
            address(
                ILiquidityProvider(address(ISecuritizeOffRamp(_externalCollateralRedemption).liquidityProvider()))
                    .liquidityToken()
            ) != address(liquidityToken)//@audit-ok (low) why this i not checked in intializatuion
        ) {
            revert LiquidityTokenMismatch();
        }
        address oldExternalCollateral = address(externalCollateralRedemption);
        externalCollateralRedemption = ISecuritizeOffRamp(_externalCollateralRedemption);
        emit ExternalCollateralRedemptionUpdated(oldExternalCollateral, address(externalCollateralRedemption));
    }
```

However, `CollateralLiquidityProvider::initialize` sets the same `externalCollateralRedemption` without performing this validation:

```solidity
function initialize(
    address _liquidityToken,
    address _recipient,
    address _securitizeOffRamp,
    address _externalCollateralRedemption,
    address _collateralProvider
) public onlyProxy initializer {
    // ... zero address checks only ...

    liquidityToken = IERC20Metadata(_liquidityToken);
    externalCollateralRedemption = ISecuritizeOffRamp(_externalCollateralRedemption);
    ...
    //@audit missing validation that _externalCollateralRedemption's liquidity token matches _liquidityToken
}
```

**Impact:** During contract deployment, an admin could mistakenly initialize the contract with an `_externalCollateralRedemption` that uses a different liquidity token than the configured `_liquidityToken`.

**Recommended Mitigation:** Add the liquidity token validation to the  `CollateralLiquidityProvider::initialize`.

**Securitize:** Fixed in commit [d8fd4fb](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/d8fd4fb9c38ed4d006df7ace366d30de239d6d4a).

**Cyfrin:** Verified.

## [M-31] Redundant Access Control Check in `Securitize Internal Nav Provider::add Rate Updater, remove Rate Updater`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `SecuritizeInternalNavProvider::addRateUpdater, removeRateUpdater` perform redundant access control checks. These functions have an `onlyRole(DEFAULT_ADMIN_ROLE)` modifier, but then call `grantRole/revokeRole` which internally perform the same check:

```solidity
  function addRateUpdater(address _account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(RATE_UPDATER, _account);
        emit RateUpdaterAdded(_account);
    }
```
Since `RATE_UPDATER` admin role defaults to `DEFAULT_ADMIN_ROLE`, both checks require the same role, resulting in duplicate authorization verification and unnecessary gas consumption.

**Recommended Mitigation:** Use the internal `_grantRole` and `_revokeRole` functions directly since access control is already enforced by the function modifiers:

**Securitize:** Fixed in commit [77a9a52](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/77a9a5295ca55f3d62df3ecc8517217598bf4deb).

**Cyfrin:** Verified.

## [M-32] `Trust Service::remove Role` doesn't delete already owned entities so address which lost role can still manage existing entities
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `TrustService::removeRole` doesn't delete entities so address which lost role can still manage existing entities.

**Proof of Concept:** Add PoC to `test/trust-service.test.ts`:
```typescript
    it('Should demonstrate orphaned entity relationships after role removal', async function() {
      const [owner, entityOwner, operator, resource] = await hre.ethers.getSigners();
      const { trustService } = await loadFixture(deployDSTokenRegulated);

      // Step 1: Give entityOwner ISSUER role
      await trustService.setRole(entityOwner, DSConstants.roles.ISSUER);
      expect(await trustService.getRole(entityOwner)).equal(DSConstants.roles.ISSUER);

      // Step 2: Create an entity owned by entityOwner
      const entityName = "TestEntity";
      const trustServiceFromEntityOwner = await trustService.connect(entityOwner);
      await trustServiceFromEntityOwner.addEntity(entityName, entityOwner);

      // Verify entity ownership
      expect(await trustService.getEntityByOwner(entityOwner)).equal(entityName);

      // Step 3: Add operator and resource to the entity
      await trustServiceFromEntityOwner.addOperator(entityName, operator);
      await trustServiceFromEntityOwner.addResource(entityName, resource);

      // Verify operator and resource are linked to entity
      expect(await trustService.getEntityByOperator(operator)).equal(entityName);
      expect(await trustService.getEntityByResource(resource)).equal(entityName);

      // Step 4: Remove entityOwner's ISSUER role
      await trustService.removeRole(entityOwner);
      expect(await trustService.getRole(entityOwner)).equal(DSConstants.roles.NONE);

      // Step 5: Demonstrate the bug - entity relationships still exist
      // These should ideally be cleaned up but they're not:
      expect(await trustService.getEntityByOwner(entityOwner)).equal(entityName);  // Still owns entity!
      expect(await trustService.getEntityByOperator(operator)).equal(entityName);   // Still linked!
      expect(await trustService.getEntityByResource(resource)).equal(entityName);  // Still linked!

      // Step 6: Show the security issue - entityOwner can still manage the entity
      // even without any role
      await expect(
        trustServiceFromEntityOwner.addOperator(entityName, hre.ethers.Wallet.createRandom())
      ).to.not.be.reverted;  // This should fail but doesn't!

      // The onlyEntityOwnerOrAbove modifier still passes because:
      // - entityOwner has NONE role (not MASTER/ISSUER)
      // - But ownersEntities[entityOwner] still equals entityName
      // - So the check passes even though they shouldn't have access
    });
```

**Recommended Mitigation:** When an address loses its role, delete entities it previously owned by clearing the entity ownership mappings.

**Securitize:** Fixed in commit [6cd6cca](https://github.com/securitize-io/dstoken/commit/6cd6ccae7201082e53befd6364aff8a1f57397f7); the relevant storage slots were deprecated and the associated functions were removed.

**Cyfrin:** Verified.

## [M-33] Don't perform storage reads unless necessary
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive; don't perform storage reads unless necessary.

* `contracts/service/ServiceConsumer.sol`
```diff
// in `onlyMaster` don't load trust manager unless required
    modifier onlyMaster {
-        IDSTrustService trustManager = getTrustService();
-        require(owner() == msg.sender || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
+        if(owner() != msg.sender) require(getTrustService().getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        _;
    }
```

**Securitize:** Fixed in commit [1ab6fd9](https://github.com/securitize-io/dstoken/commit/1ab6fd99a2a6814b23ec7e51359ced72159bfe80).

**Cyfrin:** Verified.

## [M-34] Investor can prevent themselves from being removed by making `remove Investor` revert
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The `removeInvestor` function in `RegistryService.sol` contains a flaw that allows any investor to permanently prevent their removal from the system. The function requires that `investors[_id].walletCount == 0` before allowing investor removal, but investors can add unlimited wallets via `addWalletByInvestor` without any restrictions, while only `EXCHANGE` roles can remove wallets via `removeWallet`.

```solidity
function removeInvestor(string calldata _id) public override onlyExchangeOrAbove investorExists(_id) returns (bool) {
        require(getTrustService().getRole(msg.sender) != EXCHANGE || investors[_id].creator == msg.sender, "Insufficient permissions");
        require(investors[_id].walletCount == 0, "Investor has wallets"); <----------

        for (uint8 index = 0; index < 16; index++) {
            delete attributes[_id][index];
        }

        delete investors[_id];

        emit DSRegistryServiceInvestorRemoved(_id, msg.sender);

        return true;
    }
```

This creates a permanent DoS condition where malicious investors can add wallets to prevent their own removal

**Impact:** `removeInvestor` can be DoS, making an investor unremovable.

**Recommended Mitigation:** Consider removing `addWalletByInvestor`.

**Securitize:** Fixed in commit [05c5bad](https://github.com/securitize-io/dstoken/commit/05c5bada3c2801b1333fc96f4abc5226a84471f0) by removing `addWalletByInvestor`.

**Cyfrin:** Verified.

## [M-35] Resolve inconsistency between `DSToken::check Wallets For List` and `Registry Service::remove Wallet`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `DSToken::checkWalletsForList` only removes wallets if their balance is zero:
```solidity
function checkWalletsForList(address _from, address _to) private {
    if (super.balanceOf(_from) == 0) {
        removeWalletFromList(_from);
    }
```

But `RegistryService::removeWallet` allows removing wallets with positive balances:
```solidity
function removeWallet(address _address, string memory _id) public override onlyExchangeOrAbove walletExists(_address) walletBelongsToInvestor(_address, _id) returns (bool) {
    require(getTrustService().getRole(msg.sender) != EXCHANGE || investorsWallets[_address].creator == msg.sender, "Insufficient permissions");

    delete investorsWallets[_address];
    investors[_id].walletCount--;

    emit DSRegistryServiceWalletRemoved(_address, _id, msg.sender);

    return true;
}
```

**Impact:** Wallets with positive balances can be removed via `RegistryService::removeWallet` which prevents token transfers and other related activity that depends on functions from `RegistryService` returning investor ids for given wallet addresses.

**Recommended Mitigation:** `RegistryService::removeWallet` shouldn't allow removing wallets with positive balances.

**Securitize:** Fixed in commit [1eaec18](https://github.com/securitize-io/dstoken/commit/1eaec18ce4a9dc6be24c43d02950839341b6282d#diff-8abf57cc60f7fc1ff193a0912746e8539f56be2d652f1bb59fa5ea8ef3c43d97R177-R178).

**Cyfrin:** Verified.

## [M-36] Use named mapping parameters to explicitly note the purpose of keys and values
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Use named mapping parameters to explicitly note the purpose of keys and values:
```solidity
token/TokenLibrary.sol
36:        mapping(address => uint256) walletsBalances;
37:        mapping(string => uint256) investorsBalances;

mocks/TestToken.sol
39:    mapping(address => uint256) balances;
40:    mapping(address => mapping(address => uint256)) allowed;

data-stores/TokenDataStore.sol
27:    mapping(address => mapping(address => uint256)) internal allowances;
28:    mapping(uint256 => address) internal walletsList;
30:    mapping(address => uint256) internal walletsToIndexes;

swap/SecuritizeSwap.sol
43:    mapping(string => uint256) internal noncePerInvestor;

utils/TransactionRelayer.sol
48:    mapping(bytes32 => uint256) internal noncePerInvestor;

utils/MultiSigWallet.sol
46:    mapping(address => bool) isOwner; // immutable state

data-stores/RegistryServiceDataStore.sol
44:        // Ref: https://docs.soliditylang.org/en/v0.7.1/070-breaking-changes.html#mappings-outside-storage
45:        // mapping(uint8 => Attribute) attributes;
48:    mapping(string => Investor) internal investors;
49:    mapping(address => Wallet) internal investorsWallets;
52:     * @dev DEPRECATED: This mapping is no longer used but must be kept for storage layout compatibility in the proxy.
53:     * Do not use this mapping in new code. It will be removed in future non-proxy implementations.
56:    mapping(address => address) internal DEPRECATED_omnibusWalletsControllers;
58:    mapping(string => mapping(uint8 => Attribute)) public attributes;

data-stores/InvestorLockManagerDataStore.sol
24:    mapping(string => mapping(uint256 => Lock)) internal investorsLocks;
25:    mapping(string => uint256) internal investorsLocksCounts;
26:    mapping(string => bool) internal investorsLocked;
27:    mapping(string => mapping(bytes32 => mapping(uint256 => Lock))) internal investorsPartitionsLocks;
28:    mapping(string => mapping(bytes32 => uint256)) internal investorsPartitionsLocksCounts;
29:    mapping(string => bool) internal investorsLiquidateOnly;

data-stores/TrustServiceDataStore.sol
23:    mapping(address => uint8) internal roles;
24:    mapping(string => address) internal entitiesOwners;
25:    mapping(address => string) internal ownersEntities;
26:    mapping(address => string) internal operatorsEntities;
27:    mapping(address => string) internal resourcesEntities;

data-stores/ComplianceConfigurationDataStore.sol
24:    mapping(string => uint256) public countriesCompliances;

data-stores/WalletManagerDataStore.sol
24:    mapping(address => uint8) internal walletsTypes;
25:    mapping(address => mapping(string => mapping(uint8 => uint256))) internal walletsSlots;

data-stores/ServiceConsumerDataStore.sol
23:    mapping(uint256 => address) internal services;

data-stores/LockManagerDataStore.sol
24:    mapping(address => uint256) internal locksCounts;
25:    mapping(address => mapping(uint256 => Lock)) internal locks;

data-stores/ComplianceServiceDataStore.sol
29:    mapping(string => uint256) internal euRetailInvestorsCount;
30:    mapping(string => uint256) internal issuancesCounters;
31:    mapping(string => mapping(uint256 => uint256)) issuancesValues;
32:    mapping(string => mapping(uint256 => uint256)) issuancesTimestamps;
```

**Securitize:** Fixed in commit [6c7bc52](https://github.com/securitize-io/dstoken/commit/6c7bc52d2c0eaacc06c8c6e26a7abfbd69d2edae).

**Cyfrin:** Verified.

## [M-37] Don't emit misleading events when roles haven't been added or revoked
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `AccessControlUpgradeable::_grantRole` and `_revokeRole` [return](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/access/AccessControlUpgradeable.sol#L204-L231) `bool` to indicate whether the role was actually granted or revoked.

**Impact:** Some functions using these don't check the `bool` return then emit events; such events will be misleading if the roles were not actually granted or revoked.

**Recommended Mitigation:** The affected functions are:
* `GlobalRegistryService::changeAdmin, addOperator, revokeOperator`

In these functions check the return of `_grantRole` and `_revokeRole` and only emit events if the roles were actually granted or revoked.

**Securitize:** Fixed in commit [c7d50ac](https://github.com/securitize-io/bc-global-registry-service-sc/commit/c7d50acbe661aae0edd62e54c91692d3ff3a35b9).

**Cyfrin:** Verified.

## [M-38] Incomplete mapping updates in `set Vault` function cause vault address inconsistencies
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `RWASegWrap::setVault` function allows admins to update the vault address for a specific vault ID, but it fails to properly maintain the bidirectional mapping between vault addresses and vault IDs. The function only updates `vaults[id] = vault` but does not update the `vaultIds` mapping, which should map the new vault address to the vault ID and clear the mapping for the old vault address.
This creates inconsistencies in the contract's state where the old vault address remains mapped to the vault ID in the `vaultIds` mapping, while the new vault address is not recognized by the system. The `vaultIds` mapping is critical for vault validation in functions like `isValidVault` and `getAssetId`, and is also used in `_addVault` to prevent duplicate vault registrations. The same issue exists in the `SecuritizeRWASegWrap` contract, which inherits from `RWASegWrap` and uses the same `setVault` implementation.

**Impact:** The incomplete mapping updates can cause vault operations to fail or behave unexpectedly, as the new vault address will not be recognized as valid by the system, while the old vault address may still appear valid even though it's no longer active.

**Recommended Mitigation:** Update the `setVault` function to properly maintain both mappings:

```diff
function setVault(
    address vault,
    uint256 id
) public virtual override onlyRole(DEFAULT_ADMIN_ROLE) idNotZero(id) recognizedVault(id) addressNotZero(vault) {
    address oldVault = vaults[id];
    address investorWallet = vaultIdOwnerWallets[id];
    vaults[id] = vault;
+   delete vaultIds[oldVault];
+   vaultIds[vault] = id;
    emit VaultUpdated(oldVault, vault, id, investorWallet);
}
```

**Securitize:** Fixed in commit [468bae](https://github.com/securitize-io/bc-securitize-vault-sc/commit/468bae9777ad341c700dcf30caec057f6ba101c3).

**Cyfrin:** Verified.

## [M-39] Incorrect function documentation
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `SegregatedVault::addAggregator` function contains incorrect documentation that mentions "Operators" instead of "Aggregators" in both the function description and parameter documentation. The comment states "Operators can deposit and redeem. Emits AggregatorAdded event" when it should describe aggregator capabilities, and the parameter description says "The address to which the Operator role will be granted" when it should reference the Aggregator role.

This appears to be a copy-paste error from the `addOperator` function documentation. The same issue exists in `SecuritizeVaultV2::addAggregator`.

Additionally, there is another inconsistency in `SegregatedVault::revokeAggregator` where the comment states "Revokes the Operator role from an account. Emits a OperatorRevoked event" when it should reference the Aggregator role and AggregatorRevoked event.

**Impact:** Incorrect documentation may confuse developers and auditors about the intended role permissions and capabilities, potentially leading to integration errors or security misunderstandings.

**Recommended Mitigation:** Update the documentation to correctly describe aggregator role capabilities and parameters:

```diff
/**
 * @dev Grants the aggregator role to an account.
- * Operators can deposit and redeem. Emits AggregatorAdded event
+ * Aggregators can manage vault operations and perform deposits/redeems on behalf of the protocol. Emits AggregatorAdded event
 *
- * @param account The address to which the Operator role will be granted.
+ * @param account The address to which the Aggregator role will be granted.
 */
function addAggregator(address account) external addressNotZero(account) onlyRole(DEFAULT_ADMIN_ROLE) {
    _grantRole(AGGREGATOR_ROLE, account);
    emit AggregatorAdded(account);
}
```

Apply similar fixes to `SegregatedVault::revokeAggregator` and `SecuritizeVaultV2::addAggregator` functions.

**Securitize:** Fixed in commits [0e881e](https://github.com/securitize-io/bc-securitize-vault-sc/commit/0e881e38f9ec600d7ee5b1b7555a4ab81eaa04d1) and [402daa](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/402daa31d16471b24ea42810d613064b38256a00).

**Cyfrin:** Verified.

## [M-41] `STBL_Register::add Asset` does not check for non-empty asset name
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** `STBL_Register::setupAsset` allows an assets to be created with empty names. However, elsewhere in the code, the `STBL_AssetDefinitionLib::isValid` function marks an an asset with empty name field as invalid.  This creates an inconsistency where assets can be successfully created and enabled in the protocol but would fail validation checks via the `isValid` function.

```solidity
// STBL_Register.sol - addAsset function
function addAsset(
    string memory _name,    // @audit No validation on name field
    string memory _desc,
    uint8 _type,
    bool _aggType
) external onlyRole(REGISTER_ROLE) returns (uint256) {
    unchecked {
        assetCtr += 1;
    }
    assetData[assetCtr].id = assetCtr;
    assetData[assetCtr].name = _name;        // @audit Can be empty string
    assetData[assetCtr].description = _desc;
    assetData[assetCtr].contractType = _type;
    assetData[assetCtr].isAggreagated = _aggType;
    assetData[assetCtr].status = AssetStatus.INITIALIZED;

    emit AddAssetEvent(assetCtr, assetData[assetCtr]);
    return assetCtr;
}
```
`isValid` function marks this asset invalid:

```solidity
// STBL_AssetDefinitionLib.sol
function isValid(AssetDefinition memory asset) internal pure returns (bool) {
    return
        asset.id != 0 &&
        bytes(asset.name).length > 0 &&  // ✅ Requires non-empty name
        asset.token != address(0) &&
        asset.issuer != address(0) &&
        asset.rewardDistributor != address(0) &&
        asset.vault != address(0);
}
```

The `isValid()` function is currently unused in the main protocol contracts but is imported in test files, suggesting it was intended for validation but never properly integrated into the protocol flow.

**Impact:** Inconsistent validation logic and potential off-chain integration issues.


**Recommended Mitigation:** Consider adding name validation to `addAsset` or remove name requirement from `isValid`

**STBL:** Fixed in commit [4a187a5](https://github.com/USD-Pi-Protocol/contract/commit/4a187a54fa0f5e268f4fb43305e88e37ed512c08)

**Cyfrin:** Verified.

## [M-42] Missing check if `receiver` is whitelisted in `Staking Vault::mint, deposit`
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault::mint, deposit` only validates that `msg.sender` is whitelisted but fails to check if the receiver parameter is whitelisted. Since non-whitelisted addresses cannot withdraw, redeem, or transfer shares, any shares minted to non-whitelisted receivers become permanently locked and unusable.
```solidity
 function mint(
        uint256 shares,
        address receiver //@audit receiver could be not whitelisted?
    ) public override onlyWhitelisted(msg.sender) returns (uint256 assets) {
        ...
    }
```

**Impact:** Permanent loss of user funds or temporary if owner give whitelisted permissions.

**Proof of Concept:** Run the next proof of concept in `StakingVault.sol`:
```solidity
function test_mint_non_whitelist_receiver() public {
        uint256 amount = 100 ether;

        vm.startPrank(user1);
        asset.approve(address(vault), amount);

        //create a non whitelisted receiver
        address bob = makeAddr("receiver");

        // 1. Alice (whitelisted) mints shares to Bob (non-whitelisted)
        vault.mint(1000 * 1e8, bob); // Success - only checks Alice is whitelisted

        vm.stopPrank();

        // 2. Bob tries to withdraw - REVERTS
        vm.prank(bob);
        vault.withdraw(1000 * 1e8, bob, bob); // Reverts: not whitelisted
        // Result: 1000 shares worth of HilBTC permanently locked
    }

```

**Recommended Mitigation:** Add a whitelist check for the receiver in the mint() function:

```diff
function mint(
    uint256 shares,
    address receiver
+ ) public override onlyWhitelisted(msg.sender) onlyWhitelisted(receiver) returns (uint256 assets) {
-   ) public override onlyWhitelisted(msg.sender) returns (uint256 assets) {
 ...
}
// Similar fix to `deposit`
```

**Syntetika:**
Fixed in commit [86384fe](https://github.com/SyntetikaLabs/monorepo/commit/86384fe1504780338649d25f720fb78b25132875) by removing the whitelist functionality entirely from `StakingVault` to resolve finding L-4.

**Cyfrin:** Verified.

## [M-43] Owner can not burn tokens from blacklisted addresses
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** The `HilBTC.sol` contract contains a logical inconsistency in its `burnFrom()` function regarding blacklisted addresses. While the function grants the `owner` special privileges to burn tokens from any user without requiring allowance (bypassing the `_spendAllowance` check), the underlying `_burn()` function calls `_update()` which contains the `notBlacklisted(from)` modifier. This prevents the owner from burning tokens from blacklisted addresses:
```solidity
 function burnFrom(address from, uint256 amount) external {
        address spender = msg.sender;
        if (spender != from && spender != owner()) {
            _spendAllowance(from, spender, amount);
        }
        _burn(from, amount);
    } //@audit owner can not burn from Blacklisted

    function _update(address from, address to, uint256 amount)
        internal
        override
        notBlacklisted(from)
        notBlacklisted(to)
    {
        super._update(from, to, amount);
    }
```

**Impact:** Owner can not burn tokens from blacklisted addresses.

**Recommended Mitigation:** If you want the owner to have the capability to burn blacklisted user tokens, consider creating a special access control function where the direct `_balances` of the backlisted user is reduced.

**Syntetika:**
Fixed in commit [dc14ad2](https://github.com/SyntetikaLabs/monorepo/commit/dc14ad2c7dacf389deb24fcdca155b5b0acb52d4).

**Cyfrin:** Verified.

\clearpage

## [M-44] Roles not set in `deposit-registry` contract constructors
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Roles in contracts that belong to the `issuance` contracts are being initialized in the constructors and contain proper functions to update the address for this roles (revoke and grant):

```solidity
constructor(
        string memory _name,
        string memory _symbol,
        address _initialAdmin,
        address _minter
    ) ERC20(_name, _symbol) Ownable(_initialAdmin) {
        require(
            _minter != address(0) && _initialAdmin != address(0),
            AddressCantBeZero()
        );
        minter = _minter;
        blacklister = _initialAdmin;
        _grantRole(DEFAULT_ADMIN_ROLE, _initialAdmin);
        _grantRole(MINTER_ROLE, _minter);
    }

function setMinter(
        address newMinter
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newMinter != address(0), AddressCantBeZero());
        revokeRole(MINTER_ROLE, minter);
        minter = newMinter;
        _grantRole(MINTER_ROLE, newMinter);
    }
```

But roles are not being initialized in the constructors of contracts in `deposit-registry`:
```solidity
bytes32 public constant COMPLIANCE_ADMIN_ROLE = keccak256("COMPLIANCE_ADMIN_ROLE");

    constructor(address defaultAdmin) {
        // The defaultAdmin can grant other roles later
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
    }
```

Consider initializing `COMPLIANCE_ADMIN_ROLE` in the constructor of the `ComplianceChecker` contract.
Consider initializing `CANCELER_ROLE` in the constructor of the `CompliantDepositRegistry` contract.

**Syntetika:**
Fixed in commit [9fccd3b](https://github.com/SyntetikaLabs/monorepo/commit/9fccd3b18f1543b10352e8c26fe4c59877bcf11d).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-45] Combination of Ownable and Access Control can cause loss of admin functionality
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** `BasisTradeTailor` and `BasisTradeVault` mix `Ownable(2Step)Upgradeable` with `AccessControlUpgradeable`. Several admin wrappers are `onlyOwner` but internally call `grantRole` / `revokeRole`, which themselves require the caller to hold the role’s admin (usually `DEFAULT_ADMIN_ROLE`). Example:

```solidity
function grantAdmin(address account) external onlyOwner {
    grantRole(ADMIN_ROLE, account); // requires DEFAULT_ADMIN_ROLE too
}
```

This creates a dual requirement: the caller must be both `owner` and `DEFAULT_ADMIN_ROLE`. If those identities diverge (e.g., ownership transferred without also granting default admin), governance gets brittle and confusing.

**Impact:** The “Owner” may be unable to manage roles (grant/revoke admin/agent) and a `DEFAULT_ADMIN_ROLE` holder who isn’t `owner` can’t upgrade (since `_authorizeUpgrade` is `onlyOwner`) as well as extra wrappers duplicate functionality and enlarge the attack surface/bytecode/ABI for no gain.

**Proof of Concept:** Add the following test to `BasisTradeVault.t.sol` (a very similar test would work for Tailor):
```solidity
function test_OwnerLosesGrantAbility() public {
    _setupComplete();

    // owner transfers ownership
    vm.prank(deployer);
    vault.transferOwnership(alice);
    assertEq(vault.owner(), alice);

    // new owner cannot grant admin (or agent) roles
    vm.prank(alice);
    vm.expectRevert(
        abi.encodeWithSelector(
            IAccessControl.AccessControlUnauthorizedAccount.selector,
            alice,
            bytes32(0x00)
        )
    );
    vault.grantAdmin(bob);
}
```

**Recommended Mitigation:** Consider unifying on AccessControl by removing Ownable entirely. Gate privileged functions with `onlyRole(DEFAULT_ADMIN_ROLE)` and authorize upgrades via the same role:

  ```solidity
function grantAdmin(address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
    grantRole(ADMIN_ROLE, account);
}

function _authorizeUpgrade(address impl) internal override onlyRole(DEFAULT_ADMIN_ROLE) {}
```
Then delete the bespoke wrappers `grantAdmin`, `revokeAdmin`, `grantAgent`, `revokeAgent` altogether. `DEFAULT_ADMIN_ROLE` already has authority to call `grantRole` / `revokeRole` directly, so these wrappers are redundant. Removing them shrinks bytecode/ABI, reduces surface area, and tidies the contracts.
To prevent lockout: use `AccessControlEnumerableUpgradeable` and enforce at least one default admin remains:
```solidity
function _revokeRole(bytes32 role, address account) internal override {
    if (role == DEFAULT_ADMIN_ROLE) {
        require(getRoleMemberCount(DEFAULT_ADMIN_ROLE) > 1, "keep >=1 default admin");
    }
    super._revokeRole(role, account);
}
```
Or if keeping `Ownable` is prefered, synchronize roles on ownership changes (grant new owner `DEFAULT_ADMIN_ROLE` and revoke from old).

**Button:** Fixed in commit [`32f8ca9`](https://github.com/buttonxyz/button-protocol/commit/32f8ca9c9e08986a554e12d3581178419b3d71f9) by moving to AccessControlEnumerableUpgradeable only.

**Cyfrin:** Verified. `AccessControlEnumerableUpgradeable` now used for both Tailor and Vault. The grant/revoke calls also removed in favor or AccessControls own calls.

\clearpage

## [M-47] `DEFAULT_ADMIN_ROLE` can be mistakenly granted to an account when granting permission to call `fallback` on any contract
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** `AccessControlManager` is in charge of managing roles and permissions for accounts to determine what users can call on which contracts.

Permissions are granted at the selector level, and is possible to grant permissions to only one contract at a time, or authorize an account to call the same selector on any contract.

There is an edge case when permitting an account to call the `fallback()` function whose selector is `bytes4(0)` on any account (address(0)).
- The combination of those two inputs results in calculating the role as bytes(0), which is the exact value assigned for the DEFAULT_ADMIN_ROLE.

```solidity
    function grantCall(address contractAddress, bytes4 sel, address accountToPermit) public {
//@audit-issue => The calculated role for `address(0)` and `bytes4(0)` is bytes32(0)`
        bytes32 role = roleFor(contractAddress, sel);
//@audit-issue => Granting bytes32(0) to the account results in granting the DEFAULT_ADMIN_ROLE
        grantRole(role, accountToPermit);
        emit PermissionGranted(accountToPermit, contractAddress, sel);
    }

    function roleFor(address contractAddress, bytes4 sel) internal pure returns (bytes32 role) {
//@audit-issue => The calculated role for `address(0)` and `bytes4(0)` is bytes32(0)`
        role = (bytes32(uint256(uint160(contractAddress))) << 96) | bytes32(uint256(uint32(sel)));
    }

```

**Impact:** Users can be mistakenly granted the DEFAULT_ADMIN_ROLE, which they can then use to authorize other users to call restricted functions.

**Proof of Concept:** Add the next PoC to `CDO.t.sol` test file:
1. Alice gets DEFAULT_ADMIN_ROLE by mistake when she was meant to receive permission to call fallback() on any contract
2. Once Alice has DEFAULT_ADMIN_ROLE, he authorizes Bob to call other functions on a different contract.
```solidity
    function test_grantsDefaultAdminByMisstake() public {
        bytes32 DEFAULT_ADMIN_ROLE = acm.DEFAULT_ADMIN_ROLE();

        address contractAddress = address(0);
        bytes4 selector = bytes4(0);

        address alice = makeAddr("Alice");

        assertFalse(acm.hasRole(DEFAULT_ADMIN_ROLE, alice));

        //@audit-issue => Granting permission to alice to call fallback function on any contract results on granting Alice the DEFAULT_ADMIN_ROLE
        acm.grantCall(contractAddress, selector, alice);
        assertTrue(acm.hasRole(DEFAULT_ADMIN_ROLE, alice));

        address contractA = makeAddr("contractA");
        address bob = makeAddr("bob");
        bytes4 withdrawSelector = bytes4(keccak256(bytes("withdraw(address,uint256)")));

        assertFalse(acm.hasPermission(bob, contractA, withdrawSelector));

        //@audit-info => Alice w/ DEFAULT_ADMIN can grant permissions to other accounts
        vm.startPrank(alice);
        acm.grantCall(contractA, withdrawSelector, bob);
        assertTrue(acm.hasPermission(bob, contractA, withdrawSelector));
    }

```

**Recommended Mitigation:** Validate that the computed role is not the DEFAULT_ADMIN_ROLE; otherwise, revert the tx.
```diff
    function grantCall(address contractAddress, bytes4 sel, address accountToPermit) public {
        bytes32 role = roleFor(contractAddress, sel);
+       require(role != DEFAULT_ADMIN_ROLE, "Granting DEFAULT_ADMIN_ROLE");
        grantRole(role, accountToPermit);
        emit PermissionGranted(accountToPermit, contractAddress, sel);
    }
```

**Strata:**
Fixed in commit [e6ad2d](https://github.com/Strata-Money/contracts-tranches/commit/e6ad2d59f1ad9abab0a9af685aeea8d510e9169d) by adding a check to revert when `contractAddress` is `address(0)` or `selector` is `bytes(0)`

**Cyfrin:** Verified. New change prevents from mistakenly assign DEFAULT_ADMIN_ROLE.
Permissions are granted on a per-contract per-selector basis.


\clearpage

## [M-48] `Pocket Factory::approve Tailor` doesn't verify `ITailor` interface implementation
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** The `PocketFactory.approveTailor()` function only validates that the tailor address is non-zero and has code, but doesn't verify it implements the `ITailor` interface required for pocket management operations. There is also no such check in `ApproveTailorInFactory.s.sol`

```solidity
// PocketFactory.sol:56-62
function approveTailor(address tailor) external onlyRole(OPERATOR_ROLE) {
    require(tailor != address(0), "Invalid tailor address");
    require(tailor.code.length > 0, "Tailor must be a contract");  // Only checks has code

    approvedTailors[tailor] = true;
    emit TailorApproved(tailor);
}
```

**Recommended Mitigation:** Add an ERC-165 interface check in `approveTailor()`. Also consider adding this check to the `ApproveTailorInFactory.s.sol` deployment script as an additional safety layer.

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->
