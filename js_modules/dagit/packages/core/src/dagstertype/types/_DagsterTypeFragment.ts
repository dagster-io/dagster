/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: _DagsterTypeFragment
// ====================================================

export interface _DagsterTypeFragment_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface _DagsterTypeFragment_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface _DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface _DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: _DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type _DagsterTypeFragment_metadataEntries = _DagsterTypeFragment_metadataEntries_EventPathMetadataEntry | _DagsterTypeFragment_metadataEntries_EventJsonMetadataEntry | _DagsterTypeFragment_metadataEntries_EventUrlMetadataEntry | _DagsterTypeFragment_metadataEntries_EventTextMetadataEntry | _DagsterTypeFragment_metadataEntries_EventMarkdownMetadataEntry | _DagsterTypeFragment_metadataEntries_EventPythonArtifactMetadataEntry | _DagsterTypeFragment_metadataEntries_EventFloatMetadataEntry | _DagsterTypeFragment_metadataEntries_EventIntMetadataEntry | _DagsterTypeFragment_metadataEntries_EventPipelineRunMetadataEntry | _DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry | _DagsterTypeFragment_metadataEntries_EventTableMetadataEntry | _DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry;

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: _DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: _DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface _DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface _DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
