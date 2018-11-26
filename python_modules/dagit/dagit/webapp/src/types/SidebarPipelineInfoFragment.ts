

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type = SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType | SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_type = SidebarPipelineInfoFragment_contexts_config_type_RegularType | SidebarPipelineInfoFragment_contexts_config_type_CompositeType;

export interface SidebarPipelineInfoFragment_contexts_config {
  type: SidebarPipelineInfoFragment_contexts_config_type;
}

export interface SidebarPipelineInfoFragment_contexts {
  name: string;
  description: string | null;
  config: SidebarPipelineInfoFragment_contexts_config | null;
}

export interface SidebarPipelineInfoFragment {
  name: string;
  description: string | null;
  contexts: SidebarPipelineInfoFragment_contexts[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================