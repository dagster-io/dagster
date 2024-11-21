import {Box, Colors} from '@dagster-io/ui-components';

import {TooltipCard} from '../../insights/InsightsChartShared';
import {formatMetric} from '../../insights/formatMetric';
import {ReportingUnitType} from '../../insights/types';

interface Props {
  dateTimeString: string;
  formattedValue: string;
  metricLabel: string;
}

export const AnimationBarChartTooltip = (props: Props) => {
  const {dateTimeString, formattedValue, metricLabel} = props;

  return (
    <TooltipCard>
      <Box padding={{vertical: 8, horizontal: 12}} flex={{direction: 'column', gap: 4}}>
        <div style={{fontWeight: 600, fontSize: '12px', color: Colors.textLight()}}>
          {dateTimeString}
        </div>
        <div style={{fontSize: '12px', color: Colors.textLight()}}>
          {metricLabel}:{' '}
          {formatMetric(formattedValue, ReportingUnitType.INTEGER, {
            floatPrecision: 'maximum-precision',
          })}
        </div>
      </Box>
    </TooltipCard>
  );
};
