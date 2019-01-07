

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelinePageFragment
// ====================================================

export interface PipelinePageFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent";
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes = PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_LogMessageEvent | PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepFailureEvent | PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes_ExecutionStepStartEvent;

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_logs {
  nodes: PipelinePageFragment_PipelineConnection_nodes_runs_logs_nodes[];
  pageInfo: PipelinePageFragment_PipelineConnection_nodes_runs_logs_pageInfo;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan_steps {
  name: string;
  solid: PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan {
  steps: PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan_steps[];
}

export interface PipelinePageFragment_PipelineConnection_nodes_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelinePageFragment_PipelineConnection_nodes_runs_logs;
  executionPlan: PipelinePageFragment_PipelineConnection_nodes_runs_executionPlan;
}

export interface PipelinePageFragment_PipelineConnection_nodes_environmentType {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_config_type = PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config {
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type = PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config {
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_resources {
  name: string;
  description: string | null;
  config: PipelinePageFragment_PipelineConnection_nodes_contexts_resources_config | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts {
  name: string;
  description: string | null;
  config: PipelinePageFragment_PipelineConnection_nodes_contexts_config | null;
  resources: PipelinePageFragment_PipelineConnection_nodes_contexts_resources[];
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes = PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType | PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type = PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition {
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition {
  metadata: PipelinePageFragment_PipelineConnection_nodes_solids_definition_metadata[];
  configDefinition: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition | null;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_type_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition {
  name: string;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_expectations[];
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn {
  definition: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn_definition;
  solid: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn_solid;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs {
  definition: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition;
  dependsOn: PipelinePageFragment_PipelineConnection_nodes_solids_inputs_dependsOn | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_type_typeAttributes;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition {
  name: string;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_type;
  expectations: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_dependedBy {
  solid: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_dependedBy_solid;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs {
  definition: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition;
  dependedBy: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_dependedBy[];
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids {
  name: string;
  definition: PipelinePageFragment_PipelineConnection_nodes_solids_definition;
  inputs: PipelinePageFragment_PipelineConnection_nodes_solids_inputs[];
  outputs: PipelinePageFragment_PipelineConnection_nodes_solids_outputs[];
}

export interface PipelinePageFragment_PipelineConnection_nodes {
  name: string;
  runs: PipelinePageFragment_PipelineConnection_nodes_runs[];
  environmentType: PipelinePageFragment_PipelineConnection_nodes_environmentType;
  description: string | null;
  contexts: PipelinePageFragment_PipelineConnection_nodes_contexts[];
  solids: PipelinePageFragment_PipelineConnection_nodes_solids[];
}

export interface PipelinePageFragment_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: PipelinePageFragment_PipelineConnection_nodes[];
}

export type PipelinePageFragment = PipelinePageFragment_PythonError | PipelinePageFragment_PipelineConnection;

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