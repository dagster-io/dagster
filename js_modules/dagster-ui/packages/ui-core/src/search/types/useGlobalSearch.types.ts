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
                  assetGroups: Array<{__typename: 'AssetGroup'; id: string; groupName: string}>;
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
                  allTopLevelResourceDetails: Array<{
                    __typename: 'ResourceDetails';
                    id: string;
                    name: string;
                  }>;
                }>;
              }
            | null;
        }>;
      };
};

export type SearchGroupFragment = {__typename: 'AssetGroup'; id: string; groupName: string};

export type SearchPipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  isJob: boolean;
  name: string;
};

export type SearchScheduleFragment = {__typename: 'Schedule'; id: string; name: string};

export type SearchSensorFragment = {__typename: 'Sensor'; id: string; name: string};

export type SearchPartitionSetFragment = {
  __typename: 'PartitionSet';
  id: string;
  name: string;
  pipelineName: string;
};

export type SearchResourceDetailFragment = {
  __typename: 'ResourceDetails';
  id: string;
  name: string;
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
          definition: {
            __typename: 'AssetNode';
            id: string;
            computeKind: string | null;
            groupName: string;
            kinds: Array<string>;
            owners: Array<
              | {__typename: 'TeamAssetOwner'; team: string}
              | {__typename: 'UserAssetOwner'; email: string}
            >;
            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
            repository: {
              __typename: 'Repository';
              id: string;
              name: string;
              location: {__typename: 'RepositoryLocation'; id: string; name: string};
            };
          } | null;
        }>;
      }
    | {__typename: 'PythonError'};
};

export type SearchAssetFragment = {
  __typename: 'Asset';
  id: string;
  key: {__typename: 'AssetKey'; path: Array<string>};
  definition: {
    __typename: 'AssetNode';
    id: string;
    computeKind: string | null;
    groupName: string;
    kinds: Array<string>;
    owners: Array<
      {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
    >;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
  } | null;
};

export const SearchPrimaryQueryVersion = '5d98265169496aabdee190894e504f0dd6205c3a8be462c5eac2a6c9c0c75f4a';

export const SearchSecondaryQueryVersion = '39a75cb3ec146190c7dab171af1761a0f63a080aa8dbf379066223a6ac4af7e9';
