# bridge/session-time-windows - Issues

- Count: 4

## F-2026-14911 - proof Interval Validated as Token Count but Used as Seconds in Timeout Calculation
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The proofInterval parameter has conflicting interpretations in the contract.During session creation, it is validated as a token count with a minimum of100 tokens (`MIN_PROVEN_TOKENS`). However, in `triggerSessionTimeout()`, it is usedas a time duration in seconds to determine when a session can be timedout.This causes unpredictable timeout behavior where the timeout windowis directly tied to the token count rather than an intended time period. function `_validateProofRequirements`(uint256 proofInterval, uint256 deposi t, uint256 pricePerToken) internal pure { // With `PRICE_PRECISION`: maxTokens = deposit * `PRICE_PRECISION` / price PerToken uint256 maxTokens = (deposit * `PRICE_PRECISION`) / pricePerToken; uint256 tokensPerProof = proofInterval; require(tokensPerProof >= `MIN_PROVEN_TOKENS`, "Proof interval too small "); `require(maxTokens >= tokensPerProof, "Deposit too small for proof inte rval")`; } function `triggerSessionTimeout(uint256 jobId)` external nonReentrant { // … bool hasTimedOut = (`block.timestamp` > session.startTime + session.maxD uration) || (`block.timestamp` > session.lastProofTime + session.proofInterva l * 3); `require(hasTimedOut, "Session not timed out")`; // ,,, } Users cannot independently control token-per-proof requirements andtimeout behaviorSessions may timeout unexpectedly early or remain active muchlonger than intended Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed 31

### 修補方式（建議）
Add a separate minTokensPerProof field for time-based timeout logic, keeping proofInterval for detecting abandoned sessions validation only: struct SessionJob { // … uint256 minTokensPerProof; // Minimum tokens host must claim per pro of uint256 proofTimeoutSeconds; // Time in seconds before session conside red abandoned // … } In `_validateProofRequirements`(): function `_validateProofRequirements`( uint256 minTokensPerProof, uint256 deposit, uint256 pricePerToken ) internal pure { uint256 maxTokens = (deposit * `PRICE_PRECISION`) / pricePerToken; require(minTokensPerProof >= `MIN_PROVEN_TOKENS`, "Tokens per proof too smal l"); `require(maxTokens >= minTokensPerProof, "Deposit too small for proof requi rements")`; } Resolution: Fixed in 8893036: Timeout semantics were separated from token-per-proof requirements byintroducing proofTimeoutWindow as an explicit time-based parameter insession configuration and storage. uint256 proofTimeoutWindow; 32 Validation now enforces bounded timeout values (`MIN_PROOF_TIMEOUT` to `MAX_PROOF_TIMEOUT`), while proof token requirements remain validated throughproofInterval and `MIN_PROVEN_TOKENS`. require( params.proofTimeoutWindow >= `MIN_PROOF_TIMEOUT` && params.proofTime outWindow <= `MAX_PROOF_TIMEOUT`, "Invalid proof timeout window" ); triggerSessionTimeout now evaluates abandonment using lastProofTime + proofTimeoutWindow (with `DEFAULT_PROOF_TIMEOUT` fallback for legacy sessions),eliminating the prior coupling of timeout behavior to token-countconfiguration. uint256 timeoutWindow = session.proofTimeoutWindow > 0 ? session.proofTimeoutWindow : `DEFAULT_PROOF_TIMEOUT`; || (`block.timestamp` > session.lastProofTime + timeoutWindow); 33

### 修補方式（實際）
Fixed in 8893036: Timeout semantics were separated from token-per-proof requirements byintroducing proofTimeoutWindow as an explicit time-based parameter insession configuration and storage. uint256 proofTimeoutWindow; 32 Validation now enforces bounded timeout values (`MIN_PROOF_TIMEOUT` to `MAX_PROOF_TIMEOUT`), while proof token requirements remain validated throughproofInterval and `MIN_PROVEN_TOKENS`. require( params.proofTimeoutWindow >= `MIN_PROOF_TIMEOUT` && params.proofTime outWindow <= `MAX_PROOF_TIMEOUT`, "Invalid proof timeout window" ); triggerSessionTimeout now evaluates abandonment using lastProofTime + proofTimeoutWindow (with `DEFAULT_PROOF_TIMEOUT` fallback for legacy sessions),eliminating the prior coupling of timeout behavior to token-countconfiguration. uint256 timeoutWindow = session.proofTimeoutWindow > 0 ? session.proofTimeoutWindow : `DEFAULT_PROOF_TIMEOUT`; || (`block.timestamp` > session.lastProofTime + timeoutWindow); 33

## F-2026-15144 - Dispute Window Calculated From Session Start Time Instead of Last Proof Submission
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The completeSessionJob function uses session.startTime to calculate when thedispute window expires. This is either: A bug: The implementation mistakenly uses startTime instead oflastProofTime A design flaw: If intentional, comparing a global contract `constant(disputeWindow)` against per-session variable duration (maxDuration) isarchitecturally incorrect if (`msg.sender` != session.depositor) { require(`block.timestamp` >= session.startTime + disputeWindow, "Must wait dispute window"); } The default disputeWindow is > 0 seconds, as validated in initialize: require(`_disputeWindow` > 0 && `_disputeWindow` <= 7 days, "Invalid dispute wind ow"); The design compares incompatible values: VariableType Range disputeWindowGlobal constant 30s - 7 days (set once at deploy) maxDuration Per-session parameterVariable (user chooses per session) They are not comparable because: disputeWindow = 30 seconds is meaningless for a 24-hour `session(expires at 0.03% of session)` disputeWindow = 1 day blocks a 1-hour session from completing for 23extra hours The contract cannot know appropriate disputeWindow at deploymentbecause session durations are determined later by users. A globalconstant cannot correctly protect sessions of varying lengths. Attack Scenario Session created with 100 `USDC` deposit at T0 Session runs normally for 1 hour with legitimate work At T0 + 1 hour, host submits an inflated proof claiming excessivetokens 42 At T0 + 1 hour + 1 second, host calls completeSessionJob Check passes: T0 + 1 hour > T0 + 30 seconds Session completes immediately with inflated tokensUsed User and the system had no opportunity to review the final proof The dispute window becomes meaningless after the first disputeWindow seconds of a session. Proofs submitted after startTime + disputeWindow canbe immediately settled with zero verification time. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
Change the dispute window reference from startTime to lastProofTime: if (`msg.sender` != session.depositor) { require( `block.timestamp` >= session.lastProofTime + disputeWindow, "Must wait dispute window after last proof" ); } If the current behavior is intentional, evaluate whether a single globalconstant can adequately protect sessions with varying durations, or if aper-session or proof-relative approach is needed. Resolution: Fixed in 596ea59: completeSessionJob now gates non-depositor completion using session.lastProofTime + disputeWindow instead of session.startTime + disputeWindow. 43 if (`msg.sender` != session.depositor) { require(`block.timestamp` >= session.lastProofTime + disputeWindow, "Must w ait dispute window"); } The dispute delay is therefore anchored to the most recent proofsubmission, preserving a review interval before host-triggered settlementregardless of total session duration. 44

### 修補方式（實際）
Fixed in 596ea59: completeSessionJob now gates non-depositor completion using session.lastProofTime + disputeWindow instead of session.startTime + disputeWindow. 43 if (`msg.sender` != session.depositor) { require(`block.timestamp` >= session.lastProofTime + disputeWindow, "Must w ait dispute window"); } The dispute delay is therefore anchored to the most recent proofsubmission, preserving a review interval before host-triggered settlementregardless of total session duration. 44

## F-2026-15257 - Early Cancel Fee Applied on Depositor-Triggered Timeouts
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
The `_settleSessionPayments` function applies the early cancellation fee basedsolely on whether the caller (completedBy) matches the session depositorand no proofs exist. This logic is shared by both completeSessionJob (voluntary termination) and triggerSessionTimeout (forced termination due tohost inactivity). No distinction is made between the two termination paths. uint256 earlyFee; // Early cancel fee: depositor cancels before any proofs if (completedBy == session.depositor && session.proofs.length == 0 && minToke nsFee > 0) { earlyFee = (minTokensFee * session.pricePerToken) / `PRICE_PRECISI` ON; if (hostPayment >= session.deposit) { earlyFee = 0; } else if (earlyFee > session.deposit - hostPayment) { earlyFee = session.deposit - hostPayment; } } triggerSessionTimeout passes `msg.sender` as completedBy: `_settleSessionPayments`(jobId, `msg.sender`); When a host fails to submit any proof within proofTimeoutWindow, the sessionbecomes eligible for timeout. If the depositor calls triggerSessionTimeout, thecondition completedBy == session.depositor && session.proofs.length == 0 && minTokensFee > 0 evaluates to true, and the early cancellation fee isdeducted from the depositor's deposit and forwarded to the host. This inverts the intended economic incentive: the early cancel fee exists topenalize depositors who create and immediately cancel sessions, wastinghost resources. In the timeout scenario, the host abandoned the sessionby not submitting proofs. Charging the depositor for the host's inaction andforwarding that fee to the inactive host rewards non-performance. Found in commit: f614355. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed 57

### 修補方式（建議）
Restrict early cancel fee application to voluntary session completion only.One approach is to check the session status at the point of fee evaluation: if (completedBy == session.depositor && session.proofs.length == 0 && minTokensFee > 0 && session.status == SessionStatus.Completed) { Since triggerSessionTimeout sets session.status = SessionStatus.TimedOut beforecalling `_settleSessionPayments`, the condition would exclude timeout-triggered settlements while preserving fee application for voluntarydepositor cancellations via completeSessionJob. Resolution: The early cancellation fee condition now additionally checks that session.status == SessionStatus.Completed, ensuring the fee is only applied onvoluntary depositor cancellations and not on timeout paths where thesession status is TimedOut: // Early cancel fee: depositor cancels before any proofs (F202615257: not on timeout) if (completedBy == session.depositor && session.status == SessionStatus.Compl eted && session.proofs.length == 0 && minTokensFee > 0) { Revised commit: df1f2e4. 58

### 修補方式（實際）
The early cancellation fee condition now additionally checks that session.status == SessionStatus.Completed, ensuring the fee is only applied onvoluntary depositor cancellations and not on timeout paths where thesession status is TimedOut: // Early cancel fee: depositor cancels before any proofs (F202615257: not on timeout) if (completedBy == session.depositor && session.status == SessionStatus.Compl eted && session.proofs.length == 0 && minTokensFee > 0) { Revised commit: df1f2e4. 58

## F-2025-14287 - Do S via Concurrent Joint Contributor Invites - Medium
- 嚴重度：Medium
- Report source：RYT.pdf

### 問題內容（摘要）
The Komiti contract allows a Primary Contributor to invite a SecondaryContributor to share a slot via joinGroupWithJointContributor. The contractintends to limit each Primary Contributor to a single slot, enforcing this bychecking s_contributions[groupId][msg.sender] == 0. An issue allows a Primary Contributor to bypass the single-slot restrictionby sending multiple invites concurrently before any are accepted. Because s_contributions is only updated when a Secondary accepts an invite (in acceptInviteForJointContributor), the check in joinGroupWithJointContributor passes multiple times. This results in the Primary Contributor being addedto the group.members array multiple times, creating "duplicate slots." Since auser can only be paid once per group cycle, these duplicate slots disruptthe payout logic, causing the final payout cycle to fail  DoS) andpermanently locking the funds collected for that cycle. The issue stems from the timing gap between sending an invite and itsacceptance. Concurrent Invites: The Primary calls joinGroupWithJointContributor twice (or more) in rapid succession with different Secondaries. require(s_contributions[groupId][msg.sender] == 0, "Komiti: User alre

### 修補方式（實際）
Fixed in 1829f31. The functions acceptInviteForJointContributor() and joinGroupWithJointContributor() have been removed from the codebase. Evidences PoC

## Cyfrin Fixed Issues (Merged)
- Count: `14`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] A single holder can grief the payouts of all holders forwarding their payouts to the same forwarder
- Severity: `Critical`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** This grief attack is similar to [issue [*Forwarders can lose payouts of the holders forwarding to them*](#forwarders-can-lose-payouts-of-the-holders-forwarding-to-them)](https://github.com/remora-projects/remora-smart-contracts/issues/49). The main difference is that this attack does not need the forwarder to gain holder status and zero out his balance on the same distributionIndex. This grief attack can be executed at any index while the forwarder has no balance.

The steps that allows the grief attack to occur are:
1. forwarder has balance, it is a holder
2. various holders set the same address as their designated forwarder
3. payouts for holders are computed and credited to forwarder
4. forwarder claims payouts, and gets computed all pending payouts
    - At this point, payoutBalance of forwarder would be 0
5. forwarder zeros out his balance, and [gets removed the `isHolder` status (no longer a holder)](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L596-L600)
6. distributions passes
7. One of the holders [removes the forwarder](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L215-L222) as his designated forwarder
    - [Because the forwarder has no balance, and is not a holder, the data of the forwarder will be deleted,](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L362-L365) including any outstanding calculatedPayout that has been accumulated for the holders who set the forwarder as their forwarder.
8. As a result of step 7, the unclaimed payouts earned by the holder get lost

**Impact:**
- Payouts of holders forwarding to the same forwarder can be grief by a single holder.
- Holders forwarding their payouts to a non-holder account will lose their payouts if they remove the forwarder while he is still a non-holder.

**Proof of Concept:** Run the following test to reproduce the scenario described in the Description section.
```solidity
    function test_holderForcesForwarderToLosePayouts() public {
        address user1 = users[0];
        address user2 = users[1];
        address forwarder = users[2];

        uint256 amountToMint = 1;

        _whitelistAndMintTokensToUser(user1, amountToMint * 8);
        _whitelistAndMintTokensToUser(user2, amountToMint);
        _whitelistAndMintTokensToUser(forwarder, amountToMint);

        // both users sets the same forwarder as their forwardAddress
        remoraTokenProxy.setPayoutForwardAddress(user1, forwarder);
        remoraTokenProxy.setPayoutForwardAddress(user2, forwarder);

        // fund total payout amount to funding wallet
        uint64 payoutDistributionAmount = 100e6;

        // Distribute payouts for the first 5 distributions
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // user1 must have 0 payout because it is forwarding to `forwarder`
        uint256 user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");

        // user2 must have 0 payout because it is forwarding to `forwarder`
        uint256 user2PayoutBalance = remoraTokenProxy.payoutBalance(user2);
        assertEq(user2PayoutBalance, 0, "Forwarding payout is not working as expected");

        //forwarder must have the full payout for the 5 distributions because both users are forwarding to him
        uint256 forwarderPayoutBalance = remoraTokenProxy.payoutBalance(forwarder);
        assertEq(forwarderPayoutBalance, payoutDistributionAmount * 5, "Forwarding payout is not working as expected");

        // forwarder claims all the outstanding payout
        vm.startPrank(forwarder);
        remoraTokenProxy.claimPayout();
        assertEq(stableCoin.balanceOf(forwarder), forwarderPayoutBalance);

        // forwarder zeros out his PropertyToken's balance
        remoraTokenProxy.transfer(user2, remoraTokenProxy.balanceOf(forwarder));
        vm.stopPrank();

        assertEq(remoraTokenProxy.balanceOf(forwarder), 0);

        (bool isHolder) = remoraTokenProxy.getHolderStatus(forwarder).isHolder;
        assertEq(isHolder, false);

        // Distribute payouts for distributions 5 - 10
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // user1 must have 0 payout because it is forwarding to `forwarder`
        user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");

        // user2 must have 0 payout because it is forwarding to `forwarder`
        user2PayoutBalance = remoraTokenProxy.payoutBalance(user2);
        assertEq(user2PayoutBalance, 0, "Forwarding payout is not working as expected");

        (uint64 calculatedPayout) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        assertEq(calculatedPayout, payoutDistributionAmount * 5, "Forwarder did not receive payout for holder forwarding to him");

        // user2 gets forwarder removed as its forwardedAddress
        remoraTokenProxy.removePayoutForwardAddress(user2);

        //@audit => When this vulnerability is fixed, we expect finalCalculatedPayout to be equals than calculatedPayout!
        (uint64 finalCalculatedPayout) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        //@audit-issue => user2 causes the payout of user1 to be lost, which is 4x the payout lose by him
        assertEq(finalCalculatedPayout, 0, "Forwarder did not lose payout of holder");
    }
```

There is a second scenario similar to the one explained in the description section. In this other scenario, the forwarder is a non-holder, and, after a couple of distributions, the holder decides to remove or change the current forwarder to a different address, which leads to unclaimed payouts being lost.
- Run the next test to demonstrate the previous scenario
```solidity
    function test_HolderLosesPayout_HolderRemovesForwarderWhoWasNeverAHolder() public {
        address user1 = users[0];
        address forwarder = users[1];

        uint256 amountToMint = 1;

        _whitelistAndMintTokensToUser(user1, amountToMint);

        remoraTokenProxy.setPayoutForwardAddress(user1, forwarder);

        // fund total payout amount to funding wallet
        uint64 payoutDistributionAmount = 100e6;

        // Distribute payouts for the first 5 distributions
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // user1 must have 0 payout because it is forwarding to `forwarder`
        uint256 user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");

        (uint64 forwarderPayoutBalance) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        assertEq(forwarderPayoutBalance, payoutDistributionAmount * 5, "Forwarding payout is not working as expected");

        // forwarder attempts to claim all his payout while he is not a holder
        (bool isHolder) = remoraTokenProxy.getHolderStatus(forwarder).isHolder;
        assertEq(isHolder, false);
        // claiming reverts because forwarder is not a holder
        vm.prank(forwarder);
        vm.expectRevert();
        remoraTokenProxy.claimPayout();

        // user1 gets forwarder removed as its forwardedAddress
        remoraTokenProxy.removePayoutForwardAddress(user1);

        // validate forwarder and holder have lost the payouts for the past 5 distributions
        (forwarderPayoutBalance) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        assertEq(forwarderPayoutBalance, 0, "Forwarding payout is not working as expected");

        (uint256 finalForwarderPayoutBalance) = remoraTokenProxy.payoutBalance(forwarder);
        assertEq(finalForwarderPayoutBalance, 0, "Forwarding payout is not working as expected");

        // user1 must have 0 payout because it is forwarding to `forwarder`
        user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");
    }
```

**Recommended Mitigation:** On `_removePayoutForwardAddress()`, validate that the holderStatus of the forwardedAddress is 0, if it is not, don't call `deleteUser()`

```diff
function _removePayoutForwardAddress(
        HolderManagementStorage storage $,
        address holder,
        address forwardedAddress
    ) internal {
        if (forwardedAddress != address(0)) {
            ...
            if (
                balanceOf(forwardedAddress) == 0 &&
                payoutBalance(forwardedAddress) == 0
+              && $._holderStatus[forwardedAddress].calculatedPayout == 0
            ) deleteUser(forwardedHolder);
        }
```

**Remora:** Fixed in commit [7bd2691](https://github.com/remora-projects/remora-smart-contracts/commit/7bd269128ebeac7f2cae0e30d55ee666e8fa21d7).

**Cyfrin:** Verified.

\clearpage
## High Risk

## [M-2] `Authorizable::_verify` should use EIP-712 typed structured data hashing
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** [`Authorizable::_verify`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/access/Authorizable.sol#L46-L78) signs ad-hoc payloads that include `chainId`, but the flow is not [EIP-712](https://eips.ethereum.org/EIPS/eip-712) typed-data compliant. This limits wallet UX/visibility and interoperability and mixes domain data (`chainId`) with message data.

**Impact:** Users are more susceptible to ambiguous signing prompts; weaker ecosystem compatibility; harder audits/upgrades; higher risk of encoding/packing mistakes and replay bugs across contracts or chains.

**Recommended mitigation:**
Adopt EIP-712 and move `chainId` to the domain separator (remove it from the struct). Keep the existing intent of the message:

* **Domain:** `{ name: "Authorizable", version: "1", chainId, verifyingContract: address(this) }`.
* **Typed struct (no chainId inside):**

  ```solidity
  struct TxAuthData {
      bytes   functionCallData;   // selector + encoded args
      address contractAddress;    // target contract (can be redundant with domain; decide and document)
      address account;            // controller / signer subject
      uint256 nonce;              // per-account nonce
      uint256 blockExpiration;    // deadline
  }

  bytes32 constant TXAUTH_TYPEHASH = keccak256(
      "TxAuthData(bytes functionCallData,address contractAddress,address account,uint256 nonce,uint256 blockExpiration)"
  );
  ```
* **Hashing & verify (using OZ EIP712 + SignatureChecker):**

  ```solidity
  bytes32 structHash = keccak256(abi.encode(
      TXAUTH_TYPEHASH,
      keccak256(txAuth.functionCallData), // hash dynamic bytes
      txAuth.contractAddress,
      txAuth.account,
      txAuth.nonce,
      txAuth.blockExpiration
  ));
  bytes32 digest = _hashTypedDataV4(structHash);
  require(
      SignatureChecker.isValidSignatureNow(signer, digest, signature),
      "INVALID_SIGNATURE"
  );
  ```
**Accountable:** Fixed in commit [`70cd486`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/70cd4863e3bef0f80f2eeb012c79a801c099fc7e)

**Cyfrin:** Verified. EIP-712 typed data is now used for the signatures.

## [M-3] Signatures have no expiration deadline
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Signatures which have [no expiration parameter](https://dacian.me/signature-replay-attacks#heading-no-expiration) effectively grant a lifetime license. Consider adding an expiration parameter to the signature that if used after that time results in the signature being invalid.

**CryptoArt:**
Fixed in commit [a93977d](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/a93977d2ef0b54319c7668d9fc6abda688b355c1).

**Cyfrin:** Verified.

## [M-4] `min_qty` Bypass via `IOC` limit order
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Spot orders compute the minimum order quantity `min_qty` from the user‐supplied limit price. An attacker can set an arbitrarily large limit price to drive `min_qty` down to a tiny value while the actual execution price is still clamped near the mark price. This bypasses the intended minimum order size enforcement for IOC orders.

`SpotParams::get_settings` enforces a ±12.5 % clamp on IOC prices via the `ipx` variable, but the minimum tokens are calculated from the original `px` argument (the user provided price) even when `IOC` mode is active:

```rust
        if ioc != 0 {
            if px < last_px - max_diff {
                ipx = last_px - max_diff;
            } else if px > last_px + max_diff {
                ipx = last_px + max_diff;
            } else {
                ipx = px;
            }
        } else if px < last_px - max_diff || px > last_px + max_diff {
            bail!(DeriverseErrorKind::InvalidPrice {
                price: px,
                min_price: last_px - max_diff,
                max_price: last_px + max_diff,
            });
        } else {
            ipx = px;
        }
...
        let min_tokens = min_qty(px, dc);
        // TODO remove
        if qty != 0 && qty.abs() < min_tokens {
            bail!(DeriverseErrorKind::InvalidQuantity {
                value: qty,
                min_value: min_tokens,
                max_value: SPOT_MAX_AMOUNT,
            });
        }
```

Because `min_qty` uses the unbounded px, **for bid orders**, an attacker can send `ioc != 0` with `LIMIT order` and choose an enormous `data.price`. `min_qty` then pulls a very small threshold from `PRICE_TOKENS`, allowing the attacker to submit dust-sized orders. The engine later clamps the executable price to within ±12.5 % of the mark, so the trade still goes through at the normal market price, but with an amount far below the intended minimum.

For example, the current price is `500_000_000`, the attacker/user can make `px=100_000_000_000_000` so that he can pay as little as `20_000`, making dust order.

**Impact:** Minimum order size limits for `IOC` orders can be bypassed. Attackers can generate large numbers of dust trades by supplying a large `data.price`.

**Recommended Mitigation:** Consider computing `min_qty` using the current market price.

**Deriverse:** Fixed in commit [134db8b](https://github.com/deriverse/protocol-v1/commit/134db8b1dac9e48641dac1a6b95bcf34637f695f).

**Cyfrin:** Verified.

## [M-5] Missing `last_time` Update in `spot_lp` Causes Incorrect Daily Trade Statistics
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `spot_lp` function uses `instr_state.header.last_time` to determine if a day has passed, but never updates this field.

In contrast, other trading functions (`swap, new_spot_order, spot_quotes_replace`) update `last_time` via `engine.write_last_tokens()`. This inconsistency causes incorrect daily LP trade statistics when regular trading operations haven't occurred recently.

In `src/program/processor/spot_lp.rs`, the function checks if a day has passed using:

```solidity
if instr_state.header.last_time < fixing_time {
    instr_state.header.lp_prev_day_trades = instr_state.header.lp_day_trades;
    instr_state.header.lp_day_trades = 1;
} else {
    instr_state.header.lp_day_trades += 1;
}
```

However, `instr_state.header.last_time` is never updated in the `spot_lp` function, while other trading functions update it.

Consider the following case:
- Last regular trade (swap/new_spot_order) occurred 1 day ago, setting last_time to that timestamp
- Multiple spot_lp operations occur today
- For each spot_lp:
    - `last_time` remains from 1 day ago
    - `fixing_time` is today's settlement time
    - `last_time < fixing_time` is always true
    - `lp_day_trades` is reset to 1 instead of incrementing


**Impact:** In such case(last regular trade occurred 1 day ago), all LP trades on the same day are counted as the first trade of the day, losing accurate daily statistics.

**Recommended Mitigation:** Update `last_time` in the `spot_lp` function after the day-crossing check.

```rust
instr_state.header.lp_day_trades += 1;
}
instr_state.header.last_time = time;  // Add this line
```

**Deriverse:** Fixed in commit [29281c5](https://github.com/deriverse/protocol-v1/commit/29281c5e489ad01efbb5124e62c45f55aa309348).

**Cyfrin:** Verified.

## [M-6] Missing Fixing Window Data Accumulation After Daily Reset in `drv_update`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** When `drv_update` resets fixing data for a new day, the current `last_asset_tokens` and `last_crncy_tokens` are discarded instead of being accumulated into the new day's fixing data, leading to incomplete fixing price calculations.

In `src/state/instrument.rs`, the `drv_update` function handles daily reset logic:
```rust
if current_date > last_fixing_date {
    // Calculate new fixing price based on previous day's data
    let new_fixing_px: i64 = if self.header.fixing_crncy_tokens
        > get_dec_factor(self.header.crncy_token_decs_count)
    {
        (self.header.fixing_crncy_tokens as f64 * self.header.dec_factor as f64
            / self.header.fixing_asset_tokens as f64) as i64
    } else {
        prev_px
    };
    self.header.fixing_asset_tokens = 0;  // Reset
    self.header.fixing_crncy_tokens = 0;  // Reset
    self.header.fixing_time = time;
    // ... update variance and fixing_px
} else {
    // Only accumulate if within fixing window
    let sec = time % DAY;
    if last_asset_tokens > 0 && (SETTLEMENT - FIXING_DURATION..SETTLEMENT).contains(&sec) {
        self.header.fixing_asset_tokens += last_asset_tokens;
        self.header.fixing_crncy_tokens += last_crncy_tokens;
    }
}
```

When entering a new day (`current_date > last_fixing_date`), the code resets `fixing_asset_tokens` and `fixing_crncy_tokens` to `0`
However, if the current time time is still within the fixing window (S`ETTLEMENT - FIXING_DURATION..SETTLEMENT`), the current `last_asset_tokens` and `last_crncy_tokens` should be accumulated into the new day's fixing data. **Currently, these values are discarded after reset, and the code does not check if the current time is within the fixing window**


**Impact:** Trading volume that occurs immediately after the daily reset but within the fixing window is not included in the fixing price calculation.

**Recommended Mitigation:** After resetting the fixing data, check if the current time is within the fixing window and accumulate the current data if applicable.

**Deriverse:** Fixed in commit [d17502c5](https://github.com/deriverse/protocol-v1/commit/d17502c5b1c9fc44abad88365f7d60b3b3325a26).

**Cyfrin:** Verified.

## [M-7] Seizing payouts for frozen users can lead to double spending if the holder is unfrozen in subsequent distributions
- Severity: `Medium`
- Source report: `final.md`

### Detailed Content (from source)
**Description:** The `ChildToken::seizeFrozenFunds` function is designed to perform the following operations:
- Permit the legitimate holder to claim all dividend distributions accrued prior to the imposition of the freeze.
- Transfer to the designated custodian all dividend distributions corresponding to the entire freeze period, up to and including the most recent distribution paid at the time of seizure execution.

A vulnerability exists whereby a frozen holder may subsequently claim dividends attributable to the freeze period despite those funds having already been seized and redirected to the custodian.

The issue manifests under the following sequence of events:
1. `ChildToken::seizeFrozenFunds` is invoked on a frozen account while one or more distributions have occurred during the freeze period. This correctly redirects the frozen-period dividends to the custodian and records the seizure snapshot in `holder.frozenIndex` and related accounting variables.
2. A new dividend distribution is created after the seizure has taken place.
3. While the account remains frozen, the holder (or anyone) invokes `DividendManager::payoutBalance`. Because the account is still frozen, the internal accounting variable `holder.lastPayoutIndexCalculated` is forcibly reset to `holder.frozenIndex`.
4. The account is subsequently unfrozen.
5. Post-unfreeze, the holder again calls payoutBalance. At this point:
- The account is no longer frozen.
- `holder.lastPayoutIndexCalculated` remains at the value previously forced during step 3 (`holder.frozenIndex`).
- The payout routine therefore processes and credits all distributions from `holder.frozenIndex` through the current latest distribution index. Consequently, the holder receives the entirety of the previously seized frozen-period dividends a second time, resulting in a double payment (once received by the custodian and then by the holder).

**Impact:** The frozen user, who has already had their payouts seized for the duration of the freeze period, can regain access to claim those payouts, effectively taking funds that are reserved to process the payouts of other holders.

**Proof of Concept:** Add the next PoC to the `DividendManager.t.sol` test file:
```solidity
    function test_PoC_DoubleSpendingPayoutsOfFrozenHolder() public {
        // distribute payout, freeze holder, distribute more payouts while holder is frozen, seizeFrozen, distribute a payout, call to payoutBalance() to reset lastIndex to frozenIndex, then unfreeze holder, call payoutBalance() and get access to all payouts since the user was frozen!
        address user = domesticUsers[0];
        address custodian = domesticUsers[1];

        uint64 tokenToMint = 5;
        uint64 payoutAmount = 100e6;

        // mint and send user the tokens
        _mintAndTransferToUser(user, tokenToMint);

        // create distribution + verify
        _fundPayoutToPaymentSettler(payoutAmount);
        assertEq(d_childTokenProxy.payoutBalance(user), payoutAmount);

        assertEq(d_childTokenProxy.payoutBalance(user), payoutAmount);

        // freeze user + 5 payouts
        d_childTokenProxy.freezeHolder(user);
        _fundPayoutToPaymentSettler(payoutAmount);
        _fundPayoutToPaymentSettler(payoutAmount);
        _fundPayoutToPaymentSettler(payoutAmount);
        _fundPayoutToPaymentSettler(payoutAmount);
        _fundPayoutToPaymentSettler(payoutAmount);

        // seize frozen payouts from user, send frozen funds to custodian
        d_childTokenProxy.seizeFrozenFunds(user, custodian, false);
        // user receives the payouts owed prior to being frozen
        assertEq(stableCoin.balanceOf(user), payoutAmount);
        // custodian receives the payouts while the user was frozen
        assertEq(stableCoin.balanceOf(custodian), payoutAmount * 5);
        assertEq(d_childTokenProxy.payoutBalance(user), 0);
        assertEq(d_childTokenProxy.isHolderFrozen(user), true);

        // One more payout - Since the user was frozen, this is the 6th payout
        _fundPayoutToPaymentSettler(payoutAmount);

        assertEq(d_childTokenProxy.payoutBalance(user), 0);

        d_childTokenProxy.unFreezeHolder(user);

        //@audit-issue => Because `frozenIndex` was not updated, bug allows the user to claim the 6 payouts since he was frozen regardless that 5 of those 6 payouts have already been paid out to the custodian via the `seizeFrozenFunds()`
        assertEq(d_childTokenProxy.payoutBalance(user), payoutAmount * 6);

    }
```

**Recommended Mitigation:** When freezing the user again, set the `holderStatus.frozenIndex` to the `$._currentPayoutIndex`.

**Remora:** Fixed in commit [2969545](https://github.com/remora-projects/remora-dynamic-tokens/commit/29695454e47dc9844715c9a157d90c3fcaad736d)

**Cyfrin:** Verified. `holderStatus.frozenIndex` is set to `$._currentPayoutIndex` after the holder is frozen again.

\clearpage

## [M-8] Consider emitting event when synchronizing `lst Liability Principal`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` synchronizes `$$.lstLiabilityPrincipal` which may have changed due to positive or negative `stETH` rebasing.

However this function emits no events even though it changes `$$.lstLiabilityPrincipal`; consider emitting an event with at least the delta change for easier off-chain tracking and auditability.

**Linea:** Fixed in commit [9f32daf](https://github.com/Consensys/linea-monorepo/commit/9f32daf25bf053bd099314bd1db974415a98c7fe).

**Cyfrin:** Verified.

## [M-9] Refactor `Lido St Vault Yield Provider::_sync External Liability Settlement` to eliminate `liability ETH`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Local variable `liabilityETH` can be refactored away in `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` by using the named return variable:
```solidity
  function _syncExternalLiabilitySettlement(
    YieldProviderStorage storage $$,
    uint256 _liabilityShares,
    uint256 _lstLiabilityPrincipalCached
  ) internal returns (uint256 lstLiabilityPrincipalSynced) {
    lstLiabilityPrincipalSynced = STETH.getPooledEthBySharesRoundUp(_liabilityShares);
    // If true, this means an external actor settled liabilities.
    if (lstLiabilityPrincipalSynced < _lstLiabilityPrincipalCached) {
      $$.lstLiabilityPrincipal = lstLiabilityPrincipalSynced;
    } else {
      lstLiabilityPrincipalSynced = _lstLiabilityPrincipalCached;
    }
  }
```

**Linea:** Fixed in commit [5b55950](https://github.com/Consensys/linea-monorepo/commit/5b5595062d4c4f37ceb8e23fc737e34239f7b232).

**Cyfrin:** Verified.

\clearpage

## [M-10] `Payment Settler::claim All Payouts` doesn't validate input `tokens` addresses are legitimate contracts before calling `admin Claim Payout` on them
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** In `PaymentSettler::initiateBurning` and `distributePayment`, before calling any functions on the input `token` address this check occurs to ensure it is a legitimate address:
```solidity
if (!tokenData[token].active) revert InvalidTokenAddress();
```

But in `PaymentSettler::claimAllPayouts` this check does not occur:
```solidity
function claimAllPayouts(address[] calldata tokens) external nonReentrant {
    address investor = msg.sender;
    uint256 totalPayout = 0;
    for (uint i = 0; i < tokens.length; ++i) {
        TokenData storage curToken = tokenData[tokens[i]];
        uint256 amount = IRemoraToken(tokens[i]).adminClaimPayout(
            investor,
            true
        );
```

**Impact:** An attacker can deploy their own contract which implements the `adminClaimPayout` function interface but this function can contain arbitrary code; execution flow is transferred to the attacker's contract. We have not found a way to further abuse this but it isn't a good practice to allow an attacker to hijack execution flow into their own custom contracts.

**Recommended Mitigation:** Verify that the input `tokens` are valid `RemoraToken` contracts prior to calling any functions on them.

**Remora:** Fixed in commit [4ba903e](https://github.com/remora-projects/remora-smart-contracts/commit/4ba903e52438e9570940c11ae8c39acf07256b6a).

**Cyfrin:** Verified.

## [M-11] Forwarders can lose payouts of the holders forwarding to them
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** A holder can have a designated forwarder who will accumulate the payouts earned by the holder.
The vulnerability identified in this report is when the designated forwarder has no pending payouts to claim and zeroes out his PropertyToken's balance, and, time passes (while forwarder is still accumulating the payouts of the holder) and then it becomes a holder again, but on the same distributionIndex the forwarder zeroes out his balance again.
- The combination of these steps leads the contract's state to an inconsistent state that ends up causing the unclaimed accumulated payouts to be lost.

The steps that lead the contracts to the inconsistent state are:
1. forwarder has balance, it is a holder
2. holder sets a forwarder
3. payouts for holder are computed and credited to forwarder
4. forwarder claims payouts, and gets computed all pending payouts
    - At this point, payoutBalance of forwarder would be 0
5. forwarder zeros out his balance, and [gets removed the `isHolder` status (no longer a holder)](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L596-L600)
6. distributions passes
7. payouts for holder are computed and credited to the forwarder
8. forwarder gets a balance and regains holder status
    - [lastPayoutIndexCalculated = currentPayoutIndex](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L523-L525)
10. forwarder zeros out his balance again
    - payoutBalance(forwarder) is called but returns 0 because [`lastPayoutIndexCalculated == currentPayoutIndex`](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L450-L454)
    - so, [balance == 0 and payoutBalance() returns 0, deleteUser(forwarder) gets called](https://github.com/remora-projects/remora-smart-contracts/blob/main/contracts/RWAToken/DividendManager.sol#L547-L550)
11. As a result of step 10, the payouts earned by the holder get lost

**Impact:** Forwarders can lose holders' payouts

**Proof of Concept:** Run the following test to reproduce the scenario described on the Description section.

```solidity
    function test_forwarderLosesHolderPayouts() public {
        address user1 = users[0];
        address forwarder = users[1];
        address anotherUser = users[2];

        uint256 amountToMint = 1;

        _whitelistAndMintTokensToUser(user1, amountToMint);
        _whitelistAndMintTokensToUser(forwarder, amountToMint);
        // Only whitelist and allow anotherUser
        _whitelistAndMintTokensToUser(anotherUser, 0);

        remoraTokenProxy.setPayoutForwardAddress(user1, forwarder);

        // fund total payout amount to funding wallet
        uint64 payoutDistributionAmount = 100e6;

        // Distribute payouts for the first 5 distributions
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // user1 must have 0 payout because it is forwarding to `forwarder`
        uint256 user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");

        //forwarder must have the full payout for the 5 distributions because user1 is forwarding to him
        uint256 forwarderPayoutBalance = remoraTokenProxy.payoutBalance(forwarder);
        assertEq(forwarderPayoutBalance, payoutDistributionAmount * 5, "Forwarding payout is not working as expected");

        // forwarder claims all his payout
        vm.startPrank(forwarder);
        remoraTokenProxy.claimPayout();
        assertEq(stableCoin.balanceOf(forwarder), forwarderPayoutBalance);

        // forwarder zeros out his PropertyToken's balance
        remoraTokenProxy.transfer(anotherUser, remoraTokenProxy.balanceOf(forwarder));
        vm.stopPrank();

        assertEq(remoraTokenProxy.balanceOf(forwarder), 0);

        (bool isHolder) = remoraTokenProxy.getHolderStatus(forwarder).isHolder;
        assertEq(isHolder, false);

        // Distribute payouts for distributions 5 - 10
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // user1 must have 0 payout because it is forwarding to `forwarder`
        user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        assertEq(user1PayoutBalance, 0, "Forwarding payout is not working as expected");

        (uint64 calculatedPayout) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        assertEq(calculatedPayout, (payoutDistributionAmount * 5) / 2, "Forwarder did not receive payout for holder forwarding to him");

        vm.startPrank(anotherUser);
        // forwarder becomes a holder again
        remoraTokenProxy.transfer(forwarder, remoraTokenProxy.balanceOf(anotherUser));
        vm.stopPrank();

        vm.startPrank(forwarder);
        // forwarder zeroues out his balance again
        remoraTokenProxy.transfer(anotherUser, remoraTokenProxy.balanceOf(forwarder));
        vm.stopPrank();

        //@audit => When this vulnerability is fixed, we expect finalCalculatedPayout to be equals than calculatedPayout!
        (uint64 finalCalculatedPayout) = remoraTokenProxy.getHolderStatus(forwarder).calculatedPayout;
        assertEq(finalCalculatedPayout, 0, "Forwarder did not lose payout of holder");
    }
```

**Recommended Mitigation:** In `_updateHolders()`, check `holderStatus.calculatedPayout` to be 0, if it is not 0, don’t call deleteUser()
```diff
function _updateHolders(address from, address to) internal {
        ...

        if (from != address(0)) {
            ...
            HolderStatus storage fromHolderStatus = $._holderStatus[from];
-           if (fromBalance == 0 && payoutBalance(from) == 0) {
+           if (fromBalance == 0 && payoutBalance(from) == 0 && fromHolderStatus.calculatedPayout == 0) {
                deleteUser(fromHolderStatus);
                return;
            }
            ...
            }
        }
    }
```

**Remora:** Fixed in commit [d379e89](https://github.com/remora-projects/remora-smart-contracts/commit/d379e89ac7ae503f6eec775660983c7017a4a513).

**Cyfrin:** Verified.

## [M-12] Using explicit unsigned integer sizing instead of `uint`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** In Solidity `uint` automatically maps to `uint256` but it is considered good practice to specify the exact size when declaring variables:
```solidity
PaymentSettler.sol
124:        for (uint i = 0; i < len; ++i) {
174:        for (uint i = 0; i < tokens.length; ++i) {
227:        for (uint i = 0; i < tokenList.length; ++i) {

RWAToken/DocumentManager.sol
224:        for (uint i = 0; i < dHLen; ++i) {

TokenBank.sol
185:        for (uint i = 0; i < len; ++i) {
260:        for (uint i = 0; i < developments.length; ++i)
267:        for (uint i = 0; i < developments.length; ++i) {
```

**Remora:** Fixed in commit [6602423](https://github.com/remora-projects/remora-smart-contracts/commit/66024232cfea24b69bd055086f8088d40f3d1d4a).

**Cyfrin:** Verified.

## [M-13] `Prompt::finalized Answer` is never set
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** When a game creator reveal a question the session manager checks the hash previously created and calls `revealQuestion` in the strategies. The strategy decodes  the `Prompt` and sets it in `revealedQuestions[questionId]`. Each `Prompt` struct has its own `finalizedAnswer`:
```solidity
struct Prompt {
        address sessionManager;
        uint256 gameId;
        string questionText;
        uint256 reactionDeadline;
        string finalizedAnswer;
        string[] media;
        string[] choices;
    }
```

After all votes are revealed the final answer has to be set in the `revealedQuestions[questionId].finalizedAnswer`. The problem is that no strategies are exposing a function to set this value.

**Impact:** `Prompt::finalizedAnswer` is never set after the answers are revealed; it appears to not be used at all.

**Recommended Mitigation:** Either set or remove `Prompt::finalizedAnswer`.

**Majority Games:**
Fixed in commit [581a98d](https://github.com/Engage-Protocol/engage-protocol/commit/581a98d91b0246443f5c51bde665ae3641441fd3).

**Cyfrin:** Verified.

## [M-14] Consider reverting in `Rebasing Library` functions if rounding down to zero occurs
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `RebasingLibrary` has two functions `convertTokensToShares` and `convertSharesToTokens`. If rounding down to zero occurs such that the input is non-zero but the output is zero, consider reverting as it makes little sense to continue processing at that point. For example:

* `convertTokensToShares` should revert if `_tokens > 0 && shares == 0`
* `convertSharesToTokens` should revert if `_shares > 0 && tokens == 0`

**Securitize:** Fixed in commit [60c5f92](https://github.com/securitize-io/dstoken/commit/60c5f92e4312b069d351dd08e745875fd8f60aa5) by adding this check in `convertTokensToShares`. Note that we didn't add it in `convertSharesToTokens` as that is used by functions such as `StandardToken::balanceOf`.

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->

