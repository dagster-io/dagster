import {
  Body2,
  Box,
  ButtonGroup,
  ButtonLink,
  Checkbox,
  CursorHistoryControls,
  Spinner,
  Table,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {Timestamp} from '../../app/time/Timestamp';
import {InstigationTickStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {TickStatusTag} from '../../ticks/TickStatusTag';

import {ASSET_DAEMON_TICKS_QUERY} from './AssetDaemonTicksQuery';
import {
  AssetDaemonTicksQuery,
  AssetDaemonTicksQueryVariables,
  AssetDaemonTickFragment,
} from './types/AssetDaemonTicksQuery.types';

const PAGE_SIZE = 15;

export const AutomaterializationEvaluationHistoryTable = ({
  setSelectedTick,
  setTableView,
  setTimerange,
  setParentStatuses,
}: {
  setSelectedTick: (tick: AssetDaemonTickFragment | null) => void;
  setTableView: (view: 'evaluations' | 'runs') => void;
  setTimerange: (range?: [number, number]) => void;
  setParentStatuses: (statuses?: InstigationTickStatus[]) => void;
}) => {
  const [statuses, setStatuses] = useQueryPersistedState<Set<InstigationTickStatus>>({
    queryKey: 'statuses',
    decode: React.useCallback(({statuses}: {statuses?: string}) => {
      return new Set<InstigationTickStatus>(
        statuses
          ? JSON.parse(statuses)
          : [
              InstigationTickStatus.STARTED,
              InstigationTickStatus.SUCCESS,
              InstigationTickStatus.FAILURE,
            ],
      );
    }, []),
    encode: React.useCallback((raw: Set<InstigationTickStatus>) => {
      return {statuses: JSON.stringify(Array.from(raw))};
    }, []),
  });

  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    AssetDaemonTicksQuery,
    AssetDaemonTicksQueryVariables
  >({
    query: ASSET_DAEMON_TICKS_QUERY,
    variables: {
      statuses: React.useMemo(() => Array.from(statuses), [statuses]),
    },
    nextCursorForResult: (data) => {
      const ticks = data.autoMaterializeTicks;
      if (!ticks.length) {
        return undefined;
      }
      return ticks[PAGE_SIZE - 1]?.id;
    },
    getResultArray: (data) => {
      if (!data?.autoMaterializeTicks) {
        return [];
      }
      return data.autoMaterializeTicks;
    },
    pageSize: PAGE_SIZE,
  });
  // Only refresh if we're on the first page
  useQueryRefreshAtInterval(queryResult, 10000, !paginationProps.hasPrevCursor);

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      const ticks = queryResult.data?.autoMaterializeTicks;
      if (ticks && ticks.length) {
        const start = ticks[ticks.length - 1]?.timestamp;
        const end = ticks[0]?.endTimestamp;
        if (start && end) {
          setTimerange([start, end]);
        }
      }
    } else {
      setTimerange(undefined);
    }
  }, [paginationProps.hasPrevCursor, queryResult.data?.autoMaterializeTicks, setTimerange]);

  React.useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      setParentStatuses(Array.from(statuses));
    } else {
      setParentStatuses(undefined);
    }
  }, [paginationProps.hasPrevCursor, setParentStatuses, statuses]);

  return (
    <Box>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 12, horizontal: 24}}
        margin={{top: 32}}
        border="top"
      >
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <ButtonGroup
            activeItems={new Set(['evaluations'])}
            buttons={[
              {id: 'evaluations', label: 'Evaluations'},
              {id: 'runs', label: 'Runs'},
            ]}
            onClick={(id: 'evaluations' | 'runs') => {
              setTableView(id);
            }}
          />
          {!queryResult.data ? <Spinner purpose="body-text" /> : null}
        </Box>
        <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.STARTED}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.SUCCESS}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.FAILURE}
          />
          <StatusCheckbox
            statuses={statuses}
            setStatuses={setStatuses}
            status={InstigationTickStatus.SKIPPED}
          />
        </Box>
      </Box>
      <TableWrapper>
        <thead>
          <tr>
            <th style={{width: 120}}>Timestamp</th>
            <th style={{width: 90}}>Status</th>
            <th style={{width: 90}}>Duration</th>
            <th style={{width: 180}}>Result</th>
          </tr>
        </thead>
        <tbody>
          {/* Use previous data to stop page from jumping while new data loads */}
          {(queryResult.data || queryResult.previousData)?.autoMaterializeTicks.map(
            (tick, index) => {
              // This is a hack for ticks that get stuck in started
              const isTickStuckInStartedState =
                index !== 0 && tick.status === InstigationTickStatus.STARTED;

              return (
                <tr key={tick.id}>
                  <td>
                    <Timestamp
                      timestamp={{unix: tick.timestamp}}
                      timeFormat={{showTimezone: true}}
                    />
                  </td>
                  <td>
                    <TickStatusTag tick={tick} isStuckStarted={isTickStuckInStartedState} />
                  </td>
                  <td>
                    {isTickStuckInStartedState ? (
                      ' - '
                    ) : (
                      <TimeElapsed startUnix={tick.timestamp} endUnix={tick.endTimestamp} />
                    )}
                  </td>
                  <td>
                    {[InstigationTickStatus.SKIPPED, InstigationTickStatus.SUCCESS].includes(
                      tick.status,
                    ) ? (
                      <ButtonLink
                        onClick={() => {
                          setSelectedTick(tick);
                        }}
                      >
                        <Body2>
                          {tick.requestedAssetMaterializationCount} materializations requested
                        </Body2>
                      </ButtonLink>
                    ) : (
                      ' - '
                    )}
                  </td>
                </tr>
              );
            },
          )}
        </tbody>
      </TableWrapper>
      <div style={{paddingBottom: '16px'}}>
        <CursorHistoryControls {...paginationProps} />
      </div>
    </Box>
  );
};

const StatusLabels = {
  [InstigationTickStatus.SKIPPED]: 'None requested',
  [InstigationTickStatus.STARTED]: 'Started',
  [InstigationTickStatus.FAILURE]: 'Failed',
  [InstigationTickStatus.SUCCESS]: 'Requested',
};

function StatusCheckbox({
  status,
  statuses,
  setStatuses,
}: {
  status: InstigationTickStatus;
  statuses: Set<InstigationTickStatus>;
  setStatuses: (statuses: Set<InstigationTickStatus>) => void;
}) {
  return (
    <Checkbox
      label={StatusLabels[status]}
      checked={statuses.has(status)}
      onChange={() => {
        const newStatuses = new Set(statuses);
        if (statuses.has(status)) {
          newStatuses.delete(status);
        } else {
          newStatuses.add(status);
        }
        setStatuses(newStatuses);
      }}
    />
  );
}

const TableWrapper = styled(Table)`
  th,
  td {
    vertical-align: middle !important;
  }
`;
