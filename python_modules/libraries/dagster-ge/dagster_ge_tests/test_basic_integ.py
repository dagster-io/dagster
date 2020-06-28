from dagster_ge.solidconstructor import ge_data_context, ge_validation_solid_factory
from pandas import read_csv

from dagster import (
    DagsterInstance,
    InputDefinition,
    ModeDefinition,
    Output,
    execute_pipeline,
    pipeline,
    reconstructable,
    solid,
)


@solid
def yielder(_):
    return read_csv("./basic.csv")


@solid(input_defs=[InputDefinition(name='res')])
def reyielder(_context, res):
    yield Output((res[0]['statistics'], res[0]['results']))


def define_hello_world_pipeline():
    @pipeline(
        mode_defs=[ModeDefinition('basic', resource_defs={'ge_data_context': ge_data_context})]
    )
    def hello_world_pipeline():
        return reyielder(ge_validation_solid_factory("blink", "basic.warning")(yielder()))

    return hello_world_pipeline


def test_yielded_results_no_config():
    run_config = {'resources': {'ge_data_context': {'config': {'ge_root_dir': None}}}}
    result = execute_pipeline(
        reconstructable(define_hello_world_pipeline),
        run_config=run_config,
        mode='basic',
        instance=DagsterInstance.local_temp(),
    )
    assert result.result_for_solid("reyielder").output_value()[0]["success_percent"] == 100
    expectations = result.result_for_solid("ge_validation_solid").expectation_results_during_compute
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    metadata = mainexpect.metadata_entries[0].entry_data.data
    assert metadata['overall'] == {
        'evaluated_expectations': 11,
        'success_percent': 100.0,
        'successful_expectations': 11,
        'unsuccessful_expectations': 0,
    }


def test_yielded_results_config():
    run_config = {
        'resources': {'ge_data_context': {'config': {'ge_root_dir': "./great_expectations"}}}
    }
    result = execute_pipeline(
        reconstructable(define_hello_world_pipeline),
        run_config=run_config,
        mode='basic',
        instance=DagsterInstance.local_temp(),
    )
    assert result.result_for_solid("reyielder").output_value()[0]["success_percent"] == 100
    expectations = result.result_for_solid("ge_validation_solid").expectation_results_during_compute
    assert len(expectations) == 1
    mainexpect = expectations[0]
    assert mainexpect.success
    metadata = mainexpect.metadata_entries[0].entry_data.data
    assert metadata['overall'] == {
        'evaluated_expectations': 11,
        'success_percent': 100.0,
        'successful_expectations': 11,
        'unsuccessful_expectations': 0,
    }
