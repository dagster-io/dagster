import sys
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
    cast,
    get_args,
    get_origin,
    overload,
)

import polars as pl
from dagster import (
    ConfigurableIOManager,
    EnvVar,
    InitResourceContext,
    InputContext,
    MetadataValue,
    OutputContext,
    UPathIOManager,
    _check as check,
)
from dagster._core.storage.upath_io_manager import is_dict_type
from pydantic import PrivateAttr
from pydantic.fields import Field

from dagster_polars.io_managers.utils import get_polars_metadata
from dagster_polars.types import (
    DataFramePartitions,
    DataFramePartitionsWithMetadata,
    LazyFramePartitions,
    LazyFramePartitionsWithMetadata,
    LazyFrameWithMetadata,
    StorageMetadata,
)

if TYPE_CHECKING:
    from upath import UPath

POLARS_EAGER_FRAME_ANNOTATIONS = [
    pl.DataFrame,
    Optional[pl.DataFrame],
    # common default types
    Any,
    type(None),
    None,
    # multiple partitions
    Dict[str, pl.DataFrame],
    Mapping[str, pl.DataFrame],
    DataFramePartitions,
    # DataFrame + metadata
    Tuple[pl.DataFrame, StorageMetadata],
    Optional[Tuple[pl.DataFrame, StorageMetadata]],
    # multiple partitions + metadata
    DataFramePartitionsWithMetadata,
]

POLARS_LAZY_FRAME_ANNOTATIONS = [
    pl.LazyFrame,
    Optional[pl.LazyFrame],
    # multiple partitions
    Dict[str, pl.LazyFrame],
    Mapping[str, pl.LazyFrame],
    LazyFramePartitions,
    # LazyFrame + metadata
    Tuple[pl.LazyFrame, StorageMetadata],
    Optional[Tuple[pl.LazyFrame, StorageMetadata]],
    # multiple partitions + metadata
    LazyFramePartitionsWithMetadata,
]


if sys.version_info >= (3, 9):
    POLARS_EAGER_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])
    POLARS_EAGER_FRAME_ANNOTATIONS.append(dict[str, Optional[pl.DataFrame]])

    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, pl.LazyFrame])
    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, Optional[pl.LazyFrame]])


def annotation_is_typing_optional(annotation) -> bool:
    return get_origin(annotation) == Union and type(None) in get_args(annotation)


def annotation_is_tuple(annotation) -> bool:
    return get_origin(annotation) in (Tuple, tuple)


def annotation_for_multiple_partitions(annotation) -> bool:
    if not annotation_is_typing_optional(annotation):
        return annotation_is_tuple(annotation) and get_origin(annotation) in (dict, Dict, Mapping)
    else:
        inner_annotation = get_args(annotation)[0]
        return annotation_is_tuple(inner_annotation) and get_origin(inner_annotation) in (
            dict,
            Dict,
            Mapping,
        )


def annotation_is_tuple_with_metadata(annotation) -> bool:
    if annotation_is_typing_optional(annotation):
        annotation = get_args(annotation)[0]

    return annotation_is_tuple(annotation) and get_origin(get_args(annotation)[1]) in [
        dict,
        Dict,
        Mapping,
    ]


def annotation_for_storage_metadata(annotation) -> bool:
    # first unwrap the Optional type
    if annotation_is_typing_optional(annotation):
        annotation = get_args(annotation)[0]

    if not annotation_for_multiple_partitions(annotation):
        return annotation_is_tuple_with_metadata(annotation)
    else:
        # unwrap the partitions
        annotation = get_args(annotation)[1]
        return annotation_is_tuple_with_metadata(annotation)


def _process_env_vars(config: Mapping[str, Any]) -> Dict[str, Any]:
    out = {}
    for key, value in config.items():
        if isinstance(value, dict) and len(value) == 1 and next(iter(value.keys())) == "env":
            out[key] = EnvVar(next(iter(value.values()))).get_value()
        else:
            out[key] = value
    return out


class BasePolarsUPathIOManager(ConfigurableIOManager, UPathIOManager):
    """Base class for `dagster-polars` IOManagers.

    Doesn't define a specific storage format.

    To implement a specific storage format (parquet, csv, etc), inherit from this class and implement the `write_df_to_path`, `sink_df_to_path` and `scan_df_from_path` methods.

    Features:
     - All the features of :py:class:`~dagster.UPathIOManager` - works with local and remote filesystems (like S3), supports loading multiple partitions with respect to :py:class:`~dagster.PartitionMapping`, and more
     - loads the correct type - `polars.DataFrame`, `polars.LazyFrame`, or other types defined in :py:mod:`dagster_polars.types` - based on the input type annotation (or `dagster.DagsterType`'s `typing_type`)
     - can sink lazy `pl.LazyFrame` DataFrames
     - handles `Nones` with `Optional` types by skipping loading missing inputs or saving `None` outputs
     - logs various metadata about the DataFrame - size, schema, sample, stats, ...
     - the `"columns"` input metadata value can be used to select a subset of columns to load
    """

    base_dir: Optional[str] = Field(default=None, description="Base directory for storing files.")
    cloud_storage_options: Optional[Mapping[str, Any]] = Field(
        default=None,
        description="Storage authentication for cloud object store",
        alias="storage_options",
    )
    _base_path = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        from upath import UPath

        sp = (
            _process_env_vars(self.cloud_storage_options)
            if self.cloud_storage_options is not None
            else {}
        )
        self._base_path = (
            UPath(self.base_dir, **sp)
            if self.base_dir is not None
            else UPath(check.not_none(context.instance).storage_directory())
        )

    @abstractmethod
    def write_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,
    ):
        ...

    @abstractmethod
    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,
    ):
        ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[None, False]
    ) -> pl.LazyFrame:
        ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[True]
    ) -> LazyFrameWithMetadata:
        ...

    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Optional[bool] = False
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]:
        ...

    # tmp fix until https://github.com/dagster-io/dagster/pull/19294 is merged
    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        # If no asset key, we are dealing with an op output which is always non-partitioned
        if not context.has_asset_key or not context.has_asset_partitions:
            path = self._get_path(context)
            return self._load_single_input(path, context)
        else:
            asset_partition_keys = context.asset_partition_keys
            if len(asset_partition_keys) == 0:
                return None
            elif len(asset_partition_keys) == 1:
                paths = self._get_paths_for_partitions(context)
                check.invariant(len(paths) == 1, f"Expected 1 path, but got {len(paths)}")
                path = next(iter(paths.values()))
                backcompat_paths = self._get_multipartition_backcompat_paths(context)
                backcompat_path = (
                    None if not backcompat_paths else next(iter(backcompat_paths.values()))
                )

                return self._load_partition_from_path(
                    context=context,
                    partition_key=asset_partition_keys[0],
                    path=path,
                    backcompat_path=backcompat_path,
                )
            else:  # we are dealing with multiple partitions of an asset
                type_annotation = context.dagster_type.typing_type
                if type_annotation != Any and not is_dict_type(type_annotation):
                    check.failed(
                        "Loading an input that corresponds to multiple partitions, but the"
                        " type annotation on the op input is not a dict, Dict, Mapping, or"
                        f" Any: is '{type_annotation}'."
                    )

                return self._load_multiple_inputs(context)

    def dump_to_path(
        self,
        context: OutputContext,
        obj: Union[
            pl.DataFrame,
            Optional[pl.DataFrame],
            Tuple[pl.DataFrame, Dict[str, Any]],
            pl.LazyFrame,
            Optional[pl.LazyFrame],
            Tuple[pl.LazyFrame, Dict[str, Any]],
        ],
        path: "UPath",
        partition_key: Optional[str] = None,
    ):
        typing_type = context.dagster_type.typing_type

        if annotation_is_typing_optional(typing_type) and (
            obj is None or annotation_for_storage_metadata(typing_type) and obj[0] is None
        ):
            context.log.warning(self.get_optional_output_none_log_message(context, path))
            return
        else:
            assert obj is not None, "output should not be None if it's type is not Optional"
            if not annotation_for_storage_metadata(typing_type):
                if typing_type in POLARS_EAGER_FRAME_ANNOTATIONS:
                    obj = cast(pl.DataFrame, obj)
                    df = obj
                    self.write_df_to_path(context=context, df=df, path=path)
                elif typing_type in POLARS_LAZY_FRAME_ANNOTATIONS:
                    obj = cast(pl.LazyFrame, obj)
                    df = obj
                    self.sink_df_to_path(context=context, df=df, path=path)
                else:
                    raise NotImplementedError(
                        f"dump_df_to_path for {typing_type} is not implemented"
                    )
            else:
                if not annotation_is_typing_optional(typing_type):
                    frame_type = get_args(typing_type)[0]
                else:
                    frame_type = get_args(get_args(typing_type)[0])[0]

                if frame_type in POLARS_EAGER_FRAME_ANNOTATIONS:
                    obj = cast(Tuple[pl.DataFrame, Dict[str, Any]], obj)
                    df, metadata = obj
                    self.write_df_to_path(context=context, df=df, path=path, metadata=metadata)
                elif frame_type in POLARS_LAZY_FRAME_ANNOTATIONS:
                    obj = cast(Tuple[pl.LazyFrame, Dict[str, Any]], obj)
                    df, metadata = obj
                    self.sink_df_to_path(context=context, df=df, path=path, metadata=metadata)
                else:
                    raise NotImplementedError(
                        f"dump_df_to_path for {typing_type} is not implemented"
                    )

    def load_from_path(
        self, context: InputContext, path: "UPath", partition_key: Optional[str] = None
    ) -> Union[
        pl.DataFrame,
        pl.LazyFrame,
        Tuple[pl.DataFrame, Dict[str, Any]],
        Tuple[pl.LazyFrame, Dict[str, Any]],
        None,
    ]:
        if annotation_is_typing_optional(context.dagster_type.typing_type) and not path.exists():
            context.log.warning(self.get_missing_optional_input_log_message(context, path))
            return None

        assert context.metadata is not None

        metadata: Optional[StorageMetadata] = None

        return_storage_metadata = annotation_for_storage_metadata(context.dagster_type.typing_type)

        if not return_storage_metadata:
            ldf = self.scan_df_from_path(path=path, context=context)  # type: ignore
        else:
            ldf, metadata = self.scan_df_from_path(path=path, context=context, with_metadata=True)

        columns = context.metadata.get("columns")
        if columns is not None:
            context.log.debug(f"Loading {columns=}")
            ldf = ldf.select(columns)

        if (
            context.upstream_output is not None
            and context.upstream_output.asset_info is not None
            and context.upstream_output.asset_info.partitions_def is not None
            and context.upstream_output.metadata is not None
            and partition_key is not None
        ):
            partition_by = context.upstream_output.metadata.get("partition_by")

            # we can only support automatically filtering by 1 column
            # otherwise we would have been dealing with a multi-partition key
            # which is not straightforward to filter by
            if partition_by is not None and isinstance(partition_by, str):
                context.log.debug(f"Filtering by {partition_by}=={partition_key}")
                ldf = ldf.filter(pl.col(partition_by) == partition_key)

        if context.dagster_type.typing_type in POLARS_EAGER_FRAME_ANNOTATIONS:
            if not return_storage_metadata:
                return ldf.collect()
            else:
                assert metadata is not None
                return ldf.collect(), metadata

        elif context.dagster_type.typing_type in POLARS_LAZY_FRAME_ANNOTATIONS:
            if not return_storage_metadata:
                return ldf
            else:
                assert metadata is not None
                return ldf, metadata
        else:
            raise NotImplementedError(
                f"Can't load object for type annotation {context.dagster_type.typing_type}"
            )

    def get_metadata(
        self, context: OutputContext, obj: Union[pl.DataFrame, pl.LazyFrame, None]
    ) -> Dict[str, MetadataValue]:
        if obj is None:
            return {"missing": MetadataValue.bool(True)}
        else:
            if annotation_for_storage_metadata(context.dagster_type.typing_type):
                df = obj[0]
            else:
                df = obj
            return (
                get_polars_metadata(context, df)
                if df is not None
                else {"missing": MetadataValue.bool(True)}
            )

    def get_path_for_partition(
        self, context: Union[InputContext, OutputContext], path: "UPath", partition: str
    ) -> "UPath":
        """Method for accessing the path for a given partition.

        Override this method if you want to use a different partitioning scheme
        (for example, if the saving function handles partitioning instead).
        The extension will be added later.
        :param context:
        :param path: asset path before partitioning
        :param partition: formatted partition key
        :return:
        """
        return path / partition

    def get_missing_optional_input_log_message(self, context: InputContext, path: "UPath") -> str:
        return f"Optional input {context.name} at {path} doesn't exist in the filesystem and won't be loaded!"

    def get_optional_output_none_log_message(self, context: OutputContext, path: "UPath") -> str:
        return f"The object for the optional output {context.name} is None, so it won't be saved to {path}!"

    # this method is overridden because the default one does not pass partition_key to load_from_path
    def _load_partition_from_path(
        self,
        context: InputContext,
        partition_key: str,
        path: "UPath",
        backcompat_path: Optional["UPath"] = None,
    ) -> Any:
        """1. Try to load the partition from the normal path.
        2. If it was not found, try to load it from the backcompat path.
        3. If allow_missing_partitions metadata is True, skip the partition if it was not found in any of the paths.
        Otherwise, raise an error.

        Args:
            context (InputContext): IOManager Input context
            partition_key (str): the partition key corresponding to the partition being loaded
            path (UPath): The path to the partition.
            backcompat_path (Optional[UPath]): The path to the partition in the backcompat location.

        Returns:
            Any: The object loaded from the partition.
        """
        allow_missing_partitions = (
            context.metadata.get("allow_missing_partitions", False)
            if context.metadata is not None
            else False
        )

        try:
            context.log.debug(self.get_loading_input_partition_log_message(path, partition_key))
            obj = self.load_from_path(context=context, path=path, partition_key=partition_key)
            return obj
        except FileNotFoundError as e:
            if backcompat_path is not None:
                try:
                    obj = self.load_from_path(
                        context=context, path=path, partition_key=partition_key
                    )
                    context.log.debug(
                        f"File not found at {path}. Loaded instead from backcompat path:"
                        f" {backcompat_path}"
                    )
                    return obj
                except FileNotFoundError as e:
                    if allow_missing_partitions:
                        context.log.warning(self.get_missing_partition_log_message(partition_key))
                        return None
                    else:
                        raise e
            if allow_missing_partitions:
                context.log.warning(self.get_missing_partition_log_message(partition_key))
                return None
            else:
                raise e
