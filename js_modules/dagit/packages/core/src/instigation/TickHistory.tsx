import 'chartjs-adapter-date-fns';

import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Checkbox,
  ColorsWIP,
  CursorHistoryControls,
  NonIdealState,
  Spinner,
  Tab,
  Table,
  Tabs,
  Subheading,
  FontFamily,
  IconWIP,
  IconWrapper,
} from '@dagster-io/ui';
import {Chart} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import * as React from 'react';
import styled from 'styled-components/macro';

import {SharedToaster} from '../app/DomUtils';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useCopyToClipboard} from '../app/browser';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationTickStatus, InstigationType} from '../types/globalTypes';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {HistoricalTickTimeline} from './HistoricalTickTimeline';
import {TickTag, TICK_TAG_FRAGMENT} from './InstigationTick';
import {RunStatusLink, RUN_STATUS_FRAGMENT} from './InstigationUtils';
import {LiveTickTimeline} from './LiveTickTimeline';
import {TickDetailsDialog} from './TickDetailsDialog';
import {RunStatusFragment} from './types/RunStatusFragment';
import {
  TickHistoryQuery,
  TickHistoryQueryVariables,
  TickHistoryQuery_instigationStateOrError_InstigationState_ticks,
} from './types/TickHistoryQuery';

Chart.register(zoomPlugin);

type InstigationTick = TickHistoryQuery_instigationStateOrError_InstigationState_ticks;

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

const TABS = [
  {
    id: 'recent',
    label: 'Recent',
    range: 1,
  },
  {
    id: '1d',
    label: '1 day',
    range: 1,
  },
  {
    id: '7d',
    label: '7 days',
    range: 7,
  },
  {
    id: '14d',
    label: '14 days',
    range: 14,
  },
  {
    id: '30d',
    label: '30 days',
    range: 30,
  },
  {id: 'all', label: 'All'},
];

const MILLIS_PER_DAY = 86400 * 1000;

export const TicksTable = ({name, repoAddress}: {name: string; repoAddress: RepoAddress}) => {
  const [shownStates, setShownStates] = useQueryPersistedState<ShownStatusState>({
    encode: (states) => {
      const queryState = {};
      Object.keys(states).map((state) => {
        queryState[state.toLowerCase()] = String(states[state]);
      });
      return queryState;
    },
    decode: (queryState) => {
      const status: ShownStatusState = {...DEFAULT_SHOWN_STATUS_STATE};
      Object.keys(DEFAULT_SHOWN_STATUS_STATE).forEach((state) => {
        if (state.toLowerCase() in queryState) {
          status[state] = !(queryState[state.toLowerCase()] === 'false');
        }
      });

      return status;
    },
  });
  const copyToClipboard = useCopyToClipboard();
  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const statuses = Object.keys(shownStates)
    .filter((status) => shownStates[status])
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
  const {data} = queryResult;

  if (!data || data.instigationStateOrError.__typename === 'PythonError') {
    return null;
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
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Subheading>Tick History</Subheading>
        <Box flex={{direction: 'row', justifyContent: 'flex-end'}}>
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
                      <Box flex={{direction: 'row', alignItems: 'center'}}>
                        <Box style={{fontFamily: FontFamily.monospace, marginRight: 10}}>
                          <>{truncate(tick.cursor || '')}</>
                        </Box>
                        <CopyButton
                          onClick={() => {
                            copyToClipboard(tick.cursor || '');
                            SharedToaster.show({
                              message: <div>Copied value</div>,
                              intent: 'success',
                            });
                          }}
                        >
                          <IconWIP name="assignment" />
                        </CopyButton>
                      </Box>
                    ) : (
                      <>&mdash;</>
                    )}
                  </td>
                ) : null}
                <td>
                  {tick.runIds.length ? (
                    tick.runs.map((run: RunStatusFragment) => (
                      <>
                        <RunStatusLink key={run.id} run={run} />
                      </>
                    ))
                  ) : (
                    <>&mdash;</>
                  )}
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
  showRecent,
}: {
  name: string;
  repoAddress: RepoAddress;
  onHighlightRunIds?: (runIds: string[]) => void;
  showRecent?: boolean;
}) => {
  const [selectedTab, setSelectedTab] = useQueryPersistedState<string>({
    queryKey: 'tab',
    defaults: {tab: 'recent'},
  });
  const [selectedTime, setSelectedTime] = useQueryPersistedState<number | undefined>({
    encode: (timestamp) => ({time: timestamp}),
    decode: (qs) => (qs['time'] ? Number(qs['time']) : undefined),
  });

  const [shownStates, setShownStates] = React.useState<ShownStatusState>({
    [InstigationTickStatus.SUCCESS]: true,
    [InstigationTickStatus.FAILURE]: true,
    [InstigationTickStatus.STARTED]: true,
    [InstigationTickStatus.SKIPPED]: true,
  });
  const [pollingPaused, pausePolling] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (!showRecent && selectedTab === 'recent') {
      setSelectedTab('1d');
    }
  }, [setSelectedTab, selectedTab, showRecent]);

  const instigationSelector = {...repoAddressToSelector(repoAddress), name};
  const selectedRange = TABS.find((x) => x.id === selectedTab)?.range;
  const {data} = useQuery<TickHistoryQuery, TickHistoryQueryVariables>(JOB_TICK_HISTORY_QUERY, {
    variables: {
      instigationSelector,
      dayRange: selectedRange,
      limit: selectedTab === 'recent' ? 15 : undefined,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    pollInterval: selectedTab === 'recent' && !pollingPaused ? 1000 : 0,
  });

  const tabs = (
    <Tabs selectedTabId={selectedTab} onChange={setSelectedTab}>
      {TABS.map((tab) =>
        tab.id === 'recent' && !showRecent ? null : (
          <Tab id={tab.id} key={tab.id} title={tab.label} />
        ),
      ).filter(Boolean)}
    </Tabs>
  );

  if (!data) {
    return (
      <>
        <Box
          padding={{top: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Tick Timeline</Subheading>
          {tabs}
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

  const {ticks, nextTick, instigationType} = data.instigationStateOrError;
  const displayedTicks = ticks.filter((tick) =>
    tick.status === InstigationTickStatus.SKIPPED
      ? instigationType === InstigationType.SCHEDULE && shownStates[tick.status]
      : shownStates[tick.status],
  );
  const StatusFilter = ({status}: {status: InstigationTickStatus}) => (
    <Checkbox
      label={STATUS_TEXT_MAP[status]}
      checked={shownStates[status]}
      disabled={!ticks.filter((tick) => tick.status === status).length}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
        setShownStates({...shownStates, [status]: e.target.checked});
      }}
    />
  );
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

  const now = Date.now();

  return (
    <>
      <TickDetailsDialog
        timestamp={selectedTime}
        instigationSelector={instigationSelector}
        onClose={() => onTickClick(undefined)}
      />
      <Box padding={{top: 16, horizontal: 24}}>
        <Subheading>Tick Timeline</Subheading>
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          {tabs}
          {ticks.length ? (
            <Box flex={{direction: 'row', gap: 16}}>
              <StatusFilter status={InstigationTickStatus.SUCCESS} />
              <StatusFilter status={InstigationTickStatus.FAILURE} />
              {instigationType === InstigationType.SCHEDULE ? (
                <StatusFilter status={InstigationTickStatus.SKIPPED} />
              ) : null}
            </Box>
          ) : null}
        </Box>
      </Box>
      <Box padding={{bottom: 16}} border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}>
        {showRecent && selectedTab === 'recent' ? (
          <LiveTickTimeline
            ticks={ticks}
            nextTick={nextTick}
            onHoverTick={onTickHover}
            onSelectTick={onTickClick}
          />
        ) : displayedTicks.length ? (
          <HistoricalTickTimeline
            ticks={displayedTicks}
            selectedTick={displayedTicks.find((t) => t.timestamp === selectedTime)}
            onSelectTick={onTickClick}
            onHoverTick={onTickHover}
            selectedTab={selectedTab}
            maxBounds={
              selectedTab === 'all'
                ? undefined
                : {min: now - (selectedRange || 0) * MILLIS_PER_DAY, max: Date.now()}
            }
          />
        ) : (
          <Box padding={{vertical: 32}} flex={{justifyContent: 'center'}}>
            <NonIdealState
              icon="no-results"
              title="No ticks to display"
              description="There are no ticks within this timeframe."
            />
          </Box>
        )}
      </Box>
    </>
  );
};

const JOB_TICK_HISTORY_QUERY = gql`
  query TickHistoryQuery(
    $instigationSelector: InstigationSelector!
    $dayRange: Int
    $limit: Int
    $cursor: String
    $statuses: [InstigationTickStatus!]
  ) {
    instigationStateOrError(instigationSelector: $instigationSelector) {
      __typename
      ... on InstigationState {
        id
        instigationType
        nextTick {
          timestamp
        }
        ticks(dayRange: $dayRange, limit: $limit, cursor: $cursor, statuses: $statuses) {
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
          ...TickTagFragment
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${TICK_TAG_FRAGMENT}
  ${RUN_STATUS_FRAGMENT}
`;

const CopyButton = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 8px;
  margin: -6px;
  outline: none;

  ${IconWrapper} {
    background-color: ${ColorsWIP.Gray600};
    transition: background-color 100ms;
  }

  :hover ${IconWrapper} {
    background-color: ${ColorsWIP.Gray800};
  }

  :focus ${IconWrapper} {
    background-color: ${ColorsWIP.Link};
  }
`;
