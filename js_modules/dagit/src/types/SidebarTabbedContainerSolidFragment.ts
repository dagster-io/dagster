/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerSolidFragment
// ====================================================

export interface SidebarTabbedContainerSolidFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_outputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_outputs {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidFragment_outputs_definition;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_inputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition;
  solid: SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid;
}

export interface SidebarTabbedContainerSolidFragment_inputs {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidFragment_inputs_definition;
  dependsOn: SidebarTabbedContainerSolidFragment_inputs_dependsOn | null;
}

export interface SidebarTabbedContainerSolidFragment_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition {
  __typename: "SolidDefinition";
  description: string | null;
  metadata: SidebarTabbedContainerSolidFragment_definition_metadata[];
  configDefinition: SidebarTabbedContainerSolidFragment_definition_configDefinition | null;
}

export interface SidebarTabbedContainerSolidFragment {
  __typename: "Solid";
  outputs: SidebarTabbedContainerSolidFragment_outputs[];
  inputs: SidebarTabbedContainerSolidFragment_inputs[];
  name: string;
  definition: SidebarTabbedContainerSolidFragment_definition;
}
