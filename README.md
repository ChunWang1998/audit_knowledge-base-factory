# hacken_note

在找repo時也看: 是否有public 的repo 可以也記錄在這
可以稍微看一下report, 如果沒有符合的issue 甚至不用下載

根據 https://github.com/msitarzewski/agency-agents/blob/main/specialized/blockchain-security-auditor.md
只要在cursor 説 "Activate Blockchain Security Auditor mode, ...." 然後搭配筆記(auditor 找到並且被接受的漏洞)

進度: (knoxnet~sakle)

prompt:
`PDF` rename: 根據pdf report 的標題重新命名pdf file, 以Customer 命名即可，例如Dlicom
pdf to knowledgeBase: 將pdf 中medium, high 而且是被fixed 的issue 整理出來, 包含內容出處資訊, 詳細解釋和說明該issue 以及如何fix, 並根據內容類型將內容寫入對應的folder `README` 中, 如果沒有在分類內就放進other

backtest: TODO
先找到確定有問題的github repo commmit, 不論是否是knowledgebase 來源都可以試看看, 看有沒有辦法偵測到
至少來源一定要偵測到

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
