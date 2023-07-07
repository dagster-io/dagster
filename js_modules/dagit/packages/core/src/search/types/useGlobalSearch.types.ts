// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SearchPrimaryQueryVariables = Types.Exact<{[key: string]: never}>;

export type SearchPrimaryQuery = {
  __typename: 'Query';
  workspaceOrError:
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
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
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
                  assetGroups: Array<{__typename: 'AssetGroup'; groupName: string}>;
                  pipelines: Array<{
                    __typename: 'Pipeline';
                    id: string;
                    isJob: boolean;
                    name: string;
                  }>;
                  schedules: Array<{__typename: 'Schedule'; id: string; name: string}>;
                  sensors: Array<{__typename: 'Sensor'; id: string; name: string}>;
                  partitionSets: Array<{
                    __typename: 'PartitionSet';
                    id: string;
                    name: string;
                    pipelineName: string;
                  }>;
                  allTopLevelResourceDetails: Array<{__typename: 'ResourceDetails'; name: string}>;
                }>;
              }
            | null;
        }>;
      };
};

export type SearchSecondaryQueryVariables = Types.Exact<{[key: string]: never}>;

export type SearchSecondaryQuery = {
  __typename: 'Query';
  assetsOrError:
    | {
        __typename: 'AssetConnection';
        nodes: Array<{
          __typename: 'Asset';
          id: string;
          key: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {__typename: 'PythonError'};
};
