# Plan: state-first kb maintenance and regular grooming

Status: shipped on 2026-05-13; follow-up active in
[`plan-kb-maintenance-latency.md`](plan-kb-maintenance-latency.md)

This page is the shipped receipt for the state-first kb maintenance
slice. The live contract is the [`AGENTS.md`](../AGENTS.md)
Knowledge base section; the current synthesis is in
[`subject-kb.md`](subject-kb.md); the originating rationale is in
[`decision-kb-shape.md`](decision-kb-shape.md).

## What landed

- `AGENTS.md` now treats the kb as current-state synthesis plus
  concise lineage breadcrumbs. Deep history lives in git and
  [`kb/log.md`](log.md), not inline revision narratives.
- `prompts._read_recent_log` uses a byte budget as well as an entry
  cap, so one verbose log entry cannot dominate every task prompt.
- `kb_preflight.scan` returns severity-bearing findings:
  `error` for structural drift, `warning` for heuristic advisories
  such as `oversized-page` / `missing-status-marker` /
  `revision-history-heavy`, and `info` for soft hints such as
  `recent-log-budget-exceeded`, `hub-coverage`, and
  `proposal-scaffolding`.
- `kb_health.compute_graph_stats` feeds the maintenance prompt with
  graph context: pages by kind, largest pages, peer-orphan candidates,
  and log shape.
- `_maybe_kb_maintenance` runs the deterministic scan after successful
  daemon tasks unless `kb_maintenance=never`. Under the current
  `auto` policy it invokes the LLM redundancy pass when `kb/` changed
  or the scan produced any finding, injecting task-touched pages,
  findings, and graph stats.
- Maintenance edits left uncommitted by the LLM runner are rolled into
  one task-branch commit authored as
  `brr maintenance <brr-maintenance@brr.local>`, and a
  `kb_maintenance_done` packet lets progress cards show
  `maintenance: clean` or `maintenance: N kb commits`.

## Current boundary

The shipped slice deliberately kept kb maintenance as a safety net on
top of agent discipline. Agents still own the kb pages they write;
the daemon adds a deterministic scan and a thin redundancy pass for
branch-local cleanup. The user-facing CLI did not gain a `brr kb`
subnamespace, and brr did not gain unattended mutation of `main`.

Scheduled or proactive maintenance did not ship in this slice. The
initial proposal carried a broader first-class maintenance-task sketch,
but that was rejected as too much branch-targeting and push-behaviour
surface for the state-first pass. On 2026-05-17 the latency follow-up
reopened a narrower version: keep same-branch repair for task-caused
structural errors, but move warning/info grooming and broad compaction
out of the default task-completion hot path. That active redesign lives
in [`plan-kb-maintenance-latency.md`](plan-kb-maintenance-latency.md).

## Reading path

Read [`subject-kb.md`](subject-kb.md) for the current model, then this
page for what the state-first maintenance slice shipped. Use
[`plan-kb-maintenance-latency.md`](plan-kb-maintenance-latency.md)
only for the active follow-up around when brr should pay for an
additional LLM runner.
