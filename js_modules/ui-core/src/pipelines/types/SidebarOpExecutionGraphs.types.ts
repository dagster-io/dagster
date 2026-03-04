// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarOpGraphsQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
  handleID: Types.Scalars['String']['input'];
}>;

export type SidebarOpGraphsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        solidHandle: {
          __typename: 'SolidHandle';
          stepStats:
            | {
                __typename: 'SolidStepStatsConnection';
                nodes: Array<{
                  __typename: 'RunStepStats';
                  runId: string;
                  startTime: number | null;
                  endTime: number | null;
                  status: Types.StepEventStatus | null;
                }>;
              }
            | {__typename: 'SolidStepStatusUnavailableError'}
            | null;
        } | null;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const SidebarOpGraphsQueryVersion = '3feca8de1ac2e1f479a0a6b88b76e731da4162cb717f7174e5f232527cc6ce52';
