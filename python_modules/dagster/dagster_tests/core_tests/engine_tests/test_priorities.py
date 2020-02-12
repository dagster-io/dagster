from dagster import DagsterInstance, ExecutionTargetHandle, execute_pipeline, pipeline, solid


@solid(tags={'dagster/priority': '-1'})
def low(_):
    pass


@solid
def none(_):
    pass


@solid(tags={'dagster/priority': '1'})
def high(_):
    pass


@pipeline
def priority_test():
    none()
    low()
    high()
    none()
    low()
    high()


def test_priorities():

    result = execute_pipeline(priority_test,)
    assert result.success
    assert [
        str(event.solid_handle) for event in result.step_event_list if event.is_step_success
    ] == ['high', 'high_2', 'none', 'none_2', 'low', 'low_2']


def test_priorities_mp():
    pipe = ExecutionTargetHandle.for_pipeline_python_file(
        __file__, 'priority_test'
    ).build_pipeline_definition()
    result = execute_pipeline(
        pipe,
        {
            'execution': {'multiprocess': {'config': {'max_concurrent': 1}}},
            'storage': {'filesystem': {}},
        },
        instance=DagsterInstance.local_temp(),
    )
    assert result.success
    assert [
        str(event.solid_handle) for event in result.step_event_list if event.is_step_success
    ] == ['high', 'high_2', 'none', 'none_2', 'low', 'low_2']
