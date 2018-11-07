

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineGraphFragment_solids_definition_configDefinition_type {
  description: string | null;
}

export interface PipelineGraphFragment_solids_definition_configDefinition {
  type: PipelineGraphFragment_solids_definition_configDefinition_type;
}

export interface PipelineGraphFragment_solids_definition {
  metadata: PipelineGraphFragment_solids_definition_metadata[];
  configDefinition: PipelineGraphFragment_solids_definition_configDefinition | null;
}

export interface PipelineGraphFragment_solids_inputs_definition_type {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_definition {
  name: string;
  type: PipelineGraphFragment_solids_inputs_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  definition: PipelineGraphFragment_solids_inputs_dependsOn_definition;
  solid: PipelineGraphFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineGraphFragment_solids_inputs {
  definition: PipelineGraphFragment_solids_inputs_definition;
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn | null;
}

export interface PipelineGraphFragment_solids_outputs_definition_type {
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_outputs_definition {
  name: string;
  type: PipelineGraphFragment_solids_outputs_definition_type;
  expectations: PipelineGraphFragment_solids_outputs_definition_expectations[];
}

export interface PipelineGraphFragment_solids_outputs {
  definition: PipelineGraphFragment_solids_outputs_definition;
}

export interface PipelineGraphFragment_solids {
  name: string;
  definition: PipelineGraphFragment_solids_definition;
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