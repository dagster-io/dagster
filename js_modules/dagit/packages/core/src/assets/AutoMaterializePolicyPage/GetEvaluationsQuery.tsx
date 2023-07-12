import {gql} from '@apollo/client';

export const GET_EVALUATIONS_QUERY = gql`
  query GetEvaluationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $cursor: String) {
    autoMaterializeAssetEvaluationsOrError(assetKey: $assetKey, limit: $limit, cursor: $cursor) {
      ... on AutoMaterializeAssetEvaluationRecords {
        currentEvaluationId
        records {
          id
          ...AutoMaterializeEvaluationRecordItem
        }
      }
      ... on AutoMaterializeAssetEvaluationNeedsMigrationError {
        message
      }
    }
  }

  fragment AutoMaterializeEvaluationRecordItem on AutoMaterializeAssetEvaluationRecord {
    id
    evaluationId
    numRequested
    numSkipped
    numDiscarded
    timestamp
    runIds
    conditions {
      ...AutoMateralizeWithConditionFragment
    }
  }

  fragment AutoMateralizeWithConditionFragment on AutoMaterializeConditionWithDecisionType {
    decisionType
    partitionKeysOrError {
      ... on PartitionKeys {
        partitionKeys
      }
    }
    ... on ParentOutdatedAutoMaterializeCondition {
      waitingOnAssetKeys {
        path
      }
    }
  }
`;
