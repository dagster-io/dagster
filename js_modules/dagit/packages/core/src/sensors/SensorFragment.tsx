import {graphql} from '../graphql';

export const SENSOR_FRAGMENT = graphql(`
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
`);
