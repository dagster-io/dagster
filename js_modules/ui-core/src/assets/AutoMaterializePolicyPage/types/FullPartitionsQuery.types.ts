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

export type PartitionDefinitionType = 'DYNAMIC' | 'MULTIPARTITIONED' | 'STATIC' | 'TIME_WINDOW';

export type FullPartitionsQueryVariables = Exact<{
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
