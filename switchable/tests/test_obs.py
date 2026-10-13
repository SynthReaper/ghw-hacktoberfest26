from openswitch.obs import (
    check_and_report_experiment_anomalies,
    gen_ai_span,
    sentry_event_scrubber,
)


def test_sentry_event_scrubber_removes_sensitive_data():
    raw_event = {
        "message": "Model generation completed",
        "extra": {
            "model": "gemma-2-9b",
            "tokens_in": 120,
            "api_key": "sk-secret12345",
            "prompt": "Classify this user credit card number: 1234-5678",
            "output": "Category: Banking",
            "nested": {
                "auth_token": "bearer xyz",
                "safe_field": 42,
            },
        },
        "breadcrumbs": {
            "values": [
                {
                    "message": "calling provider",
                    "data": {
                        "messages": [{"role": "user", "content": "secret prompt"}],
                        "provider": "digitalocean",
                    },
                }
            ]
        },
        "request": {
            "data": "raw payload with prompt",
            "headers": {
                "Authorization": "Bearer secret",
                "User-Agent": "openswitch-agent",
            },
        },
    }

    scrubbed = sentry_event_scrubber(raw_event, hint={})

    # Extra assertions
    assert scrubbed["extra"]["model"] == "gemma-2-9b"
    assert scrubbed["extra"]["tokens_in"] == 120
    assert scrubbed["extra"]["api_key"] == "[SCRUBBED]"
    assert scrubbed["extra"]["prompt"] == "[SCRUBBED]"
    assert scrubbed["extra"]["output"] == "[SCRUBBED]"
    assert scrubbed["extra"]["nested"]["auth_token"] == "[SCRUBBED]"
    assert scrubbed["extra"]["nested"]["safe_field"] == 42

    # Breadcrumb assertions
    b_data = scrubbed["breadcrumbs"]["values"][0]["data"]
    assert b_data["messages"] == "[SCRUBBED]"
    assert b_data["provider"] == "digitalocean"

    # Request assertions
    assert scrubbed["request"]["data"] == "[SCRUBBED]"
    assert scrubbed["request"]["headers"]["Authorization"] == "[SCRUBBED]"
    assert scrubbed["request"]["headers"]["User-Agent"] == "openswitch-agent"


def test_gen_ai_span_records_telemetry_safely():
    with gen_ai_span(
        operation="chat",
        description="Run evaluation on Gemma-2-9B",
        model="gemma-2-9b",
        provider="digitalocean",
        prompt_version="v1",
        experiment_id="exp-123",
    ) as meta:
        meta["tokens_in"] = 150
        meta["tokens_out"] = 35
        meta["latency_ms"] = 120.5
        meta["ttft_ms"] = 25.0
        meta["cost_usd"] = 0.000037

    # Verify meta populated
    assert meta["tokens_in"] == 150
    assert meta["tokens_out"] == 35
    assert meta["latency_ms"] == 120.5
    assert meta["cost_usd"] == 0.000037


def test_check_and_report_experiment_anomalies():
    # Normal experiment: no anomalies
    alerts_none = check_and_report_experiment_anomalies(
        experiment_id="exp-normal",
        inconsistency_rate=0.05,
        provider_error_rate=0.01,
        empty_output_rate=0.00,
        budget_cap_hit=False,
    )
    assert len(alerts_none) == 0

    # Anomalies triggered:
    # inconsistency > 0.20, provider_error > 0.10, empty_output > 0.05, budget cap hit
    alerts = check_and_report_experiment_anomalies(
        experiment_id="exp-troubled",
        inconsistency_rate=0.25,
        provider_error_rate=0.15,
        empty_output_rate=0.08,
        budget_cap_hit=True,
        total_cost_usd=2.50,
    )

    assert len(alerts) == 4
    assert any("judge inconsistency" in a.lower() for a in alerts)
    assert any("provider error" in a.lower() for a in alerts)
    assert any("empty output" in a.lower() for a in alerts)
    assert any("budget cap hit" in a.lower() for a in alerts)
