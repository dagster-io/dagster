// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTabsCountNewQueryVariables = Types.Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
}>;

export type RunTabsCountNewQuery = {
  __typename: 'DagitQuery';
  queuedCount:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {__typename: 'Runs'; count: number | null};
  inProgressCount:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {__typename: 'Runs'; count: number | null};
};
