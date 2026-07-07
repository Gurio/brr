from __future__ import annotations

from pathlib import Path

from brr.worktree_hygiene import (
    WorktreeSnapshot,
    classify_worktree,
    format_report_line,
    parse_worktree_list,
)


def test_parse_worktree_list_handles_detached_and_branches():
    output = """\
worktree /repo
HEAD abc123
branch refs/heads/main

worktree /repo/.brr/worktrees/task-1
HEAD def456
detached

worktree /repo/.brr/worktrees/task-2
HEAD fedcba
branch refs/heads/brr/task-2
"""
    entries = parse_worktree_list(output)
    assert entries == [
        type(entries[0])(path=Path("/repo"), branch="main"),
        type(entries[1])(path=Path("/repo/.brr/worktrees/task-1"), branch=None),
        type(entries[2])(path=Path("/repo/.brr/worktrees/task-2"), branch="brr/task-2"),
    ]


def test_classify_worktree_marks_clean_pushed_branch_reap_safe():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch="brr/task-1",
        dirty=False,
        upstream_ref="origin/brr/task-1",
        commits_ahead=0,
    )
    report = classify_worktree(snapshot)

    assert report.classification == "reap-safe"
    assert report.reason == "clean; no commits ahead of origin/brr/task-1; no open PR"
    assert format_report_line(report).endswith("reap-safe | clean; no commits ahead of origin/brr/task-1; no open PR")


def test_classify_worktree_preserves_dirty_even_without_branch():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch=None,
        dirty=True,
    )
    report = classify_worktree(snapshot)

    assert report.classification == "preserve"
    assert report.reason == "detached HEAD with dirty working tree"


def test_classify_worktree_preserves_open_pr():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch="brr/task-1",
        dirty=False,
        pr_states=("OPEN",),
        upstream_ref="origin/brr/task-1",
        commits_ahead=0,
    )
    report = classify_worktree(snapshot)

    assert report.classification == "preserve"
    assert report.reason == "open PR"


def test_classify_worktree_uses_origin_main_fallback_when_no_upstream():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch="brr/task-1",
        dirty=False,
        origin_main_is_ancestor=True,
    )
    report = classify_worktree(snapshot)

    assert report.classification == "reap-safe"
    assert report.reason == "clean; HEAD is an ancestor of origin/main; no open PR"


def test_classify_worktree_preserves_when_no_upstream_and_not_main_ancestor():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch="brr/task-1",
        dirty=False,
        origin_main_is_ancestor=False,
    )
    report = classify_worktree(snapshot)

    assert report.classification == "preserve"
    assert report.reason == "HEAD is not an ancestor of origin/main"


def test_classify_worktree_unknown_on_pr_lookup_failure():
    snapshot = WorktreeSnapshot(
        path=Path("/repo/.brr/worktrees/task-1"),
        branch="brr/task-1",
        dirty=False,
        pr_lookup_error="gh auth failed",
    )
    report = classify_worktree(snapshot)

    assert report.classification == "unknown"
    assert report.reason == "PR lookup failed: gh auth failed"
