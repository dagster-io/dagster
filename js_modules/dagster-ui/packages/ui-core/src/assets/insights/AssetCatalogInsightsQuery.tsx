import {gql} from '@apollo/client';

import {INSIGHTS_ENTRY_FRAGMENT} from './InsightsEntryFragment';
import {METRIC_TYPE_FRAGMENT} from './MetricTypeFragment';
import {CLOUD_PYTHON_ERROR_FRAGMENT} from '../app/PythonError';

export const INSIGHTS_ASSETS_QUERY = gql`
  query InsightsAssetsQuery(
    $metricsFilter: AssetReportingMetricsFilter
    $metricsSelector: ReportingMetricsSelector!
  ) {
    reportingMetricsByAsset(metricsFilter: $metricsFilter, metricsSelector: $metricsSelector) {
      ... on ReportingMetrics {
        metrics {
          ...InsightsEntryFragment
        }
        timestamps
      }
    }
  }

  ${INSIGHTS_ENTRY_FRAGMENT}
`;
