# delegate call - 已修復 Medium/High Issues（完整版）

- 篩選：`Severity in {Medium, High}` 且 `Status = Fixed`
- 說明：本版為完整敘述，不做刪節號截斷
- 筆數：2

## F-2026-14977 - Token Pricing Assumes All Payment Tokens HaveSame Decimals And Price
- 嚴重度：High
- Report source：Fabstir.pdf

### 問題內容（完整）
Pricing logic in the NodeRegistryWithModelsUpgradeable contract treats multipleERC20 payment tokens as if they share same “stable” price and, inpractice, one decimals convention. When no token-specific price is set,the same fallback value is used for every accepted token. The contractnever adjusts for token decimals or distinct economic value, so minimum-price checks and session economics can be wrong for any token thatdiffers in decimals or price from the “stable” assumption. function `getNodePricing(address operator, address token)` external view return s (uint256) { if (token == `address(0)`) { return nodes[operator].minPricePerTokenNative; } else { uint256 customPrice = customTokenPricing[operator][token]; if (customPrice > 0) { return customPrice; } return nodes[operator].minPricePerTokenStable; // same for `ALL` token s } } For any token != `address(0)` without a custom price, the return value isalways minPricePerTokenStable. The token parameter is only consideredwhen customTokenPricing[operator][token] > 0. Otherwise the protocolassumes all such tokens have the same decimals and the same price. function `getModelPricing(address operator, bytes32 modelId, address token)` ex ternal view returns (uint256) { // … if (token == `address(0)`) { uint256 modelPrice = modelPricingNative[operator][modelId]; return modelPrice > 0 ? modelPrice : nodes[operator].minPricePerToken Native; } else { uint256 modelPrice = modelPricingStable[operator][modelId]; nodes[operator].minPricePerToken Stable; } } 16 For any non-native token, the returned price depends only on “stable”model/node pricing. The token argument is ignored; there is no per-tokenmodel pricing and no use of customTokenPricing. So for model sessions, allERC20s are assumed to have the same decimals and price as this single“stable” value. Impact The same raw value is used for every token in the fallback path.Example: getNodePricing returns the same number for a 6-decimal andan 18-decimal token: function `createSessionJobWithToken(…)` external nonReentrant whenNotPaused r eturns (uint256 jobId) { // … uint256 hostMinPrice = `nodeRegistry.getNodePricing(host, token)`; `require(pricePerToken >= hostMinPrice, "Price below host minimum")`; } Without custom pricing, every token is treated as having the same value.Users can pay in a cheaper or riskier token while satisfying the single“stable” minimum, or be over-constrained for a stronger collateral token.Correct behavior for multiple tokens requires setting customTokenPricing (and/or future per-token model pricing) for every token. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#]src/NodeRegistryWithModelsUpgradeable.sol[https://github.com/Fabstir/fabstir-compute-contracts#] Status: Fixed

### 修補方式（建議）
Consider avoiding usage of fallback values. Consider reverting if pricing inunsupported token is requested. Require node operator to selectively setprice for each of the supported tokens. Resolution: Fixed in f614355: NodeRegistryWithModelsUpgradeable now enforces explicit per-tokenmodel pricing through modelTokenPricing[operator][modelId][token], and getModelPricing reverts on missing entries via `require(price > 0, "No model pricing")`. function `getModelPricing(address operator, bytes32 modelId, address token)` ex ternal view returns (uint256) { if (nodes[operator].operator == `address(0)`) return 0; uint256 price = modelTokenPricing[operator][modelId][token]; `require(price > 0, "No model pricing")`; return price; } Shared fallback paths based on a single stable value were removed fromactive pricing flow, and model session creation now depends on explicittoken-specific configuration.

### 修補方式（實際）
Fixed in f614355: NodeRegistryWithModelsUpgradeable now enforces explicit per-tokenmodel pricing through modelTokenPricing[operator][modelId][token], and getModelPricing reverts on missing entries via `require(price > 0, "No model pricing")`. function `getModelPricing(address operator, bytes32 modelId, address token)` ex ternal view returns (uint256) { if (nodes[operator].operator == `address(0)`) return 0; uint256 price = modelTokenPricing[operator][modelId][token]; `require(price > 0, "No model pricing")`; return price; } Shared fallback paths based on a single stable value were removed fromactive pricing flow, and model session creation now depends on explicittoken-specific configuration.

## F-2026-15254 - Use of IERC20.transfer() Instead ofSafeERC20.safeTransfer() in Refund Path
- 嚴重度：High
- Report source：Fabstir.pdf

### 問題內容（完整）
The `_settleSessionPayments` function uses a raw IERC20.transfer call inside a try/catch block for ERC20 refunds, whereas all other ERC20 transferoperations across the codebase consistently use SafeERC20.safeTransfer. try `IERC20(session.paymentToken)`.`transfer(session.depositor, userRefund)` retu rns (bool success) { if (!success) { userDepositsToken[session.depositor][session.paymentToken] += userRef und; emit `RefundCreditedToDeposit(jobId, session.depositor, userRefund, se ssion.paymentToken)`; } } catch { userDepositsToken[session.depositor][session.paymentToken] += userRefund; } Tokens that do not return a value on `transfer()` (e.g. `USDT` on Ethereum)cause the `ABI` decoding to fail when the compiler attempts to decodeempty returndata into a bool. Per the Solidity specification, "errors duringthe decoding of the return data inside a try/catch are not caught" — thedecoding failure occurs in the caller's execution context, not within theexternal call, so the catch block is never entered. Instead, the entiretransaction reverts, rolling back all state changes including the sessionstatus update. As a result, any session using a no-return token becomes impossible tofinalize whenever a non-zero depositor refund exists. `completeSessionJob()` reverts for both the depositor and the host, and `triggerSessionTimeout()` alsoreverts since it calls the same settlement function. Deposited funds arepermanently locked in the contract with no recovery mechanism. Evenwhen the host has submitted legitimate proofs and earned partial payment,the host cannot collect their earnings either, because the settlementreverts before the host payment can be committed. Found in commit: f614355. Assets: `src/JobMarketplaceWithModelsUpgradeable.sol`[https://github.com/Fabstir/fabstir-compute-contracts#] 20 Status: Fixed

### 修補方式（建議）
Replace the raw `IERC20.transfer()` call with `SafeERC20.safeTransfer()` insidethe try/catch block. `safeTransfer()` handles tokens with no return value bytreating empty returndata as success, while still reverting on actual transferfailures. This ensures the catch block is only entered when the transfergenuinely fails, making the fallback credit to userDepositsToken safe andcorrect. Resolution: The raw IERC20.transfer call has been replaced with a low-level call thatcorrectly handles tokens with no return value by treating empty returndataas success, while falling back to crediting the depositor's internal balancewhen the transfer fails for any reason: // F202615254: Low-level call handles non-returning tokens (`USDT`) (bool callOk, bytes memory ret) = `session.paymentToken.call( abi.encodeCall(IERC20.transfer, (session.depositor, userRefund)`) ); if (!(callOk && (ret.length == 0 || `abi.decode(ret, (bool)`)))) { userDepositsToken[session.depositor][session.paymentToken] += userRefund ; emit `RefundCreditedToDeposit(jobId, session.depositor, userRefund, sessi on.paymentToken)`; } Revised commit: df1f2e4.

### 修補方式（實際）
The raw IERC20.transfer call has been replaced with a low-level call thatcorrectly handles tokens with no return value by treating empty returndataas success, while falling back to crediting the depositor's internal balancewhen the transfer fails for any reason: // F202615254: Low-level call handles non-returning tokens (`USDT`) (bool callOk, bytes memory ret) = `session.paymentToken.call( abi.encodeCall(IERC20.transfer, (session.depositor, userRefund)`) ); if (!(callOk && (ret.length == 0 || `abi.decode(ret, (bool)`)))) { userDepositsToken[session.depositor][session.paymentToken] += userRefund ; emit `RefundCreditedToDeposit(jobId, session.depositor, userRefund, sessi on.paymentToken)`; } Revised commit: df1f2e4.

## Cyfrin Fixed Issues (Merged)
- Count: `5`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] To prevent duplicate ids in `_batchBurn`, enforce ascending order instead of nested `for` loops
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** In `_batchBurn` to prevent duplicate ids, instead of using nested `for` loops it is more efficient to [enforce ascending order of ids](https://x.com/DevDacian/status/1734885772829045205) using only 1 `for` loop.

Additionally, the duplicate id check can be completely removed since if there is a duplicate id the second `burn` call will revert. For example this test added to `test/unit/BurnOperationsTest.t.sol`:
```solidity
    function test_DoubleBurn() public {
        // Mint a token to user1
        mintNFT(user1, TOKEN_ID, TOKEN_PRICE, TOKEN_PRICE);
        testAssertions.assertTokenOwnership(nft, TOKEN_ID, user1);

        // First burn should succeed
        vm.prank(user1);
        nft.burn(TOKEN_ID);

        // Second burn should revert since token no longer exists
        vm.prank(user1);
        // vm.expectRevert();
        nft.burn(TOKEN_ID);
    }
```

Results in:
```solidity
    ├─ [4294] TransparentUpgradeableProxy::fallback(1)
    │   ├─ [3940] CryptoartNFT::burn(1) [delegatecall]
    │   │   └─ ← [Revert] ERC721NonexistentToken(1)
    │   └─ ← [Revert] ERC721NonexistentToken(1)
    └─ ← [Revert] ERC721NonexistentToken(1)
```

**CryptoArt:**
Fixed in commit [3c39fb8](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/3c39fb86db6b92424a0cf55c315d0d6284c267bf).

**Cyfrin:** Verified.

\clearpage

## [M-2] Deploy script `UpdateParallelizer.ts` does not handle facet removal case
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** When upgrading the script finds all the selectors that should be _added_ (`FaceCutAction.Add`) or _replaced_ (`Replace`) but the
case for `Remove` is missing.  This could lead to deleted selectors being present after an upgrade. This would mean that users could still call these endpoints and have them `delegatecall` to the old implementation, which may not be what was intended.

**Impact:** The impact depends entirely on what selectors would not be removed.

**Parallel:** Fixed in commit [c340795](https://github.com/parallel-protocol/parallel-parallelizer/commit/c340795ad0ecc071ff202447d67540e9943f15fd).

**Cyfrin:** Verified. `UpdateParallelizer.ts` now accounts for the case when removing selectors from the old facet.

## [M-3] `BasisTradeTailor` is ERC-165 non compliant
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** The `BasisTradeTailor` contract inherits from and implements the `ITailor` interface. According to the ERC-165 standard, the `supportsInterface` function should return `true` when queried with the interface ID of `ITailor` and `IERC1822Proxiable` (coming from `UUPSUpgradeable`).

However, the current implementation of `supportsInterface` only calls `super.supportsInterface(interfaceId)`, which delegates the check to the parent `AccessControlUpgradeable` contract. The parent contract is unaware of the `ITailor` and `IERC1822Proxiable` interfaces and will therefore return `false` for the interface IDs. This means the contract incorrectly reports that it does not support interfaces it actually implements, which can break interactions with other contracts that rely on ERC-165 for interface detection.

**Recommended Mitigation:** The `supportsInterface` function should be updated to explicitly check for the `ITailor` and `IERC1822Proxiable` interface IDs in addition to calling the `super` function. This ensures that the contract correctly advertises its implementation of the given interfaces.

```solidity
// ...existing code...

import {IERC1822Proxiable} from "@openzeppelin/contracts/interfaces/draft-IERC1822.sol";

// ...existing code...

    /**
     * @notice Override supportsInterface to resolve multiple inheritance
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(AccessControlUpgradeable)
        returns (bool)
    {
        return interfaceId == type(ITailor).interfaceId ||
        return interfaceId == type(IERC1822Proxiable).interfaceId ||
        super.supportsInterface(interfaceId);
    }

// ...existing code...
```

**Button:** Fixed in commit [`32f8ca9`](https://github.com/buttonxyz/button-protocol/commit/32f8ca9c9e08986a554e12d3581178419b3d71f9)

**Cyfrin:** Verified. Recommendation implemented.

## [M-4] Addresses excluded from voting power can re-gain their voting power via a delegatee or by transfering tokens
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** WFI V2 token has a way to exclude a user's voting power by marking its `_excludedVotingPower` status to true. The intention is that after this, the user's balance will no longer be usable in voting as it delegates current balance to address(0) so that the current delegatee can no longer use it, and getVotes() returns 0 if isExcluded(account) == true.

But this can be bypassed in two ways :
- The account can call `delegate()` to re-delegate to any address X, and then address X will be able to use the account's voting power as a delegatee (getVotes retrieves delegation checkpoints).
- The account can transfer these tokens to another address Y that is controlled by him, and then Y will have the right to use that voting power

This issue occurs because the internal `_delegate()` function does not block an account from creating new delegations after the account was excluded, and `_update()` function does not block people from transferring out tokens when their address has been excluded from voting already.

Contrary to this, if the account was blacklisted, the process of removing the voting power is same, and re-delegation as well as transfers are prevented via `notBlacklisted(_account)` modifier.

```solidity
    function _delegate(
        address _account,
        address _delegatee
    )
        notBlacklisted(_msgSender())
        notBlacklisted(_account)
        notBlacklisted(_delegatee)
        internal
        override
    {
        super._delegate(_account, _delegatee);
    }
```

As a result, even though the user's own voting power returns zero via getVotes() but the delegatee's voting power is measured via the `_delegateCheckpoints[account].latest()` which also includes the "user" voting power now after this new delegation. Similarly, transferring out tokens also transfers the related voting power to the new address which is not excluded, thus making it usable.

This bypasses the point of having an excludedVotingPower status for the user as their voting power is still in use.

**Impact:** Excluded voter can still make his voting power count by delegating votes/ transferring out tokens.

**Recommended Mitigation:** Consider reverting in `_delegate()` and `_update()` function  if account's `excludedVotingPower` status is true. Note that this also blocks any kind of transfers/ burns from an excluded account.

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L314)

**Cyfrin:** Verified.

## [M-5] Onchain governance integration breaks due to inconsistent implementation of voting power
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** OpenZeppelin's [GovernorVotesUpgradeable](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/e3ba7f6a236c55e3fb7e569ecd6043b11d567c3d/contracts/governance/extensions/GovernorVotesUpgradeable.sol#L80) uses `getPastVotes` for all voting power calculations:


```solidity
    /**
     * Read the voting weight from the token's built in snapshot mechanism (see {Governor-_getVotes}).
     */
    function _getVotes(
        address account,
        uint256 timepoint,
        bytes memory /*params*/
    ) internal view virtual override returns (uint256) {
        return token().getPastVotes(account, timepoint);
    }
```

The [Governor's](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/e3ba7f6a236c55e3fb7e569ecd6043b11d567c3d/contracts/governance/GovernorUpgradeable.sol#L668) `_castVote` function retrieves voting weight using this `_getVotes` method:

```solidity
    /**
     * @dev Internal vote casting mechanism: Check that the vote is pending, that it has not been cast yet, retrieve
     * voting weight using {IGovernor-getVotes} and call the {_countVote} internal function.
     *
     * Emits a {IGovernor-VoteCast} event.
     */
    function _castVote(
        uint256 proposalId,
        address account,
        uint8 support,
        string memory reason,
        bytes memory params
    ) internal virtual returns (uint256) {
        _validateStateBitmap(proposalId, _encodeStateBitmap(ProposalState.Active));

@>        uint256 totalWeight = _getVotes(account, proposalSnapshot(proposalId), params);
        uint256 votedWeight = _countVote(proposalId, account, support, totalWeight, params);

       // @more code

        return votedWeight;
    }
```
While WLFI's `getVotes` override correctly includes both balance and vesting tokens, and checks for blacklisted and excluded accounts, the `getPastVotes` function is not overridden.

**Impact:** While UI/frontend might show users full voting power (balance + vested) via `getVotes`, the actual voting outcomes use a different voting power. Additionally, blacklisted and excluded accounts also have valid voting power because `getPastVotes` does not account for such accounts.

**Proof of Concept:** Add the following test to `WorldLibertyFinancialV2.test.ts`

```typescript
  describe('getVotes vs getPastVotes inconsistency', () => {
    it('should show discrepancy between current and historical voting power', async () => {
      // Setup: Give user1 1 ETH
      expect(await ctx.wlfi.balanceOf(ctx.core.hhUser1)).to.eq(ONE_ETH_BI);

      // User1 has NOT delegated yet (delegates returns address(0))
      expect(await ctx.wlfi.delegates(ctx.core.hhUser1)).to.eq(ADDRESS_ZERO);

      // Current voting power includes auto-delegation (balance added when delegates == address(0))
      expect(await ctx.wlfi.getVotes(ctx.core.hhUser1)).to.eq(ONE_ETH_BI);

      // Mine a block to create a checkpoint
      await mine();
      const checkpointBlock = await time.latestBlock();

      // Historical voting power at that block should be 0 (no delegation checkpoint exists)
      expect(await ctx.wlfi.getPastVotes(ctx.core.hhUser1, checkpointBlock - 1)).to.eq(ZERO_BI);

      // This shows the inconsistency:
      // - getVotes() returns 1 ETH (auto-includes balance)
      // - getPastVotes() returns 0 (no checkpoint)

      // Now test with vesting tokens
      await ctx.registry.connect(ctx.wlfiOwner).agentBulkInsertLegacyUsers(
        ZERO_BI,
        [ctx.core.hhUser1],
        [ONE_ETH_BI],
        [DEFAULT_CATEGORY],
      );

      // Setup vesting templates with immediate unlock portion
      await ctx.vester.connect(ctx.wlfiOwner).ownerSetCategoryTemplate(DEFAULT_CATEGORY, 0, TEMPLATE_1);
      await ctx.vester.connect(ctx.wlfiOwner).ownerSetCategoryTemplate(DEFAULT_CATEGORY, 1, TEMPLATE_2);
      await ctx.vester.connect(ctx.wlfiOwner).ownerSetCategoryEnabled(DEFAULT_CATEGORY, true);

      const signature = await signWlfiActivationMessage(ctx, ctx.core.hhUser1.address);
      await ctx.wlfi.connect(ctx.core.hhUser1).activateAccount(signature.serialized);

      // User1 now has 0 balance (all in vester) but 1 ETH vesting
      expect(await ctx.wlfi.balanceOf(ctx.core.hhUser1)).to.eq(ZERO_BI);
      expect(await ctx.vester.unclaimed(ctx.core.hhUser1)).to.eq(ONE_ETH_BI);

      // Current voting power includes vesting tokens
      expect(await ctx.wlfi.getVotes(ctx.core.hhUser1)).to.eq(ONE_ETH_BI);

      // Mine another block for checkpoint
      await mine();
      const vestingCheckpointBlock = await time.latestBlock();

      // Historical voting power still 0 (vesting not included in checkpoints)
      expect(await ctx.wlfi.getPastVotes(ctx.core.hhUser1, vestingCheckpointBlock - 1)).to.eq(ZERO_BI);

      // Now let's delegate to self to create a checkpoint
      await ctx.wlfi.connect(ctx.core.hhUser1).delegate(ctx.core.hhUser1);

      // Current voting power still includes vesting (but no more auto-balance since delegated)
      expect(await ctx.wlfi.getVotes(ctx.core.hhUser1)).to.eq(ONE_ETH_BI);

      await mine();
      const delegatedCheckpointBlock = await time.latestBlock();

      // Historical voting power after delegation only shows balance (0), not vesting
      expect(await ctx.wlfi.getPastVotes(ctx.core.hhUser1, delegatedCheckpointBlock - 1)).to.eq(ZERO_BI);

      // Move to after start timestamp to allow claiming
      await advanceTimeToAfterStartTimestamp(ctx);

      // Claim the immediate portion (20% of 1 ETH = 0.2 ETH)
      await ctx.wlfi.connect(ctx.core.hhUser1).claimVest();

      const claimedAmount = parseEther('0.2'); // 20% immediate from TEMPLATE_1
      expect(await ctx.wlfi.balanceOf(ctx.core.hhUser1)).to.eq(claimedAmount);

      await mine();
      const finalCheckpointBlock = await time.latestBlock();

      // Now getPastVotes shows the claimed balance (0.2 ETH)
      expect(await ctx.wlfi.getPastVotes(ctx.core.hhUser1, finalCheckpointBlock - 1)).to.eq(claimedAmount);

      // But getVotes shows balance + remaining vesting (0.2 + 0.8 = 1 ETH)
      const currentVotes = await ctx.wlfi.getVotes(ctx.core.hhUser1);
      const remainingVesting = await ctx.vester.unclaimed(ctx.core.hhUser1);

      expect(remainingVesting).to.eq(parseEther('0.8')); // 80% still vesting
      expect(currentVotes).to.eq(ONE_ETH_BI); // 0.2 claimed + 0.8 vesting = 1 ETH

      // Summary of the bug:
      // 1. Before delegation: getVotes returns 1 ETH, getPastVotes returns 0
      // 2. After delegation but before claim: getVotes returns 1 ETH (vesting), getPastVotes returns 0
      // 3. After claiming 0.2 ETH: getVotes returns 1 ETH (0.2 + 0.8 vesting), getPastVotes returns only 0.2 ETH
      // getPastVotes never includes vesting tokens or auto-delegation balance
    });
  });
```

**Recommended Mitigation:** Consider implementing a snapshot that uses `getVotes` for a historical block and document the off-chain governance and execution process. Additionally, consider reverting on `getPastVotes` to disable any on-chain voting.

```solidity
function getPastVotes(address account, uint256 timepoint)
    public view override returns (uint256) {
    revert("WLFI: Use getVotes() at historical block via RPC");
}

function getPastTotalSupply(uint256 timepoint)
    public view override returns (uint256) {
    revert("WLFI: Use totalSupply() at historical block via RPC");
}
```

**WLFI:**
Fixed in commit [269f5c1](https://github.com/worldliberty/usd1-protocol/commit/269f5c10e02d7dfe0985c4364bcbe803b1e8932b).

**Cyfrin:** Verified.

\clearpage

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-40] Upgradeable contract initializer not disabled in constructor allows implementation contract initialization
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `SegregatedVault` contract is designed as an upgradeable contract using the UUPS (Universal Upgradeable Proxy Standard) pattern, inheriting from `BaseContract` which extends `UUPSUpgradeable`. However, the implementation contract fails to disable its initializer in the constructor, creating a security vulnerability.

In UUPS upgradeable contracts, the implementation contract should have its initializer disabled in the constructor to prevent direct initialization of the implementation contract itself. Without this protection, an attacker could potentially call `SegregatedVault::initialize` directly on the implementation contract, granting themselves admin privileges and potentially disrupting the intended proxy-based upgrade mechanism.

The `SegregatedVault::initialize` function grants `DEFAULT_ADMIN_ROLE` to `msg.sender`, which would be the attacker if called directly on the implementation. This could allow unauthorized access to admin-only functions like role management and contract upgrades.

Similar issues exist in other upgradeable contracts in the codebase:
- `SecuritizeVaultV2` in the bc-securitize-vault-sc module lacks constructor initializer disabling
- `SecuritizeVault` in the bc-securitize-vault-sc module lacks constructor initializer disabling
- `RWASegWrap` lacks constructor initializer disabling
- `SecuritizeRWASegWrap` lacks constructor initializer disabling

All these contracts follow the same pattern of inheriting from `BaseContract` and implementing UUPS upgradeability without properly securing the implementation contract.

**Impact:** An attacker could initialize the implementation contract directly to gain unauthorized admin privileges and potentially compromise the upgrade mechanism for all proxy instances.

**Recommended Mitigation:** Add a constructor that disables the initializer to prevent direct initialization of the implementation contract:

```diff
contract SegregatedVault is ERC4626Upgradeable, ISegregatedVault, IVaultAccessControl, BaseContract {

+   /// @custom:oz-upgrades-unsafe-allow constructor
+   constructor() {
+       _disableInitializers();
+   }
```

Apply the same fix to other affected upgradeable contracts: `SecuritizeVaultV2`, `SecuritizeVault`, `RWASegWrap`, and `SecuritizeRWASegWrap`.

**Securitize:** Fixed in commits [1261ec](https://github.com/securitize-io/bc-securitize-vault-sc/commit/1261ec95e1f080c628193e19a00bc9e6808ffbaa) and [1a2f4c](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/1a2f4c5a4d52e297e2662c15ba50aae30238c093).

**Cyfrin:** Verified.
