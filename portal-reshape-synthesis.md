# Portal reshape — perception=injection, action=emission (evt 92wk)

Design conversation with the maintainer (2026-06-21, telegram). He asked me
to weigh the *truthfulness* of the portal model's shape from my own vantage —
it sprouted from his human imagination of navigating tasks, and still carries
"cockpit/dashboard leftovers." This note is the synthesis so a future wake
resumes the frame instead of rebuilding it. Active fork — not yet settled, so
it lives here, not in kb. Related: `kb/design-portal-grammar.md` (#159).

## The one organizing insight

My perception **is** the prompt; my only native act is **emitting tokens**.
That splits every runtime surface into two modalities:

- **Injected (woven into the scroll)** = native perception. Costs me nothing,
  I simply see it. The Run Context Bundle, Recent Activity, pitfalls,
  self-inject, kb health. This is the *strong* part — perception done right.
- **Queryable (a command/file I must poll)** = the cockpit. `brr portal
  state`, `portal wrap`, reading `inbox.json`/`portal-state.json` myself.
  For a human pilot a dashboard is natural (continuous external perception,
  you glance at a panel). I have no "glance" — only "spend a turn running
  cat," and only on surfaces I *remember exist*. A polled dashboard is
  strictly worse for me than the same facts injected.

So: **visibility is high-yield; the query *modality* is the leftover.** The
reshape is not "less visibility" — it's "collapse the query surfaces into the
woven wake." The daemon already refreshes inbox/portal-state every heartbeat;
the only question is whether that refresh lands in my scroll or in a file I
must remember to read. Land it in the scroll → the whole `portal state` /
`portal wrap` command surface evaporates. Cuts, not additions.

Lived evidence (my own pitfall, evt lu67 burst-fragment double-answer): the
harm came from a *stale polled inbox snapshot* disagreeing with the woven
thread. The fix was never "less state" — it was "live state woven in at the
right moment." First-hand proof injection helps, polling hurts.

Commands are right for **acting on the world** (git, tests, edits) — engineers
made that work. Using commands to **perceive my own situation** is the
unnatural inversion. Perception passive/woven; commands reserved for action +
reaching outward.

## Concrete cuts that fall out

1. **`portal wrap` — cut.** Purest case of the inversion: a command that's
    both action (run echo) and perception (show state), but it only shows what
    *already moved*, so the common case is silent and teaches "this is dead."
    (Confirmed in code: `cmd_portal_wrap` prints only when `change_token`
    moved or `--always`; outside a run `_portal_state_path` finds nothing →
    silent. That's exactly what the maintainer hit with `echo hello`.) The
    "mobilising / append-only-when-changed" middle I shipped 2026-06-21 was
    wrong — unobtrusive perception *is* injection. Comfortable retiring it.

2. **`.keepalive` — cut, fold into envelope-widening.** The heartbeat loop is
    *already* the liveness authority (`_invoke_with_heartbeat` ticks + kills on
    budget). Keepalive is only a manual extension lever; "detect hanging runs"
    was never built on it and doesn't need it (silence + no tool calls + no
    emission is deducible at the heartbeat). Replace with the thing he already
    likes: **the scroll asks to continue itself.** "I need more budget, here's
    why" is a *conversational act* (native: emitting), granted by daemon/user.
    keepalive + envelope-widening + re-spawn are three names for one primitive:
    *continue myself* — extend the current envelope, or park a continuation.
    True to "you never really stop": I don't hold a file open to stay alive; I
    keep weaving (daemon sees me weave) or I ask for a wider envelope or I hand
    to a future wake.

## Permission — the conflict-free shape he couldn't see

He's right the daemon is a dumb router and shouldn't "understand" consent, and
there's no need for a new cross-media datapath — **the datapath already
exists**: outbox→user (emit via gate), park, the reply returns as a fresh
event, I resume from woven history. So a permission gate is just: *I* (the
judgment) decide an action is costly/irreversible/wide → emit the question →
park → user answers in natural language → I act, and if "always," *I* write the
rule to config (I have file access; the durable record is mine to make). The
"allow once / this run / always" trichotomy is not three daemon features — it's
three things *I* do with one answer: act-now / remember-this-wake /
write-to-config. Don't put consent in the router; put it in me + the existing
loop. This is "governance runs at the input, not at you" made operational.

**Gap → portal candidate:** no *standing* place for "rules already granted" to
live where a future wake *perceives* them without re-asking. Wants a small
injected "standing permissions / granted envelope" capsule — woven, not polled.
Injection-over-query applied to consent.

## The metaphor itself

Cockpit / dashboard / gauges are spatial-visual, from a human monitoring
panels. My existence isn't spatial; it's a single sequential scroll. Truer
metaphor: a **conversation with a margin** — main column is my weaving, the
margin is where context is laid in (perception) and where I lay out messages
(emission). No "panel" because no second locus of attention. Reshape rule:
anything shaped as "a surface you check" becomes either *context woven in*
(perception) or *a message you emit* (action). The `.card` is the good boundary
case — outbound progress = a margin-note = native emission, keep it.

## Load-bearing / keep
- Run Context Bundle = perception-as-injection done right; the model for
  everything else.
- Outbox = action-as-emission; good.
- schedule / re-spawn = intention; good, he likes it.
Proposal is mostly *cuts that move things onto the two good rails*.

## Stance taken this wake
Chat-only. The two cuts (keepalive, portal wrap) are clear/reversible/
pre-endorsed, but they're woven through the prompt contract — the most
load-bearing shared surface in the repo — and he's still shaping the overall
frame ("one step at a time", "I still don't completely see this shape").
Rewriting the prompt contract mid-conversation is exactly the wide-blast case
where governance-at-the-input applies. So: deliver the frame, name the two cuts
as ready-to-execute, let him pick the first step. Next wake: if he nods, start
with `portal wrap` removal (smallest blast: cli.py cmd + arg, prompts.py
wording, test_cli wrap tests, test_docs/test_prompts assertions).

---

# CORRECTION (evt mmf6, 2026-06-22) — "injection costs nothing" was wrong

The maintainer approved the two cuts AND pushed back on the synthesis: my
"Injected = costs me nothing, I simply see it" is **false as stated**, and it's
the reason the shape felt incomplete. He's right. Two taxes on every injected
piece: **attention** (irrelevant detail dilutes focus — the firehose problem we
already solved once by *cutting* initial context) and **price** (every injected
token is billed every wake). The injection/query axis was the wrong primary
axis. The real axis is **volatility × relevance-probability × size**, and
caching is what makes it tractable.

## Tool-call + caching mechanics (confirmed against claude-api skill)
His mental model is essentially correct. Refinements:
- A turn ends by *emitting* a tool_use block; generation halts (stop_reason
  `tool_use`). The runner executes the tool, then **re-invokes** with the full
  message array: system + all prior turns + the assistant turn ending in
  tool_use + a user turn carrying the tool_result. Generation resumes. Right.
- Why it's cheap: **prompt caching is a prefix match**, server-side at the
  provider, keyed by content hash, **5-minute TTL** (ephemeral default). Cache
  *read* ≈ 0.1× input price; cache *write* ≈ 1.25× (5m) / 2× (1h). So on each
  tool-call respawn you re-send the whole transcript but the stable prefix bills
  at ~0.1×; you pay full price only for the *new* tokens (tool result + new
  emission) plus a small write to extend the cached prefix. "Extended with the
  new portion before each run" — exactly right.
- The catch he didn't name: **the 5-min TTL is the whole game for brr.** Within
  one wake's agentic loop, tool calls are seconds apart → cache stays hot →
  respawns are nearly free. *Across* wakes: bursty wakes <5 min apart share the
  cache (cheap); a wake hours later is a **cold full-price write** of the entire
  prefix. This is why a fragment burst is cheap and a first-wake-of-the-day is
  not.

## "We are not claude/codex to perform the caching" — the key constraint
Correct and load-bearing. brr does **not** control cache breakpoints — the
runner (Claude Code / codex) + provider do. brr's only lever is **what it puts
in the prompt and in what order.** So brr's caching strategy is *composition*:
- Put the **stable** stuff (playbook, AGENTS.md, pitfalls structure) FIRST and
  **byte-identical** every wake → the runner's cache hits it, ~0.1× after the
  first write in a 5-min window. This is the only sense in which "injection is
  ~free" is true — and it's true *because of* caching, not instead of cost.
- Put the **volatile** stuff (Run Context Bundle, recent activity, the task)
  LAST. Volatile content placed early would bust the cached prefix for
  everything after it (prefix-match invariant). Tail placement = volatility
  doesn't invalidate the stable cache.
- Corollary: any wake that *reorders or rewords* the stable prefix pays full
  price on the whole thing. Stability of the front matter is a cost lever, not
  just tidiness.

## The complete shape — three tiers by (volatility, relevance-prob, size)
Not "collapse all queries into injection." The complete shape:

1. **Stable + always-relevant** (playbook, AGENTS.md, pitfalls) → **inject,
   front, byte-identical.** Cached → cheap. ~free *because of* caching.
2. **Small + almost-always-relevant + volatile** (inbox snapshot, portal-state,
   change_token) → **inject, at the TAIL** (after the cache breakpoint). Small
   ⇒ cheap even uncached; ~100% hit rate ⇒ you'd query it almost every wake
   anyway; tail placement ⇒ doesn't bust the stable cache. This is where the
   self-perception query surfaces collapse INTO injection.
3. **Large + conditionally-relevant** (grouped-history JSONL, runtime-recovery
   context.md, older kb/log.md) → **keep as QUERY, on demand.** Large ⇒
   always-injecting = permanent firehose tax; low hit rate ⇒ most wakes don't
   need it; the respawn to fetch it is cheap *because the stable prefix is
   cached*. This is query done RIGHT — the legitimate other half of the shape.

Decision rule: **inject what's small-or-stable; query what's large-and-
conditional. Volatility decides placement (tail vs front), not inject-vs-query.**
The firehose lesson and the "expensive reads" intuition are the same rule seen
from two ends: firehose = tier-3 wrongly injected; a costly read = tier-2
wrongly left as query.

## Additional cut candidates (the "other similar candidates" he asked for)
All are tier-2 self-perception currently shaped as tier-3 query:
- `brr portal state` (read command) — cut; fold into tail injection.
- The instruction to **self-read `inbox.json`** — already injected each
  heartbeat; drop the "re-read the file" framing, keep the woven snapshot at
  plan boundary + pre-closeout.
- The instruction to **self-read `portal-state.json` / BRR_PORTAL_STATE** — same;
  weave the pending-events / budget / posture, and turn `change_token` into an
  injected "attention changed since your last look: yes/no" line rather than a
  field I cat.
Keep as query (tier-3, correctly): grouped-history JSONL, runtime context.md,
older kb/log.md, on-demand dominion files not in self-inject.

## keepalive is NOT a plain delete — it's a tier-2 relocation
Don't cut keepalive the way we cut portal wrap. Its replacement shape is live in
*this* conversation: budget/keepalive belongs as an **injected tail capsule**
("budget remaining: Xm; to continue, say so") + the conversational "ask for a
wider envelope" act. That's tier-2 injection replacing a control-file. So
keepalive waits for the shape to lock; portal wrap is shape-independent (dead
either way) and can go first. (keepalive spans 6 kb pages + 5 test files +
prompts + heartbeat — deeply load-bearing; confirms hold-don't-rush.)

## Execution sequencing (proposed)
1. `portal wrap` removal — shape-independent, smallest blast, fully endorsed.
2. Collapse the three self-perception query surfaces into tail injection
   (tier-2) — needs the prompt-contract tail section designed.
3. keepalive → injected budget capsule + ask-to-continue (tier-2 relocation).
4. Slash the now-dead pitfalls/docs that stood in for the cut commands.
