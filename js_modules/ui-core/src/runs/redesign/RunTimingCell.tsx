import {Box, Text, Tooltip} from '@dagster-io/ui-components';
import {ReactNode, useEffect, useState} from 'react';

import styles from './css/RunTimingCell.module.css';
import {TimingMode, getRunStatusDisplay} from './getRunStatusDisplay';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {formatElapsedTimePadded} from '../../app/time/formatElapsedTimePadded';
import {useCompactTimeAgo} from '../../app/time/useCompactTimeAgo';
import {RunStatus} from '../../graphql/types';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

type Timing = MappedRunsFeedEntry['timing'];

type TimingDisplay = {
  text: ReactNode;
  tooltip: ReactNode;
  isClock: boolean;
};

const PLACEHOLDER_CLOCK = '--:--:--';

type RelativeTimeProps = {
  unixMs: number;
};

const RelativeTime = ({unixMs}: RelativeTimeProps) => <>{useCompactTimeAgo(unixMs)}</>;

type AbsoluteTimeProps = {
  label: string;
  unixMs: number;
};

const AbsoluteTime = ({label, unixMs}: AbsoluteTimeProps) => (
  <div>
    {label}: <TimestampDisplay timestamp={unixMs / 1000} />
  </div>
);

type LiveElapsedProps = {
  fromMs: number;
};

const LiveElapsed = ({fromMs}: LiveElapsedProps) => {
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    // Align the first update to the next second boundary, then tick with the clock.
    const timeout = setTimeout(
      () => {
        setNowMs(Date.now());
        interval = setInterval(() => setNowMs(Date.now()), 1000);
      },
      1000 - (Date.now() % 1000),
    );
    return () => {
      clearTimeout(timeout);
      if (interval !== undefined) {
        clearInterval(interval);
      }
    };
  }, []);

  return <>{formatElapsedTimePadded(nowMs - fromMs)}</>;
};

type FinishTimeTooltipProps = {
  timing: Timing;
  failedToStart: boolean;
};

const FinishTimeTooltip = ({timing, failedToStart}: FinishTimeTooltipProps) => (
  <Box flex={{direction: 'column', gap: 4}}>
    {failedToStart ? (
      <div>Failed to start</div>
    ) : (
      <>
        {timing.durationMs !== null && (
          <div>Ran for {formatElapsedTimePadded(timing.durationMs)}</div>
        )}
        {timing.startAtMs !== null && <AbsoluteTime label="Started" unixMs={timing.startAtMs} />}
      </>
    )}
    {timing.endAtMs === null ? (
      <AbsoluteTime label="Created" unixMs={timing.createdAtMs} />
    ) : (
      <AbsoluteTime label="Finished" unixMs={timing.endAtMs} />
    )}
  </Box>
);

const getTimingDisplay = (entry: MappedRunsFeedEntry, timingMode: TimingMode): TimingDisplay => {
  const {timing} = entry;

  if (timingMode === 'relative-finish-time') {
    const failedToStart = entry.runStatus === RunStatus.FAILURE && timing.startAtMs === null;
    return {
      text: <RelativeTime unixMs={timing.endAtMs ?? timing.createdAtMs} />,
      tooltip: <FinishTimeTooltip timing={timing} failedToStart={failedToStart} />,
      isClock: false,
    };
  }

  const created = <AbsoluteTime label="Created" unixMs={timing.createdAtMs} />;
  if (timingMode === 'elapsed-since-creation') {
    return {
      text: <LiveElapsed fromMs={timing.createdAtMs} />,
      tooltip: created,
      isClock: true,
    };
  }

  const started =
    timing.startAtMs === null ? (
      created
    ) : (
      <AbsoluteTime label="Started" unixMs={timing.startAtMs} />
    );
  if (timingMode === 'elapsed-since-start' && timing.startAtMs !== null) {
    return {
      text: <LiveElapsed fromMs={timing.startAtMs} />,
      tooltip: started,
      isClock: true,
    };
  }

  return {
    text: PLACEHOLDER_CLOCK,
    tooltip: started,
    isClock: true,
  };
};

type RunTimingCellProps = {
  entry: MappedRunsFeedEntry;
};

export const RunTimingCell = ({entry}: RunTimingCellProps) => {
  const {timingMode, timingColor} = getRunStatusDisplay(entry);
  const {text, tooltip, isClock} = getTimingDisplay(entry, timingMode);

  return (
    <div className={styles.cell}>
      {/* Focusable so keyboard users can reach the absolute timestamps and duration. */}
      <Tooltip content={tooltip} placement="top">
        <Text
          size={14}
          family={isClock ? 'mono' : 'default'}
          color={timingColor}
          className={styles.timing}
          tabIndex={0}
        >
          {text}
        </Text>
      </Tooltip>
    </div>
  );
};
