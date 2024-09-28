import {useEffect, useMemo} from 'react';

import {
  AutomaterializationEvaluationHistoryTable,
  AutomaterializationTickStatusDisplay,
  AutomaterializationTickStatusDisplayMappings,
} from './AutomaterializationEvaluationHistoryTable';
import {AssetDaemonTickFragment} from './types/AssetDaemonTicksQuery.types';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {InstigationTickStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useCursorPaginatedQuery} from '../../runs/useCursorPaginatedQuery';
import {ASSET_SENSOR_TICKS_QUERY} from '../../sensors/AssetSensorTicksQuery';
import {
  AssetSensorTicksQuery,
  AssetSensorTicksQueryVariables,
} from '../../sensors/types/AssetSensorTicksQuery.types';
import {SensorFragment} from '../../sensors/types/SensorFragment.types';
import {RepoAddress} from '../../workspace/types';

const PAGE_SIZE = 15;

interface Props {
  repoAddress: RepoAddress;
  sensor: SensorFragment;
  setSelectedTick: (tick: AssetDaemonTickFragment | null) => void;
  setTableView: (view: 'evaluations' | 'runs') => void;
  setTimerange: (range?: [number, number]) => void;
  setParentStatuses: (statuses?: InstigationTickStatus[]) => void;
}

export const SensorAutomaterializationEvaluationHistoryTable = ({
  repoAddress,
  sensor,
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
    AssetSensorTicksQuery,
    AssetSensorTicksQueryVariables
  >({
    query: ASSET_SENSOR_TICKS_QUERY,
    variables: {
      sensorSelector: {
        sensorName: sensor.name,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
      statuses: useMemo(() => Array.from(statuses), [statuses]),
    },
    nextCursorForResult: (data) => {
      if (data?.sensorOrError.__typename === 'Sensor') {
        const ticks = data.sensorOrError.sensorState.ticks;
        if (ticks.length) {
          return ticks[PAGE_SIZE - 1]?.id;
        }
      }
      return undefined;
    },
    getResultArray: (data) => {
      if (data?.sensorOrError.__typename === 'Sensor') {
        return data.sensorOrError.sensorState.ticks;
      }
      return [];
    },
    pageSize: PAGE_SIZE,
  });

  // Only refresh if we're on the first page
  useQueryRefreshAtInterval(queryResult, 10000, !paginationProps.hasPrevCursor);

  const allTicks =
    queryResult.data?.sensorOrError?.__typename === 'Sensor'
      ? queryResult.data.sensorOrError.sensorState.ticks
      : null;

  useEffect(() => {
    if (paginationProps.hasPrevCursor) {
      if (allTicks && allTicks.length) {
        const start = allTicks[allTicks.length - 1]?.timestamp;
        const end = allTicks[0]?.endTimestamp;
        if (start && end) {
          setTimerange([start, end]);
        }
      }
    } else {
      setTimerange(undefined);
    }
  }, [allTicks, paginationProps.hasPrevCursor, setTimerange]);

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
      ticks={allTicks || []}
      paginationProps={paginationProps}
      setSelectedTick={setSelectedTick}
      tickStatus={tickStatus}
      setTickStatus={setTickStatus}
      setTableView={setTableView}
    />
  );
};
