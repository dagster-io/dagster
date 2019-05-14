// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerFragment
// ====================================================

export interface PipelineExplorerFragment_solids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerFragment_solids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: PipelineExplorerFragment_solids_definition_CompositeSolidDefinition_metadata[];
}

export interface PipelineExplorerFragment_solids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerFragment_solids_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_solids_definition_SolidDefinition_configDefinition_configType;
}

export interface PipelineExplorerFragment_solids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: PipelineExplorerFragment_solids_definition_SolidDefinition_metadata[];
  configDefinition: PipelineExplorerFragment_solids_definition_SolidDefinition_configDefinition | null;
}

export type PipelineExplorerFragment_solids_definition = PipelineExplorerFragment_solids_definition_CompositeSolidDefinition | PipelineExplorerFragment_solids_definition_SolidDefinition;

export interface PipelineExplorerFragment_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineExplorerFragment_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_inputs_definition_type;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerFragment_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerFragment_solids_inputs_dependsOn_definition;
  solid: PipelineExplorerFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineExplorerFragment_solids_inputs {
  __typename: "Input";
  definition: PipelineExplorerFragment_solids_inputs_definition;
  dependsOn: PipelineExplorerFragment_solids_inputs_dependsOn[];
}

export interface PipelineExplorerFragment_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineExplorerFragment_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerFragment_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_outputs_definition_type;
  expectations: PipelineExplorerFragment_solids_outputs_definition_expectations[];
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerFragment_solids_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerFragment_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerFragment_solids_outputs_dependedBy_solid;
  definition: PipelineExplorerFragment_solids_outputs_dependedBy_definition;
}

export interface PipelineExplorerFragment_solids_outputs {
  __typename: "Output";
  definition: PipelineExplorerFragment_solids_outputs_definition;
  dependedBy: PipelineExplorerFragment_solids_outputs_dependedBy[];
}

export interface PipelineExplorerFragment_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerFragment_solids_definition;
  inputs: PipelineExplorerFragment_solids_inputs[];
  outputs: PipelineExplorerFragment_solids_outputs[];
}

export interface PipelineExplorerFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_resources_configField_configType = PipelineExplorerFragment_modes_resources_configField_configType_EnumConfigType | PipelineExplorerFragment_modes_resources_configField_configType_CompositeConfigType;

export interface PipelineExplorerFragment_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_modes_resources_configField_configType;
}

export interface PipelineExplorerFragment_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: PipelineExplorerFragment_modes_resources_configField | null;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes = PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerFragment_modes_loggers_configField_configType = PipelineExplorerFragment_modes_loggers_configField_configType_EnumConfigType | PipelineExplorerFragment_modes_loggers_configField_configType_CompositeConfigType;

export interface PipelineExplorerFragment_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerFragment_modes_loggers_configField_configType;
}

export interface PipelineExplorerFragment_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: PipelineExplorerFragment_modes_loggers_configField | null;
}

export interface PipelineExplorerFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: PipelineExplorerFragment_modes_resources[];
  loggers: PipelineExplorerFragment_modes_loggers[];
}

export interface PipelineExplorerFragment {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  solids: PipelineExplorerFragment_solids[];
  environmentType: PipelineExplorerFragment_environmentType;
  modes: PipelineExplorerFragment_modes[];
}
