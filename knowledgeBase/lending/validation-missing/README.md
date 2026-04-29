# lending / validation-missing

- Count: `5`
- Definition: required checks are absent or insufficient before critical state transitions or external calls.

## [Beraborrow][M-11] Infrared Collateral Vault::rebalance() can Do S protocol
- Severity: `Medium`
- Source: [Issue #56](https://github.com/sherlock-audit/2025-01-boyco-judging/issues/56)
- Impact: `dos`

### Detailed Content
- Summary: `InfraredCollateralVault::rebalance()` decreases the sent currency without bounding it to currently unlocked balance.
- Root Cause: validation missing on rebalance amount before subtracting balances that exclude future-emission allocations.
- Attack Path: attacker front-runs admin rebalance with withdrawal in the outgoing token so rebalance consumes too much; later `totalAssets()` unlocked-balance math underflows.
- Impact Detail: protocol-wide DoS because core paths depend on these accounting reads and revert after underflow.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-10] Unenforced `max Fee` and `ttl` in `send Msg`
- Severity: `Medium`
- Source: [Issue #317](https://github.com/sherlock-audit/2025-07-malda-judging/issues/317)
- Impact: `functional-break`

### Detailed Content
- Summary: Everclear netting flow requires `maxFee == 0` and `ttl == 0`, but `EverclearBridge.sendMsg` accepted arbitrary values.
- Root Cause: decoded `IntentParams` are forwarded to `everclearFeeAdapter.newIntent(...)` without protocol-side enforcement of documented invariants.
- Trigger Conditions: rebalancer submits a message with non-zero fee/ttl; message passes existing token/destination checks but violates netting constraints.
- Impact Detail: intent can be routed to unsupported solver pathway or otherwise misprocessed, breaking intended rebalance execution guarantees.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-12] Rebalancer can drain market funds via excessive bridge fees
- Severity: `Medium`
- Source: [Issue #686](https://github.com/sherlock-audit/2025-07-malda-judging/issues/686)
- Impact: `fund-loss`

### Detailed Content
- Summary: semi-trusted `REBALANCER_EOA` can set arbitrarily high `maxFee` in bridge intent payload.
- Root Cause: `Rebalancer.sendMsg` forwards unchecked blob; `EverclearBridge.sendMsg` decodes and relays `maxFee` without protocol max bound.
- Attack Path: extract market liquidity, set amount (e.g. 10 WETH) and extreme `maxFee` (e.g. 9.9 WETH), bridge executes with most value consumed by fees.
- Impact Detail: slow but repeatable permanent fund drain from market pools, violating trust model that rebalancer cannot transfer user value.

### Fix Status
- `Fixed/Resolved in report`

## [Native-V2][M-10] Valid trades fail due to incorrect slippage validation
- Severity: `Medium`
- Source: [Issue #124](https://github.com/sherlock-audit/2025-05-native-smart-contract-v2-judging/issues/124)
- Impact: `functional-break`

### Detailed Content
- Summary: external swap success condition checked output against quoted `buyerTokenAmount` instead of caller-defined minimum.
- Root Cause: `ExternalSwap.externalSwap` used overly strict comparator and ignored `amountOutMinimum` semantics already enforced at router layer.
- Trigger Conditions: market moves slightly between quote and execution; output remains above user min but below original expected amount.
- Impact Detail: economically valid trades revert, causing user-visible routing failures and unnecessary transaction loss.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][H-10] Malicious user can alter `Trade Type` to steal funds
- Severity: `High`
- Source: [Issue #715](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/715)
- Impact: `fund-loss`

### Detailed Content
- Summary: redemption logic assumes exact trade mode constraints, but user-supplied `TradeParams.tradeType` can violate those assumptions.
- Root Cause: missing enforcement that redemption should sell full secondary token balance using exact-in semantics in `_executeRedemptionTrades`.
- Attack Path: attacker crafts trade mode/path (including adapters with flexible calldata) so approval/amount behavior diverges from intended flow and extracts value.
- Impact Detail: direct theft from strategy vault or withdrawal request manager under manipulated redemption execution.

### Fix Status
- `Fixed/Resolved in report`

## Cyfrin Fixed Issues (Merged)
- Count: `10`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Missing nonce validation in signature verification allows transaction replay attacks
- Severity: `Critical`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The `SecuritizeOnRamp::executePreApprovedTransaction` function fails to validate that the nonce provided in the transaction data matches the expected nonce for the investor before executing the transaction. While the function verifies the EIP-712 signature includes the nonce as part of the signed message, it does not check if `txData.nonce` equals the current `noncePerInvestor[txData.senderInvestor]` value. The function only increments the stored nonce after signature verification, allowing old valid signatures to be replayed with their original nonce values.

The current implementation at lines 184-199 in `SecuritizeOnRamp.sol`:
```solidity
function executePreApprovedTransaction(
    bytes memory signature,
    ExecutePreApprovedTransaction calldata txData
) public override whenNotPaused {
    bytes32 digest = hashTx(txData);
    address signer = ECDSA.recover(digest, signature);

    // Check recovered address role
    IDSTrustService trustService = IDSTrustService(dsToken.getDSService(dsToken.TRUST_SERVICE()));
    uint256 signerRole = trustService.getRole(signer);
    if (signerRole != trustService.EXCHANGE() && signerRole != trustService.ISSUER()) {
        revert InvalidEIP712SignatureError();
    }
    noncePerInvestor[txData.senderInvestor] = noncePerInvestor[txData.senderInvestor] + 1;
    Address.functionCall(txData.destination, txData.data);
}
```

This vulnerability allows an attacker to replay any previously valid signed transaction, potentially executing multiple subscriptions or other operations with the same signature.

**Impact:** Attackers can replay previously valid EIP-712 signed transactions to execute duplicate subscription operations, leading to unintended token swaps and accounting failure.

**Proof Of Concept:**
Add the PoC below to `on-ramp.test.ts`.
```typescript
  it('Should allow replay attack - nonce not validated properly', async function () {
      // Setup initial balances and approvals for multiple transactions
      await usdcMock.mint(unknownWallet, 2e6); // Mint 2M USDC for two transactions
      await dsTokenMock.issueTokens(assetProviderWallet, 2e6); // Issue 2e6 DS tokens

      const liquidityFromInvestor = usdcMock.connect(unknownWallet) as Contract;
      await liquidityFromInvestor.approve(onRamp, 2e6); // Approve 2 USDC

      const dsTokenFromAssetProviderWallet = dsTokenMock.connect(assetProviderWallet) as Contract;
      await dsTokenFromAssetProviderWallet.approve(assetProvider, 2e6); // Approve 2e6 DS tokens

      const calculatedDSTokenAmount = await onRamp.calculateDsTokenAmount(1e6);

      // Create first transaction with nonce 0
      const subscribeParams = [
          '1',
          await unknownWallet.getAddress(),
          'US',
          [],
          [],
          [],
          980000,
          1e6,
          blockNumber + 10,
          HASH,
      ];
      const txData = await buildTypedData(onRamp, subscribeParams);
      const signature = await eip712OnRamp(eip712Signer, await onRamp.getAddress(), txData);

      // Verify initial nonce is 0
      expect(await onRamp.nonceByInvestor('1')).to.equal(0);

      // Execute first transaction successfully
      await expect(onRamp.executePreApprovedTransaction(signature, txData))
          .emit(onRamp, 'Swap')
          .withArgs(onRamp, calculatedDSTokenAmount, 1e6, unknownWallet);

      // Verify nonce is now 1 after first transaction
      expect(await onRamp.nonceByInvestor('1')).to.equal(1);

      // Verify first transaction effects
      expect(await dsTokenMock.balanceOf(unknownWallet)).to.equal(calculatedDSTokenAmount);
      expect(await usdcMock.balanceOf(unknownWallet)).to.equal(1e6); // 1e6 remaining

      // VULNERABILITY: Replay the same transaction with the same signature and nonce 0
      // This should fail but doesn't because nonce validation is missing
      await expect(onRamp.executePreApprovedTransaction(signature, txData))
          .emit(onRamp, 'Swap')
          .withArgs(onRamp, calculatedDSTokenAmount, 1e6, unknownWallet);

      // Verify the replay attack succeeded - investor got double the tokens
      expect(await dsTokenMock.balanceOf(unknownWallet)).to.equal(calculatedDSTokenAmount * 2n);
      expect(await usdcMock.balanceOf(unknownWallet)).to.equal(0); // All USDC spent

      // Verify nonce was incremented again (now 2) even though we replayed nonce 0
      expect(await onRamp.nonceByInvestor('1')).to.equal(2);
  });
```
**Recommended Mitigation:** Add nonce validation before executing the transaction to ensure the provided nonce matches the expected nonce for the investor:

```diff
function executePreApprovedTransaction(
    bytes memory signature,
    ExecutePreApprovedTransaction calldata txData
) public override whenNotPaused {
+   // Validate nonce matches expected value
+   if (txData.nonce != noncePerInvestor[txData.senderInvestor]) {
+       revert InvalidEIP712SignatureError();
+   }
+
    bytes32 digest = hashTx(txData);
    address signer = ECDSA.recover(digest, signature);

    // Check recovered address role
    IDSTrustService trustService = IDSTrustService(dsToken.getDSService(dsToken.TRUST_SERVICE()));
    uint256 signerRole = trustService.getRole(signer);
    if (signerRole != trustService.EXCHANGE() && signerRole != trustService.ISSUER()) {
        revert InvalidEIP712SignatureError();
    }
    noncePerInvestor[txData.senderInvestor] = noncePerInvestor[txData.senderInvestor] + 1;
    Address.functionCall(txData.destination, txData.data);
}
```

**Securitize:** Fixed in commit [65179b](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/65179bcf41ed859106069dcaa751f5a2cec3038e).

**Cyfrin:** Verified.

\clearpage

## [M-2] Optimize `_get Staker Vaults` to Avoid Redundant External Calls to `active Balance Of At`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `Rewards::_getStakerVaults` function performs two passes over the vault array to filter vaults with non-zero balances, which doubles the number of external calls to `IVaultTokenized.activeBalanceOfAt`.

```solidity
function _getStakerVaults(address staker, uint48 epoch) internal view returns (address[] memory) {
        address[] memory vaults = middlewareVaultManager.getVaults(epoch);
        uint48 epochStart = l1Middleware.getEpochStartTs(epoch);

        uint256 count = 0;

        // First pass: Count non-zero balance vaults
        for (uint256 i = 0; i < vaults.length; i++) {
            uint256 balance = IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0));
            if (balance > 0) {
                count++;
            }
        }

        // Create a new array with the exact number of valid vaults
        address[] memory validVaults = new address[](count);
        uint256 index = 0;

        // Second pass: Populate the new array
        for (uint256 i = 0; i < vaults.length; i++) {
            uint256 balance = IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0));
            if (balance > 0) {
                validVaults[index] = vaults[i];
                index++;
            }
        }

        return validVaults;
    }
```

**Recommended Mitigation:** Make the following change to the `_getStakerVaults`:

```diff
function _getStakerVaults(address staker, uint48 epoch) internal view returns (address[] memory) {
    address[] memory vaults = middlewareVaultManager.getVaults(epoch);
    uint48 epochStart = l1Middleware.getEpochStartTs(epoch);
+   address[] memory tempVaults = new address[](vaults.length); // Temporary oversized array
    uint256 count = 0;

-   // First pass: Count non-zero balance vaults
-   for (uint256 i = 0; i < vaults.length; i++) {
-       uint256 balance = IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0));
-       if (balance > 0) {
-           count++;
-       }
-   }
-
-   // Create a new array with the exact number of valid vaults
+   // Single pass: Collect valid vaults
+   for (uint256 i = 0; i < vaults.length;) {
+       if (IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0)) > 0) {
+           tempVaults[count] = vaults[i];
+           count++;
+       }
+       unchecked { i++; }
+   }
+
+   // Copy to correctly sized array
    address[] memory validVaults = new address[](count);
-   uint256 index = 0;
-
-   // Second pass: Populate the new array
-   for (uint256 i = 0; i < vaults.length; i++) {
-       uint256 balance = IVaultTokenized(vaults[i]).activeBalanceOfAt(staker, epochStart, new bytes(0));
-       if (balance > 0) {
-           validVaults[index] = vaults[i];
-           index++;
-       }
+   for (uint256 i = 0; i < count;) {
+       validVaults[i] = tempVaults[i];
+       unchecked { i++; }
    }

    return validVaults;
}
```

**Suzaku:**
Fixed in commit [2fb0daf](https://github.com/suzaku-network/suzaku-core/commit/2fb0dafd684eeaf11b177602c5047d1e6ce2d715).

**Cyfrin:** Verified.

## [M-3] Allow users to increment their nonce to void their signatures
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Currently users are unable to void their signatures by incrementing their nonce, since `NoncesUpgradeable::_useNonce` is `internal` and only called during actions which verify user signatures.

A user may want to invalidate a previous signature to prevent it from being used but is unable to.

**Impact:** Users are unable to invalidate previous signatures before they are used.

**Recommended Mitigation:** Expose `NoncesUpgradeable::_useNonce` via a `public` function that allows users to increment their own nonce.

**CryptoArt:**
Fixed in commit [cf82aeb](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/cf82aeb30d6a262cde51897f52c302be995d0202).

**Cyfrin:** Verified.

## [M-4] Anyone can sell anyone else's market seat
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In the `sell_market_seat` function the `check_signer` parameter is incorrectly set to false, allowing any user to force-sell another user's market seat without proper authorization.
```rust
let mut client_state = ClientPrimaryState::new_for_perp(
    program_id,
    client_primary_acc,
    &ctx,
    signer,
    system_program,
    0,
    false,  // alloc = false (correct)
    false,  // @audit why false? can I supply others's
)?;
```
`new_for_perp` calls `ClientPrimaryAccountHeader::from_account_info_unchecked` since we have set the `check_signer` flag to false, the `from_account_info_unchecked` only makes sure that the account `signer` is signer, however it does not make sure that the signer account is indeed the one `wallet_address` stored in  `ClientPrimaryAccountHeader`.. which means anyone could pass a anyone's valid `ClientPrimaryState` and sell their seat without consent.

Attack Scenario
- Attacker finds any `client_primary_acc` with a market seat
- Attacker call `sell_market_seat` with their own wallet as `signer` and Victim's `client_primary_acc`
- No validation occurs to check if the signer owns the client account
- Victim's market seat is sold and funds go to the victim's account, and the attacker closed victim's position without consent

**Impact:** Any user can close any other user's seats

**Recommended Mitigation:** Pass the `is_signer` flag set to true like we have done in `buy_market_seat`
```rust
// ...existing code...
let mut client_state = ClientPrimaryState::new_for_perp(
    program_id,
    client_primary_acc,
    &ctx,
    signer,
    system_program,
    0,
    false,
    true,   // check_signer = true
)?;
// ...existing code...
```
**Deriverse**
Fixed in commit: [9a5678](https://github.com/deriverse/protocol-v1/commit/9a56789cd5f5b479022da7c4da97f8ef1ee6aaf8)

**Cyfrin:** Verified.

## [M-5] Precompute `base Slot` in `Atomic Batcher::_get Nonce Slot`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `AtomicBatcher::_getNonceSlot` computes the ERC-7201 namespace base slot at runtime each time it is called:
```solidity
function _getNonceSlot(address account) private pure returns (bytes32) {
    bytes32 namespaceHash = keccak256(bytes(_NAMESPACE));
    bytes32 baseSlot = keccak256(abi.encode(uint256(namespaceHash) - 1)) & ~bytes32(uint256(0xff)); // @audit can be pre-computed
    return keccak256(abi.encode(account, uint256(baseSlot)));
}
```
Since the namespace is constant, the derived `baseSlot` can be precomputed and stored as a `bytes32` constant:
```solidity
// keccak256(abi.encode(uint256(keccak256("accountable.atomicbatcher.nonce.v1")) - 1)) & ~bytes32(uint256(0xff))
bytes32 private constant NONCE_BASE_SLOT = 0xa68386067ee8ee669468449acf0ad3e2ae0d09e4d99f78eaa329c6681c06b900;
```

**Accountable:** Fixed in commit [`fce94d2`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/fce94d2c67b3937ea1106f66138dbff7118227d8)

**Cyfrin:** Verified.

## [M-6] Use named mapping parameters to explicitly denote the purpose of keys and values
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Use named mapping parameters to explicitly denote the purpose of keys and values:
```solidity
off-ramp/BaseOffRamp.sol
43:    mapping(string => bool) public restrictedCountries;

off-ramp/CountryValidator.sol
26:        mapping(string => bool) storage _restrictedCountries

on-ramp/SecuritizeOnRamp.sol
41:    mapping(string => uint256) internal noncePerInvestor;
```

**Securitize:** Fixed in commit [ef5367e](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/ef5367e1db99cb7c72239f5702c817390d23236c).

**Cyfrin:** Verified.

## [M-7] Assembly blocks could benefit from `"memory-safe"` annotation
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** When hashing request data in [`Spin::_hashParticipation`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L383-L409) and [`Spin::_hashClaim`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L411-L438), inline assembly is used to efficiently compute the hash:
```solidity
assembly {
    let mPtr := mload(0x40)
    mstore(
        mPtr,
        0x4635ca970da82693e235d3cdaa3678d42c6824330c48b4135f080d655e54da78 // keccak256("ClaimRequest(address user,uint256 expirationTimestamp,uint64 nonce,uint32 prizeId)")
    )
    mstore(add(mPtr, 0x20), _user)
    mstore(add(mPtr, 0x40), _expirationTimestamp)
    mstore(add(mPtr, 0x60), _nonce)
    mstore(add(mPtr, 0x80), _prizeId)
    claimHash := keccak256(mPtr, 0xa0)
}
```

To improve compiler optimizations, consider adding a [`memory-safe`](https://docs.soliditylang.org/en/latest/assembly.html#memory-safety) annotation to the assembly block:

```diff
+ assembly ("memory-safe") {
```

Since the assembly block only accesses memory after the free memory pointer (`0x40`), this annotation poses no risk and can allow the Solidity compiler to apply additional optimizations, improving gas efficiency.

**Linea:** Fixed in commit [`b4aaffc`](https://github.com/Consensys/linea-hub/commit/b4aaffc43e496b085e54ef2b08397fcb3c310e68)

**Cyfrin:** Verified.

\clearpage

## [M-8] Rounding errors in boosted probability calculation can cause guaranteed wins to fail
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** The Linea SpinGame includes a boosting feature that allows the protocol to increase a specific user's chance of winning. However, this mechanism introduces the possibility of a user's total winning probability exceeding 100%, as the boosted probabilities can sum to a value greater than 100%. To address this, the contract normalizes the total boosted probability in [`Spin::_fulfillRandomness`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L538-L557):

```solidity
// Apply boost on the sum of totalProbabilities.
uint256 boostedTotalProbabilities = totalProbabilities * userBoost / BASE_POINT;

// If boostedTotalProbabilities exceeds 100% we have to increase the winning threshold so it stays in bound.
//
// Example:
//   PrizeA probability: 50%
//   PrizeB probability: 30%
//   User boost: 1.5x
//   boostedPrizeAProbability: 75%
//   boostedPrizeBProbability: 45%
//
//   We now have a total of 120% totalBoostedProbability so we need to increase winning threshold by boostedTotalProbabilities to BASE_POINT ratio.
//
//   winningThreshold = winningThreshold * 12_000 / 10_000
if (boostedTotalProbabilities > BASE_POINT) {
    winningThreshold =
        (winningThreshold * boostedTotalProbabilities) /
        BASE_POINT;
}
```

Later in [`Spin::_fulfillRandomness`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L569-L589), each prize probability is independently scaled when checking if the user has won:

```solidity
// Apply boost on a single prize probability.
uint256 boostedPrizeProbability = prizeProbability * userBoost / BASE_POINT;

unchecked {
    cumulativeProbability += boostedPrizeProbability;
}

if (winningThreshold < cumulativeProbability) {
    selectedPrizeId = localPrizeIds[i];

    // ... win
    break;
}
```

The issue arises from the probability calculation:

```solidity
uint256 boostedPrizeProbability = prize.probability +
    ((prize.probability * userBoost) / BASE_POINT);
```

Due to this calculation, the final `cumulativeProbability` can be lower than `boostedTotalProbabilities`, leading to a scenario where a user who should be guaranteed a win might still lose due to rounding errors.

**Impact:** A user who theoretically has a 100% chance of winning can still lose. While this is an unlikely edge case, it would be highly problematic for the unlucky user who, despite the math suggesting they are guaranteed a win, does not receive a prize due to numerical precision issues.

**Proof of Concept:** Consider the following example:

- There are three prizes, each with a 30% probability of being won.
- A user receives a 133% probability boost.

Calculating the boosted probabilities:

```solidity
boostedTotalProbabilities = 0.9e8*133_333_333/1e8 = 119_999_999
boostedPrizeProbability = 0.3e8*133_333_333/1e8 = 39_999_999
```
and
```
3*39_999_999 = 119_999_997
```

In the worst case, the user could get:

```
winningThreshold = 99_999_999
```

Applying the threshold adjustment:

```solidity
if (boostedTotalProbabilities > BASE_POINT) {
    winningThreshold =
        (winningThreshold * boostedTotalProbabilities) /
        BASE_POINT;
}
```

This results in:

```
winningThreshold = 99_999_999 * 119_999_999 / 1e8 = 119_999_997
```

Since `winningThreshold < cumulativeProbability` is the condition for winning, and:

```
119_999_997 < 119_999_997  // (false)
```

The condition fails, meaning the user loses, even though they were supposed to be guaranteed a win. This issue is caused by the rounding errors in scaling probabilities.


**Recommended Mitigation:** Consider ensuring that in the last iteration of the loop, if `boostedTotalProbabilities >= BASE_POINT`, the user is guaranteed a win:

```diff
- if (winningThreshold < cumulativeProbability) {
+ if (winningThreshold < cumulativeProbability ||
+     boostedTotalProbabilities >= BASE_POINT && i == prizeLen - 1 // last iteration and win is guaranteed
+ ) {
      selectedPrizeID = prizeIds[i];
```

This change slightly favors the last prize in the list in extremely rare cases, but given that this situation is already highly improbable, this trade-off is reasonable.

**Linea:** Fixed in commit [`b32e038`](https://github.com/Consensys/linea-hub/commit/b32e038bba336d1ad6dddbdb972de8cafbbb2c1a)

**Cyfrin:** Verified.

## [M-9] Vester template misconfiguration can potentially block token claims
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The `WorldLibertyFinancialVester` contract can make user tokens temporarily inaccessible when template `capPerUser` values don't sum to the user's total allocation.

Users transfer their full allocation to the vester during activation, but can only claim back the portion covered by template caps until the owner adds additional templates or modifies existing ones.

The contract's design allows for:

- User allocation can be any amount (set in `_activateVest`)
- Template caps define maximum unlockable amounts per user
- No validation ensures template caps cover the full user allocation

If the contract owner incorrectly configures/modifies the template user cap, users could potentially have a portion of their tokens unclaimable inside the Vester contract.

```solidity
function _unlockedTotal(uint8 _category, uint112 _allocation) internal view returns (uint256) {
    uint256 totalUnlocked = 0;
    uint256 remainingCap = _allocation;  // Start with full allocation

    for (uint8 i; i < count; ) {
        uint256 segmentCap = t.capPerUser < remainingCap ? t.capPerUser : remainingCap;
        uint256 unlocked = _segmentUnlocked(t, segmentCap);
        totalUnlocked += unlocked;

        // @audit remainingCap reduced by template cap, not allocation
        remainingCap -= segmentCap;

        unchecked { ++i; }
    }

    // @audit Any remaining allocation is ignored and becomes inaccessible
    return totalUnlocked;  // Missing: + remainingCap
}
```

**Impact:** Misconfigured templates can lead to unclaimable tokens for users even after completing full vesting. Users cannot claim portion of their tokens until template coverage is increased.

**Recommended Mitigation:** Consider documenting clearly that template caps should cover expected user allocations. Add both inline and interface comments that will prevent misconfiguration scenarios by admins. Alternatively consider making it mandatory to add a `remainder` template as the last template for every category.


**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/interfaces/IWorldLibertyFinancialVester.sol#L27)

**Cyfrin:** Verified. Moved to percentage allocation from a fixed cap per user.

## [M-10] `Perpetual Bond.epoch` not updated after yield distribution
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In [`PerpetualBond::distributeBondYield`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L215-L241) the caller is supposed to provide a `nonce` that matches [`epoch + 1`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L220-L221):
```solidity
function distributeBondYield(uint256 _yieldAmount, uint256 nonce) external notPaused onlyRewarder {
    require(nonce == epoch + 1, "!epoch");
```
However, `epoch` is never incremented afterwards, consider incrementing `epoch`.

**YieldFi:** Fixed in commit [`5c1f0e7`](https://github.com/YieldFiLabs/contracts/commit/5c1f0e7a805caf1d0fddbc5a15c8b6797a424467)

**Cyfrin:** Verified. `epoch` now is incremented with the new `nonce`.

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-19] Missing zero-address validation for burner address during initialization can break slashing
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The VaultTokenized contract's initialization procedure fails to validate that the burner parameter is a non-zero address. However, the `onSlash` function uses SafeERC20's `safeTransfer` to send tokens to this address, which will revert for most ERC20 implementations if the recipient is address(0).

```solidity
// In _initialize:
vs.burner = params.burner; // No validation that params.burner != address(0)

// In onSlash:
if (slashedAmount > 0) {
    IERC20(vs.collateral).safeTransfer(vs.burner, slashedAmount); // Will revert if vs.burner is address(0)
}
```
While other critical parameters like collateral are validated against the zero address, the burner parameter lacks this check despite its importance in the slashing flow.

**Impact:** Setting burner to `address(0)` would break a core security function (slashing)

**Recommended Mitigation:** Consider adding a zero-address validation for the burner parameter during initialization.

**Suzaku:**
Fixed in commit [4683ab8](https://github.com/suzaku-network/suzaku-core/pull/155/commits/4683ab82c40103fd6af5a7d2447e5be211e93f20).

**Cyfrin:** Verified.
