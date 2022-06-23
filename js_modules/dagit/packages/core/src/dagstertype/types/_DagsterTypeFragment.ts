/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: _DagsterTypeFragment
// ====================================================

export interface _DagsterTypeFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface _DagsterTypeFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface _DagsterTypeFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface _DagsterTypeFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface _DagsterTypeFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface _DagsterTypeFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface _DagsterTypeFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface _DagsterTypeFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface _DagsterTypeFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface _DagsterTypeFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface _DagsterTypeFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface _DagsterTypeFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: _DagsterTypeFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface _DagsterTypeFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: _DagsterTypeFragment_metadataEntries_TableMetadataEntry_table;
}

export interface _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type _DagsterTypeFragment_metadataEntries = _DagsterTypeFragment_metadataEntries_PathMetadataEntry | _DagsterTypeFragment_metadataEntries_JsonMetadataEntry | _DagsterTypeFragment_metadataEntries_UrlMetadataEntry | _DagsterTypeFragment_metadataEntries_TextMetadataEntry | _DagsterTypeFragment_metadataEntries_MarkdownMetadataEntry | _DagsterTypeFragment_metadataEntries_PythonArtifactMetadataEntry | _DagsterTypeFragment_metadataEntries_FloatMetadataEntry | _DagsterTypeFragment_metadataEntries_IntMetadataEntry | _DagsterTypeFragment_metadataEntries_BoolMetadataEntry | _DagsterTypeFragment_metadataEntries_PipelineRunMetadataEntry | _DagsterTypeFragment_metadataEntries_AssetMetadataEntry | _DagsterTypeFragment_metadataEntries_TableMetadataEntry | _DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry;

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes = _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type _DagsterTypeFragment_inputSchemaType = _DagsterTypeFragment_inputSchemaType_ArrayConfigType | _DagsterTypeFragment_inputSchemaType_EnumConfigType | _DagsterTypeFragment_inputSchemaType_RegularConfigType | _DagsterTypeFragment_inputSchemaType_CompositeConfigType | _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType | _DagsterTypeFragment_inputSchemaType_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes = _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type _DagsterTypeFragment_outputSchemaType = _DagsterTypeFragment_outputSchemaType_ArrayConfigType | _DagsterTypeFragment_outputSchemaType_EnumConfigType | _DagsterTypeFragment_outputSchemaType_RegularConfigType | _DagsterTypeFragment_outputSchemaType_CompositeConfigType | _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType | _DagsterTypeFragment_outputSchemaType_MapConfigType;

export interface _DagsterTypeFragment {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: _DagsterTypeFragment_metadataEntries[];
  inputSchemaType: _DagsterTypeFragment_inputSchemaType | null;
  outputSchemaType: _DagsterTypeFragment_outputSchemaType | null;
}
