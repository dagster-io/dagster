// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: ComputeLogsSubscription
// ====================================================

export interface ComputeLogsSubscription_computeLogs_stdout {
  __typename: "ComputeLogFile";
  data: string;
}

export interface ComputeLogsSubscription_computeLogs_stderr {
  __typename: "ComputeLogFile";
  data: string;
}

export interface ComputeLogsSubscription_computeLogs {
  __typename: "ComputeLogs";
  stdout: ComputeLogsSubscription_computeLogs_stdout | null;
  stderr: ComputeLogsSubscription_computeLogs_stderr | null;
  cursor: any | null;
}

export interface ComputeLogsSubscription {
  computeLogs: ComputeLogsSubscription_computeLogs;
}

export interface ComputeLogsSubscriptionVariables {
  runId: string;
  stepKey: string;
  cursor?: any | null;
}
