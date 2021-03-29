import * as React from 'react';

import {TimeFormat} from './TimestampFormat';
import {TimezoneContext} from './TimezoneContext';
import {timestampToString} from './timestampToString';

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
