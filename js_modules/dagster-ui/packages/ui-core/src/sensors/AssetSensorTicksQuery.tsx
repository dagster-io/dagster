import {gql} from '@apollo/client';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {ASSET_DAEMON_TICK_FRAGMENT} from '../assets/auto-materialization/AssetDaemonTicksQuery';

export const ASSET_SENSOR_TICKS_QUERY = gql`
  query AssetSensorTicksQuery(
    $sensorSelector: SensorSelector!
    $dayRange: Int
    $dayOffset: Int
    $statuses: [InstigationTickStatus!]
    $limit: Int
    $cursor: String
    $beforeTimestamp: Float
    $afterTimestamp: Float
  ) {
    sensorOrError(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        sensorState {
          id
          ticks(
            dayRange: $dayRange
            dayOffset: $dayOffset
            statuses: $statuses
            limit: $limit
            cursor: $cursor
            beforeTimestamp: $beforeTimestamp
            afterTimestamp: $afterTimestamp
          ) {
            id
            ...AssetDaemonTickFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${ASSET_DAEMON_TICK_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
