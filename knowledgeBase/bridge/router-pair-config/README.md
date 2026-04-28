# bridge/router-pair-config - Issues

- Count: 10

## F-2026-15975 - transferOwnership Does Not Update PrivilegedExemptions and Router Allowances After Ownership Transfer
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, ownership transfer updates only the stored owner addressand does not migrate owner-specific privileges to the new owner orrevoke them from the previous one. As a result, the previous owner retainstax, transaction-limit, and liquidity-creator exemptions, while the newowner does not automatically receive the same operational privileges. Therouter allowance granted to the previous owner also remains unchangedafter the transfer. In KnoxNet, the constructor assigns several owner-specific privileges andapprovals: `_allowances`[`owner()`][routerAddress] = `type(uint256)`.max; isTaxExempt[`owner()`] = true; isLiquidityCreator[`owner()`] = true; isTxLimitExempt[`owner()`] = true; However, ownership transfer only updates `_owner`: function `transferOwnership(address newOwner)` public virtual onlyOwner { require(newOwner != `address(0)`, "Ownable: new owner is the zero address"); `_transferOwnership`(newOwner); } function `_transferOwnership`(address newOwner) internal virtual { address oldOwner = `_owner`; `_owner` = newOwner; emit `OwnershipTransferred(oldOwner, newOwner)`; } No state migration is performed for isTaxExempt, isLiquidityCreator, isTxLimitExempt, or `_allowances`[`owner()`][routerAddress]. The previous ownertherefore remains privileged under these mappings, and the new ownermust be configured manually through separate transactions. The effective privilege model diverges from the recorded ownership stateafter transferOwnership. The previous owner may retain special transferbehavior and liquidity-related privileges, while the new owner may beunable to operate under the same assumptions until additional manualconfiguration is performed. 32 Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
Owner-specific exemptions and approvals should be migrated duringownership transfer. The old ownerʼs privileges should be revoked, and thenew owner should receive the required exemptions and router allowanceatomically. Resolution: Fixed in c20e980: In KnoxNet, ownership transfer now migrates owner-specific privilegesand approvals atomically. The overridden `_transferOwnership` functionrevokes tax, liquidity-creator, transaction-limit, and wallet-limit exemptionsfrom the previous owner, clears the previous ownerʼs router allowance,and assigns the same privileges and approval to the new owner. The priormismatch between recorded ownership and effective privileged state istherefore resolved. function `_transferOwnership`(address newOwner) internal override { address oldOwner = `owner()`; if (oldOwner != `address(0)`) { isTaxExempt[oldOwner] = false; isLiquidityCreator[oldOwner] = false; isTxLimitExempt[oldOwner] = false; isWalletLimitExempt[oldOwner] = false; `_allowances`[oldOwner][routerAddress] = 0; } super.`_transferOwnership`(newOwner); if (newOwner != `address(0)`) { isTaxExempt[newOwner] = true; isLiquidityCreator[newOwner] = true; 33 isTxLimitExempt[newOwner] = true; isWalletLimitExempt[newOwner] = true; `_allowances`[newOwner][routerAddress] = `type(uint256)`.max; } } 34

### 修補方式（實際）
Fixed in c20e980: In KnoxNet, ownership transfer now migrates owner-specific privilegesand approvals atomically. The overridden `_transferOwnership` functionrevokes tax, liquidity-creator, transaction-limit, and wallet-limit exemptionsfrom the previous owner, clears the previous ownerʼs router allowance,and assigns the same privileges and approval to the new owner. The priormismatch between recorded ownership and effective privileged state istherefore resolved. function `_transferOwnership`(address newOwner) internal override { address oldOwner = `owner()`; if (oldOwner != `address(0)`) { isTaxExempt[oldOwner] = false; isLiquidityCreator[oldOwner] = false; isTxLimitExempt[oldOwner] = false; isWalletLimitExempt[oldOwner] = false; `_allowances`[oldOwner][routerAddress] = 0; } super.`_transferOwnership`(newOwner); if (newOwner != `address(0)`) { isTaxExempt[newOwner] = true; isLiquidityCreator[newOwner] = true; 33 isTxLimitExempt[newOwner] = true; isWalletLimitExempt[newOwner] = true; `_allowances`[newOwner][routerAddress] = `type(uint256)`.max; } } 34

## F-2026-14988 - pancakeRouter and pancakePair Initialization Can BeSkipped in Constructor With No Recovery Mechanism
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
During the `NTE` contract deployment, the `_pancakeRouter` address isprovided via the constructor and is expected to be used to create theprimary liquidity pair (`NTE`/`WBNB`), with the resulting pair address stored in pancakePair. However, the constructor explicitly allows `_pancakeRouter` to bethe zero address. As a result, it is possible to deploy the contract with `_pancakeRouter` == `address(0)`. In this scenario, the deployment succeeds, but both pancakeRouter and pancakePair remain permanently set to zero addresses, asthe router and pair initialization logic is intentionally skipped. constructor( uint256 initialSupply, address initialOwner, address `_treasury`, address `_pancakeRouter` ) { … if (`_pancakeRouter` != `address(0)`) { if (!`_isContract`(`_pancakeRouter`)) revert `DEX_ROUTER`(); try IPancakeRouter(`_pancakeRouter`).`factory()` returns (address factory) { if (factory == `address(0)`) revert `DEX_FACTORY_ZERO`(); if (!`_isContract`(factory)) revert `DEX_FACTORY`(); try IPancakeRouter(`_pancakeRouter`).`WETH`() returns (address weth) { if (weth == `address(0)`) revert `DEX_WETH_ZERO`(); if (!`_isContract`(weth)) revert `DEX_WETH`(); try `IPancakeFactory(factory)`.`getPair(address(this)`, weth) returns (address existingPair) { if (existingPair != `address(0)`) { pancakePair = existingPair; isPancakePair[pancakePair] = true; } else { address newPair = `IPancakeFactory(factory)`.`createPair(add ress(this)`, weth); if (newPair == `address(0)`) revert `DEX_PAIR_ZERO`(); pancakePair = newPair; } 18 if (pancakePair == `address(0)`) revert `DEX_PAIR_FAIL`(); pancakeRouter = `_pancakeRouter`; // Router is `NOT` tax exempt to prevent arbitrage through dire ct router calls } catch { revert `DEX_PAIR_CHECK`(); } } catch { revert `DEX_WETH_CALL`(); } } catch { revert `DEX_FACTORY_CALL`(); } The `NTE` contract does not expose any setter functions to update pancakeRouter or pancakePair after deployment. Consequently, if thesevalues are not correctly initialized in the constructor, there is no way torecover or fix the configuration without redeploying the contract. These variables are required for certain runtime validations, includingchecks related to priceImpactLimitEnabled. If they remain unset, thecorresponding logic becomes ineffective. This can lead to: Any functionality depending on pancakeRouter or pancakePair `variables(e.g. price impact validation)` will not operate as intended.The contract may silently bypass or disable documented protections.The only remediation is redeployment, which can cause operationaldisruption, user confusion, and unnecessary proliferation of contractinstances. While this issue does not directly lead to fund loss, it can undermine coretoken mechanics and protocol guarantees. Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Consider one of the following approaches: Enforce a non-zero `_pancakeRouter` address in the constructor byreverting on zero address input.Alternatively, introduce controlled setter functions for pancakeRouter and pancakePair, protected by appropriate access control, to allow post-deployment configuration. Either approach would ensure that the contract can always be configuredto support its documented functionality and reduce the risk of irreversiblemisconfiguration at deployment time. Resolution: Fixed in 0fed2ea, the additional setter for pancakeRouter and pancakePair wasadded to setup this value after the contract deployment - `setPancakeRouter()` and `setPancakePair()`. 20

### 修補方式（實際）
Fixed in 0fed2ea, the additional setter for pancakeRouter and pancakePair wasadded to setup this value after the contract deployment - `setPancakeRouter()` and `setPancakePair()`. 20

## F-2026-15004 - Hardcoded Primary Pair In _calculatePriceImpact()Leads To Price Impact Limit Bypass On Secondary DEX Pairs
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
The `NTE` contract enforces a price impact limit on sells to prevent largetrades from crashing the token price. When enabled, any transfer to aregistered `DEX` pair must pass through `_calculatePriceImpact`(), whichestimates the expected price movement and reverts with `PRICE_TOO_HIGH`() ifit exceeds maxPriceImpactPercent (default 500 bps / 5% . The contract supports multiple `DEX` pairs. The owner registers secondarypairs (e.g., `NTE`/`USDT`) through `setDexPairStatus()`, which sets isPancakePair[pair] = true. The sell detection logic at line 1840 correctlyuses this mapping to identify sells to any registered pair: bool isToPair = isPancakePair[to]; The price impact gate at line 1855 then triggers for all such sells: if (priceImpactLimitEnabled && isToPair && !priceImpactExempt[from] && pancak eRouter != `address(0)`) { uint256 priceImpact = `_calculatePriceImpact`(amount); if (priceImpact > maxPriceImpactPercent) revert `PRICE_TOO_HIGH`(); } However, `_calculatePriceImpact`() at line 1961 always reads reserves fromthe hardcoded primary pair (pancakePair), not from the actual destination: (uint256 reserve0, uint256 reserve1,) = `IPancakePair(pancakePair)`.getReserves (); The destination pair address is never passed to the function. This means asell routed to a shallow secondary pair (e.g., 100,000 `NTE` liquidity) isevaluated against the deep primary pair (e.g., 10,000,000 `NTE` liquidity),underestimating the real impact by the ratio between the two reserves. Regardless of whether the intended design is to protect only the primarypair or all registered pairs, the current behavior represents a requirementviolation. The price impact check fires on sells to every registered pair butevaluates against only the primary pair reserves. No special or unlikelyowner configuration is required to reach this state — it occurs undernormal operation whenever priceImpactLimitEnabled is true and a secondarypair has been registered via `setDexPairStatus()`, both of which are standardadministrative actions documented in the contract. 21 Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Modify `_calculatePriceImpact`() to accept the destination pair address asa parameter and read reserves from that pair. The call would become `_calculatePriceImpact`(amount, to).Consider restricting the price impact check to the primary pair only byreplacing isToPair with to == pancakePair. This removes false protectionon secondary pairs but ensures the check is accurate where it applies. Resolution: Fixed in a5b8fec. The `_calculatePriceImpact`() function now accepts anadditional pancakePair parameter, which is used to perform the requiredpair-specific price impact validation.

### 修補方式（實際）
Fixed in a5b8fec. The `_calculatePriceImpact`() function now accepts anadditional pancakePair parameter, which is used to perform the requiredpair-specific price impact validation.

## F-2025-13503 - Native Balance Sweep via Absolute Balance onNATIVE Legs - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
swap() wraps the user’s msg.value into WETH immediately, but _executeSwap later sources per-route input for NATIVE legs from thecontract’s raw ETH balance: // swap(): wraps user ETH to WETH first if (params.tokenIn == NATIVE) { IWETH(WRAPPED_NATIVE).deposit{value: msg.value}(); } // _executeSwap(): per-route input is taken from absolute balances uint256 tokenInBalance = routeTokenIn == NATIVE ? address(this).balance // <— uses raw ETH on the con tract : IERC20(routeTokenIn).balanceOf(address(this)); uint256 routeAmountIn = (tokenInBalance * route.weight) / remainingWeight; If the contract already holds any ETH (e.g., prior native payouts,accidental transfers, owner funding), a malicious caller can: 1. ensure there is ETH on the contract (or wait until there is),2. call swap with tokenIn = NATIVE and tiny amountIn (e.g., 1 wei),3. use a route that sends native ETH (e.g., Kuru with isNativeSend[0] == true). Because tokenInBalance for NATIVE reads address(this).balance, the route’s amountIn becomes the entire ETH already on the contract, notthe user’s 1 wei. In _swapKuruOrderbook, that amountIn is forwarded as msg.value: if (isNativeSend.length > 0 && isNativeSend[0]) { IKuruRouter(ro

### 修補方式（實際）
The Finding was ﬁxed in commit 4688ddad by adding proper snapshotmechanics for initial balances of the route tokens. (bool hasSnapshot, uint256 snapshot) = _findTokenInSnapshot( uniqueTokensIn, tokenInSnapshots, uniqueTokenInCount, tokenTo Find ); if (!hasSnapshot) { // Failsafe: should never happen after pre-scan, but use curr entBalance as snapshot // This means tokenInBalance will be 0 for this route, preven ting unexpected behavior snapshot = currentBalance; tokenInSnapshots[uniqueTokenInCount] = snapshot; uniqueTokensIn[uniqueTokenInCount] = tokenToFind; unchecked {++uniqueTokenInCount;} } uint256 tokenInBalance = currentBalance - snapshot; Evidences POC 15


## F-2025-13529 - Missing Check for Residual Input Tokens WhenRoute Weights Are Incomplete - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The CoreAggregator._executeSwap function splits a swap across multipleroutes based on their weight. Each route consumes a proportionalamount of the total amountIn. However, there is no ﬁnal validation toensure all input tokens have been properly routed and utilized. This creates a problematic scenario: If routes are given with insuﬃcient cumulative weight (e.g.,weights summing to much less than 10000), the leftover tokensare not returned, refunded, or reverted.Those leftover tokens remain locked in the contract, as no pathexists to claim or automatically handle them.This violates the principle of least surprise: a user expects thefull amountIn to be either swapped or the transaction to fail. uint256 remainingWeight = MAX_WEIGHT; for (uint256 i = 0; i < params.routes.length;) { ... if (remainingWeight == 0) revert InvalidRoutes(); if (route.weight == 0) { unchecked { ++i; } continue; } if (route.weight > remainingWeight) revert InvalidRoutes(); uint256 tokenInBalance = routeTokenIn == NATIVE ? address(this).balance : IERC20(route TokenIn).balanceOf(address(this)); uint256 routeAmountIn = (tokenInBalance * route.weight) / remaini ngWeight; unchecked { remainingWeight -= route.weight;

### 修補方式（實際）
The Finding was ﬁxed in commit 39b76a13 by adding if (weightSum != MAX_WEIGHT) revert WeightNotFullyAllocated(); this if statement after the routes loop. Evidences POC


## F-2025-13548 - Improper Weight Reset on tokenIn Change AllowsBypassing MAX_WEIGHT Cap - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The _executeSwap() function in CoreAggregator is intended to limit thetotal route weight to MAX_WEIGHT = 10,000 per contiguous sequence ofroutes using the same tokenIn. This is enforced through the remainingWeight variable. However, there is a subtle and exploitable ﬂaw in the logic: if (routeTokenIn != currentTokenIn) { currentTokenIn = routeTokenIn; remainingWeight = MAX_WEIGHT; } This block resets the remainingWeight back to 10,000 whenever theinput token changes. While this might be intended for legitimatecases of token chaining (e.g., WETH → USDC → DAI), it opens up a bypass. A malicious user can oscillate tokenIn values between routes toreset the weight allowance repeatedly. This leads tounbounded weight usage across multiple routes, far exceedingthe intended 100% (MAX_WEIGHT), causing the aggregator to use moretokens than the user expected or authorized.

### 修補方式（實際）
The Finding was ﬁxed in commit d2cb1962 by adding _validateTokenInGrouping control under the _executeSwap function. function _validateTokenInGrouping(address[] memory seenTokensIn, uint256 seenCount, address newTokenIn) private pure { for (uint256 i; i < seenCount;) { if (seenTokensIn[i] == newTokenIn) revert TokenInNotGrouped(); unchecked {++i;} } } Evidences


## F-2025-13566 - Weights Misapplied When Routes Are NotGrouped By TokenIn - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
In the _executeSwap functionhe splitter renormalizes weights everytime tokenIn changes, eﬀectively creating separate “weight blocks.”If routes with the same tokenIn are interleaved, their shares arecomputed in multiple blocks, so allocations become order-dependentand can diverge from intended global proportions. . if (routeTokenIn != currentTokenIn) { currentTokenIn = routeTokenIn; remainingWeight = MAX_WEIGHT; } Blocks can also leave unused balances when per-block weights sumto less than MAX_WEIGHT. Per contiguous tokenIn segment, weights are normalized to thesegment’s remainingWeight (starting at MAX_WEIGHT), using the livebalance at each step. Re-encountering the same tokenIn later opensa new block with fresh normalization. Example (deviation from plan): Input A = 1000, MAX_WEIGHT=10000Routes: A(5000), B(...), A(5000)First A block: 1000*5000/10000 = 500Second A block (after B): remaining A ≈ 500 → 500*5000/10000= 250Total A used = 750 (not 1000 as a 50%+50% plan wouldsuggest) This leads to under/over-allocation versus planner intent; residualbalances when per-block weights < MAX_WEIGHT.

### 修補方式（實際）
The Finding is ﬁxed in commit 1532bc2. The tokens grouping wasenforced. _validateTokenInGrouping(seenTokensIn, seenCount, routeTokenIn); seenTokensIn[seenCount] = currentTokenIn; unchecked {++seenCount;} Evidences


## F-2025-13594 - ZkSwap Router Mismatch: Calls Non-ExistentexactInputSingle On Monad - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The adapter assumes a Uniswap V3-style SwapRouter with exactInputSingle, but zkSwap on Monad exposes a Universal/Smartrouter, not a standalone V3 SwapRouter. The current code targets a function that is not deployed, causingruntime failures. IZkSwapV3Router(router).exactInputSingle(swapParams); Route execution reverts on Monad; zkSwap path is unusable (DoS forthat router type).

### 修補方式（實際）
The Finding was ﬁxed in commit 408c3d8. The router was switched tozkSwap’s Universal Router ABI: IUniversalRouter(router).execute(commands, inputs, deadline); 31 Evidences


## F-2025-8551 - Rounding Issue in ﬁllOrder and partiallyFillOrderAllows Free Token Transfer - Medium
- 嚴重度：Medium
- Report source：EverValue Coin.pdf

### 問題內容（摘要）
The fillOrder() and partiallyFillOrder() functions in PairLib.sol suﬀerfrom an integer division rounding issue when calculating takerSendAmount (the amount of quote tokens the taker needs totransfer). Solidity uses integer division, meaning that when performing thecalculation: takerSendAmount = matchedOrder.availableQuantity * matchedOrder.price / PRECI SION; If (matchedOrder.availableQuantity * matchedOrder.price) is less than PRECISION, the result will be truncated to zero due to integer division,allowing the order to be executed without transferring anyquote tokens. This enables an attacker to receive base tokens without payingfor them by deliberately placing orders at small quantities and lowprices where rounding errors occur.

### 修補方式（實際）
The EverValue Coin team introduced necessary checks to ﬁx theissue. When takerSendAmount or takerReceiveAmount is zero, the fillOrder() function now reverts, and the partiallyFillOrder() function skips orderﬁlling and ﬁnalizes the taker's order. Lastly, the addOrder() functionreverts when takerSendAmount is zero (Revised commit: ef39ea0). 20


## F-2025-8721 - Exploitable Order Quantity Leading to Fund Loss -High
- 嚴重度：High
- Report source：EverValue Coin.pdf

### 問題內容（摘要）
A vulnerability in the order book logic allows an attacker to exploitmismatches in order fulﬁllment, leading to fund theft or permanentfund freezing. The core issue arises because the availableQuantity of acompletely fulﬁlled or a partially fulﬁlled order is not updated,leading to inconsistencies in order cancellation and fulﬁllment byother takers. When an order is partially or fully matched, only the quantity ﬁeld isupdated, while the availableQuantity remains unchanged. Thisdiscrepancy allows an attacker to manipulate the system by eithercanceling the order and reclaiming excess funds or having anothertrader fulﬁll the order again for an amount greater than whatremains. The vulnerability originates from the matchOrder() function: if (newOrder.quantity >= matchingOrder.availableQuantity) { fillOrder(pair, matchingOrder, newOrder); } else { partiallyFillOrder(pair, matchingOrder, newOrder); return (newOrder.quantity, orderCount); } The fillOrder function correctly deducts quantity, but availableQuantity is not updated: takerOrder.quantity -= matchedOrder.availableQuantity; This issue persists when the remaining order is stored back into thequeue: if (_quantity > 0) { addOrder(pair,

### 修補方式（實際）
The EverValue Coin team ﬁxed the issue by updating the availableQuantity in order ﬁlling functions.(Revised commit: 1516471) Evidences PoC

