import {Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';

import {DateRangeText} from './DateRangeText';
import {TooltipCard, iconForDatapointType} from './InsightsChartShared';
import {InsightsIdentifierDot} from './InsightsIdentifierDot';
import {TOTAL_COST_FORMATTER} from './costFormatters';
import {formatMetric, stripFormattingFromNumber} from './formatMetric';
import {DatapointType, ReportingMetricsGranularity, ReportingUnitType} from './types';

interface Props {
  color: string;
  type: DatapointType;
  label: string;
  date: Date;
  formattedValue: string;
  unitType: ReportingUnitType;
  costMultiplier: number | null;
  granularity: ReportingMetricsGranularity;
  metricLabel: string;
}

export const InsightsLineChartTooltip = (props: Props) => {
  const {
    color,
    type,
    label,
    date,
    formattedValue,
    unitType,
    costMultiplier,
    granularity,
    metricLabel,
  } = props;

  return (
    <TooltipCard>
      <Box
        padding={{vertical: 8, horizontal: 12}}
        border="bottom"
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
      >
        <InsightsIdentifierDot $color={color} key={label} />
        <Icon name={iconForDatapointType(type)} />
        <div style={{whiteSpace: 'nowrap', overflow: 'hidden', fontWeight: 600, fontSize: '14px'}}>
          <MiddleTruncate text={label} />
        </div>
      </Box>
      <Box padding={{vertical: 8, horizontal: 12}} flex={{direction: 'column', gap: 4}}>
        <div style={{fontWeight: 600, fontSize: '12px', color: Colors.textLight()}}>
          <DateRangeText date={date} granularity={granularity} />
        </div>
        <div style={{fontSize: '12px', color: Colors.textLight()}}>
          {metricLabel}:{' '}
          {formatMetric(formattedValue, unitType, {
            floatPrecision: 'maximum-precision',
          })}
        </div>
        {costMultiplier ? (
          <div style={{fontSize: '12px', color: Colors.textLight()}}>
            Estimated cost:{' '}
            {TOTAL_COST_FORMATTER.format(
              costMultiplier * stripFormattingFromNumber(formattedValue),
            )}
          </div>
        ) : null}
      </Box>
    </TooltipCard>
  );
};
