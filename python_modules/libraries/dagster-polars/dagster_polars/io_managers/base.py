from abc import abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Optional, Union

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

from dagster_polars.io_managers.type_routers import TypeRouter, resolve_type_router
from dagster_polars.io_managers.utils import get_polars_metadata

if TYPE_CHECKING:
    from upath import UPath


def _process_env_vars(config: Mapping[str, Any]) -> dict[str, Any]:
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

    def type_router_is_eager(self, type_router: TypeRouter) -> bool:
        if type_router.is_base_type:
            if type_router.typing_type in [Any, type(None), None] or issubclass(
                type_router.typing_type, pl.DataFrame
            ):
                return True
            elif issubclass(type_router.typing_type, pl.LazyFrame):
                return False
            else:
                raise NotImplementedError(
                    f"Can't determine if type annotation {type_router.typing_type} corresponds to an eager or lazy DataFrame"
                )
        else:
            return self.type_router_is_eager(type_router.parent_type_router)

    def dump_to_path(
        self,
        context: OutputContext,
        obj: Union[
            pl.DataFrame,
            Optional[pl.DataFrame],
            tuple[pl.DataFrame, dict[str, Any]],
            pl.LazyFrame,
            Optional[pl.LazyFrame],
            tuple[pl.LazyFrame, dict[str, Any]],
        ],
        path: "UPath",
    ):
        type_router = resolve_type_router(context, context.dagster_type.typing_type)

        if self.type_router_is_eager(type_router):
            dump_fn = self.write_df_to_path
        else:
            dump_fn = self.sink_df_to_path

        type_router.dump(obj, path, dump_fn)

    def load_from_path(
        self, context: InputContext, path: "UPath"
    ) -> Union[
        pl.DataFrame,
        pl.LazyFrame,
        tuple[pl.DataFrame, dict[str, Any]],
        tuple[pl.LazyFrame, dict[str, Any]],
        None,
    ]:
        type_router = resolve_type_router(context, context.dagster_type.typing_type)

        ldf = type_router.load(path, self.scan_df_from_path)

        # missing files detection in UPathIOManager doesn't work with `LazyFrame`
        # since the FileNotFoundError is raised only when calling `.collect()` outside of the UPathIOManager
        # as a workaround, we check if the file exists and if not, we raise the error here
        # this is needed for allow_missing_partitions input metadata setting to work correctly
        if (
            ldf is not None
            and not self.type_router_is_eager(type_router)
            and type_router
            and not path.exists()
        ):
            raise FileNotFoundError(f"File {path} does not exist")

        columns = context.definition_metadata.get("columns")
        if columns is not None:
            context.log.debug(f"Loading {columns=}")
            ldf = ldf.select(columns)

        if ldf is None:
            return None
        elif self.type_router_is_eager(type_router) and ldf is not None:
            return ldf.collect()
        else:
            return ldf

    def get_metadata(
        self, context: OutputContext, obj: Union[pl.DataFrame, pl.LazyFrame, None]
    ) -> dict[str, MetadataValue]:
        if obj is None:
            return {"missing": MetadataValue.bool(True)}
        else:
            return (
                get_polars_metadata(context, obj)
                if obj is not None
                else {"missing": MetadataValue.bool(True)}
            )
