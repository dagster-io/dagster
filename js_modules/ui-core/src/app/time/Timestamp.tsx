import {useContext} from 'react';

import {TimeContext} from './TimeContext';
import {TimeFormat} from './TimestampFormat';
import {timestampToString} from './timestampToString';

interface Props {
  timestamp: {ms: number} | {unix: number};
  timeFormat?: TimeFormat;
}

export const Timestamp = (props: Props) => {
  const {timestamp, timeFormat} = props;
  const {
    timezone: [timezone],
    hourCycle: [hourCycle],
  } = useContext(TimeContext);
  const locale = navigator.language;
  return <>{timestampToString({timestamp, locale, timezone, timeFormat, hourCycle})}</>;
};
