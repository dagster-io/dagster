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

export const PartitionSubsetListQueryVersion = 'a99c32a24510b715ad4a4d31421bdd663549665193b4a40bfee5e8238b586313';
