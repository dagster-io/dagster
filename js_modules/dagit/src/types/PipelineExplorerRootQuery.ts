// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExplorerRootQuery
// ====================================================

export interface PipelineExplorerRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "InvalidSubsetError";
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType = PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_resources[];
  loggers: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes_loggers[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_parent {
  __typename: "SolidHandle";
  handleID: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType = PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_EnumConfigType | PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition_configType;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  metadata: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_metadata[];
  configDefinition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition_configDefinition | null;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  metadata: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  inputMappings: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
  description: string | null;
}

export type PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition = PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_SolidDefinition | PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition_CompositeSolidDefinition;

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition_type;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_definition;
  solid: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_definition;
  dependsOn: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs_dependsOn[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition_type;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_solid;
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy_definition;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_definition;
  dependedBy: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs_dependedBy[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_definition;
  inputs: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_inputs[];
  outputs: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid_outputs[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  parent: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_parent | null;
  solid: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles_solid;
}

export interface PipelineExplorerRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  modes: PipelineExplorerRootQuery_pipelineOrError_Pipeline_modes[];
  solids: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solids[];
  solidHandles: PipelineExplorerRootQuery_pipelineOrError_Pipeline_solidHandles[];
}

export interface PipelineExplorerRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export type PipelineExplorerRootQuery_pipelineOrError = PipelineExplorerRootQuery_pipelineOrError_PythonError | PipelineExplorerRootQuery_pipelineOrError_Pipeline | PipelineExplorerRootQuery_pipelineOrError_PipelineNotFoundError;

export interface PipelineExplorerRootQuery {
  pipelineOrError: PipelineExplorerRootQuery_pipelineOrError;
}

export interface PipelineExplorerRootQueryVariables {
  name: string;
}
