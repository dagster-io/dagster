/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineFragment
// ====================================================

export interface PipelineExecutionPipelineFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionPipelineFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType = PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExecutionPipelineFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: PipelineExecutionPipelineFragment_configTypes_CompositeConfigType_fields[];
}

export type PipelineExecutionPipelineFragment_configTypes = PipelineExecutionPipelineFragment_configTypes_EnumConfigType | PipelineExecutionPipelineFragment_configTypes_CompositeConfigType;

export interface PipelineExecutionPipelineFragment {
  __typename: "Pipeline";
  name: string;
  environmentType: PipelineExecutionPipelineFragment_environmentType;
  configTypes: PipelineExecutionPipelineFragment_configTypes[];
}
