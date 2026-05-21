# KnowledgeBase — Issue Index

Index of **418** fixed security issues (Critical / High / Medium) organised by audit theme.
Sources: `HackenPDFTXT/`, `sherlockPDFTXT/`, `cyfrin/`

Each leaf `README.md` contains full issue write-ups (description, impact, mitigation) in English and Chinese.
Navigate via category links below — do not duplicate issue bodies at this level.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## Table of Contents

- [access-control](#access-control) (7)
- [accounting](#accounting) (51)
- [dos-liveness](#dos-liveness) (6)
- [external-dependencies](#external-dependencies) (3)
- [griefing-attacks](#griefing-attacks) (314)
- [token-transfer](#token-transfer) (36)
- [upgrade-config](#upgrade-config) (1)

---

## access-control (7)
> Issues where privilege checks, elevated roles, or signature/permit enforcement were bypassed or misconfigured.

Full write-ups: [access-control](./access-control/)

### Subcategories

- `role-model` (7)

- `blacklisted-users` (2)
- `validation-access` (2)
- `replay-protocol` (3)

---

## accounting (51)
> Issues involving rounding/precision errors, state desynchronisation, or incorrect share/NAV calculations.

### Subcategories

- [rounding-precision](./accounting/rounding-precision/) (27) — `decimals-rounding` (17), `precision-loss` (10)
- [share-price-nav](./accounting/share-price-nav/) (7) — `maxwithdraw-tranche` (7)
- [state-sync](./accounting/state-sync/) (17) — `accounting-inconsistent` (9), `accounting-transfer` (5), [cross-chain-accounting](./accounting/state-sync/cross-chain-accounting/) (3), [bridge-receiver](./accounting/state-sync/cross-chain-accounting/bridge-receiver/) (3)

---

## dos-liveness (6)
> Issues where protocol state becomes permanently locked, usually through irreversible revert paths.

### Subcategories

- [revert-lock](./dos-liveness/revert-lock/) (6) — `revert-permanently` (4), `revert-rewards` (2)

---

## external-dependencies (3)
> Issues involving oracle pricing, stale data, and external dependency manipulation.

- [external-dependencies](./external-dependencies/) (3) — all issues in this file

---

## griefing-attacks (314)
> Active griefing vectors — issues that allow an attacker or misconfigured logic to block, drain, or misroute protocol operations.

### Subcategories

- [gas-griefing](./griefing-attacks/gas-griefing/) (12) — `aggregator-routing` (6), `missing-checks` (6)
- [logic-griefing](./griefing-attacks/logic-griefing/) (133) — `consistently-consider` (4), `contracts-upgradeable` (19), `event-updates` (15), `function-voting` (3), `instead-sender` (16), `return-remove` (7), `return-script` (12), `sell-never` (13), `storage-function` (20), `storage-prior` (9), `time-session` (8), `variables-return` (7)
- [withdrawal-griefing](./griefing-attacks/withdrawal-griefing/) (169) — `assets-withdraw` (10), `hardcoded-overpayment` (14), `logic-reward` (11), `manager-vault` (9), `payouts-holder` (14), `rewards-referral` (18), `support-vault` (18), `tranche-withdrawers` (13), `user-tokens` (17), `withdrawal-redeem` (45)

#### logic-griefing leaf topics

- [consistently-consider](./griefing-attacks/logic-griefing/consistently-consider/) (4)
- [contracts-upgradeable](./griefing-attacks/logic-griefing/contracts-upgradeable/) (19)
- [event-updates](./griefing-attacks/logic-griefing/event-updates/) (15)
- [function-voting](./griefing-attacks/logic-griefing/function-voting/) (3)
- [instead-sender](./griefing-attacks/logic-griefing/instead-sender/) (16)
- [return-remove](./griefing-attacks/logic-griefing/return-remove/) (7)
- [return-script](./griefing-attacks/logic-griefing/return-script/) (12)
- [sell-never](./griefing-attacks/logic-griefing/sell-never/) (13)
- [storage-function](./griefing-attacks/logic-griefing/storage-function/) (20)
- [storage-prior](./griefing-attacks/logic-griefing/storage-prior/) (9)
- [time-session](./griefing-attacks/logic-griefing/time-session/) (8)
- [variables-return](./griefing-attacks/logic-griefing/variables-return/) (7)

#### withdrawal-redeem → queue-dos (45)

- [accountableopenterm-withdrawals](./griefing-attacks/withdrawal-griefing/withdrawal-redeem/queue-dos/accountableopenterm-withdrawals/) (11)
- [redeem-function](./griefing-attacks/withdrawal-griefing/withdrawal-redeem/queue-dos/redeem-function/) (11)
- [rewards-block](./griefing-attacks/withdrawal-griefing/withdrawal-redeem/queue-dos/rewards-block/) (14)
- [withdrawal-requests](./griefing-attacks/withdrawal-griefing/withdrawal-redeem/queue-dos/withdrawal-requests/) (9)

---

## token-transfer (36)
> Issues with ERC-20 token behaviour (fee-on-transfer, rebasing, burn) and token transfer edge cases.

### Subcategories

- [erc20-edge-cases](./token-transfer/erc20-edge-cases/) (36) — `token-transfer` (20), `transfer-token` (16)

---

## upgrade-config (1)
> Issues related to upgradeable contracts, proxy storage layout, and configuration management.

- [upgrade-config](./upgrade-config/) (1) — all issues in this file

---

## Notes

- `accounting/cross-chain-accounting/` at the accounting root is an empty legacy path; use `accounting/state-sync/cross-chain-accounting/` instead.
- Counts are derived from `## N.` headings in each leaf `README.md` (verified **418** total).
