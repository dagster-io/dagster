import abc
from typing import Iterable

from dagster.core.definitions.run_request import InstigatorType
from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.scheduler.instigation import InstigatorState, InstigatorTick, TickData, TickStatus


class ScheduleStorage(abc.ABC, MayHaveInstanceWeakref):
    """Abstract class for managing persistance of scheduler artifacts"""

    @abc.abstractmethod
    def wipe(self):
        """Delete all schedules from storage"""

    @abc.abstractmethod
    def all_instigator_state(
        self, repository_origin_id: str = None, instigator_type: InstigatorType = None
    ) -> Iterable[InstigatorState]:
        """Return all InstigationStates present in storage

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            instigator_type (Optional[InstigatorType]): The InstigatorType to scope results to
        """

    @abc.abstractmethod
    def get_instigator_state(self, origin_id: str) -> InstigatorState:
        """Return the instigator state for the given id

        Args:
            origin_id (str): The unique instigator identifier
        """

    @abc.abstractmethod
    def add_instigator_state(self, state: InstigatorState):
        """Add an instigator state to storage.

        Args:
            state (InstigatorState): The state to add
        """

    @abc.abstractmethod
    def update_instigator_state(self, state: InstigatorState):
        """Update an instigator state in storage.

        Args:
            state (InstigatorState): The state to update
        """

    @abc.abstractmethod
    def delete_instigator_state(self, origin_id: str):
        """Delete a state in storage.

        Args:
            origin_id (str): The id of the instigator target to delete
        """

    @abc.abstractmethod
    def get_ticks(
        self, origin_id: str, before: float = None, after: float = None, limit: int = None
    ) -> Iterable[InstigatorTick]:
        """Get the ticks for a given instigator.

        Args:
            origin_id (str): The id of the instigator target
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
    def purge_ticks(self, origin_id: str, tick_status: TickStatus, before: float):
        """Wipe ticks for an instigator for a certain status and timestamp.

        Args:
            origin_id (str): The id of the instigator target to delete
            tick_status (TickStatus): The tick status to wipe
            before (datetime): All ticks before this datetime will get purged
        """

    @abc.abstractmethod
    def get_tick_stats(self, origin_id: str):
        """Get tick stats for a given instigator.

        Args:
            origin_id (str): The id of the instigator target
        """

    @abc.abstractmethod
    def upgrade(self):
        """Perform any needed migrations"""

    def optimize_for_dagit(self, statement_timeout: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""
