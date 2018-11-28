

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

export interface PipelinePageFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
  stack: string[];
}

export interface PipelinePageFragment_Pipeline_environmentType {
  name: string;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type = PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_RegularType | PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_Pipeline_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinePageFragment_Pipeline_contexts_config_type_CompositeType_fields[];
}

export type PipelinePageFragment_Pipeline_contexts_config_type = PipelinePageFragment_Pipeline_contexts_config_type_RegularType | PipelinePageFragment_Pipeline_contexts_config_type_CompositeType;

export interface PipelinePageFragment_Pipeline_contexts_config {
  type: PipelinePageFragment_Pipeline_contexts_config_type;
}

export interface PipelinePageFragment_Pipeline_contexts {
  config: PipelinePageFragment_Pipeline_contexts_config | null;
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  __typename: "RegularType";
  name: string;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type = PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  __typename: "CompositeType";
  name: string;
  fields: PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelinePageFragment_Pipeline_solids_definition_configDefinition_type = PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_RegularType | PipelinePageFragment_Pipeline_solids_definition_configDefinition_type_CompositeType;

export interface PipelinePageFragment_Pipeline_solids_definition_configDefinition {
  type: PipelinePageFragment_Pipeline_solids_definition_configDefinition_type;
}

export interface PipelinePageFragment_Pipeline_solids_definition {
  metadata: PipelinePageFragment_Pipeline_solids_definition_metadata[];
  configDefinition: PipelinePageFragment_Pipeline_solids_definition_configDefinition | null;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_inputs_definition {
  name: string;
  type: PipelinePageFragment_Pipeline_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelinePageFragment_Pipeline_solids_inputs_definition_expectations[];
}

export interface PipelinePageFragment_Pipeline_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelinePageFragment_Pipeline_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinePageFragment_Pipeline_solids_inputs_dependsOn {
  definition: PipelinePageFragment_Pipeline_solids_inputs_dependsOn_definition;
  solid: PipelinePageFragment_Pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelinePageFragment_Pipeline_solids_inputs {
  definition: PipelinePageFragment_Pipeline_solids_inputs_definition;
  dependsOn: PipelinePageFragment_Pipeline_solids_inputs_dependsOn | null;
}

export interface PipelinePageFragment_Pipeline_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_outputs_definition {
  name: string;
  type: PipelinePageFragment_Pipeline_solids_outputs_definition_type;
  expectations: PipelinePageFragment_Pipeline_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelinePageFragment_Pipeline_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelinePageFragment_Pipeline_solids_outputs_dependedBy {
  solid: PipelinePageFragment_Pipeline_solids_outputs_dependedBy_solid;
}

export interface PipelinePageFragment_Pipeline_solids_outputs {
  definition: PipelinePageFragment_Pipeline_solids_outputs_definition;
  dependedBy: PipelinePageFragment_Pipeline_solids_outputs_dependedBy[] | null;
}

export interface PipelinePageFragment_Pipeline_solids {
  name: string;
  definition: PipelinePageFragment_Pipeline_solids_definition;
  inputs: PipelinePageFragment_Pipeline_solids_inputs[];
  outputs: PipelinePageFragment_Pipeline_solids_outputs[];
}

export interface PipelinePageFragment_Pipeline {
  __typename: "Pipeline";
  name: string;
  environmentType: PipelinePageFragment_Pipeline_environmentType;
  contexts: PipelinePageFragment_Pipeline_contexts[];
  description: string | null;
  solids: PipelinePageFragment_Pipeline_solids[];
}

export type PipelinePageFragment = PipelinePageFragment_PythonError | PipelinePageFragment_PipelineNotFoundError | PipelinePageFragment_Pipeline;

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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