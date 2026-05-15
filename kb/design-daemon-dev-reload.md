# Design: developer reload for the brr daemon

Status: shipped on 2026-05-10

This page describes the shipped opt-in reload path for brr
self-development. It hangs off the daemon subject hub,
[`subject-daemon.md`](subject-daemon.md), and the live-run ergonomics
review,
[`research-runner-context-ergonomics-2026-05-09.md`](research-runner-context-ergonomics-2026-05-09.md).

## Current shape

Normal daemon lifecycle is still small: `brr up` starts the foreground
process, `brr down` or Ctrl-C requests drain-and-stop, and production
uptime belongs to an external supervisor. Reload is a development-only
option for brr's own checkout:

```bash
pip install -e ".[dev]"       # once per venv, or after packaging metadata changes
brr up --dev-reload           # opt-in brr-development mode
```

Operators can also set `dev_reload=true` in `.brr/config` for a brr
self-development repo where this is always wanted.

The watcher in [`dev_reload.py`](../src/brr/dev_reload.py) snapshots
brr package files by relative path, size, and `st_mtime_ns`. It covers
loaded package assets such as `.py`, `.md`, and `Dockerfile`, and
includes `pyproject.toml` when the repo root looks like the brr source
checkout. It is a cheap polling guard, not a full file-watching
subsystem.

The daemon creates the watcher only when `--dev-reload` or
`dev_reload=true` is active. It checks for changes before claiming the
next pending event and again after a task has completed response
capture, kb maintenance, env finalization, and the push attempt. A change
at either safe boundary re-execs the foreground process with the same
Python executable and argv, setting `BRR_REEXEC=1` so startup can accept
the existing PID file only when it belongs to the current process.

An editable install is still the important packaging boundary. With
`pip install -e ".[dev]"`, the new process imports `src/brr` from the
checkout and sees source changes that the completed task landed. A
normal `pip install .` imports copied files from `site-packages`, so
source-only checkout changes still require reinstalling before a restart
can help. Packaging metadata or dependency changes also remain an
operator install step.

## Boundaries

- Reload is explicit because replacing the process image is surprising
  in packaged installs, supervised deployments, or repos where the
  operator is not developing brr itself.
- There is no chat or task-file command that restarts the daemon; remote
  input should not control the process responsible for delivering that
  same response.
- The implementation re-execs the process rather than using
  `importlib.reload()`, avoiding live-thread and class-identity hazards.
- It does not install packages, mutate the operator's environment, or
  act as a production supervisor. systemd, launchd, Docker, tmux, and
  future `brnrd` supervision stay separate concerns.

## Test coverage

Focused tests cover:

- watcher detection for package-source and package-data changes;
- duplicate PID handling during `BRR_REEXEC`;
- strict duplicate-daemon rejection for unrelated PIDs;
- no re-exec while `_run_worker` is active;
- re-exec only after event status, finalization, kb maintenance, and
  push hooks have run;
- unchanged drain-and-stop behavior for `brr down` and Ctrl-C.

Older live Docker runner images used for brr self-work lacked Python,
pytest, and `rg` in some sessions. The bundled runner Dockerfile now
includes the baseline tools needed to run brr's normal dev install
inside the container, but verify against a freshly rebuilt image; stale
local `brr-runner:*` tags can still reproduce the old limitation noted in
[`research-runner-context-ergonomics-2026-05-09.md`](research-runner-context-ergonomics-2026-05-09.md).
