import importlib.util
import os

import pytest

import dagster as dg

snippets_folder = dg.file_relative_path(__file__, "../docs_snippets/integrations")

EXCLUDED_FILES = {
    # exclude community integrations because they require non-editable dagster depdendencies
    f"{snippets_folder}/cube.py",
    f"{snippets_folder}/hightouch.py",
    f"{snippets_folder}/hashicorp.py",
    f"{snippets_folder}/meltano.py",
    f"{snippets_folder}/lakefs.py",
    # FIXME: need to enable the following once we have a way to run their init/compile script in CI
    f"{snippets_folder}/dbt.py",
    f"{snippets_folder}/sdf.py",
    f"{snippets_folder}/airbyte.py",
    f"{snippets_folder}/dlt.py",
    f"{snippets_folder}/fivetran/customize_fivetran_asset_defs.py",
    f"{snippets_folder}/fivetran/customize_fivetran_translator_asset_spec.py",
    f"{snippets_folder}/fivetran/multiple_fivetran_workspaces.py",
    f"{snippets_folder}/fivetran/representing_fivetran_assets.py",
    f"{snippets_folder}/fivetran/select_fivetran_connectors.py",
    f"{snippets_folder}/fivetran/sync_and_materialize_fivetran_assets.py",
    f"{snippets_folder}/fivetran/fetch_column_metadata_fivetran_assets.py",
    f"{snippets_folder}/airbyte_cloud/customize_airbyte_cloud_asset_defs.py",
    f"{snippets_folder}/airbyte_cloud/customize_airbyte_cloud_translator_asset_spec.py",
    f"{snippets_folder}/airbyte_cloud/multiple_airbyte_cloud_workspaces.py",
    f"{snippets_folder}/airbyte_cloud/representing_airbyte_cloud_assets.py",
    f"{snippets_folder}/airbyte_cloud/sync_and_materialize_airbyte_cloud_assets.py",
    # FIXME: this breaks on py3.8 and seems related to the non-dagster dependencies
    f"{snippets_folder}/pandera.py",
    # FIXME: include tests
    f"{snippets_folder}/anthropic.py",
    f"{snippets_folder}/chroma.py",
    f"{snippets_folder}/gemini.py",
    f"{snippets_folder}/weaviate.py",
    f"{snippets_folder}/looker/asset_graph.py",
    f"{snippets_folder}/looker/asset_graph_filtered.py",
    f"{snippets_folder}/looker/asset_metadata.py",
    f"{snippets_folder}/looker/pdts.py",
    f"{snippets_folder}/qdrant.py",
    # migrated from original `docs_snippets/` directory
    f"{snippets_folder}/airflow/migrate_repo.py",
    f"{snippets_folder}/airflow/migrate_repo_connections.py",
    f"{snippets_folder}/airflow/operator.py",
    f"{snippets_folder}/airlift/equivalents/airflow_hook.py",
    f"{snippets_folder}/airlift/equivalents/airflow_task.py",
    f"{snippets_folder}/airlift/equivalents/dagster_partition.py",
    f"{snippets_folder}/airlift/equivalents/dagster_resource.py",
    f"{snippets_folder}/airlift/equivalents/factory_asset.py",
    f"{snippets_folder}/airlift/operator_migration/kubernetes_pod_operator.py",
    f"{snippets_folder}/airlift/operator_migration/pyop_asset_shared.py",
    f"{snippets_folder}/airlift/operator_migration/python_operator.py",
    f"{snippets_folder}/airlift/operator_migration/using_dbt_assets.py",
    f"{snippets_folder}/bigquery/tutorial/resource/downstream.py",
    f"{snippets_folder}/dbt/potemkin_dag_for_cover_image.py",
    f"{snippets_folder}/dbt/quickstart/with_project.py",
    f"{snippets_folder}/dbt/quickstart/with_single_file.py",
    f"{snippets_folder}/dbt/tutorial/downstream_assets/assets.py",
    f"{snippets_folder}/dbt/tutorial/downstream_assets/definitions.py",
    f"{snippets_folder}/dbt/tutorial/downstream_assets/project.py",
    f"{snippets_folder}/dbt/tutorial/load_dbt_models/assets.py",
    f"{snippets_folder}/dbt/tutorial/load_dbt_models/project.py",
    f"{snippets_folder}/dbt/tutorial/upstream_assets/assets.py",
    f"{snippets_folder}/dbt/tutorial/upstream_assets/definitions.py",
    f"{snippets_folder}/dbt/tutorial/upstream_assets/project.py",
    f"{snippets_folder}/deltalake/multi_partition.py",
    f"{snippets_folder}/dlt/dlt_dagster_translator.py",
    f"{snippets_folder}/dlt/dlt_partitions.py",
    f"{snippets_folder}/dlt/dlt_source_assets.py",
    f"{snippets_folder}/duckdb/reference/resource.py",
    f"{snippets_folder}/duckdb/tutorial/resource/downstream.py",
    f"{snippets_folder}/looker/customize-looker-assets.py",
    f"{snippets_folder}/looker/filtering-looker-assets.py",
    f"{snippets_folder}/looker/materializing-looker-pdts.py",
    f"{snippets_folder}/looker/representing-looker-assets.py",
    f"{snippets_folder}/power-bi/customize-power-bi-asset-defs.py",
    f"{snippets_folder}/power-bi/materialize-semantic-models-advanced.py",
    f"{snippets_folder}/power-bi/materialize-semantic-models.py",
    f"{snippets_folder}/power-bi/multiple-power-bi-workspaces.py",
    f"{snippets_folder}/power-bi/representing-power-bi-assets.py",
    f"{snippets_folder}/sigma/customize-sigma-asset-defs.py",
    f"{snippets_folder}/sigma/filtering-sigma-assets.py",
    f"{snippets_folder}/sigma/multiple-sigma-organizations.py",
    f"{snippets_folder}/sigma/representing-sigma-assets.py",
    f"{snippets_folder}/sling/sling_dagster_translator.py",
    f"{snippets_folder}/tableau/add-tableau-data-quality-warning.py",
    f"{snippets_folder}/tableau/customize-tableau-asset-defs.py",
    f"{snippets_folder}/tableau/materialize-tableau-assets-advanced.py",
    f"{snippets_folder}/tableau/multiple-tableau-workspaces.py",
    f"{snippets_folder}/tableau/refresh-and-materialize-tableau-assets.py",
    f"{snippets_folder}/tableau/representing-tableau-cloud-assets.py",
    f"{snippets_folder}/tableau/representing-tableau-server-assets.py",
}


def get_python_files(directory):
    for root, _, files in os.walk(directory):
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
