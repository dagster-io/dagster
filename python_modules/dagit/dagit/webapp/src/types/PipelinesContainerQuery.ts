

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelinesContainerQuery
// ====================================================

export interface PipelinesContainerQuery_pipelines_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_outputs_definition {
  name: string;
  type: PipelinesContainerQuery_pipelines_solids_outputs_definition_type;
  description: string | null;
  expectations: PipelinesContainerQuery_pipelines_solids_outputs_definition_expectations[];
}

export interface PipelinesContainerQuery_pipelines_solids_outputs {
  definition: PipelinesContainerQuery_pipelines_solids_outputs_definition;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_definition {
  name: string;
  type: PipelinesContainerQuery_pipelines_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelinesContainerQuery_pipelines_solids_inputs_definition_expectations[];
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs_dependsOn {
  definition: PipelinesContainerQuery_pipelines_solids_inputs_dependsOn_definition;
  solid: PipelinesContainerQuery_pipelines_solids_inputs_dependsOn_solid;
}

export interface PipelinesContainerQuery_pipelines_solids_inputs {
  definition: PipelinesContainerQuery_pipelines_solids_inputs_definition;
  dependsOn: PipelinesContainerQuery_pipelines_solids_inputs_dependsOn | null;
}

export interface PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type = PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_RegularType | PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type_CompositeType;

export interface PipelinesContainerQuery_pipelines_solids_definition_configDefinition {
  type: PipelinesContainerQuery_pipelines_solids_definition_configDefinition_type;
}

export interface PipelinesContainerQuery_pipelines_solids_definition {
  description: string | null;
  configDefinition: PipelinesContainerQuery_pipelines_solids_definition_configDefinition;
  name: string;
}

export interface PipelinesContainerQuery_pipelines_solids {
  outputs: PipelinesContainerQuery_pipelines_solids_outputs[];
  inputs: PipelinesContainerQuery_pipelines_solids_inputs[];
  name: string;
  definition: PipelinesContainerQuery_pipelines_solids_definition;
}

export interface PipelinesContainerQuery_pipelines_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType_fields_type;
}

export interface PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType_fields[];
}

export type PipelinesContainerQuery_pipelines_contexts_config_type = PipelinesContainerQuery_pipelines_contexts_config_type_RegularType | PipelinesContainerQuery_pipelines_contexts_config_type_CompositeType;

export interface PipelinesContainerQuery_pipelines_contexts_config {
  type: PipelinesContainerQuery_pipelines_contexts_config_type;
}

export interface PipelinesContainerQuery_pipelines_contexts {
  name: string;
  description: string | null;
  config: PipelinesContainerQuery_pipelines_contexts_config;
}

export interface PipelinesContainerQuery_pipelines {
  name: string;
  description: string | null;
  solids: PipelinesContainerQuery_pipelines_solids[];
  contexts: PipelinesContainerQuery_pipelines_contexts[];
}

export interface PipelinesContainerQuery {
  pipelines: PipelinesContainerQuery_pipelines[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================