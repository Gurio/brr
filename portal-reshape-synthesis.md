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
