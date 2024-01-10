import {
  FontFamily,
  MetadataTable,
  Tooltip,
  colorBackgroundDefault,
  colorBackgroundRed,
  colorBackgroundYellow,
  colorBackgroundLightHover,
  colorKeylineDefault,
  colorTextDefault,
  colorTextLight,
  colorTextRed,
  colorTextYellow,
} from '@dagster-io/ui-components';
import memoize from 'lodash/memoize';
import qs from 'qs';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';
import styled from 'styled-components';

import {formatElapsedTimeWithMsec} from '../app/Util';
import {HourCycle} from '../app/time/HourCycle';
import {TimeContext} from '../app/time/TimeContext';
import {browserHourCycle, browserTimezone} from '../app/time/browserTimezone';

import {LogLevel} from './LogLevel';
import {ColumnWidthsContext} from './LogsScrollingTableHeader';

const bgcolorForLevel = (level: LogLevel) =>
  ({
    [LogLevel.DEBUG]: colorBackgroundDefault(),
    [LogLevel.INFO]: colorBackgroundDefault(),
    [LogLevel.EVENT]: colorBackgroundDefault(),
    [LogLevel.WARNING]: colorBackgroundYellow(),
    [LogLevel.ERROR]: colorBackgroundRed(),
    [LogLevel.CRITICAL]: colorBackgroundRed(),
  })[level];

export const Row = styled.div<{level: LogLevel; highlighted: boolean}>`
  font-size: 0.9em;
  width: 100%;
  height: 100%;
  max-height: 17em;
  word-break: break-word;
  white-space: pre-wrap;
  color: ${colorTextDefault()};
  font-family: ${FontFamily.monospace};
  display: flex;
  flex-direction: row;
  align-items: baseline;
  overflow: hidden;
  border-top: 1px solid ${colorKeylineDefault()};
  background-color: ${({highlighted, level}) =>
    highlighted ? colorBackgroundLightHover() : bgcolorForLevel(level)};

  color: ${(props) =>
    ({
      [LogLevel.DEBUG]: colorTextLight(),
      [LogLevel.INFO]: colorTextDefault(),
      [LogLevel.EVENT]: colorTextDefault(),
      [LogLevel.WARNING]: colorTextYellow(),
      [LogLevel.ERROR]: colorTextRed(),
      [LogLevel.CRITICAL]: colorTextRed(),
    })[props.level]};
`;

export const StructuredContent = styled.div`
  box-sizing: border-box;
  border-left: 1px solid ${colorKeylineDefault()};
  word-break: break-word;
  white-space: pre-wrap;
  font-family: ${FontFamily.monospace};
  flex: 1;
  align-self: stretch;
  display: flex;
  flex-direction: row;
  align-items: baseline;
`;

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

export const OpColumnContainer = styled.div`
  width: 250px;
  flex-shrink: 0;
  padding: 4px 12px;
`;

const OpColumnTooltipStyle = JSON.stringify({
  fontSize: '0.9em',
  fontFamily: FontFamily.monospace,
  color: colorTextDefault(),
  background: colorBackgroundDefault(),
  border: `1px solid ${colorKeylineDefault()}`,
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
      timeZone: timezone === 'Automatic' ? browserTimezone() : timezone,
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
    timezone: [timezone],
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
    <TimestampColumnContainer style={{width: widths.timestamp}}>
      <Tooltip
        canShow={canShowTooltip}
        content={
          <MetadataTable
            spacing={0}
            dark
            rows={[
              {
                key: 'Since start of run',
                value: (
                  <div
                    style={{textAlign: 'right', fontFamily: FontFamily.monospace, fontSize: '13px'}}
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
        }
        placement="left"
      >
        <Link to={href}>{timeString()}</Link>
      </Tooltip>
    </TimestampColumnContainer>
  );
});

const TimestampColumnContainer = styled.div`
  flex-shrink: 0;
  padding: 4px 4px 4px 12px;

  a:link,
  a:visited,
  a:hover,
  a:active {
    color: ${colorTextLight()};
  }

  a:hover,
  a:active {
    text-decoration: underline;
  }
`;

export const EventTypeColumn = (props: {children: React.ReactNode}) => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <EventTypeColumnContainer style={{width: widths.eventType}}>
      {props.children}
    </EventTypeColumnContainer>
  );
};

const EventTypeColumnContainer = styled.div`
  flex-shrink: 0;
  color: ${colorTextLight()};
  padding: 4px;
`;
