from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestStealth:
    def test_stealth_profile_dataclass(self):
        from x_scrape_cdp.stealth import StealthProfile

        profile = StealthProfile(
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Test UA",
            jitter_percent=10
        )

        assert profile.viewport_width == 1920
        assert profile.viewport_height == 1080
        assert profile.user_agent == "Test UA"
        assert profile.jitter_percent == 10

    def test_jitter_returns_positive_value(self):
        from x_scrape_cdp.stealth import _jitter

        with patch("x_scrape_cdp.stealth.random") as mock_random:
            mock_random.randint = MagicMock(return_value=50)

            result = _jitter(1000, 10)
            assert result >= 200  # Minimum is 200
            assert result <= 1050

    @pytest.mark.asyncio
    async def test_apply_stealth_sets_viewport(self):
        from x_scrape_cdp.stealth import apply_stealth, StealthProfile

        page = MagicMock()
        page.set_viewport_size = AsyncMock()
        page.set_extra_http_headers = AsyncMock()
        page.add_init_script = AsyncMock()

        profile = StealthProfile(
            viewport_width=1920,
            viewport_height=1080,
            jitter_percent=0  # No jitter for predictable test
        )

        with patch("x_scrape_cdp.stealth.random") as mock_random:
            mock_random.randint = MagicMock(return_value=0)

            await apply_stealth(page, profile)

            page.set_viewport_size.assert_called_once_with({"width": 1920, "height": 1080})

    @pytest.mark.asyncio
    async def test_apply_stealth_sets_user_agent(self):
        from x_scrape_cdp.stealth import apply_stealth, StealthProfile

        page = MagicMock()
        page.set_viewport_size = AsyncMock()
        page.set_extra_http_headers = AsyncMock()
        page.add_init_script = AsyncMock()

        profile = StealthProfile(
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Custom UA/1.0",
            jitter_percent=0
        )

        with patch("x_scrape_cdp.stealth.random") as mock_random:
            mock_random.randint = MagicMock(return_value=0)

            await apply_stealth(page, profile)

            page.set_extra_http_headers.assert_called_once_with({"User-Agent": "Custom UA/1.0"})

    @pytest.mark.asyncio
    async def test_apply_stealth_adds_init_script(self):
        from x_scrape_cdp.stealth import apply_stealth, StealthProfile

        page = MagicMock()
        page.set_viewport_size = AsyncMock()
        page.set_extra_http_headers = AsyncMock()
        page.add_init_script = AsyncMock()

        profile = StealthProfile(
            viewport_width=1920,
            viewport_height=1080,
            jitter_percent=0
        )

        with patch("x_scrape_cdp.stealth.random") as mock_random:
            mock_random.randint = MagicMock(return_value=0)

            await apply_stealth(page, profile)

            page.add_init_script.assert_called_once()
            # Verify the script contains webdriver override
            call_args = page.add_init_script.call_args[0][0]
            assert "webdriver" in call_args