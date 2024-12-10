from typing import TYPE_CHECKING, Iterator, Union

from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    MaterializeResult,
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from dagster_fivetran.resources import FivetranWorkspace


FivetranEventType = Union[AssetMaterialization, MaterializeResult]
T = TypeVar("T", bound=FivetranEventType)


def fetch_column_metadata(
    fivetran_workspace: "FivetranWorkspace",
    connector_id: str,
    materialization: Union[AssetMaterialization, MaterializeResult],
) -> AssetMaterialization:
    """Subroutine to fetch column metadata for a given table from the Fivetran API and attach it to the
    materialization.
    """
    schema_source_name = materialization.metadata["schema_source_name"].value
    table_source_name = materialization.metadata["table_source_name"].value
    client = fivetran_workspace.get_client()

    try:
        table_conn_data = client.get_columns_for_table(
            connector_id=connector_id,
            schema_name=schema_source_name,
            table_name=table_source_name,
        )
        columns = check.dict_elem(table_conn_data, "columns")
        table_columns = sorted(
            [
                TableColumn(name=col["name_in_destination"], type="")
                for col in columns.values()
                if "name_in_destination" in col and col.get("enabled")
            ],
            key=lambda col: col.name,
        )
        return materialization.with_metadata(
            {
                **materialization.metadata,
                **TableMetadataSet(column_schema=TableSchema(table_columns)),
            }
        )
    except Exception as e:
        client._log.warning(  # noqa
            "An error occurred while fetching column metadata for table %s",
            f"Exception: {e}",
            exc_info=True,
        )
        return materialization


class FivetranEventIterator(Iterator[T]):
    """A wrapper around an iterator of Fivetran events which contains additional methods for
    post-processing the events, such as fetching column metadata.
    """

    def __init__(
        self,
        events: Iterator[T],
        fivetran_workspace: "FivetranWorkspace",
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> None:
        self._inner_iterator = events
        self._fivetran_workspace = fivetran_workspace
        self._context = context

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "FivetranEventIterator[T]":
        return self

    @experimental
    @public
    def fetch_column_metadata(self) -> "FivetranEventIterator":
        """Fetches column metadata for each table synced by the Sling CLI.

        Retrieves the column schema and lineage for each target table.

        Returns:
            SlingEventIterator: An iterator of Dagster events with column metadata attached.
        """

        def _fetch_column_metadata() -> Iterator[T]:
            raise NotImplementedError()

        return FivetranEventIterator[T](
            _fetch_column_metadata(), self._fivetran_workspace, self._context
        )
