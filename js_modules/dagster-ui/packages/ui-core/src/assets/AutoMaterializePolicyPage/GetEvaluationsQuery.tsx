import {gql} from '@apollo/client';

export const GET_EVALUATIONS_QUERY = gql`
  query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
        autoMaterializePolicy {
          rules {
            description
            decisionType
            className
          }
        }
        currentAutoMaterializeEvaluationId
      }
    }

    assetConditionEvaluationRecordsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
      ... on AssetConditionEvaluationRecords {
        records {
          id
          ...AssetConditionEvaluationRecordFragment
        }
      }
      ... on AutoMaterializeAssetEvaluationNeedsMigrationError {
        message
      }
    }
  }

  fragment AssetConditionEvaluationRecordFragment on AssetConditionEvaluationRecord {
    id
    evaluationId
    numRequested
    assetKey {
      path
    }
    runIds
    timestamp
    startTimestamp
    endTimestamp
    evaluation {
      rootUniqueId
      evaluationNodes {
        ...UnpartitionedAssetConditionEvaluationNodeFragment
        ...PartitionedAssetConditionEvaluationNodeFragment
        ...SpecificPartitionAssetConditionEvaluationNodeFragment
      }
    }
  }

  fragment UnpartitionedAssetConditionEvaluationNodeFragment on UnpartitionedAssetConditionEvaluationNode {
    description
    startTimestamp
    endTimestamp
    status
    uniqueId
    childUniqueIds
  }
  fragment PartitionedAssetConditionEvaluationNodeFragment on PartitionedAssetConditionEvaluationNode {
    description
    startTimestamp
    endTimestamp
    numTrue
    numFalse
    numSkipped
    trueSubset {
      ...AssetSubsetFragment
    }
    falseSubset {
      ...AssetSubsetFragment
    }
    candidateSubset {
      ...AssetSubsetFragment
    }
    uniqueId
    childUniqueIds
  }
  fragment SpecificPartitionAssetConditionEvaluationNodeFragment on SpecificPartitionAssetConditionEvaluationNode {
    description
    status
    uniqueId
    childUniqueIds
  }

  fragment AssetSubsetFragment on AssetSubset {
    subsetValue {
      isPartitioned
      partitionKeys
      partitionKeyRanges {
        start
        end
      }
    }
  }
`;

export const GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY = gql`
  query GetEvaluationsSpecificPartitionQuery(
    $assetKey: AssetKeyInput!
    $evaluationId: Int!
    $partition: String!
  ) {
    assetConditionEvaluationForPartition(
      assetKey: $assetKey
      evaluationId: $evaluationId
      partition: $partition
    ) {
      rootUniqueId
      evaluationNodes {
        ...UnpartitionedAssetConditionEvaluationNodeFragment
        ...PartitionedAssetConditionEvaluationNodeFragment
        ...SpecificPartitionAssetConditionEvaluationNodeFragment
      }
    }
  }

  fragment UnpartitionedAssetConditionEvaluationNodeFragment on UnpartitionedAssetConditionEvaluationNode {
    description
    startTimestamp
    endTimestamp
    status
    uniqueId
    childUniqueIds
  }
  fragment PartitionedAssetConditionEvaluationNodeFragment on PartitionedAssetConditionEvaluationNode {
    description
    startTimestamp
    endTimestamp
    numTrue
    numFalse
    numSkipped
    trueSubset {
      ...AssetSubsetFragment
    }
    falseSubset {
      ...AssetSubsetFragment
    }
    candidateSubset {
      ...AssetSubsetFragment
    }
    uniqueId
    childUniqueIds
  }
  fragment SpecificPartitionAssetConditionEvaluationNodeFragment on SpecificPartitionAssetConditionEvaluationNode {
    description
    status
    uniqueId
    childUniqueIds
  }

  fragment AssetSubsetFragment on AssetSubset {
    subsetValue {
      isPartitioned
      partitionKeys
      partitionKeyRanges {
        start
        end
      }
    }
  }
`;
