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

## PDF to knowledgebase
prompt:
`PDF` rename: 根據pdf report 的標題重新命名pdf file, 以Customer 命名即可，例如Dlicom
pdf to knowledgeBase: 將 PDF folder 中被fixed 的issue 整理出來放入 @knowledgeBase/ 中, 參考原本的內容來進行分類, 架構也參考原本的內容, 內容整理要完全參考pdf 內容, 要詳細

## Bug bounty platform rank
1. code4rena (可以提交兩次)
https://code4rena.com/bounties
https://code4rena.com/audits

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
Activate Blockchain Security Auditor mode, highly refer to @knowledgeBase/ , 並試著根據folder name 的type 來找出這份repo 中expoit issue並生成一份reamde 檔案, 並對於找到的issue 根據嚴重程度分類: high, meidium, low, observation, 並每個issue 都要附上問題的contract file name, 尤其是high, meidium
issue format:
knowledgeBase type:
Location: 
Issue: 
Attack scenario:
Impact:
(Optional) Similiar issue in knowledgeBase/ folder:
