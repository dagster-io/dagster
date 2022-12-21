import {Tooltip} from '@dagster-io/ui';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import * as React from 'react';

import {Timestamp} from '../app/time/Timestamp';

dayjs.extend(relativeTime);
const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const TimeFromNow: React.FC<{unixTimestamp: number}> = React.memo(({unixTimestamp}) => {
  return (
    <Tooltip
      placement="top"
      content={<Timestamp timestamp={{unix: unixTimestamp}} timeFormat={TIME_FORMAT} />}
    >
      {dayjs(unixTimestamp * 1000).fromNow()}
    </Tooltip>
  );
});
