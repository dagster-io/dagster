import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';

export const REPORT_CHECK_EVALUATION_MUTATION = gql`
  mutation ReportCheckEvaluationMutation($eventParams: ReportAssetCheckEvaluationsParams!) {
    reportAssetCheckEvaluations(eventParams: $eventParams) {
      ...PythonErrorFragment
      ... on UnauthorizedError {
        message
      }
      ... on ReportAssetCheckEvaluationsSuccess {
        assetKey {
          path
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

export const REPORT_EVENT_PARTITION_DEFINITION_QUERY = gql`
  query ReportEventPartitionDefinitionQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
        partitionDefinition {
          type
          name
          dimensionTypes {
            type
            name
            dynamicPartitionsDefinitionName
          }
        }
      }
    }
  }
`;
