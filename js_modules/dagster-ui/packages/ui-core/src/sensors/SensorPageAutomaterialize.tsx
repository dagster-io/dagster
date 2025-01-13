import {Box, ButtonGroup, Colors, Spinner, Subtitle2} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';

import {ASSET_SENSOR_TICKS_QUERY} from './AssetSensorTicksQuery';
import {DaemonStatusForWarning, SensorInfo} from './SensorInfo';
import {useLazyQuery} from '../apollo-client';
import {
  AssetSensorTicksQuery,
  AssetSensorTicksQueryVariables,
} from './types/AssetSensorTicksQuery.types';
import {SensorFragment} from './types/SensorFragment.types';
import {useFeatureFlags} from '../app/Flags';
import {useRefreshAtInterval} from '../app/QueryRefresh';
import {AutomaterializationTickDetailDialog} from '../assets/auto-materialization/AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from '../assets/auto-materialization/AutomaterializeRunHistoryTable';
import {SensorAutomaterializationEvaluationHistoryTable} from '../assets/auto-materialization/SensorAutomaterializationEvaluationHistoryTable';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus, RunsFilter} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {LiveTickTimeline} from '../instigation/LiveTickTimeline2';
import {isStuckStartedTick} from '../instigation/util';
import {DagsterTag} from '../runs/RunTag';
import {RunsFeedTableWithFilters} from '../runs/RunsFeedTable';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const MINUTE = 60 * 1000;
const THREE_MINUTES = 3 * MINUTE;
const FIVE_MINUTES = 5 * MINUTE;
const TWENTY_MINUTES = 20 * MINUTE;

interface Props {
  repoAddress: RepoAddress;
  sensor: SensorFragment;
  loading: boolean;
  daemonStatus: DaemonStatusForWarning;
}

export const SensorPageAutomaterialize = (props: Props) => {
  const {repoAddress, sensor, loading, daemonStatus} = props;
  const {flagLegacyRunsPage} = useFeatureFlags();

  const [isPaused, setIsPaused] = useState(false);
  const [statuses, setStatuses] = useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = useState<undefined | [number, number]>(undefined);

  const getVariables = useCallback(
    (currentTime = Date.now()) => {
      if (timeRange || statuses) {
        return {
          sensorSelector: {
            sensorName: sensor.name,
            repositoryName: repoAddress.name,
            repositoryLocationName: repoAddress.location,
          },
          afterTimestamp: timeRange?.[0],
          beforeTimestamp: timeRange?.[1],
          statuses,
        };
      }
      return {
        sensorSelector: {
          sensorName: sensor.name,
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
        },
        afterTimestamp: (currentTime - TWENTY_MINUTES) / 1000,
      };
    },
    [sensor, repoAddress, statuses, timeRange],
  );

  const [fetch, queryResult] = useLazyQuery<AssetSensorTicksQuery, AssetSensorTicksQueryVariables>(
    ASSET_SENSOR_TICKS_QUERY,
  );

  const refresh = useCallback(
    async () => await fetch({variables: getVariables()}),
    [fetch, getVariables],
  );

  useRefreshAtInterval({
    refresh,
    enabled: !isPaused && !timeRange && !statuses,
    intervalMs: 2 * 1000,
    leading: true,
  });

  const [selectedTick, setSelectedTick] = useState<AssetDaemonTickFragment | null>(null);

  const [tableView, setTableView] = useQueryPersistedState<'evaluations' | 'runs'>(
    useMemo(
      () => ({
        queryKey: 'view',
        decode: ({view}) => (view === 'runs' ? 'runs' : 'evaluations'),
        encode: (raw) => {
          return {view: raw, cursor: undefined, statuses: undefined};
        },
      }),
      [],
    ),
  );

  const data = queryResult.data ?? queryResult.previousData;

  const allTicks = useMemo(() => {
    if (data?.sensorOrError.__typename === 'Sensor') {
      return data.sensorOrError.sensorState.ticks;
    }
    return [];
  }, [data]);

  const ticks = useMemo(
    () => {
      return (
        allTicks.map((tick, index) => {
          const nextTick = allTicks[index - 1];
          // For ticks that get stuck in "Started" state without an endTimestamp.
          if (nextTick && isStuckStartedTick(tick, index)) {
            const copy = {...tick};
            copy.endTimestamp = nextTick.timestamp;
            copy.status = InstigationTickStatus.FAILURE;
            return copy;
          }
          return tick;
        }) ?? []
      );
    },
    // The allTicks array changes every 2 seconds because we query every 2 seconds.
    // This would cause everything to re-render, to avoid that we memoize the ticks array that we pass around
    // using the ID and status of the ticks.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(allTicks.map((tick) => `${tick.id}:${tick.status}`))],
  );

  const onHoverTick = useCallback(
    (tick: AssetDaemonTickFragment | undefined) => {
      setIsPaused(!!tick);
    },
    [setIsPaused],
  );

  const runTableFilter: RunsFilter = useMemo(() => {
    return {
      tags: [
        {
          key: DagsterTag.RepositoryLabelTag,
          value: repoAddressAsTag(repoAddress),
        },
        {key: DagsterTag.SensorName, value: sensor.name},
      ],
    };
  }, [repoAddress, sensor]);

  const tableViewSwitch = (
    <ButtonGroup
      activeItems={new Set([tableView])}
      buttons={[
        {id: 'evaluations', label: 'Evaluations'},
        {id: 'runs', label: 'Runs'},
      ]}
      onClick={(id: 'evaluations' | 'runs') => {
        setTableView(id);
      }}
    />
  );

  return (
    <>
      <SensorInfo assetDaemonHealth={daemonStatus} padding={{vertical: 16, horizontal: 24}} />
      <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
        <Subtitle2>Evaluation timeline</Subtitle2>
      </Box>
      {!sensor && loading ? (
        <Box
          padding={{vertical: 48}}
          flex={{direction: 'row', justifyContent: 'center', gap: 12, alignItems: 'center'}}
        >
          <Spinner purpose="body-text" />
          <div style={{color: Colors.textLight()}}>Loading evaluations…</div>
        </Box>
      ) : (
        <>
          <LiveTickTimeline
            ticks={ticks}
            tickResultType="materializations"
            onHoverTick={onHoverTick}
            onSelectTick={setSelectedTick}
            exactRange={timeRange}
            timeRange={TWENTY_MINUTES}
            tickGrid={FIVE_MINUTES}
            timeAfter={THREE_MINUTES}
          />
          <AutomaterializationTickDetailDialog
            tick={selectedTick}
            isOpen={!!selectedTick}
            close={() => {
              setSelectedTick(null);
            }}
          />
          {tableView === 'evaluations' ? (
            <SensorAutomaterializationEvaluationHistoryTable
              actionBarComponents={tableViewSwitch}
              repoAddress={repoAddress}
              sensor={sensor}
              setSelectedTick={setSelectedTick}
              setParentStatuses={setStatuses}
              setTimerange={setTimerange}
            />
          ) : (
            <Box margin={{top: 32}} border="top">
              {flagLegacyRunsPage ? (
                <AutomaterializeRunHistoryTable
                  filterTags={runTableFilter.tags!}
                  setTableView={setTableView}
                />
              ) : (
                <RunsFeedTableWithFilters
                  filter={runTableFilter}
                  actionBarComponents={tableViewSwitch}
                  includeRunsFromBackfills={true}
                />
              )}
            </Box>
          )}
        </>
      )}
    </>
  );
};
