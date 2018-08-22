

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_inputs_type {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  name: string;
  solid: PipelineGraphFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineGraphFragment_solids_inputs {
  name: string;
  type: PipelineGraphFragment_solids_inputs_type;
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn | null;
}

export interface PipelineGraphFragment_solids_outputs_type {
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_expectations {
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_outputs {
  name: string;
  type: PipelineGraphFragment_solids_outputs_type;
  expectations: PipelineGraphFragment_solids_outputs_expectations[];
}

export interface PipelineGraphFragment_solids {
  name: string;
  inputs: PipelineGraphFragment_solids_inputs[];
  outputs: PipelineGraphFragment_solids_outputs[];
}

export interface PipelineGraphFragment {
  name: string;
  solids: PipelineGraphFragment_solids[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================