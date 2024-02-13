// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionStepLoaderQueryVariables = Types.Exact<{
  filter: Types.RunsFilter;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
}>;

export type PartitionStepLoaderQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'; message: string}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          stepStats: Array<{
            __typename: 'RunStepStats';
            stepKey: string;
            startTime: number | null;
            endTime: number | null;
            status: Types.StepEventStatus | null;
          }>;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      };
};
