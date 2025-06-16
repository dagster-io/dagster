import {Tooltip} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import {memo, useLayoutEffect, useRef, useState} from 'react';

import {Timestamp} from '../app/time/Timestamp';

dayjs.extend(relativeTime);
const TIME_FORMAT = {showSeconds: true, showTimezone: true};

interface Props {
  unixTimestamp: number;
  showTooltip?: boolean;
}

// Helper: returns ms until the next fromNow breakpoint for a given timestamp
function getNextFromNowUpdateMs(unixTimestamp: number): number {
  const now = dayjs();
  const then = dayjs(unixTimestamp * 1000);
  const diffSec = Math.abs(now.diff(then, 'second'));
  const diffMin = Math.abs(now.diff(then, 'minute'));
  const diffHour = Math.abs(now.diff(then, 'hour'));
  const diffDay = Math.abs(now.diff(then, 'day'));
  const diffMonth = Math.abs(now.diff(then, 'month'));
  const diffYear = Math.abs(now.diff(then, 'year'));

  // See: https://day.js.org/docs/en/display/from-now#list-of-breakdown-range
  if (diffSec < 45) {
    // Next change at 45s
    return (45 - diffSec) * 1000;
  } else if (diffSec < 90) {
    // Next change at 90s
    return (90 - diffSec) * 1000;
  } else if (diffMin < 45) {
    // Next change at next minute
    const nextMin = then.add(diffMin + 1, 'minute');
    return Math.abs(nextMin.diff(now, 'millisecond'));
  } else if (diffMin < 90) {
    // Next change at 90min
    return (90 * 60 - diffSec) * 1000;
  } else if (diffHour < 22) {
    // Next change at next hour
    const nextHour = then.add(diffHour + 1, 'hour');
    return Math.abs(nextHour.diff(now, 'millisecond'));
  } else if (diffHour < 36) {
    // Next change at 36h
    return (36 * 60 * 60 - diffSec) * 1000;
  } else if (diffDay < 25) {
    // Next change at next day
    const nextDay = then.add(diffDay + 1, 'day');
    return Math.abs(nextDay.diff(now, 'millisecond'));
  } else if (diffDay < 45) {
    // Next change at 46d
    return (46 * 24 * 60 * 60 - diffSec) * 1000;
  } else if (diffMonth < 11) {
    // Next change at next month
    const nextMonth = then.add(diffMonth + 1, 'month');
    return Math.abs(nextMonth.diff(now, 'millisecond'));
  } else if (diffYear < 1.5) {
    // Next change at 1.5y (18 months)
    const nextYear = then.add(1.5, 'year');
    return Math.abs(nextYear.diff(now, 'millisecond'));
  } else {
    // Next change at next year
    const nextYear = then.add(diffYear + 1, 'year');
    return Math.abs(nextYear.diff(now, 'millisecond'));
  }
}

export const TimeFromNow = memo(({unixTimestamp, showTooltip = true}: Props) => {
  const [timeAgo, setTimeAgo] = useState(() => dayjs(unixTimestamp * 1000).fromNow());
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useLayoutEffect(() => {
    function scheduleUpdate() {
      setTimeAgo(dayjs(unixTimestamp * 1000).fromNow());
      const nextMs = Math.max(1000, getNextFromNowUpdateMs(unixTimestamp));
      timeoutRef.current = setTimeout(scheduleUpdate, nextMs);
    }
    scheduleUpdate();
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [unixTimestamp]);

  return showTooltip ? (
    <Tooltip
      placement="top"
      content={<Timestamp timestamp={{unix: unixTimestamp}} timeFormat={TIME_FORMAT} />}
    >
      {timeAgo}
    </Tooltip>
  ) : (
    <span>{timeAgo}</span>
  );
});
