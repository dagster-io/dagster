import importlib.util
import os

import pytest

import dagster as dg

snippets_folder = dg.file_relative_path(__file__, "../docs_snippets/")

EXCLUDED_FILES = {
    # TEMPORARY: dagster-cloud environment is weird and confusing
    f"{snippets_folder}/guides/data-assets/quality-testing/freshness-checks/anomaly-detection.py",
    f"{snippets_folder}/guides/data-modeling/metadata/plus-references.py",
    f"{snippets_folder}/dagster-plus/insights/snowflake/snowflake-dbt-asset-insights.py",
    f"{snippets_folder}/dagster-plus/insights/snowflake/snowflake-resource-insights.py",
    f"{snippets_folder}/dagster-plus/insights/google-bigquery/bigquery-resource-insights.py",
    # see DOC-375
    f"{snippets_folder}/guides/data-modeling/asset-factories/python-asset-factory.py",
    f"{snippets_folder}/guides/data-modeling/asset-factories/simple-yaml-asset-factory.py",
    f"{snippets_folder}/guides/data-modeling/asset-factories/advanced-yaml-asset-factory.py",
    # setuptools.setup() eventually parses the command line that caused setup() to be called.
    # it errors because the command line for this test is for pytest and doesn't align with the arguments
    # setup() expects. So omit files that call setup() since they cannot be loaded without errors.
    f"{snippets_folder}/dagster-plus/deployment/serverless/runtime-environment/data_files_setup.py",
    f"{snippets_folder}/dagster-plus/deployment/serverless/runtime-environment/example_setup.py",
    # these files are part of a completed project and the import references are failing the tests
    f"{snippets_folder}/guides/tutorials/etl_tutorial_completed/etl_tutorial/assets.py",
    f"{snippets_folder}/guides/tutorials/etl_tutorial_completed/etl_tutorial/definitions.py",
    # there are no components defined in the snippets and so it would fail to load
    f"{snippets_folder}/guides/components/existing-project/definitions-after.py",
    # there are no components defined in the snippets and so it would fail to load
    f"{snippets_folder}/guides/components/index/5-definitions.py",
    f"{snippets_folder}/guides/components/existing-project/2-setup.py",
    f"{snippets_folder}/guides/components/existing-project/8-initial-definitions.py",
    f"{snippets_folder}/guides/components/existing-project/9-updated-definitions.py",
    f"{snippets_folder}/guides/components/migrating-definitions/2-definitions-before.py",
    f"{snippets_folder}/guides/components/migrating-definitions/5-elt-nested-definitions.py",
    f"{snippets_folder}/guides/components/migrating-definitions/7-definitions-after.py",
    f"{snippets_folder}/guides/components/migrating-definitions/10-definitions-after-all.py",
    f"{snippets_folder}/guides/dg/creating-dg-plugin/2-empty-defs.py",
    f"{snippets_folder}/guides/dg/creating-dg-plugin/4-init.py",
    # there are no defs defined in the snippets and so it would fail to load
    f"{snippets_folder}/guides/dg/migrating-definitions/2-definitions-before.py",
    f"{snippets_folder}/guides/dg/migrating-definitions/4-definitions-after.py",
    f"{snippets_folder}/guides/dg/migrating-definitions/7-definitions-after-all.py",
    f"{snippets_folder}/guides/dg/migrating-project/2-setup.py",
    f"{snippets_folder}/guides/dg/migrating-project/12-initial-definitions.py",
    f"{snippets_folder}/guides/dg/migrating-project/13-updated-definitions.py",
    f"{snippets_folder}/guides/dg/using-resources/1-asset-one.py",
    f"{snippets_folder}/guides/dg/using-resources/2-resources-at-defs-root.py",
    f"{snippets_folder}/guides/dg/using-resources/3-resource-defs-at-project-root.py",
    f"{snippets_folder}/guides/components/integrations/dlt-component/5-loads.py",
    # migrated from legacy `docs_snippets/`
    f"{snippets_folder}/concepts/assets/asset_group_module.py",
    f"{snippets_folder}/concepts/assets/asset_input_managers_numpy.py",
    f"{snippets_folder}/concepts/assets/subset_graph_backed_asset_unexpected_materializations.py",
    f"{snippets_folder}/concepts/configuration/make_values_resource_run_config.py",
    f"{snippets_folder}/concepts/declarative_automation/allow_missing_upstreams.py",
    f"{snippets_folder}/concepts/io_management/input_managers.py",
    f"{snippets_folder}/concepts/io_management/loading_multiple_upstream_partitions.py",
    f"{snippets_folder}/concepts/ops_jobs_graphs/nested_graphs.py",
    f"{snippets_folder}/concepts/partitions_schedules_sensors/schedule_from_partitions.py",
    f"{snippets_folder}/concepts/partitions_schedules_sensors/schedules/schedule_examples.py",
    f"{snippets_folder}/concepts/webserver/graphql/client_example.py",
    f"{snippets_folder}/dagster-university/lesson_3.py",
    f"{snippets_folder}/deploying/airflow/mounted.py",
    f"{snippets_folder}/guides/dagster/code_references/with_dbt_code_references.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/custom_bootstrap_loader.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/custom_context_injector.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/custom_context_loader.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/custom_message_reader.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/custom_message_writer.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/session_lifecycle_external.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/dagster_pipes_details_and_customization/session_lifecycle_orchestration.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/databricks/databricks_asset_client.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/ecs/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/emr-containers/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/emr-serverless/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/emr/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/gcp/dataproc_job/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/gcp/dataproc_job/upload_artifacts.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/glue/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/lambda/dagster_code.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/json_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/markdown_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/notebook_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/path_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_column_lineage.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_schema_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/timestamp_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_pipes/subprocess/rich_metadata/url_metadata.py",
    f"{snippets_folder}/guides/dagster/dagster_type_factories/job_1_execution.py",
    f"{snippets_folder}/guides/dagster/dagster_type_factories/job_2.py",
    f"{snippets_folder}/guides/dagster/dagster_type_factories/job_2_execution.py",
    f"{snippets_folder}/guides/dagster/dagster_type_factories/schema.py",
    f"{snippets_folder}/guides/dagster/dagster_type_factories/schema_execution.py",
    f"{snippets_folder}/guides/dagster/development_to_production/assets_v2.py",
    f"{snippets_folder}/guides/dagster/development_to_production/test_assets.py",
    f"{snippets_folder}/guides/dagster/development_to_production/branch_deployments/repository_v1.py",
    f"{snippets_folder}/guides/dagster/development_to_production/branch_deployments/repository_v2.py",
    f"{snippets_folder}/guides/dagster/development_to_production/branch_deployments/repository_v3.py",
    f"{snippets_folder}/guides/dagster/development_to_production/repository/repository_v1.py",
    f"{snippets_folder}/guides/dagster/development_to_production/repository/repository_v2.py",
    f"{snippets_folder}/guides/dagster/development_to_production/repository/repository_v3.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/sda_graph.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/sda_io_manager.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/sda_nothing.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/vanilla_graph.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/vanilla_io_manager.py",
    f"{snippets_folder}/guides/dagster/enriching_with_software_defined_assets/vanilla_nothing.py",
    f"{snippets_folder}/guides/dagster/using_environment_variables_and_secrets/repository.py",
    f"{snippets_folder}/guides/dagster/using_environment_variables_and_secrets/repository_v2.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/downstream_asset.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/downstream_asset_script.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/new_code.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/old_code.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/upstream_asset.py",
    f"{snippets_folder}/guides/migrations/from_step_launchers_to_pipes/upstream_asset_script.py",
    f"{snippets_folder}/guides/etl/transform-dbt/dbt_definitions.py",
    f"{snippets_folder}/guides/etl/transform-dbt/dbt_definitions_with_downstream.py",
    f"{snippets_folder}/guides/etl/transform-dbt/dbt_definitions_with_schedule.py",
    f"{snippets_folder}/guides/etl/transform-dbt/dbt_definitions_with_upstream.py",
    f"{snippets_folder}/intro_tutorial/basics/testing/test_complex_job.py",
    f"{snippets_folder}/legacy/dagster_pandas_guide/repository.py",
    f"{snippets_folder}/tutorial/building_an_asset_graph/asset_with_logger.py",
    f"{snippets_folder}/tutorial/building_an_asset_graph/assets_with_metadata.py",
    f"{snippets_folder}/tutorial/connecting/assets.py",
    f"{snippets_folder}/tutorial/connecting/connecting.py",
    f"{snippets_folder}/tutorial/connecting/connecting_with_config.py",
    f"{snippets_folder}/tutorial/connecting/connecting_with_envvar.py",
    f"{snippets_folder}/tutorial/scheduling/with_schedule/with_schedule.py",
}
EXCLUDED_DIRS = {
    # integrations are excluded because they have external dependencies that are easier to manage in
    # a separate tox environment
    f"{snippets_folder}/integrations",
}


def get_python_files(directory):
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in EXCLUDED_DIRS]

        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


@pytest.mark.parametrize("file_path", get_python_files(snippets_folder))
def test_file_loads(file_path):
    if file_path in EXCLUDED_FILES:
        pytest.skip(f"Skipped {file_path}")
        return
    spec = importlib.util.spec_from_file_location("module", file_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to load {file_path}: {e!s}")
