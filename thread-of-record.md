# Thread of record

Durable cross-channel project narrative I curate. brr points here; it
doesn't write it.

## 2026-06-17 — Forge/ticketing split + lean-the-mechanism (telegram, open)

Maintainer asked (evt yzdp) to fold a "tooling update" (extend the forge
gate protocol to handle review) into the forge-grooming topic (#117) and
implement it — but in the same breath said he doesn't know the right
split anymore, suspects the "input reactor gate = messenger + issue
tracker + forge" abstraction is mis-scoped, and is leaning toward a lean
agent interface (outgoing event with optional pack section; daemon does
render/upload/PR-CRUD in the background).

My reply (design conversation, no code — settling the split is the
prerequisite to implementing against it):

**Two axes the request conflates** —
- *Mechanism* (who moves the bytes: project pack, probe brnrd, write
  gist, open PR).
- *Agency* (who decides: what to publish, where, how it reads, the pack
  content).
The 2026-06-10 move (PR publication daemon→agent, via `brr review
--relay` + `gate: forge`) conflated them. Proposed reconcile: **lean the
mechanism back to the daemon, keep the agency with the agent.** Agent
emits one declarative outgoing event with an optional `pack` section +
`forge_action`; daemon's delivery loop (already opens/refreshes PRs)
absorbs projection+relay+gist-probe+PR-open. Dissolves the maintainer's
stated trade-off: introspection lives in the *pack content*, not the
upload plumbing.

**Gate abstraction mis-scope** — gates bundle three roles: ingress,
egress, and forge-as-workspace (PR/issue artifacts with lifecycle
state). Messenger gates are pure transport; the forge is a comment
channel (messenger-shaped) glued to an artifact/ticket store
(not messenger-shaped). Proposed: gates shrink to transport adapters for
event ingress/egress; forge-item ops (open/refresh/rebase/state-read,
grooming) become a daemon-owned **forge-capability** layer the agent
drives by declaring intent — not a gate. #128 (run/event model) already
half-articulates this (events vs. forge-item interaction).

Open questions left for the maintainer (see reply). Awaiting his nod on
direction before any implementation slice.

### 2026-06-17 follow-up (evt gkcx) — maintainer agreed + 3 refinements

Maintainer: "great push, agree on all accounts." Three additions, one
light pushback:

1. **Delivery failure** — agent can't know if delivery failed (GH down,
   rare-but-happened); shouldn't care about plumbing by default, but
   could try notifying via another gate. My reconcile: **delivery
   reliability (retry + cross-gate fallback) is a daemon concern**, and a
   failure should *reflux as an ingress event* into the next wake — agent
   doesn't hand-roll fallback, but is *told* when plumbing failed so it
   can react if it matters. Default-don't-care + told-on-failure.

2. **"The PR *is* a conversation, just with a big bundled diff as
   context"** — conceded; my earlier "a PR isn't a conversation, it's an
   object with state" was too binary. A PR wears **two hats**:
   conversation facet (comment thread — append-only log, messenger-shaped)
   + artifact facet (diff/branch/lifecycle/CI — desired-state). That
   duality is *exactly why* the gate felt mis-scoped: one object spans
   egress-channel + workspace-artifact. Concession strengthens the split.

3. **Average-user UX pushback (the important one)** — comaintainer/duo
   framing is real but "not the main thing"; many first users just want
   brr as a remote-TG codex/GitHub wrapper. Risk of over-complicating
   average UX. Proposed reframe: PR (and maybe all gates) as a
   **remotely↔locally synced directory** — an "ideation terraform thing."
   Notes Linear is far harder than a GH issue to represent as folder-file
   sync.

**My convergence (this turn):** the terraform/synced-directory idea is
the *implementation shape* of the daemon-owned forge-workspace layer I
proposed — agent declares desired state by editing files; daemon
reconciles to the forge (idempotent apply). Reconciles everything:
- *Average UX stays thin* — the directory abstraction is invisible to the
  texter; it's the agent's/maintainer's substrate. **Abstraction depth
  lives in the daemon; the user-facing surface stays a thin messenger
  wrapper.** No conflict between "texter's mental model = TG+GH wrapper"
  and "agent's mental model = I work in a synced directory."
- *Two file semantics in one tree* (the refinement to "all gates as
  folder-sync"): **desired-state files** (reconciled, terraform-shaped —
  PRs/issues/artifacts) vs **append-log files** (mirrored read, agent
  appends to send — conversations/comments/messenger). Conflating them is
  the trap; a comment thread is not convergent desired state.
- *Linear isn't a counterexample — it's the provider-layer argument.* The
  directory holds a *projection*; the provider adapter owns the lossy
  translation (terraform's provider model exactly). GH issue → clean;
  Linear → adapter maps rich schema as projection. Confirms
  ticketing/code-hosting provider split.
- *Bidirectional* — incoming forge state (comments, CI, conflicts, review)
  lands as files the agent reads next wake; this is the grooming (#117)
  substrate, where the shipped network-free forge-state facet graduates
  to live status.
- *Idempotency fixes a bug we just hit* — 2026-06-17 the PR gate opened
  the PR but the first poll missed it, so I tried direct creation and GH
  reported already-open. That's a non-idempotent reconcile; the terraform
  model makes it a no-op.

**Sequencing caution:** the synced directory is the *north star*; the
lean declarative outgoing-event (body + target + optional pack +
forge_action) is the *MVP first step toward it* (an outgoing intent =
one write into the desired-state tree). Not rivals — don't over-build the
directory day one. Still no code until maintainer nods on direction.
