// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount: {__typename: 'PythonError'} | {__typename: 'RunsFeed'; count: number};
  inProgressCount: {__typename: 'PythonError'} | {__typename: 'RunsFeed'; count: number};
};

export const RunFeedTabsCountQueryVersion = 'a4a47a3d175ea85430f09c47431e6591f6b79c951cb8a007fa8f2fdbb03693e8';
