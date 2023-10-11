import 'chartjs-adapter-date-fns';

import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Checkbox,
  Colors,
  CursorHistoryControls,
  NonIdealState,
  Spinner,
  Table,
  Subheading,
  FontFamily,
  Icon,
  IconWrapper,
  ButtonLink,
  ifPlural,
  Caption,
} from '@dagster-io/ui-components';
import {Chart} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';
import styled from 'styled-components';

import {showSharedToaster} from '../app/DomUtils';
import {useFeatureFlags} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {ONE_MONTH, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useCopyToClipboard} from '../app/browser';
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
import {TickLogDialog} from '../ticks/TickLogDialog';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {TICK_TAG_FRAGMENT} from './InstigationTick';
import {RunStatusLink, RUN_STATUS_FRAGMENT, HISTORY_TICK_FRAGMENT} from './InstigationUtils';
import {LiveTickTimeline} from './LiveTickTimeline2';
import {TickDetailsDialog} from './TickDetailsDialog';
import {HistoryTickFragment} from './types/InstigationUtils.types';
import {TickHistoryQuery, TickHistoryQueryVariables} from './types/TickHistory.types';
import {truncate} from './util';

Chart.register(zoomPlugin);

type InstigationTick = HistoryTickFragment;

const PAGE_SIZE = 25;
interface ShownStatusState {
  [InstigationTickStatus.SUCCESS]: boolean;
  [InstigationTickStatus.FAILURE]: boolean;
  [InstigationTickStatus.STARTED]: boolean;
  [InstigationTickStatus.SKIPPED]: boolean;
}

const DEFAULT_SHOWN_STATUS_STATE = {
  [InstigationTickStatus.SUCCESS]: true,
  [InstigationTickStatus.FAILURE]: true,
  [InstigationTickStatus.STARTED]: true,
  [InstigationTickStatus.SKIPPED]: false,
};
const STATUS_TEXT_MAP = {
  [InstigationTickStatus.SUCCESS]: 'Requested',
  [InstigationTickStatus.FAILURE]: 'Failed',
  [InstigationTickStatus.STARTED]: 'Started',
  [InstigationTickStatus.SKIPPED]: 'Skipped',
};

export const TicksTable = ({
  name,
  repoAddress,
  tabs,
}: {
  name: string;
  repoAddress: RepoAddress;
  tabs?: React.ReactElement;
}) => {
  const [shownStates, setShownStates] = useQueryPersistedState<ShownStatusState>({
    encode: (states) => {
      const queryState = {};
      Object.keys(states).map((state) => {
        (queryState as any)[state.toLowerCase()] = String(states[state as keyof typeof states]);
      });
      return queryState;
    },
    decode: (queryState) => {
      const status: ShownStatusState = {...DEFAULT_SHOWN_STATUS_STATE};
      Object.keys(DEFAULT_SHOWN_STATUS_STATE).forEach((state) => {
        if (state.toLowerCase() in queryState) {
          (status as any)[state] = !(queryState[state.toLowerCase()] === 'false');
        }
      });

      return status;
    },
  });
  const {flagSensorScheduleLogging} = useFeatureFlags();
  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const statuses = Object.keys(shownStates)
    .filter((status) => shownStates[status as keyof typeof shownStates])
    .map((status) => status as InstigationTickStatus);
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
    query: JOB_TICK_HISTORY_QUERY,
    pageSize: PAGE_SIZE,
  });
  const [logTick, setLogTick] = React.useState<InstigationTick>();
  const {data} = queryResult;

  if (!data) {
    return null;
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

  const {ticks, instigationType} = data.instigationStateOrError;

  if (!ticks.length && statuses.length === Object.keys(DEFAULT_SHOWN_STATUS_STATE).length) {
    return null;
  }

  const StatusFilter = ({status}: {status: InstigationTickStatus}) => (
    <Checkbox
      label={STATUS_TEXT_MAP[status]}
      checked={shownStates[status]}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
        setShownStates({...shownStates, [status]: e.target.checked});
      }}
    />
  );

  return (
    <>
      {logTick ? (
        <TickLogDialog
          tick={logTick}
          instigationSelector={instigationSelector}
          onClose={() => setLogTick(undefined)}
        />
      ) : null}
      <Box padding={{vertical: 8, horizontal: 24}}>
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          {tabs}
          <Box flex={{direction: 'row', gap: 16}}>
            <StatusFilter status={InstigationTickStatus.STARTED} />
            <StatusFilter status={InstigationTickStatus.SUCCESS} />
            <StatusFilter status={InstigationTickStatus.FAILURE} />
            <StatusFilter status={InstigationTickStatus.SKIPPED} />
          </Box>
        </Box>
      </Box>
      {ticks.length ? (
        <Table>
          <thead>
            <tr>
              <th style={{width: 120}}>Timestamp</th>
              <th style={{width: 90}}>Status</th>
              <th style={{width: 90}}>Duration</th>
              {instigationType === InstigationType.SENSOR ? (
                <th style={{width: 120}}>Cursor</th>
              ) : null}
              <th style={{width: 180}}>Result</th>
              {flagSensorScheduleLogging ? <th style={{width: 180}}>Logs</th> : null}
            </tr>
          </thead>
          <tbody>
            {ticks.map((tick) => (
              <TickRow
                key={tick.id}
                tick={tick}
                setLogTick={setLogTick}
                instigationSelector={instigationSelector}
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
    </>
  );
};

export const TickHistoryTimeline = ({
  name,
  repoAddress,
  onHighlightRunIds,
}: {
  name: string;
  repoAddress: RepoAddress;
  onHighlightRunIds?: (runIds: string[]) => void;
}) => {
  const [selectedTime, setSelectedTime] = useQueryPersistedState<number | undefined>({
    encode: (timestamp) => ({time: timestamp}),
    decode: (qs) => (qs['time'] ? Number(qs['time']) : undefined),
  });

  const [pollingPaused, pausePolling] = React.useState<boolean>(false);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const queryResult = useQuery<TickHistoryQuery, TickHistoryQueryVariables>(
    JOB_TICK_HISTORY_QUERY,
    {
      variables: {instigationSelector, limit: 15},
      notifyOnNetworkStatusChange: true,
    },
  );

  useQueryRefreshAtInterval(queryResult, pollingPaused ? ONE_MONTH : 1000);
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
    setSelectedTime(tick ? tick.timestamp : undefined);
  };
  const onTickHover = (tick?: InstigationTick) => {
    if (!tick) {
      pausePolling(false);
    }
    if (tick?.runIds) {
      onHighlightRunIds && onHighlightRunIds(tick.runIds);
      pausePolling(true);
    }
  };

  return (
    <>
      <TickDetailsDialog
        isOpen={!!selectedTime}
        timestamp={selectedTime}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Subheading>Recent ticks</Subheading>
      </Box>
      <Box border="top">
        <LiveTickTimeline ticks={ticks} onHoverTick={onTickHover} onSelectTick={onTickClick} />
      </Box>
    </>
  );
};

function TickRow({
  tick,
  setLogTick,
  instigationSelector,
}: {
  tick: HistoryTickFragment;
  setLogTick: (tick: InstigationTick) => void;
  instigationSelector: InstigationSelector;
}) {
  const copyToClipboard = useCopyToClipboard();
  const {flagSensorScheduleLogging} = useFeatureFlags();
  const [showResults, setShowResults] = React.useState(false);

  const [addedPartitions, deletedPartitions] = React.useMemo(() => {
    const added = tick?.dynamicPartitionsRequestResults.filter(
      (request) =>
        request.type === DynamicPartitionsRequestType.ADD_PARTITIONS &&
        request.partitionKeys?.length,
    ).length;
    const deleted = tick?.dynamicPartitionsRequestResults.filter(
      (request) =>
        request.type === DynamicPartitionsRequestType.DELETE_PARTITIONS &&
        request.partitionKeys?.length,
    ).length;
    return [added, deleted];
  }, [tick?.dynamicPartitionsRequestResults]);

  return (
    <tr>
      <td>
        <TimestampDisplay
          timestamp={tick.timestamp}
          timeFormat={{showTimezone: false, showSeconds: true}}
        />
      </td>
      <td>
        <TickStatusTag count={tick.runIds.length} status={tick.status} error={tick.error} />
      </td>
      <td>
        <TimeElapsed startUnix={tick.timestamp} endUnix={tick.endTimestamp || Date.now() / 1000} />
      </td>
      {tick.instigationType === InstigationType.SENSOR ? (
        <td style={{width: 120}}>
          {tick.cursor ? (
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <div style={{fontFamily: FontFamily.monospace, fontSize: '16px'}}>
                {truncate(tick.cursor || '')}
              </div>
              <CopyButton
                onClick={async () => {
                  copyToClipboard(tick.cursor || '');
                  await showSharedToaster({
                    message: <div>Copied value</div>,
                    intent: 'success',
                  });
                }}
              >
                <Icon name="assignment" />
              </CopyButton>
            </Box>
          ) : (
            <>&mdash;</>
          )}
        </td>
      ) : null}
      <td>
        {tick.runIds.length ? (
          <Box flex={{direction: 'column', gap: 6}}>
            <Box flex={{alignItems: 'center', gap: 8}}>
              <ButtonLink
                onClick={() => {
                  setShowResults(true);
                }}
              >
                {tick.runIds.length} run{ifPlural(tick.runIds.length, '', 's')} requested
              </ButtonLink>
              {tick.runs.length === 1
                ? tick.runs.map((run) => (
                    <React.Fragment key={run.id}>
                      <RunStatusLink run={run} />
                    </React.Fragment>
                  ))
                : null}
            </Box>
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
            <TickDetailsDialog
              isOpen={showResults}
              timestamp={tick.timestamp}
              instigationSelector={instigationSelector}
              onClose={() => {
                setShowResults(false);
              }}
            />
          </Box>
        ) : (
          <>&mdash;</>
        )}
      </td>
      {flagSensorScheduleLogging ? (
        <td>{tick.logKey ? <a onClick={() => setLogTick(tick)}>View logs</a> : <>&mdash;</>}</td>
      ) : null}
    </tr>
  );
}

const JOB_TICK_HISTORY_QUERY = gql`
  query TickHistoryQuery(
    $instigationSelector: InstigationSelector!
    $dayRange: Int
    $limit: Int
    $cursor: String
    $statuses: [InstigationTickStatus!]
  ) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      ... on InstigationState {
        id
        instigationType
        ticks(dayRange: $dayRange, limit: $limit, cursor: $cursor, statuses: $statuses) {
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

const CopyButton = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 8px;
  margin: -6px;
  outline: none;

  ${IconWrapper} {
    background-color: ${Colors.Gray600};
    transition: background-color 100ms;
  }

  :hover ${IconWrapper} {
    background-color: ${Colors.Gray800};
  }

  :focus ${IconWrapper} {
    background-color: ${Colors.Link};
  }
`;
