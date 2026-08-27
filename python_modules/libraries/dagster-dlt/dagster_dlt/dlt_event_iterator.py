from collections.abc import Iterator, Mapping
from typing import TypeAlias

from dagster import AssetMaterialization, MaterializeResult
from dagster._annotations import public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.metadata_value import JsonMetadataValue
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dlt import Pipeline
from typing_extensions import TypeVar

from dagster_dlt.metadata_set import DagsterDltMetadataSet

DltEventType: TypeAlias = AssetMaterialization | MaterializeResult
T = TypeVar("T", bound=DltEventType)


def _resolve_dlt_table_name(
    materialization: "DltEventType",
    context: OpExecutionContext | AssetExecutionContext,
) -> str | None:
    """Resolve the destination table name for a materialized dlt resource.

    Prefer the ``dagster-dlt`` metadata attached to the asset spec at definition time so the table
    can be counted even on an incremental run that loaded no new rows (which produces no dlt load
    jobs). Outside of an asset definition (e.g. op-based usage) there is no spec, so fall back to
    the run's load jobs.
    """
    if isinstance(context, AssetExecutionContext) and context.has_assets_def:
        spec_metadata = context.assets_def.metadata_by_key.get(materialization.asset_key)
        if spec_metadata:
            table_name = DagsterDltMetadataSet.extract(spec_metadata).table_name
            if table_name:
                return table_name

    jobs = DagsterDltMetadataSet.extract(materialization.metadata or {}).jobs
    if isinstance(jobs, JsonMetadataValue) and isinstance(jobs.value, list) and jobs.value:
        first_job = jobs.value[0]
        if isinstance(first_job, Mapping):
            return first_job.get("table_name")
    return None


def _fetch_row_count(
    dlt_pipeline: Pipeline,
    table_name: str,
) -> int | None:
    """Fetch the total row count for a table using dlt's built-in dataset interface.

    Uses ``pipeline.dataset().row_counts(...)`` so that dlt handles destination-specific query
    building (identifier quoting, dialects) and destinations without a raw SQL client (e.g.
    filesystem).
    """
    # ``row_counts`` returns a relation yielding ``(table_name, row_count)`` rows.
    result = dlt_pipeline.dataset().row_counts(table_names=[table_name]).fetchone()
    if result is not None and isinstance(result[1], int):
        return result[1]
    return None


def fetch_row_count_metadata(
    materialization: DltEventType,
    context: OpExecutionContext | AssetExecutionContext,
    dlt_pipeline: Pipeline,
) -> TableMetadataSet:
    if not materialization.metadata:
        raise Exception("Missing required metadata to retrieve row count.")
    if context.has_partition_key:
        # ``rows_loaded`` is the number of rows loaded this run, i.e. the partition's row count.
        rows_loaded = DagsterDltMetadataSet.extract(materialization.metadata).rows_loaded
        return TableMetadataSet(partition_row_count=rows_loaded if rows_loaded is not None else 0)

    table_name = _resolve_dlt_table_name(materialization, context)
    if table_name is None:
        return TableMetadataSet(row_count=None)
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
        context: OpExecutionContext | AssetExecutionContext,
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
                    dlt_pipeline=self._dlt_pipeline,
                )
                if event.metadata:
                    yield event._replace(metadata={**row_count_metadata, **event.metadata})  # ty: ignore[invalid-argument-type, invalid-yield]

        return DltEventIterator[T](
            _fetch_row_count(),
            self._context,
            self._dlt_pipeline,
        )
