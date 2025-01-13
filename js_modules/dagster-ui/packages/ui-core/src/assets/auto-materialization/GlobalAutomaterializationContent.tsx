import {
  Box,
  ButtonGroup,
  Checkbox,
  Colors,
  Spinner,
  Subtitle2,
  Table,
} from '@dagster-io/ui-components';
import {useCallback, useEffect, useMemo, useState} from 'react';

import {ASSET_DAEMON_TICKS_QUERY} from './AssetDaemonTicksQuery';
import {AutomaterializationTickDetailDialog} from './AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from './AutomaterializeRunHistoryTable';
import {InstanceAutomaterializationEvaluationHistoryTable} from './InstanceAutomaterializationEvaluationHistoryTable';
import {
  AssetDaemonTickFragment,
  AssetDaemonTicksQuery,
  AssetDaemonTicksQueryVariables,
} from './types/AssetDaemonTicksQuery.types';
import {useLazyQuery} from '../../apollo-client';
import {useConfirmation} from '../../app/CustomConfirmationProvider';
import {useFeatureFlags} from '../../app/Flags';
import {useUnscopedPermissions} from '../../app/Permissions';
import {useRefreshAtInterval} from '../../app/QueryRefresh';
import {InstigationTickStatus, RunsFilter} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {LiveTickTimeline} from '../../instigation/LiveTickTimeline2';
import {isStuckStartedTick} from '../../instigation/util';
import {RunsFeedTableWithFilters} from '../../runs/RunsFeedTable';
import {useAutomaterializeDaemonStatus} from '../useAutomaterializeDaemonStatus';

const MINUTE = 60 * 1000;
const THREE_MINUTES = 3 * MINUTE;
const FIVE_MINUTES = 5 * MINUTE;
const TWENTY_MINUTES = 20 * MINUTE;

const RUNS_FILTER: RunsFilter = {tags: [{key: 'dagster/auto_materialize', value: 'true'}]};

export const GlobalAutomaterializationContent = () => {
  const automaterialize = useAutomaterializeDaemonStatus();
  const {flagLegacyRunsPage} = useFeatureFlags();
  const confirm = useConfirmation();

  const {permissions: {canToggleAutoMaterialize} = {}} = useUnscopedPermissions();

  const [isPaused, setIsPaused] = useState(false);
  const [statuses, setStatuses] = useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = useState<undefined | [number, number]>(undefined);

  const getVariables = useCallback(
    (now = Date.now()) => {
      if (timeRange || statuses) {
        return {
          afterTimestamp: timeRange?.[0],
          beforeTimestamp: timeRange?.[1],
          statuses,
        };
      }
      return {
        afterTimestamp: (now - TWENTY_MINUTES) / 1000,
      };
    },
    [statuses, timeRange],
  );

  const [fetch, queryResult] = useLazyQuery<AssetDaemonTicksQuery, AssetDaemonTicksQueryVariables>(
    ASSET_DAEMON_TICKS_QUERY,
  );

  const refresh = useCallback(
    async () => await fetch({variables: getVariables()}),
    [fetch, getVariables],
  );

  // When the variables have changed (e.g. due to pagination), refresh.
  useEffect(() => {
    refresh();
  }, [refresh]);

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
    return data?.autoMaterializeTicks || [];
  }, [data]);

  const ticks = useMemo(
    () => {
      return (
        allTicks?.map((tick, index) => {
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
      <Table>
        <tbody>
          <tr>
            <td>Running</td>
            <td>
              {automaterialize.loading ? (
                <Spinner purpose="body-text" />
              ) : (
                <Checkbox
                  format="switch"
                  checked={!automaterialize.paused}
                  disabled={!canToggleAutoMaterialize}
                  onChange={async (e) => {
                    const checked = e.target.checked;
                    if (!checked) {
                      await confirm({
                        title: 'Pause Auto-materializing?',
                        description:
                          'Pausing Auto-materializing will prevent new materializations triggered by an Auto-materializing policy.',
                      });
                    }
                    automaterialize.setPaused(!checked);
                  }}
                />
              )}
            </td>
          </tr>
          <tr>
            <td>Evaluation frequency</td>
            <td>~30s</td>
          </tr>
        </tbody>
      </Table>
      <Box padding={{vertical: 12, horizontal: 24}} border="bottom">
        <Subtitle2>Evaluation timeline</Subtitle2>
      </Box>
      {!data ? (
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
            <InstanceAutomaterializationEvaluationHistoryTable
              setSelectedTick={setSelectedTick}
              setParentStatuses={setStatuses}
              setTimerange={setTimerange}
              actionBarComponents={tableViewSwitch}
            />
          ) : flagLegacyRunsPage ? (
            <AutomaterializeRunHistoryTable setTableView={setTableView} />
          ) : (
            <Box margin={{top: 32}} border="top">
              <RunsFeedTableWithFilters
                filter={RUNS_FILTER}
                actionBarComponents={tableViewSwitch}
                includeRunsFromBackfills={true}
              />
            </Box>
          )}
        </>
      )}
    </>
  );
};
