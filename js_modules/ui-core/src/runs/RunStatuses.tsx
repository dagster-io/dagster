import {RunStatus} from '../graphql/types';

export const queuedStatuses = new Set([RunStatus.QUEUED]);

export const inProgressStatuses = new Set([
  RunStatus.STARTED,
  RunStatus.STARTING,
  RunStatus.SUSPENDED,
  RunStatus.CANCELING,
]);

// In-progress runs that have a run worker. A suspended run is in progress but holds no
// concurrency or pool slot, so views about slots use this set.
export const activeStatuses = new Set([RunStatus.STARTED, RunStatus.STARTING, RunStatus.CANCELING]);

export const successStatuses = new Set([RunStatus.SUCCESS]);

export const failedStatuses = new Set([RunStatus.FAILURE, RunStatus.CANCELED]);

export const doneStatuses = new Set([RunStatus.FAILURE, RunStatus.SUCCESS, RunStatus.CANCELED]);

export const cancelableStatuses = new Set([RunStatus.QUEUED, RunStatus.STARTED]);
