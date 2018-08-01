

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_inputs_sources {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs {
  name: string;
  sources: PipelineGraphFragment_solids_inputs_sources[];
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn | null;
}

export interface PipelineGraphFragment_solids_output_materializations {
  name: string;
}

export interface PipelineGraphFragment_solids_output_expectations {
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_output {
  materializations: PipelineGraphFragment_solids_output_materializations[];
  expectations: PipelineGraphFragment_solids_output_expectations[];
}

export interface PipelineGraphFragment_solids {
  name: string;
  inputs: PipelineGraphFragment_solids_inputs[];
  output: PipelineGraphFragment_solids_output;
}

export interface PipelineGraphFragment {
  solids: PipelineGraphFragment_solids[];
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