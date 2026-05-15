from brr import protocol
from brr.gates import git


def test_loop_once_baselines_first_seen_head(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inbox = brr_dir / "inbox"
    inbox.mkdir(parents=True)

    monkeypatch.setattr(git, "_remote_head", lambda repo_root, state: "abc123")

    git._loop_once(brr_dir, inbox)

    assert git._load_state(brr_dir)["last_commit"] == "abc123"
    assert list(inbox.glob("*.md")) == []


def test_loop_once_creates_event_for_changed_task_file(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inbox = brr_dir / "inbox"
    inbox.mkdir(parents=True)
    git._save_state(brr_dir, {"last_commit": "old", "watch_dir": "tasks/"})

    calls = []

    def fake_run_git(*args, cwd=None):
        calls.append(args)
        if args[0] == "diff":
            return "tasks/fix-auth.md"
        if args[0] == "show":
            return "fix the auth tests"
        return ""

    monkeypatch.setattr(git, "_remote_head", lambda repo_root, state: "new123456789")
    monkeypatch.setattr(git, "_run_git", fake_run_git)

    git._loop_once(brr_dir, inbox)

    events = protocol.list_pending(inbox)
    assert len(events) == 1
    assert events[0]["source"] == "git"
    assert events[0]["body"] == "fix the auth tests"
    assert events[0]["git_file"] == "tasks/fix-auth.md"
    assert events[0]["git_commit"] == "new123456789"[:12]
    assert git._load_state(brr_dir)["last_commit"] == "new123456789"
    assert any("--diff-filter=AM" in call for call in calls)


def test_loop_once_respects_disabled_state(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inbox = brr_dir / "inbox"
    inbox.mkdir(parents=True)
    git._save_state(brr_dir, {"enabled": False})
    called = []
    monkeypatch.setattr(git, "_remote_head", lambda repo_root, state: called.append(1))

    git._loop_once(brr_dir, inbox)

    assert called == []
