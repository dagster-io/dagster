import {Box, Button, ButtonGroup, Checkbox, Colors, Icon, tokenToString} from '@dagster-io/ui-components';
import {useCallback, useState} from 'react';

import {QueuedRunsBanners} from './QueuedRunsBanners';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFeedError} from './RunsFeedError';
import {RunsFeedTableNew} from './RunsFeedTableNew';
import {useRunsFeedTabs, useSelectedRunsFeedTab} from './RunsFeedTabs';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from './RunsFilterInput';
import {SCHEDULED_RUNS_LIST_QUERY, ScheduledRunList} from './ScheduledRunList';
import {TerminateAllRunsButton} from './TerminateAllRunsButton';
import {
  ScheduledRunsListQuery,
  ScheduledRunsListQueryVariables,
} from './types/ScheduledRunList.types';
import {useRunsFeedEntries} from './useRunsFeedEntries';
import {useQuery} from '../apollo-client';
import {
  FIFTEEN_SECONDS,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunsFeedView} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {DaemonNotRunningAlert, useIsBackfillDaemonHealthy} from '../partitions/BackfillMessaging';
import {Loading} from '../ui/Loading';

const filters: RunFilterTokenType[] = [
  'tag',
  'snapshotId',
  'id',
  'job',
  'pipeline',
  'partition',
  'backfill',
  'status',
];

export const RunsFeedRootNew = () => {
  useTrackPageView();

  const [selectedTab, setSelectedTab] = useState<
    'all' | 'in-progress' | 'failed' | 'queued'
  >('all');

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);

  const [view, setView] = useQueryPersistedState<RunsFeedView>({
    encode: (v) => ({view: v && v !== RunsFeedView.ROOTS ? v.toLowerCase() : undefined}),
    decode: (qs) => {
      const value = typeof qs.view === 'string' ? qs.view : RunsFeedView.ROOTS;
      return value.toUpperCase() as RunsFeedView;
    },
  });

  const currentTab = useSelectedRunsFeedTab(filterTokens, view);

  const setFilterTokensWithStatus = useCallback(
    (tokens: RunFilterToken[]) => {
      setFilterTokens(tokens);
    },
    [setFilterTokens],
  );

  const onAddTag = useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!filterTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokensWithStatus([...filterTokens, token]);
      }
    },
    [filterTokens, setFilterTokensWithStatus],
  );

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: filterTokens,
    onChange: setFilterTokensWithStatus,
    enabledFilters: filters,
  });

  const {queryResult: runQueryResult} = useRunsFeedTabs(currentTab, filter);
  const isScheduled = currentTab === 'scheduled';
  const isShowingViewOption = ['all', 'failed'].includes(currentTab);

  const {entries, paginationProps, queryResult} = useRunsFeedEntries({
    view: isShowingViewOption || currentTab === 'backfills' ? view : RunsFeedView.RUNS,
    skip: isScheduled,
    filter,
  });

  const scheduledQueryResult = useQuery<ScheduledRunsListQuery, ScheduledRunsListQueryVariables>(
    SCHEDULED_RUNS_LIST_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      skip: !isScheduled,
    },
  );
  const refreshState = useQueryRefreshAtInterval(
    isScheduled ? scheduledQueryResult : queryResult,
    FIFTEEN_SECONDS,
  );
  const countRefreshState = useQueryRefreshAtInterval(runQueryResult, FIFTEEN_SECONDS);
  const combinedRefreshState = useMergedRefresh(countRefreshState, refreshState);
  const {error} = queryResult;

  const actionBarComponents = (
    <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
      <ButtonGroup
        activeItems={new Set([selectedTab])}
        buttons={[
          {id: 'all', label: 'Show all'},
          {id: 'in-progress', label: 'In progress'},
          {id: 'failed', label: 'Failed'},
          {id: 'queued', label: 'Queued'},
        ]}
        onClick={(id) => setSelectedTab(id as 'all' | 'in-progress' | 'failed' | 'queued')}
      />
      <Button rightIcon={<Icon name="expand_more" />}>More filters</Button>
      {isShowingViewOption && (
        <Box style={{paddingLeft: '24px'}}>
          <Checkbox
            format="switch"
            label={<span>Show backfills only</span>}
            checked={view === RunsFeedView.RUNS}
            onChange={() => {
              setView(view === RunsFeedView.RUNS ? RunsFeedView.ROOTS : RunsFeedView.RUNS);
            }}
          />
        </Box>
      )}
    </Box>
  );

  let belowActionBarComponents = activeFiltersJsx.length ? (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>{activeFiltersJsx}</Box>
  ) : null;

  const isDaemonHealthy = useIsBackfillDaemonHealthy();
  if (!isDaemonHealthy && currentTab === 'backfills') {
    belowActionBarComponents = (
      <Box flex={{direction: 'column', gap: 8}}>
        <DaemonNotRunningAlert />
        {belowActionBarComponents}
      </Box>
    );
  }
  if (currentTab === 'queued') {
    belowActionBarComponents = (
      <Box flex={{direction: 'column', gap: 8}}>
        <QueuedRunsBanners />
        {belowActionBarComponents}
      </Box>
    );
  }

  function content() {
    if (currentTab === 'scheduled') {
      return (
        <Loading queryResult={scheduledQueryResult} allowStaleData>
          {(result) => <ScheduledRunList result={result} />}
        </Loading>
      );
    }

    if (error) {
      return <RunsFeedError error={error} />;
    }

    return (
      <RunsFeedTableNew
        entries={entries}
        loading={queryResult.loading}
        onAddTag={onAddTag}
        refetch={combinedRefreshState.refetch}
        actionBarComponents={actionBarComponents}
        belowActionBarComponents={belowActionBarComponents}
        paginationProps={paginationProps}
        filter={filter}
        statusFilter={selectedTab}
        terminateAllRunsButton={
          currentTab === 'queued' ? (
            <TerminateAllRunsButton
              refetch={combinedRefreshState.refetch}
              filter={{...filter, statuses: Array.from(queuedStatuses)}}
              disabled={
                runQueryResult.data?.queuedCount.__typename === 'RunsFeedCount'
                  ? runQueryResult.data?.queuedCount.count === 0
                  : true
              }
            />
          ) : currentTab === 'in-progress' ? (
            <TerminateAllRunsButton
              refetch={combinedRefreshState.refetch}
              filter={{...filter, statuses: Array.from(inProgressStatuses)}}
              disabled={
                runQueryResult.data?.inProgressCount.__typename === 'RunsFeedCount'
                  ? runQueryResult.data?.inProgressCount.count === 0
                  : true
              }
            />
          ) : undefined
        }
      />
    );
  }

  return (
    <Box style={{height: '100%', display: 'flex', flexDirection: 'column'}}>
      {/* H1 Runs Header */}
      <Box
        style={{
          height: '52px',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: '16px',
          paddingRight: '16px',
          flexShrink: 0,
          borderBottom: '1px solid #e1e5e9',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: '20px',
            fontWeight: 600,
            lineHeight: '24px',
            color: Colors.textDefault(),
          }}
        >
          Runs
        </h1>
      </Box>
      <Box style={{flex: 1, minHeight: 0}}>
        <RunsQueryRefetchContext.Provider value={{refetch: combinedRefreshState.refetch}}>
          {content()}
        </RunsQueryRefetchContext.Provider>
      </Box>
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsFeedRootNew;