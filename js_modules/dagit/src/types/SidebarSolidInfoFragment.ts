/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoFragment
// ====================================================

export interface SidebarSolidInfoFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarSolidInfoFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_outputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_outputs {
  __typename: "Output";
  definition: SidebarSolidInfoFragment_outputs_definition;
}

export interface SidebarSolidInfoFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SidebarSolidInfoFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_inputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarSolidInfoFragment_inputs_dependsOn_definition;
  solid: SidebarSolidInfoFragment_inputs_dependsOn_solid;
}

export interface SidebarSolidInfoFragment_inputs {
  __typename: "Input";
  definition: SidebarSolidInfoFragment_inputs_definition;
  dependsOn: SidebarSolidInfoFragment_inputs_dependsOn | null;
}

export interface SidebarSolidInfoFragment_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType = SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType;
}

export interface SidebarSolidInfoFragment_definition {
  __typename: "SolidDefinition";
  description: string | null;
  metadata: SidebarSolidInfoFragment_definition_metadata[];
  configDefinition: SidebarSolidInfoFragment_definition_configDefinition | null;
}

export interface SidebarSolidInfoFragment {
  __typename: "Solid";
  outputs: SidebarSolidInfoFragment_outputs[];
  inputs: SidebarSolidInfoFragment_inputs[];
  name: string;
  definition: SidebarSolidInfoFragment_definition;
}
