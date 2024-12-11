import {
  EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT,
  EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT,
} from './ExecuteChecksButton';
import {ASSET_CHECK_TABLE_FRAGMENT} from './VirtualizedAssetCheckTable';
import {gql} from '../../apollo-client';

export const ASSET_CHECKS_QUERY = gql`
  query AssetChecksQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        ...ExecuteChecksButtonAssetNodeFragment

        assetChecksOrError {
          ... on AssetCheckNeedsMigrationError {
            message
          }
          ... on AssetChecks {
            checks {
              ...ExecuteChecksButtonCheckFragment
              ...AssetCheckTableFragment
            }
          }
        }
      }
    }
  }
  ${EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT}
  ${EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT}
  ${ASSET_CHECK_TABLE_FRAGMENT}
`;
