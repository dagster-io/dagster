import {useMemo} from 'react';

import {RUNS_FEED_QUERY} from './RunsFeedQuery';
import {mapRunsFeedEntry} from './mapRunsFeedData';
import {RunsFeedQuery, RunsFeedQueryVariables} from './types/RunsFeedQuery.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {RunsFeedView, RunsFilter} from '../../graphql/types';
import {RUNS_FEED_CURSOR_KEY} from '../RunsFeedUtils';
import {useCursorPaginatedQuery} from '../useCursorPaginatedQuery';

const RUNS_PER_PAGE = 30;

export type RunsFeedOptions = {
  filter: RunsFilter;
  view: RunsFeedView;
  skip: boolean;
};

/** Callers must reset pagination when applying a filter or view change. */
export function useRunsFeed({filter, view, skip}: RunsFeedOptions) {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsFeedQuery,
    RunsFeedQueryVariables
  >({
    query: RUNS_FEED_QUERY,
    queryKey: RUNS_FEED_CURSOR_KEY,
    pageSize: RUNS_PER_PAGE,
    variables: {filter, view},
    skip,
    nextCursorForResult: ({runsFeedOrError}) =>
      runsFeedOrError.__typename === 'RunsFeedConnection' && runsFeedOrError.hasMore
        ? runsFeedOrError.cursor
        : undefined,
    hasMoreForResult: ({runsFeedOrError}) =>
      runsFeedOrError.__typename === 'RunsFeedConnection' && runsFeedOrError.hasMore,
    getResultArray: (data) =>
      data?.runsFeedOrError.__typename === 'RunsFeedConnection' ? data.runsFeedOrError.results : [],
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS, !skip);

  const response = queryResult.data?.runsFeedOrError;
  const error =
    queryResult.error ?? (response?.__typename === 'PythonError' ? response : undefined);

  const entries = useMemo(
    () =>
      response?.__typename === 'RunsFeedConnection' ? response.results.map(mapRunsFeedEntry) : [],
    [response],
  );

  return {
    entries,
    error,
    queryResult,
    paginationProps,
    refreshState,
  };
}
