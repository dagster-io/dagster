/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CancelBackfill
// ====================================================

export interface CancelBackfill_cancelPartitionBackfill_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface CancelBackfill_cancelPartitionBackfill_CancelBackfillSuccess {
  __typename: "CancelBackfillSuccess";
  backfillId: string;
}

export interface CancelBackfill_cancelPartitionBackfill_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface CancelBackfill_cancelPartitionBackfill_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: CancelBackfill_cancelPartitionBackfill_PythonError_causes[];
}

export type CancelBackfill_cancelPartitionBackfill = CancelBackfill_cancelPartitionBackfill_UnauthorizedError | CancelBackfill_cancelPartitionBackfill_CancelBackfillSuccess | CancelBackfill_cancelPartitionBackfill_PythonError;

export interface CancelBackfill {
  cancelPartitionBackfill: CancelBackfill_cancelPartitionBackfill;
}

export interface CancelBackfillVariables {
  backfillId: string;
}
