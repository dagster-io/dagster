import {gql} from '../apollo-client';

export const RUN_FEED_TARGET_ASSET_SELECTION_QUERY = gql`
  query RunFeedTargetAssetSelectionQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        assetSelection {
          ... on AssetKey {
            path
          }
        }
        assetCheckSelection {
          name
          assetKey {
            path
          }
        }
      }
    }
  }
`;
