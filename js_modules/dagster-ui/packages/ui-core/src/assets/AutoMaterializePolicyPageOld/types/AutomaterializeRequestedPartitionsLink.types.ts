// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type OldRunStatusAndPartitionKeyQueryVariables = Types.Exact<{
  filter?: Types.InputMaybe<Types.RunsFilter>;
}>;

export type OldRunStatusAndPartitionKeyQuery = {
  __typename: 'Query';
  runsOrError:
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
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      };
};

export type OldRunStatusAndTagsFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};
