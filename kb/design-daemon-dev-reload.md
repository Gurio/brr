# Design: developer reload for the brr daemon

Status: shipped on 2026-05-10

Developer reload is the brr self-development path for a long-running
foreground `brr up` process. It is intentionally narrow: an operator
who is hacking on brr installs the package in editable mode and opts
into quiescent daemon re-exec so source changes landed by an agent are
loaded before the next task.

This page hangs off the daemon subject hub,
[`subject-daemon.md`](subject-daemon.md). It was compressed on
2026-05-13 from proposal form into current-state synthesis because the
implementation and tests now carry the detailed behavior.

## Current shape

For brr self-development:

```bash
pip install -e ".[dev]"
brr up --dev-reload
```

`--dev-reload` watches brr's installed package directory for source and
package-data changes. The same behavior can be made persistent in a
self-development checkout with `dev_reload=true` in `.brr/config`.

When the watcher detects a change before the next task starts, the
daemon immediately re-execs itself. When the current task changes brr
package files, the daemon waits until the safe boundary has passed:
response captured, event terminal, environment finalized, kb
maintenance complete, and push attempted. It then re-execs before
claiming another event.

Reload is explicit rather than the default. Normal users, package
installs, and external supervisors can treat `brr up` as a stable
foreground process that exits only on signal or crash. Developers who
want source reload choose it with the CLI flag or config key.

## Implementation boundary

The watcher lives in [`dev_reload.py`](../src/brr/dev_reload.py). It
snapshots files under the installed package directory using stable
metadata such as relative path, size, and `st_mtime_ns`, with package
data that brr loads included alongside Python files. When the repo root
is discoverable, `pyproject.toml` is included so packaging metadata
changes still prompt a restart; the operator may still need to reinstall
after metadata or dependency changes.

[`daemon.start`](../src/brr/daemon.py) creates the watcher only when
`--dev-reload` or `dev_reload=true` is set. The daemon checks the watcher
at quiescent points: before claiming a task and after a task's finalize /
push path has completed.

Re-exec uses the current Python executable and argv through
`os.execve`, with `BRR_REEXEC=1` in the environment. Startup accepts the
existing PID file only for this self-reexec case, where the recorded PID
matches the current process. Duplicate-daemon protection remains strict
for every other startup.

Signals keep their normal meaning. Ctrl-C and `brr down` drain and stop;
they do not restart.

## Safety rules

- Agents do not get a chat command or task-level mechanism to restart
  the daemon.
- The daemon never restarts while a runner is active.
- Reload stays local and terminal-owned, not gate-owned.
- brr does not automate `pip install .`; mutating the operator's Python
  environment remains an explicit human action.
- The implementation replaces the process image instead of trying
  `importlib.reload()`, avoiding in-process module identity and thread
  hazards.

## Tests and source

Read:

- [`dev_reload.py`](../src/brr/dev_reload.py)
- [`daemon.py`](../src/brr/daemon.py)
- [developer reload tests](../tests/test_dev_reload.py)
- [daemon tests](../tests/test_daemon.py)

The tests cover watcher change detection, same-PID reexec startup,
strict rejection of other PID files, no reexec while `_run_worker` is
active, and post-task reexec after event status, finalize, kb
maintenance, and push hooks have run.

## Rejected alternatives

| Alternative | Why not |
| ----------- | ------- |
| Public `brr restart` | Broad product surface for a development-only pain, and it still would not solve non-editable installs. |
| Telegram/Slack "restart" command | Lets remote input control the process responsible for delivering that same remote response. |
| Agent writes `.brr/restart` marker | Puts lifecycle control in gitignored runtime scratch and invites agents to edit `.brr/`. |
| `importlib.reload()` | Fragile with threads, globals, and already-bound functions/classes. Re-exec is simpler. |
| systemd/launchd/brnrd supervisor now | The right layer for production uptime and fleet management, but too much ceremony for local brr self-development. |

## Operator workflow

For brr self-development, run the daemon from an editable install and
leave the terminal alone. After an agent lands source changes, the
daemon completes that task, pushes the result, notices the package tree
changed, and re-execs before processing the next event.

For normal brr users, nothing changes: install the package, configure a
gate, run `brr up`, stop it with `brr down` or Ctrl-C, and use an
external supervisor if always-on uptime is required.
