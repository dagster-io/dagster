

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineFragment
// ====================================================

export interface PipelineFragment_solids_outputs_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs {
  name: string;
  type: PipelineFragment_solids_outputs_type;
  description: string | null;
  expectations: PipelineFragment_solids_outputs_expectations[];
}

export interface PipelineFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineFragment_solids_inputs_dependsOn {
  name: string;
  solid: PipelineFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineFragment_solids_inputs {
  name: string;
  type: PipelineFragment_solids_inputs_type;
  description: string | null;
  expectations: PipelineFragment_solids_inputs_expectations[];
  dependsOn: PipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineFragment_solids_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineFragment_solids_config_type_CompositeType_fields_type;
}

export interface PipelineFragment_solids_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineFragment_solids_config_type_CompositeType_fields[];
}

export type PipelineFragment_solids_config_type = PipelineFragment_solids_config_type_RegularType | PipelineFragment_solids_config_type_CompositeType;

export interface PipelineFragment_solids_config {
  type: PipelineFragment_solids_config_type;
}

export interface PipelineFragment_solids {
  outputs: PipelineFragment_solids_outputs[];
  inputs: PipelineFragment_solids_inputs[];
  name: string;
  description: string | null;
  config: PipelineFragment_solids_config;
}

export interface PipelineFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineFragment_contexts_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

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
  config: PipelineFragment_contexts_config;
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