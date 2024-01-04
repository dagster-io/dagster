import {
  Caption,
  Tooltip,
  colorAccentGrayHover,
  colorAccentGreen,
  colorAccentGreenHover,
  colorAccentLavender,
  colorAccentLavenderHover,
  colorAccentPrimary,
  colorAccentRed,
  colorAccentRedHover,
  colorAccentReversed,
  colorBackgroundDefault,
  colorBackgroundDisabled,
  colorKeylineDefault,
  colorTextLight,
  ifPlural,
  useViewport,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import memoize from 'lodash/memoize';
import * as React from 'react';
import styled from 'styled-components';

import {TimeContext} from '../app/time/TimeContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus} from '../graphql/types';

import {HistoryTickFragment} from './types/InstigationUtils.types';
import {isOldTickWithoutEndtimestamp} from './util';

dayjs.extend(relativeTime);

const COLOR_MAP = {
  [InstigationTickStatus.SUCCESS]: colorAccentGreen(),
  [InstigationTickStatus.FAILURE]: colorAccentRed(),
  [InstigationTickStatus.STARTED]: colorAccentLavender(),
  [InstigationTickStatus.SKIPPED]: colorBackgroundDisabled(),
};

const HoverColorMap = {
  [InstigationTickStatus.SUCCESS]: colorAccentGreenHover(),
  [InstigationTickStatus.FAILURE]: colorAccentRedHover(),
  [InstigationTickStatus.STARTED]: colorAccentLavenderHover(),
  [InstigationTickStatus.SKIPPED]: colorAccentGrayHover(),
};

const REFRESH_INTERVAL = 100;

const MIN_WIDTH = 8; // At least 8px wide

const MINUTE = 60000;

const timestampFormat = memoize((timezone: string) => {
  return new Intl.DateTimeFormat(navigator.language, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
    timeZone: timezone === 'Automatic' ? browserTimezone() : timezone,
    timeZoneName: 'short',
  });
});
export const LiveTickTimeline = <T extends HistoryTickFragment | AssetDaemonTickFragment>({
  ticks,
  onHoverTick,
  onSelectTick,
  exactRange,
  timeRange = MINUTE * 5, // 5 minutes,
  tickGrid = MINUTE, // 1 minute
  timeAfter = MINUTE, // 1 minute
}: {
  ticks: T[];
  onHoverTick: (InstigationTick?: T) => void;
  onSelectTick: (InstigationTick: T) => void;
  exactRange?: [number, number];
  timeRange?: number;
  tickGrid?: number;
  timeAfter?: number;
}) => {
  const [now, setNow] = React.useState<number>(Date.now());
  const [isPaused, setPaused] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (!isPaused && !exactRange) {
      const interval = setInterval(() => {
        setNow(Date.now());
      }, REFRESH_INTERVAL);
      return () => clearInterval(interval);
    }
    return () => {};
  }, [exactRange, isPaused]);

  const maxX = exactRange?.[1] ? exactRange[1] * 1000 : now + timeAfter;
  const minX = exactRange?.[0] ? exactRange[0] * 1000 : now - timeRange;

  const fullRange = maxX - minX;

  const {viewport, containerProps} = useViewport();

  const ticksReversed = React.useMemo(() => {
    // Reverse ticks to make tab order correct
    return ticks.filter((tick) => !tick.endTimestamp || tick.endTimestamp * 1000 > minX).reverse();
  }, [ticks, minX]);

  const ticksToDisplay = React.useMemo(() => {
    return ticksReversed.map((tick, i) => {
      const startX = getX(1000 * tick.timestamp!, viewport.width, minX, fullRange);
      const endTimestamp = isOldTickWithoutEndtimestamp(tick, ticksReversed.length - i)
        ? tick.timestamp
        : tick.endTimestamp
        ? tick.endTimestamp * 1000
        : now;
      const endX = getX(endTimestamp, viewport.width, minX, fullRange);
      return {
        ...tick,
        width: Math.max(endX - startX, MIN_WIDTH),
        startX,
      };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minX, now, ticksReversed, fullRange, viewport.width]);

  const timeTickGridDelta = Math.max((maxX - minX) / 25, tickGrid);
  const tickGridDelta = timeTickGridDelta / 5;
  const startTickGridX = Math.ceil(minX / tickGridDelta) * tickGridDelta;
  const gridTicks = React.useMemo(() => {
    const ticks = [];
    for (let i = startTickGridX; i <= maxX; i += tickGridDelta) {
      ticks.push({
        time: i,
        x: getX(i, viewport.width, minX, fullRange),
        showLabel: i % timeTickGridDelta === 0,
      });
    }
    return ticks;
  }, [maxX, startTickGridX, tickGridDelta, viewport.width, minX, fullRange, timeTickGridDelta]);

  const {
    timezone: [timezone],
  } = React.useContext(TimeContext);

  return (
    <div style={{marginRight: '8px'}}>
      <div {...containerProps}>
        <TicksWrapper>
          {gridTicks.map((tick) => (
            <GridTick
              key={tick.time}
              style={{
                transform: `translateX(${tick.x}px)`,
              }}
            >
              <GridTickLine />
              {tick.showLabel ? (
                <GridTickTime>
                  <Caption>{timestampFormat(timezone).format(new Date(tick.time))}</Caption>
                </GridTickTime>
              ) : null}
            </GridTick>
          ))}
          {ticksToDisplay.map((tick) => {
            const isAssetDaemonTick = 'requestedAssetMaterializationCount' in tick;
            const count =
              (isAssetDaemonTick ? tick.requestedAssetMaterializationCount : tick.runIds?.length) ??
              0;
            return (
              <Tick
                key={tick.id}
                style={{
                  transform: `translateX(${tick.startX}px)`,
                  width: `${tick.width}px`,
                }}
                status={tick.status}
                onMouseEnter={() => {
                  onHoverTick(tick);
                  setPaused(true);
                }}
                onMouseLeave={() => {
                  onHoverTick();
                  setPaused(false);
                }}
                onClick={() => {
                  onSelectTick(tick);
                }}
              >
                <Tooltip content={<TickTooltip tick={tick} />}>
                  <div style={{width: tick.width + 'px', height: '80px'}}>
                    {count > 0 ? count : null}
                  </div>
                </Tooltip>
              </Tick>
            );
          })}
          <NowIndicator
            style={{
              transform: `translateX(${getX(now, viewport.width, minX, fullRange)}px)`,
            }}
          />
        </TicksWrapper>
        <TimeAxisWrapper></TimeAxisWrapper>
      </div>
    </div>
  );
};

const TickTooltip = React.memo(({tick}: {tick: HistoryTickFragment | AssetDaemonTickFragment}) => {
  const status = React.useMemo(() => {
    if (tick.status === InstigationTickStatus.FAILURE) {
      return 'Evaluation failed';
    }
    if (tick.status === InstigationTickStatus.STARTED) {
      return 'Evaluating…';
    }
    const isAssetDaemonTick = 'requestedAssetMaterializationCount' in tick;
    if (isAssetDaemonTick) {
      return `${tick.requestedAssetMaterializationCount} materialization${ifPlural(
        tick.requestedAssetMaterializationCount,
        '',
        's',
      )} requested`;
    } else {
      return `${tick.runs?.length || 0} run${ifPlural(tick.runs?.length, '', 's')} requested`;
    }
  }, [tick]);
  const startTime = dayjs(1000 * tick.timestamp!);
  const endTime = dayjs(tick.endTimestamp ? 1000 * tick.endTimestamp : Date.now());
  const elapsedTime = startTime.to(endTime, true);
  return (
    <div>
      <Caption as="div">
        {status} ({elapsedTime})
      </Caption>
      {tick.status === InstigationTickStatus.STARTED ? null : (
        <Caption color={colorTextLight()}>Click for details</Caption>
      )}
    </div>
  );
});

const TicksWrapper = styled.div`
  position: relative;
  height: 100px;
  padding: 10px 2px;
  border-bottom: 1px solid ${colorKeylineDefault()};
`;

const TimeAxisWrapper = styled.div`
  height: 24px;
`;

const Tick = styled.div<{status: InstigationTickStatus}>`
  cursor: pointer;
  position: absolute;
  top: 10px;
  height: 80px;
  will-change: transform, width;
  border-radius: 2px;
  div {
    place-content: center;
    display: grid;
  }
  color: ${colorBackgroundDefault()};
  ${({status}) => `
    background: ${COLOR_MAP[status]};
    &:hover {
      background: ${HoverColorMap[status]};
    }
  `}
`;

const GridTick = styled.div`
  position: absolute;
  top: 0;
  height: 124px;
  will-change: transform;
`;
const GridTickLine = styled.div`
  position: absolute;
  top: 0;
  height: 108px;
  width: 1px;
  background: ${colorKeylineDefault()};
`;
const GridTickTime = styled.div`
  height: 16px;
  position: absolute;
  bottom: 0;
  width: 100px;
  margin-left: -24px;
`;

const NowIndicator = styled.div`
  position: absolute;
  top: 0;
  height: 126px;
  width: 2px;
  background: ${colorAccentPrimary()};
  &:after {
    content: 'Now';
    position: absolute;
    left: 0;
    background: ${colorAccentPrimary()};
    color: ${colorAccentReversed()};
    bottom: 0;
    font-size: 12px;
    padding: 3px 4px;
  }
`;

function getX(timestamp: number, viewportWidth: number, minX: number, timeRange: number) {
  return (viewportWidth * (timestamp - minX)) / timeRange;
}
