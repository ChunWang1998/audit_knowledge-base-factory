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

3. HackenProof 
先submit 看看需不需要 reputation 或是fee

a. Hyperbridge Protocol

4. sherlock 
幾乎都要先deposit 250U 進去

## Audit approach

1. use knowledgeBase create by myself in Grok
   
grok1:
我接下來要進行audit bug bounty
這是需要被進行audit 的repo:
...
這個repo是我主要要拿來當作參考的資料庫(接下來簡稱knowledgeBase) 
https://github.com/ChunWang1998/audit_knowledge-base-factory/tree/main

任何回答都要嚴格遵照 scope.txt

根據以上內容回答我接下來的問題：



然後:
- 手動移除標有false positive 的issue, 重新給這些issues 編號
- double check founded issues on Cursor, make sure it's make sense on current codebase:
這些issues 在目前的codebase 都是valid的嗎? 都是符合scope 規範嗎? 列出一個表格整理valid/invalid 還有嚴重等級
- 將filter 好的issue 存在issues.txt
- (optional): issues 在 ... 的issue 中, 概念和該issue 最像的是哪一個?
- 在cursor run:
generate a report.txt, 根據 @submitField.txt 來完成 @issues.txt 提到的issues. 如果issues 中的內容和 contracts/ 不同, 以contracts 為主來調整report 內容 
- 換個model ask:
這份report 有符合 scope.txt 嗎? 根據 contracts , 內容是正確的嗎?
- 修改內容, 讓內容更口語化

## murmur
- 大部分bug bounty 的out of scope都在說什麼? 拒絕的理由? 是否可以用來filter 目前的knowledge base
- 在cursor run 的篩選部分, 可以把篩選理由也放進prompt
- 從拿去codebase 做issue review 產生的review.txt 來優化prompt, 不過可能要多搜集一點review.txt 才知道prompt 會犯什麼通病

## target repo: 要更有效的go through 整份repo 來找issue
a. 可能需要透過graph 來進行分析, 生成檔案讓找漏洞更簡單
-> run static analysis to create summaries and graphs from Slither:
- contract_summary.md (state vars, functions, modifiers, external calls)
- call_graph.dot + inheritance tree
- data-flow diagrams


TODO:
- 整理 list.txt, hacken, sherlock (可以透過要求fetch 後的資料的內部內容確保ai 沒有亂給? 例如要給readme 第一個字)
- 新增peckshield and credSheild
- list.txt 3個train 3個評分(大量參考實際audit 結果)
- 問grok 怎麼透過skillopt 對list.txt 的內容進行audit, 並且前提是只有supergrok 的訂閱下(沒有openai)

GitHub https://github.com/ChunWang1998/audit_knowledge-base-factory/tree/main 這是我用來訓練用來做smart contract audit prompt 的repo, 我從dataSetResouce/ 找出一些內容列在list.ts中, 我想要拿list.ts 中public 的repo 拿來做prompt 的訓練, 訓練方式是用 skillopt/ 的程式碼來訓練出各個vulnerability type的prompt(參考knowledgeBase/ 的分類).  在skillopt 訓練出來的prompt 會拿來替代目前prompts/ 的內容.



訓練重點是訓練出來的prompt 應該要能從public repo 找到audit report的問題, 例如Aave labs: https://github.com/aave/aave-v4/tree/dc31f9a4d54c0503093ef6939e6e8a8d2586709d 中, 應該要能夠用prompts 找到shrelock aave labs pdf 中的findings, 這個可以拿來當作訓練用的分數標準



給出詳細實作流程, 以及如何解決"skillopt 是用openai api key 但我只有訂閱grok 的 supergrok" 這個問題



可以完全忽略 auditnotes/, fetchfreeOpenapikey/ immunifi/