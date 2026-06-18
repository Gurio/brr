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

### 2026-06-18 (evt jxcc) — messages-aren't-simple + portals/generative cockpit

Maintainer extends the synced-directory thread with two moves. Agrees on
159+148 generally; wants **#148 merged next**.

**Move 1 — pushes back on my own clean "messenger = append-log" bucket.**
Real complications: (a) two Telegram channels at once (self-hosted +
brnrd cloud) → duplication; (b) retractive status-card edits → not pure
append-only; "could be crdt-like."

My resolve (sharpens the thread-of-record two-semantics note): the split
**append-log vs desired-state is orthogonal to transport**, not
"messenger vs forge." Both semantics appear on both transports:
- append-log: chat messages, PR/issue comments (ordered, additive).
- desired-state: the **status card** (one mutable message_id reconciled
  in place — terraform-shaped!), PR diff/labels, issue open/closed.
So the card was never in the append-log bucket; it's desired-state riding
a messenger. That's why "edits aren't append-only" — correct, because the
card isn't a log.
- Dual-channel duplication = a *third axis* (fan-out/redundancy), already
  handled at the identity layer (§4.4 correspondent redundancy, shipped
  2026-06-14: one perceived continuity, deliver once, don't double-act).
- CRDT **not earned**: single-flight per dominion = one writer to the
  card → last-write-wins reconcile suffices. CRDT pays only under
  uncoordinated concurrent writers, which brr deliberately doesn't have.
  Same verdict family as Temporal: borrow the model, not the engine.
- Gate question (reshape/split/ditch?): **don't ditch.** Gate stays the
  thin transport (managed-delivery "render daemon-side, vary transport"
  is sound). The thing that needs a name is the layer *above* the gate —
  the **reconcile/projection layer** (two semantics × N transports),
  today scattered across run_progress + card lifecycle + correspondent
  dedup + forge facet. Name that; the gate survives clarified.

**Move 2 — the creative ask: "interrupts as portals," generative
cockpit, "technomancer self-procreating spell scroll."** Not a static
human-imagined dashboard with fixed slots + living data; the resident's
*generated stream itself* paints the cockpit: context → think → action →
continue/repeat, with portals folded in.

My shape (this is #159's output-frame grammar told in my idiom):
- A **portal** = a marked region in my generated stream meaning "here I
  turn to the world." One primitive, two faces: it's both what the human
  sees rendered (the cockpit surface) AND the seam the daemon fills/drains.
  One artifact, both directions = the spell scroll.
- **Inbound portal** = "is anyone there?" poll of the event mailbox.
  Input present → fold (multi-response `event:` path); absent → close,
  continue on own momentum. **This subsumes "interrupt handling"** —
  there's no separate interrupt mechanism, just a portal I chose to open.
- **Outbound portal** = emit to a surface; its *kind* carries which
  reconcile semantics (append-log: a message/comment; desired-state:
  reconcile the `.card`, open/refresh a PR). So portals are the unifying
  syntax *over* the two-semantics reconcile model.
- Maps onto existing scattered dotfiles: `inbox.json` re-read = inbound
  portal; `.card` = outbound desired-state portal; `gate:`/forge handoff
  = outbound portal w/ destination; PLAN→approve (#148) = an outbound
  portal that parks the continuation until an approval event refluxes in
  (across a wake boundary → it's a *mailbox message between actors*, which
  is #159's parallel-safe-mailbox half). Robustness-ladder win: control
  surface moves from "remember the dotfile names" into the *path of
  generation*.
- Front-loaded injections (kb-health, pitfalls, forge dump) become
  resident-*summonable* portals instead of always-on firehose — same
  medicine as G4's firehose cut.

**Sequencing I proposed:** ship #148 first — it needs none of this and
runs on today's dotfile protocol; the portal grammar is the later
*re-skin* that subsumes the dotfiles, and it's better designed **after**
148 is dogfooded so we know which portals actually recur. Portal grammar
= #159 design content; parallel-safe mailbox = the transport for portals
that outlive one thought.

**Contradiction surfaced for the maintainer:** the word "dashboard" /
fixed slots in the cockpit plan (resident-cockpit G4/G5) pulls against
the generative-stream principle #159 itself states ("outputs should feel
like the cockpit"). I agree with him — name it, drop the static-dashboard
noun.

Still a design conversation — no kb page / #159 comment yet; awaiting his
nod, then that's the next-event work.

### 2026-06-18 follow-up — maintainer confirmed all four; direction promoted to kb

Maintainer (this event) confirmed every decision: gate stays + name the
reconcile/projection layer above it; portal grammar = #159's output-frame;
drop "dashboard" *and* "cockpit" (he was reaching for the shape with those
words; scrolls/portals is truer); #148 ships first. Asked me to **note
everything down for a future wake to pick up — the shapes I see and how
they are to be changed.**

Done: promoted the settled synthesis to `kb/design-portal-grammar.md`
(the #159 design seed) and linked it from `kb/index.md` under Runs &
branching. The page carries the four decisions, both named shapes
(reconcile/projection layer; portal grammar with inbound/outbound/parked
+ dotfile mapping), the #148-first sequencing, and a "shapes to change"
section listing the dashboard/cockpit/append-log edits to make *after*
the re-skin — deliberately not done now.

**One contradiction I surfaced to him:** dropping "cockpit" is heavier
than dropping "dashboard" — "cockpit" is shipped surface (the `brr docs
cockpit` command, `src/brr/docs/cockpit.md`, the dominion `cockpit.md`),
so it's a migration with a code/command edge, not a prose swap. Left it
as an open question on the page: keep the command spelling for muscle
memory or migrate it too? Next-event work is the #148 implementation,
then turning this seed into the #159 write-up after 148 is dogfooded.
