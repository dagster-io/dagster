import abc
from typing import Mapping, Optional, Sequence, Set

from dagster import AssetKey
from dagster._core.definitions.auto_materialize_condition import AutoMaterializeAssetEvaluation
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.scheduler.instigation import (
    AutoMaterializeAssetEvaluationRecord,
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    TickData,
    TickStatus,
)
from dagster._core.storage.sql import AlembicVersion
from dagster._utils import PrintFn


class ScheduleStorage(abc.ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract class for managing persistance of scheduler artifacts."""

    @abc.abstractmethod
    def wipe(self) -> None:
        """Delete all schedules from storage."""

    @abc.abstractmethod
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional[InstigatorType] = None,
        instigator_statuses: Optional[Set[InstigatorStatus]] = None,
    ) -> Sequence[InstigatorState]:
        """Return all InstigationStates present in storage.

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            repository_selector_id (Optional[str]): The repository selector id to scope results to
            instigator_type (Optional[InstigatorType]): The InstigatorType to scope results to
            instigator_statuses (Optional[Set[InstigatorStatus]]): The InstigatorStatuses to scope results to
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
    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        """Delete a state in storage.

        Args:
            origin_id (str): The id of the instigator target to delete
            selector_id (str): The logical instigator identifier
        """

    @property
    def supports_batch_queries(self) -> bool:
        return False

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Mapping[str, Sequence[InstigatorTick]]:
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
    ) -> Sequence[InstigatorTick]:
        """Get the ticks for a given instigator.

        Args:
            origin_id (str): The id of the instigator target
            selector_id (str): The logical instigator identifier
        """

    @abc.abstractmethod
    def create_tick(self, tick_data: TickData) -> InstigatorTick:
        """Add a tick to storage.

        Args:
            tick_data (TickData): The tick to add
        """

    @abc.abstractmethod
    def update_tick(self, tick: InstigatorTick) -> InstigatorTick:
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
    ) -> None:
        """Wipe ticks for an instigator for a certain status and timestamp.

        Args:
            origin_id (str): The id of the instigator target to delete
            selector_id (str): The logical instigator identifier
            before (datetime): All ticks before this datetime will get purged
            tick_statuses (Optional[List[TickStatus]]): The tick statuses to wipe
        """

    @property
    def supports_auto_materialize_asset_evaluations(self) -> bool:
        return True

    @abc.abstractmethod
    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AutoMaterializeAssetEvaluation],
    ) -> None:
        """Add asset policy evaluations to storage."""

    @abc.abstractmethod
    def get_auto_materialize_asset_evaluations(
        self, asset_key: AssetKey, limit: int, cursor: Optional[int] = None
    ) -> Sequence[AutoMaterializeAssetEvaluationRecord]:
        """Get the policy evaluations for a given asset.

        Args:
            asset_key (AssetKey): The asset key to query
            limit (Optional[int]): The maximum number of evaluations to return
            cursor (Optional[int]): The cursor to paginate from
        """

    @abc.abstractmethod
    def purge_asset_evaluations(self, before: float) -> None:
        """Wipe evaluations before a certain timestamp.

        Args:
            before (datetime): All evaluations before this datetime will get purged
        """

    @abc.abstractmethod
    def upgrade(self) -> None:
        """Perform any needed migrations."""

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        """Call this method to run any required data migrations."""

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        """Call this method to run any optional data migrations for optimized reads."""

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        """Allows for optimizing database connection / use in the context of a long lived webserver process.
        """

    def alembic_version(self) -> Optional[AlembicVersion]:
        return None

    def dispose(self) -> None:
        """Explicit lifecycle management."""
