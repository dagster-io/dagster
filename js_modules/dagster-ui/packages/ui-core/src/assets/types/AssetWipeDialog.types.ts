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
          partitionRange: {__typename: 'PartitionRange'; start: string; end: string};
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
    | {__typename: 'UnauthorizedError'};
};
