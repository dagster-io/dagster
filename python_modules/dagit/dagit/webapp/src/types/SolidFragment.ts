

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidFragment
// ====================================================

export interface SolidFragment_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_outputs_definition {
  name: string;
  type: SolidFragment_outputs_definition_type;
  description: string | null;
  expectations: SolidFragment_outputs_definition_expectations[];
}

export interface SolidFragment_outputs {
  definition: SolidFragment_outputs_definition;
}

export interface SolidFragment_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SolidFragment_inputs_definition {
  name: string;
  type: SolidFragment_inputs_definition_type;
  description: string | null;
  expectations: SolidFragment_inputs_definition_expectations[];
}

export interface SolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SolidFragment_inputs_dependsOn {
  definition: SolidFragment_inputs_dependsOn_definition;
  solid: SolidFragment_inputs_dependsOn_solid;
}

export interface SolidFragment_inputs {
  definition: SolidFragment_inputs_definition;
  dependsOn: SolidFragment_inputs_dependsOn | null;
}

export interface SolidFragment_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface SolidFragment_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface SolidFragment_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SolidFragment_definition_configDefinition_type_CompositeType_fields_type;
}

export interface SolidFragment_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SolidFragment_definition_configDefinition_type_CompositeType_fields[];
}

export type SolidFragment_definition_configDefinition_type = SolidFragment_definition_configDefinition_type_RegularType | SolidFragment_definition_configDefinition_type_CompositeType;

export interface SolidFragment_definition_configDefinition {
  type: SolidFragment_definition_configDefinition_type;
}

export interface SolidFragment_definition {
  description: string | null;
  configDefinition: SolidFragment_definition_configDefinition;
}

export interface SolidFragment {
  outputs: SolidFragment_outputs[];
  inputs: SolidFragment_inputs[];
  name: string;
  definition: SolidFragment_definition;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================