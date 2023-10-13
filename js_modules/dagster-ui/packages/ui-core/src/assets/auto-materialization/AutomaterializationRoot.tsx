import {useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Page,
  Colors,
  Checkbox,
  Spinner,
  Subtitle2,
  Heading,
  PageHeader,
  Table,
} from '@dagster-io/ui-components';
import React from 'react';

import {useConfirmation} from '../../app/CustomConfirmationProvider';
import {useUnscopedPermissions} from '../../app/Permissions';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {InstigationTickStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {LiveTickTimeline} from '../../instigation/LiveTickTimeline2';
import {OverviewTabs} from '../../overview/OverviewTabs';
import {useAutomaterializeDaemonStatus} from '../AutomaterializeDaemonStatusTag';

import {ASSET_DAMEON_TICKS_QUERY} from './AssetDaemonTicksQuery';
import {AutomaterializationEvaluationHistoryTable} from './AutomaterializationEvaluationHistoryTable';
import {AutomaterializationTickDetailDialog} from './AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from './AutomaterializeRunHistoryTable';
import {
  AssetDaemonTicksQuery,
  AssetDaemonTicksQueryVariables,
  AssetDaemonTickFragment,
} from './types/AssetDaemonTicksQuery.types';

const MINUTE = 60 * 1000;
const THREE_MINUTES = 3 * MINUTE;
const FIVE_MINUTES = 5 * MINUTE;
const TWENTY_MINUTES = 20 * MINUTE;

export const AutomaterializationRoot = () => {
  useTrackPageView();
  const automaterialize = useAutomaterializeDaemonStatus();
  const confirm = useConfirmation();

  const {permissions: {canToggleAutoMaterialize} = {}} = useUnscopedPermissions();

  const queryResult = useQuery<AssetDaemonTicksQuery, AssetDaemonTicksQueryVariables>(
    ASSET_DAMEON_TICKS_QUERY,
    {
      variables: {
        limit: 15,
      },
    },
  );
  const [isPaused, setIsPaused] = React.useState(false);
  useQueryRefreshAtInterval(queryResult, isPaused ? Infinity : 2 * 1000);

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

  const ids = queryResult.data
    ? queryResult.data.autoMaterializeTicks.map((tick) => `${tick.id}:${tick.status}`)
    : [];
  while (ids.length < 100) {
    // Super hacky but we need to keep the memo args length the same...
    // And the memo below prevents us from changing the ticks reference every second
    // which avoids a bunch of re-rendering
    ids.push('');
  }
  const ticks = React.useMemo(
    () => {
      const ticks = queryResult.data?.autoMaterializeTicks;
      return (
        ticks?.map((tick, index) => {
          // For ticks that get stuck in "Started" state without an endtimestamp.
          if (!tick.endTimestamp && index !== ticks.length - 1) {
            const copy = {...tick};
            copy.endTimestamp = ticks[index + 1]!.timestamp;
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

  return (
    <Page>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="amp" />} />
      <Box
        padding={{vertical: 12, horizontal: 24}}
        flex={{direction: 'column', gap: 12}}
        background={Colors.Gray50}
      >
        <Alert
          intent="info"
          title="[Experimental] Dagster can automatically materialize assets when criteria are met."
          description="Auto-materialization enables a declarative approach to asset scheduling – instead of defining imperative workflows to materialize your assets, you just describe the conditions under which they should be materialized. Learn more about auto-materialization here."
        />
      </Box>
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
      {!queryResult.data ? (
        <Box padding={{vertical: 48}}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          <LiveTickTimeline
            ticks={ticks}
            onHoverTick={onHoverTick}
            onSelectTick={setSelectedTick}
            timeRange={TWENTY_MINUTES}
            tickGrid={FIVE_MINUTES}
            timeAfter={THREE_MINUTES}
          />
          <AutomaterializationTickDetailDialog
            key={selectedTick?.id}
            tick={selectedTick}
            isOpen={!!selectedTick}
            close={() => {
              setSelectedTick(null);
            }}
          />
          {tableView === 'evaluations' ? (
            <AutomaterializationEvaluationHistoryTable
              setSelectedTick={setSelectedTick}
              setTableView={setTableView}
            />
          ) : (
            <AutomaterializeRunHistoryTable setTableView={setTableView} />
          )}
        </>
      )}
    </Page>
  );
};
