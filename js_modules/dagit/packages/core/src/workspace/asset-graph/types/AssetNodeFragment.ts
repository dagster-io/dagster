/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeFragment_op_outputDefinitions_metadataEntries = AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPathMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTextMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventIntMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry | AssetNodeFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeFragment_op_outputDefinitions_type_metadataEntries = AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeFragment_op_outputDefinitions_type_inputSchemaType = AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeFragment_op_outputDefinitions_type_outputSchemaType = AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries = AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry | AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType = AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType = AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType | AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType;

export interface AssetNodeFragment_op_outputDefinitions_type_innerTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetNodeFragment_op_outputDefinitions_type_innerTypes_metadataEntries[];
  inputSchemaType: AssetNodeFragment_op_outputDefinitions_type_innerTypes_inputSchemaType | null;
  outputSchemaType: AssetNodeFragment_op_outputDefinitions_type_innerTypes_outputSchemaType | null;
}

export interface AssetNodeFragment_op_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetNodeFragment_op_outputDefinitions_type_metadataEntries[];
  inputSchemaType: AssetNodeFragment_op_outputDefinitions_type_inputSchemaType | null;
  outputSchemaType: AssetNodeFragment_op_outputDefinitions_type_outputSchemaType | null;
  innerTypes: AssetNodeFragment_op_outputDefinitions_type_innerTypes[];
}

export interface AssetNodeFragment_op_outputDefinitions {
  __typename: "OutputDefinition";
  metadataEntries: AssetNodeFragment_op_outputDefinitions_metadataEntries[];
  type: AssetNodeFragment_op_outputDefinitions_type;
}

export interface AssetNodeFragment_op {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  outputDefinitions: AssetNodeFragment_op_outputDefinitions[];
}

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeFragment_repository_location;
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  op: AssetNodeFragment_op | null;
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetNodeFragment_assetKey;
  repository: AssetNodeFragment_repository;
}
