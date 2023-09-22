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
      }
    }

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
    rulesWithRuleEvaluations {
      ...RuleWithEvaluationsFragment
    }
    rules {
      description
      decisionType
      className
    }
  }

  fragment RuleWithEvaluationsFragment on AutoMaterializeRuleWithRuleEvaluations {
    rule {
      description
      decisionType
      className
    }
    ruleEvaluations {
      evaluationData {
        ... on TextRuleEvaluationData {
          text
        }
        ... on ParentMaterializedRuleEvaluationData {
          updatedAssetKeys {
            path
          }
          willUpdateAssetKeys {
            path
          }
        }
        ... on WaitingOnKeysRuleEvaluationData {
          waitingOnAssetKeys {
            path
          }
        }
      }
      partitionKeysOrError {
        ... on PartitionKeys {
          partitionKeys
        }
        ... on Error {
          message
        }
      }
    }
  }
`;
