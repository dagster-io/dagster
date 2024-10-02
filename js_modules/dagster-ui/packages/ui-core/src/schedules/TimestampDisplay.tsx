import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';
import styled from 'styled-components';

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
    timezone: [userTimezone],
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
    <span>
      <TabularNums style={{minWidth: 0}} title={mainString}>
        {mainString}
      </TabularNums>
      {timezone && timezone !== userTimezone ? (
        <TimestampTooltip
          placement="top"
          content={
            <TabularNums>
              {timestampToString({
                timestamp: {unix: timestamp},
                locale,
                timezone: userTimezone,
                timeFormat: tooltipTimeFormat,
              })}
            </TabularNums>
          }
        >
          <Icon name="schedule" color={Colors.textLight()} size={12} />
        </TimestampTooltip>
      ) : null}
    </span>
  );
};

const TabularNums = styled.span`
  font-variant-numeric: tabular-nums;
`;

const TimestampTooltip = styled(Tooltip)`
  cursor: pointer;
  position: relative;
  top: 2px;
  margin-left: 4px;
`;
