

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigExplorerFragment
// ====================================================

export interface ConfigExplorerFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type = ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_RegularType | ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigExplorerFragment_contexts_config_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_contexts_config_type = ConfigExplorerFragment_contexts_config_type_RegularType | ConfigExplorerFragment_contexts_config_type_CompositeType;

export interface ConfigExplorerFragment_contexts_config {
  type: ConfigExplorerFragment_contexts_config_type;
}

export interface ConfigExplorerFragment_contexts {
  name: string;
  description: string | null;
  config: ConfigExplorerFragment_contexts_config | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type = ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_type = ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType | ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType;

export interface ConfigExplorerFragment_solids_definition_configDefinition {
  type: ConfigExplorerFragment_solids_definition_configDefinition_type;
}

export interface ConfigExplorerFragment_solids_definition {
  name: string;
  description: string | null;
  configDefinition: ConfigExplorerFragment_solids_definition_configDefinition | null;
}

export interface ConfigExplorerFragment_solids {
  definition: ConfigExplorerFragment_solids_definition;
}

export interface ConfigExplorerFragment {
  contexts: ConfigExplorerFragment_contexts[];
  solids: ConfigExplorerFragment_solids[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================