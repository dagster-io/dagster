// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: ComputeLogsSubscription
// ====================================================

export interface ComputeLogsSubscription_computeLogs {
  __typename: "ComputeLogs";
  stdout: string;
  stderr: string;
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
