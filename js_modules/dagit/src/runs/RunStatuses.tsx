import {PipelineRunStatus} from 'src/types/globalTypes';

export const queuedStatuses = new Set([PipelineRunStatus.QUEUED]);

export const inProgressStatuses = new Set([
  PipelineRunStatus.STARTED,
  PipelineRunStatus.STARTING,
  PipelineRunStatus.CANCELING,
]);

export const doneStatuses = new Set([
  PipelineRunStatus.FAILURE,
  PipelineRunStatus.SUCCESS,
  PipelineRunStatus.CANCELED,
]);
