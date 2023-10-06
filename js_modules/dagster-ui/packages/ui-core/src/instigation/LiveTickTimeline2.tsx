import {Caption, Colors, Tooltip, ifPlural, useViewport} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import memoize from 'lodash/memoize';
import * as React from 'react';
import styled from 'styled-components';

import {TimeContext} from '../app/time/TimeContext';
import {browserTimezone} from '../app/time/browserTimezone';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus, InstigationType} from '../graphql/types';

import {HistoryTickFragment} from './types/TickHistory.types';

dayjs.extend(relativeTime);

const COLOR_MAP = {
  [InstigationTickStatus.SUCCESS]: Colors.Green500,
  [InstigationTickStatus.FAILURE]: Colors.Red500,
  [InstigationTickStatus.STARTED]: Colors.LightPurple,
  [InstigationTickStatus.SKIPPED]: Colors.Olive200,
};

const HoverColorMap = {
  [InstigationTickStatus.SUCCESS]: Colors.Green700,
  [InstigationTickStatus.FAILURE]: Colors.Red700,
  [InstigationTickStatus.STARTED]: Colors.Blue500,
  [InstigationTickStatus.SKIPPED]: Colors.Olive500,
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
  });
});

type StrippedDownTickFragment = Pick<
  HistoryTickFragment,
  'id' | 'timestamp' | 'instigationType'
> & {
  status: InstigationTickStatus;
  runs?: HistoryTickFragment['runs'];
  endTimestamp?: number | null;
  requestedAssetMaterializationCount?: number;
} & Pick<AssetDaemonTickFragment, 'requestedMaterializationsForAssets'>;

export const LiveTickTimeline = <T extends StrippedDownTickFragment>({
  ticks,
  onHoverTick,
  onSelectTick,
  timeRange = MINUTE * 5, // 5 minutes,
  tickGrid = MINUTE, // 1 minute
  timeAfter = MINUTE, // 1 minute
}: {
  ticks: T[];
  onHoverTick: (InstigationTick?: T) => void;
  onSelectTick: (InstigationTick: T) => void;
  timeRange?: number;
  tickGrid?: number;
  timeAfter?: number;
}) => {
  const [now, setNow] = React.useState<number>(Date.now());
  const [isPaused, setPaused] = React.useState<boolean>(false);

  React.useEffect(() => {
    const interval = setInterval(() => {
      if (!isPaused) {
        setNow(Date.now());
      }
    }, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  });

  const minX = now - timeRange;
  const maxX = now + timeAfter;
  const fullRange = maxX - minX;

  const {viewport, containerProps} = useViewport();

  const ticksReversed = React.useMemo(() => {
    // Reverse ticks to make tab order correct
    return ticks.filter((tick) => !tick.endTimestamp || tick.endTimestamp * 1000 > minX).reverse();
  }, [ticks, minX]);

  const ticksToDisplay = React.useMemo(() => {
    return ticksReversed.map((tick) => {
      const startX = getX(1000 * tick.timestamp!, viewport.width, minX, fullRange);
      const endX =
        'endTimestamp' in tick
          ? getX(
              tick.endTimestamp ? tick.endTimestamp * 1000 : now,
              viewport.width,
              minX,
              fullRange,
            )
          : 0;
      return {
        ...tick,
        width: Math.max(endX - startX, MIN_WIDTH),
        startX,
      };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minX, now, ticksReversed, fullRange, viewport.width]);

  const startTickGridX = Math.ceil(minX / tickGrid) * tickGrid;
  const gridTicks = React.useMemo(() => {
    const ticks = [];
    for (let i = startTickGridX; i <= maxX; i += 60000) {
      ticks.push({
        time: i,
        x: getX(i, viewport.width, minX, fullRange),
        showLabel: i % tickGrid === 0,
      });
    }
    return ticks;
  }, [startTickGridX, maxX, tickGrid, viewport.width, minX, fullRange]);

  const {
    timezone: [timezone],
  } = React.useContext(TimeContext);

  return (
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
          const count = tick.requestedAssetMaterializationCount ?? tick.runs?.length ?? 0;
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
  );
};

const TickTooltip = React.memo(({tick}: {tick: StrippedDownTickFragment}) => {
  const status = React.useMemo(() => {
    if (tick.status === InstigationTickStatus.FAILURE) {
      return 'Evaluation failed';
    }
    if (tick.status === InstigationTickStatus.STARTED) {
      return 'Evaluating…';
    }
    if (tick.instigationType === InstigationType.AUTO_MATERIALIZE) {
      return `${tick.requestedAssetMaterializationCount} materialization${ifPlural(
        tick.requestedAssetMaterializationCount,
        's',
      )} requested`;
    } else {
      return `${tick.runs?.length || 0} run${ifPlural(tick.runs?.length, 's')} requested`;
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
        <Caption color={Colors.Gray300}>Click for details</Caption>
      )}
    </div>
  );
});

const TicksWrapper = styled.div`
  position: relative;
  height: 100px;
  padding: 10px 2px;
  border-bottom: 1px solid ${Colors.KeylineGray};
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
  color: ${Colors.White};
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
  background: ${Colors.KeylineGray};
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
  background: ${Colors.Dark};
  &:after {
    content: 'Now';
    position: absolute;
    left: 0;
    background: ${Colors.Dark};
    color: white;
    bottom: 0;
    font-size: 12px;
    padding: 3px 4px;
  }
`;

function getX(timestamp: number, viewportWidth: number, minX: number, timeRange: number) {
  return (viewportWidth * (timestamp - minX)) / timeRange;
}
