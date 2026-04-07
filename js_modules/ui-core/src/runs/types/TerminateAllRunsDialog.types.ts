// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TerminateBatchQueryVariables = Types.Exact<{
  filter: Types.RunsFilter;
  limit: Types.Scalars['Int']['input'];
}>;

export type TerminateBatchQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {__typename: 'Runs'; results: Array<{__typename: 'Run'; id: string}>};
};

export const TerminateVersion = '67acf403eb320a93c9a9aa07f675a1557e0887d499cd5598f1d5ff360afc15c0';

export const TerminateBatchQueryVersion = 'e3fedf1a144872662b554f34b42c63eb4278a9710b33df6e4b2028db699f6a40';
