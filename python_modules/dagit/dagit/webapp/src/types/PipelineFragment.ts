

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineFragment
// ====================================================

export interface PipelineFragment_solids_outputs_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_outputs {
  name: string;
  type: PipelineFragment_solids_outputs_type;
  description: string | null;
  expectations: PipelineFragment_solids_outputs_expectations[];
}

export interface PipelineFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineFragment_solids_inputs_dependsOn {
  name: string;
  solid: PipelineFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineFragment_solids_inputs {
  name: string;
  type: PipelineFragment_solids_inputs_type;
  description: string | null;
  expectations: PipelineFragment_solids_inputs_expectations[];
  dependsOn: PipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineFragment_solids_config_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_config {
  name: string;
  description: string | null;
  type: PipelineFragment_solids_config_type;
  isOptional: boolean;
}

export interface PipelineFragment_solids {
  outputs: PipelineFragment_solids_outputs[];
  inputs: PipelineFragment_solids_inputs[];
  name: string;
  description: string | null;
  config: PipelineFragment_solids_config[];
}

export interface PipelineFragment_context_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_context_arguments {
  name: string;
  description: string | null;
  type: PipelineFragment_context_arguments_type;
  isOptional: boolean;
}

export interface PipelineFragment_context {
  name: string;
  description: string | null;
  arguments: PipelineFragment_context_arguments[];
}

export interface PipelineFragment {
  name: string;
  description: string | null;
  solids: PipelineFragment_solids[];
  context: PipelineFragment_context[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================