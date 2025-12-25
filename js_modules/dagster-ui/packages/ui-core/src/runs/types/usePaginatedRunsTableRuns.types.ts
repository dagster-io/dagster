// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunsRootQueryVariables = Types.Exact<{
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
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
          hasRunMetricsEnabled: boolean;
          mode: string;
          rootRunId: string | null;
          parentRunId: string | null;
          pipelineSnapshotId: string | null;
          pipelineName: string;
          solidSelection: Array<string> | null;
          creationTime: number;
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
          assetCheckSelection: Array<{
            __typename: 'AssetCheckhandle';
            name: string;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
          }> | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      };
};

export const RunsRootQueryVersion = 'b914653fae9880b8c9539f34bedea994f281148546981bc5b572d3b62a8f78c0';
