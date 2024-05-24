import {Colors, Icon, IconName} from '@dagster-io/ui-components';
import {memo} from 'react';

import {DaggyMetricIcon} from './DaggyMetricIcon';
import {InsightsIcon, InsightsIconType} from './InsightsIcon';

export const IconForMetricName = memo(
  ({
    metricName,
    pending,
    customIcon,
  }: {
    metricName: string;
    pending?: boolean;
    customIcon?: InsightsIconType;
  }) => {
    if (customIcon) {
      return <InsightsIcon name={customIcon} />;
    }
    switch (metricName) {
      case '__dagster_dagster_credits':
        return <DaggyMetricIcon />;
      default:
        return (
          <Icon
            name={iconNameForMetric(metricName)}
            color={!!pending ? Colors.textLighter() : undefined}
          />
        );
    }
  },
);

export const iconNameForMetric = (metricName: string): IconName => {
  switch (metricName) {
    case '__dagster_materializations':
      return 'materialization';
    case '__dagster_observations':
      return 'observation';
    case '__dagster_step_retry_duration':
    case '__dagster_run_duration_ms':
      return 'timer';
    case '__dagster_execution_time_ms':
      return 'waterfall_chart';
    case '__dagster_step_failures':
      return 'error_outline';
    case '__dagster_step_retries':
      return 'cached';
    default:
      return 'bar_chart';
  }
};
