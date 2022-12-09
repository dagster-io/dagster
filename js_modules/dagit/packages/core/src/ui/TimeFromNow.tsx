import {Tooltip} from '@dagster-io/ui';
import moment from 'moment-timezone';
import * as React from 'react';

import {Timestamp} from '../app/time/Timestamp';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

export const TimeFromNow: React.FC<{unixTimestamp: number}> = ({unixTimestamp}) => {
  return (
    <Tooltip
      placement="top"
      content={<Timestamp timestamp={{unix: unixTimestamp}} timeFormat={TIME_FORMAT} />}
    >
      {moment.unix(unixTimestamp).fromNow()}
    </Tooltip>
  );
};
