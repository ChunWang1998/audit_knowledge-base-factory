Issue #1
knowledgeBase type: token-transfer/cross-chain-accounting  
The main reference issue title in knowledgeBase: cross-chain-accounting (4)  
File Location: src/core/MonetrixAccountant.sol, src/core/PrecompileReader.sol, src/core/MonetrixVault.sol (functions: _readL1Backing, settleDailyPnL, injectYield)  
Issue Description: Cross-chain token transfers (bridge inflows/outflows) are recorded via HyperCore precompile without verifying the exact transferred amount against the reported L1 event. A mismatch between the amount the bridge actually delivered and the Accountant-recorded value is never reconciled, breaking the 4-gate pipeline invariants.  
Issue Description (中文): 跨鏈代幣轉移（橋接流入/流出）是通過 HyperCore precompile 記錄，卻未將實際轉移數量與 L1 事件報告進行核對。橋接到賬量與會計記錄間差異永不補償，導致 4-gate 管線不再可靠。
Attack scenario: During a high-volume redemption period (Areas of concern #3), an attacker or bridge delay causes a partial transfer (e.g., 1 wei short due to L1 gas). The Accountant still credits the full amount in totalBackingSigned(), letting the Operator declare inflated proposedYield. This creates unbacked yield injection into sUSDM, permanently diluting all stakers while the real backing is lower than reported.  
Attack scenario (中文): 在高贖回期（關注重點 #3），攻擊者或橋故意延遲導致實際僅部分轉帳（如因 L1 gas 損耗而短 1 wei）。會計仍按全額記入 totalBackingSigned()，讓 Operator 報告溢出收益。如此會將無底層資產支持的收益注入 sUSDM，永久稀釋所有持有人份額，實際支持低於報告。

Issue #2
knowledgeBase type: withdrawal-redeem/queue-dos/withdrawal-requests
The main reference issue title in knowledgeBase: queue-dos (50)
File Location: src/core/RedeemEscrow.sol, src/core/MonetrixVault.sol, src/tokens/sUSDM.sol (functions: requestRedeem, fundRedemptions, claimRedeem)
Issue Description: The redemption queue in RedeemEscrow.sol has no mechanism to skip or remove a single failing/stuck request. When a request encounters a revert in claimRedeem() (e.g., due to transient L1 bridge delay or dust accounting mismatch), the entire queue processing halts permanently because fundRedemptions() loops until every request succeeds.
Issue Description (中文): RedeemEscrow.sol 的贖回隊列沒有跳過或移除單一失敗/卡住請求的機制。當某筆請求在 claimRedeem() 觸發 revert（例如因 L1 bridge 暫時延遲或 dust 會計 mismatch），整個 fundRedemptions() 迴圈就會永久卡住，因為它必須等到每筆請求都成功才繼續。
Attack scenario: During a bank-run (Areas of concern #3), an attacker submits a crafted requestRedeem() that will always revert on claim. Keepers calling fundRedemptions() get stuck forever. All legitimate redemptions behind it become unclaimable, freezing user funds and causing the USDM peg to collapse while the protocol cannot process any further outflows.
Attack scenario (中文): 在 bank-run 期間（Areas of concern #3），攻擊者提交一筆故意會在 claim 時 revert 的 requestRedeem()。當 keeper 呼叫 fundRedemptions() 時就會永久卡住。所有排在後面的合法贖回都無法 claim，使用者資金被凍結，USDM peg 崩潰，而協議無法處理任何後續流出。