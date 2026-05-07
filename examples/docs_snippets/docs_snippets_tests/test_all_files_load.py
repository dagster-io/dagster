import importlib.util
import os
from collections.abc import Generator
from typing import Any

import pytest

import dagster as dg

snippets_folder = dg.file_relative_path(__file__, "../docs_snippets/")

EXCLUDED_FILES = {
    # TEMPORARY: dagster-cloud environment is weird and confusing
    f"{snippets_folder}/guides/build/assets/data-assets/quality-testing/freshness-checks/anomaly-detection.py",
    f"{snippets_folder}/guides/build/assets/metadata/plus-references.py",
    f"{snippets_folder}/guides/observe/insights/snowflake/snowflake-dbt-asset-insights.py",
    f"{snippets_folder}/guides/observe/insights/snowflake/snowflake-resource-insights.py",
    f"{snippets_folder}/guides/observe/insights/google-bigquery/bigquery-resource-insights.py",
    # see DOC-375
    f"{snippets_folder}/guides/build/assets/asset-factories/python-asset-factory.py",
    f"{snippets_folder}/guides/build/assets/asset-factories/simple-yaml-asset-factory.py",
    f"{snippets_folder}/guides/build/assets/asset-factories/advanced-yaml-asset-factory.py",
    # setuptools.setup() eventually parses the command line that caused setup() to be called.
    # it errors because the command line for this test is for pytest and doesn't align with the arguments
    # setup() expects. So omit files that call setup() since they cannot be loaded without errors.
    f"{snippets_folder}/deployment/dagster_plus/serverless/runtime-environment/data_files_setup.py",
    f"{snippets_folder}/deployment/dagster_plus/serverless/runtime-environment/example_setup.py",
    f"{snippets_folder}/deployment/dagster_plus/serverless/runtime-environment/example_tarball_setup.py",
    # there are no components defined in the snippets and so it would fail to load
    f"{snippets_folder}/guides/components/existing-project/definitions-after.py",
    # there are no components defined in the snippets and so it would fail to load
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
    f"{snippets_folder}/guides/dg/migrating-project/13-initial-definitions.py",
    f"{snippets_folder}/guides/dg/migrating-project/14-updated-definitions.py",
    f"{snippets_folder}/guides/dg/using-resources/1-asset-one.py",
    f"{snippets_folder}/guides/dg/using-resources/2-resources-at-defs-root.py",
    f"{snippets_folder}/guides/dg/using-resources/3-resource-defs-at-project-root.py",
    f"{snippets_folder}/guides/dg/adding-components-to-existing-project/2-definitions-before.py",
    f"{snippets_folder}/guides/dg/adding-components-to-existing-project/6-definitions.py",
    f"{snippets_folder}/guides/components/integrations/dlt-component/5-loads.py",
    f"{snippets_folder}/guides/components/integrations/dlt-component/7-customized-loads.py",
    # resources are defined in a separate file so import references are failing tests
    f"{snippets_folder}/guides/operate/configuration/env_vars_and_secrets/assets.py",
    f"{snippets_folder}/guides/operate/configuration/run_config/asset_example/assets.py",
    f"{snippets_folder}/guides/operate/configuration/run_config/op_example/ops.py",
    f"{snippets_folder}/guides/operate/configuration/run_config/providing_config_values/assets.py",
    f"{snippets_folder}/guides/operate/configuration/run_config/using_env_vars/assets.py",
    f"{snippets_folder}/guides/operate/configuration/run_config/validation/assets.py",
    # migrated from legacy `docs_snippets/`
    f"{snippets_folder}/guides/build/assets/asset_group_module.py",
    f"{snippets_folder}/guides/build/assets/asset_input_managers_numpy.py",
    f"{snippets_folder}/guides/build/assets/subset_graph_backed_asset_unexpected_materializations.py",
    f"{snippets_folder}/guides/automate/declarative_automation/allow_missing_upstreams.py",
    f"{snippets_folder}/guides/build/io_management/input_managers.py",
    f"{snippets_folder}/guides/build/io_management/loading_multiple_upstream_partitions.py",
    f"{snippets_folder}/guides/build/ops_jobs_graphs/nested_graphs.py",
    f"{snippets_folder}/guides/build/partitions_backfills/schedule_from_partitions.py",
    f"{snippets_folder}/guides/automate/schedules/schedule_examples.py",
    f"{snippets_folder}/api/graphql/client_example.py",
    f"{snippets_folder}/integrations/dbt/with_dbt_code_references.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/azure/azureml_job/train.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/azure/azureml_job/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/custom_bootstrap_loader.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/custom_context_injector.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/custom_context_loader.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/custom_message_reader.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/custom_message_writer.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/session_lifecycle_external.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/dagster_pipes_details_and_customization/session_lifecycle_orchestration.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/databricks/databricks_asset_client.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/ecs/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/emr-containers/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/emr-serverless/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/emr/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/gcp/dataproc_job/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/gcp/dataproc_job/upload_artifacts.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/glue/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/lambda/dagster_code.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/json_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/markdown_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/notebook_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/path_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/table_column_lineage.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/table_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/table_schema_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/timestamp_metadata.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/subprocess/rich_metadata/url_metadata.py",
    f"{snippets_folder}/deployment/dagster_plus/deploying_code/branch_deployments/dev_to_prod/repository_v1.py",
    f"{snippets_folder}/deployment/dagster_plus/deploying_code/branch_deployments/dev_to_prod/repository_v2.py",
    f"{snippets_folder}/deployment/dagster_plus/deploying_code/branch_deployments/dev_to_prod/repository_v3.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/downstream_asset.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/downstream_asset_script.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/new_code.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/old_code.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/upstream_asset.py",
    f"{snippets_folder}/migration/from_step_launchers_to_pipes/upstream_asset_script.py",
    f"{snippets_folder}/integrations/external_pipelines/dagster_pipes/databricks/resources.py",
    f"{snippets_folder}/integrations/external_pipelines/spark_connect/databricks_resources.py",
    f"{snippets_folder}/about/contributing-docs/highlight.py",
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
def test_file_loads(file_path: Generator[Any, Any, None]):
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
