import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {graphql} from '../graphql';
import {StartSensorMutation, StopRunningSensorMutation} from '../graphql/graphql';

export const START_SENSOR_MUTATION = graphql(`
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
`);

export const STOP_SENSOR_MUTATION = graphql(`
  mutation StopRunningSensor($jobOriginId: String!, $jobSelectorId: String!) {
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
`);

export const displaySensorMutationErrors = (
  data: StartSensorMutation | StopRunningSensorMutation,
) => {
  let error;
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
