// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunFeedTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {__typename: 'Runs'; count: number | null};
  inProgressCount:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {__typename: 'Runs'; count: number | null};
};

export const RunFeedTabsCountQueryVersion = 'e845ed2b46945b3ae28446fd8b44ce96a48d59f06ca2f58cfad30f8d4f4d8fa2';
