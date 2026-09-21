import {gql} from '../../apollo-client';

export const PARTITION_SUBSET_LIST_QUERY = gql`
  query PartitionSubsetListQuery(
    $assetKey: AssetKeyInput
    $assetJobKey: AssetJobKeyInput
    $evaluationId: ID!
    $nodeUniqueId: String!
  ) {
    truePartitionsForAutomationConditionEvaluationNode(
      assetKey: $assetKey
      assetJobKey: $assetJobKey
      evaluationId: $evaluationId
      nodeUniqueId: $nodeUniqueId
    )
  }
`;
