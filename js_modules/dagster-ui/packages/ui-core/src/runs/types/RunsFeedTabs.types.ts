// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
  includeRunsFromBackfills: Types.Scalars['Boolean']['input'];
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
  inProgressCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
};

export const RunFeedTabsCountQueryVersion = 'fe1a07dfc152faddc4fd8936aee1f856b8d8308edf8078bdaa4e5cd111e044cc';
