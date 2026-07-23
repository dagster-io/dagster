/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type BackfillPartitionsForAssetKeyQueryVariables = Exact<{
  backfillId: string;
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
