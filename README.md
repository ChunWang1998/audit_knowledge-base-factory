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
我現在想要對 @yearn/TokenizedStrategy.sol 進行audit, 找出issue, 藉由 @prompts 內的prompts 找出問題. 我要先以@logic-griefing-economic-distribution.txt 進行audit, 將結果輸出在 issue.txt中. 找問題時要遵守 @immunefi/Immutifi Feasibility Limitations.md  的規範

agents2:
用 @accounting-balance-cross-contract.txt 做一樣的事情

agents3:(換一個high model)
將 @issues/issue.txt 的關於 @yearn/TokenizedStrategy.sol 的漏洞確認過是否真的存在, 並且刪除不合理issue, 並重新修改 @issues/issue.txt 

(自己確認過)

agents4: 
@issues/issue.txt:1-240 把該issue1 用 @immunefi/3-Immutifi submitField.txt 的格式完整描述

agents5: 
把兩個report 用更口語的方式重寫, 並且給一份中文report






## murmur
- 大部分bug bounty 的out of scope都在說什麼? 拒絕的理由? 是否可以用來filter 目前的knowledge base
- 在cursor run 的篩選部分, 可以把篩選理由也放進prompt
- 最好的model: Opus


怎麼訓練出好的prompt 
- 大量參考data set 中accepted, 且fixed 的issue. 目前只參考hacken 和sherlock
- llm as judge: 用low model 當audit agent, 用medium model 當judge. 因為要用cursor 額度所以需要手動貼上內容來judge
(真的還需要訓練prompt 嗎? 其實感覺已經很好了, 只需要用好的high model來跑了)
  
怎麼有效的用現有的prompt 來進行audit(多個model 多次audit 多個不同層面的prompt)
- 直接就用high 去找issue 吧
