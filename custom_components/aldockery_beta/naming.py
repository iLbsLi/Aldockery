"""Helpers for Aldockery entity naming."""
from __future__ import annotations

import re
import unicodedata


def slugify_part(value: str) -> str:
    """Convert a display string into a safe entity-id fragment."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "unknown"


def host_slug(host_name: str) -> str:
    return slugify_part(host_name)


def container_slug(container_name: str) -> str:
    return slugify_part(container_name)


def switch_unique_id(entry_id: str, host_name: str, container_name: str) -> str:
    return f"aldockery_beta:{entry_id}:switch:{host_slug(host_name)}:{container_slug(container_name)}"


def button_unique_id(entry_id: str, host_name: str, container_name: str, action: str) -> str:
    return f"aldockery_beta:{entry_id}:button:{host_slug(host_name)}:{container_slug(container_name)}:{slugify_part(action)}"


def switch_suggested_object_id(container_name: str) -> str:
    return container_slug(container_name)


def button_suggested_object_id(container_name: str, action: str) -> str:
    return f"{container_slug(container_name)}_{slugify_part(action)}"
