

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerFragment
// ====================================================

export interface PipelineExplorerFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type = PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_RegularType | PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelineExplorerFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerFragment_contexts_config_type_CompositeType_fields_type;
}

export interface PipelineExplorerFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineExplorerFragment_contexts_config_type_CompositeType_fields[];
}

export type PipelineExplorerFragment_contexts_config_type = PipelineExplorerFragment_contexts_config_type_RegularType | PipelineExplorerFragment_contexts_config_type_CompositeType;

export interface PipelineExplorerFragment_contexts_config {
  type: PipelineExplorerFragment_contexts_config_type;
}

export interface PipelineExplorerFragment_contexts {
  name: string;
  description: string | null;
  config: PipelineExplorerFragment_contexts_config | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition {
  name: string;
  type: PipelineExplorerFragment_solids_outputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerFragment_solids_outputs_definition_expectations[];
}

export interface PipelineExplorerFragment_solids_outputs {
  definition: PipelineExplorerFragment_solids_outputs_definition;
}

export interface PipelineExplorerFragment_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_inputs_definition {
  name: string;
  type: PipelineExplorerFragment_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerFragment_solids_inputs_definition_expectations[];
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn {
  definition: PipelineExplorerFragment_solids_inputs_dependsOn_definition;
  solid: PipelineExplorerFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineExplorerFragment_solids_inputs {
  definition: PipelineExplorerFragment_solids_inputs_definition;
  dependsOn: PipelineExplorerFragment_solids_inputs_dependsOn | null;
}

export interface PipelineExplorerFragment_solids_definition_metadata {
  key: string | null;
  value: string | null;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type = PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelineExplorerFragment_solids_definition_configDefinition_type = PipelineExplorerFragment_solids_definition_configDefinition_type_RegularType | PipelineExplorerFragment_solids_definition_configDefinition_type_CompositeType;

export interface PipelineExplorerFragment_solids_definition_configDefinition {
  type: PipelineExplorerFragment_solids_definition_configDefinition_type;
}

export interface PipelineExplorerFragment_solids_definition {
  description: string | null;
  metadata: PipelineExplorerFragment_solids_definition_metadata[] | null;
  configDefinition: PipelineExplorerFragment_solids_definition_configDefinition | null;
  name: string;
}

export interface PipelineExplorerFragment_solids {
  outputs: PipelineExplorerFragment_solids_outputs[];
  inputs: PipelineExplorerFragment_solids_inputs[];
  name: string;
  definition: PipelineExplorerFragment_solids_definition;
}

export interface PipelineExplorerFragment {
  name: string;
  description: string | null;
  contexts: PipelineExplorerFragment_contexts[];
  solids: PipelineExplorerFragment_solids[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================