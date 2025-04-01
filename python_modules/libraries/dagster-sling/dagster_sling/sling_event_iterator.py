import re
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from dagster import (
    AssetMaterialization,
    MaterializeResult,
    _check as check,
)
from dagster._annotations import public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnDep,
    TableColumnLineage,
    TableSchema,
)
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from dagster_sling.resources import SlingResource


SlingEventType = Union[AssetMaterialization, MaterializeResult]

# We define SlingEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `SlingResource.replicate()`
# will be able to see the inner type of the iterator, rather than just `SlingEventIterator`.
T = TypeVar("T", bound=SlingEventType)


def _get_logs_for_stream(
    stream_name: str,
    sling_cli: "SlingResource",
) -> Sequence[str]:
    """Parses out the logs for a specific stream from the raw logs returned by the Sling CLI."""
    corresponding_logs = []
    recording_logs = False
    for log in sling_cli.stream_raw_logs():
        if stream_name in log:
            corresponding_logs.append(log)
            recording_logs = True
        elif recording_logs:
            if len(log.strip()) == 0:
                break
            corresponding_logs.append(log)
    return corresponding_logs


def _strip_quotes_target_table_name(target_table_name: str) -> str:
    return target_table_name.replace('"', "")


INSERT_REGEX = re.compile(r".*inserted (\d+) rows into (.*) in.*")


def _get_target_table_name(stream_name: str, sling_cli: "SlingResource") -> Optional[str]:
    """Extracts the target table name from the logs for a specific stream."""
    corresponding_logs = _get_logs_for_stream(stream_name, sling_cli)
    insert_log = next((log for log in corresponding_logs if re.match(INSERT_REGEX, log)), None)
    if not insert_log:
        return None

    target_table_name = check.not_none(re.match(INSERT_REGEX, insert_log)).group(2)
    return _strip_quotes_target_table_name(target_table_name)


COLUMN_NAME_COL = "Column"
COLUMN_TYPE_COL = "General Type"

SLING_COLUMN_PREFIX = "_sling_"


def fetch_row_count_metadata(
    materialization: SlingEventType,
    sling_cli: "SlingResource",
    replication_config: dict[str, Any],
    context: Union[OpExecutionContext, AssetExecutionContext],
) -> dict[str, Any]:
    target_name = replication_config["target"]
    if not materialization.metadata:
        raise Exception("Missing required metadata to retrieve stream_name")

    stream_name = cast(str, materialization.metadata["stream_name"])
    target_table_name = _get_target_table_name(stream_name, sling_cli)

    if target_table_name:
        try:
            row_count = sling_cli.get_row_count_for_table(target_name, target_table_name)
            return dict(TableMetadataSet(row_count=row_count))
        except Exception as e:
            context.log.warning(
                f"Failed to fetch row count for stream %s\nException: {e}",
                stream_name,
                exc_info=True,
            )

    return {}


def fetch_column_metadata(
    materialization: SlingEventType,
    sling_cli: "SlingResource",
    replication_config: dict[str, Any],
    context: Union[OpExecutionContext, AssetExecutionContext],
) -> dict[str, Any]:
    target_name = replication_config["target"]

    if not materialization.metadata:
        raise Exception("Missing required metadata to retrieve stream_name")

    stream_name = cast(str, materialization.metadata["stream_name"])

    upstream_assets = set()
    if isinstance(context, AssetExecutionContext):
        if materialization.asset_key:
            upstream_assets = context.assets_def.asset_deps[materialization.asset_key]

    target_table_name = _get_target_table_name(stream_name, sling_cli)

    if target_table_name:
        try:
            column_info = sling_cli.get_column_info_for_table(target_name, target_table_name)
            column_type_map = {
                col[COLUMN_NAME_COL]: col[COLUMN_TYPE_COL]
                for col in column_info
                if COLUMN_TYPE_COL in col
            }

            column_lineage = None
            # If there is only one upstream asset (typical case), we can infer column lineage
            # from the single upstream asset which is being replicated exactly.
            if len(upstream_assets) == 1:
                upstream_asset_key = next(iter(upstream_assets))
                column_lineage = TableColumnLineage(
                    deps_by_column={
                        column_name.lower(): [
                            TableColumnDep(
                                asset_key=upstream_asset_key,
                                column_name=column_name.lower(),
                            )
                        ]
                        for column_name in column_type_map.keys()
                        if not column_name.startswith(SLING_COLUMN_PREFIX)
                    }
                )

            return dict(
                TableMetadataSet(
                    column_schema=TableSchema(
                        columns=[
                            TableColumn(name=column_name.lower(), type=column_type)
                            for column_name, column_type in column_type_map.items()
                        ]
                    ),
                    column_lineage=column_lineage,
                )
            )
        except Exception as e:
            context.log.warning(
                f"Failed to fetch column metadata for stream %s\nException: {e}",
                stream_name,
                exc_info=True,
            )

    return {}


class SlingEventIterator(Iterator[T]):
    """A wrapper around an iterator of Sling events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        sling_cli: "SlingResource",
        replication_config: dict[str, Any],
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> None:
        self._inner_iterator = events
        self._sling_cli = sling_cli
        self._replication_config = replication_config
        self._context = context

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "SlingEventIterator[T]":
        return self

    @public
    def fetch_column_metadata(self) -> "SlingEventIterator":
        """Fetches column metadata for each table synced by the Sling CLI.

        Retrieves the column schema and lineage for each target table.

        Returns:
            SlingEventIterator: An iterator of Dagster events with column metadata attached.
        """

        def _fetch_column_metadata() -> Iterator[T]:
            for event in self:
                col_metadata = fetch_column_metadata(
                    event, self._sling_cli, self._replication_config, self._context
                )
                if event.metadata:
                    yield event._replace(metadata={**col_metadata, **event.metadata})

        return SlingEventIterator[T](
            _fetch_column_metadata(), self._sling_cli, self._replication_config, self._context
        )

    @public
    def fetch_row_count(self) -> "SlingEventIterator":
        """Fetches row count metadata for each table synced by the Sling CLI.

        Retrieves the row count for each target table.

        Returns:
            SlingEventIterator: An iterator of Dagster events with row count metadata attached.
        """

        def _fetch_row_count() -> Iterator[T]:
            for event in self:
                row_count_metadata = fetch_row_count_metadata(
                    event, self._sling_cli, self._replication_config, self._context
                )
                if event.metadata:
                    yield event._replace(metadata={**row_count_metadata, **event.metadata})

        return SlingEventIterator[T](
            _fetch_row_count(), self._sling_cli, self._replication_config, self._context
        )
