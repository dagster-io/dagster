import 'chartjs-adapter-date-fns';

import {
  Box,
  Button,
  ButtonLink,
  Caption,
  CursorHistoryControls,
  FontFamily,
  Icon,
  Menu,
  MenuItem,
  MiddleTruncate,
  NonIdealState,
  Select,
  Spinner,
  Subheading,
  Table,
  ifPlural,
} from '@dagster-io/ui-components';
import {Chart} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';
import {useState} from 'react';
import clsx from 'clsx';

import styles from './TickHistory.module.css';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {HISTORY_TICK_FRAGMENT, RUN_STATUS_FRAGMENT, RunStatusLink} from './InstigationUtils';
import {LiveTickTimeline} from './LiveTickTimeline2';
import {TickDetailsDialog} from './TickDetailsDialog';
import {HistoryTickFragment} from './types/InstigationUtils.types';
import {TickHistoryQuery, TickHistoryQueryVariables} from './types/TickHistory.types';
import {countPartitionsAddedOrDeleted, isStuckStartedTick} from './util';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {
  DynamicPartitionsRequestType,
  InstigationSelector,
  InstigationTickStatus,
  InstigationType,
} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {TimeElapsed} from '../runs/TimeElapsed';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {humanizeSensorCursor} from '../sensors/SensorDetails';
import {TickLogDialog} from '../ticks/TickLogDialog';
import {TickResultType, TickStatusTag} from '../ticks/TickStatusTag';
import {CopyIconButton} from '../ui/CopyButton';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

Chart.register(zoomPlugin);

type InstigationTick = HistoryTickFragment;

const PAGE_SIZE = 25;

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

export const TicksTable = ({
  name,
  repoAddress,
  tabs,
  tickResultType,
  setTimerange,
  setParentStatuses,
}: {
  name: string;
  repoAddress: RepoAddress;
  tickResultType: TickResultType;
  tabs?: React.ReactElement;
  setTimerange?: (range?: [number, number]) => void;
  setParentStatuses?: (statuses?: InstigationTickStatus[]) => void;
}) => {
  const [tickStatus, setTickStatus] = useQueryPersistedState<TickStatusDisplay>({
    queryKey: 'status',
    defaults: {status: TickStatusDisplay.ALL},
  });

  const [showDetailsForTick, setShowDetailsForTick] = useState<HistoryTickFragment | null>(null);
  const [showLogsForTick, setShowLogsForTick] = useState<HistoryTickFragment | null>(null);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const statuses = React.useMemo(
    () => STATUS_DISPLAY_MAP[tickStatus] || STATUS_DISPLAY_MAP[TickStatusDisplay.ALL],
    [tickStatus],
  );

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
    },
    query: TICK_HISTORY_QUERY,
    pageSize: PAGE_SIZE,
  });

  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const state = queryResult?.data?.instigationStateOrError;
  const ticks = React.useMemo(
    () => (state?.__typename === 'InstigationState' ? state.ticks : []),
    [state],
  );

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      if (ticks && ticks.length) {
        const start = ticks[ticks.length - 1]?.timestamp;
        const end = ticks[0]?.endTimestamp;
        if (start && end) {
          setTimerange?.([start, end]);
        }
      }
    } else {
      setTimerange?.(undefined);
    }
  }, [paginationProps.hasPrevCursor, ticks, setTimerange]);

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      setParentStatuses?.(Array.from(statuses));
    } else {
      setParentStatuses?.(undefined);
    }
  }, [paginationProps.hasPrevCursor, setParentStatuses, statuses]);

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor && !ticks.length && !queryResult.loading) {
      paginationProps.reset();
    }
    // paginationProps.reset isn't memoized
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticks, queryResult.loading, paginationProps.hasPrevCursor]);

  const {data} = queryResult;

  if (!data) {
    return (
      <Box padding={{vertical: 48}}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  if (data.instigationStateOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={data.instigationStateOrError} />;
  }

  if (data.instigationStateOrError.__typename === 'InstigationStateNotFoundError') {
    return (
      <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
        <NonIdealState icon="no-results" title="No ticks to display" />
      </Box>
    );
  }

  const {instigationType} = data.instigationStateOrError;

  if (!ticks.length && tickStatus === TickStatusDisplay.ALL) {
    return null;
  }

  return (
    <>
      <Box padding={{vertical: 12, horizontal: 24}}>
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          {tabs}
          <Box flex={{direction: 'row', gap: 16}}>
            <StatusFilter status={tickStatus} onChange={setTickStatus} />
          </Box>
        </Box>
      </Box>
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
        tickResultType={tickResultType}
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

const StatusFilter = ({
  status,
  onChange,
}: {
  status: TickStatusDisplay;
  onChange: (value: TickStatusDisplay) => void;
}) => {
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

export const TickHistoryTimeline = ({
  name,
  repoAddress,
  tickResultType,
  onHighlightRunIds,
  beforeTimestamp,
  afterTimestamp,
  statuses,
}: {
  name: string;
  repoAddress: RepoAddress;
  onHighlightRunIds?: (runIds: string[]) => void;
  beforeTimestamp?: number;
  afterTimestamp?: number;
  statuses?: InstigationTickStatus[];
  tickResultType: TickResultType;
}) => {
  const [selectedTickId, setSelectedTickId] = useQueryPersistedState<string | undefined>({
    encode: (tickId) => ({tickId}),
    decode: (qs) => (typeof qs.tickId === 'string' ? qs.tickId : undefined),
  });

  const [pollingPaused, pausePolling] = React.useState<boolean>(false);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const queryResult = useQuery<TickHistoryQuery, TickHistoryQueryVariables>(TICK_HISTORY_QUERY, {
    variables: {
      instigationSelector,
      beforeTimestamp,
      afterTimestamp,
      statuses,
      limit: beforeTimestamp ? undefined : 15,
    },
    notifyOnNetworkStatusChange: true,
  });

  useQueryRefreshAtInterval(
    queryResult,
    1000,
    !(pollingPaused || (beforeTimestamp && afterTimestamp)),
  );
  const {data, error} = queryResult;

  if (!data || error) {
    return (
      <>
        <Box padding={{top: 16, horizontal: 24}} border="bottom">
          <Subheading>Recent ticks</Subheading>
        </Box>
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      </>
    );
  }

  if (data.instigationStateOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={data.instigationStateOrError} />;
  }
  if (data.instigationStateOrError.__typename === 'InstigationStateNotFoundError') {
    return null;
  }

  // Set it equal to an empty array in case of a weird error
  // https://elementl-workspace.slack.com/archives/C03CCE471E0/p1693237968395179?thread_ts=1693233109.602669&cid=C03CCE471E0
  const {ticks = []} = data.instigationStateOrError;

  const onTickClick = (tick?: InstigationTick) => {
    setSelectedTickId(tick ? tick.tickId : undefined);
  };

  const onTickHover = (tick?: InstigationTick) => {
    if (!tick) {
      pausePolling(false);
    }
    if (tick?.runIds) {
      if (onHighlightRunIds) {
        onHighlightRunIds(tick.runIds);
      }
      pausePolling(true);
    }
  };

  return (
    <>
      <TickDetailsDialog
        isOpen={!!selectedTickId}
        tickId={selectedTickId}
        tickResultType={tickResultType}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Subheading>Recent ticks</Subheading>
      </Box>
      <Box border="top">
        <LiveTickTimeline
          ticks={ticks}
          tickResultType={tickResultType}
          onHoverTick={onTickHover}
          onSelectTick={onTickClick}
          exactRange={
            beforeTimestamp && afterTimestamp ? [afterTimestamp, beforeTimestamp] : undefined
          }
        />
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
                {tick.requestedAssetMaterializationCount === 1
                  ? '1 materialization requested'
                  : `${tick.requestedAssetMaterializationCount} materializations requested`}
              </ButtonLink>
            </Box>
          )}
          {addedPartitions || deletedPartitions ? (
            <Caption>
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
            </Caption>
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

