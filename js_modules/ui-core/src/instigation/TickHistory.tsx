import 'chartjs-adapter-date-fns';

import {
  Box,
  Button,
  ButtonLink,
  CursorHistoryControls,
  FontFamily,
  Icon,
  Menu,
  MenuItem,
  MiddleTruncate,
  NonIdealState,
  Select,
  Spinner,
  SpinnerWithText,
  Table,
  Text,
  ifPlural,
} from '@dagster-io/ui-components';
import {Chart} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';
import {useState} from 'react';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {
  HISTORY_TICK_FRAGMENT,
  RUN_STATUS_FRAGMENT,
  RunStatusLink,
  TIMELINE_TICK_FRAGMENT,
  labelForRequestedMaterializationsAndJobRuns,
} from './InstigationUtils';
import {LiveTickTimeline} from './LiveTickTimeline';
import {TickDetailsDialog} from './TickDetailsDialog';
import {LIVE_WINDOW_MS} from './TickTimelineControls';
import {HistoryTickFragment, TimelineTickFragment} from './types/InstigationUtils.types';
import {
  TickHistoryQuery,
  TickHistoryQueryVariables,
  TickTimelineQuery,
  TickTimelineQueryVariables,
} from './types/TickHistory.types';
import {countPartitionsAddedOrDeleted, isStuckStartedTick} from './util';
import {NetworkStatus, gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {
  DynamicPartitionsRequestType,
  InstigationSelector,
  InstigationTickStatus,
  InstigationType,
} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {TimeElapsed} from '../runs/TimeElapsed';
import {useCursorAccumulatedQuery} from '../runs/useCursorAccumulatedQuery';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {humanizeSensorCursor} from '../sensors/SensorDetails';
import {TickLogDialog} from '../ticks/TickLogDialog';
import {TickResultType, TickStatusTag} from '../ticks/TickStatusTag';
import {CopyIconButton} from '../ui/CopyButton';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import timelineStyles from './css/LiveTickTimeline.module.css';
import styles from './css/TickHistory.module.css';

Chart.register(zoomPlugin);

const PAGE_SIZE = 25;

// Shared by the table's pagination and by the variables below, which have to know whether a
// cursor is in play.
const TICK_CURSOR_QUERY_KEY = 'cursor';

enum TickStatusDisplay {
  ALL = 'all',
  FAILED = 'failed',
  SUCCESS = 'success',
}

const STATUS_DISPLAY_MAP = {
  [TickStatusDisplay.ALL]: [
    InstigationTickStatus.SUCCESS,
    InstigationTickStatus.FAILURE,
    InstigationTickStatus.STARTED,
    InstigationTickStatus.SKIPPED,
  ],
  [TickStatusDisplay.FAILED]: [InstigationTickStatus.FAILURE],
  [TickStatusDisplay.SUCCESS]: [InstigationTickStatus.SUCCESS],
};

interface TicksTableProps {
  name: string;
  repoAddress: RepoAddress;
  tickResultType: TickResultType;
  // Rendered above the table. Omit when the page puts these controls somewhere of its own.
  actionBarComponents?: React.ReactNode;
  // Limits the table to ticks within this window. Omit to list all ticks.
  rangeMs?: [number, number];
  // Changes whenever the user picks a different window, to restart pagination.
  windowKey?: string;
}

/**
 * Tick status filter, persisted to the querystring so the timeline and the table below it
 * always agree on what is being shown.
 */
export const useTickStatusFilter = () => {
  const [tickStatus, setTickStatus] = useQueryPersistedState<TickStatusDisplay>({
    queryKey: 'status',
    defaults: {status: TickStatusDisplay.ALL},
  });
  const statuses = React.useMemo(
    () => STATUS_DISPLAY_MAP[tickStatus] || STATUS_DISPLAY_MAP[TickStatusDisplay.ALL],
    [tickStatus],
  );
  return {tickStatus, setTickStatus, statuses};
};

export const TicksTable = ({
  name,
  repoAddress,
  actionBarComponents,
  tickResultType,
  rangeMs,
  windowKey,
}: TicksTableProps) => {
  const {tickStatus, statuses} = useTickStatusFilter();

  const [showDetailsForTick, setShowDetailsForTick] = useState<HistoryTickFragment | null>(null);
  const [showLogsForTick, setShowLogsForTick] = useState<HistoryTickFragment | null>(null);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};

  // The pagination cursor is a tick timestamp that bounds the page from above, and an
  // explicit `beforeTimestamp` takes its place rather than combining with it. So the window's
  // end is sent only for the first page; after that the cursor bounds the page and
  // `afterTimestamp` keeps it inside the window.
  const [tableCursor] = useQueryPersistedState<string | undefined>({
    queryKey: TICK_CURSOR_QUERY_KEY,
  });

  // A cursor from the previous window would land the user mid-history in the new one. The
  // reset below runs in an effect, so this render still holds the old cursor; skipping it
  // avoids a query that pairs the new window with a cursor from the old one.
  const previousWindowKey = React.useRef(windowKey);
  const windowChanged = previousWindowKey.current !== windowKey;

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    TickHistoryQuery,
    TickHistoryQueryVariables
  >({
    nextCursorForResult: (data) => {
      if (data.instigationStateOrError.__typename !== 'InstigationState') {
        return undefined;
      }
      return data.instigationStateOrError.ticks[PAGE_SIZE - 1]?.id;
    },
    getResultArray: (data) => {
      if (!data || data.instigationStateOrError.__typename !== 'InstigationState') {
        return [];
      }
      return data.instigationStateOrError.ticks;
    },
    variables: {
      instigationSelector,
      statuses,
      afterTimestamp: rangeMs ? rangeMs[0] / 1000 : undefined,
      beforeTimestamp: rangeMs && !tableCursor ? rangeMs[1] / 1000 : undefined,
    },
    query: TICK_HISTORY_QUERY,
    queryKey: TICK_CURSOR_QUERY_KEY,
    pageSize: PAGE_SIZE,
    skip: windowChanged,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  // Apollo clears `data` while a new set of variables is in flight, which would blank the
  // table every time the window or the page changes and collapse the page height under the
  // reader. Keeping the last result on screen leaves the rows in place until the new ones
  // land, with the loading bar below carrying the state instead.
  const data = queryResult.data ?? queryResult.previousData;
  const state = data?.instigationStateOrError;
  const ticks = React.useMemo(
    () => (state?.__typename === 'InstigationState' ? state.ticks : []),
    [state],
  );

  React.useEffect(() => {
    if (windowChanged) {
      previousWindowKey.current = windowKey;
      paginationProps.reset();
    }
    // paginationProps.reset isn't memoized
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowKey]);

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor && !ticks.length && !queryResult.loading) {
      paginationProps.reset();
    }
    // paginationProps.reset isn't memoized
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticks, queryResult.loading, paginationProps.hasPrevCursor]);

  if (!data) {
    return (
      <Box padding={{vertical: 48}}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  if (state?.__typename === 'PythonError') {
    return <PythonErrorInfo error={state} />;
  }

  if (state?.__typename === 'InstigationStateNotFoundError') {
    return (
      <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
        <NonIdealState icon="no-results" title="No ticks to display" />
      </Box>
    );
  }

  const instigationType =
    state?.__typename === 'InstigationState' ? state.instigationType : undefined;

  // An unfiltered, unwindowed view with no ticks means the sensor or schedule has never run.
  // Within a window, an empty result is ordinary and still needs its filters rendered.
  if (!ticks.length && tickStatus === TickStatusDisplay.ALL && !rangeMs) {
    return null;
  }

  return (
    <>
      {actionBarComponents ? (
        <Box padding={{vertical: 12, horizontal: 24}}>{actionBarComponents}</Box>
      ) : null}
      {/* Only a change of window, page or filter, not the background refresh, which would
      otherwise pulse the bar every fifteen seconds. */}
      <IndeterminateLoadingBar
        $loading={queryResult.networkStatus === NetworkStatus.setVariables}
      />
      {ticks.length ? (
        <Table className={styles.tableWrapper}>
          <thead>
            <tr>
              <th style={{width: 120}}>Timestamp</th>
              <th style={{width: 90}}>Status</th>
              <th style={{width: 90}}>Duration</th>
              {instigationType === InstigationType.SENSOR ? (
                <th style={{width: 120}}>Cursor</th>
              ) : null}
              <th style={{width: 180}}>Result</th>
              <th style={{width: 80}}>Logs</th>
            </tr>
          </thead>
          <tbody>
            {ticks.map((tick, index) => (
              <TickRow
                key={tick.id}
                tick={tick}
                tickResultType={tickResultType}
                instigationSelector={instigationSelector}
                index={index}
                onShowDetails={setShowDetailsForTick}
                onShowLogs={setShowLogsForTick}
              />
            ))}
          </tbody>
        </Table>
      ) : (
        <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
          <NonIdealState icon="no-results" title="No ticks to display" />
        </Box>
      )}
      {ticks.length > 0 ? (
        <div style={{marginTop: '16px'}}>
          <CursorHistoryControls {...paginationProps} />
        </div>
      ) : null}
      <TickDetailsDialog
        isOpen={!!showDetailsForTick}
        tickId={showDetailsForTick?.tickId}
        instigationSelector={instigationSelector}
        onClose={() => setShowDetailsForTick(null)}
      />
      <TickLogDialog
        isOpen={!!showLogsForTick}
        tickId={showLogsForTick?.tickId ?? null}
        timestamp={showLogsForTick?.timestamp}
        instigationSelector={instigationSelector}
        onClose={() => setShowLogsForTick(null)}
      />
    </>
  );
};

interface TickStatusFilterProps {
  status: TickStatusDisplay;
  onChange: (value: TickStatusDisplay) => void;
}

export const TickStatusFilter = ({status, onChange}: TickStatusFilterProps) => {
  const items = [
    {key: TickStatusDisplay.ALL, label: 'All ticks'},
    {key: TickStatusDisplay.SUCCESS, label: 'Requested'},
    {key: TickStatusDisplay.FAILED, label: 'Failed'},
  ];
  const activeItem = items.find(({key}) => key === status);
  return (
    <Select<(typeof items)[0]>
      popoverProps={{position: 'bottom-right'}}
      filterable={false}
      activeItem={activeItem}
      items={items}
      itemRenderer={(item, props) => {
        return (
          <MenuItem
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={item.key}
            text={item.label}
            style={{width: '300px'}}
          />
        );
      }}
      itemListRenderer={({renderItem, filteredItems}) => {
        const renderedItems = filteredItems.map(renderItem).filter(Boolean);
        return <Menu>{renderedItems}</Menu>;
      }}
      onItemSelect={(item) => onChange(item.key)}
    >
      <Button
        rightIcon={<Icon name="arrow_drop_down" />}
        style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
      >
        {activeItem?.label}
      </Button>
    </Select>
  );
};

// A window covers an arbitrary span, so ticks are fetched a page at a time until it is
// covered. The cap keeps a pathological sensor from streaming forever.
const TIMELINE_PAGE_SIZE = 500;
const MAX_TIMELINE_PAGES = 20;

type TimelineProps = {
  name: string;
  repoAddress: RepoAddress;
  tickResultType: TickResultType;
  onHighlightRunIds?: (runIds: string[]) => void;
  statuses?: InstigationTickStatus[];
};

/**
 * Shows ticks over the given window, or the live view of the last few minutes when no window
 * is given.
 */
export const TickHistoryTimeline = ({
  rangeMs,
  ...props
}: TimelineProps & {rangeMs?: [number, number]}) =>
  rangeMs ? <WindowedTicks rangeMs={rangeMs} {...props} /> : <LiveTicks {...props} />;

const LiveTicks = ({statuses, ...props}: TimelineProps) => {
  const instigationSelector = useInstigationSelector(props.repoAddress, props.name);
  const [pollingPaused, pausePolling] = React.useState(false);

  // Snapshotted at mount so the query variables stay referentially stable across renders;
  // polling keeps the data fresh.
  const afterTimestamp = React.useMemo(() => Date.now() / 1000 - LIVE_WINDOW_MS / 1000, []);

  const queryResult = useQuery<TickTimelineQuery, TickTimelineQueryVariables>(TICK_TIMELINE_QUERY, {
    variables: {instigationSelector, afterTimestamp, statuses, limit: PAGE_SIZE},
    notifyOnNetworkStatusChange: true,
  });
  useQueryRefreshAtInterval(queryResult, 1000, !pollingPaused);

  const state = queryResult.data?.instigationStateOrError;
  const ticks = React.useMemo(() => {
    if (!state) {
      return null;
    }
    return state.__typename === 'InstigationState' ? state.ticks : [];
  }, [state]);

  return (
    <TickTimelineView
      {...props}
      instigationSelector={instigationSelector}
      ticks={ticks}
      error={state?.__typename === 'PythonError' ? state : null}
      onHoverChange={pausePolling}
    />
  );
};

const WindowedTicks = ({
  rangeMs,
  statuses,
  ...props
}: TimelineProps & {rangeMs: [number, number]}) => {
  const instigationSelector = useInstigationSelector(props.repoAddress, props.name);
  const {fetched, error} = useTimelineTicks({instigationSelector, rangeMs, statuses});

  const exactRange = React.useMemo(
    (): [number, number] => [rangeMs[0] / 1000, rangeMs[1] / 1000],
    [rangeMs],
  );

  return (
    <TickTimelineView
      {...props}
      instigationSelector={instigationSelector}
      ticks={fetched}
      error={error}
      exactRange={exactRange}
    />
  );
};

function useInstigationSelector(repoAddress: RepoAddress, name: string) {
  return React.useMemo(() => ({...repoAddressToSelector(repoAddress), name}), [repoAddress, name]);
}

function useTimelineTicks({
  instigationSelector,
  rangeMs,
  statuses,
}: {
  instigationSelector: InstigationSelector;
  rangeMs: [number, number];
  statuses?: InstigationTickStatus[];
}) {
  const [afterTimestamp, beforeTimestamp] = [rangeMs[0] / 1000, rangeMs[1] / 1000];

  const variables = React.useMemo(
    () => ({
      instigationSelector,
      afterTimestamp,
      limit: TIMELINE_PAGE_SIZE,
      statuses,
    }),
    [instigationSelector, afterTimestamp, statuses],
  );

  const getResult = React.useCallback((data: TickTimelineQuery) => {
    const state = data.instigationStateOrError;
    if (state.__typename === 'PythonError') {
      return {data: [], hasMore: false, cursor: undefined, error: state};
    }
    if (state.__typename !== 'InstigationState') {
      return {data: [], hasMore: false, cursor: undefined, error: undefined};
    }
    const {ticks = []} = state;
    return {
      data: ticks,
      hasMore: ticks.length === TIMELINE_PAGE_SIZE,
      // Ticks arrive newest-first, so the oldest one bounds the next page.
      cursor: ticks[ticks.length - 1]?.timestamp,
      error: undefined,
    };
  }, []);

  return useCursorAccumulatedQuery<
    TickTimelineQuery,
    TickTimelineQueryVariables,
    TimelineTickFragment,
    PythonErrorFragment
  >({
    query: TICK_TIMELINE_QUERY,
    variables,
    getResult,
    initialCursor: beforeTimestamp,
    maxPages: MAX_TIMELINE_PAGES,
  });
}

interface TickTimelineViewProps {
  instigationSelector: InstigationSelector;
  tickResultType: TickResultType;
  onHighlightRunIds?: (runIds: string[]) => void;
  // Null while the first page is still loading.
  ticks: TimelineTickFragment[] | null;
  error?: PythonErrorFragment | null;
  exactRange?: [number, number];
  onHoverChange?: (isHovered: boolean) => void;
}

const TickTimelineView = ({
  instigationSelector,
  tickResultType,
  onHighlightRunIds,
  ticks,
  error,
  exactRange,
  onHoverChange,
}: TickTimelineViewProps) => {
  const [selectedTickId, setSelectedTickId] = useQueryPersistedState<string | undefined>({
    encode: (tickId) => ({tickId}),
    decode: (qs) => (typeof qs.tickId === 'string' ? qs.tickId : undefined),
  });

  const onTickClick = (tick?: TimelineTickFragment) => {
    setSelectedTickId(tick ? tick.tickId : undefined);
  };

  const onTickHover = (tick?: TimelineTickFragment) => {
    if (tick?.runIds && onHighlightRunIds) {
      onHighlightRunIds(tick.runIds);
    }
  };

  if (error) {
    return <PythonErrorInfo error={error} />;
  }

  return (
    <>
      <TickDetailsDialog
        isOpen={!!selectedTickId}
        tickId={selectedTickId}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box border="top">
        {ticks ? (
          <LiveTickTimeline
            ticks={ticks}
            tickResultType={tickResultType}
            onHoverTick={onTickHover}
            onHoverChange={onHoverChange}
            onSelectTick={onTickClick}
            exactRange={exactRange}
          />
        ) : (
          <div className={timelineStyles.timelinePlaceholder}>
            <SpinnerWithText label="Loading ticks…" />
          </div>
        )}
      </Box>
    </>
  );
};

function TickRow({
  tick,
  tickResultType,
  index,
  onShowDetails,
  onShowLogs,
}: {
  tick: HistoryTickFragment;
  tickResultType: TickResultType;
  instigationSelector: InstigationSelector;
  index: number;
  onShowDetails: (tick: HistoryTickFragment) => void;
  onShowLogs: (tick: HistoryTickFragment) => void;
}) {
  const [addedPartitions, deletedPartitions] = React.useMemo(() => {
    const requests = tick.dynamicPartitionsRequestResults;
    const added = countPartitionsAddedOrDeleted(
      requests,
      DynamicPartitionsRequestType.ADD_PARTITIONS,
    );
    const deleted = countPartitionsAddedOrDeleted(
      requests,
      DynamicPartitionsRequestType.DELETE_PARTITIONS,
    );
    return [added, deleted];
  }, [tick?.dynamicPartitionsRequestResults]);

  const isStuckStarted = isStuckStartedTick(tick, index);

  return (
    <tr>
      <td>
        <TimestampDisplay
          timestamp={tick.timestamp}
          timeFormat={{showTimezone: false, showSeconds: true}}
        />
      </td>
      <td>
        <TickStatusTag
          tick={tick}
          tickResultType={tickResultType}
          isStuckStarted={isStuckStarted}
        />
      </td>
      <td>
        {isStuckStarted ? (
          '- '
        ) : (
          <TimeElapsed
            startUnix={tick.timestamp}
            endUnix={tick.endTimestamp || Date.now() / 1000}
          />
        )}
      </td>
      {tick.instigationType === InstigationType.SENSOR ? (
        <td>
          {tick.cursor ? (
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <div
                style={{
                  fontFamily: FontFamily.monospace,
                  fontSize: '14px',
                  maxWidth: '400px',
                  overflow: 'hidden',
                }}
              >
                <MiddleTruncate text={humanizeSensorCursor(tick.cursor) || ''} />
              </div>
              <CopyIconButton value={tick.cursor || ''} />
            </Box>
          ) : (
            <>&mdash;</>
          )}
        </td>
      ) : null}
      <td>
        <Box flex={{direction: 'column', gap: 6}}>
          {tickResultType === 'runs' ? (
            <Box flex={{alignItems: 'center', gap: 8}}>
              <ButtonLink onClick={() => onShowDetails(tick)}>
                {tick.runIds.length === 1
                  ? '1 run requested'
                  : `${tick.runIds.length} runs requested`}
              </ButtonLink>
              {tick.runs.length === 1
                ? tick.runs.map((run) => (
                    <React.Fragment key={run.id}>
                      <RunStatusLink run={run} />
                    </React.Fragment>
                  ))
                : null}
            </Box>
          ) : (
            <Box flex={{alignItems: 'center', gap: 8}}>
              <ButtonLink onClick={() => onShowDetails(tick)}>
                {labelForRequestedMaterializationsAndJobRuns(
                  tick.requestedAssetMaterializationCount,
                  tick.requestedJobRunCount,
                )}
              </ButtonLink>
            </Box>
          )}
          {addedPartitions || deletedPartitions ? (
            <Text size={12}>
              (
              {addedPartitions ? (
                <span>
                  {addedPartitions} partition{ifPlural(addedPartitions, '', 's')} created
                  {deletedPartitions ? ',' : ''}
                </span>
              ) : null}
              {deletedPartitions ? (
                <span>
                  {deletedPartitions} partition{ifPlural(deletedPartitions, '', 's')} deleted,
                </span>
              ) : null}
              )
            </Text>
          ) : null}
        </Box>
      </td>
      <td>
        <Button onClick={() => onShowLogs(tick)}>View logs</Button>
      </td>
    </tr>
  );
}

const TICK_HISTORY_QUERY = gql`
  query TickHistoryQuery(
    $instigationSelector: InstigationSelector!
    $dayRange: Int
    $limit: Int
    $cursor: String
    $statuses: [InstigationTickStatus!]
    $beforeTimestamp: Float
    $afterTimestamp: Float
  ) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        instigationType
        ticks(
          dayRange: $dayRange
          limit: $limit
          cursor: $cursor
          statuses: $statuses
          beforeTimestamp: $beforeTimestamp
          afterTimestamp: $afterTimestamp
        ) {
          id
          ...HistoryTick
        }
      }
      ...PythonErrorFragment
    }
  }

  ${RUN_STATUS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
  ${HISTORY_TICK_FRAGMENT}
`;

const TICK_TIMELINE_QUERY = gql`
  query TickTimelineQuery(
    $instigationSelector: InstigationSelector!
    $afterTimestamp: Float
    $cursor: Float
    $limit: Int
    $statuses: [InstigationTickStatus!]
  ) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        instigationType
        # The cursor is the timestamp of the oldest tick fetched so far, so each page picks
        # up where the last one ended while staying inside the requested window.
        ticks(
          afterTimestamp: $afterTimestamp
          beforeTimestamp: $cursor
          limit: $limit
          statuses: $statuses
        ) {
          id
          ...TimelineTick
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${TIMELINE_TICK_FRAGMENT}
`;
