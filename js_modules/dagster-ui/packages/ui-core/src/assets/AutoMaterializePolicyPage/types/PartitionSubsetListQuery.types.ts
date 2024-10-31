// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type PartitionSubsetListQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: Types.Scalars['ID']['input'];
  nodeUniqueId: Types.Scalars['String']['input'];
}>;

export type PartitionSubsetListQuery = {
  __typename: 'Query';
  truePartitionsForAutomationConditionEvaluationNode: Array<string>;
};

export const PartitionSubsetListQueryVersion = '9a560790b6c1828137f31532f5879cfb6611d9ca8c14b7f315464510b6a4bd75';
