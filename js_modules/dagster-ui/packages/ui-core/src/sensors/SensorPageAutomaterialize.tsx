import {useLazyQuery} from '@apollo/client';
import {Alert, Box, Colors, Spinner, Subtitle2} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';

import {ASSET_SENSOR_TICKS_QUERY} from './AssetSensorTicksQuery';
import {DaemonStatusForWarning, SensorInfo} from './SensorInfo';
import {
  AssetSensorTicksQuery,
  AssetSensorTicksQueryVariables,
} from './types/AssetSensorTicksQuery.types';
import {SensorFragment} from './types/SensorFragment.types';
import {useRefreshAtInterval} from '../app/QueryRefresh';
import {AutomaterializationTickDetailDialog} from '../assets/auto-materialization/AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from '../assets/auto-materialization/AutomaterializeRunHistoryTable';
import {SensorAutomaterializationEvaluationHistoryTable} from '../assets/auto-materialization/SensorAutomaterializationEvaluationHistoryTable';
import {AssetDaemonTickFragment} from '../assets/auto-materialization/types/AssetDaemonTicksQuery.types';
import {InstigationTickStatus} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {LiveTickTimeline} from '../instigation/LiveTickTimeline2';
import {isStuckStartedTick} from '../instigation/util';
import {DagsterTag} from '../runs/RunTag';
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

  const runTableFilterTags = useMemo(() => {
    return [
      {
        key: DagsterTag.RepositoryLabelTag,
        value: repoAddressAsTag(repoAddress),
      },
      {key: DagsterTag.SensorName, value: sensor.name},
    ];
  }, [repoAddress, sensor]);

  return (
    <>
      <Box padding={{vertical: 12, horizontal: 24}} flex={{direction: 'column', gap: 12}}>
        <Alert
          intent="info"
          title="[Experimental] Dagster can automatically materialize assets when criteria are met."
          description={
            <>
              Auto-materialization enables a declarative approach to asset scheduling – instead of
              defining imperative workflows to materialize your assets, you just describe the
              conditions under which they should be materialized.{' '}
              <a
                href="https://docs.dagster.io/concepts/assets/asset-auto-execution"
                target="_blank"
                rel="noreferrer"
              >
                Learn more about auto-materialization here
              </a>
              .
            </>
          }
        />
      </Box>
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
              repoAddress={repoAddress}
              sensor={sensor}
              setSelectedTick={setSelectedTick}
              setTableView={setTableView}
              setParentStatuses={setStatuses}
              setTimerange={setTimerange}
            />
          ) : (
            <AutomaterializeRunHistoryTable
              filterTags={runTableFilterTags}
              setTableView={setTableView}
            />
          )}
        </>
      )}
    </>
  );
};
