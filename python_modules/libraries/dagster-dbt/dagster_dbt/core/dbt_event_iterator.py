from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AssetObservation,
    Output,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.metadata import TableMetadataSet, TextMetadataValue
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._core.utils import exhaust_iterator_and_yield_results_with_exception, imap
from typing_extensions import TypeVar

from dagster_dbt.asset_utils import default_metadata_from_dbt_resource_props
from dagster_dbt.core.dbt_cli_event import EventHistoryMetadata, _build_column_lineage_metadata

if TYPE_CHECKING:
    from dagster_dbt.core.dbt_cli_invocation import DbtCliInvocation


logger = get_dagster_logger()

DbtDagsterEventType = Union[
    Output, AssetMaterialization, AssetCheckResult, AssetObservation, AssetCheckEvaluation
]

# We define DbtEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `DbtCliInvocation.stream()`
# will be able to see the inner type of the iterator, rather than just `DbtEventIterator`.
T = TypeVar("T", bound=DbtDagsterEventType)


def _get_dbt_resource_props_from_event(
    invocation: "DbtCliInvocation", event: DbtDagsterEventType
) -> dict[str, Any]:
    unique_id = cast(TextMetadataValue, event.metadata["unique_id"]).text
    return check.not_none(invocation.manifest["nodes"].get(unique_id))


def _fetch_column_metadata(
    invocation: "DbtCliInvocation", event: DbtDagsterEventType, with_column_lineage: bool
) -> Optional[dict[str, Any]]:
    """Threaded task which fetches column schema and lineage metadata for dbt models in a dbt
    run once they are built, returning the metadata to be attached.

    First we use the dbt adapter to obtain the column metadata for the built model. Then we
    retrieve the column metadata for the model's parent models, if they exist. Finally, we
    build the column lineage metadata for the model and attach it to the event.

    Args:
        invocation (DbtCliInvocation): The dbt CLI invocation.
        event (DbtDagsterEventType): The dbt event to append column metadata to.
        with_column_lineage (bool): Whether to include column lineage metadata in the event.
    """
    adapter = check.not_none(invocation.adapter)

    dbt_resource_props = _get_dbt_resource_props_from_event(invocation, event)

    with adapter.connection_named(f"column_metadata_{dbt_resource_props['unique_id']}"):
        try:
            cols = invocation._get_columns_from_dbt_resource_props(  # noqa: SLF001
                adapter=adapter, dbt_resource_props=dbt_resource_props
            ).columns
        except Exception as e:
            logger.warning(
                "An error occurred while fetching column schema metadata for the dbt resource"
                f" `{dbt_resource_props['original_file_path']}`."
                " Column metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )
            return {}

        schema_metadata = {}
        try:
            column_schema_data = {col.name: {"data_type": col.data_type} for col in cols}
            col_data = {"columns": column_schema_data}
            schema_metadata = default_metadata_from_dbt_resource_props(col_data)
        except Exception as e:
            logger.warning(
                "An error occurred while building column schema metadata from data"
                f" `{col_data}` for the dbt resource"  # pyright: ignore[reportPossiblyUnboundVariable]
                f" `{dbt_resource_props['original_file_path']}`."
                " Column schema metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )

        lineage_metadata = {}
        if with_column_lineage:
            try:
                parents = {}
                parent_unique_ids = invocation.manifest["parent_map"].get(
                    dbt_resource_props["unique_id"], []
                )
                for parent_unique_id in parent_unique_ids:
                    dbt_parent_resource_props = invocation.manifest["nodes"].get(
                        parent_unique_id
                    ) or invocation.manifest["sources"].get(parent_unique_id)

                    parent_name, parent_columns = invocation._get_columns_from_dbt_resource_props(  # noqa: SLF001
                        adapter=adapter, dbt_resource_props=dbt_parent_resource_props
                    )

                    parents[parent_name] = {
                        col.name: {"data_type": col.data_type} for col in parent_columns
                    }

                lineage_metadata = _build_column_lineage_metadata(
                    event_history_metadata=EventHistoryMetadata(
                        columns=column_schema_data,  # pyright: ignore[reportPossiblyUnboundVariable]
                        parents=parents,
                    ),
                    dbt_resource_props=dbt_resource_props,
                    manifest=invocation.manifest,
                    dagster_dbt_translator=invocation.dagster_dbt_translator,
                    target_path=invocation.target_path,
                )

            except Exception as e:
                logger.warning(
                    "An error occurred while building column lineage metadata for the dbt resource"
                    f" `{dbt_resource_props['original_file_path']}`."
                    " Lineage metadata will not be included in the event.\n\n"
                    f"Exception: {e}",
                    exc_info=True,
                )

        return {
            **schema_metadata,
            **lineage_metadata,
        }


def _fetch_row_count_metadata(
    invocation: "DbtCliInvocation",
    event: DbtDagsterEventType,
) -> Optional[dict[str, Any]]:
    """Threaded task which fetches row counts for materialized dbt models in a dbt run
    once they are built, and attaches the row count as metadata to the event.
    """
    if not isinstance(event, (AssetMaterialization, Output)):
        return None

    adapter = check.not_none(invocation.adapter)

    dbt_resource_props = _get_dbt_resource_props_from_event(invocation, event)
    is_view = dbt_resource_props["config"]["materialized"] == "view"

    # Avoid counting rows for views, since they may include complex SQL queries
    # that are costly to execute. We can revisit this in the future if there is
    # a demand for it.
    if is_view:
        return None

    unique_id = dbt_resource_props["unique_id"]
    logger.debug("Fetching row count for %s", unique_id)
    relation_name = dbt_resource_props["relation_name"]

    try:
        with adapter.connection_named(f"row_count_{unique_id}"):
            query_result = adapter.execute(
                f"""
                    SELECT
                    count(*) as row_count
                    FROM
                    {relation_name}
                """,
                fetch=True,
            )
        query_result_table = query_result[1]
        # some adapters do not output the column names, so we need
        # to index by position
        row_count = query_result_table[0][0]
        return {**TableMetadataSet(row_count=row_count)}

    except Exception as e:
        logger.exception(
            f"An error occurred while fetching row count for {unique_id}. Row count metadata"
            " will not be included in the event.\n\n"
            f"Exception: {e}"
        )
        return None


class DbtEventIterator(Iterator[T]):
    """A wrapper around an iterator of dbt events which contains additional methods for
    post-processing the events, such as fetching row counts for materialized tables.
    """

    def __init__(
        self,
        events: Iterator[T],
        dbt_cli_invocation: "DbtCliInvocation",
    ) -> None:
        self._inner_iterator = events
        self._dbt_cli_invocation = dbt_cli_invocation

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "DbtEventIterator[T]":
        return self

    @public
    def fetch_row_counts(
        self,
    ) -> "DbtEventIterator[Union[Output, AssetMaterialization, AssetCheckResult, AssetObservation, AssetCheckEvaluation]]":
        """Functionality which will fetch row counts for materialized dbt
        models in a dbt run once they are built. Note that row counts will not be fetched
        for views, since this requires running the view's SQL query which may be costly.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]:
                A set of corresponding Dagster events for dbt models, with row counts attached,
                yielded in the order they are emitted by dbt.
        """
        return self._attach_metadata(_fetch_row_count_metadata)

    @public
    def fetch_column_metadata(
        self,
        with_column_lineage: bool = True,
    ) -> "DbtEventIterator[Union[Output, AssetMaterialization, AssetCheckResult, AssetObservation, AssetCheckEvaluation]]":
        """Functionality which will fetch column schema metadata for dbt models in a run
        once they're built. It will also fetch schema information for upstream models and generate
        column lineage metadata using sqlglot, if enabled.

        Args:
            generate_column_lineage (bool): Whether to generate column lineage metadata using sqlglot.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]:
                A set of corresponding Dagster events for dbt models, with column metadata attached,
                yielded in the order they are emitted by dbt.
        """
        fetch_metadata = lambda invocation, event: _fetch_column_metadata(
            invocation, event, with_column_lineage
        )
        return self._attach_metadata(fetch_metadata)

    def _attach_metadata(
        self,
        fn: Callable[["DbtCliInvocation", DbtDagsterEventType], Optional[dict[str, Any]]],
    ) -> "DbtEventIterator[DbtDagsterEventType]":
        """Runs a threaded task to attach metadata to each event in the iterator.

        Args:
            fn (Callable[[DbtCliInvocation, DbtDagsterEventType], Optional[Dict[str, Any]]]):
                A function which takes a DbtCliInvocation and a DbtDagsterEventType and returns
                a dictionary of metadata to attach to the event.

        Returns:
             Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events for dbt models, with any metadata output
                by the function attached, yielded in the order they are emitted by dbt.
        """

        def _map_fn(event: DbtDagsterEventType) -> DbtDagsterEventType:
            result = fn(self._dbt_cli_invocation, event)
            if result is None:
                return event

            return event.with_metadata({**event.metadata, **result})

        # If the adapter is DuckDB, we need to wait for the dbt CLI process to complete
        # so that the DuckDB lock is released. This is because DuckDB does not allow for
        # opening multiple connections to the same database when a write connection, such
        # as the one dbt uses, is open.
        event_stream = self
        if (
            self._dbt_cli_invocation.adapter
            and self._dbt_cli_invocation.adapter.__class__.__name__ == "DuckDBAdapter"
        ):
            from dbt.adapters.duckdb import DuckDBAdapter

            if isinstance(self._dbt_cli_invocation.adapter, DuckDBAdapter):
                event_stream = exhaust_iterator_and_yield_results_with_exception(self)

        def _threadpool_wrap_map_fn() -> (
            Iterator[
                Union[
                    Output,
                    AssetMaterialization,
                    AssetObservation,
                    AssetCheckResult,
                    AssetCheckEvaluation,
                ]
            ]
        ):
            with ThreadPoolExecutor(
                max_workers=self._dbt_cli_invocation.postprocessing_threadpool_num_threads,
                thread_name_prefix=f"dbt_attach_metadata_{fn.__name__}",
            ) as executor:
                yield from imap(
                    executor=executor,
                    iterable=event_stream,
                    func=_map_fn,
                )

        return DbtEventIterator(
            _threadpool_wrap_map_fn(),
            dbt_cli_invocation=self._dbt_cli_invocation,
        )

    @public
    def with_insights(
        self,
        skip_config_check: bool = False,
        record_observation_usage: bool = True,
    ) -> "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]":
        """Associate each warehouse query with the produced asset materializations for use in Dagster
        Plus Insights. Currently supports Snowflake and BigQuery.

        For more information, see the documentation for
        `dagster_cloud.dagster_insights.dbt_with_snowflake_insights` and
        `dagster_cloud.dagster_insights.dbt_with_bigquery_insights`.

        Args:
            skip_config_check (bool): If true, skips the check that the dbt project config is set up
                correctly. Defaults to False.
            record_observation_usage (bool): If True, associates the usage associated with
                asset observations with that asset. Default is True.

        **Example:**

        .. code-block:: python

            @dbt_assets(manifest=DBT_MANIFEST_PATH)
            def jaffle_shop_dbt_assets(
                context: AssetExecutionContext,
                dbt: DbtCliResource,
            ):
                yield from dbt.cli(["build"], context=context).stream().with_insights()
        """
        adapter_type = self._dbt_cli_invocation.manifest.get("metadata", {}).get("adapter_type")
        if adapter_type == "snowflake":
            try:
                from dagster_cloud.dagster_insights import (  # pyright: ignore[reportMissingImports]
                    dbt_with_snowflake_insights,
                )
            except ImportError as e:
                raise DagsterInvalidPropertyError(
                    "The `dagster_cloud` library is required to use the `with_insights`"
                    " method. Install the library with `pip install dagster-cloud`."
                ) from e

            return DbtEventIterator(
                events=dbt_with_snowflake_insights(
                    context=self._dbt_cli_invocation.context,
                    dbt_cli_invocation=self._dbt_cli_invocation,
                    dagster_events=self,
                    skip_config_check=skip_config_check,
                    record_observation_usage=record_observation_usage,
                ),
                dbt_cli_invocation=self._dbt_cli_invocation,
            )
        elif adapter_type == "bigquery":
            try:
                from dagster_cloud.dagster_insights import (  # pyright: ignore[reportMissingImports]
                    dbt_with_bigquery_insights,
                )
            except ImportError as e:
                raise DagsterInvalidPropertyError(
                    "The `dagster_cloud` library is required to use the `with_insights`"
                    " method. Install the library with `pip install dagster-cloud`."
                ) from e

            return DbtEventIterator(
                events=dbt_with_bigquery_insights(
                    context=self._dbt_cli_invocation.context,
                    dbt_cli_invocation=self._dbt_cli_invocation,
                    dagster_events=self,
                    skip_config_check=skip_config_check,
                    record_observation_usage=record_observation_usage,
                ),
                dbt_cli_invocation=self._dbt_cli_invocation,
            )
        else:
            check.failed(
                f"The `with_insights` method is only supported for Snowflake and BigQuery and is not supported for adapter type `{adapter_type}`"
            )
