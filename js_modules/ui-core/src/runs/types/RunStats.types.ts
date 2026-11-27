/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunStatsQueryVariables = Exact<{
  runId: string;
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
