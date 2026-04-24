# hacken_note

first: 在細看hacken.io 找到有 "critical / high / medium 的audit issue, 並只找fixed/mitigated 的issue", 而且該repo 是public 的
重點1: 找到該repo 並熟悉, 不用從exploit 的角度看
重點2: back to commit, 找出問題並整理進去prompt, 用自己的話分類和說明, 慢慢看 多學點
重點3: 用ai 問怎麼用test tool 來找到問題

根據 https://github.com/msitarzewski/agency-agents/blob/main/specialized/blockchain-security-auditor.md
只要在cursor 説 "Activate Blockchain Security Auditor mode, ...." 然後搭配筆記(auditor 找到並且被接受的漏洞)

進度: (knoxnet~sakle)

[
    https://hacken.io/audits/digital-oro-international/sca-digital-oro-sweepstakes-sep2025/#Findings

    根據這份文件的 finding 分別給出相對應的中文prompt
    這個prompt 需要是很general 的敘述, 讓我可以把這個prompt 使用到其他專案上
    將prompt 根據basic, bridge, delegate call, lending, timing, auth gasSafing 進行分類
    只需要給prompt 即可, 不需給程式碼和分析
    並附上是參考文件中哪個audit issue 而產生的prompt, 也附上網址
    未在本審計報告中出現的issue 就不要列出來
    忽略low 和Observation, accepted的issue
]

prompt:
PDF rename: 根據pdf report 的標題重新命名pdf file, 以Customer 命名即可，例如Dlicom

pdf to knowledgeBase: 將pdf 中medium, high 而且是被fixed 的issue 整理出來, 包含內容出處資訊, 詳細解釋和說明該issue 以及如何fix, 並根據內容類型將內容寫入對應的folder README 中, 如果沒有在分類內就放進other