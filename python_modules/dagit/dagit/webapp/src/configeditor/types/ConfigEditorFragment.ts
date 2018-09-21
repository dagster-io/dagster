

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorFragment
// ====================================================

export interface ConfigEditorFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface ConfigEditorFragment_contexts_config_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface ConfigEditorFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigEditorFragment_contexts_config_type_CompositeType_fields_type;
}

export interface ConfigEditorFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigEditorFragment_contexts_config_type_CompositeType_fields[];
}

export type ConfigEditorFragment_contexts_config_type = ConfigEditorFragment_contexts_config_type_RegularType | ConfigEditorFragment_contexts_config_type_CompositeType;

export interface ConfigEditorFragment_contexts_config {
  type: ConfigEditorFragment_contexts_config_type;
}

export interface ConfigEditorFragment_contexts {
  name: string;
  description: string | null;
  config: ConfigEditorFragment_contexts_config;
}

export interface ConfigEditorFragment_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type ConfigEditorFragment_solids_definition_configDefinition_type = ConfigEditorFragment_solids_definition_configDefinition_type_RegularType | ConfigEditorFragment_solids_definition_configDefinition_type_CompositeType;

export interface ConfigEditorFragment_solids_definition_configDefinition {
  type: ConfigEditorFragment_solids_definition_configDefinition_type;
}

export interface ConfigEditorFragment_solids_definition {
  name: string;
  description: string | null;
  configDefinition: ConfigEditorFragment_solids_definition_configDefinition;
}

export interface ConfigEditorFragment_solids {
  definition: ConfigEditorFragment_solids_definition;
}

export interface ConfigEditorFragment {
  contexts: ConfigEditorFragment_contexts[];
  solids: ConfigEditorFragment_solids[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================