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

export interface CancelBackfill_cancelPartitionBackfill_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface CancelBackfill_cancelPartitionBackfill_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: CancelBackfill_cancelPartitionBackfill_PythonError_errorChain_error;
}

export interface CancelBackfill_cancelPartitionBackfill_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: CancelBackfill_cancelPartitionBackfill_PythonError_errorChain[];
}

export type CancelBackfill_cancelPartitionBackfill = CancelBackfill_cancelPartitionBackfill_UnauthorizedError | CancelBackfill_cancelPartitionBackfill_CancelBackfillSuccess | CancelBackfill_cancelPartitionBackfill_PythonError;

export interface CancelBackfill {
  cancelPartitionBackfill: CancelBackfill_cancelPartitionBackfill;
}

export interface CancelBackfillVariables {
  backfillId: string;
}
