# access-control (reorganized and merged, all issues sequentially)

> Covers privileged checks, roles, signature/permit mechanisms, and `msg.sender` verification bypasses (or misconfiguration).  
Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

### Issue 1: Lack of Access Control Enabling Unauthorized Credential Issuance and Revocation

**Severity:** 🔴 Critical  
**Source:** `HackenPDFTXT/RYT-2.txt`

**Description:**  
The `DIDContract` manages decentralized identity documents and issues two credential types: simple credentials and Soulbound Token (SBT) credentials. Its critical lifecycle functions (`issueCredential()`, `issueSBTCredential()`, `revokeSBTCredential()`) lack access control: any address can issue or revoke credentials. The wrapper for `mintCredential()` in `DIDContract` has no issuer check, bypassing the expected authorization model; likewise, anyone can call `revokeSBTCredential()`.

**Impact:**  
All credential trust is lost—attackers can issue fake credentials or revoke SBTs of legitimate users at will, manipulating user histories, destroying trust and reliability.

**Recommended Mitigation:**  
Add an `authorizedIssuers` mapping and admin setter, plus an `onlyAuthorizedIssuer()` modifier, and apply it to all sensitive functions. Only whitelisted addresses should issue or revoke credentials.

---

### Issue 2: Blacklisted Token Recipient Permanently Blocks FIFO Forced Withdrawals

**Severity:** 🟠 High  
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**  
The protocol uses a FIFO forced withdrawal queue. A transfer to a blacklisted recipient at the head reverts, permanently blocking the entire queue, as processing only advances after each successful transfer; there is no way to skip or mark failed requests.

**Impact:**  
All subsequent forced withdrawals are blocked if the head is blacklisted. The escape-hatch path ceases to function if a blacklisted address is first.

**Recommended Mitigation:**  
Wrap transfer calls in try-catch, advance pointer regardless of transfer success, or switch to a pull pattern with user claims.

---

### Issue 3: Missing Nonce Validation in Signature Verification Allows Transaction Replay Attacks

**Severity:** 🔴 Critical  
**Source:** `cyfrin/bridge.md`

**Description:**  
`SecuritizeOnRamp::executePreApprovedTransaction` validates the EIP-712 signature but never checks `txData.nonce == noncePerInvestor[txData.senderInvestor]` before execution—only increments nonce post-verification, which allows replays of already used signatures (with the old nonce).

**Impact:**  
Attackers can replay valid signed transactions, causing multiple unintended token swaps/subscriptions and draining investor funds.

**Recommended Mitigation:**  
At function entry, revert if the nonce does not match the stored on-chain value.

---

### Issue 4: Incomplete Blacklist Enforcement in transferFrom Allows Blacklisted Callers to Bypass Transfer Restrictions

**Severity:** 🟠 High  
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**  
Blacklist checks in `_enforceTxLimit` only cover `sender`, not `msg.sender` (spender) or `recipient`. Therefore, blacklisted addresses can use allowance and act as recipient.

**Impact:**  
Blacklisted actors can participate in transfers via allowance or as recipient, making the restriction ineffective.

**Recommended Mitigation:**  
Checks must cover `sender`, `recipient`, and `msg.sender` in all transfer flows.

---

### Issue 5: After the Upgrade Permissionless Attacker Can Fully Drain the L1 TokenBridge of ERC20 Tokens Currently Valued Around $29M USD

**Severity:** 🔴 Critical  
**Source:** `cyfrin/upgrade.md`

**Description:**  
A storage slot change made `TokenBridge` believe it was not initialized post-upgrade. Any attacker can call `initialize` and become admin, set themselves as message service controller, and drain all tokens.

**Impact:**  
Full loss of all L1 bridge assets—unrecoverable asset theft.

**Recommended Mitigation:**  
Ensure correct inheritance from `Initializable` to place the slot properly and protect reinitializer logic.

---

### Issue 6: LivenessRecovery::setLivenessRecoveryOperator Will Emit Misleading Event When Role Is Not Granted

**Severity:** 🔴 Critical  
**Source:** `cyfrin/upgrade.md`

**Description:**  
Calling `_grantRole` in `setLivenessRecoveryOperator` emits the event regardless of whether the role was newly granted or not; thus, a duplicate call causes a misleading `LivenessRecoveryOperatorRoleGranted` log even if no state change.

**Impact:**  
Off-chain and audit systems are misled, event history diverges from real state, causing operational and security risk.

**Recommended Mitigation:**  
Only emit the event if the returned boolean is `true`, i.e., when the role is actually newly granted.

---

### Issue 7: EntryPoint Not Included in User Operation Hash Creates the Possibility of Replay Attacks

**Severity:** 🟠 High  
**Source:** `cyfrin/DelegationFramework1.md`

**Description:**  
User operation hash calculation omits the EntryPoint address; therefore, signatures under one EntryPoint deployment are valid on others, enabling replay.

**Impact:**  
Replay attacks are enabled after delegator contract upgrades to a new EntryPoint—attackers can repeat prior operations.

**Recommended Mitigation:**  
Use the provided EntryPoint's `userOpHash` in signature checks to ensure domain separation.

---

### Issue 8: Rewards Drain due to Invalid Last Claimed Period Update

**Severity:** 🔴 Critical  
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**  
`_claimRewards` writes (0,0) as `lastClaimedPeriod` when `_claimableDelegationPeriods` returns it (indicating nothing claimable remaining), unlocking the chance to claim all rewards repeatedly.

**Impact:**  
Attackers can reset reward pointers and drain the entire pool indefinitely.

**Recommended Mitigation:**  
Revert if claimable period is (0,0), i.e., do not write or allow such updates.

---

### Issue 9: Security Mechanisms Inoperative due to OpenZeppelin v5 Hook Incompatibility

**Severity:** 🟠 High  
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**  
The contract overrides `_beforeTokenTransfer`, but OpenZeppelin v5 ERC20 no longer calls this hook (uses `_update`). Thus, pausability and blacklist checks are dead code and never enforced.

**Impact:**  
Critical controls are disabled—tokens can never be paused or prevented from transfer, including by blocklisted addresses.

**Recommended Mitigation:**  
Override `_update` instead, and implement critical checks there.

---

### Issue 10: Winner Selection Ignores Assigned Payout Positions Due To A Faulty If Condition

**Severity:** 🟠 High  
**Source:** `HackenPDFTXT/RYT.txt`

**Description:**  
In `distributeFunds()`, the winner selection logic accidentally always picks the first unpaid member due to a short-circuit OR condition, ignoring the payout ordering mapping.

**Impact:**  
Payout order configuration has no effect—always the first unpaid address is chosen.

**Recommended Mitigation:**  
Remove the `winner == address(0)` short-circuit; always require payout position match.

---
