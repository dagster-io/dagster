/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionsStatusQuery
// ====================================================

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export type PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError | PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions;

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionRuns_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionRuns {
  __typename: "PartitionRun";
  id: string;
  partitionName: string;
  run: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionRuns_run | null;
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: RunStatus | null;
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError_cause | null;
}

export type PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError = PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses | PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError;

export interface PartitionsStatusQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  pipelineName: string;
  partitionsOrError: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionsOrError;
  partitionRuns: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionRuns[];
  partitionStatusesOrError: PartitionsStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError;
}

export type PartitionsStatusQuery_partitionSetOrError = PartitionsStatusQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionsStatusQuery_partitionSetOrError_PartitionSet;

export interface PartitionsStatusQuery {
  partitionSetOrError: PartitionsStatusQuery_partitionSetOrError;
}

export interface PartitionsStatusQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
}
