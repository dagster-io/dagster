import {gql} from '@apollo/client';

import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';

export const ASSET_DAMEON_TICKS_QUERY = gql`
  query AssetDaemonTicksQuery(
    $dayRange: Int
    $dayOffset: Int
    $statuses: [InstigationTickStatus!]
    $limit: Int
    $cursor: String
  ) {
    autoMaterializeTicks(
      dayRange: $dayRange
      dayOffset: $dayOffset
      statuses: $statuses
      limit: $limit
      cursor: $cursor
    ) {
      id
      ...AssetDaemonTickFragment
    }
  }

  fragment AssetDaemonTickFragment on InstigationTick {
    id
    timestamp
    endTimestamp
    status
    instigationType
    error {
      ...PythonErrorFragment
    }
    requestedAssetKeys {
      path
    }
    requestedAssetMaterializationCount
    autoMaterializeAssetEvaluationId
    requestedMaterializationsForAssets {
      assetKey {
        path
      }
      partitionKeys
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
