Activate @.cursor/rules/blockchain-security-auditor.mdc mode
highly cross-referencing to @knowledgeBase/access-control,
and based on folder name, which is exploit type to find the issues and generate a readme
Only listed the most two highest-severity exploitable issues with english and chinese
the issue format:
knowledgeBase type: (based on the folder name ex: access-control/role-model/blacklsted-users)
The main reference issue title in knowledgeBase:(ex: if this issue mainly refer to the issue ` Lack of Access Control Enabling Unauthorized Credential Issuance and Revocation` in access-control/role-model/blacklsted-users readme, the content should be this)
File Location: 
Issue Description: 
Attack scenario:

---------------------------------------------
when finding vulnerabilities, always follow README.md, only check the contracts in `Files in scope` part
focus on `Areas of concern (where to focus for bugs)` part in README.md
v12 test result is in @v12.txt, the issue overlap with @v12.txt findings is not allowed.

repeat the same workflow,  but this time select the top 2 issues by strongly mapping them to knowledgeBase/accounting, keep the existing content and append the new section
double check the issue is not repeated in @v12.txt
double check the issue in @test/c4/README.md is in Areas of concern (where to focus for bugs) in @README.md

(check again with the constraint in the readme)

list the most 3 reasonable, highest-severity exploitable issues based on the `Areas of concern` in readme



grok:
https://grok.com/c/8cd03560-1fd7-4ca0-a93a-16c161c210be?rid=4bc640de-3420-4c6f-9332-4d209de4ce38

Issue #1
knowledgeBase type: token-transfer/cross-chain-accounting  
The main reference issue title in knowledgeBase: cross-chain-accounting (4)  
File Location: src/core/MonetrixAccountant.sol, src/core/PrecompileReader.sol, src/core/MonetrixVault.sol (functions: _readL1Backing, settleDailyPnL, injectYield)  
Issue Description: Cross-chain token transfers (bridge inflows/outflows) are recorded via HyperCore precompile without verifying the exact transferred amount against the reported L1 event. A mismatch between the amount the bridge actually delivered and the Accountant-recorded value is never reconciled, breaking the 4-gate pipeline invariants.  
Issue Description (中文): 跨鏈代幣轉移（橋接流入/流出）是通過 HyperCore precompile 記錄，卻未將實際轉移數量與 L1 事件報告進行核對。橋接到賬量與會計記錄間差異永不補償，導致 4-gate 管線不再可靠。
Attack scenario: During a high-volume redemption period (Areas of concern #3), an attacker or bridge delay causes a partial transfer (e.g., 1 wei short due to L1 gas). The Accountant still credits the full amount in totalBackingSigned(), letting the Operator declare inflated proposedYield. This creates unbacked yield injection into sUSDM, permanently diluting all stakers while the real backing is lower than reported.  
Attack scenario (中文): 在高贖回期（關注重點 #3），攻擊者或橋故意延遲導致實際僅部分轉帳（如因 L1 gas 損耗而短 1 wei）。會計仍按全額記入 totalBackingSigned()，讓 Operator 報告溢出收益。如此會將無底層資產支持的收益注入 sUSDM，永久稀釋所有持有人份額，實際支持低於報告。

grok for the issue:
https://grok.com/c/4210bf54-577c-4e97-9ba9-beea3d3eeecd?rid=8228556b-d292-4802-ae4c-90f16490d86d

