import {useEffect, useMemo} from 'react';

import {ASSET_DAEMON_TICKS_QUERY} from './AssetDaemonTicksQuery';
import {
  AutomaterializationEvaluationHistoryTable,
  AutomaterializationTickStatusDisplay,
  AutomaterializationTickStatusDisplayMappings,
} from './AutomaterializationEvaluationHistoryTable';
import {
  AssetDaemonTickFragment,
  AssetDaemonTicksQuery,
  AssetDaemonTicksQueryVariables,
} from './types/AssetDaemonTicksQuery.types';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {InstigationTickStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';

const PAGE_SIZE = 15;

interface Props {
  setSelectedTick: (tick: AssetDaemonTickFragment | null) => void;
  setTableView: (view: 'evaluations' | 'runs') => void;
  setTimerange: (range?: [number, number]) => void;
  setParentStatuses: (statuses?: InstigationTickStatus[]) => void;
}

export const InstanceAutomaterializationEvaluationHistoryTable = ({
  setSelectedTick,
  setTableView,
  setTimerange,
  setParentStatuses,
}: Props) => {
  const [tickStatus, setTickStatus] = useQueryPersistedState<AutomaterializationTickStatusDisplay>({
    queryKey: 'status',
    defaults: {status: AutomaterializationTickStatusDisplay.ALL},
  });

  const statuses = useMemo(
    () =>
      AutomaterializationTickStatusDisplayMappings[tickStatus] ||
      AutomaterializationTickStatusDisplayMappings[AutomaterializationTickStatusDisplay.ALL],
    [tickStatus],
  );
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    AssetDaemonTicksQuery,
    AssetDaemonTicksQueryVariables
  >({
    query: ASSET_DAEMON_TICKS_QUERY,
    variables: {
      statuses: useMemo(() => Array.from(statuses), [statuses]),
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

  useEffect(() => {
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

  useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      setParentStatuses(Array.from(statuses));
    } else {
      setParentStatuses(undefined);
    }
  }, [paginationProps.hasPrevCursor, setParentStatuses, statuses]);

  return (
    <AutomaterializationEvaluationHistoryTable
      loading={queryResult.loading}
      ticks={queryResult.data?.autoMaterializeTicks || []}
      paginationProps={paginationProps}
      setSelectedTick={setSelectedTick}
      setTableView={setTableView}
      tickStatus={tickStatus}
      setTickStatus={setTickStatus}
    />
  );
};
