from dlt.extract import DltResource
from dlt.pipeline.pipeline import Pipeline
from collections import abc
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterator, Union, List

from dagster import (
    AssetMaterialization,
    MaterializeResult,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet

from dagster._core.execution.context.asset_execution_context import (
    AssetExecutionContext,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from typing_extensions import TypeVar

# if TYPE_CHECKING:
#     from dagster_embedded_elt.dlt.resource import DagsterDltResource

DltEventType = Union[AssetMaterialization, MaterializeResult]
T = TypeVar("T", bound=DltEventType)


def fetch_row_count_metadata(
    materialization: DltEventType,
    context: Union[OpExecutionContext, AssetExecutionContext],
    # table_name: str,
    dlt_pipeline: Pipeline,
) -> Dict[str, Any]:
    if not materialization.metadata:
        raise Exception("Missing required metadata to retrieve row count.")
    jobs_metadata = materialization.metadata.get("jobs")
    if not jobs_metadata or not isinstance(jobs_metadata, list):
        raise Exception("Missing jobs metadata to retrieve row count.")
    table_name = jobs_metadata[0].get("table_name")

    try:
        with dlt_pipeline.sql_client() as client:
            with client.execute_query(
                f"select count(*) as row_count from {table_name}",
            ) as cursor:
                row_count_result = cursor.fetchone()
    # Filesystem does not have a SQL client and table might not be found
    except Exception as e:
        context.log.error(
            f"An error occurred while fetching row count for {table_name}. Row count metadata"
            " will not be included in the event.\n\n"
            f"Exception: {e}"
        )
    row_count = row_count_result[0] if row_count_result else None
    return {
        # output object may be a slice/partition, so we output different metadata keys based on
        # whether this output represents an entire table or just a slice/partition
        **(
            TableMetadataSet(
                partition_row_count=row_count
            )  # TODO: Should be the same as `rows_loaded`
            if context.has_partition_key
            else TableMetadataSet(row_count=row_count)
        )
    }


class DltEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of Dlt events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        context: Union[OpExecutionContext, AssetExecutionContext],
        # resource: DltResource,
        dlt_pipeline: Pipeline,
    ) -> None:
        self._inner_iterator = events
        self._context = context
        # self._resource = resource
        self._dlt_pipeline = dlt_pipeline

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "DltEventIterator[T]":
        return self

    @public
    @experimental
    def fetch_row_count(self) -> "DltEventIterator":
        """Fetches row count metadata for each resource loaded by dlt.

        Retrieves the row count for each resource.

        Returns:
            DltEventIterator: An iterator of Dagster events with row count metadata attached.
        """

        def _fetch_row_count() -> Iterator[T]:
            for event in self:
                row_count_metadata = fetch_row_count_metadata(
                    event,
                    context=self._context,
                    # table_name=str(self._resource.table_name),
                    dlt_pipeline=self._dlt_pipeline,
                )
                if event.metadata:
                    yield event._replace(
                        metadata={**row_count_metadata, **event.metadata}
                    )

        return DltEventIterator[T](
            _fetch_row_count(),
            self._context,
            # self._resource,
            self._dlt_pipeline,
        )
