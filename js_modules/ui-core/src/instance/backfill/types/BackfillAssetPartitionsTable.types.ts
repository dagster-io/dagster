// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillPartitionsForAssetKeyQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
  assetKey: Types.AssetKeyInput;
}>;

export type BackfillPartitionsForAssetKeyQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        partitionsTargetedForAssetKey: {
          __typename: 'AssetBackfillTargetPartitions';
          partitionKeys: Array<string> | null;
          ranges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
        } | null;
      }
    | {__typename: 'PythonError'};
};

export const BackfillPartitionsForAssetKeyVersion = '672b7141fd1dfb275a4ef6ae3e8fc1eaa0707270c1fd329ed6b66058e2376e55';
