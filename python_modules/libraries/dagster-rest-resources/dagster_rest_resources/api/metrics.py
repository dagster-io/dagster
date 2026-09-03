from dataclasses import dataclass
from typing import Any

from dagster_rest_resources.__generated__.enums import (
    MetricsStoreType,
    ReportingAggregationFunction,
    ReportingMetricsGranularity,
    ReportingSortDirection,
    ReportingSortTarget,
)
from dagster_rest_resources.__generated__.input_types import (
    AssetKeyInput,
    AssetReportingMetricsFilter,
    AssetSelectionReportingMetricsFilter,
    DeploymentReportingMetricsFilter,
    JobReportingMetricsFilter,
    QualifiedAssetKey,
    QualifiedJob,
    ReportingMetricsSelector,
    ReportingMetricsTimeframeSelector,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusClientError,
    DagsterPlusServerError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.metrics import (
    DgApiMetricEntry,
    DgApiMetrics,
    DgApiMetricType,
    DgApiMetricTypeList,
    DgApiMetricValueChange,
)

# insights metrics are only served from the victoria metrics store
_METRICS_STORE = MetricsStoreType.VICTORIA_METRICS


def _build_metric_types(result: Any, operation: str) -> DgApiMetricTypeList:
    match result.typename__:
        case "MetricTypeList":
            return DgApiMetricTypeList(
                items=[
                    DgApiMetricType(
                        id=t.id,
                        metric_name=t.metric_name,
                        display_name=t.display_name,
                        category=t.category,
                        unit_type=t.unit_type,
                        description=t.description,
                        pending=t.pending,
                        visible=t.visible,
                        custom_icon=t.custom_icon,
                        cost_multiplier=t.cost_multiplier,
                    )
                    for t in result.metric_types
                ]
            )
        case "UnauthorizedError":
            raise DagsterPlusUnauthorizedError(f"Error {operation}: {result.message}")
        case "PythonError":
            raise DagsterPlusServerError(f"Error {operation}: {result.message}")
        case unexpected:
            raise DagsterPlusServerError(f"Error {operation}: unexpected result {unexpected}")


def _build_metrics(result: Any, operation: str) -> DgApiMetrics:
    match result.typename__:
        case "ReportingMetrics":
            return DgApiMetrics(
                items=[
                    DgApiMetricEntry(
                        entity=entry.entity.model_dump(by_alias=True),
                        aggregate_value=entry.aggregate_value,
                        aggregate_value_change=DgApiMetricValueChange(
                            change=entry.aggregate_value_change.change,
                            is_newly_available=entry.aggregate_value_change.is_newly_available,
                        ),
                        values=list(entry.values),
                    )
                    for entry in result.metrics
                    if entry is not None
                ],
                timestamps=list(result.timestamps),
            )
        case "UnauthorizedError":
            raise DagsterPlusUnauthorizedError(f"Error {operation}: {result.message}")
        case "ReportingInputError":
            raise DagsterPlusClientError(f"Invalid metrics request: {result.message}")
        case "PythonError":
            raise DagsterPlusServerError(f"Error {operation}: {result.message}")
        case unexpected:
            raise DagsterPlusServerError(f"Error {operation}: unexpected result {unexpected}")


def _selector(
    *,
    metric_name: str,
    after: float,
    before: float,
    granularity: ReportingMetricsGranularity,
    aggregation_function: ReportingAggregationFunction | None,
    sort_targets: list[ReportingSortTarget] | None,
    sort_directions: list[ReportingSortDirection] | None,
) -> ReportingMetricsSelector:
    return ReportingMetricsSelector(
        metricName=metric_name,
        after=after,
        before=before,
        granularity=granularity,
        aggregationFunction=aggregation_function,
        sortTarget=sort_targets,
        sortDirection=sort_directions,
    )


def _timeframe(after: float | None, before: float | None) -> ReportingMetricsTimeframeSelector:
    return ReportingMetricsTimeframeSelector(after=after, before=before)


def _qualified_jobs(jobs: list[dict[str, str]] | None) -> list[QualifiedJob] | None:
    if not jobs:
        return None
    return [
        QualifiedJob(
            jobName=job.get("job_name"),
            repositoryName=job.get("repository_name"),
            codeLocationName=job.get("code_location_name"),
        )
        for job in jobs
    ]


def _asset_inputs(asset_keys: list[list[str]] | None) -> list[QualifiedAssetKey] | None:
    if not asset_keys:
        return None
    return [QualifiedAssetKey(assetKey=AssetKeyInput(path=key)) for key in asset_keys]


@dataclass(frozen=True)
class DgApiMetricsApi:
    """Insights metrics, one method per scope.

    The graphql api splits every read by scope (asset, job, deployment) and again by whether
    the request is narrowed to specific entities, which is why there are more queries here
    than methods.

    Asset keys are path components, as `[["marts", "dim_customers"]]`, because a single
    component may itself contain a slash and a joined form cannot be split back
    unambiguously.
    """

    _client: IGraphQLClient

    def list_asset_metric_types(
        self,
        after: float | None = None,
        before: float | None = None,
        asset_keys: list[list[str]] | None = None,
        asset_selection: str | None = None,
    ) -> DgApiMetricTypeList:
        narrowed = asset_keys or asset_selection or after is not None or before is not None
        if not narrowed:
            result = self._client.list_asset_metric_types(
                metrics_store_type=_METRICS_STORE
            ).metric_types_for_asset
            return _build_metric_types(result, "listing asset metric types")

        result = self._client.list_specific_asset_metric_types(
            metrics_filter=AssetReportingMetricsFilter(
                assets=_asset_inputs(asset_keys),
                assetSelection=asset_selection,
            ),
            timeframe_selector=_timeframe(after, before),
            metrics_store_type=_METRICS_STORE,
        ).metric_types_for_specific_asset
        return _build_metric_types(result, "listing asset metric types")

    def list_job_metric_types(
        self,
        after: float | None = None,
        before: float | None = None,
        jobs: list[dict[str, str]] | None = None,
    ) -> DgApiMetricTypeList:
        narrowed = jobs or after is not None or before is not None
        if not narrowed:
            result = self._client.list_job_metric_types(
                metrics_store_type=_METRICS_STORE
            ).metric_types_for_job
            return _build_metric_types(result, "listing job metric types")

        result = self._client.list_specific_job_metric_types(
            metrics_filter=JobReportingMetricsFilter(jobs=_qualified_jobs(jobs)),
            timeframe_selector=_timeframe(after, before),
            metrics_store_type=_METRICS_STORE,
        ).metric_types_for_specific_job
        return _build_metric_types(result, "listing job metric types")

    def list_deployment_metric_types(self) -> DgApiMetricTypeList:
        result = self._client.list_deployment_metric_types(
            metrics_store_type=_METRICS_STORE
        ).metric_types_for_deployment
        return _build_metric_types(result, "listing deployment metric types")

    def get_asset_metrics(
        self,
        metric_name: str,
        after: float,
        before: float,
        granularity: ReportingMetricsGranularity = ReportingMetricsGranularity.DAILY,
        aggregation_function: ReportingAggregationFunction | None = None,
        asset_keys: list[list[str]] | None = None,
        asset_selection: str | None = None,
        limit: int | None = None,
        sort_targets: list[ReportingSortTarget] | None = None,
        sort_directions: list[ReportingSortDirection] | None = None,
    ) -> DgApiMetrics:
        result = self._client.get_asset_metrics(
            metrics_filter=AssetReportingMetricsFilter(
                assets=_asset_inputs(asset_keys),
                assetSelection=asset_selection,
                limit=limit,
            ),
            metrics_selector=_selector(
                metric_name=metric_name,
                after=after,
                before=before,
                granularity=granularity,
                aggregation_function=aggregation_function,
                sort_targets=sort_targets,
                sort_directions=sort_directions,
            ),
            metrics_store_type=_METRICS_STORE,
        ).reporting_metrics_by_asset
        return _build_metrics(result, "fetching asset metrics")

    def get_job_metrics(
        self,
        metric_name: str,
        after: float,
        before: float,
        granularity: ReportingMetricsGranularity = ReportingMetricsGranularity.DAILY,
        aggregation_function: ReportingAggregationFunction | None = None,
        jobs: list[dict[str, str]] | None = None,
        limit: int | None = None,
        sort_targets: list[ReportingSortTarget] | None = None,
        sort_directions: list[ReportingSortDirection] | None = None,
    ) -> DgApiMetrics:
        result = self._client.get_job_metrics(
            metrics_filter=JobReportingMetricsFilter(jobs=_qualified_jobs(jobs), limit=limit),
            metrics_selector=_selector(
                metric_name=metric_name,
                after=after,
                before=before,
                granularity=granularity,
                aggregation_function=aggregation_function,
                sort_targets=sort_targets,
                sort_directions=sort_directions,
            ),
            metrics_store_type=_METRICS_STORE,
        ).reporting_metrics_by_job
        return _build_metrics(result, "fetching job metrics")

    def get_deployment_metrics(
        self,
        metric_name: str,
        after: float,
        before: float,
        granularity: ReportingMetricsGranularity = ReportingMetricsGranularity.DAILY,
        aggregation_function: ReportingAggregationFunction | None = None,
        deployment_ids: list[int] | None = None,
        limit: int | None = None,
        sort_targets: list[ReportingSortTarget] | None = None,
        sort_directions: list[ReportingSortDirection] | None = None,
    ) -> DgApiMetrics:
        result = self._client.get_deployment_metrics(
            metrics_filter=DeploymentReportingMetricsFilter(
                deploymentIds=deployment_ids,
                branchDeployments=False,
                limit=limit,
            ),
            metrics_selector=_selector(
                metric_name=metric_name,
                after=after,
                before=before,
                granularity=granularity,
                aggregation_function=aggregation_function,
                sort_targets=sort_targets,
                sort_directions=sort_directions,
            ),
            metrics_store_type=_METRICS_STORE,
        ).reporting_metrics_by_deployment
        return _build_metrics(result, "fetching deployment metrics")

    def get_asset_selection_metrics(
        self,
        metric_name: str,
        after: float,
        before: float,
        granularity: ReportingMetricsGranularity = ReportingMetricsGranularity.DAILY,
        aggregation_function: ReportingAggregationFunction | None = None,
        asset_keys: list[list[str]] | None = None,
        asset_selection: str | None = None,
    ) -> DgApiMetrics:
        if not asset_keys and not asset_selection:
            raise DagsterPlusClientError("An asset_selection or asset_keys is required.")

        result = self._client.get_asset_selection_metrics(
            metrics_filter=AssetSelectionReportingMetricsFilter(
                assetSelection=asset_selection,
                assetKeys=([AssetKeyInput(path=key) for key in asset_keys] if asset_keys else None),
            ),
            metrics_selector=_selector(
                metric_name=metric_name,
                after=after,
                before=before,
                granularity=granularity,
                aggregation_function=aggregation_function,
                sort_targets=None,
                sort_directions=None,
            ),
            metrics_store_type=_METRICS_STORE,
        ).reporting_metrics_by_asset_selection
        return _build_metrics(result, "fetching asset selection metrics")
