/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: string;
};

export type AssetKeyInput = {
  path: Array<string>;
};

export type PartitionDefinitionType = 'DYNAMIC' | 'MULTIPARTITIONED' | 'STATIC' | 'TIME_WINDOW';

export type PipelineSelector = {
  assetCheckSelection?: Array<AssetCheckHandleInput> | null | undefined;
  assetSelection?: Array<AssetKeyInput> | null | undefined;
  pipelineName: string;
  repositoryLocationName: string;
  repositoryName: string;
  solidSelection?: Array<string> | null | undefined;
};

export type RepositorySelector = {
  repositoryLocationName: string;
  repositoryName: string;
};

export type ConfigPartitionsQueryVariables = Exact<{
  repositorySelector: Types.RepositorySelector;
  partitionSetName: string;
}>;

export type ConfigPartitionsQuery = {
  __typename: 'Query';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        partitionsOrError:
          | {__typename: 'Partitions'; results: Array<{__typename: 'Partition'; name: string}>}
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
      }
    | {__typename: 'PartitionSetNotFoundError'}
    | {__typename: 'PythonError'};
};

export type ConfigPartitionResultFragment = {__typename: 'Partition'; name: string};

export type ConfigPartitionsAssetsQueryVariables = Exact<{
  params: Types.PipelineSelector;
  assetKeys?: Array<Types.AssetKeyInput> | Types.AssetKeyInput | null | undefined;
}>;

export type ConfigPartitionsAssetsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'Pipeline';
        id: string;
        partitionKeysOrError: {__typename: 'PartitionKeys'; partitionKeys: Array<string>};
      }
    | {__typename: 'PipelineNotFoundError'; message: string}
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
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      name: string | null;
      type: Types.PartitionDefinitionType;
    } | null;
  }>;
};

export const ConfigPartitionsQueryVersion = 'b2982b87aa317ad4df2f4227ac4285280de352fa571e952f56f9f85e2a0096fc';

export const ConfigPartitionsAssetsQueryVersion = '02438f2590d14870b0df3107680c2d33da2c7a492a3f8a507c591f7ad4555409';
