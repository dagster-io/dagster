from datetime import datetime

import pytest
from dagster import DagsterInstance, EnvVar
from dagster._core.definitions.observe import observe
from dagster_gcp.bigquery.assets import observe_table_factory
from dagster_gcp.bigquery.resources import BigQueryResource

from .conftest import IS_BUILDKITE, temporary_bigquery_table


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.integration
def test_observe_table_factory():
    dataset_name = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(schema_name=dataset_name, column_str="FOO string") as table_name:
        table_src_asset = observe_table_factory(dataset_name, table_name)
        instance = DagsterInstance.ephemeral()
        result = observe(
            [table_src_asset],
            instance=instance,
            resources={"bigquery": BigQueryResource(project=EnvVar("GCP_PROJECT_ID"))},
        )
        observations = result.asset_observations_for_node(table_src_asset.op.name)
        assert len(observations) == 1
        observation = observations[0]
        assert observation.tags["dagster/data_version"] is not None
        # Interpret the data version as a timestamp
        # Convert from a string in the format 2024-02-09 00:41:29.829000 to a timestamp
        timestamp = datetime.strptime(
            observation.tags["dagster/data_version"], "%Y-%m-%d %H:%M:%S.%f"
        )
        assert timestamp is not None
