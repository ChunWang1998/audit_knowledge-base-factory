# auth/operational-security - Issues

- Count: 2

## F-2026-15280 - Hardcoded Private Key Exposure in Test ScriptsEnables Unauthorized Account Control
- 嚴重度：Medium
- Report source：Fabstir.pdf

### 問題內容（完整）
Private keys were embedded in repository test scripts, which constitutescredential exposure and enables full signing authority over thecorresponding externally owned accounts. Since both derived addresseswere observed with on-chain activity in October 2025, the exposurecannot be treated as purely synthetic test data and must be considered anoperational security incident until key rotation and usage invalidation areconfirmed. The integration/example JavaScript tests instantiate wallets from literalprivate-key constants, creating recoverable signing credentials in sourcecontrol history. Representative pattern (redacted): // Wallets const userWallet = new ethers.Wallet('<`REDACTED_PRIVATE_KEY`>', provider); const hostWallet = new ethers.Wallet('<`REDACTED_PRIVATE_KEY`>', provider); Affected locations include: tests/integration/usdc-payment-flow.jstests/integration/usdc-complete-cycle.jstests/examples/usdc-job-parsing-example.js Derived addresses: 0x8D64…..4bF6 0x4594…..4504 Risk mechanism: Any actor with repository access can derive the same accounts andproduce valid signatures.If the same credentials were reused in deployment pipelines,operational wallets, relayers, or privileged off-chain services,unauthorized transactions and state changes could be executed.Exposure persists in Git history even after file-level replacement,unless history rewrite and coordinated secret revocation areperformed. If key reuse occurred in any operational context, unauthorized actors couldexecute transactions, impersonate trusted signers, and transfer controlledassets; even where current deployment usage is dismissed and keys arerotated, historical leakage preserves residual risk until complete revocationvalidation and dependency rotation are finalized. 59 Found in commit: f614355. Status: Fixed

### 修補方式（建議）
Immediate revocation/retirement of all exposed keypairs should beenforced.Verification should be completed that no deployment, relayer,automation job, CI secret, or production environment references theexposed addresses.Fresh keys should be generated through secure entropy sources andisolated per environment (dev/test/staging/prod) with strict non-reusepolicy.Secret material should be loaded from secure secret managers orenvironment injection, never from literals in source code.Repository and CI secret-scanning controls should be enabled (pre-commit and pipeline) to block future commits containing private-keypatterns. Resolution: Hardcoded private keys have been replaced with environment variablereferences across all affected test scripts; however, the original keyspersist in Git history and the associated accounts should be consideredpermanently compromised — key rotation and fund migration are stillrequired. Revised commit: df1f2e4. 60

### 修補方式（實際）
Hardcoded private keys have been replaced with environment variablereferences across all affected test scripts; however, the original keyspersist in Git history and the associated accounts should be consideredpermanently compromised — key rotation and fund migration are stillrequired. Revised commit: df1f2e4. 60

## F-2025-14485 - Lack of Limits and Delay in Forced WithdrawalParameter Updates - Medium
- 嚴重度：Medium
- Report source：BullBit.pdf

### 問題內容（摘要）
The InclusionQueue contract enables the creation of forced withdrawalrequests originating from the Vault and Pool contracts. These requests arelater consumed by the verifier contract to finalize withdrawals. Duringrequest creation, a fee equal to the feeAmount variable must be paid. Thisfee is not deducted from the internally deposited balance, requiring theavailability of additional externally held assets. The setAmount() function is responsible for updating both minWithdrawAmount and feeAmount. This function is protected by the onlyOwner modifier.However, several design shortcomings introduce risk and negatively affectthe withdrawal process. function setAmount(uint256 _minWithdrawAmount, uint256 _feeAmount) external o nlyOwner { require(_minWithdrawAmount > 0, "Queue: 0 min amount"); minWithdrawAmount = _minWithdrawAmount; feeAmount = _feeAmount; } First, no reasonable upper bounds are enforced for either parameter. As aresult, minWithdrawAmount can be set to excessively high values, potentiallypreventing withdrawals of smaller deposits or blocking withdrawalsentirely. Similarly, feeAmount can be set to arbitrarily large values, requiringdisproportionately high external assets to

### 修補方式（實際）
The BullBit team implemented upper bounds for feeAmount and minWithdrawAmount and a time-lock mechanism is integrated to reflectchanges in commit 322258e. 32

