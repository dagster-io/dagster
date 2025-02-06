from collections.abc import Iterator
from typing import Optional, Union

from dagster import AssetMaterialization, MaterializeResult
from dagster._annotations import public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dlt import Pipeline
from typing_extensions import TypeVar

DltEventType = Union[AssetMaterialization, MaterializeResult]
T = TypeVar("T", bound=DltEventType)


def _fetch_row_count(
    dlt_pipeline: Pipeline,
    table_name: str,
) -> Optional[int]:
    """Exists mostly for ease of testing."""
    with dlt_pipeline.sql_client() as client:
        with client.execute_query(
            f"select count(*) as row_count from {table_name}",
        ) as cursor:
            result = cursor.fetchone()
            if result is not None and isinstance(result[0], int):
                return result[0]
            else:
                return None


def fetch_row_count_metadata(
    materialization: DltEventType,
    context: Union[OpExecutionContext, AssetExecutionContext],
    dlt_pipeline: Pipeline,
) -> TableMetadataSet:
    if not materialization.metadata:
        raise Exception("Missing required metadata to retrieve row count.")
    if context.has_partition_key:
        rows_loaded = materialization.metadata.get("rows_loaded")
        return TableMetadataSet(
            partition_row_count=rows_loaded.value if rows_loaded else 0  # type: ignore
        )

    jobs_metadata = materialization.metadata.get("jobs")
    if not jobs_metadata or not isinstance(jobs_metadata, list):
        raise Exception("Missing jobs metadata to retrieve row count.")
    table_name = jobs_metadata[0].get("table_name")
    try:
        return TableMetadataSet(row_count=_fetch_row_count(dlt_pipeline, table_name))
    # Filesystem does not have a SQL client and table might not be found
    except Exception as e:
        context.log.error(
            f"An error occurred while fetching row count for {table_name}. Row count metadata"
            " will not be included in the event.\n\n"
            f"Exception: {e}"
        )
        return TableMetadataSet(row_count=None)


class DltEventIterator(Iterator[T]):
    """A wrapper around an iterator of Dlt events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        context: Union[OpExecutionContext, AssetExecutionContext],
        dlt_pipeline: Pipeline,
    ) -> None:
        self._inner_iterator = events
        self._context = context
        self._dlt_pipeline = dlt_pipeline

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "DltEventIterator[T]":
        return self

    @public
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
                    yield event._replace(metadata={**row_count_metadata, **event.metadata})

        return DltEventIterator[T](
            _fetch_row_count(),
            self._context,
            self._dlt_pipeline,
        )
