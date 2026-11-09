import {gql} from '../apollo-client';
import {
  ResetSensorMutation,
  StartSensorMutation,
  StopRunningSensorMutation,
} from './types/SensorMutations.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {showMutationErrorToast} from '../app/showMutationErrorToast';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';

export const START_SENSOR_MUTATION = gql`
  mutation StartSensor($sensorSelector: SensorSelector!) {
    startSensor(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        sensorState {
          ...InstigationStateBaseFragment
        }
      }
      ... on SensorNotFoundError {
        message
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${INSTIGATION_STATE_BASE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const STOP_SENSOR_MUTATION = gql`
  mutation StopRunningSensor($id: String!) {
    stopSensor(id: $id) {
      ... on StopSensorMutationResult {
        instigationState {
          ...InstigationStateBaseFragment
        }
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${INSTIGATION_STATE_BASE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const RESET_SENSOR_MUTATION = gql`
  mutation ResetSensor($sensorSelector: SensorSelector!) {
    resetSensor(sensorSelector: $sensorSelector) {
      ... on Sensor {
        id
        sensorState {
          id
          status
        }
      }
      ... on SensorNotFoundError {
        message
      }
      ... on UnauthorizedError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const displaySensorMutationErrors = (
  data: StartSensorMutation | StopRunningSensorMutation | ResetSensorMutation,
) => {
  if ('startSensor' in data) {
    showMutationErrorToast(data.startSensor, 'Sensor', 'Could not start sensor.');
  } else if ('stopSensor' in data) {
    showMutationErrorToast(data.stopSensor, 'StopSensorMutationResult', 'Could not stop sensor.');
  } else if ('resetSensor' in data) {
    showMutationErrorToast(data.resetSensor, 'Sensor', 'Could not reset sensor.');
  }
};
