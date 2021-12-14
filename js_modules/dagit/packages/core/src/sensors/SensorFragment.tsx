import {gql} from '@apollo/client';

import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    jobOriginId
    name
    description
    minIntervalSeconds
    nextTick {
      timestamp
    }
    sensorState {
      id
      ...InstigationStateFragment
    }
    targets {
      pipelineName
      solidSelection
      mode
    }
    metadata {
      assetKeys {
        path
      }
    }
  }
  ${INSTIGATION_STATE_FRAGMENT}
`;
