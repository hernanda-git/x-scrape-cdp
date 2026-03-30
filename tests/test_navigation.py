from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestNavigation:
    @pytest.mark.asyncio
    async def test_open_profile_without_replies(self):
        from x_scrape_cdp.navigation import open_profile

        page = MagicMock()
        page.goto = AsyncMock()

        await open_profile(page, "testuser")

        page.goto.assert_called_once_with(
            "https://x.com/testuser",
            wait_until="domcontentloaded"
        )

    @pytest.mark.asyncio
    async def test_open_profile_with_replies(self):
        from x_scrape_cdp.navigation import open_profile

        page = MagicMock()
        page.goto = AsyncMock()

        await open_profile(page, "testuser", replies=True)

        page.goto.assert_called_once_with(
            "https://x.com/testuser/with_replies",
            wait_until="domcontentloaded"
        )

    @pytest.mark.asyncio
    async def test_open_profile_custom_wait(self):
        from x_scrape_cdp.navigation import open_profile

        page = MagicMock()
        page.goto = AsyncMock()

        await open_profile(page, "testuser", wait_until="networkidle")

        page.goto.assert_called_once_with(
            "https://x.com/testuser",
            wait_until="networkidle"
        )

    @pytest.mark.asyncio
    async def test_human_warmup_calls_mouse_methods(self):
        from x_scrape_cdp.navigation import human_warmup

        page = MagicMock()
        page.mouse = MagicMock()
        page.mouse.move = AsyncMock()
        page.mouse.wheel = AsyncMock()

        with patch("x_scrape_cdp.navigation.random") as mock_random:
            mock_random.randint = MagicMock(side_effect=[100, 200, 5, 150])
            mock_random.uniform = MagicMock(side_effect=[0.5, 0.6])

            await human_warmup(page)

            page.mouse.move.assert_called_once()
            page.mouse.wheel.assert_called_once()

    @pytest.mark.asyncio
    async def test_gentle_scroll_performs_rounds(self):
        from x_scrape_cdp.navigation import gentle_scroll_for_fresh_posts

        page = MagicMock()
        page.mouse = MagicMock()
        page.mouse.wheel = AsyncMock()

        with patch("x_scrape_cdp.navigation.random") as mock_random:
            mock_random.randint = MagicMock(side_effect=[800, 3.0] * 3)
            mock_random.uniform = MagicMock(return_value=3.0)

            await gentle_scroll_for_fresh_posts(page, rounds=3, pause_range_sec=(2.0, 4.0))

            assert page.mouse.wheel.call_count == 3