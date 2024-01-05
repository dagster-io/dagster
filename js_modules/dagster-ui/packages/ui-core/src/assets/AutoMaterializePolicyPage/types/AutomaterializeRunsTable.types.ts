// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AutomaterializeRunsQueryVariables = Types.Exact<{
  filter?: Types.InputMaybe<Types.RunsFilter>;
}>;

export type AutomaterializeRunsQuery = {
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
          runId: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
        }>;
      };
};

export type AutomaterializeRunFragment = {
  __typename: 'Run';
  id: string;
  runId: string;
  status: Types.RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
};
