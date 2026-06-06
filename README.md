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

目前訓練效果不佳 因為消耗的token 太多, 而且因為一定要求要有找到issue 所以會一直訓練下去
不要訓練prompt 了
- 針對比較重要的類別
- 手動去修改prompt
- 善用db
- 與其創造倒不如用很多種prompt 讓AI產生上百個prompt 去測試已知? 然後一直合併優化
- 或是確保每個issue 都能找到再進行下一步
- 用不同llm 來多測試個幾次
- 一樣從兩個角度出發: 怎麼訓練出好的prompt 和怎麼有效的用現有的prompt 來進行audit