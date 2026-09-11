# Auteur : Patrick Ritaine
from datetime import datetime, timedelta

import app


def test_service_since_parses_iso_string():
    value = (datetime.now() - timedelta(minutes=3)).isoformat()
    result = app._service_since(value)
    assert "minute" in result
    assert "T" not in result


def test_service_since_parses_epoch_float():
    value = (datetime.now() - timedelta(hours=2)).timestamp()
    result = app._service_since(value)
    assert "hour" in result


def test_service_since_handles_unknown():
    assert app._service_since("unknown") == "unknown"
    assert app._service_since(None) == "unknown"


def test_service_since_handles_invalid_string():
    assert app._service_since("not-a-date") == "unknown"
