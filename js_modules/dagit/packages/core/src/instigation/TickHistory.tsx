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
  Dialog,
  Button,
  DialogFooter,
} from '@dagster-io/ui';
import {Chart} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showSharedToaster} from '../app/DomUtils';
import {useFeatureFlags} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {ONE_MONTH, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useCopyToClipboard} from '../app/browser';
import {InstigationTickStatus, InstigationType} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {DynamicPartitionRequests} from '../ticks/DynamicPartitionRequests';
import {TickLogDialog} from '../ticks/TickLogDialog';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {TickTag, TICK_TAG_FRAGMENT} from './InstigationTick';
import {RunStatusLink, RUN_STATUS_FRAGMENT} from './InstigationUtils';
import {LiveTickTimeline} from './LiveTickTimeline';
import {TickDetailsDialog} from './TickDetailsDialog';
import {
  DynamicPartitionsRequestResultFragment,
  HistoryTickFragment,
  TickHistoryQuery,
  TickHistoryQueryVariables,
} from './types/TickHistory.types';

Chart.register(zoomPlugin);

type InstigationTick = HistoryTickFragment;

const TRUNCATION_THRESHOLD = 100;
const TRUNCATION_BUFFER = 5;

const truncate = (str: string) =>
  str.length > TRUNCATION_THRESHOLD
    ? `${str.slice(0, TRUNCATION_THRESHOLD - TRUNCATION_BUFFER)}…`
    : str;

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
  const copyToClipboard = useCopyToClipboard();
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
      <Box margin={{vertical: 8, horizontal: 24}}>
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
              {instigationType === InstigationType.SENSOR ? (
                <th style={{width: 120}}>Cursor</th>
              ) : null}
              <th style={{width: 180}}>Runs</th>
              {flagSensorScheduleLogging ? <th style={{width: 180}}>Logs</th> : null}
              <th style={{width: 200}}>Requests</th>
            </tr>
          </thead>
          <tbody>
            {ticks.map((tick) => (
              <tr key={tick.id}>
                <td>
                  <TimestampDisplay
                    timestamp={tick.timestamp}
                    timeFormat={{showTimezone: false, showSeconds: true}}
                  />
                </td>
                <td>
                  <TickTag tick={tick} />
                </td>
                {instigationType === InstigationType.SENSOR ? (
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
                    tick.runs.map((run) => (
                      <React.Fragment key={run.id}>
                        <RunStatusLink run={run} />
                      </React.Fragment>
                    ))
                  ) : (
                    <>&mdash;</>
                  )}
                </td>
                {flagSensorScheduleLogging ? (
                  <td>
                    {tick.logKey ? <a onClick={() => setLogTick(tick)}>View logs</a> : <>&mdash;</>}
                  </td>
                ) : null}
                <td>
                  <DynamicPartitionRequestsCell requests={tick.dynamicPartitionsRequestResults} />
                </td>
              </tr>
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
      partialRefetch: true,
      notifyOnNetworkStatusChange: true,
    },
  );

  useQueryRefreshAtInterval(queryResult, pollingPaused ? ONE_MONTH : 1000);
  const {data} = queryResult;

  if (!data) {
    return (
      <>
        <Box
          padding={{top: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
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

  const {ticks, nextTick} = data.instigationStateOrError;

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
        timestamp={selectedTime}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Subheading>Recent ticks</Subheading>
      </Box>
      <Box border={{side: 'top', width: 1, color: Colors.KeylineGray}}>
        <LiveTickTimeline
          ticks={ticks}
          nextTick={nextTick}
          onHoverTick={onTickHover}
          onSelectTick={onTickClick}
        />
      </Box>
    </>
  );
};

function DynamicPartitionRequestsCell({
  requests,
}: {
  requests: DynamicPartitionsRequestResultFragment[];
}) {
  const [isDialogOpen, setDialogOpen] = React.useState(false);
  const nonSkipOnlyRequests = requests.filter((request) => request.partitionKeys?.length);
  if (!nonSkipOnlyRequests.length) {
    return null;
  }

  return (
    <>
      <ButtonLink
        onClick={() => {
          setDialogOpen(true);
        }}
      >
        {nonSkipOnlyRequests.length} dynamic partition change
        {nonSkipOnlyRequests.length === 1 ? '' : 's'}
      </ButtonLink>
      <Dialog
        isOpen={isDialogOpen}
        onClose={() => {
          setDialogOpen(false);
        }}
        style={{width: '60%', minWidth: '400px'}}
        icon="partition"
        title="Dynamic partition changes"
      >
        <DynamicPartitionRequests includeTitle={false} requests={nonSkipOnlyRequests} />
        <DialogFooter>
          <Button
            intent="primary"
            onClick={() => {
              setDialogOpen(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </>
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
        nextTick {
          ...NextTickForHistory
        }
        ticks(dayRange: $dayRange, limit: $limit, cursor: $cursor, statuses: $statuses) {
          id
          ...HistoryTick
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment NextTickForHistory on DryRunInstigationTick {
    timestamp
  }

  fragment HistoryTick on InstigationTick {
    id
    status
    timestamp
    cursor
    skipReason
    runIds
    runs {
      id
      status
      ...RunStatusFragment
    }
    originRunIds
    error {
      ...PythonErrorFragment
    }
    logKey
    ...TickTagFragment
    dynamicPartitionsRequestResults {
      ...DynamicPartitionsRequestResultFragment
    }
  }

  fragment DynamicPartitionsRequestResultFragment on DynamicPartitionsRequestResult {
    partitionsDefName
    partitionKeys
    skippedPartitionKeys
    type
  }

  ${RUN_STATUS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
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
