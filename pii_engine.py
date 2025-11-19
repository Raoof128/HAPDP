"""PII detection and de-identification engine."""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from config import RuleConfig, load_settings

# Regex patterns for additional PII detection in free-form fields.
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"(?:\+?61|0)[0-9]{8,10}")
MEDICARE_REGEX = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
DOB_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


class PIIEngine:
    def __init__(self, rule_config: RuleConfig | None = None):
        self.rule_config = rule_config or load_settings().rule_config

    def refresh_rules(self) -> None:
        self.rule_config = load_settings().rule_config

    def sanitize(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        clean_payload = copy.deepcopy(payload)
        modifications: List[str] = []
        root_type = payload.get("resourceType", "Resource")
        self._walk(clean_payload, [root_type], root_type, modifications)
        return clean_payload, modifications

    # Recursive traversal -------------------------------------------------
    def _walk(
        self,
        value: Any,
        path_tokens: Sequence[str],
        display_path: str,
        modifications: List[str],
    ) -> Any:
        if self._path_matches(path_tokens, self.rule_config.redact_fields):
            modifications.append(f"{display_path}:redacted")
            return self._placeholder(value)
        if isinstance(value, dict):
            for key in list(value.keys()):
                child_path = list(path_tokens) + [key]
                display = f"{display_path}.{key}" if display_path else key
                value[key] = self._walk(value[key], child_path, display, modifications)
            return value
        if isinstance(value, list):
            for index, item in enumerate(value):
                child_display = f"{display_path}[{index}]"
                value[index] = self._walk(item, path_tokens, child_display, modifications)
            return value
        return self._apply_rules(value, path_tokens, display_path, modifications)

    # Rule application ----------------------------------------------------
    def _apply_rules(
        self,
        value: Any,
        path_tokens: Sequence[str],
        display_path: str,
        modifications: List[str],
    ) -> Any:
        if value is None:
            return value

        # Always operate on string representation for regex detection
        str_value = str(value) if not isinstance(value, str) else value

        if self._path_matches(path_tokens, self.rule_config.redact_fields):
            modifications.append(f"{display_path}:redacted")
            return "REDACTED"

        mask_rule = self._mask_rule(path_tokens)
        if mask_rule:
            masked = self._mask_value(str_value, mask_rule)
            modifications.append(f"{display_path}:masked")
            return masked

        if self._path_matches(path_tokens, self.rule_config.hash_fields):
            hashed = self._hash_value(str_value)
            modifications.append(f"{display_path}:hashed")
            return hashed

        regex_match = self._regex_detect(str_value)
        if regex_match:
            modifications.append(f"{display_path}:{regex_match}")
            return "REDACTED"

        return value

    def _path_matches(self, path_tokens: Sequence[str], patterns: Iterable[str]) -> bool:
        for pattern in patterns:
            pattern_tokens = pattern.split(".")
            if len(pattern_tokens) != len(path_tokens):
                continue
            if all(
                pt == token or pt == "*"
                for pt, token in zip(pattern_tokens, path_tokens)
            ):
                return True
        return False

    @staticmethod
    def _placeholder(value: Any) -> Any:
        if isinstance(value, list):
            return []
        if isinstance(value, dict):
            return {}
        return "REDACTED"

    def _mask_rule(self, path_tokens: Sequence[str]):
        for rule in self.rule_config.mask_fields:
            pattern = rule.get("path")
            if not pattern:
                continue
            pattern_tokens = pattern.split(".")
            if len(pattern_tokens) != len(path_tokens):
                continue
            if all(
                pt == token or pt == "*"
                for pt, token in zip(pattern_tokens, path_tokens)
            ):
                return rule
        return None

    def _hash_value(self, value: str) -> str:
        salt = self.rule_config.hash_salt or "privacy-proxy"
        return hashlib.sha256((salt + value).encode("utf-8")).hexdigest()

    @staticmethod
    def _mask_value(value: str, rule: Dict[str, Any]) -> str:
        visible = int(rule.get("visible", 3))
        mask_char = rule.get("mask_char", "*")
        if len(value) <= visible:
            return mask_char * len(value)
        return f"{mask_char * (len(value) - visible)}{value[-visible:]}"

    def _regex_detect(self, value: str) -> str | None:
        if EMAIL_REGEX.search(value):
            return "email_redacted"
        if PHONE_REGEX.search(value):
            return "phone_redacted"
        if MEDICARE_REGEX.search(value):
            return "medicare_redacted"
        if DOB_REGEX.search(value):
            return "dob_redacted"
        return None
