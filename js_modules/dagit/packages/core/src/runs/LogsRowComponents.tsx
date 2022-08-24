import {Colors, FontFamily, MetadataTable, Tooltip} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';
import styled from 'styled-components/macro';

import {formatElapsedTimeWithMsec} from '../app/Util';
import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';

import {LogLevel} from './LogLevel';
import {ColumnWidthsContext} from './LogsScrollingTableHeader';

const bgcolorForLevel = (level: LogLevel) =>
  ({
    [LogLevel.DEBUG]: Colors.White,
    [LogLevel.INFO]: Colors.White,
    [LogLevel.EVENT]: Colors.White,
    [LogLevel.WARNING]: Colors.Yellow50,
    [LogLevel.ERROR]: Colors.Red50,
    [LogLevel.CRITICAL]: Colors.Red50,
  }[level]);

export const Row = styled.div<{level: LogLevel; highlighted: boolean}>`
  font-size: 0.9em;
  width: 100%;
  height: 100%;
  max-height: 17em;
  word-break: break-word;
  white-space: pre-wrap;
  font-family: ${FontFamily.monospace};
  display: flex;
  flex-direction: row;
  align-items: baseline;
  overflow: hidden;
  border-top: 1px solid ${Colors.KeylineGray};
  background: ${({highlighted, level}) => (highlighted ? '#ffe39f' : bgcolorForLevel(level))};
  &:hover {
    background: ${({highlighted}) => (highlighted ? '#ffe39f' : 'white')};
  }
  color: ${(props) =>
    ({
      [LogLevel.DEBUG]: Colors.Gray400,
      [LogLevel.INFO]: Colors.Gray900,
      [LogLevel.EVENT]: Colors.Gray900,
      [LogLevel.WARNING]: Colors.Yellow700,
      [LogLevel.ERROR]: Colors.Red500,
      [LogLevel.CRITICAL]: Colors.Red500,
    }[props.level])};
`;

export const StructuredContent = styled.div`
  background: rgba(255, 255, 255, 0.5);
  color: ${Colors.Gray900};
  box-sizing: border-box;
  border-left: 1px solid ${Colors.KeylineGray};
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
  color: Colors.Dark,
  background: Colors.White,
  border: `1px solid ${Colors.Gray100}`,
  top: -8,
  left: 1,
});

// Timestamp Column

export const TimestampColumn: React.FC<{
  time: string | null;
  runStartTime?: number;
  stepStartTime?: number;
}> = React.memo((props) => {
  const {time, runStartTime, stepStartTime} = props;
  const location = useLocation();
  const widths = React.useContext(ColumnWidthsContext);
  const [timezone] = React.useContext(TimezoneContext);
  const canShowTooltip = typeof time === 'string' && typeof runStartTime === 'number';

  const timeString = () => {
    if (time) {
      const timeNumber = Number(time);
      const locale = navigator.language;
      const main = new Date(timeNumber).toLocaleTimeString(locale, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23',
        timeZone: timezone === 'Automatic' ? browserTimezone() : timezone,
      });
      const fractionalSec = (timeNumber % 1000) / 1000;
      return `${main}${fractionalSec
        .toLocaleString(locale, {
          minimumFractionDigits: 3,
          maximumFractionDigits: 3,
        })
        .slice(1)}`;
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
                  <span style={{fontFamily: FontFamily.monospace, fontSize: '13px'}}>
                    {runElapsedTime}
                  </span>
                ),
              },
              stepStartTime
                ? {
                    key: 'Since start of step',
                    value: (
                      <span style={{fontFamily: FontFamily.monospace, fontSize: '13px'}}>
                        {stepElapsedTime}
                      </span>
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
    color: ${Colors.Gray400};
  }

  a:hover,
  a:active {
    text-decoration: underline;
  }
`;

export const EventTypeColumn: React.FC = (props) => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <EventTypeColumnContainer style={{width: widths.eventType}}>
      {props.children}
    </EventTypeColumnContainer>
  );
};

const EventTypeColumnContainer = styled.div`
  flex-shrink: 0;
  color: ${Colors.Gray400};
  padding: 4px;
`;
