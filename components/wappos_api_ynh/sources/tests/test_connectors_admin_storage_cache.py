from __future__ import annotations
# Auteur : Patrick Ritaine

from unittest.mock import patch

import pytest

from wappos_api.connectors import admin


@pytest.fixture(autouse=True)
def _isolate_consumer_sizes_cache(tmp_path):
    cache_file = tmp_path / "consumer_sizes_cache.json"
    with patch.object(admin, "_CONSUMER_SIZES_CACHE_FILE", cache_file):
        yield cache_file


def test_cached_consumer_sizes_calls_du_only_once_within_ttl():
    with patch.object(admin, "_dir_size_bytes", return_value=1024) as mocked, \
         patch.object(admin.os.path, "isdir", return_value=True):
        first = admin._cached_consumer_sizes()
        second = admin._cached_consumer_sizes()

    assert first == second
    assert mocked.call_count == len(admin._CONSUMER_CANDIDATES)


def test_cached_consumer_sizes_is_shared_across_processes_via_file(_isolate_consumer_sizes_cache):
    with patch.object(admin, "_dir_size_bytes", return_value=1024), \
         patch.object(admin.os.path, "isdir", return_value=True):
        admin._cached_consumer_sizes()

    assert _isolate_consumer_sizes_cache.exists()

    with patch.object(admin, "_dir_size_bytes", return_value=9999) as mocked_second_worker:
        result = admin._cached_consumer_sizes()

    mocked_second_worker.assert_not_called()
    assert all(size == 1024 for _, _, size in result)


def test_cached_consumer_sizes_recomputes_after_ttl_expiry(_isolate_consumer_sizes_cache):
    with patch.object(admin, "_dir_size_bytes", return_value=1024), \
         patch.object(admin.os.path, "isdir", return_value=True):
        admin._cached_consumer_sizes()

    import json
    cached = json.loads(_isolate_consumer_sizes_cache.read_text())
    cached["fetched_at"] -= admin._CONSUMER_SIZES_CACHE_TTL_SECONDS + 1
    _isolate_consumer_sizes_cache.write_text(json.dumps(cached))

    with patch.object(admin, "_dir_size_bytes", return_value=2048) as mocked_again, \
         patch.object(admin.os.path, "isdir", return_value=True):
        result = admin._cached_consumer_sizes()

    assert mocked_again.call_count == len(admin._CONSUMER_CANDIDATES)
    assert all(size == 2048 for _, _, size in result)
