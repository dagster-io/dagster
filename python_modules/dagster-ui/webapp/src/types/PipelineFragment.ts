

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineFragment
// ====================================================

export interface PipelineFragment_solids_inputs_sources_arguments {
  name: string;
  description: string | null;
  type: Type;
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
  description: string | null;
  sources: PipelineFragment_solids_inputs_sources[];
  dependsOn: PipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineFragment_solids_output_materializations_arguments {
  name: string;
  description: string | null;
  type: Type;
  isOptional: boolean;
}

export interface PipelineFragment_solids_output_materializations {
  name: string;
  description: string | null;
  arguments: PipelineFragment_solids_output_materializations_arguments[];
}

export interface PipelineFragment_solids_output_expectations {
  name: string;
  description: string | null;
}

export interface PipelineFragment_solids_output {
  materializations: PipelineFragment_solids_output_materializations[];
  expectations: PipelineFragment_solids_output_expectations[];
}

export interface PipelineFragment_solids {
  name: string;
  description: string | null;
  inputs: PipelineFragment_solids_inputs[];
  output: PipelineFragment_solids_output;
}

export interface PipelineFragment_context_arguments {
  name: string;
  description: string | null;
  type: Type;
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

export enum Type {
  BOOL = "BOOL",
  INT = "INT",
  PATH = "PATH",
  STRING = "STRING",
}

//==============================================================
// END Enums and Input Objects
//==============================================================