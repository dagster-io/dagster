

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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType {
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config {
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts {
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config | null;
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata {
  key: string;
  value: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  __typename: "RegularType";
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  __typename: "CompositeType";
  name: string;
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

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string;
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
  name: string;
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
  dependedBy: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy[] | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids {
  name: string;
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition;
  inputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs[];
  outputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes {
  name: string;
  environmentType: AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType;
  contexts: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts[];
  description: string | null;
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

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  JOIN = "JOIN",
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