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

export type PartitionSubsetListQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: string;
  nodeUniqueId: string;
}>;

export type PartitionSubsetListQuery = {
  __typename: 'Query';
  truePartitionsForAutomationConditionEvaluationNode: Array<string>;
};

export const PartitionSubsetListQueryVersion = '9a560790b6c1828137f31532f5879cfb6611d9ca8c14b7f315464510b6a4bd75';
