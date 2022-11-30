import datetime
from typing import Any, Dict

import great_expectations as ge
from dagster_pandas import DataFrame
from great_expectations.render.renderer import ValidationResultsPageRenderer
from great_expectations.render.view import DefaultMarkdownPageView

from dagster import (
    ExpectationResult,
    In,
    MetadataEntry,
    MetadataValue,
    Noneable,
    Out,
    Output,
    StringSource,
)
from dagster import _check as check
from dagster import op, resource

try:
    # ge < v0.13.0
    from great_expectations.core import convert_to_json_serializable
except ImportError:
    # ge >= v0.13.0
    from great_expectations.core.util import convert_to_json_serializable


@resource(config_schema={"ge_root_dir": Noneable(StringSource)})
def ge_data_context(context):
    if context.resource_config["ge_root_dir"] is None:
        yield ge.data_context.DataContext()
    else:
        yield ge.data_context.DataContext(context_root_dir=context.resource_config["ge_root_dir"])


def ge_validation_op_factory(
    name,
    datasource_name,
    suite_name,
    validation_operator_name=None,
    input_dagster_type=DataFrame,
    batch_kwargs=None,
):
    """Generates ops for interacting with GE.

    Args:
        name (str): the name of the op
        datasource_name (str): the name of your DataSource, see your great_expectations.yml
        suite_name (str): the name of your expectation suite, see your great_expectations.yml
        validation_operator_name (Optional[str]): what validation operator to run  -- defaults to
            None, which generates an ephemeral validator.  If you want to save data docs, use
            'action_list_operator'.
            See https://docs.greatexpectations.io/en/latest/reference/core_concepts/validation_operators_and_actions.html
        input_dagster_type (DagsterType): the Dagster type used to type check the input to the op.
            Defaults to `dagster_pandas.DataFrame`.
        batch_kwargs (Optional[dict]): overrides the `batch_kwargs` parameter when calling the
            `ge_data_context`'s `get_batch` method. Defaults to `{"dataset": dataset}`, where
            `dataset` is the input to the generated op.
    Returns:
        An op that takes in a set of data and yields both an expectation with relevant metadata
        and an output with all the metadata (for user processing)
    """
    check.str_param(datasource_name, "datasource_name")
    check.str_param(suite_name, "suite_name")
    check.opt_str_param(validation_operator_name, "validation_operator_name")
    batch_kwargs = check.opt_dict_param(batch_kwargs, "batch_kwargs")

    @op(
        name=name,
        ins={"dataset": In(input_dagster_type)},
        out=Out(
            dict,
            description="""
        This op yields an expectationResult with a structured dict of metadata from
        the GE suite, as well as the full result in case a user wants to process it differently.
        The structured dict contains both summary stats from the suite as well as expectation by
        expectation results/details.
        """,
        ),
        required_resource_keys={"ge_data_context"},
        tags={"kind": "ge"},
    )
    def _ge_validation_fn(context, dataset):
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
        final_batch_kwargs = batch_kwargs or {"dataset": dataset}
        if "datasource" in final_batch_kwargs:
            context.log.warning(
                "`datasource` field of `batch_kwargs` will be ignored; use the `datasource_name` "
                "parameter of the op factory instead."
            )
        final_batch_kwargs["datasource"] = datasource_name
        batch = data_context.get_batch(final_batch_kwargs, suite)
        run_id = {
            "run_name": datasource_name + " run",
            "run_time": datetime.datetime.utcnow(),
        }
        results = data_context.run_validation_operator(
            validation_operator, assets_to_validate=[batch], run_id=run_id
        )
        res = convert_to_json_serializable(results.list_validation_results())[0]
        validation_results_page_renderer = ValidationResultsPageRenderer(run_info_at_end=True)
        rendered_document_content_list = (
            validation_results_page_renderer.render_validation_operator_result(results)
        )
        md_str = " ".join(DefaultMarkdownPageView().render(rendered_document_content_list))

        meta_stats = MetadataEntry("Expectation Results", value=MetadataValue.md(md_str))
        yield ExpectationResult(
            success=res["success"],
            metadata_entries=[
                meta_stats,
            ],
        )
        yield Output(res)

    return _ge_validation_fn


def ge_validation_op_factory_v3(
    name,
    datasource_name,
    data_connector_name,
    data_asset_name,
    suite_name,
    batch_identifiers: dict,
    input_dagster_type=DataFrame,
    runtime_method_type="batch_data",
    extra_kwargs=None,
):
    """Generates ops for interacting with GE (v3 API)

    Args:
        name (str): the name of the op
        datasource_name (str): the name of your DataSource, see your great_expectations.yml
        data_connector_name (str): the name of the data connector for this datasource. This should
            point to a RuntimeDataConnector. For information on how to set this up, see:
            https://docs.greatexpectations.io/docs/guides/connecting_to_your_data/how_to_create_a_batch_of_data_from_an_in_memory_spark_or_pandas_dataframe
        data_asset_name (str): the name of the data asset that this op will be validating.
        suite_name (str): the name of your expectation suite, see your great_expectations.yml
        batch_identifier_fn (dict): A dicitonary of batch identifiers to uniquely identify this
            batch of data. To learn more about batch identifiers, see:
            https://docs.greatexpectations.io/docs/reference/datasources#batches.
        input_dagster_type (DagsterType): the Dagster type used to type check the input to the op.
            Defaults to `dagster_pandas.DataFrame`.
        runtime_method_type (str): how GE should interperet the op input. One of ("batch_data",
            "path", "query"). Defaults to "batch_data", which will interperet the input as an
            in-memory object.
        extra_kwargs (Optional[dict]): adds extra kwargs to the invocation of `ge_data_context`'s
            `get_validator` method. If not set, input will be:
                {
                    "datasource_name": datasource_name,
                    "data_connector_name": data_connector_name,
                    "data_asset_name": data_asset_name,
                    "runtime_parameters": {
                        "<runtime_method_type>": <op input>
                    },
                    "batch_identifiers": batch_identifiers,
                    "expectation_suite_name": suite_name,
                }

    Returns:
        An op that takes in a set of data and yields both an expectation with relevant metadata and
        an output with all the metadata (for user processing)

    """

    check.str_param(datasource_name, "datasource_name")
    check.str_param(data_connector_name, "data_connector_name")
    check.str_param(suite_name, "suite_name")

    _extra_kwargs: Dict[Any, Any] = check.opt_dict_param(extra_kwargs, "extra_kwargs")

    @op(
        name=name,
        ins={"dataset": In(input_dagster_type)},
        out=Out(
            dict,
            description="""
        This op yields an ExpectationResult with a structured dict of metadata from
        the GE suite, as well as the full result in case a user wants to process it differently.
        The structured dict contains both summary stats from the suite as well as expectation by
        expectation results/details.
        """,
        ),
        required_resource_keys={"ge_data_context"},
        tags={"kind": "ge"},
    )
    def _ge_validation_fn(context, dataset):
        data_context = context.resources.ge_data_context
        validator_kwargs = {
            "datasource_name": datasource_name,
            "data_connector_name": data_connector_name,
            "data_asset_name": datasource_name or data_asset_name,
            "runtime_parameters": {runtime_method_type: dataset},
            "batch_identifiers": batch_identifiers,
            "expectation_suite_name": suite_name,
            **_extra_kwargs,
        }
        validator = data_context.get_validator(**validator_kwargs)

        run_id = {
            "run_name": datasource_name + " run",
            "run_time": datetime.datetime.utcnow(),
        }
        results = validator.validate(run_id=run_id)

        validation_results_page_renderer = ValidationResultsPageRenderer(run_info_at_end=True)
        rendered_document_content_list = validation_results_page_renderer.render(
            validation_results=results
        )
        md_str = "".join(DefaultMarkdownPageView().render(rendered_document_content_list))

        meta_stats = MetadataEntry("Expectation Results", value=MetadataValue.md(md_str))
        yield ExpectationResult(
            success=bool(results["success"]),
            metadata_entries=[meta_stats],
        )
        yield Output(results.to_json_dict())

    return _ge_validation_fn
