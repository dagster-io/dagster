

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelinesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes = AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_LogMessageEvent | AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent | AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs {
  nodes: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_nodes[];
  pageInfo: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs_pageInfo;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan_steps_solid {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan_steps {
  name: string;
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan {
  steps: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan_steps[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_logs;
  executionPlan: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs_executionPlan;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType_fields {
  name: string;
  isOptional: boolean;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_types = AppQuery_pipelinesOrError_PipelineConnection_nodes_types_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_types_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources {
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts {
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config | null;
  resources: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata {
  key: string;
  value: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition {
  metadata: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata[];
  configDefinition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition | null;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition {
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type;
  description: string | null;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition;
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition;
  dependsOn: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition {
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy {
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs {
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition;
  dependedBy: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids {
  name: string;
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition;
  inputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs[];
  outputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes {
  name: string;
  runs: AppQuery_pipelinesOrError_PipelineConnection_nodes_runs[];
  environmentType: AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType;
  types: AppQuery_pipelinesOrError_PipelineConnection_nodes_types[];
  description: string | null;
  contexts: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts[];
  solids: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: AppQuery_pipelinesOrError_PipelineConnection_nodes[];
}

export type AppQuery_pipelinesOrError = AppQuery_pipelinesOrError_PythonError | AppQuery_pipelinesOrError_PipelineConnection;

export interface AppQuery {
  pipelinesOrError: AppQuery_pipelinesOrError;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
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