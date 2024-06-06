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
