from typing import Sequence

from dagster._core.libraries import DagsterLibraryRegistry
from dagster._core.storage.db_io_manager import DbTypeHandler

from .config import (
    AzureConfig as AzureConfig,
    LocalConfig as LocalConfig,
    S3Config as S3Config,
    StorageLocation as StorageLocation,
    StorageOptions as StorageOptions,
)
from .handler import DeltalakeArrowTypeHandler as DeltalakeArrowTypeHandler
from .io_manager import (
    DELTA_DATE_FORMAT as DELTA_DATE_FORMAT,
    DELTA_DATETIME_FORMAT as DELTA_DATETIME_FORMAT,
    DeltaTableIOManager as DeltaTableIOManager,
)
from .resource import DeltaTableResource as DeltaTableResource
from .version import __version__


class DeltaTablePyarrowIOManager(DeltaTableIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltalakeArrowTypeHandler()]


DagsterLibraryRegistry.register("dagster-deltalake", __version__)
