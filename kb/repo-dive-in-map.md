# Repo Dive-In Map

Compact current-state source map for the `brr` repository. Use it when
you need to know where a behavior lives before reading code. The page is
intentionally a map, not a second implementation manual; read the linked
source and tests for detail.

Lineage: the earlier full file-by-file walkthrough was compressed on
2026-05-17 after `kb_preflight` flagged it as oversized; deep history
lives in git.

## How to Use This Page

Read the orientation bullets first, then jump by symptom:

- Product / CLI surface: `README.md`, [`src/brr/cli.py`](../src/brr/cli.py).
- File protocol and task shape: [`protocol.py`](../src/brr/protocol.py),
  [`task.py`](../src/brr/task.py).
- Branch intent: [`branching.py`](../src/brr/branching.py),
  [`worktree.py`](../src/brr/worktree.py), and
  [`subject-tasks-branching.md`](subject-tasks-branching.md).
- Environments: [`envs/__init__.py`](../src/brr/envs/__init__.py) and
  [`subject-envs.md`](subject-envs.md).
- Daemon loop and progress: [`daemon.py`](../src/brr/daemon.py),
  [`updates.py`](../src/brr/updates.py),
  [`run_progress.py`](../src/brr/run_progress.py), and
  [`subject-daemon.md`](subject-daemon.md).
- Conversations: [`conversations.py`](../src/brr/conversations.py) and
  [`decision-drop-streams.md`](decision-drop-streams.md).
- Gate behavior: [`src/brr/gates/`](../src/brr/gates/) and
  [`src/brr/gates/README.md`](../src/brr/gates/README.md).
- Prompt assembly: [`prompts.py`](../src/brr/prompts.py),
  [`run_context.py`](../src/brr/run_context.py), and
  [`plan-agent-orientation-layering.md`](plan-agent-orientation-layering.md).
- KB shape: [`subject-kb.md`](subject-kb.md),
  [`decision-kb-shape.md`](decision-kb-shape.md), and
  [`AGENTS.md`](../AGENTS.md).

## Current Ownership Snapshot

- `AGENTS.md` is the universal contract every tool reads. The canonical
  copy lives at [`src/brr/AGENTS.md`](../src/brr/AGENTS.md) and is
  symlinked from the repo root.
- The public CLI is small: `init`, `run`, `auth`, `bind`, `setup`, `up`,
  and `down`. Older diagnostic commands such as `status` and `inspect`
  are intentionally absent.
- Gates create event files in `.brr/inbox/` and deliver response files
  from `.brr/responses/`.
- `Task.from_event` constructs tasks mechanically. There is no LLM triage
  step and no frontmatter-as-stdout response contract.
- The user-facing environment policy is
  `environment=<auto|host|worktree|docker>`. `auto` picks `docker` only
  when a Docker image is configured; otherwise it picks `worktree`.
  `host` is explicit-only.
- Task files persist the concrete backend as `env`. Legacy `env` and
  `default_env` remain accepted aliases for input config.
- Before branch planning, the daemon runs
  [`sync.refresh_before_task`](../src/brr/sync.py): one fetch plus
  best-effort ff-only refresh of the local default branch and any
  structured event branch.
- Branch planning is deterministic in [`branching.py`](../src/brr/branching.py):
  structured event branch fields first (`branch_target`, `target_branch`,
  `base_branch`, legacy `branch`), then `branch.fallback`.
- The agent owns runtime branching inside the selected environment.
  Worktree and Docker tasks start on `brr/<task-id>` from the resolved
  seed ref; leaving commits there lets brr fast-forward an auto-land
  target when one exists.
- The daemon runs a bounded worker pool (`max_workers=2` default,
  `max_workers=1` for serial behavior). Contention-free state is the
  design: task files, conversation jsonl files, gate progress cards,
  worktrees, and trace dirs are partitioned by task or event.
- Per-branch locks guard only the genuinely shared git refs: auto-land
  fast-forward and push.
- Conversations are routing/history, not identity. There is no manifest,
  title, intent, or status; durable meaning belongs in `kb/`.
- Live progress is a projection over conversation records. Gates receive
  `UpdatePacket`s and may implement `render_update`.
- Built-in gates are `telegram`, `slack`, and `github`. All three can
  render task progress; Telegram/Slack update chat messages, while
  GitHub creates/edits an issue or PR comment.
- GitHub triggers are label-on-issue, mention-in-comment, and `any`
  activity. PR and PR-comment events carry `branch_target` when the head
  branch can be resolved.
- The kb is persistent semantic memory. Runtime traces, tasks, responses,
  and raw conversation files stay under `.brr/`.

## One-Sentence Model

`brr` turns external messages into event files, constructs task files
mechanically, resolves branch intent and environment policy, runs a
configured AI CLI, records lifecycle state to a per-thread conversation
log, and delivers the captured stdout response through the originating
gate.

```text
gate -> event -> conversation -> task -> env -> runner -> response -> gate
```

## Source Routes

### Package Skin

Start here to understand how users enter the package:

- [`pyproject.toml`](../pyproject.toml)
- [`README.md`](../README.md)
- [`src/brr/__init__.py`](../src/brr/__init__.py)
- [`src/brr/__main__.py`](../src/brr/__main__.py)
- [`src/brr/cli.py`](../src/brr/cli.py)

Tests:

- [`tests/test_cli.py`](../tests/test_cli.py)

### File Protocol and Tasks

The primitive storage model lives here:

- [`src/brr/protocol.py`](../src/brr/protocol.py) reads/writes event and
  response Markdown files with restricted frontmatter.
- [`src/brr/config.py`](../src/brr/config.py) parses `.brr/config`.
- [`src/brr/task.py`](../src/brr/task.py) owns task construction,
  task-file persistence, environment policy resolution, and the
  `env`/`environment` alias.
- [`src/brr/gitops.py`](../src/brr/gitops.py) wraps repository detection,
  shared `.brr/` resolution, branch inspection, and basic git commands.
- [`src/brr/worktree.py`](../src/brr/worktree.py) creates and removes
  `.brr/worktrees/<task-id>/` worktrees on `brr/<task-id>` branches.

Key files:

- `.brr/inbox/<event-id>.md`
- `.brr/tasks/<task-id>.md`
- `.brr/responses/<event-id>.md`
- `.brr/traces/<task-id>-<label>/`

Tests:

- [`tests/test_protocol.py`](../tests/test_protocol.py)
- [`tests/test_config.py`](../tests/test_config.py)
- [`tests/test_task.py`](../tests/test_task.py)
- [`tests/test_gitops.py`](../tests/test_gitops.py)

### Branching and Freshness

Branch intent is resolved once per task before environment prep:

- [`src/brr/branching.py`](../src/brr/branching.py) defines `BranchPlan`
  and the structured branch-field priority.
- [`src/brr/sync.py`](../src/brr/sync.py) performs the pre-task fetch and
  ff-only refreshes that make seed refs current at task start.
- [`src/brr/forges.py`](../src/brr/forges.py) turns remotes into branch
  view URLs for `push_done` packets.

Design context:

- [`design-daemon-landing-branch.md`](design-daemon-landing-branch.md)
- [`design-git-layer-rework.md`](design-git-layer-rework.md)
- [`subject-tasks-branching.md`](subject-tasks-branching.md)

Tests:

- [`tests/test_branching.py`](../tests/test_branching.py)
- [`tests/test_sync.py`](../tests/test_sync.py)
- [`tests/test_forges.py`](../tests/test_forges.py)

### Environments and Runner Invocation

Environment backends implement `prepare -> invoke -> finalize`:

- [`src/brr/envs/__init__.py`](../src/brr/envs/__init__.py) ships the
  `host`, `worktree`, and `docker` backends.
- [`src/brr/runner.py`](../src/brr/runner.py) invokes the external AI
  CLI and captures stdout/traces.
- [`src/brr/run_context.py`](../src/brr/run_context.py) writes the
  recovery context file under `.brr/runs/<task-id>/context.md`.

Current backend shape:

- `host` runs in the main checkout and does not isolate writes.
- `worktree` creates an isolated git worktree and finalizes by
  fast-forwarding, preserving, or keeping scratch based on outcome.
- `docker` creates the same worktree first, then runs the runner in a
  container with credential passthrough, host UID, `HOME=/brr-home`, and
  git `safe.directory` wiring.
- Unknown backends raise `UnsupportedEnvironmentError`; `ssh`,
  `devcontainer`, and plugin dispatch are design material, not shipped
  code.

Tests:

- [`tests/test_envs.py`](../tests/test_envs.py)
- [`tests/test_runner.py`](../tests/test_runner.py)
- [`tests/test_dockerfile.py`](../tests/test_dockerfile.py)

### Conversations, Updates, and Progress

Conversation state is runtime history:

- [`src/brr/conversations.py`](../src/brr/conversations.py) stores
  `.brr/conversations/<safe-key>/<event-id>.jsonl`.
- [`src/brr/updates.py`](../src/brr/updates.py) defines `UpdatePacket`,
  `PACKET_TYPES`, persistence to conversations, and dispatch to gate
  `render_update` hooks.
- [`src/brr/run_progress.py`](../src/brr/run_progress.py) folds
  conversation records into `RunProgressView` for compact gate cards and
  expanded diagnostics.

Important details:

- Each event-pipeline jsonl has one writer. Readers merge files by `ts`
  for whole-conversation projections.
- `read_recent` tails across per-event files without reading every line
  when the caller asks for a short window.
- `records_for_task` currently filters the merged conversation records by
  `task_id`; `read_event_records` is the single-event helper when the
  caller already has `event_id`.
- `prompts.format_recent_conversation` filters ordinary daemon prompt
  context to semantic records: user events, task branch/status rows,
  final outcomes, and push summaries.

Tests:

- [`tests/test_conversations.py`](../tests/test_conversations.py)
- [`tests/test_run_progress.py`](../tests/test_run_progress.py)
- [`tests/test_daemon_conversations.py`](../tests/test_daemon_conversations.py)
- [`tests/test_daemon_progress_packets.py`](../tests/test_daemon_progress_packets.py)

### Daemon Loop

[`src/brr/daemon.py`](../src/brr/daemon.py) is the orchestration spine:

1. start configured gate threads;
2. scan `.brr/inbox/`;
3. mark events `processing`;
4. refresh refs with `sync.refresh_before_task`;
5. resolve `BranchPlan`;
6. create and persist `Task`;
7. append conversation task rows;
8. prepare the env backend;
9. write run context and build the daemon prompt;
10. invoke the runner with heartbeats;
11. write the response from captured stdout;
12. run kb preflight and optional maintenance after successful work;
13. finalize the environment under per-branch locks when needed;
14. mark the event terminal;
15. push the changed branch and emit delivery packets;
16. reap completed futures and, in dev-reload mode, re-exec only after
    the worker pool drains.

Design context:

- [`subject-daemon.md`](subject-daemon.md)
- [`design-concurrent-execution.md`](design-concurrent-execution.md)
- [`design-daemon-dev-reload.md`](design-daemon-dev-reload.md)

Tests:

- [`tests/test_daemon.py`](../tests/test_daemon.py)
- [`tests/test_dev_reload.py`](../tests/test_dev_reload.py)

### Gates and Operator Views

Gate modules live under [`src/brr/gates/`](../src/brr/gates/):

- [`telegram.py`](../src/brr/gates/telegram.py)
- [`slack.py`](../src/brr/gates/slack.py)
- [`github.py`](../src/brr/gates/github.py)

Gate contract:

- `auth(brr_dir)`, `bind(brr_dir)`, and optional `setup(brr_dir)` handle
  configuration.
- `poll(brr_dir, inbox_dir, responses_dir)` may create events and deliver
  completed responses.
- Optional `render_update(brr_dir, packet)` renders live progress from
  `RunProgressView`.

Current built-ins:

- Telegram and Slack poll chat APIs, create inbox events, deliver final
  responses, and update per-task progress messages.
- GitHub polls REST for label, mention, or `any` triggers; posts final
  responses as issue/PR comments; and creates/edits a progress comment for
  GitHub-sourced tasks.
- Per-task gate progress state lives at
  `.brr/gates/<gate>/progress/<task-id>.json`.

Tests:

- [`tests/test_telegram_gate.py`](../tests/test_telegram_gate.py)
- [`tests/test_github_gate.py`](../tests/test_github_gate.py)
- [`tests/test_gate_setup.py`](../tests/test_gate_setup.py)
- [`tests/test_telegram_render_update.py`](../tests/test_telegram_render_update.py)
- [`tests/test_slack_render_update.py`](../tests/test_slack_render_update.py)

### Prompts and KB Maintenance

Prompt and kb plumbing:

- [`src/brr/prompts.py`](../src/brr/prompts.py) assembles the run prompt,
  daemon Task Context Bundle, recent `kb/log.md` extract, and filtered
  conversation block.
- [`src/brr/prompts/run.md`](../src/brr/prompts/run.md) is the generic
  runner prompt template.
- [`src/brr/prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md)
  is the thin post-task redundancy pass.
- [`src/brr/kb_preflight.py`](../src/brr/kb_preflight.py) scans structural
  kb issues.
- [`src/brr/kb_health.py`](../src/brr/kb_health.py) computes graph stats.

Current daemon prompt shape:

- The Task Context Bundle opens with `### Mode` and is the hot path for
  daemon tasks.
- The generated run-context file is recovery detail.
- The injected recent-activity block plus the filtered recent-conversation
  block satisfies the AGENTS.md log-read startup step for daemon tasks.
- The kb-maintenance prompt receives task-touched kb pages, deterministic
  findings, and graph stats.

Tests:

- [`tests/test_prompts.py`](../tests/test_prompts.py)
- [`tests/test_kb_preflight.py`](../tests/test_kb_preflight.py)
- [`tests/test_kb_health.py`](../tests/test_kb_health.py)

## Runtime Invariants

- `.brr/` is runtime state and gitignored. Do not commit it.
- `kb/` is durable project knowledge. It describes current state, not a
  per-task transcript.
- `src/brr/docs/` is bundled user/tool documentation shipped with the
  package. `kb/` links to it instead of duplicating it.
- Runner success has multiple layers: subprocess result, required
  artifacts when configured, and response presence when a response path is
  part of the invocation.
- The runner's stdout is the user response. Agents do not manually write
  `.brr/responses/`.
- The daemon does not infer task identity from conversation history.
- Conversation logs are not workstreams. If an ongoing line of work needs
  a name, create or update a kb page.
- New live UX should add packet types in `updates.py`, project them in
  `run_progress.py`, and render through gate hooks.
- Kb consistency is a safety net: deterministic preflight plus an LLM
  redundancy pass when findings exist or task changes touch the kb.
- Troubleshooting is artifact-first: run context, task file, response,
  trace, conversation records, preserved worktree/container metadata.

## Design History to Read After Source

- [`decision-remove-triage.md`](decision-remove-triage.md) explains why
  mechanical task construction replaced LLM triage.
- [`decision-drop-streams.md`](decision-drop-streams.md) explains why
  conversations are routing/history rather than identity.
- [`decision-kb-shape.md`](decision-kb-shape.md) explains the current kb
  schema and maintenance model.
- [`design-env-interface.md`](design-env-interface.md) is the full env
  protocol design, including future backend ideas that are not all wired
  into current source.
- [`design-concurrent-execution.md`](design-concurrent-execution.md)
  records the accepted worker-pool and partitioned-state design.
- [`design-git-layer-rework.md`](design-git-layer-rework.md) covers the
  sync hook and GitHub gate direction.
- [`plan-agent-orientation-layering.md`](plan-agent-orientation-layering.md)
  explains the repository-contract / stage-overlay / runtime-packet /
  subject-knowledge layering model.

## Practical Navigator Notes

- If a page says "event", check `protocol.py`.
- If it says "task status" or "environment policy", check `task.py`.
- If it says "seed ref", "auto-land", or `branch_target`, check
  `branching.py`, `sync.py`, and `daemon.py`.
- If it says "conversation", check `conversations.py` first, then
  `run_progress.py` for projections.
- If it says `render_update`, check `updates.py` and the relevant gate.
- If it says "prompt", check `prompts.py` and the templates under
  `src/brr/prompts/`.
- If it says "daemon lifecycle", check `subject-daemon.md` before diving
  into `daemon.py`.
- If it says "environment", check `subject-envs.md`, `envs/__init__.py`,
  and the bundled env docs.
- If it says "kb consistency", check `subject-kb.md`, `kb_preflight.py`,
  `kb_health.py`, and `prompts/kb-maintenance.md`.

## Maintenance Rule

Update this page when any of these change:

- public CLI commands;
- event, task, response, conversation, or gate-progress file formats;
- shipped environment backends or environment config keys;
- branch-plan fields, fallback policy, or pre-task sync behavior;
- daemon worker-pool lifecycle, packet vocabulary, push/finalize flow, or
  dev-reload behavior;
- gate setup, trigger, delivery, or progress-rendering behavior;
- prompt-layer hot-path contracts;
- kb preflight, graph stats, or maintenance prompt contracts;
- subject hubs added, retired, or renamed.
