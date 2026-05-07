"""Re-export ClickHouse session fixtures from ``dagster-clickhouse`` (no ``pytest_plugins``).

Importing the fixture from ``dagster_clickhouse_tests.fixtures`` avoids registering
``dagster_clickhouse_tests.conftest`` as a pytest plugin twice when running
``pytest`` across multiple packages in one session.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent / "dagster-clickhouse"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dagster_clickhouse_tests.fixtures import clickhouse_connection  # ty: ignore[unresolved-import]

__all__ = ["clickhouse_connection"]


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests that require Docker and a real ClickHouse container",
    )
