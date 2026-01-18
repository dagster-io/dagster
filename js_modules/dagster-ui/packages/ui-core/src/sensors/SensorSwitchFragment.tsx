import {gql} from '../apollo-client';

export const SENSOR_SWITCH_FRAGMENT = gql`
  fragment SensorSwitchFragment on Sensor {
    id
    name
    sensorState {
      id
      selectorId
      status
      typeSpecificData {
        ... on SensorData {
          lastCursor
        }
      }
      hasStartPermission
      hasStopPermission
    }
    sensorType
  }
`;
