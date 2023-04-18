// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type RunDetailsTestQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunDetailsTestQuery = {
  __typename: 'DagitQuery';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        startTime: number | null;
        endTime: number | null;
        status: Types.RunStatus;
      }
    | {__typename: 'RunNotFoundError'};
};
