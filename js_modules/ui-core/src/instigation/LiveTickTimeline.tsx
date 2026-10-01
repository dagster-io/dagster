import {Box, ButtonLink, Popover, Text, Tooltip, useViewport} from '@dagster-io/ui-components';
import clsx from 'clsx';
import dayjs from 'dayjs';
import {memo, useEffect, useMemo, useState} from 'react';

import styles from './css/LiveTickTimeline.module.css';
import {Timestamp} from '../app/time/Timestamp';
import {TickResultType} from '../ticks/TickStatusTag';
import {HistoryTickFragment, TimelineTickFragment} from './types/InstigationUtils.types';
import {
  TICK_SUMMARY_RANK_QUIET,
  countForTick,
  isStuckStartedTick,
  mostSevereTickStatus,
  tickSummaryRank,
} from './util';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus} from '../graphql/types';
import {batchRunsForTimeline} from '../runs/batchRunsForTimeline';
import {buildTimeAxis} from '../ui/timeAxis';

import '../util/dayjsExtensions';

const TICK_STATUS_CLASS: Record<InstigationTickStatus, string | undefined> = {
  [InstigationTickStatus.SUCCESS]: styles.tickSuccess,
  [InstigationTickStatus.FAILURE]: styles.tickFailure,
  [InstigationTickStatus.STARTED]: styles.tickStarted,
  [InstigationTickStatus.SKIPPED]: styles.tickSkipped,
};

const REFRESH_INTERVAL = 100;

// Wider windows don't need the 10fps redraw; the now indicator moves imperceptibly.
const WINDOWED_REFRESH_INTERVAL = 1000;

const MIN_WIDTH = 8; // At least 8px wide

// Ticks closer together than this are drawn as a single batch.
const MIN_BATCH_WIDTH = 20;

// A batch popover lists at most this many ticks.
const MAX_TICKS_LISTED = 50;

// Room an axis label needs, which sets how far apart the labeled gridlines can be.
const MIN_LABEL_SPACING = 160;

// Labels closer than this to an edge get dropped rather than clipped.
const LABEL_EDGE_PADDING = 70;

// Width of the now indicator's label, which sits on whichever side has room for it.
const NOW_LABEL_WIDTH = 44;

const MINUTE = 60000;

type TimelineTick = HistoryTickFragment | AssetDaemonTickFragment | TimelineTickFragment;

interface LiveTickTimelineProps<T extends TimelineTick> {
  ticks: T[];
  tickResultType: TickResultType;
  // Receives the hovered tick, or undefined when the mark covers a batch of them.
  onHoverTick?: (InstigationTick?: T) => void;
  // Whether any mark is hovered, batched or not, for callers that pause polling underneath it.
  onHoverChange?: (isHovered: boolean) => void;
  onSelectTick: (InstigationTick: T) => void;
  exactRange?: [number, number];
  timeRange?: number;
  // Labels are never closer together than this, for data coarser than the pixels allow.
  minLabelInterval?: number;
  timeAfter?: number;
}

export const LiveTickTimeline = <T extends TimelineTick>({
  ticks,
  tickResultType,
  onHoverTick,
  onHoverChange,
  onSelectTick,
  exactRange,
  timeRange = MINUTE * 5, // 5 minutes,
  minLabelInterval = MINUTE, // 1 minute
  timeAfter = MINUTE, // 1 minute
}: LiveTickTimelineProps<T>) => {
  const [now, setNow] = useState<number>(Date.now());
  const [isPaused, setPaused] = useState<boolean>(false);

  // An explicit range that reaches the present still animates, so the now indicator and any
  // in-progress tick keep moving. A range entirely in the past is static.
  const isRangeCurrent = !exactRange || exactRange[1] * 1000 >= Date.now();

  useEffect(() => {
    if (!isPaused && isRangeCurrent) {
      const interval = setInterval(
        () => {
          setNow(Date.now());
        },
        exactRange ? WINDOWED_REFRESH_INTERVAL : REFRESH_INTERVAL,
      );
      return () => clearInterval(interval);
    }
    return () => {};
  }, [exactRange, isPaused, isRangeCurrent]);

  const maxX = exactRange?.[1] ? exactRange[1] * 1000 : now + timeAfter;
  const minX = exactRange?.[0] ? exactRange[0] * 1000 : now - timeRange;
  const showNowLine = minX < now && now < maxX;

  const fullRange = maxX - minX;

  const {viewport, containerProps} = useViewport();

  const onMarkHoverStart = (tick?: T) => {
    onHoverTick?.(tick);
    onHoverChange?.(true);
    setPaused(true);
  };

  const onMarkHoverEnd = () => {
    onHoverTick?.();
    onHoverChange?.(false);
    setPaused(false);
  };

  const ticksReversed = useMemo(() => {
    // Ticks outside the window are dropped rather than drawn past its edges, which is what a
    // previous window's ticks would do while the new window loads. Reversed for tab order.
    return ticks
      .filter(
        (tick) =>
          tick.timestamp * 1000 < maxX && (!tick.endTimestamp || tick.endTimestamp * 1000 > minX),
      )
      .reverse();
  }, [ticks, minX, maxX]);

  // A tick that hasn't ended is the only one whose width follows the clock. Separating those
  // out keeps them out of the batching below, which would otherwise re-run over the whole
  // window every time the clock advances.
  const positioned = useMemo(
    () =>
      ticksReversed.map((tick, i) => ({
        tick,
        startTime: 1000 * tick.timestamp,
        endTime: isStuckStartedTick(tick, ticksReversed.length - i - 1)
          ? 1000 * tick.timestamp
          : tick.endTimestamp
            ? tick.endTimestamp * 1000
            : null,
      })),
    [ticksReversed],
  );

  // Over a long window many ticks land on the same pixel, so ticks that would overlap are
  // drawn as a single batch and enumerated in its popover.
  const batches = useMemo(() => {
    if (!viewport.width) {
      return [];
    }
    return batchRunsForTimeline({
      runs: positioned.filter(hasEnded),
      start: minX,
      end: maxX,
      width: viewport.width,
      minChunkWidth: MIN_WIDTH,
      minMultipleWidth: MIN_BATCH_WIDTH,
    });
  }, [minX, maxX, positioned, viewport.width]);

  const runningMarks = useMemo(
    () =>
      positioned
        .filter((entry) => entry.endTime === null)
        .map(({tick, startTime}) => {
          const left = getX(startTime, viewport.width, minX, fullRange);
          // Clamped to the window's end, which the clock is past whenever the window is a
          // historical one.
          const end = getX(Math.min(now, maxX), viewport.width, minX, fullRange);
          return {tick, left, width: Math.max(end - left, MIN_WIDTH)};
        }),
    [positioned, now, maxX, minX, fullRange, viewport.width],
  );

  const axis = useMemo(
    () =>
      buildTimeAxis({
        start: minX,
        end: maxX,
        width: viewport.width,
        minLabelSpacingPx: MIN_LABEL_SPACING,
        minIntervalMs: minLabelInterval,
      }),
    [minX, maxX, viewport.width, minLabelInterval],
  );

  // Labels a minute or more apart land on whole minutes, where the seconds say nothing.
  const showSeconds = axis.intervalMs > 0 && axis.intervalMs < MINUTE;

  const nowX = getX(now, viewport.width, minX, fullRange);

  const gridTicks = useMemo(
    () =>
      axis.ticks.map(({time, isMajor}) => {
        const x = getX(time, viewport.width, minX, fullRange);
        return {
          time,
          isMajor,
          x,
          // A label centered on a line near either edge would be clipped by the viewport.
          showLabel: isMajor && x >= LABEL_EDGE_PADDING && x <= viewport.width - LABEL_EDGE_PADDING,
        };
      }),
    [axis, viewport.width, minX, fullRange],
  );

  return (
    <div style={{marginRight: '8px'}}>
      <div {...containerProps}>
        <div className={styles.ticksWrapper}>
          {gridTicks.map((tick) => (
            <div
              className={clsx(styles.gridTick, tick.isMajor && styles.gridTickMajor)}
              key={tick.time}
              style={{
                transform: `translateX(${tick.x}px)`,
              }}
            >
              <div className={styles.gridTickLine} />
              {tick.showLabel ? (
                <div className={styles.gridTickTime}>
                  <Text size={12}>
                    <Timestamp timestamp={{ms: tick.time}} timeFormat={{showSeconds}} />
                  </Text>
                </div>
              ) : null}
            </div>
          ))}
          {batches.map((batch) => {
            const [first] = batch.runs;
            if (!first) {
              return null;
            }

            if (batch.runs.length === 1) {
              return (
                <TickMark
                  key={first.tick.id}
                  tick={first.tick}
                  left={batch.left}
                  width={batch.width}
                  tickResultType={tickResultType}
                  onHoverStart={onMarkHoverStart}
                  onHoverEnd={onMarkHoverEnd}
                  onSelect={onSelectTick}
                />
              );
            }

            const batchTicks = batch.runs.map(({tick}) => tick);
            return (
              <div
                key={first.tick.id}
                className={clsx(
                  styles.tick,
                  styles.tickBatch,
                  TICK_STATUS_CLASS[mostSevereTickStatus(batchTicks)],
                )}
                style={{transform: `translateX(${batch.left}px)`, width: `${batch.width}px`}}
                onMouseEnter={() => onMarkHoverStart()}
                onMouseLeave={onMarkHoverEnd}
              >
                <Popover
                  position="bottom"
                  interactionKind="hover"
                  content={
                    <TickBatchList
                      ticks={batchTicks}
                      tickResultType={tickResultType}
                      onSelectTick={onSelectTick}
                    />
                  }
                >
                  <div className={styles.tickInner} style={{width: `${batch.width}px`}}>
                    {batch.runs.length}
                  </div>
                </Popover>
              </div>
            );
          })}
          {runningMarks.map(({tick, left, width}) => (
            <TickMark
              key={tick.id}
              tick={tick}
              left={left}
              width={width}
              tickResultType={tickResultType}
              onHoverStart={onMarkHoverStart}
              onHoverEnd={onMarkHoverEnd}
              onSelect={onSelectTick}
            />
          ))}
          {showNowLine ? (
            <div
              className={clsx(
                styles.nowIndicator,
                viewport.width - nowX < NOW_LABEL_WIDTH && styles.nowIndicatorLabelLeft,
              )}
              style={{transform: `translateX(${nowX}px)`}}
            />
          ) : null}
        </div>
        <div className={styles.timeAxisWrapper} />
      </div>
    </div>
  );
};

type PositionedTick<T> = {tick: T; startTime: number; endTime: number | null};

function hasEnded<T>(entry: PositionedTick<T>): entry is PositionedTick<T> & {endTime: number} {
  return entry.endTime !== null;
}

interface TickMarkProps<T extends TimelineTick> {
  tick: T;
  left: number;
  width: number;
  tickResultType: TickResultType;
  onHoverStart: (tick: T) => void;
  onHoverEnd: () => void;
  onSelect: (tick: T) => void;
}

const TickMark = <T extends TimelineTick>({
  tick,
  left,
  width,
  tickResultType,
  onHoverStart,
  onHoverEnd,
  onSelect,
}: TickMarkProps<T>) => (
  <div
    className={clsx(styles.tick, TICK_STATUS_CLASS[tick.status])}
    style={{transform: `translateX(${left}px)`, width: `${width}px`}}
    onMouseEnter={() => onHoverStart(tick)}
    onMouseLeave={onHoverEnd}
    onClick={() => onSelect(tick)}
  >
    <Tooltip content={<TickTooltip tick={tick} tickResultType={tickResultType} />}>
      <div className={styles.tickInner} style={{width: `${width}px`}}>
        {countForTick(tick, tickResultType) || null}
      </div>
    </Tooltip>
  </div>
);

interface TickBatchListProps<T extends TimelineTick> {
  ticks: T[];
  tickResultType: TickResultType;
  onSelectTick: (tick: T) => void;
}

const TickBatchList = <T extends TimelineTick>({
  ticks,
  tickResultType,
  onSelectTick,
}: TickBatchListProps<T>) => {
  // The list is capped, so lead with the ticks that did something — a lone failure or run
  // request among hundreds of skipped ticks is exactly what the mark's color is pointing at.
  const sorted = useMemo(
    () =>
      [...ticks].sort(
        (a, b) =>
          tickSummaryRank(a, tickResultType) - tickSummaryRank(b, tickResultType) ||
          b.timestamp - a.timestamp,
      ),
    [ticks, tickResultType],
  );
  const listed = sorted.slice(0, MAX_TICKS_LISTED);
  const remaining = sorted.length - listed.length;

  return (
    <div className={styles.batchList}>
      <Box padding={{vertical: 8, horizontal: 12}} border="bottom">
        <Text size={12} weight={600}>
          {sorted.length === 1 ? '1 tick' : `${sorted.length} ticks`}
        </Text>
      </Box>
      <div className={styles.batchListScroll}>
        {listed.map((tick, index) => {
          const previous = index > 0 ? listed[index - 1] : undefined;
          // The list is grouped rather than purely chronological, so a rule marks where the
          // ticks that did something end and the quiet ones begin.
          const startsQuietSection =
            !!previous &&
            tickSummaryRank(previous, tickResultType) < TICK_SUMMARY_RANK_QUIET &&
            tickSummaryRank(tick, tickResultType) === TICK_SUMMARY_RANK_QUIET;

          return (
            <Box
              key={tick.id}
              padding={{vertical: 4, horizontal: 12}}
              border={startsQuietSection ? 'top' : undefined}
              flex={{direction: 'row', justifyContent: 'space-between', gap: 12}}
            >
              <ButtonLink onClick={() => onSelectTick(tick)}>
                <Text size={12}>
                  <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showSeconds: true}} />
                </Text>
              </ButtonLink>
              <Text size={12} color="textLight">
                {labelForTick(tick, tickResultType)}
              </Text>
            </Box>
          );
        })}
      </div>
      {remaining > 0 ? (
        <Box padding={{vertical: 8, horizontal: 12}} border="top">
          <Text size={12} color="textLight">
            {remaining === 1 ? '1 more tick not shown' : `${remaining} more ticks not shown`}
          </Text>
        </Box>
      ) : null}
    </div>
  );
};

function labelForTick(tick: TimelineTick, tickResultType: TickResultType) {
  if (tick.status === InstigationTickStatus.FAILURE) {
    return 'Failed';
  }
  if (tick.status === InstigationTickStatus.STARTED) {
    return 'Evaluating…';
  }
  if (tick.status === InstigationTickStatus.SKIPPED) {
    return 'Skipped';
  }
  const count = countForTick(tick, tickResultType);
  if (count === 0) {
    return 'Succeeded';
  }
  if (tickResultType === 'materializations' || !('runIds' in tick)) {
    return count === 1 ? '1 materialization' : `${count} materializations`;
  }
  return count === 1 ? '1 run' : `${count} runs`;
}

interface TickTooltipProps {
  tick: TimelineTick;
  tickResultType: TickResultType;
}

const TickTooltip = memo(({tick, tickResultType}: TickTooltipProps) => {
  const status = useMemo(() => {
    if (tick.status === InstigationTickStatus.FAILURE) {
      return 'Evaluation failed';
    }
    if (tick.status === InstigationTickStatus.STARTED) {
      return 'Evaluating…';
    }
    const count = countForTick(tick, tickResultType);
    if (tickResultType === 'materializations' || !('runIds' in tick)) {
      return count === 1 ? '1 materialization requested' : `${count} materializations requested`;
    }
    return count === 1 ? '1 run requested' : `${count} runs requested`;
  }, [tick, tickResultType]);

  const startTime = dayjs(1000 * tick.timestamp);
  const endTime = dayjs(tick.endTimestamp ? 1000 * tick.endTimestamp : Date.now());
  const elapsedTime = startTime.to(endTime, true);

  return (
    <div>
      <Text size={12} as="div">
        <Timestamp timestamp={{unix: tick.timestamp}} timeFormat={{showSeconds: true}} />
      </Text>
      <Text size={12} as="div">
        {status} ({elapsedTime})
      </Text>
      {tick.status === InstigationTickStatus.STARTED ? null : (
        <Text size={12} color="textLight">
          Click for details
        </Text>
      )}
    </div>
  );
});

function getX(timestamp: number, viewportWidth: number, minX: number, timeRange: number) {
  return (viewportWidth * (timestamp - minX)) / timeRange;
}
