# KnowledgeBase — Issue Index

Index of **418** fixed security issues (Critical / High / Medium) organised by audit theme.
Sources: `HackenPDFTXT/`, `sherlockPDFTXT/`, `cyfrin/`

Each leaf `README.md` contains full issue write-ups (description, impact, mitigation) in English and Chinese.
Navigate via category links below — do not duplicate issue bodies at this level.

Severity legend: 🔴 Critical  🟠 High  🟡 Medium

---

## Table of Contents

- [access-control](#access-control) (50)
- [accounting](#accounting) (108)
- [dos-liveness](#dos-liveness) (51)
- [external-dependencies](#external-dependencies) (3)
- [griefing-attacks](#griefing-attacks) (121)
- [token-transfer](#token-transfer) (36)
- [upgrade-config](#upgrade-config) (49)

---

## access-control (50)
> Issues where privilege checks, elevated roles, signature/permit enforcement, or `msg.sender` validation were bypassed or misconfigured.

Full write-ups: [access-control](./access-control/)

### Subcategories

- [instead-sender](./access-control/instead-sender/) (16)
- [manager-vault](./access-control/manager-vault/) (9)
- [support-vault](./access-control/support-vault/) (18)
- `role-model` (7) — `blacklisted-users` (2), `validation-access` (2), `replay-protocol` (3)

---

## accounting (108)
> Issues involving rounding/precision errors, state desynchronisation, incorrect share/NAV calculations, or payout/reward distribution miscalculations.

### Subcategories

- [rounding-precision](./accounting/rounding-precision/) (27) — `decimals-rounding` (17), `precision-loss` (10)
- [share-price-nav](./accounting/share-price-nav/) (7) — `maxwithdraw-tranche` (7)
- [state-sync](./accounting/state-sync/) (27) — `accounting-inconsistent` (9), `accounting-transfer` (5), [cross-chain-accounting](./accounting/state-sync/cross-chain-accounting/) (3), [bridge-receiver](./accounting/state-sync/cross-chain-accounting/bridge-receiver/) (3)
- [payout-errors](./accounting/payout-errors/) (57) — `hardcoded-overpayment` (14), `logic-reward` (11), `rewards-referral` (18), `payouts-holder` (14)

---

## dos-liveness (51)
> Issues where protocol liveness is blocked — permanent reverts, irrecoverable locks, or queue-based denial-of-service on withdrawals/redemptions.

Full write-ups: [dos-liveness](./dos-liveness/)

### Subcategories

- [revert-permanently](./dos-liveness/revert-permanently/) (4)
- [revert-rewards](./dos-liveness/revert-rewards/) (2)
- [queue-dos](./dos-liveness/queue-dos/) (45) — `accountableopenterm-withdrawals` (11), `redeem-function` (11), `rewards-block` (14), `withdrawal-requests` (9)

---

## external-dependencies (3)
> Issues involving oracle pricing, stale data, and external dependency manipulation.

- [external-dependencies](./external-dependencies/) (3) — all issues in this file

---

## griefing-attacks (121)
> Active griefing vectors — issues that allow an attacker or misconfigured logic to block, drain, or misroute protocol operations.

### Subcategories

- [withdrawal-griefing](./griefing-attacks/withdrawal-griefing/) (40) — `assets-withdraw` (10), `tranche-withdrawers` (13), `user-tokens` (17)
- [logic-griefing](./griefing-attacks/logic-griefing/) (69) — `consistently-consider` (4), `event-updates` (15), `function-voting` (3), `return-remove` (7), `return-script` (12), `sell-never` (13), `time-session` (8), `variables-return` (7)
- [gas-griefing](./griefing-attacks/gas-griefing/) (12) — `aggregator-routing` (6), `missing-checks` (6)

#### logic-griefing leaf topics

- [consistently-consider](./griefing-attacks/logic-griefing/consistently-consider/) (4)
- [event-updates](./griefing-attacks/logic-griefing/event-updates/) (15)
- [function-voting](./griefing-attacks/logic-griefing/function-voting/) (3)
- [return-remove](./griefing-attacks/logic-griefing/return-remove/) (7)
- [return-script](./griefing-attacks/logic-griefing/return-script/) (12)
- [sell-never](./griefing-attacks/logic-griefing/sell-never/) (13)
- [time-session](./griefing-attacks/logic-griefing/time-session/) (8)
- [variables-return](./griefing-attacks/logic-griefing/variables-return/) (7)

---

## token-transfer (36)
> Issues with ERC-20 token behaviour (fee-on-transfer, rebasing, burn) and token transfer edge cases.

### Subcategories

- [erc20-edge-cases](./token-transfer/erc20-edge-cases/) (36) — `token-transfer` (20), `transfer-token` (16)

---

## upgrade-config (49)
> Issues related to upgradeable contracts, proxy storage layout, slot collisions, and configuration management.

Full write-ups: [upgrade-config](./upgrade-config/)

### Subcategories

- [contracts-upgradeable](./upgrade-config/contracts-upgradeable/) (19)
- [storage-function](./upgrade-config/storage-function/) (20)
- [storage-prior](./upgrade-config/storage-prior/) (9)
- root README (1) — missing ownership validation on migration

---

## Notes

- `accounting/cross-chain-accounting/` at the accounting root is an empty legacy path; use `accounting/state-sync/cross-chain-accounting/` instead.
- Counts are derived from `## N.` headings in each leaf `README.md` (verified **418** total).
