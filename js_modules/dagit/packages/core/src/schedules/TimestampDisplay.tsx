import {Box, Colors, Icon, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {DEFAULT_TIME_FORMAT, TimeFormat} from '../app/time/TimestampFormat';
import {TimezoneContext} from '../app/time/TimezoneContext';
import {timestampToString} from '../app/time/timestampToString';

interface Props {
  timestamp: number;
  timezone?: string | null;
  timeFormat?: TimeFormat;
  tooltipTimeFormat?: TimeFormat;
}

export const TimestampDisplay = (props: Props) => {
  const {timestamp, timezone, timeFormat, tooltipTimeFormat} = props;
  const [userTimezone] = React.useContext(TimezoneContext);
  const locale = navigator.language;

  return (
    <Box
      flex={{display: 'inline-flex', direction: 'row', alignItems: 'center', wrap: 'wrap', gap: 8}}
    >
      <TabularNums>
        {timestampToString({
          timestamp: {unix: timestamp},
          locale,
          timezone: timezone || userTimezone,
          timeFormat,
        })}
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
          <Icon name="schedule" color={Colors.Gray400} />
        </TimestampTooltip>
      ) : null}
    </Box>
  );
};

TimestampDisplay.defaultProps = {
  timeFormat: DEFAULT_TIME_FORMAT,
  tooltipTimeFormat: {showSeconds: false, showTimezone: true},
};

const TabularNums = styled.div`
  font-variant-numeric: tabular-nums;
`;

const TimestampTooltip = styled(Tooltip)`
  cursor: pointer;

  &.bp3-popover2-target {
    display: block;
  }
`;
