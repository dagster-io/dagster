import {MockedResponse} from '@apollo/client/testing';

import {
  InstigationStatus,
  buildInstigationState,
  buildScheduleStateResult,
  buildSensor,
  buildStopSensorMutationResult,
  buildUnauthorizedError,
} from '../../graphql/types';
import {START_SCHEDULE_MUTATION, STOP_SCHEDULE_MUTATION} from '../../schedules/ScheduleMutations';
import {
  StartThisScheduleMutation,
  StopScheduleMutation,
} from '../../schedules/types/ScheduleMutations.types';
import {START_SENSOR_MUTATION, STOP_SENSOR_MUTATION} from '../../sensors/SensorMutations';
import {
  StartSensorMutation,
  StopRunningSensorMutation,
} from '../../sensors/types/SensorMutations.types';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';

const repoAddress = buildRepoAddress('foo', 'bar');

export const scheduleAlaskaCurrentlyStopped = {
  repoAddress,
  name: 'alaska',
  type: 'schedule' as const,
  instigationState: buildInstigationState({
    status: InstigationStatus.STOPPED,
    hasStartPermission: true,
    hasStopPermission: true,
  }),
};

export const scheduleColoradoCurrentlyStopped = {
  repoAddress,
  name: 'colorado',
  type: 'schedule' as const,
  instigationState: buildInstigationState({
    status: InstigationStatus.STOPPED,
  }),
};

export const scheduleDelawareCurrentlyRunning = {
  repoAddress,
  name: 'delaware',
  type: 'schedule' as const,
  instigationState: buildInstigationState({
    id: 'delaware-id',
    status: InstigationStatus.RUNNING,
  }),
};

export const scheduleHawaiiCurrentlyRunning = {
  repoAddress,
  name: 'hawaii',
  type: 'schedule' as const,
  instigationState: buildInstigationState({
    id: 'hawaii-id',
    status: InstigationStatus.RUNNING,
  }),
};

export const buildStartAlaskaSuccess = (delay = 0): MockedResponse<StartThisScheduleMutation> => {
  return {
    request: {
      query: START_SCHEDULE_MUTATION,
      variables: {
        scheduleSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          scheduleName: 'alaska',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSchedule: buildScheduleStateResult({
          scheduleState: buildInstigationState({
            status: InstigationStatus.RUNNING,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStartColoradoSuccess = (delay = 0): MockedResponse<StartThisScheduleMutation> => {
  return {
    request: {
      query: START_SCHEDULE_MUTATION,
      variables: {
        scheduleSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          scheduleName: 'colorado',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSchedule: buildScheduleStateResult({
          scheduleState: buildInstigationState({
            status: InstigationStatus.RUNNING,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStartColoradoError = (delay = 0): MockedResponse<StartThisScheduleMutation> => {
  return {
    request: {
      query: START_SCHEDULE_MUTATION,
      variables: {
        scheduleSelector: {
          repositoryLocationName: repoAddress.location,
          repositoryName: repoAddress.name,
          scheduleName: 'colorado',
        },
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        startSchedule: buildUnauthorizedError({
          message: 'lol u cannot',
        }),
      },
    },
    delay,
  };
};

export const buildStopDelawareSuccess = (delay = 0): MockedResponse<StopScheduleMutation> => {
  return {
    request: {
      query: STOP_SCHEDULE_MUTATION,
      variables: {
        id: 'delaware-id',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopRunningSchedule: buildScheduleStateResult({
          scheduleState: buildInstigationState({
            status: InstigationStatus.STOPPED,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStopHawaiiSuccess = (delay = 0): MockedResponse<StopScheduleMutation> => {
  return {
    request: {
      query: STOP_SCHEDULE_MUTATION,
      variables: {
        id: 'hawaii-id',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopRunningSchedule: buildScheduleStateResult({
          scheduleState: buildInstigationState({
            status: InstigationStatus.STOPPED,
          }),
        }),
      },
    },
    delay,
  };
};

export const buildStopHawaiiError = (delay = 0): MockedResponse<StopScheduleMutation> => {
  return {
    request: {
      query: STOP_SCHEDULE_MUTATION,
      variables: {
        id: 'hawaii-id',
      },
    },
    result: {
      data: {
        __typename: 'Mutation',
        stopRunningSchedule: buildUnauthorizedError({
          message: 'lol u cannot',
        }),
      },
    },
    delay,
  };
};

export const sensorKansasCurrentlyStopped = {
  repoAddress,
  name: 'kansas',
  type: 'sensor' as const,
  instigationState: buildInstigationState({
    status: InstigationStatus.STOPPED,
    hasStartPermission: true,
    hasStopPermission: true,
  }),
};

export const sensorLouisianaCurrentlyStopped = {
  repoAddress,
  name: 'louisiana',
  type: 'sensor' as const,
  instigationState: buildInstigationState({
    status: InstigationStatus.STOPPED,
  }),
};

export const sensorMinnesotaCurrentlyRunning = {
  repoAddress,
  name: 'minnesota',
  type: 'sensor' as const,
  instigationState: buildInstigationState({
    id: 'minnesota-id',
    status: InstigationStatus.RUNNING,
  }),
};

export const sensorOregonCurrentlyRunning = {
  repoAddress,
  name: 'oregon',
  type: 'sensor' as const,
  instigationState: buildInstigationState({
    id: 'oregon-id',
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
        id: 'minnesota-id',
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
        id: 'oregon-id',
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
        id: 'oregon-id',
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
