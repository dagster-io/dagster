import {Colors} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {useLocation, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {TimezoneContext} from '../app/time/TimezoneContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {FontFamily} from '../ui/styles';

import {LogLevel} from './LogLevel';
import {ColumnWidthsContext} from './LogsScrollingTableHeader';

const bgcolorForLevel = (level: LogLevel) =>
  ({
    [LogLevel.DEBUG]: `transparent`,
    [LogLevel.INFO]: `transparent`,
    [LogLevel.EVENT]: `transparent`,
    [LogLevel.WARNING]: `rgba(166, 121, 8, 0.05)`,
    [LogLevel.ERROR]: `rgba(206, 17, 38, 0.05)`,
    [LogLevel.CRITICAL]: `rgba(206, 17, 38, 0.05)`,
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
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  background: ${({highlighted, level}) => (highlighted ? '#ffe39f' : bgcolorForLevel(level))};
  &:hover {
    background: ${({highlighted}) => (highlighted ? '#ffe39f' : 'white')};
  }
  color: ${(props) =>
    ({
      [LogLevel.DEBUG]: Colors.GRAY3,
      [LogLevel.INFO]: Colors.DARK_GRAY2,
      [LogLevel.EVENT]: Colors.DARK_GRAY2,
      [LogLevel.WARNING]: Colors.GOLD2,
      [LogLevel.ERROR]: Colors.RED3,
      [LogLevel.CRITICAL]: Colors.RED3,
    }[props.level])};
`;

export const StructuredContent = styled.div`
  background: rgba(255, 255, 255, 0.5);
  color: ${Colors.DARK_GRAY2};
  box-sizing: border-box;
  border-left: 1px solid ${Colors.LIGHT_GRAY4};
  border-right: 1px solid ${Colors.LIGHT_GRAY4};
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
export const SolidColumn = (props: {stepKey: string | false | null}) => {
  const widths = React.useContext(ColumnWidthsContext);
  const parts = String(props.stepKey).split('.');
  return (
    <SolidColumnContainer style={{width: widths.solid}}>
      {props.stepKey
        ? parts.map((p, idx) => (
            <div
              key={idx}
              data-tooltip={p}
              data-tooltip-style={SolidColumnTooltipStyle}
              style={{
                marginLeft: Math.max(0, idx * 15 - 9),
                fontWeight: idx === parts.length - 1 ? 600 : 300,
                paddingRight: 15,
              }}
            >
              {idx > 0 ? '↳' : ''}
              {p.length > 30 - idx * 2
                ? `${p.substr(0, 16 - idx * 2)}…${p.substr(p.length - 14)}`
                : p}
            </div>
          ))
        : '-'}
    </SolidColumnContainer>
  );
};

const SolidColumnContainer = styled.div`
  width: 250px;
  flex-shrink: 0;
  padding: 4px;
`;

const SolidColumnTooltipStyle = JSON.stringify({
  fontSize: '0.9em',
  fontFamily: FontFamily.monospace,
  color: Colors.BLACK,
  background: Colors.WHITE,
  border: `1px solid ${Colors.LIGHT_GRAY3}`,
  top: -8,
  left: 1,
});

// Timestamp Column

export const TimestampColumn: React.FC<{time: string | null}> = React.memo((props) => {
  const location = useLocation();
  const widths = React.useContext(ColumnWidthsContext);
  const [timezone] = React.useContext(TimezoneContext);
  const timeString = () => {
    const {time} = props;
    if (time) {
      const timeNumber = Number(time);
      const locale = navigator.language;
      const main = new Date(timeNumber).toLocaleTimeString(locale, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
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

  return (
    <TimestampColumnContainer style={{width: widths.timestamp}}>
      <Link to={href}>{timeString()}</Link>
    </TimestampColumnContainer>
  );
});

const TimestampColumnContainer = styled.div`
  flex-shrink: 0;
  padding: 4px 4px 4px 8px;

  a:link,
  a:visited,
  a:hover,
  a:active {
    color: ${Colors.GRAY3};
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
  color: ${Colors.GRAY3};
  padding: 4px;
`;
