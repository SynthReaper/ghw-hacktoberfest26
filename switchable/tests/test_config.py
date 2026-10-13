import pytest

from openswitch.config import Settings


def test_default_settings():
    s = Settings(openswitch_mode="hosted")
    assert s.openswitch_mode == "hosted"
    assert s.max_rows == 200
    assert s.experiment_max_cost_usd == 2.0
    assert s.global_daily_budget_usd == 5.0
    assert not s.kill_switch


def test_local_mode_allows_localhost():
    s = Settings(openswitch_mode="local")
    # Should succeed without raising
    s.validate_provider_url("http://localhost:11434/v1", "ollama")
    s.validate_provider_url("http://127.0.0.1:8000/v1", "local_vllm")
    s.validate_provider_url("http://[::1]:11434/v1", "ipv6_local")


def test_local_mode_blocks_remote_providers():
    s = Settings(openswitch_mode="local")
    with pytest.raises(PermissionError) as exc_info:
        s.validate_provider_url("https://inference.do-ai.run/v1/", "digitalocean")
    assert "OPENSWITCH_MODE=local is active" in str(exc_info.value)
    assert "digitalocean" in str(exc_info.value)
    assert "inference.do-ai.run" in str(exc_info.value)


def test_hosted_mode_allows_remote_providers():
    s = Settings(openswitch_mode="hosted")
    # Should succeed without raising
    s.validate_provider_url("https://inference.do-ai.run/v1/", "digitalocean")
    s.validate_provider_url("https://api.backboard.io/v1", "backboard")


def test_missing_required_key_error_clarity():
    s = Settings(do_model_access_key=None)
    with pytest.raises(ValueError) as exc_info:
        s.get_required_key("do_model_access_key", "DigitalOcean")
    assert "DO_MODEL_ACCESS_KEY" in str(exc_info.value)
    assert "DigitalOcean" in str(exc_info.value)
    assert ".env" in str(exc_info.value)
