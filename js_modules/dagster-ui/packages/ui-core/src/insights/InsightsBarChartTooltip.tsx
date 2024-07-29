import {Box, Colors, Icon, MiddleTruncate} from '@dagster-io/ui-components';

import {TooltipCard, iconForDatapointType} from './InsightsChartShared';
import {InsightsIdentifierDot} from './InsightsIdentifierDot';
import {TOTAL_COST_FORMATTER} from './costFormatters';
import {formatMetric, stripFormattingFromNumber} from './formatMetric';
import {DatapointType, ReportingUnitType} from './types';
import {HourCycle} from '../app/time/HourCycle';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

interface Props {
  color: string;
  type: DatapointType;
  label: string;
  date: Date;
  timezone: string;
  hourCycle: HourCycle;
  formattedValue: string;
  unitType: ReportingUnitType;
  costMultiplier: number | null;
  metricLabel: string;
}

export const InsightsBarChartTooltip = (props: Props) => {
  const {
    color,
    type,
    label,
    date,
    timezone,
    hourCycle,
    formattedValue,
    unitType,
    metricLabel,
    costMultiplier,
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
          <TimestampDisplay
            timestamp={date.getTime() / 1000}
            timezone={timezone}
            hourCycle={hourCycle}
          />
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
