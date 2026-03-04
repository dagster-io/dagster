import {useMemo} from 'react';

import {RUNS_FEED_TABLE_ENTRY_FRAGMENT} from './RunsFeedTableEntryFragment';
import {RUNS_FEED_CURSOR_KEY} from './RunsFeedUtils';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from './types/useRunsFeedEntries.types';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';
import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RunsFeedView, RunsFilter} from '../graphql/types';

const PAGE_SIZE = 30;

export function useRunsFeedEntries({
  filter,
  skip,
  view,
}: {
  filter: RunsFilter;
  skip: boolean;
  view: RunsFeedView;
}) {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsFeedRootQuery,
    RunsFeedRootQueryVariables
  >({
    query: RUNS_FEED_ROOT_QUERY,
    queryKey: RUNS_FEED_CURSOR_KEY,
    pageSize: PAGE_SIZE,
    variables: {filter, view},
    skip,
    nextCursorForResult: (data) => {
      if (data.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return undefined;
      }
      return data.runsFeedOrError.hasMore ? data.runsFeedOrError.cursor : undefined;
    },
    hasMoreForResult: (data) => {
      if (data.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return false;
      }
      return data.runsFeedOrError.hasMore;
    },
    getResultArray: (data) => {
      if (!data || data.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return [];
      }
      return data.runsFeedOrError.results;
    },
  });

  const data = queryResult.data || queryResult.previousData;

  const entries = useMemo(() => {
    return data?.runsFeedOrError.__typename === 'RunsFeedConnection'
      ? data?.runsFeedOrError.results
      : [];
  }, [data]);

  return {
    queryResult,
    paginationProps,
    entries,
  };
}

export const RUNS_FEED_ROOT_QUERY = gql`
  query RunsFeedRootQuery(
    $limit: Int!
    $cursor: String
    $filter: RunsFilter
    $view: RunsFeedView!
  ) {
    runsFeedOrError(limit: $limit, cursor: $cursor, filter: $filter, view: $view) {
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
