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
    overload, Callable, Generic, TypeVar, List,

)


if sys.version_info >= (3, 9):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

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
from pydantic import PrivateAttr
from pydantic.fields import Field

from dagster_polars.io_managers.utils import get_polars_metadata
from dagster_polars.types import (
    DataFramePartitions,
    LazyFramePartitions,
    LazyFrameWithMetadata,
)

try:
    import pandera

    PANDERA_INSTALLED = True
except ImportError:
    PANDERA_INSTALLED = False


if TYPE_CHECKING:
    from upath import UPath


T = TypeVar("T")


# dump_to_path signature
F_D: TypeAlias = Callable[[OutputContext, T, "UPath"], None]

# load_from_path signature
F_L: TypeAlias = Callable[[InputContext, "UPath"], T]


class BaseTypeRouter(Generic[T]):
    """
    Specifies how to apply a given dump/load operation to a given type annotation.
    """

    def __init__(self, context: Union[InputContext, OutputContext], type_to_resolve: Any):
        self.context = context
        self.type_to_resolve = type_to_resolve

    @abstractmethod
    def match(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    @property
    def is_root_type(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    @property
    def parent_type(self) -> Any:
        raise NotImplementedError

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        dump_fn(self.context, obj, path)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        return load_fn(self.context, path)


class TypeRouter(BaseTypeRouter, Generic[T]):
    """
    Specifies how to apply a given dump/load operation to a given type annotation.
    This base class trivially calls the dump/load functions if the type matches the most simple cases.
    """

    def match(self) -> bool:
        return self.type_to_resolve in [
            pl.DataFrame,
            pl.LazyFrame,
            Any,
            type(None),
            None,
        ]

    @property
    def is_root_type(self) -> bool:
        return True


class OptionalTypeRouter(TypeRouter):
    """
    Handles Optional type annotations with a noop if the object is None or missing in storage.
    """

    def match(self) -> bool:
        return get_origin(self.type_to_resolve) == Union and type(None) in get_args(self.type_to_resolve)

    @property
    def is_root_type(self) -> bool:
        return False

    def parent_type(self) -> Any:
        return get_args(self.type_to_resolve)[0]

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        if obj is None:
            self.context.log.warning(f"Skipping saving optional output at {path} as it is None")
            return
        else:
            router = resolve_type_router(self.context, self.parent_type)
            router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        if not path.exists():
            self.context.log.warning(f"Skipping loading optional input at {path} as it is missing")
            return None
        else:
            router = resolve_type_router(self.context, self.parent_type)
            return router.load(path, load_fn)


class DictTypeRouter(TypeRouter):
    """
    Handles loading partitions as dictionaries of DataFrames.
    """

    def match(self) -> bool:
        return get_origin(self.type_to_resolve) in (dict, Dict, Mapping)

    @property
    def is_root_type(self) -> bool:
        return False

    @property
    def parent_type(self) -> Any:
        return get_args(self.type_to_resolve)[1]


class PanderaTypeRouter(TypeRouter):
    """
    Handles loading Pandera DataFrames.
    """

    def match(self) -> bool:
        try:
            import pandera
            import pandera.typing.polars

            return (
                    get_origin(self.type_to_resolve) == pandera.typing.polars.LazyFrame
                    and issubclass(get_args(self.type_to_resolve)[0], pandera.DataFrameModel)
            )
        except ImportError:
            return False

    @property
    def is_root_type(self) -> bool:
        return True

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        if isinstance()
        router = resolve_type_router(self.context, self.parent_type)
        router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        if not path.exists():
            self.context.log.warning(f"Skipping loading optional input at {path} as it is missing")
            return None
        else:
            router = resolve_type_router(self.context, self.parent_type)
            return router.load(path, load_fn)


TYPE_ROUTERS = [
    TypeRouter,
    OptionalTypeRouter,
    DictTypeRouter,
]

if PANDERA_INSTALLED:
    TYPE_ROUTERS.append(PanderaTypeRo`uter)


def resolve_type_router(context: Union[InputContext, OutputContext], type_to_resolve: Any) -> TypeRouter:
    """
    Finds the correct TypeRouter for the given context.
    """

    # try each router class in order of increasing complexity
    for router_class in [
        TypeRouter,
        OptionalTypeRouter,
        ...
    ]:
        router = router_class(context, type_to_resolve)

        if not router.match():
            continue
        else:
            if router.is_root_type:
                return router
            else:
                # recursively resolve the parent type
                return resolve_type_router(context, router.parent_type)


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
    ): ...

    @abstractmethod
    def sink_df_to_path(
        self,
        context: OutputContext,
        df: pl.LazyFrame,
        path: "UPath",
    ): ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext,
    ) -> pl.LazyFrame: ...

    @overload
    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext,
    ) -> LazyFrameWithMetadata: ...

    @abstractmethod
    def scan_df_from_path(
        self, path: "UPath", context: InputContext,
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
        if annotation_is_typing_optional(context.dagster_type.typing_type) and not path.exists():
            context.log.warning(self.get_missing_optional_input_log_message(context, path))
            return None

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
