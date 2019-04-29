from dagster import (
    resource,
    MultiprocessExecutorConfig,
    PipelineContextDefinition,
    PipelineDefinition,
    RunConfig,
    execute_pipeline,
    solid,
    RunStorageMode,
)


def define_resource():
    @resource
    def a_resource(_):
        return None

    return a_resource


lots_of_resources = {'R' + str(r): define_resource() for r in range(20)}


@solid(resources=set(lots_of_resources.keys()))
def all_resources(_):
    return 1


@solid(resources={'R1'})
def one(_):
    return 1


@solid(resources={'R2'})
def two(_):
    return 1


@solid(resources={'R1', 'R2', 'R3'})
def one_and_two_and_three(_):
    return 1


def define_resource_pipeline():
    return PipelineDefinition(
        name='resources for days',
        solids=[all_resources, one, two, one_and_two_and_three],
        context_definitions={'default': PipelineContextDefinition(resources=lots_of_resources)},
    )


if __name__ == '__main__':
    pipeline = define_resource_pipeline()
    result = execute_pipeline(
        pipeline,
        run_config=RunConfig(
            executor_config=MultiprocessExecutorConfig(define_resource_pipeline),
            storage_mode=RunStorageMode.FILESYSTEM,
        ),
    )
