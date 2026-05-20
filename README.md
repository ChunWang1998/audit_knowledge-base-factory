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
1. immunefi 
https://immunefi.com/bug-bounty/?filter=language%3DSolidity%26programType%3DSmart%2BContract
幾乎都是很古早發的
記得先去submit 看看是否需要很高的whitehat才能提交

a. Gearbox

b. Linea

c. Enzyme Onyx

2. Cantina (幾乎都deposit required)

a. BitGo

3. HackenProof (要求的reputation 很高)

4. sherlock (要先deposit 250U 進去!)

## Audit approach

1. use knowledgeBase create by myself in Grok
   
grok1:
我接下來要進行audit bug bounty
這是需要被進行audit 的repo:
...
這個repo是我主要要拿來當作參考的資料庫(接下來簡稱knowledgeBase) 
https://github.com/ChunWang1998/audit_knowledge-base-factory/tree/main

任何回答都要嚴格遵照 scope.txt 和 Immutifi Feasibility Limitations.md

根據以上內容回答我接下來的問題：







然後:
1. 手動移除標有false positive 的issue, 重新給這些issues 編號
2.double check founded issues on Cursor, make sure it's make sense on current codebase:
這些issues 在目前的codebase 都是valid的嗎? 都是符合scope 規範嗎? 列出一個表格整理valid/invalid 還有嚴重等級
1. 將filter 好的issue 存在issues.txt
2. 在cursor run:
generate a report.txt, 根據 @submitField.txt 來完成 @issues.txt 提到的issues. 如果issues 中的內容和 contracts/ 不同, 以contracts 為主來調整report 內容 
1. 換個model ask:
這份report 有符合 scope.txt 嗎? 根據 contracts , 內容是正確的嗎?




2. use md file in cursor

You are the Blockchain Security Auditor as defined in the complete [blockchain-security-auditor.md](https://github.com/msitarzewski/agency-agents/blob/main/specialized/blockchain-security-auditor.md) document (now loaded as your core identity and methodology). You are performing a professional, paranoid, adversarial smart contract security audit for an official bug bounty program.
Repository to audit: https://github.com/dextrade-solutions/UP10-Smart-Contracts/tree/def382048e4739ae306f1aaa603f0db08af024b8
Bug Bounty Scope: contracts/
Strict rules you MUST obey at all times:

Report bugs that map directly to Critical, High, Medium, or Low severity impacts defined in the scope (Critical/High prioritized for rewards, Medium/Low also fully accepted).
Apply Primacy of Impact for all Critical and High smart contract findings.
Exclude every known issue listed in the scope’s GitHub links, disclosures folder, or previously reported bugs.
PoC is mandatory for every finding: provide complete, compilable Solidity + Foundry/Hardhat code that reproduces the issue on a local fork only.

For every potential vulnerability, output exactly: (1) file path + exact line numbers, (2) clear title, (3) detailed attack scenario with realistic conditions, (4) estimated funds-at-risk / economic impact, (5) full working PoC code, (6) exact severity mapping to the bounty scope (Critical/High/Medium/Low), (7) recommended fix that does not introduce new issues.

Systematically apply EVERY section and checklist from blockchain-security-auditor.md: access control, reentrancy & callbacks, oracle manipulation, token accounting & flow tracing, flash-loan vectors, composability & integration risks, invariant breaking, MEV extraction, griefing, unbounded gas, upgradeability/pausability, cross-contract interactions, and all edge-case business logic.
Workflow:

First list all main contracts in the repo and their primary functions.
Perform static + manual line-by-line analysis on the highest-risk contracts.
Conduct full composability review across multiple contracts.
End with a clean summary table of all Critical/High/Medium/Low findings (sorted by severity). 

Be extremely thorough and think like a sophisticated attacker with unlimited flash loans and perfect protocol knowledge. Begin the audit now.





## murmur
- 不知道哪一種類型的vulnerability 最容易被接受?
- 就算沒找到問題 也至少要更熟knowledge base 的內容
- 大部分bug bounty 的out of scope都在說什麼? 拒絕的理由? 是否可以用來filter 目前的knowledge base
- 新增reports?
- 增加機會: 加入參考的reference issue, 內容口語避免被歸類為AI report
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

- 現在的prompt還沒有很好, 多透過"舊的repo" 和 "auditor md" 找漏洞來回測, 直到可以用很general 的方式回測找到為止
- 要先做deep architecure 分析?
https://grok.com/c/2533847a-996d-46dc-8bcb-c1b7efe5132b?rid=d82afc71-165f-40e3-a03f-1ccb7e71ad77