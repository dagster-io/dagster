import {gql} from '@apollo/client';

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    name
    pipelineName
    solidSelection
    mode
    status
    runs(limit: 20) {
      id
      runId
      pipelineName
      status
    }
    ticks(limit: 1) {
      id
      status
      timestamp
    }
  }
`;
