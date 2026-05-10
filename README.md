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
1. code4rena (可以提交兩次)(POC 不用整個file! function 即可)
https://code4rena.com/bounties
https://code4rena.com/audits

a. Monetrix

2. immunefi 
https://immunefi.com/bug-bounty/?filter=language%3DSolidity

3. Cantina (幾乎都deposit required)

a. BitGo

4. HackenProof (要求的reputation 很高)

5. sherlock (要先deposit 250U 進去!)

## Use knowledgebase to audit 
根據 https://github.com/msitarzewski/agency-agents/blob/main/specialized/blockchain-security-auditor.md
只要在cursor 説 "Activate Blockchain Security Auditor mode, ...." 然後搭配筆記(auditor 找到並且被接受的漏洞)

1. 下載目標repo
2. 把knowledgeBase/ 放到repo 中
3. install auditor agent: /Users/leo_1/Documents/GitHub/superpredict/agency-agents/scripts/install.sh --tool cursor
4. 下prompt: 
   
grok1:
我接下來要進行audit bug bounty
根據以下網站回答問題:
https://github.com/ChunWang1998/audit_knowledge-base-factory/tree/main
...
這是bug bounty 的內容, 之後都簡稱為bug bounty scope:



grok2:
highly cross-referencing all the files/issues in knowledgeBase repo knowledgebase/access-control
and based on folder name (which is the exploit type) + conceptual similarity to find the most relevant issues (even if the title is not 1:1 exact match).
Always list exactly the top 2 most relevant issues (High or Medium severity is fine; do not skip Medium if it is conceptually strong).
Output them in English and Chinese using this exact issue format:

knowledgeBase type: (based on the folder name ex: access-control/role-model/blacklisted-users — must be at least 3 layers)
The main reference issue title in knowledgeBase: (use the closest matching / conceptually strongest title from the KB README; if no perfect match, use a clear descriptive title that best represents the concept)
File Location: 
Issue Description: 
Attack scenario: 

Before logging the data, double-check these rules:
1. knowledgeBase type should be at least 3 layers
2. The main reference issue title in knowledgeBase field should be the strongest conceptual match (semantic similarity based on exploit type/folder name) — exact wording is NOT required
3. the issue you found is a real violation / risk in the target code, is in-scope for the bug bounty, and does NOT rely on violating the explicit "Out-of-Scope" or "Design-Accepted & Trust Assumptions" sections (but Medium griefing / edge-case issues are still valid if they can cause real operational impact or fund risk).

If you find fewer than 2 strong matches, still list the 2 closest conceptual ones and note the severity clearly.


grok3:
repeat the same workflow on knowledgeBase/accounting, Strongly map the top 2 most relevant issues (High or Medium severity is fine) using folder name + conceptual similarity. Report even if they are borderline or Medium — as long as they are in-scope and exploitable.

knowledgeBase/dos-liveness
knowledgeBase/oracle-pricing
knowledgeBase/token-transfer
knowledgeBase/upgrade-config
knowledgeBase/withdrawal-redeem
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
   4. 最核心的file 和functions note
   5. key word in repo
   6. 一些基本的work flow
   7. 可以學起來的地方(名詞概念)

Q:
- 根據repo readme 說明該專案的目的
- 列出三個最核心的smart contract 並介紹
- 根據test file 給出基本的work flow
- 介紹專案中一些比較重要的名詞和概念


1. 用grok `export` go through knowledgebase 的folder, 參考上述"highly cross-referencing..."
2. 了解用AI 找到的對應的knowledge base 內容
3. 將1, 2 的結果可以整理成一份note, 用該note 進行篩選(可以用test file 重現, 符合readme scope)
4. 用篩選過的issue 來寫test, 在cursor 做比較好, 不然會常常compile fail from grok



knowledgeBase type: token-transfer/erc20-edge-cases/fee-on-transfer
The main reference issue title in knowledgeBase: Fee-on-Transfer Token Dust in Forwarder Flush
File Location: contracts/ForwarderV4.sol (flushTokens、batchFlushERC20Tokens) 與 contracts/WalletSimple.sol (flushForwarderTokens)
Issue Description: Forwarder 合約會先查詢 ERC20 目前餘額，再使用 TransferHelper.safeTransfer 嘗試轉出全額。對於 fee-on-transfer 代幣，接收方（parent wallet）實際收到的金額會少於預期，導致 forwarder 內留下 dust 並造成預期資金與實際資金的 accounting desynchronization（與 fee-on-transfer 模式高度概念吻合）。
Attack scenario: 用戶或攻擊者向 Forwarder 地址發送 fee-on-transfer 代幣。呼叫 flushTokens 時，parent 只收到少於 balanceOf 的金額。重複 flush 會累積 dust 或在 BitGo 託管系統中造成對帳錯誤（Medium 等級資金管理風險，完全符合 in-scope）。