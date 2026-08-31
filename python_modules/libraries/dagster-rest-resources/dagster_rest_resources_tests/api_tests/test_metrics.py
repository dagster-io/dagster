from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import (
    MetricsStoreType,
    ReportingMetricsGranularity,
    ReportingUnitType,
)
from dagster_rest_resources.__generated__.get_asset_metrics import (
    GetAssetMetrics,
    GetAssetMetricsReportingMetricsByAssetReportingMetrics,
    GetAssetMetricsReportingMetricsByAssetReportingMetricsMetrics,
    GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsAggregateValueChange,
    GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsEntityReportingAsset,
    GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsEntityReportingAssetAssetKey,
    GetAssetMetricsReportingMetricsByAssetUnauthorizedError,
)
from dagster_rest_resources.__generated__.list_asset_metric_types import (
    ListAssetMetricTypes,
    ListAssetMetricTypesMetricTypesForAssetMetricTypeList,
    ListAssetMetricTypesMetricTypesForAssetMetricTypeListMetricTypes,
)
from dagster_rest_resources.api.metrics import DgApiMetricsApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


def _metric_type_list() -> ListAssetMetricTypes:
    return ListAssetMetricTypes(
        metricTypesForAsset=ListAssetMetricTypesMetricTypesForAssetMetricTypeList(
            __typename="MetricTypeList",
            id="types",
            metricTypes=[
                ListAssetMetricTypesMetricTypesForAssetMetricTypeListMetricTypes(
                    id="m1",
                    metricName="__dagster_dagster_credits",
                    displayName="Dagster credits",
                    category="cost",
                    unitType=ReportingUnitType.FLOAT,
                    description="credits used",
                    pending=False,
                    visible=True,
                    customIcon=None,
                    costMultiplier=1.0,
                )
            ],
        )
    )


class TestListAssetMetricTypes:
    def test_unnarrowed_request_uses_the_general_query(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_metric_types.return_value = _metric_type_list()

        result = DgApiMetricsApi(_client=client).list_asset_metric_types()

        assert result.total == 1
        assert result.items[0].metric_name == "__dagster_dagster_credits"
        client.list_asset_metric_types.assert_called_once_with(
            metrics_store_type=MetricsStoreType.VICTORIA_METRICS
        )
        client.list_specific_asset_metric_types.assert_not_called()

    def test_narrowing_by_asset_key_uses_the_specific_query(self):
        client = Mock(spec=IGraphQLClient)
        client.list_specific_asset_metric_types.return_value = Mock(
            metric_types_for_specific_asset=_metric_type_list().metric_types_for_asset
        )

        DgApiMetricsApi(_client=client).list_asset_metric_types(
            asset_keys=[["warehouse", "orders"]], after=1.0, before=2.0
        )

        client.list_asset_metric_types.assert_not_called()
        kwargs = client.list_specific_asset_metric_types.call_args.kwargs
        assert kwargs["metrics_filter"].assets[0].asset_key.path == ["warehouse", "orders"]
        assert kwargs["timeframe_selector"].after == 1.0
        assert kwargs["timeframe_selector"].before == 2.0

    def test_a_timeframe_alone_narrows_the_request(self):
        client = Mock(spec=IGraphQLClient)
        client.list_specific_asset_metric_types.return_value = Mock(
            metric_types_for_specific_asset=_metric_type_list().metric_types_for_asset
        )

        DgApiMetricsApi(_client=client).list_asset_metric_types(after=1.0)

        client.list_asset_metric_types.assert_not_called()


class TestGetAssetMetrics:
    def test_returns_entries_and_timestamps(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_metrics.return_value = GetAssetMetrics(
            reportingMetricsByAsset=GetAssetMetricsReportingMetricsByAssetReportingMetrics(
                __typename="ReportingMetrics",
                metrics=[
                    GetAssetMetricsReportingMetricsByAssetReportingMetricsMetrics(
                        entity=GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsEntityReportingAsset(
                            __typename="ReportingAsset",
                            assetKey=GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsEntityReportingAssetAssetKey(
                                path=["warehouse", "orders"]
                            ),
                            assetGroup="warehouse",
                            codeLocationName="loc",
                            repositoryName="repo",
                        ),
                        aggregateValue=12.5,
                        aggregateValueChange=GetAssetMetricsReportingMetricsByAssetReportingMetricsMetricsAggregateValueChange(
                            change=0.25, isNewlyAvailable=False
                        ),
                        values=[4.0, None, 8.5],
                    )
                ],
                timestamps=[1.0, 2.0, 3.0],
            )
        )

        result = DgApiMetricsApi(_client=client).get_asset_metrics(
            metric_name="__dagster_dagster_credits", after=1.0, before=3.0
        )

        assert result.timestamps == [1.0, 2.0, 3.0]
        entry = result.items[0]
        assert entry.aggregate_value == 12.5
        assert entry.aggregate_value_change.change == 0.25
        # gaps in the series are preserved rather than dropped, so values lines up with timestamps
        assert entry.values == [4.0, None, 8.5]
        # the entity comes through as the shape graphql returned
        assert entry.entity["assetKey"] == {"path": ["warehouse", "orders"]}
        assert entry.entity["__typename"] == "ReportingAsset"

        selector = client.get_asset_metrics.call_args.kwargs["metrics_selector"]
        assert selector.granularity == ReportingMetricsGranularity.DAILY

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_asset_metrics.return_value = GetAssetMetrics(
            reportingMetricsByAsset=GetAssetMetricsReportingMetricsByAssetUnauthorizedError(
                __typename="UnauthorizedError", message="nope"
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching asset metrics"):
            DgApiMetricsApi(_client=client).get_asset_metrics(
                metric_name="m", after=1.0, before=2.0
            )


class TestGetAssetSelectionMetrics:
    def test_requires_a_selection_or_keys(self):
        client = Mock(spec=IGraphQLClient)

        with pytest.raises(DagsterPlusGraphqlError, match="asset_selection or asset_keys"):
            DgApiMetricsApi(_client=client).get_asset_selection_metrics(
                metric_name="m", after=1.0, before=2.0
            )

        client.get_asset_selection_metrics.assert_not_called()
