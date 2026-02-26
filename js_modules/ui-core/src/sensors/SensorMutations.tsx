import {gql} from '../apollo-client';
import {
  ResetSensorMutation,
  StartSensorMutation,
  StopRunningSensorMutation,
} from './types/SensorMutations.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
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
  let error;
  if ('startSensor' in data && data.startSensor.__typename === 'PythonError') {
    error = data.startSensor;
  } else if ('stopSensor' in data && data.stopSensor.__typename === 'PythonError') {
    error = data.stopSensor;
  } else if ('resetSensor' in data && data.resetSensor.__typename === 'PythonError') {
    error = data.resetSensor;
  }

  if (error) {
    showCustomAlert({
      title: 'Sensor Response',
      body: <PythonErrorInfo error={error} />,
    });
  }
};
