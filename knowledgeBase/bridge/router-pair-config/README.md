# bridge/router-pair-config - Issues

- Count: 10

## F-2026-15975 - transfer Ownership Does Not Update Privileged Exemptions and Router Allowances After Ownership Transfer
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, ownership transfer updates only the stored owner addressand does not migrate owner-specific privileges to the new owner orrevoke them from the previous one. As a result, the previous owner retainstax, transaction-limit, and liquidity-creator exemptions, while the newowner does not automatically receive the same operational privileges. Therouter allowance granted to the previous owner also remains unchangedafter the transfer. In KnoxNet, the constructor assigns several owner-specific privileges andapprovals: `_allowances`[`owner()`][routerAddress] = `type(uint256)`.max; isTaxExempt[`owner()`] = true; isLiquidityCreator[`owner()`] = true; isTxLimitExempt[`owner()`] = true; However, ownership transfer only updates `_owner`: function `transferOwnership(address newOwner)` public virtual onlyOwner { require(newOwner != `address(0)`, "Ownable: new owner is the zero address"); `_transferOwnership`(newOwner); } function `_transferOwnership`(address newOwner) internal virtual { address oldOwner = `_owner`; `_owner` = newOwner; emit `OwnershipTransferred(oldOwner, newOwner)`; } No state migration is performed for isTaxExempt, isLiquidityCreator, isTxLimitExempt, or `_allowances`[`owner()`][routerAddress]. The previous ownertherefore remains privileged under these mappings, and the new ownermust be configured manually through separate transactions. The effective privilege model diverges from the recorded ownership stateafter transferOwnership. The previous owner may retain special transferbehavior and liquidity-related privileges, while the new owner may beunable to operate under the same assumptions until additional manualconfiguration is performed. 32 Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
Owner-specific exemptions and approvals should be migrated duringownership transfer. The old ownerʼs privileges should be revoked, and thenew owner should receive the required exemptions and router allowanceatomically. Resolution: Fixed in c20e980: In KnoxNet, ownership transfer now migrates owner-specific privilegesand approvals atomically. The overridden `_transferOwnership` functionrevokes tax, liquidity-creator, transaction-limit, and wallet-limit exemptionsfrom the previous owner, clears the previous ownerʼs router allowance,and assigns the same privileges and approval to the new owner. The priormismatch between recorded ownership and effective privileged state istherefore resolved. function `_transferOwnership`(address newOwner) internal override { address oldOwner = `owner()`; if (oldOwner != `address(0)`) { isTaxExempt[oldOwner] = false; isLiquidityCreator[oldOwner] = false; isTxLimitExempt[oldOwner] = false; isWalletLimitExempt[oldOwner] = false; `_allowances`[oldOwner][routerAddress] = 0; } super.`_transferOwnership`(newOwner); if (newOwner != `address(0)`) { isTaxExempt[newOwner] = true; isLiquidityCreator[newOwner] = true; 33 isTxLimitExempt[newOwner] = true; isWalletLimitExempt[newOwner] = true; `_allowances`[newOwner][routerAddress] = `type(uint256)`.max; } } 34

### 修補方式（實際）
Fixed in c20e980: In KnoxNet, ownership transfer now migrates owner-specific privilegesand approvals atomically. The overridden `_transferOwnership` functionrevokes tax, liquidity-creator, transaction-limit, and wallet-limit exemptionsfrom the previous owner, clears the previous ownerʼs router allowance,and assigns the same privileges and approval to the new owner. The priormismatch between recorded ownership and effective privileged state istherefore resolved. function `_transferOwnership`(address newOwner) internal override { address oldOwner = `owner()`; if (oldOwner != `address(0)`) { isTaxExempt[oldOwner] = false; isLiquidityCreator[oldOwner] = false; isTxLimitExempt[oldOwner] = false; isWalletLimitExempt[oldOwner] = false; `_allowances`[oldOwner][routerAddress] = 0; } super.`_transferOwnership`(newOwner); if (newOwner != `address(0)`) { isTaxExempt[newOwner] = true; isLiquidityCreator[newOwner] = true; 33 isTxLimitExempt[newOwner] = true; isWalletLimitExempt[newOwner] = true; `_allowances`[newOwner][routerAddress] = `type(uint256)`.max; } } 34

## F-2026-14988 - pancake Router and pancake Pair Initialization Can Be Skipped in Constructor With No Recovery Mechanism
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
During the `NTE` contract deployment, the `_pancakeRouter` address isprovided via the constructor and is expected to be used to create theprimary liquidity pair (`NTE`/`WBNB`), with the resulting pair address stored in pancakePair. However, the constructor explicitly allows `_pancakeRouter` to bethe zero address. As a result, it is possible to deploy the contract with `_pancakeRouter` == `address(0)`. In this scenario, the deployment succeeds, but both pancakeRouter and pancakePair remain permanently set to zero addresses, asthe router and pair initialization logic is intentionally skipped. constructor( uint256 initialSupply, address initialOwner, address `_treasury`, address `_pancakeRouter` ) { … if (`_pancakeRouter` != `address(0)`) { if (!`_isContract`(`_pancakeRouter`)) revert `DEX_ROUTER`(); try IPancakeRouter(`_pancakeRouter`).`factory()` returns (address factory) { if (factory == `address(0)`) revert `DEX_FACTORY_ZERO`(); if (!`_isContract`(factory)) revert `DEX_FACTORY`(); try IPancakeRouter(`_pancakeRouter`).`WETH`() returns (address weth) { if (weth == `address(0)`) revert `DEX_WETH_ZERO`(); if (!`_isContract`(weth)) revert `DEX_WETH`(); try `IPancakeFactory(factory)`.`getPair(address(this)`, weth) returns (address existingPair) { if (existingPair != `address(0)`) { pancakePair = existingPair; isPancakePair[pancakePair] = true; } else { address newPair = `IPancakeFactory(factory)`.`createPair(add ress(this)`, weth); if (newPair == `address(0)`) revert `DEX_PAIR_ZERO`(); pancakePair = newPair; } 18 if (pancakePair == `address(0)`) revert `DEX_PAIR_FAIL`(); pancakeRouter = `_pancakeRouter`; // Router is `NOT` tax exempt to prevent arbitrage through dire ct router calls } catch { revert `DEX_PAIR_CHECK`(); } } catch { revert `DEX_WETH_CALL`(); } } catch { revert `DEX_FACTORY_CALL`(); } The `NTE` contract does not expose any setter functions to update pancakeRouter or pancakePair after deployment. Consequently, if thesevalues are not correctly initialized in the constructor, there is no way torecover or fix the configuration without redeploying the contract. These variables are required for certain runtime validations, includingchecks related to priceImpactLimitEnabled. If they remain unset, thecorresponding logic becomes ineffective. This can lead to: Any functionality depending on pancakeRouter or pancakePair `variables(e.g. price impact validation)` will not operate as intended.The contract may silently bypass or disable documented protections.The only remediation is redeployment, which can cause operationaldisruption, user confusion, and unnecessary proliferation of contractinstances. While this issue does not directly lead to fund loss, it can undermine coretoken mechanics and protocol guarantees. Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Consider one of the following approaches: Enforce a non-zero `_pancakeRouter` address in the constructor byreverting on zero address input.Alternatively, introduce controlled setter functions for pancakeRouter and pancakePair, protected by appropriate access control, to allow post-deployment configuration. Either approach would ensure that the contract can always be configuredto support its documented functionality and reduce the risk of irreversiblemisconfiguration at deployment time. Resolution: Fixed in 0fed2ea, the additional setter for pancakeRouter and pancakePair wasadded to setup this value after the contract deployment - `setPancakeRouter()` and `setPancakePair()`. 20

### 修補方式（實際）
Fixed in 0fed2ea, the additional setter for pancakeRouter and pancakePair wasadded to setup this value after the contract deployment - `setPancakeRouter()` and `setPancakePair()`. 20

## F-2026-15004 - Hardcoded Primary Pair In _calculate Price Impact()Leads To Price Impact Limit Bypass On Secondary DEX Pairs
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
The `NTE` contract enforces a price impact limit on sells to prevent largetrades from crashing the token price. When enabled, any transfer to aregistered `DEX` pair must pass through `_calculatePriceImpact`(), whichestimates the expected price movement and reverts with `PRICE_TOO_HIGH`() ifit exceeds maxPriceImpactPercent (default 500 bps / 5% . The contract supports multiple `DEX` pairs. The owner registers secondarypairs (e.g., `NTE`/`USDT`) through `setDexPairStatus()`, which sets isPancakePair[pair] = true. The sell detection logic at line 1840 correctlyuses this mapping to identify sells to any registered pair: bool isToPair = isPancakePair[to]; The price impact gate at line 1855 then triggers for all such sells: if (priceImpactLimitEnabled && isToPair && !priceImpactExempt[from] && pancak eRouter != `address(0)`) { uint256 priceImpact = `_calculatePriceImpact`(amount); if (priceImpact > maxPriceImpactPercent) revert `PRICE_TOO_HIGH`(); } However, `_calculatePriceImpact`() at line 1961 always reads reserves fromthe hardcoded primary pair (pancakePair), not from the actual destination: (uint256 reserve0, uint256 reserve1,) = `IPancakePair(pancakePair)`.getReserves (); The destination pair address is never passed to the function. This means asell routed to a shallow secondary pair (e.g., 100,000 `NTE` liquidity) isevaluated against the deep primary pair (e.g., 10,000,000 `NTE` liquidity),underestimating the real impact by the ratio between the two reserves. Regardless of whether the intended design is to protect only the primarypair or all registered pairs, the current behavior represents a requirementviolation. The price impact check fires on sells to every registered pair butevaluates against only the primary pair reserves. No special or unlikelyowner configuration is required to reach this state — it occurs undernormal operation whenever priceImpactLimitEnabled is true and a secondarypair has been registered via `setDexPairStatus()`, both of which are standardadministrative actions documented in the contract. 21 Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Modify `_calculatePriceImpact`() to accept the destination pair address asa parameter and read reserves from that pair. The call would become `_calculatePriceImpact`(amount, to).Consider restricting the price impact check to the primary pair only byreplacing isToPair with to == pancakePair. This removes false protectionon secondary pairs but ensures the check is accurate where it applies. Resolution: Fixed in a5b8fec. The `_calculatePriceImpact`() function now accepts anadditional pancakePair parameter, which is used to perform the requiredpair-specific price impact validation.

### 修補方式（實際）
Fixed in a5b8fec. The `_calculatePriceImpact`() function now accepts anadditional pancakePair parameter, which is used to perform the requiredpair-specific price impact validation.

## F-2025-13503 - Native Balance Sweep via Absolute Balance on NATIVE Legs - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
swap() wraps the user’s msg.value into WETH immediately, but _executeSwap later sources per-route input for NATIVE legs from thecontract’s raw ETH balance: // swap(): wraps user ETH to WETH first if (params.tokenIn == NATIVE) { IWETH(WRAPPED_NATIVE).deposit{value: msg.value}(); } // _executeSwap(): per-route input is taken from absolute balances uint256 tokenInBalance = routeTokenIn == NATIVE ? address(this).balance // <— uses raw ETH on the con tract : IERC20(routeTokenIn).balanceOf(address(this)); uint256 routeAmountIn = (tokenInBalance * route.weight) / remainingWeight; If the contract already holds any ETH (e.g., prior native payouts,accidental transfers, owner funding), a malicious caller can: 1. ensure there is ETH on the contract (or wait until there is),2. call swap with tokenIn = NATIVE and tiny amountIn (e.g., 1 wei),3. use a route that sends native ETH (e.g., Kuru with isNativeSend[0] == true). Because tokenInBalance for NATIVE reads address(this).balance, the route’s amountIn becomes the entire ETH already on the contract, notthe user’s 1 wei. In _swapKuruOrderbook, that amountIn is forwarded as msg.value: if (isNativeSend.length > 0 && isNativeSend[0]) { IKuruRouter(ro

### 修補方式（實際）
The Finding was ﬁxed in commit 4688ddad by adding proper snapshotmechanics for initial balances of the route tokens. (bool hasSnapshot, uint256 snapshot) = _findTokenInSnapshot( uniqueTokensIn, tokenInSnapshots, uniqueTokenInCount, tokenTo Find ); if (!hasSnapshot) { // Failsafe: should never happen after pre-scan, but use curr entBalance as snapshot // This means tokenInBalance will be 0 for this route, preven ting unexpected behavior snapshot = currentBalance; tokenInSnapshots[uniqueTokenInCount] = snapshot; uniqueTokensIn[uniqueTokenInCount] = tokenToFind; unchecked {++uniqueTokenInCount;} } uint256 tokenInBalance = currentBalance - snapshot; Evidences POC 15


## F-2025-13529 - Missing Check for Residual Input Tokens When Route Weights Are Incomplete - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The CoreAggregator._executeSwap function splits a swap across multipleroutes based on their weight. Each route consumes a proportionalamount of the total amountIn. However, there is no ﬁnal validation toensure all input tokens have been properly routed and utilized. This creates a problematic scenario: If routes are given with insuﬃcient cumulative weight (e.g.,weights summing to much less than 10000), the leftover tokensare not returned, refunded, or reverted.Those leftover tokens remain locked in the contract, as no pathexists to claim or automatically handle them.This violates the principle of least surprise: a user expects thefull amountIn to be either swapped or the transaction to fail. uint256 remainingWeight = MAX_WEIGHT; for (uint256 i = 0; i < params.routes.length;) { ... if (remainingWeight == 0) revert InvalidRoutes(); if (route.weight == 0) { unchecked { ++i; } continue; } if (route.weight > remainingWeight) revert InvalidRoutes(); uint256 tokenInBalance = routeTokenIn == NATIVE ? address(this).balance : IERC20(route TokenIn).balanceOf(address(this)); uint256 routeAmountIn = (tokenInBalance * route.weight) / remaini ngWeight; unchecked { remainingWeight -= route.weight;

### 修補方式（實際）
The Finding was ﬁxed in commit 39b76a13 by adding if (weightSum != MAX_WEIGHT) revert WeightNotFullyAllocated(); this if statement after the routes loop. Evidences POC


## F-2025-13548 - Improper Weight Reset on token In Change Allows Bypassing MAX_WEIGHT Cap - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The _executeSwap() function in CoreAggregator is intended to limit thetotal route weight to MAX_WEIGHT = 10,000 per contiguous sequence ofroutes using the same tokenIn. This is enforced through the remainingWeight variable. However, there is a subtle and exploitable ﬂaw in the logic: if (routeTokenIn != currentTokenIn) { currentTokenIn = routeTokenIn; remainingWeight = MAX_WEIGHT; } This block resets the remainingWeight back to 10,000 whenever theinput token changes. While this might be intended for legitimatecases of token chaining (e.g., WETH → USDC → DAI), it opens up a bypass. A malicious user can oscillate tokenIn values between routes toreset the weight allowance repeatedly. This leads tounbounded weight usage across multiple routes, far exceedingthe intended 100% (MAX_WEIGHT), causing the aggregator to use moretokens than the user expected or authorized.

### 修補方式（實際）
The Finding was ﬁxed in commit d2cb1962 by adding _validateTokenInGrouping control under the _executeSwap function. function _validateTokenInGrouping(address[] memory seenTokensIn, uint256 seenCount, address newTokenIn) private pure { for (uint256 i; i < seenCount;) { if (seenTokensIn[i] == newTokenIn) revert TokenInNotGrouped(); unchecked {++i;} } } Evidences


## F-2025-13566 - Weights Misapplied When Routes Are Not Grouped By Token In - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
In the _executeSwap functionhe splitter renormalizes weights everytime tokenIn changes, eﬀectively creating separate “weight blocks.”If routes with the same tokenIn are interleaved, their shares arecomputed in multiple blocks, so allocations become order-dependentand can diverge from intended global proportions. . if (routeTokenIn != currentTokenIn) { currentTokenIn = routeTokenIn; remainingWeight = MAX_WEIGHT; } Blocks can also leave unused balances when per-block weights sumto less than MAX_WEIGHT. Per contiguous tokenIn segment, weights are normalized to thesegment’s remainingWeight (starting at MAX_WEIGHT), using the livebalance at each step. Re-encountering the same tokenIn later opensa new block with fresh normalization. Example (deviation from plan): Input A = 1000, MAX_WEIGHT=10000Routes: A(5000), B(...), A(5000)First A block: 1000*5000/10000 = 500Second A block (after B): remaining A ≈ 500 → 500*5000/10000= 250Total A used = 750 (not 1000 as a 50%+50% plan wouldsuggest) This leads to under/over-allocation versus planner intent; residualbalances when per-block weights < MAX_WEIGHT.

### 修補方式（實際）
The Finding is ﬁxed in commit 1532bc2. The tokens grouping wasenforced. _validateTokenInGrouping(seenTokensIn, seenCount, routeTokenIn); seenTokensIn[seenCount] = currentTokenIn; unchecked {++seenCount;} Evidences


## F-2025-13594 - Zk Swap Router Mismatch: Calls Non-Existentexact Input Single On Monad - High
- 嚴重度：High
- Report source：Dirol.pdf

### 問題內容（摘要）
The adapter assumes a Uniswap V3-style SwapRouter with exactInputSingle, but zkSwap on Monad exposes a Universal/Smartrouter, not a standalone V3 SwapRouter. The current code targets a function that is not deployed, causingruntime failures. IZkSwapV3Router(router).exactInputSingle(swapParams); Route execution reverts on Monad; zkSwap path is unusable (DoS forthat router type).

### 修補方式（實際）
The Finding was ﬁxed in commit 408c3d8. The router was switched tozkSwap’s Universal Router ABI: IUniversalRouter(router).execute(commands, inputs, deadline); 31 Evidences


## F-2025-8551 - Rounding Issue in ﬁll Order and partially Fill Order Allows Free Token Transfer - Medium
- 嚴重度：Medium
- Report source：EverValue Coin.pdf

### 問題內容（摘要）
The fillOrder() and partiallyFillOrder() functions in PairLib.sol suﬀerfrom an integer division rounding issue when calculating takerSendAmount (the amount of quote tokens the taker needs totransfer). Solidity uses integer division, meaning that when performing thecalculation: takerSendAmount = matchedOrder.availableQuantity * matchedOrder.price / PRECI SION; If (matchedOrder.availableQuantity * matchedOrder.price) is less than PRECISION, the result will be truncated to zero due to integer division,allowing the order to be executed without transferring anyquote tokens. This enables an attacker to receive base tokens without payingfor them by deliberately placing orders at small quantities and lowprices where rounding errors occur.

### 修補方式（實際）
The EverValue Coin team introduced necessary checks to ﬁx theissue. When takerSendAmount or takerReceiveAmount is zero, the fillOrder() function now reverts, and the partiallyFillOrder() function skips orderﬁlling and ﬁnalizes the taker's order. Lastly, the addOrder() functionreverts when takerSendAmount is zero (Revised commit: ef39ea0). 20


## F-2025-8721 - Exploitable Order Quantity Leading to Fund Loss - High
- 嚴重度：High
- Report source：EverValue Coin.pdf

### 問題內容（摘要）
A vulnerability in the order book logic allows an attacker to exploitmismatches in order fulﬁllment, leading to fund theft or permanentfund freezing. The core issue arises because the availableQuantity of acompletely fulﬁlled or a partially fulﬁlled order is not updated,leading to inconsistencies in order cancellation and fulﬁllment byother takers. When an order is partially or fully matched, only the quantity ﬁeld isupdated, while the availableQuantity remains unchanged. Thisdiscrepancy allows an attacker to manipulate the system by eithercanceling the order and reclaiming excess funds or having anothertrader fulﬁll the order again for an amount greater than whatremains. The vulnerability originates from the matchOrder() function: if (newOrder.quantity >= matchingOrder.availableQuantity) { fillOrder(pair, matchingOrder, newOrder); } else { partiallyFillOrder(pair, matchingOrder, newOrder); return (newOrder.quantity, orderCount); } The fillOrder function correctly deducts quantity, but availableQuantity is not updated: takerOrder.quantity -= matchedOrder.availableQuantity; This issue persists when the remaining order is stored back into thequeue: if (_quantity > 0) { addOrder(pair,

### 修補方式（實際）
The EverValue Coin team ﬁxed the issue by updating the availableQuantity in order ﬁlling functions.(Revised commit: 1516471) Evidences PoC

## Cyfrin Fixed Issues (Merged)
- Count: `43`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] Fees never deducted in `Accountable Open Term` loan
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** In `AccountableOpenTerm`, `interestData()` returns non-zero `performanceFee` and `establishmentFee`, but no path ever charges these fees. `_accrueInterest()` only updates `_scaleFactor` for base interest and none of `supply` or `repay` calls `FeeManager` (unlike FixedTerm’s `collect`). As a result, fees are never charged.

**Impact:** Protocol/manager fees are effectively never taken.

**Recommended Mitigation:** Consider charge the fee in `supply()`/`repay()`, before any other state changes. Compute fees for the elapsed period and transfer to `FeeManager`, then proceed.

**Accountable:** Fixed in commits [`fce6961`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/fce6961c71269739ec35da60131eaf63e66e1726) and [`8e53eba`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/8e53eba7340f223f86c9c392f50b8b2d885fdd39)

**Cyfrin:** Verified. `performanceFee` and `establishmentFee` are now deducted for open term loans.

## [M-2] `Tick Iterator::_advance To Next Up` sets uninitialized end tick as the current tick which causes `Tick Iterator::has Next` to return true when this is not actually the case
- Severity: `Medium`
- Source report: `angstrom.md`

### Detailed Content (from source)
**Description:** `TickIterator::hasNext` returns true if there are more ticks to iterate, inclusive if the end tick, while `TickIterator::getNext` returns the next tick and advances the iterator:

```solidity
function hasNext(TickIteratorUp memory self) internal pure returns (bool) {
@>   return self.currentTick <= self.endTick;
}

function getNext(TickIteratorUp memory self) internal view returns (int24 tick) {
    if (!hasNext(self)) revert NoNext();
    tick = self.currentTick;
    _advanceToNextUp(self);
}
```

`TickIterator::_advanceToNextUp` intends to advance the upward tick iterator to the next initialized tick, setting it as the current tick. The do-while loop condition terminates once the end tick is reached; however, this logic incorrectly considers the end tick as the next tick even when it is not initialized:

```solidity
function _advanceToNextUp(TickIteratorUp memory self) private view {
    do {
        (int16 wordPos, uint8 bitPos) =
            TickLib.position(TickLib.compress(self.currentTick, self.tickSpacing) + 1);

        if (bitPos == 0) {
            self.currentWord = self.manager.getPoolBitmapInfo(self.poolId, wordPos);
        }

        bool initialized;
        (initialized, bitPos) = self.currentWord.nextBitPosGte(bitPos);
@>      self.currentTick = TickLib.toTick(wordPos, bitPos, self.tickSpacing);
@>      if (initialized) break;
@>  } while (self.currentTick < self.endTick);
```

Instead, the iterator should marked as exhausted by setting `self.currentTick = type(int24).max` and adding explicit validation within `hasNext()` which should also use an exclusive comparison operator instead.

**Impact:** Based on the below PoC, this does not appear to affect either the effective price calculation or crediting of rewards as all repeated evaluations yield zero and effectively act as a no-op, although this is not a guarantee that such impact does not exist.

**Proof of Concept:** The following tests should be added to `TickIterator.t.sol`:

```solidity
function test_iterateUp_phantomAtTopOfWordBoundary() public view {
    // No liquidity anywhere.

    int24 startTick = 2500;
    int24 endTick = 2550;
    TickIteratorUp memory iter =
        TickIteratorLib.initUp(manager, pid, TICK_SPACING, startTick, endTick);

    // Erroneously returns true - should be false with no initialized ticks up to boundary.
    bool hasNext = iter.hasNext();
    console2.log("iter.hasNext(): %s", hasNext);

    // Returns endTick even though it isn't initialized - should revert with NoNext().
    int24 tick = iter.getNext();
    console2.log("iter.getNext(): %s", tick);
    console2.log("endTick: %s", endTick);

    // Prove the returned tick is not initialized.
    (int16 wordPos, uint8 bitPos) = TickLib.position(TickLib.compress(tick, TICK_SPACING));
    uint256 word = IPoolManager(address(manager)).getPoolBitmapInfo(pid, wordPos);
    console2.log("isInitialized: %s", TickLib.isInitialized(word, bitPos));
}

function test_iterateDown_noPhantomAtBottomOfWordBoundary() public view {
    // No liquidity anywhere.

    int24 startTick = 50;
    int24 endTick = 0;

    TickIteratorDown memory iter =
        TickIteratorLib.initDown(manager, pid, TICK_SPACING, startTick, endTick);

    // Should be exhausted - no initialized ticks in (0, 50].
    assertFalse(iter.hasNext(), "Down iterator has a phantom next tick");
}
```

The following test should be added to `AngstromL2.t.sol` and run with `forge test --mt test_tickIteration --decode-internal -vvvv`:

```solidity
function test_tickIteration() public {
    PoolKey memory key = initializePool(address(token), 10, 2500);
    addLiquidity(key, 2500, 2540, 1e21);
    uint256 PRIORITY_FEE = 0.5 gwei;
    setPriorityFee(PRIORITY_FEE);

    router.swap(key, false, 1000e18, int24(2550).getSqrtPriceAtTick());
}
```

**Recommended Mitigation:** Modify the upward tick iterator functions such that `hasNext()` returns false when there are no further initialized ticks.

**Sorella Labs:** Fixed in commit [0d6d39e](https://github.com/SorellaLabs/l2-angstrom/commit/0d6d39ec7be2d9e151aa47e05a6c0dec4364b2a5).

**Cyfrin:** Verified. The do-while loop is now inclusive of the end tick such that the current tick advances beyond the end and `hasNext()` returns false.

## [M-3] `Myriad CTFExchange::_require Market Open` makes two external calls to `manager`
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `MyriadCTFExchange::_requireMarketOpen` issues two separate external calls to `manager` on every invocation:

```solidity
function _requireMarketOpen(uint256 marketId) internal view {
    require(manager.getMarketState(marketId) == IMyriadMarketManager.MarketState.open, "market closed");
    require(!manager.isMarketPaused(marketId), "market paused");
}
```

Each external call costs at minimum 100 gas (warm) or 2100 gas (cold) for the `CALL` opcode. `_requireMarketOpen` is called once per order in `matchCrossMarketOrders` (N times for an N-outcome event) and once per `_matchOrders` call in the single-market path, making the overhead cumulative.

**Recommended Mitigation:** Add a combined view function to `IMyriadMarketManager` and its implementation:

```solidity
function isMarketTradeable(uint256 marketId) external view returns (bool) {
    Market storage m = markets[marketId];
    return m.state == MarketState.open && !m.paused;
}
```

Then simplify `_requireMarketOpen` to a single external call:

```solidity
function _requireMarketOpen(uint256 marketId) internal view {
    require(manager.isMarketTradeable(marketId), "market not tradeable");
}
```

**Myriad:** Fixed in commit [`b3e2586`](https://github.com/Polkamarkets/polkamarkets-js/commit/b3e2586a797a3c2e2fb388d4ff1a733b2350a36a)

**Cyfrin:** Verified.

## [M-4] `Neg Risk Adapter::create Event` allows different `closes At` across outcome markets
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `NegRiskAdapter::createEvent` iterates over caller-supplied `marketParams` and creates one market per outcome via `manager.createNegRiskMarket`. There is no validation that all `marketParams[i].closesAt` values are identical:

```solidity
for (uint256 i = 0; i < marketParams.length; i++) {
    uint256 marketId = manager.createNegRiskMarket(marketParams[i], IERC20(address(wcol)), eventId);
    evt.marketIds.push(marketId);
}
```

`MyriadCTFExchange::matchCrossMarketOrders` calls `_requireMarketOpen` for every order in the batch. The moment the earliest-closing market transitions to `closed`, any cross-market fill for the event reverts:

```solidity
require(manager.getMarketState(marketId) == MarketState.open, "market closed");
```

Users holding YES positions in the still-open markets lose their primary exit mechanism (cross-market matching) before the event has actually concluded.

**Recommended Mitigation:** Enforce uniform close times in `createEvent`:

```solidity
uint256 closesAt = marketParams[0].closesAt;
for (uint256 i = 1; i < marketParams.length; i++) {
    require(marketParams[i].closesAt == closesAt, "closesAt mismatch");
}
```

**Myriad:** Fixed in commit [`9a77afb`](https://github.com/Polkamarkets/polkamarkets-js/commit/9a77afb38be03035a2cdd2b44393b288188f9c00)

**Cyfrin:** Verified.

## [M-5] Cache repeated storage reads
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** Across the matching functions these variables are accessed far more times than necessary:

| Variable | Function | Reads |
|---|---|---|
| `conditionalTokens` | `_settleMintMatch` | 6 |
| `conditionalTokens` | `_settleMergeMatch` | 5 |
| `conditionalTokens` | `matchCrossMarketOrders` | 2×N (distribution loop) |
| `conditionalTokens` | `_settleDirectMatch` | 2 |
| `manager` | `matchCrossMarketOrders` | 2×N+2 (validation loop + outside) |
| `feeModule` | `matchCrossMarketOrders` | N+2 (fee loop + accrue) |
| `feeModule` | `matchOrdersWithFees` | 3 |
| `negRiskAdapter` | `matchCrossMarketOrders` | 4 |

**Recommended Mitigation:** Cache each variable into a local at the top of every function where it is read more than once:

```solidity
// matchCrossMarketOrders — saves (2N+1) + (N+1) + (2N−1) + 3 SLOADs
IMyriadMarketManager _manager   = manager;
IFeeModule           _feeModule = IFeeModule(feeModule);
ConditionalTokens    _ct        = conditionalTokens;
address              _adapter   = negRiskAdapter;

bytes32 eventId = _manager.getEventId(orders[0].marketId);
// ... use _manager, _feeModule, _ct, _adapter throughout

// _settleMintMatch — saves 5 SLOADs
ConditionalTokens _ct = conditionalTokens;
collateral.forceApprove(address(_ct), fillAmount);
_ct.splitPosition(maker.marketId, fillAmount);
_ct.safeTransferFrom(address(this), outcome0Order.trader, _ct.getTokenId(maker.marketId, 0), fillAmount, "");
_ct.safeTransferFrom(address(this), outcome1Order.trader, _ct.getTokenId(maker.marketId, 1), fillAmount, "");

// _settleMergeMatch — saves 4 SLOADs
ConditionalTokens _ct = conditionalTokens;
uint256 outcome0TokenId = _ct.getTokenId(maker.marketId, 0);
uint256 outcome1TokenId = _ct.getTokenId(maker.marketId, 1);
_ct.safeTransferFrom(...);
_ct.safeTransferFrom(...);
_ct.mergePositions(...);
```

**Myriad:** Fixed in commit [`5870aa4`](https://github.com/Polkamarkets/polkamarkets-js/commit/5870aa42a6177978d566785a474715195abac763)

**Cyfrin:** Verified.

## [M-6] Consider switching to `Reentrancy Guard Transient`
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `NegRiskAdapter` inherits `ReentrancyGuard` and `MyriadCTFExchange` / `PredictionMarketV3ManagerCLOB` inherit `ReentrancyGuardUpgradeable`. Both variants store the lock flag in a regular storage slot (`_status`). Because the slot is cold at the start of each transaction, each guarded function call costs approximately:

OpenZeppelin ≥ 5.1.0 (the project already depends on v5.3.0) ships `ReentrancyGuardTransient` and `ReentrancyGuardTransientUpgradeable`, which store the flag in transient storage.

Affected in-scope contracts:

| Contract | Current base | Transient replacement |
|---|---|---|
| `NegRiskAdapter` | `ReentrancyGuard` | `ReentrancyGuardTransient` |
| `MyriadCTFExchange` | `ReentrancyGuardUpgradeable` | `ReentrancyGuardTransientUpgradeable` |
| `PredictionMarketV3ManagerCLOB` | `ReentrancyGuardUpgradeable` | `ReentrancyGuardTransientUpgradeable` |

**Recommended Mitigation:** Replace the base contract import and inheritance for each affected contract. For the upgradeable variants the `__ReentrancyGuard_init()` call in `initialize()` can be removed (the transient variant needs no initialization):

```solidity
// NegRiskAdapter
import "@openzeppelin/contracts/utils/ReentrancyGuardTransient.sol";
contract NegRiskAdapter is ReentrancyGuardTransient, ERC1155Holder { ... }

// MyriadCTFExchange / PredictionMarketV3ManagerCLOB
import "@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardTransientUpgradeable.sol";
contract MyriadCTFExchange is ..., ReentrancyGuardTransientUpgradeable, ... { ... }
// remove: __ReentrancyGuard_init();
```

**Myriad:** Fixed in commit [`5993fc7`](https://github.com/Polkamarkets/polkamarkets-js/commit/5993fc77c583b4c6626e512380a27a5be9a0795d)

**Cyfrin:** Verified.

## [M-7] Magic numbers `0` and `1` used for YES and NO outcome indices throughout the codebase
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** Outcome indices are hardcoded as bare integer literals `0` (YES) and `1` (NO) throughout the contracts with no named constant:

```solidity
// NegRiskAdapter.sol
manager.adminResolveMarket(evt.marketIds[i], 0); // YES wins
manager.adminResolveMarket(evt.marketIds[i], 1); // NO wins

uint256 yesTokenId = conditionalTokens.getTokenId(marketId, 0);
uint256 noTokenId  = conditionalTokens.getTokenId(marketId, 1);

// ConditionalTokens.sol
_mint(msg.sender, getTokenId(marketId, 0), amount, "");
_mint(msg.sender, getTokenId(marketId, 1), amount, "");
```

Using unnamed literals makes the intent harder to verify at a glance, increases the risk of a transposition error (passing `1` where `0` was intended), and means any future change to the outcome encoding would require hunting down every occurrence manually.

**Recommended Mitigation:** Define shared constants and use them consistently:

```solidity
uint256 internal constant YES = 0;
uint256 internal constant NO  = 1;

// Usage becomes self-documenting:
conditionalTokens.getTokenId(marketId, YES);
manager.adminResolveMarket(marketId, NO);
```

**Myriad:** Fixed in commits [`6530746`](https://github.com/Polkamarkets/polkamarkets-js/pull/126/changes/6530746f656a40e9124201ac4d0c90d0b57f8fda) and [`a7ce7a7`](https://github.com/Polkamarkets/polkamarkets-js/pull/126/changes/a7ce7a77e6639368e3fd679a87748c831ee7d45c)

**Cyfrin:** Verified.

## [M-8] Neg-risk events have no void/cancellation path
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** Standalone binary markets support cancellation via `adminVoidMarket`, which sets `resolvedOutcome = -1`, records admin-specified payout ratios in `voidedPayouts`, and allows participants to recover collateral pro-rata through `ConditionalTokens::redeemVoided`.

Neg-risk event markets have no equivalent path. `adminVoidMarket` hard-blocks neg-risk markets:

```solidity
// PredictionMarketV3ManagerCLOB.sol:219
require(!market.negRisk, "use resolveEvent for neg risk");
```

And `NegRiskAdapter::resolveEvent` only accepts a winning outcome (`winningIndex >= -1`), where `-1` is explicitly the "Other" outcome, meaning no named candidate won, not a cancellation. If an event needs to be cancelled (oracle becomes unavailable, question is invalidated, regulatory action), the admin has no safe option:

- **Leave unresolved** - all participant collateral remains locked in `ConditionalTokens` indefinitely with no redemption path.
- **Resolve as "Other" wins** - all participant collateral is recovered by the adapter via its NO token redemptions and forwarded to treasury, rather than being refunded to participants.

Neither option is a fair cancellation.

**Recommended Mitigation:** Add a `voidEvent` function to `NegRiskAdapter` that calls `adminVoidMarket` on each underlying market with a provided payout split, sets `evt.resolved = true`, and handles the adapter's minted wcol accounting for the partial recovery scenario. This gives participants access to `redeemVoided` and recovers their collateral proportionally.

**Myriad:** Fixed in commit [`185c204`](https://github.com/Polkamarkets/polkamarkets-js/commit/185c204e8bcacccaf26566c6d62ecdc22211f986)

**Cyfrin:** Verified.

## [M-9] Neg Risk market creator is set to adapter address instead of the initiator
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `PredictionMarketV3ManagerCLOB::createNegRiskMarket` is restricted to the registered `NegRiskAdapter`. When the adapter creates a neg-risk event it calls the manager in a loop; inside the manager we set `market.creator = msg.sender`. At that point `msg.sender` is the adapter contract, not the address that called the adapter. So every neg-risk market ends up with `creator` equal to the adapter, and the actual initiator (the market admin who called `NegRiskAdapter::createEvent`) is not recorded.

This matters for any logic or UI that treats `creator` as the human or admin who created the market — for example display, permissions, or analytics. For neg-risk markets that information is wrong.

```solidity
// PredictionMarketV3ManagerCLOB.sol:129-154
function createNegRiskMarket(
  CreateMarketParams calldata params,
  IERC20 collateralOverride,
  bytes32 eventId
) external nonReentrant returns (uint256 marketId) {
  require(msg.sender == negRiskAdapter, "not adapter");
  // ...
  market.creator = msg.sender;  // adapter, not the EOA/admin who called the adapter
```

**Recommended Mitigation:** Pass the actual creator into `createNegRiskMarket` and use it for `market.creator`. Also consider adding the creator to the `MarketCreated` event.

**Myriad:** Fixed in commit [`285a63c`](https://github.com/Polkamarkets/polkamarkets-js/commit/285a63c7a7bdbb10ac3604855cc1e216b1343b3d)

**Cyfrin:** Verified.

## [M-10] State change without event
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** Four setter functions update addresses that gate critical protocol functionality but emit no event, making changes invisible to off-chain monitors and indexers:

- `MyriadCTFExchange::setNegRiskAdapter` - only address allowed to call `mintAllYesTokens`; controls cross-market matching
- `NegRiskAdapter::setExchange` - only address allowed to call `mintAllYesTokens` on the adapter
- `NegRiskAdapter::setTreasury` - destination for excess collateral recovered at event resolution
- `PredictionMarketV3ManagerCLOB::setNegRiskAdapter` - only address allowed to create neg-risk markets and call `adminResolveMarket` for them

```solidity
// MyriadCTFExchange.sol
function setNegRiskAdapter(address _adapter) external { negRiskAdapter = _adapter; /* no event */ }

// NegRiskAdapter.sol
function setTreasury(address newTreasury) external { treasury = newTreasury; /* no event */ }
function setExchange(address _exchange) external  { exchange = _exchange;   /* no event */ }

// PredictionMarketV3ManagerCLOB.sol
function setNegRiskAdapter(address _adapter) external { negRiskAdapter = _adapter; /* no event */ }
```

**Recommended Mitigation:** Add and emit a dedicated event in each setter, e.g.:

```solidity
event NegRiskAdapterUpdated(address indexed newAdapter);
event ExchangeUpdated(address indexed newExchange);
event TreasuryUpdated(address indexed newTreasury);
```


**Myriad:** Fixed in commit [`d6c6654`](https://github.com/Polkamarkets/polkamarkets-js/commit/d6c6654794550095a65d79be701f3e0ee7701bb3)

**Cyfrin:** Verified.

## [M-11] Decompression Bomb due to lack of  post decompression size check
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The deeplink connection flow enforces a 1 MB size limit on the **compressed, base64-encoded** payload and not the decompressed output. A crafted `~26 KB` deeplink trivially passes the guard and forces `pako.inflate()` to allocate an unbounded amount of heap memory. The wallet processes the bomb silently, establishing a full connection and persisting it to storage, with no error surfaced to the user.

An attacker can crash MetaMask Mobile or degrade device memory by sending a single deeplink. No authentication, no user account, and no existing session are required. The entire attack surface is reachable with a tap on a malicious `metamask://` URL.
```typescript
// connection-registry.ts
if (payload.length > 1024 * 1024) {   // checked on compressed + base64 input
    throw new Error('Payload too large (max 1MB).');
}
const jsonString =
    compressionFlag === '1' ? decompressPayloadB64(payload) : payload;
```
Inside `decompressPayloadB64`, `pako.inflate()` is called with **no output size limit**:
```typescript
// compression-utils.ts
const decompressed = inflate(compressed);  // no max_size / chunkSize limit
return new TextDecoder().decode(decompressed);
```

`payload` is the raw URL query parameter which is the base64 encoding of the compressed data. A 1 MB compressed stream encodes to ~1.33 MB base64, so the effective compressed size budget is ~750 KB. The decompressed output is **never validated**.

A single maximum-budget deeplink can force upto **~578 MB** of heap allocation in one call. Check PoC which we

**Impact:** A crafted compressed payload of ~750 KB (which passes the 1 MB base64 check) can expand to **500 MB+** of JSON data depending on content repetition. `JSON.parse()` on the resulting oversized string exhausts mobile process memory and crashes the MetaMask app. It is exploitable by anyone who can deliver a deeplink to the target device however its likelihood is quite low as only prior old devices would be practically impacted.

**Proof of Concept:** <details>
<summary>Add this to `connection-registry.test.ts` </summary>

``` typescript

 describe('Decompression Bomb', () => {
    // ES2017 lib only — no Buffer, no DOM btoa. Encode Uint8Array → base64
    // by iterating bytes and casting through charCodeAt.
    const u8ToB64 = (b: Uint8Array): string => {
      let s = '';
      for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (global as any).btoa(s);
    };


    const buildBombB64 = () =>
      u8ToB64(
        deflate(
          JSON.stringify({
            ...mockConnectionRequest,
            _padding: 'A'.repeat(20_000_000),
          }),
        ),
      );


    // Building + deflating 400 MB takes ~8 s; Jest timeout extended to 30 s.
    const buildMaxExpansionBombB64 = () =>
      u8ToB64(
        deflate(
          JSON.stringify({
            ...mockConnectionRequest,
            _bomb: 'A'.repeat(400_000_000), // ~400 MB
          }),
        ),
      );


    it('should traverse the full connection flow without error when given a compressed bomb deeplink', async () => {
      // Given: a registry ready to handle connections
      registry = new ConnectionRegistry(
        RELAY_URL,
        mockKeyManager,
        mockHostApp,
        mockStore,
      );

      const b64 = buildBombB64();
      const deeplink = `metamask://connect/mwp?p=${encodeURIComponent(b64)}&c=1`;

      // The size guard passes — payload is ~33 KB, well under the 1 MB limit
        expect(b64.length).toBeLessThan(1024 * 1024);

      // When: the bomb deeplink is processed
      await registry.handleConnectDeeplink(deeplink);

      // Then: the full happy path completes — guard bypassed, ~20 MB allocated,
      //   connection created, saved to store, no error surfaced to the user
      expect(mockHostApp.showConnectionError).not.toHaveBeenCalled();
      expect(mockHostApp.showConnectionLoading).toHaveBeenCalledTimes(1);
      expect(Connection.create).toHaveBeenCalledTimes(1);
      expect(mockConnection.connect).toHaveBeenCalledTimes(1);
      expect(mockStore.save).toHaveBeenCalledTimes(1);
      expect(mockHostApp.hideConnectionLoading).toHaveBeenCalledTimes(1);
    });

    it('should process N distinct bomb deeplinks independently — no rate limit or concurrency cap exists', async () => {

      registry = new ConnectionRegistry(
        RELAY_URL,
        mockKeyManager,
        mockHostApp,
        mockStore,
      );

      const BOMB_COUNT = 3;
      const bombs = Array.from({ length: BOMB_COUNT }, (_, i) => {
        const b64 = u8ToB64(
          deflate(
            JSON.stringify({
              ...mockConnectionRequest,
              sessionRequest: {
                ...mockConnectionRequest.sessionRequest,
                id: `bomb-session-${i}`,
              },
              _padding: 'A'.repeat(20_000_000),
            }),
          ),
        );
        return `metamask://connect/mwp?p=${encodeURIComponent(b64)}&c=1`;
      });

      // Each deeplink has a unique URL, deduplication guard does not apply
      expect(new Set(bombs).size).toBe(BOMB_COUNT);


      (Connection.create as jest.Mock).mockResolvedValue({
        ...mockConnection,
        id: expect.any(String),
      });

      await Promise.all(bombs.map((dl) => registry.handleConnectDeeplink(dl)));

      // Then: all N inflate() calls complete — no rate limiting, no abort
      expect(mockHostApp.showConnectionError).not.toHaveBeenCalled();
      expect(Connection.create).toHaveBeenCalledTimes(BOMB_COUNT);
    });

    // Building + deflating 400 MB takes ~8 s — per-test timeout extended to 30 s.
    it('should accept a ~526 KB compressed payload and inflate it to 400 MB — guard checks pre-decompression size only', async () => {
      // Given: a registry ready to handle connections
      registry = new ConnectionRegistry(
        RELAY_URL,
        mockKeyManager,
        mockHostApp,
        mockStore,
      );

      // 400 MB of 'A' → deflate → ~394 KB compressed → ~526 KB base64
      const b64 = buildMaxExpansionBombB64();

      // The guard at connection-registry.ts:236 sees only the compressed+base64 length
      expect(b64.length).toBeGreaterThan(400_000);   // ~526 KB compressed+base64
      expect(b64.length).toBeLessThan(1024 * 1024);  // passes the 1 MB guard

      const out = compressionUtils.decompressPayloadB64(b64);
      expect(out.length).toBeGreaterThan(350_000_000);      // >350 MB actual data
      expect(out.length / b64.length).toBeGreaterThan(600); // >600× expansion ratio

      // When: the bomb is delivered as a deeplink
      const deeplink = `metamask://connect/mwp?p=${encodeURIComponent(b64)}&c=1`;
      await registry.handleConnectDeeplink(deeplink);

      expect(mockHostApp.showConnectionError).not.toHaveBeenCalled();
      expect(mockHostApp.showConnectionLoading).toHaveBeenCalledTimes(1);
      expect(Connection.create).toHaveBeenCalledTimes(1);
      expect(mockConnection.connect).toHaveBeenCalledTimes(1);
      expect(mockStore.save).toHaveBeenCalledTimes(1);
      expect(mockHostApp.hideConnectionLoading).toHaveBeenCalledTimes(1);
    }, 30_000); // 30 s — building + deflating 400 MB takes ~8 s
  });

```
```
Output:
    Decompression Bomb
      ✓ should expand a ~33 KB compressed payload to 20 MB — the guard checks compressed size only, leaving decompressed output unbounded (580 ms)
      ✓ should traverse the full connection flow without error when given a compressed bomb deeplink (548 ms)
      ✓ should process N distinct bomb deeplinks independently — no rate limit or concurrency cap exists (1197 ms)
      ✓ should accept a ~526 KB compressed payload and inflate it to 400 MB — guard checks pre-decompression size only (11599 ms)
```

</details>

**Recommended Mitigation:** Check post-decompression size in `decompressPayloadB64`

**Metamask:**
Fixed in commit [867acb](https://github.com/MetaMask/metamask-mobile/commit/867acb98f4f409d3feb7f413d9c59640190e70f0).

**Cyfrin:** Verified.

## [M-12] Internal origin allowlist bypass via unnormalized URL matching in Connection Registry
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The `ConnectionRegistry.handleConnectDeeplink()` method validates incoming connection requests against a static list of internal origins using `Array.includes()` which performs exact string comparison. The values being compared (`connReq.metadata.dapp.ur`l and `connReq.metadata.dapp.name`) are self-reported by the connecting dApp through the deeplink payload and are never verified against any external source.

```js
if (
  INTERNAL_ORIGINS.includes(connReq.metadata.dapp.url) ||
  INTERNAL_ORIGINS.includes(connReq.metadata.dapp.name)
) {
  throw rpcErrors.invalidParams({
    message: 'External transactions cannot use internal origins',
  });
}
```
The `connReq.metadata` comes directly from a deeplink payload:
```js
const connReq: unknown = JSON.parse(jsonString);
```

This metadata is attacker controlled. There is no normalization, canonicalization, or sanitization before the `includes()` comparison. An attacker controlled dApp can bypass this check by submitting a `URL` that is semantically equivalent to an internal origin but differs at the string level.

Examples:
```
https://metamask.io/ vs https://metamask.io     (trailing slash)
https://MetaMask.io vs https://metamask.io      (casing)
https://metamask.io/./                          (dot segment)
https://metamаsk.io                             (cyrillic 'а' U+0430 vs latin 'a' U+0061)
```

**Impact:** A malicious dApp can set its metadata to closely resemble a trusted MetaMask internal `origin` bypassing the blocklist and displaying a spoofed origin string in the wallet approval UI. This is a UI deception issue. It does not bypass transaction approval since the wallet still requires explicit user confirmation for every action and the user sees actual transaction details (recipient, amount, contract data) in the approval screen.

**Recommended Mitigation:** Normalize URLs before comparison. At minimum, lowercase both sides, strip trailing slashes, and resolve relative path segments. Consider using prefix or pattern matching rather than exact string equality. As a broader point, treat all dApp-reported metadata as untrusted input and avoid using it as the sole basis for any security decision.

```js
private isInternalOrigin(origin: string): boolean {
  try {
    const normalized = new URL(origin).origin.toLowerCase();
    return INTERNAL_ORIGINS.some(
      (internal) => new URL(internal).origin.toLowerCase() === normalized,
    );
  } catch {
    return false;
  }
}
```

Then replace the current check:
```js
if (
  this.isInternalOrigin(connReq.metadata.dapp.url) ||
  INTERNAL_ORIGINS.some(
    (o) => o.toLowerCase() === connReq.metadata.dapp.name.toLowerCase(),
  )
) {
  throw rpcErrors.invalidParams({
    message: 'External transactions cannot use internal origins',
  });
}
```

**MetaMask:** Fixed in commits [ca66895](https://github.com/MetaMask/metamask-mobile/commit/ca668952d2d80352560f193d7dd2e22aed7ae4e9), [b60153](https://github.com/MetaMask/metamask-mobile/commit/b6015313dba44592814e58f2e9612e585852de14).

**Cyfrin:** Verified.

\clearpage

## [M-13] OTP generated using math.random is not cryptographically secure way to generate verification code
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The `untrusted` connection flow is the protocol's high-security path. It is designed for cross-device scenarios (e.g., scanning a QR code from an untrusted computer) where a man-in-the-middle could subscribe to the handshake channel and race the legitimate dApp. In this flow, the One-Time Password is the sole mechanism that authenticates the two parties to each other,  the user visually compares the OTP displayed on the wallet screen to the one presented by the dApp.
```js
// packages/wallet-client/src/handlers/untrusted-connection-handler.ts:49-53
private _generateOtpWithDeadline(): { otp: string; deadline: number } {
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    const deadline = Date.now() + this.otpTimeoutMs;
    return { otp, deadline };
}
```

The same non-cryptographic pattern is also used in the legacy V1 OTP generator on the `metamask-mobile` side:
```js
// metamask-mobile/app/core/SDKConnect/utils/generateOTP.util.ts:1-2
const generateRandomIntegerInRange = (min: number, max: number): number =>
  Math.floor(Math.random() * (max - min + 1)) + min;
```

`Math.random()` is explicitly defined by the `ECMAScript` specification as [not providing cryptographically secure random numbers](https://deepsource.com/blog/dont-use-math-random). Every modern JavaScript engine implements it with `xorshift128+`, a fast but fully deterministic PRNG. Its full 128-bit internal state can be reconstructed from a handful of observed outputs using known algebraic techniques (e.g., Z3 constraint solving).

In React native's `JavaScriptCore` and `Hermes` engines, the `PRNG` state is shared across the entire JS execution context, meaning any call to Math.random() anywhere in the application animation timing, layout jitter, analytics sampling advances the same state and provides useful observations to an attacker who can instrument or observe the execution.

**Impact:** Because the OTP is the only authentication factor in the untrusted handshake, predictability here could the entire security model of the cross-device flow. The OTP search space is already limited to `900,000` possible values (six-digit codes from `100000` to `999999`), and the dApp allows 3 guesses (`this.otpAttempts = 3`), giving a blind brute-force a `1-in-300,000` chance per connection.

With PRNG state recovery (feasible from approximately 3–4 prior `Math.random() `observations from the same context), an attacker can predict the exact OTP with certainty, enabling a complete man-in-the-middle of the key exchange.

On the dApp side, the OTP verification itself also uses a direct string comparison rather than a timing-safe comparison:
```js
// packages/dapp-client/src/handlers/untrusted-connection-handler.ts:93
if (otp !== offer.otp) {
```
While this comparison between short strings and practical timing extraction is `difficult over a WebSocket`, it compounds the weak generation with a weak verification pattern.

**Recommended Mitigation:** Replace `Math.random()` with the Web Crypto API's `crypto.getRandomValues()`, which is backed by the operating system's `CSPRNG` and is available in all target environments (browser, React Native, Node.js):
```js
private _generateOtpWithDeadline(): { otp: string; deadline: number } {
    const buf = new Uint32Array(1);
    crypto.getRandomValues(buf);
    const otp = (100000 + (buf[0] % 900000)).toString();
    const deadline = Date.now() + this.otpTimeoutMs;
    return { otp, deadline };
}
```

Additionally, consider using a timing-safe comparison for OTP verification on the dApp side, and consider rate-limiting OTP attempts at the protocol level rather than relying solely on a client-side counter.

**MetaMask:** Fixed in commits [46f81](https://github.com/MetaMask/mobile-wallet-protocol/commit/46f8111c151484d44992ced7bc5cd24307ab7930) , [7bbacf](https://github.com/MetaMask/mobile-wallet-protocol/commit/7bbacf3a17fa6d362ac4f29df5158e17ff34513d).

**Cyfrin:** Verified

## [M-14] Session object with private key, decrypted payloads logged in debug mode and deeplink url being logged unconditionally on error path
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** Debug-level logging outputs full session objects (including private keys) and decrypted message payloads. Additionally, one error path logs the raw deeplink URL unconditionally, which may contain sensitive connection parameters.

1. When debug logging is enabled, the dApp SDK logs the full `session` object (which contains `keyPair.privateKey`) via `logger('active session found', session)`. The mobile wallet logs decrypted JSON-RPC payloads via `logger.debug('Received message:', payload)` and `logger.debug('Sending message:', payload)`.

On mobile devices, these logs can be accessible via crash reporters, log aggregation, or ADB logcat.

2. When deeplink parsing fails, the raw deeplink URL is logged at the error level regardless of debug mode. Deeplink URLs contain connection parameters (channel ID, public key) that could be used to intercept or replay connections.
```js
logger.error('Failed to handle connect deeplink:', error, url);
```
```js
error: (...args: unknown[]) => {
    console.error(prefix, ...args);  // Always active, no debug gate
},
```

**Impact:**
- Private key exposure via device logs, crash reporters, or log aggregation
- Decrypted transaction details (addresses, amounts) visible in logs
- Connection parameters leaked on error paths even in production builds

**Recommended Mitigation:**
- Create a safe session serializer that excludes keyPair:
```js
function safeSessionLog(session: Session) {
    return { id: session.id, channel: session.channel, expiresAt: session.expiresAt };
}
```
- Redact message payloads in debug logs to metadata only.
- Gate `logger.error` calls containing URLs behind the debug flag, or strip query parameters before logging.


**MetaMask:** Fixed in commits [e9e2ad](https://github.com/MetaMask/connect-monorepo/commit/e9e2ade076ae56ba2264937a1fb68339025b319b), [be2b91](https://github.com/MetaMask/metamask-mobile/commit/be2b91ce59f2f3caeb10a322b7b26251380f3aba)

**Cyfrin:** Verified.

## [M-15] Weak structural validation of connection Request from deeplink
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The `ConnectionRequest` parsed from deeplinks undergoes minimal structural validation. Required fields are checked for presence and type but not for format, length, or semantic correctness.

When a deeplink is received, its parameters are parsed into a `ConnectionRequest`. The validation checks:
- `mode`: verified as `typeof string` only, not validated against `["trusted", "untrusted"]`
- `id`: verified as `typeof string`, and not validated againt `UUID` format validation
- `publicKeyB64`: checked for presence but no format/length validation
- `channel` with `typeof string` and no `handshake:{uuid}` format check
- `expiresAt`: checked as `typeof number` but no `isNaN` or future-time check
- `dapp.name`, `dapp.url` , `url`:  validated as URL format but no length cap on either field

For example:
An invalid mode value (e.g., "invalid") passes validation and at `dapp-client` and `wallet-client` the ternary `mode === "trusted" ? TrustedConnectionHandler : UntrustedConnectionHandler` defaults to `UntrustedConnectionHandler` which is the more secure path (a safe failure mode). This allows malformed or adversarial values to enter the system which in-future may cause unexpected behavior in downstream processing.

**Impact:**
- Malformed but structurally valid connection requests proceed into the connection flow. An arbitrarily long `dapp.name` (megabytes) could cause UI rendering issues when displayed in the connection approval dialog.
- `NaN` `expiresAt` values propagate through without detection.
- Increases attack surface by accepting inputs that should be rejected early

**Recommended Mitigation:**
- Validate `mode` against allowed enum values (`"trusted"`, `"untrusted"`)
- Validate `publicKeyB64` format (base64 string decoding to correct byte length for `secp256k1`)
- Add `isNaN` guard on `expiresAt` and verify it's a future timestamp
```js
if (!['trusted', 'untrusted'].includes(sessionReq.mode)) return false;
if (isNaN(sessionReq.expiresAt) || sessionReq.expiresAt < Date.now()) return false;
if (sessionReq.publicKeyB64.length > 200) return false;
if (metadata.dapp.name.length > 256) return false;
```
- Enforce maximum length bounds on all string fields

**MetaMask:** Fixed in commit [ca6689](https://github.com/MetaMask/metamask-mobile/commit/ca668952d2d80352560f193d7dd2e22aed7ae4e9).

**Cyfrin:** Verified.

## [M-16] `create_account` can be dosed with pre-funding
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** Instructions like `new_holder_account` create PDAs using `system_instruction::create_account` with `invoke_signed`. Per Solana system program rules, `create_account` fails if the target already **exists with non-zero lamports or data**.

An attacker can pre-calculate the PDA and transfer SOL to it, causing subsequent `create_account` to fail, blocking account initialization and the following logic flow.

```rust
let account_size = size_of::<HolderAccountHeader>();
invoke_signed(
    &system_instruction::create_account(
        holder_admin.key,
        holder_acc.key,
        Rent::default().minimum_balance(account_size),
        account_size as u64,
        program_id,
    ),
    &[holder_admin.clone(), holder_acc.clone()],
    &[&[HOLDER_SEED, holder_admin.key.as_ref(), &[bump_seed]]],
)
.map_err(|err| drv_err!(err.into()))?;
```

For Reference: https://x.com/r0bre/status/1887939134385172496

Note: the `system_instruction::create_account` also exists in `src/program/processor/new_holder_account.rs, src/program/processor/new_root_account.rs, src/program/create_client_account.rs, src/state/candles.rs, src/state/instrument.rs, src/state/perps/perp_trade_header.rs, src/state/spots/spot_account_header.rs, src/state/token.rs`

**Impact:**
- Any actor can block creation of critical PDAs (`holder accounts, root accounts, headers, tokens, etc`) by pre-funding them with a minimal lamport amount.

**Proof of Concept:**
```rust
/// Test to demonstrate PDA DOS attack vulnerability
///
/// This test simulates an attacker pre-calculating the PDA address
/// and pre-funding it to prevent the admin from creating the Holder Account
#[tokio::test]
async fn test_holder_account_dos_attack() {
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Create program test environment
    let mut test = ProgramTest::new(
        "smart_contract",
        program_id,
        processor!(smart_contract::process_instruction),
    );

    // Setup admin and attacker accounts
    let admin_signer = Keypair::from_bytes(CLIENTS[0].kp).unwrap();
    let attacker = Keypair::new();

    // Add accounts to test environment with initial SOL balance
    test.add_account(
        admin_signer.pubkey(),
        Account {
            lamports: 10_000_000_000, // 10 SOL
            data: vec![],
            owner: system_program::id(),
            executable: false,
            rent_epoch: 0,
        },
    );
    test.add_account(
        attacker.pubkey(),
        Account {
            lamports: 10_000_000_000, // 10 SOL
            data: vec![],
            owner: system_program::id(),
            executable: false,
            rent_epoch: 0,
        },
    );

    // Attacker pre-calculates the PDA address using the same seeds as the protocol
    let (pda_address, _) = Pubkey::find_program_address(
        &[HOLDER_SEED, admin_signer.pubkey().as_ref()],
        &program_id
    );

    println!("🎯 Attacker pre-calculated PDA address: {}", pda_address);

    // Start the test context
    let mut ctx = test.start_with_context().await;

    // Attacker pre-funds the PDA address to make it balance non-zero
    let transfer_instruction = system_instruction::transfer(
        &attacker.pubkey(),
        &pda_address,
        1_000_000, // Transfer 0.001 SOL, mimic minimum balance
    );

    let transfer_transaction = Transaction::new_signed_with_payer(
        &[transfer_instruction],
        Some(&attacker.pubkey()),
        &[&attacker],
        ctx.last_blockhash,
    );

    let result = ctx.banks_client.process_transaction(transfer_transaction).await;
    assert!(result.is_ok(), "Attacker should be able to pre-fund PDA address");

    println!("✅ Attacker successfully pre-funded PDA address");

    // Admin attempts to create Holder Account
    println!("Admin attempts to create Holder Account");
    let mut tx = Transaction::new_with_payer(
        &[Instruction::new_with_bytes(
            program_id,
            &[0], // NewHolderInstruction
            vec![
                AccountMeta {
                    pubkey: admin_signer.pubkey(),
                    is_signer: true,
                    is_writable: true,
                },
                AccountMeta {
                    pubkey: pda_address,
                    is_signer: false,
                    is_writable: true,
                },
                AccountMeta {
                    pubkey: system_program::ID,
                    is_signer: false,
                    is_writable: false,
                },
            ],
        )],
        Some(&admin_signer.pubkey()),
    );
    tx.sign(&[&admin_signer], ctx.last_blockhash);

    // Admin creation should fail because PDA is pre-occupied
    let result = ctx.banks_client.process_transaction(tx).await;

    if result.is_err() {
        println!("🚨 DOS ATTACK SUCCESSFUL: Admin failed to create holder account");
    } else {
        println!("❌ Test failed: Admin creation should have failed but didn't");
    }
}

```

Test Output:
```plaintext
running 1 test
[2025-10-30T01:37:51.898533000Z INFO  solana_program_test] "smart_contract" builtin program
🎯 Attacker pre-calculated PDA address: 5zAb3ZhCNjTwoMxK39fheR4fXbuArMJVN9bhaeQkZHrq
[2025-10-30T01:37:52.011771000Z DEBUG solana_runtime::message_processor::stable_log] Program 11111111111111111111111111111111 invoke [1]
[2025-10-30T01:37:52.011914000Z DEBUG solana_runtime::message_processor::stable_log] Program 11111111111111111111111111111111 success
✅ Attacker successfully pre-funded PDA address
Admin attempts to create Holder Account
[2025-10-30T01:37:52.013452000Z DEBUG solana_runtime::message_processor::stable_log] Program Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu invoke [1]
[2025-10-30T01:37:52.013485000Z DEBUG solana_runtime::message_processor::stable_log] Program Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu invoke [1]
[2025-10-30T01:37:52.013963000Z DEBUG solana_runtime::message_processor::stable_log] Program 11111111111111111111111111111111 invoke [1]
[2025-10-30T01:37:52.014048000Z DEBUG solana_runtime::message_processor::stable_log] Program 11111111111111111111111111111111 invoke [2]
[2025-10-30T01:37:52.014070000Z DEBUG solana_runtime::message_processor::stable_log] Create Account: account Address { address: 5zAb3ZhCNjTwoMxK39fheR4fXbuArMJVN9bhaeQkZHrq, base: None } already in use
[2025-10-30T01:37:52.014101000Z DEBUG solana_runtime::message_processor::stable_log] Program 11111111111111111111111111111111 failed: custom program error: 0x0
{"code":100,"error":{"Custom":0},"location":{"file":"src/program/processor/new_holder_account.rs","line":63},"msg":"System error Custom program error: 0x0"}
[2025-10-30T01:37:52.014285000Z DEBUG solana_runtime::message_processor::stable_log] Program Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu failed: custom program error: 0x64
[2025-10-30T01:37:52.014303000Z DEBUG solana_runtime::message_processor::stable_log] Program Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu failed: custom program error: 0x64
🚨 DOS ATTACK SUCCESSFUL: Admin failed to create holder account
test instructions::test_holder_dos::test_holder_account_dos_attack ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out; finished in 0.24s
```

**Recommended Mitigation:** Do not rely on `create_account` for PDAs. Instead, support both fresh and pre-funded PDA flows by:
1. Funding (if needed),
2. allocating
3. assigning the PDA with invoke_signed.

**Deriverse:** Fixed in commit [df95974](https://github.com/deriverse/protocol-v1/commit/df95974c9c967e79e35403b313ee2e299f01a2ef) and [9b8e442](https://github.com/deriverse/protocol-v1/commit/9b8e442ec18843e4e8b77975486d37a19bf9c9e2).

**Cyfrin:** Verified.

## [M-17] `get_by_tag` tries to access out of bound index
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The [get_by_tag](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/constants.rs#L4) contains an off-by-one error in its loop condition. The function iterates using [while i <= continer.candles.len()](https://github.com/deriverse/protocol-v1/blob/30b06d2da69e956c000120cdc15907b5f33088d7/src/program/constants.rs#L9) instead of the correct [while i < continer.candles.len()](), causing an out-of-bounds array access when iterating past the last valid index.
```rust
pub const fn get_by_tag<const TAG: u32>(
    continer: CandleRegister,
) -> Result<CandleParams, DeriverseError> {
    let mut i = 0;

    while i <= continer.candles.len() {  // BUG: should be `<` not `<=`
        if continer.candles[i].tag == TAG {  // Out-of-bounds when i == len
            return Ok(continer.candles[i]);
        }
        i += 1;
    }
    // ...
}
```
This function is called throughout the codebase in different candle-related operations & all paths are affected.  The bug may not manifest during normal operations if the TAG is found early in the array, It will panic when i == len() due to out-of-bounds indexing rather than returning normal error
```rust
    Err(DeriverseError {
        error: DeriverseErrorKind::CandleWasNotFound { tag: TAG },
        location: ErrorLocation {
            file: file!(),
            line: line!(),
        },
    })
```

**Impact:** When the requested TAG is not found before the loop exhausts, or when i reaches [continer.candles.len()](), the code attempts to access memory beyond the array bounds and hence will cause program to panic rather than throwing proper error.

**Recommended Mitigation:**
```rust
pub const fn get_by_tag<const TAG: u32>(
    continer: CandleRegister,
) -> Result<CandleParams, DeriverseError> {
    let mut i = 0;

    while i < continer.candles.len() {  // Fixed: use `<` instead of `<=`
        if continer.candles[i].tag == TAG {
            return Ok(continer.candles[i]);
        }
        i += 1;
    }

    Err(DeriverseError {
        error: DeriverseErrorKind::CandleWasNotFound { tag: TAG },
        location: ErrorLocation {
            file: file!(),
            line: line!(),
        },
    })
}
```
**Deriverse:** Fixed in commit: [4e88698](https://github.com/deriverse/protocol-v1/commit/4e8869833c3de69ad84ed5b9f32fff3b560c5b93)

**Cyfrin:** Verified.

## [M-18] Forced Oldest-Order Eviction Enables Griefing
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** **This issue is theoretically possible, but the exploitation conditions are quite strict, so I marked it as INFO.**

When a side of the spot order book exceeds `MAX_ORDERS`, the matching engine unconditionally cancels the globally oldest order on that side. Because `MAX_ORDERS` is shared by all traders, a malicious participant can deliberately fill the book with tiny orders, repeatedly trigger the eviction path, and force legitimate users’ resting/large orders to be cancelled.

`add_order` grows the order book and, after inserting the new order, checks whether the per-side total exceeds MAX_ORDERS. If so, it removes the oldest order, without regard to ownership and the order size.

```rust
        } else if self.orders_count(side) > MAX_ORDERS {
            let oldest_node = self.find_oldest_order_node(side);
            let oldest_order = self.get_order_ptr(oldest_node.link(), side);
            self.erase_client_order(oldest_order, oldest_node, true, side)?;
            ...
```

`MAX_ORDERS` is a global limit (≈14,334) shared by all users of the instrument.

```rust
pub mod spot {
    pub const MAX_LINES: usize = 2048;
    pub const MAX_ORDERS: u32 = (4 * 64 * 64 - MAX_LINES) as u32 - 2;
```

An attacker can create many minimum-quantity orders (funds are returned when their orders are eventually evicted), drive `orders_count(side)` above `MAX_ORDERS`, and delete the oldest resting order. The cost is limited to transaction fees plus temporarily locking collateral for the attacker’s own active orders.

**Impact:** Other traders’ limit orders can be griefed off the book at will regardless of the order size, degrading market integrity, denying service, and allowing the attacker to control displayed liquidity.

**Recommended Mitigation:** Prevent a single participant from consuming the entire order quota. Options include:
- Enforce a per-client cap on orders numbers.

**Deriverse:** Fixed in commit [ed3b97ec](https://github.com/deriverse/protocol-v1/commit/ed3b97ec0e4157a55df4c5a8e56dda6786ec2195).

**Cyfrin:** Verified.

## [M-19] Incorrect Token Program Error Message in Airdrop Flow
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The airdrop instruction correctly enforces that DRVS tokens must use the `Token‑2022` program, but the error message suggests the opposite. This inconsistency can mislead operators when diagnosing configuration mistakes.

```rust
if check_spl_token(...) ? {
    let token_program_version = TokenProgram::new(token_program.key)?;
    bail!(InvalidTokenProgramId {
        expected: TokenProgram::Original,
        actual: token_program_version,
    });
}
```

The bailout is correct: the code later calls `spl_token_2022::instruction::transfer_checked`, so Token‑2022 is required. However, the error message reports `expected: TokenProgram::Original`, which is the *rejected* option.

**Impact:** Operators who misconfigure the mint/program pair will see an error stating that “Original” was expected even though the instruction actually expects Token‑2022.


**Recommended Mitigation:** Update the `InvalidTokenProgramId` message to reflect the real expectation.

**Deriverse:** Fixed in commit [40043ae](https://github.com/deriverse/protocol-v1/commit/40043aeec9d5e731544e6c0b36b766690e7b9c55).

**Cyfrin:** Verified.

## [M-20] `Exit Within Grace Period` event emits inaccurate `amount Received` for adapter vaults
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** In `SablierBob::exitWithinGracePeriod` (`SablierBob.sol:237-287`), the event always emits the share balance as `amountReceived`:

```solidity
emit ExitWithinGracePeriod(vaultId, msg.sender, amount, amount);
```

For non-adapter vaults this is correct — tokens transfer 1:1 with shares. But for adapter vaults (line 278-280), the actual WETH received depends on the Curve stETH→ETH swap which is subject to slippage:

```solidity
if (address(vault.adapter) != address(0)) {
    vault.adapter.unstakeForUserWithinGracePeriod(vaultId, msg.sender);
} else {
    vault.token.safeTransfer(msg.sender, amount);
}
```

`SablierLidoAdapter::unstakeForUserWithinGracePeriod` does not return the WETH received to the caller, so `SablierBob` has no way to emit the correct value. The adapter emits its own `UnstakeForUserWithinGracePeriod` event with the accurate amount in the same transaction, but the parent `ExitWithinGracePeriod` event's `amountReceived` is misleading.

**Recommended Mitigation:** Have `unstakeForUserWithinGracePeriod` return the WETH received, then use that value in the event:
```solidity
if (address(vault.adapter) != address(0)) {
    uint128 received = vault.adapter.unstakeForUserWithinGracePeriod(vaultId, msg.sender);
    emit ExitWithinGracePeriod(vaultId, msg.sender, received, amount);
} else {
    vault.token.safeTransfer(msg.sender, amount);
    emit ExitWithinGracePeriod(vaultId, msg.sender, amount, amount);
}
```

**Sablier:** Fixed in commit [74fa619](https://github.com/sablier-labs/lockup/commit/74fa619471e00958b6b922f8b6c4d9bb95ccc37a) by removing the early exit grace period functionality.

**Cyfrin:** Verified.

## [M-21] `fee Amount` never set when no vault adapter used in `Sablier Bob::redeem`
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** When no vault adapter is used in `SablierBob::redeem`, the output `feeAmount` is never set even though:
* the user does pay a fee as `msg.value`
* `feeAmount` is returned as an output variable and also emitted in the `Redeem` event

**Sablier:** Fixed in commit [75448ba](https://github.com/sablier-labs/lockup/commit/75448ba4e6f5f22207cc5b03096206a7708e5a54) by renaming `feeAmount` to `feeAmountDeductedFromYield` to make it explicit that this applies only when vault adapters are used.

**Cyfrin:** Verified.

## [M-22] `Sablier Bob::_unstake Full Amount Via Adapter` should take `vault.adapter` as input parameter
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** `SablierBob::_unstakeFullAmountViaAdapter` should take `vault.adapter` as an input parameter since both callers already read it, so there is no point in re-reading it again from storage when the value is already known.

**Sablier:** Fixed in commit [7d9ac86](https://github.com/sablier-labs/lockup/commit/7d9ac86a6edc85383b1fc9b58fdfbaf78a8f1cb1).

**Cyfrin:** Verified.

## [M-23] `Sablier Lido Adapter::unstake Full Amount` should return `total Wst ETH`
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** `SablierBob::_unstakeFullAmountViaAdapter` always calls `SablierLidoAdapter::getTotalYieldBearingTokenBalance` then `SablierLidoAdapter::unstakeFullAmount`:

* `SablierLidoAdapter::getTotalYieldBearingTokenBalance` just reads and returns `_vaultTotalWstETH[vaultId]`
* the first thing `SablierLidoAdapter::unstakeFullAmount` does is perform an identical storage read of `_vaultTotalWstETH[vaultId]`

This is inefficient; there are two identical storage reads and one redundant external call. Simply have `SablierLidoAdapter::unstakeFullAmount` return `_vaultTotalWstETH[vaultId]`:
```diff
    function unstakeFullAmount(uint256 vaultId)
        external
        override
        onlySablierBob
-       returns (uint128 amountReceivedFromUnstaking)
+       returns (uint128 totalWstETH, uint128 amountReceivedFromUnstaking)
    {
        // Get total amount of wstETH in the vault.
-       uint128 totalWstETH = _vaultTotalWstETH[vaultId];
+       totalWstETH = _vaultTotalWstETH[vaultId];
```

Then change `SablierBob::_unstakeFullAmountViaAdapter` to use it:
```diff
    function _unstakeFullAmountViaAdapter(uint256 vaultId) private returns (uint128 amountReceivedFromAdapter) {
        Bob.Vault storage vault = _vaults[vaultId];

-       // Get the total amount staked via the adapter.
-       uint128 amountStakedViaAdapter = vault.adapter.getTotalYieldBearingTokenBalance(vaultId);

        // Interaction: unstake all tokens via the adapter.
-       amountReceivedFromAdapter = vault.adapter.unstakeFullAmount(vaultId);
+       uint128 amountStakedViaAdapter;
+       (amountStakedViaAdapter, amountReceivedFromAdapter) = vault.adapter.unstakeFullAmount(vaultId);

        // Log the event.
        emit UnstakeFromAdapter(vaultId, vault.adapter, amountStakedViaAdapter, amountReceivedFromAdapter);
    }
```

**Sablier:** Fixed in commit [d812e23](https://github.com/sablier-labs/lockup/commit/d812e2325975748019f5108f5fa87070e92fa753).

**Cyfrin:** Verified.

## [M-25] ETH sent with adapter vault redemption is trapped in `Sablier Bob`
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** `SablierBob::redeem` is declared `payable` unconditionally, but only the non-adapter path handles `msg.value`. When a user calls `redeem` on an adapter vault with `msg.value > 0` (`SablierBob.sol:290-373`), the adapter path (`SablierBob.sol:326-345`) never checks, forwards, or refunds the ETH:

```solidity
if (address(vault.adapter) != address(0)) {
    // Adapter path: handles ERC-20 yield fee
    // msg.value is NEVER checked, forwarded, or refunded
}
else {
    // Non-adapter path: checks msg.value >= minFeeWei, forwards to comptroller
}
```

The ETH enters `SablierBob` via the `payable` function but has no code path to return to the user. It remains in the contract until someone calls `transferFeesToComptroller` (inherited from `Comptrollerable`), which sweeps the contract's entire ETH balance to the comptroller — not back to the user who sent it.

**Impact:** Users who mistakenly send ETH when redeeming from adapter vaults permanently lose that ETH. While `transferFeesToComptroller` can recover the ETH to the comptroller, the user who sent it has no claim to it. The likelihood is low since adapter vaults don't require ETH fees, but the `payable` modifier provides no indication that ETH is unnecessary and will be lost.

**Recommended Mitigation:** Revert early in the adapter path if `msg.value > 0`:

```solidity
if (address(vault.adapter) != address(0)) {
    if (msg.value > 0) {
        revert Errors.SablierBob_UnexpectedNativeToken(vaultId);
    }
    // ... rest of adapter logic
}
```

**Sablier:** Fixed in commit [44b6bf1](https://github.com/sablier-labs/lockup/commit/44b6bf10f5e9e126b808f8bfd20a098d1275063f).

**Cyfrin:** Verified.

## [M-26] Floor division in `Sablier Lido Adapter::update Staked Token Balance` allows transferring `Bob Vault Shares` without moving wst ETH backing
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** In `SablierLidoAdapter::updateStakedTokenBalance` (`SablierLidoAdapter.sol:352`), the wstETH to transfer is computed using floor division:

```solidity
uint128 wstETHToTransfer = (fromWstETH * shareAmountTransferred / userShareBalanceBeforeTransfer).toUint128();
```

When `fromWstETH * shareAmountTransferred < userShareBalanceBeforeTransfer`, floor division truncates `wstETHToTransfer` to 0. This is easily triggered because the wstETH exchange rate is less than 1:1 with shares — a deposit of N WETH mints N shares but produces less than N wstETH (e.g., with a 0.9 exchange rate, 1000 shares correspond to 900 wstETH). As a result, any 1-wei share transfer satisfies the rounding-to-zero condition: `900 * 1 / 1000 = 0`.

By transferring `BobVaultShares` in 1-wei increments instead of a single bulk transfer, a sender can move an arbitrary number of shares to a recipient while retaining all of their wstETH backing. The recipient ends up holding worthless shares with zero wstETH attribution. Since `SablierLidoAdapter::calculateAmountToTransferWithYield` computes WETH payouts based on `_userWstETH` (not share balances), the recipient receives zero WETH when they redeem.

**Impact:** Any user who receives `BobVaultShare` tokens via small incremental transfers (e.g., buying shares OTC, receiving from a vault share marketplace, or receiving via any transfer mechanism that uses small amounts) will have shares with no wstETH backing. When they redeem after vault settlement/expiry, they receive zero WETH despite holding valid shares.

The sender retains all wstETH backing and receives a disproportionately large WETH payout on redemption. This creates a direct loss for share recipients and a corresponding gain for senders who exploit the rounding.

**Proof of Concept:** Add the following test to `tests/bob/integration/concrete/adapter/adapterPoC.t.sol`:

```solidity
/// - Normal path: A transfers 99 shares to B in one transfer, both redeem
///   and receive proportional WETH
/// - Exploit path: A transfers 99 shares to B in 1-wei increments, both redeem
///   but B receives ZERO WETH while A receives almost everything
///
/// Uses a 1000-wei deposit. With exchange rate 0.9, wstETH = 900.
/// Transferring 99 shares (1000→901) keeps shares > wstETH throughout,
/// so every 1-wei transfer rounds wstETHToTransfer to 0.
function test_PoC_SmallTransfersMakeSharesWorthless() external {
    // Setup: create adapter vault, user A deposits 1000 wei
    uint256 vaultId = createVaultWithAdapter();
    uint128 depositAmount = 1000;

    setMsgSender(users.depositor); // User A
    bob.enter(vaultId, depositAmount);

    uint128 wstETHInitial = adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor);
    assertGt(wstETHInitial, 0, "A should have wstETH after deposit");

    // Expire vault and unstake all tokens to WETH
    vm.warp(EXPIRY + 1);
    bob.unstakeTokensViaAdapter(vaultId);

    uint256 totalWeth = adapter.getWethReceivedAfterUnstaking(vaultId);
    assertGt(totalWeth, 0, "vault should have WETH after unstaking");

    IERC20 shareToken = IERC20(address(bob.getShareToken(vaultId)));
    uint128 transferAmount = 99; // A keeps 901 shares so both can redeem

    // ====== SNAPSHOT ======
    uint256 snapshotId = vm.snapshot();

    // ====== NORMAL PATH: A transfers 99 shares to B in one transfer ======
    setMsgSender(users.depositor);
    shareToken.transfer(users.depositor2, transferAmount);

    // Both redeem
    setMsgSender(users.depositor);
    (uint128 normalRedeemA,) = bob.redeem(vaultId);

    setMsgSender(users.depositor2);
    (uint128 normalRedeemB,) = bob.redeem(vaultId);

    // ====== REVERT TO SNAPSHOT ======
    vm.revertTo(snapshotId);

    // ====== EXPLOIT PATH: A transfers 99 shares to B in 1-wei increments ======
    setMsgSender(users.depositor);
    for (uint256 i; i < transferAmount; i++) {
        shareToken.transfer(users.depositor2, 1);
    }

    // Verify state: B has 99 shares but ZERO wstETH; A has 901 shares and ALL wstETH
    assertEq(
        shareToken.balanceOf(users.depositor),
        depositAmount - transferAmount,
        "A has 901 shares"
    );
    assertEq(shareToken.balanceOf(users.depositor2), transferAmount, "B has 99 shares");
    assertEq(
        adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor2),
        0,
        "BUG: B has 0 wstETH despite holding 99 shares"
    );
    assertEq(
        adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor),
        wstETHInitial,
        "BUG: A retained all wstETH despite transferring 99 shares"
    );

    // Both redeem
    setMsgSender(users.depositor);
    (uint128 exploitRedeemA,) = bob.redeem(vaultId);

    setMsgSender(users.depositor2);
    (uint128 exploitRedeemB,) = bob.redeem(vaultId);

    // ====== COMPARE RESULTS ======
    // Normal path: B gets proportional WETH
    assertGt(normalRedeemB, 0, "Normal: B received WETH");

    // Exploit path: B gets ZERO despite holding shares
    assertEq(exploitRedeemB, 0, "Exploit: B received ZERO WETH despite holding 99 shares");

    // Exploit path: A gets nearly all WETH
    assertGt(exploitRedeemA, normalRedeemA, "Exploit: A received MORE than in normal path");
}
```

Run with: `forge test --match-test test_PoC_SmallTransfersMakeSharesWorthless -vvv`

**Recommended Mitigation:** A simple mitigation is to revert in `SablierLidoAdapter::updateStakedTokenBalance` if `wstETHToTransfer == 0`.

**Sablier:** Fixed in commit [3c669df](https://github.com/sablier-labs/lockup/commit/3c669df3ffd53828fe3b6ec6284316f76bdabb70).

**Cyfrin:** Verified.

## [M-27] Missing getter function for `Sablier Bob State::is Staked In Adapter`
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** The `SablierBobState` contract implements getter functionality for all members of the `Vault` struct for a particular `vaultId`. However it does not implement one for the `isStakedInAdapter` member.
```solidity
struct Vault {
        // slot 0
        IERC20 token;
        uint40 expiry;
        uint40 lastSyncedAt;
        // slot 1
        IBobVaultShare shareToken;
        // slot 2
        AggregatorV3Interface oracle;
        // slot 3
        ISablierBobAdapter adapter;
        bool isStakedInAdapter;
        // slot 4
        uint128 targetPrice;
        uint128 lastSyncedPrice;
    }
```

**Recommended Mitigation:** Consider implementing a getter function for the `isStakedInAdapter` member.

**Sablier:** Fixed in commit [c616091](https://github.com/sablier-labs/lockup/pull/1420/changes/c6160910fc7fb6669b11c6338336eab12400dd6d).

**Cyfrin:** Verified.

## [M-28] Revert fast by performing input related checks prior to storage reads and external calls
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Revert fast by performing input related checks prior to storage reads and external calls:
* `SablierBob::enter` - perform `amount` check first
* `SablierLidoAdapter::updateStakedTokenBalance` - perform `userShareBalanceBeforeTransfer` check first

**Sablier:** Fixed in commit [0b2ea33](https://github.com/sablier-labs/lockup/commit/0b2ea3320e6ced340588c916d53713e0ce98136e).

**Cyfrin:** Verified.

## [M-29] `collat Info.stablecoin Cap` hardcap can be bypassed via `Setters Governor::adjust Stablecoins`
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** The `stablecoinCap` parameter in the `Collateral` struct is intended to cap the maximum amount of normalized stablecoins (`normalizedStables`) that a single collateral asset can back. This limit is correctly enforced during normal user mint operations in the `Swapper` facet.

However, the Governor can call `SettersGovernor::adjustStablecoins` to arbitrarily **increase** `normalizedStables` **without any check** against `stablecoinCap`. This creates a direct bypass of the hardcap mechanism, allowing the system to enter a state where a collateral backs more stablecoins than its configured limit.

**Proof of Concept:** Missing cap validation in the increase path of `LibSetters::adjustStablecoins`:

```solidity
// `LibSetters::adjustStablecoins`
if (increase) {
    newCollateralNormalizedStable += uint216(normalizedAmount);
    newNormalizedStables += uint216(normalizedAmount);
    // Missing:
    // if (newCollateralNormalizedStable * ts.normalizer / BASE_27 > collatInfo.stablecoinCap) revert AboveCap();
}
```

**Recommended Mitigation:** Add cap enforcement in the increase path:
```diff
// In LibSetters.adjustStablecoins
if (increase) {
    newCollateralNormalizedStable += uint216(normalizedAmount);
    newNormalizedStables += uint216(normalizedAmount);

+   if (newCollateralNormalizedStable * ts.normalizer / BASE_27 > collatInfo.stablecoinCap) {
+       revert AboveCap();
+   }
}
```

**Parallel**
Fixed in commit [7df01b8](https://github.com/parallel-protocol/parallel-parallelizer/commit/7df01b8df43f32dabf1e5dcf19ebe6ae2f9060d3#diff-41e3c405851499899c192341a0bd4b5587ba64730ba738b5db5ebba0a08de5c2) && commit [f41738d](https://github.com/parallel-protocol/parallel-parallelizer/commit/f41738d754a541a06aef4fd9037bc9b1fd08b755)

**Cyfrin:** Verified. Implemented a check to validate that `stablecoinCap` is not bypassed.

## [M-30] `Accountable Open Term` manual interest rate proposal is unbounded
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** The manual interest rate path can propose/queue an interest rate without enforcing an upper bound. By contrast, the DVN publishing path enforces a cap when applying rates:

* DVN flow: `AccountableOpenTerm::publishRate(uint256 newRate)` checks `newRate` against `MAX_PUBLISH_RATE` before applying it.
* Manual flow: `AccountableOpenTerm::proposeInterestRate(...)` queues a pending rate, and `approveInterestRateChange()` applies it, but the queued rate is not capped.

**Recommended Mitigation:** Add the same bounds check in `proposeInterestRate(...)` (preferred), so invalid/extreme rates cannot be queued.

**Accountable:** Fixed in commit [`4a737a6`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/4a737a63a92cff754a0e712ce5f8124f601829c1)

**Cyfrin:** Verified.

## [M-31] Superfluous vault support validation can be removed from `p USDe Depositor::deposit`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** If the caller to `pUSDeDepositor::deposit` attempts to deposit a vault token that is not `USDe` or one of those preconfigured with an auto swap path, it will first query `MetaVault::isAssetSupported`:

```solidity
    function deposit(IERC20 asset, uint256 amount, address receiver) external returns (uint256) {
        address user = _msgSender();
        ...
        IMetaVault vault = IMetaVault(address(pUSDe));
@>      if (vault.isAssetSupported(address(asset))) {
            SafeERC20.safeTransferFrom(asset, user, address(this), amount);
            asset.approve(address(vault), amount);
            return vault.deposit(address(asset), amount, receiver);
        }
@>      revert InvalidAsset(address(asset));
    }
```

If the specified vault token fails all validation then it falls through to the `InvalidAsset` custom error; however, this is not strictly necessary as `MetaVault::deposit` already performs the same validation within `MetaVault::requireSupportedVault`:

```solidity
    function deposit(address token, uint256 tokenAssets, address receiver) public virtual returns (uint256) {
        if (token == asset()) {
            return deposit(tokenAssets, receiver);
        }
@>      requireSupportedVault(token);
        ...
    }

    function requireSupportedVault(address token) internal view {
        address vaultAddress = assetsMap[token].asset;
        if (vaultAddress == address(0)) {
@>          revert UnsupportedAsset(token);
        }
    }
```

**Recommended Mitigation:** If it is not intentionally desired to fail early, consider removing the superfluous validation to save gas in the happy path case:

```diff
function deposit(IERC20 asset, uint256 amount, address receiver) external returns (uint256) {
        address user = _msgSender();
        ...
        IMetaVault vault = IMetaVault(address(pUSDe));
--      if (vault.isAssetSupported(address(asset))) {
            SafeERC20.safeTransferFrom(asset, user, address(this), amount);
            asset.approve(address(vault), amount);
            return vault.deposit(address(asset), amount, receiver);
--      }
--      revert InvalidAsset(address(asset));
    }
```

**Strata:** Fixed in commit [7f0c5dc](https://github.com/Strata-Money/contracts/commit/7f0c5dc54d1230589e2d9403b69effd64fb35227).

**Cyfrin:** Verified.

## [M-32] Use `Safe ERC20::force Approve` instead of standard `IERC20::approve`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Use [`SafeERC20::forceApprove`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/utils/SafeERC20.sol#L101-L108) when dealing with a range of potential tokens instead of standard `IERC20::approve`:
```solidity
predeposit/yUSDeDepositor.sol
58:        pUSDe.approve(address(yUSDe), amount);

predeposit/pUSDeVault.sol
178:        USDe.approve(address(sUSDe), USDeAssets);

predeposit/pUSDeDepositor.sol
86:            asset.approve(address(vault), amount);
98:        sUSDe.approve(address(pUSDe), amount);
110:        USDe.approve(address(pUSDe), amount);
122:        token.approve(swapInfo.router, amount);
```

**Strata:** Fixed in commit [f258bdc](https://github.com/Strata-Money/contracts/commit/f258bdcc49b87a2f8658b150bc3e3597a5187816).

**Cyfrin:** Verified.

## [M-33] `Securitize Amm Nav Provider` violates core AMM invariant that `k` should never decrease
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Both `SecuritizeAmmNavProvider::_curveBuy` and `_curveSell` round down when calculating new reserves:
```solidity
// `_curveBuy`
newQuote = Y + amountInQuote;
newBase = kLocal / newQuote; // @audit rounds down, k decreases

// `_curveSell`
newBase = X + amountInBase;
newQuote = kLocal / newBase; // @audit rounds down, k decreases
```
This causes users to receive slightly more output than mathematically correct and also `k` to effectively decrease over time.

Best practice is to have an invariant that `k` never decreases (as can be seen in [`UniswapV2Pair::swap`](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L182)). I.e. round in favor of the protocol.

**Impact:** Dust-level value leakage per trade; minimal practical impact due to virtual AMM design and periodic resets.

**Recommended Mitigation:** Consider explicitly rounding up using OZ [Math::ceilDiv](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/Math.sol#L183-L197).

**Securitize:** Fixed in commit [04d2392](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/04d2392c4944aead08bf7a4793fd57e625918910).

**Cyfrin:** Verified.

## [M-34] Missing zero output validation in `Securitize Amm Nav Provider` quote and buy functions
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** `SecuritizeAmmNavProvider::quoteBuyBase, quoteSellBase, executeBuyBase, executeSellBase` lack validation that output values are non-zero. Apart from issues already mentioned where rounding down to zero can occur, there are multiple other calculation points which can result in the final return values of these functions round down to zero:

**1. `baseOut` in buy operations:**
```solidity
baseOut = (amountInQuote * WAD) / rawExecPriceWad;
```

Rounds to zero when `amountInQuote < rawExecPriceWad / 1e18`. For example, if `rawExecPriceWad = 100e18` (100 quote per base), any `amountInQuote < 100` produces `baseOut = 0`.

**2. `quoteOut` in sell operations:**
```solidity
quoteOut = (amountInBase * rawExecPriceWad) / WAD;
```

Rounds to zero when `amountInBase * rawExecPriceWad < 1e18`. For example, if `rawExecPriceWad = 1e16` (0.01 quote per base), any `amountInBase < 100` produces `quoteOut = 0`.

**3. `execPrice` in both directions:**
```solidity
uint256 scaleDown = 10 ** (18 - d);
execPrice = rawExecPriceWad / scaleDown;
```

Rounds to zero when `rawExecPriceWad < scaleDown`. For a 6-decimal asset, `scaleDown = 1e12`, so any `rawExecPriceWad < 1e12` produces `execPrice = 0`.

These conditions can occur through:
- Small trade amounts relative to price
- Extreme price deviations from curve imbalance (as described in another issue)
- Low-decimal assets with unfavorable price scaling

**Impact:** When zero outputs are returned the potential negative outcomes include:

1. **Silent fund loss** — A router calling `executeBuyBase` or `executeSellBase` may transfer real tokens. The NAV provider returns `baseOut = 0` or `quoteOut = 0`, but the router may not distinguish this from a legitimate trade. In a worst-case scenario the user could send tokens and receive nothing, though this is unlikely.

2. **State corruption** — Virtual reserves update based on a trade that produced zero output:
```solidity
   baseReserves = newBase;
   quoteReserves = newQuote;
   k = newBase * newQuote;
```
The AMM state reflects input that was "absorbed" without corresponding output.

3. **Broken invariants** — The constant-product invariant assumes balanced input/output. Zero-output trades violate this assumption and skew future pricing.

4. **Misleading quotes** — The view functions `quoteBuyBase` and `quoteSellBase` return zero outputs without reverting, causing off-chain integrations to display incorrect expectations.

**Recommended Mitigation:** Add zero-output validation to all four functions:
```diff
function executeBuyBase(
    uint256 amountInQuote,
    uint256 anchorPriceWad,
    uint8 marketStatus
) external onlyRole(EXECUTOR_ROLE) returns (uint256 baseOut, uint256 execPrice) {
    // ... existing logic ...
    if (marketStatus == CLOSED_MARKET) {
        (baseOut, rawExecPriceWad) = _pricingFromCurveBuy(amountInQuote, curvePriceWad, anchorPriceWad);
    } else if (marketStatus == OPEN_MARKET) {
        rawExecPriceWad = anchorPriceWad;
        baseOut = (amountInQuote * WAD) / rawExecPriceWad;
    } else {
        revert("invalid market status");
    }

+   require(baseOut > 0, "baseOut=0");

    baseReserves = newBase;
    quoteReserves = newQuote;
    k = newBase * newQuote;

    _recordTrade(marketStatus, anchorPriceWad);

    uint8 d = asset.decimals();
    require(d <= 18, "decimals > 18");
    uint256 scaleDown = 10 ** (18 - d);

    execPrice = rawExecPriceWad / scaleDown;

+   require(execPrice > 0, "execPrice=0");

    emit ExecuteBuy(msg.sender, amountInQuote, baseOut, rawExecPriceWad);
}

function executeSellBase(
    uint256 amountInBase,
    uint256 anchorPriceWad,
    uint8 marketStatus
) external onlyRole(EXECUTOR_ROLE) returns (uint256 quoteOut, uint256 execPrice) {
    // ... existing logic ...
    if (marketStatus == CLOSED_MARKET) {
        (quoteOut, rawExecPriceWad) = _pricingFromCurveSell(amountInBase, curvePriceWad, anchorPriceWad);
    } else if (marketStatus == OPEN_MARKET) {
        rawExecPriceWad = anchorPriceWad;
        quoteOut = (amountInBase * rawExecPriceWad) / WAD;
    } else {
        revert("invalid market status");
    }

+   require(quoteOut > 0, "quoteOut=0");

    baseReserves = newBase;
    quoteReserves = newQuote;
    k = newBase * newQuote;

    _recordTrade(marketStatus, anchorPriceWad);

    uint8 d = asset.decimals();
    require(d <= 18, "decimals > 18");
    uint256 scaleDown = 10 ** (18 - d);

    execPrice = rawExecPriceWad / scaleDown;

+   require(execPrice > 0, "execPrice=0");

    emit ExecuteSell(msg.sender, amountInBase, quoteOut, rawExecPriceWad);
}

function quoteBuyBase(
    uint256 amountInQuote,
    uint256 anchorPriceWad,
    uint8 marketStatus
) external view returns (uint256 baseOut, uint256 execPrice) {
    // ... existing logic ...
+   require(baseOut > 0, "baseOut=0");

    execPrice = rawExecPriceWad / scaleDown;
+   require(execPrice > 0, "execPrice=0");
}

function quoteSellBase(
    uint256 amountInBase,
    uint256 anchorPriceWad,
    uint8 marketStatus
) external view returns (uint256 quoteOut, uint256 execPrice) {
    // ... existing logic ...
+   require(quoteOut > 0, "quoteOut=0");

    execPrice = rawExecPriceWad / scaleDown;
+   require(execPrice > 0, "execPrice=0");
}
```

**Securitize:** Fixed in commit [affb350](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/affb35097f9b638d6b1cfe4f58b42fdf79bc8778).

**Cyfrin:** Verified.

## [M-35] Token name update breaks EIP-712 Domain Separator for permit functionality
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** The EIP-712 domain separator is initialized once during contract deployment in `__ERC20PermitMixin_init()` with the initial token name:
```solidity
function __ERC20PermitMixin_init(string memory name_) internal onlyInitializing {
    __EIP712_init(name_, "1");  // Domain separator set with initial name
    __Nonces_init();
}
```

However, `StandardToken` allows the Master role to update the token name via `updateNameAndSymbol`:
```solidity
function updateNameAndSymbol(string calldata _name, string calldata _symbol) external onlyMaster {
    // ...
    name = _name;  // Name updated but EIP-712 domain separator NOT updated
    // ...
}
```

**Impact:** When the token name is changed, the EIP-712 domain separator remains unchanged. This creates a mismatch between what wallets use to generate permit signatures (the current token name) and what the contract uses to validate them (the original deployment name). Potential impact:

1. **Complete permit functionality breakage**: After any name change, 100% of newly generated permit signatures will fail validation with "Permit: invalid signature"
2. **Silent failure mode**: Users and integrations have no programmatic way to detect this mismatch; the error message doesn't indicate it's a domain separator issue
3. **All dynamic integrations break**: Any dApp that fetches `token.name()` to generate permit signatures will automatically break after a name update
4. **Inconsistent behavior**: Permits signed before the name change continue to work, while new ones fail, creating a confusing split state
5. **No easy recovery path**: Fixing this requires either a contract upgrade or instructing all users/integrations to use the deprecated name (breaking EIP-2612 expectations)

**Proof of Concept:** Add a new file `test/change.name.permit.test.ts`:
```typescript
import { expect } from 'chai';
import { loadFixture } from '@nomicfoundation/hardhat-toolbox/network-helpers';
import hre from 'hardhat';
import {
  deployDSTokenRegulated,
  INVESTORS,
} from './utils/fixture';
import { buildPermitSignature, registerInvestor } from './utils/test-helper';

describe('M-01: Token Name Update Breaks Permit Functionality - Proof of Concept', function() {

  describe('Demonstrating the Vulnerability', function() {

    it('CRITICAL: Permit fails after name update - All new permits become invalid', async function() {
      const [owner, spender] = await hre.ethers.getSigners();
      const { dsToken } = await loadFixture(deployDSTokenRegulated);

      // Initial state: Token name is "Token Example 1"
      const originalName = await dsToken.name();
      expect(originalName).to.equal('Token Example 1');

      // ✅ STEP 1: Permit works BEFORE name change
      console.log('\n--- BEFORE NAME CHANGE ---');
      const deadline1 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const value = 100;
      const message1 = {
        owner: owner.address,
        spender: spender.address,
        value,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline1,
      };

      // User signs with original name "Token Example 1"
      const sig1 = await buildPermitSignature(
        owner,
        message1,
        originalName,  // Uses "Token Example 1"
        await dsToken.getAddress()
      );

      // Permit succeeds with original name
      await dsToken.permit(owner.address, spender.address, value, deadline1, sig1.v, sig1.r, sig1.s);
      console.log('✅ Permit with original name: SUCCESS');
      expect(await dsToken.allowance(owner.address, spender.address)).to.equal(value);

      // ⚠️ STEP 2: Master updates token name
      console.log('\n--- NAME CHANGE ---');
      const newName = 'Token Example 2 - Updated';
      await dsToken.updateNameAndSymbol(newName, 'TX2');
      expect(await dsToken.name()).to.equal(newName);
      console.log(`Token name updated: "${originalName}" → "${newName}"`);

      // ❌ STEP 3: Permit FAILS after name change
      console.log('\n--- AFTER NAME CHANGE ---');
      const deadline2 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message2 = {
        owner: owner.address,
        spender: spender.address,
        value: 200,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline2,
      };

      // User's wallet fetches current name and generates signature
      const currentName = await dsToken.name(); // Returns "Token Example 2 - Updated"
      console.log(`User's wallet uses current name: "${currentName}"`);

      const sig2 = await buildPermitSignature(
        owner,
        message2,
        currentName,  // Uses NEW name "Token Example 2 - Updated"
        await dsToken.getAddress()
      );

      // 🚨 PERMIT FAILS - Domain separator mismatch!
      await expect(
        dsToken.permit(owner.address, spender.address, 200, deadline2, sig2.v, sig2.r, sig2.s)
      ).to.be.revertedWith('Permit: invalid signature');

      console.log('❌ Permit with new name: FAILED - "Permit: invalid signature"');
      console.log('\n🚨 VULNERABILITY CONFIRMED: All new permits fail after name change!');
    });

    it('IMPACT: Old permits continue working while new ones fail - Inconsistent behavior', async function() {
      const [owner, spender] = await hre.ethers.getSigners();
      const { dsToken } = await loadFixture(deployDSTokenRegulated);

      const originalName = await dsToken.name();

      // Generate permit signature BEFORE name change
      const deadline1 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message1 = {
        owner: owner.address,
        spender: spender.address,
        value: 100,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline1,
      };

      const oldSignature = await buildPermitSignature(
        owner,
        message1,
        originalName,
        await dsToken.getAddress()
      );

      // Master changes the name
      await dsToken.updateNameAndSymbol('Token Example 2', 'TX2');
      const newName = await dsToken.name();

      // ✅ OLD permit (signed before name change) still works!
      await dsToken.permit(
        owner.address,
        spender.address,
        100,
        deadline1,
        oldSignature.v,
        oldSignature.r,
        oldSignature.s
      );
      console.log('✅ Old permit (signed before name change): SUCCESS');

      // ❌ NEW permit (signed after name change) fails!
      const deadline2 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message2 = {
        owner: owner.address,
        spender: spender.address,
        value: 200,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline2,
      };

      const newSignature = await buildPermitSignature(
        owner,
        message2,
        newName,  // Uses new name
        await dsToken.getAddress()
      );

      await expect(
        dsToken.permit(owner.address, spender.address, 200, deadline2, newSignature.v, newSignature.r, newSignature.s)
      ).to.be.revertedWith('Permit: invalid signature');

      console.log('❌ New permit (signed after name change): FAILED');
      console.log('\n🚨 INCONSISTENT STATE: Split behavior based on signature timing!');
    });

    it('IMPACT: DApp integrations break silently', async function() {
      const [owner, spender] = await hre.ethers.getSigners();
      const { dsToken } = await loadFixture(deployDSTokenRegulated);

      // Simulate a DApp that dynamically fetches token name
      async function dAppGeneratePermitSignature(tokenContract, ownerSigner, spenderAddress, value, deadline) {
        // Standard DApp implementation: fetch name dynamically
        const tokenName = await tokenContract.name();
        const tokenAddress = await tokenContract.getAddress();

        const message = {
          owner: ownerSigner.address,
          spender: spenderAddress,
          value,
          nonce: await tokenContract.nonces(ownerSigner.address),
          deadline,
        };

        return await buildPermitSignature(ownerSigner, message, tokenName, tokenAddress);
      }

      // ✅ DApp works fine initially
      const deadline1 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const sig1 = await dAppGeneratePermitSignature(dsToken, owner, spender.address, 100, deadline1);

      await dsToken.permit(owner.address, spender.address, 100, deadline1, sig1.v, sig1.r, sig1.s);
      console.log('✅ DApp integration BEFORE name change: SUCCESS');

      // Master updates name
      await dsToken.updateNameAndSymbol('Token Example 2', 'TX2');
      console.log('\n⚠️  Token name updated to "Token Example 2"');

      // ❌ DApp breaks - it fetches the NEW name but contract validates against OLD name
      const deadline2 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const sig2 = await dAppGeneratePermitSignature(dsToken, owner, spender.address, 200, deadline2);

      await expect(
        dsToken.permit(owner.address, spender.address, 200, deadline2, sig2.v, sig2.r, sig2.s)
      ).to.be.revertedWith('Permit: invalid signature');

      console.log('❌ DApp integration AFTER name change: FAILED');
      console.log('🚨 DApp has NO way to detect this issue programmatically!');
    });

    it('WORKAROUND: Permit succeeds if user manually uses ORIGINAL name (terrible UX)', async function() {
      const [owner, spender] = await hre.ethers.getSigners();
      const { dsToken } = await loadFixture(deployDSTokenRegulated);

      const originalName = await dsToken.name(); // "Token Example 1"

      // Master updates name
      await dsToken.updateNameAndSymbol('Token Example 2', 'TX2');

      // ❌ Using current name fails
      const deadline1 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message1 = {
        owner: owner.address,
        spender: spender.address,
        value: 100,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline1,
      };

      const sigWithNewName = await buildPermitSignature(
        owner,
        message1,
        await dsToken.name(),  // "Token Example 2" (current)
        await dsToken.getAddress()
      );

      await expect(
        dsToken.permit(owner.address, spender.address, 100, deadline1, sigWithNewName.v, sigWithNewName.r, sigWithNewName.s)
      ).to.be.revertedWith('Permit: invalid signature');
      console.log('❌ Permit with current name "Token Example 2": FAILED');

      // ✅ Using ORIGINAL name works (but terrible UX)
      const deadline2 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message2 = {
        owner: owner.address,
        spender: spender.address,
        value: 200,
        nonce: await dsToken.nonces(owner.address),
        deadline: deadline2,
      };

      const sigWithOriginalName = await buildPermitSignature(
        owner,
        message2,
        originalName,  // "Token Example 1" (original)
        await dsToken.getAddress()
      );

      await dsToken.permit(
        owner.address,
        spender.address,
        200,
        deadline2,
        sigWithOriginalName.v,
        sigWithOriginalName.r,
        sigWithOriginalName.s
      );
      console.log('✅ Permit with ORIGINAL name "Token Example 1": SUCCESS');
      console.log('\n🚨 WORKAROUND: Users must use deprecated name - breaks EIP-2612 expectations!');
    });

    it('VERIFICATION: DOMAIN_SEPARATOR remains unchanged after name update', async function() {
      const { dsToken } = await loadFixture(deployDSTokenRegulated);

      const originalName = 'Token Example 1';

      // Get domain separator before name change
      const domainSeparatorBefore = await dsToken.DOMAIN_SEPARATOR();
      console.log('Domain separator BEFORE name change:', domainSeparatorBefore);

      // Compute expected domain separator with original name
      const expectedDomainBefore = hre.ethers.TypedDataEncoder.hashDomain({
        version: '1',
        name: originalName,
        verifyingContract: await dsToken.getAddress(),
        chainId: (await hre.ethers.provider.getNetwork()).chainId,
      });

      expect(domainSeparatorBefore).to.equal(expectedDomainBefore);

      // Update name
      await dsToken.updateNameAndSymbol('Token Example 2', 'TX2');
      const newName = await dsToken.name();
      console.log(`\nName updated: "${originalName}" → "${newName}"`);

      // Get domain separator after name change
      const domainSeparatorAfter = await dsToken.DOMAIN_SEPARATOR();
      console.log('Domain separator AFTER name change:', domainSeparatorAfter);

      // 🚨 DOMAIN SEPARATOR UNCHANGED!
      expect(domainSeparatorAfter).to.equal(domainSeparatorBefore);
      console.log('\n🚨 VERIFIED: Domain separator did NOT update with new name!');

      // Compute what the domain separator SHOULD be with new name
      const expectedDomainWithNewName = hre.ethers.TypedDataEncoder.hashDomain({
        version: '1',
        name: newName,
        verifyingContract: await dsToken.getAddress(),
        chainId: (await hre.ethers.provider.getNetwork()).chainId,
      });

      console.log('\nExpected domain with NEW name:', expectedDomainWithNewName);
      console.log('Actual domain separator:      ', domainSeparatorAfter);
      console.log('Match:', domainSeparatorAfter === expectedDomainWithNewName ? '✅' : '❌');

      // They don't match - this is the root cause
      expect(domainSeparatorAfter).to.not.equal(expectedDomainWithNewName);
    });
  });

  describe('Real-World Attack Scenarios', function() {

    it('SCENARIO 1: Protocol rebranding breaks all user permits', async function() {
      const [owner, user1, user2, dex] = await hre.ethers.getSigners();
      const { dsToken, registryService } = await loadFixture(deployDSTokenRegulated);

      // Setup investors
      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, user1, registryService);
      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_2, user2, registryService);
      await dsToken.issueTokens(user1, 1000);

      console.log('\n📊 SCENARIO: Token rebranding from "Token Example 1" to "Acme Securities Token"');

      // Before rebrand: User1 can use permit to approve DEX
      const deadline1 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message1 = {
        owner: user1.address,
        spender: dex.address,
        value: 500,
        nonce: await dsToken.nonces(user1.address),
        deadline: deadline1,
      };

      const sig1 = await buildPermitSignature(
        user1,
        message1,
        await dsToken.name(),
        await dsToken.getAddress()
      );

      await dsToken.permit(user1.address, dex.address, 500, deadline1, sig1.v, sig1.r, sig1.s);
      console.log('✅ User1 successfully approved DEX using permit (before rebrand)');

      // 🏢 PROTOCOL REBRANDS
      await dsToken.updateNameAndSymbol('Acme Securities Token', 'AST');
      console.log('\n🏢 Protocol rebrands to "Acme Securities Token"');

      // After rebrand: All new permits fail
      const deadline2 = BigInt(Math.floor(Date.now() / 1000) + 3600);
      const message2 = {
        owner: user2.address,
        spender: dex.address,
        value: 500,
        nonce: await dsToken.nonces(user2.address),
        deadline: deadline2,
      };

      await dsToken.issueTokens(user2, 1000);

      const sig2 = await buildPermitSignature(
        user2,
        message2,
        await dsToken.name(), // Uses new name
        await dsToken.getAddress()
      );

      await expect(
        dsToken.permit(user2.address, dex.address, 500, deadline2, sig2.v, sig2.r, sig2.s)
      ).to.be.revertedWith('Permit: invalid signature');

      console.log('❌ User2 permit FAILS after rebrand');
      console.log('🚨 Impact: 100% of new users cannot use gasless approvals!');
      console.log('📞 Result: Support tickets flood in, users confused');
    });

    it('SCENARIO 2: Front-end integration breaks without warning', async function() {
      const [owner, user, spender] = await hre.ethers.getSigners();
      const { dsToken, registryService } = await loadFixture(deployDSTokenRegulated);

      await registerInvestor(INVESTORS.INVESTOR_ID.INVESTOR_ID_1, user, registryService);
      await dsToken.issueTokens(user, 1000);

      console.log('\n🌐 SCENARIO: Frontend dApp integration');

      // Simulate frontend code
      const frontendPermitFlow = async (token, fromUser, toSpender, amount) => {
        // Standard EIP-2612 implementation in frontend
        const name = await token.name(); // Fetch current name dynamically
        const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);
        const nonce = await token.nonces(fromUser.address);

        const message = {
          owner: fromUser.address,
          spender: toSpender,
          value: amount,
          nonce,
          deadline,
        };

        const signature = await buildPermitSignature(
          fromUser,
          message,
          name,
          await token.getAddress()
        );

        return { deadline, signature };
      };

      // ✅ Frontend works initially
      const { deadline: d1, signature: s1 } = await frontendPermitFlow(dsToken, user, spender.address, 100);
      await dsToken.permit(user.address, spender.address, 100, d1, s1.v, s1.r, s1.s);
      console.log('✅ Frontend permit flow: SUCCESS (initial deployment)');

      // Master updates name (e.g., for compliance reasons)
      await dsToken.updateNameAndSymbol('Compliant Token v2', 'CTv2');
      console.log('\n⚠️  Master updates name for compliance');

      // ❌ Frontend breaks silently
      const { deadline: d2, signature: s2 } = await frontendPermitFlow(dsToken, user, spender.address, 200);
      await expect(
        dsToken.permit(user.address, spender.address, 200, d2, s2.v, s2.r, s2.s)
      ).to.be.revertedWith('Permit: invalid signature');

      console.log('❌ Frontend permit flow: BROKEN (after name update)');
      console.log('🚨 Error message gives NO hint about name mismatch');
      console.log('😰 Users see "Invalid signature" and blame wallet/frontend');
    });
  });
});
```

Run with: `npx hardhat test --grep "Token Name Update Breaks Permit Functionality"`

**Recommended Mitigation:** The most elegant solution appears to be:
* `StandardToken` defines a `_name` function that just returns `name`:
```solidity
    function _name() internal view virtual override returns (string memory) {
        return name;  // Returns current storage variable
    }
```

* `ERC20PermitMixin` overrides `EIP712Upgradeable::_EIP712Name` to call this function:
```solidity
    // ✨ Override to return dynamic name instead of cached name
    function _EIP712Name() internal view virtual override returns (string memory) {
        return _name();  // Calls abstract function implemented by StandardToken
    }

    // Abstract function for StandardToken to implement
    function _name() internal view virtual returns (string memory);
```

**Securitize:** Fixed in commit [4ebb9b7](https://github.com/securitize-io/dstoken/commit/4ebb9b706e7570ba0f0e295205c79949c16f1b0c).

**Cyfrin:** Verified.

\clearpage

## [M-36] Shared configuration parameters across different asset types in vault deployers leads to incorrect pricing and fee calculations
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `VaultDeployer` and `SecuritizeVaultDeployer` contracts maintain shared configuration parameters (`navProvider`, `feeManager`, `redemptionAddress`) that are applied to all deployed vaults regardless of their underlying asset type. When `SegregatedVaultDeployer::deploy()` or `SecuritizeVaultDeployer::deploy()` is called with different `assetToken` and `liquidationToken` parameters to support various vault types, the same `navProvider` is used across all deployments. This creates a critical architectural flaw because different RWA assets require asset-specific NAV providers for accurate valuation.

In `SecuritizeVaultV2`, the `navProvider.rate()` is extensively used in critical functions like `_convertToShares()`, `_convertToAssets()`, and `getShareValue()` to determine share-to-asset conversion ratios. When vaults for different assets (e.g., real estate tokens vs commodity tokens) share the same NAV provider, the pricing calculations become incorrect for at least one of the asset types.

Similar issues exist with:
- `SecuritizeVaultDeployer.feeManager` - applies the same fee logic to all asset types
- `SecuritizeVaultDeployer.redemptionAddress` - uses the same redemption contract for different assets that may require different redemption mechanisms

Note that `SegregatedVault` does not use `navProvider` in its calculations, so it is not directly affected by this issue, but the architecture problem persists in the deployment pattern.

**Impact:** Users depositing assets into vaults with incorrect NAV providers will receive wrong share amounts, leading to economic losses and potential exploitation opportunities where attackers can deposit low-value assets but receive shares calculated using high-value asset NAV rates.

```solidity
// In SecuritizeVaultDeployer::deploy()
BeaconProxy proxy = new BeaconProxy(
    upgradeableBeacon,
    abi.encodeWithSelector(
        SecuritizeVaultV2(payable(address(0))).initializeV2.selector,
        name,
        symbol,
        assetToken,      // Different per deployment
        redemptionAddress, // Same for all deployments - ISSUE
        liquidationToken,
        navProvider,     // Same for all deployments - ISSUE
        feeManager       // Same for all deployments - ISSUE
    )
);
```

**Recommended Mitigation:** We understand that these parameters are meant to be managed by only the admin, and that is why it's managed by the contract instead of allowing users to specify in the deploy function. We recommend the team consider either of below two solutions.

1. Modify the vault deployer architecture to support asset-specific configurations. Below is an example implementation.

```diff
+ mapping(address => address) public assetNavProviders;
+ mapping(address => address) public assetFeeManagers;
+ mapping(address => address) public assetRedemptionAddresses;

+ function setAssetConfiguration(
+     address assetToken,
+     address navProvider,
+     address feeManager,
+     address redemptionAddress
+ ) external onlyRole(DEFAULT_ADMIN_ROLE) {
+     assetNavProviders[assetToken] = navProvider;
+     assetFeeManagers[assetToken] = feeManager;
+     assetRedemptionAddresses[assetToken] = redemptionAddress;
+ }
```
2. If the intention is to have one deployer for every pair of asset token ad liquid token, store the asset token address and liquid token address in the deployer with the nav provider together and remove the `assetToken` adn `liquidToken` parameters from the deploy function.

**Securitize:** Fixed in commit [05044b](https://github.com/securitize-io/bc-rwa-seg-wrap-sc/commit/05044b3f10d66d82ad134fc73f712c62ba5796e2).

**Cyfrin:** Verified.

\clearpage

## [M-37] Enforce minimum transaction amounts in `Staking Vault`
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Some elaborate vault hacks have involved performing vault transactions using very small amounts such as 1 wei in order to manipulate the vault via rounding.

Normal users will never perform transactions using such small amounts; hence consider enforcing minimum transaction amounts to deprive attackers of this potential attack path.

Since hBTC uses 8 decimals and is 1:1 redeemable for BTC:
* 100000000 = 1 BTC ($118K)
* 10000 = 0.0001 BTC($11.87)

Consider making the minimum transaction limit a configurable parameter that the admin can change as the price of BTC fluctuates, so that it can remain around ~$10 (or even higher if preferred).

The best way to enforce this is likely overriding `ERC4626::_deposit, _withdraw` and reverting inside them if `assets` is smaller than the minimum transaction amount.

**Syntetika:**
Fixed in commit [5ba3c19](https://github.com/SyntetikaLabs/monorepo/commit/5ba3c199cf571679503f8f472769c8efe869a001).

**Cyfrin:** Verified.

## [M-39] Lack of check for 0 shares minted
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** `previewDeposit(assets)` can legitimately return `0` shares for tiny deposits due to rounding and/or deposit fees. If the deposit path doesn’t guard against this, a user could transfer assets to the vault and receive 0 shares (an unintended “donation”).

Consider adding a check for 0 shares:
```solidity
function previewDeposit(uint256 assets) public view virtual override returns (uint256) {
    uint256 fee = _extractFeeFromTotal(assets, depositFeeBps);
    require(fee < assets, "Deposit fee exceeds assets");
    uint256 shares = super.previewDeposit(assets - fee);
    require(shares > 0, "0 shares");
    return shares;
}
```


**Button:** Fixed in commit [`9cde24c`](https://github.com/buttonxyz/button-protocol/commit/9cde24caa4b3f5f37a059bb2fde172cfa374d3a9)

**Cyfrin:** Verified. `previewDeposit` now checks that `> 0 shares` are minted.

\clearpage

## [M-40] `Apr Pair Feed::get Round Data` can return data for a different round than the specified
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** When updating round data on the `AprPairFeed`, the data is saved in the `rounds` mapping, which is accessed via the calculated `roundIdx`. The way in which the `roundIdx` is derived causes it to be repeated every 20 updates, from 0 to 20, over and over. This means that an older  `roundIdx` would eventually calculate the same `roundIdx` as a newer one. This can cause the problem that when retrieving data for a specific roundId, `AprPairFeed::getRoundData` returns data for a newer roundId.

```solidity
    function updateRoundDataInner(int64 aprTarget, int64 aprBase, uint64 t) internal {
        ...
        uint64 roundId = (latestRoundId + 1);
@>      uint64 roundIdx = roundId % roundsCap;

        latestRoundId = roundId;
        latestRound = TRound({
            aprTarget: aprTarget,
            aprBase: aprBase,
            updatedAt: t,
            answeredInRound: roundId
        });
@>      rounds[roundIdx] = latestRound;

        emit AnswerUpdated(aprTarget, aprBase, roundId, t);
    }

    function getRoundData(uint64 roundId) public view returns (TRound memory) {
@>      uint64 roundIdx = roundId % roundsCap;
        TRound memory round = rounds[roundIdx];
        require(round.updatedAt > 0, "No data present");
@>      return round;
    }

```

**Recommended Mitigation:** Consider validating that the data read from the `rounds` mapping matches the specified roundId.
```diff
    function getRoundData(uint64 roundId) public view returns (TRound memory) {
        uint64 roundIdx = roundId % roundsCap;
        TRound memory round = rounds[roundIdx];
        require(round.updatedAt > 0, "No data present");
+       require(round.answeredInRound == roundId, "old round");
        return round;
    }
```

**Strata:**
Fixed in commit [233e3d](https://github.com/Strata-Money/contracts-tranches/commit/233e3d398b9bb52929170572fed69d1083ee1ce1) by verifying the queried data corresponds to the same requested `roundId`.

**Cyfrin:** Verified.

## [M-41] Missing Validation of Fallback APR Values in `Apr Pair Feed::latest Round Data`
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** `AprPairFeed::latestRoundData` fetches APRs from a preferred source (feed or strategy provider). If the feed is stale, it falls back to the strategy provider via `provider.getAprPair()` but does not validate the returned values (e.g., via `ensureValidAprs` or bounds checks), unlike potential validations in the feed path. This allows potentially invalid values to be used

```solidity
function latestRoundData() external view returns (TRound memory) {
        TRound memory round = latestRound;

        if (sourcePref == ESourcePref.Feed) {
            uint256 deltaT = block.timestamp - uint256(round.updatedAt);
            if (deltaT < roundStaleAfter) {
                return round;
            }
            // falls back to strategy ↓
        }

        (int64 aprTarget, int64 aprBase, uint64 t1) = provider.getAprPair();
        return TRound({
            aprTarget: aprTarget,
            aprBase: aprBase,
            updatedAt: t1,
            answeredInRound: latestRoundId + 1
        });
    }
```


**Recommended Mitigation:** Add validation after fallback fetch, similar to feed bounds:
```diff
        (int64 aprTarget, int64 aprBase, uint64 t1) = provider.getAprPair();
+       // Add validation, e.g.:
+       ensureValid(aprTarget);
+       ensureValid(aprBase);
        return TRound({
            aprTarget: aprTarget,
            aprBase: aprBase,
            updatedAt: t1,
            answeredInRound: latestRoundId + 1
        });
```

**Strata:**
Fixed in commit [1c4009a](https://github.com/Strata-Money/contracts-tranches/commit/1c4009a61f6aa1802b0a1541c6e63b096d601d1b) by validating `aprTarget` and `aprBase`.

**Cyfrin:** Verified.

## [M-42] `Basis Trade Tailor::core Deposit Wallet` is not blocked for adapters calls
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** `BasisTradeTailor::executeAdapter` blocks `coreWriter` but not `coreDepositWallet`:

```solidity
// BasisTradeTailor.sol:781
require(target != coreWriter, "Adapter cannot call coreWriter");
// No check for coreDepositWallet
```

`CoreDepositWallet.depositFor(address user, ...)` can send pocket USDC to arbitrary Core addresses. While adapters are trusted, this creates inconsistency in Core contract restrictions - if `coreWriter` is blocked for defense-in-depth, `coreDepositWallet` (which also interacts with Core) should be blocked too.

**Recommended Mitigation:**
```diff
-require(target != coreWriter, "Adapter cannot call coreWriter");
+require(target != coreWriter && target != coreDepositWallet, "Adapter cannot call Core contracts");
```

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

## [M-43] Adapter removal script lacks Safe-mode calldata output
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description**
`RemoveAdapterFromBasisTradeTailor.s.sol` does not follow the `SAFE_MODE` pattern used in other operational scripts (i.e., printing `to/value/data` calldata for multisig execution) and instead relies on direct execution flow.

Consider add a `SAFE_MODE` path that prints the encoded calldata (`to`, `value`, `data`) for `removeAdapter(adapter)`.

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

<!-- /Cyfrin Fixed Issues (Merged) -->
