

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

export interface PipelinePageFragment_PipelineConnection_nodes_environmentType {
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type = PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_contexts_config_type = PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_contexts_config_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_contexts_config {
  type: PipelinePageFragment_PipelineConnection_nodes_contexts_config_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_contexts {
  config: PipelinePageFragment_PipelineConnection_nodes_contexts_config | null;
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  __typename: "RegularType";
  name: string;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type = PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  __typename: "CompositeType";
  name: string;
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

export interface PipelinePageFragment_PipelineConnection_nodes_solids_inputs_definition_type {
  name: string;
  description: string | null;
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

export interface PipelinePageFragment_PipelineConnection_nodes_solids_outputs_definition_type {
  name: string;
  description: string | null;
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
  dependedBy: PipelinePageFragment_PipelineConnection_nodes_solids_outputs_dependedBy[] | null;
}

export interface PipelinePageFragment_PipelineConnection_nodes_solids {
  name: string;
  definition: PipelinePageFragment_PipelineConnection_nodes_solids_definition;
  inputs: PipelinePageFragment_PipelineConnection_nodes_solids_inputs[];
  outputs: PipelinePageFragment_PipelineConnection_nodes_solids_outputs[];
}

export interface PipelinePageFragment_PipelineConnection_nodes {
  name: string;
  environmentType: PipelinePageFragment_PipelineConnection_nodes_environmentType;
  contexts: PipelinePageFragment_PipelineConnection_nodes_contexts[];
  description: string | null;
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