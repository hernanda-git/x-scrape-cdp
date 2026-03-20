from __future__ import annotations

import asyncio
import logging

import typer

from .config import load_settings
from .logging_setup import configure_logging
from .loop import run_listener, run_once
from .loop import validate_session as validate_session_conn

app = typer.Typer(help="X CDP listener CLI")
logger = logging.getLogger("x_scrape_cdp.cli")


@app.command("validate-session")
def validate_session_cmd(
    config: str | None = typer.Option(default=None, help="Path to config yaml"),
) -> None:
    asyncio.run(_validate_session_async(config))


async def _validate_session_async(config: str | None) -> None:
    configure_logging()
    settings = load_settings(config)
    ok = await validate_session_conn(settings)
    if ok:
        logger.info("session_validated status=ok cdp_url=%s", settings.cdp_http_url)
        typer.echo("Session is valid.")
    else:
        logger.error("session_invalid reason=not_logged_in cdp_url=%s", settings.cdp_http_url)
        typer.echo("Session is not valid. Re-login with the selected user-data-dir.", err=True)
        raise typer.Exit(code=1)


@app.command("once")
def once(config: str | None = typer.Option(default=None, help="Path to config yaml")) -> None:
    asyncio.run(_once_async(config))


async def _once_async(config: str | None) -> None:
    configure_logging()
    settings = load_settings(config)
    new_total, _new_posts = await run_once(settings)
    typer.echo(f"Completed once cycle. New posts: {new_total}")


@app.command("run")
def run(config: str | None = typer.Option(default=None, help="Path to config yaml")) -> None:
    try:
        asyncio.run(_run_async(config))
    except KeyboardInterrupt:
        typer.echo("Shutting down gracefully.")


async def _run_async(config: str | None) -> None:
    configure_logging()
    settings = load_settings(config)
    await run_listener(settings)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
