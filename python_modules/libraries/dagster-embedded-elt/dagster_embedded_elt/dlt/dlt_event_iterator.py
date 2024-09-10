import re
from collections import abc
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterator, Optional, Sequence, Union, cast

from dagster import (
    AssetMaterialization,
    MaterializeResult,
    _check as check,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from dagster_embedded_elt.dlt.resources import DltResource

DltEventType = Union[AssetMaterialization, MaterializeResult]

def fetch_row_count():
    try:
        with dlt_pipeline.sql_client() as client:
            with client.execute_query(
                f"""
                    SELECT
                    count(*) as row_count
                    FROM
                    {resource.table_name}
                """,
            ) as cursor:
                row_count_result = cursor.fetchone()
    # Filesystem does not have a SQL client and table might not be found
    except Exception as e:
        context.log.error(
            f"An error occurred while fetching row count for {resource.table_name}. Row count metadata"
            " will not be included in the event.\n\n"
            f"Exception: {e}"
        )
    # Need to use 'partition_row_count' for partitioned assets
    row_count = None
    if row_count_result and not context.has_partition_key:
        row_count = row_count_result[0]

class DltEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of Dlt events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        sling_cli: "DltResource",
        replication_config: Dict[str, Any],
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> None:
        self._inner_iterator = events
        self._sling_cli = sling_cli
        self._replication_config = replication_config
        self._context = context

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "DltEventIterator[T]":
        return self

    @public
    @experimental
    def fetch_row_counts(
        self,
    ) -> (
        "DltEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Experimental functionality which will fetch row counts for materialized dlt
        resources in a dlt run once they are ran.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events for dbt models, with row counts attached,
                yielded in the order they are emitted by dbt.
        """

        def _fetch_row_counts() -> Iterator[T]:
            for event in self:
                col_metadata = fetch_row_count(
                    event, self._sling_cli, self._replication_config, self._context
                )
                if event.metadata:
                    yield event._replace(metadata={**col_metadata, **event.metadata})

        return DltEventIterator[T](
            _fetch_row_counts(), self._sling_cli, self._replication_config, self._context
        )
