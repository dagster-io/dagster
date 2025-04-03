import {Box, Checkbox, Colors, tokenToString} from '@dagster-io/ui-components';
import {useCallback} from 'react';

import {QueuedRunsBanners} from './QueuedRunsBanners';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFeedError} from './RunsFeedError';
import {RunsFeedTable} from './RunsFeedTable';
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
  QueryRefreshCountdown,
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

export const RunsFeedRoot = () => {
  useTrackPageView();

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);

  const [view, setView] = useQueryPersistedState<RunsFeedView>({
    encode: (v) => ({view: v && v !== RunsFeedView.ROOTS ? v.toLowerCase() : undefined}),
    decode: (qs) => (qs.view || RunsFeedView.ROOTS).toUpperCase(),
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

  const {tabs, queryResult: runQueryResult} = useRunsFeedTabs(currentTab, filter);
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
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      {button}
      {isShowingViewOption && (
        <Checkbox
          label={<span>Show runs within backfills</span>}
          checked={view === RunsFeedView.RUNS}
          onChange={() => {
            setView(view === RunsFeedView.RUNS ? RunsFeedView.ROOTS : RunsFeedView.RUNS);
          }}
        />
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
      <RunsFeedTable
        entries={entries}
        loading={queryResult.loading}
        onAddTag={onAddTag}
        refetch={combinedRefreshState.refetch}
        actionBarComponents={actionBarComponents}
        belowActionBarComponents={belowActionBarComponents}
        paginationProps={paginationProps}
        filter={filter}
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
    <Box style={{height: '100%', display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)'}}>
      <Box
        border="bottom"
        background={Colors.backgroundLight()}
        padding={{left: 24, right: 20}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
      >
        {tabs}
        <Box flex={{gap: 16, alignItems: 'center'}}>
          <QueryRefreshCountdown refreshState={combinedRefreshState} />
        </Box>
      </Box>
      <div>
        <RunsQueryRefetchContext.Provider value={{refetch: combinedRefreshState.refetch}}>
          {content()}
        </RunsQueryRefetchContext.Provider>
      </div>
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsFeedRoot;
