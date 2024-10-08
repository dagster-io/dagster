import {Box, Checkbox, Colors, NonIdealState, tokenToString} from '@dagster-io/ui-components';
import partition from 'lodash/partition';
import {useCallback, useMemo} from 'react';

import {RunsQueryRefetchContext} from './RunUtils';
import {RUNS_FEED_TABLE_ENTRY_FRAGMENT} from './RunsFeedRow';
import {RunsFeedTable} from './RunsFeedTable';
import {useRunsFeedTabs, useSelectedRunsFeedTab} from './RunsFeedTabs';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from './RunsFilterInput';
import {SCHEDULED_RUNS_LIST_QUERY, ScheduledRunList} from './ScheduledRunListRoot';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from './types/RunsFeedRoot.types';
import {
  ScheduledRunsListQuery,
  ScheduledRunsListQueryVariables,
} from './types/ScheduledRunListRoot.types';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunsFilter} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {Loading, LoadingSpinner} from '../ui/Loading';

const PAGE_SIZE = 25;

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

export function useRunsFeedEntries(
  filter: RunsFilter,
  currentTab: ReturnType<typeof useSelectedRunsFeedTab>,
  includeRunsFromBackfills: boolean,
) {
  const isScheduled = currentTab === 'scheduled';
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsFeedRootQuery,
    RunsFeedRootQueryVariables
  >({
    query: RUNS_FEED_ROOT_QUERY,
    pageSize: PAGE_SIZE,
    variables: {filter, includeRunsFromBackfills},
    skip: isScheduled,
    nextCursorForResult: (runs) => {
      if (runs.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return undefined;
      }
      return runs.runsFeedOrError.hasMore ? runs.runsFeedOrError.cursor : undefined;
    },
    getResultArray: (data) => {
      if (!data || data.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return [];
      }
      return data.runsFeedOrError.results;
    },
  });

  const data = queryResult.data || queryResult.previousData;

  const entries =
    data?.runsFeedOrError.__typename === 'RunsFeedConnection' ? data?.runsFeedOrError.results : [];

  const scheduledQueryResult = useQuery<ScheduledRunsListQuery, ScheduledRunsListQueryVariables>(
    SCHEDULED_RUNS_LIST_QUERY,
    {
      notifyOnNetworkStatusChange: true,
      skip: !isScheduled,
    },
  );

  return {
    queryResult,
    paginationProps,
    entries,
    scheduledQueryResult,
  };
}

export const RunsFeedRoot = () => {
  useTrackPageView();

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);

  const currentTab = useSelectedRunsFeedTab(filterTokens);
  const staticStatusTags = currentTab !== 'all';

  const [statusTokens, nonStatusTokens] = partition(
    filterTokens,
    (token) => token.token === 'status',
  );

  const setFilterTokensWithStatus = useCallback(
    (tokens: RunFilterToken[]) => {
      if (staticStatusTags) {
        setFilterTokens([...statusTokens, ...tokens]);
      } else {
        setFilterTokens(tokens);
      }
    },
    [setFilterTokens, staticStatusTags, statusTokens],
  );

  const onAddTag = useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!nonStatusTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokensWithStatus([...nonStatusTokens, token]);
      }
    },
    [nonStatusTokens, setFilterTokensWithStatus],
  );

  const mutableTokens = useMemo(() => {
    if (staticStatusTags) {
      return filterTokens.filter((token) => token.token !== 'status');
    }
    return filterTokens;
  }, [filterTokens, staticStatusTags]);

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: mutableTokens,
    onChange: setFilterTokensWithStatus,
    enabledFilters: filters,
  });

  const [includeRunsFromBackfills, setincludeRunsFromBackfills] = useQueryPersistedState<boolean>({
    queryKey: 'show_runs_within_backfills',
    defaults: {show_runs_within_backfills: false},
  });
  const {tabs, queryResult: runQueryResult} = useRunsFeedTabs(filter, includeRunsFromBackfills);

  const {entries, paginationProps, queryResult, scheduledQueryResult} = useRunsFeedEntries(
    filter,
    currentTab,
    includeRunsFromBackfills,
  );
  const refreshState = useQueryRefreshAtInterval(
    currentTab === 'scheduled' ? scheduledQueryResult : queryResult,
    FIFTEEN_SECONDS,
  );
  const countRefreshState = useQueryRefreshAtInterval(runQueryResult, FIFTEEN_SECONDS);
  const combinedRefreshState = useMergedRefresh(countRefreshState, refreshState);
  const {error} = queryResult;

  const actionBarComponents = (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      {button}
      <Checkbox
        label={<span>Show runs within backfills</span>}
        checked={includeRunsFromBackfills}
        onChange={() => {
          setincludeRunsFromBackfills(!includeRunsFromBackfills);
        }}
      />
    </Box>
  );

  const belowActionBarComponents = activeFiltersJsx.length ? (
    <Box
      border="top"
      flex={{direction: 'row', gap: 4, alignItems: 'center'}}
      padding={{left: 24, right: 12, top: 12}}
    >
      {activeFiltersJsx}
    </Box>
  ) : null;

  function content() {
    if (currentTab === 'scheduled') {
      return (
        <Loading queryResult={scheduledQueryResult} allowStaleData>
          {(result) => {
            return <ScheduledRunList result={result} />;
          }}
        </Loading>
      );
    }
    if (error) {
      const badRequest = !!(
        typeof error === 'object' &&
        'statusCode' in error &&
        error.statusCode === 400
      );
      return (
        <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8}} border="top">
          <NonIdealState
            icon="warning"
            title={badRequest ? 'Invalid run filters' : 'Unexpected error'}
            description={
              badRequest
                ? 'The specified run filters are not valid. Please check the filters and try again.'
                : 'An unexpected error occurred. Check the console for details.'
            }
          />
        </Box>
      );
    }
    if (queryResult.loading && !queryResult.data) {
      return (
        <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8}} border="top">
          <LoadingSpinner purpose="page" />
        </Box>
      );
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
      />
    );
  }

  return (
    <Box style={{height: '100%', display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)'}}>
      <Box
        border="bottom"
        background={Colors.backgroundLight()}
        padding={{left: 24, right: 20, top: 12}}
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

export const RUNS_FEED_ROOT_QUERY = gql`
  query RunsFeedRootQuery(
    $limit: Int!
    $cursor: String
    $filter: RunsFilter
    $includeRunsFromBackfills: Boolean!
  ) {
    runsFeedOrError(
      limit: $limit
      cursor: $cursor
      filter: $filter
      includeRunsFromBackfills: $includeRunsFromBackfills
    ) {
      ... on RunsFeedConnection {
        cursor
        hasMore
        results {
          id
          ...RunsFeedTableEntryFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${RUNS_FEED_TABLE_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
