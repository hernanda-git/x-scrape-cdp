from __future__ import annotations

import logging
import os


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    # Playwright spawns Node processes that can emit noisy deprecation warnings.
    # Keep terminal output focused on listener events unless user overrides it.
    os.environ.setdefault("NODE_OPTIONS", "--no-deprecation")

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    return logging.getLogger("x_scrape_cdp")
