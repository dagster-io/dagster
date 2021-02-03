from dagster import execute_pipeline
from dagster.utils import pushd, script_relative_path
from docs_snippets.intro_tutorial.advanced.repositories.repos import hello_cereal_repository
from docs_snippets.intro_tutorial.advanced.scheduling.scheduler import (
    hello_cereal_repository as scheduler_repository,
)


def test_define_repo():
    repo = hello_cereal_repository
    assert repo.name == "hello_cereal_repository"
    assert repo.has_pipeline("hello_cereal_pipeline")
    with pushd(
        script_relative_path("../../../docs_snippets/intro_tutorial/advanced/repositories/")
    ):
        result = execute_pipeline(repo.get_pipeline("hello_cereal_pipeline"))
    assert result.success


def test_define_scheduler_repo():
    repo = scheduler_repository
    assert repo.name == "hello_cereal_repository"
    assert repo.has_pipeline("hello_cereal_pipeline")
    with pushd(script_relative_path("../../../docs_snippets/intro_tutorial/advanced/scheduling/")):
        result = execute_pipeline(
            repo.get_pipeline(
                "hello_cereal_pipeline",
            ),
            {"solids": {"hello_cereal": {"inputs": {"date": {"value": "date"}}}}},
        )
    assert result.success
