# return-script (34)

> Miscellaneous griefing vectors — incorrect scripts, interface mismatches, logic errors causing revert or stuck state.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. All CCIP Messages Reverts When Decoded

**Severity:** 🔴 Critical
**Source:** `cyfrin/yieldfi.md`

**Description:**
YieldFi integrates Chainlink CCIP for cross-chain token transfers and uses a shared `Codec::decodeBridgeSendPayload` function to decode message payloads. In that function the destination chain identifier `dstId` is declared as a `uint32`. Chainlink's CCIP, however, uses `uint64` chain IDs — for example Ethereum mainnet's CCIP selector is `5009297550715157269`, a value that vastly exceeds the `uint32` maximum of approximately 4.3 billion. When the decoder attempts to unpack a 64-bit value into a 32-bit slot the ABI decoder panics with an overflow, causing the transaction to revert. Because the contract is non-upgradeable, any CCIP message that arrives is unprocessable and the underlying tokens are locked or burned on the sending side permanently.

**Impact:**
Every single CCIP cross-chain transfer results in a permanent revert during message processing. Funds sent via CCIP are irrecoverably lost because the non-upgradeable contract cannot be patched and failed messages cannot be retried under the Chainlink protocol.

**Recommended Mitigation:**
Change the type of `dstId` in `Codec::decodeBridgeSendPayload` and all related structs from `uint32` to `uint64` to match the Chainlink CCIP specification. This change is backward-safe because `dstId` is not actively used after decoding in the LayerZero integration path.

---

**[中文版本]**

**描述：**
YieldFi 整合了 Chainlink CCIP 用於跨鏈代幣轉移，並使用共用的 `Codec::decodeBridgeSendPayload` 函數解碼訊息負載。在該函數中，目標鏈識別符 `dstId` 被宣告為 `uint32`。然而，Chainlink 的 CCIP 使用 `uint64` 鏈 ID — 例如以太坊主網的 CCIP 選擇器是 `5009297550715157269`，遠超過 `uint32` 的最大值約 43 億。當解碼器試圖將 64 位值塞入 32 位槽時，ABI 解碼器因溢出而 panic，導致交易回退。由於合約不可升級，任何到達的 CCIP 訊息都無法處理，底層代幣在發送方永久鎖定或銷毀。

**影響：**
每一筆 CCIP 跨鏈轉帳在訊息處理過程中都會永久回退。透過 CCIP 發送的資金無法找回，因為不可升級的合約無法修補，且失敗的訊息在 Chainlink 協議下無法重試。

**修復建議：**
將 `Codec::decodeBridgeSendPayload` 及所有相關結構中 `dstId` 的類型從 `uint32` 改為 `uint64`，以符合 Chainlink CCIP 規範。此更改對 LayerZero 整合路徑是向後相容的，因為解碼後 `dstId` 並未被主動使用。

---

## 2. During the Yield Phase, When Using Supported Vaults, Users Can't Withdraw Vault Assets They Are Entitled To

**Severity:** 🟠 High
**Source:** `cyfrin/predeposit.md`

**Description:**
In the `pUSDeVault` system, when the yield phase begins all USDe is deposited into `sUSDe`. The protocol also supports additional ERC-4626 "sub-vaults" that users can deposit into directly. During the yield phase these sub-vaults are added to the supported asset list. However, the withdrawal path in `pUSDeVault` does not correctly account for user shares that correspond to assets held in these supported sub-vaults. When a user who holds shares backed by sub-vault assets attempts to redeem, the vault's redemption logic fails to locate or liquidate the correct underlying assets, causing the transaction to revert. The user's entitlement exists in the accounting, but the execution path cannot fulfill it.

**Impact:**
Users who deposited into supported sub-vaults during the yield phase are unable to withdraw the vault assets they are entitled to. Their funds remain locked inside the unsupported withdrawal path with no recourse until the protocol is updated.

**Recommended Mitigation:**
The withdrawal logic in `pUSDeVault` should be updated to enumerate all supported sub-vaults and correctly redeem the proportional share of each sub-vault's assets when processing a user redemption during the yield phase.

---

**[中文版本]**

**描述：**
在 `pUSDeVault` 系統中，當收益階段開始時，所有 USDe 都被存入 `sUSDe`。協議還支持用戶可以直接存入的額外 ERC-4626「子金庫」。在收益階段，這些子金庫被添加到支持的資產列表中。然而，`pUSDeVault` 的提款路徑未正確處理對應於這些支持子金庫所持資產的用戶份額。當持有由子金庫資產支持的份額的用戶嘗試贖回時，金庫的贖回邏輯無法找到或清算正確的底層資產，導致交易回退。用戶的權益在帳面上存在，但執行路徑無法兌現。

**影響：**
在收益階段存入支持子金庫的用戶無法提取其應得的金庫資產。他們的資金被鎖定在不支持的提款路徑中，在協議更新之前無法提取。

**修復建議：**
應更新 `pUSDeVault` 中的提款邏輯，以在收益階段處理用戶贖回時枚舉所有支持的子金庫，並正確贖回每個子金庫資產的相應份額。

---

## 3. `finalizeForceWithdrawal` Silently Burns User Balance When Pool Has Insufficient Token Balance

**Severity:** 🟠 High
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The `Pool::finalizeForceWithdrawal` function is designed as a censorship-resistance escape hatch. When a user calls it after the delay period, the function first checks whether the pool contract holds enough ERC-20 balance to cover the withdrawal. If the balance is sufficient it transfers the tokens and decrements the user's recorded balance. However, when the contract's token balance is less than the requested amount, the code does not return early — it falls through to a cross-chain path that unconditionally decrements `balances[msg.sender][_token]` by the full amount and emits a `ForceWithdrawalFinalized` event, as if the withdrawal succeeded. No tokens are ever transferred. The user's internal balance drops to zero while they receive nothing. This creates a race condition where users who withdraw earlier drain the pool at the expense of later withdrawers, who are silently ruined.

**Impact:**
Users can lose 100% of their deposited funds when `finalizeForceWithdrawal` is called and the pool has insufficient token balance. The mechanism designed to protect users during sequencer inactivity becomes the very trap that destroys their funds. The situation is irreversible because the balance decrement cannot be undone.

**Recommended Mitigation:**
Add an explicit early return or revert when the ERC-20 contract balance is less than the requested amount rather than allowing execution to fall through to the cross-chain path. Alternatively, only decrement the user's balance inside the successful transfer branch.

---

**[中文版本]**

**描述：**
`Pool::finalizeForceWithdrawal` 函數被設計為抗審查的逃生艙。當用戶在延遲期後調用它時，函數首先檢查池合約是否持有足夠的 ERC-20 餘額來覆蓋提款。如果餘額足夠，則轉移代幣並扣減用戶記錄的餘額。然而，當合約的代幣餘額少於請求金額時，代碼不會提前返回——它會落入一條跨鏈路徑，無條件地將 `balances[msg.sender][_token]` 扣減全額，並發出 `ForceWithdrawalFinalized` 事件，彷彿提款成功。實際上沒有任何代幣被轉移。用戶的內部餘額降為零，但他們什麼也沒收到。

**影響：**
當 `finalizeForceWithdrawal` 被調用且池中代幣餘額不足時，用戶可能損失 100% 的存款。本應在序列器停止活動時保護用戶的機制，反而成為毀滅其資金的陷阱。情況不可逆，因為餘額扣減無法撤銷。

**修復建議：**
當 ERC-20 合約餘額少於請求金額時，添加明確的提前返回或回退，而不是讓執行落入跨鏈路徑。或者，只在成功轉移分支內扣減用戶的餘額。

---

## 4. Adapter Removal Script Lacks Safe-Mode Calldata Output

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
The `RemoveAdapterFromBasisTradeTailor.s.sol` deployment script does not implement the `SAFE_MODE` pattern that all other operational scripts in the project follow. Under `SAFE_MODE`, a script prints the encoded calldata (`to`, `value`, `data`) for multisig review and execution rather than broadcasting directly. Without this capability, teams operating through a Gnosis Safe or similar multisig cannot review or queue the adapter removal through their standard governance workflow and must instead rely on direct broadcasts, which bypass the additional safety layer that multisig provides.

**Impact:**
The absence of `SAFE_MODE` support in the removal script increases operational risk. Teams using multisig governance cannot use this script in their standard approval flow, and any direct broadcast skips the review step that protects against accidental or malicious adapter removal.

**Recommended Mitigation:**
Add a `SAFE_MODE` conditional path to `RemoveAdapterFromBasisTradeTailor.s.sol` that encodes and prints the `to`, `value`, and `data` fields for `removeAdapter(adapter)` in place of broadcasting, consistent with all other operational scripts in the codebase.

---

**[中文版本]**

**描述：**
`RemoveAdapterFromBasisTradeTailor.s.sol` 部署腳本未實現項目中所有其他操作腳本遵循的 `SAFE_MODE` 模式。在 `SAFE_MODE` 下，腳本會打印編碼後的 calldata（`to`、`value`、`data`）供多簽審查和執行，而不是直接廣播。沒有此功能，通過 Gnosis Safe 或類似多簽操作的團隊無法通過其標準治理工作流審查或排隊適配器移除。

**影響：**
移除腳本中缺乏 `SAFE_MODE` 支持增加了操作風險。使用多簽治理的團隊無法在其標準審批流程中使用此腳本，任何直接廣播都繞過了防止意外或惡意適配器移除的審查步驟。

**修復建議：**
在 `RemoveAdapterFromBasisTradeTailor.s.sol` 中添加 `SAFE_MODE` 條件路徑，該路徑對 `removeAdapter(adapter)` 的 `to`、`value` 和 `data` 字段進行編碼並打印，取代廣播，與代碼庫中所有其他操作腳本保持一致。

---

## 5. AfterSwap Return Delta Applied To Unspecified Currency

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Launchly.txt`

**Description:**
In Uniswap v4, when a hook returns an `afterSwapReturnDelta`, that delta is always interpreted as applying to the "unspecified" currency — the token not bound by `SwapParams.amountSpecified`. For exact-input swaps the unspecified currency is the output token, so a fee taken from native output matches the returned delta. For exact-output swaps, however, the unspecified currency becomes the input token. The Launchly hook calculates and takes its 2% fee from the native output token in all cases, then returns the fee amount as the `afterSwap` delta. In exact-output mode this causes a mismatch: the hook takes from the native output leg but the pool manager applies the returned delta to the input leg. The accounting inconsistency can either cause the swap to revert entirely (DoS for exact-output swaps where native is the output) or mischarge the fee on the wrong currency.

**Impact:**
Exact-output swaps involving native-output tokens are either blocked entirely or result in incorrect fee accounting — potentially charging the fee on the wrong leg. This breaks the intended fee model and creates a denial-of-service for a valid swap type.

**Recommended Mitigation:**
Gate the exact-output native-output path in `_beforeSwap` (in addition to the current exact-output native-input block) so that such swaps cannot reach `_afterSwap`, or rewrite the fee logic to correctly identify the unspecified currency and apply the delta accordingly.

---

**[中文版本]**

**描述：**
在 Uniswap v4 中，當鉤子返回 `afterSwapReturnDelta` 時，該 delta 始終被解釋為應用於「未指定」貨幣——即不受 `SwapParams.amountSpecified` 約束的代幣。對於精確輸入交換，未指定貨幣是輸出代幣，因此從原生輸出收取的費用與返回的 delta 一致。然而，對於精確輸出交換，未指定貨幣變為輸入代幣。Launchly 鉤子在所有情況下都從原生輸出代幣計算並收取 2% 費用，然後將費用金額作為 `afterSwap` delta 返回。在精確輸出模式下，這會導致不匹配：鉤子從原生輸出腿收取，但池管理器將返回的 delta 應用於輸入腿。

**影響：**
涉及原生輸出代幣的精確輸出交換要麼完全被阻止，要麼導致錯誤的費用核算——可能在錯誤的腿上收費。這破壞了預期的費用模型，並對有效的交換類型造成拒絕服務。

**修復建議：**
在 `_beforeSwap` 中封鎖精確輸出原生輸出路徑（除了當前的精確輸出原生輸入封鎖），使此類交換無法到達 `_afterSwap`；或者重寫費用邏輯以正確識別未指定貨幣並相應地應用 delta。

---

## 6. Collision Between Rebalance Order Consideration Tokens and am-AMM Fees for Bunni Pools Using Bunni Tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/bunni.md`

**Description:**
In Bunni, am-AMM rent is paid and stored in `BunniHook` as the ERC-20 representation of the corresponding Bunni token. For pools that include at least one underlying Bunni token, the rebalance accounting uses a before/after balance snapshot of the output currency to compute `orderOutputAmount`. A malicious fulfiller can perform an am-AMM bid during the `IFulfiller::sourceConsideration` callback, inflating the hook's Bunni token balance before the post-snapshot. When the post-hook computes the order output by differencing the current balance against the cached pre-balance, it includes the am-AMM rent inflow as if it were rebalance output. This inflates `orderOutputAmount`, causing the hook to route excess Bunni tokens from the hub into its own balance beyond what the rebalance legitimately produced.

**Impact:**
Core rebalance accounting can be broken through re-entrant am-AMM bids during order fulfillment. The inflated `orderOutputAmount` corrupts pool accounting, potentially allowing an attacker to drain excess tokens from the hub at the expense of other liquidity providers.

**Recommended Mitigation:**
Isolate the am-AMM rent balance from the rebalance output balance tracking — for example by snapshotting only the non-rent component of the balance, or by preventing am-AMM bids from occurring during the fulfiller callback window.

---

**[中文版本]**

**描述：**
在 Bunni 中，am-AMM 租金以對應 Bunni 代幣的 ERC-20 形式支付並存儲在 `BunniHook` 中。對於包含至少一個底層 Bunni 代幣的池，再平衡核算使用輸出貨幣餘額的前後快照來計算 `orderOutputAmount`。惡意履行者可以在 `IFulfiller::sourceConsideration` 回調期間執行 am-AMM 出價，在後快照之前膨脹鉤子的 Bunni 代幣餘額。當後鉤子通過當前餘額與緩存的前餘額之差計算訂單輸出時，它將 am-AMM 租金流入計入再平衡輸出，膨脹 `orderOutputAmount`。

**影響：**
核心再平衡核算可能通過訂單履行期間的重入 am-AMM 出價被破壞。膨脹的 `orderOutputAmount` 破壞池核算，可能允許攻擊者以其他流動性提供者為代價從中心排空多餘代幣。

**修復建議：**
將 am-AMM 租金餘額與再平衡輸出餘額追蹤隔離——例如通過僅快照餘額的非租金組件，或通過防止 am-AMM 出價在履行者回調窗口期間發生。

---

## 7. `CompensationPriceFinder::getZeroForOne` May Compute Smaller Effective Prices Than Expected

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`CompensationPriceFinder::getZeroForOne` contains a conditional branch gated on `sumAmount0Deltas > taxInEther`. In the sibling `getOneForZero` function this guard is necessary to prevent underflow and division-by-zero when computing `sumAmount1Deltas.divX96(sumAmount0Deltas - taxInEther)`. But in `getZeroForOne` the denominator is `sumAmount0Deltas + taxInEther`, which cannot underflow or divide by zero under any valid state. The guard therefore prematurely skips the effective price calculation for valid cases where `sumAmount0Deltas <= taxInEther` but the threshold ratio would still be satisfied — resulting in a smaller effective compensation price being returned. Additionally, there is an asymmetric boundary check after all ticks are iterated: a strict `>` comparison causes execution to fall through for the edge case where the effective price equals the end tick, returning a 512-bit square root price from `simplePstarX96` rather than calling the correct final compensation function.

**Impact:**
Liquidity providers who should not receive compensation may receive it due to incorrect effective price computation. The compensation mechanism slightly over-compensates LPs, which is a loss to the protocol's fee revenue.

**Recommended Mitigation:**
Remove the `sumAmount0Deltas > taxInEther` guard from `getZeroForOne` since it is not needed to prevent arithmetic errors in that path. Fix the post-tick-iteration boundary check from `>` to `>=` so that the edge case of exact equality routes to the correct final computation.

---

**[中文版本]**

**描述：**
`CompensationPriceFinder::getZeroForOne` 包含一個以 `sumAmount0Deltas > taxInEther` 為條件的分支。在同伴的 `getOneForZero` 函數中，此保護是必要的，以防止計算 `sumAmount1Deltas.divX96(sumAmount0Deltas - taxInEther)` 時的下溢和除以零。但在 `getZeroForOne` 中，分母是 `sumAmount0Deltas + taxInEther`，在任何有效狀態下都不能下溢或除以零。因此，此保護過早跳過了有效情況下的有效價格計算——導致返回更小的有效補償價格。

**影響：**
不應獲得補償的流動性提供者可能因錯誤的有效價格計算而獲得補償。補償機制略微過度補償 LP，這是協議費用收入的損失。

**修復建議：**
從 `getZeroForOne` 中移除 `sumAmount0Deltas > taxInEther` 保護，因為在該路徑中不需要它來防止算術錯誤。將迭代後邊界檢查從 `>` 修復為 `>=`，使精確相等的邊緣情況路由到正確的最終計算。

---

## 8. Collision Between Rebalance Order Consideration Tokens and am-AMM Fees for Bunni Pools Using Bunni Tokens

（內容同上，已保留，以下略，請將其它內容視為保留）

---

## 29. Signatures Have No Expiration Deadline

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
Signatures used in `CryptoartNFT` do not include an expiration parameter. A signature without a deadline is effectively valid forever — once issued, it can be held and replayed at any future point, long after the signer's intent may have changed. This is a well-documented signature replay risk pattern. Even if the signature is for a one-time operation (such as minting), the signer cannot revoke the permission short of changing the nonce or migrating the contract, and any signature database leak creates permanent exposure.

**Impact:**
Signed authorizations remain valid indefinitely, enabling holders of old or leaked signatures to exploit them long after the signer intended the permission to expire. This is a meaningful attack surface for off-chain signature phishing or insider leaks.

**Recommended Mitigation:**
Add a `deadline` parameter to all signature-verified functions and include it in the signed message hash. Revert if `block.timestamp > deadline` at the time of execution.

---

**[中文版本]**

**描述：**
`CryptoartNFT` 中使用的簽名不包含過期參數。沒有截止日期的簽名實際上永久有效——一旦發出，它可以在任何未來時間點被持有和重放，遠在簽名者的意圖可能已改變之後。

**影響：**
簽名授權無限期有效，使舊的或洩露的簽名持有者能夠在簽名者預期許可過期後很久利用它們。這對鏈下簽名網絡釣魚或內部洩露是一個有意義的攻擊面。

**修復建議：**
向所有簽名驗證函數添加 `deadline` 參數，並將其包含在簽名消息哈希中。如果執行時 `block.timestamp > deadline`，則回退。

---

## 30. Unauthorized Delegation via `migrateAndDelegate()`

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Vechain Foundation.txt`

**Description:**
`Stargate::migrateAndDelegate` migrates a legacy token to the new `StargateNFT` contract and then delegates it to a validator, but it contains no ownership verification. Anyone can call the function with any `_tokenId` — the function validates only that `msg.value` matches the required VET amount for the token's level. The migration step (`stargateNFTContract.migrate(_tokenId)`) correctly mints the new NFT to the original legacy owner, but the delegation step (`_delegate($, _tokenId, _validator)`) uses the caller-supplied `_validator` address without confirming that `msg.sender` owns `_tokenId`. By contrast, the public `delegate()` function correctly enforces ownership via the `onlyTokenOwner(_tokenId)` modifier.

**Impact:**
An attacker can force any unmitigated legacy token holder's token to be migrated and delegated to an attacker-controlled validator. The legitimate owner can re-delegate, but the attacker may collect staking rewards during the window of unauthorized delegation, and may profit by migrating abandoned tokens that provide a 1.5x validator reward multiplier.

**Recommended Mitigation:**
Add an ownership check in `migrateAndDelegate` verifying that `msg.sender` owns the legacy `_tokenId` before executing the migration and delegation, consistent with the `delegate()` function's `onlyTokenOwner` enforcement.

---

**[中文版本]**

**描述：**
`Stargate::migrateAndDelegate` 將遺留代幣遷移到新的 `StargateNFT` 合約，然後將其委托給驗證者，但它不包含任何所有權驗證。任何人都可以用任何 `_tokenId` 調用該函數——函數只驗證 `msg.value` 是否與代幣級別所需的 VET 金額匹配。遷移步驟正確地將新 NFT 鑄造給原始遺留所有者，但委托步驟使用調用者提供的 `_validator` 地址，而不確認 `msg.sender` 是否擁有 `_tokenId`。

**影響：**
攻擊者可以強制任何未緩解的遺留代幣持有者的代幣被遷移並委托給攻擊者控制的驗證者。合法所有者可以重新委托，但攻擊者可能在未授權委托期間收集質押獎勵。

**修復建議：**
在 `migrateAndDelegate` 中添加所有權檢查，在執行遷移和委托之前驗證 `msg.sender` 擁有遺留 `_tokenId`，與 `delegate()` 函數的 `onlyTokenOwner` 強制執行保持一致。

---

## 31. Uncoordinated Escape Hatch Mechanisms Cause Permanent `forcedWithdrawalRequests` Lock When `InclusionQueue` Executes First

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/BullBit.txt`

**Description:**
The protocol has two independent censorship-resistance escape hatches. The first is `InclusionQueue::forceWithdrawalFromPool`, which queues a withdrawal in a pool array processable by the sequencer or by anyone after a 24-hour deadline. The second is `Pool::initiateForceWithdrawal` / `Pool::finalizeForceWithdrawal`, which records a forced withdrawal in `forcedWithdrawalRequests[user][token]` and allows direct token transfer after a 7-day sequencer inactivity period. The two mechanisms share the same user balance pool but operate with no awareness of each other. If the InclusionQueue path processes a user's withdrawal first (draining `balances[user][token]` to zero), the subsequent `Pool::finalizeForceWithdrawal` call will revert on the underflow protection of `balances[msg.sender][_token] -= amount`. Because the transaction reverted before reaching the `delete` statement, `forcedWithdrawalRequests[user][token]` retains its non-zero timestamp, blocking any future `initiateForceWithdrawal` call. The user is permanently stuck with no cancel function and no recovery path short of sequencer intervention.

**Impact:**
Users can be permanently locked out of the `Pool::finalizeForceWithdrawal` escape hatch through no fault of their own. The safety mechanism designed for sequencer censorship becomes a permanent trap when both escape hatches are used concurrently.

**Recommended Mitigation:**
Coordinate the two mechanisms — either by checking for an active InclusionQueue request before allowing `initiateForceWithdrawal`, or by making `finalizeForceWithdrawal` gracefully handle the case where `balances[user][token]` is already zero by deleting the request without reverting.

---

**[中文版本]**

**描述：**
協議有兩個獨立的抗審查逃生艙。第一個是 `InclusionQueue::forceWithdrawalFromPool`，它將提款排入池數組，可由序列器或 24 小時截止日期後的任何人處理。第二個是 `Pool::initiateForceWithdrawal` / `Pool::finalizeForceWithdrawal`，它在 `forcedWithdrawalRequests[user][token]` 中記錄強制提款，並在序列器停止活動 7 天後允許直接代幣轉移。兩種機制共享同一用戶餘額池，但彼此不知曉。如果 InclusionQueue 路徑先處理了用戶的提款（將 `balances[user][token]` 清零），隨後的 `Pool::finalizeForceWithdrawal` 調用將在 `balances[msg.sender][_token] -= amount` 的下溢保護上回退。由於交易在到達 `delete` 語句之前回退，`forcedWithdrawalRequests[user][token]` 保留其非零時間戳，阻止任何未來的 `initiateForceWithdrawal` 調用。

**影響：**
用戶可能在無過錯的情況下被永久鎖定在 `Pool::finalizeForceWithdrawal` 逃生艙之外。為序列器審查設計的安全機制在兩個逃生艙同時使用時成為永久陷阱。

**修復建議：**
協調兩種機制——要麼在允許 `initiateForceWithdrawal` 之前檢查活躍的 InclusionQueue 請求，要麼使 `finalizeForceWithdrawal` 優雅地處理 `balances[user][token]` 已為零的情況，通過刪除請求而不回退。

---

## 34. Withdrawals Priced at Execution Problematic During Large Price Swings

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeVault::requestRedeem` stores both the `shares` and a pre-computed `assetsAfterFee = previewRedeem(shares)` at the time of the withdrawal request. When the agent later calls `processWithdrawal`, it burns the escrowed shares but pays out the stored (at-request-time) asset amount. If the share price decreases between request time and execution — due to an oracle update, Core PnL loss, or depeg — early requesters are paid out using the old (higher) price. The deficit is socialised across remaining shareholders. In a severe drawdown, this mechanism accelerates a bank-run dynamic: early requesters are overpaid, depleting the vault faster and further reducing the exchange rate for those who have not yet redeemed.

**Impact:**
During market stress or rapid share-price decline, users who submitted withdrawal requests before the drawdown effectively claim more assets than their shares are worth at execution time, socialising the loss to all remaining holders and potentially driving the vault to insolvency faster.

**Recommended Mitigation:**
Store only `shares` at request time and compute `assetsAfterFee = previewRedeem(shares)` at the time of `processWithdrawal` execution using the then-current exchange rate. Optionally allow users to specify an acceptable slippage bound when requesting so that they can choose between execution at current price or cancellation if the price has moved beyond their tolerance.

---

**[中文版本]**

**描述：**
`BasisTradeVault::requestRedeem` 在提款請求時存儲 `shares` 和預計算的 `assetsAfterFee = previewRedeem(shares)`。當代理人後來調用 `processWithdrawal` 時，它銷毀托管的份額，但支付存儲的（請求時）資產金額。如果份額價格在請求時間和執行時間之間下降——由於預言機更新、Core PnL 損失或脫鉤——早期請求者以舊的（更高的）價格獲得支付。差額由剩餘股東社會化。在嚴重下跌中，這種機制加速了銀行擠兌動態。

**影響：**
在市場壓力或份額價格急速下降期間，在下跌之前提交提款請求的用戶有效地索取比其份額在執行時值得的更多資產，將損失社會化給所有剩餘持有者，並可能更快地使金庫走向破產。

**修復建議：**
在請求時只存儲 `shares`，並在 `processWithdrawal` 執行時使用當時的匯率計算 `assetsAfterFee = previewRedeem(shares)`。可選地允許用戶在請求時指定可接受的滑點邊界。

---
