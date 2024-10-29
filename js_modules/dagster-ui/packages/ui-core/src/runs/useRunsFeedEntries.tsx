import {RUNS_FEED_TABLE_ENTRY_FRAGMENT} from './RunsFeedRow';
import {useSelectedRunsFeedTab} from './RunsFeedTabs';
import {SCHEDULED_RUNS_LIST_QUERY} from './ScheduledRunListRoot';
import {
  ScheduledRunsListQuery,
  ScheduledRunsListQueryVariables,
} from './types/ScheduledRunListRoot.types';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from './types/useRunsFeedEntries.types';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';
import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RunsFilter} from '../graphql/types';

const PAGE_SIZE = 25;

const RUNS_FEED_CURSOR_KEY = `runs_before`;

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
    queryKey: RUNS_FEED_CURSOR_KEY,
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
