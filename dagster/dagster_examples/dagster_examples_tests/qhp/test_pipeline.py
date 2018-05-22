from dagster.dagster_examples.qhp.pipeline import define_pipeline
from dagster.core.execution import (
    execute_pipeline_through_solid, DagsterExecutionContext, execute_pipeline
)
from dagster.utils.test import script_relative_path


def providers_771_args():
    return {
        'qhp_json_input': {
            'path': script_relative_path('providers-771.json'),
        }
    }


def test_plans():
    pipeline = define_pipeline()

    result = execute_pipeline_through_solid(
        DagsterExecutionContext(),
        pipeline,
        input_arg_dicts=providers_771_args(),
        solid_name='plans',
    )

    plans_df = result.materialized_output

    assert not plans_df.empty


def test_plan_years():
    pipeline = define_pipeline()

    result = execute_pipeline_through_solid(
        DagsterExecutionContext(),
        pipeline,
        input_arg_dicts=providers_771_args(),
        solid_name='plan_years',
    )

    plan_years_df = result.materialized_output

    assert not plan_years_df.empty


def test_plan_and_plan_years_pipeline():
    pipeline = define_pipeline()

    results = execute_pipeline(
        DagsterExecutionContext(), pipeline, providers_771_args(), ['plans', 'plan_years']
    )
    assert len(results) == 2


def test_insurance_pipeline():
    pipeline = define_pipeline()

    result = execute_pipeline_through_solid(
        DagsterExecutionContext(),
        pipeline,
        providers_771_args(),
        solid_name='insurance',
    )
    assert result.success
    assert result.name == 'insurance'
    assert not result.materialized_output.empty


def test_practices_pipeline():
    pipeline = define_pipeline()

    # this should only execute the solids necessary
    # to produce practices. i.e. addresses, providers and practices
    results = execute_pipeline(
        DagsterExecutionContext(),
        pipeline,
        providers_771_args(),
        through_solids=['practices'],
    )

    assert len(results) == 3

    result_names = [result.name for result in results]

    executed_list = ['addresses', 'providers', 'practices']

    for executed in executed_list:
        assert executed in result_names

    for result in results:
        if not result.success:
            raise result.exception
        assert result.success
        assert not result.materialized_output.empty


def test_practice_insurances_pipeline():
    pipeline = define_pipeline()

    results = execute_pipeline(
        DagsterExecutionContext(),
        pipeline,
        providers_771_args(),
        through_solids=['practice_insurances'],
    )

    assert len(results) == 7

    result_names = [result.name for result in results]

    executed_list = [
        'addresses',
        'providers',
        'practices',
        'plans',
        'plan_years',
        'insurance',
        'practice_insurances',
    ]

    for executed in executed_list:
        assert executed in result_names

    for result in results:
        assert result.success
        assert not result.materialized_output.empty


def test_languages_pipeline():
    pipeline = define_pipeline()

    result = execute_pipeline_through_solid(
        DagsterExecutionContext(),
        pipeline,
        input_arg_dicts={'languages_csv': {
            'path': script_relative_path('Language.csv')
        }},
        solid_name='languages',
    )

    assert result.success
    df = result.materialized_output
    assert list(df.columns) == [
        'SK_Language', 'ISO639-3Code', 'ISO639-2BCode', 'ISO639-2TCode', 'ISO639-1Code',
        'LanguageName', 'Scope', 'Type', 'MacroLanguageISO639-3Code', 'MacroLanguageName', 'IsChild'
    ]


def test_specialities_pipeline():
    pipeline = define_pipeline()

    result = execute_pipeline_through_solid(
        DagsterExecutionContext(),
        pipeline,
        input_arg_dicts={
            'specialities_csv': {
                'path': script_relative_path('betterdoctor_qhp_specialities.csv')
            }
        },
        solid_name='specialities',
    )

    assert result.success
    df = result.materialized_output
    assert list(df.columns) == [
        'betterdoctor_uid', 'client_name_org', 'client_id', 'client_name', 'mappable', 'Notes'
    ]


def all_external_arg_dicts():
    return {
        'languages_csv': {
            'path': script_relative_path('Language.csv')
        },
        'specialities_csv': {
            'path': script_relative_path('betterdoctor_qhp_specialities.csv')
        },
        'qhp_json_input': {
            'path': script_relative_path('providers-771.json'),
        },
    }


def test_provider_languages_specialities():
    pipeline = define_pipeline()

    results = execute_pipeline(
        DagsterExecutionContext(),
        pipeline,
        input_arg_dicts=all_external_arg_dicts(),
        through_solids=['provider_languages_specialities'],
    )

    assert len(results) == 4

    for result in results:
        assert result.success

    result_names = [result.name for result in results]

    executed_list = [
        'providers',
        'languages',
        'specialities',
        'provider_languages_specialities',
    ]

    for executed in executed_list:
        assert executed in result_names


if __name__ == '__main__':
    from dagster.embedded_cli import embedded_dagster_single_pipeline_cli_main
    import sys

    embedded_dagster_single_pipeline_cli_main(sys.argv, define_pipeline())
