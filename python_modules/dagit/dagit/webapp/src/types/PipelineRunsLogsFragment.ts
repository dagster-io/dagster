

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunsLogsFragment
// ====================================================

export interface PipelineRunsLogsFragment_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineRunsLogsFragment_logs_nodes {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
}

export interface PipelineRunsLogsFragment_logs {
  pageInfo: PipelineRunsLogsFragment_logs_pageInfo;
  nodes: PipelineRunsLogsFragment_logs_nodes[];
}

export interface PipelineRunsLogsFragment {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineRunsLogsFragment_logs;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================