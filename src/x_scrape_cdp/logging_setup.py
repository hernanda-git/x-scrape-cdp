from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format="%(asctime)s level=%(levelname)s name=%(name)s message=%(message)s",
    )
    return logging.getLogger("x_scrape_cdp")
