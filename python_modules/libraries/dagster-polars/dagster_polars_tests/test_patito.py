from typing import Optional

import dagster as dg
import patito as pt  # noqa: TID253
import polars as pl
import pytest
from dagster_polars import BasePolarsUPathIOManager
from dagster_polars.patito import get_patito_metadata, patito_model_to_dagster_type


class TestingRecord(pt.Model):
    foo: str = pt.Field(unique=True, description="A `foo` column")
    bar: Optional[int]


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


def test_get_patito_metadata():
    metadata = get_patito_metadata(TestingRecord)
    assert metadata["dagster/column_schema"] == dg.TableSchemaMetadataValue(
        schema=dg.TableSchema(
            columns=[
                dg.TableColumn(
                    name="foo",
                    type="String",
                    description="A `foo` column",
                    constraints=dg.TableColumnConstraints(
                        nullable=False, unique=True, other=[]
                    ),
                    tags={},
                ),
                dg.TableColumn(
                    name="bar",
                    type="Int64",
                    description=None,
                    constraints=dg.TableColumnConstraints(
                        nullable=True, unique=False, other=[]
                    ),
                    tags={},
                ),
            ],
            constraints=dg.TableConstraints(other=[]),
        )
    )


def test_patito_eager_happy_path(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
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


def test_patito_eager_bad_output(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def bad() -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(bad_df)

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


def test_patito_eager_bad_input(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(good_df)

    @dg.asset(io_manager_def=manager)
    def bad_downstream(upstream: TestingRecord.DataFrame) -> TestingRecord.DataFrame:
        return TestingRecord.DataFrame(bad_df)

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [upstream, bad_downstream], instance=instance, raise_on_error=False
        )
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_lazy_happy_path(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
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
def test_patito_lazy_bad_output(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def bad() -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(bad_df).lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_lazy_bad_input(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df

    @dg.asset(io_manager_def=manager)
    def upstream() -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(good_df).lazy()

    @dg.asset(io_manager_def=manager)
    def bad_downstream(
        good_upstream: TestingRecord.LazyFrame,
    ) -> TestingRecord.LazyFrame:
        return TestingRecord.DataFrame(bad_df).lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [upstream, bad_downstream], instance=instance, raise_on_error=False
        )
        assert not res.success


def test_patito_type_check_happy_flow(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def upstream() -> pl.DataFrame:
        return good_df

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def downstream(upstream: pl.DataFrame) -> pl.DataFrame:
        return upstream

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, downstream], instance=instance)
        assert res.success


def test_patito_type_check_bad_input(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def bad() -> pl.DataFrame:
        return bad_df

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


def test_patito_type_check_bad_output(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def upstream() -> pl.DataFrame:
        return good_df

    @dg.asset(
        name="bad_downstream",
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def bad_downstream() -> pl.DataFrame:
        return bad_df

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [upstream, bad_downstream], instance=instance, raise_on_error=False
        )
        assert not res.success


def test_dagster_type_with_default_io_manager():
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        dagster_type=dagster_type,
    )
    def upstream() -> pl.DataFrame:
        return good_df

    @dg.asset(
        name="bad_downstream",
        dagster_type=dagster_type,
    )
    def bad_downstream() -> pl.DataFrame:
        return bad_df

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [
                upstream,
            ],
            instance=instance,
        )
        assert res.success

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [upstream, bad_downstream], instance=instance, raise_on_error=False
        )
        assert not res.success


class MaybeReturnConfig(dg.Config):
    return_value: bool


def test_io_manager_with_optional_type(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
) -> None:
    manager, _ = io_manager_and_df

    @dg.asset(
        io_manager_def=manager,
    )
    def good(config: MaybeReturnConfig) -> Optional[TestingRecord.DataFrame]:
        if config.return_value:
            return TestingRecord.DataFrame(good_df)
        else:
            return None

    @dg.asset(
        io_manager_def=manager,
    )
    def bad(config: MaybeReturnConfig) -> Optional[TestingRecord.DataFrame]:
        if config.return_value:
            return TestingRecord.DataFrame(bad_df)
        else:
            return None

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [good],
            instance=instance,
            run_config=dg.RunConfig({"good": MaybeReturnConfig(return_value=True)}),
            raise_on_error=False,
        )
        assert res.success

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [good],
            instance=instance,
            run_config=dg.RunConfig({"good": MaybeReturnConfig(return_value=False)}),
            raise_on_error=False,
        )
        assert res.success

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [bad],
            instance=instance,
            run_config=dg.RunConfig({"bad": MaybeReturnConfig(return_value=True)}),
            raise_on_error=False,
        )
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_type_check_lazy_happy_path(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def upstream() -> pl.LazyFrame:
        return good_df.lazy()

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def downstream(upstream: pl.LazyFrame) -> pl.LazyFrame:
        return upstream

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([upstream, downstream], instance=instance)
        assert res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_type_check_lazy_bad_input(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def bad() -> pl.LazyFrame:
        return bad_df.lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize([bad], instance=instance, raise_on_error=False)
        assert not res.success


@pytest.mark.skip(reason="Lazy frame validation is not supported yet")
def test_patito_type_check_lazy_bad_output(
    io_manager_and_df: tuple[BasePolarsUPathIOManager, pl.DataFrame],
):
    manager, _ = io_manager_and_df
    dagster_type = patito_model_to_dagster_type(TestingRecord)

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def upstream() -> pl.LazyFrame:
        return good_df.lazy()

    @dg.asset(
        io_manager_def=manager,
        dagster_type=dagster_type,
    )
    def bad_downstream() -> pl.LazyFrame:
        return bad_df.lazy()

    with dg.DagsterInstance.ephemeral() as instance:
        res = dg.materialize(
            [upstream, bad_downstream], instance=instance, raise_on_error=False
        )
        assert not res.success
