# pylint: disable=no-value-for-parameter

from dagster import Output, OutputDefinition, RunConfig, execute_pipeline, pipeline, solid
from dagster.core.instance import DagsterInstance


def test_retries():
    fail = {'count': 0}

    @solid
    def fail_first_times(_, _start_fail):
        if fail['count'] < 1:
            fail['count'] += 1
            raise Exception('blah')

        return 'okay perfect'

    @solid(
        output_defs=[
            OutputDefinition(bool, 'start_fail', is_optional=True),
            OutputDefinition(bool, 'start_skip', is_optional=True),
        ]
    )
    def two_outputs(_):
        yield Output(True, 'start_fail')
        # won't yield start_skip

    @solid
    def will_be_skipped(_, _start_skip):
        pass  # doesn't matter

    @solid
    def downstream_of_failed(_, input_str):
        return input_str

    @pipeline
    def pipe():
        start_fail, start_skip = two_outputs()
        downstream_of_failed(fail_first_times(start_fail))
        will_be_skipped(start_skip)

    env = {'storage': {'filesystem': {}}}

    instance = DagsterInstance.ephemeral()

    result = execute_pipeline(pipe, environment_dict=env, instance=instance, raise_on_error=False)

    second_result = execute_pipeline(
        pipe,
        environment_dict=env,
        run_config=RunConfig(previous_run_id=result.run_id),
        instance=instance,
    )

    assert second_result.success
    downstream_of_failed = second_result.result_for_solid('downstream_of_failed').output_value()
    assert downstream_of_failed == 'okay perfect'

    will_be_skipped = [
        e for e in second_result.event_list if str(e.solid_handle) == 'will_be_skipped'
    ][0]
    assert str(will_be_skipped.event_type_value) == 'STEP_SKIPPED'
