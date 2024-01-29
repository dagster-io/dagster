// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetTimelineQueryVariables = Types.Exact<{
  inProgressFilter: Types.RunsFilter;
  terminatedFilter: Types.RunsFilter;
  tickCursor?: Types.InputMaybe<Types.Scalars['Float']>;
  ticksUntil?: Types.InputMaybe<Types.Scalars['Float']>;
}>;

export type AssetTimelineQuery = {
  __typename: 'Query';
  unterminated:
    | {__typename: 'InvalidPipelineRunsFilterError'}
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
          pipelineName: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
          assets: Array<{
            __typename: 'Asset';
            id: string;
            key: {__typename: 'AssetKey'; path: Array<string>};
          }>;
          assetMaterializations: Array<{
            __typename: 'MaterializationEvent';
            assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
          }>;
        }>;
      };
  terminated:
    | {__typename: 'InvalidPipelineRunsFilterError'}
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
          pipelineName: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
          assets: Array<{
            __typename: 'Asset';
            id: string;
            key: {__typename: 'AssetKey'; path: Array<string>};
          }>;
          assetMaterializations: Array<{
            __typename: 'MaterializationEvent';
            assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
          }>;
        }>;
      };
  workspaceOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          name: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
          displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
          locationOrLoadError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'RepositoryLocation';
                id: string;
                name: string;
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  pipelines: Array<{
                    __typename: 'Pipeline';
                    id: string;
                    name: string;
                    isJob: boolean;
                  }>;
                  schedules: Array<{
                    __typename: 'Schedule';
                    id: string;
                    name: string;
                    pipelineName: string;
                    executionTimezone: string | null;
                    scheduleState: {
                      __typename: 'InstigationState';
                      id: string;
                      status: Types.InstigationStatus;
                    };
                    futureTicks: {
                      __typename: 'DryRunInstigationTicks';
                      results: Array<{
                        __typename: 'DryRunInstigationTick';
                        timestamp: number | null;
                      }>;
                    };
                  }>;
                }>;
              }
            | null;
        }>;
      };
};

export type RunWithAssetsFragment = {
  __typename: 'Run';
  id: string;
  pipelineName: string;
  status: Types.RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
  assets: Array<{
    __typename: 'Asset';
    id: string;
    key: {__typename: 'AssetKey'; path: Array<string>};
  }>;
  assetMaterializations: Array<{
    __typename: 'MaterializationEvent';
    assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
  }>;
};
