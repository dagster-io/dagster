// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ComputeLogsSubscriptionFragment
// ====================================================

export interface ComputeLogsSubscriptionFragment_stdout {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogsSubscriptionFragment_stderr {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogsSubscriptionFragment {
  __typename: "ComputeLogs";
  stdout: ComputeLogsSubscriptionFragment_stdout | null;
  stderr: ComputeLogsSubscriptionFragment_stderr | null;
  cursor: string;
}
