import {useContext, useEffect, useState} from 'react';

import {TimeContext} from './TimeContext';
import {formatCompactTimeAgo, getNextCompactTimeAgoUpdateMs} from './formatCompactTimeAgo';

/** Compact "ago" text for a timestamp that re-renders at each unit boundary. */
export const useCompactTimeAgo = (unixMs: number) => {
  const {resolvedTimezone: timezone} = useContext(TimeContext);
  const [text, setText] = useState(() =>
    formatCompactTimeAgo(Date.now(), unixMs, {locale: navigator.language, timezone}),
  );

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const update = () => {
      const nowMs = Date.now();
      setText(formatCompactTimeAgo(nowMs, unixMs, {locale: navigator.language, timezone}));
      timeout = setTimeout(update, getNextCompactTimeAgoUpdateMs(nowMs, unixMs));
    };
    update();
    return () => clearTimeout(timeout);
  }, [unixMs, timezone]);

  return text;
};
