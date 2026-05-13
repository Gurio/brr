# Repo Dive-In Map

This page is a source-oriented navigator for the `brr` repository. It
is not the canonical synthesis for every subsystem; that job belongs
to the subject hubs linked below. Use this guide when you need to know
which files and tests to open, in what order, without losing the
cross-references between runtime concepts.

## Link Policy

Links are relative repository links. They work in GitHub, GitHub
mobile, local editors, and non-main branches without pinning the
reader to the wrong branch.

When this guide says "read source with tests", open the source file
first and the tests immediately after. The tests are often the most
compact statement of intended behavior.

## Current Shape

`brr` turns an external message into a frontmatter event file, appends
it to a gate-thread conversation log, builds a task mechanically,
resolves branch/environment policy, invokes a configured AI runner,
captures stdout as the response, runs kb maintenance when needed, and
delivers the response through the originating gate.

```text
gate -> event -> conversation -> task -> branch plan + env -> runner
     -> response -> kb maintenance/finalize/push -> gate
```

Carry these current-state facts while reading:

- [`AGENTS.md`](../src/brr/AGENTS.md) is the universal playbook
  schema. The repo root copy is a symlink; the canonical source lives
  in `src/brr/AGENTS.md`.
- Public CLI commands are `init`, `run`, `auth`, `bind`, `setup`,
  `up`, and `down`; older `status`, `inspect`, `streams`, `stream`,
  and `eject` commands are gone.
- `.brr/` is gitignored runtime state. `kb/` is committed project
  knowledge. `src/brr/docs/` is bundled tool documentation.
- Task construction is mechanical. There is no LLM triage call,
  `needs_context` status, task `branch` field, or response
  frontmatter contract; see
  [`decision-remove-triage.md`](decision-remove-triage.md).
- Conversation logs are routing/history, not workstream identity.
  They have no title, manifest, or intent; see
  [`decision-drop-streams.md`](decision-drop-streams.md).
- Environment policy is user-facing as
  `environment=<auto|host|worktree|docker>`. `auto` picks configured
  Docker first, otherwise `worktree`; `host` is explicit only. The
  legacy `env` / `default_env` inputs still resolve.
- The daemon resolves a thin [`BranchPlan`](../src/brr/branching.py)
  before env prep: a seed ref plus an optional auto-land target from
  structured event branch fields or `branch.fallback`. Free-text branch
  intent belongs to the worker agent inside the worktree.
- Worktree and Docker tasks start on `brr/<task-id>` from the seed
  ref. If an auto-land target exists and the agent leaves commits on
  the task branch, finalization fast-forwards it. Otherwise the branch
  is preserved for human routing.
- Built-in env backends are `host`, `worktree`, and `docker`.
  Resolver names for future backends such as `ssh` and `devcontainer`
  are accepted by the task model but `get_env()` rejects unavailable
  backends at execution time.
- Docker execution always uses a worktree, bind-mounts the repo, runs
  as the host UID, sets `HOME=/brr-home`, mounts known runner login
  directories by default, forwards known runner API keys plus
  `docker.env`, and injects git `safe.directory='*'`.
- Runner stdout is the response. Empty stdout on a response-bearing
  daemon invocation is the canonical retry signal.
- Gate progress cards are projections from lifecycle `UpdatePacket`s
  through [`run_progress.py`](../src/brr/run_progress.py). There is no
  local status module.
- KB consistency is deterministic preflight plus graph stats plus a
  thin LLM redundancy pass when findings exist or `kb/` changed. The
  schema lives in `AGENTS.md`, not in daemon-specific prompt prose.

## Reading Spine

Read in rings. Each ring gives enough context for the next one.

### Ring 0: Package Skin

Purpose: know how execution enters the package.

Read source with tests:

- [`pyproject.toml`](../pyproject.toml)
- [`README.md`](../README.md)
- [`src/brr/AGENTS.md`](../src/brr/AGENTS.md)
- [`src/brr/__init__.py`](../src/brr/__init__.py)
- [`src/brr/__main__.py`](../src/brr/__main__.py)
- [`src/brr/cli.py`](../src/brr/cli.py)
- [`tests/test_cli.py`](../tests/test_cli.py)
- [`tests/test_docs.py`](../tests/test_docs.py)

Key question: what public surface exists, and which old commands are
intentionally absent?

### Ring 1: Filesystem Atoms

Purpose: understand the low-level file and git contracts all higher
layers assume.

Read source with tests:

- [`src/brr/protocol.py`](../src/brr/protocol.py) with
  [`tests/test_protocol.py`](../tests/test_protocol.py)
- [`src/brr/config.py`](../src/brr/config.py) with
  [`tests/test_config.py`](../tests/test_config.py)
- [`src/brr/gitops.py`](../src/brr/gitops.py) and
  [`src/brr/worktree.py`](../src/brr/worktree.py) with
  [`tests/test_gitops.py`](../tests/test_gitops.py)

Key question: how do event/response files, `.brr/config`, shared
runtime directories, and linked worktrees behave?

### Ring 2: Runtime State

Purpose: learn the durable entities before the orchestration loop.

Read source with tests:

- [`src/brr/task.py`](../src/brr/task.py) with
  [`tests/test_task.py`](../tests/test_task.py)
- [`src/brr/branching.py`](../src/brr/branching.py) with
  [`tests/test_branching.py`](../tests/test_branching.py)
- [`src/brr/conversations.py`](../src/brr/conversations.py) with
  [`tests/test_conversations.py`](../tests/test_conversations.py)
- [`src/brr/updates.py`](../src/brr/updates.py) with
  [`tests/test_daemon_progress_packets.py`](../tests/test_daemon_progress_packets.py)
- [`src/brr/run_progress.py`](../src/brr/run_progress.py) with
  [`tests/test_run_progress.py`](../tests/test_run_progress.py)
- [`src/brr/run_context.py`](../src/brr/run_context.py) with
  daemon tests

Key question: which fields are persisted as task/conversation state,
and which facts are projections or prompt context only?

### Ring 3: Execution Contract

Purpose: understand the runner boundary and the chosen isolation
backend.

Read source with tests:

- [`src/brr/runner.py`](../src/brr/runner.py) with
  [`tests/test_runner.py`](../tests/test_runner.py)
- [`src/brr/prompts.py`](../src/brr/prompts.py) with
  [`tests/test_prompts.py`](../tests/test_prompts.py)
- [`src/brr/envs/__init__.py`](../src/brr/envs/__init__.py) with
  [`tests/test_envs.py`](../tests/test_envs.py)
- [`src/brr/Dockerfile`](../src/brr/Dockerfile) with
  [`tests/test_dockerfile.py`](../tests/test_dockerfile.py)
- [`src/brr/dev_reload.py`](../src/brr/dev_reload.py) with
  [`tests/test_dev_reload.py`](../tests/test_dev_reload.py)
- bundled prompt templates under [`src/brr/prompts/`](../src/brr/prompts/)

Key question: what does brr own around a runner invocation, and what
is delegated to the external AI CLI?

### Ring 4: Orchestration Spine

Purpose: read the event-to-response loop after the lower layers are
clear.

Read source with tests:

- [`src/brr/daemon.py`](../src/brr/daemon.py)
- [`tests/test_daemon.py`](../tests/test_daemon.py)
- [`tests/test_daemon_conversations.py`](../tests/test_daemon_conversations.py)
- [`tests/test_daemon_heartbeat.py`](../tests/test_daemon_heartbeat.py)
- [`tests/test_daemon_progress_packets.py`](../tests/test_daemon_progress_packets.py)

Read `_run_worker()` in lifecycle passes:

1. Receive a pending event and derive its conversation key.
2. Build and save a `Task` mechanically.
3. Resolve `BranchPlan` and concrete env backend.
4. Prepare the env and write the per-task run context.
5. Build the daemon prompt with recent conversation context.
6. Invoke the runner, retrying empty stdout when appropriate.
7. Write the plain-text response from stdout.
8. Run kb preflight/maintenance when findings or kb changes require it.
9. Finalize the env, including landing or preserving branches.
10. Push when configured and deliver through the gate.

Key question: which side effect happens before/after final response
capture, env finalization, kb maintenance, and push?

### Ring 5: Edges And Operator Views

Purpose: understand message ingress/egress, live progress, and human
debugging surfaces.

Read source with tests:

- [`src/brr/gates/__init__.py`](../src/brr/gates/__init__.py)
- [`src/brr/gates/README.md`](../src/brr/gates/README.md)
- [`src/brr/gates/telegram.py`](../src/brr/gates/telegram.py) with
  [`tests/test_telegram_gate.py`](../tests/test_telegram_gate.py) and
  [`tests/test_telegram_render_update.py`](../tests/test_telegram_render_update.py)
- [`src/brr/gates/slack.py`](../src/brr/gates/slack.py) with
  [`tests/test_slack_render_update.py`](../tests/test_slack_render_update.py)
- [`src/brr/gates/git_gate.py`](../src/brr/gates/git_gate.py)
- [`tests/test_gate_setup.py`](../tests/test_gate_setup.py)
- bundled docs under [`src/brr/docs/`](../src/brr/docs/)

Key question: what belongs in transport adapters, and what stays in
daemon/run-progress core?

## Entity Map

### Event

Source: [`protocol.py`](../src/brr/protocol.py).

Events are markdown files in `.brr/inbox/` with restricted
frontmatter plus body text. Gates create them, the daemon lists and
marks them terminal, and conversations record their arrival.

### Task

Source: [`task.py`](../src/brr/task.py).

Tasks are markdown files in `.brr/tasks/`. `Task.from_event()` copies
the instruction and selected metadata, resolves the concrete env, and
does not call an LLM. Runtime branch/worktree/response facts live in
`task.meta`.

### BranchPlan

Source: [`branching.py`](../src/brr/branching.py).

The branch plan is a pre-run safety record: `seed_ref`,
`auto_land_branch`, source, host context branch, and expected old OID.
It does not parse conversation history or free text; the agent handles
that inside the env.

### Conversation Log

Source: [`conversations.py`](../src/brr/conversations.py).

Conversation logs are `.brr/conversations/<safe-key>.ndjson`, one per
gate thread. Records include events, tasks, artifacts, and lifecycle
updates. Durable project memory belongs in `kb/`, not here.

### UpdatePacket And RunProgressView

Sources: [`updates.py`](../src/brr/updates.py) and
[`run_progress.py`](../src/brr/run_progress.py).

`UpdatePacket` is the lifecycle vocabulary. `RunProgressView` folds
packets into the compact status card Telegram and Slack render. New
live UX should extend this projection rather than deriving state again
inside each gate.

### RunnerInvocation And RunnerResult

Source: [`runner.py`](../src/brr/runner.py).

`RunnerInvocation` describes one external AI CLI call. `RunnerResult`
tracks subprocess exit, required artifact validation, response stdout,
and trace paths. `validation_ok` combines those layers.

### RunContext And EnvBackend

Source: [`envs/__init__.py`](../src/brr/envs/__init__.py).

`RunContext` carries host and environment paths, repo/runtime roots,
branch plan, branch name, and backend state. Each `EnvBackend`
implements `prepare`, `invoke`, and `finalize`.

### Gate Module

Source: [`gates/__init__.py`](../src/brr/gates/__init__.py).

Gates expose setup/auth/bind hooks, a daemon `run_loop`, and optional
`render_update`. They create events and deliver responses; they should
not reach into daemon internals for state.

## Module Cross-Reference

| Area | Main files | Primary tests |
| --- | --- | --- |
| CLI/bootstrap | [`cli.py`](../src/brr/cli.py), [`adopt.py`](../src/brr/adopt.py), [`__main__.py`](../src/brr/__main__.py) | [`test_cli.py`](../tests/test_cli.py), [`test_adopt.py`](../tests/test_adopt.py), [`test_integration.py`](../tests/test_integration.py) |
| File protocol/config | [`protocol.py`](../src/brr/protocol.py), [`config.py`](../src/brr/config.py) | [`test_protocol.py`](../tests/test_protocol.py), [`test_config.py`](../tests/test_config.py) |
| Git/worktrees | [`gitops.py`](../src/brr/gitops.py), [`worktree.py`](../src/brr/worktree.py), [`branching.py`](../src/brr/branching.py) | [`test_gitops.py`](../tests/test_gitops.py), [`test_branching.py`](../tests/test_branching.py) |
| Task/conversation state | [`task.py`](../src/brr/task.py), [`conversations.py`](../src/brr/conversations.py), [`updates.py`](../src/brr/updates.py), [`run_progress.py`](../src/brr/run_progress.py), [`run_context.py`](../src/brr/run_context.py) | [`test_task.py`](../tests/test_task.py), [`test_conversations.py`](../tests/test_conversations.py), [`test_run_progress.py`](../tests/test_run_progress.py), daemon progress tests |
| Runner/prompts | [`runner.py`](../src/brr/runner.py), [`prompts.py`](../src/brr/prompts.py), [`src/brr/prompts/`](../src/brr/prompts/) | [`test_runner.py`](../tests/test_runner.py), [`test_prompts.py`](../tests/test_prompts.py) |
| Environments | [`envs/__init__.py`](../src/brr/envs/__init__.py), [`Dockerfile`](../src/brr/Dockerfile), [`dev_reload.py`](../src/brr/dev_reload.py) | [`test_envs.py`](../tests/test_envs.py), [`test_dockerfile.py`](../tests/test_dockerfile.py), [`test_dev_reload.py`](../tests/test_dev_reload.py) |
| Daemon loop | [`daemon.py`](../src/brr/daemon.py) | [`test_daemon.py`](../tests/test_daemon.py), [`test_daemon_conversations.py`](../tests/test_daemon_conversations.py), [`test_daemon_heartbeat.py`](../tests/test_daemon_heartbeat.py), [`test_daemon_progress_packets.py`](../tests/test_daemon_progress_packets.py) |
| Gates | [`gates/`](../src/brr/gates/) | [`test_gate_setup.py`](../tests/test_gate_setup.py), Telegram/Slack gate tests |
| Bundled docs | [`docs/`](../src/brr/docs/) | [`test_docs.py`](../tests/test_docs.py) |
| KB maintenance | [`kb_preflight.py`](../src/brr/kb_preflight.py), [`kb_health.py`](../src/brr/kb_health.py), [`prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md) | [`test_kb_preflight.py`](../tests/test_kb_preflight.py), [`test_kb_health.py`](../tests/test_kb_health.py) |

## Runtime Invariants

- Runtime state is under `.brr/` and is not committed. This includes
  inbox, responses, tasks, runs, conversations, traces, gate state,
  preserved worktrees, prompt overrides, doc overrides, and config.
- Project knowledge is under `kb/` and is committed. Subject hubs
  describe current state; chronological narrative belongs in
  [`log.md`](log.md).
- Tool-level documentation ships under [`src/brr/docs/`](../src/brr/docs/)
  and can be overridden per repo under `.brr/docs/`; see
  [`decision-bundled-docs.md`](decision-bundled-docs.md).
- Runner success has three layers: subprocess exit, required artifacts
  when declared, and non-empty stdout when a response path is expected.
- Branching is finalized from actual git state. The daemon does not
  freeze a task-level branch strategy after prep.
- Responses are plain text. If work cannot be completed, the agent
  explains the blocker in its final stdout and the operator follows up
  in-thread.
- KB preflight handles deterministic structure: index coverage, stale
  links, broken links, size/status/revision advisories, hub-coverage
  hints, and shipped-page proposal scaffolding. Synthesis-heavy
  judgement stays in the LLM redundancy pass.

## Design Context

Read source first; then use these kb pages to understand why the
current shape exists.

Current subject hubs:

- [`subject-daemon.md`](subject-daemon.md) for `brr up`, gate/file
  protocol boundary, serial worker lifecycle, process control, and
  developer reload.
- [`subject-envs.md`](subject-envs.md) for the `EnvBackend` protocol,
  host/worktree/Docker behavior, salvage rules, and future env shape.
- [`subject-tasks-branching.md`](subject-tasks-branching.md) for
  mechanical task construction, branch intent, env resolution, and
  finalization.
- [`subject-kb.md`](subject-kb.md) for the kb graph, memory layers,
  lifecycle markers, and maintenance workflow.

Decisions and designs:

- [`decision-remove-triage.md`](decision-remove-triage.md),
  [`decision-drop-streams.md`](decision-drop-streams.md), and
  [`decision-kb-shape.md`](decision-kb-shape.md) are the main "drop
  the noisy abstraction" sequence.
- [`design-daemon-landing-branch.md`](design-daemon-landing-branch.md)
  and
  [`research-branch-plan-simplification-2026-05-12.md`](research-branch-plan-simplification-2026-05-12.md)
  explain the current deterministic branch-plan contract.
- [`design-env-interface.md`](design-env-interface.md) is the accepted
  env protocol spec; [`plan-concurrent-worktrees.md`](plan-concurrent-worktrees.md)
  is the shipped predecessor that explains the one-task-per-worktree
  slice and abandoned merge coordinator path.
- [`design-daemon-dev-reload.md`](design-daemon-dev-reload.md)
  explains the shipped opt-in reload mode for brr self-development.
- [`plan-branch-modes.md`](plan-branch-modes.md) is historical context
  for branch/env as task properties and the reversals that followed.
- [`decision-bundled-docs.md`](decision-bundled-docs.md) explains
  why package docs live under `src/brr/docs/`.

Paused or strategic material:

- [`deck-brr-fleet-steering.md`](deck-brr-fleet-steering.md),
  [`plan-overlays.md`](plan-overlays.md), and
  [`notes-pondering-fleet.md`](notes-pondering-fleet.md) cover the
  paused fleet/overlays/brnrd framing. Treat the env axis as the live
  strand and overlays/brnrd as parked.
- [`research-brr-vs-gh-aw.md`](research-brr-vs-gh-aw.md) compares brr
  with GitHub Agentic Workflows.
- [`research-runner-context-ergonomics-2026-05-09.md`](research-runner-context-ergonomics-2026-05-09.md)
  is a point-in-time review of daemon-run context ergonomics.
- [`plan-kb-state-first-maintenance.md`](plan-kb-state-first-maintenance.md)
  tracks active kb grooming work around current-state synthesis and
  first-class maintenance tasks.
- [`llm-wiki.md`](llm-wiki.md) is the external framing source for the
  wiki/synthesis layer.

## Practical Navigator Notes

- Event files, frontmatter parsing, response files: start at
  [`protocol.py`](../src/brr/protocol.py).
- Environment policy or task status: start at
  [`task.py`](../src/brr/task.py), then
  [`envs/__init__.py`](../src/brr/envs/__init__.py).
- Branch seed/auto-land behavior: start at
  [`branching.py`](../src/brr/branching.py), then worktree finalization
  in [`envs/__init__.py`](../src/brr/envs/__init__.py).
- Gate-thread continuity: start at
  [`conversations.py`](../src/brr/conversations.py).
- Progress packets or remote cards: start at
  [`updates.py`](../src/brr/updates.py) and
  [`run_progress.py`](../src/brr/run_progress.py).
- Prompt assembly, Task Context Bundle, recent conversation injection,
  and kb maintenance prompts: start at
  [`prompts.py`](../src/brr/prompts.py).
- Subprocess execution, runner detection, response capture, and traces:
  start at [`runner.py`](../src/brr/runner.py).
- Process lifecycle, PID files, daemon drain/stop, and reload: start
  with [`subject-daemon.md`](subject-daemon.md), then
  [`daemon.py`](../src/brr/daemon.py) and
  [`dev_reload.py`](../src/brr/dev_reload.py).
- KB consistency and graph stats: start at
  [`kb_preflight.py`](../src/brr/kb_preflight.py),
  [`kb_health.py`](../src/brr/kb_health.py), and
  [`AGENTS.md`](../src/brr/AGENTS.md).
- Transport, auth, polling, response delivery, and live gate cards:
  start at [`src/brr/gates/`](../src/brr/gates/).

## Maintenance

Update this page only when a source boundary or reading route changes:
public CLI commands, file formats, env backends, daemon lifecycle,
runner response/artifact contract, gate hook surface, bundled-docs vs
kb ownership, kb consistency contract, major module boundaries,
subject hubs, or test files that become the best behavioral reference.

For deeper subsystem knowledge, update the relevant subject hub instead
of growing this page into a second canonical spec.

Lineage: on 2026-05-13 this page was compressed from a detailed
file-by-file chronicle into the current-state navigator above because
the kb preflight flagged it as oversized. Current subsystem synthesis
now lives in the subject hubs
([daemon](subject-daemon.md), [envs](subject-envs.md),
[tasks/branching](subject-tasks-branching.md), [kb](subject-kb.md));
the removed detail remains available in git history.
