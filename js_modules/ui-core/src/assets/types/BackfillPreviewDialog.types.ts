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

export type BackfillPreviewQueryVariables = Exact<{
  partitionNames: Array<string> | string;
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type BackfillPreviewQuery = {
  __typename: 'Query';
  assetBackfillPreview: Array<{
    __typename: 'AssetPartitions';
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    partitions: {
      __typename: 'AssetBackfillTargetPartitions';
      partitionKeys: Array<string> | null;
      ranges: Array<{__typename: 'PartitionKeyRange'; start: string; end: string}> | null;
    } | null;
  }>;
};

export const BackfillPreviewQueryVersion = '21a636242bab27144e5627361658207b708cc3e60c149f8901e476c3d9d0b021';
