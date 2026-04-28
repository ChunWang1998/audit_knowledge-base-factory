# auth/policy-enforcement - Issues

- Count: 11

## F-2026-14935 - Auction Mode Bypass in bulkTransferTokens AllowsTransfers During Active Auctions
- 嚴重度：Medium
- Report source：Dexalot.pdf

### 問題內容（完整）
The bulkTransferTokens function does not validate auction mode beforetransferring tokens, unlike the public transferToken function. This allowstokens under auction restrictions to be transferred, potentially underminingauction integrity by enabling early distribution of auction tokens. The public transferToken function includes an auction mode check: require(tokenDetailsMap[`_symbol`].auctionMode == ITradePairs.AuctionMode.`OFF`, "P-`AUCT`-01"); However, bulkTransferTokens calls the private transferToken function directlywithout this validation: function bulkTransferTokens( address `_from`, address `_to`, bytes32[] calldata `_symbols`, uint256[] calldata `_quantities` ) external whenNotPaused nonReentrant { require(`_from` == `msg.sender` || hasRole(`TRUSTED_TRANSFER_ROLE`, msg.sen der), "P-`OOWN`-03"); require(`_to` != `msg.sender`, "P-`DOTS`-01"); require(`_symbols`.length == `_quantities`.length, "P-`ARLM`-01"); for (uint256 i = 0; i < `_symbols`.length; ) { bytes32 symbol = `_symbols`[i]; uint256 quantity = `_quantities`[i]; `require(tokenList.contains(symbol)`, "P-`ETNS`-01"); // No auction mode check before calling private transferToken transferToken(`_from`, `_to`, symbol, quantity, 0, Tx.`IXFERSENT`, fals e, `address(0)`); unchecked { i++; } } } This creates an inconsistency where single-token transfers respect auctionrestrictions while bulk transfers bypass them. This can lead to: Auction integrity violation: Tokens under auction can be transferredbefore the auction concludes. 27 Early token distribution: Auction tokens can be distributed torecipients who should not have access until the auction ends.Inconsistent behavior: Single and bulk transfer functions havedifferent security guarantees for the same operation. Assets: `contracts/PortfolioSub.sol`[https://github.com/Dexalot/contracts/commits/omnivaults/] Status: Fixed

### 修補方式（建議）
The auction mode check should be added to the bulkTransferTokens loopbefore calling the private transferToken: require(tokenDetailsMap[symbol].auctionMode == ITradePairs.AuctionMode.`OFF`, " P-`AUCT`-01"); This ensures consistent auction mode enforcement regardless of whethersingle or bulk transfer is used. Resolution: Fixed in 0e1526e: bulkTransferTokens now enforces the same auction-mode restriction as transferToken by adding: The bypass path described in the issue is removed, and transfer behavioris now consistent between single-transfer and bulk-transfer flows forauction-restricted tokens. 28

### 修補方式（實際）
Fixed in 0e1526e: bulkTransferTokens now enforces the same auction-mode restriction as transferToken by adding: require(tokenDetailsMap[symbol].auctionMode == ITradePairs.AuctionMode.`OFF`, " P-`AUCT`-01"); The bypass path described in the issue is removed, and transfer behavioris now consistent between single-transfer and bulk-transfer flows forauction-restricted tokens. 28

## F-2026-15965 - Incomplete Blacklist Enforcement in transferFromAllows Blacklisted Callers to Bypass Transfer Restrictions
- 嚴重度：High
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, blacklist enforcement is applied only to the sender addressand does not cover either `msg.sender` or recipient. As a result, a blacklistedaddress can still initiate transfers through transferFrom when acting as anapproved spender for a non-blacklisted account. The blacklist mechanismtherefore fails to prevent blocked actors from continuing to move tokens. In KnoxNet, the transferFrom function forwards execution to `_transferFrom`,which in turn applies blacklist checks through `_enforceTxLimit`. However,only the sender parameter is checked: function `transferFrom( address sender, address recipient, uint256 amount )` external override returns (bool) { // … return `_transferFrom`(sender, recipient, amount); function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { // … `require(blacklist[sender] == 0, "Wallet blacklisted!")`; } This logic assumes that the token owner and the transaction initiator arethe same actor. That assumption does not hold for transferFrom, where `msg.sender` is the spender. A blacklisted address can therefore obtainallowance from a non-blacklisted wallet and continue transferring orselling that walletʼs tokens. Since recipient is not checked either,blacklisted addresses may still receive tokens. Blacklisted addresses remain able to operate through the allowance flowand are not effectively excluded from token activity. The anti-bot and 11 administrative restriction mechanism can therefore be bypassed inpractice. Blacklisted recipients may also continue accumulating tokens. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
Blacklist validation should be applied to all relevant actors in the transferpath: sender, recipient, and `msg.sender`. function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; require( amount <= (liquidityPools[sender] ? `_maxBuyTxAmount` : `_maxSellTxAmount` ), "Amount exceeds the tx limit." ); `require(blacklist[sender] == 0, "Sender blacklisted!")`; `require(blacklist[recipient] == 0, "Recipient blacklisted!")`; require(blacklist[`msg.sender`] == 0, "Caller blacklisted!"); } Resolution: Fixed inc20e980: In KnoxNet, blacklist validation now covers all relevant actors in thetransfer path. The `_enforceTxLimit` function checks sender, recipient, and `_msgSender`, which prevents a blacklisted spender from using transferFrom 12 on behalf of a non-blacklisted holder and prevents transfers to blacklistedrecipients. The allowance-based blacklist bypass described in the findingis therefore no longer present. function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { `require(blacklist[sender] == 0, "Sender blacklisted!")`; require(blacklist[`_msgSender`()] == 0, "Caller blacklisted!"); if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; TransferType transferType = `_classifyTransfer`(sender, recipient); uint256 maxTxAmount = transferType == TransferType.Sell ? `_maxSellTxAmount` : `_maxBuyTxAmount`; `require( amount <= maxTxAmount, "Amount exceeds the tx limit." )`;

### 修補方式（實際）
Fixed inc20e980: In KnoxNet, blacklist validation now covers all relevant actors in thetransfer path. The `_enforceTxLimit` function checks sender, recipient, and `_msgSender`, which prevents a blacklisted spender from using transferFrom 12 on behalf of a non-blacklisted holder and prevents transfers to blacklistedrecipients. The allowance-based blacklist bypass described in the findingis therefore no longer present. function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { `require(blacklist[sender] == 0, "Sender blacklisted!")`; `require(blacklist[recipient] == 0, "Recipient blacklisted!")`; require(blacklist[`_msgSender`()] == 0, "Caller blacklisted!"); if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; TransferType transferType = `_classifyTransfer`(sender, recipient); uint256 maxTxAmount = transferType == TransferType.Sell ? `_maxSellTxAmount` : `_maxBuyTxAmount`; `require( amount <= maxTxAmount, "Amount exceeds the tx limit." )`;

## F-2026-15974 - Blacklist Enforcement Bypassed When Recipient IsTransaction-Limit Exempt
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, the blacklist check resides inside `_enforceTxLimit` after anearly-return guard that exits when either party is transaction-limit exempt.If the recipient holds isTxLimitExempt status, the function returns before the blacklist[sender] check is evaluated. A blacklisted sender can thereforetransfer tokens to any tx-limit-exempt address without restriction. In KnoxNet, the `_enforceTxLimit` function combines two logically distinctconcerns, transaction size limits and blacklist enforcement, under a singleexemption guard: function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; require( amount <= (liquidityPools[sender] ? `_maxBuyTxAmount` : `_maxSellTxAmount` ), "Amount exceeds the tx limit." ); `require(blacklist[sender] == 0, "Wallet blacklisted!")`; } The early return on the first line exits unconditionally when either sender or recipient is exempt. The blacklist check on the last line is therefore neverreached. Several addresses are marked as tx-limit exempt duringconstruction: isTxLimitExempt[`address(this)`] = true; isTxLimitExempt[`owner()`] = true; isTxLimitExempt[routerAddress] = true; isTxLimitExempt[`DEAD`] = true; Any additional address granted exemption via setIsTxLimitExempt becomesan unrestricted transfer target for blacklisted senders as well. Blacklisted addresses can transfer tokens to the contract, the owner, therouter, the dead address, and any future tx-limit-exempt address. Thispartially defeats the blacklist mechanism. If a `DEX` pool or user wallet islater granted tx-limit exemption, blacklisted addresses can freely transfertokens to it. 29 Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
Blacklist enforcement should be decoupled from the transaction-limitexemption check. The blacklist validation should execute unconditionallybefore the early return. Resolution: Fixed in c20e980: In KnoxNet, blacklist enforcement has been moved ahead of thetransaction-limit exemption guard within `_enforceTxLimit`. The function nowchecks sender, recipient, and `_msgSender` against the blacklist beforeevaluating isTxLimitExempt, so tx-limit exemption no longer bypassesblacklist restrictions. The previously described path allowing blacklistedsenders to transfer to exempt addresses is therefore removed. function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { `require(blacklist[sender] == 0, "Sender blacklisted!")`; `require(blacklist[recipient] == 0, "Recipient blacklisted!")`; require(blacklist[`_msgSender`()] == 0, "Caller blacklisted!"); if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; TransferType transferType = `_classifyTransfer`(sender, recipient); uint256 maxTxAmount = transferType == TransferType.Sell ? `_maxSellTxAmount` : `_maxBuyTxAmount`; 30 `require(amount <= maxTxAmount, "Amount exceeds the tx limit.")`; } 31

### 修補方式（實際）
Fixed in c20e980: In KnoxNet, blacklist enforcement has been moved ahead of thetransaction-limit exemption guard within `_enforceTxLimit`. The function nowchecks sender, recipient, and `_msgSender` against the blacklist beforeevaluating isTxLimitExempt, so tx-limit exemption no longer bypassesblacklist restrictions. The previously described path allowing blacklistedsenders to transfer to exempt addresses is therefore removed. function `_enforceTxLimit`( address sender, address recipient, uint256 amount ) internal view { `require(blacklist[sender] == 0, "Sender blacklisted!")`; `require(blacklist[recipient] == 0, "Recipient blacklisted!")`; require(blacklist[`_msgSender`()] == 0, "Caller blacklisted!"); if (isTxLimitExempt[sender] || isTxLimitExempt[recipient]) return; TransferType transferType = `_classifyTransfer`(sender, recipient); uint256 maxTxAmount = transferType == TransferType.Sell ? `_maxSellTxAmount` : `_maxBuyTxAmount`; 30 `require(amount <= maxTxAmount, "Amount exceeds the tx limit.")`; } 31

## F-2025-14461 - Fee-on-Transfer / Rebasing Tokens Break Accounting- Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The depositToken() function assumes that the Pool contract receivesexactly the amount of tokens specified by the user. However, thisassumption does not hold for fee-on-transfer, deflationary, or rebasingERC20 tokens. When a user deposits such a token, the token contract may deduct atransfer fee, burn a portion of the amount, or otherwise reduce the numberof tokens actually transferred to the Pool. Despite this, the Pool credits theuserʼs internal balance by the full amount parameter, without verifying howmany tokens were actually received. As a result, the internal accounting can become inconsistent with the Poolʼs real token balance. The Pool may record a higher balance for theuser than the contract actually holds on-chain, leading to balance inflation. This inconsistency can later surface during on-chain withdrawals, forcedwithdrawals, or emergency exit flows, where the Pool attempts to transfertokens that it does not actually have. In such cases, withdrawals mayrevert or fail, effectively locking user funds or breaking the escape-hatchmechanism. Pool.sol — depositToken(): function depositToken(address token, uint256 amount) external whenNotPaused notContract nonReentrant { requi

### 修補方式（實際）
The deposit logic was updated to account for fee-on-transfer anddeflationary tokens by measuring the Poolʼs token balance before and afterthe transfer and crediting users only with the actual amount received incommit 322258e. function depositToken(uint256 amount) external whenNotPaused nonReentrant { require(usdcToken != address(0), Pool_Usdc0x()); require(amount > 0, Pool_AmountZero()); 29 uint256 balanceBefore = IERC20(usdcToken).balanceOf(address(this)); IERC20(usdcToken).safeTransferFrom(msg.sender, address(this), amount); uint256 balanceAfter = IERC20(usdcToken).balanceOf(address(this)); uint256 receivedAmount = balanceAfter - balanceBefore; require(receivedAmount > 0, Pool_NoTokenReceived()); uint256 userBalanceBefore = balances[msg.sender][usdcToken]; balances[msg.sender][usdcToken] += receivedAmount; emit Deposit(msg.sender, usdcToken, receivedAmount, balances[msg.sende r][usdcTo


## F-2026-14500 -  nalizeForceWithdrawal Silently Burns User BalanceWhen Pool Has Insu cient Token Balance - High
- 嚴重度：High
- Report source：BullBit.pdf

### 問題內容（摘要）
The finalizeForceWithdrawal() function in the Pool contract contains avulnerability where users can permanently lose their funds if the Pool contract's actual token balance is insufficient to cover the withdrawalamount. When the contract balance check fails, the function silently fallsthrough to a cross-chain withdrawal path that decrements the user'srecorded balance without transferring any tokens.The vulnerable code path is as follows: function finalizeForceWithdrawal(address _token) external notContract non Reentrant whenNotPaused { ForcedWithdrawalRequest memory request = forcedWithdrawalRequests[msg. sender][_token]; require(request.timestamp > 0, "Pool: no forced withdrawal initiated") ; require( block.timestamp >= request.timestamp + forceWithdrawDelay, "Pool: withdrawal delay not passed" ); uint256 amount = request.amount; string memory destination = request.destination; delete forcedWithdrawalRequests[msg.sender][_token]; // For on-chain assets, transfer tokens; for cross-chain, just emit ev ent as proof if (_token.code.length > 0) { // Try to transfer if it's an ERC20 contract try IERC20(_token).balanceOf(address(this)) returns (uint256 contr actBalance) { if (contractBal

### 修補方式（實際）
The force-withdrawal mechanism was entirely removed from the contractby eliminating the initiateForceWithdrawal() and finalizeForceWithdrawal() functions in commit 322258e. 19 Evidences PoC


## F-2025-13316 - Total Supply ERC-721 Enumeration Incompliance -Medium
- 嚴重度：Medium
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The DOI_Gold and DOI_Token contracts are ERC-721 tokenimplementations. The contracts declare totalSupply function whichaccording to EIP-721 standard is meant to return the number of validtokens tracked by the contract. function totalSupply() public view override returns (uint256) { return tokenCounter; } However, the tokenCounter variable (used as return value of the totalSupply function) represents increasing counter to be used astoken id for new tokens minted and does not consider token burnpossibility. The replaceToken function (admin restricted) of the DOI_Gold contractburns token and mints a new one with a new token id, causing the tokenCounter increase while the actual number of tokens is kept same. function replaceToken( uint256 oldTokenId, address recipient, string calldata reason ) external onlyAdmin { ... // Burn the old token _burn(oldTokenId); // Mint the new token uint256 newTokenId = tokenCounter + 1; tokenCounter = newTokenId; _safeMint(recipient, newTokenId); ... } This may lead to the totalSupply function return an invalid valuepotentially causing issues in external services.

### 修補方式（實際）
The Finding is ﬁxed in the commit c19b227. The custom totalSupply function declarations are removed. 23


## F-2025-13411 - Pausing Disables Allowance Revocation LeavingUsers Exposed During Emergencies - Medium
- 嚴重度：Medium
- Report source：NEBA Token.pdf

### 問題內容（摘要）
The token intentionally pauses transfers via ERC20PausableUpgradeable. Inaddition, approvals are also gated by the whenNotPaused modiﬁerthrough a custom _approve() override. This deviates fromOpenZeppelin’s default ERC20Pausable behavior, which does not pauseapprovals. // Approvals are disabled while paused function _approve(address owner, address spender, uint256 value, bool emitEve nt) internal virtual override whenNotPaused // <-- blocks *all* allowance changes during paus e { super._approve(owner, spender, value, emitEvent); } During a pause, users often want to rapidly reduce or zero-outallowances granted to DEXs, routers, custodians, bots, orcompromised third-party keys. Because _approve() function isguarded with the whenNotPaused modiﬁer, allowance changes—including reductions to 0—are rejected while the token is paused. As a result, users remain exposed to stale or compromised spendersfor the duration of a pause, exactly when risk is elevated (e.g., aDEX/router exploit discovered, API key leak, or phishing event).

### 修補方式（實際）
The approve() function does not enforce an unpaused status nowwithin the new implementation. Revised commit: 1f432d1. 9


## F-2025-14262 - Reusable Authentication Signatures Due to MissingNonce - Medium
- 嚴重度：Medium
- Report source：RYT-2.pdf

### 問題內容（摘要）
The DIDContract implements an authenticate function that verifies userauthentication through an ECDSA signature constructed from the DID,verification method, timestamp, and msg.sender. However, the functiondoes not incorporate any nonce, replay counter, or signature-trackingmechanism. As a result, any valid signature remains reusable for the entireduration of the proof.timestamp window. Because the message hash isdeterministic and contains no unique per-request value, the contractaccepts identical signatures multiple times without detecting replayattempts. function authenticate( string memory did, AuthenticationProof memory proof ) external whenNotPaused validDID(did) notExpired(proof.timestamp + 300) { ... // Verify the signature bytes32 messageHash = keccak256( abi.encodePacked( did, proof.verificationMethod, proof.timestamp, msg.sender ) ); bytes32 ethSignedMessageHash = ECDSA.toEthSignedMessageHash(messageHash); address signer = ECDSA.recover(ethSignedMessageHash, proof.signature); require( signer == didDocuments[did].owner || didControllers[didDocuments[did].owner].contains(signer), "DIDContract: Invalid signature" ); // Update user stats _updateUserStats(msg.sender); emit Aut

### 修補方式（實際）
Fixed in a695108, the authentication hash now includes the nonce which isincremented each time when the signature was used ensuring thatpreviously issued signatures become invalid: bytes32 messageHash = keccak256( abi.encodePacked( did, proof.verificationMethod, proof.timestamp, msg.sender, proof.nonce ) ); authNonces[msg.sender] = authNonces[msg.sender] + 1; 16


## F-2025-14269 - Possibility of Burning Incorrect Token Because ofMutable Credential Contract Address - Medium
- 嚴重度：Medium
- Report source：RYT-2.pdf

### 問題內容（摘要）
The DIDContract and SoulboundCredential contracts are designed to operatetogether. The soulbound credentials are minted through the DIDContract,which requires the credential contract address to be set beforehand. The revokeSBTCredential() function burns an existing ERC721 soulbound token byreferencing its token ID. function revokeSBTCredential(uint256 tokenId) external whenNotPaused sbtRequired { // Get the owner before burning address tokenOwner = sbtContract.ownerOf(tokenId); // Burn SBT through the SBT contract sbtContract.burnCredential(tokenId); emit SBTRevoked(msg.sender, tokenOwner, tokenId, block.timestamp); } The credential contract address can be modified by the contract owner atany time. function setSBTContract(address _sbtContract) external onlyOwner { require(_sbtContract != address(0), "DIDContract: Invalid SBT contract address"); sbtContract = SoulboundCredential(_sbtContract); sbtEnabled = true; emit SBTContractSet(_sbtContract); } If multiple instances of the SoulboundCredential contract exist, a modificationof the stored credential contract address while a revokeSBTCredential() transaction is pending in the mempool may result in a burn operationexecuted against a

### 修補方式（實際）
Fixed in a695108, the new sbtAddr param was introduced in the revokeSBTCredential() function that is used as the target address of the SoulboundCredential contract: function revokeSBTCredential(address sbtAddr, uint256 tokenId) external whenNotPaused sbtRequired onlyAuthorizedIssuer { if (sbtAddr == address(0)) revert InvalidSBTAddress(); SoulboundCredential target = SoulboundCredential(sbtAddr); ... } 18


## F-2025-14222 - Security Mechanisms Inoperative due toOpenZeppelin v5 Hook Incompatibility - High
- 嚴重度：High
- Report source：RYT.pdf

### 問題內容（摘要）
The RYTStablecoin contract is an ERC20 token that implements regulatory andsecurity compliance features. It relies on the _beforeTokenTransfer internalfunction to enforce two critical restrictions before any tokens are moved(minted, burned, or transferred):    Pausability: Transfers should revert if the contract is paused by anadmin.   Blocklisting: Transfers should revert if the sender or receiver is in theisBlocklisted mapping. The project dependencies include OpenZeppelin Contracts v5.4.0, but thecontract implements the _beforeTokenTransfer hook, which was removed inversion 5.0 and replaced by _update. Because the parent ERC20 implementation in v5 never calls _beforeTokenTransfer, the custom securitylogic in RYTStablecoin is effectively dead code. Consequently, the Pauseand Blocklist features are completely non-functional, allowing blockedusers to transfer funds and preventing the admin from halting the contractduring emergencies. In OpenZeppelin Contracts v5.0, the _beforeTokenTransfer and _afterTokenTransfer hooks were refactored into a single _update function.The RYTStablecoin.sol contract defines its security logic as follows: function _beforeTokenTransfer(address from, addr

### 修補方式（實際）
In file hash 851798d95a8fa81a37c950c9c2da0a4085a96f52e73d38eb2f044b56868adb21, thefix replaces the deprecated _beforeTokenTransfer hook with the correct _update override, ensuring that pausability and blocklisting checks areactually executed during all token transfers, mints, and burns. Evidences PoC #1

## F-2026-15162 - Deactivated Model Still Usable for Sessions and NodeRegistration
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
When the owner deactivates a model via deactivateModel, no enforcementexists in the session creation path to prevent new sessions from beingcreated against that model. The deactivation mechanism is effectivelybypassed. createSessionJobForModel and createSessionJobForModelWithToken validate that ahost supports a model by calling `nodeRegistry.nodeSupportsModel()`, whichonly checks the host's local supportedModels array: function `nodeSupportsModel(address nodeAddress, bytes32 modelId)` external view returns (bool) { bytes32[] memory models = nodes[nodeAddress].supportedModels; for (uint i = 0; i < models.length; i++) { if (models[i] == modelId) return true; } return false; } Neither the JobMarketplaceWithModelsUpgradeable session creationfunctions nor nodeSupportsModel ever call `modelRegistry.isModelApproved(modelId)` to verify the model is still active: JobMarketplaceWithModelsUpgradeable `require(nodeRegistry.nodeSupportsModel(host, modelId)`, "Host does not support model"); Model approval is checked only at node registration time (registerNode) andmodel update time (updateSupportedModels), but never at session creation.Once a host has the model in its local array, deactivation in ModelRegistryhas no downstream effect. A model deactivated by the owner for security reasons (e.g., compromisedweights, harmful outputs) continues to be available for new sessioncreation indefinitely. This renders the emergency deactivation mechanismineffective and exposes renters to inference from a model the ownerexplicitly deemed unsafe. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] 54 `src/NodeRegistryWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#]src/ModelRegistryUpgradeable.sol [https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
Add an isModelApproved check inJobMarketplaceWithModelsUpgradeable during model-aware sessioncreation, querying the ModelRegistry directly. Expose a reference toModelRegistry (either stored on JobMarketplace or accessed via `nodeRegistry.modelRegistry()`) and insert the check before the host-supportvalidation: `require(nodeRegistry.modelRegistry()`.`isModelApproved(modelId)`, "Model not act ive"); `require(nodeRegistry.nodeSupportsModel(host, modelId)`, "Host does not support model"); Apply this to both createSessionJobForModel and createSessionJobForModelWithToken. Resolution: Fixed in a49ef12: JobMarketplaceWithModelsUpgradeable now enforces model activationat model-aware session creation by requiring `nodeRegistry.modelRegistry()`.`isModelApproved(modelId)` before `nodeRegistry.nodeSupportsModel(host, modelId)`. `require(nodeRegistry.modelRegistry()`.`isModelApproved(modelId)`, "Model not app roved"); 55 The control is present in createSessionJobForModel and createSessionJobForModelWithToken, and the same enforcement is applied inthe delegate flow createSessionForModelAsDelegate. 56

### 修補方式（實際）
Fixed in a49ef12: JobMarketplaceWithModelsUpgradeable now enforces model activationat model-aware session creation by requiring `nodeRegistry.modelRegistry()`.`isModelApproved(modelId)` before `nodeRegistry.nodeSupportsModel(host, modelId)`. `require(nodeRegistry.modelRegistry()`.`isModelApproved(modelId)`, "Model not app roved"); 55 The control is present in createSessionJobForModel and createSessionJobForModelWithToken, and the same enforcement is applied inthe delegate flow createSessionForModelAsDelegate. 56

## Cyfrin Fixed Issues (Merged)
- Count: `35`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] In `DelegatorFactory` new entity can be created for a blacklisted implementation
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The current implementation of `DelegatorFactory::create` fails to verify whether the specified implementation type has been explicitly blacklisted. This creates a security and consistency risk where blacklisted contract types can still be deployed, potentially bypassing governance or security restrictions.

**Impact:** The lack of a blacklist check in the create function allows the creation of contracts based on implementation types that may have been deemed unsafe, deprecated, or otherwise restricted.

**Proof of Concept:** Create a new test class `DelegatorFactoryTest.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright 2024 ADDPHO

pragma solidity 0.8.25;

import {Test, console2} from "forge-std/Test.sol";
import {DelegatorFactory} from "../src/contracts/DelegatorFactory.sol";
import {IDelegatorFactory} from "../src/interfaces/IDelegatorFactory.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {IEntity} from "../../src/interfaces/common/IEntity.sol";
import {ERC165} from "@openzeppelin/contracts/utils/introspection/ERC165.sol";
import "@openzeppelin/contracts/utils/introspection/IERC165.sol";

contract DelegatorFactoryTest is Test {
    address owner;
    address operator1;
    address operator2;

    DelegatorFactory factory;
    MockEntity mockImpl;

    function setUp() public {
        owner = address(this);
        operator1 = makeAddr("operator1");
        operator2 = makeAddr("operator2");

        factory = new DelegatorFactory(owner);

        // Deploy a mock implementation that conforms to IEntity
        mockImpl = new MockEntity(address(factory), 0);

        // Whitelist the implementation
        factory.whitelist(address(mockImpl));
    }

    function testCreateBeforeBlacklist() public {
        bytes memory initData = abi.encode("test");

        address created = factory.create(0, initData);

        assertTrue(factory.isEntity(created), "Entity should be created and registered");
    }

    function testCreateFailsAfterBlacklist() public {
        bytes memory initData = abi.encode("test");

        factory.blacklist(0);

        factory.create(0, initData); //@note no revert although blacklisted
    }
}

contract MockEntity is IEntity, ERC165 {
    address public immutable FACTORY;
    uint64 public immutable TYPE;

    string public data;

    constructor(address factory_, uint64 type_) {
        FACTORY = factory_;
        TYPE = type_;
    }

    function initialize(
        bytes calldata initData
    ) external {
        data = abi.decode(initData, (string));
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override(ERC165, IERC165) returns (bool) {
        return interfaceId == type(IEntity).interfaceId || super.supportsInterface(interfaceId);
    }
}

```

**Recommended Mitigation:** Consider adding the following check to the `DelagatorFactory::create`

```diff solidity
function create(uint64 type_, bytes calldata data) external returns (address entity_) {
++    if (blacklisted[type_]) {
++       revert DelagatorFactory__TypeBlacklisted();
++    }
        entity_ = implementation(type_).cloneDeterministic(keccak256(abi.encode(totalEntities(), type_, data)));

        _addDelegatorEntity(entity_);

        IEntity(entity_).initialize(data);
    }
```

**Suzaku:**
Fixed in commit [292d5b7](https://github.com/suzaku-network/suzaku-core/pull/155/commits/292d5b71ac3a377351d66f239405c4d38af53830).

**Cyfrin:** Verified.

## [M-2] Missing mode field validation in walletclient allows handler selection via untrusted input
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The `WalletClient.connect()` method in `wallet-client/src/client.ts` uses the dApp-provided `sessionRequest.mode` field to select between `TrustedConnectionHandler` (no OTP) and `UntrustedConnectionHandler` (OTP required) without any input validation:

```js
const handler: IConnectionHandler = request.mode === "trusted"
  ? new TrustedConnectionHandler(context)
  : new UntrustedConnectionHandler(context);
```

The `mode` field originates entirely from the dApp side (`dapp-client/src/client.ts`) and is embedded directly into the `SessionRequest` transmitted via QR code or deeplink. No runtime enum check, type guard, or wallet-side policy enforcement exists before handler selection.

**Impact:** In MetaMask's actual deployments, this has **no practical impact** as:
- **connect-monorepo** (`connect-multichain/src/multichain/transports/mwp/index.ts`) hard-codes `mode: 'trusted'` so the dApp can never controls this value.
- **MetaMask Mobile** (`SDKConnect/handlers/handleConnectionReady.ts`) ignores the `mode` field entirely and enforces its own OTP policy based on `connection.origin` and `lastAuthorized`.

However, any **third-party wallet** integrating the raw `WalletClient` library without implementing independent security policy would allow a malicious dApp to set `mode: 'trusted'` and skip OTP verification entirely. This is a defense-in-depth gap in the library's public API.

**Recommended Mitigation:** Add runtime validation of the `mode` field before handler selection in `WalletClient.connect()`:

```js
if (!["trusted", "untrusted"].includes(request.mode)) {
  throw new SessionError(ErrorCode.INVALID_PARAM, `Invalid connection mode: ${request.mode}`);
}
```

Ideally, the wallet should not rely on the dApp-provided `mode` at all. Consider allowing wallet integrators to override or enforce mode via a configuration option (e.g., `WalletClient({ forceUntrusted: true })`), so the security decision stays on the wallet side.

**MetaMask:** Fixed in commit [4c8bf8](https://github.com/MetaMask/mobile-wallet-protocol/commit/4c8bf8564ab1190e37f8b47769534445b88fe2d6).

**Cyfrin:** Verified.

## [M-3] Inaccurate stake calculation due to decimal mismatch across multitoken asset classes
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** Currently, when calculating the operator stake, the system iterates through all vaults associated with a specific asset class ID and sums all of the staked amounts. However, an asset class may consist of multiple token types (collaterals) that use different decimal precision (e.g., one token with 6 decimals and another with 18). Because the summation logic does not normalize these values to a common decimal base, assets with fewer decimals (e.g., USDC with 6 decimals) may effectively contribute negligible or zero value in the final stake calculation, even though significant value may be staked in that token.

1. Asset Class ID 100 is composed of:

   * Token A with 6 decimals (e.g., USDC).
   * Token B with 18 decimals (e.g., DAI).
2. A vault is created where:

   * 10,000 Token A (USDC) is staked (actual value = 10,000 \* 10⁶).
   * 10 Token B (DAI) is staked (actual value = 10 \* 10¹⁸).
3. Current stake summing logic simply adds the raw amounts across vaults.
4. Due to the difference in decimals, 10,000 Token A (USDC) may be treated as “0” or an insignificant amount when compared directly to Token B’s value.
5. The resulting total stake is incorrectly calculated

```solidity
function getOperatorStake(
        address operator,
        uint48 epoch,
        uint96 assetClassId
    ) public view returns (uint256 stake) {
        if (totalStakeCached[epoch][assetClassId]) {
            uint256 cachedStake = operatorStakeCache[epoch][assetClassId][operator];

            return cachedStake;
        }

        uint48 epochStartTs = getEpochStartTs(epoch);

        uint256 totalVaults = vaultManager.getVaultCount();

        for (uint256 i; i < totalVaults; ++i) {
            (address vault, uint48 enabledTime, uint48 disabledTime) = vaultManager.getVaultAtWithTimes(i);

            // Skip if vault not active in the target epoch
            if (!_wasActiveAt(enabledTime, disabledTime, epochStartTs)) {
                continue;
            }

            // Skip if vault asset not in AssetClassID
            if (vaultManager.getVaultAssetClass(vault) != assetClassId) {
                continue;
            }

            uint256 vaultStake = BaseDelegator(IVaultTokenized(vault).delegator()).stakeAt(
                L1_VALIDATOR_MANAGER, assetClassId, operator, epochStartTs, new bytes(0)
            );

            stake += vaultStake;
        }
```

**Impact:**
- Underreported Stake: Tokens with fewer decimals are underrepresented or ignored entirely in stake calculations.

**Proof of Concept:** Add this test to `AvalancheL1MiddlewareTest.t.sol` :

```solidity
function test_operatorStakeWithoutNormalization() public {
        uint48 epoch = 1;
        uint256 uptime = 4 hours;

        // Deploy tokens with different decimals
        ERC20WithDecimals tokenA = new ERC20WithDecimals("TokenA", "TKA", 6);  // e.g., USDC
        ERC20WithDecimals tokenB = new ERC20WithDecimals("TokenB", "TKB", 18); // e.g., DAI

        // Deploy vaults and associate with asset class 1
        vm.startPrank(validatorManagerAddress);
        address vaultAddress1 = vaultFactory.create(
            1,
            bob,
            abi.encode(
                IVaultTokenized.InitParams({
                    collateral: address(tokenA),
                    burner: address(0xdEaD),
                    epochDuration: 8 hours,
                    depositWhitelist: false,
                    isDepositLimit: false,
                    depositLimit: 0,
                    defaultAdminRoleHolder: bob,
                    depositWhitelistSetRoleHolder: bob,
                    depositorWhitelistRoleHolder: bob,
                    isDepositLimitSetRoleHolder: bob,
                    depositLimitSetRoleHolder: bob,
                    name: "Test",
                    symbol: "TEST"
                })
            ),
            address(delegatorFactory),
            address(slasherFactory)
        );
        address vaultAddress2 = vaultFactory.create(
            1,
            bob,
            abi.encode(
                IVaultTokenized.InitParams({
                    collateral: address(tokenB),
                    burner: address(0xdEaD),
                    epochDuration: 8 hours,
                    depositWhitelist: false,
                    isDepositLimit: false,
                    depositLimit: 0,
                    defaultAdminRoleHolder: bob,
                    depositWhitelistSetRoleHolder: bob,
                    depositorWhitelistRoleHolder: bob,
                    isDepositLimitSetRoleHolder: bob,
                    depositLimitSetRoleHolder: bob,
                    name: "Test",
                    symbol: "TEST"
                })
            ),
            address(delegatorFactory),
            address(slasherFactory)
        );
        VaultTokenized vaultTokenA = VaultTokenized(vaultAddress1);
        VaultTokenized vaultTokenB = VaultTokenized(vaultAddress2);
        vm.startPrank(validatorManagerAddress);
        middleware.addAssetClass(2, 0, 100, address(tokenA));
        middleware.activateSecondaryAssetClass(2);
        middleware.addAssetToClass(2, address(tokenB));
        vm.stopPrank();

        address[] memory l1LimitSetRoleHolders = new address[](1);
        l1LimitSetRoleHolders[0] = bob;
        address[] memory operatorL1SharesSetRoleHolders = new address[](1);
        operatorL1SharesSetRoleHolders[0] = bob;

        address delegatorAddress2 = delegatorFactory.create(
            0,
            abi.encode(
                address(vaultTokenA),
                abi.encode(
                    IL1RestakeDelegator.InitParams({
                        baseParams: IBaseDelegator.BaseParams({
                            defaultAdminRoleHolder: bob,
                            hook: address(0),
                            hookSetRoleHolder: bob
                        }),
                        l1LimitSetRoleHolders: l1LimitSetRoleHolders,
                        operatorL1SharesSetRoleHolders: operatorL1SharesSetRoleHolders
                    })
                )
            )
        );

        L1RestakeDelegator delegator2 = L1RestakeDelegator(delegatorAddress2);

        address delegatorAddress3 = delegatorFactory.create(
            0,
            abi.encode(
                address(vaultTokenB),
                abi.encode(
                    IL1RestakeDelegator.InitParams({
                        baseParams: IBaseDelegator.BaseParams({
                            defaultAdminRoleHolder: bob,
                            hook: address(0),
                            hookSetRoleHolder: bob
                        }),
                        l1LimitSetRoleHolders: l1LimitSetRoleHolders,
                        operatorL1SharesSetRoleHolders: operatorL1SharesSetRoleHolders
                    })
                )
            )
        );
        L1RestakeDelegator delegator3 = L1RestakeDelegator(delegatorAddress3);

        vm.prank(bob);
        vaultTokenA.setDelegator(delegatorAddress2);

        // Set the delegator in vault3
        vm.prank(bob);
        vaultTokenB.setDelegator(delegatorAddress3);

        _setOperatorL1Shares(bob, validatorManagerAddress, 2, alice, 100, delegator2);
        _setOperatorL1Shares(bob, validatorManagerAddress, 2, alice, 100, delegator3);

        vm.startPrank(validatorManagerAddress);
        vaultManager.registerVault(address(vaultTokenA), 2, 3000 ether);
        vaultManager.registerVault(address(vaultTokenB), 2, 3000 ether);
        vm.stopPrank();

        _optInOperatorVault(alice, address(vaultTokenA));
        _optInOperatorVault(alice, address(vaultTokenB));
        //_optInOperatorL1(alice, validatorManagerAddress);

        _setL1Limit(bob, validatorManagerAddress, 2, 10000 * 10**6, delegator2);
        _setL1Limit(bob, validatorManagerAddress, 2, 10 * 10**18, delegator3);

        // Define stakes without normalization
        uint256 stakeA = 10000 * 10**6; // 10,000 TokenA (6 decimals)
        uint256 stakeB = 10 * 10**18;   // 10 TokenB (18 decimals)

        tokenA.transfer(staker, stakeA);
        vm.startPrank(staker);
        tokenA.approve(address(vaultTokenA), stakeA);
        vaultTokenA.deposit(staker, stakeA);
        vm.stopPrank();

        tokenB.transfer(staker, stakeB);
        vm.startPrank(staker);
        tokenB.approve(address(vaultTokenB), stakeB);
        vaultTokenB.deposit(staker, stakeB);
        vm.stopPrank();

        vm.warp((epoch + 3) * middleware.EPOCH_DURATION());


        assertNotEq(middleware.getOperatorStake(alice, 2, 2), stakeA + stakeB);

    }
```

**Recommended Mitigation:** Before summing, normalize all token amounts to a common unit (e.g., 18 decimals).

```diff
 function getOperatorStake(
     address operator,
     uint48 epoch,
     uint96 assetClassId
 ) public view returns (uint256 stake) {
     if (totalStakeCached[epoch][assetClassId]) {
         return operatorStakeCache[epoch][assetClassId][operator];
     }

     uint48 epochStartTs = getEpochStartTs(epoch);
     uint256 totalVaults = vaultManager.getVaultCount();

     for (uint256 i; i < totalVaults; ++i) {
         (address vault, uint48 enabledTime, uint48 disabledTime) = vaultManager.getVaultAtWithTimes(i);

         // Skip if vault not active in the target epoch
         if (!_wasActiveAt(enabledTime, disabledTime, epochStartTs)) {
             continue;
         }

         // Skip if vault asset not in AssetClassID
         if (vaultManager.getVaultAssetClass(vault) != assetClassId) {
             continue;
         }

-        uint256 vaultStake = BaseDelegator(IVaultTokenized(vault).delegator()).stakeAt(
+        uint256 rawStake = BaseDelegator(IVaultTokenized(vault).delegator()).stakeAt(
             L1_VALIDATOR_MANAGER, assetClassId, operator, epochStartTs, new bytes(0)
         );

+        // Normalize stake to 18 decimals
+        address token = IVaultTokenized(vault).underlyingToken();
+        uint8 tokenDecimals = IERC20Metadata(token).decimals();
+
+        if (tokenDecimals < 18) {
+            rawStake *= 10 ** (18 - tokenDecimals);
+        } else if (tokenDecimals > 18) {
+            rawStake /= 10 ** (tokenDecimals - 18);
+        }

-        stake += vaultStake;
+        stake += rawStake;
     }
 }

```

**Suzaku:**
Fixed in commit [ccd5e7d](https://github.com/suzaku-network/suzaku-core/pull/155/commits/ccd5e7dd376933fd3f31acf31602ff38ee93654a).

**Cyfrin:** Verified.

## [M-4] `MintType` is almost never enforced
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The contract has an enumeration `MintType` which defines several types of mints:
```solidity
enum MintType {
    OpenMint,
    Whitelist,
    Claim,
    Burn
}
```

But there are never any checks for these mint types, for example:
* there is no check for `MintType.Whitelist` and no corresponding whitelist enforcement
* the `claim` function doesn't enforce input `data.mintType == MintType.Claim`
* similarly `burnAndMint` doesn't enforce input `data.mintType == MintType.Burn`

The only place input `data.mintType` is used is in `_validateSignature` to validate that the input parameter matches what was signed, but there is no other validation that the correct mint types are being used for the correct operations.

**CryptoArt:**
Fixed in commit [deaf964](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/deaf96420b3176be09c1522ea8c79a211f77ef82).

**Cyfrin:** Verified.

## [M-5] Inconsistent storage location namespace root in `YieldManagerStorageLayout`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** In `YieldManagerStorageLayout` `YieldManagerStorage` is annotated with `@custom:storage-location erc7201:linea.storage.YieldManager`, but the hardcoded namespace root used by the contract is documented and chosen for a different identifier, `"linea.storage.YieldManagerStorage"`. Per ERC‑7201, the namespace id used in the annotation must be the exact same id used to derive the storage root; otherwise the annotation does not describe the actual storage schema in use.

**Impact:** Off-chain tooling that reads the annotation and computes `erc7201("linea.storage.YieldManager")` will inspect the wrong storage root, leading to incorrect decoding, analysis, or monitoring of state. Standards non-compliance can cause confusion during audits and upgrades, and increases the risk of accidental collisions or mismatches if another component follows the annotated id literally.

**Recommended Mitigation:** Choose one of the following and keep the annotation, the comment, and the constant perfectly in sync:

1. Option A (minimal change): Update the annotation to match the slot’s documented/computed id.

 - Change to: `@custom:storage-location erc7201:linea.storage.YieldManagerStorage`

2. Option B (preserve current annotation): Recompute the constant and its doc comment using the ERC‑7201 formula for `"linea.storage.YieldManager"`, and update `YieldManagerStorageLocation` to that value.

- Formula: `keccak256(abi.encode(uint256(keccak256(bytes("linea.storage.YieldManager"))) - 1)) & ~bytes32(uint256(0xff))`

- Keep the comment and the hex value aligned with this id.

**Linea:** Fixed in commit [f3e11c0](https://github.com/Consensys/linea-monorepo/commit/f3e11c0dc8a887eb3a377d2ec14d7366809fbeb8).

**Cyfrin:** Verified.

## [M-6] `DividendManager::distributePayout` records a new payout record increasing the current payout index for zero `payoutAmount`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `DividendManager::distributePayout` records a new payout record increasing the current payout index for zero `payoutAmount`.

**Proof of Concept:**
```solidity
function test_distributePayout_ZeroPayout() external {
    // setup one user
    address user = users[0];
    uint256 userRemoraTokens = 1;

    // whitelist user
    remoraTokenProxy.addToWhitelist(user);
    assertTrue(remoraTokenProxy.isWhitelisted(user));

    // mint user their tokens
    remoraTokenProxy.mint(user, userRemoraTokens);
    assertEq(remoraTokenProxy.balanceOf(user), userRemoraTokens);

    // allowlist user
    allowListProxy.allowUser(user, true, true, false);
    assertTrue(allowListProxy.allowed(user));

    // zero payout distribution - should revert here
    remoraTokenProxy.distributePayout(0);
    // didn't revert but increased current payout index
    assertEq(remoraTokenProxy.getCurrentPayoutIndex(), 1);
}
```

**Recommended Mitigation:** `DividendManager::distributePayout` should revert when `payoutAmount == 0`.

**Remora:** Fixed in commit [c2002fb](https://github.com/remora-projects/remora-smart-contracts/commit/c2002fb751c22d6f4009eaa6f3dd651b5b4ca474).

**Cyfrin:** Verified.

## [M-7] `RemoraToken` transfers are bricked when `from` is not whitelisted, has sufficient tokens to transfer but no tokens locked
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `RemoraToken::adminTransferFrom`, `transfer` and `transferFrom` always check if `from` is on the whitelist and if not, call `_unlockTokens`:
```solidity
    bool fromWL = whitelist[from];
    bool toWL = whitelist[to];

    if (!fromWL) _unlockTokens(from, value, false);
    if (!toWL) _lockTokens(to, value);
```

But a scenario can occur where:
1) `from` has nothing to unlock
2) `from` has tokens to fulfill the transfer

In this case transfer would be bricked. Another scenario to consider is when:

1) `from` has 10 tokens
2) only 5 of those tokens are locked
3) `from` is attempting to transfer 10 tokens

In this case the call to `_unlockTokens` should have `amount = 5` since `from` only needs to unlock 5 tokens in order to send the 10 total.

But with the current code the call to `_unlockTokens` will have `amount = 10` (since it just uses the transfer amount) which makes no sense and causes a revert.

**Impact:** `RemoraToken` transfers are bricked when `from` is not whitelisted, has sufficient tokens to transfer but no tokens locked since the call to `_unlockTokens` will revert.

**Proof Of Concept:**
```solidity
function test_transferBricked_fromNotWhitelisted_ButHasTokensToTransfer() external {
    address from = users[0];
    address to = users[1];
    uint256 amountToTransfer = 1;

    // fund `from` with remora tokens
    remoraTokenProxy.mint(from, amountToTransfer);
    assertEq(remoraTokenProxy.balanceOf(from), amountToTransfer);

    // remove `from` from whitelist
    remoraTokenProxy.removeFromWhitelist(from);

    // set lock time
    remoraTokenProxy.setLockUpTime(3600);

    vm.expectRevert(); // reverts with InsufficientTokensUnlockable
    vm.prank(from);
    remoraTokenProxy.transfer(to, amountToTransfer);
}
```

This also totally bricks transfers for users who received tokens when they were whitelisted, then are removed from the whitelist:
```solidity
    function test_transferBricked_whitelistedHolderIsRemovedFromWhitelist() external {
        address from = users[0];
        address to = users[1];
        uint256 amountToTransfer = 10;

        _whitelistAndMintTokensToUser(from, amountToTransfer);

        // set lock time
        remoraTokenProxy.setLockUpTime(3600);

        // remove `from` from whitelist
        remoraTokenProxy.removeFromWhitelist(from);

        // fund `from` with remora tokens once it is not whitelisted
        remoraTokenProxy.mint(from, amountToTransfer);

        // 10 when was whitelisted and 10 when from was not whitelisted
        assertEq(remoraTokenProxy.balanceOf(from), amountToTransfer * 2);

        // forward beyond the lockup time to demonstrate the removed whitelisted holder can't do transfers
        vm.warp(3600 + 1);

        // reverts because from has only 10 tokens locked
        vm.expectRevert(); // reverts with InsufficientTokensUnlockable
        vm.prank(from);
        remoraTokenProxy.transfer(to, 11);

        // verify from can only transfer the 10 tokens that he received after he was removed from whitelist
        vm.prank(from);
        remoraTokenProxy.transfer(to, 10);
    }
```

**Recommended Mitigation:** A simple and elegant solution may be:
1) check `from` balance; if smaller than `amount` required for transfer revert
2) in transfer functions if the user is not whitelisted, calculate their `uint256 unlockedBalanceToSend = balance - getTokensLocked(sender);` then if `unlockedBalanceToSend < amount` call `_unlockTokens(sender, value - unlockedBalanceToSend..)`;

This solution only attempts to unlock the exact amount needed to fulfill a transfer, and doesn't attempt unlock if nothing to unlock or not required as the user has enough unlocked tokens to fulfill the transfer.

**Remora:** Fixed in commits [67c5e8e](https://github.com/remora-projects/remora-smart-contracts/commit/67c5e8e3262d45f38c18d295a0983dd51f5fd612), [5db7f11](https://github.com/remora-projects/remora-smart-contracts/commit/5db7f11427f6e767a6042c443d552ee9c024494b).

**Cyfrin:** Verified.

## [M-8] Buyers can pledge for tokens without having signed all documents that are required to be signed
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** When buyers pledge() during the pledgeRound, it is verified that they [have signed all the documents](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/PledgeManager.sol#L316) that are required to be signed.
If at least one document is not signed, instead of reverting the tx, the execution will [verify a signature on behalf of the signer](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/PledgeManager.sol#L317-L322), and, if this signature is legit, the execution continues.

```solidity
    function _verifyDocumentSignature(
        PledgeData calldata data,
        address signer
    ) internal {
        (bool res, ) = IRemoraRWAToken(propertyToken).hasSignedDocs(signer);
        if (!res)
            IRemoraRWAToken(propertyToken).verifySignature(
                signer,
                data.docHash,
                data.signature
            );
    }
```

**The problem is** that this implementation allows buyers to bypass the requirement to have signed all the documents by signing only one. For example:
There are 3 documents that need to be signed, and the user has not signed any of them. The user calls pledge() and provides the signature's data to sign 1 document. Here is what will happen:

[PropertyToken::hasSignedDocs() ](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DocumentManager.sol#L114-L127) will return false because the user has not signed any of the 3 documents
```solidity
    function hasSignedDocs(address signer) public view returns (bool, bytes32) {
        ...

        for (uint256 i = 0; i < numDocs; ++i) {
            bytes32 docHash = $._docHashes[i];
//@audit => If one document that needs signature is not signed, returns false
            if (
                $._documents[docHash].needSignature &&
                $._signatureRecords[signer][docHash] == 0
            ) return (false, docHash);
        }

//@audit => returns true only if all documents that requires signature are signed
        return (true, 0x0);
    }
```

[PropertyToken::verifySignature()](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DocumentManager.sol#L148-L184) won't revert because it will sign one of the 3 documents
```solidity
    function verifySignature(
        address signer,
        bytes32 docHash,
        bytes memory signature
    ) external returns (bool result) {
        ...
        if (signer.code.length == 0) {
            //signer is EOA
            (address returnedSigner, , ) = ECDSA.tryRecover(digest, signature);
            result = returnedSigner == signer;
        } else {
            //signer is SCA
            (bool success, bytes memory ret) = signer.staticcall(
                ...
            );
            result = (success && ret.length == 32 && bytes4(ret) == MAGICVALUE);
        }

        if (!result) revert InvalidSignature();
        if ($._signatureRecords[signer][docHash] == 0) {
           ...
        }
//@audit => if the verification of the provided signature succeeds, execution continues
    }
```

**The problem is** that the execution will continue even though the user has only signed 1 of the 3 documents that have to be signed because (as previously explained), [_verifyDocumentSignature()](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/PledgeManager.sol#L312-L323) will be bypassed to only enforce one signature, and, when transferring from the holderWallet to the signer, the [`checkTC` is set as false](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/PledgeManager.sol#L207).

[PledgeManager::pledge()](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/PledgeManager.sol#L167-L221)
```solidity
    function pledge(PledgeData calldata data) external nonReentrant {
        ...

        _verifyDocumentSignature(data, signer);

       ...

//@audit => checkTC is set as false
        //this address should be whitelisted in property token
        IRemoraRWAToken(propertyToken).adminTransferFrom(
            holderWallet,
            signer,
            numTokens,
            false,  // <====> checkTC //
            true
        );
       ...
    }
```

[RemoraToken::adminTransferFrom()](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/RemoraToken.sol#L228-L252)
```solidity
    function adminTransferFrom(
        address from,
        address to,
        uint256 value,
        bool checkTC,
        bool enforceLock
    ) external restricted returns (bool) {
       ...
//@audit => checkTC as false effectively bypass the verification of TC to be signed
        (bool res, ) = hasSignedDocs(to);
        if (checkTC && !res) revert TermsAndConditionsNotSigned(to);

       ...
    }

```


**Impact:** Buyers can purchase tokens even though they have not signed all the documents that have to be signed

**Recommended Mitigation:** Revert the execution if the call to `PropertyToken.hasSignedDocs()` returns false.

```diff
function _verifyDocumentSignature(
        PledgeData calldata data,
        address signer
    ) internal {

        (bool res, ) = IRemoraRWAToken(propertyToken).hasSignedDocs(signer);

-      if (!res)
-          IRemoraRWAToken(propertyToken).verifySignature(
-             signer,
-             data.docHash,
-              data.signature
-         );

+     if (!res) revert NotAllDocumentsAreSigned();

    }
```

**Remora:** Fixed in commit [5510920](https://github.com/remora-projects/remora-smart-contracts/commit/55109201b0b592abb94a3c73a5f45c9c24b3d440#diff-7ce9b56302de46e809d6a2bc534817c3a4ea314d0e16d299fae932f057245486L193-R191).

**Cyfrin:** Verified.

## [M-9] In `RemoraToken::transfer`, `transferFrom` and `_exchangeAllowed` perform all checks for each user together in order to prevent unnecessary work
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** In `RemoraToken::transfer`, `transferFrom` and `_exchangeAllowed` perform all checks for each user together in order to prevent unnecessary work.

`transfer`:
```solidity
        bool fromWL = _whitelist[sender];
        if (!fromWL) _unlockTokens(sender, value, false);

        bool toWL = _whitelist[to];
        if (!toWL) _lockTokens(to, value);
```

`transferFrom`:
```solidity
        bool fromWL = _whitelist[from];
        if (!fromWL) _unlockTokens(from, value, false);

        bool toWL = _whitelist[to];
        if (!toWL) _lockTokens(to, value);
```

`_exchangeAllowed`:
```solidity
        (bool resFrom, ) = hasSignedDocs(from);
        if (!resFrom && !_whitelist[from]) revert TermsAndConditionsNotSigned(from);

        (bool resTo, ) = hasSignedDocs(to);
        if (!resTo && !_whitelist[to]) revert TermsAndConditionsNotSigned(to);
```

**Remora:** Fixed in commit [59cf2eb](https://github.com/remora-projects/remora-smart-contracts/commit/59cf2eb26742de48988623fdd029d17b2993ba2f).

**Cyfrin:** Verified.

## [M-10] Remove `decimals` from initial `RemoraToken` mint
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `RemoraToken` overrides the `decimals` function to return 0 as its tokens are non-fractional:
```solidity
    /**
     * @notice Defines the number of decimal places for the token.
     * RWA tokens are non-fractional and operate in whole units only.
     * @return The number of decimals (always `0`).
     */
    function decimals() public pure override returns (uint8) {
        return 0;
    }
```

So remove the call to `decimals` inside `RemoraToken::initialize` since `10 ** decimals()` will always evaluate to 1:
```diff
    function initialize(
        address tokenOwner,
        address initialAuthority,
        address stablecoin,
        address wallet,
        address _allowList,
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) public initializer {
        // does this order matter?, open zeppelin upgrades giving errors here
        __ERC20_init(_name, _symbol);
        __ERC20Permit_init(_name);
        __Pausable_init();
        __RemoraBurnable_init();
        __RemoraLockUp_init(0); //start with 0 lock up time
        __RemoraDocuments_init(_name, "1");
        __RemoraHolderManagement_init(
            initialAuthority,
            stablecoin,
            wallet,
            0 //starts at zero, will need to update it later
        );
        __UUPSUpgradeable_init();

        allowlist = _allowList;
        _whitelist[tokenOwner] = true; //whitelist owner to be able to send tokens freely
-       _mint(tokenOwner, _initialSupply * 10 ** decimals());
+       _mint(tokenOwner, _initialSupply);
    }
```

**Remora:** Fixed in commit [462d2de](https://github.com/remora-projects/remora-smart-contracts/commit/462d2def8f09453435e4df433228cfaa565d2e37).

**Cyfrin:** Verified.

## [M-11] Same user can join the same game multiple times increasing their chance of winning by preventing other players from participating
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SessionManager::joinGame` doesn't validate whether the user joining has already joined. As long as the game is still in the `Created` state, the same user can join multiple times each time incrementing `numContestants`.

**Impact:** The same user can take all or most of the available player positions massively increasing their chances of winning since less players are able to compete against them. When `MajorityChoicePrompt` is used this could be especially powerful.

Games have an optional `verificationRequired` "whitelist" feature to prevent the same player using multiple addresses from taking over a game, but a player can abuse this bug to bypasses the `verificationRequired` option since the same whitelisted address can join the same game multiple times preventing other players from joining.

**Recommended Mitigation:** `SessionManager::joinGame` should revert if `contestants[_gameId][msg.sender] == true`. Consider wrapping this into a modifier `onlyNotJoinedGame` and putting that modifier onto `joinGame`.

**Majority Games:**
Fixed in commit [2bba52d](https://github.com/Engage-Protocol/engage-protocol/commit/2bba52d8a8dfecf45566b2d0b1790161102becd2).

**Cyfrin:** Verified.

## [M-12] `ComplianceServiceRegulated::getComplianceTransferableTokens` should call `IDSLockManager::getTransferableTokensForInvestor`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceRegulated::getComplianceTransferableTokens` already loads the registry and fetches the investor id, so therefore it should call `IDSLockManager::getTransferableTokensForInvestor` instead of `getTransferableTokens` to save again loading the registry and again fetching the investor id:
```diff
    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        uint64 _lockTime
    ) public view override returns (uint256) {
        require(_time != 0, "Time must be greater than zero");
        string memory investor = getRegistryService().getInvestor(_who);

-       uint256 balanceOfInvestor = getLockManager().getTransferableTokens(_who, _time);
+       uint256 balanceOfInvestor = getLockManager().getTransferableTokensForInvestor(investor, _time);

```

**Securitize:** Fixed in commit [382eaae](https://github.com/securitize-io/dstoken/commit/382eaae50dbf5a9a33ce343268e6dc9d257428c2).

**Cyfrin:** Verified.

## [M-13] `ComplianceServiceRegulated::preIssuanceCheck` allows issuance to non-accredited investors when `forceAccredited` or `forceAccreditedUS` is set, and allows issuance below regional minimum thresholds, violating compliance requirements
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceRegulated::completeTransferCheck` has several checks that `preIssuanceCheck` is missing:

1) Force Accredited

`completeTransferCheck` verifies whether force accredited is enabled and if so only allow transfers to accredited investors:
```solidity
bool isAccreditedTo = isAccredited(_services, _args.to);
if (
    IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceAccredited() && !isAccreditedTo
) {
    return (61, ONLY_ACCREDITED);
}

} else if (toRegion == US) {
    if (
        IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceAccreditedUS() &&
        !isAccreditedTo
    ) {
        return (62, ONLY_US_ACCREDITED);
    }
```

But `preIssuanceCheck` doesn't enforce this, so it could allow issuance to unaccredited investors even when `ForceAccredited` or `ForceAccreditedUS` is enabled.

2) Regional Minimal Token Holdings

`completeTransferCheck` verifies regional minimum token holdings eg:
```solidity
if (toInvestorBalance + _value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinUSTokens()) {
    return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
}
```
But preIssuanceCheck only verifies the generic minimum holdings:
```solidity
        if (
            !walletManager.isPlatformWallet(_to) &&
        balanceOfInvestorTo + _value < complianceConfigurationService.getMinimumHoldingsPerInvestor()
        ) {
            return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
        }
```

Hence `preIssuanceCheck` could result in users being issued an amount of tokens that violates their regional minimum token holdings.

**Impact:** `ComplianceServiceRegulated::preIssuanceCheck` allows issuance to non-accredited investors when `forceAccredited` or `forceAccreditedUS` is set, and allows issuance below regional minimum thresholds, violating compliance requirements

**Recommended Mitigation:** Enforce the above checks in `ComplianceServiceRegulated::preIssuanceCheck`.

**Securitize:** Fixed in commits [4991826](https://github.com/securitize-io/dstoken/commit/499182670e4b05c0a8f5eefc639403e5dbaf15bd), [0656ccd](https://github.com/securitize-io/dstoken/commit/0656ccd7e48af296770bcf780a47c3a14fcc9eba).

**Cyfrin:** Verified.

## [M-14] `ComplianceServiceRegulated` and its parent `ComplianceServiceWhitelisted` uses a chain of `initializer` modifiers when calling the `initialize`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceRegulated` is the child contract inheriting from `ComplianceServiceWhitelisted`.
The `ComplianceServiceRegulated::initialize()` uses the `initializer modifier` as well as the `ComplianceServiceWhitelisted:initialize()`.

```solidity
contract ComplianceServiceRegulated is ComplianceServiceWhitelisted {
    function initialize() public virtual override onlyProxy initializer {
        super.initialize();
    }
}

contract ComplianceServiceWhitelisted is ComplianceService {
    function initialize() public virtual override onlyProxy initializer {
        ComplianceService.initialize();
    }
}
```

According to [OpenZeppelin's documentation](https://docs.openzeppelin.com/contracts/4.x/api/proxy#Initializable-initializer--) and best practices, the initializer modifier should only be used in the final initialization function of an inheritance chain, while initialization functions of parent contracts should use the [onlyInitializing](https://docs.openzeppelin.com/contracts/4.x/api/proxy#Initializable-onlyInitializing--) modifier. This ensures proper initialization when using inheritance.


**Recommended Mitigation:** * change `ComplianceServiceWhitelisted` to have this:
```solidity
contract ComplianceServiceWhitelisted is ComplianceService {

    function initialize() public virtual override onlyProxy initializer {
        _initialize();
    }

    function _initialize() internal onlyInitializing {
        ComplianceService.initialize();
    }
```

* change `ComplianceServiceRegulated` to have this:
```solidity
contract ComplianceServiceRegulated is ComplianceServiceWhitelisted {

    function initialize() public virtual override onlyProxy initializer {
        _initialize();
    }
```

**Securitize:** Fixed in commit [b24ecd5](https://github.com/securitize-io/dstoken/commit/b24ecd57bc82d0fd473d9de1317046300faab984).

**Cyfrin:** Verified.

## [M-15] Asymmetry enforcement between `TokenIssuer::registerInvestor`, `WalletRegistrar::registerWallet` and `SecuritizeSwap::_registerNewInvestor`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** In `TokenIssuer::registerInvestor`, if the user isn't already an investor they get registered and must have 3 specific attributes set:
```solidity
if (!getRegistryService().isInvestor(_id)) {
    getRegistryService().registerInvestor(_id, _collisionHash);
    getRegistryService().setCountry(_id, _country);

    if (_attributeValues.length > 0) {
        require(_attributeValues.length == 3, "Wrong length of parameters");
        getRegistryService().setAttribute(_id, KYC_APPROVED, _attributeValues[0], _attributeExpirations[0], "");
        getRegistryService().setAttribute(_id, ACCREDITED, _attributeValues[1], _attributeExpirations[1], "");
        getRegistryService().setAttribute(_id, QUALIFIED, _attributeValues[2], _attributeExpirations[2], "");
    }
```

But in `WalletRegistrar::registerWallet` and `SecuritizeSwap::_registerNewInvestor` if the user isn't already an investor, they get registered but the same attribute logic is not there. Instead it is more generic appearing to over-write anything that exists and not enforcing existence of KYC_APPROVED, ACCREDITED or QUALIFIED attributes:
```solidity
if (!registryService.isInvestor(_id)) {
    registryService.registerInvestor(_id, _collisionHash);
    registryService.setCountry(_id, _country);
}

for (uint256 i = 0; i < _wallets.length; i++) {
    if (registryService.isWallet(_wallets[i])) {
        require(CommonUtils.isEqualString(registryService.getInvestor(_wallets[i]), _id), "Wallet belongs to a different investor");
    } else {
        registryService.addWallet(_wallets[i], _id);
    }
}

for (uint256 i = 0; i < _attributeIds.length; i++) {
    registryService.setAttribute(_id, _attributeIds[i], _attributeValues[i], _attributeExpirations[i], "");
}
```

**Impact:** Going through `WalletRegistrar::registerWallet` or `SecuritizeSwap::_registerNewInvestor` an investor can be registered without the required attributes.

**Recommended Mitigation:** Harmonize the investor registration process to remove duplicated code and enforce the same requirements.

**Securitize:** Fixed in commit [72e54d2](https://github.com/securitize-io/dstoken/commit/72e54d2863f87cba2eda1535a4fc3f8902839ddc).

**Cyfrin:** Verified.

## [M-16] Changing investor country to the same country inflates investor count erroneously triggering max investor errors
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Changing investor country to the same country inflates investor count.

**Impact:** Inflating the investor count will erroneously trigger `MAX_INVESTORS_IN_CATEGORY` error in `ComplianceServiceRegulated::completeTransferCheck`. This does not require any error on the admin's part since the admin can call `RegistryService::updateInvestor` where the country remains the same but other investor properties are being changed, and this ends up calling `ComplianceServiceRegulated::adjustInvestorCountsAfterCountryChange` and inflating the investor count.

**Proof of Concept:** Add PoC to `test/compliance-service-regulated.test.ts`:
```typescript
    it('Changing to the same country inflates investor count', async function() {
      const [wallet] = await hre.ethers.getSigners();
      const { dsToken, registryService, complianceConfigurationService, complianceService } = await loadFixture(deployDSTokenRegulated);

      // Setup
      await complianceConfigurationService.setCountryCompliance(INVESTORS.Country.USA, INVESTORS.Compliance.US);

      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, wallet, registryService);
      await registryService.setAttribute(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, 2, 1, 0, ""); // Make accredited

      // Set initial country and issue tokens
      await registryService.setCountry(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, INVESTORS.Country.USA);
      await dsToken.setCap(1000);
      await dsToken.issueTokens(wallet, 100);

      // Verify initial state: 1 US investor
      expect(await complianceService.getUSInvestorsCount()).to.equal(1);

      // Change country from USA to USA
      await registryService.setCountry(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, INVESTORS.Country.USA);

      // bug: us investor count increased even though it is the same investor
      //      and their country hasn't actually changed
      expect(await complianceService.getUSInvestorsCount()).to.equal(2);
    });
```

Run with: `npx hardhat test --grep "Changing to the same country inflates investor count"`

**Recommended Mitigation:** `ComplianceServiceRegulated::adjustInvestorCountsAfterCountryChange` should revert or simply not adjust anything if `_country` and `_prevCountry` are the same.

The second option (not adjust anything) may be preferred since this can end up being called from an original call to `RegistryService::updateInvestor` where the country remains the same but other investor properties are being changed.

**Securitize:** Fixed in commit [86d4135](https://github.com/securitize-io/dstoken/commit/86d413548c5a41cc662681c1d7a67c8135d808e7) by changing `RegistryService::setCountry` (which calls `ComplianceServiceRegulated::adjustInvestorCountsAfterCountryChange` to not process if the countries are the same.

As part of another issue `ComplianceServiceRegulated::adjustInvestorCountsAfterCountryChange` was also changed to correctly decrement previous country so calling this function directly with identical countries would decrement then increment resulting in no net change to investor counts which is correct.

**Cyfrin:** Verified.

## [M-17] Don't write to the same storage slot multiple times
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** In EVM writing to storage is expensive; ideally only write to the same storage slot once. For example `ComplianceServiceRegulated::cleanupInvestorIssuances` does this:
```solidity
        uint256 time = block.timestamp;

        uint256 currentIssuancesCount = issuancesCounters[investor];
        uint256 currentIndex = 0;

        if (currentIssuancesCount == 0) {
            return;
        }

        while (currentIndex < currentIssuancesCount) {
            uint256 issuanceTimestamp = issuancesTimestamps[investor][currentIndex];

            bool isNoLongerLocked = issuanceTimestamp <= (time - lockTime);

            if (isNoLongerLocked) {
                if (currentIndex != currentIssuancesCount - 1) {
                    issuancesTimestamps[investor][currentIndex] = issuancesTimestamps[investor][currentIssuancesCount - 1];
                    issuancesValues[investor][currentIndex] = issuancesValues[investor][currentIssuancesCount - 1];
                }

                delete issuancesTimestamps[investor][currentIssuancesCount - 1];
                delete issuancesValues[investor][currentIssuancesCount - 1];

                // @audit storage write to decrement
                issuancesCounters[investor]--;
                // @audit storage read of value just written
                currentIssuancesCount = issuancesCounters[investor];
            } else {
                currentIndex++;
            }
        }
```

This is very inefficient as it results in an additional storage write and storage read during every loop iteration when `isNoLongerLocked == true`. Instead just decrement the `currentIssuancesCount` variable then write once to `issuancesCounters[investor]` after the loop:
```solidity
        while (currentIndex < currentIssuancesCount) {
            uint256 issuanceTimestamp = issuancesTimestamps[investor][currentIndex];

            bool isNoLongerLocked = issuanceTimestamp <= (time - lockTime);

            if (isNoLongerLocked) {
                if (currentIndex != currentIssuancesCount - 1) {
                    issuancesTimestamps[investor][currentIndex] = issuancesTimestamps[investor][currentIssuancesCount - 1];
                    issuancesValues[investor][currentIndex] = issuancesValues[investor][currentIssuancesCount - 1];
                }

                delete issuancesTimestamps[investor][currentIssuancesCount - 1];
                delete issuancesValues[investor][currentIssuancesCount - 1];

                currentIssuancesCount--;
            } else {
                currentIndex++;
            }
        }

        issuancesCounters[investor] = currentIssuancesCount;
```

Also there don't appear to be any unit tests around this area; I commented out the `while` loop and re-ran the test suite and no tests failed! So ideally before changing anything write some unit tests first to ensure the optimized version doesn't break anything.

**Securitize:** Fixed in commit [10ac116](https://github.com/securitize-io/dstoken/commit/10ac116901001ce804c39aecdadad16b4fc3251c) where we also added additional unit tests around the contents of the `while` loop.

**Cyfrin:** Verified.

## [M-18] Fast fail without performing unnecessary storage reads or external calls
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Fast fail without performing unnecessary storage reads or external calls. For example in `ComplianceServiceRegulated::preIssuanceCheck` the start of the function looks like this:
```solidity
function preIssuanceCheck(
    address[] calldata _services,
    address _to,
    uint256 _value
) public view returns (uint256 code, string memory reason) {
    ComplianceServiceRegulated complianceService = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
    IDSComplianceConfigurationService complianceConfigurationService = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]);
    IDSWalletManager walletManager = IDSWalletManager(_services[WALLET_MANAGER]);
    string memory toCountry = IDSRegistryService(_services[REGISTRY_SERVICE]).getCountry(IDSRegistryService(_services[REGISTRY_SERVICE]).getInvestor(_to));
    uint256 toRegion = complianceConfigurationService.getCountryCompliance(toCountry);

    if (toRegion == FORBIDDEN) {
        return (26, DESTINATION_RESTRICTED);
    }

    if (!complianceService.checkWhitelisted(_to)) {
        return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
    }
```

But if the function is going to return because `_to` is not whitelisted, then it makes no sense to spend gas performing all the interim unrelated storage reads and external calls. Instead storage reads and external calls should only be made as they are needed, eg:
```solidity
function preIssuanceCheck(
    address[] calldata _services,
    address _to,
    uint256 _value
) public view returns (uint256 code, string memory reason) {
    ComplianceServiceRegulated complianceService = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
    // fail fast if not whitelisted
    if (!complianceService.checkWhitelisted(_to)) {
        return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
    }

    IDSComplianceConfigurationService complianceConfigurationService = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]);

     // don't need this until much later in the function so no point doing it here
    // IDSWalletManager walletManager = IDSWalletManager(_services[WALLET_MANAGER]);

    // add this to improve readability as this is used multiple times
    IDSRegistryService regService = IDSRegistryService(_services[REGISTRY_SERVICE]);

    string memory toCountry = regService.getCountry(regService.getInvestor(_to));
    uint256 toRegion = complianceConfigurationService.getCountryCompliance(toCountry);

    if (toRegion == FORBIDDEN) {
        return (26, DESTINATION_RESTRICTED);
    }

    // continue remaining processing, following the principles of failing fast by only
    // perform storage reads and external calls as they are needed
```

**Securitize:** Fixed in commit [80d536e](https://github.com/securitize-io/dstoken/commit/80d536ec48d316b08226fbe53ee8a0e793ec074a).

**Cyfrin:** Verified.

## [M-19] Platform Wallet not exception for Maximum Holdings Per Investor Limits
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The `preIssuanceCheck` function in `ComplianceServiceRegulated.sol` exhibits inconsistent behavior regarding platform wallet exemptions for investor holdings limits. While platform wallets are properly exempted from the minimum holdings per investor check, they are not exempted from the maximum holdings per investor check.

```solidity
if (
    !_args.isPlatformWalletTo &&
    toInvestorBalance + _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinimumHoldingsPerInvestor()
) {
    return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
}
```
The minimum holdings check correctly includes `!_args.isPlatformWalletTo &&` to exempt platform wallets, but the maximum holdings check lacks this exemption, subjecting platform wallets to the same maximum holdings limits as regular investors.

```solidity
if (
            isMaximumHoldingsPerInvestorOk(
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMaximumHoldingsPerInvestor(),
                toInvestorBalance, _args.value)
        ) {
            return (52, AMOUNT_OF_TOKENS_ABOVE_MAX);
        }

```

**Impact:** Platform wallets may be unable to hold sufficient tokens for operational purposes due to maximum holdings limits.

**Recommended Mitigation:** Add platform wallet exemption to the maximum holdings check:
```diff
if (
+    !_args.isPlatformWalletTo &&
    isMaximumHoldingsPerInvestorOk(
        complianceConfigurationService.getMaximumHoldingsPerInvestor(),
        balanceOfInvestorTo,
        _value)
) {
    return (52, AMOUNT_OF_TOKENS_ABOVE_MAX);
}
```

**Securitize:** Fixed in commits [5b96460](https://github.com/securitize-io/dstoken/commit/5b964605cd92bdc1307f975355ec7ca402265119), [2cab0c2](https://github.com/securitize-io/dstoken/commit/2cab0c298cbeee8951c76e63947a69dc48a2698b).

**Cyfrin:** Verified.

## [M-20] Prefer explicit unsigned integer sizes
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Prefer explicit unsigned integer sizes:
```solidity
trust/TrustService.sol
218:        for (uint i = 0; i < _addresses.length; i++) {

compliance/ComplianceConfigurationService.sol
34:        for (uint i = 0; i < _countries.length; i++) {

compliance/WalletManager.sol
75:        for (uint i = 0; i < _wallets.length; i++) {
97:        for (uint i = 0; i < _wallets.length; i++) {

```

**Securitize:** Fixed in commit [26c5bb0](https://github.com/securitize-io/dstoken/commit/26c5bb05676233ca0c5caa1d9b02fd98360ad4e7).

**Cyfrin:** Verified.

## [M-21] Refactor away duplicated code between `ComplianceService::newPreTransferCheck` and `preTransferCheck`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceService::newPreTransferCheck` and `preTransferCheck` do exactly the same thing, the only difference is that:
* `newPreTransferCheck` takes `balanceFrom` and `paused` as input parameters
* `preTransferCheck` doesn't and has to look them up

So to remove code duplication, `preTransferCheck` should call `newPreTransferCheck` with the parameters it looks up eg:
```solidity
    function preTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual override returns (uint256 code, string memory reason) {
        IDSToken token = getToken();
        return newPreTransferCheck(_from, _to, _value, token.balanceOf(_from), token.isPaused());
    }
```

**Securitize:** Fixed in commit [3b1894a](https://github.com/securitize-io/dstoken/commit/3b1894af9b02fc10f41dd697122f6339db518d2f).

**Cyfrin:** Verified.

## [M-22] Remove useless function `ComplianceServiceRegulated::adjustTransferCounts`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The function `ComplianceServiceRegulated::adjustTransferCounts` is useless as it always just calls `adjustTotalInvestorsCounts` with its two parameters; remove it and simply call `adjustTotalInvestorsCounts` direct:
```diff
    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal override returns (bool) {
        if (compareInvestorBalance(_to, _value, 0)) {
-            adjustTransferCounts(_to, CommonUtils.IncDec.Increase);
+            adjustTotalInvestorsCounts(_to, CommonUtils.IncDec.Increase);
        }

        if (compareInvestorBalance(_from, _value, _value)) {
            adjustTotalInvestorsCounts(_from, CommonUtils.IncDec.Decrease);
        }

        cleanupInvestorIssuances(_from);
        cleanupInvestorIssuances(_to);
        return true;
    }

-    function adjustTransferCounts(
-        address _from,
-        CommonUtils.IncDec _increase
-    ) internal {
-        adjustTotalInvestorsCounts(_from, _increase);
-    }
```

**Securitize:** Fixed in commit [5e524cd](https://github.com/securitize-io/dstoken/commit/5e524cdb10bffc7c118ad0f19bfed315b098f795).

**Cyfrin:** Verified.

## [M-23] Transferring all the investor balance from a non-us investor to a new us investor allows to bypass the `usInvestorLimit`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceLibrary.completeTransferCheck()` runs a list of validations to prevent investor limits (regional and global) from being bypassed in case the recipient of the transfer is a new investor and the number of investors has reached the limit.

When validating the `usInvestorsLimit,` it is not validated whether the sender's region is also the US.
- This means that transferring all the investor balance of a non-US investor will bypass the `usInvestorsLimit`

Thanks to bypassing the check on `ComplianceServiceRegulated.completeTransferCheck()` (as explained in the snippet below), the `usInvestorLimit` will be increased on the `ComplianceServiceRegulated.adjustInvestorsCountsByCountry()`, which is called from the `ComplianceServiceRegulated.recordTransfer()` to increase the investor's counters because the `to` recipient is a new investor (execution flow explained in the second snippet).

```solidity
//completeTransferCheck()//
        } else if (toRegion == US) {
            ...

            uint256 usInvestorsLimit = getUSInvestorsLimit(_services);
            if (
                usInvestorsLimit != 0 &&
//@audit-info => Transferring the full balance turns out the entire conditional to evaluate to false
//@audit => A single false on any of the individual conditions causes all the conditions to evaluate to false because all of them are &&
                _args.fromInvestorBalance > _args.value &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getUSInvestorsCount() >= usInvestorsLimit &&
                isNewInvestor(toInvestorBalance)
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            ...
        }
```

```solidity
//ComplianceServiceRegulated.sol//

    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal override returns (bool) {
//@audit => The `to` recipient is a new investor, therefore, calls adjustTransferCounts to increase the counters
//@audit => `to` investor is a us investor, therefore, the usInvestorLimit will be incremented
        if (compareInvestorBalance(_to, _value, 0)) {
            adjustTransferCounts(_to, CommonUtils.IncDec.Increase);
        }

//@audit => `from` investor is not a us investor
//@audit-info => The usInvestorLimit won't be decremented here, it will be decremented the counter of the from investor's region
        if (compareInvestorBalance(_from, _value, _value)) {
            adjustTotalInvestorsCounts(_from, CommonUtils.IncDec.Decrease);
        }

        cleanupInvestorIssuances(_from);
        cleanupInvestorIssuances(_to);
        return true;
    }

```

**Impact:** *  US securities regulations requiring strict investor limits can be bypassed.
*  Note that this could lead to violations of country-specific transfer restrictions.

**Proof of Concept:** Run the next proof of concept in `dstoken-regulated.test.ts`:
```typescript
describe('US Investor Limit Bypass Vulnerability POC', function() {
    it('Should demonstrate that US investor limit can be bypassed with full transfer from any country', async function() {
      const [usInvestor1, usInvestor2, nonUsInvestor] = await hre.ethers.getSigners();
      const { dsToken, registryService, complianceConfigurationService, complianceService } = await loadFixture(deployDSTokenRegulatedWithRebasingAndEighteenDecimal);

      // Setup: US limit = 1, disable other limits
      await complianceConfigurationService.setAll(
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 150, 1, 1, 0], // No other limits, short lock period
        [false, false, false, false, false] // Disable all compliance checks initially
      );
      await complianceConfigurationService.setUSInvestorsLimit(1);// set one investor limit for us investor
      await complianceConfigurationService.setBlockFlowbackEndTime(1); // Disable flowback restriction
      await complianceConfigurationService.setCountryCompliance(INVESTORS.Country.USA, INVESTORS.Compliance.US);
      await complianceConfigurationService.setCountryCompliance(INVESTORS.Country.GERMANY, INVESTORS.Compliance.EU);

      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, usInvestor1.address, registryService);
      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, usInvestor2.address, registryService);
      await registerInvestor(INVESTORS.INVESTOR_ID.GERMANY_INVESTOR_ID, nonUsInvestor.address, registryService);

      await registryService.setCountry(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.GERMANY_INVESTOR_ID, INVESTORS.Country.GERMANY);

      // Issue tokens to non-US investor first
      await dsToken.issueTokens(nonUsInvestor.address, 1000);
      console.log('Non-US investor count:', await complianceService.getUSInvestorsCount());

      // Issue tokens to first US investor (reaches limit)
      await dsToken.issueTokens(usInvestor1.address, 1000);
      console.log('After US investor count:', await complianceService.getUSInvestorsCount());
      expect(await complianceService.getUSInvestorsCount()).to.equal(1);

      // Direct issuance to second US investor should fail
      await expect(dsToken.issueTokens(usInvestor2.address, 100))
        .to.be.revertedWith('Max investors in category');

      // VULNERABILITY: Non-US investor can bypass US limit with full transfer
      // This should be blocked but isn't due to missing country check in US logic
      await dsToken.connect(nonUsInvestor).transfer(usInvestor2.address, 1000);

      // Verify bypass succeeded - usInvestor2 now has tokens despite limit being reached
      expect(await dsToken.balanceOf(usInvestor2.address)).to.equal(1000);
      expect(await dsToken.balanceOf(nonUsInvestor.address)).to.equal(0);
      expect(await complianceService.getUSInvestorsCount()).to.equal(2);
    });
  });
```

**Recommended Mitigation:** Consider updating the conditionals to evaluate to true when the sender (`from`) investor is not a US investor, or when it is a US investor and is not transferring all of its balance; If it's transferring all of its balance, the `from` investor would be decremented from the `usInvestorLimit`.
```diff
        } else if (toRegion == US) {
            ...

            uint256 usInvestorsLimit = getUSInvestorsLimit(_services);
            if (
                usInvestorsLimit != 0 &&
-               _args.fromInvestorBalance > _args.value &&
+               (_args.fromRegion != US || _args.fromInvestorBalance > _args.value) &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getUSInvestorsCount() >= usInvestorsLimit &&
                isNewInvestor(toInvestorBalance)
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            ...
        }
```

**Securitize:** Fixed in commit [5d52ceb](https://github.com/securitize-io/dstoken/commit/5d52ceb4434a89b9547cf22b8d9c8404fa4f5116).

**Cyfrin:** Verified.

## [M-24] Upgradeable contracts should call `_disableInitializers` in constructor
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Upgradeable contracts should [call](https://docs.openzeppelin.com/upgrades-plugins/writing-upgradeable#initializing_the_implementation_contract) `_disableInitializers` in constructor:
```solidity
/// @custom:oz-upgrades-unsafe-allow constructor
constructor() {
    _disableInitializers();
}
```

Affected contracts:
* `contracts/bulk/BulkOperator.sol`
* `contracts/compliance/ComplianceConfigurationService.sol`
* `contracts/compliance/ComplianceServiceNotRegulated.sol`
* `contracts/compliance/ComplianceServiceWhitelisted.sol`
* `contracts/compliance/InvestorLockManager.sol`
* `contracts/compliance/LockManager.sol`
* `contracts/compliance/WalletManager.sol`
* `contracts/issuance/TokenIssuer.sol`
* `contracts/multicall/IssuerMulticall.sol`
* `contracts/rebasing/SecuritizeRebasingProvider.sol`
* `contracts/registry/RegistryService.sol`
* `contracts/registry/WalletRegistrar.sol`
* `contracts/swap/SecuritizeSwap.sol`
* `contracts/token/DSToken.sol`
* `contracts/trust/TrustService.sol`
* `contracts/utils/TransactionRelayer.sol`

**Securitize:** Fixed in commit [094baaf](https://github.com/securitize-io/dstoken/commit/094baaf8562cc2eaae1a89769188ad4e8e7476cb); note some of the listed contracts have been removed as they were obsolete.

**Cyfrin:** Verified.

## [M-25] `ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens` returns positive token amount for blacklisted users
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens` inherited from `ComplianceServiceWhitelisted` will return positive amount of transferable tokens even if the user is blacklisted; this is misleading  because they actually have ZERO transferable tokens due to being blacklisted.

```solidity
  function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        uint64 /*_lockTime*/
    ) public view virtual override returns (uint256) {
        require(_time > 0, "Time must be greater than zero");
        return getLockManager().getTransferableTokens(_who, _time);
    }
```

**Recommended Mitigation:** The function should return 0 for blacklisted addresses.

**Securitize:** Fixed in commit [dc11a37](https://github.com/securitize-io/dstoken/commit/dc11a37ca955ecb0ee03baedcf5f580e7085b1bd).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-26] `ComplianceServiceGlobalWhitelisted::newPreTransferCheck` and `preTransferCheck` allow blacklisted users to transfer tokens
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceGlobalWhitelisted::newPreTransferCheck` and `preTransferCheck` only enforce that the recipient of tokens is not blacklisted, but they don't check that the sender is also not blacklisted:
```solidity
function newPreTransferCheck(
    address _from,
    address _to,
    uint256 _value,
    uint256 _balanceFrom,
    bool _pausedToken
) public view virtual override returns (uint256 code, string memory reason) {
    // First check if recipient is blacklisted
    if (getBlackListManager().isBlacklisted(_to)) {
        return (100, WALLET_BLACKLISTED);
    }

    // Then perform the standard whitelist check
    return super.newPreTransferCheck(_from, _to, _value, _balanceFrom, _pausedToken);
}

function preTransferCheck(address _from, address _to, uint256 _value) public view virtual override returns (uint256 code, string memory reason) {
    // First check if recipient is blacklisted
    if (getBlackListManager().isBlacklisted(_to)) {
        return (100, WALLET_BLACKLISTED);
    }

    // Then perform the standard whitelist check
    return super.preTransferCheck(_from, _to, _value);
}
```

**Impact:** A blacklisted user can transfer their tokens to a non-blacklisted user, effectively evading the blacklist.

**Recommended Mitigation:** `ComplianceServiceGlobalWhitelisted::newPreTransferCheck` and `preTransferCheck` should return correct error codes if `from` address is blacklisted.

**Securitize:** Fixed in commits [32d1a02](https://github.com/securitize-io/dstoken/commit/32d1a020f4fad010f656da2a0da739b06d338e65), [a616d39](https://github.com/securitize-io/dstoken/commit/a616d398add96a08e53942a11ba26cfc505a8ef3).

**Cyfrin:** Verified.

## [M-27] Remove redundant calls to `EnumerableSet::contains`
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `EnumerableSet::_add` and `_remove` already [call](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/structs/EnumerableSet.sol#L75) `_contains` (or perform similar logic), hence there is no need to call this prior to adding or removing elements in:
* `BlackListManager::_addToBlacklist, _removeFromBlacklist`

**Recommended Mitigation:** Call `EnumerableSet::add` or `remove` directly and revert if they return `false`.

**Securitize:** Fixed in commit [a878a41](https://github.com/securitize-io/dstoken/commit/a878a41be5769dc3282c8646f6d145946be7d5ff).

**Cyfrin:** Verified.

## [M-28] Don't initialize to default values in Solidity
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Don't initialize to default values in Solidity:
* `Deposit-Registry`:
```solidity
ComplianceChecker.sol
44:        for (uint i = 0; i < complianceOptions.length; i++) {
58:            uint optionIndex = 0;
65:                uint sbtIndex = 0;

CompliantDepositRegistry.sol
133:            uint i = 0;
157:        for (uint i = 0; i < newDepositAddresses.length; i++) {
200:        for (uint i = 0; i < batchLength; i++) {
```

**Syntetika:**
Fixed in commit [7c69e94](https://github.com/SyntetikaLabs/monorepo/commit/7c69e94d165cfe4b78ace518d622e25654e482d3).

**Cyfrin:** Verified.

## [M-29] Inability for users to permissionlessly stake and earn yield
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** The intention of the protocol as specified in the kick-off call and in discussion with the client is that users should be able to permissionlessly:
* buy hBTC from a decentralized exchange
* stake/unstake hBTC in a permissionless manner via `StakingVault`

**Impact:** In the current implementation `StakingVault` uses `onlyWhitelisted` modifiers on many core functions which prohibits users who permissionlessly bought hBTC using a decentralized exchange from subsequently staking their hBTC and earning yield.

To enable this the admin would need to call `setGlobalWhitelist` which would effectively disable the whitelist and compliance checks anyway.

**Recommended Mitigation:** Consider using only the "blacklist" functionality in `StakingVault` but removing the "whitelist" functionality to allow users to permissionlessly participate in staking and earning yield.

**Syntetika:**
Fixed in commit [86384fe](https://github.com/SyntetikaLabs/monorepo/commit/86384fe1504780338649d25f720fb78b25132875).

**Cyfrin:** Verified.

## [M-30] Missing call to `_setGlobalWhitelist` in `Minter.sol`
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** The `Minter.sol` contract inherits the `Whitelist.sol` abstract contract, which manages access control for the `mint ` and `redeem` functions through the `onlyWhitelisted` modifier:

```solidity
  modifier onlyWhitelisted(address addr) {
        require(isAddressWhitelisted(addr), AddressNotWhitelisted());
        _;
    }

    /// @notice Checks if an address is whitelisted.
    /// @param user The address to check.
    /// @return bool True if the address is whitelisted, false otherwise.
    function isAddressWhitelisted(address user) public view returns (bool) {
        if (manualWhitelist[user] || globalWhitelist) { <-------
            return true;
        }

        return complianceChecker.isCompliant(user);
    }

```

The `onlyWhitelisted` modifier checks the `globalWhitelist` flag. The` StakingVault.sol` contract implements the `setGlobalWhitelist ` function, which is crucial because the `StakingVault.sol` contract expects to use it. However, the `Minter.sol` contract, which mints `HilBTC` (the asset for `StakingVault.sol`), does not implement `setGlobalWhitelist`.

**Impact:** The `StakingVault.sol` contract will not work as expected when `setGlobalWhitelist` is enabled because `setGlobalWhitelist` is not implemented in `Minter.sol`.

**Recommended Mitigation:** Consider implementing `setGlobalWhitelist`  in `minter.sol`:

```solidity
 function setGlobalWhitelist(bool enable) external onlyOwner {
        _setGlobalWhitelist(enable);
    }
```

**Syntetika:**
Fixed in commits [1796e5e](https://github.com/SyntetikaLabs/monorepo/commit/1796e5ec7f50e73e5fc4af32365b936244811217), [86c7b2e](https://github.com/SyntetikaLabs/monorepo/commit/86c7b2e30666f4c6522d48b4f4ed05f5d52238b0) by removing the global whitelist functionality as it was not required by the `Minter` contract, and after the fix for L-4 it is not required at all.

**Cyfrin:** Verified.

## [M-31] Use named mapping parameters to explicitly note the purpose of keys and values
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Use named mapping parameters to explicitly note the purpose of keys and values:
* `Issuance`:
```solidity
vault/StakingVault.sol
37:    mapping(address => UserCooldown) cooldowns;

helpers/Blacklistable.sol
8:    mapping(address => bool) internal _blacklisted;

helpers/Whitelist.sol
6:    /// @notice A mapping of specific user addresses that are allowed to bypass SBT checks
8:    mapping(address => bool) public manualWhitelist;
```

* `Deposit-Registry`:
```solidity
CompliantDepositRegistry.sol
21:    mapping(address => uint) public investorDepositMap;
```

**Syntetika:**
Fixed in commit [6f77988](https://github.com/SyntetikaLabs/monorepo/commit/6f779887cb2ab813c2d15dbc9cca7991a7301367).

**Cyfrin:** Verified.

## [M-32] Variables only set once in `constructor` of non-upgradeable contracts should be declared `immutable`
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Variables only set once in `constructor` of non-upgradeable contracts should be declared `immutable`:
* `CompliantDepositRegistry::complianceChecker`
* `Minter::baseAsset, hilBTCToken`

**Syntetika:**
Fixed in commit [3d1e596](https://github.com/SyntetikaLabs/monorepo/commit/3d1e5967e99de56cb212565eca42845ba8149784).

**Cyfrin:** Verified.

## [M-33] Incorrect error message in `_checkNotBlacklisted`
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The error message in following function says `WLFI: caller is blacklisted`  even though the check is applicable on the input `account` address, not the caller address.

```solidity
  function _checkNotBlacklisted(address _account) internal view {
        require(
            _account == address(0) || !_getStorage().blacklistStatus[_account],
            "WLFI: caller is blacklisted"
        );
    }
```

**Recommended Mitigation:** Consider changing the error message to `WLFI: account is blacklisted`

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L440)

**Cyfrin:** Verified.

## [M-34] Unlimited token reallocation power creates centralization risk
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The `WorldLibertyFinancialV::ownerReallocateFrom` function provides the owner with unrestricted power to burn tokens from any address and mint them to any other address, completely bypassing all security mechanisms implemented throughout the contract.

While this may be intended for legal compliance scenarios, the function creates significant centralization risks and governance manipulation opportunities that undermine the decentralized nature of the token.

```solidity
//WorldLibertyFinancialV2.sol
function ownerReallocateFrom(
    address _from,
    address _to,
    uint256 _value
) public onlyOwner {
    _burn(_from, _value);  // No approval, no checks
    _mint(_to, _value);    // No restrictions
}
```

The function circumvents ALL protective mechanisms:
- Can seize from and send to blacklisted addresses
- Can make transfers when contract is in paused state
- No timelocks - can instantly move tokens between accounts before/after voting deadline
- Minimal event emissions specific to `reallocation`
- No rate-limiting on reallocation - can reallocate any amount between accounts

**Impact:** Users don't truly "own" their tokens if owner can seize them arbitrarily.


**Recommended Mitigation:** Consider adding one or multiple safeguards for the use of this function:

- Clear documentation as to the circumstances when this function will be called (eg. court ordered seizures etc)
- Add specific event emissions when this function is called
- Add governance approval if reallocation is above a threshold amount
- Add time delay if reallocation is above a threshold amount

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L170)

**Cyfrin:** Verified. Specific use case documentation added and additional safeguards implemented.

## [M-35] Commented-out blacklist check allows restricted transfers
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In [`PerpetualBond::_update`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L508-L510), the line intended to restrict transfers between non-blacklisted users is currently commented out:

```solidity
function _update(address from, address to, uint256 amount) internal virtual override {
    // Placeholder for Blacklist check
    // require(!IBlackList(administrator).isBlackListed(from) && !IBlackList(administrator).isBlackListed(to), "blacklisted");
```

This effectively disables blacklist enforcement on transfers of `PerpetualBond` tokens.

**Impact:** Blacklisted addresses can freely hold and transfer `PerpetualBond` tokens, bypassing any intended access control or compliance restrictions.

**Recommended Mitigation:** Uncomment the blacklist check in `_update` to enforce transfer restrictions for blacklisted users.

**YieldFi:** Fixed in commit [`a820743`](https://github.com/YieldFiLabs/contracts/commit/a82074332cc1f57eba398100c3a43e8a70a4c8ce)

**Cyfrin:** Verified. Line doing the blacklist check is now uncommented.

<!-- /Cyfrin Fixed Issues (Merged) -->

