import {gql} from '../../apollo-client';
import {METADATA_ENTRY_FRAGMENT} from '../../metadata/MetadataEntryFragment';

const SpecificPartitionAssetConditionEvaluationNodeFragment = gql`
  fragment SpecificPartitionAssetConditionEvaluationNodeFragment on SpecificPartitionAssetConditionEvaluationNode {
    description
    status
    uniqueId
    childUniqueIds
    metadataEntries {
      ...MetadataEntryFragment
    }
    entityKey {
      ... on AssetKey {
        path
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

const UnpartitionedAssetConditionEvaluationNodeFragment = gql`
  fragment UnpartitionedAssetConditionEvaluationNodeFragment on UnpartitionedAssetConditionEvaluationNode {
    description
    entityKey {
      ... on AssetKey {
        path
      }
    }
    startTimestamp
    endTimestamp
    status
    uniqueId
    childUniqueIds
    metadataEntries {
      ...MetadataEntryFragment
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
const PartitionedAssetConditionEvaluationNodeFragment = gql`
  fragment PartitionedAssetConditionEvaluationNodeFragment on PartitionedAssetConditionEvaluationNode {
    description
    startTimestamp
    endTimestamp
    numTrue
    uniqueId
    childUniqueIds
    numTrue
    numCandidates
    entityKey {
      ... on AssetKey {
        path
      }
    }
  }
`;

const NEW_EVALUATION_NODE_FRAGMENT = gql`
  fragment NewEvaluationNodeFragment on AutomationConditionEvaluationNode {
    uniqueId
    expandedLabel
    userLabel
    startTimestamp
    endTimestamp
    numCandidates
    numTrue
    isPartitioned
    childUniqueIds
    entityKey {
      ... on AssetKey {
        path
      }
    }
  }
`;

export const ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT = gql`
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
    isLegacy
    evaluation {
      rootUniqueId
      evaluationNodes {
        ...UnpartitionedAssetConditionEvaluationNodeFragment
        ...PartitionedAssetConditionEvaluationNodeFragment
        ...SpecificPartitionAssetConditionEvaluationNodeFragment
      }
    }
    evaluationNodes {
      ...NewEvaluationNodeFragment
    }
  }

  ${UnpartitionedAssetConditionEvaluationNodeFragment}
  ${PartitionedAssetConditionEvaluationNodeFragment}
  ${SpecificPartitionAssetConditionEvaluationNodeFragment}
  ${NEW_EVALUATION_NODE_FRAGMENT}
`;

export const GET_EVALUATIONS_QUERY = gql`
  query GetEvaluationsQuery(
    $assetKey: AssetKeyInput!
    $assetCheckKey: AssetCheckHandleInput
    $limit: Int!
    $cursor: String
  ) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        autoMaterializePolicy {
          rules {
            description
            decisionType
            className
          }
        }
      }
    }

    assetConditionEvaluationRecordsOrError(
      assetKey: $assetKey
      assetCheckKey: $assetCheckKey
      limit: $limit
      cursor: $cursor
    ) {
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

  ${ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT}
`;

export const GET_SLIM_EVALUATIONS_QUERY = gql`
  query GetSlimEvaluationsQuery(
    $assetKey: AssetKeyInput
    $assetCheckKey: AssetCheckHandleInput
    $limit: Int!
    $cursor: String
  ) {
    assetConditionEvaluationRecordsOrError(
      assetKey: $assetKey
      assetCheckKey: $assetCheckKey
      limit: $limit
      cursor: $cursor
    ) {
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

  ${ASSET_CONDITION_EVALUATION_RECORD_FRAGMENT}
`;

export const GET_EVALUATIONS_SPECIFIC_PARTITION_QUERY = gql`
  query GetEvaluationsSpecificPartitionQuery(
    $assetKey: AssetKeyInput!
    $evaluationId: ID!
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

  ${UnpartitionedAssetConditionEvaluationNodeFragment}
  ${PartitionedAssetConditionEvaluationNodeFragment}
  ${SpecificPartitionAssetConditionEvaluationNodeFragment}
`;

export const ASSET_LAST_EVALUATION_FRAGMENT = gql`
  fragment AssetLastEvaluationFragment on AutoMaterializeAssetEvaluationRecord {
    id
    evaluationId
    timestamp
  }
`;
export const GET_ASSET_EVALUATION_DETAILS_QUERY = gql`
  query GetAssetEvaluationDetailsQuery($assetKeys: [AssetKeyInput!]!, $asOfEvaluationId: ID!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      assetKey {
        path
      }
      lastAutoMaterializationEvaluationRecord(asOfEvaluationId: $asOfEvaluationId) {
        ...AssetLastEvaluationFragment
      }
    }
  }
  ${ASSET_LAST_EVALUATION_FRAGMENT}
`;
