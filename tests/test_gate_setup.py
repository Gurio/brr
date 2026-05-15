from brr.gates import git, slack, telegram


def test_telegram_setup_saves_token_and_accepts_any_chat(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inputs = iter(["secret-token", ""])

    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(
        telegram,
        "_api_call",
        lambda token, method, params=None: {
            "result": {"username": "brrbot"},
        },
    )

    telegram.setup(brr_dir)

    assert telegram._load_state(brr_dir) == {"token": "secret-token"}


def test_slack_setup_saves_token_and_channel(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inputs = iter(["xoxb-secret", "C123"])
    calls = []

    def fake_slack_api(token, method, params=None):
        calls.append((token, method, params))
        return {"ok": True}

    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(slack, "_slack_api", fake_slack_api)

    slack.setup(brr_dir)

    assert slack._load_state(brr_dir) == {
        "token": "xoxb-secret",
        "channel": "C123",
    }
    assert calls == [
        ("xoxb-secret", "auth.test", None),
        ("xoxb-secret", "chat.postMessage", {"channel": "C123", "text": "brr bound."}),
    ]


def test_git_setup_saves_watch_configuration(tmp_path, monkeypatch):
    brr_dir = tmp_path / ".brr"
    inputs = iter(["incoming/", "y"])

    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr(git, "_run_git", lambda *args, cwd=None: "abc123def")

    git.setup(brr_dir)

    assert git._load_state(brr_dir) == {
        "enabled": True,
        "watch_dir": "incoming/",
        "diff_filter": "AM",
        "use_pull": True,
        "last_commit": "abc123def",
    }


def test_git_gate_is_configured_by_default(tmp_path):
    brr_dir = tmp_path / ".brr"

    assert git.is_configured(brr_dir) is True


def test_git_gate_can_be_disabled(tmp_path):
    brr_dir = tmp_path / ".brr"
    git._save_state(brr_dir, {"enabled": False})

    assert git.is_configured(brr_dir) is False


def test_git_gate_reads_legacy_state_file(tmp_path):
    brr_dir = tmp_path / ".brr"
    legacy = brr_dir / "gates" / "git_gate.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"enabled": false}\n', encoding="utf-8")

    assert git.is_configured(brr_dir) is False
