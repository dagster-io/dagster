from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Tuple, Union

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

from dagster_polars.io_managers.type_routers import resolve_type_router
from dagster_polars.io_managers.utils import get_polars_metadata

if TYPE_CHECKING:
    from upath import UPath


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

    @abstractmethod
    def scan_df_from_path(
        self,
        path: "UPath",
        context: InputContext,
    ) -> pl.LazyFrame: ...

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
        type_router = resolve_type_router(context, context.dagster_type.typing_type)

        if type_router.is_eager:
            dump_fn = self.write_df_to_path
        elif type_router.is_lazy:
            dump_fn = self.sink_df_to_path
        else:
            raise NotImplementedError(
                f"Can't dump object for type annotation {context.dagster_type.typing_type}"
            )

        type_router.dump(obj, path, dump_fn)

    def load_from_path(
        self, context: InputContext, path: "UPath"
    ) -> Union[
        pl.DataFrame,
        pl.LazyFrame,
        Tuple[pl.DataFrame, Dict[str, Any]],
        Tuple[pl.LazyFrame, Dict[str, Any]],
        None,
    ]:
        type_router = resolve_type_router(context, context.dagster_type.typing_type)

        ldf = type_router.load(path, self.scan_df_from_path)

        columns = context.definition_metadata.get("columns")
        if columns is not None:
            context.log.debug(f"Loading {columns=}")
            ldf = ldf.select(columns)

        if ldf is None:
            return None
        elif type_router.is_eager and ldf is not None:
            return ldf.collect()
        elif type_router.is_lazy:
            return ldf
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
            return (
                get_polars_metadata(context, obj)
                if obj is not None
                else {"missing": MetadataValue.bool(True)}
            )
