"""Configuration helpers for the privacy proxy."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import importlib
import importlib.util
import json
import os

YAML_LOADER = None
if importlib.util.find_spec("yaml"):
    YAML_LOADER = importlib.import_module("yaml")


@dataclass
class RuleConfig:
    """Represents the privacy rules to apply when sanitising payloads."""

    redact_fields: List[str] = field(default_factory=list)
    hash_fields: List[str] = field(default_factory=list)
    mask_fields: List[Dict[str, Any]] = field(default_factory=list)
    hash_salt: str = ""


@dataclass
class Settings:
    """Runtime configuration."""

    ai_endpoint_url: str = "http://localhost:9000/analyse"
    ai_endpoint_timeout: int = 20
    ai_auth_header: Optional[str] = None
    rule_config_path: Path = Path("pii_rules.json")
    audit_log_path: Optional[Path] = Path("logs/audit.log")

    @property
    def rule_config(self) -> RuleConfig:
        return load_rules(self.rule_config_path)


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load settings from environment variables."""

    settings = Settings()
    if value := os.getenv("AI_ENDPOINT_URL"):
        settings.ai_endpoint_url = value
    if value := os.getenv("AI_ENDPOINT_TIMEOUT"):
        settings.ai_endpoint_timeout = int(value)
    if value := os.getenv("AI_AUTH_HEADER"):
        settings.ai_auth_header = value
    if value := os.getenv("PII_RULE_PATH"):
        settings.rule_config_path = Path(value)
    if value := os.getenv("AUDIT_LOG_PATH"):
        settings.audit_log_path = Path(value)
    return settings


@lru_cache(maxsize=1)
def load_rules(path: Path) -> RuleConfig:
    """Load the rule configuration from disk."""

    if not path.exists():
        return RuleConfig()
    if path.suffix in {".yaml", ".yml"}:
        if not YAML_LOADER:
            raise RuntimeError("PyYAML is required to read YAML rule files")
        data = YAML_LOADER.safe_load(path.read_text())
    else:
        data = json.loads(path.read_text())
    return RuleConfig(**(data or {}))


def reload_rules() -> RuleConfig:
    """Clear the rule cache so changes are picked up."""

    load_rules.cache_clear()
    settings = load_settings()
    return load_rules(settings.rule_config_path)


def reload_settings() -> Settings:
    """Clear cached settings (and rules) to pick up env changes, useful in tests."""

    load_settings.cache_clear()
    settings = load_settings()
    # Rules are cached separately and depend on the new settings
    load_rules.cache_clear()
    load_rules(settings.rule_config_path)
    return settings
