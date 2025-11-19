import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import RuleConfig
from fhir_utils import FHIRValidationError, validate_resource
from pii_engine import PIIEngine


def load_payload():
    with open("examples/patient_before.json") as f:
        return json.load(f)


def test_engine_redacts_expected_fields():
    engine = PIIEngine()
    clean, modifications = engine.sanitize(load_payload())

    assert clean["name"] == []
    assert clean["birthDate"] == "REDACTED"
    assert clean["telecom"] == []
    assert len(clean["identifier"][0]["value"]) == 64
    assert len(clean["identifier"][1]["value"]) == 64
    assert any("hashed" in entry for entry in modifications)


def test_mask_rules_take_precedence_over_hash_rules():
    config = RuleConfig(
        hash_fields=["Patient.identifier.value"],
        mask_fields=[{"path": "Patient.identifier.value", "visible": 2, "mask_char": "#"}],
        hash_salt="demo",
    )
    engine = PIIEngine(config)
    payload = {
        "resourceType": "Patient",
        "id": "demo",
        "identifier": [{"value": "A123456"}],
    }
    clean, modifications = engine.sanitize(payload)

    assert clean["identifier"][0]["value"].endswith("56")
    assert "#" in clean["identifier"][0]["value"]
    assert len(clean["identifier"][0]["value"]) == len("A123456")
    assert any("masked" in entry for entry in modifications)


def test_regex_detection_redacts_free_form_values():
    engine = PIIEngine()
    payload = {"resourceType": "Patient", "id": "demo", "note": "DOB 1990-05-06"}
    clean, modifications = engine.sanitize(payload)

    assert clean["note"] == "REDACTED"
    assert any("dob_redacted" in entry for entry in modifications)


def test_managing_organization_reference_masked():
    engine = PIIEngine()
    clean, _ = engine.sanitize(load_payload())

    assert clean["managingOrganization"]["reference"].startswith("****")


def test_validate_resource_requires_resource_type():
    with pytest.raises(FHIRValidationError):
        validate_resource({"id": "123"})


def test_patient_requires_mandatory_fields():
    with pytest.raises(FHIRValidationError):
        validate_resource({"resourceType": "Patient", "id": "abc"})
