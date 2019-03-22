from time import sleep

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    List,
    MultiprocessExecutorConfig,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidInstance,
    RunConfig,
    execute_pipeline,
    lambda_solid,
    solid,
    RunStorageMode,
)


@lambda_solid(
    inputs=[InputDefinition('units', List(Int))],
    output=OutputDefinition(Int, 'total'),
)
def sleeper(units):
    tot = 0
    for sec in units:
        sleep(sec)
        tot += sec

    return tot


@solid(
    config_field=Field(
        List(Int), is_optional=True, default_value=[1, 1, 1, 1]
    ),
    outputs=[
        OutputDefinition(List(Int), 'out_1'),
        OutputDefinition(List(Int), 'out_2'),
        OutputDefinition(List(Int), 'out_3'),
        OutputDefinition(List(Int), 'out_4'),
    ],
)
def giver(context):
    units = context.solid_config
    queues = [[], [], [], []]
    for i, sec in enumerate(units):
        queues[i % 4].append(sec)

    yield Result(queues[0], 'out_1')
    yield Result(queues[1], 'out_2')
    yield Result(queues[2], 'out_3')
    yield Result(queues[3], 'out_4')


@lambda_solid(
    inputs=[
        InputDefinition('in_1', Int),
        InputDefinition('in_2', Int),
        InputDefinition('in_3', Int),
        InputDefinition('in_4', Int),
    ],
    output=OutputDefinition(Int),
)
def total(in_1, in_2, in_3, in_4):
    return in_1 + in_2 + in_3 + in_4


def define_sleepy_pipeline():
    return PipelineDefinition(
        name="sleepy",
        solids=[giver, sleeper, total],
        dependencies={
            SolidInstance('giver'): {},
            SolidInstance('sleeper', alias='sleeper_1'): {
                'units': DependencyDefinition('giver', 'out_1')
            },
            SolidInstance('sleeper', alias='sleeper_2'): {
                'units': DependencyDefinition('giver', 'out_2')
            },
            SolidInstance('sleeper', alias='sleeper_3'): {
                'units': DependencyDefinition('giver', 'out_3')
            },
            SolidInstance('sleeper', alias='sleeper_4'): {
                'units': DependencyDefinition('giver', 'out_4')
            },
            SolidInstance('total'): {
                'in_1': DependencyDefinition('sleeper_1', 'total'),
                'in_2': DependencyDefinition('sleeper_2', 'total'),
                'in_3': DependencyDefinition('sleeper_3', 'total'),
                'in_4': DependencyDefinition('sleeper_4', 'total'),
            },
        },
    )


if __name__ == '__main__':
    pipeline = define_sleepy_pipeline()
    result = execute_pipeline(
        pipeline,
        run_config=RunConfig(
            executor_config=MultiprocessExecutorConfig(define_sleepy_pipeline),
            storage_mode=RunStorageMode.FILESYSTEM,
        ),
    )

    print(
        'Total Sleep Time: ',
        result.result_for_solid('total').transformed_value(),
    )
