# lending / oracle-decimals

- Count: `2`
- Definition: oracle values from different feeds/scales are compared or consumed without normalization.

## [Malda][M-14] Mixed Price Oracle V4 decimal mismatch
- Severity: `Medium`
- Source: [Issue #945](https://github.com/sherlock-audit/2025-07-malda-judging/issues/945)
- Impact: `dos`, `value-mispricing`

### Detailed Content
- Summary: oracle aggregator compares API3 and eOracle prices directly although feeds can return different decimal precision.
- Root Cause: `_getLatestPrice` computes absolute delta and bps delta before normalizing feed scales.
- Trigger Conditions: one feed uses larger decimals; raw numeric delta appears inflated and branch logic disproportionately prefers one source.
- Impact Detail: wrong oracle branch selection and stale/delta checks can misbehave, leading to mispricing and potential DoS side effects.

### Fix Status
- `Fixed/Resolved in report`

## [Notional][M-12] `Pendle PTOracle._get PTRate` decimal assumption invalid
- Severity: `Medium`
- Source: [Issue #623](https://github.com/sherlock-audit/2025-06-notional-exponent-judging/issues/623)
- Impact: `value-mispricing`

### Detailed Content
- Summary: `PendlePTOracle._getPTRate` comment/logic assumed PT rate always `1e18`.
- Root Cause: `getPtToAssetRate` is `1e18`-scaled, but `getPtToSyRate` can be higher-scale in specific markets; code converts directly without normalization.
- Trigger Conditions: markets where SY rate decimals differ from assumed 18.
- Impact Detail: PT valuation is skewed, which propagates to collateral/pricing decisions.

### Fix Status
- `Fixed/Resolved in report`

## Cyfrin Fixed Issues (Merged)
- Count: `24`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] Attacker can extract value by buying and selling the seat
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Whenever a user buys a seat, they must pay `seat_price` in the currency token. The `seat_price` depends on the `perp_clients_count` at the time of purchase. If the `perp_clients_count` is higher, the user will pay more for the seat; if it is lower, the seat will cost less.

```rust
    pub fn get_place_buy_price(supply: u32, dec_factor: u32) -> Result<i64, DeriverseError> {
        let df = get_dec_factor(dec_factor);
        Ok(get_reserve(supply + 1, df)? - get_reserve(supply, df)?)
    }
```


The attacker can exploit this behavior and extract profit by creating a scenario where the user ends up paying a much higher seat price. For example, assuming a currency X with 6 decimals:

1. Initially, the `perp_clients_count` is 199,999.
2. The attacker buys 1,000 seats to profit later.
3. During user transaction, the `perp_clients_count` is 200,999, and the user pays a seat price of 26,030,289.
5. The attacker then sells the 1,000 seats and extracts a profit of 1,030,788.
6. If the attacker had not performed this attack, the user would have only needed to pay 24,999,501 for their seat.

No front-running is required. An attacker can pre-purchase seats and later sell them to extract the funds without using the instrument.



**Impact:** The attacker can extract user funds through this behavior, causing the user to pay more than expected.


**Recommended Mitigation:** Recommendation is to store the seat price the user originally paid and later when the user sells the seat return the exact same amount they paid at the time of purchase.

**Deriverse:** Fixed in commit [a80b0e](https://github.com/deriverse/protocol-v1/commit/a80b0ebf90f707d8e527cbcccce0790f35676d13).

**Cyfrin:** Verified.

## [M-2] Missing Signer and New Account Validation for `asset_token_program_acc` in `new_instrument`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `new_instrument` instruction lacks validation checks for `asset_token_program_acc` when creating a new asset token account. Unlike `new_base_crncy` which explicitly validates that the program token account is a signer and a new account, `new_instrument` omits these checks, leading to inconsistent error handling.

In new_instrument.rs, when `is_new_account(asset_token_acc)` is true, the code directly calls `TokenState::create_token` which internally calls `create_programs_token_account`. This function requires `asset_token_program_acc` to be a signer because it performs system operations:

```rust
    if is_new_account(asset_token_acc) {
        let decimals = *asset_mint
            .data
            .borrow()
            .get(MINT_DECIMALS_OFFSET)
            .ok_or_else(|| drv_err!(DeriverseErrorKind::InvalidClientDataFormat))?
            as u32;

        if !(MIN_DECS_COUNT..=MAX_DECS_COUNT).contains(&decimals) {
            bail!(DeriverseErrorKind::InvalidDecsCount {
                decs_count: decimals,
                min: MIN_DECS_COUNT,
                max: MAX_DECS_COUNT,
                token_address: *asset_mint.key,
            });
        }

        #[cfg(feature = "native_mint_2022")]
        if *asset_mint.key == spl_token::native_mint::ID {
            bail!(LegacyNativeMintNotSupported);
        }
        #[cfg(not(feature = "native_mint_2022"))]
        if *asset_mint.key == spl_token_2022::native_mint::ID {
            bail!(Token2022NativeMintNotSupported);
        }

        TokenState::create_token(
            root_state,
            asset_mint,
            asset_token_acc,
            drvs_auth_acc,
            &drvs_auth,
            bump_seed,
            program_id,
            asset_token_program_acc,
            token_program,
            signer,
            decimals,
        )?;
```

However, new_instrument does not validate:
- Whether `asset_token_program_acc.is_signer` is true
- Whether `asset_token_program_acc` is a new account (`is_new_account(asset_token_program_acc)`)

This is required, however, in the comment, indicating that when creating a new token, this account should be a signer.

```rust
///
/// [*Incorrect Price Validation When Creating `NewInstrumentData` Struct during `NewInstrumentInstruction` instruction*](#incorrect-price-validation-when-creating-newinstrumentdata-struct-during-newinstrumentinstruction-instruction) - Asset Tokens Program Account `[SPL, if new_token signer]` - Spl token account
///
```

In contrast, `new_base_crncy.rs` explicitly performs these validations:

```rust
if is_new_account(token_acc) {
    if !is_new_account(program_acc) {
        bail!(InvalidNewAccount { ... });
    }
    if !program_acc.is_signer {
        return Err(drv_err!(MustBeSigner { ... }));
    }
    // ...
}
```

Note: similar works for `new_root_account`, do we also need to check the signer for that?

```rust
///
/// [*typo error in variables*](#typo-error-in-variables) - Deriverse Program Account `[SPL]` - Spl token account
///
```

**Impact:**
- Inconsistent error handling: different validation patterns across similar instructions, causing failures occur during CPI calls rather than early validation

**Recommended Mitigation:** Add explicit validation checks in new_instrument.rs when `is_new_account(asset_token_acc)` is true, matching the pattern in `new_base_crncy.rs`

**Deriverse:** Fixed in commit [96f4e923](https://github.com/deriverse/protocol-v1/commit/96f4e92343fce5610ed89a3063bfed053bc578e5).

**Cyfrin:** Verified.

## [M-3] Rounding Error Accumulation in Partial Order Fills Leads to Unfair Cost Distribution
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Note:**
This finding was submitted after careful consideration. The impact is negligible in practice, as it only manifests when an order is partially filled multiple times, causing tiny rounding errors to accumulate. However, it is still worth documenting, as it represents a systematic bias that could potentially be addressed in documentation or future improvements.

**Description:** When an order is partially filled multiple times, rounding errors from the `trade_sum` function accumulate in the order's remaining `sum` field. The final fill receives the accumulated rounding errors, causing the last trader to pay more than they should based on the actual traded quantity.

The vulnerability exists in the `fill` function of the spot trading engine. When an order is created, the total currency value is calculated using `trade_sum(price, qty)` and stored in `order.sum`:

```rust
// Line 643: Order creation
let order_sum = self.trade_sum(price, qty)?;
// ...
sum: order_sum,  // Stored in order
```


The `trade_sum` function performs floating-point multiplication with `rdf` (rounding division factor) and truncates to `i64`:

```rust
// Lines 157-158: rdf calculation
let df = state.header.dec_factor as f64;
let rdf = 1f64 / df;  // rdf is typically a decimal (e.g., 0.1, 0.01, 0.001)

// Lines 277-284: trade_sum function
fn trade_sum(&self, a: i64, b: i64) -> Result<i64, DeriverseError> {
    let sum = (a as f64 * b as f64) * self.rdf;  // Floating-point multiplication with rdf
    // ...
    Ok(sum as i64)  // Truncation from f64 to i64 causes rounding errors
}
```


**Root Cause of Rounding Errors:**
The rounding errors occur because:
1. `rdf = 1.0 / dec_factor`, where `dec_factor = 10^n` (a power of 10 based on token decimal differences)
2. `rdf` could be a decimal fraction (e.g., 0.1, 0.01, 0.001), requiring floating-point arithmetic
3. The multiplication `(a * b) * rdf` in floating-point can produce results that are not exactly representable as integers
4. The conversion from `f64` to `i64` truncates the fractional part, causing precision loss
5. Without `rdf` (i.e., if `rdf = 1.0`), the calculation would be exact integer arithmetic with no rounding errors


When an order is partially filled (line 1187), the code recalculates the currency value using `trade_sum`:

```rust
// Lines 1178-1188
let (traded_qty, traded_crncy, last) = if order_qty <= *remaining_qty {
    (order_qty, order.sum(), false)  // Full fill uses stored sum
} else {
    (*remaining_qty, self.trade_sum(*remaining_qty, px)?, true)  // Partial fill recalculates
};
```


Then, when `last = true` (partial fill), the code decrements the order's sum:

```rust
// Lines 1265-1267
if last {
    order.decr_qty(traded_qty).map_err(|err| drv_err!(err))?;
    order.decr_sum(traded_crncy).map_err(|err| drv_err!(err))?;  // Subtracts recalculated value
    // ...
}
```


**The Problem:**
1. The presence of `rdf` (a decimal fraction) in `trade_sum` causes floating-point precision issues when converting to `i64`.
2. Each partial fill recalculates `trade_sum(remaining_qty, px)`, which introduces rounding errors due to `f64→i64` truncation in the presence of `rdf`.
3. The recalculated value is subtracted from `order.sum`, causing rounding errors to accumulate in the remaining `sum`.
4. When the order is fully filled, the remaining `order.sum` may not equal `trade_sum(remaining_qty, px)` but instead contains all accumulated rounding errors from previous partial fills.


**Example Scenario:**
Assume `rdf = 0.1` (i.e., `dec_factor = 10`) and price = 99:
- Order: qty=100, price=99, rdf=0.1
- Original sum: `trade_sum(100, 99) = (100 * 99) * 0.1 = 990.0` → `990` (exact)
- First partial fill (33 qty): `traded_crncy = trade_sum(33, 99) = (33 * 99) * 0.1 = 326.7` → `326` (truncated, loses 0.7)
- Remaining sum: `990 - 326 = 664` (should be 663.3, but stored as integer)
- Second partial fill (33 qty): `traded_crncy = trade_sum(33, 99) = 326.7` → `326` (truncated, loses 0.7)
- Remaining sum: `664 - 326 = 338` (should be 337.3, but stored as integer)
- Final fill (34 qty):
  - Expected: `trade_sum(34, 99) = (34 * 99) * 0.1 = 336.6` → `336`
  - Actual received: `order.sum = 338` (contains accumulated rounding errors: 0.7 + 0.7 = 1.4)
  - The final trader receives `338` instead of `336`, paying `2` more than they should

**Impact:** **Unfair Cost Distribution**: The last trader to fill a partially-filled order bears the cost of all accumulated rounding errors from previous partial fills.

**Recommended Mitigation:** This may be a design choice, and leaving it as-is is acceptable. However, it should be clearly documented that rounding errors are unavoidable when using floating-point arithmetic with `rdf`, and the current implementation accumulates these errors to the final partial fill,
Given the negligible impact and the fact that rounding errors are unavoidable (the question is only who bears them), **the current design choice is acceptable as long as it is properly documented.**

**Deriverse:** Fixed in commit [058c856](https://github.com/deriverse/protocol-v1/commit/058c8565a6394ac0ce0cba8841c523db51d5f8a5).

**Cyfrin:** Verified. Added documents.

## [M-4] `Lib Helpers.convert Decimals To` favours the user on a exact-out mint and burn for certain collateral decimals
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** Function `convertToDecimals` favours user on the exact-out mint path of `Swapper::swap`. It always rounds down when converting from higher decimals to lower decimals

```solidity
function _quoteMintExactOutput(
...
@@> amountIn = LibHelpers.convertDecimalTo((amountIn * BASE_18) / oracleValue, 18, collatInfo.decimals);
```

For the exact-out burn path it is collaterals with decimals higher than 18 that get a small discount. Here

```solidity
function _quoteBurnExactOutput(
...
@@> amountIn = Math.mulDiv(LibHelpers.convertDecimalTo(amountOut, collatInfo.decimals, 18), oracleValue, ratio);
```
**Impact:** The rounding error of a mint with low decimals violates the maxim "rounding should always favour the protocol".

In this case it gives a negligible advantage to the user and no way to exploit this in a meaningful way has been found.

However, the addition of extra features to the codebase may allow exploitation in the future.

**Proof of Concept:** See tests `test_cyfrin_[mint/burn]ExactOutput_[low/high]Decimals_userFavorableRounding` in tests/units/parallel-protocolSwapperDecimalRounding.t.sol
```solidity

// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.28;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { console2 } from "@forge-std/console2.sol";
import { AggregatorV3Interface } from "contracts/interfaces/external/chainlink/AggregatorV3Interface.sol";
import "contracts/utils/Constants.sol";
import "contracts/parallelizer/Storage.sol";

import "../Fixture.sol";
import { MockChainlinkOracle } from "../mock/MockChainlinkOracle.sol";
import { MockTokenPermit } from "../mock/MockTokenPermit.sol";
import { DecimalString } from "../utils/DecimalString.sol";

contract CyfrinSwapperDecimalRoundingTest is Fixture {
  using DecimalString for uint256;

  IERC20 internal eurZ;
  AggregatorV3Interface internal oracleZ;

  function setUp() public override {
    super.setUp();

    // Normalize oracles to 1.0 (8 decimals) to isolate rounding from price effects.
    MockChainlinkOracle(address(oracleA)).setLatestAnswer(100_000_000);
    MockChainlinkOracle(address(oracleY)).setLatestAnswer(100_000_000);

    // Zero mint/burn fees on both collaterals so the only nonlinearity is decimal rounding.
    uint64[] memory xFeeMint = new uint64[](1);
    int64[] memory yFeeMint = new int64[](1);
    xFeeMint[0] = 0;
    yFeeMint[0] = 0;
    uint64[] memory xFeeBurn = new uint64[](1);
    int64[] memory yFeeBurn = new int64[](1);
    xFeeBurn[0] = uint64(BASE_9);
    yFeeBurn[0] = 0;

    vm.startPrank(guardian);
    parallelizer.setFees(address(eurA), xFeeMint, yFeeMint, true);
    parallelizer.setFees(address(eurA), xFeeBurn, yFeeBurn, false);
    parallelizer.setFees(address(eurY), xFeeMint, yFeeMint, true);
    parallelizer.setFees(address(eurY), xFeeBurn, yFeeBurn, false);
    vm.stopPrank();

    // Add a 27-decimal collateral for the exact input test.
    eurZ = IERC20(address(new MockTokenPermit("EUR_Z", "EUR_Z", 27)));
    oracleZ = AggregatorV3Interface(address(new MockChainlinkOracle()));
    MockChainlinkOracle(address(oracleZ)).setLatestAnswer(100_000_000);

    vm.startPrank(governor);
    parallelizer.addCollateral(address(eurZ));
    _setOracleStable(address(eurZ), address(oracleZ));
    vm.stopPrank();

    vm.startPrank(guardian);
    parallelizer.setFees(address(eurZ), xFeeMint, yFeeMint, true);
    parallelizer.setFees(address(eurZ), xFeeBurn, yFeeBurn, false);
    parallelizer.setStablecoinCap(address(eurZ), type(uint256).max);
    parallelizer.togglePause(address(eurZ), ActionType.Mint);
    parallelizer.togglePause(address(eurZ), ActionType.Burn);
    vm.stopPrank();
  }

  function _setOracleStable(address collateral, address oracle) internal {
    AggregatorV3Interface[] memory circuitChainlink = new AggregatorV3Interface[](1);
    uint32[] memory stalePeriods = new uint32[](1);
    uint8[] memory circuitChainIsMultiplied = new uint8[](1);
    uint8[] memory chainlinkDecimals = new uint8[](1);
    circuitChainlink[0] = AggregatorV3Interface(oracle);
    stalePeriods[0] = 1 hours;
    circuitChainIsMultiplied[0] = 1;
    chainlinkDecimals[0] = 8;
    OracleQuoteType quoteType = OracleQuoteType.UNIT;
    bytes memory readData =
      abi.encode(circuitChainlink, stalePeriods, circuitChainIsMultiplied, chainlinkDecimals, quoteType);
    bytes memory targetData;
    parallelizer.setOracle(
      collateral,
      abi.encode(
        OracleReadType.CHAINLINK_FEEDS, OracleReadType.STABLE, readData, targetData, abi.encode(uint128(0), uint128(0))
      )
    );
  }

  function _mintExactOutputAndGetSpent(address tokenIn, address owner, uint256 amountOut)
    internal
    returns (uint256 spent)
  {
    deal(tokenIn, owner, type(uint128).max); // really large amount
    uint256 beforeBal = IERC20(tokenIn).balanceOf(owner);
    vm.startPrank(owner);
    IERC20(tokenIn).approve(address(parallelizer), type(uint256).max);
    parallelizer.swapExactOutput(amountOut, type(uint256).max, tokenIn, address(tokenP), owner, block.timestamp * 2);
    vm.stopPrank();
    spent = beforeBal - IERC20(tokenIn).balanceOf(owner);
  }

  function test_cyfrin_mintExactOutput_lowDecimals_userFavorableRounding() external {
    // Maximize rounding delta: choose amountOut with remainder (1e12 - 1) when divided by 1e12.
    // This makes the 6-decimal path floor by almost 1e12 units (in 18-decimal terms).
    uint256 amountOut = 1e24 + (1e12 - 1);

    uint256 quote6 = parallelizer.quoteOut(amountOut, address(eurA), address(tokenP));
    uint256 spent6 = _mintExactOutputAndGetSpent(address(eurA), alice, amountOut);

    uint256 quote18 = parallelizer.quoteOut(amountOut, address(eurY), address(tokenP));
    uint256 spent18 = _mintExactOutputAndGetSpent(address(eurY), alice, amountOut);

    // Normalize 6-decimals collateral into 18-decimals for apples-to-apples comparison.
    uint256 cost6In18 = spent6 * 1e12;
    uint256 cost18In18 = spent18;

    console2.log("Mint exact output comparison (same amountOut):");
    console2.log(string.concat("amountOut (TokenP, 18 dec) = ", amountOut.formatFixed(18)));
    console2.log(string.concat("collateral 6-dec (eurA) spent = ", spent6.formatFixed(6)));
    console2.log(string.concat("collateral 18-dec (eurY) spent = ", spent18.formatFixed(18)));
    console2.log(string.concat("eurA cost normalized to 18 dec = ", cost6In18.formatFixed(18)));
    console2.log(string.concat("eurY cost (18 dec) = ", cost18In18.formatFixed(18)));
    console2.log(string.concat("rounding delta (18 dec units) = ", (cost18In18 - cost6In18).formatFixed(18)));

    // Rounding in convertDecimalTo(18 -> 6) floors, making the 6-decimals mint slightly cheaper.
    assertLt(cost6In18, cost18In18);
  }


  function test_cyfrin_burnExactOutput_highDecimals_userFavorableRounding() external {
    // Choose amountOut for 27-dec collateral with remainder (1e9 - 1) to maximize rounding down
    // when converting 27 -> 18, reducing the TokenP required.
    uint256 amountOut18 = 1_000_000e18;
    uint256 amountOut27 = amountOut18 * 1e9 + (1e9 - 1);

    // Mint TokenP from each collateral to seed normalizedStables for burns.
    _mintExactInput(alice, address(eurZ), amountOut27, 0);
    _mintExactInput(alice, address(eurY), amountOut18, 0);

    // Fund the Parallelizer with collateral to pay out on burn.
    deal(address(eurY), address(parallelizer), amountOut18);
    deal(address(eurZ), address(parallelizer), amountOut27);

    uint256 expectedIn27 = amountOut18; // floor(amountOut27 / 1e9)

    vm.startPrank(alice);
    uint256 in27 =
      parallelizer.swapExactOutput(amountOut27, type(uint256).max, address(tokenP), address(eurZ), alice, block.timestamp * 2);
    uint256 in18 =
      parallelizer.swapExactOutput(amountOut18, type(uint256).max, address(tokenP), address(eurY), alice, block.timestamp * 2);
    vm.stopPrank();

    uint256 extraOut27 = amountOut27 - amountOut18 * 1e9;

    console2.log("Exact output burn comparison (27-dec vs 18-dec collateral):");
    console2.log(string.concat("amountOut27 (EUR_Z, 27 dec) = ", amountOut27.formatFixed(27)));
    console2.log(string.concat("amountOut18 (EUR_Y, 18 dec) = ", amountOut18.formatFixed(18)));
    console2.log(string.concat("tokenP in for 27-dec collateral = ", in27.formatFixed(18)));
    console2.log(string.concat("tokenP in for 18-dec collateral = ", in18.formatFixed(18)));
    console2.log(string.concat("extra collateral gained (27-dec units) = ", extraOut27.formatFixed(27)));

    // 27-dec path rounds down in 27 -> 18 conversion, so it needs the same TokenP
    // as the 18-dec path while delivering slightly more collateral.
    assertEq(in27, expectedIn27);
    assertEq(in18, amountOut18);
    assertEq(in27, in18);
    assertEq(extraOut27, 1e9 - 1);
  }

  function test_cyfrin_exactInput_27Decimals_roundingCanWasteInput() external {
    // Choose an amountIn with remainder (1e9 - 1) when divided by 1e9 to maximize rounding loss
    // in the 27-decimal -> 18-decimal conversion.
    uint256 amountIn27 = 1e27 + (1e9 - 1);
    uint256 amountIn18 = 1e18;

    deal(address(eurZ), alice, amountIn27);
    deal(address(eurY), alice, amountIn18);

    vm.startPrank(alice);
    eurZ.approve(address(parallelizer), type(uint256).max);
    eurY.approve(address(parallelizer), type(uint256).max);
    uint256 out27 = parallelizer.swapExactInput(amountIn27, 0, address(eurZ), address(tokenP), alice, block.timestamp * 2);
    uint256 out18 = parallelizer.swapExactInput(amountIn18, 0, address(eurY), address(tokenP), alice, block.timestamp * 2);
    vm.stopPrank();

    uint256 idealOut27 = (amountIn27 + (1e9 - 1)) / 1e9;
    uint256 roundingLoss = idealOut27 - out27;

    console2.log("Exact input comparison (27-dec vs 18-dec collateral):");
    console2.log(string.concat("amountIn27 (EUR_Z, 27 dec) = ", amountIn27.formatFixed(27)));
    console2.log(string.concat("amountIn18 (EUR_Y, 18 dec) = ", amountIn18.formatFixed(18)));
    console2.log(string.concat("out27 (TokenP, 18 dec) = ", out27.formatFixed(18)));
    console2.log(string.concat("out18 (TokenP, 18 dec) = ", out18.formatFixed(18)));
    console2.log(string.concat("idealOut27 (ceil, 18 dec) = ", idealOut27.formatFixed(18)));
    console2.log(string.concat("roundingLoss (TokenP wei) = ", roundingLoss.formatFixed(18)));

    // The 27-decimal path floors, so it loses up to 1 TokenP wei vs a ceiling conversion.
    assertEq(out27 + roundingLoss, idealOut27);
    assertEq(roundingLoss, 1);
  }

}
```

```
[PASS] test_cyfrin_mintExactOutput_lowDecimals_userFavorableRounding() (gas: 735829)
Logs:
  Mint exact output comparison (same amountOut):
  amountOut (TokenP, 18 dec) = 1,000,000.000000999999999999
  collateral 6-dec (eurA) spent = 1,000,000.000000
  collateral 18-dec (eurY) spent = 1,000,000.000000999999999999
  eurA cost normalized to 18 dec = 1,000,000.000000000000000000
  eurY cost (18 dec) = 1,000,000.000000999999999999
  rounding delta (18 dec units) = 0.000000999999999999```
```

```
[PASS] test_cyfrin_burnExactOutput_highDecimals_userFavorableRounding() (gas: 1288290)
Logs:
  Exact output burn comparison (27-dec vs 18-dec collateral):
  amountOut27 (EUR_Z, 27 dec) = 1,000,000.000000000000000000999999999
  amountOut18 (EUR_Y, 18 dec) = 1,000,000.000000000000000000
  tokenP in for 27-dec collateral = 1,000,000.000000000000000000
  tokenP in for 18-dec collateral = 1,000,000.000000000000000000
  extra collateral gained (27-dec units) = 0.000000000000000000999999999
```

**Recommended Mitigation:** Modify `convertDecimalsTo` to include a parameter for the rounding direction and use appropriately.

**Parallel:** Fixed in commit [f60101a](https://github.com/parallel-protocol/parallel-parallelizer/commit/f60101a455c9215c49a7ea70551da7d31ca5ca76).

**Cyfrin:** Verified. `LibHelpers.convertDecimalsTo` now rounds towards the specified direction when converting from higher decimals to lower decimals.

## [M-5] `Lib Surplus::_compute Collateral Surplus` doesn't account for `surplus Buffer Ratio > 100%`
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** `LibSurplus::_computeCollateralSurplus` treats as surplus everything above 100% CR:
```solidity
  function _computeCollateralSurplus(address collateral)
    internal
    view
    returns (uint256 collateralSurplus, uint256 stableSurplus)
  {
    ParallelizerStorage storage ts = s.transmuterStorage();
    Collateral storage collatInfo = ts.collaterals[collateral];
    uint256 currentCollateralBalance;
    if (collatInfo.isManaged > 0) {
      (, currentCollateralBalance) = LibManager.totalAssets(collatInfo.managerData.config);
    } else {
      currentCollateralBalance = IERC20(collateral).balanceOf(address(this));
    }
    uint256 oracleValue = LibOracle.readMint(collatInfo.oracleConfig);
    uint256 totalCollateralValue =
      LibHelpers.convertDecimalTo(oracleValue * currentCollateralBalance, 18 + collatInfo.decimals, 18);
    uint256 stablesBacked = (uint256(collatInfo.normalizedStables) * ts.normalizer) / BASE_27;
    if (totalCollateralValue <= stablesBacked) revert ZeroSurplusAmount();
@>  stableSurplus = totalCollateralValue - stablesBacked;
@>  collateralSurplus = LibHelpers.convertDecimalTo((stableSurplus * BASE_18) / oracleValue, 18, collatInfo.decimals);
  }
```

However in the end it uses value `ts.surplusBufferRatio` instead of hardcoded 100% CR:
```solidity
  function processSurplus(
    address collateral,
    uint256 maxCollateralAmount
  )
    external
    restricted
    returns (uint256 collateralSurplus, uint256 stableSurplus, uint256 issuedAmount)
  {
    ...
    issuedAmount = ISwapper(address(this))
      .swapExactInput(
        collateralSurplus, minExpectedAmount, collateral, address(ts.tokenP), address(this), block.timestamp
      );
    (uint64 collatRatio,,,,) = LibGetters.getCollateralRatio();
@>  if (collatRatio < ts.surplusBufferRatio) revert Undercollateralized();
  }
```

Suppose following example:
1) Collateral DAI is 105e18, USDP minted is 100e18, `surplusBufferRatio` is 101%
2) It calculates surplus collateral 5e18 DAI, so will mint extra 5e18 USDP
3) In the end CR = 100%
4) But `surplusBufferRatio = 101%`, so transaction reverts

**Impact:** `Surplus::processSurplus()` will revert in case `surplusBufferRatio > 100%`. Check will always pass if `surplusBufferRatio < 100%`, so currently there is no sense in having variable instead of hardcoded 100%.

**Recommended Mitigation:** Fix consists of 2 parts:
1) Calculate per-collateral surplus above `surplusBufferRatio` instead of `100%`. Basically it's solution to equation `totalCollateralValue / (stablesBacked + X) = surplusBufferRatio`. For example in above scenario correct surplus is `3.96e18 USDP`. In the end `CR = 105 / (100 + 3.96) = 101% == surplusBufferRatio`.
2) However above fix still can revert in certain edge case when other collateral has `CR < surplusBufferRatio`. Suppose following example:
- `USDC = 115`, `USDP = 100`; `USDT = 105`, `USDP = 100`; `surplusBufferRatio = 110%`
- Global `CR = (115 + 105) / 200 = 110%`, which is exactly `110%`. It means there is no surplus.
- But it will calculate surplus `4.54` for USDC. Therefore reverts in the end.

So it should cap per-collateral surplus by global extractable surplus. It can be implemented either onchain or offchain via sending specific `maxCollateralAmount`.

**Parallel:** Fixed in commits [3d5bb19](https://github.com/parallel-protocol/parallel-parallelizer/commit/3d5bb19745d24c9178ae5ca716360c90cb9cf54d), [27e8857](https://github.com/parallel-protocol/parallel-parallelizer/commit/27e88579aec725e6dee67150ff4144db757e03ca) && [60fec2c](https://github.com/parallel-protocol/parallel-parallelizer/commit/60fec2cba723dc47984d3b8b8e000cb5c86c3073)

**Cyfrin:** Verified. Surplus per collateral is now calculated accounting for the `surplusBufferRatio` and considers the global collateralRatio. Calculated surplus ensures both, the per-collateral collateralRatio as well as global collateral ratio to remain above the `surplusBufferRatio`.

\clearpage

## [M-6] In zero-fee case, flashloan can result in a few wei profit
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** This is issue is placeholder for: https://github.com/parallel-protocol/parallel-core/blob/audit/100proof/Parallel-Parallelizer/tests/fuzz/parallel-protocolFlashloanRedeemPiecewiseMint.t.sol and leverages Issue [*`LibHelpers.convertDecimalsTo` favours the user on a exact-out mint and burn for certain collateral decimals*](#libhelpersconvertdecimalsto-favours-the-user-on-a-exactout-mint-and-burn-for-certain-collateral-decimals).
```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.28;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import { ITokenP } from "contracts/interfaces/ITokenP.sol";
import { IParallelizer } from "contracts/interfaces/IParallelizer.sol";

import "../Fixture.sol";

/// @dev Minimal ERC-3156 interfaces (avoid depending on OZ interfaces in this repo).
interface IERC3156FlashBorrower {
  function onFlashLoan(
    address initiator,
    address token,
    uint256 amount,
    uint256 fee,
    bytes calldata data
  )
    external
    returns (bytes32);
}

interface IERC3156FlashLender {
  function maxFlashLoan(address token) external view returns (uint256);
  function flashFee(address token, uint256 amount) external view returns (uint256);
  function flashLoan(IERC3156FlashBorrower receiver, address token, uint256 amount, bytes calldata data)
    external
    returns (bool);
}

/// @dev Flash lender that mints principal, pulls back principal+fee via transferFrom, then burns principal.
/// This matches the mechanics of `FlashParallelToken` (principal is minted/burned, lender keeps fees).
contract FlashLenderMock is IERC3156FlashLender {
  bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

  ITokenP public immutable tokenP;

  uint256 public maxBorrowable;
  uint256 public flatFee; // simplest fee model for fuzzing

  constructor(ITokenP _tokenP) {
    tokenP = _tokenP;
  }

  function setParams(uint256 _maxBorrowable, uint256 _flatFee) external {
    maxBorrowable = _maxBorrowable;
    flatFee = _flatFee;
  }

  function maxFlashLoan(address token) external view returns (uint256) {
    return token == address(tokenP) ? maxBorrowable : 0;
  }

  function flashFee(address token, uint256 /*amount*/ ) external view returns (uint256) {
    require(token == address(tokenP), "unsupported token");
    return flatFee;
  }

  function flashLoan(IERC3156FlashBorrower receiver, address token, uint256 amount, bytes calldata data)
    external
    returns (bool)
  {
    require(token == address(tokenP), "unsupported token");
    require(amount <= maxBorrowable, "too big");

    uint256 fee = flatFee;

    tokenP.mint(address(receiver), amount);
    require(receiver.onFlashLoan(msg.sender, token, amount, fee, data) == CALLBACK_SUCCESS, "bad callback");

    // Repay principal+fee to the lender, then burn the principal minted for the loan.
    IERC20(token).transferFrom(address(receiver), address(this), amount + fee);
    tokenP.burnSelf(amount, address(this));
    return true;
  }
}

/// @dev Borrower that tries the sequence:
/// 1) redeem all borrowed tokenP for collateral
/// 2) piecewise mint exact output to get back amount+fee with minimal collateral
/// 3) keep any leftover collateral/tokenP as profit
contract RedeemPiecewiseMintBorrower is IERC3156FlashBorrower {
  bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

  IParallelizer public immutable parallelizer;
  ITokenP public immutable tokenP;
  FlashLenderMock public immutable lender;

  address[] public collaterals; // ordered by preference (low decimals first)

  constructor(IParallelizer _parallelizer, ITokenP _tokenP, FlashLenderMock _lender, address[] memory _collaterals) {
    parallelizer = _parallelizer;
    tokenP = _tokenP;
    lender = _lender;
    collaterals = _collaterals;

    for (uint256 i; i < _collaterals.length; ++i) {
      IERC20(_collaterals[i]).approve(address(_parallelizer), type(uint256).max);
    }
    IERC20(address(_tokenP)).approve(address(_parallelizer), type(uint256).max);
  }

  function onFlashLoan(
    address,
    address token,
    uint256 amount,
    uint256 fee,
    bytes calldata data
  )
    external
    returns (bytes32)
  {
    require(msg.sender == address(lender), "only lender");
    require(token == address(tokenP), "wrong token");

    (uint8 chunks, bytes32 salt) = abi.decode(data, (uint8, bytes32));
    if (chunks == 0) chunks = 1;
    if (chunks > 24) chunks = 24;

    // Redeem all borrowed tokenP into collateral.
    (address[] memory tokens,) = parallelizer.quoteRedemptionCurve(amount);
    uint256[] memory minAmountOuts = new uint256[](tokens.length);
    parallelizer.redeem(amount, address(this), block.timestamp * 2, minAmountOuts);

    // Piecewise mint exact output of stablecoins to repay (amount + fee).
    uint256 remainingOut = amount + fee;
    for (uint256 i; i < chunks; ++i) {
      uint256 chunksLeft = chunks - i;
      uint256 chunkOut;
      if (chunksLeft == 1) {
        chunkOut = remainingOut;
      } else {
        // 1..2x(avg) to exercise rounding paths while keeping progress.
        uint256 avg = remainingOut / chunksLeft;
        uint256 r = uint256(keccak256(abi.encodePacked(salt, i, remainingOut)));
        uint256 span = avg == 0 ? remainingOut : (avg * 2);
        chunkOut = 1 + (r % (span == 0 ? remainingOut : span));
        if (chunkOut > remainingOut - (chunksLeft - 1)) chunkOut = remainingOut - (chunksLeft - 1);
      }

      bool minted;
      // Prefer low-decimal collaterals to maximize any rounding benefit.
      for (uint256 c; c < collaterals.length && !minted; ++c) {
        address collateral = collaterals[c];
        uint256 bal = IERC20(collateral).balanceOf(address(this));
        if (bal == 0) continue;

        uint256 needIn = parallelizer.quoteOut(chunkOut, collateral, address(tokenP));
        if (needIn == 0 || needIn > bal) continue;

        // Mint exact stable output.
        parallelizer.swapExactOutput(chunkOut, needIn, collateral, address(tokenP), address(this), block.timestamp * 2);
        minted = true;
      }
      require(minted, "cannot mint repay chunk");
      remainingOut -= chunkOut;
    }

    // Approve repayment to lender.
    IERC20(address(tokenP)).approve(address(lender), amount + fee);
    return CALLBACK_SUCCESS;
  }
}

/// @dev Borrower that tries the sequence:
/// 1) burn all borrowed tokenP into one chosen collateral via swapExactInput
/// 2) piecewise mint exact output to get back amount+fee with minimal collateral
/// 3) keep any leftover collateral/tokenP as profit
contract BurnPiecewiseMintBorrower is IERC3156FlashBorrower {
  bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

  IParallelizer public immutable parallelizer;
  ITokenP public immutable tokenP;
  FlashLenderMock public immutable lender;

  address[] public collaterals; // ordered by preference (low decimals first)

  constructor(IParallelizer _parallelizer, ITokenP _tokenP, FlashLenderMock _lender, address[] memory _collaterals) {
    parallelizer = _parallelizer;
    tokenP = _tokenP;
    lender = _lender;
    collaterals = _collaterals;

    for (uint256 i; i < _collaterals.length; ++i) {
      IERC20(_collaterals[i]).approve(address(_parallelizer), type(uint256).max);
    }
    IERC20(address(_tokenP)).approve(address(_parallelizer), type(uint256).max);
  }

  function onFlashLoan(
    address,
    address token,
    uint256 amount,
    uint256 fee,
    bytes calldata data
  )
    external
    returns (bytes32)
  {
    require(msg.sender == address(lender), "only lender");
    require(token == address(tokenP), "wrong token");

    (uint8 chunks, bytes32 salt, uint8 burnIndex) = abi.decode(data, (uint8, bytes32, uint8));
    if (chunks == 0) chunks = 1;
    if (chunks > 24) chunks = 24;

    address burnCollateral = collaterals[burnIndex % collaterals.length];

    // Burn all borrowed tokenP into the chosen collateral.
    uint256 out = parallelizer.quoteIn(amount, address(tokenP), burnCollateral);
    require(out > 0, "cannot burn");
    parallelizer.swapExactInput(amount, 0, address(tokenP), burnCollateral, address(this), block.timestamp * 2);

    // Piecewise mint exact output of stablecoins to repay (amount + fee).
    uint256 remainingOut = amount + fee;
    for (uint256 i; i < chunks; ++i) {
      uint256 chunksLeft = chunks - i;
      uint256 chunkOut;
      if (chunksLeft == 1) {
        chunkOut = remainingOut;
      } else {
        // 1..2x(avg) to exercise rounding paths while keeping progress.
        uint256 avg = remainingOut / chunksLeft;
        uint256 r = uint256(keccak256(abi.encodePacked(salt, i, remainingOut)));
        uint256 span = avg == 0 ? remainingOut : (avg * 2);
        chunkOut = 1 + (r % (span == 0 ? remainingOut : span));
        if (chunkOut > remainingOut - (chunksLeft - 1)) chunkOut = remainingOut - (chunksLeft - 1);
      }

      bool minted;
      for (uint256 c; c < collaterals.length && !minted; ++c) {
        address collateral = collaterals[c];
        uint256 bal = IERC20(collateral).balanceOf(address(this));
        if (bal == 0) continue;

        uint256 needIn = parallelizer.quoteOut(chunkOut, collateral, address(tokenP));
        if (needIn == 0 || needIn > bal) continue;

        parallelizer.swapExactOutput(chunkOut, needIn, collateral, address(tokenP), address(this), block.timestamp * 2);
        minted = true;
      }
      require(minted, "cannot mint repay chunk");
      remainingOut -= chunkOut;
    }

    // Approve repayment to lender.
    IERC20(address(tokenP)).approve(address(lender), amount + fee);
    return CALLBACK_SUCCESS;
  }
}

contract FlashloanRedeemPiecewiseMintFuzzTest is Fixture {
  FlashLenderMock internal lender;
  RedeemPiecewiseMintBorrower internal borrower;
  RedeemPiecewiseMintBorrower internal borrowerHighDecFirst;
  RedeemPiecewiseMintBorrower internal borrowerOnlyY;

  function setUp() public override {
    super.setUp();

    lender = new FlashLenderMock(tokenP);

    address[] memory cols = new address[](3);
    // Prefer low decimals first.
    cols[0] = address(eurA); // 6 decimals
    cols[1] = address(eurB); // 12 decimals
    cols[2] = address(eurY); // 18 decimals

    borrower = new RedeemPiecewiseMintBorrower(parallelizer, tokenP, lender, cols);

    // Prefer high decimals first (more precise), then fall back.
    address[] memory colsHigh = new address[](3);
    colsHigh[0] = address(eurY);
    colsHigh[1] = address(eurB);
    colsHigh[2] = address(eurA);
    borrowerHighDecFirst = new RedeemPiecewiseMintBorrower(parallelizer, tokenP, lender, colsHigh);

    // Only allow minting back using eurY (most precise). This should often fail to repay for tiny redeems.
    address[] memory colsOnlyY = new address[](1);
    colsOnlyY[0] = address(eurY);
    borrowerOnlyY = new RedeemPiecewiseMintBorrower(parallelizer, tokenP, lender, colsOnlyY);
  }

  function _setMonotonicMintFeesAndFlatRedemption() internal {
    // Set oracle prices to 1.0 so we isolate rounding/fee math rather than price effects.
    MockChainlinkOracle(address(oracleA)).setLatestAnswer(100_000_000);
    MockChainlinkOracle(address(oracleB)).setLatestAnswer(100_000_000);
    MockChainlinkOracle(address(oracleY)).setLatestAnswer(100_000_000);

    // Strictly increasing mint fees (monotonic) as observed in a path-independence counterexample.
    uint64[] memory xFeeMint = new uint64[](3);
    int64[] memory yFeeMint = new int64[](3);
    xFeeMint[0] = 0;
    xFeeMint[1] = 24_428_931;
    xFeeMint[2] = 44_762_710;
    yFeeMint[0] = 250_678_608;
    yFeeMint[1] = 294_321_635;
    yFeeMint[2] = 296_375_599;

    // Burn fees are irrelevant for this redeem->mint repayment cycle; keep them at 0.
    uint64[] memory xFeeBurn = new uint64[](1);
    xFeeBurn[0] = uint64(BASE_9);
    int64[] memory yFee0 = new int64[](1);
    yFee0[0] = 0;

    // Redemption curve set to flat 1.0.
    int64[] memory yRedeem = new int64[](1);
    yRedeem[0] = int64(int256(BASE_9));

    vm.startPrank(guardian);
    parallelizer.setFees(address(eurA), xFeeMint, yFeeMint, true);
    parallelizer.setFees(address(eurB), xFeeMint, yFeeMint, true);
    parallelizer.setFees(address(eurY), xFeeMint, yFeeMint, true);

    parallelizer.setFees(address(eurA), xFeeBurn, yFee0, false);
    parallelizer.setFees(address(eurB), xFeeBurn, yFee0, false);
    parallelizer.setFees(address(eurY), xFeeBurn, yFee0, false);

    // x array for redemption is strictly increasing; reuse [0] and y=BASE_9 for constant factor 1.0.
    uint64[] memory xRedeem = new uint64[](1);
    xRedeem[0] = 0;
    parallelizer.setRedemptionCurveParams(xRedeem, yRedeem);
    vm.stopPrank();
  }

  function _setZeroFeesAndFlatRedemption() internal {
    // Set mint/burn fees to 0, and redemption curve to 1, to isolate rounding effects.
    uint64[] memory xFeeMint = new uint64[](1);
    xFeeMint[0] = uint64(0);
    uint64[] memory xFeeBurn = new uint64[](1);
    xFeeBurn[0] = uint64(BASE_9);

    int64[] memory yFee = new int64[](1);
    yFee[0] = 0;

    vm.startPrank(guardian);
    parallelizer.setFees(address(eurA), xFeeMint, yFee, true);
    parallelizer.setFees(address(eurB), xFeeMint, yFee, true);
    parallelizer.setFees(address(eurY), xFeeMint, yFee, true);
    parallelizer.setFees(address(eurA), xFeeBurn, yFee, false);
    parallelizer.setFees(address(eurB), xFeeBurn, yFee, false);
    parallelizer.setFees(address(eurY), xFeeBurn, yFee, false);

    int64[] memory yRedeem = new int64[](1);
    yRedeem[0] = int64(int256(BASE_9));
    parallelizer.setRedemptionCurveParams(xFeeMint, yRedeem);
    vm.stopPrank();
  }

  function _seedReserves(uint256[3] memory initialAmounts) internal returns (uint256 mintedStables) {
    // Mint stablecoins into Alice by depositing collateral, creating backing in the parallelizer.
    vm.startPrank(alice);
    // Bound amounts so tests run quickly but still exercise rounding; eurA has 6 decimals.
    initialAmounts[0] = bound(initialAmounts[0], 1e6, 1e15 * 10 ** 6);
    initialAmounts[1] = bound(initialAmounts[1], 1e6, 1e15 * 10 ** 12);
    initialAmounts[2] = bound(initialAmounts[2], 1e6, 1e15 * 10 ** 18);

    deal(address(eurA), alice, initialAmounts[0]);
    deal(address(eurB), alice, initialAmounts[1]);
    deal(address(eurY), alice, initialAmounts[2]);

    IERC20(address(eurA)).approve(address(parallelizer), type(uint256).max);
    IERC20(address(eurB)).approve(address(parallelizer), type(uint256).max);
    IERC20(address(eurY)).approve(address(parallelizer), type(uint256).max);

    mintedStables += parallelizer.swapExactInput(initialAmounts[0], 0, address(eurA), address(tokenP), alice, block.timestamp * 2);
    mintedStables += parallelizer.swapExactInput(initialAmounts[1], 0, address(eurB), address(tokenP), alice, block.timestamp * 2);
    mintedStables += parallelizer.swapExactInput(initialAmounts[2], 0, address(eurY), address(tokenP), alice, block.timestamp * 2);
    vm.stopPrank();
  }

  /// @notice Attack attempt: borrow the max amount, redeem all borrowed tokenP, then piecewise mint to repay.
  /// Expected property (default params): attacker cannot end the flashloan with any positive residual balance
  /// (tokenP or collateral). If this fails, it suggests a rounding/curve issue worth investigating.
  function testFuzz_Flashloan_Max_RedeemAll_PiecewiseMint_NoProfit_DefaultParams(
    uint256[3] memory initialAmounts,
    uint256 loanAmountSeed,
    uint8 chunks,
    bytes32 salt
  )
    public
  {
    uint256 mintedStables = _seedReserves(initialAmounts);
    vm.assume(mintedStables > 1); // need room for a non-zero flat fee

    uint256 loanAmount = bound(loanAmountSeed, 1, mintedStables);
    lender.setParams(loanAmount, 1); // flat fee = 1 wei of tokenP

    bytes memory data = abi.encode(chunks, salt);

    // If the flashloan cannot be repaid, it will revert and the attack fails (acceptable outcome).
    try lender.flashLoan(borrower, address(tokenP), loanAmount, data) returns (bool ok) {
      require(ok, "flashLoan returned false");

      // If it succeeds, there must be no profit left behind.
      assertEq(IERC20(address(tokenP)).balanceOf(address(borrower)), 0, "profit in tokenP");
      assertEq(IERC20(address(eurA)).balanceOf(address(borrower)), 0, "profit in eurA");
      assertEq(IERC20(address(eurB)).balanceOf(address(borrower)), 0, "profit in eurB");
      assertEq(IERC20(address(eurY)).balanceOf(address(borrower)), 0, "profit in eurY");
    } catch {
      // Revert means the borrower couldn't complete the cycle and repay.
    }
  }

  /// @notice Same as the default-params test, but forces a strictly monotonic mint fee curve.
  /// This is a probe to see whether rounding dust profit can still exist even with sane (monotonic) fees.
  function testFuzz_Flashloan_Max_RedeemAll_PiecewiseMint_MonotonicMintFees_Probe(
    uint256[3] memory initialAmounts,
    uint256 loanAmountSeed,
    uint8 chunks,
    bytes32 salt
  )
    public
  {
    _setMonotonicMintFeesAndFlatRedemption();

    uint256 mintedStables = _seedReserves(initialAmounts);
    vm.assume(mintedStables > 1);

    uint256 loanAmount = bound(loanAmountSeed, 1, mintedStables);
    lender.setParams(loanAmount, 1); // flat fee = 1 wei of tokenP

    bytes memory data = abi.encode(chunks, salt);

    try lender.flashLoan(borrower, address(tokenP), loanAmount, data) returns (bool ok) {
      require(ok, "flashLoan returned false");
    } catch {
      // Revert means the borrower couldn't complete the cycle and repay.
    }
  }

  /// @notice Deterministic counterexample showing dust profit can still exist with strictly monotonic mint fees.
  function test_Flashloan_RedeemAll_PiecewiseMint_MonotonicMintFees_LeavesDustProfit() public {
    _setMonotonicMintFeesAndFlatRedemption();

    // Counterexample found by the fuzz probe above.
    uint256[3] memory initialAmounts = [
      uint256(999999999999999295433), // eurA
      uint256(132846194),             // eurB
      uint256(5626568696961731130948) // eurY
    ];
    uint256 mintedStables = _seedReserves(initialAmounts);
    assertGt(mintedStables, 1);

    uint256 loanAmount = 3621523563518;
    lender.setParams(loanAmount, 1);

    uint8 chunks = 2;
    bytes32 salt = 0xea2375bda3eedb5ded144352e05763230ad6950f8ee3d7645723968c15611ee6;
    bytes memory data = abi.encode(chunks, salt);

    bool ok = lender.flashLoan(borrower, address(tokenP), loanAmount, data);
    assertTrue(ok);

    assertEq(IERC20(address(tokenP)).balanceOf(address(borrower)), 0);
    assertEq(IERC20(address(eurA)).balanceOf(address(borrower)), 0);
    assertEq(IERC20(address(eurB)).balanceOf(address(borrower)), 0);
    assertEq(IERC20(address(eurY)).balanceOf(address(borrower)), 20);
  }

  function test_Flashloan_RedeemAll_PiecewiseMint_MonotonicMintFees_HighDecimalsFirst_StillLeavesDust() public {
    _setMonotonicMintFeesAndFlatRedemption();

    uint256[3] memory initialAmounts = [
      uint256(999999999999999295433), // eurA
      uint256(132846194),             // eurB
      uint256(5626568696961731130948) // eurY
    ];
    uint256 mintedStables = _seedReserves(initialAmounts);
    assertGt(mintedStables, 1);

    uint256 loanAmount = 3621523563518;
    lender.setParams(loanAmount, 1);

    uint8 chunks = 2;
    bytes32 salt = 0xea2375bda3eedb5ded144352e05763230ad6950f8ee3d7645723968c15611ee6;
    bytes memory data = abi.encode(chunks, salt);

    bool ok = lender.flashLoan(borrowerHighDecFirst, address(tokenP), loanAmount, data);
    assertTrue(ok);

    // We expect the borrower still to repay using eurA (eurY dust is too small to be useful),
    // so eurY dust remains.
    assertEq(IERC20(address(tokenP)).balanceOf(address(borrowerHighDecFirst)), 0);
    assertEq(IERC20(address(eurA)).balanceOf(address(borrowerHighDecFirst)), 0);
    assertEq(IERC20(address(eurB)).balanceOf(address(borrowerHighDecFirst)), 0);
    assertEq(IERC20(address(eurY)).balanceOf(address(borrowerHighDecFirst)), 20);
  }

  function test_Flashloan_RedeemAll_PiecewiseMint_MonotonicMintFees_OnlyEurY_CannotRepay() public {
    _setMonotonicMintFeesAndFlatRedemption();

    uint256[3] memory initialAmounts = [
      uint256(999999999999999295433), // eurA
      uint256(132846194),             // eurB
      uint256(5626568696961731130948) // eurY
    ];
    uint256 mintedStables = _seedReserves(initialAmounts);
    assertGt(mintedStables, 1);

    uint256 loanAmount = 3621523563518;
    lender.setParams(loanAmount, 1);

    uint8 chunks = 2;
    bytes32 salt = 0xea2375bda3eedb5ded144352e05763230ad6950f8ee3d7645723968c15611ee6;
    bytes memory data = abi.encode(chunks, salt);

    // With only eurY allowed for minting back, the borrower should revert (insufficient eurY to repay).
    vm.expectRevert("cannot mint repay chunk");
    lender.flashLoan(borrowerOnlyY, address(tokenP), loanAmount, data);
  }

  /// @notice Deterministic counterexample showing dust profit from rounding when fees are set to 0.
  /// Salt was found by brute forcing locally (see git history); this keeps the regression fast.
  function test_Flashloan_RedeemAll_PiecewiseMint_ZeroFees_LeavesDustProfit() public {
    _setZeroFeesAndFlatRedemption();

    // From failing fuzz counterexample.
    uint256[3] memory initialAmounts = [
      uint256(7722290069109197059061462975852720261121524117259838058631119),
      uint256(771447797),
      uint256(3)
    ];
    uint256 mintedStables = _seedReserves(initialAmounts);
    assertGt(mintedStables, 1);

    uint256 loanAmount = 581558164043130774767101051304;
    lender.setParams(loanAmount, 1);

    uint8 chunks = 24;
    // Brute-forced salt giving a larger deterministic eurA dust profit.
    bytes32 salt = 0xb06106542bac778aeaad81cc158812cb2f6ea44dae69fc118099eaae95163ba1;
    bytes memory data = abi.encode(chunks, salt);

    bool ok = lender.flashLoan(borrower, address(tokenP), loanAmount, data);
    assertTrue(ok);

    // Pays back principal+fee, keeps dust profit in 6-decimal collateral.
    assertEq(IERC20(address(tokenP)).balanceOf(address(borrower)), 0);
    assertEq(IERC20(address(eurA)).balanceOf(address(borrower)), 15);
    console.log("eurA: %s", IERC20(address(eurA)).balanceOf(address(borrower)));
  }
}

contract FlashloanBurnPiecewiseMintFuzzTest is Fixture {
  FlashLenderMock internal lender;
  BurnPiecewiseMintBorrower internal borrower;

  function setUp() public override {
    super.setUp();

    lender = new FlashLenderMock(tokenP);

    address[] memory cols = new address[](3);
    cols[0] = address(eurA); // 6 decimals
    cols[1] = address(eurB); // 12 decimals
    cols[2] = address(eurY); // 18 decimals

    borrower = new BurnPiecewiseMintBorrower(parallelizer, tokenP, lender, cols);
  }

  function _seedReserves(uint256[3] memory initialAmounts) internal returns (uint256 mintedStables) {
    // Same reserve seeding as the redeem test: mint stablecoins by depositing collateral,
    // leaving collateral backing on the parallelizer to be burnt out.
    vm.startPrank(alice);

    initialAmounts[0] = bound(initialAmounts[0], 1e6, 1e15 * 10 ** 6);
    initialAmounts[1] = bound(initialAmounts[1], 1e6, 1e15 * 10 ** 12);
    initialAmounts[2] = bound(initialAmounts[2], 1e6, 1e15 * 10 ** 18);

    deal(address(eurA), alice, initialAmounts[0]);
    deal(address(eurB), alice, initialAmounts[1]);
    deal(address(eurY), alice, initialAmounts[2]);

    IERC20(address(eurA)).approve(address(parallelizer), type(uint256).max);
    IERC20(address(eurB)).approve(address(parallelizer), type(uint256).max);
    IERC20(address(eurY)).approve(address(parallelizer), type(uint256).max);

    mintedStables += parallelizer.swapExactInput(
      initialAmounts[0], 0, address(eurA), address(tokenP), alice, block.timestamp * 2
    );
    mintedStables += parallelizer.swapExactInput(
      initialAmounts[1], 0, address(eurB), address(tokenP), alice, block.timestamp * 2
    );
    mintedStables += parallelizer.swapExactInput(
      initialAmounts[2], 0, address(eurY), address(tokenP), alice, block.timestamp * 2
    );

    vm.stopPrank();
  }

  /// @notice Attack attempt: borrow tokenP, burn all to a chosen collateral, then piecewise mint to repay.
  /// If the flashloan succeeds, there should be no profit left behind.
  function testFuzz_Flashloan_Max_BurnAll_PiecewiseMint_NoProfit_DefaultParams(
    uint256[3] memory initialAmounts,
    uint256 loanAmountSeed,
    uint8 chunks,
    bytes32 salt,
    uint8 burnIndex
  )
    public
  {
    uint256 mintedStables = _seedReserves(initialAmounts);
    vm.assume(mintedStables > 1);

    address burnCollateral = burnIndex % 3 == 0 ? address(eurA) : burnIndex % 3 == 1 ? address(eurB) : address(eurY);
    (uint256 issuedFromCollateral,) = parallelizer.getIssuedByCollateral(burnCollateral);
    vm.assume(issuedFromCollateral > 1);

    uint256 loanAmount = bound(loanAmountSeed, 1, issuedFromCollateral);
    lender.setParams(loanAmount, 1); // flat fee = 1 wei

    bytes memory data = abi.encode(chunks, salt, burnIndex);

    try lender.flashLoan(borrower, address(tokenP), loanAmount, data) returns (bool ok) {
      require(ok, "flashLoan returned false");

      assertEq(IERC20(address(tokenP)).balanceOf(address(borrower)), 0, "profit in tokenP");
      assertEq(IERC20(address(eurA)).balanceOf(address(borrower)), 0, "profit in eurA");
      assertEq(IERC20(address(eurB)).balanceOf(address(borrower)), 0, "profit in eurB");
      assertEq(IERC20(address(eurY)).balanceOf(address(borrower)), 0, "profit in eurY");
    } catch {
      // revert means the borrower couldn't complete the cycle and repay
    }
  }
}
```

Attack:
- redeem
- piece-wise mint

**Parallel:** Fixed in commit [f60101a](https://github.com/parallel-protocol/parallel-parallelizer/commit/f60101a455c9215c49a7ea70551da7d31ca5ca76).

**Cyfrin:** Verified. `LibHelpers.convertDecimalsTo` now rounds towards the specified direction when converting from higher decimals to lower decimals.

## [M-7] Missing validation allows `user Deviation > burn Ratio Deviation`, silently disabling burn ratio protection
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** In `LibOracle::readBurn`, `readSpotAndTarget` snaps `oracleValue` to `targetPrice` when spot is within `userDeviation`. The burn ratio check (L84) then compares the already-snapped value against `burnRatioDeviation`. If `userDeviation > burnRatioDeviation`, depegs between the two thresholds are snapped away before the ratio check sees them — the check compares `targetPrice` against itself and never triggers.

`LibSetters::setOracle` validates only via `readMint` (L153), which ignores `burnRatioDeviation`. Nothing enforces `burnRatioDeviation >= userDeviation`.

**Impact:** When triggered, the burn ratio penalty is silently disabled — `getBurnOracle` returns `minRatio = BASE_18` and all burns proceed at full value during a depeg that should have activated the penalty.

**Proof of Concept:**
1. Oracle set with `userDeviation=5%`, `burnRatioDeviation=2%`
2. Collateral depegs to 0.96 (4% — between the two thresholds)
3. `readSpotAndTarget` snaps 0.96 → 1.0 → ratio check on L84 passes → `ratio = BASE_18`
4. Burns proceed at full value; the depeg is invisible

**Recommended Mitigation:** Add in `LibSetters::setOracle`:

```solidity
(uint128 userDeviation, uint128 burnRatioDeviation) = abi.decode(hyperparameters, (uint128, uint128));
if (userDeviation > burnRatioDeviation) revert InvalidParams();
```

**Parallel:** Fixed in commit [bc4574a](https://github.com/parallel-protocol/parallel-parallelizer/commit/bc4574ac3f794e53952092f264e3863af6247b5b#diff-dc2d240c037d4c60536e1992723693494bd288601798008bae2a168763783ccb).

**Cyfrin:** Verified. Remediated by implementing the recommended mitigation.

## [M-8] `Meta Vault::add Vault` should enforce identical underlying base asset
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** When supporting additional vaults, `MetaVault::addVault` should enforce that the new vault being supported has an identical underlying base asset as itself. Otherwise:
* `redeemRequiredBaseAssets` won't work as expected since the newly supported vault doesn't have the same base asset
* `MetaVault::depositedBase` will become corrupt, especially if the underlying asset tokens use different decimal precision

**Proof of Concept:**
```solidity
function test_vaultSupportedWithDifferentUnderlyingAsset() external {
    // create ERC4626 vault with different underlying ERC20 asset
    MockUSDe differentERC20 = new MockUSDe();
    MockERC4626 newSupportedVault = new MockERC4626(differentERC20);

    // verify pUSDe doesn't have same underlying asset as new vault
    assertNotEq(pUSDe.asset(), newSupportedVault.asset());

    // but still allows it to be added
    pUSDe.addVault(address(newSupportedVault));

    // this breaks `MetaVault::redeemRequiredBaseAssets` since
    // the newly supported vault doesn't have the same base asset
}
```

**Recommended Mitigation:** Change `MetaVault::addVaultInner`:
```diff
    function addVaultInner (address vaultAddress) internal {
+       IERC4626 newVault = IERC4626(vaultAddress);
+       require(newVault.asset() == asset(), "Vault asset mismatch");
```

**Strata:** Fixed in commits [9e64f09](https://github.com/Strata-Money/contracts/commit/9e64f09af6eb927c9c736796aeb92333dbb72c18), [706c2df](https://github.com/Strata-Money/contracts/commit/706c2df3f2caf6651b1d8e858beb5097dbd7d066).

**Cyfrin:** Verified.

## [M-9] Incorrect `record Result` recorded for each question in `record Results`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** When an assertion is resolved the UMA oracle makes a call back to `DefaultSession::assertionResolvedCallback` if the assertion was truthful, it calls `recordResults`:
```solidity
function recordResults(uint256 sessionId, bytes32 assertionId) public {
        ...
        uint256[] memory questionIds = SessionManager(sessionManager).getQuestionsForGame(sessionId);

        for (uint256 i = 0; i < assertion.winners.length; ++i) {
            address winner = assertion.winners[i]; //@audit how many winners could be?
            for (uint256 j = 0; j < questionIds.length; ++j) {
                (, address promptStrategy) = SessionManager(sessionManager).questionCommitment(questionIds[j]);
                IPromptStrategy(promptStrategy).recordResult(
                    questionIds[j], winner, assertion.totalXPs[i], assertion.totalTimes[i]
                ); <------
            }
          ...
        }

        winners[sessionId] = assertion.winners;
    }
```

As you can see the `recordResults` is calling the `recordResult` function for the specific strategies:
```solidity
 function recordResult(uint256 questionId, address player, uint256 xp, uint256 time) external {
        address sessionStrategy = SessionManager(revealedQuestions[questionId].sessionManager).getSessionStrategy(
            revealedQuestions[questionId].gameId
        );
        require(sessionStrategy == msg.sender, OnlySessionStrategy(sessionStrategy, msg.sender));

        results[questionId][player] = Result({xp: xp, time: time}); <------
    }
```

The problem is that the `recordResult` function is mean to savee the xp and time of the specific question of a gameId but what the `recordResults` function is passing the average of the user xp and time for all question corresponding to a specific gameId(sessionId).

**Impact:** Incorrect value passed for `recordResult` in all startgyes  this will return incorrect values in  `getResult` which is called in `_calculatePlayerSessionResult` and used as a view function.

**Majority Games:**
Fixed in commit [a3bcfb6](https://github.com/Engage-Protocol/engage-protocol/commit/a3bcfb6518f0eb33a6a37089e9e0a2c14ea7b210).

**Cyfrin:** Verified.

## [M-10] Prevent negative assertion following previous truthful assertion in `Default Session::assertion Resolved Callback`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DefaultSession::assertionResolvedCallback` does not handle the state where:
* it is first called with `assertedTruthfully = true` for given `assertionId`
* it is later called with `assertedTruthfully = false` for the same `assertionId`

**Impact:** In this state `delete assertions[assertionId];` is executed even though the results have already been recorded based on the first truthful assertion.

**Recommended Mitigation:** `DefaultSession::assertionResolvedCallback` should revert if `assertions[assertionId].resolved`:
```diff
    function assertionResolvedCallback(bytes32 assertionId, bool assertedTruthfully) public override {
        require(msg.sender == address(optimisticOracle), NotOptimisticOracle(msg.sender));
+       require(!assertions[assertionId].resolved, AssertionAlreadyResolved(assertionId));
```

**Majority Games:**
Fixed in commit [99ec735](https://github.com/Engage-Protocol/engage-protocol/commit/99ec735d6b0a42c22fd0af6ae6ec8c91ef2e922d).

**Cyfrin:** Verified.

## [M-11] `Red Stone Nav Provider::rate` can return zero for non-zero oracle input due to rounding in `Helper::normalize Rate`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** In `RedStoneNavProvider::rate`, the zero check validates the raw oracle value but not the normalized result:
```solidity
function rate() external view override returns (uint256) {
    uint8 oracleDecimals = priceFeed.decimals();
    uint8 assetDecimals = asset.decimals();
    int256 rsRate = priceFeed.latestAnswer();
    require(rsRate != 0, 'Rate must not be zero');  // @audit Checks raw value only

    // @audit normalized rate never zero checked
    return Helper.normalizeRate(uint256(rsRate), oracleDecimals, assetDecimals);
}
```

The `Helper::normalizeRate` function divides when `fromDecimals > toDecimals`:
```solidity
function normalizeRate(uint256 value, uint8 fromDecimals, uint8 toDecimals) internal pure returns (uint256) {
    if (fromDecimals == toDecimals) {
        return value;
    } else if (fromDecimals > toDecimals) {
        return value / (10**(fromDecimals - toDecimals));  // @audit Can round to zero
    } else {
        return value * (10**(toDecimals - fromDecimals));
    }
}
```

When the raw oracle value is smaller than the divisor, integer division truncates to zero:
```solidity
oracleDecimals = 18 (common for RedStone)
assetDecimals = 6 (like USDC)
rsRate = 5e11 (passes the != 0 check)
divisor = 10^(18 - 6) = 1e12
normalizedRate = 5e11 / 1e12 = 0
```

The `require(rsRate != 0)` passes because `5e11 != 0`, but the function returns `0`.

This could occur with:
- Severely devalued assets approaching zero value
- Misconfigured oracle/asset decimal pairing
- Oracle malfunction returning unexpectedly small values
- Exotic assets with very low unit prices

**Impact:** Any protocol consuming `RedStoneNavProvider::rate` receives zero, potentially causing a number of errors if the protocol doesn't revert such as:
- Incorrect NAV calculations valuing assets at zero
- Potential division-by-zero errors in downstream calculations
- Users trading at incorrect prices, either losing funds or extracting value from the protocol

**Recommended Mitigation:** Add a zero check on the normalized result:
```solidity
function rate() external view override returns (uint256 normalizedRate) {
    uint8 oracleDecimals = priceFeed.decimals();
    uint8 assetDecimals = asset.decimals();
    int256 rsRate = priceFeed.latestAnswer();
    require(rsRate > 0, 'Rate must be positive');

    normalizedRate = Helper.normalizeRate(uint256(rsRate), oracleDecimals, assetDecimals);
    require(normalizedRate > 0, 'Normalized rate is zero');
}
```

**Securitize:** Fixed in commit [f4bed90](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/f4bed908104433d41035215a5315718dcc5669a9).

**Cyfrin:** Verified.

## [M-12] `Red Stone Nav Provider::rate` will return massively inflated value if underlying oracle returns a negative value and lacks common oracle validations
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `RedStoneNavProvider::rate` has an underlying oracle price feed which returns an `int256`, then performs an unsafe cast to `uint256`:
```solidity
int256 rsRate = priceFeed.latestAnswer();
require(rsRate != 0, 'Rate must not be zero');
return Helper.normalizeRate(uint256(rsRate), oracleDecimals, assetDecimals);
```

**Impact:** If the underlying oracle returned a negative number, performing an unsafe cast to `uint256` will return an absurdly high rate.

**Recommended Mitigation:** Enforce that the rate returned by the underlying oracle must be greater than zero:
```diff
    function rate() external view override returns (uint256) {
        uint8 oracleDecimals = priceFeed.decimals();
        uint8 assetDecimals = asset.decimals();
        int256 rsRate = priceFeed.latestAnswer();
-       require(rsRate != 0, 'Rate must not be zero');
+       require(rsRate > 0, 'Rate must be greater than zero');
        return Helper.normalizeRate(uint256(rsRate), oracleDecimals, assetDecimals);
    }
```

Also consider adding other common oracle-related checks such as:
* staleness
* min/max price thresholds

**Securitize:** Fixed in commit [ec23faf](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/ec23faf7f773b7a42229cb5f7f6ae3dd51a07772).

**Cyfrin:** Verified.

## [M-13] `Securitize Amm Nav Provider` virtual reserve rounding erosion can lead to denial of service
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The virtual AMM's constant-product math erodes `k` through integer division truncation on every trade:
```solidity
// In `_curveBuy`:
newQuote = Y + amountInQuote;
newBase = kLocal / newQuote;  // Rounds down

// After trade execution:
baseReserves = newBase;
quoteReserves = newQuote;
k = newBase * newQuote;  // New k ≤ old k due to truncation
```

Each trade can lose up to `(denominator - 1)` from k. Over many trades, `baseReserves` (or `quoteReserves` for sells) progressively decreases.

The `_checkAndResetBaseline` function can accelerate this by locking in depleted reserves when market status changes from OPEN → CLOSED:
```solidity
if (shouldReset) {
    uint256 newBase = baseReserves;  // Uses current depleted value
    uint256 newQuote = (newBase * anchorPriceWad) / WAD;
    _resetBaseline(newBase, newQuote);  // k = newBase * newQuote (tiny)
}
```

Once k becomes sufficiently small, a single trade can round reserves to zero:
```solidity
// If k = 1, quoteReserves = 1, and amountInQuote = 2:
newQuote = 1 + 2 = 3;
newBase = 1 / 3 = 0;  // Rounds to zero

// Trade completes (deltaBase = 1 passes the check), then:
baseReserves = 0;
k = 0 * 3 = 0;
```

All subsequent trades revert at the `initialized` modifier:
```solidity
modifier initialized() {
    require(baseReserves > 0 && quoteReserves > 0, "uninitialized");
    // ...
}
```

**Impact:** Denial of service for all trade execution until admin manually calls `resetBaseline` to restore valid reserves.

**Recommended Mitigation:** Add minimum reserve thresholds to prevent reserves from falling into the danger zone. This could be done using new admin-configurable storage slots and should be based on the decimals of the `asset`:
```diff
+ uint256 public minReserves;

function initialize(uint256 _baseReserves, uint256 _quoteReserves, address _asset) public onlyProxy initializer {
    // ... existing checks ...

    asset = IERC20Metadata(_asset);
+   uint8 d = asset.decimals();
+   uint256 minReservesTemp = 10 ** d;  // 1 whole token minimum

+   require(_baseReserves >= minReservesTemp, "baseReserves too small");
+   require(_quoteReserves >= minReservesTemp, "quoteReserves too small");
+   minReserves = minReservesTemp;

    // ... rest of initialization
}

function _resetBaseline(uint256 newBase, uint256 newQuote) internal {
    require(newBase > 0, "newBase=0");
    require(newQuote > 0, "newQuote=0");

+   uint256 minReservesCache = minReserves;
+   require(newBase >= minReservesCache, "newBase too small");
+   require(newQuote >= minReservesCache, "newQuote too small");

    // ... rest of function
}

function _curveBuy(uint256 amountInQuote) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInQuote > 0, "amountInQuote=0");

    uint256 X = baseReserves;
    uint256 Y = quoteReserves;
    uint256 kLocal = k;

    newQuote = Y + amountInQuote;
    newBase = kLocal / newQuote;

+   require(newBase >= minReserves, "base reserves too low");

    uint256 deltaBase = X - newBase;
    require(deltaBase > 0, "deltaBase=0");

    curvePriceWad = (amountInQuote * WAD) / deltaBase;
}

function _curveSell(uint256 amountInBase) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInBase > 0, "amountInBase=0");

    uint256 X = baseReserves;
    uint256 Y = quoteReserves;
    uint256 kLocal = k;

    newBase = X + amountInBase;
    newQuote = kLocal / newBase;

+   require(newQuote >= minReserves, "quote reserves too low");

    uint256 deltaQuote = Y - newQuote;
    require(deltaQuote > 0, "deltaQuote=0");

    curvePriceWad = (deltaQuote * WAD) / amountInBase;
}
```

Another benefit of enforcing minimum reserves is a consistent pattern of high-profile mainnet hacks have involved attackers manipulating pool reserves to very low wei amounts; enforcing minimum reserves acts as defensive programming technique helping to reduce the attack surface available to hackers.

**Securitize:** Fixed in commit [1919a89](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/1919a8993ec7e0cd9f1931b4bb02ec622321c0fe).

**Cyfrin:** Verified.

## [M-14] Incorrect rounding direction in `Securitize Amm Nav Provider::execute Buy Base` when scaling down `exec Price`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** In `SecuritizeAmmNavProvider::executeBuyBase`, the execution price is scaled down from WAD precision (18 decimals) to the asset's native decimal precision using integer division. The current implementation uses floor division, which systematically rounds DOWN the execution price:

```solidity
 uint256 scaleDown = 10 ** (18 - d);

 execPrice = rawExecPriceWad / scaleDown;
```

When users buy base assets, rounding the price DOWN means they pay less than the true calculated price. For example, with a 6-decimal token where `scaleDown` = 10^12:
* True price: $100.0000007 → `rawExecPriceWad` = 100,000,000,700,000,000,000
* Rounded price: $100.000000 → `execPrice` = 100,000,000
* Loss: $0.0000007 per share (always favors the buyer)

This issue is especially significant in `CLOSED_MARKET ` mode where AMM-based curve pricing is applied. In `CLOSED_MARKET`, the execution price calculation involves:

```solidity
function _pricingFromCurveBuy(
        uint256 amountInQuote,
        uint256 curvePriceWad,
        uint256 anchorPriceWad
    ) internal view returns (uint256 baseOut, uint256 execPriceWad) {
        require(anchorPriceWad > 0, "anchor=0");
        require(priceScaleFactor > 0, "scaleFactor = 0");

        uint256 r0Wad = (quoteBaseline * WAD) / baseBaseline;
        uint256 mWad = (curvePriceWad * WAD) / r0Wad;

        uint256 baseExecPriceWad = (anchorPriceWad * mWad) / WAD;

        // Smooth towards anchor:
        // execPriceWad = anchor + (baseExec - anchor) / scaleFactor
        if (baseExecPriceWad >= anchorPriceWad) {
            uint256 diff = baseExecPriceWad - anchorPriceWad;
            execPriceWad = anchorPriceWad + (diff / priceScaleFactor);
        } else {
            uint256 diff = anchorPriceWad - baseExecPriceWad;
            execPriceWad = anchorPriceWad - (diff / priceScaleFactor);
        }

        baseOut = (amountInQuote * WAD) / execPriceWad;
    }
```

These operations produce prices with deep fractional precision that almost never align with the `scaleDown` boundaries. This means every `CLOSED_MARKET` trade experiences truncation loss, unlike `OPEN_MARKET` mode where prices are set directly to clean anchor values.

**Impact:** On buy operations the protocol systematically loses a fractional amount on every trade. While the per-trade loss is small (typically sub-cent), it accumulates over time and volume.

**Recommended Mitigation:** Round up the final `execPrice` in `executeBuyBase`. Consider:
* using OZ [Math::mulDiv](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/Math.sol#L282) with explicit rounding for all multiplication followed by division
* documenting with comments why the rounding direction is logically correct at every place where rounding can occur

**Securitize:** Fixed in commit [0b268e8](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/0b268e8282cfcacf4cbcd32e4b908a87af04b0e8).

**Cyfrin:** Verified.

## [M-15] Lack of Price Feed Update Function in `Red Stone Nav Provider`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The `RedStoneNavProvider` contract sets the RedStone price feed address during initialization but provides no mechanism to update it afterwards. The priceFeed is set once in the `RedStoneNavProvider::initialize` function and becomes immutable for the lifetime of the contract:

```solidity
function initialize(address _priceFeed, address _asset) public onlyProxy initializer {
        __BaseDSContract_init();
        priceFeed = IPriceFeed(_priceFeed);
        asset = IERC20Metadata(_asset);
    }
```
The contract declares the `priceFeed` as a public state variable but offers no admin function to update it, f the RedStone oracle address needs to be changed due to:
* Oracle migration to a new address
* Oracle deprecation or compromise
* Need to switch to a different price feed
* Oracle upgrade or maintenance

The only solution is to:
1. Deploy a new `RedStoneNavProvider` contract with the new feed address
2. Call `updateNavProvider()` on all `OnRamp/OffRamp` contracts using this provider
3. Potentially requiring governance votes or multi-sig operations

**Impact:** Requires complete contract redeployment instead of a simple parameter update in case of the `priceFeed` need to be changed.

**Recommended Mitigation:** Add an admin-controlled function to update the price feed address.

**Securitize:** Fixed in commit [4146a77](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/4146a77b4e5d3a72e67f164ef6e1ca3a12c99657).

**Cyfrin:** Verified.

## [M-16] When emitting events don't read known values from storage
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** When emitting events don't read known values from storage; for example in `SecuritizeAmmNavProvider::_resetBaseline`:
```diff
    function _resetBaseline(uint256 newBase, uint256 newQuote) internal {
        require(newBase > 0, "newBase=0");
        require(newQuote > 0, "newQuote=0");

        baseReserves = newBase;
        quoteReserves = newQuote;

        baseBaseline = newBase;
        quoteBaseline = newQuote;

        k = newBase * newQuote;

-       emit BaselineReset(baseBaseline, quoteBaseline);
+       emit BaselineReset(newBase, newQuote);
    }
```

Similar optimizations can be made in:
* `AllowanceLiquidityProvider::setAllowanceProviderWallet`
* `CollateralLiquidityProvider::setExternalCollateralRedemption, setCollateralProvider`
* `BaseOffRamp::updateLiquidityProvider` at this line `uint256 _liquidityDecimals = IERC20Metadata(address(liquidityProvider.liquidityToken())).decimals();` - use `_liquidityProvider` instead of `liquidityProvider`
* `BaseOffRamp::toggleTwoStepTransfer`
* `PublicStockOffRamp::updateNavProvider`
* `SecuritizeOffRamp::updateNavProvider`
* `AllowanceAssetProvider::setAllowanceProviderWallet`
* `BaseOnRamp::updateMinSubscriptionAmount, toggleInvestorSubscription, toggleTwoStepTransfer`

**Securitize:** Fixed in commits [fe9f910](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/fe9f910f1fe6b73aa63171a2e8f4cb55f0092123), [5d39cc1](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/5d39cc1122fabdef280dd0da4ecc5d984f6355a1).

**Cyfrin:** Verified.

## [M-17] `Sherpa Vault::_roll Internal` price calculation comment and math inconsistent
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** When calculating a new price a script queries all vaults on all chains then passes that to `SherpaVault:: rollToNextRound`. This in turn calls [`SherpaVault::_rollInternal`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/blob/50eb8ad6ee048a767f7ed2265404c59592c098b7/contracts/SherpaVault.sol#L518-L529) where the new price is calculated:
```solidity
// Calculate global price using script-provided totals
// globalBalance must include pending deposits for correct price calculation
uint256 globalBalance = isYieldPositive
    ? globalTotalStaked + globalTotalPending + yield
    : globalTotalStaked + globalTotalPending - yield;

uint256 newPricePerShare = ShareMath.pricePerShare(
    globalShareSupply,
    globalBalance,
    globalTotalPending,
    _vaultParams.decimals
);
```
The code comments state that `globalBalance must include pending deposits` yet `globalBalance` is passed to [`ShareMath:pricePerShare`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/blob/50eb8ad6ee048a767f7ed2265404c59592c098b7/contracts/lib/ShareMath.sol#L66-L77), which immediately subtracts the `pending` amount: (`(totalBalance - pending) / totalSupply`):
```solidity
function pricePerShare(
    uint256 totalSupply,   // @audit-info globalShareSupply
    uint256 totalBalance,  // @audit-info globalBalance
    uint256 pendingAmount, // @audit-info globalTotalPending
    uint256 decimals
) internal pure returns (uint256) {
    uint256 singleShare = 10 ** decimals;
    return
        totalSupply > 0
            ? (singleShare * (totalBalance - pendingAmount)) / totalSupply
            : singleShare;
}
```
The comment in `_rollInternal` is inconsistent with the math applied as the actual price calculation doesn't include the `pendingAmount`.

Consider changing the comment or if the comment is correct, the math.


**Sherpa:** Fixed in commit [`9dbaf27`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/9dbaf277ec7b7349af682aa5d9f6a6ae78151db9)

**Cyfrin:** Verified. Comment was incorrect and is not fixed.

## [M-18] Consider implementing explicit rounding behaviour instead of default round down
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** All functions in `ShareMath.sol` round down to the nearest integer currently. This can be unfavourable in certain instances for the SherpaVault.

For example, the `ShareMath.pricePerShare` function uses integer division which causes precision loss. Hence it would slightly underestimate the price per share.

```solidity
function pricePerShare(
    uint256 totalSupply,
    uint256 totalBalance,
    uint256 pendingAmount,
    uint256 decimals
) internal pure returns (uint256) {
    uint256 singleShare = 10 ** decimals;
    return
        totalSupply > 0
            ? (singleShare * (totalBalance - pendingAmount)) / totalSupply
            : singleShare;
}
```

**Recommended Mitigation:** It is recommend to perform explicit rounding in addition to adding comments that logically elaborate why the respective rounding direction is appropriate in each instance.

**Sherpa:** Fixed in commit [`61345a1`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/61345a1967311167ec8fe4dba81bb2a21247ea50)

**Cyfrin:** Verified. Documentation about the specific rounding directions added.

\clearpage
## Gas Optimization

## [M-19] Misconfigured decimal scale can skew vault accounting
- Severity: `Medium`
- Source report: `sherpa.md`

### Detailed Content (from source)
**Description:** The vault’s math assumes the same decimal scale as the wrapped asset (USDC, 6 decimals) and as the `globalPricePerShare` fed by ops. While deployment sets `vaultParams.decimals = 6` and the wrapper enforces USDC’s 6 decimals, a misconfiguration will skew conversions.

**Impact:** Configuring the vault with more than 6 decimals can cause incorrect accounting, and follow-on reverts in rebalancing.

**Recommended Mitigation:** Consider locking the vault decimals to 6, same as `SherpaUSD`.

**Sherpa:** Fixed in commit [`1a634e0`](https://github.com/hedgemonyxyz/sherpa-vault-smartcontracts/commit/1a634e0331968ea5a73f38a62ef824da9376ab52)

**Cyfrin:** Verified. `_vaultParams.decimals` now verified to be 6 in the constructor.

## [M-20] Missing event emissions for critical oracle parameter changes
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** The oracle contracts (`STBL_PT1_Oracle` and `STBL_LT1_Oracle`) do not emit events when critical parameters are modified by admin functions.

Following admin functions modify critical parameters but do not emit events:

- `setPriceDecimals`
- `setPriceThreshold`
- `enableOracle`
- `disableOracle`

**Recommended Mitigation:** Consider adding event declarations for the above functions.

**STBL:** Fixed in commit [c540943](https://github.com/USD-Pi-Protocol/contract/commit/c54094363b196b534c9c36d563851dff31fe2975)

**Cyfrin:** Verified.

## [M-21] Missing zero address checks in `STBL_Register::setup Asset`
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** Several asset addresses are initialized without zero address checks in `STBL_Register::setupAsset` :

- `_contractAddr`
- `_issuanceAddr`
- `_distAddr`
- `_vaultAddr`
- `_oracle`

Notably, the same variables when set via their respective setter functions, eg,. `setOracle` have these validations. It is also important to note that an asset can only be setup once.

**Recommended Mitigation:** Consider adding zero address checks in the `setupAsset`

**STBL:** Fixed in commit [a737746](https://github.com/USD-Pi-Protocol/contract/commit/a737746e3f136f6c83605228b81b23da23e27183)

**Cyfrin:** Verified.

## [M-22] Enforce that `Staking Vault::decimals` is greater or equal to the underlying asset decimals
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** [EIP4626](https://eips.ethereum.org/EIPS/eip-4626) states:
> Although the convertTo functions should eliminate the need for any use of an EIP-4626 Vault’s decimals variable, it is still strongly recommended to mirror the underlying token’s decimals if at all possible, to eliminate possible sources of confusion and simplify integration across front-ends and for other off-chain users.

And this set of [vault property tests](https://github.com/crytic/properties/blob/main/contracts/ERC4626/properties/SecurityProps.sol#L8-L11) enforce that the vault's decimals are greater or equal to the underlying asset decimals:
```solidity
        assertGte(
            vault.decimals(),
            asset.decimals(),
            "The vault's share token should have greater than or equal to the number of decimals as the vault's asset token."
        );
```

**Recommended Mitigation:** In `StakingVault::constructor`, revert if `IERC20Metadata(_asset).decimals() > decimals()`.

**Syntetika:**
Fixed in commit [ac97972](https://github.com/SyntetikaLabs/monorepo/commit/ac97972d762392dc8465fa70c718fa78615636ff) by enforcing decimal equality per the EIP4626 standard recommendation.

**Cyfrin:** Verified.

## [M-23] Consider using exponential notation in tests
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** Tests frequently write decimals amounts as `100 * 10**6`. Consider using scientific notation (`100e6`) instead as it’s more concise, improves readability (fewer visual tokens/zeros), and reduces exponent mistakes.

**Button:** Fixed in commit [`9d8ed75`](https://github.com/buttonxyz/button-protocol/commit/9d8ed75bd5ed4957c7b23f9b06ff362b7bb218a4)

**Cyfrin:** Verified.

## [M-24] Missing L2 sequencer uptime check in `Oracle Adapter`
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** On L2, the `YToken` exchange rate is provided by custom Chainlink oracles. The exchange rate is queried in [`OracleAdapter::fetchExchangeRate`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/OracleAdapter.sol#L52-L77):

```solidity
function fetchExchangeRate(address token) external view override returns (uint256) {
    address oracle = oracles[token];
    require(oracle != address(0), "Oracle not set");

    (, /* uint80 roundId */ int256 answer, , /* uint256 startedAt */ uint256 updatedAt /* uint80 answeredInRound */, ) = IOracle(oracle).latestRoundData();

    require(answer > 0, "Invalid price");
    require(updatedAt > 0, "Round not complete");
    require(block.timestamp - updatedAt < staleThreshold, "Stale price");

    // Get decimals and normalize to 1e18 (PINT)
    uint8 decimals = IOracle(oracle).decimals();

    if (decimals < 18) {
        return uint256(answer) * (10 ** (18 - decimals));
    } else if (decimals > 18) {
        return uint256(answer) / (10 ** (decimals - 18));
    } else {
        return uint256(answer);
    }
}
```

However, this protocol is intended to be deployed on L2 networks such as Arbitrum and Optimism, where it's important to verify that the [sequencer is up](https://docs.chain.link/data-feeds/l2-sequencer-feeds). Without this check, if the sequencer goes down, the latest round data may appear fresh, when in fact it is stale, for advanced users submitting transactions from L1.

**Impact:** If the L2 sequencer goes down, oracle data will stop updating. Actually stale prices can appear fresh and be relied upon incorrectly. This could be exploited if significant price movement occurs during the downtime.

**Recommended Mitigation:** Consider implementing a sequencer uptime check, as shown in the [Chainlink example](https://docs.chain.link/data-feeds/l2-sequencer-feeds#example-consumer-contract), to prevent usage of stale oracle data during sequencer downtime.

**YieldFi:** Fixed in commits [`bb26a71`](https://github.com/YieldFiLabs/contracts/commit/bb26a71e9c57685996f6c853af6df6ed961c2f98) and [`e9c160f`](https://github.com/YieldFiLabs/contracts/commit/e9c160fdfd6dd90650c9537fba73c17cb3c53ea5)

**Cyfrin:** Verified. Sequencer uptime is now verified on L2s.

<!-- /Cyfrin Fixed Issues (Merged) -->

