

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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config {
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config {
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType;
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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType {
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType {
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition {
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition {
  metadata: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata[];
  configDefinition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition | null;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string | null;
  description: string | null;
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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type {
  name: string | null;
  description: string | null;
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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType {
  name: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes {
  name: string;
  description: string | null;
  contexts: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts[];
  solids: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids[];
  environmentType: AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType;
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

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

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

export enum StepKind {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================