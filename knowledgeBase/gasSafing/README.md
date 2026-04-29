# gas Safing - 已修復 Medium/High Issues（完整版）

- 篩選：`Severity in {Medium, High}` 且 `Status = Fixed`
- 說明：本版為完整敘述，不做刪節號截斷
- 筆數：9

## F-2025-14449 - Incorrect Assumption of USDT Decimals Leads to Fee Miscalculations
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The protocol makes a fundamental and incorrect assumption about thedecimal precision of the `USDT` token by treating it as an 18-decimal ERC20asset. In reality, `USDT` uses 6 decimals, and this discrepancy introducessevere inconsistencies in all fee-related logic across the system. This incorrect assumption is embedded directly into the contract designthrough hardcoded constants and fee calculations that rely on 1e18precision. For example, the Subscription contract defines fee limits anddefaults using 18-decimal units: uint256 public constant `MAX_FEE` = 3 * 1e18; /* 3 `USDT` (18 decimals) */ … defaultFee = 1e18; This implementation implicitly assumes that 1 `USDT` == 1e18, which is false.On-chain `USDT` represents: 1 `USDT` = 1e6 As a result, all protocol fees are effectively scaled by 12 additional ordersof magnitude beyond their intended value. Any logic that relies on thesevalues - including registration, subscription renewal, level access, andcustom fee configuration- operates on incorrect economic assumptions. Because ERC20 tokens do not enforce a standard decimal size, this issueis not a theoretical edge case but a concrete integration flaw thatmanifests immediately when interacting with a real `USDT` contract. This vulnerability leads to protocol-wide economic breakage, including: Users being required to approve and transfer impossibly large USDTamounts as feesTransactions reverting due to insufficient balances or allowancesInability to onboard users or renew subscriptionsIncorrect fee reporting in off-chain services and UIs Assets: `Subscription.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed 17

### 修補方式（建議）
It is recommended to: replace the incorrect hardcoded number of decimals for `USDT` uint256 public constant `MAX_FEE` = 3 * 1e18; defaultFee = 1e18; with uint256 public constant `MAX_FEE` = 3 * 1e6; defaultFee = 1e6; edit the provided natspec comment to ensure it describes the correctsystem maximum limits 3 `USDT` (6 decimals) clearly document decimal handling expectations for integrators andfrontends Resolution: Fixed in f9604f9. The incorrect 18 decimals was replaced with the correctnumber 6 to represent the appropriate decimals number of the USDTtoken. 18

### 修補方式（實際）
Fixed in f9604f9. The incorrect 18 decimals was replaced with the correctnumber 6 to represent the appropriate decimals number of the USDTtoken. 18

## F-2025-14450 - Unstake() Function Behaves Di erently Than Documented System Requirement
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The project documentation explicitly claims that the contract verifies itstoken balance on every stake and claim/withdraw operation. The contract balance is checked on every stake and claim/withdraw operation. However, this guarantee is not upheld in the implementation of StakingAndRewards::`unstake()` function, which performs no explicit contract-balance validation prior to transferring tokens back to the user. Specifically,the `stake()` function enforces strict balance and safety constraints,including total staking caps and protection-system gating, function `stake(uint256 amount)` external onlyActive nonReentrant { `require(amount > 0, "Cannot stake 0")`; /* Cache contract balance for gas efficiency */ uint256 contractBalance = `IERC20(aceToken)`.`balanceOf(address(this)`); /* Check if new stakes are allowed under protection system */ bool protectionSystemActive = `isProtectionSystemActive()`; if (protectionSystemActive) { `revert("Protection system active: New stakes blocked to protect 2 x rewards")`; } `require(totalStaked + amount <= contractBalance, "Insufficient contra ct balance")`; } while `claimRewards()` routes through additional safeguards when liquidity isconstrained. function `claimRewards()` external onlyActive nonReentrant { require(`block.timestamp` >= lastClaimTime[`msg.sender`] + `HOURS`, "Cooldo wn active"); /* Cache user data to avoid multiple storage reads */ address user = `msg.sender`; uint256 userTotalStaked = 0; uint256 totalClaimed = 0; 19 /* Calculate user totals in gas-efficient loop */ for (uint i = 0; i < 2; i++) { if (activeStakes[user][i].active) { userTotalStaked += activeStakes[user][i].amount; totalClaimed += activeStakes[user][i].totalClaimed; } } require(totalClaimed < (userTotalStaked * `MAX_REWARD_MULTIPLIER`) / PE `RCENT_DENOMINATOR`, "Maximum rewards claimed"); uint256 stakingReward = `_calculateAllRewards`(user); /* Check if team rewards and foundation unlock are allowed under prot ection system */ bool protectionSystemActive = `isProtectionSystemActive()`; uint256 teamReward = 0; uint256 foundationUnlock = 0; if (stakingReward > 0 && !protectionSystemActive) { `_processTeamRewards`(user, stakingReward); } if (!protectionSystemActive) { teamReward = `_calculateTeamRewards`(user); foundationUnlock = ((stakingReward + teamReward) * `FOUNDATION_UNL` `OCK`) / `PERCENT_DENOMINATOR`; } In contrast, `unstake()` directly attempts to transfer the userʼs principalwithout first ensuring that the contract holds sufficient `ACE` balance. Such discrepancies between the functionʼs intended behavior and itsdocumentation can cause confusion for integrators, auditors, orcontributors who rely on NatSpec or other documentation forunderstanding the external interface of the protocol. Assets: `StakingAndRewards.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
It is recommended to fix the mismatch between the documentation andimplementation by either editing the documentation or introducing themissing protection features. Resolution: Fixed in commit f9604f9. `unstake()` now explicitly validates the contractʼs aceToken balance before transferring returnAmount to the user, aligning theimplementation with the documented guarantee that balance checks occuron stake and claim/withdraw flows and preventing misleading assumptionsby integrators and reviewers. 21

### 修補方式（實際）
Fixed in commit f9604f9. `unstake()` now explicitly validates the contractʼs aceToken balance before transferring returnAmount to the user, aligning theimplementation with the documented guarantee that balance checks occuron stake and claim/withdraw flows and preventing misleading assumptionsby integrators and reviewers. 21

## F-2025-14482 - Staking Capacity Permanently Lost as Stakes Complete
- 嚴重度：High
- Report source：Acecoin.pdf

### 問題內容（完整）
The totalStaked counter is never decremented when stakes completenaturally (by reaching the 2x reward limit). This counter is used in criticalchecks that determine whether new stakes are allowed, meaning over timethe system will incorrectly reject valid staking attempts. Example Scenario: 1000 users stake 1000 `ACE` each = totalStaked = 1,000,000 `ACE` All stakes complete 2x claimed), actual locked tokens = 0 totalStaked still shows 1,000,000 ACENew user tries to stake 100 `ACE` but fails because 1,000,100 > contractBalance / 2 When a stake completes in `_processFIFOStakeInactivity`, only totalActiveStaked is decremented: `StakingAndRewards.sol`: // Check if stake0 is now complete if (stake0.totalClaimed >= stake0MaxReward) { stake0.active = false; `_updateCountersForInactiveStake`(user, stake0.amount); totalActiveStaked -= stake0.amount; // `BUG`: totalStaked is `NOT` decremented here! } But totalStaked is used in the staking validation: `require(totalStaked + amount <= contractBalance, "Insufficient contract balan ce")`; /* Check for existing active stakes and validate amount */ bool hasActiveStake = activeStakes[`msg.sender`][0].active || activeStakes[`msg.sender`][1].active; if (hasActiveStake) { require(amount >= lastStakeAmount[`msg.sender`], "New stake must be greater than or equal to last stake"); 9 } uint256 potentialTotalStaked = totalStaked + amount; `require(potentialTotalStaked <= contractBalance / 2, "Total staked would exce ed 2x limit")`; The variable totalActiveStaked (which is correctly updated) is never used inthese checks. Impact Progressive System Degradation: As more stakes complete naturally, totalStaked continues to accumulate while actual locked tokensdecrease Staking Denial of Service: Eventually, the checks totalStaked + amount <= contractBalance and potentialTotalStaked <= contractBalance / 2 will faileven when the contract has plenty of capacity Permanent Lockout: Once totalStaked exceeds contractBalance / 2, nonew stakes can be created, even though the contract may havemillions of tokens available Protocol Death: The staking system will become completely unusablefor new participants once enough stakes complete Assets: `StakingAndRewards.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
Replace totalStaked with totalActiveStaked in the staking validation checks: function `stake(uint256 amount)` external onlyActive nonReentrant { `require(amount > 0, "Cannot stake 0")`; uint256 contractBalance = `IERC20(aceToken)`.`balanceOf(address(this)`); 10 bool protectionSystemActive = `isProtectionSystemActive()`; if (protectionSystemActive) { `revert("Protection system active: New stakes blocked to protect 2x rew ards")`; } // `FIX`: Use totalActiveStaked instead of totalStaked `require(totalActiveStaked + amount <= contractBalance, "Insufficient contr act balance")`; bool hasActiveStake = activeStakes[`msg.sender`][0].active || activeStakes[`msg.sender`][1].active; if (hasActiveStake) { require(amount >= lastStakeAmount[`msg.sender`], "New stake must be grea ter than or equal to last stake"); Use totalActiveStaked instead of totalStaked uint256 potentialTotalActiveStaked = totalActiveStaked + amount; `require(potentialTotalActiveStaked <= contractBalance / 2, "Total staked w ould exceed 2x limit")`; rest of function } Resolution: Fixed in commit f9604f9. The codebase updated `stake()` admission checksto use totalActiveStaked (live exposure) rather than totalStaked, and re-scoped totalStaked to a statistics-only metric, ensuring completed stakesno longer inflate capacity/2x-limit gating and preventing the progressivestaking lockout condition over time.

### 修補方式（實際）
Fixed in commit f9604f9. The codebase updated `stake()` admission checksto use totalActiveStaked (live exposure) rather than totalStaked, and re-scoped totalStaked to a statistics-only metric, ensuring completed stakesno longer inflate capacity/2x-limit gating and preventing the progressivestaking lockout condition over time.

## F-2026-14497 - Incorrect Referral Traversal in _add Downlines() Skips Intermediate Uplines
- 嚴重度：Medium
- Report source：Acecoin.pdf

### 問題內容（完整）
The Subscription::`_addDownlines`() function incorrectly traverses the referralhierarchy when propagating downline updates using current.referrers[level]. During registration, `register()` first builds the referrer chain via `_buildReferrerChain`(), storing up to 12 upstream referrer IDs in users[userId].referrers. This array is ordered such that: referrers[0 → direct referrer (parent)referrers[1 → referrer of the parentetc. The function `_addDownlines`() is then invoked to propagate the newlyregistered user across uplinesʼ downline structures. The functionadvances as follows for traversing the tree: current = users[current.referrers[level]]; which can be seen in the `_addDownlines`() function below: function `_addDownlines`(uint256 newUserId, uint256 referrerId) private { User storage current = users[referrerId]; // Cache constants for gas efficiency uint256 maxLevels = `MAX_LEVELS`; uint256 maxLevelsMinus1 = maxLevels - 1; for (uint256 level = 0; level < maxLevels; level++) { `if(current.id == 0)` break; /* Add to tier system instead of direct array push */ `addToTier(downlineTiers[current.id][level], newUserId)`; downlineCount[current.id][level]++; /* Update tier count if needed */ uint256 newTierCount = `getTierCount(downlineCount[current.id][lev el])`; if (newTierCount > downlineTierCount[current.id][level]) { downlineTierCount[current.id][level] = newTierCount; } emit `DownlineAdded(current.id, level, newUserId)`; 50 if (level < maxLevelsMinus1) { current = users[current.referrers[level]]; } else { break; } } } This logic incorrectly jumps to the level-th ancestor of the current node,rather than progressing through the immediate upline (referrers[0 . As thelevel increases, this causes the traversal to skip intermediate ancestors,resulting in misplaced downline assignments and desynchronized per-level accounting. For instance, for the built chain of referrers: level 0 referrer 5004 level 1 referrer 5003 level 2 referrer 5002 level 3 referrer 5001 level 4 referrer 5000 level 5 referrer 1 the `_addDownlines`() loops them as follows: 5004 5003 5001 instead of 5004 5003 5002 5001 5000 1 This issue silently corrupts referral accounting and becomes increasinglysevere as the referral depth grows. Assets: `Subscription.sol` [https://github.com/AMGAceToken/Ace-SmartContracts] Status: Fixed

### 修補方式（建議）
It is recommended to: always advance the traversal using the direct upline relationship: current = users[current.referrers[0]]; add invariant checks: ensure that per-level downline counts areconsistent with aggregate totals after updates.add unit tests: Include multi-level referral scenarios that verify:no ancestor is skippeddownline tiers align correctly with referral depthper-level and total counters remain synchronizedif the downlineCount mapping is not expected to be used, considerdeleting it. Resolution: Fixed in commit f9604f9. Subscription::`_addDownlines`() was corrected totraverse the upline chain step-by-step by always advancing via the directparent (current.referrers[0]) rather than jumping to current.referrers[level].

### 修補方式（實際）
Fixed in commit f9604f9. Subscription::`_addDownlines`() was corrected totraverse the upline chain step-by-step by always advancing via the directparent (current.referrers[0]) rather than jumping to current.referrers[level].

## F-2026-14653 - Incorrect Before Swap Delta Mapping Causes Fee To Be Applied To Wrong Swap Side
- 嚴重度：High
- Report source：Launchly.pdf

### 問題內容（完整）
In Uniswap v4, hooks can return a BeforeSwapDelta to adjust swapaccounting before execution.Importantly, BeforeSwapDelta is defined in terms of specified andunspecified currencies, not currency0 and currency1.Key Uniswap v4 concepts required to understand this issue: A swap has two modes:Exact input (amountSpecified < 0)Exact output (amountSpecified > 0)In exact-input swaps:specified currency = input tokenunspecified currency = output token `BeforeSwapDelta(specifiedDelta, unspecifiedDelta)` applies balanceadjustments based on this rule. This contract explicitly restricts `_beforeSwap` to exact-input swaps only: `require(params.amountSpecified < 0, "unexpected amount sign")`; Therefore, in this function the specified currency is always the inputtoken. In the contract, when the native currency is the input, the hook: Takes a 2% fee from the native input currency using the `poolManager.take()` function. Returns a BeforeSwapDelta intended to account for that fee. However, the returned delta is chosen based on whether the nativecurrency is currency0 or currency1, instead of whether it is the specifiedcurrency. if (`Currency.unwrap(nativeCurrency)` == `Currency.unwrap(key.currency0)`) { return ( BaseHook.beforeSwap.selector, `toBeforeSwapDelta(int128(int256(feeAmount)`), 0), 0 8 ); } else { return ( BaseHook.beforeSwap.selector, `toBeforeSwapDelta(0, int128(int256(feeAmount)`)), 0 ); } This logic assumes: first delta field corresponds to currency0 second delta field corresponds to currency1 In Uniswap v4, this assumption is incorrect. The two fields correspond tospecified and unspecified currencies. For example, let's assume: currency0 = ERC20 currency1 = native zeroForOne == false (so swap currency1 to currency0)exact-input swap Then: input token = currency1 (native)specified currency = nativethe fee is correctly taken from native input To deduct the fee from the userʼs exact input, the hook must apply thedelta to the specified component: `BeforeSwapDelta(specifiedDelta = feeAmount, unspecifiedDelta = 0)` Instead, the current code returns: `BeforeSwapDelta(0, feeAmount)` This applies the delta to the unspecified (output) side, while the fee wastaken from the input. The specified amount sent to the pool is therefore notreduced, and accounting becomes inconsistent. As a result: The fee delta is applied to the wrong swap component.The specified amount sent to the pool does not correctly reflect thededucted fee.This creates an accounting mismatch between the hookʼs `take()` calland the returned delta.Depending on PoolManager invariant enforcement, this may: 9 revert the swap (denial of service), ormischarge the user by affecting the wrong leg of the swap. This issue occurs even though the hook restricts itself to exact-inputswaps. Assets: `src/LaunchlyBNBHook.sol`[https://github.com/ashutoshchaturvedi08/audit-v4-hook] Status: Fixed

### 修補方式（建議）
The hook must return BeforeSwapDelta based on specified/unspecifiedsemantics, not on currency0 / currency1. Since `_beforeSwap` only allows exact-input swaps, the fee is always takenfrom the specified currency.Therefore, the delta should always be applied to the specified side,regardless of whether the token is currency0 or currency1. Example Fix. Replace the conditional delta logic with keeping only: return ( BaseHook.beforeSwap.selector, `toBeforeSwapDelta(int128(int256(feeAmount)`), 0), 0 ); This correctly expresses: “the specified (input) currency pays the fee”independent of pool token ordering If support for exact-output swaps is added in the future, the deltaplacement must then be adjusted based on swap mode as well. 10 Resolution: Fixed in commit a8f07f4. The beforeSwap fee accounting logic was updatedto correctly apply BeforeSwapDelta using Uniswap v4ʼs specified/unspecifiedsemantics rather than relying on currency0/currency1 ordering. The hooknow always applies the fee delta to the specified (input) currency forexact-input swaps, ensuring that the accounting delta matches thecurrency from which the fee is actually taken. This eliminates swapaccounting mismatches and prevents potential reverts or incorrect feeapplication caused by applying the delta to the wrong swap leg.

### 修補方式（實際）
Fixed in commit a8f07f4. The beforeSwap fee accounting logic was updatedto correctly apply BeforeSwapDelta using Uniswap v4ʼs specified/unspecifiedsemantics rather than relying on currency0/currency1 ordering. The hooknow always applies the fee delta to the specified (input) currency forexact-input swaps, ensuring that the accounting delta matches thecurrency from which the fee is actually taken. This eliminates swapaccounting mismatches and prevents potential reverts or incorrect feeapplication caused by applying the delta to the wrong swap leg.

## F-2026-14654 - After Swap Return Delta Applied To Unspeci ed Currency Breaks Exact-Output Fee Charging
- 嚴重度：Medium
- Report source：Launchly.pdf

### 問題內容（完整）
In Uniswap v4, when a hook enables afterSwapReturnDelta, the `_afterSwap` callback must return an int128 delta.This returned value is always interpreted as a delta on the “unspecified”currency, i.e., the currency that is not tied to SwapParams.amountSpecified. The “unspecified” currency depends on swap mode: Exact input (amountSpecified < 0): unspecified = output tokenExact output (amountSpecified > 0): unspecified = input token Within the contract, when native currency is the output, the hookcalculates a 2% fee on the native output amount, takes that fee from thenative currency via `poolManager.take()` function, and returns the fee amountas the afterSwap delta: Currency nativeCurrency = !params.zeroForOne ? key.currency0 : key.currency1; poolManager.take(nativeCurrency, `FEE_RECIPIENT`, feeAmount); emit `FeeCollected(Currency.unwrap(nativeCurrency)`, feeAmount, false); return (BaseHook.afterSwap.selector, `int128(int256(feeAmount)`)); This is consistent for exact-input swaps because the unspecified currencyis the output token, so the returned delta is applied to the output `leg(native)`, matching the currency taken. However, for exact-output swaps: specified = output token (native)unspecified = input token (non-native) The hook still takes the fee from native output, but BaseHook.afterSwap willapply the returned delta to the unspecified leg (input). This causes amismatch between the currency actually taken and the currency beingadjusted by the returned delta. Exact-output swaps are only blocked in `_beforeSwap` when native is the input. Exact-output swaps where native isthe output are still reachable and will execute this `_afterSwap` path. As a result: The hookʼs fee extraction (take in native output) and the returned `delta(applied to input in exact-output mode)` are inconsistent.This can create an accounting imbalance during settlement and may:revert the swap (denial of service for exact-output swaps withnative output), or 13 mischarge by charging the fee on the wrong leg depending onsettlement behaviour. Assets: `src/LaunchlyBNBHook.sol`[https://github.com/ashutoshchaturvedi08/audit-v4-hook] Status: Fixed

### 修補方式（建議）
Ensure the fee is taken from the same leg that the afterSwap return delta isapplied to.A minimal fix consistent with the current design is to disallow exact-outputswaps in `_afterSwap`: Example fix: `require(params.amountSpecified < 0, "exact-output not supported")`; Alternatively, if exact-output support is required, charge the fee on theunspecified leg when amountSpecified > 0 (i.e., charge input instead ofoutput in that mode) or redesign fee collection so `take()` and the returneddelta always refer to the same currency leg. Resolution: Fixed in commit a8f07f4. The hook now explicitly disallows exact-outputswaps in afterSwap (`require(amountSpecified < 0)`), preventing the scenariowhere the returned afterSwap delta is applied to the unspecified (input)currency while the fee is taken from native output, which previously couldcause accounting mismatches and swap reverts. 14

### 修補方式（實際）
Fixed in commit a8f07f4. The hook now explicitly disallows exact-outputswaps in afterSwap (`require(amountSpecified < 0)`), preventing the scenariowhere the returned afterSwap delta is applied to the unspecified (input)currency while the fee is taken from native output, which previously couldcause accounting mismatches and swap reverts. 14

## F-2025-13516 - Storage Inconsistency in `migrate Token Manager`Function Leading to Data Corruption
- 嚴重度：Medium
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The migrateTokenManager function in the TokenManager library contains astorage inconsistency bug that corrupts contract state during migrationoperations. When migrating token managers from the legacy NodeManagementV3 contract to the new StargateNFT contract, the function failsto clean up previous manager mappings, resulting in multiple usersappearing to manage the same token simultaneously. This vulnerability affects the integrity of the token management system inseveral ways: Migration Data Corruption During the migration from NodeManagementV3 to StargateNFT, all migrated token manager relationships will becorrupted, creating inconsistent storage state that cannot be easilyremediated. View Function Inconsistency: The contract's view functions returncontradictory information about token management relationships.While `getTokenManager()` and `isTokenManager()` return correct data, `idsManagedBy()` returns stale entries, leading to developer confusion andpotential integration issues. Gas Inefficiency: Users with stale entries in their managerToTokenIds mapping will experience increased gas costs when calling `idsManagedBy()` due to unnecessary `tokenExists()` checks on tokens theyno longer manage. While this bug does not directly impact the core Stargate protocolfunctionality (staking, delegation, rewards), it compromises data integrityand creates significant risks for the upcoming migration process and futureecosystem integrations. `TokenManager.sol` LoC 80 91 /// @notice Migrate a token manager to the StargateNFT contract without doing any checks, /// this function is used to migrate the storage from NodeManagementV3 to Sta rgateNFT, /// after the migration we can remove this function /// @param `_tokenId` The ID of the token to migrate /// @param `_manager` The address of the manager to migrate function migrateTokenManager( DataTypes.StargateNFTStorage storage $, uint256 `_tokenId`, address `_manager` ) external { 35 // `MISSING`: Cleanup of existing manager before setting new one // Update mappings for delegation $.managerToTokenIds[`_manager`].add(`_tokenId`); $.tokenIdToManager[`_tokenId`] = `_manager`; // Emit event for delegation emit TokenManagerAdded(`_tokenId`, `_manager`); } The function directly sets the new manager without removing the tokenfrom the previous manager's managerToTokenIds set, creating storageinconsistency. Assets: `packages/contracts/contracts/StargateNFT/StargateNFT.sol`[https://github.com/vechain/stargate]packages/contracts/contracts/StargateNFT/libraries/TokenManager.sol[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
Update the migrateTokenManager function to include proper cleanup logic: function migrateTokenManager( DataTypes.StargateNFTStorage storage $, uint256 `_tokenId`, address `_manager` ) external { // `ADD`: Cleanup existing manager before setting new one if (`_hasTokenManager`($, `_tokenId`)) { address currentManager = $.tokenIdToManager[`_tokenId`]; $.managerToTokenIds[currentManager].remove(`_tokenId`); emit TokenManagerRemoved(`_tokenId`, currentManager); 36 } // Update mappings for delegation $.managerToTokenIds[`_manager`].add(`_tokenId`); $.tokenIdToManager[`_tokenId`] = `_manager`; // Emit event for delegation emit TokenManagerAdded(`_tokenId`, `_manager`); } Resolution: The finding is fixed in commit hash aef891e after adding cleanup logic tothe `migrateTokenManager()` function. The fix retrieves the current managerfrom tokenIdToManager[`_tokenId`], removes the token from the old manager'sset (managerToTokenIds[currentManager].remove(`_tokenId`)), and emits a removalevent before adding the new manager. 37

### 修補方式（實際）
The finding is fixed in commit hash aef891e after adding cleanup logic tothe `migrateTokenManager()` function. The fix retrieves the current managerfrom tokenIdToManager[`_tokenId`], removes the token from the old manager'sset (managerToTokenIds[currentManager].remove(`_tokenId`)), and emits a removalevent before adding the new manager. 37

## F-2025-13786 - Missing E ective Stake Decrease During Unstake
- 嚴重度：High
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The `unstake()` function in `Stargate.sol` fails to decrease the effective stakefrom the validator when a user unstakes a token that was previously in `PENDING` or `EXITED` delegation status. This creates a accounting vulnerabilitysimilar to the redelegation issue, where effective stake remains inflated onvalidators even after tokens are unstaked and burned. function unstake(uint256 `_tokenId`) external { StargateStorage storage $ = `_getStargateStorage`(); Delegation memory delegation = `_getDelegationDetails`($, `_tokenId`); // check the delegation status if (delegation.status == DelegationStatus.`ACTIVE`) { revert InvalidDelegationStatus(`_tokenId`, DelegationStatus.`ACTIVE`); } else if (delegation.status != DelegationStatus.`NONE`) { // Step 1: Withdraw `VET` from protocol $.`protocolStakerContract.withdrawDelegation(delegation.delegationId)`; emit DelegationWithdrawn( `_tokenId`, delegation.validator, delegation.delegationId, delegation.stake ); // [!] `MISSING`: No decrease of effective stake from validator! } if (delegation.status == DelegationStatus.`PENDING`) { emit `DelegationExitRequested(…)`; } // Step 2: Claim rewards (if any) if (`_exceedsMaxClaimablePeriods`($, `_tokenId`)) { revert `MaxClaimablePeriodsExceeded()`; } `_claimRewards`($, `_tokenId`); // Step 3: Reset delegation details `_resetDelegationDetails`($, `_tokenId`); // Only resets mappings, not effec tive stake! // Step 4: Burn token 27 $.stargateNFTContract.burn(`_tokenId`); // Step 5: Return `VET` to user (bool success, ) = `msg.sender`.call{ value: token.vetAmountStaked }(""); } When a user unstakes a token that has a `PENDING` or `EXITED` delegation the `unstake()` function: Withdraws `VET` from protocol Claims pending rewards Does `NOT` decrease effective stake from the validator Resets delegation mappings Burns the token Returns `VET` to user As a result, the validator's delegatorsEffectiveStake remains permanentlyinflated with the stake from the burned token. Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
Consider implementing additional delegation statuses to differentiatevalidator exit due to failing block production and conscious user delegationexit. Process the cases separately in the unstake functions. if (delegation.status == DelegationStatus.`PENDING`) { … `_updatePeriodEffectiveStake`($, validator, `_tokenId`, periods, false); } if (delegation.status == DelegationStatus.`FORCED_EXIT`) { 28 … } if (delegation.status == DelegationStatus.`VOLUNTARY_EXIT`) { … // No need to update effective stake as updated in `requestDelegationExit ` } Resolution: The finding is fixed in commit hash eb5b8cb after adding validator statuschecks in the `unstake()` function. The fix properly decreases delegatorsEffectiveStake when unstaking tokens with `PENDING` delegationstatus or `EXITED` validator status, preventing permanent inflation of thevalidator's effective stake accounting.

### 修補方式（實際）
The finding is fixed in commit hash eb5b8cb after adding validator statuschecks in the `unstake()` function. The fix properly decreases delegatorsEffectiveStake when unstaking tokens with `PENDING` delegationstatus or `EXITED` validator status, preventing permanent inflation of thevalidator's effective stake accounting.

## F-2026-14778 - [Dual Defense] Double E ective Stake Reduction on Redelegation Leading to Arithmetic Under ow
- 嚴重度：High
- Report source：Vechain Foundation.pdf

### 問題內容（完整）
The contract incorrectly reduces a validator's effective stake twice for thesame token when a user requests a delegation exit and later unstakes afterthe validator transitions to `VALIDATOR_STATUS_EXITED`. This double reductionoccurs because both `requestDelegationExit()` and `unstake()` independentlycall `_updatePeriodEffectiveStake`() to decrease the effective stake for thesame period, without checking whether the reduction has already beenapplied. Affected Functions: `requestDelegationExit()`, `unstake()`, `_updatePeriodEffectiveStake`(). In `requestDelegationExit()`: // Reduces effective stake when exit is requested (, , , uint32 completedPeriods) = $.protocolStakerContract.getValidationPerio `dDetails( delegation.validator )`; `_updatePeriodEffectiveStake`($, delegation.validator, `_tokenId`, completedPerio ds + 2, false); In `unstake()`: // Reduces effective stake again if validator is exited if ( currentValidatorStatus == `VALIDATOR_STATUS_EXITED` || delegation.status == DelegationStatus.`PENDING` ) { (, , , uint32 oldCompletedPeriods) = $.protocolStakerContract.getValidati `onPeriodDetails(delegation.validator)`; `_updatePeriodEffectiveStake`( $, delegation.validator, `_tokenId`, oldCompletedPeriods + 2, false // decrease ); } Core Function `_updatePeriodEffectiveStake`(): 31 function `_updatePeriodEffectiveStake`( StargateStorage storage $, address `_validator`, uint256 `_tokenId`, uint32 `_period`, bool `_isIncrease` ) private { uint256 effectiveStake = `_calculateEffectiveStake`($, `_tokenId`); uint256 currentValue = $.delegatorsEffectiveStake[`_validator`].upperLookup (`_period`); uint256 updatedValue = `_isIncrease` ? currentValue + effectiveStake : currentValue - effectiveStake; $.delegatorsEffectiveStake[`_validator`].push(`_period`, `SafeCast.toUint224(u pdatedValue)`); } DoS via Underflow: The cumulative double reductions could causearithmetic underflow, reverting future unstake operations for other users. Reward Calculation Corruption: The validator's effective stake is used tocalculate reward distribution among delegators. Double reductionartificially deflates the validator's total effective stake. Assets: `packages/contracts/contracts/Stargate.sol`[https://github.com/vechain/stargate] Status: Fixed

### 修補方式（建議）
報告未提供建議修補段落。

### 修補方式（實際）
The Finding is addressed in the b601538 commit. Checks in the unstake and `_delegate` functions are updated to prevent effective stake reduction in 32 case exit was requested via the requestDelegationExit function. if ( (currentValidatorStatus == `VALIDATOR_STATUS_EXITED` && !`_hasRequestedExit`($, `_tokenId`)) || delegation.status == DelegationStatus .`PENDING` ) …

## Cyfrin Fixed Issues (Merged)
- Count: `8`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] State changes without events
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
There are state variable changes in this function but no event is emitted. Consider emitting an event to enable offchain indexers to track the changes.

- [Line: 47](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/modules/GlobalRegistry.sol#L47)

	```solidity
	    function setSecurityAdmin(address securityAdmin_) external onlyOwner {
	```

- [Line: 53](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/modules/GlobalRegistry.sol#L53)

	```solidity
	    function setOperationsAdmin(address operationsAdmin_) external onlyOwner {
	```

- [Line: 59](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/modules/GlobalRegistry.sol#L59)

	```solidity
	    function setTreasury(address treasury_) external onlyOwner {
	```

- [Line: 65](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/modules/GlobalRegistry.sol#L65)

	```solidity
	    function setVaultFactory(address vaultFactory_) external onlyOwner {
	```

- [Line: 71](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/src/modules/GlobalRegistry.sol#L71)

	```solidity
	    function setRewardsFactory(address rewardsFactory_) external onlyOwner {
	```

**Accountable:** Fixed in commit [`13600f4`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/13600f460f9796f16d151d19dc4a1d5c35c1475d)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-2] ERC 1155 `safe Transfer From` callbacks forward unbounded gas to EIP 7702 EOAs
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** When the exchange distributes outcome tokens to traders, every transfer goes through ERC-1155 `safeTransferFrom`, which checks whether the recipient has code and, if so, invokes `onERC1155Received` with no explicit gas cap. Historically this was safe for EOA recipients because `to.code.length` returned zero, skipping the callback entirely. With EIP-7702, however, an EOA can set a delegation designator in its code field, causing `to.code.length > 0` to evaluate to `true` and triggering the full acceptance check:

```solidity
// ERC1155Utils.sol:33-49
if (to.code.length > 0) {
    try IERC1155Receiver(to).onERC1155Received(operator, from, id, value, data) returns (bytes4 response) {
        if (response != IERC1155Receiver.onERC1155Received.selector) {
            revert IERC1155Errors.ERC1155InvalidReceiver(to);
        }
    } catch ...
}
```

The `try` call forwards all available gas minus the 1/64 retained by EIP-150. This means the callback recipient receives approximately `(63/64)^2 ≈ 96.9%` of the remaining gas at that point in execution, an enormous budget paid for entirely by the operator.

This affects three settlement paths inside `MyriadCTFExchange`:

- `MyriadCTFExchange::matchCrossMarketOrders` — the most dangerous path. We iterate over every order in a loop and call `ConditionalTokens::safeTransferFrom` for each one. An attacker placed at index `i=0` receives the callback first and can burn enough gas to starve all subsequent iterations, reverting the entire batch.
- `MyriadCTFExchange::_settleMintMatch` — two sequential `safeTransferFrom` calls distribute outcome-0 and outcome-1 tokens. The first trader's callback fires before the second transfer, creating the same gas-draining window.
- `MyriadCTFExchange::_settleDirectMatch` — a single `safeTransferFrom` from seller to buyer fires the callback on the buyer.

For each of the above paths the attacker can approach this in two different ways.

1) Siphon enough gas to execute their own logic without causing the transaction to later revert. This could be simple arbitrage swaps or other actions that are typically unprofitable due to gas cost but with that cost removed for the attacker it is now a viable strategy.

2) Consume gas in the callback so that it doesn't revert on their `safeTransfer`, but instead reverts on a later traders `safeTransfer` with an Out Of Gas revert reason. Depending on the off chain gas griefing mitigation logic, this can result in the later traders order being blacklisted since it technically caused the OOG revert. With the real attackers order not being properly blacklisted repeated attempts at `matchCrossMarketOrders` will cause many honest orders to not be executed.

An attack would go as follows:

1. Attacker EOA sets a delegation designator via EIP-7702 pointing to a contract whose `onERC1155Received` performs expensive storage writes, then returns the correct selector.
2. Attacker signs a valid cross-market buy order and submits it to the operator's order book.
3. The operator batches the attacker's order with honest traders' orders and calls `MyriadCTFExchange::matchCrossMarketOrders`.
4. During the distribution loop, the attacker at index 0 receives the `onERC1155Received` callback with ~90% of remaining gas and burns it writing to attacker-controlled storage.
5. When the loop advances to index 3, insufficient gas remains for the next `safeTransferFrom`. The call reverts OOG, rolling back the entire transaction including all honest traders' fills.
6. The operator's error-tracing logic sees the OOG at index 3 and may incorrectly flag the honest trader at that index as the source of the grief.

**Impact:** An EIP-7702-enabled EOA placed in a cross-market or mint-match batch siphons the operator's gas to subsidize its own on-chain operations, or burns enough gas to revert the entire settlement transaction. In `matchCrossMarketOrders`, this causes honest traders' fills to fail with an out-of-gas error that off-chain tracing may attribute to the wrong trader, risking incorrect blacklisting of innocent addresses.


**Recommended Mitigation:** Wrap each `safeTransferFrom` where the `to` address is an arbitrary trader in a low-level call with an explicit gas cap so that no single callback can consume the gas budget needed for subsequent iterations. This will prevent users from consuming more than allowed gas as well as allow for direct traces to malicious traders who's order should be blacklisted.

**Myriad:** Fixed in commit [`c820bcf`](https://github.com/Polkamarkets/polkamarkets-js/commit/c820bcfbd28347c161529e0d89fab11eff9ee87f)

**Cyfrin:** Verified.

\clearpage

## [M-3] Remove unused constant `Cryptoart NFT::ROYALTY_BASE`
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The `CryptoartNFT` contract defines a constant `ROYALTY_BASE` with a value of 10,000 that is never used in the contract. This constant is intended to represent the denominator for royalty percentage calculations (where 10,000 = 100%), but it's not referenced anywhere in the contract's implementation.

**Recommended Mitigation:** Remove the unused constant to improve code clarity and reduce deployment gas costs.

**Cryptoart:**
Fixed in commit [0c0dd8c](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/0c0dd8c8d01e1b5b396852d38faceee007b37891).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-4] Remove unnecessary imports and inheritance
- Severity: `Medium`
- Source report: `pledge.md`

### Detailed Content (from source)
**Description:** Remove unnecessary imports and inheritance:
* `BurnStateManager` should only import and inherit from `Initializable`

**Remora:** Fixed in commit [8419903](https://github.com/remora-projects/remora-smart-contracts/commit/84199034d7255cfc90cd6eef502616a874f26908).

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-5] `Session Manager::cancel Game If Creator Missing, end Game` could revert due to out of gas if there are too many question in a game
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** Since there are no restrictions on the number of questions a game can support, a game could have so many questions that it causes `SessionManager::cancelGameIfCreatorMissing, endGame` to revert due to out-of-gas errors.

* `endGame` iterates over all questions:
```solidity
 function endGame(uint256 _gameId) external onlyState(_gameId, SessionState.Ongoing) {
        require(block.timestamp >= games[_gameId].endTime, GameIsNotEnded(games[_gameId].endTime, block.timestamp));
        uint256[] storage questions = gameQuestions[_gameId];
        for (uint256 i = 0; i < questions.length; i++) {
            require(_isRevealed(questions[i]), QuestionNotRevealed(_gameId, questions[i]));
        } <-----------
        games[_gameId].state = SessionState.Ended;
        emit GameEnded(_gameId);
    }
```

* so does `cancelGameIfCreatorMissing`:
```solidity
  function cancelGameIfCreatorMissing(uint256 _gameId) external {
        require(
            games[_gameId].state != SessionState.Cancelled,
            InvalidGameState(SessionState.Cancelled, games[_gameId].state)
        );
        require(
            games[_gameId].state != SessionState.Concluded,
            InvalidGameState(SessionState.Concluded, games[_gameId].state)
        );
        require(block.timestamp >= games[_gameId].endTime, GameIsNotEnded(games[_gameId].endTime, block.timestamp));
        uint256[] storage questions = gameQuestions[_gameId];
        for (uint256 i = 0; i < questions.length; i++) { <-------

            if (!_isRevealed(questions[i])) {
                games[_gameId].state = SessionState.Cancelled;
                emit GameCancelled(_gameId);
                return;
            }
        }
        revert GameWaitingForConclusion(_gameId);
    }
```

**Impact:** `SessionManager::cancelGameIfCreatorMissing, endGame` could revert if there are too many questions in a game.

* If `endGame` cannot complete, users and the creator lose their funds and fees
* If `cancelGameIfCreatorMissing` reverts, users lose their funds if the creator is missing

**Recommended Mitigation:** Limit the number of questions in a game.

**Majority Games:**
Fixed in commit [cb88233](https://github.com/Engage-Protocol/engage-protocol/commit/cb8823378ef74d688ff15eefb7b6ac0d2b0e5bc2).

**Cyfrin:** Verified.

## [M-6] Excessive amount `maximum Contestants` could make games to revert in `Default Session::record Results` due to out of gas
- Severity: `Medium`
- Source report: `protocol.md`

### Detailed Content (from source)
**Description:** `SessionManager::maximumContestants` is initially set to 1 million so potentially a large number of contestants can join each game:
```solidity
/**
 * @notice Maximum number of contestants allowed in a game
 */
 uint256 public maximumContestants = 1_000_000;
```

`DefaultSession::recordResults` iterates over all the winners to record the result for each question in the respective strategies:
```solidity
 function recordResults(uint256 sessionId, bytes32 assertionId) public {
     ...
        for (uint256 i = 0; i < assertion.winners.length; ++i) { <------
            address winner = assertion.winners[i]; //@audit how many winners could be?
            for (uint256 j = 0; j < questionIds.length; ++j) {
                (, address promptStrategy) = SessionManager(sessionManager).questionCommitment(questionIds[j]);
                IPromptStrategy(promptStrategy).recordResult(
                    questionIds[j], winner, assertion.totalXPs[i], assertion.totalTimes[i]
                );
            }
         ...
    }
```

If there are many winners this loop iteration could revert due to out-of-gas.

**Impact:** Games may not finish due to out of gas.

**Proof of Concept:** Taking in consideration that the block gas limit in base is around 30M and if we call ` forge test --mt test_RecordResults_Success --gas-report `  we could see that the `assertionResolvedCallback` is costing an avg 280587 for just two winners if we divide 30M /  280587  we get approximately 100 winner maximum.

**Assumptions:**
Block gas limit: 30,000,000 gas
Function overhead: ~50,000 gas

**Average questions per game: 5-10 questions
Conservative Estimate (10 questions per game):**
Gas per winner: 25,000 + (7,600 × 10) = 101,000 gas
Available gas: 30,000,000 - 50,000 = 29,950,000 gas
Maximum winners: 29,950,000 ÷ 101,000 ≈ 296 winners

**Optimistic Estimate (5 questions per game):**
Gas per winner: 25,000 + (7,600 × 5) = 63,000 gas
Maximum winners: 29,950,000 ÷ 63,000 ≈ 475 winners

**Realistic Maximum: ~300-400 winners**

**Recommended Mitigation:** Consider set a realistic `maximumContestants` to approx. 1000 participants. Alternatively another approach is just keep the winners in the array and create another function where user can `recordResult` by chunks.

**Majority Games:**
Fixed in commit [a2e353e](https://github.com/Engage-Protocol/engage-protocol/commit/a2e353e664f7707d49a3ca9ca2bea792d731711c).

**Cyfrin:** Verified.

## [M-7] use fixed length array for `re SDLToken Ids`
- Severity: `Medium`
- Source report: `vesting.md`

### Detailed Content (from source)
**Description:** The contract currently declares

```solidity
uint256[] private reSDLTokenIds;
```

and in the constructor uses a `for`-loop with `.push(0)` to initialize it to length `MAX_LOCK_TIME + 1`. This incurs:

* A dynamic‐array length slot in storage
* A pointer slot for the array data
* Multiple storage writes (one per `.push`)

Since the array’s length is always exactly `MAX_LOCK_TIME + 1` (5), a static array:

```solidity
uint256[MAX_LOCK_TIME + 1] private reSDLTokenIds;
```

removes the dynamic‐array overhead and eliminates the initialization loop.

Consider replacing the dynamic array with a fixed-length array and remove the constructor loop:

```diff
-   // list of reSDL token ids for each lock time
-   uint256[] private reSDLTokenIds;

+   // list of reSDL token ids for each lock time (0–4 years)
+   uint256[MAX_LOCK_TIME + 1] private reSDLTokenIds;

    constructor(…) {
        ...
-       for (uint256 i = 0; i <= MAX_LOCK_TIME; ++i) {
-           reSDLTokenIds.push(0);
-       }
     }
```

This change collapses two storage slots (length + data pointer) into one and removes the costly initialization loop, reducing both deployment and per-read gas costs.

**Stake.Link:** Fixed in commit [`128c335`](https://github.com/stakedotlink/contracts/commit/128c33560d8f43057c5d10d822b4904d0762d0fd)

**Cyfrin:** Verified. `reSDLTokenIds` now static.

\clearpage

## [M-8] `owner Set Voting Power Excluded Status()` applies only Owner modifier twice
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** In WLF V2 contract, the function `ownerSetVotingPowerExcludedStatus()` applies `onlyOwner` modifier twice :
- First in the external `ownerSetVotingPowerExcludedStatus()` function
- Again in the internal  `_ownerSetVotingPowerExcludedStatus()` function in the same call flow.

The second onlyOwner modifier on `_ownerSetVotingPowerExcludedStatus()` is unnecessary.


**Recommended Mitigation:** Remove onlyOwner modifier from `_ownerSetVotingPowerExcludedStatus()` function.

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L387)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-34] Cache storage to prevent identical storage reads
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive, cache storage to prevent identical storage reads:

* `SecuritizeAmmNavProvider::_pricingFromCurveBuy, _pricingFromCurveSell` - cache `priceScaleFactor`
* `SecuritizeAmmNavProvider::_checkAndResetBaseline` - cache `lastAnchorPriceWad, lastMarketStatus` prior to first `if` statement
* `AllowanceLiquidityProvider::_availableLiquidity` - cache `liquidityToken, liquidityProviderWallet`
* `BaseOffRamp::_redeem` - cache `asset`
* `BaseOnRamp::_executeLiquidityTransfer` - cache `liquidityToken, feeManager, bridgeChainId, USDCBridge`

**Securitize:** Fixed in commits [e631361](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/e631361371ccaabceabd8ba1a200f4fd1200e54f), [ea883b9](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/ea883b99af2eb802ffe49c7338379b1e31cd76de), [d32d6a0](https://bitbucket.org/securitize_dev/bc-nav-provider-sc/commits/d32d6a0d6cf9a4215360deb11711740450d1db48).

**Cyfrin:** Verified.

## [M-24] Cache storage to prevent identical storage reads
- Severity: `Medium`
- Source report: `escrow.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive; cache storage to prevent identical storage reads:
* `SablierBob::exitWithinGracePeriod, redeem` - `vault.shareToken`, potentially also `vault.adapter` if the most likely case is non-zero
* `SablierBob::redeem` - `comptroller` in the branch where no vault adapter exists if `minFeeWei` is likely to be > 0
* `SablierBob::unstakeTokensViaAdapter` - `vault.adapter`
* `SablierBob::onShareTransfer` - `_vaults[vaultId].adapter` if the most likely case is non-zero

**Sablier:** Fixed in commit [7d9ac86](https://github.com/sablier-labs/lockup/commit/7d9ac86a6edc85383b1fc9b58fdfbaf78a8f1cb1).

**Cyfrin:** Verified.

## [M-6] Cache storage to prevent identical storage reads
- Severity: `Medium`
- Source report: `harbor.md`

### Detailed Content (from source)
**Description:** Cache storage to prevent identical storage reads:

* `Agreement.sol`
```solidity
// cache `accts.length` in `getDetails`
320:            _details.chains[i].accounts = new Account[](accts.length);
321:            for (uint256 j = 0; j < accts.length; ++j) {

// cache `chainAccounts.length` in `_findAccountIndex`
398:        for (uint256 i = 0; i < chainAccounts.length; i++) {
```

**SafeHarbor:**
Fixed in commit [eb51eb0](https://github.com/PatrickAlphaC/safe-harbor/commit/eb51eb04669c5c48ca6fa692b2215593f7eae11b).

**Cyfrin:** Verified.

## [M-19] Cache storage slots to prevent identical storage reads
- Severity: `Medium`
- Source report: `wannabetv2.md`

### Detailed Content (from source)
**Description:** Cache storage slots to prevent identical storage reads if the values don't change during execution.

For example, `Bet::accept,cancel,resolve` should cache `_aavePool` if it is likely to be non-zero since this saves 1 storage read in `accept` and 2 storage reads in `resolve,cancel`.

**WannaBet:** Fixed in commit [b8b4863](https://github.com/gskril/wannabet-v2/commit/b8b4863960cc3eeee3ccf017e4ac3d26f65959fe).

**Cyfrin:** Verified.

## [M-38] Cache storage to prevent identical storage reads
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Reading from storage is expensive; cache storage to prevent identical storage reads:
* `ComplianceChecker.sol`:
```solidity
// cache `for` loop storage lengths in `isCompliant`
59:            optionIndex < _complianceOptions.length;
66:                sbtIndex < _complianceOptions[optionIndex].requiredSBTs.length;
```

* `CompliantDepositRegistry.sol`:
```solidity
// cache `investorDepositMap[investor]` in `getDepositAddress`
60:        require(investorDepositMap[investor] > 0, UnregisteredInvestor());
64:        return depositAddresses[investorDepositMap[investor]];

// cache `nextDepositAddressIndex` in `registerDepositAddress`
93:                nextDepositAddressIndex < depositAddresses.length &&
102:        investorDepositMap[msg.sender] = nextDepositAddressIndex;

// cache `getDepositAddress(msg.sender)` in `registerDepositAddress`
// ideally do this by using a named return variable, assigning straight to it,
// using the named return variable to emit the event then deleting the obsolete
// `return` statement
104:        emit DepositAddressSet(msg.sender, getDepositAddress(msg.sender));
106:        return getDepositAddress(msg.sender);

// cache `depositAddresses.length` in `getDepositAddresses`
128:        if (startIndex + count > depositAddresses.length) {
129:            returnLength = depositAddresses.length - startIndex;
134:            i < count && startIndex + i < depositAddresses.length;

// cache `depositAddresses.length` in `addDepositAddresses`
// just invert the order of these two statements then use `startIndex`
// to set `finalizedAddressesLength`
154:        finalizedAddressesLength = depositAddresses.length;
156:        uint startIndex = depositAddresses.length;

// cache `block.timestamp + batchChallengePeriod` in `addDepositAddresses`
// and use it to set `latestBatchUnlockTime` and also to emit the event
161:        latestBatchUnlockTime = block.timestamp + batchChallengePeriod;
165:            latestBatchUnlockTime,

// cache `finalizedAddressesLength` and use `block.timestamp` instead of
// `latestBatchUnlockTime` when emitting event in `challengeLatestBatch`
199:        uint batchLength = depositAddresses.length - finalizedAddressesLength;
208:            finalizedAddressesLength,
209:            latestBatchUnlockTime,
```

* `Blacklistable.sol`:
```solidity
// use input `_newBlacklister` when emitting event in `updateBlackLister`
74:        emit BlacklisterChanged(blacklister);
```

* `Minter.sol`:
```solidity
// cache `custodian` in `transferToCustody`
135:        baseAsset.safeTransfer(custodian, amount);
136:        emit FundsTransferredToCustody(amount, custodian);
```

* `StakingVault.sol`:
```solidity
// cache `cooldownDuration` in `redeem, withdraw`
137:        if (cooldownDuration == 0) {
142:            cooldownDuration;
159:        if (cooldownDuration == 0) {
164:            cooldownDuration;

// use input `duration` when emitting event in `setCooldownDuration`
220:        cooldownDuration = duration;
221:        emit CooldownDurationUpdated(previousDuration, cooldownDuration);

// cache `lastDistributionTimestamp` in `getUnvestedAmount` if first `return`
// statement is unlikely to be frequently triggered
271:        if (lastDistributionTimestamp > block.timestamp) {
275:            lastDistributionTimestamp;
```

**Syntetika:**
Fixed in commits [bc24502](https://github.com/SyntetikaLabs/monorepo/commit/bc245024d7a3d4773661a2eb82284653bfa7f46b), [8560039](https://github.com/SyntetikaLabs/monorepo/commit/8560039b80334a3ad234f7f90ff0a55e50d13edd), [bfad835](https://github.com/SyntetikaLabs/monorepo/commit/bfad8350a4b6b843c47bea023237271c198bfa84).

**Cyfrin:** Verified though ideally `StakingVault::withdraw` would also [cache](https://github.com/SyntetikaLabs/monorepo/blob/audit/issuance/src/vault/StakingVault.sol#L190-L195) `cooldownDuration` similar to the fix made inside `redeem`.
