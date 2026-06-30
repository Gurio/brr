# CS5-7 shipped — 2026-06-30

CS5-7 landed in this wake on `brr/cs5-cs7-plan-policy-ledger` (07d13f2).

Three new injection blocks in `_build_injected_blocks()`:
- **Active inter-run plan** (`plans/<repo-slug>/active.md`) — the plan I leave myself
- **Stored runner policy** (`runner-policy/<repo-slug>/policy.md`) — standing runner prefs
- **Decision ledger** (`ledger/decisions.md`) — user-facing through-line

All silent when absent; perception=injection. 22 new tests, 1207 total passing.

CS6b (daemon-owned confirmation step for policy proposals) deferred — it needs a
proposal+confirm loop in the daemon that isn't there yet. For now the operator
writes policy directly; I propose changes in prose.

The `plans/` and `plans/_cross-repo/` paths are now available in my account dominion.
I should start using `plans/Gurio__brr/active.md` for inter-run plans.
