/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "DagsterTypeNotFoundError" | "PythonError";
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table_schema;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry_table;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PathMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_JsonMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_UrlMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TextMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_MarkdownMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PythonArtifactMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_FloatMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_IntMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_BoolMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_PipelineRunMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_AssetMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableMetadataEntry | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries_TableSchemaMetadataEntry;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_MapConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType {
  __typename: "RegularDagsterType";
  name: string | null;
  description: string | null;
  metadataEntries: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_metadataEntries[];
  inputSchemaType: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType | null;
  outputSchemaType: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_PipelineNotFoundError | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  dagsterTypeOrError: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError;
}

export type TypeExplorerContainerQuery_pipelineOrError = TypeExplorerContainerQuery_pipelineOrError_PipelineNotFoundError | TypeExplorerContainerQuery_pipelineOrError_Pipeline;

export interface TypeExplorerContainerQuery {
  pipelineOrError: TypeExplorerContainerQuery_pipelineOrError;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineSelector: PipelineSelector;
  dagsterTypeName: string;
}
