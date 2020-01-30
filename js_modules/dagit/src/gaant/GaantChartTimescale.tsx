import * as React from "react";
import styled from "styled-components/macro";
import { Colors } from "@blueprintjs/core";
import { LEFT_INSET, CSS_DURATION } from "./Constants";

interface GaantChartTimescaleProps {
  scale: number;
  scrollLeft: number;
  nowMs: number;
  startMs: number;
  highlightedMs: number[];
}

const TICK_LABEL_WIDTH = 40;

export const GaantChartTimescale = ({
  scale,
  scrollLeft,
  nowMs,
  startMs,
  highlightedMs
}: GaantChartTimescaleProps) => {
  const viewportWidth = window.innerWidth;

  const pxPerMs = scale;
  const msPerTick = 1000 * (scale < 0.1 ? 5 : scale < 0.2 ? 1 : 0.5);
  const pxPerTick = msPerTick * pxPerMs;
  const transform = `translate(${LEFT_INSET - scrollLeft}px)`;

  const ticks: React.ReactChild[] = [];
  const lines: React.ReactChild[] = [];

  const labelPrecision = scale < 0.2 ? 0 : 1;
  const labelForTime = (ms: number, precision: number = labelPrecision) =>
    `${Number(ms / 1000).toFixed(precision)}s`;

  const firstTickX = Math.floor(scrollLeft / pxPerTick) * pxPerTick;

  for (let x = firstTickX; x < firstTickX + viewportWidth; x += pxPerTick) {
    if (x - scrollLeft < 10) continue;
    const label = labelForTime(x / pxPerMs);
    lines.push(
      <div className="line" key={label} style={{ left: x, transform }} />
    );
    ticks.push(
      <div className="tick" key={label} style={{ left: x - 20, transform }}>
        {label}
      </div>
    );
  }

  return (
    <TimescaleContainer>
      <TimescaleTicksContainer>
        {ticks}
        {highlightedMs.length === 2 && (
          <div
            key={`highlight-duration`}
            className="tick duration"
            style={{
              left: (highlightedMs[0] - startMs) * pxPerMs + 2,
              width: (highlightedMs[1] - highlightedMs[0]) * pxPerMs - 2,
              transform
            }}
          >
            {labelForTime(highlightedMs[1] - highlightedMs[0], 2)}
          </div>
        )}
        {highlightedMs.map((ms, idx) => {
          const timeX = (ms - startMs) * pxPerMs;
          const labelOffset =
            idx === 0 && timeX > TICK_LABEL_WIDTH + scrollLeft
              ? -(TICK_LABEL_WIDTH - 1)
              : 0;

          return (
            <div
              key={`highlight-${idx}`}
              className="tick highlight"
              style={{ left: timeX + labelOffset, transform }}
            >
              {labelForTime(ms - startMs, 2)}
            </div>
          );
        })}
      </TimescaleTicksContainer>
      <TimescaleLinesContainer>
        {lines}
        {highlightedMs.map((ms, idx) => (
          <div
            className="line highlight"
            key={`highlight-${idx}`}
            style={{ left: (ms - startMs) * pxPerMs, transform }}
          />
        ))}
        {nowMs > startMs && (
          <div
            className="fog-of-war"
            style={{ left: (nowMs - startMs) * pxPerMs, transform }}
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
    padding-top: 3px;
    width: ${TICK_LABEL_WIDTH}px;
    height: 20px;
    box-sizing: border-box;
    transition: left ${CSS_DURATION} linear, width ${CSS_DURATION} linear;
    text-align: center;
    font-size: 11px;
  }
  & .tick.duration {
    color: ${Colors.GRAY2};
    background: ${Colors.LIGHT_GRAY2};
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  }
  & .tick.highlight {
    color: white;
    margin-top: 1px;
    padding-top: 2px;
    height: 17px;
    background: linear-gradient(
      to bottom,
      ${Colors.GOLD3} 0%,
      ${Colors.GOLD2} 100%
    );
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  }
  & .line {
    position: absolute;
    border-left: 1px solid #eee;
    transition: left ${CSS_DURATION} linear;
    top: 0px;
    bottom: 0px;
  }
  & .line.highlight {
    border-left: 1px solid ${Colors.GOLD2};
    z-index: 3;
    top: -1px;
  }

  & .fog-of-war {
    position: absolute;
    background: rgba(0, 0, 0, 0.08);
    transition: left ${CSS_DURATION} linear;
    top: 0px;
    bottom: 0px;
    width: 100%;
  }
`;

const TimescaleTicksContainer = styled.div`
  height: 20px;
  z-index: 4;
  position: relative;
  background: ${Colors.LIGHT_GRAY4};
  display: flex;
  color: ${Colors.GRAY3};
  font-size: 11px;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  overflow: hidden;
`;

const TimescaleLinesContainer = styled.div`
  z-index: 0;
  bottom: 0;
  top: 0;
  left: 0;
  right: 0;
  position: absolute;
  pointer-events: none;
  overflow: hidden;
`;
