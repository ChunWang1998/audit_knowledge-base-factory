# named-explicitly (23)

> Issues where identifiers, parameters, or logic were not explicitly named/specified, causing ambiguity or incorrect behavior.
Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## 1. All Updated Pools Will Have the Wrong `predictedPool`

**Severity:** 🟠 High
**Source:** `sherlockPDFTXT/EasyA Kickstart.txt`

**Description:**
`PumpBondingCurve` protects against pre-graduation price manipulation by storing a `predictedPool` address and blocking token transfers to that address until graduation. When the protocol upgrades from Aerodrome V2 pools to Slipstream (CL) pools, the graduation logic in `PumpBondingCurve` is updated to compute the new CL pool address using `AerodromeLib.predictCLPoolAddress`. However, existing ungraduated `PumpToken` instances — which are not upgradeable — still hold their old `predictedPool` set to the legacy V2 pool address. After the protocol upgrade, the actual CL pool address at graduation is completely different from the stored `predictedPool`. The transfer restriction therefore does not apply to the real deployment address, allowing attackers to freely transfer tokens to the actual CL pool before graduation and skew the price, causing graduation to fail.

**Impact:**
For any existing ungraduated token after the protocol upgrade, an attacker can transfer tokens to the correct CL pool address before graduation, manipulating the initial price and bricking the `_graduate` function via a skewed ratio.

**Recommended Mitigation:**
When upgrading to Slipstream graduation, provide a migration path that updates `predictedPool` in existing `PumpToken` instances to reflect the new CL pool prediction formula, or ensure that the graduation logic in `PumpToken` is also upgraded atomically.

---

**[中文版本]**

**描述：**
`PumpBondingCurve` 通過存儲 `predictedPool` 地址並阻止代幣在畢業前轉移到該地址來防止畢業前的價格操縱。當協議從 Aerodrome V2 池升級到 Slipstream（CL）池時，`PumpBondingCurve` 中的畢業邏輯更新為使用 `AerodromeLib.predictCLPoolAddress` 計算新的 CL 池地址。然而，現有的未畢業 `PumpToken` 實例——它們不可升級——仍然持有設置為舊版 V2 池地址的 `predictedPool`。協議升級後，畢業時的實際 CL 池地址與存儲的 `predictedPool` 完全不同。因此，轉移限制不適用於真實部署地址，允許攻擊者在畢業前自由地將代幣轉移到實際的 CL 池並傾斜價格。

**影響：**
對於協議升級後任何現有的未畢業代幣，攻擊者可以在畢業前將代幣轉移到正確的 CL 池地址，操縱初始價格，並通過傾斜的比率使 `_graduate` 函數失效。

**修復建議：**
升級到 Slipstream 畢業時，提供一個遷移路徑，將現有 `PumpToken` 實例中的 `predictedPool` 更新以反映新的 CL 池預測公式，或確保 `PumpToken` 中的畢業邏輯也被原子性地升級。

---

## 2. Asymmetry Enforcement Between `TokenIssuer::registerInvestor`, `WalletRegistrar::registerWallet` and `SecuritizeSwap::_registerNewInvestor`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`TokenIssuer::registerInvestor` enforces that when registering a new investor, exactly three compliance attributes — `KYC_APPROVED`, `ACCREDITED`, and `QUALIFIED` — must be provided. By contrast, `WalletRegistrar::registerWallet` and `SecuritizeSwap::_registerNewInvestor` both register new investors without enforcing those mandatory attributes. They accept a generic `_attributeIds` array and set whatever attributes the caller provides, without requiring the three compliance-critical attributes to be present. This inconsistency means an investor can be registered through the wallet or swap paths with incomplete compliance data, potentially allowing token interactions that should be blocked.

**Impact:**
Investors registered through `WalletRegistrar` or `SecuritizeSwap` may lack the required KYC and accreditation attributes, bypassing compliance gates that depend on those attributes being set. Token issuance and transfer compliance checks that rely on `KYC_APPROVED`, `ACCREDITED`, or `QUALIFIED` attributes may be circumvented.

**Recommended Mitigation:**
Harmonize all three investor registration paths to enforce the same mandatory attribute requirements, either by extracting a shared internal registration function or by adding the three-attribute enforcement to `registerWallet` and `_registerNewInvestor`.

---

**[中文版本]**

**描述：**
`TokenIssuer::registerInvestor` 強制執行在注冊新投資者時必須提供恰好三個合規屬性——`KYC_APPROVED`、`ACCREDITED` 和 `QUALIFIED`。相比之下，`WalletRegistrar::registerWallet` 和 `SecuritizeSwap::_registerNewInvestor` 都注冊新投資者而不強制執行這些強制屬性。它們接受通用的 `_attributeIds` 數組並設置調用者提供的任何屬性，而不要求三個合規關鍵屬性存在。這種不一致意味著投資者可以通過錢包或交換路徑以不完整的合規數據注冊。

**影響：**
通過 `WalletRegistrar` 或 `SecuritizeSwap` 注冊的投資者可能缺乏所需的 KYC 和資質屬性，繞過依賴這些屬性設置的合規門控。依賴 `KYC_APPROVED`、`ACCREDITED` 或 `QUALIFIED` 屬性的代幣發行和轉移合規檢查可能被規避。

**修復建議：**
統一所有三條投資者注冊路徑以強制執行相同的強制屬性要求，無論是通過提取共享的內部注冊函數，還是通過向 `registerWallet` 和 `_registerNewInvestor` 添加三屬性強制執行。

---

## 3. Calculation of Available Liquidity in `CollateralLiquidityProvider::availableLiquidity` Assumes 1:1 Ratio Between Collateral Asset and Liquidity Tokens

**Severity:** 🟡 Medium
**Source:** `cyfrin/bridge.md`

**Description:**
`CollateralLiquidityProvider::availableLiquidity` returns the raw ERC-20 balance of the collateral asset held by the collateral provider. This assumes a 1:1 correspondence between collateral asset and the liquidity tokens that will actually be given to redeemers. In reality, the liquidity token amount is computed by `externalCollateralRedemption.calculateLiquidityTokenAmount(collateralAmount)`, which may apply fees, exchange rates, or other conversion logic that breaks the 1:1 assumption. The external `availableLiquidity` function also duplicates the logic of the internal `_availableLiquidity` function rather than delegating to it, creating a code duplication bug where changes to one function are not reflected in the other.

**Impact:**
Callers — including the redeemer contract — may receive an inflated or incorrect view of available liquidity. If the actual convertible liquidity is less than the reported collateral balance, redemption calls built on this view will revert unexpectedly, creating a DoS for redeemers.

**Recommended Mitigation:**
Update `availableLiquidity` to compute the actual liquidity tokens available by querying `externalCollateralRedemption.calculateLiquidityTokenAmount(balance)`. Also fix the duplication by having the public `availableLiquidity` call the private `_availableLiquidity` function.

---

**[中文版本]**

**描述：**
`CollateralLiquidityProvider::availableLiquidity` 返回抵押提供者持有的抵押資產的原始 ERC-20 餘額。這假設抵押資產與實際提供給贖回者的流動性代幣之間存在 1:1 對應關係。實際上，流動性代幣數量由 `externalCollateralRedemption.calculateLiquidityTokenAmount(collateralAmount)` 計算，可能應用費用、匯率或其他打破 1:1 假設的轉換邏輯。外部 `availableLiquidity` 函數還複製了內部 `_availableLiquidity` 函數的邏輯而不是委托給它，造成代碼重複錯誤。

**影響：**
調用者——包括贖回合約——可能收到虛高或不正確的可用流動性視圖。如果實際可轉換流動性少於報告的抵押餘額，基於此視圖構建的贖回調用將意外回退，為贖回者創造 DoS。

**修復建議：**
更新 `availableLiquidity` 以通過查詢 `externalCollateralRedemption.calculateLiquidityTokenAmount(balance)` 來計算實際可用的流動性代幣。同時通過讓公共 `availableLiquidity` 調用私有 `_availableLiquidity` 函數來修復重複。

---

## 4. Cooldown Contracts Underreport the Real Balance of Users Because They Only Consider the Balance of Requests Whose Cooldown Period Is Over

**Severity:** 🟡 Medium
**Source:** `cyfrin/tranches.md`

**Description:**
Cooldown contracts implement a `balanceOf` method that only sums up the underlying value of cooldown requests whose cooldown period has already elapsed (i.e., requests that are currently claimable). Requests that are still in their lock window are excluded from the reported balance. This means that a user who has submitted a large redemption request that has not yet unlocked will see their `balanceOf` return far less than the actual value of assets they have committed and are waiting for. The balance only grows as time passes and locks expire, creating an inaccurate picture of user positions.

**Impact:**
Users, integrations, and off-chain monitoring systems that rely on `balanceOf` will see an artificially low balance for users with pending (not-yet-expired) cooldown requests. This can cause incorrect collateral calculations, faulty liquidation triggers, or misleading UI displays.

**Recommended Mitigation:**
Refactor `balanceOf` to return the total of all active requests — both locked (pending) and unlocked (claimable). Consider providing separate view functions like `pendingBalance` and `claimableBalance` for contexts that need to distinguish between the two.

---

**[中文版本]**

**描述：**
冷卻合約實現了一個 `balanceOf` 方法，只匯總冷卻期已過的冷卻請求的底層價值（即當前可認領的請求）。仍在鎖定窗口內的請求被排除在報告的餘額之外。這意味著提交了尚未解鎖的大型贖回請求的用戶，其 `balanceOf` 返回的值遠少於他們已承諾並等待的資產實際價值。

**影響：**
依賴 `balanceOf` 的用戶、集成和鏈下監控系統，對有待處理（尚未到期）冷卻請求的用戶將看到人為偏低的餘額。這可能導致不正確的抵押品計算、錯誤的清算觸發器或誤導性的 UI 顯示。

**修復建議：**
重構 `balanceOf` 以返回所有活躍請求的總和——包括鎖定的（待處理）和解鎖的（可認領的）。考慮提供單獨的視圖函數如 `pendingBalance` 和 `claimableBalance`，供需要區分兩者的上下文使用。

---

## 5. Dynamic LP Fees Will Remain Zero by Default Unless Explicitly Updated

**Severity:** 🟡 Medium
**Source:** `cyfrin/angstrom.md`

**Description:**
`LPFeeLibrary::getInitialLPFee` returns 0 for dynamic fee pools, per Uniswap v4's design. `AngstromL2::setPoolLPFee` allows the hook owner to update the fee after initialization, but there is no `afterInitialize()` hook implementation that would set a non-zero fee immediately upon pool creation. This means every pool deployed through the hook will have an LP fee of 0% from the moment of creation until the hook owner manually calls `setPoolLPFee`. Depending on protocol latency, this window could span multiple blocks during which LPs receive no fee income while the pool is active and taking trades.

**Impact:**
Liquidity providers earn zero fees from pool creation until the hook owner explicitly sets the LP fee. The zero-fee window, however brief, reduces LP compensation and can affect their incentive to remain in the pool.

**Recommended Mitigation:**
Implement the `afterInitialize()` hook to immediately set the desired initial LP fee upon pool creation, eliminating the zero-fee window between initialization and the first manual `setPoolLPFee` call.

---

**[中文版本]**

**描述：**
按照 Uniswap v4 的設計，`LPFeeLibrary::getInitialLPFee` 對動態費率池返回 0。`AngstromL2::setPoolLPFee` 允許鉤子所有者在初始化後更新費率，但沒有 `afterInitialize()` 鉤子實現，無法在池創建時立即設置非零費率。這意味著通過鉤子部署的每個池從創建時刻到鉤子所有者手動調用 `setPoolLPFee` 之前，LP 費率都為 0%。

**影響：**
流動性提供者從池創建到鉤子所有者明確設置 LP 費率之前收取零費用。這個零費用窗口，無論多短，都會減少 LP 補償並影響他們留在池中的激勵。

**修復建議：**
實現 `afterInitialize()` 鉤子，在池創建時立即設置所需的初始 LP 費率，消除初始化和第一次手動 `setPoolLPFee` 調用之間的零費用窗口。

---

## 6. External LST Liability Settlements Are Lost to the Protocol When Ossification and Yield Provider Removal Precedes Yield Reporting

**Severity:** 🟡 Medium
**Source:** `cyfrin/manager.md`

**Description:**
When an external actor settles LST liabilities, the vault gains ETH without the protocol's accounting (`userFunds`) reflecting this. The windfall is normally captured when `YieldManager::reportYield` is called next. However, if ossification is initiated before `reportYield` is called, and then `YieldManager::withdrawFromYieldProvider` followed by `YieldManager::removeYieldProvider` is executed, the windfall is permanently lost. `withdrawFromYieldProvider` correctly detects and syncs `lstLiabilityPrincipal` after external settlement, but it does not record the resulting surplus in `userFunds`. `removeYieldProvider` only verifies `userFunds == 0` before allowing removal; it does not check whether the vault's actual balance matches `userFunds`. Once the vault is removed and ownership transferred, the windfall is orphaned with no recovery mechanism.

**Impact:**
Protocol funds that should have been distributed to L2 users as yield are permanently lost. The internal accounting becomes permanently disconnected from the physical vault balance, and the vault is transferred to a new owner without ever distributing the windfall.

**Recommended Mitigation:**
Add a check in `removeYieldProvider` that verifies the vault's actual value is zero before permitting removal. Additionally, modify `withdrawFromYieldProvider` to capture any LST liability windfall into `userFunds` when detected.

---

**[中文版本]**

**描述：**
當外部參與者結算 LST 負債時，金庫獲得 ETH，而協議的核算（`userFunds`）未反映這一點。這個意外之財通常在下次調用 `YieldManager::reportYield` 時被捕獲。然而，如果在調用 `reportYield` 之前啟動了骨化（ossification），然後執行了 `YieldManager::withdrawFromYieldProvider` 和 `YieldManager::removeYieldProvider`，意外之財將永久損失。`withdrawFromYieldProvider` 在外部結算後正確地檢測並同步 `lstLiabilityPrincipal`，但它不將結果盈餘記錄在 `userFunds` 中。`removeYieldProvider` 只在允許移除之前驗證 `userFunds == 0`；它不檢查金庫的實際餘額是否與 `userFunds` 匹配。

**影響：**
應分配給 L2 用戶作為收益的協議資金永久損失。內部核算與物理金庫餘額永久脫節，金庫在沒有分配意外之財的情況下轉移給新所有者。

**修復建議：**
在 `removeYieldProvider` 中添加一個檢查，在允許移除之前驗證金庫的實際價值為零。此外，修改 `withdrawFromYieldProvider`，在檢測到 LST 負債意外之財時將其捕獲到 `userFunds` 中。

---

## 7. Mismatch Between Tier Assignment and Enumeration Breaks Tier Determinism

**Severity:** 🟡 Medium
**Source:** `HackenPDFTXT/Acecoin.txt`

**Description:**
The `MemoryManager` contract uses two fundamentally different strategies for tier management. During insertion, stake tiers and downline tiers are assigned by dividing the value (e.g., `stakeId`) by a constant `TIER_SIZE` (value-based tiering). During enumeration, the total number of tiers is estimated by dividing the count of items by `TIER_SIZE` with ceiling rounding (count-based tiering). These two approaches produce inconsistent results. For example, Alice's two stakes with IDs 1999 and 2000 are assigned to tiers 1 and 2 respectively (value-based), but `getTierCount(2)` returns 1 (count-based), implying only one tier is used. This mismatch corrupts paginated data generation in `MemoryManager::getPaginatedData` and downstream functions `getUserStakeIds` and `getUserStakeIdsPaginated`.

**Impact:**
Tier enumeration does not accurately reflect actual tier distributions. Downstream queries return incorrect or incomplete data, breaking frontend integrations and dApp components that rely on accurate stake and downline tier information.

**Recommended Mitigation:**
Align the enumeration logic with the insertion logic: compute tier count by tracking the maximum tier ID encountered during insertions (or by computing `maxValue / TIER_SIZE + 1`) rather than using count-based rounding.

---

**[中文版本]**

**描述：**
`MemoryManager` 合約使用兩種根本不同的策略進行層級管理。在插入期間，質押層級和下線層級通過將值（例如 `stakeId`）除以常量 `TIER_SIZE` 來分配（基於值的分層）。在枚舉期間，層級總數通過將項目數除以 `TIER_SIZE` 並向上取整來估計（基於計數的分層）。這兩種方法產生不一致的結果。例如，Alice 的 ID 為 1999 和 2000 的兩筆質押分別被分配到層級 1 和 2（基於值），但 `getTierCount(2)` 返回 1（基於計數），暗示只使用了一個層級。

**影響：**
層級枚舉不能準確反映實際的層級分佈。下游查詢返回不正確或不完整的數據，破壞依賴準確質押和下線層級信息的前端集成和 dApp 組件。

**修復建議：**
將枚舉邏輯與插入邏輯對齊：通過跟蹤插入期間遇到的最大層級 ID（或通過計算 `maxValue / TIER_SIZE + 1`）來計算層級數，而不是使用基於計數的四捨五入。

---

## 8. `MyriadCTFExchange.filledAmounts` Mapping Slot and `hashOrder` Computed Multiple Times Per Order

**Severity:** 🟡 Medium
**Source:** `cyfrin/clob.md`

**Description:**
In `MyriadCTFExchange::_matchOrders`, each order's `filledAmounts` storage slot is accessed three times: once to check the constraint (`filledAmounts[makerHash] + fillAmount <= maker.amount`), once to increment it, and once to emit the event. The same pattern applies to the taker hash. In `MyriadCTFExchange::matchCrossMarketOrders`, `hashOrder(orders[i])` is computed in both the validation loop and the distribution loop, and `filledAmounts[orderHash]` is read in the validation loop, then read-modified-written in the distribution loop, then read again for the emit. Each repeat access triggers a warm storage read (100 gas) and the repeated `hashOrder` computation wastes CPU cycles, inflating gas costs for every matched order.

**Impact:**
Gas inefficiency. Protocols with high order throughput accumulate meaningful unnecessary gas costs per match. No security impact.

**Recommended Mitigation:**
Cache each `hashOrder` result in a local variable after the first computation. Cache each `filledAmounts` slot value after the first SLOAD. Increment the cached value in memory and perform a single SSTORE at the end, then use the cached post-update value in the event emit.

---

**[中文版本]**

**描述：**
在 `MyriadCTFExchange::_matchOrders` 中，每個訂單的 `filledAmounts` 存儲槽被訪問三次：一次用於檢查約束（`filledAmounts[makerHash] + fillAmount <= maker.amount`），一次用於遞增它，一次用於發出事件。相同的模式適用於接受者哈希。在 `MyriadCTFExchange::matchCrossMarketOrders` 中，`hashOrder(orders[i])` 在驗證循環和分配循環中都被計算，`filledAmounts[orderHash]` 在驗證循環中被讀取，然後在分配循環中讀取-修改-寫入，然後再次讀取用於事件發出。

**影響：**
氣體效率低下。具有高訂單吞吐量的協議每次匹配都會積累有意義的不必要氣體成本。沒有安全影響。

**修復建議：**
在第一次計算後將每個 `hashOrder` 結果緩存在局部變量中。在第一次 SLOAD 後緩存每個 `filledAmounts` 槽值。在內存中遞增緩存值，最後執行一次 SSTORE，然後在事件發出中使用緩存的更新後值。

---

## 9. Refactor Away Duplicated Code Between `ComplianceService::newPreTransferCheck` and `preTransferCheck`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`ComplianceService::newPreTransferCheck` and `preTransferCheck` implement identical transfer validation logic. The only difference is that `newPreTransferCheck` accepts `balanceFrom` and `paused` as input parameters, while `preTransferCheck` looks them up internally via `token.balanceOf(_from)` and `token.isPaused()`. The two functions should be related by composition: `preTransferCheck` should look up its parameters and delegate directly to `newPreTransferCheck`. Instead, both functions contain a full copy of the validation logic, meaning any future change to the compliance rules must be applied twice and the two implementations can drift apart.

**Impact:**
Code duplication creates maintenance risk. Any bug fix or rule change applied to one function but not the other will cause inconsistent compliance behavior between the two call paths. The divergence may go unnoticed until a discrepancy is encountered in production.

**Recommended Mitigation:**
Refactor `preTransferCheck` to look up `balanceFrom` and `paused` from the token contract, then delegate to `newPreTransferCheck` with those values, eliminating all duplicated logic.

---

**[中文版本]**

**描述：**
`ComplianceService::newPreTransferCheck` 和 `preTransferCheck` 實現了相同的轉移驗證邏輯。唯一的區別是 `newPreTransferCheck` 接受 `balanceFrom` 和 `paused` 作為輸入參數，而 `preTransferCheck` 通過 `token.balanceOf(_from)` 和 `token.isPaused()` 在內部查找它們。兩個函數應通過組合相關：`preTransferCheck` 應查找其參數並直接委托給 `newPreTransferCheck`。相反，兩個函數都包含驗證邏輯的完整副本，意味著對合規規則的任何未來更改必須應用兩次，且兩個實現可能出現偏差。

**影響：**
代碼重複造成維護風險。應用於一個函數但不應用於另一個函數的任何錯誤修復或規則更改將導致兩個調用路徑之間的合規行為不一致。這種分歧可能直到在生產中遇到差異時才被注意到。

**修復建議：**
重構 `preTransferCheck` 以從代幣合約查找 `balanceFrom` 和 `paused`，然後用這些值委托給 `newPreTransferCheck`，消除所有重複邏輯。

---

## 10. Resolve Inconsistency Between `DSToken::checkWalletsForList` and `RegistryService::removeWallet`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`DSToken::checkWalletsForList` only removes a wallet from the registry when its token balance is zero — enforcing the invariant that wallets with a balance remain registered. However, `RegistryService::removeWallet` allows any exchange-or-above role to remove a wallet regardless of its current token balance. After such a removal, the registry no longer has a mapping from that wallet address to an investor ID. Any subsequent transfer involving that wallet — deductions from `_from` or credits to `_to` — will fail on registry lookups that expect the wallet to be registered, blocking token activity.

**Impact:**
Removing a wallet with a positive balance breaks the registry-to-investor mapping for that wallet. Any transfer that involves the de-registered wallet as sender or receiver will revert, effectively freezing those tokens and blocking legitimate transfers.

**Recommended Mitigation:**
Add a balance check to `RegistryService::removeWallet` that reverts if the wallet being removed holds a non-zero token balance, making it consistent with the zero-balance enforcement in `checkWalletsForList`.

---

**[中文版本]**

**描述：**
`DSToken::checkWalletsForList` 只在錢包的代幣餘額為零時從注冊表中移除它——強制執行持有餘額的錢包保持注冊的不變量。然而，`RegistryService::removeWallet` 允許任何交易所或更高角色移除錢包，無論其當前代幣餘額如何。移除後，注冊表不再有從該錢包地址到投資者 ID 的映射。任何後續涉及該錢包的轉移——從 `_from` 扣減或對 `_to` 的信用——都將在期望錢包已注冊的注冊表查找中失敗，阻止代幣活動。

**影響：**
移除具有正餘額的錢包破壞了該錢包的注冊表到投資者映射。任何涉及取消注冊錢包作為發送者或接收者的轉移都將回退，有效地凍結這些代幣並阻止合法轉移。

**修復建議：**
向 `RegistryService::removeWallet` 添加餘額檢查，如果被移除的錢包持有非零代幣餘額則回退，使其與 `checkWalletsForList` 中的零餘額強制執行保持一致。

---

## 11. `TransactionRelayer` and `SecuritizeSwap` Should Use `CommonUtils::encodeString`

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
`TransactionRelayer::toBytes32` re-implements string-to-bytes32 encoding that is already available as `CommonUtils::encodeString`. A second instance of the same duplication appears in `TransactionRelayer` itself (line 178: `keccak256(abi.encodePacked(senderInvestor))`), and a third in `SecuritizeSwap` (line 191: `keccak256(abi.encodePacked(_senderInvestorId))`). Having three independent copies of the same encoding logic increases maintenance burden and creates risk of subtle encoding differences if any one copy is updated without updating the others.

**Impact:**
Code-quality issue. If the encoding logic in `CommonUtils::encodeString` is ever updated — for example to use a different hash function or encoding standard — the independent copies in `TransactionRelayer` and `SecuritizeSwap` will silently diverge, producing different hash values and causing investor ID lookups to fail.

**Recommended Mitigation:**
Remove `TransactionRelayer::toBytes32` and replace all three manual `keccak256(abi.encodePacked(...))` usages with calls to `CommonUtils::encodeString` to ensure a single canonical encoding path.

---

**[中文版本]**

**描述：**
`TransactionRelayer::toBytes32` 重新實現了 `CommonUtils::encodeString` 中已有的字符串到 bytes32 編碼。相同重複的第二個實例出現在 `TransactionRelayer` 自身中（第 178 行：`keccak256(abi.encodePacked(senderInvestor))`），第三個在 `SecuritizeSwap` 中（第 191 行：`keccak256(abi.encodePacked(_senderInvestorId))`）。擁有相同編碼邏輯的三個獨立副本增加了維護負擔，並在任何一個副本更新而其他副本未更新時創造了微妙編碼差異的風險。

**影響：**
代碼質量問題。如果 `CommonUtils::encodeString` 中的編碼邏輯更新——例如使用不同的哈希函數或編碼標準——`TransactionRelayer` 和 `SecuritizeSwap` 中的獨立副本將靜默地偏離，產生不同的哈希值，導致投資者 ID 查找失敗。

**修復建議：**
刪除 `TransactionRelayer::toBytes32` 並將所有三個手動 `keccak256(abi.encodePacked(...))` 用法替換為對 `CommonUtils::encodeString` 的調用，以確保單一的規範編碼路徑。

---

## 12. Use `uint128` to Pack `DepositManager::protocolFee`, `maxCreatorFee` Into the Same Storage Slot

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
`DepositManager::protocolFee` and `maxCreatorFee` are both declared as `uint256` but their values are always constrained to be less than `BASIS_POINTS = 10000`. A `uint128` is more than sufficient to represent any value in the 0–10000 range and takes half the storage space of `uint256`. By changing both fields to `uint128`, the Solidity compiler will pack them together into a single 32-byte storage slot. Functions like `getRewards` that read both fields in the same call will therefore require only one SLOAD instead of two, reducing gas costs. The same optimization applies to the corresponding fields inside the `GamePool` struct.

**Impact:**
Minor gas inefficiency. No security impact. Every call to `getRewards` and similar functions wastes one SLOAD that could be eliminated by packing the two fee fields.

**Recommended Mitigation:**
Declare `protocolFee` and `maxCreatorFee` as `uint128` in both `DepositManager` and the `GamePool` struct, ensuring the compiler packs them into the same slot.

---

**[中文版本]**

**描述：**
`DepositManager::protocolFee` 和 `maxCreatorFee` 都被聲明為 `uint256`，但它們的值始終被約束為小於 `BASIS_POINTS = 10000`。`uint128` 足以表示 0–10000 範圍內的任何值，並占用 `uint256` 一半的存儲空間。通過將兩個字段都更改為 `uint128`，Solidity 編譯器將把它們打包到同一個 32 字節存儲槽中。讀取兩個字段的函數（如 `getRewards`）因此只需要一個 SLOAD 而不是兩個，降低了氣體成本。

**影響：**
輕微的氣體效率低下。沒有安全影響。每次調用 `getRewards` 等函數都浪費一個可通過打包兩個費用字段消除的 SLOAD。

**修復建議：**
在 `DepositManager` 和 `GamePool` 結構中將 `protocolFee` 和 `maxCreatorFee` 聲明為 `uint128`，確保編譯器將它們打包到同一個槽中。

---

## 13. Use Named Constants to Indicate Purpose of Magic Numbers

**Severity:** 🟡 Medium
**Source:** `cyfrin/cryptoart.md`

**Description:**
The `CryptoartNFT` contract uses several magic numbers in array type declarations and index accesses without explaining their semantic meaning. For example, `string[2]` is used throughout the token URI mapping and related functions, but the literal `2` conveys nothing about why there are exactly two URIs. A named constant `URIS_PER_TOKEN = 2` would document this intent. Similarly, array indices for redeemable versus non-redeemable URIs appear as bare `0` and `1` literals in `updateMetadata` and `_setTokenURIs`, instead of named constants like `URI_REDEEMABLE_INDEX` and `URI_NOT_REDEEMABLE_INDEX`.

**Impact:**
Code-quality issue. Magic numbers make code harder to audit and maintain — a reader must infer the purpose of `2`, `0`, or `1` from context. If the index convention changes, all literal accesses must be updated, creating risk of missed locations.

**Recommended Mitigation:**
Define named constants for all recurring magic numbers — `URIS_PER_TOKEN`, `URI_REDEEMABLE_INDEX`, `URI_NOT_REDEEMABLE_INDEX` — and replace all literal occurrences with the named constant.

---

**[中文版本]**

**描述：**
`CryptoartNFT` 合約在數組類型聲明和索引訪問中使用幾個魔術數字，而沒有解釋其語義含義。例如，`string[2]` 在整個代幣 URI 映射和相關函數中使用，但字面量 `2` 沒有傳達為什麼恰好有兩個 URI 的含義。命名常量 `URIS_PER_TOKEN = 2` 將記錄這一意圖。同樣，可贖回與不可贖回 URI 的數組索引在 `updateMetadata` 和 `_setTokenURIs` 中以裸 `0` 和 `1` 字面量出現。

**影響：**
代碼質量問題。魔術數字使代碼更難審計和維護——讀者必須從上下文推斷 `2`、`0` 或 `1` 的目的。如果索引約定更改，所有字面訪問都必須更新，造成遺漏位置的風險。

**修復建議：**
為所有重複的魔術數字定義命名常量——`URIS_PER_TOKEN`、`URI_REDEEMABLE_INDEX`、`URI_NOT_REDEEMABLE_INDEX`——並用命名常量替換所有字面出現。

---

## 14. Use Named Imports (rebasing)

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
The Securitize DSToken codebase inconsistently applies named imports. Some files use named imports (`import {Foo} from "..."`) while others use bare imports (`import "..."`). Bare imports bring all exported symbols of the imported module into scope, which can cause naming collisions, make it harder to trace where a symbol comes from, and reduce the signal-to-noise ratio when reading the code. Named imports make dependencies explicit at the import statement level.

**Impact:**
Code-quality issue. Inconsistent import styles increase the maintenance burden and can slow down audits. No direct security impact.

**Recommended Mitigation:**
Apply named imports consistently throughout all contracts in the codebase, using the `import {Symbol} from "module"` syntax for every import statement.

---

**[中文版本]**

**描述：**
Securitize DSToken 代碼庫不一致地應用命名導入。一些文件使用命名導入（`import {Foo} from "..."`），而另一些使用裸導入（`import "..."`）。裸導入將導入模塊的所有導出符號帶入作用域，可能導致命名衝突，使追蹤符號來源更困難，並在閱讀代碼時降低信噪比。

**影響：**
代碼質量問題。不一致的導入風格增加了維護負擔，可能減慢審計速度。沒有直接安全影響。

**修復建議：**
在代碼庫的所有合約中一致地應用命名導入，對每個導入語句使用 `import {Symbol} from "module"` 語法。

---

## 15. Use Named Imports (syntetika)

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
The Syntetika codebase applies named imports in some files but uses bare module-level imports in others, including `Minter.sol`, `StakingVault.sol`, `TokensHolder.sol`, and `HilBTC.sol`. Bare imports that pull in entire OpenZeppelin or project files without naming specific symbols reduce clarity, can introduce unexpected symbol pollution in the importing file's namespace, and make automated dependency analysis harder.

**Impact:**
Code-quality issue. No direct security impact. Inconsistent import style increases cognitive overhead for auditors and developers.

**Recommended Mitigation:**
Convert all bare imports in the affected contracts to named imports, explicitly listing each imported symbol.

---

**[中文版本]**

**描述：**
Syntetika 代碼庫在一些文件中應用命名導入，但在其他文件中使用裸模塊級導入，包括 `Minter.sol`、`StakingVault.sol`、`TokensHolder.sol` 和 `HilBTC.sol`。不命名特定符號地引入整個 OpenZeppelin 或項目文件的裸導入降低了清晰度，可能在導入文件的命名空間中引入意外的符號污染。

**影響：**
代碼質量問題。沒有直接安全影響。不一致的導入風格增加了審計員和開發者的認知開銷。

**修復建議：**
將受影響合約中的所有裸導入轉換為命名導入，明確列出每個導入的符號。

---

## 16. Use Named Mapping Parameters to Explicitly Note the Purpose of Keys and Values (rebasing)

**Severity:** 🟡 Medium
**Source:** `cyfrin/rebasing.md`

**Description:**
The Securitize DSToken codebase declares mappings without the named parameter syntax introduced in Solidity 0.8.18, such that the semantic meaning of key and value types must be inferred from variable names and surrounding code rather than being stated at the declaration site. Functions like compliance lookups, registry queries, and lock management all use mappings where descriptive key and value names would greatly improve the readability and auditability of the contract.

**Impact:**
Code-quality issue. No direct security impact. Unnamed mapping parameters increase the cognitive effort needed to understand what a mapping represents, raising the risk of misinterpretation in future development.

**Recommended Mitigation:**
Apply Solidity 0.8.18 named mapping parameters consistently throughout all mapping declarations in the codebase.

---

**[中文版本]**

**描述：**
Securitize DSToken 代碼庫在聲明映射時沒有使用 Solidity 0.8.18 引入的命名參數語法，使得鍵和值類型的語義含義必須從變量名和周圍代碼推斷，而不是在聲明點明確說明。合規查找、注冊表查詢和鎖定管理等函數都使用映射，描述性的鍵和值名稱將大大提高合約的可讀性和可審計性。

**影響：**
代碼質量問題。沒有直接安全影響。未命名的映射參數增加了理解映射代表什麼所需的認知努力，在未來開發中提高了誤解的風險。

**修復建議：**
在代碼庫的所有映射聲明中一致地應用 Solidity 0.8.18 命名映射參數。

---

## 17. Use Named Mapping Parameters to Explicitly Note the Purpose of Keys and Values (syntetika)

**Severity:** 🟡 Medium
**Source:** `cyfrin/syntetika.md`

**Description:**
The Syntetika codebase uses mappings throughout its contracts without applying the Solidity 0.8.18 named parameter syntax. Mappings in `StakingVault` and other contracts that track user cooldowns, positions, and allowances all use anonymous key and value slots. Readers must cross-reference variable names, natspec comments, and call sites to understand what each mapping key and value represents, adding unnecessary friction to code review and auditing.

**Impact:**
Code-quality issue. No direct security impact. The lack of named mapping parameters adds overhead to every code review and increases the risk of subtle misuse at call sites.

**Recommended Mitigation:**
Add named parameters to all mapping declarations throughout the Syntetika codebase, annotating key and value slots with descriptive identifiers.

---

**[中文版本]**

**描述：**
Syntetika 代碼庫在其合約中廣泛使用映射，但沒有應用 Solidity 0.8.18 的命名參數語法。`StakingVault` 和其他追蹤用戶冷卻期、倉位和許可的合約中的映射都使用匿名鍵和值槽。讀者必須交叉引用變量名、natspec 注釋和調用點來理解每個映射的鍵和值代表什麼。

**影響：**
代碼質量問題。沒有直接安全影響。缺乏命名映射參數為每次代碼審查增加了開銷，並增加了在調用點微妙誤用的風險。

**修復建議：**
向整個 Syntetika 代碼庫中的所有映射聲明添加命名參數，用描述性標識符注釋鍵和值槽。

---

## 18. Use Named Mapping Parameters to Explicitly Note the Purpose of Keys and Values (trade)

**Severity:** 🟡 Medium
**Source:** `cyfrin/trade.md`

**Description:**
`BasisTradeTailor` and `BasisTradeVault` declare several mappings — including `pocketUser`, `withdrawalRequests`, `creationWhitelist`, and `depositWhitelist` — without using Solidity 0.8.18 named parameters. While variable names partially communicate intent, explicit key and value annotations in the mapping declaration itself make the contract self-documenting and reduce the risk of incorrect usage. For example, `mapping(address pocket => address user) public pocketUser` is unambiguous about which address is the key and which is the value, even when reading the declaration in isolation.

**Impact:**
Code-quality issue. No direct security impact. Unnamed parameters add cognitive load to auditors and increase the chance of key/value confusion in complex integrations.

**Recommended Mitigation:**
Apply named mapping parameters to all mapping declarations in `BasisTradeTailor` and `BasisTradeVault`, explicitly annotating each key and value with a descriptive identifier.

---

**[中文版本]**

**描述：**
`BasisTradeTailor` 和 `BasisTradeVault` 聲明了幾個映射——包括 `pocketUser`、`withdrawalRequests`、`creationWhitelist` 和 `depositWhitelist`——但沒有使用 Solidity 0.8.18 命名參數。雖然變量名部分傳達了意圖，但在映射聲明本身中明確的鍵和值注釋使合約自我說明，降低了不正確使用的風險。

**影響：**
代碼質量問題。沒有直接安全影響。未命名參數為審計員增加了認知負擔，增加了複雜集成中鍵/值混淆的機會。

**修復建議：**
在 `BasisTradeTailor` 和 `BasisTradeVault` 中的所有映射聲明中應用命名映射參數，用描述性標識符明確注釋每個鍵和值。

---

## 19. Use Named Mappings to Explicitly Denote the Purpose of Keys and Values (predeposit)

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Several contracts in the Strata predeposit system declare mappings without applying Solidity 0.8.18 named parameters. Affected mappings include `assetsMap` in `MetaVault.sol`, `autoSwaps` in `pUSDeDepositor.sol`, and `cooldowns` in `MockStakedUSDe.sol`. These mappings track asset configurations, auto-swap settings, and user cooldown states, respectively. The absence of explicit key and value names makes these declarations less self-documenting and more error-prone in integrations and future refactors.

**Impact:**
Code-quality issue. No direct security impact. Undocumented mapping semantics increase review time and the chance of misuse.

**Recommended Mitigation:**
Add named key and value parameters to all mapping declarations in the predeposit contracts, following the Solidity 0.8.18 syntax.

---

**[中文版本]**

**描述：**
Strata 預存款系統中的幾個合約在聲明映射時沒有應用 Solidity 0.8.18 命名參數。受影響的映射包括 `MetaVault.sol` 中的 `assetsMap`、`pUSDeDepositor.sol` 中的 `autoSwaps` 和 `MockStakedUSDe.sol` 中的 `cooldowns`。這些映射分別追蹤資產配置、自動交換設置和用戶冷卻期狀態。缺乏明確的鍵和值名稱使這些聲明在集成和未來重構中不夠自我說明且更容易出錯。

**影響：**
代碼質量問題。沒有直接安全影響。未記錄的映射語義增加了審查時間和誤用的機會。

**修復建議：**
在預存款合約的所有映射聲明中添加命名鍵和值參數，遵循 Solidity 0.8.18 語法。

---

## 20. Use Named Mappings to Explicitly Denote the Purpose of Keys and Values (protocol)

**Severity:** 🟡 Medium
**Source:** `cyfrin/protocol.md`

**Description:**
The `Majority Games` protocol uses named mappings in some contracts but not others. Several mappings across the protocol's contracts — including those tracking player deposits, game pools, and fee configurations — are declared without explicit key or value name annotations. The inconsistency means some contract declarations are self-documenting while others require contextual inference. A fully consistent application of named mapping parameters would make the entire contract suite easier to audit.

**Impact:**
Code-quality issue. No direct security impact. The inconsistency increases auditor effort and raises the risk of misinterpretation in less documented mappings.

**Recommended Mitigation:**
Audit all mapping declarations throughout the protocol contracts and apply named parameters consistently to any that are missing them, following the pattern established in the contracts that already use this feature.

---

**[中文版本]**

**描述：**
`Majority Games` 協議在某些合約中使用命名映射，但在其他合約中不使用。協議合約中的幾個映射——包括追蹤玩家存款、遊戲池和費用配置的映射——在聲明時沒有明確的鍵或值名稱注釋。這種不一致意味著一些合約聲明是自我說明的，而另一些需要上下文推斷。

**影響：**
代碼質量問題。沒有直接安全影響。不一致性增加了審計員的工作量，並提高了在較少記錄的映射中誤解的風險。

**修復建議：**
審計協議合約中的所有映射聲明，並對任何缺少命名參數的聲明一致地應用命名參數，遵循已使用此功能的合約中建立的模式。

---

## 21. Use Named Mappings to Explicitly Indicate the Purpose of Keys and Values (wannabetv2)

**Severity:** 🟡 Medium
**Source:** `cyfrin/wannabetv2.md`

**Description:**
`WannaBet v2` contracts contain mapping declarations that lack named key and value parameters. Without explicit names at the declaration site, developers must rely on the variable name alone to understand what the mapping key represents — for example, whether a `mapping(address => Bet)` maps from a better's address, a bet ID, or some other address type. The Solidity 0.8.18 named mapping feature was introduced specifically to eliminate this ambiguity at the declaration level.

**Impact:**
Code-quality issue. No direct security impact. Unnamed mappings increase the cognitive load for auditors and increase risk of incorrect usage in future maintenance.

**Recommended Mitigation:**
Apply named mapping parameters to all mapping declarations in `WannaBet v2` contracts, explicitly naming both the key and value types with descriptive identifiers.

---

**[中文版本]**

**描述：**
`WannaBet v2` 合約包含缺少命名鍵和值參數的映射聲明。在聲明點沒有明確名稱的情況下，開發者必須僅依賴變量名來理解映射鍵代表什麼——例如，`mapping(address => Bet)` 是否從投注者的地址、投注 ID 或其他地址類型映射。Solidity 0.8.18 命名映射功能的引入正是為了在聲明層面消除這種歧義。

**影響：**
代碼質量問題。沒有直接安全影響。未命名的映射增加了審計員的認知負擔，並增加了未來維護中不正確使用的風險。

**修復建議：**
在 `WannaBet v2` 合約的所有映射聲明中應用命名映射參數，用描述性標識符明確命名鍵和值類型。

---

## 22. `eciesjs` Major Version Mismatch Between dApp SDK and Mobile Wallet Creates Untested Cryptographic Interoperability Risk

**Severity:** 🟡 Medium
**Source:** `cyfrin/connect.md`

**Description:**
The MetaMask `connect-multichain` dApp SDK uses `eciesjs` v0.4.16, while MetaMask Mobile uses `eciesjs` v0.3.21. Additionally, the mobile wallet specifies `secp256k1@^5.0.1` as a dependency of `eciesjs v0.3.21` but overrides it via a Yarn `resolutions` field to pin `secp256k1` at v4.0.4 — a full major version downgrade. The two library versions differ in their default hash functions, error handling, and constant-time guarantees. Because the dApp SDK and mobile wallet communicate by encrypting and decrypting messages using these libraries on opposite ends, the version mismatch and the secp256k1 override create an untested cross-platform cryptographic pairing.

**Impact:**
Silent decryption failures or degraded cipher parameters are possible if the two library versions produce envelope formats that differ in ways not immediately obvious. Cross-platform encrypt/decrypt round-trips may fail intermittently or exhibit subtly different security properties, and bugs arising from this mismatch are difficult to reproduce and diagnose.

**Recommended Mitigation:**
Align both the dApp SDK and mobile wallet on the same `eciesjs` major version (preferably 0.4.x). Remove or update the `secp256k1` Yarn resolution override so both sides use the same `secp256k1` version. Add CI integration tests that verify cross-platform encrypt/decrypt round-trips between the two sides.

---

**[中文版本]**

**描述：**
MetaMask `connect-multichain` dApp SDK 使用 `eciesjs` v0.4.16，而 MetaMask Mobile 使用 `eciesjs` v0.3.21。此外，移動錢包將 `secp256k1@^5.0.1` 指定為 `eciesjs v0.3.21` 的依賴項，但通過 Yarn `resolutions` 字段覆寫以將 `secp256k1` 固定在 v4.0.4——一個完整的主要版本降級。兩個庫版本在其默認哈希函數、錯誤處理和恆定時間保證方面有所不同。

**影響：**
如果兩個庫版本產生以不立即明顯的方式不同的信封格式，可能會出現靜默解密失敗或降級的密碼參數。跨平台加密/解密往返可能間歇性失敗或表現出細微不同的安全屬性。

**修復建議：**
使 dApp SDK 和移動錢包都使用相同的 `eciesjs` 主要版本（最好是 0.4.x）。刪除或更新 `secp256k1` Yarn 解析覆寫，以便雙方使用相同的 `secp256k1` 版本。添加 CI 集成測試，驗證兩側之間的跨平台加密/解密往返。

---

## 23. `yUSDeVault` Edge Cases Should Be Explicitly Handled to Prevent View Functions From Reverting

**Severity:** 🟡 Medium
**Source:** `cyfrin/predeposit.md`

**Description:**
Per the ERC-4626 specification, `previewDeposit` and `previewMint` must not revert due to vault-specific limits. However, several code paths in `yUSDeVault` can revert unexpectedly. `totalAccruedUSDe` calls `_convertAssetsToUSDe(pUSDeAssets, true)` without checking whether `pUSDeAssets` is zero first; when it is zero, `pUSDeVault::previewRedeem` can revert due to division-by-zero in `previewYield` when the `yUSDe` vault holds no pUSDe balance. Both `previewDeposit` and `previewMint` call `totalAccruedUSDe` internally and also rely on `_valueMulDiv` which can revert when the denominator is zero. These edge cases all arise in valid operational states — specifically when the yUSDe vault has no pUSDe balance — and should be explicitly short-circuited to return zero rather than reverting.

**Impact:**
View functions that the ERC-4626 specification guarantees should not revert will revert in normal operational states (empty vault, no pUSDe deposited), breaking any aggregator, UI, or integration that calls these functions for simulation or display purposes.

**Recommended Mitigation:**
Add explicit zero-checks at the start of `totalAccruedUSDe` (returning 0 when pUSDe balance is zero) and handle the zero-assets/shares edge cases in `_convertAssetsToUSDe` and `previewYield` to return 0 instead of reverting.

---

**[中文版本]**

**描述：**
根據 ERC-4626 規範，`previewDeposit` 和 `previewMint` 不得因金庫特定限制而回退。然而，`yUSDeVault` 中的幾個代碼路徑可能意外回退。`totalAccruedUSDe` 在調用 `_convertAssetsToUSDe(pUSDeAssets, true)` 之前沒有先檢查 `pUSDeAssets` 是否為零；當它為零時，`pUSDeVault::previewRedeem` 可能因 `previewYield` 中的除以零而回退，當 `yUSDe` 金庫沒有 pUSDe 餘額時。`previewDeposit` 和 `previewMint` 都在內部調用 `totalAccruedUSDe`，並依賴於當分母為零時可能回退的 `_valueMulDiv`。這些邊緣情況都出現在有效的操作狀態中——特別是當 yUSDe 金庫沒有 pUSDe 餘額時。

**影響：**
ERC-4626 規範保證不應回退的視圖函數在正常操作狀態下（空金庫、無 pUSDe 存入）會回退，破壞任何為模擬或顯示目的調用這些函數的聚合器、UI 或集成。

**修復建議：**
在 `totalAccruedUSDe` 開頭添加明確的零檢查（當 pUSDe 餘額為零時返回 0），並在 `_convertAssetsToUSDe` 和 `previewYield` 中處理零資產/份額的邊緣情況，返回 0 而不是回退。
