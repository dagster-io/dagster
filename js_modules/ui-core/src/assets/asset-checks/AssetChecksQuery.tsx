import {
  EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT,
  EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT,
} from './ExecuteChecksButton';
import {ASSET_CHECK_TABLE_FRAGMENT} from './VirtualizedAssetCheckTable';
import {gql} from '../../apollo-client';

const ASSET_CHECK_KEY_FRAGMENT = gql`
  fragment AssetCheckKeyFragment on AssetCheck {
    name
    assetKey {
      path
    }
  }
`;

export const ASSET_CHECK_PARTITION_FRAGMENT = gql`
  fragment AssetCheckPartitionFragment on AssetCheck {
    partitionDefinition {
      description
      dimensionTypes {
        type
        dynamicPartitionsDefinitionName
      }
    }
  }
`;

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
              ...AssetCheckKeyFragment
              ...ExecuteChecksButtonCheckFragment
              ...AssetCheckTableFragment
              ...AssetCheckPartitionFragment
            }
          }
        }
      }
    }
  }

  ${EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT}
  ${EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT}
  ${ASSET_CHECK_TABLE_FRAGMENT}
  ${ASSET_CHECK_KEY_FRAGMENT}
  ${ASSET_CHECK_PARTITION_FRAGMENT}
`;
