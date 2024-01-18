// Generated GraphQL types, do not edit manually.
import * as Types from '../../graphql/types';

export type BackfillPreviewQueryVariables = Types.Exact<{
  partitionNames: Array<Types.Scalars['String']> | Types.Scalars['String'];
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
