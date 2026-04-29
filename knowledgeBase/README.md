# KnowledgeBase — Issue Index

Automatically generated index of **682** fixed security issues (Critical / High / Medium).
Sources: `HackenPDFTXT/`, `sherlockPDFTXT/`, `cyfrin/`

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## Table of Contents

- [access-control](#access-control) (55)
- [accounting](#accounting) (57)
- [dos-liveness](#dos-liveness) (437)
- [oracle-pricing](#oracle-pricing) (11)
- [token-transfer](#token-transfer) (40)
- [upgrade-config](#upgrade-config) (32)
- [withdrawal-redeem](#withdrawal-redeem) (50)

---

## access-control (55)
> Issues where privilege checks, admin roles, or signature/permit enforcement were bypassed or misconfigured.

### role-model (55)

#### `owner-admin` (20)

- 🟠 **In `DelegatorFactory` new entity can be created for a blacklisted implementation**  
  `cyfrin/core.md`
- 🟠 **Incorrect `owner` passed to `Manager::redeem` in YToken withdrawal flow**  
  `cyfrin/yieldfi.md`
- 🟠 **Users Can Renounce BLACKLISTED_ROLE and Bypass**  
  `HackenPDFTXT/Overlayer.txt`
- 🟡 **Admin Can Arbitrarily Decrease User’s Vesting Amount**  
  `HackenPDFTXT/A Two Tech Limited.txt`
- 🟡 **Blacklist Enforcement Bypassed When Recipient Is**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **Combination of Ownable and AccessControl can cause loss of admin functionality**  
  `cyfrin/trade.md`
- 🟡 **DEFAULT_ADMIN_ROLE` can be mistakenly granted to an account when granting permission to call `fallback` on any contract**  
  `cyfrin/tranches.md`
- 🟡 **Default Admin Can Assign Blacklisted Role Without Enforcing**  
  `HackenPDFTXT/Overlayer.txt`
- 🟡 **Guardian can override owner's emergency pause**  
  `cyfrin/wlf.md`
- 🟡 **Misleading owner field in OnMetaWithdraw event**  
  `cyfrin/cooldown.md`
- 🟡 **Owner Authorization Allows Arbitrary Burning of Soulbound**  
  `HackenPDFTXT/RYT-2.txt`
- 🟡 **Owner Rights Can Be Renounced While Contract Is Paused**  
  `HackenPDFTXT/Node Meta.txt`
- 🟡 **Owner can chain admin calls for same-block drains**  
  `cyfrin/sherpa.md`
- 🟡 **Owner can front-run depositors by call-**  
  `sherlockPDFTXT/Prodigy Finance.txt`
- 🟡 **Owner can not burn tokens from blacklisted addresses**  
  `cyfrin/syntetika.md`
- 🟡 **Owner can rescue the vault’s own share tokens**  
  `cyfrin/sherpa.md`
- 🟡 **StandardToken::transferWithPermit` can be DoS attacked by front-running to directly call `ERC20PermitMixin::permit**  
  `cyfrin/registry.md`
- 🟡 **TrustService::removeRole` doesn't delete already owned entities so address which lost role can still manage existing entities**  
  `cyfrin/rebasing.md`
- 🟡 **Untrusted Contract Remains Callable via Whitelisted**  
  `HackenPDFTXT/Dexalot.txt`
- 🟡 **WLFI owner can DoS legacy users through direct vester activation**  
  `cyfrin/wlf.md`

#### `blacklisted-users` (16)

- 🔴 **Lack of Access Control Enabling Unauthorized Credential**  
  `HackenPDFTXT/RYT-2.txt`
- 🟠 **Blacklisted Token Recipient Permanently Blocks FIFO Forced**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Admin void with arbitrary payout ratios allows buy then redeem profit**  
  `cyfrin/clob.md`
- 🟡 **Allow users to increment their nonce to void their signatures**  
  `cyfrin/cryptoart.md`
- 🟡 **Authorizable::_verify` should use EIP-712 typed structured data hashing**  
  `cyfrin/accountable.md`
- 🟡 **Blacklisted shares continue earning re-**  
  `sherlockPDFTXT/Tori Finance.txt`
- 🟡 **Blacklisted users can claim withdrawn assets after the cooldown period**  
  `cyfrin/syntetika.md`
- 🟡 **ComplianceServiceGlobalWhitelisted::getComplianceTransferableTokens` returns positive token amount for blacklisted users**  
  `cyfrin/registry.md`
- 🟡 **Excessive Admin Control Over Critical Staking Parameters**  
  `HackenPDFTXT/A Two Tech Limited.txt`
- 🟡 **Inability for users to permissionlessly stake and earn yield**  
  `cyfrin/syntetika.md`
- 🟡 **Prevent accidental ownership and admin renouncement**  
  `cyfrin/accountable.md`
- 🟡 **Remove unused `ExecutePreApprovedTransaction::nonce**  
  `cyfrin/registry.md`
- 🟡 **Shared Proof Replay-Prevention State Across Multiple**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Token name update breaks EIP-712 Domain Separator for permit functionality**  
  `cyfrin/registry.md`
- 🟡 **Transport-Layer Nonce Poisoning Causes Permanent Session Denial of Service**  
  `cyfrin/connect.md`
- 🟡 **ownerSetVotingPowerExcludedStatus()` applies onlyOwner modifier twice**  
  `cyfrin/wlf.md`

#### `validation-access` (11)

- 🔴 **Missing nonce validation in signature verification allows transaction replay attacks**  
  `cyfrin/bridge.md`
- 🟠 **Incomplete Blacklist Enforcement in transferFrom Allows**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **Commented-out blacklist check allows restricted transfers**  
  `cyfrin/yieldfi.md`
- 🟡 **Minting is Allowed for Frozen and Non-Whitelisted**  
  `HackenPDFTXT/Tokenizer.Estate.txt`
- 🟡 **Missing Access Control on verifyAndMarkComplete Enables**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Missing access control in `SDLVesting::stakeReleasableTokens**  
  `cyfrin/vesting.md`
- 🟡 **Missing check if `receiver` is whitelisted in `StakingVault::mint, deposit**  
  `cyfrin/syntetika.md`
- 🟡 **Missing zero address validation for authorized signer in `WorldLibertyFinancialV2.initialize()**  
  `cyfrin/wlf.md`
- 🟡 **Reusable Authentication Signatures Due to Missing Nonce**  
  `HackenPDFTXT/RYT-2.txt`
- 🟡 **Vault initialization allows deposit whitelist with no management capability**  
  `cyfrin/core.md`
- 🟡 **Weak signature validation in account activation**  
  `cyfrin/wlf.md`

#### `replay-protocol` (8)

- 🔴 **After the upgrade permissionless attacker can fully drain the L1 `TokenBridge` of `ERC20` tokens currently valued around $29M USD**  
  `cyfrin/upgrade.md`
- 🔴 **LivenessRecovery::setLivenessRecoveryOperator` will emit misleading event when role is not granted**  
  `cyfrin/upgrade.md`
- 🟠 **EntryPoint not included in user operation hash creates the possibility of Replay Attacks**  
  `cyfrin/DelegationFramework1.md`
- 🟡 **AdminRegistry::acceptAdmin` leaves other roles on the outgoing admin**  
  `cyfrin/clob.md`
- 🟡 **AdminRegistry` inherited `grantRole`/`revokeRole` bypass the two-step transfer guard**  
  `cyfrin/clob.md`
- 🟡 **All swaps will revert if the dynamic protocol fee is enabled since `hook-config.sol` does not encode the `afterSwapReturnDelta` permission**  
  `cyfrin/angstrom.md`
- 🟡 **Automation DoS via blacklisted or reverting fee recipients**  
  `cyfrin/octodefi.md`
- 🟡 **Protocol vulnerable to cross-chain signature replay**  
  `cyfrin/cryptoart.md`

## accounting (57)
> Issues involving rounding/precision errors, state desynchronisation, or incorrect share/NAV calculations.

### rounding-precision (27)

#### `decimals-rounding` (17)

- 🟡 **Arithmetic underflow in `withdrawERC20` when there is a negative rebasing of asset tokens**  
  `cyfrin/stbl.md`
- 🟡 **Consider implementing explicit rounding behaviour instead of default round down**  
  `cyfrin/sherpa.md`
- 🟡 **Consider reverting in `RebasingLibrary` functions if rounding down to zero occurs**  
  `cyfrin/rebasing.md`
- 🟡 **Duplicated `Math` import should be removed from `ERC721WrapperBase**  
  `cyfrin/vii.md`
- 🟡 **Enforce that `StakingVault::decimals` is greater or equal to the underlying asset decimals**  
  `cyfrin/syntetika.md`
- 🟡 **Flawed Rounding Logic in calculateBuyAmount Leads**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Inaccurate stake calculation due to decimal mismatch across multitoken asset classes**  
  `cyfrin/core.md`
- 🟡 **Incorrect Assumption of USDT Decimals Leads to Fee**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **LibHelpers.convertDecimalsTo` favours the user on a exact-out mint and burn for certain collateral decimals**  
  `cyfrin/parallel3.1.md`
- 🟡 **Multiplication could overflow in `RebasingLibrary` for tokens with greater than 18 decimals**  
  `cyfrin/rebasing.md`
- 🟡 **Potential underflow in slashing logic**  
  `cyfrin/core.md`
- 🟡 **Redundant overflow checks in safe arithmetic operations**  
  `cyfrin/core.md`
- 🟡 **Remove `decimals` from initial `RemoraToken` mint**  
  `cyfrin/pledge.md`
- 🟡 **Rounding in favor of the violator can subject liquidators to losses during partial liquidation**  
  `cyfrin/vii.md`
- 🟡 **Tranche::maxMint` for Junior Tranches is at risk of overflow when the `jrNav` falls below `1:1` rate to `JR_Shares**  
  `cyfrin/tranches.md`
- 🟡 **Value leakage due to pUSDe redemptions rounding against the protocol/yUSDe depositors**  
  `cyfrin/predeposit.md`
- 🟡 **YtokenL2::previewMint` and `YTokenL2::previewWithdraw` round in favor of user**  
  `cyfrin/yieldfi.md`

#### `precision-loss` (10)

- 🟠 **Precision Loss in Bonding Curve Calculations**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **AprPairFeed::getRoundData` can return data for a different round than the specified**  
  `cyfrin/tranches.md`
- 🟡 **Decimal mismatch in `BasisTradeTailor:transferHypeToCore` causes precision loss**  
  `cyfrin/update.md`
- 🟡 **Fee refund can lose precision**  
  `cyfrin/pledge.md`
- 🟡 **Incorrect Fee Math Allows Users to Exceed Allocation**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Insufficient fee validation in `STBL_Register::setupAsset` can cause underflow**  
  `cyfrin/stbl.md`
- 🟡 **Probability overflow can bypass `MaxProbabilityExceeded` check**  
  `cyfrin/spingame.md`
- 🟡 **Rounding errors in boosted probability calculation can cause guaranteed wins to fail**  
  `cyfrin/spingame.md`
- 🟡 **Rounding errors in ratio calculations can**  
  `sherlockPDFTXT/Tori Finance.txt`
- 🟡 **Unbounded weight scale factor causes precision loss in stake conversion, potentially leading to loss of operator funds**  
  `cyfrin/core.md`

### share-price-nav (7)

#### `maxwithdraw-tranche` (7)

- 🟡 **Deposits using lagging Vested NAV (cur-**  
  `sherlockPDFTXT/YieldFi.txt`
- 🟡 **Immediate withdrawals possible even when NAV is stale through `AccountableYield::accrueAndProcess**  
  `cyfrin/pr50.md`
- 🟡 **Invalid `maxWithdraw()` check in `withdraw()**  
  `cyfrin/accountable.md`
- 🟡 **Tranche::burnSharesAsFee` can be used to manipulate the exchange rate to cause withdrawals to revert for legitimate users**  
  `cyfrin/cooldown.md`
- 🟡 **Tranche::maxWithdraw` can understate the max withdrawal for the `SharesCooldown` contract**  
  `cyfrin/cooldown.md`
- 🟡 **When Senior's TargetGain is negative, the tx will revert because the senior loss is not accounted for on the Junior Tranche as profit, causing the navs summation to not match the current nav**  
  `cyfrin/tranches.md`
- 🟡 **pUSDeVault::maxWithdraw` doesn't account for withdrawal pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault**  
  `cyfrin/predeposit.md`

### state-sync (23)

#### `accounting-inconsistent` (18)

- 🔴 **An attacker can drain the entire protocol balance of sUSDe during the yield phase due to incorrect redemption accounting logic in `pUSDeVault::_withdraw**  
  `cyfrin/predeposit.md`
- 🟡 **Accounting::setMinimumJrtSrtRatio` sets `reserveBps` instead of `minimumJrtSrtRatio` making ratio configuration impossible**  
  `cyfrin/tranches.md`
- 🟡 **Direct amount assignment in `SherpaUSD::ownerMint`/`ownerBurn` can break accounting for totalStaked and accountingSupply**  
  `cyfrin/sherpa.md`
- 🟡 **Incomplete Transfer Classification Causes Inconsistent Limit**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **Inconsistent APR boundary validation between `AprPairFeed` and `Accounting**  
  `cyfrin/tranches.md`
- 🟡 **Inconsistent Risk Premium Validation in `Accounting` Allows Future Underflows or Zero APR**  
  `cyfrin/tranches.md`
- 🟡 **Inconsistent State Change in autoRefund() Affects TGE**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Inconsistent pause functionality allows certain state-changing operations when contract is paused**  
  `cyfrin/cryptoart.md`
- 🟡 **Inconsistent storage location namespace root in `YieldManagerStorageLayout**  
  `cyfrin/manager.md`
- 🟡 **Incorrect Comment and Missing Lower Bound for `minimumJrtSrtRatio` in `Accounting**  
  `cyfrin/tranches.md`
- 🟡 **Incorrect yield accounting when `_payNodeOperatorFees` reverts in `LidoStVaultYieldProvider::reportYield**  
  `cyfrin/manager.md`
- 🟡 **Misconfigured decimal scale can skew vault accounting**  
  `cyfrin/sherpa.md`
- 🟡 **Missing debt asset APPROVAL leafs in _**  
  `sherlockPDFTXT/Vesu Vaults.txt`
- 🟡 **Onchain governance integration breaks due to inconsistent implementation of voting power**  
  `cyfrin/wlf.md`
- 🟡 **Output Accounting Uses Absolute Balance**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **Reuse `aum_` in `_accrueFeeShares` to avoid recomputing debt**  
  `cyfrin/pr50.md`
- 🟡 **SherpaVault::_rollInternal` price calculation comment and math inconsistent**  
  `cyfrin/sherpa.md`
- 🟡 **Unused Import of `OwnableUpgradeable` in `Accounting.sol**  
  `cyfrin/tranches.md`

#### `accounting-transfer` (5)

- 🔴 **AccountableAsyncRedeemVault::fulfillCancelRedeemRequest` can de-sync request data causing permanent DOS for queue processing**  
  `cyfrin/accountable.md`
- 🟡 **DoS on stake accounting functions by bloating `operatorNodesArray` with irremovable nodes**  
  `cyfrin/core.md`
- 🟡 **Fee-On-Transfer And Rebasing Tokens Break Accounting**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Fee-on-Transfer / Rebasing Tokens Break Accounting**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Inconsistent stake calculation due to mutable `vaultManager` reference in `AvalancheL1Middleware**  
  `cyfrin/core.md`

## dos-liveness (437)
> Issues that block normal protocol operation — including griefing of funds/rewards/fees and irreversible revert-locks.

### griefing (405)

#### `return-script` (39)

- 🔴 **All CCIP messages reverts when decoded**  
  `cyfrin/yieldfi.md`
- 🟠 **During the yield phase, when using supported vaults, users can't withdraw vault assets they are entitled to**  
  `cyfrin/predeposit.md`
- 🟠 **finalizeForceWithdrawal Silently Burns User Balance When**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Adapter removal script lacks Safe-mode calldata output**  
  `cyfrin/update.md`
- 🟡 **AfterSwap Return Delta Applied To Unspecified Currency**  
  `HackenPDFTXT/Launchly.txt`
- 🟡 **BasisTradeTailor::transferPerp` comment mismatch**  
  `cyfrin/update.md`
- 🟡 **Cap Semantics Mismatch: _cap Enforces**  
  `sherlockPDFTXT/Fluent (2).txt`
- 🟡 **Chainlink router configured twice**  
  `cyfrin/yieldfi.md`
- 🟡 **Check return value when calling `Allowlist::exchangeAllowed` and `RemoraToken::_exchangeAllowed` to prevent unauthorized transfers**  
  `cyfrin/pledge.md`
- 🟡 **Collision between rebalance order consideration tokens and am-AMM fees for Bunni pools using Bunni tokens**  
  `cyfrin/bunni.md`
- 🟡 **CompensationPriceFinder::getZeroForOne` may compute smaller effective prices than expected**  
  `cyfrin/angstrom.md`
- 🟡 **Consider using `SafeCast` when downcasting amounts**  
  `cyfrin/syntetika.md`
- 🟡 **Consider using exponential notation in tests**  
  `cyfrin/trade.md`
- 🟡 **Consider using named mapping parameters**  
  `cyfrin/clob.md`
- 🟡 **Deploy script `UpdateParallelizer.ts` does not handle facet removal case**  
  `cyfrin/parallel3.1.md`
- 🟡 **Deployment script requires unencrypted private key**  
  `cyfrin/accountable.md`
- 🟡 **DocumentManager::hasSignedDocs` incorrectly returns `true` when there are no documents to sign**  
  `cyfrin/pledge.md`
- 🟡 **IBridgeableTokenP::swapLzTokenToPrincipalToken` interface declares a `uint256` return value but `BridgeableTokenP::swapLzTokenToPrincipalToken` returns nothing, breaking external integrations**  
  `cyfrin/parallel3.1.md`
- 🟡 **Only update `deployedAssets` when `remaining > 0` in `AccountableYield::repay**  
  `cyfrin/pr50.md`
- 🟡 **Order not eligible at `eligibleAt**  
  `cyfrin/yieldfi.md`
- 🟡 **PledgeManager::refundTokens` doesn't decrement `tokensSold` when pledge hasn't concluded, preventing pledge from reaching its funding goal**  
  `cyfrin/pledge.md`
- 🟡 **Prefer explicit `uint` sizes**  
  `cyfrin/syntetika.md`
- 🟡 **Prefer explicit unsigned integer sizes**  
  `cyfrin/rebasing.md`
- 🟡 **Prefer named return parameters, especially for `memory` returns**  
  `cyfrin/cryptoart.md`
- 🟡 **Refactor duplicated checks into modifiers**  
  `cyfrin/manager.md`
- 🟡 **Remove obsolete `onlyTokenOwner` from `_transferToNftReceiver**  
  `cyfrin/cryptoart.md`
- 🟡 **Remove or resolve TODO**  
  `cyfrin/escrow.md`
- 🟡 **Remove return value from `DSToken::updateInvestorBalance` as it is never checked**  
  `cyfrin/rebasing.md`
- 🟡 **Return fast in `ComplianceServiceRegulated::checkHoldUp` if platform wallet**  
  `cyfrin/rebasing.md`
- 🟡 **SDLVesting::withdrawRESDLPositions` enhancements**  
  `cyfrin/vesting.md`
- 🟡 **Scaling `winningThreshold` incorrectly reduces randomness distribution**  
  `cyfrin/spingame.md`
- 🟡 **Signatures have no expiration deadline**  
  `cyfrin/cryptoart.md`
- 🟡 **Unauthorized Delegation via `migrateAndDelegate()`**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **Uncoordinated Escape Hatch Mechanisms Cause**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Unresolved developer comments**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use `type(uint256).max` when withdrawing from Aave**  
  `cyfrin/wannabetv2.md`
- 🟡 **Withdrawals priced at execution problematic during large price swings**  
  `cyfrin/trade.md`
- 🟡 **finalizeWithFee lacks race conditioning protection**  
  `cyfrin/cooldown.md`
- 🟡 **transferOwnership Does Not Update Privileged Exemptions**  
  `HackenPDFTXT/Knoxnet.txt`

#### `named-explicitly` (26)

- 🟠 **All updated pools will have the wrong pr**  
  `sherlockPDFTXT/EasyA Kickstart.txt`
- 🟡 **Asymmetry enforcement between `TokenIssuer::registerInvestor`, `WalletRegistrar::registerWallet` and `SecuritizeSwap::_registerNewInvestor**  
  `cyfrin/rebasing.md`
- 🟡 **Calculation of available liquidity in `CollateralLiquidityProvider::availableLiquidity` assumes 1:1 ratio between collateral asset and liquidity tokens**  
  `cyfrin/bridge.md`
- 🟡 **Changing investor country to the same country inflates investor count erroneously triggering max investor errors**  
  `cyfrin/rebasing.md`
- 🟡 **Cooldown contracts underreport the real balance of users because they only consider the balance of requests whose cooldown period is over**  
  `cyfrin/tranches.md`
- 🟡 **Deployment script requires unencrypted private keys**  
  `cyfrin/trade.md`
- 🟡 **Dynamic LP fees will remain zero by default unless explicitly updated**  
  `cyfrin/angstrom.md`
- 🟡 **External LST liability settlements are lost to the protocol when ossification and yield provider removal precedes yield reporting**  
  `cyfrin/manager.md`
- 🟡 **Mismatch Between Tier Assignment and Enumeration**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **MyriadCTFExchange.filledAmounts` mapping slot and `hashOrder` computed multiple times per order**  
  `cyfrin/clob.md`
- 🟡 **Refactor away duplicated code between `ComplianceService::newPreTransferCheck` and `preTransferCheck**  
  `cyfrin/rebasing.md`
- 🟡 **Resolve inconsistency between `DSToken::checkWalletsForList` and `RegistryService::removeWallet**  
  `cyfrin/rebasing.md`
- 🟡 **TransactionRelayer` and `SecuritizeSwap` should use `CommonUtils::encodeString**  
  `cyfrin/rebasing.md`
- 🟡 **Use `uint128` to pack `DepositManager::protocolFee`, `maxCreatorFee` into the same storage slot**  
  `cyfrin/protocol.md`
- 🟡 **Use named constants to indicate purpose of magic numbers**  
  `cyfrin/cryptoart.md`
- 🟡 **Use named imports**  
  `cyfrin/rebasing.md`
- 🟡 **Use named imports**  
  `cyfrin/syntetika.md`
- 🟡 **Use named mapping parameters to explicitly note the purpose of keys and values**  
  `cyfrin/rebasing.md`
- 🟡 **Use named mapping parameters to explicitly note the purpose of keys and values**  
  `cyfrin/syntetika.md`
- 🟡 **Use named mapping parameters to explicitly note the purpose of keys and values**  
  `cyfrin/trade.md`
- 🟡 **Use named mappings to explicitly denote the purpose of keys and values**  
  `cyfrin/predeposit.md`
- 🟡 **Use named mappings to explicitly denote the purpose of keys and values**  
  `cyfrin/protocol.md`
- 🟡 **Use named mappings to explicitly indicate the purpose of keys and values**  
  `cyfrin/wannabetv2.md`
- 🟡 **YieldManager::fundYieldProvider` and `LidoStVaultYieldProvider::fundYieldProvider` don't enforce `isStakingPaused` and `isOssificationInitiated` allowing unsafe staking**  
  `cyfrin/manager.md`
- 🟡 **eciesjs major version mismatch between dApp SDK and mobile wallet creates untested cryptographic interoperability risk**  
  `cyfrin/connect.md`
- 🟡 **yUSDeVault` edge cases should be explicitly handled to prevent view functions from reverting**  
  `cyfrin/predeposit.md`

#### `storage-function` (20)

- 🟠 **Missing Effective Stake Decrease During Unstake**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **AccountableYield::setNavGracePeriod` uses `Unauthorized` error for invalid input**  
  `cyfrin/pr50.md`
- 🟡 **Deactivated Model Still Usable for Sessions and Node**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Don't emit misleading events when roles haven't been added or revoked**  
  `cyfrin/registry.md`
- 🟡 **Emit missing event information**  
  `cyfrin/syntetika.md`
- 🟡 **Emit missing events for storage changes**  
  `cyfrin/pledge.md`
- 🟡 **Fast fast by performing input-related checks first**  
  `cyfrin/manager.md`
- 🟡 **Missing Gas Tank Auto-Fill for Recipients in Bulk Transfers**  
  `HackenPDFTXT/Dexalot.txt`
- 🟡 **Missing Refund Mechanism for Regular Members Leads To**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Missing getter function for `SablierBobState::isStakedInAdapter**  
  `cyfrin/escrow.md`
- 🟡 **Missing minimum deposit enforcement**  
  `cyfrin/trade.md`
- 🟡 **More efficient implementation of `SessionManager::joinGame` via better storage packing**  
  `cyfrin/protocol.md`
- 🟡 **Neg-risk events have no void/cancellation path**  
  `cyfrin/clob.md`
- 🟡 **Prefer `calldata` to `memory` for external read-only function inputs**  
  `cyfrin/protocol.md`
- 🟡 **Rename all `sessionId` to `gameId` or vice versa for consistency**  
  `cyfrin/protocol.md`
- 🟡 **Storage Inconsistency in `migrateTokenManager` Function**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **Storage read optimizations**  
  `cyfrin/accountable.md`
- 🟡 **Taker receives Aave yield for cancelled pending bets**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use `uint32` for timestamps for better storage packing**  
  `cyfrin/protocol.md`
- 🟡 **use fixed length array for `reSDLTokenIds**  
  `cyfrin/vesting.md`

#### `validation-zero` (19)

- 🔴 **Missing source validation in CCIP message handling**  
  `cyfrin/yieldfi.md`
- 🔴 **Native Input Routed as Zero for Native-Send Routes**  
  `HackenPDFTXT/Dirol.txt`
- 🟠 **Improper Weight Reset on tokenIn Change Allows**  
  `HackenPDFTXT/Dirol.txt`
- 🟠 **Surplus::processSurplus` always reverts for managed collateral - diamond holds zero balance**  
  `cyfrin/parallel3.1.md`
- 🟡 **Auction Mode Bypass in bulkTransferTokens Allows**  
  `HackenPDFTXT/Dexalot.txt`
- 🟡 **DividendManager::distributePayout` records a new payout record increasing the current payout index for zero `payoutAmount**  
  `cyfrin/pledge.md`
- 🟡 **Floor division in `SablierLidoAdapter::updateStakedTokenBalance` allows transferring `BobVaultShares` without moving wstETH backing**  
  `cyfrin/escrow.md`
- 🟡 **Incomplete mapping updates in `setVault` function cause vault address inconsistencies**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Insufficient duration validation in `STBL_Register::setupAsset` can lock user withdrawals**  
  `cyfrin/stbl.md`
- 🟡 **Lack of Contract Address in Signed Payload Leads to**  
  `HackenPDFTXT/Panini America.txt`
- 🟡 **Missing State Validation Enables Re-Subscription to An**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **Missing Validation of Fallback APR Values in `AprPairFeed::latestRoundData**  
  `cyfrin/tranches.md`
- 🟡 **Missing controller validation in `AccountableAsyncRedeemVault::requestRedeem` allows zero address state**  
  `cyfrin/accountable.md`
- 🟡 **Missing mode field validation in walletclient allows handler selection via untrusted input**  
  `cyfrin/connect.md`
- 🟡 **Missing zero address checks in `STBL_Register::setupAsset**  
  `cyfrin/stbl.md`
- 🟡 **Missing zero deposit amount validation**  
  `cyfrin/predeposit.md`
- 🟡 **NegRiskAdapter::createEvent` allows different `closesAt` across outcome markets**  
  `cyfrin/clob.md`
- 🟡 **Referral rewards accumulate to `address(0)` when players aren't referred**  
  `cyfrin/protocol.md`
- 🟡 **Uninitialized minWithdrawAmount Allows Zero-Amount**  
  `HackenPDFTXT/BullBit.txt`

#### `contracts-upgradeable` (19)

- 🟡 **AllowList::hasTradeRestriction` mutability should be set to `view**  
  `cyfrin/pledge.md`
- 🟡 **Anyone should be able to conclude the game once winners have been determined**  
  `cyfrin/protocol.md`
- 🟡 **ComplianceServiceRegulated::getComplianceTransferableTokens` should call `IDSLockManager::getTransferableTokensForInvestor**  
  `cyfrin/rebasing.md`
- 🟡 **DefaultSession::assertResults` should verify input `sessionId` belongs to a game associated with its instance**  
  `cyfrin/protocol.md`
- 🟡 **Extra data should only be decoded when its length is exactly 96 bytes**  
  `cyfrin/vii.md`
- 🟡 **IBeforeInitializeHook` should be added to the `AngstromL2` inheritance chain**  
  `cyfrin/angstrom.md`
- 🟡 **In `RemoraToken::adminClaimPayout`, `adminTransferFrom` don't call `hasSignedDocs` when `checkTC == false**  
  `cyfrin/pledge.md`
- 🟡 **Incorrect link to Angle contracts across protocol**  
  `cyfrin/parallel3.1.md`
- 🟡 **Lack of `_disableInitializers` in upgradeable contracts**  
  `cyfrin/yieldfi.md`
- 🟡 **Lack of `_lockTime` validation in `constructor**  
  `cyfrin/vesting.md`
- 🟡 **Misleading comments and documentation inconsistencies in on-ramp contracts**  
  `cyfrin/bridge.md`
- 🟡 **Outdated reference to rebalance in `IHooklet::afterSwap` should be removed**  
  `cyfrin/hooklet.md`
- 🟡 **SablierLidoAdapter::unstakeFullAmount` should return `totalWstETH**  
  `cyfrin/escrow.md`
- 🟡 **Skip call to `CDO::accrueFee` when there are no fees to charge**  
  `cyfrin/cooldown.md`
- 🟡 **Upgradeable contracts missing _disableInitializers() in constructors**  
  `cyfrin/bridge.md`
- 🟡 **Upgradeable contracts should call `_disableInitializers` in constructor**  
  `cyfrin/rebasing.md`
- 🟡 **Variables in non-upgradeable contracts which are only set once in `constructor` should be declared `immutable**  
  `cyfrin/pledge.md`
- 🟡 **Variables only set once in `constructor` of non-upgradeable contracts should be declared `immutable**  
  `cyfrin/syntetika.md`
- 🟡 **pUSDeVault::startYieldPhase` should not remove supported vaults from being supported or should prevent new supported vaults once in the yield phase**  
  `cyfrin/predeposit.md`

#### `rewards-referral` (18)

- 🔴 **DepositManager::_refundEntryFee` doesn't deduct referral rewards allowing users to join then leave games to drain tokens via inflated referral rewards they aren't entitled to**  
  `cyfrin/protocol.md`
- 🔴 **Instant withdrawals in priority pool can result in loss of funds for StakingProxy contract**  
  `cyfrin/stakingproxy.md`
- 🔴 **[DualDefense] Exited Delegator Receives Rewards**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟠 **Incorrect BeforeSwapDelta Mapping Causes Fee To Be**  
  `HackenPDFTXT/Launchly.txt`
- 🟠 **Incorrect summation of curator shares in `claimUndistributedRewards` leads to deficit in claimed undistributed rewards**  
  `cyfrin/core.md`
- 🟠 **Team Rewards Accumulate Without Required Active Stake**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **Incorrect Handling of reserveFee During dex()**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Incorrect Progressive-TGE Calculation Order Leads to**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Incorrect Referral Traversal in _addDownlines() Skips**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **Incorrect `recordResult` recorded for each question in `recordResults**  
  `cyfrin/protocol.md`
- 🟡 **Incorrect error message in `_checkNotBlacklisted**  
  `cyfrin/wlf.md`
- 🟡 **Incorrect haircut asset value conversion in `STBL_PT1_Issuer::generateMetaData**  
  `cyfrin/stbl.md`
- 🟡 **Incorrect inclusion of removed nodes in `_requireMinSecondaryAssetClasses` during `forceUpdateNodes**  
  `cyfrin/core.md`
- 🟡 **Incorrect maxSellAmount Calculation Allows Selling Up to**  
  `HackenPDFTXT/Node Meta.txt`
- 🟡 **Incorrect vault status determination in `MiddlewareVaultManager**  
  `cyfrin/core.md`
- 🟡 **Reducing reserves requesting `USDe` as the asset to receive causes the Strategy to release more `sUSDe` than necessary**  
  `cyfrin/tranches.md`
- 🟡 **Unclaimable rewards for removed vaults in `Rewards::claimRewards**  
  `cyfrin/core.md`
- 🟡 **Uptime loss due to integer division in `UptimeTracker::computeValidatorUptime` can make validator lose entire rewards for an epoch**  
  `cyfrin/core.md`

#### `unnecessary-usage` (18)

- 🔴 **Adapter vault `_userWstETH` not cleared after redemption enables theft of other users' funds**  
  `cyfrin/escrow.md`
- 🟠 **Attacker can make pledge on behalf of users if those users have approved `PledgeManager` to spend their tokens**  
  `cyfrin/pledge.md`
- 🟠 **Double Taxation on Liquidity ETH Removal via Router**  
  `HackenPDFTXT/Node Meta.txt`
- 🟠 **Native Balance Sweep via Absolute Balance on NATIVE**  
  `HackenPDFTXT/Dirol.txt`
- 🟠 **[DualDefense] Double Effective Stake Reduction on**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **Auto-draw on `AccountableFixedTerm::pay` lets third parties force unwanted borrowing**  
  `cyfrin/accountable.md`
- 🟡 **Changing stablecoin on TokenBank can mess up fees collection**  
  `cyfrin/pledge.md`
- 🟡 **Incorrect `chainid` prevents correct Strategy deployment on Berachain**  
  `cyfrin/d2.md`
- 🟡 **Incorrect usage of minOutputAmount in executeTwoStepRedemption can cause unnecessary reverts**  
  `cyfrin/bridge.md`
- 🟡 **Missing modifiers on `YieldStrategyFactory.createYieldStrategy` can lead to deployment of unverified strategies**  
  `cyfrin/pr50.md`
- 🟡 **Remove unnecessary imports and inheritance**  
  `cyfrin/pledge.md`
- 🟡 **Unnecessary `onlyRegisteredOperatorNode` on `completeStakeUpdate` function**  
  `cyfrin/core.md`
- 🟡 **Unnecessary override keywords on interface implementation functions**  
  `cyfrin/bridge.md`
- 🟡 **Unnecessary usage of `_msgSender()` to validate if caller is the `Issuer` on the `STBL_PT1_YieldDistributor**  
  `cyfrin/stbl.md`
- 🟡 **Unnecessary usage of `nonReentrant` modifier on `ReferralManager::completeFirstPurchase**  
  `cyfrin/final.md`
- 🟡 **Usage of unofficial wormhole-solidity-sdk npm package poses security and maintenance risks**  
  `cyfrin/bridge.md`
- 🟡 **Use `ReentrancyGuardTransient` for faster `nonReentrant` modifiers**  
  `cyfrin/syntetika.md`
- 🟡 **nonReentrant` is not the first modifier**  
  `cyfrin/accountable.md`

#### `support-vault` (18)

- 🔴 **Rewards Drain due to Invalid Last Claimed Period Update**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟠 **Security Mechanisms Inoperative due to OpenZeppelin v5**  
  `HackenPDFTXT/RYT.txt`
- 🟠 **Winner Selection Ignores Assigned Payout Positions Due To**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **AUM inflated in vault kit strategies due**  
  `sherlockPDFTXT/Vesu Vaults.txt`
- 🟡 **Accumulative reward setting to prevent overwrite and support incremental updates**  
  `cyfrin/core.md`
- 🟡 **BasisTradeTailor` is ERC-165 non compliant**  
  `cyfrin/trade.md`
- 🟡 **Decompression Bomb due to lack of  post decompression size check**  
  `cyfrin/connect.md`
- 🟡 **DelegationManager is incompatible with smart contract wallets with Approved hashes**  
  `cyfrin/DelegationFramework1.md`
- 🟡 **Double Fee Charged in Limit Order Execution Due to**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **ERC 1155 `safeTransferFrom` callbacks forward unbounded gas to EIP 7702 EOAs**  
  `cyfrin/clob.md`
- 🟡 **FeeModule::_lookupFees` returns zero fees at price = 1e18 due to strict less-than comparison**  
  `cyfrin/clob.md`
- 🟡 **Lack of multicall support for `FeeOverrideHooklet::setFeeOverride**  
  `cyfrin/hooklet.md`
- 🟡 **Malicious investor can register wallets that belong to other investors**  
  `cyfrin/rebasing.md`
- 🟡 **PoketFactory` is ERC-165 non compilant**  
  `cyfrin/update.md`
- 🟡 **Smart contract wallets cannot sign orders due to missing ERC 1271 support**  
  `cyfrin/clob.md`
- 🟡 **Some SherpaUSD can never be unstaked due to minimumSupply check**  
  `cyfrin/sherpa.md`
- 🟡 **Use `SignatureChecker` library and optionally support `EIP7702` accounts which use their private key to sign**  
  `cyfrin/pledge.md`
- 🟡 **Vault limit cannot be modified if vault Is already enabled**  
  `cyfrin/core.md`

#### `user-tokens` (17)

- 🟠 **Fees can be stolen from partially unwrapped `UniswapV4Wrapper` positions**  
  `cyfrin/vii.md`
- 🟠 **Users Can Perform New Tokens Purchase After**  
  `HackenPDFTXT/Seedify.fund.txt`
- 🟡 **Active and pending bets can be cancelled by anyone**  
  `cyfrin/wannabetv2.md`
- 🟡 **AngstromL2::_computeAndCollectProtocolSwapFee` computation can be simplified**  
  `cyfrin/angstrom.md`
- 🟡 **BridgeCCIP.isL1` can be immutable**  
  `cyfrin/yieldfi.md`
- 🟡 **Buyers can pledge for tokens without having signed all documents that are required to be signed**  
  `cyfrin/pledge.md`
- 🟡 **Duplicate vaults can be pushed to `assetsArr**  
  `cyfrin/predeposit.md`
- 🟡 **Effective price calculations can be affected by edge cases in `Math512Lib::sqrt512` and `Math512Lib::div512by256**  
  `cyfrin/angstrom.md`
- 🟡 **Overriding fees can't be switched back once set**  
  `cyfrin/pledge.md`
- 🟡 **Recover Function Can Steal User Funds**  
  `HackenPDFTXT/A Two Tech Limited.txt`
- 🟡 **SDLVesting::claimRESDLRewards()` can be used to drain the entire vesting contract balance in edge case**  
  `cyfrin/vesting.md`
- 🟡 **Superfluous vault support validation can be removed from `pUSDeDepositor::deposit**  
  `cyfrin/predeposit.md`
- 🟡 **Unnecessarily complex iteration logic in `MetaVault::redeemMetaVaults` can be simplified**  
  `cyfrin/predeposit.md`
- 🟡 **Unnecessary arithmetic validation within `AngstromL2::withdrawProtocolRevenue` can be removed**  
  `cyfrin/angstrom.md`
- 🟡 **Unsafe external calls made during proportional LP fee transfers can be used to reenter wrapper contracts**  
  `cyfrin/vii.md`
- 🟡 **burnFrom Can Brick User Accounts**  
  `HackenPDFTXT/Tokenizer.Estate.txt`
- 🟡 **collatInfo.stablecoinCap` hardcap can be bypassed via `SettersGovernor::adjustStablecoins**  
  `cyfrin/parallel3.1.md`

#### `instead-sender` (16)

- 🟡 **Consider emitting events early to save gas**  
  `cyfrin/pr50.md`
- 🟡 **Gas optimization for `getVaults` function**  
  `cyfrin/core.md`
- 🟡 **Meta transactions will not work due to direct msg.sender usage in validateLockedTokens**  
  `cyfrin/dstokenswap.md`
- 🟡 **Reuse `fm` Instead of re-instantiating `IFeeManager` in `AccountableOpenTerm::_mintFeeShares**  
  `cyfrin/pr50.md`
- 🟡 **Subscription Renewal Resets Timer Instead of Extending**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **To prevent duplicate ids in `_batchBurn`, enforce ascending order instead of nested `for` loops**  
  `cyfrin/cryptoart.md`
- 🟡 **Unimplemented pendingReward State Variable Results in**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **Use `Ownable2Step` instead of `Ownable**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use `SafeERC20::forceApprove` instead of standard `IERC20::approve**  
  `cyfrin/predeposit.md`
- 🟡 **Use `msg.sender` instead of accessing `comptroller` state variable to save gas**  
  `cyfrin/escrow.md`
- 🟡 **Use constants instead of magic numbers**  
  `cyfrin/pledge.md`
- 🟡 **Use explicit sizes instead of `uint**  
  `cyfrin/predeposit.md`
- 🟡 **Use explicit unsigned integer sizing instead of `uint**  
  `cyfrin/tranches.md`
- 🟡 **Use of `msg.sender` instead of `_msgSender()` prevents meta-transaction support**  
  `cyfrin/bridge.md`
- 🟡 **Use preview_redeem(...) instead of con**  
  `sherlockPDFTXT/Vesu Vaults.txt`
- 🟡 **Using explicit unsigned integer sizing instead of `uint**  
  `cyfrin/pledge.md`

#### `event-updates` (15)

- 🟠 **Immediate stake cache updates enable reward distribution without P-Chain confirmation**  
  `cyfrin/core.md`
- 🟠 **Weights Misapplied When Routes Are Not Grouped By**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **Consider emitting event when synchronizing `lstLiabilityPrincipal**  
  `cyfrin/manager.md`
- 🟡 **Country updates is not reducing from the storage the prev country**  
  `cyfrin/rebasing.md`
- 🟡 **DVNPublisher::publish` does not enforce a maximum age for updates**  
  `cyfrin/pr50.md`
- 🟡 **ExitWithinGracePeriod` event emits inaccurate `amountReceived` for adapter vaults**  
  `cyfrin/escrow.md`
- 🟡 **Fee structure updates can trigger accrual after loan has ended**  
  `cyfrin/pr50.md`
- 🟡 **Game creator can call `TriviaChoicePrompt::revealSolutions` before the `reactionDeadline` or end of game, griefing players from submitting answers while still retaining player entry fees**  
  `cyfrin/protocol.md`
- 🟡 **Lack of event emissions on important state changes**  
  `cyfrin/yieldfi.md`
- 🟡 **Market pause flag not enforced by `ConditionalTokens::splitPosition**  
  `cyfrin/clob.md`
- 🟡 **Off-By-One Error in `_exceedsMaxClaimablePeriods()`**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **Optimize setters by emitting event before state updates**  
  `cyfrin/sherpa.md`
- 🟡 **SherpaUSD::consumeTotalStakedApproval` and `SherpaUSD::consumeAccountingApproval` callable by anyone**  
  `cyfrin/sherpa.md`
- 🟡 **State change without event**  
  `cyfrin/clob.md`
- 🟡 **forceTransfer is Blocked by Pause**  
  `HackenPDFTXT/Tokenizer.Estate.txt`

#### `hardcoded-overpayment` (14)

- 🟠 **Secondary Contributions Not Recorded in Slot Total, Leading**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Fix comment in `revealSolution**  
  `cyfrin/protocol.md`
- 🟡 **Hardcoded Primary Pair In _calculatePriceImpact() Leads To**  
  `HackenPDFTXT/Node Meta.txt`
- 🟡 **Hardcoded Private Key Exposure in Test Scripts Enables**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **High centralization risk in `STBL_USST::bridgeBurn**  
  `cyfrin/stbl.md`
- 🟡 **Overpayment vulnerability in `registerL1**  
  `cyfrin/core.md`
- 🟡 **PerpetualBond.epoch` not updated after yield distribution**  
  `cyfrin/yieldfi.md`
- 🟡 **Precompute `baseSlot` in `AtomicBatcher::_getNonceSlot**  
  `cyfrin/pr50.md`
- 🟡 **Precompute `callTypeHash` in `AtomicBatcher::_hashCallArray**  
  `cyfrin/pr50.md`
- 🟡 **Prevent negative assertion following previous truthful assertion in `DefaultSession::assertionResolvedCallback**  
  `cyfrin/protocol.md`
- 🟡 **Rename `isAllowed` to `wasAllowed` in `Allowlist::allowUser`, `disallowUser**  
  `cyfrin/pledge.md`
- 🟡 **Static `gasLimit` will result in overpayment**  
  `cyfrin/yieldfi.md`
- 🟡 **Zero‑Duration vesting edge case**  
  `cyfrin/vesting.md`
- 🟡 **bondFaceValue` read in `PerpetualBond::_convertToBond` can be cached**  
  `cyfrin/yieldfi.md`

#### `payouts-holder` (14)

- 🔴 **A single holder can grief the payouts of all holders forwarding their payouts to the same forwarder**  
  `cyfrin/pledge.md`
- 🟠 **All rewards can be stolen due to incorrect active liquidity calculations when the current tick is an exact multiple of the tick spacing at the upper end of a liquidity range**  
  `cyfrin/angstrom.md`
- 🟠 **If multiple users call `DefaultSession::assertResults` all but the first caller lose their bonds**  
  `cyfrin/protocol.md`
- 🟡 **Burning ALL PropertyTokens of a frozen holder results in the holder losing the payouts distribution while he was frozen**  
  `cyfrin/pledge.md`
- 🟡 **Collector can add `CreatorStory`, corrupting the provenance of an artwork**  
  `cyfrin/cryptoart.md`
- 🟡 **Consider limiting max royalty to prevent large amount or all of the sale fee being taken as royalty**  
  `cyfrin/cryptoart.md`
- 🟡 **Forwarders can lose payouts of the holders forwarding to them**  
  `cyfrin/pledge.md`
- 🟡 **Forwarders who aren't also holders are unable to claim forwarded payouts**  
  `cyfrin/pledge.md`
- 🟡 **NegRisk market creator is set to adapter address instead of the initiator**  
  `cyfrin/clob.md`
- 🟡 **Operators can lose their reward share**  
  `cyfrin/core.md`
- 🟡 **PaymentSettler::claimAllPayouts` doesn't validate input `tokens` addresses are legitimate contracts before calling `adminClaimPayout` on them**  
  `cyfrin/pledge.md`
- 🟡 **Same user can join the same game multiple times increasing their chance of winning by preventing other players from participating**  
  `cyfrin/protocol.md`
- 🟡 **Seizing payouts for frozen users can lead to double spending if the holder is unfrozen in subsequent distributions**  
  `cyfrin/final.md`
- 🟡 **Withdrawals can effectively only happen on the primary chain after any yield has accrued**  
  `cyfrin/sherpa.md`

#### `sell-never` (13)

- 🟠 **Excessive Initial Sell Tax Can Severely Restrict Exits and Is**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟠 **Unvalidated taxDenominator Breaks Tax Cap Invariants and**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **AccountableOpenTerm` manual interest rate proposal is unbounded**  
  `cyfrin/pr50.md`
- 🟡 **Auto-Swap Reverts During Sell Execution Can Deny User**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **Buy and Sell Fees Unexpectedly Applied During Liquidity**  
  `HackenPDFTXT/Node Meta.txt`
- 🟡 **Fee Distribution in _autoSwapBack Uses Configured Tax**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **Judge can designate arbitrary winner who is neither maker nor taker**  
  `cyfrin/wannabetv2.md`
- 🟡 **MintType` is almost never enforced**  
  `cyfrin/cryptoart.md`
- 🟡 **Pledge can't successfully complete unless `RemoraToken` is paused**  
  `cyfrin/pledge.md`
- 🟡 **Prompt::finalizedAnswer` is never set**  
  `cyfrin/protocol.md`
- 🟡 **StakedTrUSD.reportLoss is blocked dur-**  
  `sherlockPDFTXT/Tori Finance.txt`
- 🟡 **TrustService::changeEntityOwner` can overwrite existing `_newOwner` record, breaking 1-1 relationship between owners and addresses**  
  `cyfrin/rebasing.md`
- 🟡 **Wrong value is returned in `upperLookupRecentCheckpoint**  
  `cyfrin/core.md`

#### `tranche-withdrawers` (13)

- 🔴 **Primary Contributor Deposits Are Not Recorded, Leading to**  
  `HackenPDFTXT/RYT.txt`
- 🔴 **Withdrawers of `sUSDe` always incur a loss because parameters passed from `Tranche::_withdraw` to `CDO::withdraw` are inverted**  
  `cyfrin/tranches.md`
- 🟠 **Impossible for user to get refund after re-joining a rescheduled game which is subsequently cancelled**  
  `cyfrin/protocol.md`
- 🟡 **Cheaper not to cache `calldata` array length**  
  `cyfrin/rebasing.md`
- 🟡 **Code duplication in function overrides that only add modifiers**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Consider switching to `ReentrancyGuardTransient**  
  `cyfrin/clob.md`
- 🟡 **Don't cache `calldata` array length**  
  `cyfrin/harbor.md`
- 🟡 **JR Tranche is susceptible to bankrun scenarios given that `SharesCooldown` finalization allows to bypass `minimumJrtSrtRatio` and first withdrawers from JR Tranche get a better cooldown and fees compared to late withdrawers**  
  `cyfrin/cooldown.md`
- 🟡 **Misleading variable name to set the `asset` for the `Tranche**  
  `cyfrin/tranches.md`
- 🟡 **SessionManager::revealGameQuestion` doesn't validate that input `_questionId` belongs to input `_gameId**  
  `cyfrin/protocol.md`
- 🟡 **Tokens that were locked when `lockUpTime > 0` will be impossible to unlock if `lockUpTime` is set to zero**  
  `cyfrin/pledge.md`
- 🟡 **Transferring all the investor balance from a non-us investor to a new us investor allows to bypass the `usInvestorLimit**  
  `cyfrin/rebasing.md`
- 🟡 **User can join after the first question is revealed to gain an advantage over other users**  
  `cyfrin/protocol.md`

#### `calls-redundant` (12)

- 🟠 **ZkSwap Router Mismatch: Calls Non-Existent**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **BasisTradeTailor::coreDepositWallet` is not blocked for adapters calls**  
  `cyfrin/update.md`
- 🟡 **Cache result of external calls when result can't change between calls and is used multiple times**  
  `cyfrin/tranches.md`
- 🟡 **Cooldown Timer Reset on Repeated Calls Leads to Extended**  
  `HackenPDFTXT/Overlayer.txt`
- 🟡 **Frequent `AccountableOpenTerm::accrueInterest` calls reduce interest accrual**  
  `cyfrin/accountable.md`
- 🟡 **Impossible to remove a document added with zero uri length**  
  `cyfrin/pledge.md`
- 🟡 **MyriadCTFExchange::_requireMarketOpen` makes two external calls to `manager**  
  `cyfrin/clob.md`
- 🟡 **Optimize `_getStakerVaults` to Avoid Redundant External Calls to `activeBalanceOfAt**  
  `cyfrin/core.md`
- 🟡 **Redundant `FUNDER_ROLE` in `LineaRollupYieldExtension**  
  `cyfrin/manager.md`
- 🟡 **Redundant `approve(0)` in `BasisTradeVault::depositToTailor**  
  `cyfrin/trade.md`
- 🟡 **Redundant variable statements**  
  `cyfrin/trade.md`
- 🟡 **Remove redundant calls to `EnumerableSet::contains**  
  `cyfrin/registry.md`

#### `doesn-pusdevault` (12)

- 🔴 **Attacker can drain all tokens from cancelled game since `SessionManager::refundCancelledGame` doesn't validate caller actually joined the game**  
  `cyfrin/protocol.md`
- 🟡 **BridgeableTokenP::getMaxDebitableAmount` doesn't account for isolate mode, returning inflated values**  
  `cyfrin/parallel3.1.md`
- 🟡 **ETH sent with adapter vault redemption is trapped in `SablierBob**  
  `cyfrin/escrow.md`
- 🟡 **Inconsistency in `currentPhase` between `pUSDeVault` and `yUSDeVault**  
  `cyfrin/predeposit.md`
- 🟡 **Manual/Instant `fulfillRedeemRequest` doesn’t reserve liquidity**  
  `cyfrin/accountable.md`
- 🟡 **More efficient way of checking for empty string in `CommonUtils::isEmptyString**  
  `cyfrin/rebasing.md`
- 🟡 **Pausing Disables Allowance Revocation Leaving Users**  
  `HackenPDFTXT/NEBA Token.txt`
- 🟡 **PocketFactory::approveTailor` doesn't verify `ITailor` interface implementation**  
  `cyfrin/update.md`
- 🟡 **Prefix internal and private function names with `_` character**  
  `cyfrin/predeposit.md`
- 🟡 **Roles not set in `deposit-registry` contract constructors**  
  `cyfrin/syntetika.md`
- 🟡 **pUSDeVault::maxDeposit` doesn't account for deposit pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault**  
  `cyfrin/predeposit.md`
- 🟡 **pUSDeVault::maxRedeem` doesn't account for redemption pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault**  
  `cyfrin/predeposit.md`

#### `logic-reward` (11)

- 🟠 **DepositManager::getRewards` always includes `REFERRER_FEE` resulting in 2 percent of every games' rewards not being distributed to winners when there were no referrers**  
  `cyfrin/protocol.md`
- 🟠 **Incorrect reward claim logic causes loss of access to intermediate epoch rewards**  
  `cyfrin/core.md`
- 🟠 **Vault rewards incorrectly scaled by cross-asset-class operator totals instead of asset class specific shares causing rewards leakage**  
  `cyfrin/core.md`
- 🟠 **Winner-Selection Logic Flaw Allows The Group Creator To**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Access to `LockBox::unlock` doesn't follow principle of least privilege**  
  `cyfrin/yieldfi.md`
- 🟡 **AngstromL2::_oneForZeroCreditRewards` should skip execution of range reward logic if there is no liquidity**  
  `cyfrin/angstrom.md`
- 🟡 **Consider burning `ERC-6909` claim tokens within `AngstromL2::withdrawProtocolRevenue` and transferring the underlying asset instead**  
  `cyfrin/angstrom.md`
- 🟡 **Historical reward loss due to `NodeId` reuse in `AvalancheL1Middleware**  
  `cyfrin/core.md`
- 🟡 **L2 Sequencer Status Check Logic Inver-**  
  `sherlockPDFTXT/YieldFi.txt`
- 🟡 **Operator can over allocate the same stake to unlimited nodes within one epoch causing weight inflation and reward theft**  
  `cyfrin/core.md`
- 🟡 **Optimisation of elapsed epoch calculation**  
  `cyfrin/core.md`

#### `check-length` (11)

- 🟠 **Missing Check for Residual Input Tokens When Route**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **Array length checks in `FixedRanksReward::getRewards`, `getReward` check against the wrong comparator**  
  `cyfrin/protocol.md`
- 🟡 **Balance check for yield claims in `PerpetualBond::_validate` can be easily bypassed**  
  `cyfrin/yieldfi.md`
- 🟡 **Enforce minimum transaction amounts in `StakingVault**  
  `cyfrin/syntetika.md`
- 🟡 **Invalid validateRedemptionParams check**  
  `cyfrin/cooldown.md`
- 🟡 **Lack of check for 0 shares minted**  
  `cyfrin/trade.md`
- 🟡 **Missing USER_ROLE Check Allows Unauthorized**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Missing vesting check in `PerpetualBond::setVestingPeriod**  
  `cyfrin/yieldfi.md`
- 🟡 **Missing zero length check in `AllowedMethodsEnforcer::getTermsInfo()**  
  `cyfrin/DelegationFramework1.md`
- 🟡 **STBL_Register::addAsset` does not check for non-empty asset name**  
  `cyfrin/stbl.md`
- 🟡 **_receiverGas` check excludes minimum acceptable value**  
  `cyfrin/yieldfi.md`

#### `unused-remove` (11)

- 🟡 **Remove `< 0` comparison for unsigned integers**  
  `cyfrin/pledge.md`
- 🟡 **Remove setting deprecated `lastUpdatedBy` in RegistryService**  
  `cyfrin/rebasing.md`
- 🟡 **Remove todo comments**  
  `cyfrin/manager.md`
- 🟡 **Remove unused constant `CryptoartNFT::ROYALTY_BASE**  
  `cyfrin/cryptoart.md`
- 🟡 **Remove useless function `ComplianceServiceRegulated::adjustTransferCounts**  
  `cyfrin/rebasing.md`
- 🟡 **Unused constants**  
  `cyfrin/yieldfi.md`
- 🟡 **Unused custom error should removed if not required**  
  `cyfrin/angstrom.md`
- 🟡 **Unused error `IBet::InvalidAmount**  
  `cyfrin/wannabetv2.md`
- 🟡 **Unused errors**  
  `cyfrin/yieldfi.md`
- 🟡 **Unused imports**  
  `cyfrin/yieldfi.md`
- 🟡 **Unused library and struct definitions increase deployment costs and reduce code clarity**  
  `cyfrin/bridge.md`

#### `assets-withdraw` (10)

- 🔴 **Partial redemptions can be used to steal assets**  
  `cyfrin/accountable.md`
- 🟡 **Disabled operators can register new validator nodes**  
  `cyfrin/core.md`
- 🟡 **Excessive Emergency Withdraw Can Steal User Funds**  
  `HackenPDFTXT/A Two Tech Limited.txt`
- 🟡 **If zero xp is earned by all users, once game has concluded `SessionManager::claimRewards` panic reverts due to division by zero but game also can't be cancelled resulting in locked tokens**  
  `cyfrin/protocol.md`
- 🟡 **Inline small internal functions only used once**  
  `cyfrin/predeposit.md`
- 🟡 **LockUpManager::LockUpStorage::_regLockUpTime` is never used**  
  `cyfrin/pledge.md`
- 🟡 **No way to compound deposited supported vault assets into `sUSDe` stake during yield phase**  
  `cyfrin/predeposit.md`
- 🟡 **Non-compliant users can claim withdrawn assets after the cooldown period**  
  `cyfrin/syntetika.md`
- 🟡 **Reserved assets could be extracted from the Vault**  
  `cyfrin/accountable.md`
- 🟡 **Treasury cannot withdraw expired assets if NFT is disabled**  
  `cyfrin/stbl.md`

#### `storage-prior` (9)

- 🟡 **Allow custom Creator and Collector names to be emitted in `IStory` events to build artwork provenance**  
  `cyfrin/cryptoart.md`
- 🟡 **Consider reverting in `publishedDataByBatchId` for invalid batch IDs**  
  `cyfrin/pr50.md`
- 🟡 **Don't copy entire `Assertion` struct from `storage` to `memory` in `DefaultSession::assertionResolvedCallback**  
  `cyfrin/protocol.md`
- 🟡 **Don't write to the same storage slot multiple times**  
  `cyfrin/rebasing.md`
- 🟡 **In `Bet::accept,resolve,cancel` update `Bet` state prior to external calls**  
  `cyfrin/wannabetv2.md`
- 🟡 **In `tokenURI` avoid copying entire `_tokenURIs[tokenId]` from `storage` into `memory**  
  `cyfrin/cryptoart.md`
- 🟡 **Perform input-related checks prior to reading storage**  
  `cyfrin/protocol.md`
- 🟡 **Perform storage updates prior to external calls**  
  `cyfrin/protocol.md`
- 🟡 **State changes without events**  
  `cyfrin/accountable.md`

#### `manager-vault` (9)

- 🟡 **Confusing variable naming in fee manager contracts**  
  `cyfrin/bridge.md`
- 🟡 **Early Cancel Fee Applied on Depositor-Triggered Timeouts**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **FeeModule::setMarketFees` permits 100% fee rates**  
  `cyfrin/clob.md`
- 🟡 **In zero-fee case, flashloan can result in a few wei profit**  
  `cyfrin/parallel3.1.md`
- 🟡 **Manager::_transferFee` returns invalid `feeShares` when `fee` is zero**  
  `cyfrin/yieldfi.md`
- 🟡 **Mismatching variable naming for `Metadata.depositBlock**  
  `cyfrin/stbl.md`
- 🟡 **Order read twice in `Manager::executeOrder**  
  `cyfrin/yieldfi.md`
- 🟡 **Shared configuration parameters across different asset types in vault deployers leads to incorrect pricing and fee calculations**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Vault fee distribution incorrectly incurs**  
  `sherlockPDFTXT/Vesu Vaults.txt`

#### `storage-reads` (9)

- 🟡 **Cache identical storage reads**  
  `cyfrin/pledge.md`
- 🟡 **Cache identical storage reads**  
  `cyfrin/predeposit.md`
- 🟡 **Cache identical storage reads and only write to storage once**  
  `cyfrin/protocol.md`
- 🟡 **Cache repeated storage reads**  
  `cyfrin/clob.md`
- 🟡 **Cache storage slots to prevent identical storage reads**  
  `cyfrin/wannabetv2.md`
- 🟡 **Cache storage to prevent identical storage reads**  
  `cyfrin/escrow.md`
- 🟡 **Cache storage to prevent identical storage reads**  
  `cyfrin/harbor.md`
- 🟡 **Don't perform storage reads unless necessary**  
  `cyfrin/rebasing.md`
- 🟡 **Fast fail without performing unnecessary storage reads or external calls**  
  `cyfrin/rebasing.md`

#### `time-session` (8)

- 🟡 **Assembly blocks could benefit from `"memory-safe"` annotation**  
  `cyfrin/spingame.md`
- 🟡 **Compliance Status is Decoupled from Voting Power**  
  `HackenPDFTXT/Tokenizer.Estate.txt`
- 🟡 **Dispute Window Calculated From Session Start Time Instead**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Insufficient update window validation can cause denial of service in `forceUpdateNodes**  
  `cyfrin/core.md`
- 🟡 **Refund Failure Prevents Host Payment and Locks Session**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **SessionManager::rescheduleGame` advances the start time but not the end time allowing for a griefing attack where the game creator can collect fees while preventing users from participating**  
  `cyfrin/protocol.md`
- 🟡 **Testnet Time Constants Used in Production Code**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **Users can bypass vault lock and withdraw at any time**  
  `cyfrin/escrow.md`

#### `return-remove` (7)

- 🟡 **Remove obsolete `return` statements when already using named return variables**  
  `cyfrin/rebasing.md`
- 🟡 **Remove obsolete `return` statements when already using named return variables**  
  `cyfrin/wannabetv2.md`
- 🟡 **Remove obsolete `return` statements when using named return values**  
  `cyfrin/protocol.md`
- 🟡 **Remove obsolete `return` statements when using named return variables**  
  `cyfrin/syntetika.md`
- 🟡 **Remove obsolete `return` statements when using named returns**  
  `cyfrin/wlf.md`
- 🟡 **Remove obsolete final `return` statement when already using named returns**  
  `cyfrin/harbor.md`
- 🟡 **Remove obsolete return statements when using named return variables**  
  `cyfrin/trade.md`

#### `variables-return` (7)

- 🟡 **Refactor `LidoStVaultYieldProvider::_syncExternalLiabilitySettlement` to eliminate `liabilityETH**  
  `cyfrin/manager.md`
- 🟡 **SDLVesting::stakeReleasableTokens` gas optimization by caching variables**  
  `cyfrin/vesting.md`
- 🟡 **TickIterator::_advanceToNextUp` sets uninitialized end tick as the current tick which causes `TickIterator::hasNext` to return true when this is not actually the case**  
  `cyfrin/angstrom.md`
- 🟡 **Use named return variables when this eliminates local variables**  
  `cyfrin/syntetika.md`
- 🟡 **Use named return variables where this can eliminate local variables**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use named return variables where this can optimize away local variables**  
  `cyfrin/escrow.md`
- 🟡 **Use named returns where this eliminates a local variable and especially for `memory` returns**  
  `cyfrin/pledge.md`

#### `consistently-consider` (4)

- 🟡 **Consider consistently use `Ownable2Step**  
  `cyfrin/accountable.md`
- 🟡 **Consistently use `ErrorUtils::revertIfZeroAddress**  
  `cyfrin/manager.md`
- 🟡 **Use `EIP712Upgradeable` library to simplify `DocumentManager**  
  `cyfrin/pledge.md`
- 🟡 **Use `SafeCast` to safely downcast amounts**  
  `cyfrin/wlf.md`

#### `function-voting` (3)

- 🟠 **transferToCustody() function always re-**  
  `sherlockPDFTXT/Tori Finance.txt`
- 🟡 **Addresses excluded from voting power can re-gain their voting power via a delegatee or by transfering tokens**  
  `cyfrin/wlf.md`
- 🟡 **Unstake() Function Behaves Differently Than Documented**  
  `HackenPDFTXT/Acecoin.txt`

#### `validation-weak` (3)

- 🟡 **Consider removing redundant zero address check from `createYieldStrategy**  
  `cyfrin/pr50.md`
- 🟡 **No validation on `reactionDeadline` allows multiple griefing scenarios**  
  `cyfrin/protocol.md`
- 🟡 **Weak structural validation of connectionRequest from deeplink**  
  `cyfrin/connect.md`

### revert-lock (32)

#### `revert-permanently` (18)

- 🟠 **Expired Tokens Permanently Trapped**  
  `HackenPDFTXT/S3 Markets.txt`
- 🟠 **Permanent Phantom Stake Accumulation Due to Missing**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟠 **Proposal Fee Permanently Locked on Rejection**  
  `HackenPDFTXT/Fabstir.txt`
- 🟠 **Staking Capacity Permanently Lost as Stakes Complete**  
  `HackenPDFTXT/Acecoin.txt`
- 🟡 **AdminRegistry::proposeAdmin` self-proposal permanently removes `DEFAULT_ADMIN_ROLE**  
  `cyfrin/clob.md`
- 🟡 **Don't add duplicate `documentHash` to `DocumentManager::DocumentStorage::_docHashes` when overwriting via `_setDocument` as this causes panic revert when calling `_removeDocument**  
  `cyfrin/pledge.md`
- 🟡 **Excess Contributions Become Permanently Locked Due to**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Excessive amount `maximumContestants` could make games to revert in `DefaultSession::recordResults` due to out of gas**  
  `cyfrin/protocol.md`
- 🟡 **Getters::getCollateralSurplus` returns positive values even when `Surplus::processSurplus` is guaranteed to revert**  
  `cyfrin/parallel3.1.md`
- 🟡 **IERC7160` specification requires `hasPinnedTokenURI` to revert for non-existent `tokenId**  
  `cyfrin/cryptoart.md`
- 🟡 **IERC7160` specification requires `pinTokenURI` to revert for non-existent `tokenId**  
  `cyfrin/cryptoart.md`
- 🟡 **Insufficient validation in `AvalancheL1Middleware::removeOperator` can create permanent validator lockup**  
  `cyfrin/core.md`
- 🟡 **No way to revert `setInvestorLiquidateOnly**  
  `cyfrin/rebasing.md`
- 🟡 **Revert fast by performing input related checks prior to storage reads and external calls**  
  `cyfrin/escrow.md`
- 🟡 **RewardHandler` may revert due to receiving less than expected**  
  `cyfrin/parallel3.1.md`
- 🟡 **Same wallet can be added multiple times to an investor, artificially increasing their wallet count causing adding new wallets to revert**  
  `cyfrin/registry.md`
- 🟡 **Unbounded `depositAddresses` can cause `CompliantDepositRegistry::challengeLatestBatch` to revert due to out of gas**  
  `cyfrin/syntetika.md`
- 🟡 **Users can reset the status of their `firstPurchase` on the `referralData` when the `stablecoin` doesn't revert on transfers to `address(0)**  
  `cyfrin/final.md`

#### `revert-rewards` (14)

- 🟠 **Division by zero in rewards distribution can cause permanent lock of epoch rewards**  
  `cyfrin/core.md`
- 🟠 **Impossible to claim rewards when `XPTiers` are not set, resulting in permanently locked tokens once game has concluded**  
  `cyfrin/protocol.md`
- 🟡 **DefaultSession::assertResults` should revert if `proposedWinners`, `totalXPs` and `totalTimes` array lengths don't match**  
  `cyfrin/protocol.md`
- 🟡 **DepositManager::sponsorGame` should revert if the game is `Cancelled` or `Concluded**  
  `cyfrin/protocol.md`
- 🟡 **DividendManager::distributePayout` will always revert after 255 payouts, preventing any future payout distributions**  
  `cyfrin/pledge.md`
- 🟡 **Investor can prevent themselves from being removed by making `removeInvestor` revert**  
  `cyfrin/rebasing.md`
- 🟡 **Misleading revert message in onlyUser modifier**  
  `cyfrin/cooldown.md`
- 🟡 **RegistryService::addWallet` should revert if the wallet being added has positive balance of `DSToken**  
  `cyfrin/rebasing.md`
- 🟡 **Remove unused return value from `pUSDeVault::stakeUSDe` and explicitly revert if `USDeAssets == 0**  
  `cyfrin/predeposit.md`
- 🟡 **SessionManager::cancelGameIfCreatorMissing, endGame` could revert due to out of gas if there are too many question in a game**  
  `cyfrin/protocol.md`
- 🟡 **StakingVault::claimWithdraw` should revert if `assets` are zero**  
  `cyfrin/syntetika.md`
- 🟡 **StakingVault::distributeYield` should revert when there are no vault shares**  
  `cyfrin/syntetika.md`
- 🟡 **Swaps will revert when `A = B + Xhat - x = 0**  
  `cyfrin/angstrom.md`
- 🟡 **Wrong revert reason In `onSlash` functionality**  
  `cyfrin/core.md`

## oracle-pricing (11)
> Issues involving stale oracle data, timestamp manipulation, or price manipulation attacks.

### price-manipulation (3)

#### `manipulation-future` (3)

- 🔴 **Future epoch cache manipulation via `calcAndCacheStakes` allows reward manipulation**  
  `cyfrin/core.md`
- 🟡 **Hard-coded slippage in `pUSDeDepositor::deposit_viaSwap` can lead to denial of service**  
  `cyfrin/predeposit.md`
- 🟡 **User can set their answer's probability value to `uint16.max`, manipulating `result.probabilityAverage` in their favor**  
  `cyfrin/protocol.md`

### stale-data (8)

#### `timestamp-oracle` (8)

- 🟠 **Oracle void outcome leaves `PredictionMarketV3ManagerCLOB.voidedPayouts` unset, locking collateral**  
  `cyfrin/clob.md`
- 🟠 **Timestamp boundary condition causes reward dilution for active operators**  
  `cyfrin/core.md`
- 🟡 **Lack of on-chain oracle circuit breaker**  
  `sherlockPDFTXT/Tori Finance.txt`
- 🟡 **Missing event emissions for critical oracle parameter changes**  
  `cyfrin/stbl.md`
- 🟡 **Order expiration check uses inclusive bound so order remains valid at the expiration timestamp**  
  `cyfrin/clob.md`
- 🟡 **Remove redundant timestamp check in `Bet::resolve**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use timestamp instead of uri length to test of existing document in `DocumentManager**  
  `cyfrin/pledge.md`
- 🟡 **lastTotalAssets` stores stale value due to update before penalty accrual**  
  `cyfrin/pr50.md`

## token-transfer (40)
> Issues with ERC-20 token behaviour (fee-on-transfer, rebasing, burn) and cross-chain transfer accounting.

### cross-chain-accounting (4)

#### `bridge-receiver` (4)

- 🟠 **Hub Chain OverLayer Supply Reduction After OFT Transfers**  
  `HackenPDFTXT/Overlayer.txt`
- 🟡 **Pause modifier in bridge receiver functions causes receiver failures for in-flight messages**  
  `cyfrin/bridge.md`
- 🟡 **Settlement of liabilities and obligations lacks optimization for priority repayment, leading to accumulation of unpaid negative yield in the system**  
  `cyfrin/manager.md`
- 🟡 **depositTokenFromContract Cannot Pay Bridge Fees**  
  `HackenPDFTXT/Dexalot.txt`

### erc20-edge-cases (36)

#### `token-transfer` (20)

- 🔴 **Inverted isDirect Flag Logic Causes ERC20 Tokens to Not Be**  
  `HackenPDFTXT/Dexalot.txt`
- 🟠 **Delegate Spending Cap Bypass via Token Selection Allows**  
  `HackenPDFTXT/Fabstir.txt`
- 🟠 **More value can be extracted by liquidations than expected due to incorrect transfer calculations when the violator does not own the total ERC-6909 supply for each `tokenId` enabled as collateral**  
  `cyfrin/vii.md`
- 🟠 **Not all reward token rewards are claimable**  
  `cyfrin/core.md`
- 🟠 **Token Pricing Assumes All Payment Tokens Have Same**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **BetFactory::setPool` should validate input pool is legitimate AaveV3 pool and supports input token**  
  `cyfrin/wannabetv2.md`
- 🟡 **Expired Tokens Permanently Locked Due to Burn Restriction**  
  `HackenPDFTXT/S3 Markets.txt`
- 🟡 **InvestmentManager can use `AccountableFixedTerm::coverDefault` to misuse token approvals from anyone**  
  `cyfrin/accountable.md`
- 🟡 **Missing `Unstaked` event for immediate unstake in `UnstakeCooldown::transfer**  
  `cyfrin/tranches.md`
- 🟡 **Missing validation allows `userDeviation > burnRatioDeviation`, silently disabling burn ratio protection**  
  `cyfrin/parallel3.1.md`
- 🟡 **Native token prizes cannot be funded due to missing `receive()` function**  
  `cyfrin/spingame.md`
- 🟡 **Native token transfers lack explicit balance check**  
  `cyfrin/spingame.md`
- 🟡 **Pocket::execWithValue` does not emit native transfer event**  
  `cyfrin/update.md`
- 🟡 **Possibility of Burning Incorrect Token Because of Mutable**  
  `HackenPDFTXT/RYT-2.txt`
- 🟡 **Redundant balance check in safeTransferFrom before calling underlying transfer function**  
  `cyfrin/rwasegwrap.md`
- 🟡 **TokenBank::withdrawFunds` resets `memory` not `storage` fee and sale amounts allowing multiple withdraws for the same token**  
  `cyfrin/pledge.md`
- 🟡 **Unlimited token reallocation power creates centralization risk**  
  `cyfrin/wlf.md`
- 🟡 **Unvalidated Market Address Leads To Arbitrary Token**  
  `HackenPDFTXT/Dirol.txt`
- 🟡 **Unverified `_receiver` can cause irrecoverable token loss**  
  `cyfrin/yieldfi.md`
- 🟡 **proofInterval Validated as Token Count but Used as Seconds**  
  `HackenPDFTXT/Fabstir.txt`

#### `transfer-token` (16)

- 🔴 **Investors can steal tokens from other investors since `StandardToken::transferFrom` never checks spending approvals**  
  `cyfrin/rebasing.md`
- 🟠 **Funds Loss via Direct Transfer in CustodyVault**  
  `HackenPDFTXT/S3 Markets.txt`
- 🟠 **Use of IERC20.transfer() Instead of**  
  `HackenPDFTXT/Fabstir.txt`
- 🟡 **Complete bypass of transfer restrictions on vault share token is possible**  
  `cyfrin/accountable.md`
- 🟡 **ERC20 zero amount transfer rejection**  
  `cyfrin/accountable.md`
- 🟡 **In `Bet::cancel` if one transfer reverts but the other succeeds, one users's tokens are permanently locked in the `Bet` contract**  
  `cyfrin/wannabetv2.md`
- 🟡 **In `RemoraToken::transfer`, `transferFrom` and `_exchangeAllowed` perform all checks for each user together in order to prevent unnecessary work**  
  `cyfrin/pledge.md`
- 🟡 **Missing Transfer Event for Taxed Amount Breaks ERC20**  
  `HackenPDFTXT/Knoxnet.txt`
- 🟡 **TokenBank::removeToken` reverts when token balance is zero, making it impossible to remove tokens from the `developments` array**  
  `cyfrin/pledge.md`
- 🟡 **Transfer Amount enforcer for ERC20 and Native transfers increase spend limit without checking actual transfers**  
  `cyfrin/DelegationFramework1.md`
- 🟡 **Unsafe ERC20 operations can cause unexpected failures with non-standard tokens**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Use `SafeERC20` functions instead of standard ERC20 functions**  
  `cyfrin/wannabetv2.md`
- 🟡 **Use `SafeERC20` functions instead of standard `ERC20` transfer functions**  
  `cyfrin/pledge.md`
- 🟡 **Zero token transfers record receiving user as a holder in `DividendManager::HolderStatus` even if they have zero token balance**  
  `cyfrin/pledge.md`
- 🟡 **burn` should delete `tokenURI` related data and emit `TokenUriUnpinned` event**  
  `cyfrin/cryptoart.md`
- 🟡 **pUSDeVault::maxMint` doesn't account for mint pausing, in violation of EIP-4626 which can break protocols integrating with `pUSDeVault**  
  `cyfrin/predeposit.md`

## upgrade-config (32)
> Issues in upgrade safety (proxy storage gaps, initialiser hygiene) and governance configuration.

### governance-config (5)

#### `parameter-validation` (5)

- 🟠 **Missing ownership validation of positions**  
  `sherlockPDFTXT/Vesu.txt`
- 🟡 **SablierBob::_unstakeFullAmountViaAdapter` should take `vault.adapter` as input parameter**  
  `cyfrin/escrow.md`
- 🟡 **Unnecessary `_msgSender()` call in `_resolveVaultId` when `caller` parameter is available**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Unused parameter in address validation modifier SecuritizeOffRamp::addressNonZero**  
  `cyfrin/bridge.md`
- 🟡 **Use event indexing for faster off-chain parameter lookup**  
  `cyfrin/registry.md`

### upgrade-safety (27)

#### `storage-upgradeable` (15)

- 🔴 **Consider wiping slot 177 on Linea `L2MessageService` after upgrade**  
  `cyfrin/upgrade.md`
- 🟡 **AtomicBatcher` uses placeholder ERC-7201 namespace**  
  `cyfrin/pr50.md`
- 🟡 **ComplianceServiceRegulated` and its parent `ComplianceServiceWhitelisted` uses a chain of `initializer` modifiers when calling the `initialize**  
  `cyfrin/rebasing.md`
- 🟡 **Disable initializers on upgradeable contracts**  
  `cyfrin/predeposit.md`
- 🟡 **ERC-7201 Storage Location Comment Does Not Match**  
  `HackenPDFTXT/Vechain Foundation.txt`
- 🟡 **Missing `notEmptyURI` modifier during initialization**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Missing storage gap in upgradeable parent contract causes storage slot collision risk**  
  `cyfrin/rwasegwrap.md`
- 🟡 **Missing storage gap on upgradeable base contracts**  
  `cyfrin/bridge.md`
- 🟡 **Missing zero address validation in initialize function**  
  `cyfrin/dstokenswap.md`
- 🟡 **Upgrade script deploys implementation but doesn't execute upgrade**  
  `cyfrin/update.md`
- 🟡 **Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collision**  
  `cyfrin/predeposit.md`
- 🟡 **Upgradeable contracts which are inherited from should use ERC7201 namespaced storage layouts or storage gaps to prevent storage collisions**  
  `cyfrin/accountable.md`
- 🟡 **Use unchained initializers instead**  
  `cyfrin/predeposit.md`
- 🟡 **rewardGrowthOutsideX128` is not correctly initialized in `PoolRewards::updateAfterLiquidityAdd**  
  `cyfrin/angstrom.md`
- 🟡 **setApprovalForAll()` function is double initialized in the child contract**  
  `cyfrin/rwasegwrap.md`

#### `initialization-vault` (6)

- 🟡 **Missing zero-address validation for burner address during initialization can break slashing**  
  `cyfrin/core.md`
- 🟡 **Proxy reuse without implementation check inside `UnstakeCooldown` leads to execution on outdated/vulnerable logic**  
  `cyfrin/tranches.md`
- 🟡 **Vault governor cannot upgrade target**  
  `sherlockPDFTXT/Vesu Vaults.txt`
- 🟡 **Vault initialization allows zero deposit limit with no ability to modify causing denial of service**  
  `cyfrin/core.md`
- 🟡 **liquidityProviderWallet` is not set during initialization**  
  `cyfrin/bridge.md`
- 🟡 **pancakeRouter and pancakePair Initialization Can Be**  
  `HackenPDFTXT/Node Meta.txt`

#### `initialize-default` (6)

- 🟡 **Don't initialize to default values**  
  `cyfrin/pledge.md`
- 🟡 **Don't initialize to default values**  
  `cyfrin/predeposit.md`
- 🟡 **Don't initialize to default values**  
  `cyfrin/registry.md`
- 🟡 **Don't initialize to default values in Solidity**  
  `cyfrin/syntetika.md`
- 🟡 **In Solidity don't initialize to default values**  
  `cyfrin/harbor.md`
- 🟡 **In Solidity don't initialize to default values**  
  `cyfrin/protocol.md`

## withdrawal-redeem (50)
> Issues that block or grief the withdrawal/redemption queue.

### queue-dos (50)

#### `withdrawal-requests` (14)

- 🟠 **Single reverting withdrawal can block the `BasisTradeVault` withdrawal queue**  
  `cyfrin/trade.md`
- 🟡 **APR Targets are not updated when withdrawal requests are sent to the `SharesCooldown` to reflect the change on NAVs caused by the charged fees for the withdrawal**  
  `cyfrin/cooldown.md`
- 🟡 **BasisTradeTailor` withdrawal request overwrite enables race conditions**  
  `cyfrin/update.md`
- 🟡 **DOS for certain scenarios depending on**  
  `sherlockPDFTXT/Vesu.txt`
- 🟡 **Direct YToken deposits can lock funds below minimum withdrawal threshold**  
  `cyfrin/yieldfi.md`
- 🟡 **Finalizing withdrawal requests on the `SharesCooldown` contract allows for third-parties to override user’s chosen output token**  
  `cyfrin/cooldown.md`
- 🟡 **Forced Withdrawal Flow Is Not Fully Censorship-Resistant**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Front-Running DoS on Batch Settlement via Rolling Hash**  
  `HackenPDFTXT/Dexalot.txt`
- 🟡 **Increase in coverage can lead to a grief attack causing a DoS for previous withdrawal requests**  
  `cyfrin/cooldown.md`
- 🟡 **Investors transferring all their balances among their wallets or self-transferring on the same wallet causes to incorrectly decrement the investor counters causing DoS for other investors transfers**  
  `cyfrin/rebasing.md`
- 🟡 **Lack of Limits and Delay in Forced Withdrawal Parameter**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Missing revert of LST withdrawal when `L1MessageService` balance is exactly equal to required value**  
  `cyfrin/manager.md`
- 🟡 **Pending Force Withdrawal Requests Removed On Balance**  
  `HackenPDFTXT/BullBit.txt`
- 🟡 **Withdrawal queue `RequestPrice` can be front run in case of defaults**  
  `cyfrin/accountable.md`

#### `rewards-block` (14)

- 🔴 **Critical DOS in queue processing if async cancellations are allowed**  
  `cyfrin/accountable.md`
- 🔴 **Dust limit attack on `forceUpdateNodes` allows DoS of rebalancing and potential vault insolvency**  
  `cyfrin/core.md`
- 🔴 **Transfer/Approval Bypass and DoS Due To Missing**  
  `HackenPDFTXT/Panini America.txt`
- 🟡 **Allowance-Based Withdrawals Can Revert Due to Cooldown Request Slot Limits**  
  `cyfrin/cooldown.md`
- 🟡 **Burn and seize functions can be DoS when investor has several wallets that they control**  
  `cyfrin/rebasing.md`
- 🟡 **DoS via Concurrent Joint Contributor Invites**  
  `HackenPDFTXT/RYT.txt`
- 🟡 **Oracle Inconsistency between surplus computation and post-check causes `Surplus::processSurplus(collateralAddress,0)` DoS**  
  `cyfrin/parallel3.1.md`
- 🟡 **Premature zeroing of epoch rewards in `claimUndistributedRewards` can block legitimate claims**  
  `cyfrin/core.md`
- 🟡 **Rewards distribution DoS due to uncached secondary asset classes**  
  `cyfrin/core.md`
- 🟡 **Rewards system DOS due to unchecked asset class share and fee allocations**  
  `cyfrin/core.md`
- 🟡 **SettersGovernor::setWhitelistStatus` allows values other than 0 and 1 potentially leading to DOS**  
  `cyfrin/parallel3.1.md`
- 🟡 **Use unchecked block for increment operations in `distributeRewards**  
  `cyfrin/core.md`
- 🟡 **YieldManager::unpauseStaking` uses stale `lstLiabilityPrincipal` causing DoS when external actor repays LST liability**  
  `cyfrin/manager.md`
- 🟡 **report(...) may be vulnerable to DoS**  
  `sherlockPDFTXT/Vesu Vaults.txt`

#### `redeem-function` (11)

- 🟡 **All swaps other than the top-of-block swap will revert**  
  `cyfrin/angstrom.md`
- 🟡 **DoS of meta vault withdrawals during points phase if one vault is paused or attempted redemption exceeds the maximum**  
  `cyfrin/predeposit.md`
- 🟡 **Frontrunning to Block Junior Tranche Withdrawals**  
  `cyfrin/tranches.md`
- 🟡 **Function `execute` overwrites seenSigner values irrespective of request age**  
  `cyfrin/pr50.md`
- 🟡 **MetaVault::redeem` erroneously calls `ERC4626Upgradeable::withdraw` when attempting to redeem `USDe` from `pUSDeVault**  
  `cyfrin/predeposit.md`
- 🟡 **Missing  `redeem` convenience function in the `StakingVault.sol**  
  `cyfrin/syntetika.md`
- 🟡 **Remove `from` parameter from `Minter:redeem` and `_onlySender` function**  
  `cyfrin/syntetika.md`
- 🟡 **Revert if `StakingVault::deposit, mint, redeem, withdraw` would return zero**  
  `cyfrin/syntetika.md`
- 🟡 **SharesCooldown` instant finalization can be DoSed because of the `UnstakeCooldown` request limits**  
  `cyfrin/cooldown.md`
- 🟡 **SherpaVault::redeem` naming ambiguous**  
  `cyfrin/sherpa.md`
- 🟡 **Tranche::redeem` calls `super.withdraw` instead of `super.redeem` causing users to receive fewer assets**  
  `cyfrin/tranches.md`

#### `accountableopenterm-withdrawals` (11)

- 🟠 **Mechanism to prevent donation attack can be gamed to cause withdrawals to revert causing assets to get stuck on the Strategy**  
  `cyfrin/tranches.md`
- 🟠 **PaymentSettler` can change `stablecoin` but `RemoraToken` can't resulting in corrupted state with DoS for core functions**  
  `cyfrin/pledge.md`
- 🟡 **Cancelling a later-batch request in `AccountableOpenTerm` can delay earlier withdrawals**  
  `cyfrin/pr50.md`
- 🟡 **Delinquency status update in `AccountableOpenTerm` hooks uses pre-queue state**  
  `cyfrin/pr50.md`
- 🟡 **Fees can become stuck in `UniswapV4Wrapper**  
  `cyfrin/vii.md`
- 🟡 **In `pUSDeDepositor::deposit_viaSwap`, using `block.timestamp` in swap deadline is not very effective**  
  `cyfrin/predeposit.md`
- 🟡 **Inability to remove and redeem from vaults with withdrawal issues could result in a bank-run**  
  `cyfrin/predeposit.md`
- 🟡 **Increasing `AccountableOpenTerm.loan.withdrawalPeriod` from `0` can cause withdrawals to become stuck**  
  `cyfrin/pr50.md`
- 🟡 **Negative yield never accounted in `YieldManager::_getTotalSystemBalance` can result in temporary DoS**  
  `cyfrin/manager.md`
- 🟡 **Vester template misconfiguration can potentially block token claims**  
  `cyfrin/wlf.md`
- 🟡 **feeAmount` never set when no vault adapter used in `SablierBob::redeem**  
  `cyfrin/escrow.md`
