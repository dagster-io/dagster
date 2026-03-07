import {Tooltip} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import {memo, useLayoutEffect, useRef, useState} from 'react';

import {Timestamp} from '../app/time/Timestamp';
import {getNextFromNowUpdateMs} from '../util/dayjsExtensions';

const TIME_FORMAT = {showSeconds: true, showTimezone: true};

interface Props {
  unixTimestamp: number;
  showTooltip?: boolean;
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
