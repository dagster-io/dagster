import {RunStatus} from '../graphql/types';

export const queuedStatuses = new Set([RunStatus.QUEUED]);

export const inProgressStatuses = new Set([
  RunStatus.STARTED,
  RunStatus.STARTING,
  RunStatus.CANCELING,
]);

export const successStatuses = new Set([RunStatus.SUCCESS]);
export const failedStatuses = new Set([RunStatus.FAILURE, RunStatus.CANCELED]);

export const doneStatuses = new Set([RunStatus.FAILURE, RunStatus.SUCCESS, RunStatus.CANCELED]);

export const cancelableStatuses = new Set([RunStatus.QUEUED, RunStatus.STARTED]);
