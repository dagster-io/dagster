import great_expectations as ge
from dagster_ge import (
    create_expectation_result,
    expectation_result_list_from_validation,
    expectation_results_from_validation,
)

from dagster import execute_pipeline, file_relative_path, pipeline, solid


def test_dummy_ge():
    df = ge.read_csv(file_relative_path(__file__, './num.csv'))
    ge_evr = df.expect_column_mean_to_be_between('num1', 0, 10)

    er = create_expectation_result('expect_column_mean_to_be_between', ge_evr)

    assert er.label == 'expect_column_mean_to_be_between'
    assert er.success
    assert len(er.metadata_entries) == 1
    assert er.metadata_entries[0].label == 'evr'
    assert er.metadata_entries[0].entry_data.data == {
        'success': True,
        'result': {
            'observed_value': 2.0,
            'element_count': 2,
            'missing_count': 0,
            'missing_percent': 0.0,
        },
    }


def test_execute_expectation_suite_success():
    df = ge.read_csv(file_relative_path(__file__, './num.csv'))
    validation = df.validate(
        expectation_suite=file_relative_path(__file__, 'num_expectations.json')
    )

    ers = expectation_result_list_from_validation(validation)

    assert len(ers) == 3
    assert ers[0].label == 'expect_column_to_exist'
    assert ers[0].success is True
    assert ers[0].metadata_entries[0].entry_data.data == {
        'success': True,
        'exception_info': {
            'raised_exception': False,
            'exception_message': None,
            'exception_traceback': None,
        },
        'expectation_config': {
            'expectation_type': 'expect_column_to_exist',
            'kwargs': {'column': 'num1'},
        },
    }

    assert ers[1].label == 'expect_column_to_exist'
    assert ers[1].success is True

    assert ers[1].metadata_entries[0].entry_data.data == {
        'success': True,
        'exception_info': {
            'raised_exception': False,
            'exception_message': None,
            'exception_traceback': None,
        },
        'expectation_config': {
            'expectation_type': 'expect_column_to_exist',
            'kwargs': {'column': 'num2'},
        },
    }

    assert ers[2].label == 'expect_column_mean_to_be_between'
    assert ers[2].success is True
    assert ers[2].metadata_entries[0].entry_data.data == {
        'success': True,
        'result': {
            'observed_value': 2.0,
            'element_count': 2,
            'missing_count': 0,
            'missing_percent': 0.0,
        },
        'exception_info': {
            'raised_exception': False,
            'exception_message': None,
            'exception_traceback': None,
        },
        'expectation_config': {
            'expectation_type': 'expect_column_mean_to_be_between',
            'kwargs': {'column': 'num1', 'min_value': 0, 'max_value': 10},
        },
    }


def test_execute_expectation_suite_failure():
    df = ge.read_csv(file_relative_path(__file__, './num_bad_data.csv'))
    validation = df.validate(
        expectation_suite=file_relative_path(__file__, 'num_expectations.json')
    )

    ers = expectation_result_list_from_validation(validation)

    assert ers[0].success is True
    assert ers[1].success is True
    assert ers[2].success is False

    assert ers[2].metadata_entries[0].entry_data.data == {
        'success': False,
        'result': {
            'observed_value': -2.0,
            'element_count': 2,
            'missing_count': 0,
            'missing_percent': 0.0,
        },
        'exception_info': {
            'raised_exception': False,
            'exception_message': None,
            'exception_traceback': None,
        },
        'expectation_config': {
            'expectation_type': 'expect_column_mean_to_be_between',
            'kwargs': {'column': 'num1', 'min_value': 0, 'max_value': 10},
        },
    }


@solid(output_defs=[])
def valid_data(_):
    df = ge.read_csv(file_relative_path(__file__, './num.csv'))
    for er in expectation_results_from_validation(
        df.validate(expectation_suite=file_relative_path(__file__, 'num_expectations.json'))
    ):
        yield er


@solid(output_defs=[])
def invalid_data(_):
    df = ge.read_csv(file_relative_path(__file__, './num_bad_data.csv'))
    for er in expectation_results_from_validation(
        df.validate(expectation_suite=file_relative_path(__file__, 'num_expectations.json'))
    ):
        yield er


@pipeline
def ge_hello_world_pipeline():

    valid_data()
    invalid_data()


def test_within_pipeline():
    pipeline_result = execute_pipeline(ge_hello_world_pipeline)
    assert pipeline_result.success
