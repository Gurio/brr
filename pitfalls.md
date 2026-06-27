# Pitfalls — trigger-indexed failure memory
#
# The *remember* step of the environment-shaping loop. When you hit
# friction worth recording but not yet worth a forcing function, write it
# here: brr surfaces a pitfall in your wake prompt when one of its
# triggers appears in the task at hand — the lesson placed in your path,
# not prose you must remember to re-read.
#
# Format: a `## ` heading (the lesson's name), a `trigger:` line
# (comma-separated keywords or loci that tend to appear when the failure
# is about to recur), then the lesson. Slash a pitfall once a lint, test,
# or baked tool guards the failure — the forcing function is the better
# memory, and a stale pitfall is just orientation tax.
#
# Example (delete once you have real ones):
#
# ## Blind 5xx retry masks caller bugs
# trigger: retry, 5xx, http client
# The HTTP client surfaces 5xx to the caller without retrying. If you add
# a retry, gate it behind idempotency — a blind retry hid a caller bug
# here before.

## diffense `--relay` needs `requests` + network — use the embedded-pack fallback
trigger: brr review, --relay, diffense, pr-body, review pack, ModuleNotFoundError requests
Publishing a diffense PR from a sandboxed runner: `brr review <pack> --pr-body --relay`
imports the GitHub gate (for repo detection + gist publication), which imports
`requests` — absent in the sandbox — so `--relay` crashes with
`ModuleNotFoundError: No module named 'requests'`. Don't fight it: drop `--relay`.
`brr review <pack> --pr-body` (no relay) projects the same body and embeds the full
pack JSON in a `<!-- diffense:pack:v1 ... -->` HTML comment, which is the renderer's
fallback when no gist URL exists. Then push the branch and publish via a `gate: forge`
outbox file (`head`/`base`/`title` frontmatter, body = the projected PR body). The
`--pr-title` projection works without network. Validated on #128 (task-260614-1637).

## Full pytest run shows 5 collection ERRORs for gate tests (requests missing)
trigger: pytest, ModuleNotFoundError requests, collection error, telegram_gate, github_gate
`requests` is absent in the sandbox, and `src/brr/gates/{telegram,github,slack}.py`
import it at module load. A bare `python -m pytest` aborts collection with 5 errors
(test_gate_setup, test_github_gate, test_slack_render_update, test_telegram_gate,
test_telegram_render_update) — *before running anything*. This is env friction, not
your change. Run the rest with `--ignore=tests/test_gate_setup.py
--ignore=tests/test_github_gate.py --ignore=tests/test_slack_render_update.py
--ignore=tests/test_telegram_gate.py --ignore=tests/test_telegram_render_update.py`
(or `pip install requests` if network is up). Confirm pre-existing by stashing your
diff and re-collecting one gate test. Seen on task-260614-1644 (#131).

## Editing the host checkout instead of the task worktree
trigger: Edit absolute path, /home/gurio/src/misc/brr/src, /home/gurio/src/misc/brr/kb, wrong branch, worktree, execution root, host checkout
The bundle's Execution root is a *worktree* at
`/home/gurio/src/misc/brr/.brr/worktrees/<task-id>/`, but the obvious repo path
`/home/gurio/src/misc/brr/src/...` is the **host checkout** (on `main`), a different
tree. Read/Edit calls with that host absolute path silently land in the host
checkout, not your task branch — your worktree stays clean and the work is on the
wrong tree (and mixed with whatever the host had uncommitted). Either `cd` into the
worktree and use relative paths, or build absolute paths under
`.brr/worktrees/<task-id>/`. Recovery if you already edited the host tree:
`git -C <host> diff -- <your files> > /tmp/p.patch && git -C <host> checkout -- <your files>`,
then `git apply /tmp/p.patch` inside the worktree (exclude any pre-existing host
changes you didn't make). Seen on task-260614-1903 (#115). **Recurred
task-260616-2151** editing `kb/` (not just `src/`) — and the trigger model
*missed it*: the failure is structural to **every** worktree task that edits
files, but this pitfall only injects when the task body happens to mention the
trigger words, which a "discuss the cockpit" task never will. That's the gap:
the right fix is a forcing function (the Edit tool / runner refusing absolute
paths outside the worktree, or the wake context not advertising the host path),
not a memory I trip over by luck. Surfaced to the maintainer 2026-06-16.

## Emitting a diffense review pack — schema gotchas that fail `--check`
trigger: review pack, pack.json, brr review --check, diffense emit, uncertainty card, lore.headline
Two snags cost a re-validate cycle when hand-emitting a pack (task-260617-2104):
(1) An **uncertainty card's gloss must be `lore.descriptive` or a *top-level*
`headline`** — `lore.headline` is NOT read by `_gloss`, so it fails
`card.gloss missing`. Use `lore.descriptive` for every card, uncertainty
included. (2) **`kind` must be from `KNOWN_KINDS`**, not the id namespace — a
card with `"id": "item:foo"` still needs a real kind like `code-fn-edit`,
`kb-page-new`, `kb-page-edit`, `test-add`, or `custom` (prose/prompt/doc files →
`custom`). A bare `"kind": "item"` only warns (renders generic) but is sloppy.
The clean-pack recipe: summary card first (exactly one), every card carries
`identity.label` + `lore.descriptive` + `provenance`; any card with
`identity.file` needs a resolvable `locator.local` of `path:line`; uncertainty
cards add `subkind` (assumption/concern/dilemma/out-of-scope-flag/follow-up/meta)
+ `severity` (low/med/high/blocking/blocking-for-merge); list every card id in
`reading_order`. `brr review --check <path>` must report 0 errors AND 0 warnings.

## Recovery wake after a mid-flight runner failure starts cold — the failed run's reasoning evaporates
trigger: prior run failed, connection closed mid-response, pick up your work, recovery wake, resume failed run, runner error
When a run dies operationally (API flake, quota), the recovery wake's Run
Context Bundle flags *that* a prior run failed but carries **nothing about
what it was doing**. The failed run leaves no commit, no branch, no
dominion scratch — its in-flight reasoning is gone. The ONLY durable trace
of its mid-flight state is what it already *pushed to the user*: the
`.card` `[update]` notes and `[artifact]` outbox messages, preserved in
the gate-thread history JSONL (`.brr/runs/<this-run>/history/gate_thread-*.jsonl`).
The Runtime-recovery pointer in the bundle is for *this* run's context, not
the failed one. So to pick up: read the gate history JSONL, find the last
`[update]`/`[artifact]` turns from the failed run, and the last user turn
(it usually carries the decision/fork the run was acting on). The Bundle's
"Recent turns" woven view gives short *event bodies* only — not the run's
own emitted artifacts — so you must grep the full JSONL for the plan.
Lesson for next time you're the one at risk: on any non-trivial run, push
your plan/intent to a durable surface *early* (a `.card` + an outbox
artifact, or a dominion scratch note) so a recovery wake reads it off a
live surface instead of reconstructing from history. The daemon-side fix
is a "prior run was working on" recovery handle in the bundle — see
thread-of-record / the note to the maintainer 2026-06-19.

## woven "Recent turns" block carries thread-openers, not the recent tail
trigger: merged and updated, what's that about, thank you closeout, woven thread stale, recent turns oldest first

Observed evt 6q1m (2026-06-23): the Run Context Bundle's "Recent turns (woven,
oldest first)" listed 8 turns all dated 2026-06-10..06-12 — the *opening* turns
of a 415-dialogue thread — while today's event was 06-23. The exchanges that
actually established current state (#171/#175 hook wiring, the salvage net) were
absent from the woven block. I could only tell what "Merged and updated" referred
to by tailing the gate_thread JSONL in the run's history/ dir.

Lesson: on a long-running thread, don't trust the woven "Recent turns" to carry
the *recent* tail — it appears to select salient thread-openers, not recency. When
a closeout/ack references something you can't place, tail
`.brr/runs/<run>/history/gate_thread-*.jsonl` before answering. Candidate to raise
with the maintainer: either rename the block (it isn't "recent") or window it to
the tail, because right now it half-promises continuity it doesn't deliver.

## A hooks-capable runner profile must not also disable hooks (claude --safe-mode)
trigger: hooks back channel, brr hook, post-tool, inbound injection, --safe-mode, settings.local.json, hooks not firing, runner profile, Tier 2
The back channel (#171/#175) can be fully wired daemon-side — config generated,
`brr hook post-tool` returning correct `additionalContext` — and still fire
**zero times**, because the *runner invocation flag* suppresses hooks. The
`claude` profile shipped `--safe-mode`, which sets `CLAUDE_CODE_SAFE_MODE=1` and
disables hooks (+ CLAUDE.md/skills/plugins/MCP), silently no-op'ing its own
`hooks: claude`. Fixed 2026-06-23 → `--setting-sources local` (brr's hook config
lives in the *local* settings source). Diagnostic that nails "did the harness
fire the hook at all": the hook writes `.hook-state.json` on every invocation —
if it's absent after a run of tool calls, the harness never called the hook
(distinct from "called but didn't inject"). Don't trust config-present /
endpoint-works as proof the channel is live; trust `.hook-state.json` / `.flush`
firing evidence, or a visible `[brr portal update]` injection in your context.

UPDATE 2026-06-23 (run …-1953-mf1j): the `--setting-sources local` fix was NOT
sufficient — hooks STILL don't fire under `claude --print` v2.1.185. Same
diagnostic confirmed it (no `.hook-state.json` after 6+ tool calls; endpoint
perfect when run by hand). Leading suspect: **untrusted local hooks** —
`~/.claude.json` has `hasTrustDialogAccepted=False` and no hook-approval record;
headless `--print` can't clear Claude Code's hook trust/approval gate, so
local-source hooks get silently skipped. RESOLVED by experiment 2026-06-23: ran nested `claude --print` against fresh temp
dirs with a sentinel hook and isolated by elimination. It is NOT trust, NOT the
setting-source, NOT a missing matcher — all tested, all no-fire (even
`--output-format stream-json`, even a forced-trusted dir, even with a confirmed
tool call). **The real cause is structural: Claude Code v2.1.185 does not run
settings-file lifecycle hooks under the headless `claude --print "<prompt>"`
invocation at all.** The whole tier-2 was built on a documented-but-never-tested
assumption. Likely (untested) fix: full streaming SDK mode (`--input-format
stream-json --output-format stream-json`), which is a runner.py rearchitecture.
So the firing diagnostic stands (`.hook-state.json` / `[brr portal update]`
injection = proof), but the lesson is broader: **verify a runner capability by
firing it end-to-end before building on it; docs-verified ≠ works.** Demote claude
to Tier 0/1 (responsiveness via heartbeat-polled outbox drain, which DOES work)
until streaming lands. Full writeup: `kb/design-runner-back-channel.md` §Second
activation failure / §Fix directions.

---

trigger: stream-json, runner_stream, streaming runner, --print, mid-loop injection, stop-control, boundary injection, persistent session, claude --print
**`claude --print` stream-json is SINGLE-TURN — injection after the model commits to finishing is silently dropped, and there is NO stop-control.** Live-verified 2026-06-26 (evt 8f8y) driving `runner_stream.py` against real haiku v2.1.191. Two seams behave very differently:
- **Mid-loop injection** (a user message written on stdin *between tool calls*) IS attended — but only while the model still has pending tool calls. A 1-tool task ignored a post-boundary injection (it had already decided to finish); a 3-tool task acted on the same injection between calls.
- **Stop-control** (block a premature finish / fold a late event into the run) does **NOT** work under `--print`: the process exits on the first `result` event no matter what's on stdin. Keeping stdin open does nothing.
**The fix is to DROP `--print`** — claude stream-json *without* `--print` runs a **persistent multi-turn session** (verified: result#1 "RED" → send msg → result#2 "BLUE", one process). In persistent mode, after a `result` a new user message starts a fresh turn the model addresses → that *is* stop-control, same stdin-write mechanism as mid-loop injection. `build_stream_cmd` currently inherits `--print` from the claude profile cmd, so it builds the weaker single-turn channel — step 2 must strip it. Also: `run_stream`'s `on_boundary` callback can't inject (no stdin handle) — boundary seam is read-only until step 2 passes it an injector. Don't reason about this from the spike notes; the spike conflated the two seams. Live harnesses kept at `/tmp/brr_stream_livetest/drive{,2,3,4}.py`.

## Firing-test a runner CLI from a CLEAN env — parent agent session leaks CLAUDE_CODE_SAFE_MODE
trigger: claude hooks, codex hooks, --print, settings.local.json, PostToolUse, PostToolBatch, hooks don't fire, firing test, runner hooks
When you spawn `claude`/`codex` to test whether hooks/skills/plugins fire, you
are (usually) spawning it from inside your OWN agent session, which exports
`CLAUDE_CODE_SAFE_MODE=1` (+ CLAUDECODE, CLAUDE_CODE_SESSION_ID, AI_AGENT, …).
Safe mode **silently disables settings-file hooks** while logging the reassuring
"managed settings-file hooks still run" — so the child reports "Found 0 total
hooks in registry" and you wrongly conclude hooks don't fire under `--print`.
This single contaminant poisoned the whole streams-vs-hooks design for weeks
(evt o538, 2026-06-27). ALWAYS run such firing tests with
`env -u CLAUDE_CODE_SAFE_MODE -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT
-u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_CHILD_SESSION -u AI_AGENT … claude …`.
Confirmed truth: Claude PostToolUse/PostToolBatch/Stop(block-continues) all fire
under `--print` with additionalContext injection; Codex PostToolUse fires too.
Production fix landed: `runner.clean_runner_environ()` strips these. (If that
helper is ever proven by a test to make the leak impossible end-to-end, slash
this pitfall — the guardrail is the better memory.)
