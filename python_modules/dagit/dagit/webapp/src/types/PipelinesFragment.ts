

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelinesFragment
// ====================================================

export interface PipelinesFragment_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_outputs_definition {
  name: string;
  type: PipelinesFragment_solids_outputs_definition_type;
  description: string | null;
  expectations: PipelinesFragment_solids_outputs_definition_expectations[];
}

export interface PipelinesFragment_solids_outputs {
  definition: PipelinesFragment_solids_outputs_definition;
}

export interface PipelinesFragment_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_inputs_definition {
  name: string;
  type: PipelinesFragment_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelinesFragment_solids_inputs_definition_expectations[];
}

export interface PipelinesFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelinesFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelinesFragment_solids_inputs_dependsOn {
  definition: PipelinesFragment_solids_inputs_dependsOn_definition;
  solid: PipelinesFragment_solids_inputs_dependsOn_solid;
}

export interface PipelinesFragment_solids_inputs {
  definition: PipelinesFragment_solids_inputs_definition;
  dependsOn: PipelinesFragment_solids_inputs_dependsOn | null;
}

export interface PipelinesFragment_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelinesFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelinesFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelinesFragment_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelinesFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelinesFragment_solids_definition_configDefinition_type = PipelinesFragment_solids_definition_configDefinition_type_RegularType | PipelinesFragment_solids_definition_configDefinition_type_CompositeType;

export interface PipelinesFragment_solids_definition_configDefinition {
  type: PipelinesFragment_solids_definition_configDefinition_type;
}

export interface PipelinesFragment_solids_definition {
  description: string | null;
  configDefinition: PipelinesFragment_solids_definition_configDefinition | null;
}

export interface PipelinesFragment_solids {
  outputs: PipelinesFragment_solids_outputs[];
  inputs: PipelinesFragment_solids_inputs[];
  name: string;
  definition: PipelinesFragment_solids_definition;
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
  config: PipelinesFragment_contexts_config | null;
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