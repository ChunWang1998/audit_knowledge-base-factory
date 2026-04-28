# lending / state-machine-flow

- Count: `9`
- Definition: valid system states/transitions are incomplete or inconsistent across multi-step flows.

## [Malda][M-11] Missing endpoint for extension-chain liquidation trigger
- Severity: `Medium`
- Source: [Issue #370](https://github.com/sherlock-audit/2025-07-malda-judging/issues/370)
- Impact: `functional-break`

### Detailed Content
- Summary: host-side liquidation primitive existed, but gateway did not expose equivalent extension-chain trigger carrying borrower context.
- Root Cause: interface/state transition gap between `supplyOnHost` path and `liquidateExternal` execution requirements.
- Trigger Conditions: extension chain attempts to initiate liquidation through proof-forwarder route.
- Impact Detail: critical liquidation workflow becomes unreachable for specific cross-chain execution paths.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-13] wrap+supply flow breaks with gas fee
- Severity: `Medium`
- Source: [Issue #741](https://github.com/sherlock-audit/2025-07-malda-judging/issues/741)
- Impact: `functional-break`

### Detailed Content
- Summary: helper wraps native asset using full `msg.value`, then immediately calls host supply that also requires `msg.value >= gasFee`.
- Root Cause: single-transaction value budgeting omitted reservation for gateway fee.
- Trigger Conditions: owner configures non-zero `gasFee` and user uses wrap-and-supply helper path.
- Impact Detail: wrap+supply on extension market reverts consistently, disabling a primary UX flow.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-10] Incorrect ETH/WETH matching can DoS exit flow
- Severity: `Medium`
- Source: [Issue #581](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/581)
- Impact: `dos`

### Detailed Content
- Summary: redemption flow intended to skip swap for primary token, but ETH marker and WETH address mismatch broke identity check.
- Root Cause: token comparison relied on raw address equality without canonical ETH/WETH equivalence handling across all stages.
- Trigger Conditions: strategy asset is WETH and one pool token is native ETH marker.
- Impact Detail: unnecessary/invalid trade path can execute and revert, producing exit-flow DoS.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-11] Missing gauge branch reward claim path
- Severity: `Medium`
- Source: [Issue #595](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/595)
- Impact: `functional-break`

### Detailed Content
- Summary: reward manager supports booster and gauge modes, but claim logic short-circuited when reward pool unset.
- Root Cause: gauge branch was not implemented in claim path and `rewardPool == address(0)` returned early.
- Trigger Conditions: LP is staked directly in Curve Gauge (no Convex booster path).
- Impact Detail: users accrue but cannot claim gauge rewards.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-14] Withdrawal valuation flow uses wrong pricing mode
- Severity: `Medium`
- Source: [Issue #665](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/665)
- Impact: `value-mispricing`

### Detailed Content
- Summary: once cooldown converts shares into fixed underlying amount, valuation still priced request via yield-token market value.
- Root Cause: valuation logic did not switch to deterministic-underlying mode after cooldown conversion state transition.
- Trigger Conditions: assets like USDe-style cooldown where resulting underlying is fixed and held in escrow/silo.
- Impact Detail: withdrawal request value is misstated and can propagate to risk and accounting decisions.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-17] Migration fails in debt-free edge case
- Severity: `Medium`
- Source: [Issue #674](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/674)
- Impact: `functional-break`

### Detailed Content
- Summary: migration path always passed `assetToRepay = uint256.max` and relied on debt-share derivation inside exit flow.
- Root Cause: edge case with zero borrow shares was not handled cleanly in max-sentinel repay branch.
- Trigger Conditions: user migrates collateral-only position (no debt) between routers.
- Impact Detail: migration can fail despite valid user state.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-22] WETH/native ETH setup causes loss in some exits
- Severity: `Medium`
- Source: [Issue #708](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/708)
- Impact: `fund-loss`

### Detailed Content
- Summary: for `asset=WETH` and Curve pool containing native ETH, lifecycle flows (exit/liquidation/init withdraw) use mixed wrapped/native assumptions.
- Root Cause: token-index and wrapping logic are not consistently aligned across all branches of the state machine.
- Trigger Conditions: proportional exits and request creation in this specific pool configuration.
- Impact Detail: inconsistent treatment can leak value and cause user loss.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-23] Curve pool with native ETH unsupported in valuation path
- Severity: `Medium`
- Source: [Issue #717](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/717)
- Impact: `functional-break`

### Detailed Content
- Summary: constructor rewrites Curve ALT ETH marker to internal ETH representation, but later valuation loops assume manager/request paths exist for each token uniformly.
- Root Cause: native ETH representation is not fully supported by downstream withdraw-request value retrieval flow.
- Trigger Conditions: pool includes native ETH token and code iterates token list to aggregate request values.
- Impact Detail: unsupported branch/revert behavior prevents proper pool support.

### Fix Status
- `Fixed/Resolved in report`

## [USG-Tangent][M-13] Reward cut update applies with two-cycle lag
- Severity: `Medium`
- Source: [Issue #697](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/697)
- Impact: `value-mispricing`, `functional-break`

### Detailed Content
- Summary: admin updates reward-cut params, but function processes rewards first and only then stores new params.
- Root Cause: operation ordering in `updateRCParams()` causes `lastRewardCuts` and current processing to use stale params.
- Trigger Conditions: first cycle after update still uses old cached values; effective change appears after additional cycle.
- Impact Detail: two-cycle enforcement lag creates policy-control mismatch and temporary mispricing/distribution drift.

### Fix Status
- `Fixed/Resolved in report`

## Cyfrin Fixed Issues (Merged)
- Count: `24`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Withdrawers of `sUSDe` always incur a loss because parameters passed from `Tranche::_withdraw` to `CDO::withdraw` are inverted
- Severity: `Critical`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** Users can choose to withdraw either `sUSDe` or `USDe`. The system is in charge of making the proper calculations to determine how much `USDe` value will be withdrawn based on the requested asset and the `tokenAmount` of such an asset. Based on the calculated `USDe` value being withdrawn, the system burns the required `TrancheShares` for that amount of `USDe` being withdrawn from the system.

This issue reports a problem in which the `Tranche::_withdraw` passes two parameters in the inverse order to the `CDO::withdraw`. These parameters are `baseAssets` and `tokenAssets`.
The CDO expects to receive `tokenAssets` first and then `baseAssets`, but the Tranche passes `baseAssets` first and then `tokenAssets`.
  - The parameters in the inverse order make the system do calculations with the wrong amounts, resulting (on the `Strategy` contract) that the amount of `sUSDe` to release to the user is way lower than what it should be (especially when the `sUSDe <=> USDe` rate is high.

```solidity
// Tranche::_withdraw() //
    function _withdraw(
        address token,
        address caller,
        address receiver,
        address owner,
        uint256 baseAssets,
        uint256 tokenAssets,
        uint256 shares
    ) internal virtual {
        ...
//@audit => Burn Trancheshares for the full requested sUSDe
@>      _burn(owner, shares);

//@audit-issue => Sends baseAssets first and then tokenAssets
@>      cdo.withdraw(address(this), token, baseAssets, tokenAssets, receiver);
        ...
    }

// StrataCDO::withdraw() //
    function withdraw(address tranche, address token, uint256 tokenAmount, uint256 baseAssets, address receiver) external onlyTranche nonReentrant {
        ...
//@audit => Because of the inverted parameters `tokenAmount` is actually `baseAssets`, and `baseAssets` is actually `tokenAssets`
 @>     strategy.withdraw(tranche, token, tokenAmount, baseAssets, receiver);
        ...
    }

// Strategy::withdraw() //
    function withdraw (address tranche, address token, uint256 tokenAmount, uint256 baseAssets, address receiver) external onlyCDO returns (uint256) {
//@audit => `baseAssets` should represent amount of `USDe` being withdrawn, but, because of the inverted parameters, here represents the actual requested amount of `sUSDe` to withdraw
        uint256 shares = sUSDe.previewWithdraw(baseAssets);
        if (token == address(sUSDe)) {
            uint256 cooldownSeconds = cdo.isJrt (tranche) ? sUSDeCooldownJrt : sUSDeCooldownSrt;
//@audit => transfers calculates `shares` of `sUSDe` to Cooldown to be sent to the user after cooldown.
            erc20Cooldown.transfer(sUSDe, receiver, shares, cooldownSeconds);
            return shares;
        }
        ...
    }
```

**Impact:** Withdrawers will always incur a loss in USDe value because more TrancheShares are burned compared to the received value in USDe terms.

**Proof of Concept:** In the next PoC, it is demonstrated how a user withdrawing sUSDe incurs a loss because he receives fewer sSUDe than the requested amount and the TrancheShares that were burned during the process.

As demonstrated on the next PoC, given a `sUSDe => USDe` rate of 1:1.5.
A user requests to withdraw 100 sUSDe, which are worth 150 USDe
- 150 JRTranche will be burnt
- ERC20Cooldown should receive the requested 100 sUSDe

The withdrawer receives only ~66 `sUSDe`, which can withdraw only 100 `USDe` instead of transferring 100 `sUSDe,` which could withdraw 150 `USDe`

Add the next PoC to `CDO.t.sol` test file:
```solidity
    function test_WithdrawingsUSDECausesLosesForUsers() public {
        address bob = makeAddr("Bob");
        USDe.mint(bob, 1000 ether);
        vm.startPrank(bob);
            //@audit => Bob initializes the exchange rate on sUSDe
            USDe.approve(address(sUSDe), type(uint256).max);
            sUSDe.deposit(1000 ether, bob);
        vm.stopPrank();

        address alice = makeAddr("Alice");
        uint256 initialDeposit = 150 ether;
        USDe.mint(alice, initialDeposit);

        //@audit-info => There are 1k sUSDe in circulation and 1k USDe deposited on the sUSDe contract
        //@audit-info => Exchange Rate is 1:1
        assertEq(USDe.balanceOf(address(sUSDe)), 1000 ether);
        assertEq(sUSDe.totalSupply(), 1000 ether);
        assertEq(sUSDe.convertToAssets(1e18), 1e18);

        // Simulate yield by adding USDe directly to sUSDe contract
        //@audit-info => Set sUSDe exchange rate to USDe (1:1.5)
        USDe.mint(address(sUSDe), 500 ether); // 50% yield
        assertApproxEqAbs(sUSDe.convertToAssets(1e18), 1.5e18, 1e6);

        //@audit-info => Bob deposits sUSDe when sUSDE rate to USDe is 1:1.5
        vm.startPrank(bob);
            sUSDe.approve(address(jrtVault), type(uint256).max);
            jrtVault.deposit(address(sUSDe), 100e18, bob);
            assertApproxEqAbs(jrtVault.balanceOf(bob), 150e18, 1e6);
        vm.stopPrank();

        vm.startPrank(alice);
            //@audit => Alice gets 100 sUSDe by staking 150 USDe
            USDe.approve(address(sUSDe), type(uint256).max);
            sUSDe.deposit(150e18, alice);
            assertApproxEqAbs(sUSDe.balanceOf(alice), 100e18, 1e6);

            //@audit => Alice deposits 100 sUSDe on the JRTranche and gets 150 JRTrancheShares
            sUSDe.approve(address(jrtVault), type(uint256).max);
            jrtVault.deposit(address(sUSDe), 100e18, alice);
            assertApproxEqAbs(jrtVault.balanceOf(alice), 150e18, 1e6);
            assertEq(sUSDe.balanceOf(alice), 0);

            //@audit-info => Requests to withdraw 100e18 sUSDe which are worth 150 USDe
            uint256 expected_sUSDeWithdrawn = 100e18;
            uint256 expected_USDe_valueWithdrawn = sUSDe.convertToAssets(expected_sUSDeWithdrawn);

            //@audit-issue => Alice withdraws 100 sUSDe but gets only ~66.6 sUSDe, all her JRTrancheShares are burnt
            jrtVault.withdraw(address(sUSDe), expected_sUSDeWithdrawn, alice, alice);
            uint256 alice_actual_sUSDeBalance = sUSDe.balanceOf(alice);
            uint256 alice_USDe_actualWithdrawn = sUSDe.convertToAssets(alice_actual_sUSDeBalance);

            assertEq(jrtVault.balanceOf(alice), 0);
            assertApproxEqAbs(alice_actual_sUSDeBalance, 66.5e18, 1e18);

            console2.log("Alice expected withdrawn sUSDe: ", expected_sUSDeWithdrawn);
            console2.log("Alice actual withdrawn sUSDe: ", alice_actual_sUSDeBalance);
            console2.log("====");
            console2.log("Alice expected withdrawn USDe value: ", expected_USDe_valueWithdrawn);
            console2.log("Alice actual withdrawn USDe value: ", alice_USDe_actualWithdrawn);
        vm.stopPrank();
    }
```

**Recommended Mitigation:** On the `Tranche::_withdraw`, make sure to pass the parameters in the correct order when calling the `CDO::withdraw`
```diff
    function _withdraw(
        address token,
        address caller,
        address receiver,
        address owner,
        uint256 baseAssets,
        uint256 tokenAssets,
        uint256 shares
    ) internal virtual {
        ...
-       cdo.withdraw(address(this), token, baseAssets, tokenAssets, receiver);
+       cdo.withdraw(address(this), token, tokenAssets, baseAssets, receiver);

    }

```

**Strata:**
Fixed in commit [31d9b72](https://github.com/Strata-Money/contracts-tranches/commit/31d9b7248073652ce28d579d4511d5b93414c6be) by passing the parameters in the correct order.

**Cyfrin:** Verified.

\clearpage
## High Risk

## [M-2] Withdrawal queue `RequestPrice` can be front run in case of defaults
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** When `processingMode == ProcessingMode.RequestPrice` in `AccountableWithdrawalQueue`, a redeem request’s value is fixed at the request-time share price. The request is later processed potentially at a very different price.

**Impact:** * Normal operation: Requesters are typically disadvantaged because price usually rises as interest accrues. Locking at request time forfeits subsequent gains.
* Defaults: Requesters can front-run defaults by submitting withdrawals just before delinquency/default and keep the pre-default higher price, draining liquidity and pushing losses onto remaining LPs. This worsens loss socialization precisely when fairness matters most.

**Recommended Mitigation:** Consider removing `ProcessingMode.RequestPrice` (and `AccountableWithdrawalQueue .processingMode` all together) so redemption value is always determined at processing time. Alternatively implement a safeguard for large price movements that will invalidate the redeem request.

**Accontable:**
Fixed in commit [`4e5eef5`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/4e5eef57464d548ec09048eae27b6fcc1489a5c3)

**Cyfrin:** Verified. `processingMode` removed and current price used throughout.

## [M-3] Admin void with arbitrary payout ratios allows buy then redeem profit
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `PredictionMarketV3ManagerCLOB::adminVoidMarket` lets a resolution admin set custom payout ratios `outcome0Payout` and `outcome1Payout` (which must sum to `1e18`) and immediately marks the market resolved. We do not require the market to be closed first, and we do not tie the void payouts to the current market prices. So the admin can void at any time with any valid split, for example 50/50, regardless of the prevailing yes/no ratio in the order book.

If the void payouts differ from the prices at which users can still trade, someone can buy the cheaper outcome and redeem at the void ratio for a risk-free profit. For instance, if YES trades at 60 and NO at 40, and the admin voids with 50/50, a user can front-run this call and buy NO at 40 and directly after voided receive 50 per share on redemption, gaining 10 per share. The same holds in reverse if the void favours the other side. The value of shares therefore jumps at resolution in a way that does not reflect the last tradable prices, and the last movers before the void can capture that gap.

```solidity
// PredictionMarketV3ManagerCLOB.sol:205-220
function adminVoidMarket(
  uint256 marketId,
  uint256 outcome0Payout,
  uint256 outcome1Payout
) external nonReentrant returns (int256) {
  require(registry.hasRole(registry.RESOLUTION_ADMIN_ROLE(), msg.sender), "not resolution admin");
  require(outcome0Payout + outcome1Payout == ONE, "payouts must sum to 1e18");
  // ... no check that market is closed; payouts are arbitrary
  market.resolvedOutcome = -1;
  market.state = MarketState.resolved;
  voidedPayouts[marketId] = [outcome0Payout, outcome1Payout];
```

**Impact:** Users can buy at current market prices and redeem at the admin-chosen void ratios when those ratios differ from market prices, locking in profit. Void resolution can create a step change in share value relative to the last tradable prices, allowing value extraction.

**Recommended Mitigation:** Make voiding a two-step process. In the first step, close the market (e.g. set state to closed or a dedicated “pending void” state) so that no further buys or sells can occur. In the second step, set the void payouts. When setting the payouts, use the current yes/no ratio (e.g. from a snapshot of the order book or the last traded prices at close) so that the void ratios align with the market at the time trading stopped. That avoids stepwise jumps in share value and removes the buy-then-redeem arbitrage.

**Myriad:** Fixed in commit [`4c4ec70`](https://github.com/Polkamarkets/polkamarkets-js/commit/4c4ec70b73cc506249a28b435205e97449cde3c0)

**Cyfrin:** Verified.

## [M-4] Increase in coverage can lead to a grief attack causing a DoS for previous withdrawal requests
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** This issue demonstrates how an increment in the `coverage`, caused by **a) a large withdrawal on the SR Tranche**, or **b) an increment on the JR deposits**, can be leveraged to pull off a DoS attack on demand and affect both instant and normal (once the cooldown period is over) finalizations.

The fix for issue [*Finalizing withdrawal requests on the `SharesCooldown` contract allows for third-parties to override user’s chosen output token*](#finalizing-withdrawal-requests-on-the-sharescooldown-contract-allows-for-thirdparties-to-override-users-chosen-output-token) addresses an issue with the permissionless`finalize` function. However, even with that fix, this issue can still be pulled off for withdrawals requesting `USDe`, and the fix for issue [*`SharesCooldown` instant finalization can be DoSed because of the `UnstakeCooldown` request limits*](#sharescooldown-instant-finalization-can-be-dosed-because-of-the-unstakecooldown-request-limits) only addresses the problem on instant finalizations.

Following the premise behind the cooldown period and fees based on the current `coverage`.
- High coverage => Low cooldown and fees
- Low coverage => High cooldown and fees

Attackers can grief legitimate users' withdrawals from the SR Tranche requesting `USDe` in a scenario where, after the withdrawal, `coverage` goes from a lower range (more restrictive) to a higher range (less restrictive), withdrawal conditions improves, which means that subsequent withdrawals will take less cooldown time + the attacker knows the end time of the real withdrawal's shares cooldown.

An example of an attack derived from an increment in coverage would look like this:
1. A withdrawal requesting `USDe` from the SR Tranche.
2. `coverage` increments and goes to a less restrictive range. Coverage is incremented either by a) the withdrawal on step 1 (a large withdrawal), or b) an increment on the deposits on the JR Tranche.
3. An attacker requests small withdrawals, asking for `USDe` as the asset to receive, setting the withdrawer of step 1 as the `receiver`.
- All these withdrawals will have a lower cooldown because the `coverage` is on a better range than the range at which the withdrawal from step 1 was processed.
4. Time passes, and as these withdrawals' cooldown is over, the attacker finalizes them, lowering the number of `activeRequests` for the withdrawer on the `SharesCooldown` and incrementing the queue for the withdrawer on the `UnstakeCooldown.
5. As the number of `activeRequests` on the `SharesCooldown` decrements, while the first withdrawal request is under cooldown, the attacker can continue to repeat steps 3-5 to drive the queue of the withdrawer on the `UnstakeCooldown` to its limit, and have more withdrawal requests cooling down on the `SharesCooldown`.
6. Once the first withdrawal passes the cooldown period, the withdrawer attempts to finalize it, but because the `UnstakeCooldown`'s queue for the withdrawer is complete, the finalization attempt reverts with error `ExternalReceiverRequestLimitReached`.

**Impact:** SR withdrawals can be temporarily DoSed when they request to withdraw `USDe`

**Recommended Mitigation:** Given that issue [*`SharesCooldown` instant finalization can be DoSed because of the `UnstakeCooldown` request limits*](#sharescooldown-instant-finalization-can-be-dosed-because-of-the-unstakecooldown-request-limits) by itself only prevents the DoS on the instant finalizations. The recommended mitigation for issue [*Finalizing withdrawal requests on the `SharesCooldown` contract allows for third-parties to override user’s chosen output token*](#finalizing-withdrawal-requests-on-the-sharescooldown-contract-allows-for-thirdparties-to-override-users-chosen-output-token) would not address this issue for the normal finalizations, the suggested mitigation to fully cover all the DoS scenarios accounting for the fixes of both problems (#15 and [*Finalizing withdrawal requests on the `SharesCooldown` contract allows for third-parties to override user’s chosen output token*](#finalizing-withdrawal-requests-on-the-sharescooldown-contract-allows-for-thirdparties-to-override-users-chosen-output-token)), the fix for this issue would be:
- **Create a new `finalize` function that is permissioned and only allows the withdrawer to call it.** The difference between this function and the suggested mitigation for [*Finalizing withdrawal requests on the `SharesCooldown` contract allows for third-parties to override user’s chosen output token*](#finalizing-withdrawal-requests-on-the-sharescooldown-contract-allows-for-thirdparties-to-override-users-chosen-output-token) is that **this new function should allow the withdrawer to specify the asset to receive**, whilst the permissionless version should not (The permissionless version must preserve the original choice at the moment of the withdrawal request).

**Strata:** Fixed in commit [0354983](https://github.com/Strata-Money/contracts-tranches/commit/03549831cf5912b15d9a0eac2bdcfae7e1c395d8).

**Cyfrin:** Verified. New function `SharesCooldown::finalizeWithTokenOverride` allows the withdrawers to finalize their withdrawal requests, specifying the `token` they wish to receive

\clearpage

## [M-5] Unbounded weight scale factor causes precision loss in stake conversion, potentially leading to loss of operator funds
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware` uses a `WEIGHT_SCALE_FACTOR` to convert between 256-bit stake amounts and 64-bit validator weights for the P-Chain. However, there are no bounds on this scale factor, and an inappropriately high value can cause precision loss.

The conversion process works as follows:

`stakeToWeight(): weight = stakeAmount / scaleFactor`
`weightToStake(): recoveredStake = weight * scaleFactor`

When `WEIGHT_SCALE_FACTOR` is too high relative to stake amounts, the division in `stakeToWeight()` truncates to zero, making the stake effectively unusable.


**Impact:** Weight recorded for validator can be 0 due to precision loss.

**Recommended Mitigation:** Consider implementing reasonable maximum bounds in the constructor.

**Suzaku:**
Fixed in commit [b38dfed](https://github.com/suzaku-network/suzaku-core/pull/155/commits/b38dfed1d21a628582b11d217f5112290b973034).

**Cyfrin:** Verified.

## [M-6] Account Count Validation Mismatch in `new_base_crncy` Instruction
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `new_base_crncy` instruction has an inconsistency between the declared minimum account count and the actual number of accounts required.

The function comment and implementation both indicate that `9` accounts are needed, but `NewBaseCrncyInstruction::MIN_ACCOUNTS` is set to `8`.

```rust
pub fn new_base_crncy(program_id: &Pubkey, accounts: &[AccountInfo], _: &[u8]) -> DeriverseResult {
    // New Base Currency Instruction
    // 1 - Admin (Signer)
    // 2 - Root Account (Read Only)
    // 3 - Token Account
    // 4 - Program Token Account (Signer when creating a new token)
    // 5 - Deriverse Authority Account (Read Only)
    // 6 - Token Program ID (Read Only)
    // 7 - Mint Address (Read Only, when wSOL can not be old native mint)
    // 8 - System Program (Read Only)
    // 9 - Community Account
```

The function first reads 8 accounts, then later reads the 9th account:

```rust:145:src/program/processor/new_base_crncy.rs
    let community_acc = next_account_info!(accounts_iter)?;
```


However, the validation check only requires 8 accounts:

```rust:50-55:src/program/processor/new_base_crncy.rs
    if accounts.len() < NewBaseCrncyInstruction::MIN_ACCOUNTS {
        bail!(InvalidAccountsNumber {
            expected: NewBaseCrncyInstruction::MIN_ACCOUNTS,
            actual: accounts.len(),
        });
    }
```

Where `MIN_ACCOUNTS` is defined as:

```rust:281-285:constants.rs
    pub struct NewBaseCrncyInstruction;
    impl DrvInstruction for NewBaseCrncyInstruction {
        const INSTRUCTION_NUMBER: u8 = 4;
        const MIN_ACCOUNTS: usize = 8;
    }
```

**Impact:**
1. **Incorrect Validation**: The instruction accepts `8` accounts when it actually requires `9,` creating a mismatch between the validation and the actual account requirements.
2. **Late Failure**: Transactions with only `8` accounts will pass the initial check but fail later during execution.

**Recommended Mitigation:** Update `MIN_ACCOUNTS` to `9` to match the actual account requirements:

```rust
pub struct NewBaseCrncyInstruction;
impl DrvInstruction for NewBaseCrncyInstruction {
    const INSTRUCTION_NUMBER: u8 = 4;
    const MIN_ACCOUNTS: usize = 9;  // Changed from 8 to 9
}
```

**Deriverse:** Fixed in commit [f54117b0](https://github.com/deriverse/protocol-v1/commit/f54117b09012e11e0003844f5f855e6f878d3f73).

**Cyfrin:** Verified.

## [M-7] Eligible intruments may not be propagated
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The function `dividends_allocation` currently throws error when encountering an instrument whose `distrib_time` has not yet passed the 1-hour threshold:
```rust
        } else {
            //@audit instead of returning we should have continued to another instr
            bail!(TooEarlyToDistribFunds {
                limit_time: instr_state.header.distrib_time,
                current_time: time,
            });
        }
```
This immediately terminates the entire dividends allocation process, even if subsequent instruments in the same transaction are eligible for distribution.
As a result, valid instruments are skipped.

**Impact:** Eligible instruments in the same batch are not processed.

**Recommended Mitigation:** Instead of bailing, we should continue to the next instrument in the loop:
```rust
if time > instr_state.header.distrib_time + HOUR {
    // distribute funds
} else {
    // skip this instrument, continue to next
    continue;
}
```
**Deriverse**
Fixed in commit [ca593e2](https://github.com/deriverse/protocol-v1/commit/ca593e2bc30b93a7a4a53c69ceb5b91a282c8955).

**Cyfrin:** Verified.

## [M-8] Entrypoint panics on empty `instruction_data`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The issue originates from a missing bounds check for the `instruction_data` array before accessing its first element during opcode dispatch.

```rust
entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    match instruction_data[0] {
        NewHolderInstruction::INSTRUCTION_NUMBER => new_holder_account(program_id, accounts)?,
        NewOperatorInstruction::INSTRUCTION_NUMBER => {
            new_operator(program_id, accounts, instruction_data)?
        }
```


**Impact:** This can result in an out-of-bounds read and program panic when `instruction_data` is empty instead of exiting gracefully with correct error message.

**Recommended Mitigation:** To mitigate this vulnerability, the program should validate the length of `instruction_data` before accessing entries, and handle the error gracefully instead of resorting to a crash.

**Deriverse:** Fixed in commit [8a2bd16](https://github.com/deriverse/protocol-v1/commit/8a2bd16db9fd84126fdf58c7f7eeb7b13410ba54).

**Cyfrin:** Verified.

## [M-9] Expired Private Client Cannot Be Re-added to Queue
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `new_private_client()` function incorrectly rejects re-adding a wallet whose previous entry has expired. The function checks for duplicate wallet addresses before validating expiration status, preventing expired records from being treated as vacant slots.

In the record insertion logic (lines 131-133), the code checks if a wallet already exists:
```rust
if record.wallet == *wallet.key && record.creation_time != 0 {
    return Err(AlreadyExists(index));
}
```
However, this check occurs before the expiration validation. According to the `PrivateClient::is_vacant()` method (defined in `src/state/private_client.rs`), a record should be considered vacant if either:
1. `creation_time == 0` (uninitialized), or
2. `current_time > expiration_time` (expired)

The problem is that when iterating through records to find an insertion position, the duplicate check at line 131 returns an error immediately when a matching wallet is found, regardless of expiration status. This prevents the code from reaching the `is_vacant()` check at line 136, which would correctly identify expired records as reusable slots.

**Impact:** **Queue Slot Exhaustion:** Expired private client cannot be renewed.


**Recommended Mitigation:** Modify the duplicate wallet check to validate expiration status before returning an error. Only return `AlreadyExists` if the wallet matches and the record is still valid (not expired).

**Deriverse:** Fixed in commit [a626a26](https://github.com/deriverse/protocol-v1/commit/a626a2626a483e55f76b582f5bd49ff2a7b2d62a).

**Cyfrin:** Verified.

## [M-10] Fixed token account size causes initialization failures for token accounts whose mints have token 22 extensions are active
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:**  The `create_token` function in `token.rs` uses a hardcoded size of 165 bytes when creating SPL token accounts, regardless of whether the mint has Token 2022 extensions enabled. This will cause initialisation failures for mints with extensions that require additional account space.

```rust
let spl_lamports = rent.minimum_balance(165);
invoke(
    &system_instruction::create_account(
        creator.key,
        program_acc.key,
        spl_lamports,
        165, // @audit why is it hardcoded to 165?
        token_program_id.key,
    ),
    &[creator.clone(), program_acc.clone()],
)
```
The constant 165 bytes is the legacy SPL-Token size. Allocating only 165 bytes causes `initialize_account3` to fail with `InvalidAccountData`[here](https://github.com/solana-program/token-2022/blob/50a849ef96634e02208086605efade0b0a9f5cd4/program/src/processor.rs#L187-L191)


**Impact:**
- Token creation will fail for any Token 2022 mint with extensions

**Recommended Mitigation:** In the case when the mint's owner is token 2022 program, calculate the size first and then allocate that calculated space instead of a hardcoded 165 bytes.

```rust
let account_size = if token_program == TokenProgram::Token2022 {
    use spl_token_2022::extension::StateWithExtensions;
    StateWithExtensions::<spl_token_2022::state::Account>::try_get_account_len(mint)?
} else {
    165 // Standard SPL token account size
};

let spl_lamports = rent.minimum_balance(account_size);
invoke(
    &system_instruction::create_account(
        creator.key,
        program_acc.key,
        spl_lamports,
        account_size as u64,
        token_program_id.key,
    ),
    &[creator.clone(), program_acc.clone()],
)
```
**Deriverse:** Fixed in commit: https://github.com/deriverse/protocol-v1/commit/6e8b8b011e69c356a81e4cc1f8cbe14adf5bf0a6

**Cyfrin:** Verified.

## [M-11] Inflexible Voting System Prevents Rapid Parameter Adjustments
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The governance voting system uses a rigid rotation mechanism where which parameter can be modified is determined by `voting_counter % 6`.

This creates a fixed 6-parameter rotation cycle where each parameter can only be voted on once every 6 voting periods. Combined with the 14-day voting period duration, this means a specific parameter can only be modified again after approximately 84 days (6 periods × 14 days), severely limiting the protocol's ability to respond to urgent situations or make consecutive adjustments to the same parameter.

The parameter selection is determined in `finalize_voting()`:

```rust
let tag = community_account_header.voting_counter % 6;
match tag {
    0 => spot_fee_rate,
    1 => perp_fee_rate,
    2 => spot_pool_ratio,
    3 => margin_call_penalty_rate,
    4 => fees_prepayment_for_max_discount,
    _ => max_discount,
}
```

The `voting_counter` can only increment by 1 in `finalize_voting()`:

```rust
community_account_header.voting_counter += 1;
```

And in `next_voting()`, the counter can only be incremented to 1 if it's 0, or finalized (which increments by 1):

```rust
if community_state.header.voting_counter == 0 {
    community_state.header.upgrade()?.voting_counter += 1;
}
community_state.finalize_voting(clock.unix_timestamp as u32, clock.slot as u32)?;
```

**The Problem:**
1. There is no mechanism to skip voting rounds or target a specific parameter directly
2. The `voting_counter` can only increment sequentially, never skip ahead
3. If a parameter needs urgent adjustment or consecutive modifications, the protocol must wait through the entire 6-parameter cycle
4. No emergency mechanism exists for operator or admin to override the rotation schedule

**Example Scenario:**
1. Voting period 1 (`voting_counter` = 1): Community votes to decrease `perp_fee_rate` (tag `1`)
2. After 14 days, the change is applied, `voting_counter` becomes 2
3. Market conditions change, requiring another immediate adjustment to `perp_fee_rate`
4. The protocol must wait for voting_counter = `7, 13, 19`, etc. (every 6th period)
5. This means waiting approximately `70 days` (5 more periods × 14 days) before `perp_fee_rate` can be voted on again

```rust
#[cfg(not(feature = "test-sbf"))]
pub fn voting_end(time: u32) -> u32 {
    let days = (time - SETTLEMENT) / DAY;
    days * DAY + 14 * DAY + SETTLEMENT
}

```

**Impact:**
- **Delayed Response to Market Conditions:** The protocol cannot quickly respond to urgent situations requiring consecutive parameter adjustments
- **Inefficient Governance:** If a parameter needs multiple adjustments to reach an optimal value, the process takes months(5*14 = 70 days) instead of weeks

**Recommended Mitigation:** Consider adding an optional mechanism to allow the operator to specify the next `voting_counter` value in extreme circumstances, while maintaining the default sequential increment for normal operations.

**Deriverse::**
Fixed in commit [bb853ad](https://github.com/deriverse/protocol-v1/commit/bb853adf0cfecf974b1b1933a6192b4dfb7e42ae).

**Cyfrin:** Verified.

## [M-12] Missing System Program Check in Instructions like `new_operator`(Inconsistency)
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Unlike many other handlers, `new_operator` does not verify that the `system_program` account equals `solana_program::system_program::ID` before using it in `realloc_account_data`. The call would eventually fail if a wrong account is supplied, but the error surfaces only after a CPI panic rather than as a clean, descriptive failure.

The instruction expects `system_program (accounts[3])` to be the Solana system program and later passes it into `realloc_account_data`, which performs a CPI to the system program.

```rust
    let system_program = next_account_info!(accounts_iter)?;
    check_holder_admin(admin)?;
    let mut holder_state = HolderState::new(holder_acc, program_id)?;

    let begin = std::mem::size_of::<HolderAccountHeader>()
        + (holder_state.header.operators_count as usize) * std::mem::size_of::<Operator>();

    let new_size = begin + std::mem::size_of::<Operator>();

    if holder_acc.data_len() < new_size {
        realloc_account_data(admin, holder_acc, system_program, new_size, None, true)
            .map_err(|err| drv_err!(err.into()))?;
    }
```

 If a client provides some other executable account, the CPI will trap because the runtime detects the program-id mismatch. This isn’t exploitable, but it differs from other processors (e.g., `new_instrument`) that proactively check `system_program.key == system_program::ID` and return a clear error before the CPI.

```rust
    if !system_program::check_id(system_program.key) {
        bail!(InvalidSystemProgramId {
            actual_address: *system_program.key,
        });
    }
```


**Impact:** Program will panic instead of returning a well-typed error.

**Recommended Mitigation:** Add an explicit check in `new_operator` (and any similar handlers) that `system_program.key == &solana_program::system_program::ID`

**Deriverse:** Fixed in commit [d7b852b4](https://github.com/deriverse/protocol-v1/commit/d7b852b42564541dddec86289a23ac2696b264af).

**Cyfrin:** Verified.

## [M-13] Missing Validation for `order_type` in NewSpotOrderData
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `NewSpotOrderData::new` validation function does not verify that `order_type` is a valid value for spot orders. While spot orders should only accept `Limit (0)` and `Market (1)`, the validation allows `MarginCall (2)` and `ForcedClose (3)` to pass through. These invalid values are then incorrectly processed as Market orders, leading to data inconsistency in logs and potential confusion.

In `src/program/instruction_data.rs`, the `NewSpotOrderData::new` function validates:
- `instr_id range
- price validity (only when `order_type == 0`)
- `amount` range
However, it does not validate that `order_type` is within the allowed range for spot orders (0 or 1).

```rust
    fn new(instruction_data: &[u8], instr_count: u32) -> Result<&Self, DeriverseError> {
        let data = bytemuck::try_from_bytes::<Self>(instruction_data)
            .map_err(|_| drv_err!(InvalidClientDataFormat))?;

        if data.instr_id >= instr_count {
            bail!(InvalidInstrId { id: *data.instr_id })
        }
        if data.order_type == 0 && !(MIN_PRICE..=MAX_PRICE).contains(&data.price) {
            bail!(InvalidPrice {
                price: data.price,
                min_price: MIN_PRICE,
                max_price: MAX_PRICE,
            })
        }
        if !(1..=SPOT_MAX_AMOUNT).contains(&data.amount) {
            bail!(InvalidQuantity {
                value: data.amount,
                min_value: 1,
                max_value: SPOT_MAX_AMOUNT,
            })
        }

        return Ok(data);
    }
```

The `OrderType` enum defines:
```rust
pub enum OrderType {
    Limit = 0,
    Market = 1,
    MarginCall = 2,    // Only for perp orders
    ForcedClose = 3,   // Not used in codebase
}
```

In `src/program/processor/new_spot_order.rs`, the code only explicitly handles Limit:
```rust
if data.order_type == OrderType::Limit as u8 {
    data.price
} else if buy {
    mark_px + (mark_px >> 3)  // All other values treated as Market
} else {
    mark_px - (mark_px >> 3)
}
```

Then the `type` is being emitted in logs:

```rust
    solana_program::log::sol_log_data(&[bytemuck::bytes_of::<SpotPlaceOrderReport>(
        &SpotPlaceOrderReport {
            tag: log_type::SPOT_PLACE_ORDER,
            order_type: data.order_type,
            side: if buy { 0 } else { 1 },
            ioc: data.ioc,
            client_id: client_state.id,
            order_id: engine.state.header.counter,
            instr_id: data.instr_id,
            qty: data.amount,
            price,
            time: ctx.time,
        },
    )]);
```

**Impact:**
- Data Inconsistency: Logs will contain incorrect order_type values that don't match the actual order behavior
- Input Validation Gap: Missing validation allows invalid enum values to be accepted

**Recommended Mitigation:** Add validation in `NewSpotOrderData::new` to ensure `order_type` is only 0 (Limit) or 1 (Market) for spot orders:

Example:
```rust
        // Add this validation
        if data.order_type > OrderType::Market as u8 {
            bail!(InvalidOrderType {
                order_type: data.order_type,
                allowed_types: vec![OrderType::Limit as u8, OrderType::Market as u8],
            })
        }
```

**Deriverse:** Fixed in commit [53000a3](https://github.com/deriverse/protocol-v1/commit/53000a32c4f9af1629b8a9f7d9b6b696a6084189).

**Cyfrin:** Verified.

## [M-14] Silent Error Handling in `clean_generic` Introduces Multiple Risks
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `clean_generic()` function in `ClientPrimaryState` implements silent error handling for account parsing using `if let Ok(header)`, which introduces three potential issues that can lead to incorrect state updates, account desynchronization, and masking of underlying instruction problems.

The function expects accounts to be provided in pairs: a `maps_acc` account followed by a `client_infos_acc`. The loop counter increments by 2 for each successfully processed pair, assuming 2 accounts are consumed per iteration.

```rust
            if let Ok(header) = header { // Silent failure handling
                counter += 2;
                let client_infos_acc = next_account_info!(accounts_iter)?;

                SpotTradeAccountHeader::<SPOT_CLIENT_INFOS>::validate(
                    client_infos_acc,
                    program_id,
                    Some(header.instr_id),
                    version,
                )?;

                self.client_infos_acc = client_infos_acc;
                self.maps_acc = maps_acc;
                self.resolve_instr(client_infos_acc, false)?;
                self.finalize_spot()?;
            }
        }
        Ok(())
    }

```


- Issue 1: Silent Error Handling Masks Instruction-Level Problems

**A single parsing failure may indicate that the entire instruction is malformed or that the account structure is fundamentally incorrect. By silently continuing execution, the function masks these critical errors and may introduce additional risks**

- Issue 2: Incorrect Assumption About Account Pairing Structure

The silent error handling assumes a specific account ordering pattern: `[bad_maps_acc, good_maps_acc, good_client_infos_acc]`. However, this assumption is fragile and often incorrect. The actual account sequence may not follow this pattern. For example, if a `maps_acc` fails, the next account might be another `maps_acc` (as assumed), but it could also be a `client_infos_acc` from a previous pair

- Issue 3: Iterator-Counter Desynchronization

When `maps_acc` fails to parse, `next_account_info!(accounts_iter)?` has already advanced the iterator, consuming one account, but the counter does not increment when parsing fails. This creates a desynchronization:

- **Iterator position**: Advances by 1 account (`maps_acc consumed`)
- **Counter value**: Remains unchanged (no increment)
- **Expected behavior**: Counter should track consumed accounts


Given 6 accounts: `[map1(bad), map2(ok), client_info2(ok), map3(bad), map3(ok), client_info3(ok)]` and `length = 6`:

1. Iteration 1: Reads `map1(bad)` → parsing fails → counter = 1, iterator at position 1
2. Iteration 2: Reads `map2(ok)` → parsing succeeds → counter = 3, iterator at position 3 (after reading `client_info2`)
3. Iteration 3: Reads `map3(bad)` → parsing fails → counter = 3, iterator at position 4
4. Iteration 4: Reads `map3(ok)` → parsing succeeds → counter = 5, iterator at position 6 (after reading `client_info3`)
5. Loop condition `counter < length` (5 < 6) is still true, but iterator is exhausted

This desynchronization can cause:
- Reading accounts beyond the intended range
- Processing incorrect account pairs
- Potential panic if `next_account_info!` is called when the iterator is exhausted

**Impact:**
1. **Instruction Integrity Violation**: Silent error handling masks critical instruction-level problems, allowing malformed or malicious instructions to partially execute.

2. **Incorrect Account Pairing**: The assumption that failed accounts are followed by correct pairs is often violated.

3. **Iterator-Counter Desynchronization**: The iterator position and counter become misaligned when parsing fails, causing:
   - Subsequent iterations to read incorrect accounts
   - Processing accounts out of order or skipping required accounts
   - Potential panic when `next_account_info!` is called on an exhausted iterator

**Recommended Mitigation:** The function should fail fast on parsing errors rather than silently continuing. This addresses all three issues.

**Deriverse:** Fixed in commit [1c2f2a5](https://github.com/deriverse/protocol-v1/commit/1c2f2a5c3f6475eea2fdbbd9f1b77595fbd622e1).

**Cyfrin:** Verified.

## [M-15] Unnecessary Lamports Transfer Without Checking Existing Balance
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `new_private_client()` function transfers the full `minimum_balance` amount to the `private_clients_acc` account without first checking if the account already has sufficient lamports. This results in unnecessary transfers even when the account already contains enough funds to cover the rent requirement.

```rust
// src/program/processor/new_private_client.rs:163-174
let rent = &Rent::default();
let lamports = rent.minimum_balance(std::mem::size_of::<PrivateClient>());

invoke(
    &system_instruction::transfer(admin.key, private_clients_acc.key, lamports),
    &[
        admin.clone(),
        private_clients_acc.clone(),
        system_program.clone(),
    ],
)
.map_err(|err| drv_err!(err.into()))?;
```

This approach differs from the pattern used consistently throughout the codebase in similar scenarios, which calculate and transfer only the difference needed:

**Impact:** **Potential Over-payment:** If the account already contains more than the minimum required balance, the function still attempts to transfer the full minimum balance amount.

**Recommended Mitigation:** Calculate and transfer only the difference needed, matching the pattern used in other functions like `new_operator()`.

**Deriverse:** Fixed in commit [7091f4](https://github.com/deriverse/protocol-v1/commit/7091f48316d77e6769ee8fddeadd4d3a250ba1e1).

**Cyfrin:** Verified.

## [M-16] Users are getting back their `soc-loss-funds` while selling their market seat
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Inside `sell-market-seat` when [soc-loss-funds](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/sell_market_seat.rs#L122) are negative, which means user has added and contributed to protocol's soc loss funds & beared losses on behalf of others of his side... in this case user is getting back those funds, and these funds are being deducted from insurance funds as well, general idea is to not give back what user has contributed towards soc loss, but here, user is getting it back
```rust
    let collactable_losses = info.funds().min(client_state.perp_info4()?.soc_loss_funds);
    engine.state.header.perp_insurance_fund += collactable_losses;

    client_state.add_crncy_tokens((info.funds() - collactable_losses).max(0))?;
```
for eg.
- A user incurred some losses, his soc loss are updated to +20
- in next call to [check-soc-loss](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/perp/perp_engine.rs#L2216) he pays back +30, user's net soc loss becomes -10, meaning user contributed towards protocol's soc losses as we can see this amount being added to `self.state.header.perp_soc_loss_funds` as well
- now user goes to sell his market seat with his `soc-loss-funds` set to -10..... he [gets back](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/sell_market_seat.rs#L125) this amount, which he should not.

**Impact:** Users get back what they paid towards soc loss.

**Recommended Mitigation:** In the cases when user's `soc-loss-funds` come out to be negative, avoid accounting for it.

**Deriverse:** Fixed in commit: [e5af702](https://github.com/deriverse/protocol-v1/commit/e5af70204e812ed9f388a0dea23ff89fd15f2394)

**Cyfrin:** Verified.

## [M-17] Users can sell their market seat without paying loss coverage
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** When users incur loss, its covered from available insurance funds and is stored and tracked inside `taker_info4.loss_coverage`, this is what user owes to protocol before he closes his position, because insurance funds have been used to cover up for these losses incurred by user. Inside `sell-market-seat` we are calling [close_account](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/sell_market_seat.rs#L127), it does not check for users's loss coverage, it only checks
```rust
            if (*self.perp_info3).bids_entry != NULL_ORDER
                || (*self.perp_info3).asks_entry != NULL_ORDER
                || self.current_instr_index >= self.assets.len()
            {
                bail!(ClientDataDestruction);
            }
```
if user has incurred losses in past and insurance funds covered this loss, he must pay back these funds before closing the seat, the function [`try_to_close_perp`](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/state/client_primary.rs#L701) checks this properly, if user has pending loss coverage we subtract it from users' funds, this way he pays back his losses and then closes the position.
```rust
            if (*self.perp_info4).loss_coverage > 0 {
                let delta = (*self.perp_info4)
                    .loss_coverage
                    .min((*self.perp_info).funds);
                if delta > 0 {
                    engine.state.header.perp_insurance_fund += delta;
                    (*self.perp_info4).loss_coverage -= delta;
                    (*self.perp_info).funds -= delta;
                }
            }
```

**Impact:** Users can close their seats without paying for their incured losses

**Recommended Mitigation:** Call `try_to_close_perp` instead of `close_perp` inside `sell-market-seat`.

**Deriverse:** Fixed in commit: [e5af702](https://github.com/deriverse/protocol-v1/commit/e5af70204e812ed9f388a0dea23ff89fd15f2394)

**Cyfrin:** Verified.

## [M-18] Voting is allowed even after voting period's end time.
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `voting()` function does not validate whether the voting period has ended before processing and recording votes. The function only checks the voting end time in the `finalize_voting()` call at the very end, but by that point the user's vote has already been cast and included in the voting tallies. This allows the last user to submit a vote even after the official voting period has expired, as long as they call the function before anyone else triggers the finalization.
```rust
//here vote has been included even if end time has been passed of this period
        match data.choice {
            VoteOption::DECREMENT => {
                community_account_header.voting_decr += voting_tokens;
            }
            VoteOption::INCREMENT => {
                community_account_header.voting_incr += voting_tokens;
            }
            _ => community_account_header.voting_unchange += voting_tokens,
        }
....
// the call to finalize voting is made later, so the late user's vote has been included
        community_state.finalize_voting(time, clock.slot as u32)?;
```
**Impact:**
- Malicious actors can cast votes after the voting period has officially ended
-  Late voter(if is holding many tokens) gain knowledge of current vote tallies and can strategically vote to influence outcomes in his favor.

**Recommended Mitigation:** Implement a check which errors when user tries to cast vote affter official `CommunityState.header.voting_end_time` time prior to casting vote & making call to `finalize voting`

**Deriverse**
Fixed in commit: [a5194d]9https://github.com/deriverse/protocol-v1/commit/a5194d26218f0828e83481ebb2a6f7071773b13a)

**Cyfrin:** Verified.

## [M-19] wrong error emitted from `spot-order-cancel`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Inside [spot-order-cancel](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/spot_order_cancel.rs#L51), wrong error is emitted when accounts length is more than expected length, which is wrong and inconsistent with rest of the places.
```rust
    if accounts.len() < SpotOrderCancelInstruction::MIN_ACCOUNTS {
        //@audit wrong, should have been InvalidAccountsNumber
        bail!(InvalidDataLength {
            expected: SpotOrderCancelInstruction::MIN_ACCOUNTS,
            actual: accounts.len(),
        });
    }
```

**Impact:** wrong errors cause confusions and give hard time debugging underlying issue.

**Recommended Mitigation:** Replace it with
```rust
        bail!(InvalidAccountsNumber {
            expected: SpotMassCancelInstruction::MIN_ACCOUNTS,
            actual: accounts.len(),
        });
```

**Deriverse:** Fixed in commit : [4b2e123](https://github.com/deriverse/protocol-v1/commit/4b2e1230342c2ef474803c50a10dd34d46276376)

**Cyfrin:** verified.

## [M-20] Delinquency status update in `AccountableOpenTerm` hooks uses pre-queue state
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** The Vault calls strategy hooks (e.g., `AccountableStrategy::onRequestRedeem`, `onDeposit`, `onMint`) before the Vault updates the state that these actions affect (queue totals for redeem requests, and `totalAssets`/liquidity for deposits/mints).

However, `AccountableOpenTerm` updates delinquency status inside the hooks.

As a result, delinquency calculations that depend on Vault-side values (e.g., queued shares / available liquidity derived from `totalAssets`, `reservedLiquidity`, `totalQueuedShares`, etc.) can be evaluated using a pre-action snapshot:

* `AccountableOpenTerm::onRequestRedeem`: for queued (non-instant) requests, the request is only enqueued after the hook returns, so delinquency is checked before the new queued shares are reflected.
* `AccountableOpenTerm::onDeposit` / `onMint`: the hook runs before the Vault receives assets / updates totals, so delinquency can be checked before the new liquidity from the deposit/mint is reflected.

**Impact:** Delinquency status may lag by one interaction (or until another status update is triggered). For example:

* a queued redeem may not immediately mark the loan delinquent, and/or
* a deposit/mint that would restore liquidity may not immediately clear delinquency.

This is primarily a correctness / timing issue unless delinquency gating is expected to be exact within the same transaction.

**Recommended Mitigation:** Consider passing the changes in shares and assets to the delinquency calculation so that it can account for the added/removed shares/assets. Or use the same pattern as `Vault::cancelRedeemRequest` where the. `strategy.updateLateStatus()` hook is called at the end.

**Accountable:** Fixed in commit [`5f815ee`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/5f815ee49e6f88585befd3061abf2bc081ae3d8c)

**Cyfrin:** Verified. Delinquency update removed from the strategy hooks and each vault function now calls `trategy.updateLateStatus`.

## [M-21] Function `execute` overwrites seenSigner values irrespective of request age
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Function `publish` allows authenticated signers to publish requests for the current batch in process. By design, signers are allowed publish multiple requests in a batch, with each request having its own distinct timestamp.

When an authorized executor calls the `execute` function, this for loop will overwrite the signer's first request value with the second request value (assuming only two requests have been published). However, it is possible that the `request.timestamp` of the second request is older than the timestamp of the first request. In this case, the function uses the seen signer's relatively older request value instead of the latest, which can lead to slightly inaccurate publish rates.
```solidity
          for (uint256 j = 0; j < uniqueSigners; ++j) {
                if (requests[i].signer == seenSigners[j]) {
                    // Update to latest value from this signer
                    values[j] = requests[i].value;
                    isDuplicate = true;
                    break;
                }
            }
```

**Proof of Concept:** Let's take a simple example:
 - Alice submits two requests - R1 and R2
 - The timestamps of R1 and R2 are 20 and 10 respectively.
 - During execution, R1's value is overwritten by R2's value even though R2 is a relatively older request.

**Recommended Mitigation:** If a signer has multiple requests in a batch, ensure the value is not overwritten unless the timestamp of the request is fresher.

**Accountable:** Fixed in commit [`141ca3b`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/141ca3b7025ddb9316eb55b0399ed9999daf60aa)

**Cyfrin:** Verified. Only updates if timestamp is later.

## [M-22] Immediate withdrawals possible even when NAV is stale through `AccountableYield::accrueAndProcess`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** When NAV is stale, `AccountableYield::onRequestRedeem` disables “instant fulfill” by forcing requests into the queue:

```solidity
canFulfill = liquidity >= assets && !_navIsStale();
```

However, `AccountableYield::accrueAndProcess` is publicly callable and is not gated by `whenNotStale`. It processes the withdrawal queue immediately:

```solidity
function accrueAndProcess() external ... {
    _accrueFees();
    usedAssets = _processAvailableWithdrawals();
    _updateDelinquentStatus();
}
```

As a result, a user can queue a redeem request and then immediately call `accrueAndProcess()` (potentially in the same transaction via a router/multicall) to have the request processed even while NAV is stale.

**Impact:** This undermines the intended protection of “no immediate withdrawals when NAV is stale.” Withdrawals can still be processed at the last known (stale) NAV-derived price, which may be economically incorrect during periods when NAV updates are unavailable.

**Recommended Mitigation:** Gate queue processing while NAV is stale (e.g., add `whenNotStale` to `accrueAndProcess()` and any other public entrypoints that trigger `_processAvailableWithdrawals()`, like `AccountableYield::repay`)


**Accountable:** Fixed in commit [`ddcbfa5`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/ddcbfa5faac90cc6e6ff3c1f1a0e754951363ba1)

**Cyfrin:** Verified. Both `repay` and `accrueAndProcess` now have the `whenNotStale` modifier.

## [M-23] Scaling `winningThreshold` incorrectly reduces randomness distribution
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** When a user has a boost that results in a >100% probability of winning, the contract adjusts `winningThreshold` to match `boostedTotalProbabilities` in [`Spin::_fulfillRandomness`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L534-L557):

```solidity
uint256 winningThreshold = _randomness % BASE_POINT;

// ...

if (boostedTotalProbabilities > BASE_POINT) {
    winningThreshold =
        (winningThreshold * boostedTotalProbabilities) /
        BASE_POINT;
}
```

The issue here is that `_randomness` is first scaled down to `BASE_POINT` before being scaled up to `boostedTotalProbabilities`. This process reduces the effective randomness (entropy) because some values in the original `_randomness` range will no longer be represented in the final `winningThreshold` after scaling. As a result, the final threshold may not be evenly distributed, potentially introducing bias.

Consider applying `_randomness` directly to `boostedTotalProbabilities` when the win probability exceeds 100%, ensuring no loss of entropy:

```diff
  if (boostedTotalProbabilities > BASE_POINT) {
-     winningThreshold =
-         (winningThreshold * boostedTotalProbabilities) /
-         BASE_POINT;

+     winningThreshold = _randomness % boostedTotalProbabilities;
  }
```

This preserves the full randomness range and ensures a more uniform distribution of possible winning thresholds.

**Linea:** Fixed in commit [`37a18ca`](https://github.com/Consensys/linea-hub/commit/37a18ca60b8e503643b5b6e996e9a0cd7c257ec2)

**Cyfrin:** Verified.

## [M-24] Remove obsolete return statements when using named return variables
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** Remove either the named return value or the `return` statement.

* [`BasisTradeVault::requestWithdraw`](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/BasisTradeVault.sol#L396-L404)
  ```solidity
  function requestWithdraw(uint256 assets) external returns (uint256 queuePosition) {
      // ...

      return requestRedeem(shares);
  }
  ```

* [BasisTradeVault::](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/BasisTradeVault.sol#L412-L444)
  ```solidity
  function requestRedeem(uint256 shares) public requirePocket returns (uint256 queuePosition) {
      // ...

      return queuePosition;
  }
  ```

* [`Pocket::exec`](https://github.com/buttonxyz/button-protocol/blob/9002f2b0d05ba80039bd942c809dbe5bc1a252c9/src/Pocket.sol#L94-L106)
  ```solidity
  function exec(address target, bytes calldata data) external onlyOwner returns (bytes memory result) {
      // ...

      return result;
  }
  ```

**Button:** Fixed in commit [`9d8ed75`](https://github.com/buttonxyz/button-protocol/commit/9d8ed75bd5ed4957c7b23f9b06ff362b7bb218a4)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-14] Incorrect event emission is possible in `AccountableAsyncRedeemVault::cancelRedeemRequest` flows
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** `cancelRedeemRequest()` takes "requestID" as input, but it is never used and never validated to be associated with the input controller address.

All cancellation flows (immediate/ async) work with the requestID of the controller address stored in `_requestIds[controller]`, but the input requestID is only used for event data in `CancelRedeemRequest()` and `CancelRedeemClaimable()` events.

Because this is never verified, caller can input any requestID and have it emitted in the events.

**Impact:** Incorrect event emission is possible, potentially leading to data corruption for the frontend and anyone else using this event data.

**Recommended Mitigation:** Remove the "requestID" parameter from the `cancelRedeemRequest()` function definition and simply use the existing requestID of the controller in event emission.

**Accountable:** Fixed in commits [`aa64491`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/aa64491b1ebe68375793efbc961a323ea739f58c) and [`0675c3d`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/0675c3de2f4eae3456470f04a2241c8f60255088).

**Cyfrin:** Verified. The redeem request of the controller is now used.

## [C-1] `AccountableAsyncRedeemVault::fulfillCancelRedeemRequest` can de-sync request data causing permanent DOS for queue processing
- Severity: `Critical`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** `fulfillCancelRedeemRequest()` function first finalises the cancellation of the redeeem request with input `requestID`, and then calls `_reduce()` to update the request state and `totalQueuedShares`.

```solidity
    function fulfillCancelRedeemRequest(address controller) public onlyOperatorOrStrategy {
        _fulfillCancelRedeemRequest(_requestIds[controller], controller);
        _reduce(controller, _vaultStates[controller].pendingRedeemRequest);
    }
```

The problem here is that it is using current value of `_vaultStates[controller].pendingRedeemRequest` in the `_reduce()` call, but it has been set to zero in `_fulfillCancelRedeemRequest()`.

This means `_reduce()` here will always be called with zero shares, and it does not revert when shares input is zero. But it corrupts the request struct and `totalQueuedShares` value.

The request will still exist with actual shares values, and create problems in usual batch processing of the queue.

One example of the resulting impact is this :
1. User X places a redeem request for 100 shares
2. User X cancels this redeem request
3. His request is not fulfilled instantly (this depends on the strategy)
4. Operator calls `fulfillCancelRedeemRequest()` to process this cancellation.
5. The call goes through properly. As a result [state.pendingRedeemRequest = 0] but the request state still has request.shares == 100 and other values. Also, the `_queue.nextRequestID` remains unchanged.
6. Now when batch processing proceeds via `processUpToShares()`, it is guaranteed that User X's requestID will also be processed (it is still in the queue from nextRequestID to lastRequestID) and when that happens, it will suffer a revert in `_processUptoShares()` => `_fulfillRedeemRequest()` because `state.pendingRedeemRequest` was set to == 0 in step 5.

```solidity
    function _fulfillRedeemRequest(uint128 requestId, address controller, uint256 shares, uint256 price)
        internal
        override
    {
        VaultState storage state = _vaultStates[controller];
        if (state.pendingRedeemRequest == 0) revert NoRedeemRequest();
        if (state.pendingRedeemRequest < shares) revert InsufficientAmount();
        if (state.pendingCancelRedeemRequest) revert RedeemRequestWasCancelled();
```


**Impact:** If this function is ever called, there will be a permanent de-sync between the values stored as per requestID data and the vaultState of the controller, which will interfere with queue processing in different ways.

The example showcased here is a critical DOS blocking queue processing permanently. This will happen for strategies that offer async cancellation processing, but since vault is expected to be compatible with this behavior, fixing this is critical.


**Recommended Mitigation:**
```solidity
    function fulfillCancelRedeemRequest(address controller) public onlyOperatorOrStrategy {

+++        uint256 pendingShares = state.pendingRedeemRequest;
               _fulfillCancelRedeemRequest(_requestIds[controller], controller);
---          _reduce(controller, _vaultStates[controller].pendingRedeemRequest);
+++        _reduce(controller, pendingShares);
    }
```

**Accountable:** Fixed in commit [`84946dd`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/84946dd49dd70f9f5dfe40184beb52b734362701)

**Cyfrin:** Verified. `pendingShares` now cached before fulfill and then passed as argument to `_reduce`.
