/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunRetriedStepsQueryVariables = Exact<{
  runId: string;
}>;

export type RunRetriedStepsQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        stepStats: Array<{
          __typename: 'RunStepStats';
          stepKey: string;
          attempts: Array<{__typename: 'RunMarker'; startTime: number | null}>;
        }>;
      }
    | {__typename: 'RunNotFoundError'};
};
