# Plan: state-first kb maintenance and regular grooming

Status: shipped on 2026-05-13

This page is a shipped receipt, not the live spec. The current kb
contract is synthesised in [`subject-kb.md`](subject-kb.md), decided in
[`decision-kb-shape.md`](decision-kb-shape.md), and implemented across
[`AGENTS.md`](../AGENTS.md),
[`src/brr/kb_preflight.py`](../src/brr/kb_preflight.py),
[`src/brr/kb_health.py`](../src/brr/kb_health.py),
[`src/brr/prompts.py`](../src/brr/prompts.py), and
[`daemon._maybe_kb_maintenance`](../src/brr/daemon.py).

Lineage: shipped on 2026-05-13 by making state-first maintenance part
of the universal schema, adding deterministic advisory signals and graph
stats to the maintenance prompt, and making inline kb-maintenance edits
durable and visible. Earlier drafts proposed scheduled/proactive
maintenance tasks; that strand was rejected because unattended branch
targeting and push behaviour added more daemon policy than the problem
needed.

## Current outcome

The plan landed five durable changes:

- The universal schema now says kb pages are current-state synthesis.
  Subject hubs, decisions, and designs describe what is true now; a
  short lineage breadcrumb captures load-bearing changes; deep history
  lives in `git log` and [`kb/log.md`](log.md).
- `prompts._read_recent_log` uses a byte budget plus an entry-count
  ceiling, so one verbose log entry can no longer dominate every daemon
  prompt's recent-activity block.
- `kb_preflight.scan` reports structural errors and advisory findings:
  `oversized-page`, `missing-status-marker`,
  `revision-history-heavy`, and `recent-log-budget-exceeded`.
- `kb_health.compute_graph_stats` adds graph topology context to the
  maintenance prompt: page counts, kinds, largest pages, peer-orphan
  candidates, and log shape.
- `_maybe_kb_maintenance` still runs inline after a daemon task when kb
  pages changed or preflight found something, but edits are no longer a
  hidden best effort. The maintenance prompt asks the runner to commit;
  if allowed kb / AGENTS edits are left uncommitted after the runner exits,
  the daemon rolls them into an automated `brr maintenance` commit on the
  current task branch and emits `kb_maintenance_done` so response cards
  show `maintenance: N kb commits` or `maintenance: clean`.

## Policy carried forward

| Page kind | Current-state rule | Historical breadcrumb |
| --- | --- | --- |
| Subject hub | Canonical state of the area today. Avoid revision logs and old implementation tours. | One compact lineage paragraph linking to current decisions, log entries, or `git log -- <path>`. |
| Decision | Current accepted decision and the reasoning still needed to understand it. If reversed, mark superseded and point at the successor. | Keep the key alternatives and why the chosen path won. Do not keep every later implementation delta inline. |
| Plan/design | Active pages describe intended work. Shipped pages become receipts only when their reasoning is still useful. | If the useful knowledge has moved to a subject hub, mark the page shipped/superseded and compress or delete it. |
| Research | Point-in-time findings. Keep when they answer a reusable question; delete when absorbed and no longer useful. | Link to the subject or decision that absorbed it. |
| Log | Chronological narrative, not a design database. | Keep entries short enough to be prompt context; deep detail belongs in the committed page or git diff. |

The practical test is whether a cold reader can open the index, the
relevant subject hub, and recent log context without spending most of
their prompt on superseded implementation history. Pages that describe
live areas should open with current shape, not revision narrative.

## Deferred or rejected

- **Scheduled/proactive maintenance tasks** were rejected for now. Inline
  maintenance plus explicit daemon visibility solved the immediate
  "cleanup edits disappear" problem without adding unattended internal
  events, maintenance branch policy, or push routing.
- **External hooks** remain deferred. Cursor and direct CLI sessions
  still rely on [`AGENTS.md`](../AGENTS.md); a future pre-commit hook or
  tool-specific recipe can reuse `kb_preflight` without changing the
  policy layer.
- **History depth in decisions** remains a judgement call. Keep
  rationale and rejected alternatives that still constrain future work;
  move detailed implementation evolution to git/log breadcrumbs.
- **A `brr kb` CLI namespace** remains rejected by
  [`subject-kb.md`](subject-kb.md). Agent-facing maintenance goes through
  prompt injection and scanner output, not user-facing command sprawl.

## Verification

The shipped source shape to check when this page drifts:

- [`src/brr/prompts.py`](../src/brr/prompts.py) for recent-log budgeting
  and Task Context Bundle assembly.
- [`src/brr/kb_preflight.py`](../src/brr/kb_preflight.py) for structural
  and advisory findings.
- [`src/brr/kb_health.py`](../src/brr/kb_health.py) for graph statistics.
- [`daemon._maybe_kb_maintenance`](../src/brr/daemon.py) and
  `_commit_kb_maintenance_edits` for inline pass triggering, automated
  commit fallback, and `kb_maintenance_done` packets.
- [`tests/test_kb_preflight.py`](../tests/test_kb_preflight.py),
  [`tests/test_run_progress.py`](../tests/test_run_progress.py), and the
  daemon maintenance tests for regression coverage.
