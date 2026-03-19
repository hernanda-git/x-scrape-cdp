from __future__ import annotations

import pytest


@pytest.mark.live
def test_live_placeholder():
    pytest.skip("Live smoke test placeholder.")
