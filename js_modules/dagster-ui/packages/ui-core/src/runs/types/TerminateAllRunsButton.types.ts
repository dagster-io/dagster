// Generated GraphQL types, do not edit manually.
import * as Types from '../../graphql/types';

export type TerminateRunIdsQueryVariables = Types.Exact<{
  filter: Types.RunsFilter;
}>;

export type TerminateRunIdsQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          canTerminate: boolean;
        }>;
      };
};
