.PHONY: lint test run-once

lint:
	python -m ruff check src tests

test:
	python -m pytest -m "not live"

run-once:
	python -m x_scrape_cdp.cli once
