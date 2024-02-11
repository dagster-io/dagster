from abc import abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from dagster import InputContext, MetadataValue, OutputContext, TableColumn, TableSchema
from dagster._core.definitions.time_window_partitions import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from deltalake import DeltaTable, WriterProperties, write_deltalake
from deltalake.exceptions import TableNotFoundError
from deltalake.schema import (
    Field as DeltaField,
    PrimitiveType,
    Schema,
    _convert_pa_schema_to_delta,
)
from deltalake.table import FilterLiteralType, _filters_to_expression

from .config import MergeType
from .io_manager import DELTA_DATE_FORMAT, DELTA_DATETIME_FORMAT, TableConnection

T = TypeVar("T")
ArrowTypes = Union[pa.Table, pa.RecordBatchReader]

from .io_manager import _DeltaTableIOManagerResourceConfig


def _merge_execute(
    dt: DeltaTable,
    reader: pa.RecordBatchReader,
    merge_config: Dict[str, Any],
    writer_properties: Optional[WriterProperties],
    custom_metadata: Optional[Dict[str, str]],
    delta_params: Dict[str, Any],
) -> Dict[str, Any]:
    merge_type = merge_config.get("merge_type")
    error_on_type_mismatch = merge_config.get("error_on_type_mismatch", True)

    merger = dt.merge(
        source=reader,
        predicate=merge_config.get("predicate"),  # type: ignore
        source_alias=merge_config.get("source_alias"),
        target_alias=merge_config.get("target_alias"),
        error_on_type_mismatch=error_on_type_mismatch,
        writer_properties=writer_properties,
        custom_metadata=custom_metadata,
        **delta_params,
    )

    if merge_type == MergeType.update_only:
        return merger.when_matched_update_all().execute()
    elif merge_type == MergeType.deduplicate_insert:
        return merger.when_not_matched_insert_all().execute()
    elif merge_type == MergeType.upsert:
        return merger.when_matched_update_all().when_not_matched_insert_all().execute()
    elif merge_type == MergeType.replace_delete_unmatched:
        return merger.when_matched_update_all().when_not_matched_by_source_delete().execute()
    else:
        raise NotImplementedError


class DeltalakeBaseArrowTypeHandler(DbTypeHandler[T], Generic[T]):
    @abstractmethod
    def from_arrow(self, obj: pa.RecordBatchReader, target_type: type) -> T:
        pass

    @abstractmethod
    def to_arrow(self, obj: T) -> Tuple[pa.RecordBatchReader, Dict[str, Any]]:
        pass

    @abstractmethod
    def get_output_stats(self, obj: T) -> Dict[str, MetadataValue]:
        pass

    def handle_output(
        self,
        context: OutputContext,
        table_slice: TableSlice,
        obj: T,
        connection: TableConnection,
    ):
        """Stores pyarrow types in Delta table."""
        metadata = context.metadata or {}
        resource_config = context.resource_config or {}
        object_stats = self.get_output_stats(obj)
        reader, delta_params = self.to_arrow(obj=obj)
        delta_schema = Schema.from_pyarrow(reader.schema)
        resource_config = cast(_DeltaTableIOManagerResourceConfig, context.resource_config)
        engine = resource_config.get("writer_engine")
        save_mode = metadata.get("mode")
        main_save_mode = resource_config.get("mode")
        custom_metadata = metadata.get("custom_metadata") or resource_config.get("custom_metadata")
        overwrite_schema = metadata.get("overwrite_schema") or resource_config.get(
            "overwrite_schema"
        )
        writer_properties = resource_config.get("writer_properties")
        writer_properties = (
            WriterProperties(**writer_properties) if writer_properties is not None else None  # type: ignore
        )
        merge_config = resource_config.get("merge_config")

        if save_mode is not None:
            context.log.debug(
                "IO manager mode overridden with the asset metadata mode, %s -> %s",
                main_save_mode,
                save_mode,
            )
            main_save_mode = save_mode
        context.log.debug("Writing with mode: `%s`", main_save_mode)

        merge_stats = None
        partition_filters = None
        partition_columns = None

        if table_slice.partition_dimensions is not None:
            partition_filters = partition_dimensions_to_dnf(
                partition_dimensions=table_slice.partition_dimensions,
                table_schema=delta_schema,
                str_values=True,
            )
            if partition_filters is not None and engine == "rust":
                raise ValueError(
                    """Partition dimension with rust engine writer combined is not supported yet, use the default 'pyarrow' engine."""
                )
            # TODO make robust and move to function
            partition_columns = [dim.partition_expr for dim in table_slice.partition_dimensions]

        if main_save_mode != "merge":
            write_deltalake(  # type: ignore
                table_or_uri=connection.table_uri,
                data=reader,
                storage_options=connection.storage_options,
                mode=main_save_mode,
                partition_filters=partition_filters,
                partition_by=partition_columns,
                engine=engine,
                overwrite_schema=overwrite_schema,
                custom_metadata=custom_metadata,
                writer_properties=writer_properties,
                **delta_params,
            )
        else:
            if merge_config is None:
                raise ValueError(
                    "Merge Configuration should be provided when `mode = WriterMode.merge`"
                )
            try:
                dt = DeltaTable(connection.table_uri, storage_options=connection.storage_options)
            except TableNotFoundError:
                context.log.debug("Creating a DeltaTable first before merging.")
                dt = DeltaTable.create(
                    table_uri=connection.table_uri,
                    schema=_convert_pa_schema_to_delta(reader.schema, **delta_params),
                    partition_by=partition_columns,
                    storage_options=connection.storage_options,
                    custom_metadata=custom_metadata,
                )
            merge_stats = _merge_execute(
                dt,
                reader,
                merge_config,
                writer_properties=writer_properties,
                custom_metadata=custom_metadata,
                delta_params=delta_params,
            )

        # TODO make stats computation configurable on type handler
        dt = DeltaTable(connection.table_uri, storage_options=connection.storage_options)
        try:
            _table, stats = _get_partition_stats(dt=dt, partition_filters=partition_filters)
        except Exception as e:
            context.log.warn(f"error while computing table stats: {e}")
            stats = {}

        output_metadata = {
            "table_columns": MetadataValue.table_schema(
                TableSchema(
                    columns=[
                        TableColumn(name=name, type=str(dtype))
                        for name, dtype in zip(reader.schema.names, reader.schema.types)
                    ]
                )
            ),
            "table_uri": MetadataValue.path(connection.table_uri),
            "table_version": MetadataValue.int(dt.version()),
            **stats,
            **object_stats,
        }
        if merge_stats is not None:
            output_metadata["merge_stats"] = MetadataValue.json(merge_stats)

        context.add_output_metadata(output_metadata)

    def load_input(
        self,
        context: InputContext,
        table_slice: TableSlice,
        connection: TableConnection,
    ) -> T:
        """Loads the input as a pyarrow Table or RecordBatchReader."""
        dataset = _table_reader(table_slice, connection)

        if context.dagster_type.typing_type == ds.Dataset:
            if table_slice.columns is not None:
                raise ValueError("Cannot select columns when loading as Dataset.")
            return dataset

        scanner = dataset.scanner(columns=table_slice.columns)
        return self.from_arrow(scanner.to_reader(), context.dagster_type.typing_type)


class DeltaLakePyArrowTypeHandler(DeltalakeBaseArrowTypeHandler[ArrowTypes]):
    def from_arrow(self, obj: pa.RecordBatchReader, target_type: Type[ArrowTypes]) -> ArrowTypes:
        if target_type == pa.Table:
            return obj.read_all()
        return obj

    def to_arrow(self, obj: ArrowTypes) -> Tuple[pa.RecordBatchReader, Dict[str, Any]]:
        if isinstance(obj, pa.Table):
            return obj.to_reader(), {}
        if isinstance(obj, ds.Dataset):
            return obj.scanner().to_reader(), {}
        return obj, {}

    def get_output_stats(self, obj: ArrowTypes) -> Dict[str, MetadataValue]:
        return {}

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pa.Table, pa.RecordBatchReader, ds.Dataset]


def partition_dimensions_to_dnf(
    partition_dimensions: Iterable[TablePartitionDimension],
    table_schema: Schema,
    str_values: bool = False,
    input_dnf: bool = False,  # during input we want to read a range when it's (un)-partitioned
) -> Optional[List[FilterLiteralType]]:
    parts = []
    for partition_dimension in partition_dimensions:
        field = _field_from_schema(partition_dimension.partition_expr, table_schema)
        if field is None:
            raise ValueError(
                f"Field {partition_dimension.partition_expr} is not part of table schema.",
                "Currently only column names are supported as partition expressions",
            )
        if isinstance(field.type, PrimitiveType):
            if field.type.type in ["timestamp", "date"]:
                filter_ = _time_window_partition_dnf(
                    partition_dimension, field.type.type, str_values, input_dnf
                )
                if isinstance(filter_, list):
                    parts.extend(filter_)
                else:
                    parts.append(filter_)
            elif field.type.type == "string":
                parts.append(_value_dnf(partition_dimension))
            else:
                raise ValueError(f"Unsupported partition type {field.type.type}")
        else:
            raise ValueError(f"Unsupported partition type {field.type}")

    return parts if len(parts) > 0 else None


def _value_dnf(table_partition: TablePartitionDimension):
    # ", ".join(f"'{partition}'" for partition in table_partition.partitions)
    partition = cast(Sequence[str], table_partition.partitions)
    if len(partition) > 1:
        return (table_partition.partition_expr, "in", table_partition.partitions)
    else:
        return (table_partition.partition_expr, "=", table_partition.partitions[0])


def _time_window_partition_dnf(
    table_partition: TablePartitionDimension, data_type: str, str_values: bool, input_dnf: bool
) -> Union[FilterLiteralType, List[FilterLiteralType]]:
    partition = cast(TimeWindow, table_partition.partitions)
    start_dt, end_dt = partition
    start_dt, end_dt = start_dt.replace(tzinfo=None), end_dt.replace(tzinfo=None)
    if str_values:
        if data_type == "timestamp":
            start_dt, end_dt = (
                start_dt.strftime(DELTA_DATETIME_FORMAT),
                end_dt.strftime(DELTA_DATETIME_FORMAT),
            )
        elif data_type == "date":
            start_dt, end_dt = (
                start_dt.strftime(DELTA_DATE_FORMAT),
                end_dt.strftime(DELTA_DATETIME_FORMAT),
            )
        else:
            raise ValueError(f"Unknown primitive type: {data_type}")

    if input_dnf:
        return [
            (table_partition.partition_expr, ">=", start_dt),
            (table_partition.partition_expr, "<", end_dt),
        ]
    else:
        return (table_partition.partition_expr, "=", start_dt)


def _field_from_schema(field_name: str, schema: Schema) -> Optional[DeltaField]:
    for field in schema.fields:
        if field.name == field_name:
            return field
    return None


def _get_partition_stats(dt: DeltaTable, partition_filters=None):
    files = pa.array(dt.files(partition_filters=partition_filters))
    files_table = pa.Table.from_arrays([files], names=["path"])
    actions_table = pa.Table.from_batches([dt.get_add_actions(flatten=True)])
    actions_table = actions_table.select(["path", "size_bytes", "num_records"])
    table = files_table.join(actions_table, keys="path")

    stats = {
        "size_bytes": MetadataValue.int(pc.sum(table.column("size_bytes")).as_py()),
        "num_rows": MetadataValue.int(pc.sum(table.column("num_records")).as_py()),
    }

    return table, stats


def _table_reader(table_slice: TableSlice, connection: TableConnection) -> ds.Dataset:
    table = DeltaTable(table_uri=connection.table_uri, storage_options=connection.storage_options)

    partition_expr = None
    if table_slice.partition_dimensions is not None:
        partition_filters = partition_dimensions_to_dnf(
            partition_dimensions=table_slice.partition_dimensions,
            table_schema=table.schema(),
            input_dnf=True,
        )
        if partition_filters is not None:
            partition_expr = _filters_to_expression([partition_filters])

    dataset = table.to_pyarrow_dataset()
    if partition_expr is not None:
        dataset = dataset.filter(expression=partition_expr)

    return dataset
