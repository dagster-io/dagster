from contextlib import contextmanager

import pytest
from dagster._core.errors import DagsterInvalidInvocationError
from dagster_postgres.event_log import PostgresEventLogStorage


class _RecordingConnection:
    def __init__(self) -> None:
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)


def _build_storage(
    connection: _RecordingConnection, supports_display_labels: bool
) -> PostgresEventLogStorage:
    storage = PostgresEventLogStorage.__new__(PostgresEventLogStorage)
    storage.__dict__["has_dynamic_partition_display_label_col"] = supports_display_labels
    storage._check_partitions_table = lambda: None  # noqa: SLF001

    @contextmanager
    def _index_connection():
        yield connection

    storage.index_connection = _index_connection  # type: ignore[method-assign]
    return storage


def test_add_dynamic_partitions_accepts_labels_and_updates_labels():
    connection = _RecordingConnection()
    storage = _build_storage(connection, supports_display_labels=True)

    storage.add_dynamic_partitions("foo", ["foo", "bar"], labels={"foo": "Foo label"})

    assert [statement.__visit_name__ for statement in connection.statements] == [
        "insert",
        "update",
    ]


def test_add_dynamic_partitions_checks_label_column_migration():
    storage = _build_storage(_RecordingConnection(), supports_display_labels=False)

    def _check_dynamic_partition_label_column():
        raise DagsterInvalidInvocationError(
            "Dynamic partition labels require a database schema migration."
        )

    storage._check_dynamic_partition_label_column = _check_dynamic_partition_label_column  # noqa: SLF001

    with pytest.raises(DagsterInvalidInvocationError, match="database schema migration"):
        storage.add_dynamic_partitions("foo", ["bar"], labels={"bar": "Bar label"})


def test_add_dynamic_partitions_checks_label_column_migration_for_empty_partition_keys():
    storage = _build_storage(_RecordingConnection(), supports_display_labels=False)

    def _check_dynamic_partition_label_column():
        raise DagsterInvalidInvocationError(
            "Dynamic partition labels require a database schema migration."
        )

    storage._check_dynamic_partition_label_column = _check_dynamic_partition_label_column  # noqa: SLF001

    with pytest.raises(DagsterInvalidInvocationError, match="database schema migration"):
        storage.add_dynamic_partitions("foo", [], labels={"bar": "Bar label"})


def test_add_dynamic_partitions_noops_for_empty_partition_keys_without_labels():
    connection = _RecordingConnection()
    storage = _build_storage(connection, supports_display_labels=False)

    storage.add_dynamic_partitions("foo", [])

    assert connection.statements == []
