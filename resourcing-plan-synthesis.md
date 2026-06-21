# The resourcing-plan reframe (#139 ↔ #148 ↔ #170), 2026-06-21

Context: maintainer split a message across two telegram events (9y75 +
qgwa). Half one rejected PR #170 (the "default to a reviewable PR" bundle
prose nudge) as wrong-layer. Half two named the real shape.

## The unifying thesis (what I proposed)

The decisions a wake makes — open a PR / which environment / which runner /
what to hand off / whether to spend budget — are **not** separate prose
nudges. They are facets of **one** object: the runner's **resourcing plan
for the wake**, bounded by a **user-set envelope**, surfaced (not gated)
via the plan portal. PR #170's mistake was treating one facet (PR-landing)
with static bundle prose instead of folding it into that plan.

## Resolving the maintainer's central tension

Wants: control, BUT no blocking-on-confirmation UX, no daemon toggles/
branching, work *felt done*, and never a wake whose credits burn in vain.

Resolution — **approval is not a per-action synchronous gate**. Control =
1. **Envelope** (set once, ambient policy): allowed environments, allowed
   runner types, budget ceilings incl. a brnrd-burn cap. The "control"
   lives here, ahead of time, declaratively. Reliability comes from the
   *daemon enforcing the envelope as a hard floor* — not from prose the
   agent must remember, and not from a popup.
2. **Plan-as-receipt** (per wake, visible, interruptible): the runner's
   first act on non-trivial work emits its plan — chosen env, runner(s),
   handoffs, est. budget draw, blockers — to the card / plan portal.
   Non-blocking; the user corrects early by *interrupting*, not approving.

So the maintainer's own instinct ("the approvals point was vague and
tangential") is right: the reliable primitive isn't *approval*, it's
**envelope + accountability + interrupt**.

## "Leave the daemon out of this"

= the daemon is a **policy-enforcing resource broker**: it enforces the
envelope (refuses over-cap spend) and surfaces the *menu* (which envs/
runners exist, their costs, the user's caps) as injected state. It does
**not** decide or branch on toggles. The intelligence — env/runner/landing
choice — lives in the runner's plan. That is exactly the "host environment
is for local action" alignment.

## The no-wasted-wake contract

Every wake returns either (a) work within the envelope, or (b) a
**curation**: why it can't proceed in this shape, what the user must
redefine/allow to unblock, and the *minimal* slice that might satisfy the
want (done if within envelope). Credit is never spent in vain because the
output is always work OR an actionable unblock-spec.

## Minimal next increment (what I'd build; did NOT build)

Foundation both control & visibility rest on:
- declare the **envelope** as config/state (allowed envs, runner types,
  budget caps incl. brnrd burn) — daemon-enforced;
- extend the **plan portal** (#148 PLAN shape) + #139 Phase-1 medium line
  to emit *chosen env / runner / est. cost*.
Everything else (handoff to child runs, finalize-time landing check)
layers on. Do NOT build the whole branching machine in the daemon.

## Receipts this wake
- Closed PR #170 with a superseding comment.
- This note. Offered to fold the thesis into plan-resident-cockpit.md
  (G1/G2 unification) + a #139 comment once the maintainer picks a
  direction. Held off on heavier kb scaffolding because it's a fork the
  maintainer hasn't chosen yet.
