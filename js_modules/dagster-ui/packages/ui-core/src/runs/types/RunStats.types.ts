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
              expectations: number;
              materializations: number;
            };
      }
    | {__typename: 'RunNotFoundError'; message: string};
};

export const RunStatsQueryVersion = '75e80f740a79607de9e1152f9b7074d319197fbc219784c767c1abd5553e9a49';
