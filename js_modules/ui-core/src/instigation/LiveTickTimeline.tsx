import {Caption, Colors, Tooltip, ifPlural, useViewport} from '@dagster-io/ui-components';
import clsx from 'clsx';
import dayjs from 'dayjs';
import {memo, useEffect, useMemo, useState} from 'react';

import styles from './css/LiveTickTimeline.module.css';
import {Timestamp} from '../app/time/Timestamp';
import {TickResultType} from '../ticks/TickStatusTag';
import {HistoryTickFragment} from './types/InstigationUtils.types';
import {isStuckStartedTick} from './util';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus} from '../graphql/types';

import '../util/dayjsExtensions';

const TICK_STATUS_CLASS: Record<InstigationTickStatus, string | undefined> = {
  [InstigationTickStatus.SUCCESS]: styles.tickSuccess,
  [InstigationTickStatus.FAILURE]: styles.tickFailure,
  [InstigationTickStatus.STARTED]: styles.tickStarted,
  [InstigationTickStatus.SKIPPED]: styles.tickSkipped,
};

const REFRESH_INTERVAL = 100;

const MIN_WIDTH = 8; // At least 8px wide

const MINUTE = 60000;

export const LiveTickTimeline = <T extends HistoryTickFragment | AssetDaemonTickFragment>({
  ticks,
  tickResultType,
  onHoverTick,
  onSelectTick,
  exactRange,
  timeRange = MINUTE * 5, // 5 minutes,
  tickGrid = MINUTE, // 1 minute
  timeAfter = MINUTE, // 1 minute
}: {
  ticks: T[];
  tickResultType: TickResultType;
  onHoverTick: (InstigationTick?: T) => void;
  onSelectTick: (InstigationTick: T) => void;
  exactRange?: [number, number];
  timeRange?: number;
  tickGrid?: number;
  timeAfter?: number;
}) => {
  const [now, setNow] = useState<number>(Date.now());
  const [isPaused, setPaused] = useState<boolean>(false);

  useEffect(() => {
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
  const showNowLine = minX < now && now < maxX;

  const fullRange = maxX - minX;

  const {viewport, containerProps} = useViewport();

  const ticksReversed = useMemo(() => {
    // Reverse ticks to make tab order correct
    return ticks.filter((tick) => !tick.endTimestamp || tick.endTimestamp * 1000 > minX).reverse();
  }, [ticks, minX]);

  const ticksToDisplay = useMemo(() => {
    return ticksReversed.map((tick, i) => {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const startX = getX(1000 * tick.timestamp!, viewport.width, minX, fullRange);
      const endTimestamp = isStuckStartedTick(tick, ticksReversed.length - i - 1)
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
  }, [minX, now, ticksReversed, fullRange, viewport.width]);

  const timeTickGridDelta = Math.max((maxX - minX) / 25, tickGrid);
  const tickGridDelta = timeTickGridDelta / 5;
  const startTickGridX = Math.ceil(minX / tickGridDelta) * tickGridDelta;
  const numTicks = Math.ceil((maxX - startTickGridX) / tickGridDelta);
  const numLabels = Math.ceil(numTicks / 5);

  const gridTicks = useMemo(() => {
    const ticks = [];
    for (let ii = 0; ii < numTicks; ii++) {
      const time = startTickGridX + ii * tickGridDelta;
      ticks.push({
        time,
        x: getX(time, viewport.width, minX, fullRange),
        showLabel: ii % numLabels === 0,
      });
    }
    return ticks;
  }, [numTicks, startTickGridX, tickGridDelta, viewport.width, minX, fullRange, numLabels]);

  return (
    <div style={{marginRight: '8px'}}>
      <div {...containerProps}>
        <div className={styles.ticksWrapper}>
          {gridTicks.map((tick) => (
            <div
              className={styles.gridTick}
              key={tick.time}
              style={{
                transform: `translateX(${tick.x}px)`,
              }}
            >
              <div className={styles.gridTickLine} />
              {tick.showLabel ? (
                <div className={styles.gridTickTime}>
                  <Caption>
                    <Timestamp timestamp={{ms: tick.time}} timeFormat={{showSeconds: true}} />
                  </Caption>
                </div>
              ) : null}
            </div>
          ))}
          {ticksToDisplay.map((tick) => {
            const count =
              (tickResultType === 'materializations' || !('runIds' in tick)
                ? tick.requestedAssetMaterializationCount
                : tick.runIds?.length) ?? 0;
            return (
              <div
                key={tick.id}
                className={clsx(styles.tick, TICK_STATUS_CLASS[tick.status])}
                style={{
                  transform: `translateX(${tick.startX}px)`,
                  width: `${tick.width}px`,
                }}
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
                <Tooltip content={<TickTooltip tick={tick} tickResultType={tickResultType} />}>
                  <div style={{width: tick.width + 'px', height: '80px'}}>
                    {count > 0 ? count : null}
                  </div>
                </Tooltip>
              </div>
            );
          })}
          {showNowLine ? (
            <div
              className={styles.nowIndicator}
              style={{
                transform: `translateX(${getX(now, viewport.width, minX, fullRange)}px)`,
              }}
            />
          ) : null}
        </div>
        <div className={styles.timeAxisWrapper} />
      </div>
    </div>
  );
};

const TickTooltip = memo(
  ({
    tick,
    tickResultType,
  }: {
    tick: HistoryTickFragment | AssetDaemonTickFragment;
    tickResultType: TickResultType;
  }) => {
    const status = useMemo(() => {
      if (tick.status === InstigationTickStatus.FAILURE) {
        return 'Evaluation failed';
      }
      if (tick.status === InstigationTickStatus.STARTED) {
        return 'Evaluating…';
      }
      if (tickResultType === 'materializations' || !('runs' in tick)) {
        return `${tick.requestedAssetMaterializationCount} materialization${ifPlural(
          tick.requestedAssetMaterializationCount,
          '',
          's',
        )} requested`;
      } else {
        return `${tick.runs?.length || 0} run${ifPlural(tick.runs?.length, '', 's')} requested`;
      }
    }, [tick, tickResultType]);

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const startTime = dayjs(1000 * tick.timestamp!);
    const endTime = dayjs(tick.endTimestamp ? 1000 * tick.endTimestamp : Date.now());
    const elapsedTime = startTime.to(endTime, true);

    return (
      <div>
        <Caption as="div">
          <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showSeconds: true}} />
        </Caption>
        <Caption as="div">
          {status} ({elapsedTime})
        </Caption>
        {tick.status === InstigationTickStatus.STARTED ? null : (
          <Caption color={Colors.textLight()}>Click for details</Caption>
        )}
      </div>
    );
  },
);

function getX(timestamp: number, viewportWidth: number, minX: number, timeRange: number) {
  return (viewportWidth * (timestamp - minX)) / timeRange;
}
