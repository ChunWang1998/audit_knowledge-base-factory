# auth/operational-security - Issues

- Count: 2

## F-2026-15280 - Hardcoded Private Key Exposure in Test Scripts Enables Unauthorized Account Control
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
Private keys were embedded in repository test scripts, which constitutescredential exposure and enables full signing authority over thecorresponding externally owned accounts. Since both derived addresseswere observed with on-chain activity in October 2025, the exposurecannot be treated as purely synthetic test data and must be considered anoperational security incident until key rotation and usage invalidation areconfirmed. The integration/example JavaScript tests instantiate wallets from literalprivate-key constants, creating recoverable signing credentials in sourcecontrol history. Representative pattern (redacted): // Wallets const userWallet = new ethers.Wallet('<`REDACTED_PRIVATE_KEY`>', provider); const hostWallet = new ethers.Wallet('<`REDACTED_PRIVATE_KEY`>', provider); Affected locations include: tests/integration/usdc-payment-flow.jstests/integration/usdc-complete-cycle.jstests/examples/usdc-job-parsing-example.js Derived addresses: 0x8D64…..4bF6 0x4594…..4504 Risk mechanism: Any actor with repository access can derive the same accounts andproduce valid signatures.If the same credentials were reused in deployment pipelines,operational wallets, relayers, or privileged off-chain services,unauthorized transactions and state changes could be executed.Exposure persists in Git history even after file-level replacement,unless history rewrite and coordinated secret revocation areperformed. If key reuse occurred in any operational context, unauthorized actors couldexecute transactions, impersonate trusted signers, and transfer controlledassets; even where current deployment usage is dismissed and keys arerotated, historical leakage preserves residual risk until complete revocationvalidation and dependency rotation are finalized. 59 Found in commit: f614355. Status: Fixed

### 修補方式（建議）
Immediate revocation/retirement of all exposed keypairs should beenforced.Verification should be completed that no deployment, relayer,automation job, CI secret, or production environment references theexposed addresses.Fresh keys should be generated through secure entropy sources andisolated per environment (dev/test/staging/prod) with strict non-reusepolicy.Secret material should be loaded from secure secret managers orenvironment injection, never from literals in source code.Repository and CI secret-scanning controls should be enabled (pre-commit and pipeline) to block future commits containing private-keypatterns. Resolution: Hardcoded private keys have been replaced with environment variablereferences across all affected test scripts; however, the original keyspersist in Git history and the associated accounts should be consideredpermanently compromised — key rotation and fund migration are stillrequired. Revised commit: df1f2e4. 60

### 修補方式（實際）
Hardcoded private keys have been replaced with environment variablereferences across all affected test scripts; however, the original keyspersist in Git history and the associated accounts should be consideredpermanently compromised — key rotation and fund migration are stillrequired. Revised commit: df1f2e4. 60

## F-2025-14485 - Lack of Limits and Delay in Forced Withdrawal Parameter Updates - Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The InclusionQueue contract enables the creation of forced withdrawalrequests originating from the Vault and Pool contracts. These requests arelater consumed by the verifier contract to finalize withdrawals. Duringrequest creation, a fee equal to the feeAmount variable must be paid. Thisfee is not deducted from the internally deposited balance, requiring theavailability of additional externally held assets. The setAmount() function is responsible for updating both minWithdrawAmount and feeAmount. This function is protected by the onlyOwner modifier.However, several design shortcomings introduce risk and negatively affectthe withdrawal process. function setAmount(uint256 _minWithdrawAmount, uint256 _feeAmount) external o nlyOwner { require(_minWithdrawAmount > 0, "Queue: 0 min amount"); minWithdrawAmount = _minWithdrawAmount; feeAmount = _feeAmount; } First, no reasonable upper bounds are enforced for either parameter. As aresult, minWithdrawAmount can be set to excessively high values, potentiallypreventing withdrawals of smaller deposits or blocking withdrawalsentirely. Similarly, feeAmount can be set to arbitrarily large values, requiringdisproportionately high external assets to

### 修補方式（實際）
The BullBit team implemented upper bounds for feeAmount and minWithdrawAmount and a time-lock mechanism is integrated to reflectchanges in commit 322258e. 32

## Cyfrin Fixed Issues (Merged)
- Count: `2`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] Market pause flag not enforced by `Conditional Tokens::split Position`
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** `PredictionMarketV3ManagerCLOB::pauseMarket` sets a per-market `paused` flag. The exchange respects this via `_requireMarketOpen` -> `manager.isMarketPaused`. However, `ConditionalTokens::splitPosition` checks only the market state, not the pause flag:

```solidity
// ConditionalTokens.sol:34
require(manager.getMarketState(marketId) == IMyriadMarketManager.MarketState.open, "market not open");
// isMarketPaused is never checked
```

Any user can call `ConditionalTokens::splitPosition` directly to acquire fresh YES/NO tokens on a market the admin intended to freeze, bypassing the pause entirely. During an incident pause (e.g. ahead of an emergency void), new exposure can still be created.

**Recommended Mitigation:** Add a pause guard to `ConditionalTokens::splitPosition`:

```solidity
require(!manager.isMarketPaused(marketId), "market paused");
```

**Myriad:** Fixed in commit [`8be2650`](https://github.com/Polkamarkets/polkamarkets-js/commit/8be265059802e5e1e79bca4286d17616be90c47f)

**Cyfrin:** Verified.

## [M-2] Inconsistent pause functionality allows certain state-changing operations when contract is paused
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The `CryptoartNFT` contract implements a pause mechanism using OpenZeppelin's `PausableUpgradeable` contract. However, the pause functionality is inconsistently applied across the contract's functions. While minting and burning operations are properly protected with the `whenNotPaused` modifier, several other state-changing functions remain accessible even when the contract is paused, including token transfers, metadata management, and story-related functions.

The following state-changing functions lack the `whenNotPaused` modifier:

1. Token transfers and approvals (inherited from ERC721)
2. Metadata management functions:
   - `updateMetadata`
   - `pinTokenURI`
   - `markAsRedeemable`
3. Story-related functions:
   - `addCollectionStory`
   - `addCreatorStory`
   - `addStory`
   - `toggleStoryVisibility`

**Impact:** When the contract is paused (typically during emergencies or upgrades), users can still perform various state-changing operations that might be undesirable during a pause period. It could lead to unexpected state changes during contract upgrades or emergency situations.

**Recommended Mitigation:** Add the `whenNotPaused` modifier to all state-changing functions to ensure consistent behavior when the contract is paused. For example:

**Cryptoart:**
Fixed in commit [e7d7e5b](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/e7d7e5b3b1c8976a11d49f889b4168ce649be2ee).

**Cyfrin:** Verified.

\clearpage

<!-- /Cyfrin Fixed Issues (Merged) -->

## [M-46] Deployment script requires unencrypted private keys
- Severity: `Medium`
- Source report: `trade.md`

### Detailed Content (from source)
**Description:** Several deployment/ops scripts require private keys to be loaded from environment variables and used directly inside the script, e.g.:

```solidity
// DeployBasisTradeTailor.s.sol
uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
uint256 adminPrivateKey    = vm.envUint("ADMIN_PRIVATE_KEY");
...
vm.startBroadcast(deployerPrivateKey);
...
vm.startBroadcast(adminPrivateKey);

// DeployBasisTradeVault.s.sol
uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
...
vm.startBroadcast(deployerPrivateKey);

// DeployMockPocketOracle.s.sol
uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
...
vm.startBroadcast(deployerPrivateKey);

// DeployMocks.s.sol
uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
...
vm.startBroadcast(deployerPrivateKey);
```

Storing and loading raw private keys via `.env` (plain text) is an operational security risk: keys can be leaked through version control, logs, shell history, misconfigured backups, or compromised developer machines/CI runners.

A safer approach is to avoid embedding keys in scripts and use Foundry’s [wallet management](https://getfoundry.sh/forge/reference/script/) and keystore support. Recommended pattern:

1. Import keys into an encrypted local keystore (once per machine) using [`cast`](https://getfoundry.sh/cast/reference/wallet/import/):

```bash
cast wallet import deployerKey --interactive
cast wallet import adminKey --interactive
cast wallet import agentKey --interactive   # if needed
```

2. Change scripts to use parameterless broadcasting so the signer is supplied by CLI:

```solidity
// before: vm.startBroadcast(deployerPrivateKey);
vm.startBroadcast();
// ...
vm.stopBroadcast();
```

3. Run each role-sensitive phase as the appropriate account (split into separate runs or separate scripts if different signers are required):

```bash
# Deployer phase
forge script script/DeployBasisTradeTailor.s.sol:DeployBasisTradeTailor \
  --rpc-url "$RPC_URL" --broadcast --account deployerKey --sender <deployer_addr> -vvv

# Admin phase (grants/approvals)
forge script script/ConfigureBasisTradeTailor.s.sol:ConfigureBasisTradeTailor \
  --rpc-url "$RPC_URL" --broadcast --account adminKey --sender <admin_addr> -vvv
```

This keeps private keys encrypted at rest and never exposes them via plaintext environment variables. As alternatives, consider hardware wallets (`--ledger`), and ensure `.env` never contains raw keys in shared environments.

For additional guidance, see [this explanation video](https://www.youtube.com/watch?v=VQe7cIpaE54) by Patrick.

**Button:** Fixed in commit [`c89bce0`](https://github.com/buttonxyz/button-protocol/commit/c89bce0f88770f473524e997eb47fca7dccae0e0)

**Cyfrin:** Verified. Keystores are now used for the keys.

## [M-5] Deployment script requires unencrypted private key
- Severity: `Medium`
- Source report: `accountable.md`

### Detailed Content (from source)
**Description:** The deployment scripts [`FactoryScript.s.sol`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/script/FactoryScript.s.sol) and [`FeeManagerScript.s.sol`](https://github.com/Accountable-Protocol/audit-2025-09-accountable/blob/fc43546fe67183235c0725f6214ee2b876b1aac6/script/FeeManagerScript.s.sol) requires a private key to be stored in clear text as an environment variable:

```solidity
uint256 deployerPk = vm.envUint("DEPLOYER_TESTNET_PK");
```

Storing private keys in plain text represents an operational security risk, as it increases the chance of accidental exposure through version control, misconfigured backups, or compromised developer machines.

A more secure approach is to use Foundry’s [wallet management features](https://getfoundry.sh/forge/reference/script/), which allow encrypted key storage. For example, a private key can be imported into a local keystore using [`cast`](https://getfoundry.sh/cast/reference/wallet/import/):

```bash
cast wallet import deployerKey --interactive
```

This key can then be referenced securely during deployment:

```bash
forge script script/Deploy.s.sol:DeployScript \
    --rpc-url "$RPC_URL" \
    --broadcast \
    --account deployerKey \
    --sender <address associated with deployerKey> \
    -vvv
```
And used just with `vm.startBroadcast()`:
```solidity
vm.startBroadcast();

...

vm.stopBroadcast();
```

For additional guidance, see [this explanation video](https://www.youtube.com/watch?v=VQe7cIpaE54) by Patrick.

**Accountable:** Fixed in commit [`79d8cfd`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/79d8cfd8dee652adb0964ade05280a745cedb3b3)

**Cyfrin:** Verified. Deploy scripts now don't require a private key in clear text.

\clearpage
