# lending / bridge-integration

- Count: `4`
- Definition: bridge adapter assumptions do not match actual bridge behavior/constraints.

## [Malda][M-10] Unenforced `maxFee` and `ttl` in `sendMsg`
- Severity: `Medium`
- Source: [Issue #317](https://github.com/sherlock-audit/2025-07-malda-judging/issues/317)
- Impact: `functional-break`

### Detailed Content
- Summary: netting-mode intent in Everclear requires `maxFee=0` and `ttl=0`, but bridge adapter accepted arbitrary values from decoded payload.
- Root Cause: `sendMsg` validated token/destination but did not enforce netting-specific protocol constraints before calling `newIntent`.
- Trigger Conditions: rebalancer submits non-zero fee/ttl in `_message`; transaction remains syntactically valid.
- Impact Detail: rebalance can be sent through unsupported solver semantics or misrouted, reducing cross-chain reliability.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-12] Excessive bridge fee can drain market funds
- Severity: `Medium`
- Source: [Issue #686](https://github.com/sherlock-audit/2025-07-malda-judging/issues/686)
- Impact: `fund-loss`

### Detailed Content
- Summary: bridge fee cap was effectively controlled by message payload, allowing outsized fee authorization.
- Root Cause: no protocol max bound/sanity check on `maxFee` before forwarding to external bridge fee adapter.
- Attack Path: repeated rebalance operations with extreme fee settings transfer little net value to destination while consuming source liquidity.
- Impact Detail: cumulative drain from market reserves through fee channel.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-15] Across failure locks bridged funds
- Severity: `Medium`
- Source: [Issue #1309](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1309)
- Impact: `locked-funds`

### Detailed Content
- Summary: Across refunds failed/expired deposits to depositor on origin chain; depositor was rebalancer contract.
- Root Cause: integration did not include reclaim/redispatch mechanism for refunded assets held by rebalancer.
- Trigger Conditions: relayer does not fill intent or fill expires; optimistic verification completes and refund executes.
- Impact Detail: bridge funds return to non-user-facing contract and become inaccessible to intended market flow.

### Fix Status
- `Fixed/Resolved in report`

## [Malda][M-16] Bridges do not support all listed assets
- Severity: `Medium`
- Source: [Issue #1477](https://github.com/sherlock-audit/2025-07-malda-judging/issues/1477)
- Impact: `functional-break`

### Detailed Content
- Summary: protocol asset support list and bridge-supported asset set diverged.
- Root Cause: capability matrix for Across/Everclear was not enforced at listing/rebalance routing boundary.
- Trigger Conditions: rebalance requested for listed token unsupported by selected bridge.
- Impact Detail: deterministic rebalance failure for affected markets, creating operational dead zones.

### Fix Status
- `Fixed/Resolved in report`

## Cyfrin Fixed Issues (Merged)
- Count: `11`
- Filter: `Severity in {Critical, Medium}` and explicit `Fixed/Resolved markers`
- Source: `cyfrin/*.md`

## [M-1] Consider using named mapping parameters
- Severity: `Medium`
- Source report: `clob.md`

### Detailed Content (from source)
**Description:** Solidity 0.8.18 introduced named mapping parameters, allowing key and value types to be given descriptive names that appear in the source and in IDE tooling. None of the in-scope contracts use this feature, making mappings harder to read at a glance:

```solidity
// Current — intent must be inferred from context
mapping(bytes32 => Event) internal _events;
mapping(bytes32 => bool) public noPositionsRedeemed;
mapping(bytes32 => uint256) public mintedWcolPerEvent;
mapping(bytes32 => bool) public orderInvalidated;
mapping(bytes32 => uint256) public filledAmounts;
mapping(uint256 => uint256[2]) public voidedPayouts;
```

**Recommended Mitigation:** Apply named parameters consistently across the in-scope contracts:

```solidity
mapping(bytes32 eventId => Event) internal _events;
mapping(bytes32 eventId => bool) public noPositionsRedeemed;
mapping(bytes32 eventId => uint256 wcolMinted) public mintedWcolPerEvent;
mapping(bytes32 orderHash => bool) public orderInvalidated;
mapping(bytes32 orderHash => uint256 filled) public filledAmounts;
mapping(uint256 marketId => uint256[2] payouts) public voidedPayouts;
```

**Myriad:** Fixed in commit [`fc17f36`](https://github.com/Polkamarkets/polkamarkets-js/commit/fc17f36fbf8773e31fe88917ea38f6858d297e1f)

**Cyfrin:** Verified.

## [M-2] Transport-Layer Nonce Poisoning Causes Permanent Session Denial of Service
- Severity: `Medium`
- Source report: `connect.md`

### Detailed Content (from source)
**Description:** The WebSocket transport layer (`websocket/index.ts`) wraps every E2E-encrypted payload in a plaintext `TransportMessage` envelope containing a `clientId (UUID)` and a monotonically-increasing nonce. The deduplication logic on the receiving side accepts any message whose nonce exceeds the highest nonce previously seen for a given `clientId`, then persists the new nonce before the encrypted payload is validated.

Because the Centrifugo relay server allows anonymous connections with no authentication (`allow_anonymous_connect_without_token: true`), any attacker can subscribe to a known channel and observe the plaintext `clientId` and `nonce` fields. The attacker then publishes a single spoofed message with the victim's `clientId` and `nonce` set to `Number.MAX_SAFE_INTEGER (9007199254740991)`. This permanently advances the stored nonce counter so that all subsequent legitimate messages (which have lower, sequential nonces) are silently dropped as "duplicates."

The only pre-requisite for attacker is to have handshake channel name `(handshake:{uuid})` is transmitted in plaintext via the deeplink URL or QR code, making it discoverable.

The `clientId` is discoverable when `TransportMessage` envelope is published as plaintext JSON on the Centrifugo channel. Only the `payload` field is ECIES-encrypted, the `clientId` and `nonce` sit outside the E2E encryption layer.

```ts
// websocket/index.ts _process method
const message: TransportMessage = { clientId, nonce, payload: item.payload };
const data = JSON.stringify(message);
await this.centrifuge.publish(item.channel, data);
```
Any subscriber to the channel reads the clientId directly from the JSON, No decryption needed.

```ts
private async _handleIncomingMessage(channel: string, rawData: string): Promise<void> {
    const message = JSON.parse(rawData) as TransportMessage;
    // ... type checks ...

    if (message.clientId === this.storage.getClientId()) return; // skip own

    const latestNonces = await this.storage.getLatestNonces(channel);
    const latestNonce = latestNonces.get(message.clientId) || 0;

    if (message.nonce > latestNonce) {
        //@audit: Nonce is persisted BEFORE payload validation
        latestNonces.set(message.clientId, message.nonce);
        await this.storage.setLatestNonces(channel, latestNonces);
        this.emit("message", { channel, data: message.payload });
    }
}
```
The issue is that the nonce is updated and persisted to storage unconditionally, regardless of whether the payload subsequently passes E2E decryption in `base-client.ts`. Once persisted, all future legitimate messages with `nonce < MAX_SAFE_INTEGER` are silently dropped.

The DoS is permanent because
- The poisoned nonce is persisted to MMKV via `setLatestNonces`, so it survives app restarts
- The only way to recover is to manually clear the app's storage for this channel
- The victim sees no error as messages are silently dropped as "duplicates"

**Impact:**
- **Handshake channel attack:** An attacker who observes the deeplink URL can subscribe to `handshake:{uuid}`, wait for the wallet to publish its encrypted handshake offer, observe its `clientId`, and immediately publish a nonce-poisoning message. The dApp will advance the nonce, preventing any future communication on the poisoned channel. This is a zero-authentication, single-message DoS.
- **Session channel attack (requires channel discovery):** If the attacker discovers the session channel UUID (e.g., through a prior MITM or relay-side visibility), they can permanently kill an active 30-day session. Neither side can communicate until one creates a completely new session.
- **Persistence across restarts:** Nonces are stored in persistent `IKVStore` (MMKV on mobile), so the DoS survives app restarts and device reboots.


**Proof of Concept:**
1. Attacker observes/gets handshake channel name from the deeplink URL (obtainable via clipboard interception, Android Intent inspection, or QR code scanning), which is plaintext: `metamask://connect/mwp?p=...` containing `channel: "handshake:{uuid}"`.
2. Attacker connects to the Centrifugo relay (no auth token needed). The `WebSocketTransport` constructor in `websocket/index.ts` connects with only reconnect options, no token) and subscribes to that channel.
3. Attacker observes the legitimate peer's `clientId` from any message on the channel. Every message is a plaintext JSON envelope: `{ clientId: "abc-123", nonce: 1, payload: "<encrypted>" }`.
4. Attacker publishes one message: `{ clientId: "abc-123", nonce: 9007199254740991, payload: "x" }`.
5. The victim's `_handleIncomingMessage` (line 233 of `websocket/index.ts`) processes it:
6. All subsequent legitimate messages from `clientId: "abc-123"` with normal sequential nonces (2, 3, 4, ...) hit Number.MAX_SAFE_INTEGER

<details>
<summary>Attached script for poisoning nonce</summary>

```ts
// ============================================================================
// Test: Transport-Layer Nonce Poisoning Causes Permanent Session DoS
// File under test: websocket/index.ts (_handleIncomingMessage, lines 233-258)
// Supporting file: websocket/store.ts (getLatestNonces, setLatestNonces)
// ============================================================================

// Mock KV Store (simulates MMKV persistent storage)
class MockKVStore {
  private store = new Map<string, string>();
  async get(key: string): Promise<string | undefined> {
    return this.store.get(key);
  }
  async set(key: string, value: string): Promise<void> {
    this.store.set(key, value);
  }
  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}


// ============================================================================
// Test 1: Nonce poisoning drops all legitimate messages
// ============================================================================

async function test_nonce_poisoning_drops_legitimate_messages() {
  /**
   * Reproduces the exact logic from websocket/index.ts _handleIncomingMessage.
   *
   * Steps:
   *   1. Legitimate message arrives with nonce=1 (accepted)
   *   2. Attacker publishes message with same clientId but nonce=MAX_SAFE_INTEGER
   *   3. Legitimate message arrives with nonce=2 (silently dropped)
   *
   * Root cause: Nonce is persisted (line 248-249) BEFORE the payload reaches
   * base-client.ts for E2E decryption. The attacker's garbage payload fails
   * decryption harmlessly, but the nonce counter is already poisoned.
   */

  const kvstore = new MockKVStore();
  const CHANNEL = "session:test-uuid";
  const NONCE_KEY = `latest-nonces:my-client-id:${CHANNEL}`;
  const emitted: string[] = [];

  // Exact logic from websocket/index.ts lines 233-258
  async function handleIncomingMessage(rawData: string): Promise<void> {
    const message = JSON.parse(rawData);

    // Line 236-238: Type validation
    if (
      typeof message.clientId !== "string" ||
      typeof message.nonce !== "number" ||
      typeof message.payload !== "string"
    ) {
      throw new Error("Invalid message format");
    }

    // Line 241: Skip own messages
    if (message.clientId === "my-client-id") return;

    // Line 244: Load persisted nonces
    const raw = await kvstore.get(NONCE_KEY);
    const latestNonces: Map<string, number> = raw
      ? new Map(Object.entries(JSON.parse(raw)))
      : new Map();

    // Line 245: Get latest nonce for this sender
    const latestNonce = latestNonces.get(message.clientId) || 0;

    // Line 247: Nonce comparison
    if (message.nonce > latestNonce) {
      // Line 248-249: BUG — nonce persisted BEFORE payload validation
      latestNonces.set(message.clientId, message.nonce);
      await kvstore.set(
        NONCE_KEY,
        JSON.stringify(Object.fromEntries(latestNonces))
      );

      // Line 250: Emit to application layer
      emitted.push(message.payload);
    }
    // If nonce <= latestNonce, message is silently dropped as "duplicate"
  }

  // Step 1: Legitimate message (nonce=1) — accepted
  await handleIncomingMessage(
    JSON.stringify({
      clientId: "peer-123",
      nonce: 1,
      payload: "legitimate-encrypted-payload-1",
    })
  );

  // Step 2: Attacker poisons nonce with MAX_SAFE_INTEGER
  await handleIncomingMessage(
    JSON.stringify({
      clientId: "peer-123",
      nonce: Number.MAX_SAFE_INTEGER,
      payload: "garbage-not-valid-ecies",
    })
  );

  // Step 3: Legitimate message (nonce=2) — THIS GETS DROPPED
  await handleIncomingMessage(
    JSON.stringify({
      clientId: "peer-123",
      nonce: 2,
      payload: "legitimate-encrypted-payload-2",
    })
  );

  // Verify: only 2 messages emitted, message [*eciesjs major version mismatch between dApp SDK and mobile wallet creates untested cryptographic interoperability risk*](#eciesjs-major-version-mismatch-between-dapp-sdk-and-mobile-wallet-creates-untested-cryptographic-interoperability-risk) was silently dropped
  const isVulnerable = emitted.length === 2;

  console.log(
    "Test 1 - Nonce poisoning drops legitimate messages:",
    isVulnerable
      ? "VULNERABLE ❌ (Message [*eciesjs major version mismatch between dApp SDK and mobile wallet creates untested cryptographic interoperability risk*](#eciesjs-major-version-mismatch-between-dapp-sdk-and-mobile-wallet-creates-untested-cryptographic-interoperability-risk) silently dropped after nonce poisoning)"
      : "FIXED ✅"
  );
}


// ============================================================================
// Test 2: Poisoned nonce persists across app restarts
// ============================================================================

async function test_nonce_poisoning_persists_across_restarts() {
  /**
   * Proves the DoS is permanent because nonces are stored in persistent
   * KV storage (MMKV on mobile). After an app restart, the poisoned nonce
   * is reloaded and continues to block all legitimate messages.
   *
   * Traces: websocket/store.ts getLatestNonces() and setLatestNonces()
   */

  const kvstore = new MockKVStore();
  const CHANNEL = "session:some-uuid";
  const NONCE_KEY = `latest-nonces:my-client-id:${CHANNEL}`;

  // Simulate: attacker has already poisoned the nonce
  const poisonedNonces = { "peer-123": Number.MAX_SAFE_INTEGER };
  await kvstore.set(NONCE_KEY, JSON.stringify(poisonedNonces));

  // Simulate: app restarts, nonce is reloaded from persistent storage
  const raw = await kvstore.get(NONCE_KEY);
  const restored = new Map<string, number>(Object.entries(JSON.parse(raw!)));
  const storedNonce = restored.get("peer-123") || 0;

  // Simulate: legitimate message arrives after restart with nonce=5
  const legitimateNonce = 5;
  const isDropped = !(legitimateNonce > storedNonce);

  console.log(
    "Test 2 - Poisoned nonce persists across restarts:",
    isDropped
      ? "VULNERABLE ❌ (DoS survives app restart, nonce still poisoned in MMKV)"
      : "FIXED ✅"
  );
}


// ============================================================================
// Test 3: Attacker's garbage payload does not need to pass decryption
// ============================================================================

async function test_nonce_poisoned_before_decryption() {
  /**
   * Proves that the nonce is persisted in _handleIncomingMessage (transport layer)
   * BEFORE the payload reaches decryptMessage in base-client.ts (application layer).
   *
   * The attacker's garbage payload "x" will fail ECIES decryption, but by that
   * point the nonce counter is already written to storage.
   */

  const kvstore = new MockKVStore();
  const CHANNEL = "session:test-uuid";
  const NONCE_KEY = `latest-nonces:my-client-id:${CHANNEL}`;

  // Simulate _handleIncomingMessage with attacker's garbage payload
  const attackerMessage = JSON.stringify({
    clientId: "peer-123",
    nonce: Number.MAX_SAFE_INTEGER,
    payload: "x", // Not valid ECIES ciphertext
  });

  const message = JSON.parse(attackerMessage);

  // Transport layer persists nonce (lines 248-249)
  const latestNonces = new Map<string, number>();
  latestNonces.set(message.clientId, message.nonce);
  await kvstore.set(
    NONCE_KEY,
    JSON.stringify(Object.fromEntries(latestNonces))
  );

  // Application layer tries to decrypt (base-client.ts line 48)
  let decryptionFailed = false;
  try {
    // Simulates: this.keymanager.decrypt("x", privateKey)
    // ECIES decryption of "x" will always fail
    throw new Error("Decryption failed: invalid ciphertext");
  } catch {
    decryptionFailed = true;
  }

  // Check: nonce is already persisted even though decryption failed
  const raw = await kvstore.get(NONCE_KEY);
  const stored = JSON.parse(raw!);
  const nonceAlreadyPoisoned = stored["peer-123"] === Number.MAX_SAFE_INTEGER;

  console.log(
    "Test 3 - Nonce persisted before decryption:",
    decryptionFailed && nonceAlreadyPoisoned
      ? "VULNERABLE ❌ (Nonce written to storage before payload validation)"
      : "FIXED ✅"
  );
}


// ============================================================================
// Runner
// ============================================================================

async function main() {
  console.log("=== Nonce Poisoning DoS Test Suite ===\n");

  await test_nonce_poisoning_drops_legitimate_messages();
  await test_nonce_poisoning_persists_across_restarts();
  await test_nonce_poisoned_before_decryption();

  console.log("\n=== Tests Complete ===");
}

main().catch(console.error);


```

</details>

**Recommended Mitigation:**
1. **Defer nonce persistence until after successful decryption.** Move the `setLatestNonces` call out of `_handleIncomingMessage` and into the application layer (e.g., `base-client.ts`) after the payload has been successfully decrypted and validated. Only update the nonce for messages that pass E2E verification.
2. **Add a maximum nonce jump threshold.** Reject any message where `message.nonce - latestNonce > MAX_NONCE_JUMP` (e.g., 100). Legitimate sequential messages will never jump by thousands.
3. **Consider HMAC authentication on the transport envelope.** Derive a symmetric key from the session's ECDH shared secret and include a MAC over `{clientId, nonce}` in the transport envelope. Only messages with a valid MAC can update the nonce counter.

**Metamask:**
Fixed in commit [fd3a66](https://github.com/MetaMask/mobile-wallet-protocol/commit/fd3a662207b2a2337e89add2a40aec88cbe7cdd2).

**Cyfrin:** Verified.

## [M-3] Inconsistent stake calculation due to mutable `vaultManager` reference in `AvalancheL1Middleware`
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description**

The `AvalancheL1Middleware` contract permits updating the `vaultManager` reference. However, doing so can introduce **critical inconsistencies** in logic that depends on stateful or historical data tied to the original `vaultManager`. Key issues include:

* **Vaults registered in the original manager are not migrated** to the new one.
* **Time-based metadata** like `enabledTime` and `disabledTime` resets upon re-registration, misaligning historical activity.
* Core logic in `getOperatorStake()` depends on `_wasActiveAt()`, which checks whether a vault was active during a given epoch.
* Replacing the `vaultManager` disrupts this check, leading to:

  * Ignored historical stakes
  * Miscounted or missed vaults
  * Incorrect stake attribution

This breaks key protocol guarantees across the middleware and compromises correctness in systems like staking(node creation) and rewards.

**Illustrative Flow**

1. Register vault `V1` in the original `vaultManager`.
2. Replace with `vaultManagerV2` via `setVaultManager()`.
3. Re-register `V1` in `vaultManagerV2` — note: `enabledTime` is reset.
4. Query `getOperatorStake()` for an epoch before re-registration.
5. `_wasActiveAt()` returns `false`, excluding the stake.

**Impact**

* **Data Inconsistency**: `getOperatorStake()` may return incorrect values.
* **Broken Epoch Tracking**: Epoch-based logic dependent on vault state (like `_wasActiveAt`) becomes unreliable.

**Proof of Concept**

```solidity
    function test_changeVaultManager() public {
        // Move forward to let the vault roll epochs
        uint48 epoch = _calcAndWarpOneEpoch();

        uint256 operatorStake = middleware.getOperatorStake(alice, epoch, assetClassId);
        console2.log("Operator stake (epoch", epoch, "):", operatorStake);
        assertGt(operatorStake, 0);

        MiddlewareVaultManager vaultManager2 = new MiddlewareVaultManager(address(vaultFactory), owner, address(middleware));

        vm.startPrank(validatorManagerAddress);
        middleware.setVaultManager(address(vaultManager2));
        vm.stopPrank();

        uint256 operatorStake2 = middleware.getOperatorStake(alice, epoch, assetClassId);
        console2.log("Operator stake (epoch", epoch, "):", operatorStake2);
        assertEq(operatorStake2, 0);
    }

```

**Recommended Mitigation**

Consider eliminating the ability to arbitrarily update the `vaultManager` once the middleware is initialized. Flexibility to update this variable introduces unintended side-effects that likely expand the attack surface.

**Suzaku:**
Fixed in commit [35f6e56](https://github.com/suzaku-network/suzaku-core/pull/155/commits/35f6e5604c9d3ea77ad38424bb7587f4977f2146).

**Cyfrin:** Verified.

## [M-4] Uptime loss due to integer division in `UptimeTracker::computeValidatorUptime` can make validator lose entire rewards for an epoch
- Severity: `Medium`
- Source report: `core.md`

### Detailed Content (from source)
**Description:** `UptimeTracker::computeValidatorUptime` loses validator uptime due to integer division truncation when distributing uptime across multiple epochs. This results in validators losing reward eligibility for uptime they legitimately earned.

```solidity
// UptimeTracker::computeValidatorUptime
// Distribute the recorded uptime across multiple epochs
if (elapsedEpochs >= 1) {
    uint256 uptimePerEpoch = uptimeToDistribute / elapsedEpochs; // @audit integer division
    for (uint48 i = 0; i < elapsedEpochs; i++) {
        uint48 epoch = lastUptimeEpoch + i;
        if (isValidatorUptimeSet[epoch][validationID] == true) {
            break;
        }
        validatorUptimePerEpoch[epoch][validationID] = uptimePerEpoch; // @audit time loss due to precision
        isValidatorUptimeSet[epoch][validationID] = true;
    }
}
```

Integer division in Solidity truncates the remainder:
- `uptimeToDistribute / elapsedEpochs` loses `uptimeToDistribute % elapsedEpochs`
- The lost remainder is never recovered in future calculations
- Each call to `computeValidatorUptime` can lose up to `elapsedEpochs - 1` seconds

This truncation could become a serious issue in edge cases where the uptime is close to the minimum uptime threshold to qualify for rewards. If the truncated uptime is even 1 second less than `minRequiredTime`, the entire rewards for the validator become zero for that epoch.

```solidity
//Rewards.sol
function _calculateOperatorShare(uint48 epoch, address operator) internal {
    uint256 uptime = uptimeTracker.operatorUptimePerEpoch(epoch, operator);
    if (uptime < minRequiredUptime) {
        operatorBeneficiariesShares[epoch][operator] = 0;  // @audit no rewards
        operatorShares[epoch][operator] = 0;
        return;
    }
    // ... calculate rewards normally
}
```
**Impact:** Precision loss due to integer division can make a validator lose entire rewards for an epoch in certain edge cases.

**Proof of Concept:** Add the test to `UptimeTrackerTest.t.sol`

```solidity
 function test_UptimeTruncationCausesRewardLoss() public {


        uint256 MIN_REQUIRED_UPTIME = 11_520;

        console2.log("Minimum required uptime per epoch:", MIN_REQUIRED_UPTIME, "seconds");
        console2.log("Epoch duration:", EPOCH_DURATION, "seconds");

        // Demonstrate how small time lost can have big impact
        uint256 totalUptime = (MIN_REQUIRED_UPTIME * 3) - 2; // 34,558 seconds across 3 epochs
        uint256 elapsedEpochs = 3;
        uint256 uptimePerEpoch = totalUptime / elapsedEpochs; // 11,519 per epoch
        uint256 remainder = totalUptime % elapsedEpochs; // 2 seconds lost

        console2.log("3 epochs scenario:");
        console2.log("  Total uptime:", totalUptime, "seconds (9.6 hours!)");
        console2.log("  Epochs:", elapsedEpochs);
        console2.log("  Per epoch after division:", uptimePerEpoch, "seconds");
        console2.log("  Lost to truncation:", remainder, "seconds");
        console2.log("  Result: ALL 3 epochs FAIL threshold!");


        // Verify
        assertFalse(uptimePerEpoch >= MIN_REQUIRED_UPTIME, "Fails threshold due to truncation");
    }
```

**Recommended Mitigation:** Consider distributing the remaining uptime either evenly to as many epochs as possible or simply distribute it to the latest epoch.

**Suzaku:**
Fixed in commit [6c37d1c](https://github.com/suzaku-network/suzaku-core/pull/155/commits/6c37d1c3791565fcdf6e097e0587d956ac68f676).

**Cyfrin:** Verified.

## [M-5] Inconsistent Price Reference Used for Trade Execution Logic in `new_spot_order` and `swap`
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The `new_spot_order` and `swap` functions use different methods to obtain the reference price (`px`) for determining whether orders should execute, which creates inconsistency in the codebase.


In `src/program/processor/new_spot_order.rs`:
```rust
let px = engine.market_px();
```

In `src/program/processor/swap.rs`:
```rust
let px = engine.state.header.last_px;
```

In `src/program/processor/spot_quotes_replace.rs`:
```rust
let px = engine.state.header.last_px;
```

**Difference:**

The `market_px()` function (lines 1898-1906 in `engine.rs`) returns:
- `best_ask` if `best_ask < last_px`
- `best_bid` if `best_bid > last_px`
- `last_px` otherwise

This means `market_px()` may return an order book price (`best_ask` or `best_bid`) rather than the actual last traded price (`last_px`).

**Impact:** While both functions use `|| engine.cross(...)` as a fallback, the different `px` values may not directly cause security vulnerabilities, it may lead to subtle behavioral differences since:

- The `px` value is passed to `drv_update`, which uses it for fixing price calculations.
- Also, the `px` value is passed to `write_last_tokens`, which uses it to set `last_close` and `day_low` when crossing day boundaries.

**Recommended Mitigation:** Standardize the price reference across all spot trading functions.

**Deriverse:** Fixed in commit [f7e57dc](https://github.com/deriverse/protocol-v1/commit/f7e57dcf4bac3b7ec6bf4fdc07198abb7a9a443e).

**Cyfrin:** Verified

## [M-6] Margin call limit bypass
- Severity: `Medium`
- Source report: `dex.md`

### Detailed Content (from source)
**Description:** The limit check for margin calls can be bypassed, allowing the total number of margin calls to exceed `MAX_MARGIN_CALL_TRADES`.

The issue occurs because after the first `check_{short,long}_margin_call`, the trade counter is reset in next `check_{short,long}_margin_call` tha allow to execute additional trades beyond the intended limit.

Example:
`MAX_MARGIN_CALL_TRADES` is set to 10.
`check_short_margin_call` returns 9 (meaning 9 margin calls were executed).
Since 9 < 10, `check_long_margin_call` is then called.
`check_long_margin_call` executes an additional 10 margin calls.

As a result, a total of 9 + 10 = 19 margin calls are executed, which exceeds the intended limit of 10.

**Impact:** The `MAX_MARGIN_CALL_TRADES` limit can be exceeded, which may also lead to more execution costs.

**Recommended Mitigation:** Track the cumulative margin-call count across both functions and compare it to MAX_MARGIN_CALL_TRADES before executing any additional margin calls.

**Deriverse:** Fixed in commit [4f7bc8](https://github.com/deriverse/protocol-v1/commit/4f7bc8ac68325aa93b339ff91c0ac794ea17ffd9).

**Cyfrin:** Verified.

## [M-7] Incorrect link to Angle contracts across protocol
- Severity: `Medium`
- Source report: `parallel3.1.md`

### Detailed Content (from source)
**Description:** Parallelizer protocol is fork of Angle, it always refers origin implementation. However link pattern doesn't work anymore. It uses `parallelizer` folder, however there is no such folder in Angle's GitHub.
```solidity
/// @dev This contract is an authorized fork of Angle's `AccessControlModifiers` contract
/// https://github.com/AngleProtocol/angle-transmuter/blob/main/contracts/parallelizer/facets/AccessControlModifiers.sol
```

**Recommended Mitigation:** Update folder name from `parallelizer` to `transmuter` in all such links to make them work. It should be done across all forked contracts.

**Parallel:** Fixed in commit [08bc292](https://github.com/parallel-protocol/parallel-parallelizer/commit/08bc292d52bee8505e6f67883b3059e8faf1696f).

## [M-8] `AtomicBatcher` uses placeholder ERC-7201 namespace
- Severity: `Medium`
- Source report: `pr50.md`

### Detailed Content (from source)
**Description:** `AtomicBatcher` derives its nonce storage slot from an ERC-7201 namespace constant that is still a placeholder:

```solidity
/// @notice ERC-7201 namespace for nonce storage
string private constant _NAMESPACE = "<namespace>";
```

If this is not replaced with a unique, project-specific namespace, different contracts/tools that reuse the same placeholder can end up writing to the same storage slot.

**Impact:** Nonce storage can collide with other code using the same placeholder namespace, potentially breaking replay protection (unexpected nonce changes), causing failed executions, or enabling cross-application interference when running in shared storage contexts (e.g., EIP-7702 style execution in an EOA’s storage).

**Recommended Mitigation:** Replace `"<namespace>"` with a unique, stable identifier (e.g., `"accountable.atomicbatcher.nonce.v1"`), and treat it as immutable across upgrades/deployments.

**Accountable:** Fixed in commit [`2247cec`](https://github.com/Accountable-Protocol/credit-vaults-internal/commit/2247cec53a91ccc8f2d47d6d976d99308d676b85)

**Cyfrin:** Verified. Namespace is now `accountable.atomicbatcher.nonce.v1`.

## [M-9] Native token transfers lack explicit balance check
- Severity: `Medium`
- Source report: `spingame.md`

### Detailed Content (from source)
**Description:** One possible prize type is native tokens, represented by `tokenAddress = address(0)`. A user who wins native tokens can claim them in [`Spin::_transferPrize`](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L347-L352):

```solidity
if (prize.tokenAddress == address(0)) {
    (bool success, ) = _winner.call{value: prize.amount}("");
    if (!success) {
        revert NativeTokenTransferFailed();
    }
} else {
```

For ERC20 prizes ([handled here](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L353-L362)) and ERC721 prizes ([handled here](https://github.com/Consensys/linea-hub/blob/295344925ec4321265f7cbac174fcf903b529a4e/contracts/src/Spin.sol#L369-L371)), the contract explicitly checks whether it has a sufficient balance or ownership of the token before proceeding with the transfer.

While the current implementation would still revert if the contract lacks the required native token balance, consider adding an explicit balance check for native tokens as it would provide consistency across all prize types and ensure uniform error messages, improving usability and debugging.

**Linea:** Fixed in commit [`7675766`](https://github.com/Consensys/linea-hub/commit/7675766ba45bd87888897ac130a587a45e47e96b)

**Cyfrin:** Verified.

## [M-11] Proxy reuse without implementation check inside `UnstakeCooldown` leads to execution on outdated/vulnerable logic
- Severity: `Medium`
- Source report: `tranches.md`

### Detailed Content (from source)
**Description:** The contract reuses old proxies from the user’s `UnstakeCooldown::proxiesPool` without verifying whether those proxies were created from the current implementation. Since a clone’s target implementation is permanently embedded in its bytecode, if the owner updates `implementations[token]` using the available `UnstakeCooldown::setImplementations`, any proxies already in a user’s pool will still delegate to the old implementation.

**Impact:** Users may continue operating through outdated or vulnerable implementations even after the owner updates `implementations`. This can cause:
- Inconsistent behavior across requests (some proxies use the new implementation, others use the old one).
- Security risks if the previous implementation contains a bug or vulnerability.
- Accounting or logic mismatches if old and new implementations are not compatible.

**Proof of Concept:**
1. Owner sets `implementations[token] = ImplV1`.
2. Alice makes two transfers, creating two proxies that point to `ImplV1`.
3. Owner later calls `setImplementations(token, ImplV2)`.
4. Some time passes, the two proxies pointing to `ImplV1` are available.
5. Alice makes another transfer. The contract pops a proxy from her pool and reuses it.
6. That proxy still delegates to `ImplV1`, even though `implementations[token]` is now `ImplV2`.

**Recommended Mitigation:** When reusing proxies, verify that the proxy’s implementation matches the current `implementations[token]`. If not, discard the old proxy and create a new one.

**Strata:**
Fixed in commit [ffbedf48d](https://github.com/Strata-Money/contracts-tranches/commit/ffbedf48d268f2617e189cddc1daa167220082b3) by implementing a validation to check if the current implementation for a token is different than the implementation that was used to create a proxy being reused. If so, then a new proxy is made with the new implementation, and the old proxy is discarded.

**Cyfrin:** Verified.

<!-- /Cyfrin Fixed Issues (Merged) -->
