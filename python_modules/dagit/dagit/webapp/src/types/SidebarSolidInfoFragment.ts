

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoFragment
// ====================================================

export interface SidebarSolidInfoFragment_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition {
  name: string;
  type: SidebarSolidInfoFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_outputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_outputs {
  definition: SidebarSolidInfoFragment_outputs_definition;
}

export interface SidebarSolidInfoFragment_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition {
  name: string;
  type: SidebarSolidInfoFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_inputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn {
  definition: SidebarSolidInfoFragment_inputs_dependsOn_definition;
  solid: SidebarSolidInfoFragment_inputs_dependsOn_solid;
}

export interface SidebarSolidInfoFragment_inputs {
  definition: SidebarSolidInfoFragment_inputs_definition;
  dependsOn: SidebarSolidInfoFragment_inputs_dependsOn | null;
}

export interface SidebarSolidInfoFragment_definition_metadata {
  key: string | null;
  value: string | null;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type = SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_RegularType | SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_type = SidebarSolidInfoFragment_definition_configDefinition_type_RegularType | SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType;

export interface SidebarSolidInfoFragment_definition_configDefinition {
  type: SidebarSolidInfoFragment_definition_configDefinition_type;
}

export interface SidebarSolidInfoFragment_definition {
  description: string | null;
  metadata: SidebarSolidInfoFragment_definition_metadata[] | null;
  configDefinition: SidebarSolidInfoFragment_definition_configDefinition | null;
}

export interface SidebarSolidInfoFragment {
  outputs: SidebarSolidInfoFragment_outputs[];
  inputs: SidebarSolidInfoFragment_inputs[];
  name: string;
  definition: SidebarSolidInfoFragment_definition;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================