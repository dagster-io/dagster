import pytest

from dagster.core.errors import DagsterRunConflict
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun


def test_get_or_create_run():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    pipeline_run = PipelineRun.create_empty_run('foo_pipeline', 'new_run')
    assert instance.get_or_create_run(pipeline_run) == pipeline_run

    assert instance.get_runs() == [pipeline_run]

    assert instance.get_or_create_run(pipeline_run) == pipeline_run

    assert instance.get_runs() == [pipeline_run]

    conflicting_pipeline_run = PipelineRun.create_empty_run('bar_pipeline', 'new_run')

    with pytest.raises(DagsterRunConflict, match='Found conflicting existing run with same id.'):
        instance.get_or_create_run(conflicting_pipeline_run)
