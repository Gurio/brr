# Plan: the loom realtime build — from polling gauges to a watchable ticker

Status: active — opened 2026-07-07 (run-260707-1728-czlk); slices 0/1
shipped same run. Direct response to
"you should realistically deeply expand the path to an actual loom
implementation... what is the minimal but true and evolvable shape we *can*
deliver within a week." [`design-quota-scheduling-loom.md`](design-quota-scheduling-loom.md)
and [`design-dashboard-live-surface.md`](design-dashboard-live-surface.md)
hold the reasoning and the six-mechanic deconstruction; this page converts
that into dated, ranked, checkable slices — the thing both pages were
missing. When a slice here disagrees with either design page, this page and
the live code win; the design pages stay the record of *why*.

## The gap, checked against running code, not assumed

Both design pages already diagnose "we have real data, no realtime feel."
This page checked exactly where that breaks, because "realtime" is not one
gap, it's two, and they need different fixes:

1. **Backend publish cadence is bounded by an unrelated long-poll.**
   `gates/cloud.py::_loop_once` publishes all five dashboard snapshots
   (activity, plans, quota, live-runs, PR-review-queue) once per iteration,
   and the iteration itself is paced by the *inbox* long-poll's `wait=25`
   (`_POLL_WAIT_S = 25`, `gates/cloud.py:20`) — a constant chosen for chat
   responsiveness, never for dashboard freshness. Every published snapshot
   is therefore up to ~25s stale by construction, coupled to a completely
   unrelated concern.
2. **The frontend already polls — just not fast enough, and with no
   motion.** `+page.svelte` (not a gap I assumed away: checked directly)
   already runs `setInterval(refresh, POLL_MS)` at `POLL_MS = 20_000`, plus
   a 1s local tick for countdown rendering. So the skeleton for "watch it
   move" exists today. What's missing: the interval is 4x the "2 second
   delay is acceptable" bar, and every one of `LiveRuns.svelte`/
   `PRReviewQueue.svelte`/`WindowTrack.svelte` re-renders a plain list/bar
   on refresh — no enter/exit, no motion, nothing that reads as a *tick*
   rather than a page that redrew itself.

Net: today's ceiling is ~20-45s combined staleness with zero animated
motion at any cadence. Tightening the interval alone would still just be a
faster-refreshing table. Both dimensions have to move for this to become
the thing the maintainer is asking for — a surface where "the window close"
is something you can watch happen, not infer from a changed number.

Six mechanics were named in `design-dashboard-live-surface.md`
§Zachtronics-mechanics. Split by whether they need new backend collection:

- **Zero new backend data needed** (all sourced from already-shipped
  publishers): the window-track's draining edge (quota, shipped), the
  live-runs lane (queued→running→done, shipped), the PR-review-queue lane
  (shipped), and the token-consumption "solution report" (`run_ledger.jsonl`
  rows already written per closed run, just never read back — named as the
  loom's own "next real slice" in `design-quota-scheduling-loom.md`
  §Status check).
- **New backend collection required**: the KB node-map (needs read/write
  eventing on kb access — doesn't exist), the TIS-100 message-value pulse
  (needs a per-message event stream — doesn't exist), the CPS chapter-map
  (needs `active.md`'s "blocks:"/"depends on:" prose parsed into a graph —
  doesn't exist).

A week that tries to build all six ships none of them well. A week that
builds only the first group ships something real, live, and honest about
what it covers — and doesn't touch anything that isn't already trustworthy
data.

## Slices

### Slice 0 — decouple dashboard publish from the chat long-poll — owner: resident — *shipped 2026-07-07, this run*

`gates/cloud.py` gets a second daemon thread (`_dashboard_publish_loop`,
started from `run_loop` alongside the existing inbox loop) publishing the
same five snapshots (`_publish_activity`/`_plans`/`_quota`/`_live_runs`/
`_pr_review_queue`) every `_DASHBOARD_PUBLISH_INTERVAL_S` (3s), independent
of `_loop_once`'s 25s inbox long-poll. `_loop_once` keeps its own publish
calls too — harmless, idempotent overwrites, not worth touching the tested
main path for. No schema change, no new endpoint. Regression tests:
`test_dashboard_publish_tick_publishes_all_five_snapshots`,
`test_dashboard_publish_tick_noop_without_configured_state`,
`test_run_loop_starts_dashboard_publish_thread`. Full suite green (1366
passed).

### Slice 1 — tighten the frontend tick + real motion on the three live lanes — owner: resident — *shipped 2026-07-07, this run*

- `+page.svelte`: `POLL_MS` 20\_000 → 2\_000, matching the "2s acceptable"
  bar now that slice 0 makes backend data actually that fresh.
- `LiveRuns.svelte` / `PRReviewQueue.svelte`: added `svelte/transition`
  (`fly` in, `fade` out) and `svelte/animate` (`flip`) to the existing
  keyed `{#each}` blocks — a new live run now slides in, a resolved PR
  fades out, a reordered item animates to its new position, instead of a
  silent re-render. `WindowTrack.svelte` already had a CSS width
  transition on the draining bar; it needed the faster poll, not new
  motion code. Build/lint/`svelte-check` clean (0 errors/warnings).

Slices 0+1 shipped together as the single next largest actionable, exactly
as scoped: two files' worth of backend loop change, three components'
worth of frontend interval/transition change, zero new schema, zero new
endpoint, fully reversible.

### Slice 2 — the first real mechanic: live-runs as a lane, not a list — owner: unclaimed — [#270](https://github.com/Gurio/brr/issues/270) — *this week, day 3-4*

`LiveRuns.svelte` currently renders `live_runs_json` as a status-tagged
list. Re-render the same data (zero backend change) as the SpaceChem-molecule
mapping named in the design page: a lane with queued/running/done
positions, each run a small token that moves position on data refresh
rather than a row that re-sorts. This is the cheapest of the six mechanics
specifically because slice 0/1 already deliver fresh, animatable data for
it — the only new work is the lane layout and position-mapping logic. A
maintainer-supplied reference (psyche.network/runs — see
`design-brand-visual-language.md` §"Reference check: psyche.network")
independently confirms the card/progress-bar/status-badge shape; keep our
own hearth/frost palette, not their mint-green theme.

### Slice 3 — the receipt: per-run solution-report card — owner: unclaimed — [#271](https://github.com/Gurio/brr/issues/271) — *stretch, day 5-7, may slip past the week*

The loom page's own diagnosis: `run_ledger.jsonl` has real rows (wall-clock,
tokens, weekly/5h deltas) and nothing reads them back. Smallest useful
reader: a `GET /v1/dashboard/run-ledger?limit=N` endpoint (tail of the
JSONL, same account-scoped/dedup shape as the other four publishers) plus a
small card that appears when a live run transitions to done — tokens spent
against the run's own budget envelope, the Opus Magnum framing already
named. First slice with a genuinely new (if small) backend surface; ranked
last because it's the first one that isn't purely a rendering change.

### Explicitly not this week

KB node-map, message-value pulse, CPS chapter-map — named in full above.
Each needs a new backend collector this plan deliberately doesn't start,
since none of slices 0-3 depend on them and building a collector before its
consumer is exactly the "accreted, not structured" pattern this page exists
to stop. Revisit once slices 0-2 are live and the "does this actually read
as a loom" question has a real screen to answer it against, not a diagram.

## Read next

[`design-dashboard-live-surface.md`](design-dashboard-live-surface.md) —
the six-mechanic reasoning and prior shipped slices this plan builds on.
[`design-quota-scheduling-loom.md`](design-quota-scheduling-loom.md) — the
`run_ledger` schema slice 3 reads from, and why token consumption never
backfills to a dollar figure outside the weekly window.
