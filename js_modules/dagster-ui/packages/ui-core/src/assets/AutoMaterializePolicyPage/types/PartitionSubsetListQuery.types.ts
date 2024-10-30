// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type PartitionSubsetListQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: Types.Scalars['BigInt']['input'];
  nodeUniqueId: Types.Scalars['String']['input'];
}>;

export type PartitionSubsetListQuery = {
  __typename: 'Query';
  truePartitionsForAutomationConditionEvaluationNode: Array<string>;
};

export const PartitionSubsetListQueryVersion = '2c8c8f7bd10e0be6ef37e833057c78ca202b23f0bc89dafe4e8a12389e3fe2b8';
