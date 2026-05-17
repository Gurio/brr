# Plan: low-latency kb maintenance

Status: active

This plan revisits the shipped
[`plan-kb-state-first-maintenance.md`](plan-kb-state-first-maintenance.md)
shape from the latency side. The state-first schema, deterministic
scan, graph stats, and visible maintenance commits still hold. The
part under redesign is *when* brr pays for an additional LLM runner.

## Current implemented shape

The daemon currently handles kb maintenance after a successful task in
this order:

1. the main runner writes the user-visible response;
2. the daemon records the response and marks the task done;
3. `_maybe_kb_maintenance` runs before environment finalization and
   branch push;
4. if the maintenance runner leaves kb edits behind, the daemon rolls
   them into a `brr maintenance <brr-maintenance@brr.local>` commit on
   the same task branch;
5. the progress card surfaces `maintenance: clean` or
   `maintenance: N kb commits`.

Under the default `kb_maintenance=auto`, the second runner is invoked
when `kb/` changed or when `kb_preflight.scan` returns any finding.
That includes advisory findings, not only structural errors. As of
2026-05-17, this repo has a persistent `oversized-page` warning for
`repo-dive-in-map.md`, so the current code can pay the second-runner
cost on every successful daemon task even when the task did not touch
the kb.

The attached-commit property is valuable: when grooming follows the
task on the same branch, the operator reviews one branch and one PR
rather than chasing a separate cleanup change. The problem is that the
same mechanism is being used for two different jobs:

- **repair the task's kb breakage** before the branch is handed back;
- **groom the repo's broader kb** when pages have become too large,
  stale, or over-historical.

Those jobs have different latency budgets.

## Goals

- Keep the hot path fast for ordinary implementation and small
  research tasks.
- Preserve same-branch, attached cleanup for kb problems introduced by
  the task that just ran.
- Keep broad semantic grooming possible: compaction, reference
  reconciliation, current-state rewrites, and lifecycle cleanup.
- Avoid hidden background mutation of `main`.
- Keep AGENTS.md as the primary cross-tool schema; brr's daemon hook is
  a safety mechanism, not the only maintenance path.
- Make strict maintenance opt-in for operators who prefer slower
  completion over deferred cleanup.

## Alternatives

| Alternative | What it optimizes | Where it fails |
| --- | --- | --- |
| Keep the current inline post-task LLM pass | Same-branch cleanup, one review surface, simple implementation | A warning anywhere in the kb can tax every task; clean kb-writing tasks still pay a second cold start; the pass duplicates work the main agent should already have done |
| Inline deterministic scan only | Fastest hot path; structural checks are cheap and reliable | No semantic compaction; references and current-state drift depend entirely on the main agent noticing them |
| Inline LLM only for hard structural errors | Keeps attached repair for broken links, missing index entries, and similar branch-breaking issues | Advisory cleanup needs another path; persistent pre-existing errors need debouncing so unrelated tasks are not taxed forever |
| Inline diff-scoped LLM for every kb-touching task | Keeps the review attached to the task that changed kb files | Still doubles latency for the small research tasks that most often write kb material; the main agent already has the freshest context |
| Deferred first-class maintenance task | Expensive grooming runs through the normal task/branch/commit path without blocking the original task | Cleanup may be reviewed separately from the change that motivated it; branch targeting and duplicate suppression need explicit state |
| Asynchronous same-branch post-task maintenance | Preserves the attached branch while letting the user response return sooner | Harder branch lifecycle: the branch may be pushed and reviewed before cleanup lands; concurrent updates to the same branch need locking and clear progress UX |
| Manual-only maintenance | No surprise runtime cost and no daemon scheduler surface | The kb will drift unless operators remember to ask; this undercuts the point of LLM-maintained project memory |

## Recommended shape

Split maintenance into two lanes.

### Lane 1: hot-path repair

Keep the deterministic scan after every successful task, but make the
default LLM trigger severity- and diff-aware:

- "Task-caused" should be based on finding fingerprints compared to a
  pre-task scan captured before the main runner starts. If that
  baseline is unavailable during the first implementation slice, fall
  back to `task_touched` target matching and the debounced
  maintenance-due state below.
- `error` findings caused by a task that changed `kb/`, `AGENTS.md`, or
  `src/brr/AGENTS.md` trigger the inline maintenance runner on the same
  branch.
- `warning` and `info` findings do not trigger the inline runner under
  `kb_maintenance=auto`; they become deferred grooming signals.
- `kb_changed` alone does not trigger the inline runner. The main agent
  is already responsible for maintaining the kb it writes, and a clean
  deterministic scan is enough for the hot path.
- `kb_maintenance=always` preserves today's strict behaviour for
  operators who want a second LLM pass after every task.
- A compatibility policy such as `kb_maintenance=attached` can preserve
  the current "run when kb changed or any finding exists" behaviour if
  that proves useful during transition.

The important line is: a clean kb-writing task should not pay for a
second LLM just because it wrote kb material.

Pre-existing hard errors should not tax unrelated user tasks forever.
The daemon should either record them as maintenance-due state or run a
single debounced repair attempt, then avoid repeating the same failed
maintenance run until the repo advances or the finding fingerprint
changes.

### Lane 2: deferred grooming

Treat warning/info findings and broad compaction as maintenance backlog,
not task finalization work.

The daemon should maintain a small runtime state file under `.brr/`
recording:

- the latest scan commit;
- finding fingerprints, severities, first-seen and last-seen times;
- whether a maintenance task is already pending or running;
- the last maintenance result.

When the daemon is quiescent and maintenance is enabled, it can enqueue
a normal internal task with `source=brr-maintenance`. That task uses a
repo-maintenance prompt, receives the findings and graph stats, commits
like any other task, and is preserved/pushed like any other brr branch.
No autoland by default.

This reopens the "first-class maintenance task" idea, but in a narrower
form than the rejected scheduled job from the state-first plan:

- default off or conservative for adopters;
- idle-only, never ahead of user work;
- driven by deterministic backlog, not by a blind calendar;
- normal branch and commit discipline;
- no hidden mutation of `main`.

For this repo, opting in early is reasonable because the kb is part of
the product design loop and the maintenance behaviour itself needs a
proving ground.

## Why not keep every cleanup attached?

Attached post-task cleanup is strongest when the cleanup repairs the
task's own branch. A missing index link introduced by a research task
belongs on that branch; the operator should see the fix beside the
research artifact.

Broad grooming is different. Compressing `repo-dive-in-map.md`, merging
old design notes, or reconciling sibling subject hubs is usually global
repo hygiene. Attaching that work to an unrelated bug fix only makes the
review larger and slower. The review attachment is worth preserving for
branch-local repair, not for every advisory the scanner knows about.

## Implementation plan

1. Split preflight findings by severity in `_maybe_kb_maintenance`, and
   add a pre-task finding baseline (or an equivalent stored fingerprint
   comparison) so the daemon can distinguish new branch-local errors
   from old repo backlog. Under `auto`, inline LLM maintenance should
   run for task-caused structural errors, not for `warning` / `info`
   findings and not for `kb_changed` alone.
2. Add a debounced maintenance-due record for findings that do not run
   inline. This can start as runtime-only state; no committed kb page is
   needed for transient scanner fingerprints.
3. Update progress/card wording so skipped advisory grooming is visible
   without becoming noise. A verbose view can show finding counts; the
   compact card should stay quiet unless maintenance actually ran or a
   hard error was deferred.
4. Add a first-class repo-maintenance prompt and daemon enqueue path,
   gated by conservative config such as `maintenance.enabled=false`,
   `maintenance.interval_days=7`, and `maintenance.idle_only=true`.
5. Keep `kb_maintenance=always` as the escape hatch for strict
   same-branch grooming, and optionally add `kb_maintenance=attached`
   for the current policy during migration.
6. Update bundled docs and tests around the new trigger semantics:
   clean kb changes skip the LLM pass; warning-only scans skip the LLM
   pass; task-caused structural errors still run inline; `always`
   still runs.

## Acceptance criteria

- A small research task that writes a valid kb page completes after the
  main runner plus the cheap deterministic scan; no second runner starts
  under default config.
- The existing `repo-dive-in-map.md` oversized-page warning does not
  make every daemon task run kb maintenance.
- A task that introduces a broken kb link or missing index entry still
  gets same-branch repair before finalization.
- Operators can choose strict attached grooming with configuration
  rather than accepting it as the default latency cost.
- Broad compaction remains available as a normal reviewable branch,
  not as hidden background mutation.
