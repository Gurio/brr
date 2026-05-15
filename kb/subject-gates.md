# Subject: gates

Gates are brr's transport adapters. They are deliberately thin: a gate
turns some external stimulus into a file under `.brr/inbox/`, and may
deliver `.brr/responses/` back to the same surface. The daemon owns task
construction, environment prep, progress packets, finalization, and push;
gates should not grow private daemon logic.

The common contract lives in the bundled
[`gates/README.md`](../src/brr/gates/README.md). A daemon-thread gate
implements `is_configured(brr_dir)` and
`run_loop(brr_dir, inbox_dir, responses_dir)`. CLI setup is optional but,
when present, uses `setup(brr_dir)` as the one-step path with `auth` /
`bind` retained for split setup.

## Built-ins

- `git.py` is enabled by default because it needs no credentials. Its
  default mode watches `tasks/` on the repo's default branch and emits one
  event per new or modified task file. It reads legacy
  `.brr/gates/git_gate.json` state but writes `.brr/gates/git.json`.
- `telegram.py` and `slack.py` are explicit setup gates because they need
  credentials and a destination channel or chat. They poll their APIs for
  incoming messages and deliver the final response back to the thread.
- Scripts and third-party gates can bypass Python entirely as long as they
  write the same inbox files and, if they deliver responses themselves,
  read the matching response file.

## Progress rendering

Progress UX is gate-optional and flows through `updates.emit()` plus the
`RunProgressView` projection. Telegram and Slack implement
`render_update()` and maintain one live card per task, editing it as
packets arrive. Git intentionally does not render live progress: a git
remote is a poor chat surface, and the durable result is the commit/branch
that the daemon pushes after the task.

New progress UI should extend `run_progress.py` first, then let gates render
the projection in their own markup. Do not rebuild task state by reading
conversation logs inside a gate.

## Git versus forge sources

Pure Git can reliably provide refs and file contents. It cannot provide
portable PR, issue, review-comment, label, permission, or notification
semantics because those belong to forges such as GitHub, GitLab, Bitbucket,
Gitea, and Forgejo. The current `forges.py` layer is therefore intentionally
view-only: it derives branch URLs after a successful push but does not try
to make provider actions generic.

The live git gate direction is captured in
[`design-git-gate.md`](design-git-gate.md): keep the default credential-free
and task-file-shaped, add opt-in repository-change automation later if the
operator explicitly accepts the token cost, and treat PR/issues as
provider-aware forge gates or post-task hooks rather than as generic Git.

## Read next

- [`repo-dive-in-map.md`](repo-dive-in-map.md) Ring 5 for the source reading
  route through the built-in gates.
- [`subject-daemon.md`](subject-daemon.md) for the foreground process and
  gate/file-protocol boundary.
- [`design-git-gate.md`](design-git-gate.md) for the current git gate design
  direction and rejected default shapes.
