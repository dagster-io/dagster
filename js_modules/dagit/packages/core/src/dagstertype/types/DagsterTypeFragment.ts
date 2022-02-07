/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: DagsterTypeFragment
// ====================================================

export interface DagsterTypeFragment_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface DagsterTypeFragment_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface DagsterTypeFragment_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface DagsterTypeFragment_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface DagsterTypeFragment_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface DagsterTypeFragment_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface DagsterTypeFragment_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface DagsterTypeFragment_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface DagsterTypeFragment_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface DagsterTypeFragment_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: DagsterTypeFragment_metadataEntries_EventTableMetadataEntry_table;
}

export interface DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type DagsterTypeFragment_metadataEntries = DagsterTypeFragment_metadataEntries_EventPathMetadataEntry | DagsterTypeFragment_metadataEntries_EventJsonMetadataEntry | DagsterTypeFragment_metadataEntries_EventUrlMetadataEntry | DagsterTypeFragment_metadataEntries_EventTextMetadataEntry | DagsterTypeFragment_metadataEntries_EventMarkdownMetadataEntry | DagsterTypeFragment_metadataEntries_EventPythonArtifactMetadataEntry | DagsterTypeFragment_metadataEntries_EventFloatMetadataEntry | DagsterTypeFragment_metadataEntries_EventIntMetadataEntry | DagsterTypeFragment_metadataEntries_EventPipelineRunMetadataEntry | DagsterTypeFragment_metadataEntries_EventAssetMetadataEntry | DagsterTypeFragment_metadataEntries_EventTableMetadataEntry | DagsterTypeFragment_metadataEntries_EventTableSchemaMetadataEntry;

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: DagsterTypeFragment_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: DagsterTypeFragment_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: DagsterTypeFragment_innerTypes_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry_table;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type DagsterTypeFragment_innerTypes_metadataEntries = DagsterTypeFragment_innerTypes_metadataEntries_EventPathMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventJsonMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventUrlMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventTextMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventMarkdownMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventPythonArtifactMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventFloatMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventIntMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventPipelineRunMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventAssetMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventTableMetadataEntry | DagsterTypeFragment_innerTypes_metadataEntries_EventTableSchemaMetadataEntry;

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_inputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
  recursiveConfigTypes: DagsterTypeFragment_innerTypes_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface DagsterTypeFragment_innerTypes_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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

export interface DagsterTypeFragment_innerTypes_outputSchemaType_MapConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
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
