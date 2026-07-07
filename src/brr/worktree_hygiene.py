"""Dry-run hygiene report for local git worktrees and branches."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from . import gitops, worktree


Classification = Literal["reap-safe", "preserve", "unknown"]


@dataclass(frozen=True)
class WorktreeEntry:
    """A row from ``git worktree list --porcelain``."""

    path: Path
    branch: str | None


@dataclass(frozen=True)
class WorktreeSnapshot:
    """Inspection results for one worktree before classification."""

    path: Path
    branch: str | None
    dirty: bool
    upstream_ref: str | None = None
    commits_ahead: int | None = None
    origin_main_is_ancestor: bool | None = None
    pr_states: tuple[str, ...] = ()
    pr_lookup_error: str | None = None
    commit_lookup_error: str | None = None


@dataclass(frozen=True)
class WorktreeReport:
    """Final report row for one worktree."""

    path: Path
    branch: str | None
    classification: Classification
    reason: str


def parse_worktree_list(output: str) -> list[WorktreeEntry]:
    """Parse ``git worktree list --porcelain`` output."""
    entries: list[WorktreeEntry] = []
    current_path: Path | None = None
    current_branch: str | None = None

    def flush() -> None:
        nonlocal current_path, current_branch
        if current_path is not None:
            entries.append(WorktreeEntry(path=current_path, branch=current_branch))
        current_path = None
        current_branch = None

    for line in output.splitlines():
        if not line:
            flush()
            continue
        if line.startswith("worktree "):
            current_path = Path(line.split(" ", 1)[1])
            current_branch = None
            continue
        if line.startswith("branch "):
            ref = line.split(" ", 1)[1].strip()
            current_branch = ref.removeprefix("refs/heads/") or None
            continue
        if line.startswith("detached"):
            current_branch = None

    flush()
    return entries


def classify_worktree(snapshot: WorktreeSnapshot) -> WorktreeReport:
    """Classify one inspected worktree for the report."""
    branch = (snapshot.branch or "").strip() or None
    path = snapshot.path

    if snapshot.dirty:
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="preserve",
            reason=_reason_dirty(branch),
        )

    if branch is None:
        return WorktreeReport(
            path=path,
            branch=None,
            classification="unknown",
            reason="detached HEAD",
        )

    if snapshot.pr_lookup_error:
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="unknown",
            reason=f"PR lookup failed: {snapshot.pr_lookup_error}",
        )

    if _has_open_pr(snapshot.pr_states):
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="preserve",
            reason="open PR",
        )

    if snapshot.commit_lookup_error:
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="unknown",
            reason=f"commit lookup failed: {snapshot.commit_lookup_error}",
        )

    if snapshot.upstream_ref:
        if snapshot.commits_ahead is None:
            return WorktreeReport(
                path=path,
                branch=branch,
                classification="unknown",
                reason=f"cannot count commits ahead of {snapshot.upstream_ref}",
            )
        if snapshot.commits_ahead > 0:
            return WorktreeReport(
                path=path,
                branch=branch,
                classification="preserve",
                reason=(
                    f"{snapshot.commits_ahead} unpushed commit(s) "
                    f"ahead of {snapshot.upstream_ref}"
                ),
            )
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="reap-safe",
            reason=(
                f"clean; no commits ahead of {snapshot.upstream_ref}; "
                "no open PR"
            ),
        )

    if snapshot.origin_main_is_ancestor is None:
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="unknown",
            reason="cannot compare against origin/main",
        )

    if snapshot.origin_main_is_ancestor:
        return WorktreeReport(
            path=path,
            branch=branch,
            classification="reap-safe",
            reason="clean; HEAD is an ancestor of origin/main; no open PR",
        )

    return WorktreeReport(
        path=path,
        branch=branch,
        classification="preserve",
        reason="HEAD is not an ancestor of origin/main",
    )


def format_report_line(report: WorktreeReport) -> str:
    """Render one report row."""
    branch = report.branch or "<detached>"
    return f"{report.path} | {branch} | {report.classification} | {report.reason}"


def build_worktree_hygiene_report(repo_root: Path) -> list[WorktreeReport]:
    """Inspect all worktrees in *repo_root* and classify them."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or "failed to list worktrees")

    entries = parse_worktree_list(result.stdout)
    pr_cache: dict[str, tuple[tuple[str, ...], str | None]] = {}
    reports: list[WorktreeReport] = []
    for entry in entries:
        try:
            snapshot = inspect_worktree(repo_root, entry, pr_cache=pr_cache)
        except Exception as exc:  # pragma: no cover - defensive, report-only tool
            snapshot = WorktreeSnapshot(
                path=entry.path,
                branch=entry.branch,
                dirty=False,
                pr_lookup_error=str(exc),
            )
        reports.append(classify_worktree(snapshot))
    return reports


def inspect_worktree(
    repo_root: Path,
    entry: WorktreeEntry,
    *,
    pr_cache: dict[str, tuple[tuple[str, ...], str | None]],
) -> WorktreeSnapshot:
    """Collect the git/gh facts needed to classify one worktree."""
    dirty = False
    try:
        dirty = worktree.has_uncommitted_changes(entry.path)
    except Exception as exc:
        return WorktreeSnapshot(
            path=entry.path,
            branch=entry.branch,
            dirty=False,
            pr_lookup_error=str(exc),
        )

    branch = entry.branch
    if branch is None:
        return WorktreeSnapshot(path=entry.path, branch=None, dirty=dirty)

    pr_states, pr_error = _lookup_pr_states(repo_root, branch, pr_cache=pr_cache)
    if pr_error and dirty:
        # Dirty is enough to preserve, so do not hide that behind a lookup miss.
        pr_error = None

    upstream_ref = None
    commits_ahead = None
    commit_lookup_error = None
    origin_main_is_ancestor = None

    try:
        upstream_ref = gitops.branch_upstream(repo_root, branch)
    except Exception as exc:
        commit_lookup_error = str(exc)

    if commit_lookup_error is None and upstream_ref:
        commits_ahead, commit_lookup_error = _count_commits_ahead(entry.path, upstream_ref)
    elif commit_lookup_error is None:
        origin_main_oid = gitops.rev_parse(repo_root, "origin/main")
        if origin_main_oid is None:
            commit_lookup_error = "cannot resolve origin/main"
        elif gitops.rev_parse(repo_root, branch) is None:
            commit_lookup_error = f"cannot resolve {branch}"
        else:
            origin_main_is_ancestor = _is_ancestor(repo_root, branch, "origin/main")

    return WorktreeSnapshot(
        path=entry.path,
        branch=branch,
        dirty=dirty,
        upstream_ref=upstream_ref,
        commits_ahead=commits_ahead,
        origin_main_is_ancestor=origin_main_is_ancestor,
        pr_states=pr_states,
        pr_lookup_error=pr_error,
        commit_lookup_error=commit_lookup_error,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the dry-run report."""
    del argv
    repo_root = gitops.ensure_git_repo()
    for report in build_worktree_hygiene_report(repo_root):
        print(format_report_line(report))
    return 0


def _lookup_pr_states(
    repo_root: Path,
    branch: str,
    *,
    pr_cache: dict[str, tuple[tuple[str, ...], str | None]],
) -> tuple[tuple[str, ...], str | None]:
    cached = pr_cache.get(branch)
    if cached is not None:
        return cached

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--state",
            "all",
            "--json",
            "state",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        cached = ((), detail or "gh pr list failed")
        pr_cache[branch] = cached
        return cached

    try:
        payload = json.loads(result.stdout or "[]")
    except ValueError as exc:
        cached = ((), f"invalid gh pr list output: {exc}")
        pr_cache[branch] = cached
        return cached

    if not isinstance(payload, list):
        cached = ((), "invalid gh pr list payload")
        pr_cache[branch] = cached
        return cached

    states: list[str] = []
    for item in payload:
        if isinstance(item, dict):
            state = str(item.get("state") or "").strip()
            if state:
                states.append(state)
    cached = (tuple(states), None)
    pr_cache[branch] = cached
    return cached


def _count_commits_ahead(worktree_path: Path, upstream_ref: str) -> tuple[int | None, str | None]:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{upstream_ref}..HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, str(exc)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        return None, detail or f"failed to count commits ahead of {upstream_ref}"
    try:
        return int(result.stdout.strip() or "0"), None
    except ValueError:
        return None, f"invalid rev-list count: {result.stdout.strip()!r}"


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _has_open_pr(pr_states: tuple[str, ...]) -> bool:
    return any(state.strip().casefold() == "open" for state in pr_states)


def _reason_dirty(branch: str | None) -> str:
    if branch:
        return "dirty working tree"
    return "detached HEAD with dirty working tree"


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main(sys.argv[1:]))
