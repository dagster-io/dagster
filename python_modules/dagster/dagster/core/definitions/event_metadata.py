import os
from collections import namedtuple
from typing import Any, Callable, Dict, Optional, Union

from dagster import check, seven
from dagster.core.errors import DagsterInvalidEventMetadata
from dagster.serdes import whitelist_for_serdes
from dagster.utils.backcompat import experimental_class_warning


def last_file_comp(path):
    return os.path.basename(os.path.normpath(path))


def parse_metadata_entry(label, value):
    check.str_param(label, "label")

    if isinstance(value, (EventMetadataEntry, PartitionMetadataEntry)):
        raise DagsterInvalidEventMetadata(
            f"Expected a metadata value, found an instance of {value.__class__.__name__}. Consider "
            "instead using a EventMetadata wrapper for the value, or using the `metadata_entries` "
            "parameter to pass in a List[EventMetadataEntry|PartitionMetadataEntry]."
        )

    if isinstance(
        value,
        (
            TextMetadataEntryData,
            UrlMetadataEntryData,
            PathMetadataEntryData,
            JsonMetadataEntryData,
            MarkdownMetadataEntryData,
            FloatMetadataEntryData,
            IntMetadataEntryData,
            PythonArtifactMetadataEntryData,
        ),
    ):
        return EventMetadataEntry(label, None, value)

    if isinstance(value, str):
        return EventMetadataEntry.text(value, label)

    if isinstance(value, float):
        return EventMetadataEntry.float(value, label)

    if isinstance(value, int):
        return EventMetadataEntry.int(value, label)

    if isinstance(value, (list, dict)):
        try:
            # check that the value is JSON serializable
            seven.dumps(value)
            return EventMetadataEntry.json(value, label)
        except TypeError:
            raise DagsterInvalidEventMetadata(
                f'Could not resolve the metadata value for "{label}" to a JSON serializable value. '
                "Consider wrapping the value with the appropriate EventMetadata type."
            )

    raise DagsterInvalidEventMetadata(
        f'Could not resolve the metadata value for "{label}" to a known type. Consider '
        "wrapping the value with the appropriate EventMetadata type."
    )


def parse_metadata(metadata, metadata_entries):
    if metadata and metadata_entries:
        raise DagsterInvalidEventMetadata(
            "Attempted to provide both `metadata` and `metadata_entries` arguments to an event. "
            "Must provide only one of the two."
        )

    if metadata_entries:
        return check.list_param(
            metadata_entries, "metadata_entries", (EventMetadataEntry, PartitionMetadataEntry)
        )

    return [
        parse_metadata_entry(k, v)
        for k, v in check.opt_dict_param(metadata, "metadata", key_type=str).items()
    ]


## Event metadata data types


@whitelist_for_serdes
class TextMetadataEntryData(namedtuple("_TextMetadataEntryData", "text")):
    """Container class for text metadata entry data.

    Args:
        text (Optional[str]): The text data.
    """

    def __new__(cls, text):
        return super(TextMetadataEntryData, cls).__new__(
            cls, check.opt_str_param(text, "text", default="")
        )


@whitelist_for_serdes
class UrlMetadataEntryData(namedtuple("_UrlMetadataEntryData", "url")):
    """Container class for URL metadata entry data.

    Args:
        url (Optional[str]): The URL as a string.
    """

    def __new__(cls, url):
        return super(UrlMetadataEntryData, cls).__new__(
            cls, check.opt_str_param(url, "url", default="")
        )


@whitelist_for_serdes
class PathMetadataEntryData(namedtuple("_PathMetadataEntryData", "path")):
    """Container class for path metadata entry data.

    Args:
        path (Optional[str]): The path as a string.
    """

    def __new__(cls, path):
        return super(PathMetadataEntryData, cls).__new__(
            cls, check.opt_str_param(path, "path", default="")
        )


@whitelist_for_serdes
class JsonMetadataEntryData(namedtuple("_JsonMetadataEntryData", "data")):
    """Container class for JSON metadata entry data.

    Args:
        data (Optional[Dict[str, Any]]): The JSON data.
    """

    def __new__(cls, data):
        return super(JsonMetadataEntryData, cls).__new__(
            cls, check.opt_dict_param(data, "data", key_type=str)
        )


@whitelist_for_serdes
class MarkdownMetadataEntryData(namedtuple("_MarkdownMetadataEntryData", "md_str")):
    """Container class for markdown metadata entry data.

    Args:
        md_str (Optional[str]): The markdown as a string.
    """

    def __new__(cls, md_str):
        return super(MarkdownMetadataEntryData, cls).__new__(
            cls, check.opt_str_param(md_str, "md_str", default="")
        )


@whitelist_for_serdes
class PythonArtifactMetadataEntryData(
    namedtuple("_PythonArtifactMetadataEntryData", "module name")
):
    """Container class for python artifact metadata entry data.

    Args:
        module (str): The module where the python artifact can be found
        name (str): The name of the python artifact
    """

    def __new__(cls, module, name):
        return super(PythonArtifactMetadataEntryData, cls).__new__(
            cls, check.str_param(module, "module"), check.str_param(name, "name")
        )


@whitelist_for_serdes
class FloatMetadataEntryData(namedtuple("_FloatMetadataEntryData", "value")):
    """Container class for float metadata entry data.

    Args:
        value (Optional[float]): The float value.
    """

    def __new__(cls, value):
        return super(FloatMetadataEntryData, cls).__new__(
            cls, check.opt_float_param(value, "value")
        )


@whitelist_for_serdes
class IntMetadataEntryData(namedtuple("_IntMetadataEntryData", "value")):
    """Container class for int metadata entry data.

    Args:
        value (Optional[int]): The int value.
    """

    def __new__(cls, value):
        return super(IntMetadataEntryData, cls).__new__(cls, check.opt_int_param(value, "value"))


@whitelist_for_serdes
class DagsterPipelineRunMetadataEntryData(
    namedtuple("_DagsterPipelineRunMetadataEntryData", "run_id")
):
    """Representation of a dagster pipeline run.

    Args:
        run_id (str): The pipeline run id
    """

    def __new__(cls, run_id):
        return super(DagsterPipelineRunMetadataEntryData, cls).__new__(
            cls, check.str_param(run_id, "run_id")
        )


@whitelist_for_serdes
class DagsterAssetMetadataEntryData(namedtuple("_DagsterAssetMetadataEntryData", "asset_key")):
    """Representation of a dagster asset.

    Args:
        asset_key (str): The dagster asset key
    """

    def __new__(cls, asset_key):
        from dagster.core.definitions.events import AssetKey

        return super(DagsterAssetMetadataEntryData, cls).__new__(
            cls, check.inst_param(asset_key, "asset_key", AssetKey)
        )


## for typing

EventMetadataEntryData = Union[
    TextMetadataEntryData,
    UrlMetadataEntryData,
    PathMetadataEntryData,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    FloatMetadataEntryData,
    IntMetadataEntryData,
    PythonArtifactMetadataEntryData,
    DagsterAssetMetadataEntryData,
    DagsterPipelineRunMetadataEntryData,
]

## for runtime checks

EntryDataUnion = (
    TextMetadataEntryData,
    UrlMetadataEntryData,
    PathMetadataEntryData,
    JsonMetadataEntryData,
    MarkdownMetadataEntryData,
    FloatMetadataEntryData,
    IntMetadataEntryData,
    PythonArtifactMetadataEntryData,
    DagsterAssetMetadataEntryData,
    DagsterPipelineRunMetadataEntryData,
)


class EventMetadata:
    """Utility class to wrap metadata values passed into Dagster events so that they can be
    displayed in Dagit and other tooling.

    .. code-block:: python

        @solid
        def emit_metadata_solid(context, df):
            yield AssetMaterialization(
                asset_key="my_dataset",
                metadata={
                    "my_text_label": "hello",
                    "dashboard_url": EventMetadata.url("http://mycoolsite.com/my_dashboard"),
                    "num_rows": 0,
                },
            )
    """

    @staticmethod
    def text(text: str) -> "TextMetadataEntryData":
        """Static constructor for a metadata value wrapping text as
        :py:class:`TextMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "my_text_label": EventMetadata.text("hello")
                    },
                )

        Args:
            text (str): The text string for a metadata entry.
        """
        return TextMetadataEntryData(text)

    @staticmethod
    def url(url: str) -> "UrlMetadataEntryData":
        """Static constructor for a metadata value wrapping a URL as
        :py:class:`UrlMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield AssetMaterialization(
                    asset_key="my_dashboard",
                    metadata={
                        "dashboard_url": EventMetadata.url("http://mycoolsite.com/my_dashboard"),
                    }
                )


        Args:
            url (str): The URL for a metadata entry.
        """
        return UrlMetadataEntryData(url)

    @staticmethod
    def path(path: str) -> "PathMetadataEntryData":
        """Static constructor for a metadata value wrapping a path as
        :py:class:`PathMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "filepath": EventMetadata.path("path/to/file"),
                    }
                )

        Args:
            path (str): The path for a metadata entry.
        """
        return PathMetadataEntryData(path)

    @staticmethod
    def json(data: Dict[str, Any]) -> "JsonMetadataEntryData":
        """Static constructor for a metadata value wrapping a path as
        :py:class:`JsonMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield ExpectationResult(
                    success=not missing_things,
                    label="is_present",
                    metadata={
                        "about my dataset": EventMetadata.json({"missing_columns": missing_things})
                    },
                )

        Args:
            data (Dict[str, Any]): The JSON data for a metadata entry.
        """
        return JsonMetadataEntryData(data)

    @staticmethod
    def md(data: str) -> "MarkdownMetadataEntryData":
        """Static constructor for a metadata value wrapping markdown data as
        :py:class:`MarkdownMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:


        .. code-block:: python

            @solid
            def emit_metadata_solid(context, md_str):
                yield AssetMaterialization(
                    asset_key="info",
                    metadata={
                        'Details': EventMetadata.md(md_str)
                    },
                )

        Args:
            md_str (str): The markdown for a metadata entry.
        """
        return MarkdownMetadataEntryData(data)

    @staticmethod
    def python_artifact(python_artifact: Callable) -> "PythonArtifactMetadataEntryData":
        """Static constructor for a metadata value wrapping a python artifact as
        :py:class:`PythonArtifactMetadataEntryData`. Can be used as the value type for the
        `metadata` parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "size (bytes)": EventMetadata.float(calculate_bytes(df)),
                    }
                )

        Args:
            value (Callable): The python class or function for a metadata entry.
        """
        check.callable_param(python_artifact, "python_artifact")
        return PythonArtifactMetadataEntryData(python_artifact.__module__, python_artifact.__name__)

    @staticmethod
    def float(value: float) -> "FloatMetadataEntryData":
        """Static constructor for a metadata value wrapping a float as
        :py:class:`FloatMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "size (bytes)": EventMetadata.float(calculate_bytes(df)),
                    }
                )

        Args:
            value (float): The float value for a metadata entry.
        """

        return FloatMetadataEntryData(value)

    @staticmethod
    def int(value: int) -> "IntMetadataEntryData":
        """Static constructor for a metadata entry wrapping an int as
        :py:class:`IntMetadataEntryData`. Can be used as the value type for the `metadata`
        parameter for supported events. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata={
                        "number of rows": EventMetadata.int(len(df)),
                    },
                )

        Args:
            value (int): The int value for a metadata entry.
        """

        return IntMetadataEntryData(value)

    @staticmethod
    def pipeline_run(run_id: str) -> "DagsterPipelineRunMetadataEntryData":
        check.str_param(run_id, "run_id")
        return DagsterPipelineRunMetadataEntryData(run_id)

    @staticmethod
    def asset(asset_key) -> "DagsterAssetMetadataEntryData":
        from dagster.core.definitions.events import AssetKey

        check.inst_param(asset_key, "asset_key", AssetKey)
        return DagsterAssetMetadataEntryData(asset_key)


@whitelist_for_serdes
class EventMetadataEntry(namedtuple("_EventMetadataEntry", "label description entry_data")):
    """The standard structure for describing metadata for Dagster events.

    Lists of objects of this type can be passed as arguments to Dagster events and will be displayed
    in Dagit and other tooling.

    Should be yielded from within an IO manager to append metadata for a given input/output event.
    For other event types, passing a dict with `EventMetadata` values to the `metadata` argument
    is preferred.

    Args:
        label (str): Short display label for this metadata entry.
        description (Optional[str]): A human-readable description of this metadata entry.
        entry_data (EventMetadataEntryData): Typed metadata entry data. The different types allow
            for customized display in tools like dagit.
    """

    def __new__(cls, label: str, description: Optional[str], entry_data: EventMetadataEntryData):
        return super(EventMetadataEntry, cls).__new__(
            cls,
            check.str_param(label, "label"),
            check.opt_str_param(description, "description"),
            check.inst_param(entry_data, "entry_data", EntryDataUnion),
        )

    @staticmethod
    def text(text, label, description=None):
        """Static constructor for a metadata entry containing text as
        :py:class:`TextMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[
                        EventMetadataEntry.text("Text-based metadata for this event", "text_metadata")
                    ],
                )

        Args:
            text (Optional[str]): The text of this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry(label, description, TextMetadataEntryData(text))

    @staticmethod
    def url(url, label, description=None):
        """Static constructor for a metadata entry containing a URL as
        :py:class:`UrlMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield AssetMaterialization(
                    asset_key="my_dashboard",
                    metadata_entries=[
                        EventMetadataEntry.url(
                            "http://mycoolsite.com/my_dashboard", label="dashboard_url"
                        ),
                    ],
                )

        Args:
            url (Optional[str]): The URL contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry(label, description, UrlMetadataEntryData(url))

    @staticmethod
    def path(path, label, description=None):
        """Static constructor for a metadata entry containing a path as
        :py:class:`PathMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[EventMetadataEntry.path("path/to/file", label="filepath")],
                )

        Args:
            path (Optional[str]): The path contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry(label, description, PathMetadataEntryData(path))

    @staticmethod
    def fspath(path, label=None, description=None):
        """Static constructor for a metadata entry containing a filesystem path as
        :py:class:`PathMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[EventMetadataEntry.fspath("path/to/file")],
                )

        Args:
            path (Optional[str]): The path contained by this metadata entry.
            label (str): Short display label for this metadata entry. Defaults to the
                base name of the path.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry.path(
            path, label if label is not None else last_file_comp(path), description
        )

    @staticmethod
    def json(data, label, description=None):
        """Static constructor for a metadata entry containing JSON data as
        :py:class:`JsonMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context):
                yield ExpectationResult(
                    success=not missing_things,
                    label="is_present",
                    metadata_entries=[
                        EventMetadataEntry.json(
                            label="metadata", data={"missing_columns": missing_things},
                        )
                    ],
                )

        Args:
            data (Optional[Dict[str, Any]]): The JSON data contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry(label, description, JsonMetadataEntryData(data))

    @staticmethod
    def md(md_str, label, description=None):
        """Static constructor for a metadata entry containing markdown data as
        :py:class:`MarkdownMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, md_str):
                yield AssetMaterialization(
                    asset_key="info",
                    metadata_entries=[EventMetadataEntry.md(md_str=md_str)],
                )

        Args:
            md_str (Optional[str]): The markdown contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """
        return EventMetadataEntry(label, description, MarkdownMetadataEntryData(md_str))

    @staticmethod
    def python_artifact(python_artifact, label, description=None):
        check.callable_param(python_artifact, "python_artifact")
        return EventMetadataEntry(
            label,
            description,
            PythonArtifactMetadataEntryData(python_artifact.__module__, python_artifact.__name__),
        )

    @staticmethod
    def float(value, label, description=None):
        """Static constructor for a metadata entry containing float as
        :py:class:`FloatMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[EventMetadataEntry.float(calculate_bytes(df), "size (bytes)")],
                )

        Args:
            value (Optional[float]): The float value contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """

        return EventMetadataEntry(label, description, FloatMetadataEntryData(value))

    @staticmethod
    def int(value, label, description=None):
        """Static constructor for a metadata entry containing int as
        :py:class:`IntMetadataEntryData`. For example:

        .. code-block:: python

            @solid
            def emit_metadata_solid(context, df):
                yield AssetMaterialization(
                    asset_key="my_dataset",
                    metadata_entries=[EventMetadataEntry.int(len(df), "number of rows")],
                )

        Args:
            value (Optional[int]): The int value contained by this metadata entry.
            label (str): Short display label for this metadata entry.
            description (Optional[str]): A human-readable description of this metadata entry.
        """

        return EventMetadataEntry(label, description, IntMetadataEntryData(value))

    @staticmethod
    def pipeline_run(run_id, label, description=None):
        check.str_param(run_id, "run_id")
        return EventMetadataEntry(label, description, DagsterPipelineRunMetadataEntryData(run_id))

    @staticmethod
    def asset(asset_key, label, description=None):
        from dagster.core.definitions.events import AssetKey

        check.inst_param(asset_key, "asset_key", AssetKey)
        return EventMetadataEntry(label, description, DagsterAssetMetadataEntryData(asset_key))


class PartitionMetadataEntry(namedtuple("_PartitionMetadataEntry", "partition entry")):
    """Event containing an :py:class:`EventMetdataEntry` and the name of a partition that the entry
    applies to.

    This can be yielded or returned in place of EventMetadataEntries for cases where you are trying
    to associate metadata more precisely.
    """

    def __new__(cls, partition: str, entry: EventMetadataEntry):
        experimental_class_warning("PartitionMetadataEntry")
        return super(PartitionMetadataEntry, cls).__new__(
            cls,
            check.str_param(partition, "partition"),
            check.inst_param(entry, "entry", EventMetadataEntry),
        )
