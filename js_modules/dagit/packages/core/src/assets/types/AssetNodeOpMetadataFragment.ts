/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeOpMetadataFragment
// ====================================================

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries = AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPathMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTextMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventIntMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries = AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType = AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType = AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType = AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType | AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType;

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_metadataEntries[];
  inputSchemaType: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_inputSchemaType | null;
  outputSchemaType: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes_outputSchemaType | null;
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetNodeOpMetadataFragment_op_outputDefinitions_type_metadataEntries[];
  inputSchemaType: AssetNodeOpMetadataFragment_op_outputDefinitions_type_inputSchemaType | null;
  outputSchemaType: AssetNodeOpMetadataFragment_op_outputDefinitions_type_outputSchemaType | null;
  innerTypes: AssetNodeOpMetadataFragment_op_outputDefinitions_type_innerTypes[];
}

export interface AssetNodeOpMetadataFragment_op_outputDefinitions {
  __typename: "OutputDefinition";
  metadataEntries: AssetNodeOpMetadataFragment_op_outputDefinitions_metadataEntries[];
  type: AssetNodeOpMetadataFragment_op_outputDefinitions_type;
}

export interface AssetNodeOpMetadataFragment_op {
  __typename: "SolidDefinition";
  outputDefinitions: AssetNodeOpMetadataFragment_op_outputDefinitions[];
}

export interface AssetNodeOpMetadataFragment {
  __typename: "AssetNode";
  id: string;
  op: AssetNodeOpMetadataFragment_op | null;
}
