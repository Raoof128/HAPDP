"""FHIR helper utilities."""
from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_FIELDS = {
    "Patient": ["id", "name"],
    "Observation": ["id", "subject"],
    "Encounter": ["id", "status"],
    "Condition": ["id", "subject"],
}


class FHIRValidationError(ValueError):
    """Raised when a payload is not a valid FHIR resource."""


def validate_resource(resource: Dict[str, Any]) -> None:
    """Perform lightweight validation of a FHIR resource."""

    if not isinstance(resource, dict):
        raise FHIRValidationError("Payload must be a JSON object")

    resource_type = resource.get("resourceType")
    if not resource_type:
        raise FHIRValidationError("Missing resourceType")

    required = REQUIRED_FIELDS.get(resource_type)
    if not required:
        # Allow passthrough for unknown types but log it upstream.
        return

    missing: List[str] = [field for field in required if field not in resource]
    if missing:
        raise FHIRValidationError(
            f"Resource {resource_type} missing required fields: {', '.join(missing)}"
        )


def extract_resource_type(resource: Dict[str, Any]) -> str:
    return resource.get("resourceType", "Unknown")
