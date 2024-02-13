import {MockedResponse} from '@apollo/client/testing';

import {
  InstigationStatus,
  buildInstigationState,
  buildSensor,
  buildStopSensorMutationResult,
  buildUnauthorizedError,
} from '../../graphql/types';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {START_SENSOR_MUTATION, STOP_SENSOR_MUTATION} from '../SensorMutations';
import {StartSensorMutation, StopRunningSensorMutation} from '../types/SensorMutations.types';

const repoAddress = buildRepoAddress('foo', 'bar');

export const sensorKansasCurrentlyStopped = {
  repoAddress,
  sensorName: 'kansas',
  sensorState: buildInstigationState({
    status: InstigationStatus.STOPPED,
    hasStartPermission: true,
    hasStopPermission: true,
  }),
};

export const sensorLouisianaCurrentlyStopped = {
  repoAddress,
  sensorName: 'louisiana',
  sensorState: buildInstigationState({
    status: InstigationStatus.STOPPED,
  }),
};

export const sensorMinnesotaCurrentlyRunning = {
  repoAddress,
  sensorName: 'minnesota',
  sensorState: buildInstigationState({
    id: 'minnesota-state-id',
    selectorId: 'minnesota-selector',
    status: InstigationStatus.RUNNING,
  }),
};

export const sensorOregonCurrentlyRunning = {
  repoAddress,
  sensorName: 'oregon',
  sensorState: buildInstigationState({
    id: 'oregon-state-id',
    selectorId: 'oregon-selector',
    status: InstigationStatus.RUNNING,
  }),
};

export const buildStartKansasSuccess = (delay = 0): MockedResponse<StartSensorMutation> => {
  return {
    request: {
      query: START_SENSOR_MUTATION,
      variables: {
        sensorSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          sensorName: 'kansas',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSensor: buildSensor({
          sensorState: buildInstigationState({
            status: InstigationStatus.RUNNING,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStartLouisianaSuccess = (delay = 0): MockedResponse<StartSensorMutation> => {
  return {
    request: {
      query: START_SENSOR_MUTATION,
      variables: {
        sensorSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          sensorName: 'louisiana',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSensor: buildSensor({
          sensorState: buildInstigationState({
            status: InstigationStatus.RUNNING,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStartLouisianaError = (delay = 0): MockedResponse<StartSensorMutation> => {
  return {
    request: {
      query: START_SENSOR_MUTATION,
      variables: {
        sensorSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          sensorName: 'louisiana',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSensor: buildUnauthorizedError({
          message: 'lol u cannot',
        }),
      },
    },
    delay,
  };
};

export const buildStopMinnesotaSuccess = (delay = 0): MockedResponse<StopRunningSensorMutation> => {
  return {
    request: {
      query: STOP_SENSOR_MUTATION,
      variables: {
        jobOriginId: 'minnesota-state-id',
        jobSelectorId: 'minnesota-selector',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopSensor: buildStopSensorMutationResult({
          instigationState: buildInstigationState({
            status: InstigationStatus.STOPPED,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStopOregonSuccess = (delay = 0): MockedResponse<StopRunningSensorMutation> => {
  return {
    request: {
      query: STOP_SENSOR_MUTATION,
      variables: {
        jobOriginId: 'oregon-state-id',
        jobSelectorId: 'oregon-selector',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopSensor: buildStopSensorMutationResult({
          instigationState: buildInstigationState({
            status: InstigationStatus.STOPPED,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStopOregonError = (delay = 0): MockedResponse<StopRunningSensorMutation> => {
  return {
    request: {
      query: STOP_SENSOR_MUTATION,
      variables: {
        jobOriginId: 'oregon-state-id',
        jobSelectorId: 'oregon-selector',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopSensor: buildUnauthorizedError({
          message: 'lol u cannot',
        }),
      },
    },
    delay,
  };
};
