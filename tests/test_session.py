from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestSession:
    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_on_login_flow(self):
        from x_scrape_cdp.session import is_logged_in

        page = MagicMock()
        page.url = "https://x.com/i/flow/login"
        page.locator = MagicMock(return_value=AsyncMock(count=AsyncMock(return_value=0)))

        result = await is_logged_in(page)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_false_on_username_input(self):
        from x_scrape_cdp.session import is_logged_in

        page = MagicMock()
        page.url = "https://x.com/home"
        page.locator = MagicMock()
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        page.locator.return_value = mock_locator

        result = await is_logged_in(page)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_returns_true_on_home_with_nav(self):
        from x_scrape_cdp.session import is_logged_in

        page = MagicMock()
        page.url = "https://x.com/home"

        # Create a locator that returns different counts for different selectors
        def locator_factory(selector):
            mock = AsyncMock()
            if "AppTabBar_Home_Link" in selector:
                mock.count = AsyncMock(return_value=1)
            else:
                mock.count = AsyncMock(return_value=0)
            return mock

        page.locator = locator_factory

        result = await is_logged_in(page)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_logged_in_profile_handle(self):
        from x_scrape_cdp.session import get_logged_in_profile_handle

        page = MagicMock()
        mock_link = MagicMock()
        mock_first = MagicMock()
        mock_first.get_attribute = AsyncMock(return_value="/testuser")
        mock_link.first = mock_first
        mock_link.count = AsyncMock(return_value=1)
        page.locator = MagicMock(return_value=mock_link)

        result = await get_logged_in_profile_handle(page)
        assert result == "testuser"

    @pytest.mark.asyncio
    async def test_get_logged_in_profile_handle_returns_none_on_no_link(self):
        from x_scrape_cdp.session import get_logged_in_profile_handle

        page = MagicMock()
        mock_link = AsyncMock()
        mock_link.count = AsyncMock(return_value=0)
        page.locator = MagicMock(return_value=mock_link)

        result = await get_logged_in_profile_handle(page)
        assert result is None