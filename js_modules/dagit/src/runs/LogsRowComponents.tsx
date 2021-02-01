import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Timestamp} from 'src/app/time/Timestamp';
import {LogLevel} from 'src/runs/LogLevel';
import {ColumnWidthsContext} from 'src/runs/LogsScrollingTableHeader';
import {FontFamily} from 'src/ui/styles';

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
  font-size: 0.75em;
  width: 100%;
  height: 100%;
  max-height: 17em;
  padding: 4px 8px;
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
  margin: -4px;
  margin-bottom: -4px;
  border-left: 1px solid ${Colors.LIGHT_GRAY4};
  border-right: 1px solid ${Colors.LIGHT_GRAY4};
  padding: 4px;
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
`;

const SolidColumnTooltipStyle = JSON.stringify({
  fontSize: '0.75em',
  fontFamily: FontFamily.monospace,
  color: Colors.BLACK,
  background: Colors.WHITE,
  border: `1px solid ${Colors.LIGHT_GRAY3}`,
  top: -8,
  left: 1,
});

// Timestamp Column

export const TimestampColumn = (props: {time: string | false}) => {
  const widths = React.useContext(ColumnWidthsContext);
  return (
    <TimestampColumnContainer style={{width: widths.timestamp}}>
      {props.time && <Timestamp ms={Number(props.time)} format="HH:mm:ss.SSS" />}
    </TimestampColumnContainer>
  );
};

const TimestampColumnContainer = styled.div`
  flex-shrink: 0;
  text-align: right;
  color: ${Colors.GRAY3};
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
`;
