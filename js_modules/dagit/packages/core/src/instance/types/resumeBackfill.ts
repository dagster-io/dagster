/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: resumeBackfill
// ====================================================

export interface resumeBackfill_resumePartitionBackfill_ResumeBackfillSuccess {
  __typename: "ResumeBackfillSuccess";
  backfillId: string;
}

export interface resumeBackfill_resumePartitionBackfill_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface resumeBackfill_resumePartitionBackfill_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface resumeBackfill_resumePartitionBackfill_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: resumeBackfill_resumePartitionBackfill_PythonError_causes[];
}

export type resumeBackfill_resumePartitionBackfill = resumeBackfill_resumePartitionBackfill_ResumeBackfillSuccess | resumeBackfill_resumePartitionBackfill_UnauthorizedError | resumeBackfill_resumePartitionBackfill_PythonError;

export interface resumeBackfill {
  resumePartitionBackfill: resumeBackfill_resumePartitionBackfill;
}

export interface resumeBackfillVariables {
  backfillId: string;
}
