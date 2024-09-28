import logging
import warnings
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Tuple, Type

import dagster
import polars as pl
import pytest
import pytest_cases
from _pytest.tmpdir import TempPathFactory
from dagster import DagsterInstance
from dagster_polars import BasePolarsUPathIOManager, PolarsDeltaIOManager, PolarsParquetIOManager

logging.getLogger("alembic.runtime.migration").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


@pytest.fixture
def dagster_instance(tmp_path_factory: TempPathFactory) -> DagsterInstance:
    return DagsterInstance.ephemeral(tempdir=str(tmp_path_factory.mktemp("dagster_home")))


@pytest.fixture
def polars_parquet_io_manager(dagster_instance: DagsterInstance) -> PolarsParquetIOManager:
    return PolarsParquetIOManager(base_dir=dagster_instance.storage_directory())


@pytest.fixture
def polars_delta_io_manager(dagster_instance: DagsterInstance) -> PolarsDeltaIOManager:
    return PolarsDeltaIOManager(base_dir=dagster_instance.storage_directory())


@pytest.fixture(scope="session")
def session_scoped_dagster_instance(tmp_path_factory: TempPathFactory) -> DagsterInstance:
    return DagsterInstance.ephemeral(tempdir=str(tmp_path_factory.mktemp("dagster_home_session")))


@pytest.fixture(scope="session")
def session_polars_parquet_io_manager(
    session_scoped_dagster_instance: DagsterInstance,
) -> PolarsParquetIOManager:
    return PolarsParquetIOManager(
        base_dir=session_scoped_dagster_instance.storage_directory()
    )  # to use with hypothesis


@pytest.fixture(scope="session")
def session_polars_delta_io_manager(
    session_scoped_dagster_instance: DagsterInstance,
) -> PolarsDeltaIOManager:
    return PolarsDeltaIOManager(
        base_dir=session_scoped_dagster_instance.storage_directory()
    )  # to use with hypothesis


main_data = {
    "1": [0, 1, None],
    "2": [0.0, 1.0, None],
    "3": ["a", "b", None],
    "4": [[0, 1], [2, 3], None],
    "6": [{"a": 0}, {"a": 1}, None],
    "7": [datetime(2022, 1, 1), datetime(2022, 1, 2), None],
    "8": [date(2022, 1, 1), date(2022, 1, 2), None],
    "9": [Decimal("1.0"), Decimal("2.0"), None],
}

schema = {
    "1": pl.Int64,
    "2": pl.Float64,
    "3": pl.Utf8,
    "4": pl.List(pl.Int64),
    "6": pl.Struct({"a": pl.Int64}),
    "7": pl.Datetime,
    "8": pl.Date,
    "9": pl.Decimal(precision=38),  # default precision isn't propagated after save-load
}

_df_for_delta = pl.DataFrame(main_data, schema=schema)

_lazy_df_for_delta = pl.LazyFrame(main_data, schema=schema)

parquet_data = main_data
parquet_data["9"] = [timedelta(hours=1), timedelta(hours=2), None]

_df_for_parquet = pl.DataFrame(parquet_data)
_lazy_df_for_parquet = pl.LazyFrame(parquet_data)


@pytest_cases.fixture(scope="session")  # type: ignore  # (bad stubs)
def df_for_parquet() -> pl.DataFrame:
    return _df_for_parquet


@pytest_cases.fixture(scope="session")  # type: ignore  # (bad stubs)
def df_for_delta() -> pl.DataFrame:
    return _df_for_delta


@pytest_cases.fixture(scope="session")  # type: ignore  # (bad stubs)
def lazy_df_for_parquet() -> pl.LazyFrame:
    return _lazy_df_for_parquet


@pytest_cases.fixture(scope="session")  # type: ignore  # (bad stubs)
def lazy_df_for_delta() -> pl.LazyFrame:
    return _lazy_df_for_delta


@pytest_cases.fixture  # type: ignore  # (bad stubs)
@pytest_cases.parametrize(
    "io_manager,frame",
    [(PolarsParquetIOManager, _df_for_parquet), (PolarsDeltaIOManager, _df_for_delta)],
)
def io_manager_and_df(  # to use without hypothesis
    io_manager: Type[BasePolarsUPathIOManager],
    frame: pl.DataFrame,
    dagster_instance: DagsterInstance,
) -> Tuple[BasePolarsUPathIOManager, pl.DataFrame]:
    return io_manager(base_dir=dagster_instance.storage_directory()), frame


@pytest_cases.fixture  # type: ignore  # (bad stubs)
@pytest_cases.parametrize(
    "io_manager,frame",
    [(PolarsParquetIOManager, _lazy_df_for_parquet), (PolarsDeltaIOManager, _lazy_df_for_delta)],
)
def io_manager_and_lazy_df(  # to use without hypothesis
    io_manager: Type[BasePolarsUPathIOManager],
    frame: pl.LazyFrame,
    dagster_instance: DagsterInstance,
) -> Tuple[BasePolarsUPathIOManager, pl.LazyFrame]:
    return io_manager(base_dir=dagster_instance.storage_directory()), frame
