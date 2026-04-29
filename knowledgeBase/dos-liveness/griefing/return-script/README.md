# return-script (39)

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

## 6. `BasisTradeTailor::transferPerp` Comment Mismatch

**Severity:** 🟡 Medium
**Source:** `cyfrin/update.md`

**Description:**
The NatSpec comment on `BasisTradeTailor::transferPerp` reads "agent only", yet the function is guarded by the `onlyEngine` modifier, which restricts calls to addresses holding `ENGINE_ROLE`. The agent role and engine role are distinct — an agent cannot call this function. The discrepancy between the comment and the actual modifier means that developers, auditors, or integrators reading the documentation will have a false understanding of who can invoke this function, potentially leading to incorrect access-control reasoning or wasted troubleshooting effort.

**Impact:**
Misleading documentation can cause incorrect assumptions about the access model. While the implementation itself is likely correct, the comment divergence increases the maintenance risk and may cause incorrect integration decisions.

**Recommended Mitigation:**
Update the NatSpec comment from "(agent only)" to "(engine only)" to accurately reflect the `onlyEngine` modifier used on the function.

---

**[中文版本]**

**描述：**
`BasisTradeTailor::transferPerp` 的 NatSpec 注釋寫著「僅限代理人（agent only）」，然而該函數受 `onlyEngine` 修飾符保護，將調用限制為持有 `ENGINE_ROLE` 的地址。代理人角色和引擎角色是不同的——代理人無法調用此函數。注釋與實際修飾符之間的差異意味著閱讀文檔的開發者、審計員或集成者對誰可以調用此函數會有錯誤的理解。

**影響：**
誤導性文檔可能導致對訪問模型的錯誤假設。雖然實現本身可能是正確的，但注釋差異增加了維護風險，可能導致不正確的集成決策。

**修復建議：**
將 NatSpec 注釋從「(agent only)」更新為「(engine only)」，以準確反映函數上使用的 `onlyEngine` 修飾符。

---

## 7. Cap Semantics Mismatch: `_cap` Enforces Live Supply, Not Lifetime Issuance

**Severity:** 🟡 Medium
**Source:** `sherlockPDFTXT/Fluent (2).txt`

**Description:**
`BlendToken` enforces its `_cap` by checking `totalSupply() + amount > _cap` in both `mint` and `mintBatch`. Because burn operations reduce `totalSupply()`, minters can repeatedly mint up to the cap, burn tokens, then mint again. The cumulative number of tokens ever minted therefore exceeds `_cap` indefinitely. The protocol's intended tokenomics explicitly specify that `_cap` should be a lifetime issuance ceiling — "never mint more than X cumulatively" — but the current implementation only enforces it as a maximum live supply at any given moment.

**Impact:**
The tokenomics invariant is broken. Minters can issue far more than the nominal cap over time by cycling mint-and-burn operations, undermining the scarcity model and potentially enabling economic manipulation or trust erosion.

**Recommended Mitigation:**
Introduce a separate `mintedTotal` counter that is incremented on every mint but never decremented by burns. Replace the `totalSupply()` check with a check against `mintedTotal`, so the cap enforces lifetime issuance rather than live supply.

---

**[中文版本]**

**描述：**
`BlendToken` 在 `mint` 和 `mintBatch` 中通過檢查 `totalSupply() + amount > _cap` 來強制執行其 `_cap`。由於銷毀操作會減少 `totalSupply()`，鑄造者可以反復鑄造至上限、銷毀代幣、然後再次鑄造。因此，曾經鑄造的代幣累積數量無限期地超過 `_cap`。協議的預期代幣經濟學明確規定 `_cap` 應是終身發行上限——「永遠不要累積鑄造超過 X」——但當前實現僅將其作為任意時刻的最大流通供應量強制執行。

**影響：**
代幣經濟學不變量被打破。鑄造者可以通過循環鑄造和銷毀操作，隨時間發行遠超名義上限的代幣，破壞稀缺性模型，並可能實現經濟操縱或侵蝕信任。

**修復建議：**
引入一個單獨的 `mintedTotal` 計數器，在每次鑄造時遞增但不因銷毀而遞減。將 `totalSupply()` 檢查替換為對 `mintedTotal` 的檢查，使上限強制終身發行而非流通供應。

---

## 8. Chainlink Router Configured Twice

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
`BridgeCCIP` maintains its own mutable `router` storage slot that can be updated by the admin via `setRouter`. This `router` is used when sending CCIP messages. However, `BridgeCCIP` also inherits from `CCIPReceiver`, which stores an immutable `i_ccipRouter` set at construction time and used to validate that incoming messages originate from the authorised router. If an admin updates `BridgeCCIP.router` to a new address — for example during a Chainlink router upgrade — the contract will send through the new router but continue receiving from the original immutable router. This split-brain state means cross-chain communication either breaks silently (messages rejected on receive) or the dual-router setup creates confusion about the canonical router address.

**Impact:**
After any admin router update the contract enters an inconsistent state: outbound messages use the new router while inbound messages are only accepted from the old immutable one. Cross-chain functionality becomes unreliable and may silently fail.

**Recommended Mitigation:**
Remove the redundant `router` storage slot and `setRouter` function from `BridgeCCIP`. Any router change requires redeployment regardless (since `i_ccipRouter` is immutable), so the mutable slot provides no real benefit. Use `i_ccipRouter` exclusively for both send and receive paths.

---

**[中文版本]**

**描述：**
`BridgeCCIP` 維護自己的可變 `router` 存儲槽，管理員可以通過 `setRouter` 更新它。該 `router` 在發送 CCIP 訊息時使用。然而，`BridgeCCIP` 還繼承自 `CCIPReceiver`，它存儲一個在構造時設置的不可變 `i_ccipRouter`，用於驗證傳入訊息來自授權路由器。如果管理員更新 `BridgeCCIP.router` 到新地址——例如在 Chainlink 路由器升級期間——合約將通過新路由器發送，但繼續僅從原始不可變路由器接收。

**影響：**
任何管理員路由器更新後，合約進入不一致狀態：出站訊息使用新路由器，而入站訊息只接受來自舊不可變路由器的訊息。跨鏈功能變得不可靠，可能靜默失敗。

**修復建議：**
從 `BridgeCCIP` 中移除多餘的 `router` 存儲槽和 `setRouter` 函數。由於 `i_ccipRouter` 是不可變的，任何路由器更改無論如何都需要重新部署，因此可變槽不提供任何實際好處。對發送和接收路徑都專用 `i_ccipRouter`。

---

## 9. Check Return Value When Calling `Allowlist::exchangeAllowed` and `RemoraToken::_exchangeAllowed` to Prevent Unauthorized Transfers

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`Allowlist::exchangeAllowed` is a view function that reverts if either participant is unregistered but returns a boolean indicating whether a domestic-flag match exists when both are registered. `RemoraToken::adminTransferFrom` calls this function but discards its return value — the call is made purely for the revert-on-unregistered side effect without ever checking whether the domestic-flag condition also returned false. Similarly, `RemoraToken::transfer` and `transferFrom` call `RemoraToken::_exchangeAllowed` which wraps and returns the `Allowlist` result, but again the return value is never checked at the call site. Transfers therefore proceed even when both parties are registered but the domestic-flag criterion is not satisfied.

**Impact:**
Transfers that should be blocked by the allowlist's domestic-match condition are silently permitted. Compliance controls intended to restrict cross-jurisdiction transfers are ineffective.

**Recommended Mitigation:**
Check the boolean return value of `Allowlist::exchangeAllowed` and `RemoraToken::_exchangeAllowed` at every call site and revert when the result is false. Alternatively, change both functions to revert instead of returning false when the condition is not met, eliminating the need for callers to remember to check.

---

**[中文版本]**

**描述：**
`Allowlist::exchangeAllowed` 是一個視圖函數，如果任一參與者未注冊則回退，但當兩者都已注冊時返回一個布爾值，指示是否存在國內標誌匹配。`RemoraToken::adminTransferFrom` 調用此函數但丟棄其返回值——調用純粹是為了「未注冊時回退」的副作用，而從未檢查國內標誌條件是否也返回了 false。同樣，`RemoraToken::transfer` 和 `transferFrom` 調用 `RemoraToken::_exchangeAllowed`，它包裝並返回 `Allowlist` 結果，但調用點再次從未檢查返回值。

**影響：**
應被允許列表的國內匹配條件阻止的轉賬被靜默允許。旨在限制跨管轄區轉賬的合規控制無效。

**修復建議：**
在每個調用點檢查 `Allowlist::exchangeAllowed` 和 `RemoraToken::_exchangeAllowed` 的布爾返回值，並在結果為 false 時回退。或者，將兩個函數更改為在條件不滿足時回退而不是返回 false，消除調用者需要記住檢查的必要性。

---

## 10. Collision Between Rebalance Order Consideration Tokens and am-AMM Fees for Bunni Pools Using Bunni Tokens

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

## 11. `CompensationPriceFinder::getZeroForOne` May Compute Smaller Effective Prices Than Expected

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

## 12. Consider Using `SafeCast` When Downcasting Amounts

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
In `StakingVault`, the `underlyingAmount` field in the cooldowns mapping is typed as `uint152`. When assets are redeemed or deposited, the code adds the computed asset amount to `cooldowns[msg.sender].underlyingAmount` with an unsafe cast: `uint152(assetsRedeemed)`. If `assetsRedeemed` ever exceeds the `uint152` maximum (approximately 5.7 × 10^45 tokens), the cast silently truncates the value, recording a smaller cooldown amount than what was actually staked. The user would later be able to claim far less than what they deposited. OpenZeppelin's `SafeCast` library provides overflow-checked downcasts that revert rather than truncate.

**Impact:**
Silent truncation during downcasting would cause a discrepancy between actual deposited amounts and the tracked cooldown balance, resulting in user fund loss if a deposit is large enough to overflow `uint152`.

**Recommended Mitigation:**
Replace the bare `uint152(assetsRedeemed)` cast with `SafeCast.toUint152(assetsRedeemed)` throughout `StakingVault` to ensure all downcast operations are overflow-checked and revert on out-of-range values.

---

**[中文版本]**

**描述：**
在 `StakingVault` 中，冷卻期映射中的 `underlyingAmount` 字段被類型化為 `uint152`。當資產被贖回或存入時，代碼使用不安全的強制轉換將計算出的資產金額添加到 `cooldowns[msg.sender].underlyingAmount`：`uint152(assetsRedeemed)`。如果 `assetsRedeemed` 超過 `uint152` 最大值（約 5.7 × 10^45 個代幣），強制轉換會靜默截斷值，記錄比實際質押量小的冷卻金額。

**影響：**
強制轉換期間的靜默截斷會導致實際存款金額與追蹤的冷卻餘額之間的差異，如果存款足夠大以溢出 `uint152`，將導致用戶資金損失。

**修復建議：**
在整個 `StakingVault` 中用 `SafeCast.toUint152(assetsRedeemed)` 替換裸 `uint152(assetsRedeemed)` 強制轉換，以確保所有下轉換操作都有溢出檢查，並在超出範圍的值上回退。

---

## 13. Consider Using Exponential Notation in Tests

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
Test files frequently express decimal token amounts in the form `100 * 10**6`, which is syntactically verbose and prone to exponent or multiplier mistakes (e.g., accidentally writing `10**7` instead of `10**6`). Solidity supports scientific notation (`100e6`) which is more concise, immediately readable at a glance, and eliminates the risk of miscounting powers of ten. The codebase could benefit from a consistent style across all test files.

**Impact:**
Incorrect decimal amounts in tests could mask precision bugs, cause tests to silently pass at wrong magnitudes, or create misleading test coverage. The risk is low in isolation but compounds across a large test suite.

**Recommended Mitigation:**
Replace `amount * 10**decimals` expressions throughout test files with `amounte{decimals}` scientific notation for clarity and correctness.

---

**[中文版本]**

**描述：**
測試文件頻繁以 `100 * 10**6` 形式表達十進制代幣金額，語法冗長且容易出現指數或乘數錯誤（例如，意外寫 `10**7` 而非 `10**6`）。Solidity 支持科學計數法（`100e6`），更簡潔、一目了然，並消除了錯誤計算十的冪次的風險。

**影響：**
測試中不正確的十進制金額可能掩蓋精度錯誤，導致測試在錯誤的數量級下靜默通過，或造成誤導性的測試覆蓋率。

**修復建議：**
在整個測試文件中用 `amounte{decimals}` 科學計數法替換 `amount * 10**decimals` 表達式，以提高清晰度和正確性。

---

## 14. Consider Using Named Mapping Parameters

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
Solidity 0.8.18 introduced named mapping parameters, allowing key and value types to be annotated with descriptive identifiers that appear in source code and IDE tooling. None of the in-scope `MyriadCTFExchange` contracts use this feature. Mappings such as `mapping(bytes32 => bool) public noPositionsRedeemed`, `mapping(bytes32 => uint256) public mintedWcolPerEvent`, and `mapping(bytes32 => uint256) public filledAmounts` require developers to rely entirely on surrounding context — variable name, comments, or call sites — to understand what the key represents. Named parameters like `mapping(bytes32 eventId => bool)` make the semantic intent explicit at the declaration site.

**Impact:**
Reduced readability and maintainability increase the risk of incorrect usage — for example, accidentally passing an order hash where an event ID is expected. This is a code-quality issue without direct security impact.

**Recommended Mitigation:**
Apply named mapping parameters consistently across all in-scope contracts, annotating both key and value types with descriptive identifiers as shown in the Solidity 0.8.18 release notes.

---

**[中文版本]**

**描述：**
Solidity 0.8.18 引入了命名映射參數，允許用描述性標識符注釋鍵和值類型，這些標識符出現在源代碼和 IDE 工具中。範圍內的 `MyriadCTFExchange` 合約均未使用此功能。`mapping(bytes32 => bool) public noPositionsRedeemed` 等映射要求開發者完全依賴周圍上下文來理解鍵代表什麼。

**影響：**
可讀性和可維護性降低增加了不正確使用的風險——例如，意外地在期望事件 ID 的地方傳遞訂單哈希。這是一個代碼質量問題，沒有直接的安全影響。

**修復建議：**
在所有範圍內合約中一致應用命名映射參數，用描述性標識符注釋鍵和值類型。

---

## 15. Deploy Script `UpdateParallelizer.ts` Does Not Handle Facet Removal Case

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
The `UpdateParallelizer.ts` upgrade script identifies function selectors that need to be added (`FacetCutAction.Add`) or replaced (`Replace`) when upgrading a Diamond proxy, but it never generates `Remove` cut actions. When a facet is removed from the new implementation — meaning its selectors should no longer be routable through the Diamond — the missing `Remove` entries mean those selectors remain pointing at the old facet implementation after the upgrade. Users and integrators can still call the removed endpoints, which `delegatecall` into the deprecated or removed implementation, potentially executing logic that was intentionally disabled.

**Impact:**
Selectors intended to be removed after a Diamond upgrade remain callable, routing to old implementation logic. Depending on what those selectors do, this could range from redundant gas waste to execution of dangerous deprecated functionality.

**Recommended Mitigation:**
Extend `UpdateParallelizer.ts` to detect selectors present in the old facet but absent in the new one and generate corresponding `FacetCutAction.Remove` entries for the Diamond cut transaction.

---

**[中文版本]**

**描述：**
`UpdateParallelizer.ts` 升級腳本在升級 Diamond 代理時識別需要添加（`FacetCutAction.Add`）或替換（`Replace`）的函數選擇器，但從不生成 `Remove` 切割操作。當從新實現中移除一個 facet 時——意味著其選擇器不應再通過 Diamond 路由——缺失的 `Remove` 條目意味著這些選擇器在升級後仍然指向舊的 facet 實現。

**影響：**
打算在 Diamond 升級後移除的選擇器仍然可調用，路由到舊的實現邏輯。根據這些選擇器的功能，這可能從多餘的氣體浪費到執行有意禁用的危險廢棄功能。

**修復建議：**
擴展 `UpdateParallelizer.ts` 以檢測舊 facet 中存在但新 facet 中不存在的選擇器，並為 Diamond 切割交易生成相應的 `FacetCutAction.Remove` 條目。

---

## 16. Deployment Script Requires Unencrypted Private Key

**Severity:** 🟡 Medium
**Source:** `cyfrin/accountable.md`

**Description:**
The deployment scripts `FactoryScript.s.sol` and `FeeManagerScript.s.sol` retrieve the deployer private key via `vm.envUint("DEPLOYER_TESTNET_PK")` and pass it directly to `vm.startBroadcast`. Storing raw private keys in plain-text environment variables creates an operational security risk: the key can leak through version control (accidentally committed `.env` files), shell history files, CI/CD log output, misconfigured backup systems, or compromised developer machines. Foundry provides a secure alternative through its encrypted keystore mechanism, which stores keys encrypted at rest and decrypts them only at signing time.

**Impact:**
Exposure of the deployer private key allows an attacker to fully control the deployer account, enabling unauthorized contract deployments, configuration changes, or fund drains at the protocol level.

**Recommended Mitigation:**
Import the deployer key into a local Foundry keystore using `cast wallet import deployerKey --interactive`, then reference the keystore account in scripts via `--account deployerKey` and `vm.startBroadcast()` without any private key argument.

---

**[中文版本]**

**描述：**
部署腳本 `FactoryScript.s.sol` 和 `FeeManagerScript.s.sol` 通過 `vm.envUint("DEPLOYER_TESTNET_PK")` 獲取部署者私鑰，並直接傳遞給 `vm.startBroadcast`。將原始私鑰存儲在明文環境變量中會造成操作安全風險：密鑰可能通過版本控制（意外提交的 `.env` 文件）、Shell 歷史文件、CI/CD 日誌輸出、配置錯誤的備份系統或受感染的開發者機器洩露。

**影響：**
暴露部署者私鑰允許攻擊者完全控制部署者賬戶，從而在協議層面實現未授權的合約部署、配置更改或資金耗盡。

**修復建議：**
使用 `cast wallet import deployerKey --interactive` 將部署者密鑰導入本地 Foundry 密鑰庫，然後在腳本中通過 `--account deployerKey` 和不帶私鑰參數的 `vm.startBroadcast()` 引用密鑰庫賬戶。

---

## 17. `DocumentManager::hasSignedDocs` Incorrectly Returns `true` When There Are No Documents to Sign

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
`DocumentManager::hasSignedDocs` iterates over all document hashes and returns `(false, docHash)` as soon as it finds a document that requires a signature and has no record of the given signer having signed it. If the loop completes without finding such a document it returns `(true, 0x0)`. When the document list is empty (`numDocs == 0`), the loop body is never executed and the function falls straight through to `return (true, 0x0)`. This means the function reports that any user has signed all required documents even when the document registry is empty — a state where "no documents exist" is semantically different from "all documents have been signed."

**Impact:**
Upstream contracts that gate user actions on `hasSignedDocs` returning true will incorrectly permit those actions before any documents have been registered. Compliance workflows that depend on document signature verification are bypassed entirely when the document list is empty.

**Recommended Mitigation:**
Add an explicit check at the start of `hasSignedDocs` that returns `(false, bytes32(0))` when `numDocs == 0`, distinguishing the empty-document case from the all-signed case.

---

**[中文版本]**

**描述：**
`DocumentManager::hasSignedDocs` 遍歷所有文件哈希，一旦找到需要簽名但沒有給定簽名者已簽名記錄的文件，就返回 `(false, docHash)`。如果循環完成而未找到此類文件，則返回 `(true, 0x0)`。當文件列表為空時（`numDocs == 0`），循環體從未執行，函數直接落入 `return (true, 0x0)`。這意味著函數報告任何用戶已簽署所有必需文件，即使文件注冊表為空也是如此。

**影響：**
依賴 `hasSignedDocs` 返回 true 來限制用戶操作的上游合約將在任何文件注冊之前錯誤地允許這些操作。在文件列表為空時，依賴文件簽名驗證的合規工作流程完全被繞過。

**修復建議：**
在 `hasSignedDocs` 開頭添加明確的檢查，當 `numDocs == 0` 時返回 `(false, bytes32(0))`，區分空文件情況和全部已簽名情況。

---

## 18. `IBridgeableTokenP::swapLzTokenToPrincipalToken` Interface Declares a `uint256` Return Value but Implementation Returns Nothing

**Severity:** 🟡 Medium
**Source:** `cyfrin/parallel3.1.md`

**Description:**
The `IBridgeableTokenP` interface declares `swapLzTokenToPrincipalToken` with a `uint256` return type. The concrete implementation in `BridgeableTokenP` defines the same function with no return value — it is declared `external nonReentrant whenNotPaused` with no return statement. When any external contract holds a reference of type `IBridgeableTokenP` and calls this function, the caller's ABI decoder expects 32 bytes of return data. Since the implementation returns nothing, the decoder finds 0 bytes and reverts. Only contracts that bypass the interface and call the implementation address directly are unaffected.

**Impact:**
All external contracts and protocols that integrate with `BridgeableTokenP` through the `IBridgeableTokenP` interface will have their `swapLzTokenToPrincipalToken` calls revert, breaking cross-chain token swaps for all integrators.

**Recommended Mitigation:**
Either add a return value to the implementation — returning the amount of principal tokens credited — to match the interface declaration, or remove the return type from the interface declaration to match the implementation.

---

**[中文版本]**

**描述：**
`IBridgeableTokenP` 接口聲明 `swapLzTokenToPrincipalToken` 帶有 `uint256` 返回類型。`BridgeableTokenP` 中的具體實現定義了相同的函數但沒有返回值——它被聲明為 `external nonReentrant whenNotPaused` 且沒有 return 語句。當任何外部合約持有 `IBridgeableTokenP` 類型的引用並調用此函數時，調用者的 ABI 解碼器期望 32 字節的返回數據。由於實現不返回任何內容，解碼器找到 0 字節並回退。

**影響：**
所有通過 `IBridgeableTokenP` 接口與 `BridgeableTokenP` 集成的外部合約和協議的 `swapLzTokenToPrincipalToken` 調用將回退，為所有集成者破壞跨鏈代幣交換。

**修復建議：**
要麼向實現添加返回值——返回記入的本金代幣數量——以匹配接口聲明；要麼從接口聲明中刪除返回類型以匹配實現。

---

## 19. Only Update `deployedAssets` When `remaining > 0` in `AccountableYield::repay`

**Severity:** 🟡 Medium
**Source:** `cyfrin/pr50.md`

**Description:**
In `AccountableYield::repay`, the code reads the `deployedAssets` storage variable and unconditionally subtracts `Math.min(remaining, deployed)` from it, even when `remaining == 0`. When `remaining` is zero, `Math.min(0, deployed)` is zero, so the arithmetic produces no net change — but the storage read and write still occur. The immediately following `if (remaining > 0)` block only reduces outstanding principal when there is something to repay. The `deployedAssets` update should be gated by the same condition to avoid a no-op storage operation that wastes gas.

**Impact:**
Unnecessary SLOAD and SSTORE operations are executed every time `repay` is called with zero remaining, wasting approximately 2100 gas per SLOAD and 5000 gas per SSTORE. In a protocol with many loans this compounds meaningfully.

**Recommended Mitigation:**
Move the `deployedAssets` read and decrement inside the existing `if (remaining > 0)` block so that storage is only touched when an actual deduction is needed.

---

**[中文版本]**

**描述：**
在 `AccountableYield::repay` 中，代碼讀取 `deployedAssets` 存儲變量並無條件減去 `Math.min(remaining, deployed)`，即使當 `remaining == 0` 時也是如此。當 `remaining` 為零時，`Math.min(0, deployed)` 為零，因此算術不產生淨變化——但存儲讀取和寫入仍然發生。緊隨其後的 `if (remaining > 0)` 塊只在有要償還的東西時才減少未償還本金。

**影響：**
每次 `repay` 以零 remaining 調用時，都會執行不必要的 SLOAD 和 SSTORE 操作，浪費約 2100 gas（SLOAD）和 5000 gas（SSTORE）。在有許多貸款的協議中，這會顯著積累。

**修復建議：**
將 `deployedAssets` 的讀取和遞減移到現有的 `if (remaining > 0)` 塊內，以便只在需要實際扣減時才訪問存儲。

---

## 20. Order Not Eligible at `eligibleAt`

**Severity:** 🟡 Medium
**Source:** `cyfrin/yieldfi.md`

**Description:**
Both `PerpetualBond::executeOrder` and `Manager::executeOrder` include a time-based eligibility check: `require(block.timestamp > order.eligibleAt, "!waitingPeriod")`. The field name `eligibleAt` semantically indicates that the order becomes eligible at that exact timestamp. However, the strict-greater-than comparison `>` excludes the timestamp itself, meaning an order is not processable at the exact moment it should first become eligible — only one second later. This off-by-one error means users and keepers who attempt to execute at `eligibleAt` will be unexpectedly rejected.

**Impact:**
Orders cannot be executed at their exact `eligibleAt` timestamp. This is a minor UX issue but can create confusion for off-chain keepers and users who rely on the semantic meaning of the field name, potentially causing delayed order execution.

**Recommended Mitigation:**
Change `>` to `>=` in the eligibility check so that `block.timestamp >= order.eligibleAt` correctly permits execution at the intended boundary.

---

**[中文版本]**

**描述：**
`PerpetualBond::executeOrder` 和 `Manager::executeOrder` 都包含基於時間的資格檢查：`require(block.timestamp > order.eligibleAt, "!waitingPeriod")`。字段名稱 `eligibleAt` 在語義上表示訂單在該確切時間戳變得合格。然而，嚴格大於比較 `>` 排除了時間戳本身，意味著訂單在應該首次合格的確切時刻無法處理——只能在一秒後處理。

**影響：**
訂單無法在其確切的 `eligibleAt` 時間戳執行。這是一個輕微的用戶體驗問題，但可能對依賴字段名稱語義含義的鏈下保管者和用戶造成混淆，可能導致訂單執行延遲。

**修復建議：**
將資格檢查中的 `>` 更改為 `>=`，使 `block.timestamp >= order.eligibleAt` 正確允許在預期邊界執行。

---

## 21. `PledgeManager::refundTokens` Doesn't Decrement `tokensSold` When Pledge Hasn't Concluded

**Severity:** 🟡 Medium
**Source:** `cyfrin/pledge.md`

**Description:**
When a user calls `PledgeManager::refundTokens` before the pledge has concluded and before the deadline, the code applies an early-sell penalty, transfers the tokens back to the holder wallet, and emits `TokensUnPledged` — but it does not decrement `tokensSold`. By contrast, the post-deadline / post-conclusion branch correctly decrements `tokensSold`. This means that when a user exits early, the tokens they held are returned but the `tokensSold` counter remains inflated. Other users are therefore prevented from purchasing those same tokens because the counter makes the pledge appear fuller than it is, blocking the pledge from reaching its funding goal through secondary purchases.

**Impact:**
Early refunds artificially inflate `tokensSold`, reducing the apparent availability of tokens and making it harder for the pledge to reach its funding goal. Remaining pledgers and new investors may be unable to fill the funding gap.

**Recommended Mitigation:**
Move the `tokensSold -= numTokens` decrement outside the conditional branching so it executes in both the early-exit path and the post-deadline path, ensuring `tokensSold` accurately reflects the number of tokens currently committed.

---

**[中文版本]**

**描述：**
當用戶在認購尚未結束且未超過截止日期時調用 `PledgeManager::refundTokens` 時，代碼應用提前出售罰款，將代幣退還給持有人錢包，並發出 `TokensUnPledged` 事件——但它沒有遞減 `tokensSold`。相比之下，截止日期後/結束後的分支正確地遞減了 `tokensSold`。這意味著當用戶提前退出時，他們持有的代幣被返回，但 `tokensSold` 計數器仍然虛高。

**影響：**
提前退款人為虛高 `tokensSold`，減少代幣的表觀可用性，使認購更難達到融資目標。剩餘的認購者和新投資者可能無法填補融資缺口。

**修復建議：**
將 `tokensSold -= numTokens` 遞減移到條件分支之外，使其在提前退出路徑和截止日期後路徑中都執行，確保 `tokensSold` 準確反映當前承諾的代幣數量。

---

## 22. Prefer Explicit `uint` Sizes

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
Several contracts in the Syntetika system use the unqualified `uint` type (which aliases `uint256`) in loop variables, function parameters, and return values rather than explicitly writing `uint256`. While this compiles without error, the implicit alias reduces readability and can surprise readers who are less familiar with Solidity defaults. Consistent explicit sizing also makes storage layout reasoning more straightforward and reduces ambiguity during ABI encoding.

**Impact:**
Code-quality issue without direct security impact. Inconsistent typing practices increase the cognitive load for auditors and developers, slightly increasing the risk of overlooking real type-sizing issues in surrounding code.

**Recommended Mitigation:**
Replace all `uint` occurrences with `uint256` throughout the codebase for explicit and consistent type declarations.

---

**[中文版本]**

**描述：**
Syntetika 系統中的幾個合約在循環變量、函數參數和返回值中使用未限定的 `uint` 類型（它是 `uint256` 的別名），而不是明確地寫 `uint256`。雖然這可以無錯誤地編譯，但隱式別名降低了可讀性，可能讓不太熟悉 Solidity 默認值的讀者感到驚訝。

**影響：**
代碼質量問題，沒有直接安全影響。不一致的類型實踐增加了審計員和開發者的認知負擔。

**修復建議：**
在整個代碼庫中將所有 `uint` 替換為 `uint256`，以獲得明確且一致的類型聲明。

---

## 23. Prefer Explicit Unsigned Integer Sizes

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
Several contracts in the DSToken (Securitize) codebase declare loop counters as `uint i` rather than `uint256 i`, including `TrustService.sol`, `ComplianceConfigurationService.sol`, and `WalletManager.sol`. While functionally equivalent, the shorthand `uint` is an alias and deviates from best practices that call for explicit type sizes in all declarations. This inconsistency can create confusion for developers auditing storage layouts or performing ABI-level analysis.

**Impact:**
Code-quality issue without direct security impact. Consistency in type declarations reduces the chance of subtle misunderstandings about integer sizes in future code changes.

**Recommended Mitigation:**
Replace `uint i` with `uint256 i` in all loop variable declarations across the affected contracts.

---

**[中文版本]**

**描述：**
DSToken（Securitize）代碼庫中的幾個合約將循環計數器聲明為 `uint i` 而不是 `uint256 i`，包括 `TrustService.sol`、`ComplianceConfigurationService.sol` 和 `WalletManager.sol`。雖然在功能上等效，但簡寫 `uint` 是一個別名，偏離了在所有聲明中要求明確類型大小的最佳實踐。

**影響：**
代碼質量問題，沒有直接安全影響。類型聲明的一致性減少了在未來代碼更改中對整數大小產生微妙誤解的機會。

**修復建議：**
在受影響合約的所有循環變量聲明中，將 `uint i` 替換為 `uint256 i`。

---

## 24. Prefer Named Return Parameters, Especially for `memory` Returns

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
Functions in the `CryptoartNFT` contract that return memory types use unnamed return parameters paired with local variables and explicit `return` statements, rather than named return parameters. For example, `tokenURIs` declares `returns (uint256 index, string[2] memory uris, bool isPinned)` but still assigns local variables and returns them explicitly. Named return parameters eliminate the need for local variable declarations, reduce code size, and make the function signature self-documenting by expressing what each position in the return tuple represents.

**Impact:**
Code-quality issue without direct security impact. Unnamed memory returns add minor code bloat and reduce the expressiveness of function signatures.

**Recommended Mitigation:**
Refactor memory-returning functions to use named return parameters and assign directly to those names, removing the corresponding local variable declarations and explicit return statements.

---

**[中文版本]**

**描述：**
`CryptoartNFT` 合約中返回 memory 類型的函數使用未命名的返回參數配合局部變量和顯式 `return` 語句，而不是命名返回參數。命名返回參數消除了局部變量聲明的需要，減少了代碼大小，並通過表達返回元組中每個位置代表什麼使函數簽名自我說明。

**影響：**
代碼質量問題，沒有直接安全影響。未命名的 memory 返回增加了輕微的代碼膨脹並降低了函數簽名的表達力。

**修復建議：**
重構 memory 返回函數以使用命名返回參數，並直接分配給這些名稱，刪除相應的局部變量聲明和顯式 return 語句。

---

## 25. Refactor Duplicated Checks Into Modifiers

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
`YieldManager.sol` contains several checks that are repeated verbatim across multiple functions. The `msg.sender != L1_MESSAGE_SERVICE` guard appears in both `receiveFundsFromReserve` and `withdrawLST`. The `isWithdrawalReserveBelowMinimum()` check and its inverse appear in three and two functions respectively. The `isOssified` check for `AlreadyOssified` appears in `initiateOssification` and `progressPendingOssification`. Duplicated guards increase the maintenance burden — a change to the condition logic must be applied in multiple locations — and increase the surface area for future inconsistencies if one copy is updated but others are not.

**Impact:**
Code-quality issue. Duplicated guards create maintenance risk: future modifications to the condition may be applied inconsistently, leading to subtle access control or state validation bugs.

**Recommended Mitigation:**
Extract each repeated check into a named modifier (`onlyL1MessageService`, `onlyWhenReserveBelowMinimum`, `onlyWhenReserveNotInDeficit`, `onlyWhenNotOssified`) and replace the inline checks with those modifiers.

---

**[中文版本]**

**描述：**
`YieldManager.sol` 包含多個在不同函數中逐字重複的檢查。`msg.sender != L1_MESSAGE_SERVICE` 守衛出現在 `receiveFundsFromReserve` 和 `withdrawLST` 中。`isWithdrawalReserveBelowMinimum()` 檢查及其反向分別出現在三個和兩個函數中。`isOssified` 檢查出現在 `initiateOssification` 和 `progressPendingOssification` 中。重複的守衛增加了維護負擔——對條件邏輯的更改必須在多個位置應用。

**影響：**
代碼質量問題。重複的守衛造成維護風險：對條件的未來修改可能應用不一致，導致微妙的訪問控制或狀態驗證錯誤。

**修復建議：**
將每個重複的檢查提取到命名的修飾符中，並用這些修飾符替換內聯檢查。

---

## 26. Remove Obsolete `onlyTokenOwner` From `_transferToNftReceiver`

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
`CryptoartNFT::_transferToNftReceiver` carries an `onlyTokenOwner(tokenId)` modifier that checks whether `msg.sender` is the token owner before executing. However, the function body calls `ERC721Upgradeable::safeTransferFrom`, which internally calls `transferFrom`, which calls `_update` with `_msgSender()` as the `auth` parameter, which in turn calls `_checkAuthorized`. The `_checkAuthorized` function already verifies that the caller is either the owner or an approved operator via `_isAuthorized`. The `onlyTokenOwner` modifier therefore duplicates work already performed deeper in the call stack, and is more restrictive than necessary — it would reject calls from approved operators who should legitimately be able to trigger this transfer.

**Impact:**
Approved operators who have allowance to transfer a token but are not the owner cannot call `_transferToNftReceiver`, unnecessarily restricting the function's intended use. The redundant modifier also wastes gas.

**Recommended Mitigation:**
Remove the `onlyTokenOwner(tokenId)` modifier from `_transferToNftReceiver` and rely solely on the authorization checks already performed by `ERC721Upgradeable::safeTransferFrom`.

---

**[中文版本]**

**描述：**
`CryptoartNFT::_transferToNftReceiver` 帶有一個 `onlyTokenOwner(tokenId)` 修飾符，在執行之前檢查 `msg.sender` 是否是代幣所有者。然而，函數體調用 `ERC721Upgradeable::safeTransferFrom`，它內部調用 `transferFrom`，後者調用帶有 `_msgSender()` 作為 `auth` 參數的 `_update`，後者再調用 `_checkAuthorized`。`_checkAuthorized` 函數已經通過 `_isAuthorized` 驗證調用者是所有者還是批准的操作者。

**影響：**
具有轉移代幣許可但不是所有者的批准操作者無法調用 `_transferToNftReceiver`，不必要地限制了函數的預期使用。多餘的修飾符也浪費氣體。

**修復建議：**
從 `_transferToNftReceiver` 中刪除 `onlyTokenOwner(tokenId)` 修飾符，僅依靠 `ERC721Upgradeable::safeTransferFrom` 已執行的授權檢查。

---

## 27. Remove or Resolve TODO

**Severity:** 🟡 Medium
**Source:** `cyfrin/escrow.md`

**Description:**
`SablierBob.sol` contains a `TODO` comment on line 330 stating "transfer entire fee to comptroller admin instead of transferring when user redeems." This indicates an unresolved design decision about when and to whom protocol fees should be forwarded. Leftover `TODO` comments in production code are a code hygiene issue that signals incomplete implementation, potential discrepancies between the intended and actual fee-transfer behaviour, and increased audit surface area. In this specific case, the comment suggests the current fee handling may not match the intended design.

**Impact:**
The current fee-forwarding behaviour may deviate from what protocol designers intended. If the TODO describes a meaningful economic change (centralised vs deferred fee distribution), shipping without resolving it could result in unintended treasury distribution flows.

**Recommended Mitigation:**
Either implement the described fee-transfer approach — accumulating fees and forwarding them to the comptroller admin rather than per-user-redemption — or explicitly document (with a formal comment) that the current implementation is intentional and remove the TODO.

---

**[中文版本]**

**描述：**
`SablierBob.sol` 在第 330 行包含一個 `TODO` 注釋，內容為「將整個費用轉移給 comptroller 管理員，而不是在用戶贖回時轉移」。這表明關於何時以及向誰轉發協議費用的設計決策尚未解決。生產代碼中殘留的 `TODO` 注釋是代碼衛生問題，表明實現不完整。

**影響：**
當前的費用轉發行為可能偏離協議設計者的意圖。如果 TODO 描述了有意義的經濟變化（集中式與延遲費用分配），在不解決的情況下交付可能導致意外的財務分配流。

**修復建議：**
要麼實現描述的費用轉移方法——積累費用並轉發給 comptroller 管理員，而不是每次用戶贖回——要麼明確記錄當前實現是故意的並刪除 TODO。

---

## 28. Remove Return Value From `DSToken::updateInvestorBalance` as It Is Never Checked

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`DSToken::updateInvestorBalance` is an `internal` function that returns `bool`. None of the call sites in `DSToken.sol`, `TokenLibrary.sol`, or any mock contract ever check this return value. The function also has a misleading edge case: when `_wallet` does not belong to a registered investor, the update never happens but the function still returns `true` (the boolean default). This creates a silent no-op that callers could mistake for a successful update. The unchecked boolean return is a pattern that, if later promoted to an external function or relied upon by new code, could introduce real logic errors.

**Impact:**
The unused return value creates misleading contract behaviour (returning `true` on a no-op) and increases cognitive complexity. If future code starts checking the return value assuming `true` means "the update happened," it will incorrectly handle the case where the wallet is unregistered.

**Recommended Mitigation:**
Remove the `bool` return type from `DSToken::updateInvestorBalance` and all its overrides, or change the function to revert when the wallet is unregistered rather than silently returning `true`.

---

**[中文版本]**

**描述：**
`DSToken::updateInvestorBalance` 是一個返回 `bool` 的 `internal` 函數。`DSToken.sol`、`TokenLibrary.sol` 或任何模擬合約中的調用點都從未檢查此返回值。該函數還有一個誤導性的邊緣情況：當 `_wallet` 不屬於已注冊的投資者時，更新從不發生，但函數仍然返回 `true`（布爾默認值）。

**影響：**
未使用的返回值創造了誤導性的合約行為（在無操作時返回 `true`），並增加了認知複雜性。如果未來的代碼開始檢查返回值，假設 `true` 意味著「更新已發生」，它將錯誤地處理錢包未注冊的情況。

**修復建議：**
從 `DSToken::updateInvestorBalance` 及其所有重寫中刪除 `bool` 返回類型，或更改函數以在錢包未注冊時回退，而不是靜默返回 `true`。

---

## 29. Return Fast in `ComplianceServiceRegulated::checkHoldUp` If Platform Wallet

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceServiceRegulated::checkHoldUp` guards its body with `if (!_isPlatformWalletFrom)`, meaning the compliance checks only run for non-platform wallets. Platform wallets always return `false` (no hold-up). However the current structure wraps the entire substantive logic inside the `if (!_isPlatformWalletFrom)` block rather than returning immediately at the top when `_isPlatformWalletFrom` is true. This means the function performs unnecessary conditional branching and skips over complex service lookups. An early-return pattern would make the intent explicit and trivially skip all downstream logic.

**Impact:**
Minor gas inefficiency and reduced readability. The logic is correct but unnecessarily verbose, adding cognitive overhead when auditing the compliance service.

**Recommended Mitigation:**
Add `if (_isPlatformWalletFrom) return false;` at the top of the function body, removing the wrapping `if (!_isPlatformWalletFrom)` block and flattening the indentation level.

---

**[中文版本]**

**描述：**
`ComplianceServiceRegulated::checkHoldUp` 用 `if (!_isPlatformWalletFrom)` 守衛其函數體，意味著合規檢查只對非平台錢包運行。平台錢包始終返回 `false`（無阻擋）。然而，當前結構將整個實質性邏輯包裝在 `if (!_isPlatformWalletFrom)` 塊內，而不是在 `_isPlatformWalletFrom` 為 true 時立即在頂部返回。

**影響：**
輕微的氣體效率低下和可讀性降低。邏輯是正確的，但不必要地冗長，在審計合規服務時增加了認知開銷。

**修復建議：**
在函數體頂部添加 `if (_isPlatformWalletFrom) return false;`，刪除包裝的 `if (!_isPlatformWalletFrom)` 塊，並展平縮進級別。

---

## 30. `SDLVesting::withdrawRESDLPositions` Enhancements

**Severity:** 🟡 Medium
**Source:** `cyfrin/vesting.md`

**Description:**
`SDLVesting::withdrawRESDLPositions` violates the Checks-Effects-Interactions (CEI) pattern: it calls `sdlPool.safeTransferFrom` (an external call) before deleting `reSDLTokenIds[_lockTimes[i]]` from storage. While not currently exploitable due to `SDLPool`'s ownership checks, the external-call-before-state-change ordering creates a potential re-entrancy window. Additionally, the function lacks input validation for lock time values — if `_lockTimes[i]` exceeds `MAX_LOCK_TIME` the call will attempt to read a storage slot that holds no valid token ID, potentially causing a confusing revert during the subsequent transfer. Non-existent token IDs (zero values) are also not handled gracefully.

**Impact:**
The CEI violation creates a latent re-entrancy risk dependent on SDLPool ownership semantics. Invalid or out-of-range lock times cause unexpected transaction failures, degrading user experience and potentially locking beneficiaries out of their positions.

**Recommended Mitigation:**
Validate each `_lockTimes[i]` against `MAX_LOCK_TIME` and skip or revert on zero token IDs. Reorder the loop body so that `delete reSDLTokenIds[_lockTimes[i]]` executes before `sdlPool.safeTransferFrom` to follow CEI.

---

**[中文版本]**

**描述：**
`SDLVesting::withdrawRESDLPositions` 違反了檢查-效果-交互（CEI）模式：它在從存儲中刪除 `reSDLTokenIds[_lockTimes[i]]` 之前調用 `sdlPool.safeTransferFrom`（外部調用）。雖然由於 `SDLPool` 的所有權檢查目前無法利用，但外部調用在狀態更改之前的順序創造了潛在的重入窗口。此外，該函數缺乏對鎖定時間值的輸入驗證。

**影響：**
CEI 違規創造了依賴 SDLPool 所有權語義的潛在重入風險。無效或超出範圍的鎖定時間會導致意外的交易失敗，降低用戶體驗，並可能將受益人鎖定在其倉位之外。

**修復建議：**
根據 `MAX_LOCK_TIME` 驗證每個 `_lockTimes[i]`，並在零代幣 ID 上跳過或回退。重新排列循環體，使 `delete reSDLTokenIds[_lockTimes[i]]` 在 `sdlPool.safeTransferFrom` 之前執行，以遵循 CEI。

---

## 31. Scaling `winningThreshold` Incorrectly Reduces Randomness Distribution

**Severity:** 🟡 Medium
**Source:** `cyfrin/spingame.md`

**Description:**
In `Spin::_fulfillRandomness`, when a user's boost results in a total win probability greater than 100%, the contract scales the `winningThreshold` from the base-point range up to the `boostedTotalProbabilities` range. The current implementation does this by first reducing `_randomness` to the base-point range (`_randomness % BASE_POINT`) and then scaling the result upward (`winningThreshold * boostedTotalProbabilities / BASE_POINT`). This double transformation loses entropy: distinct values of `_randomness` that were distinguishable in the full random range collapse to the same post-modulo value and then scale to the same `winningThreshold`, reducing the effective randomness and potentially introducing bias in the win determination.

**Impact:**
The effective randomness distribution for boosted users is compressed, potentially making some outcomes more likely than intended. This biases the game's fairness for users with boosts exceeding 100%.

**Recommended Mitigation:**
When `boostedTotalProbabilities > BASE_POINT`, compute `winningThreshold = _randomness % boostedTotalProbabilities` directly, applying the modulo to the full randomness in one step without the intermediate base-point reduction.

---

**[中文版本]**

**描述：**
在 `Spin::_fulfillRandomness` 中，當用戶的助推導致總獲勝概率超過 100% 時，合約將 `winningThreshold` 從基礎點範圍放大到 `boostedTotalProbabilities` 範圍。當前實現通過先將 `_randomness` 降至基礎點範圍（`_randomness % BASE_POINT`），然後向上縮放結果（`winningThreshold * boostedTotalProbabilities / BASE_POINT`）來實現這一點。這種雙重轉換損失了熵：在完整隨機範圍內可區分的不同 `_randomness` 值在取模後折疊為相同的值，然後縮放為相同的 `winningThreshold`。

**影響：**
助推用戶的有效隨機性分佈被壓縮，可能使某些結果比預期更有可能。這使得助推超過 100% 的用戶的遊戲公平性產生偏差。

**修復建議：**
當 `boostedTotalProbabilities > BASE_POINT` 時，直接計算 `winningThreshold = _randomness % boostedTotalProbabilities`，在一步中對完整隨機性應用取模，而不進行中間的基礎點降低。

---

## 32. Signatures Have No Expiration Deadline

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

## 33. Unauthorized Delegation via `migrateAndDelegate()`

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

## 34. Uncoordinated Escape Hatch Mechanisms Cause Permanent `forcedWithdrawalRequests` Lock When `InclusionQueue` Executes First

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

## 35. Unresolved Developer Comments

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`WannaBet v2` contains two lingering developer comments that should be resolved before deployment. The first, in `Bet::initialize`, suggests that funds could be sent directly to Aave rather than custodied in the contract — a design alternative that the protocol has not actually implemented and which would be incorrect (the Aave pool might not always be available at initialization). The second, in `IBbet.Bet`, is an unresolved `TODO` expressing uncertainty about whether the maker-to-taker ratio representation is optimal. Both comments mislead future maintainers about the intentionality of the current design.

**Impact:**
Unresolved TODOs and misleading comments increase the risk of future refactors making incorrect assumptions, and signal to reviewers that the codebase may not have reached a finalized design state. One comment specifically suggests an alternative (direct Aave deposit) that would be operationally incorrect.

**Recommended Mitigation:**
Remove or replace the misleading Aave comment with an explanation of why direct deposit is not used. Resolve the TODO by either implementing a more efficient ratio representation or documenting that the current approach is intentionally chosen.

---

**[中文版本]**

**描述：**
`WannaBet v2` 包含兩個在部署前應解決的殘留開發者注釋。第一個在 `Bet::initialize` 中，建議資金可以直接發送到 Aave 而不是在合約中托管——這是協議實際上沒有實現的設計替代方案，且在初始化時 Aave 池可能並不總是可用，所以這個建議是不正確的。第二個在 `IBbet.Bet` 中，是一個未解決的 `TODO`，對做市商與接受者比率表示是否最優表示不確定。

**影響：**
未解決的 TODO 和誤導性注釋增加了未來重構做出不正確假設的風險，並向審查者表明代碼庫可能尚未達到最終設計狀態。

**修復建議：**
刪除或替換誤導性的 Aave 注釋，解釋為什麼不使用直接存款。通過實現更高效的比率表示或記錄當前方法是故意選擇的來解決 TODO。

---

## 36. Use `type(uint256).max` When Withdrawing From Aave

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
When unwinding Aave positions in `Bet::resolve` and `Bet::cancel`, the contract queries the aToken balance and passes that amount to `_aavePool.withdraw(b.asset, aTokenBalance, address(this))`. Aave's recommended pattern for fully closing a position is to pass `type(uint256).max` as the amount, which signals to Aave to withdraw the entire available balance. The balance-based approach is subtly fragile: due to Aave's interest-accrual indexing, the balance read in one call may differ fractionally from the balance that is withdrawable in the same transaction, potentially leaving a dust amount of aTokens in the contract. The `type(uint256).max` approach also eliminates the extra `balanceOf` call, saving one external call per resolution.

**Impact:**
Using the raw balance query instead of `type(uint256).max` may leave dust aTokens stranded in the contract due to rounding in Aave's interest accrual model, creating a small but persistent accounting discrepancy.

**Recommended Mitigation:**
Replace `_aavePool.withdraw(b.asset, aTokenBalance, address(this))` with `_aavePool.withdraw(b.asset, type(uint256).max, address(this))` and use the returned value (the actual amount withdrawn) instead of the prior `aTokenBalance` query.

---

**[中文版本]**

**描述：**
在 `Bet::resolve` 和 `Bet::cancel` 中解除 Aave 倉位時，合約查詢 aToken 餘額，並將該金額傳遞給 `_aavePool.withdraw(b.asset, aTokenBalance, address(this))`。Aave 完全關閉倉位的推薦模式是傳遞 `type(uint256).max` 作為金額，這向 Aave 表示提取整個可用餘額。基於餘額的方法微妙地脆弱：由於 Aave 的利息累積索引，在一次調用中讀取的餘額可能與同一交易中可提取的餘額略有不同，可能在合約中留下少量塵埃 aTokens。

**影響：**
使用原始餘額查詢而不是 `type(uint256).max` 可能因 Aave 利息累積模型中的四捨五入而在合約中留下少量塵埃 aTokens，造成小但持續的核算差異。

**修復建議：**
將 `_aavePool.withdraw(b.asset, aTokenBalance, address(this))` 替換為 `_aavePool.withdraw(b.asset, type(uint256).max, address(this))`，並使用返回值（實際提取金額）代替之前的 `aTokenBalance` 查詢。

---

## 37. Withdrawals Priced at Execution Problematic During Large Price Swings

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

## 38. `finalizeWithFee` Lacks Race Conditioning Protection

**Severity:** 🟡 Medium
**Source:** `cyfrin/cooldown.md`

**Description:**
`SharesCooldown::finalizeWithFee` does not accept any user-specified bounds on the fee or output amount. The effective fee can change between transaction submission and on-chain execution if: new cooldown requests are merged into existing slots (especially when the 70th slot limit is hit), the `vaultEarlyExitFeePerDay` parameter is updated by the admin, or the execution timestamp crosses a day boundary which increases the calculated `daysLeft`. Additionally, request reordering due to concurrent `cancel` or `finalize` calls can cause an unexpected request index to be finalized. Users therefore cannot predict or cap their early-exit cost at transaction submission time, and their transactions may execute at a significantly higher fee than anticipated.

**Impact:**
Users who submit `finalizeWithFee` transactions during periods of fee parameter updates or high concurrent activity can be charged substantially more than the fee visible at submission time. There is no mechanism to cancel if the fee has moved beyond an acceptable threshold.

**Recommended Mitigation:**
Add an optional `maxFee` parameter to `finalizeWithFee` and revert if the computed fee at execution time exceeds the user-specified maximum, providing slippage-style protection analogous to DEX swap limits.

---

**[中文版本]**

**描述：**
`SharesCooldown::finalizeWithFee` 不接受任何用戶指定的費用或輸出金額界限。有效費用可能在交易提交和鏈上執行之間發生變化，如果：新的冷卻請求合併到現有槽中（特別是當達到第 70 個槽限制時）、管理員更新 `vaultEarlyExitFeePerDay` 參數，或執行時間戳跨越增加計算的 `daysLeft` 的日邊界。此外，由於並發的 `cancel` 或 `finalize` 調用導致請求重新排序，可能導致意外的請求索引被最終確定。

**影響：**
在費用參數更新或高並發活動期間提交 `finalizeWithFee` 交易的用戶可能被收取比提交時可見的費用高得多的費用。如果費用超出可接受閾值，沒有機制可以取消。

**修復建議：**
向 `finalizeWithFee` 添加可選的 `maxFee` 參數，如果執行時計算的費用超過用戶指定的最大值則回退，提供類似 DEX 交換限制的滑點保護。

---

## 39. `transferOwnership` Does Not Update Privileged Exemptions

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Knoxnet.txt`

**Description:**
The `KnoxNet` token constructor grants the initial owner several automatic privileges: a `type(uint256).max` router allowance, `isTaxExempt` status, `isLiquidityCreator` status, and `isTxLimitExempt` status. When ownership is transferred via the inherited `transferOwnership` function, the function only updates the `_owner` address. It does not revoke the privileges from the old owner's address, and it does not grant the equivalent privileges to the new owner. After the transfer, the previous owner retains all operational exemptions, while the new owner — who is expected to have the same privileges — must be manually configured through separate transactions. The router allowance for the previous owner also remains unchanged.

**Impact:**
After an ownership transfer, the old owner retains privileged status (tax-exempt, liquidity creator, tx-limit-exempt, router allowance) while the new owner lacks those privileges. The new owner may be unable to perform intended administrative operations such as adding liquidity or executing large transactions without triggering the restrictions the contract was designed to apply only to non-owners.

**Recommended Mitigation:**
Override `transferOwnership` in `KnoxNet` to atomically revoke all privilege mappings from the old owner, grant them to the new owner, and update the router allowance in a single transaction.

---

**[中文版本]**

**描述：**
`KnoxNet` 代幣構造函數為初始所有者授予幾個自動特權：`type(uint256).max` 路由器許可、`isTaxExempt` 狀態、`isLiquidityCreator` 狀態和 `isTxLimitExempt` 狀態。當所有權通過繼承的 `transferOwnership` 函數轉移時，函數只更新 `_owner` 地址。它不從舊所有者地址撤銷特權，也不向新所有者授予相等的特權。轉移後，前所有者保留所有操作豁免，而新所有者——預計具有相同特權——必須通過單獨的交易手動配置。

**影響：**
所有權轉移後，舊所有者保留特權狀態（免稅、流動性創建者、交易限制豁免、路由器許可），而新所有者缺乏這些特權。新所有者可能無法執行預期的管理操作，如添加流動性或在不觸發限制的情況下執行大型交易。

**修復建議：**
在 `KnoxNet` 中覆寫 `transferOwnership`，以在單個交易中原子地從舊所有者撤銷所有特權映射，將其授予新所有者，並更新路由器許可。
