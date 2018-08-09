

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineFragment
// ====================================================

export interface PipelineFragment_solids_output_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_output_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_output_materializations_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_output_materializations_arguments {
  name: string;
  description: string | null;
  type: PipelineFragment_solids_output_materializations_arguments_type;
  isOptional: boolean;
}

export interface PipelineFragment_solids_output_materializations {
  name: string;
  description: string | null;
  arguments: PipelineFragment_solids_output_materializations_arguments[];
}

export interface PipelineFragment_solids_output {
  type: PipelineFragment_solids_output_type;
  expectations: PipelineFragment_solids_output_expectations[];
  materializations: PipelineFragment_solids_output_materializations[];
}

export interface PipelineFragment_solids_inputs_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_sources_arguments_type {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_inputs_sources_arguments {
  name: string;
  description: string | null;
  type: PipelineFragment_solids_inputs_sources_arguments_type;
  isOptional: boolean;
}

export interface PipelineFragment_solids_inputs_sources {
  name: string;
  description: string | null;
  arguments: PipelineFragment_solids_inputs_sources_arguments[];
}

export interface PipelineFragment_solids_inputs_dependsOn {
  name: string;
}

export interface PipelineFragment_solids_inputs {
  name: string;
  type: PipelineFragment_solids_inputs_type;
  expectations: PipelineFragment_solids_inputs_expectations[];
  description: string | null;
  sources: PipelineFragment_solids_inputs_sources[];
  dependsOn: PipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineFragment_solids {
  output: PipelineFragment_solids_output;
  inputs: PipelineFragment_solids_inputs[];
  name: string;
  description: string | null;
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