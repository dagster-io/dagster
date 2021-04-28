import re
import warnings
from collections import namedtuple
from enum import Enum

from dagster import check, seven
from dagster.core.errors import DagsterInvalidAssetKey
from dagster.serdes import DefaultNamedTupleSerializer, whitelist_for_serdes
from dagster.utils.backcompat import experimental_arg_warning, experimental_class_param_warning

from .event_metadata import EventMetadataEntry, last_file_comp, parse_metadata
from .utils import DEFAULT_OUTPUT, check_valid_name

ASSET_KEY_REGEX = re.compile("^[a-zA-Z0-9_.-]+$")  # alphanumeric, _, -, .
ASSET_KEY_SPLIT_REGEX = re.compile("[^a-zA-Z0-9_]")
ASSET_KEY_STRUCTURED_DELIMITER = "."


def validate_asset_key_string(s):
    if not s or not ASSET_KEY_REGEX.match(s):
        raise DagsterInvalidAssetKey()

    return s


def parse_asset_key_string(s):
    return list(filter(lambda x: x, re.split(ASSET_KEY_SPLIT_REGEX, s)))


@whitelist_for_serdes
class AssetKey(namedtuple("_AssetKey", "path")):
    """Object representing the structure of an asset key.  Takes in a sanitized string, list of
    strings, or tuple of strings.

    Example usage:

    .. code-block:: python

        @solid
        def emit_metadata_solid(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey('flat_asset_key'),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @solid
        def structured_asset_key_solid(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(['parent', 'child', 'grandchild']),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @solid
        def structured_asset_key_solid_2(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(('parent', 'child', 'grandchild')),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

    Args:
        path (str|str[]|str()): String, list of strings, or tuple of strings.  A list of strings
            represent the hierarchical structure of the asset_key.
    """

    def __new__(cls, path=None):
        if isinstance(path, str):
            path = [path]
        elif isinstance(path, list):
            path = check.list_param(path, "path", of_type=str)
        else:
            path = check.tuple_param(path, "path", of_type=str)

        return super(AssetKey, cls).__new__(cls, path=path)

    def __str__(self):
        return "AssetKey({})".format(self.path)

    def __repr__(self):
        return "AssetKey({})".format(self.path)

    def __hash__(self):
        return hash(tuple(self.path))

    def __eq__(self, other):
        if not isinstance(other, AssetKey):
            return False
        return self.to_string() == other.to_string()

    def to_string(self, legacy=False):
        if not self.path:
            return None
        if legacy:
            return ASSET_KEY_STRUCTURED_DELIMITER.join(self.path)
        return seven.json.dumps(self.path)

    @staticmethod
    def from_db_string(asset_key_string):
        if not asset_key_string:
            return None
        if asset_key_string[0] == "[":
            # is a json string
            try:
                path = seven.json.loads(asset_key_string)
            except seven.JSONDecodeError:
                path = parse_asset_key_string(asset_key_string)
        else:
            path = parse_asset_key_string(asset_key_string)
        return AssetKey(path)

    @staticmethod
    def get_db_prefix(path, legacy=False):
        check.list_param(path, "path", of_type=str)
        if legacy:
            return ASSET_KEY_STRUCTURED_DELIMITER.join(path)
        return seven.json.dumps(path)[:-2]  # strip trailing '"]' from json string

    @staticmethod
    def from_graphql_input(asset_key):
        if asset_key and asset_key.get("path"):
            return AssetKey(asset_key.get("path"))
        return None


@whitelist_for_serdes
class AssetLineageInfo(namedtuple("_AssetLineageInfo", "asset_key partitions")):
    def __new__(cls, asset_key, partitions=None):
        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        partitions = check.opt_set_param(partitions, "partitions", str)
        return super(AssetLineageInfo, cls).__new__(cls, asset_key=asset_key, partitions=partitions)


class Output(namedtuple("_Output", "value output_name metadata_entries")):
    """Event corresponding to one of a solid's outputs.

    Solid compute functions must explicitly yield events of this type when they have more than
    one output, or when they also yield events of other types, or when defining a solid using the
    :py:class:`SolidDefinition` API directly.

    Outputs are values produced by solids that will be consumed by downstream solids in a pipeline.
    They are type-checked at solid boundaries when their corresponding :py:class:`OutputDefinition`
    or the downstream :py:class:`InputDefinition` is typed.

    Args:
        value (Any): The value returned by the compute function.
        output_name (Optional[str]): Name of the corresponding output definition. (default:
            "result")
        metadata_entries (Optional[Union[EventMetadataEntry, PartitionMetadataEntry]]):
            (Experimental) A set of metadata entries to attach to events related to this Output.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __new__(cls, value, output_name=DEFAULT_OUTPUT, metadata_entries=None, metadata=None):
        if metadata_entries:
            experimental_arg_warning("metadata_entries", "Output.__new__")
        elif metadata:
            experimental_arg_warning("metadata", "Output.__new__")

        return super(Output, cls).__new__(
            cls,
            value,
            check.str_param(output_name, "output_name"),
            parse_metadata(metadata, metadata_entries),
        )


class DynamicOutput(namedtuple("_DynamicOutput", "value mapping_key output_name metadata_entries")):
    """
    (Experimental) Variant of :py:class:`Output <dagster.Output>` used to support
    dynamic mapping & collect. Each ``DynamicOutput`` produced by a solid represents
    one item in a set that can be processed individually with ``map`` or gathered
    with ``collect``.

    Each ``DynamicOutput`` must have a unique ``mapping_key`` to distinguish it with it's set.

    Args:
        value (Any):
            The value returned by the compute function.
        mapping_key (str):
            The key that uniquely identifies this dynamic value relative to its peers.
            This key will be used to identify the downstream solids when mapped, ie
            ``mapped_solid[example_mapping_key]``
        output_name (Optional[str]):
            Name of the corresponding :py:class:`DynamicOutputDefinition` defined on the solid.
            (default: "result")
        metadata_entries (Optional[Union[EventMetadataEntry, PartitionMetadataEntry]]):
            (Experimental) A set of metadata entries to attach to events related to this output.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __new__(
        cls, value, mapping_key, output_name=DEFAULT_OUTPUT, metadata_entries=None, metadata=None
    ):
        if metadata_entries:
            experimental_arg_warning("metadata_entries", "DynamicOutput.__new__")
        elif metadata:
            experimental_arg_warning("metadata", "DynamicOutput.__new__")

        return super(DynamicOutput, cls).__new__(
            cls,
            value,
            check_valid_name(check.str_param(mapping_key, "mapping_key")),
            check.str_param(output_name, "output_name"),
            parse_metadata(metadata, metadata_entries),
        )


@whitelist_for_serdes
class AssetMaterialization(
    namedtuple("_AssetMaterialization", "asset_key description metadata_entries partition tags")
):
    """Event indicating that a solid has materialized an asset.

    Solid compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that they have produced a materialized value as a
    side effect of computation. Unlike outputs, asset materializations can not be passed to other
    solids, and their persistence is controlled by solid logic, rather than by the Dagster
    framework.

    Solid authors should use these events to organize metadata about the side effects of their
    computations, enabling tooling like the Assets dashboard in Dagit.

    Args:
        asset_key (str|List[str]|AssetKey): A key to identify the materialized asset across pipeline
            runs
        description (Optional[str]): A longer human-readable description of the materialized value.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            materialized value.
        partition (Optional[str]): The name of the partition that was materialized.
        tags (Optional[Dict[str, str]]): (Experimental) Tag metadata for a given asset
            materialization.  Used for search and organization of the asset entry in the asset
            catalog in Dagit.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __new__(
        cls,
        asset_key,
        description=None,
        metadata_entries=None,
        partition=None,
        tags=None,
        metadata=None,
    ):
        if isinstance(asset_key, AssetKey):
            check.inst_param(asset_key, "asset_key", AssetKey)
        elif isinstance(asset_key, str):
            asset_key = AssetKey(parse_asset_key_string(asset_key))
        elif isinstance(asset_key, list):
            check.is_list(asset_key, of_type=str)
            asset_key = AssetKey(asset_key)
        else:
            check.is_tuple(asset_key, of_type=str)
            asset_key = AssetKey(asset_key)

        if tags:
            experimental_class_param_warning("tags", "AssetMaterialization")

        return super(AssetMaterialization, cls).__new__(
            cls,
            asset_key=asset_key,
            description=check.opt_str_param(description, "description"),
            metadata_entries=parse_metadata(metadata, metadata_entries),
            partition=check.opt_str_param(partition, "partition"),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
        )

    @property
    def label(self):
        return " ".join(self.asset_key.path)

    @staticmethod
    def file(path, description=None, asset_key=None):
        """Static constructor for standard materializations corresponding to files on disk.

        Args:
            path (str): The path to the file.
            description (Optional[str]): A human-readable description of the materialization.
        """
        if not asset_key:
            asset_key = path

        return AssetMaterialization(
            asset_key=asset_key,
            description=description,
            metadata_entries=[EventMetadataEntry.fspath(path)],
        )


class MaterializationSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(cls, storage_dict, klass):
        # override the default `from_storage_dict` implementation in order to skip the deprecation
        # warning for historical Materialization events, loaded from event_log storage
        return Materialization(skip_deprecation_warning=True, **storage_dict)


@whitelist_for_serdes(serializer=MaterializationSerializer)
class Materialization(
    namedtuple("_Materialization", "label description metadata_entries asset_key partition")
):
    """Event indicating that a solid has materialized a value.

    Solid compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that they have produced a materialized value as a
    side effect of computation. Unlike outputs, materializations can not be passed to other solids,
    and their persistence is controlled by solid logic, rather than by the Dagster framework.

    Solid authors should use these events to organize metadata about the side effects of their
    computations to enable downstream tooling like artifact catalogues and diff tools.

    Args:
        label (str): A short display name for the materialized value.
        description (Optional[str]): A longer human-radable description of the materialized value.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            materialized value.
        asset_key (Optional[str|AssetKey]): An optional parameter to identify the materialized asset
            across pipeline runs
        partition (Optional[str]): The name of the partition that was materialized.
    """

    def __new__(
        cls,
        label=None,
        description=None,
        metadata_entries=None,
        asset_key=None,
        partition=None,
        skip_deprecation_warning=False,
    ):
        if asset_key and isinstance(asset_key, str):
            asset_key = AssetKey(parse_asset_key_string(asset_key))
        else:
            check.opt_inst_param(asset_key, "asset_key", AssetKey)

        if not label:
            check.param_invariant(
                asset_key and asset_key.path,
                "label",
                "Either label or asset_key with a path must be provided",
            )
            label = asset_key.to_string()

        if not skip_deprecation_warning:
            warnings.warn("`Materialization` is deprecated; use `AssetMaterialization` instead.")

        return super(Materialization, cls).__new__(
            cls,
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
            asset_key=asset_key,
            partition=check.opt_str_param(partition, "partition"),
        )

    @staticmethod
    def file(path, description=None, asset_key=None):
        """Static constructor for standard materializations corresponding to files on disk.

        Args:
            path (str): The path to the file.
            description (Optional[str]): A human-readable description of the materialization.
        """
        return Materialization(
            label=last_file_comp(path),
            description=description,
            metadata_entries=[EventMetadataEntry.fspath(path)],
            asset_key=asset_key,
        )


@whitelist_for_serdes
class ExpectationResult(
    namedtuple("_ExpectationResult", "success label description metadata_entries")
):
    """Event corresponding to a data quality test.

    Solid compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that a data quality test has produced a (positive or
    negative) result.

    Args:
        success (bool): Whether the expectation passed or not.
        label (Optional[str]): Short display name for expectation. Defaults to "result".
        description (Optional[str]): A longer human-readable description of the expectation.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            expectation.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __new__(cls, success, label=None, description=None, metadata_entries=None, metadata=None):
        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            label=check.opt_str_param(label, "label", "result"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=parse_metadata(metadata, metadata_entries),
        )


@whitelist_for_serdes
class TypeCheck(namedtuple("_TypeCheck", "success description metadata_entries")):
    """Event corresponding to a successful typecheck.

    Events of this type should be returned by user-defined type checks when they need to encapsulate
    additional metadata about a type check's success or failure. (i.e., when using
    :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type>`, or the underlying
    :py:func:`PythonObjectDagsterType` API.)

    Solid compute functions should generally avoid yielding events of this type to avoid confusion.

    Args:
        success (bool): ``True`` if the type check succeeded, ``False`` otherwise.
        description (Optional[str]): A human-readable description of the type check.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            type check.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __new__(cls, success, description=None, metadata_entries=None, metadata=None):
        return super(TypeCheck, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=parse_metadata(metadata, metadata_entries),
        )


class Failure(Exception):
    """Event indicating solid failure.

    Raise events of this type from within solid compute functions or custom type checks in order to
    indicate an unrecoverable failure in user code to the Dagster machinery and return
    structured metadata about the failure.

    Args:
        description (Optional[str]): A human-readable description of the failure.
        metadata_entries (Optional[List[EventMetadataEntry]]): Arbitrary metadata about the
            failure.
        metadata (Optional[Dict[str, Union[str, float, int, Dict, EventMetadata]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a EventMetadata static method.
    """

    def __init__(self, description=None, metadata_entries=None, metadata=None):
        super(Failure, self).__init__(description)
        self.description = check.opt_str_param(description, "description")
        self.metadata_entries = parse_metadata(metadata, metadata_entries)


class RetryRequested(Exception):
    """
    An exception to raise from a solid to indicate that it should be retried.

    Args:
        max_retries (Optional[int]):
            The max number of retries this step should attempt before failing
        seconds_to_wait (Optional[Union[float,int]]):
            Seconds to wait before restarting the step after putting the step in
            to the up_for_retry state

    Example:

        .. code-block:: python

            @solid
            def flakes():
                try:
                    flakey_operation()
                except:
                    raise RetryRequested(max_retries=3)
    """

    def __init__(self, max_retries=1, seconds_to_wait=None):
        super(RetryRequested, self).__init__()
        self.max_retries = check.int_param(max_retries, "max_retries")
        self.seconds_to_wait = check.opt_numeric_param(seconds_to_wait, "seconds_to_wait")


class ObjectStoreOperationType(Enum):
    SET_OBJECT = "SET_OBJECT"
    GET_OBJECT = "GET_OBJECT"
    RM_OBJECT = "RM_OBJECT"
    CP_OBJECT = "CP_OBJECT"


class ObjectStoreOperation(
    namedtuple(
        "_ObjectStoreOperation",
        "op key dest_key obj serialization_strategy_name object_store_name value_name version mapping_key",
    )
):
    """This event is used internally by Dagster machinery when values are written to and read from
    an ObjectStore.

    Users should not import this class or yield events of this type from user code.

    Args:
        op (ObjectStoreOperationType): The type of the operation on the object store.
        key (str): The key of the object on which the operation was performed.
        dest_key (Optional[str]): The destination key, if any, to which the object was copied.
        obj (Any): The object, if any, retrieved by the operation.
        serialization_strategy_name (Optional[str]): The name of the serialization strategy, if any,
            employed by the operation
        object_store_name (Optional[str]): The name of the object store that performed the
            operation.
        value_name (Optional[str]): The name of the input/output
        version (Optional[str]): (Experimental) The version of the stored data.
        mapping_key (Optional[str]): The mapping key when a dynamic output is used.
    """

    def __new__(
        cls,
        op,
        key,
        dest_key=None,
        obj=None,
        serialization_strategy_name=None,
        object_store_name=None,
        value_name=None,
        version=None,
        mapping_key=None,
    ):
        return super(ObjectStoreOperation, cls).__new__(
            cls,
            op=op,
            key=check.str_param(key, "key"),
            dest_key=check.opt_str_param(dest_key, "dest_key"),
            obj=obj,
            serialization_strategy_name=check.opt_str_param(
                serialization_strategy_name, "serialization_strategy_name"
            ),
            object_store_name=check.opt_str_param(object_store_name, "object_store_name"),
            value_name=check.opt_str_param(value_name, "value_name"),
            version=check.opt_str_param(version, "version"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        )

    @classmethod
    def serializable(cls, inst, **kwargs):
        return cls(
            **dict(
                {
                    "op": inst.op.value,
                    "key": inst.key,
                    "dest_key": inst.dest_key,
                    "obj": None,
                    "serialization_strategy_name": inst.serialization_strategy_name,
                    "object_store_name": inst.object_store_name,
                    "value_name": inst.value_name,
                    "version": inst.version,
                },
                **kwargs,
            )
        )


class HookExecutionResult(namedtuple("_HookExecutionResult", "hook_name is_skipped")):
    """This event is used internally to indicate the execution result of a hook, e.g. whether the
    user-defined hook function is skipped.

    Args:
        hook_name (str): The name of the hook.
        is_skipped (bool): ``False`` if the hook_fn is executed, ``True`` otheriwse.
    """

    def __new__(cls, hook_name, is_skipped=None):
        return super(HookExecutionResult, cls).__new__(
            cls,
            hook_name=check.str_param(hook_name, "hook_name"),
            is_skipped=check.opt_bool_param(is_skipped, "is_skipped", default=False),
        )
