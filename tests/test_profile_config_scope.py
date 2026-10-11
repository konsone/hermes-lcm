"""Profile-scoped settings survive external-worker environment stripping."""
import sys
from types import ModuleType

import pytest

from hermes_lcm.config import LCMConfig, read_lcm_env


def bind_scope(monkeypatch, values):
    module = ModuleType("agent.secret_scope")
    module.get_secret = lambda key, default=None: values.get(key, default)
    monkeypatch.setitem(sys.modules, "agent.secret_scope", module)
    return module


def test_worker_uses_scoped_settings_after_env_is_stripped(monkeypatch):
    for key in ("LCM_IGNORE_SESSION_PATTERNS", "LCM_FRESH_TAIL_COUNT", "LCM_EMBEDDINGS_ENABLED"):
        monkeypatch.delenv(key, raising=False)
    bind_scope(monkeypatch, {
        "LCM_IGNORE_SESSION_PATTERNS": "cron:*,cron_*",
        "LCM_FRESH_TAIL_COUNT": "11",
        "LCM_EMBEDDINGS_ENABLED": "false",
    })
    config = LCMConfig.from_env()
    assert config.ignore_session_patterns == ["cron:*", "cron_*"]
    assert config.fresh_tail_count == 11
    assert config.embeddings_enabled is False


def test_scoped_miss_does_not_reuse_launch_profile_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LCM_IGNORE_SESSION_PATTERNS", "launch:*")
    monkeypatch.setenv("LCM_FRESH_TAIL_COUNT", "999")
    bind_scope(monkeypatch, {})
    home = tmp_path / "routed"
    home.mkdir()
    (home / "config.yaml").write_text("lcm:\n  ignore_session_patterns: ['routed:*']\n  fresh_tail_count: 7\n")
    host = ModuleType("hermes_constants")
    host.get_hermes_home = lambda: home
    monkeypatch.setitem(sys.modules, "hermes_constants", host)
    config = LCMConfig.from_env()
    assert config.ignore_session_patterns == ["routed:*"]
    assert config.fresh_tail_count == 7


def test_yaml_home_follows_current_profile_without_env_mutation(monkeypatch, tmp_path):
    bind_scope(monkeypatch, {})
    homes = [tmp_path / "one", tmp_path / "two"]
    for home, count in zip(homes, [5, 9]):
        home.mkdir()
        (home / "config.yaml").write_text(f"lcm:\n  fresh_tail_count: {count}\n")
    host = ModuleType("hermes_constants")
    current = [homes[0]]
    host.get_hermes_home = lambda: current[0]
    monkeypatch.setitem(sys.modules, "hermes_constants", host)
    first = LCMConfig.from_env()
    current[0] = homes[1]
    second = LCMConfig.from_env()
    assert (first.fresh_tail_count, second.fresh_tail_count) == (5, 9)


def test_legacy_host_keeps_env_support(monkeypatch):
    monkeypatch.setitem(sys.modules, "agent.secret_scope", None)
    monkeypatch.setenv("LCM_FRESH_TAIL_COUNT", "8")
    assert read_lcm_env("LCM_FRESH_TAIL_COUNT") == "8"


def test_scope_guard_is_not_bypassed(monkeypatch):
    module = bind_scope(monkeypatch, {})
    def guarded(key, default=None):
        raise RuntimeError("profile scope required")
    module.get_secret = guarded
    monkeypatch.setenv("LCM_FRESH_TAIL_COUNT", "999")
    with pytest.raises(RuntimeError, match="profile scope required"):
        read_lcm_env("LCM_FRESH_TAIL_COUNT")
