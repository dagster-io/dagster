

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionFragment
// ====================================================

export interface PipelineExecutionFragment_environmentType {
  name: string;
}

export interface PipelineExecutionFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type = PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_RegularType | PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineExecutionFragment_contexts_config_type_CompositeType_fields[];
}

export type PipelineExecutionFragment_contexts_config_type = PipelineExecutionFragment_contexts_config_type_RegularType | PipelineExecutionFragment_contexts_config_type_CompositeType;

export interface PipelineExecutionFragment_contexts_config {
  type: PipelineExecutionFragment_contexts_config_type;
}

export interface PipelineExecutionFragment_contexts {
  config: PipelineExecutionFragment_contexts_config | null;
}

export interface PipelineExecutionFragment_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionFragment_runs_logs_nodes {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
}

export interface PipelineExecutionFragment_runs_logs {
  pageInfo: PipelineExecutionFragment_runs_logs_pageInfo;
  nodes: PipelineExecutionFragment_runs_logs_nodes[];
}

export interface PipelineExecutionFragment_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionFragment_runs_logs;
}

export interface PipelineExecutionFragment {
  name: string;
  environmentType: PipelineExecutionFragment_environmentType;
  contexts: PipelineExecutionFragment_contexts[];
  runs: PipelineExecutionFragment_runs[];
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