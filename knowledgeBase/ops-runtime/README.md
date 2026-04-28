# ops-runtime - Issues

- Count: 4

## F-2026-14863 - Missing Gas Tank Auto-Fill for Recipients in BulkTransfers
- 嚴重度：Medium
- Report source：Dexalot.pdf

### 問題內容（完整）
The PortfolioSub contract implements an auto-fill `mechanism(autoFillPrivate)` designed to ensure users always have sufficient gastokens (`ALOT`) in their Gas Tank to perform transactions on the Dexalot L1.According to the contract's documentation: Users will always have some `ALOT` deposited to their gasTank ifthey start from the mainnet with any token. Hence it is notpossible to have a portfolioSub holding without gas in theGasTank. In other words: if assets[`_trader`][`_symbol`].available > 0then `_trader`.balance > 0 However, this invariant is violated in bulkTransferTokens function, wheretoken recipients do not receive the automatic gas refill that occurs insimilar operations. The single-token transferToken function correctly calls autoFillPrivate forthe recipient: function transferToken( address `_to`, bytes32 `_symbol`, uint256 `_quantity` ) external override whenNotPaused nonReentrant { require(tokenList.contains(`_symbol`), "P-`ETNS`-01"); require(`_to` != `msg.sender`, "P-`DOTS`-01"); require(tokenDetailsMap[`_symbol`].auctionMode == ITradePairs.AuctionMode.OF F, "P-`AUCT`-01"); transferToken(`msg.sender`, `_to`, `_symbol`, `_quantity`, 0, Tx.`IXFERSENT`, false, `address(0)`); autoFillPrivate(`_to`, `_symbol`, Tx.`AUTOFILL`); } However, the bulk transfer function omits this call: function bulkTransferTokens( address `_from`, address `_to`, bytes32[] calldata `_symbols`, uint256[] calldata `_quantities` ) external whenNotPaused nonReentrant { require(`_from` == `msg.sender` || hasRole(`TRUSTED_TRANSFER_ROLE`, `msg.sender`), "P-`OOWN`-03"); 24 require(`_to` != `msg.sender`, "P-`DOTS`-01"); require(`_symbols`.length == `_quantities`.length, "P-`ARLM`-01"); for (uint256 i = 0; i < `_symbols`.length; ) { bytes32 symbol = `_symbols`[i]; uint256 quantity = `_quantities`[i]; `require(tokenList.contains(symbol)`, "P-`ETNS`-01"); transferToken(`_from`, `_to`, symbol, quantity, 0, Tx.`IXFERSENT`, false, ad `dress(0)`); unchecked { i++; } } } This may lead to the following consequences: Recipients cannot perform any transactions on Dexalot L1Users may believe their funds are lost or inaccessibleInvariant violation: Breaks the documented guarantee: assets[trader] [symbol].available > 0 → trader.balance > 0 Inconsistent behavior: Single transfers work correctly while bulktransfers leave users stranded Assets: `contracts/PortfolioSub.sol`[https://github.com/Dexalot/contracts/commits/omnivaults/] Status: Fixed

### 修補方式（建議）
Add autoFillPrivate to bulkTransferTokens: autoFillPrivate(`_to`, `_symbols`[`_symbols`.length - 1], Tx.`AUTOFILL`); 25 Resolution: Fixed in bf20793: The function now calls autoFillPrivate(`_to`, `_symbols`[0], Tx.`AUTOFILL`) aftercompleting all transfers, ensuring the recipient's Gas Tank is refilled ifneeded. autoFillPrivate(`_to`, `_symbols`[0], Tx.`AUTOFILL`); 26

### 修補方式（實際）
Fixed in bf20793: The function now calls autoFillPrivate(`_to`, `_symbols`[0], Tx.`AUTOFILL`) aftercompleting all transfers, ensuring the recipient's Gas Tank is refilled ifneeded. autoFillPrivate(`_to`, `_symbols`[0], Tx.`AUTOFILL`); 26

## 補充 Issues

- Count: 3

## L-10 - No way to cancel or reduce cooldown re
- 嚴重度：Low
- Report source：Tori Finance.pdf

### 問題內容（完整）
quests [RESOLVED] Source: https://github.com/sherlock-audit/2026-01-tori-finance-jan-15th/issues/36 Summary Once a user initiates a cooldown via cooldownAssets() or cooldownShares(), there is no way to cancel the request, reduce the amount, or re-stake the assets. Users are locked into waiting for the full cooldown period. Vulnerability Detail The cooldown functions only allow increasing the underlyingAmount: // StakedTrUSD.sol:225-237 function cooldownAssets(uint256 assets) external ensureCooldownOn returns (uint256) {,→ if (assets > maxWithdraw(msg.sender)) revert ExcessiveWithdrawAmount(); uint256 shares = previewWithdraw(assets); StakedTrUSDStorage storage $ = _getStakedTrUSDStorage(); $.cooldowns[msg.sender].cooldownEnd = uint104(block.timestamp) + $.cooldownDuration;,→ $.cooldowns[msg.sender].underlyingAmount += assets; // Only increases! _withdraw(msg.sender, address($.silo), msg.sender, assets, shares); // Assets sent to silo,→ return shares; } // StakedTrUSD.sol:239-251 function cooldownShares(uint256 shares) external ensureCooldownOn returns (uint256) {,→ if (shares > maxRedeem(msg.sender)) revert ExcessiveRedeemAmount(); uint256 assets = previewRedeem(shares); StakedTrUSDStorage storage $ = _getStakedTrUSDStorage(); $.cooldowns[msg.sender].cooldownEnd = uint104(block.timestamp) + $.cooldownDuration;,→ $.cooldowns[msg.sender].underlyingAmount += assets; // Only increases! _withdraw(msg.sender, address($.silo), msg.sender, assets, shares); // Assets sent to silo,→ 43 return assets; } The TrUsdSilo contract only has a withdraw function callable by the staking vault: // TrUsdSilo.sol:29-31 function withdraw(address to, uint256 amount) external onlyStakingVault { trUSD.safeTransfer(to, amount); } // No user-facing cancel function Step Action Result 1 User calls cooldownAssets(10000) 10,000 TrUSD sent to silo, shares burned 2 Market conditions change, user wants to re-stake No option available 3 User must wait 7 days (default cooldown) Opportunity cost, no yield during cooldown 4 After cooldown, user calls unstake() Finally receives TrUSD 5 User deposits again Gets new shares at potentially worse rate Impact Users cannot change their mind after initiating cooldown. Code Snippet https://github.com/sherlock-audit/2026-01-tori-finance-jan-15th/blob/main/Tori-Finan ce__contracts/contracts/core/StakedTrUSD.sol#L225 Tool Used Manual Review Recommendation Consider adding a cancelCooldown() function. 44

### 修補方式（實際）
Status: Fixed/Resolved in report.

## L-12 - Compilation Failure Due to Reentrancy
- 嚴重度：Low
- Report source：Tori Finance.pdf

### 問題內容（完整）
GuardUpgradeable Removal in OpenZeppelin v5.5 [RESOLVED] Source: https://github.com/sherlock-audit/2026-01-tori-finance-jan-15th/issues/38 Summary The project utilizes the OpenZeppelin Contracts Upgradeable library. Due to OpenZeppelin removing ReentrancyGuardUpgradeable (or modifying its path/implementation) in version v5.5.0, and Foundry potentially pulling this latest incompatible version, StakedTrUSD.sol fails to compile. Vulnerability Detail In StakedTrUSD.sol, the contract imports ReentrancyGuardUpgradeable: import "@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardUpgradeable.sol"; According to the OpenZeppelin v5.5.0 release notes, changes in the library structure have made the above import path invalid or the file unavailable. Even if package.json defines a version range, Foundry's dependency management (via git submodules or remappings) may fetch the latest v5.5.0 version if not strictly locked. This results in build failures during compilation due to missing dependencies or incompatibility. Impact The project cannot compile, making it impossible to run tests or deploy the contracts. Code Snippet import "@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardUpgradeable.sol"; Tool Used Manual Review 47 Recommendation It is recommended to take one of the following actions: 1. Lock Dependency Version: Strictly lock @openzeppelin/contracts-upgradeable to a compatible version (e.g., v5.4.0) in both package.json and Foundry configuration to ensure it does not auto-upgrade to v5.5.0. 2. Adapt to New Version: If v5.5.0 is required, update the code according to the OpenZeppelin migration guide to use the new import paths or storage patterns. 48

### 修補方式（實際）
Status: Fixed/Resolved in report.

## L-13 - rescueOrphanFunds fails to reset vesting
- 嚴重度：Low
- Report source：Tori Finance.pdf

### 問題內容（完整）
Amount causing temporary DoS [RESOLVED] Source: https://github.com/sherlock-audit/2026-01-tori-finance-jan-15th/issues/41 Summary The rescueOrphanFunds function in StakedTrUSD extracts idle funds but fails to reset vesti ngAmount. This causes the totalAssets() function to revert due to integer underflow. Consequently, users cannot deposit funds during the remaining vesting period. Vulnerability Detail The StakedTrUSD contract uses rescueOrphanFunds to allow the admin to withdraw all underlying assets when totalSupply() == 0 . However, this function only transfers the asset balance but fails to reset the vestingAmount variable (which tracks unvested rewards) to zero. The logic for calculating total assets in StakedTrUSD is as follows: function totalAssets() public view override returns (uint256) { return IERC20(asset()).balanceOf(address(this)) - getUnvestedAmount(); } If rescueOrphanFunds is called while there are still unvested rewards ( getUnvestedAmount() > 0 ): 1. IERC20(asset()).balanceOf(address(this)) becomes 0. 2. getUnvestedAmount() remains a positive number. 3. totalAssets() executes 0 - positive_number , causing an EVM arithmetic underflow and revert. Since the ERC4626 deposit and mint flows rely on totalAssets() to calculate exchange rates, this causes a Denial of Service (DoS) where the contract cannot process any new deposits until the vesting period ends (up to 8 hours). Impact After the admin executes the rescue, the contract becomes non-functional for the remainder of the vesting period ( VESTING_PERIOD, default 8 hours). During this time, no users can deposit funds. 49 Code Snippet function rescueOrphanFunds(address to) external onlyRole(DEFAULT_ADMIN_ROLE) { if (totalSupply() != 0) revert OperationNotAllowed(); if (to == address(0)) revert InvalidZeroAddress(); uint256 balance = IERC20(asset()).balanceOf(address(this)); if (balance == 0) revert NoOrphanFunds(); IERC20(asset()).safeTransfer(to, balance); // @audit-issue Asset removed but vestingAmount not reset,→ emit OrphanFundsRescued(to, balance); } Tool Used Manual Review Recommendation In the rescueOrphanFunds function, both vestingAmount and lastDistributionTimestamp should be reset to ensure consistency between the state and the asset balance. 50

### 修補方式（實際）
Status: Fixed/Resolved in report.

## Cyfrin Fixed Issues (Merged)
- Count: `3`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] Use named mappings to explicitly denote the purpose of keys and values
- Severity: `Medium`
- Source report: `predeposit.md`

### Detailed Content (from source)
**Description:** Use named mappings to explicitly denote the purpose of keys and values:
```solidity
predeposit/MetaVault.sol
23:    // Track the assets in the mapping for easier access
24:    mapping(address => TAsset) public assetsMap;

predeposit/pUSDeDepositor.sol
35:    mapping (address => TAutoSwap) autoSwaps;

test/MockStakedUSDe.sol
20:  mapping(address => UserCooldown) public cooldowns;
```

**Strata:** Fixed in commit [ab231d9](https://github.com/Strata-Money/contracts/commit/ab231d99e4ba6c7c82c4928515775a39dc008808).

**Cyfrin:** Verified.

## [M-2] Consider using `SafeCast` when downcasting amounts
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Consider using [SafeCast](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/SafeCast.sol) when downcasting amounts:
* `StakingVault.sol`:
```solidity
144:        cooldowns[msg.sender].underlyingAmount += uint152(assetsRedeemed);
165:        cooldowns[msg.sender].underlyingAmount += uint152(assets);
```

**Syntetika:**
Fixed in commit [8d7987c](https://github.com/SyntetikaLabs/monorepo/commit/8d7987cfe72ab33c51b486fd3ac5fe2670292a30).

**Cyfrin:** Verified.

## [M-3] Guardian can override owner's emergency pause
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The contract implements symmetric `pause/unpause` powers between the owner and guardians, allowing guardians to unpause the contract even when the owner intentionally paused it for security or operational reasons. This creates an authority hierarchy conflict where guardians can override the owner's emergency decisions, potentially undermining security responses and operational control.

```solidity
function guardianUnpause() external onlyGuardian whenPaused {
    // @audit - do you think only the owner should be able to unpause?
    _unpause();
}
```
Note: The comment in the code indicates the dev team flagged this design choice from a security viewpoint.

During periods of emergency or security breach, owner should have ultimate control over contract state. While pausing a contract is low-risk, unpausing it is higher-risk operation that needs to have a hierarchical access. Common security practice is:

```text
Multiple parties can pause (defensive action, low risk)
Only highest authority can unpause (requires careful consideration)
```

**Impact:** Guardian override can undermine owner's authority on contract pause/unpause status.


**Recommended Mitigation:** Consider removing `unpause` option for guardians.

**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L214)

**Cyfrin:** Verified.

\clearpage

<!-- /Cyfrin Fixed Issues (Merged) -->

