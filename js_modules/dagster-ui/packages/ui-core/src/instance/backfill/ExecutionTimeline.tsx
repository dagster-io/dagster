import {Box, Colors, Mono, Spinner, useViewport} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React from 'react';
import {Link} from 'react-router-dom';

import {RunStatusDot} from '../../runs/RunStatusDots';
import {
  CONSTANTS,
  RunChunk,
  RunChunks,
  TimeDividers,
  TimelineRowContainer,
} from '../../runs/RunTimeline';
import {TimelineRun} from '../../runs/RunTimelineTypes';
import {titleForRun} from '../../runs/RunUtils';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {RunBatch, batchRunsForTimeline} from '../../runs/batchRunsForTimeline';
import {mergeStatusToBackground} from '../../runs/mergeStatusToBackground';
import {Container, Inner} from '../../ui/VirtualizedTable';

const {DATE_TIME_HEIGHT, ONE_HOUR_MSEC, EMPTY_STATE_HEIGHT, LEFT_SIDE_SPACE_ALLOTTED} = CONSTANTS;

type Props = {
  loading?: boolean;
  runs: TimelineRun[];
  rangeMs: [number, number];
  annotations: {label: string; ms: number}[];
  now: number;
};

export const ExecutionTimeline = (props: Props) => {
  const {loading = false, runs, rangeMs, annotations, now} = props;
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const {
    viewport: {width, height},
    containerProps: {ref: measureRef},
  } = useViewport();

  const rowVirtualizer = useVirtualizer({
    count: runs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (_: number) => 32,
    overscan: 40,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  if (!width) {
    return <div style={{height: DATE_TIME_HEIGHT + EMPTY_STATE_HEIGHT}} ref={measureRef} />;
  }

  return (
    <>
      <Box
        padding={{left: 24}}
        border="bottom"
        flex={{direction: 'column', justifyContent: 'center'}}
        style={{
          fontSize: '16px',
          flex: `0 0 ${DATE_TIME_HEIGHT}px`,
        }}
      />
      <div style={{position: 'relative'}}>
        <TimeDividers
          now={now}
          interval={rangeMs[1] - rangeMs[0] > ONE_HOUR_MSEC * 4 ? ONE_HOUR_MSEC : ONE_HOUR_MSEC / 6}
          rangeMs={rangeMs}
          annotations={annotations}
          height={runs.length > 0 ? height : 0}
        />
      </div>
      {runs.length ? (
        <div ref={measureRef} style={{overflow: 'hidden', position: 'relative'}}>
          <Container ref={parentRef}>
            <Inner $totalHeight={totalHeight}>
              {items.map(({index, key, size, start}) => (
                <ExecutionTimelineRow
                  key={key}
                  run={runs[index]!}
                  top={start}
                  height={size}
                  range={rangeMs}
                  width={width}
                />
              ))}
            </Inner>
          </Container>
        </div>
      ) : (
        <div ref={measureRef}>
          <ExecutionTimelineEmptyOrLoading loading={loading} />
        </div>
      )}
    </>
  );
};

const ExecutionTimelineEmptyOrLoading = (props: {loading: boolean}) => {
  const {loading} = props;

  const content = () => {
    if (loading) {
      return (
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <Spinner purpose="body-text" />
          Loading runs
        </Box>
      );
    }

    return (
      <Box flex={{direction: 'column', gap: 12, alignItems: 'center'}}>
        <div>No runs were executing in this time period.</div>
      </Box>
    );
  };

  return (
    <Box
      background={Colors.backgroundDefault()}
      padding={{vertical: 24}}
      flex={{direction: 'row', justifyContent: 'center'}}
      border="top-and-bottom"
    >
      {content()}
    </Box>
  );
};

export const ExecutionTimelineRow = ({
  run,
  top,
  height,
  range,
  width: containerWidth,
}: {
  run: TimelineRun;
  top: number;
  height: number;
  range: [number, number];
  width: number;
}) => {
  const [start, end] = range;
  const width = containerWidth - LEFT_SIDE_SPACE_ALLOTTED;

  const chunk = React.useMemo(() => {
    const batches: RunBatch<TimelineRun>[] = batchRunsForTimeline({
      runs: [run],
      start,
      end,
      width,
      minChunkWidth: 4,
      minMultipleWidth: 4,
    });

    return batches[0];
  }, [run, start, end, width]);

  return (
    <TimelineRowContainer $height={height} $start={top}>
      <Box
        style={{width: LEFT_SIDE_SPACE_ALLOTTED}}
        padding={{horizontal: 24}}
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
      >
        <Box flex={{alignItems: 'center', gap: 4}}>
          <RunStatusDot status={run.status} size={12} />
          <Link to={`/runs/${run.id}`}>
            <Mono>{titleForRun(run)}</Mono>
          </Link>
        </Box>
        <TimeElapsed startUnix={run.startTime / 1000} endUnix={run.endTime / 1000} />
      </Box>
      <RunChunks>
        {chunk && (
          <RunChunk
            $background={mergeStatusToBackground(chunk.runs)}
            $multiple={false}
            style={{
              left: `${chunk.left}px`,
              width: `${chunk.width}px`,
            }}
          />
        )}
      </RunChunks>
    </TimelineRowContainer>
  );
};
