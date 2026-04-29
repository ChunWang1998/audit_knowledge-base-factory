(ask)
從 
- @sherlockPDFTXT 找出high 和medium, 而且被fixed 的issue
- @HackenPDFTXT 找出critical, high, medium 而且被fixed 的issue
- @cyfrin 中找出 critical, high, medium 而且被fixed 的issue

用這些找到的issue 來進行分類


我需要用這些issue 來創建KnowledgeBase, 讓我可以用來參考audit 其他repo
將這些issue 進行分類, 分類最多三層, 每個子類型放5~20 個issue, 如果太多太少就進行調整
例如:
knowledgeBase/auth/access-control
knowledgeBase/auth/policy3
用這些issue依照上述層級來分類, 並將各層的數量寫在旁邊, 如果發現有明顯過大的分類層, 試著拆成更細子類, 並給出更新後的層級

(agent)
(複製上面給的分類樹)
根據上述的分類樹, 創建一個knowledgeBase 的readme 當作issue 的索引, 要包括:
1. 該issue來自哪個file(ex: cyfrin/aave3.3.md)
2. issue 名稱
整理完後double check 該readme 的issue 數量和上面整理的issue 數量是否相同, 確保沒有漏掉

(agent)
根據@knowledgeBase/readme 的分類創建資料夾, 每個資料夾放一個readme file 即可

(agent)
先試著整理access-control/role-model/owner-admin 給我看 確認是否正確

(agent)
根據 @knowledgeBase/readme 的分類, 將所有對應的issue 內容整理進去相對應的readme file, 內容整理要完全參考原本資料的內容, 要詳細, 不要包括程式碼 中英文都要 整理方式參考access-control/role-model/owner-admin 

