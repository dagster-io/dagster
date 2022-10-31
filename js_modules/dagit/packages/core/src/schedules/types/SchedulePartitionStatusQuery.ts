/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulePartitionStatusQuery
// ====================================================

export interface SchedulePartitionStatusQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError" | "PythonError";
}

export interface SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: RunStatus | null;
}

export interface SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError = SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PythonError | SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet_partitionStatusesOrError;
}

export interface SchedulePartitionStatusQuery_scheduleOrError_Schedule {
  __typename: "Schedule";
  id: string;
  mode: string;
  pipelineName: string;
  partitionSet: SchedulePartitionStatusQuery_scheduleOrError_Schedule_partitionSet | null;
}

export type SchedulePartitionStatusQuery_scheduleOrError = SchedulePartitionStatusQuery_scheduleOrError_ScheduleNotFoundError | SchedulePartitionStatusQuery_scheduleOrError_Schedule;

export interface SchedulePartitionStatusQuery {
  scheduleOrError: SchedulePartitionStatusQuery_scheduleOrError;
}

export interface SchedulePartitionStatusQueryVariables {
  scheduleSelector: ScheduleSelector;
}
