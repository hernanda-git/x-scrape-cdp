from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path: Path) -> Path:
    path = tmp_path / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path
