/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidFragment
// ====================================================

export interface PipelineExplorerSolidFragment_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType = PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType;
}

export interface PipelineExplorerSolidFragment_definition {
  __typename: "SolidDefinition";
  metadata: PipelineExplorerSolidFragment_definition_metadata[];
  configDefinition: PipelineExplorerSolidFragment_definition_configDefinition | null;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerSolidFragment_inputs_definition_expectations[];
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerSolidFragment_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerSolidFragment_inputs_dependsOn_definition;
  solid: PipelineExplorerSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineExplorerSolidFragment_inputs {
  __typename: "Input";
  definition: PipelineExplorerSolidFragment_inputs_definition;
  dependsOn: PipelineExplorerSolidFragment_inputs_dependsOn | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerSolidFragment_outputs_definition_type;
  expectations: PipelineExplorerSolidFragment_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerSolidFragment_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerSolidFragment_outputs_dependedBy_solid;
  definition: PipelineExplorerSolidFragment_outputs_dependedBy_definition;
}

export interface PipelineExplorerSolidFragment_outputs {
  __typename: "Output";
  definition: PipelineExplorerSolidFragment_outputs_definition;
  dependedBy: PipelineExplorerSolidFragment_outputs_dependedBy[];
}

export interface PipelineExplorerSolidFragment {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerSolidFragment_definition;
  inputs: PipelineExplorerSolidFragment_inputs[];
  outputs: PipelineExplorerSolidFragment_outputs[];
}
