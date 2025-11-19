import json

from audit_logger import emit_audit_event, reset_audit_logger
from config import reload_settings


def test_emit_audit_event_creates_log(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(log_path))
    reload_settings()
    reset_audit_logger()

    emit_audit_event(
        "req-123",
        "Patient",
        "127.0.0.1",
        ["Patient.name:redacted"],
        "success",
    )

    contents = log_path.read_text().strip()
    record = json.loads(contents)
    assert record["request_id"] == "req-123"
    assert record["resource_type"] == "Patient"
    assert record["modified_fields"] == ["Patient.name:redacted"]
