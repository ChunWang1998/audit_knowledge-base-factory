# data-structure-consistency - Issues

- Count: 16

## F-2025-14458 - Mismatch Between Tier Assignment andEnumeration Breaks Tier Determinism
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The MemoryManager contract uses two fundamentally different approachesto handle tiering, which causes critical inconsistency in tier calculationand enumeration logic. Value-Based Tiering during insertion: stake tiers and downline tiersare determined by dividing the value (e.g., stakeId) by a constantTIER_SIZE function `addToTier(mapping(uint256 => uint256[])` storage tiers, uint256 value ) internal { uint256 tier = value / `TIER_SIZE`; tiers[tier].`push(value)`; } Count-Based Tier Enumeration during tier counting: the number oftiers is estimated by dividing the count of stakes or downlines by `TIER_SIZE` with rounding: function `getTierCount(uint256 totalCount)` internal pure returns (uint256) { return (totalCount + `TIER_SIZE` - 1) / `TIER_SIZE`; } ForExample: Consider Alice staking twice with stakeId values 1999 and 2000 1999 → assigned to tier 1 (since 1999 / 1000 = 1) 2000 → assigned to tier 2 (since 2000 / 1000 = 2) Since: userStakeCount[`msg.sender`] == 2 `getTierCount(2)` => (totalCount + `TIER_SIZE` - 1) / `TIER_SIZE` => 2 + 1000 - 1 / 1000 = 1 This result incorrectly implies only one tier is used, which conflicts withthe actual tier assignments. This design mismatch leads to incorrect and non-deterministic tiercounts that do not reflect: 27 The actual distribution of stake ids among tiers in the StakingAndRewards::`stake()` function and leads to the incorrect calculationof the maxTiers number that affects the paginated data generationprocess in the MemoryManager::`getPaginatedData()` function that has anegative impact on the StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` functions output data. The actual distribution of downlines among downline tiers in the Subcription::`_addDownlines`() which is utilized in the Subscription::`register()` function. Although the issue does not directly impact the financial components ofthe system, this discrepancy undermines the reliability and integrity of thetiering mechanism and may lead to downstream issues for systemintegrators, including frontend components and decentralized applications. Assets: `MemoryManager.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
It is recommended to: redesign the tier calculation logic to take into account situations whenuser stakes are in different tiers.provide a proper test suite covering all edge cases of the newfunctionality.document the intended behavior of the system. Resolution: Fixed in 825eaaf. The `_addDownlines`() function was redesigned to properlycalculate the downlineTierCount value as follows: uint256 actualTier = newUserId / `TIER_SIZE`; // Same formula as `addToTier()` 28 line 30 if (!tierUsed[current.id][level][actualTier]) { tierUsed[current.id][level][actualTier] = true; // Mark tier as used downlineTierCount[current.id][level]++; // Increment unique tier count } … In addition to that the functions MemoryManager::`getTierCount()`, MemoryManager::`getPaginatedData()`, StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` were removed from thecodebase. The calculation of the userStakeTierCount was removed from the StakingAndRewards::`stake()` function.

### 修補方式（實際）
Fixed in 825eaaf. The `_addDownlines`() function was redesigned to properlycalculate the downlineTierCount value as follows: uint256 actualTier = newUserId / `TIER_SIZE`; // Same formula as `addToTier()` 28 line 30 if (!tierUsed[current.id][level][actualTier]) { tierUsed[current.id][level][actualTier] = true; // Mark tier as used downlineTierCount[current.id][level]++; // Increment unique tier count } … In addition to that the functions MemoryManager::`getTierCount()`, MemoryManager::`getPaginatedData()`, StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` were removed from thecodebase. The calculation of the userStakeTierCount was removed from the StakingAndRewards::`stake()` function.

## F-2025-14443 - Uninitialized minWithdrawAmount Allows Zero-Amount Forced Withdrawal Requests To Block Queue Processing -Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The minWithdrawAmount state variable in InclusionQueue.sol is never initializedduring contract deployment, defaulting to 0. This allows any user to queuea forced withdrawal request with amount = 0, which passes all validationchecks in InclusionQueue.sol. However, when this request is processed, Pool.executeOnChainWithdrawal() explicitly requires amount > 0 and reverts.Due to the strict FIFO queue processing, this zero-amount requestpermanently blocks all subsequent forced withdrawal requests, completelydisabling the escape hatch mechanism. While minWithdrawAmount can be set via the setAmount() function, this providesno protection against the vulnerability. There is no check requiring setAmount() to be called before the queue becomes operational. Betweendeployment and the owner calling setAmount(), attackers can queue zero-amount requests This means even if the owner eventually sets minWithdrawAmount to a propervalue, the system can already be irreversibly compromised by zero-amount requests submitted during the unprotected window afterdeployment. Missing initialization: function initialize(address _usdcToken, address _governance, address _own er) external initializer { require(_usd

### 修補方式（實際）
initialize() function is modified to initialize minWithdrawAmount variable with 1in the commit 322258e. function initialize(address _usdcToken, address _governance, address _own er) external initializer { require(_usdcToken != address(0), Queue_Token0x()); require(_governance != address(0), Queue_Governance0x()); require(_owner != address(0), Queue_Owner0x()); __UUPSUpgradeable_init(); __ReentrancyGuard_init(); __Pausable_init(_owner); usdcToken = _usdcToken; governance = _governance; minWithdrawAmount = 1; } 24


## F-2025-13207 - User Funds Unexpectedly Transferred to Treasurydue to Arbitrary Transfer From Parameter - High
- 嚴重度：High
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The receivePayment function of the DOI_Treasury contract is part of thepayment system, allowing anyone to deposit funds directly into theTreasury as a form of service payment. However, the function calls token.safeTransferFrom with an arbitrary from parameter provided by the caller. This allows anyone to drain userallowances by transferring user-approved funds to the Treasury. Users are expected to grant allowances to the Treasury in order todeposit funds and participate in the Locks functionality. As a result,there may be multiple unspent allowances left on the Treasurycontract, with new allowances being granted on a regular basis. The receivePayment function does not update the internal Treasury userbalance. This is intended by design as services payment is notexpected to be deposited to internal Treasury user balance. Any funds deposited into the Treasury are recoverable by thecontract owner. The withdrawTo function allows the owner to manuallyreturn funds to users. function receivePayment( address user, uint256 amount, string memory service ) external nonReentrant { ... usdtToken.safeTransferFrom(user, address(this), amount); ... } function withdrawTo(uint256 amount, address re

### 修補方式（實際）
The Finding is ﬁxed in the commit 2a5f4e4. The receivePayment function is limited to process only user funds. The _purchaseTokensWithUSDT directly transfers funds from the user to the 14 Treasury. Evidences PoC


## F-2025-13271 - Maximum Token Supply may Be Never Reacheddue to Invalid Validation - Medium
- 嚴重度：Medium
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The mintGoldMembership function of the DOI_Gold contract is expected toallow users to mint new tokens untill the MAX_SUPPLY constant isreached. function mintGoldMembership() public nonReentrant { uint256 currentSupply = tokenCounter; if (currentSupply > MAX_SUPPLY) revert TotalSupplyLimitReached(); ... uint256 newSupply = currentSupply + 1; tokenCounter = newSupply; // Update in storage // Mint the Gold Membership token _safeMint(msg.sender, newSupply); ... } The limitReached view function is expected to return if the supply limitis reached. function limitReached() external view returns (bool) { return tokenCounter >= MAX_SUPPLY; } However, the functions use the tokenCounter variable as the currenttoken supply value. This variable represents an increasing counter tobe used as token id for new tokens minted and does not track thenumber of tokens in the contract (F-2025-13316). In fact, the tokenCounter variable value may exceed the actual currenttoken supply, in case the replaceToken function (admin restricted) wasever called. function replaceToken( uint256 oldTokenId, address recipient, string calldata reason ) external onlyAdmin { ... 19 // Burn the old token _burn(oldTokenId); //

### 修補方式（實際）
Fixed in commit ID 6a67ac3: the custom totalSupply() was removedfrom the code, using the parent's contract function in order to checkthe amount of existing token for sensitive operations, such as limitReached(). 21


## F-2025-13317 - Excessive Token Mint due to Invalid Validation -Medium
- 嚴重度：Medium
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The mintGoldMembership function of the DOI_Gold contract is expected toallow users to mint the MAX_SUPPLY of tokens. function mintGoldMembership() public nonReentrant { ... if (currentSupply > MAX_SUPPLY) revert TotalSupplyLimitReached(); ... } However, the validation allows minting when the currentSupply equalsto MAX_SUPPLY meaning one excessive token can be minted. This may lead to the total supply exceeds the MAX_SUPPLY constant.

### 修補方式（實際）
The Finding is ﬁxed in the commit c19b227. The check is changed to prevent excessive token minting. 25


## F-2024-7595 - Pseudo-Randomness Enables Raﬄe OutcomeManipulation - High
- 嚴重度：High
- Report source：Digital Oro.pdf

### 問題內容（摘要）
The Raffle contract facilitates a raﬄe system where users participateby submitting a tokenID from an ERC721-compliant DOIToken. Eachtoken is valued at 100 USD. When a token is submitted, it is markedas used, and the user is entered into the raﬄe. The contract ownerinvokes the finalizeWave() function to determine the winner for aspeciﬁc wave. Entries for each raﬄe are stored in the entries array. To determine a winner, the finalizeWave() function shuﬄes the entries array using the shuffleEntries() function, which relies on the random() function for randomization. The winner index is then determinedusing modulo division. function finalizeWave() external onlyAdmin { require(isActive, "Winner has already been drawn"); require(entries.length >= participantLimit, "Participant limit not reache d"); shuffleentries(); // Shuffle the entries to randomize their order uint256 winnerIndex = random() % entries.length; Entry memory winner = entries[winnerIndex]; {...} } The random() function is implemented as follows: /// @dev Function to generate pseudo-random numbers function random() internal view returns (uint256) { return uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrand ao,

### 修補方式（實際）
The Finding was ﬁxed in commit fdd11c068b6f01bd9169a4e6cc620b5c8a46cd72.The pseudo-random mechanism used to determine the raﬄe winnerwas replaced by Chainlink VRF (Veriﬁable Random Function) v2.5. Evidences PoC


## F-2025-8353 - Multiple Payouts Possible Due to InsuﬃcientValidation in FinalizeWave() - Medium
- 嚴重度：Medium
- Report source：Digital Oro.pdf

### 問題內容（摘要）
Following the initial audit, a design change was implemented toaddress issue F-2024-7595, "Pseudo-Randomness Enables RaﬄeOutcome Manipulation." The pseudo-random mechanism wasreplaced with Chainlink VRF (Veriﬁable Random Function) to ensurerandomness in selecting the raﬄe winner. Currently, the contractowner is required to call DOI_Raffle::drawWinner() to retrieve a randomnumber from the Chainlink oracle and then call DOI_Raffle::finalizeWave() to select the winner and initiate the payout. However, due to insuﬃcient validation of the contract state, the DOI_Raffle::finalizeWave() function can be invoked multiple times by thecontract owner, resulting in multiple payout initializations for thesame wave. Currently, the function only checks if the winner hasbeen drawn (DOI_Raffle::drawWinner() needs to be called ﬁrst to passthis check). function drawWinner() external onlyAdmin { // Cache variables uint256 _currentWave = currentWave; uint256 _participantLimit = waveHistory[_currentWave].participantLimit; require(!waveHistory[_currentWave].isWinnerDrawn, "Winner has already bee n drawn"); require(entries.length >= _participantLimit, "Participant limit not reach ed"); // Request random nu

### 修補方式（實際）
The Finding was ﬁxed in commit a59038370fc32e0abf88696cd1f495a40723c14e.A check for the current wave status was added to the finalizeWave() function, allowing execution only when the current wave is activeand preventing multiple calls to the function. 21


## F-2025-13531 - Double Fee Charged in Limit Order Execution Dueto Aggregator Fee Overlap - Medium
- 嚴重度：Medium
- Report source：Dirol.pdf

### 問題內容（摘要）
The LimitOrderModule’s fillOrder() function invokes aggregator.swap(swapParams) to execute a swap on behalf of the user.After the swap, it independently calculates a 10 bps (0.1%) fee onthe amountOut and transfers this fee to feeRecipient. uint256 amountOut = aggregator.swap(swapParams); if (amountOut < order.amountOutMin) revert InsufficientOut(); uint256 fee; unchecked { fee = (amountOut * FEE_BPS) / 10_000; netOut = amountOut - fee; } However, the CoreAggregator.swap() function already deducts aprotocol-level fee on the output amount before returning the ﬁnal destinationAmount to the caller. This leads to double fee deduction: 1. Aggregator deducts feeBps set by CoreAggregator owner2. LimitOrderModule deducts again 10 bps unconditionally. This contradicts the architecture described in the README: “LimitOrderModule Fees: Fixed 10 bps (0.1%) on outputamount… Covers keeper gas costs and protocol revenue.” “CoreAggregator Fees: Conﬁgurable… calculated on outputamount…”

### 修補方式（實際）
The Finding was ﬁxed in commit 9ae2b497 by adding the setFeeExempt function, allowing speciﬁc modules to be excluded from protocolfees. 40


## F-2024-4200 - Sales made with low amounts can be made forfree due to lack of control - Medium
- 嚴重度：Medium
- Report source：EverValue Coin-2.pdf

### 問題內容（摘要）
During the remediation commit, it was observed that there is apossibility to complete sell operations for free due to precision loss.It has been determined that in the scenario where there is a decimaldiﬀerence between the Market token and the EverValue token andsmall amounts of EverValue token are sold, the sale transactiontakes place and there is no token transfer in return for the sale. uint256 marketTokenToTransfer = (((normalizedAmount * marketTokenPer100Eva) / 100) * (1000 - fee)) / 1000; require( marketTokenToTransfer <= marketToken.balanceOf(address(this)), "Market doesn't have enough balance" ); eva.safeTransferFrom(msg.sender, this.owner(), amount); marketToken.safeTransfer(msg.sender, marketTokenToTransfer); Additional control should be provided to prevent free sales in theprotocol. It is important to add such controls to prevent potentiallosses.

### 修補方式（實際）
The EverValue team implemented the recommended check toeliminate this ﬁnding in given commit (4631b7). 10 Observation Details


## F-2025-14265 - Winner Selection Ignores Assigned Payout PositionsDue To A Faulty If Condition - High
- 嚴重度：High
- Report source：RYT.pdf

### 問題內容（摘要）
The payout selection mechanism in distributeFunds() is intended to enforcea strict order - either sequential or randomized via the s_payoutPositions mapping and setPayoutPositions() function. function distributeFunds() ... for (uint256 i = 0; i < totalMembers; i++) { address member = selectedGroup.members[i]; if ( !s_hasReceivedPayout[groupId][member] && (winner == address(0) || s_payoutPositions[groupId][me mber] == selectedGroup.currentPayoutIndex) ) { winner = member; break; } } ... However, due to a flawed conditional structure , the selection logic alwayspicks the first unpaid member in the group, completely ignoring theposition assigned in s_payoutPositions via the setPayoutPositions() function. The winner == address(0) condition is always true at the start of each payoutround, otherwise the looping is over and the winner is chosen. The winnercondition is evaluated before checking whether the user has the correctpayout position. This effectively short-circuits the entire payout-positioningsystem. As a result, the s_payoutPositions mapping has little to no impacton the selection process, violating the core invariant that the payout mustfollow the configured order.

### 修補方式（實際）
In commit 1829f31, the distributeFunds function now strictly selects thewinner by matching their assigned payout position against the currentcycle index, having removed the winner == address(0) condition thatpreviously allowed the first unpaid member to bypass the ordering logic. Evidences POC


## F-2025-14280 - Secondary Contributions Not Recorded in Slot Total,Leading to Incorrect Payout Ratios - High
- 嚴重度：High
- Report source：RYT.pdf

### 問題內容（摘要）
The Komiti contract supports "Joint Contributors," where two users share asingle slot. The Primary Contributor's address is used to track the total"Slot Balance" in the s_contributions mapping. The Secondary Contributor'sspecific equity is tracked in s_contributionShares. When a payout occurs, thecontract calculates the Secondary's share using the ratio: SecondaryEquity / TotalSlotBalance. The contributeAsJointMember function contains a logic error wherecontributions made by the Secondary Contributor update their equity(s_contributionShares) but fail to update the total slot balance (s_contributions of the Primary). This causes the TotalSlotBalance denominator to beartificially low during payout calculations. Consequently, the SecondaryContributor receives an inflated share of the payout - potentially exceedingtheir entitlement - while the Primary Contributor receives significantly lessthan owed (or nothing at all). The issue is located in the contributeAsJointMember function. The codehandles contributions separately based on the sender: if (primaryContributor == msg.sender) { s_contributions[groupId][primaryContributor] += msg.value; } else { s_contributionShares[groupId][secondar

### 修補方式（實際）
Fixed in 1829f31. The contributeAsJointMember() was removed from thecodebase making the current finding no longer applicable. Evidences PoC


## F-2025-11651 - Precision Loss in Bonding Curve Calculations -High
- 嚴重度：High
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The calculateBuyCost function is designed to calculate the cost ofpurchasing a speciﬁc amount of tokens from an exponential bondingcurve. The pricing should be continuous, meaning the cost issmoothly inﬂuenced by the exact number of tokens already sold,including fractional amounts (represented in wei). The core mathematical formula discards all fractional token precisionby performing integer division on the soldSoFarWei and sellableSupply amounts before converting them to ﬁxed-point numbers. Thisfundamentally changes the behavior of the continuous exponentialcurve into a discrete step-function where the price only updateswhen a full integer token has been sold. This leads to inaccuratepricing, causing users to consistently overpay or underpay andcreating a growing mismatch between the funds held by the contractand the value predicted by its own formula. The precision loss occurs in the _area0 private function. Beforeperforming high-precision ﬁxed-point math, the number of tokenssold (sWei) is truncated to an integer. function _area0( uint256 sWei, // ... ) private pure returns (uint256) { // number of tokens (human) uint256 supplyTokens = sellableSupply / SCALE; int128 fracQ64 = (s

### 修補方式（實際）
In commit f6e452b, the ABDKMath64x64 library is utilized. Evidences PoC


## F-2025-11654 - Flawed Rounding Logic in calculateBuyAmountLeads to Loss of Funds - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The calculateBuyAmount function is the inverse of calculateBuyCost. It isintended to take a speciﬁc cost (in wei) and determine the exactamount of tokens that can be purchased. This function is critical foruser-facing applications to query purchase amounts beforesubmitting a transaction. The function contains a "smart rounding" feature that aggressivelyrounds the calculated purchase amount to the nearest whole token.If a user's provided cost corresponds to a purchase of less than 0.5 tokens, the function will round the amount down to 0. This creates asituation where a user can pay a non-zero, tangible cost but receivezero tokens in return, resulting in a direct and irreversible loss of theuser's funds. The issue is located at the end of the _inverseArea0 function, which iscalled by calculateBuyAmount. After correctly calculating the tokenamount sWei that corresponds to the targetArea, the code rounds it tothe nearest multiple of 1e18 (SCALE). function _inverseArea0( // ... ) private pure returns (uint256) { // ... preceding calculations ... uint256 sWei = fracQ64.mulu(SCALE * supplyTokens); // Smart rounding: round to nearest wei to eliminate calculation drift // while preserving s

### 修補方式（實際）
In commit f6e452b, the rounding logic has been removed. Evidences PoC


## F-2025-11735 - Incorrect Progressive-TGE Calculation Order Leadsto Unintended Token Unlocks - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The buy function facilitates token purchases and subsequentlycalculates the buyer's Token Generation Event (TGE) allocation usingthe _calculateTGEPercent internal function. The TGE percentage isdesigned to be progressive: it should start at a baseTGEUnlockPercent forthe very ﬁrst tokens sold and scale up towards 100% for the very lasttokens sold. The contract updates the totalProjectTokenSold state variable before itcalculates the progressive TGE percentage for the current buyer.This ﬂawed order of operations has two major consequences. First,every buyer receives a slightly larger TGE allocation than intended.Second, and more critically, it allows for a scenario where a user whobuys all remaining tokens in a single transaction will receive a 100% TGE on their entire purchase, completely bypassing the vestingschedule for that amount. This undermines the core tokenomicmodel and creates a signiﬁcant economic vulnerability. In the _buy function, the totalProjectTokenSold is incremented.Immediately after, this updated value is used to calculate the TGEpercentage for the user's purchase. …. strg.ledger.totalProjectTokenSold += tokensToGive; uint256 tgePercent = _calculateTGEPercent( strg

### 修補方式（實際）
In commit a893459, the TGE calculation logic is re-ordered, the newimplementation performs calculation before the current purchase isfactored in. 24


## F-2025-11767 - Inconsistent State Change in autoRefund() AﬀectsTGE Unlock and Price Logic - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract provides a mechanism for the default adminto refund users via autoRefund() function if the softCap has not beenreached. The refund process is expected to return the user's bondedtokens, remove their project token claim, and return that tokenamount to the available pool so other users can purchase them. The bonding curve maintains two key state variables: tokenToSell: the ﬁxed amount of tokens intended to be sold duringthe curve lifecycle, calculated once on deployment. function _updateLedger( ProjectTokenDetails calldata projectTokenDetails, Ledger storage ledger, uint256 tSupply ) internal { ledger.tokenToSell = (tSupply * projectTokenDetails.tokenToSellPercent) / 10000; ... } totalProjectTokenSold: the amount of tokens sold so far, whichshould decrease if tokens are refunded. In the _buy() function, the contract checks whether the remainingtokens (tokenToSell - totalProjectTokenSold) are suﬃcient for the newpurchase. However, the autoRefund() function currently adds the refunded tokensback to tokenToSell, instead of subtracting them from totalProjectTokenSold. This behavior deviates from the expected logic,where tokenToSell should remain constant, and on

### 修補方式（實際）
Fixed in c4b53ea: the value of totalProjectTokenSold is now correctlyupdated by subtracting totalClaimAmount of the refunded users. 36

## F-2025-13707 - ERC-7201 Storage Location Comment Does NotMatch Actual Value
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `Stargate.sol` contract contains a mismatch between the `ERC` 7201storage location comment and the actual storage slot value. The commentindicates the namespace "storage.Stargate", but the actual storage location 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 wascalculated using the old contract name "storage.StargateStaker". This discrepancy was introduced during the contract rename from StargateStaker to Stargate in commit 13fee598, where the comment wasupdated but the storage location value was not recalculated. If a developer creates a new implementation based on the developercomment, they would use: bytes32 private constant StargateStorageLocation = 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800; This would cause the new implementation to read/write to completelydifferent storage slots, resulting in: Loss of all existing state dataCorrupted validator dataBroken delegation mappingsTotal system failure `Stargate.sol`: // `keccak256(abi.encode(uint256(keccak256("storage.Stargate")`) - 1)) & ~bytes 32(`uint256(0xff)`) bytes32 private constant StargateStorageLocation = 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700; Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
If the Stargate contract is already deployed, the storage location must notchange. Update the comment to match the actual value: // `keccak256(abi.encode(uint256(keccak256("storage.StargateStaker")`) - 1)) & ~`bytes32(uint256(0xff)`) // `NOTE`: Storage namespace uses legacy "StargateStaker" name to maintain comp atibility // with deployed contracts. This `MUST` `NOT` be changed in future versions. bytes32 private constant StargateStorageLocation = 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700; Else, change the developer comment and storage location with the correctone. // `keccak256(abi.encode(uint256(keccak256("storage.Stargate")`) - 1)) & ~bytes 32(`uint256(0xff)`) bytes32 private constant StargateStorageLocation = 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800; Resolution: The finding is fixed in commit hash 982996b after updating the storagelocation constant from 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 (calculatedfrom "storage.StargateStaker") to 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800 (calculatedfrom "storage.Stargate"). The fix correctly aligns the storage locationvalue with its `ERC` 7201 comment, ensuring consistency for futuredevelopment. The change is safe because Stargate is a new contractdeployment with fresh storage, not an upgrade of existing deployedstorage. 41

### 修補方式（實際）
The finding is fixed in commit hash 982996b after updating the storagelocation constant from 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 (calculatedfrom "storage.StargateStaker") to 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800 (calculatedfrom "storage.Stargate"). The fix correctly aligns the storage locationvalue with its `ERC` 7201 comment, ensuring consistency for futuredevelopment. The change is safe because Stargate is a new contractdeployment with fresh storage, not an upgrade of existing deployedstorage. 41
