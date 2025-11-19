import json

from config import load_settings, reload_settings


def test_load_rules_from_json(tmp_path, monkeypatch):
    rule_file = tmp_path / "rules.json"
    rule_file.write_text(
        json.dumps(
            {
                "hash_fields": ["Patient.identifier.value"],
                "hash_salt": "unit-test",
                "redact_fields": ["Patient.name"],
            }
        )
    )

    monkeypatch.setenv("PII_RULE_PATH", str(rule_file))
    reload_settings()

    settings = load_settings()
    assert settings.rule_config.hash_fields == ["Patient.identifier.value"]
    assert settings.rule_config.hash_salt == "unit-test"
    assert settings.rule_config.redact_fields == ["Patient.name"]


def test_reload_settings_picks_up_env(monkeypatch):
    monkeypatch.setenv("AI_ENDPOINT_URL", "http://example.com")
    reload_settings()
    assert load_settings().ai_endpoint_url == "http://example.com"
