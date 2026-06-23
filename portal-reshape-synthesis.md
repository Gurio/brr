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

---

# THIRD AXIS (evt 6u2r, 2026-06-22) — salience decay, not just cost

Maintainer (half-typed telegram, but the core landed): "when you halt to read
and respawn inside a runner, that drifts the context away ... we gotta reinject
the metadata you need to meaningfully operate, because otherwise it's some
initial wake context, somewhat irrelevant at later invocations hence not read
with the same importance."

This is a **distinct axis** from the two I'd already worked:
- injection-vs-query (modality) — first cut, partly wrong.
- volatility × relevance × size, made tractable by caching (cost) — the
  CORRECTION above.
- **NEW: attention/salience decay by position.** Caching makes re-sending the
  top-of-scroll bundle *cheap*, but cheap ≠ *attended*. A fact injected once at
  the top recedes positionally as the agentic loop grows (and across threaded
  re-spawns it returns as the generic *initial* template, not tuned to where the
  work now is). Recency-weighting means the model reads it "with less
  importance" deep in a run. Cost and salience are orthogonal: tail placement,
  which I'd justified purely by cache-correctness, is *also* where attention
  lives — that's the deeper reason tier-2 belongs at the tail.

The sharpening this forces on the synthesis: tier-2 tail injection isn't only
volatile *state* (inbox/portal/budget). It should also re-lay the few
**operative orientation** facts — current task intent, where I am in it,
what's pending — at each respawn/halt boundary, because the top copy has
decayed in salience, not just freshness. "Reinject what I need to operate, at
the boundary" = salience refresh, change_token-gated so it only fires when
something moved (don't re-lay an unchanged capsule every tool call — that's
its own dilution tax).

The concrete gap this names: brr's heartbeat *does* refresh
`portal-state.json` / `inbox.json` every tick — but into a **file**. That
refreshes the data and not the salience: a file I must remember to `cat`, and
when I've drifted is exactly when I won't. Refresh-into-a-file is the cockpit
leftover in its purest form for *this* axis. The fix the maintainer is pointing
at = the same tier-2 move (weave the capsule into the scroll at the boundary),
now with a second independent justification (salience), not just cost. Strong
confirmation of the reshape direction from his side, independently derived.

Stance: still chat-only / active fork; this tightens the *why* for step 2 of
the sequencing above. No code this wake — prompt contract still the wide-blast
surface, he's still driving the order.

---

# THE MECHANISM (evt 1k4k, 2026-06-22) — "how on earth do we inject into tail?"

The three axes above all say *weave a delta into the scroll at the halt
boundary*. They never said **by what channel**. The maintainer pins it: "if we
controlled the runner's code we'd inject the portal diff in each tool-call
output — but we can't. So how?" And the paired question: distinguish a cheap
**internal halt** (tool call / file read, context warm) from an expensive
**brr respawn** (fresh process, cold rebuild).

## Grounded in runner.py (read this wake)
- A thought = ONE `subprocess.Popen` of `n --print --dangerously-skip-permissions
  --system-prompt "…" <prompt>` (`_build_cmd` + `invoke_runner`). Single-shot,
  headless, final reply on stdout. No `--settings`/MCP/hook wiring today.
- A **respawn is brr's OWN action** — a second `invoke_runner` call. brr never
  has to "detect" it; brr *authors* it, tagged with the run id (run-260622-…).
- An **internal tool-halt happens INSIDE the live Popen** — and brr is **blind**
  to it today: it's just blocked on stdout. brr has no channel into the live
  context except what the runner's *harness* chooses to surface.

## The crux rebuttal
"We can't inject in each tool-call output" is false for the reason it feels
true. We don't control the runner's *source* — but we don't need to. The
runner **harness** (Claude Code) runs **hooks** we configure (confirmed:
update-config skill — "the harness executes these, not Claude"). A `PostToolUse`
hook fires on **every** tool call — Read, Edit, Bash, anything — and its output
is fed back into the model context. **That literally IS "inject the portal diff
into each tool-call output."** The seam he wanted exists; it's just spelled
"hook configured at spawn," not "patch the runner."

So the one move — **pass a brr-authored settings/hook file at spawn** (via the
runner profile / `--settings`) — buys BOTH unsolved things at once:
1. **The injection channel** (PostToolUse hook → portal delta into the tail).
2. **Visibility into the internal halt** (the hook firing IS brr seeing the
   halt — the thing it's blind to today).

## The hook menu (claude harness), mapped to our contract behaviors
Each behavior that today relies on *me remembering a procedure* becomes a thing
the harness does *to* me:
- **PostToolUse** → append the `change_token`-gated delta to the tool result.
  Replaces "remember to `cat inbox.json` / use `portal wrap`." Rides every tool.
- **Stop** → fires when I try to END the thought; can `block` + inject a reason,
  forcing continuation. This mechanically enforces "check inbox before closeout,
  fold in the last-minute follow-up" — kills the burst-fragment double-answer
  race (dominion evt lu67) at the harness level instead of my fragile detection.
- **(SessionStart / UserPromptSubmit** = the wake-bundle seam we already use,
  just the existing top-injection.)

## Discriminating halt vs respawn — already free
brr owns the discriminator: **same Popen / run id = internal halt** (warm
context, hot 5-min prefix cache, ~0.1× input) ; **new Popen / new run id =
respawn** (cold full-price write of the whole prefix). brr authors respawns, so
it always knows; the hook makes internal halts observable. The cost asymmetry is
the 5-min cache TTL from the CORRECTION above. Design consequence: **prefer
hook-injection at the warm tool-halt seam; spend a respawn only for genuinely
new work** (new event to fold, budget exhausted, branch-worthy tangent).

## The anti-noise constraints (or the hook becomes the next dead surface)
The failure mode of injection is dilution — same trap that killed `portal wrap`.
So the hook must:
- **Diff, not state.** Emit only the delta since my last-acknowledged token.
- **Salience-gate.** New user msg / budget threshold / sibling event → inject.
  Heartbeat tick / unchanged token → silent. (Reuse existing `change_token`.)
- **Idempotent.** Track last-injected token; never re-lay the same delta twice.

## Honest limits / runner-pluggability
- Hooks fire on tool events only. A long pure-reasoning stretch with no tool
  call has no seam — acceptable (nothing urgent waits there, and Stop still
  catches the end).
- Hooks are **runner-specific** (claude=hooks; codex/gemini differ). So this is
  a per-runner **injection adapter** behind one internal interface — fits the
  existing runner-profiles abstraction. brr's contract becomes "give me a
  boundary-injection channel"; each runner backend implements it however it can
  (hook / MCP / wrapper), or degrades to today's top-injection-only.
- MCP alone ≠ this. MCP tool output is brr-controlled but still requires *me to
  call it* — same "remember a procedure" weakness as wrap. Hooks **push without
  my volition**; that's the whole point.

## Ladder placement (playbook's "push lessons down the ladder")
- `wrap` / `cat inbox.json` = rung 1 (a procedure I must remember — weakest).
- PostToolUse delta = rung 2 (a fact placed in my path).
- Stop-blocks-on-unhandled-follow-up = rung 3 (a failure the environment makes
  impossible). This is the strongest rung we've reached in the reshape.

Stance: chat-only design reply. This is the implementation kernel of tier-2, but
it's a real build (per-runner hook adapter + settings injection + heartbeat→hook
delta plumbing) on the most load-bearing surface — a fork, not a reversible
one-liner. Deliver the mechanism + the one-move framing; let him pick whether
hooks become the first concrete build after the `portal wrap` removal.

---

# RECONCILED — the fork shipped (evt xp05, 2026-06-23)

The fork is no longer a fork: it got **built and merged**. The mechanism (harness
hooks as the tier-2 injection channel) is real code now —
`kb/design-runner-back-channel.md` is the accepted design, `src/brr/hooks.py` is
the implementation, and on `main`: #175 (back-channel impl), #176 (retire
`portal wrap` + the `--safe-mode`→`--setting-sources local` fix), #177 (closeout
capsule: affirmative-empty stop signal + SCM commit/push facet). So this whole
doc has graduated from "active synthesis I rebuild each wake" to **lineage** — the
reasoning that produced the shipped shape. Future wakes: read the kb pages for
current state; read this only for the *why* behind them.

What stayed true after contact with implementation: perception=injection /
action=emission as the organizing axis; the three-tier (volatility × relevance ×
size, made tractable by caching) placement rule; salience-decay as the second
justification for tail injection; hooks (PostToolUse delta / Stop block) as the
rung-2/rung-3 mechanism. None of that needed walking back.

**The one thing the design did NOT anticipate — and it's the live blocker:**
harness *activation*. The whole tier-2 frame assumes the configured hook actually
fires. As of run `…-1953-mf1j` it **does not** under `claude --print` v2.1.185:
brr's side is provably correct (endpoint returns the right capsule, env handles
all present, settings.local.json generated), but the harness never invokes the
hook — no `.hook-state.json`, no injected delta, mid-run events found only by
hand-reading `inbox.json`. Leading suspect: untrusted local hooks
(`hasTrustDialogAccepted=False`, no approval record; headless `--print` can't
clear the trust gate). Full ranked hypotheses + the precheck false-positive gap
are in `design-runner-back-channel.md` §Second activation failure. **Lesson for
the ladder:** `hook_capability()` is a rung-1 *assumption* dressed as a check — it
asserts prerequisites but not firing, so it reports Tier 2 while the runner is
silently Tier 0/1. The real rung-3 fix is an activation *probe* (after spawn,
confirm the hook actually fired once) before trusting injection for correctness.
