import {useLazyQuery} from '@apollo/client';
import {Alert, Box, Spinner, Subtitle2, colorTextLight} from '@dagster-io/ui-components';
import * as React from 'react';

import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
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

import {ASSET_SENSOR_TICKS_QUERY} from './AssetSensorTicksQuery';
import {DaemonStatusForWarning, SensorInfo} from './SensorInfo';
import {
  AssetSensorTicksQuery,
  AssetSensorTicksQueryVariables,
} from './types/AssetSensorTicksQuery.types';
import {SensorFragment} from './types/SensorFragment.types';

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

  const [isPaused, setIsPaused] = React.useState(false);
  const [statuses, setStatuses] = React.useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = React.useState<undefined | [number, number]>(undefined);

  const [fetch, queryResult] = useLazyQuery<AssetSensorTicksQuery, AssetSensorTicksQueryVariables>(
    ASSET_SENSOR_TICKS_QUERY,
  );

  const variables: AssetSensorTicksQueryVariables = React.useMemo(() => {
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
      afterTimestamp: (Date.now() - TWENTY_MINUTES) / 1000,
    };
  }, [sensor, repoAddress, statuses, timeRange]);

  function fetchData() {
    fetch({
      variables,
    });
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  React.useLayoutEffect(fetchData, [variables]);
  useQueryRefreshAtInterval(queryResult, 2 * 1000, !isPaused && !timeRange && !statuses, fetchData);

  const [selectedTick, setSelectedTick] = React.useState<AssetDaemonTickFragment | null>(null);

  const [tableView, setTableView] = useQueryPersistedState<'evaluations' | 'runs'>(
    React.useMemo(
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

  const allTicks = React.useMemo(() => {
    if (data?.sensorOrError.__typename === 'Sensor') {
      return data.sensorOrError.sensorState.ticks;
    }
    return [];
  }, [data]);

  const ids = React.useMemo(() => allTicks.map((tick) => `${tick.id}:${tick.status}`), [allTicks]);

  while (ids.length < 100) {
    // Super hacky but we need to keep the memo args length the same...
    // And the memo below prevents us from changing the ticks reference every second
    // which avoids a bunch of re-rendering
    ids.push('');
  }

  const ticks = React.useMemo(
    () => {
      return (
        allTicks.map((tick, index) => {
          const nextTick = ticks[index - 1];
          // For ticks that get stuck in "Started" state without an endTimestamp.
          if (nextTick && !isStuckStartedTick(tick, index) && !tick.endTimestamp) {
            const copy = {...tick};
            copy.endTimestamp = nextTick.timestamp;
            copy.status = InstigationTickStatus.FAILURE;
            return copy;
          }
          return tick;
        }) ?? []
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...ids.slice(0, 100)],
  );

  const onHoverTick = React.useCallback(
    (tick: AssetDaemonTickFragment | undefined) => {
      setIsPaused(!!tick);
    },
    [setIsPaused],
  );

  const runTableFilterTags = React.useMemo(() => {
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
          <div style={{color: colorTextLight()}}>Loading evaluations…</div>
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
