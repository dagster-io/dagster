/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type PartitionRangeSelector = {
  end: string;
  start: string;
};

export type PartitionsByAssetSelector = {
  assetKey: AssetKeyInput;
  partitions?: PartitionsSelector | null | undefined;
};

export type PartitionsSelector = {
  range?: PartitionRangeSelector | null | undefined;
  ranges?: Array<PartitionRangeSelector> | null | undefined;
};

export type AssetWipeMutationVariables = Exact<{
  assetPartitionRanges: Array<Types.PartitionsByAssetSelector> | Types.PartitionsByAssetSelector;
}>;

export type AssetWipeMutation = {
  __typename: 'Mutation';
  wipeAssets:
    | {__typename: 'AssetNotFoundError'}
    | {
        __typename: 'AssetWipeSuccess';
        assetPartitionRanges: Array<{
          __typename: 'AssetPartitionRange';
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          partitionRange: {__typename: 'PartitionRange'; start: string; end: string} | null;
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
      }
    | {__typename: 'UnauthorizedError'}
    | {__typename: 'UnsupportedOperationError'};
};

export const AssetWipeMutationVersion = 'accefb0c47b3d4a980d16965e8af565afed787a8a987a03570df876bd734dc8f';
