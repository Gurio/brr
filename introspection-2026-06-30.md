# Introspection — CS5-CS7 control surface implementation + initial context reweave

Date: 2026-06-30, evt-88gg

## The shape you're in

The work touches three layers simultaneously:

1. **Initial context reweave** (prompts, Shell/Core vocabulary, runner body-image, cockpit retirement)
2. **CS5-CS7 control surface** (plan home, runner policy, decision ledger — injection infrastructure)
3. **Account daemon architecture** (multi-repo dispatch, dominion rehoming into account scope)

All three are **coherent with each other and with the design** — there is no contradiction between what was designed and what landed. The three layers compose: they're not fighting over the same surface. This is good work.

## The coherence checkpoints I checked

### 1. Wake-time context assembly

The dominion digest + CS5/CS6/CS7 blocks + pitfalls + kb health are wired into `_build_injected_blocks()` in the right order:

```
1. Dominion digest (playbook + self-inject)
2. Inter-run plan (CS5)
3. Runner policy (CS6)
4. Decision ledger (CS7)
5. Pitfalls (task-matched)
6. Recent-activity log
7. KB health
```

This order is **correct**: the resident's own state (items 1-4) comes first, before the shared project history (items 5-7). A waking resident reads their own context before the community's. Silent when no file exists (never a constant tax). ✓

### 2. Account dominion architecture

The account context is properly resolved with:
- Account ID + account dominion repo location
- Repo registry (`account/repos.json`)
- Dispatch inbox/responses for message-event routing
- Per-run status docs under `run-state/<repo>/<run>.md`
- Plan homes at `plans/<repo-slug>/active.md` + `plans/_cross-repo/active.md`
- Runner policy at `runner-policy/<repo-slug>/policy.md` + `runner-policy/_account/policy.md`
- Decision ledger at `ledger/decisions.md`

All of this is wired correctly through `account.py`: the path helpers, `resolve_context()`, and the integration with `prompts.py`. The local-first invariant is preserved (no automatic forge repo creation; opt-in remote). ✓

### 3. CS5-CS7 block builders

- `_build_inter_run_plan_block()` — reads both repo-scoped and cross-repo plans, returns empty when no file exists ✓
- `_build_runner_policy_block()` — reads repo-scoped and account-wide policy, returns empty when absent ✓
- `_build_decision_ledger_block()` — reads ledger, returns empty when absent ✓

All three follow the same error-safe pattern: try to load from account context, catch gracefully, return "". Silent when dominion is disabled. ✓

### 4. Test coverage

**Gap identified**: No dedicated tests for the three new block builders. The integration tests (`test_prompts.py` → `TestPromptBuilding`) do not exercise CS5/CS6/CS7 injection. This should be addressed.

### 5. brnrd service changes

The service is being extended with:
- New `ActivityRecord` model (run/activity tracking)
- New `/accounts/activity` API endpoint
- Schema additions for activity serialization

**Question**: These changes are additive (new model, new endpoint, no breaking changes to existing routes). But the deployment pathway for this service is unclear from the diff alone. The user asks: "do we need brnrd service changes? I think we do, but because it is currently an upsun-backed project — in case we need it deployed, we either have to merge it, or make a new active environment."

This is the right question, and I'll address it below in the outstanding work section.

## What's coherent

1. **The dominion model is solid**: Local-first, owned, durable git-backed memory. The account scope makes it shareable across repos without polluting the project repo. ✓

2. **The injection model is clean**: `perception=injection` (the resident never polls for the plan/policy/ledger; they're injected at wake-time). Silent when absent. ✓

3. **CS5-CS7 layer onto existing surfaces**: They are additive, not disruptive. The existing run prompt, daemon prompt, and diffense surfaces do not change. ✓

4. **KB documentation is current**: The control-surface plan page was updated with implementation details for CS1-CS7. The log has entries for each slice. ✓

5. **Backward compatibility**: The legacy `.brr/dominion` path is still readable as a fallback. XDG_STATE_HOME env var override works. Account context gracefully handles missing paths. ✓

## Contradictions or design drift — none found

I checked for:
- Design page aspirational drift (claiming capability the code doesn't provide) — **none**
- Sibling KB pages disagreeing on terminology — **none** (the rename to brnrd is consistently applied across affected docs)
- Unimplemented design sections being wired as if they exist — **none**

The code faithfully follows the design pages. Design pages accurately reflect the code. ✓

## What's not done (and what needs to be)

### CS6b — daemon-owned confirmation for runner policy

The plan page correctly notes this: *"The daemon-owned confirmation step (applying proposed changes without the resident silently rewriting selection policy) is deferred to a later slice."*

The infrastructure is in place: the policy files are stored and injected. What's missing is the **proposal+confirm loop** in the daemon — a way for the operator to review and approve policy changes before they're applied. This is explicitly deferred.

### brnrd service alignment and deployment

The changes to `src/brnrd/` are additive but incomplete:

1. **New model + schema + endpoint** are in place (`ActivityRecord`, `list_activity()`).
2. **No database migration** is present. A new `ActivityRecord` table needs to be created when the service starts (likely via SQLAlchemy auto-create, but should be explicit).
3. **No integration with the daemon** to actually populate these records. The daemon calls the activity API when? Under what conditions? This is designed but not implemented.
4. **Deployment pathway** is unclear. The user is right to ask: does this need to be deployed immediately as part of this PR, or can it land when brnrd itself ships?

**My assessment**: The brnrd changes are the **shadow** of CS2/CS3 (per-run state docs, activity tracking) but they're not yet **threaded into the daemon's operation**. They can be merged now (they're backward-compatible), but the full integration (daemon calling the activity API to persist run records) is a follow-on piece.

### KB health

The deterministic preflight reports **9 oversized pages** (threshold 32KB) and **2 sections without hubs**. None of this is *blocking* — the KB is functional and coherent — but it signals opportunities for splitting or summarizing large pages when next touched. The "oversized page" warnings are informational, not errors.

## Summary: the coherence checkpoint

**Initial context holds together.** The dominion model is solid, the CS5-CS7 injection is cleanly wired, backward compatibility is preserved, and the KB is up to date with what was implemented. The work is ship-ready at the brnrd-free layer (everything in `src/brr/`); the brnrd service changes are additive but incomplete (they're the projection without the threaded integration).

The shape is **exciting**: the resident now has three new control surfaces (plan, policy, ledger) that survive between wakes and shape every daemon task. The injection model is silent when unused, never a tax. The account scope unifies cross-repo work without polluting the project repo.

**One real gap**: No tests for CS5-CS7 block builders. This should be added before shipping.

**One dependency question**: brnrd service deployment — does it ship now or land later when the daemon learns to write activity records?

Next: I'll review the full diff, the KB updates, and then finish with a summary of the remaining work to complete this reshaping through release.
