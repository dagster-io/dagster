/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CapturedLogsMetadataQuery
// ====================================================

export interface CapturedLogsMetadataQuery_capturedLogsMetadata {
  __typename: "CapturedLogsMetadata";
  stdoutDownloadUrl: string | null;
  stdoutLocation: string | null;
  stderrDownloadUrl: string | null;
  stderrLocation: string | null;
}

export interface CapturedLogsMetadataQuery {
  capturedLogsMetadata: CapturedLogsMetadataQuery_capturedLogsMetadata;
}

export interface CapturedLogsMetadataQueryVariables {
  logKey: string[];
}
