import json

from dagster.utils import script_relative_path

from .utils import sync_execute_get_events


def get_expectation_results(logs, solid_name):
    def _f():
        for log in logs:
            if (
                log['__typename'] == 'StepExpectationResultEvent'
                and log['step']['solidHandle'] == solid_name
            ):
                yield log

    return list(_f())


def get_expectation_result(logs, solid_name):
    expt_results = get_expectation_results(logs, solid_name)
    if len(expt_results) != 1:
        raise Exception('Only expected one expectation result')
    return expt_results[0]


def test_basic_expectations_within_transforms():
    logs = sync_execute_get_events(variables={'pipeline': {'name': 'pipeline_with_expectations'}})

    emit_failed_expectation_event = get_expectation_result(logs, 'emit_failed_expectation')
    assert emit_failed_expectation_event['expectationResult']['success'] is False
    assert emit_failed_expectation_event['expectationResult']['message'] == 'Failure'
    failed_result_metadata = json.loads(
        emit_failed_expectation_event['expectationResult']['resultMetadataJsonString']
    )
    assert emit_failed_expectation_event['expectationResult']['name'] == 'always_false'

    assert failed_result_metadata == {'reason': 'Relentless pessimism.'}

    emit_successful_expectation_event = get_expectation_result(logs, 'emit_successful_expectation')

    assert emit_successful_expectation_event['expectationResult']['success'] is True
    assert emit_successful_expectation_event['expectationResult']['message'] == 'Successful'
    assert emit_successful_expectation_event['expectationResult']['name'] == 'always_true'
    successful_result_metadata = json.loads(
        emit_successful_expectation_event['expectationResult']['resultMetadataJsonString']
    )

    assert successful_result_metadata == {'reason': 'Just because.'}

    emit_no_metadata = get_expectation_result(logs, 'emit_successful_expectation_no_metadata')

    assert emit_no_metadata['expectationResult']['resultMetadataJsonString'] is None


def test_basic_input_output_expectations(snapshot):
    logs = sync_execute_get_events(
        variables={
            'pipeline': {'name': 'pandas_hello_world_with_expectations'},
            'config': {
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}}
                    }
                }
            },
        }
    )

    expectation_results = get_expectation_results(logs, 'df_expectations_solid')
    assert len(expectation_results) == 2

    snapshot.assert_match(expectation_results)
