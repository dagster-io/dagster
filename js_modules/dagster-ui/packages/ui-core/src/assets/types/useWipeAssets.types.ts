// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetWipeMutationVariables = Types.Exact<{
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
