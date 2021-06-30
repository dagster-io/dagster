import {gql} from '@apollo/client';

import {JOB_STATE_FRAGMENT} from '../jobs/JobUtils';

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
  ${JOB_STATE_FRAGMENT}
`;
