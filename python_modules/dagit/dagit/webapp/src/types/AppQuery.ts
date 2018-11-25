

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelinesOrErrors_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type = AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_RegularType | AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type = AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_RegularType | AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type_CompositeType;

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts_config {
  type: AppQuery_pipelinesOrErrors_Pipeline_contexts_config_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_contexts {
  name: string;
  description: string | null;
  config: AppQuery_pipelinesOrErrors_Pipeline_contexts_config | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_metadata {
  key: string;
  value: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_RegularType {
  description: string | null;
  __typename: "RegularType";
  name: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type = AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_RegularType | AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType {
  description: string | null;
  __typename: "CompositeType";
  name: string;
  fields: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type = AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_RegularType | AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type_CompositeType;

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition {
  type: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition_type;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_definition {
  metadata: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_metadata[];
  configDefinition: AppQuery_pipelinesOrErrors_Pipeline_solids_definition_configDefinition | null;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition {
  name: string;
  type: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition_type;
  description: string | null;
  expectations: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition_expectations[];
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn_definition {
  name: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn_solid {
  name: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn {
  definition: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn_definition;
  solid: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn_solid;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_inputs {
  definition: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_definition;
  dependsOn: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition {
  name: string;
  type: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition_type;
  expectations: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_dependedBy_solid {
  name: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_dependedBy {
  solid: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_dependedBy_solid;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids_outputs {
  definition: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_definition;
  dependedBy: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs_dependedBy[] | null;
}

export interface AppQuery_pipelinesOrErrors_Pipeline_solids {
  name: string;
  definition: AppQuery_pipelinesOrErrors_Pipeline_solids_definition;
  inputs: AppQuery_pipelinesOrErrors_Pipeline_solids_inputs[];
  outputs: AppQuery_pipelinesOrErrors_Pipeline_solids_outputs[];
}

export interface AppQuery_pipelinesOrErrors_Pipeline_environmentType {
  name: string;
}

export interface AppQuery_pipelinesOrErrors_Pipeline {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  contexts: AppQuery_pipelinesOrErrors_Pipeline_contexts[];
  solids: AppQuery_pipelinesOrErrors_Pipeline_solids[];
  environmentType: AppQuery_pipelinesOrErrors_Pipeline_environmentType;
}

export type AppQuery_pipelinesOrErrors = AppQuery_pipelinesOrErrors_PythonError | AppQuery_pipelinesOrErrors_Pipeline;

export interface AppQuery {
  pipelinesOrErrors: AppQuery_pipelinesOrErrors[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================