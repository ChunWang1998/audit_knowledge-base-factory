# bridge/fee-tax-economics - Issues

- Count: 6

## F-2026-15966 - Excessive Initial Sell Tax Can Severely Restrict Exitsand Is Inconsistent With the Contract's Tax Limit Invariants
- 嚴重度：High
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, the initial sell tax is configured to 90%, which causes sellersto retain only a small portion of the transferred amount. This materiallyrestricts exit liquidity under the initial deployment state. The initialconfiguration is also inconsistent with the contractʼs own tax limitassumptions, because subsequent administrative updates enforce a 65%maximum sell tax while the initial state exceeds that threshold. In KnoxNet, the initial tax configuration is defined as follows: uint256 marketingBuyTaxBps = 500; uint256 marketingSellTaxBps = 9000; uint256 liquidityBuyTaxBps = 0; uint256 liquiditySellTaxBps = 0; uint256 totalBuyTaxBps = marketingBuyTaxBps + liquidityBuyTaxBps; uint256 totalSellTaxBps = marketingSellTaxBps + liquiditySellTaxBps; uint256 taxDenominator = 10000; Under these values, the effective sell tax is 9000 / 10000 = 90%. The sell-sidededuction is applied in `_applyTax`, which routes the taxed amount to thecontract balance and leaves only the remainder for the recipient: function `_applyTax`( address recipient, uint256 amount ) internal returns (uint256) { bool selling = liquidityPools[recipient]; uint256 taxAmount = (amount * `getTotalTaxBps(selling)`) / taxDenominator; `_balances`[`address(this)`] += taxAmount; return amount - taxAmount; } This initial state does not align with the constraints enforced in setTaxConfig, where the combined sell tax is limited to 65% require( `_liquiditySellTaxBps` + `_marketingSellTaxBps` <= 6500, "Sell tax cannot exceed 65%" ); As a result, the deployed parameters do not satisfy the same invariant thatis later applied to administrative updates. 16 Under the initial configuration, sellers receive only 10% of the gross sellamount. This can make exits economically impractical until the taxparameters are changed. The inconsistency between the deployment stateand the runtime tax cap may also invalidate assumptions made by users,reviewers, or integrations about the maximum configured sell tax. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
The initial tax configuration should be aligned with the same boundsenforced for later updates. Deployment-time values should satisfy theintended sell-tax maximum from the outset.A single invariant should be maintained across both initialization and setTaxConfig, ensuring that the effective buy and sell tax values remainwithin the intended limits at all times. Resolution: Fixed inc20e980: In the current KnoxNet implementation, the initial sell tax has beenreduced from 9000 basis points to 500 basis points, which removes the90% sell-side deduction present in the original deployment configuration.The initial values now remain within the same 65% bound enforced by setTaxConfig, so the deployment state is consistent with the administrativetax cap. uint256 public marketingBuyTaxBps = 500; uint256 public marketingSellTaxBps = 500;

### 修補方式（實際）
Fixed inc20e980: In the current KnoxNet implementation, the initial sell tax has beenreduced from 9000 basis points to 500 basis points, which removes the90% sell-side deduction present in the original deployment configuration.The initial values now remain within the same 65% bound enforced by setTaxConfig, so the deployment state is consistent with the administrativetax cap. uint256 public marketingBuyTaxBps = 500; uint256 public marketingSellTaxBps = 500;

## F-2026-15969 - Unvalidated tax Denominator Breaks Tax Cap Invariants and Causes Hardcoded Limits to Misapply in Both Directions
- 嚴重度：High
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, the taxDenominator value is owner-configurable but is notvalidated against the configured tax rates. The contract enforceshardcoded tax caps using absolute values such as 6500, while the actualeffective tax is computed relative to taxDenominator. As a result, the statedbuy and sell limits no longer represent fixed percentage bounds and maybecome either materially weaker or materially stricter than intended. In KnoxNet, setTaxConfig allows arbitrary updates to taxDenominator: function setTaxConfig( uint256 `_liquidityBuyTaxBps`, uint256 `_liquiditySellTaxBps`, uint256 `_marketingBuyTaxBps`, uint256 `_marketingSellTaxBps`, uint256 `_taxDenominator` ) external onlyOwner { require( `_liquidityBuyTaxBps` + `_marketingBuyTaxBps` <= 6500, "Buy tax cannot exceed 65%" ); require( `_liquiditySellTaxBps` + `_marketingSellTaxBps` <= 6500, "Sell tax cannot exceed 65%" ); taxDenominator = `_taxDenominator`; } However, the actual tax charged in KnoxNet is derived from theconfigured denominator: function `_applyTax`( address recipient, uint256 amount ) internal returns (uint256) { bool selling = liquidityPools[recipient]; uint256 taxAmount = (amount * `getTotalTaxBps(selling)`) / taxDenominator; `_balances`[`address(this)`] += taxAmount; return amount - taxAmount; } 20 This creates a broken invariant. If taxDenominator is set below 10000, thehardcoded 6500 cap permits a higher effective rate than 65%, including100% tax when taxDenominator == 6500, and a reverting transfer path whenthe tax sum exceeds the denominator. If taxDenominator is set above 10000,the same hardcoded cap becomes stricter than intended, because 6500 / taxDenominator produces an effective rate below 65%. The limit checks aretherefore decoupled from the value actually used in tax calculation. The effective buy and sell tax may exceed the stated 65% cap or becomeinconsistent with administrative expectations, depending on the configureddenominator. In the lower-denominator case, taxed transfers may becomeconfiscatory or revert entirely. In the higher-denominator case, theenforced limits no longer correspond to the percentages described by thecontract. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
taxDenominator should either be fixed to 10000 or validated so that all tax capchecks are normalized to the same denominator used in `_applyTax`.Hardcoded bounds should not be compared directly against tax valueswhen the denominator is mutable. function setTaxConfig( uint256 `_liquidityBuyTaxBps`, uint256 `_liquiditySellTaxBps`, uint256 `_marketingBuyTaxBps`, uint256 `_marketingSellTaxBps`, uint256 `_taxDenominator` ) external onlyOwner { require(`_taxDenominator` == 10000, "Invalid tax denominator"); 21 require( `_liquidityBuyTaxBps` + `_marketingBuyTaxBps` <= 6500, "Buy tax cannot exceed 65%" ); require( `_liquiditySellTaxBps` + `_marketingSellTaxBps` <= 6500, "Sell tax cannot exceed 65%" ); } If a variable denominator must be supported, the cap checks should beexpressed relative to `_taxDenominator`, and the total tax should always berequired to remain less than or equal to that denominator. Resolution: Fixed inc20e980: In KnoxNet, the previously mutable taxDenominator has been replaced withthe fixed constant `BPS_DENOMINATOR` = 10000, and the `_taxDenominator` parameterhas been removed from setTaxConfig. The tax cap checks in setTaxConfig are now evaluated against the same denominator used by `_applyTax`,eliminating the prior mismatch between validation and effective taxcalculation. uint256 constant `BPS_DENOMINATOR` = 10000; uint256 public constant taxDenominator = `BPS_DENOMINATOR`; function setTaxConfig( uint256 `_liquidityBuyTaxBps`, uint256 `_liquiditySellTaxBps`, uint256 `_marketingBuyTaxBps`, uint256 `_marketingSellTaxBps` ) external onlyOwner { require( `_liquidityBuyTaxBps` + `_marketingBuyTaxBps` <= 6500, "Buy tax cannot exceed 65%" );

### 修補方式（實際）
Fixed inc20e980: In KnoxNet, the previously mutable taxDenominator has been replaced withthe fixed constant `BPS_DENOMINATOR` = 10000, and the `_taxDenominator` parameterhas been removed from setTaxConfig. The tax cap checks in setTaxConfig are now evaluated against the same denominator used by `_applyTax`,eliminating the prior mismatch between validation and effective taxcalculation. uint256 constant `BPS_DENOMINATOR` = 10000; uint256 public constant taxDenominator = `BPS_DENOMINATOR`; function setTaxConfig( uint256 `_liquidityBuyTaxBps`, uint256 `_liquiditySellTaxBps`, uint256 `_marketingBuyTaxBps`, uint256 `_marketingSellTaxBps` ) external onlyOwner { require( `_liquidityBuyTaxBps` + `_marketingBuyTaxBps` <= 6500, "Buy tax cannot exceed 65%" ); require( `_liquiditySellTaxBps` + `_marketingSellTaxBps` <= 6500, "Sell tax cannot exceed 65%" );

## F-2026-15980 - Fee Distribution in _auto Swap Back Uses Con gured Tax Rates as Proxy for Actual Fee Composition, Causing Systematic Misallocation Between Marketing and Liquidity
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, all fee tokens from both buys and sells are collected into asingle undifferentiated balance. When distributing, `_autoSwapBack` assumesthat the marketing/liquidity composition of this balance matches the ratioof configured tax rates. In practice, the actual composition depends on realtrading volumes, which the contract does not track. When buy and sell taxstructures differ, the distribution formula systematically over- or under-allocates to one receiver at the expense of the other. In KnoxNet, `_applyTax` collects all fee tokens into one shared poolregardless of whether the fee originated from a buy or a sell, andregardless of the marketing/liquidity split configured for that direction: `_balances`[`address(this)`] += taxAmount; When `_autoSwapBack` distributes this pool, it calculates the liquidity shareusing the ratio of configured rates: uint256 combinedTaxBps = totalBuyTaxBps + totalSellTaxBps; uint256 totalLiquidityTaxBps = liquidityBuyTaxBps + liquiditySellTaxBps; uint256 amountToLiquify = ((amountToSwap * totalLiquidityTaxBps) / 2) / combinedTaxBps; This formula produces the correct result only when buy volume and sellvolume contribute equally to the pool. Consider a configuration where buytax is entirely liquidity-oriented and sell tax is entirely marketing-oriented: liquidityBuyTaxBps = 500, marketingBuyTaxBps = 0 → totalBuy = 500 liquiditySellTaxBps = 0, marketingSellTaxBps = 6500 → totalSell = 6500 The formula computes liquidity share as 500 / 7000 = 7.1% regardless oftrading activity. But real fee composition depends on volumes: Scenario A — mostly sells: Buys: 1M tokens × 5% = 50K tokens (100% liquidity) Sells: 4M tokens × 65% = 2.6M tokens (100% marketing) Pool total: 2.65M tokens Real liquidity share: 50K / 2.65M = 1.9% Formula applies: 7.1% Result: liquidity receives ~3.7x more than it should (taken from marketing's share) 35 Scenario B — mostly buys: 4M tokens × 5% = 200K tokens (100% liquidity) Sells: 1M tokens × 65% = 650K tokens (100% marketing) Pool total: 850K tokens Real liquidity share: 200K / 850K = 23.5% Formula applies: liquidity receives ~3.3x less than it should (surplus goes to marketing) The same 7.1% ratio propagates through all three allocation stages: tokenreservation for LP, `ETH` denominator calculation, and `ETH` split. The errordirection is consistent across all stages and compounds in the samedirection. Fee distribution between marketing and liquidity receivers may deviatesignificantly from the fees actually collected for each purpose. Themagnitude scales with the asymmetry between buy-side and sell-side taxconfigurations and with the imbalance between buy and sell tradingvolumes. User balances are not affected. Both receivers are currentlyconfigured to the same owner-controlled address, which limits practicalimpact under the current deployment configuration. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
Fee accrual should be tracked separately by purpose instead ofaggregating all taxed tokens into a single undifferentiated balance. Distinctcounters should be maintained for marketing and liquidity allocations, and `_autoSwapBack` should consume those tracked amounts directly. If the current approximation is intentional, the resulting allocationinaccuracy should be documented explicitly. 36 Resolution: Fixed inc20e980: In KnoxNet, fee accrual has been replaced with per-purpose trackingusing dedicated accumulatedMarketingTokens and accumulatedLiquidityTokens counters. The `_applyTax` function now splits each taxed amount at the pointof collection based on the actual buy/sell direction and its configured taxcomposition, rather than deferring the split to distribution time. The `_autoSwapBack` function consumes these tracked amounts directly anddistributes proportionally to the real accumulated balances, eliminating theprior dependency on a static rate-based formula that ignored actualtrading volumes. function `_applyTax`( address sender, address recipient, uint256 amount ) internal returns (uint256) { bool selling = `_classifyTransfer`(sender, recipient) == TransferType.Sell; uint256 totalTaxBps = selling ? totalSellTaxBps : totalBuyTaxBps; uint256 liquidityTaxBps = selling ? liquiditySellTaxBps : liquidityBuyTaxB ps; uint256 liquidityTokens = (taxAmount * liquidityTaxBps) / totalTaxBps; uint256 marketingTokens = taxAmount - liquidityTokens; accumulatedLiquidityTokens += liquidityTokens; accumulatedMarketingTokens += marketingTokens; } function `_autoSwapBack`(uint256 amount) internal swapping { // … uint256 totalAccumulatedTokens = accumulatedMarketingTokens + accumulatedL iquidityTokens; if (totalAccumulatedTokens == 0) return; if (amountToSwap > totalAccumulatedTokens) amountToSwap = totalAccumulated Tokens; uint256 liquidityPortion = (accumulatedLiquidityTokens * amountToSwap) / t otalAccumulatedTokens; uint256 marketingPortion = amountToSwap - liquidityPortion; } 37

### 修補方式（實際）
Fixed inc20e980: In KnoxNet, fee accrual has been replaced with per-purpose trackingusing dedicated accumulatedMarketingTokens and accumulatedLiquidityTokens counters. The `_applyTax` function now splits each taxed amount at the pointof collection based on the actual buy/sell direction and its configured taxcomposition, rather than deferring the split to distribution time. The `_autoSwapBack` function consumes these tracked amounts directly anddistributes proportionally to the real accumulated balances, eliminating theprior dependency on a static rate-based formula that ignored actualtrading volumes. function `_applyTax`( address sender, address recipient, uint256 amount ) internal returns (uint256) { bool selling = `_classifyTransfer`(sender, recipient) == TransferType.Sell; uint256 totalTaxBps = selling ? totalSellTaxBps : totalBuyTaxBps; uint256 liquidityTaxBps = selling ? liquiditySellTaxBps : liquidityBuyTaxB ps; uint256 liquidityTokens = (taxAmount * liquidityTaxBps) / totalTaxBps; uint256 marketingTokens = taxAmount - liquidityTokens; accumulatedLiquidityTokens += liquidityTokens; accumulatedMarketingTokens += marketingTokens; } function `_autoSwapBack`(uint256 amount) internal swapping { // … uint256 totalAccumulatedTokens = accumulatedMarketingTokens + accumulatedL iquidityTokens; if (totalAccumulatedTokens == 0) return; if (amountToSwap > totalAccumulatedTokens) amountToSwap = totalAccumulated Tokens; uint256 liquidityPortion = (accumulatedLiquidityTokens * amountToSwap) / t otalAccumulatedTokens; uint256 marketingPortion = amountToSwap - liquidityPortion; } 37

## F-2026-14942 - Incorrect max Sell Amount Calculation Allows Selling Up to Total Supply Amount
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
The `NTE` contract is an `ERC` 20 token that implements an anti-dumpmechanism to limit the maximum amount of tokens that can be sold in asingle transaction. This behavior is controlled by the antiDumpEnabled flag.When enabled, sell transactions are restricted based on the maxSellPercentage parameter, which represents the maximum allowed sellamount as a percentage of the total token supply. According to the implementation and validation logic in the `setAntiDumpConfig()` function, maxSellPercentage cannot exceed a value of 100,where 100 represents 1% (expressed in basis points). function `setAntiDumpConfig(bool enabled, uint256 maxPercentage, uint256 coold ownTime)` external onlyOwner { if (maxPercentage == 0 || maxPercentage > 100) revert `DUMP_PERCENT`(); } However, the current calculation of maxSellAmount inside the `_transferWithTax`() function uses an incorrect denominator. The calculationdivides by 100 instead of 10000 (basis points), which causes the sell limit tobe miscalculated and effectively disables the intended restriction. // `_transferWithTax`() if (antiDumpEnabled && isToPair && !taxExempt[from]) { uint256 maxSellAmount = (`_totalSupply` * maxSellPercentage) / 100; if (amount > maxSellAmount) revert `DUMP_EXCEEDS`(); } For example, if maxSellPercentage is 100 (= 1%), the following calculation willresult in maxSellAmount = `_totalSupply` * 100 / 100 = `_totalSupply`. As a result,the anti-dump mechanism can be bypassed, allowing users to sell up tothe entire token supply in a single transaction, even when antiDumpEnabled isset to true. This current flaw completely undermines the sell-limit protectionmechanism and exposes the protocol to the following risks: Anti-dump logic bypass: Users can sell up to totalSupply in a singletransaction despite configured limits. 16 Tokenomics disruption: Large, unrestricted sell transactions maycause sudden price crashes and market instability.Mismatch with documentation and expectations: The actualbehavior deviates from documented constraints and projectassumptions.Loss of user trust: Holders may be exposed to unexpected dilution orprice manipulation events. Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Consider updating the maxSellAmount calculation to correctly apply basis-point arithmetic by using 10000 as the denominator: uint256 maxSellAmount = (`_totalSupply` * maxSellPercentage) / 10000; Resolution: Fixed in 3ac4ad1, the maxSellAmount calculation was updated to correctlyapply basis-point arithmetic by using 10000 as the denominator: 17

### 修補方式（實際）
Fixed in 3ac4ad1, the maxSellAmount calculation was updated to correctlyapply basis-point arithmetic by using 10000 as the denominator: uint256 maxSellAmount = (`_totalSupply` * maxSellPercentage) / 10000; 17

## F-2026-15019 - Double Taxation on Liquidity ETH Removal via Router
- 嚴重度：High
- Report source：Node Meta.pdf

### 問題內容（完整）
The `NTE` token implements two distinct taxation mechanisms: `AMM` interaction tax: applied to buy/sell operations involving theliquidity pair.Transfer tax: applied to direct token transfers between externallyowned accounts EOAs . function `_calculateTax`(address from, address to, uint256 amount) private view returns (uint256) { uint256 taxBps = 0; if (isPancakePair[from] && !isPancakePair[to]) { // Buy: from `DEX` to user taxBps = buyTaxBps; } else if (!isPancakePair[from] && isPancakePair[to]) { // Sell: from user to `DEX` taxBps = sellTaxBps; } else if (isPancakePair[from] && isPancakePair[to]) { // Pool-to-pool move (usually arbitrage) taxBps = sellTaxBps; } else { // Just a regular P2P transfer taxBps = transferTaxBps; if (taxBps == 0) return 0; // Check for math overflow before we calculate if (amount > `type(uint256)`.max / taxBps) revert `TXN_OVERFLOW`(); return (amount * taxBps) / `BASIS_POINTS`; } During a liquidity `ETH` removal operation executed via the `DEX` router, thecurrent tax logic unintentionally applies both taxes, resulting in doubletaxation for a single user action. Specifically, when liquidity is removed: 9 Tokens are transferred from the liquidity pair to the router, where thetransaction is interpreted as an `AMM` buy and the buy tax is applied. function `removeLiquidityETHSupportingFeeOnTransferTokens( … )` public virtual override `ensure(deadline)` returns (uint amountToken, uint am ountETH) { // The first transfer triggerred from pair to router (, amountETH) = removeLiquidity( token, `WETH`, liquidity, amountTokenMin, amountETHMin, `address(this)`, // <-- router address passed as recipient of the token s from pair deadline ); } function `removeLiquidity( … )` public virtual override `ensure(deadline)` returns (uint amountA, uint amount B) { address pair = `PancakeLibrary.pairFor(factory, tokenA, tokenB)`; `IPancakePair(pair)`.transferFrom(`msg.sender`, pair, liquidity); // send liq uidity to pair (uint amount0, uint amount1) = `IPancakePair(pair)`.`burn(to)`; // `transfer()` from pair to router occur … } Tokens are subsequently transferred from the router to the end user,where the transfer is treated as a regular token transfer and thetransfer tax is applied again. ) public virtual override `ensure(deadline)` returns (uint amountToken, uint am ountETH) { … // the second transfer from router to user <to> `TransferHelper.safeTransfer(token, to, IERC20(token)`.`balanceOf(address(th is)`)); 10 … } As a result, liquidity removal transactions are taxed twice, despiterepresenting a single economic operation initiated by the user. It may lead to: Users removing liquidity receive significantly fewer tokens thanexpected due to compounded taxation.Liquidity providers are economically penalized, discouragingparticipation and reducing protocol liquidity.The effective tax rate during liquidity removal may exceed intendedlimits, potentially breaking economic assumptions of the tokenomics.This behavior deviates from standard `AMM` expectations, increasingthe risk of user confusion, complaints, or loss of trust.In extreme configurations, the compounded tax may make liquidityremoval economically unviable by breaking the `AMM` constantformula. Additionally, the double-taxation flaw only occurs when liquidity isremoved using the `ETH`-supporting `function(removeLiquidityETHSupportingFeeOnTransferTokens)`. In this flow, the router actsas an intermediate recipient, causing an additional transfer tax to beapplied. The non-`ETH` `removeLiquidity()` variant (which returns WBNBinstead of native `BNB`) performs a direct pair-to-user transfer and does nottrigger the same double-tax behavior. Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Adjust the taxation logic to ensure that liquidity removal operations aretaxed at most once. it can be done by validating that the transfer tax is not 11 applied if one of the participants address is router, for example: } else if (pancakeRouter != from && pancakeRouter != to){ // Just a regular P2P transfer taxBps = transferTaxBps; } Resolution: Fixed in 363459b, the regular transfer is now checked if the transfer did notcome form the router: else if (pancakeRouter != from && pancakeRouter != to) { // Just a regular P2P transfer (exclude router to prevent double taxation on liquidity removal) taxBps = transferTaxBps;

### 修補方式（實際）
Fixed in 363459b, the regular transfer is now checked if the transfer did notcome form the router: else if (pancakeRouter != from && pancakeRouter != to) { // Just a regular P2P transfer (exclude router to prevent double taxation on liquidity removal) taxBps = transferTaxBps;

## F-2026-15970 - Missing Transfer Event for Taxed Amount Breaks ERC20 Compliance and Causes Balance Tracking Mismatches
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, taxed transfers move a portion of tokens from the sender tothe contract balance without emitting a corresponding Transfer event forthat amount. Only the net amount sent to the recipient is emitted. Thisbreaks the expected ERC20 event model and causes on-chain eventhistory to diverge from actual balance changes. In KnoxNet, the transfer and transferFrom flows route through `_transferFrom`, which deducts the full amount from the sender, applies taxthrough `_applyTax`, credits the contract with the taxed portion, and emitsonly a single Transfer event for the post-tax amount: function `_transferFrom`( address sender, address recipient, uint256 amount ) internal returns (bool) { // … `_balances`[sender] = `_balances`[sender] - amount; uint256 amountReceived = amount; if (`_shouldApplyTax`(sender, recipient)) { amountReceived = `_applyTax`(recipient, amount); } `_balances`[recipient] = `_balances`[recipient] + amountReceived; emit `Transfer(sender, recipient, amountReceived)`; return true; } The taxed amount is added to the contract balance in `_applyTax`, but no `Transfer(sender, address(this)`, taxAmount) event is emitted for that balancemovement: function `_applyTax`( address recipient, uint256 amount ) internal returns (uint256) { bool selling = liquidityPools[recipient]; uint256 taxAmount = (amount * `getTotalTaxBps(selling)`) / taxDenominator; `_balances`[`address(this)`] += taxAmount; 26 return amount - taxAmount; } As a result, event consumers observe only the net transfer, while thecontract balance increases without a matching ERC20 transfer log. Block explorers, indexers, accounting systems, and integrations thatreconstruct balances from Transfer events may report incorrect tokenmovements. Tax collection becomes non-transparent at the event layer,and emitted transfer history no longer fully reflects actual token balancetransitions. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
A separate Transfer event should be emitted for the taxed portionwhenever tokens are credited to the contract. The recipient transfer eventshould continue to reflect only the net amount received. function `_transferFrom`( address sender, address recipient, uint256 amount ) internal returns (bool) { // … `_balances`[sender] -= amount; uint256 amountReceived = amount; uint256 taxAmount; if (`_shouldApplyTax`(sender, recipient)) { bool selling = liquidityPools[recipient]; taxAmount = (amount * `getTotalTaxBps(selling)`) / taxDenominator; 27 `_balances`[`address(this)`] += taxAmount; amountReceived = amount - taxAmount; emit `Transfer(sender, address(this)`, taxAmount); } `_balances`[recipient] += amountReceived; emit `Transfer(sender, recipient, amountReceived)`; return true; } Resolution: Fixed inc20e980: In KnoxNet, taxed transfers now emit a dedicated Transfer event for theportion credited to the contract. The `_applyTax` function adds the taxedamount to `address(this)` and emits `Transfer(sender, address(this)`, taxAmount),while `_transferFrom` continues to emit the net transfer to the recipient. Theevent stream now reflects both balance movements and aligns with ERC20event expectations for taxed transfers. function `_applyTax`( address sender, address recipient, uint256 amount ) internal returns (uint256) { bool selling = `_classifyTransfer`(sender, recipient) == TransferType.Sell; uint256 totalTaxBps = selling ? totalSellTaxBps : totalBuyTaxBps; if (totalTaxBps == 0) return amount; uint256 taxAmount = (amount * totalTaxBps) / taxDenominator; if (taxAmount == 0) return amount; `_balances`[`address(this)`] += taxAmount; return amount - taxAmount; } 28

### 修補方式（實際）
Fixed inc20e980: In KnoxNet, taxed transfers now emit a dedicated Transfer event for theportion credited to the contract. The `_applyTax` function adds the taxedamount to `address(this)` and emits `Transfer(sender, address(this)`, taxAmount),while `_transferFrom` continues to emit the net transfer to the recipient. Theevent stream now reflects both balance movements and aligns with ERC20event expectations for taxed transfers. function `_applyTax`( address sender, address recipient, uint256 amount ) internal returns (uint256) { bool selling = `_classifyTransfer`(sender, recipient) == TransferType.Sell; uint256 totalTaxBps = selling ? totalSellTaxBps : totalBuyTaxBps; if (totalTaxBps == 0) return amount; uint256 taxAmount = (amount * totalTaxBps) / taxDenominator; if (taxAmount == 0) return amount; `_balances`[`address(this)`] += taxAmount; emit `Transfer(sender, address(this)`, taxAmount); return amount - taxAmount; } 28

## Cyfrin Fixed Issues (Merged)
- Count: `81`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Incorrect reward claim logic causes loss of access to intermediate epoch rewards
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In the current implementation of `Rewards::distributeRewards`, all shares are calculated for participants after a 3-epoch delay between the current epoch and the one being distributed. However, an issue arises in the **claim logic**.

When rewards are claimed for a past epoch, the `lastEpochClaimedOperator` is updated unconditionally to `currentEpoch - 1`. This can block claims for **intermediate epochs** that were not yet distributed at the time of the first claim.

**Problem Scenario**

Consider the following sequence:

1. **Epoch 4**: Rewards are distributed for **epoch 1**
2. **Epoch 5**: Operator1 claims rewards → `lastEpochClaimedOperator = 4`
3. **Epoch 5**: Rewards are now distributed for **epoch 2**
4. **Epoch 5**: Operator1 attempts to claim rewards for **epoch 2**, but it's **blocked** because `lastEpochClaimedOperator > 2`

As a result, the operator **loses access** to claimable rewards from epoch 2.

**Problematic Code**

```solidity
if (totalRewards == 0) revert NoRewardsToClaim(msg.sender);
IERC20(rewardsToken).safeTransfer(recipient, totalRewards);
lastEpochClaimedOperator[msg.sender] = currentEpoch - 1; // <-- Incorrectly skips intermediate epochs
```

**Impact:** **Loss of Funds** — Users (operators) are permanently prevented from claiming their legitimate rewards if intermediate epochs are distributed after a later claim has already advanced `lastEpochClaimedOperator`.

**Proof of Concept:** Add this test case to `RewardTest.t.sol` to reproduce the issue:

```solidity
function test_distributeRewards_claimFee(uint256 uptime) public {
    uint48 epoch = 1;
    uptime = bound(uptime, 0, 4 hours);

    _setupStakes(epoch, uptime);
    _setupStakes(epoch + 2, uptime);

    address[] memory operators = middleware.getAllOperators();
    uint256 batchSize = 3;
    uint256 remainingOperators = operators.length;

    vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
    while (remainingOperators > 0) {
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.distributeRewards(epoch, uint48(batchSize));
        remainingOperators = remainingOperators > batchSize ? remainingOperators - batchSize : 0;
    }

    vm.warp((epoch + 4) * middleware.EPOCH_DURATION());

    for (uint256 i = 0; i < operators.length; i++) {
        uint256 operatorShare = rewards.operatorShares(epoch, operators[i]);
        if (operatorShare > 0) {
            vm.prank(operators[i]);
            rewards.claimOperatorFee(address(rewardsToken), operators[i]);
            assertGt(rewardsToken.balanceOf(operators[i]), 0, "Operator should receive rewards ");
            vm.stopPrank();
            break;
        }
    }

    vm.warp((epoch + 5) * middleware.EPOCH_DURATION());
    remainingOperators = operators.length;
    while (remainingOperators > 0) {
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.distributeRewards(epoch + 2, uint48(batchSize));
        remainingOperators = remainingOperators > batchSize ? remainingOperators - batchSize : 0;
    }

    vm.warp((epoch + 9) * middleware.EPOCH_DURATION());
    for (uint256 i = 0; i < operators.length; i++) {
        uint256 operatorShare = rewards.operatorShares(epoch + 2, operators[i]);
        if (operatorShare > 0) {
            vm.prank(operators[i]);
            rewards.claimOperatorFee(address(rewardsToken), operators[i]);
            vm.stopPrank();
            break;
        }
    }
}
```

**Recommended Mitigation:** Update the `claimOperatorFee` logic to **only update** `lastEpochClaimedOperator` to the **maximum epoch for which the user has successfully claimed rewards**, instead of always assigning `currentEpoch - 1`.

**Suzaku:**
Fixed in commit [6a0cbb1](https://github.com/suzaku-network/suzaku-core/pull/155/commits/6a0cbb1faa796e8925decad1ce9860eb20f184e7).

**Cyfrin:** Verified.

## [C-2] Impossible to claim rewards when `XPTiers` are not set, resulting in permanently locked tokens once game has concluded
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DefaultSession::setXPTiers` enforces that XP tiers  can only be set when the game is in the Created state:

```solidity
 function setXPTiers(uint256 gameId, uint256[] memory _xpTiers) external {
        require(
            msg.sender == SessionManager(sessionManager).getCreator(gameId),
            NotGameCreator(SessionManager(sessionManager).getCreator(gameId), msg.sender)
        );
        require(_xpTiers.length >= 2, ArrayLengthMismatch());
        require(SessionManager(sessionManager).getSessionState(gameId) == SessionState.Created, GameNotCreated(gameId)); <--------
        xpTiers[gameId] = _xpTiers;
        emit XpTiersUpdated(gameId, _xpTiers);
    }
```

But `SessionManager::startAndRevealGameQuestion`  will start the game without XP Tier being set, and the game will progress all the way to the final Concluded state. This will affect `SPBinaryPrompt.sol` and `TriviaChoicePrompt.sol` which are using the XP tiers to get the results:
```solidity
function getResult(uint256 gameId, uint256 questionId, address user) public view returns (Result memory) {
        SessionManager sessionManager = SessionManager(revealedQuestions[questionId].sessionManager);
        uint256 score = getScore(questionId, user);
        address sessionStrategy = sessionManager.getSessionStrategy(gameId);
        uint256[] memory xpTiers = ISessionStrategy(sessionStrategy).getXPTiers(gameId); <-------
        if (score > 0) {
            return
                Result({xp: xpTiers[0] / 2 + score * xpTiers[0] / 2 / 10000, time: _getReactionTime(questionId, user)});
        } else {
            return Result({xp: xpTiers[1], time: _getReactionTime(questionId, user)});
        }
    }
```

These xp results are being used by `assertResults` but since the xp are not set the xp for user will be all zero.
```solidity
 function assertResults(
        uint256 sessionId,
        string calldata resultCid,
        address[] calldata proposedWinners,
        uint256[] calldata totalXPs, <-----
        uint256[] calldata totalTimes
```

When user is going to claim his rewards he end up receiving zero amount because the rewards are base in the xp; note this is valid just for `ProportionalToXpReward` strategy.

**Impact:** Once the game has concluded, when the winners try to claim their rewards they will end up receiving zero amount.

**Proof of Concept:** Run this proof of concept in `test/SessionManagerEndGameTest`
```solidity
 function test_getGameEndTime_notXptiers_set() public {
        _createGame_notSession();

        vm.prank(address(this));
        FixedRanksReward(address(rewardStrategy)).setRankedRewards(1, Solarray.uint256s(10000));

        _startGame();
        _revealQuestion();
        _warpToEndTime();
        sessionManager.endGame(1);
        _concludeGame();
    }

    function _createGame_notSession() internal {
        uint256 _startTime = block.timestamp + 1 days;
        uint256 _endTime = _startTime + sessionManager.maxGameDuration() - 1 seconds;

        uint256 gameId = sessionManager.createGame({
            _startTime: _startTime,
            _endTime: _endTime,
            _ticketPrice: 10 ether,
            _creatorFee: 1000,
            _creatorFeeReceiver: address(this),
            _token: usdc,
            _promptHashes: promptHashes,
            _promptStrategies: promptStrategies,
            _sessionStrategy: sessionStrategy,
            _rewardStrategy: rewardStrategy,
            _verificationRequired: false
        });
    }

```

**Recommended Mitigation:** Same as `H-3`; don't allow the game to be started unless the xp tiers have been set.

**Majority Games:**
Fixed in commit [65727de](https://github.com/Engage-Protocol/engage-protocol/commit/65727de8b15027a8ac8b61b7203be692e60f34cb).

**Cyfrin:** Verified.

## [M-3] `non Reentrant` is not the first modifier
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** In `FeeManager::withdrawProtocolFee`, `nonReentrant` is not the first modifier. To protect against reentrancy in other modifiers, the `nonReentrant` modifier should be the first modifier in the list of modifiers. Consider putting `nonReentrant` first for consistent reentrancy protection.

**Accountable:** Fixed in commit [`c7f31b5`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/c7f31b51fc1bfb4fe96450a189751f6f72d8274d)

**Cyfrin:** Verified.

## [M-4] Auto-draw on `Accountable Fixed Term::pay` lets third parties force unwanted borrowing
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
In [`AccountableFixedTerm::pay`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/strategies/AccountableFixedTerm.sol#L354-L357), any positive `_loan.drawableFunds` are automatically drawn via `_updateAndRelease(drawableFunds)` before transferring the due interest/fees:
```solidity
uint256 drawableFunds = _loan.drawableFunds;
if (drawableFunds > 0) {
    _updateAndRelease(drawableFunds);
}
```

Since `_loan.drawableFunds` increases when users deposit/mint into the vault, a third party can deposit immediately before the borrower calls `pay`. This causes `pay` to both increase `_loan.outstandingPrincipal` by the new liquidity and also add remaining-term interest on that added principal, while releasing the assets to the borrower, without borrower consent.

**Impact:** Borrower loses discretion over principal size. Calling `pay` can increase debt (principal + future interest) unexpectedly. This enables griefing/economic DoS as attackers can “stuff” the vault before each payment window, repeatedly forcing draws and increasing interest payments in the future.

**Recommended Mitigation:** Consider removing auto-draw from `AccountableFixedTerm::pay`. Loan increases should occur only via an explicit borrower action (e.g., `draw(uint256)`), not implicitly during interest payment.

**Accountable:** Fixed in commit [`03f871b`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/03f871bfc7baff5fe5f9dfbd8a0ef74e99619e78)

**Cyfrin:** Verified. "auto-draw" is removed from `pay`.

## [M-6] `Angstrom L2::_compute And Collect Protocol Swap Fee` computation can be simplified
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `AngstromL2::_computeAndCollectProtocolSwapFee` currently performs the following computation:

```solidity
    uint256 fee = exactIn
        ? absTargetAmount * protocolFeeE6 / FACTOR_E6
@>      : absTargetAmount * FACTOR_E6 / (FACTOR_E6 - protocolFeeE6) - absTargetAmount;
    fee128 = fee.toInt128();
```

However, the highlighted line can be simplified to:

```diff
absTargetAmount * protocolFeeE6 / (FACTOR_E6 - protocolFeeE6)
```

**Sorella Labs:** Fixed in commit [aa90806](https://github.com/SorellaLabs/l2-angstrom/commit/aa9080697d683aae327de2c64f638f2730c193dd).

**Cyfrin:** Verified. The calculation has been simplified.

\clearpage

## [M-7] `Angstrom L2::_one For Zero Credit Rewards` should skip execution of range reward logic if there is no liquidity
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** When crediting top-of-block tax rewards, `AngstromL2::_zeroForOneCreditRewards` skips execution if there is no liquidity in the given range:

```solidity
if (tickNext >= lastTick && liquidity != 0) {
```

However, the equivalent condition within `AngstromL2::_oneForZeroCreditRewards` is implemented incorrectly:

```solidity
if (tickNext <= lastTick || liquidity == 0) {
```

This causes execution to continue into the range reward calculation logic even when there is no liquidity in the given range. This is effectively a no-op since:

* `delta0` and `delta1` will both be evaluated as `0`.
* `rangeReward` will thus also be assigned as `0`.
* `taxInEther` will remain unchanged.
* `cumulativeGrowthX128` will also remain unchanged, although this is almost accidental as `PoolRewardsLib::getGrowthDelta` will return zero when called with zero liquidity due to the behavior of `FixedPointMathLib::rawDiv`, narrowly avoiding a revert.

```solidity
    function getGrowthDelta(uint256 reward, uint256 liquidity)
        internal
        pure
        returns (uint256 growthDeltaX128)
    {
        if (!(reward < 1 << 128)) revert RewardOverflow();
@>      return (reward << 128).rawDiv(liquidity);
    }
```

Therefore, this logic should be skipped when there is no liquidity inside the range.

**Proof of Concept:** The following standalone file should be added to the test suite:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/console2.sol";
import {Pretty} from "./_helpers/Pretty.sol";
import {PoolRewards, PoolRewardsLib} from "../src/types/PoolRewards.sol";
import {CompensationPriceFinder} from "../src/libraries/CompensationPriceFinder.sol";
import {TickIteratorLib, TickIteratorUp} from "../src/libraries/TickIterator.sol";
import {SqrtPriceMath} from "v4-core/src/libraries/SqrtPriceMath.sol";
import {Q96MathLib} from "../src/libraries/Q96MathLib.sol";
import {FixedPointMathLib} from "solady/src/utils/FixedPointMathLib.sol";
import {MixedSignLib} from "../src/libraries/MixedSignLib.sol";
import {Slot0} from "v4-core/src/types/Slot0.sol";

import {BaseTest} from "./_helpers/BaseTest.sol";
import {RouterActor} from "./_mocks/RouterActor.sol";
import {MockERC20} from "super-sol/mocks/MockERC20.sol";
import {UniV4Inspector} from "./_mocks/UniV4Inspector.sol";
import {IPoolManager} from "v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/src/types/PoolId.sol";
import {Currency} from "v4-core/src/types/Currency.sol";
import {IHooks} from "v4-core/src/interfaces/IHooks.sol";
import {BalanceDelta} from "v4-core/src/types/BalanceDelta.sol";
import {TickMath} from "v4-core/src/libraries/TickMath.sol";
import {LPFeeLibrary} from "v4-core/src/libraries/LPFeeLibrary.sol";

import {AngstromL2} from "../src/AngstromL2.sol";
import {getRequiredHookPermissions, POOLS_MUST_HAVE_DYNAMIC_FEE} from "../src/hook-config.sol";
import {IUniV4} from "../src/interfaces/IUniV4.sol";

import {IFlashBlockNumber} from "src/interfaces/IFlashBlockNumber.sol";

contract AngstromL2RewardsTest is BaseTest {

    using PoolIdLibrary for PoolKey;
    using IUniV4 for UniV4Inspector;
    using IUniV4 for IPoolManager;
    using TickMath for int24;
    using Q96MathLib for uint256;
    using FixedPointMathLib for *;
    using MixedSignLib for *;

    using Pretty for *;

    UniV4Inspector manager;
    RouterActor router;
    AngstromL2 angstrom;

    MockERC20 token;

    uint160 constant INIT_SQRT_PRICE = 1 << 96; // 1:1 price
    int24[2][] positionRanges; // Track positions ranges added with addLiquidity helper
    mapping(PoolId id => PoolRewards) internal rewardsModified;
    mapping(PoolId id => PoolRewards) internal rewardsOriginal;

    function setUp() public {
        vm.roll(100);
        manager = new UniV4Inspector();
        router = new RouterActor(manager);
        vm.deal(address(router), 100 ether);

        token = new MockERC20();
        token.mint(address(router), 1_000_000_000e18);

        angstrom = AngstromL2(
            deployAngstromL2(
                type(AngstromL2).creationCode,
                IPoolManager(address(manager)),
                address(this),
                getRequiredHookPermissions(),
                IFlashBlockNumber(address(0))
            )
        );
    }

    function initializePool(address asset1, int24 tickSpacing, int24 startTick)
        internal
        returns (PoolKey memory key)
    {
        require(asset1 != address(0), "Token cannot be address(0)");

        key = PoolKey({
            currency0: Currency.wrap(address(0)),
            currency1: Currency.wrap(asset1),
            fee: POOLS_MUST_HAVE_DYNAMIC_FEE ? LPFeeLibrary.DYNAMIC_FEE_FLAG : 0,
            tickSpacing: tickSpacing,
            hooks: IHooks(address(angstrom))
        });

        manager.initialize(key, TickMath.getSqrtPriceAtTick(startTick));

        return key;
    }

    /// @notice Helper to add liquidity on a given tick range
    /// @param key The pool key
    /// @param tickLower The lower tick of the range
    /// @param tickUpper The upper tick of the range
    /// @param liquidityAmount The amount of liquidity to add
    function addLiquidity(
        PoolKey memory key,
        int24 tickLower,
        int24 tickUpper,
        uint128 liquidityAmount
    ) internal returns (BalanceDelta delta) {
        require(tickLower % key.tickSpacing == 0, "Lower tick not aligned");
        require(tickUpper % key.tickSpacing == 0, "Upper tick not aligned");
        require(tickLower < tickUpper, "Invalid tick range");

        (delta,) = router.modifyLiquidity(
            key, tickLower, tickUpper, int256(uint256(liquidityAmount)), bytes32(0)
        );

        // console.log("delta.amount0(): %s", delta.amount0().fmtD());
        // console.log("delta.amount1(): %s", delta.amount1().fmtD());
        positionRanges.push([tickLower, tickUpper]);

        return delta;
    }

    /*
     *  Shows that this doesn't revert even though it crosses through
     *  a range of zero liquidity
     */
    function test_cyfrin_TestOneForZeroOnZeroLiquidityRange() public {
        PoolKey memory key = initializePool(address(token), 10, 3);

        setPriorityFee(100 gwei);
        addLiquidity(key, 0,  10, 1e22);
        /* Leave a gap of zero liquidity */
        addLiquidity(key, 20, 30, 1e22);
        router.swap(key, false, 1000e18, int24(25).getSqrtPriceAtTick());
        logRewards("after", key);
    }

    function test_cyfrin_PoolRewardsGetGrowthDeltaDoesntRevertOnZeroLiqudity() public {
        PoolRewardsLib.getGrowthDelta(0,0);
    }

    error RewardOverflow();

    /// forge-config: default.allow_internal_expect_revert = true
    function test_cyfrin_GetGrowthDeltaWouldRevertWithoutRawDiv() public {
         vm.expectRevert();
        _getGrowthDelta(0,0);
    }

    function test_cyfrin_OneForZeroCreditRewardsWorksWithModifiedLogic() public {
        uint128 LIQUIDITY = 1e22;
        uint256 PRIORITY_FEE = 100 gwei;
        int24[4] memory TICKS_TO_CHECK = [int24(0), 10, 20, 30];


        PoolKey memory key = initializePool(address(token), 10, 3);
        PoolId id = key.toId();

        setPriorityFee(PRIORITY_FEE);
        addLiquidity(key, 0,  10, LIQUIDITY);
        /* Leave a gap of zero liquidity */
        addLiquidity(key, 20, 30, LIQUIDITY);

        Slot0 slot0BeforeSwap = manager.getSlot0(id);
        router.swap(key, false, 1000e18, int24(25).getSqrtPriceAtTick());
        Slot0 slot0AfterSwap = manager.getSlot0(id);

        TickIteratorUp memory ticks = TickIteratorLib.initUp(
            IPoolManager(manager), id, 10, slot0BeforeSwap.tick(), slot0AfterSwap.tick()
        );

        uint256 taxInEther = angstrom.getSwapTaxAmount(PRIORITY_FEE);

        (int24 lastTick, uint160 pstarSqrtX96) = CompensationPriceFinder.getOneForZero(
            ticks, LIQUIDITY, taxInEther, slot0BeforeSwap, slot0AfterSwap
        );

        _oneForZeroCreditRewardsModified(ticks,1e22,taxInEther,slot0BeforeSwap.sqrtPriceX96(),lastTick,pstarSqrtX96);
        _oneForZeroCreditRewardsOriginal(ticks,1e22,taxInEther,slot0BeforeSwap.sqrtPriceX96(),lastTick,pstarSqrtX96);

        assertEq(rewardsOriginal[id].globalGrowthX128, rewardsModified[id].globalGrowthX128);


        for (uint256 i = 0; i < TICKS_TO_CHECK.length; i++) {
            int24 tick = TICKS_TO_CHECK[i];
            assertEq(rewardsOriginal[id].rewardGrowthOutsideX128[tick],
                     rewardsModified[id].rewardGrowthOutsideX128[tick]);
        }

    }


    /*********************************************************************/

    /*
     * Logic copied from PoolRewardsLib.getGrowthDelta and modified to not use `rawDiv`
     */
    function _getGrowthDelta(uint256 reward, uint256 liquidity)
        internal
        pure
        returns (uint256 growthDelta)
    {
        if (!(reward < 1 << 128)) revert RewardOverflow();
        return (reward << 128) / (liquidity);
    }

    function _min(uint160 x, uint160 y) internal pure returns (uint160) {
        return x < y ? x : y;
    }

    /*
     * Logic copied from AngstromL2.sol and modified to have following if-condition:
     *
     *    if (tickNext <= lastTick && liquidity != 0) {
     *
     * Also code modifies `rewardsModified` instead of `rewards` mapping
     */
    function _oneForZeroCreditRewardsModified(
        TickIteratorUp memory ticks,
        uint128 liquidity,
        uint256 taxInEther,
        uint160 priceLowerSqrtX96,
        int24 lastTick,
        uint160 pstarSqrtX96
    ) internal {
        uint256 pstarX96 = uint256(pstarSqrtX96).mulX96(pstarSqrtX96);
        uint256 cumulativeGrowthX128 = 0;
        uint160 priceUpperSqrtX96;

        while (ticks.hasNext()) {
            int24 tickNext = ticks.getNext();

            priceUpperSqrtX96 = _min(TickMath.getSqrtPriceAtTick(tickNext), pstarSqrtX96);

            uint256 rangeReward = 0;
            if (tickNext <= lastTick && liquidity != 0) {
                uint256 delta0 = SqrtPriceMath.getAmount0Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                uint256 delta1 = SqrtPriceMath.getAmount1Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                rangeReward = (delta0 - delta1.divX96(pstarX96)).min(taxInEther);

                unchecked {
                    taxInEther -= rangeReward;
                    cumulativeGrowthX128 += PoolRewardsLib.getGrowthDelta(rangeReward, liquidity);
                }
            }

            unchecked {
                rewardsModified[ticks.poolId].rewardGrowthOutsideX128[tickNext] += cumulativeGrowthX128;
            }

            (, int128 liquidityNet) = ticks.manager.getTickLiquidity(ticks.poolId, tickNext);
            liquidity = liquidity.add(liquidityNet);

            priceLowerSqrtX96 = priceUpperSqrtX96;
        }

        // Distribute remainder to last range and update global accumulator.
        unchecked {
            cumulativeGrowthX128 += PoolRewardsLib.getGrowthDelta(taxInEther, liquidity);
            rewardsModified[ticks.poolId].globalGrowthX128 += cumulativeGrowthX128;
        }
    }

    /*
     * Original logic for _oneForZeroCreditRewards but modifying `rewardsOriginal` instead of `rewards` mapping
     */

    function _oneForZeroCreditRewardsOriginal(
        TickIteratorUp memory ticks,
        uint128 liquidity,
        uint256 taxInEther,
        uint160 priceLowerSqrtX96,
        int24 lastTick,
        uint160 pstarSqrtX96
    ) internal {
        uint256 pstarX96 = uint256(pstarSqrtX96).mulX96(pstarSqrtX96);
        uint256 cumulativeGrowthX128 = 0;
        uint160 priceUpperSqrtX96;

        while (ticks.hasNext()) {
            int24 tickNext = ticks.getNext();

            priceUpperSqrtX96 = _min(TickMath.getSqrtPriceAtTick(tickNext), pstarSqrtX96);

            uint256 rangeReward = 0;
            if (tickNext <= lastTick || liquidity == 0) {
                uint256 delta0 = SqrtPriceMath.getAmount0Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                uint256 delta1 = SqrtPriceMath.getAmount1Delta(
                    priceLowerSqrtX96, priceUpperSqrtX96, liquidity, false
                );
                rangeReward = (delta0 - delta1.divX96(pstarX96)).min(taxInEther);

                unchecked {
                    taxInEther -= rangeReward;
                    cumulativeGrowthX128 += PoolRewardsLib.getGrowthDelta(rangeReward, liquidity);
                }
            }

            unchecked {
                rewardsOriginal[ticks.poolId].rewardGrowthOutsideX128[tickNext] += cumulativeGrowthX128;
            }

            (, int128 liquidityNet) = ticks.manager.getTickLiquidity(ticks.poolId, tickNext);
            liquidity = liquidity.add(liquidityNet);

            priceLowerSqrtX96 = priceUpperSqrtX96;
        }

        // Distribute remainder to last range and update global accumulator.
        unchecked {
            cumulativeGrowthX128 += PoolRewardsLib.getGrowthDelta(taxInEther, liquidity);
            rewardsOriginal[ticks.poolId].globalGrowthX128 += cumulativeGrowthX128;
        }
    }



    /*
     * Helper functions
     */

    function logRewards(string memory s, PoolKey memory key) internal {
        bytes32 SALT = bytes32(0);
        console2.log("Rewards %s {", s);
        for (uint256 i = 0; i < positionRanges.length; i++) {

            int24 lower = positionRanges[i][0];
            int24 upper = positionRanges[i][1];

            uint256 rewards = angstrom.getPendingPositionRewards(key, address(router), lower, upper, SALT);
            console2.log("  rewards in [%s,%s]: %s", vm.toString(lower), vm.toString(upper), rewards.pretty());
        }
        console2.log("}");
    }
}
```

**Recommended Mitigation:** Modify the condition within `AngstromL2::_oneForZeroCreditRewards` to:

```solidity
if (tickNext <= lastTick && liquidity != 0)
```

**Sorella Labs:** Fixed in commit [d53cc19](https://github.com/SorellaLabs/l2-angstrom/commit/d53cc197c43fc2d1db6d946def3fe847c2e1281c).

**Cyfrin:** Verified.

## [M-8] All swaps other than the top-of-block swap will revert
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** For swaps that are not top-of-block, `AngstromL2::afterSwap` short-circuits; however, this occurs too late in the execution with an incorrect `hookDeltaUnspecified` after a debt is erroneously created in the invocation of `_computeAndCollectProtocolSwapFee()`. This happens because `_getSwapTaxAmount()` is not top-of-block context dependent, so a non-zero `taxInEther` is passed even though the tax has already been taken from the swap with the highest priority fee:

```solidity
function afterSwap(
    address,
    PoolKey calldata key,
    SwapParams calldata params,
    BalanceDelta swapDelta,
    bytes calldata
) external override returns (bytes4, int128 hookDeltaUnspecified) {
    _onlyUniV4();

    PoolId id = key.calldataToId();
@>  uint256 taxInEther = _getSwapTaxAmount();
@>  hookDeltaUnspecified =
        _computeAndCollectProtocolSwapFee(key, id, params, swapDelta, taxInEther);

    Slot0 slot0BeforeSwap = Slot0.wrap(slot0BeforeSwapStore.get());
    Slot0 slot0AfterSwap = UNI_V4.getSlot0(id);
    rewards[id].updateAfterTickMove(
        id, UNI_V4, slot0BeforeSwap.tick(), slot0AfterSwap.tick(), key.tickSpacing
    );

    uint128 blockNumber = _getBlock();
    if (taxInEther == 0 || blockNumber == _blockOfLastTopOfBlock) {
@>      return (this.afterSwap.selector, hookDeltaUnspecified);
    }
    _blockOfLastTopOfBlock = blockNumber;

    params.zeroForOne
        ? _zeroForOneDistributeTax(id, key.tickSpacing, slot0BeforeSwap, slot0AfterSwap)
        : _oneForZeroDistributeTax(id, key.tickSpacing, slot0BeforeSwap, slot0AfterSwap);

    return (this.afterSwap.selector, hookDeltaUnspecified);
}
```

This behavior [violates](https://prover.certora.com/output/52567/2ff4b86b481c42c9b70ca9c7b5d08995/?anonymousKey=b11e81aaae9967377cf8f3273d88c841812aa11a) the following property:

```solidity
// Hook must maintain zero balance deltas for all currencies (delta neutral)
invariant hookDeltaNeutrality(env e)
    forall PoolManager.Currency currency.
        ghostCurrencyDeltas[_AngstromL2][currency] == 0
```

**Impact:** It is only possible for a single top-of-block swap to be executed and all other swaps within the same block will revert.

**Proof of Concept:** The following test should be added to `AngstromL2.t.sol`:

```solidity
function test_cyfrin_multipleSwaps() public {
    setPriorityFee(0.7 gwei);

    PoolKey memory key = initializePool(address(token), 10, 3);
    setupSimpleZeroForOnePositions(key);

    router.swap(key, true, -100e18, int24(-20).getSqrtPriceAtTick());

    setPriorityFee(0.6 gwei);

    vm.expectRevert("CurrencyNotSettled()");
    router.swap(key, true, -100e18, int24(-35).getSqrtPriceAtTick());
}
```

**Recommended Mitigation:** If the given swap is not a top-of-block swap, ensure a zero value `taxInEther` is passed to `_computeAndCollectProtocolSwapFee()`:

```diff
function afterSwap(
    address,
    PoolKey calldata key,
    SwapParams calldata params,
    BalanceDelta swapDelta,
    bytes calldata
) external override returns (bytes4, int128 hookDeltaUnspecified) {
        _onlyUniV4();

+       uint128 blockNumber = _getBlock();
        PoolId id = key.calldataToId();
-       uint256 taxInEther = _getSwapTaxAmount();
+       uint256 taxInEther = blockNumber == _blockOfLastTopOfBlock ? 0 : _getSwapTaxAmount();
        hookDeltaUnspecified =
            _computeAndCollectProtocolSwapFee(key, id, params, swapDelta, taxInEther);

@@ -237,7 +238,6 @@ contract AngstromL2 is
            id, UNI_V4, slot0BeforeSwap.tick(), slot0AfterSwap.tick(), key.tickSpacing
        );

-       uint128 blockNumber = _getBlock();
        if (taxInEther == 0 || blockNumber == _blockOfLastTopOfBlock) {
            return (this.afterSwap.selector, hookDeltaUnspecified);
        }
```

The property is [no longer violated](https://prover.certora.com/output/52567/61528817ccbc4f83a2b6ccac6e12058e/?anonymousKey=f3063485b95f5dc7d548fe11fd26a8e895e04a5b) after applying this fix.

**Sorella Labs:** Other major changes were made in this commit but was broadly fixed in commit [ffb9fb2](https://github.com/SorellaLabs/l2-angstrom/commit/ffb9fb20e5b0afbf6996ef9528ef10acd8c94f91).

**Cyfrin:** Verified. The tax amount is only calculated for top-of-block swaps; otherwise, zero is passed as recommended.

## [M-9] All swaps will revert if the dynamic protocol fee is enabled since `hook-config.sol` does not encode the `after Swap Return Delta` permission
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** If `AngstromL2::setPoolHookSwapFee` is called by the owner to configure the dynamic hook protocol fee to a non-zero value then the Uniswap V4 delta accounting will result in a revert with `CurrencyNotSettled()`.

This happens because the non-zero fee delta will be accounted to the hook:

```solidity
    if (feeCurrencyId == NATIVE_CURRENCY_ID) {
        unclaimedProtocolRevenueInEther += fee.toUint128();
@>      UNI_V4.mint(address(this), feeCurrencyId, fee + taxInEther);
    } else {
@>      UNI_V4.mint(address(this), feeCurrencyId, fee);
        UNI_V4.mint(address(this), NATIVE_CURRENCY_ID, taxInEther);
    }
```

However, `hook-config.sol` does not specify that the `afterSwapReturnDelta` permission should be encoded within the hook address, so it is possible to construct the contract without it:

```solidity
Hooks.validateHookPermissions(IHooks(address(this)), getRequiredHookPermissions());
```

With this omission, the permission is false and so the unspecified hook delta is not parsed, meaning the intended `afterSwap()` return delta is not added to the caller delta and the additional protocol fee is not paid:

```solidity
    if (self.hasPermission(AFTER_SWAP_FLAG)) {
        hookDeltaUnspecified += self.callHookWithReturnDelta(
            abi.encodeCall(IHooks.afterSwap, (msg.sender, key, params, swapDelta, hookData)),
@>          self.hasPermission(AFTER_SWAP_RETURNS_DELTA_FLAG)
        ).toInt128();
    }

    function callHookWithReturnDelta(IHooks self, bytes memory data, bool parseReturn) internal returns (int256) {
        bytes memory result = callHook(self, data);

        // If this hook wasn't meant to return something, default to 0 delta
@>      if (!parseReturn) return 0;

        // A length of 64 bytes is required to return a bytes4, and a 32 byte delta
        if (result.length != 64) InvalidHookResponse.selector.revertWith();
        return result.parseReturnDelta();
    }
```

**Impact:** All swaps will revert if the dynamic protocol fee is enabled.

**Proof of Concept:** The following test should be added to `AngstromL2.t.sol`

```solidity
function test_cyfrin_SwapFeeNotSettledBecauseHookConfigMissing() public  {
    PoolKey memory key = initializePool(address(token), 10, 3);

    angstrom.setPoolHookSwapFee(key, 0.005e6); // 0.5%

    addLiquidity(key, 0, 10, 1e22);

    vm.expectRevert(bytes4(keccak256("CurrencyNotSettled()")));
    router.swap(key, true, -10e18, int24(0).getSqrtPriceAtTick());
}
```

**Recommended Mitigation:** The following permission should be added to `hooks-config.sol`:

```solidity
permissions.afterSwapReturnDelta = true;
```

**Sorella Labs:** Fixed in commit [d79a87b](https://github.com/SorellaLabs/l2-angstrom/commit/d79a87bc0153e9d75079f0a5de98f444fb9a8cd6).

**Cyfrin:** Verified. The permission has been added.

## [M-10] Dynamic LP fees will remain zero by default unless explicitly updated
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** As given by the logic in `LPFeeLibrary::getInitialLPFee`, dynamic fee pools initialize with an LP fee of 0%:

```solidity
function getInitialLPFee(uint24 self) internal pure returns (uint24) {
    // the initial fee for a dynamic fee pool is 0
    if (self.isDynamicFee()) return 0;
    self.validate();
    return self;
}
```

While `AngstromL2::setPoolLPFee` allows the contract owner to update the dynamic LP fee, there will be a period following initialization when it is not set. As such, it may be desirable to implement the `afterInitialize()` hook if a non-zero LP fee is required immediately upon initialization.

**Impact:** The LP fee will remain zero for all pools unless explicitly updated by the hook owner.

**Proof of Concept:** The following test should be added to `AngstromL2.t.sol`:

```solidity
function test_zeroInitialLPFee() public {
    PoolKey memory key = initializePool(address(token), 10, 3);
    assertEq(manager.getSlot0(key.toId()).lpFee(), 0);
}
```

**Recommended Mitigation:** Implement the `afterInitialize()` hook to set the desired LP fee immediately upon initialization.

**Sorella Labs:** Fixed in commit [ffb9fb2](https://github.com/SorellaLabs/l2-angstrom/commit/ffb9fb20e5b0afbf6996ef9528ef10acd8c94f91#diff-eff6e215636c02633f38518bd4bf97879ede5fdd1586aa6d73fc2ab3fa816396).

**Cyfrin:** Verified. Dynamic fee pools are no longer supported.

## [M-11] Calculation of available liquidity in `Collateral Liquidity Provider::available Liquidity` assumes 1:1 ratio between collateral asset and liquidity tokens
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The `CollateralLiquidityProvider::availableLiquidity` function incorrectly returns the balance of the collateral asset held by the collateral provider, assuming a 1:1 ratio between the collateral asset and the liquidity tokens that will actually be provided to redeemers. This assumption is flawed because the actual liquidity supplied to redeemers goes through the `externalCollateralRedemption.redeem()` function, which may apply fees, exchange rates, or other conversion mechanisms that break the 1:1 assumption.

```solidity
function availableLiquidity() external view returns (uint256) {
    return IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider);
}

function _availableLiquidity() private view returns (uint256) {
    return IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider);
}

function supplyTo(
    address redeemer,
    uint256 amount,
    uint256 minOutputAmount
) public whenNotPaused onlySecuritizeRedemption {
    if (amount > _availableLiquidity()) {
        revert InsufficientLiquidity(amount, _availableLiquidity());
    }

    // ... collateral transfer and redemption logic ...

    // The actual liquidity provided is calculated here, not the raw collateral amount
    uint256 assetsAfterExternalCollateralRedemptionFee = externalCollateralRedemption.calculateLiquidityTokenAmount(
        amount
    );

    liquidityToken.transfer(redeemer, assetsAfterExternalCollateralRedemptionFee);
}
```

When `CollateralLiquidityProvider::supplyTo` is called, the flow involves: transferring collateral assets from the collateral provider, calling `externalCollateralRedemption.redeem()` to convert collateral to liquidity tokens, calculating the actual liquidity amount using `externalCollateralRedemption.calculateLiquidityTokenAmount()`, and finally transferring the calculated liquidity tokens to the redeemer.
The `availableLiquidity()` function should query the external redemption contract to determine the actual liquidity that can be provided, rather than using the raw collateral asset balance. (e.g. `externalCollateralRedemption.calculateLiquidityTokenAmount(IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider));`

Additionally, the external `availableLiquidity()` function duplicates the logic of the internal `_availableLiquidity()` function instead of calling it, which goes against the intended design pattern and creates unnecessary code duplication.

**Impact:** Users and integrating systems may receive incorrect information about available liquidity, potentially leading to failed transactions when the actual convertible liquidity is less than the reported collateral asset balance.

**Recommended Mitigation:** Update the `availableLiquidity()` function to calculate the actual liquidity that can be provided by querying the external redemption contract, and fix the function to call the internal `_availableLiquidity()` function as intended:

```diff
function availableLiquidity() external view returns (uint256) {
-    return IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider);
+    return _availableLiquidity();
}

function _availableLiquidity() private view returns (uint256) {
-    return IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider);
+    uint256 collateralBalance = IERC20(externalCollateralRedemption.asset()).balanceOf(collateralProvider);
+    return externalCollateralRedemption.calculateLiquidityTokenAmount(collateralBalance);
}
```

**Securitize:** Fixed in commit [1da35c](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/bf970d6cc4152c1b22e386b6acc6095aece8f12a) and [4a426e](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/4a426e689586a37cdcb463dba2f670fd58190ef9).

**Cyfrin:** Verified.

\clearpage

## [M-12] Confusing variable naming in fee manager contracts
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The fee manager contracts use confusing variable names for fee percentage values.
In `MbpsFeeManager`, the variable `fee` represents a fee percentage in MBPS (milli basis points), not an actual fee amount. The comment even clarifies "Fee expressed in mbps (1000 mbps = 1%)", and the calculation formula `(amount * fee + FEE_DENOMINATOR - 1) / FEE_DENOMINATOR` shows that `fee` is used as a percentage rate. However, the variable name `fee` typically implies an actual fee amount rather than a percentage rate. For example, the fee manager contract exposes a function `getFee(uint256 amount)`.

This naming convention creates confusion for those who expect `fee` to represent an actual fee amount rather than a percentage rate used in calculations.

**Impact:** The confusing variable names could lead to integration errors, misunderstanding of fee calculations, and potential bugs in contracts that interact with the fee managers.

**Recommended Mitigation:** Rename the fee variables to clearly indicate they represent percentages:

```diff
- uint256 public fee;
+ uint256 public feeMBPS;
```
Consider using `feePercentageMBPS` for even better clarity.

**Securitize:** Fixed in commit [6a5d45](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/6a5d45daf788fe573cb435f24a033472b336b21a).

**Cyfrin:** Verified.

## [M-13] Incorrect usage of min Output Amount in execute Two Step Redemption can cause unnecessary reverts
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** In the `RedemptionManager::executeTwoStepRedemption` function, the following call is made:

```solidity
params.liquidityProvider.supplyTo(contractAddress, params.liquidityTokenAmount, params.minOutputAmount);
```

Here, `params.minOutputAmount` is used as the minimum expected return from the liquidity provider. However, this value does not account for any fee deductions that are applied later in the function.

Immediately after the `supplyTo` call, the contract performs a slippage protection check:

```solidity
uint256 offRampBalance = params.liquidityProvider.liquidityToken().balanceOf(contractAddress);
uint256 fee = _getFee(params.feeManager, offRampBalance);

if (offRampBalance - fee < params.minOutputAmount) {
    revert Errors.SlippageControlError();
}
```

If the liquidity provider returns exactly `minOutputAmount`, then the deduction of the fee from that amount will cause `offRampBalance - fee` to fall below `minOutputAmount`, resulting in a slippage error—even though the liquidity provider met the minimum requirement.

The issue is not with the slippage check itself, which is correctly accounting for the fee. The problem is that the `minOutputAmount` passed to `supplyTo` should also include the fee, to ensure consistency with the later slippage check.

**Impact:** Unexpected transaction reverts may occur due to slippage errors, even when the liquidity provider meets the `minOutputAmount` requirement.

**Recommended Mitigation:** Update the call to `supplyTo` to include the expected fee in the `minOutputAmount` parameter. For example:

```solidity
uint256 expectedFee = _getFee(params.feeManager, params.minOutputAmount);
params.liquidityProvider.supplyTo(contractAddress, params.liquidityTokenAmount, params.minOutputAmount + expectedFee);
```

This ensures that the post-fee amount meets the expected minimum and aligns with the logic in the slippage protection check.

**Securitize:** Fixed in commit [54243f](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/54243f7e6716826c30c9561c6390fa0e05440252).

**Cyfrin:** Verified.

## [M-14] Misleading comments and documentation inconsistencies in on-ramp contracts
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** Multiple contracts in the on-ramp system contain misleading comments, incorrect documentation, and interface inconsistencies that misrepresent the actual functionality.

- The ```ISecuritizeOnRamp``` interface documents a ```Buy``` event that is never emitted anywhere in the codebase, and references a non-existent ```swapFor``` function in the ```toggleInvestorSubscription``` documentation.

- The ```ISecuritizeOnRamp``` interface incorrectly declares ```nonceByInvestor``` and ```calculateDsTokenAmount``` as state-changing functions when they are actually view functions in the implementation.

- ```MintingAssetProvider``` uses ```@title IAssetProvider``` instead of its actual contract name, creating confusion about which contract is being documented.

- ```IAssetProvider::securitizeOnRamp``` function documentation contains a typo referring to "on ramo contract" instead of "on ramp contract".

- `MpbsFeeManager::setRedemptionFee` function documentation mentions the fee percentage is in basis points while it is supposed to be MBPS.

**Impact:** These misleading comments can cause developers to incorrectly integrate with the contracts by expecting functionality that doesn't exist.

**Securitize:** Fixed in commit [2b6c3a](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/2b6c3a8efdc23b4e2fc5fed273987830fbeaee18).

**Cyfrin:** Verified.

## [M-15] `Fee Module::_lookup Fees` returns zero fees at price = 1e18 due to strict less-than comparison
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `FeeModule::_lookupFees` uses a strict less-than comparison (`price < tiers[i].maxPrice`) to find the applicable fee tier. Since `maxPrice` is validated as `<= 1e18` (i.e., the maximum tier boundary is 1e18), a trade at exactly `price = 1e18` will not match any tier and fall through to the default `return (0, 0)`.

A price of 1e18 represents a 100% probability outcome — while uncommon, it is explicitly allowed by `_matchOrders` which validates `maker.price <= ONE && taker.price <= ONE`.

```solidity
// FeeModule.sol:151-158
function _lookupFees(uint256 marketId, uint256 price) internal view returns (uint16 makerBps, uint16 takerBps) {
    FeeTier[] storage tiers = _marketFees[marketId];
    for (uint256 i = 0; i < tiers.length; i++) {
        if (price < tiers[i].maxPrice) {  // @audit strict less-than: price=1e18 never matches
            return (uint16(tiers[i].makerFeeBps), uint16(tiers[i].takerFeeBps));
        }
    }
    return (0, 0); // price=1e18 falls through to zero fees
}
```

**Impact:** Trades at `price = 1e18` pay zero fees when the fee admin intended them to be covered by the highest tier. This represents fee revenue leakage.

**Recommended Mitigation:** Change to less-than-or-equal:

```solidity
if (price <= tiers[i].maxPrice) {
```

**Myriad:** Fixed in commit [`8074df6`](https://github.com/Polkamarkets/polkamarkets-js/commit/8074df65a4b3b18b5393eba526621d0c65c96823)

**Cyfrin:** Verified.

## [M-16] `Fee Module::set Market Fees` permits 100% fee rates
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `FeeModule::setMarketFees` validates individual fee rates against `BPS` (10000 basis points = 100%):

```solidity
// FeeModule.sol:102
require(tiers[i].makerFeeBps <= BPS && tiers[i].takerFeeBps <= BPS, "fee too high");
```

This allows the `FEE_ADMIN` to configure a tier with `makerFeeBps = 10000` and `takerFeeBps = 10000`. In a direct match, the seller would receive 0 proceeds and the buyer would pay double the notional value (all sent to fees). Even without malicious intent, misconfigured fee schedules (e.g., entering basis points when percentages are expected) could result in catastrophic fees.

**Recommended Mitigation:** Introduce a protocol-level maximum fee constant and enforce it:

```solidity
uint256 public constant MAX_FEE_BPS = 500; // 5%

require(tiers[i].makerFeeBps <= MAX_FEE_BPS && tiers[i].takerFeeBps <= MAX_FEE_BPS, "fee too high");
```

Make `MAX_FEE_BPS` configurable only by `DEFAULT_ADMIN_ROLE` with a separate governance process.

**Myriad:** Fixed in commit [`e7a85bc`](https://github.com/Polkamarkets/polkamarkets-js/commit/e7a85bccc3fac7d14a2b95cb6eb46b320274c0f7)

**Cyfrin:** Verified. Max fee of 10% (`1000`) enforced.

## [M-17] finalize With Fee lacks race conditioning protection
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** `finalizeWithFee` does not provide any user-defined bounds on the resulting fee or claimed amount, making the outcome sensitive to state changes between transaction submission and execution. The effective fee can change
if new requests are merged (especially when hitting the 70th slot), if `vaultEarlyExitFeePerDay` is updated, or if the execution crosses a day boundary which increases `daysLeft`.

Additionally, reordering of requests due to `cancel/finalize` can change which request index is finalized, potentially causing unexpected reverts. As a result, users cannot reliably predict or cap the cost of early finalization at the time they sign the transaction.

**Recommended Mitigation:** Allow users to specify explicit bounds (e.g. maxFee) when calling `finalizeWithFee` and revert if those bounds are violated. This provides slippage-style protection against fee changes, timing effects, and request mutations.

**Strata:** Fixed in commit [092a08b](https://github.com/Strata-Money/contracts-tranches/commit/092a08b9fd0b79f3f7fa2461cb277113db121c8d).

**Cyfrin:** Verified. Now, users can input slippage protection when calling `finalizeWithFee`. The slippage protection is optional; users can choose not to specify it and accept the calculated values at execution time.

\clearpage

## [M-18] Invalid validate Redemption Params check
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** The `withdraw` and `redeem` functions were designed to provide UX-level slippage protection by requiring user-supplied exit parameters to match the protocol-calculated exit mode. If conditions change, the transaction is expected to revert, as stated by the protocol.

However, `validateRedemptionParams` currently returns instead of reverting when user parameters do not match system parameters. This completely pass any slippage protection and breaking the UX guarantee described by the team.

```solidity
function validateRedemptionParams(TRedemptionParams memory params, IStrataCDO.TExitMode exitMode, uint256 exitFee, uint32 cooldownSec) internal pure {
        if (params.exitMode == IStrataCDO.TExitMode.Dynamic) {
            return;
        }
        if (params.exitMode != exitMode || params.exitFee != exitFee || params.cooldownSeconds != cooldownSec) {
            return;
        }
        revert RedemptionParamsMismatch(params, TRedemptionParams({
            exitMode: exitMode,
            exitFee: exitFee,
            cooldownSeconds: cooldownSec
        }));
    }
```

**Recommended Mitigation:** The `validateRedemtionParams` function should revert instead of return if at least one of the parameters does not match. Also, revert at the end of the function should be replaced with return.

**Strata:** Fixed in commit **652a5c1**

## [M-20] Consider limiting max royalty to prevent large amount or all of the sale fee being taken as royalty
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** Currently `updateRoyalties` and `setTokenRoyalty` allow the contract owner to set a royalty up to `10_000` which would take the entire sale fee as a royalty. Consider limiting these functions to set the max royalty to something more reasonable like 1000 (10%).

**CryptoArt:**
Fixed in commit [1d1125e](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/1d1125e5a021f2926dc2a2e39e05c065e3bd207c).

**Cyfrin:** Verified.

## [M-21] Dividend Calculation Uses Stale Token Balance in Subsequent `update()` Calls After `fees_deposit` with DRVS
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `fees_deposit()` function calls `client_community_state.update()` before `client_state.sub_crncy_tokens()`, causing `self.header.drvs_tokens` to be updated with a stale value that doesn't reflect the actual token balance after the reduction. When `update()` is called again in subsequent instructions (e.g., `deposit`, `spot_quotes_replace`), it calculates dividends using this stale stored value instead of the actual current balance.

**Prerequisites**: This issue only occurs when `fees_deposit` is called with `token_id = 0` (DRVS token)

The issue occurs because:

1. **Order of operations**: In `fees_deposit()`, `update()` is called before `sub_crncy_tokens()`
2. **Stale balance storage**: `update()` reads the current balance (before reduction) and stores it in `self.header.drvs_tokens`, but `sub_crncy_tokens()` reduces the actual balance afterward
3. **Stale dividend calculation**: When `update()` is called again in a subsequent instruction, it calculates dividends using `self.header.drvs_tokens` (the stale stored value from before the reduction) instead of the actual current balance

```rust
// src/program/processor/fees_deposit.rs
client_community_state.update(&mut client_state, &mut community_state)?;
client_state.resolve(AssetType::Token, data.token_id, TokenType::Crncy, false)?;
// ... fee calculation logic ...
client_state.sub_crncy_tokens(data.amount)?;
```

```rust
// src/state/client_community.rs
        if available_tokens != self.header.drvs_tokens {
            for (i, d) in self.data.iter_mut().enumerate() {
                let amount = (((community_state.base_crncy[i].rate - d.dividends_rate)
                    * self.header.drvs_tokens as f64) as i64)
                    .max(0);
                d.dividends_value += amount;
            }
```

**Example scenario demonstrating the issue:**

Initial state: User has 100 DRVS tokens, `self.header.drvs_tokens = 100`

1. **First `fees_deposit(token_id=0, amount=10)` call:**
   - `update()` is called:
     - `resolve(AssetType::Token, 0, ...)` resolves DRVS token (token_id = 0)
     - `available_tokens = 100` (current balance before reduction)
     - `self.header.drvs_tokens = 100` (stored value)
     - Since they're equal, no dividend calculation occurs
     - `self.header.drvs_tokens` is updated to `100`
   - `sub_crncy_tokens(10)` is called, actual balance becomes `90`
   - **Result**: `self.header.drvs_tokens = 100` (stale), but `actual balance = 90`

2. **Next instruction that calls `update()` (e.g., `deposit`, `spot_quotes_replace`):**
   - `update()` is called again:
     - `available_tokens = 90` (actual current balance, or could be others)
     - `self.header.drvs_tokens = 100` (stale stored value from step 1)
     - Since they differ, dividend calculation occurs using `self.header.drvs_tokens = 100`
     - **Problem**: Dividends are calculated based on `100` tokens, but the user only has `90` tokens during this period
   - **Result**: User receives dividends calculated on `100` tokens instead of `90`, receiving more than they should

The root cause is that in `fees_deposit()`, `update()` stores the balance before `sub_crncy_tokens()` reduces it, creating a discrepancy between the stored value and the actual balance. When `update()` is called again later, it uses this stale stored value for dividend calculations.

**Impact:** **Overpayment of Dividends**: When `update()` is called in subsequent instructions after a `fees_deposit(token_id=0)`, users receive dividends calculated on a higher token balance than they actually hold, leading to financial loss for the protocol.

**Recommended Mitigation:** The order should be re-arranged to ensure that the `drvs_token` is always update to date

**Deriverse:** Fixed in commit [4df80d](https://github.com/deriverse/protocol-v1/commit/4df80d97a4b72e144ccabf6956d10d463d4ca91e).

**Cyfrin:** Verified.

## [M-22] Incomplete Balance Check Missing Transaction Fee and Reserve Balance
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `create_client_account()` function checks if the wallet has sufficient balance to create two accounts, but it does not account for transaction fees or reserve balance for the wallet itself. This can lead to transaction failures or leave the wallet account in an unusable state after the operation.

When creating client accounts, the code only verifies that the wallet balance covers the rent-exempt minimums for the two new accounts:
```rust
    if balance < client_primary_lamports + client_community_lamports {
        bail!(InsufficientFunds);
    }
```

After the two `create_account` instructions execute, the wallet transfers:
- `client_primary_lamports` to the primary account
- `client_community_lamports` to the community account

If the wallet's initial balance was exactly `client_primary_lamports + client_community_lamports`, the wallet would be left with:
- 0 lamports (or very close to 0)
- Unable to pay transaction fees
- Potentially unable to perform subsequent operations


**Impact:** If a wallet has exactly `client_primary_lamports + client_community_lamports` balance, the transaction may fail during execution.

**Recommended Mitigation:** Reserve a small, predefined amount (e.g., a few thousand lamports) on top of the required rent-exempt minimums.
```rust
const WALLET_RESERVE_LAMPORTS: u64 = 5_000_000; // example reserve
if balance < client_primary_lamports + client_community_lamports + WALLET_RESERVE_LAMPORTS {
    bail!(InsufficientFunds);
}
```

**Deriverse:** Fixed in commit [548040f](https://github.com/deriverse/protocol-v1/commit/548040fcce8e00f6b42546a19e79a4bd7d0fb5d0).

**Cyfrin:** Verified.

## [M-23] Inconsistent Price Calculation for Fee in Spot LP Trading
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The fee calculation in the `spot_lp` instruction uses `last_px` directly without applying the same price constraints (`best_bid, best_ask`) and unit conversion (`RDF`) that are used when adding liquidity. This inconsistency can lead to incorrect fee calculations when `last_px` falls outside the valid market price range.

In `src/program/processor/spot_lp.rs`, there are two different price calculation approaches:

1. When adding liquidity:

```rust
let px_f64 = instr_state
    .header
    .last_px
    .max(instr_state.header.best_bid)
    .min(instr_state.header.best_ask) as f64
    * RDF;
```

This calculation constrains the price to the range `[best_bid, best_ask]`

2. When calculating fees

```rust
fees = 1
    + ((instr_state.header.last_px as f64
        / get_dec_factor(instr_state.header.asset_token_decs_count) as f64)
        as i64)
        .max(1);
```

Uses `last_px` directly without price range constraints.

**Impact:** If `last_px` is outside `[best_bid, best_ask]` (e.g., due to market volatility or order book changes), fees may be calculated using an invalid price, leading to overcharging or undercharging users.

**Recommended Mitigation:** Update the fee calculation to use the same price logic as liquidity addition:


**Deriverse:** Fixed in commit [40e36f70](https://github.com/deriverse/protocol-v1/commit/40e36f70a57a89a76ec19f9d825852bced7002dd).

**Cyfrin:** Verified.

## [M-24] Incorrect Boundary Condition in `check_pool_fees` Function Excludes Valid Minimum Token Transactions
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `check_pool_fees` function uses a strict greater-than (`>`) comparison when checking if `tokens_qty` meets the `min_tokens` requirement. This incorrectly excludes the valid boundary case where `tokens_qty` equals `min_tokens`, preventing legitimate pool fee conversions when the calculated quantity exactly matches the minimum allowed value.

In `src/program/spot/engine.rs`, the `check_pool_fees` function contains the following condition:

```rust
pub fn check_pool_fees(
    &mut self,
    client_state: &mut ClientPrimaryState,
    rest_of_order: &mut i64,
    traded_sum: &mut i64,
    price: i64,
    min_tokens: i64,
) -> DeriverseResult {
    let mints_qty = self.state.header.pool_fees >> 1;
    let tokens_qty = (self.state.header.asset_tokens as f64 * mints_qty as f64
        / self.state.header.crncy_tokens as f64) as i64;
    if tokens_qty > min_tokens && *rest_of_order > min_tokens + tokens_qty {
        // ... execute pool fee conversion logic
    }
    Ok(())
}
```

This violates with other parts of the code, like:

```rust
    if !(data.order_type == OrderType::Market as u8 || data.ioc != 0) && data.amount < min_tokens {
        bail!(InvalidQuantity {
            value: data.amount,
            min_value: min_tokens,
            max_value: SPOT_MAX_AMOUNT
        })
    }
```

**Impact:** Valid pool fee conversions are incorrectly rejected when the calculated tokens_qty exactly equals min_tokens, reducing the efficiency of pool fee utilization

**Recommended Mitigation:** Change the comparison operator from `>` to `>=` to include the valid boundary case.

**Deriverse:** Fixed in commit [3a24de8](https://github.com/deriverse/protocol-v1/commit/3a24de8933a2f1f9b039224d89857f857c2fdfc6).

**Cyfrin:** Verified.

## [M-25] Incorrect Price Validation When Creating `New Instrument Data` Struct during `New Instrument Instruction` instruction
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The current validation logic when creating `NewInstrumentData` using `new` method during `NewInstrumentInstruction` instruction uses an exclusive upper bound when checking the price field. As a result, a price equal to MAX_PRICE is incorrectly rejected even though it should be considered valid.

```rust
    fn new(instruction_data: &[u8], tokens_count: u32) -> Result<&Self, DeriverseError> {
        let data = bytemuck::try_from_bytes::<Self>(instruction_data)
            .map_err(|_| drv_err!(InvalidClientDataFormat))?;

        if data.crncy_token_id >= tokens_count {
            bail!(InvalidTokenId {
                id: data.crncy_token_id,
            })
        }

        if !(MIN_PRICE..MAX_PRICE).contains(&data.price) {                  //<- HERE
            bail!(InvalidPrice {
                price: data.price,
                min_price: MIN_PRICE,
                max_price: MAX_PRICE,
            })
        }

        return Ok(data);
    }
```

In Rust, the syntax a..b defines a range that excludes the upper bound(b), whereas a..=b defines an inclusive range that allows b as a valid value.


**Impact:** This bug prevents legitimate instruments with a price equal to MAX_PRICE from being created.

**Recommended Mitigation:** To fix this issue, the validation should use an inclusive range (a..=b) so that prices equal to MAX_PRICE pass the check.
```rust
    fn new(instruction_data: &[u8], tokens_count: u32) -> Result<&Self, DeriverseError> {
        let data = bytemuck::try_from_bytes::<Self>(instruction_data)
            .map_err(|_| drv_err!(InvalidClientDataFormat))?;

        if data.crncy_token_id >= tokens_count {
            bail!(InvalidTokenId {
                id: data.crncy_token_id,
            })
        }

        if !(MIN_PRICE..=MAX_PRICE).contains(&data.price) {                  //<- HERE
            bail!(InvalidPrice {
                price: data.price,
                min_price: MIN_PRICE,
                max_price: MAX_PRICE,
            })
        }

        return Ok(data);
    }
```


**Deriverse:** Fixed in commit [aa6136](https://github.com/deriverse/protocol-v1/commit/aa613649a9dcd3394890a03e964a6d2b6b6570ad).

**Cyfrin:** Verified.

## [M-26] Insurance fund decrease when `margin_call_penalty_rate` is less than `rebates_rate`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** When `margin_call_penalty_rate` is less than `rebates_rate`(`fee_rate * REBATES_RATIO`), the insurance fund decreases instead of increasing during margin calls.

During a margin call, the insurance fund is updated as: `perp_insurance_fund += (new_fees - rebates)`, where:
- `new_fees = traded_crncy * margin_call_penalty_rate`
- `rebates = traded_crncy * fee_rate * REBATES_RATIO`

If `margin_call_penalty_rate < fee_rate * REBATES_RATIO`, then `(new_fees - rebates)` becomes negative, causing the insurance fund to decrease when it should increase.

**Impact:** The insurance fund can be drained during margin calls instead of being replenished.

**Recommended Mitigation:** Ensure that `margin_call_penalty_rate >= fee_rate * REBATES_RATIO` to guarantee that margin call penalties always contribute positively to the insurance fund.

**Deriverse:** Fixed in commit [1ef948](https://github.com/deriverse/protocol-v1/commit/1ef948af18b47f3e502d0054d760212d4b6263f1).

**Cyfrin:** Verified.



\clearpage

## [M-27] Lack of slippage in `spot_lp` liquidity operations due to relying on the changing `header.crncy_tokens` and `header.asset_tokens`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `spot_lp` function lacks slippage protection when adding or removing liquidity.

In most cases, the function calculates the required asset and currency tokens based on the current pool state at execution time, **without allowing users to specify minimum output amounts or maximum acceptable slippage**. This exposes users to unfavorable execution prices due to pool state changes between transaction submission and execution.

In `src/program/processor/spot_lp.rs`, when adding liquidity (lines 189-194), the function directly calculates the required tokens based on the current pool state:

```rust
trade_crncy_tokens = ((instr_state.header.crncy_tokens + instr_state.header.pool_fees)
    as f64
    * amount as f64
    / instr_state.header.ps as f64) as i64;
trade_asset_tokens = (instr_state.header.asset_tokens as f64 * amount as f64
    / instr_state.header.ps as f64) as i64;
```

The pool's asset_tokens and crncy_tokens are modified during normal trading operations (as seen in `engine.rs` via `change_tokens` and `change_mints`).

```rust
                self.change_tokens(traded_qty, side)?;
                self.change_mints(traded_mints, side)?;
                self.log_amm(traded_qty, traded_mints, side);
```

However, the spot_lp function:
- Does not allow users to specify minimum acceptable output amounts (similar to Uniswap V2's `amountAMin `and `amountBMin`)
- Does not validate that the execution price is within an acceptable range

**Impact:** Users can suffer unexpected losses when adding/removing liquidity due to pool state changes

**Recommended Mitigation:** Add slippage protection parameters to SpotLpData structure and Implement validation checks after calculating `trade_asset_tokens` and `trade_crncy_tokens`

**Deriverse:** Fixed in commit [337383](https://github.com/deriverse/protocol-v1/commit/3373834b7988ba52810515f514664e0c80ca2c8c).

**Cyfrin:** Verified.

## [M-28] Missing `change_funding_rate` Call After Price Update in `perp_mass_cancel` and `perp_order_cancel`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `perp_order_cancel` and `perp_mass_cancel functions`, the code updates the underlying price (`perp_underlying_px`) via `set_underlying_px` but fails to call `change_funding_rate` before invoking `check_rebalancing`(and potentially `mass_cancel`), which internally calls `check_funding_rate`. This results in funding rate calculations being performed with stale global funding rate values that haven't been updated to reflect the new underlying price(even though the price is correctly updated), potentially leading to incorrect funding fee calculations for users.

The funding rate mechanism works as follows:
- `change_funding_rate` updates the global funding rate state
```rust
    pub fn change_funding_rate(&mut self) {
        let time_delta = self.time - self.state.header.perp_funding_rate_time;
        if time_delta > 0 && self.state.header.perp_price_delta != 0.0 {
            self.state.header.perp_funding_rate +=
                ((time_delta as f64) / DAY as f64) * self.state.header.perp_price_delta;
        }
        self.state.header.perp_price_delta =
            (self.market_px() - self.state.header.perp_underlying_px) as f64 * self.rdf;
        self.state.header.perp_funding_rate_time = self.time;
    }
    /*
```
- `check_funding_rate` applies the global funding rate to individual clients:
```rust
    pub fn check_funding_rate(&mut self, temp_client_id: ClientId) -> Result<bool, DeriverseError> {
        let info = unsafe { &mut *(self.client_infos.offset(*temp_client_id as isize)) };
        let info5 = unsafe { &mut *(self.client_infos5.offset(*temp_client_id as isize)) };
        let perps = info.total_perps();
        let mut change = false;
        if perps != 0 {
            if self.state.header.perp_funding_rate != info5.last_funding_rate {
                let funding_funds = -(perps as f64
                    * (self.state.header.perp_funding_rate - info5.last_funding_rate))
                    .round() as i64;
```

Thus the `perp_funding_rate` should be refreshed each time before `check_funding_rate` is called.

The issue is that in the `perp_order_cancel` and `perp_mass_cancel`:

```rust
// perp_order_cancel
engine.state.set_underlying_px(accounts_iter)?;
// ... order cancellation logic ...
engine.check_rebalancing()?;  // Calls check_funding_rate() internally

// perp_mass_cancel
engine.state.set_underlying_px(accounts_iter)?;
engine.mass_cancel(client_state.temp_client_id)?;  // Calls check_funding_rate() at line 1888
// ... margin call checks ...
engine.check_rebalancing()?;  // Also calls check_funding_rate() at line 2363
```

When `perp_underlying_px` is updated but `change_funding_rate` is not called, the global `perp_funding_rate` may not reflect the latest price changes.

**Impact:** Users may be charged incorrect funding fees when canceling orders, as the funding rate calculations use stale global funding rate values that don't reflect the updated underlying price since the `change_funding_rate` is not called.

**Recommended Mitigation:** Add `change_funding_rate` calls immediately after `set_underlying_px` in both vulnerable functions.

**Deriverse:** Fixed in commit [74f9650](https://github.com/deriverse/protocol-v1/commit/74f9650ef966b422d95a384bb1e39f4f7bd9cf22).

**Cyfrin:** Verified.

## [M-29] Missing Array Synchronization in `dividends_claim` Prevents Users from Claiming Dividends for Newly Added Base Currencies
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `dividends_claim` instruction does not synchronize `client_community_state.data` with` community_state.base_crncy` before processing dividends. If a new base currency is added to the community and a user hasn't performed any operations (like `deposit` or `trading`) that trigger synchronization, the user's `client_community_state.data` array will be shorter than community_state.base_crncy. This causes the zip iterator to stop early, preventing users from claiming dividends for newly added base currencies until they perform another operation that triggers synchronization.

In `src/state/client_community.rs`, the update function synchronizes arrays before processing:

```rust
pub fn update(
    &mut self,
    client_primary_state: &mut ClientPrimaryState<'a, 'info>,
    community_state: &mut CommunityState,
    payer: Option<&'a AccountInfo<'info>>,
) -> DeriverseResult {
    self.update_records(community_state, payer)?;  // Synchronizes arrays
    // ... rest of the logic
}
```

The update_records function ensures `client_community_state.data` matches `community_state.base_crncy`:

```rust
fn update_records(
    &mut self,
    community_state: &CommunityState,
    payer: Option<&'a AccountInfo<'info>>,
) -> DeriverseResult {
    // ... reallocates if needed ...
    self.header.count = community_state.header.count;
    // ... creates new data array ...
    for (d, b) in self.data.iter_mut().zip(community_state.base_crncy.iter()) {
        d.crncy_token_id = b.crncy_token_id;
        d.fees_ratio = 1.0;
    }
}
```

However, in `src/program/processor/dividends_claim.rs`, the instruction directly iterates without synchronization:

```rust
for (d, b) in client_community_state
    .data
    .iter_mut()
    .zip(community_state.base_crncy.iter_mut())
{
    // Process dividends...
}
```

- Other instructions like `deposit` call `client_community_state.update()`, which triggers `update_records`
- `dividends_claim` does not call `update_records` or update before processing
- If `client_community_state.data.len() < community_state.base_crncy.len()`, the zip iterator stops when the shorter array ends
- Users cannot claim dividends for newly added base currencies until they perform another operation

**Impact:** Users who haven't performed operations after new base currencies are added cannot claim dividends for those currencies. Users must perform an additional operation (e.g., deposit) to trigger synchronization before claiming dividends

**Recommended Mitigation:** Add synchronization before processing dividends in dividends_claim

**Deriverse:** Fixed in commit [5f5460](https://github.com/deriverse/protocol-v1/commit/5f5460d75277aa1c946501680577adc33382b7b5).

**Cyfrin:** Verified.

## [M-30] Missing Quorum Requirement in Governance Voting
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The governance voting system in `finalize_voting()` lacks a quorum requirement, allowing protocol parameters to be changed based on relative vote counts without validating that a minimum percentage of total token supply has participated. This enables a small minority of token holders to control protocol governance decisions, undermining the decentralized nature of the system.


```rust
let decr = community_account_header.voting_decr;
let incr = community_account_header.voting_incr;
let unchange = community_account_header.voting_unchange;
let tag = community_account_header.voting_counter % 6;

if decr > unchange && decr > incr {
    // Apply DECREMENT - no quorum check
    match tag {
        0 => { community_account_header.spot_fee_rate -= 1; }
        // ... other parameters
    }
} else if incr > unchange && incr > decr {
    // Apply INCREMENT - no quorum check
    match tag {
        0 => { community_account_header.spot_fee_rate += 1; }
        // ... other parameters
    }
}
```

While `voting_supply` is tracked and set to `drvs_tokens` (total supply), it is never used to validate that sufficient tokens participated in the vote:

```rust
community_account_header.voting_supply = community_account_header.drvs_tokens;
```


**The Problem:**
1. No minimum participation threshold (quorum) is checked before applying voting results
2. A single voter with a small amount of tokens can determine protocol changes if no one else votes
3. The total voting power (`decr + incr + unchange`) is never compared against `voting_supply` or any minimum threshold
4. This violates common governance best practices where significant decisions require meaningful community participation

**Impact:**
- **Governance Attack Vector:** Malicious actors can wait for low-activity periods to push through unfavorable parameter changes
- **Undermined Decentralization:** The voting system fails to ensure decisions represent a meaningful portion of the community

**Recommended Mitigation:** Add a quorum requirement that validates minimum participation before applying voting results. The quorum should be a percentage of the total voting supply.
```rust
        let total_votes = decr + incr + unchange;
        let voting_supply = community_account_header.voting_supply;

        // Add quorum check (e.g., require at least 5% participation)
        const MIN_QUORUM_PERCENTAGE: i64 = 5; // 5% of voting supply
        let min_quorum = (voting_supply * MIN_QUORUM_PERCENTAGE) / 100;
```

**deriverse:**
Fixed in commit [b4e1045](https://github.com/deriverse/protocol-v1/commit/b4e10453eb5fe7a0866a264fac4187167640f998).

**Cyfrin:** Verified.

## [M-31] Missing Slippage Protection in Market Seat Buy/Sell Operations
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `buy_market_seat()` and `sell_market_seat()` functions calculate seat prices dynamically based on the current `perp_clients_count` at execution time, but provide no slippage protection. Users cannot specify maximum/minimum acceptable prices, exposing them to unexpected price changes.

In `buy_market_seat()`, the seat price is calculated as:

```rust
let seat_price = PerpEngine::get_place_buy_price(
    instrument.perp_clients_count,
    instrument.crncy_token_decs_count,
)?;

instrument.seats_reserve += seat_price;
let price = data.amount + seat_price;
// ... price is deducted without validation
client_state.sub_crncy_tokens(price)?;
```

Similarly, in `sell_market_seat()`, the sell price is calculated:

```rust
let seat_price = PerpEngine::get_place_sell_price(
    instrument.perp_clients_count,
    instrument.crncy_token_decs_count,
)?;

client_state.add_crncy_tokens(seat_price)?;
```

The price calculation functions (`get_place_buy_price()` and `get_place_sell_price()`) use a bonding curve model where the price increases with each additional seat. The price is calculated based on:

```rust
pub fn get_place_buy_price(supply: u32, dec_factor: u32) -> Result<i64, DeriverseError> {
    let df = get_dec_factor(dec_factor);
    Ok(get_reserve(supply + 1, df)? - get_reserve(supply, df)?)
}

pub fn get_place_sell_price(supply: u32, dec_factor: u32) -> Result<i64, DeriverseError> {
    let df = get_dec_factor(dec_factor);
    Ok(get_reserve(supply, df)? - get_reserve(supply - 1, df)?)
}
```
The problem:
1. Between transaction submission and execution, other legitimate market transactions can change `perp_clients_count`, causing the actual execution price to differ from what the user expected
2. Users have no way to specify a maximum acceptable price for buying or minimum acceptable price for selling
3. The price is calculated and immediately applied without any validation against user expectations
4. During periods of high market activity, concurrent seat purchases/sales can cause significant price drift

**Impact:**
- **Unpredictable Execution:** Users have no guarantee that their transaction will execute at an acceptable price, even in normal market conditions
- **Poor User Experience:** Users cannot protect themselves from unfavorable price movements caused by legitimate concurrent market activity

**Recommended Mitigation:** Add slippage protection by allowing users to specify maximum/minimum acceptable prices in the instruction data, and validate the calculated price against these limits before execution.

**Deriverse:** Fixed in commit [a8181f3](https://github.com/deriverse/protocol-v1/commit/a8181f37e475eb1144f39490b62e45a476b2455d).

**Cyfrin:** Verified

## [M-32] Referral discount is not applied when `fees_prepayment` is zero in `Perp Engine::fill`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In `PerpEngine::fill`, when `fees_prepayment` is zero we do not apply the referral discount even though we still send `ref_payment` to `ref_address`.

```rust
                if *fees_prepayment == 0 {
                    let fee = (traded_crncy as f64 * self.fee_rate) as i64;
                    taker_info.sub_funds(fee).map_err(|err| drv_err!(err))?;
                    fee
                } else {
```

`self.fee_rate` is equal to `perp_fee_rate`.

**Impact:** The user is required to pay additional funds due to the referral discount not being applied, causing a loss to the user.


**Recommended Mitigation:** Instead of charging `self.fee_rate`, we should charge the fee rate after applying the referral discount, `(1.0 - args.ref_discount) * self.fee_rate`.



**Deriverse:** Fixed in commit [91bffc](https://github.com/deriverse/protocol-v1/commit/91bffc86cf2e6e441ca8a526d68808dbc19a122a).

**Cyfrin:** Verified.

## [M-33] Referral Incentives Disabled for All Legitimate Users During Any Liquidation
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Once the engine detects any instrument that requires liquidation (`is_long_margin_call` or `is_short_margin_call`), the `margin_call` flag is set to true for every subsequent `new_perp_order`. This flag is passed unchanged into `match_{ask,bid}_orders`, which disables referral payouts while it is `true`. As a result, all users— even those submitting normal orders unrelated to the liquidation — stop receiving/producing referral rewards for as long as any liquidation candidate remains. This global switch was likely intended only for actual liquidation trades.

In `new_perp_order.rs` the code sets `margin_call = engine.is_long_margin_call() || engine.is_short_margin_call();`

```rust
    let margin_call = engine.is_long_margin_call() || engine.is_short_margin_call();
    if !margin_call {
        engine.state.header.perp_spot_price_for_withdrowal = engine.state.header.perp_underlying_px;
    }
```

That boolean is forwarded to `PerpEngine::match_{ask,bid}_orders` via `MatchOrdersStaticArgs`

```rust
        if engine.cross(price, OrderSide::Ask) {
            (remaining_qty, _, ref_payment) = engine.match_ask_orders(
                Some(&mut client_community_state),
                &MatchOrdersStaticArgs {
                    price,
                    qty: data.amount,
                    ref_discount,
                    ref_ratio: header.ref_program_ratio,
                    ref_expiration: header.ref_program_expiration,
                    ref_client_id: header.ref_client_id,
                    trades_limit: 0,
                    margin_call,
                    client_id: client_state.temp_client_id,
                },
            )?;
        }
```

Referral rebates are conditioned on `!args.margin_call in perp_engine.rs`: when `margin_call` is `true`, ref_payment is forced to zero.
```rust
        let ref_payment = if self.time < args.ref_expiration && !args.margin_call {
            ((fees - rebates) as f64 * args.ref_ratio) as i64
        } else {
            0
        };
```

Liquidation routines (`check_long_margin_call, check_short_margin_call`) also pass `margin_call: true` explicitly, but there is no distinction between liquidation-triggered fills and ordinary orders.
```rust
    if buy {
        if engine.check_short_margin_call()? < MAX_MARGIN_CALL_TRADES {
            engine.check_long_margin_call()?;
        }
    } else if engine.check_long_margin_call()? < MAX_MARGIN_CALL_TRADES {
        engine.check_short_margin_call()?;
    }
```

Therefore, the presence of any liquidation candidate globally blocks referral rewards for all traders, regardless of who is being liquidated.


**Impact:** Legitimate users lose their expected referral incentives whenever any other account is under liquidation. Although not an immediate loss of funds, it represents a systemic incentive failure affecting all participants during stressed periods.

**Recommended Mitigation:** Restrict the `margin_call` flag to trades that are actually part of liquidation flows.

**Deriverse:** Fixed in commit [bc9bd6](https://github.com/deriverse/protocol-v1/commit/bc9bd6ab49dd15dcf2c3d83559fa4ad0bd6777d9).

**Cyfrin:** Verified.

## [M-34] Silent Failure in `voting_reset`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `voting_reset` function silently ignores failures when attempting to upgrade the community account header for writing. If the `community_acc` account is not marked as writable, the `upgrade()` call fails, but the function still returns `Ok(())`, giving the caller a false impression that the voting parameters were successfully reset when they were not.

The voting_reset function uses if let `Ok(header) = community_state.header.upgrade()` to conditionally update the community account header. However, this pattern silently returns error that occurs when the account is not marked as writable.

```rust
    if let Ok(header) = community_state.header.upgrade() {
        header.spot_fee_rate = START_SPOT_FEE_RATE;
        header.perp_fee_rate = START_PERP_FEE_RATE;
        header.max_discount = START_MAX_DISCOUNT;
        header.margin_call_penalty_rate = START_MARGIN_CALL_PENALTY_RATE;
        header.fees_prepayment_for_max_discount = START_FEES_PREPAYMENT_FOR_MAX_DISCOUNT;
        header.spot_pool_ratio = START_SPOT_POOL_RATIO;
    }
```

Throughout the codebase, all other functions that use `upgrade` properly propagate errors using the `?` operator:

```rust
    if let Some(ref mut header) = client_state.header {
        header.upgrade()?.points = 0;
        header.upgrade()?.mask &= 0xFFFFFFFFFFFFFF;
    }
```

```rust
        if community_state.header.voting_counter == 0 {
            community_state.header.upgrade()?.voting_counter += 1;
        }
```

**Impact:** If the `community_acc` account is incorrectly not marked as writable (due to a bug in the caller or a configuration error), the function will appear to succeed but no state updates will occur.

**Recommended Mitigation:** Change the code to properly propagate the error when `upgrade()` fails.

**Deriverse:** Fixed in commit [9ef2d7](https://github.com/deriverse/protocol-v1/commit/9ef2d7602f2964b210e36b8d1de3360992d9caa2).

**Cyfrin:** Verified.

\clearpage

## [M-35] Slippage Guard Could be Too Loose For Leveraged Perp Markets
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Perpetual “market” orders fall back to the same hard-coded `±12.5 %` price cap that is used for spot orders. While that cap is arguably acceptable for spot, it is dangerously loose for leveraged perp trading: a user can be filled up to 12.5 % away from the reference price in one shot, magnifying losses by the user’s leverage factor. There is no ability to tighten this slippage or enforce a stricter cap when leverage is high.

In `new_perp_order.rs`, non-limit buys default to `px + (px >> 3)` and sells to `px - (px >> 3)`, i.e. ±12.5 % of the current underlying price.

```rust
    let (price, min_tokens) = PerpParams::get_settings(
        if data.order_type == OrderType::Limit as u8 {
            data.price
        } else if buy {
            px + (px >> 3)
        } else {
            px - (px >> 3)
        },
        data.amount,
        if buy { OrderSide::Bid } else { OrderSide::Ask },
        px,
        data.ioc,
        engine.dc,
    )?;
```

Spot orders reuse the same ±12.5 % window, which is acceptable because spot positions are unleveraged.

Perp orders, however, can be levered up to the protocol maximum (`MAX_PERP_LEVERAGE`). Filling a leveraged market order at `−12.5 % (or +12.5 %)` immediately consumes a large portion of the user’s margin and can nearly trigger unintended liquidation during extreme market conditions, even when the user was intended to trade near the mark price.

Also, users have no way to configure a tighter cap unless they avoid market orders altogether (use `limit+IOC`), which is unrealistic—many traders still expect market orders to have reasonable slippage protection.

**Impact:** Under volatile or thin-liquidity conditions, leveraged traders who rely on market orders can be executed at very unfavorable prices (up to `12.5 %` away), leading to outsized losses or incoming instant liquidations.

**Recommended Mitigation:** Ultimately the team should decide how strict to be, but the current 12.5 % blanket cap is out of line with leveraged-market risk management and should be tightened.

If possible, implement leverage-aware slippage caps (e.g., shrink tolerance as leverage increases) or allow users to specify a custom slippage limit, with a protocol-defined maximum.

Another recommendation is to benchmark major CEX/DEX perp products to choose a safer default.

**Deriverse:** Fixed in commit [b2ff47aa](https://github.com/deriverse/protocol-v1/commit/b2ff47aa00fc88daec2eb15339751e27fb23a723).

**Cyfrin:** Verified.

## [M-36] Wrong accounting of fee in perp engine
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** In the perp fee calculation logic within [perp_engine.rs](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/perp/perp_engine.rs#L1202), when a user has partial fee prepayment that doesn't fully cover the trade fee, the function incorrectly returns [discount_sum + extra_fee](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/perp/perp_engine.rs#L1202) instead of `fees_prepayment + extra_fee`

The bug occurs because [discount_sum](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/perp/perp_engine.rs#L1198) represents the`trade value` covered by prepayment (calculated as [fees_prepayment / fee_rate]), not the fee amount itself. This results in a massively inflated fee return value.

```rust
                    } else {
                        let discount_sum = (*fees_prepayment as f64 / args.fee_rate) as i64;
                        let extra_fee = ((traded_crncy - discount_sum) as f64
                            * (1.0 - args.ref_discount)
                            * self.fee_rate) as i64;
                        let fee = discount_sum + extra_fee; // here, discount_sum is trade value, not fee
                        taker_info
                            .sub_funds(extra_fee)
                            .map_err(|err| drv_err!(err))?;
                        *fees_prepayment = 0;
                        fee
                    }
```
Consider this scenario:
INPUTS:
- traded_crncy = $10,000 (trade value)
- self.fee_rate = 0.001 (0.1% base fee)
- ref_discount = 0.20 (20% referral discount)
- args.fee_rate = 0.001 * 0.80 = 0.0008 (discounted rate)
- fees_prepayment = $5

STEP 1: Calculate `discount_fee`
discount_fee = 0.0008 * $10,000 = $8
Is $8 <= $5? NO means we enter partial coverage branch

STEP 2: Calculate `discount_sum`
discount_sum = $5 / 0.0008 = $6,250 (This is trade value covered from prepayment)

STEP 3: Calculate `extra_fee`
remaining_trade = $10,000 - $6,250 = $3,750
extra_fee = $3,750 * 0.80 * 0.001 = $3

IT RETURNS (worng):
fee = discount_sum + extra_fee = $6,250 + $3 = $6,253 : this is wrong, it's inflated

CORRECT RETURN:
fee = fees_prepayment + extra_fee = $5 + $3 = $8 ← CORRECT

WHAT USER ACTUALLY PAYS:
- Prepayment consumed: $5
- extra_fee from funds: $3
- Total paid: $8 (correct amount deducted)

BUT PROTOCOL RECORDS: $6,253 as fee which is way too much inflated and totally incorrect

**Impact:** Protocol records inflated fee which will later on corrupt rest of accounting which depend on it.

**Recommended Mitigation:** In the fill() function, change:
```rust
} else {
    let discount_sum = (*fees_prepayment as f64 / args.fee_rate) as i64;
    let extra_fee = ((traded_crncy - discount_sum) as f64
        * (1.0 - args.ref_discount)
        * self.fee_rate) as i64;
    // FIX: Use `fees_prepayment` (actual fee amount), not discount_sum (trade value)
    let fee = (*fees_prepayment) + extra_fee;
    taker_info
        .sub_funds(extra_fee)
        .map_err(|err| drv_err!(err))?;
    *fees_prepayment = 0;
    fee
}
```
**Deriverse**
Fixed in commit: [94da2f1](https://github.com/deriverse/protocol-v1/commit/94da2f1ed0a85b0a8f247bbd5da9cd7dc04f82ba)

**Cyfrin:** Verified.

## [M-37] Remove or resolve TODO
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Remove or resolve TODO:
```solidity
SablierBob.sol
330:                // TODO: transfer entire fee to comptroller admin instead of transferring when user redeems.
```

**Sablier:** Fixed in commit [7928553](https://github.com/sablier-labs/lockup/commit/79285536d2dde653c0a7629785787ffb79f548f6#diff-f327a4238131660e66994c40e1d9f1ddd672c4403ed6f4ca2f1e04f7c82a86c3L330).

**Cyfrin:** Verified.

## [M-38] Use `msg.sender` instead of accessing `comptroller` state variable to save gas
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Event `SetTradeFee` in `SablierEscrow` should use `msg.sender` (`CALLER` opcode = 2 gas) instead of accessing the comptroller storage variable (`SLOAD` opcode = 100 gas) to save gas. Since the function can only be called by the `comptroller`, using `msg.sender` is safe.

```solidity
function setTradeFee(UD60x18 newTradeFee) external override onlyComptroller {

        ... ... ...

        // Log the event.
        emit SetTradeFee(address(comptroller), previousTradeFee, newTradeFee);
    }
```

**Recommended Mitigation:** Use `msg.sender` in the event emission instead.

**Sablier:** Fixed in commit [c94cb23](https://github.com/sablier-labs/lockup/commit/c94cb232b62c188e2a1b23ab625bfd5374b92d7a#diff-ba86d209aeed90bf0447759321f08154ad7e0f4edc85849136cba83e27281fbbR162-R280).

**Cyfrin:** Verified.

\clearpage

## [M-39] Inconsistent effective swap fee calculations between `Bunni Quoter::quote Swap` and `Bunni Hook Logic::before Swap` due to incorrect application of hook and curator fees
- Severity: `Medium`
- Source report: `hooklet.md`

### Detailed Content (from source)
**Description:** While both `BunniQuoter::quoteSwap` and `BunniHookLogic::beforeSwap` are intended to contain the same fee logic, there remain a couple of inconsistencies that appear to have either been missed or reintroduced as a regression.

Firstly, `BunniQuoter::quoteSwap` applies an additional adjustment to the swap fee when `useAmAmmFee` is enabled to add the hook fee, increasing the effective fee charged to the swapper:

```solidity
swapFee += uint24(hookFeesBaseSwapFee.mulDivUp(hookFeeModifier, MODIFIER_BASE));
```

This adjustment is intended to account for the actual cost of the swap including the hook fee; however, in `BunniHookLogic::beforeSwap`, which performs the actual execution of the swap, this adjustment is not actually applied. The base fee is computed for use in subsequent event emission and passed to the `HookletLib::hookletAfterSwap` call without including the hook fee, resulting in an incorrect effective swap fee being used during execution.

Secondly, while `BunniQuoter::quoteSwap` intends to provide pricing and fee estimates for a simulated swap, it omits the application of a curator fee that is present and deducted alongside the protocol and am-AMM fees in the actual `BunniHookLogic::beforeSwap` logic:

```solidity
curatorFeeAmount = baseSwapFeeAmount.mulDivUp(curatorFees.feeRate, CURATOR_FEE_BASE);
```

As such, this represents an additional inconsistency between these two implementations that results in the quote differing from the actual execution, in this case charging more than quoted. This portion of the discrepancy originates from the design of `BunniQuoter::quoteSwap` as a view function that does not have direct access to the `curatorFees` in `HookStorage`.

**Impact:** Off-chain components relying on the `Swap` event may reference an incorrect value for the swap fee. Interfaces relying on `BunniQuoter::quoteSwap` to estimate the swap fees/output will underestimate the total fee and overestimate the user’s output. Hooklets relying on `swapFee` for accounting or additional fee calculations may charge an incorrect amount. When the hook fee modifier and curator fee rate are non-zero, the swap fee used in the actual deduction and emitted in events is smaller than that computed by the quote.

**Proof of Concept:** The following fuzz test can be added to `BunniHook.t.sol` to assert equivalence, and demonstrates that this is not currently the case:

```solidity
function test_fuzz_quoter_quoteSwap(
    uint256 swapAmount,
    bool zeroForOne,
    bool amAmmEnabled
) external {
    swapAmount = bound(swapAmount, 1e6, 1e36);

    // deploy mock hooklet with all flags
    bytes32 salt;
    unchecked {
        bytes memory creationCode = type(HookletMock).creationCode;
        for (uint256 offset; offset < 100000; offset++) {
            salt = bytes32(offset);
            address deployed = computeAddress(address(this), salt, creationCode);
            if (
                uint160(bytes20(deployed)) & HookletLib.ALL_FLAGS_MASK == HookletLib.ALL_FLAGS_MASK
                    && deployed.code.length == 0
            ) {
                break;
            }
        }
    }
    HookletMock hooklet = new HookletMock{salt: salt}();

    ILiquidityDensityFunction ldf_ =
        new UniformDistribution(address(hub), address(bunniHook), address(quoter));
    bytes32 ldfParams = bytes32(abi.encodePacked(ShiftMode.STATIC, int24(-5) * TICK_SPACING, int24(5) * TICK_SPACING));

    (IBunniToken bunniToken, PoolKey memory key) = hub.deployBunniToken(
        IBunniHub.DeployBunniTokenParams({
            currency0: Currency.wrap(address(token0)),
            currency1: Currency.wrap(address(token1)),
            tickSpacing: TICK_SPACING,
            twapSecondsAgo: 0,
            liquidityDensityFunction: ldf_,
            hooklet: hooklet,
            ldfType: LDFType.STATIC,
            ldfParams: ldfParams,
            hooks: bunniHook,
            hookParams: abi.encodePacked(
                FEE_MIN,
                FEE_MAX,
                FEE_QUADRATIC_MULTIPLIER,
                FEE_TWAP_SECONDS_AGO,
                POOL_MAX_AMAMM_FEE,
                SURGE_HALFLIFE,
                SURGE_AUTOSTART_TIME,
                VAULT_SURGE_THRESHOLD_0,
                VAULT_SURGE_THRESHOLD_1,
                REBALANCE_THRESHOLD,
                REBALANCE_MAX_SLIPPAGE,
                REBALANCE_TWAP_SECONDS_AGO,
                REBALANCE_ORDER_TTL,
                amAmmEnabled,
                ORACLE_MIN_INTERVAL,
                uint48(1)
            ),
            vault0: ERC4626(address(0)),
            vault1: ERC4626(address(0)),
            minRawTokenRatio0: 0.08e6,
            targetRawTokenRatio0: 0.1e6,
            maxRawTokenRatio0: 0.12e6,
            minRawTokenRatio1: 0.08e6,
            targetRawTokenRatio1: 0.1e6,
            maxRawTokenRatio1: 0.12e6,
            sqrtPriceX96: TickMath.getSqrtPriceAtTick(4),
            name: bytes32("BunniToken"),
            symbol: bytes32("BUNNI-LP"),
            owner: address(this),
            metadataURI: "metadataURI",
            salt: ""
        })
    );

    // make initial deposit to avoid accounting for MIN_INITIAL_SHARES
    uint256 depositAmount0 = PRECISION;
    uint256 depositAmount1 = PRECISION;
    vm.startPrank(address(0x6969));
    token0.approve(address(PERMIT2), type(uint256).max);
    token1.approve(address(PERMIT2), type(uint256).max);
    weth.approve(address(PERMIT2), type(uint256).max);
    PERMIT2.approve(address(token0), address(hub), type(uint160).max, type(uint48).max);
    PERMIT2.approve(address(token1), address(hub), type(uint160).max, type(uint48).max);
    PERMIT2.approve(address(weth), address(hub), type(uint160).max, type(uint48).max);
    vm.stopPrank();

    _makeDepositWithFee(key, depositAmount0, depositAmount1, address(0x6969), 0, 0, "");

    vm.prank(HOOK_FEE_RECIPIENT_CONTROLLER);
    bunniHook.setHookFeeRecipient(HOOK_FEE_RECIPIENT);
    bunniHook.setHookFeeModifier(HOOK_FEE_MODIFIER);
    bunniHook.curatorSetFeeRate(key.toId(), uint16(MAX_CURATOR_FEE));

    if (amAmmEnabled) {
        _makeDeposit(key, 1_000_000_000 * depositAmount0, 1_000_000_000 * depositAmount1, address(this), "");

        bunniToken.approve(address(bunniHook), type(uint256).max);
        bunniHook.bid({
            id: key.toId(),
            manager: address(this),
            payload: bytes6(bytes3(POOL_MAX_AMAMM_FEE)),
            rent: 1e18,
            deposit: uint128(K) * 1e18
        });

        skipBlocks(K);

        IAmAmm.Bid memory bid = bunniHook.getBid(key.toId(), true);
        assertEq(bid.manager, address(this), "manager incorrect");
    }

    (Currency inputToken, Currency outputToken) =
        zeroForOne ? (key.currency0, key.currency1) : (key.currency1, key.currency0);
    _mint(inputToken, address(this), swapAmount * 2);
    IPoolManager.SwapParams memory params = IPoolManager.SwapParams({
        zeroForOne: zeroForOne,
        amountSpecified: -int256(swapAmount),
        sqrtPriceLimitX96: zeroForOne ? TickMath.MIN_SQRT_PRICE + 1 : TickMath.MAX_SQRT_PRICE - 1
    });

    // quote swap
    (bool success,,, uint256 inputAmount, uint256 outputAmount, uint24 swapFee,) = quoter.quoteSwap(address(this), key, params);
    assertTrue(success, "quoteSwap failed");

    // execute swap
    uint256 actualInputAmount;
    uint256 actualOutputAmount;
    {
        uint256 beforeInputTokenBalance = inputToken.balanceOfSelf();
        uint256 beforeOutputTokenBalance = outputToken.balanceOfSelf();
        vm.recordLogs();
        swapper.swap(key, params, type(uint256).max, 0);
        actualInputAmount = beforeInputTokenBalance - inputToken.balanceOfSelf();
        actualOutputAmount = outputToken.balanceOfSelf() - beforeOutputTokenBalance;
    }

    // check if swapFee matches
    Vm.Log[] memory logs = vm.getRecordedLogs();
    Vm.Log memory swapLog;
    for (uint256 i = 0; i < logs.length; i++) {
        if (logs[i].emitter == address(bunniHook) && logs[i].topics[0] == keccak256("Swap(bytes32,address,bool,bool,uint256,uint256,uint160,int24,uint24,uint256)")) {
            swapLog = logs[i];
            break;
        }
    }

    // parse log and extract swapFee from calldata
    (,,,,,,uint24 fee,) = abi.decode(swapLog.data, (
        bool,
        bool,
        uint256,
        uint256,
        uint160,
        int24,
        uint24,
        uint256
    ));

    assertEq(swapFee, fee, "swapFee doesn't match quoted swapFee");

    // check if actual amounts match quoted amounts
    assertEq(actualInputAmount, inputAmount, "actual input amount doesn't match quoted input amount");
    assertEq(actualOutputAmount, outputAmount, "actual output amount doesn't match quoted output amount");
}
```

**Recommended Mitigation:** Ensure that the hook fee modifier and curator fee logic is consistently applied across both `BunniQuoter::quoteSwap` and `BunniHookLogic::beforeSwap`. To do so, it may be necessary to expose a view function to query the curator fee rate per pool.

The `outputAmount`/`swapFeeAmount` adjustments are confusing because the logic is slightly inconsistent which makes them difficult to compare. If possible, consider pulling out this common shared logic into a separate library function to minimize the likelihood of introducing further inconsistencies.

**Bacon Labs:** Fixed in commits [2a54265](https://github.com/Bunniapp/bunni-v2/pull/135/commits/2a542654f0f13425a20306df4f7c82bb05685ae5) and [99dd8d4](https://github.com/Bunniapp/bunni-v2/pull/135/commits/99dd8d485b342a298eec028db91b54b90f63208d).

**Cyfrin:** Verified. The quoter and hook implementations are now consistent.

\clearpage

## [M-40] Lack of multicall support for `Fee Override Hooklet::set Fee Override`
- Severity: `Medium`
- Source report: `hooklet.md`

### Detailed Content (from source)
**Description:** `FeeOverrideHooklet::setFeeOverride` relies on `msg.sender` when validating ownership of the corresponding `BunniToken`; however, this will be incorrect when invoked through a multicaller contract and cause validation to fail even if the original caller is the actual owner.

Given that any account is free to deploy a Bunni pool and `LibMulticaller` is used heavily throughout the core Bunni contracts, it may be desirable to allow the owner of the pool to perform batched actions on both the hooklet and Bunni itself.

**Impact:** Any legitimate pool owner interacting with the `FeeOverrideHooklet` via a multicaller contract will be incorrectly prevented from doing so, potentially breaking external compatibilities that rely on multicall support.

**Recommended Mitigation:** Replace direct usage of `msg.sender` with `LibMulticaller::senderOrSigner` to remain consistent with the core Bunni contracts. This approach preserves compatibility with both direct and batched calls, ensuring proper access control while supporting multicall infrastructure.

**Bacon Labs:** Fixed in commit [9cf16a8](https://github.com/Bunniapp/hooklets/commit/9cf16a8400f25f5f9eeb2837915c76adc6dc4f54).

**Cyfrin:** Verified. `FeeOverrideHooklet::setFeeOverride` is now compatible with multicall invocations.

## [M-41] Oracle Inconsistency between surplus computation and post-check causes `Surplus::process Surplus(collateral Address,0)` Do S
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** `LibSurplus::_computeCollateralSurplus` uses `LibOracle::readMint` (L88) to value collateral and compute the extractable surplus. `readMint` snaps the spot price to the target price when spot falls within the `userDeviation` band — for example, spot=1.07 gets snapped to target=1.10 if `userDeviation` is 5%.

The computed `collateralSurplus` is then swapped into tokenP via `Swapper::swapExactInput` (Surplus L55), which internally calls `_quoteMintExactInput` — also using `readMint`. Both the surplus sizing and the swap agree on the inflated valuation, so the swap succeeds and mints tokenP proportional to the snapped price.

The problem is the post-check. After the swap, `Surplus::processSurplus` calls `LibGetters::getCollateralRatio` (L59) to verify the system is still healthy. `getCollateralRatio` uses `LibOracle::readRedemption` (LibGetters L81), which passes `deviation=0` — no snapping, always raw spot. It sees the collateral at 1.07 (not 1.10), but the stables issued now include the extra tokenP minted at the inflated 1.10 rate. The resulting CR drops below `surplusBufferRatio` and the transaction reverts with `Undercollateralized`.

```solidity
// Surplus.sol L59-60
(uint64 collatRatio,,,,) = LibGetters.getCollateralRatio();
if (collatRatio < ts.surplusBufferRatio) revert Undercollateralized();
```

The root cause is that surplus computation and the swap use `readMint` (optimistic, snapped), while the safety check uses `readRedemption` (conservative, raw). When spot < target within the deviation band, these two oracles diverge — the surplus is sized for the snapped price but validated against the real one.

**Impact:** DoS on `Surplus::processSurplus(collateralAddress,0)` whenever spot is below target but within `userDeviation`.
The governor can partially work around it by passing maxCollateralAmount lower than the value computed in `LibSurplus::_computeCollateralSurplus` , which caps the extraction to what the CR can absorb. But this requires off-chain knowledge of the oracle divergence.

**Proof of Concept:** Added to `tests/units/Parallelizer.t.sol`. Run with:
`forge test --match-test "test_ProcessSurplus_RevertWhen_OracleInconsistency_SpotBelowTargetWithinDeviation" -vvvv`

```solidity
function test_ProcessSurplus_RevertWhen_OracleInconsistency_SpotBelowTargetWithinDeviation()
    public
    setZeroMintFeesOnAllCollaterals
{
    // --- Step 1: Mint 100 tokenP at oracle = 1.0 (default STABLE target, userDeviation=0) ---
    _mintZeroFee(address(eurA), 100 * BASE_6);

    // --- Step 2: Reconfigure eurA oracle: MAX target = 1.10, userDeviation = 5% ---
    AggregatorV3Interface[] memory circuitChainlink = new AggregatorV3Interface[](1);
    uint32[] memory stalePeriods = new uint32[](1);
    uint8[] memory circuitChainIsMultiplied = new uint8[](1);
    uint8[] memory chainlinkDecimals = new uint8[](1);
    circuitChainlink[0] = AggregatorV3Interface(address(oracleA));
    stalePeriods[0] = 1 hours;
    circuitChainIsMultiplied[0] = 1;
    chainlinkDecimals[0] = 8;
    OracleQuoteType quoteType = OracleQuoteType.UNIT;
    bytes memory readData =
      abi.encode(circuitChainlink, stalePeriods, circuitChainIsMultiplied, chainlinkDecimals, quoteType);
    bytes memory targetData = abi.encode(uint256(1.10e18));

    vm.startPrank(governor);
    parallelizer.setOracle(
      address(eurA),
      abi.encode(
        OracleReadType.CHAINLINK_FEEDS,
        OracleReadType.MAX,
        readData,
        targetData,
        abi.encode(uint128(5e16), uint128(0)) // userDeviation=5%, burnRatioDeviation=0
      )
    );
    vm.stopPrank();

    // --- Step 3: Drop spot price to 1.07 — below target (1.10) but within 5% deviation ---
    MockChainlinkOracle(address(oracleA)).setLatestAnswer(int256(1.07e8));

    // --- Step 4: Verify surplus exists (overestimated by readMint) ---
    (uint256 collateralSurplus, uint256 stableSurplus) = parallelizer.getCollateralSurplus(address(eurA));
    assertGt(collateralSurplus, 0, "Surplus should exist (readMint snaps to 1.10)");
    assertGt(stableSurplus, 0, "Stable surplus should exist");

    // --- Step 5: processSurplus reverts — oracle inconsistency → Undercollateralized ---
    _setSlippageTolerance(address(eurA), 1e8);
    vm.startPrank(governor);
    parallelizer.updateSurplusBufferRatio(uint64(BASE_9));

    vm.expectRevert(Undercollateralized.selector);
    parallelizer.processSurplus(address(eurA), 0);
    vm.stopPrank();
}
```

The `-vvvv` trace confirms the flow:

```
Surplus::processSurplus
  → readMint(oracleA) → snaps 1.07 → 1.10   // surplus = ~10 eurA
  → eurA::approve(Parallelizer, 9.09e6)
  → Swapper::swapExactInput                   // self-swap, readMint=1.10
    → eurA::transferFrom(self, self, 9.09e6)  // collateral stays in diamond
    → tokenP::mint(Parallelizer, 9.999e18)    // ~10 tokenP minted
  → getCollateralRatio()                       // post-check
    → readRedemption(oracleA) → raw 1.07      // no snapping
    → CR = 107e18 / 110e18 ≈ 0.972            // < surplusBufferRatio (1.0)
    └─ REVERT: Undercollateralized()
```

**Recommended Mitigation:** A complete fix requires resolving the oracle valuation in `LibSurplus::_computeCollateralSurplus` to conservatively compute the stable surplus, and readMint to back-convert to collateral (matching the swap execution price).

```diff
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
-    uint256 oracleValue = LibOracle.readMint(collatInfo.oracleConfig);
+    uint256 redemptionValue = LibOracle.readRedemption(collatInfo.oracleConfig);
+    uint256 mintValue = LibOracle.readMint(collatInfo.oracleConfig);
+    uint256 conservativeValue = redemptionValue < mintValue ? redemptionValue : mintValue;
     uint256 totalCollateralValue =
-      LibHelpers.convertDecimalTo(oracleValue * currentCollateralBalance, 18 + collatInfo.decimals, 18);
+      LibHelpers.convertDecimalTo(conservativeValue * currentCollateralBalance, 18 + collatInfo.decimals, 18);
     uint256 stablesBacked = (uint256(collatInfo.normalizedStables) * ts.normalizer) / BASE_27;
     if (totalCollateralValue <= stablesBacked) revert ZeroSurplusAmount();
     stableSurplus = totalCollateralValue - stablesBacked;
-    collateralSurplus = LibHelpers.convertDecimalTo((stableSurplus * BASE_18) / oracleValue, 18, collatInfo.decimals);
+    collateralSurplus = LibHelpers.convertDecimalTo((stableSurplus * BASE_18) / mintValue, 18, collatInfo.decimals);
   }
```
This adds non-trivial complexity.
As a practical alternative, the team can use the existing maxCollateralAmount parameter: compute the correct collateralSurplus off-chain using both oracle values and pass it to processSurplus, bypassing the on-chain overestimate.


**Parallel:** Fixed in commit [7d9d712](https://github.com/parallel-protocol/parallel-parallelizer/commit/7d9d712c7fcd3db8325424d932089b7f79ab8656).

**Cyfrin:** Verified. Fixed by implementing the recommended mitigation.

## [M-42] `Dividend Manager::distribute Payout` will always revert after 255 payouts, preventing any future payout distributions
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `DividendManager::HolderManagementStorage::_currentPayoutIndex` is declared as `uint8`:
```solidity
/// @dev The current index that is yet to be paid out.
uint8 _currentPayoutIndex;
```

`_currentPayoutIndex` is incremented every time `DividendManager::distributePayout` is called:
```solidity
$._payouts[$._currentPayoutIndex++] = PayoutInfo({
    amount: payoutAmount,
    totalSupply: SafeCast.toUint128(totalSupply())
});
```

**Impact:** The maximum value of `uint8` is 255 so `DividendManager::distributePayout` can only be called 255 times; any further calls will always revert meaning no more payout distributions are possible.

**Recommended Mitigation:** If requiring more than 255 payout distributions:
* use a larger size to store `DividendManager::HolderManagementStorage::_currentPayoutIndex`
* change the `uint8` key in this mapping to match the larger size:
```solidity
mapping(address => mapping(uint8 => TokenBalanceChange)) _balanceHistory;
```
* change the `uint256` key in this mapping to match:
```solidity
mapping(uint256 => PayoutInfo) _payouts;
```

Consider using named mappings to explicitly show that these indexes all refer to the same entity, the payout index.

In Solidity a storage slot is 256 bits and an address uses 160 bits. Examining the relevant storage layout of `struct HolderManagementStorage` shows that `_currentPayoutIndex` could be declared as large as `uint56` without using any additional storage slots:
```solidity
IERC20 _stablecoin; // 160 bits
uint8 _stablecoinDecimals; // 8 bits
uint32 _payoutFee; // 32 bits
// 200 bits have been used so 56 bits available in the current storage slot
// _currentPayoutIndex could be declared as large as `uint56` with no
// extra storage requirements
uint8 _currentPayoutIndex;
```

**Remora:** Fixed in commit [f929ff1](https://github.com/remora-projects/remora-smart-contracts/commit/f929ff115f82e76c8eb497ce769792e8de99602b#diff-b6e3759e2288f06f4db11f44b35e7a6398f0301035472704a0479aab4afd9b48R62) by increasing `_currentPayoutIndex` to `uint16` which will be sufficient.

**Cyfrin:** Verified.

## [M-43] Burning ALL Property Tokens of a frozen holder results in the holder losing the payouts distribution while he was frozen
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Burning PropertyTokens from frozen holders has an edge case when all the tokens owned by a frozen holder get burned. This is how burning PropertyTokens impacts the payouts for distributions of frozen holders:
- If not all the PropertyTokens owned by a frozen holder are burned, the holder can still have access to the payouts for the distributions while he was frozen.
- If all the PropertyTokens owned by a frozen holder are burned, the holder would lose the payouts for the distributions while he was frozen.

The discrepancy in the behavior when burning PropertyTokens of Frozen Holders demonstrates an edge case that can result in frozen holders losing payouts.

For example - (Assume holders were frozen at the same index and got their tokens burned at the same index too):
- UserA has 1 PropertyToken and is frozen
- UserB has 2 PropertyTokens and is frozen too
- UserA and B get burned each a PropertyToken.
  - UserA loses the payouts distributions while he was frozen, whilst UserB still has access to the payouts for the 2 PropertyTokens that he owned during those distributions.

**Impact:** Burning ALL the PropertyTokens owned by a frozen holder causes the holder to lose the payouts for the distributions while he was frozen.

**Proof of Concept:** Run the following test to reproduce the issue described on the Description section
```solidity
    function test_frozenHolderLosesPayoutsBecauseItsTokensGotBurnt() public {
        address user1 = users[0];
        uint256 amountToMint = 2;

        // fund total payout amount to funding wallet
        uint64 payoutDistributionAmount = 100e6;

        // Distribute payouts for the first 5 distributions
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        _whitelistAndMintTokensToUser(user1, amountToMint);

        vm.prank(user1);
        remoraTokenProxy.approve(address(this), amountToMint);

        paySettlerProxy.initiateBurning(address(remoraTokenProxy), address(this), 0);

        // verify increased current payout index twice
        assertEq(remoraTokenProxy.getCurrentPayoutIndex(), 5);

        // Distribute payouts for distributions 5 - 10
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // Freze user 2 at distributionIndex 10
        remoraTokenProxy.freezeHolder(user1);

        uint256 user1HolderBalanceAfterBeingFrozen = remoraTokenProxy.payoutBalance(user1);

        // Distribute payouts for distributions 10 - 15
        for(uint i = 1; i <= 5; i++) {
            _fundPayoutToPaymentSettler(payoutDistributionAmount);
        }

        // verify increased current payout index twice
        assertEq(remoraTokenProxy.getCurrentPayoutIndex(), 15);

        assertEq(user1HolderBalanceAfterBeingFrozen, remoraTokenProxy.payoutBalance(user1), "Frozen holder earned payout while being frozen");

        uint256 user1PayoutBalance = remoraTokenProxy.payoutBalance(user1);
        // 5 distributions of 100e6 all for user1
        assertEq(user1PayoutBalance, 500e6, "User1 Payout is incorrect");

        vm.prank(user1);
        remoraTokenProxy.claimPayout();
        assertEq(stableCoin.balanceOf(user1), user1PayoutBalance, "Error while claiming payout");
        assertEq(remoraTokenProxy.payoutBalance(user1), 0);

        //@audit-info => When the holder is unfrozen, he gets access to the payouts for al the distributions while he was frozen
        uint256 snapshotBeforeUnfreezing = vm.snapshotState();
        // unfreeze user1 and validate it gets access to all the distributions while it was frozen
        remoraTokenProxy.unFreezeHolder(user1);
        // After being unfrozen there were pending only 5 distributions of 100e6 all for user1
        assertEq(remoraTokenProxy.payoutBalance(user1), 500e6, "User1 Payout is incorrect");
        vm.revertToState(snapshotBeforeUnfreezing);

        uint256 snapshotBeforeBurningAllFrozenHolderTokens = vm.snapshotState();
        //@audit-info => Burning ALL PropertyTokens from a holder while is frozen results in the holder
        // NOT being able to access the payouts of the distributions while he was frozen
        remoraTokenProxy.burnFrom(user1, 2, false);
        assertEq(remoraTokenProxy.balanceOf(user1), 0);

        assertEq(remoraTokenProxy.payoutBalance(user1), 0);
        // unfreeze user1 and validate it loses the payouts of the distributions while it was frozen
        remoraTokenProxy.unFreezeHolder(user1);
        assertEq(remoraTokenProxy.payoutBalance(user1), 0);
        vm.revertToState(snapshotBeforeBurningAllFrozenHolderTokens);

        //@audit-info => Burning NOT ALL PropertyTokens from a holder while is frozen results in the holder
        // being able to access the payouts of the distributions while he was frozen
        assertEq(remoraTokenProxy.payoutBalance(user1), 0);
        remoraTokenProxy.burnFrom(user1, 1, false);
        assertEq(remoraTokenProxy.balanceOf(user1), 1);
        remoraTokenProxy.unFreezeHolder(user1);
        assertEq(remoraTokenProxy.payoutBalance(user1), 500e6);
    }
```

**Recommended Mitigation:** The least disruptive mitigation to prevent this issue is to add a check on the `burnFrom` to revert the tx if the account has been left without more propertyTokens and the account is frozen
```diff
function burnFrom(
        address account,
        uint256 value
    ) external restricted whenBurnable {
        _spendAllowance(account, _msgSender(), value);
        _burn(account, value);
+      if(balanceOf(account) == 0 && isHolderFrozen(account)) revert UserIsFrozen(account);
    }
```
Alternatively, similar to the burn(), revert if the account if frozen.
```diff
    function burnFrom(
        address account,
        uint256 value
    ) external restricted whenBurnable {
+       if (isHolderFrozen(account)) revert UserIsFrozen(account);
        _spendAllowance(account, _msgSender(), value);
        _burn(account, value);
    }
```

**Remora:** Fixed in commit [6008aec](https://github.com/remora-projects/remora-smart-contracts/commit/6008aecffdd83311e4552e8efee42eae59b3cd30) by preventing burning on frozen users.

**Cyfrin:** Verified.

## [M-44] Cache identical storage reads
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive, cache identical storage reads to prevent re-reading the same storage values multiple times.

`PledgeManager.sol`:
```solidity
// cache `stablecoinDecimals` in `_fixDecimals`
307:            stablecoinDecimals < 6
308:                ? value / (10 ** (6 - stablecoinDecimals))
309:                : value * (10 ** (stablecoinDecimals - 6));

// cache `propertyToken` in `_verifyDocumentSignature`
316:        (bool res, ) = IRemoraRWAToken(propertyToken).hasSignedDocs(signer);
318:            IRemoraRWAToken(propertyToken).verifySignature(
```

`TokenBank.sol`:
```solidity
// cache `developments.length` in `removeToken`
152:        for (uint i = 0; i < developments.length; ++i) {
154:            address end = developments[developments.length - 1];

// cache `developments.length` in `viewAllFees`, claimAllFees
226:        for (uint i = 0; i < developments.length; ++i)
233:        for (uint i = 0; i < developments.length; ++i) {
```

`LockUpManager.sol`:
```solidity
// cache `userData.endInd` in `availableTokens`, `_unlockTokens`
117:        for (uint16 i = userData.startInd; i < userData.endInd; ++i) {
146:        for (uint16 i = userData.startInd; i < userData.endInd; ++i) {
```

**Remora:** Fixed in commit [6602423](https://github.com/remora-projects/remora-smart-contracts/commit/66024232cfea24b69bd055086f8088d40f3d1d4a).

**Cyfrin:** Verified.

## [M-45] Changing stablecoin on Token Bank can mess up fees collection
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** The feeAmount on each token is computed with the decimals of the current stablecoin (initially, a stablecoin of 6 decimals). If the stablecoin is changed to another one that uses decimals != than 6, if there are any pending fees before changing the stablecoin, those pending fees will then be paid with the new stablecoin, causing the actual collected money to be different than expected.

It is possible that by normal operations, a tx to buyTokens gets executed in between fees were claimed and the stablecoin is changed, if the purchased of new tokens generates fees, those new fees will be computed based on the current stablecoin, but will be paid out in the new stablecoin.
For example: if 10USDC (10e6) are as pending fees, and the new stablecoin is USDT (10e8), when those fees are collected, they will represent 0.1USDT.

```solidity
    function buyToken(
        address tokenAddress,
        uint32 amount
    ) external nonReentrant {
        ...
        uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;

        ...
        curData.feeAmount += feeValue;

        IERC20(stablecoin).transferFrom(
            to,
            address(this),
            stablecoinValue + feeValue
        );
        ...
    }

    function claimAllFees() external nonReentrant restricted {
       ...
        for (uint i = 0; i < developments.length; ++i) {
//@audit => Pending fees before stablecoin was changed were computed with the decimals of the old stablecoin
            totalValue += tokenData[developments[i]].feeAmount;
            tokenData[developments[i]].feeAmount = 0;
        }
        IERC20(stablecoin).transfer(custodialWallet, totalValue);
    }
```


**Impact:** Collected fees can be different from expected if the stablecoin is changed to a stablecoin that has different decimals than 6

**Recommended Mitigation:** Similar to how values are normalized to the decimals of the current stablecoin on the PledgeManager, implement the same logic on the TokenBank.
- Normalize the amounts of stablecoin before doing the actual transfers.

```diff
    function claimAllFees() external nonReentrant restricted {
        ...
-       IERC20(stablecoin).transfer(custodialWallet, totalValue);
+       IERC20(stablecoin).transfer(custodialWallet, _fixDecimals(totalValue));
        ...
    }

//@audit => Add this function to normalize values to decimals of the current stablecoin
    function _fixDecimals(uint256 value) internal view returns (uint256) {
        return
            stablecoinDecimals < 6
                ? value / (10 ** (6 - stablecoinDecimals))
                : value * (10 ** (stablecoinDecimals - 6));
    }
```

**Remora:** Fixed in commit [afd07fb](https://github.com/remora-projects/remora-smart-contracts/commit/afd07fb419c354dc223d0105b2fd0c5d565f465f).

**Cyfrin:** Verified.

## [M-46] Don't initialize to default values
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Don't initialize to default values:
```solidity
RWAToken/DividendManager.sol
186:      $._currentPayoutIndex = 0;

RWAToken/DocumentManager.sol
118:        for (uint256 i = 0; i < numDocs; ++i) {
222:        for (uint i = 0; i < dHLen; ++i) {

RWAToken/DividendManager.sol
349:                for (uint256 i = 0; i < len; ++i) {
463:        for (uint256 i = 0; i < rHolderStatus.forwardedPayouts.length; ++i) {

TokenBank.sol
152:        for (uint i = 0; i < developments.length; ++i) {
225:        uint64 totalValue = 0;
226:        for (uint i = 0; i < developments.length; ++i)
232:        uint64 totalValue = 0;
233:        for (uint i = 0; i < developments.length; ++i) {

PledgeManager.sol
119:        tokensSold = 0;
278:        uint256 fee = 0;

RemoraIntermediary.sol
258:        for (uint256 i = 0; i < len; ++i) {

PaymentSettler.sol
124:        for (uint i = 0; i < len; ++i) {
174:        for (uint i = 0; i < tokens.length; ++i) {
226:        uint256 totalFees = 0;
227:        for (uint i = 0; i < tokenList.length; ++i) {
```

**Remora:** Fixed in commit [6602423](https://github.com/remora-projects/remora-smart-contracts/commit/66024232cfea24b69bd055086f8088d40f3d1d4a).

**Cyfrin:** Verified.

## [M-47] Fee refund can lose precision
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `PledgeManager::refundTokens` calculates the user fee refund as:
```solidity
fee = (userPay.fee / userPay.tokensBought) * numTokens;
```

**Impact:** The fee refund will be less than it should be due to [division before multiplication](https://dacian.me/precision-loss-errors#heading-division-before-multiplication)

**Recommended Mitigation:** Perform multiplication before division:
```solidity
fee = userPay.fee * numTokens / userPay.tokensBought;
```

**Remora:** Fixed in commit [b69836f](https://github.com/remora-projects/remora-smart-contracts/commit/b69836f4e7effd2f1cc209608b9149671c79bc18).

**Cyfrin:** Verified.

## [M-48] Fee should be calculated after first purchase discount is applied in `Token Bank::buy` to prevent over-charging users
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `TokenBank::buy` calculates the total purchase amount as being composed of:
* `stablecoinValue` : value of the tokens
* `feeValue` : fee calculated off `stablecoinValue`
```solidity
        uint64 stablecoinValue = amount * curData.pricePerToken;
        uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;
```

Afterwards if this is the user's first purchase, they receive a discount on the `stablecoinValue`:
```solidity
        IReferralManager refManager = IReferralManager(referralManager);
        bool firstPurchase = refManager.isFirstPurchase(to);
        if (firstPurchase) stablecoinValue -= refManager.referDiscount();
```

However the fee is not updated so was still calculated from the initial higher `stablecoinValue` amount.

**Impact:** Users will pay higher fees than they should when receiving the first purchase discount.

**Recommended Mitigation:** Only calculate `feeValue` once the discount has been applied:
```diff
        address to = msg.sender;
        uint64 stablecoinValue = amount * curData.pricePerToken;
-       uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;

        IReferralManager refManager = IReferralManager(referralManager);
        bool firstPurchase = refManager.isFirstPurchase(to);
        if (firstPurchase) stablecoinValue -= refManager.referDiscount();

+       uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;
        curData.saleAmount += stablecoinValue;
        curData.feeAmount += feeValue;
```

**Remora:** Fixed in commits [4aea246](https://github.com/remora-projects/remora-smart-contracts/commit/4aea246c8de4dcd03bc11a5cd87ca617e787bdaf), [5510920](https://github.com/remora-projects/remora-smart-contracts/commit/55109201b0b592abb94a3c73a5f45c9c24b3d440) - changed the way fee calculation works for regulatory reasons.

**Cyfrin:** Verified.

## [M-50] Overriding fees can't be switched back once set
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** A fee is charged when buying a PropertyToken via the TokenBank. The system allows for charging a personalized fee on a per-token basis or a baseFee for all tokens.
If the variable `overrideFees` is set as true, the TokenBank will charge the baseFee that is charged to all tokens instead of charging the configured per-token fee.

The problem is that once the `overrideFees` variable is set to true, it is not possible to set it back to false to allow charging fees on a per-token basis.

```solidity
    function setBaseFee(
        bool updateFee,
        bool overrideFee,
        uint32 newFee
    ) external restricted {
        ...
//@audit => enters only when it is true.
//@audit => So, once set to true, it can't be changed back to false
        if (overrideFee) {
            overrideFees = overrideFee;
            emit FeeOverride(overrideFee);
        }
    }

```

**Impact:** Not possible to charge fees on a per-token basis once it has been configured to charge the baseFee.

**Recommended Mitigation:** Directly update `overrideFees` with the value of the parameter `overrideFee`.
```diff
    function setBaseFee(
        bool updateFee,
        bool overrideFee,
        uint32 newFee
    ) external restricted {
        ...
-       if (overrideFee) {
            overrideFees = overrideFee;
            emit FeeOverride(overrideFee);
-       }
    }
```

**Remora:** Fixed in commit [c38787f](https://github.com/remora-projects/remora-smart-contracts/commit/c38787f4cfd8272868bc939e73ee3d3d50889740).

**Cyfrin:** Verified.

## [M-51] Pledge can't successfully complete unless `Remora Token` is paused
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** When the funding goal has been reached, `PledgeManager::checkPledgeStatus` calls `RemoraToken::unpause`:
```solidity
function checkPledgeStatus() public returns(bool pledgeNowConcluded) {
    if (pledgeRoundConcluded) return true;

    uint32 curTime = SafeCast.toUint32(block.timestamp);
    if (tokensSold >= fundingGoal) {
        pledgeRoundConcluded = true;
        IRemoraRWAToken(propertyToken).unpause();
        emit PledgeHasConcluded(curTime);
        return true;
```

But if `RemoraToken` is not paused, this [reverts](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/utils/PausableUpgradeable.sol#L128) since `PausableUpgradeable::_unpause` has the `whenPaused` modifier.

**Impact:** Pledge can't successfully complete unless `RemoraToken` is paused.

**Proof of Concept:**
```solidity
function test_pledge(uint256 userIndex, uint32 numTokensToBuy) external {
    address user = _getRandomUser(userIndex);
    numTokensToBuy = uint32(bound(numTokensToBuy, 1, DEFAULT_FUNDING_GOAL));

    // fund buyer with stablecoin
    (uint256 finalStablecoinAmount, uint256 fee)
        = pledgeManager.getCost(numTokensToBuy);
    stableCoin.transfer(user, finalStablecoinAmount);

    // fund this with remora tokens
    remoraTokenProxy.mint(address(this), numTokensToBuy);
    assertEq(remoraTokenProxy.balanceOf(address(this)), numTokensToBuy);

    // allow PledgeManager to spend our remora tokens
    remoraTokenProxy.approve(address(pledgeManager), numTokensToBuy);

    PledgeManagerState memory pre = _getState(address(this), user);

    remoraTokenProxy.pause();

    vm.startPrank(user);
    stableCoin.approve(address(pledgeManager), finalStablecoinAmount);
    pledgeManager.pledge(numTokensToBuy, bytes32(0x0), bytes(""));
    vm.stopPrank();

    PledgeManagerState memory post = _getState(address(this), user);

    // verify remora token balances
    assertEq(post.holderRemoraBal, pre.holderRemoraBal - numTokensToBuy);
    assertEq(post.buyerRemoraBal, pre.buyerRemoraBal + numTokensToBuy);

    // verify stablecoin balances
    assertEq(post.pledgeMgrStableBal, pre.pledgeMgrStableBal + finalStablecoinAmount);
    assertEq(post.buyerStableBal, pre.buyerStableBal - finalStablecoinAmount);

    // verify PledgeManager storage
    assertEq(post.pledgeMgrTokensSold, pre.pledgeMgrTokensSold + numTokensToBuy);
    assertEq(post.pledgeMgrTotalFee, pre.pledgeMgrTotalFee + fee);
    assertEq(post.pledgeMgrBuyerFee, pre.pledgeMgrBuyerFee + fee);
    assertEq(post.pledgeMgrTokensBought, pre.pledgeMgrTokensBought + numTokensToBuy);
}
```

**Recommended Mitigation:** The `RemoraToken` contract should remain in the `paused` state until the pledge completes, though this may not be convenient. Alternatively change `PledgeManager::checkPledgeStatus` to only unpause `RemoraToken` if it is paused.

**Remora:** Fixed in commit [dddde02](https://github.com/remora-projects/remora-smart-contracts/commit/dddde029b97f33bcb91d0353632a3aa5f028c684).

**Cyfrin:** Verified.

## [M-52] Use constants instead of magic numbers
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Use constants instead of magic numbers; 1000000, 1e6 and 10 ** 6 are all identical and should declared in a constant that is imported into the various files.
```solidity
TokenBank.sol
111:        if (newFee > 1000000) revert InvalidValuePassed();
252:        uint64 feeValue = (stablecoinValue * curData.saleFee) / 1e6;

PledgeManager.sol
151:        require(newPenalty <= 1000000);
157:        require(newFee <= 1000000);
180:        uint256 fee = (stablecoinAmount * pledgeFee) / 1e6;
283:            refundAmount -= (refundAmount * earlySellPenalty) / 1e6;

RWAToken/DividendManager.sol
230:        require(newFee <= 1e6);
416:        payoutAmount -= (payoutAmount * fee) / (10 ** 6);

RWAToken/RemoraToken.sol
306:            require(newBurnFee <= 1e6);
398:        if (burnFee != 0) burnPayout -= (burnPayout * burnFee) / 1e6;
```

**Remora:** Fixed in commit [aaaab45](https://github.com/remora-projects/remora-smart-contracts/commit/aaaab4558bd370173de2d6f11697ecfd5f097072).

**Cyfrin:** Verified.

## [M-53] Use named returns where this eliminates a local variable and especially for `memory` returns
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Use named returns where this eliminates a local variable and especially for `memory` returns:
* `TokenBank::viewAllFees`

**Remora:** Fixed in commit [6602423](https://github.com/remora-projects/remora-smart-contracts/commit/66024232cfea24b69bd055086f8088d40f3d1d4a).

**Cyfrin:** Verified.

## [M-54] `last Total Assets` stores stale value due to update before penalty accrual
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** Across the `AccountableYield` strategy, variable `lastTotalAssets` stores the value returned from function `_totalAssets`. Since `accruedPenalties` is a factor taken into consideration  in `_totalAssets`, the code should ensure penalties are accrued before updating the `lastTotalAssets`.
```solidity
/// @dev Total assets managed = vault assets + deployed assets + accrued penalties
    function _totalAssets(address vault_) internal view returns (uint256) {
        return IAccountableVault(vault_).totalAssets() + deployedAssets + accruedPenalties;
    }
```

However, in all instances across the `AccountableYield` contract, `lastTotalAssets` does not accrue penalties before.

[`AccountableYield.borrow`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L282)

[`AccountableYield.onDeposit`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L367)

[`AccountableYield.onMint`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L392)

[`AccountableYield._accrueFees/_accruedFeeShares`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L463)

Similar instances also exist when `_totalAssets` is accessed directly before accruing penalties:

[`AccountableYield._accruedFeeShares`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L515)  -  In this particular instance, function `_accruedFeeShares` also returns this `newTotalAssets` value to function `_sharePrice`, which leads to a stale share price.

[`AccountableYield._calculateRequiredLiquidity`](https://github.com/Accountable-Protocol/credit-vaults-internal/blob/ba1c7754f891dd6d28a4b47d1989c8b03073abe2/src/strategies/AccountableYield.sol#L620)


**Recommended Mitigation:** Consider accruing penalties before updating `lastTotalAssets` as well as before directly accessing the value returned from function `_totalAssets`.

**Accountable:** Fixed in commit [`97f8b1a`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/97f8b1aed9e52e67c788892e97346d9b83bcacb1)

**Cyfrin:** Verified. Penalties now accrued in the above stated cases.

\clearpage

## [M-55] Fee structure updates can trigger accrual after loan has ended
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** In both `AccountableYield` and `AccountableOpenTerm`, `onFeeStructureChange()` only checks `if (_loan.startTime != 0)` before accruing:

```solidity
if (_loan.startTime != 0) {
    _accrueFees();     // AccountableYield
    // or _accrueInterest(); // AccountableOpenTerm
}
```

Since `startTime` is set once and not reset when a loan is `Repaid` or in default, fee-structure changes can still trigger accrual logic after the loan is no longer ongoing.

**Impact:** In `AccountableYield`, management fees are time-based; if no accrual happens after repayment, a later fee-structure update can “catch up” and mint a large amount of fee shares for the elapsed time since the last fee accrual, diluting holders unexpectedly. In `AccountableOpenTerm`, the hook can similarly update interest bookkeeping (or potentially revert if accrual assumes an ongoing loan). However this requires the protocol to update the fee structure after the loan has ended, which is unlikely.

**Recommended Mitigation:** Gate `onFeeStructureChange()` by loan state (e.g., only accrue when the loan is ongoing), rather than `startTime != 0`. For example, require `loanState == Ongoing*` before calling `_accrueFees()` / `_accrueInterest()`, or use `_requireLoanOngoing()` similar to other calls.

**Accountable:** Fixed in commit [`5f8fd3`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/5f8fd343287101ae69b6bc767e9459a9543526ab)

**Cyfrin:** Verified. Check changed to `loanState == LoanState.OngoingDynamic`.

## [M-56] Precompute `call Type Hash` in `Atomic Batcher::_hash Call Array`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `AtomicBatcher::_hashCallArray` recomputes the call type hash (the `keccak256` of the call-type string / type description) on every invocation:
```solidity
function _hashCallArray(Call[] calldata calls) private pure returns (bytes32) {
    bytes32 callTypeHash = keccak256("Call(address target,uint256 value,bytes data)");
```
Since this value is constant, it can be precomputed once as a `bytes32` constant.

Consider defining `bytes32 private constant _CALL_TYPEHASH = keccak256("...");` and use `_CALL_TYPEHASH` in `_hashCallArray()` instead of computing it each time.

**Accountable:** Fixed in commit [`6a63afe`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/6a63afee9fca88312fad4c208797b4b27b2f9b28)

**Cyfrin:** Verified.

## [M-57] Reuse `aum_` in `_accrue Fee Shares` to avoid recomputing debt
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** In `AccountableOpenTerm::_accrueFeeShares`, debt is recomputed as:

```solidity
uint256 debt = _loan.outstandingPrincipal.mulDiv(scaleFactor_, PRECISION);
```

However, the same debt/AUM value is already computed in `_accrueInterest()` and passed down as `aum_`. This makes the multiplication/division redundant and also keeps `scaleFactor_` as an unnecessary parameter.

Consider using `aum_` directly in `_accrueFeeShares` (e.g., `uint256 debt = aum_;`) and remove the `scaleFactor_` parameter from the function signature and call sites to save gas and simplify the code.

**Accountable:** Fixed in commit [`f350a8d`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/f350a8dc1769f9401b4d1ef62d3748540545ca4d)

**Cyfrin:** Verified.

## [M-58] Reuse `fm` Instead of re-instantiating `IFee Manager` in `Accountable Open Term::_mint Fee Shares`
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** In `AccountableOpenTerm::_mintFeeShares`, the treasury address is fetched by re-casting `feeManager`:

```solidity
address treasury_ = IFeeManager(feeManager).treasury();
```

However, the `IFeeManager fm` interface is already passed into the function, so this extra cast/load is unnecessary:

```solidity
address treasury_ = fm.treasury();
```

**Accountable:** Fixed in commit [`5e13285`](http://github.com/Accountable-Protocol/credit-vaults-internal/commit/5e132854c6ce3230350daf12feea77bb4a7e8586)

**Cyfrin:** Verified.

## [M-59] Cache identical storage reads
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** As reading from storage is expensive, it is more gas-efficient to cache values and read them from the cache if the storage has not changed. Cache identical storage reads:

`PreDepositPhaser.sol`:
```solidity
// use PreDepositPhase.YieldPhase instead
19:        emit PhaseStarted(currentPhase);
```

`pUSDeDepositor.sol`:
```solidity
// cache sUSDe and pUSDe to save 3 storage reads
// also change `deposit` to cache `sUSDe` and pass it as input to `deposit_sUSDe` saves 1 more storage read
96:            SafeERC20.safeTransferFrom(sUSDe, from, address(this), amount);
98:        sUSDe.approve(address(pUSDe), amount);
99:        return IMetaVault(address(pUSDe)).deposit(address(sUSDe), amount, receiver);

// cache USDe and pUSDe to save 2 storage reads
// also change `deposit` to cache `USDe` and pass it as input to `deposit_USDe` saves 1 more storage read
107:            SafeERC20.safeTransferFrom(USDe, from, address(this), amount);
110:        USDe.approve(address(pUSDe), amount);
111:        return pUSDe.deposit(amount, receiver);

// cache USDe to save 2 storage reads
// also change `deposit` to cache `USDe` and `autoSwaps[address(asset)]` then pass them as inputs to `deposit_viaSwap` saves 2 more storage reads
127:        uint256 USDeBalance = USDe.balanceOf(address(this));
130:            tokenOut: address(USDe),
140:        uint256 amountOut = USDe.balanceOf(address(this)) - USDeBalance;
```

`yUSDeDepositor.sol`:
```solidity
// cache pUSDe and yUSDe to save 2 storage reads
56:            SafeERC20.safeTransferFrom(pUSDe, from, address(this), amount);
58:        pUSDe.approve(address(yUSDe), amount);
59:        return yUSDe.deposit(amount, receiver);
```

`MetaVault.sol`:
```solidity
// cache assetsArr.length
241:        for (uint i = 0; i < assetsArr.length; i++) {
```

**Strata:** Fixed in commit [9a19939](https://github.com/Strata-Money/contracts/commit/9a1993975912fbcbaf684811b25de229947671c9).

**Cyfrin:** Verified.

## [M-60] Hard-coded slippage in `p USDe Depositor::deposit_via Swap` can lead to denial of service
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [Hard-coded slippage](https://dacian.me/defi-slippage-attacks#heading-hard-coded-slippage-may-freeze-user-funds) in `pUSDeDepositor::deposit_viaSwap` can lead to denial of service and in dramatic cases even [lock user funds](https://x.com/0xULTI/status/1875220541625528539).

**Recommended Mitigation:** Slippage parameters should be calculated off-chain and supplied as input to swaps.

**Strata:** Fixed in commit [2c43c07](https://github.com/Strata-Money/contracts/commit/2c43c07a839eb9d593c6bf67fc1b5c75b694aed7).

**Cyfrin:** Verified. Callers can now override the default slippage.

## [M-61] `Deposit Manager::sponsor Game` should revert if the game is `Cancelled` or `Concluded`
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DepositManager::sponsorGame` doesn't verify the state of the game when accepting sponsorship amounts:
```solidity
function sponsorGame(uint256 gameId, uint256 amount) external {
    GamePool storage pool = gamePools[gameId];
    pool.totalCollectedAmount += amount;
    sponsorAmounts[msg.sender][gameId] += amount;
    emit GameSponsored(gameId, msg.sender, pool.token, amount);
    SafeERC20.safeTransferFrom(IERC20(pool.token), msg.sender, address(this), amount);
}
```

**Impact:** Sponsors can sponsor `Cancelled` or `Concluded` games; in the case of `Concluded` games there is no way to retrieve their tokens. Sponsors can also sponsor non-existent games since `gameId` is not validated to belong to an actual game at all.

**Recommended Mitigation:** `DepositManager::sponsorGame` should revert if the game is `Cancelled` or `Concluded`.

**Majority Games:**
Fixed in commit [e01a1df](https://github.com/Engage-Protocol/engage-protocol/commit/e01a1df84bf8dc1cfda40ef9a52ac7bcc5e6fc75) - only allowing sponsorships for existing games in the `Created` or `Ongoing` state.

**Cyfrin:** Verified.

## [M-62] `Session Manager::reschedule Game` advances the start time but not the end time allowing for a griefing attack where the game creator can collect fees while preventing users from participating
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** When a game creator reschedules a game, they set a new start time, but the end time is never updated.

```solidity
 function rescheduleGame(uint256 _gameId, uint256 _newStartTime)
        external
        onlyCreator(_gameId)
        onlyState(_gameId, SessionState.Created)
    {
        Game storage game = games[_gameId];
        require(
            _newStartTime > game.startTime + minimumRescheduleTime,
            RescheduleTooSoon(game.startTime, minimumRescheduleTime, _newStartTime)
        );
        require(game.originalStartTime == 0, GameIsAlreadyRescheduled(_gameId));
        game.originalStartTime = game.startTime;
        game.startTime = _newStartTime; <------ just moving start time?
        emit GameRescheduled(_gameId, _newStartTime);
    }
```

The maximum game duration is 10 minutes, and the `minimumRescheduleTime` is 15 minutes, so the `rescheduleGame` function will always set a new start time that is later than the end time.

**Impact:** The `rescheduleGame` function does not work as expected which can result in the official game "end time" being in the past when the game starts. However the actual gameplay is controlled by:

* When questions are revealed
* The reaction deadlines for each question
* When solutions are revealed

Hence the creator can:

* Reschedule without updating end time
* Rush through revealing all questions
* Use minimum reaction deadlines (5 seconds each)
* Complete the game in minutes instead of the intended duration
* Conclude the game & collect fees while players barely had time to participate and can't get their game fee refunded

This issue allows creators to effectively steal entry fees by conducting "speed-run" games that players can't reasonably participate in.

**Proof of Concept:** The existing test in the test suite shows that the values passed for the new start time are typically greater than one day:

```solidity
// file: /test/SessionManagerRescheduleTest

 function test_rescheduleGame_VerifyOriginalStartTime() public {
        uint256 gameId = _createGame();

        uint256 originalStartTime = sessionManager.getStartTime(gameId);
        uint256 newStartTime = originalStartTime + sessionManager.minimumRescheduleTime() + 1 days;

        vm.prank(creator);
        sessionManager.rescheduleGame(gameId, newStartTime);

        // Verify original start time is preserved
        assertEq(sessionManager.getOriginalStartTime(gameId), originalStartTime);
    }
```

**Recommended Mitigation:** Consider updating the end time as well. The end time could be calculated by adding the original game duration (the difference between  start time and the original start time) to the new start time.

**Majority Games:**
Fixed in commit [ddb690f](https://github.com/Engage-Protocol/engage-protocol/commit/ddb690f09fc49e0a5d9191f1c8c9ce74c434aa58).

**Cyfrin:** Verified.

## [M-63] Anyone should be able to conclude the game once winners have been determined
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Currently only the game creator can call `SessionManager::concludeGame`, even though at this point the winners have been determined.

**Impact:** If the game creator doesn't like who won, they can not conclude the game. The game could then be cancelled by users via `SessionManager::cancelGameIfCreatorMissing` to get their game fee refunded, but this allows a game creator to not pay out winners if they don't like who won.

**Recommended Mitigation:** Allow anyone to call `SessionManager::concludeGame`. Since during this time the game creator can also call `SessionManager::cancelGame`, perhaps allow a timeout period before anyone can call `SessionManager::concludeGame` using an offset from when the game entered the `End` state.

**Majority Games:**
Fixed in commit [dca8622](https://github.com/Engage-Protocol/engage-protocol/commit/dca86228c93ad73486766a8d06f0e63eb292ee26).

**Cyfrin:** Verified.

## [M-64] More efficient implementation of `Session Manager::join Game` via better storage packing
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SessionManager::joinGame` performs these 4 storage reads:
```solidity
// reads games[_gameId].state up to 2 times
require(
    games[_gameId].state == SessionState.Created || games[_gameId].state == SessionState.Ongoing,
    InvalidGameState(SessionState.Created, games[_gameId].state)
);
// reads games[_gameId].numContestants once
require(
    games[_gameId].numContestants < maximumContestants,
    TooManyContestants(maximumContestants, games[_gameId].numContestants)
);
// reads games[_gameId].verificationRequired once
if (games[_gameId].verificationRequired) {
    require(isVerificationApproved[msg.sender], NotVerified(msg.sender));
}
```

The `Game` struct can be refactored to pack `state`, `numContestants` and `verificationRequired` into the same storage slot like this:
```solidity
struct Game {
    uint256 gameId;
    uint256 startTime;
    uint256 endTime;
    address sessionStrategy;
    address rewardStrategy;
    uint256 originalStartTime;
    address creator;
    address creatorfeeReceiver;
    uint32 numContestants;
    SessionState state;
    bool verificationRequired;
}
```

Then all 3 can be read inside `SessionManager::joinGame` through just one storage read:
```solidity
Game storage gameRef = games[_gameId];
(uint32 numContestants, SessionState state, bool verificationRequired)
    = (gameRef.numContestants, gameRef.state, gameRef.verificationRequired);

// remaining checks/processing follows as normal
```

**Majority Games:**
Fixed in commit [c7eafa2](https://github.com/Engage-Protocol/engage-protocol/commit/c7eafa2037270b0358e37c6f547950a37df01fe6).

**Cyfrin:** Verified.

## [M-65] Perform storage updates prior to external calls
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Most times it is safer to perform storage updates prior to external calls:
* `DepositManager.sol`
```solidity
// switch these around in `_refundEntryFee`
186:        SafeERC20.safeTransfer(IERC20(pool.token), player, pool.ticketPrice);
187:        pool.totalCollectedAmount -= pool.ticketPrice;
```

* `SessionManager.sol`
```solidity
// in `joinGame` perform the 2 storage updates prior to calling `_payEntryFee`
311:        _payEntryFee(_gameId, msg.sender);
312:        contestants[_gameId][msg.sender] = true;
313:        games[_gameId].numContestants++;
```

**Majestic Games:**
Fixed in commit [6525ee1](https://github.com/Engage-Protocol/engage-protocol/commit/6525ee1547e0b7834cb99a786773bed1861369c7).

**Cyfrin:** Verified.

## [M-66] Referral rewards accumulate to `address(0)` when players aren't referred
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DepositManager::_payEntryFee` does this:
```solidity
referralRewards[gameId][Registry(registry).referrers(player)] += pool.ticketPrice * REFERRER_FEE;
```

But `Registry(registry).referrers(player)` returns `address(0)` when `player` has not been referred.

**Impact:** Referral rewards accumulate to `address(0)`. These can't be claimed but it is still incorrect and should be fixed.

**Recommended Mitigation:** Only allocate referral rewards if the player has actually been referred; eg if `Registry(registry).referrers(player) != address(0)`.

**Majority Games:**
Fixed in commit [e090f2e](https://github.com/Engage-Protocol/engage-protocol/commit/e090f2e1b5f42eb212fdbda7be94ccf295281075) by introducing a `CLAIMER_ROLE` which can collect referral fees assigned to `address(0)`, such that referral fees are always collected. `Registry::setReferrer` has been modified to prevent an address having `CLAIMER_ROLE` from becoming a referrer since then they couldn't collect fees associated with their address.

**Cyfrin:** Verified. We note that `AccessControl::grantRole` has not been overridden such that a referrer could be granted `CLAIMER_ROLE` which would prevent them from claiming referrals associated with their address.

## [M-67] Use `uint128` to pack `Deposit Manager::protocol Fee`, `max Creator Fee` into the same storage slot
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `DepositManager::protocolFee`, `maxCreatorFee` (and the same fields inside the `GamePool` struct) will always be < `BASIS_POINTS=10000`, so they can be declared as `uint128` to pack both of them into the same storage slot.

This means that functions such as `DepositManager::getRewards` which read both of them can perform only 1 storage read instead of 2.

**Majority Games:**
Fixed in commit [adedfc2](https://github.com/Engage-Protocol/engage-protocol/commit/adedfc2224c118fd2ac88eeec826bd4be48d8b6e).

**Cyfrin:** Verified.

## [M-68] `Securitize Amm Nav Provider` missing `when Not Paused` modifier on important state-changing functions
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `SecuritizeAmmNavProvider` inherits from `BaseContract` which inherits from `PausableUpgradeable`, but does not have the `whenNotPaused` modifier on important state-changing functions.

**Impact:** Pausing `SecuritizeAmmNavProvider` has no effect; important state-changing functions can continue to be called even when the contract is paused. Looking at the other NAV providers this doesn't seem to be intended, eg  `SecuritizeInternalNavProvider::setRate` has the `whenNotPaused` modifier.

**Recommended Mitigation:** Add the `whenNotPaused` modifier to important state-changing functions such as `SecuritizeAmmNavProvider::resetBaseline, setPriceScaleFactor, executeBuyBase, executeSellBase`.

**Securitize:** Fixed in commit [f09cb9a](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/f09cb9a621b2fee4890d4cca7b952ec0398a6d1e).

**Cyfrin:** Verified.

## [M-69] Emit events first to refactor away local variables storing previous values
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** When values are being changed, emit events first to refactor away local variables storing previous values. For example in `SecuritizeAmmNavProvider::setPriceScaleFactor`:
```diff
    function setPriceScaleFactor(uint256 newScaleFactor) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newScaleFactor > 0, "scaleFactor = 0");

-       uint256 oldScaleFactor = priceScaleFactor;
+       emit PriceScaleFactorUpdated(priceScaleFactor, newScaleFactor);
        priceScaleFactor = newScaleFactor;

-       emit PriceScaleFactorUpdated(oldScaleFactor, newScaleFactor);
    }
```

Similar optimizations can be made in:
* `SecuritizeInternalNavProvider::setRate`
* `MbpsFeeManager::setFeePercentageMBPS, setFeeCollector`
* `AllowanceLiquidityProvider::setAllowanceProviderWallet`
* `CollateralLiquidityProvider::setExternalCollateralRedemption, setCollateralProvider`
* `BaseOffRamp::updateLiquidityProvider`
* `PublicStockOffRamp::updateNavProvider`
* `SecuritizeOffRamp::updateNavProvider`
* `AllowanceAssetProvider::setAllowanceProviderWallet`
* `SecuritizeOnRamp::updateNavProvider`
* `BaseOnRamp::updateAssetProvider, updateMinSubscriptionAmount`
* `PublicStockOnRamp::updateNavProvider`

**Securitize:** Fixed in commits [41538fa](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/41538faf0df8e31fd4a51f2a478fc6a48a7d6f3a), [7f500c1](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/7f500c1d40da961f709fdeeb9551ef1b6f258363).

**Cyfrin:** Verified.

## [M-70] Signatures used in `Public Stock On Ramp` and `Public Stock Off Ramp` lack investor-specified deadline and nonce parameters so can be used multiple times by operators
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Both `PublicStockOnRamp` and `PublicStockOffRamp` contracts use EIP-712 signatures to authorize investor transactions. However, these signatures do not include a deadline/expiration parameter in their signed data structure, making them valid indefinitely until executed.
In  `PublicStockOnRamp`, the signature only includes the liquidity amount and minimum output amount:

```solidity
bytes32 private constant TXTYPE_HASH = keccak256("Swap(uint256 liquidityAmount,uint256 minOutAmount)");

  function hashTx(uint256 _liquidityAmount, uint256 _minOutAmount) private view returns (bytes32) {
        bytes32 structHash = keccak256(
            abi.encode(TXTYPE_HASH, _liquidityAmount, _minOutAmount)
        );

        return _hashTypedDataV4(structHash);
    }
```

Similarly in `PublicStockOffRamp`:

```solidity
bytes32 private constant TXTYPE_HASH = keccak256("Redeem(uint256 assetAmount,uint256 minOutputAmount)");

function hashTx(uint256 _assetAmount, uint256 _minOutputAmount) private view returns (bytes32) {
        bytes32 structHash = keccak256(
            abi.encode(TXTYPE_HASH, _assetAmount, _minOutputAmount)
        );

        return _hashTypedDataV4(structHash);
    }
```

While both contracts have `_anchorPriceExpiresAt` as a function parameter to ensure the price feed isn't stale, this expiration is not part of the signed message. An investor's signature remains valid indefinitely and can be executed at any future time by an operator, as long as they provide a valid (non-expired) anchor price.
Additionally, there is no nonce mechanism in either contract to allow investors to invalidate/cancel previously signed transactions.

**Impact:** Once an investor signs a transaction, they cannot invalidate it even if market conditions change significantly, An operator could hold onto a signature for days/weeks/months and execute it at an inopportune time for the investor. Because there is no nonce used the operator could use the investor's signature to execute multiple transactions.

**Recommended Mitigation:** Include a deadline parameter in the signed message structure and implement a nonce perhaps using [NoncesUpgradeable](https://github.com/OpenZeppelin/openzeppelin-contracts-upgradeable/blob/master/contracts/utils/NoncesUpgradeable.sol) or similar to how `SecuritizeOnRamp` does it via the mapping `noncePerInvestor`. Since `PublicStockOnRamp` and `SecuritizeOnRamp` both inherit from `BaseOnRamp`, it may be ideal to move the common functionality into there.

**Securitize:** Fixed in commit [85142ed](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/85142edf57f24a4af30f2e46382188adac60fbc2).

**Cyfrin:** Verified.

## [M-71] Remove unused `Execute Pre Approved Transaction::nonce`
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `ExecutePreApprovedTransaction::nonce` is never actually used, since:

* `GlobalRegistryService::hashTx` always reads the current nonce from storage `noncePerInvestor[txData.senderInvestor]`
* the caller must have used the current nonce to sign - otherwise the signature will fail validation
* when validation succeeds, `executePreApprovedTransaction` always increments the current nonce by 1 so it can never be re-used

Hence the above mechanics correctly validate the nonce and `ExecutePreApprovedTransaction::nonce` can be safely removed as it is never used.

**Securitize:** Fixed in commit [c841572](https://github.com/securitize-io/bc-global-registry-service-sc/commit/c841572de8b7dcfee484f6f7f4ce9a19e579bf21).

**Cyfrin:** Verified.

\clearpage

## [M-73] Unnecessary gas consumption in deposit function due to redundant maximum deposit check
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `SecuritizeVaultV2::_depositWithFee` function performs an unnecessary check against `maxDeposit(from)` to validate that the deposit amount doesn't exceed the maximum allowed deposit limit. However, `SecuritizeVaultV2` does not override the `maxDeposit` function from its parent `ERC4626Upgradeable` contract, which means `maxDeposit` always returns `type(uint256).max`.

```solidity
// In SecuritizeVaultV2::_depositWithFee
function _depositWithFee(uint256 assets, address from) private returns (uint256) {
    address caller = _msgSender();
    uint256 maxAssets = maxDeposit(from); // Returns type(uint256).max
    if (assets > maxAssets) { // This condition will never be true
        revert ERC4626ExceededMaxDeposit(from, assets, maxAssets);
    }
    // ... rest of function
}

// In ERC4626Upgradeable (not overridden by SecuritizeVaultV2)
function maxDeposit(address) public view virtual returns (uint256) {
    return type(uint256).max; // Always returns maximum uint256 value
}
```
This creates a redundant comparison where `assets > type(uint256).max` will never be true for any realistic deposit amount, making the check pointless and wasteful of gas. The condition on line 346-348 will never trigger the revert `ERC4626ExceededMaxDeposit` because no uint256 value can exceed `type(uint256).max`.

The function call `maxDeposit(from)` and the subsequent comparison are executed on every deposit operation, unnecessarily consuming gas for a check that serves no purpose in the current implementation.

**Impact:** This unnecessary computation increases gas costs for every deposit operation without providing any functional benefit, resulting in higher transaction costs for users.

**Recommended Mitigation:** Remove the unnecessary maximum deposit check since `SecuritizeVaultV2` doesn't implement custom deposit limits:

```diff
function _depositWithFee(uint256 assets, address from) private returns (uint256) {
    address caller = _msgSender();
-   uint256 maxAssets = maxDeposit(from);
-   if (assets > maxAssets) {
-       revert ERC4626ExceededMaxDeposit(from, assets, maxAssets);
-   }

    uint256 fee = 0;
    if (address(feeManager) != address(0)) {
        fee = IFeeManager(feeManager).computeFee(IFeeManager.FeeApplicableOperation.Deposit, assets);
    }

    uint256 shares = previewDeposit(assets - fee);
    _depositAndSendFees(caller, from, assets, fee, shares);
    return shares;
}
```

Alternatively, if deposit limits are intended to be implemented in the future, override the `maxDeposit` function with the appropriate logic.

**Securitize:** Fixed in commits [5105f0](https://github.com/securitize-io/bc-securitize-vault-sc/commit/5105f03e95502fc887241e47f660996e9163d3e8) and [57805a](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/57805a83958e87e3f9b3677caf8554c09bd8fad0).

**Cyfrin:** Verified.

## [M-74] Unsafe ERC20 operations can cause unexpected failures with non-standard tokens
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The protocol uses direct `IERC20.transferFrom` and `IERC20.approve` function calls instead of OpenZeppelin's `SafeERC20` library wrappers. This creates compatibility issues with tokens that do not return boolean values or have non-standard implementations.

The primary occurrence is in `RWASegWrap::_pullAndApprove`, which is a critical internal function used during deposit and mint operations. When users call `depositById` or `mintById`, the wrapper contract attempts to transfer assets from the caller and approve the vault for spending. With tokens like USDT, the `approve` function may fail when trying to approve from a non-zero allowance to another non-zero value, or the `transferFrom` may not return a boolean value, causing the transaction to revert unexpectedly.

Similar unsafe operations are found in:
- `SecuritizeVault::liquidate` - uses `IERC20Metadata(asset()).approve(address(redemption), assets)`
- `SecuritizeVaultV2::_liquidateTo` - uses `IERC20Metadata(asset()).approve(address(redemption), assets)`

These functions handle core protocol operations, including asset deposits, share minting, and liquidations, making them critical for normal protocol functionality.

**Impact:** Users may be unable to deposit assets or liquidate shares when using tokens with non-standard ERC20 implementations, leading to failed transactions and degraded user experience.

**Recommended Mitigation:** Replace all direct `IERC20` calls with `SafeERC20` equivalents. Add the SafeERC20 import to `RWASegWrap.sol` and update the unsafe operations:

```diff
// Add import to RWASegWrap.sol
+import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract RWASegWrap is ... {
+   using SafeERC20 for IERC20;

    function _pullAndApprove(address caller, uint256 assets, uint256 vaultId) internal {
        ISegregatedVault vault = ISegregatedVault(vaults[vaultId]);
-       bool success = IERC20(asset).transferFrom(caller, address(this), assets);
-       if (!success) {
-           revert AssetTransferFailed();
-       }
-       success = IERC20(asset).approve(address(vault), assets);
-       if (!success) {
-           revert AssetApprovalFailed();
-       }
+       IERC20(asset).safeTransferFrom(caller, address(this), assets);
+       IERC20(asset).forceApprove(address(vault), assets);
    }
}
```

For the SecuritizeVault contracts:

```diff
// In SecuritizeVault.liquidate
-IERC20Metadata(asset()).approve(address(redemption), assets);
+IERC20Metadata(asset()).forceApprove(address(redemption), assets);

// In SecuritizeVaultV2._liquidateTo
-bool success = IERC20Metadata(asset()).approve(address(redemption), assets);
-if (!success) {
-    revert AssetApprovalFailed();
-}
+IERC20Metadata(asset()).forceApprove(address(redemption), assets);
```

**Securitize:** Fixed in commit [b64b27](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/b64b2772c6584d9133763a1c128a32d2df9d5ff0).

**Cyfrin:** Verified.

## [M-75] Incorrect haircut asset value conversion in `STBL_PT1_Issuer::generate Meta Data`
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** `STBL_PT1_Issuer::generateMetaData` (and its `STBL_LT1_Issuer` counterpart) uses the wrong oracle conversion function when calculating `haircutAmountAssetValue`, resulting in mathematically incorrect values being stored in NFT metadata.  The function uses `fetchForwardPrice()` that expects the input (`MetaData.haircutAmount`) to be in the asset currency but haircut amount is already converted into USD (when applied on `stableValueGross` which is in USD terms).

The issue stems from a unit conversion error where USD amounts are incorrectly passed to a function expecting asset amounts:

```solidity
function generateMetaData(uint256 assetValue) internal view returns (YLD_Metadata memory MetaData) {
    // ... other calculations ...

    // @audit Step 1: Convert asset to USD using fetchForwardPRice
    MetaData.stableValueGross = iSTBL_PT1_AssetOracle(AssetData.oracle)
        .fetchForwardPrice(MetaData.assetValue);

    // @audit Step 2: Calculate haircut in USD terms
    MetaData = MetaData.calculateDepositFees(); // Sets haircutAmount in USD

    // @audit BUG - Wrong conversion function used
    MetaData.haircutAmountAssetValue = iSTBL_PT1_AssetOracle(AssetData.oracle)
        .fetchForwardPrice(MetaData.haircutAmount);  // @audit inverse of price needs to be used
        //                 ^^^^^^^^^^^^^^^^^^^^
        // @audit This expects ASSET AMOUNT but receives USD AMOUNT
}
```


Correct conversion here is by applying the inverse of the oracle price to get the haircut value in asset token denomination.

**Impact:** While the core vault accounting logic is unaffected, `haircutAmountAssetValue` metadata is incorrect. Off-chain systems reading metadata get wrong values.

**Proof of Concept:** Here is a mock calculation:

```text
Step 1: stableValueGross = fetchForwardPrice(100e18)
       = (110000000 * 100e18) / 1e8 = 110e18 USD

Step 2: haircutAmount = (110e18 * 500) / 10000 = 5.5e18 USD

Step 3 (WRONG): haircutAmountAssetValue = fetchForwardPrice(5.5e18)
       = (110000000 * 5.5e18) / 1e8 = 6.05e18

Step 3 (CORRECT): haircutAmountAssetValue = fetchInversePrice(5.5e18)
       = (5.5e18 * 1e8) / 110000000 = 5e18

```

**Recommended Mitigation:** Consider using the `fetchInversePrice` to calculate `haircutAmountAssetValue`

**STBL:** Fixed in commit [1adc1f2](https://github.com/USD-Pi-Protocol/contract/commit/1adc1f2d05dcbcee89826ab9b7d625642c0834bd).

**Cyfrin:** Verified.

## [M-76] Use named imports
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Use named imports; this is already being done in some places but not others:
* `Issuance`:
```solidity
minter/Minter.sol
4:import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
5:import "@openzeppelin/contracts/access/AccessControl.sol";
6:import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

vault/StakingVault.sol
5:import "../interfaces/vault/IStakingVault.sol";
7:import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

helpers/TokensHolder.sol
4:import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

token/HilBTC.sol
4:import "@openzeppelin/contracts/access/AccessControl.sol";
```

* `Deposit-Registry`:
```solidity
interfaces/ICompliantDepositRegistry.sol
4:import "@openzeppelin/contracts/access/IAccessControl.sol";
5:import "./IComplianceChecker.sol";

interfaces/IComplianceChecker.sol
4:import "@openzeppelin/contracts/access/IAccessControl.sol";
5:import "@galactica-net/zk-certificates/contracts/interfaces/IVerificationSBT.sol";

ComplianceChecker.sol
4:import "@openzeppelin/contracts/access/AccessControl.sol";
5:import "./interfaces/IComplianceChecker.sol";

CompliantDepositRegistry.sol
4:import "@openzeppelin/contracts/access/AccessControl.sol";
5:import "./interfaces/IComplianceChecker.sol";
6:import "./interfaces/ICompliantDepositRegistry.sol";
```

**Syntetika:**
Fixed in commit [a8b4853](https://github.com/SyntetikaLabs/monorepo/commit/a8b485381ad97ffb01595e8e5cc3d479126fcee8).

**Cyfrin:** Verified.

## [M-77] Missing minimum deposit enforcement
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** The `BasisTradeVault::deposit` function does not enforce a minimum deposit amount. Allowing dust deposits can lead to several undesirable situations:

1.  **Economic Unviability:** A user might deposit an amount so small that the gas fees for the transaction are significantly higher than the value of the deposit itself.

2.  **Potential for Nuisance:** It could enable scenarios where an attacker spams the vault with many tiny deposits, which, while not a direct security threat, can be a nuisance.

Although the contract is protected from the most severe issues by the base ERC4626 implementation, enforcing a sensible minimum deposit amount is a good practice for user protection and contract robustness.

**Recommended Mitigation:** Introduce a new state variable, `minDepositAmount`, which can be set by an admin. Modify the `deposit` function to require that the deposited `assets` are greater than or equal to this minimum amount.

**Button:** Fixed in commit [`9cde24c`](https://github.com/buttonxyz/button-protocol/commit/9cde24caa4b3f5f37a059bb2fde172cfa374d3a9).

**Cyfrin:** Verified. A minimum deposit configurable by admin is now enforced

## [M-78] Incorrect Comment and Missing Lower Bound for `minimum Jrt Srt Ratio` in `Accounting`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:**
```solidity
/// @dev minimum TVL ratio: TVLjrt/TVLsrt, e.g. >= 0.05%
```
```solidity
minimumJrtSrtRatio = 0.05e18;
```
The comment says “0.05%” (0.0005e18) but the value is 5% (0.05e18). and there is no check to prevent setting value <0.05%
and it may be intended to start with 5% ratio



**Recommended Mitigation:**
- Update comment to reflect intended 5% (e.g., “>= 5%”).
- In `Accounting::setMinimumJrtSrtRatio`, add `require(bps >= 0.0005e18, "RatioTooLow");` for a min bound.

**Strata:**
Fixed in commit [eefd73](https://github.com/Strata-Money/contracts-tranches/commit/eefd73cfee7783cb45b19e0763d83ba2fb0084af) and [c1afee2](https://github.com/Strata-Money/contracts-tranches/commit/c1afee2f0c14531ddbe88f81d4aa4f3325e87fd1). Updated comment and added check to validate lower bound for `minimumJrtSrtRatio`

**Cyfrin:** Verified.

## [M-79] Fees can become stuck in `Uniswap V4Wrapper`
- Severity: `Medium`
- Source report: `vii.md`

### Detailed Content (from source)
**Description:** When a modification is made to Uniswap V4 position liquidity, such as in the case of a partial `UniswapV4Wrapper` unwrap which decreases liquidity, any outstanding fees are also transferred and required to be completely settled. For multiple holders of a given ERC-6909 `tokenId`, a proportional share is escrowed and paid out during a given holder's next interaction with the wrapper contract. However, there exists an edge case in which fees can become stuck in `UniswapV4Wrapper` if the final holder performs a full unwrap through the overload which transfers the underlying position directly to the caller.

Consider the following scenario:
* Alice has full ownership of a position `tokenId1`.
* Assume LP fees have accrued in the position.
* Alice partially unwraps `tokenId1` to remove a portion of the underlying liquidity.
* This accrues LP fees corresponding to the remainder of the position to the `UniswapV4Wrapper`.
* Alice max borrows and later gets fully liquidated.
* The liquidator fully unwraps the `tokenId1` position and received the underlying NFT but loses their share of the previously-accrued fees.
* The liquidator removes all the liquidity of the underlying position they received for the full liquidation, and burns the position.
* As a result, it is impossible to retrieve the fees remaining in the wrapper because the position has been burnt and is impossible to mint the same `tokenId` again.

**Impact:** LP fees can become stuck in the `UniswapV4Wrapper` contract under certain edge cases. This loss has medium/high impact with medium likelihood.

**Proof of Concept:** The following test is a simplified demonstration of the issue:

```solidity
function test_finalLosesFeesPoC() public {
    int256 liquidityDelta = -19999;
    uint256 swapAmount = 100_000 * unit0;

    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: liquidityDelta
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, borrower);
    wrapper.enableTokenIdAsCollateral(tokenId1);
    address borrower2 = makeAddr("borrower2");
    wrapper.transfer(borrower2, tokenId1, wrapper.FULL_AMOUNT() * 5 / 10);

    //swap so that some fees are generated
    swapExactInput(borrower, address(token0), address(token1), swapAmount);

    (uint256 expectedFees0Position1, uint256 expectedFees1Position1) =
        MockUniswapV4Wrapper(payable(address(wrapper))).pendingFees(tokenId1);

    console.log("Expected Fees Position 1: %s, %s", expectedFees0Position1, expectedFees1Position1);

    startHoax(borrower);
    wrapper.unwrap(
        borrower,
        tokenId1,
        borrower,
        wrapper.balanceOf(borrower, tokenId1),
        bytes("")
    );

    console.log("Wrapper balance of currency0: %s", currency0.balanceOf(address(wrapper)));

    startHoax(borrower2);
    wrapper.unwrap(borrower2, tokenId1, borrower2);

    console.log("Wrapper balance of currency0: %s", currency0.balanceOf(address(wrapper)));
    if (currency0.balanceOf(address(wrapper)) > 0 && wrapper.totalSupply(tokenId1) == 0) {
        console.log("Fees stuck in wrapper!");
    }
}
```

**Recommended Mitigation:** Check whether there are any outstanding fees accrued for a given `tokenId` when performing a full unwrap and transfer these to the recipient along with the underlying NFT. This would also have the added benefit of avoiding dust accumulating in the contract which may arise from floor rounding during proportional share calculations using small ERC-6909 balances.

**VII Finance:** Fixed in commit [bf5f099](https://github.com/kankodu/vii-finance-smart-contracts/commit/bf5f099b5d73dbff8fa6d403cb54ee6474828ac4).

**Cyfrin:** Verified. Fees are now fully settled when performing a full unwrap.

## [M-80] Unresolved developer comments
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** There are leftover developer comments that should be removed or resolved:

`Bet::initialize#L62`:
```solidity
// Maybe can skip this and send it striaght to Aave ?
```

and

`IBbet.Bet#L29`
```solidity
// TODO: I feel like there's a more efficient way to represent the maker:taker ratio
```

The first is misleading (the contract must custody funds itself, not send them directly to Aave as the Aave pool might not be present), and the second is an unresolved `TODO`. Consider removing or clarifying these.

**WannaBet:** Fixed in commit [6bddf7f](https://github.com/gskril/wannabet-v2/commit/6bddf7fc0be929fd10ac731ef87cebba9f7ee686).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-81] Use `Safe ERC20` functions instead of standard ERC20 functions
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Use [SafeERC20](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/utils/SafeERC20.sol) functions `safeTransfer`, `safeTransferFrom`, `forceApprove` etc instead of standard ERC20 functions to ensure support for ERC20 tokens with non-standard behavior:
```solidity
Bet.sol
63:        IERC20(initialBet.asset).transferFrom(
71:            IERC20(initialBet.asset).approve(pool, type(uint256).max);
114:        IERC20(b.asset).transferFrom(msg.sender, address(this), b.takerStake);
150:        IERC20(b.asset).transfer(winner, totalWinnings);
155:            IERC20(b.asset).transfer(_treasury, remainder);
193:        try IERC20(b.asset).transfer(b.maker, makerRefund) {} catch {}
194:        try IERC20(b.asset).transfer(b.taker, takerRefund) {} catch {}
```

**WannaBet:** Fixed in commit [b571b26](https://github.com/gskril/wannabet-v2/commit/b571b26b093d20ab5d876fa0f8845671e1b6e80b).

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->
