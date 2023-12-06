import {
  FontFamily,
  colorAccentPrimary,
  colorAccentReversed,
  colorBackgroundLight,
  colorBorderDefault,
  colorKeylineDefault,
  colorShadowDefault,
  colorTextLight,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {formatElapsedTime} from '../app/Util';

import {CSS_DURATION, GanttViewport, LEFT_INSET} from './Constants';

const ONE_MIN = 60 * 1000;
const ONE_HOUR = 60 * 60 * 1000;

// If we're zoomed in to second or minute resolution but showing large values,
// switch to the "1:00:05" format used elsewhere in the Dagster UI.
const subsecondResolutionLabel = (ms: number) =>
  ms > 5 * ONE_MIN ? formatElapsedTime(ms) : `${(ms / 1000).toFixed(1)}s`;
const secondResolutionLabel = (ms: number) =>
  ms > 5 * ONE_MIN ? formatElapsedTime(ms) : `${(ms / 1000).toFixed(0)}s`;
const minuteResolutionLabel = (ms: number) =>
  ms > 59 * ONE_MIN ? formatElapsedTime(ms) : `${Math.round(ms / ONE_MIN)}m`;
const hourResolutionLabel = (ms: number) => `${Math.round(ms / ONE_HOUR)}h`;

// We want to gracefully transition the tick marks shown as you zoom, but it's
// nontrivial to programatically pick good intervals. (500ms => 1s => 5s, etc.)
// This lookup table defines the available tick mark intervals and the labeling
// that should be used for each one("2:00" or "2m" or "2s" or "0.05s", etc.).
//
// We use the first configuration that places ticks at least 80 pixels apart
// at the rendered scale.
//
const TICK_CONFIG = [
  {
    tickIntervalMs: 0.5 * 1000,
    tickLabels: subsecondResolutionLabel,
  },
  {
    tickIntervalMs: 1 * 1000,
    tickLabels: secondResolutionLabel,
  },
  {
    tickIntervalMs: 5 * 1000,
    tickLabels: secondResolutionLabel,
  },
  {
    tickIntervalMs: 10 * 1000,
    tickLabels: secondResolutionLabel,
  },
  {
    tickIntervalMs: 30 * 1000,
    tickLabels: secondResolutionLabel,
  },
  {
    tickIntervalMs: 60 * 1000,
    tickLabels: secondResolutionLabel,
  },
  {
    tickIntervalMs: 2 * 60 * 1000,
    tickLabels: minuteResolutionLabel,
  },
  {
    tickIntervalMs: 5 * 60 * 1000,
    tickLabels: minuteResolutionLabel,
  },
  {
    tickIntervalMs: 10 * 60 * 1000,
    tickLabels: minuteResolutionLabel,
  },
  {
    tickIntervalMs: 20 * 60 * 1000,
    tickLabels: minuteResolutionLabel,
  },
  {
    tickIntervalMs: 60 * 60 * 1000,
    tickLabels: hourResolutionLabel,
  },
  {
    tickIntervalMs: 3 * 60 * 60 * 1000,
    tickLabels: hourResolutionLabel,
  },
  {
    tickIntervalMs: 6 * 60 * 60 * 1000,
    tickLabels: hourResolutionLabel,
  },
  {
    tickIntervalMs: 12 * 60 * 60 * 1000,
    tickLabels: hourResolutionLabel,
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

const TICKS_ROW_HEIGHT = 32;
const TICK_LABEL_WIDTH = 56;
const MIN_PX_BETWEEN_TICKS = 80;

export const GanttChartTimescale = ({
  scale,
  viewport,
  nowMs,
  startMs,
  highlightedMs,
  layoutSize,
}: GanttChartTimescaleProps) => {
  const transform = `translate(${LEFT_INSET - viewport.left}px)`;
  const ticks: React.ReactNode[] = [];
  const lines: React.ReactNode[] = [];

  const pxPerMs = scale;
  const tickConfig = TICK_CONFIG.find((t) => t.tickIntervalMs * pxPerMs > MIN_PX_BETWEEN_TICKS);
  if (tickConfig) {
    const {tickIntervalMs, tickLabels} = tickConfig;
    const pxPerTick = tickIntervalMs * pxPerMs;

    let tickMs = Math.floor(viewport.left / pxPerTick) * tickIntervalMs;
    let tickX = tickMs * pxPerMs;

    while (tickX < viewport.left + viewport.width) {
      tickMs += tickIntervalMs;
      tickX += pxPerTick;
      if (tickX - viewport.left < 10) {
        continue;
      }
      const key = `${tickMs.toFixed(2)}`;
      const label = tickLabels(tickMs);
      lines.push(<div className="line" key={key} style={{left: tickX, transform}} />);
      ticks.push(
        <div className="tick" key={key} style={{left: tickX - TICK_LABEL_WIDTH / 2, transform}}>
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
              left: (highlightedMs[0]! - startMs) * pxPerMs + 2,
              width: (highlightedMs[1]! - highlightedMs[0]!) * pxPerMs - 2,
              transform,
            }}
          >
            {formatElapsedTime(highlightedMs[1]! - highlightedMs[0]!)}
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
              {subsecondResolutionLabel(ms - startMs)}
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

const TimescaleContainer = styled.div`
  width: 100%;

  & .tick {
    position: absolute;
    padding-top: 7px;
    width: ${TICK_LABEL_WIDTH}px;
    height: ${TICKS_ROW_HEIGHT}px;
    box-sizing: border-box;
    transition:
      left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear;
    text-align: center;
  }
  & .tick.duration {
    color: ${colorTextLight()};
    background: ${colorBackgroundLight()};
    box-shadow: 0 1px 1px ${colorShadowDefault()};
  }
  & .tick.highlight {
    color: ${colorAccentReversed()};
    height: ${TICKS_ROW_HEIGHT + 2}px;
    background: ${colorAccentPrimary()};
  }
  & .line {
    position: absolute;
    border-left: 1px solid ${colorKeylineDefault()};
    transition: left ${CSS_DURATION}ms linear;
    top: 0px;
    bottom: 0px;
  }
  & .line.highlight {
    border-left: 2px solid ${colorBorderDefault()};
    z-index: 1111;
    top: -1px;
  }

  & .fog-of-war {
    position: absolute;
    background: ${colorBackgroundLight()};
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
  background: ${colorBackgroundLight()};
  display: flex;
  color: ${colorTextLight()};
  font-size: 13px;
  font-family: ${FontFamily.monospace};
  box-shadow: inset 0 -1px ${colorKeylineDefault()};
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
