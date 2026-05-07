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
highly cross-referencing all the files/issues in knowledgeBase repo [FOLDER_NAME]
and based on folder name (which is the exploit type) + conceptual similarity to find the most relevant issues (even if the title is not 1:1 exact match).
Only listed the most two highest-severity exploitable issues with english and chinese

the issue format:
knowledgeBase type: (based on the folder name ex: access-control/role-model/blacklisted-users — must be at least 3 layers)
The main reference issue title in knowledgeBase: (use the closest matching / conceptually strongest title from the KB README; if no perfect match, use a clear descriptive title that best represents the concept)
File Location: 
Issue Description: 
Attack scenario: 

before you log the data, double check that:
1. knowledgeBase type should be at least 3 layers
2. The main reference issue title in knowledgeBase field should be the strongest conceptual match (semantic similarity based on exploit type/folder name) — exact wording is NOT required
3. the issue you found is a real violation / risk in the target code and does not violate any design-accepted assumptions in the bug bounty scope


grok3:
repeat the same workflow,  but this time select the top 2 issues by strongly mapping them to knowledgeBase/withdrawal-redeem
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

