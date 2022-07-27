/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineExplorerRootQuery
// ====================================================

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table_schema;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry_table;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PathMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_JsonMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_UrlMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TextMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_MarkdownMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PythonArtifactMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_FloatMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_IntMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_BoolMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_PipelineRunMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_AssetMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableMetadataEntry | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries_TableSchemaMetadataEntry;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_values[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType_recursiveConfigTypes[];
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ArrayConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_RegularConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_CompositeConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_ScalarUnionConfigType | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType_MapConfigType;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
  resources: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_resources[];
  loggers: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes_loggers[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs_dependsOn[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_solid;
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy_definition;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_definition;
  dependedBy: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs_dependedBy[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_metadata[];
  assetNodes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_assetNodes[];
  inputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  assetNodes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_assetNodes[];
  inputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_SolidDefinition | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition_CompositeSolidDefinition;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_inputs[];
  outputs: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_outputs[];
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid_definition;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  assetKey: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes_assetKey;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType" | "MapConfigType";
  key: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField_configType;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  assetNodes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_assetNodes[];
  name: string;
  description: string | null;
  metadata: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_outputDefinitions[];
  configField: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition_configField | null;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  assetKey: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes_assetKey;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  assetNodes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_assetNodes[];
  name: string;
  description: string | null;
  metadata: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_SolidDefinition | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition_CompositeSolidDefinition;

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_definition;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_definition;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_definition;
  dependedBy: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
  isDynamicMapped: boolean;
  inputs: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  metadataEntries: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_metadataEntries[];
  description: string | null;
  modes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_modes[];
  pipelineSnapshotId: string;
  parentSnapshotId: string | null;
  solidHandle: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandle | null;
  solidHandles: PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelineExplorerRootQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PipelineExplorerRootQuery_pipelineSnapshotOrError_PythonError_causes[];
}

export type PipelineExplorerRootQuery_pipelineSnapshotOrError = PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineNotFoundError | PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | PipelineExplorerRootQuery_pipelineSnapshotOrError_PythonError;

export interface PipelineExplorerRootQuery {
  pipelineSnapshotOrError: PipelineExplorerRootQuery_pipelineSnapshotOrError;
}

export interface PipelineExplorerRootQueryVariables {
  snapshotPipelineSelector?: PipelineSelector | null;
  snapshotId?: string | null;
  rootHandleID: string;
  requestScopeHandleID?: string | null;
}
