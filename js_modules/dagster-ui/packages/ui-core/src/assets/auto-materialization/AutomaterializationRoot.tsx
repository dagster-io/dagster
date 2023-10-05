import {gql, useQuery} from '@apollo/client';
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
  ButtonGroup,
} from '@dagster-io/ui-components';
import React from 'react';

import {useConfirmation} from '../../app/CustomConfirmationProvider';
import {useUnscopedPermissions} from '../../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {LiveTickTimeline} from '../../instigation/LiveTickTimeline2';
import {OverviewTabs} from '../../overview/OverviewTabs';
import {useAutomaterializeDaemonStatus} from '../AutomaterializeDaemonStatusTag';

import {AutomaterializationEvaluationHistoryTable} from './AutomaterializationEvaluationHistoryTable';
import {AutomaterializationTickDetailDialog} from './AutomaterializationTickDetailDialog';
import {AutomaterializeRunHistoryTable} from './AutomaterializeRunHistoryTable';
import {
  AssetDameonTicksQuery,
  AssetDameonTicksQueryVariables,
  AssetDaemonTickFragment,
} from './types/AutomaterializationRoot.types';

export const AutomaterializationRoot = () => {
  useTrackPageView();
  const automaterialize = useAutomaterializeDaemonStatus();
  const confirm = useConfirmation();

  const {permissions: {canToggleAutoMaterialize} = {}} = useUnscopedPermissions();

  const queryResult = useQuery<AssetDameonTicksQuery, AssetDameonTicksQueryVariables>(
    ASSET_DAMEON_TICKS_QUERY,
  );
  const [isPaused, setIsPaused] = React.useState(false);
  useQueryRefreshAtInterval(queryResult, isPaused ? Infinity : 2 * 1000);

  const [selectedTick, setSelectedTick] = React.useState<AssetDaemonTickFragment | null>(null);

  const [tableView, setTableView] = React.useState<'evaluations' | 'runs'>('evaluations');

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
      return queryResult.data?.autoMaterializeTicks ?? [];
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...ids.slice(0, 100)],
  );

  const onHoverTick = React.useCallback(
    (tick: AssetDaemonTickFragment | undefined) => {
      setIsPaused(tick ? true : false);
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
            timeRange={20 * 60 * 1000}
            tickGrid={5 * 60000}
            timeAfter={3 * 60000}
          />
          <AutomaterializationTickDetailDialog
            key={selectedTick?.id}
            tick={selectedTick}
            isOpen={!!selectedTick}
            close={() => {
              setSelectedTick(null);
            }}
          />
          <Box padding={{vertical: 12, horizontal: 24}} margin={{top: 32}} border="top">
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
          </Box>
          {tableView === 'evaluations' ? (
            <AutomaterializationEvaluationHistoryTable />
          ) : (
            <AutomaterializeRunHistoryTable />
          )}
        </>
      )}
    </Page>
  );
};

const ASSET_DAMEON_TICKS_QUERY = gql`
  query AssetDameonTicksQuery(
    $dayRange: Int
    $dayOffset: Int
    $statuses: [InstigationTickStatus!]
    $limit: Int
    $cursor: String
  ) {
    autoMaterializeTicks(
      dayRange: $dayRange
      dayOffset: $dayOffset
      statuses: $statuses
      limit: $limit
      cursor: $cursor
    ) {
      id
      ...AssetDaemonTickFragment
    }
  }

  fragment AssetDaemonTickFragment on InstigationTick {
    id
    timestamp
    endTimestamp
    status
    instigationType
    error {
      ...PythonErrorFragment
    }
    requestedAssetMaterializationCount
    requestedAssetKeys {
      path
    }
    autoMaterializeAssetEvaluationId
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
