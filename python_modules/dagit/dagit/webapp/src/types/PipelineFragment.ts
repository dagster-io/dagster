

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineFragment
// ====================================================

export interface PipelineFragment_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs_definition {
  name: string;
  type: PipelineFragment_solids_outputs_definition_type;
  description: string | null;
  expectations: PipelineFragment_solids_outputs_definition_expectations[];
}

export interface PipelineFragment_solids_outputs {
  definition: PipelineFragment_solids_outputs_definition;
}

export interface PipelineFragment_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_definition {
  name: string;
  type: PipelineFragment_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelineFragment_solids_inputs_definition_expectations[];
}

export interface PipelineFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineFragment_solids_inputs_dependsOn {
  definition: PipelineFragment_solids_inputs_dependsOn_definition;
  solid: PipelineFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineFragment_solids_inputs {
  definition: PipelineFragment_solids_inputs_definition;
  dependsOn: PipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineFragment_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type = PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelineFragment_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelineFragment_solids_definition_configDefinition_type = PipelineFragment_solids_definition_configDefinition_type_RegularType | PipelineFragment_solids_definition_configDefinition_type_CompositeType;

export interface PipelineFragment_solids_definition_configDefinition {
  type: PipelineFragment_solids_definition_configDefinition_type;
}

export interface PipelineFragment_solids_definition {
  description: string | null;
  configDefinition: PipelineFragment_solids_definition_configDefinition | null;
  name: string;
}

export interface PipelineFragment_solids {
  outputs: PipelineFragment_solids_outputs[];
  inputs: PipelineFragment_solids_inputs[];
  name: string;
  definition: PipelineFragment_solids_definition;
}

export interface PipelineFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineFragment_contexts_config_type_CompositeType_fields_type = PipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType | PipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelineFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineFragment_contexts_config_type_CompositeType_fields_type;
}

export interface PipelineFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineFragment_contexts_config_type_CompositeType_fields[];
}

export type PipelineFragment_contexts_config_type = PipelineFragment_contexts_config_type_RegularType | PipelineFragment_contexts_config_type_CompositeType;

export interface PipelineFragment_contexts_config {
  type: PipelineFragment_contexts_config_type;
}

export interface PipelineFragment_contexts {
  name: string;
  description: string | null;
  config: PipelineFragment_contexts_config | null;
}

export interface PipelineFragment {
  name: string;
  description: string | null;
  solids: PipelineFragment_solids[];
  contexts: PipelineFragment_contexts[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================