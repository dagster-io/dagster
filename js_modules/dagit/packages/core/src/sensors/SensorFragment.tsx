import {gql} from '@apollo/client';

import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    jobOriginId
    name
    pipelineName
    solidSelection
    mode
    description
    minIntervalSeconds
    nextTick {
      timestamp
    }
    sensorState {
      id
      ...InstigationStateFragment
    }
  }
  ${INSTIGATION_STATE_FRAGMENT}
`;
