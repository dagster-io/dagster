from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import datetime
from os import PathLike
from typing import Any, Callable, Generic, Optional, Union

import dagster_shared.seven as seven
from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, record, record_custom
from dagster_shared.serdes.serdes import (
    FieldSerializer,
    JsonSerializableValue,
    PackableValue,
    UnpackContext,
    WhitelistMap,
    pack_value,
    whitelist_for_serdes,
)
from typing_extensions import Self, TypeVar

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.table import (
    TableColumn as TableColumn,
    TableColumnConstraints as TableColumnConstraints,
    TableColumnDep as TableColumnDep,
    TableColumnLineage as TableColumnLineage,
    TableConstraints as TableConstraints,
    TableRecord as TableRecord,
    TableSchema as TableSchema,
)
from dagster._core.errors import DagsterInvalidMetadata

T_Packable = TypeVar("T_Packable", bound=PackableValue, default=PackableValue, covariant=True)

# ########################
# ##### METADATA VALUE
# ########################


@public
class MetadataValue(ABC, Generic[T_Packable]):
    """Utility class to wrap metadata values passed into Dagster events so that they can be
    displayed in the Dagster UI and other tooling.

    .. code-block:: python

        @op
        def emit_metadata(context, df):
            yield AssetMaterialization(
                asset_key="my_dataset",
                metadata={
                    "my_text_label": "hello",
                    "dashboard_url": MetadataValue.url("http://mycoolsite.com/my_dashboard"),
                    "num_rows": 0,
                },
            )
    """

    @public
    @property
    @abstractmethod
    def value(self) -> T_Packable:
        """The wrapped value."""
        raise NotImplementedError()

    @public
    @staticmethod
    def text(text: str) -> "TextMetadataValue":
        """Static constructor for a metadata value wrapping text as
        :py:class:`TextMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, df):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "my_text_label": MetadataValue.text("hello")
                        },
                    )

        Args:
            text (str): The text string for a metadata entry.
        """
        return TextMetadataValue(text)

    @public
    @staticmethod
    def url(url: str) -> "UrlMetadataValue":
        """Static constructor for a metadata value wrapping a URL as
        :py:class:`UrlMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context):
                    yield AssetMaterialization(
                        asset_key="my_dashboard",
                        metadata={
                            "dashboard_url": MetadataValue.url("http://mycoolsite.com/my_dashboard"),
                        }
                    )

        Args:
            url (str): The URL for a metadata entry.
        """
        return UrlMetadataValue(url)

    @public
    @staticmethod
    def path(path: Union[str, PathLike]) -> "PathMetadataValue":
        """Static constructor for a metadata value wrapping a path as
        :py:class:`PathMetadataValue`.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "filepath": MetadataValue.path("path/to/file"),
                        }
                    )

        Args:
            path (str): The path for a metadata entry.
        """
        return PathMetadataValue(path)

    @public
    @staticmethod
    def notebook(path: Union[str, PathLike]) -> "NotebookMetadataValue":
        """Static constructor for a metadata value wrapping a notebook path as
        :py:class:`NotebookMetadataValue`.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "notebook_path": MetadataValue.notebook("path/to/notebook.ipynb"),
                        }
                    )

        Args:
            path (str): The path to a notebook for a metadata entry.
        """
        return NotebookMetadataValue(path)

    @public
    @staticmethod
    def json(data: Union[Sequence[Any], Mapping[str, Any]]) -> "JsonMetadataValue":
        """Static constructor for a metadata value wrapping a json-serializable list or dict
        as :py:class:`JsonMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context):
                    yield ExpectationResult(
                        success=not missing_things,
                        label="is_present",
                        metadata={
                            "about my dataset": MetadataValue.json({"missing_columns": missing_things})
                        },
                    )

        Args:
            data (Union[Sequence[Any], Mapping[str, Any]]): The JSON data for a metadata entry.
        """
        return JsonMetadataValue(data)

    @public
    @staticmethod
    def md(data: str) -> "MarkdownMetadataValue":
        """Static constructor for a metadata value wrapping markdown data as
        :py:class:`MarkdownMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.


        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, md_str):
                    yield AssetMaterialization(
                        asset_key="info",
                        metadata={
                            'Details': MetadataValue.md(md_str)
                        },
                    )

        Args:
            md_str (str): The markdown for a metadata entry.
        """
        return MarkdownMetadataValue(data)

    @public
    @staticmethod
    def python_artifact(python_artifact: Callable[..., Any]) -> "PythonArtifactMetadataValue":
        """Static constructor for a metadata value wrapping a python artifact as
        :py:class:`PythonArtifactMetadataValue`. Can be used as the value type for the
        `metadata` parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, df):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "class": MetadataValue.python_artifact(MyClass),
                            "function": MetadataValue.python_artifact(my_function),
                        }
                    )

        Args:
            value (Callable): The python class or function for a metadata entry.
        """
        check.callable_param(python_artifact, "python_artifact")
        return PythonArtifactMetadataValue(python_artifact.__module__, python_artifact.__name__)

    @public
    @staticmethod
    def float(value: float) -> "FloatMetadataValue":
        """Static constructor for a metadata value wrapping a float as
        :py:class:`FloatMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, df):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "size (bytes)": MetadataValue.float(calculate_bytes(df)),
                        }
                    )

        Args:
            value (float): The float value for a metadata entry.
        """
        return FloatMetadataValue(value)

    @public
    @staticmethod
    def int(value: int) -> "IntMetadataValue":
        """Static constructor for a metadata value wrapping an int as
        :py:class:`IntMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, df):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "number of rows": MetadataValue.int(len(df)),
                        },
                    )

        Args:
            value (int): The int value for a metadata entry.
        """
        return IntMetadataValue(value)

    @public
    @staticmethod
    def bool(value: bool) -> "BoolMetadataValue":
        """Static constructor for a metadata value wrapping a bool as
        :py:class:`BoolMetadataValuye`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context, df):
                    yield AssetMaterialization(
                        asset_key="my_dataset",
                        metadata={
                            "num rows > 1000": MetadataValue.bool(len(df) > 1000),
                        },
                    )

        Args:
            value (bool): The bool value for a metadata entry.
        """
        return BoolMetadataValue(value)

    @public
    @staticmethod
    def timestamp(value: Union["float", datetime]) -> "TimestampMetadataValue":
        """Static constructor for a metadata value wrapping a UNIX timestamp as a
        :py:class:`TimestampMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Args:
            value (Union[float, datetime]): The unix timestamp value for a metadata entry. If a
                datetime is provided, the timestamp will be extracted. datetimes without timezones
                are not accepted, because their timestamps can be ambiguous.
        """
        if isinstance(value, float):
            return TimestampMetadataValue(value)
        elif isinstance(value, datetime):
            if value.tzinfo is None:
                check.failed(
                    "Datetime values provided to MetadataValue.timestamp must have timezones, "
                    f"but {value.isoformat()} does not"
                )
            return TimestampMetadataValue(value.timestamp())
        else:
            check.failed(f"Expected either a float or a datetime, but received a {type(value)}")

    @public
    @staticmethod
    def dagster_run(run_id: str) -> "DagsterRunMetadataValue":
        """Static constructor for a metadata value wrapping a reference to a Dagster run.

        Args:
            run_id (str): The ID of the run.
        """
        return DagsterRunMetadataValue(run_id)

    @public
    @staticmethod
    def asset(asset_key: AssetKey) -> "DagsterAssetMetadataValue":
        """Static constructor for a metadata value referencing a Dagster asset, by key.

        For example:

        .. code-block:: python

            @op
            def validate_table(context, df):
                yield AssetMaterialization(
                    asset_key=AssetKey("my_table"),
                    metadata={
                        "Related asset": MetadataValue.asset(AssetKey('my_other_table')),
                    },
                )

        Args:
            asset_key (AssetKey): The asset key referencing the asset.
        """
        from dagster._core.definitions.events import AssetKey

        check.inst_param(asset_key, "asset_key", AssetKey)
        return DagsterAssetMetadataValue(asset_key)

    @public
    @staticmethod
    def job(
        job_name: str,
        location_name: str,
        *,
        repository_name: Optional[str] = None,
    ) -> "DagsterJobMetadataValue":
        """Static constructor for a metadata value referencing a Dagster job, by name.

        For example:

        .. code-block:: python

            from dagster import AssetMaterialization, MetadataValue, op

            @op
            def emit_metadata(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "Producing job": MetadataValue.job('my_other_job', 'my_location'),
                    },
                )

        Args:
            job_name (str): The name of the job.
            location_name (Optional[str]): The code location name for the job.
            repository_name (Optional[str]): The repository name of the job, if different from the
                default.
        """
        return DagsterJobMetadataValue(
            job_name=check.str_param(job_name, "job_name"),
            location_name=check.str_param(location_name, "location_name"),
            repository_name=check.opt_str_param(repository_name, "repository_name"),
        )

    @public
    @staticmethod
    def table(
        records: Sequence[TableRecord], schema: Optional[TableSchema] = None
    ) -> "TableMetadataValue":
        """Static constructor for a metadata value wrapping arbitrary tabular data as
        :py:class:`TableMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Example:
            .. code-block:: python

                @op
                def emit_metadata(context):
                    yield ExpectationResult(
                        success=not has_errors,
                        label="is_valid",
                        metadata={
                            "errors": MetadataValue.table(
                                records=[
                                    TableRecord(data={"code": "invalid-data-type", "row": 2, "col": "name"})
                                ],
                                schema=TableSchema(
                                    columns=[
                                        TableColumn(name="code", type="string"),
                                        TableColumn(name="row", type="int"),
                                        TableColumn(name="col", type="string"),
                                    ]
                                )
                            ),
                        },
                    )
        """
        return TableMetadataValue(records, schema)

    @public
    @staticmethod
    def table_schema(
        schema: TableSchema,
    ) -> "TableSchemaMetadataValue":
        """Static constructor for a metadata value wrapping a table schema as
        :py:class:`TableSchemaMetadataValue`. Can be used as the value type
        for the `metadata` parameter for supported events.

        Example:
            .. code-block:: python

                schema = TableSchema(
                    columns = [
                        TableColumn(name="id", type="int"),
                        TableColumn(name="status", type="bool"),
                    ]
                )

                DagsterType(
                    type_check_fn=some_validation_fn,
                    name='MyTable',
                    metadata={
                        'my_table_schema': MetadataValue.table_schema(schema),
                    }
                )

        Args:
            schema (TableSchema): The table schema for a metadata entry.
        """
        return TableSchemaMetadataValue(schema)

    @public
    @staticmethod
    def column_lineage(
        lineage: TableColumnLineage,
    ) -> "TableColumnLineageMetadataValue":
        """Static constructor for a metadata value wrapping a column lineage as
        :py:class:`TableColumnLineageMetadataValue`. Can be used as the value type
        for the `metadata` parameter for supported events.

        Args:
            lineage (TableColumnLineage): The column lineage for a metadata entry.
        """
        return TableColumnLineageMetadataValue(lineage)

    @public
    @staticmethod
    def null() -> "NullMetadataValue":
        """Static constructor for a metadata value representing null. Can be used as the value type
        for the `metadata` parameter for supported events.
        """
        return NullMetadataValue()

    # not public because rest of code location metadata API is not public
    @staticmethod
    def code_location_reconstruction(data: str) -> "CodeLocationReconstructionMetadataValue":
        """Static constructor for a metadata value wrapping arbitrary code location data useful during reconstruction as
        :py:class:`CodeLocationReconstructionMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events.

        Args:
            data (str): The serialized code location state for a metadata entry.
        """
        return CodeLocationReconstructionMetadataValue(data)

    @public
    @staticmethod
    def pool(pool: str) -> "PoolMetadataValue":
        """Static constructor for a metadata value wrapping a reference to a concurrency pool.

        Args:
            pool (str): The identifier for the pool.
        """
        return PoolMetadataValue(pool=pool)


# ########################
# ##### METADATA VALUE TYPES
# ########################

# NOTE: We have `type: ignore` in a few places below because mypy complains about an instance method
# (e.g. `text`) overriding a static method on the superclass of the same name. This is not a concern
# for us because these static methods should never be called on instances.

# NOTE: `XMetadataValue` classes are serialized with a storage name of `XMetadataEntryData` to
# maintain backward compatibility. See docstring of `whitelist_for_serdes` for more info.


@public
@whitelist_for_serdes(storage_name="TextMetadataEntryData")
@record(kw_only=False)
class TextMetadataValue(MetadataValue[str]):
    """Container class for text metadata entry data.

    Args:
        text (Optional[str]): The text data.
    """

    text: PublicAttr[Optional[str]] = ""  # type: ignore

    @public
    @property
    def value(self) -> str:
        """Optional[str]: The wrapped text data."""
        return self.text if self.text is not None else ""


@public
@whitelist_for_serdes(storage_name="UrlMetadataEntryData")
@record(kw_only=False)
class UrlMetadataValue(MetadataValue[str]):
    """Container class for URL metadata entry data.

    Args:
        url (Optional[str]): The URL as a string.
    """

    url: PublicAttr[Optional[str]] = ""  # type: ignore

    @public
    @property
    def value(self) -> str:
        """Optional[str]: The wrapped URL."""
        return self.url if self.url is not None else ""


@public
@whitelist_for_serdes(storage_name="PathMetadataEntryData")
@record_custom(field_to_new_mapping={"fspath": "path"})
class PathMetadataValue(MetadataValue[str], IHaveNew):
    """Container class for path metadata entry data.

    Args:
        path (str): The path as a string or conforming to os.PathLike.
    """

    fspath: str

    def __new__(cls, path: Optional[Union[str, PathLike]]):
        return super().__new__(
            cls,
            # coerces to str
            fspath=check.opt_path_param(path, "path", default=""),
        )

    @public
    @property
    def value(self) -> str:
        """str: The wrapped path."""
        return self.fspath

    @public
    @property
    def path(self) -> str:  # type: ignore
        return self.fspath


@public
@whitelist_for_serdes(storage_name="NotebookMetadataEntryData")
@record_custom(field_to_new_mapping={"fspath": "path"})
class NotebookMetadataValue(MetadataValue[str], IHaveNew):
    """Container class for notebook metadata entry data.

    Args:
        path (Optional[str]): The path to the notebook as a string or conforming to os.PathLike.
    """

    fspath: str

    def __new__(cls, path: Optional[Union[str, PathLike]]):
        return super().__new__(
            cls,
            # coerces to str
            fspath=check.opt_path_param(path, "path", default=""),
        )

    @public
    @property
    def value(self) -> str:
        """str: The wrapped path to the notebook as a string."""
        return self.fspath

    @public
    @property
    def path(self) -> str:  # type: ignore
        return self.fspath


class JsonDataFieldSerializer(FieldSerializer):
    def pack(
        self,
        mapping: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        # return the json serializable data field as is
        return mapping

    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        # erase any serdes objects that were stored here in earlier versions and
        # return plain json serializable data
        return pack_value(unpacked_value, whitelist_map=whitelist_map)


@whitelist_for_serdes(
    storage_name="JsonMetadataEntryData",
    field_serializers={"data": JsonDataFieldSerializer},
)
@record_custom
@public
class JsonMetadataValue(
    IHaveNew,
    MetadataValue[Optional[Union[Sequence[Any], Mapping[str, Any]]]],
):
    """Container class for JSON metadata entry data.

    Args:
        data (Union[Sequence[Any], Dict[str, Any]]): The JSON data.
    """

    data: PublicAttr[Optional[Union[Sequence[Any], Mapping[str, Any]]]]

    def __new__(cls, data: Optional[Union[Sequence[Any], Mapping[str, Any]]]):
        try:
            # check that the value is JSON serializable
            seven.dumps(data)
        except TypeError:
            raise DagsterInvalidMetadata("Value is not JSON serializable.")
        return super().__new__(cls, data=data)

    @public
    @property
    def value(self) -> Optional[Union[Sequence[Any], Mapping[str, Any]]]:
        """Optional[Union[Sequence[Any], Dict[str, Any]]]: The wrapped JSON data."""
        return self.data


@whitelist_for_serdes(storage_name="MarkdownMetadataEntryData")
@record(kw_only=False)
@public
class MarkdownMetadataValue(MetadataValue[str]):
    """Container class for markdown metadata entry data.

    Args:
        md_str (Optional[str]): The markdown as a string.
    """

    md_str: PublicAttr[Optional[str]] = ""

    @public
    @property
    def value(self) -> str:
        """Optional[str]: The wrapped markdown as a string."""
        return self.md_str if self.md_str is not None else ""


# This should be deprecated or fixed so that `value` does not return itself.
@public
@whitelist_for_serdes(storage_name="PythonArtifactMetadataEntryData")
@record(kw_only=False)
class PythonArtifactMetadataValue(
    LegacyNamedTupleMixin,
    MetadataValue["PythonArtifactMetadataValue"],
):
    """Container class for python artifact metadata entry data.

    Args:
        module (str): The module where the python artifact can be found
        name (str): The name of the python artifact
    """

    module: PublicAttr[str]
    name: PublicAttr[str]

    @public
    @property
    def value(self) -> Self:
        """PythonArtifactMetadataValue: Identity function."""
        return self


@whitelist_for_serdes(storage_name="FloatMetadataEntryData")
@record(kw_only=False)
@public
class FloatMetadataValue(MetadataValue[Optional[float]]):
    """Container class for float metadata entry data.

    Args:
        value (Optional[float]): The float value.
    """

    value: PublicAttr[Optional[float]]  # type: ignore


@whitelist_for_serdes(storage_name="IntMetadataEntryData")
@record(kw_only=False)
@public
class IntMetadataValue(MetadataValue[Optional[int]]):
    """Container class for int metadata entry data.

    Args:
        value (Optional[int]): The int value.
    """

    value: PublicAttr[Optional[int]]  # type: ignore


@whitelist_for_serdes(storage_name="BoolMetadataEntryData")
@record(kw_only=False)
class BoolMetadataValue(MetadataValue[Optional[bool]]):
    """Container class for bool metadata entry data.

    Args:
        value (Optional[bool]): The bool value.
    """

    value: PublicAttr[Optional[bool]]  # type: ignore


@public
@whitelist_for_serdes
@record(kw_only=False)
class TimestampMetadataValue(MetadataValue[float]):
    """Container class for metadata value that's a unix timestamp.

    Args:
        value (float): Seconds since the unix epoch.
    """

    value: PublicAttr[float]  # type: ignore


@whitelist_for_serdes(storage_name="DagsterPipelineRunMetadataEntryData")
@public
@record(kw_only=False)
class DagsterRunMetadataValue(MetadataValue[str]):
    """Representation of a dagster run.

    Args:
        run_id (str): The run id
    """

    run_id: PublicAttr[str]

    @public
    @property
    def value(self) -> str:
        """str: The wrapped run id."""
        return self.run_id


@whitelist_for_serdes
@record(kw_only=False)
class DagsterJobMetadataValue(MetadataValue["DagsterJobMetadataValue"]):
    """Representation of a dagster run.

    Args:
        job_name (str): The job's name
        location_name (str): The job's code location name
        repository_name (Optional[str]): The job's repository name. If not provided, the job is
            assumed to be in the same repository as this object.
    """

    job_name: PublicAttr[str]
    location_name: PublicAttr[str]
    repository_name: PublicAttr[Optional[str]] = None

    @public
    @property
    def value(self) -> Self:
        return self


@whitelist_for_serdes(storage_name="DagsterAssetMetadataEntryData")
@record(kw_only=False)
@public
class DagsterAssetMetadataValue(MetadataValue[AssetKey]):
    """Representation of a dagster asset.

    Args:
        asset_key (AssetKey): The dagster asset key
    """

    asset_key: PublicAttr[AssetKey]

    @public
    @property
    def value(self) -> AssetKey:
        """AssetKey: The wrapped :py:class:`AssetKey`."""
        return self.asset_key


# This should be deprecated or fixed so that `value` does not return itself.
@public
@whitelist_for_serdes(storage_name="TableMetadataEntryData")
@record_custom
class TableMetadataValue(
    MetadataValue["TableMetadataValue"],
    LegacyNamedTupleMixin,
    IHaveNew,
):
    """Container class for table metadata entry data.

    Args:
        records (TableRecord): The data as a list of records (i.e. rows).
        schema (Optional[TableSchema]): A schema for the table.

    Example:
        .. code-block:: python

            from dagster import TableMetadataValue, TableRecord

            TableMetadataValue(
                schema=None,
                records=[
                    TableRecord({"column1": 5, "column2": "x"}),
                    TableRecord({"column1": 7, "column2": "y"}),
                ]
            )
    """

    records: PublicAttr[Sequence[TableRecord]]
    schema: PublicAttr[TableSchema]

    @public
    @staticmethod
    def infer_column_type(value: object) -> str:
        """str: Infer the :py:class:`TableSchema` column type that will be used for a value."""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        else:
            return "string"

    def __new__(cls, records: Sequence[TableRecord], schema: Optional[TableSchema]):
        check.sequence_param(records, "records", of_type=TableRecord)
        check.opt_inst_param(schema, "schema", TableSchema)

        if len(records) == 0:
            schema = check.not_none(schema, "schema must be provided if records is empty")
        else:
            columns = set(records[0].data.keys())
            for record in records[1:]:
                check.invariant(
                    set(record.data.keys()) == columns, "All records must have the same fields"
                )
            schema = schema or TableSchema(
                columns=[
                    TableColumn(name=k, type=TableMetadataValue.infer_column_type(v))
                    for k, v in records[0].data.items()
                ]
            )

        return super().__new__(
            cls,
            records=records,
            schema=schema,
        )

    @public
    @property
    def value(self) -> Self:
        """TableMetadataValue: Identity function."""
        return self


@public
@whitelist_for_serdes(storage_name="TableSchemaMetadataEntryData")
@record(kw_only=False)
class TableSchemaMetadataValue(MetadataValue[TableSchema]):
    """Representation of a schema for arbitrary tabular data.

    Args:
        schema (TableSchema): The dictionary containing the schema representation.
    """

    schema: PublicAttr[TableSchema]

    @public
    @property
    def value(self) -> TableSchema:
        """TableSchema: The wrapped :py:class:`TableSchema`."""
        return self.schema


@public
@whitelist_for_serdes
@record_custom(field_to_new_mapping={"lineage": "column_lineage"})
class TableColumnLineageMetadataValue(
    MetadataValue[TableColumnLineage],
    IHaveNew,
):
    """Representation of the lineage of column inputs to column outputs of arbitrary tabular data.

    Args:
        column_lineage (TableColumnLineage): The lineage of column inputs to column outputs
            for the table.
    """

    lineage: PublicAttr[TableColumnLineage]

    def __new__(cls, column_lineage: TableColumnLineage):
        return super().__new__(
            cls,
            lineage=column_lineage,
        )

    @public
    @property
    def value(self) -> TableColumnLineage:
        """TableSpec: The wrapped :py:class:`TableSpec`."""
        return self.column_lineage

    @public
    @property
    def column_lineage(self) -> TableColumnLineage:  # type: ignore
        return self.lineage


@whitelist_for_serdes(storage_name="NullMetadataEntryData")
@record(kw_only=False)
class NullMetadataValue(MetadataValue[None]):
    """Representation of null."""

    @public
    @property
    def value(self) -> None:
        """None: The wrapped null value."""
        return None


@whitelist_for_serdes
@record(kw_only=False)
class CodeLocationReconstructionMetadataValue(MetadataValue[str]):
    """Representation of some state data used to define the Definitions in a code location. Users
    are expected to serialize data before passing it to this class.

    Args:
        data (str): A string representing data used to define the Definitions in a
            code location.
    """

    data: PublicAttr[str]

    @public
    @property
    def value(self) -> str:
        """str: The wrapped code location state data."""
        return self.data


@whitelist_for_serdes
@record_custom(field_to_new_mapping={"name": "pool"})
class PoolMetadataValue(
    MetadataValue[str],
    IHaveNew,
):
    name: PublicAttr[str]

    def __new__(cls, pool: str):
        return super().__new__(cls, name=pool)

    @public
    @property
    def value(self) -> str:
        """str: The wrapped pool string."""
        return self.pool

    @public
    @property
    def pool(self) -> str:  # type: ignore
        return self.name


class NullFieldSerializer(FieldSerializer):
    def pack(self, value: Any, whitelist_map: WhitelistMap, descent_path: str) -> Any:
        return None

    def unpack(self, value: Any, whitelist_map: WhitelistMap, context: UnpackContext) -> Any:
        return None


@whitelist_for_serdes(
    field_serializers={"instance": NullFieldSerializer},
    kwargs_fields={"instance"},
    skip_when_none_fields={"instance"},
)
@record_custom(
    field_to_new_mapping={
        "class_name": "inst",
    }
)
class ObjectMetadataValue(
    MetadataValue[str],
    IHaveNew,
):
    """An instance of an unserializable object. Only the class name will be available across process,
    but the instance can be accessed within the origin process.
    """

    class_name: PublicAttr[str]
    instance: Optional[object] = None

    def __new__(
        cls,
        inst: Union[str, object],
        **kwargs,
    ):
        if isinstance(inst, str):
            class_name = inst
            instance = kwargs.get("instance", None)
        else:
            class_name = inst.__class__.__name__
            instance = inst
        return super().__new__(
            cls,
            class_name=class_name,
            instance=instance,
        )

    @public
    @property
    def value(self) -> str:
        return self.class_name
