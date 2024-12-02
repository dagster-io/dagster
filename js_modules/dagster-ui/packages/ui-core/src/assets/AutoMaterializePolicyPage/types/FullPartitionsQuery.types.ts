// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type FullPartitionsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type FullPartitionsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        partitionKeysByDimension: Array<{
          __typename: 'DimensionPartitionKeys';
          name: string;
          type: Types.PartitionDefinitionType;
          partitionKeys: Array<string>;
        }>;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const FullPartitionsQueryVersion = 'bfe939600c7396798b3c92b0e8335e639c9d76479c1cecaabc309a83c8f7ca4d';
