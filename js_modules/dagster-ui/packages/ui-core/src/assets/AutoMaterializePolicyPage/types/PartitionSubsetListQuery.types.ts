// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type PartitionSubsetListQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  evaluationId: Types.Scalars['Int']['input'];
  nodeUniqueId: Types.Scalars['String']['input'];
}>;

export type PartitionSubsetListQuery = {
  __typename: 'Query';
  truePartitionsForAutomationConditionEvaluationNode: Array<string>;
};
