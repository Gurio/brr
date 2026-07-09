# Execution environments

How brr places a runner invocation: where the agent's working directory
lives, how isolation is achieved, and how credentials reach the runner.

## At a glance

| Env         | Where the runner runs                       | Credentials       | Repo isolation                | Notes                                |
| ----------- | ------------------------------------------- | ----------------- | ----------------------------- | ------------------------------------ |
| `host`      | Main repo checkout, current process         | Inherited         | None                          | Default for trivial / Q&A runs       |
| `worktree`  | `.brr/worktrees/<run-id>/` (`brr/<run-id>` branch) | Inherited | Working dir + branch | Default for code work |
| `docker`    | A container, worktree bind-mounted          | Auto-wired to host| Container + worktree          | Bundled image includes brr + common dev tools |

Other envs (`devcontainer`, `ssh`) are planned but not yet shipped.

## Picking an env

Resolution order in `.brr/config`:

1. `environment=` — the setting you configure.
2. `env=` / `default_env=` — legacy aliases, still accepted.
3. `auto` — the daemon picks: docker if `docker.image` is set and
   Docker is on `PATH`, otherwise worktree. `host` is never auto-picked;
   set it explicitly if you want to forgo isolation.

The env is resolved deterministically when the run manifest is built —
there's no LLM in the loop. If a request needs different isolation,
change `.brr/config` or wire your gate to set `env=` on the event.

## `host`

The runner runs in the main checkout, in the daemon's process. There is
no isolation; uncommitted edits land directly in your working tree.
Pick this for read-only tasks (Q&A, review, research) and one-off fixes
where you want the change visible immediately.

## `worktree`

The daemon creates a git worktree under `.brr/worktrees/<run-id>/`
on a fresh `brr/<run-id>` branch sprouted from the resolved seed ref.
The runner's working directory points at the worktree; your main
checkout is untouched. After a successful run, the daemon inspects the
worktree's git state and records one of four outcomes:

- `ready` — the agent committed on a branch. That branch gets pushed;
  the worktree is torn down unless it carries uncommitted leftovers.
- `nothing` — no commits beyond the seed ref. The empty run branch and
  worktree are deleted; nothing is published.
- `detached` — the agent left `HEAD` detached. The worktree is kept so
  you can recover the commits.
- `conflict` — the push itself failed, so the gate renders the delivery
  failure instead of celebrating a successful run.

This is the right default for code-modifying work. Worktrees that end
up in a non-clean state (failures, conflicts, or untracked files left
behind) are kept automatically so you can inspect what the agent did.

## `docker`

The runner command is wrapped in `docker run`. The repo is bind-mounted
into the container at the same absolute path it has on the host, so
file references in prompts and traces remain valid in both directions.
Docker runs first set up the same `brr/<run-id>` worktree as the
`worktree` env and mount that directory instead of the main checkout,
keeping the host's working tree clean.

### Required configuration

```ini
default_env=docker
docker.image=ghcr.io/example/your-image:tag
```

That's it for required keys. Everything else is automatic or has a
sensible default.

### Credentials are wired automatically

Two paths cover both API-key and subscription-only auth:

1. **Env-var pass-through.** When set on the daemon's environment, brr
   forwards `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`,
   `GOOGLE_API_KEY`, `GITHUB_TOKEN`, and `GH_TOKEN` into the container.
   Add more with `docker.env=KEY1,KEY2`.
2. **Login-dir bind mounts.** When `~/.claude/`, `~/.claude.json`,
   `~/.codex/`, `~/.gemini/`, or `~/.gitconfig` exists on the host,
   it's bind-mounted read-write into the matching path under `$HOME`
   inside the container. This is what makes Claude Pro/Max, ChatGPT
   Plus/Pro, and Gemini OAuth users work without an API key, and gives
   `git commit` your real author identity.

**GitHub auth is handled separately.** `~/.config/gh/` on Linux
typically only stores the account name on disk — the OAuth token lives
in the system keyring, which isn't reachable inside a container.
Instead, brr resolves a token explicitly on every Docker task (stored
gate state → `GITHUB_TOKEN`/`GH_TOKEN` → `gh auth token` on the host)
and injects it as `GITHUB_TOKEN` inside the container, plus git config
that rewrites GitHub SSH remotes to HTTPS with a token-backed credential
helper. Net effect: `gh pr create`, `gh api`, and HTTPS `git push` all
work cleanly inside the container.

If `gh auth token` can't return a token on the host, set `GITHUB_TOKEN`
in the daemon's environment, or run the GitHub gate's `setup` flow to
store one explicitly. A Personal Access Token with `repo` and
`read:org` is sufficient for most workflows.

Opt out of the credential-dir mounts with `docker.mount_credentials=false`.
The mounts are read-write, so refresh tokens written inside the
container land back on the host.

### File ownership inside the container

The container runs as the **host user's UID** (`-u "$(id -u):$(id -g)"`,
`-e HOME=/brr-home`), and the bundled image bakes a writable `/brr-home`
so any UID can use it as `HOME`. There's no root-owned residue to clean
up after the daemon runs, and brr sets `safe.directory='*'` via git's
`GIT_CONFIG_*` env vars so the agent can operate on the bind-mounted
repo without per-image configuration (working around
[CVE-2022-24765](https://github.com/git/git/security/advisories/GHSA-vw2c-22j4-2fh2)).

### Runtime knobs

| Key                           | Default      | Purpose                                              |
| ------------------------------ | ------------ | ----------------------------------------------------- |
| `docker.image`                | required     | Image reference passed to `docker run`               |
| `docker.network`              | `bridge`     | `--network` argument                                 |
| `docker.env`                  | empty        | Comma-separated extra env-var names to pass through  |
| `docker.mount_credentials`    | `true`       | Mount `~/.{claude,codex,gemini}` when present        |

### Image expectations

The image must:

- Have your configured runner CLI on `PATH` (`claude`, `codex`,
  `gemini`, or whatever you set `runner=` to).
- Have `git` available — the agent commits inside the container.
- Accept being run as an arbitrary UID. Custom images that hard-code
  `USER root` and write tokens to `/root/...` won't see the credential
  mounts — follow the bundled image's `/brr-home` pattern or build with
  the same `HOME` the daemon expects.

It does *not* need an API key or a `safe.directory` config baked in —
brr wires both at run time.

### Minimum viable image

Any image with `git` and one runner CLI works. For example, the
smallest Claude-only image:

```dockerfile
FROM node:22-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g @anthropic-ai/claude-code
```

Build with `docker build -t my-brr-runner .` and set
`docker.image=my-brr-runner`. Swap the last line for `@openai/codex` or
`@google/gemini-cli` for the other runners.

### Layering project tooling

Project-specific tooling belongs *on top of* the runner image — repo
dependencies, service CLIs, databases, browser drivers, pinned test
tools:

```dockerfile
FROM brr-runner:local
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install -e ".[dev]"
```

### Container lifecycle

| Outcome              | Container is...                                          |
| --------------------- | ---------------------------------------------------------- |
| `done`                | Removed (`docker rm -f`)                                  |
| `error` / `conflict` | Preserved (name recorded in run metadata)                 |

Same rule as worktrees: clean teardown only on a successful run.
Failures preserve the container so you can inspect, re-run, or copy
work out manually.

## Durability contract

Across all envs, brr only guarantees three kinds of output survive:

1. **Git commits** on whatever branch the agent left checked out,
   reachable from the host's `.git`.
2. **The response file** at `.brr/responses/<event-id>.md`, captured
   from the runner's stdout.
3. **Trace artefacts** under `.brr/traces/<kind>/...`, kept on
   `error`/`conflict` and removed on a clean `done` — on a successful
   run the durable record is the commit + response file, and the trace
   would only repeat that.

Anything else an agent writes (untracked files, ephemeral container
state) is **not durable**. The corresponding scratch space is torn down
on a clean success, and preserved on `error`/`conflict` — or when a
worktree has untracked/unstaged files at finalize time, regardless of
status — so you can recover work.

## Troubleshooting

- **`docker env requires docker.image in .brr/config`** — set
  `docker.image=` to a built or pulled image reference.
- **`fatal: detected dubious ownership in repository`** — should not
  appear with a recent brr; if it does, your container's git is older
  than 2.31 or strips `GIT_CONFIG_*` env vars. Update git in the image
  or add `RUN git config --system --add safe.directory '*'` to the
  Dockerfile.
- **Runner exits with auth error inside container** — confirm the
  matching `~/.<runner>/` exists on host (for subscription auth) or the
  corresponding `*_API_KEY` is exported in the daemon's environment.
- **File ownership leaked to root on host** — you're likely on a stale
  image; rebuild from the current bundled Dockerfile (`brnrd init -i`).
  One-shot recovery while rebuilding:
  `sudo chown -R "$(id -un):$(id -gn)" .git`.
- **Credentials not picked up inside the container** — confirm the
  matching `~/.<runner>/` exists on host *and* the image runs with
  `HOME=/brr-home`. Custom images that hard-code `USER root` won't see
  the mounts.

## Next

- [CLI reference](cli.md) for the `environment=` config key and the
  other `.brr/config` settings.
- [Self-hosting brnrd](../self-hosting/index.md) for running the
  daemon as a persistent service.
