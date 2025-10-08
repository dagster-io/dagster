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
        __typename
        email
      }
      ... on TeamDefinitionOwner {
        __typename
        team
      }
    }
  }

  ${INSTIGATION_STATE_FRAGMENT}
`;
