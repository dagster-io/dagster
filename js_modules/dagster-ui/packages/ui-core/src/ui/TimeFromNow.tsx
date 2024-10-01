import {Tooltip} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import {memo} from 'react';

import {Timestamp} from '../app/time/Timestamp';

dayjs.extend(relativeTime);
const TIME_FORMAT = {showSeconds: true, showTimezone: true};

interface Props {
  unixTimestamp: number;
  showTooltip?: boolean;
}

export const TimeFromNow = memo(({unixTimestamp, showTooltip = true}: Props) => {
  const value = dayjs(unixTimestamp * 1000).fromNow();
  return showTooltip ? (
    <Tooltip
      placement="top"
      content={<Timestamp timestamp={{unix: unixTimestamp}} timeFormat={TIME_FORMAT} />}
    >
      {value}
    </Tooltip>
  ) : (
    <span>{value}</span>
  );
});
