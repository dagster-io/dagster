from collections.abc import Sequence

from dagster._core.storage.db_io_manager import DbTypeHandler
from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_deltalake.config import (
    AzureConfig as AzureConfig,
    GcsConfig as GcsConfig,
    LocalConfig as LocalConfig,
    S3Config as S3Config,
)
from dagster_deltalake.handler import (
    DeltalakeBaseArrowTypeHandler as DeltalakeBaseArrowTypeHandler,
    DeltaLakePyArrowTypeHandler as DeltaLakePyArrowTypeHandler,
)
from dagster_deltalake.io_manager import (
    DELTA_DATE_FORMAT as DELTA_DATE_FORMAT,
    DELTA_DATETIME_FORMAT as DELTA_DATETIME_FORMAT,
    DeltaLakeIOManager as DeltaLakeIOManager,
    WriteMode as WriteMode,
    WriterEngine as WriterEngine,
)
from dagster_deltalake.resource import DeltaTableResource as DeltaTableResource
from dagster_deltalake.version import __version__


class DeltaLakePyarrowIOManager(DeltaLakeIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePyArrowTypeHandler()]


DagsterLibraryRegistry.register("dagster-deltalake", __version__)
