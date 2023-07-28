import re
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Generic,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
import dagster._seven as seven
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.data_version import DataVersion
from dagster._core.storage.tags import MULTIDIMENSIONAL_PARTITION_PREFIX, SYSTEM_TAG_PREFIX
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import NamedTupleSerializer
from dagster._utils.backcompat import experimental_class_param_warning

from .metadata import (
    MetadataFieldSerializer,
    MetadataMapping,
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from .utils import DEFAULT_OUTPUT, check_valid_name

if TYPE_CHECKING:
    from dagster._core.execution.context.output import OutputContext

ASSET_KEY_SPLIT_REGEX = re.compile("[^a-zA-Z0-9_]")
ASSET_KEY_DELIMITER = "/"


def parse_asset_key_string(s: str) -> Sequence[str]:
    return list(filter(lambda x: x, re.split(ASSET_KEY_SPLIT_REGEX, s)))


@whitelist_for_serdes
class AssetKey(NamedTuple("_AssetKey", [("path", PublicAttr[Sequence[str]])])):
    """Object representing the structure of an asset key.  Takes in a sanitized string, list of
    strings, or tuple of strings.

    Example usage:

    .. code-block:: python

        from dagster import op

        @op
        def emit_metadata(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey('flat_asset_key'),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @op
        def structured_asset_key(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(['parent', 'child', 'grandchild']),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

        @op
        def structured_asset_key_2(context, df):
            yield AssetMaterialization(
                asset_key=AssetKey(('parent', 'child', 'grandchild')),
                metadata={"text_metadata": "Text-based metadata for this event"},
            )

    Args:
        path (Sequence[str]): String, list of strings, or tuple of strings.  A list of strings
            represent the hierarchical structure of the asset_key.
    """

    def __new__(cls, path: Sequence[str]):
        if isinstance(path, str):
            path = [path]
        else:
            path = list(check.sequence_param(path, "path", of_type=str))

        return super(AssetKey, cls).__new__(cls, path=path)

    def __str__(self):
        return f"AssetKey({self.path})"

    def __repr__(self):
        return f"AssetKey({self.path})"

    def __hash__(self):
        return hash(tuple(self.path))

    def __eq__(self, other):
        if not isinstance(other, AssetKey):
            return False
        if len(self.path) != len(other.path):
            return False
        for i in range(0, len(self.path)):
            if self.path[i] != other.path[i]:
                return False
        return True

    def to_string(self) -> str:
        """E.g. '["first_component", "second_component"]'."""
        return seven.json.dumps(self.path)

    def to_user_string(self) -> str:
        """E.g. "first_component/second_component"."""
        return ASSET_KEY_DELIMITER.join(self.path)

    def to_python_identifier(self, suffix: Optional[str] = None) -> str:
        """Build a valid Python identifier based on the asset key that can be used for
        operation names or I/O manager keys.
        """
        path = list(self.path)

        if suffix is not None:
            path.append(suffix)

        return "__".join(path).replace("-", "_")

    @staticmethod
    def from_user_string(asset_key_string: str) -> "AssetKey":
        return AssetKey(asset_key_string.split(ASSET_KEY_DELIMITER))

    @staticmethod
    def from_db_string(asset_key_string: Optional[str]) -> Optional["AssetKey"]:
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
    def get_db_prefix(path: Sequence[str]):
        check.sequence_param(path, "path", of_type=str)
        return seven.json.dumps(path)[:-2]  # strip trailing '"]' from json string

    @staticmethod
    def from_graphql_input(graphql_input_asset_key: Mapping[str, Sequence[str]]) -> "AssetKey":
        return AssetKey(graphql_input_asset_key["path"])

    def to_graphql_input(self) -> Mapping[str, Sequence[str]]:
        return {"path": self.path}

    @staticmethod
    def from_coercible(arg: "CoercibleToAssetKey") -> "AssetKey":
        if isinstance(arg, AssetKey):
            return check.inst_param(arg, "arg", AssetKey)
        elif isinstance(arg, str):
            return AssetKey([arg])
        elif isinstance(arg, list):
            check.list_param(arg, "arg", of_type=str)
            return AssetKey(arg)
        elif isinstance(arg, tuple):
            check.tuple_param(arg, "arg", of_type=str)
            return AssetKey(arg)
        else:
            check.failed(f"Unexpected type for AssetKey: {type(arg)}")

    def has_prefix(self, prefix: Sequence[str]) -> bool:
        return len(self.path) >= len(prefix) and self.path[: len(prefix)] == prefix

    def with_prefix(self, prefix: "CoercibleToAssetKeyPrefix") -> "AssetKey":
        prefix = key_prefix_from_coercible(prefix)
        return AssetKey(list(prefix) + list(self.path))


class AssetKeyPartitionKey(NamedTuple):
    """An AssetKey with an (optional) partition key. Refers either to a non-partitioned asset or a
    partition of a partitioned asset.
    """

    asset_key: AssetKey
    partition_key: Optional[str] = None


CoercibleToAssetKey = Union[AssetKey, str, Sequence[str]]
CoercibleToAssetKeyPrefix = Union[str, Sequence[str]]


def check_opt_coercible_to_asset_key_prefix_param(
    prefix: Optional[CoercibleToAssetKeyPrefix], param_name: str
) -> Optional[Sequence[str]]:
    try:
        return key_prefix_from_coercible(prefix) if prefix is not None else None
    except check.CheckError:
        raise check.ParameterCheckError(
            f'Param "{param_name}" is not a string or a sequence of strings'
        )


def key_prefix_from_coercible(key_prefix: CoercibleToAssetKeyPrefix) -> Sequence[str]:
    if isinstance(key_prefix, str):
        return [key_prefix]
    elif isinstance(key_prefix, list):
        return key_prefix
    else:
        check.failed(f"Unexpected type for key_prefix: {type(key_prefix)}")


DynamicAssetKey = Callable[["OutputContext"], Optional[AssetKey]]


@whitelist_for_serdes
class AssetLineageInfo(
    NamedTuple("_AssetLineageInfo", [("asset_key", AssetKey), ("partitions", AbstractSet[str])])
):
    def __new__(cls, asset_key: AssetKey, partitions: Optional[AbstractSet[str]] = None):
        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        partitions = check.opt_set_param(partitions, "partitions", str)
        return super(AssetLineageInfo, cls).__new__(cls, asset_key=asset_key, partitions=partitions)


T = TypeVar("T")


class Output(Generic[T]):
    """Event corresponding to one of a op's outputs.

    Op compute functions must explicitly yield events of this type when they have more than
    one output, or when they also yield events of other types, or when defining a op using the
    :py:class:`OpDefinition` API directly.

    Outputs are values produced by ops that will be consumed by downstream ops in a job.
    They are type-checked at op boundaries when their corresponding :py:class:`Out`
    or the downstream :py:class:`In` is typed.

    Args:
        value (Any): The value returned by the compute function.
        output_name (Optional[str]): Name of the corresponding out. (default:
            "result")
        metadata (Optional[Dict[str, Union[str, float, int, MetadataValue]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
        data_version (Optional[DataVersion]): (Experimental) A data version to manually set
            for the asset.
    """

    def __init__(
        self,
        value: T,
        output_name: Optional[str] = DEFAULT_OUTPUT,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        data_version: Optional[DataVersion] = None,
    ):
        self._value = value
        self._output_name = check.str_param(output_name, "output_name")
        if data_version is not None:
            experimental_class_param_warning("data_version", "Output")
        self._data_version = check.opt_inst_param(data_version, "data_version", DataVersion)
        self._metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

    @property
    def metadata(self) -> MetadataMapping:
        return self._metadata

    @public
    @property
    def value(self) -> Any:
        """Any: The value returned by the compute function."""
        return self._value

    @public
    @property
    def output_name(self) -> str:
        """str: Name of the corresponding :py:class:`Out`."""
        return self._output_name

    @public
    @property
    def data_version(self) -> Optional[DataVersion]:
        """Optional[DataVersion]: A data version that was manually set on the `Output`."""
        return self._data_version

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Output)
            and self.value == other.value
            and self.output_name == other.output_name
            and self.metadata == other.metadata
        )


class DynamicOutput(Generic[T]):
    """Variant of :py:class:`Output <dagster.Output>` used to support
    dynamic mapping & collect. Each ``DynamicOutput`` produced by an op represents
    one item in a set that can be processed individually with ``map`` or gathered
    with ``collect``.

    Each ``DynamicOutput`` must have a unique ``mapping_key`` to distinguish it with it's set.

    Args:
        value (Any):
            The value returned by the compute function.
        mapping_key (str):
            The key that uniquely identifies this dynamic value relative to its peers.
            This key will be used to identify the downstream ops when mapped, ie
            ``mapped_op[example_mapping_key]``
        output_name (Optional[str]):
            Name of the corresponding :py:class:`DynamicOut` defined on the op.
            (default: "result")
        metadata (Optional[Dict[str, Union[str, float, int, MetadataValue]]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __init__(
        self,
        value: T,
        mapping_key: str,
        output_name: Optional[str] = DEFAULT_OUTPUT,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    ):
        self._mapping_key = check_valid_name(check.str_param(mapping_key, "mapping_key"))
        self._output_name = check.str_param(output_name, "output_name")
        self._value = value
        self._metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

    @property
    def metadata(self) -> Mapping[str, MetadataValue]:
        return self._metadata

    @public
    @property
    def mapping_key(self) -> str:
        """The mapping_key that was set for this DynamicOutput at instantiation."""
        return self._mapping_key

    @public
    @property
    def value(self) -> T:
        """The value that is returned by the compute function for this DynamicOut."""
        return self._value

    @public
    @property
    def output_name(self) -> str:
        """Name of the :py:class:`DynamicOut` defined on the op that this DynamicOut is associated with.
        """
        return self._output_name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DynamicOutput)
            and self.value == other.value
            and self.output_name == other.output_name
            and self.mapping_key == other.mapping_key
            and self.metadata == other.metadata
        )


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class AssetObservation(
    NamedTuple(
        "_AssetObservation",
        [
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
            ("partition", PublicAttr[Optional[str]]),
            ("tags", PublicAttr[Mapping[str, str]]),
        ],
    )
):
    """Event that captures metadata about an asset at a point in time.

    Args:
        asset_key (Union[str, List[str], AssetKey]): A key to identify the asset.
        partition (Optional[str]): The name of a partition of the asset that the metadata
            corresponds to.
        tags (Optional[Mapping[str, str]]): A mapping containing system-populated tags for the
            observation. Users should not pass values into this argument.
        metadata (Optional[Dict[str, Union[str, float, int, MetadataValue]]]):
            Arbitrary metadata about the asset.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __new__(
        cls,
        asset_key: CoercibleToAssetKey,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        partition: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        if isinstance(asset_key, AssetKey):
            check.inst_param(asset_key, "asset_key", AssetKey)
        elif isinstance(asset_key, str):
            asset_key = AssetKey(parse_asset_key_string(asset_key))
        else:
            check.sequence_param(asset_key, "asset_key", of_type=str)
            asset_key = AssetKey(asset_key)

        tags = check.opt_mapping_param(tags, "tags", key_type=str, value_type=str)
        if any([not tag.startswith(SYSTEM_TAG_PREFIX) for tag in tags or {}]):
            check.failed(
                "Users should not pass values into the tags argument for AssetMaterializations. "
                "The tags argument is reserved for system-populated tags."
            )

        metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

        return super(AssetObservation, cls).__new__(
            cls,
            asset_key=asset_key,
            description=check.opt_str_param(description, "description"),
            metadata=metadata,
            tags=tags,
            partition=check.opt_str_param(partition, "partition"),
        )

    @property
    def label(self) -> str:
        return " ".join(self.asset_key.path)


UNDEFINED_ASSET_KEY_PATH = ["__undefined__"]


class AssetMaterializationSerializer(NamedTupleSerializer):
    # There are old `Materialization` objects in storage. We set the default value for asset key to
    # be `AssetKey(["__undefined__"])` to ensure that we can load these objects, without needing to
    # allow for the construction of new `AssetMaterialization` objects with no defined AssetKey.
    def before_unpack(self, context, unpacked_dict: Any) -> Any:
        # cover both the case where "asset_key" is not present at all and where it is None
        if unpacked_dict.get("asset_key") is None:
            unpacked_dict["asset_key"] = AssetKey(UNDEFINED_ASSET_KEY_PATH)
        return unpacked_dict


@whitelist_for_serdes(
    old_storage_names={"Materialization"},
    serializer=AssetMaterializationSerializer,
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class AssetMaterialization(
    NamedTuple(
        "_AssetMaterialization",
        [
            ("asset_key", PublicAttr[AssetKey]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
            ("partition", PublicAttr[Optional[str]]),
            ("tags", Optional[Mapping[str, str]]),
        ],
    )
):
    """Event indicating that an op has materialized an asset.

    Op compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that they have produced a materialized value as a
    side effect of computation. Unlike outputs, asset materializations can not be passed to other
    ops, and their persistence is controlled by op logic, rather than by the Dagster
    framework.

    Op authors should use these events to organize metadata about the side effects of their
    computations, enabling tooling like the Assets dashboard in the Dagster UI.

    Args:
        asset_key (Union[str, List[str], AssetKey]): A key to identify the materialized asset across
            job runs
        description (Optional[str]): A longer human-readable description of the materialized value.
        partition (Optional[str]): The name of the partition
            that was materialized.
        tags (Optional[Mapping[str, str]]): A mapping containing system-populated tags for the
            materialization. Users should not pass values into this argument.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the asset.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __new__(
        cls,
        asset_key: CoercibleToAssetKey,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        partition: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionKey

        if isinstance(asset_key, AssetKey):
            check.inst_param(asset_key, "asset_key", AssetKey)
        elif isinstance(asset_key, str):
            asset_key = AssetKey(parse_asset_key_string(asset_key))
        else:
            check.sequence_param(asset_key, "asset_key", of_type=str)
            asset_key = AssetKey(asset_key)

        check.opt_mapping_param(tags, "tags", key_type=str, value_type=str)
        invalid_tags = [tag for tag in tags or {} if not tag.startswith(SYSTEM_TAG_PREFIX)]
        if len(invalid_tags) > 0:
            check.failed(
                f"Invalid tags: {tags} Users should not pass values into the tags argument for"
                " AssetMaterializations. The tags argument is reserved for system-populated tags."
            )

        metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

        partition = check.opt_str_param(partition, "partition")

        if not isinstance(partition, MultiPartitionKey):
            # When event log records are unpacked from storage, cast the partition key as a
            # MultiPartitionKey if multi-dimensional partition tags exist
            multi_dimensional_partitions = {
                dimension[len(MULTIDIMENSIONAL_PARTITION_PREFIX) :]: partition_key
                for dimension, partition_key in (tags or {}).items()
                if dimension.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX)
            }
            if multi_dimensional_partitions:
                partition = MultiPartitionKey(multi_dimensional_partitions)

        return super(AssetMaterialization, cls).__new__(
            cls,
            asset_key=asset_key,
            description=check.opt_str_param(description, "description"),
            metadata=metadata,
            tags=tags,
            partition=partition,
        )

    @property
    def label(self) -> str:
        return " ".join(self.asset_key.path)

    @public
    @staticmethod
    def file(
        path: str,
        description: Optional[str] = None,
        asset_key: Optional[Union[str, Sequence[str], AssetKey]] = None,
    ) -> "AssetMaterialization":
        """Static constructor for standard materializations corresponding to files on disk.

        Args:
            path (str): The path to the file.
            description (Optional[str]): A human-readable description of the materialization.
        """
        if not asset_key:
            asset_key = path

        return AssetMaterialization(
            asset_key=cast(Union[str, AssetKey, List[str]], asset_key),
            description=description,
            metadata={"path": MetadataValue.path(path)},
        )


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class ExpectationResult(
    NamedTuple(
        "_ExpectationResult",
        [
            ("success", PublicAttr[bool]),
            ("label", PublicAttr[Optional[str]]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
        ],
    )
):
    """Event corresponding to a data quality test.

    Op compute functions may yield events of this type whenever they wish to indicate to the
    Dagster framework (and the end user) that a data quality test has produced a (positive or
    negative) result.

    Args:
        success (bool): Whether the expectation passed or not.
        label (Optional[str]): Short display name for expectation. Defaults to "result".
        description (Optional[str]): A longer human-readable description of the expectation.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __new__(
        cls,
        success: bool,
        label: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    ):
        metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            label=check.opt_str_param(label, "label", "result"),
            description=check.opt_str_param(description, "description"),
            metadata=metadata,
        )


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
@whitelist_for_serdes
class TypeCheck(
    NamedTuple(
        "_TypeCheck",
        [
            ("success", PublicAttr[bool]),
            ("description", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
        ],
    )
):
    """Event corresponding to a successful typecheck.

    Events of this type should be returned by user-defined type checks when they need to encapsulate
    additional metadata about a type check's success or failure. (i.e., when using
    :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type>`, or the underlying
    :py:func:`PythonObjectDagsterType` API.)

    Op compute functions should generally avoid yielding events of this type to avoid confusion.

    Args:
        success (bool): ``True`` if the type check succeeded, ``False`` otherwise.
        description (Optional[str]): A human-readable description of the type check.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __new__(
        cls,
        success: bool,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    ):
        metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

        return super(TypeCheck, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            description=check.opt_str_param(description, "description"),
            metadata=metadata,
        )


class Failure(Exception):
    """Event indicating op failure.

    Raise events of this type from within op compute functions or custom type checks in order to
    indicate an unrecoverable failure in user code to the Dagster machinery and return
    structured metadata about the failure.

    Args:
        description (Optional[str]): A human-readable description of the failure.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the failure.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
        allow_retries (Optional[bool]):
            Whether this Failure should respect the retry policy or bypass it and immediately fail.
            Defaults to True, respecting the retry policy and allowing retries.
    """

    def __init__(
        self,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        allow_retries: Optional[bool] = None,
    ):
        super(Failure, self).__init__(description)
        self.description = check.opt_str_param(description, "description")
        self.metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )
        self.allow_retries = check.opt_bool_param(allow_retries, "allow_retries", True)


class RetryRequested(Exception):
    """An exception to raise from an op to indicate that it should be retried.

    Args:
        max_retries (Optional[int]):
            The max number of retries this step should attempt before failing
        seconds_to_wait (Optional[Union[float,int]]):
            Seconds to wait before restarting the step after putting the step in
            to the up_for_retry state

    Example:
        .. code-block:: python

            @op
            def flakes():
                try:
                    flakey_operation()
                except Exception as e:
                    raise RetryRequested(max_retries=3) from e
    """

    def __init__(
        self, max_retries: Optional[int] = 1, seconds_to_wait: Optional[Union[float, int]] = None
    ):
        super(RetryRequested, self).__init__()
        self.max_retries = check.int_param(max_retries, "max_retries")
        self.seconds_to_wait = check.opt_numeric_param(seconds_to_wait, "seconds_to_wait")


class ObjectStoreOperationType(Enum):
    SET_OBJECT = "SET_OBJECT"
    GET_OBJECT = "GET_OBJECT"
    RM_OBJECT = "RM_OBJECT"
    CP_OBJECT = "CP_OBJECT"


class ObjectStoreOperation(
    NamedTuple(
        "_ObjectStoreOperation",
        [
            ("op", ObjectStoreOperationType),
            ("key", str),
            ("dest_key", Optional[str]),
            ("obj", Any),
            ("serialization_strategy_name", Optional[str]),
            ("object_store_name", Optional[str]),
            ("value_name", Optional[str]),
            ("version", Optional[str]),
            ("mapping_key", Optional[str]),
        ],
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
        op: ObjectStoreOperationType,
        key: str,
        dest_key: Optional[str] = None,
        obj: Any = None,
        serialization_strategy_name: Optional[str] = None,
        object_store_name: Optional[str] = None,
        value_name: Optional[str] = None,
        version: Optional[str] = None,
        mapping_key: Optional[str] = None,
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


class HookExecutionResult(
    NamedTuple("_HookExecutionResult", [("hook_name", str), ("is_skipped", bool)])
):
    """This event is used internally to indicate the execution result of a hook, e.g. whether the
    user-defined hook function is skipped.

    Args:
        hook_name (str): The name of the hook.
        is_skipped (bool): ``False`` if the hook_fn is executed, ``True`` otheriwse.
    """

    def __new__(cls, hook_name: str, is_skipped: Optional[bool] = None):
        return super(HookExecutionResult, cls).__new__(
            cls,
            hook_name=check.str_param(hook_name, "hook_name"),
            is_skipped=cast(bool, check.opt_bool_param(is_skipped, "is_skipped", default=False)),
        )


UserEvent = Union[AssetMaterialization, AssetObservation, ExpectationResult]
