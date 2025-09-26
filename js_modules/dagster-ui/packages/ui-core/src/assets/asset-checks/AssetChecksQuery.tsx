import {
  EXECUTE_CHECKS_BUTTON_ASSET_NODE_FRAGMENT,
  EXECUTE_CHECKS_BUTTON_CHECK_FRAGMENT,
} from './ExecuteChecksButton';
import { ASSET_CHECK_TABLE_FRAGMENT } from './VirtualizedAssetCheckTable';
import { ASSET_CHECK_EXECUTION_FRAGMENT } from './AssetCheckDetailDialog';

import { gql } from '../../apollo-client';
import {
  INSTIGATION_EVENT_LOG_FRAGMENT
} from '../../ticks/InstigationEventLogTable';

const ASSET_CHECK_KEY_FRAGMENT = gql`
  fragment AssetCheckKeyFragment on AssetCheck {
    name
    assetKey {
      path
    }
  }
`;

export const DATA_QUALITY_FRAGMENT = gql`
  fragment DataQualityFragment on DataQualityCheck {
    name
    assetKey {
      path
    }
    description
    config
    checkType
    executionHistory(limit: 100) {
      checkExecution {
        ...AssetCheckExecutionFragment
      }
      logsForExecution(cursor: null) {
        ... on InstigationEventConnection {
          cursor
          hasMore
          events {
            ...InstigationEventLog
          }
        }
      }
    }
  }
  ${ASSET_CHECK_EXECUTION_FRAGMENT}
  ${INSTIGATION_EVENT_LOG_FRAGMENT}
`;

export const ASSET_CHECKS_QUERY = gql`
  query AssetChecksQuery($assetKey: AssetKeyInput!) {
    dataQualityChecksForAsset(assetKey: $assetKey) {
      ...DataQualityFragment
    }
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
  ${DATA_QUALITY_FRAGMENT}
`;
