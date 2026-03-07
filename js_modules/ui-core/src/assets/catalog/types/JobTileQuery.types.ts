// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type JobTileQueryVariables = Types.Exact<{
  pipelineSelector: Types.PipelineSelector;
}>;

export type JobTileQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        runs: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          runStatus: Types.RunStatus;
          startTime: number | null;
        }>;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const JobTileQueryVersion = '6fd1bb8a16c8bd5fff0fb75f6608d5402a426d5c2763fefcb61d60e94ff0a3e8';
