// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: ReconcileSchedulerState
// ====================================================

export interface ReconcileSchedulerState_reconcileSchedulerState_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ReconcileSchedulerState_reconcileSchedulerState_ReconcileSchedulerStateSuccess {
  __typename: "ReconcileSchedulerStateSuccess";
  message: string;
}

export type ReconcileSchedulerState_reconcileSchedulerState = ReconcileSchedulerState_reconcileSchedulerState_PythonError | ReconcileSchedulerState_reconcileSchedulerState_ReconcileSchedulerStateSuccess;

export interface ReconcileSchedulerState {
  reconcileSchedulerState: ReconcileSchedulerState_reconcileSchedulerState;
}

export interface ReconcileSchedulerStateVariables {
  repositorySelector: RepositorySelector;
}
