import {gql} from '../../apollo-client';

export const FRESHNESS_EVALUATION_ENABLED_QUERY = gql`
  query FreshnessEvaluationEnabledQuery {
    instance {
      id
      freshnessEvaluationEnabled
    }
  }
`;

export const FRESHNESS_STATUS_QUERY = gql`
  query FreshnessStatusQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        freshnessStatusInfo {
          freshnessStatus
          freshnessStatusMetadata {
            lastMaterializedTimestamp
          }
        }
      }
    }
  }
`;
