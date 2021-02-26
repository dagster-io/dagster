import moment from 'moment-timezone';
import * as React from 'react';

import {TimezoneContext} from 'src/app/time/TimezoneContext';
import {browserTimezone} from 'src/app/time/browserTimezone';

type TimestampProps = ({ms: number} | {unix: number}) & {
  format?: string;
};

const defaultTimeFormat = (m: moment.Moment, timezone: string) => {
  if (timezone === 'UTC') {
    return 'YYYY-MM-DD HH:mm';
  }

  const now = moment(Date.now());
  if (timezone !== 'Automatic') {
    now.tz(timezone);
  }

  return m.year() === now.year() ? 'MMM D, h:mm A' : 'MMM D, YYYY, h:mm A';
};

// This helper is here so that we can swap out Moment in the future as needed and
// encourage use of the same default format string across the app.
export const timestampToString = (time: TimestampProps, timezone: string) => {
  let m = 'ms' in time ? moment(time.ms) : moment.unix(time.unix);
  m = m.tz(timezone === 'Automatic' ? browserTimezone() : timezone);

  return m.format(time.format || defaultTimeFormat(m, timezone));
};

export const Timestamp: React.FC<TimestampProps> = (props) => {
  const [timezone] = React.useContext(TimezoneContext);
  return <>{timestampToString(props, timezone)}</>;
};
