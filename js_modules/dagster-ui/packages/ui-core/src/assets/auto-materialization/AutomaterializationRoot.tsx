import {useLazyQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Page,
  Checkbox,
  Spinner,
  Subtitle2,
  Heading,
  PageHeader,
  Table,
  colorTextLight,
} from '@dagster-io/ui-components';
import React, {useLayoutEffect} from 'react';
import {Redirect} from 'react-router-dom';

import {useConfirmation} from '../../app/CustomConfirmationProvider';
import {useUnscopedPermissions} from '../../app/Permissions';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {assertUnreachable} from '../../app/Util';
import {useTrackPageView} from '../../app/analytics';
import {InstigationTickStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {LiveTickTimeline} from '../../instigation/LiveTickTimeline2';
import {isStuckStartedTick} from '../../instigation/util';
import {OverviewTabs} from '../../overview/OverviewTabs';
import {useAutomationPolicySensorFlag} from '../AutomationPolicySensorFlag';
import {useAutomaterializeDaemonStatus} from '../useAutomaterializeDaemonStatus';

import {ASSET_DAEMON_TICKS_QUERY} from './AssetDaemonTicksQuery';
import {AutomaterializationTickDetailDialog} from './AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from './AutomaterializeRunHistoryTable';
import {InstanceAutomaterializationEvaluationHistoryTable} from './InstanceAutomaterializationEvaluationHistoryTable';
import {
  AssetDaemonTicksQuery,
  AssetDaemonTicksQueryVariables,
  AssetDaemonTickFragment,
} from './types/AssetDaemonTicksQuery.types';

const MINUTE = 60 * 1000;
const THREE_MINUTES = 3 * MINUTE;
const FIVE_MINUTES = 5 * MINUTE;
const TWENTY_MINUTES = 20 * MINUTE;

// Determine whether the user is flagged to see automaterialize policies as
// sensors. If so, redirect to the Sensors overview.
export const AutomaterializationRoot = () => {
  const automaterializeSensorsFlagState = useAutomationPolicySensorFlag();
  switch (automaterializeSensorsFlagState) {
    case 'unknown':
      return <div />; // Waiting for result
    case 'has-global-amp':
      return <GlobalAutomaterializationRoot />;
    case 'has-sensor-amp':
      return <Redirect to="/overview/sensors" />;
    default:
      assertUnreachable(automaterializeSensorsFlagState);
  }
};

const GlobalAutomaterializationRoot = () => {
  useTrackPageView();

  const automaterialize = useAutomaterializeDaemonStatus();
  const confirm = useConfirmation();

  const {permissions: {canToggleAutoMaterialize} = {}} = useUnscopedPermissions();

  const [fetch, queryResult] = useLazyQuery<AssetDaemonTicksQuery, AssetDaemonTicksQueryVariables>(
    ASSET_DAEMON_TICKS_QUERY,
  );
  const [isPaused, setIsPaused] = React.useState(false);
  const [statuses, setStatuses] = React.useState<undefined | InstigationTickStatus[]>(undefined);
  const [timeRange, setTimerange] = React.useState<undefined | [number, number]>(undefined);
  const variables: AssetDaemonTicksQueryVariables = React.useMemo(() => {
    if (timeRange || statuses) {
      return {
        afterTimestamp: timeRange?.[0],
        beforeTimestamp: timeRange?.[1],
        statuses,
      };
    }
    return {
      afterTimestamp: (Date.now() - TWENTY_MINUTES) / 1000,
    };
  }, [statuses, timeRange]);
  function fetchData() {
    fetch({
      variables,
    });
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useLayoutEffect(fetchData, [variables]);
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

  const ids = data ? data.autoMaterializeTicks.map((tick) => `${tick.id}:${tick.status}`) : [];
  while (ids.length < 100) {
    // Super hacky but we need to keep the memo args length the same...
    // And the memo below prevents us from changing the ticks reference every second
    // which avoids a bunch of re-rendering
    ids.push('');
  }

  const ticks = React.useMemo(
    () => {
      const ticks = data?.autoMaterializeTicks;
      return (
        ticks?.map((tick, index) => {
          // For ticks that get stuck in "Started" state without an endTimestamp.
          if (!isStuckStartedTick(tick, index)) {
            const copy = {...tick};
            copy.endTimestamp = ticks[index - 1]!.timestamp;
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
            <InstanceAutomaterializationEvaluationHistoryTable
              setSelectedTick={setSelectedTick}
              setTableView={setTableView}
              setParentStatuses={setStatuses}
              setTimerange={setTimerange}
            />
          ) : (
            <AutomaterializeRunHistoryTable setTableView={setTableView} />
          )}
        </>
      )}
    </Page>
  );
};
