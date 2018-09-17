

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidFragment
// ====================================================

export interface SolidFragment_outputs_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_outputs_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_outputs {
  name: string;
  type: SolidFragment_outputs_type;
  description: string | null;
  expectations: SolidFragment_outputs_expectations[];
}

export interface SolidFragment_inputs_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SolidFragment_inputs_dependsOn {
  name: string;
  solid: SolidFragment_inputs_dependsOn_solid;
}

export interface SolidFragment_inputs {
  name: string;
  type: SolidFragment_inputs_type;
  description: string | null;
  expectations: SolidFragment_inputs_expectations[];
  dependsOn: SolidFragment_inputs_dependsOn | null;
}

export interface SolidFragment_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface SolidFragment_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SolidFragment_config_type_CompositeType_fields_type;
}

export interface SolidFragment_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SolidFragment_config_type_CompositeType_fields[];
}

export type SolidFragment_config_type = SolidFragment_config_type_RegularType | SolidFragment_config_type_CompositeType;

export interface SolidFragment_config {
  type: SolidFragment_config_type;
}

export interface SolidFragment {
  outputs: SolidFragment_outputs[];
  inputs: SolidFragment_inputs[];
  name: string;
  description: string | null;
  config: SolidFragment_config;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================