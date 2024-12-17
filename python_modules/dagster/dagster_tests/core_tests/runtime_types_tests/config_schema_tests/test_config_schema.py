import pytest
from dagster import String
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.config_schema import dagster_type_loader


def test_dagster_type_loader_one():
    @dagster_type_loader(String)
    def _foo(_, hello):
        return hello


def test_dagster_type_loader_missing_context():
    with pytest.raises(DagsterInvalidDefinitionError):

        @dagster_type_loader(String)  # pyright: ignore[reportArgumentType]
        def _foo(hello):
            return hello


def test_dagster_type_loader_missing_variable():
    with pytest.raises(DagsterInvalidDefinitionError):

        @dagster_type_loader(String)  # pyright: ignore[reportArgumentType]
        def _foo(_):
            return 1
