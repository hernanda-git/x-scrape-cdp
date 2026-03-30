"""Shared utilities for x-scrape-cdp."""

from __future__ import annotations


def preview_text(text: str, max_len: int = 100) -> str:
    """
    Preview text with single-line normalization and truncation.

    Args:
        text: The text to preview
        max_len: Maximum length before truncation

    Returns:
        Single-line text, truncated with ellipsis if needed
    """
    one_line = " ".join((text or "").split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"