"""Git gate — turns task files from a git remote into brr events.

The git gate is intentionally credential-free: if the repository can
``git fetch`` its remote, brr can poll for task files. It is enabled by
default and watches ``tasks/`` on the repo's default branch. Each new or
modified file under that directory becomes an inbox event.

This is a conservative default. It gives users a universal, forge-agnostic
input path without spending runner tokens on every arbitrary code push.
Broader repository-change automation, PRs, issues, and comments belong in
explicit source modes or provider-specific forge gates.

Delivery is a no-op — the agent's commit and the daemon's push *are* the
delivery.

State lives in ``.brr/gates/git.json``. Older installs may still have
``git_gate.json``; the gate reads that file and migrates state on write.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .. import gitops
from .. import protocol

_BACKOFF_MAX = 120
_POLL_INTERVAL = 30
_DEFAULT_WATCH_DIR = "tasks/"
_DEFAULT_DIFF_FILTER = "AM"


# ── State ────────────────────────────────────────────────────────────


def _state_path(brr_dir: Path) -> Path:
    return brr_dir / "gates" / "git.json"


def _legacy_state_path(brr_dir: Path) -> Path:
    return brr_dir / "gates" / "git_gate.json"


def _load_state(brr_dir: Path) -> dict:
    path = _state_path(brr_dir)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    legacy = _legacy_state_path(brr_dir)
    if legacy.exists():
        return json.loads(legacy.read_text(encoding="utf-8"))
    return {}


def _save_state(brr_dir: Path, state: dict) -> None:
    path = _state_path(brr_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _default_state() -> dict:
    return {
        "enabled": True,
        "watch_dir": _DEFAULT_WATCH_DIR,
        "diff_filter": _DEFAULT_DIFF_FILTER,
        "use_pull": False,
    }


def _effective_state(brr_dir: Path) -> dict:
    state = _default_state()
    state.update(_load_state(brr_dir))
    return state


def configure_default(brr_dir: Path) -> None:
    """Persist the default git gate configuration if none exists yet."""
    if _state_path(brr_dir).exists() or _legacy_state_path(brr_dir).exists():
        return
    state = _default_state()
    head = _run_git("rev-parse", "HEAD", cwd=brr_dir.parent)
    if head:
        state["last_commit"] = head
    _save_state(brr_dir, state)


# ── Git helpers ──────────────────────────────────────────────────────


def _run_git_result(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd,
        capture_output=True, text=True, timeout=60,
    )


def _run_git(*args: str, cwd: Path | None = None) -> str:
    result = _run_git_result(*args, cwd=cwd)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _default_branch(repo_root: Path) -> str:
    return gitops.default_branch(repo_root) or "HEAD"


def _default_remote(repo_root: Path) -> str:
    return gitops.default_remote(repo_root) or "origin"


def _remote_head(repo_root: Path, state: dict) -> str:
    if state.get("use_pull", False):
        branch = str(state.get("branch") or _default_branch(repo_root))
        return _run_git("rev-parse", branch, cwd=repo_root)

    remote = str(state.get("remote") or _default_remote(repo_root))
    branch = str(state.get("branch") or _default_branch(repo_root))
    if branch == "HEAD":
        return _run_git("rev-parse", "HEAD", cwd=repo_root)
    fetched = _run_git_result("fetch", "--quiet", remote, branch, cwd=repo_root)
    if fetched.returncode != 0:
        return ""
    return _run_git("rev-parse", "FETCH_HEAD", cwd=repo_root)


# ── Setup ────────────────────────────────────────────────────────────


def auth(brr_dir: Path) -> None:
    print("[brr:git] No auth needed for git gate.")
    print("[brr:git] It is enabled by default and watches 'tasks/'.")
    print("[brr:git] Configure .brr/gates/git.json to change the watch source.")


def bind(brr_dir: Path) -> None:
    state = _effective_state(brr_dir)
    watch_dir = input("Watch directory (default: tasks/): ").strip() or _DEFAULT_WATCH_DIR
    state["watch_dir"] = watch_dir

    use_pull = input("Use git pull instead of fetch+diff? (y/N): ").strip().lower()
    state["use_pull"] = use_pull in ("y", "yes")
    state["enabled"] = True

    head = _run_git("rev-parse", "HEAD", cwd=brr_dir.parent)
    if head:
        state["last_commit"] = head
    _save_state(brr_dir, state)
    print(f"[brr:git] Watching '{watch_dir}' from commit {head[:8] if head else 'current'}")


def setup(brr_dir: Path) -> None:
    """Configure the git watch source in one interactive flow."""
    auth(brr_dir)
    bind(brr_dir)


def is_configured(brr_dir: Path) -> bool:
    state = _effective_state(brr_dir)
    return state.get("enabled", True) is not False


# ── Gate loop ────────────────────────────────────────────────────────


def run_loop(brr_dir: Path, inbox_dir: Path, responses_dir: Path) -> None:
    backoff = 1
    while True:
        try:
            _loop_once(brr_dir, inbox_dir)
            time.sleep(_POLL_INTERVAL)
            backoff = 1
        except Exception as e:
            print(f"[brr:git] error: {e}, retrying in {backoff}s")
            time.sleep(backoff)
            backoff = min(backoff * 2, _BACKOFF_MAX)


def _loop_once(brr_dir: Path, inbox_dir: Path) -> None:
    state = _effective_state(brr_dir)
    if state.get("enabled", True) is False:
        return

    watch_dir = str(state.get("watch_dir") or _DEFAULT_WATCH_DIR)
    diff_filter = str(state.get("diff_filter") or _DEFAULT_DIFF_FILTER)
    last_commit = str(state.get("last_commit") or "")
    repo_root = brr_dir.parent

    if state.get("use_pull", False):
        _run_git("pull", "--ff-only", cwd=repo_root)

    head = _remote_head(repo_root, state)
    if not head:
        return
    if not last_commit:
        state["last_commit"] = head
        _save_state(brr_dir, state)
        return
    if head == last_commit:
        return

    diff_output = _run_git(
        "diff", "--name-only", f"--diff-filter={diff_filter}",
        f"{last_commit}..{head}", "--", watch_dir,
        cwd=repo_root,
    )

    if not diff_output:
        state["last_commit"] = head
        _save_state(brr_dir, state)
        return

    for filename in diff_output.splitlines():
        filename = filename.strip()
        if not filename:
            continue
        content = _run_git("show", f"{head}:{filename}", cwd=repo_root)
        if content:
            protocol.create_event(
                inbox_dir,
                source="git",
                body=content,
                git_file=filename,
                git_commit=head[:12],
            )

    state["last_commit"] = head
    _save_state(brr_dir, state)
