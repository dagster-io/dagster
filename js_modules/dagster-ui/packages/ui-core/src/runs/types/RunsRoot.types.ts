// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunsRootQueryVariables = Types.Exact<{
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
  filter: Types.RunsFilter;
}>;

export type RunsRootQuery = {
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
          stepKeysToExecute: Array<string> | null;
          canTerminate: boolean;
          hasReExecutePermission: boolean;
          hasTerminatePermission: boolean;
          hasDeletePermission: boolean;
          mode: string;
          rootRunId: string | null;
          parentRunId: string | null;
          pipelineSnapshotId: string | null;
          pipelineName: string;
          solidSelection: Array<string> | null;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
          assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      };
};

export type QueueDaemonStatusQueryVariables = Types.Exact<{[key: string]: never}>;

export type QueueDaemonStatusQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {
        __typename: 'DaemonStatus';
        id: string;
        daemonType: string;
        healthy: boolean | null;
        required: boolean;
      };
    };
  };
};
