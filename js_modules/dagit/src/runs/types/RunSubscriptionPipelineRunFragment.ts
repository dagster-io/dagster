/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunSubscriptionPipelineRunFragment
// ====================================================

export interface RunSubscriptionPipelineRunFragment_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface RunSubscriptionPipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  pageInfo: RunSubscriptionPipelineRunFragment_logs_pageInfo;
}

export interface RunSubscriptionPipelineRunFragment {
  __typename: "PipelineRun";
  runId: string;
  logs: RunSubscriptionPipelineRunFragment_logs;
}
