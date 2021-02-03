from dagster import execute_pipeline, pipeline, reconstructable, solid
from dagster.core.test_utils import instance_for_test


@solid(tags={"dagster/priority": "-1"})
def low(_):
    pass


@solid
def none(_):
    pass


@solid(tags={"dagster/priority": "1"})
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

    result = execute_pipeline(
        priority_test,
    )
    assert result.success
    assert [
        str(event.solid_handle) for event in result.step_event_list if event.is_step_success
    ] == ["high", "high_2", "none", "none_2", "low", "low_2"]


def test_priorities_mp():
    with instance_for_test() as instance:
        pipe = reconstructable(priority_test)
        result = execute_pipeline(
            pipe,
            {
                "execution": {"multiprocess": {"config": {"max_concurrent": 1}}},
                "intermediate_storage": {"filesystem": {}},
            },
            instance=instance,
        )
        assert result.success
        assert [
            str(event.solid_handle) for event in result.step_event_list if event.is_step_success
        ] == ["high", "high_2", "none", "none_2", "low", "low_2"]
