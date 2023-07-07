import {MockedResponse} from '@apollo/client/testing';

import {
  InstigationStatus,
  buildInstigationState,
  buildScheduleStateResult,
  buildUnauthorizedError,
} from '../../graphql/types';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {START_SCHEDULE_MUTATION, STOP_SCHEDULE_MUTATION} from '../ScheduleMutations';
import {StartThisScheduleMutation, StopScheduleMutation} from '../types/ScheduleMutations.types';

const repoAddress = buildRepoAddress('foo', 'bar');

export const scheduleAlaskaCurrentlyStopped = {
  repoAddress,
  scheduleName: 'alaska',
  scheduleState: buildInstigationState({
    status: InstigationStatus.STOPPED,
    hasStartPermission: true,
    hasStopPermission: true,
  }),
};

export const scheduleColoradoCurrentlyStopped = {
  repoAddress,
  scheduleName: 'colorado',
  scheduleState: buildInstigationState({
    status: InstigationStatus.STOPPED,
  }),
};

export const scheduleDelawareCurrentlyRunning = {
  repoAddress,
  scheduleName: 'delaware',
  scheduleState: buildInstigationState({
    id: 'delaware-state-id',
    selectorId: 'delaware-selector',
    status: InstigationStatus.RUNNING,
  }),
};

export const scheduleHawaiiCurrentlyRunning = {
  repoAddress,
  scheduleName: 'hawaii',
  scheduleState: buildInstigationState({
    id: 'hawaii-state-id',
    selectorId: 'hawaii-selector',
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
        scheduleOriginId: 'delaware-state-id',
        scheduleSelectorId: 'delaware-selector',
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
        scheduleOriginId: 'hawaii-state-id',
        scheduleSelectorId: 'hawaii-selector',
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
        scheduleOriginId: 'hawaii-state-id',
        scheduleSelectorId: 'hawaii-selector',
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
