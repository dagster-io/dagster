import {gql} from '@apollo/client';

import {JOB_STATE_FRAGMENT} from 'src/jobs/JobUtils';

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    jobOriginId
    name
    pipelineName
    solidSelection
    mode
    minIntervalSeconds
    nextTick {
      timestamp
    }
    sensorState {
      id
      ...JobStateFragment
    }
  }
  ${JOB_STATE_FRAGMENT}
`;
