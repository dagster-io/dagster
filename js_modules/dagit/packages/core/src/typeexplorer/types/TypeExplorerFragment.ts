/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface TypeExplorerFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface TypeExplorerFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface TypeExplorerFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface TypeExplorerFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface TypeExplorerFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface TypeExplorerFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface TypeExplorerFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface TypeExplorerFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface TypeExplorerFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface TypeExplorerFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface TypeExplorerFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: TypeExplorerFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: TypeExplorerFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface TypeExplorerFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: TypeExplorerFragment_metadataEntries_TableMetadataEntry_table;
}

export interface TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type TypeExplorerFragment_metadataEntries = TypeExplorerFragment_metadataEntries_PathMetadataEntry | TypeExplorerFragment_metadataEntries_JsonMetadataEntry | TypeExplorerFragment_metadataEntries_UrlMetadataEntry | TypeExplorerFragment_metadataEntries_TextMetadataEntry | TypeExplorerFragment_metadataEntries_MarkdownMetadataEntry | TypeExplorerFragment_metadataEntries_PythonArtifactMetadataEntry | TypeExplorerFragment_metadataEntries_FloatMetadataEntry | TypeExplorerFragment_metadataEntries_IntMetadataEntry | TypeExplorerFragment_metadataEntries_BoolMetadataEntry | TypeExplorerFragment_metadataEntries_PipelineRunMetadataEntry | TypeExplorerFragment_metadataEntries_AssetMetadataEntry | TypeExplorerFragment_metadataEntries_TableMetadataEntry | TypeExplorerFragment_metadataEntries_TableSchemaMetadataEntry;

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_inputSchemaType = TypeExplorerFragment_inputSchemaType_ArrayConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType | TypeExplorerFragment_inputSchemaType_RegularConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType | TypeExplorerFragment_inputSchemaType_ScalarUnionConfigType | TypeExplorerFragment_inputSchemaType_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface TypeExplorerFragment_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_outputSchemaType = TypeExplorerFragment_outputSchemaType_ArrayConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType | TypeExplorerFragment_outputSchemaType_RegularConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType | TypeExplorerFragment_outputSchemaType_ScalarUnionConfigType | TypeExplorerFragment_outputSchemaType_MapConfigType;

export interface TypeExplorerFragment {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  description: string | null;
  metadataEntries: TypeExplorerFragment_metadataEntries[];
  inputSchemaType: TypeExplorerFragment_inputSchemaType | null;
  outputSchemaType: TypeExplorerFragment_outputSchemaType | null;
}
