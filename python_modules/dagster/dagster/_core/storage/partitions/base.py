from abc import ABC, abstractmethod
from typing import Callable, Optional, Sequence

from dagster._core.instance import MayHaveInstanceWeakref


class PartitionsStorage(ABC, MayHaveInstanceWeakref):
    """Abstract class for managing persistence of runtime partitions."""

    @abstractmethod
    def get_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the list of partition keys for a partition definition."""
        raise NotImplementedError()

    @abstractmethod
    def has_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a partition exists."""
        raise NotImplementedError()

    @abstractmethod
    def add_partitions(self, partitions_def_name: str, partition_keys: Sequence[str]) -> None:
        """Add a partition for the specified partition definition."""
        raise NotImplementedError()

    @abstractmethod
    def delete_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a partition for the specified partition definition."""
        raise NotImplementedError()

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    def alembic_version(self):
        return None

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process.
        """

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any required data migrations."""
