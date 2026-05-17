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

2. Cantina (幾乎都deposit required)

a. BitGo

3. HackenProof (要求的reputation 很高)

4. sherlock (要先deposit 250U 進去!)

## Audit approach

1. use knowledgeBase create by myself in Grok
   
grok1:
我接下來要進行audit bug bounty
根據以下網站回答問題:
https://github.com/ChunWang1998/audit_knowledge-base-factory/tree/main
...
這是bug bounty 的內容, 之後都簡稱為bug bounty scope:



grok2:
highly cross-referencing "each issue" in knowledgeBase repo knowledgebase/access-control
and based on folder name (which is the exploit type) + conceptual similarity to find the most relevant issues (even if the title is not 1:1 exact match).
Always list exactly the top 2 most relevant issues (High or Medium severity is fine; do not skip Medium if it is conceptually strong).
Output them in English and Chinese using this exact issue format:

knowledgeBase type: (based on the folder name ex: access-control/role-model/blacklisted-users — must be at least 3 layers)
The main reference issue title in knowledgeBase: (use the closest matching / conceptually strongest title from the KB README; if no perfect match, use a clear descriptive title that best represents the concept)
File Location: 
Issue Description: 
Attack scenario: 

Before logging the data, double-check these rules:
1. knowledgeBase type should be at least 3 layers
2. The main reference issue title in knowledgeBase field should be the strongest conceptual match (semantic similarity based on exploit type/folder name) — exact wording is NOT required
3. the issue you found is a real violation / risk in the target code, is in-scope for the bug bounty, and does NOT rely on violating the explicit "Out-of-Scope" or "Design-Accepted & Trust Assumptions" sections (but Medium griefing / edge-case issues are still valid if they can cause real operational impact or fund risk).
4. **Mandatory code verification step**: Before reporting ANY issue, you MUST first inspect the actual source code of the mentioned files/functions in the target repo. Quote or describe the relevant code snippets that prove the vulnerability actually exists.

5. "PRIVILEGED-ACCESS FILTER (MANDATORY): Only report issues that can be triggered by unprivileged / external callers. Explicitly exclude anything that requires onlyOwner, auditor signatures. If it needs privileged access → immediately mark INVALID and do not list."

6. **If a strong mitigation exists, do NOT report the issue** unless the mitigation itself is broken or bypassable. Clearly state “mitigation present” and move on. Only report issues that survive this verification.

7. **False-positive avoidance**: If the KB concept is conceptually similar but the implementation already addresses it, note it as “false positive due to X mitigation” and do not list it as a valid bug.
If you find fewer than 2 strong matches, still list the 2 closest conceptual ones and note the severity clearly.
8. **GOVERNANCE-CONTROLLED STATE FILTER (MANDATORY)**: If the vulnerable 
   state (array length, parameter value, list size, etc.) can ONLY grow 
   or change via a privileged role (governance, multisig, admin), AND the 
   attack path requires that role to act negligently or maliciously, 
   mark the issue INVALID. Specifically:
   - DoS/gas issues on arrays/lists that are exclusively populated by 
     governance → INVALID (governance is trusted not to bloat them)
   - Precision/math issues that only manifest when a governance-set 
     parameter hits an extreme value → INVALID
   - Exception: if you can demonstrate that the array/parameter CAN grow 
     through unprivileged user actions (e.g., anyone can push to the 
     array), it remains VALID.
   Always check: "Who controls the size/value of the vulnerable state?" 
   If the answer is only governance/admin → mark INVALID.

grok3: 
repeat the same workflow on knowledgeBase/accounting, Strongly map the top 2 most relevant issues (High or Medium severity is fine) using folder name + conceptual similarity. Report even if they are borderline or Medium — as long as they are in-scope and exploitable.

---------------------------------------------
knowledgeBase/accounting
knowledgeBase/dos-liveness
knowledgeBase/external-dependencies
knowledgeBase/griefing-attacks/gas-griefing
knowledgeBase/griefing-attacks/logic-griefing
knowledgeBase/griefing-attacks/withdrawal-griefing
knowledgeBase/token-transfer
knowledgeBase/upgrade-config


然後:
1. 手動移除標有false positive 的issue, 重新給這些issues 編號
2.double check founded issues on Cursor, make sure it's make sense on current codebase:
這些issues 在目前的codebase 都是valid的嗎? 都是符合scope 規範嗎? 列出一個表格整理valid/invalid 還有嚴重等級
3. 將filter 好的issue 存在issues.txt
4. 在cursor run:
generate a report.txt, 根據 @submitField.txt 來完成 @issues.txt 提到的issues. 如果issues 中的內容和 contracts/ 不同, 以contracts 為主來調整report 內容 
5. 換個model ask:
這份report 有符合 scope.txt 嗎? 根據 contracts , 內容是正確的嗎?




2. use md file in cursor
Activate @.cursor/rules/blockchain-security-auditor.mdc mode 




## murmur
- 不知道哪一種類型的vulnerability 最容易被接受?
- 就算沒找到問題 也至少要更熟knowledge base 的內容
- 大部分bug bounty 的out of scope都在說什麼? 拒絕的理由? 是否可以用來filter 目前的knowledge base
- 新增reports?
- 是否在report 中加入issue reference 比較有機會?
- 現在的指令可能還沒有很好, 多透過"舊的repo" 和 "auditor md" 找漏洞來回測
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

