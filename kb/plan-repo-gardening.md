# Plan: repo gardening — initial context, respawn model, imagery, kb/code sweep

**Status: planning — written 2026-06-28 (evt-spwd) on Claude.** The maintainer
asked this run to *evaluate and plan only*; a later run on a cheaper-but-capable
model (Sonnet) executes the plan. We are at an architecture crossroads where
**vessel / medium / runner / core** are mixed across configs, kb, prompts, and
code, plus a leaning to settle the imagery on *Armored Core* (Core/Shell) and to
build a cost-and-capability-aware respawn model. This hub holds four tasks.

- **Task 1 — initial-context reweave:** see
  [`plan-initial-context-reweave.md`](plan-initial-context-reweave.md) (the
  detailed file-by-file spec; the maintainer's most-important task).
- **Task 2 — informed respawn model:** Part 2 below; extends
  [`design-runner-media.md`](design-runner-media.md).
- **Task 3 — imagery / vocabulary:** Part 3 below (a naming decision; the
  maintainer invited pushback — given here).
- **Task 4 — kb + code gardening sweep:** Part 4 below.

Companions: [`design-portal-grammar.md`](design-portal-grammar.md),
[`design-resident-boundary.md`](design-resident-boundary.md),
[`plan-cost-aware-cockpit.md`](plan-cost-aware-cockpit.md) (to be renamed,
Part 3), [`design-runner-back-channel.md`](design-runner-back-channel.md).

## Daemon-quota check (the maintainer's side-ask)

The maintainer restarted the daemon with the Claude quota-awareness changes and
asked me to verify. **It works, partially as designed:** this wake's
`portal-state.json` carries `resources.quota` = `known`:
"session 100% left (resets 12am Berlin); week 55% left (resets Jul 3)" — the
cached `/usage` PTY scrape rides into the wake. But `resources.spend` and
`resources.context_window` are **`absent`** at wake ("no … reading from this
medium yet"). That is the **structural boundary** already recorded
(`design-resident-boundary.md`): Claude spend/context are *terminal* (written
to the per-event outbox after `claude --print` exits), so they appear on a
run's closeout card, never in the *next* run's opening bundle. Codex, by
contrast, exposes live subscription quota from the on-disk session rollout.
**Net: Claude quota now rides the wake (good); Claude spend/context remain
closeout-only (by Anthropic's surface, not a brr bug).** Part 2 below treats
this asymmetry as a v1 constraint, not a thing to fix.

## Part 2 — Informed respawn model (Task 2)

The foundation shipped 2026-06-28 (`runner_media.py`: schema,
`implicit_medium`, conservative `select_medium`, `RespawnRequest`,
profile-borne metadata). The maintainer's Task-2 asks add five requirements on
top of `design-runner-media.md`. Plan each as a slice for the execution run.

### 2A — Cheap dispatcher runner owns the user-facing knobs, then respawns
The maintainer's shape: **the initial wake runs on a cheap Shell/Core**; it
parses the user's intent and execution preferences ("run on Opus", "in half an
hour on Codex"), then **respawns** the real work onto the chosen Runner.
- This is the "first selector is deterministic and conservative; the resident
  escalates after reading the repo" principle already in
  `design-runner-media.md` §Dispatch — but extended: the cheap runner is also
  the **knob parser**, not only a fallback.
- v1 keeps the *parked* `RespawnRequest` (no auto-chain until #128's
  `defer_until`/re-claim). The cheap runner emits a respawn request naming the
  target Runner + carry-forward context; the daemon (or a user nod) starts it.
- **Open question for the maintainer:** does the cheap dispatcher *always* run
  first (every event pays one cheap hop), or only when the event looks like it
  needs routing? Recommend: **only when `runner=auto` and `runner_policy` is
  cost-aware** — a pinned `runner=` skips the hop. Keep low cognitive load:
  the user sets intent in plain words, brr does the routing.

### 2B — Extract available models from the Shell itself (no hardcoded staleness)
The maintainer wants brr to pick up a new model release on an installed Shell
without a brr update. Plan:
- Add a per-Shell **model-probe** (`brr/<shell>_models.py` or fold into the
  existing `*_status.py`): `claude` and `codex` should expose an installed
  model list (probe the CLI's own listing/help, cache with TTL like
  `claude_usage.py`). Gemini stays intent until installed.
- The probe feeds a **dynamic Core registry** the selector reads, instead of
  the static `model:` fields in profiles being the only known Cores. Static
  profile metadata becomes *defaults/overrides*; the probe is the live source.
- Provenance-tag each Core (probed vs declared) like the quota grades.

### 2C — Capability-aware selection (swe-bench / terminal-bench), cached
The maintainer wants cost **and capability** awareness, ideally from a
benchmark. Plan:
- Add a small, **cached capability table** keyed by model id (swe-bench-verified
  / terminal-bench scores), shipped as a data file the resident can refresh,
  *not* a live network call on the prompt path. Tag freshness/source.
- The selector's `class` (economy/balanced/strong) becomes *derivable* from
  capability score + cost_rank rather than hand-set, while keeping hand-set as
  an override. Keep `cost_rank` as the coarse tie-break ordering hint it is.
- **Pushback/caution:** benchmarks go stale and game-able; treat them as a
  *hint to the class assignment*, never a hard selector. The deterministic,
  conservative selector stays the floor (no revived LLM triage). Recommend
  shipping 2B (model discovery) before 2C (scoring) — discovery is the
  load-bearing half; scoring is polish.

### 2D — Scheduling-aware respawn
"Run in half an hour on Codex" = a scheduled respawn. This already has a home:
the dominion `schedule.md` (`at:`/`every:`) and #128's `defer_until`. Plan: the
`RespawnRequest` gains an optional `at:`/`defer_until` so a respawn can be both
medium-routed and time-deferred. No new mechanism — compose the two existing
ones.

### 2E — Show running + scheduled runs on the brnrd overview
`plan-brnrd-dashboard-mvp.md` has **no run-listing view today** (grep: none).
The presence registry (`presence.py`) and schedule (`schedule.py`) hold the
data locally. Plan: add an **"Activity" view** to the dashboard inventory
(running runs from the presence/run registry; scheduled wakes from schedule
entries + parked `RespawnRequest`s). This is a dashboard slice to add to
`plan-brnrd-dashboard-mvp.md`'s view inventory, consuming the brnrd protocol —
flag it there so the dashboard plan owns the UI and this plan owns the data
contract (what a run/scheduled-wake record must expose).

### 2F — Portal/structured-state upgrade (already sequenced)
`design-runner-media.md` step 3 ("replace flat `resources.quota` string with
structured `runner_media`") and its "Standing portal candidates" are the
governance-exposure half (the maintainer's "expose selected medium/cost/quota
in the card"). Keep that sequence; rename `runner_media` → `runner`/`core` per
Part 3.

## Part 3 — Imagery & vocabulary (Task 3) — decision + pushback

The maintainer invited pushback on two fronts. Here is my judgement (he sent
"judgement." as the trust mandate). **These are reversible naming calls; I
recommend adopting them and flag them for veto.**

### Term sprawl, measured (2026-06-28)
| term | code | prompts | kb | verdict |
| --- | --- | --- | --- | --- |
| runner | 271 | 35 | 1056 | **keep** (umbrella) |
| medium | 35 | 8 | 174 | **retire** → Runner/Core |
| vessel | 20 | 2 | 17 | **retire** → Runner/Core |
| core | 8 | 0 | 92* | **adopt** = the model |
| shell | 14 | 0 | 60* | **adopt** = the CLI |
| portal | 71 | 8 | 286 | **keep** (genus) |
| viewport | 0 | 0 | 0 | **adopt only as the inbound sub-type** |
| cockpit | 1 | 0 | 138 | **retire** (already settled, never swept) |

\* `core`/`shell` counts are mostly incidental ("core idea", shell commands) —
confirm with context-grep before mass-rename so we don't clobber unrelated use.

### Recommendation 3.1 — Runner = Shell + Core; retire vessel & medium
Adopt the Armored Core frame, with one correction to the maintainer's phrasing:
- **Resident** = the persistent spirit/identity (the "semantic silkworm").
  *Keep this word* — it already names the entity the maintainer called the
  silkworm. **Do not move "runner" onto the spirit:** we already have
  "resident", and overloading "runner" would orphan 271 code uses and the
  `runner=` knob.
- **Runner** = the *executing body* for one thought (the mech). It is composed
  of:
  - **Shell** = the CLI program on PATH (`claude`/`codex`/`gemini`) — the
    carapace that gives the Core hands (file ops, tools, hooks).
  - **Core** = the model (`opus`/`sonnet`/`gpt-5-codex`) — the swappable reactor.
- A **profile** in `runners.md` names a Runner = a Shell (+ optional pinned
  Core) + selection metadata. The cost-aware layer selects **Cores within
  Shells**. Rename `runner_media.py` → `runner_select.py` (and the page
  `design-runner-media.md` → `design-runner-cores.md`); `RunnerMedium` →
  `RunnerProfile` or `Runner`. Config: `runner=` stays (selects the Runner);
  the `model:` field is "the Core"; **no new user knob required.**

This dissolves D1 (the triple-naming) with the least churn: "runner" — the most
entrenched, accurate-enough word — survives; only the two redundant
imports (vessel, medium) die, and Shell/Core fill the two real sub-layers that
were previously unnamed or called "medium".

### Recommendation 3.2 — Keep "portal"; "viewport" only as the inbound kind
**Pushback against renaming portal → viewport wholesale.** The maintainer's own
instinct ("a portal lets you move *through*") is exactly why portal is the right
genus: `design-portal-grammar.md` defines a portal as a seam where the stream
**turns to the world**, and it has *three* directions — **inbound** (state
flows in), **outbound** (you emit out), **parked** (you emit and the
continuation waits). A *viewport / magic mirror / illuminator* is
**perception-only**: you can look, things come to you, but a mirror cannot
*send* and cannot *park*. Renaming the genus to viewport would silently drop the
outbound and parked semantics that the outbox, `gate:` sends, `.card`, and
PLAN→approve depend on.

So: **portal stays the genus.** Where the maintainer's mirror instinct is
*correct* is the **inbound** portal specifically — `portal-state.json`,
`inbox.json`: you look in, state flows to you. Name that sub-type a **viewport**
(or keep "inbound portal"; "viewport" is a fine, evocative label for it). This
honours both the instinct and the design:
- inbound portal = **viewport** (perception) — ties to *injection = perception*;
- outbound portal = emission seam (action) — ties to *emission = action*;
- parked portal = a threshold that holds the continuation.

This also lands the dominion's `portal-reshape-synthesis` frame:
**perception = injection (free, woven into the scroll), action = emission;** the
retired *cockpit* was the polling/queryable surface. Pushing inbound state from
"a file you `cat`" (viewport-as-cockpit) toward "woven into the wake"
(viewport-as-injection) is the standing direction — see Part 2F.

### Recommendation 3.3 — Finish the cockpit retirement
"cockpit" was disowned in `design-portal-grammar.md` §3 but never swept (138 kb
hits, 1 code hit, 2 plan filenames). Rename the files and sweep the prose:
- `plan-cost-aware-cockpit.md` → `plan-cost-aware-runner.md` (or fold into
  `design-runner-cores.md`);
- `plan-resident-cockpit.md` → `plan-resident-portals.md`;
- replace the in-code link in `prompts.py` (D2) and sweep kb prose.

### The unifying register (keep)
The **ornamented magic scroll** the resident turns to the world through, Ummon
tone — already committed (dominion `portal-reshape-synthesis`, the `run.md`/
introspection voice reshape). The vocabulary above sits inside it cleanly:
the resident (spirit) weaves the scroll; portals are the ornamented seams; the
Runner (Shell+Core) is the body the spirit is given for a wake. No conflict.

## Part 4 — kb + code gardening sweep (Task 4)

The edit/research-heavy pass: read broadly, resolve the resolvable, surface the
unresolvable. Method for the execution run:

### 4A — Mechanical, deterministic first (cheap, high-confidence)
From this wake's kb-health preflight + greps, the known backlog:
- **Vocabulary sweep** (after Part 3 is confirmed): retire vessel/medium/cockpit
  across kb + code + prompts; introduce Shell/Core. Rename the 2 cockpit plan
  files and `runner_media.py` → `runner_select.py`.
- **Index hygiene:** 4 pages missing from `kb/index.md`
  (`decision-brnrd-repo-first-model`, `design-brnrd-channel-routing`,
  `design-brnrd-github-bot-user`, `design-brnrd-github-installation-sync`) —
  add index entries.
- **Oversized pages** (>32KB): `design-brnrd-protocol` (101KB!),
  `design-diffense` (87KB), `index` (57KB), `subject-managed-mode`,
  `design-agent-dominion`, `design-agent-ergonomics`,
  `design-resident-boundary`, `plan-failover-compute` — split into hub +
  daughters or compress accreted history to a lineage breadcrumb. The index
  being oversized is itself a signal it should become a hub-of-hubs.
- **Proposal-scaffolding cleanup:** `decision-licensing-and-defense`,
  `decision-monorepo-structure`, `design-diffense`, `plan-env-fly-machines`
  are accepted but still carry Goals/Alternatives proposal shape — compress to
  current-state synthesis + a short Rejected-alternatives appendix.
- **Hub coverage:** `index §Research` and `index §Reviews` lack `subject-*`
  hubs — consider writing them.

### 4B — Semantic reconciliation (judgement, do carefully)
- `design-runner-management.md` is marked "superseded by the cockpit framing" —
  re-point it at the post-cockpit shape (`design-runner-cores.md` + portals)
  rather than a retired label.
- Reconcile the runner/medium/vessel framing across `design-runner-media.md`,
  `design-resident-boundary.md`, `design-runner-back-channel.md`,
  `subject-managed-mode.md`, and the index so the graph says Runner/Shell/Core
  with one voice.
- The portal-grammar "concept prose sweep" (step 9 there) overlaps 4A's cockpit
  sweep — do them together.

### 4C — Surface, don't force (the unresolvable)
The execution run should **not** invent resolutions for genuine forks. Where a
page records an open product/values decision (relay billing specifics, parallel
execution, #128 claim model, capability-benchmark trust), leave it flagged and
report it to the maintainer rather than papering it with a guess. The gardening
is "leave the graph no worse, ideally clearer," not "decide everything."

### 4D — Method
Read in dependency order (most-referenced first: `design-brnrd-protocol`,
`decision-pricing-shape`, `subject-managed-mode`, `design-billing`,
`notes-pondering-fleet`). Keep a running conflict ledger in the dominion;
promote settled resolutions to kb; commit per theme. Budget-aware: this is the
largest task — the execution run should chunk it and may want its own follow-up
wakes per area rather than one giant sweep.

## What needs the maintainer before the execution run
1. **Vocabulary veto check (Part 3.1/3.2):** adopt Runner=Shell+Core, retire
   vessel+medium, keep portal (viewport = inbound sub-type only), finish
   cockpit retirement? This **blocks Task 1** (the reweave uses these terms).
2. **Dispatcher-hop policy (2A):** cheap hop only on `runner=auto`+cost-aware,
   or always? Recommend the former.
3. **Sequencing:** confirm Task 1 (reweave) goes first on the Sonnet run, then
   Task 2 slices, with Task 4 gardening as chunked follow-ups.
