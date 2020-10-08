from docs_snippets.overview.repositories_workspaces.lazy_repository_definition import (
    my_lazy_repository,
)
from docs_snippets.overview.repositories_workspaces.repository_definition import (
    addition_pipeline,
    my_repository,
    subtraction_pipeline,
)

from dagster import execute_pipeline


def test_pipelines():
    result = execute_pipeline(addition_pipeline)
    assert result.success
    assert result.result_for_solid("add").output_value() == 3

    result = execute_pipeline(subtraction_pipeline)
    assert result.success
    assert result.result_for_solid("subtract").output_value() == -1


def test_my_repository():
    assert my_repository
    assert len(my_repository.get_all_pipelines()) == 2
    assert len(my_repository.schedule_defs) == 1


def test_my_lazy_repository():
    assert my_lazy_repository
    assert len(my_lazy_repository.get_all_pipelines()) == 2
    assert len(my_lazy_repository.schedule_defs) == 1
