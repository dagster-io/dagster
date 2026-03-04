import {Box, Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {HourCycle} from '../app/time/HourCycle';
import {TimeContext} from '../app/time/TimeContext';
import {
  DEFAULT_TIME_FORMAT,
  DEFAULT_TOOLTIP_TIME_FORMAT,
  TimeFormat,
} from '../app/time/TimestampFormat';
import {timestampToString} from '../app/time/timestampToString';

interface Props {
  timestamp: number;
  timezone?: string | null;
  timeFormat?: TimeFormat;
  hourCycle?: HourCycle | null;
  tooltipTimeFormat?: TimeFormat;
}

export const TimestampDisplay = (props: Props) => {
  const {
    timestamp,
    timezone,
    timeFormat = DEFAULT_TIME_FORMAT,
    hourCycle,
    tooltipTimeFormat = DEFAULT_TOOLTIP_TIME_FORMAT,
  } = props;
  const {
    resolvedTimezone: userTimezone,
    hourCycle: [userHourCycle],
  } = useContext(TimeContext);

  const locale = navigator.language;
  const mainString = timestampToString({
    timestamp: {unix: timestamp},
    locale,
    timezone: timezone || userTimezone,
    timeFormat,
    hourCycle: hourCycle || userHourCycle,
  });

  return (
    <Box
      style={{fontVariantNumeric: 'tabular-nums'}}
      flex={{display: 'inline-flex', alignItems: 'center', gap: 4}}
    >
      <div style={{minWidth: 0}} title={mainString}>
        {mainString}
      </div>
      {timezone && timezone !== userTimezone ? (
        <Tooltip
          placement="top"
          content={
            <div>
              {timestampToString({
                timestamp: {unix: timestamp},
                locale,
                timezone: userTimezone,
                timeFormat: tooltipTimeFormat,
              })}
            </div>
          }
        >
          <Icon name="schedule" color={Colors.textLight()} size={12} />
        </Tooltip>
      ) : null}
    </Box>
  );
};
