import datetime
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, cast

from dagster import (
    AssetCheckExecutionContext,
    MetadataValue,
    _check as check,
)
from dagster._core.definitions.asset_checks.asset_check_factories.freshness_checks.last_update import (
    construct_description,
)
from dagster._core.definitions.asset_checks.asset_check_factories.utils import (
    FRESH_UNTIL_METADATA_KEY,
    LAST_UPDATED_TIMESTAMP_METADATA_KEY,
    LOWER_BOUND_TIMESTAMP_METADATA_KEY,
    assets_to_keys,
)
from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
    AssetCheckSpec,
)
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.assets_definition import (
    AssetsDefinition,
    unique_id_from_asset_and_check_keys,
)
from dagster._core.definitions.decorators.asset_check_decorator import multi_asset_check
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterError, DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._time import get_current_timestamp
from dagster_cloud_cli.core.graphql_client import (
    DagsterCloudGraphQLClient,
    create_cloud_webserver_client,
)

from dagster_cloud.anomaly_detection.mutation import ANOMALY_DETECTION_INFERENCE_MUTATION
from dagster_cloud.anomaly_detection.types import (
    AnomalyDetectionModelParams,
    BetaFreshnessAnomalyDetectionParams,
    FreshnessAnomalyDetectionResult,
)

if TYPE_CHECKING:
    from dagster_cloud import DagsterCloudAgentInstance

DEFAULT_MODEL_PARAMS = BetaFreshnessAnomalyDetectionParams(sensitivity=0.1)
MODEL_PARAMS_METADATA_KEY = "dagster/anomaly_detection_model_params"
MODEL_VERSION_METADATA_KEY = "dagster/anomaly_detection_model_version"
MODEL_TRAINING_RANGE_START_TIMESTAMP_METADATA_KEY = (
    "dagster/anomaly_detection_model_training_range_start_timestamp"
)
MODEL_TRAINING_RANGE_END_TIMESTAMP_METADATA_KEY = (
    "dagster/anomaly_detection_model_training_range_end_timestamp"
)
MAXIMUM_ACCEPTABLE_DELTA_METADATA_KEY = "dagster/anomaly_detection_maximum_acceptable_delta"


class DagsterCloudAnomalyDetectionFailed(DagsterError):
    """Raised when an anomaly detection check fails host-side."""


def _build_check_for_assets(
    asset_keys: Sequence[AssetKey],
    params: AnomalyDetectionModelParams,
    severity: AssetCheckSeverity,
) -> AssetChecksDefinition:
    @multi_asset_check(
        specs=[
            AssetCheckSpec(
                name="anomaly_detection_freshness_check",
                description=f"Detects anomalies in the freshness of the asset using model {params.model_version.value.lower()}.",
                asset=asset_key,
                metadata={
                    MODEL_PARAMS_METADATA_KEY: params.as_metadata,
                    MODEL_VERSION_METADATA_KEY: params.model_version.value,
                },
            )
            for asset_key in asset_keys
        ],
        can_subset=True,
        name=f"anomaly_detection_freshness_check_{unique_id_from_asset_and_check_keys(asset_keys)}",
    )
    def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
        if not _is_agent_instance(context.instance):
            raise DagsterInvariantViolationError(
                f"This anomaly detection check is not being launched from a dagster agent. "
                "Anomaly detection is only available for dagster cloud deployments."
                f"Instance type: {type(context.instance)}."
            )
        instance = cast("DagsterCloudAgentInstance", context.instance)
        with create_cloud_webserver_client(
            instance.dagit_url[:-1]
            if instance.dagit_url.endswith("/")
            else instance.dagit_url,  # Remove trailing slash
            check.str_param(instance.dagster_cloud_agent_token, "dagster_cloud_agent_token"),
        ) as client:
            for check_key in context.selected_asset_check_keys:
                yield _anomaly_detection_inner(check_key, context, client, params, severity)

    return the_check


def handle_anomaly_detection_inference_failure(
    data: dict,
    metadata: dict,
    params: AnomalyDetectionModelParams,
    asset_key: AssetKey,
    severity: AssetCheckSeverity,
) -> AssetCheckResult:
    if (
        data["__typename"] == "AnomalyDetectionFailure"
        and data["message"] == params.model_version.minimum_required_records_msg
    ):
        # Pause evaluation for a day if there are not enough records.
        metadata[FRESH_UNTIL_METADATA_KEY] = MetadataValue.timestamp(
            get_current_timestamp() + datetime.timedelta(days=1).total_seconds()
        )
        description = (
            f"Anomaly detection failed: {data['message']} Any sensors will wait to "
            "re-evaluate this check for a day."
        )
        # Intercept failure in the case of not enough records, and return a pass to avoid
        # being too noisy with failures.
        return AssetCheckResult(
            passed=True,
            severity=severity,
            metadata=metadata,
            description=description,
            asset_key=asset_key,
        )
    raise DagsterCloudAnomalyDetectionFailed(f"Anomaly detection failed: {data['message']}")


def _anomaly_detection_inner(
    check_key: AssetCheckKey,
    context: AssetCheckExecutionContext,
    client: DagsterCloudGraphQLClient,
    params: AnomalyDetectionModelParams,
    severity: AssetCheckSeverity,
) -> AssetCheckResult:
    asset_key = check_key.asset_key
    if not context.job_def.asset_layer.asset_graph.has(asset_key):
        raise Exception(f"Could not find targeted asset {asset_key.to_string()}.")
    result = client.execute(
        ANOMALY_DETECTION_INFERENCE_MUTATION,
        {
            "modelVersion": params.model_version.value,
            "params": {
                **dict(params),
                "asset_key_user_string": asset_key.to_user_string(),
            },
        },
    )
    data = result["data"]["anomalyDetectionInference"]
    metadata = {
        MODEL_PARAMS_METADATA_KEY: {**params.as_metadata},
        MODEL_VERSION_METADATA_KEY: params.model_version.value,
    }
    if data["__typename"] != "AnomalyDetectionSuccess":
        return handle_anomaly_detection_inference_failure(
            data, metadata, params, asset_key, severity
        )
    response = result["data"]["anomalyDetectionInference"]["response"]
    result_obj = FreshnessAnomalyDetectionResult(**response)
    metadata[MODEL_TRAINING_RANGE_START_TIMESTAMP_METADATA_KEY] = MetadataValue.timestamp(
        result_obj.model_training_range_start_timestamp
    )
    metadata[MODEL_TRAINING_RANGE_END_TIMESTAMP_METADATA_KEY] = MetadataValue.timestamp(
        result_obj.model_training_range_end_timestamp
    )
    metadata[LAST_UPDATED_TIMESTAMP_METADATA_KEY] = MetadataValue.timestamp(
        result_obj.last_updated_timestamp
    )
    metadata[LOWER_BOUND_TIMESTAMP_METADATA_KEY] = MetadataValue.timestamp(
        result_obj.last_update_time_lower_bound
    )
    passed = result_obj.last_update_time_lower_bound <= result_obj.last_updated_timestamp

    if passed:
        fresh_until = result_obj.last_updated_timestamp + result_obj.maximum_acceptable_delta
        metadata[FRESH_UNTIL_METADATA_KEY] = MetadataValue.timestamp(fresh_until)

    return AssetCheckResult(
        passed=passed,
        description=construct_description(
            passed=passed,
            last_update_time_lower_bound=result_obj.last_update_time_lower_bound,
            current_timestamp=result_obj.evaluation_timestamp,
            update_timestamp=result_obj.last_updated_timestamp,
        ),
        severity=AssetCheckSeverity.WARN,
        metadata=metadata,
        asset_key=asset_key,
    )


def build_anomaly_detection_freshness_checks(
    *,
    assets: Sequence[CoercibleToAssetKey | AssetsDefinition | SourceAsset],
    params: AnomalyDetectionModelParams | None,
    severity: AssetCheckSeverity = AssetCheckSeverity.WARN,
) -> Sequence[AssetChecksDefinition]:
    """Builds a list of asset checks which utilize anomaly detection algorithms to
    determine the freshness of data.

    Args:
        assets (Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]): The assets to construct checks for. For each passed in
            asset, there will be a corresponding constructed `AssetChecksDefinition`.
        params (AnomalyDetectionModelParams): The parameters to use for the model. The parameterization corresponds to the model used.
        severity (AssetCheckSeverity): The severity of the check. Defaults to `AssetCheckSeverity.WARN`.

    Returns:
        Sequence[AssetChecksDefinition]: `AssetChecksDefinition` objects which execute freshness checks
            for the provided assets.

    Examples:
        .. code-block:: python

            from dagster_cloud import build_anomaly_detection_freshness_checks, BetaFreshnessAnomalyDetectionParams

            checks_def = build_anomaly_detection_freshness_checks(
                assets=[AssetKey("foo_asset"), AssetKey("foo_asset")],
                params=BetaFreshnessAnomalyDetectionParams(sensitivity=0.1),
            )
    """
    params = check.opt_inst_param(
        params, "params", AnomalyDetectionModelParams, DEFAULT_MODEL_PARAMS
    )
    severity = check.inst_param(severity, "severity", AssetCheckSeverity)
    return [
        _build_check_for_assets(
            [asset_key for asset in assets for asset_key in assets_to_keys([asset])],
            params,
            severity,
        )
    ]


def _is_agent_instance(instance: DagsterInstance) -> bool:
    if hasattr(instance, "dagster_cloud_agent_token") and hasattr(instance, "dagit_url"):
        return True
    return False
