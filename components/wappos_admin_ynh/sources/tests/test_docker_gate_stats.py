from unittest.mock import MagicMock, patch

import pytest

import docker_gate as dg


@pytest.fixture
def sample_app(monkeypatch):
    entry = {"slug": "myapp", "container_name": "docker-gate-myapp"}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    return entry


def test_get_container_stats_unknown_app(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.get_container_stats("ghost")


def test_get_container_stats_container_not_found(sample_app):
    import docker as docker_lib
    fake_client = MagicMock()
    fake_client.containers.get.side_effect = docker_lib.errors.NotFound("nope")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        with pytest.raises(dg.DockerGateError):
            dg.get_container_stats("myapp")


def test_get_container_stats_stopped_container(sample_app):
    fake_container = MagicMock()
    fake_container.status = "exited"
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.get_container_stats("myapp")
    assert result == {"running": False}


def test_get_container_stats_computes_cpu_percent(sample_app):
    fake_container = MagicMock()
    fake_container.status = "running"
    fake_container.stats.return_value = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 2_000_000_000},
            "system_cpu_usage": 100_000_000_000,
            "online_cpus": 4,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 1_000_000_000},
            "system_cpu_usage": 90_000_000_000,
        },
        "memory_stats": {"usage": 50_000_000, "limit": 500_000_000},
        "networks": {
            "eth0": {"rx_bytes": 1000, "tx_bytes": 500},
            "eth1": {"rx_bytes": 200, "tx_bytes": 100},
        },
    }
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.get_container_stats("myapp")

    assert result["running"] is True
    cpu_delta = 2_000_000_000 - 1_000_000_000
    system_delta = 100_000_000_000 - 90_000_000_000
    expected_cpu_percent = (cpu_delta / system_delta) * 4 * 100
    assert result["cpu_percent"] == pytest.approx(expected_cpu_percent)
    assert result["mem_usage"] == 50_000_000
    assert result["mem_limit"] == 500_000_000
    assert result["rx_bytes"] == 1200
    assert result["tx_bytes"] == 600


def test_get_container_stats_zero_system_delta_returns_none_cpu(sample_app):
    fake_container = MagicMock()
    fake_container.status = "running"
    fake_container.stats.return_value = {
        "cpu_stats": {"cpu_usage": {"total_usage": 1000}, "system_cpu_usage": 5000, "online_cpus": 2},
        "precpu_stats": {"cpu_usage": {"total_usage": 1000}, "system_cpu_usage": 5000},
        "memory_stats": {"usage": 100, "limit": 200},
        "networks": {},
    }
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.get_container_stats("myapp")
    assert result["cpu_percent"] is None
    assert result["rx_bytes"] == 0
    assert result["tx_bytes"] == 0
