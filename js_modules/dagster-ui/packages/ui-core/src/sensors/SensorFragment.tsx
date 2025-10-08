import {gql} from '../apollo-client';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';

export const SENSOR_FRAGMENT = gql`
  fragment SensorFragment on Sensor {
    id
    name
    description
    minIntervalSeconds
    sensorType
    nextTick {
      timestamp
    }
    defaultStatus
    canReset
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
    owners {
      ... on UserDefinitionOwner {
        email
      }
      ... on TeamDefinitionOwner {
        team
      }
    }
  }

  ${INSTIGATION_STATE_FRAGMENT}
`;
