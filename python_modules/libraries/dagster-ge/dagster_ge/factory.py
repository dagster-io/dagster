import datetime

import great_expectations as ge
from dagster_pandas import DataFrame
from great_expectations.core import convert_to_json_serializable
from great_expectations.render.page_renderer_util import (
    render_multiple_validation_result_pages_markdown,
)

from dagster import (
    EventMetadataEntry,
    ExpectationResult,
    InputDefinition,
    Noneable,
    Output,
    OutputDefinition,
    StringSource,
    resource,
    solid,
)


@resource(config_schema={"ge_root_dir": Noneable(StringSource)})
def ge_data_context(context):
    if context.resource_config["ge_root_dir"] is None:
        yield ge.data_context.DataContext()
    else:
        yield ge.data_context.DataContext(context_root_dir=context.resource_config["ge_root_dir"])


def ge_validation_solid_factory(datasource_name, suite_name, validation_operator_name=None):
    """
        Generates solids for interacting with GE, currently only works on pandas dataframes
    Args:
        datasource_name (str): the name of your pandas DataSource, see your great_expectations.yml
        suite_name (str): the name of your expectation suite, see your great_expectations.yml
        validation_operator_name (Optional[str]): what validation operator to run  -- defaults to None,
                    which generates an ephemeral validator.
                    If you want to save data docs, use 'action_list_operator'.
                    See https://docs.greatexpectations.io/en/latest/reference/core_concepts/validation_operators_and_actions.html

    Returns:
        A solid that takes in an in-memory dataframe and yields both an expectation with relevant metadata
        and an output with all the metadata (for user processing)

    """

    @solid(
        input_defs=[InputDefinition("pandas_df", dagster_type=DataFrame)],
        output_defs=[
            OutputDefinition(
                dagster_type=dict,
                description="""
        This solid yields an expectationResult with a structured dict of metadata from the GE suite,
        as well as the full result in case a user wants to process it differently.
        The structured dict contains both summary stats from the suite as well as expectation by expectation
        results/details.
        """,
            )
        ],
        required_resource_keys={"ge_data_context"},
        tags={"kind": "ge"},
    )
    def ge_validation_solid(context, pandas_df):
        data_context = context.resources.ge_data_context
        if validation_operator_name is not None:
            validation_operator = validation_operator_name
        else:
            data_context.add_validation_operator(
                "ephemeral_validation",
                {"class_name": "ActionListValidationOperator", "action_list": []},
            )
            validation_operator = "ephemeral_validation"
        suite = data_context.get_expectation_suite(suite_name)
        batch_kwargs = {
            "dataset": pandas_df,
            "datasource": datasource_name,
        }
        batch = data_context.get_batch(batch_kwargs, suite)
        run_id = {
            "run_name": datasource_name + " run",
            "run_time": datetime.datetime.utcnow(),
        }
        results = data_context.run_validation_operator(
            validation_operator, assets_to_validate=[batch], run_id=run_id
        )
        res = convert_to_json_serializable(results.list_validation_results())[0]
        md_str = render_multiple_validation_result_pages_markdown(
            validation_operator_result=results, run_info_at_end=True,
        )
        meta_stats = EventMetadataEntry.md(md_str=md_str, label="Expectation Results")
        yield ExpectationResult(
            success=res["success"], metadata_entries=[meta_stats,],
        )
        yield Output(res)

    return ge_validation_solid
