/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelinesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config {
  __typename: "ConfigTypeField";
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config {
  __typename: "ConfigTypeField";
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources_config | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts {
  __typename: "PipelineContext";
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_config | null;
  resources: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts_resources[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType = AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_EnumConfigType | AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType_CompositeConfigType;

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition_configType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition {
  __typename: "SolidDefinition";
  metadata: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_metadata[];
  configDefinition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition_configDefinition | null;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_type;
  description: string | null;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition_expectations[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn {
  __typename: "Output";
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_definition;
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs {
  __typename: "Input";
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_definition;
  dependsOn: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_type;
  expectations: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy {
  __typename: "Input";
  solid: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy_solid;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs {
  __typename: "Output";
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_definition;
  dependedBy: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs_dependedBy[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_solids {
  __typename: "Solid";
  name: string;
  definition: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_definition;
  inputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_inputs[];
  outputs: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids_outputs[];
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
}

export interface AppQuery_pipelinesOrError_PipelineConnection_nodes {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  contexts: AppQuery_pipelinesOrError_PipelineConnection_nodes_contexts[];
  solids: AppQuery_pipelinesOrError_PipelineConnection_nodes_solids[];
  environmentType: AppQuery_pipelinesOrError_PipelineConnection_nodes_environmentType;
}

export interface AppQuery_pipelinesOrError_PipelineConnection {
  __typename: "PipelineConnection";
  nodes: AppQuery_pipelinesOrError_PipelineConnection_nodes[];
}

export type AppQuery_pipelinesOrError = AppQuery_pipelinesOrError_PythonError | AppQuery_pipelinesOrError_PipelineConnection;

export interface AppQuery {
  pipelinesOrError: AppQuery_pipelinesOrError;
}
