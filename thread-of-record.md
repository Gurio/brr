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
