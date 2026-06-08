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
(很差的report, 無法看出the issues accepted by the team or not)

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

in target repo, agents1:
我現在想要對contract Moolah, contract PublicLiquidator 進行audit, 找出issue, 藉由 @prompts/ 內的prompts 找出問題. 我要先以logic-griefing , 並先以第一個prompt 進行audit, 幫我進行3 次獨立的audit, 並且結合結果產出2個最有效的issues, 將結果輸出在 issues.txt中. 找問題時要遵守 @Immutifi Feasibility Limitations.md  的規範

agents2:
對logic griefing 的其他prompt 做一樣的事情


## murmur
- 大部分bug bounty 的out of scope都在說什麼? 拒絕的理由? 是否可以用來filter 目前的knowledge base
- 在cursor run 的篩選部分, 可以把篩選理由也放進prompt
- 從拿去codebase 做issue review 產生的review.txt 來優化prompt, 不過可能要多搜集一點review.txt 才知道prompt 會犯什麼通病


怎麼訓練出好的prompt 
- train prompt with existing issues (X: cost a lot)
- 大量參考data set 中accepted, 且fixed 的issue. 目前只參考hacken 和sherlock
- 只針對最好的類型做audit: logic griefing, accounting, access-control 
  
怎麼有效的用現有的prompt 來進行audit(多個model 多次audit 多個不同層面的prompt)
- 一個type 多個prompt, 多個llm(找public 的, cost 怎麼取捨), 多次verify -> 好像只能手動開多個chat with diff llm 去跑
- 怎麼切入repo 比較省錢
- 每個階段的llm model 怎麼挑比較省錢


free llm in cursor:
composer 2.5 -> 太快了! -> auto
grok build 0.1 -> 很久!
sonnet 4.5 -> 還行 -> non auto