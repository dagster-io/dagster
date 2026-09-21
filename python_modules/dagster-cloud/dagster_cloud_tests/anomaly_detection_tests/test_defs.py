import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from dagster import define_asset_job
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata import JsonMetadataValue, MetadataValue, TextMetadataValue
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.test_utils import freeze_time, instance_for_test
from dagster._time import create_datetime, get_current_datetime
from dagster_cloud.anomaly_detection.defs import (
    DagsterCloudAnomalyDetectionFailed,
    build_anomaly_detection_freshness_checks,
)
from dagster_cloud.anomaly_detection.types import BetaFreshnessAnomalyDetectionParams


@pytest.fixture
def mock_gql_client_execute():
    with patch(
        "dagster_cloud_cli.core.graphql_client.DagsterCloudGraphQLClient.execute"
    ) as mock_client_execute:
        yield mock_client_execute


@pytest.fixture
def mock_agent_params():
    with patch(
        "dagster._core.instance.DagsterInstance.dagit_url", create=True, new_callable=PropertyMock
    ) as mock_dagit_url:
        mock_dagit_url.return_value = "http://localhost:3000"
        with patch(
            "dagster._core.instance.DagsterInstance.dagster_cloud_agent_token",
            create=True,
            new_callable=PropertyMock,
        ) as mock_agent_token:
            mock_agent_token.return_value = "fake_token"
            yield None


@asset(key_prefix="bar")
def foo_asset():
    pass


foo_src = foo_asset.to_source_asset()


@pytest.mark.parametrize(
    "targeted_asset",
    [
        foo_src,
        foo_asset,
    ],
    ids=["source_asset", "asset"],
)
@pytest.mark.parametrize(
    "params",
    [None, BetaFreshnessAnomalyDetectionParams(sensitivity=0.2)],
)
def test_anomaly_detection_freshness_checks_builder(
    mock_gql_client_execute: MagicMock,
    mock_agent_params: None,
    params: BetaFreshnessAnomalyDetectionParams | None,
    targeted_asset: SourceAsset | AssetsDefinition,
) -> None:
    check = build_anomaly_detection_freshness_checks(
        assets=[targeted_asset],
        params=params,
    )[0]
    assert isinstance(check, AssetChecksDefinition)
    assert check.node_def.name.startswith("anomaly_detection_freshness_check_")
    check_job = define_asset_job("check_job", selection=AssetSelection.all_asset_checks())
    defs = Definitions(
        assets=[targeted_asset],
        asset_checks=[check],
        jobs=[check_job],  # We run checks independently of the underlying asset.
    )
    job_def = defs.resolve_job_def(check_job.name)

    with instance_for_test() as instance:
        # Valid output from the gql query
        mock_gql_client_execute.return_value = {
            "data": {
                "anomalyDetectionInference": {
                    "__typename": "AnomalyDetectionSuccess",
                    "response": {
                        "last_updated_timestamp": create_datetime(
                            2020, 3, 5, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "evaluation_timestamp": create_datetime(
                            2020, 3, 5, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "last_update_time_lower_bound": create_datetime(
                            2020, 3, 4, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "maximum_acceptable_delta": 1.0,
                        "model_training_range_start_timestamp": create_datetime(
                            2020, 3, 1, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "model_training_range_end_timestamp": create_datetime(
                            2020, 3, 5, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                    },
                }
            }
        }
        result = job_def.execute_in_process(instance=instance)
        assert result.success
        evaluations = result.get_asset_check_evaluations()
        assert len(evaluations) == 1
        assert evaluations[0].passed
        assert {key: val for key, val in evaluations[0].metadata.items()} == {
            "dagster/anomaly_detection_model_params": JsonMetadataValue(
                {
                    "sensitivity": 0.1 if params is None else params.sensitivity,
                }
            ),
            "dagster/anomaly_detection_model_version": TextMetadataValue("FRESHNESS_BETA"),
            "dagster/anomaly_detection_model_training_range_start_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 1, 0, 0, 0, tz="UTC")
            ),
            "dagster/anomaly_detection_model_training_range_end_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 5, 0, 0, 0, tz="UTC")
            ),
            "dagster/last_updated_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 5, 0, 0, 0, tz="UTC")
            ),
            "dagster/freshness_lower_bound_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 4, 0, 0, 0, tz="UTC")
            ),
            "dagster/fresh_until_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 5, 0, 0, 1, tz="UTC")
            ),
        }
        mock_gql_client_execute.assert_called_once()
        _, gql_params = mock_gql_client_execute.call_args.args
        assert gql_params["modelVersion"] == "FRESHNESS_BETA"
        assert gql_params["params"]["sensitivity"] == 0.1 if params is None else params.sensitivity
        assert gql_params["params"]["asset_key_user_string"] == "bar/foo_asset"

        # Valid overdue output from the gql query
        mock_gql_client_execute.return_value = {
            "data": {
                "anomalyDetectionInference": {
                    "__typename": "AnomalyDetectionSuccess",
                    "response": {
                        "last_updated_timestamp": create_datetime(
                            2020, 3, 1, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "evaluation_timestamp": create_datetime(
                            2020, 3, 1, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "last_update_time_lower_bound": create_datetime(
                            2020, 3, 5, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "maximum_acceptable_delta": 1.0,
                        "model_training_range_start_timestamp": create_datetime(
                            2020, 3, 1, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                        "model_training_range_end_timestamp": create_datetime(
                            2020, 3, 1, 0, 0, 0, tz="UTC"
                        ).timestamp(),
                    },
                }
            }
        }

        result = job_def.execute_in_process(instance=instance)
        assert result.success
        evaluations = result.get_asset_check_evaluations()
        assert len(evaluations) == 1
        assert not evaluations[0].passed
        assert {key: val for key, val in evaluations[0].metadata.items()} == {
            "dagster/anomaly_detection_model_params": JsonMetadataValue(
                {
                    "sensitivity": 0.1 if params is None else params.sensitivity,
                }
            ),
            "dagster/anomaly_detection_model_version": TextMetadataValue("FRESHNESS_BETA"),
            "dagster/anomaly_detection_model_training_range_start_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 1, 0, 0, 0, tz="UTC")
            ),
            "dagster/anomaly_detection_model_training_range_end_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 1, 0, 0, 0, tz="UTC")
            ),
            "dagster/last_updated_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 1, 0, 0, 0, tz="UTC")
            ),
            "dagster/freshness_lower_bound_timestamp": MetadataValue.timestamp(
                create_datetime(2020, 3, 5, 0, 0, 0, tz="UTC")
            ),
        }
        assert evaluations[0].severity == AssetCheckSeverity.WARN

        _, gql_params = mock_gql_client_execute.call_args.args
        assert gql_params["modelVersion"] == "FRESHNESS_BETA"
        assert gql_params["params"]["sensitivity"] == 0.1 if params is None else params.sensitivity
        assert gql_params["params"]["asset_key_user_string"] == "bar/foo_asset"

        # Graphql query failure
        mock_gql_client_execute.return_value = {
            "data": {
                "anomalyDetectionInference": {
                    "__typename": "AnomalyDetectionFailure",
                    "message": "Exception: Anomaly detection failed.",
                }
            }
        }
        with pytest.raises(DagsterCloudAnomalyDetectionFailed, match=r"Anomaly detection failed."):
            job_def.execute_in_process(instance=instance)

        # Not enough records
        mock_gql_client_execute.return_value = {
            "data": {
                "anomalyDetectionInference": {
                    "__typename": "AnomalyDetectionFailure",
                    "message": "Not enough records found to detect anomalies. Need at least 15.",
                }
            }
        }
        freeze_datetime = get_current_datetime()
        with freeze_time(freeze_datetime):
            result = job_def.execute_in_process(instance=instance)
            assert result.success
            evaluations = result.get_asset_check_evaluations()
            assert len(evaluations) == 1
            assert evaluations[0].passed
            assert evaluations[0].severity == AssetCheckSeverity.WARN
            assert (
                evaluations[0].description
                == "Anomaly detection failed: Not enough records found to detect anomalies. Need at "
                "least 15. Any sensors will wait to re-evaluate this check for a day."
            )
            assert evaluations[0].metadata[
                "dagster/fresh_until_timestamp"
            ] == MetadataValue.timestamp(freeze_datetime + datetime.timedelta(days=1))
