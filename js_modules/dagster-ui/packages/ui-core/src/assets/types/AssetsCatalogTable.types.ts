// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCatalogTableQueryVariables = Types.Exact<{
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit: Types.Scalars['Int']['input'];
}>;

export type AssetCatalogTableQuery = {
  __typename: 'Query';
  assetsOrError:
    | {
        __typename: 'AssetConnection';
        cursor: string | null;
        nodes: Array<{
          __typename: 'Asset';
          id: string;
          key: {__typename: 'AssetKey'; path: Array<string>};
          definition: {
            __typename: 'AssetNode';
            id: string;
            changedReasons: Array<Types.ChangeReason>;
            groupName: string;
            opNames: Array<string>;
            isMaterializable: boolean;
            isObservable: boolean;
            isExecutable: boolean;
            computeKind: string | null;
            hasMaterializePermission: boolean;
            description: string | null;
            kinds: Array<string>;
            partitionDefinition: {
              __typename: 'PartitionDefinition';
              description: string;
              dimensionTypes: Array<{
                __typename: 'DimensionDefinitionType';
                type: Types.PartitionDefinitionType;
                dynamicPartitionsDefinitionName: string | null;
              }>;
            } | null;
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
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export type AssetCatalogGroupTableQueryVariables = Types.Exact<{
  group?: Types.InputMaybe<Types.AssetGroupSelector>;
}>;

export type AssetCatalogGroupTableQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    changedReasons: Array<Types.ChangeReason>;
    groupName: string;
    opNames: Array<string>;
    isMaterializable: boolean;
    isObservable: boolean;
    isExecutable: boolean;
    computeKind: string | null;
    hasMaterializePermission: boolean;
    description: string | null;
    kinds: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      description: string;
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        type: Types.PartitionDefinitionType;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
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
  }>;
};

export type AssetCatalogGroupTableNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  changedReasons: Array<Types.ChangeReason>;
  groupName: string;
  opNames: Array<string>;
  isMaterializable: boolean;
  isObservable: boolean;
  isExecutable: boolean;
  computeKind: string | null;
  hasMaterializePermission: boolean;
  description: string | null;
  kinds: Array<string>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  partitionDefinition: {
    __typename: 'PartitionDefinition';
    description: string;
    dimensionTypes: Array<{
      __typename: 'DimensionDefinitionType';
      type: Types.PartitionDefinitionType;
      dynamicPartitionsDefinitionName: string | null;
    }>;
  } | null;
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
};
