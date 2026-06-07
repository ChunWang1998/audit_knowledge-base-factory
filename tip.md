• 高性價比主力（Discovery + 大量驗證）：
  • DeepSeek-V3 / V3.2 / R1 系列（尤其是 distill 版本）、Qwen2.5-Coder-32B / Qwen3 Coder 系列。
  • 平台：Groq（速度極快）、Fireworks、Together.ai、DeepSeek 官方、Alibaba。
  • 價格：blended 常見 $0.18~1.4 / M tokens，部分低到 $0.28 input / $0.42 output。比 Claude 便宜 10-20 倍以上。
  • 優勢：context 夠（128k+）、coding/reasoning 在開源模型中頂尖、適合第一輪掃 6 個 prompt。

• 最佳平衡（主力驗證 + 大多數最終 polishing）：
  • Claude Sonnet 4.6（$3 input / $15 output）。
  • 目前大多數人做嚴肅 code review / audit 時的甜蜜點。reasoning、long context、一致性都很好，價格比 Opus 便宜 40% 左右。

• 最終深挖 / 高信心 issue：
  • Claude Opus 4.6/4.7 系列（$5 / $25）。
  • 用在「已經篩到只剩 5~10 個候選 issue」時，讓它做最嚴格的 code verification + impact 量化 + PoC 草稿。
  • 也可以偶爾用 Gemini 2.5/3 Pro（長 context 性價比高，1M token 價格親民）做 cross-check。

• 其他可選：
  • Grok 系列（如果你有好 pipeline）。
  • Gemini Flash 系列做超低成本第一輪過濾。

實務成本策略：
• 一個中型合約（幾萬行）做完整 Logic Griefing 多 prompt 流程：Discovery 階段用 DeepSeek/Qwen 可能只要幾塊錢；Sonnet 驗證階段十幾到幾十塊；最後 Opus 只打幾個關鍵 issue，總成本可控在百元美金以內。
• 重點是用 prompt caching（Claude 很強）+ Batch API（50% off）+ 先用便宜模型過濾 80% 的 noise。

省額度 + 多樣性策略：

1. Discovery 階段（大量掃描）
   • 先用 Cursor 內的 Claude Sonnet 4.6（最划算）跑 3~4 個核心 prompt（base + low-cost-griefer + queue-forced-action + redemption）。
   • 把目標範圍縮小（不要一次丟整個 monorepo，先鎖定 redemption / queue / distribution 相關檔案）。
   • 每輪只要求 top 2，並嚴格貼輸出格式。

2. 交叉驗證階段
   • 把有潛力的 finding 丟到 Grok（這裡或 grok.com）用不同 prompt lens 再跑一次。
   • 或在 Cursor 裡切不同模型再驗證。
   • 這步最能展現「多 LLM」的價值。

3. 深挖 + 報告階段
   • 只對活下來的少數 issue 用 Opus（或 Grok 強 reasoning 模式）做最終打磨 + code verification + impact 量化。
   • Opus 很貴（額度消耗快），要省著用。

4. 額度節省小技巧（很重要）
   • 先用小範圍合約測試 prompt 效果。
   • 善用 focused context：不要每次都貼全部 code，只貼相關函數 + 呼叫圖 + scope 重點。
   • 善用 Cursor 的 Auto / slow 模式做初步過濾。
   • 把常用 prompt 存成 Cursor rules 或 snippets，減少重複貼。
   • 監控 usage dashboard，發現快用完時就把剩餘工作切到 Grok chat 或外部便宜模型。


   根據目前 Cursor 的實際情況，這些模型對 credit pool 消耗很低或幾乎不消耗（尤其是 Auto 模式）：

┌────────┬───────────────────────────────────────┬───────────────┬─────────────────────────────────────────┬────────────────────────────────────────┐
│ 優先級 │ 模型建議                              │ 消耗等級      │ 推薦用途（對你 audit 來說）             │ 備註                                   │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★★★★  │ Auto（最推薦）                        │ 極低 /        │ 跑 prompt、初步分析、整理 finding、寫   │ Cursor 自己路由到便宜模型，            │
│        │                                       │ 接近無限      │ issues.txt                              │ 強烈建議預設用這個                     │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★★★   │ Gemini Flash 系列（2.5 Flash 等）     │ 很低          │ 跑 logic-griefing prompt、code          │ 速度快、context 好、便宜               │
│        │                                       │               │ exploration                             │                                        │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★★★   │ GPT-5 Mini / GPT nano 類              │ 很低          │ 簡單驗證、格式整理、第一輪掃描          │ 穩定                                   │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★★    │ Grok Code Fast（如果有）              │ 低            │ 另一個獨立視角                          │ 如果 Cursor 內建就用                   │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★★    │ DeepSeek Coder / V3 Flash 類（Cursor  │ 低            │ 跑 prompt                               │ 開源模型裡 coding 能力不錯             │
│        │ 內建版本）                            │               │                                         │                                        │
├────────┼───────────────────────────────────────┼───────────────┼─────────────────────────────────────────┼────────────────────────────────────────┤
│ ★★     │ Composer 1.5 / Cursor 自己的 base     │ 低            │ 日常操作、簡單任務                      │ 避免手動切到 premium                   │
│        │ 模型                                  │               │                                         │                                        │
└────────┴───────────────────────────────────────┴───────────────┴─────────────────────────────────────────┴────────────────────────────────────────┘
// 已建議模型名稱清單：
// - Auto（最推薦）
// - Gemini Flash 系列（如 2.5 Flash）
// - GPT-5 Mini / GPT nano 類
// - Grok Code Fast
// - DeepSeek Coder / V3 Flash（Cursor 內建版）
// - Composer 1.5 / Cursor base 模型
嚴禁：手動選擇 Claude Sonnet、Opus、任何標示 High / Max / frontier 的模型。