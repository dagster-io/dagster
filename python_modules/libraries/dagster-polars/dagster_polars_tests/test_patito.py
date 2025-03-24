import dagster as dg
import patito as pt
import polars as pl
import pytest
from dagster_polars import BasePolarsUPathIOManager


class TestingRecord(pt.Model):
    foo: str = pt.Field(unique=True)
    bar: int


good_df = pl.DataFrame(
    {
        "foo": ["a", "b", "c"],
        "bar": [1, 2, 3],
    }
)

bad_df = pl.DataFrame(
    {
        "foo": ["a", "a", "c"],
        "bar": [1, 2, 3],
    }
)


def test_patito_eager_happy_path(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(good_df)

    @dg.asset(io_manager_def=manager)
    def downstream(upstream: TestingRecord.DataFrame) -> TestingRecord.DataFrame:
        return upstream

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, downstream], instance=instance)
        assert res.success


def test_patito_eager_bad_output(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def bad() -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(bad_df)

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


def test_patito_eager_bad_input(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(good_df)

    @dg.asset(io_manager_def=manager)
    def bad_downstream(upstream: TestingRecord.DataFrame) -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(bad_df)

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, bad_downstream], instance=instance, raise_on_error=False)
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_lazy_happy_path(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(good_df).lazy()

    @dg.asset(io_manager_def=manager)
    def downstream(upstream: TestingRecord.LazyFrame) -> TestingRecord.LazyFrame:
        return upstream

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, downstream], instance=instance)
        assert res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_lazy_bad_output(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def bad() -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(bad_df).lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_lazy_bad_input(io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame]):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(good_df).lazy()

    @dg.asset(io_manager_def=manager)
    def bad_downstream(good_upstream: TestingRecord.LazyFrame) -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(bad_df).lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, bad_downstream], instance=instance, raise_on_error=False)
        assert not res.success
