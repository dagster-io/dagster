// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTabsCountQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
}>;

export type RunTabsCountQuery = {
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

export const RunTabsCountQueryVersion = '5fe1760a3bf0494fb98e3c09f31add5138f9f31d59507a8b25186e2103bebbb4';
