"""Shared pytest configuration for ClickHouse integration tests (Docker + testcontainers)."""

from dagster_clickhouse_tests.fixtures import clickhouse_connection

__all__ = ["clickhouse_connection"]


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests that require Docker and a real ClickHouse container",
    )
