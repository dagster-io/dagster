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
from dagster._utils.warnings import deprecation_warning
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


def emit_storage_metadata_deprecation_warning() -> None:
    deprecation_warning(
        subject="dagster-polars storage metadata",
        breaking_version="0.25.0",
        additional_warn_text="Please use a multi-output asset or op to save metadata.",
    )


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

    # method calling chain:
    # 1. Non-partitioned: UPathIOManager.load_input -> UPathIOManager._load_single_input -> UPathIOManager.load_from_path -> BasePolarsUPathIOManager.scan_df_from_path
    # 2. Partitioned: UPathIOManager.load_input -> UPathIOManager.load_partitions -> UPathIOManager.load_from_path -> BasePolarsUPathIOManager.scan_df_from_path

    # If a child IOManager supports loading multiple partitions at once, it should override .load_partitions to immidiately return a LazyFrame (by using scan_df_from_path)

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
    ): ...

    @abstractmethod
    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
        metadata: Optional[StorageMetadata] = None,
    ): ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[None, False]
    ) -> pl.LazyFrame: ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Literal[True]
    ) -> LazyFrameWithMetadata: ...

    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext, with_metadata: Optional[bool] = False
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]: ...

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
    ):
        if self.needs_output_metadata(context):
            emit_storage_metadata_deprecation_warning()

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

    def needs_output_metadata(self, context: Union[InputContext, OutputContext]) -> bool:
        return annotation_for_storage_metadata(context.dagster_type.typing_type)

    def load_from_path(
        self, context: InputContext, path: "UPath"
    ) -> Union[
        pl.DataFrame,
        pl.LazyFrame,
        Tuple[pl.DataFrame, Dict[str, Any]],
        Tuple[pl.LazyFrame, Dict[str, Any]],
        None,
    ]:
        if self.needs_output_metadata(context):
            emit_storage_metadata_deprecation_warning()

        if annotation_is_typing_optional(context.dagster_type.typing_type) and not path.exists():
            context.log.warning(self.get_missing_optional_input_log_message(context, path))
            return None

        # missing files detection in UPathIOManager doesn't work with `LazyFrame`
        # since the FileNotFoundError is raised only when calling `.collect()` outside of the UPathIOManager
        # as a workaround, we check if the file exists and if not, we raise the error here
        if context.dagster_type.typing_type in POLARS_LAZY_FRAME_ANNOTATIONS and not path.exists():
            raise FileNotFoundError(f"File {path} does not exist")

        assert context.definition_metadata is not None

        metadata: Optional[StorageMetadata] = None

        return_storage_metadata = self.needs_output_metadata(context)
        if not return_storage_metadata:
            ldf = self.scan_df_from_path(path=path, context=context)  # type: ignore
        else:
            ldf, metadata = self.scan_df_from_path(path=path, context=context, with_metadata=True)

        columns = context.definition_metadata.get("columns")
        if columns is not None:
            context.log.debug(f"Loading {columns=}")
            ldf = ldf.select(columns)

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

    def get_missing_optional_input_log_message(self, context: InputContext, path: "UPath") -> str:
        return f"Optional input {context.name} at {path} doesn't exist in the filesystem and won't be loaded!"

    def get_optional_output_none_log_message(self, context: OutputContext, path: "UPath") -> str:
        return f"The object for the optional output {context.name} is None, so it won't be saved to {path}!"
