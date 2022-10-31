/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionStatusQuery
// ====================================================

export interface PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: RunStatus | null;
}

export interface PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export interface PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError_causes[];
}

export type PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError = PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses | PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError;

export interface PartitionStatusQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: PartitionStatusQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError;
}

export interface PartitionStatusQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError";
  message: string;
}

export interface PartitionStatusQuery_partitionSetOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionStatusQuery_partitionSetOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionStatusQuery_partitionSetOrError_PythonError_causes[];
}

export type PartitionStatusQuery_partitionSetOrError = PartitionStatusQuery_partitionSetOrError_PartitionSet | PartitionStatusQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionStatusQuery_partitionSetOrError_PythonError;

export interface PartitionStatusQuery {
  partitionSetOrError: PartitionStatusQuery_partitionSetOrError;
}

export interface PartitionStatusQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
}
