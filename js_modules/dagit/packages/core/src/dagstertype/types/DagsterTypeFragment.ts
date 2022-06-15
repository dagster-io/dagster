/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: DagsterTypeFragment
// ====================================================

export interface DagsterTypeFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface DagsterTypeFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface DagsterTypeFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface DagsterTypeFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface DagsterTypeFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface DagsterTypeFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface DagsterTypeFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface DagsterTypeFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface DagsterTypeFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface DagsterTypeFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface DagsterTypeFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface DagsterTypeFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: DagsterTypeFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: DagsterTypeFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface DagsterTypeFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: DagsterTypeFragment_metadataEntries_TableMetadataEntry_table;
}

export interface DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type DagsterTypeFragment_metadataEntries = DagsterTypeFragment_metadataEntries_PathMetadataEntry | DagsterTypeFragment_metadataEntries_JsonMetadataEntry | DagsterTypeFragment_metadataEntries_UrlMetadataEntry | DagsterTypeFragment_metadataEntries_TextMetadataEntry | DagsterTypeFragment_metadataEntries_MarkdownMetadataEntry | DagsterTypeFragment_metadataEntries_PythonArtifactMetadataEntry | DagsterTypeFragment_metadataEntries_FloatMetadataEntry | DagsterTypeFragment_metadataEntries_IntMetadataEntry | DagsterTypeFragment_metadataEntries_BoolMetadataEntry | DagsterTypeFragment_metadataEntries_PipelineRunMetadataEntry | DagsterTypeFragment_metadataEntries_AssetMetadataEntry | DagsterTypeFragment_metadataEntries_TableMetadataEntry | DagsterTypeFragment_metadataEntries_TableSchemaMetadataEntry;

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes = DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type DagsterTypeFragment_inputSchemaType = DagsterTypeFragment_inputSchemaType_ArrayConfigType | DagsterTypeFragment_inputSchemaType_EnumConfigType | DagsterTypeFragment_inputSchemaType_RegularConfigType | DagsterTypeFragment_inputSchemaType_CompositeConfigType | DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType | DagsterTypeFragment_inputSchemaType_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes = DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type DagsterTypeFragment_outputSchemaType = DagsterTypeFragment_outputSchemaType_ArrayConfigType | DagsterTypeFragment_outputSchemaType_EnumConfigType | DagsterTypeFragment_outputSchemaType_RegularConfigType | DagsterTypeFragment_outputSchemaType_CompositeConfigType | DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType | DagsterTypeFragment_outputSchemaType_MapConfigType;

export interface DagsterTypeFragment_innerTypes_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: DagsterTypeFragment_innerTypes_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table_schema;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry_table;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type DagsterTypeFragment_innerTypes_metadataEntries = DagsterTypeFragment_innerTypes_metadataEntries_PathMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_JsonMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_UrlMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_TextMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_MarkdownMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_PythonArtifactMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_FloatMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_IntMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_BoolMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_PipelineRunMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_AssetMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_TableMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_TableSchemaMetadataEntry;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type DagsterTypeFragment_innerTypes_inputSchemaType = DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_values[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType_values[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes = DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type DagsterTypeFragment_innerTypes_outputSchemaType = DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType | DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType;

export interface DagsterTypeFragment_innerTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: DagsterTypeFragment_innerTypes_metadataEntries[];
  inputSchemaType: DagsterTypeFragment_innerTypes_inputSchemaType | null;
  outputSchemaType: DagsterTypeFragment_innerTypes_outputSchemaType | null;
}

export interface DagsterTypeFragment {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: DagsterTypeFragment_metadataEntries[];
  inputSchemaType: DagsterTypeFragment_inputSchemaType | null;
  outputSchemaType: DagsterTypeFragment_outputSchemaType | null;
  innerTypes: DagsterTypeFragment_innerTypes[];
}
