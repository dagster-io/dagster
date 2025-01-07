import datetime
from collections.abc import Mapping
from typing import Any, Literal, Optional

import great_expectations as ge
from dagster import (
    ConfigurableResource,
    ExpectationResult,
    IAttachDifferentObjectToOpContext,
    In,
    MetadataValue,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
    _check as check,
    op,
    resource,
)
from dagster._annotations import beta
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._core.types.dagster_type import DagsterType
from dagster_pandas import DataFrame
from great_expectations.render.renderer import ValidationResultsPageRenderer
from great_expectations.render.view import DefaultMarkdownPageView
from pydantic import Field


@beta
class GEContextResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    ge_root_dir: Optional[str] = Field(
        default=None,
        description="The root directory for your Great Expectations project.",
    )

    def get_data_context(self):
        if self.ge_root_dir is None:
            return ge.data_context.DataContext()
        return ge.data_context.DataContext(context_root_dir=self.ge_root_dir)

    def get_object_to_set_on_execution_context(self):
        return self.get_data_context()


@beta
@dagster_maintained_resource
@resource(config_schema=GEContextResource.to_config_schema())
def ge_data_context(context: InitResourceContext) -> GEContextResource:
    return GEContextResource.from_resource_context(context).get_data_context()


@beta
def ge_validation_op_factory(
    name: str,
    datasource_name: str,
    data_connector_name: str,
    data_asset_name: str,
    suite_name: str,
    batch_identifiers: dict,
    input_dagster_type: DagsterType = DataFrame,  # default to pandas support
    runtime_method_type: Literal["batch_data", "path", "query"] = "batch_data",
    extra_kwargs: Optional[Mapping[str, Any]] = None,
) -> OpDefinition:
    """Generates ops for interacting with Great Expectations.

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

                ::

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

    _extra_kwargs = check.opt_mapping_param(extra_kwargs, "extra_kwargs")

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
        tags={COMPUTE_KIND_TAG: "ge"},
    )
    def _ge_validation_fn(context: OpExecutionContext, dataset):
        data_context = context.resources.ge_data_context

        validator = data_context.get_validator(
            datasource_name=datasource_name,
            data_connector_name=data_connector_name,
            data_asset_name=datasource_name or data_asset_name,
            runtime_parameters={runtime_method_type: dataset},
            batch_identifiers=batch_identifiers,
            expectation_suite_name=suite_name,
            **_extra_kwargs,
        )

        run_id = {
            "run_name": datasource_name + " run",
            "run_time": datetime.datetime.now(datetime.timezone.utc),
        }
        results = validator.validate(run_id=run_id)

        validation_results_page_renderer = ValidationResultsPageRenderer(run_info_at_end=True)
        rendered_document_content_list = validation_results_page_renderer.render(
            validation_results=results
        )
        md_str = "".join(DefaultMarkdownPageView().render(rendered_document_content_list))

        yield ExpectationResult(
            success=bool(results["success"]),
            metadata={"Expectation Results": MetadataValue.md(md_str)},
        )
        yield Output(results.to_json_dict())

    return _ge_validation_fn
