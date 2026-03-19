from __future__ import annotations

from x_scrape_cdp.state import should_reset_listener_data


def test_no_reset_on_first_run():
    assert should_reset_listener_data({}, "cfg1", "user1") is False


def test_reset_when_config_fingerprint_changes():
    assert (
        should_reset_listener_data({"config_fingerprint": "old"}, "new", "user1") is True
    )


def test_reset_when_session_handle_changes():
    assert (
        should_reset_listener_data(
            {"config_fingerprint": "same", "session_handle": "a"},
            "same",
            "b",
        )
        is True
    )


def test_no_reset_when_session_unknown():
    assert (
        should_reset_listener_data(
            {"config_fingerprint": "same", "session_handle": "a"},
            "same",
            None,
        )
        is False
    )
