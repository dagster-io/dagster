import {
  Box,
  Colors,
  Icon,
  IconName,
  Popover,
  Spinner,
  Text,
  Tooltip,
} from '@dagster-io/ui-components';
import {ReactNode, useEffect, useState} from 'react';

import styles from './css/RunStatusCell.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {formatElapsedTimePadded} from '../../app/time/formatElapsedTimePadded';
import {useCompactTimeAgo} from '../../app/time/useCompactTimeAgo';
import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {RunStats} from '../RunStats';
import {runStatusToBackfillStateString} from '../RunStatusTag';

type Timing = MappedRunsFeedEntry['timing'];

type Phase = 'created' | 'starting' | 'live' | 'terminal';

type StatusDisplay = {
  icon: IconName | 'spinner';
  iconColor: string;
  label: string;
  phase: Phase;
  textColor: 'textBlue' | 'textYellow' | 'textLight';
  isPulsing: boolean;
};

type TimingDisplay = {
  text: ReactNode;
  tooltip: ReactNode;
  isCounter: boolean;
};

const UNKNOWN_CLOCK = '--:--:--';

const RUN_STATUS_DISPLAYS = {
  [RunStatus.NOT_STARTED]: {
    icon: 'dagster_primary',
    iconColor: Colors.accentBlue(),
    label: 'Not started',
    phase: 'created',
    textColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.QUEUED]: {
    icon: 'dagster_primary',
    iconColor: Colors.accentBlue(),
    label: 'Queued',
    phase: 'created',
    textColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.STARTING]: {
    icon: 'status',
    iconColor: Colors.accentBlue(),
    label: 'Starting',
    phase: 'starting',
    textColor: 'textBlue',
    isPulsing: true,
  },
  [RunStatus.STARTED]: {
    icon: 'spinner',
    iconColor: Colors.accentBlue(),
    label: 'Started',
    phase: 'live',
    textColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.MANAGED]: {
    icon: 'spinner',
    iconColor: Colors.accentBlue(),
    label: 'Managed',
    phase: 'live',
    textColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.CANCELING]: {
    icon: 'cancel',
    iconColor: Colors.accentYellow(),
    label: 'Canceling',
    phase: 'live',
    textColor: 'textYellow',
    isPulsing: true,
  },
  [RunStatus.SUCCESS]: {
    icon: 'check_filled',
    iconColor: Colors.accentGreen(),
    label: 'Success',
    phase: 'terminal',
    textColor: 'textLight',
    isPulsing: false,
  },
  [RunStatus.FAILURE]: {
    icon: 'error',
    iconColor: Colors.accentRed(),
    label: 'Failed',
    phase: 'terminal',
    textColor: 'textLight',
    isPulsing: false,
  },
  [RunStatus.CANCELED]: {
    icon: 'cancel',
    iconColor: Colors.accentYellow(),
    label: 'Canceled',
    phase: 'terminal',
    textColor: 'textLight',
    isPulsing: false,
  },
} as const satisfies Record<RunStatus, StatusDisplay>;

const getStatusDisplay = (entry: MappedRunsFeedEntry): StatusDisplay => {
  const display = RUN_STATUS_DISPLAYS[entry.runStatus];
  if (entry.__typename === 'PartitionBackfill') {
    // FAILING maps to FAILURE while the backfill is still canceling its runs.
    if (entry.backfillStatus === BulkActionStatus.FAILING) {
      return {
        ...display,
        label: 'Failing',
        phase: 'live',
        textColor: 'textYellow',
        isPulsing: true,
      };
    }
    return {
      ...display,
      label: runStatusToBackfillStateString(entry.runStatus),
    };
  }

  if (entry.willRetry) {
    return {
      ...display,
      icon: 'replay',
      iconColor: Colors.accentYellow(),
      label: 'Failed (will retry)',
    };
  }

  return display;
};

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
  startAtMs: number;
};

const LiveElapsed = ({startAtMs}: LiveElapsedProps) => {
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

  return <>{formatElapsedTimePadded(nowMs - startAtMs)}</>;
};

type TerminalTooltipProps = {
  timing: Timing;
  failedToStart: boolean;
};

const TerminalTooltip = ({timing, failedToStart}: TerminalTooltipProps) => (
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

const getTimingDisplay = (entry: MappedRunsFeedEntry, phase: Phase): TimingDisplay => {
  const {timing} = entry;
  const created = <AbsoluteTime label="Created" unixMs={timing.createdAtMs} />;

  if (phase === 'created') {
    return {
      text: <RelativeTime unixMs={timing.createdAtMs} />,
      tooltip: created,
      isCounter: false,
    };
  }

  if (phase === 'terminal') {
    const failedToStart = entry.runStatus === RunStatus.FAILURE && timing.startAtMs === null;
    return {
      text: <RelativeTime unixMs={timing.endAtMs ?? timing.createdAtMs} />,
      tooltip: <TerminalTooltip timing={timing} failedToStart={failedToStart} />,
      isCounter: false,
    };
  }

  const started =
    timing.startAtMs === null ? (
      created
    ) : (
      <AbsoluteTime label="Started" unixMs={timing.startAtMs} />
    );

  if (phase === 'starting') {
    return {
      text: formatElapsedTimePadded(0),
      tooltip: started,
      isCounter: true,
    };
  }

  return {
    text: timing.startAtMs === null ? UNKNOWN_CLOCK : <LiveElapsed startAtMs={timing.startAtMs} />,
    tooltip: started,
    isCounter: true,
  };
};

type RunStatusCellProps = {
  entry: MappedRunsFeedEntry;
};

export const RunStatusCell = ({entry}: RunStatusCellProps) => {
  const {icon, iconColor, label, phase, textColor, isPulsing} = getStatusDisplay(entry);
  const {text, tooltip, isCounter} = getTimingDisplay(entry, phase);

  const statusIcon = (
    <Box
      flex={{alignItems: 'center', shrink: 0}}
      padding={{right: 16}}
      margin={{right: 16}}
      border="right"
      role="img"
      aria-label={label}
    >
      {icon === 'spinner' ? (
        <Spinner purpose="body-text" fillColor={iconColor} title={label} />
      ) : (
        <Icon name={icon} color={iconColor} className={isPulsing ? styles.pulse : undefined} />
      )}
    </Box>
  );

  return (
    <Box flex={{direction: 'row', alignItems: 'center'}}>
      {entry.__typename === 'Run' ? (
        <Popover
          interactionKind="hover"
          usePortal
          position="bottom-left"
          hoverOpenDelay={100}
          // The timing text is the row's one tab stop; the step statistics are a hover extra.
          openOnTargetFocus={false}
          content={
            <>
              <Text as="div" size={12} weight={600} className={styles.popoverHeading}>
                {label}
              </Text>
              <RunStats runId={entry.id} />
            </>
          }
        >
          {statusIcon}
        </Popover>
      ) : (
        <Tooltip content={label} placement="top">
          {statusIcon}
        </Tooltip>
      )}
      {/* Focusable so keyboard users can reach the absolute timestamps and duration. */}
      <Tooltip content={tooltip} placement="top">
        <Text
          size={14}
          family={isCounter ? 'mono' : 'default'}
          color={textColor}
          className={styles.timing}
          tabIndex={0}
        >
          {text}
        </Text>
      </Tooltip>
    </Box>
  );
};
