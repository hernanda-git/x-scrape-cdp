from __future__ import annotations

import pytest

from x_scrape_cdp.utils import preview_text


class TestPreviewText:
    def test_empty_string(self):
        assert preview_text("") == ""

    def test_none_handling(self):
        assert preview_text(None) == ""

    def test_no_truncation_needed(self):
        result = preview_text("short text", max_len=100)
        assert result == "short text"

    def test_truncation_with_ellipsis(self):
        long_text = "a" * 150
        result = preview_text(long_text, max_len=100)
        assert len(result) == 100
        assert result.endswith("…")

    def test_multiline_normalized(self):
        result = preview_text("line1\n\n  line2   \t  line3", max_len=50)
        assert "\n" not in result
        assert "  " not in result

    def test_exact_length_unchanged(self):
        exact = "a" * 50
        result = preview_text(exact, max_len=50)
        assert result == exact