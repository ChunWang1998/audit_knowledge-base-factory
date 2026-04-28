# bridge/cross-chain-core - Issues

- Count: 2

## F-2026-14991 - depositTokenFromContract Cannot Pay Bridge Fees
- 嚴重度：Medium
- Report source：Dexalot.pdf

### 問題內容（完整）
The depositTokenFromContract function is used by trusted contracts to deposittokens on behalf of users. Following the v2.6.3 upgrade, the deposit flownow requires native bridge fees to be paid via `msg.value`, which isforwarded to portfolioBridge.sendXChainMessage{value: `_nativeBridgeFee`}(…). However, depositTokenFromContract is not payable and does not forward anyvalue when calling depositToken: function depositTokenFromContract(address `_from`, bytes32 `_symbol`, uint256 `_qu` antity) external override { require(trustedContracts[`msg.sender`], "P-`AOTC`-01"); this.depositToken(`_from`, `_symbol`, `_quantity`, portfolioBridge.getDefaultBri `dgeProvider()`); } When depositToken is subsequently called: `msg.value` will be 0 The internal deposit function will call portfolioBridge.sendXChainMessage{value: 0}(…) If the bridge provider requires a fee (userPaysFee returns true), thetransaction will fail This may lead to: Breaking existing integrations: Trusted contracts that previouslyused depositTokenFromContract will fail when bridge fees are enabled forthe default bridge providerDenial of Service for trusted contracts: Trusted integrations cannotcomplete depositsInconsistent behavior: Direct calls to depositToken can pay fees, butcalls via depositTokenFromContract cannot Assets: `contracts/PortfolioMain.sol`[https://github.com/Dexalot/contracts/commits/omnivaults/] Status: Fixed

### 修補方式（建議）
Make depositTokenFromContractpayable and forward the value to depositToken. Resolution: Fixed in fbe76ba: The issue has been resolved by making the following changes to the depositTokenFromContract function: Addedpayablemodifier: The function now accepts native currencyvia `msg.value`, allowing trusted contracts to include bridge fees withtheir deposit calls. Forwardmsg.valuetodepositToken: The internal call to depositToken nowincludes {value: `msg.value`}, ensuring that any native bridge fees sentby the trusted contract are properly forwarded through the depositflow to portfolioBridge.sendXChainMessage. function depositTokenFromContract(address `_from`, bytes32 `_symbol`, uint256 `_qu` antity) external payable override { require(trustedContracts[`msg.sender`], "P-`AOTC`-01"); this.depositToken{value: `msg.value`}(`_from`, `_symbol`, `_quantity`, portfolioB `ridge.getDefaultBridgeProvider()`); } 30

### 修補方式（實際）
Fixed in fbe76ba: The issue has been resolved by making the following changes to the depositTokenFromContract function: Addedpayablemodifier: The function now accepts native currencyvia `msg.value`, allowing trusted contracts to include bridge fees withtheir deposit calls. Forwardmsg.valuetodepositToken: The internal call to depositToken nowincludes {value: `msg.value`}, ensuring that any native bridge fees sentby the trusted contract are properly forwarded through the depositflow to portfolioBridge.sendXChainMessage. function depositTokenFromContract(address `_from`, bytes32 `_symbol`, uint256 `_qu` antity) external payable override { require(trustedContracts[`msg.sender`], "P-`AOTC`-01"); this.depositToken{value: `msg.value`}(`_from`, `_symbol`, `_quantity`, portfolioB `ridge.getDefaultBridgeProvider()`); } 30

## F-2026-15250 - Hub Chain OverLayer Supply Reduction After OFTTransfers Lead to supply() DoS
- 嚴重度：High
- Report source：Overlayer.pdf

### 問題內容（完整）
The OverlayerWrap token supports LayerZeroʼs `OFT` standard, allowingcross-chain transfers between supported networks (currently: Ethereum<> Base). Under the `OFT` model, bridging is implemented via burn-on-source / mint-on-destination (and vice versa), which preserves the globalsupply across chains but changes the `totalSupply()` value on any singlechain depending on how much liquidity has migrated. OverlayerWrap is minted 1 1 upon collateral deposits. The protocol canthen supply deposited collateral to Aave via AaveHandler::`supply()` to startgenerating yield: function `supply( uint256 amountCollateral_, address collateralToken_ )` external onlyProtocol nonReentrant { //… supply functionality // Do not count donations to overlayerWrap: compute how much we have to i ncrease our supply counters. // We cannot exceed the overlayerWrap supply. uint256 owTotalSupp = `IOverlayerWrap(overlayerWrap)`.`totalSupply()`; if (owTotalSupp < `DECIMALS_DIFF_AMOUNT`) revert `AaveHandlerOverlayerWrapTotalSupplyTooLow()`; // Total supply cannot be less than total supplied collateral as ow token is not burnable uint256 normalizedSupply = owTotalSupp / `DECIMALS_DIFF_AMOUNT`; uint256 differenceCollateral = normalizedSupply - totalSuppliedCollateral; uint256 minIncrease = `Math.min(amountCollateral_, differenceCollateral)`; totalSuppliedCollateral += minIncrease; emit `AaveSupply(minIncrease)`; } The accounting logic assumes that the hub-chain OverlayerWrap::`totalSupply()` is monotonically non-decreasing (or at leastnever falls below the tracked totalSuppliedCollateral). This assumption isexplicitly reflected in the inline comment (“ow token is not burnable”).However, this assumption is invalid for an `OFT` token: cross-chaintransfers burn tokens on the source chain, which can reduce `totalSupply()` on the hub chain. 14 As a result, the normalizedSupply can become less than totalSuppliedCollateral. In Solidity ≥ 0.8, the subtraction differenceCollateral = normalizedSupply - totalSuppliedCollateral; will underflow and revert. Oncethis condition is reached, `supply()` becomes permanently unusable (untilsupply returns), creating a denial of service on the Aave supply path. If totalSuppliedCollateral > normalizedSupply due to hub-chain supplydecreasing after `OFT` transfers, `supply()` will revert due to arithmeticunderflow. This prevents newly deposited (or previously unsupplied)collateral from being supplied to Aave, breaking the protocolʼs yield-generation workflow. This creates a protocol-level Denial of Service condition for the yield-supply path: `supplyToBacking()`/`supply()` can become non-functional after sufficientcross-chain transfers (if some inactive or inaccessible wallets did nottransfer token back to source chain – it becomes permanent)Newly deposited collateral (or collateral not yet supplied) may becomeimpossible to supply to Aave, preventing yield generation.Collateral remaining idle instead of earning yield.The protocol can become operationally inefficient and fail to deliver itsintended yield-backed design, degrading user trust and potentiallyimpacting economic assumptions across the system. Assets: `contracts/overlayerbacking/AaveHandler.sol`[https://github.com/Overlayerfi/contracts/tree/main] Status: Fixed

### 修補方式（建議）
Revise the AaveHandler::`supply()` delta calculation for updating totalSuppliedCollateral so it is resilient to `OFT` burn/mint behavior andcannot underflow due to cross-chain supply changes. 15 Resolution: Fixed in f55efce, the bridged supply is now stored separately in the totalBridgedOut variable. The `supply()` function now checks not only `totalSupply()`, but also the bridged amount, to ensure the total suppliedamount remains consistent: uint256 owTotalSupp = `IOverlayerWrap(overlayerWrap)`.`totalSupply()` + `IOverlayerWrap(overlayerWrap)`.`totalBridgedOut()`;

### 修補方式（實際）
Fixed in f55efce, the bridged supply is now stored separately in the totalBridgedOut variable. The `supply()` function now checks not only `totalSupply()`, but also the bridged amount, to ensure the total suppliedamount remains consistent: uint256 owTotalSupp = `IOverlayerWrap(overlayerWrap)`.`totalSupply()` + `IOverlayerWrap(overlayerWrap)`.`totalBridgedOut()`;

## Cyfrin Fixed Issues (Merged)
- Count: `50`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [C-1] Missing `onlyInitializing` modifier on initialization functions for abstract contracts
- Severity: `Critical`
- Source report: `upgrade.md`

### Detailed Content (from source)
**Description:** The `onlyInitializing` modifier is the established standard for protecting internal initialization functions in abstract contracts against unintended calls post-initialization. These new initialization functions introduced here do not include this modifier, which deviates from common security patterns:
* `L2MessageServiceBase::__L2MessageService_init`
* `LineaRollupBase::__LineaRollup_init`
* `TokenBridgeBase::__TokenBridge_init`

**Recommended Mitigation:** Consider adding the `onlyInitializing` modifier to those functions.

**Linea:** Fixed in commits [802cf72](https://github.com/Consensys/linea-monorepo/pull/2007/commits/802cf7239754526861e1e8777380619e8bc39cf2), [2d63895](https://github.com/Consensys/linea-monorepo/commit/2d638959adec0c13f66d72bb6c44b16f7df4bea1).

**Cyfrin:** Verified.

## [C-2] All CCIP messages reverts when decoded
- Severity: `Critical`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** YieldFi has integrated Chainlink CCIP alongside its existing LayerZero support to enable cross-chain token transfers using multiple messaging protocols. To support this, a custom message payload is used to indicate the token transfer. This payload is decoded in [`Codec::decodeBridgeSendPayload`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/libs/Codec.sol#L22-L51) as follows:
```solidity
(uint32 dstId, address to, address token, uint256 amount, bytes32 trxnType) = abi.decode(_data, (uint32, address, address, uint256, bytes32));
```
This same decoding logic is reused for CCIP message processing.

However, Chainlink uses a `uint64` for `dstId`, and their chain IDs (e.g., [Ethereum mainnet](https://docs.chain.link/ccip/directory/mainnet/chain/mainnet)) all exceed the `uint32` range. For instance, Ethereum’s CCIP chain ID is `5009297550715157269`, which is well beyond the limits of `uint32`.

**Impact:** All CCIP messages will revert during decoding due to the overflow when casting a `uint64` value into a `uint32`. Since the contract is not upgradeable, failed messages cannot be retried, resulting in permanent loss of funds—tokens may be either locked or burned depending on the sending logic.

**Proof of Concept:** Attempting to process a message with `dstId = 5009297550715157269` in the `CCIP Receive: Should handle received message successfully` test causes the transaction to revert silently. The same behavior is observed when manually decoding a 64-bit value as a 32-bit integer using Remix.

**Recommended Mitigation:** Consider updating the type of `dstId` to `uint64` to match the Chainlink format. This change should be safe, as `dstId` is not used after decoding in the current LayerZero integration.

**YieldFi:** Fixed in commit [`14fc17a`](https://github.com/YieldFiLabs/contracts/commit/14fc17a46702bf0db0efb199c48e52530221612b)

**Cyfrin:** Verified. `dstId` is now a `uint64` in `Codec.BridgeSendPayload`.

\clearpage
## High Risk

## [C-3] Missing source validation in CCIP message handling
- Severity: `Critical`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** YieldFi integrates with Chainlink CCIP to facilitate cross-chain transfers of its yield tokens (`YToken`). This functionality is handled by the `BridgeCCIP` contract, which manages token accounting for these transfers.

However, in the [`BridgeCCIP::_ccipReceive`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L160-L181) function, there is no validation of the message sender from the source chain:
```solidity
/// handle a received message
function _ccipReceive(Client.Any2EVMMessage memory any2EvmMessage) internal override {
    bytes memory message = abi.decode(any2EvmMessage.data, (bytes)); // abi-decoding of the sent text
    BridgeSendPayload memory payload = Codec.decodeBridgeSendPayload(message);
    bytes32 _hash = keccak256(abi.encode(message, any2EvmMessage.messageId));
    require(!processedMessages[_hash], "processed");

    processedMessages[_hash] = true;

    require(payload.amount > 0, "!amount");

    ...
}
```

As a result, an attacker could craft a malicious `Any2EVMMessage` containing valid data and trigger the minting or unlocking of arbitrary tokens by sending it through CCIP to the `BridgeCCIP` contract.


**Impact:** An attacker could drain the bridge of tokens on L1 or mint an unlimited amount of tokens on L2. While a two-step redeem process offers some mitigation, such an exploit would still severely disrupt the protocol’s accounting and could be abused when claiming yield for example.

**Recommended Mitigation:** Consider implementing validation to ensure that messages are only accepted from trusted peers on the source chain:
```solidity
mapping(uint64 sourceChain => mapping(address peer => bool allowed)) public allowedPeers;
...
function _ccipReceive(
    Client.Any2EVMMessage memory any2EvmMessage
) internal override {
    address sender = abi.decode(any2EvmMessage.sender, (address));
    require(allowedPeers[any2EvmMessage.sourceChainSelector][sender],"allowed");
    ...
```

**YieldFi:** Fixed in commit [`a03341d`](https://github.com/YieldFiLabs/contracts/commit/a03341d8103ba08473ea1cd39e64192608692aca)

**Cyfrin:** Verified. `sender` is now verified to be a trusted sender.

## [M-4] Missing storage gap on upgradeable base contracts
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The contract `/contracts/utils/BaseContract` of `bc-securitize-bridge-sc` repository is upgradeable (inherits from `UUPSUpgradeable`, `OwnableUpgradeable`, and `PausableUpgradeable`) but does not include a storage gap.

Storage gaps are essential for ensuring that new state variables can be added to the base contracts in future upgrades without affecting the storage layout of inheriting child contracts.

**Impact:** Any addition of new state variables in future versions of `BaseContract` can lead to storage collisions in the children contracts.

**Recommendation:**
Add a storage gap to the `BaseContract`.
```solidity
uint256[50] private __gap;
```

**Securitize:** Fixed in commit [1da35c](https://bitbucket.org/securitize_dev/bc-securitize-bridge-sc/commits/1da35cde31a53e7b2de56de0d313ebdcb80cbfa3).

**Cyfrin:** Verified.

## [M-5] Pause modifier in bridge receiver functions causes receiver failures for in-flight messages
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The `USDCBridge::receivePayloadAndUSDC` and `SecuritizeBridge::receiveWormholeMessages` functions are protected by the `whenNotPaused` modifier, which causes these functions to revert when the respective bridge contracts are paused. According to the [Wormhole documentation](https://wormhole.com/docs/products/messaging/guides/wormhole-relayers/#delivery-statuses), when receiver functions revert, the message status becomes "Receiver Failure" and there is no automatic retry mechanism available. The only way to recover from receiver failures is to restart the entire process from the source chain.

```solidity
// USDCBridge.sol
function receivePayloadAndUSDC(
    bytes memory payload,
    uint256 amountUSDCReceived,
    bytes32 sourceAddress,
    uint16 sourceChain,
    bytes32 deliveryHash
) internal override onlyWormholeRelayer whenNotPaused {
    // Function will revert if contract is paused
    // ...
}

// SecuritizeBridge.sol
function receiveWormholeMessages(
    bytes memory payload,
    bytes[] memory additionalVaas,
    bytes32 sourceBridge,
    uint16 sourceChain,
    bytes32 deliveryHash
) public override payable whenNotPaused {
    // Function will revert if contract is paused
    // ...
}
```

This creates an operational issue where funds associated with in-flight messages become stuck without any built-in recovery mechanism provided by the bridge contracts.

The problematic scenario:
1. User initiates a cross-chain transfer from Chain A to Chain B
2. Bridge contract on Chain B gets paused due to an emergency or maintenance
3. Wormhole relayer attempts to deliver the message to Chain B
4. The receiver function reverts due to the `whenNotPaused` modifier
5. Message status becomes "Receiver Failure" permanently
6. Funds are stuck with no automatic recovery mechanism

**Impact:** Funds associated with in-flight cross-chain messages become stuck when bridge contracts are paused, requiring manual intervention to recover assets.

**Recommended Mitigation:** Remove the `whenNotPaused` modifier from receiver functions to prevent receiver failures.
Furthermore, consider tracking received messages with the receive process success flag and allow the admin to retry the failed messages.

**Securitize:** Partially fixed in commit [97e37b](https://bitbucket.org/securitize_dev/bc-securitize-bridge-sc/commits/97e37bed37168bc1ca73fb18f06fbae06161819d), `whenNotPaused` has been removed for the `USDCBridge` receive function.

**Cyfrin:** Verified.

## [M-6] Unnecessary override keywords on interface implementation functions
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** Multiple functions in the `SecuritizeOnRamp` contract use the `override` keyword unnecessarily. In Solidity, the `override` keyword is only required when overriding functions from parent contracts, not when implementing interface functions.

The following functions unnecessarily use the `override` keyword:
- `SecuritizeOnRamp::nonceByInvestor`
- `SecuritizeOnRamp::subscribe`
- `SecuritizeOnRamp::swap`
- `SecuritizeOnRamp::executePreApprovedTransaction`
- `SecuritizeOnRamp::calculateDsTokenAmount`
- `SecuritizeOnRamp::updateAssetProvider`
- `SecuritizeOnRamp::updateNavProvider`
- `SecuritizeOnRamp::updateMinSubscriptionAmount`
- `SecuritizeOnRamp::updateBridgeParams`
- `SecuritizeOnRamp::toggleInvestorSubscription`

**Impact:** The unnecessary `override` keywords create confusion about the contract's inheritance structure.

**Recommended Mitigation:** Remove the `override` keyword.

**Securitize:** Fixed in commit [bf7b87](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/bf7b873d62fd346493c5726ea0a0726088926136).

**Cyfrin:** Verified.

## [M-7] Unused library and struct definitions increase deployment costs and reduce code clarity
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The `CCTPMessageLib` library and `CCTPMessage` struct are defined but never used throughout the CCTP integration contracts. In `WormholeCCTPUpgradeable.sol`, the library defines a `CCTPMessage` struct containing `message` and `signature` fields, and the contract imports it with `using CCTPMessageLib for *`. However, the `CCTPBase::redeemUSDC` function manually decodes CCTP messages using `abi.decod
e(cctpMessage, (bytes, bytes))` instead of utilizing the defined struct.

```solidity
function redeemUSDC(bytes memory cctpMessage) internal returns (uint256 amount) {
    (bytes memory message, bytes memory signature) = abi.decode(cctpMessage, (bytes, bytes));
    uint256 beforeBalance = IERC20(USDC).balanceOf(address(this));
    circleMessageTransmitter.receiveMessage(message, signature);
    return IERC20(USDC).balanceOf(address(this)) - beforeBalance;
}
```

The same issue exists in the upstream wormhole SDK's `CCTPBase.sol` file, suggesting this may have been copied without proper cleanup.

**Impact:** The unused code increases deployment gas costs and reduces code maintainability without providing any functional benefit.

**Recommended Mitigation:** Remove the unused `CCTPMessageLib` library and the `using` statement from the contracts:

```diff
- library CCTPMessageLib {
-     struct CCTPMessage {
-         bytes message;
-         bytes signature;
-     }
- }

abstract contract CCTPSender is CCTPBase {
    uint8 internal constant CONSISTENCY_LEVEL_FINALIZED = 15;

-   using CCTPMessageLib for *;

    mapping(uint16 => uint32) public chainIdToCCTPDomain;
```

**Securitize:** Fixed in commit [97e37b](https://bitbucket.org/securitize_dev/bc-securitize-bridge-sc/commits/97e37bed37168bc1ca73fb18f06fbae06161819d).

**Cyfrin:** Verified.

## [M-8] Unused parameter in address validation modifier SecuritizeOffRamp::addressNonZero
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The `addressNonZero` modifier used in `SecuritizeOffRamp::initialize()`, `SecuritizeOffRamp::updateLiquidityProvider()`, and `SecuritizeOffRamp::updateNavProvider()` functions accepts a `string memory parameter` argument but never uses it within the modifier logic.
This parameter appears to be intended for providing context about which address parameter is being validated, but it remains unused in the error handling.

```solidity
modifier addressNonZero(address _address, string memory parameter) {
    if (_address == address(0)) {
        revert NonZeroAddressError();
    }
    _;
}
```

The modifier is called with descriptive strings like "asset", "navProvider", "feeManager", and "liquidityProvider" but this contextual information is not utilized in the error reporting or validation logic. For comparison, other contracts in the codebase use similar address validation modifiers without unused parameters, such as `addressNotZero` in `USDCBridge.sol` which correctly implements the validation without taking unnecessary parameters.

**Impact:** The unused parameter creates inconsistent code patterns and represents a missed opportunity to provide meaningful error context when address validation fails.

**Recommended Mitigation:** Remove the unused parameter from the `addressNonZero` modifier to maintain consistency with similar validation patterns in other contracts:

```diff
- modifier addressNonZero(address _address, string memory parameter) {
+ modifier addressNonZero(address _address) {
    if (_address == address(0)) {
        revert NonZeroAddressError();
    }
    _;
}
```

And update all usage sites to remove the string parameter:

```diff
- addressNonZero(_asset, "asset")
+ addressNonZero(_asset)
- addressNonZero(_navProvider, "navProvider")
+ addressNonZero(_navProvider)
- addressNonZero(_feeManager, "feeManager")
+ addressNonZero(_feeManager)
- addressNonZero(_liquidityProvider, "liquidityProvider")
+ addressNonZero(_liquidityProvider)
```

**Securitize:** Fixed in commit [fd5511](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/fd5511077e368ee1d84f2695fe67b77bb185d6a3).

**Cyfrin:** Verified.

## [M-9] Usage of unofficial wormhole-solidity-sdk npm package poses security and maintenance risks
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** The bridge contracts in the codebase are using `wormhole-solidity-sdk` version 0.9.0 from npm, which has been confirmed by the Wormhole team to be an unofficial deployment. According to the Wormhole team, the npm package published by `sullof <francesco@sullo.co>` is not their official release, and the only approved version is v0.1.0 available on GitHub. The official recommended approach is to use `forge install wormhole-foundation/wormhole-solidity-sdk@v0.1.0`.

The following contracts are affected by this issue:
- `SecuritizeBridge.sol` - imports `IWormholeReceiver` and `IWormholeRelayer`
- `WormholeCCTPUpgradeable.sol` - imports `IWormholeRelayer`, `IWormhole`, and `ITokenMessenger`
- `USDCBridge.sol` - inherits from `WormholeCCTPUpgradeable` via `CCTPSender` and `CCTPReceiver`
- `RelayerMock.sol` - imports `IWormholeRelayer`

The unofficial package is declared as a dependency in `package.json` with `"wormhole-solidity-sdk": "^0.9.0"` and is used throughout the bridge implementation for cross-chain message passing and CCTP (Circle Cross-Chain Transfer Protocol) functionality.

**Impact:** Using an unofficial SDK introduces potential security vulnerabilities, compatibility issues, and maintenance challenges as the codebase depends on unverified third-party code.

**Recommended Mitigation:** Replace the unofficial npm package with the official GitHub release.

**Securitize:** Fixed in commit [1da35c](https://bitbucket.org/securitize_dev/bc-securitize-bridge-sc/commits/1da35cde31a53e7b2de56de0d313ebdcb80cbfa3).

**Cyfrin:** Verified. We posted a [tweet](https://x.com/hansfriese/status/1945048296461848901) to alert others using the package, and the author replied, confirming it was intended solely for personal use, not for protocols. To prevent further confusion, the author has taken down the [package](https://x.com/sullof/status/1945490920809304324).

\clearpage

## [M-10] Use of `msg.sender` instead of `_msgSender()` prevents meta-transaction support
- Severity: `Medium`
- Source report: `bridge.md`

### Detailed Content (from source)
**Description:** Several contracts in the codebase use `msg.sender` directly instead of `_msgSender()`, which prevents proper meta-transaction support. This inconsistency affects both initialization and core functionality across the system.

The affected contracts and functions include:

- `BaseContract::__BaseContract_init()`
- `SecuritizeOffRamp::redeem()`
- `SecuritizeBridge::bridgeDSTokens()`
- `SecuritizeBridge::validateLockedTokens()`

The protocol properly uses `_msgSender()` in their other functions and access control patterns, indicating awareness of meta-transaction support, but this was not consistently applied across all functions.

When a user performs a meta-transaction through a trusted forwarder:
1. The forwarder calls the contract on behalf of the user
2. Functions using `msg.sender` receive the forwarder's address instead of the user's address
3. Validation, authorization, and business logic fail or operate incorrectly

**Impact:** Meta-transaction functionality is broken as the forwarder contract becomes the transaction sender instead of the intended user, potentially causing authorization failures, incorrect event emissions, and improper validation logic.

**Recommended Mitigation:** Replace all instances of `msg.sender` with `_msgSender()` to support meta-transactions:

```diff
// BaseContract.sol
function __BaseContract_init() internal onlyInitializing {
    __UUPSUpgradeable_init();
    __Pausable_init();
-   __Ownable_init(msg.sender);
+   __Ownable_init(_msgSender());
}

// SecuritizeOffRamp.sol
function redeem(uint256 assetAmount, uint256 minOutputAmount) external whenNotPaused nonZeroNavRate nonZeroLiquidityProvider {
    uint256 rate = navProvider.rate();

-   RedemptionValidator.validateRedemption(msg.sender, assetAmount, asset);
+   RedemptionValidator.validateRedemption(_msgSender(), assetAmount, asset);

-   CountryValidator.validateCountryRestriction(msg.sender, dsServiceConsumer, restrictedCountries);
+   CountryValidator.validateCountryRestriction(_msgSender(), dsServiceConsumer, restrictedCountries);

    // ... calculations ...

    RedemptionManager.RedemptionParams memory params = RedemptionManager.RedemptionParams({
        asset: asset,
        liquidityProvider: liquidityProvider,
        feeManager: feeManager,
        assetAmount: assetAmount,
        liquidityTokenAmount: liquidityTokenAmount,
        minOutputAmount: minOutputAmount,
-       redeemer: msg.sender,
+       redeemer: _msgSender(),
        assetBurn: assetBurn
    });

    // ... execution logic ...

    emit RedemptionCompleted(
-       msg.sender,
+       _msgSender(),
        assetAmount,
        liquidityTokenAmount,
        rate,
        fee,
        address(liquidityProvider.liquidityToken())
    );
}

// SecuritizeBridge.sol
function bridgeDSTokens(uint16 targetChain, uint256 value) external override payable whenNotPaused {
    uint256 cost = quoteBridge(targetChain);
    require(msg.value >= cost, "Transaction value should be equal or greater than quoteBridge response");
-   require(dsToken.balanceOf(msg.sender) >= value, "Not enough balance in source chain to bridge");
+   require(dsToken.balanceOf(_msgSender()) >= value, "Not enough balance in source chain to bridge");

    // ... validation logic ...

-   require(registryService.isWallet(msg.sender), "Investor not registered");
+   require(registryService.isWallet(_msgSender()), "Investor not registered");

-   string memory investorId = registryService.getInvestor(msg.sender);
+   string memory investorId = registryService.getInvestor(_msgSender());

    // ... other logic ...

-   dsToken.burn(msg.sender, value, BRIDGE_REASON);
+   dsToken.burn(_msgSender(), value, BRIDGE_REASON);

    wormholeRelayer.sendPayloadToEvm{value: msg.value}(
        targetChain,
        targetAddress,
        abi.encode(
            investorDetail.investorId,
            value,
-           msg.sender,
+           _msgSender(),
            investorDetail.country,
            investorDetail.attributeValues,
            investorDetail.attributeExpirations
        ),
        0,
        gasLimit,
        whChainId,
-       msg.sender
+       _msgSender()
    );

-   emit DSTokenBridgeSend(targetChain, address(dsToken), msg.sender, value);
+   emit DSTokenBridgeSend(targetChain, address(dsToken), _msgSender(), value);
}

function validateLockedTokens(string memory investorId, uint256 value, IDSRegistryService registryService) private view {
    // ... compliance service logic ...

-   uint256 availableBalanceForTransfer = complianceService.getComplianceTransferableTokens(msg.sender, block.timestamp, uint64(lockPeriod));
+   uint256 availableBalanceForTransfer = complianceService.getComplianceTransferableTokens(_msgSender(), block.timestamp, uint64(lockPeriod));
    require(availableBalanceForTransfer >= value, "Not enough unlocked balance in source chain to bridge");
}
```

**Securitize:** Fixed in commit [045925](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/045925798158710fef70ecdd0e47da1974b37bfd) and commit [1da35c](https://bitbucket.org/securitize_dev/bc-securitize-bridge-sc/commits/1da35cde31a53e7b2de56de0d313ebdcb80cbfa3).

**Cyfrin:** Verified.

## [M-11] `USDCBridgeV2::_quoteBridge` hardcodes `msgValue=0` creating fee mismatch that bricks the USDC bridge when gas dropoff is configured
- Severity: `Medium`
- Source report: `bridgev2.md`

### Detailed Content (from source)
**Description:** `USDCBridgeV2::_quoteBridge` computes the executor fee using `RelayInstructions.encodeGas(gasLimit, 0)` with a hardcoded zero for the gas dropoff parameter:

```solidity
function _quoteBridge(uint16 _targetChain) private view returns (uint256 execFee) {
    bytes memory request = ExecutorMessages.makeCCTPv2Request();
@>  bytes memory relayInstructions = RelayInstructions.encodeGas(gasLimit, 0); // hardcoded 0
    execFee = executorQuoterRouter.quoteExecution(
        _targetChain, bytes32(0), address(this), quoterAddr, request, relayInstructions
    );
}
```

However, `USDCBridgeV2::sendUSDCCrossChainDeposit` calls `requestExecution` with the actual stored `msgValue`:

```solidity
executorQuoterRouter.requestExecution{value: execFee}(
    _targetChain,
    bytes32(0),
    address(this),
    quoterAddr,
    ExecutorMessages.makeCCTPv2Request(),
@>  RelayInstructions.encodeGas(gasLimit, msgValue) // actual msgValue
);
```

When admin sets `msgValue > 0` via `USDCBridgeV2::updateMsgValue`, the fee quoted by `_quoteBridge` is lower than what the executor actually requires for the relay instructions passed to `requestExecution`. The balance check at L215 (`address(this).balance < execFee`) uses this underestimated fee, allowing the transaction to proceed with insufficient ETH for the actual execution cost.

**Impact:** When admin configures `msgValue > 0` via `USDCBridgeV2::updateMsgValue`, the USDC bridge is completely bricked — every `USDCBridgeV2::sendUSDCCrossChainDeposit` call reverts and no USDC can be bridged until admin resets `msgValue` to 0.

The Wormhole `ExecutorQuoterRouter::requestExecution` ([source](https://github.com/wormholelabs-xyz/example-messaging-executor/blob/main/evm/src/ExecutorQuoterRouter.sol)) re-computes the required fee from the **actual relay instructions passed in the same call** (not from a prior quote). It parses the `relayInstructions` bytes to extract `gasLimit` and `msgValue`, converts them to source chain value, and checks `msg.value >= requiredPayment`. If insufficient, it reverts with `Underpaid(provided, expected)`.

Since the revert occurs within the same atomic transaction, the preceding USDC `safeTransferFrom` and CCTP `depositForBurn` are also rolled back — no USDC is permanently lost. However, the bridge is non-functional for its intended purpose: bridging USDC with gas dropoff configured.

**Recommended Mitigation:** Use `msgValue` in `_quoteBridge` to match the relay instructions actually passed to `requestExecution`:

```diff
function _quoteBridge(uint16 _targetChain) private view returns (uint256 execFee) {
    bytes memory request = ExecutorMessages.makeCCTPv2Request();
-   bytes memory relayInstructions = RelayInstructions.encodeGas(gasLimit, 0);
+   bytes memory relayInstructions = RelayInstructions.encodeGas(gasLimit, msgValue);
    execFee = executorQuoterRouter.quoteExecution(
        _targetChain, bytes32(0), address(this), quoterAddr, request, relayInstructions
    );
}
```

**Securitize:** Fixed in commit [c313304](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/c31330414ae1c0d7dd9477fd6e02411ce56fd1a0)

**Cyfrin:** Verified. Call to `RelayInstructions::encodeGas` is now called with `msgValue` instead of hardcoding the value to`0`

## [M-12] Permanent loss of DSTokens when bridging to non-EVM chains via the backward-compatible `SecuritizeBridge::bridgeDSTokens` due to missing target chain type validation
- Severity: `Medium`
- Source report: `bridgev2.md`

### Detailed Content (from source)
**Description:** `SecuritizeBridge.bridgeDSTokens(uint16 _targetChain, uint256 _value)` is the backward-compatible bridge entry point for users who want to bridge DS tokens to the same wallet address on a destination chain. To derive the destination address, it encodes `msg.sender` (a 20-byte EVM address) into a 32-byte value using EVM-specific padding:

```solidity
// SecuritizeBridge.bridgeDSTokens(uint16 _targetChain, uint256 _value)
bytes32 destinationAddress = bytes32(uint256(uint160(_msgSender())));
```

This encoding is only valid for EVM-compatible chains (Ethereum, Arbitrum, Avalanche, Base, Optimism, Polygon), where addresses are 20 bytes padded to 32. Non-EVM chains supported by the bridge — specifically Solana (Wormhole chain ID 1) — use a different address scheme: Ed25519 public keys, which are natively 32 random bytes and bear no structural relationship to EVM addresses.

If a user calls the backward-compatible `SecuritizeBridge::bridgeDSTokens` and it passes the `_targetChain` as the ID of a non-EVM chain, the burnt bridged tokens are permanently unrecoverable.

The precondition is a user calling `SecuritizeBridge::bridgeDSTokens` — the simpler, backward-compatible entry point — with a non-EVM target chain ID. Unlike `SecuritizeBridge.bridgeDSTokensToAddress(uint16 _targetChain, uint256 _value, bytes32 _destinationAddress)`, which requires callers to supply a chain-appropriate bytes32 destination and is therefore more explicitly a power-user interface.

The call path is:

1. `bridgeDSTokens(_targetChain=1, _value)` — encodes `msg.sender` as `bytes32(uint256(uint160(msg.sender)))` (EVM padding)
2. Calls `bridgeDSTokensToAddress(1, _value, malformedBytes32)` — no zero-check or chain-type check
3. `_bridgeDSTokensInternal()` — validates investor compliance, burns tokens, publishes VAA with malformed destination
4. Executor delivers VAA to Solana bridge
5. Solana bridge issues tokens to the 32-byte value — an address the user does not own

No validation between steps 1 and 2 checks whether `_targetChain` corresponds to an EVM chain before applying EVM-specific address encoding.

**Recommended Mitigation:** Add a check in `SecuritizeBridge::bridgeDSTokens` that reverts if `_targetChain` is not an EVM-compatible chain before deriving the destination address from `msg.sender`. Maintain an allowlist of EVM Wormhole chain IDs (or a mapping of chain ID to address type), and revert with a descriptive error when a non-EVM chain ID is supplied to the backward-compatible entry point.

**Securitize:** Fixed in commit [328f890](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/328f890f5726ce2aec8b2ab7a55ef455784a4586).

**Cyfrin:** Verified. Added a check in `SecuritizeBridge::bridgeDSTokens`  to revert if `_targetChain` is not an EVM-compatible chain.

\clearpage
## Gas Optimization

## [M-13] Bridging `DSToken` back-and-forth between chains causes `totalIssuance` cap to be reached, preventing further issuances and cross-chain transfers
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** `StandardToken::totalIssuance` is not decreased by burns but is used to enforce maximum cap, since `totalIssuance` is supposed to track the total number of tokens ever issued, not the current "supply".

However there is an interesting consequence to this when considering cross-chain bridging via `SecuritizeBridge`; `receiveWormholeMessages` calls `DSToken::issueTokens` on the destination chain which increases `StandardToken::totalIssuance`.

**Impact:** Consider this scenario:
* Alice bridges from Ethereum -> Arbitrum with 1000 `DSToken`
* Alice bridges back from Arbitrum -> Ethereum with the "same" 1000 `DSToken`
* Alice keeps doing this over and over again

This process continually increases the `totalIssuance` on both chains, even though it is just the same tokens going back and forth; at some point this will cause the cap to be hit on one of the chains. This doesn't even require malicious investors, just investors who bridge back-and-forth frequently.

Once the cap is hit further issuances and cross-chain transfers will revert on that chain.

**Recommended Mitigation:** Potential mitigations include:
* have bridging actually decrement `totalIssuance` on the source chain
* have `SecuritizeBridge::receiveWormholeMessages` call `DSToken::issueTokensCustom` passing a `reason == "BRIDGING"` then  in `TokenLibrary::issueTokensCustom` don't increment `totalIssuance` for `"BRIDGING"` reason
* track the number of bridged tokens separately and modify the cap check to account for this

**Securitize:** Fixed in commit [c2e62c9](https://github.com/securitize-io/dstoken/commit/c2e62c9c1137bb7c6f548b72f960d864c42445fc); the cap was deprecated and associated checks removed. There is a similar compliance-related check that uses `totalSupply` so correctly accounts for burns.

**Cyfrin:** Verified.

\clearpage

## [M-14] Emit missing events on important parameter changes
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Emit missing events on important parameter changes:
* `CCTPSender::setCCTPDomain`
* `USDCBridgeV2::setCCTPDomain`

**Securitize:** Fixed in commit [cd8c8ad](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/cd8c8ada1240c862458138cc1db9372aaf970573) for `USDCBridgeV2`, leaving the other as it will be deprecated.

**Cyfrin:** Verified.

## [M-15] Fail fast without doing unnecessary work
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** If a transaction is going to revert, then revert as fast as possible without doing unnecessary work. Strategies to achieve this include:
* perform all input-related validation first
* read only enough storage or make enough external calls to perform the next validation step

For example in `SecuritizeBridge::bridgeDSTokens`:
```solidity
    function bridgeDSTokens(uint16 targetChain, uint256 value) external override payable whenNotPaused {
        // @audit why do all this work...
        uint256 cost = quoteBridge(targetChain);
        require(msg.value >= cost, "Transaction value should be equal or greater than quoteBridge response");
        require(dsToken.balanceOf(_msgSender()) >= value, "Not enough balance in source chain to bridge");
        address targetAddress = bridgeAddresses[targetChain];
        require(bridgeAddresses[targetChain] != address(0), "No bridge address available");

        IDSRegistryService registryService = IDSRegistryService(dsServiceConsumer.getDSService(dsServiceConsumer.REGISTRY_SERVICE()));
        require(registryService.isWallet(_msgSender()), "Investor not registered");

        // @audit ...if txn will revert here due to invalid input?
        require(value > 0, "DSToken value must be greater than 0");
```

And in `USDCBridgeV2::sendUSDCCrossChainDeposit`
```solidity
    function sendUSDCCrossChainDeposit(
        uint16 _targetChain,
        address _recipient,
        uint256 _amount
    ) external override whenNotPaused nonReentrant onlyRole(BRIDGE_CALLER) {
        uint256 deliveryCost = quoteBridge(_targetChain);
        // @audit why perform this storage read...
        address targetBridge = bridgeAddresses[_targetChain];
        // @audit ...if this check will just revert? Perform this check immediately
        // after `uint256 deliveryCost = quoteBridge(_targetChain);`
        if (address(this).balance < deliveryCost) {
            revert InsufficientContractBalance();
        }
        // @audit why perform this check here?
        if (IERC20(USDC).balanceOf(_msgSender()) < _amount) {
            revert NotEnoughBalance();
        }
        // @audit if it is going to revert from this? Perform this check immediately
        // after ` address targetBridge = bridgeAddresses[_targetChain];`
        if (targetBridge == address(0)) {
            revert BridgeAddressUndefined();
        }
```

**Securitize:** Fixed in commit [2ad89cf](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/2ad89cf65ea61c999f140fa6754fb1077a3674b1).

**Cyfrin:** Verified.

## [M-16] Follow function declaration solidity style guide in `BaseContract`
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Functions `pause` and `unpause` defines the visibility `public` after the modifier `onlyOwner`. As per the [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html#function-declaration), the order expects modifiers to be placed after visibility declarations.
```solidity
function pause() onlyOwner external {
        _pause();
    }

    function unpause() onlyOwner external {
        _unpause();
    }
```

**Recommended Mitigation:** Update the code in the following way:
```solidity
function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
```

**Securitize:** Fixed in commit [61fb6a6](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/61fb6a6e4cb0830d152aa3a436a718fb0e0795ae).

**Cyfrin:** Verified.

## [M-17] Hard-coding 0 max fee with fast finality is incompatible as this combination commonly has minimum fees of 1
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Circle's [CCTPv2 Technical Guide](https://developers.circle.com/cctp/technical-guide) provides the following relevant information:
* Messages with `minFinalityThreshold` of 1000 or lower are considered Fast messages
* Messages with `minFinalityThreshold` of 2000 are considered Standard messages (in practice everything > 1000 is considered Standard)
* The applicable fee should be retrieved every time before executing a transaction using this [API](https://developers.circle.com/api-reference/cctp/all/get-burn-usdc-fees)

The provided API requires specifying the CCTP input and output [domains](https://developers.circle.com/cctp/cctp-supported-blockchains#cctp-v2-supported-domains). Using the `wget` form of the API, the minimum fees for fast finality (1000) are typically 1:

* Ethereum -> Avalanche
```console
$ wget --quiet \
  --method GET \
  --header 'Content-Type: application/json' \
  --output-document \
  - https://iris-api-sandbox.circle.com/v2/burn/USDC/fees/0/1
[{"finalityThreshold":1000,"minimumFee":1},{"finalityThreshold":2000,"minimumFee":0}]%
```

* Ethereum -> Solana
```console
$ wget --quiet \
  --method GET \
  --header 'Content-Type: application/json' \
  --output-document \
  - https://iris-api-sandbox.circle.com/v2/burn/USDC/fees/0/5
[{"finalityThreshold":1000,"minimumFee":1},{"finalityThreshold":2000,"minimumFee":0}]%
```

**Impact:** Many CCTP cross-domain transfers have a minimum fee of 1 for fast finality, but `USDCBridgeV2::_transferUSDC` hard-codes a maximum fee of 0 with fast finality 1000:
```solidity
circleTokenMessenger.depositForBurn(
    _amount,
    getCCTPDomain(_targetChain),
    targetAddressBytes32,        // mintRecipient on destination
    USDC,          // burnToken
    destinationCallerBytes32,        // destinationCaller (restrict who can mint)
    0,   // @audit maximum fee
    1000 // @audit fast finality
);
```

This combination is incompatible and will result in many cross-domain transfers unable to use fast finality, reverting to standard finality. If the minimum fee for standard finality ever becomes > 0, this would cause all attempted cross-domain transfers to revert since the automatic downgrade to standard finality would no longer be possible.

**Recommended Mitigation:** Ideally the maximum fee and finality should be provided as inputs:
* current fee bps should be retrieved off-chain using the provided API for the desired domain combination
* multiply fee bps by the amount to be transferred to calculate the maximum fee
* pass maximum fee and desired finality as inputs when calling `circleTokenMessenger.depositForBurn`

At least there should be a way to change the maximum fee, it shouldn't be hard-coded to zero as this causes the protocol to become unusable if standard finality fees become non-zero.

**Securitize:** Fixed in commit [0d3e50d](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/0d3e50daadb37b29266a86d76a9c060eeed5805d) by:
* always using standard finality
* max fee is now a variable so we can change it if Circle increases standard finality fees in the future

**Cyfrin:** Verified.

## [M-18] No way to retrieve ETH sent with call to `SecuritizeBridge::receiveWormholeMessages`
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** `SecuritizeBridge::receiveWormholeMessages` is marked as `payable` however:
* it does nothing with `msg.value`
* there is no function in `SecuritizeBridge` to withdraw ETH

**Impact:** If ETH should be sent along with the call to `SecuritizeBridge::receiveWormholeMessages`, it will be stuck in the contract unable to be retrieved.

**Recommended Mitigation:** Add a function `withdrawETH` that allows the contract owner to withdraw the contract's ETH balance.

**Securitize:** Fixed in commits [923e50e](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/923e50e41dc859fa9516dd370988d01d685759e6), [2b18646](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/2b18646e6344fcebe4f32107cd56812877ddadea#diff-3f58493270011157ff7c863627332c733405a46f8b6524660d25b33ef16f9f74R171) by adding a `withdrawETH` function the owner can call.

**Cyfrin:** Verified.

## [M-19] Refactor `SecuritizeBridge::bridgeDSTokens` and `quoteBridge` to use `internal` function saves 2 storage reads per bridging transaction
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** `SecuritizeBridge::bridgeDSTokens`:
* L71 calls `quoteBridge` which reads `wormholeRelayer` and `gasLimit` from storage
* L91 calls `wormholeRelayer.sendPayloadToEvm` which reads `wormholeRelayer` from storage again
* L108 reads `gasLimit` from storage again

Storage reads are expensive; refactor like this to avoid identical storage reads here:
```solidity
// new internal function
    function _quoteBridge(IWormholeRelayer relayer, uint256 _gasLimit, uint16 targetChain) internal view returns (uint256 cost) {
        (cost, ) = relayer.quoteEVMDeliveryPrice(targetChain, 0, _gasLimit);
    }

// modify `quoteBridge` to use new internal function
    function quoteBridge(uint16 targetChain) public override view returns (uint256 cost) {
        (cost, ) = _quoteBridge(wormholeRelayer, gasLimit, targetChain);
    }

// in `bridgeDSTokens` to cache `wormholeRelayer` and `gasLimit`
// then pass them to `_quoteBridge` and use them at L91 & L108
```

The same optimization should also be applied to `USDCBridgeV2::sendUSDCCrossChainDeposit`, `quoteBridge` and `_sendUSDCWithPayloadToEvm`.

**Securitize:** Fixed in commit [47c1ad0](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/47c1ad0de51887344785cebb7f5668b769b9d092).

**Cyfrin:** Verified.

## [M-20] Refactor `SecuritizeBridge::validateLockedTokens` to take `dsServiceConsumer` as input parameter
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** `SecuritizeBridge::bridgeDSTokens` at L77 reads `dsServiceConsumer` from storage then at L83 calls `validateLockedTokens`.

The internal function `validateLockedTokens` itself re-reads `dsServiceConsumer` from storage multiple times.

Reading from storage is expensive; instead:
* cache `dsServiceConsumer` once in `bridgeDSTokens`
* refactor `validateLockedTokens` to take `dsServiceConsumer` as an input parameter
* in `bridgeDSTokens` when calling `validateLockedTokens` pass the cached `dsServiceConsumer` as an input parameter

**Securitize:** Fixed in commits [bcc83e0](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/bcc83e04b66320b07fcc621352de72e59985bf8a), [0cf5dd9](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/0cf5dd91a4ff6ba1d2a1d5c9b55c395e415536e1).

**Cyfrin:** Verified.

## [M-21] Remove unused function `USDCBridgeV2::_redeemUSDC`
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** The `private` function `USDCBridgeV2::_redeemUSDC` is not used anywhere; remove it.

**Securitize:** Fixed in commit [07a872e](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/07a872e8266411a440b736e328a86528b75cbdb0).

**Cyfrin:** Verified.

## [M-22] Remove unused imports
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Remove unused imports:
* `USDCBridgeV2.sol`
```solidity
28:import {IBridge} from "./IBridge.sol";
```

**Securitize:** Fixed in commit [a45cb7e](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/a45cb7edcc9ec79c5e1cc30420c826e0566af827).

**Cyfrin:** Verified.

## [M-23] Uninitialized CCTP domain mapping can send USDC to the incorrect blockchain
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** `USDCBridgeV2::chainIdToCCTPDomain` maps Wormhole chain IDs to Circle's CCTP domain IDs:
```solidity
mapping(uint16 => uint32) public chainIdToCCTPDomain;

function getCCTPDomain(uint16 _chain) internal view returns (uint32) {
    return chainIdToCCTPDomain[_chain];  // @audit returns 0 if not set!
}
```

**Impact:** When this mapping isn't initialized for a wormhole chain id, it returns 0 by default (Solidity's default value for `uint32`). However [Circle's CCTP domain 0 is Ethereum mainnet](https://developers.circle.com/cctp/cctp-supported-blockchains#cctp-v2-supported-domains). So if a mapping has not been configured for a given [wormhole chain id](https://wormhole.com/docs/products/reference/chain-ids/) eg (6 for Avalanche),`USDCBridgeV2::_transferUSDC` will happily send USDC to Ethereum instead of Avalanche:
```solidity
        circleTokenMessenger.depositForBurn(
            _amount,
            getCCTPDomain(_targetChain), // @audit 0 by default = Ethereum mainnet
            targetAddressBytes32,        // mintRecipient on destination
            USDC,          // burnToken
            destinationCallerBytes32,        // destinationCaller (restrict who can mint)
            0,
            1000
        );
```

**Recommended Mitigation:** The simplest option is to change `USDCBridgeV2::getCCTPDomain` to only allow domain 0 for wormhole's Ethereum chain id:
```solidity
function getCCTPDomain(uint16 _chain) internal view returns (uint32 domain) {
    domain = chainIdToCCTPDomain[_chain];
    // Wormhole ChainID 2 = Ethereum https://wormhole.com/docs/products/reference/chain-ids/
    // Only allow CCTP Domain 0 for Ethereum https://developers.circle.com/cctp/cctp-supported-blockchains#cctp-v2-supported-domains
    require(domain != 0 || _chain == 2, "CCTP domain not configured");
}
```

Another potential solution is to change `setBridgeAddress` such that it always sets the CCTP domain as well eg:
```solidity
    function setBridgeAddress(uint16 _chainId, address _bridgeAddress, uint32 _cctpDomain) external override onlyRole(DEFAULT_ADMIN_ROLE) {
        bridgeAddresses[_chainId] = _bridgeAddress;
        chainIdToCCTPDomain[_chain] = _cctpDomain;
        emit BridgeAddressAdd(_chainId, _bridgeAddress, _cctpDomain);
    }
```

Also consider changing `removeBridgeAddress` to delete from `chainIdToCCTPDomain` eg:
```solidity
    function removeBridgeAddress(uint16 _chainId) external override onlyRole(DEFAULT_ADMIN_ROLE) {
        delete bridgeAddresses[_chainId];
        delete chainIdToCCTPDomain[_chainId];
        emit BridgeAddressRemove(_chainId);
    }
```

**Securitize:** Fixed in commit [d750854](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/d750854aadd6873ad2be3aa95fd5abe80fa01bd3) by removing `setBridgeAddress` and adding a new function `setCCTPBridgeAddress` which enforces that CCTP Domain is configured at the same time as target bridge address for the same wormhole chain id. Also changed `removeBridgeAddress` to clear both mappings together as well.

**Cyfrin:** Verified.

## [M-24] Upgradeable contracts should call `_disableInitializers` in constructor
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Upgradeable contracts should [call](https://docs.openzeppelin.com/upgrades-plugins/writing-upgradeable#initializing_the_implementation_contract) `_disableInitializers` in constructor:
```solidity
/// @custom:oz-upgrades-unsafe-allow constructor
constructor() {
    _disableInitializers();
}
```

Affected contracts:
* `SecuritizeBridge`
* `USDCBridgeV2`

**Securitize:** Fixed in commit [4b7f654](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/4b7f654e98b0a2b4d953101372b360c906459d9b).

**Cyfrin:** Verified.

## [M-25] Use `addressNotZero` modifier on `USDCBridgeV2::setBridgeAddress`
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Use `addressNotZero` modifier on `USDCBridgeV2::setBridgeAddress`:
```diff
-   function setBridgeAddress(uint16 _chainId, address _bridgeAddress) external override onlyRole(DEFAULT_ADMIN_ROLE) {
+   function setBridgeAddress(uint16 _chainId, address _bridgeAddress) external override addressNotZero(_bridgeAddress) onlyRole(DEFAULT_ADMIN_ROLE) {
```

**Securitize:** Fixed in commit [f51d885](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/f51d885e50218167a7fb16d0152337bf8e8445d6).

**Cyfrin:** Verified.

## [M-26] Use `SafeERC20` approval and transfer functions instead of standard IERC20 functions
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Use [SafeERC20::forceApprove](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/utils/SafeERC20.sol#L105-L110) and `safeTransfer` functions instead of standard IERC20 functions:
```solidity
wormhole/WormholeCCTPUpgradeable.sol
121:        IERC20(USDC).approve(address(circleTokenMessenger), amount);

bridge/USDCBridgeV2.sol
150:        IERC20(USDC).transferFrom(_msgSender(), address(this), _amount);
264:        IERC20(USDC).approve(address(circleTokenMessenger), _amount);
```

**Securitize:** Fixed in commit [d75ac6f](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/d75ac6fb219f2f536172e4c7b146cece27ca175e).

**Cyfrin:** Verified.

## [M-27] Use `targetAddress` instead of `bridgeAddresses[targetChain]` for check in `SecuritizeBridge::bridgeDSTokens`
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Use `targetAddress` instead of `bridgeAddresses[targetChain]` for check in `SecuritizeBridge::bridgeDSTokens`:
```diff
        address targetAddress = bridgeAddresses[targetChain];
-       require(bridgeAddresses[targetChain] != address(0), "No bridge address available");
+       require(targetAddress != address(0), "No bridge address available");
```

**Securitize:** Fixed in commit [9081b85](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/9081b858ffddcf1b9b6a3eafcbee3b6a2da192e8).

**Cyfrin:** Verified.

## [M-28] Use named imports
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Use named imports consistently throughout the codebase.

**Securitize:** Fixed in commit [85ca7bb](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/85ca7bb455cd78921b4f9ad7c48b0cf9eb0470e4).

**Cyfrin:** Verified.

## [M-29] Use named mapping parameters to make explicit the purpose of keys and values
- Severity: `Medium`
- Source report: `cctpv2.md`

### Detailed Content (from source)
**Description:** Use named mapping parameters to make explicit the purpose of keys and values:
```solidity
wormhole/WormholeCCTPUpgradeable.sol
79:    mapping(uint16 => uint32) public chainIdToCCTPDomain;

bridge/USDCBridgeV2.sol
63:    mapping(uint16 => address) public bridgeAddresses;
64:    mapping(uint16 => uint32) public chainIdToCCTPDomain;

bridge/SecuritizeBridge.sol
40:    mapping(uint16 => address) public bridgeAddresses;
```

**Securitize:** Fixed in commit [40f4db0](https://github.com/securitize-io/bc-securitize-bridge-sc/commit/40f4db07a0351b3aebb3547a49236a1ca54a99d3).

**Cyfrin:** Verified.

## [M-30] Allow custom Creator and Collector names to be emitted in `IStory` events to build artwork provenance
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** The `IStory` interface is designed to allow custom names to be emitted for the Creator and Collector events. Here is an [example](https://www.transient.xyz/nfts/base/0x6c81306129b3cc63b0a6c7cec3dd50721ac378fe/9) where a Creator has used the custom name `lytke`.

But in CryptoArt's implementation of `IStory` interface, custom names are not allowed and it is always the caller's hex string that will be set:
```solidity
function addCollectionStory(string calldata, /*creatorName*/ string calldata story) external onlyOwner {
    emit CollectionStory(msg.sender, msg.sender.toHexString(), story);
}

/// @inheritdoc IStory
function addCreatorStory(uint256 tokenId, string calldata, /*creatorName*/ string calldata story)
    external
    onlyTokenOwner(tokenId)
{
    emit CreatorStory(tokenId, msg.sender, msg.sender.toHexString(), story);
}

/// @inheritdoc IStory
function addStory(uint256 tokenId, string calldata, /*collectorName*/ string calldata story)
    external
    onlyTokenOwner(tokenId)
{
    emit Story(tokenId, msg.sender, msg.sender.toHexString(), story);
}
```

**Impact:** Custom names should be allowed as they form part of the "provenance" of an artwork; the value of an artwork is often based on who the creator was and if it has been held by significant collectors in the past. Proper custom names are a lot easier to remember and tell a story about rather than 0x1343335...Artworks with custom names will be able to build a better story around them resulting in improved "provenance".

**CryptoArt:**
Fixed in commit [77f34a4](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/77f34a49cbc27589f3179b35b58a86696696bf83).

**Cyfrin:** Verified.

## [M-31] Protocol vulnerable to cross-chain signature replay
- Severity: `Medium`
- Source report: `cryptoart.md`

### Detailed Content (from source)
**Description:** As signatures do not include`chainId`, signature verification is vulnerable to [cross-chain replay](https://dacian.me/signature-replay-attacks#heading-cross-chain-replay).

**Impact:** Although the protocol plans to deploy cross-chain in the future, the specification of this audit is to only consider deployment to one chain. Hence this finding is only Informational as this attack path is not possible when the protocol is only deployed on one chain.

**Recommended Mitigation:** Include `block.chainid` as a signature parameter.

**CryptoArt:**
Fixed in commit [1e25f8c](https://github.com/cryptoartcom/cryptoart-smart-contracts/commit/1e25f8cd172a32e3e35ccf8a86e7af9fe1ed47fe).

**Cyfrin:** Verified.

## [M-32] `BridgeableTokenP::getMaxDebitableAmount` doesn't account for isolate mode, returning inflated values
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** When isolate mode is on, `BridgeableTokenP::_debit` enforces that `creditDebitBalance` stays `>= 0` after debiting:

```solidity
if (isIsolateMode) {
    if (creditDebitBalance < 0) revert ErrorsLib.IsolateModeLimitReach();
}
```

This effectively caps the max debit at the current `creditDebitBalance`. But `BridgeableTokenP::getMaxDebitableAmount` doesn't factor this in — it only considers the global and daily limits:

```solidity
function getMaxDebitableAmount() external view returns (uint256) {
    if (isIsolateMode && creditDebitBalance < 0) return 0;
    if (creditDebitBalance <= globalDebitLimit) return 0;
    uint256 globalMax = MathLib.abs(globalDebitLimit - creditDebitBalance);
    ...
    return MathLib.min(globalMax, dailyMax);
}
```

So the view can report, say, 500 as the max debitable when in practice only 50 can go through before isolate mode reverts.

There's also a minor off-by-one in the early return: the guard checks `creditDebitBalance < 0` instead of `<= 0`. When the balance is exactly 0, the function doesn't bail out early and returns a non-zero value, even though any debit at that point would revert.

**Impact:** Any user or integrating contract that relies on this view to build transactions will show an incorrect max. Transactions built on top of this will revert, wasting gas.

**Proof of Concept:** Assume `isIsolateMode = true`, `creditDebitBalance = 50`, `globalDebitLimit = -1000`, `dailyDebitLimit = 500`, no daily usage yet.

1. A user calls `getMaxDebitableAmount()` — it computes `globalMax = 1050`, `dailyMax = 500`, returns `500`
2. User submits a debit of 51 tokens trusting the view output
3. Inside `_debit`, balance goes to `50 - 51 = -1`
4. Isolate mode check catches it and reverts with `IsolateModeLimitReach`

The real cap here is 50, not 500.

**Recommended Mitigation:** Two changes: fix the `< 0` guard to `<= 0`, and cap the result by `creditDebitBalance` when in isolate mode:

```solidity
function getMaxDebitableAmount() external view returns (uint256) {
    if (isIsolateMode && creditDebitBalance <= 0) return 0;
    if (creditDebitBalance <= globalDebitLimit) return 0;
    uint256 globalMax = MathLib.abs(globalDebitLimit - creditDebitBalance);
    uint256 currentDebitAmount = dailyDebitAmount[_getCurrentDay()];
    uint256 dailyMax = dailyDebitLimit > currentDebitAmount
        ? dailyDebitLimit - currentDebitAmount
        : 0;
    uint256 result = MathLib.min(globalMax, dailyMax);
    if (isIsolateMode) return MathLib.min(result, uint256(creditDebitBalance));
    return result;
}
```

**Parallel:** Fixed in commit [6735f32](https://github.com/parallel-protocol/parrallel-tokens/commit/6735f32b21b888f53ca8ef08c96a5bfab498f2dd).

**Cyfrin:** Verified. Remediated by implementing the recommended mitigation, `BridgeableTokenP::getMaxDebitableAmount` now correctly caps the limits when `isolateMode` is enabled.


\clearpage

## [M-33] `IBridgeableTokenP::swapLzTokenToPrincipalToken` interface declares a `uint256` return value but `BridgeableTokenP::swapLzTokenToPrincipalToken` returns nothing, breaking external integrations
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** The `IBridgeableTokenP` interface declares `swapLzTokenToPrincipalToken` as returning `uint256`:

```solidity
function swapLzTokenToPrincipalToken(address _to, uint256 _amount) external returns(uint256);
```

However, the actual implementation in `BridgeableTokenP::swapLzTokenToPrincipalToken` has no return value:

```solidity
function swapLzTokenToPrincipalToken(address _to, uint256 _amount) external nonReentrant whenNotPaused {
```

Any external contract calling `swapLzTokenToPrincipalToken` through the `IBridgeableTokenP` interface will have its ABI decoder attempt to decode a `uint256` from the return data. Since the implementation returns nothing, the decoder will revert.

**Impact:** External contracts and protocols integrating with `BridgeableTokenP` through the `IBridgeableTokenP` interface will have their calls revert. Direct calls (not through the interface) are unaffected.

**Proof of Concept:**
1. An external contract holds a reference: `IBridgeableTokenP bridge = IBridgeableTokenP(bridgeAddress);`
2. It calls `uint256 minted = bridge.swapLzTokenToPrincipalToken(user, amount);`
3. The function executes successfully internally, but returns no data
4. The ABI decoder on the caller side expects 32 bytes of return data, finds 0 bytes, and reverts

**Recommended Mitigation:** Either add a return value to the implementation to match the interface:

```solidity
function swapLzTokenToPrincipalToken(address _to, uint256 _amount) external nonReentrant whenNotPaused returns (uint256) {
    // ... existing logic ...
    return principalTokenAmountCredited;
}
```

Or remove the return type from the interface:

```solidity
function swapLzTokenToPrincipalToken(address _to, uint256 _amount) external;
```

**Parallel:** Fixed in commit [68faa40](https://github.com/parallel-protocol/parrallel-tokens/commit/68faa401d4d837bd97ff38e38855bf5db220b77d).

**Cyfrin:** Verified. `BridgeableTokenP::swapLzTokenToPrincipalToken` now returns the amount of `principalToken` actually minted.

## [M-35] Use `SafeERC20` approval and transfer functions instead of standard IERC20 functions for `liquidityToken`
- Severity: `Medium`
- Source report: `ramp.md`

### Detailed Content (from source)
**Description:** The on-ramping and off-ramping processes are linked to external liquidity tokens such as stablecoins whose code is not controlled by the protocol; hence use [`SafeERC20::forceApprove, transfer, safeTransfer`](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/utils/SafeERC20.sol) when dealing with a range of potential tokens:
```solidity
on-ramp/provider/AllowanceAssetProvider.sol
98:        asset.transferFrom(assetProviderWallet, _buyer, _amount);

on-ramp/BaseOnRamp.sol
122:        liquidityToken.transferFrom(from, address(this), amount);
125:            liquidityToken.transfer(feeManager.feeCollector(), fee);
131:            liquidityToken.approve(address(USDCBridge), amountExcludingFee);
134:            liquidityToken.transfer(custodianWallet, amountExcludingFee);

off-ramp/provider/AllowanceLiquidityProvider.sol
141:        liquidityToken.transferFrom(liquidityProviderWallet, _redeemer, _liquidityAmount);

off-ramp/provider/CollateralLiquidityProvider.sol
186:        collateralToken.transferFrom(collateralProvider, address(this), collateralAmount);
189:        collateralToken.approve(address(externalCollateralRedemption), collateralAmount);
198:        liquidityToken.transfer(_redeemer, amountToSupply);

off-ramp/RedemptionManager.sol
43:            _params.asset.transferFrom(_params.redeemer, _params.liquidityProvider.recipient(), _params.assetAmount);
74:        _params.asset.transferFrom(_params.redeemer, _contractAddress, _params.assetAmount);
80:            _params.asset.transfer(_params.liquidityProvider.recipient(), _params.assetAmount);
96:        _params.liquidityProvider.liquidityToken().transfer(_params.redeemer, userSuppliedAmount);
100:            _params.liquidityProvider.liquidityToken().transfer(IFeeManager(_params.feeManager).feeCollector(), fee);
```

**Securitize:** Fixed in commit [a694dc3](https://github.com/securitize-io/bc-on-off-ramp-sc/commit/a694dc32386e038f8541ef79155b7a06a905fc52).

**Cyfrin:** Verified.

## [M-36] Cross-chain incompatibility with `block.number` based timeout mechanism
- Severity: `Medium`
- Source report: `registry.md`

### Detailed Content (from source)
**Description:** `GlobalRegistryService::addGlobalInvestorWallet` function uses `block.number` to validate transaction freshness through a `blockLimit parameter`:
```solidity
function addGlobalInvestorWallet(
    string calldata id,
    address walletAddress,
    uint256 blockLimit
) external override whenNotPaused onlySelf newWallet(walletAddress) returns (bool) {
    if (blockLimit < block.number) {
        revert TransactionTooOld();
    }
    // ...
}
```

According to the hardhat configuration, this contract is designed to be deployed on multiple chains with vastly different block production rates:
* Ethereum Mainnet - Block time: ~12-14 seconds
* Sepolia (Ethereum testnet) - Block time: ~12-14 seconds
* Arbitrum (chainId: 421614) - Block time: ~0.25 seconds (48-56x faster)
* Optimism (chainId: 11155420) - Block time: ~2 seconds (6-7x faster)
* Avalanche/Fuji (chainId: 43113) - Block time: ~2 seconds (6-7x faster)

The problem is that block production rates vary dramatically across these chains, making block-based time validation inconsistent and unreliable. I an operator signs a pre-approved transaction with `blockLimit = currentBlock + 100`:
* On Ethereum: Valid for ~100 × 13 seconds = ~21 minutes
* On Arbitrum: Valid for ~100 × 0.25 seconds = ~25 seconds
* On Optimism/Avalanche: Valid for ~100 × 2 seconds = ~3.3 minutes

**Impact:** Transactions could revert in one chain and be added in other chains if an investor is adding the same wallet among different chains.

**Recommended Mitigation:** Replace `block.number` with `block.timestamp` for consistent cross-chain behavior.

**Securitize:** Fixed in commits [8f92757](https://github.com/securitize-io/bc-global-registry-service-sc/commit/8f927571c7526817ffe43c5f37d11560e79809d9), [e99c56f](https://github.com/securitize-io/bc-global-registry-service-sc/commit/e99c56fe94f9b41e0680d2318f504fca33be4919), [920e496](https://github.com/securitize-io/bc-global-registry-service-sc/commit/920e4965bb9306203a8251e58c962f4dfff67a3f).

**Cyfrin:** Verified.

## [M-37] High centralization risk in `STBL_USST::bridgeBurn`
- Severity: `Medium`
- Source report: `stbl.md`

### Detailed Content (from source)
**Description:** Current implementation of `STBL_USST::bridgeBurn` allows `BRIDGE_ROLE` to burn tokens from any arbitrary address without user approval. This creates unnecessary centralization risk when a safer approach is already demonstrated in the protocol's own `STBL_Token` contract.

```solidity
// STBL_USST.solfunction bridgeBurn(
    address _from,      // @audit can be any address
    uint256 _amt,
    bytes memory _data
) external whenNotPaused onlyRole(BRIDGE_ROLE) {
    _burn(_from, _amt);  // @audit Burns from arbitrary address without consent
    emit BridgeBurn(_from, _amt, _data);
}
```
The above approach allows the `BRIDGE_ROLE` (initialized to the `DEFAULT_ADMIN`) to burn tokens from any address. An alternate implementation already implemented in `STBL_TOKEN` is much safer:

```solidity
// STBL_Token.sol
function bridgeBurn(uint256 _amt) external whenNotPaused onlyRole(BRIDGE_ROLE) {
    _burn(_msgSender(), _amt);  // @audit Only burns caller's (bridge's) own tokens
}
```

**Impact:** Bridge contract compromise can allow mass token burning in a single transaction. This also significantly increases the trust assumptions and centralization risk around the bridge contract creating a single point of failure for entire token ecosystem.


**Recommended Mitigation:** Consider using the `STBL_Token` code for implementing `bridgeBurn` functionality. Alternatively, first transfer tokens from the caller into the contract and then burn them.

**STBL:** Fixed in commit [a737746](https://github.com/USD-Pi-Protocol/contract/commit/a737746e3f136f6c83605228b81b23da23e27183)

**Cyfrin:** Verified.

## [M-38] Prefer explicit `uint` sizes
- Severity: `Medium`
- Source report: `syntetika.md`

### Detailed Content (from source)
**Description:** Prefer explicit `uint` sizes:
* `Issuance`
```solidity
interfaces/minter/IBridgeMinter.sol
14:        uint id,
29:        uint id;

interfaces/galactica/IVerificationSBT.sol
45:        uint _expirationTime,
55:        uint _expirationTime

interfaces/token/IMintableERC20.sol
7:    function mint(address to, uint amount) external;
8:    function burn(address from, uint amount) external;

vault/StakingVault.sol
143:        uint assetsRedeemed = _redeemTo(shares, address(tokensHolder));
289:    ) internal returns (uint shares) {
306:    ) internal returns (uint assets) {
```

* `Deposit-Registry`:
```solidity
interfaces/ICompliantDepositRegistry.sol
44:        uint indexed startIndex,
45:        uint challengePeriodEnd,
48:    event BatchChallengePeriodSet(uint newChallengePeriod);
50:        uint indexed startIndex,
51:        uint challengePeriodEnd,
52:        uint batchLength
100:        uint startIndex,
101:        uint count
116:    function setBatchChallengePeriod(uint newChallengePeriod) external;

ComplianceChecker.sol
44:        for (uint i = 0; i < complianceOptions.length; i++) {
58:            uint optionIndex = 0;
65:                uint sbtIndex = 0;

CompliantDepositRegistry.sol
27:    uint public nextDepositAddressIndex;
30:    uint public batchChallengePeriod;
32:    uint public latestBatchUnlockTime;
34:    uint public finalizedAddressesLength;
44:        // Block the first deposit address so that the default uint does not point to a valid address
124:        uint startIndex,
125:        uint count
127:        uint returnLength = count;
133:            uint i = 0;
156:        uint startIndex = depositAddresses.length;
157:        for (uint i = 0; i < newDepositAddresses.length; i++) {
174:    function _setBatchChallengePeriod(uint newChallengePeriod) internal {
184:        uint newChallengePeriod
199:        uint batchLength = depositAddresses.length - finalizedAddressesLength;
200:        for (uint i = 0; i < batchLength; i++) {
```

**Syntetika:**
Fixed in commit [cb00843](https://github.com/SyntetikaLabs/monorepo/commit/cb0084368c85c4878dfd0af0fbca1c4924a36497).

**Cyfrin:** Verified.

## [M-39] Decimal mismatch in `BasisTradeTailor:transferHypeToCore` causes precision loss
- Severity: `Medium`
- Source report: `update.md`

### Detailed Content (from source)
**Description:** The `BasisTradeTailor::transferHypeToCore` function accepts `uint256 amount` with 18 decimals (HyperEVM standard), but when bridging to HyperCore, the amount is truncated to 8 decimals. Any precision beyond 8 decimals is permanently lost.

```solidity
// BasisTradeTailor.sol:400-412
function transferHypeToCore(address pocket, uint256 amount) external onlyOperator {
    require(pocketUser[pocket] != address(0), "Pocket does not exist");
    require(amount > 0, "Amount must be positive");

    IPocket(pocket).transferNative(
        CoreWriterEncoder.HYPE_SYSTEM_ADDRESS,  // Bridges to Core with 8 decimals
        amount  // uint256 with 18 decimals - precision beyond 8 decimals lost
    );

    lastCoreActionBlock[pocket] = block.number;
    emit LastCoreActionBlockUpdated(pocket, block.number);
    emit HypeTransferredToCore(pocket, amount);  // Emits full 18-decimal amount
}
```

Per [HyperLiquid documentation](https://hyperliquid.gitbook.io/hyperliquid-docs), HYPE uses 18 decimals on HyperEVM but only 8 decimals on HyperCore. The bridge automatically truncates any precision beyond 8 decimals.

**Impact:** Each bridge transaction loses the fractional amount beyond 8 decimal precision. While individual losses are small (~9e-10 HYPE per transaction in worst case), they accumulate over time and represent permanent fund loss.

**Recommended Mitigation:** Add validation requiring amounts to be multiples of `1e10` (8 decimal precision):

```solidity
function transferHypeToCore(address pocket, uint256 amount) external onlyOperator {
    require(pocketUser[pocket] != address(0), "Pocket does not exist");
    require(amount > 0, "Amount must be positive");
    require(amount % 1e10 == 0, "Amount must be multiple of 1e10 for 8-decimal precision");

    IPocket(pocket).transferNative(CoreWriterEncoder.HYPE_SYSTEM_ADDRESS, amount);

    lastCoreActionBlock[pocket] = block.number;
    emit LastCoreActionBlockUpdated(pocket, block.number);
    emit HypeTransferredToCore(pocket, amount);
}
```

**Button:** Fixed in commit [`b74a07d`](https://github.com/buttonxyz/button-protocol/commit/b74a07db825a07098bf83e06f9467308d9f0a211)

**Cyfrin:** Verified. Amount verified to be a multiple of `1e10`.

## [M-40] Rounding in favor of the violator can subject liquidators to losses during partial liquidation
- Severity: `Medium`
- Source report: `vii.md`

### Detailed Content (from source)
**Description:** Currently, `ERC721WrapperBase::transfer` rounds in favor of the sender, or in the context of liquidation in favor of the violator:

```solidity
/// @notice For regular EVK vaults, it transfers the specified amount of vault shares from the sender to the receiver
/// @dev For ERC721WrapperBase, transfers a proportional amount of ERC6909 tokens (calculated as totalSupply(tokenId) * amount / balanceOf(sender)) for each enabled tokenId from the sender to the receiver.
/// @dev no need to check if sender is being liquidated, sender can choose to do this at any time
/// @dev When calculating how many ERC6909 tokens to transfer, rounding is performed in favor of the sender (typically the violator).
/// @dev This means that the sender may end up with a slightly larger amount of ERC6909 tokens than expected, as the rounding is done in their favor.
function transfer(address to, uint256 amount) external callThroughEVC returns (bool) {
    address sender = _msgSender();
    uint256 currentBalance = balanceOf(sender);

    uint256 totalTokenIds = totalTokenIdsEnabledBy(sender);

    for (uint256 i = 0; i < totalTokenIds; ++i) {
        uint256 tokenId = tokenIdOfOwnerByIndex(sender, i);
        _transfer(sender, to, tokenId, normalizedToFull(tokenId, amount, currentBalance)); //this concludes the liquidation. The liquidator can come back to do whatever they want with the ERC6909 tokens
    }
    return true;
}
```

This stems from the usage of `Math::mulDiv` in `ERC721WrapperBase` which performs floor rounding when calculating the normalized amount of ERC-6909 token to transfer for the given sender's underlying collateral value:

```solidity
function normalizedToFull(uint256 tokenId, uint256 amount, uint256 currentBalance) public view returns (uint256) {
    return Math.mulDiv(amount, totalSupply(tokenId), currentBalance);
}
```

However, this behavior can be leveraged by a malicious actor to inflate the value of their position. Considering the scenario in which a borrower enables multiple `tokenIds` as collateral, this is possible is they unwrap all but 1 wei of the ERC-6909 token balance for a given `tokenId`. This can also occur when one of the `tokenIds` is fully transferred per the proportional calculation by an earlier partial liquidation. In both cases, this leaves behind 1 wei due to rounding which can cause issues during subsequent liquidation.

Note that it is not possible to inflate the value of 1 wei of ERC-6909 token by adding liquidity to the underlying position since atomically unwrapping the full position, adding liquidity, and rewrapping (as required due to access control implemented by Uniswap when modifying liquidity owned by another account) would result in the `FULL_AMOUNT` of ERC-6909 tokens being minted again. It is, however, possible to leverage fee accrual from donations and swaps, which contributes to the value of the position, to inflate 1 wei in this manner.

Rounding should therefore be done in favor of the liquidator to avoid the scenario in which they are forced to either perform a full liquidation or sustain losses due to a partial liquidation in which they receive no ERC-6909 tokens.

**Impact:** Liquidators can be subject to losses during partial liquidation, especially if there has been significant fee accrual to the underlying Uniswap position in the time after the ERC-6909 token supply is reduced to 1 wei.

**Proof of Concept:** Run the following tests with `forge test --mt test_transferRoundingPoC -vvv`:

* Without the transfer inflation fix applied as described in H-02, the floor rounding setup can be observed in this first test:

```solidity
function test_transferRoundingPoC_currentTransfer() public {
    address borrower2 = makeAddr("borrower2");

    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: -19999
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);
    (uint256 tokenId2,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);

    // 1. borrower wraps tokenId1
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, borrower);
    wrapper.enableTokenIdAsCollateral(tokenId1);

    // 2. borrower sends some of tokenId1 to borrower2
    wrapper.transfer(borrower2, wrapper.balanceOf(borrower) / 2);

    // 3. borrower wraps tokenId2
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, borrower);
    wrapper.enableTokenIdAsCollateral(tokenId2);

    // 4. borrower max borrows from vault
    evc.enableCollateral(borrower, address(wrapper));
    evc.enableController(borrower, address(eVault));
    eVault.borrow(type(uint256).max, borrower);

    vm.warp(block.timestamp + eVault.liquidationCoolOffTime());

    (uint256 maxRepay, uint256 yield) = eVault.checkLiquidation(liquidator, borrower, address(wrapper));
    assertEq(maxRepay, 0);
    assertEq(yield, 0);

    // 5. simulate borrower becoming partially liquidatable
    startHoax(IEulerRouter(address(oracle)).governor());
    IEulerRouter(address(oracle)).govSetConfig(
        address(wrapper),
        unitOfAccount,
        address(
            new FixedRateOracle(
                address(wrapper),
                unitOfAccount,
                1
            )
        )
    );

    (maxRepay, yield) = eVault.checkLiquidation(liquidator, borrower, address(wrapper));
    assertTrue(maxRepay > 0);

    // 6. liquidator partially liquidates borrower
    startHoax(liquidator);
    evc.enableCollateral(liquidator, address(wrapper));
    evc.enableController(liquidator, address(eVault));
    wrapper.enableTokenIdAsCollateral(tokenId1);
    wrapper.enableTokenIdAsCollateral(tokenId2);
    eVault.liquidate(borrower, address(wrapper), maxRepay / 2, 0);

    console.log("balanceOf(borrower, tokenId1): %s", wrapper.balanceOf(borrower, tokenId1));
    console.log("balanceOf(borrower, tokenId2): %s", wrapper.balanceOf(borrower, tokenId2));
}
```

* Assuming the H-02 fix is applied, losses to the liquidator during partial liquidations due to rounding in favor of the violator can be observed in the following test:

```solidity
function test_transferRoundingPoC_transferFixed() public {
    LiquidityParams memory params = LiquidityParams({
        tickLower: TickMath.MIN_TICK + 1,
        tickUpper: TickMath.MAX_TICK - 1,
        liquidityDelta: -19999
    });

    (uint256 tokenId1,,) = boundLiquidityParamsAndMint(params);
    (uint256 tokenId2,,) = boundLiquidityParamsAndMint(params);

    startHoax(borrower);

    // 1. borrower wraps tokenId1
    wrapper.underlying().approve(address(wrapper), tokenId1);
    wrapper.wrap(tokenId1, borrower);
    wrapper.enableTokenIdAsCollateral(tokenId1);

    // 2. borrower unwraps all but 1 wei of tokenId1
    wrapper.unwrap(
        borrower,
        tokenId1,
        borrower,
        wrapper.FULL_AMOUNT() - 1,
        bytes("")
    );

    // 3. borrower wraps tokenId2
    wrapper.underlying().approve(address(wrapper), tokenId2);
    wrapper.wrap(tokenId2, borrower);
    wrapper.enableTokenIdAsCollateral(tokenId2);

    // 4. borrower max borrows from vault
    evc.enableCollateral(borrower, address(wrapper));
    evc.enableController(borrower, address(eVault));
    eVault.borrow(type(uint256).max, borrower);

    vm.warp(block.timestamp + eVault.liquidationCoolOffTime());

    (uint256 maxRepay, uint256 yield) = eVault.checkLiquidation(liquidator, borrower, address(wrapper));
    assertEq(maxRepay, 0);
    assertEq(yield, 0);

    // 5. swap to accrue fees
    swapExactInput(borrower, address(token0), address(token1), 100 * unit0);

    // 6. simulate borrower becoming partially liquidatable
    startHoax(IEulerRouter(address(oracle)).governor());
    IEulerRouter(address(oracle)).govSetConfig(
        address(wrapper),
        unitOfAccount,
        address(
            new FixedRateOracle(
                address(wrapper),
                unitOfAccount,
                1
            )
        )
    );

    (maxRepay, yield) = eVault.checkLiquidation(liquidator, borrower, address(wrapper));
    assertTrue(maxRepay > 0);

    // 7. liquidator partially liquidates borrower but receives no tokenId1
    startHoax(liquidator);
    evc.enableCollateral(liquidator, address(wrapper));
    evc.enableController(liquidator, address(eVault));
    wrapper.enableTokenIdAsCollateral(tokenId1);
    wrapper.enableTokenIdAsCollateral(tokenId2);

    uint256 liquidatorBalanceOfTokenId1Before = wrapper.balanceOf(liquidator, tokenId1);
    uint256 liquidatorBalanceOfTokenId2Before = wrapper.balanceOf(liquidator, tokenId2);
    eVault.liquidate(borrower, address(wrapper), maxRepay / 2, 0);
    uint256 liquidatorBalanceOfTokenId1After = wrapper.balanceOf(liquidator, tokenId1);
    uint256 liquidatorBalanceOfTokenId2After = wrapper.balanceOf(liquidator, tokenId2);

    console.log("balanceOf(borrower, tokenId1): %s", wrapper.balanceOf(borrower, tokenId1));
    console.log("balanceOf(borrower, tokenId2): %s", wrapper.balanceOf(borrower, tokenId2));

    console.log("liquidatorBalanceOfTokenId1Before: %s", liquidatorBalanceOfTokenId1Before);
    console.log("liquidatorBalanceOfTokenId1After: %s", liquidatorBalanceOfTokenId1After);

    console.log("liquidatorBalanceOfTokenId2Before: %s", liquidatorBalanceOfTokenId2Before);
    console.log("liquidatorBalanceOfTokenId2After: %s", liquidatorBalanceOfTokenId2After);

    assertGt(liquidatorBalanceOfTokenId1After, liquidatorBalanceOfTokenId1Before);
    assertGt(liquidatorBalanceOfTokenId2After, liquidatorBalanceOfTokenId2Before);
}
```

**Recommended Mitigation:** Consider rounding in favor of the liquidator:

```diff
    function normalizedToFull(uint256 tokenId, uint256 amount, uint256 currentBalance) public view returns (uint256) {
-        return Math.mulDiv(amount, totalSupply(tokenId), currentBalance);
+        return Math.mulDiv(amount, balanceOf(_msgSender(), tokenId), currentBalance, Math.Rounding.Ceil);
    }
```

Also consider preventing liquidators from executing liquidations of zero value to avoid scenarios in which they can repeatedly extract 1 wei of a high-value position from the violator.

**VII Finance:** Fixed in commit [5e825d5](https://github.com/kankodu/vii-finance-smart-contracts/commit/5e825d5f2eee6789b646bd0f00e9a9a53b5039ca).

**Cyfrin:** Verified. Transfers now round up in favor of the receiver (typically the liquidator). Note that liquidators are still not explicitly prevented from executing liquidations of zero value.

**VII Finance:** When liquidation happens, the Euler vault associated with borrowed token, asks EVC to manipulate the injected `_msgSender()` to be violator and call transfer function with to = liquidator and amount = whatever liquidator deserves for taking on violator's debt.  As far as the wrapper is concerned, zero value liquidation is just a zero value transfer. The wrapper allows it the same way any other Euler vault that follow ERC20 standard allows for zero value transfers. We don't see a need for preventing the zero value transfers.

**Cyfrin:** Acknowledged.

\clearpage

## [M-41] Weak signature validation in account activation
- Severity: `Medium`
- Source report: `wlf.md`

### Detailed Content (from source)
**Description:** The `WorldLibertyFinancialV2::activateAccount` function uses a simple hash of the account address for signature validation instead of following EIP-712 standards.

While the contract initializes EIP-712 infrastructure during setup, the activation function bypasses this standard and uses a basic `keccak256(abi.encode(account))` hash. This deviates from established security best practices for signature hashing.

```solidity
function activateAccount(bytes calldata _signature) external {
    address account = _msgSender();
    bytes32 hash = keccak256(abi.encode(account)); // @account simple hash, no EIP-712

    if (authorizedSigner() != ECDSA.recover(hash, _signature)) {
        revert InvalidSignature();
    }

    _activateAccount(account);
}
```

**Impact:** If WLFI expands to multiple chains in the future, signatures could be replayed across chains. Alternatively, if contract was ever migrated to a new proxy or implementation, signatures generated for current contract could work on new deployments.

Also, since the contract implements EIP712, off-chain systems expect EIP-712 structured data for security.


**Recommended Mitigation:** The practical risk is currently mitigated by:

- Double activation protection
- Assumed single-chain deployment

Nevertheless, consider implementing EIP-712 signature validation to follow security best practices and future-proof the contract,


**WLFI:**
Fixed in commit [b567696](https://github.com/worldliberty/usd1-protocol/blob/b56769613b6438b62b8b4133a63fca727fdbc631/contracts/wlfi/WorldLibertyFinancialV2.sol#L41).

**Cyfrin:** Verified.

## [M-42] `_receiverGas` check excludes minimum acceptable value
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In the LayerZero bridge contracts [`BridgeLR::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/BridgeLR.sol#L76) and [`BridgeMB::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/BridgeMB.sol#L66), there's a check to ensure the user has provided sufficient `_receiverGas`:

```solidity
require(_receiverGas > MIN_RECEIVER_GAS, "!gas");
```

The variable name `MIN_RECEIVER_GAS` suggests that the specified amount should be *inclusive*, meaning the minimum acceptable value is valid. However, the current `>` check excludes `MIN_RECEIVER_GAS` itself. To align with the semantic expectation, consider changing the comparison to `>=`:

```diff
- require(_receiverGas > MIN_RECEIVER_GAS, "!gas");
+ require(_receiverGas >= MIN_RECEIVER_GAS, "!gas");
```

Same applies to the call [`Bridge::setMIN_RECEIVER_GAS`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L53) and the check in [`Bridge::quote`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L85) as well.

**YieldFi:** Fixed in commit [`9aa242b`](https://github.com/YieldFiLabs/contracts/commit/9aa242b7351314fe07160e98699d8da14a1b9bc2)

**Cyfrin:** Verified.

## [M-43] `BridgeCCIP.isL1` can be immutable
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** [`BridgeCCIP.isL1`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L34) is only [assigned](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L44) in the constructor. Therefore it can be made immutable as immutable values are cheaper to read.

Consider making `BridgeCCIP.isL1` immutable.

**YieldFi:** Fixed in commit [`823b010`](https://github.com/YieldFiLabs/contracts/commit/823b010d74fd55fb88b31619c1a94dac2ef65ad3)

**Cyfrin:** Verified.

## [M-44] Access to `LockBox::unlock` doesn't follow principle of least privilege
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** The function [`LockBox::unlock`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/LockBox.sol#L97) has the modifier [`onlyBridgeOrLockBox`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/administrator/Access.sol#L37-L40) which allows callers with either the role `BRIDGE_ROLE` or `LOCKBOX_ROLE` to access the call.

The function is however only called from the bridge contracts. Consider removing the access from the `LOCKBOX_ROLE` to follow principle of least privileges.

**YieldFi:** Fixed in commit [`f0c751a`](https://github.com/YieldFiLabs/contracts/commit/f0c751a25d3cf8d46661f7508b72193c88e6fc91)

**Cyfrin:** Verified.

\clearpage
## Gas Optimization

## [M-45] Chainlink router configured twice
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In `BridgeCCIP`, there is a dedicated storage slot for the CCIP router address, [`router`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L32-L33):

```solidity
contract BridgeCCIP is CCIPReceiver, Ownable {
    address public router;
```

This value can be updated by the admin through [`BridgeCCIP::setRouter`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L69-L73):

```solidity
function setRouter(address _router) external onlyAdmin {
    require(_router != address(0), "!router");
    router = _router;
    emit SetRouter(msg.sender, _router);
}
```

The `router` is then used in [`BridgeCCIP::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L157) to send messages via CCIP:

```solidity
IRouterClient(router).ccipSend{ value: msg.value }(_dstChain, evm2AnyMessage);
```

However, the inherited `CCIPReceiver` contract already defines an immutable router address (`i_ccipRouter`), which is used to validate that incoming CCIP messages originate from the correct router.

This introduces an inconsistency: if `BridgeCCIP.router` is changed, the contract will continue to *send* messages via the new router, but *receive* messages only from the original, immutable `i_ccipRouter`. This mismatch could break cross-chain communication or make message delivery non-functional.

**Recommended Mitigation:** Since the router address in `CCIPReceiver` is immutable, any future change to the router would already require redeployment of the `BridgeCCIP` contract. Therefore, the `router` storage slot and the `setRouter` function in `BridgeCCIP` are redundant and potentially misleading. We recommend removing both and relying exclusively on the `i_ccipRouter` value inherited from `CCIPReceiver`.

**YieldFi:** Fixed in commit [`3cc0b23`](https://github.com/YieldFiLabs/contracts/commit/3cc0b2331c35327a43e95176ce6c5578f145c0ee)

**Cyfrin:** Verified. `router` removed and `i_ccipRouter` used from the inherited contract.

## [M-46] Hardcoded `extraArgs` violates CCIP best practices
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** When sending cross-chain messages via CCIP, Chainlink recommends keeping the `extraArgs` parameter mutable to allow for future upgrades or configuration changes, as outlined in their [best practices](https://docs.chain.link/ccip/best-practices#using-extraargs).

However, this recommendation is not followed in [`BridgeCCIP::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L126-L133), where `extraArgs` is hardcoded:
```solidity
// Sends the message to the destination endpoint
Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
    receiver: abi.encode(_receiver), // ABI-encoded receiver address
    data: abi.encode(_encodedMessage), // ABI-encoded string
    tokenAmounts: new Client.EVMTokenAmount[](0), // Empty array indicating no tokens are being sent
    // @audit-issue `extraArgs` hardcoded
    extraArgs: Client._argsToBytes(Client.EVMExtraArgsV2({ gasLimit: 200_000, allowOutOfOrderExecution: true })),
    feeToken: address(0) // For msg.value
});
```

**Impact:** Because `extraArgs` is hardcoded, any future changes would require deploying a new version of the bridge contract.

**Recommended Mitigation:** Consider making `extraArgs` mutable by either passing it as a parameter to the `send` function or deriving it from configurable contract storage.

**YieldFi:** Fixed in commits [`3cc0b23`](https://github.com/YieldFiLabs/contracts/commit/3cc0b2331c35327a43e95176ce6c5578f145c0ee) and [`fd4b7ab5`](https://github.com/YieldFiLabs/contracts/commit/fd4b7ab57a5ae2ac366b4d9d086eb372defc7f8c)

**Cyfrin:** Verified. `extraArgs` is now passed as a parameter to the call.

## [M-47] Hardcoded CCIP `feeToken` prevents LINK discount usage
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** In `BridgeCCIP::send`, the [`feeToken`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L126-L133) parameter is hardcoded:
```solidity
// Sends the message to the destination endpoint
Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
    receiver: abi.encode(_receiver), // ABI-encoded receiver address
    data: abi.encode(_encodedMessage), // ABI-encoded string
    tokenAmounts: new Client.EVMTokenAmount[](0), // Empty array indicating no tokens are being sent
    extraArgs: Client._argsToBytes(Client.EVMExtraArgsV2({ gasLimit: 200_000, allowOutOfOrderExecution: true })),
    // @audit-issue hardcoded fee token
    feeToken: address(0) // For msg.value
});
```

Chainlink CCIP supports paying fees using either the native gas token or `LINK`. By hardcoding `feeToken = address(0)`, the protocol forces all users to pay with the native gas token, removing flexibility.

This design choice simplifies implementation but has cost implications: CCIP offers a [10% fee discount](https://docs.chain.link/ccip/billing#network-fee-table) when using `LINK`, so users holding `LINK` are unable to take advantage of these reduced fees.

**Recommended Mitigation:** Consider allowing users to choose their preferred payment token—either `LINK` or native gas—based on their individual cost and convenience preferences.

**YieldFi:** Fixed in commits [`3cc0b23`](https://github.com/YieldFiLabs/contracts/commit/3cc0b2331c35327a43e95176ce6c5578f145c0ee) and [`e9c160f`](https://github.com/YieldFiLabs/contracts/commit/e9c160fdfd6dd90650c9537fba73c17cb3c53ea5)

**Cyfrin:** Verified.

## [M-48] Static `gasLimit` will result in overpayment
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** Since [unspent gas is not refunded](https://docs.chain.link/ccip/best-practices#setting-gaslimit), Chainlink recommends carefully setting the `gasLimit` within the `extraArgs` parameter to avoid overpaying for execution.

In [`BridgeCCIP::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L131), the `gasLimit` is hardcoded to `200_000`, which is also Chainlink’s default:

```solidity
extraArgs: Client._argsToBytes(Client.EVMExtraArgsV2({ gasLimit: 200_000, allowOutOfOrderExecution: true })),
```

This hardcoded value directly affects every user bridging tokens, as they will be consistently overpaying for execution costs on the destination chain.

**Recommended Mitigation:** A more efficient approach would be to measure the gas usage of the `_ccipReceive` function using tools like Hardhat or Foundry and set the `gasLimit` accordingly—adding a margin for safety. This ensures that the protocol avoids overpaying for gas on every cross-chain message.

This issue also reinforces the importance of making `extraArgs` mutable, so the gas limit and other parameters can be adjusted if execution costs change over time (e.g., due to protocol upgrades like [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884)).

**YieldFi:** Fixed in commit [`3cc0b23`](https://github.com/YieldFiLabs/contracts/commit/3cc0b2331c35327a43e95176ce6c5578f145c0ee)

**Cyfrin:** Verified. `extraArgs` is now passed as a parameter to the call.

## [M-49] Unused imports
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** Consider removing the following unused imports:

- contracts/bridge/Bridge.sol [Line: 7](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L7)
- contracts/bridge/Bridge.sol [Line: 9](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L9)
- contracts/bridge/Bridge.sol [Line: 13](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L13)
- contracts/bridge/Bridge.sol [Line: 15](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L15)
- contracts/bridge/Bridge.sol [Line: 18](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L18)
- contracts/bridge/Bridge.sol [Line: 20](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/Bridge.sol#L20)
- contracts/bridge/BridgeMB.sol [Line: 17](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/BridgeMB.sol#L17)
- contracts/bridge/ccip/BridgeCCIP.sol [Line: 4](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L4)
- contracts/bridge/ccip/BridgeCCIP.sol [Line: 13](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L13)
- contracts/core/Manager.sol [Line: 6](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L6)
- contracts/core/Manager.sol [Line: 15](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L15)
- contracts/core/Manager.sol [Line: 17](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/Manager.sol#L17)
- contracts/core/OracleAdapter.sol [Line: 6](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/OracleAdapter.sol#L6)
- contracts/core/PerpetualBond.sol [Line: 7](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L7)
- contracts/core/PerpetualBond.sol [Line: 13](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/PerpetualBond.sol#L13)
- contracts/core/interface/IPerpetualBond.sol [Line: 4](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/interface/IPerpetualBond.sol#L4)
- contracts/core/l1/LockBox.sol [Line: 10](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/LockBox.sol#L10)
- contracts/core/l1/LockBox.sol [Line: 13](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/LockBox.sol#L13)
- contracts/core/l1/Yield.sol [Line: 5](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L5)
- contracts/core/l1/Yield.sol [Line: 10](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L10)
- contracts/core/l1/Yield.sol [Line: 11](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L11)
- contracts/core/l1/Yield.sol [Line: 12](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L12)
- contracts/core/l1/Yield.sol [Line: 13](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L13)
- contracts/core/l1/Yield.sol [Line: 14](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L14)
- contracts/core/l1/Yield.sol [Line: 16](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/l1/Yield.sol#L16)
- contracts/core/tokens/YToken.sol [Line: 8](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L8)
- contracts/core/tokens/YToken.sol [Line: 14](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YToken.sol#L14)
- contracts/core/tokens/YTokenL2.sol [Line: 12](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/core/tokens/YTokenL2.sol#L12)

**YieldFi:** Fixed in commit [`8264429`](https://github.com/YieldFiLabs/contracts/commit/826442914cb9829aa302dbaef0741659cc5a1a67)

**Cyfrin:** Verified.

## [M-50] Unverified `_receiver` can cause irrecoverable token loss
- Severity: `Medium`
- Source report: `yieldfi.md`

### Detailed Content (from source)
**Description:** When a user bridges their YTokens using CCIP, they call [`BridgeCCIP::send`](https://github.com/YieldFiLabs/contracts/blob/40caad6c60625d750cc5c3a5a7df92b96a93a2fb/contracts/bridge/ccip/BridgeCCIP.sol#L117-L158). One of the parameters passed to this function is `_receiver`, which is intended to be the destination contract on the receiving chain:

```solidity
function send(address _yToken, uint64 _dstChain, address _to, uint256 _amount, address _receiver) external payable notBlacklisted(msg.sender) notBlacklisted(_to) notPaused {
    require(_amount > 0, "!amount");
    require(lockboxes[_yToken] != address(0), "!token !lockbox");
    require(IERC20(_yToken).balanceOf(msg.sender) >= _amount, "!balance");
    require(_to != address(0), "!receiver");
    require(tokens[_yToken][_dstChain] != address(0), "!destination");

    bytes memory _encodedMessage = abi.encode(_dstChain, _to, tokens[_yToken][_dstChain], _amount, Constants.BRIDGE_SEND_HASH);

    // Sends the message to the destination endpoint
    Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
        // @audit-issue `_receiver` not verified
        receiver: abi.encode(_receiver), // ABI-encoded receiver address
        data: abi.encode(_encodedMessage), // ABI-encoded string
        tokenAmounts: new Client.EVMTokenAmount[](0), // Empty array indicating no tokens are being sent
        extraArgs: Client._argsToBytes(Client.EVMExtraArgsV2({ gasLimit: 200_000, allowOutOfOrderExecution: true })),
        feeToken: address(0) // For msg.value
    });
```

However, the `_receiver` parameter is not validated. If the user provides an incorrect or malicious address, the message may be delivered to a contract that cannot handle it, resulting in unrecoverable loss of the bridged tokens.

**Recommended Mitigation:** Validate the `_receiver` address against a trusted mapping, such as the `peers` mapping mentioned in a previous finding, to ensure it corresponds to a legitimate contract on the destination chain.

**YieldFi:** Fixed in commit [`a03341d`](https://github.com/YieldFiLabs/contracts/commit/a03341d8103ba08473ea1cd39e64192608692aca)

**Cyfrin:** Verified. `_receiver ` is now verified to be a trusted peer.

<!-- /Cyfrin Fixed Issues (Merged) -->
