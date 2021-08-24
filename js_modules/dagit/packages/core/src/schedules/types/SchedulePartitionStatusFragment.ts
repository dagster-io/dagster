// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SchedulePartitionStatusFragment
// ====================================================

export interface SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError = SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PythonError | SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface SchedulePartitionStatusFragment_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: SchedulePartitionStatusFragment_partitionSet_partitionStatusesOrError;
}

export interface SchedulePartitionStatusFragment {
  __typename: "Schedule";
  id: string;
  mode: string;
  pipelineName: string;
  partitionSet: SchedulePartitionStatusFragment_partitionSet | null;
}
