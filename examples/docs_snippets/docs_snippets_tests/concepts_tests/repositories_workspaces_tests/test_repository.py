from docs_snippets.concepts.repositories_workspaces.lazy_repository_definition import (
    my_lazy_repository,
)
from docs_snippets.concepts.repositories_workspaces.repository_definition import (
    job1,
    job2,
    my_repository,
)


def test_jobs():
    result = job1.execute_in_process()
    assert result.success

    result = job2.execute_in_process()
    assert result.success


def test_my_repository():
    assert my_repository
    assert len(my_repository.get_all_pipelines()) == 4
    assert len(my_repository.schedule_defs) == 1
    assert len(my_repository.sensor_defs) == 1
    assert len(my_repository.get_all_jobs()) == 4


def test_my_lazy_repository():
    assert my_lazy_repository
    assert len(my_lazy_repository.get_all_pipelines()) == 3
    assert len(my_lazy_repository.schedule_defs) == 1
    assert len(my_lazy_repository.sensor_defs) == 1
    assert len(my_lazy_repository.get_all_jobs()) == 1
