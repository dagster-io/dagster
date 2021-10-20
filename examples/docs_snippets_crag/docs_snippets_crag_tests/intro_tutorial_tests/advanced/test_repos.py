from dagster.utils import pushd, script_relative_path
from docs_snippets_crag.intro_tutorial.advanced.repositories.repos import hello_cereal_repository
from docs_snippets_crag.intro_tutorial.advanced.scheduling.scheduler import (
    hello_cereal_repository as scheduler_repository,
)


def test_define_repo():
    repo = hello_cereal_repository
    assert repo.name == "hello_cereal_repository"
    assert repo.has_job("hello_cereal_job")
    with pushd(
        script_relative_path("../../../docs_snippets_crag/intro_tutorial/advanced/repositories/")
    ):
        result = repo.get_job("hello_cereal_job").execute_in_process()
    assert result.success


def test_define_scheduler_repo():
    repo = scheduler_repository
    assert repo.name == "hello_cereal_repository"
    assert repo.has_job("hello_cereal_job")
    with pushd(
        script_relative_path("../../../docs_snippets_crag/intro_tutorial/advanced/scheduling/")
    ):
        result = repo.get_job(
            "hello_cereal_job",
        ).execute_in_process({"ops": {"hello_cereal": {"config": {"date": "date"}}}})
    assert result.success
