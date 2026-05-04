# Knowledgebase

## resorce 
- hacken
resouce: https://hacken.io/audits/
scope: knoxnet~seedify

- sherlock
resouce: https://github.com/sherlock-protocol/sherlock-reports/tree/main/audits
scope: 2025~2026.03

- cyfrin
recouse: https://github.com/Cyfrin/cyfrin-audit-reports/tree/main/reports
scope:

- credshield
resouce: https://github.com/Credshields/audit-reports
scope:

- peckshield
resouce: https://github.com/peckshield/publications/tree/master/audit_reports
scope: 

## Bug bounty platform rank
1. code4rena (可以提交兩次)
https://code4rena.com/bounties
https://code4rena.com/audits

a. Monetrix

2. immunefi 
https://immunefi.com/bug-bounty/?filter=language%3DSolidity

3. Cantina (幾乎都deposit required)
TODO: https://cantina.xyz/code/78a734d2-b460-4245-9c81-833487d6a339/overview

4. HackenProof (要求的reputation 很高)

5. sherlock (要先deposit 250U 進去!)

## Use knowledgebase to audit 
根據 https://github.com/msitarzewski/agency-agents/blob/main/specialized/blockchain-security-auditor.md
只要在cursor 説 "Activate Blockchain Security Auditor mode, ...." 然後搭配筆記(auditor 找到並且被接受的漏洞)

1. 下載目標repo
2. 把knowledgeBase/ 放到repo 中
3. install auditor agent: /Users/leo_1/Documents/GitHub/superpredict/agency-agents/scripts/install.sh --tool cursor
4. 下prompt: 
   
(agent)
Activate @.cursor/rules/blockchain-security-auditor.mdc mode
highly cross-referencing all the files in @knowledgeBase/access-control, (Don't invent a folder name by yourself)
and based on folder name, which is exploit type to find the issues and generate a readme
Only listed the most two highest-severity exploitable issues with english and chinese
the issue format:
knowledgeBase type: (based on the folder name ex: access-control/role-model/blacklsted-users)
The main reference issue title in knowledgeBase:(ex: if this issue mainly refer to the issue ` Lack of Access Control Enabling Unauthorized Credential Issuance and Revocation` in access-control/role-model/blacklsted-users readme, the content should be this)
File Location: 
Issue Description: 
Attack scenario: 

before you log the data, double check that:
1. knowledgeBase type should be at least 3 layers
2. The main reference issue title in knowledgeBase field should exactly match the sentence from issue in knowledgebase

---------------------------------------------





## murmur
- 不知道哪一種類型的vulnerability 最容易被接受?
- 就算沒找到問題 也至少要更熟knowledge base 的內容
- 勁量用grok 代替cursor 來問問題找問題, grok 讀得到public repo
flow:
1. 深入了解該repo, 第一輪先用grok 亂問,把不懂的名詞問一問丟給notebookLM(可以開三個copilot 來問比較好貼), 第二輪再寫一些note, 重點:
   1. 類型
   2. 通常該類型可能會有的問題
   3. 特別點
   4.最核心的file 和functions note
   4. 一些基本的work flow
   5. 可以學起來的地方(名詞概念)
2. 用grok `export` go through knowledgebase 的folder, 參考上述"highly cross-referencing..."
3. 了解用AI 找到的對應的knowledge base 內容
4. 將1, 2 的結果可以整理成一份note, 用該note 進行篩選(可以用test file 重現, 符合readme scope)
5. 用篩選過的issue 來寫test, 在cursor 做比較好, 不然會常常compile fail from grok


Issue #1
knowledgeBase type: token-transfer/cross-chain-accounting  
The main reference issue title in knowledgeBase: cross-chain-accounting (4)  
File Location: src/core/MonetrixAccountant.sol, src/core/PrecompileReader.sol, src/core/MonetrixVault.sol (functions: _readL1Backing, settleDailyPnL, injectYield)  
Issue Description: Cross-chain token transfers (bridge inflows/outflows) are recorded via HyperCore precompile without verifying the exact transferred amount against the reported L1 event. A mismatch between the amount the bridge actually delivered and the Accountant-recorded value is never reconciled, breaking the 4-gate pipeline invariants.  
Issue Description (中文): 跨鏈代幣轉移（橋接流入/流出）是通過 HyperCore precompile 記錄，卻未將實際轉移數量與 L1 事件報告進行核對。橋接到賬量與會計記錄間差異永不補償，導致 4-gate 管線不再可靠。
Attack scenario: During a high-volume redemption period (Areas of concern #3), an attacker or bridge delay causes a partial transfer (e.g., 1 wei short due to L1 gas). The Accountant still credits the full amount in totalBackingSigned(), letting the Operator declare inflated proposedYield. This creates unbacked yield injection into sUSDM, permanently diluting all stakers while the real backing is lower than reported.  
Attack scenario (中文): 在高贖回期（關注重點 #3），攻擊者或橋故意延遲導致實際僅部分轉帳（如因 L1 gas 損耗而短 1 wei）。會計仍按全額記入 totalBackingSigned()，讓 Operator 報告溢出收益。如此會將無底層資產支持的收益注入 sUSDM，永久稀釋所有持有人份額，實際支持低於報告。


https://grok.com/c/4210bf54-577c-4e97-9ba9-beea3d3eeecd?rid=8228556b-d292-4802-ae4c-90f16490d86d