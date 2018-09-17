

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelinesFragment
// ====================================================

export interface PipelinesFragment_solids_outputs_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs {
  name: string;
  type: PipelinesFragment_solids_outputs_type;
  description: string | null;
  expectations: PipelinesFragment_solids_outputs_expectations[];
}

export interface PipelinesFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinesFragment_solids_inputs_dependsOn {
  name: string;
  solid: PipelinesFragment_solids_inputs_dependsOn_solid;
}

export interface PipelinesFragment_solids_inputs {
  name: string;
  type: PipelinesFragment_solids_inputs_type;
  description: string | null;
  expectations: PipelinesFragment_solids_inputs_expectations[];
  dependsOn: PipelinesFragment_solids_inputs_dependsOn | null;
}

export interface PipelinesFragment_solids_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinesFragment_solids_config_type_CompositeType_fields_type;
}

export interface PipelinesFragment_solids_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinesFragment_solids_config_type_CompositeType_fields[];
}

export type PipelinesFragment_solids_config_type = PipelinesFragment_solids_config_type_RegularType | PipelinesFragment_solids_config_type_CompositeType;

export interface PipelinesFragment_solids_config {
  type: PipelinesFragment_solids_config_type;
}

export interface PipelinesFragment_solids {
  outputs: PipelinesFragment_solids_outputs[];
  inputs: PipelinesFragment_solids_inputs[];
  name: string;
  description: string | null;
  config: PipelinesFragment_solids_config;
}

export interface PipelinesFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinesFragment_contexts_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinesFragment_contexts_config_type_CompositeType_fields_type;
}

export interface PipelinesFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinesFragment_contexts_config_type_CompositeType_fields[];
}

export type PipelinesFragment_contexts_config_type = PipelinesFragment_contexts_config_type_RegularType | PipelinesFragment_contexts_config_type_CompositeType;

export interface PipelinesFragment_contexts_config {
  type: PipelinesFragment_contexts_config_type;
}

export interface PipelinesFragment_contexts {
  name: string;
  description: string | null;
  config: PipelinesFragment_contexts_config;
}

export interface PipelinesFragment {
  name: string;
  description: string | null;
  solids: PipelinesFragment_solids[];
  contexts: PipelinesFragment_contexts[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================