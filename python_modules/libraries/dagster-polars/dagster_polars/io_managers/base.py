import sys
from abc import abstractmethod
from typing import (
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
    InitResourceContext,
    InputContext,
    MetadataValue,
    OutputContext,
    UPathIOManager,
    _check as check,
)
from pydantic.fields import Field, PrivateAttr
from upath import UPath

from dagster._annotations import experimental
from dagster_polars.io_managers.utils import get_polars_metadata
from dagster_polars.types import (
    DataFramePartitions,
    DataFramePartitionsWithMetadata,
    LazyFramePartitions,
    LazyFramePartitionsWithMetadata,
    LazyFrameWithMetadata,
    StorageMetadata,
)

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
    POLARS_EAGER_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])  # type: ignore
    POLARS_EAGER_FRAME_ANNOTATIONS.append(dict[str, Optional[pl.DataFrame]])  # type: ignore

    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, pl.LazyFrame])  # type: ignore
    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, Optional[pl.LazyFrame]])  # type: ignore


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


@experimental
class BasePolarsUPathIOManager(ConfigurableIOManager, UPathIOManager):
    """Base class for `dagster-polars` IOManagers.

    Doesn't define a specific storage format (parquet, csv, etc).

    To implement a specific storage format, inherit from this class and implement the `dump_df_to_path` and `scan_df_from_path` methods.

    Features:
     - All the features of :py:class:`~dagster.UPathIOManager` - works with local and remote filesystems (like S3), supports loading multiple partitions, and more
     - returns the correct type - `polars.DataFrame`, `polars.LazyFrame`, or other types defined in :py:mod:`dagster_polars.types` - based on the input type annotation (or `dagster.DagsterType`'s `typing_type`)
     - handles `Optional` types by skipping loading missing inputs or `None` outputs
     - logs various metadata about the DataFrame - size, schema, sample, stats, ...
     - the `"columns"` input metadata value can be used to select a subset of columns to load
    """

    base_dir: Optional[str] = Field(default=None, description="Base directory for storing files.")

    _base_path: UPath = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._base_path = (
            UPath(self.base_dir)
            if self.base_dir is not None
            else UPath(check.not_none(context.instance).storage_directory())
        )

    @abstractmethod
    def dump_df_to_path(
        self,
        context: OutputContext,
        df: pl.DataFrame,
        path: UPath,
        metadata: Optional[StorageMetadata] = None,
    ):
        ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: UPath, context: InputContext, with_metadata: Literal[None, False]
    ) -> pl.LazyFrame:
        ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: UPath, context: InputContext, with_metadata: Literal[True]
    ) -> LazyFrameWithMetadata:
        ...

    @abstractmethod
    def scan_df_from_path(
        self, path: UPath, context: InputContext, with_metadata: Optional[bool] = False
    ) -> Union[pl.LazyFrame, LazyFrameWithMetadata]:
        ...

    def dump_to_path(
        self,
        context: OutputContext,
        obj: Union[pl.DataFrame, Optional[pl.DataFrame], Tuple[pl.DataFrame, Dict[str, Any]]],
        path: UPath,
    ):
        if annotation_is_typing_optional(context.dagster_type.typing_type) and (
            obj is None
            or annotation_for_storage_metadata(context.dagster_type.typing_type)
            and obj[0] is None
        ):
            context.log.warning(self.get_optional_output_none_log_message(context, path))
            return
        else:
            assert obj is not None, "output should not be None if it's type is not Optional"
            if not annotation_for_storage_metadata(context.dagster_type.typing_type):
                obj = cast(pl.DataFrame, obj)
                df = obj
                self.dump_df_to_path(context=context, df=df, path=path)
            else:
                obj = cast(Tuple[pl.DataFrame, Dict[str, Any]], obj)
                df, metadata = obj
                self.dump_df_to_path(context=context, df=df, path=path, metadata=metadata)

    def load_from_path(
        self, path: UPath, context: InputContext
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

    def get_metadata(self, context: OutputContext, obj: pl.DataFrame) -> Dict[str, MetadataValue]:
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

    @staticmethod
    def get_storage_options(path: UPath) -> dict:
        storage_options = {}

        try:
            storage_options.update(path.storage_options.copy())
        except AttributeError:
            pass

        return storage_options

    def get_path_for_partition(
        self, context: Union[InputContext, OutputContext], path: UPath, partition: str
    ) -> UPath:
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

    def get_missing_optional_input_log_message(self, context: InputContext, path: UPath) -> str:
        return f"Optional input {context.name} at {path} doesn't exist in the filesystem and won't be loaded!"

    def get_optional_output_none_log_message(self, context: OutputContext, path: UPath) -> str:
        return f"The object for the optional output {context.name} is None, so it won't be saved to {path}!"
