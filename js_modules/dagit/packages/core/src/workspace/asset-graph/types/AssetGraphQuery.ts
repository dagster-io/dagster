/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries = AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPathMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventJsonMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventUrlMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTextMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventMarkdownMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventFloatMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventIntMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventAssetMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries = AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPathMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTextMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventIntMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType = AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType = AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPathMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventJsonMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventUrlMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTextMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventMarkdownMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventFloatMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventIntMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventAssetMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableMetadataEntry | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries_EventTableSchemaMetadataEntry;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType {
  __typename: "MapConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
  recursiveConfigTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes[];
}

export type AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType = AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ArrayConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_EnumConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_RegularConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_CompositeConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_ScalarUnionConfigType | AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType_MapConfigType;

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_metadataEntries[];
  inputSchemaType: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_inputSchemaType | null;
  outputSchemaType: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes_outputSchemaType | null;
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  key: string;
  name: string | null;
  displayName: string;
  description: string | null;
  isNullable: boolean;
  isList: boolean;
  isBuiltin: boolean;
  isNothing: boolean;
  metadataEntries: AssetGraphQuery_assetNodes_op_outputDefinitions_type_metadataEntries[];
  inputSchemaType: AssetGraphQuery_assetNodes_op_outputDefinitions_type_inputSchemaType | null;
  outputSchemaType: AssetGraphQuery_assetNodes_op_outputDefinitions_type_outputSchemaType | null;
  innerTypes: AssetGraphQuery_assetNodes_op_outputDefinitions_type_innerTypes[];
}

export interface AssetGraphQuery_assetNodes_op_outputDefinitions {
  __typename: "OutputDefinition";
  metadataEntries: AssetGraphQuery_assetNodes_op_outputDefinitions_metadataEntries[];
  type: AssetGraphQuery_assetNodes_op_outputDefinitions_type;
}

export interface AssetGraphQuery_assetNodes_op {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  outputDefinitions: AssetGraphQuery_assetNodes_op_outputDefinitions[];
}

export interface AssetGraphQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphQuery_assetNodes_repository_location;
}

export interface AssetGraphQuery_assetNodes_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_dependedByKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  op: AssetGraphQuery_assetNodes_op | null;
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetGraphQuery_assetNodes_assetKey;
  repository: AssetGraphQuery_assetNodes_repository;
  dependencyKeys: AssetGraphQuery_assetNodes_dependencyKeys[];
  dependedByKeys: AssetGraphQuery_assetNodes_dependedByKeys[];
}

export interface AssetGraphQuery {
  assetNodes: AssetGraphQuery_assetNodes[];
}

export interface AssetGraphQueryVariables {
  pipelineSelector?: PipelineSelector | null;
}
