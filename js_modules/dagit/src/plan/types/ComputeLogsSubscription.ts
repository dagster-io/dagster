// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: ComputeLogsSubscription
// ====================================================

export interface ComputeLogsSubscription_computeLogs_stdout {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogsSubscription_computeLogs_stderr {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogsSubscription_computeLogs {
  __typename: "ComputeLogs";
  stdout: ComputeLogsSubscription_computeLogs_stdout | null;
  stderr: ComputeLogsSubscription_computeLogs_stderr | null;
  cursor: string;
}

export interface ComputeLogsSubscription {
  computeLogs: ComputeLogsSubscription_computeLogs;
}

export interface ComputeLogsSubscriptionVariables {
  runId: string;
  stepKey: string;
  cursor?: string | null;
}
