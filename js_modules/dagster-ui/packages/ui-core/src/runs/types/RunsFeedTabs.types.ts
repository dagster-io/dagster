// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
  inProgressCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
};

export const RunFeedTabsCountQueryVersion = '5ddccded028ae94b64bda3c2b850bcc8f384de9851c0dd393f158b2a53469262';
