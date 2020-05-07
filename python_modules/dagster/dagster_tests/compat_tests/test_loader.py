from dagster import (
    ExecutionTargetHandle,
    PartitionSetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
    lambda_solid,
    pipeline,
    repository_partitions,
    schedules,
)
from dagster.utils import file_relative_path


def test_deprecated_load():
    repo = ExecutionTargetHandle.for_repo_yaml(
        file_relative_path(__file__, 'repository.yaml')
    ).build_repository_definition()
    assert len(repo.get_all_pipelines()) == 1
    assert len(repo.schedule_defs) == 1
    assert len(repo.partition_set_defs) == 1


def define_repository():
    @lambda_solid
    def hello():
        return 'hello'

    @pipeline
    def test():
        hello()

    return RepositoryDefinition('test', pipeline_defs=[test])


@schedules
def define_schedules():
    return [ScheduleDefinition('test', '0 0 * * *', 'test')]


@repository_partitions
def define_partitions():
    return [
        PartitionSetDefinition(
            name="test",
            pipeline_name="test",
            partition_fn=lambda: ["test"],
            environment_dict_fn_for_partition=lambda _: {},
        )
    ]
