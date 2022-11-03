/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: CapturedLogsSubscription
// ====================================================

export interface CapturedLogsSubscription_capturedLogs {
  __typename: "CapturedLogs";
  stdout: string | null;
  stderr: string | null;
  cursor: string | null;
}

export interface CapturedLogsSubscription {
  capturedLogs: CapturedLogsSubscription_capturedLogs;
}

export interface CapturedLogsSubscriptionVariables {
  logKey: string[];
  cursor?: string | null;
}
