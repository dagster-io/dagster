import {gql} from '@apollo/client';

export const PARTITION_SUBSET_LIST_QUERY = gql`
  query PartitionSubsetListQuery(
    $assetKey: AssetKeyInput!
    $evaluationId: Int!
    $nodeUniqueId: String!
  ) {
    truePartitionsForAutomationConditionEvaluationNode(
      assetKey: $assetKey
      evaluationId: $evaluationId
      nodeUniqueId: $nodeUniqueId
    )
  }
`;
