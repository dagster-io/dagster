// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunStatsQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunStatsQuery = {
  __typename: 'Query';
  pipelineRunOrError:
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
        __typename: 'Run';
        id: string;
        pipelineName: string;
        stats:
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
              __typename: 'RunStatsSnapshot';
              id: string;
              stepsSucceeded: number;
              stepsFailed: number;
            };
      }
    | {__typename: 'RunNotFoundError'; message: string};
};

export const RunStatsQueryVersion = '5aa2922c5e4a7b4ce8e8096878fa9f08eaf037ab689a4b2a66b452ad542ee278';
