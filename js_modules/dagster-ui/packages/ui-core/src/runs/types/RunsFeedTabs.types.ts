// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
  view: Types.RunsFeedView;
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
  inProgressCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
};

export const RunFeedTabsCountQueryVersion = '5bf6c4d00cebf6817ce69cc4fc6d25c99b98f7a9031934b61187f95020880b4a';
