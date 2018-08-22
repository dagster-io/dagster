

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AppQuery
// ====================================================

export interface AppQuery_pipelines_solids_outputs_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_outputs {
  name: string;
  type: AppQuery_pipelines_solids_outputs_type;
  description: string | null;
  expectations: AppQuery_pipelines_solids_outputs_expectations[];
}

export interface AppQuery_pipelines_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_inputs_dependsOn_solid {
  name: string;
}

export interface AppQuery_pipelines_solids_inputs_dependsOn {
  name: string;
  solid: AppQuery_pipelines_solids_inputs_dependsOn_solid;
}

export interface AppQuery_pipelines_solids_inputs {
  name: string;
  type: AppQuery_pipelines_solids_inputs_type;
  description: string | null;
  expectations: AppQuery_pipelines_solids_inputs_expectations[];
  dependsOn: AppQuery_pipelines_solids_inputs_dependsOn | null;
}

export interface AppQuery_pipelines_solids_config_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_solids_config {
  name: string;
  description: string | null;
  type: AppQuery_pipelines_solids_config_type;
  isOptional: boolean;
}

export interface AppQuery_pipelines_solids {
  outputs: AppQuery_pipelines_solids_outputs[];
  inputs: AppQuery_pipelines_solids_inputs[];
  name: string;
  description: string | null;
  config: AppQuery_pipelines_solids_config[];
}

export interface AppQuery_pipelines_context_arguments_type {
  name: string;
  description: string | null;
}

export interface AppQuery_pipelines_context_arguments {
  name: string;
  description: string | null;
  type: AppQuery_pipelines_context_arguments_type;
  isOptional: boolean;
}

export interface AppQuery_pipelines_context {
  name: string;
  description: string | null;
  arguments: AppQuery_pipelines_context_arguments[];
}

export interface AppQuery_pipelines {
  name: string;
  description: string | null;
  solids: AppQuery_pipelines_solids[];
  context: AppQuery_pipelines_context[];
}

export interface AppQuery {
  pipelines: AppQuery_pipelines[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================