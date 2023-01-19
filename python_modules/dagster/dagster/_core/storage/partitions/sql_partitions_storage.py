from abc import ABC, abstractmethod
from typing import Callable, Iterable, Mapping, Optional, Sequence
from dagster._core.utils import check
from dagster._core.instance import MayHaveInstanceWeakref
from dagster._core.errors import DagsterInvalidInvocationError
from .base import PartitionsStorage
from dagster._core.storage.partitions.schema import RuntimePartitions
import sqlalchemy as db


class SqlPartitionsStorage(PartitionsStorage):
    @abstractmethod
    def connect(self):
        """Return a connection to the index database."""

    @abstractmethod
    def has_table(self, table_name: str) -> bool:
        """This method checks if a table exists in the database."""

    def _check_partitions_table(self):
        if not self.has_table("runtime_partitions"):
            raise DagsterInvalidInvocationError(
                "Cannot add partitions to non-existent table. Add this table by running `dagster"
                " instance migrate`."
            )

    def _fetch_partition_keys_for_partition_def(self, partitions_def_name: str) -> Sequence[str]:
        columns = [
            RuntimePartitions.c.partitions_def_name,
            RuntimePartitions.c.partition_key,
        ]
        query = db.select(columns).where(
            RuntimePartitions.c.partitions_def_name == partitions_def_name
        )
        with self.connect() as conn:
            rows = conn.execute(query).fetchall()

        return [row[1] for row in rows]

    def get_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the list of partition keys for a partition definition."""
        self._check_partitions_table()
        return self._fetch_partition_keys_for_partition_def(partitions_def_name)

    def has_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a partition exists."""
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_key")
        self._check_partitions_table()
        return partition_key in self._fetch_partition_keys_for_partition_def(partitions_def_name)

    def add_partitions(self, partitions_def_name: str, partition_keys: Sequence[str]) -> None:
        """Add a partition for the specified partition definition."""
        check.str_param(partitions_def_name, "partitions_def_name")
        check.sequence_param(partition_keys, "partition_keys")
        self._check_partitions_table()
        existing_partitions = set(self.get_partitions(partitions_def_name))

        new_keys = list(set(partition_keys) - existing_partitions)
        if new_keys:
            with self.connect() as conn:
                conn.execute(
                    RuntimePartitions.insert(),
                    [
                        dict(partitions_def_name=partitions_def_name, partition_key=partition_key)
                        for partition_key in new_keys
                    ],
                )

    def delete_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a partition for the specified partition definition."""
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_keys")
        self._check_partitions_table()
        with self.connect() as conn:
            conn.execute(
                RuntimePartitions.delete().where(
                    RuntimePartitions.c.partitions_def_name == partitions_def_name,
                    RuntimePartitions.c.partition_key == partition_key,
                )
            )

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    def alembic_version(self):
        return None
