import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {DEFAULT_TIME_FORMAT, TimeFormat} from '../app/time/TimestampFormat';
import {TimezoneContext} from '../app/time/TimezoneContext';
import {timestampToString} from '../app/time/timestampToString';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';

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
    <Group direction="row" spacing={8} alignItems="center" wrap="wrap">
      <TabularNums>
        {timestampToString({
          timestamp: {unix: timestamp},
          locale,
          timezone: timezone || userTimezone,
          timeFormat: timeFormat,
        })}
      </TabularNums>
      {timezone && timezone !== userTimezone ? (
        <TimestampTooltip
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
          <IconWIP name="schedule" color={ColorsWIP.Gray400} />
        </TimestampTooltip>
      ) : null}
    </Group>
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
