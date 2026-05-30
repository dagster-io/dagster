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
            isPartitioned: boolean;
            isAutoCreatedStub: boolean;
            hasAssetChecks: boolean;
            computeKind: string | null;
            hasMaterializePermission: boolean;
            hasWipePermission: boolean;
            hasReportRunlessAssetEventPermission: boolean;
            description: string | null;
            jobNames: Array<string>;
            kinds: Array<string>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
            internalFreshnessPolicy:
              | {
                  __typename: 'CronFreshnessPolicy';
                  deadlineCron: string;
                  lowerBoundDeltaSeconds: number;
                  timezone: string;
                }
              | {
                  __typename: 'TimeWindowFreshnessPolicy';
                  failWindowSeconds: number;
                  warnWindowSeconds: number | null;
                }
              | null;
            partitionDefinition: {
              __typename: 'PartitionDefinition';
              dimensionTypes: Array<{
                __typename: 'DimensionDefinitionType';
                type: Types.PartitionDefinitionType;
                dynamicPartitionsDefinitionName: string | null;
              }>;
            } | null;
            automationCondition: {__typename: 'AutomationCondition'} | null;
            owners: Array<
              | {__typename: 'TeamAssetOwner'; team: string}
              | {__typename: 'UserAssetOwner'; email: string}
            >;
            tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
            storageAddress: {
              __typename: 'StorageAddress';
              storageKind: string | null;
              tableName: string;
            } | null;
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
    isPartitioned: boolean;
    isAutoCreatedStub: boolean;
    hasAssetChecks: boolean;
    computeKind: string | null;
    hasMaterializePermission: boolean;
    hasWipePermission: boolean;
    hasReportRunlessAssetEventPermission: boolean;
    description: string | null;
    jobNames: Array<string>;
    kinds: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    internalFreshnessPolicy:
      | {
          __typename: 'CronFreshnessPolicy';
          deadlineCron: string;
          lowerBoundDeltaSeconds: number;
          timezone: string;
        }
      | {
          __typename: 'TimeWindowFreshnessPolicy';
          failWindowSeconds: number;
          warnWindowSeconds: number | null;
        }
      | null;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        type: Types.PartitionDefinitionType;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
    automationCondition: {__typename: 'AutomationCondition'} | null;
    owners: Array<
      {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
    >;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    storageAddress: {
      __typename: 'StorageAddress';
      storageKind: string | null;
      tableName: string;
    } | null;
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
  isPartitioned: boolean;
  isAutoCreatedStub: boolean;
  hasAssetChecks: boolean;
  computeKind: string | null;
  hasMaterializePermission: boolean;
  hasWipePermission: boolean;
  hasReportRunlessAssetEventPermission: boolean;
  description: string | null;
  jobNames: Array<string>;
  kinds: Array<string>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  internalFreshnessPolicy:
    | {
        __typename: 'CronFreshnessPolicy';
        deadlineCron: string;
        lowerBoundDeltaSeconds: number;
        timezone: string;
      }
    | {
        __typename: 'TimeWindowFreshnessPolicy';
        failWindowSeconds: number;
        warnWindowSeconds: number | null;
      }
    | null;
  partitionDefinition: {
    __typename: 'PartitionDefinition';
    dimensionTypes: Array<{
      __typename: 'DimensionDefinitionType';
      type: Types.PartitionDefinitionType;
      dynamicPartitionsDefinitionName: string | null;
    }>;
  } | null;
  automationCondition: {__typename: 'AutomationCondition'} | null;
  owners: Array<
    {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
  >;
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
  storageAddress: {
    __typename: 'StorageAddress';
    storageKind: string | null;
    tableName: string;
  } | null;
  repository: {
    __typename: 'Repository';
    id: string;
    name: string;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
  };
};

export const AssetCatalogTableQueryVersion = '67bd29bba7f7d1ddc9c2d3e7bd5a1b3fe26d36875ba9dea6052c799ab4c98955';

export const AssetCatalogGroupTableQueryVersion = '2a2ce4dd539e52f1a5c95072d6c41e61fd0939380ed25f5e0700188b1e6edd20';
