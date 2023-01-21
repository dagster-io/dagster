import abc
from typing import Callable, Iterable, Mapping, Optional, Sequence

from dagster._core.definitions.run_request import InstigatorType
from dagster._core.instance import MayHaveInstanceWeakref
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorTick,
    TickData,
    TickStatus,
)


class ScheduleStorage(abc.ABC, MayHaveInstanceWeakref):
    """Abstract class for managing persistance of scheduler artifacts."""

    @abc.abstractmethod
    def wipe(self):
        """Delete all schedules from storage."""

    @abc.abstractmethod
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional[InstigatorType] = None,
    ) -> Iterable[InstigatorState]:
        """Return all InstigationStates present in storage.

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            repository_selector_id (Optional[str]): The repository selector id to scope results to
            instigator_type (Optional[InstigatorType]): The InstigatorType to scope results to
        """

    @abc.abstractmethod
    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional[InstigatorState]:
        """Return the instigator state for the given id.

        Args:
            origin_id (str): The unique instigator identifier
            selector_id (str): The logical instigator identifier
        """

    @abc.abstractmethod
    def add_instigator_state(self, state: InstigatorState) -> InstigatorState:
        """Add an instigator state to storage.

        Args:
            state (InstigatorState): The state to add
        """

    @abc.abstractmethod
    def update_instigator_state(self, state: InstigatorState) -> InstigatorState:
        """Update an instigator state in storage.

        Args:
            state (InstigatorState): The state to update
        """

    @abc.abstractmethod
    def delete_instigator_state(self, origin_id: str, selector_id: str):
        """Delete a state in storage.

        Args:
            origin_id (str): The id of the instigator target to delete
            selector_id (str): The logical instigator identifier
        """

    @property
    def supports_batch_queries(self):
        return False

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Mapping[str, Iterable[InstigatorTick]]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Iterable[InstigatorTick]:
        """Get the ticks for a given instigator.

        Args:
            origin_id (str): The id of the instigator target
            selector_id (str): The logical instigator identifier
        """

    @abc.abstractmethod
    def create_tick(self, tick_data: TickData):
        """Add a tick to storage.

        Args:
            tick_data (TickData): The tick to add
        """

    @abc.abstractmethod
    def update_tick(self, tick: InstigatorTick):
        """Update a tick already in storage.

        Args:
            tick (InstigatorTick): The tick to update
        """

    @abc.abstractmethod
    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence[TickStatus]] = None,
    ):
        """Wipe ticks for an instigator for a certain status and timestamp.

        Args:
            origin_id (str): The id of the instigator target to delete
            selector_id (str): The logical instigator identifier
            before (datetime): All ticks before this datetime will get purged
            tick_statuses (Optional[List[TickStatus]]): The tick statuses to wipe
        """

    @abc.abstractmethod
    def upgrade(self):
        """Perform any needed migrations."""

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any required data migrations."""

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any optional data migrations for optimized reads."""

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process.
        """

    def alembic_version(self):
        return None

    def dispose(self):
        """Explicit lifecycle management."""
