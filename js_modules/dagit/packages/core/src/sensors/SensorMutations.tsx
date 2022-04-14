import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';

import {StartSensor_startSensor_PythonError, StartSensor} from './types/StartSensor';
import {StopSensor_stopSensor_PythonError, StopSensor} from './types/StopSensor';

export const START_SENSOR_MUTATION = gql`
  mutation StartSensor($sensorSelector: SensorSelector!) {
    startSensor(sensorSelector: $sensorSelector) {
      __typename
      ... on Sensor {
        id
        sensorState {
          id
          status
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const STOP_SENSOR_MUTATION = gql`
  mutation StopSensor($jobOriginId: String!, $jobSelectorId: String!) {
    stopSensor(jobOriginId: $jobOriginId, jobSelectorId: $jobSelectorId) {
      __typename
      ... on StopSensorMutationResult {
        instigationState {
          id
          status
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

type PythonError = StartSensor_startSensor_PythonError | StopSensor_stopSensor_PythonError;

export const displaySensorMutationErrors = (data: StartSensor | StopSensor) => {
  let error: PythonError | null = null;

  if ('startSensor' in data && data.startSensor.__typename === 'PythonError') {
    error = data.startSensor;
  } else if ('stopSensor' in data && data.stopSensor.__typename === 'PythonError') {
    error = data.stopSensor;
  }

  if (error) {
    showCustomAlert({
      title: 'Schedule Response',
      body: <PythonErrorInfo error={error} />,
    });
  }
};
