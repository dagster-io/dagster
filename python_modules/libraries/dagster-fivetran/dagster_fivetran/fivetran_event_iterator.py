import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Union

from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    MaterializeResult,
    OpExecutionContext,
    _check as check,
)
from dagster._annotations import beta, public
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.utils import imap
from typing_extensions import TypeVar

from dagster_fivetran.translator import FivetranMetadataSet
from dagster_fivetran.utils import get_column_schema_for_columns, get_fivetran_connector_table_name

if TYPE_CHECKING:
    from dagster_fivetran.resources import FivetranWorkspace

FivetranEventType = Union[AssetMaterialization, MaterializeResult]
T = TypeVar("T", bound=FivetranEventType)

DEFAULT_MAX_THREADPOOL_WORKERS = 10


def _fetch_column_metadata(
    materialization: FivetranEventType,
    fivetran_workspace: "FivetranWorkspace",
) -> dict[str, Any]:
    """Subroutine to fetch column metadata for a given table from the Fivetran API."""
    materialization_metadata = check.not_none(materialization.metadata)
    connector_id = check.not_none(
        FivetranMetadataSet.extract(materialization_metadata).connector_id
    )
    schema_name = check.not_none(
        FivetranMetadataSet.extract(materialization_metadata).destination_schema_name
    )
    table_name = check.not_none(
        FivetranMetadataSet.extract(materialization_metadata).destination_table_name
    )

    client = fivetran_workspace.get_client()

    metadata = {}
    try:
        table_conn_data = client.get_columns_config_for_table(
            connector_id=connector_id,
            schema_name=schema_name,
            table_name=table_name,
        )

        columns = check.dict_elem(table_conn_data, "columns")
        metadata = {**TableMetadataSet(column_schema=get_column_schema_for_columns(columns))}
    except Exception as e:
        client._log.warning(  # noqa
            f"An error occurred while fetching column metadata for table "
            f"{get_fivetran_connector_table_name(schema_name=schema_name, table_name=table_name)}."
            "Column metadata will not be included in the event.\n\n"
            f"Exception: {e}",
            exc_info=True,
        )
    return metadata


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

    @beta
    @public
    def fetch_column_metadata(self) -> "FivetranEventIterator":
        """Fetches column metadata for each table synced with the Fivetran API.

        Retrieves the column schema for each destination table.

        Returns:
            FivetranEventIterator: An iterator of Dagster events with column metadata attached.
        """
        fetch_metadata_fn: Callable[
            [FivetranEventType],
            dict[str, Any],
        ] = lambda materialization: _fetch_column_metadata(
            materialization=materialization,
            fivetran_workspace=self._fivetran_workspace,
        )

        return self._attach_metadata(fetch_metadata_fn)

    def _attach_metadata(
        self,
        fn: Callable[[FivetranEventType], dict[str, Any]],
    ) -> "FivetranEventIterator":
        """Runs a threaded task to attach metadata to each event in the iterator.

        Args:
            fn (Callable[[Union[AssetMaterialization, MaterializeResult]], Dict[str, Any]]):
                A function which takes a FivetranEventType and returns
                a dictionary of metadata to attach to the event.

        Returns:
             Iterator[Union[AssetMaterialization, MaterializeResult]]:
                A set of corresponding Dagster events for Fivetran tables, with any metadata output
                by the function attached, yielded in the order they are emitted by the Fivetran API.
        """

        def _map_fn(event: FivetranEventType) -> FivetranEventType:
            return event._replace(metadata={**check.is_dict(event.metadata), **fn(event)})

        def _threadpool_wrap_map_fn() -> Iterator[FivetranEventType]:
            assets_def = self._context.assets_def
            connector_id = next(
                check.not_none(FivetranMetadataSet.extract(spec.metadata).connector_id)
                for spec in assets_def.specs
            )

            with ThreadPoolExecutor(
                max_workers=int(
                    os.getenv(
                        "FIVETRAN_POSTPROCESSING_THREADPOOL_WORKERS",
                        default=DEFAULT_MAX_THREADPOOL_WORKERS,
                    )
                ),
                thread_name_prefix=f"fivetran_{connector_id}",
            ) as executor:
                yield from imap(
                    executor=executor,
                    iterable=self._inner_iterator,
                    func=_map_fn,
                )

        return FivetranEventIterator(
            events=_threadpool_wrap_map_fn(),
            fivetran_workspace=self._fivetran_workspace,
            context=self._context,
        )
