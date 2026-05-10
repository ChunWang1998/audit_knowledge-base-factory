# Security Audit — Top 3 Findings (BitGo ETH Multisig v4)

**Scope**: `contracts/WalletSimple.sol`, `contracts/ForwarderV4.sol`, `contracts/Forwarder.sol`, `contracts/Batcher.sol`  
**In-scope alignment**: signature validation, fund management, EVM opcode exploit vectors, multisig approval bypass

---

## Issue 1 — High (should be in knowledgeBase/token-transfer/erc20-edge-cases/)

**File Location:**  
`contracts/ForwarderV4.sol` — `flushERC721Token()`  
`contracts/Forwarder.sol` — `flushERC721Token()`

**Issue Description:**  
`flushERC721Token()` uses:
- `ownerOf(tokenId)` to get token owner  
- `transferFrom(ownerAddress, parentAddress, tokenId)` from the forwarder contract

This allows transfer of tokens not owned by the forwarder, as long as the forwarder is approved as operator by the current owner. The function should only move NFTs actually held by the forwarder itself.

**Attack Scenario:**  
1. A user has previously approved the forwarder as ERC721 operator (`setApprovalForAll`).  
2. A single authorized caller (through wallet-forwarder flow) invokes NFT flush for that token ID.  
3. Forwarder calls `transferFrom(user, parentAddress, tokenId)` and succeeds due to operator approval.  
4. NFT is moved without requiring intended multisig-level authorization for third-party asset movement.

---

## Issue 2 — Medium

**File Location:**  
`contracts/WalletSimple.sol` — `batchTransfer()`

**Issue Description:**  
Batch payouts in `WalletSimple` use unrestricted gas forwarding per recipient call and revert on any single failure. This enables a malicious recipient contract to force full batch failure (gas grief or explicit revert), blocking all other recipients in the signed batch. In contrast, `Batcher.sol` includes explicit transfer gas control.

**Attack Scenario:**  
1. A signed batch contains many valid recipients plus one malicious recipient contract.  
2. Malicious recipient reverts (or consumes all gas) on receive.  
3. `require(success)` fails for that recipient; whole batch transaction reverts.  
4. Valid recipients receive nothing; signers must re-coordinate and re-sign with a new sequence ID, creating repeatable operational DoS pressure.

---

# 中文版（Chinese Version）

**審計範圍**：`contracts/WalletSimple.sol`、`contracts/ForwarderV4.sol`、`contracts/Forwarder.sol`、`contracts/Batcher.sol`  
**符合賞金範圍**：簽名驗證、資金管理、EVM 呼叫風險、多簽授權繞過

---

## 問題 1 — 高風險（High）

**File Location:**  
`contracts/ForwarderV4.sol` — `flushERC721Token()`  
`contracts/Forwarder.sol` — `flushERC721Token()`

**Issue Description:**  
`flushERC721Token()` 透過 `ownerOf(tokenId)` 查得 owner 後，直接由 forwarder 執行 `transferFrom(ownerAddress, parentAddress, tokenId)`。  
這使得 forwarder 只要被 owner 授權為 operator，就能轉移非 forwarder 自身持有的 NFT。正確邏輯應僅允許轉移 forwarder 自己持有的 NFT。

**Attack scenario:**  
1. 某使用者曾對 forwarder 設過 `setApprovalForAll`。  
2. 一位具權限呼叫者（透過 wallet-forwarder 流程）觸發該 tokenId 的 flush。  
3. forwarder 因 operator 權限成功執行 `transferFrom(user, parentAddress, tokenId)`。  
4. 該 NFT 在未滿足預期多簽授權意圖下被轉走。

---

## 問題 2 — medium

**File Location:**  
`contracts/WalletSimple.sol` — `batchTransfer()`

**Issue Description:**  
`WalletSimple` 的批次轉帳對每個 recipient 使用無上限 gas 外呼，且任一 recipient 失敗即整批回滾。惡意 recipient 合約可用 revert 或 gas grief 讓整批付款失敗，阻斷其他正常收款方。對比之下，`Batcher.sol` 有顯式 gas 限制。

**Attack scenario:**  
1. 一筆已簽名批次中包含多個正常地址和一個惡意 recipient 合約。  
2. 惡意合約在接收時 revert（或吃光 gas）。  
3. `require(success)` 失敗導致整筆 batch 回滾。  
4. 所有正常收款方都收不到款，簽名者必須重新協調新 sequenceId 再簽，形成可重複觸發的營運型 DoS 壓力。

