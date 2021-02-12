// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionProgressQuery
// ====================================================

export interface PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_runs {
  __typename: "PipelineRun";
  id: string;
  canTerminate: boolean;
  status: PipelineRunStatus;
}

export interface PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  isPersisted: boolean;
  numRequested: number | null;
  numTotal: number | null;
  runs: PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_runs[];
}

export interface PartitionProgressQuery_partitionBackfillOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionProgressQuery_partitionBackfillOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionProgressQuery_partitionBackfillOrError_PythonError_cause | null;
}

export type PartitionProgressQuery_partitionBackfillOrError = PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill | PartitionProgressQuery_partitionBackfillOrError_PythonError;

export interface PartitionProgressQuery {
  partitionBackfillOrError: PartitionProgressQuery_partitionBackfillOrError;
}

export interface PartitionProgressQueryVariables {
  backfillId: string;
  limit?: number | null;
}
