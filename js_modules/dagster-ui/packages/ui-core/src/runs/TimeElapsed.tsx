import {Colors, Group, Icon} from '@dagster-io/ui-components';
import * as React from 'react';

import {formatElapsedTimeWithMsec, formatElapsedTimeWithoutMsec} from '../app/Util';

export interface Props {
  startUnix: number | null;
  endUnix: number | null;
  showMsec?: boolean;
}

export const TimeElapsed = (props: Props) => {
  const {startUnix, endUnix, showMsec} = props;

  const [endTime, setEndTime] = React.useState(() => (endUnix ? endUnix * 1000 : null));
  const interval = React.useRef<ReturnType<typeof setInterval>>();
  const timeout = React.useRef<ReturnType<typeof setTimeout>>();

  const clearTimers = React.useCallback(() => {
    interval.current && clearInterval(interval.current);
    timeout.current && clearTimeout(timeout.current);
  }, []);

  React.useEffect(() => {
    // An end time has been supplied. Simply set a static value.
    if (endUnix) {
      setEndTime(endUnix * 1000);
      return;
    }

    // Align to the next second and then update every second so the elapsed
    // time "ticks" up.
    timeout.current = setTimeout(() => {
      interval.current = setInterval(() => {
        setEndTime(Date.now());
      }, 1000);
    }, Date.now() % 1000);

    return () => clearTimers();
  }, [clearTimers, endUnix]);

  const startTime = startUnix ? startUnix * 1000 : 0;

  return (
    <Group direction="row" spacing={4} alignItems="center">
      <Icon name="timer" color={Colors.textLight()} />
      <span style={{fontVariantNumeric: 'tabular-nums'}}>
        {startTime
          ? showMsec
            ? formatElapsedTimeWithMsec((endTime || Date.now()) - startTime)
            : formatElapsedTimeWithoutMsec((endTime || Date.now()) - startTime)
          : '–'}
      </span>
    </Group>
  );
};
