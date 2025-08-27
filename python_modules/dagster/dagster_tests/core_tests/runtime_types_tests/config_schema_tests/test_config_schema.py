import dagster as dg
import pytest


def test_dagster_type_loader_one():
    @dg.dagster_type_loader(dg.String)
    def _foo(_, hello):
        return hello


def test_dagster_type_loader_missing_context():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.dagster_type_loader(dg.String)  # pyright: ignore[reportArgumentType]
        def _foo(hello):
            return hello


def test_dagster_type_loader_missing_variable():
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.dagster_type_loader(dg.String)  # pyright: ignore[reportArgumentType]
        def _foo(_):
            return 1
