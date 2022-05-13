import functools
import os
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Union,
    cast,
)

import dagster._check as check
import dagster.seven as seven
from dagster.core.errors import DagsterInvalidMetadata
from dagster.serdes import whitelist_for_serdes
from dagster.utils.backcompat import (
    canonicalize_backcompat_args,
    deprecation_warning,
    experimental,
    experimental_class_warning,
)

from .table import TableColumn, TableColumnConstraints, TableConstraints, TableRecord, TableSchema

if TYPE_CHECKING:
    from dagster.core.definitions.events import AssetKey

RawMetadataValue = Union[
    "MetadataValue",
    dict,
    float,
    int,
    list,
    str,
]

MetadataMapping = Mapping[str, "MetadataValue"]
MetadataUserInput = Mapping[str, RawMetadataValue]


def last_file_comp(path: str) -> str:
    return os.path.basename(os.path.normpath(path))


# ########################
# ##### NORMALIZATION
# ########################


def normalize_metadata(
    metadata: Mapping[str, RawMetadataValue],
    metadata_entries: Sequence[Union["MetadataEntry", "PartitionMetadataEntry"]],
    allow_invalid: bool = False,
) -> List[Union["MetadataEntry", "PartitionMetadataEntry"]]:
    if metadata and metadata_entries:
        raise DagsterInvalidMetadata(
            "Attempted to provide both `metadata` and `metadata_entries` arguments to an event. "
            "Must provide only one of the two."
        )

    if metadata_entries:
        deprecation_warning(
            'Argument "metadata_entries"',
            "0.15.0",
            additional_warn_txt="Use argument `metadata` instead. The `MetadataEntry` `description` attribute is also deprecated-- argument `metadata` takes a label: value dictionary.",
            stacklevel=4,  # to get the caller of `normalize_metadata`
        )
        return check.list_param(
            metadata_entries, "metadata_entries", (MetadataEntry, PartitionMetadataEntry)
        )

    # This is a stopgap measure to deal with unsupported metadata values, which occur when we try
    # to convert arbitrary metadata (on e.g. OutputDefinition) to a MetadataValue, which is required
    # for serialization. This will cause unsupported values to be silently replaced with a
    # string placeholder.
    elif allow_invalid:
        metadata_entries = []
        for k, v in metadata.items():
            try:
                metadata_entries.append(package_metadata_value(k, v))
            except DagsterInvalidMetadata:
                deprecation_warning(
                    "Support for arbitrary metadata values",
                    "0.15.0",
                    additional_warn_txt=f"In the future, all user-supplied metadata values must be one of {RawMetadataValue}",
                    stacklevel=4,  # to get the caller of `normalize_metadata`
                )
                metadata_entries.append(
                    MetadataEntry.text(f"[{v.__class__.__name__}] (unserializable)", k)
                )
        return metadata_entries

    return [
        package_metadata_value(k, v)
        for k, v in check.opt_dict_param(metadata, "metadata", key_type=str).items()
    ]


def normalize_metadata_value(raw_value: RawMetadataValue):
    from dagster.core.definitions.events import AssetKey

    if isinstance(raw_value, MetadataValue):
        return raw_value
    elif isinstance(raw_value, str):
        return MetadataValue.text(raw_value)
    elif isinstance(raw_value, float):
        return MetadataValue.float(raw_value)
    elif isinstance(raw_value, bool):
        return MetadataValue.bool(raw_value)
    elif isinstance(raw_value, int):
        return MetadataValue.int(raw_value)
    elif isinstance(raw_value, dict):
        return MetadataValue.json(raw_value)
    elif isinstance(raw_value, os.PathLike):
        return MetadataValue.path(raw_value)
    elif isinstance(raw_value, AssetKey):
        return MetadataValue.asset(raw_value)
    elif isinstance(raw_value, TableSchema):
        return MetadataValue.table_schema(raw_value)

    raise DagsterInvalidMetadata(
        f"Its type was {type(raw_value)}. Consider wrapping the value with the appropriate "
        "MetadataValue type."
    )


def package_metadata_value(label: str, raw_value: RawMetadataValue) -> "MetadataEntry":
    check.str_param(label, "label")

    if isinstance(raw_value, (MetadataEntry, PartitionMetadataEntry)):
        raise DagsterInvalidMetadata(
            f"Expected a metadata value, found an instance of {raw_value.__class__.__name__}. Consider "
            "instead using a MetadataValue wrapper for the value."
        )
    try:
        value = normalize_metadata_value(raw_value)
    except DagsterInvalidMetadata as e:
        raise DagsterInvalidMetadata(
            f'Could not resolve the metadata value for "{label}" to a known type. {e}'
        ) from None
    return MetadataEntry(label=label, value=value)


# ########################
# ##### METADATA VALUE
# ########################


class MetadataValue:
    """Utility class to wrap metadata values passed into Dagster events so that they can be
    displayed in Dagit and other tooling.

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

    @staticmethod
    def text(text: str) -> "TextMetadataValue":
        """Static constructor for a metadata value wrapping text as
        :py:class:`TextMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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

    @staticmethod
    def url(url: str) -> "UrlMetadataValue":
        """Static constructor for a metadata value wrapping a URL as
        :py:class:`UrlMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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

    @staticmethod
    def path(path: Union[str, os.PathLike]) -> "PathMetadataValue":
        """Static constructor for a metadata value wrapping a path as
        :py:class:`PathMetadataValue`. For example:

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

    @staticmethod
    def json(data: Dict[str, Any]) -> "JsonMetadataValue":
        """Static constructor for a metadata value wrapping a path as
        :py:class:`JsonMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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
            data (Dict[str, Any]): The JSON data for a metadata entry.
        """
        return JsonMetadataValue(data)

    @staticmethod
    def md(data: str) -> "MarkdownMetadataValue":
        """Static constructor for a metadata value wrapping markdown data as
        :py:class:`MarkdownMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:


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

    @staticmethod
    def python_artifact(python_artifact: Callable) -> "PythonArtifactMetadataValue":
        """Static constructor for a metadata value wrapping a python artifact as
        :py:class:`PythonArtifactMetadataValue`. Can be used as the value type for the
        `metadata` parameter for supported events. For example:

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

    @staticmethod
    def float(value: float) -> "FloatMetadataValue":
        """Static constructor for a metadata value wrapping a float as
        :py:class:`FloatMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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

    @staticmethod
    def int(value: int) -> "IntMetadataValue":
        """Static constructor for a metadata value wrapping an int as
        :py:class:`IntMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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

    @staticmethod
    def bool(value: bool) -> "BoolMetadataValue":
        """Static constructor for a metadata value wrapping a bool as
        :py:class:`BoolMetadataValuye`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

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

    @staticmethod
    def pipeline_run(run_id: str) -> "DagsterPipelineRunMetadataValue":
        check.str_param(run_id, "run_id")
        return DagsterPipelineRunMetadataValue(run_id)

    @staticmethod
    def dagster_run(run_id: str) -> "DagsterPipelineRunMetadataValue":
        """Static constructor for a metadata value wrapping a reference to a Dagster run.

        Args:
            run_id (str): The ID of the run.
        """
        return MetadataValue.pipeline_run(run_id)

    @staticmethod
    def asset(asset_key: "AssetKey") -> "DagsterAssetMetadataValue":
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

        from dagster.core.definitions.events import AssetKey

        check.inst_param(asset_key, "asset_key", AssetKey)
        return DagsterAssetMetadataValue(asset_key)

    @staticmethod
    @experimental
    def table(
        records: List[TableRecord], schema: Optional[TableSchema] = None
    ) -> "TableMetadataValue":
        """Static constructor for a metadata value wrapping arbitrary tabular data as
        :py:class:`TableMetadataValue`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield ExpectationResult(
                    success=not has_errors,
                    label="is_valid",
                    metadata={
                        "errors": MetadataValue.table(
                            records=[
                                TableRecord(code="invalid-data-type", row=2, col="name"}]
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

        Args:
            records (List[TableRecord]): The data as a list of records (i.e. rows).
            schema (Optional[TableSchema]): A schema for the table.
        """
        return TableMetadataValue(records, schema)

    @staticmethod
    def table_schema(
        schema: TableSchema,
    ) -> "TableSchemaMetadataValue":
        """Static constructor for a metadata value wrapping a table schema as
        :py:class:`TableSchemaMetadataValue`. Can be used as the value type
        for the `metadata` parameter for supported events. For example:

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


# ########################
# ##### METADATA VALUE TYPES
# ########################

# NOTE: We have `type: ignore` in a few places below because mypy complains about an instance method
# (e.g. `text`) overriding a static method on the superclass of the same name. This is not a concern
# for us because these static methods should never be called on instances.

# NOTE: `XMetadataValue` classes are serialized with a storage name of `XMetadataEntryData` to
# maintain backward compatibility. See docstring of `whitelist_for_serdes` for more info.


@whitelist_for_serdes(storage_name="TextMetadataEntryData")
class TextMetadataValue(  # type: ignore
    NamedTuple(
        "_TextMetadataValue",
        [
            ("text", Optional[str]),
        ],
    ),
    MetadataValue,
):
    """Container class for text metadata entry data.

    Args:
        text (Optional[str]): The text data.
    """

    def __new__(cls, text: Optional[str]):
        return super(TextMetadataValue, cls).__new__(
            cls, check.opt_str_param(text, "text", default="")
        )


@whitelist_for_serdes(storage_name="UrlMetadataEntryData")
class UrlMetadataValue(  # type: ignore
    NamedTuple(
        "_UrlMetadataValue",
        [
            ("url", Optional[str]),
        ],
    ),
    MetadataValue,
):
    """Container class for URL metadata entry data.

    Args:
        url (Optional[str]): The URL as a string.
    """

    def __new__(cls, url: Optional[str]):
        return super(UrlMetadataValue, cls).__new__(
            cls, check.opt_str_param(url, "url", default="")
        )


@whitelist_for_serdes(storage_name="PathMetadataEntryData")
class PathMetadataValue(  # type: ignore
    NamedTuple("_PathMetadataValue", [("path", Optional[str])]), MetadataValue
):
    """Container class for path metadata entry data.

    Args:
        path (Optional[str]): The path as a string or conforming to os.PathLike.
    """

    def __new__(cls, path: Optional[Union[str, os.PathLike]]):
        return super(PathMetadataValue, cls).__new__(
            cls, check.opt_path_param(path, "path", default="")
        )


@whitelist_for_serdes(storage_name="JsonMetadataEntryData")
class JsonMetadataValue(
    NamedTuple(
        "_JsonMetadataValue",
        [
            ("data", Dict[str, Any]),
        ],
    ),
    MetadataValue,
):
    """Container class for JSON metadata entry data.

    Args:
        data (Dict[str, Any]): The JSON data.
    """

    def __new__(cls, data: Optional[Dict[str, Any]]):
        data = check.opt_dict_param(data, "data", key_type=str)
        try:
            # check that the value is JSON serializable
            seven.dumps(data)
        except TypeError:
            raise DagsterInvalidMetadata("Value is a dictionary but is not JSON serializable.")
        return super(JsonMetadataValue, cls).__new__(cls, data)


@whitelist_for_serdes(storage_name="MarkdownMetadataEntryData")
class MarkdownMetadataValue(
    NamedTuple(
        "_MarkdownMetadataValue",
        [
            ("md_str", Optional[str]),
        ],
    ),
    MetadataValue,
):
    """Container class for markdown metadata entry data.

    Args:
        md_str (Optional[str]): The markdown as a string.
    """

    def __new__(cls, md_str: Optional[str]):
        return super(MarkdownMetadataValue, cls).__new__(
            cls, check.opt_str_param(md_str, "md_str", default="")
        )


@whitelist_for_serdes(storage_name="PythonArtifactMetadataEntryData")
class PythonArtifactMetadataValue(
    NamedTuple(
        "_PythonArtifactMetadataValue",
        [
            ("module", str),
            ("name", str),
        ],
    ),
    MetadataValue,
):
    """Container class for python artifact metadata entry data.

    Args:
        module (str): The module where the python artifact can be found
        name (str): The name of the python artifact
    """

    def __new__(cls, module: str, name: str):
        return super(PythonArtifactMetadataValue, cls).__new__(
            cls, check.str_param(module, "module"), check.str_param(name, "name")
        )


@whitelist_for_serdes(storage_name="FloatMetadataEntryData")
class FloatMetadataValue(
    NamedTuple(
        "_FloatMetadataValue",
        [
            ("value", Optional[float]),
        ],
    ),
    MetadataValue,
):
    """Container class for float metadata entry data.

    Args:
        value (Optional[float]): The float value.
    """

    def __new__(cls, value: Optional[float]):
        return super(FloatMetadataValue, cls).__new__(cls, check.opt_float_param(value, "value"))


@whitelist_for_serdes(storage_name="IntMetadataEntryData")
class IntMetadataValue(
    NamedTuple(
        "_IntMetadataValue",
        [
            ("value", Optional[int]),
        ],
    ),
    MetadataValue,
):
    """Container class for int metadata entry data.

    Args:
        value (Optional[int]): The int value.
    """

    def __new__(cls, value: Optional[int]):
        return super(IntMetadataValue, cls).__new__(cls, check.opt_int_param(value, "value"))


@whitelist_for_serdes(storage_name="BoolMetadataEntryData")
class BoolMetadataValue(
    NamedTuple("_BoolMetadataValue", [("value", Optional[bool])]),
    MetadataValue,
):
    """Container class for bool metadata entry data.

    Args:
        value (Optional[bool]): The bool value.
    """

    def __new__(cls, value: Optional[bool]):
        return super(BoolMetadataValue, cls).__new__(cls, check.opt_bool_param(value, "value"))


@whitelist_for_serdes(storage_name="DagsterPipelineRunMetadataEntryData")
class DagsterPipelineRunMetadataValue(
    NamedTuple(
        "_DagsterPipelineRunMetadataValue",
        [
            ("run_id", str),
        ],
    ),
    MetadataValue,
):
    """Representation of a dagster pipeline run.

    Args:
        run_id (str): The pipeline run id
    """

    def __new__(cls, run_id: str):
        return super(DagsterPipelineRunMetadataValue, cls).__new__(
            cls, check.str_param(run_id, "run_id")
        )


@whitelist_for_serdes(storage_name="DagsterAssetMetadataEntryData")
class DagsterAssetMetadataValue(
    NamedTuple("_DagsterAssetMetadataValue", [("asset_key", "AssetKey")]), MetadataValue
):
    """Representation of a dagster asset.

    Args:
        asset_key (AssetKey): The dagster asset key
    """

    def __new__(cls, asset_key: "AssetKey"):
        from dagster.core.definitions.events import AssetKey

        return super(DagsterAssetMetadataValue, cls).__new__(
            cls, check.inst_param(asset_key, "asset_key", AssetKey)
        )


@experimental
@whitelist_for_serdes(storage_name="TableMetadataEntryData")
class TableMetadataValue(
    NamedTuple(
        "_TableMetadataValue",
        [
            ("records", List[TableRecord]),
            ("schema", TableSchema),
        ],
    ),
    MetadataValue,
):
    """Container class for table metadata entry data.

    Args:
        records (TableRecord): The data as a list of records (i.e. rows).
        schema (Optional[TableSchema]): A schema for the table.
    """

    @staticmethod
    def infer_column_type(value):
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        else:
            return "string"

    def __new__(cls, records: List[TableRecord], schema: Optional[TableSchema]):

        check.list_param(records, "records", of_type=TableRecord)
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

        return super(TableMetadataValue, cls).__new__(
            cls,
            records,
            schema,
        )


@whitelist_for_serdes(storage_name="TableSchemaMetadataEntryData")
class TableSchemaMetadataValue(
    NamedTuple("_TableSchemaMetadataValue", [("schema", TableSchema)]), MetadataValue
):
    """Representation of a schema for arbitrary tabular data.

    Args:
        schema (TableSchema): The dictionary containing the schema representation.
    """

    def __new__(cls, schema: TableSchema):
        return super(TableSchemaMetadataValue, cls).__new__(
            cls, check.inst_param(schema, "schema", TableSchema)
        )


# ########################
# ##### METADATA ENTRY
# ########################


def deprecated_metadata_entry_constructor(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        deprecation_warning(
            f"Function `MetadataEntry.{fn.__name__}`",
            "0.15.0",
            additional_warn_txt=re.sub(
                r"\n\s*",
                " ",
                """
            The recommended way to supply metadata is to pass a `Dict[str,
            MetadataValue]` to the `metadata` keyword argument. To construct `MetadataEntry`
            directly, call constructor and pass a `MetadataValue`: `MetadataEntry(label="foo",
            value=MetadataValue.text("bar")",
            """,
            ),
        )
        return fn(*args, **kwargs)

    return wrapper


# NOTE: This would better be implemented as a generic with `MetadataValue` set as a
# typevar, but as of 2022-01-25 mypy does not support generics on NamedTuple.
#
# NOTE: This currently stores value in the `entry_data` NamedTuple attribute. In the next release,
# we will change the name of the NamedTuple property to `value`, and need to implement custom
# serialization so that it continues to be saved as `entry_data` for backcompat purposes.
@whitelist_for_serdes(storage_name="EventMetadataEntry")
class MetadataEntry(
    NamedTuple(
        "_MetadataEntry",
        [
            ("label", str),
            ("description", Optional[str]),
            ("entry_data", MetadataValue),
        ],
    ),
):
    """The standard structure for describing metadata for Dagster events.

    Lists of objects of this type can be passed as arguments to Dagster events and will be displayed
    in Dagit and other tooling.

    Should be yielded from within an IO manager to append metadata for a given input/output event.
    For other event types, passing a dict with `MetadataValue` values to the `metadata` argument
    is preferred.

    Args:
        label (str): Short display label for this metadata entry.
        description (Optional[str]): A human-readable description of this metadata entry.
        value (MetadataValue): Typed metadata entry data. The different types allow
            for customized display in tools like dagit.
    """

    def __new__(
        cls,
        label: str,
        description: Optional[str] = None,
        entry_data: Optional["RawMetadataValue"] = None,
        value: Optional["RawMetadataValue"] = None,
    ):
        if description is not None:
            deprecation_warning(
                'The "description" attribute on "MetadataEntry"',
                "0.15.0",
            )
        value = cast(
            RawMetadataValue,
            canonicalize_backcompat_args(
                new_val=value,
                new_arg="value",
                old_val=entry_data,
                old_arg="entry_data",
                breaking_version="0.15.0",
            ),
        )
        value = normalize_metadata_value(value)

        return super(MetadataEntry, cls).__new__(
            cls,
            check.str_param(label, "label"),
            check.opt_str_param(description, "description"),
            check.inst_param(value, "value", MetadataValue),
        )

    @property
    def value(self):
        """Alias of `entry_data`."""
        return self.entry_data

    @staticmethod
    @deprecated_metadata_entry_constructor
    def text(text: Optional[str], label: str, description: Optional[str] = None) -> "MetadataEntry":
        """Static constructor for a metadata entry containing text as
        :py:class:`TextMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[
                        MetadataEntry.text("Text-based metadata for this event", "text_metadata")
                    ],
                )

        Args:
            text (Optional[str]): The text of this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(label, description, TextMetadataValue(text))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def url(url: Optional[str], label: str, description: Optional[str] = None) -> "MetadataEntry":
        """Static constructor for a metadata entry containing a URL as
        :py:class:`UrlMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield AssetMaterialization(
                    asset_key="my_dashboard",
                    metadata_entries=[
                        MetadataEntry.url(
                            "http://mycoolsite.com/my_dashboard", label="dashboard_url"
                        ),
                    ],
                )

        Args:
            url (Optional[str]): The URL contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(label, description, UrlMetadataValue(url))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def path(path: Optional[str], label: str, description: Optional[str] = None) -> "MetadataEntry":
        """Static constructor for a metadata entry containing a path as
        :py:class:`PathMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[MetadataEntry.path("path/to/file", label="filepath")],
                )

        Args:
            path (Optional[str]): The path contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(label, description, PathMetadataValue(path))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def fspath(
        path: Optional[str], label: Optional[str] = None, description: Optional[str] = None
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry containing a filesystem path as
        :py:class:`PathMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[MetadataEntry.fspath("path/to/file")],
                )

        Args:
            path (Optional[str]): The path contained by this metadata entry.
            label (Optional[str]): Short display label for this metadata entry. Defaults to the
                base name of the path.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        if not label:
            path = cast(str, check.str_param(path, "path"))
            label = last_file_comp(path)

        return MetadataEntry.path(path, label, description)

    @staticmethod
    @deprecated_metadata_entry_constructor
    def json(
        data: Optional[Dict[str, Any]],
        label: str,
        description: Optional[str] = None,
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry containing JSON data as
        :py:class:`JsonMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield ExpectationResult(
                    success=not missing_things,
                    label="is_present",
                    metadata_entries=[
                        MetadataEntry.json(
                            label="metadata", data={"missing_columns": missing_things},
                        )
                    ],
                )

        Args:
            data (Optional[Dict[str, Any]]): The JSON data contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(label, description, JsonMetadataValue(data))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def md(md_str: Optional[str], label: str, description: Optional[str] = None) -> "MetadataEntry":
        """Static constructor for a metadata entry containing markdown data as
        :py:class:`MarkdownMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context, md_str):
                yield AssetMaterialization(
                    asset_key="info",
                    metadata_entries=[MetadataEntry.md(md_str=md_str)],
                )

        Args:
            md_str (Optional[str]): The markdown contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(label, description, MarkdownMetadataValue(md_str))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def python_artifact(
        python_artifact: Callable[..., Any], label: str, description: Optional[str] = None
    ) -> "MetadataEntry":
        check.callable_param(python_artifact, "python_artifact")
        return MetadataEntry(
            label,
            description,
            PythonArtifactMetadataValue(python_artifact.__module__, python_artifact.__name__),
        )

    @staticmethod
    @deprecated_metadata_entry_constructor
    def float(
        value: Optional[float], label: str, description: Optional[str] = None
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry containing float as
        :py:class:`FloatMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[MetadataEntry.float(calculate_bytes(df), "size (bytes)")],
                )

        Args:
            value (Optional[float]): The float value contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """

        return MetadataEntry(label, description, FloatMetadataValue(value))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def int(value: Optional[int], label: str, description: Optional[str] = None) -> "MetadataEntry":
        """Static constructor for a metadata entry containing int as
        :py:class:`IntMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[MetadataEntry.int(len(df), "number of rows")],
                )

        Args:
            value (Optional[int]): The int value contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """

        return MetadataEntry(label, description, IntMetadataValue(value))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def pipeline_run(run_id: str, label: str, description: Optional[str] = None) -> "MetadataEntry":
        check.str_param(run_id, "run_id")
        return MetadataEntry(label, description, DagsterPipelineRunMetadataValue(run_id))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def asset(
        asset_key: "AssetKey", label: str, description: Optional[str] = None
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry referencing a Dagster asset, by key.

        For example:

        .. code-block:: python

            @op
            def validate_table(context, df):
                yield AssetMaterialization(
                    asset_key=AssetKey("my_table"),
                    metadata_entries=[
                         MetadataEntry.asset(AssetKey('my_other_table'), "Related asset"),
                    ],
                )

        Args:
            asset_key (AssetKey): The asset key referencing the asset.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """

        from dagster.core.definitions.events import AssetKey

        check.inst_param(asset_key, "asset_key", AssetKey)
        return MetadataEntry(label, description, DagsterAssetMetadataValue(asset_key))

    @staticmethod
    @deprecated_metadata_entry_constructor
    @experimental
    def table(
        records: List[TableRecord],
        label: str,
        description: Optional[str] = None,
        schema: Optional[TableSchema] = None,
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry containing tabluar data as
        :py:class:`TableMetadataValue`. For example:

        .. code-block:: python

            @op
            def emit_metadata(context):
                yield ExpectationResult(
                    success=not has_errors,
                    label="is_valid",
                    metadata_entries=[
                        MetadataEntry.table(
                            label="errors",
                            records=[
                                TableRecord(code="invalid-data-type", row=2, col="name"}]
                            ],
                            schema=TableSchema(
                                columns=[
                                    TableColumn(name="code", type="string"),
                                    TableColumn(name="row", type="int"),
                                    TableColumn(name="col", type="string"),
                                ]
                            )
                        ),
                    ],
                )

        Args:
            records (List[TableRecord]): The data as a list of records (i.e. rows).
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
            schema (Optional[TableSchema]): A schema for the table. If none is provided, one will be
                automatically generated by examining the first record. The schema will include as columns all
                field names present in the first record, with a type of `"string"`, `"int"`,
                `"bool"` or `"float"` inferred from the first record's values. If a value does
                not directly match one of the above types, it will be treated as a string.
        """
        return MetadataEntry(label, description, TableMetadataValue(records, schema))

    @staticmethod
    @deprecated_metadata_entry_constructor
    def table_schema(
        schema: TableSchema, label: str, description: Optional[str] = None
    ) -> "MetadataEntry":
        """Static constructor for a metadata entry containing a table schema as
        :py:class:`TableSchemaMetadataValue`. For example:

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
                metadata_entries=[
                    MetadataEntry.table_schema(
                        schema,
                        label='schema',
                    )
                ]
            )

        Args:
            schema (TableSchema): The table schema for a metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return MetadataEntry(
            label,
            description,
            TableSchemaMetadataValue(schema),
        )


class PartitionMetadataEntry(
    NamedTuple(
        "_PartitionMetadataEntry",
        [
            ("partition", str),
            ("entry", "MetadataEntry"),
        ],
    )
):
    """Event containing an :py:class:`MetadataEntry` and the name of a partition that the entry
    applies to.

    This can be yielded or returned in place of MetadataEntries for cases where you are trying
    to associate metadata more precisely.
    """

    def __new__(cls, partition: str, entry: MetadataEntry):
        experimental_class_warning("PartitionMetadataEntry")
        return super(PartitionMetadataEntry, cls).__new__(
            cls,
            check.str_param(partition, "partition"),
            check.inst_param(entry, "entry", MetadataEntry),
        )
