import {Box, Colors, FontFamily, MetadataTable, Tooltip} from '@dagster-io/ui-components';
import clsx from 'clsx';
import memoize from 'lodash/memoize';
import qs from 'qs';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';

import {LogLevel} from './LogLevel';
import {ColumnWidthsContext} from './LogsScrollingTableHeader';
import styles from './css/LogsRowComponents.module.css';
import {formatElapsedTimeWithMsec} from '../app/Util';
import {HourCycle} from '../app/time/HourCycle';
import {TimeContext} from '../app/time/TimeContext';
import {browserHourCycle} from '../app/time/browserTimezone';
import {TimestampDisplay} from '../schedules/TimestampDisplay';

export const MAX_ROW_HEIGHT_PX = 200;

const rowLevelClass: Record<LogLevel, string | undefined> = {
  [LogLevel.DEBUG]: styles.rowDebug,
  [LogLevel.INFO]: styles.rowInfo,
  [LogLevel.EVENT]: styles.rowEvent,
  [LogLevel.WARNING]: styles.rowWarning,
  [LogLevel.ERROR]: styles.rowError,
  [LogLevel.CRITICAL]: styles.rowCritical,
};

export const Row = React.forwardRef<
  HTMLDivElement,
  {level: LogLevel; highlighted: boolean} & React.HTMLAttributes<HTMLDivElement>
>(({level, highlighted, className, ...rest}, ref) => (
  <div
    ref={ref}
    className={clsx(
      styles.row,
      rowLevelClass[level],
      highlighted && styles.rowHighlighted,
      className,
    )}
    {...rest}
  />
));

export const StructuredContent = ({className, ...rest}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.structuredContent, className)} {...rest} />
);

// Step Key Column
//
// Renders the left column with the step key broken into hierarchical components.
// Manually implements middle text truncation since we can count on monospace font
// rendering being fairly consistent.
//
export const OpColumn = (props: {stepKey: string | false | null}) => {
  const widths = React.useContext(ColumnWidthsContext);
  const parts = String(props.stepKey).split('.');
  return (
    <OpColumnContainer style={{width: widths.solid}}>
      {props.stepKey
        ? parts.map((p, idx) => (
            <div
              key={idx}
              data-tooltip={p}
              data-tooltip-style={OpColumnTooltipStyle}
              style={{
                marginLeft: Math.max(0, idx * 15 - 9),
                fontWeight: idx === parts.length - 1 ? 600 : 300,
              }}
            >
              {idx > 0 ? '↳' : ''}
              {p.length > 30 - idx * 2
                ? `${p.substr(0, 16 - idx * 2)}…${p.substr(p.length - 14)}`
                : p}
            </div>
          ))
        : '-'}
    </OpColumnContainer>
  );
};

export const OP_COLUMN_CONTAINER_CLASS = 'op-column-container';

export const OpColumnContainer = ({className, ...rest}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(OP_COLUMN_CONTAINER_CLASS, styles.opColumnContainer, className)} {...rest} />
);

const OpColumnTooltipStyle = JSON.stringify({
  fontSize: '12px',
  fontFamily: FontFamily.monospace,
  color: Colors.textDefault(),
  background: Colors.backgroundDefault(),
  border: `1px solid ${Colors.keylineDefault()}`,
  top: -8,
  left: 1,
});

const timestampFormat = memoize(
  (timezone: string, hourCycle: HourCycle) => {
    const evaluatedHourCycle = hourCycle === 'Automatic' ? browserHourCycle() : hourCycle;
    return new Intl.DateTimeFormat(navigator.language, {
      hour: evaluatedHourCycle === 'h23' ? '2-digit' : 'numeric',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
      hourCycle: evaluatedHourCycle,
      timeZone: timezone,
    });
  },
  (timezone, hourCycle) => `${timezone}-${hourCycle}`,
);

// Timestamp Column

interface TimestampColumnProps {
  time: string | null;
  runStartTime?: number;
  stepStartTime?: number;
}

export const TimestampColumn = React.memo((props: TimestampColumnProps) => {
  const {time, runStartTime, stepStartTime} = props;
  const location = useLocation();
  const widths = React.useContext(ColumnWidthsContext);
  const {
    resolvedTimezone: timezone,
    hourCycle: [hourCycle],
  } = React.useContext(TimeContext);
  const canShowTooltip = typeof time === 'string' && typeof runStartTime === 'number';

  const timeString = () => {
    if (time) {
      const date = new Date(Number(time));
      return timestampFormat(timezone, hourCycle).format(date);
    }
    return '';
  };

  const href = `${location.pathname}?${qs.stringify({focusedTime: props.time})}`;
  const runElapsedTime = formatElapsedTimeWithMsec(Number(time) - (runStartTime || 0));
  const stepElapsedTime = formatElapsedTimeWithMsec(Number(time) - (stepStartTime || 0));

  return (
    <div className={styles.timestampColumnContainer} style={{width: widths.timestamp}}>
      <Tooltip
        canShow={canShowTooltip}
        content={
          <div>
            <Box margin={{bottom: 8}}>
              <TimestampDisplay
                timestamp={Number(time) / 1000}
                timeFormat={{showSeconds: true, showMsec: true, showTimezone: false}}
              />
            </Box>
            <MetadataTable
              spacing={0}
              rows={[
                {
                  key: 'Since start of run',
                  value: (
                    <div
                      style={{
                        textAlign: 'right',
                        fontFamily: FontFamily.monospace,
                        fontSize: '13px',
                      }}
                    >
                      {runElapsedTime}
                    </div>
                  ),
                },
                stepStartTime
                  ? {
                      key: 'Since start of step',
                      value: (
                        <div
                          style={{
                            textAlign: 'right',
                            fontFamily: FontFamily.monospace,
                            fontSize: '13px',
                          }}
                        >
                          {stepElapsedTime}
                        </div>
                      ),
                    }
                  : null,
              ]}
            />
          </div>
        }
        placement="left"
      >
        <Link to={href}>{timeString()}</Link>
      </Tooltip>
    </div>
  );
});

export const EventTypeColumn = (props: {children: React.ReactNode}) => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <div className={styles.eventTypeColumnContainer} style={{width: widths.eventType}}>
      {props.children}
    </div>
  );
};
