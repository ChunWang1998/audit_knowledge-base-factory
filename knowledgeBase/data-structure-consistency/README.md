# data-structure-consistency - Issues

- Count: 16

## F-2025-14458 - Mismatch Between Tier Assignment and Enumeration Breaks Tier Determinism
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The MemoryManager contract uses two fundamentally different approachesto handle tiering, which causes critical inconsistency in tier calculationand enumeration logic. Value-Based Tiering during insertion: stake tiers and downline tiersare determined by dividing the value (e.g., stakeId) by a constantTIER_SIZE function `addToTier(mapping(uint256 => uint256[])` storage tiers, uint256 value ) internal { uint256 tier = value / `TIER_SIZE`; tiers[tier].`push(value)`; } Count-Based Tier Enumeration during tier counting: the number oftiers is estimated by dividing the count of stakes or downlines by `TIER_SIZE` with rounding: function `getTierCount(uint256 totalCount)` internal pure returns (uint256) { return (totalCount + `TIER_SIZE` - 1) / `TIER_SIZE`; } ForExample: Consider Alice staking twice with stakeId values 1999 and 2000 1999 → assigned to tier 1 (since 1999 / 1000 = 1) 2000 → assigned to tier 2 (since 2000 / 1000 = 2) Since: userStakeCount[`msg.sender`] == 2 `getTierCount(2)` => (totalCount + `TIER_SIZE` - 1) / `TIER_SIZE` => 2 + 1000 - 1 / 1000 = 1 This result incorrectly implies only one tier is used, which conflicts withthe actual tier assignments. This design mismatch leads to incorrect and non-deterministic tiercounts that do not reflect: 27 The actual distribution of stake ids among tiers in the StakingAndRewards::`stake()` function and leads to the incorrect calculationof the maxTiers number that affects the paginated data generationprocess in the MemoryManager::`getPaginatedData()` function that has anegative impact on the StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` functions output data. The actual distribution of downlines among downline tiers in the Subcription::`_addDownlines`() which is utilized in the Subscription::`register()` function. Although the issue does not directly impact the financial components ofthe system, this discrepancy undermines the reliability and integrity of thetiering mechanism and may lead to downstream issues for systemintegrators, including frontend components and decentralized applications. Assets: `MemoryManager.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
It is recommended to: redesign the tier calculation logic to take into account situations whenuser stakes are in different tiers.provide a proper test suite covering all edge cases of the newfunctionality.document the intended behavior of the system. Resolution: Fixed in 825eaaf. The `_addDownlines`() function was redesigned to properlycalculate the downlineTierCount value as follows: uint256 actualTier = newUserId / `TIER_SIZE`; // Same formula as `addToTier()` 28 line 30 if (!tierUsed[current.id][level][actualTier]) { tierUsed[current.id][level][actualTier] = true; // Mark tier as used downlineTierCount[current.id][level]++; // Increment unique tier count } … In addition to that the functions MemoryManager::`getTierCount()`, MemoryManager::`getPaginatedData()`, StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` were removed from thecodebase. The calculation of the userStakeTierCount was removed from the StakingAndRewards::`stake()` function.

### 修補方式（實際）
Fixed in 825eaaf. The `_addDownlines`() function was redesigned to properlycalculate the downlineTierCount value as follows: uint256 actualTier = newUserId / `TIER_SIZE`; // Same formula as `addToTier()` 28 line 30 if (!tierUsed[current.id][level][actualTier]) { tierUsed[current.id][level][actualTier] = true; // Mark tier as used downlineTierCount[current.id][level]++; // Increment unique tier count } … In addition to that the functions MemoryManager::`getTierCount()`, MemoryManager::`getPaginatedData()`, StakingAndRewards::`getUserStakeIds()` and StakingAndRewards::`getUserStakeIdsPaginated()` were removed from thecodebase. The calculation of the userStakeTierCount was removed from the StakingAndRewards::`stake()` function.

## F-2025-14443 - Uninitialized min Withdraw Amount Allows Zero-Amount Forced Withdrawal Requests To Block Queue Processing - Medium
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


## F-2025-13317 - Excessive Token Mint due to Invalid Validation - Medium
- 嚴重度：Medium
- Report source：Digital Oro International.pdf

### 問題內容（摘要）
The mintGoldMembership function of the DOI_Gold contract is expected toallow users to mint the MAX_SUPPLY of tokens. function mintGoldMembership() public nonReentrant { ... if (currentSupply > MAX_SUPPLY) revert TotalSupplyLimitReached(); ... } However, the validation allows minting when the currentSupply equalsto MAX_SUPPLY meaning one excessive token can be minted. This may lead to the total supply exceeds the MAX_SUPPLY constant.

### 修補方式（實際）
The Finding is ﬁxed in the commit c19b227. The check is changed to prevent excessive token minting. 25


## F-2024-7595 - Pseudo-Randomness Enables Raﬄe Outcome Manipulation - High
- 嚴重度：High
- Report source：Digital Oro.pdf

### 問題內容（摘要）
The Raffle contract facilitates a raﬄe system where users participateby submitting a tokenID from an ERC721-compliant DOIToken. Eachtoken is valued at 100 USD. When a token is submitted, it is markedas used, and the user is entered into the raﬄe. The contract ownerinvokes the finalizeWave() function to determine the winner for aspeciﬁc wave. Entries for each raﬄe are stored in the entries array. To determine a winner, the finalizeWave() function shuﬄes the entries array using the shuffleEntries() function, which relies on the random() function for randomization. The winner index is then determinedusing modulo division. function finalizeWave() external onlyAdmin { require(isActive, "Winner has already been drawn"); require(entries.length >= participantLimit, "Participant limit not reache d"); shuffleentries(); // Shuffle the entries to randomize their order uint256 winnerIndex = random() % entries.length; Entry memory winner = entries[winnerIndex]; {...} } The random() function is implemented as follows: /// @dev Function to generate pseudo-random numbers function random() internal view returns (uint256) { return uint256(keccak256(abi.encodePacked(block.timestamp, block.prevrand ao,

### 修補方式（實際）
The Finding was ﬁxed in commit fdd11c068b6f01bd9169a4e6cc620b5c8a46cd72.The pseudo-random mechanism used to determine the raﬄe winnerwas replaced by Chainlink VRF (Veriﬁable Random Function) v2.5. Evidences PoC


## F-2025-8353 - Multiple Payouts Possible Due to Insuﬃcient Validation in Finalize Wave() - Medium
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


## F-2025-14265 - Winner Selection Ignores Assigned Payout Positions Due To A Faulty If Condition - High
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


## F-2025-11651 - Precision Loss in Bonding Curve Calculations - High
- 嚴重度：High
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The calculateBuyCost function is designed to calculate the cost ofpurchasing a speciﬁc amount of tokens from an exponential bondingcurve. The pricing should be continuous, meaning the cost issmoothly inﬂuenced by the exact number of tokens already sold,including fractional amounts (represented in wei). The core mathematical formula discards all fractional token precisionby performing integer division on the soldSoFarWei and sellableSupply amounts before converting them to ﬁxed-point numbers. Thisfundamentally changes the behavior of the continuous exponentialcurve into a discrete step-function where the price only updateswhen a full integer token has been sold. This leads to inaccuratepricing, causing users to consistently overpay or underpay andcreating a growing mismatch between the funds held by the contractand the value predicted by its own formula. The precision loss occurs in the _area0 private function. Beforeperforming high-precision ﬁxed-point math, the number of tokenssold (sWei) is truncated to an integer. function _area0( uint256 sWei, // ... ) private pure returns (uint256) { // number of tokens (human) uint256 supplyTokens = sellableSupply / SCALE; int128 fracQ64 = (s

### 修補方式（實際）
In commit f6e452b, the ABDKMath64x64 library is utilized. Evidences PoC


## F-2025-11654 - Flawed Rounding Logic in calculate Buy Amount Leads to Loss of Funds - Medium
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


## F-2025-11767 - Inconsistent State Change in auto Refund() Aﬀects TGE Unlock and Price Logic - Medium
- 嚴重度：Medium
- Report source：Seedify.fund.pdf

### 問題內容（摘要）
The BondingCurve contract provides a mechanism for the default adminto refund users via autoRefund() function if the softCap has not beenreached. The refund process is expected to return the user's bondedtokens, remove their project token claim, and return that tokenamount to the available pool so other users can purchase them. The bonding curve maintains two key state variables: tokenToSell: the ﬁxed amount of tokens intended to be sold duringthe curve lifecycle, calculated once on deployment. function _updateLedger( ProjectTokenDetails calldata projectTokenDetails, Ledger storage ledger, uint256 tSupply ) internal { ledger.tokenToSell = (tSupply * projectTokenDetails.tokenToSellPercent) / 10000; ... } totalProjectTokenSold: the amount of tokens sold so far, whichshould decrease if tokens are refunded. In the _buy() function, the contract checks whether the remainingtokens (tokenToSell - totalProjectTokenSold) are suﬃcient for the newpurchase. However, the autoRefund() function currently adds the refunded tokensback to tokenToSell, instead of subtracting them from totalProjectTokenSold. This behavior deviates from the expected logic,where tokenToSell should remain constant, and on

### 修補方式（實際）
Fixed in c4b53ea: the value of totalProjectTokenSold is now correctlyupdated by subtracting totalClaimAmount of the refunded users. 36

## F-2025-13707 - ERC-7201 Storage Location Comment Does Not Match Actual Value
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `Stargate.sol` contract contains a mismatch between the `ERC` 7201storage location comment and the actual storage slot value. The commentindicates the namespace "storage.Stargate", but the actual storage location 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 wascalculated using the old contract name "storage.StargateStaker". This discrepancy was introduced during the contract rename from StargateStaker to Stargate in commit 13fee598, where the comment wasupdated but the storage location value was not recalculated. If a developer creates a new implementation based on the developercomment, they would use: bytes32 private constant StargateStorageLocation = 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800; This would cause the new implementation to read/write to completelydifferent storage slots, resulting in: Loss of all existing state dataCorrupted validator dataBroken delegation mappingsTotal system failure `Stargate.sol`: // `keccak256(abi.encode(uint256(keccak256("storage.Stargate")`) - 1)) & ~bytes 32(`uint256(0xff)`) bytes32 private constant StargateStorageLocation = 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700; Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
If the Stargate contract is already deployed, the storage location must notchange. Update the comment to match the actual value: // `keccak256(abi.encode(uint256(keccak256("storage.StargateStaker")`) - 1)) & ~`bytes32(uint256(0xff)`) // `NOTE`: Storage namespace uses legacy "StargateStaker" name to maintain comp atibility // with deployed contracts. This `MUST` `NOT` be changed in future versions. bytes32 private constant StargateStorageLocation = 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700; Else, change the developer comment and storage location with the correctone. // `keccak256(abi.encode(uint256(keccak256("storage.Stargate")`) - 1)) & ~bytes 32(`uint256(0xff)`) bytes32 private constant StargateStorageLocation = 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800; Resolution: The finding is fixed in commit hash 982996b after updating the storagelocation constant from 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 (calculatedfrom "storage.StargateStaker") to 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800 (calculatedfrom "storage.Stargate"). The fix correctly aligns the storage locationvalue with its `ERC` 7201 comment, ensuring consistency for futuredevelopment. The change is safe because Stargate is a new contractdeployment with fresh storage, not an upgrade of existing deployedstorage. 41

### 修補方式（實際）
The finding is fixed in commit hash 982996b after updating the storagelocation constant from 0xaf70fbb7e0f95b3e16b002fff11ff1ea2145b66dd31261eff20d74fda9749700 (calculatedfrom "storage.StargateStaker") to 0x13d735e507c4583a99e864ed7b084588a10d8c61b213ed56516dd29987bcd800 (calculatedfrom "storage.Stargate"). The fix correctly aligns the storage locationvalue with its `ERC` 7201 comment, ensuring consistency for futuredevelopment. The change is safe because Stargate is a new contractdeployment with fresh storage, not an upgrade of existing deployedstorage. 41

## Cyfrin Fixed Issues (Merged)
- Count: `21`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Immediate stake cache updates enable reward distribution without P-Chain confirmation
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The middleware immediately updates stake cache for reward calculations when operators initiate stake changes via `initializeValidatorStakeUpdate()`, even though these changes remain unconfirmed by the P-Chain.

This creates a temporal window where reward calculations diverge from the actual validated P-Chain state, potentially allowing operators to receive rewards based on unconfirmed stake increases.

When an operator calls `initializeValidatorStakeUpdate()` to modify their validator's stake, the middleware immediately updates the stake cache for the next epoch:

```solidity
// In initializeValidatorStakeUpdate():
function _initializeValidatorStakeUpdate(address operator, bytes32 validationID, uint256 newStake) internal {
    uint48 currentEpoch = getCurrentEpoch();

    nodeStakeCache[currentEpoch + 1][validationID] = newStake;
    nodePendingUpdate[validationID] = true;

    // @audit P-Chain operation initiated but NOT confirmed
    balancerValidatorManager.initializeValidatorWeightUpdate(validationID, scaledWeight);
}
```
However, reward calculations immediately use this cached stake without verifying P-Chain confirmation:

```solidity
function getOperatorUsedStakeCachedPerEpoch(uint48 epoch, address operator, uint96 assetClass) external view returns (uint256) {
    // Uses cached stake regardless of P-Chain confirmation status
    bytes32[] memory nodesArr = this.getActiveNodesForEpoch(operator, epoch);
    for (uint256 i = 0; i < nodesArr.length; i++) {
        bytes32 nodeId = nodesArr[i];
        bytes32 validationID = balancerValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));
        registeredStake += getEffectiveNodeStake(epoch, validationID); // @audit Uses unconfirmed stake
    }
```

It is worthwhile to note that the middleware explicitly skips validators with pending updates in the `forceUpdateNodes`:

```solidity
function forceUpdateNodes(address operator, uint256 limitStake) external {
    // ...
    for (uint256 i = length; i > 0 && leftoverStake > 0;) {
        bytes32 valID = balancerValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));
        if (balancerValidatorManager.isValidatorPendingWeightUpdate(valID)) {
            continue; // @audit No correction possible for pending validators
        }
        // ... stake adjustment logic
    }
}
```
This creates an inconsistent approach - while rebalancing nodes, logic is verifying the P-chain state while the same check is missing for reward estimation.


**Impact:**
- Operators receive immediate reward boosts upon submitting stake increases, before P-Chain validation
- P-chain may reject operations or take multiple epochs to confirm causing an inconsistency in L1 Middleware state and P-chain state

**Proof of Concept:** Current POC shows that the reward calculation uses unconfirmed stake updates. Add to `AvalancheMiddlewareTest.t.sol`

```solidity
    function test_UnconfirmedStakeImmediateRewards() public {
        // Setup: Alice has 100 ETH equivalent stake
        uint48 epoch = _calcAndWarpOneEpoch();

        // increasuing vaults total stake
        (, uint256 additionalMinted) = _deposit(staker, 500 ether);

        // Now allocate more of this deposited stake to Alice (the operator)
        uint256 totalAliceShares = mintedShares + additionalMinted;
        _setL1Limit(bob, validatorManagerAddress, assetClassId, 3000 ether, delegator);
        _setOperatorL1Shares(bob, validatorManagerAddress, assetClassId, alice, totalAliceShares, delegator);

        // Move to next epoch to make the new stake available
        epoch = _calcAndWarpOneEpoch();

        // Verify Alice now has sufficient available stake
        uint256 aliceAvailableStake = middleware.getOperatorAvailableStake(alice);
        console2.log("Alice available stake: %s ETH", aliceAvailableStake / 1 ether);

        // Alice adds a node with 10 ETH stake
        (bytes32[] memory nodeIds, bytes32[] memory validationIDs,) =
            _createAndConfirmNodes(alice, 1, 10 ether, true);
        bytes32 nodeId = nodeIds[0];
        bytes32 validationID = validationIDs[0];

        // Move to next epoch and confirm initial state
        epoch = _calcAndWarpOneEpoch();
        uint256 initialStake = middleware.getNodeStake(epoch, validationID);
        assertEq(initialStake, 10 ether, "Initial stake should be 10 ETH");

        // Alice increases stake to 1000 ETH (10x increase)
        uint256 modifiedStake = 50 ether;
        vm.prank(alice);
        middleware.initializeValidatorStakeUpdate(nodeId, modifiedStake);

        // Check: Stake cache immediately updated for next epoch (unconfirmed!)
        uint48 nextEpoch = middleware.getCurrentEpoch() + 1;
        uint256 unconfirmedStake = middleware.nodeStakeCache(nextEpoch, validationID);
        assertEq(unconfirmedStake, modifiedStake, "Unconfirmed stake should be immediately set");

        // Verify: P-Chain operation is still pending
        assertTrue(
            mockValidatorManager.isValidatorPendingWeightUpdate(validationID),
            "P-Chain operation should still be pending"
        );

        // Move to next epoch (when unconfirmed stake takes effect)
        epoch = _calcAndWarpOneEpoch();

        // Reward calculations now use unconfirmed 1000 ETH stake
        uint256 operatorStakeForRewards = middleware.getOperatorUsedStakeCachedPerEpoch(
            epoch, alice, middleware.PRIMARY_ASSET_CLASS()
        );
        assertEq(
            operatorStakeForRewards,
            modifiedStake,
            "Reward calculations should use unconfirmed 500 ETH stake"
        );
        console2.log("Stake used for rewards: %s ETH", operatorStakeForRewards / 1 ether);
    }
```

**Recommended Mitigation:** Consider updating the stake cache only after P-Chain confirmation rather than during initialization:

```solidity
function completeStakeUpdate(bytes32 nodeId, uint32 messageIndex) external {
    // ... existing logic ...

    // Update cache only after P-Chain confirms
    uint48 currentEpoch = getCurrentEpoch();
    nodeStakeCache[currentEpoch + 1][validationID] = validator.weight;
}
```
Note that this change also requires changes in `_calcAndCacheNodeStakeForOperatorAtEpoch` - currently the `nodeStakeCache` of current epoch is updated to the one in previous epoch, only when there are no pending updates. If the above change is implemented, `nodeStakeCache` for current epoch should **always be** the one rolled over from previous epochs.

**Suzaku:**
Fixed in commit [5157351](https://github.com/suzaku-network/suzaku-core/pull/155/commits/5157351d0e9a799679a74c33c6b69aa87d58ab51).

**Cyfrin:** Verified.

## [C-2] Incorrect summation of curator shares in `claim Undistributed Rewards` leads to deficit in claimed undistributed rewards
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `claimUndistributedRewards` function is designed to allow a `REWARDS_DISTRIBUTOR_ROLE` to collect any rewards for a specific `epoch` that were not claimed by stakers, operators, or curators. To do this, it calculates `totalDistributedShares`, representing the sum of all share percentages (in basis points) allocated to various participants.

```solidity
// Calculate total distributed shares for the epoch
uint256 totalDistributedShares = 0;

// Sum operator shares
address[] memory operators = l1Middleware.getAllOperators();
for (uint256 i = 0; i < operators.length; i++) {
    totalDistributedShares += operatorShares[epoch][operators[i]];
}

// Sum vault shares
address[] memory vaults = middlewareVaultManager.getVaults(epoch);
for (uint256 i = 0; i < vaults.length; i++) {
    totalDistributedShares += vaultShares[epoch][vaults[i]];
}

// Sum curator shares
for (uint256 i = 0; i < vaults.length; i++) {
    address curator = VaultTokenized(vaults[i]).owner();
    totalDistributedShares += curatorShares[epoch][curator];
}
```

The code iterates through all `vaults` active in the epoch. For each `vault`, it retrieves the `curator` (owner) and adds `curatorShares[epoch][curator]` to `totalDistributedShares`. However, the `curatorShares[epoch][curator]` mapping already stores the *total accumulated share* for that specific `curator` for that `epoch`, aggregated from all vaults they own and all operators those vaults delegated to.

```solidity
// First pass: calculate raw shares and total
for (uint256 i = 0; i < vaults.length; i++) {
    address vault = vaults[i];
    uint96 vaultAssetClass = middlewareVaultManager.getVaultAssetClass(vault);

    uint256 vaultStake = BaseDelegator(IVaultTokenized(vault).delegator()).stakeAt(
        l1Middleware.L1_VALIDATOR_MANAGER(), vaultAssetClass, operator, epochTs, new bytes(0)
    );

    if (vaultStake > 0) {
        uint256 operatorActiveStake =
            l1Middleware.getOperatorUsedStakeCachedPerEpoch(epoch, operator, vaultAssetClass);

        uint256 vaultShare = Math.mulDiv(vaultStake, BASIS_POINTS_DENOMINATOR, operatorActiveStake);
        vaultShare =
            Math.mulDiv(vaultShare, rewardsSharePerAssetClass[vaultAssetClass], BASIS_POINTS_DENOMINATOR);
        vaultShare = Math.mulDiv(vaultShare, operatorShare, BASIS_POINTS_DENOMINATOR);

        uint256 operatorTotalStake = l1Middleware.getOperatorStake(operator, epoch, vaultAssetClass);

        if (operatorTotalStake > 0) {
            uint256 operatorStakeRatio =
                Math.mulDiv(operatorActiveStake, BASIS_POINTS_DENOMINATOR, operatorTotalStake);
            vaultShare = Math.mulDiv(vaultShare, operatorStakeRatio, BASIS_POINTS_DENOMINATOR);
        }

        // Calculate curator share
        uint256 curatorShare = Math.mulDiv(vaultShare, curatorFee, BASIS_POINTS_DENOMINATOR);
        curatorShares[epoch][VaultTokenized(vault).owner()] += curatorShare;

        // Store vault share after removing curator share
        vaultShares[epoch][vault] += vaultShare - curatorShare;
    }
}
```

If a single curator owns multiple vaults that were active in the epoch, their *total* share (from `curatorShares[epoch][curator]`) is added to `totalDistributedShares` multiple times—once for each vault they own. This artificially inflates the `totalDistributedShares` value.

**Impact:** The inflated `totalDistributedShares` leads to an underestimation of the actual `undistributedRewards`. The formula `undistributedRewards = totalRewardsForEpoch - Math.mulDiv(totalRewardsForEpoch, totalDistributedShares, BASIS_POINTS_DENOMINATOR)` will yield a smaller amount than what is truly undistributed.

Consequently:
1.  The `REWARDS_DISTRIBUTOR_ROLE` will claim a smaller amount of undistributed tokens than they are entitled to.
2.  The difference between the actual undistributed amount and the incorrectly calculated (smaller) amount will remain locked in the contract (unless it's upgraded) .

**Proof of Concept:**
```solidity
// ─────────────────────────────────────────────────────────────────────────────
// PoC – Incorrect Sum-of-Shares
// Shows that the sum of operator + vault + curator shares can exceed 10 000 bp
// (100 %), proving that `claimUndistributedRewards` will mis-count.
// ─────────────────────────────────────────────────────────────────────────────
import {AvalancheL1MiddlewareTest} from "./AvalancheL1MiddlewareTest.t.sol";

import {Rewards}           from "src/contracts/rewards/Rewards.sol";
import {MockUptimeTracker} from "../mocks/MockUptimeTracker.sol";
import {ERC20Mock}         from "@openzeppelin/contracts/mocks/token/ERC20Mock.sol";

import {VaultTokenized}    from "src/contracts/vault/VaultTokenized.sol";

import {console2}          from "forge-std/console2.sol";
import {stdError}          from "forge-std/Test.sol";

contract PoCIncorrectSumOfShares is AvalancheL1MiddlewareTest {
    // ── helpers & globals ────────────────────────────────────────────────────
    MockUptimeTracker internal uptimeTracker;
    Rewards          internal rewards;
    ERC20Mock        internal rewardsToken;

    address internal REWARDS_MANAGER_ROLE     = makeAddr("REWARDS_MANAGER_ROLE");
    address internal REWARDS_DISTRIBUTOR_ROLE = makeAddr("REWARDS_DISTRIBUTOR_ROLE");

    uint96 secondaryAssetClassId = 2;          // activate a 2nd asset-class (40 % of rewards)

    // -----------------------------------------------------------------------
    //                      MAIN TEST ROUTINE
    // -----------------------------------------------------------------------
    function test_PoCIncorrectSumOfShares() public {
        _setupRewardsAndSecondaryAssetClass();          // 1. deploy + fund rewards

        address[] memory operators = middleware.getAllOperators();

        // 2. Alice creates *two* nodes (same stake reused) -------------------
        console2.log("Creating nodes for Alice");
        _createAndConfirmNodes(alice, 2, 100_000_000_001_000, true);

        // 3. Charlie is honest – single big node -----------------------------
        console2.log("Creating node for Charlie");
        _createAndConfirmNodes(charlie, 1, 150_000_000_000_000, true);

        // 4. Roll over so stakes are cached at epoch T ------------------------
        uint48 epoch = _calcAndWarpOneEpoch();
        console2.log("Moved to one epoch ");

        // Cache total stakes for primary & secondary classes
        middleware.calcAndCacheStakes(epoch, assetClassId);
        middleware.calcAndCacheStakes(epoch, secondaryAssetClassId);

        // 5. Give everyone perfect uptime so shares are fully counted --------
        for (uint i = 0; i < operators.length; i++) {
            uptimeTracker.setOperatorUptimePerEpoch(epoch,   operators[i], 4 hours);
            uptimeTracker.setOperatorUptimePerEpoch(epoch+1, operators[i], 4 hours);
        }

        // 6. Warp forward 3 epochs (rewards are distributable @ T-2) ---------
        _calcAndWarpOneEpoch(3);
        console2.log("Warped forward for rewards distribution");

        // 7. Distribute rewards ---------------------------------------------
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.distributeRewards(epoch, uint48(operators.length));
        console2.log("Rewards distributed");

        // 8. Sum all shares and show bug (>10 000 bp) ------------------------
        uint256 totalShares = 0;

        // operator shares
        for (uint i = 0; i < operators.length; i++) {
            uint256 s = rewards.operatorShares(epoch, operators[i]);
            totalShares += s;
        }
        // vault shares
        address[] memory vaults = vaultManager.getVaults(epoch);
        for (uint i = 0; i < vaults.length; i++) {
            uint256 s = rewards.vaultShares(epoch, vaults[i]);
            totalShares += s;
        }
        // curator shares (may be double-counted!)
        for (uint i = 0; i < vaults.length; i++) {
            address curator = VaultTokenized(vaults[i]).owner();
            uint256 s = rewards.curatorShares(epoch, curator);
            totalShares += s;
        }
        console2.log("Total shares is greater than 10000 bp");

        assertGt(totalShares, 10_000);
    }

    // -----------------------------------------------------------------------
    //                      SET-UP HELPER
    // -----------------------------------------------------------------------
    function _setupRewardsAndSecondaryAssetClass() internal {
        uptimeTracker = new MockUptimeTracker();
        rewards       = new Rewards();

        // Initialise Rewards contract ---------------------------------------
        rewards.initialize(
            owner,                                  // admin
            owner,                                  // protocol fee recipient
            payable(address(middleware)),           // middleware
            address(uptimeTracker),                 // uptime oracle
            1000,                                   // protocol fee 10%
            2000,                                   // operator fee 20%
            1000,                                   // curator  fee 10%
            11_520                                  // min uptime (s)
        );

        // Assign roles -------------------------------------------------------
        vm.prank(owner);
        rewards.setRewardsManagerRole(REWARDS_MANAGER_ROLE);
        vm.prank(REWARDS_MANAGER_ROLE);
        rewards.setRewardsDistributorRole(REWARDS_DISTRIBUTOR_ROLE);

        // Mint & approve mock reward token ----------------------------------
        rewardsToken = new ERC20Mock();
        rewardsToken.mint(REWARDS_DISTRIBUTOR_ROLE, 1_000_000 ether);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewardsToken.approve(address(rewards), 1_000_000 ether);

        // Fund 10 epochs of rewards -----------------------------------------
        vm.startPrank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.setRewardsAmountForEpochs(1, 10, address(rewardsToken), 100_000 * 1e18);
        vm.stopPrank();
        console2.log("Reward pool funded");

        // Configure 60 % primary / 40 % secondary split ---------------------
        vm.startPrank(REWARDS_MANAGER_ROLE);
        rewards.setRewardsShareForAssetClass(1,                     6000); // 60 %
        rewards.setRewardsShareForAssetClass(secondaryAssetClassId, 4000); // 40 %
        vm.stopPrank();
        console2.log("Reward share split set: 60/40");

        // Create a secondary asset-class + vault so split is in effect
        _setupAssetClassAndRegisterVault(
            secondaryAssetClassId, 0,
            collateral2, vault3,
            type(uint256).max, type(uint256).max, delegator3
        );
        console2.log("Secondary asset-class & vault registered\n");
    }
}
```
**Output:**
```bash
Ran 1 test for test/middleware/PoCIncorrectSumOfShares.t.sol:PoCIncorrectSumOfShares
[PASS] test_PoCIncorrectSumOfShares() (gas: 8309923)
Logs:
  Reward pool funded
  Reward share split set: 60/40
  Secondary asset-class & vault registered

  Creating nodes for Alice
  Creating node for Charlie
  Moved to one epoch
  Warped forward for rewards distribution
  Rewards distributed
  Total shares is greater than 10000 bp

Suite result: ok. 1 passed; 0 failed; 0 skipped; finished in 6.20ms (2.58ms CPU time)

Ran 1 test suite in 129.02ms (6.20ms CPU time): 1 tests passed, 0 failed, 0 skipped (1 total tests)
```

**Recommended Mitigation:** To correctly sum curator shares, ensure each curator's total share for the epoch is counted only once. This can be achieved by:

1.  **Tracking Unique Curators:** During the initial share calculation (e.g., in `_calculateAndStoreVaultShares`), maintain a data structure (like `EnumerableSet.AddressSet`) that stores the unique addresses of curators who earned shares in that epoch.
    ```solidity
     // Example: Add to state variables
     mapping(uint48 epoch => EnumerableSet.AddressSet) private _epochUniqueCurators;

     // In _calculateAndStoreVaultShares, after calculating curatorShare for a vault's owner:
     if (curatorShare > 0) {
         _epochUniqueCurators[epoch].add(VaultTokenized(vault).owner());
     }
    ```

2.  **Iterating Unique Curators in `claimUndistributedRewards`:** Modify the curator share summation loop to iterate over this set of unique curators.
    ```solidity
     // In claimUndistributedRewards:
     ...
     // Sum curator shares
     EnumerableSet.AddressSet storage uniqueCurators = _epochUniqueCurators[epoch];
     for (uint256 i = 0; i < uniqueCurators.length(); i++) {
         address curator = uniqueCurators.at(i);
         totalDistributedShares += curatorShares[epoch][curator];
     }
     ...
    ```
This ensures that `curatorShares[epoch][curatorAddress]` is added to `totalDistributedShares` precisely once for each distinct curator who earned rewards in the epoch.

**Suzaku:**
Fixed in commit [8f4adaa](https://github.com/suzaku-network/suzaku-core/pull/155/commits/8f4adaaca91402b1bde166f2d02c3ac9d72fc96c).

**Cyfrin:** Verified.

## [C-3] Vault rewards incorrectly scaled by cross-asset-class operator totals instead of asset class specific shares causing rewards leakage
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The current vault reward distribution logic causes systematic under-distribution of rewards to vault stakers. The issue stems from using cross-asset-class operator beneficiary share totals to scale individual vault rewards, instead of using asset-class-specific operator rewards. This causes a leakage of rewards in scenarios where operators have assymetric stake across different asset class IDs.

The `Rewards::_calculateAndStoreVaultShares` function incorrectly uses `operatorBeneficiariesShares[operator]` (which represents the operator's total rewards across ALL asset classes) to scale rewards for individual vaults that belong to specific asset classes. This creates an inappropriate dilution effect where vault rewards are scaled down by the operator's participation in other unrelated asset classes.

 First in `_calculateOperatorShare()` when calculating the operator's total share

```solidity
function _calculateOperatorShare(uint48 epoch, address operator) internal {
    // ... uptime calculations ...

    uint96[] memory assetClasses = l1Middleware.getAssetClassIds();
    for (uint256 i = 0; i < assetClasses.length; i++) {
        uint256 operatorStake = l1Middleware.getOperatorUsedStakeCachedPerEpoch(epoch, operator, assetClasses[i]);
        uint256 totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]);
        uint16 assetClassShare = rewardsSharePerAssetClass[assetClasses[i]];

        uint256 shareForClass = Math.mulDiv(
            Math.mulDiv(operatorStake, BASIS_POINTS_DENOMINATOR, totalStake),
            assetClassShare, // @audit asset class share applied here
            BASIS_POINTS_DENOMINATOR
        );
        totalShare += shareForClass;
    }
    // ... rest of function
    operatorBeneficiariesShares[epoch][operator] = totalShare; //@audit this is storing cross-asset total
```


Again in `_calculateAndStoreVaultShares()`, `operatorBeneficiariesShares` which is a cross-asset operator share is used to calculate vault share for a specific vault:

```solidity
function _calculateAndStoreVaultShares(uint48 epoch, address operator) internal {
    uint256 operatorShare = operatorBeneficiariesShares[epoch][operator]; // @audit already includes asset class weighting

    for (uint256 i = 0; i < vaults.length; i++) {
        address vault = vaults[i];
        uint96 vaultAssetClass = middlewareVaultManager.getVaultAssetClass(vault);

        // ... vault stake calculation ...

        uint256 vaultShare = Math.mulDiv(vaultStake, BASIS_POINTS_DENOMINATOR, operatorActiveStake);
        vaultShare = Math.mulDiv(vaultShare, rewardsSharePerAssetClass[vaultAssetClass], BASIS_POINTS_DENOMINATOR);
        vaultShare = Math.mulDiv(vaultShare, operatorShare, BASIS_POINTS_DENOMINATOR);
        //@audit Uses cross-asset operator total instead of asset-class-specific share
        // This scales vault rewards by operator's participation in OTHER asset classes
        // ... rest of function
    }
}
```

Net effect is, even if a specific operator contributes 100% of the vault stake, it gets scaled by the global operator share causing a leakage in rewards for that specific asset class.

**Impact:** Systematic under-rewards in every epoch where vault stakes receive less than what they should, and this excess is being reclaimed as undistributed rewards. Effectively, the actual reward distribution doesn't match intended asset class allocations.

**Proof of Concept:** The test demonstrates that even when all fees are zero, the vault share is only 92.5% of the epoch rewards. The 7.5% is attributed to the reward leakage that becomes part of undistributed rewards.

```text
  In the POC below,
- Asset Class 1: 50% share (5000 bp), 1000 total stake
- Asset Class 2: 20% share (2000 bp), 100 total stake
- Asset Class 3: 30% share (3000 bp), 100 total stake
- Operator B: 700/100/100 stake in classes 1/2/3 respectively
- Operator B's cross-asset total: (700/1000×5000) + (100/100×2000) + (100/100×3000) = 8500 bp
- Vault Share of Asset ID 2:
    - vaultShare = (100/100) × 2000 × 8500 / (10000 × 10000)
    - vaultShare = 1 × 2000 × 8500 / 100,000,000 = 1700 bp

Vault 2 should get Operator B's Asset Class 2 rewards only (2000 bp)
Instead, it gets scaled by operator's total across all classes (8500 bp)

This causes a dilution of 300 bp

```

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import {Test} from "forge-std/Test.sol";
import {console2} from "forge-std/console2.sol";

import {MockAvalancheL1Middleware} from "../mocks/MockAvalancheL1Middleware.sol";
import {MockUptimeTracker} from "../mocks/MockUptimeTracker.sol";
import {MockVaultManager} from "../mocks/MockVaultManager.sol";
import {MockDelegator} from "../mocks/MockDelegator.sol";
import {MockVault} from "../mocks/MockVault.sol";
import {ERC20Mock} from "@openzeppelin/contracts/mocks/token/ERC20Mock.sol";

import {Rewards} from "../../src/contracts/rewards/Rewards.sol";
import {IRewards} from "../../src/interfaces/rewards/IRewards.sol";
import {BaseDelegator} from "../../src/contracts/delegator/BaseDelegator.sol";
import {IVaultTokenized} from "../../src/interfaces/vault/IVaultTokenized.sol";

contract RewardsAssetShareTest is Test {
    // Contracts
    MockAvalancheL1Middleware public middleware;
    MockUptimeTracker public uptimeTracker;
    MockVaultManager public vaultManager;
    Rewards public rewards;
    ERC20Mock public rewardsToken;

    // Test addresses
    address constant ADMIN = address(0x1);
    address constant PROTOCOL_OWNER = address(0x2);
    address constant REWARDS_MANAGER = address(0x3);
    address constant REWARDS_DISTRIBUTOR = address(0x4);
    address constant OPERATOR_A = address(0x1000);
    address constant OPERATOR_B = address(uint160(0x1000 + 1));

    function setUp() public {
        // Deploy mock contracts - simplified setup for our POC
        vaultManager = new MockVaultManager();

        //Set up 2 operators
        uint256[] memory nodesPerOperator = new uint256[](2);
        nodesPerOperator[0] = 1; // Operator 0x1000 has 1 node
        nodesPerOperator[1] = 1; // Operator A has 1 node

        middleware = new MockAvalancheL1Middleware(
            2,
            nodesPerOperator,
            address(0),
            address(vaultManager)
        );

        uptimeTracker = new MockUptimeTracker();

        // Deploy Rewards contract
        rewards = new Rewards();
        rewardsToken = new ERC20Mock();

        // Initialize with no fees to match our simplified example
        rewards.initialize(
            ADMIN,
            PROTOCOL_OWNER,
            payable(address(middleware)),
            address(uptimeTracker),
            0, // protocolFee = 0%
            0, // operatorFee = 0%
            0, // curatorFee = 0%
            0  // minRequiredUptime = 0
        );

        // Set up roles
        vm.prank(ADMIN);
        rewards.setRewardsManagerRole(REWARDS_MANAGER);

        vm.prank(REWARDS_MANAGER);
        rewards.setRewardsDistributorRole(REWARDS_DISTRIBUTOR);

        // Set up rewards token
        rewardsToken.mint(REWARDS_DISTRIBUTOR, 1_000_000 * 10**18);
        vm.prank(REWARDS_DISTRIBUTOR);
        rewardsToken.approve(address(rewards), 1_000_000 * 10**18);
    }

    function test_AssetShareFormula() public {
        uint48 epoch = 1;

        // Set Asset Class 1 to 50% rewards share (5000 basis points)
        vm.prank(REWARDS_MANAGER);
        rewards.setRewardsShareForAssetClass(1, 5000); // 50%

        vm.prank(REWARDS_MANAGER);
        rewards.setRewardsShareForAssetClass(2, 2000); // 20%

        vm.prank(REWARDS_MANAGER);
        rewards.setRewardsShareForAssetClass(3, 3000); // 30%

        // Set total stake in Asset Class 1 = 1000 tokens across network
        middleware.setTotalStakeCache(epoch, 1, 1000);
        middleware.setTotalStakeCache(epoch, 2, 100);  // Asset Class 2: 0 tokens
        middleware.setTotalStakeCache(epoch, 3, 100);  // Asset Class 3: 0 tokens

        // Set Operator A stake = 300 tokens (30% of network)
        middleware.setOperatorStake(epoch, OPERATOR_A, 1, 300);

        // Set operator A node stake (for primary asset class calculation)
        bytes32[] memory operatorNodes = middleware.getOperatorNodes(OPERATOR_A);
        middleware.setNodeStake(epoch, operatorNodes[0], 300);

        // No stake in other asset classes for Operator A
        middleware.setOperatorStake(epoch, OPERATOR_A, 2, 0);
        middleware.setOperatorStake(epoch, OPERATOR_A, 3, 0);

        bytes32[] memory operatorBNodes = middleware.getOperatorNodes(OPERATOR_B);
        middleware.setNodeStake(epoch, operatorBNodes[0], 700); // Remaining Asset Class 1 stake
        middleware.setOperatorStake(epoch, OPERATOR_B, 1, 700);
        middleware.setOperatorStake(epoch, OPERATOR_B, 2, 100);
        middleware.setOperatorStake(epoch, OPERATOR_B, 3, 100);

        // Set 100% uptime for Operator A & B
        uptimeTracker.setOperatorUptimePerEpoch(epoch, OPERATOR_A, 4 hours);
        uptimeTracker.setOperatorUptimePerEpoch(epoch, OPERATOR_B, 4 hours);


        // Create a vault for Asset Class 1 with 300 tokens staked (100% of operator's stake)
        address vault1Owner = address(0x500);
        (address vault1, address delegator1) = vaultManager.deployAndAddVault(
            address(0x123), // collateral
            vault1Owner
        );
        middleware.setAssetInAssetClass(1, vault1);
        vaultManager.setVaultAssetClass(vault1, 1);

          // Create vault for Asset Class 2
        address vault2Owner = address(0x600);
        (address vault2, address delegator2) = vaultManager.deployAndAddVault(address(0x123), vault2Owner);
        middleware.setAssetInAssetClass(2, vault2);
        vaultManager.setVaultAssetClass(vault2, 2);

        // Create vault for Asset Class 3
        address vault3Owner = address(0x700);
        (address vault3, address delegator3) = vaultManager.deployAndAddVault(
            address(0x125), // different collateral
            vault3Owner
        );
        middleware.setAssetInAssetClass(3, vault3);
        vaultManager.setVaultAssetClass(vault3, 3);


        // Set vault delegation: 300 tokens staked to Operator A
        uint256 epochTs = middleware.getEpochStartTs(epoch);
        MockDelegator(delegator1).setStake(
            middleware.L1_VALIDATOR_MANAGER(),
            1, // asset class
            OPERATOR_A,
            uint48(epochTs),
            300 // stake amount
        );

        MockDelegator(delegator1).setStake(middleware.L1_VALIDATOR_MANAGER(),
                                            1,
                                            OPERATOR_B,
                                            uint48(epochTs),
                                            700);

        MockDelegator(delegator2).setStake(
            middleware.L1_VALIDATOR_MANAGER(), 2, OPERATOR_B, uint48(epochTs), 100
        );

        MockDelegator(delegator3).setStake(
            middleware.L1_VALIDATOR_MANAGER(), 3, OPERATOR_B, uint48(epochTs), 100
        );

        // Set rewards for the epoch: 100,000 tokens
        vm.prank(REWARDS_DISTRIBUTOR);
        rewards.setRewardsAmountForEpochs(epoch, 1, address(rewardsToken), 100_000);


        // Wait 3 epochs as required by contract
        vm.warp((epoch + 3) * middleware.EPOCH_DURATION());

        // Distribute rewards
        vm.prank(REWARDS_DISTRIBUTOR);
        rewards.distributeRewards(epoch, 2);

        // Get calculated shares
        uint256 operatorABeneficiariesShare = rewards.operatorBeneficiariesShares(epoch, OPERATOR_A);
        uint256 operatorBBeneficiariesShare = rewards.operatorBeneficiariesShares(epoch, OPERATOR_B);

        uint256 vault1Share = rewards.vaultShares(epoch, vault1);
        uint256 vault2Share = rewards.vaultShares(epoch, vault2);
        uint256 vault3Share = rewards.vaultShares(epoch, vault3);

        console2.log("=== RESULTS ===");
        console2.log("operatorBeneficiariesShares[OPERATOR_A] =", operatorABeneficiariesShare, "basis points");
        console2.log("vaultShares[vault_1] =", vault1Share, "basis points");
        console2.log("operatorBeneficiariesShares[OPERATOR_B] =", operatorBBeneficiariesShare, "basis points");
        console2.log("vaultShares[vault_2] =", vault2Share, "basis points");
        console2.log("vaultShares[vault_3] =", vault3Share, "basis points");

        // Expected: 30% stake * 50% asset class = 15% = 1500 basis points
        assertEq(operatorABeneficiariesShare, 1500,
            "Operator share should be 1500 basis points (15%)");
        assertEq(vault1Share, 5000,
            "Vault share should be 5000 basis points (7.5% + 42.5)");

        assertEq(operatorBBeneficiariesShare, 8500,
            "Operator share should be 9500 basis points (85%)"); //  (700/1000) × 50%  +  (100/100) × 20%  + (100/100) × 30% = 85%
        assertEq(vault2Share, 1700,
            "Vault share should be 1700 basis points (19%)");
            // vaultShare = (100 / 100) × 10,000 = 10,000 bp
            // vaultShare = 10,000 × 2,000 / 10,000 = 2,000 bp (vaultShare * assetClassShare / 10000)
            // vaultShare = 2,000 × 8,500 / 10,000 = 1,700 bp (vaultShare * operatorShare / 10000)

         assertEq(vault3Share, 2550,
            "Vault share should be 2550 basis points (28.5%)");
            // vaultShare = (100 / 100) × 10,000 = 10,000 bp
            // vaultShare = 10,000 × 3,000/10,000 = 3,000 bp (vaultShare * assetClassShare / 10000)
            // vaultShare = 3,000 × 8,500/10,000 = 2,550 bp (vaultShare * operatorShare / 10000)


    }
}
```

**Recommended Mitigation:** Consider implementing a per-asset class operator shares instead of total operator shares. The `operatorBeneficiariesShare` should be more granular and asset-id specific to prevent this leakage. Corresponding logic in `_calculateOperatorShare` and `_calculateAndStoreVaultShares` should be adjusted specific to each assetID.

```solidity
// Add per-asset-class tracking
mapping(uint48 epoch => mapping(address operator => mapping(uint96 assetClass => uint256 share)))
    public operatorBeneficiariesSharesPerAssetClass;
```

**Suzaku:**
Fixed in commit [f9bfdf7](https://github.com/suzaku-network/suzaku-core/pull/155/commits/f9bfdf7faa7023a0e662280a34cb41be145ba7ab).

**Cyfrin:** Verified.

## [M-4] `Myriad CTFExchange.filled Amounts` mapping slot and `hash Order` computed multiple times per order
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** In `MyriadCTFExchange::_matchOrders` (the inner settlement function called by every `matchOrdersWithFees` invocation), each order's `filledAmounts` slot is read three times:

```
line 360: require(filledAmounts[makerHash] + fillAmount <= maker.amount, …)  // cold SLOAD
line 366: filledAmounts[makerHash] += fillAmount;                             // warm SLOAD + SSTORE
line 389: emit OrdersMatched(…, filledAmounts[makerHash], …)                 // warm SLOAD
```

The same pattern applies to `takerHash`.

In `MyriadCTFExchange::matchCrossMarketOrders`, the problem compounds across N orders: `hashOrder(orders[i])` is computed in both the validation loop (line 242) and the distribution loop (line 295), and `filledAmounts[orderHash]` is read in the validation loop (line 243), then read-modified-written in the distribution loop (line 296), then read again for the emit (line 298).

**Recommended Mitigation:** Cache each value after its first read:

```solidity
// _matchOrders
uint256 makerFilled = filledAmounts[makerHash];
uint256 takerFilled = filledAmounts[takerHash];
require(makerFilled + fillAmount <= maker.amount, "maker overfill");
require(takerFilled + fillAmount <= taker.amount, "taker overfill");
makerFilled += fillAmount;
takerFilled += fillAmount;
filledAmounts[makerHash] = makerFilled;
filledAmounts[takerHash] = takerFilled;
// use makerFilled / takerFilled in the emit

// matchCrossMarketOrders — first loop: cache hash and current fill
bytes32[] memory orderHashes   = new bytes32[](orders.length);
uint256[] memory currentFilled = new uint256[](orders.length);
for (uint256 i = 0; i < orders.length; i++) {
    bytes32 h = hashOrder(orders[i]);
    orderHashes[i]   = h;
    currentFilled[i] = filledAmounts[h];
    require(currentFilled[i] + fillAmount <= orders[i].amount, "overfill");
    …
}
// second loop: use cached values
for (uint256 i = 0; i < orders.length; i++) {
    uint256 newFill = currentFilled[i] + fillAmount;
    filledAmounts[orderHashes[i]] = newFill;
    emit CrossMarketOrderFilled(orderHashes[i], eventId, orders[i].marketId, fillAmount, newFill);
}
```

**Myriad:** Fixed in commit [`968ca58`](https://github.com/Polkamarkets/polkamarkets-js/commit/968ca583d63c14f53b6cefcd192cee98e08a1bbe)

**Cyfrin:** Verified.

\clearpage

## [M-5] typo error in variables
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The variable `mint_token_prgoram_version` contains a typo: "prgoram" should be "program". This typo is repeated in the error message.

```rust

    let data = NewInstrumentData::new(instruction_data, root_state.tokens_count)?;
    let mint_token_prgoram_version = TokenProgram::new(asset_mint.owner)?;

    let token_program_version = TokenProgram::new(token_program.key)?;

    if token_program_version != mint_token_prgoram_version {
        bail!(DeriverseErrorKind::InvalidMintProgramId {
            expected: token_program_version,
            actual: mint_token_prgoram_version,
            mint_address: *asset_mint.key,
        });
    }
```



**Impact:** This does not affect functionality, it reduces code readability and consistency.

**Recommended Mitigation:** Rename the variable to mint_token_program_version:
```rust
-    let mint_token_prgoram_version = TokenProgram::new(asset_mint.owner)?;
+    let mint_token_program_version = TokenProgram::new(asset_mint.owner)?;

    let token_program_version = TokenProgram::new(token_program.key)?;

-    if token_program_version != mint_token_prgoram_version {
+    if token_program_version != mint_token_program_version {
        bail!(DeriverseErrorKind::InvalidMintProgramId {
            expected: token_program_version,
-            actual: mint_token_prgoram_version,
+            actual: mint_token_program_version,
            mint_address: *asset_mint.key,
        });
    }
```
**Deriverse:** Fixed in commit [a3c75ae8](https://github.com/deriverse/protocol-v1/commit/a3c75ae87eb1f7122b7be778223950aae3cd91b5).

**Cyfrin:** Verified.

## [M-7] Don't cache `calldata` array length
- Severity: `Medium`
- Source report: `harbor.md`

### Detailed Content (from source)
**Description:** It is [cheaper not to cache `calldata` array length](https://github.com/devdacian/solidity-gas-optimization?tab=readme-ov-file#6-dont-cache-calldata-length-effective-009-cheaper) (which is another reason why it is better to use `calldata` for input read-only arrays than `memory`):
* `ChainValidator::setvalidChains, setInvalidChains`

**SafeHarbor:**
Fixed in commit [af8cbc7](https://github.com/PatrickAlphaC/safe-harbor/commit/af8cbc70851ffcf1fb8d393e8fb91e7ad077ad70).

**Cyfrin:** Verified.

\clearpage

## [M-8] Inconsistency in `current Phase` between `p USDe Vault` and `y USDe Vault`
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Both `pUSDeVault` and `yUSDeVault` inherit the `PreDepositVault` which in turn inherits the `PreDepositPhaser`; however, there is an inconsistency between the state of `pUSDe::currentPhase`, which is updated when the phase changes, and `yUSDe::currentPhase`, which is never updated and is thus always the default `PointsPhase` variant. This is assumedly not an issue given that this state is never needed for the yUSDe vault, though a view function is exposed by virtue of the state variable being public which could cause confusion.

**Recommended Mitigation:** The simplest solution would be modifying this state to be internal by default and only expose the corresponding view function within `pUSDeVault`.

**Strata:** Fixed in commit [aac3b61](https://github.com/Strata-Money/contracts/commit/aac3b617084fb5a06b29728a9f52e5884b062b6a).

**Cyfrin:** Verified. The `yUSDeVault` now returns the `pUSDeVault` phase state.

\clearpage
## Gas Optimization

## [M-9] Inline small internal functions only used once
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** It is more gas efficient to inline small internal functions only used once.

For example `pUSDeDepositor::getPhase` is only called by `deposit_sUSDe`. Changing `deposit_sUSDe` to cache `pUSDe` then use the cached copy in the call to `PreDepositPhaser::currentPhase` saves 1 storage read in addition to saving the function call overhead.

**Strata:** Fixed in commit [9398379](https://github.com/Strata-Money/contracts/commit/93983791adbd45a555d947a12a5a6fd9bbfe7330).

**Cyfrin:** Verified.

## [M-10] Unnecessarily complex iteration logic in `Meta Vault::redeem Meta Vaults` can be simplified
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** `MetaVault::redeemMetaVaults` is currently implemented as a while loop, indexing the first array element and calling `MetaVault::removeVaultAndRedeemInner` which implements a "replace-and-pop" solution for removing elements from the `assetsArr` array:

```solidity
    function removeVaultAndRedeemInner (address vaultAddress) internal {
        // Redeem
        uint balance = IERC20(vaultAddress).balanceOf(address(this));
        if (balance > 0) {
            IERC4626(vaultAddress).redeem(balance, address(this), address(this));
        }

        // Clean
        TAsset memory emptyAsset;
        assetsMap[vaultAddress] = emptyAsset;
        uint length = assetsArr.length;
        for (uint i = 0; i < length; i++) {
            if (assetsArr[i].asset == vaultAddress) {
@>              assetsArr[i] = assetsArr[length - 1];
@>              assetsArr.pop();
                break;
            }
        }
    }

    function redeemMetaVaults () internal {
        while (assetsArr.length > 0) {
@>          removeVaultAndRedeemInner(assetsArr[0].asset);
        }
    }
```

While this logic is still required for use in `MetaVault::removeVault`, where the contract admin can manually remove a single underlying vault, it would be preferable to avoid re-using this functionality for `MetaVault::redeemMetaVaults`. Instead, starting at the final element and walking backwards would preserve the ordering of the array and avoid unnecessary storage writes.

**Strata:** Fixed in commit [fbb6818](https://github.com/Strata-Money/contracts/commit/fbb6818f5c1f621a25c58a40f1673609ad9611fb) and [98bd92d](https://github.com/Strata-Money/contracts/commit/98bd92d0aed75161332227239859c34161df1bcc).

**Cyfrin:** Verified. The logic has been simplified by iterating over the asset addresses, deleting the individual mapping entries, and finally deleting the array.


\clearpage

## [M-11] `SPBinary Prompt::get Score` and `get Result` conflict on what score users who didn't participate should receive, `get Score` also rewards users who got the wrong answer
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SPBinaryPrompt::getScore` returns 0 if a user didn't participate, but `getResult` calls `getScore`, and if the score is 0, returns `xpTIers[1]`.

`SPBinaryPrompt::getScore` also gives users a score based on the probability prediction even if the user chose the wrong answer, since it never checks `answerAIsWinner == reactions[questionId][player].answer`.

**Impact:** Users who didn't participate can actually get > 0 score if `xpTiers[1] > 0`. Users who didn't get the right answer still get rewarded based on their probability prediction.

**Recommended Mitigation:** Resolve the inconsistency between `SPBinaryPrompt::getScore` and `getResult`. Don't reward users who got the wrong answer.

**Majority Games:**
Fixed in commits [50657e9](https://github.com/Engage-Protocol/engage-protocol/commit/50657e94bb54245a456520c41982b882d2d08433), [a55eb19](https://github.com/Engage-Protocol/engage-protocol/commit/a55eb1998d08ebfff17e668887986878409cd8d5).

**Cyfrin:** Verified.

## [M-12] Rename all `session Id` to `game Id` or vice versa for consistency
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `sessionId` appears to be used interchangeably with `gameId`; for consistency it would be best to rename all `sessionId` to `gameId` (or vice versa) where the same meaning is intended:
```solidity
session/DefaultSession.sol
44:    error SessionIdMismatch(uint256 sessionId, uint256 assertionSessionId);
137:     * @param sessionId The session ID
144:        uint256 sessionId,
150:        require(SessionManager(sessionManager).getSessionState(sessionId) == SessionState.Ended, GameNotEnded());
152:            sessionId, resultCid, resolutionGitRepoAtCommitHash, proposedWinners, totalXPs, totalTimes, msg.sender
158:     * @param sessionId The session ID
161:    function recordResults(uint256 sessionId, bytes32 assertionId) public {
162:        require(SessionManager(sessionManager).getSessionState(sessionId) == SessionState.Ended, GameNotEnded());
164:            sessionId == assertions[assertionId].sessionId,
165:            SessionIdMismatch(sessionId, assertions[assertionId].sessionId)
168:        require(winners[sessionId].length == 0, WinnersAlreadyRecorded(sessionId));
170:        uint256[] memory questionIds = SessionManager(sessionManager).getQuestionsForGame(sessionId);
180:            userResult[assertion.sessionId][winner] =
184:        winners[sessionId] = assertion.winners;
195:                dataAssertion.sessionId,
201:            recordResults(assertions[assertionId].sessionId, assertionId);

session/ISessionStrategy.sol
24:    error WinnersAlreadyRecorded(uint256 sessionId);
57:     * @param sessionId The session ID
64:        uint256 sessionId,
73:     * @param sessionId The session ID
76:    function recordResults(uint256 sessionId, bytes32 assertionId) external;

reward/IRewardStrategy.sol
13:    error NotCreator(uint256 sessionId, address sender);
14:    error AlreadySet(uint256 sessionId);
15:    error NotCreated(uint256 sessionId);

offchain/uma/SessionResultAsserter.sol
20:        uint256 sessionId;
33:        uint256 indexed sessionId,
41:        uint256 indexed sessionId,
62:        uint256 sessionId,
79:                "sessionId asserted: ",
80:                sessionId,
107:            sessionId, resultCid, resolutionGitRepoAtCommitHash, asserter, false, winners, totalXPs, totalTimes
109:        emit DataAsserted(sessionId, resultCid, resolutionGitRepoAtCommitHash, asserter, assertionId);

reward/FixedRanksReward.sol
19:    event RankedRewardsUpdated(uint256 indexed sessionId, uint256[] rankedRewards);
21:    error RankedRewardsNotSet(uint256 sessionId);
22:    error InvalidRanks(uint256 sessionId, uint256 numRanks);
23:    error InvalidTotalPoints(uint256 sessionId, uint256 numPoints);
29:    mapping(uint256 sessionId => uint256[]) public rankedRewards;
47:     * @param sessionId The ID of the game
50:    function setRankedRewards(uint256 sessionId, uint256[] calldata _rankedRewards) external {
51:        require(sessionManager.getSessionState(sessionId) == SessionState.Created, NotCreated(sessionId));
52:        require(sessionManager.getCreator(sessionId) == msg.sender, NotCreator(sessionId, msg.sender));
53:        require(rankedRewards[sessionId].length == 0, AlreadySet(sessionId));
54:        require(_rankedRewards.length > 0, InvalidRanks(sessionId, _rankedRewards.length));
55:        require(_rankedRewards.length <= 20, InvalidRanks(sessionId, _rankedRewards.length));
62:        require(totalPoints == BASIS_POINTS, InvalidTotalPoints(sessionId, totalPoints));
64:        rankedRewards[sessionId] = _rankedRewards;
65:        emit RankedRewardsUpdated(sessionId, _rankedRewards);
69:    function getRewards(uint256 sessionId, address[] calldata winners, uint256 prizePool)
74:        require(rankedRewards[sessionId].length > 0, RankedRewardsNotSet(sessionId));
77:            rewards[i] = prizePool * rankedRewards[sessionId][i] / BASIS_POINTS;
82:    function getReward(uint256 sessionId, address[] calldata, uint256 position, uint256 prizePool)
87:        require(rankedRewards[sessionId].length > 0, RankedRewardsNotSet(sessionId));
88:        reward = prizePool * rankedRewards[sessionId][position] / BASIS_POINTS;

reward/ProportionalToXPReward.sol
19:    event NumberOfWinnersUpdated(uint256 indexed sessionId, uint256 numberOfWinners);
21:    error NumberOfWinnersMismatch(uint256 sessionId, uint256 numberOfWinners);
28:    mapping(uint256 sessionId => uint256 numberOfWinners) public numberOfWinners;
35:    function getRewards(uint256 sessionId, address[] calldata winners, uint256 prizePool)
40:        require(numberOfWinners[sessionId] == winners.length, NumberOfWinnersMismatch(sessionId, winners.length));
41:        ISessionStrategy sessionStrategy = ISessionStrategy(sessionManager.getSessionStrategy(sessionId));
45:            (, uint256 xp,) = sessionStrategy.userResult(sessionId, winners[i]);
56:    function getReward(uint256 sessionId, address[] calldata winners, uint256 position, uint256 prizePool)
61:        require(numberOfWinners[sessionId] == winners.length, NumberOfWinnersMismatch(sessionId, winners.length));
62:        ISessionStrategy sessionStrategy = ISessionStrategy(sessionManager.getSessionStrategy(sessionId));
66:            (, uint256 xp,) = sessionStrategy.userResult(sessionId, winners[i]);
75:    function setNumberOfWinners(uint256 sessionId, uint256 _numberOfWinners) external {
76:        require(sessionManager.getSessionState(sessionId) == SessionState.Created, NotCreated(sessionId));
77:        require(sessionManager.getCreator(sessionId) == msg.sender, NotCreator(sessionId, msg.sender));
78:        require(numberOfWinners[sessionId] == 0, AlreadySet(sessionId));
79:        numberOfWinners[sessionId] = _numberOfWinners;
80:        emit NumberOfWinnersUpdated(sessionId, _numberOfWinners);
```

**Majority Games:**
Fixed in commit [75663d1](https://github.com/Engage-Protocol/engage-protocol/commit/75663d17c2a514eac4ccc7c01bb2d780ed344ab3) - everything is now `sessionId`.

**Cyfrin:** Verified.

## [M-13] Refactor away unnecessary local variables in `Securitize Amm Nav Provider::_curve Buy, _curve Sell`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** In `SecuritizeAmmNavProvider::_curveBuy, _curveSell` the local variables `X, Y, kLocal` are only read once so there is no need to use them to cache storage, just read the storage slots directly when required:
```solidity
function _curveBuy(uint256 amountInQuote) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInQuote > 0, "amountInQuote=0");

    newQuote = quoteReserves + amountInQuote;
    newBase = k / newQuote;

    uint256 deltaBase = baseReserves - newBase;
    require(deltaBase > 0, "deltaBase=0");

    curvePriceWad = (amountInQuote * WAD) / deltaBase;
}

function _curveSell(uint256 amountInBase) internal view initialized returns (uint256 curvePriceWad, uint256 newBase, uint256 newQuote) {
    require(amountInBase > 0, "amountInBase=0");

    newBase = baseReserves + amountInBase;
    newQuote = k / newBase;

    uint256 deltaQuote = quoteReserves - newQuote;
    require(deltaQuote > 0, "deltaQuote=0");

    curvePriceWad = (deltaQuote * WAD) / amountInBase;
}
```

**Securitize:** Fixed in commit [5ca8229](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/5ca82293e642b42741dcded549d89e2f74a0f757).

**Cyfrin:** Verified.

\clearpage

## [M-14] `Trust Service::change Entity Owner` can overwrite existing `_new Owner` record, breaking 1-1 relationship between owners and addresses
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `TrustService::changeEntityOwner` can overwrite existing `_newOwner` record, breaking 1-1 relationship between owners and addresses.

**Proof of Concept:** Add PoC to `test/trust-service.test.ts`:
```typescript
    it('overwrite existing owner breaks 1-1 relationship', async function() {
      const [owner, firstOwner, secondOwner] = await hre.ethers.getSigners();
      const { trustService } = await loadFixture(deployDSTokenRegulated);

      // Setup: Create two entities with different owners
      await trustService.setRole(firstOwner, DSConstants.roles.ISSUER);
      await trustService.setRole(secondOwner, DSConstants.roles.ISSUER);

      const entity1 = "Entity1";
      const entity2 = "Entity2";

      const trustServiceFromFirst = await trustService.connect(firstOwner);
      await trustServiceFromFirst.addEntity(entity1, firstOwner);

      const trustServiceFromSecond = await trustService.connect(secondOwner);
      await trustServiceFromSecond.addEntity(entity2, secondOwner);

      // Verify initial state
      expect(await trustService.getEntityByOwner(firstOwner)).equal(entity1);
      expect(await trustService.getEntityByOwner(secondOwner)).equal(entity2);

      // Change entity1 owner from firstOwner to secondOwner
      await trustService.changeEntityOwner(entity1, firstOwner, secondOwner);

      // Bug: secondOwner now owns both entities in the forward mapping
      // but reverse mapping shows only entity1
      expect(await trustService.getEntityByOwner(secondOwner)).equal(entity1);
      // entity2 is now orphaned - no way to find its owner through getEntityByOwner

      // firstOwner has no entity in reverse mapping
      expect(await trustService.getEntityByOwner(firstOwner)).equal("");
    });
```

Run with: `npx hardhat test --grep "overwrite existing owner"`.

**Recommended Mitigation:** Add modifier `onlyNewEntityOwner(_newOwner)` to function `changeEntityOwner`.

**Securitize:** Fixed in commit [6cd6cca](https://github.com/securitize-io/dstoken/commit/6cd6ccae7201082e53befd6364aff8a1f57397f7); the relevant storage slots were deprecated and the associated functions were removed.

**Cyfrin:** Verified.

## [M-15] Cheaper not to cache `calldata` array length
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** It is [cheaper](https://github.com/devdacian/solidity-gas-optimization?tab=readme-ov-file#6-dont-cache-calldata-length-effective-009-cheaper) not to cache `calldata` array length:
* `BulkBalanceChecker::getTokenBalances`

**Securitize:** Fixed in commit [fd6eb3b](https://github.com/securitize-io/dstoken/commit/fd6eb3bc4b075ec5975bc8d05305bfcdda054847).

**Cyfrin:** Verified.

## [M-16] Unnecessary `_msg Sender()` call in `_resolve Vault Id` when `caller` parameter is available
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** In `RWASegWrap::_resolveVaultId()`, the function receives a `caller` parameter representing the address for which a vault ID should be resolved, but when calling `_addVault()`, it uses `_msgSender()` instead of the provided `caller` parameter. This creates an unnecessary function call and potential inconsistency since the `caller` parameter already contains the correct address.

```solidity
function _resolveVaultId(address caller) internal returns (uint256) {
    uint256 vaultId = getVaultId(caller);
    if (vaultId == 0) {
        vaultId = ++latestVaultId;
        ISegregatedVault vault = _deployVault(vaultId);
        _addVault(address(vault), vaultId, _msgSender()); // <- use caller directly
    }
    return vaultId;
}
```

**Impact:** The unnecessary `_msgSender()` call results in additional gas consumption and reduces code clarity by using different variables that should represent the same address.

**Recommended Mitigation:** Replace `_msgSender()` with the `caller` parameter in the `_addVault()` call:

```diff
function _resolveVaultId(address caller) internal returns (uint256) {
    uint256 vaultId = getVaultId(caller);
    if (vaultId == 0) {
        vaultId = ++latestVaultId;
        ISegregatedVault vault = _deployVault(vaultId);
-       _addVault(address(vault), vaultId, _msgSender());
+       _addVault(address(vault), vaultId, caller);
    }
    return vaultId;
}
```

**Securitize:** Fixed in commit [3e16e8](https://github.com/securitize-io/bc-securitize-vault-sc/commit/3e16e88ea071e3365e7fd0b70789b22c0f717ccd).

**Cyfrin:** Verified.

## [M-17] Cache result of external calls when result can't change between calls and is used multiple times
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** * `Tranche.sol`
```solidity
// configure
212:        IERC20[] memory tokens = cdo.strategy().getSupportedTokens();
213:        uint256 len = tokens.length;
214:        address strategy = address(cdo.strategy());
```

**Recommended Mitigation:**
```diff
++import { IStrategy } from "./interfaces/IStrategy.sol";
[…]
    function configure () external onlyCDO {
--      IERC20[] memory tokens = cdo.strategy().getSupportedTokens();
--      uint256 len = tokens.length;
--      address strategy = address(cdo.strategy());
++      address strategy = address(cdo.strategy());
++      IERC20[] memory tokens = IStrategy(strategy).getSupportedTokens();
++      uint256 len = tokens.length;
```

**Strata:**
Fixed in commit [732b1a8](https://github.com/Strata-Money/contracts-tranches/commit/732b1a8ee5ae0bda763f74556f89bbb28b63f784) by caching the result of the call `cdo::strategy` and re-using it.

**Cyfrin:** Verified.

\clearpage

## [M-18] `Pocket::exec With Value` does not emit native transfer event
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** The `Pocket::execWithValue` function sends native tokens via the `value` parameter but only emits `Executed(target, selector)`, not `NativeTransferred(to, amount)`:

```solidity
// Pocket.sol:107
result = target.functionCallWithValue(data, value);  // sends native tokens

emit Executed(target, selector);  // doesn't include value amount
```

This differs from `transferNative()` which properly emits `NativeTransferred(to, amount)` (line 130). Off-chain systems tracking native token movements through events will miss transfers made via `execWithValue()`, since the `Executed` event doesn't include the `value` parameter.

**Recommended Mitigation:** Emit `NativeTransferred` when value is sent to maintain consistency with `transferNative()`

```diff
function execWithValue(...) external onlyOwner returns (bytes memory result) {
    require(target != address(0), "Invalid target");
    result = target.functionCallWithValue(data, value);

    bytes4 selector;
    if (data.length >= 4) {
        selector = bytes4(data[:4]);
    }

+   if (value > 0) {
+       emit NativeTransferred(target, value);
+   }
    emit Executed(target, selector);
}
```

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified.

## [M-20] Use named mappings to explicitly indicate the purpose of keys and values
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Use named mappings to explicitly indicate the purpose of keys and values:
```
BetFactory.sol
22:    mapping(address => address) public tokenToPool;
```

**WannaBet:** Fixed in commit [a20d1e7](https://github.com/gskril/wannabet-v2/commit/a20d1e7acfbeee00cc891324b022fcf0afdd721b).

**Cyfrin:** Verified.

## [M-21] `bond Face Value` read in `Perpetual Bond::_convert To Bond` can be cached
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** The storage value `bondFaceValue` is read twice in [`PerpetualBond::__convertToBond`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L291-L294):
```solidity
function _convertToBond(uint256 assetAmount) internal view returns (uint256) {
    if (bondFaceValue == 0) return 0; // Prevent division by zero
    return (assetAmount * 1e18) / bondFaceValue;
}
```
The value can be cached and only read once:
```solidity
function _convertToBond(uint256 assetAmount) internal view returns (uint256) {
    // cache read
    uint256 _bondFaceValue = bondFaceValue;
    if (_bondFaceValue == 0) return 0; // Prevent division by zero
    return (assetAmount * 1e18) / _bondFaceValue;
}
```

**YieldFi:** Fixed in commit [`823b010`](https://github.com/YieldFiLabs/contracts/commit/823b010d74fd55fb88b31619c1a94dac2ef65ad3)

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-72] Missing storage gap in upgradeable parent contract causes storage slot collision risk
- Severity: `Medium`
- Source report: `rwasegwrap.md`

### Detailed Content (from source)
**Description:** The `VaultDeployer` abstract contract is designed to be upgradeable and inherited by child contracts `SegregatedVaultDeployer` and `SecuritizeVaultDeployer`. However, `VaultDeployer` lacks storage gap variables to reserve space for future upgrades.

Currently, `VaultDeployer` declares three state variables:
- `address public navProvider`
- `address internal admin`
- `address public upgradeableBeacon`

The child contracts add their own state variables after the parent's storage:
- `SecuritizeVaultDeployer` adds `redemptionAddress` and `feeManager`
- `SegregatedVaultDeployer` currently adds no additional state variables

In upgradeable contracts, when a parent contract adds new state variables in future versions, those variables are allocated to storage slots immediately following the existing parent variables. This will overwrite the storage slots currently occupied by child contract variables, leading to storage collision and data corruption.

While `BaseContract` (the grandparent) properly implements storage gaps with `uint256[50] private __gap`, the intermediate `VaultDeployer` contract breaks this pattern by not reserving space for its own future expansion.

**Impact:** If future versions of `VaultDeployer` add new state variables, they will overwrite child contract storage slots causing data corruption and potentially rendering deployed contracts unusable.

**Recommended Mitigation:** Add storage gap variables to `VaultDeployer` contract to reserve space for future upgrades. Choose either traditional storage gaps or ERC-7201 namespaced storage:

**Option 1: Traditional Storage Gap**
```diff
abstract contract VaultDeployer is IVaultDeployer, BaseContract {
    bytes32 public constant AGGREGATOR_ROLE = keccak256("AGGREGATOR_ROLE");

    address public navProvider;
    address internal admin;
    address public upgradeableBeacon;

+   // Reserve storage slots for future VaultDeployer upgrades
+   uint256[47] private __gap;

    // ... rest of contract
}
```

**Option 2: ERC-7201 Namespaced Storage**
```diff
abstract contract VaultDeployer is IVaultDeployer, BaseContract {
    /// @custom:storage-location erc7201:securitize.storage.VaultDeployer
    struct VaultDeployerStorage {
        address navProvider;
        address admin;
        address upgradeableBeacon;
    }

    // keccak256(abi.encode(uint256(keccak256("securitize.storage.VaultDeployer")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant VAULT_DEPLOYER_STORAGE_LOCATION = 0x...;

    function _getVaultDeployerStorage() private pure returns (VaultDeployerStorage storage $) {
        assembly {
            $.slot := VAULT_DEPLOYER_STORAGE_LOCATION
        }
    }

    // Update all variable access to use the storage struct
    // ... rest of contract
}
```

**Securitize:** Fixed in commit [3048c3](https://github.com/securitize-io/bc-securitize-vault-sc/commit/3048c3ee21d18fe3a30c4d55ec96332f379bbcdc).

**Cyfrin:** Verified.
