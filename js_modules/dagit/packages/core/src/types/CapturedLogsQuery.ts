/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CapturedLogsQuery
// ====================================================

export interface CapturedLogsQuery_capturedLogs {
  __typename: "CapturedLogs";
  stdout: string | null;
  stderr: string | null;
  cursor: string | null;
}

export interface CapturedLogsQuery {
  capturedLogs: CapturedLogsQuery_capturedLogs;
}

export interface CapturedLogsQueryVariables {
  logKey: string[];
  cursor?: string | null;
  limit?: number | null;
}
