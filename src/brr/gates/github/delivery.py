"""Response delivery — post the agent's reply to the originating thread.

Three reply shapes:

- Label-triggered issues: a plain top-level comment on the issue. No
  quote pointer; the issue *is* the source.
- Mention-triggered timeline comments (issue or PR): top-level comment
  on the issue/PR, prefixed with a blockquote linking back at the
  triggering comment (mirrors what GitHub's "Quote reply" button does).
- Mention-triggered inline review comments: in-thread reply via the
  pull-request review-replies API, again with a quote pointer header.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from requests.utils import quote

from ... import protocol
from ...task import Task
from .. import runtime
from . import client
from .constants import _COMMENT_KINDS
from .paths import issue_comments, pull, pull_comment_replies, repo_pulls


def _coerce_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_task_for_event(brr_dir: Path, event_id: str) -> Task | None:
    """Scan .brr/tasks/ for the task whose event_id matches *event_id*."""
    tasks_dir = brr_dir / "tasks"
    if not tasks_dir.exists():
        return None
    for path in tasks_dir.glob("*.md"):
        task = Task.from_file(path)
        if task and task.event_id == event_id:
            return task
    return None


def _branch_footer(repo: str, task: Task) -> str:
    """Return a Markdown footer with branch / PR links, or empty string.

    Only appended after finalization has identified the branch that
    should be published. The ``?expand=1`` on the compare URL pre-fills
    GitHub's PR-creation form so clicking it is one step from merging.
    """
    branch = task.meta.get("publish_branch")
    if not branch:
        return ""
    base_url = f"https://github.com/{repo}"
    tree_url = f"{base_url}/tree/{quote(branch, safe='/')}"
    compare_url = f"{base_url}/compare/{quote(branch, safe='/')}?expand=1"
    return (
        f"\n\n---\n"
        f"Branch: [`{branch}`]({tree_url}) · "
        f"[Compare & open PR ↗]({compare_url})"
    )


def _thread_reply_body(event: dict, body: str) -> str:
    """Prepend a quote-style pointer back at the triggering comment.

    GitHub's issue/PR comment endpoint has no first-class "reply to a
    specific comment" primitive for timeline comments. The closest
    visible thread anchor is a blockquote linking to the source comment,
    matching what the GitHub web UI's "Quote reply" button generates.
    Skipped for label-triggered events because the issue itself *is*
    the source — the comment doesn't need to point at it. Inline review
    replies *do* have a first-class reply primitive (handled by the
    ``pulls/{n}/comments/{cid}/replies`` endpoint), but we still
    prepend the pointer there because the review-replies API anchors
    only to the *thread*, not to the specific comment we're replying
    to within it.
    """
    kind = str(event.get("github_kind") or "")
    if kind not in _COMMENT_KINDS:
        return body
    url = str(event.get("github_html_url") or "").strip()
    if not url:
        return body
    author = str(event.get("github_author") or "").strip()
    if author:
        preface = f"> Replying to [@{author}'s comment]({url})\n\n"
    else:
        preface = f"> Replying to [the source comment]({url})\n\n"
    return preface + body


def _post_comment(token: str, event: dict, body: str) -> None:
    """Post one message (interim or terminal) as a GitHub comment.

    Raises on a missing target or API error so the streaming driver
    skips the event and retries it on the next loop (rather than
    silently dropping the message or cleaning up prematurely).
    """
    eid = event["id"]
    repo = event.get("github_repo")
    number = _coerce_int(event.get("github_issue_number"))
    if not repo or number is None:
        raise ValueError("missing repo / issue_number")
    threaded_body = _thread_reply_body(event, body)
    kind = str(event.get("github_kind") or "")
    review_cid = _coerce_int(event.get("github_comment_id"))
    pr_number = _coerce_int(
        event.get("github_pr_number") or event.get("github_issue_number"),
    )
    if kind == "pr-review-comment" and review_cid is not None and pr_number is not None:
        post_path = pull_comment_replies(repo, pr_number, review_cid)
    else:
        post_path = issue_comments(repo, number)
    client._api_post(token, post_path, body={"body": threaded_body})


def _is_pull_request_delivery(event: dict) -> bool:
    kind = str(
        event.get("github_delivery")
        or event.get("forge_delivery")
        or event.get("delivery")
        or ""
    ).strip()
    return kind in {"pull-request", "pull_request", "pr"}


def _event_repo(event: dict, default_repo: str | None) -> str | None:
    repo = str(event.get("github_repo") or event.get("repo") or "").strip()
    return repo or default_repo


def _head_query(repo: str, head: str) -> str:
    """Return GitHub's owner:branch head selector for same-repo branches."""
    if ":" in head:
        return head
    owner, _, _name = repo.partition("/")
    return f"{owner}:{head}" if owner else head


def _existing_open_pr(token: str, repo: str, head: str) -> dict | None:
    """Return the first open PR for *head*, or ``None`` if absent."""
    payload = client._api_get(
        token,
        repo_pulls(repo),
        params={"state": "open", "head": _head_query(repo, head), "per_page": 1},
    )
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    return None


def _pr_number(pr: dict | None) -> int | None:
    if not pr:
        return None
    raw = pr.get("number")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _pr_url(payload: Any, fallback: dict | None = None) -> str | None:
    if isinstance(payload, dict) and isinstance(payload.get("html_url"), str):
        return payload["html_url"]
    if isinstance(fallback, dict) and isinstance(fallback.get("html_url"), str):
        return fallback["html_url"]
    return None


def _deliver_pull_request(
    token: str,
    event: dict,
    body: str,
    *,
    default_repo: str | None = None,
) -> None:
    """Open or refresh a PR described by a gate-addressed delivery event.

    The resident owns the review pack and Markdown projection; this gate
    only performs the forge delivery. Missing required fields are treated
    as a malformed message and dropped by returning normally. GitHub API
    errors are left to bubble so ``runtime.deliver_stream`` retries the
    done event on the next gate loop — important when the outbox message
    is drained before the daemon finishes pushing the head branch.
    """
    repo = _event_repo(event, default_repo)
    base = str(event.get("base") or event.get("github_base") or "").strip()
    head = str(event.get("head") or event.get("github_head") or "").strip()
    title = str(event.get("title") or event.get("github_title") or "").strip()
    if not (repo and base and head and title and body):
        print("[brr:github] PR delivery missing repo/base/head/title/body; dropping")
        return
    if base == head:
        print(f"[brr:github] PR delivery head matches base ({head}); skipping")
        return

    existing = _existing_open_pr(token, repo, head)
    number = _pr_number(existing)
    if number is not None:
        payload = client._api_patch(
            token,
            pull(repo, number),
            body={"title": title, "body": body},
        )
        print(f"[brr:github] PR refreshed -> {_pr_url(payload, existing) or head}")
        return

    payload = client._api_post(
        token,
        repo_pulls(repo),
        body={"base": base, "head": head, "title": title, "body": body},
    )
    print(f"[brr:github] PR opened -> {_pr_url(payload) or head}")


def _deliver_responses(
    brr_dir: Path,
    inbox_dir: Path,
    responses_dir: Path,
    token: str,
    *,
    default_repo: str | None = None,
) -> None:
    def deliver_partial(event: dict, body: str) -> None:
        _post_comment(token, event, body)

    def deliver_terminal(event: dict, body: str) -> None:
        if _is_pull_request_delivery(event):
            _deliver_pull_request(token, event, body, default_repo=default_repo)
            return
        # The branch footer (committed SHA + compare link) is the
        # thread's closing context, so it rides only the terminal reply.
        repo = event.get("github_repo")
        task = _find_task_for_event(brr_dir, event["id"])
        if repo and task is not None:
            footer = _branch_footer(repo, task)
            if footer:
                body = body.rstrip() + footer + "\n"
        _post_comment(token, event, body)

    runtime.deliver_stream(
        inbox_dir, responses_dir, "github", deliver_partial, deliver_terminal,
    )
