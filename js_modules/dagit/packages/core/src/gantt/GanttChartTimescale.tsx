import {Colors, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {formatElapsedTime} from '../app/Util';

import {CSS_DURATION, GanttViewport, LEFT_INSET} from './Constants';

const msToMinuteLabel = (ms: number) => `${Math.round(ms / 1000 / 60)}m`;
const msToSecondLabel = (ms: number) => `${(ms / 1000).toFixed(0)}s`;
const msToSubsecondLabel = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

// We want to gracefully transition the tick marks shown as you zoom, but it's
// nontrivial to programatically pick good intervals. (500ms => 1s => 5s, etc.)
// This lookup table defines the available tick mark intervals and the labeling
// that should be used for each one("2:00" or "2m" or "2s" or "0.05s", etc.).
//
// We use the first configuration that places ticks at least 80 pixels apart
// at the rendered scale.
//
const TICK_LABEL_WIDTH = 56;
const TICK_CONFIG = [
  {
    tickIntervalMs: 0.5 * 1000,
    tickLabels: msToSubsecondLabel,
  },
  {
    tickIntervalMs: 1 * 1000,
    tickLabels: msToSecondLabel,
  },
  {
    tickIntervalMs: 5 * 1000,
    tickLabels: msToSecondLabel,
  },
  {
    tickIntervalMs: 10 * 1000,
    tickLabels: msToSecondLabel,
  },
  {
    tickIntervalMs: 30 * 1000,
    tickLabels: msToSecondLabel,
  },
  {
    tickIntervalMs: 60 * 1000,
    tickLabels: msToSecondLabel,
  },
  {
    tickIntervalMs: 2 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
  {
    tickIntervalMs: 5 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
  {
    tickIntervalMs: 10 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
  {
    tickIntervalMs: 20 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
  {
    tickIntervalMs: 60 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
  {
    tickIntervalMs: 6 * 60 * 60 * 1000,
    tickLabels: msToMinuteLabel,
  },
];

interface GanttChartTimescaleProps {
  scale: number;
  viewport: GanttViewport;
  layoutSize: {width: number; height: number};
  nowMs: number;
  startMs: number;
  highlightedMs: number[];
}

export const GanttChartTimescale = ({
  scale,
  viewport,
  nowMs,
  startMs,
  highlightedMs,
  layoutSize,
}: GanttChartTimescaleProps) => {
  const transform = `translate(${LEFT_INSET - viewport.left}px)`;
  const ticks: React.ReactChild[] = [];
  const lines: React.ReactChild[] = [];

  const pxPerMs = scale;
  const tickConfig = TICK_CONFIG.find((t) => t.tickIntervalMs * pxPerMs > 80);
  if (tickConfig) {
    const {tickIntervalMs, tickLabels} = tickConfig;
    const pxPerTick = tickIntervalMs * pxPerMs;
    const firstTickX = Math.floor(viewport.left / pxPerTick) * pxPerTick;

    for (let x = firstTickX; x < firstTickX + viewport.width; x += pxPerTick) {
      if (x - viewport.left < 10) {
        continue;
      }
      const ms = x / pxPerMs;
      const key = `${ms.toFixed(2)}`;
      const label = tickLabels(ms);
      lines.push(<div className="line" key={key} style={{left: x, transform}} />);
      ticks.push(
        <div className="tick" key={key} style={{left: x - TICK_LABEL_WIDTH / 2, transform}}>
          {label}
        </div>,
      );
    }
  }

  return (
    <TimescaleContainer>
      <TimescaleTicksContainer>
        {ticks}
        {highlightedMs.length === 2 && (
          <div
            key="highlight-duration"
            className="tick duration"
            style={{
              left: (highlightedMs[0] - startMs) * pxPerMs + 2,
              width: (highlightedMs[1] - highlightedMs[0]) * pxPerMs - 2,
              transform,
            }}
          >
            {formatElapsedTime(highlightedMs[1] - highlightedMs[0])}
          </div>
        )}
        {highlightedMs.map((ms, idx) => {
          const timeX = (ms - startMs) * pxPerMs;
          const labelOffset =
            idx === 0 && timeX > TICK_LABEL_WIDTH + viewport.left ? -(TICK_LABEL_WIDTH - 1) : 0;

          return (
            <div
              key={`highlight-${idx}`}
              className="tick highlight"
              style={{left: timeX + labelOffset, transform}}
            >
              {msToSubsecondLabel(ms - startMs)}
            </div>
          );
        })}
      </TimescaleTicksContainer>
      <TimescaleLinesContainer style={{width: viewport.width, height: viewport.height}}>
        {lines}
        {highlightedMs.map((ms, idx) => (
          <div
            className="line highlight"
            key={`highlight-${idx}`}
            style={{left: (ms - startMs) * pxPerMs + (idx === 0 ? -1 : 0), transform}}
          />
        ))}
        {nowMs > startMs && (
          <div
            className="fog-of-war"
            style={{
              left: (nowMs - startMs) * pxPerMs,
              width: Math.max(layoutSize.width, viewport.width) - (nowMs - startMs) * pxPerMs + 100,
              transform,
            }}
          ></div>
        )}
      </TimescaleLinesContainer>
    </TimescaleContainer>
  );
};

const TICKS_ROW_HEIGHT = 32;

const TimescaleContainer = styled.div`
  width: 100%;

  & .tick {
    position: absolute;
    padding-top: 7px;
    width: ${TICK_LABEL_WIDTH}px;
    height: ${TICKS_ROW_HEIGHT}px;
    box-sizing: border-box;
    transition: left ${CSS_DURATION}ms linear, width ${CSS_DURATION}ms linear;
    text-align: center;
  }
  & .tick.duration {
    color: ${Colors.Gray500};
    background: ${Colors.Gray100};
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  }
  & .tick.highlight {
    color: white;
    height: ${TICKS_ROW_HEIGHT + 2}px;
    background: ${Colors.Gray900};
  }
  & .line {
    position: absolute;
    border-left: 1px solid #f0f0f0;
    transition: left ${CSS_DURATION}ms linear;
    top: 0px;
    bottom: 0px;
  }
  & .line.highlight {
    border-left: 2px solid ${Colors.Gray900};
    z-index: 1111;
    top: -1px;
  }

  & .fog-of-war {
    position: absolute;
    background: ${Colors.Gray50};
    transition: left ${CSS_DURATION}ms linear;
    top: 0px;
    bottom: 0px;
    width: 100%;
  }
`;

const TimescaleTicksContainer = styled.div`
  height: ${TICKS_ROW_HEIGHT}px;
  z-index: 4;
  position: relative;
  background: ${Colors.White};
  display: flex;
  color: ${Colors.Gray500};
  font-size: 13px;
  font-family: ${FontFamily.monospace};
  box-shadow: inset 0 -1px ${Colors.KeylineGray};
  overflow: hidden;
`;

const TimescaleLinesContainer = styled.div`
  z-index: 0;
  top: ${TICKS_ROW_HEIGHT}px;
  left: 0;
  position: absolute;
  pointer-events: none;
  overflow: hidden;
`;
