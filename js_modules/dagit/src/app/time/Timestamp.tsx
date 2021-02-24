import * as React from 'react';

import {TimeFormat} from 'src/app/time/TimestampFormat';
import {TimezoneContext} from 'src/app/time/TimezoneContext';
import {timestampToString} from 'src/app/time/timestampToString';

interface Props {
  timestamp: {ms: number} | {unix: number};
  timeFormat?: TimeFormat;
}

export const Timestamp: React.FC<Props> = (props) => {
  const {timestamp, timeFormat} = props;
  const [timezone] = React.useContext(TimezoneContext);
  const locale = navigator.language;
  return <>{timestampToString({timestamp, locale, timezone, timeFormat})}</>;
};
